from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_activity as activity_module
import concord.menu_attention as attention_menu
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import ReturnToMainMenu
from concord.workflows.activity_attention import (
    ActivityAttentionItem,
    ActivityAttentionSummary,
)
from concord.workflows.models import ActivitySummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Macbeth Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=7,
    )


def _summary(*items: ActivityAttentionItem) -> ActivityAttentionSummary:
    return ActivityAttentionSummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Macbeth Seminar",
        items=items,
    )


def _item(
    *,
    task: str = "score",
    code: str = "concord_score_ready",
    label: str = "Reviewed evidence is ready for scoring",
    count: int = 2,
    action_id: str = "open_activity_score",
) -> ActivityAttentionItem:
    return ActivityAttentionItem(
        code=code,
        label=label,
        task=task,  # type: ignore[arg-type]
        count=count,
        action_id=action_id,
    )


def _stable_activity(monkeypatch: pytest.MonkeyPatch) -> ActivitySummary:
    activity = _activity()
    monkeypatch.setattr(
        activity_module,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=activity),
    )
    return activity


def test_opened_activity_shows_bounded_next_action_without_renumbering(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _stable_activity(monkeypatch)
    summary = _summary(
        _item(),
        _item(
            task="share",
            code="concord_share_publish",
            label="Current result is ready for explicit publication",
            count=1,
            action_id="open_activity_share",
        ),
    )
    monkeypatch.setattr(
        activity_module,
        "inspect_activity_attention",
        lambda *_args, **_kwargs: summary,
    )
    routed: list[str] = []
    monkeypatch.setattr(
        activity_module,
        "launch_activity_attention_action",
        lambda _activity, _state, action_id: routed.append(action_id),
    )
    answers = iter(("a", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)

    activity_module.launch_activity_context_menu(activity, MenuSessionContext())

    output = capsys.readouterr().out
    assert "1. Plan" in output
    assert "2. Prepare" in output
    assert "3. Collect" in output
    assert "4. Review" in output
    assert "5. Score" in output
    assert "6. Share" in output
    assert "7. Advanced Activity tools" in output
    assert "A. Open next action" in output
    assert "Next: Score - Reviewed evidence is ready for scoring (count 2)" in output
    assert "Also: 1 other attention category" in output
    assert routed == ["open_activity_score"]


@pytest.mark.parametrize(
    ("action_id", "target_name"),
    (
        ("open_activity_plan", "launch_plan_menu"),
        ("open_activity_prepare", "launch_prepare_menu"),
        ("open_activity_collect", "launch_collect_menu"),
        ("open_activity_review", "launch_review_task_menu"),
        ("open_activity_score", "launch_score_task_menu"),
        ("open_activity_share", "launch_share_menu"),
    ),
)
def test_owner_action_ids_route_to_existing_issue66_task_menus(
    monkeypatch: pytest.MonkeyPatch,
    action_id: str,
    target_name: str,
) -> None:
    activity = _activity()
    state = MenuSessionContext()
    calls: list[tuple[str, object]] = []
    monkeypatch.setattr(
        activity_module,
        target_name,
        lambda selected, selected_state: calls.append(
            (selected.activity_id, selected_state)
        ),
    )

    activity_module.launch_activity_attention_action(activity, state, action_id)

    assert calls == [("activity-1", state)]


def test_unknown_owner_action_is_rejected_without_fallback() -> None:
    with pytest.raises(Exception, match="Unsupported Concord attention action"):
        activity_module.launch_activity_attention_action(
            _activity(), MenuSessionContext(), "open_student_secret"
        )


def test_attention_failure_is_generic_and_does_not_leak_exception_text(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = _stable_activity(monkeypatch)

    def _fail(*_args: object, **_kwargs: object) -> ActivityAttentionSummary:
        raise RuntimeError("student-secret grouping-signal=high")

    monkeypatch.setattr(activity_module, "inspect_activity_attention", _fail)
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")

    activity_module.launch_activity_context_menu(activity)

    output = capsys.readouterr().out
    assert "Attention: unavailable" in output
    assert "student-secret" not in output
    assert "grouping-signal" not in output


def test_activity_management_adds_attention_discovery_without_renumbering(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls: list[object] = []
    monkeypatch.setattr(
        activity_module,
        "launch_activity_attention_discovery",
        lambda state, **_kwargs: calls.append(state),
    )
    answers = iter(("a", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(activity_module, "clear_screen", lambda: None)
    state = MenuSessionContext()

    activity_module.launch_activity_management_menu(state)

    output = capsys.readouterr().out
    assert "1. Create Classroom Activity" in output
    assert "2. Continue setup for an Activity" in output
    assert "3. Advanced Activity tools" in output
    assert "A. Attention needed" in output
    assert calls == [state]


def test_cross_activity_discovery_routes_only_the_selected_next_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    summary = _summary(_item(task="review", action_id="open_activity_review"))
    monkeypatch.setattr(
        attention_menu,
        "list_activity_attention",
        lambda: (summary,),
    )
    monkeypatch.setattr(
        attention_menu,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=_activity()),
    )
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)
    answers = iter(("1", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    calls: list[str] = []

    attention_menu.launch_activity_attention_discovery(
        MenuSessionContext(),
        route_action=lambda _activity, _state, action_id: calls.append(action_id),
    )

    output = capsys.readouterr().out
    assert "Attention Needed" in output
    assert "Macbeth Seminar (class-1)" in output
    assert "Review: Reviewed evidence is ready for scoring" in output
    assert calls == ["open_activity_review"]


def test_cross_activity_discovery_preserves_main_menu_unwind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = _summary(_item())
    monkeypatch.setattr(
        attention_menu,
        "list_activity_attention",
        lambda: (summary,),
    )
    monkeypatch.setattr(
        attention_menu,
        "show_activity",
        lambda *_args, **_kwargs: SimpleNamespace(summary=_activity()),
    )
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "1")

    def _route(*_args: object) -> None:
        raise ReturnToMainMenu

    with pytest.raises(ReturnToMainMenu):
        attention_menu.launch_activity_attention_discovery(
            MenuSessionContext(),
            route_action=_route,
        )


def test_opened_summary_does_not_sum_heterogeneous_attention_counts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    attention_menu.print_activity_attention_summary(
        _summary(
            _item(count=4),
            _item(
                task="share",
                code="concord_share_publish",
                label="Current result is ready for explicit publication",
                count=1,
                action_id="open_activity_share",
            ),
        )
    )

    output = capsys.readouterr().out
    assert "count 4" in output
    assert "5" not in output
    assert "1 other attention category" in output
