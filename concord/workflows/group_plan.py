"""Application services for GroupPlan creation, revision, and approval."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import GroupPlan, PlannedGroup
from concord.storage import (
    commit_record_batch,
    load_current_record,
    load_current_snapshot,
    load_work_snapshot,
)
from concord.storage_errors import ConcordStorageNotFoundError
from concord.workflows._collaboration import (
    current_records_of_kind,
    load_graph,
    require_activity,
    require_new_identity,
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
from concord.workflows.grouping_signal import select_grouping_signal_dimension
from concord.workflows.models import WorkflowActor, WorkflowCommitResult
from concord.workflows.participants import load_required_roster

_SIGNAL_STRATEGIES = frozenset({"similar_signal", "mixed_signal"})


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateGroupPlanRequest:
    """Create one draft plan against the exact current Core roster."""

    class_id: str
    activity_id: str
    group_plan_id: str
    strategy: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    proposed_groups: tuple[PlannedGroup, ...] = ()
    target_group_size: int | None = None
    target_group_count: int | None = None
    seed: str | None = None
    source_signal_set_id: str | None = None
    source_signal_set_digest: str | None = None
    source_signal_dimension_id: str | None = None
    expected_roster_student_ids: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceGroupPlanProposalRequest:
    """Replace all editable proposal content under one stable plan identity."""

    class_id: str
    activity_id: str
    group_plan_id: str
    strategy: str
    proposed_groups: tuple[PlannedGroup, ...]
    expected_snapshot_revision: int
    actor: WorkflowActor
    target_group_size: int | None = None
    target_group_count: int | None = None
    seed: str | None = None
    source_signal_set_id: str | None = None
    source_signal_set_digest: str | None = None
    source_signal_dimension_id: str | None = None
    clear_missing_signal_disposition: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviewGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class ApproveGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupPlanSummary:
    class_id: str
    activity_id: str
    group_plan_id: str
    strategy: str
    status: str
    proposed_group_count: int
    assigned_student_count: int
    unresolved_student_count: int
    target_group_size: int | None
    target_group_count: int | None
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupPlanDetail:
    """Exact persisted plan plus native revision/snapshot identity."""

    summary: GroupPlanSummary
    plan: GroupPlan
    record_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupPlanMutationResult:
    commit: WorkflowCommitResult
    group_plan_id: str
    status: str


def _require_expected_snapshot(actual: int, expected: int) -> None:
    if actual != expected:
        raise ConcordWorkflowConflictError(
            "Activity changed since the caller's expected snapshot."
        )


def _require_plan(
    graph: ConcordRecordGraph,
    group_plan_id: str,
) -> GroupPlan:
    plans = getattr(graph, "group_plans", ())
    for plan in plans:
        if isinstance(plan, GroupPlan) and plan.group_plan_id == group_plan_id:
            return plan
    raise ConcordWorkflowNotFoundError(
        f"GroupPlan is not available: {group_plan_id}"
    )


def _roster_student_ids(root: Path, class_id: str) -> tuple[str, ...]:
    roster = load_required_roster(root, class_id)
    return tuple(sorted(student.student_id for student in roster.students))


def _validate_proposed_students(
    groups: tuple[PlannedGroup, ...],
    roster_student_ids: tuple[str, ...],
) -> tuple[str, ...]:
    roster = set(roster_student_ids)
    assigned: list[str] = []
    group_keys: set[str] = set()
    for group in groups:
        if not isinstance(group, PlannedGroup):
            raise ConcordWorkflowValidationError(
                "proposed_groups must contain PlannedGroup values."
            )
        if group.planned_group_key in group_keys:
            raise ConcordWorkflowValidationError(
                "proposed_groups must not duplicate planned_group_key."
            )
        group_keys.add(group.planned_group_key)
        for student_id in group.student_ids:
            if student_id not in roster:
                raise ConcordWorkflowValidationError(
                    "Proposed student is not in the current Core roster: "
                    f"{student_id}"
                )
            if student_id in assigned:
                raise ConcordWorkflowValidationError(
                    "A student may appear in at most one PlannedGroup: "
                    f"{student_id}"
                )
            assigned.append(student_id)
    return tuple(sorted(roster - set(assigned)))


def _require_plan_activity(
    class_id: str,
    activity_id: str,
    graph: ConcordRecordGraph,
) -> None:
    activity = require_activity(graph, activity_id)
    if activity.class_reference.record_id != class_id:
        raise ConcordWorkflowValidationError(
            "GroupPlan class must exactly match the Activity Core class."
        )


def _summary(plan: GroupPlan, snapshot_revision: int) -> GroupPlanSummary:
    assigned = sum(len(group.student_ids) for group in plan.proposed_groups)
    return GroupPlanSummary(
        class_id=plan.class_reference.record_id,
        activity_id=plan.activity_id,
        group_plan_id=plan.group_plan_id,
        strategy=plan.strategy,
        status=plan.status,
        proposed_group_count=len(plan.proposed_groups),
        assigned_student_count=assigned,
        unresolved_student_count=len(plan.unresolved_student_ids),
        target_group_size=plan.target_group_size,
        target_group_count=plan.target_group_count,
        snapshot_revision=snapshot_revision,
    )


def _detail_from_current(
    root: Path,
    class_id: str,
    activity_id: str,
    group_plan_id: str,
) -> GroupPlanDetail:
    work = work_ref(class_id, activity_id)
    try:
        record, envelope = load_current_record(
            root,
            work,
            "group_plan",
            group_plan_id,
        )
        current = load_current_snapshot(root, work)
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"GroupPlan is not available: {group_plan_id}"
        ) from error
    if not isinstance(record, GroupPlan):
        raise ConcordWorkflowNotFoundError(
            f"GroupPlan is not available: {group_plan_id}"
        )
    return GroupPlanDetail(
        summary=_summary(record, current.snapshot_revision),
        plan=record,
        record_revision=envelope.record_revision,
    )


def _require_current_roster(
    root: Path,
    class_id: str,
    plan: GroupPlan,
) -> None:
    current = _roster_student_ids(root, class_id)
    if current != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed since this GroupPlan proposal revision."
        )


def _current_signal_missing_student_ids(
    root: Path,
    class_id: str,
    plan: GroupPlan,
) -> tuple[str, ...]:
    # Revalidate the exact bound signal and selected-dimension missing IDs.
    if plan.strategy not in _SIGNAL_STRATEGIES:
        return ()

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

    if _roster_student_ids(root, class_id) != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed while validating the GroupPlan signal binding; "
            "refresh and preview the plan again."
        )

    missing = tuple(
        sorted(
            finding.student_id
            for finding in selection.inspection.diagnostics.findings
            if finding.code == "missing_student_signal"
            and finding.dimension_id == dimension_id
            and finding.student_id is not None
        )
    )
    if len(missing) != selection.dimension_diagnostics.missing_student_count:
        raise ConcordWorkflowValidationError(
            "Core grouping-signal diagnostics returned inconsistent "
            "missing-student detail."
        )
    return missing


def _require_preview_is_latest_work_change(
    root: Path,
    class_id: str,
    activity_id: str,
    group_plan_id: str,
) -> None:
    """Require the previewed plan revision to have created the current snapshot."""

    work = work_ref(class_id, activity_id)
    current = load_current_snapshot(root, work)
    current_snapshot, _ = load_work_snapshot(
        root,
        work,
        current.snapshot_revision,
    )
    current_ref = next(
        (
            item
            for item in current_snapshot.records
            if item.record_kind == "group_plan"
            and item.record_id == group_plan_id
        ),
        None,
    )
    if current_ref is None:
        raise ConcordWorkflowNotFoundError(
            f"GroupPlan is not available: {group_plan_id}"
        )
    if current.snapshot_revision == 1:
        return
    previous_snapshot, _ = load_work_snapshot(
        root,
        work,
        current.snapshot_revision - 1,
    )
    previous_ref = next(
        (
            item
            for item in previous_snapshot.records
            if item.record_kind == "group_plan"
            and item.record_id == group_plan_id
        ),
        None,
    )
    if (
        previous_ref is not None
        and previous_ref.record_revision == current_ref.record_revision
    ):
        raise ConcordWorkflowConflictError(
            "Activity changed after GroupPlan preview; preview the plan again."
        )


def create_group_plan(
    request: CreateGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanMutationResult:
    """Create one draft GroupPlan without creating canonical Groups."""

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    _require_plan_activity(request.class_id, request.activity_id, graph)
    require_new_identity(
        graph.group_plans,
        "group_plan_id",
        request.group_plan_id,
        "GroupPlan",
    )
    roster_student_ids = _roster_student_ids(root, request.class_id)
    if (
        request.expected_roster_student_ids is not None
        and roster_student_ids != request.expected_roster_student_ids
    ):
        raise ConcordWorkflowConflictError(
            "Core roster changed while preparing the GroupPlan; reload and retry."
        )
    unresolved = _validate_proposed_students(
        request.proposed_groups,
        roster_student_ids,
    )
    activity = require_activity(graph, request.activity_id)
    plan = GroupPlan(
        group_plan_id=request.group_plan_id,
        activity_id=request.activity_id,
        class_reference=activity.class_reference,
        strategy=request.strategy,
        status="draft",
        roster_student_ids=roster_student_ids,
        proposed_groups=request.proposed_groups,
        unresolved_student_ids=unresolved,
        target_group_size=request.target_group_size,
        target_group_count=request.target_group_count,
        seed=request.seed,
        source_signal_set_id=request.source_signal_set_id,
        source_signal_set_digest=request.source_signal_set_digest,
        source_signal_dimension_id=request.source_signal_dimension_id,
        created_provenance=provenance(request.actor, clock=clock),
    )
    result = commit_record_batch(
        root,
        work,
        (plan,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupPlanMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_plan_id=plan.group_plan_id,
        status=plan.status,
    )


def replace_group_plan_proposal(
    request: ReplaceGroupPlanProposalRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanMutationResult:
    """Replace editable proposal content and return any preview to draft."""

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    _require_plan_activity(request.class_id, request.activity_id, graph)
    current = _require_plan(graph, request.group_plan_id)
    if current.status not in {"draft", "previewed"}:
        raise ConcordWorkflowConflictError(
            "Only draft or previewed GroupPlans may replace proposal content."
        )
    roster_student_ids = _roster_student_ids(root, request.class_id)
    unresolved = _validate_proposed_students(
        request.proposed_groups,
        roster_student_ids,
    )
    if not isinstance(request.clear_missing_signal_disposition, bool):
        raise ConcordWorkflowValidationError(
            "clear_missing_signal_disposition must be a boolean."
        )
    if request.clear_missing_signal_disposition:
        disposition = None
        disposition_seed = None
        disposition_provenance = None
    else:
        disposition = current.missing_signal_disposition
        disposition_seed = current.missing_signal_random_seed
        disposition_provenance = current.missing_signal_disposition_provenance

    candidate = GroupPlan(
        group_plan_id=current.group_plan_id,
        activity_id=current.activity_id,
        class_reference=current.class_reference,
        strategy=request.strategy,
        status="draft",
        roster_student_ids=roster_student_ids,
        proposed_groups=request.proposed_groups,
        unresolved_student_ids=unresolved,
        target_group_size=request.target_group_size,
        target_group_count=request.target_group_count,
        seed=request.seed,
        source_signal_set_id=request.source_signal_set_id,
        source_signal_set_digest=request.source_signal_set_digest,
        source_signal_dimension_id=request.source_signal_dimension_id,
        missing_signal_disposition=disposition,
        missing_signal_random_seed=disposition_seed,
        missing_signal_disposition_provenance=disposition_provenance,
        created_provenance=current.created_provenance,
        updated_provenance=provenance(request.actor, clock=clock),
    )
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupPlanMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_plan_id=candidate.group_plan_id,
        status=candidate.status,
    )


def list_group_plans(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[GroupPlanSummary, ...]:
    """List privacy-minimized plan summaries without roster display data."""

    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = work_ref(class_id, activity_id)
    records, revision = current_records_of_kind(root, work, "group_plan")
    plans = tuple(item for item in records if isinstance(item, GroupPlan))
    return tuple(
        sorted(
            (_summary(plan, revision) for plan in plans),
            key=lambda item: item.group_plan_id,
        )
    )


def show_group_plan(
    class_id: str,
    activity_id: str,
    group_plan_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> GroupPlanDetail:
    """Return the exact current persisted plan without mutating its status."""

    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    return _detail_from_current(
        root,
        class_id,
        activity_id,
        group_plan_id,
    )


def preview_group_plan(
    request: PreviewGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanDetail:
    """Persist and return the exact proposal revision presented for preview."""

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    _require_plan_activity(request.class_id, request.activity_id, graph)
    current = _require_plan(graph, request.group_plan_id)
    if current.status != "draft":
        raise ConcordWorkflowConflictError(
            "Only a draft GroupPlan may be previewed."
        )
    _require_current_roster(root, request.class_id, current)
    candidate = replace(
        current,
        status="previewed",
        previewed_provenance=provenance(request.actor, clock=clock),
        approved_provenance=None,
        cancelled_provenance=None,
        applied_provenance=None,
    )
    commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return _detail_from_current(
        root,
        request.class_id,
        request.activity_id,
        request.group_plan_id,
    )


def approve_group_plan(
    request: ApproveGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanMutationResult:
    """Approve exactly the current preview without applying it."""

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    _require_plan_activity(request.class_id, request.activity_id, graph)
    current = _require_plan(graph, request.group_plan_id)
    if current.status != "previewed":
        raise ConcordWorkflowConflictError(
            "Only a previewed GroupPlan may be approved."
        )
    _require_current_roster(root, request.class_id, current)
    _require_preview_is_latest_work_change(
        root,
        request.class_id,
        request.activity_id,
        request.group_plan_id,
    )
    if current.strategy in _SIGNAL_STRATEGIES:
        missing_student_ids = _current_signal_missing_student_ids(
            root,
            request.class_id,
            current,
        )
        if missing_student_ids:
            disposition = current.missing_signal_disposition
            if disposition is None:
                raise ConcordWorkflowValidationError(
                    "Signal-backed GroupPlan approval requires an explicit "
                    "missing-signal disposition."
                )
            if disposition in {"manual", "random"}:
                if current.unresolved_student_ids:
                    raise ConcordWorkflowValidationError(
                        "Manual/random missing-signal disposition requires every "
                        "roster student to be resolved before approval."
                    )
            elif disposition == "leave_unassigned":
                if set(current.unresolved_student_ids) != set(missing_student_ids):
                    raise ConcordWorkflowValidationError(
                        "leave_unassigned approval requires unresolved students "
                        "to exactly equal the current missing-signal population."
                    )
            else:
                raise ConcordWorkflowValidationError(
                    "Signal-backed GroupPlan has an invalid missing-signal "
                    "disposition."
                )
        elif current.unresolved_student_ids:
            raise ConcordWorkflowValidationError(
                "GroupPlan approval requires every roster student to be resolved."
            )
    elif current.unresolved_student_ids:
        raise ConcordWorkflowValidationError(
            "GroupPlan approval requires every roster student to be resolved."
        )
    if not any(group.student_ids for group in current.proposed_groups):
        raise ConcordWorkflowValidationError(
            "GroupPlan approval requires at least one nonempty PlannedGroup."
        )
    candidate = replace(
        current,
        status="approved",
        approved_provenance=provenance(request.actor, clock=clock),
    )
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupPlanMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_plan_id=candidate.group_plan_id,
        status=candidate.status,
    )


def cancel_group_plan(
    request: CancelGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanMutationResult:
    """Cancel a draft, previewed, or approved plan without deleting history."""

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    _require_plan_activity(request.class_id, request.activity_id, graph)
    current = _require_plan(graph, request.group_plan_id)
    if current.status not in {"draft", "previewed", "approved"}:
        raise ConcordWorkflowConflictError(
            "Only draft, previewed, or approved GroupPlans may be cancelled."
        )
    candidate = replace(
        current,
        status="cancelled",
        cancelled_provenance=provenance(request.actor, clock=clock),
    )
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupPlanMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        group_plan_id=candidate.group_plan_id,
        status=candidate.status,
    )
