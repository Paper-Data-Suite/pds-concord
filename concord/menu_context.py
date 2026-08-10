"""In-memory state for one launched Concord teacher-menu session."""

from __future__ import annotations

from dataclasses import dataclass

from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    parse_menu_navigation,
)
from concord.menu_ui import clear_screen, pause_for_user, print_menu_header
from concord.workflows import WorkflowActor


class CancelMenuAction(Exception):
    """Cancel the current form and return to its parent menu."""


@dataclass(slots=True)
class MenuSessionContext:
    """Ephemeral teacher-menu state; nothing here is persisted as credentials."""

    actor: WorkflowActor | None = None

    def require_actor(self) -> WorkflowActor:
        """Collect one authorized actor identity and reuse it for this process."""
        if self.actor is not None:
            return self.actor
        while True:
            clear_screen()
            print_menu_header("Teacher Identity")
            print("Enter the authorized actor ID to record action provenance.")
            print("This identifies who made the change; it is not authentication.")
            print()
            print("H. Help")
            print("B. Back")
            print("M. Main Menu")
            print("Q. Quit")
            print()
            raw = input("Actor ID: ").strip()
            navigation = parse_menu_navigation(raw)
            if navigation is ConcordMenuChoice.HELP:
                clear_screen()
                print_menu_header("Teacher Identity Help")
                print(
                    "Use a stable identifier for the authorized adult making changes."
                )
                print("Do not use a student's ID or enter a password or other secret.")
                print()
                pause_for_user()
                continue
            if navigation is NavigationChoice.BACK:
                raise CancelMenuAction
            if not raw:
                continue
            try:
                actor = WorkflowActor(actor_id=raw)
            except ValueError as error:
                clear_screen()
                print_menu_header("Teacher Identity")
                print(f"Actor ID is invalid: {error}")
                print()
                pause_for_user()
                continue
            self.actor = actor
            return actor
