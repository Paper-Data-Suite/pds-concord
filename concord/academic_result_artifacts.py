"""Consumer-neutral contracts and authorized Concord Artifact source resolution.

Public contract models remain presentation-neutral. Native workspace access is
permitted only behind the explicit deployment-owned authorization gate, and
resolution is bound to the exact historical Concord snapshot named by the
validated Academic Result Manifest.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn, Protocol, TypeAlias

from pds_core.identifiers import validate_identifier
from pds_core.routing_models import ModuleWorkRef

from concord.academic_result_manifest import (
    AcademicResultManifest,
    ConcordAcademicResultManifestValidationError,
    CorePublicationReferenceProjection,
    EvidenceLocatorProjection,
    EvidenceReferenceProjection,
    PublicActor,
    RecordReferenceProjection,
    ScoreEvidenceLinkProjection,
    SubjectReferenceProjection,
    validate_academic_result_manifest,
)
from concord.academic_result_reader import (
    ConcordAcademicResultReaderNotFoundError,
    lookup_academic_result_score_evidence_link,
)
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ActorReference,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactSubject,
    ConcordRecordReference,
    EvidenceLocator,
    EvidenceReference,
    ParticipantReference,
    ScoreEvidenceLink,
    SubjectReference,
)
from concord.pds_contract import (
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_MODULE_ID,
)
from concord.storage import load_record_graph_at_snapshot
from concord.storage_errors import (
    ConcordStorageError,
    ConcordStorageNotFoundError,
)
from concord.storage_models import ConcordLoadedRecordGraph

AcademicResultArtifactRepresentation: TypeAlias = Literal[
    "returned_artifact_pdf"
]
ArtifactAuthorizationStatus: TypeAlias = Literal[
    "allowed",
    "denied",
    "unresolved",
]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXTENSION_KEY = re.compile(r"^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$")
_ARTIFACT_CATEGORIES = frozenset(
    {
        "student_work",
        "observation",
        "discussion_record",
        "laboratory_record",
        "project_record",
    }
)
_AUTHORSHIP_MODES = frozenset(
    {
        "individual_author",
        "co_author",
        "observer",
        "recorder",
        "recorder_for_group",
        "collective_group_author",
        "teacher_author",
        "authorized_adult_author",
        "unknown",
    }
)
_ATTRIBUTION_STATUSES = frozenset(
    {"proposed", "confirmed", "disputed", "unknown", "superseded"}
)
_REPRESENTATION_STATUSES = frozenset(
    {
        "individual_view",
        "recorder_summary",
        "majority_position",
        "unanimous_position",
        "multiple_named_positions",
        "no_consensus",
        "not_applicable",
    }
)
_SUBJECT_ROLES = frozenset(
    {
        "observed_participant",
        "represented_group",
        "activity_context",
        "session_context",
        "evaluated_artifact",
        "general_subject",
    }
)
_CONFIRMATION_STATUSES = frozenset(
    {"proposed", "confirmed", "disputed", "unresolved", "superseded"}
)
_PRIVACY_CLASSIFICATIONS = frozenset(
    {
        "teacher_restricted",
        "teacher_and_subjects",
        "group_and_teacher",
        "classroom_shared",
        "inherited",
        "external_policy",
    }
)


class ConcordAcademicResultArtifactError(Exception):
    """Base failure for public Concord Academic Result Artifact access."""


class ConcordAcademicResultArtifactValidationError(
    ConcordAcademicResultArtifactError, ValueError
):
    """Artifact request or public projection violates the public contract."""


class ConcordAcademicResultArtifactAuthorizationError(
    ConcordAcademicResultArtifactError
):
    """External authorization did not affirmatively allow Artifact I/O."""


class ConcordAcademicResultArtifactNotFoundError(
    ConcordAcademicResultArtifactError, LookupError
):
    """An authorized exact historical canonical object is absent."""


class ConcordAcademicResultArtifactUnavailableError(
    ConcordAcademicResultArtifactError
):
    """Represented evidence cannot produce the bounded Artifact."""


class ConcordAcademicResultArtifactAmbiguityError(
    ConcordAcademicResultArtifactError
):
    """Represented evidence cannot resolve to one exact Artifact."""


class ConcordAcademicResultArtifactIntegrityError(
    ConcordAcademicResultArtifactError
):
    """Historical identity, lineage, path, digest, or output integrity failed."""


def _fail(message: str) -> NoReturn:
    raise ConcordAcademicResultArtifactValidationError(message)


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str):
        _fail(f"{field} must be a safe identifier.")
    try:
        return validate_identifier(value, field)
    except (TypeError, ValueError) as error:
        raise ConcordAcademicResultArtifactValidationError(
            f"{field} must be a safe identifier."
        ) from error


def _optional_identifier(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _identifier(value, field)


def _lower_identifier(value: object, field: str) -> str:
    result = _identifier(value, field)
    if result != result.lower():
        _fail(f"{field} must be lowercase.")
    return result


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        _fail(f"{field} must be a positive integer.")
    return value


def _optional_public_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _public_text(value, field)


def _public_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        _fail(f"{field} must be nonempty and trimmed.")
    if len(value) > 512:
        _fail(f"{field} is too long.")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        _fail(f"{field} must be control-free.")
    return value


def _controlled(value: object, field: str, allowed: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{field} must be one of: {', '.join(sorted(allowed))}.")
    return value


def _controlled_key(
    value: object,
    field: str,
    builtins: frozenset[str],
) -> str:
    text = _public_text(value, field)
    if text not in builtins and _EXTENSION_KEY.fullmatch(text) is None:
        _fail(f"{field} must be a built-in or namespace-qualified key.")
    return text


def _sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        _fail(f"{field} must be a lowercase SHA-256 digest.")
    return value


@dataclass(frozen=True, slots=True)
class AcademicResultParticipantReferenceProjection:
    participant_kind: str
    participant_id: str
    owning_system: str

    def __post_init__(self) -> None:
        _controlled(
            self.participant_kind,
            "participant_reference.participant_kind",
            frozenset({"core_student", "authorized_actor"}),
        )
        _identifier(
            self.participant_id,
            "participant_reference.participant_id",
        )
        _lower_identifier(
            self.owning_system,
            "participant_reference.owning_system",
        )


AcademicResultArtifactAuthorReference: TypeAlias = (
    AcademicResultParticipantReferenceProjection
    | PublicActor
    | RecordReferenceProjection
)


@dataclass(frozen=True, slots=True)
class AcademicResultArtifactPageProjection:
    artifact_page_id: str
    page_number: int

    def __post_init__(self) -> None:
        _identifier(self.artifact_page_id, "artifact_page.artifact_page_id")
        _positive_int(self.page_number, "artifact_page.page_number")


@dataclass(frozen=True, slots=True)
class AcademicResultArtifactProjection:
    artifact_instance_id: str
    artifact_category: str
    session_id: str | None
    group_id: str | None
    pages: tuple[AcademicResultArtifactPageProjection, ...]
    privacy_classification: str

    def __post_init__(self) -> None:
        _identifier(
            self.artifact_instance_id,
            "artifact.artifact_instance_id",
        )
        _controlled_key(
            self.artifact_category,
            "artifact.artifact_category",
            _ARTIFACT_CATEGORIES,
        )
        _optional_identifier(self.session_id, "artifact.session_id")
        _optional_identifier(self.group_id, "artifact.group_id")
        pages = tuple(self.pages)
        if not pages or any(
            not isinstance(item, AcademicResultArtifactPageProjection)
            for item in pages
        ):
            _fail("artifact.pages must contain public Artifact Page projections.")
        if len({item.artifact_page_id for item in pages}) != len(pages):
            _fail("artifact.pages must not repeat Artifact Page identities.")
        if len({item.page_number for item in pages}) != len(pages):
            _fail("artifact.pages must not repeat logical page numbers.")
        object.__setattr__(self, "pages", pages)
        _controlled(
            self.privacy_classification,
            "artifact.privacy_classification",
            _PRIVACY_CLASSIFICATIONS,
        )


@dataclass(frozen=True, slots=True)
class AcademicResultArtifactAuthorProjection:
    artifact_author_id: str
    artifact_instance_id: str
    author_reference: AcademicResultArtifactAuthorReference | None
    authorship_mode: str
    attribution_status: str
    represented_group_id: str | None
    representation_status: str | None

    def __post_init__(self) -> None:
        _identifier(
            self.artifact_author_id,
            "artifact_author.artifact_author_id",
        )
        _identifier(
            self.artifact_instance_id,
            "artifact_author.artifact_instance_id",
        )
        if self.author_reference is not None and not isinstance(
            self.author_reference,
            (
                AcademicResultParticipantReferenceProjection,
                PublicActor,
                RecordReferenceProjection,
            ),
        ):
            _fail("artifact_author.author_reference is invalid.")
        _controlled(
            self.authorship_mode,
            "artifact_author.authorship_mode",
            _AUTHORSHIP_MODES,
        )
        _controlled(
            self.attribution_status,
            "artifact_author.attribution_status",
            _ATTRIBUTION_STATUSES,
        )
        _optional_identifier(
            self.represented_group_id,
            "artifact_author.represented_group_id",
        )
        if self.representation_status is not None:
            _controlled(
                self.representation_status,
                "artifact_author.representation_status",
                _REPRESENTATION_STATUSES,
            )
        if self.authorship_mode == "unknown":
            if self.author_reference is not None:
                _fail("unknown authorship must not invent an author reference.")
            if self.attribution_status != "unknown":
                _fail("unknown authorship requires unknown attribution status.")
            if (
                self.represented_group_id is not None
                or self.representation_status is not None
            ):
                _fail("unknown authorship cannot carry representation context.")
        elif self.author_reference is None:
            _fail("known authorship requires an exact author reference.")
        if (
            self.authorship_mode == "recorder_for_group"
            and self.represented_group_id is None
        ):
            _fail("recorder_for_group requires represented_group_id.")


@dataclass(frozen=True, slots=True)
class AcademicResultArtifactSubjectProjection:
    artifact_subject_id: str
    artifact_instance_id: str
    subject_reference: SubjectReferenceProjection
    subject_role: str
    confirmation_status: str
    criterion_id: str | None

    def __post_init__(self) -> None:
        _identifier(
            self.artifact_subject_id,
            "artifact_subject.artifact_subject_id",
        )
        _identifier(
            self.artifact_instance_id,
            "artifact_subject.artifact_instance_id",
        )
        if not isinstance(self.subject_reference, SubjectReferenceProjection):
            _fail("artifact_subject.subject_reference is invalid.")
        _controlled_key(
            self.subject_role,
            "artifact_subject.subject_role",
            _SUBJECT_ROLES,
        )
        _controlled(
            self.confirmation_status,
            "artifact_subject.confirmation_status",
            _CONFIRMATION_STATUSES,
        )
        _optional_identifier(self.criterion_id, "artifact_subject.criterion_id")


@dataclass(frozen=True, slots=True)
class AcademicResultArtifactAuthorizationRequest:
    work: ModuleWorkRef
    record_set_id: str
    record_set_revision: int
    source_snapshot_revision: int
    score_record_id: str
    score_evidence_link_id: str
    evidence_reference: EvidenceReferenceProjection
    purpose: str

    def __post_init__(self) -> None:
        if not isinstance(self.work, ModuleWorkRef):
            _fail("authorization work must be a ModuleWorkRef.")
        if self.work.module_id != CONCORD_MODULE_ID:
            _fail('authorization work.module_id must be exactly "concord".')
        if self.record_set_id != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID:
            _fail('record_set_id must be exactly "academic_results".')
        _positive_int(self.record_set_revision, "record_set_revision")
        _positive_int(self.source_snapshot_revision, "source_snapshot_revision")
        _identifier(self.score_record_id, "score_record_id")
        _identifier(self.score_evidence_link_id, "score_evidence_link_id")
        if not isinstance(self.evidence_reference, EvidenceReferenceProjection):
            _fail("evidence_reference must be an EvidenceReferenceProjection.")
        if self.evidence_reference.owning_system != CONCORD_MODULE_ID:
            _fail("Artifact authorization requires Concord-owned evidence.")
        if self.evidence_reference.evidence_kind not in {
            "artifact_instance",
            "artifact_page",
        }:
            _fail(
                "Artifact authorization requires artifact_instance or "
                "artifact_page evidence."
            )
        _public_text(self.purpose, "purpose")


@dataclass(frozen=True, slots=True)
class AcademicResultArtifactAuthorizationDecision:
    status: ArtifactAuthorizationStatus

    def __post_init__(self) -> None:
        _controlled(
            self.status,
            "authorization status",
            frozenset({"allowed", "denied", "unresolved"}),
        )


class AcademicResultArtifactAuthorizationGate(Protocol):
    """Deployment-owned decision gate invoked before native Artifact I/O."""

    def authorize(
        self,
        request: AcademicResultArtifactAuthorizationRequest,
    ) -> AcademicResultArtifactAuthorizationDecision: ...


@dataclass(frozen=True, slots=True)
class AuthorizedAcademicResultArtifact:
    representation: AcademicResultArtifactRepresentation
    work: ModuleWorkRef
    record_set_revision: int
    source_snapshot_revision: int
    score_record_id: str
    score_evidence_link_id: str
    evidence_reference: EvidenceReferenceProjection
    artifact: AcademicResultArtifactProjection
    authors: tuple[AcademicResultArtifactAuthorProjection, ...]
    subjects: tuple[AcademicResultArtifactSubjectProjection, ...]
    media_type: str
    sha256: str
    byte_size: int
    content: bytes

    def __post_init__(self) -> None:
        if self.representation != "returned_artifact_pdf":
            _fail('representation must be exactly "returned_artifact_pdf".')
        if not isinstance(self.work, ModuleWorkRef):
            _fail("result work must be a ModuleWorkRef.")
        if self.work.module_id != CONCORD_MODULE_ID:
            _fail('result work.module_id must be exactly "concord".')
        _positive_int(self.record_set_revision, "record_set_revision")
        _positive_int(self.source_snapshot_revision, "source_snapshot_revision")
        _identifier(self.score_record_id, "score_record_id")
        _identifier(self.score_evidence_link_id, "score_evidence_link_id")
        if not isinstance(self.evidence_reference, EvidenceReferenceProjection):
            _fail("evidence_reference must be an EvidenceReferenceProjection.")
        if (
            self.evidence_reference.owning_system != CONCORD_MODULE_ID
            or self.evidence_reference.evidence_kind
            not in {"artifact_instance", "artifact_page"}
        ):
            _fail("result evidence must be Concord-owned Artifact evidence.")
        if not isinstance(self.artifact, AcademicResultArtifactProjection):
            _fail("artifact must be an AcademicResultArtifactProjection.")
        page_ids = {item.artifact_page_id for item in self.artifact.pages}
        if self.evidence_reference.evidence_kind == "artifact_instance":
            if (
                self.evidence_reference.record_id
                != self.artifact.artifact_instance_id
            ):
                _fail("Artifact Instance evidence identity is inconsistent.")
        elif self.evidence_reference.record_id not in page_ids:
            _fail("Artifact Page evidence identity is inconsistent.")

        authors = tuple(self.authors)
        if any(
            not isinstance(item, AcademicResultArtifactAuthorProjection)
            for item in authors
        ):
            _fail("authors contains an invalid public Author projection.")
        if len({item.artifact_author_id for item in authors}) != len(authors):
            _fail("authors must not repeat Artifact Author identities.")
        if any(
            item.artifact_instance_id != self.artifact.artifact_instance_id
            for item in authors
        ):
            _fail("Artifact Author belongs to another Artifact Instance.")
        object.__setattr__(self, "authors", authors)

        subjects = tuple(self.subjects)
        if any(
            not isinstance(item, AcademicResultArtifactSubjectProjection)
            for item in subjects
        ):
            _fail("subjects contains an invalid public Subject projection.")
        if len({item.artifact_subject_id for item in subjects}) != len(subjects):
            _fail("subjects must not repeat Artifact Subject identities.")
        if any(
            item.artifact_instance_id != self.artifact.artifact_instance_id
            for item in subjects
        ):
            _fail("Artifact Subject belongs to another Artifact Instance.")
        object.__setattr__(self, "subjects", subjects)

        if self.media_type != "application/pdf":
            _fail('media_type must be exactly "application/pdf".')
        _sha256(self.sha256, "sha256")
        if isinstance(self.byte_size, bool) or not isinstance(self.byte_size, int):
            _fail("byte_size must be an integer.")
        if self.byte_size < 1:
            _fail("byte_size must be positive.")
        if type(self.content) is not bytes:
            _fail("content must be immutable bytes.")
        if not self.content.startswith(b"%PDF"):
            _fail("content must contain PDF bytes.")
        if self.byte_size != len(self.content):
            _fail("byte_size does not match content length.")
        if self.sha256 != hashlib.sha256(self.content).hexdigest():
            _fail("sha256 does not match returned Artifact bytes.")


@dataclass(frozen=True, slots=True)
class _AuthorizedAcademicResultArtifactContext:
    request: AcademicResultArtifactAuthorizationRequest
    loaded: ConcordLoadedRecordGraph
    artifact_instance: ArtifactInstance
    evidence_page: ArtifactPage | None
    artifact: AcademicResultArtifactProjection
    authors: tuple[AcademicResultArtifactAuthorProjection, ...]
    subjects: tuple[AcademicResultArtifactSubjectProjection, ...]


def _project_subject_reference(
    value: SubjectReference,
) -> SubjectReferenceProjection:
    return SubjectReferenceProjection(
        subject_kind=value.subject_kind,
        subject_id=value.subject_id,
        owning_system=value.owning_system,
        contract_version=value.contract_version,
    )


def _project_locator(
    value: EvidenceLocator | None,
) -> EvidenceLocatorProjection | None:
    if value is None:
        return None
    return EvidenceLocatorProjection(
        page_number=value.page_number,
        source_page_index=value.source_page_index,
        section_label=value.section_label,
        row_label=value.row_label,
        column_label=value.column_label,
        participant_label=value.participant_label,
        session_id=value.session_id,
    )


def _project_evidence_reference(
    value: EvidenceReference,
) -> EvidenceReferenceProjection:
    publication = value.source_publication_reference
    return EvidenceReferenceProjection(
        evidence_kind=value.evidence_kind,
        owning_system=value.owning_system,
        record_id=value.record_id,
        contract_version=value.contract_version,
        source_publication_reference=(
            CorePublicationReferenceProjection(
                publication_id=publication.publication_id,
                publication_schema_version=publication.publication_schema_version,
            )
            if publication is not None
            else None
        ),
        immutable_source_version=value.immutable_source_version,
        locator=_project_locator(value.locator),
        subject_context=tuple(
            _project_subject_reference(item) for item in value.subject_context
        ),
        moderation_requirement=value.moderation_requirement,
    )


def _project_score_evidence_link(
    value: ScoreEvidenceLink,
) -> ScoreEvidenceLinkProjection:
    return ScoreEvidenceLinkProjection(
        score_evidence_link_id=value.score_evidence_link_id,
        score_record_id=value.score_record_id,
        evidence_reference=_project_evidence_reference(value.evidence_reference),
        evidence_locator=_project_locator(value.evidence_locator),
        subject_context=tuple(
            _project_subject_reference(item) for item in value.subject_context
        ),
        relevance_description=value.relevance_description,
        significance=value.significance,
        moderation_record_id=value.moderation_record_id,
        status=value.status,
        supersedes_score_evidence_link_id=value.supersedes_score_evidence_link_id,
    )


def _project_author_reference(
    value: ParticipantReference | ActorReference | ConcordRecordReference | None,
) -> AcademicResultArtifactAuthorReference | None:
    if value is None:
        return None
    if isinstance(value, ParticipantReference):
        return AcademicResultParticipantReferenceProjection(
            participant_kind=value.participant_kind,
            participant_id=value.participant_id,
            owning_system=value.owning_system,
        )
    if isinstance(value, ActorReference):
        return PublicActor(
            actor_kind=value.actor_kind,
            actor_id=value.actor_id,
            owning_system=value.owning_system,
        )
    if isinstance(value, ConcordRecordReference):
        return RecordReferenceProjection(
            module_id=CONCORD_MODULE_ID,
            record_kind=value.record_kind,
            record_id=value.record_id,
            contract_version=value.contract_version,
        )
    raise ConcordAcademicResultArtifactIntegrityError(
        "Historical Artifact Author reference is invalid."
    )


def _project_artifact_author(
    value: ArtifactAuthor,
) -> AcademicResultArtifactAuthorProjection:
    return AcademicResultArtifactAuthorProjection(
        artifact_author_id=value.artifact_author_id,
        artifact_instance_id=value.artifact_instance_id,
        author_reference=_project_author_reference(value.author_reference),
        authorship_mode=value.authorship_mode,
        attribution_status=value.attribution_status,
        represented_group_id=value.represented_group_id,
        representation_status=value.representation_status,
    )


def _project_artifact_subject(
    value: ArtifactSubject,
) -> AcademicResultArtifactSubjectProjection:
    return AcademicResultArtifactSubjectProjection(
        artifact_subject_id=value.artifact_subject_id,
        artifact_instance_id=value.artifact_instance_id,
        subject_reference=_project_subject_reference(value.subject_reference),
        subject_role=value.subject_role,
        confirmation_status=value.confirmation_status,
        criterion_id=value.criterion_id,
    )


def _current_artifact_authors(
    graph: ConcordRecordGraph,
    artifact_instance_id: str,
) -> tuple[ArtifactAuthor, ...]:
    """Return current Author associations as of this exact historical graph."""
    superseded_ids = {
        item.supersedes_artifact_author_id
        for item in graph.artifact_authors
        if item.supersedes_artifact_author_id is not None
    }
    return tuple(
        item
        for item in graph.artifact_authors
        if item.artifact_instance_id == artifact_instance_id
        and item.artifact_author_id not in superseded_ids
        and item.attribution_status != "superseded"
    )


def _current_artifact_subjects(
    graph: ConcordRecordGraph,
    artifact_instance_id: str,
) -> tuple[ArtifactSubject, ...]:
    """Return current Subject associations as of this exact historical graph."""
    superseded_ids = {
        item.supersedes_artifact_subject_id
        for item in graph.artifact_subjects
        if item.supersedes_artifact_subject_id is not None
    }
    return tuple(
        item
        for item in graph.artifact_subjects
        if item.artifact_instance_id == artifact_instance_id
        and item.artifact_subject_id not in superseded_ids
        and item.confirmation_status != "superseded"
    )


def _project_artifact(
    graph: ConcordRecordGraph,
    artifact: ArtifactInstance,
) -> AcademicResultArtifactProjection:
    page_by_id = {item.artifact_page_id: item for item in graph.artifact_pages}
    pages: list[AcademicResultArtifactPageProjection] = []
    for page_id in artifact.page_ids:
        page = page_by_id.get(page_id)
        if page is None:
            raise ConcordAcademicResultArtifactIntegrityError(
                "Historical Artifact references a missing Artifact Page."
            )
        if page.artifact_instance_id != artifact.artifact_instance_id:
            raise ConcordAcademicResultArtifactIntegrityError(
                "Historical Artifact Page belongs to another Artifact Instance."
            )
        pages.append(
            AcademicResultArtifactPageProjection(
                artifact_page_id=page.artifact_page_id,
                page_number=page.page_number,
            )
        )
    return AcademicResultArtifactProjection(
        artifact_instance_id=artifact.artifact_instance_id,
        artifact_category=artifact.artifact_category,
        session_id=artifact.session_id,
        group_id=artifact.group_id,
        pages=tuple(pages),
        privacy_classification=artifact.privacy_policy.classification,
    )


def _validated_artifact_manifest(
    manifest: AcademicResultManifest,
) -> AcademicResultManifest:
    invalid = False
    try:
        checked = validate_academic_result_manifest(manifest)
    except ConcordAcademicResultManifestValidationError:
        invalid = True
        checked = None
    if invalid or checked is None:
        raise ConcordAcademicResultArtifactValidationError(
            "Academic-result manifest model is invalid."
        )
    return checked


def _manifest_artifact_link(
    manifest: AcademicResultManifest,
    score_evidence_link_id: str,
) -> ScoreEvidenceLinkProjection:
    _identifier(score_evidence_link_id, "score_evidence_link_id")
    missing = False
    try:
        link = lookup_academic_result_score_evidence_link(
            manifest,
            score_evidence_link_id,
        )
    except ConcordAcademicResultReaderNotFoundError:
        missing = True
        link = None
    if missing or link is None:
        raise ConcordAcademicResultArtifactNotFoundError(
            "Requested evidence link is not represented in this manifest."
        )
    evidence = link.evidence_reference
    if (
        evidence.owning_system != CONCORD_MODULE_ID
        or evidence.evidence_kind not in {"artifact_instance", "artifact_page"}
    ):
        raise ConcordAcademicResultArtifactValidationError(
            "Requested evidence link is not Concord-owned Artifact evidence."
        )
    return link


def _authorize_artifact_request(
    request: AcademicResultArtifactAuthorizationRequest,
    authorization_gate: AcademicResultArtifactAuthorizationGate,
) -> None:
    gate_failed = False
    try:
        decision = authorization_gate.authorize(request)
    except Exception:
        gate_failed = True
        decision = None
    if gate_failed:
        raise ConcordAcademicResultArtifactAuthorizationError(
            "Artifact authorization could not be affirmed."
        )
    if (
        not isinstance(decision, AcademicResultArtifactAuthorizationDecision)
        or decision.status != "allowed"
    ):
        raise ConcordAcademicResultArtifactAuthorizationError(
            "Artifact authorization was not affirmed."
        )


def _load_authorized_historical_graph(
    workspace_root: str | Path,
    request: AcademicResultArtifactAuthorizationRequest,
) -> ConcordLoadedRecordGraph:
    failure: str | None = None
    try:
        loaded = load_record_graph_at_snapshot(
            workspace_root,
            request.work,
            request.source_snapshot_revision,
        )
    except ConcordStorageNotFoundError:
        failure = "not_found"
        loaded = None
    except ConcordStorageError:
        failure = "integrity"
        loaded = None
    if failure == "not_found":
        raise ConcordAcademicResultArtifactNotFoundError(
            "Authorized historical Concord state is unavailable."
        )
    if failure == "integrity" or loaded is None:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Authorized historical Concord state could not be verified."
        )
    if loaded.snapshot_revision != request.source_snapshot_revision:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical Concord snapshot revision is inconsistent."
        )
    if not isinstance(loaded.graph, ConcordRecordGraph):
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical Concord graph is invalid."
        )
    return loaded


def _verify_historical_evidence(
    loaded: ConcordLoadedRecordGraph,
    request: AcademicResultArtifactAuthorizationRequest,
    manifest_link: ScoreEvidenceLinkProjection,
) -> tuple[ArtifactInstance, ArtifactPage | None]:
    graph = loaded.graph
    if (
        len(graph.activities) != 1
        or graph.activities[0].work_reference != request.work
    ):
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical Concord Activity identity is inconsistent."
        )

    native_score = next(
        (
            item
            for item in graph.score_records
            if item.score_record_id == request.score_record_id
        ),
        None,
    )
    if native_score is None:
        raise ConcordAcademicResultArtifactNotFoundError(
            "Manifest-required historical Score is unavailable."
        )
    if native_score.activity_id != request.work.work_id:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical Score belongs to another Activity."
        )

    native_link = next(
        (
            item
            for item in graph.score_evidence_links
            if item.score_evidence_link_id == request.score_evidence_link_id
        ),
        None,
    )
    if native_link is None:
        raise ConcordAcademicResultArtifactNotFoundError(
            "Manifest-required historical evidence link is unavailable."
        )
    if native_link.score_record_id != native_score.score_record_id:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical evidence link belongs to another Score."
        )
    projection_failed = False
    try:
        projected_link = _project_score_evidence_link(native_link)
    except (TypeError, ValueError):
        projection_failed = True
        projected_link = None
    if projection_failed or projected_link is None:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical evidence link cannot reproduce the public projection."
        )
    if projected_link != manifest_link:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical evidence link disagrees with the manifest projection."
        )

    evidence = native_link.evidence_reference
    artifact_by_id = {
        item.artifact_instance_id: item for item in graph.artifact_instances
    }
    page_by_id = {item.artifact_page_id: item for item in graph.artifact_pages}
    evidence_page: ArtifactPage | None = None
    if evidence.evidence_kind == "artifact_instance":
        artifact = artifact_by_id.get(evidence.record_id)
        if artifact is None:
            raise ConcordAcademicResultArtifactNotFoundError(
                "Manifest-required historical Artifact is unavailable."
            )
    elif evidence.evidence_kind == "artifact_page":
        evidence_page = page_by_id.get(evidence.record_id)
        if evidence_page is None:
            raise ConcordAcademicResultArtifactNotFoundError(
                "Manifest-required historical Artifact Page is unavailable."
            )
        artifact = artifact_by_id.get(evidence_page.artifact_instance_id)
        if artifact is None:
            raise ConcordAcademicResultArtifactNotFoundError(
                "Historical Artifact Page parent is unavailable."
            )
    else:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical evidence is not Concord Artifact evidence."
        )

    if artifact.activity_id != request.work.work_id:
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical Artifact belongs to another Activity."
        )
    if (
        evidence_page is not None
        and evidence_page.artifact_page_id not in artifact.page_ids
    ):
        raise ConcordAcademicResultArtifactIntegrityError(
            "Historical Artifact Page is not selected by its Artifact Instance."
        )
    return artifact, evidence_page


def _resolve_authorized_academic_result_artifact_context(
    workspace_root: str | Path,
    manifest: AcademicResultManifest,
    score_evidence_link_id: str,
    *,
    purpose: str,
    authorization_gate: AcademicResultArtifactAuthorizationGate,
) -> _AuthorizedAcademicResultArtifactContext:
    """Authorize first, then verify exact historical Concord Artifact lineage."""
    checked = _validated_artifact_manifest(manifest)
    manifest_link = _manifest_artifact_link(
        checked,
        score_evidence_link_id,
    )
    request = AcademicResultArtifactAuthorizationRequest(
        work=checked.work,
        record_set_id=checked.record_set.record_set_id,
        record_set_revision=checked.record_set.revision,
        source_snapshot_revision=checked.projection.source_snapshot_revision,
        score_record_id=manifest_link.score_record_id,
        score_evidence_link_id=manifest_link.score_evidence_link_id,
        evidence_reference=manifest_link.evidence_reference,
        purpose=purpose,
    )

    # This is intentionally the last operation before any native workspace I/O.
    _authorize_artifact_request(request, authorization_gate)

    loaded = _load_authorized_historical_graph(workspace_root, request)
    artifact_instance, evidence_page = _verify_historical_evidence(
        loaded,
        request,
        manifest_link,
    )
    graph = loaded.graph
    artifact = _project_artifact(graph, artifact_instance)
    authors = tuple(
        _project_artifact_author(item)
        for item in _current_artifact_authors(
            graph,
            artifact_instance.artifact_instance_id,
        )
    )
    subjects = tuple(
        _project_artifact_subject(item)
        for item in _current_artifact_subjects(
            graph,
            artifact_instance.artifact_instance_id,
        )
    )
    return _AuthorizedAcademicResultArtifactContext(
        request=request,
        loaded=loaded,
        artifact_instance=artifact_instance,
        evidence_page=evidence_page,
        artifact=artifact,
        authors=authors,
        subjects=subjects,
    )


def read_authorized_academic_result_artifact(
    workspace_root: str | Path,
    manifest: AcademicResultManifest,
    score_evidence_link_id: str,
    *,
    purpose: str,
    authorization_gate: AcademicResultArtifactAuthorizationGate,
) -> AuthorizedAcademicResultArtifact:
    """Return one authorization-gated bounded Concord Artifact PDF."""
    context = _resolve_authorized_academic_result_artifact_context(
        workspace_root,
        manifest,
        score_evidence_link_id,
        purpose=purpose,
        authorization_gate=authorization_gate,
    )

    # Import only after authorization and historical identity verification.
    # The neutral rendering layer contains no workflow or publication orchestration.
    from concord.artifact_rendering import (
        ReturnedArtifactRenderAmbiguityError,
        ReturnedArtifactRenderError,
        ReturnedArtifactRenderIntegrityError,
        ReturnedArtifactRenderUnavailableError,
        render_returned_artifact_pdf,
    )

    render_failure: str | None = None
    try:
        content = render_returned_artifact_pdf(
            workspace_root,
            context.loaded.graph,
            context.artifact_instance,
            evidence_page=context.evidence_page,
        )
    except ReturnedArtifactRenderAmbiguityError:
        render_failure = "ambiguity"
        content = None
    except ReturnedArtifactRenderUnavailableError:
        render_failure = "unavailable"
        content = None
    except ReturnedArtifactRenderIntegrityError:
        render_failure = "integrity"
        content = None
    except ReturnedArtifactRenderError:
        render_failure = "unsupported"
        content = None

    if render_failure == "ambiguity":
        raise ConcordAcademicResultArtifactAmbiguityError(
            "Authorized Artifact evidence has ambiguous returned-source lineage."
        )
    if render_failure == "integrity":
        raise ConcordAcademicResultArtifactIntegrityError(
            "Authorized Artifact source bytes could not be verified."
        )
    if render_failure == "unavailable":
        raise ConcordAcademicResultArtifactUnavailableError(
            "Authorized Artifact evidence has no complete returned representation."
        )
    if render_failure == "unsupported" or content is None:
        raise ConcordAcademicResultArtifactUnavailableError(
            "Authorized Artifact evidence cannot produce a returned representation."
        )

    return AuthorizedAcademicResultArtifact(
        representation="returned_artifact_pdf",
        work=context.request.work,
        record_set_revision=context.request.record_set_revision,
        source_snapshot_revision=context.request.source_snapshot_revision,
        score_record_id=context.request.score_record_id,
        score_evidence_link_id=context.request.score_evidence_link_id,
        evidence_reference=context.request.evidence_reference,
        artifact=context.artifact,
        authors=context.authors,
        subjects=context.subjects,
        media_type="application/pdf",
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
        content=content,
    )


__all__ = (
    "AcademicResultArtifactAuthorizationDecision",
    "AcademicResultArtifactAuthorizationGate",
    "AcademicResultArtifactAuthorizationRequest",
    "AcademicResultArtifactAuthorProjection",
    "AcademicResultArtifactAuthorReference",
    "AcademicResultArtifactPageProjection",
    "AcademicResultArtifactProjection",
    "AcademicResultArtifactRepresentation",
    "AcademicResultArtifactSubjectProjection",
    "AcademicResultParticipantReferenceProjection",
    "ArtifactAuthorizationStatus",
    "AuthorizedAcademicResultArtifact",
    "ConcordAcademicResultArtifactAmbiguityError",
    "ConcordAcademicResultArtifactAuthorizationError",
    "ConcordAcademicResultArtifactError",
    "ConcordAcademicResultArtifactIntegrityError",
    "ConcordAcademicResultArtifactNotFoundError",
    "ConcordAcademicResultArtifactUnavailableError",
    "ConcordAcademicResultArtifactValidationError",
    "read_authorized_academic_result_artifact",
)
