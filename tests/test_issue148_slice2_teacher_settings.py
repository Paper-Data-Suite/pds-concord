"""#148 Slice 2: local settings, provider-backed menus and safe relaunch.

No real local configuration, classroom workspace, actor or student data used.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

import concord.menu as menu
import concord.menu_activity as activity_menu
import concord.menu_scan as scan_menu
import concord.menu_scoring as scoring_menu
import concord.menu_teacher_settings as settings
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
)
from concord.workflows import WorkflowActor


def _configured(tmp_path: Path) -> ConcordTeacherAttributionProvider:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    store.create("Dr. Ñ. Example", actor_id="teacher-ordinary")
    return ConcordTeacherAttributionProvider(store)


def _no_prompt(*_args: object, **_kwargs: object) -> str:
    raise AssertionError("Saved profile resolution may not prompt for actor ID")


def test_saved_actor_is_silent_across_new_menu_contexts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _configured(tmp_path)
    monkeypatch.setattr("builtins.input", _no_prompt)
    first = MenuSessionContext(attribution_provider=provider)
    a = first.require_actor()
    assert first.require_actor() is a
    assert a.actor_id == "teacher-ordinary"
    assert a.display_label == "Dr. Ñ. Example"
    assert a.owning_system == "concord"
    second = MenuSessionContext(attribution_provider=provider)
    b = second.require_actor()
    assert b.actor_id == a.actor_id
    assert b.display_label == a.display_label
    assert b is not a


def test_missing_profile_blocks_injected_write_without_writing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    monkeypatch.setattr("builtins.input", _no_prompt)
    session = MenuSessionContext(
        attribution_provider=ConcordTeacherAttributionProvider(store)
    )
    with pytest.raises(CancelMenuAction, match="Teacher Settings"):
        session.require_actor()
    assert not store.directory.exists()
    assert session.actor is None


def test_corrupt_profile_blocks_saved_actor_and_clears_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _configured(tmp_path)
    state = MenuSessionContext(attribution_provider=provider)
    monkeypatch.setattr("builtins.input", _no_prompt)
    assert state.require_actor().actor_id == "teacher-ordinary"
    path = provider.store.profile_path
    path.write_text("this isn't JSON", encoding="utf-8")
    with pytest.raises(CancelMenuAction, match="unavailable"):
        state.require_actor()
    assert state.actor is None
    assert state.actor_fingerprint is None


def test_external_profile_change_requires_new_review_before_actor_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _configured(tmp_path)
    state = MenuSessionContext(attribution_provider=provider)
    monkeypatch.setattr("builtins.input", _no_prompt)
    assert state.require_actor().display_label == "Dr. Ñ. Example"
    current = provider.store.load()
    assert current is not None
    provider.store.update_display_name(current, "Teacher Revised")
    with pytest.raises(CancelMenuAction, match="changed since"):
        state.require_actor()
    assert state.actor is None
    assert state.require_actor().display_label == "Teacher Revised"


def test_settings_first_use_requires_review_and_leaves_history_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    provider = ConcordTeacherAttributionProvider(store)
    state = MenuSessionContext(attribution_provider=provider)
    confirmations: list[tuple[str, str, tuple[str, ...]]] = []
    monkeypatch.setattr(settings, "_ask_name", lambda **_k: "Dr. Ñ. Example")
    monkeypatch.setattr(settings, "_choose_actor_id", lambda _n: "teacher-ordinary")
    monkeypatch.setattr(
        settings,
        "confirm_write",
        lambda title, expected, lines: (
            confirmations.append((title, expected, tuple(lines))) or True
        ),
    )
    monkeypatch.setattr(settings, "show_result", lambda *_args: None)
    settings._setup(state, provider)
    saved = store.load()
    assert saved is not None
    assert saved.profile.actor_id == "teacher-ordinary"
    assert saved.profile.display_name == "Dr. Ñ. Example"
    assert confirmations[0][1] == "SAVE PROFILE"
    assert "teacher-ordinary" in " ".join(confirmations[0][2])
    assert state.actor is None


def test_cancel_setup_does_not_create_preference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    provider = ConcordTeacherAttributionProvider(store)
    state = MenuSessionContext(attribution_provider=provider)
    monkeypatch.setattr(settings, "_ask_name", lambda **_k: "Example")
    monkeypatch.setattr(settings, "_choose_actor_id", lambda _n: "teacher-ordinary")
    monkeypatch.setattr(settings, "confirm_write", lambda *_args: False)
    settings._setup(state, provider)
    assert store.load() is None
    assert not store.directory.exists()


def test_rename_keeps_identity_and_refreshes_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _configured(tmp_path)
    state = MenuSessionContext(attribution_provider=provider)
    old = state.require_actor()
    monkeypatch.setattr(settings, "_ask_name", lambda **_k: "Teacher Revised")
    monkeypatch.setattr(settings, "confirm_write", lambda *_args: True)
    monkeypatch.setattr(settings, "show_result", lambda *_args: None)
    settings._rename(state, provider)
    current = provider.store.load()
    assert current is not None
    assert current.profile.actor_id == old.actor_id
    assert current.profile.display_name == "Teacher Revised"
    assert state.actor is None
    assert state.require_actor().actor_id == old.actor_id


def test_replace_is_future_only_and_reset_clears_only_concord(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = _configured(tmp_path)
    state = MenuSessionContext(attribution_provider=provider)
    old = state.require_actor()
    monkeypatch.setattr(settings, "_ask_name", lambda **_k: "Second Teacher")
    monkeypatch.setattr(settings, "_choose_actor_id", lambda _n: "teacher-second")
    monkeypatch.setattr(settings, "confirm_write", lambda *_args: True)
    monkeypatch.setattr(settings, "show_result", lambda *_args: None)
    settings._replace(state, provider)
    assert old.actor_id == "teacher-ordinary"
    assert state.require_actor().actor_id == "teacher-second"
    settings._reset(state, provider)
    assert provider.store.load() is None
    assert state.actor is None


def test_status_is_read_only_for_absent_preference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = ConcordTeacherAttributionProvider(
        ConcordTeacherAttributionStore(config_directory=tmp_path)
    )
    recorded: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        settings,
        "show_result",
        lambda title, lines: recorded.append((title, tuple(lines))),
    )
    settings._show_status(provider)
    assert "not configured" in " ".join(recorded[0][1])
    assert not provider.store.directory.exists()


def test_main_menu_settings_handoff_uses_same_actor_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-a"))
    seen: list[MenuSessionContext] = []
    monkeypatch.setattr("builtins.input", lambda _prompt="": "8")
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        menu,
        "launch_teacher_settings_menu",
        lambda session: seen.append(session),
    )
    assert menu._main_menu_once(state)
    assert seen == [state]


def test_workspace_menu_return_invalidates_cached_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-a"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": "3")
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "launch_workspace_menu", lambda: None)
    assert menu._main_menu_once(state)
    assert state.actor is None


def test_standalone_entry_points_choose_provider_instead_of_raw_actor_prompt() -> None:
    for function in (
        activity_menu.launch_activity_context_menu,
        activity_menu.launch_advanced_activity_tools_menu,
        activity_menu.launch_activity_management_menu,
        scan_menu.launch_scan_routing_menu,
        scoring_menu.launch_assessment_setup_menu,
        scoring_menu.launch_score_menu,
        scoring_menu.launch_scoring_menu,
    ):
        source = inspect.getsource(function)
        assert "new_menu_session() if state is None else state" in source


def test_settings_help_and_back_are_zero_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = ConcordTeacherAttributionProvider(
        ConcordTeacherAttributionStore(config_directory=tmp_path)
    )
    state = MenuSessionContext(attribution_provider=provider)
    choices = iter(("h", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(settings, "clear_screen", lambda: None)
    monkeypatch.setattr(settings, "show_result", lambda *_args: None)
    settings.launch_teacher_settings_menu(state)
    assert not provider.store.directory.exists()


def test_settings_cancel_action_is_bounded_to_settings_menu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = ConcordTeacherAttributionProvider(
        ConcordTeacherAttributionStore(config_directory=tmp_path)
    )
    state = MenuSessionContext(attribution_provider=provider)
    choices = iter(("2", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(settings, "clear_screen", lambda: None)
    monkeypatch.setattr(
        settings, "_setup", lambda *_args: (_ for _ in ()).throw(CancelMenuAction())
    )
    settings.launch_teacher_settings_menu(state)
    assert not provider.store.directory.exists()
