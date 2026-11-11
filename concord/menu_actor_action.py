"""Prompt-scoped, one-operation actor review; no sticky override state.

No globally intercepted keystrokes, Notes permissions, or stored actor overrides.
Only callers that deliberately use this helper offer the Advanced option.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    parse_menu_navigation,
)
from concord.menu_prompts import prompt_text, show_result
from concord.menu_ui import clear_screen, print_menu_header, print_navigation
from concord.teacher_attribution import (
    TeacherAttributionIdentity,
    TeacherAttributionValidationError,
)
from concord.workflows import WorkflowActor

LegacyConfirm = Callable[[str, str, Sequence[str]], bool]
_PreparedT = TypeVar("_PreparedT")


def _choose_temporary_actor() -> TeacherAttributionIdentity:
    name = prompt_text(
        "Alternate Actor — This Action Only",
        "Attribution display name",
        help_text=(
            "Enter the adult's recorded name for this one reviewed action. "
            "This is not authentication or permission."
        ),
    )
    if name is None:
        raise CancelMenuAction
    actor_id = prompt_text(
        "Alternate Actor — This Action Only",
        "Exact stable actor ID",
        help_text=(
            "Enter an existing Core-valid actor ID known to the teacher. "
            "This is not a new login or a change to the saved default."
        ),
    )
    if actor_id is None:
        raise CancelMenuAction
    return TeacherAttributionIdentity(actor_id, name, "temporary")


def confirm_actor_write(
    title: str,
    expected: str,
    lines: Sequence[str],
    *,
    state: MenuSessionContext,
    legacy_confirm: LegacyConfirm,
    review_lines: Callable[[WorkflowActor], Sequence[str]] | None = None,
) -> WorkflowActor | None:
    """Return a *reviewed* actor for this operation or None on cancellation.

    The existing legacy helper is retained for older explicit session callers,
    without adding an actor prompt to unrelated tests/direct commands.
    A provider-backed teacher sees one normal substantive confirmation plus
    an opt-in Advanced actor choice in that very same review screen.
    """
    if getattr(state, "attribution_provider", None) is None:
        rendered = (
            lines if review_lines is None else review_lines(state.require_actor())
        )
        if not legacy_confirm(title, expected, rendered):
            return None
        return state.require_actor()

    # Bind this pending review to the exact saved profile fingerprint. A
    # concurrent change must abort, not silently change the recorded actor.
    state.actor_for_action(action_label=title)
    alternate: TeacherAttributionIdentity | None = None
    while True:
        actor = state.actor_for_action(action_label=title, alternate=alternate)
        clear_screen()
        print_menu_header(title)
        for line in lines if review_lines is None else review_lines(actor):
            print(line)
        print()
        print(f"Recorded by: {actor.display_label or actor.actor_id}")
        print(f"Actor ID: {actor.actor_id}")
        print("Actor attribution is self-declared, not authentication.")
        if alternate is not None:
            print("Attribution: temporary for THIS action; no default changed.")
            print("D. Use saved default instead")
        print("A. Advanced: use another actor for this action")
        print(f"Type {expected} to confirm, or press Enter to cancel.")
        print_navigation()
        print()
        raw = input("Confirmation: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Action Attribution Help",
                (
                    "The confirmed action stores the reviewed Actor ID and label.",
                    "A selects a temporary actor only for this exact review.",
                    "D restores the saved default for this review.",
                    "Back or Enter cancels with no action write.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK or not raw:
            return None
        if raw.casefold() == "a":
            try:
                alternate = _choose_temporary_actor()
            except CancelMenuAction:
                return None
            except TeacherAttributionValidationError as error:
                show_result(
                    "Invalid Alternate Actor",
                    (str(error), "No action was recorded; review again."),
                )
            continue
        if raw.casefold() == "d" and alternate is not None:
            alternate = None
            continue
        if raw.casefold() == expected.casefold():
            # Revalidate AFTER the substantive review and before the guarded
            # service call. This returns a fresh value, never a queued override.
            return state.actor_for_action(action_label=title, alternate=alternate)
        show_result(
            "Confirmation Not Accepted",
            ("No action recorded; use the displayed confirmation or Back.",),
        )


def confirm_prepared_actor_write(
    title: str,
    expected: str,
    *,
    state: MenuSessionContext,
    legacy_confirm: LegacyConfirm,
    prepare_for_actor: Callable[[WorkflowActor], tuple[_PreparedT, Sequence[str]]],
) -> _PreparedT | None:
    """Reprepare and review the exact request for each selected actor.

    The digest and request remain paired through alternate/default toggles.
    Cancellation never exposes a prepared request for commitment.
    """
    latest: tuple[WorkflowActor, _PreparedT] | None = None

    def render(actor: WorkflowActor) -> Sequence[str]:
        nonlocal latest
        pending, lines = prepare_for_actor(actor)
        latest = actor, pending
        return lines

    actor = confirm_actor_write(
        title,
        expected,
        (),
        state=state,
        legacy_confirm=legacy_confirm,
        review_lines=render,
    )
    if actor is None:
        return None
    if latest is None or latest[0] != actor:
        raise RuntimeError(
            "Reviewed actor differs from prepared actor; no write attempted."
        )
    return latest[1]


__all__ = ["confirm_actor_write", "confirm_prepared_actor_write"]
