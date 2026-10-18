"""Reviewed export of actual Group/Membership placements to saved arrangements.

This read-only Activity projection is scoped to one explicitly selected Session.
It never infers placement from historical/ended memberships or scores.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from concord.class_group_arrangement_storage import (
    LoadedArrangement,
    create_arrangement,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
)
from concord.models import EffectiveContext, Group, GroupMembership
from concord.workflows._collaboration import current_records_of_kind, work_ref
from concord.workflows.activity import show_activity
from concord.workflows.context import (
    Clock,
    require_core_class,
    resolve_read_workspace_root,
    workflow_timestamp,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import SessionSummary, WorkflowActor
from concord.workflows.participants import load_required_roster
from concord.workflows.session import list_sessions

_ACTIVE = frozenset({"planned", "active"})


@dataclass(frozen=True, slots=True, kw_only=True)
class SaveOperationalGroupingRequest:
    class_id: str
    activity_id: str
    session_id: str
    arrangement_id: str
    name: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    acknowledge_unresolved: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedOperationalGroupingSave:
    class_id: str
    school_year: str
    source_activity_id: str
    source_session_id: str
    source_snapshot_revision: int
    arrangement_id: str
    name: str
    owner_actor_id: str
    groups: tuple[SavedArrangementGroup, ...]
    roster_student_ids: tuple[str, ...]
    unresolved_student_ids: tuple[str, ...]
    review_digest: str

    @property
    def assigned_count(self) -> int:
        return sum(len(group.student_ids) for group in self.groups)


def _session_covered(
    context: EffectiveContext,
    *,
    activity_id: str,
    session_id: str,
    sessions: tuple[SessionSummary, ...],
) -> bool:
    """Expand an EffectiveContext like collaboration.context_session_ids."""
    if context.activity_id != activity_id:
        raise ConcordWorkflowValidationError(
            "Membership/Group context belongs to another Activity."
        )
    indexed = {item.session_id: item.sequence for item in sessions}
    selected = {sid for sid in context.session_ids if sid in indexed}
    if not selected:
        raise ConcordWorkflowValidationError(
            "Operational Group context has no current Session references."
        )
    sequences = tuple(indexed[sid] for sid in selected)
    start, end = context.sequence_start, context.sequence_end
    if context.applies_to_remaining_activity:
        if start is None:
            start = min(sequences)
        selected.update(
            item.session_id
            for item in sessions
            if item.sequence >= start and (end is None or item.sequence <= end)
        )
    elif start is not None or end is not None:
        lower = min(sequences) if start is None else start
        upper = max(sequences) if end is None else end
        selected.update(
            item.session_id for item in sessions if lower <= item.sequence <= upper
        )
    return session_id in selected


def _snapshot(
    root: Path, request: SaveOperationalGroupingRequest
) -> tuple[tuple[Group, ...], tuple[GroupMembership, ...], tuple[SessionSummary, ...]]:
    summary = show_activity(
        request.class_id, request.activity_id, workspace_root=root
    ).summary
    if summary.snapshot_revision != request.expected_snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Source Activity changed; reload current Groups before saving."
        )
    work = work_ref(request.class_id, request.activity_id)
    group_records, group_revision = current_records_of_kind(root, work, "group")
    membership_records, membership_revision = current_records_of_kind(
        root, work, "group_membership"
    )
    sessions = list_sessions(request.class_id, request.activity_id, workspace_root=root)
    if (
        group_revision != request.expected_snapshot_revision
        or membership_revision != request.expected_snapshot_revision
        or any(
            s.snapshot_revision != request.expected_snapshot_revision for s in sessions
        )
        or show_activity(
            request.class_id, request.activity_id, workspace_root=root
        ).summary.snapshot_revision
        != request.expected_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Source Activity changed during grouping review; reload and retry."
        )
    if not any(s.session_id == request.session_id for s in sessions):
        raise ConcordWorkflowNotFoundError(
            "Selected source Session is not present in the Activity."
        )
    return (
        tuple(g for g in group_records if isinstance(g, Group)),
        tuple(m for m in membership_records if isinstance(m, GroupMembership)),
        sessions,
    )


def prepare_save_operational_grouping(
    request: SaveOperationalGroupingRequest,
    *,
    workspace_root: str | Path | None = None,
) -> PreparedOperationalGroupingSave:
    """Review one exact Session's live Group assignments without writing."""
    if request.actor.actor_kind != "authorized_adult" or (
        request.actor.owning_system != "concord"
    ):
        raise ConcordWorkflowValidationError(
            "Saved groupings require an authorized Concord teacher actor."
        )
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace is unavailable.")
    metadata = require_core_class(root, request.class_id)
    roster = tuple(
        sorted(
            student.student_id
            for student in load_required_roster(root, request.class_id).students
        )
    )
    group_records, memberships, sessions = _snapshot(root, request)
    if not group_records:
        raise ConcordWorkflowValidationError(
            "No operational Groups exist; create Groups or save a GroupPlan instead."
        )
    source_groups = tuple(
        sorted(
            (g for g in group_records if g.status in _ACTIVE),
            key=lambda g: (g.label.casefold(), g.group_id),
        )
    )
    if not source_groups:
        raise ConcordWorkflowValidationError(
            "No planned or active operational Groups are available to save."
        )
    if any(
        group.parent_group_id is not None or group.supersedes_group_id is not None
        for group in source_groups
    ):
        raise ConcordWorkflowConflictError(
            "Nested or superseded operational Groups require a separate explicit "
            "review; they cannot be flattened into a reusable arrangement."
        )
    for group in source_groups:
        if group.effective_context is not None and not _session_covered(
            group.effective_context,
            activity_id=request.activity_id,
            session_id=request.session_id,
            sessions=sessions,
        ):
            raise ConcordWorkflowConflictError(
                "A current Group is not active in the selected Session. Select a "
                "different Session or reconcile Groups before saving."
            )
    ids = set(roster)
    groups_by_id = {g.group_id: g for g in source_groups}
    assignments: dict[str, list[str]] = {g.group_id: [] for g in source_groups}
    chosen_students: set[str] = set()
    for member in memberships:
        if member.status not in _ACTIVE:
            continue
        if not _session_covered(
            member.effective_context,
            activity_id=request.activity_id,
            session_id=request.session_id,
            sessions=sessions,
        ):
            continue
        if member.group_id not in groups_by_id:
            raise ConcordWorkflowConflictError(
                "An active Session Membership targets an inactive or missing Group; "
                "reconcile it before saving."
            )
        participant = member.participant_reference
        if (
            participant.participant_kind != "core_student"
            or participant.owning_system != "core"
            or participant.participant_id not in ids
        ):
            raise ConcordWorkflowConflictError(
                "An active Session Membership is not an exact current Core student."
            )
        student = participant.participant_id
        if student in chosen_students:
            raise ConcordWorkflowConflictError(
                "A student has multiple active Memberships for this Session. "
                "Resolve the ambiguity before saving."
            )
        chosen_students.add(student)
        assignments[member.group_id].append(student)
    if not chosen_students:
        raise ConcordWorkflowValidationError(
            "No active Core-student Memberships exist for the selected Session."
        )
    groups = tuple(
        SavedArrangementGroup(
            key=f"saved-group-{index:02d}",
            label=group.label,
            description=group.description,
            student_ids=tuple(sorted(assignments[group.group_id])),
        )
        for index, group in enumerate(source_groups, 1)
    )
    unresolved = tuple(sorted(ids - chosen_students))
    candidate = SavedArrangementRevision(
        arrangement_id=request.arrangement_id,
        class_id=request.class_id,
        school_year=metadata.school_year,
        revision=1,
        name=request.name,
        owner_actor_id=request.actor.actor_id,
        created_by_actor_id=request.actor.actor_id,
        created_at=workflow_timestamp(),
        groups=groups,
        roster_student_ids=roster,
        unresolved_student_ids=unresolved,
    )
    # Recheck snapshot after all roster and membership projections.
    if (
        show_activity(
            request.class_id, request.activity_id, workspace_root=root
        ).summary.snapshot_revision
        != request.expected_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Source Activity changed during review; reload before saving."
        )
    digest_data: dict[str, object] = {
        "contract": "concord_operational_grouping_save_review_v1",
        "class_id": request.class_id,
        "school_year": metadata.school_year,
        "activity_id": request.activity_id,
        "session_id": request.session_id,
        "snapshot": request.expected_snapshot_revision,
        "arrangement_id": candidate.arrangement_id,
        "name": candidate.name,
        "actor_id": request.actor.actor_id,
        "groups": [
            {
                "key": g.key,
                "label": g.label,
                "description": g.description,
                "students": list(g.student_ids),
            }
            for g in groups
        ],
        "roster": list(roster),
        "unresolved": list(unresolved),
    }
    review_digest = hashlib.sha256(
        json.dumps(digest_data, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return PreparedOperationalGroupingSave(
        class_id=request.class_id,
        school_year=metadata.school_year,
        source_activity_id=request.activity_id,
        source_session_id=request.session_id,
        source_snapshot_revision=request.expected_snapshot_revision,
        arrangement_id=request.arrangement_id,
        name=request.name,
        owner_actor_id=request.actor.actor_id,
        groups=groups,
        roster_student_ids=roster,
        unresolved_student_ids=unresolved,
        review_digest=review_digest,
    )


def save_operational_grouping(
    request: SaveOperationalGroupingRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> LoadedArrangement:
    """Recheck exact source and store only an immutable class grouping revision."""
    prepared = prepare_save_operational_grouping(request, workspace_root=workspace_root)
    if review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "Operational grouping preview changed; review again before saving."
        )
    if prepared.unresolved_student_ids and request.acknowledge_unresolved is not True:
        raise ConcordWorkflowConflictError(
            "Explicitly acknowledge unresolved students before saving the grouping."
        )
    revision = SavedArrangementRevision(
        arrangement_id=prepared.arrangement_id,
        class_id=prepared.class_id,
        school_year=prepared.school_year,
        revision=1,
        name=prepared.name,
        owner_actor_id=prepared.owner_actor_id,
        created_by_actor_id=prepared.owner_actor_id,
        created_at=workflow_timestamp(clock),
        groups=prepared.groups,
        roster_student_ids=prepared.roster_student_ids,
        unresolved_student_ids=prepared.unresolved_student_ids,
    )
    root = resolve_read_workspace_root(workspace_root)
    assert root is not None
    return create_arrangement(root, revision, actor_id=prepared.owner_actor_id)


__all__ = [
    "PreparedOperationalGroupingSave",
    "SaveOperationalGroupingRequest",
    "prepare_save_operational_grouping",
    "save_operational_grouping",
]
