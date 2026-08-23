"""Explicit #55 dispositions for students missing a selected grouping signal."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.group_plan_missing_signal import (
    MissingSignalRandomizationError,
    distribute_missing_signal_students,
)
from concord.models import GroupPlan, PlannedGroup
from concord.storage import commit_record_batch
from concord.workflows._collaboration import work_ref
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
from concord.workflows.group_plan import (
    GroupPlanDetail,
    GroupPlanMutationResult,
    show_group_plan,
)
from concord.workflows.grouping_signal import (
    select_grouping_signal_dimension,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult
from concord.workflows.participants import load_required_roster

_SIGNAL_STRATEGIES = frozenset({"similar_signal", "mixed_signal"})
_DISPOSITIONS = frozenset({"manual", "random", "leave_unassigned"})


@dataclass(frozen=True, slots=True)
class MissingSignalPlanInspection:
    """Exact teacher-restricted #55 planning context without student-band values."""

    detail: GroupPlanDetail
    signal_set_id: str
    signal_set_digest: str
    dimension_id: str
    missing_student_ids: tuple[str, ...]
    missing_assigned_student_ids: tuple[str, ...]
    missing_unresolved_student_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class SetMissingSignalDispositionRequest:
    """Record one explicit plan-level decision for the current missing population."""

    class_id: str
    activity_id: str
    group_plan_id: str
    disposition: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    random_seed: str | None = None


@dataclass(frozen=True, slots=True)
class MissingSignalDispositionResult:
    """Privacy-bounded persisted #55 mutation result."""

    mutation: GroupPlanMutationResult
    disposition: str
    missing_student_count: int
    assigned_student_count: int
    unresolved_student_count: int
    group_sizes: tuple[int, ...]
    random_seed: str | None


def _required_root(workspace_root: str | Path | None) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    return root


def _roster_student_ids(root: Path, class_id: str) -> tuple[str, ...]:
    roster = load_required_roster(root, class_id)
    return tuple(sorted(student.student_id for student in roster.students))


def _require_signal_binding(plan: GroupPlan) -> tuple[str, str, str]:
    if plan.strategy not in _SIGNAL_STRATEGIES:
        raise ConcordWorkflowValidationError(
            "Missing-signal disposition is available only for "
            "similar_signal or mixed_signal GroupPlans."
        )
    signal_set_id = plan.source_signal_set_id
    signal_set_digest = plan.source_signal_set_digest
    dimension_id = plan.source_signal_dimension_id
    if (
        signal_set_id is None
        or signal_set_digest is None
        or dimension_id is None
    ):
        raise ConcordWorkflowValidationError(
            "Signal-backed GroupPlan is missing its exact signal binding."
        )
    return signal_set_id, signal_set_digest, dimension_id


def _missing_student_ids(
    *,
    dimension_id: str,
    findings: tuple[object, ...],
) -> tuple[str, ...]:
    missing: list[str] = []
    for finding in findings:
        code = getattr(finding, "code", None)
        finding_dimension = getattr(finding, "dimension_id", None)
        student_id = getattr(finding, "student_id", None)
        if (
            code == "missing_student_signal"
            and finding_dimension == dimension_id
            and isinstance(student_id, str)
        ):
            missing.append(student_id)
    return tuple(sorted(missing))


def _inspect(
    class_id: str,
    activity_id: str,
    group_plan_id: str,
    *,
    expected_snapshot_revision: int | None,
    workspace_root: str | Path | None,
) -> tuple[Path, MissingSignalPlanInspection]:
    root = _required_root(workspace_root)
    require_core_class(root, class_id)
    detail = show_group_plan(
        class_id,
        activity_id,
        group_plan_id,
        workspace_root=root,
    )
    if (
        expected_snapshot_revision is not None
        and detail.summary.snapshot_revision != expected_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Activity changed since the caller's expected snapshot."
        )

    plan = detail.plan
    signal_set_id, signal_set_digest, dimension_id = _require_signal_binding(plan)

    roster_before = _roster_student_ids(root, class_id)
    if roster_before != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed since this GroupPlan proposal revision; "
            "refresh the GroupPlan roster explicitly before deciding how to "
            "handle missing-signal students."
        )

    selection = select_grouping_signal_dimension(
        class_id,
        signal_set_id,
        dimension_id,
        workspace_root=root,
    )
    if selection.digest != signal_set_digest:
        raise ConcordWorkflowConflictError(
            "Grouping signal canonical digest does not match the exact signal "
            "binding stored on this GroupPlan."
        )

    roster_after = _roster_student_ids(root, class_id)
    if roster_after != roster_before:
        raise ConcordWorkflowConflictError(
            "Core roster changed while checking missing-signal students; "
            "reload and retry."
        )

    missing = _missing_student_ids(
        dimension_id=dimension_id,
        findings=selection.inspection.diagnostics.findings,
    )
    if (
        len(missing)
        != selection.dimension_diagnostics.missing_student_count
    ):
        raise ConcordWorkflowValidationError(
            "Core grouping-signal diagnostics returned inconsistent "
            "missing-student detail."
        )

    unresolved = set(plan.unresolved_student_ids)
    missing_set = set(missing)
    missing_unresolved = tuple(sorted(missing_set & unresolved))
    missing_assigned = tuple(sorted(missing_set - unresolved))

    return root, MissingSignalPlanInspection(
        detail=detail,
        signal_set_id=signal_set_id,
        signal_set_digest=signal_set_digest,
        dimension_id=dimension_id,
        missing_student_ids=missing,
        missing_assigned_student_ids=missing_assigned,
        missing_unresolved_student_ids=missing_unresolved,
    )


def inspect_group_plan_missing_signal(
    class_id: str,
    activity_id: str,
    group_plan_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> MissingSignalPlanInspection:
    """Revalidate the exact bound signal and return current missing-student context."""

    _, inspection = _inspect(
        class_id,
        activity_id,
        group_plan_id,
        expected_snapshot_revision=None,
        workspace_root=workspace_root,
    )
    return inspection


def _validate_choice(
    request: SetMissingSignalDispositionRequest,
    inspection: MissingSignalPlanInspection,
) -> None:
    if request.disposition not in _DISPOSITIONS:
        raise ConcordWorkflowValidationError(
            "disposition must be one of: leave_unassigned, manual, random."
        )
    if inspection.detail.plan.status not in {"draft", "previewed"}:
        raise ConcordWorkflowConflictError(
            "Only draft or previewed GroupPlans may record a missing-signal "
            "disposition."
        )
    if not inspection.missing_student_ids:
        raise ConcordWorkflowValidationError(
            "The selected signal dimension has no missing roster students; "
            "no missing-signal disposition is required."
        )

    if request.disposition == "random":
        if request.random_seed is None:
            raise ConcordWorkflowValidationError(
                "random missing-signal disposition requires an explicit seed."
            )
    elif request.random_seed is not None:
        raise ConcordWorkflowValidationError(
            "random_seed is allowed only for random missing-signal disposition."
        )

    if request.disposition == "manual":
        if inspection.missing_unresolved_student_ids:
            raise ConcordWorkflowValidationError(
                "Manual missing-signal disposition requires every exact "
                "missing-signal student to be placed first."
            )
    elif request.disposition == "leave_unassigned":
        if inspection.missing_assigned_student_ids:
            raise ConcordWorkflowValidationError(
                "leave_unassigned requires every exact missing-signal student "
                "to remain unresolved."
            )
    elif inspection.missing_assigned_student_ids:
        raise ConcordWorkflowValidationError(
            "Random missing-signal distribution requires every exact "
            "missing-signal student to be unresolved first."
        )


def _candidate_groups_and_unresolved(
    request: SetMissingSignalDispositionRequest,
    inspection: MissingSignalPlanInspection,
) -> tuple[tuple[PlannedGroup, ...], tuple[str, ...]]:
    plan = inspection.detail.plan
    if request.disposition != "random":
        return plan.proposed_groups, plan.unresolved_student_ids

    assert request.random_seed is not None
    try:
        randomized = distribute_missing_signal_students(
            plan.proposed_groups,
            inspection.missing_student_ids,
            seed=request.random_seed,
        )
    except MissingSignalRandomizationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    missing = set(inspection.missing_student_ids)
    unresolved = tuple(
        sorted(
            student_id
            for student_id in plan.unresolved_student_ids
            if student_id not in missing
        )
    )
    return randomized.proposed_groups, unresolved


def set_missing_signal_disposition(
    request: SetMissingSignalDispositionRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> MissingSignalDispositionResult:
    """Persist one explicit #55 decision without creating canonical Groups."""

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root, inspection = _inspect(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        workspace_root=bootstrap.root,
    )
    _validate_choice(request, inspection)

    plan = inspection.detail.plan
    groups, unresolved = _candidate_groups_and_unresolved(
        request,
        inspection,
    )
    decision_provenance = provenance(request.actor, clock=clock)
    candidate = replace(
        plan,
        status="draft",
        proposed_groups=groups,
        unresolved_student_ids=unresolved,
        missing_signal_disposition=request.disposition,
        missing_signal_random_seed=request.random_seed,
        missing_signal_disposition_provenance=decision_provenance,
        updated_provenance=decision_provenance,
        previewed_provenance=None,
        approved_provenance=None,
        cancelled_provenance=None,
        applied_provenance=None,
    )

    if _roster_student_ids(root, request.class_id) != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed while preparing the missing-signal decision; "
            "reload and retry."
        )

    storage_result = commit_record_batch(
        root,
        work_ref(request.class_id, request.activity_id),
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    mutation = GroupPlanMutationResult(
        commit=WorkflowCommitResult.from_storage(
            storage_result,
            workspace_created=bootstrap.created,
        ),
        group_plan_id=candidate.group_plan_id,
        status=candidate.status,
    )
    assigned_count = sum(
        len(group.student_ids) for group in candidate.proposed_groups
    )
    return MissingSignalDispositionResult(
        mutation=mutation,
        disposition=request.disposition,
        missing_student_count=len(inspection.missing_student_ids),
        assigned_student_count=assigned_count,
        unresolved_student_count=len(candidate.unresolved_student_ids),
        group_sizes=tuple(
            len(group.student_ids) for group in candidate.proposed_groups
        ),
        random_seed=request.random_seed,
    )
