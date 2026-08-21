"""Teacher-facing GroupPlan authoring for one Concord Activity."""

from __future__ import annotations

from pathlib import Path

from pds_core.workspace import resolve_workspace_root

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_group_plan_signal import create_signal_group_plan_from_menu
from concord.menu_grouping_signal import launch_grouping_signal_menu
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    choose_student,
    confirm_write,
    handle_write_error,
    prompt_exact_text,
    prompt_positive_int,
    prompt_text,
    select_one,
    show_result,
    slug_identifier,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import PlannedGroup
from concord.workflows import (
    ActivitySummary,
    AddPlannedGroupRequest,
    ApproveGroupPlanRequest,
    CancelGroupPlanRequest,
    ConcordWorkflowError,
    CreateManualGroupPlanRequest,
    CreateRandomGroupPlanRequest,
    EditPlannedGroupRequest,
    GroupPlanDetail,
    GroupPlanSummary,
    ImportArrangementGroupPlanRequest,
    PlaceStudentInPlanRequest,
    PreviewGroupPlanRequest,
    RefreshGroupPlanRosterRequest,
    RemovePlannedGroupRequest,
    ReplaceArrangementGroupPlanRequest,
    UnassignStudentFromPlanRequest,
    add_planned_group,
    approve_group_plan,
    cancel_group_plan,
    create_manual_group_plan,
    create_random_group_plan,
    edit_planned_group,
    import_arrangement_group_plan,
    list_group_plans,
    place_student_in_plan,
    preview_group_plan,
    refresh_group_plan_roster,
    remove_planned_group,
    replace_group_plan_from_arrangement,
    show_activity,
    show_group_plan,
    unassign_student_from_plan,
)


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _handle_error(activity: ActivitySummary, title: str, error: Exception) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title=title,
    )


def _select_plan(activity: ActivitySummary, *, title: str) -> GroupPlanSummary:
    plans = list_group_plans(activity.class_id, activity.activity_id)
    return select_one(
        title,
        plans,
        [
            (
                f"{item.group_plan_id} - {item.status}; {item.strategy}; "
                f"groups: {item.proposed_group_count}; "
                f"unresolved: {item.unresolved_student_count}"
            )
            for item in plans
        ],
        help_text=(
            "GroupPlans are teacher-controlled proposals. They do not create canonical "
            "Groups or Memberships until a later explicit application workflow."
        ),
    )


def _select_planned_group(detail: GroupPlanDetail, *, title: str) -> PlannedGroup:
    return select_one(
        title,
        detail.plan.proposed_groups,
        [
            (
                f"{item.label} ({item.planned_group_key}) - "
                f"students: {len(item.student_ids)}"
            )
            for item in detail.plan.proposed_groups
        ],
        help_text=(
            "Choose a plan-local group. Its planned_group_key is not a canonical "
            "Group ID."
        ),
    )


def _show_detail(detail: GroupPlanDetail) -> None:
    plan = detail.plan
    clear_screen()
    print_menu_header("GroupPlan")
    print(f"GroupPlan: {plan.group_plan_id}")
    print(f"Strategy: {plan.strategy}")
    print(f"Status: {plan.status}")
    print(f"Snapshot: {detail.summary.snapshot_revision}")
    print(f"Record revision: {detail.record_revision}")
    print(f"Planned groups: {len(plan.proposed_groups)}")
    print(f"Unresolved students: {len(plan.unresolved_student_ids)}")
    if plan.target_group_size is not None:
        print(f"Target group size: {plan.target_group_size}")
    if plan.target_group_count is not None:
        print(f"Target group count: {plan.target_group_count}")
    if plan.seed is not None:
        print(f"Seed: {plan.seed}")
    if plan.source_signal_set_id is not None:
        print(f"Signal set: {plan.source_signal_set_id}")
        print(f"Core signal digest: {plan.source_signal_set_digest}")
        print(f"Signal dimension: {plan.source_signal_dimension_id}")
    print()
    for group in plan.proposed_groups:
        print(
            f"{group.label} ({group.planned_group_key}) - "
            f"students: {', '.join(group.student_ids) or '-'}"
        )
    if plan.unresolved_student_ids:
        print()
        print(f"Unresolved IDs: {', '.join(plan.unresolved_student_ids)}")
    print()
    print("Approval does not create canonical Groups or Memberships.")
    print()
    pause_for_user()


def _list_plans(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("GroupPlans")
    try:
        plans = list_group_plans(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"GroupPlans could not be loaded: {error}")
    else:
        if not plans:
            print("No GroupPlans are available.")
        for item in plans:
            print(
                f"{item.group_plan_id} - {item.status}; {item.strategy}; "
                f"groups: {item.proposed_group_count}; "
                f"assigned: {item.assigned_student_count}; "
                f"unresolved: {item.unresolved_student_count}"
            )
    print()
    pause_for_user()


def _create_manual(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        plan_id = prompt_text(
            "Create Manual GroupPlan",
            "GroupPlan ID",
            help_text="Use a durable identifier for this planning proposal.",
            default=slug_identifier(f"{current.activity_id}-group-plan", "group-plan"),
        )
        assert plan_id is not None
        if not confirm_write(
            "Create Manual GroupPlan",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"GroupPlan: {plan_id}",
                "All roster students begin unresolved.",
                "No canonical Groups or Memberships will be created.",
            ),
        ):
            return
        result = create_manual_group_plan(
            CreateManualGroupPlanRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                group_plan_id=plan_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            )
        )
        show_result(
            "GroupPlan Result",
            (
                "Manual GroupPlan created.",
                f"GroupPlan: {result.group_plan_id}",
                f"Status: {result.status}",
                f"Snapshot: {result.commit.snapshot_revision}",
                "Canonical Groups created: no",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "GroupPlan Error", error)


def _create_random(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        plan_id = prompt_text(
            "Create Random GroupPlan",
            "GroupPlan ID",
            help_text="Use a durable identifier for this planning proposal.",
            default=slug_identifier(f"{current.activity_id}-random", "group-plan"),
        )
        assert plan_id is not None
        target_kind = select_one(
            "Random Group Target",
            ("size", "count"),
            ("Target group size", "Target group count"),
            help_text=(
                "Choose whether Concord should derive the group count from a maximum "
                "target size or create an exact requested number of groups."
            ),
        )
        if target_kind == "size":
            target_group_size = prompt_positive_int(
                "Create Random GroupPlan",
                "Target group size",
                help_text=(
                    "Concord will use ceil(roster size / target size) groups and "
                    "balance their sizes as evenly as possible."
                ),
                default=4,
            )
            target_group_count = None
            target_line = f"Target group size: {target_group_size}"
        else:
            target_group_count = prompt_positive_int(
                "Create Random GroupPlan",
                "Target group count",
                help_text=(
                    "Concord will create exactly this many nonempty groups; the count "
                    "cannot exceed the current roster size."
                ),
                default=4,
            )
            target_group_size = None
            target_line = f"Target group count: {target_group_count}"
        seed = prompt_exact_text(
            "Create Random GroupPlan",
            "Seed",
            help_text=(
                "Enter an explicit reproducibility seed. Leading or trailing "
                "whitespace is invalid and will be rejected rather than trimmed. "
                "The same exact roster, target, and seed reproduce the same v0.3 "
                "arrangement."
            ),
        )
        assert seed is not None
        if not confirm_write(
            "Create Random GroupPlan",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"GroupPlan: {plan_id}",
                target_line,
                f"Seed: {seed}",
                "The current Core roster will be assigned exactly once.",
                "This is a deterministic random proposal, not an optimized grouping.",
                "No canonical Groups or Memberships will be created.",
            ),
        ):
            return
        result = create_random_group_plan(
            CreateRandomGroupPlanRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                group_plan_id=plan_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
                seed=seed,
                target_group_size=target_group_size,
                target_group_count=target_group_count,
            )
        )
        mutation = result.mutation
        show_result(
            "GroupPlan Result",
            (
                "Random GroupPlan created.",
                f"GroupPlan: {mutation.group_plan_id}",
                "Strategy: random",
                f"Status: {mutation.status}",
                target_line,
                f"Seed: {seed}",
                f"Generated groups: {result.group_count}",
                f"Assigned students: {result.assigned_student_count}",
                "Unresolved students: 0",
                f"Group sizes: {','.join(str(size) for size in result.group_sizes)}",
                f"Snapshot: {mutation.commit.snapshot_revision}",
                "Canonical Groups created: no",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "GroupPlan Error", error)


def _import_arrangement(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        plan_id = prompt_text(
            "Import Arrangement",
            "GroupPlan ID",
            help_text="Use a durable identifier for the imported planning proposal.",
            default=slug_identifier(f"{current.activity_id}-arrangement", "group-plan"),
        )
        assert plan_id is not None
        raw_path = prompt_text(
            "Import Arrangement",
            "CSV path",
            help_text="Choose a UTF-8 CSV with the exact header student_id,group.",
        )
        assert raw_path is not None
        if not confirm_write(
            "Import Arrangement",
            "IMPORT",
            (
                f"Activity: {current.title}",
                f"GroupPlan: {plan_id}",
                "The CSV will be validated completely before any write.",
                "Import does not create canonical Groups or Memberships.",
            ),
        ):
            return
        result = import_arrangement_group_plan(
            ImportArrangementGroupPlanRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                group_plan_id=plan_id,
                csv_path=Path(raw_path),
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
            )
        )
        show_result(
            "Arrangement Import Result",
            (
                f"GroupPlan: {result.mutation.group_plan_id}",
                f"Rows: {result.data_row_count}",
                f"Planned groups: {result.proposed_group_count}",
                f"Assigned students: {result.assigned_student_count}",
                f"Unresolved students: {result.unresolved_student_count}",
                f"Snapshot: {result.mutation.commit.snapshot_revision}",
                "Canonical Groups created: no",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "Arrangement Import Error", error)


def _add_group(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    label = prompt_text(
        "Add Planned Group",
        "Label",
        help_text="Use the teacher-facing label for this plan-local group.",
    )
    assert label is not None
    group_key = prompt_text(
        "Add Planned Group",
        "Planned group key",
        help_text="This plan-local key is not a canonical Group ID.",
        default=slug_identifier(label, "planned-group"),
    )
    assert group_key is not None
    description = prompt_text(
        "Add Planned Group",
        "Description",
        help_text="Optional short description for this planned group.",
        optional=True,
    )
    if not confirm_write(
        "Add Planned Group",
        "ADD",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            f"Planned group: {label} ({group_key})",
        ),
    ):
        return
    result = add_planned_group(
        AddPlannedGroupRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            planned_group_key=group_key,
            label=label,
            description=description,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            "Planned group added." if result.changed else "No changes were needed.",
            f"Status: {result.detail.plan.status}",
            f"Snapshot: {result.detail.summary.snapshot_revision}",
        ),
    )


def _edit_group(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    group = _select_planned_group(detail, title="Edit a Planned Group")
    label = prompt_text(
        "Edit Planned Group",
        "Label",
        help_text="Change the teacher-facing label; the plan-local key stays stable.",
        default=group.label,
    )
    assert label is not None
    description = prompt_text(
        "Edit Planned Group",
        "Description",
        help_text=(
            "Optional short description; leave blank to preserve the current value."
        ),
        optional=True,
    )
    if not confirm_write(
        "Edit Planned Group",
        "UPDATE",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            f"Planned group key: {group.planned_group_key}",
            f"Label: {label}",
        ),
    ):
        return
    result = edit_planned_group(
        EditPlannedGroupRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            planned_group_key=group.planned_group_key,
            label=label,
            description=description,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            "Planned group updated." if result.changed else "No changes were needed.",
            f"Status: {result.detail.plan.status}",
            f"Snapshot: {result.detail.summary.snapshot_revision}",
        ),
    )


def _remove_group(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    group = _select_planned_group(detail, title="Remove a Planned Group")
    if not confirm_write(
        "Remove Planned Group",
        "REMOVE",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            f"Planned group: {group.label}",
            f"Students becoming unresolved: {len(group.student_ids)}",
        ),
    ):
        return
    result = remove_planned_group(
        RemovePlannedGroupRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            planned_group_key=group.planned_group_key,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            "Planned group removed." if result.changed else "No changes were needed.",
            f"Unresolved students: {result.detail.summary.unresolved_student_count}",
            f"Snapshot: {result.detail.summary.snapshot_revision}",
        ),
    )


def _planned_group_menu(
    activity: ActivitySummary,
    plan_id: str,
    state: MenuSessionContext,
) -> None:
    while True:
        detail = show_group_plan(activity.class_id, activity.activity_id, plan_id)
        clear_screen()
        print_menu_header("Planned Groups")
        print(f"GroupPlan: {plan_id}")
        print(f"Status: {detail.plan.status}")
        print()
        print("1. Add a planned group")
        print("2. Edit a planned group")
        print("3. Remove a planned group")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Planned Groups Help")
            print("These groups exist only inside the GroupPlan proposal.")
            print(
                "Removing one makes its students unresolved rather than deleting them."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        else:
            try:
                if choice == "1":
                    _add_group(detail, state)
                elif choice == "2":
                    _edit_group(detail, state)
                elif choice == "3":
                    _remove_group(detail, state)
                else:
                    print(navigation_hint_with_help())
                    pause_for_user()
            except CancelMenuAction:
                continue
            except Exception as error:
                _handle_error(activity, "GroupPlan Error", error)


def _place_student(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    root = resolve_workspace_root()
    student = choose_student(root, detail.summary.class_id)
    group = _select_planned_group(detail, title="Choose a Planned Group")
    if not confirm_write(
        "Place Student",
        "PLACE",
        (
            f"Student: {student.first_name} {student.last_name} ({student.student_id})",
            f"Planned group: {group.label}",
            "This changes only the GroupPlan proposal.",
        ),
    ):
        return
    result = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            student_id=student.student_id,
            planned_group_key=group.planned_group_key,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            "Student placement saved." if result.changed else "No changes were needed.",
            f"Unresolved students: {result.detail.summary.unresolved_student_count}",
            f"Snapshot: {result.detail.summary.snapshot_revision}",
        ),
    )


def _unassign_student(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    root = resolve_workspace_root()
    student = choose_student(root, detail.summary.class_id)
    if not confirm_write(
        "Unassign Student",
        "UNASSIGN",
        (
            f"Student: {student.first_name} {student.last_name} ({student.student_id})",
            "The student will remain in the GroupPlan as unresolved.",
        ),
    ):
        return
    result = unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            student_id=student.student_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            "Student unassigned." if result.changed else "No changes were needed.",
            f"Unresolved students: {result.detail.summary.unresolved_student_count}",
            f"Snapshot: {result.detail.summary.snapshot_revision}",
        ),
    )


def _refresh_roster(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    if not confirm_write(
        "Refresh GroupPlan Roster",
        "REFRESH",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            "Departed students will be removed from the proposal.",
            "New roster students will be added as unresolved.",
        ),
    ):
        return
    result = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            "Roster refreshed." if result.changed else "Roster was already current.",
            f"Unresolved students: {result.detail.summary.unresolved_student_count}",
            f"Snapshot: {result.detail.summary.snapshot_revision}",
        ),
    )


def _replace_arrangement(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    raw_path = prompt_text(
        "Replace from Arrangement",
        "CSV path",
        help_text="Choose a UTF-8 CSV with the exact header student_id,group.",
    )
    assert raw_path is not None
    if not confirm_write(
        "Replace from Arrangement",
        "REPLACE",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            "The complete proposal will be replaced only after full CSV validation.",
            "The GroupPlan identity and revision history will be preserved.",
        ),
    ):
        return
    result = replace_group_plan_from_arrangement(
        ReplaceArrangementGroupPlanRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            csv_path=Path(raw_path),
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Arrangement Replacement Result",
        (
            f"Rows: {result.data_row_count}",
            f"Planned groups: {result.proposed_group_count}",
            f"Assigned students: {result.assigned_student_count}",
            f"Unresolved students: {result.unresolved_student_count}",
            f"Snapshot: {result.mutation.commit.snapshot_revision}",
        ),
    )


def _preview(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    if not confirm_write(
        "Preview GroupPlan",
        "PREVIEW",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            f"Unresolved students: {detail.summary.unresolved_student_count}",
            "Preview does not create canonical Groups or Memberships.",
        ),
    ):
        return
    result = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Preview",
        (
            f"Status: {result.plan.status}",
            f"Snapshot: {result.summary.snapshot_revision}",
            "Canonical Groups created: no",
        ),
    )


def _approve(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    if not confirm_write(
        "Approve GroupPlan",
        "APPROVE",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            "Every roster student must already be resolved.",
            "Approval freezes this proposal but does not apply it.",
            "Canonical Groups created: no",
        ),
    ):
        return
    result = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Approval",
        (
            f"Status: {result.status}",
            f"Snapshot: {result.commit.snapshot_revision}",
            "Canonical Groups created: no",
            "Application remains a separate later workflow.",
        ),
    )


def _cancel(detail: GroupPlanDetail, state: MenuSessionContext) -> None:
    if not confirm_write(
        "Cancel GroupPlan",
        "CANCEL",
        (
            f"GroupPlan: {detail.plan.group_plan_id}",
            "Cancellation is terminal and preserves GroupPlan history.",
        ),
    ):
        return
    result = cancel_group_plan(
        CancelGroupPlanRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "GroupPlan Result",
        (
            f"Status: {result.status}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _open_plan(
    activity: ActivitySummary,
    selected: GroupPlanSummary,
    state: MenuSessionContext,
) -> None:
    while True:
        detail = show_group_plan(
            selected.class_id,
            selected.activity_id,
            selected.group_plan_id,
        )
        clear_screen()
        print_menu_header("Plan Groups")
        print(f"GroupPlan: {detail.plan.group_plan_id}")
        print(f"Strategy: {detail.plan.strategy}")
        print(f"Status: {detail.plan.status}")
        print(f"Unresolved: {detail.summary.unresolved_student_count}")
        print()
        print("1. View GroupPlan")
        print("2. Edit planned groups")
        print("3. Place or move a student")
        print("4. Unassign a student")
        print("5. Refresh roster")
        print("6. Replace from arrangement CSV")
        print("7. Preview")
        print("8. Approve")
        print("9. Cancel")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("GroupPlan Help")
            print("A GroupPlan is a proposal, not canonical classroom Group state.")
            print("Editing a previewed plan returns it to draft.")
            print("Approval does not apply the plan; application belongs to issue #56.")
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        else:
            try:
                if choice == "1":
                    _show_detail(detail)
                elif choice == "2":
                    _planned_group_menu(activity, selected.group_plan_id, state)
                elif choice == "3":
                    _place_student(detail, state)
                elif choice == "4":
                    _unassign_student(detail, state)
                elif choice == "5":
                    _refresh_roster(detail, state)
                elif choice == "6":
                    _replace_arrangement(detail, state)
                elif choice == "7":
                    _preview(detail, state)
                elif choice == "8":
                    _approve(detail, state)
                elif choice == "9":
                    _cancel(detail, state)
                else:
                    print(navigation_hint_with_help())
                    pause_for_user()
            except CancelMenuAction:
                continue
            except Exception as error:
                _handle_error(activity, "GroupPlan Error", error)


def launch_group_plan_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Manage teacher-controlled GroupPlan proposals for one Activity."""
    while True:
        current = _latest(activity)
        clear_screen()
        print_menu_header("Plan Groups")
        print(f"Activity: {current.title}")
        print()
        print("1. List GroupPlans")
        print("2. Create a manual GroupPlan")
        print("3. Create a random GroupPlan")
        print("4. Import an arrangement CSV")
        print("5. Grouping signals")
        print("6. Open a GroupPlan")
        print("7. Create similar-signal plan")
        print("8. Create mixed-signal plan")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Plan Groups Help")
            print("GroupPlans are editable proposals for later teacher approval.")
            print("They remain separate from canonical Groups and Memberships.")
            print("Direct Group management remains available from the previous menu.")
            print(
                "Signal-backed plans require explicit signal and dimension "
                "selection and never assign academic meaning to ordinal bands."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _list_plans(current)
        elif choice == "2":
            _create_manual(current, state)
        elif choice == "3":
            _create_random(current, state)
        elif choice == "4":
            _import_arrangement(current, state)
        elif choice == "5":
            launch_grouping_signal_menu(current)
        elif choice == "6":
            try:
                selected = _select_plan(current, title="Open a GroupPlan")
                _open_plan(current, selected, state)
            except CancelMenuAction:
                continue
            except Exception as error:
                show_result("GroupPlan Error", (str(error),))
        elif choice == "7":
            create_signal_group_plan_from_menu(current, state, "similar_signal")
        elif choice == "8":
            create_signal_group_plan_from_menu(current, state, "mixed_signal")
        else:
            print(navigation_hint_with_help())
            pause_for_user()
