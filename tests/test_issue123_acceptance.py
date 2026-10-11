from __future__ import annotations

from pathlib import Path

import pytest

from concord.generated_paths import build_generated_output_token
from concord.workflows import (
    ActivityAnalysisReport,
    PreparedScoreAnalysisReport,
    RenderedScoreAnalysisArtifact,
    RenderedScoreAnalysisReport,
    ScoreAnalysisReportOutputError,
    ScoreAnalysisReportTechnicalMetadata,
    TargetKindScoreCount,
    install_rendered_score_analysis_report,
)

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "v0.3.1-activity-score-analysis-local-reports.md"
DOC_INDEX = ROOT / "docs" / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
REPORTS = ROOT / "concord" / "workflows" / "activity_score_reports.py"
OUTPUT = ROOT / "concord" / "workflows" / "activity_score_report_output.py"
PDF = ROOT / "concord" / "workflows" / "activity_score_report_pdf.py"
MENU = ROOT / "concord" / "menu_score_analysis_export.py"

CORE_064_SHA256 = (
    "48cea9317f2967bdc0f2d4c14349a56677c7c3f8211f0f33978ccb1a1c75859b"
)


def _prepared(package: Path) -> PreparedScoreAnalysisReport:
    payload = ActivityAnalysisReport(
        metadata=ScoreAnalysisReportTechnicalMetadata(
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=12,
            snapshot_sha256="a" * 64,
            generated_at="2026-10-04T13:00:00+00:00",
            report_scope="activity_analysis",
            score_basis="current_score_lineage_heads",
        ),
        activity_title="Synthetic Activity",
        current_score_count=0,
        target_kind_counts=(
            TargetKindScoreCount(
                target_kind="core_student",
                score_count=0,
            ),
        ),
        represented_criterion_count=0,
        represented_scoring_scale_count=0,
        criterion_analyses=(),
        standard_analyses=(),
        boundary_statements=("Descriptive only.",),
    )
    return PreparedScoreAnalysisReport(
        report_scope="activity_analysis",
        report_format="json",
        package_token=package.name,
        package_path=package,
        output_paths=(package / "report.json",),
        includes_target_level_rows=False,
        includes_history=False,
        includes_grade_or_proficiency_interpretation=False,
        payload=payload,
    )


def test_issue123_documentation_freezes_semantic_and_path_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    normalized = " ".join(text.split())
    required = (
        "descriptive Concord Score analysis",
        "current Score lineage heads only",
        "Score History",
        "core_student",
        "concord_group",
        "concord_artifact_instance",
        "concord_session",
        "concord_activity",
        "scored current judgments",
        "all current Score heads",
        "teacher_local",
        "concord_activity_score_analysis_v1",
        "activity_overview.csv",
        "criterion_distributions.csv",
        "score_dispositions.csv",
        "standards_criteria.csv",
        "target_scores.csv",
        "activity_analysis.pdf",
        "target_detail.pdf",
        "GENERATE",
        "build_generated_output_token",
        "build_human_readable_output_filename",
        "requires no workspace migration",
        "persists no separate report registry",
        "Academic Result Manifest",
        "Core Publication Record",
        "pds-core>=0.6.3,<0.7",
        CORE_064_SHA256,
    )
    for fragment in required:
        assert " ".join(fragment.split()) in normalized


def test_issue123_documentation_is_indexed_and_changelog_is_current() -> None:
    index = DOC_INDEX.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")
    assert "v0.3.1-activity-score-analysis-local-reports.md" in index
    assert "Issue #123" in changelog
    assert "Activity Score Analysis" in changelog
    assert "GENERATE" in changelog


def test_issue123_uses_shared_path_policy_without_local_naming_scheme() -> None:
    reports = REPORTS.read_text(encoding="utf-8")
    combined = "\n".join(
        (
            reports,
            OUTPUT.read_text(encoding="utf-8"),
            PDF.read_text(encoding="utf-8"),
            MENU.read_text(encoding="utf-8"),
        )
    )

    assert "build_generated_output_token(" in reports
    assert 'REPORT_PACKAGE_DOMAIN: Final[str] = "score-analysis-report"' in reports
    assert "build_human_readable_output_filename(" not in combined

    for fragment in (
        "slugify(",
        "sanitize_filename(",
        "truncate_filename(",
        "hash_filename(",
    ):
        assert fragment not in combined


def test_issue123_default_projection_omits_sensitive_surfaces() -> None:
    source = "\n".join(
        (
            REPORTS.read_text(encoding="utf-8"),
            OUTPUT.read_text(encoding="utf-8"),
            PDF.read_text(encoding="utf-8"),
        )
    ).casefold()
    for fragment in (
        "retained_source_relative_path",
        "route_id",
        "pds2_route_payload",
        "moderation_rationale",
        "evidence_link_id",
        "rationale=",
    ):
        assert fragment not in source


def test_issue123_report_services_do_not_invoke_publication_mutators() -> None:
    source = "\n".join(
        (
            REPORTS.read_text(encoding="utf-8"),
            OUTPUT.read_text(encoding="utf-8"),
            PDF.read_text(encoding="utf-8"),
        )
    )
    for fragment in (
        "register_concord_academic_work(",
        "generate_academic_result_manifest(",
        "publish_academic_result(",
        "publish_academic_result_manifest(",
    ):
        assert fragment not in source


def test_issue123_fixed_report_leaves_remain_bounded() -> None:
    source = REPORTS.read_text(encoding="utf-8")
    for fragment in (
        '"report.json"',
        '"activity_analysis.pdf"',
        '"target_detail.pdf"',
        '"activity_overview.csv"',
        '"criterion_distributions.csv"',
        '"score_dispositions.csv"',
        '"target_scores.csv"',
        '"standards_criteria.csv"',
    ):
        assert fragment in source


def test_issue123_installer_rejects_symlink_report_parent(
    tmp_path: Path,
) -> None:
    work = tmp_path / "work"
    outside = tmp_path / "outside"
    work.mkdir()
    outside.mkdir()

    exports = work / "exports"
    try:
        exports.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable on this platform")

    token = build_generated_output_token(
        domain="score-analysis-report",
        identity_parts=("class-1", "activity-1", "snapshot-12"),
    )
    package = exports / "score_analysis" / token
    prepared = _prepared(package)
    rendered = RenderedScoreAnalysisReport(
        report_scope="activity_analysis",
        report_format="json",
        artifacts=(
            RenderedScoreAnalysisArtifact(
                filename="report.json",
                media_type="application/json; charset=utf-8",
                content=b"{}\n",
            ),
        ),
    )

    with pytest.raises(
        ScoreAnalysisReportOutputError,
        match="non-symlink directory",
    ):
        install_rendered_score_analysis_report(prepared, rendered)

    assert not package.exists()


def test_issue123_report_identity_excludes_display_labels() -> None:
    reports = REPORTS.read_text(encoding="utf-8")
    start = reports.index("def _identity_parts(")
    end = reports.index("\ndef _package_token(", start)
    identity = reports[start:end]

    for fragment in (
        "activity_title",
        "target_label",
        "criterion_label",
        "scoring_scale_name",
        "standard_label",
        "group.label",
    ):
        assert fragment not in identity


def test_issue123_confirmation_is_literal_generate() -> None:
    source = MENU.read_text(encoding="utf-8")
    assert 'GENERATE_CONFIRMATION_TOKEN = "GENERATE"' in source
    assert "return raw == GENERATE_CONFIRMATION_TOKEN" in source
    assert "casefold() == GENERATE_CONFIRMATION_TOKEN" not in source
