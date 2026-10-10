from __future__ import annotations

import pytest
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
)

import concord.workflows.activity_score_report_pdf as score_pdf
from concord.cli_app.output import (
    print_activity_copy_preview,
    print_activity_detail,
)
from concord.menu_activity import _copy_review_lines
from concord.models import PrivacyPolicy
from concord.standards_display import (
    format_standard_display_label,
    resolve_profile_display,
    resolve_standard_display,
)
from concord.workflows import (
    ActivityAnalysisReport,
    ActivityDetail,
    ActivitySummary,
    CriterionScaleTargetAnalysis,
    CriterionScoreAnalysis,
    PreparedActivityCopy,
    ScaleValueDistribution,
    ScoreAnalysisReportTechnicalMetadata,
    StandardCriterionAnalysis,
    StandardScoreAnalysis,
    TargetKindScoreCount,
)

PROFILE_ID = "njsls-ela:profile.2023:11-12"
PROFILE_TITLE = "NJSLS ELA Grades 11–12"
STANDARD_ID = "njsls-ela:2023:rl-ts-11-12-4"
STANDARD_CODE = "RL.TS.11-12.4"
STANDARD_SHORT_NAME = "Analyze Text Structure"


def _library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD_ID,
                code=STANDARD_CODE,
                source="NJSLS ELA",
                short_name=STANDARD_SHORT_NAME,
                description="Analyze structural choices and their effects.",
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE_ID,
                standards=(STANDARD_ID,),
                subject="English Language Arts",
                title=PROFILE_TITLE,
            ),
        ),
    )


def _prepared_copy() -> PreparedActivityCopy:
    return PreparedActivityCopy(
        source_class_id="class-source",
        source_activity_id="activity-source",
        source_status="active",
        target_class_id="class-target",
        target_activity_id="activity-copy",
        title="Copied Activity",
        description=None,
        activity_type="project",
        scoring_orientation="standards_based",
        standards_profile_id=PROFILE_ID,
        focus_standard_ids=(STANDARD_ID,),
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        first_session_id="session-1",
        first_session_label="Day 1",
        diagnostics=(),
        excluded_state=("source Groups",),
        review_digest="a" * 64,
    )


def _activity_detail() -> ActivityDetail:
    return ActivityDetail(
        summary=ActivitySummary(
            class_id="class-1",
            activity_id="activity-1",
            title="Standards Activity",
            status="active",
            scoring_orientation="standards_based",
            session_count=1,
            group_count=0,
            snapshot_revision=4,
        ),
        description=None,
        activity_type="project",
        standards_profile_id=PROFILE_ID,
        focus_standard_ids=(STANDARD_ID,),
    )


def _analysis_payload() -> ActivityAnalysisReport:
    analysis_slice = CriterionScaleTargetAnalysis(
        criterion_id="criterion-1",
        criterion_label="Text Structure Analysis",
        criterion_kind="standard_backed",
        standard_id=STANDARD_ID,
        scoring_scale_id="scale-1",
        scoring_scale_lineage_id="scale-lineage-1",
        scoring_scale_name="Four Point Scale",
        scoring_scale_revision=1,
        scoring_scale_type="ordinal",
        target_kind="core_student",
        current_judgment_count=1,
        scored_count=1,
        non_score_count=0,
        value_distributions=(
            ScaleValueDistribution(
                value="meeting",
                label="Meeting",
                count=1,
                denominator=1,
                percentage="100.0",
            ),
        ),
        disposition_distributions=(),
    )
    criterion = CriterionScoreAnalysis(
        criterion_id="criterion-1",
        criterion_label="Text Structure Analysis",
        criterion_kind="standard_backed",
        standard_id=STANDARD_ID,
        current_judgment_count=1,
        slices=(analysis_slice,),
    )
    standard = StandardScoreAnalysis(
        standard_id=STANDARD_ID,
        standard_label=STANDARD_CODE,
        standard_code=STANDARD_CODE,
        standard_short_name=STANDARD_SHORT_NAME,
        criteria=(
            StandardCriterionAnalysis(
                criterion_id=criterion.criterion_id,
                criterion_label=criterion.criterion_label,
                current_judgment_count=1,
                slices=(analysis_slice,),
            ),
        ),
    )
    return ActivityAnalysisReport(
        metadata=ScoreAnalysisReportTechnicalMetadata(
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=4,
            snapshot_sha256="a" * 64,
            generated_at="2026-10-08T14:00:00+00:00",
            report_scope="activity_analysis",
            score_basis="current_score_lineage_heads",
        ),
        activity_title="Standards Activity",
        current_score_count=1,
        target_kind_counts=(
            TargetKindScoreCount(
                target_kind="core_student",
                score_count=1,
            ),
        ),
        represented_criterion_count=1,
        represented_scoring_scale_count=1,
        criterion_analyses=(criterion,),
        standard_analyses=(standard,),
        boundary_statements=("Descriptive only.",),
    )


def test_issue129_standard_depiction_keeps_identity_separate_from_display() -> None:
    display = resolve_standard_display(STANDARD_ID, _library())

    assert display.standard_id == STANDARD_ID
    assert display.code == STANDARD_CODE
    assert display.short_name == STANDARD_SHORT_NAME
    assert display.label == f"{STANDARD_CODE} — {STANDARD_SHORT_NAME}"

    profile = resolve_profile_display(PROFILE_ID, _library())
    assert profile.profile_id == PROFILE_ID
    assert profile.title == PROFILE_TITLE
    assert profile.label == PROFILE_TITLE


def test_issue129_missing_core_metadata_falls_back_to_exact_durable_identity() -> None:
    assert resolve_standard_display(STANDARD_ID, None).label == STANDARD_ID
    assert resolve_profile_display(PROFILE_ID, None).label == PROFILE_ID
    assert (
        format_standard_display_label(
            STANDARD_ID,
            code=None,
            short_name=None,
        )
        == STANDARD_ID
    )


def test_issue129_activity_copy_review_prefers_core_teacher_labels() -> None:
    lines = _copy_review_lines(
        _prepared_copy(),
        standards_library=_library(),
    )

    assert f"Standards profile: {PROFILE_TITLE}" in lines
    start = lines.index("Focus Standards (ordered):")
    assert lines[start + 1] == (
        f"  1. {STANDARD_CODE} — {STANDARD_SHORT_NAME}"
    )
    assert not any(STANDARD_ID in line for line in lines)


def test_issue129_activity_copy_review_falls_back_to_durable_ids() -> None:
    lines = _copy_review_lines(_prepared_copy())

    assert f"Standards profile: {PROFILE_ID}" in lines
    start = lines.index("Focus Standards (ordered):")
    assert lines[start + 1] == f"  1. {STANDARD_ID}"


def test_issue129_cli_copy_preview_and_activity_detail_use_core_labels(
    capsys: pytest.CaptureFixture[str],
) -> None:
    library = _library()

    print_activity_copy_preview(
        _prepared_copy(),
        standards_library=library,
    )
    preview = capsys.readouterr().out
    assert f"Standards profile: {PROFILE_TITLE}" in preview
    assert f"{STANDARD_CODE} — {STANDARD_SHORT_NAME}" in preview
    assert STANDARD_ID not in preview

    print_activity_detail(
        _activity_detail(),
        standards_library=library,
    )
    detail = capsys.readouterr().out
    assert f"Standards profile: {PROFILE_TITLE}" in detail
    assert f"Focus standards: {STANDARD_CODE} — {STANDARD_SHORT_NAME}" in detail
    assert STANDARD_ID not in detail


def test_issue129_cli_activity_detail_without_library_preserves_exact_fallback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    print_activity_detail(_activity_detail())
    output = capsys.readouterr().out

    assert f"Standards profile: {PROFILE_ID}" in output
    assert f"Focus standards: {STANDARD_ID}" in output


def test_issue129_activity_score_pdf_uses_teacher_label_not_raw_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paragraphs: list[str] = []
    tables: list[tuple[tuple[str, ...], tuple[tuple[str, ...], ...]]] = []

    original_paragraph = score_pdf._ReportPainter.paragraph
    original_table = score_pdf._ReportPainter.table

    def capture_paragraph(
        self: object,
        text: str,
        *args: object,
        **kwargs: object,
    ) -> None:
        paragraphs.append(text)
        original_paragraph(self, text, *args, **kwargs)

    def capture_table(
        self: object,
        headers: object,
        rows: object,
        widths: object,
    ) -> None:
        header_tuple = tuple(headers)  # type: ignore[arg-type]
        row_tuple = tuple(tuple(row) for row in rows)  # type: ignore[arg-type]
        tables.append((header_tuple, row_tuple))
        original_table(self, header_tuple, row_tuple, widths)  # type: ignore[arg-type]

    monkeypatch.setattr(score_pdf._ReportPainter, "paragraph", capture_paragraph)
    monkeypatch.setattr(score_pdf._ReportPainter, "table", capture_table)

    images = score_pdf._activity_images(_analysis_payload())
    try:
        teacher_label = f"{STANDARD_CODE} — {STANDARD_SHORT_NAME}"
        assert f"Standard: {teacher_label}" in paragraphs
        assert not any(text.startswith("Standard ID:") for text in paragraphs)
        standards_tables = [
            rows
            for headers, rows in tables
            if headers and headers[0] == "Standard"
        ]
        assert standards_tables
        assert standards_tables[0][0][0] == teacher_label
    finally:
        for image in images:
            image.close()
