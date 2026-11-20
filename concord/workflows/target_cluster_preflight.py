"""Source-independent Core-roster review before target Activity Cluster planning.

This projects only the *target* class roster and Activity. Six proposed Clusters
are shape-only; a teacher must place target students, preview, approve and
apply the GroupPlan using Concord's existing owner workflow. No source
GroupPlan, Membership, saved class arrangement or academic evidence is read.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.models import PlannedGroup
from concord.workflows.activity import show_activity
from concord.workflows.context import require_core_class, resolve_read_workspace_root
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
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster

CLUSTER_COUNT = 6


@dataclass(frozen=True, slots=True)
class TargetClusterPreflight:
    """Verified target-only snapshot; student IDs are internal review guards."""

    class_id: str
    activity_id: str
    title: str
    snapshot_revision: int
    roster_student_ids: tuple[str, ...]
    current_group_count: int
    existing_plan_count: int
    six_cluster_size_reference: tuple[int, ...]

    @property
    def roster_count(self) -> int:
        return len(self.roster_student_ids)

    @property
    def can_create_new_shape(self) -> bool:
        return self.current_group_count == 0 and self.existing_plan_count == 0


def six_cluster_size_reference(roster_count: int) -> tuple[int, ...]:
    """Even-size *reference*, never student placement or a required capacity."""
    if not isinstance(roster_count, int) or isinstance(roster_count, bool):
        raise TypeError("roster_count must be an integer")
    if roster_count < 0:
        raise ValueError("roster_count cannot be negative")
    base, remainder = divmod(roster_count, CLUSTER_COUNT)
    return tuple(base + (i < remainder) for i in range(CLUSTER_COUNT))


def six_empty_planned_clusters() -> tuple[PlannedGroup, ...]:
    """Six identity-free labels; do not create or select memberships."""
    return tuple(
        PlannedGroup(planned_group_key=f"cluster-{i}", label=f"Cluster {i}")
        for i in range(1, CLUSTER_COUNT + 1)
    )


def inspect_target_cluster_preflight(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> TargetClusterPreflight:
    """Read exactly one target Core roster and one target Concord Activity."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace is unavailable.")
    require_core_class(root, class_id)
    current = show_activity(class_id, activity_id, workspace_root=root).summary
    if current.class_id != class_id or current.activity_id != activity_id:
        raise ConcordWorkflowValidationError("Target Activity identity changed.")
    roster = load_required_roster(root, class_id)
    student_ids = tuple(sorted(student.student_id for student in roster.students))
    if len(student_ids) != len(set(student_ids)):
        raise ConcordWorkflowValidationError("Core target roster has duplicate IDs.")
    if not student_ids:
        raise ConcordWorkflowValidationError("Core target roster has no students.")
    plans = list_group_plans(class_id, activity_id, workspace_root=root)
    if any(
        plan.class_id != class_id or plan.activity_id != activity_id for plan in plans
    ):
        raise ConcordWorkflowValidationError(
            "Target GroupPlan ownership is inconsistent."
        )
    return TargetClusterPreflight(
        class_id=class_id,
        activity_id=activity_id,
        title=current.title,
        snapshot_revision=current.snapshot_revision,
        roster_student_ids=student_ids,
        current_group_count=current.group_count,
        existing_plan_count=len(plans),
        six_cluster_size_reference=six_cluster_size_reference(len(student_ids)),
    )


def create_target_six_cluster_draft(
    reviewed: TargetClusterPreflight,
    *,
    group_plan_id: str,
    actor: WorkflowActor,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> GroupPlanMutationResult:
    """One existing guarded GroupPlan write, only if review is still current.

    The service independently enforces the pinned snapshot and *target* roster
    at commit. A concurrent plan creation also changes the snapshot and blocks.
    """
    current = inspect_target_cluster_preflight(
        reviewed.class_id, reviewed.activity_id, workspace_root=workspace_root
    )
    if (
        current.snapshot_revision != reviewed.snapshot_revision
        or current.roster_student_ids != reviewed.roster_student_ids
    ):
        raise ConcordWorkflowConflictError(
            "Target Activity or Core roster changed; review Clusters again."
        )
    if not current.can_create_new_shape:
        raise ConcordWorkflowConflictError(
            "This target already has Groups or GroupPlans; inspect them instead."
        )
    return create_group_plan(
        CreateGroupPlanRequest(
            class_id=reviewed.class_id,
            activity_id=reviewed.activity_id,
            group_plan_id=group_plan_id,
            strategy="manual",
            expected_snapshot_revision=reviewed.snapshot_revision,
            expected_roster_student_ids=reviewed.roster_student_ids,
            actor=actor,
            proposed_groups=six_empty_planned_clusters(),
            target_group_count=CLUSTER_COUNT,
        ),
        workspace_root=workspace_root,
        standards_library=standards_library,
    )


__all__ = [
    "CLUSTER_COUNT",
    "TargetClusterPreflight",
    "create_target_six_cluster_draft",
    "inspect_target_cluster_preflight",
    "six_cluster_size_reference",
    "six_empty_planned_clusters",
]
