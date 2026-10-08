
"""Teacher-facing Student Feedback Distribution menu for one Activity."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pds_core.routing_models import ModuleWorkRef

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import prompt_text, select_many, show_result
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.pds_contract import CONCORD_MODULE_ID
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_AVAILABILITY_UNRESOLVED,
    FEEDBACK_SELECTION_ALL,
    FEEDBACK_SELECTION_SELECTED,
    ActivitySummary,
    StudentFeedbackDistributionPreview,
    StudentFeedbackRosterEntry,
    StudentFeedbackRosterPreparation,
    execute_student_feedback_distribution,
    load_student_feedback_roster_preparation,
    open_student_feedback_distribution_directory,
    open_student_feedback_distribution_print_pdf,
    prepare_student_feedback_distribution_plan,
    preview_student_feedback_distribution,
    verify_student_feedback_distribution_directory,
)
from concord.workflows.activity_read import load_activity_read_context
from concord.workflows.context import resolve_read_workspace_root

_AVAILABLE_ONLY_CONFIRMATION = "PREPARE AVAILABLE ONLY"


def _root() -> Path:
    root = resolve_read_workspace_root()
    if root is None:
        raise FileNotFoundError("Paper Data Suite workspace does not exist.")
    return Path(root)


def _created_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _display_name(entry: StudentFeedbackRosterEntry) -> str:
    return entry.student_display_name or "Unresolved roster student"


def _availability_label(entry: StudentFeedbackRosterEntry) -> str:
    if entry.availability == FEEDBACK_AVAILABILITY_DISTRIBUTABLE:
        return "feedback available"
    if entry.availability == FEEDBACK_AVAILABILITY_NONE:
        return "no distributable feedback"
    if entry.availability == FEEDBACK_AVAILABILITY_UNRESOLVED:
        return "unresolved"
    return "unavailable"


def _load_preparation(
    activity: ActivitySummary,
) -> tuple[Path, StudentFeedbackRosterPreparation]:
    root = _root()
    context = load_activity_read_context(
        root,
        ModuleWorkRef(
            module_id=CONCORD_MODULE_ID,
            class_id=activity.class_id,
            work_id=activity.activity_id,
        ),
    )
    return root, load_student_feedback_roster_preparation(context)


def _affected_names(
    preview: StudentFeedbackDistributionPreview,
    availability: str,
) -> tuple[str, ...]:
    return tuple(
        _display_name(entry)
        for entry in preview.requested_entries
        if entry.availability == availability
    )


def _preview_lines(
    activity: ActivitySummary,
    preview: StudentFeedbackDistributionPreview,
) -> tuple[str, ...]:
    lines = [
        f"Class: {activity.class_id}",
        f"Activity: {preview.activity_title}",
        "",
        f"Roster students: {preview.roster_count}",
        f"Distributable feedback: {preview.distributable_count}",
        f"No distributable feedback: {preview.no_feedback_count}",
        f"Unresolved: {preview.unresolved_count}",
        f"Requested students: {preview.requested_count}",
        f"Selected for distribution: {preview.selected_for_output_count}",
    ]
    selected = tuple(
        _display_name(entry) for entry in preview.selected_entries
    )
    no_feedback = _affected_names(preview, FEEDBACK_AVAILABILITY_NONE)
    unresolved = _affected_names(preview, FEEDBACK_AVAILABILITY_UNRESOLVED)
    if selected:
        lines.append("")
        lines.append("Selected for output:")
        lines.extend(f"  - {name}" for name in selected)
    if no_feedback:
        lines.append("")
        lines.append("Requested students with no distributable feedback:")
        lines.extend(f"  - {name}" for name in no_feedback)
    if unresolved:
        lines.append("")
        lines.append("Requested unresolved students:")
        lines.extend(f"  - {name}" for name in unresolved)
    return tuple(lines)


def _authorize_available_only(
    activity: ActivitySummary,
    preview: StudentFeedbackDistributionPreview,
) -> bool:
    while True:
        clear_screen()
        print_menu_header("Incomplete Whole-Class Feedback")
        for line in _preview_lines(activity, preview):
            print(line)
        print()
        print(
            "Some roster students cannot be included in this distribution. "
            "No academic completion state will be recorded."
        )
        print()
        print(
            f"Type {_AVAILABLE_ONLY_CONFIRMATION} exactly to continue with "
            "available feedback only."
        )
        print("Press Enter or B to cancel.")
        print_navigation()
        print()
        raw = input("Confirmation: ")
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Available-Only Help",
                (
                    "This choice only authorizes omission from this local package.",
                    "It does not mark work missing, incomplete, failed, or complete.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK or raw == "":
            return False
        if raw == _AVAILABLE_ONLY_CONFIRMATION:
            return True
        print(f"Type {_AVAILABLE_ONLY_CONFIRMATION} exactly, or B to cancel.")
        pause_for_user()


def _destination() -> Path:
    value = prompt_text(
        "Student Feedback Distribution Destination",
        "Absolute destination directory",
        help_text=(
            "Choose the exact teacher-controlled folder to create. "
            "Concord will not email, upload, or change sharing permissions."
        ),
    )
    assert value is not None
    return Path(value)


def _confirm_prepare(
    activity: ActivitySummary,
    preview: StudentFeedbackDistributionPreview,
    destination: Path,
) -> bool:
    while True:
        clear_screen()
        print_menu_header("Prepare Student Feedback Distribution")
        for line in _preview_lines(activity, preview):
            print(line)
        print()
        print("Outputs:")
        print(
            f"- {preview.selected_for_output_count} individual student feedback PDFs"
        )
        print("- 1 combined class print PDF")
        print("- Feedback Index")
        print("- Distribution manifest")
        print()
        print(f"Destination: {destination}")
        print()
        print("Individual PDFs contain current student-target Concord Scores only.")
        print(
            "Group, Artifact, Session, and Activity Scores are not converted "
            "to student Scores."
        )
        print("No Grade or proficiency will be calculated.")
        print("No messages will be sent.")
        print("No sharing permissions will be changed.")
        print("No Concord canonical records will be changed.")
        print()
        print("Type PREPARE exactly to continue, or press Enter to cancel.")
        print_navigation()
        print()
        raw = input("Confirmation: ")
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Prepare Student Feedback Distribution Help",
                (
                    "PREPARE creates a bounded local feedback package.",
                    "It does not publish Academic Results through Core.",
                    "Review the selected count and destination before continuing.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK or raw == "":
            return False
        if raw == "PREPARE":
            return True
        print("Type uppercase PREPARE exactly, or B to cancel.")
        pause_for_user()


def _prepare_distribution(
    activity: ActivitySummary,
    *,
    selected: bool,
) -> None:
    root, preparation = _load_preparation(activity)
    selected_ids: tuple[str, ...] = ()
    selection_mode = FEEDBACK_SELECTION_ALL

    if selected:
        selection_mode = FEEDBACK_SELECTION_SELECTED
        chosen = select_many(
            "Select Students for Feedback",
            preparation.entries,
            tuple(
                f"{_display_name(entry)} - {_availability_label(entry)}"
                for entry in preparation.entries
            ),
            help_text=(
                "Choose exact roster students. The final output preserves "
                "authoritative roster order."
            ),
        )
        selected_ids = tuple(entry.student_id for entry in chosen)

    preview = preview_student_feedback_distribution(
        preparation,
        selection_mode=selection_mode,
        selected_student_ids=selected_ids,
    )

    if (
        selection_mode == FEEDBACK_SELECTION_SELECTED
        and preview.has_unavailable_requested_students
    ):
        show_result(
            "Student Feedback Selection",
            _preview_lines(activity, preview)
            + (
                "",
                "The selected set contains unavailable or unresolved feedback.",
                "No package was prepared. Revise the selection and try again.",
            ),
        )
        return

    authorize_available_only = False
    if preview.requires_available_only_decision:
        authorize_available_only = _authorize_available_only(activity, preview)
        if not authorize_available_only:
            return

    destination = _destination()
    plan = prepare_student_feedback_distribution_plan(
        preview,
        destination=destination,
        authorize_available_only=authorize_available_only,
    )
    if not _confirm_prepare(activity, preview, destination):
        return

    result = execute_student_feedback_distribution(
        plan,
        confirmation="PREPARE",
        workspace_root=root,
        created_at=_created_at(),
    )
    action = "created" if result.action == "installed" else "verified and reused"
    show_result(
        "Student Feedback Distribution Ready",
        (
            f"Package {action}.",
            f"Feedback files: {result.verification.selected_count}",
            f"Class print pages: {result.verification.combined_page_count}",
            "No delivery, printing, or student receipt state was recorded.",
        ),
    )


def _existing_directory() -> Path:
    value = prompt_text(
        "Existing Student Feedback Distribution",
        "Absolute distribution directory",
        help_text="Choose an existing Concord feedback distribution package.",
    )
    assert value is not None
    return Path(value)


def _verify_existing() -> None:
    verified = verify_student_feedback_distribution_directory(
        _existing_directory()
    )
    show_result(
        "Student Feedback Distribution Verified",
        (
            "Package verification: passed",
            f"Feedback files: {verified.selected_count}",
            f"Class print pages: {verified.combined_page_count}",
            "This verifies the package itself, not later delivery or receipt.",
        ),
    )


def _open_existing_folder() -> None:
    verified = open_student_feedback_distribution_directory(
        _existing_directory()
    )
    show_result(
        "Student Feedback Distribution",
        (
            "Verified distribution folder opened.",
            f"Feedback files: {verified.selected_count}",
        ),
    )


def _open_existing_print_pdf() -> None:
    verified = open_student_feedback_distribution_print_pdf(
        _existing_directory()
    )
    show_result(
        "Student Feedback Distribution",
        (
            "Verified class print PDF opened.",
            f"Class print pages: {verified.combined_page_count}",
        ),
    )


def launch_student_feedback_distribution_menu(
    activity: ActivitySummary,
    _state: MenuSessionContext,
) -> None:
    """Open the Activity-scoped local student feedback distribution surface."""
    while True:
        clear_screen()
        print_menu_header("Student Feedback Distribution")
        print(f"Activity: {activity.title}")
        print()
        print("1. Prepare feedback for all roster students")
        print("2. Prepare feedback for selected students")
        print("3. Verify an existing distribution")
        print("4. Open a verified distribution folder")
        print("5. Open a verified class print PDF")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Student Feedback Distribution Help",
                (
                    "Prepare a local bounded feedback package from current "
                    "student-target Scores.",
                    "This is separate from Academic Result sharing/publication.",
                    "Preparing or opening a package does not record delivery state.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            return
        try:
            if choice == "1":
                _prepare_distribution(activity, selected=False)
            elif choice == "2":
                _prepare_distribution(activity, selected=True)
            elif choice == "3":
                _verify_existing()
            elif choice == "4":
                _open_existing_folder()
            elif choice == "5":
                _open_existing_print_pdf()
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except Exception as error:
            show_result("Student Feedback Distribution Error", (str(error),))


__all__ = ["launch_student_feedback_distribution_menu"]
