from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_group_plan as plan_menu
import concord.menu_group_plan_missing_signal as missing_menu
from concord.menu_context import MenuSessionContext
from concord.models import PlannedGroup
from concord.workflows import (
    GroupPlanDetail,
    MissingSignalPlanInspection,
    WorkflowActor,
)


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def _detail(*, strategy: str = "mixed_signal") -> GroupPlanDetail:
    plan = SimpleNamespace(
        group_plan_id="signal-plan",
        strategy=strategy,
        status="draft",
        roster_student_ids=("student-1", "student-2", "student-3", "student-4"),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="mixed-1",
                label="Group 1",
                student_ids=("student-1",),
            ),
            PlannedGroup(
                planned_group_key="mixed-2",
                label="Group 2",
                student_ids=("student-2",),
            ),
        ),
        unresolved_student_ids=("student-3", "student-4"),
        missing_signal_disposition=None,
        missing_signal_random_seed=None,
    )
    summary = SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="signal-plan",
        snapshot_revision=7,
        unresolved_student_count=2,
    )
    return cast(
        GroupPlanDetail,
        SimpleNamespace(plan=plan, summary=summary, record_revision=1),
    )


def _inspection() -> MissingSignalPlanInspection:
    return MissingSignalPlanInspection(
        detail=_detail(),
        signal_set_id="signal-55",
        signal_set_digest="d" * 64,
        dimension_id="collaboration-context",
        missing_student_ids=("student-3", "student-4"),
        missing_assigned_student_ids=(),
        missing_unresolved_student_ids=("student-3", "student-4"),
    )


def test_random_menu_previews_affected_placements_before_write(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    inspection = _inspection()
    events: list[str] = []
    captured: list[object] = []

    monkeypatch.setattr(
        missing_menu,
        "inspect_group_plan_missing_signal",
        lambda *a, **k: inspection,
    )
    monkeypatch.setattr(missing_menu, "_show_context", lambda _item: None)
    monkeypatch.setattr(missing_menu, "select_one", lambda *a, **k: "random")
    monkeypatch.setattr(
        missing_menu,
        "prompt_exact_text",
        lambda *a, **k: "missing-seed",
    )
    monkeypatch.setattr(missing_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(missing_menu, "print_menu_header", lambda *a, **k: None)
    monkeypatch.setattr(
        missing_menu,
        "pause_for_user",
        lambda: events.append("preview"),
    )
    monkeypatch.setattr(
        missing_menu,
        "confirm_write",
        lambda *a, **k: events.append("confirm") or True,
    )
    monkeypatch.setattr(missing_menu, "show_result", lambda *a, **k: None)

    def fake_set(request: object) -> object:
        captured.append(request)
        assert events == ["preview", "confirm"]
        return SimpleNamespace(
            mutation=SimpleNamespace(
                group_plan_id="signal-plan",
                status="draft",
                commit=SimpleNamespace(snapshot_revision=8),
            ),
            disposition="random",
            missing_student_count=2,
            assigned_student_count=4,
            unresolved_student_count=0,
            group_sizes=(2, 2),
            random_seed="missing-seed",
        )

    monkeypatch.setattr(missing_menu, "set_missing_signal_disposition", fake_set)

    missing_menu.resolve_missing_signal_from_menu(_detail(), _state())
    output = capsys.readouterr().out
    assert "Affected missing-signal students: 2" in output
    assert "Seed: missing-seed" in output
    assert "Result group sizes: 2,2" in output
    assert "student-3 ->" in output
    assert "student-4 ->" in output
    assert "Students already represented" in output
    request = captured[0]
    assert getattr(request, "disposition") == "random"
    assert getattr(request, "random_seed") == "missing-seed"
    assert getattr(request, "expected_snapshot_revision") == 7


def test_signal_plan_open_menu_exposes_missing_signal_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    values = iter(["7", "b"])

    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(plan_menu, "print_menu_header", lambda *a, **k: None)
    monkeypatch.setattr(plan_menu, "print_navigation", lambda *a, **k: None)
    monkeypatch.setattr(plan_menu, "show_group_plan", lambda *a, **k: _detail())
    monkeypatch.setattr(
        plan_menu,
        "resolve_missing_signal_from_menu",
        lambda _detail, _state: calls.append("resolve"),
    )

    selected = SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="signal-plan",
    )
    activity = SimpleNamespace(class_id="class-1", activity_id="activity-1")
    plan_menu._open_plan(activity, selected, _state())
    assert calls == ["resolve"]
