"""Concord-local Teacher Settings, without authentication or academic writes."""

from __future__ import annotations

import uuid

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    parse_menu_navigation,
)
from concord.menu_prompts import confirm_write, prompt_text, show_result
from concord.menu_ui import (
    clear_screen,
    print_menu_header,
    print_navigation,
)
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    StoredTeacherAttribution,
    TeacherAttributionError,
    TeacherAttributionIdentity,
)


def _provider(state: MenuSessionContext) -> ConcordTeacherAttributionProvider:
    if state.attribution_provider is None:
        state.attribution_provider = ConcordTeacherAttributionProvider(
            ConcordTeacherAttributionStore()
        )
    return state.attribution_provider


def _safe_load(
    provider: ConcordTeacherAttributionProvider,
) -> StoredTeacherAttribution | None:
    return provider.store.load()


def _show_status(provider: ConcordTeacherAttributionProvider) -> None:
    current = _safe_load(provider)
    if current is None:
        lines: tuple[str, ...] = (
            "Status: not configured",
            "No Concord attribution profile is saved for this OS user.",
            "Use first-time setup before authoring with a saved default.",
        )
    else:
        lines = (
            "Status: ready",
            f"Recorded by: {current.profile.display_name}",
            f"Actor ID: {current.profile.actor_id}",
            f"Profile revision: {current.profile.revision}",
        )
    show_result(
        "My Concord Attribution",
        (
            *lines,
            "Scope: Concord-local self-declared attribution preference.",
            "Not login, evidence permission or Core Notes ownership.",
            "Stored outside the classroom workspace and its ordinary backup.",
            "A different OS user/device does not inherit this preference.",
        ),
    )


def _ask_name(*, previous: str | None = None) -> str:
    name = prompt_text(
        "My Concord Attribution",
        "Teacher name for recorded attribution",
        help_text=(
            "Enter the human-readable name to appear in *future* Concord "
            "record attribution. It does not authenticate anyone."
        ),
        default=previous,
    )
    if name is None:
        raise CancelMenuAction
    return name


def _choose_actor_id(name: str) -> str:
    """Choose a reviewed actor ID before any durable storage mutation."""
    while True:
        clear_screen()
        print_menu_header("Choose Attribution ID")
        print(f"Teacher: {name}")
        print("1. Generate a new stable actor ID")
        print("2. Use a known existing actor ID (Advanced)")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        nav = parse_menu_navigation(raw)
        if nav is ConcordMenuChoice.HELP:
            show_result(
                "Actor ID Help",
                (
                    "An actor ID is a stable record attribution key, not a login.",
                    "Choose an existing value only if you know it is correct.",
                    "Changing a saved ID affects future records, never history.",
                ),
            )
            continue
        if nav is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            actor_id = "teacher-" + uuid.uuid4().hex
        elif raw == "2":
            entered = prompt_text(
                "Existing Attribution ID",
                "Exact actor ID",
                help_text=(
                    "Use an existing Core-valid actor ID to preserve the intended "
                    "historical record identity. This does not prove identity."
                ),
            )
            if entered is None:
                raise CancelMenuAction
            actor_id = entered
        else:
            continue
        # Pure validation, no preference/academic file modification.
        TeacherAttributionIdentity(actor_id, name, "temporary")
        return actor_id


def _setup(
    state: MenuSessionContext, provider: ConcordTeacherAttributionProvider
) -> None:
    if _safe_load(provider) is not None:
        show_result(
            "Already Configured",
            ("Inspect or deliberately edit the existing attribution profile.",),
        )
        return
    name = _ask_name()
    actor_id = _choose_actor_id(name)
    if not confirm_write(
        "Save Concord Attribution",
        "SAVE PROFILE",
        (
            f"Recorded by: {name}",
            f"Stable actor ID: {actor_id}",
            "Scope: Concord on this local OS-user profile, not shared PDS login.",
            "No academic records or Core/Meridian settings will be changed.",
        ),
    ):
        return
    saved = provider.store.create(name, actor_id=actor_id)
    state.invalidate_actor()
    show_result(
        "Concord Attribution Saved",
        (
            f"Recorded by: {saved.profile.display_name}",
            f"Actor ID: {saved.profile.actor_id}",
            f"Profile revision: {saved.profile.revision}",
            "Future ordinary Concord menu actions will use this default.",
        ),
    )


def _rename(
    state: MenuSessionContext, provider: ConcordTeacherAttributionProvider
) -> None:
    current = _safe_load(provider)
    if current is None:
        show_result("Profile Not Configured", ("Use first-time setup instead.",))
        return
    name = _ask_name(previous=current.profile.display_name)
    if name == current.profile.display_name:
        show_result("No Change", ("The teacher name is unchanged.",))
        return
    if not confirm_write(
        "Rename Concord Attribution",
        "RENAME",
        (
            f"Current name: {current.profile.display_name}",
            f"Requested name: {name}",
            f"Stable actor ID unchanged: {current.profile.actor_id}",
            "Only future attribution labels change; historical records remain.",
        ),
    ):
        return
    saved = provider.store.update_display_name(current, name)
    state.invalidate_actor()
    show_result(
        "Teacher Attribution Updated",
        (
            f"Recorded by: {saved.profile.display_name}",
            f"Stable actor ID: {saved.profile.actor_id}",
            f"Profile revision: {saved.profile.revision}",
            "Existing Concord records were not rewritten.",
        ),
    )


def _replace(
    state: MenuSessionContext, provider: ConcordTeacherAttributionProvider
) -> None:
    current = _safe_load(provider)
    if current is None:
        show_result("Profile Not Configured", ("Use first-time setup instead.",))
        return
    name = _ask_name(previous=current.profile.display_name)
    actor_id = _choose_actor_id(name)
    if actor_id == current.profile.actor_id:
        show_result(
            "Same Actor ID",
            ("Use Rename to change only the displayed name.",),
        )
        return
    if not confirm_write(
        "Replace Concord Actor Identity",
        "REPLACE ID",
        (
            f"Old: {current.profile.display_name} ({current.profile.actor_id})",
            f"New: {name} ({actor_id})",
            "New actor identity applies to FUTURE actions only.",
            "Old immutable provenance is preserved exactly.",
            "This action does not grant access or private Notes ownership.",
        ),
    ):
        return
    saved = provider.store.replace_identity(
        current, display_name=name, actor_id=actor_id, confirmed=True
    )
    state.invalidate_actor()
    show_result(
        "Actor Identity Replaced",
        (
            f"New default: {saved.profile.display_name}",
            f"New actor ID: {saved.profile.actor_id}",
            "Previous records keep their existing actor identities.",
        ),
    )


def _reset(
    state: MenuSessionContext, provider: ConcordTeacherAttributionProvider
) -> None:
    current = _safe_load(provider)
    if current is None:
        show_result("No Profile", ("There is no saved preference to reset.",))
        return
    if not confirm_write(
        "Reset Concord Attribution",
        "RESET PROFILE",
        (
            f"Saved default: {current.profile.display_name}",
            f"Saved actor ID: {current.profile.actor_id}",
            "Removes only this Concord-local preference after confirmation.",
            "Core workspace, Meridian settings and Concord records stay intact.",
        ),
    ):
        return
    provider.store.reset(current, confirmed=True)
    state.invalidate_actor()
    show_result(
        "Concord Default Reset",
        ("The local attribution preference was cleared. Records remain intact.",),
    )


def launch_teacher_settings_menu(state: MenuSessionContext) -> None:
    """Inspect/change only Concord attribution, with explicit save/review."""
    provider = _provider(state)
    while True:
        clear_screen()
        print_menu_header("Teacher Settings — Concord Attribution")
        print("1. Show saved attribution and scope")
        print("2. First-time setup")
        print("3. Edit displayed teacher name")
        print("4. Advanced: change stable actor ID")
        print("5. Advanced: reset saved attribution")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Teacher Attribution Help",
                (
                    "Concord remembers a self-declared actor name and stable ID.",
                    "It is not authentication or Core Notes ownership.",
                    "Direct noninteractive CLI still requires explicit --actor-id.",
                    "Use Settings to inspect/replace or reset the local default.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            return
        actions = {
            "1": lambda: _show_status(provider),
            "2": lambda: _setup(state, provider),
            "3": lambda: _rename(state, provider),
            "4": lambda: _replace(state, provider),
            "5": lambda: _reset(state, provider),
        }
        action = actions.get(choice)
        if action is None:
            continue
        try:
            action()
        except CancelMenuAction:
            # B cancels the current form, never the entire saved profile.
            continue
        except TeacherAttributionError as error:
            show_result(
                "Concord Attribution Unavailable",
                (
                    str(error),
                    "Check Show current before retrying; the save "
                    "outcome may be uncertain.",
                    "Inspect the existing profile or return safely.",
                ),
            )


__all__ = ["launch_teacher_settings_menu"]
