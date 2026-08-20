"""Deterministic random GroupPlan creation over the native planning boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.group_plan_random import (
    RandomGroupPlanningError,
    generate_random_group_plan_proposal,
)
from concord.workflows.context import (
    Clock,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan import (
    CreateGroupPlanRequest,
    GroupPlanMutationResult,
    create_group_plan,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRandomGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    seed: str
    target_group_size: int | None = None
    target_group_count: int | None = None


@dataclass(frozen=True, slots=True)
class RandomGroupPlanCreationResult:
    mutation: GroupPlanMutationResult
    group_count: int
    assigned_student_count: int
    group_sizes: tuple[int, ...]


def create_random_group_plan(
    request: CreateRandomGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> RandomGroupPlanCreationResult:
    """Create one complete deterministic random draft through #50 services."""

    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    require_core_class(root, request.class_id)
    roster = load_required_roster(root, request.class_id)
    roster_student_ids = tuple(
        sorted(student.student_id for student in roster.students)
    )
    try:
        proposal = generate_random_group_plan_proposal(
            roster_student_ids,
            seed=request.seed,
            target_group_size=request.target_group_size,
            target_group_count=request.target_group_count,
        )
    except RandomGroupPlanningError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    mutation = create_group_plan(
        CreateGroupPlanRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_plan_id=request.group_plan_id,
            strategy="random",
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            proposed_groups=proposal.proposed_groups,
            target_group_size=request.target_group_size,
            target_group_count=request.target_group_count,
            seed=request.seed,
            expected_roster_student_ids=proposal.roster_student_ids,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )
    return RandomGroupPlanCreationResult(
        mutation=mutation,
        group_count=proposal.group_count,
        assigned_student_count=proposal.assigned_student_count,
        group_sizes=proposal.group_sizes,
    )
