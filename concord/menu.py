"""Teacher-facing menu entry point for Concord."""

from __future__ import annotations

from concord.menu_activity import (
    launch_activity_context_menu,
    launch_activity_management_menu,
    select_activity,
)
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    QuitPDS,
    ReturnToMainMenu,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_packet import launch_packet_library_menu
from concord.menu_presets import launch_preset_library_menu
from concord.menu_scan import launch_scan_routing_menu
from concord.menu_template import launch_template_library_menu
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.menu_workspace import launch_workspace_menu


def _main_help() -> None:
    clear_screen()
    print_menu_header("Help")
    print("Concord manages paper-first collaborative classroom evidence.")
    print("Activity, Session, Group, Role, and Responsibility records remain distinct.")
    print("Teacher judgment remains primary; Concord does not calculate Grades.")
    print()
    print("Complete direct command help:")
    print("  concord --help")
    print()
    pause_for_user()


def _main_menu_once(state: MenuSessionContext) -> bool:
    clear_screen()
    print_menu_header()
    print("1. Activity Management")
    print("2. Open an Activity")
    print("3. Workspace Settings")
    print("4. Scan Routing")
    print("5. Template Library")
    print("6. Packet Library")
    print("7. Reusable Presets")
    print_navigation(back=False, main_menu=False)
    print()
    choice = input("Select an option: ").strip()
    navigation = parse_menu_navigation(
        choice,
        allow_back=False,
        allow_main_menu=False,
    )
    if navigation is ConcordMenuChoice.HELP:
        _main_help()
        return True
    if choice == "1":
        launch_activity_management_menu(state)
        return True
    if choice == "2":
        activity = select_activity()
        if activity is not None:
            launch_activity_context_menu(activity, state)
        return True
    if choice == "3":
        launch_workspace_menu()
        return True
    if choice == "4":
        launch_scan_routing_menu(state)
        return True
    if choice == "5":
        launch_template_library_menu(state)
        return True
    if choice == "6":
        launch_packet_library_menu(state)
        return True
    if choice == "7":
        launch_preset_library_menu(state)
        return True
    print(
        navigation_hint_with_help(
            back=False,
            main_menu=False,
        )
    )
    pause_for_user()
    return True


def launch_menu() -> int:
    """Launch Concord's menu and unwind B/M/Q/Ctrl+C/EOF cleanly."""
    state = MenuSessionContext()
    while True:
        try:
            _main_menu_once(state)
        except ReturnToMainMenu:
            continue
        except (QuitPDS, KeyboardInterrupt, EOFError):
            clear_screen()
            return 0
