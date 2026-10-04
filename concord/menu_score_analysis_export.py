"""Interactive deliberate export for Concord Activity Score analysis."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    parse_menu_navigation,
)
from concord.menu_prompts import select_one, show_result
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import ScoreTargetReference
from concord.workflows import (
    ActivityAnalysisReport,
    ActivityScoreAnalysis,
    InstalledScoreAnalysisReport,
    PreparedScoreAnalysisReport,
    ScoreAnalysisReportOutputError,
    TargetDetailReport,
    execute_prepared_score_analysis_report,
    prepare_activity_analysis_report,
    prepare_target_detail_report,
)
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.activity_score_analysis import TargetDisplayLabelResolver

GENERATE_CONFIRMATION_TOKEN = "GENERATE"
TargetLabeler = Callable[[ScoreTargetReference], str]

_SCOPE_ACTIVITY = "activity_analysis"
_SCOPE_TARGET = "target_detail"


def _choose_scope() -> str:
    return select_one(
        "Export Score Analysis",
        (_SCOPE_ACTIVITY, _SCOPE_TARGET),
        ("Activity Analysis Report", "Target Detail Report"),
        help_text=(
            "Activity Analysis is aggregate and privacy-minimized. "
            "Target Detail contains current Score rows for one exact target "
            "and remains teacher-local."
        ),
    )


def _choose_format() -> str:
    return select_one(
        "Choose Report Format",
        ("pdf", "csv", "json"),
        (
            "PDF - readable local report",
            "CSV - deterministic spreadsheet/data files",
            "JSON - complete selected local analysis scope",
        ),
        help_text=(
            "All formats represent the same prepared descriptive analysis. "
            "None is a Grade report or Core publication."
        ),
    )


def _choose_target(
    analysis: ActivityScoreAnalysis,
    target_labeler: TargetLabeler,
) -> ScoreTargetReference:
    targets = tuple(
        dict.fromkeys(item.target_reference for item in analysis.current_scores)
    )
    if not targets:
        raise ScoreAnalysisReportOutputError(
            "No current Score targets are available for Target Detail export."
        )
    labels = tuple(
        f"{item.target_kind}: {target_labeler(item)}"
        for item in targets
    )
    return select_one(
        "Choose Target Detail",
        targets,
        labels,
        help_text=(
            "Choose one exact current Score target. Target kinds remain "
            "distinct; Concord does not reinterpret Group or Artifact Scores "
            "as student Scores."
        ),
    )


def _prepare_report(
    context: ActivityReadContext,
    analysis: ActivityScoreAnalysis,
    *,
    report_scope: str,
    report_format: str,
    target_labeler: TargetLabeler,
    target_label_resolver: TargetDisplayLabelResolver | None,
    standards_library: StandardsLibrary | None,
) -> PreparedScoreAnalysisReport:
    if report_scope == _SCOPE_ACTIVITY:
        return prepare_activity_analysis_report(
            context,
            report_format=report_format,
            standards_library=standards_library,
        )
    if report_scope == _SCOPE_TARGET:
        target = _choose_target(analysis, target_labeler)
        return prepare_target_detail_report(
            context,
            target,
            report_format=report_format,
            target_label_resolver=target_label_resolver,
        )
    raise ScoreAnalysisReportOutputError(
        f"Unsupported report scope: {report_scope}"
    )


def _scope_label(prepared: PreparedScoreAnalysisReport) -> str:
    if prepared.report_scope == _SCOPE_ACTIVITY:
        return "Activity Analysis"
    if prepared.report_scope == _SCOPE_TARGET:
        return "Target Detail"
    return prepared.report_scope


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _report_count(prepared: PreparedScoreAnalysisReport) -> int:
    payload = prepared.payload
    if isinstance(payload, ActivityAnalysisReport):
        return payload.current_score_count
    if isinstance(payload, TargetDetailReport):
        return payload.target_detail.current_score_count
    raise ScoreAnalysisReportOutputError(
        "Prepared report payload is unsupported."
    )


def _report_subject_lines(
    prepared: PreparedScoreAnalysisReport,
) -> tuple[str, ...]:
    payload = prepared.payload
    if isinstance(payload, ActivityAnalysisReport):
        return ()
    if isinstance(payload, TargetDetailReport):
        return (
            f"Target: {payload.target_detail.target_label}",
            f"Target kind: {payload.target_detail.target_reference.target_kind}",
        )
    raise ScoreAnalysisReportOutputError(
        "Prepared report payload is unsupported."
    )


def _display_destination(path: Path) -> str:
    return path.as_posix()


def format_score_report_preview(
    prepared: PreparedScoreAnalysisReport,
) -> tuple[str, ...]:
    """Return exact teacher-facing scope/destination preview lines."""
    payload = prepared.payload
    metadata = payload.metadata
    lines = [
        f"Class: {metadata.class_id}",
        f"Activity: {payload.activity_title}",
        f"Scope: {_scope_label(prepared)}",
    ]
    lines.extend(_report_subject_lines(prepared))
    lines.extend(
        (
            f"Score basis: {metadata.score_basis}",
            f"Current Score records represented: {_report_count(prepared)}",
            (
                "Includes target-level rows: "
                f"{_yes_no(prepared.includes_target_level_rows)}"
            ),
            f"Includes Score history: {_yes_no(prepared.includes_history)}",
            (
                "Includes Grade/proficiency interpretation: "
                f"{_yes_no(prepared.includes_grade_or_proficiency_interpretation)}"
            ),
            f"Format: {prepared.report_format.upper()}",
            "",
            "Destination:",
            _display_destination(prepared.package_path),
            "",
            "Output files:",
        )
    )
    lines.extend(f"- {path.name}" for path in prepared.output_paths)
    lines.extend(
        (
            "",
            "Existing identical output may be reused.",
            "Conflicting existing output is never silently overwritten.",
            "This remains a local teacher-controlled output.",
        )
    )
    return tuple(lines)


def _confirm_generate(
    prepared: PreparedScoreAnalysisReport,
) -> bool:
    while True:
        clear_screen()
        print_menu_header("Generate Concord Score Analysis")
        for line in format_score_report_preview(prepared):
            print(line)
        print()
        print(
            f"Type {GENERATE_CONFIRMATION_TOKEN} to create the local report, "
            "or press Enter to cancel."
        )
        print_navigation()
        print()
        raw = input("Confirmation: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Generate Concord Score Analysis Help")
            print(
                "This confirmation creates only the bounded local report "
                "shown in the preview."
            )
            print(
                "It does not change Scores, publish an Academic Result "
                "Manifest, or create a Core Publication Record."
            )
            print(
                f"Type the exact token {GENERATE_CONFIRMATION_TOKEN} only "
                "when the displayed scope and destination are correct."
            )
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or not raw:
            return False
        return raw == GENERATE_CONFIRMATION_TOKEN


def _installed_summary(
    installed: InstalledScoreAnalysisReport,
) -> tuple[str, ...]:
    lines = [
        "Local teacher-controlled report output is ready.",
        f"Report package: {installed.package_path.as_posix()}",
    ]
    if installed.created_output_paths:
        lines.append("")
        lines.append("Created files:")
        lines.extend(
            f"- {path.name}" for path in installed.created_output_paths
        )
    if installed.reused_output_paths:
        lines.append("")
        lines.append("Reused verified existing files:")
        lines.extend(
            f"- {path.name}" for path in installed.reused_output_paths
        )
    lines.extend(
        (
            "",
            "No report was sent, shared, published, or filed by this action.",
        )
    )
    return tuple(lines)


def launch_score_report_export(
    context: ActivityReadContext,
    analysis: ActivityScoreAnalysis,
    *,
    target_labeler: TargetLabeler,
    target_label_resolver: TargetDisplayLabelResolver | None,
    standards_library: StandardsLibrary | None,
) -> InstalledScoreAnalysisReport | None:
    """Prepare, preview, explicitly confirm, and write one local report."""
    try:
        scope = _choose_scope()
        report_format = _choose_format()
        prepared = _prepare_report(
            context,
            analysis,
            report_scope=scope,
            report_format=report_format,
            target_labeler=target_labeler,
            target_label_resolver=target_label_resolver,
            standards_library=standards_library,
        )
        if not _confirm_generate(prepared):
            show_result(
                "Score Analysis Export Cancelled",
                ("No report files were created by this export attempt.",),
            )
            return None
        installed = execute_prepared_score_analysis_report(prepared)
    except ScoreAnalysisReportOutputError as error:
        show_result(
            "Score Analysis Export Error",
            (str(error),),
        )
        return None

    show_result(
        "Score Analysis Report Ready",
        _installed_summary(installed),
    )
    return installed


__all__ = [
    "GENERATE_CONFIRMATION_TOKEN",
    "TargetLabeler",
    "format_score_report_preview",
    "launch_score_report_export",
]
