"""Bounded teacher-facing presentation for Concord Activity attention."""

from __future__ import annotations

from collections.abc import Callable

from concord.menu_context import MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
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
from concord.workflows.activity import show_activity
from concord.workflows.activity_attention import (
    ActivityAttentionSummary,
    list_activity_attention,
)
from concord.workflows.activity_lesson_readiness import (
    LessonReadiness,
    inspect_lesson_readiness_from_context,
)
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.models import ActivitySummary

ActivityAttentionActionRouter = Callable[
    [ActivitySummary, MenuSessionContext, str], None
]


def _task_label(summary: ActivityAttentionSummary) -> str:
    item = summary.next_item
    return "-" if item is None else item.task.title()


def _next_label(summary: ActivityAttentionSummary) -> str:
    item = summary.next_item
    return "No current teacher attention" if item is None else item.label


def print_activity_attention_summary(summary: ActivityAttentionSummary) -> None:
    """Print one compact opened-Activity attention summary.

    Only the deterministic next fact is expanded. Other categories are reported
    as a category count so the opened Activity screen remains bounded and does
    not add together heterogeneous count units.
    """
    print("Attention")
    next_item = summary.next_item
    if next_item is None:
        print("No current teacher attention.")
        print()
        return

    print(
        f"Next: {next_item.task.title()} - {next_item.label} (count {next_item.count})"
    )
    remaining = len(summary.items) - 1
    if remaining:
        suffix = "category" if remaining == 1 else "categories"
        print(f"Also: {remaining} other attention {suffix}")
    print()


def _selection_hint(page_index: int, pages: int) -> str:
    commands: list[str] = []
    if page_index + 1 < pages:
        commands.append("N")
    if page_index > 0:
        commands.append("P")
    commands.extend(("H", "B", "M", "Q"))
    if len(commands) == 1:
        suffix = commands[0]
    elif len(commands) == 2:
        suffix = f"{commands[0]} or {commands[1]}"
    else:
        suffix = ", ".join(commands[:-1]) + f", or {commands[-1]}"
    return f"Please choose a listed option, {suffix}."


def _help() -> None:
    clear_screen()
    print_menu_header("Attention Needed Help")
    print("This screen lists Activities with current mechanically observable")
    print("teacher attention. It does not rank urgency, students, or Activities.")
    print("Choosing an Activity opens its deterministic next existing task menu.")
    print()
    pause_for_user()


def launch_activity_attention_discovery(
    state: MenuSessionContext,
    *,
    route_action: ActivityAttentionActionRouter,
) -> None:
    """Browse current Activity attention without creating canonical task state."""
    page_index = 0
    while True:
        try:
            summaries = tuple(item for item in list_activity_attention() if item.items)
        except Exception:
            clear_screen()
            print_menu_header("Attention Needed")
            print("Concord attention could not be loaded safely.")
            print()
            pause_for_user()
            return

        if not summaries:
            clear_screen()
            print_menu_header("Attention Needed")
            print("No Concord Activities currently need teacher attention.")
            print()
            pause_for_user()
            return

        pages = page_count(len(summaries))
        page_index = min(page_index, pages - 1)
        clear_screen()
        print_menu_header("Attention Needed")
        page = page_items(summaries, page_index)
        for index, summary in enumerate(page, start=1):
            print(
                f"{index}. {summary.title} ({summary.class_id}) - "
                f"{_task_label(summary)}: {_next_label(summary)}"
            )
        if pages > 1:
            print()
            print(f"Page {page_index + 1} of {pages}")
            if page_index + 1 < pages:
                print("N. Next page")
            if page_index > 0:
                print("P. Previous page")
        print_navigation()
        print()

        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _help()
            continue
        if navigation is NavigationChoice.BACK:
            return
        normalized = choice.casefold()
        if normalized == "n" and page_index + 1 < pages:
            page_index += 1
            continue
        if normalized == "p" and page_index > 0:
            page_index -= 1
            continue
        if choice.isdigit():
            selected = int(choice)
            if 1 <= selected <= len(page):
                summary = page[selected - 1]
                next_item = summary.next_item
                assert next_item is not None
                try:
                    activity = show_activity(
                        summary.class_id,
                        summary.activity_id,
                    ).summary
                except Exception:
                    clear_screen()
                    print_menu_header("Attention Needed")
                    print("The selected Activity could not be loaded safely.")
                    print()
                    pause_for_user()
                    continue
                route_action(activity, state, next_item.action_id)
                continue
        print(_selection_hint(page_index, pages))
        pause_for_user()


def _read_only_return(*, prompt: str) -> bool:
    """Recognize Core B/M/Q and Concord H without introducing write routes."""
    try:
        choice = input(prompt).strip()
    except EOFError:
        return True
    navigation = parse_menu_navigation(choice)
    if navigation is NavigationChoice.BACK:
        return True
    if navigation is ConcordMenuChoice.HELP:
        print("These are read-only Concord snapshot facts, not teacher tasks.")
        print("B returns; M and Q retain their normal navigation meanings.")
        return False
    print("Enter B to return or H for help.")
    return False


def print_lesson_readiness(report: LessonReadiness) -> None:
    """Present only source-backed preparation facts, with physical unknowns."""
    print(f"Activity snapshot: {report.snapshot_revision}")
    if report.plan_stage == "current_operational":
        print(
            "Plan: current applied GroupPlan verified against Core roster "
            f"({report.operational_group_count} Clusters)."
        )
        if report.unused_proposal_count:
            print(
                f"Optional: {report.unused_proposal_count} alternative GroupPlan "
                "proposal(s); inspect/cancel under Plan."
            )
    elif report.plan_stage == "applied_needs_inspection":
        print("Plan: historical applied GroupPlan needs current-placement inspection.")
    elif report.plan_stage == "proposals_only":
        print("Plan: no current applied GroupPlan is verified.")
    else:
        print("Plan: no GroupPlan is recorded; manual Groups may be separate.")
    if report.pending_proposal_count:
        print(f"Plan proposals needing inspection: {report.pending_proposal_count}")
    print(
        f"Packets generated: {report.generated_packet_count}; "
        f"still preparing: {report.pending_packet_count}; "
        f"need recovery: {report.recovery_packet_count}."
    )
    print("Printing/distribution: not verified by this status view.")
    print(
        "Return records: "
        f"{report.routed_return_artifact_count} Artifact(s) have routed page "
        "references; "
        f"{report.expected_without_routed_return_count} expected-return "
        "Artifact(s) have none."
    )
    if report.optional_return_artifact_count:
        print(
            f"Optional work without routed returns: "
            f"{report.optional_return_artifact_count} Artifact(s)."
        )
    print("Routed references do not by themselves verify physical source custody.")
    print("Review, Score, Share and teacher decisions are not inferred here.")
    print("This inspection does not change classroom records.")


def launch_activity_prelesson_readiness(
    context: ActivityReadContext | None,
) -> None:
    """Inspect current opened-Activity context without any write operations."""
    clear_screen()
    print_menu_header("Before class - lesson readiness")
    if context is None:
        print("Lesson readiness unavailable: current Activity could not be loaded.")
    else:
        try:
            report = inspect_lesson_readiness_from_context(context)
        except Exception:
            # The teacher view must not leak student data or local file paths.
            print("Lesson readiness unavailable: source inspection was incomplete.")
        else:
            print_lesson_readiness(report)
    print()
    while True:
        print_navigation()
        if _read_only_return(prompt="Select B to return: "):
            return


def launch_activity_attention_details(
    summary: ActivityAttentionSummary | None,
) -> None:
    """Page through all current attention categories; no implicit owner route."""
    page_index = 0
    while True:
        clear_screen()
        print_menu_header("All Activity attention categories")
        if summary is None:
            print("Attention unavailable: the Activity could not be inspected safely.")
            print()
            print_navigation()
            if _read_only_return(prompt="Select B to return: "):
                return
            continue
        items = summary.items
        if not items:
            print("No current actionable Concord attention categories.")
            print("This does not prove that physical returns or Scores exist.")
        else:
            pages = page_count(len(items))
            page_index = min(page_index, pages - 1)
            for item in page_items(items, page_index):
                print(f"{item.task.title()}: {item.label} (count {item.count})")
            if pages > 1:
                print(f"Page {page_index + 1} of {pages}")
                if page_index + 1 < pages:
                    print("N. Next page")
                if page_index > 0:
                    print("P. Previous page")
        print("Open the owning Plan/Prepare/Collect/Review/Score/Share menu to act.")
        print("Categories are not ranked by urgency; counts are not additive.")
        print_navigation()
        try:
            choice = input("Select an option: ").strip()
        except EOFError:
            return
        nav = parse_menu_navigation(choice)
        if nav is NavigationChoice.BACK:
            return
        if nav is ConcordMenuChoice.HELP:
            print("This view is read-only. Use N/P to page and B to return.")
            continue
        if (
            items
            and choice.casefold() == "n"
            and page_index + 1 < page_count(len(items))
        ):
            page_index += 1
            continue
        if items and choice.casefold() == "p" and page_index > 0:
            page_index -= 1
            continue
        print("Use N/P for pages, B to return, or H for help.")


__all__ = [
    "ActivityAttentionActionRouter",
    "launch_activity_attention_details",
    "launch_activity_attention_discovery",
    "launch_activity_prelesson_readiness",
    "print_activity_attention_summary",
    "print_lesson_readiness",
]
