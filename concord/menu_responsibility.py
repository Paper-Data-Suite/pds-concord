"""Teacher-facing Responsibility Assignment workflows for Concord."""

from __future__ import annotations

import uuid

from pds_core.workspace import resolve_workspace_root

from concord.menu_actor_action import (
    confirm_actor_write,
    confirm_prepared_actor_write,
)
from concord.menu_assignment_end import (
    assignment_end_review,
    choose_assignment_end_status,
)
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
from concord.menu_standards_context import standards_kwargs_for_activity
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import ConcordRecordReference
from concord.workflows import (
    ActivitySummary,
    ApplyResponsibilityPresetRequest,
    AssignResponsibilityRequest,
    ConcordWorkflowError,
    EndResponsibilityRequest,
    PresetSummary,
    ReassignResponsibilityRequest,
    ResponsibilitySummary,
    SaveResponsibilityPresetFromAssignmentRequest,
    apply_responsibility_preset,
    assign_responsibility,
    core_student_participant,
    end_responsibility,
    group_record_reference,
    list_groups,
    list_presets,
    list_responsibilities,
    list_sessions,
    prepare_responsibility_preset_application,
    prepare_responsibility_preset_from_assignment,
    reassign_responsibility,
    save_responsibility_preset_from_assignment,
    show_activity,
)
from concord.workflows.models import WorkflowActor, WorkflowAssigneeReference


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _handle_error(activity: ActivitySummary, error: Exception) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title="Responsibility Error",
    )


def _list(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Responsibilities")
    try:
        items = list_responsibilities(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"Responsibilities could not be loaded: {error}")
    else:
        if not items:
            print("No Responsibility Assignments are available.")
        for item in items:
            print(
                f"{_responsibility_assignee_label(item)}: "
                f"{item.description} - {item.status}"
            )
    print()
    pause_for_user()


def _responsibility_assignee_label(item: ResponsibilitySummary) -> str:
    if item.assignee_display_label is not None:
        return item.assignee_display_label
    if isinstance(item.assignee_reference, ConcordRecordReference):
        return item.assignee_reference.record_id
    return item.assignee_reference.participant_id


def _choose_existing(
    items: tuple[ResponsibilitySummary, ...],
    title: str,
) -> ResponsibilitySummary:
    return select_one(
        title,
        items,
        [
            f"{_responsibility_assignee_label(item)}: "
            f"{item.description} - {item.status}"
            for item in items
        ],
        help_text=(
            "Choose the Responsibility Assignment whose lifecycle you want to change."
        ),
    )


def _choose_assignee(
    activity: ActivitySummary,
) -> tuple[WorkflowAssigneeReference, str | None, str]:
    clear_screen()
    print_menu_header("Responsibility Assignee")
    print("1. Student")
    print("2. Group")
    print_navigation()
    print()
    raw = input("Select an option: ").strip()
    navigation = parse_menu_navigation(raw)
    if navigation is ConcordMenuChoice.HELP:
        clear_screen()
        print_menu_header("Responsibility Assignee Help")
        print("Responsibilities may belong to one rostered student or to a Group.")
        print(
            "A Group assignee remains a Group; Concord does not synthesize a student."
        )
        print()
        pause_for_user()
        return _choose_assignee(activity)
    if navigation is NavigationChoice.BACK:
        raise CancelMenuAction
    if raw == "1":
        root = resolve_workspace_root()
        student = choose_student(root, activity.class_id)
        return (
            core_student_participant(root, activity.class_id, student.student_id),
            None,
            f"{student.first_name} {student.last_name}",
        )
    if raw == "2":
        groups = list_groups(activity.class_id, activity.activity_id)
        group = choose_group(groups, title="Choose an Assignee Group")
        return group_record_reference(group.group_id), group.group_id, group.label
    print(navigation_hint_with_help())
    pause_for_user()
    return _choose_assignee(activity)


def _choose_responsibility_preset() -> PresetSummary | None:
    presets = list_presets("responsibility")
    if not presets:
        return None
    while True:
        clear_screen()
        print_menu_header("Responsibility Source")
        print("1. Use a saved Responsibility")
        print("2. Enter Responsibility manually")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Saved Responsibility Help",
                (
                    "Saved Responsibilities reuse obligation text only.",
                    "Assignee, Group, context, identity, and history are always fresh.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            return select_one(
                "Choose a Saved Responsibility",
                presets,
                tuple(item.name for item in presets),
                help_text="Choose reusable work expectations; assignee state is new.",
            )
        if raw == "2":
            return None
        print(navigation_hint_with_help())
        pause_for_user()


def _assign(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        assignee, group_id, label = _choose_assignee(current)
        preset = _choose_responsibility_preset()
        description: str | None = None
        expected_output: str | None = None
        if preset is None:
            description = prompt_text(
                "Assign Responsibility",
                "Responsibility",
                help_text="Describe the concrete responsibility being assigned.",
            )
            assert description is not None
            expected_output = prompt_text(
                "Assign Responsibility",
                "Expected output",
                help_text="Optionally name the expected product or outcome.",
                optional=True,
            )
        sessions = list_sessions(current.class_id, current.activity_id)
        context = choose_effective_context(current.activity_id, sessions)
        assignment_id = f"responsibility-{uuid.uuid4().hex}"
        if preset is None:
            assert description is not None
            actor = confirm_actor_write(
                "Assign Responsibility",
                "ADD",
                (
                    f"Assignee: {label}",
                    f"Responsibility: {description}",
                    f"Sessions: {len(context.session_ids)}",
                ),
                state=state,
                legacy_confirm=confirm_write,
            )
            if actor is None:
                return
            result = assign_responsibility(
                AssignResponsibilityRequest(
                    class_id=current.class_id,
                    activity_id=current.activity_id,
                    responsibility_assignment_id=assignment_id,
                    assignee_reference=assignee,
                    description=description,
                    effective_context=context,
                    expected_snapshot_revision=current.snapshot_revision,
                    actor=actor,
                    group_id=group_id,
                    expected_output=expected_output,
                ),
                **standards_kwargs_for_activity(current),
            )
        else:
            standards_kwargs = standards_kwargs_for_activity(current)

            def _prepare_for_actor(
                actor: WorkflowActor,
            ) -> tuple[
                tuple[ApplyResponsibilityPresetRequest, str],
                tuple[str, ...],
            ]:
                request = ApplyResponsibilityPresetRequest(
                    preset_id=preset.preset_id,
                    preset_revision_id=preset.preset_revision_id,
                    class_id=current.class_id,
                    activity_id=current.activity_id,
                    responsibility_assignment_id=assignment_id,
                    assignee_reference=assignee,
                    effective_context=context,
                    expected_snapshot_revision=current.snapshot_revision,
                    actor=actor,
                    group_id=group_id,
                )
                prepared = prepare_responsibility_preset_application(
                    request, **standards_kwargs
                )
                return (request, prepared.review_digest), (
                    f"Assignee: {label}",
                    f"Responsibility: {prepared.description}",
                    f"Expected output: {prepared.expected_output or '-'}",
                )

            reviewed = confirm_prepared_actor_write(
                "Assign Saved Responsibility",
                "ADD",
                state=state,
                legacy_confirm=confirm_write,
                prepare_for_actor=_prepare_for_actor,
            )
            if reviewed is None:
                return
            request, review_digest = reviewed
            result = apply_responsibility_preset(
                request,
                review_digest=review_digest,
                **standards_kwargs,
            )
        show_result(
            "Responsibility Result",
            (
                "Responsibility assigned.",
                f"Responsibility: {result.responsibility_assignment_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _save_responsibility_as_preset(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    try:
        current = _latest(activity)
        items = list_responsibilities(current.class_id, current.activity_id)
        selected = _choose_existing(items, "Save a Responsibility as a Preset")
        name = prompt_text(
            "Save Responsibility Preset",
            "Preset name",
            help_text="Name the reusable work expectation shown during setup.",
            default=selected.description,
        )
        assert name is not None
        preset_id = f"responsibility-preset-{uuid.uuid4().hex}"
        standards_kwargs = standards_kwargs_for_activity(current)

        def _prepare_for_actor(
            actor: WorkflowActor,
        ) -> tuple[
            tuple[SaveResponsibilityPresetFromAssignmentRequest, str],
            tuple[str, ...],
        ]:
            request = SaveResponsibilityPresetFromAssignmentRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                responsibility_assignment_id=selected.responsibility_assignment_id,
                preset_id=preset_id,
                preset_revision_id=f"{preset_id}-v1",
                name=name,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
            )
            prepared = prepare_responsibility_preset_from_assignment(
                request, **standards_kwargs
            )
            return (request, prepared.review_digest), (
                f"Preset: {prepared.name}",
                *prepared.reusable_fields,
                "NOT SAVED:",
                *prepared.excluded_state,
            )

        reviewed = confirm_prepared_actor_write(
            "Save Responsibility Preset",
            "SAVE",
            state=state,
            legacy_confirm=confirm_write,
            prepare_for_actor=_prepare_for_actor,
        )
        if reviewed is None:
            return
        request, review_digest = reviewed
        result = save_responsibility_preset_from_assignment(
            request,
            review_digest=review_digest,
            **standards_kwargs,
        )
        show_result(
            "Responsibility Preset Saved",
            (f"Preset: {result.preset_id}", "Assignee/context were not copied."),
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
            for item in list_responsibilities(current.class_id, current.activity_id)
            if item.status in {"planned", "active"}
        )
        if not items:
            show_result(
                "Responsibility Result",
                ("No planned or active Responsibilities are available to end.",),
            )
            return
        responsibility = _choose_existing(items, "End a Responsibility")
        if responsibility.snapshot_revision != current.snapshot_revision:
            raise ConcordWorkflowError(
                "The Responsibility selection is stale. Reopen this Activity and retry."
            )
        assignee = _responsibility_assignee_label(responsibility)
        display = f"{assignee}: {responsibility.description}"
        status = choose_assignment_end_status(
            current,
            record_kind="Responsibility",
            record_id=responsibility.responsibility_assignment_id,
            display_label=display,
            current_status=responsibility.status,
        )
        actor = confirm_actor_write(
            "End Responsibility",
            "END",
            assignment_end_review(
                current,
                record_kind="Responsibility",
                record_id=responsibility.responsibility_assignment_id,
                display_label=display,
                previous_status=responsibility.status,
                requested_status=status,
            ),
            state=state,
            legacy_confirm=confirm_write,
        )
        if actor is None:
            return
        result = end_responsibility(
            EndResponsibilityRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                responsibility_assignment_id=(
                    responsibility.responsibility_assignment_id
                ),
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                status=status,
            ),
            **standards_kwargs_for_activity(current),
        )
        show_result(
            "Responsibility Result",
            (
                "Responsibility ended; prior revisions retained.",
                f"Responsibility: {result.responsibility_assignment_id}",
                f"Status: {responsibility.status} -> {status}",
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
            for item in list_responsibilities(current.class_id, current.activity_id)
            if item.status in {"planned", "active"}
        )
        predecessor = _choose_existing(items, "Reassign a Responsibility")
        assignee, group_id, label = _choose_assignee(current)
        description = prompt_text(
            "Reassign Responsibility",
            "Responsibility",
            help_text="Describe the successor responsibility assignment.",
            default=predecessor.description,
        )
        assert description is not None
        sessions = list_sessions(current.class_id, current.activity_id)
        context = choose_effective_context(current.activity_id, sessions)
        actor = confirm_actor_write(
            "Reassign Responsibility",
            "REASSIGN",
            (
                f"Previous: {predecessor.description}",
                f"New assignee: {label}",
                f"Responsibility: {description}",
            ),
            state=state,
            legacy_confirm=confirm_write,
        )
        if actor is None:
            return
        result = reassign_responsibility(
            ReassignResponsibilityRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                responsibility_assignment_id=(predecessor.responsibility_assignment_id),
                successor_responsibility_assignment_id=(
                    f"responsibility-{uuid.uuid4().hex}"
                ),
                assignee_reference=assignee,
                description=description,
                effective_context=context,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                group_id=group_id,
            ),
            **standards_kwargs_for_activity(current),
        )
        show_result(
            "Responsibility Result",
            (
                "Responsibility reassigned.",
                f"New Responsibility: {result.responsibility_assignment_id}",
                f"Previous: {result.predecessor_responsibility_assignment_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def launch_responsibility_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Manage Responsibility Assignments for one Activity."""
    while True:
        clear_screen()
        print_menu_header("Responsibilities")
        print(f"Activity: {activity.title}")
        print()
        print("1. List Responsibilities")
        print("2. Assign a Responsibility")
        print("3. End a Responsibility")
        print("4. Reassign a Responsibility")
        print("5. Save a Responsibility as a Preset")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Responsibility Help")
            print("Responsibilities record expected work, not proof it was fulfilled.")
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
            _save_responsibility_as_preset(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()
