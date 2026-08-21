"""Teacher-facing Core grouping-signal discovery, diagnostics, and import."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from concord.menu_context import CancelMenuAction
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    confirm_write,
    prompt_text,
    select_one,
    show_result,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.workflows import (
    ActivitySummary,
    GroupingSignalImportPreview,
    GroupingSignalInspection,
    GroupingSignalSummary,
    ImportGroupingSignalCsvRequest,
    import_grouping_signal_csv,
    inspect_grouping_signal,
    inspect_grouping_signal_csv_file,
    list_grouping_signals,
    prepare_grouping_signal_csv_import,
)


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


def _source_lines(inspection: GroupingSignalInspection) -> tuple[str, ...]:
    source = inspection.stored.signal.source
    lines = [f"Source kind: {source.kind}"]
    if source.module_id is not None:
        lines.append(f"Source module: {source.module_id}")
    if source.snapshot_id is not None:
        lines.append(f"Source snapshot: {source.snapshot_id}")
    if source.snapshot_digest_algorithm is not None:
        lines.append(
            "Source snapshot digest algorithm: "
            f"{source.snapshot_digest_algorithm}"
        )
    if source.snapshot_digest is not None:
        lines.append(f"Source snapshot digest: {source.snapshot_digest}")
    return tuple(lines)


def _import_source_lines(preview: GroupingSignalImportPreview) -> tuple[str, ...]:
    source = preview.signal.source
    lines = [f"Source kind: {source.kind}"]
    if source.module_id is not None:
        lines.append(f"Source module: {source.module_id}")
    if source.snapshot_id is not None:
        lines.append(f"Source snapshot: {source.snapshot_id}")
    if source.snapshot_digest_algorithm is not None:
        lines.append(
            "Source snapshot digest algorithm: "
            f"{source.snapshot_digest_algorithm}"
        )
    if source.snapshot_digest is not None:
        lines.append(f"Source snapshot digest: {source.snapshot_digest}")
    return tuple(lines)


def _problem_ids(
    inspection: GroupingSignalInspection,
    dimension_id: str,
) -> tuple[str, ...]:
    lines: list[str] = []
    for finding in inspection.diagnostics.findings:
        if finding.dimension_id not in {None, dimension_id}:
            continue
        if finding.student_id is None:
            lines.append(f"Finding: {finding.code}")
        elif finding.code == "missing_student_signal":
            lines.append(f"Missing student ID: {finding.student_id}")
        elif finding.code == "unknown_student":
            lines.append(f"Unknown student ID: {finding.student_id}")
        elif finding.code == "wrong_class_student":
            other_classes = ",".join(finding.other_class_ids)
            lines.append(
                f"Wrong-class student ID: {finding.student_id}; "
                f"other classes: {other_classes}"
            )
    return tuple(lines)


def _missing_import_ids(
    preview: GroupingSignalImportPreview,
) -> tuple[str, ...]:
    dimension_id = preview.dimension.dimension_id
    return tuple(
        finding.student_id
        for finding in preview.diagnostics.findings
        if finding.code == "missing_student_signal"
        and finding.dimension_id == dimension_id
        and finding.student_id is not None
    )


def _select_signal(class_id: str) -> GroupingSignalSummary:
    summaries = list_grouping_signals(class_id)
    return select_one(
        "Choose a Grouping Signal",
        summaries,
        tuple(
            (
                f"{item.signal_set_id} - {item.source_kind}; "
                f"dimensions: {len(item.dimension_ids)}"
            )
            for item in summaries
        ),
        help_text=(
            "Choose one exact immutable Core signal snapshot. Concord does not "
            "select a latest, current, or newest signal automatically."
        ),
    )


def _show_signal_inspection(inspection: GroupingSignalInspection) -> None:
    signal = inspection.stored.signal
    errors, warnings = _finding_counts(inspection)
    clear_screen()
    print_menu_header("Grouping Signal")
    print(f"Signal set: {signal.signal_set_id}")
    print(f"Class: {signal.class_id}")
    print(f"Created at: {signal.created_at.isoformat()}")
    print(f"Core signal digest: {inspection.stored.digest}")
    for line in _source_lines(inspection):
        print(line)
    print()
    print("Dimensions:")
    for dimension in signal.dimensions:
        print(f"- {dimension.dimension_id}; bands: {dimension.band_count}")
    print()
    print(f"Diagnostic errors: {errors}")
    print(f"Diagnostic warnings: {warnings}")
    print()
    pause_for_user()


def _show_dimension_diagnostics(
    inspection: GroupingSignalInspection,
    dimension_id: str,
) -> None:
    diagnostics = next(
        item
        for item in inspection.diagnostics.dimensions
        if item.dimension_id == dimension_id
    )
    clear_screen()
    print_menu_header("Grouping Signal Diagnostics")
    print(f"Signal set: {inspection.summary.signal_set_id}")
    print(f"Core signal digest: {inspection.summary.digest}")
    print(f"Dimension: {diagnostics.dimension_id}")
    print(f"Band count: {diagnostics.band_count}")
    print(f"Roster students: {diagnostics.roster_student_count}")
    print(f"Signal entries: {diagnostics.signal_entry_count}")
    print(f"Matched students: {diagnostics.matched_student_count}")
    print(f"Missing students: {diagnostics.missing_student_count}")
    print(f"Wrong-class students: {diagnostics.wrong_class_student_count}")
    print(f"Unknown students: {diagnostics.unknown_student_count}")
    print()
    print("Band distribution:")
    for band, count in diagnostics.band_counts:
        print(f"Band {band}: {count}")
    problems = _problem_ids(inspection, dimension_id)
    if problems:
        print()
        for line in problems:
            print(line)
    print()
    print("Missing signal coverage is not a lowest-band value.")
    print()
    pause_for_user()


def _list_signals(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Grouping Signals")
    summaries = list_grouping_signals(activity.class_id)
    if not summaries:
        print("No grouping signals are available for this class.")
    else:
        for item in summaries:
            module = (
                f"; module: {item.source_module_id}"
                if item.source_module_id is not None
                else ""
            )
            print(
                f"{item.signal_set_id} - {item.source_kind}{module}; "
                f"dimensions: {','.join(item.dimension_ids)}"
            )
            print(f"  Core digest: {item.digest}")
    print()
    pause_for_user()


def _inspect_signal(activity: ActivitySummary) -> None:
    selected = _select_signal(activity.class_id)
    inspection = inspect_grouping_signal(
        activity.class_id,
        selected.signal_set_id,
    )
    _show_signal_inspection(inspection)
    dimension = select_one(
        "Choose a Signal Dimension",
        inspection.stored.signal.dimensions,
        tuple(
            f"{item.dimension_id} - bands: {item.band_count}"
            for item in inspection.stored.signal.dimensions
        ),
        help_text=(
            "Choose the exact dimension to diagnose. Concord never combines "
            "dimensions or selects the first dimension automatically."
        ),
    )
    _show_dimension_diagnostics(inspection, dimension.dimension_id)


def _parse_created_at(value: str) -> datetime:
    if value != value.strip():
        raise ValueError(
            "New created_at must not contain leading or trailing whitespace."
        )
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError(
            "New created_at must be a valid ISO-8601 datetime."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("New created_at must be timezone-aware.")
    return parsed


def _import_preview_lines(
    preview: GroupingSignalImportPreview,
) -> tuple[str, ...]:
    dimension = preview.diagnostics.dimensions[0]
    warnings = sum(
        1
        for finding in preview.diagnostics.findings
        if finding.severity == "warning"
    )
    lines = [
        f"Class: {preview.signal.class_id}",
        f"Representation: {preview.representation_scope}",
        f"Signal set: {preview.signal.signal_set_id}",
        f"Core signal digest: {preview.digest}",
        *_import_source_lines(preview),
        f"Dimension: {dimension.dimension_id}",
        f"Band count: {dimension.band_count}",
        f"Matched students: {dimension.matched_student_count}",
        f"Missing students: {dimension.missing_student_count}",
        f"Warnings: {warnings}",
    ]
    missing_ids = _missing_import_ids(preview)
    if missing_ids:
        lines.append(f"Missing student IDs: {','.join(missing_ids)}")
        lines.append("Missing coverage is not a lowest-band value.")
    lines.extend(
        (
            "Import writes only the immutable Core grouping-signal exchange.",
            "No GroupPlan, Group, or GroupMembership will be created.",
        )
    )
    return tuple(lines)


def _import_csv(activity: ActivitySummary) -> None:
    raw_path = prompt_text(
        "Import Grouping Signal",
        "CSV path",
        help_text=(
            "Choose an explicit Core grouping_signal_csv_v1 file. "
            "The source file is never modified."
        ),
    )
    assert raw_path is not None

    source = inspect_grouping_signal_csv_file(raw_path)
    new_signal_set_id: str | None = None
    new_created_at: datetime | None = None
    if source.requires_new_identity:
        new_signal_set_id = prompt_text(
            "Import Signal Projection",
            "New signal set ID",
            help_text=(
                "A dimension projection cannot reuse the source multi-dimension "
                "signal identity."
            ),
        )
        assert new_signal_set_id is not None
        raw_created_at = prompt_text(
            "Import Signal Projection",
            "New created_at",
            help_text=(
                "Enter an explicit timezone-aware ISO-8601 timestamp for the "
                "new immutable projection identity."
            ),
        )
        assert raw_created_at is not None
        new_created_at = _parse_created_at(raw_created_at)

    request = ImportGroupingSignalCsvRequest(
        class_id=activity.class_id,
        csv_path=raw_path,
        new_signal_set_id=new_signal_set_id,
        new_created_at=new_created_at,
    )
    preview = prepare_grouping_signal_csv_import(request)
    if not confirm_write(
        "Import Grouping Signal",
        "IMPORT",
        _import_preview_lines(preview),
    ):
        return

    result = import_grouping_signal_csv(
        replace(
            request,
            expected_signal_digest=preview.digest,
        )
    )
    dimension = result.preview.diagnostics.dimensions[0]
    show_result(
        "Grouping Signal Import Result",
        (
            f"Import disposition: {result.disposition}",
            f"Signal set: {result.stored.signal.signal_set_id}",
            f"Class: {result.stored.signal.class_id}",
            f"Core signal digest: {result.stored.digest}",
            f"Dimension: {dimension.dimension_id}",
            f"Matched students: {dimension.matched_student_count}",
            f"Missing students: {dimension.missing_student_count}",
            "No GroupPlan or canonical Group state was created.",
        ),
    )


def launch_grouping_signal_menu(activity: ActivitySummary) -> None:
    """Inspect and import Core grouping signals for one Activity's exact class."""

    while True:
        clear_screen()
        print_menu_header("Grouping Signals")
        print(f"Activity: {activity.title}")
        print(f"Class: {activity.class_id}")
        print()
        print("1. List signals")
        print("2. Inspect / diagnose a signal")
        print("3. Import grouping-signal CSV")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Grouping Signals Help")
            print(
                "Grouping signals are immutable Core planning inputs. "
                "Concord does not choose a latest signal or dimension."
            )
            print(
                "This menu does not create GroupPlans or canonical Groups. "
                "Signal-backed planning begins in issue #54."
            )
            print()
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            return
        else:
            try:
                if choice == "1":
                    _list_signals(activity)
                elif choice == "2":
                    _inspect_signal(activity)
                elif choice == "3":
                    _import_csv(activity)
                else:
                    print(navigation_hint_with_help())
                    pause_for_user()
            except CancelMenuAction:
                continue
            except Exception as error:
                show_result("Grouping Signal Error", (str(error),))
