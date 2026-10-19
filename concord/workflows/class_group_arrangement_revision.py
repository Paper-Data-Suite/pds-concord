"""Reviewed rename, replacement and retirement of reusable class groupings.

Only the class-scoped grouping library is mutated. Native Activity records are
never written here; group placements are copied exclusively from an editable,
exact-roster GroupPlan when explicitly requested.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from concord.class_group_arrangement_storage import (
    ArrangementConflictError,
    LoadedArrangement,
    append_arrangement_revision,
    load_current_arrangement,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
)
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
from concord.workflows.group_plan import show_group_plan
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster

_ACTIONS = frozenset({"rename", "replace_from_plan", "retire"})


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeGroupingRequest:
    class_id: str
    arrangement_id: str
    expected_revision: int
    expected_sha256: str
    actor: WorkflowActor
    action: str
    new_name: str | None = None
    source_activity_id: str | None = None
    source_group_plan_id: str | None = None
    expected_source_snapshot_revision: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedGroupingChange:
    class_id: str
    school_year: str
    arrangement_id: str
    action: str
    previous_revision: int
    previous_sha256: str
    new_revision: int
    name: str
    status: str
    groups: tuple[SavedArrangementGroup, ...]
    roster_student_ids: tuple[str, ...]
    unresolved_student_ids: tuple[str, ...]
    review_digest: str

    @property
    def assigned_count(self) -> int:
        return sum(len(group.student_ids) for group in self.groups)


def _root(workspace_root: str | Path | None) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace is unavailable.")
    return root


def _actor_id(actor: WorkflowActor) -> str:
    if actor.actor_kind != "authorized_adult" or actor.owning_system != "concord":
        raise ConcordWorkflowValidationError(
            "Saved class groupings require an authorized Concord teacher actor."
        )
    return actor.actor_id


def _require_request(request: ChangeGroupingRequest) -> None:
    if request.action not in _ACTIONS:
        raise ConcordWorkflowValidationError(
            "Unsupported saved grouping revision action."
        )
    if type(request.expected_revision) is not int or request.expected_revision < 1:
        raise ConcordWorkflowValidationError("Expected revision must be positive.")
    if (
        not isinstance(request.expected_sha256, str)
        or len(request.expected_sha256) != 64
    ):
        raise ConcordWorkflowValidationError("An exact current SHA-256 is required.")
    has_source = any(
        value is not None
        for value in (
            request.source_activity_id,
            request.source_group_plan_id,
            request.expected_source_snapshot_revision,
        )
    )
    if request.action == "replace_from_plan":
        expected_source = request.expected_source_snapshot_revision
        if (
            not request.source_activity_id
            or not request.source_group_plan_id
            or not isinstance(expected_source, int)
            or isinstance(expected_source, bool)
            or expected_source < 1
        ):
            raise ConcordWorkflowValidationError(
                "Replacement requires an exact Activity, GroupPlan, and snapshot."
            )
    elif has_source:
        raise ConcordWorkflowValidationError(
            "Rename and retirement must not include an Activity source."
        )
    if request.action == "rename" and request.new_name is None:
        raise ConcordWorkflowValidationError("Rename requires a new display name.")
    if request.action == "retire" and request.new_name is not None:
        raise ConcordWorkflowValidationError(
            "Retirement must not silently rename the saved grouping."
        )


def _source_groups(
    request: ChangeGroupingRequest,
    root: Path,
    *,
    class_id: str,
) -> tuple[tuple[SavedArrangementGroup, ...], tuple[str, ...], tuple[str, ...]]:
    assert request.source_activity_id is not None
    assert request.source_group_plan_id is not None
    assert request.expected_source_snapshot_revision is not None
    summary = show_activity(
        class_id, request.source_activity_id, workspace_root=root
    ).summary
    plan = show_group_plan(
        class_id,
        request.source_activity_id,
        request.source_group_plan_id,
        workspace_root=root,
    )
    if (
        summary.snapshot_revision != request.expected_source_snapshot_revision
        or plan.summary.snapshot_revision != request.expected_source_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Source Activity changed; reopen the GroupPlan before revising."
        )
    if plan.plan.status not in {"draft", "previewed"}:
        raise ConcordWorkflowConflictError(
            "Only an editable GroupPlan can replace a saved grouping."
        )
    roster = tuple(
        sorted(
            student.student_id
            for student in load_required_roster(root, class_id).students
        )
    )
    if tuple(plan.plan.roster_student_ids) != roster:
        raise ConcordWorkflowConflictError(
            "Core class roster changed; refresh the source GroupPlan first."
        )
    groups = tuple(
        SavedArrangementGroup(
            key=group.planned_group_key,
            label=group.label,
            description=group.description,
            student_ids=tuple(group.student_ids),
        )
        for group in plan.plan.proposed_groups
    )
    if not groups:
        raise ConcordWorkflowValidationError(
            "Add at least one planned group before replacing a saved grouping."
        )
    return groups, roster, tuple(plan.plan.unresolved_student_ids)


def prepare_grouping_change(
    request: ChangeGroupingRequest,
    *,
    workspace_root: str | Path | None = None,
) -> PreparedGroupingChange:
    """Validate the exact proposed successor and return a read-only review."""
    _require_request(request)
    root = _root(workspace_root)
    actor_id = _actor_id(request.actor)
    metadata = require_core_class(root, request.class_id)
    loaded = load_current_arrangement(
        root,
        class_id=request.class_id,
        school_year=metadata.school_year,
        arrangement_id=request.arrangement_id,
        actor_id=actor_id,
    )
    current = loaded.revision
    if current.status != "active":
        raise ArrangementConflictError("Retired groupings cannot be changed.")
    if (
        current.revision != request.expected_revision
        or loaded.sha256 != request.expected_sha256
    ):
        raise ArrangementConflictError(
            "Saved grouping changed; reload and review its current revision."
        )
    groups = current.groups
    roster = current.roster_student_ids
    unresolved = current.unresolved_student_ids
    name = request.new_name if request.new_name is not None else current.name
    status = "retired" if request.action == "retire" else "active"
    if request.action == "replace_from_plan":
        groups, roster, unresolved = _source_groups(
            request, root, class_id=request.class_id
        )
    if (
        name == current.name
        and status == current.status
        and groups == current.groups
        and roster == current.roster_student_ids
        and unresolved == current.unresolved_student_ids
    ):
        raise ConcordWorkflowConflictError(
            "The reviewed changes are identical to the current saved grouping."
        )
    # Construct the native immutable model before offering any write.
    successor = SavedArrangementRevision(
        arrangement_id=current.arrangement_id,
        class_id=current.class_id,
        school_year=current.school_year,
        revision=current.revision + 1,
        name=name,
        owner_actor_id=current.owner_actor_id,
        created_by_actor_id=actor_id,
        created_at=workflow_timestamp(),
        groups=groups,
        roster_student_ids=roster,
        unresolved_student_ids=unresolved,
        status=status,
        predecessor_sha256=loaded.sha256,
    )
    digest_data = {
        "contract": "concord_grouping_change_review_v1",
        "class_id": successor.class_id,
        "school_year": successor.school_year,
        "arrangement_id": successor.arrangement_id,
        "actor_id": actor_id,
        "action": request.action,
        "previous_revision": current.revision,
        "previous_sha256": loaded.sha256,
        "new_revision": successor.revision,
        "new_name": successor.name,
        "status": successor.status,
        "source_activity_id": request.source_activity_id,
        "source_group_plan_id": request.source_group_plan_id,
        "source_snapshot": request.expected_source_snapshot_revision,
        "groups": [
            {
                "key": item.key,
                "label": item.label,
                "description": item.description,
                "student_ids": list(item.student_ids),
            }
            for item in successor.groups
        ],
        "roster_student_ids": list(successor.roster_student_ids),
        "unresolved_student_ids": list(successor.unresolved_student_ids),
    }
    raw = json.dumps(
        digest_data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return PreparedGroupingChange(
        class_id=successor.class_id,
        school_year=successor.school_year,
        arrangement_id=successor.arrangement_id,
        action=request.action,
        previous_revision=current.revision,
        previous_sha256=loaded.sha256,
        new_revision=successor.revision,
        name=successor.name,
        status=successor.status,
        groups=successor.groups,
        roster_student_ids=successor.roster_student_ids,
        unresolved_student_ids=successor.unresolved_student_ids,
        review_digest=hashlib.sha256(raw).hexdigest(),
    )


def change_grouping(
    request: ChangeGroupingRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> LoadedArrangement:
    """Re-review and append exactly one immutable successor under CAS."""
    prepared = prepare_grouping_change(request, workspace_root=workspace_root)
    if review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "Saved grouping review changed; inspect it again before confirming."
        )
    successor = SavedArrangementRevision(
        arrangement_id=prepared.arrangement_id,
        class_id=prepared.class_id,
        school_year=prepared.school_year,
        revision=prepared.new_revision,
        name=prepared.name,
        owner_actor_id=_actor_id(request.actor),
        created_by_actor_id=_actor_id(request.actor),
        created_at=workflow_timestamp(clock),
        groups=prepared.groups,
        roster_student_ids=prepared.roster_student_ids,
        unresolved_student_ids=prepared.unresolved_student_ids,
        status=prepared.status,
        predecessor_sha256=prepared.previous_sha256,
    )
    return append_arrangement_revision(
        _root(workspace_root),
        successor,
        actor_id=request.actor.actor_id,
        expected_revision=prepared.previous_revision,
        expected_sha256=prepared.previous_sha256,
    )


__all__ = [
    "ChangeGroupingRequest",
    "PreparedGroupingChange",
    "change_grouping",
    "prepare_grouping_change",
]
