"""Teacher-facing Group and Membership workflows for one Concord Activity."""

from __future__ import annotations

import uuid

from pds_core.workspace import resolve_workspace_root

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_group_plan import launch_group_plan_menu
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    choose_effective_context,
    choose_group,
    choose_membership,
    choose_students,
    confirm_write,
    handle_write_error,
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
from concord.models import EffectiveContext
from concord.workflows import (
    ActivitySummary,
    AddMembershipsRequest,
    ConcordWorkflowError,
    CreateGroupRequest,
    EndMembershipRequest,
    GroupMemberSpec,
    GroupSummary,
    ReassignMembershipRequest,
    UpdateGroupRequest,
    add_memberships,
    create_group,
    end_membership,
    list_groups,
    list_memberships,
    list_sessions,
    reassign_membership,
    show_activity,
    show_group,
    update_group,
)


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _handle_error(
    activity: ActivitySummary,
    title: str,
    error: Exception,
) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title=title,
    )


def _list_groups(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Groups")
    try:
        groups = list_groups(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"Groups could not be loaded: {error}")
    else:
        if not groups:
            print("No Groups are available.")
        for item in groups:
            print(
                f"{item.label} ({item.group_id}) - {item.status}; "
                f"members: {item.member_count}"
            )
    print()
    pause_for_user()


def _create_group(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        label = prompt_text(
            "Create Group",
            "Group label",
            help_text="Use the classroom-facing name for this Activity-specific Group.",
        )
        assert label is not None
        proposed = slug_identifier(label, "group")
        group_id = prompt_text(
            "Create Group",
            "Group ID",
            help_text="The Group ID is durable and distinct from the display label.",
            default=proposed,
        )
        assert group_id is not None
        description = prompt_text(
            "Create Group",
            "Description",
            help_text="Optional short description of the Group's purpose.",
            optional=True,
        )
        actor = state.require_actor()
        if not confirm_write(
            "Create Group",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"Group: {label}",
                f"Group ID: {group_id}",
                "Status: planned",
            ),
        ):
            return
        result = create_group(
            CreateGroupRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                group_id=group_id,
                label=label,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                description=description,
            )
        )
        show_result(
            "Group Result",
            (
                (
                    "Group saved."
                    if not result.commit.no_op
                    else "No changes were needed."
                ),
                f"Group: {result.group_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "Group Error", error)


def _choose_parent_group(
    activity: ActivitySummary,
    current_group_id: str,
) -> str | None:
    groups = tuple(
        item
        for item in list_groups(activity.class_id, activity.activity_id)
        if item.group_id != current_group_id
    )
    options: tuple[GroupSummary | None, ...] = (None, *groups)
    labels = ("No parent Group",) + tuple(
        f"{item.label} ({item.group_id})" for item in groups
    )
    selected = select_one(
        "Choose Parent Group",
        options,
        labels,
        help_text=(
            "A parent must belong to this Activity. Concord rejects parent cycles."
        ),
    )
    if selected is None:
        return None
    return selected.group_id


def _choose_group_context(
    activity: ActivitySummary,
) -> EffectiveContext | None:
    while True:
        clear_screen()
        print_menu_header("Group Effective Context")
        print("1. Set Session context")
        print("2. Clear Session context")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Group Context Help")
            print("A Group context limits when its contextual assignments may apply.")
            print("Leave it unset when the Group is valid across the Activity.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if choice == "1":
            sessions = list_sessions(activity.class_id, activity.activity_id)
            return choose_effective_context(activity.activity_id, sessions)
        if choice == "2":
            return None
        print(navigation_hint_with_help())
        pause_for_user()


def _edit_group(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        groups = list_groups(activity.class_id, activity.activity_id)
        selected = choose_group(groups, title="Edit a Group")
        detail = show_group(activity.class_id, activity.activity_id, selected.group_id)
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "Group Error", error)
        return
    while True:
        clear_screen()
        print_menu_header("Edit Group")
        print(f"Group: {selected.label}")
        print()
        print("1. Label")
        print("2. Description")
        print("3. Status")
        print("4. Parent Group")
        print("5. Effective Session context")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Group Help")
            print("Group revision preserves the same durable Group identity.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        try:
            current = _latest(activity)
            values: dict[str, object] = {
                "class_id": current.class_id,
                "activity_id": current.activity_id,
                "group_id": selected.group_id,
                "expected_snapshot_revision": current.snapshot_revision,
                "actor": state.require_actor(),
            }
            change_label = ""
            if choice == "1":
                value = prompt_text(
                    "Edit Group",
                    "Label",
                    help_text="Change only the teacher-facing Group label.",
                    default=selected.label,
                )
                assert value is not None
                values["label"] = value
                change_label = "Label"
            elif choice == "2":
                values["description"] = prompt_text(
                    "Edit Group",
                    "Description",
                    help_text="Change or add a short Group description.",
                    default=detail.description,
                    optional=True,
                )
                change_label = "Description"
            elif choice == "3":
                value = prompt_text(
                    "Edit Group",
                    "Status",
                    help_text=(
                        "Valid statuses include planned, active, inactive, completed, "
                        "cancelled, archived, and superseded."
                    ),
                    default=selected.status,
                )
                assert value is not None
                values["status"] = value
                change_label = "Status"
            elif choice == "4":
                values["parent_group_id"] = _choose_parent_group(
                    current, selected.group_id
                )
                change_label = "Parent Group"
            elif choice == "5":
                values["effective_context"] = _choose_group_context(current)
                change_label = "Effective Session context"
            else:
                print(navigation_hint_with_help())
                pause_for_user()
                continue
            if not confirm_write(
                "Edit Group",
                "UPDATE",
                (f"Group: {selected.label}", f"Change: {change_label}"),
            ):
                return
            result = update_group(
                UpdateGroupRequest(**values)  # type: ignore[arg-type]
            )
            show_result(
                "Group Result",
                (
                    (
                    "Group saved."
                    if not result.commit.no_op
                    else "No changes were needed."
                ),
                    f"Group: {result.group_id}",
                    f"Snapshot: {result.commit.snapshot_revision}",
                ),
            )
            return
        except CancelMenuAction:
            return
        except Exception as error:
            _handle_error(activity, "Group Error", error)
            return


def _list_members(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Group Memberships")
    try:
        items = list_memberships(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"Memberships could not be loaded: {error}")
    else:
        if not items:
            print("No Memberships are available.")
        for item in items:
            label = (
                item.participant_display_label
                or item.participant_reference.participant_id
            )
            print(f"{label} -> {item.group_id} - {item.status}")
    print()
    pause_for_user()


def _add_member(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        groups = list_groups(current.class_id, current.activity_id)
        group = choose_group(groups, title="Choose a Group")
        sessions = list_sessions(current.class_id, current.activity_id)
        context = choose_effective_context(current.activity_id, sessions)
        root = resolve_workspace_root()
        students = choose_students(root, current.class_id)
        actor = state.require_actor()
        members = tuple(
            GroupMemberSpec(
                membership_id=f"membership-{uuid.uuid4().hex}",
                student_id=student.student_id,
                effective_context=context,
            )
            for student in students
        )
        if not confirm_write(
            "Add Group Members",
            "ADD",
            (
                f"Group: {group.label}",
                f"Students: {len(students)}",
                f"Sessions: {len(context.session_ids)}",
            ),
        ):
            return
        result = add_memberships(
            AddMembershipsRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                group_id=group.group_id,
                members=members,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
            )
        )
        show_result(
            "Membership Result",
            (
                f"Memberships added: {len(result.membership_ids)}",
                f"Group: {group.group_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "Membership Error", error)


def _end_member(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        memberships = list_memberships(current.class_id, current.activity_id)
        active = tuple(
            item for item in memberships if item.status in {"planned", "active"}
        )
        membership = choose_membership(active, title="End a Membership")
        status = prompt_text(
            "End Membership",
            "End status",
            help_text="Use completed, withdrawn, or cancelled.",
            default="completed",
        )
        assert status is not None
        actor = state.require_actor()
        if not confirm_write(
            "End Membership",
            "END",
            (
                f"Membership: {membership.membership_id}",
                (
                    "Student: "
                    + (
                        membership.participant_display_label
                        or membership.participant_reference.participant_id
                    )
                ),
                f"Status: {status}",
            ),
        ):
            return
        result = end_membership(
            EndMembershipRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                membership_id=membership.membership_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                status=status,
            )
        )
        show_result(
            "Membership Result",
            (
                "Membership ended.",
                f"Membership: {result.membership_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "Membership Error", error)


def _reassign_member(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        memberships = list_memberships(current.class_id, current.activity_id)
        active = tuple(
            item for item in memberships if item.status in {"planned", "active"}
        )
        membership = choose_membership(active, title="Reassign a Membership")
        groups = tuple(
            item
            for item in list_groups(current.class_id, current.activity_id)
            if item.group_id != membership.group_id
        )
        new_group = choose_group(groups, title="Choose the New Group")
        sessions = list_sessions(current.class_id, current.activity_id)
        context = choose_effective_context(current.activity_id, sessions)
        actor = state.require_actor()
        successor_id = f"membership-{uuid.uuid4().hex}"
        if not confirm_write(
            "Reassign Membership",
            "REASSIGN",
            (
                (
                    "Student: "
                    + (
                        membership.participant_display_label
                        or membership.participant_reference.participant_id
                    )
                ),
                f"From: {membership.group_id}",
                f"To: {new_group.label}",
            ),
        ):
            return
        result = reassign_membership(
            ReassignMembershipRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                membership_id=membership.membership_id,
                successor_membership_id=successor_id,
                new_group_id=new_group.group_id,
                effective_context=context,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
            )
        )
        show_result(
            "Membership Result",
            (
                "Membership reassigned.",
                f"New Membership: {result.membership_id}",
                f"Previous Membership: {result.predecessor_membership_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, "Membership Error", error)


def launch_direct_group_menu(
    activity: ActivitySummary, state: MenuSessionContext
) -> None:
    """Manage canonical Activity-specific Groups and Memberships."""
    while True:
        clear_screen()
        print_menu_header("Groups and Participants")
        print(f"Activity: {activity.title}")
        print()
        print("1. List Groups")
        print("2. Create a Group")
        print("3. Edit a Group")
        print("4. List Memberships")
        print("5. Add Members")
        print("6. End a Membership")
        print("7. Reassign a Membership")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Group Help")
            print(
                "Groups are Activity-specific; students remain Core roster identities."
            )
            print("Membership changes preserve earlier contextual history.")
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _list_groups(activity)
        elif choice == "2":
            _create_group(activity, state)
        elif choice == "3":
            _edit_group(activity, state)
        elif choice == "4":
            _list_members(activity)
        elif choice == "5":
            _add_member(activity, state)
        elif choice == "6":
            _end_member(activity, state)
        elif choice == "7":
            _reassign_member(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def launch_group_menu(activity: ActivitySummary, state: MenuSessionContext) -> None:
    """Choose planning proposals or direct canonical Group management."""
    while True:
        clear_screen()
        print_menu_header("Groups and Participants")
        print(f"Activity: {activity.title}")
        print()
        print("1. Plan groups")
        print("2. Manage Groups and Memberships")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Groups and Participants Help")
            print("Plan groups creates or edits GroupPlan proposals.")
            print(
                "Manage Groups and Memberships edits canonical classroom "
                "Group state directly."
            )
            print(
                "A GroupPlan never becomes canonical Group state merely by "
                "preview or approval."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            launch_group_plan_menu(activity, state)
        elif choice == "2":
            launch_direct_group_menu(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()
