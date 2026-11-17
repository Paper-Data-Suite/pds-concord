"""#149 Slice 3: read-only attention/readiness navigation and privacy.

No real teacher profile, workspace or academic records are used.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_activity as activity_menu
import concord.menu_attention as attention_menu
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import ReturnToMainMenu
from concord.workflows.activity_attention import (
    ActivityAttentionItem,
    ActivityAttentionSummary,
)
from concord.workflows.activity_lesson_readiness import LessonReadiness
from concord.workflows.models import ActivitySummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Six Cluster Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=17,
    )


def _summary(count: int = 1) -> ActivityAttentionSummary:
    return ActivityAttentionSummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Six Cluster Seminar",
        items=tuple(
            ActivityAttentionItem(
                code=f"synthetic-{i}",
                label=f"Synthetic category {i}",
                task="prepare",
                count=1,
                action_id="open_activity_prepare",
            )
            for i in range(count)
        ),
    )


def _report() -> LessonReadiness:
    return LessonReadiness(
        snapshot_revision=17,
        plan_stage="current_operational",
        operational_group_count=6,
        unused_proposal_count=1,
        pending_proposal_count=0,
        generated_packet_count=6,
        pending_packet_count=0,
        recovery_packet_count=0,
        routed_return_artifact_count=0,
        expected_without_routed_return_count=6,
        optional_return_artifact_count=0,
    )


def test_opened_activity_exposes_both_read_only_views_without_renumbering(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = SimpleNamespace(snapshot_revision=17)
    activity = _activity()
    state = MenuSessionContext()
    monkeypatch.setattr(activity_menu, "_load_activity_context", lambda *_a: context)
    monkeypatch.setattr(
        activity_menu, "activity_summary_from_context", lambda _c: activity
    )
    monkeypatch.setattr(
        activity_menu, "_inspect_activity_attention_from_context", lambda _c: _summary()
    )
    calls: list[object] = []
    monkeypatch.setattr(
        activity_menu,
        "launch_activity_prelesson_readiness",
        lambda ctx: calls.append(ctx),
    )
    monkeypatch.setattr(
        activity_menu, "launch_activity_attention_details", lambda x: calls.append(x)
    )
    monkeypatch.setattr(activity_menu, "clear_screen", lambda: None)
    answers = iter(("r", "d", "b"))
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    activity_menu.launch_activity_context_menu(activity, state)
    output = capsys.readouterr().out
    for number, name in enumerate(
        (
            "Plan",
            "Prepare",
            "Collect",
            "Review",
            "Score",
            "Share",
            "Advanced Activity tools",
        ),
        start=1,
    ):
        assert f"{number}. {name}" in output
    assert "R. Before class" in output
    assert "D. All attention categories" in output
    assert "A. Open next action" in output
    assert calls[0] is context
    assert isinstance(calls[1], ActivityAttentionSummary)


def test_before_class_reports_truthful_unknowns_and_optional_work(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(
        attention_menu, "inspect_lesson_readiness_from_context", lambda _c: _report()
    )
    monkeypatch.setattr("builtins.input", lambda _p="": "b")
    attention_menu.launch_activity_prelesson_readiness(SimpleNamespace())
    shown = capsys.readouterr().out
    assert "6 Clusters" in shown
    assert "1 alternative GroupPlan" in shown
    assert "Packets generated: 6" in shown
    assert "Printing/distribution: not verified" in shown
    assert "6 expected-return Artifact(s) have none" in shown
    assert "does not change classroom records" in shown
    assert "students scored" not in shown


def test_all_categories_paginates_without_implicitly_routing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)
    answers = iter(("n", "p", "b"))
    monkeypatch.setattr("builtins.input", lambda _p="": next(answers))
    attention_menu.launch_activity_attention_details(_summary(12))
    shown = capsys.readouterr().out
    assert "Synthetic category 0" in shown
    assert "Synthetic category 11" in shown
    assert "Page 2 of 2" in shown
    assert "not ranked by urgency" in shown


def test_empty_attention_does_not_claim_finished_academic_work(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _p="": "b")
    attention_menu.launch_activity_attention_details(_summary(0))
    shown = capsys.readouterr().out
    assert "No current actionable Concord attention categories" in shown
    assert "does not prove that physical returns or Scores exist" in shown


def test_unavailable_readiness_redacts_exception_and_student_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)

    def fail(_c: object) -> LessonReadiness:
        raise RuntimeError("student-secret /Users/Private/record.pdf")

    monkeypatch.setattr(attention_menu, "inspect_lesson_readiness_from_context", fail)
    monkeypatch.setattr("builtins.input", lambda _p="": "b")
    attention_menu.launch_activity_prelesson_readiness(SimpleNamespace())
    shown = capsys.readouterr().out
    assert "unavailable" in shown
    assert "student-secret" not in shown
    assert "record.pdf" not in shown


def test_details_main_menu_navigation_unwinds_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _p="": "m")
    with pytest.raises(ReturnToMainMenu):
        attention_menu.launch_activity_attention_details(_summary(1))


def test_eof_in_read_only_details_returns_without_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(attention_menu, "clear_screen", lambda: None)

    def eof(_p: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    attention_menu.launch_activity_attention_details(_summary(1))
    attention_menu.launch_activity_prelesson_readiness(None)
