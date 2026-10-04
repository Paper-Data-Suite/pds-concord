from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.workflows.activity_score_reports as reports
from concord.models import ScoreTargetReference
from concord.workflows import (
    SCORE_ANALYSIS_BASIS,
    ActivityScoreAnalysis,
    ActivityScoreObservation,
    TargetKindScoreCount,
    TargetScoreDetail,
    TargetScoreResult,
)
from concord.workflows.activity_read import ActivityReadContext


def _context(
    tmp_path: Path,
    *,
    title: str = "Synthetic Analysis Activity",
    revision: int = 12,
    snapshot_sha256: str = "a" * 64,
) -> ActivityReadContext:
    return cast(
        ActivityReadContext,
        SimpleNamespace(
            root=tmp_path,
            work=ModuleWorkRef(
                module_id="concord",
                class_id="class-1",
                work_id="activity-1",
            ),
            snapshot_revision=revision,
            snapshot_sha256=snapshot_sha256,
            activity=SimpleNamespace(
                activity_id="activity-1",
                title=title,
            ),
        ),
    )


def _analysis(
    *,
    title: str = "Synthetic Analysis Activity",
) -> ActivityScoreAnalysis:
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-private-001",
        owning_system="core",
    )
    observation = ActivityScoreObservation(
        score_record_id="score-private-001",
        target_reference=target,
        criterion_id="criterion-1",
        score_kind="local",
        standard_id=None,
        scoring_scale_id="scale-1",
        disposition="scored",
        value=3,
        basis="professional_judgment",
        session_id=None,
        scored_at="2026-10-03T14:00:00+00:00",
        supersedes_score_record_id=None,
    )
    return ActivityScoreAnalysis(
        class_id="class-1",
        activity_id="activity-1",
        activity_title=title,
        snapshot_revision=12,
        snapshot_sha256="a" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        current_score_count=1,
        target_kind_counts=(
            TargetKindScoreCount(
                target_kind="core_student",
                score_count=1,
            ),
        ),
        represented_criterion_count=0,
        represented_scoring_scale_count=1,
        criterion_analyses=(),
        standard_analyses=(),
        current_scores=(observation,),
    )


def _target_detail(
    *,
    target: ScoreTargetReference,
    label: str,
) -> TargetScoreDetail:
    return TargetScoreDetail(
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Synthetic Analysis Activity",
        snapshot_revision=12,
        snapshot_sha256="a" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope="teacher_local",
        target_reference=target,
        target_label=label,
        current_score_count=1,
        results=(
            TargetScoreResult(
                score_record_id="score-private-001",
                criterion_id="criterion-1",
                criterion_label="Uses Evidence",
                criterion_kind="local",
                standard_id=None,
                scoring_scale_id="scale-1",
                scoring_scale_name="Four Point Scale",
                scoring_scale_revision=1,
                scoring_scale_type="ordinal",
                disposition="scored",
                value=3,
                value_label="Meeting",
                basis="professional_judgment",
                session_id=None,
                scored_at="2026-10-03T14:00:00+00:00",
            ),
        ),
    )


def _clock(hour: int) -> object:
    return lambda: datetime(2026, 10, 3, hour, 0, tzinfo=timezone.utc)


def test_activity_report_projection_excludes_target_rows_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analysis = _analysis()
    monkeypatch.setattr(
        reports,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: analysis,
    )

    prepared = reports.prepare_activity_analysis_report(
        _context(tmp_path),
        report_format="json",
        clock=cast(object, _clock(15)),
    )

    assert prepared.includes_target_level_rows is False
    assert prepared.includes_history is False
    assert prepared.includes_grade_or_proficiency_interpretation is False
    payload = cast(reports.ActivityAnalysisReport, prepared.payload)
    assert "current_scores" not in {item.name for item in fields(payload)}
    assert payload.current_score_count == 1
    assert payload.metadata.snapshot_sha256 == "a" * 64
    assert reports.REPORT_BOUNDARY_STATEMENT in payload.boundary_statements
    assert (
        reports.CURRENT_HEAD_BOUNDARY_STATEMENT
        in payload.boundary_statements
    )


def test_activity_report_preparation_is_zero_write_and_uses_fixed_leaves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        reports,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: _analysis(),
    )
    before = tuple(sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*")))

    prepared = reports.prepare_activity_analysis_report(
        _context(tmp_path),
        report_format="csv",
        clock=cast(object, _clock(15)),
    )

    after = tuple(sorted(item.relative_to(tmp_path) for item in tmp_path.rglob("*")))
    assert after == before
    assert prepared.package_path.name.startswith("cgo_")
    assert prepared.package_path.parent.name == "score_analysis"
    assert tuple(item.name for item in prepared.output_paths) == (
        "activity_overview.csv",
        "criterion_distributions.csv",
        "score_dispositions.csv",
        "standards_criteria.csv",
    )
    assert not prepared.package_path.exists()


def test_generated_timestamp_does_not_change_canonical_package_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        reports,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: _analysis(),
    )
    context = _context(tmp_path)

    first = reports.prepare_activity_analysis_report(
        context,
        report_format="pdf",
        clock=cast(object, _clock(15)),
    )
    second = reports.prepare_activity_analysis_report(
        context,
        report_format="pdf",
        clock=cast(object, _clock(16)),
    )

    assert first.package_token == second.package_token
    assert first.package_path == second.package_path
    first_payload = cast(reports.ActivityAnalysisReport, first.payload)
    second_payload = cast(reports.ActivityAnalysisReport, second.payload)
    assert (
        first_payload.metadata.generated_at
        != second_payload.metadata.generated_at
    )


def test_long_display_labels_do_not_expand_canonical_report_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    long_title = "Activity " + ("Very Long Human Label " * 500)
    analysis = _analysis(title=long_title)
    monkeypatch.setattr(
        reports,
        "activity_score_analysis_from_context",
        lambda *args, **kwargs: analysis,
    )

    prepared = reports.prepare_activity_analysis_report(
        _context(tmp_path, title=long_title),
        report_format="pdf",
        clock=cast(object, _clock(15)),
    )

    assert long_title not in str(prepared.package_path)
    assert prepared.package_path.name.startswith("cgo_")
    assert prepared.output_paths[0].name == "activity_analysis.pdf"
    payload = cast(reports.ActivityAnalysisReport, prepared.payload)
    assert payload.activity_title == long_title


def test_target_report_identity_hashes_exact_target_and_keeps_teacher_label(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-private-001",
        owning_system="core",
    )
    label = "Jane Doe " + ("Very Long Display Name " * 200)
    detail = _target_detail(target=target, label=label)
    monkeypatch.setattr(
        reports,
        "target_score_detail_from_context",
        lambda *args, **kwargs: detail,
    )

    prepared = reports.prepare_target_detail_report(
        _context(tmp_path),
        target,
        report_format="pdf",
        clock=cast(object, _clock(15)),
    )

    payload = cast(reports.TargetDetailReport, prepared.payload)
    assert prepared.includes_target_level_rows is True
    assert prepared.output_paths[0].name == "target_detail.pdf"
    assert label not in str(prepared.package_path)
    assert target.target_id not in prepared.package_path.name
    assert payload.target_detail.target_label == label
    assert payload.metadata.target_reference == target
    assert (
        reports.TARGET_LOCAL_BOUNDARY_STATEMENT
        in payload.boundary_statements
    )


def test_different_target_identity_changes_target_report_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-private-001",
        owning_system="core",
    )
    second_target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-private-002",
        owning_system="core",
    )

    def fake_detail(
        context: ActivityReadContext,
        target: ScoreTargetReference,
        **kwargs: object,
    ) -> TargetScoreDetail:
        return _target_detail(target=target, label="Alex Smith")

    monkeypatch.setattr(
        reports,
        "target_score_detail_from_context",
        fake_detail,
    )

    first = reports.prepare_target_detail_report(
        _context(tmp_path),
        first_target,
        report_format="json",
        clock=cast(object, _clock(15)),
    )
    second = reports.prepare_target_detail_report(
        _context(tmp_path),
        second_target,
        report_format="json",
        clock=cast(object, _clock(15)),
    )

    assert first.package_token != second.package_token
    assert first.package_path != second.package_path
    assert first.output_paths[0].name == second.output_paths[0].name == "report.json"


@pytest.mark.parametrize("value", ("", "txt", "PDF", "xlsx"))
def test_report_format_is_bounded(value: str, tmp_path: Path) -> None:
    context = _context(tmp_path)
    with pytest.raises(ValueError, match="report_format"):
        reports._prepared(
            context,
            report_scope=reports.REPORT_SCOPE_ACTIVITY_ANALYSIS,
            report_format=value,
            target_reference=None,
            includes_target_level_rows=False,
            payload=cast(reports.ActivityAnalysisReport, SimpleNamespace()),
        )
