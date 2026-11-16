"""Teacher review/save of exact Session-scoped current Groups as a grouping."""

from __future__ import annotations

from pds_core.rosters import student_display_name, student_lookup
from pds_core.workspace import resolve_workspace_root

from concord.menu_actor_action import confirm_prepared_actor_write
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
from concord.workflows import (
    ActivitySummary,
    WorkflowActor,
    list_sessions,
    show_activity,
)
from concord.workflows.class_group_arrangement_operational import (
    PreparedOperationalGroupingSave,
    SaveOperationalGroupingRequest,
    prepare_save_operational_grouping,
    save_operational_grouping,
)
from concord.workflows.errors import ConcordWorkflowConflictError
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
        inspection_request = SaveOperationalGroupingRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            session_id=session.session_id,
            arrangement_id=arrangement_id,
            name=name,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
        inspected = prepare_save_operational_grouping(inspection_request)
        _review_placements(current, inspected)
        acknowledged = not inspected.unresolved_student_ids
        if not acknowledged:
            acknowledged = confirm_write(
                "Acknowledge unassigned students",
                "ACKNOWLEDGE",
                (
                    f"Unassigned students: {len(inspected.unresolved_student_ids)}",
                    "They will remain explicitly unassigned in this saved grouping.",
                    "They will require a placement decision when this grouping "
                    "is reused.",
                ),
            )
        if not acknowledged:
            return

        def _prepare_for_actor(
            actor: WorkflowActor,
        ) -> tuple[
            tuple[SaveOperationalGroupingRequest, PreparedOperationalGroupingSave],
            tuple[str, ...],
        ]:
            request = SaveOperationalGroupingRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                session_id=session.session_id,
                arrangement_id=arrangement_id,
                name=name,
                expected_snapshot_revision=current.snapshot_revision,
                actor=actor,
                acknowledge_unresolved=acknowledged,
            )
            preview = prepare_save_operational_grouping(request)
            # An actor switch cannot silently switch the Group/Membership
            # snapshot or the placements previously reviewed and acknowledged.
            if (
                preview.source_activity_id != inspected.source_activity_id
                or preview.source_session_id != inspected.source_session_id
                or (
                    preview.source_snapshot_revision
                    != inspected.source_snapshot_revision
                )
                or preview.groups != inspected.groups
                or preview.unresolved_student_ids != inspected.unresolved_student_ids
                or preview.assigned_count != inspected.assigned_count
                or preview.name != inspected.name
            ):
                raise ConcordWorkflowConflictError(
                    "Existing Group placements changed during actor review. "
                    "Reopen and review before saving; nothing was written."
                )
            return (request, preview), (
                f"Saved name: {preview.name}",
                f"Source Session: {session.label or session.session_id}",
                f"Groups: {len(preview.groups)}",
                f"Assigned: {preview.assigned_count}",
                f"Unassigned: {len(preview.unresolved_student_ids)}",
                "Copies placements only; no Activity records or Scores are modified.",
            )

        confirmed = confirm_prepared_actor_write(
            "Save existing Groups",
            "SAVE",
            state=state,
            legacy_confirm=confirm_write,
            prepare_for_actor=_prepare_for_actor,
        )
        if confirmed is None:
            return
        request, preview = confirmed
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
