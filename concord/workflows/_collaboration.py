"""Internal helpers shared by collaboration-context application services."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.model_conversion import Record
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    Activity,
    EffectiveContext,
    Group,
    GroupMembership,
    ResponsibilityAssignment,
    RoleAssignment,
    Session,
)
from concord.storage import (
    load_current_record_graph,
    load_current_snapshot,
    load_record_revision,
    load_work_snapshot,
)
from concord.storage_errors import ConcordStorageNotFoundError
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)

ACTIVE_ASSIGNMENT_STATUSES = frozenset({"planned", "active"})
END_ASSIGNMENT_STATUSES = frozenset({"completed", "withdrawn", "cancelled"})
REASSIGNMENT_PREDECESSOR_STATUSES = frozenset({"reassigned", "superseded"})


def work_ref(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef(module_id="concord", class_id=class_id, work_id=activity_id)


def load_graph(
    root: str | Path,
    work: ModuleWorkRef,
    standards_library: StandardsLibrary | None = None,
) -> tuple[ConcordRecordGraph, int, str]:
    """Load the exact current graph required by a mutating collaboration workflow."""
    try:
        loaded = load_current_record_graph(
            root,
            work,
            standards_library=standards_library,
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {work.work_id}"
        ) from error
    graph = cast(ConcordRecordGraph, loaded.graph)
    return graph, loaded.snapshot_revision, loaded.snapshot_sha256



def current_records_of_kind(
    root: str | Path,
    work: ModuleWorkRef,
    record_kind: str,
) -> tuple[tuple[Record, ...], int]:
    """Read current records of one kind without requiring Core standards context."""
    try:
        current = load_current_snapshot(root, work)
        snapshot, _ = load_work_snapshot(root, work, current.snapshot_revision)
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {work.work_id}"
        ) from error
    records: list[Record] = []
    for reference in snapshot.records:
        if reference.record_kind != record_kind:
            continue
        record, _ = load_record_revision(
            root,
            work,
            reference.record_kind,
            reference.record_id,
            reference.record_revision,
        )
        records.append(record)
    return tuple(records), current.snapshot_revision

def require_activity(graph: ConcordRecordGraph, activity_id: str) -> Activity:
    for activity in graph.activities:
        if activity.activity_id == activity_id:
            return activity
    raise ConcordWorkflowNotFoundError(f"Activity is not available: {activity_id}")


def require_group(graph: ConcordRecordGraph, group_id: str) -> Group:
    for group in graph.groups:
        if group.group_id == group_id:
            return group
    raise ConcordWorkflowNotFoundError(f"Group is not available: {group_id}")


def require_membership(
    graph: ConcordRecordGraph,
    membership_id: str,
) -> GroupMembership:
    for membership in graph.memberships:
        if membership.membership_id == membership_id:
            return membership
    raise ConcordWorkflowNotFoundError(
        f"Group Membership is not available: {membership_id}"
    )


def require_role(graph: ConcordRecordGraph, role_assignment_id: str) -> RoleAssignment:
    for role in graph.role_assignments:
        if role.role_assignment_id == role_assignment_id:
            return role
    raise ConcordWorkflowNotFoundError(
        f"Role Assignment is not available: {role_assignment_id}"
    )


def require_responsibility(
    graph: ConcordRecordGraph,
    responsibility_assignment_id: str,
) -> ResponsibilityAssignment:
    for responsibility in graph.responsibility_assignments:
        if (
            responsibility.responsibility_assignment_id
            == responsibility_assignment_id
        ):
            return responsibility
    raise ConcordWorkflowNotFoundError(
        "Responsibility Assignment is not available: "
        f"{responsibility_assignment_id}"
    )


def require_new_identity(
    records: tuple[object, ...],
    identity_field: str,
    identity: str,
    label: str,
) -> None:
    if any(getattr(record, identity_field) == identity for record in records):
        raise ConcordWorkflowConflictError(f"{label} already exists: {identity}")


def session_index(graph: ConcordRecordGraph) -> dict[str, Session]:
    return {session.session_id: session for session in graph.sessions}


def context_session_ids(
    graph: ConcordRecordGraph,
    context: EffectiveContext,
) -> frozenset[str]:
    """Expand a context to the Sessions it currently covers for overlap checks."""
    sessions = session_index(graph)
    selected = {
        session_id for session_id in context.session_ids if session_id in sessions
    }
    if not selected:
        return frozenset()

    selected_sequences = [sessions[session_id].sequence for session_id in selected]
    start = context.sequence_start
    end = context.sequence_end
    if context.applies_to_remaining_activity:
        if start is None:
            start = min(selected_sequences)
        for session in graph.sessions:
            if session.activity_id != context.activity_id:
                continue
            if session.sequence < start:
                continue
            if end is not None and session.sequence > end:
                continue
            selected.add(session.session_id)
    elif start is not None or end is not None:
        lower = min(selected_sequences) if start is None else start
        upper = max(selected_sequences) if end is None else end
        for session in graph.sessions:
            if (
                session.activity_id == context.activity_id
                and lower <= session.sequence <= upper
            ):
                selected.add(session.session_id)
    return frozenset(selected)


def context_is_within(
    graph: ConcordRecordGraph,
    candidate: EffectiveContext,
    container: EffectiveContext,
) -> bool:
    if candidate.activity_id != container.activity_id:
        return False
    return context_session_ids(graph, candidate) <= context_session_ids(
        graph, container
    )


def contexts_overlap(
    graph: ConcordRecordGraph,
    left: EffectiveContext,
    right: EffectiveContext,
) -> bool:
    if left.activity_id != right.activity_id:
        return False
    return bool(context_session_ids(graph, left) & context_session_ids(graph, right))


def require_end_status(status: str) -> None:
    if status not in END_ASSIGNMENT_STATUSES:
        allowed = ", ".join(sorted(END_ASSIGNMENT_STATUSES))
        raise ConcordWorkflowValidationError(
            f"end status must be one of: {allowed}."
        )


def require_reassignment_status(status: str) -> None:
    if status not in REASSIGNMENT_PREDECESSOR_STATUSES:
        allowed = ", ".join(sorted(REASSIGNMENT_PREDECESSOR_STATUSES))
        raise ConcordWorkflowValidationError(
            f"reassignment predecessor status must be one of: {allowed}."
        )
