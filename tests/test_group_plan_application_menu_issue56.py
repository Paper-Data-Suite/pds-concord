from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_group_plan as plan_menu
import concord.menu_group_plan_application as application_menu
from concord.group_plan_application import (
    ApplicationGroupSpec,
    ApplicationMembershipSpec,
)
from concord.menu_context import MenuSessionContext
from concord.models import EffectiveContext, PlannedGroup
from concord.workflows import (
    GroupPlanApplicationPreview,
    GroupPlanDetail,
    WorkflowActor,
)


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))


def _context() -> EffectiveContext:
    return EffectiveContext(activity_id="activity-1", session_ids=("session-1",))


def _detail(*, status: str = "approved") -> GroupPlanDetail:
    plan = SimpleNamespace(
        group_plan_id="plan-1",
        strategy="manual",
        status=status,
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1",),
            ),
        ),
    )
    summary = SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        snapshot_revision=7,
        unresolved_student_count=0,
    )
    return cast(
        GroupPlanDetail,
        SimpleNamespace(plan=plan, summary=summary, record_revision=4),
    )


def _preview() -> GroupPlanApplicationPreview:
    context = _context()
    group = ApplicationGroupSpec(
        planned_group_key="group-a",
        group_id="group-" + "a" * 64,
        label="Group A",
        description=None,
        effective_context=None,
    )
    membership = ApplicationMembershipSpec(
        planned_group_key="group-a",
        student_id="student-1",
        membership_id="membership-" + "b" * 64,
        group_id=group.group_id,
        effective_context=context,
    )
    return GroupPlanApplicationPreview(
        application_id="apply-menu-1",
        application_digest="c" * 64,
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        group_plan_record_revision=4,
        expected_snapshot_revision=7,
        fallback_effective_context=context,
        groups=(group,),
        memberships=(membership,),
        unresolved_student_ids=(),
    )


def test_menu_previews_before_apply_and_uses_exact_prepared_identity(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    preview = _preview()
    events: list[str] = []
    captured: list[object] = []
    monkeypatch.setattr(application_menu, "list_sessions", lambda *a, **k: (object(),))
    monkeypatch.setattr(
        application_menu,
        "choose_effective_context",
        lambda *a, **k: _context(),
    )
    monkeypatch.setattr(
        application_menu,
        "prepare_group_plan_application",
        lambda request: captured.append(request) or preview,
    )
    monkeypatch.setattr(application_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(application_menu, "print_menu_header", lambda *a, **k: None)
    monkeypatch.setattr(
        application_menu,
        "pause_for_user",
        lambda: events.append("preview"),
    )
    monkeypatch.setattr(
        application_menu,
        "confirm_write",
        lambda *a, **k: events.append("confirm") or True,
    )

    def fake_apply(request: object) -> object:
        captured.append(request)
        assert events == ["preview", "confirm"]
        return SimpleNamespace(
            group_plan_id="plan-1",
            status="applied",
            application_id="apply-menu-1",
            application_digest="c" * 64,
            group_count=1,
            membership_count=1,
            unresolved_count=0,
            commit=SimpleNamespace(snapshot_revision=8),
        )

    monkeypatch.setattr(application_menu, "apply_group_plan", fake_apply)
    monkeypatch.setattr(application_menu, "show_result", lambda *a, **k: None)

    application_menu.apply_approved_group_plan_from_menu(_detail(), _state())
    output = capsys.readouterr().out
    assert "Application ID: apply-menu-1" in output
    assert "Application digest: " + "c" * 64 in output
    assert "student-1 -> membership-" in output
    assert "No changes have been written." in output
    prepare_request, apply_request = captured
    assert getattr(prepare_request, "fallback_effective_context") == _context()
    assert getattr(apply_request, "application_id") == preview.application_id
    assert getattr(apply_request, "application_digest") == preview.application_digest
    assert getattr(apply_request, "expected_snapshot_revision") == 7
    assert getattr(apply_request, "actor").actor_id == "teacher-1"


def test_open_plan_exposes_apply_only_for_approved_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    values = iter(["10", "b"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(values))
    monkeypatch.setattr(plan_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(plan_menu, "print_menu_header", lambda *a, **k: None)
    monkeypatch.setattr(plan_menu, "print_navigation", lambda *a, **k: None)
    monkeypatch.setattr(plan_menu, "show_group_plan", lambda *a, **k: _detail())
    monkeypatch.setattr(
        plan_menu,
        "apply_approved_group_plan_from_menu",
        lambda _detail, _state: calls.append("apply"),
    )
    selected = SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
    )
    activity = SimpleNamespace(class_id="class-1", activity_id="activity-1")
    plan_menu._open_plan(activity, selected, _state())
    assert calls == ["apply"]
