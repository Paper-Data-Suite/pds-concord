"""Immutable generation of Concord Academic Result Manifest v1."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, TypeAlias, cast

from pds_core.academic_work_registrations import AcademicWorkRegistration
from pds_core.publication_records import validate_publication_manifest_path
from pds_core.publication_storage import (
    PublicationManifestError,
    PublicationManifestIntegrityError,
    PublicationManifestNotFoundError,
    verify_publication_manifest,
)
from pds_core.registry_services import (
    RegistryServiceError,
    RegistryServiceNotFoundError,
    get_canonical_publication_record,
)
from pds_core.routes import safe_module_work_descendant
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.academic_result_manifest import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    AcademicResultManifest,
    ActivityContextProjection,
    ConcordAcademicResultManifestValidationError,
    CorePublicationReferenceProjection,
    CriterionProjection,
    CriterionSetProjection,
    EvidenceLocatorProjection,
    EvidenceReferenceProjection,
    ManifestProjection,
    ManifestRecordSet,
    ModerationProjection,
    PrivacyProjection,
    PublicActor,
    RecordReferenceProjection,
    RevisionReason,
    ScaleLevelProjection,
    ScoreEvidenceLinkProjection,
    ScoreProjection,
    ScoringScaleProjection,
    StandardsResultProjection,
    StatusReasonProjection,
    SubjectReferenceProjection,
    TargetReferenceProjection,
    academic_result_manifest_from_bytes,
    academic_result_manifest_to_bytes,
    derive_manifest_capabilities,
    with_semantic_projection_digest,
)
from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationError,
    ConcordAcademicWorkRegistrationIntegrityError,
    ConcordAcademicWorkRegistrationNotFoundError,
    ConcordAcademicWorkRegistrationValidationError,
    load_current_concord_academic_work_registration,
)
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ActorReference,
    ConcordRecordReference,
    Criterion,
    CriterionSet,
    EvidenceLocator,
    EvidenceReference,
    ModerationRecord,
    PrivacyPolicy,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
    StatusReason,
    SubjectReference,
)
from concord.pds_contract import (
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)
from concord.storage import (
    load_current_record_graph,
    load_current_snapshot,
)
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStorageError,
    ConcordStorageIntegrityError,
    ConcordStorageNotFoundError,
    ConcordStorageReadError,
    ConcordStorageValidationError,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor

ManifestGenerationDisposition: TypeAlias = Literal["created", "existing"]
ManifestPreviewDisposition: TypeAlias = Literal["would_create", "would_reuse"]

_RECORD_SET_RELATIVE_DIR = "exports/manifests/academic_results"
_LOCK_NAME = ".write.lock"


class ConcordManifestGenerationError(Exception):
    """Base error for Concord manifest generation and immutable storage."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self._lock_cleanup_failure: ManifestGenerationCleanupFailure | None = None

    @property
    def lock_cleanup_failure(self) -> ManifestGenerationCleanupFailure | None:
        return self._lock_cleanup_failure

    def _record_lock_cleanup_failure(
        self, failure: ManifestGenerationCleanupFailure
    ) -> None:
        self._lock_cleanup_failure = failure


class ConcordManifestGenerationValidationError(
    ConcordManifestGenerationError, ValueError
):
    """Generation input or native Concord state is not publishable."""


class ConcordManifestGenerationNotFoundError(ConcordManifestGenerationError):
    """Required managed native/Core state does not exist."""


class ConcordManifestGenerationConflictError(ConcordManifestGenerationError):
    """Expected native state or immutable producer storage has moved."""


class ConcordManifestGenerationIntegrityError(ConcordManifestGenerationError):
    """Canonical native, registry, or manifest state is contradictory."""


class ConcordManifestGenerationWriteError(ConcordManifestGenerationError):
    """Producer-owned immutable storage could not be completed safely."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.incomplete_target_cleanup_failure: OSError | None = None


@dataclass(frozen=True, slots=True)
class ManifestGenerationCleanupFailure:
    path: Path
    relative_path: str
    message: str
    error: OSError

    def __post_init__(self) -> None:
        if not isinstance(self.path, Path):
            raise TypeError("cleanup failure path must be a Path.")
        if not isinstance(self.relative_path, str) or not self.relative_path:
            raise ValueError("cleanup failure relative_path must be nonempty.")
        if not isinstance(self.message, str) or not self.message:
            raise ValueError("cleanup failure message must be nonempty.")
        if not isinstance(self.error, OSError):
            raise TypeError("cleanup failure error must be an OSError.")


@dataclass(frozen=True, slots=True)
class ManifestGenerationPartialState:
    operation: str
    work: ModuleWorkRef
    revision: int
    path: Path
    relative_path: str
    expected_sha256: str | None
    durable_file_exists: bool
    lock_cleanup_failure: ManifestGenerationCleanupFailure | None = None


class ConcordManifestGenerationPartialSuccessError(
    ConcordManifestGenerationWriteError
):
    """Manifest bytes are durable but completion/verification is uncertain."""

    def __init__(
        self,
        message: str,
        state: ManifestGenerationPartialState,
    ) -> None:
        super().__init__(message)
        self.state = state
        if state.lock_cleanup_failure is not None:
            self._record_lock_cleanup_failure(state.lock_cleanup_failure)


class _DurableRevisionWriteError(Exception):
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class GenerateAcademicResultManifestRequest:
    class_id: str
    activity_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    revision_reason: RevisionReason

    def __post_init__(self) -> None:
        try:
            ModuleWorkRef(
                module_id=CONCORD_MODULE_ID,
                class_id=self.class_id,
                work_id=self.activity_id,
            )
        except Exception as error:
            raise ConcordManifestGenerationValidationError(
                "class_id and activity_id must be safe identifiers."
            ) from error
        if (
            isinstance(self.expected_snapshot_revision, bool)
            or not isinstance(self.expected_snapshot_revision, int)
            or self.expected_snapshot_revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "expected_snapshot_revision must be a positive integer."
            )
        if not isinstance(self.actor, WorkflowActor):
            raise ConcordManifestGenerationValidationError(
                "actor must be a WorkflowActor."
            )
        try:
            ManifestProjection(
                source_snapshot_revision=1,
                projection_digest_algorithm="sha256",
                projection_digest="0" * 64,
                generated_by=_workflow_actor(self.actor),
                revision_reason=self.revision_reason,
            )
        except Exception as error:
            raise ConcordManifestGenerationValidationError(
                "revision_reason is not a supported manifest revision reason."
            ) from error


@dataclass(frozen=True, slots=True)
class ManifestGenerationContext:
    work: ModuleWorkRef
    graph: ConcordRecordGraph
    snapshot_revision: int
    snapshot_sha256: str
    registration: AcademicWorkRegistration

    def __post_init__(self) -> None:
        if not isinstance(self.work, ModuleWorkRef):
            raise ConcordManifestGenerationValidationError(
                "context work must be a ModuleWorkRef."
            )
        if self.work.module_id != CONCORD_MODULE_ID:
            raise ConcordManifestGenerationValidationError(
                'context work.module_id must be "concord".'
            )
        if not isinstance(self.graph, ConcordRecordGraph):
            raise ConcordManifestGenerationValidationError(
                "context graph must be a ConcordRecordGraph."
            )
        if (
            isinstance(self.snapshot_revision, bool)
            or not isinstance(self.snapshot_revision, int)
            or self.snapshot_revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "context snapshot_revision must be positive."
            )
        if (
            not isinstance(self.snapshot_sha256, str)
            or len(self.snapshot_sha256) != 64
        ):
            raise ConcordManifestGenerationValidationError(
                "context snapshot_sha256 must be a SHA-256 digest."
            )
        if not isinstance(self.registration, AcademicWorkRegistration):
            raise ConcordManifestGenerationValidationError(
                "context registration is invalid."
            )


@dataclass(frozen=True, slots=True)
class StoredAcademicResultManifest:
    manifest: AcademicResultManifest
    revision: int
    path: Path
    relative_path: str
    content: bytes
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, AcademicResultManifest):
            raise ConcordManifestGenerationValidationError(
                "stored manifest has an invalid manifest value."
            )
        if (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "stored manifest revision must be positive."
            )
        if not isinstance(self.path, Path):
            raise ConcordManifestGenerationValidationError(
                "stored manifest path must be a Path."
            )
        if not isinstance(self.relative_path, str) or not self.relative_path:
            raise ConcordManifestGenerationValidationError(
                "stored manifest relative_path must be nonempty."
            )
        if not isinstance(self.content, bytes):
            raise ConcordManifestGenerationValidationError(
                "stored manifest content must be bytes."
            )
        expected_digest = hashlib.sha256(self.content).hexdigest()
        if self.sha256 != expected_digest:
            raise ConcordManifestGenerationIntegrityError(
                "stored manifest digest disagrees with its bytes."
            )
        decoded = academic_result_manifest_from_bytes(self.content)
        if decoded != self.manifest:
            raise ConcordManifestGenerationIntegrityError(
                "stored manifest bytes disagree with the typed manifest."
            )
        if decoded.record_set.revision != self.revision:
            raise ConcordManifestGenerationIntegrityError(
                "stored manifest revision disagrees with its record-set revision."
            )
        expected_relative = academic_result_manifest_relative_path(
            decoded.work, self.revision
        )
        if self.relative_path != expected_relative:
            raise ConcordManifestGenerationIntegrityError(
                "stored manifest relative path disagrees with its identity."
            )


@dataclass(frozen=True, slots=True)
class AcademicResultManifestPreview:
    """Read-only projection of what manifest generation would do."""

    disposition: ManifestPreviewDisposition
    manifest: AcademicResultManifest
    revision: int
    path: Path
    relative_path: str
    content: bytes
    sha256: str
    registration_revision: int
    source_snapshot_revision: int

    def __post_init__(self) -> None:
        if self.disposition not in {"would_create", "would_reuse"}:
            raise ConcordManifestGenerationValidationError(
                "preview disposition is invalid."
            )
        if not isinstance(self.manifest, AcademicResultManifest):
            raise ConcordManifestGenerationValidationError(
                "preview manifest is invalid."
            )
        if (
            isinstance(self.revision, bool)
            or not isinstance(self.revision, int)
            or self.revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "preview revision must be positive."
            )
        if not isinstance(self.path, Path):
            raise ConcordManifestGenerationValidationError(
                "preview path must be a Path."
            )
        if not isinstance(self.relative_path, str) or not self.relative_path:
            raise ConcordManifestGenerationValidationError(
                "preview relative_path must be nonempty."
            )
        if not isinstance(self.content, bytes):
            raise ConcordManifestGenerationValidationError(
                "preview content must be bytes."
            )
        if self.sha256 != hashlib.sha256(self.content).hexdigest():
            raise ConcordManifestGenerationIntegrityError(
                "preview SHA-256 disagrees with its bytes."
            )
        stored = StoredAcademicResultManifest(
            manifest=self.manifest,
            revision=self.revision,
            path=self.path,
            relative_path=self.relative_path,
            content=self.content,
            sha256=self.sha256,
        )
        del stored
        if (
            isinstance(self.registration_revision, bool)
            or not isinstance(self.registration_revision, int)
            or self.registration_revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "preview registration_revision must be positive."
            )
        if (
            isinstance(self.source_snapshot_revision, bool)
            or not isinstance(self.source_snapshot_revision, int)
            or self.source_snapshot_revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "preview source_snapshot_revision must be positive."
            )


@dataclass(frozen=True, slots=True)
class AcademicResultManifestGenerationResult:
    disposition: ManifestGenerationDisposition
    manifest: AcademicResultManifest
    revision: int
    path: Path
    relative_path: str
    content: bytes
    sha256: str
    registration_revision: int
    source_snapshot_revision: int

    def __post_init__(self) -> None:
        if self.disposition not in {"created", "existing"}:
            raise ConcordManifestGenerationValidationError(
                "generation disposition is invalid."
            )
        stored = StoredAcademicResultManifest(
            manifest=self.manifest,
            revision=self.revision,
            path=self.path,
            relative_path=self.relative_path,
            content=self.content,
            sha256=self.sha256,
        )
        del stored
        if (
            isinstance(self.registration_revision, bool)
            or not isinstance(self.registration_revision, int)
            or self.registration_revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "registration_revision must be positive."
            )
        if (
            isinstance(self.source_snapshot_revision, bool)
            or not isinstance(self.source_snapshot_revision, int)
            or self.source_snapshot_revision < 1
        ):
            raise ConcordManifestGenerationValidationError(
                "source_snapshot_revision must be positive."
            )


def _workflow_actor(value: WorkflowActor) -> PublicActor:
    return PublicActor(
        actor_kind=value.actor_kind,
        actor_id=value.actor_id,
        owning_system=value.owning_system,
    )


def _actor(value: ActorReference) -> PublicActor:
    return PublicActor(
        actor_kind=value.actor_kind,
        actor_id=value.actor_id,
        owning_system=value.owning_system,
    )


def _subject(value: SubjectReference) -> SubjectReferenceProjection:
    return SubjectReferenceProjection(
        subject_kind=value.subject_kind,
        subject_id=value.subject_id,
        owning_system=value.owning_system,
        contract_version=value.contract_version,
    )


def _target(value: ScoreTargetReference) -> TargetReferenceProjection:
    return TargetReferenceProjection(
        target_kind=value.target_kind,
        target_id=value.target_id,
        owning_system=value.owning_system,
        contract_version=value.contract_version,
    )


def _record_reference(
    value: ModuleRecordRef | ConcordRecordReference,
) -> RecordReferenceProjection:
    if isinstance(value, ModuleRecordRef):
        return RecordReferenceProjection(
            module_id=value.module_id,
            record_kind=value.record_kind,
            record_id=value.record_id,
            contract_version=value.contract_version,
        )
    return RecordReferenceProjection(
        module_id=CONCORD_MODULE_ID,
        record_kind=value.record_kind,
        record_id=value.record_id,
        contract_version=value.contract_version,
    )


def _locator(value: EvidenceLocator | None) -> EvidenceLocatorProjection | None:
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


def _evidence_reference(
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
        locator=_locator(value.locator),
        subject_context=tuple(_subject(item) for item in value.subject_context),
        moderation_requirement=value.moderation_requirement,
    )


def _status_reason(
    value: StatusReason | None,
) -> StatusReasonProjection | None:
    if value is None:
        return None
    return StatusReasonProjection(
        reason_code=value.reason_code,
        recorded_by=_actor(value.recorded_by),
        recorded_at=_native_timestamp(value.recorded_at, "status_reason.recorded_at"),
        related_record=(
            _record_reference(value.related_record)
            if value.related_record is not None
            else None
        ),
    )


def _native_timestamp(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ConcordManifestGenerationIntegrityError(
            f"{field} is not a valid native timestamp."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ConcordManifestGenerationIntegrityError(
            f"{field} must be timezone-aware."
        )
    return parsed


def _criterion_set(value: CriterionSet) -> CriterionSetProjection:
    return CriterionSetProjection(
        criterion_set_id=value.criterion_set_id,
        lineage_id=value.lineage_id,
        revision=value.revision,
        criterion_set_kind=value.criterion_set_kind,
        scope=value.scope,
        criterion_ids=value.criterion_ids,
        status=value.status,
        supersedes_criterion_set_id=value.supersedes_criterion_set_id,
        standards_profile_id=value.standards_profile_id,
    )


def _criterion(value: Criterion) -> CriterionProjection:
    return CriterionProjection(
        criterion_id=value.criterion_id,
        criterion_set_id=value.criterion_set_id,
        key=value.key,
        label=value.label,
        definition=value.definition,
        criterion_kind=value.criterion_kind,
        supported_target_kinds=value.supported_target_kinds,
        status=value.status,
        standard_id=value.standard_id,
        alignment_standard_ids=value.alignment_standard_ids,
        default_scoring_scale_id=value.default_scoring_scale_id,
    )


def _scale(value: ScoringScale) -> ScoringScaleProjection:
    return ScoringScaleProjection(
        scoring_scale_id=value.scoring_scale_id,
        lineage_id=value.lineage_id,
        name=value.name,
        revision=value.revision,
        scale_type=value.scale_type,
        levels=tuple(
            ScaleLevelProjection(
                value=item.value,
                label=item.label,
                meaning=item.meaning,
                position=item.position,
                description=item.description,
            )
            for item in value.levels
        ),
        status=value.status,
        supersedes_scoring_scale_id=value.supersedes_scoring_scale_id,
    )


def _score_current_states(
    values: tuple[ScoreRecord, ...],
) -> dict[str, Literal["current", "superseded"]]:
    predecessor_ids = {
        value.supersedes_score_record_id
        for value in values
        if value.supersedes_score_record_id is not None
    }
    return {
        value.score_record_id: (
            "superseded"
            if value.score_record_id in predecessor_ids
            else "current"
        )
        for value in values
    }


def _moderation_current_states(
    values: tuple[ModerationRecord, ...],
) -> dict[str, Literal["current", "superseded"]]:
    predecessor_ids = {
        value.supersedes_moderation_record_id
        for value in values
        if value.supersedes_moderation_record_id is not None
    }
    return {
        value.moderation_record_id: (
            "superseded"
            if value.moderation_record_id in predecessor_ids
            else "current"
        )
        for value in values
    }


def _score(
    value: ScoreRecord,
    states: dict[str, Literal["current", "superseded"]],
) -> ScoreProjection:
    return ScoreProjection(
        score_record_id=value.score_record_id,
        activity_id=value.activity_id,
        session_id=value.session_id,
        target_reference=_target(value.target_reference),
        criterion_id=value.criterion_id,
        score_kind=cast(Literal["standard_backed", "local"], value.score_kind),
        standard_id=value.standard_id,
        scoring_scale_id=value.scoring_scale_id,
        disposition=cast(
            Literal[
                "scored",
                "insufficient_evidence",
                "absent",
                "excused",
                "not_observed",
                "not_applicable",
                "deferred",
            ],
            value.disposition,
        ),
        value=value.value,
        basis=cast(
            Literal[
                "linked_evidence",
                "professional_judgment",
                "mixed_basis",
            ],
            value.basis,
        ),
        scorer=_actor(value.scorer),
        scored_at=_native_timestamp(value.scored_at, "score.scored_at"),
        moderation_complete=value.moderation_complete,
        status_reason=_status_reason(value.status_reason),
        supersedes_score_record_id=value.supersedes_score_record_id,
        current_state=states[value.score_record_id],
    )


def _score_link(value: ScoreEvidenceLink) -> ScoreEvidenceLinkProjection:
    return ScoreEvidenceLinkProjection(
        score_evidence_link_id=value.score_evidence_link_id,
        score_record_id=value.score_record_id,
        evidence_reference=_evidence_reference(value.evidence_reference),
        evidence_locator=_locator(value.evidence_locator),
        subject_context=tuple(_subject(item) for item in value.subject_context),
        relevance_description=value.relevance_description,
        significance=value.significance,
        moderation_record_id=value.moderation_record_id,
        status=value.status,
        supersedes_score_evidence_link_id=value.supersedes_score_evidence_link_id,
    )


def _moderation(
    value: ModerationRecord,
    states: dict[str, Literal["current", "superseded"]],
) -> ModerationProjection:
    return ModerationProjection(
        moderation_record_id=value.moderation_record_id,
        target_evidence_reference=_evidence_reference(
            value.target_evidence_reference
        ),
        target_subject_references=tuple(
            _subject(item) for item in value.target_subject_references
        ),
        status=value.status,
        permitted_use=value.permitted_use,
        qualification=value.qualification,
        supersedes_moderation_record_id=value.supersedes_moderation_record_id,
        current_state=states[value.moderation_record_id],
    )


def _public_privacy(value: PrivacyPolicy) -> PrivacyProjection:
    return PrivacyProjection(
        classification=value.classification,
        audience_references=tuple(
            _subject(item) for item in value.audience_references
        ),
        policy_reference=(
            _record_reference(value.policy_reference)
            if value.policy_reference is not None
            else None
        ),
        inherited_from=(
            _record_reference(value.inherited_from)
            if value.inherited_from is not None
            else None
        ),
    )


def _resolve_effective_privacy(
    values: Iterable[PrivacyPolicy],
) -> PrivacyProjection:
    projected = tuple(_public_privacy(value) for value in values)
    restricted = PrivacyProjection(
        classification="teacher_restricted",
        audience_references=(),
        policy_reference=None,
        inherited_from=None,
    )
    if not projected:
        return restricted

    first = projected[0]
    if all(item == first for item in projected):
        return first

    if any(
        value.classification == "teacher_restricted"
        for value in projected
    ):
        return restricted

    if any(
        value.classification in {"external_policy", "inherited"}
        for value in projected
    ):
        return restricted

    narrower_classes = {
        value.classification
        for value in projected
        if value.classification != "classroom_shared"
    }
    if len(narrower_classes) != 1:
        return restricted

    classification = next(iter(narrower_classes))
    narrower = tuple(
        value
        for value in projected
        if value.classification == classification
    )
    narrowest = narrower[0]
    if all(item == narrowest for item in narrower):
        return narrowest
    return restricted

def _verify_external_publication_reference(
    root: Path,
    reference: EvidenceReference,
) -> None:
    source = reference.source_publication_reference
    if source is None:
        return
    try:
        publication = get_canonical_publication_record(
            root, source.publication_id
        )
    except RegistryServiceNotFoundError as error:
        raise ConcordManifestGenerationNotFoundError(
            "Referenced Core Publication Record is unavailable: "
            f"{source.publication_id}"
        ) from error
    except RegistryServiceError as error:
        raise ConcordManifestGenerationIntegrityError(
            "Referenced Core Publication Record could not be verified."
        ) from error

    expected_schema = source.publication_schema_version
    if (
        expected_schema is not None
        and publication.schema_version != expected_schema
    ):
        raise ConcordManifestGenerationIntegrityError(
            "Referenced Core Publication schema version does not match "
            "the Concord evidence reference."
        )
    if publication.work.module_id != reference.owning_system:
        raise ConcordManifestGenerationIntegrityError(
            "Referenced Core Publication producer module does not match "
            "the Concord evidence owner."
        )
    try:
        verify_publication_manifest(root, publication)
    except PublicationManifestNotFoundError as error:
        raise ConcordManifestGenerationNotFoundError(
            "Referenced external publication manifest is unavailable."
        ) from error
    except PublicationManifestIntegrityError as error:
        raise ConcordManifestGenerationIntegrityError(
            "Referenced external publication manifest failed digest or "
            "containment verification."
        ) from error
    except PublicationManifestError as error:
        raise ConcordManifestGenerationIntegrityError(
            "Referenced external publication manifest could not be verified."
        ) from error


def _verify_external_lineage(root: Path, graph: ConcordRecordGraph) -> None:
    references: list[EvidenceReference] = []
    references.extend(
        item.evidence_reference for item in graph.score_evidence_links
    )
    references.extend(
        item.target_evidence_reference for item in graph.moderation_records
    )
    seen: set[EvidenceReference] = set()
    for reference in references:
        if reference in seen:
            continue
        seen.add(reference)
        if (
            reference.source_publication_reference is not None
        ):
            _verify_external_publication_reference(root, reference)
        if (
            reference.owning_system != CONCORD_MODULE_ID
            and reference.source_publication_reference is None
            and reference.immutable_source_version is None
        ):
            raise ConcordManifestGenerationIntegrityError(
                "External evidence lacks exact immutable lineage."
            )


def _registration_for_generation(
    root: Path,
    class_id: str,
    activity_id: str,
) -> AcademicWorkRegistration:
    try:
        registration = load_current_concord_academic_work_registration(
            root, class_id, activity_id
        )
    except ConcordAcademicWorkRegistrationNotFoundError as error:
        raise ConcordManifestGenerationNotFoundError(str(error)) from error
    except ConcordAcademicWorkRegistrationValidationError as error:
        raise ConcordManifestGenerationValidationError(str(error)) from error
    except ConcordAcademicWorkRegistrationIntegrityError as error:
        raise ConcordManifestGenerationIntegrityError(str(error)) from error
    except ConcordAcademicWorkRegistrationError as error:
        raise ConcordManifestGenerationIntegrityError(str(error)) from error
    if registration is None:
        raise ConcordManifestGenerationValidationError(
            "Concord Activity must have an explicit current Academic Work "
            "Registration before manifest generation."
        )
    return registration


def _validate_registration_for_activity(
    registration: AcademicWorkRegistration,
    *,
    work: ModuleWorkRef,
    title: str,
) -> None:
    expected_source = ModuleRecordRef(
        module_id=CONCORD_MODULE_ID,
        record_kind=CONCORD_ACTIVITY_RECORD_KIND,
        record_id=work.work_id,
        contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
    )
    if (
        registration.work != work
        or registration.producer_contract_version
        != CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
        or registration.work_kind != CONCORD_ACADEMIC_WORK_KIND
        or registration.source_records != (expected_source,)
    ):
        raise ConcordManifestGenerationIntegrityError(
            "Current Academic Work Registration does not match the exact "
            "Concord Activity publication contract."
        )
    if registration.title != title:
        raise ConcordManifestGenerationValidationError(
            "Activity title differs from the current Academic Work "
            "Registration; explicitly update the registration first."
        )


def _load_generation_context(
    root: Path,
    request: GenerateAcademicResultManifestRequest,
    *,
    standards_library: StandardsLibrary | None,
) -> ManifestGenerationContext:
    try:
        require_core_class(root, request.class_id)
    except ConcordWorkflowValidationError as error:
        raise ConcordManifestGenerationValidationError(str(error)) from error
    except ConcordWorkflowNotFoundError as error:
        raise ConcordManifestGenerationNotFoundError(str(error)) from error

    work = ModuleWorkRef(
        module_id=CONCORD_MODULE_ID,
        class_id=request.class_id,
        work_id=request.activity_id,
    )
    try:
        loaded = load_current_record_graph(
            root,
            work,
            standards_library=standards_library,
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordManifestGenerationNotFoundError(
            f"Concord Activity is unavailable: {request.activity_id}"
        ) from error
    except ConcordStorageConflictError as error:
        raise ConcordManifestGenerationConflictError(str(error)) from error
    except ConcordStorageValidationError as error:
        raise ConcordManifestGenerationValidationError(str(error)) from error
    except (ConcordStorageIntegrityError, ConcordStorageReadError) as error:
        raise ConcordManifestGenerationIntegrityError(str(error)) from error
    except ConcordStorageError as error:
        raise ConcordManifestGenerationIntegrityError(str(error)) from error

    if loaded.snapshot_revision != request.expected_snapshot_revision:
        raise ConcordManifestGenerationConflictError(
            "The expected Concord snapshot revision is stale or in the future."
        )
    if len(loaded.graph.activities) != 1:
        raise ConcordManifestGenerationIntegrityError(
            "Concord snapshot must contain exactly one Activity."
        )
    activity = loaded.graph.activities[0]
    if activity.work_reference != work:
        raise ConcordManifestGenerationIntegrityError(
            "Concord Activity identity disagrees with its work."
        )
    registration = _registration_for_generation(
        root, request.class_id, request.activity_id
    )
    try:
        current_after_registration = load_current_snapshot(root, work)
    except ConcordStorageError as error:
        raise ConcordManifestGenerationIntegrityError(str(error)) from error
    if (
        current_after_registration.snapshot_revision
        != loaded.snapshot_revision
        or current_after_registration.snapshot_sha256
        != loaded.snapshot_sha256
    ):
        raise ConcordManifestGenerationConflictError(
            "Concord native snapshot changed while registration was loaded."
        )
    _validate_registration_for_activity(
        registration,
        work=work,
        title=activity.title,
    )

    if activity.scoring_orientation == "evidence_only":
        raise ConcordManifestGenerationValidationError(
            "evidence_only Activity cannot generate an academic-result manifest."
        )
    if not loaded.graph.score_records:
        raise ConcordManifestGenerationValidationError(
            "Academic-result manifest requires at least one Score Record."
        )

    _verify_external_lineage(root, loaded.graph)
    return ManifestGenerationContext(
        work=work,
        graph=loaded.graph,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        registration=registration,
    )


def _required_moderation_records(
    graph: ConcordRecordGraph,
) -> tuple[ModerationRecord, ...]:
    referenced = {
        item.moderation_record_id
        for item in graph.score_evidence_links
        if item.moderation_record_id is not None
    }
    if not referenced:
        return ()

    by_id = {
        item.moderation_record_id: item
        for item in graph.moderation_records
    }
    predecessor_to_successors: dict[str, set[str]] = {}
    for item in graph.moderation_records:
        predecessor = item.supersedes_moderation_record_id
        if predecessor is not None:
            predecessor_to_successors.setdefault(predecessor, set()).add(
                item.moderation_record_id
            )

    selected: set[str] = set(referenced)
    changed = True
    while changed:
        changed = False
        for record_id in tuple(selected):
            record = by_id.get(record_id)
            if record is None:
                raise ConcordManifestGenerationIntegrityError(
                    "Score Evidence Link references a missing Moderation Record."
                )
            predecessor = record.supersedes_moderation_record_id
            if predecessor is not None and predecessor not in selected:
                selected.add(predecessor)
                changed = True
            for successor in predecessor_to_successors.get(record_id, ()):
                if successor not in selected:
                    selected.add(successor)
                    changed = True

    return tuple(
        sorted(
            (by_id[record_id] for record_id in selected),
            key=lambda item: item.moderation_record_id,
        )
    )


def _build_manifest(
    context: ManifestGenerationContext,
    request: GenerateAcademicResultManifestRequest,
    *,
    revision: int,
    generated_at: datetime,
) -> AcademicResultManifest:
    graph = context.graph
    activity = graph.activities[0]

    set_by_id = {
        item.criterion_set_id: item for item in graph.criterion_sets
    }
    criterion_by_id = {
        item.criterion_id: item for item in graph.criteria
    }
    scale_by_id = {
        item.scoring_scale_id: item for item in graph.scoring_scales
    }

    required_set_ids = set(activity.criterion_set_ids)
    for score_record in graph.score_records:
        criterion = criterion_by_id.get(score_record.criterion_id)
        if criterion is None:
            raise ConcordManifestGenerationIntegrityError(
                "Score references a missing Criterion."
            )
        required_set_ids.add(criterion.criterion_set_id)

    projected_sets_native: list[CriterionSet] = []
    for set_id in required_set_ids:
        criterion_set = set_by_id.get(set_id)
        if criterion_set is None:
            raise ConcordManifestGenerationIntegrityError(
                "Activity/Score references a missing Criterion Set."
            )
        projected_sets_native.append(criterion_set)
    projected_sets_native.sort(
        key=lambda item: (
            item.lineage_id,
            item.revision,
            item.criterion_set_id,
        )
    )

    projected_criteria_native: list[Criterion] = []
    for criterion_set in projected_sets_native:
        for criterion_id in criterion_set.criterion_ids:
            criterion = criterion_by_id.get(criterion_id)
            if criterion is None:
                raise ConcordManifestGenerationIntegrityError(
                    "Criterion Set member is missing."
                )
            projected_criteria_native.append(criterion)

    used_scale_ids = {
        score_record.scoring_scale_id for score_record in graph.score_records
    }
    projected_scales_native: list[ScoringScale] = []
    for scale_id in used_scale_ids:
        scale = scale_by_id.get(scale_id)
        if scale is None:
            raise ConcordManifestGenerationIntegrityError(
                "Score references a missing Scoring Scale."
            )
        projected_scales_native.append(scale)
    projected_scales_native.sort(
        key=lambda item: (
            item.lineage_id,
            item.revision,
            item.scoring_scale_id,
        )
    )

    native_scores = tuple(
        sorted(graph.score_records, key=lambda item: item.score_record_id)
    )
    score_states = _score_current_states(native_scores)

    native_links = tuple(
        sorted(
            graph.score_evidence_links,
            key=lambda item: (
                item.score_record_id,
                item.score_evidence_link_id,
            ),
        )
    )

    native_moderation = _required_moderation_records(graph)
    moderation_states = _moderation_current_states(native_moderation)

    privacy_values: list[PrivacyPolicy] = []
    if activity.privacy_policy is not None:
        privacy_values.append(activity.privacy_policy)
    privacy_values.extend(item.privacy_policy for item in native_scores)
    privacy_values.extend(item.privacy_policy for item in native_moderation)

    manifest = AcademicResultManifest(
        record_type=ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
        contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
        producer_module_id=CONCORD_MODULE_ID,
        generated_at=generated_at,
        record_set=ManifestRecordSet(
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
            revision,
        ),
        work=context.work,
        source_activity=ModuleRecordRef(
            module_id=CONCORD_MODULE_ID,
            record_kind=CONCORD_ACTIVITY_RECORD_KIND,
            record_id=context.work.work_id,
            contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
        ),
        projection=ManifestProjection(
            source_snapshot_revision=context.snapshot_revision,
            projection_digest_algorithm="sha256",
            projection_digest="0" * 64,
            generated_by=_workflow_actor(request.actor),
            revision_reason=request.revision_reason,
        ),
        activity_context=ActivityContextProjection(
            activity_id=activity.activity_id,
            class_id=context.work.class_id,
            title=activity.title,
            scoring_orientation=activity.scoring_orientation,
            standards_profile_id=activity.standards_profile_id,
            focus_standard_ids=activity.focus_standard_ids,
            criterion_set_ids=activity.criterion_set_ids,
        ),
        criterion_sets=tuple(
            _criterion_set(item) for item in projected_sets_native
        ),
        criteria=tuple(
            _criterion(item) for item in projected_criteria_native
        ),
        scoring_scales=tuple(
            _scale(item) for item in projected_scales_native
        ),
        scores=tuple(
            _score(item, score_states) for item in native_scores
        ),
        score_evidence_links=tuple(
            _score_link(item) for item in native_links
        ),
        moderation_records=tuple(
            _moderation(item, moderation_states)
            for item in native_moderation
        ),
        standards_result_projection=tuple(
            StandardsResultProjection(
                score_record_id=item.score_record_id,
                standard_id=cast(str, item.standard_id),
            )
            for item in native_scores
            if item.score_kind == "standard_backed"
        ),
        privacy=_resolve_effective_privacy(privacy_values),
    )
    return with_semantic_projection_digest(manifest)


def build_academic_result_manifest(
    context: ManifestGenerationContext,
    request: GenerateAcademicResultManifestRequest,
    *,
    revision: int,
    generated_at: datetime,
) -> AcademicResultManifest:
    """Purely build one validated manifest from an immutable loaded context."""
    if not isinstance(context, ManifestGenerationContext):
        raise ConcordManifestGenerationValidationError(
            "context must be a ManifestGenerationContext."
        )
    if not isinstance(request, GenerateAcademicResultManifestRequest):
        raise ConcordManifestGenerationValidationError(
            "request must be a GenerateAcademicResultManifestRequest."
        )
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ConcordManifestGenerationValidationError(
            "revision must be a positive integer."
        )
    if (
        not isinstance(generated_at, datetime)
        or generated_at.tzinfo is None
        or generated_at.utcoffset() is None
    ):
        raise ConcordManifestGenerationValidationError(
            "generated_at must be timezone-aware."
        )
    try:
        return _build_manifest(
            context,
            request,
            revision=revision,
            generated_at=generated_at,
        )
    except ConcordAcademicResultManifestValidationError as error:
        raise ConcordManifestGenerationValidationError(str(error)) from error


def academic_result_manifest_relative_path(
    work: ModuleWorkRef,
    revision: int,
) -> str:
    if not isinstance(work, ModuleWorkRef) or work.module_id != CONCORD_MODULE_ID:
        raise ConcordManifestGenerationValidationError(
            "work must identify Concord."
        )
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ConcordManifestGenerationValidationError(
            "revision must be positive."
        )
    relative = (
        f"classes/{work.class_id}/modules/{work.module_id}/work/"
        f"{work.work_id}/{_RECORD_SET_RELATIVE_DIR}/{revision}.json"
    )
    try:
        return validate_publication_manifest_path(work, relative)
    except Exception as error:
        raise ConcordManifestGenerationValidationError(
            "manifest relative path is invalid."
        ) from error


def _manifest_directory(root: Path, work: ModuleWorkRef) -> Path:
    try:
        return safe_module_work_descendant(
            root,
            work,
            _RECORD_SET_RELATIVE_DIR,
        )
    except Exception as error:
        raise ConcordManifestGenerationValidationError(
            "manifest directory is outside the exact Concord work root."
        ) from error


def _canonical_revision_name(name: str) -> int | None:
    if not name.endswith(".json"):
        return None
    stem = name[:-5]
    if (
        not stem.isdecimal()
        or stem == "0"
        or str(int(stem)) != stem
    ):
        return None
    return int(stem)


def _stored_from_bytes(
    root: Path,
    work: ModuleWorkRef,
    revision: int,
    path: Path,
    content: bytes,
) -> StoredAcademicResultManifest:
    try:
        manifest = academic_result_manifest_from_bytes(content)
    except Exception as error:
        raise ConcordManifestGenerationIntegrityError(
            f"Manifest revision {revision} is invalid."
        ) from error
    relative = academic_result_manifest_relative_path(work, revision)
    if (
        manifest.work != work
        or manifest.record_set.record_set_id
        != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
        or manifest.record_set.revision != revision
        or path.name != f"{revision}.json"
    ):
        raise ConcordManifestGenerationIntegrityError(
            f"Manifest revision {revision} disagrees with its series/path."
        )
    expected_path = root.joinpath(*relative.split("/"))
    try:
        if path.resolve(strict=True) != expected_path.resolve(strict=True):
            raise ConcordManifestGenerationIntegrityError(
                "Manifest path resolves differently from its canonical path."
            )
    except FileNotFoundError as error:
        raise ConcordManifestGenerationNotFoundError(
            f"Manifest revision {revision} disappeared."
        ) from error
    except (OSError, RuntimeError) as error:
        raise ConcordManifestGenerationIntegrityError(
            "Manifest path could not be safely resolved."
        ) from error
    return StoredAcademicResultManifest(
        manifest=manifest,
        revision=revision,
        path=path,
        relative_path=relative,
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def _load_history(
    root: Path,
    work: ModuleWorkRef,
    *,
    allow_lock: bool,
) -> tuple[StoredAcademicResultManifest, ...]:
    directory = _manifest_directory(root, work)
    if not directory.exists():
        return ()
    if directory.is_symlink() or not directory.is_dir():
        raise ConcordManifestGenerationIntegrityError(
            "manifest history must be a nonsymlink directory."
        )
    try:
        work_root = directory.parents[2].resolve(strict=True)
        directory.resolve(strict=True).relative_to(work_root)
    except (OSError, RuntimeError, ValueError) as error:
        raise ConcordManifestGenerationIntegrityError(
            "manifest history escapes the Concord work root."
        ) from error

    stored: list[StoredAcademicResultManifest] = []
    try:
        entries = tuple(directory.iterdir())
    except OSError as error:
        raise ConcordManifestGenerationIntegrityError(
            "manifest history could not be enumerated."
        ) from error

    revision_entries: list[tuple[int, Path]] = []
    for entry in entries:
        if entry.name == _LOCK_NAME:
            if allow_lock:
                continue
            raise ConcordManifestGenerationConflictError(
                "Manifest generation history is currently locked."
            )
        revision = _canonical_revision_name(entry.name)
        if revision is None:
            raise ConcordManifestGenerationIntegrityError(
                "manifest history contains an unexpected entry."
            )
        revision_entries.append((revision, entry))

    for revision, entry in sorted(
        revision_entries, key=lambda item: item[0]
    ):
        if entry.is_symlink() or not entry.is_file():
            raise ConcordManifestGenerationIntegrityError(
                "manifest revision must be a nonsymlink regular file."
            )
        try:
            content = entry.read_bytes()
        except OSError as error:
            raise ConcordManifestGenerationIntegrityError(
                f"Manifest revision {revision} could not be read."
            ) from error
        stored.append(
            _stored_from_bytes(root, work, revision, entry, content)
        )

    revisions = tuple(item.revision for item in stored)
    if revisions:
        if revisions[0] != 1:
            raise ConcordManifestGenerationIntegrityError(
                "manifest history must begin at revision 1."
            )
        if tuple(sorted(revisions)) != revisions:
            raise ConcordManifestGenerationIntegrityError(
                "manifest revisions must be numerically ordered."
            )
        if len(revisions) != len(set(revisions)):
            raise ConcordManifestGenerationIntegrityError(
                "manifest history contains duplicate revisions."
            )
        for previous, current in zip(revisions, revisions[1:]):
            if current <= previous:
                raise ConcordManifestGenerationIntegrityError(
                    "manifest revisions must strictly increase."
                )
    return tuple(stored)


def list_academic_result_manifest_revisions(
    workspace_root: str | Path,
    work: ModuleWorkRef,
) -> tuple[StoredAcademicResultManifest, ...]:
    root = Path(workspace_root)
    return _load_history(root, work, allow_lock=False)


def load_academic_result_manifest_revision(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    revision: int,
) -> StoredAcademicResultManifest:
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ConcordManifestGenerationValidationError(
            "revision must be a positive integer."
        )
    for stored in list_academic_result_manifest_revisions(
        workspace_root, work
    ):
        if stored.revision == revision:
            return stored
    raise ConcordManifestGenerationNotFoundError(
        f"Academic-result manifest revision {revision} was not found."
    )


def load_academic_result_manifest_head(
    workspace_root: str | Path,
    work: ModuleWorkRef,
) -> StoredAcademicResultManifest | None:
    history = list_academic_result_manifest_revisions(
        workspace_root, work
    )
    return history[-1] if history else None


def _acquire_lock(directory: Path) -> tuple[int, Path]:
    try:
        work_root = directory.parents[2]
        for candidate in (
            directory.parents[1],
            directory.parent,
            directory,
        ):
            if candidate.is_symlink() or (
                candidate.exists() and not candidate.is_dir()
            ):
                raise ConcordManifestGenerationConflictError(
                    "manifest generation path contains an unsafe entry."
                )
            candidate.mkdir(exist_ok=True)
        directory.resolve(strict=True).relative_to(
            work_root.resolve(strict=True)
        )
    except ConcordManifestGenerationError:
        raise
    except (OSError, RuntimeError, ValueError) as error:
        raise ConcordManifestGenerationWriteError(
            "Could not establish a contained manifest generation directory."
        ) from error

    lock_path = directory / _LOCK_NAME
    try:
        descriptor = os.open(
            lock_path,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0),
            0o600,
        )
    except FileExistsError as error:
        raise ConcordManifestGenerationConflictError(
            "Another manifest generation operation holds .write.lock."
        ) from error
    except OSError as error:
        raise ConcordManifestGenerationWriteError(
            "Could not create the manifest generation lock."
        ) from error
    return descriptor, lock_path


def _sync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_new_revision(path: Path, content: bytes) -> None:
    descriptor: int | None = None
    created = False
    durable = False
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_BINARY", 0),
            0o600,
        )
        created = True
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            written = stream.write(content)
            if written != len(content):
                raise OSError("Manifest revision write was incomplete.")
            stream.flush()
            os.fsync(stream.fileno())
        durable = True
        _sync_directory(path.parent)
    except FileExistsError as error:
        raise ConcordManifestGenerationConflictError(
            "The planned immutable manifest revision already exists."
        ) from error
    except Exception as error:
        cleanup_error: OSError | None = None
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if created and not durable:
            try:
                path.unlink()
            except OSError as caught:
                cleanup_error = caught
        if durable:
            raise _DurableRevisionWriteError(
                "Manifest is durable but directory sync failed."
            ) from error
        write_error = ConcordManifestGenerationWriteError(
            "Could not durably create immutable manifest revision"
            + (
                "; incomplete-file cleanup also failed."
                if cleanup_error is not None
                else "."
            )
        )
        write_error.incomplete_target_cleanup_failure = cleanup_error
        raise write_error from error


def _prewrite_state_check(
    root: Path,
    context: ManifestGenerationContext,
    request: GenerateAcademicResultManifestRequest,
) -> None:
    try:
        current = load_current_snapshot(root, context.work)
    except ConcordStorageNotFoundError as error:
        raise ConcordManifestGenerationConflictError(
            "Concord current snapshot disappeared before manifest completion."
        ) from error
    except ConcordStorageError as error:
        raise ConcordManifestGenerationIntegrityError(str(error)) from error
    if (
        current.snapshot_revision != context.snapshot_revision
        or current.snapshot_sha256 != context.snapshot_sha256
        or current.snapshot_revision != request.expected_snapshot_revision
    ):
        raise ConcordManifestGenerationConflictError(
            "Concord native snapshot changed during manifest generation."
        )

    registration = _registration_for_generation(
        root, request.class_id, request.activity_id
    )
    if registration != context.registration:
        raise ConcordManifestGenerationConflictError(
            "Academic Work Registration changed during manifest generation."
        )


def _clock_now() -> datetime:
    return datetime.now(timezone.utc)


def preview_academic_result_manifest(
    request: GenerateAcademicResultManifestRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Callable[[], datetime] = _clock_now,
) -> AcademicResultManifestPreview:
    """Project generation read-only without acquiring a write lock or writing bytes."""
    if not isinstance(request, GenerateAcademicResultManifestRequest):
        raise ConcordManifestGenerationValidationError(
            "request must be GenerateAcademicResultManifestRequest."
        )
    if not callable(clock):
        raise ConcordManifestGenerationValidationError("clock must be callable.")
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordManifestGenerationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordManifestGenerationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = ModuleWorkRef(
        module_id=CONCORD_MODULE_ID,
        class_id=request.class_id,
        work_id=request.activity_id,
    )
    history = _load_history(root, work, allow_lock=False)
    context = _load_generation_context(
        root,
        request,
        standards_library=standards_library,
    )
    next_revision = 1 if not history else history[-1].revision + 1
    if not history and request.revision_reason != "initial":
        raise ConcordManifestGenerationValidationError(
            "The first producer manifest revision requires "
            'revision_reason="initial".'
        )
    generated_at = clock()
    if (
        not isinstance(generated_at, datetime)
        or generated_at.tzinfo is None
        or generated_at.utcoffset() is None
    ):
        raise ConcordManifestGenerationValidationError(
            "clock must return a timezone-aware datetime."
        )
    candidate = build_academic_result_manifest(
        context,
        request,
        revision=next_revision,
        generated_at=generated_at,
    )
    predecessor = history[-1] if history else None
    _prewrite_state_check(root, context, request)
    if (
        predecessor is not None
        and predecessor.manifest.projection.projection_digest
        == candidate.projection.projection_digest
    ):
        return AcademicResultManifestPreview(
            disposition="would_reuse",
            manifest=predecessor.manifest,
            revision=predecessor.revision,
            path=predecessor.path,
            relative_path=predecessor.relative_path,
            content=predecessor.content,
            sha256=predecessor.sha256,
            registration_revision=context.registration.registration_revision,
            source_snapshot_revision=context.snapshot_revision,
        )
    if history and request.revision_reason == "initial":
        raise ConcordManifestGenerationValidationError(
            "A materially changed successor manifest cannot use "
            'revision_reason="initial".'
        )
    content = academic_result_manifest_to_bytes(candidate)
    relative_path = academic_result_manifest_relative_path(work, next_revision)
    path = root.joinpath(*relative_path.split("/"))
    return AcademicResultManifestPreview(
        disposition="would_create",
        manifest=candidate,
        revision=next_revision,
        path=path,
        relative_path=relative_path,
        content=content,
        sha256=hashlib.sha256(content).hexdigest(),
        registration_revision=context.registration.registration_revision,
        source_snapshot_revision=context.snapshot_revision,
    )


def generate_academic_result_manifest(
    request: GenerateAcademicResultManifestRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Callable[[], datetime] = _clock_now,
) -> AcademicResultManifestGenerationResult:
    """Generate or reuse one immutable producer manifest revision."""
    if not isinstance(request, GenerateAcademicResultManifestRequest):
        raise ConcordManifestGenerationValidationError(
            "request must be GenerateAcademicResultManifestRequest."
        )
    if not callable(clock):
        raise ConcordManifestGenerationValidationError(
            "clock must be callable."
        )
    try:
        resolved = resolve_read_workspace_root(workspace_root)
    except Exception as error:
        raise ConcordManifestGenerationValidationError(str(error)) from error
    if resolved is None:
        raise ConcordManifestGenerationNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    root = Path(resolved)
    work = ModuleWorkRef(
        module_id=CONCORD_MODULE_ID,
        class_id=request.class_id,
        work_id=request.activity_id,
    )
    directory = _manifest_directory(root, work)
    lock_descriptor, lock_path = _acquire_lock(directory)

    operation_error: BaseException | None = None
    durable_path: Path | None = None
    durable_revision: int | None = None
    expected_digest: str | None = None
    result_value: AcademicResultManifestGenerationResult | None = None
    try:
        os.close(lock_descriptor)
        history = _load_history(root, work, allow_lock=True)
        context = _load_generation_context(
            root,
            request,
            standards_library=standards_library,
        )
        next_revision = (
            1 if not history else history[-1].revision + 1
        )
        if not history and request.revision_reason != "initial":
            raise ConcordManifestGenerationValidationError(
                "The first producer manifest revision requires "
                'revision_reason="initial".'
            )
        generated_at = clock()
        if (
            not isinstance(generated_at, datetime)
            or generated_at.tzinfo is None
            or generated_at.utcoffset() is None
        ):
            raise ConcordManifestGenerationValidationError(
                "clock must return a timezone-aware datetime."
            )

        candidate = build_academic_result_manifest(
            context,
            request,
            revision=next_revision,
            generated_at=generated_at,
        )
        predecessor = history[-1] if history else None

        _prewrite_state_check(root, context, request)

        if (
            predecessor is not None
            and predecessor.manifest.projection.projection_digest
            == candidate.projection.projection_digest
        ):
            expected_digest = predecessor.sha256
            durable_path = predecessor.path
            durable_revision = predecessor.revision
            result_value = AcademicResultManifestGenerationResult(
                disposition="existing",
                manifest=predecessor.manifest,
                revision=predecessor.revision,
                path=predecessor.path,
                relative_path=predecessor.relative_path,
                content=predecessor.content,
                sha256=predecessor.sha256,
                registration_revision=(
                    context.registration.registration_revision
                ),
                source_snapshot_revision=(
                    predecessor.manifest.projection.source_snapshot_revision
                ),
            )
        else:
            if history and request.revision_reason == "initial":
                raise ConcordManifestGenerationValidationError(
                    "A materially changed successor manifest cannot use "
                    'revision_reason="initial".'
                )
            content = academic_result_manifest_to_bytes(candidate)
            target = directory / f"{next_revision}.json"
            relative = academic_result_manifest_relative_path(
                work, next_revision
            )
            expected_digest = hashlib.sha256(content).hexdigest()
            try:
                _write_new_revision(target, content)
            except _DurableRevisionWriteError as error:
                durable_path = target
                durable_revision = next_revision
                state = ManifestGenerationPartialState(
                    operation="directory_sync",
                    work=work,
                    revision=next_revision,
                    path=target,
                    relative_path=relative,
                    expected_sha256=expected_digest,
                    durable_file_exists=target.exists(),
                )
                raise ConcordManifestGenerationPartialSuccessError(
                    "Manifest revision is durable but directory sync failed.",
                    state,
                ) from error

            durable_path = target
            durable_revision = next_revision
            try:
                stored_history = _load_history(
                    root, work, allow_lock=True
                )
                stored = next(
                    item
                    for item in stored_history
                    if item.revision == next_revision
                )
                if (
                    stored.content != content
                    or stored.manifest != candidate
                    or stored.sha256 != expected_digest
                ):
                    raise ConcordManifestGenerationIntegrityError(
                        "Durable manifest contradicts generated candidate."
                    )
                _prewrite_state_check(root, context, request)
                result_value = AcademicResultManifestGenerationResult(
                    disposition="created",
                    manifest=stored.manifest,
                    revision=stored.revision,
                    path=stored.path,
                    relative_path=stored.relative_path,
                    content=stored.content,
                    sha256=stored.sha256,
                    registration_revision=(
                        context.registration.registration_revision
                    ),
                    source_snapshot_revision=context.snapshot_revision,
                )
            except ConcordManifestGenerationError:
                raise
            except Exception as error:
                state = ManifestGenerationPartialState(
                    operation="generate",
                    work=work,
                    revision=next_revision,
                    path=target,
                    relative_path=relative,
                    expected_sha256=expected_digest,
                    durable_file_exists=target.exists(),
                )
                raise ConcordManifestGenerationPartialSuccessError(
                    "Manifest is durable but final verification failed.",
                    state,
                ) from error
        assert result_value is not None
        return result_value
    except ConcordManifestGenerationError as error:
        operation_error = error
        raise
    except Exception as error:
        normalized = ConcordManifestGenerationIntegrityError(
            "Manifest generation failed during validation or projection."
        )
        operation_error = normalized
        raise normalized from error
    except BaseException as error:
        operation_error = error
        raise
    finally:
        try:
            lock_path.unlink()
        except OSError as cleanup_error:
            cleanup_failure = ManifestGenerationCleanupFailure(
                path=lock_path,
                relative_path=(
                    academic_result_manifest_relative_path(work, 1)
                    .rsplit("/", 1)[0]
                    + f"/{_LOCK_NAME}"
                ),
                message=str(cleanup_error),
                error=cleanup_error,
            )
            if operation_error is None:
                if durable_path is not None and durable_revision is not None:
                    state = ManifestGenerationPartialState(
                        operation="lock_cleanup",
                        work=work,
                        revision=durable_revision,
                        path=durable_path,
                        relative_path=academic_result_manifest_relative_path(
                            work, durable_revision
                        ),
                        expected_sha256=expected_digest,
                        durable_file_exists=durable_path.exists(),
                        lock_cleanup_failure=cleanup_failure,
                    )
                    raise ConcordManifestGenerationPartialSuccessError(
                        "Manifest is durable but generation lock cleanup failed.",
                        state,
                    ) from cleanup_error
                write_error = ConcordManifestGenerationWriteError(
                    "Manifest generation lock cleanup failed."
                )
                write_error._record_lock_cleanup_failure(cleanup_failure)
                raise write_error from cleanup_error
            if isinstance(operation_error, ConcordManifestGenerationError):
                operation_error._record_lock_cleanup_failure(cleanup_failure)
                if isinstance(
                    operation_error,
                    ConcordManifestGenerationPartialSuccessError,
                ):
                    object.__setattr__(
                        operation_error.state,
                        "lock_cleanup_failure",
                        cleanup_failure,
                    )


def _manifest_summary(
    *,
    manifest: AcademicResultManifest,
    revision: int,
    registration_revision: int,
    source_snapshot_revision: int,
    relative_path: str,
    sha256: str,
) -> dict[str, object]:
    scores = manifest.scores
    current_count = sum(item.current_state == "current" for item in scores)
    standard_count = sum(item.score_kind == "standard_backed" for item in scores)
    non_score_count = sum(item.disposition != "scored" for item in scores)
    score_by_id = {score.score_record_id: score for score in scores}
    moderated_score_ids = {
        item.score_record_id
        for item in manifest.score_evidence_links
        if (
            item.moderation_record_id is not None
            and score_by_id[item.score_record_id].disposition == "scored"
        )
    }
    return {
        "work": manifest.work,
        "registration_revision": registration_revision,
        "source_snapshot_revision": source_snapshot_revision,
        "record_set_id": manifest.record_set.record_set_id,
        "record_set_revision": revision,
        "manifest_contract_version": manifest.contract_version,
        "score_count": len(scores),
        "current_score_count": current_count,
        "historical_score_count": len(scores) - current_count,
        "standard_backed_score_count": standard_count,
        "local_score_count": len(scores) - standard_count,
        "non_score_count": non_score_count,
        "moderation_dependent_count": len(moderated_score_ids),
        "capabilities": derive_manifest_capabilities(manifest),
        "manifest_path": relative_path,
        "manifest_sha256": sha256,
        "privacy_classification": manifest.privacy.classification,
    }


def manifest_preview_summary(
    preview: AcademicResultManifestPreview,
) -> dict[str, object]:
    """Return the compact publication-safe summary of a read-only preview."""
    if not isinstance(preview, AcademicResultManifestPreview):
        raise ConcordManifestGenerationValidationError(
            "preview must be AcademicResultManifestPreview."
        )
    result = _manifest_summary(
        manifest=preview.manifest,
        revision=preview.revision,
        registration_revision=preview.registration_revision,
        source_snapshot_revision=preview.source_snapshot_revision,
        relative_path=preview.relative_path,
        sha256=preview.sha256,
    )
    return {"disposition": preview.disposition, **result}


def manifest_generation_summary(
    result: AcademicResultManifestGenerationResult,
) -> dict[str, object]:
    """Return a compact privacy-safe summary of a generated/reused manifest."""
    if not isinstance(result, AcademicResultManifestGenerationResult):
        raise ConcordManifestGenerationValidationError(
            "result must be AcademicResultManifestGenerationResult."
        )
    summary = _manifest_summary(
        manifest=result.manifest,
        revision=result.revision,
        registration_revision=result.registration_revision,
        source_snapshot_revision=result.source_snapshot_revision,
        relative_path=result.relative_path,
        sha256=result.sha256,
    )
    return {"disposition": result.disposition, **summary}


__all__ = [
    "AcademicResultManifestGenerationResult",
    "AcademicResultManifestPreview",
    "ConcordManifestGenerationConflictError",
    "ConcordManifestGenerationError",
    "ConcordManifestGenerationIntegrityError",
    "ConcordManifestGenerationNotFoundError",
    "ConcordManifestGenerationPartialSuccessError",
    "ConcordManifestGenerationValidationError",
    "ConcordManifestGenerationWriteError",
    "GenerateAcademicResultManifestRequest",
    "ManifestGenerationCleanupFailure",
    "ManifestGenerationContext",
    "ManifestGenerationDisposition",
    "ManifestGenerationPartialState",
    "ManifestPreviewDisposition",
    "StoredAcademicResultManifest",
    "academic_result_manifest_relative_path",
    "build_academic_result_manifest",
    "generate_academic_result_manifest",
    "list_academic_result_manifest_revisions",
    "load_academic_result_manifest_head",
    "load_academic_result_manifest_revision",
    "manifest_generation_summary",
    "manifest_preview_summary",
    "preview_academic_result_manifest",
]
