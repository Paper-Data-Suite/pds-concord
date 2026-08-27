"""Teacher-facing Role Assignment workflows for one Concord Activity."""

from __future__ import annotations

import uuid

from pds_core.workspace import resolve_workspace_root

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    choose_effective_context,
    choose_group,
    choose_student,
    confirm_write,
    handle_write_error,
    prompt_text,
    select_one,
    show_result,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.workflows import (
    ActivitySummary,
    ApplyRolePresetRequest,
    AssignRoleRequest,
    ConcordWorkflowError,
    EndRoleRequest,
    PresetSummary,
    ReassignRoleRequest,
    RoleSummary,
    SaveRolePresetFromAssignmentRequest,
    apply_role_preset,
    assign_role,
    core_student_participant,
    end_role,
    list_groups,
    list_presets,
    list_roles,
    list_sessions,
    prepare_role_preset_application,
    prepare_role_preset_from_assignment,
    reassign_role,
    save_role_preset_from_assignment,
    show_activity,
)

_ROLE_KEYS = (
    "facilitator",
    "recorder",
    "observer",
    "speaker",
    "researcher",
    "builder",
    "presenter",
)


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _handle_error(activity: ActivitySummary, error: Exception) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title="Role Error",
    )


def _choose_role_key() -> str:
    while True:
        clear_screen()
        print_menu_header("Choose a Role")
        for index, key in enumerate(_ROLE_KEYS, start=1):
            print(f"{index}. {key.replace('_', ' ').title()}")
        print("8. Custom namespaced role")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Role Help")
            print("Roles describe assignments, not proof of performance or authorship.")
            print("Custom roles must use the model's namespaced extension syntax.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(_ROLE_KEYS):
                return _ROLE_KEYS[index - 1]
            if index == len(_ROLE_KEYS) + 1:
                custom = prompt_text(
                    "Custom Role",
                    "Role key",
                    help_text="Enter a valid namespace-qualified role key.",
                )
                assert custom is not None
                return custom
        print(navigation_hint_with_help())
        pause_for_user()


def _list(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Roles")
    try:
        items = list_roles(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"Roles could not be loaded: {error}")
    else:
        if not items:
            print("No Role Assignments are available.")
        for item in items:
            label = (
                item.participant_display_label
                or item.participant_reference.participant_id
            )
            group = f" / {item.group_id}" if item.group_id else ""
            print(f"{label}: {item.role_key}{group} - {item.status}")
    print()
    pause_for_user()


def _choose_existing(items: tuple[RoleSummary, ...], title: str) -> RoleSummary:
    return select_one(
        title,
        items,
        [
            (
                item.participant_display_label
                or item.participant_reference.participant_id
            )
            + f": {item.role_key} - {item.status}"
            for item in items
        ],
        help_text="Choose the Role Assignment whose lifecycle you want to change.",
    )


def _choose_optional_group(activity: ActivitySummary) -> str | None:
    groups = list_groups(activity.class_id, activity.activity_id)
    if not groups:
        return None
    clear_screen()
    print_menu_header("Role Group")
    print("1. No Group")
    print("2. Choose a Group")
    print_navigation()
    print()
    raw = input("Select an option: ").strip()
    navigation = parse_menu_navigation(raw)
    if navigation is ConcordMenuChoice.HELP:
        clear_screen()
        print_menu_header("Role Group Help")
        print("A Role may be Activity-wide or associated with one Group.")
        print()
        pause_for_user()
        return _choose_optional_group(activity)
    if navigation is NavigationChoice.BACK:
        raise CancelMenuAction
    if raw == "1":
        return None
    if raw == "2":
        return choose_group(groups, title="Choose a Role Group").group_id
    print(navigation_hint_with_help())
    pause_for_user()
    return _choose_optional_group(activity)



def _choose_role_preset() -> PresetSummary | None:
    presets = list_presets("role")
    if not presets:
        return None
    while True:
        clear_screen()
        print_menu_header("Role Source")
        print("1. Use a saved Role")
        print("2. Enter Role manually")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Saved Role Help",
                (
                    "Saved Roles reuse the Role definition only.",
                    "Student, Group, context, identity, and history are always fresh.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            return select_one(
                "Choose a Saved Role",
                presets,
                tuple(item.name for item in presets),
                help_text="Choose the Role definition; assignment state is new.",
            )
        if raw == "2":
            return None
        print(navigation_hint_with_help())
        pause_for_user()


def _assign(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        root = resolve_workspace_root()
        student = choose_student(root, current.class_id)
        preset = _choose_role_preset()
        role_key = None if preset is not None else _choose_role_key()
        group_id = _choose_optional_group(current)
        sessions = list_sessions(current.class_id, current.activity_id)
        context = choose_effective_context(current.activity_id, sessions)
        actor = state.require_actor()
        participant = core_student_participant(
            root,
            current.class_id,
            student.student_id,
        )
        assignment_id = f"role-{uuid.uuid4().hex}"
        if preset is None:
            assert role_key is not None
            if not confirm_write(
                "Assign Role",
                "ADD",
                (
                    f"Student: {student.first_name} {student.last_name}",
                    f"Role: {role_key}",
                    f"Group: {group_id or 'Activity-wide'}",
                ),
            ):
                return
            result = assign_role(
                AssignRoleRequest(
                    class_id=current.class_id,
                    activity_id=current.activity_id,
                    role_assignment_id=assignment_id,
                    participant_reference=participant,
                    role_key=role_key,
                    effective_context=context,
                    expected_snapshot_revision=current.snapshot_revision,
                    actor=actor,
                    group_id=group_id,
                )
            )
        else:
            request = ApplyRolePresetRequest(
                preset_id=preset.preset_id,
                preset_revision_id=preset.preset_revision_id,
                class_id=current.class_id,
                activity_id=current.activity_id,
                role_assignment_id=assignment_id,
                participant_reference=participant,
                effective_context=context,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                group_id=group_id,
            )
            prepared = prepare_role_preset_application(request)
            if not confirm_write(
                "Assign Saved Role",
                "ADD",
                (
                    f"Student: {student.first_name} {student.last_name}",
                    f"Role: {prepared.preset_name}",
                    f"Group: {group_id or 'Activity-wide'}",
                ),
            ):
                return
            result = apply_role_preset(
                request,
                review_digest=prepared.review_digest,
            )
        show_result(
            "Role Result",
            (
                "Role assigned.",
                f"Role Assignment: {result.role_assignment_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)




def _save_role_as_preset(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        roles = list_roles(current.class_id, current.activity_id)
        selected = _choose_existing(roles, "Save a Role as a Preset")
        name = prompt_text(
            "Save Role Preset",
            "Preset name",
            help_text="Name the reusable Role shown in future assignment setup.",
            default=selected.role_key.replace("_", " ").title(),
        )
        assert name is not None
        description = prompt_text(
            "Save Role Preset",
            "Description",
            help_text="Optional reusable guidance; assignee/context are never saved.",
            optional=True,
        )
        preset_id = f"role-preset-{uuid.uuid4().hex}"
        request = SaveRolePresetFromAssignmentRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            role_assignment_id=selected.role_assignment_id,
            preset_id=preset_id,
            preset_revision_id=f"{preset_id}-v1",
            name=name,
            description=description,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
        prepared = prepare_role_preset_from_assignment(request)
        if not confirm_write(
            "Save Role Preset",
            "SAVE",
            (
                f"Preset: {prepared.name}",
                *prepared.reusable_fields,
                "NOT SAVED:",
                *prepared.excluded_state,
            ),
        ):
            return
        result = save_role_preset_from_assignment(
            request,
            review_digest=prepared.review_digest,
        )
        show_result(
            "Role Preset Saved",
            (f"Preset: {result.preset_id}", "Assignment state was not copied."),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _end(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        items = tuple(
            item
            for item in list_roles(current.class_id, current.activity_id)
            if item.status in {"planned", "active"}
        )
        role = _choose_existing(items, "End a Role")
        status = prompt_text(
            "End Role",
            "End status",
            help_text="Use completed, withdrawn, or cancelled.",
            default="completed",
        )
        assert status is not None
        actor = state.require_actor()
        if not confirm_write(
            "End Role",
            "END",
            (f"Role: {role.role_key}", f"Status: {status}"),
        ):
            return
        result = end_role(
            EndRoleRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                role_assignment_id=role.role_assignment_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                status=status,
            )
        )
        show_result(
            "Role Result",
            (
                "Role ended.",
                f"Role Assignment: {result.role_assignment_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _reassign(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        items = tuple(
            item
            for item in list_roles(current.class_id, current.activity_id)
            if item.status in {"planned", "active"}
        )
        predecessor = _choose_existing(items, "Reassign a Role")
        root = resolve_workspace_root()
        student = choose_student(root, current.class_id)
        role_key = _choose_role_key()
        group_id = _choose_optional_group(current)
        sessions = list_sessions(current.class_id, current.activity_id)
        context = choose_effective_context(current.activity_id, sessions)
        actor = state.require_actor()
        if not confirm_write(
            "Reassign Role",
            "REASSIGN",
            (
                f"Previous Role: {predecessor.role_key}",
                f"New student: {student.first_name} {student.last_name}",
                f"New Role: {role_key}",
            ),
        ):
            return
        result = reassign_role(
            ReassignRoleRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                role_assignment_id=predecessor.role_assignment_id,
                successor_role_assignment_id=f"role-{uuid.uuid4().hex}",
                participant_reference=core_student_participant(
                    root,
                    current.class_id,
                    student.student_id,
                ),
                role_key=role_key,
                effective_context=context,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                group_id=group_id,
            )
        )
        show_result(
            "Role Result",
            (
                "Role reassigned.",
                f"New Role Assignment: {result.role_assignment_id}",
                f"Previous: {result.predecessor_role_assignment_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def launch_role_menu(activity: ActivitySummary, state: MenuSessionContext) -> None:
    """Manage contextual Role Assignments for one Activity."""
    while True:
        clear_screen()
        print_menu_header("Roles")
        print(f"Activity: {activity.title}")
        print()
        print("1. List Roles")
        print("2. Assign a Role")
        print("3. End a Role")
        print("4. Reassign a Role")
        print("5. Save a Role as a Preset")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Role Help")
            print(
                "Roles record an assignment, not proof of contribution or authorship."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _list(activity)
        elif choice == "2":
            _assign(activity, state)
        elif choice == "3":
            _end(activity, state)
        elif choice == "4":
            _reassign(activity, state)
        elif choice == "5":
            _save_role_as_preset(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()
