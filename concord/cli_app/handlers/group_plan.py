"""Direct GroupPlan authoring and lifecycle commands."""

from __future__ import annotations

import argparse

from concord.cli_app.common import (
    effective_context,
    load_command_standards_library,
    workflow_actor,
    workspace_arg,
)
from concord.cli_app.output import print_commit
from concord.workflows import (
    AddPlannedGroupRequest,
    ApplyGroupPlanRequest,
    ApproveGroupPlanRequest,
    ArrangementImportResult,
    CancelGroupPlanRequest,
    CreateManualGroupPlanRequest,
    CreateRandomGroupPlanRequest,
    CreateSignalGroupPlanRequest,
    EditPlannedGroupRequest,
    GroupPlanApplicationPreview,
    GroupPlanDetail,
    GroupPlanEditResult,
    GroupPlanSummary,
    ImportArrangementGroupPlanRequest,
    MissingSignalDispositionResult,
    PlaceStudentInPlanRequest,
    PrepareGroupPlanApplicationRequest,
    PreviewGroupPlanRequest,
    RefreshGroupPlanRosterRequest,
    RemovePlannedGroupRequest,
    ReplaceArrangementGroupPlanRequest,
    SetMissingSignalDispositionRequest,
    SignalGroupPlanCreationResult,
    UnassignStudentFromPlanRequest,
    add_planned_group,
    apply_group_plan,
    approve_group_plan,
    cancel_group_plan,
    create_manual_group_plan,
    create_random_group_plan,
    create_signal_group_plan,
    edit_planned_group,
    import_arrangement_group_plan,
    list_group_plans,
    place_student_in_plan,
    prepare_group_plan_application,
    preview_group_plan,
    refresh_group_plan_roster,
    remove_planned_group,
    replace_group_plan_from_arrangement,
    set_missing_signal_disposition,
    show_group_plan,
    unassign_student_from_plan,
)


def _print_summary(item: GroupPlanSummary) -> None:
    print(
        f"{item.group_plan_id}\t{item.strategy}\t{item.status}\t"
        f"groups={item.proposed_group_count}\tassigned={item.assigned_student_count}\t"
        f"unresolved={item.unresolved_student_count}\t"
        f"snapshot={item.snapshot_revision}"
    )


def _print_detail(detail: GroupPlanDetail) -> None:
    item = detail.summary
    plan = detail.plan
    print(f"GroupPlan: {item.group_plan_id}")
    print(f"Class: {item.class_id}")
    print(f"Activity: {item.activity_id}")
    print(f"Strategy: {item.strategy}")
    print(f"Status: {item.status}")
    print(f"Record revision: {detail.record_revision}")
    print(f"Snapshot revision: {item.snapshot_revision}")
    print(f"Proposed groups: {item.proposed_group_count}")
    print(f"Assigned students: {item.assigned_student_count}")
    print(f"Unresolved students: {item.unresolved_student_count}")
    if plan.target_group_size is not None:
        print(f"Target group size: {plan.target_group_size}")
    if plan.target_group_count is not None:
        print(f"Target group count: {plan.target_group_count}")
    if plan.seed is not None:
        print(f"Seed: {plan.seed}")
    if plan.source_signal_set_id is not None:
        print(f"Signal set: {plan.source_signal_set_id}")
        print(f"Signal digest: {plan.source_signal_set_digest}")
        print(f"Signal dimension: {plan.source_signal_dimension_id}")
    if plan.missing_signal_disposition is not None:
        print(f"Missing-signal disposition: {plan.missing_signal_disposition}")
    if plan.missing_signal_random_seed is not None:
        print(f"Missing-signal random seed: {plan.missing_signal_random_seed}")
    for group in plan.proposed_groups:
        students = ",".join(group.student_ids) or "-"
        print(
            f"Planned group: {group.planned_group_key}\tlabel={group.label}\t"
            f"students={students}"
        )
        if group.description is not None:
            print(f"  Description: {group.description}")
        if group.effective_context is not None:
            print(f"  Sessions: {','.join(group.effective_context.session_ids)}")
    if plan.unresolved_student_ids:
        print(f"Unresolved student IDs: {','.join(plan.unresolved_student_ids)}")


def _print_edit(result: GroupPlanEditResult) -> None:
    if result.mutation is None:
        print("No changes were needed.")
    else:
        print_commit(result.mutation.commit)
    print(f"GroupPlan: {result.detail.summary.group_plan_id}")
    print(f"Status: {result.detail.summary.status}")
    print(f"Unresolved students: {result.detail.summary.unresolved_student_count}")
    print(f"Snapshot revision: {result.detail.summary.snapshot_revision}")


def handle_list(args: argparse.Namespace) -> int:
    items = list_group_plans(
        args.class_id,
        args.activity_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No GroupPlans found.")
        return 0
    for item in items:
        _print_summary(item)
    return 0


def handle_show(args: argparse.Namespace) -> int:
    detail = show_group_plan(
        args.class_id,
        args.activity_id,
        args.group_plan_id,
        workspace_root=workspace_arg(args),
    )
    _print_detail(detail)
    return 0


def handle_create_manual(args: argparse.Namespace) -> int:
    result = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            target_group_size=args.target_group_size,
            target_group_count=args.target_group_count,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"GroupPlan: {result.group_plan_id}")
    print(f"Status: {result.status}")
    return 0


def handle_create_random(args: argparse.Namespace) -> int:
    result = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            seed=args.seed,
            target_group_size=args.target_group_size,
            target_group_count=args.target_group_count,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    mutation = result.mutation
    print_commit(mutation.commit)
    print(f"GroupPlan: {mutation.group_plan_id}")
    print("Strategy: random")
    print(f"Status: {mutation.status}")
    if args.target_group_size is not None:
        print(f"Target group size: {args.target_group_size}")
    else:
        print(f"Target group count: {args.target_group_count}")
    print(f"Seed: {args.seed}")
    print(f"Generated groups: {result.group_count}")
    print(f"Assigned students: {result.assigned_student_count}")
    print("Unresolved students: 0")
    print(f"Group sizes: {','.join(str(size) for size in result.group_sizes)}")
    print("Canonical Groups created: no")
    return 0


def _handle_create_signal(args: argparse.Namespace, strategy: str) -> int:
    result = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            strategy=strategy,
            signal_set_id=args.signal_set_id,
            dimension_id=args.dimension_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            target_group_size=args.target_group_size,
            target_group_count=args.target_group_count,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_signal_create_result(result, args)
    return 0


def _print_signal_create_result(
    result: SignalGroupPlanCreationResult,
    args: argparse.Namespace,
) -> None:
    mutation = result.mutation
    print_commit(mutation.commit)
    print(f"GroupPlan: {mutation.group_plan_id}")
    print(f"Strategy: {result.strategy}")
    print(f"Status: {mutation.status}")
    if args.target_group_size is not None:
        print(f"Target group size: {args.target_group_size}")
    else:
        print(f"Target group count: {args.target_group_count}")
    print(f"Signal set: {result.signal_set_id}")
    print(f"Signal digest: {result.signal_set_digest}")
    print(f"Signal dimension: {result.dimension_id}")
    print(f"Generated groups: {result.group_count}")
    print(f"Assigned students: {result.assigned_student_count}")
    print(f"Unresolved students: {result.unresolved_student_count}")
    print(f"Group sizes: {','.join(str(size) for size in result.group_sizes)}")
    print("Canonical Groups created: no")


def handle_create_similar_signal(args: argparse.Namespace) -> int:
    return _handle_create_signal(args, "similar_signal")


def handle_create_mixed_signal(args: argparse.Namespace) -> int:
    return _handle_create_signal(args, "mixed_signal")


def _print_missing_signal_result(
    result: MissingSignalDispositionResult,
    *,
    strategy: str,
) -> None:
    print_commit(result.mutation.commit)
    print(f"GroupPlan: {result.mutation.group_plan_id}")
    print(f"Strategy: {strategy}")
    print(f"Status: {result.mutation.status}")
    print(f"Missing-signal disposition: {result.disposition}")
    print(f"Missing-signal students: {result.missing_student_count}")
    print(f"Assigned students: {result.assigned_student_count}")
    print(f"Unresolved students: {result.unresolved_student_count}")
    print(f"Group sizes: {','.join(str(size) for size in result.group_sizes)}")
    if result.random_seed is not None:
        print(f"Random seed: {result.random_seed}")
    print(f"Snapshot revision: {result.mutation.commit.snapshot_revision}")
    print("Canonical Groups created: no")


def _handle_missing_signal_disposition(
    args: argparse.Namespace,
    disposition: str,
) -> int:
    result = set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            disposition=disposition,
            random_seed=getattr(args, "seed", None),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    detail = show_group_plan(
        args.class_id,
        args.activity_id,
        args.group_plan_id,
        workspace_root=workspace_arg(args),
    )
    _print_missing_signal_result(result, strategy=detail.plan.strategy)
    return 0


def handle_confirm_missing_manual(args: argparse.Namespace) -> int:
    return _handle_missing_signal_disposition(args, "manual")


def handle_distribute_missing_random(args: argparse.Namespace) -> int:
    return _handle_missing_signal_disposition(args, "random")


def handle_leave_missing_unassigned(args: argparse.Namespace) -> int:
    return _handle_missing_signal_disposition(args, "leave_unassigned")


def handle_add_group(args: argparse.Namespace) -> int:
    result = add_planned_group(
        AddPlannedGroupRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            planned_group_key=args.planned_group_key,
            label=args.label,
            description=args.description,
            effective_context=(effective_context(args) if args.session_id else None),
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_edit(result)
    return 0


def handle_edit_group(args: argparse.Namespace) -> int:
    if args.clear_context and args.session_id:
        raise ValueError("--clear-context and --session-id are mutually exclusive.")
    if args.clear_description and args.description is not None:
        raise ValueError(
            "--clear-description and --description are mutually exclusive."
        )
    result = edit_planned_group(
        EditPlannedGroupRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            planned_group_key=args.planned_group_key,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            label=args.label,
            description=args.description,
            clear_description=args.clear_description,
            effective_context=(effective_context(args) if args.session_id else None),
            clear_effective_context=args.clear_context,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_edit(result)
    return 0


def handle_remove_group(args: argparse.Namespace) -> int:
    result = remove_planned_group(
        RemovePlannedGroupRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            planned_group_key=args.planned_group_key,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_edit(result)
    return 0


def handle_place_student(args: argparse.Namespace) -> int:
    result = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            student_id=args.student_id,
            planned_group_key=args.planned_group_key,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_edit(result)
    return 0


def handle_unassign_student(args: argparse.Namespace) -> int:
    result = unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            student_id=args.student_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_edit(result)
    return 0


def handle_refresh_roster(args: argparse.Namespace) -> int:
    result = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_edit(result)
    return 0


def _print_import_result(result: ArrangementImportResult) -> None:
    print_commit(result.mutation.commit)
    print(f"GroupPlan: {result.mutation.group_plan_id}")
    print(f"Status: {result.mutation.status}")
    print(f"Data rows: {result.data_row_count}")
    print(f"Proposed groups: {result.proposed_group_count}")
    print(f"Assigned students: {result.assigned_student_count}")
    print(f"Unresolved students: {result.unresolved_student_count}")


def handle_import_arrangement(args: argparse.Namespace) -> int:
    result = import_arrangement_group_plan(
        ImportArrangementGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            csv_path=args.csv_path,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_import_result(result)
    return 0


def handle_replace_arrangement(args: argparse.Namespace) -> int:
    result = replace_group_plan_from_arrangement(
        ReplaceArrangementGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            csv_path=args.csv_path,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_import_result(result)
    return 0


def _context_text(context: object) -> str:
    if context is None:
        return "none"
    session_ids = getattr(context, "session_ids")
    return ",".join(session_ids)


def _print_application_preview(preview: GroupPlanApplicationPreview) -> None:
    print(f"GroupPlan: {preview.group_plan_id}")
    print("Status: approved")
    print(f"GroupPlan record revision: {preview.group_plan_record_revision}")
    print(f"Expected Activity snapshot: {preview.expected_snapshot_revision}")
    print(f"Application ID: {preview.application_id}")
    print(f"Application digest: {preview.application_digest}")
    if preview.fallback_effective_context is not None:
        print(
            "Fallback Membership context: "
            f"{_context_text(preview.fallback_effective_context)}"
        )
    print(f"Canonical Groups to create: {preview.group_count}")
    print(f"Canonical Memberships to create: {preview.membership_count}")
    print(f"Students left without Membership: {preview.unresolved_count}")
    for group in preview.groups:
        print(
            f"Group: {group.planned_group_key} -> {group.group_id}; "
            f"label={group.label}; context={_context_text(group.effective_context)}"
        )
    for membership in preview.memberships:
        print(
            f"Membership: {membership.student_id} -> {membership.membership_id}; "
            f"group={membership.group_id}; "
            f"context={_context_text(membership.effective_context)}"
        )
    if preview.unresolved_student_ids:
        print(
            "No-Membership student IDs: "
            + ",".join(preview.unresolved_student_ids)
        )
        print(
            "These roster students will receive no GroupMembership from this "
            "application."
        )
    print("No changes have been written.")
    print(
        "Use this Application ID, digest, expected snapshot, and fallback context "
        "with group-plan apply."
    )


def handle_application_preview(args: argparse.Namespace) -> int:
    fallback = effective_context(args) if args.session_id else None
    preview = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            application_id=args.application_id,
            fallback_effective_context=fallback,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    _print_application_preview(preview)
    return 0


def handle_apply(args: argparse.Namespace) -> int:
    fallback = effective_context(args) if args.session_id else None
    result = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            application_id=args.application_id,
            application_digest=args.application_digest,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
            fallback_effective_context=fallback,
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"GroupPlan: {result.group_plan_id}")
    print(f"Status: {result.status}")
    print(f"Application ID: {result.application_id}")
    print(f"Application digest: {result.application_digest}")
    print(f"Groups created: {result.group_count}")
    print(f"Memberships created: {result.membership_count}")
    print(f"Students left unresolved: {result.unresolved_count}")
    return 0


def handle_preview(args: argparse.Namespace) -> int:
    detail = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print("Persisted exact GroupPlan preview.")
    _print_detail(detail)
    return 0


def handle_approve(args: argparse.Namespace) -> int:
    result = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"GroupPlan: {result.group_plan_id}")
    print(f"Status: {result.status}")
    print("Canonical Groups created: no")
    return 0


def handle_cancel(args: argparse.Namespace) -> int:
    result = cancel_group_plan(
        CancelGroupPlanRequest(
            class_id=args.class_id,
            activity_id=args.activity_id,
            group_plan_id=args.group_plan_id,
            expected_snapshot_revision=args.expected_snapshot,
            actor=workflow_actor(args),
        ),
        workspace_root=workspace_arg(args),
        standards_library=load_command_standards_library(args),
    )
    print_commit(result.commit)
    print(f"GroupPlan: {result.group_plan_id}")
    print(f"Status: {result.status}")
    return 0
