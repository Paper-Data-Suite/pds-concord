"""Teacher-facing Session workflows for one open Concord Activity."""

from __future__ import annotations

from concord.menu_actor_action import confirm_actor_write
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
    select_one,
    show_result,
    slug_identifier,
)
from concord.menu_standards_context import standards_kwargs_for_activity
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

_SESSION_STATUS_CHOICES = (
    "planned",
    "active",
    "completed",
    "cancelled",
    "interrupted",
    "archived",
)
_SESSION_STATUS_EXPLANATIONS = (
    "Planned - Session is scheduled or being prepared",
    "Active - teacher identifies this Session as underway",
    "Completed - Session has concluded; no Scores are created",
    "Cancelled - Session will not proceed as planned",
    "Interrupted - Session stopped before normal completion",
    "Archived - Session is retained as history",
)


def _choose_session_status(activity: ActivitySummary, session: SessionSummary) -> str:
    """Choose an exact native Session status, without inventing transitions."""
    labels = tuple(
        f"{explanation}{' [current]' if status == session.status else ''}"
        for status, explanation in zip(
            _SESSION_STATUS_CHOICES, _SESSION_STATUS_EXPLANATIONS, strict=True
        )
    )
    return select_one(
        (
            "Edit Session Status\n"
            f"Activity: {activity.title} ({activity.activity_id})\n"
            f"Class: {activity.class_id}\n"
            f"Session: {session.sequence}: {session.label or 'Unlabeled session'}\n"
            f"Session ID: {session.session_id}\n"
            f"Current status: {session.status}\n"
            f"Snapshot: {activity.snapshot_revision}"
        ),
        _SESSION_STATUS_CHOICES,
        labels,
        help_text=(
            "Select a Concord Session status, not an Activity status. "
            "This does not set actual/scheduled timestamps, create an evidence "
            "record, Score, Grade or publication. The canonical service still "
            "checks the candidate and Activity snapshot before writing."
        ),
    )


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _result_lines(
    result_snapshot: int,
    session_id: str,
    *,
    no_op: bool,
) -> tuple[str, ...]:
    """Human result; the exact session ID and revision remain internal."""
    return (
        "No Session changes were needed." if no_op else "Session saved.",
        "Return to the Session list to see its current label and status.",
    )


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
            print(
                f"Session {item.sequence}: {item.label or 'Unlabeled session'} "
                f"[{item.status.replace('_', ' ')}]"
            )
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
        actor = confirm_actor_write(
            "Add Session",
            "ADD",
            (
                f"Activity: {current.title}",
                f"Session: {label or f'Session {sequence}'}",
                f"Sequence: {sequence}",
                "Status: planned",
            ),
            state=state,
            legacy_confirm=confirm_write,
        )
        if actor is None:
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
            ),
            **standards_kwargs_for_activity(current),
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
            if (
                session.class_id != current.class_id
                or session.activity_id != current.activity_id
                or session.snapshot_revision != current.snapshot_revision
            ):
                raise ConcordWorkflowError(
                    "The selected Session or Activity changed before status "
                    "selection. Reopen the Session and retry. No Session was updated."
                )
            status = _choose_session_status(current, session)
            if status == session.status:
                show_result(
                    "Session Result",
                    (
                        "No Session changes were needed.",
                        f"Session: {session.session_id}",
                        f"Status remains: {session.status}",
                        f"Snapshot: {current.snapshot_revision}",
                    ),
                )
                return
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
        review_lines = [
            f"Activity: {current.title} ({current.activity_id})",
            f"Class: {current.class_id}",
            f"Session {session.sequence}: {session.label or 'Unlabeled session'}",
            f"Session ID: {session.session_id}",
            f"Snapshot: {current.snapshot_revision}",
            f"Change: {display}",
        ]
        if field == "status":
            review_lines.extend(
                (
                    f"Current status: {session.status}",
                    f"Requested status: {values['status']}",
                    "This does not create timestamps, evidence, Scores, "
                    "Grades or publications.",
                )
            )
        actor = confirm_actor_write(
            "Edit Session",
            "UPDATE",
            tuple(review_lines),
            state=state,
            legacy_confirm=confirm_write,
        )
        if actor is None:
            return
        values["actor"] = actor
        request = UpdateSessionRequest(**values)  # type: ignore[arg-type]
        result = update_session(request, **standards_kwargs_for_activity(current))
        receipt_lines = list(
            _result_lines(
                result.commit.snapshot_revision,
                result.session_id,
                no_op=result.commit.no_op,
            )
        )
        if field == "status":
            receipt_lines.extend(
                (
                    f"Session: {result.session_id}",
                    f"Status: {session.status} -> {values['status']}",
                    f"Snapshot: {result.commit.snapshot_revision}",
                )
            )
        show_result("Session Result", tuple(receipt_lines))
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
        print(f"Session {session.sequence}: {session.label or 'Unlabeled session'}")
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
