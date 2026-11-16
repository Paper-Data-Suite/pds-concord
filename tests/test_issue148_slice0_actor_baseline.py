"""#148 source-pinned actor baseline and explicit future-feature witnesses.

Characterization tests distinguish a working one-session cache from missing
cross-process persistence. Strict XFAILs belong to later implementation slices.
All identities are synthetic. No real user configuration or workspace is read.
"""

from __future__ import annotations

import importlib.util
from argparse import Namespace

import pytest

import concord.menu as menu
import concord.menu_context as actor_menu
from concord.cli_app.common import workflow_actor
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows import WorkflowActor


def test_concord_scoped_teacher_attribution_provider_is_available() -> None:
    """Slice 1 owns the read-only store/provider, not Meridian or Core Notes."""
    assert importlib.util.find_spec("concord.teacher_attribution") is not None


def test_main_menu_discloses_teacher_attribution_settings(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "q")
    assert menu.launch_menu() == 0
    output = capsys.readouterr().out
    assert "Teacher Settings" in output
    assert "attribution" in output.casefold()


def test_menu_session_has_explicit_provider_injection_seam() -> None:
    """Slice 2 must connect an injectable provider without global settings writes."""
    assert "attribution_provider" in MenuSessionContext.__dataclass_fields__


def test_menu_session_exposes_one_action_override_contract() -> None:
    """Slice 3 owns actor selection tied to one reviewed write, not a sticky actor."""
    assert callable(getattr(MenuSessionContext, "actor_for_action", None))


def test_one_menu_session_prompts_exactly_once_and_reuses_same_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts: list[str] = []
    monkeypatch.setattr(actor_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": prompts.append(prompt) or "synthetic-teacher-1",
    )
    session = MenuSessionContext()
    first = session.require_actor()
    assert session.require_actor() is first
    assert first.actor_id == "synthetic-teacher-1"
    assert first.display_label is None  # legacy prompt captures only an ID
    assert prompts == ["Actor ID: "]


def test_independent_process_like_contexts_reprompt_in_current_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A characterization to update when durable setup/relaunch is implemented."""
    seen: list[str] = []
    monkeypatch.setattr(actor_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": seen.append(prompt) or "synthetic-teacher-1",
    )
    first = MenuSessionContext()
    second = MenuSessionContext()
    assert first.require_actor().actor_id == second.require_actor().actor_id
    assert len(seen) == 2  # cache is per MenuSessionContext, not process-persistent
    assert first.actor is not second.actor


def test_main_menu_passes_exact_session_to_activity_and_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[tuple[str, object]] = []
    choices = iter(("1", "4"))
    session = MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher-1"))
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(
        menu,
        "launch_activity_management_menu",
        lambda context: seen.append(("activity", context)),
    )
    monkeypatch.setattr(
        menu,
        "launch_scan_routing_menu",
        lambda context: seen.append(("scan", context)),
    )
    assert menu._main_menu_once(session)
    assert menu._main_menu_once(session)
    assert seen == [("activity", session), ("scan", session)]
    assert all(state is session for _kind, state in seen)


def test_actor_back_cancels_and_main_quit_preserve_navigation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(actor_menu, "clear_screen", lambda: None)
    for choice, expected in (
        ("b", CancelMenuAction),
        ("m", ReturnToMainMenu),
        ("q", QuitPDS),
    ):
        monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
        session = MenuSessionContext()
        with pytest.raises(expected):
            session.require_actor()
        assert session.actor is None


def test_existing_actor_model_preserves_canonical_id_and_display_snapshot() -> None:
    actor = WorkflowActor(
        actor_id="synthetic-teacher-1",
        display_label="Dr. Ñ. Example",
    )
    assert actor.actor_id == "synthetic-teacher-1"
    assert actor.display_label == "Dr. Ñ. Example"
    assert actor.actor_kind == "authorized_adult"
    assert actor.owning_system == "concord"


def test_direct_cli_actor_is_explicit_and_separate_from_menu_preferences() -> None:
    args = Namespace(
        actor_id="synthetic-cli-teacher-2",
        actor_label="Second Teacher",
        actor_role=None,
    )
    actor = workflow_actor(args)
    assert actor.actor_id == "synthetic-cli-teacher-2"
    assert actor.display_label == "Second Teacher"
    assert actor.role_label is None
