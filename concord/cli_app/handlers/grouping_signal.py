"""Direct Core grouping-signal discovery, diagnostics, and import commands."""

from __future__ import annotations

import argparse
from datetime import datetime

from pds_core.grouping_signal_diagnostics import GroupingSignalDimensionDiagnostics
from pds_core.grouping_signals import GroupingSignalDimension

from concord.cli_app.common import workspace_arg
from concord.workflows import (
    ConcordWorkflowValidationError,
    GroupingSignalImportResult,
    GroupingSignalInspection,
    GroupingSignalSummary,
    ImportGroupingSignalCsvRequest,
    import_grouping_signal_csv,
    inspect_grouping_signal,
    list_grouping_signals,
)


def _source_label(item: GroupingSignalSummary) -> str:
    if item.source_module_id is None:
        return item.source_kind
    return f"{item.source_kind}:{item.source_module_id}"


def _finding_counts(inspection: GroupingSignalInspection) -> tuple[int, int]:
    errors = sum(
        1
        for finding in inspection.diagnostics.findings
        if finding.severity == "error"
    )
    warnings = sum(
        1
        for finding in inspection.diagnostics.findings
        if finding.severity == "warning"
    )
    return errors, warnings


def _print_summary(item: GroupingSignalSummary) -> None:
    dimensions = ",".join(item.dimension_ids)
    print(
        f"{item.signal_set_id}\tcreated={item.created_at.isoformat()}\t"
        f"source={_source_label(item)}\tdimensions={dimensions}\t"
        f"digest={item.digest}"
    )


def _print_source(inspection: GroupingSignalInspection) -> None:
    source = inspection.stored.signal.source
    print(f"Source kind: {source.kind}")
    if source.module_id is not None:
        print(f"Source module: {source.module_id}")
    if source.snapshot_id is not None:
        print(f"Source snapshot: {source.snapshot_id}")
    if source.snapshot_digest_algorithm is not None:
        print(
            "Source snapshot digest algorithm: "
            f"{source.snapshot_digest_algorithm}"
        )
    if source.snapshot_digest is not None:
        print(f"Source snapshot digest: {source.snapshot_digest}")


def _print_inspection(inspection: GroupingSignalInspection) -> None:
    signal = inspection.stored.signal
    errors, warnings = _finding_counts(inspection)
    print(f"Signal set: {signal.signal_set_id}")
    print(f"Class: {signal.class_id}")
    print(f"Created at: {signal.created_at.isoformat()}")
    print(f"Core digest algorithm: {inspection.stored.digest_algorithm}")
    print(f"Core signal digest: {inspection.stored.digest}")
    _print_source(inspection)
    print(f"Dimensions: {len(signal.dimensions)}")
    for dimension in signal.dimensions:
        print(
            f"Dimension: {dimension.dimension_id}\t"
            f"band_count={dimension.band_count}"
        )
    print(f"Diagnostic errors: {errors}")
    print(f"Diagnostic warnings: {warnings}")


def _selected_dimension(
    inspection: GroupingSignalInspection,
    dimension_id: str,
) -> tuple[GroupingSignalDimension, GroupingSignalDimensionDiagnostics]:
    dimension = next(
        (
            item
            for item in inspection.stored.signal.dimensions
            if item.dimension_id == dimension_id
        ),
        None,
    )
    if dimension is None:
        raise ConcordWorkflowValidationError(
            f"Grouping-signal dimension is not available: {dimension_id!r}."
        )
    diagnostics = next(
        item
        for item in inspection.diagnostics.dimensions
        if item.dimension_id == dimension_id
    )
    return dimension, diagnostics


def _print_problem_findings(
    inspection: GroupingSignalInspection,
    dimension_id: str,
) -> None:
    findings = tuple(
        finding
        for finding in inspection.diagnostics.findings
        if finding.dimension_id in {None, dimension_id}
    )
    for finding in findings:
        if finding.student_id is None:
            print(f"Finding: {finding.code}")
            continue
        if finding.code == "wrong_class_student":
            other_classes = ",".join(finding.other_class_ids)
            print(
                f"Wrong-class student ID: {finding.student_id}\t"
                f"other_classes={other_classes}"
            )
        elif finding.code == "unknown_student":
            print(f"Unknown student ID: {finding.student_id}")
        elif finding.code == "missing_student_signal":
            print(f"Missing student ID: {finding.student_id}")


def _parse_created_at(value: str | None) -> datetime | None:
    if value is None:
        return None
    if value != value.strip():
        raise ConcordWorkflowValidationError(
            "--new-created-at must not contain leading or trailing whitespace."
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ConcordWorkflowValidationError(
            "--new-created-at must be a valid ISO-8601 datetime."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ConcordWorkflowValidationError(
            "--new-created-at must be timezone-aware."
        )
    return parsed


def _print_import_result(result: GroupingSignalImportResult) -> None:
    preview = result.preview
    signal = result.stored.signal
    dimension = preview.diagnostics.dimensions[0]
    warnings = sum(
        1
        for finding in preview.diagnostics.findings
        if finding.severity == "warning"
    )
    print(f"Import disposition: {result.disposition}")
    print(f"Signal set: {signal.signal_set_id}")
    print(f"Class: {signal.class_id}")
    print(f"Core signal digest: {result.stored.digest}")
    print(f"Source kind: {signal.source.kind}")
    if signal.source.module_id is not None:
        print(f"Source module: {signal.source.module_id}")
    print(f"Dimension: {dimension.dimension_id}")
    print(f"Band count: {dimension.band_count}")
    print(f"Matched students: {dimension.matched_student_count}")
    print(f"Missing students: {dimension.missing_student_count}")
    print(f"Warnings: {warnings}")


def handle_list(args: argparse.Namespace) -> int:
    items = list_grouping_signals(
        args.class_id,
        workspace_root=workspace_arg(args),
    )
    if not items:
        print("No grouping signals found.")
        return 0
    for item in items:
        _print_summary(item)
    return 0


def handle_show(args: argparse.Namespace) -> int:
    inspection = inspect_grouping_signal(
        args.class_id,
        args.signal_set_id,
        workspace_root=workspace_arg(args),
    )
    _print_inspection(inspection)
    return 0


def handle_diagnose(args: argparse.Namespace) -> int:
    inspection = inspect_grouping_signal(
        args.class_id,
        args.signal_set_id,
        workspace_root=workspace_arg(args),
    )
    dimension, diagnostics = _selected_dimension(
        inspection,
        args.dimension_id,
    )
    print(f"Signal set: {inspection.summary.signal_set_id}")
    print(f"Core signal digest: {inspection.summary.digest}")
    print(f"Dimension: {dimension.dimension_id}")
    print(f"Band count: {dimension.band_count}")
    print(f"Roster students: {diagnostics.roster_student_count}")
    print(f"Signal entries: {diagnostics.signal_entry_count}")
    print(f"Matched students: {diagnostics.matched_student_count}")
    print(f"Missing students: {diagnostics.missing_student_count}")
    print(f"Wrong-class students: {diagnostics.wrong_class_student_count}")
    print(f"Unknown students: {diagnostics.unknown_student_count}")
    print("Band distribution:")
    for band, count in diagnostics.band_counts:
        print(f"  Band {band}: {count}")
    _print_problem_findings(inspection, dimension.dimension_id)
    return 0


def handle_import_csv(args: argparse.Namespace) -> int:
    result = import_grouping_signal_csv(
        ImportGroupingSignalCsvRequest(
            class_id=args.class_id,
            csv_path=args.csv_path,
            new_signal_set_id=args.new_signal_set_id,
            new_created_at=_parse_created_at(args.new_created_at),
        ),
        workspace_root=workspace_arg(args),
    )
    _print_import_result(result)
    return 0
