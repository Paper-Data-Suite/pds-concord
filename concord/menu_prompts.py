"""Reusable low-density prompt helpers for Concord teacher workflows."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from pds_core.classes import load_class_roster
from pds_core.rosters import StudentRecord, student_display_name, student_sort_name
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
    load_standards_library,
    standards_library_path,
)
from pds_core.workspace import resolve_workspace_root

from concord.menu_context import CancelMenuAction
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_ui import (
    clear_screen,
    page_count,
    page_items,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import EffectiveContext
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStoragePartialSuccessError,
)
from concord.workflows import (
    ClassSummary,
    ConcordWorkflowValidationError,
    GroupSummary,
    MembershipSummary,
    SessionSummary,
)

T = TypeVar("T")


def prompt_text(
    title: str,
    label: str,
    *,
    help_text: str,
    default: str | None = None,
    optional: bool = False,
) -> str | None:
    """Prompt for one text value while honoring H/B/M/Q navigation."""
    while True:
        clear_screen()
        print_menu_header(title)
        if default is not None:
            print(f"Current/default: {default}")
        elif optional:
            print("Press Enter to leave this blank.")
        print_navigation()
        print()
        raw = input(f"{label}: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header(f"{title} Help")
            print(help_text)
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw:
            return raw
        if default is not None:
            return default
        if optional:
            return None


def prompt_exact_text(
    title: str,
    label: str,
    *,
    help_text: str,
) -> str:
    """Prompt for exact text while preserving whitespace for validation."""
    while True:
        clear_screen()
        print_menu_header(title)
        print_navigation()
        print()
        raw = input(f"{label}: ")
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header(f"{title} Help")
            print(help_text)
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw != "":
            return raw


def prompt_positive_int(
    title: str,
    label: str,
    *,
    help_text: str,
    default: int,
) -> int:
    """Prompt for one positive integer."""
    while True:
        raw = prompt_text(
            title,
            label,
            help_text=help_text,
            default=str(default),
        )
        assert raw is not None
        try:
            value = int(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
        clear_screen()
        print_menu_header(title)
        print("Enter a positive whole number.")
        print()
        pause_for_user()


def confirm_write(title: str, expected: str, lines: Sequence[str]) -> bool:
    """Review one write while honoring H/B/M/Q before confirmation."""
    while True:
        clear_screen()
        print_menu_header(title)
        for line in lines:
            print(line)
        print()
        print(f"Type {expected} to confirm, or press Enter to cancel.")
        print_navigation()
        print()
        raw = input("Confirmation: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header(f"{title} Help")
            print("Review the values before writing canonical Activity state.")
            print(f"Type {expected} only when the displayed change is correct.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return False
        if not raw:
            return False
        return raw.casefold() == expected.casefold()


def prompt_conflict_reload() -> bool:
    """Offer the ticketed stale-snapshot Reload/B/M/Q decision."""
    while True:
        clear_screen()
        print_menu_header("Activity Changed")
        print("This Activity changed after you opened it.")
        print()
        print("Reload the current Activity before making another change.")
        print()
        print("1. Reload")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Activity Changed Help")
            print("Reload reads the current Activity without retrying the write.")
            print("Concord never force-overwrites a stale snapshot.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return False
        if raw == "1":
            return True
        print(navigation_hint_with_help())
        pause_for_user()


def show_partial_success(error: ConcordStoragePartialSuccessError) -> None:
    """Present durable partial-success identity without dumping paths."""
    lines = [
        (
            "The Activity was committed, but follow-up work was incomplete."
            if error.pointer_published
            else "The Activity was not published as the current snapshot."
        )
    ]
    if error.snapshot_revision is not None:
        lines.append(f"Snapshot: {error.snapshot_revision}")
    if error.snapshot_sha256 is not None:
        lines.append(f"Snapshot SHA-256: {error.snapshot_sha256}")
    if error.durable_paths:
        lines.append(f"Durable recovery paths: {len(error.durable_paths)}")
    lines.append("Review canonical storage before retrying this action.")
    show_result("Partial Success", tuple(lines))



def handle_write_error(
    error: Exception,
    *,
    reload: Callable[[], object],
    error_title: str,
) -> None:
    """Translate write conflicts/partial success at the teacher-menu boundary."""
    if isinstance(error, ConcordStorageConflictError):
        if prompt_conflict_reload():
            try:
                reload()
            except Exception as reload_error:
                show_result("Reload Error", (str(reload_error),))
        return
    if isinstance(error, ConcordStoragePartialSuccessError):
        show_partial_success(error)
        return
    show_result(error_title, (str(error),))


def show_result(title: str, lines: Sequence[str]) -> None:
    clear_screen()
    print_menu_header(title)
    for line in lines:
        print(line)
    print()
    pause_for_user()


def select_one(
    title: str,
    items: Sequence[T],
    labels: Sequence[str],
    *,
    help_text: str,
) -> T:
    """Choose one item with ten-row pagination and standard navigation."""
    if len(items) != len(labels):
        raise ValueError("items and labels must have equal length.")
    if not items:
        raise ConcordWorkflowValidationError("No selectable items are available.")
    page_index = 0
    while True:
        clear_screen()
        print_menu_header(title)
        visible_items = page_items(items, page_index)
        visible_labels = page_items(labels, page_index)
        for index, label in enumerate(visible_labels, start=1):
            print(f"{index}. {label}")
        pages = page_count(len(items))
        if pages > 1:
            print()
            print(f"Page {page_index + 1} of {pages}")
            if page_index + 1 < pages:
                print("N. Next page")
            if page_index > 0:
                print("P. Previous page")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header(f"{title} Help")
            print(help_text)
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        normalized = raw.casefold()
        if normalized == "n" and page_index + 1 < pages:
            page_index += 1
            continue
        if normalized == "p" and page_index > 0:
            page_index -= 1
            continue
        if raw.isdigit():
            selected = int(raw)
            if 1 <= selected <= len(visible_items):
                return visible_items[selected - 1]
        print(navigation_hint_with_help())
        pause_for_user()


def select_many(
    title: str,
    items: Sequence[T],
    labels: Sequence[str],
    *,
    help_text: str,
) -> tuple[T, ...]:
    """Choose one or more items without displaying more than ten at once."""
    if len(items) != len(labels):
        raise ValueError("items and labels must have equal length.")
    if not items:
        raise ConcordWorkflowValidationError("No selectable items are available.")
    selected: set[int] = set()
    page_index = 0
    while True:
        clear_screen()
        print_menu_header(title)
        start = page_index * 10
        visible_items = page_items(items, page_index)
        visible_labels = page_items(labels, page_index)
        for local_index, label in enumerate(visible_labels, start=1):
            absolute_index = start + local_index - 1
            marker = "*" if absolute_index in selected else " "
            print(f"{local_index}. [{marker}] {label}")
        print()
        print(f"Selected: {len(selected)}")
        pages = page_count(len(items))
        if pages > 1:
            print(f"Page {page_index + 1} of {pages}")
            if page_index + 1 < pages:
                print("N. Next page")
            if page_index > 0:
                print("P. Previous page")
        print("A. Select all")
        print("D. Done")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header(f"{title} Help")
            print(help_text)
            print("Choose a number to add or remove it from the selection.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        normalized = raw.casefold()
        if normalized == "a":
            selected = set(range(len(items)))
            continue
        if normalized == "d" and selected:
            return tuple(items[index] for index in sorted(selected))
        if normalized == "n" and page_index + 1 < pages:
            page_index += 1
            continue
        if normalized == "p" and page_index > 0:
            page_index -= 1
            continue
        if raw.isdigit():
            local_index = int(raw) - 1
            if 0 <= local_index < len(visible_items):
                absolute_index = start + local_index
                if absolute_index in selected:
                    selected.remove(absolute_index)
                else:
                    selected.add(absolute_index)
                continue
        print("Choose a listed item, A, D, H, B, M, or Q.")
        pause_for_user()


def choose_class(classes: Sequence[ClassSummary]) -> ClassSummary:
    return select_one(
        "Choose a Class",
        classes,
        [f"{item.class_id} ({item.school_year})" for item in classes],
        help_text="Choose the existing Core class that owns this Concord Activity.",
    )


def choose_session(
    sessions: Sequence[SessionSummary],
    *,
    title: str = "Choose a Session",
) -> SessionSummary:
    return select_one(
        title,
        sessions,
        [
            f"{item.sequence}. {item.label or item.session_id} - {item.status}"
            for item in sessions
        ],
        help_text="Choose the Session whose collaboration context you want to change.",
    )


def choose_group(groups: Sequence[GroupSummary], *, title: str) -> GroupSummary:
    return select_one(
        title,
        groups,
        [f"{item.label} ({item.group_id}) - {item.status}" for item in groups],
        help_text="Choose the Activity-specific Group for this action.",
    )


def choose_membership(
    memberships: Sequence[MembershipSummary],
    *,
    title: str,
) -> MembershipSummary:
    return select_one(
        title,
        memberships,
        [
            (
                item.participant_display_label
                or item.participant_reference.participant_id
            )
            + " "
            f"in {item.group_id} - {item.status}"
            for item in memberships
        ],
        help_text="Choose the historical Membership record to change.",
    )


def choose_student(root: Path, class_id: str) -> StudentRecord:
    roster = load_class_roster(root, class_id)
    students = tuple(sorted(roster.students, key=student_sort_name))
    return select_one(
        "Choose a Student",
        students,
        [f"{student_display_name(item)} ({item.student_id})" for item in students],
        help_text=(
            "Students come from the Core-owned class roster; Concord does not copy it."
        ),
    )


def choose_students(root: Path, class_id: str) -> tuple[StudentRecord, ...]:
    roster = load_class_roster(root, class_id)
    students = tuple(sorted(roster.students, key=student_sort_name))
    return select_many(
        "Choose Students",
        students,
        [f"{student_display_name(item)} ({item.student_id})" for item in students],
        help_text=(
            "Select one or more Core roster students for the same Group context."
        ),
    )


def choose_effective_context(
    activity_id: str,
    sessions: Sequence[SessionSummary],
) -> EffectiveContext:
    """Choose a compact common Effective Context for an assignment."""
    ordered = tuple(sorted(sessions, key=lambda item: (item.sequence, item.session_id)))
    if not ordered:
        raise ConcordWorkflowValidationError("At least one Session is required.")
    while True:
        clear_screen()
        print_menu_header("Effective Context")
        print("1. One Session")
        print("2. Several selected Sessions")
        print("3. From a Session through the remaining Activity")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Effective Context Help")
            print(
                "Context records when this Membership, Role, or Responsibility applies."
            )
            print("Later assignment changes do not rewrite earlier Session context.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            selected_session = choose_session(ordered)
            return EffectiveContext(
                activity_id=activity_id,
                session_ids=(selected_session.session_id,),
            )
        if raw == "2":
            selected_sessions = select_many(
                "Choose Sessions",
                ordered,
                [
                    f"{item.sequence}. {item.label or item.session_id} - {item.status}"
                    for item in ordered
                ],
                help_text="Select every Session where this assignment applies.",
            )
            return EffectiveContext(
                activity_id=activity_id,
                session_ids=tuple(item.session_id for item in selected_sessions),
            )
        if raw == "3":
            starting_session = choose_session(
                ordered, title="Choose the Starting Session"
            )
            remaining = tuple(
                item for item in ordered if item.sequence >= starting_session.sequence
            )
            return EffectiveContext(
                activity_id=activity_id,
                session_ids=tuple(item.session_id for item in remaining),
                sequence_start=starting_session.sequence,
                applies_to_remaining_activity=True,
            )
        print(navigation_hint_with_help())
        pause_for_user()


def slug_identifier(value: str, fallback: str) -> str:
    """Create a Core-compatible identifier proposal from teacher-facing text."""
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip()).strip("-_").lower()
    return slug or fallback


def load_menu_standards_library(root: Path | None = None) -> StandardsLibrary | None:
    workspace = resolve_workspace_root() if root is None else root
    path = standards_library_path(workspace)
    if not path.is_file():
        return None
    return load_standards_library(path)


def choose_standards_profile(library: StandardsLibrary) -> StandardsProfile:
    profiles = library.profiles
    return select_one(
        "Choose a Standards Profile",
        profiles,
        [item.title or item.profile_id for item in profiles],
        help_text=(
            "A profile is the Core-owned set from which Focus Standards are chosen."
        ),
    )


def choose_focus_standards(
    library: StandardsLibrary,
    profile: StandardsProfile,
) -> tuple[str, ...]:
    by_id = {item.standard_id: item for item in library.standards}
    available = tuple(
        by_id[standard_id]
        for standard_id in profile.standards
        if standard_id in by_id and by_id[standard_id].active
    )
    if not available:
        raise ConcordWorkflowValidationError(
            "The selected standards profile has no active standards."
        )
    selected: list[StandardDefinition] = []
    remaining = list(available)
    page_index = 0
    while remaining:
        pages = page_count(len(remaining))
        page_index = min(page_index, pages - 1)
        visible = page_items(remaining, page_index)
        clear_screen()
        print_menu_header("Choose Focus Standards")
        if selected:
            print("Selected: " + ", ".join(item.code for item in selected))
            print()
        print("Choose another Focus Standard, or D when done.")
        for index, item in enumerate(visible, start=1):
            print(f"{index}. {item.code} - {item.short_name}")
        if pages > 1:
            print()
            print(f"Page {page_index + 1} of {pages}")
            if page_index + 1 < pages:
                print("N. Next page")
            if page_index > 0:
                print("P. Previous page")
        print("D. Done")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Focus Standards Help")
            print("Choose one to four standards that will govern this Activity.")
            print("Selection order is preserved.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        normalized = raw.casefold()
        if normalized == "d":
            if selected:
                return tuple(item.standard_id for item in selected)
            continue
        if normalized == "n" and page_index + 1 < pages:
            page_index += 1
            continue
        if normalized == "p" and page_index > 0:
            page_index -= 1
            continue
        if raw.isdigit():
            index = int(raw) - 1
            if 0 <= index < len(visible) and len(selected) < 4:
                chosen = visible[index]
                selected.append(chosen)
                remaining.remove(chosen)
                continue
        print("Choose a listed standard or D when done.")
        pause_for_user()
    return tuple(item.standard_id for item in selected)
