from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_score_analysis as menu_analysis
import concord.menu_scoring as menu_scoring
from concord.menu_context import MenuSessionContext
from concord.models import ScoreTargetReference
from concord.workflows import ActivityScoreAnalysis, ActivitySummary, WorkflowActor
from concord.workflows.activity_read import ActivityReadContext


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic Analysis Activity",
        status="active",
        scoring_orientation="local_criteria_only",
        session_count=1,
        group_count=0,
        snapshot_revision=12,
    )


def _analysis() -> ActivityScoreAnalysis:
    return cast(
        ActivityScoreAnalysis,
        SimpleNamespace(
            activity_title="Synthetic Analysis Activity",
            current_score_count=3,
            score_basis="current_score_lineage_heads",
            target_kind_counts=(
                SimpleNamespace(target_kind="core_student", score_count=2),
                SimpleNamespace(target_kind="concord_group", score_count=1),
            ),
            represented_criterion_count=2,
            represented_scoring_scale_count=1,
            criterion_analyses=(),
            standard_analyses=(),
            current_scores=(),
        ),
    )


def test_analysis_menu_loads_one_exact_context_for_all_views(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    context = cast(
        ActivityReadContext,
        SimpleNamespace(
            root="root",
            work=SimpleNamespace(class_id="class-1"),
        ),
    )
    loads: list[tuple[str, str]] = []
    views: list[str] = []
    answers = iter(("1", "2", "3", "4", "b"))

    def fake_load(class_id: str, activity_id: str) -> ActivityReadContext:
        loads.append((class_id, activity_id))
        return context

    monkeypatch.setattr(menu_analysis, "_load_activity_context", fake_load)
    monkeypatch.setattr(
        menu_analysis,
        "_student_label_resolver",
        lambda _context: lambda _target: None,
    )
    monkeypatch.setattr(
        menu_analysis,
        "load_menu_standards_library",
        lambda: None,
    )
    monkeypatch.setattr(
        menu_analysis,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: _analysis(),
    )
    monkeypatch.setattr(
        menu_analysis,
        "_criterion_view",
        lambda _analysis_value: views.append("criterion"),
    )
    monkeypatch.setattr(
        menu_analysis,
        "_target_view",
        lambda *args: views.append("target"),
    )
    monkeypatch.setattr(
        menu_analysis,
        "_standard_view",
        lambda _analysis_value: views.append("standard"),
    )
    monkeypatch.setattr(
        menu_analysis,
        "_history_view",
        lambda *args: views.append("history"),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_analysis, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_analysis, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_analysis, "print_navigation", lambda: None)

    menu_analysis.launch_score_analysis_menu(activity)

    assert loads == [("class-1", "activity-1")]
    assert views == ["criterion", "target", "standard", "history"]


def test_analysis_overview_states_descriptive_current_head_boundary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    context = cast(
        ActivityReadContext,
        SimpleNamespace(
            root="root",
            work=SimpleNamespace(class_id="class-1"),
        ),
    )
    monkeypatch.setattr(
        menu_analysis,
        "_load_activity_context",
        lambda *args: context,
    )
    monkeypatch.setattr(
        menu_analysis,
        "_student_label_resolver",
        lambda _context: lambda _target: None,
    )
    monkeypatch.setattr(
        menu_analysis,
        "load_menu_standards_library",
        lambda: None,
    )
    monkeypatch.setattr(
        menu_analysis,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: _analysis(),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")
    monkeypatch.setattr(menu_analysis, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_analysis, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_analysis, "print_navigation", lambda: None)

    menu_analysis.launch_score_analysis_menu(_activity())

    output = capsys.readouterr().out
    assert "Current Score records: 3" in output
    assert "Score basis: current_score_lineage_heads" in output
    assert "Students: 2" in output
    assert "Groups: 1" in output
    assert "no Grade, proficiency/mastery" in output
    assert "superseded revisions are available separately" in output


def test_score_task_menu_dispatches_review_score_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    calls: list[str] = []
    answers = iter(("4", "b"))

    monkeypatch.setattr(menu_scoring, "_latest", lambda value: value)
    monkeypatch.setattr(
        menu_scoring,
        "launch_score_analysis_menu",
        lambda selected: calls.append(selected.activity_id),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_scoring, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_scoring, "print_navigation", lambda: None)

    menu_scoring.launch_score_menu(
        activity,
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )

    assert calls == ["activity-1"]


def test_advanced_scoring_menu_dispatches_review_score_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    activity = _activity()
    calls: list[str] = []
    answers = iter(("7", "b"))

    monkeypatch.setattr(menu_scoring, "_latest", lambda value: value)
    monkeypatch.setattr(
        menu_scoring,
        "launch_score_analysis_menu",
        lambda selected: calls.append(selected.activity_id),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_scoring, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_scoring, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_scoring, "print_navigation", lambda: None)

    menu_scoring.launch_scoring_menu(
        activity,
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )

    assert calls == ["activity-1"]


def test_target_label_prefers_readable_student_name_over_machine_id() -> None:
    context = cast(
        ActivityReadContext,
        SimpleNamespace(
            activity=SimpleNamespace(activity_id="activity-1"),
            graph=SimpleNamespace(groups=(), sessions=()),
        ),
    )
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-123",
        owning_system="core",
    )

    label = menu_analysis._target_label(
        context,
        target,
        lambda item: "Jane Doe" if item == target else None,
    )

    assert label == "Jane Doe"
