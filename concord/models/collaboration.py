"""Activity, Session, Group, and contextual assignment records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

from concord.models.common import (
    ActorReference,
    AssigneeReference,
    ConcordModelError,
    ConcordRecordReference,
    EffectiveContext,
    ParticipantReference,
    PrivacyPolicy,
    Provenance,
    StatusReason,
    controlled,
    controlled_key,
    identifier,
    optional_identifier,
    optional_text,
    optional_timestamp,
    positive_int,
    require_text,
    tuple_of_identifiers,
)

ACTIVITY_TYPES = frozenset({"socratic_seminar", "laboratory", "project"})
SCORING_ORIENTATIONS = frozenset(
    {"evidence_only", "standards_based", "mixed", "local_criteria_only"}
)

ASSIGNMENT_STATUSES = frozenset(
    {
        "planned",
        "active",
        "completed",
        "withdrawn",
        "reassigned",
        "cancelled",
        "superseded",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class Activity:
    activity_id: str
    class_reference: ModuleRecordRef
    title: str
    activity_type: str
    scoring_orientation: str
    status: str
    created_provenance: Provenance
    standards_profile_id: str | None = None
    focus_standard_ids: tuple[str, ...] = ()
    description: str | None = None
    criterion_set_ids: tuple[str, ...] = ()
    privacy_policy: PrivacyPolicy | None = None
    updated_provenance: Provenance | None = None
    external_reference_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        identifier(self.activity_id, "activity_id")
        if not isinstance(self.class_reference, ModuleRecordRef):
            raise ConcordModelError("class_reference must be a ModuleRecordRef.")
        if (
            self.class_reference.module_id != "core"
            or self.class_reference.record_kind != "class"
        ):
            raise ConcordModelError("class_reference must identify a Core class.")
        require_text(self.title, "title")
        controlled_key(
            self.activity_type,
            "activity_type",
            ACTIVITY_TYPES,
        )
        orientation = controlled(
            self.scoring_orientation,
            "scoring_orientation",
            SCORING_ORIENTATIONS,
        )
        controlled(
            self.status,
            "status",
            frozenset(
                {"draft", "configured", "active", "completed", "cancelled", "archived"}
            ),
        )
        optional_identifier(self.standards_profile_id, "standards_profile_id")
        object.__setattr__(
            self,
            "focus_standard_ids",
            tuple_of_identifiers(self.focus_standard_ids, "focus_standard_ids"),
        )
        object.__setattr__(
            self,
            "criterion_set_ids",
            tuple_of_identifiers(self.criterion_set_ids, "criterion_set_ids"),
        )
        object.__setattr__(
            self,
            "external_reference_ids",
            tuple_of_identifiers(self.external_reference_ids, "external_reference_ids"),
        )
        optional_text(self.description, "description")
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.updated_provenance is not None and not isinstance(
            self.updated_provenance, Provenance
        ):
            raise ConcordModelError("updated_provenance must be Provenance.")
        if self.privacy_policy is not None and not isinstance(
            self.privacy_policy, PrivacyPolicy
        ):
            raise ConcordModelError("privacy_policy must be PrivacyPolicy.")
        if orientation in {"standards_based", "mixed"} and (
            self.standards_profile_id is None or not self.focus_standard_ids
        ):
            raise ConcordModelError(
                "standards_based and mixed activities require a profile "
                "and focus standards."
            )

    @property
    def work_reference(self) -> ModuleWorkRef:
        return ModuleWorkRef(
            module_id="concord",
            class_id=self.class_reference.record_id,
            work_id=self.activity_id,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class Session:
    session_id: str
    activity_id: str
    sequence: int
    status: str
    created_provenance: Provenance
    label: str | None = None
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    actual_start: str | None = None
    actual_end: str | None = None
    status_reason: StatusReason | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        identifier(self.session_id, "session_id")
        identifier(self.activity_id, "activity_id")
        positive_int(self.sequence, "sequence")
        controlled(
            self.status,
            "status",
            frozenset(
                {
                    "planned",
                    "active",
                    "completed",
                    "cancelled",
                    "interrupted",
                    "archived",
                }
            ),
        )
        optional_text(self.label, "label")
        for name in ("scheduled_start", "scheduled_end", "actual_start", "actual_end"):
            optional_timestamp(getattr(self, name), name)
        if (
            self.scheduled_start
            and self.scheduled_end
            and datetime.fromisoformat(self.scheduled_end.replace("Z", "+00:00"))
            < datetime.fromisoformat(self.scheduled_start.replace("Z", "+00:00"))
        ):
            raise ConcordModelError("scheduled_end must not precede scheduled_start.")
        if (
            self.actual_start
            and self.actual_end
            and datetime.fromisoformat(self.actual_end.replace("Z", "+00:00"))
            < datetime.fromisoformat(self.actual_start.replace("Z", "+00:00"))
        ):
            raise ConcordModelError("actual_end must not precede actual_start.")
        optional_text(self.notes, "notes")
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.status_reason is not None and not isinstance(
            self.status_reason, StatusReason
        ):
            raise ConcordModelError("status_reason must be StatusReason.")


@dataclass(frozen=True, slots=True, kw_only=True)
class Group:
    group_id: str
    activity_id: str
    label: str
    status: str
    created_provenance: Provenance
    description: str | None = None
    parent_group_id: str | None = None
    effective_context: EffectiveContext | None = None
    supersedes_group_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.group_id, "group_id")
        identifier(self.activity_id, "activity_id")
        require_text(self.label, "label")
        optional_text(self.description, "description")
        optional_identifier(self.parent_group_id, "parent_group_id")
        optional_identifier(self.supersedes_group_id, "supersedes_group_id")
        controlled(
            self.status,
            "status",
            frozenset(
                {
                    "planned",
                    "active",
                    "inactive",
                    "completed",
                    "cancelled",
                    "archived",
                    "superseded",
                }
            ),
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.effective_context is not None and not isinstance(
            self.effective_context, EffectiveContext
        ):
            raise ConcordModelError("effective_context must be EffectiveContext.")


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupMembership:
    membership_id: str
    group_id: str
    participant_reference: ParticipantReference
    effective_context: EffectiveContext
    status: str
    created_provenance: Provenance
    status_reason: StatusReason | None = None
    supersedes_membership_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.membership_id, "membership_id")
        identifier(self.group_id, "group_id")
        if not isinstance(self.participant_reference, ParticipantReference):
            raise ConcordModelError(
                "participant_reference must be ParticipantReference."
            )
        if not isinstance(self.effective_context, EffectiveContext):
            raise ConcordModelError("effective_context must be EffectiveContext.")
        controlled(self.status, "status", ASSIGNMENT_STATUSES)
        optional_identifier(self.supersedes_membership_id, "supersedes_membership_id")
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.status_reason is not None and not isinstance(
            self.status_reason, StatusReason
        ):
            raise ConcordModelError("status_reason must be StatusReason.")


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleAssignment:
    role_assignment_id: str
    activity_id: str
    participant_reference: ParticipantReference
    role_key: str
    effective_context: EffectiveContext
    status: str
    assigned_by: ActorReference
    created_provenance: Provenance
    membership_id: str | None = None
    group_id: str | None = None
    role_label_snapshot: str | None = None
    supersedes_role_assignment_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.role_assignment_id, "role_assignment_id")
        identifier(self.activity_id, "activity_id")
        if not isinstance(self.participant_reference, ParticipantReference):
            raise ConcordModelError(
                "participant_reference must be ParticipantReference."
            )
        optional_identifier(self.membership_id, "membership_id")
        optional_identifier(self.group_id, "group_id")
        controlled_key(
            self.role_key,
            "role_key",
            frozenset(
                {
                    "facilitator",
                    "recorder",
                    "observer",
                    "speaker",
                    "researcher",
                    "builder",
                    "presenter",
                }
            ),
        )
        optional_text(self.role_label_snapshot, "role_label_snapshot")
        controlled(self.status, "status", ASSIGNMENT_STATUSES)
        optional_identifier(
            self.supersedes_role_assignment_id, "supersedes_role_assignment_id"
        )
        if not isinstance(self.effective_context, EffectiveContext):
            raise ConcordModelError("effective_context must be EffectiveContext.")
        if not isinstance(self.assigned_by, ActorReference):
            raise ConcordModelError("assigned_by must be ActorReference.")
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")


@dataclass(frozen=True, slots=True, kw_only=True)
class ResponsibilityAssignment:
    responsibility_assignment_id: str
    activity_id: str
    assignee_reference: AssigneeReference
    description: str
    effective_context: EffectiveContext
    status: str
    assigned_by: ActorReference
    created_provenance: Provenance
    group_id: str | None = None
    work_item_id: str | None = None
    expected_output: str | None = None
    status_reason: StatusReason | None = None
    supersedes_responsibility_assignment_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.responsibility_assignment_id, "responsibility_assignment_id")
        identifier(self.activity_id, "activity_id")
        if not isinstance(
            self.assignee_reference,
            (ParticipantReference, ConcordRecordReference),
        ):
            raise ConcordModelError("assignee_reference is invalid.")
        require_text(self.description, "description")
        optional_identifier(self.group_id, "group_id")
        optional_identifier(self.work_item_id, "work_item_id")
        optional_text(self.expected_output, "expected_output")
        controlled(self.status, "status", ASSIGNMENT_STATUSES)
        optional_identifier(
            self.supersedes_responsibility_assignment_id,
            "supersedes_responsibility_assignment_id",
        )
        if not isinstance(self.effective_context, EffectiveContext):
            raise ConcordModelError("effective_context must be EffectiveContext.")
        if not isinstance(self.assigned_by, ActorReference):
            raise ConcordModelError("assigned_by must be ActorReference.")
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.status_reason is not None and not isinstance(
            self.status_reason, StatusReason
        ):
            raise ConcordModelError("status_reason must be StatusReason.")
