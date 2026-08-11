"""Application services for contextual Role Assignments."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    EffectiveContext,
    GroupMembership,
    ParticipantReference,
    RoleAssignment,
)
from concord.storage import commit_record_batch
from concord.workflows._collaboration import (
    ACTIVE_ASSIGNMENT_STATUSES,
    context_is_within,
    current_records_of_kind,
    load_graph,
    require_end_status,
    require_group,
    require_membership,
    require_new_identity,
    require_reassignment_status,
    require_role,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    actor_reference,
    ensure_mutating_workspace_root,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import (
    AssignRoleRequest,
    EndRoleRequest,
    ReassignRoleRequest,
    RoleMutationResult,
    RoleSummary,
    WorkflowActor,
    WorkflowCommitResult,
)
from concord.workflows.participants import (
    participant_display_label,
    participant_sort_label,
    validate_participant_reference,
)


def _resolved_role_group(
    graph: ConcordRecordGraph,
    membership: GroupMembership | None,
    requested_group_id: str | None,
    effective_context: EffectiveContext,
) -> str | None:
    group_id = requested_group_id
    if membership is not None:
        if membership.status not in ACTIVE_ASSIGNMENT_STATUSES:
            raise ConcordWorkflowConflictError(
                "Role cannot use an ended Group Membership."
            )
        if group_id is None:
            group_id = membership.group_id
        elif group_id != membership.group_id:
            raise ConcordWorkflowValidationError(
                "Role Group must match the referenced Membership Group."
            )
        if not context_is_within(
            graph,
            effective_context,
            membership.effective_context,
        ):
            raise ConcordWorkflowValidationError(
                "Role Effective Context extends beyond the referenced Membership."
            )
    if group_id is not None:
        group = require_group(graph, group_id)
        if group.effective_context is not None and not context_is_within(
            graph,
            effective_context,
            group.effective_context,
        ):
            raise ConcordWorkflowValidationError(
                "Role Effective Context extends beyond the Group context."
            )
    return group_id


def _build_role(
    *,
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    role_assignment_id: str,
    participant_reference: ParticipantReference,
    role_key: str,
    effective_context: EffectiveContext,
    status: str,
    actor: WorkflowActor,
    membership_id: str | None,
    group_id: str | None,
    role_label_snapshot: str | None,
    supersedes_role_assignment_id: str | None,
    clock: Clock | None,
) -> RoleAssignment:
    participant = validate_participant_reference(root, class_id, participant_reference)
    membership = (
        None if membership_id is None else require_membership(graph, membership_id)
    )
    if membership is not None and membership.participant_reference != participant:
        raise ConcordWorkflowValidationError(
            "Role participant must match the referenced Membership participant."
        )
    resolved_group_id = _resolved_role_group(
        graph,
        membership,
        group_id,
        effective_context,
    )
    return RoleAssignment(
        role_assignment_id=role_assignment_id,
        activity_id=effective_context.activity_id,
        participant_reference=participant,
        role_key=role_key,
        effective_context=effective_context,
        status=status,
        assigned_by=actor_reference(actor),
        created_provenance=provenance(actor, clock=clock),
        membership_id=membership_id,
        group_id=resolved_group_id,
        role_label_snapshot=role_label_snapshot,
        supersedes_role_assignment_id=supersedes_role_assignment_id,
    )


def assign_role(
    request: AssignRoleRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> RoleMutationResult:
    """Create one contextual Role Assignment."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_new_identity(
        graph.role_assignments,
        "role_assignment_id",
        request.role_assignment_id,
        "Role Assignment",
    )
    role = _build_role(
        root=root,
        class_id=request.class_id,
        graph=graph,
        role_assignment_id=request.role_assignment_id,
        participant_reference=request.participant_reference,
        role_key=request.role_key,
        effective_context=request.effective_context,
        status=request.status,
        actor=request.actor,
        membership_id=request.membership_id,
        group_id=request.group_id,
        role_label_snapshot=request.role_label_snapshot,
        supersedes_role_assignment_id=None,
        clock=clock,
    )
    if role.activity_id != request.activity_id:
        raise ConcordWorkflowValidationError(
            "Role Effective Context must identify the selected Activity."
        )
    result = commit_record_batch(
        root,
        work,
        (role,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return RoleMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        role_assignment_id=role.role_assignment_id,
    )


def list_roles(
    class_id: str,
    activity_id: str,
    *,
    group_id: str | None = None,
    workspace_root: str | Path | None = None,
) -> tuple[RoleSummary, ...]:
    """List current Role Assignments with best-effort participant display labels."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = work_ref(class_id, activity_id)
    records, revision = current_records_of_kind(root, work, "role_assignment")
    roles = tuple(item for item in records if isinstance(item, RoleAssignment))
    summaries = [
        RoleSummary(
            class_id=class_id,
            activity_id=activity_id,
            role_assignment_id=role.role_assignment_id,
            participant_reference=role.participant_reference,
            participant_display_label=participant_display_label(
                root,
                class_id,
                role.participant_reference,
            ),
            role_key=role.role_key,
            status=role.status,
            group_id=role.group_id,
            membership_id=role.membership_id,
            effective_context=role.effective_context,
            supersedes_role_assignment_id=role.supersedes_role_assignment_id,
            snapshot_revision=revision,
        )
        for role in roles
        if group_id is None or role.group_id == group_id
    ]
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.group_id or "",
                item.role_key,
                participant_sort_label(
                    root,
                    class_id,
                    item.participant_reference,
                ),
                item.role_assignment_id,
            ),
        )
    )


def end_role(
    request: EndRoleRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> RoleMutationResult:
    """End a Role Assignment by status revision; never delete it."""
    require_end_status(request.status)
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = require_role(graph, request.role_assignment_id)
    candidate = replace(current, status=request.status)
    _ = clock
    _ = request.actor
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return RoleMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        role_assignment_id=candidate.role_assignment_id,
    )


def reassign_role(
    request: ReassignRoleRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> RoleMutationResult:
    """Atomically end a Role Assignment and create a same-Activity successor."""
    require_reassignment_status(request.predecessor_status)
    if request.successor_status not in ACTIVE_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowValidationError(
            "reassignment successor status must be planned or active."
        )
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = require_role(graph, request.role_assignment_id)
    if current.status not in ACTIVE_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowConflictError(
            "Only a planned or active Role Assignment can be reassigned."
        )
    require_new_identity(
        graph.role_assignments,
        "role_assignment_id",
        request.successor_role_assignment_id,
        "Role Assignment",
    )
    predecessor = replace(current, status=request.predecessor_status)
    successor = _build_role(
        root=root,
        class_id=request.class_id,
        graph=graph,
        role_assignment_id=request.successor_role_assignment_id,
        participant_reference=request.participant_reference,
        role_key=request.role_key,
        effective_context=request.effective_context,
        status=request.successor_status,
        actor=request.actor,
        membership_id=request.membership_id,
        group_id=request.group_id,
        role_label_snapshot=request.role_label_snapshot,
        supersedes_role_assignment_id=current.role_assignment_id,
        clock=clock,
    )
    if successor.activity_id != current.activity_id:
        raise ConcordWorkflowValidationError(
            "Role successor must remain in the same Activity."
        )
    result = commit_record_batch(
        root,
        work,
        (predecessor, successor),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return RoleMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        role_assignment_id=successor.role_assignment_id,
        predecessor_role_assignment_id=predecessor.role_assignment_id,
    )
