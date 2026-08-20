"""Teacher-controlled manual and arrangement-import GroupPlan authoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.identifiers import IdentifierValidationError, validate_identifier
from pds_core.standards import StandardsLibrary

from concord.group_plan_arrangement_csv import (
    ArrangementCsvResult,
    parse_arrangement_csv_file,
)
from concord.models import ConcordModelError, EffectiveContext, PlannedGroup
from concord.workflows.context import Clock, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan import (
    CreateGroupPlanRequest,
    GroupPlanDetail,
    GroupPlanMutationResult,
    ReplaceGroupPlanProposalRequest,
    create_group_plan,
    replace_group_plan_proposal,
    show_group_plan,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import load_required_roster


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateManualGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    proposed_groups: tuple[PlannedGroup, ...] = ()
    target_group_size: int | None = None
    target_group_count: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AddPlannedGroupRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    planned_group_key: str
    label: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    description: str | None = None
    effective_context: EffectiveContext | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class EditPlannedGroupRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    planned_group_key: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    label: str | None = None
    description: str | None = None
    clear_description: bool = False
    effective_context: EffectiveContext | None = None
    clear_effective_context: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class RemovePlannedGroupRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    planned_group_key: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PlaceStudentInPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    student_id: str
    planned_group_key: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class UnassignStudentFromPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    student_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class RefreshGroupPlanRosterRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class ImportArrangementGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    csv_path: str | Path
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceArrangementGroupPlanRequest:
    class_id: str
    activity_id: str
    group_plan_id: str
    csv_path: str | Path
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupPlanEditResult:
    detail: GroupPlanDetail
    changed: bool
    mutation: GroupPlanMutationResult | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ArrangementImportResult:
    mutation: GroupPlanMutationResult
    data_row_count: int
    proposed_group_count: int
    assigned_student_count: int
    unresolved_student_count: int


def _root(workspace_root: str | Path | None) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    return root


def _roster_student_ids(root: Path, class_id: str) -> tuple[str, ...]:
    roster = load_required_roster(root, class_id)
    return tuple(sorted(student.student_id for student in roster.students))


def _require_expected_snapshot(detail: GroupPlanDetail, expected: int) -> None:
    if detail.summary.snapshot_revision != expected:
        raise ConcordWorkflowConflictError(
            "Activity changed since the caller's expected snapshot."
        )


def _require_editable(detail: GroupPlanDetail) -> None:
    if detail.plan.status not in {"draft", "previewed"}:
        raise ConcordWorkflowConflictError(
            "Only draft or previewed GroupPlans may be edited."
        )


def _require_identifier(value: str, field_name: str) -> str:
    try:
        return validate_identifier(value, field_name)
    except IdentifierValidationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _load_targeted_edit(
    class_id: str,
    activity_id: str,
    group_plan_id: str,
    expected_snapshot_revision: int,
    *,
    workspace_root: str | Path | None,
) -> tuple[Path, GroupPlanDetail, tuple[str, ...]]:
    root = _root(workspace_root)
    detail = show_group_plan(
        class_id,
        activity_id,
        group_plan_id,
        workspace_root=root,
    )
    _require_expected_snapshot(detail, expected_snapshot_revision)
    _require_editable(detail)
    current_roster = _roster_student_ids(root, class_id)
    if current_roster != detail.plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed since this GroupPlan proposal revision; "
            "refresh the GroupPlan roster explicitly before editing."
        )
    return root, detail, current_roster


def _replace_preserving_origin(
    detail: GroupPlanDetail,
    groups: tuple[PlannedGroup, ...],
    actor: WorkflowActor,
    *,
    root: Path,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
) -> GroupPlanEditResult:
    plan = detail.plan
    result = replace_group_plan_proposal(
        ReplaceGroupPlanProposalRequest(
            class_id=plan.class_reference.record_id,
            activity_id=plan.activity_id,
            group_plan_id=plan.group_plan_id,
            strategy=plan.strategy,
            proposed_groups=groups,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=actor,
            target_group_size=plan.target_group_size,
            target_group_count=plan.target_group_count,
            seed=plan.seed,
            source_signal_set_id=plan.source_signal_set_id,
            source_signal_set_digest=plan.source_signal_set_digest,
            source_signal_dimension_id=plan.source_signal_dimension_id,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )
    updated = show_group_plan(
        plan.class_reference.record_id,
        plan.activity_id,
        plan.group_plan_id,
        workspace_root=root,
    )
    if updated.summary.snapshot_revision != result.commit.snapshot_revision:
        raise ConcordWorkflowConflictError(
            "GroupPlan changed unexpectedly after proposal replacement."
        )
    return GroupPlanEditResult(detail=updated, changed=True, mutation=result)


def _no_change(detail: GroupPlanDetail) -> GroupPlanEditResult:
    return GroupPlanEditResult(detail=detail, changed=False, mutation=None)


def _new_planned_group(
    *,
    planned_group_key: str,
    label: str,
    student_ids: tuple[str, ...] = (),
    description: str | None = None,
    effective_context: EffectiveContext | None = None,
) -> PlannedGroup:
    try:
        return PlannedGroup(
            planned_group_key=planned_group_key,
            label=label,
            student_ids=student_ids,
            description=description,
            effective_context=effective_context,
        )
    except ConcordModelError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def create_manual_group_plan(
    request: CreateManualGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanMutationResult:
    """Create one manual draft while reusing the #50 creation boundary."""

    return create_group_plan(
        CreateGroupPlanRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_plan_id=request.group_plan_id,
            strategy="manual",
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            proposed_groups=request.proposed_groups,
            target_group_size=request.target_group_size,
            target_group_count=request.target_group_count,
        ),
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )


def add_planned_group(
    request: AddPlannedGroupRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    root, detail, _ = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    key = _require_identifier(request.planned_group_key, "planned_group_key")
    if any(group.planned_group_key == key for group in detail.plan.proposed_groups):
        raise ConcordWorkflowConflictError(
            f"PlannedGroup already exists in this plan: {key}"
        )
    group = _new_planned_group(
        planned_group_key=key,
        label=request.label,
        description=request.description,
        effective_context=request.effective_context,
    )
    return _replace_preserving_origin(
        detail,
        detail.plan.proposed_groups + (group,),
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )


def edit_planned_group(
    request: EditPlannedGroupRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    root, detail, _ = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    key = _require_identifier(request.planned_group_key, "planned_group_key")
    current = next(
        (
            group
            for group in detail.plan.proposed_groups
            if group.planned_group_key == key
        ),
        None,
    )
    if current is None:
        raise ConcordWorkflowNotFoundError(f"PlannedGroup is not available: {key}")
    if request.clear_description and request.description is not None:
        raise ConcordWorkflowValidationError(
            "description and clear_description are mutually exclusive."
        )
    if request.clear_effective_context and request.effective_context is not None:
        raise ConcordWorkflowValidationError(
            "effective_context and clear_effective_context are mutually exclusive."
        )
    label = current.label if request.label is None else request.label
    if request.clear_description:
        description = None
    elif request.description is not None:
        description = request.description
    else:
        description = current.description
    if request.clear_effective_context:
        context = None
    elif request.effective_context is not None:
        context = request.effective_context
    else:
        context = current.effective_context
    replacement = _new_planned_group(
        planned_group_key=current.planned_group_key,
        label=label,
        student_ids=current.student_ids,
        description=description,
        effective_context=context,
    )
    if replacement == current:
        return _no_change(detail)
    groups = tuple(
        replacement if group.planned_group_key == key else group
        for group in detail.plan.proposed_groups
    )
    return _replace_preserving_origin(
        detail,
        groups,
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )


def remove_planned_group(
    request: RemovePlannedGroupRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    root, detail, _ = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    key = _require_identifier(request.planned_group_key, "planned_group_key")
    if not any(group.planned_group_key == key for group in detail.plan.proposed_groups):
        raise ConcordWorkflowNotFoundError(f"PlannedGroup is not available: {key}")
    groups = tuple(
        group for group in detail.plan.proposed_groups if group.planned_group_key != key
    )
    return _replace_preserving_origin(
        detail,
        groups,
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )


def place_student_in_plan(
    request: PlaceStudentInPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    root, detail, roster = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    student_id = _require_identifier(request.student_id, "student_id")
    key = _require_identifier(request.planned_group_key, "planned_group_key")
    if student_id not in set(roster):
        raise ConcordWorkflowValidationError(
            f"Student is not in the current Core roster: {student_id}"
        )
    destination = next(
        (
            group
            for group in detail.plan.proposed_groups
            if group.planned_group_key == key
        ),
        None,
    )
    if destination is None:
        raise ConcordWorkflowNotFoundError(f"PlannedGroup is not available: {key}")
    if student_id in destination.student_ids:
        return _no_change(detail)

    groups: list[PlannedGroup] = []
    for group in detail.plan.proposed_groups:
        students = tuple(item for item in group.student_ids if item != student_id)
        if group.planned_group_key == key:
            students = students + (student_id,)
        groups.append(
            _new_planned_group(
                planned_group_key=group.planned_group_key,
                label=group.label,
                student_ids=students,
                description=group.description,
                effective_context=group.effective_context,
            )
        )
    return _replace_preserving_origin(
        detail,
        tuple(groups),
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )


def unassign_student_from_plan(
    request: UnassignStudentFromPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    root, detail, roster = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    student_id = _require_identifier(request.student_id, "student_id")
    if student_id not in set(roster):
        raise ConcordWorkflowValidationError(
            f"Student is not in the current Core roster: {student_id}"
        )
    if student_id in detail.plan.unresolved_student_ids:
        return _no_change(detail)

    groups = tuple(
        _new_planned_group(
            planned_group_key=group.planned_group_key,
            label=group.label,
            student_ids=tuple(
                item for item in group.student_ids if item != student_id
            ),
            description=group.description,
            effective_context=group.effective_context,
        )
        for group in detail.plan.proposed_groups
    )
    return _replace_preserving_origin(
        detail,
        groups,
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )


def refresh_group_plan_roster(
    request: RefreshGroupPlanRosterRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    root = _root(workspace_root)
    detail = show_group_plan(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        workspace_root=root,
    )
    _require_expected_snapshot(detail, request.expected_snapshot_revision)
    _require_editable(detail)
    current_roster = _roster_student_ids(root, request.class_id)
    if current_roster == detail.plan.roster_student_ids:
        return _no_change(detail)

    current_set = set(current_roster)
    groups = tuple(
        _new_planned_group(
            planned_group_key=group.planned_group_key,
            label=group.label,
            student_ids=tuple(
                student_id
                for student_id in group.student_ids
                if student_id in current_set
            ),
            description=group.description,
            effective_context=group.effective_context,
        )
        for group in detail.plan.proposed_groups
    )
    return _replace_preserving_origin(
        detail,
        groups,
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )


def _parse_for_current_roster(
    class_id: str,
    csv_path: str | Path,
    *,
    workspace_root: str | Path | None,
) -> tuple[Path, ArrangementCsvResult]:
    root = _root(workspace_root)
    roster = _roster_student_ids(root, class_id)
    parsed = parse_arrangement_csv_file(csv_path, roster_student_ids=roster)
    return root, parsed


def _import_result(
    mutation: GroupPlanMutationResult,
    parsed: ArrangementCsvResult,
) -> ArrangementImportResult:
    return ArrangementImportResult(
        mutation=mutation,
        data_row_count=parsed.data_row_count,
        proposed_group_count=parsed.proposed_group_count,
        assigned_student_count=parsed.assigned_student_count,
        unresolved_student_count=parsed.unresolved_student_count,
    )


def import_arrangement_group_plan(
    request: ImportArrangementGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArrangementImportResult:
    """Create an imported-arrangement draft after full CSV validation."""

    root, parsed = _parse_for_current_roster(
        request.class_id,
        request.csv_path,
        workspace_root=workspace_root,
    )
    mutation = create_group_plan(
        CreateGroupPlanRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_plan_id=request.group_plan_id,
            strategy="imported_arrangement",
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            proposed_groups=parsed.proposed_groups,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )
    return _import_result(mutation, parsed)


def replace_group_plan_from_arrangement(
    request: ReplaceArrangementGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArrangementImportResult:
    """Atomically replace one editable proposal from a validated arrangement CSV."""

    root, parsed = _parse_for_current_roster(
        request.class_id,
        request.csv_path,
        workspace_root=workspace_root,
    )
    mutation = replace_group_plan_proposal(
        ReplaceGroupPlanProposalRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_plan_id=request.group_plan_id,
            strategy="imported_arrangement",
            proposed_groups=parsed.proposed_groups,
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )
    return _import_result(mutation, parsed)
