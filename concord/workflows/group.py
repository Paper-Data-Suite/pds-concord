"""Application services for Groups and contextual Group Memberships."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import Group, GroupMembership
from concord.storage import commit_record_batch, load_current_record
from concord.storage_errors import ConcordStorageNotFoundError
from concord.workflows._collaboration import (
    ACTIVE_ASSIGNMENT_STATUSES,
    context_is_within,
    contexts_overlap,
    current_records_of_kind,
    load_graph,
    require_end_status,
    require_group,
    require_membership,
    require_new_identity,
    require_reassignment_status,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import (
    AddMembershipRequest,
    AddMembershipsRequest,
    CreateGroupRequest,
    CreateGroupWithMembersRequest,
    EndMembershipRequest,
    GroupDetail,
    GroupMemberSpec,
    GroupMutationResult,
    GroupSummary,
    MembershipBatchMutationResult,
    MembershipMutationResult,
    MembershipSummary,
    ReassignMembershipRequest,
    UpdateGroupRequest,
    WorkflowCommitResult,
    resolve_update,
)
from concord.workflows.participants import (
    core_student_participant,
    participant_display_label,
    participant_sort_label,
)
from concord.workflows.responsibility import _build_responsibility
from concord.workflows.role import _build_role


def _active_memberships_for_group(
    memberships: tuple[GroupMembership, ...],
    group_id: str,
) -> tuple[GroupMembership, ...]:
    return tuple(
        item
        for item in memberships
        if item.group_id == group_id and item.status in ACTIVE_ASSIGNMENT_STATUSES
    )


def _ensure_membership_context_available(
    graph: ConcordRecordGraph,
    memberships: tuple[GroupMembership, ...],
    candidate: GroupMembership,
    *,
    exclude_membership_id: str | None = None,
) -> None:
    if candidate.status not in ACTIVE_ASSIGNMENT_STATUSES:
        return
    for existing in memberships:
        if existing.membership_id == exclude_membership_id:
            continue
        if existing.status not in ACTIVE_ASSIGNMENT_STATUSES:
            continue
        if existing.group_id != candidate.group_id:
            continue
        if existing.participant_reference != candidate.participant_reference:
            continue
        if contexts_overlap(
            graph,
            existing.effective_context,
            candidate.effective_context,
        ):
            raise ConcordWorkflowConflictError(
                "Participant already has an active Membership in this Group for "
                "an overlapping Session context."
            )



def _require_membership_within_group_context(
    graph: ConcordRecordGraph,
    group: Group,
    membership: GroupMembership,
) -> None:
    if group.effective_context is None:
        return
    if not context_is_within(
        graph,
        membership.effective_context,
        group.effective_context,
    ):
        raise ConcordWorkflowValidationError(
            "Membership Effective Context extends beyond the Group context."
        )


def create_group(
    request: CreateGroupRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupMutationResult:
    """Create one empty Activity-specific Group."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_new_identity(graph.groups, "group_id", request.group_id, "Group")
    group = Group(
        group_id=request.group_id,
        activity_id=request.activity_id,
        label=request.label,
        status=request.status,
        created_provenance=provenance(request.actor, clock=clock),
        description=request.description,
        parent_group_id=request.parent_group_id,
        effective_context=request.effective_context,
    )
    result = commit_record_batch(
        root,
        work,
        (group,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_id=group.group_id,
    )


def create_group_with_members(
    request: CreateGroupWithMembersRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupMutationResult:
    """Create one Group and its initial collaboration context atomically."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_new_identity(graph.groups, "group_id", request.group_id, "Group")

    group = Group(
        group_id=request.group_id,
        activity_id=request.activity_id,
        label=request.label,
        status=request.status,
        created_provenance=provenance(request.actor, clock=clock),
        description=request.description,
        parent_group_id=request.parent_group_id,
        effective_context=request.effective_context,
    )
    created = provenance(request.actor, clock=clock)
    memberships: list[GroupMembership] = []
    seen_membership_ids: set[str] = set()
    for member in request.members:
        if member.membership_id in seen_membership_ids:
            raise ConcordWorkflowConflictError(
                f"Duplicate Membership identity in request: {member.membership_id}"
            )
        seen_membership_ids.add(member.membership_id)
        require_new_identity(
            graph.memberships,
            "membership_id",
            member.membership_id,
            "Group Membership",
        )
        candidate = GroupMembership(
            membership_id=member.membership_id,
            group_id=group.group_id,
            participant_reference=core_student_participant(
                root,
                request.class_id,
                member.student_id,
            ),
            effective_context=member.effective_context,
            status=member.status,
            created_provenance=created,
        )
        _require_membership_within_group_context(graph, group, candidate)
        _ensure_membership_context_available(
            graph,
            tuple(graph.memberships) + tuple(memberships),
            candidate,
        )
        memberships.append(candidate)

    candidate_graph = replace(
        graph,
        groups=(*graph.groups, group),
        memberships=(*graph.memberships, *memberships),
    )

    roles = []
    seen_role_ids: set[str] = set()
    for role_spec in request.roles:
        if role_spec.role_assignment_id in seen_role_ids:
            raise ConcordWorkflowConflictError(
                "Duplicate Role Assignment identity in request: "
                f"{role_spec.role_assignment_id}"
            )
        seen_role_ids.add(role_spec.role_assignment_id)
        require_new_identity(
            graph.role_assignments,
            "role_assignment_id",
            role_spec.role_assignment_id,
            "Role Assignment",
        )
        role = _build_role(
            root=root,
            class_id=request.class_id,
            graph=candidate_graph,
            role_assignment_id=role_spec.role_assignment_id,
            participant_reference=role_spec.participant_reference,
            role_key=role_spec.role_key,
            effective_context=role_spec.effective_context,
            status=role_spec.status,
            actor=request.actor,
            membership_id=role_spec.membership_id,
            group_id=group.group_id,
            role_label_snapshot=role_spec.role_label_snapshot,
            supersedes_role_assignment_id=None,
            clock=clock,
        )
        if role.activity_id != request.activity_id:
            raise ConcordWorkflowValidationError(
                "Role Effective Context must identify the selected Activity."
            )
        roles.append(role)

    responsibilities = []
    seen_responsibility_ids: set[str] = set()
    for responsibility_spec in request.responsibilities:
        if responsibility_spec.responsibility_assignment_id in seen_responsibility_ids:
            raise ConcordWorkflowConflictError(
                "Duplicate Responsibility Assignment identity in request: "
                f"{responsibility_spec.responsibility_assignment_id}"
            )
        seen_responsibility_ids.add(
            responsibility_spec.responsibility_assignment_id
        )
        require_new_identity(
            graph.responsibility_assignments,
            "responsibility_assignment_id",
            responsibility_spec.responsibility_assignment_id,
            "Responsibility Assignment",
        )
        responsibility = _build_responsibility(
            root=root,
            class_id=request.class_id,
            graph=candidate_graph,
            responsibility_assignment_id=(
                responsibility_spec.responsibility_assignment_id
            ),
            assignee_reference=responsibility_spec.assignee_reference,
            description=responsibility_spec.description,
            effective_context=responsibility_spec.effective_context,
            status=responsibility_spec.status,
            actor=request.actor,
            group_id=group.group_id,
            work_item_id=responsibility_spec.work_item_id,
            expected_output=responsibility_spec.expected_output,
            status_reason=responsibility_spec.status_reason,
            supersedes_responsibility_assignment_id=None,
            clock=clock,
        )
        if responsibility.activity_id != request.activity_id:
            raise ConcordWorkflowValidationError(
                "Responsibility Effective Context must identify the selected Activity."
            )
        responsibilities.append(responsibility)

    result = commit_record_batch(
        root,
        work,
        (group, *memberships, *roles, *responsibilities),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_id=group.group_id,
        membership_ids=tuple(item.membership_id for item in memberships),
        role_assignment_ids=tuple(item.role_assignment_id for item in roles),
        responsibility_assignment_ids=tuple(
            item.responsibility_assignment_id for item in responsibilities
        ),
    )


def list_groups(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[GroupSummary, ...]:
    """List compact current Group summaries without requiring SQLite."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = work_ref(class_id, activity_id)
    group_records, revision = current_records_of_kind(root, work, "group")
    membership_records, membership_revision = current_records_of_kind(
        root,
        work,
        "group_membership",
    )
    if revision != membership_revision:
        raise ConcordWorkflowValidationError(
            "Activity changed while Group summaries were being read."
        )
    groups = tuple(item for item in group_records if isinstance(item, Group))
    memberships = tuple(
        item for item in membership_records if isinstance(item, GroupMembership)
    )
    summaries = [
        GroupSummary(
            class_id=class_id,
            activity_id=activity_id,
            group_id=group.group_id,
            label=group.label,
            status=group.status,
            member_count=len(
                _active_memberships_for_group(memberships, group.group_id)
            ),
            parent_group_id=group.parent_group_id,
            effective_session_count=(
                0
                if group.effective_context is None
                else len(group.effective_context.session_ids)
            ),
            snapshot_revision=revision,
        )
        for group in groups
    ]
    return tuple(
        sorted(summaries, key=lambda item: (item.label.casefold(), item.group_id))
    )


def show_group(
    class_id: str,
    activity_id: str,
    group_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> GroupDetail:
    """Load one current Group with compact summary metadata."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    work = work_ref(class_id, activity_id)
    try:
        record, _ = load_current_record(root, work, "group", group_id)
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Group is not available: {group_id}"
        ) from error
    if not isinstance(record, Group):
        raise ConcordWorkflowNotFoundError(f"Group is not available: {group_id}")
    summary = next(
        (
            item
            for item in list_groups(class_id, activity_id, workspace_root=root)
            if item.group_id == group_id
        ),
        None,
    )
    if summary is None:
        raise ConcordWorkflowNotFoundError(f"Group is not available: {group_id}")
    return GroupDetail(
        summary=summary,
        description=record.description,
        effective_context=record.effective_context,
        supersedes_group_id=record.supersedes_group_id,
    )


def update_group(
    request: UpdateGroupRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupMutationResult:
    """Revise ordinary Group fields without changing durable Group identity."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = require_group(graph, request.group_id)
    candidate = Group(
        group_id=current.group_id,
        activity_id=current.activity_id,
        label=resolve_update(current.label, request.label),
        status=resolve_update(current.status, request.status),
        created_provenance=current.created_provenance,
        description=resolve_update(current.description, request.description),
        parent_group_id=resolve_update(
            current.parent_group_id,
            request.parent_group_id,
        ),
        effective_context=resolve_update(
            current.effective_context,
            request.effective_context,
        ),
        supersedes_group_id=current.supersedes_group_id,
    )
    # Group has creation provenance only in the accepted native contract. Actor and
    # clock remain workflow context; an ordinary storage revision must not invent
    # an updated-provenance field.
    _ = clock
    _ = request.actor
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_id=candidate.group_id,
    )


def list_memberships(
    class_id: str,
    activity_id: str,
    *,
    group_id: str | None = None,
    workspace_root: str | Path | None = None,
) -> tuple[MembershipSummary, ...]:
    """List current Membership records with best-effort roster display labels."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = work_ref(class_id, activity_id)
    records, revision = current_records_of_kind(root, work, "group_membership")
    memberships = tuple(item for item in records if isinstance(item, GroupMembership))
    summaries: list[MembershipSummary] = []
    for membership in memberships:
        if group_id is not None and membership.group_id != group_id:
            continue
        summaries.append(
            MembershipSummary(
                class_id=class_id,
                activity_id=activity_id,
                membership_id=membership.membership_id,
                group_id=membership.group_id,
                participant_reference=membership.participant_reference,
                participant_display_label=participant_display_label(
                    root,
                    class_id,
                    membership.participant_reference,
                ),
                status=membership.status,
                effective_context=membership.effective_context,
                supersedes_membership_id=membership.supersedes_membership_id,
                snapshot_revision=revision,
            )
        )
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.group_id,
                participant_sort_label(
                    root,
                    class_id,
                    item.participant_reference,
                ),
                item.membership_id,
            ),
        )
    )


def add_memberships(
    request: AddMembershipsRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> MembershipBatchMutationResult:
    """Add one or more roster students to one Group in one guarded commit."""
    if not request.members:
        raise ConcordWorkflowValidationError(
            "At least one Group Membership is required."
        )
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    group = require_group(graph, request.group_id)
    created = provenance(request.actor, clock=clock)
    candidates: list[GroupMembership] = []
    seen_ids: set[str] = set()
    for member in request.members:
        if member.membership_id in seen_ids:
            raise ConcordWorkflowConflictError(
                f"Duplicate Membership identity in request: {member.membership_id}"
            )
        seen_ids.add(member.membership_id)
        require_new_identity(
            graph.memberships,
            "membership_id",
            member.membership_id,
            "Group Membership",
        )
        candidate = GroupMembership(
            membership_id=member.membership_id,
            group_id=request.group_id,
            participant_reference=core_student_participant(
                root,
                request.class_id,
                member.student_id,
            ),
            effective_context=member.effective_context,
            status=member.status,
            created_provenance=created,
        )
        _require_membership_within_group_context(graph, group, candidate)
        _ensure_membership_context_available(
            graph,
            tuple(graph.memberships) + tuple(candidates),
            candidate,
        )
        candidates.append(candidate)
    result = commit_record_batch(
        root,
        work,
        tuple(candidates),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return MembershipBatchMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        membership_ids=tuple(item.membership_id for item in candidates),
    )


def add_membership(
    request: AddMembershipRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> MembershipMutationResult:
    """Add one Core-roster student Membership to an existing Group."""
    result = add_memberships(
        AddMembershipsRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_id=request.group_id,
            members=(
                GroupMemberSpec(
                    membership_id=request.membership_id,
                    student_id=request.student_id,
                    effective_context=request.effective_context,
                    status=request.status,
                ),
            ),
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
        ),
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )
    return MembershipMutationResult(
        commit=result.commit,
        membership_id=result.membership_ids[0],
    )


def end_membership(
    request: EndMembershipRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> MembershipMutationResult:
    """End one Membership by revising status; never delete the record."""
    require_end_status(request.status)
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = require_membership(graph, request.membership_id)
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
    return MembershipMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        membership_id=candidate.membership_id,
    )


def reassign_membership(
    request: ReassignMembershipRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> MembershipMutationResult:
    """Atomically end one Membership and create its successor in another Group."""
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
    current = require_membership(graph, request.membership_id)
    if current.status not in ACTIVE_ASSIGNMENT_STATUSES:
        raise ConcordWorkflowConflictError(
            "Only a planned or active Membership can be reassigned."
        )
    if current.group_id == request.new_group_id:
        raise ConcordWorkflowValidationError(
            "Membership reassignment requires a different Group."
        )
    new_group = require_group(graph, request.new_group_id)
    require_new_identity(
        graph.memberships,
        "membership_id",
        request.successor_membership_id,
        "Group Membership",
    )
    predecessor = replace(
        current,
        status=request.predecessor_status,
        status_reason=request.predecessor_status_reason,
    )
    successor = GroupMembership(
        membership_id=request.successor_membership_id,
        group_id=request.new_group_id,
        participant_reference=current.participant_reference,
        effective_context=request.effective_context,
        status=request.successor_status,
        created_provenance=provenance(request.actor, clock=clock),
        supersedes_membership_id=current.membership_id,
    )
    _require_membership_within_group_context(graph, new_group, successor)
    _ensure_membership_context_available(
        graph,
        tuple(graph.memberships),
        successor,
        exclude_membership_id=current.membership_id,
    )
    result = commit_record_batch(
        root,
        work,
        (predecessor, successor),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return MembershipMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        membership_id=successor.membership_id,
        predecessor_membership_id=predecessor.membership_id,
    )
