"""Signal-backed deterministic GroupPlan creation over the native planning boundary."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.group_plan_signal import (
    SignalGroupPlanningError,
    generate_mixed_signal_group_plan_proposal,
    generate_similar_signal_group_plan_proposal,
)
from concord.workflows.context import (
    Clock,
    require_core_class,
    resolve_read_workspace_root,
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
)
from concord.workflows.grouping_signal import (
    GroupingSignalDimensionSelection,
    select_grouping_signal_dimension,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster

_SIGNAL_STRATEGIES = frozenset({"similar_signal", "mixed_signal"})


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateSignalGroupPlanRequest:
    """Create one deterministic signal-backed draft from an exact Core dimension."""

    class_id: str
    activity_id: str
    group_plan_id: str
    strategy: str
    signal_set_id: str
    dimension_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    target_group_size: int | None = None
    target_group_count: int | None = None
    expected_roster_student_ids: tuple[str, ...] | None = None
    expected_signal_set_digest: str | None = None


@dataclass(frozen=True, slots=True)
class SignalGroupPlanCreationResult:
    """Privacy-bounded result for one persisted signal-backed draft."""

    mutation: GroupPlanMutationResult
    strategy: str
    group_count: int
    assigned_student_count: int
    unresolved_student_count: int
    group_sizes: tuple[int, ...]
    signal_set_id: str
    signal_set_digest: str
    dimension_id: str


def _roster_student_ids(root: Path, class_id: str) -> tuple[str, ...]:
    roster = load_required_roster(root, class_id)
    return tuple(sorted(student.student_id for student in roster.students))


def _selected_signal_bands(
    selection: GroupingSignalDimensionSelection,
) -> dict[str, int]:
    return {
        entry.student_id: entry.band
        for entry in selection.inspection.stored.signal.student_bands
        if entry.dimension_id == selection.dimension_id
    }


def create_signal_group_plan(
    request: CreateSignalGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> SignalGroupPlanCreationResult:
    """Create one signal-backed draft without creating canonical Groups."""

    if request.strategy not in _SIGNAL_STRATEGIES:
        raise ConcordWorkflowValidationError(
            "strategy must be 'similar_signal' or 'mixed_signal'."
        )

    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    require_core_class(root, request.class_id)

    roster_student_ids = _roster_student_ids(root, request.class_id)
    if (
        request.expected_roster_student_ids is not None
        and roster_student_ids != request.expected_roster_student_ids
    ):
        raise ConcordWorkflowConflictError(
            "Core roster changed since the signal GroupPlan preview; "
            "reload and retry."
        )

    selection = select_grouping_signal_dimension(
        request.class_id,
        request.signal_set_id,
        request.dimension_id,
        workspace_root=root,
    )
    if (
        request.expected_signal_set_digest is not None
        and selection.digest != request.expected_signal_set_digest
    ):
        raise ConcordWorkflowConflictError(
            "Grouping signal changed since the GroupPlan preview; reload and retry."
        )

    # The #53 diagnostics above were calculated against a concrete Core roster.
    # Do not combine them with a different roster if the shared class changed
    # while the exact signal/dimension was being selected.
    if _roster_student_ids(root, request.class_id) != roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed while selecting the grouping signal; "
            "reload and retry."
        )

    signal_bands = _selected_signal_bands(selection)
    try:
        if request.strategy == "similar_signal":
            proposal = generate_similar_signal_group_plan_proposal(
                roster_student_ids,
                signal_bands,
                target_group_size=request.target_group_size,
                target_group_count=request.target_group_count,
            )
        else:
            proposal = generate_mixed_signal_group_plan_proposal(
                roster_student_ids,
                signal_bands,
                target_group_size=request.target_group_size,
                target_group_count=request.target_group_count,
            )
    except SignalGroupPlanningError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    mutation = create_group_plan(
        CreateGroupPlanRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_plan_id=request.group_plan_id,
            strategy=request.strategy,
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            proposed_groups=proposal.proposed_groups,
            target_group_size=request.target_group_size,
            target_group_count=request.target_group_count,
            source_signal_set_id=selection.signal_set_id,
            source_signal_set_digest=selection.digest,
            source_signal_dimension_id=selection.dimension_id,
            expected_roster_student_ids=proposal.roster_student_ids,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )
    return SignalGroupPlanCreationResult(
        mutation=mutation,
        strategy=request.strategy,
        group_count=proposal.group_count,
        assigned_student_count=proposal.assigned_student_count,
        unresolved_student_count=proposal.unresolved_student_count,
        group_sizes=proposal.group_sizes,
        signal_set_id=selection.signal_set_id,
        signal_set_digest=selection.digest,
        dimension_id=selection.dimension_id,
    )
