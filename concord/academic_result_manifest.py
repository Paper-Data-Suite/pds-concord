"""Pure Concord Academic Result Manifest v1 contract.

This module performs no workspace discovery or persistence. It owns only the
immutable public value objects, strict JSON conversion, whole-manifest
validation, shared capability derivation, semantic projection digests, and
canonical UTF-8 JSON bytes.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Final, Literal, NoReturn, TypeAlias, cast

from pds_core.identifiers import IdentifierValidationError, validate_identifier
from pds_core.publication_records import PublicationCapability
from pds_core.routing_models import (
    ModuleRecordRef,
    ModuleWorkRef,
    RoutingModelError,
    module_record_ref_from_dict,
    module_record_ref_to_dict,
    module_work_ref_from_dict,
    module_work_ref_to_dict,
)

from concord.pds_contract import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)

JsonScalar: TypeAlias = str | int | float | bool
ScoreKind: TypeAlias = Literal["standard_backed", "local"]
ScoreDisposition: TypeAlias = Literal[
    "scored",
    "insufficient_evidence",
    "absent",
    "excused",
    "not_observed",
    "not_applicable",
    "deferred",
]
ScoreBasis: TypeAlias = Literal[
    "linked_evidence", "professional_judgment", "mixed_basis"
]
CurrentState: TypeAlias = Literal["current", "superseded"]
RevisionReason: TypeAlias = Literal[
    "initial",
    "native_state_change",
    "evidence_lineage_change",
    "moderation_change",
    "projection_correction",
    "privacy_correction",
    "contract_migration",
]

PROJECTION_DIGEST_ALGORITHM: Final[str] = "sha256"
PUBLICATION_KIND: Final[str] = "academic_result_set"

_SCORE_KINDS = frozenset({"standard_backed", "local"})
_SCORE_DISPOSITIONS = frozenset(
    {
        "scored",
        "insufficient_evidence",
        "absent",
        "excused",
        "not_observed",
        "not_applicable",
        "deferred",
    }
)
_SCORE_BASES = frozenset(
    {"linked_evidence", "professional_judgment", "mixed_basis"}
)
_CURRENT_STATES = frozenset({"current", "superseded"})
_REVISION_REASONS = frozenset(
    {
        "initial",
        "native_state_change",
        "evidence_lineage_change",
        "moderation_change",
        "projection_correction",
        "privacy_correction",
        "contract_migration",
    }
)
_TARGET_KINDS = frozenset(
    {
        "core_student",
        "concord_group",
        "concord_session",
        "concord_activity",
        "concord_artifact_instance",
    }
)
_SUBJECT_KINDS = _TARGET_KINDS | frozenset({"external_record"})
_CRITERION_KINDS = _SCORE_KINDS
_CRITERION_SET_KINDS = frozenset({"standard_backed", "local", "mixed"})
_CRITERION_SET_SCOPES = frozenset({"reusable", "activity_specific"})
_SCALE_TYPES = frozenset(
    {"numeric", "ordinal", "categorical", "binary", "teacher_defined"}
)
_SCALE_STATUSES = frozenset(
    {"draft", "active", "inactive", "archived", "superseded"}
)
_CRITERION_SET_STATUSES = _SCALE_STATUSES
_CRITERION_STATUSES = frozenset({"draft", "active", "inactive", "archived"})
_LINK_STATUSES = frozenset({"active", "inactive", "superseded", "rejected"})
_LINK_SIGNIFICANCE = frozenset(
    {
        "primary",
        "corroborating",
        "contextual",
        "qualifying",
        "counterevidence",
        "background",
    }
)
_MODERATION_STATUSES = frozenset(
    {
        "accepted",
        "accepted_with_qualification",
        "insufficient",
        "disputed",
        "rejected",
        "not_used_for_scoring",
    }
)
_MODERATION_PERMITTED_USES = frozenset(
    {
        "support_group_score",
        "support_named_subject",
        "corroborate_only",
        "formative_only",
        "not_independently_determine_score",
        "not_be_used_for_scoring",
    }
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
_SCORING_ORIENTATIONS = frozenset(
    {"evidence_only", "standards_based", "mixed", "local_criteria_only"}
)
_EVIDENCE_KINDS = frozenset(
    {
        "artifact_instance",
        "artifact_page",
        "teacher_rationale",
        "scoreform_result",
        "quillan_response",
        "external_record",
    }
)
_MODERATION_REQUIREMENTS = frozenset({"required", "not_required"})

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
_SECRET_SHAPED = re.compile(
    r"(?i)(?:password|passwd|api[_ -]?key|access[_ -]?token|secret)\s*[:=]"
)

_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "record_type",
        "contract_version",
        "producer_module_id",
        "generated_at",
        "record_set",
        "work",
        "source_activity",
        "projection",
        "activity_context",
        "criterion_sets",
        "criteria",
        "scoring_scales",
        "scores",
        "score_evidence_links",
        "moderation_records",
        "standards_result_projection",
        "privacy",
    }
)


class ConcordAcademicResultManifestError(Exception):
    """Base error for the Concord public manifest contract."""


class ConcordAcademicResultManifestValidationError(
    ConcordAcademicResultManifestError, ValueError
):
    """A manifest value violates the v1 public contract."""


class ConcordAcademicResultManifestDecodeError(
    ConcordAcademicResultManifestValidationError
):
    """Manifest JSON cannot be decoded without violating the v1 contract."""


def _fail(message: str) -> NoReturn:
    raise ConcordAcademicResultManifestValidationError(message)


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str):
        _fail(f"{field} must be a safe identifier.")
    try:
        return validate_identifier(value, field)
    except (IdentifierValidationError, TypeError, ValueError) as error:
        raise ConcordAcademicResultManifestValidationError(
            f"{field} must be a safe identifier."
        ) from error


def _optional_identifier(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _identifier(value, field)


def _lower_kind(value: object, field: str) -> str:
    text = _identifier(value, field)
    if text != text.lower():
        _fail(f"{field} must be lowercase.")
    return text


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        _fail(f"{field} must be a positive integer.")
    return value


def _nonnegative_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail(f"{field} must be a nonnegative integer.")
    return value


def _bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        _fail(f"{field} must be a Boolean.")
    return value


def _public_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        _fail(f"{field} must be nonempty and trimmed.")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        _fail(f"{field} must be control-free.")
    lowered = value.lower()
    if (
        _SECRET_SHAPED.search(value) is not None
        or _WINDOWS_ABSOLUTE.match(value) is not None
        or "file://" in lowered
        or "/users/" in lowered
        or "/home/" in lowered
    ):
        _fail(f"{field} contains unsafe publication text.")
    return value


def _optional_public_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _public_text(value, field)


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _fail(f"{field} must be a timezone-aware datetime.")
    try:
        if value.utcoffset() is None:
            _fail(f"{field} must be a timezone-aware datetime.")
    except Exception as error:
        raise ConcordAcademicResultManifestValidationError(
            f"{field} must be a valid timezone-aware datetime."
        ) from error
    return value


def _timestamp_from_json(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value or value != value.strip():
        _fail(f"{field} must be an ISO 8601 timestamp string.")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as error:
        raise ConcordAcademicResultManifestValidationError(
            f"{field} must be a valid ISO 8601 timestamp."
        ) from error
    return _timestamp(parsed, field)


def _timestamp_to_json(value: datetime) -> str:
    normalized = _timestamp(value, "timestamp").astimezone(timezone.utc)
    return normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        _fail(f"{field} must be a lowercase SHA-256 digest.")
    return value


def _scalar(value: object, field: str) -> JsonScalar:
    if not isinstance(value, (str, int, float, bool)):
        _fail(f"{field} must be a non-null JSON scalar.")
    if isinstance(value, float) and not math.isfinite(value):
        _fail(f"{field} must be finite.")
    return value


def _scalar_key(value: JsonScalar) -> tuple[type[object], JsonScalar]:
    return (type(value), value)


def _controlled(value: object, field: str, allowed: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        _fail(f"{field} must be one of: {', '.join(sorted(allowed))}.")
    return value


def _tuple_identifiers(
    value: Sequence[str],
    field: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes, bytearray)):
        _fail(f"{field} must be an array of identifiers.")
    result = tuple(
        _identifier(item, f"{field}[{index}]")
        for index, item in enumerate(value)
    )
    if nonempty and not result:
        _fail(f"{field} must not be empty.")
    if len(set(result)) != len(result):
        _fail(f"{field} must not contain duplicates.")
    return result


def _tuple_values(
    value: Sequence[object],
    expected: type[object],
    field: str,
) -> tuple[object, ...]:
    if isinstance(value, (str, bytes, bytearray)):
        _fail(f"{field} must be an array.")
    result = tuple(value)
    if any(not isinstance(item, expected) for item in result):
        _fail(f"{field} contains an invalid value.")
    return result


def _exact_mapping(
    value: object, keys: frozenset[str], field: str
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(f"{field} must be an object.")
    if any(not isinstance(key, str) for key in value):
        _fail(f"{field} keys must be strings.")
    actual = frozenset(cast(Mapping[str, object], value).keys())
    if actual != keys:
        missing = sorted(keys - actual)
        unknown = sorted(actual - keys)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        _fail(f"{field} has an invalid key set ({'; '.join(details)}).")
    return cast(Mapping[str, object], value)


def _array(value: object, field: str) -> tuple[object, ...]:
    if not isinstance(value, list):
        _fail(f"{field} must be a JSON array.")
    return tuple(value)


def _module_work(value: object, field: str) -> ModuleWorkRef:
    if isinstance(value, ModuleWorkRef):
        return value
    try:
        return module_work_ref_from_dict(value)
    except (RoutingModelError, TypeError, ValueError) as error:
        raise ConcordAcademicResultManifestValidationError(
            f"{field} is invalid."
        ) from error


def _module_record(value: object, field: str) -> ModuleRecordRef:
    if isinstance(value, ModuleRecordRef):
        return value
    try:
        return module_record_ref_from_dict(value)
    except (RoutingModelError, TypeError, ValueError) as error:
        raise ConcordAcademicResultManifestValidationError(
            f"{field} is invalid."
        ) from error


@dataclass(frozen=True, slots=True)
class ManifestRecordSet:
    record_set_id: str
    revision: int

    def __post_init__(self) -> None:
        if self.record_set_id != CONCORD_ACADEMIC_RESULT_RECORD_SET_ID:
            _fail('record_set_id must be exactly "academic_results".')
        _positive_int(self.revision, "record_set.revision")


@dataclass(frozen=True, slots=True)
class PublicActor:
    actor_kind: str
    actor_id: str
    owning_system: str

    def __post_init__(self) -> None:
        _controlled(
            self.actor_kind,
            "actor_kind",
            frozenset(
                {
                    "core_student",
                    "authorized_adult",
                    "system",
                    "external_actor",
                }
            ),
        )
        _identifier(self.actor_id, "actor_id")
        _lower_kind(self.owning_system, "owning_system")


@dataclass(frozen=True, slots=True)
class ManifestProjection:
    source_snapshot_revision: int
    projection_digest_algorithm: str
    projection_digest: str
    generated_by: PublicActor
    revision_reason: RevisionReason

    def __post_init__(self) -> None:
        _positive_int(
            self.source_snapshot_revision, "projection.source_snapshot_revision"
        )
        if self.projection_digest_algorithm != PROJECTION_DIGEST_ALGORITHM:
            _fail('projection_digest_algorithm must be exactly "sha256".')
        _digest(self.projection_digest, "projection.projection_digest")
        if not isinstance(self.generated_by, PublicActor):
            _fail("projection.generated_by must be a PublicActor.")
        _controlled(
            self.revision_reason,
            "projection.revision_reason",
            _REVISION_REASONS,
        )


@dataclass(frozen=True, slots=True)
class ActivityContextProjection:
    activity_id: str
    class_id: str
    title: str
    scoring_orientation: str
    standards_profile_id: str | None
    focus_standard_ids: tuple[str, ...]
    criterion_set_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier(self.activity_id, "activity_context.activity_id")
        _identifier(self.class_id, "activity_context.class_id")
        _public_text(self.title, "activity_context.title")
        _controlled(
            self.scoring_orientation,
            "activity_context.scoring_orientation",
            _SCORING_ORIENTATIONS,
        )
        _optional_identifier(
            self.standards_profile_id,
            "activity_context.standards_profile_id",
        )
        object.__setattr__(
            self,
            "focus_standard_ids",
            _tuple_identifiers(
                self.focus_standard_ids,
                "activity_context.focus_standard_ids",
            ),
        )
        object.__setattr__(
            self,
            "criterion_set_ids",
            _tuple_identifiers(
                self.criterion_set_ids,
                "activity_context.criterion_set_ids",
            ),
        )


@dataclass(frozen=True, slots=True)
class CriterionSetProjection:
    criterion_set_id: str
    lineage_id: str
    revision: int
    criterion_set_kind: str
    scope: str
    criterion_ids: tuple[str, ...]
    status: str
    supersedes_criterion_set_id: str | None
    standards_profile_id: str | None

    def __post_init__(self) -> None:
        _identifier(self.criterion_set_id, "criterion_set_id")
        _identifier(self.lineage_id, "criterion_set.lineage_id")
        _positive_int(self.revision, "criterion_set.revision")
        _controlled(
            self.criterion_set_kind,
            "criterion_set.criterion_set_kind",
            _CRITERION_SET_KINDS,
        )
        _controlled(self.scope, "criterion_set.scope", _CRITERION_SET_SCOPES)
        object.__setattr__(
            self,
            "criterion_ids",
            _tuple_identifiers(
                self.criterion_ids,
                "criterion_set.criterion_ids",
                nonempty=True,
            ),
        )
        _controlled(
            self.status, "criterion_set.status", _CRITERION_SET_STATUSES
        )
        _optional_identifier(
            self.supersedes_criterion_set_id,
            "criterion_set.supersedes_criterion_set_id",
        )
        _optional_identifier(
            self.standards_profile_id,
            "criterion_set.standards_profile_id",
        )


@dataclass(frozen=True, slots=True)
class CriterionProjection:
    criterion_id: str
    criterion_set_id: str
    key: str
    label: str
    definition: str
    criterion_kind: str
    supported_target_kinds: tuple[str, ...]
    status: str
    standard_id: str | None
    alignment_standard_ids: tuple[str, ...]
    default_scoring_scale_id: str | None

    def __post_init__(self) -> None:
        _identifier(self.criterion_id, "criterion_id")
        _identifier(self.criterion_set_id, "criterion.criterion_set_id")
        _identifier(self.key, "criterion.key")
        _public_text(self.label, "criterion.label")
        _public_text(self.definition, "criterion.definition")
        kind = _controlled(
            self.criterion_kind,
            "criterion.criterion_kind",
            _CRITERION_KINDS,
        )
        targets = tuple(self.supported_target_kinds)
        if not targets or len(set(targets)) != len(targets):
            _fail("criterion.supported_target_kinds must be nonempty and unique.")
        for index, target in enumerate(targets):
            _controlled(
                target,
                f"criterion.supported_target_kinds[{index}]",
                _TARGET_KINDS,
            )
        object.__setattr__(self, "supported_target_kinds", targets)
        _controlled(self.status, "criterion.status", _CRITERION_STATUSES)
        _optional_identifier(self.standard_id, "criterion.standard_id")
        object.__setattr__(
            self,
            "alignment_standard_ids",
            _tuple_identifiers(
                self.alignment_standard_ids,
                "criterion.alignment_standard_ids",
            ),
        )
        _optional_identifier(
            self.default_scoring_scale_id,
            "criterion.default_scoring_scale_id",
        )
        if kind == "standard_backed" and self.standard_id is None:
            _fail("standard-backed Criterion requires standard_id.")
        if kind == "local" and self.standard_id is not None:
            _fail("local Criterion forbids standard_id.")


@dataclass(frozen=True, slots=True)
class ScaleLevelProjection:
    value: JsonScalar
    label: str
    meaning: str
    position: int | None
    description: str | None

    def __post_init__(self) -> None:
        _scalar(self.value, "scale_level.value")
        _public_text(self.label, "scale_level.label")
        _public_text(self.meaning, "scale_level.meaning")
        if self.position is not None:
            _positive_int(self.position, "scale_level.position")
        _optional_public_text(self.description, "scale_level.description")


@dataclass(frozen=True, slots=True)
class ScoringScaleProjection:
    scoring_scale_id: str
    lineage_id: str
    name: str
    revision: int
    scale_type: str
    levels: tuple[ScaleLevelProjection, ...]
    status: str
    supersedes_scoring_scale_id: str | None

    def __post_init__(self) -> None:
        _identifier(self.scoring_scale_id, "scoring_scale_id")
        _identifier(self.lineage_id, "scoring_scale.lineage_id")
        _public_text(self.name, "scoring_scale.name")
        _positive_int(self.revision, "scoring_scale.revision")
        scale_type = _controlled(
            self.scale_type, "scoring_scale.scale_type", _SCALE_TYPES
        )
        levels = tuple(self.levels)
        if not levels or any(
            not isinstance(level, ScaleLevelProjection) for level in levels
        ):
            _fail("scoring_scale.levels must contain ScaleLevelProjection values.")
        object.__setattr__(self, "levels", levels)
        keys = tuple(_scalar_key(level.value) for level in levels)
        if len(set(keys)) != len(keys):
            _fail("scoring_scale level values must be type-sensitively unique.")
        positions = tuple(
            level.position for level in levels if level.position is not None
        )
        if len(set(positions)) != len(positions):
            _fail("scoring_scale positions must be unique.")
        if positions and len(positions) != len(levels):
            _fail("scoring_scale positions must be complete or absent.")
        if scale_type == "numeric" and any(
            isinstance(level.value, bool)
            or not isinstance(level.value, (int, float))
            for level in levels
        ):
            _fail("numeric Scale levels require int or float values.")
        if scale_type == "ordinal" and any(
            level.position is None for level in levels
        ):
            _fail("ordinal Scale levels require positions.")
        if scale_type == "binary" and len(levels) != 2:
            _fail("binary Scale requires exactly two levels.")
        _controlled(self.status, "scoring_scale.status", _SCALE_STATUSES)
        _optional_identifier(
            self.supersedes_scoring_scale_id,
            "scoring_scale.supersedes_scoring_scale_id",
        )

    def level_for_value(
        self, value: JsonScalar
    ) -> ScaleLevelProjection | None:
        """Return the exact type-sensitive Scale level for one JSON scalar."""
        key = _scalar_key(value)
        return next(
            (level for level in self.levels if _scalar_key(level.value) == key),
            None,
        )

    def has_value(self, value: JsonScalar) -> bool:
        return self.level_for_value(value) is not None


@dataclass(frozen=True, slots=True)
class TargetReferenceProjection:
    target_kind: str
    target_id: str
    owning_system: str
    contract_version: str | None

    def __post_init__(self) -> None:
        kind = _controlled(
            self.target_kind, "target.target_kind", _TARGET_KINDS
        )
        _identifier(self.target_id, "target.target_id")
        owner = _lower_kind(self.owning_system, "target.owning_system")
        _optional_identifier(
            self.contract_version, "target.contract_version"
        )
        expected_owner = "core" if kind == "core_student" else "concord"
        if owner != expected_owner:
            _fail(
                f"{kind} target owning_system must be exactly "
                f"{expected_owner}."
            )


@dataclass(frozen=True, slots=True)
class SubjectReferenceProjection:
    subject_kind: str
    subject_id: str
    owning_system: str
    contract_version: str | None

    def __post_init__(self) -> None:
        _controlled(
            self.subject_kind, "subject.subject_kind", _SUBJECT_KINDS
        )
        _identifier(self.subject_id, "subject.subject_id")
        _lower_kind(self.owning_system, "subject.owning_system")
        _optional_identifier(
            self.contract_version, "subject.contract_version"
        )


@dataclass(frozen=True, slots=True)
class RecordReferenceProjection:
    module_id: str
    record_kind: str
    record_id: str
    contract_version: str | None

    def __post_init__(self) -> None:
        _lower_kind(self.module_id, "record_reference.module_id")
        _lower_kind(self.record_kind, "record_reference.record_kind")
        _identifier(self.record_id, "record_reference.record_id")
        _optional_identifier(
            self.contract_version, "record_reference.contract_version"
        )


@dataclass(frozen=True, slots=True)
class CorePublicationReferenceProjection:
    publication_id: str
    publication_schema_version: str | None

    def __post_init__(self) -> None:
        _identifier(self.publication_id, "publication_reference.publication_id")
        _optional_identifier(
            self.publication_schema_version,
            "publication_reference.publication_schema_version",
        )


@dataclass(frozen=True, slots=True)
class EvidenceLocatorProjection:
    page_number: int | None
    source_page_index: int | None
    section_label: str | None
    row_label: str | None
    column_label: str | None
    participant_label: str | None
    session_id: str | None

    def __post_init__(self) -> None:
        if self.page_number is not None:
            _positive_int(self.page_number, "evidence_locator.page_number")
        if self.source_page_index is not None:
            _nonnegative_int(
                self.source_page_index,
                "evidence_locator.source_page_index",
            )
        for field in (
            "section_label",
            "row_label",
            "column_label",
            "participant_label",
        ):
            _optional_public_text(
                getattr(self, field), f"evidence_locator.{field}"
            )
        _optional_identifier(
            self.session_id, "evidence_locator.session_id"
        )


@dataclass(frozen=True, slots=True)
class EvidenceReferenceProjection:
    evidence_kind: str
    owning_system: str
    record_id: str
    contract_version: str | None
    source_publication_reference: CorePublicationReferenceProjection | None
    immutable_source_version: str | None
    locator: EvidenceLocatorProjection | None
    subject_context: tuple[SubjectReferenceProjection, ...]
    moderation_requirement: str | None

    def __post_init__(self) -> None:
        _controlled(
            self.evidence_kind,
            "evidence_reference.evidence_kind",
            _EVIDENCE_KINDS,
        )
        owner = _lower_kind(
            self.owning_system, "evidence_reference.owning_system"
        )
        _identifier(self.record_id, "evidence_reference.record_id")
        _optional_identifier(
            self.contract_version,
            "evidence_reference.contract_version",
        )
        if (
            self.source_publication_reference is not None
            and not isinstance(
                self.source_publication_reference,
                CorePublicationReferenceProjection,
            )
        ):
            _fail(
                "evidence_reference.source_publication_reference is invalid."
            )
        if self.immutable_source_version is not None:
            version = _public_text(
                self.immutable_source_version,
                "evidence_reference.immutable_source_version",
            )
            if version.lower() in {"current", "latest", "mutable"}:
                _fail(
                    "immutable_source_version must identify an exact revision."
                )
        if self.locator is not None and not isinstance(
            self.locator, EvidenceLocatorProjection
        ):
            _fail("evidence_reference.locator is invalid.")
        subjects = tuple(self.subject_context)
        if any(
            not isinstance(subject, SubjectReferenceProjection)
            for subject in subjects
        ):
            _fail("evidence_reference.subject_context is invalid.")
        if len(set(subjects)) != len(subjects):
            _fail(
                "evidence_reference.subject_context must not contain duplicates."
            )
        object.__setattr__(self, "subject_context", subjects)
        if self.moderation_requirement is not None:
            _controlled(
                self.moderation_requirement,
                "evidence_reference.moderation_requirement",
                _MODERATION_REQUIREMENTS,
            )
        if (
            owner != CONCORD_MODULE_ID
            and self.source_publication_reference is None
            and self.immutable_source_version is None
        ):
            _fail(
                "external evidence requires an exact immutable source version "
                "or Core Publication Reference."
            )


@dataclass(frozen=True, slots=True)
class StatusReasonProjection:
    reason_code: str
    recorded_by: PublicActor
    recorded_at: datetime
    related_record: RecordReferenceProjection | None

    def __post_init__(self) -> None:
        _identifier(self.reason_code, "status_reason.reason_code")
        if not isinstance(self.recorded_by, PublicActor):
            _fail("status_reason.recorded_by must be a PublicActor.")
        _timestamp(self.recorded_at, "status_reason.recorded_at")
        if self.related_record is not None and not isinstance(
            self.related_record, RecordReferenceProjection
        ):
            _fail("status_reason.related_record is invalid.")


@dataclass(frozen=True, slots=True)
class ScoreProjection:
    score_record_id: str
    activity_id: str
    session_id: str | None
    target_reference: TargetReferenceProjection
    criterion_id: str
    score_kind: ScoreKind
    standard_id: str | None
    scoring_scale_id: str
    disposition: ScoreDisposition
    value: JsonScalar | None
    basis: ScoreBasis
    scorer: PublicActor
    scored_at: datetime
    moderation_complete: bool
    status_reason: StatusReasonProjection | None
    supersedes_score_record_id: str | None
    current_state: CurrentState

    def __post_init__(self) -> None:
        _identifier(self.score_record_id, "score.score_record_id")
        _identifier(self.activity_id, "score.activity_id")
        _optional_identifier(self.session_id, "score.session_id")
        if not isinstance(self.target_reference, TargetReferenceProjection):
            _fail("score.target_reference is invalid.")
        _identifier(self.criterion_id, "score.criterion_id")
        kind = cast(
            ScoreKind,
            _controlled(self.score_kind, "score.score_kind", _SCORE_KINDS),
        )
        _optional_identifier(self.standard_id, "score.standard_id")
        _identifier(self.scoring_scale_id, "score.scoring_scale_id")
        disposition = cast(
            ScoreDisposition,
            _controlled(
                self.disposition,
                "score.disposition",
                _SCORE_DISPOSITIONS,
            ),
        )
        cast(
            ScoreBasis,
            _controlled(self.basis, "score.basis", _SCORE_BASES),
        )
        if not isinstance(self.scorer, PublicActor):
            _fail("score.scorer must be a PublicActor.")
        _timestamp(self.scored_at, "score.scored_at")
        _bool(self.moderation_complete, "score.moderation_complete")
        if self.status_reason is not None and not isinstance(
            self.status_reason, StatusReasonProjection
        ):
            _fail("score.status_reason is invalid.")
        _optional_identifier(
            self.supersedes_score_record_id,
            "score.supersedes_score_record_id",
        )
        _controlled(
            self.current_state, "score.current_state", _CURRENT_STATES
        )
        if disposition == "scored":
            if self.value is None:
                _fail("scored Score requires value.")
            _scalar(self.value, "score.value")
            if self.status_reason is not None:
                _fail("scored Score forbids status_reason.")
            if not self.moderation_complete:
                _fail("scored Score requires moderation_complete.")
        else:
            if self.value is not None:
                _fail("non-score Score forbids value.")
            if self.status_reason is None:
                _fail("published non-score Score requires status_reason.")
            if self.status_reason.reason_code != disposition:
                _fail(
                    "published non-score status reason must match disposition."
                )
        if kind == "standard_backed" and self.standard_id is None:
            _fail("standard-backed Score requires standard_id.")
        if kind == "local" and self.standard_id is not None:
            _fail("local Score forbids standard_id.")


@dataclass(frozen=True, slots=True)
class ScoreEvidenceLinkProjection:
    score_evidence_link_id: str
    score_record_id: str
    evidence_reference: EvidenceReferenceProjection
    evidence_locator: EvidenceLocatorProjection | None
    subject_context: tuple[SubjectReferenceProjection, ...]
    relevance_description: str
    significance: str | None
    moderation_record_id: str | None
    status: str
    supersedes_score_evidence_link_id: str | None

    def __post_init__(self) -> None:
        _identifier(
            self.score_evidence_link_id,
            "score_evidence_link.score_evidence_link_id",
        )
        _identifier(
            self.score_record_id,
            "score_evidence_link.score_record_id",
        )
        if not isinstance(
            self.evidence_reference, EvidenceReferenceProjection
        ):
            _fail("score_evidence_link.evidence_reference is invalid.")
        if self.evidence_locator is not None and not isinstance(
            self.evidence_locator, EvidenceLocatorProjection
        ):
            _fail("score_evidence_link.evidence_locator is invalid.")
        subjects = tuple(self.subject_context)
        if any(
            not isinstance(subject, SubjectReferenceProjection)
            for subject in subjects
        ):
            _fail("score_evidence_link.subject_context is invalid.")
        if len(set(subjects)) != len(subjects):
            _fail(
                "score_evidence_link.subject_context must not contain "
                "duplicates."
            )
        object.__setattr__(self, "subject_context", subjects)
        _public_text(
            self.relevance_description,
            "score_evidence_link.relevance_description",
        )
        if self.significance is not None:
            _controlled(
                self.significance,
                "score_evidence_link.significance",
                _LINK_SIGNIFICANCE,
            )
        _optional_identifier(
            self.moderation_record_id,
            "score_evidence_link.moderation_record_id",
        )
        _controlled(
            self.status, "score_evidence_link.status", _LINK_STATUSES
        )
        _optional_identifier(
            self.supersedes_score_evidence_link_id,
            "score_evidence_link.supersedes_score_evidence_link_id",
        )


@dataclass(frozen=True, slots=True)
class ModerationProjection:
    moderation_record_id: str
    target_evidence_reference: EvidenceReferenceProjection
    target_subject_references: tuple[SubjectReferenceProjection, ...]
    status: str
    permitted_use: str
    qualification: str | None
    supersedes_moderation_record_id: str | None
    current_state: CurrentState

    def __post_init__(self) -> None:
        _identifier(
            self.moderation_record_id,
            "moderation.moderation_record_id",
        )
        if not isinstance(
            self.target_evidence_reference,
            EvidenceReferenceProjection,
        ):
            _fail("moderation.target_evidence_reference is invalid.")
        subjects = tuple(self.target_subject_references)
        if any(
            not isinstance(subject, SubjectReferenceProjection)
            for subject in subjects
        ):
            _fail("moderation.target_subject_references is invalid.")
        if len(set(subjects)) != len(subjects):
            _fail(
                "moderation.target_subject_references must not contain "
                "duplicates."
            )
        object.__setattr__(
            self,
            "target_subject_references",
            tuple(
                sorted(
                    subjects,
                    key=lambda item: (
                        item.subject_kind,
                        item.owning_system,
                        item.subject_id,
                        item.contract_version or "",
                    ),
                )
            ),
        )
        status = _controlled(
            self.status, "moderation.status", _MODERATION_STATUSES
        )
        permitted = _controlled(
            self.permitted_use,
            "moderation.permitted_use",
            _MODERATION_PERMITTED_USES,
        )
        _optional_public_text(
            self.qualification, "moderation.qualification"
        )
        _optional_identifier(
            self.supersedes_moderation_record_id,
            "moderation.supersedes_moderation_record_id",
        )
        _controlled(
            self.current_state,
            "moderation.current_state",
            _CURRENT_STATES,
        )
        if (
            status == "accepted_with_qualification"
            and self.qualification is None
        ):
            _fail(
                "accepted_with_qualification requires qualification."
            )
        if (
            status != "accepted_with_qualification"
            and self.qualification is not None
        ):
            _fail(
                "qualification is allowed only for "
                "accepted_with_qualification."
            )
        if (
            status in {"rejected", "not_used_for_scoring"}
            and permitted != "not_be_used_for_scoring"
        ):
            _fail(
                "rejected/not-used Moderation cannot permit scoring."
            )


@dataclass(frozen=True, slots=True)
class StandardsResultProjection:
    score_record_id: str
    standard_id: str

    def __post_init__(self) -> None:
        _identifier(
            self.score_record_id,
            "standards_result.score_record_id",
        )
        _identifier(self.standard_id, "standards_result.standard_id")


@dataclass(frozen=True, slots=True)
class PrivacyProjection:
    classification: str
    audience_references: tuple[SubjectReferenceProjection, ...]
    policy_reference: RecordReferenceProjection | None
    inherited_from: RecordReferenceProjection | None

    def __post_init__(self) -> None:
        classification = _controlled(
            self.classification,
            "privacy.classification",
            _PRIVACY_CLASSIFICATIONS,
        )
        audiences = tuple(self.audience_references)
        if any(
            not isinstance(subject, SubjectReferenceProjection)
            for subject in audiences
        ):
            _fail("privacy.audience_references is invalid.")
        if len(set(audiences)) != len(audiences):
            _fail("privacy.audience_references must not contain duplicates.")
        object.__setattr__(
            self,
            "audience_references",
            tuple(
                sorted(
                    audiences,
                    key=lambda item: (
                        item.subject_kind,
                        item.owning_system,
                        item.subject_id,
                        item.contract_version or "",
                    ),
                )
            ),
        )
        if self.policy_reference is not None and not isinstance(
            self.policy_reference, RecordReferenceProjection
        ):
            _fail("privacy.policy_reference is invalid.")
        if self.inherited_from is not None and not isinstance(
            self.inherited_from, RecordReferenceProjection
        ):
            _fail("privacy.inherited_from is invalid.")
        if classification == "inherited" and self.inherited_from is None:
            _fail("inherited privacy requires inherited_from.")
        if (
            classification == "external_policy"
            and self.policy_reference is None
        ):
            _fail("external_policy privacy requires policy_reference.")
        if classification not in {"inherited", "external_policy"} and (
            self.policy_reference is not None
            or self.inherited_from is not None
        ):
            _fail(
                "direct privacy classifications cannot carry resolution "
                "references."
            )


@dataclass(frozen=True, slots=True)
class AcademicResultManifest:
    record_type: str
    contract_version: str
    producer_module_id: str
    generated_at: datetime
    record_set: ManifestRecordSet
    work: ModuleWorkRef
    source_activity: ModuleRecordRef
    projection: ManifestProjection
    activity_context: ActivityContextProjection
    criterion_sets: tuple[CriterionSetProjection, ...]
    criteria: tuple[CriterionProjection, ...]
    scoring_scales: tuple[ScoringScaleProjection, ...]
    scores: tuple[ScoreProjection, ...]
    score_evidence_links: tuple[ScoreEvidenceLinkProjection, ...]
    moderation_records: tuple[ModerationProjection, ...]
    standards_result_projection: tuple[StandardsResultProjection, ...]
    privacy: PrivacyProjection

    def __post_init__(self) -> None:
        if self.record_type != ACADEMIC_RESULT_MANIFEST_RECORD_TYPE:
            _fail(
                'record_type must be exactly '
                '"concord_academic_result_manifest".'
            )
        if self.contract_version != ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION:
            _fail(
                'contract_version must be exactly '
                '"concord_academic_result_manifest_v1".'
            )
        if self.producer_module_id != CONCORD_MODULE_ID:
            _fail('producer_module_id must be exactly "concord".')
        _timestamp(self.generated_at, "generated_at")
        if not isinstance(self.record_set, ManifestRecordSet):
            _fail("record_set is invalid.")
        if not isinstance(self.work, ModuleWorkRef):
            _fail("work must be a ModuleWorkRef.")
        if not isinstance(self.source_activity, ModuleRecordRef):
            _fail("source_activity must be a ModuleRecordRef.")
        if not isinstance(self.projection, ManifestProjection):
            _fail("projection is invalid.")
        if not isinstance(
            self.activity_context, ActivityContextProjection
        ):
            _fail("activity_context is invalid.")
        if not isinstance(self.privacy, PrivacyProjection):
            _fail("privacy is invalid.")
        _require_projection_tuple(
            self.criterion_sets,
            CriterionSetProjection,
            "criterion_sets",
        )
        _require_projection_tuple(
            self.criteria, CriterionProjection, "criteria"
        )
        _require_projection_tuple(
            self.scoring_scales,
            ScoringScaleProjection,
            "scoring_scales",
        )
        _require_projection_tuple(
            self.scores, ScoreProjection, "scores"
        )
        _require_projection_tuple(
            self.score_evidence_links,
            ScoreEvidenceLinkProjection,
            "score_evidence_links",
        )
        _require_projection_tuple(
            self.moderation_records,
            ModerationProjection,
            "moderation_records",
        )
        _require_projection_tuple(
            self.standards_result_projection,
            StandardsResultProjection,
            "standards_result_projection",
        )


def _require_projection_tuple(
    values: Sequence[object],
    expected: type[object],
    field: str,
) -> None:
    if isinstance(values, (str, bytes, bytearray)):
        _fail(f"{field} must be an array.")
    if any(not isinstance(item, expected) for item in values):
        _fail(f"{field} contains an invalid value.")


def _criterion_set_sort_key(
    value: CriterionSetProjection,
) -> tuple[str, int, str]:
    return (value.lineage_id, value.revision, value.criterion_set_id)


def _scale_sort_key(
    value: ScoringScaleProjection,
) -> tuple[str, int, str]:
    return (value.lineage_id, value.revision, value.scoring_scale_id)


def _subject_sort_key(
    value: SubjectReferenceProjection,
) -> tuple[str, str, str, str]:
    return (
        value.subject_kind,
        value.owning_system,
        value.subject_id,
        value.contract_version or "",
    )


def _validate_unique_ids(
    values: Sequence[object],
    attribute: str,
    field: str,
) -> None:
    ids = tuple(cast(str, getattr(item, attribute)) for item in values)
    if len(ids) != len(set(ids)):
        _fail(f"{field} must not contain duplicate identities.")


def _validate_supersession_state(
    values: Sequence[object],
    *,
    id_attribute: str,
    predecessor_attribute: str,
    current_attribute: str,
    field: str,
) -> None:
    ids = {
        cast(str, getattr(item, id_attribute))
        for item in values
    }
    predecessor_ids: list[str] = []
    successor_count: dict[str, int] = {}
    for item in values:
        item_id = cast(str, getattr(item, id_attribute))
        predecessor = cast(
            str | None, getattr(item, predecessor_attribute)
        )
        if predecessor is None:
            continue
        if predecessor == item_id:
            _fail(f"{field} supersession cannot self-reference.")
        if predecessor not in ids:
            _fail(f"{field} supersession predecessor is missing.")
        predecessor_ids.append(predecessor)
        successor_count[predecessor] = successor_count.get(predecessor, 0) + 1
    if any(count > 1 for count in successor_count.values()):
        _fail(f"{field} supersession cannot branch.")

    predecessor_set = set(predecessor_ids)
    for item in values:
        item_id = cast(str, getattr(item, id_attribute))
        expected = "superseded" if item_id in predecessor_set else "current"
        if getattr(item, current_attribute) != expected:
            _fail(
                f"{field} current_state disagrees with explicit supersession."
            )

    predecessor_of = {
        cast(str, getattr(item, id_attribute)): cast(
            str | None, getattr(item, predecessor_attribute)
        )
        for item in values
    }
    for start in ids:
        seen: set[str] = set()
        cursor: str | None = start
        while cursor is not None:
            if cursor in seen:
                _fail(f"{field} supersession contains a cycle.")
            seen.add(cursor)
            cursor = predecessor_of.get(cursor)


def validate_academic_result_manifest(
    value: AcademicResultManifest,
) -> AcademicResultManifest:
    """Validate all cross-record and digest invariants for one v1 manifest."""
    if not isinstance(value, AcademicResultManifest):
        raise ConcordAcademicResultManifestValidationError(
            "manifest must be an AcademicResultManifest."
        )
    manifest = value

    if manifest.work.module_id != CONCORD_MODULE_ID:
        _fail('manifest work.module_id must be exactly "concord".')
    expected_source = ModuleRecordRef(
        module_id=CONCORD_MODULE_ID,
        record_kind=CONCORD_ACTIVITY_RECORD_KIND,
        record_id=manifest.work.work_id,
        contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
    )
    if manifest.source_activity != expected_source:
        _fail(
            "source_activity must identify the exact versioned Concord Activity."
        )
    if (
        manifest.activity_context.activity_id != manifest.work.work_id
        or manifest.activity_context.class_id != manifest.work.class_id
    ):
        _fail("activity_context identity must agree with manifest work.")
    if manifest.activity_context.scoring_orientation == "evidence_only":
        _fail("evidence_only Activity cannot produce academic results.")
    if not manifest.scores:
        _fail("academic-result manifest requires at least one Score.")

    if tuple(sorted(manifest.criterion_sets, key=_criterion_set_sort_key)) != (
        manifest.criterion_sets
    ):
        _fail("criterion_sets must use canonical lineage/revision/id order.")
    if tuple(sorted(manifest.scoring_scales, key=_scale_sort_key)) != (
        manifest.scoring_scales
    ):
        _fail("scoring_scales must use canonical lineage/revision/id order.")
    if tuple(sorted(manifest.scores, key=lambda item: item.score_record_id)) != (
        manifest.scores
    ):
        _fail("scores must be ordered by score_record_id.")
    if tuple(
        sorted(
            manifest.score_evidence_links,
            key=lambda item: (
                item.score_record_id,
                item.score_evidence_link_id,
            ),
        )
    ) != manifest.score_evidence_links:
        _fail(
            "score_evidence_links must be ordered by "
            "score_record_id/link_id."
        )
    if tuple(
        sorted(
            manifest.moderation_records,
            key=lambda item: item.moderation_record_id,
        )
    ) != manifest.moderation_records:
        _fail("moderation_records must be ordered by moderation_record_id.")
    if tuple(
        sorted(
            manifest.standards_result_projection,
            key=lambda item: item.score_record_id,
        )
    ) != manifest.standards_result_projection:
        _fail(
            "standards_result_projection must be ordered by score_record_id."
        )

    _validate_unique_ids(
        manifest.criterion_sets,
        "criterion_set_id",
        "criterion_sets",
    )
    _validate_unique_ids(manifest.criteria, "criterion_id", "criteria")
    _validate_unique_ids(
        manifest.scoring_scales,
        "scoring_scale_id",
        "scoring_scales",
    )
    _validate_unique_ids(manifest.scores, "score_record_id", "scores")
    _validate_unique_ids(
        manifest.score_evidence_links,
        "score_evidence_link_id",
        "score_evidence_links",
    )
    _validate_unique_ids(
        manifest.moderation_records,
        "moderation_record_id",
        "moderation_records",
    )

    set_by_id = {
        item.criterion_set_id: item for item in manifest.criterion_sets
    }
    criterion_by_id = {
        item.criterion_id: item for item in manifest.criteria
    }
    scale_by_id = {
        item.scoring_scale_id: item for item in manifest.scoring_scales
    }
    score_by_id = {
        item.score_record_id: item for item in manifest.scores
    }
    moderation_by_id = {
        item.moderation_record_id: item
        for item in manifest.moderation_records
    }

    expected_criterion_order: list[str] = []
    for criterion_set in manifest.criterion_sets:
        expected_criterion_order.extend(criterion_set.criterion_ids)
        for criterion_id in criterion_set.criterion_ids:
            criterion = criterion_by_id.get(criterion_id)
            if criterion is None:
                _fail("Criterion Set references a missing Criterion.")
            if criterion.criterion_set_id != criterion_set.criterion_set_id:
                _fail("Criterion parent Set identity is inconsistent.")
        if (
            criterion_set.criterion_set_kind == "standard_backed"
            and any(
                criterion_by_id[item].criterion_kind != "standard_backed"
                for item in criterion_set.criterion_ids
            )
        ):
            _fail("standard-backed Set contains a local Criterion.")
        if (
            criterion_set.criterion_set_kind == "local"
            and any(
                criterion_by_id[item].criterion_kind != "local"
                for item in criterion_set.criterion_ids
            )
        ):
            _fail("local Set contains a standard-backed Criterion.")
    if tuple(expected_criterion_order) != tuple(
        item.criterion_id for item in manifest.criteria
    ):
        _fail(
            "criteria must follow projected Set order and declared member order."
        )

    required_set_ids = set(manifest.activity_context.criterion_set_ids)
    used_scale_ids: set[str] = set()
    for score in manifest.scores:
        if score.activity_id != manifest.work.work_id:
            _fail("Score activity_id must match manifest work.")
        criterion = criterion_by_id.get(score.criterion_id)
        if criterion is None:
            _fail("Score references a missing Criterion.")
        required_set_ids.add(criterion.criterion_set_id)
        if criterion.criterion_set_id not in set_by_id:
            _fail("Score Criterion belongs to a missing Criterion Set.")
        if (
            score.target_reference.target_kind
            not in criterion.supported_target_kinds
        ):
            _fail("Score target is not supported by its Criterion.")
        if score.score_kind != criterion.criterion_kind:
            _fail("Score kind must match Criterion kind.")
        if score.score_kind == "standard_backed":
            if (
                score.standard_id != criterion.standard_id
                or score.standard_id
                not in manifest.activity_context.focus_standard_ids
            ):
                _fail(
                    "standard-backed Score must use its governing Focus Standard."
                )
            if manifest.activity_context.scoring_orientation not in {
                "standards_based",
                "mixed",
            }:
                _fail(
                    "standard-backed Score is incompatible with Activity "
                    "orientation."
                )
        else:
            if manifest.activity_context.scoring_orientation not in {
                "local_criteria_only",
                "mixed",
            }:
                _fail(
                    "local Score is incompatible with Activity orientation."
                )
        scale = scale_by_id.get(score.scoring_scale_id)
        if scale is None:
            _fail("Score references a missing Scoring Scale.")
        used_scale_ids.add(score.scoring_scale_id)
        if score.disposition == "scored":
            if score.value is None or not scale.has_value(score.value):
                _fail("Score value is not an exact Scale level.")

    if set(set_by_id) != required_set_ids:
        _fail(
            "criterion_sets must contain exactly selected and Score-required "
            "Set revisions."
        )
    if set(scale_by_id) != used_scale_ids:
        _fail(
            "scoring_scales must contain exactly the Scale revisions used by "
            "Scores."
        )

    _validate_supersession_state(
        manifest.scores,
        id_attribute="score_record_id",
        predecessor_attribute="supersedes_score_record_id",
        current_attribute="current_state",
        field="Score",
    )
    score_by_identity = {
        score.score_record_id: score for score in manifest.scores
    }
    for score in manifest.scores:
        predecessor_id = score.supersedes_score_record_id
        if predecessor_id is not None:
            score_predecessor = score_by_identity[predecessor_id]
            if score.scored_at < score_predecessor.scored_at:
                _fail("Score successor scored_at must not move backward.")
    _validate_supersession_state(
        manifest.moderation_records,
        id_attribute="moderation_record_id",
        predecessor_attribute="supersedes_moderation_record_id",
        current_attribute="current_state",
        field="Moderation",
    )

    link_ids = {
        item.score_evidence_link_id
        for item in manifest.score_evidence_links
    }
    link_successors: dict[str, int] = {}
    for link in manifest.score_evidence_links:
        if link.score_record_id not in score_by_id:
            _fail("Score Evidence Link references a missing Score.")
        link_predecessor_id = link.supersedes_score_evidence_link_id
        if link_predecessor_id is not None:
            if link_predecessor_id == link.score_evidence_link_id:
                _fail("Score Evidence Link cannot supersede itself.")
            if link_predecessor_id not in link_ids:
                _fail(
                    "Score Evidence Link supersession predecessor is missing."
                )
            link_successors[link_predecessor_id] = (
                link_successors.get(link_predecessor_id, 0) + 1
            )
        if link.moderation_record_id is not None:
            moderation = moderation_by_id.get(link.moderation_record_id)
            if moderation is None:
                _fail(
                    "Score Evidence Link references a missing Moderation Record."
                )
            if (
                moderation.target_evidence_reference
                != link.evidence_reference
            ):
                _fail(
                    "Moderation target evidence must equal the linked evidence."
                )
    if any(count > 1 for count in link_successors.values()):
        _fail("Score Evidence Link supersession cannot branch.")

    link_predecessor_of = {
        item.score_evidence_link_id: item.supersedes_score_evidence_link_id
        for item in manifest.score_evidence_links
    }
    for start in link_ids:
        seen: set[str] = set()
        cursor: str | None = start
        while cursor is not None:
            if cursor in seen:
                _fail("Score Evidence Link supersession contains a cycle.")
            seen.add(cursor)
            cursor = link_predecessor_of.get(cursor)

    link_by_id = {
        item.score_evidence_link_id: item
        for item in manifest.score_evidence_links
    }
    for link in manifest.score_evidence_links:
        predecessor_id = link.supersedes_score_evidence_link_id
        if predecessor_id is not None:
            predecessor_link = link_by_id[predecessor_id]
            if predecessor_link.score_record_id != link.score_record_id:
                _fail(
                    "Score Evidence Link successor must keep its Score parent."
                )

    superseded_link_ids = set(link_successors)
    for score in manifest.scores:
        active_links = tuple(
            link
            for link in manifest.score_evidence_links
            if (
                link.score_record_id == score.score_record_id
                and link.status == "active"
                and link.score_evidence_link_id not in superseded_link_ids
            )
        )
        if score.basis == "linked_evidence" and not active_links:
            _fail("linked_evidence Score requires an active Evidence Link.")
        if score.basis == "professional_judgment" and active_links:
            _fail(
                "professional_judgment Score must not have active Evidence Links."
            )
        if score.basis == "mixed_basis" and not active_links:
            _fail("mixed_basis Score requires an active Evidence Link.")

    standard_scores = {
        score.score_record_id: score
        for score in manifest.scores
        if score.score_kind == "standard_backed"
    }
    standard_rows = {
        row.score_record_id: row
        for row in manifest.standards_result_projection
    }
    if len(standard_rows) != len(manifest.standards_result_projection):
        _fail(
            "standards_result_projection must not contain duplicate Scores."
        )
    if set(standard_rows) != set(standard_scores):
        _fail(
            "standards_result_projection must contain exactly the "
            "standard-backed Scores."
        )
    for score_id, row in standard_rows.items():
        score = standard_scores[score_id]
        if row.standard_id != score.standard_id:
            _fail(
                "standards result standard must equal the Score governing "
                "standard."
            )

    expected_digest = calculate_semantic_projection_digest(manifest)
    if manifest.projection.projection_digest != expected_digest:
        _fail("projection_digest does not match the semantic public projection.")

    return manifest


def derive_manifest_capabilities(
    manifest: AcademicResultManifest,
) -> tuple[PublicationCapability, ...]:
    """Derive only the exact shared Core capabilities present in the manifest."""
    validate_academic_result_manifest(manifest)
    capabilities: list[PublicationCapability] = ["criterion_scores"]
    if any(score.score_kind == "standard_backed" for score in manifest.scores):
        capabilities.append("standards_ratings")
    score_by_id = {
        score.score_record_id: score for score in manifest.scores
    }
    if any(
        link.moderation_record_id is not None
        and score_by_id[link.score_record_id].disposition == "scored"
        for link in manifest.score_evidence_links
    ):
        capabilities.append("moderated_scores")
    return tuple(capabilities)


def _actor_to_dict(value: PublicActor) -> dict[str, object]:
    return {
        "actor_kind": value.actor_kind,
        "actor_id": value.actor_id,
        "owning_system": value.owning_system,
    }


def _subject_to_dict(
    value: SubjectReferenceProjection,
) -> dict[str, object]:
    return {
        "subject_kind": value.subject_kind,
        "subject_id": value.subject_id,
        "owning_system": value.owning_system,
        "contract_version": value.contract_version,
    }


def _record_reference_to_dict(
    value: RecordReferenceProjection,
) -> dict[str, object]:
    return {
        "module_id": value.module_id,
        "record_kind": value.record_kind,
        "record_id": value.record_id,
        "contract_version": value.contract_version,
    }


def _publication_reference_to_dict(
    value: CorePublicationReferenceProjection,
) -> dict[str, object]:
    return {
        "publication_id": value.publication_id,
        "publication_schema_version": value.publication_schema_version,
    }


def _locator_to_dict(
    value: EvidenceLocatorProjection,
) -> dict[str, object]:
    return {
        "page_number": value.page_number,
        "source_page_index": value.source_page_index,
        "section_label": value.section_label,
        "row_label": value.row_label,
        "column_label": value.column_label,
        "participant_label": value.participant_label,
        "session_id": value.session_id,
    }


def _evidence_reference_to_dict(
    value: EvidenceReferenceProjection,
) -> dict[str, object]:
    return {
        "evidence_kind": value.evidence_kind,
        "owning_system": value.owning_system,
        "record_id": value.record_id,
        "contract_version": value.contract_version,
        "source_publication_reference": (
            _publication_reference_to_dict(
                value.source_publication_reference
            )
            if value.source_publication_reference is not None
            else None
        ),
        "immutable_source_version": value.immutable_source_version,
        "locator": (
            _locator_to_dict(value.locator)
            if value.locator is not None
            else None
        ),
        "subject_context": [
            _subject_to_dict(subject) for subject in value.subject_context
        ],
        "moderation_requirement": value.moderation_requirement,
    }


def _moderation_to_dict(
    value: ModerationProjection,
) -> dict[str, object]:
    result: dict[str, object] = {
        "moderation_record_id": value.moderation_record_id,
        "target_evidence_reference": _evidence_reference_to_dict(
            value.target_evidence_reference
        ),
        "target_subject_references": [
            _subject_to_dict(subject)
            for subject in value.target_subject_references
        ],
        "status": value.status,
        "permitted_use": value.permitted_use,
        "supersedes_moderation_record_id": (
            value.supersedes_moderation_record_id
        ),
        "current_state": value.current_state,
    }
    if value.qualification is not None:
        result["qualification"] = value.qualification
    return result


def _score_to_dict(value: ScoreProjection) -> dict[str, object]:
    result: dict[str, object] = {
        "score_record_id": value.score_record_id,
        "activity_id": value.activity_id,
        "session_id": value.session_id,
        "target_reference": {
            "target_kind": value.target_reference.target_kind,
            "target_id": value.target_reference.target_id,
            "owning_system": value.target_reference.owning_system,
            "contract_version": value.target_reference.contract_version,
        },
        "criterion_id": value.criterion_id,
        "score_kind": value.score_kind,
        "standard_id": value.standard_id,
        "scoring_scale_id": value.scoring_scale_id,
        "disposition": value.disposition,
        "basis": value.basis,
        "scorer": _actor_to_dict(value.scorer),
        "scored_at": _timestamp_to_json(value.scored_at),
        "moderation_complete": value.moderation_complete,
        "supersedes_score_record_id": value.supersedes_score_record_id,
        "current_state": value.current_state,
    }
    if value.disposition == "scored":
        result["value"] = value.value
    else:
        reason = value.status_reason
        if reason is None:
            _fail("published non-score Score requires status_reason.")
        result["status_reason"] = {
            "reason_code": reason.reason_code,
            "recorded_by": _actor_to_dict(reason.recorded_by),
            "recorded_at": _timestamp_to_json(reason.recorded_at),
            "related_record": (
                _record_reference_to_dict(reason.related_record)
                if reason.related_record is not None
                else None
            ),
        }
    return result


def academic_result_manifest_to_dict(
    value: AcademicResultManifest,
) -> dict[str, object]:
    """Convert one fully validated manifest to its exact JSON-native shape."""
    manifest = validate_academic_result_manifest(value)
    return _manifest_to_dict_unvalidated(manifest)


def _manifest_to_dict_unvalidated(
    manifest: AcademicResultManifest,
) -> dict[str, object]:
    return {
        "record_type": manifest.record_type,
        "contract_version": manifest.contract_version,
        "producer_module_id": manifest.producer_module_id,
        "generated_at": _timestamp_to_json(manifest.generated_at),
        "record_set": {
            "record_set_id": manifest.record_set.record_set_id,
            "revision": manifest.record_set.revision,
        },
        "work": module_work_ref_to_dict(manifest.work),
        "source_activity": module_record_ref_to_dict(
            manifest.source_activity
        ),
        "projection": {
            "source_snapshot_revision": (
                manifest.projection.source_snapshot_revision
            ),
            "projection_digest_algorithm": (
                manifest.projection.projection_digest_algorithm
            ),
            "projection_digest": manifest.projection.projection_digest,
            "generated_by": _actor_to_dict(
                manifest.projection.generated_by
            ),
            "revision_reason": manifest.projection.revision_reason,
        },
        "activity_context": {
            "activity_id": manifest.activity_context.activity_id,
            "class_id": manifest.activity_context.class_id,
            "title": manifest.activity_context.title,
            "scoring_orientation": (
                manifest.activity_context.scoring_orientation
            ),
            "standards_profile_id": (
                manifest.activity_context.standards_profile_id
            ),
            "focus_standard_ids": list(
                manifest.activity_context.focus_standard_ids
            ),
            "criterion_set_ids": list(
                manifest.activity_context.criterion_set_ids
            ),
        },
        "criterion_sets": [
            {
                "criterion_set_id": item.criterion_set_id,
                "lineage_id": item.lineage_id,
                "revision": item.revision,
                "criterion_set_kind": item.criterion_set_kind,
                "scope": item.scope,
                "criterion_ids": list(item.criterion_ids),
                "status": item.status,
                "supersedes_criterion_set_id": (
                    item.supersedes_criterion_set_id
                ),
                "standards_profile_id": item.standards_profile_id,
            }
            for item in manifest.criterion_sets
        ],
        "criteria": [
            {
                "criterion_id": item.criterion_id,
                "criterion_set_id": item.criterion_set_id,
                "key": item.key,
                "label": item.label,
                "definition": item.definition,
                "criterion_kind": item.criterion_kind,
                "supported_target_kinds": list(
                    item.supported_target_kinds
                ),
                "status": item.status,
                "standard_id": item.standard_id,
                "alignment_standard_ids": list(
                    item.alignment_standard_ids
                ),
                "default_scoring_scale_id": (
                    item.default_scoring_scale_id
                ),
            }
            for item in manifest.criteria
        ],
        "scoring_scales": [
            {
                "scoring_scale_id": item.scoring_scale_id,
                "lineage_id": item.lineage_id,
                "name": item.name,
                "revision": item.revision,
                "scale_type": item.scale_type,
                "levels": [
                    {
                        "value": level.value,
                        "label": level.label,
                        "meaning": level.meaning,
                        "position": level.position,
                        "description": level.description,
                    }
                    for level in item.levels
                ],
                "status": item.status,
                "supersedes_scoring_scale_id": (
                    item.supersedes_scoring_scale_id
                ),
            }
            for item in manifest.scoring_scales
        ],
        "scores": [_score_to_dict(item) for item in manifest.scores],
        "score_evidence_links": [
            {
                "score_evidence_link_id": item.score_evidence_link_id,
                "score_record_id": item.score_record_id,
                "evidence_reference": _evidence_reference_to_dict(
                    item.evidence_reference
                ),
                "evidence_locator": (
                    _locator_to_dict(item.evidence_locator)
                    if item.evidence_locator is not None
                    else None
                ),
                "subject_context": [
                    _subject_to_dict(subject)
                    for subject in item.subject_context
                ],
                "relevance_description": item.relevance_description,
                "significance": item.significance,
                "moderation_record_id": item.moderation_record_id,
                "status": item.status,
                "supersedes_score_evidence_link_id": (
                    item.supersedes_score_evidence_link_id
                ),
            }
            for item in manifest.score_evidence_links
        ],
        "moderation_records": [
            _moderation_to_dict(item)
            for item in manifest.moderation_records
        ],
        "standards_result_projection": [
            {
                "score_record_id": item.score_record_id,
                "standard_id": item.standard_id,
            }
            for item in manifest.standards_result_projection
        ],
        "privacy": {
            "classification": manifest.privacy.classification,
            "audience_references": [
                _subject_to_dict(subject)
                for subject in manifest.privacy.audience_references
            ],
            "policy_reference": (
                _record_reference_to_dict(
                    manifest.privacy.policy_reference
                )
                if manifest.privacy.policy_reference is not None
                else None
            ),
            "inherited_from": (
                _record_reference_to_dict(manifest.privacy.inherited_from)
                if manifest.privacy.inherited_from is not None
                else None
            ),
        },
    }


def _semantic_projection_dict(
    manifest: AcademicResultManifest,
) -> dict[str, object]:
    data = _manifest_to_dict_unvalidated(manifest)
    data.pop("generated_at")
    projection = cast(dict[str, object], data.pop("projection"))
    del projection
    record_set = cast(dict[str, object], data["record_set"])
    data["record_set"] = {
        "record_set_id": record_set["record_set_id"],
    }
    return data


def _canonical_json_bytes(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as error:
        raise ConcordAcademicResultManifestValidationError(
            "manifest contains a non-canonical JSON value."
        ) from error
    return (text + "\n").encode("utf-8")


def calculate_semantic_projection_digest(
    manifest: AcademicResultManifest,
) -> str:
    """Hash only the semantic public projection, excluding revision envelope."""
    if not isinstance(manifest, AcademicResultManifest):
        raise ConcordAcademicResultManifestValidationError(
            "manifest must be an AcademicResultManifest."
        )
    return hashlib.sha256(
        _canonical_json_bytes(_semantic_projection_dict(manifest))
    ).hexdigest()


def with_semantic_projection_digest(
    manifest: AcademicResultManifest,
) -> AcademicResultManifest:
    """Return a validated copy carrying its calculated semantic digest."""
    if not isinstance(manifest, AcademicResultManifest):
        raise ConcordAcademicResultManifestValidationError(
            "manifest must be an AcademicResultManifest."
        )
    digest = calculate_semantic_projection_digest(manifest)
    candidate = replace(
        manifest,
        projection=replace(
            manifest.projection,
            projection_digest=digest,
        ),
    )
    return validate_academic_result_manifest(candidate)


def academic_result_manifest_to_bytes(
    value: AcademicResultManifest,
) -> bytes:
    """Return canonical UTF-8 JSON with exactly one final LF."""
    return _canonical_json_bytes(academic_result_manifest_to_dict(value))


class _DuplicateJsonKeyError(ValueError):
    pass


class _InvalidJsonConstantError(ValueError):
    pass


def _reject_duplicate_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> NoReturn:
    raise _InvalidJsonConstantError(value)


def academic_result_manifest_from_bytes(
    data: bytes,
) -> AcademicResultManifest:
    """Decode strict UTF-8 canonical-shape JSON and validate the whole manifest."""
    if not isinstance(data, bytes):
        raise ConcordAcademicResultManifestDecodeError(
            "manifest data must be bytes."
        )
    if data.startswith(b"\xef\xbb\xbf"):
        raise ConcordAcademicResultManifestDecodeError(
            "manifest must not contain a UTF-8 BOM."
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ConcordAcademicResultManifestDecodeError(
            "manifest must be valid UTF-8."
        ) from error
    if not text.endswith("\n") or text.endswith("\n\n"):
        raise ConcordAcademicResultManifestDecodeError(
            "manifest must end with exactly one LF."
        )
    try:
        raw = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except (
        json.JSONDecodeError,
        _DuplicateJsonKeyError,
        _InvalidJsonConstantError,
    ) as error:
        raise ConcordAcademicResultManifestDecodeError(
            "manifest JSON is invalid."
        ) from error
    manifest = academic_result_manifest_from_dict(raw)
    if academic_result_manifest_to_bytes(manifest) != data:
        raise ConcordAcademicResultManifestDecodeError(
            "manifest JSON is not canonical."
        )
    return manifest


def academic_result_manifest_from_dict(
    data: object,
) -> AcademicResultManifest:
    """Parse an exact JSON-native v1 mapping and validate the whole manifest."""
    mapping = _exact_mapping(data, _TOP_LEVEL_KEYS, "manifest")
    manifest = AcademicResultManifest(
        record_type=_required_str(mapping["record_type"], "record_type"),
        contract_version=_required_str(
            mapping["contract_version"], "contract_version"
        ),
        producer_module_id=_required_str(
            mapping["producer_module_id"], "producer_module_id"
        ),
        generated_at=_timestamp_from_json(
            mapping["generated_at"], "generated_at"
        ),
        record_set=_record_set_from_dict(mapping["record_set"]),
        work=_module_work(mapping["work"], "work"),
        source_activity=_module_record(
            mapping["source_activity"], "source_activity"
        ),
        projection=_projection_from_dict(mapping["projection"]),
        activity_context=_activity_context_from_dict(
            mapping["activity_context"]
        ),
        criterion_sets=tuple(
            _criterion_set_from_dict(item)
            for item in _array(mapping["criterion_sets"], "criterion_sets")
        ),
        criteria=tuple(
            _criterion_from_dict(item)
            for item in _array(mapping["criteria"], "criteria")
        ),
        scoring_scales=tuple(
            _scale_from_dict(item)
            for item in _array(
                mapping["scoring_scales"], "scoring_scales"
            )
        ),
        scores=tuple(
            _score_from_dict(item)
            for item in _array(mapping["scores"], "scores")
        ),
        score_evidence_links=tuple(
            _score_link_from_dict(item)
            for item in _array(
                mapping["score_evidence_links"],
                "score_evidence_links",
            )
        ),
        moderation_records=tuple(
            _moderation_from_dict(item)
            for item in _array(
                mapping["moderation_records"], "moderation_records"
            )
        ),
        standards_result_projection=tuple(
            _standards_result_from_dict(item)
            for item in _array(
                mapping["standards_result_projection"],
                "standards_result_projection",
            )
        ),
        privacy=_privacy_from_dict(mapping["privacy"]),
    )
    return validate_academic_result_manifest(manifest)


def _required_str(value: object, field: str) -> str:
    if not isinstance(value, str):
        _fail(f"{field} must be a string.")
    return value


def _optional_str(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _required_str(value, field)


def _record_set_from_dict(value: object) -> ManifestRecordSet:
    mapping = _exact_mapping(
        value,
        frozenset({"record_set_id", "revision"}),
        "record_set",
    )
    return ManifestRecordSet(
        record_set_id=_required_str(
            mapping["record_set_id"], "record_set.record_set_id"
        ),
        revision=_positive_int(
            mapping["revision"], "record_set.revision"
        ),
    )


def _actor_from_dict(value: object, field: str) -> PublicActor:
    mapping = _exact_mapping(
        value,
        frozenset({"actor_kind", "actor_id", "owning_system"}),
        field,
    )
    return PublicActor(
        actor_kind=_required_str(
            mapping["actor_kind"], f"{field}.actor_kind"
        ),
        actor_id=_required_str(mapping["actor_id"], f"{field}.actor_id"),
        owning_system=_required_str(
            mapping["owning_system"], f"{field}.owning_system"
        ),
    )


def _projection_from_dict(value: object) -> ManifestProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "source_snapshot_revision",
                "projection_digest_algorithm",
                "projection_digest",
                "generated_by",
                "revision_reason",
            }
        ),
        "projection",
    )
    return ManifestProjection(
        source_snapshot_revision=_positive_int(
            mapping["source_snapshot_revision"],
            "projection.source_snapshot_revision",
        ),
        projection_digest_algorithm=_required_str(
            mapping["projection_digest_algorithm"],
            "projection.projection_digest_algorithm",
        ),
        projection_digest=_required_str(
            mapping["projection_digest"],
            "projection.projection_digest",
        ),
        generated_by=_actor_from_dict(
            mapping["generated_by"], "projection.generated_by"
        ),
        revision_reason=cast(
            RevisionReason,
            _required_str(
                mapping["revision_reason"],
                "projection.revision_reason",
            ),
        ),
    )


def _activity_context_from_dict(
    value: object,
) -> ActivityContextProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "activity_id",
                "class_id",
                "title",
                "scoring_orientation",
                "standards_profile_id",
                "focus_standard_ids",
                "criterion_set_ids",
            }
        ),
        "activity_context",
    )
    return ActivityContextProjection(
        activity_id=_required_str(
            mapping["activity_id"], "activity_context.activity_id"
        ),
        class_id=_required_str(
            mapping["class_id"], "activity_context.class_id"
        ),
        title=_required_str(
            mapping["title"], "activity_context.title"
        ),
        scoring_orientation=_required_str(
            mapping["scoring_orientation"],
            "activity_context.scoring_orientation",
        ),
        standards_profile_id=_optional_str(
            mapping["standards_profile_id"],
            "activity_context.standards_profile_id",
        ),
        focus_standard_ids=tuple(
            _required_str(
                item, f"activity_context.focus_standard_ids[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["focus_standard_ids"],
                    "activity_context.focus_standard_ids",
                )
            )
        ),
        criterion_set_ids=tuple(
            _required_str(
                item, f"activity_context.criterion_set_ids[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["criterion_set_ids"],
                    "activity_context.criterion_set_ids",
                )
            )
        ),
    )


def _criterion_set_from_dict(value: object) -> CriterionSetProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "criterion_set_id",
                "lineage_id",
                "revision",
                "criterion_set_kind",
                "scope",
                "criterion_ids",
                "status",
                "supersedes_criterion_set_id",
                "standards_profile_id",
            }
        ),
        "criterion_set",
    )
    return CriterionSetProjection(
        criterion_set_id=_required_str(
            mapping["criterion_set_id"], "criterion_set.criterion_set_id"
        ),
        lineage_id=_required_str(
            mapping["lineage_id"], "criterion_set.lineage_id"
        ),
        revision=_positive_int(
            mapping["revision"], "criterion_set.revision"
        ),
        criterion_set_kind=_required_str(
            mapping["criterion_set_kind"],
            "criterion_set.criterion_set_kind",
        ),
        scope=_required_str(mapping["scope"], "criterion_set.scope"),
        criterion_ids=tuple(
            _required_str(
                item, f"criterion_set.criterion_ids[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["criterion_ids"],
                    "criterion_set.criterion_ids",
                )
            )
        ),
        status=_required_str(mapping["status"], "criterion_set.status"),
        supersedes_criterion_set_id=_optional_str(
            mapping["supersedes_criterion_set_id"],
            "criterion_set.supersedes_criterion_set_id",
        ),
        standards_profile_id=_optional_str(
            mapping["standards_profile_id"],
            "criterion_set.standards_profile_id",
        ),
    )


def _criterion_from_dict(value: object) -> CriterionProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "criterion_id",
                "criterion_set_id",
                "key",
                "label",
                "definition",
                "criterion_kind",
                "supported_target_kinds",
                "status",
                "standard_id",
                "alignment_standard_ids",
                "default_scoring_scale_id",
            }
        ),
        "criterion",
    )
    return CriterionProjection(
        criterion_id=_required_str(
            mapping["criterion_id"], "criterion.criterion_id"
        ),
        criterion_set_id=_required_str(
            mapping["criterion_set_id"], "criterion.criterion_set_id"
        ),
        key=_required_str(mapping["key"], "criterion.key"),
        label=_required_str(mapping["label"], "criterion.label"),
        definition=_required_str(
            mapping["definition"], "criterion.definition"
        ),
        criterion_kind=_required_str(
            mapping["criterion_kind"], "criterion.criterion_kind"
        ),
        supported_target_kinds=tuple(
            _required_str(
                item, f"criterion.supported_target_kinds[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["supported_target_kinds"],
                    "criterion.supported_target_kinds",
                )
            )
        ),
        status=_required_str(mapping["status"], "criterion.status"),
        standard_id=_optional_str(
            mapping["standard_id"], "criterion.standard_id"
        ),
        alignment_standard_ids=tuple(
            _required_str(
                item, f"criterion.alignment_standard_ids[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["alignment_standard_ids"],
                    "criterion.alignment_standard_ids",
                )
            )
        ),
        default_scoring_scale_id=_optional_str(
            mapping["default_scoring_scale_id"],
            "criterion.default_scoring_scale_id",
        ),
    )


def _scale_level_from_dict(value: object) -> ScaleLevelProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {"value", "label", "meaning", "position", "description"}
        ),
        "scale_level",
    )
    position_raw = mapping["position"]
    return ScaleLevelProjection(
        value=_scalar(mapping["value"], "scale_level.value"),
        label=_required_str(mapping["label"], "scale_level.label"),
        meaning=_required_str(mapping["meaning"], "scale_level.meaning"),
        position=(
            None
            if position_raw is None
            else _positive_int(position_raw, "scale_level.position")
        ),
        description=_optional_str(
            mapping["description"], "scale_level.description"
        ),
    )


def _scale_from_dict(value: object) -> ScoringScaleProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "scoring_scale_id",
                "lineage_id",
                "name",
                "revision",
                "scale_type",
                "levels",
                "status",
                "supersedes_scoring_scale_id",
            }
        ),
        "scoring_scale",
    )
    return ScoringScaleProjection(
        scoring_scale_id=_required_str(
            mapping["scoring_scale_id"],
            "scoring_scale.scoring_scale_id",
        ),
        lineage_id=_required_str(
            mapping["lineage_id"], "scoring_scale.lineage_id"
        ),
        name=_required_str(mapping["name"], "scoring_scale.name"),
        revision=_positive_int(
            mapping["revision"], "scoring_scale.revision"
        ),
        scale_type=_required_str(
            mapping["scale_type"], "scoring_scale.scale_type"
        ),
        levels=tuple(
            _scale_level_from_dict(item)
            for item in _array(
                mapping["levels"], "scoring_scale.levels"
            )
        ),
        status=_required_str(mapping["status"], "scoring_scale.status"),
        supersedes_scoring_scale_id=_optional_str(
            mapping["supersedes_scoring_scale_id"],
            "scoring_scale.supersedes_scoring_scale_id",
        ),
    )


def _target_from_dict(value: object) -> TargetReferenceProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "target_kind",
                "target_id",
                "owning_system",
                "contract_version",
            }
        ),
        "target_reference",
    )
    return TargetReferenceProjection(
        target_kind=_required_str(
            mapping["target_kind"], "target_reference.target_kind"
        ),
        target_id=_required_str(
            mapping["target_id"], "target_reference.target_id"
        ),
        owning_system=_required_str(
            mapping["owning_system"],
            "target_reference.owning_system",
        ),
        contract_version=_optional_str(
            mapping["contract_version"],
            "target_reference.contract_version",
        ),
    )


def _subject_from_dict(
    value: object, field: str
) -> SubjectReferenceProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "subject_kind",
                "subject_id",
                "owning_system",
                "contract_version",
            }
        ),
        field,
    )
    return SubjectReferenceProjection(
        subject_kind=_required_str(
            mapping["subject_kind"], f"{field}.subject_kind"
        ),
        subject_id=_required_str(
            mapping["subject_id"], f"{field}.subject_id"
        ),
        owning_system=_required_str(
            mapping["owning_system"], f"{field}.owning_system"
        ),
        contract_version=_optional_str(
            mapping["contract_version"], f"{field}.contract_version"
        ),
    )


def _record_reference_from_dict(
    value: object, field: str
) -> RecordReferenceProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "module_id",
                "record_kind",
                "record_id",
                "contract_version",
            }
        ),
        field,
    )
    return RecordReferenceProjection(
        module_id=_required_str(
            mapping["module_id"], f"{field}.module_id"
        ),
        record_kind=_required_str(
            mapping["record_kind"], f"{field}.record_kind"
        ),
        record_id=_required_str(
            mapping["record_id"], f"{field}.record_id"
        ),
        contract_version=_optional_str(
            mapping["contract_version"], f"{field}.contract_version"
        ),
    )


def _publication_reference_from_dict(
    value: object,
) -> CorePublicationReferenceProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {"publication_id", "publication_schema_version"}
        ),
        "publication_reference",
    )
    return CorePublicationReferenceProjection(
        publication_id=_required_str(
            mapping["publication_id"],
            "publication_reference.publication_id",
        ),
        publication_schema_version=_optional_str(
            mapping["publication_schema_version"],
            "publication_reference.publication_schema_version",
        ),
    )


def _locator_from_dict(
    value: object, field: str
) -> EvidenceLocatorProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "page_number",
                "source_page_index",
                "section_label",
                "row_label",
                "column_label",
                "participant_label",
                "session_id",
            }
        ),
        field,
    )
    page = mapping["page_number"]
    source_page = mapping["source_page_index"]
    return EvidenceLocatorProjection(
        page_number=(
            None
            if page is None
            else _positive_int(page, f"{field}.page_number")
        ),
        source_page_index=(
            None
            if source_page is None
            else _nonnegative_int(
                source_page, f"{field}.source_page_index"
            )
        ),
        section_label=_optional_str(
            mapping["section_label"], f"{field}.section_label"
        ),
        row_label=_optional_str(
            mapping["row_label"], f"{field}.row_label"
        ),
        column_label=_optional_str(
            mapping["column_label"], f"{field}.column_label"
        ),
        participant_label=_optional_str(
            mapping["participant_label"], f"{field}.participant_label"
        ),
        session_id=_optional_str(
            mapping["session_id"], f"{field}.session_id"
        ),
    )


def _evidence_reference_from_dict(
    value: object,
) -> EvidenceReferenceProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "evidence_kind",
                "owning_system",
                "record_id",
                "contract_version",
                "source_publication_reference",
                "immutable_source_version",
                "locator",
                "subject_context",
                "moderation_requirement",
            }
        ),
        "evidence_reference",
    )
    publication = mapping["source_publication_reference"]
    locator = mapping["locator"]
    return EvidenceReferenceProjection(
        evidence_kind=_required_str(
            mapping["evidence_kind"],
            "evidence_reference.evidence_kind",
        ),
        owning_system=_required_str(
            mapping["owning_system"],
            "evidence_reference.owning_system",
        ),
        record_id=_required_str(
            mapping["record_id"], "evidence_reference.record_id"
        ),
        contract_version=_optional_str(
            mapping["contract_version"],
            "evidence_reference.contract_version",
        ),
        source_publication_reference=(
            None
            if publication is None
            else _publication_reference_from_dict(publication)
        ),
        immutable_source_version=_optional_str(
            mapping["immutable_source_version"],
            "evidence_reference.immutable_source_version",
        ),
        locator=(
            None
            if locator is None
            else _locator_from_dict(
                locator, "evidence_reference.locator"
            )
        ),
        subject_context=tuple(
            _subject_from_dict(
                item, f"evidence_reference.subject_context[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["subject_context"],
                    "evidence_reference.subject_context",
                )
            )
        ),
        moderation_requirement=_optional_str(
            mapping["moderation_requirement"],
            "evidence_reference.moderation_requirement",
        ),
    )


def _status_reason_from_dict(value: object) -> StatusReasonProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "reason_code",
                "recorded_by",
                "recorded_at",
                "related_record",
            }
        ),
        "status_reason",
    )
    related = mapping["related_record"]
    return StatusReasonProjection(
        reason_code=_required_str(
            mapping["reason_code"], "status_reason.reason_code"
        ),
        recorded_by=_actor_from_dict(
            mapping["recorded_by"], "status_reason.recorded_by"
        ),
        recorded_at=_timestamp_from_json(
            mapping["recorded_at"], "status_reason.recorded_at"
        ),
        related_record=(
            None
            if related is None
            else _record_reference_from_dict(
                related, "status_reason.related_record"
            )
        ),
    )


def _score_from_dict(value: object) -> ScoreProjection:
    if not isinstance(value, Mapping):
        _fail("score must be an object.")
    if any(not isinstance(key, str) for key in value):
        _fail("score keys must be strings.")
    mapping = cast(Mapping[str, object], value)
    base_keys = frozenset(
        {
            "score_record_id",
            "activity_id",
            "session_id",
            "target_reference",
            "criterion_id",
            "score_kind",
            "standard_id",
            "scoring_scale_id",
            "disposition",
            "basis",
            "scorer",
            "scored_at",
            "moderation_complete",
            "supersedes_score_record_id",
            "current_state",
        }
    )
    disposition_raw = mapping.get("disposition")
    disposition = _required_str(disposition_raw, "score.disposition")
    if disposition == "scored":
        expected_keys = base_keys | frozenset({"value"})
    else:
        expected_keys = base_keys | frozenset({"status_reason"})
    actual_keys = frozenset(mapping.keys())
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unknown = sorted(actual_keys - expected_keys)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        _fail(
            "score has an invalid key set "
            f"({'; '.join(details)})."
        )

    if disposition == "scored":
        value_raw = mapping["value"]
        status_reason = None
    else:
        value_raw = None
        status_reason = _status_reason_from_dict(
            mapping["status_reason"]
        )

    return ScoreProjection(
        score_record_id=_required_str(
            mapping["score_record_id"], "score.score_record_id"
        ),
        activity_id=_required_str(
            mapping["activity_id"], "score.activity_id"
        ),
        session_id=_optional_str(
            mapping["session_id"], "score.session_id"
        ),
        target_reference=_target_from_dict(
            mapping["target_reference"]
        ),
        criterion_id=_required_str(
            mapping["criterion_id"], "score.criterion_id"
        ),
        score_kind=cast(
            ScoreKind,
            _required_str(mapping["score_kind"], "score.score_kind"),
        ),
        standard_id=_optional_str(
            mapping["standard_id"], "score.standard_id"
        ),
        scoring_scale_id=_required_str(
            mapping["scoring_scale_id"], "score.scoring_scale_id"
        ),
        disposition=cast(ScoreDisposition, disposition),
        value=(
            None if value_raw is None else _scalar(value_raw, "score.value")
        ),
        basis=cast(
            ScoreBasis,
            _required_str(mapping["basis"], "score.basis"),
        ),
        scorer=_actor_from_dict(mapping["scorer"], "score.scorer"),
        scored_at=_timestamp_from_json(
            mapping["scored_at"], "score.scored_at"
        ),
        moderation_complete=_bool(
            mapping["moderation_complete"], "score.moderation_complete"
        ),
        status_reason=status_reason,
        supersedes_score_record_id=_optional_str(
            mapping["supersedes_score_record_id"],
            "score.supersedes_score_record_id",
        ),
        current_state=cast(
            CurrentState,
            _required_str(
                mapping["current_state"], "score.current_state"
            ),
        ),
    )

def _score_link_from_dict(
    value: object,
) -> ScoreEvidenceLinkProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "score_evidence_link_id",
                "score_record_id",
                "evidence_reference",
                "evidence_locator",
                "subject_context",
                "relevance_description",
                "significance",
                "moderation_record_id",
                "status",
                "supersedes_score_evidence_link_id",
            }
        ),
        "score_evidence_link",
    )
    locator = mapping["evidence_locator"]
    return ScoreEvidenceLinkProjection(
        score_evidence_link_id=_required_str(
            mapping["score_evidence_link_id"],
            "score_evidence_link.score_evidence_link_id",
        ),
        score_record_id=_required_str(
            mapping["score_record_id"],
            "score_evidence_link.score_record_id",
        ),
        evidence_reference=_evidence_reference_from_dict(
            mapping["evidence_reference"]
        ),
        evidence_locator=(
            None
            if locator is None
            else _locator_from_dict(
                locator, "score_evidence_link.evidence_locator"
            )
        ),
        subject_context=tuple(
            _subject_from_dict(
                item, f"score_evidence_link.subject_context[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["subject_context"],
                    "score_evidence_link.subject_context",
                )
            )
        ),
        relevance_description=_required_str(
            mapping["relevance_description"],
            "score_evidence_link.relevance_description",
        ),
        significance=_optional_str(
            mapping["significance"],
            "score_evidence_link.significance",
        ),
        moderation_record_id=_optional_str(
            mapping["moderation_record_id"],
            "score_evidence_link.moderation_record_id",
        ),
        status=_required_str(
            mapping["status"], "score_evidence_link.status"
        ),
        supersedes_score_evidence_link_id=_optional_str(
            mapping["supersedes_score_evidence_link_id"],
            "score_evidence_link.supersedes_score_evidence_link_id",
        ),
    )


def _moderation_from_dict(value: object) -> ModerationProjection:
    if not isinstance(value, Mapping):
        _fail("moderation must be an object.")
    if any(not isinstance(key, str) for key in value):
        _fail("moderation keys must be strings.")
    mapping = cast(Mapping[str, object], value)
    base_keys = frozenset(
        {
            "moderation_record_id",
            "target_evidence_reference",
            "target_subject_references",
            "status",
            "permitted_use",
            "supersedes_moderation_record_id",
            "current_state",
        }
    )
    status = _required_str(mapping.get("status"), "moderation.status")
    expected_keys = (
        base_keys | frozenset({"qualification"})
        if status == "accepted_with_qualification"
        else base_keys
    )
    actual_keys = frozenset(mapping.keys())
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unknown = sorted(actual_keys - expected_keys)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        _fail(
            "moderation has an invalid key set "
            f"({'; '.join(details)})."
        )
    return ModerationProjection(
        moderation_record_id=_required_str(
            mapping["moderation_record_id"],
            "moderation.moderation_record_id",
        ),
        target_evidence_reference=_evidence_reference_from_dict(
            mapping["target_evidence_reference"]
        ),
        target_subject_references=tuple(
            _subject_from_dict(
                item, f"moderation.target_subject_references[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["target_subject_references"],
                    "moderation.target_subject_references",
                )
            )
        ),
        status=status,
        permitted_use=_required_str(
            mapping["permitted_use"], "moderation.permitted_use"
        ),
        qualification=(
            _required_str(
                mapping["qualification"], "moderation.qualification"
            )
            if "qualification" in mapping
            else None
        ),
        supersedes_moderation_record_id=_optional_str(
            mapping["supersedes_moderation_record_id"],
            "moderation.supersedes_moderation_record_id",
        ),
        current_state=cast(
            CurrentState,
            _required_str(
                mapping["current_state"], "moderation.current_state"
            ),
        ),
    )

def _standards_result_from_dict(
    value: object,
) -> StandardsResultProjection:
    mapping = _exact_mapping(
        value,
        frozenset({"score_record_id", "standard_id"}),
        "standards_result",
    )
    return StandardsResultProjection(
        score_record_id=_required_str(
            mapping["score_record_id"],
            "standards_result.score_record_id",
        ),
        standard_id=_required_str(
            mapping["standard_id"], "standards_result.standard_id"
        ),
    )


def _privacy_from_dict(value: object) -> PrivacyProjection:
    mapping = _exact_mapping(
        value,
        frozenset(
            {
                "classification",
                "audience_references",
                "policy_reference",
                "inherited_from",
            }
        ),
        "privacy",
    )
    policy = mapping["policy_reference"]
    inherited = mapping["inherited_from"]
    return PrivacyProjection(
        classification=_required_str(
            mapping["classification"], "privacy.classification"
        ),
        audience_references=tuple(
            _subject_from_dict(
                item, f"privacy.audience_references[{index}]"
            )
            for index, item in enumerate(
                _array(
                    mapping["audience_references"],
                    "privacy.audience_references",
                )
            )
        ),
        policy_reference=(
            None
            if policy is None
            else _record_reference_from_dict(
                policy, "privacy.policy_reference"
            )
        ),
        inherited_from=(
            None
            if inherited is None
            else _record_reference_from_dict(
                inherited, "privacy.inherited_from"
            )
        ),
    )


__all__ = [
    "ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION",
    "ACADEMIC_RESULT_MANIFEST_RECORD_TYPE",
    "AcademicResultManifest",
    "ActivityContextProjection",
    "ConcordAcademicResultManifestDecodeError",
    "ConcordAcademicResultManifestError",
    "ConcordAcademicResultManifestValidationError",
    "CorePublicationReferenceProjection",
    "CriterionProjection",
    "CriterionSetProjection",
    "CurrentState",
    "EvidenceLocatorProjection",
    "EvidenceReferenceProjection",
    "JsonScalar",
    "ManifestProjection",
    "ManifestRecordSet",
    "ModerationProjection",
    "PROJECTION_DIGEST_ALGORITHM",
    "PUBLICATION_KIND",
    "PrivacyProjection",
    "PublicActor",
    "RecordReferenceProjection",
    "RevisionReason",
    "ScaleLevelProjection",
    "ScoreBasis",
    "ScoreDisposition",
    "ScoreEvidenceLinkProjection",
    "ScoreKind",
    "ScoreProjection",
    "ScoringScaleProjection",
    "StandardsResultProjection",
    "StatusReasonProjection",
    "SubjectReferenceProjection",
    "TargetReferenceProjection",
    "academic_result_manifest_from_bytes",
    "academic_result_manifest_from_dict",
    "academic_result_manifest_to_bytes",
    "academic_result_manifest_to_dict",
    "calculate_semantic_projection_digest",
    "derive_manifest_capabilities",
    "validate_academic_result_manifest",
    "with_semantic_projection_digest",
]
