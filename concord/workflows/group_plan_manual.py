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
    clear_missing_signal_disposition: bool = False,
    expected_roster_student_ids: tuple[str, ...] | None = None,
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
            clear_missing_signal_disposition=clear_missing_signal_disposition,
            expected_roster_student_ids=expected_roster_student_ids,
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
        clear_missing_signal_disposition=True,
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


# #147: canonical Cluster-first batch preparation and one-write proposal mutation.
@dataclass(frozen=True, slots=True, kw_only=True)
class BulkPlannedGroupEditRequest:
    """One reviewed proposal edit, never a Core roster or operational Group edit."""

    class_id: str
    activity_id: str
    group_plan_id: str
    planned_group_key: str
    operation: str  # place_or_move | unassign_from_target
    student_ids: tuple[str, ...]
    expected_snapshot_revision: int
    expected_record_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkPlannedGroupStudentChange:
    student_id: str
    from_group_key: str | None
    to_group_key: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkPlannedGroupEditPreview:
    class_id: str
    activity_id: str
    group_plan_id: str
    planned_group_key: str
    operation: str
    snapshot_revision: int
    record_revision: int
    original_status: str
    roster_student_ids: tuple[str, ...]
    selected_student_ids: tuple[str, ...]
    changes: tuple[BulkPlannedGroupStudentChange, ...]
    unchanged_count: int
    before_sizes: tuple[tuple[str, int], ...]
    after_sizes: tuple[tuple[str, int], ...]
    unresolved_before: int
    unresolved_after: int
    proposed_groups: tuple[PlannedGroup, ...]
    review_digest: str
    no_op: bool


def _bulk_identifiers(request: BulkPlannedGroupEditRequest) -> tuple[str, ...]:
    if not isinstance(request, BulkPlannedGroupEditRequest):
        raise ConcordWorkflowValidationError("Bulk request must be typed.")
    if not isinstance(request.actor, WorkflowActor):
        raise ConcordWorkflowValidationError("A valid workflow actor is required.")
    if request.operation not in {"place_or_move", "unassign_from_target"}:
        raise ConcordWorkflowValidationError("Unsupported bulk placement operation.")
    _require_identifier(request.planned_group_key, "planned_group_key")
    if not isinstance(request.student_ids, tuple):
        raise ConcordWorkflowValidationError("student_ids must be a tuple.")
    values = tuple(
        _require_identifier(student_id, "student_id")
        for student_id in request.student_ids
    )
    if len(values) != len(set(values)):
        raise ConcordWorkflowValidationError(
            "Bulk student selection contains duplicate IDs."
        )
    return tuple(sorted(values))


def _bulk_review_digest(
    request: BulkPlannedGroupEditRequest,
    detail: GroupPlanDetail,
    *,
    root: Path,
    selected: tuple[str, ...],
    groups: tuple[PlannedGroup, ...],
    changes: tuple[BulkPlannedGroupStudentChange, ...],
) -> str:
    """Non-secret integrity binding: review is *not* authorization."""
    import hashlib
    import json

    payload = {
        "contract": "concord.group_plan_manual.bulk.v1",
        "workspace": str(root.resolve()),
        "class_id": request.class_id,
        "activity_id": request.activity_id,
        "group_plan_id": request.group_plan_id,
        "planned_group_key": request.planned_group_key,
        "operation": request.operation,
        "snapshot": detail.summary.snapshot_revision,
        "record_revision": detail.record_revision,
        "actor": repr(request.actor),
        "original_plan": repr(detail.plan),
        "selected": selected,
        "candidate_groups": tuple(repr(group) for group in groups),
        "changes": tuple(
            (item.student_id, item.from_group_key, item.to_group_key)
            for item in changes
        ),
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def prepare_bulk_planned_group_edit(
    request: BulkPlannedGroupEditRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> BulkPlannedGroupEditPreview:
    """Compute a complete read-only candidate from one live manual GroupPlan.

    Does not save a GroupPlan preview, change a snapshot or write Core state.
    The canonical service remains authoritative at the separate commit gate.
    """
    from dataclasses import replace

    selected = _bulk_identifiers(request)
    root, detail, roster = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    if detail.record_revision != request.expected_record_revision:
        raise ConcordWorkflowConflictError(
            "GroupPlan revision changed since the reviewed selection."
        )
    plan = detail.plan
    if plan.strategy != "manual":
        raise ConcordWorkflowConflictError(
            "Cluster-first bulk placement edits only manual GroupPlans."
        )
    groups_by_key = {
        group.planned_group_key: group for group in plan.proposed_groups
    }
    target = groups_by_key.get(request.planned_group_key)
    if target is None:
        raise ConcordWorkflowNotFoundError(
            f"PlannedGroup is not available: {request.planned_group_key}"
        )
    roster_set = set(roster)
    unknown = set(selected) - roster_set
    if unknown:
        raise ConcordWorkflowValidationError(
            f"Selected student is not in the current Core roster: {min(unknown)}"
        )
    assigned: dict[str, str] = {}
    for group in plan.proposed_groups:
        for student_id in group.student_ids:
            if student_id in assigned:
                raise ConcordWorkflowValidationError(
                    f"Student is assigned to more than one PlannedGroup: {student_id}"
                )
            assigned[student_id] = group.planned_group_key
    if request.operation == "unassign_from_target":
        outside = tuple(
            student_id for student_id in selected
            if assigned.get(student_id) != request.planned_group_key
        )
        if outside:
            raise ConcordWorkflowValidationError(
                f"Selected student is not in the chosen PlannedGroup: {outside[0]}"
            )
    destination = (
        request.planned_group_key
        if request.operation == "place_or_move" else None
    )
    changes = tuple(
        BulkPlannedGroupStudentChange(
            student_id=student_id,
            from_group_key=assigned.get(student_id),
            to_group_key=destination,
        )
        for student_id in selected
        if assigned.get(student_id) != destination
    )
    changed_ids = {change.student_id for change in changes}
    updated_groups = tuple(
        replace(
            group,
            student_ids=tuple(
                sorted(
                    (
                        set(group.student_ids) - changed_ids
                    ) | (
                        changed_ids
                        if (destination == group.planned_group_key) else set()
                    )
                )
            ),
        )
        for group in plan.proposed_groups
    ) if changes else plan.proposed_groups
    assigned_after = {
        student_id
        for group in updated_groups for student_id in group.student_ids
    }
    unresolved_after = roster_set - assigned_after
    digest = _bulk_review_digest(
        request, detail, root=root, selected=selected,
        groups=updated_groups, changes=changes,
    )
    return BulkPlannedGroupEditPreview(
        class_id=request.class_id,
        activity_id=request.activity_id,
        group_plan_id=request.group_plan_id,
        planned_group_key=request.planned_group_key,
        operation=request.operation,
        snapshot_revision=detail.summary.snapshot_revision,
        record_revision=detail.record_revision,
        original_status=plan.status,
        roster_student_ids=roster,
        selected_student_ids=selected,
        changes=changes,
        unchanged_count=len(selected) - len(changes),
        before_sizes=tuple(
            (g.planned_group_key, len(g.student_ids)) for g in plan.proposed_groups
        ),
        after_sizes=tuple(
            (g.planned_group_key, len(g.student_ids)) for g in updated_groups
        ),
        unresolved_before=len(plan.unresolved_student_ids),
        unresolved_after=len(unresolved_after),
        proposed_groups=updated_groups,
        review_digest=digest,
        no_op=not changes,
    )


def commit_bulk_planned_group_edit(
    request: BulkPlannedGroupEditRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanEditResult:
    """Recheck reviewed candidate then make at most one canonical plan write."""
    import hmac

    if (
        not isinstance(review_digest, str)
        or len(review_digest) != 64
        or any(char not in "0123456789abcdef" for char in review_digest)
    ):
        raise ConcordWorkflowValidationError("Valid batch review digest required.")
    reviewed = prepare_bulk_planned_group_edit(
        request,
        workspace_root=workspace_root,
        standards_library=standards_library,
    )
    if not hmac.compare_digest(reviewed.review_digest, review_digest):
        raise ConcordWorkflowConflictError(
            "Batch review is no longer valid for this exact selection; review again."
        )
    root, detail, roster = _load_targeted_edit(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        request.expected_snapshot_revision,
        workspace_root=workspace_root,
    )
    if detail.record_revision != reviewed.record_revision:
        raise ConcordWorkflowConflictError("GroupPlan revision changed before save.")
    if not reviewed.changes:
        return _no_change(detail)
    # This recheck also ensures the proposed candidate has not changed between
    # review and commit. The canonical service checks CAS again under its lock.
    return _replace_preserving_origin(
        detail,
        reviewed.proposed_groups,
        request.actor,
        root=root,
        standards_library=standards_library,
        clock=clock,
        expected_roster_student_ids=roster,
    )
