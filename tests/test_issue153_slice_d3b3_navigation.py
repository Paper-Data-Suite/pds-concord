"""#153 D3b3: signal, grouping revision and feedback navigation."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_group_plan_signal as plans
import concord.menu_grouping_signal as signals
import concord.menu_saved_grouping_revisions as revisions
import concord.menu_saved_operational_grouping as operational
import concord.menu_student_feedback as feedback
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


def _choose(*_args: object, **_kwargs: object) -> str:
    return select_one("Synthetic choice", ("one",), ("One",), help_text="Choose one.")


def _forbidden(*_args: object, **_kwargs: object) -> None:
    pytest.fail("Navigation must not reach a mutation or operational error receipt")


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher"))


@pytest.mark.parametrize("route", ("signal-plan", "operational-save"))
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_direct_action_navigation(
    monkeypatch: pytest.MonkeyPatch, route: str, choice: str
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
    monkeypatch.setattr(plans, "_latest", lambda *_a: ACTIVITY)
    monkeypatch.setattr(plans, "prompt_text", _choose)
    monkeypatch.setattr(plans, "_handle_error", _forbidden)
    monkeypatch.setattr(plans, "create_signal_group_plan", _forbidden)
    monkeypatch.setattr(
        operational, "show_activity", lambda *_a: SimpleNamespace(summary=ACTIVITY)
    )
    monkeypatch.setattr(operational, "list_sessions", lambda *_a: (object(),))
    monkeypatch.setattr(operational, "choose_session", _choose)
    monkeypatch.setattr(operational, "handle_write_error", _forbidden)
    monkeypatch.setattr(operational, "save_operational_grouping", _forbidden)
    state = _state()
    actions = {
        "signal-plan": lambda: plans.create_signal_group_plan_from_menu(
            ACTIVITY, state, "similar_signal"
        ),
        "operational-save": lambda: operational.save_grouping_from_existing_groups(
            ACTIVITY, state
        ),
    }
    if choice == "b":
        assert actions[route]() is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            actions[route]()


@pytest.mark.parametrize("route", ("signal-import", "revision", "feedback"))
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_parent_action_navigation(
    monkeypatch: pytest.MonkeyPatch, route: str, choice: str
) -> None:
    option = {"signal-import": "3", "revision": "3", "feedback": "2"}[route]
    answers = iter((option, choice, "b") if choice == "b" else (option, choice))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(signals, "_import_csv", _choose)
    monkeypatch.setattr(signals, "show_result", _forbidden)
    monkeypatch.setattr(feedback, "_prepare_distribution", _choose)
    monkeypatch.setattr(feedback, "show_result", _forbidden)
    selected = SimpleNamespace(
        revision=SimpleNamespace(
            arrangement_id="grouping-1",
            name="Synthetic grouping",
            status="active",
            revision=1,
            groups=(),
        )
    )
    monkeypatch.setattr(revisions, "_current", lambda *_a: selected)
    monkeypatch.setattr(revisions, "_change", _choose)
    monkeypatch.setattr(revisions, "handle_write_error", _forbidden)
    state = _state()
    actions = {
        "signal-import": lambda: signals.launch_grouping_signal_menu(ACTIVITY),
        "revision": lambda: revisions.manage_grouping_revision(
            ACTIVITY, state, selected, show_placements=_forbidden
        ),
        "feedback": lambda: feedback.launch_student_feedback_distribution_menu(
            ACTIVITY, state
        ),
    }
    if choice == "b":
        assert actions[route]() is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            actions[route]()
    assert next(answers, None) is None


@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_saved_revision_direct_navigation(
    monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    selected = SimpleNamespace(
        revision=SimpleNamespace(
            arrangement_id="grouping-1",
            name="Synthetic grouping",
            status="active",
            revision=1,
            groups=(),
        )
    )
    monkeypatch.setattr(revisions, "_current", lambda *_a: selected)
    monkeypatch.setattr(revisions, "handle_write_error", _forbidden)
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
    if choice == "b":
        revisions.manage_grouping_revision(
            ACTIVITY, _state(), selected, show_placements=_forbidden
        )
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            revisions.manage_grouping_revision(
                ACTIVITY, _state(), selected, show_placements=_forbidden
            )
