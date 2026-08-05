"""Shared immutable value objects and structural validation helpers."""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Final, TypeAlias, TypeVar

from pds_core.identifiers import validate_identifier
from pds_core.routing_models import ModuleRecordRef


class ConcordModelError(ValueError):
    """Raised when a Concord model is structurally invalid."""


JsonScalar: TypeAlias = str | int | float | bool
T = TypeVar("T")

_LOWER_KEY: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*$")
_EXTENSION_KEY: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$"
)


def require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConcordModelError(f"{field_name} must be a nonempty string.")
    if value != value.strip():
        raise ConcordModelError(
            f"{field_name} must not contain leading or trailing whitespace."
        )
    return value


def optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return require_text(value, field_name)


def identifier(value: object, field_name: str) -> str:
    try:
        return validate_identifier(value, field_name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ConcordModelError(str(error)) from error


def optional_identifier(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return identifier(value, field_name)


def controlled(value: object, field_name: str, allowed: frozenset[str]) -> str:
    text = require_text(value, field_name)
    if text not in allowed:
        raise ConcordModelError(
            f"{field_name} must be one of {', '.join(sorted(allowed))}."
        )
    return text


def controlled_key(
    value: object,
    field_name: str,
    builtins: frozenset[str],
) -> str:
    text = require_text(value, field_name)
    if text not in builtins and _EXTENSION_KEY.fullmatch(text) is None:
        raise ConcordModelError(
            f"{field_name} must be a built-in or namespace-qualified key."
        )
    return text


def lowercase_kind(value: object, field_name: str) -> str:
    text = require_text(value, field_name)
    if _LOWER_KEY.fullmatch(text) is None:
        raise ConcordModelError(
            f"{field_name} must be a lowercase identifier using underscores."
        )
    return text


def timestamp(value: object, field_name: str) -> str:
    text = require_text(value, field_name)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ConcordModelError(
            f"{field_name} must be an ISO-8601 timestamp."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ConcordModelError(f"{field_name} must include a UTC offset.")
    return text


def optional_timestamp(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return timestamp(value, field_name)


def positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConcordModelError(f"{field_name} must be a positive integer.")
    return value


def optional_positive_int(value: object, field_name: str) -> int | None:
    if value is None:
        return None
    return positive_int(value, field_name)


def tuple_of_identifiers(
    value: Iterable[str], field_name: str, *, nonempty: bool = False
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ConcordModelError(f"{field_name} must be an iterable of identifiers.")
    try:
        values = tuple(value)
    except TypeError as error:
        raise ConcordModelError(f"{field_name} must be iterable.") from error
    normalized = tuple(
        identifier(item, f"{field_name}[{index}]") for index, item in enumerate(values)
    )
    if nonempty and not normalized:
        raise ConcordModelError(f"{field_name} must not be empty.")
    if len(set(normalized)) != len(normalized):
        raise ConcordModelError(f"{field_name} must not contain duplicates.")
    return normalized


def tuple_of_values(
    value: Iterable[T], expected: type[T], field_name: str, *, nonempty: bool = False
) -> tuple[T, ...]:
    if isinstance(value, (str, bytes)):
        raise ConcordModelError(f"{field_name} must be an iterable.")
    try:
        result = tuple(value)
    except TypeError as error:
        raise ConcordModelError(f"{field_name} must be iterable.") from error
    if nonempty and not result:
        raise ConcordModelError(f"{field_name} must not be empty.")
    if any(not isinstance(item, expected) for item in result):
        raise ConcordModelError(f"{field_name} contains an invalid value.")
    return result


def require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ConcordModelError(f"{field_name} must be a boolean.")
    return value


def scalar_key(value: JsonScalar) -> tuple[type[object], JsonScalar]:
    if not isinstance(value, (str, int, float, bool)):
        raise ConcordModelError("scale value must be a JSON-native non-null scalar.")
    if isinstance(value, float) and not math.isfinite(value):
        raise ConcordModelError("scale value must be finite.")
    return (type(value), value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRecordReference:
    record_kind: str
    record_id: str
    contract_version: str | None = None

    def __post_init__(self) -> None:
        lowercase_kind(self.record_kind, "record_kind")
        identifier(self.record_id, "record_id")
        optional_identifier(self.contract_version, "contract_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class ParticipantReference:
    participant_kind: str
    participant_id: str
    owning_system: str

    def __post_init__(self) -> None:
        controlled(
            self.participant_kind,
            "participant_kind",
            frozenset({"core_student", "authorized_actor"}),
        )
        identifier(self.participant_id, "participant_id")
        lowercase_kind(self.owning_system, "owning_system")


@dataclass(frozen=True, slots=True, kw_only=True)
class ActorReference:
    actor_kind: str
    actor_id: str
    owning_system: str
    display_label_snapshot: str | None = None
    role_snapshot: str | None = None

    def __post_init__(self) -> None:
        controlled(
            self.actor_kind,
            "actor_kind",
            frozenset({"core_student", "authorized_adult", "system", "external_actor"}),
        )
        identifier(self.actor_id, "actor_id")
        lowercase_kind(self.owning_system, "owning_system")
        optional_text(self.display_label_snapshot, "display_label_snapshot")
        optional_text(self.role_snapshot, "role_snapshot")


@dataclass(frozen=True, slots=True, kw_only=True)
class SubjectReference:
    subject_kind: str
    subject_id: str
    owning_system: str
    contract_version: str | None = None

    def __post_init__(self) -> None:
        controlled(
            self.subject_kind,
            "subject_kind",
            frozenset(
                {
                    "core_student",
                    "concord_group",
                    "concord_session",
                    "concord_activity",
                    "concord_artifact_instance",
                    "external_record",
                }
            ),
        )
        identifier(self.subject_id, "subject_id")
        lowercase_kind(self.owning_system, "owning_system")
        optional_identifier(self.contract_version, "contract_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreTargetReference:
    target_kind: str
    target_id: str
    owning_system: str
    contract_version: str | None = None

    def __post_init__(self) -> None:
        controlled(
            self.target_kind,
            "target_kind",
            frozenset(
                {
                    "core_student",
                    "concord_group",
                    "concord_session",
                    "concord_activity",
                    "concord_artifact_instance",
                }
            ),
        )
        identifier(self.target_id, "target_id")
        lowercase_kind(self.owning_system, "owning_system")
        optional_identifier(self.contract_version, "contract_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceLocator:
    page_number: int | None = None
    source_page_index: int | None = None
    section_label: str | None = None
    row_label: str | None = None
    column_label: str | None = None
    participant_label: str | None = None
    session_id: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        optional_positive_int(self.page_number, "page_number")
        if self.source_page_index is not None and (
            isinstance(self.source_page_index, bool)
            or not isinstance(self.source_page_index, int)
            or self.source_page_index < 0
        ):
            raise ConcordModelError("source_page_index must be a nonnegative integer.")
        for name in (
            "section_label",
            "row_label",
            "column_label",
            "participant_label",
            "note",
        ):
            optional_text(getattr(self, name), name)
        optional_identifier(self.session_id, "session_id")


@dataclass(frozen=True, slots=True, kw_only=True)
class CorePublicationReference:
    publication_id: str
    publication_schema_version: str | None = None

    def __post_init__(self) -> None:
        identifier(self.publication_id, "publication_id")
        optional_identifier(
            self.publication_schema_version, "publication_schema_version"
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceReference:
    evidence_kind: str
    owning_system: str
    record_id: str
    contract_version: str | None = None
    source_publication_reference: CorePublicationReference | None = None
    immutable_source_version: str | None = None
    locator: EvidenceLocator | None = None
    subject_context: tuple[SubjectReference, ...] = ()
    moderation_requirement: str | None = None

    def __post_init__(self) -> None:
        controlled(
            self.evidence_kind,
            "evidence_kind",
            frozenset(
                {
                    "artifact_instance",
                    "artifact_page",
                    "teacher_rationale",
                    "scoreform_result",
                    "quillan_response",
                    "external_record",
                }
            ),
        )
        lowercase_kind(self.owning_system, "owning_system")
        identifier(self.record_id, "record_id")
        optional_identifier(self.contract_version, "contract_version")
        optional_text(self.immutable_source_version, "immutable_source_version")
        if (
            self.immutable_source_version is not None
            and self.immutable_source_version.lower()
            in {
                "current",
                "latest",
                "mutable",
            }
        ):
            raise ConcordModelError(
                "immutable_source_version must identify an exact immutable revision."
            )
        if self.source_publication_reference is not None and not isinstance(
            self.source_publication_reference, CorePublicationReference
        ):
            raise ConcordModelError("source_publication_reference is invalid.")
        if self.locator is not None and not isinstance(self.locator, EvidenceLocator):
            raise ConcordModelError("locator must be an EvidenceLocator.")
        object.__setattr__(
            self,
            "subject_context",
            tuple_of_values(self.subject_context, SubjectReference, "subject_context"),
        )
        if self.moderation_requirement is not None:
            controlled_key(
                self.moderation_requirement,
                "moderation_requirement",
                frozenset({"required", "not_required"}),
            )
        if (
            self.owning_system != "concord"
            and self.source_publication_reference is None
            and self.immutable_source_version is None
        ):
            raise ConcordModelError(
                "external evidence requires an immutable source version "
                "or publication reference."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Provenance:
    actor: ActorReference
    timestamp: str
    source_kind: str
    source_reference: ModuleRecordRef | ConcordRecordReference | None = None
    application_version: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.actor, ActorReference):
            raise ConcordModelError("actor must be an ActorReference.")
        timestamp(self.timestamp, "timestamp")
        controlled(
            self.source_kind,
            "source_kind",
            frozenset({"manual", "generated", "imported", "routed", "system"}),
        )
        if self.source_reference is not None and not isinstance(
            self.source_reference, (ModuleRecordRef, ConcordRecordReference)
        ):
            raise ConcordModelError("source_reference is invalid.")
        optional_text(self.application_version, "application_version")
        optional_text(self.note, "note")


@dataclass(frozen=True, slots=True, kw_only=True)
class EffectiveContext:
    activity_id: str
    session_ids: tuple[str, ...]
    sequence_start: int | None = None
    sequence_end: int | None = None
    applies_to_remaining_activity: bool = False

    def __post_init__(self) -> None:
        identifier(self.activity_id, "activity_id")
        object.__setattr__(
            self,
            "session_ids",
            tuple_of_identifiers(self.session_ids, "session_ids", nonempty=True),
        )
        start = optional_positive_int(self.sequence_start, "sequence_start")
        end = optional_positive_int(self.sequence_end, "sequence_end")
        require_bool(
            self.applies_to_remaining_activity, "applies_to_remaining_activity"
        )
        if start is not None and end is not None and start > end:
            raise ConcordModelError("sequence_start must not exceed sequence_end.")


@dataclass(frozen=True, slots=True, kw_only=True)
class PrivacyPolicy:
    classification: str
    audience_references: tuple[SubjectReference, ...] = ()
    policy_reference: ModuleRecordRef | None = None
    reason: str | None = None
    inherited_from: ConcordRecordReference | None = None

    def __post_init__(self) -> None:
        classifications = frozenset(
            {
                "teacher_restricted",
                "teacher_and_subjects",
                "group_and_teacher",
                "classroom_shared",
                "inherited",
                "external_policy",
            }
        )
        controlled(self.classification, "classification", classifications)
        object.__setattr__(
            self,
            "audience_references",
            tuple_of_values(
                self.audience_references, SubjectReference, "audience_references"
            ),
        )
        optional_text(self.reason, "reason")
        if self.policy_reference is not None and not isinstance(
            self.policy_reference, ModuleRecordRef
        ):
            raise ConcordModelError("policy_reference must be a ModuleRecordRef.")
        if self.inherited_from is not None and not isinstance(
            self.inherited_from, ConcordRecordReference
        ):
            raise ConcordModelError("inherited_from must be a ConcordRecordReference.")
        if self.reason is not None:
            lowered_reason = self.reason.lower()
            sensitive_terms = (
                "password",
                "credential",
                "secret",
                "medical",
                "disability",
                "disciplinary",
                "counseling",
            )
            if any(term in lowered_reason for term in sensitive_terms):
                raise ConcordModelError(
                    "privacy reason must not embed sensitive or secret data."
                )
        if self.classification == "inherited" and self.inherited_from is None:
            raise ConcordModelError("inherited privacy requires inherited_from.")
        if self.classification == "external_policy" and self.policy_reference is None:
            raise ConcordModelError(
                "external_policy privacy requires policy_reference."
            )
        if self.classification not in {"inherited", "external_policy"} and (
            self.policy_reference is not None or self.inherited_from is not None
        ):
            raise ConcordModelError(
                "direct privacy classifications cannot carry resolution references."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class StatusReason:
    reason_code: str
    recorded_by: ActorReference
    recorded_at: str
    note: str | None = None
    related_record: ConcordRecordReference | ModuleRecordRef | None = None

    def __post_init__(self) -> None:
        controlled_key(
            self.reason_code,
            "reason_code",
            frozenset(
                {
                    "cancelled",
                    "interrupted",
                    "withdrawn",
                    "reassigned",
                    "superseded",
                    "insufficient_evidence",
                    "absent",
                    "excused",
                    "not_observed",
                    "not_applicable",
                    "deferred",
                }
            ),
        )
        if not isinstance(self.recorded_by, ActorReference):
            raise ConcordModelError("recorded_by must be an ActorReference.")
        timestamp(self.recorded_at, "recorded_at")
        optional_text(self.note, "note")
        if self.related_record is not None and not isinstance(
            self.related_record, (ConcordRecordReference, ModuleRecordRef)
        ):
            raise ConcordModelError("related_record is invalid.")


AuthorReference: TypeAlias = (
    ParticipantReference | ActorReference | ConcordRecordReference
)
AssigneeReference: TypeAlias = ParticipantReference | ConcordRecordReference
