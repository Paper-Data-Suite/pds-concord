"""Application services for contextual Responsibility Assignments."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ConcordRecordReference,
    EffectiveContext,
    Group,
    ParticipantReference,
    ResponsibilityAssignment,
    StatusReason,
)
from concord.storage import commit_record_batch
from concord.workflows._collaboration import (
    ACTIVE_ASSIGNMENT_STATUSES,
    context_is_within,
    current_records_of_kind,
    load_graph,
    require_end_status,
    require_group,
    require_new_identity,
    require_reassignment_status,
    require_responsibility,
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
    AssignResponsibilityRequest,
    EndResponsibilityRequest,
    ReassignResponsibilityRequest,
    ResponsibilityMutationResult,
    ResponsibilitySummary,
    WorkflowActor,
    WorkflowAssigneeReference,
    WorkflowCommitResult,
)
from concord.workflows.participants import (
    participant_display_label,
    participant_sort_label,
    validate_participant_reference,
)


def _resolve_assignee_and_group(
    *,
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    assignee_reference: WorkflowAssigneeReference,
    requested_group_id: str | None,
    effective_context: EffectiveContext,
) -> tuple[WorkflowAssigneeReference, str | None]:
    group_id = requested_group_id
    if isinstance(assignee_reference, ParticipantReference):
        assignee: WorkflowAssigneeReference = validate_participant_reference(
            root,
            class_id,
            assignee_reference,
        )
    elif isinstance(assignee_reference, ConcordRecordReference):
        if assignee_reference.record_kind != "group":
            raise ConcordWorkflowValidationError(
                "Concord Responsibility assignees must identify a Group."
            )
        assignee_group = require_group(graph, assignee_reference.record_id)
        assignee = assignee_reference
        if group_id is None:
            group_id = assignee_group.group_id
        elif group_id != assignee_group.group_id:
            raise ConcordWorkflowValidationError(
                "Responsibility Group must match the Group assignee."
            )
    else:
        raise ConcordWorkflowValidationError(
            "Responsibility assignee reference is invalid."
        )

    if group_id is not None:
        group = require_group(graph, group_id)
        if group.effective_context is not None and not context_is_within(
            graph,
            effective_context,
            group.effective_context,
        ):
            raise ConcordWorkflowValidationError(
                "Responsibility Effective Context extends beyond the Group context."
            )
    return assignee, group_id


def _build_responsibility(
    *,
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    responsibility_assignment_id: str,
    assignee_reference: WorkflowAssigneeReference,
    description: str,
    effective_context: EffectiveContext,
    status: str,
    actor: WorkflowActor,
    group_id: str | None,
    work_item_id: str | None,
    expected_output: str | None,
    status_reason: StatusReason | None,
    supersedes_responsibility_assignment_id: str | None,
    clock: Clock | None,
) -> ResponsibilityAssignment:
    assignee, resolved_group_id = _resolve_assignee_and_group(
        root=root,
        class_id=class_id,
        graph=graph,
        assignee_reference=assignee_reference,
        requested_group_id=group_id,
        effective_context=effective_context,
    )
    return ResponsibilityAssignment(
        responsibility_assignment_id=responsibility_assignment_id,
        activity_id=effective_context.activity_id,
        assignee_reference=assignee,
        description=description,
        effective_context=effective_context,
        status=status,
        assigned_by=actor_reference(actor),
        created_provenance=provenance(actor, clock=clock),
        group_id=resolved_group_id,
        work_item_id=work_item_id,
        expected_output=expected_output,
        status_reason=status_reason,
        supersedes_responsibility_assignment_id=(
            supersedes_responsibility_assignment_id
        ),
    )


def assign_responsibility(
    request: AssignResponsibilityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ResponsibilityMutationResult:
    """Create one contextual Responsibility Assignment."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_new_identity(
        graph.responsibility_assignments,
        "responsibility_assignment_id",
        request.responsibility_assignment_id,
        "Responsibility Assignment",
    )
    responsibility = _build_responsibility(
        root=root,
        class_id=request.class_id,
        graph=graph,
        responsibility_assignment_id=request.responsibility_assignment_id,
        assignee_reference=request.assignee_reference,
        description=request.description,
        effective_context=request.effective_context,
        status=request.status,
        actor=request.actor,
        group_id=request.group_id,
        work_item_id=request.work_item_id,
        expected_output=request.expected_output,
        status_reason=request.status_reason,
        supersedes_responsibility_assignment_id=None,
        clock=clock,
    )
    if responsibility.activity_id != request.activity_id:
        raise ConcordWorkflowValidationError(
            "Responsibility Effective Context must identify the selected Activity."
        )
    result = commit_record_batch(
        root,
        work,
        (responsibility,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ResponsibilityMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        responsibility_assignment_id=responsibility.responsibility_assignment_id,
    )


def list_responsibilities(
    class_id: str,
    activity_id: str,
    *,
    group_id: str | None = None,
    workspace_root: str | Path | None = None,
) -> tuple[ResponsibilitySummary, ...]:
    """List current Responsibilities with compact assignee display metadata."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = work_ref(class_id, activity_id)
    records, revision = current_records_of_kind(
        root,
        work,
        "responsibility_assignment",
    )
    group_records, group_revision = current_records_of_kind(root, work, "group")
    if revision != group_revision:
        raise ConcordWorkflowValidationError(
            "Activity changed while Responsibility summaries were being read."
        )
    groups = {
        item.group_id: item for item in group_records if isinstance(item, Group)
    }
    summaries: list[ResponsibilitySummary] = []
    for responsibility in records:
        if not isinstance(responsibility, ResponsibilityAssignment):
            continue
        if group_id is not None and responsibility.group_id != group_id:
            continue
        if isinstance(responsibility.assignee_reference, ParticipantReference):
            display_label = participant_display_label(
                root,
                class_id,
                responsibility.assignee_reference,
            )
        else:
            assignee_group = groups.get(responsibility.assignee_reference.record_id)
            display_label = None if assignee_group is None else assignee_group.label
        summaries.append(
            ResponsibilitySummary(
                class_id=class_id,
                activity_id=activity_id,
                responsibility_assignment_id=(
                    responsibility.responsibility_assignment_id
                ),
                assignee_reference=responsibility.assignee_reference,
                assignee_display_label=display_label,
                description=responsibility.description,
                status=responsibility.status,
                group_id=responsibility.group_id,
                effective_context=responsibility.effective_context,
                supersedes_responsibility_assignment_id=(
                    responsibility.supersedes_responsibility_assignment_id
                ),
                snapshot_revision=revision,
            )
        )
    def sort_key(item: ResponsibilitySummary) -> tuple[str, str, str]:
        if isinstance(item.assignee_reference, ParticipantReference):
            assignee_key = participant_sort_label(
                root,
                class_id,
                item.assignee_reference,
            )
        else:
            assignee_key = (
                item.assignee_display_label
                or item.assignee_reference.record_id
            )
        return (item.group_id or "", assignee_key, item.responsibility_assignment_id)

    return tuple(sorted(summaries, key=sort_key))


def end_responsibility(
    request: EndResponsibilityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ResponsibilityMutationResult:
    """End a Responsibility by status revision; never delete it."""
    require_end_status(request.status)
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = require_responsibility(graph, request.responsibility_assignment_id)
    candidate = replace(
        current,
        status=request.status,
        status_reason=request.status_reason,
    )
    _ = clock
    _ = request.actor
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ResponsibilityMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        responsibility_assignment_id=candidate.responsibility_assignment_id,
    )


def reassign_responsibility(
    request: ReassignResponsibilityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ResponsibilityMutationResult:
    """Atomically end a Responsibility and create a same-Activity successor."""
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
    current = require_responsibility(graph, request.responsibility_assignment_id)
    if current.status not in ACTIVE_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowConflictError(
            "Only a planned or active Responsibility can be reassigned."
        )
    require_new_identity(
        graph.responsibility_assignments,
        "responsibility_assignment_id",
        request.successor_responsibility_assignment_id,
        "Responsibility Assignment",
    )
    predecessor = replace(
        current,
        status=request.predecessor_status,
        status_reason=request.predecessor_status_reason,
    )
    successor = _build_responsibility(
        root=root,
        class_id=request.class_id,
        graph=graph,
        responsibility_assignment_id=(
            request.successor_responsibility_assignment_id
        ),
        assignee_reference=request.assignee_reference,
        description=request.description,
        effective_context=request.effective_context,
        status=request.successor_status,
        actor=request.actor,
        group_id=request.group_id,
        work_item_id=request.work_item_id,
        expected_output=request.expected_output,
        status_reason=request.successor_status_reason,
        supersedes_responsibility_assignment_id=(
            current.responsibility_assignment_id
        ),
        clock=clock,
    )
    if successor.activity_id != current.activity_id:
        raise ConcordWorkflowValidationError(
            "Responsibility successor must remain in the same Activity."
        )
    result = commit_record_batch(
        root,
        work,
        (predecessor, successor),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ResponsibilityMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        responsibility_assignment_id=successor.responsibility_assignment_id,
        predecessor_responsibility_assignment_id=(
            predecessor.responsibility_assignment_id
        ),
    )
