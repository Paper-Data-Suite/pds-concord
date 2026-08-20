from __future__ import annotations

from types import SimpleNamespace

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.menu_group as group_menu
import concord.menu_group_plan as plan_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor, WorkflowCommitResult


def _activity(snapshot: int = 7) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Planning Activity",
        status="draft",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=0,
        snapshot_revision=snapshot,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def _commit(snapshot: int = 8) -> WorkflowCommitResult:
    return WorkflowCommitResult(
        work=ModuleWorkRef(
            module_id="concord",
            class_id="class-1",
            work_id="activity-1",
        ),
        snapshot_revision=snapshot,
        snapshot_sha256="a" * 64,
        changed_records=(),
        no_op=False,
    )


def test_groups_and_participants_menu_exposes_plan_and_direct_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    values = iter(["1", "2", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(group_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(group_menu, "print_menu_header", lambda *_a, **_k: None)
    monkeypatch.setattr(group_menu, "print_navigation", lambda *_a, **_k: None)
    monkeypatch.setattr(
        group_menu,
        "launch_group_plan_menu",
        lambda _activity, _state: calls.append("plan"),
    )
    monkeypatch.setattr(
        group_menu,
        "launch_direct_group_menu",
        lambda _activity, _state: calls.append("direct"),
    )
    group_menu.launch_group_menu(_activity(), _state())
    assert calls == ["plan", "direct"]


def test_manual_menu_creation_uses_latest_snapshot_and_group_plan_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[object] = []
    current = _activity(11)
    monkeypatch.setattr(plan_menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        plan_menu,
        "prompt_text",
        lambda *a, **k: "activity-1-group-plan",
    )
    monkeypatch.setattr(plan_menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(plan_menu, "show_result", lambda *a, **k: None)

    def fake_create(request: object) -> object:
        captured.append(request)
        return SimpleNamespace(
            commit=_commit(12),
            group_plan_id="activity-1-group-plan",
            status="draft",
        )

    monkeypatch.setattr(plan_menu, "create_manual_group_plan", fake_create)
    plan_menu._create_manual(current, _state())
    assert len(captured) == 1
    request = captured[0]
    assert getattr(request, "class_id") == "class-1"
    assert getattr(request, "activity_id") == "activity-1"
    assert getattr(request, "group_plan_id") == "activity-1-group-plan"
    assert getattr(request, "expected_snapshot_revision") == 11
    assert getattr(request, "actor").actor_id == "teacher-1"


def test_plan_menu_help_states_proposal_not_group_state(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    values = iter(["h", "", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(plan_menu, "_latest", lambda activity: activity)
    plan_menu.launch_group_plan_menu(_activity(), _state())
    output = capsys.readouterr().out
    assert "GroupPlans are editable proposals" in output
    assert "separate from canonical Groups and Memberships" in output
    assert "Direct Group management remains available" in output
