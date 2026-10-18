"""Teacher review/save of exact Session-scoped current Groups as a grouping."""

from __future__ import annotations

from pds_core.rosters import student_display_name, student_lookup
from pds_core.workspace import resolve_workspace_root

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_prompts import (
    choose_session,
    confirm_write,
    handle_write_error,
    prompt_text,
    show_result,
    slug_identifier,
)
from concord.menu_ui import clear_screen, pause_for_user, print_menu_header
from concord.workflows import ActivitySummary, list_sessions, show_activity
from concord.workflows.class_group_arrangement_operational import (
    PreparedOperationalGroupingSave,
    SaveOperationalGroupingRequest,
    prepare_save_operational_grouping,
    save_operational_grouping,
)
from concord.workflows.participants import load_required_roster


def _review_placements(
    activity: ActivitySummary, preview: PreparedOperationalGroupingSave
) -> None:
    """Reveal named membership only inside the teacher's requested review."""
    roster = load_required_roster(resolve_workspace_root(), activity.class_id)
    names = {
        sid: student_display_name(student)
        for sid, student in student_lookup(roster).items()
    }
    clear_screen()
    print_menu_header("Review existing Group placements")
    print(f"Selected Session: {preview.source_session_id}")
    print(f"Groups: {len(preview.groups)}; assigned: {preview.assigned_count}")
    print()
    for group in preview.groups:
        print(f"{group.label}: {len(group.student_ids)} students")
        for student_id in group.student_ids:
            print(f"  {names.get(student_id, 'Student no longer on current roster')}")
    if preview.unresolved_student_ids:
        print()
        print(f"Unassigned students: {len(preview.unresolved_student_ids)}")
        for student_id in preview.unresolved_student_ids:
            print(f"  {names.get(student_id, 'Student no longer on current roster')}")
    print()
    pause_for_user()


def save_grouping_from_existing_groups(
    activity: ActivitySummary, state: MenuSessionContext
) -> None:
    """One Session, one reviewed source snapshot, and one final SAVE."""
    try:
        current = show_activity(activity.class_id, activity.activity_id).summary
        sessions = list_sessions(current.class_id, current.activity_id)
        if not sessions:
            show_result(
                "Save existing Groups",
                ("This Activity has no Session to inspect.",),
            )
            return
        session = choose_session(sessions, title="Choose source Session")
        name = prompt_text(
            "Save existing Groups",
            "Grouping name",
            help_text="Name the reusable arrangement, e.g. Six Table Groups.",
        )
        assert name is not None
        arrangement_id = prompt_text(
            "Save existing Groups",
            "Grouping identifier",
            help_text="Stable, class-scoped saved grouping identifier.",
            default=slug_identifier(name, "saved-grouping"),
        )
        assert arrangement_id is not None
        request = SaveOperationalGroupingRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            session_id=session.session_id,
            arrangement_id=arrangement_id,
            name=name,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
        preview = prepare_save_operational_grouping(request)
        _review_placements(current, preview)
        acknowledged = not preview.unresolved_student_ids
        if not acknowledged:
            acknowledged = confirm_write(
                "Acknowledge unassigned students",
                "ACKNOWLEDGE",
                (
                    f"Unassigned students: {len(preview.unresolved_student_ids)}",
                    "They will remain explicitly unassigned in this saved grouping.",
                    "They will require a placement decision when this grouping "
                    "is reused.",
                ),
            )
        if not acknowledged:
            return
        if not confirm_write(
            "Save existing Groups",
            "SAVE",
            (
                f"Saved name: {preview.name}",
                f"Source Session: {session.label or session.session_id}",
                f"Groups: {len(preview.groups)}",
                f"Assigned: {preview.assigned_count}",
                f"Unassigned: {len(preview.unresolved_student_ids)}",
                "Copies placements only; no Activity records or Scores are modified.",
            ),
        ):
            return
        request = SaveOperationalGroupingRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            session_id=request.session_id,
            arrangement_id=request.arrangement_id,
            name=request.name,
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            acknowledge_unresolved=acknowledged,
        )
        saved = save_operational_grouping(request, review_digest=preview.review_digest)
        show_result(
            "Saved existing Groups",
            (
                f"Saved grouping: {saved.revision.name}",
                f"Groups: {len(saved.revision.groups)}",
                "The original Activity and memberships are unchanged.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        handle_write_error(
            error,
            reload=lambda: (
                show_activity(activity.class_id, activity.activity_id).summary
            ),
            error_title="Save existing Groups error",
        )


__all__ = ["save_grouping_from_existing_groups"]
