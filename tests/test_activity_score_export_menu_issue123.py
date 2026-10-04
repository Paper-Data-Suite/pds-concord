from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.menu_score_analysis as menu_analysis
import concord.menu_score_analysis_export as menu_export
from concord.models import ScoreTargetReference
from concord.workflows import (
    SCORE_ANALYSIS_BASIS,
    ActivityAnalysisReport,
    ActivityScoreAnalysis,
    ActivitySummary,
    InstalledScoreAnalysisReport,
    PreparedScoreAnalysisReport,
    ScoreAnalysisReportTechnicalMetadata,
    TargetKindScoreCount,
)
from concord.workflows.activity_read import ActivityReadContext


def _context(tmp_path: Path) -> ActivityReadContext:
    return cast(
        ActivityReadContext,
        SimpleNamespace(
            root=tmp_path,
            work=ModuleWorkRef(
                module_id="concord",
                class_id="class-1",
                work_id="activity-1",
            ),
            activity=SimpleNamespace(
                activity_id="activity-1",
                title="Seminar Reflection",
            ),
        ),
    )


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Seminar Reflection",
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
            activity_title="Seminar Reflection",
            current_score_count=3,
            score_basis=SCORE_ANALYSIS_BASIS,
            target_kind_counts=(
                TargetKindScoreCount(
                    target_kind="core_student",
                    score_count=3,
                ),
            ),
            represented_criterion_count=1,
            represented_scoring_scale_count=1,
            criterion_analyses=(),
            standard_analyses=(),
            current_scores=(),
        ),
    )


def _prepared(tmp_path: Path) -> PreparedScoreAnalysisReport:
    package = tmp_path / "exports" / "score_analysis" / ("cgo_" + "a" * 24)
    payload = ActivityAnalysisReport(
        metadata=ScoreAnalysisReportTechnicalMetadata(
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=12,
            snapshot_sha256="b" * 64,
            generated_at="2026-10-04T13:00:00+00:00",
            report_scope="activity_analysis",
            score_basis=SCORE_ANALYSIS_BASIS,
        ),
        activity_title="Seminar Reflection",
        current_score_count=3,
        target_kind_counts=(
            TargetKindScoreCount(
                target_kind="core_student",
                score_count=3,
            ),
        ),
        represented_criterion_count=1,
        represented_scoring_scale_count=1,
        criterion_analyses=(),
        standard_analyses=(),
        boundary_statements=("Descriptive only.",),
    )
    return PreparedScoreAnalysisReport(
        report_scope="activity_analysis",
        report_format="pdf",
        package_token=package.name,
        package_path=package,
        output_paths=(package / "activity_analysis.pdf",),
        includes_target_level_rows=False,
        includes_history=False,
        includes_grade_or_proficiency_interpretation=False,
        payload=payload,
    )


def test_preview_states_exact_scope_destination_and_boundaries(
    tmp_path: Path,
) -> None:
    prepared = _prepared(tmp_path)

    text = "\n".join(menu_export.format_score_report_preview(prepared))

    assert "Class: class-1" in text
    assert "Activity: Seminar Reflection" in text
    assert "Scope: Activity Analysis" in text
    assert "Score basis: current_score_lineage_heads" in text
    assert "Current Score records represented: 3" in text
    assert "Includes target-level rows: No" in text
    assert "Includes Score history: No" in text
    assert "Includes Grade/proficiency interpretation: No" in text
    assert "Format: PDF" in text
    assert prepared.package_path.as_posix() in text
    assert "activity_analysis.pdf" in text


def test_cancel_before_generate_executes_no_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    choices = iter(("activity_analysis", "pdf"))
    executed: list[PreparedScoreAnalysisReport] = []

    monkeypatch.setattr(
        menu_export,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )
    monkeypatch.setattr(
        menu_export,
        "prepare_activity_analysis_report",
        lambda *args, **kwargs: prepared,
    )
    monkeypatch.setattr(
        menu_export,
        "execute_prepared_score_analysis_report",
        lambda value: executed.append(value),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")
    monkeypatch.setattr(menu_export, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_export, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_export, "print_navigation", lambda: None)
    monkeypatch.setattr(menu_export, "show_result", lambda *args: None)

    result = menu_export.launch_score_report_export(
        _context(tmp_path),
        _analysis(),
        target_labeler=lambda target: target.target_id,
        target_label_resolver=None,
        standards_library=None,
    )

    assert result is None
    assert executed == []
    assert not prepared.package_path.exists()


def test_only_exact_generate_token_executes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    choices = iter(("activity_analysis", "pdf"))
    installed = InstalledScoreAnalysisReport(
        package_path=prepared.package_path,
        output_paths=prepared.output_paths,
        created_output_paths=prepared.output_paths,
        reused_output_paths=(),
    )
    executed: list[PreparedScoreAnalysisReport] = []
    shown: list[str] = []

    monkeypatch.setattr(
        menu_export,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )
    monkeypatch.setattr(
        menu_export,
        "prepare_activity_analysis_report",
        lambda *args, **kwargs: prepared,
    )

    def fake_execute(
        value: PreparedScoreAnalysisReport,
    ) -> InstalledScoreAnalysisReport:
        executed.append(value)
        return installed

    monkeypatch.setattr(
        menu_export,
        "execute_prepared_score_analysis_report",
        fake_execute,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "GENERATE")
    monkeypatch.setattr(menu_export, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_export, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_export, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_export,
        "show_result",
        lambda title, lines: shown.append(title),
    )

    result = menu_export.launch_score_report_export(
        _context(tmp_path),
        _analysis(),
        target_labeler=lambda target: target.target_id,
        target_label_resolver=None,
        standards_library=None,
    )

    assert result == installed
    assert executed == [prepared]
    assert shown == ["Score Analysis Report Ready"]


@pytest.mark.parametrize("confirmation", ("generate", "Generate", "YES", "G"))
def test_non_exact_generate_token_is_cancelled(
    confirmation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = _prepared(tmp_path)
    choices = iter(("activity_analysis", "pdf"))
    executed: list[PreparedScoreAnalysisReport] = []

    monkeypatch.setattr(
        menu_export,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )
    monkeypatch.setattr(
        menu_export,
        "prepare_activity_analysis_report",
        lambda *args, **kwargs: prepared,
    )
    monkeypatch.setattr(
        menu_export,
        "execute_prepared_score_analysis_report",
        lambda value: executed.append(value),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": confirmation)
    monkeypatch.setattr(menu_export, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_export, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_export, "print_navigation", lambda: None)
    monkeypatch.setattr(menu_export, "show_result", lambda *args: None)

    result = menu_export.launch_score_report_export(
        _context(tmp_path),
        _analysis(),
        target_labeler=lambda target: target.target_id,
        target_label_resolver=None,
        standards_library=None,
    )

    assert result is None
    assert executed == []


def test_target_export_selects_exact_current_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )
    analysis = cast(
        ActivityScoreAnalysis,
        SimpleNamespace(
            current_scores=(SimpleNamespace(target_reference=target),),
        ),
    )
    choices = iter(("target_detail", "json", target))
    prepared = _prepared(tmp_path)
    received: list[ScoreTargetReference] = []

    monkeypatch.setattr(
        menu_export,
        "select_one",
        lambda *args, **kwargs: next(choices),
    )

    def fake_prepare(
        context: ActivityReadContext,
        selected: ScoreTargetReference,
        **kwargs: object,
    ) -> PreparedScoreAnalysisReport:
        received.append(selected)
        return prepared

    monkeypatch.setattr(
        menu_export,
        "prepare_target_detail_report",
        fake_prepare,
    )
    monkeypatch.setattr(
        menu_export,
        "_confirm_generate",
        lambda value: False,
    )
    monkeypatch.setattr(menu_export, "show_result", lambda *args: None)

    menu_export.launch_score_report_export(
        _context(tmp_path),
        analysis,
        target_labeler=lambda value: "Jane Doe",
        target_label_resolver=None,
        standards_library=None,
    )

    assert received == [target]


def test_analysis_menu_routes_export_through_same_loaded_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _context(tmp_path)
    analysis = _analysis()
    calls: list[tuple[ActivityReadContext, ActivityScoreAnalysis]] = []
    answers = iter(("5", "b"))

    monkeypatch.setattr(
        menu_analysis,
        "_load_activity_context",
        lambda *args: context,
    )
    monkeypatch.setattr(
        menu_analysis,
        "_student_label_resolver",
        lambda value: lambda target: None,
    )
    monkeypatch.setattr(
        menu_analysis,
        "load_menu_standards_library",
        lambda root=None: None,
    )
    monkeypatch.setattr(
        menu_analysis,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: analysis,
    )

    def fake_export(
        export_context: ActivityReadContext,
        export_analysis: ActivityScoreAnalysis,
        **kwargs: object,
    ) -> None:
        calls.append((export_context, export_analysis))

    monkeypatch.setattr(
        menu_analysis,
        "launch_score_report_export",
        fake_export,
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(menu_analysis, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_analysis, "print_menu_header", lambda *args: None)
    monkeypatch.setattr(menu_analysis, "print_navigation", lambda: None)

    menu_analysis.launch_score_analysis_menu(_activity())

    assert calls == [(context, analysis)]
