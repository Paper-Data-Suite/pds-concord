"""Reviewed class-grouping saves and fresh Activity GroupPlan reuse (#136).

The saved library is class-scoped, while GroupPlan creation remains owned by
Concord's existing canonical Activity writer. This service does not create
Groups, Memberships, Roles, Responsibilities, or Scores.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from pds_core.identifiers import validate_identifier
from pds_core.standards import StandardsLibrary

from concord.class_group_arrangement_storage import (
    LoadedArrangement,
    create_arrangement,
    load_current_arrangement,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
    compare_roster,
)
from concord.models import PlannedGroup
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
from concord.workflows.group_plan import (
    CreateGroupPlanRequest,
    GroupPlanMutationResult,
    create_group_plan,
    list_group_plans,
    show_group_plan,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster


@dataclass(frozen=True, slots=True, kw_only=True)
class SaveGroupingRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    arrangement_id: str
    name: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedGroupingSave:
    class_id: str
    school_year: str
    source_activity_id: str
    source_plan_id: str
    source_record_revision: int
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


@dataclass(frozen=True, slots=True, kw_only=True)
class StudentPlacementDecision:
    """Explicit target-roster decision; None means deliberately unresolved."""

    student_id: str
    group_key: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReuseGroupingRequest:
    class_id: str
    activity_id: str
    arrangement_id: str
    new_group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    placement_decisions: tuple[StudentPlacementDecision, ...] = ()
    acknowledged_departed_student_ids: tuple[str, ...] = ()
    acknowledge_existing_plans: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedGroupingReuse:
    class_id: str
    school_year: str
    target_activity_id: str
    target_snapshot_revision: int
    target_roster_student_ids: tuple[str, ...]
    arrangement_id: str
    arrangement_revision: int
    arrangement_sha256: str
    new_group_plan_id: str
    groups: tuple[PlannedGroup, ...]
    unresolved_student_ids: tuple[str, ...]
    departed_student_ids: tuple[str, ...]
    added_student_ids: tuple[str, ...]
    review_digest: str

    @property
    def assigned_count(self) -> int:
        return sum(len(group.student_ids) for group in self.groups)


def _root(workspace_root: str | Path | None) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace is unavailable.")
    return root


def _digest(data: dict[str, object]) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _group_items(groups: tuple[SavedArrangementGroup, ...]) -> list[dict[str, object]]:
    return [
        {
            "key": item.key,
            "label": item.label,
            "description": item.description,
            "student_ids": list(item.student_ids),
        }
        for item in groups
    ]


def _roster(root: Path, class_id: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            student.student_id
            for student in load_required_roster(root, class_id).students
        )
    )


def _actor_id(actor: WorkflowActor) -> str:
    if actor.actor_kind != "authorized_adult" or actor.owning_system != "concord":
        raise ConcordWorkflowValidationError(
            "Saved class groupings require an authorized Concord teacher actor."
        )
    return actor.actor_id


def prepare_save_grouping(
    request: SaveGroupingRequest,
    *,
    workspace_root: str | Path | None = None,
) -> PreparedGroupingSave:
    """Inspect one current editable proposal without mutating either storage domain."""
    root = _root(workspace_root)
    actor_id = _actor_id(request.actor)
    metadata = require_core_class(root, request.class_id)
    summary = show_activity(
        request.class_id, request.activity_id, workspace_root=root
    ).summary
    detail = show_group_plan(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        workspace_root=root,
    )
    if (
        summary.snapshot_revision != request.expected_snapshot_revision
        or detail.summary.snapshot_revision != request.expected_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Activity changed; reopen the GroupPlan before saving its grouping."
        )
    if detail.plan.status not in {"draft", "previewed"}:
        raise ConcordWorkflowConflictError(
            "Only an editable draft or previewed GroupPlan may be saved here."
        )
    current_roster = _roster(root, request.class_id)
    if tuple(detail.plan.roster_student_ids) != current_roster:
        raise ConcordWorkflowConflictError(
            "Core class roster changed; review and refresh the GroupPlan first."
        )
    groups = tuple(
        SavedArrangementGroup(
            key=g.planned_group_key,
            label=g.label,
            description=g.description,
            student_ids=tuple(g.student_ids),
        )
        for g in detail.plan.proposed_groups
    )
    if not groups:
        raise ConcordWorkflowValidationError(
            "Add at least one planned group before saving a reusable grouping."
        )
    unresolved = tuple(detail.plan.unresolved_student_ids)
    # Validate exact coverage, duplicate prevention, and no Activity IDs using
    # the Slice 3 immutable record contract before creating any directory.
    captured = SavedArrangementRevision(
        arrangement_id=request.arrangement_id,
        class_id=request.class_id,
        school_year=metadata.school_year,
        revision=1,
        name=request.name,
        owner_actor_id=actor_id,
        created_by_actor_id=actor_id,
        created_at=workflow_timestamp(),
        groups=groups,
        roster_student_ids=current_roster,
        unresolved_student_ids=unresolved,
    )
    digest = _digest(
        {
            "kind": "save_grouping_review_v1",
            "class_id": request.class_id,
            "school_year": metadata.school_year,
            "activity_id": request.activity_id,
            "plan_id": request.group_plan_id,
            "plan_record_revision": detail.record_revision,
            "activity_snapshot": summary.snapshot_revision,
            "arrangement_id": captured.arrangement_id,
            "name": captured.name,
            "actor_id": actor_id,
            "groups": _group_items(groups),
            "roster_student_ids": list(current_roster),
            "unresolved_student_ids": list(unresolved),
        }
    )
    return PreparedGroupingSave(
        class_id=request.class_id,
        school_year=metadata.school_year,
        source_activity_id=request.activity_id,
        source_plan_id=request.group_plan_id,
        source_record_revision=detail.record_revision,
        source_snapshot_revision=summary.snapshot_revision,
        arrangement_id=request.arrangement_id,
        name=request.name,
        owner_actor_id=actor_id,
        groups=groups,
        roster_student_ids=current_roster,
        unresolved_student_ids=unresolved,
        review_digest=digest,
    )


def save_grouping(
    request: SaveGroupingRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> LoadedArrangement:
    """Recheck the reviewed source and save a new teacher-owned library identity."""
    prepared = prepare_save_grouping(request, workspace_root=workspace_root)
    if review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "Grouping preview changed; review the source plan again before saving."
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
    return create_arrangement(
        _root(workspace_root), revision, actor_id=prepared.owner_actor_id
    )


def _checked_decisions(
    request: ReuseGroupingRequest,
    *,
    required_student_ids: set[str],
    group_keys: set[str],
) -> dict[str, str | None]:
    if not isinstance(request.placement_decisions, tuple):
        raise ConcordWorkflowValidationError("Placement decisions must be a tuple.")
    result: dict[str, str | None] = {}
    for item in request.placement_decisions:
        if not isinstance(item, StudentPlacementDecision):
            raise ConcordWorkflowValidationError("Invalid student placement decision.")
        try:
            student_id = validate_identifier(item.student_id, "student_id")
            if item.group_key is not None:
                validate_identifier(item.group_key, "group_key")
        except (TypeError, ValueError) as exc:
            raise ConcordWorkflowValidationError(
                "Invalid placement identifier."
            ) from exc
        if student_id in result:
            raise ConcordWorkflowValidationError(
                "Each student must have exactly one placement decision."
            )
        if item.group_key is not None and item.group_key not in group_keys:
            raise ConcordWorkflowValidationError(
                "Placement references a group that is not in the saved grouping."
            )
        result[student_id] = item.group_key
    if set(result) != required_student_ids:
        raise ConcordWorkflowConflictError(
            "Explicit placement or unresolved decisions are required for every "
            "new or previously unresolved student. Review the roster differences."
        )
    return result


def prepare_reuse_grouping(
    request: ReuseGroupingRequest,
    *,
    workspace_root: str | Path | None = None,
) -> PreparedGroupingReuse:
    """Review target roster/conflicts before creating a fresh Activity-owned plan."""
    root = _root(workspace_root)
    actor_id = _actor_id(request.actor)
    metadata = require_core_class(root, request.class_id)
    saved = load_current_arrangement(
        root,
        class_id=request.class_id,
        school_year=metadata.school_year,
        arrangement_id=request.arrangement_id,
        actor_id=actor_id,
    )
    if saved.revision.status != "active":
        raise ConcordWorkflowConflictError(
            "This saved grouping is retired; select an active grouping."
        )
    target = show_activity(
        request.class_id, request.activity_id, workspace_root=root
    ).summary
    if target.snapshot_revision != request.expected_snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Target Activity changed; reload its grouping setup."
        )
    if target.group_count:
        raise ConcordWorkflowConflictError(
            "Target Activity already has canonical Groups; review those before reuse."
        )
    existing_plans = list_group_plans(
        request.class_id, request.activity_id, workspace_root=root
    )
    if any(item.group_plan_id == request.new_group_plan_id for item in existing_plans):
        raise ConcordWorkflowConflictError(
            "That GroupPlan ID is already used in this Activity."
        )
    if existing_plans and not request.acknowledge_existing_plans:
        raise ConcordWorkflowConflictError(
            "Target Activity has existing GroupPlans. Review them and explicitly "
            "acknowledge creating an additional separate plan."
        )
    roster = _roster(root, request.class_id)
    differences = compare_roster(
        saved.revision,
        target_class_id=request.class_id,
        target_school_year=metadata.school_year,
        target_student_ids=roster,
    )
    acknowledged = request.acknowledged_departed_student_ids
    if (
        not isinstance(acknowledged, tuple)
        or len(acknowledged) != len(set(acknowledged))
        or set(acknowledged) != set(differences.departed_ids)
    ):
        raise ConcordWorkflowConflictError(
            "Review and explicitly acknowledge every departed roster student."
        )
    required = set(differences.newly_enrolled_ids) | set(differences.unresolved_ids)
    decisions = _checked_decisions(
        request,
        required_student_ids=required,
        group_keys={group.key for group in saved.revision.groups},
    )
    current = set(roster)
    groups = tuple(
        PlannedGroup(
            planned_group_key=item.key,
            label=item.label,
            description=item.description,
            student_ids=tuple(
                sid
                for sid in roster
                if (sid in item.student_ids and sid in current)
                or decisions.get(sid, "<unreviewed>") == item.key
            ),
        )
        for item in saved.revision.groups
    )
    assigned = [sid for item in groups for sid in item.student_ids]
    if len(assigned) != len(set(assigned)):
        raise ConcordWorkflowValidationError(
            "Reconciled grouping contains overlapping memberships."
        )
    unresolved = tuple(sorted(current - set(assigned)))
    if any(sid not in decisions or decisions[sid] is not None for sid in unresolved):
        raise ConcordWorkflowConflictError(
            "Unresolved students require explicit review decisions."
        )
    digest = _digest(
        {
            "kind": "reuse_grouping_review_v1",
            "class_id": request.class_id,
            "school_year": metadata.school_year,
            "activity_id": request.activity_id,
            "target_snapshot": target.snapshot_revision,
            "target_roster": list(roster),
            "actor_id": actor_id,
            "arrangement_id": saved.revision.arrangement_id,
            "arrangement_revision": saved.revision.revision,
            "arrangement_sha256": saved.sha256,
            "new_plan_id": request.new_group_plan_id,
            "groups": [
                {
                    "key": g.planned_group_key,
                    "label": g.label,
                    "description": g.description,
                    "student_ids": list(g.student_ids),
                }
                for g in groups
            ],
            "unresolved_ids": list(unresolved),
            "departed_ids": list(differences.departed_ids),
            "added_ids": list(differences.newly_enrolled_ids),
            "ack_existing_plans": request.acknowledge_existing_plans,
        }
    )
    return PreparedGroupingReuse(
        class_id=request.class_id,
        school_year=metadata.school_year,
        target_activity_id=request.activity_id,
        target_snapshot_revision=target.snapshot_revision,
        target_roster_student_ids=roster,
        arrangement_id=saved.revision.arrangement_id,
        arrangement_revision=saved.revision.revision,
        arrangement_sha256=saved.sha256,
        new_group_plan_id=request.new_group_plan_id,
        groups=groups,
        unresolved_student_ids=unresolved,
        departed_student_ids=differences.departed_ids,
        added_student_ids=differences.newly_enrolled_ids,
        review_digest=digest,
    )


def reuse_grouping(
    request: ReuseGroupingRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanMutationResult:
    """Revalidate review and delegate one guarded GroupPlan write."""
    preview = prepare_reuse_grouping(request, workspace_root=workspace_root)
    if review_digest != preview.review_digest:
        raise ConcordWorkflowConflictError(
            "Grouping or target Activity changed; review the grouping again."
        )
    return create_group_plan(
        CreateGroupPlanRequest(
            class_id=preview.class_id,
            activity_id=preview.target_activity_id,
            group_plan_id=preview.new_group_plan_id,
            strategy="manual",
            proposed_groups=preview.groups,
            expected_roster_student_ids=preview.target_roster_student_ids,
            expected_snapshot_revision=preview.target_snapshot_revision,
            actor=request.actor,
        ),
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )


__all__ = [
    "PreparedGroupingReuse",
    "PreparedGroupingSave",
    "ReuseGroupingRequest",
    "SaveGroupingRequest",
    "StudentPlacementDecision",
    "prepare_reuse_grouping",
    "prepare_save_grouping",
    "reuse_grouping",
    "save_grouping",
]
