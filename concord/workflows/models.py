"""Immutable request/result models for Concord collaboration workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias, TypeVar

from pds_core.routing_models import ModuleWorkRef

from concord.models import (
    ActorReference,
    ConcordRecordReference,
    EffectiveContext,
    ParticipantReference,
    PrivacyPolicy,
    StatusReason,
)
from concord.storage_models import ConcordStorageCommitResult


class _UnsetType:
    __slots__ = ()


UNSET = _UnsetType()
T = TypeVar("T")

TextUpdate: TypeAlias = str | _UnsetType
OptionalTextUpdate: TypeAlias = str | None | _UnsetType
StringTupleUpdate: TypeAlias = tuple[str, ...] | _UnsetType
OptionalPrivacyUpdate: TypeAlias = PrivacyPolicy | None | _UnsetType
OptionalStatusReasonUpdate: TypeAlias = StatusReason | None | _UnsetType
OptionalContextUpdate: TypeAlias = EffectiveContext | None | _UnsetType
PositiveIntUpdate: TypeAlias = int | _UnsetType
WorkflowAssigneeReference: TypeAlias = ParticipantReference | ConcordRecordReference


def resolve_update(current: T, update: T | _UnsetType) -> T:
    """Resolve a partial-update field without conflating None with omission."""
    if isinstance(update, _UnsetType):
        return current
    return update


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowActor:
    """Durable actor identity supplied by a workflow caller."""

    actor_id: str
    actor_kind: str = "authorized_adult"
    owning_system: str = "concord"
    display_label: str | None = None
    role_label: str | None = None

    def __post_init__(self) -> None:
        # Reuse the native contract for exact structural validation.
        ActorReference(
            actor_kind=self.actor_kind,
            actor_id=self.actor_id,
            owning_system=self.owning_system,
            display_label_snapshot=self.display_label,
            role_snapshot=self.role_label,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceBootstrapResult:
    root: Path
    created: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class ClassSummary:
    class_id: str
    school_year: str


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowRecordRevision:
    record_kind: str
    record_id: str
    record_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowCommitResult:
    work: ModuleWorkRef
    snapshot_revision: int
    snapshot_sha256: str
    changed_records: tuple[WorkflowRecordRevision, ...]
    no_op: bool
    workspace_created: bool = False

    @classmethod
    def from_storage(
        cls,
        result: ConcordStorageCommitResult,
        *,
        workspace_created: bool = False,
    ) -> "WorkflowCommitResult":
        return cls(
            work=result.work,
            snapshot_revision=result.snapshot_revision,
            snapshot_sha256=result.snapshot_sha256,
            changed_records=tuple(
                WorkflowRecordRevision(
                    record_kind=item.record_kind,
                    record_id=item.record_id,
                    record_revision=item.record_revision,
                )
                for item in result.created_record_revisions
            ),
            no_op=result.no_op,
            workspace_created=workspace_created,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivitySummary:
    class_id: str
    activity_id: str
    title: str
    status: str
    scoring_orientation: str
    session_count: int
    group_count: int
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionSummary:
    class_id: str
    activity_id: str
    session_id: str
    sequence: int
    label: str | None
    status: str
    scheduled_start: str | None
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityDetail:
    summary: ActivitySummary
    description: str | None
    activity_type: str
    standards_profile_id: str | None
    focus_standard_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityContextResult:
    commit: WorkflowCommitResult
    activity_id: str
    first_session_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityUpdateResult:
    commit: WorkflowCommitResult
    activity_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionMutationResult:
    commit: WorkflowCommitResult
    session_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupSummary:
    class_id: str
    activity_id: str
    group_id: str
    label: str
    status: str
    member_count: int
    parent_group_id: str | None
    effective_session_count: int
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupDetail:
    summary: GroupSummary
    description: str | None
    effective_context: EffectiveContext | None
    supersedes_group_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class MembershipSummary:
    class_id: str
    activity_id: str
    membership_id: str
    group_id: str
    participant_reference: ParticipantReference
    participant_display_label: str | None
    status: str
    effective_context: EffectiveContext
    supersedes_membership_id: str | None
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleSummary:
    class_id: str
    activity_id: str
    role_assignment_id: str
    participant_reference: ParticipantReference
    participant_display_label: str | None
    role_key: str
    status: str
    group_id: str | None
    membership_id: str | None
    effective_context: EffectiveContext
    supersedes_role_assignment_id: str | None
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ResponsibilitySummary:
    class_id: str
    activity_id: str
    responsibility_assignment_id: str
    assignee_reference: WorkflowAssigneeReference
    assignee_display_label: str | None
    description: str
    status: str
    group_id: str | None
    effective_context: EffectiveContext
    supersedes_responsibility_assignment_id: str | None
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupMutationResult:
    commit: WorkflowCommitResult
    group_id: str
    membership_ids: tuple[str, ...] = ()
    role_assignment_ids: tuple[str, ...] = ()
    responsibility_assignment_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class MembershipBatchMutationResult:
    commit: WorkflowCommitResult
    membership_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class MembershipMutationResult:
    commit: WorkflowCommitResult
    membership_id: str
    predecessor_membership_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RoleMutationResult:
    commit: WorkflowCommitResult
    role_assignment_id: str
    predecessor_role_assignment_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ResponsibilityMutationResult:
    commit: WorkflowCommitResult
    responsibility_assignment_id: str
    predecessor_responsibility_assignment_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateActivityContextRequest:
    class_id: str
    activity_id: str
    title: str
    activity_type: str
    scoring_orientation: str
    session_id: str
    actor: WorkflowActor
    activity_status: str = "draft"
    session_sequence: int = 1
    session_status: str = "planned"
    description: str | None = None
    standards_profile_id: str | None = None
    focus_standard_ids: tuple[str, ...] = ()
    privacy_policy: PrivacyPolicy | None = None
    external_reference_ids: tuple[str, ...] = ()
    session_label: str | None = None
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    session_notes: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateActivityRequest:
    class_id: str
    activity_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    title: TextUpdate = UNSET
    description: OptionalTextUpdate = UNSET
    activity_type: TextUpdate = UNSET
    scoring_orientation: TextUpdate = UNSET
    standards_profile_id: OptionalTextUpdate = UNSET
    focus_standard_ids: StringTupleUpdate = UNSET
    status: TextUpdate = UNSET
    privacy_policy: OptionalPrivacyUpdate = UNSET
    external_reference_ids: StringTupleUpdate = UNSET


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateSessionRequest:
    class_id: str
    activity_id: str
    session_id: str
    sequence: int
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "planned"
    label: str | None = None
    scheduled_start: str | None = None
    scheduled_end: str | None = None
    actual_start: str | None = None
    actual_end: str | None = None
    status_reason: StatusReason | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateSessionRequest:
    class_id: str
    activity_id: str
    session_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    sequence: PositiveIntUpdate = UNSET
    status: TextUpdate = UNSET
    label: OptionalTextUpdate = UNSET
    scheduled_start: OptionalTextUpdate = UNSET
    scheduled_end: OptionalTextUpdate = UNSET
    actual_start: OptionalTextUpdate = UNSET
    actual_end: OptionalTextUpdate = UNSET
    status_reason: OptionalStatusReasonUpdate = UNSET
    notes: OptionalTextUpdate = UNSET


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateGroupRequest:
    class_id: str
    activity_id: str
    group_id: str
    label: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "planned"
    description: str | None = None
    parent_group_id: str | None = None
    effective_context: EffectiveContext | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateGroupRequest:
    class_id: str
    activity_id: str
    group_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    label: TextUpdate = UNSET
    status: TextUpdate = UNSET
    description: OptionalTextUpdate = UNSET
    parent_group_id: OptionalTextUpdate = UNSET
    effective_context: OptionalContextUpdate = UNSET


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupMemberSpec:
    membership_id: str
    student_id: str
    effective_context: EffectiveContext
    status: str = "active"


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupRoleSpec:
    role_assignment_id: str
    participant_reference: ParticipantReference
    role_key: str
    effective_context: EffectiveContext
    status: str = "active"
    membership_id: str | None = None
    role_label_snapshot: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupResponsibilitySpec:
    responsibility_assignment_id: str
    assignee_reference: WorkflowAssigneeReference
    description: str
    effective_context: EffectiveContext
    status: str = "active"
    work_item_id: str | None = None
    expected_output: str | None = None
    status_reason: StatusReason | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateGroupWithMembersRequest:
    class_id: str
    activity_id: str
    group_id: str
    label: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    members: tuple[GroupMemberSpec, ...]
    roles: tuple[GroupRoleSpec, ...] = ()
    responsibilities: tuple[GroupResponsibilitySpec, ...] = ()
    status: str = "planned"
    description: str | None = None
    parent_group_id: str | None = None
    effective_context: EffectiveContext | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AddMembershipsRequest:
    class_id: str
    activity_id: str
    group_id: str
    members: tuple[GroupMemberSpec, ...]
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class AddMembershipRequest:
    class_id: str
    activity_id: str
    group_id: str
    membership_id: str
    student_id: str
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "active"


@dataclass(frozen=True, slots=True, kw_only=True)
class EndMembershipRequest:
    class_id: str
    activity_id: str
    membership_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str
    status_reason: StatusReason | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReassignMembershipRequest:
    class_id: str
    activity_id: str
    membership_id: str
    successor_membership_id: str
    new_group_id: str
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    predecessor_status: str = "reassigned"
    successor_status: str = "active"
    predecessor_status_reason: StatusReason | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AssignRoleRequest:
    class_id: str
    activity_id: str
    role_assignment_id: str
    participant_reference: ParticipantReference
    role_key: str
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "active"
    membership_id: str | None = None
    group_id: str | None = None
    role_label_snapshot: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class EndRoleRequest:
    class_id: str
    activity_id: str
    role_assignment_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ReassignRoleRequest:
    class_id: str
    activity_id: str
    role_assignment_id: str
    successor_role_assignment_id: str
    participant_reference: ParticipantReference
    role_key: str
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    membership_id: str | None = None
    group_id: str | None = None
    role_label_snapshot: str | None = None
    predecessor_status: str = "reassigned"
    successor_status: str = "active"


@dataclass(frozen=True, slots=True, kw_only=True)
class AssignResponsibilityRequest:
    class_id: str
    activity_id: str
    responsibility_assignment_id: str
    assignee_reference: WorkflowAssigneeReference
    description: str
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "active"
    group_id: str | None = None
    work_item_id: str | None = None
    expected_output: str | None = None
    status_reason: StatusReason | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class EndResponsibilityRequest:
    class_id: str
    activity_id: str
    responsibility_assignment_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str
    status_reason: StatusReason | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReassignResponsibilityRequest:
    class_id: str
    activity_id: str
    responsibility_assignment_id: str
    successor_responsibility_assignment_id: str
    assignee_reference: WorkflowAssigneeReference
    description: str
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    group_id: str | None = None
    work_item_id: str | None = None
    expected_output: str | None = None
    predecessor_status: str = "reassigned"
    successor_status: str = "active"
    predecessor_status_reason: StatusReason | None = None
    successor_status_reason: StatusReason | None = None
