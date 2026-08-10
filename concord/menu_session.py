"""Teacher-facing Session workflows for one open Concord Activity."""

from __future__ import annotations

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    choose_session,
    confirm_write,
    handle_write_error,
    prompt_positive_int,
    prompt_text,
    show_result,
    slug_identifier,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowError,
    CreateSessionRequest,
    SessionSummary,
    UpdateSessionRequest,
    create_session,
    list_sessions,
    show_activity,
    update_session,
)


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _result_lines(
    result_snapshot: int,
    session_id: str,
    *,
    no_op: bool,
) -> tuple[str, ...]:
    if no_op:
        return (
            "No changes were needed.",
            f"Session: {session_id}",
            f"Snapshot: {result_snapshot}",
        )
    return ("Session saved.", f"Session: {session_id}", f"Snapshot: {result_snapshot}")


def _handle_error(activity: ActivitySummary, error: Exception) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title="Session Error",
    )


def _list(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Sessions")
    try:
        sessions = list_sessions(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"Sessions could not be loaded: {error}")
    else:
        if not sessions:
            print("No Sessions are available.")
        for item in sessions:
            print(f"{item.sequence}. {item.label or item.session_id} - {item.status}")
    print()
    pause_for_user()


def _add(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        current = _latest(activity)
        sessions = list_sessions(current.class_id, current.activity_id)
        next_sequence = max((item.sequence for item in sessions), default=0) + 1
        label = prompt_text(
            "Add Session",
            "Session label",
            help_text=(
                "Use a short teacher-facing label, such as Day 2 or Lab follow-up."
            ),
            optional=True,
        )
        proposed = slug_identifier(
            f"{current.activity_id}-session-{next_sequence}",
            f"session-{next_sequence}",
        )
        session_id = prompt_text(
            "Add Session",
            "Session ID",
            help_text="The Session ID is durable and cannot be only a display label.",
            default=proposed,
        )
        assert session_id is not None
        sequence = prompt_positive_int(
            "Add Session",
            "Sequence",
            help_text="Sequence controls Session ordering inside the Activity.",
            default=next_sequence,
        )
        actor = state.require_actor()
        if not confirm_write(
            "Add Session",
            "ADD",
            (
                f"Activity: {current.title}",
                f"Session: {label or session_id}",
                f"Sequence: {sequence}",
                "Status: planned",
            ),
        ):
            return
        result = create_session(
            CreateSessionRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                session_id=session_id,
                sequence=sequence,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                label=label,
            )
        )
        show_result(
            "Session Result",
            _result_lines(
                result.commit.snapshot_revision,
                result.session_id,
                no_op=result.commit.no_op,
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _edit_field(
    activity: ActivitySummary,
    session: SessionSummary,
    state: MenuSessionContext,
    field: str,
) -> None:
    try:
        current = _latest(activity)
        values: dict[str, object] = {
            "class_id": current.class_id,
            "activity_id": current.activity_id,
            "session_id": session.session_id,
            "expected_snapshot_revision": current.snapshot_revision,
            "actor": state.require_actor(),
        }
        display = field.replace("_", " ").title()
        if field == "sequence":
            values[field] = prompt_positive_int(
                "Edit Session",
                "Sequence",
                help_text="Sequence controls Session ordering inside the Activity.",
                default=session.sequence,
            )
        elif field == "status":
            status = prompt_text(
                "Edit Session",
                "Status",
                help_text=(
                    "Valid statuses include planned, active, completed, cancelled, "
                    "interrupted, and archived."
                ),
                default=session.status,
            )
            assert status is not None
            values[field] = status
        else:
            current_value = getattr(session, field, None)
            values[field] = prompt_text(
                "Edit Session",
                display,
                help_text=f"Update the Session {field.replace('_', ' ')}.",
                default=current_value if isinstance(current_value, str) else None,
                optional=True,
            )
        if not confirm_write(
            "Edit Session",
            "UPDATE",
            (f"Session: {session.label or session.session_id}", f"Change: {display}"),
        ):
            return
        request = UpdateSessionRequest(**values)  # type: ignore[arg-type]
        result = update_session(request)
        show_result(
            "Session Result",
            _result_lines(
                result.commit.snapshot_revision,
                result.session_id,
                no_op=result.commit.no_op,
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)


def _edit(activity: ActivitySummary, state: MenuSessionContext) -> None:
    try:
        sessions = list_sessions(activity.class_id, activity.activity_id)
        session = choose_session(sessions, title="Edit a Session")
    except CancelMenuAction:
        return
    except ConcordWorkflowError as error:
        show_result("Session Error", (str(error),))
        return
    while True:
        clear_screen()
        print_menu_header("Edit Session")
        print(f"Session: {session.label or session.session_id}")
        print()
        print("1. Label")
        print("2. Sequence")
        print("3. Status")
        print("4. Scheduled start")
        print("5. Scheduled end")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Session Help")
            print(
                "Session changes create new storage revisions of the same Session ID."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _edit_field(activity, session, state, "label")
            return
        elif choice == "2":
            _edit_field(activity, session, state, "sequence")
            return
        elif choice == "3":
            _edit_field(activity, session, state, "status")
            return
        elif choice == "4":
            _edit_field(activity, session, state, "scheduled_start")
            return
        elif choice == "5":
            _edit_field(activity, session, state, "scheduled_end")
            return
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def launch_session_menu(activity: ActivitySummary, state: MenuSessionContext) -> None:
    """Manage Sessions for one open Activity."""
    while True:
        clear_screen()
        print_menu_header("Sessions")
        print(f"Activity: {activity.title}")
        print()
        print("1. List Sessions")
        print("2. Add a Session")
        print("3. Edit a Session")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Session Help")
            print(
                "Sessions preserve the time/context boundaries of collaboration work."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _list(activity)
        elif choice == "2":
            _add(activity, state)
        elif choice == "3":
            _edit(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()
