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
        f"Next: {next_item.task.title()} - {next_item.label} "
        f"(count {next_item.count})"
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
            summaries = tuple(
                item for item in list_activity_attention() if item.items
            )
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


__all__ = [
    "ActivityAttentionActionRouter",
    "launch_activity_attention_discovery",
    "print_activity_attention_summary",
]
