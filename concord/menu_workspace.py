"""Teacher-facing workspace settings with explicit write confirmation."""

from __future__ import annotations

from pathlib import Path

from pds_core.workspace import (
    WorkspaceRootError,
    clear_saved_workspace_root,
    ensure_workspace_root,
    inspect_workspace_root,
    resolve_workspace_root,
    save_workspace_root,
)

from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)


def _help() -> None:
    clear_screen()
    print_menu_header("Workspace Help")
    print("Core owns the shared Paper Data Suite workspace.")
    print("Concord uses Core's explicit/environment/saved/default resolution order.")
    print("Changing the saved workspace never moves or deletes existing files.")
    print()
    pause_for_user()


def _show() -> None:
    clear_screen()
    print_menu_header("Current Workspace")
    try:
        status = inspect_workspace_root()
    except WorkspaceRootError as error:
        print(f"Workspace status could not be loaded: {error}")
    else:
        print(f"Path: {status.root}")
        print(f"Source: {status.source}")
        print(f"Exists: {'yes' if status.exists else 'no'}")
        print(f"Writable: {'yes' if status.is_writable else 'no'}")
    print()
    pause_for_user()


def _confirm(label: str, expected: str) -> bool:
    print()
    print(f"Type {expected} to confirm, or press Enter to cancel.")
    return input(f"{label}: ").strip().casefold() == expected.casefold()


def _set_workspace() -> None:
    clear_screen()
    print_menu_header("Set Workspace Folder")
    print("Enter the folder to create/validate and save as the PDS workspace.")
    print("Press Enter to cancel.")
    print()
    raw = input("Workspace folder: ").strip()
    if not raw:
        return
    path = Path(raw).expanduser()
    clear_screen()
    print_menu_header("Set Workspace Folder")
    print(f"Folder: {path}")
    if not _confirm("Confirmation", "SET"):
        return
    clear_screen()
    print_menu_header("Workspace Result")
    try:
        root = ensure_workspace_root(path)
        saved = save_workspace_root(root)
    except WorkspaceRootError as error:
        print(f"Workspace was not changed: {error}")
    else:
        print(f"Saved workspace: {saved}")
        print("Existing Paper Data Suite files were not moved.")
    print()
    pause_for_user()


def _validate_workspace() -> None:
    clear_screen()
    print_menu_header("Validate Workspace")
    try:
        root = resolve_workspace_root()
    except WorkspaceRootError as error:
        print(f"Workspace could not be resolved: {error}")
        print()
        pause_for_user()
        return
    print(f"Resolved folder: {root}")
    if not _confirm("Confirmation", "VALIDATE"):
        return
    clear_screen()
    print_menu_header("Workspace Result")
    try:
        validated = ensure_workspace_root(root)
    except WorkspaceRootError as error:
        print(f"Workspace validation failed: {error}")
    else:
        print(f"Workspace validated: {validated}")
    print()
    pause_for_user()


def _reset_workspace() -> None:
    clear_screen()
    print_menu_header("Reset Saved Workspace")
    print("This clears only the saved workspace preference.")
    print("No workspace files will be deleted.")
    if not _confirm("Confirmation", "RESET"):
        return
    clear_screen()
    print_menu_header("Workspace Result")
    try:
        cleared = clear_saved_workspace_root()
    except WorkspaceRootError as error:
        print(f"Saved workspace preference was not changed: {error}")
    else:
        if cleared:
            print("Saved workspace preference cleared.")
        else:
            print("No saved workspace preference was set.")
        print("No workspace files were deleted.")
    print()
    pause_for_user()


def launch_workspace_menu() -> None:
    """Run the low-density teacher workspace menu."""
    while True:
        clear_screen()
        print_menu_header("Workspace Settings")
        print("1. Show current workspace")
        print("2. Set workspace folder")
        print("3. Validate/create current workspace")
        print("4. Reset saved workspace preference")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _help()
            continue
        if navigation is NavigationChoice.BACK:
            return
        if choice == "1":
            _show()
        elif choice == "2":
            _set_workspace()
        elif choice == "3":
            _validate_workspace()
        elif choice == "4":
            _reset_workspace()
        else:
            print(navigation_hint_with_help())
            pause_for_user()
