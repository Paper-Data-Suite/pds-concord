"""Immutable preparation for local descriptive Activity Score reports."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypeAlias

from pds_core.standards import StandardsLibrary

from concord.generated_paths import build_generated_output_token
from concord.models import ScoreTargetReference
from concord.storage_paths import work_root
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.activity_score_analysis import (
    SCORE_ANALYSIS_BASIS,
    ActivityScoreAnalysis,
    CriterionScoreAnalysis,
    StandardScoreAnalysis,
    TargetDisplayLabelResolver,
    TargetKindScoreCount,
    TargetScoreDetail,
    activity_score_analysis_from_context,
    target_score_detail_from_context,
)
from concord.workflows.context import Clock, workflow_timestamp

REPORT_SCOPE_ACTIVITY_ANALYSIS: Final[str] = "activity_analysis"
REPORT_SCOPE_TARGET_DETAIL: Final[str] = "target_detail"
REPORT_FORMATS: Final[tuple[str, ...]] = ("json", "csv", "pdf")
REPORT_PACKAGE_DOMAIN: Final[str] = "score-analysis-report"

REPORT_BOUNDARY_STATEMENT: Final[str] = (
    "Concord Activity Score Analysis describes current Concord Score records. "
    "It does not calculate Grades, proficiency/mastery, required/missing "
    "Scores, or Academic Period results."
)
CURRENT_HEAD_BOUNDARY_STATEMENT: Final[str] = (
    "Current analysis uses current Score lineage heads; superseded revisions "
    "are available separately through Score history."
)
STANDARDS_BOUNDARY_STATEMENT: Final[str] = (
    "Standards sections group existing standard-backed Criteria. Concord does "
    "not convert these distributions into standards proficiency."
)
TARGET_LOCAL_BOUNDARY_STATEMENT: Final[str] = (
    "This Target Detail report is teacher-local descriptive output. It is not "
    "automatically student-facing, parent-facing, share-safe, or a Grade report."
)

ReportPayload: TypeAlias = "ActivityAnalysisReport | TargetDetailReport"


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreAnalysisReportTechnicalMetadata:
    """Exact technical identity kept separate from ordinary presentation."""

    class_id: str
    activity_id: str
    snapshot_revision: int
    snapshot_sha256: str
    generated_at: str
    report_scope: str
    score_basis: str
    target_reference: ScoreTargetReference | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityAnalysisReport:
    """Privacy-minimized aggregate Activity report payload."""

    metadata: ScoreAnalysisReportTechnicalMetadata
    activity_title: str
    current_score_count: int
    target_kind_counts: tuple[TargetKindScoreCount, ...]
    represented_criterion_count: int
    represented_scoring_scale_count: int
    criterion_analyses: tuple[CriterionScoreAnalysis, ...]
    standard_analyses: tuple[StandardScoreAnalysis, ...]
    boundary_statements: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetDetailReport:
    """Exact teacher-local Target Detail payload."""

    metadata: ScoreAnalysisReportTechnicalMetadata
    activity_title: str
    target_detail: TargetScoreDetail
    boundary_statements: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedScoreAnalysisReport:
    """Zero-write exact report preparation result."""

    report_scope: str
    report_format: str
    package_token: str
    package_path: Path
    output_paths: tuple[Path, ...]
    includes_target_level_rows: bool
    includes_history: bool
    includes_grade_or_proficiency_interpretation: bool
    payload: ReportPayload


def _report_format(value: str) -> str:
    if value not in REPORT_FORMATS:
        raise ValueError(
            "report_format must be one of: " + ", ".join(REPORT_FORMATS)
        )
    return value


def _identity_parts(
    context: ActivityReadContext,
    *,
    report_scope: str,
    target_reference: ScoreTargetReference | None,
) -> tuple[str, ...]:
    values = [
        "module",
        context.work.module_id,
        "class",
        context.work.class_id,
        "work",
        context.work.work_id,
        "activity",
        context.activity.activity_id,
        "snapshot-revision",
        str(context.snapshot_revision),
        "snapshot-sha256",
        context.snapshot_sha256,
        "report-scope",
        report_scope,
        "score-population",
        SCORE_ANALYSIS_BASIS,
    ]
    if target_reference is not None:
        values.extend(
            (
                "target-kind",
                target_reference.target_kind,
                "target-owner",
                target_reference.owning_system,
                "target-id",
                target_reference.target_id,
                "target-contract",
                target_reference.contract_version or "-",
            )
        )
    return tuple(values)


def _package_token(
    context: ActivityReadContext,
    *,
    report_scope: str,
    target_reference: ScoreTargetReference | None,
) -> str:
    return build_generated_output_token(
        domain=REPORT_PACKAGE_DOMAIN,
        identity_parts=_identity_parts(
            context,
            report_scope=report_scope,
            target_reference=target_reference,
        ),
    )


def _package_path(
    context: ActivityReadContext,
    token: str,
) -> Path:
    return (
        work_root(context.root, context.work)
        / "exports"
        / "score_analysis"
        / token
    )


def _fixed_leaves(
    report_scope: str,
    report_format: str,
) -> tuple[str, ...]:
    if report_scope == REPORT_SCOPE_ACTIVITY_ANALYSIS:
        if report_format == "json":
            return ("report.json",)
        if report_format == "pdf":
            return ("activity_analysis.pdf",)
        return (
            "activity_overview.csv",
            "criterion_distributions.csv",
            "score_dispositions.csv",
            "standards_criteria.csv",
        )
    if report_scope == REPORT_SCOPE_TARGET_DETAIL:
        if report_format == "json":
            return ("report.json",)
        if report_format == "pdf":
            return ("target_detail.pdf",)
        return ("target_scores.csv",)
    raise ValueError(f"unsupported report scope: {report_scope}")


def _prepared(
    context: ActivityReadContext,
    *,
    report_scope: str,
    report_format: str,
    target_reference: ScoreTargetReference | None,
    includes_target_level_rows: bool,
    payload: ReportPayload,
) -> PreparedScoreAnalysisReport:
    checked_format = _report_format(report_format)
    token = _package_token(
        context,
        report_scope=report_scope,
        target_reference=target_reference,
    )
    package = _package_path(context, token)
    leaves = _fixed_leaves(report_scope, checked_format)
    return PreparedScoreAnalysisReport(
        report_scope=report_scope,
        report_format=checked_format,
        package_token=token,
        package_path=package,
        output_paths=tuple(package / leaf for leaf in leaves),
        includes_target_level_rows=includes_target_level_rows,
        includes_history=False,
        includes_grade_or_proficiency_interpretation=False,
        payload=payload,
    )


def _activity_boundaries(
    analysis: ActivityScoreAnalysis,
) -> tuple[str, ...]:
    values = [REPORT_BOUNDARY_STATEMENT, CURRENT_HEAD_BOUNDARY_STATEMENT]
    if analysis.standard_analyses:
        values.append(STANDARDS_BOUNDARY_STATEMENT)
    return tuple(values)


def prepare_activity_analysis_report(
    context: ActivityReadContext,
    *,
    report_format: str,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedScoreAnalysisReport:
    """Prepare one aggregate Activity report without writing filesystem state."""
    analysis = activity_score_analysis_from_context(
        context,
        standards_library=standards_library,
    )
    metadata = ScoreAnalysisReportTechnicalMetadata(
        class_id=analysis.class_id,
        activity_id=analysis.activity_id,
        snapshot_revision=analysis.snapshot_revision,
        snapshot_sha256=analysis.snapshot_sha256,
        generated_at=workflow_timestamp(clock),
        report_scope=REPORT_SCOPE_ACTIVITY_ANALYSIS,
        score_basis=analysis.score_basis,
    )
    payload = ActivityAnalysisReport(
        metadata=metadata,
        activity_title=analysis.activity_title,
        current_score_count=analysis.current_score_count,
        target_kind_counts=analysis.target_kind_counts,
        represented_criterion_count=analysis.represented_criterion_count,
        represented_scoring_scale_count=(
            analysis.represented_scoring_scale_count
        ),
        criterion_analyses=analysis.criterion_analyses,
        standard_analyses=analysis.standard_analyses,
        boundary_statements=_activity_boundaries(analysis),
    )
    return _prepared(
        context,
        report_scope=REPORT_SCOPE_ACTIVITY_ANALYSIS,
        report_format=report_format,
        target_reference=None,
        includes_target_level_rows=False,
        payload=payload,
    )


def prepare_target_detail_report(
    context: ActivityReadContext,
    target_reference: ScoreTargetReference,
    *,
    report_format: str,
    target_label_resolver: TargetDisplayLabelResolver | None = None,
    clock: Clock | None = None,
) -> PreparedScoreAnalysisReport:
    """Prepare one exact teacher-local target report without writing files."""
    detail = target_score_detail_from_context(
        context,
        target_reference,
        target_label_resolver=target_label_resolver,
    )
    metadata = ScoreAnalysisReportTechnicalMetadata(
        class_id=detail.class_id,
        activity_id=detail.activity_id,
        snapshot_revision=detail.snapshot_revision,
        snapshot_sha256=detail.snapshot_sha256,
        generated_at=workflow_timestamp(clock),
        report_scope=REPORT_SCOPE_TARGET_DETAIL,
        score_basis=detail.score_basis,
        target_reference=target_reference,
    )
    boundaries = [
        REPORT_BOUNDARY_STATEMENT,
        CURRENT_HEAD_BOUNDARY_STATEMENT,
        TARGET_LOCAL_BOUNDARY_STATEMENT,
    ]
    if any(item.criterion_kind == "standard_backed" for item in detail.results):
        boundaries.append(STANDARDS_BOUNDARY_STATEMENT)
    payload = TargetDetailReport(
        metadata=metadata,
        activity_title=detail.activity_title,
        target_detail=detail,
        boundary_statements=tuple(boundaries),
    )
    return _prepared(
        context,
        report_scope=REPORT_SCOPE_TARGET_DETAIL,
        report_format=report_format,
        target_reference=target_reference,
        includes_target_level_rows=True,
        payload=payload,
    )


__all__ = [
    "CURRENT_HEAD_BOUNDARY_STATEMENT",
    "REPORT_BOUNDARY_STATEMENT",
    "REPORT_FORMATS",
    "REPORT_PACKAGE_DOMAIN",
    "REPORT_SCOPE_ACTIVITY_ANALYSIS",
    "REPORT_SCOPE_TARGET_DETAIL",
    "STANDARDS_BOUNDARY_STATEMENT",
    "TARGET_LOCAL_BOUNDARY_STATEMENT",
    "ActivityAnalysisReport",
    "PreparedScoreAnalysisReport",
    "ReportPayload",
    "ScoreAnalysisReportTechnicalMetadata",
    "TargetDetailReport",
    "prepare_activity_analysis_report",
    "prepare_target_detail_report",
]
