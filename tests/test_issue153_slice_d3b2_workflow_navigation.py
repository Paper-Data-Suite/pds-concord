"""#153 D3b2: publication, reusable grouping and materials navigation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided
import concord.menu_presets as presets
import concord.menu_publication as publication
import concord.menu_saved_groupings as groupings
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.menu_prompts import select_one
from concord.workflows import ActivitySummary, WorkflowActor

ACTIVITY = ActivitySummary(
    class_id="class-1",
    activity_id="activity-1",
    title="Synthetic Activity",
    status="draft",
    scoring_orientation="mixed",
    session_count=1,
    group_count=1,
    snapshot_revision=1,
)


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher"))


def _choose(*_args: object, **_kwargs: object) -> str:
    return select_one("Synthetic choice", ("one",), ("One",), help_text="Choose one.")


def _forbidden(*_args: object, **_kwargs: object) -> None:
    pytest.fail("Navigation must not produce an operational error or authorize a write")


@pytest.mark.parametrize("route", ("share", "publication", "preset", "materials"))
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_parent_menu_preserves_nested_navigation(
    monkeypatch: pytest.MonkeyPatch, route: str, choice: str
) -> None:
    option = {"share": "3", "publication": "7", "preset": "2", "materials": "1"}[route]
    answers = iter((option, choice, "b") if choice == "b" else (option, choice))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(publication, "_root", lambda: Path("synthetic"))
    monkeypatch.setattr(
        publication,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=ACTIVITY),
    )
    monkeypatch.setattr(publication, "_handle_error", _forbidden)
    monkeypatch.setattr(publication, "_share_results", _choose)
    monkeypatch.setattr(publication, "_publish", _choose)
    monkeypatch.setattr(presets, "_create", _choose)
    monkeypatch.setattr(guided, "_use_saved_packet", _choose)
    monkeypatch.setattr(presets, "show_result", _forbidden)
    monkeypatch.setattr(guided, "show_result", _forbidden)
    state = _state()
    actions = {
        "share": lambda: publication.launch_share_results_menu(ACTIVITY, state),
        "publication": lambda: publication.launch_publication_menu(ACTIVITY, state),
        "preset": lambda: presets._kind_menu("scoring_scale", state),
        "materials": lambda: guided._launch_materials(ACTIVITY, state),
    }
    if choice == "b":
        assert actions[route]() is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            actions[route]()
    assert next(answers, None) is None


@pytest.mark.parametrize("route", ("save", "use", "manage"))
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_saved_grouping_actions_preserve_nested_navigation(
    monkeypatch: pytest.MonkeyPatch, route: str, choice: str
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
    monkeypatch.setattr(groupings, "_latest", lambda *_a: ACTIVITY)
    monkeypatch.setattr(groupings, "handle_write_error", _forbidden)
    monkeypatch.setattr(groupings, "show_result", _forbidden)
    monkeypatch.setattr(groupings, "confirm_prepared_actor_write", _forbidden)
    monkeypatch.setattr(groupings, "save_grouping", _forbidden)
    monkeypatch.setattr(groupings, "reuse_grouping", _forbidden)
    monkeypatch.setattr(groupings, "prompt_text", _choose)
    monkeypatch.setattr(groupings, "_select_saved", _choose)
    saved = SimpleNamespace(
        revision=SimpleNamespace(
            name="Synthetic grouping", status="active", revision=1, groups=()
        )
    )
    monkeypatch.setattr(groupings, "_saved", lambda *_a: (saved,))
    monkeypatch.setattr(groupings, "select_one", _choose)
    state = _state()
    actions = {
        "save": lambda: groupings.save_grouping_from_plan(
            ACTIVITY, state, group_plan_id="plan-1"
        ),
        "use": lambda: groupings.use_saved_grouping(ACTIVITY, state),
        "manage": lambda: groupings.manage_saved_groupings(ACTIVITY, state),
    }
    if choice == "b":
        assert actions[route]() is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            actions[route]()
