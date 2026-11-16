"""#148 Slice 3: action-scoped actor review and no-leakage contracts."""

from __future__ import annotations

import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_activity as activity_menu
import concord.menu_actor_action as action_menu
import concord.menu_group_plan as group_plan_menu
import concord.menu_scan as scan_menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    TeacherAttributionIdentity,
)
from concord.workflows import ActivitySummary, WorkflowActor


def _state(tmp_path: Path) -> tuple[MenuSessionContext, ConcordTeacherAttributionStore]:
    store = ConcordTeacherAttributionStore(config_directory=tmp_path)
    store.create("Teacher Default", actor_id="teacher-default")
    return MenuSessionContext(
        attribution_provider=ConcordTeacherAttributionProvider(store)
    ), store


def _ui(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(action_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(action_menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(action_menu, "print_navigation", lambda: None)
    monkeypatch.setattr(action_menu, "show_result", lambda *_a: None)
    monkeypatch.setattr(action_menu, "prompt_text", lambda *_a, **_kw: None)


def _confirm(state: MenuSessionContext, *, legacy=None):
    return action_menu.confirm_actor_write(
        "Review the exact action",
        "SAVE",
        ("Activity: synthetic", "Exact target: synthetic-one"),
        state=state,
        legacy_confirm=legacy or (lambda *_: True),
    )


def test_default_review_has_single_substantive_confirmation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state, store = _state(tmp_path)
    _ui(monkeypatch)
    calls: list[str] = []
    monkeypatch.setattr(
        "builtins.input", lambda prompt="": calls.append(prompt) or "SAVE"
    )
    actor = _confirm(state)
    assert actor is not None
    assert (actor.actor_id, actor.display_label) == (
        "teacher-default",
        "Teacher Default",
    )
    assert calls == ["Confirmation: "]
    assert "Recorded by: Teacher Default" in capsys.readouterr().out
    assert store.load() is not None


def test_advanced_alternate_applies_once_without_changing_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _state(tmp_path)
    _ui(monkeypatch)
    choices = iter(("a", "SAVE", "SAVE"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(
        action_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-other", "Other Adult", "temporary"),
    )
    first = _confirm(state)
    second = _confirm(state)
    assert first is not None and first.actor_id == "teacher-other"
    assert first.display_label == "Other Adult"
    assert second is not None and second.actor_id == "teacher-default"
    assert state.actor is not None and state.actor.actor_id == "teacher-default"
    stored = store.load()
    assert stored is not None and stored.profile.actor_id == "teacher-default"


def test_cancelled_temporary_actor_never_leaks_to_next_action(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, _store = _state(tmp_path)
    _ui(monkeypatch)
    choices = iter(("a", "", "SAVE"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(
        action_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-other", "Other Adult", "temporary"),
    )
    assert _confirm(state) is None
    chosen = _confirm(state)
    assert chosen is not None and chosen.actor_id == "teacher-default"


def test_restore_default_inside_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, _store = _state(tmp_path)
    _ui(monkeypatch)
    choices = iter(("a", "d", "SAVE"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(
        action_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-other", "Other Adult", "temporary"),
    )
    chosen = _confirm(state)
    assert chosen is not None and chosen.actor_id == "teacher-default"


def test_changed_profile_during_review_refuses_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, store = _state(tmp_path)
    _ui(monkeypatch)

    def change_during_review(_prompt: str = "") -> str:
        profile = store.load()
        assert profile is not None
        store.update_display_name(profile, "New Name")
        return "SAVE"

    monkeypatch.setattr("builtins.input", change_during_review)
    with pytest.raises(CancelMenuAction, match="changed"):
        _confirm(state)
    assert state.actor is None


def test_alternate_cannot_be_persisted_or_queued_without_active_review(
    tmp_path: Path,
) -> None:
    state, store = _state(tmp_path)
    alternate = TeacherAttributionIdentity("teacher-other", "Other Adult", "temporary")
    selected = state.actor_for_action(
        action_label="one exact write", alternate=alternate
    )
    assert selected.actor_id == "teacher-other"
    assert state.require_actor().actor_id == "teacher-default"
    assert (
        state.actor_for_action(action_label="next action").actor_id == "teacher-default"
    )
    assert store.load() is not None
    with pytest.raises(CancelMenuAction, match="explicitly selected"):
        state.actor_for_action(
            action_label="wrong source",
            alternate=TeacherAttributionIdentity(
                "teacher-other", "Other Adult", "saved"
            ),
        )
    with pytest.raises(ValueError, match="action label"):
        state.actor_for_action(action_label="  ")


def test_legacy_actor_confirmation_keeps_existing_menu_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ui(monkeypatch)
    actor = WorkflowActor(actor_id="teacher-explicit")
    state = MenuSessionContext(actor=actor)
    confirmations: list[str] = []
    result = _confirm(
        state,
        legacy=lambda _t, expected, _lines: confirmations.append(expected) or True,
    )
    assert result is actor
    assert confirmations == ["SAVE"]


def test_cancelled_temporary_entry_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, _store = _state(tmp_path)
    _ui(monkeypatch)
    choices = iter(("a", "SAVE"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(
        action_menu,
        "_choose_temporary_actor",
        lambda: (_ for _ in ()).throw(CancelMenuAction()),
    )
    assert _confirm(state) is None
    next_actor = _confirm(state)
    assert next_actor is not None and next_actor.actor_id == "teacher-default"


def test_manual_group_plan_creation_accepts_reviewed_alternate_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state, _store = _state(tmp_path)
    activity = ActivitySummary(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=3,
    )
    _ui(monkeypatch)
    monkeypatch.setattr(group_plan_menu, "_latest", lambda _a: activity)
    monkeypatch.setattr(
        group_plan_menu, "prompt_text", lambda *_a, **_kw: "synthetic-plan"
    )
    monkeypatch.setattr(group_plan_menu, "standards_for_activity", lambda _a: None)
    monkeypatch.setattr(group_plan_menu, "show_result", lambda *_a: None)
    recorded: list[WorkflowActor] = []

    def fake_create(request: object, **_kwargs: object) -> SimpleNamespace:
        recorded.append(getattr(request, "actor"))
        return SimpleNamespace(
            group_plan_id="synthetic-plan",
            status="draft",
            commit=SimpleNamespace(snapshot_revision=4),
        )

    monkeypatch.setattr(group_plan_menu, "create_manual_group_plan", fake_create)
    choices = iter(("a", "CREATE"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(choices))
    monkeypatch.setattr(
        action_menu,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("teacher-other", "Other Adult", "temporary"),
    )
    group_plan_menu._create_manual(activity, state)
    assert len(recorded) == 1 and recorded[0].actor_id == "teacher-other"
    assert state.require_actor().actor_id == "teacher-default"


def test_activity_and_scan_owner_paths_use_same_reviewed_actor_helper() -> None:
    activity = inspect.getsource(activity_menu._create_activity)
    scan = inspect.getsource(scan_menu._review)
    assert "actor = confirm_actor_write(" in activity
    assert scan.count("actor = confirm_actor_write(") == 2
    assert "reviewer=actor" in scan
    assert "actor=actor" in activity


def test_direct_cli_actor_and_core_boundaries_are_unmodified() -> None:
    from argparse import Namespace

    from concord.cli_app.common import workflow_actor

    actor = workflow_actor(
        Namespace(actor_id="cli-teacher", actor_label="CLI User", actor_role=None)
    )
    assert actor.actor_id == "cli-teacher"
    assert actor.display_label == "CLI User"


@pytest.mark.parametrize("confirmed", [True, False])
def test_minimal_legacy_routing_context_without_provider_attribute(
    confirmed: bool,
) -> None:
    """Issue #109 supplies a session exposing only require_actor()."""
    actor = WorkflowActor(actor_id="legacy-routing-adult")
    consulted: list[str] = []

    def require_actor() -> WorkflowActor:
        consulted.append("resolved")
        return actor

    state = SimpleNamespace(require_actor=require_actor)
    chosen = action_menu.confirm_actor_write(
        "Defer Routing Failure",
        "DEFER",
        ("Physical page: 4", "Resolution note: synthetic"),
        state=state,
        legacy_confirm=lambda _title, _verb, _lines: confirmed,
    )
    assert chosen is (actor if confirmed else None)
    assert consulted == (["resolved"] if confirmed else [])
