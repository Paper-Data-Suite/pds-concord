"""In-memory state for one launched Concord teacher-menu session."""

from __future__ import annotations

from dataclasses import dataclass

from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    parse_menu_navigation,
)
from concord.menu_ui import clear_screen, pause_for_user, print_menu_header
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    TeacherAttributionError,
)
from concord.workflows import WorkflowActor


class CancelMenuAction(Exception):
    """Cancel the current form and return to its parent menu."""


@dataclass(slots=True)
class MenuSessionContext:
    """Ephemeral menu state, optionally backed by local *attribution*, not login."""

    actor: WorkflowActor | None = None
    attribution_provider: ConcordTeacherAttributionProvider | None = None
    actor_fingerprint: str | None = None

    def invalidate_actor(self) -> None:
        """Drop a cached default after Settings/workspace changes, not history."""
        self.actor = None
        self.actor_fingerprint = None

    def require_actor(self) -> WorkflowActor:
        """Resolve a concrete actor without treating it as authorization.

        An injected provider makes normal menu writes use the explicitly saved
        local preference. Without one, preserve the legacy *test/explicit*
        session and standalone caller semantics until those callers adopt the
        provider via ``new_menu_session``.
        """
        if self.attribution_provider is not None:
            try:
                identity, fingerprint = (
                    self.attribution_provider.resolve_with_fingerprint()
                )
            except TeacherAttributionError as error:
                self.invalidate_actor()
                raise CancelMenuAction(
                    f"Concord teacher attribution is unavailable: {error} "
                    "Open Teacher Settings to inspect or configure it. "
                    "No actor-attributed action was recorded."
                ) from error
            if self.actor is not None:
                if self.actor_fingerprint != fingerprint:
                    self.invalidate_actor()
                    raise CancelMenuAction(
                        "Teacher attribution changed since it was selected. "
                        "Review the current profile and the intended action "
                        "before trying again; no new action was recorded."
                    )
                return self.actor
            self.actor = identity.workflow_actor()
            self.actor_fingerprint = fingerprint
            return self.actor

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


def new_menu_session() -> MenuSessionContext:
    """Create a fresh provider-backed *interactive* session, without I/O."""
    return MenuSessionContext(
        attribution_provider=ConcordTeacherAttributionProvider(
            ConcordTeacherAttributionStore()
        )
    )
