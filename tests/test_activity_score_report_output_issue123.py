from __future__ import annotations

import csv
import io
import json
from dataclasses import replace
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from concord.generated_paths import build_generated_output_token
from concord.models import ScoreTargetReference
from concord.workflows import (
    SCORE_ANALYSIS_BASIS,
    ActivityAnalysisReport,
    CriterionScaleTargetAnalysis,
    CriterionScoreAnalysis,
    DispositionDistribution,
    PreparedScoreAnalysisReport,
    ScaleValueDistribution,
    ScoreAnalysisReportTechnicalMetadata,
    StandardCriterionAnalysis,
    StandardScoreAnalysis,
    TargetDetailReport,
    TargetKindScoreCount,
    TargetScoreDetail,
    TargetScoreResult,
)
from concord.workflows.activity_score_report_output import (
    LOCAL_REPORT_SCHEMA_VERSION,
    ScoreAnalysisReportOutputError,
    execute_prepared_score_analysis_report,
    render_score_analysis_report_csv,
    render_score_analysis_report_json,
)
from concord.workflows.activity_score_report_pdf import (
    PDF_MEDIA_TYPE,
    render_score_analysis_report_pdf,
)


def _token(scope: str) -> str:
    return build_generated_output_token(
        domain="score-analysis-report",
        identity_parts=("class-1", "activity-1", "snapshot-12", scope),
    )


def _package(tmp_path: Path, scope: str) -> Path:
    work = tmp_path / "managed-work"
    work.mkdir(exist_ok=True)
    return work / "exports" / "score_analysis" / _token(scope)


def _slice() -> CriterionScaleTargetAnalysis:
    return CriterionScaleTargetAnalysis(
        criterion_id="criterion-1",
        criterion_label="Uses Evidence",
        criterion_kind="standard_backed",
        standard_id="standard-1",
        scoring_scale_id="scale-1",
        scoring_scale_lineage_id="scale-lineage-1",
        scoring_scale_name="Four Point Scale",
        scoring_scale_revision=2,
        scoring_scale_type="ordinal",
        target_kind="core_student",
        current_judgment_count=3,
        scored_count=3,
        non_score_count=0,
        value_distributions=(
            ScaleValueDistribution(
                value=1,
                label="Beginning",
                count=1,
                denominator=3,
                percentage="33.3",
            ),
            ScaleValueDistribution(
                value=3,
                label="Meeting",
                count=2,
                denominator=3,
                percentage="66.7",
            ),
        ),
        disposition_distributions=(
            DispositionDistribution(
                disposition="scored",
                count=3,
                denominator=3,
                percentage="100.0",
            ),
        ),
    )


def _activity_payload(
    *,
    generated_at: str = "2026-10-03T15:00:00+00:00",
    title: str = "Seminar Reflection",
) -> ActivityAnalysisReport:
    item = _slice()
    criterion = CriterionScoreAnalysis(
        criterion_id=item.criterion_id,
        criterion_label=item.criterion_label,
        criterion_kind=item.criterion_kind,
        standard_id=item.standard_id,
        current_judgment_count=3,
        slices=(item,),
    )
    standard = StandardScoreAnalysis(
        standard_id="standard-1",
        standard_label="RL.CR.11-12.1",
        standard_code="RL.CR.11-12.1",
        standard_short_name="Cite Textual Evidence",
        criteria=(
            StandardCriterionAnalysis(
                criterion_id=criterion.criterion_id,
                criterion_label=criterion.criterion_label,
                current_judgment_count=3,
                slices=(item,),
            ),
        ),
    )
    return ActivityAnalysisReport(
        metadata=ScoreAnalysisReportTechnicalMetadata(
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=12,
            snapshot_sha256="a" * 64,
            generated_at=generated_at,
            report_scope="activity_analysis",
            score_basis=SCORE_ANALYSIS_BASIS,
        ),
        activity_title=title,
        current_score_count=3,
        target_kind_counts=(
            TargetKindScoreCount(
                target_kind="core_student",
                score_count=3,
            ),
        ),
        represented_criterion_count=1,
        represented_scoring_scale_count=1,
        criterion_analyses=(criterion,),
        standard_analyses=(standard,),
        boundary_statements=("Descriptive only.",),
    )


def _activity_prepared(
    tmp_path: Path,
    *,
    report_format: str,
    generated_at: str = "2026-10-03T15:00:00+00:00",
    title: str = "Seminar Reflection",
) -> PreparedScoreAnalysisReport:
    package = _package(tmp_path, "activity_analysis")
    leaves = {
        "json": ("report.json",),
        "csv": (
            "activity_overview.csv",
            "criterion_distributions.csv",
            "score_dispositions.csv",
            "standards_criteria.csv",
        ),
    }[report_format]
    return PreparedScoreAnalysisReport(
        report_scope="activity_analysis",
        report_format=report_format,
        package_token=package.name,
        package_path=package,
        output_paths=tuple(package / leaf for leaf in leaves),
        includes_target_level_rows=False,
        includes_history=False,
        includes_grade_or_proficiency_interpretation=False,
        payload=_activity_payload(
            generated_at=generated_at,
            title=title,
        ),
    )


def _target_prepared(
    tmp_path: Path,
    *,
    report_format: str,
) -> PreparedScoreAnalysisReport:
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-private-001",
        owning_system="core",
    )
    package = _package(tmp_path, "target_detail")
    detail = TargetScoreDetail(
        class_id="class-1",
        activity_id="activity-1",
        activity_title="Seminar Reflection",
        snapshot_revision=12,
        snapshot_sha256="a" * 64,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope="teacher_local",
        target_reference=target,
        target_label="Jane Doe",
        current_score_count=1,
        results=(
            TargetScoreResult(
                score_record_id="score-1",
                criterion_id="criterion-1",
                criterion_label="Uses Evidence",
                criterion_kind="standard_backed",
                standard_id="standard-1",
                scoring_scale_id="scale-1",
                scoring_scale_name="Four Point Scale",
                scoring_scale_revision=2,
                scoring_scale_type="ordinal",
                disposition="scored",
                value="1",
                value_label="Meeting",
                basis="professional_judgment",
                session_id=None,
                scored_at="2026-10-03T14:00:00+00:00",
            ),
        ),
    )
    payload = TargetDetailReport(
        metadata=ScoreAnalysisReportTechnicalMetadata(
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=12,
            snapshot_sha256="a" * 64,
            generated_at="2026-10-03T15:00:00+00:00",
            report_scope="target_detail",
            score_basis=SCORE_ANALYSIS_BASIS,
            target_reference=target,
        ),
        activity_title="Seminar Reflection",
        target_detail=detail,
        boundary_statements=("Teacher-local.",),
    )
    leaf = "report.json" if report_format == "json" else "target_scores.csv"
    return PreparedScoreAnalysisReport(
        report_scope="target_detail",
        report_format=report_format,
        package_token=package.name,
        package_path=package,
        output_paths=(package / leaf,),
        includes_target_level_rows=True,
        includes_history=False,
        includes_grade_or_proficiency_interpretation=False,
        payload=payload,
    )


def test_json_is_versioned_deterministic_and_preserves_derived_percentages(
    tmp_path: Path,
) -> None:
    prepared = _activity_prepared(tmp_path, report_format="json")

    first = render_score_analysis_report_json(prepared)
    second = render_score_analysis_report_json(prepared)

    assert first == second
    data = json.loads(first.artifacts[0].content)
    assert data["schema_version"] == LOCAL_REPORT_SCHEMA_VERSION
    assert data["metadata"]["snapshot_sha256"] == "a" * 64
    values = data["criterion_analysis"][0]["slices"][0]["value_distributions"]
    assert values[1]["count"] == 2
    assert values[1]["denominator"] == 3
    assert values[1]["percentage"] == "66.7"
    assert "current_scores" not in data


def test_activity_csv_uses_fixed_leaves_and_precomputed_percentages(
    tmp_path: Path,
) -> None:
    prepared = _activity_prepared(tmp_path, report_format="csv")
    rendered = render_score_analysis_report_csv(prepared)

    assert tuple(item.filename for item in rendered.artifacts) == (
        "activity_overview.csv",
        "criterion_distributions.csv",
        "score_dispositions.csv",
        "standards_criteria.csv",
    )
    rows = tuple(
        csv.DictReader(
            io.StringIO(rendered.artifacts[1].content.decode("utf-8"))
        )
    )
    assert rows[1]["value"] == "3"
    assert rows[1]["count"] == "2"
    assert rows[1]["scored_denominator"] == "3"
    assert rows[1]["percent"] == "66.7"


def test_target_csv_uses_display_identity_without_raw_target_id(
    tmp_path: Path,
) -> None:
    prepared = _target_prepared(tmp_path, report_format="csv")
    rendered = render_score_analysis_report_csv(prepared)

    content = rendered.artifacts[0].content.decode("utf-8")
    rows = tuple(csv.DictReader(io.StringIO(content)))
    assert rows[0]["target_display"] == "Jane Doe"
    assert rows[0]["target_kind"] == "core_student"
    assert rows[0]["value"] == '"1"'
    assert "student-private-001" not in content


def test_execution_creates_bounded_package_without_overwrite(
    tmp_path: Path,
) -> None:
    prepared = _activity_prepared(tmp_path, report_format="json")

    installed = execute_prepared_score_analysis_report(prepared)

    assert installed.package_path == prepared.package_path
    assert installed.created_output_paths == prepared.output_paths
    assert installed.reused_output_paths == ()
    assert prepared.output_paths[0].is_file()


def test_same_json_identity_reuses_first_generation_timestamp(
    tmp_path: Path,
) -> None:
    first = _activity_prepared(
        tmp_path,
        report_format="json",
        generated_at="2026-10-03T15:00:00+00:00",
    )
    first_install = execute_prepared_score_analysis_report(first)
    original = first.output_paths[0].read_bytes()

    second = _activity_prepared(
        tmp_path,
        report_format="json",
        generated_at="2026-10-03T16:00:00+00:00",
    )
    second_install = execute_prepared_score_analysis_report(second)

    assert first_install.reused is False
    assert second_install.reused is True
    assert second_install.created_output_paths == ()
    assert second_install.reused_output_paths == second.output_paths
    assert second.output_paths[0].read_bytes() == original
    stored = json.loads(original)
    assert stored["metadata"]["generated_at"] == "2026-10-03T15:00:00+00:00"


def test_conflicting_existing_json_fails_without_replacement(
    tmp_path: Path,
) -> None:
    original = _activity_prepared(tmp_path, report_format="json")
    execute_prepared_score_analysis_report(original)
    before = original.output_paths[0].read_bytes()

    conflicting = _activity_prepared(
        tmp_path,
        report_format="json",
        title="Changed report content without changed canonical identity",
    )
    with pytest.raises(ScoreAnalysisReportOutputError, match="conflicts"):
        execute_prepared_score_analysis_report(conflicting)

    assert original.output_paths[0].read_bytes() == before


def test_json_and_csv_can_share_one_exact_report_package(
    tmp_path: Path,
) -> None:
    json_report = _activity_prepared(tmp_path, report_format="json")
    csv_report = _activity_prepared(tmp_path, report_format="csv")

    execute_prepared_score_analysis_report(json_report)
    csv_install = execute_prepared_score_analysis_report(csv_report)

    assert csv_install.created_output_paths == csv_report.output_paths
    names = {item.name for item in json_report.package_path.iterdir()}
    assert names == {
        "report.json",
        "activity_overview.csv",
        "criterion_distributions.csv",
        "score_dispositions.csv",
        "standards_criteria.csv",
    }


def test_unexpected_existing_package_entry_blocks_generation(
    tmp_path: Path,
) -> None:
    prepared = _activity_prepared(tmp_path, report_format="csv")
    prepared.package_path.mkdir(parents=True)
    unexpected = prepared.package_path / "student-private-001.txt"
    unexpected.write_text("unexpected", encoding="utf-8")

    with pytest.raises(ScoreAnalysisReportOutputError, match="unexpected entry"):
        execute_prepared_score_analysis_report(prepared)

    assert tuple(path for path in prepared.output_paths if path.exists()) == ()


def _pdf_activity_prepared(
    tmp_path: Path,
    *,
    payload: ActivityAnalysisReport | None = None,
) -> PreparedScoreAnalysisReport:
    base = _activity_prepared(tmp_path, report_format="json")
    return replace(
        base,
        report_format="pdf",
        output_paths=(base.package_path / "activity_analysis.pdf",),
        payload=base.payload if payload is None else payload,
    )


def _pdf_target_prepared(tmp_path: Path) -> PreparedScoreAnalysisReport:
    base = _target_prepared(tmp_path, report_format="json")
    return replace(
        base,
        report_format="pdf",
        output_paths=(base.package_path / "target_detail.pdf",),
    )


def _pdf_page_count(data: bytes) -> int:
    document = pdfium.PdfDocument(data)
    try:
        return len(document)
    finally:
        document.close()


def test_activity_pdf_is_deterministic_readable_and_fixed_leaf(
    tmp_path: Path,
) -> None:
    prepared = _pdf_activity_prepared(tmp_path)

    first = render_score_analysis_report_pdf(prepared)
    second = render_score_analysis_report_pdf(prepared)

    assert first == second
    assert first.report_format == "pdf"
    assert first.artifacts[0].filename == "activity_analysis.pdf"
    assert first.artifacts[0].media_type == PDF_MEDIA_TYPE
    assert first.artifacts[0].content.startswith(b"%PDF")
    assert _pdf_page_count(first.artifacts[0].content) >= 1


def test_activity_pdf_paginates_large_analysis_without_shrinking(
    tmp_path: Path,
) -> None:
    base = _activity_payload()
    large = replace(
        base,
        criterion_analyses=base.criterion_analyses * 30,
        standard_analyses=base.standard_analyses * 8,
    )
    prepared = _pdf_activity_prepared(tmp_path, payload=large)

    rendered = render_score_analysis_report_pdf(prepared)

    assert _pdf_page_count(rendered.artifacts[0].content) > 1


def test_target_pdf_uses_teacher_local_fixed_leaf_without_raw_target_id(
    tmp_path: Path,
) -> None:
    prepared = _pdf_target_prepared(tmp_path)

    rendered = render_score_analysis_report_pdf(prepared)

    artifact = rendered.artifacts[0]
    assert artifact.filename == "target_detail.pdf"
    assert artifact.content.startswith(b"%PDF")
    assert b"student-private-001" not in artifact.content
    assert _pdf_page_count(artifact.content) >= 1


def test_pdf_execution_uses_shared_bounded_installer_and_reuse(
    tmp_path: Path,
) -> None:
    prepared = _pdf_activity_prepared(tmp_path)

    first = execute_prepared_score_analysis_report(prepared)
    before = prepared.output_paths[0].read_bytes()
    second = execute_prepared_score_analysis_report(prepared)

    assert first.created_output_paths == prepared.output_paths
    assert second.reused is True
    assert second.reused_output_paths == prepared.output_paths
    assert prepared.output_paths[0].read_bytes() == before
