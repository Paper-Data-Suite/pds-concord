from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_storage import (
    calculate_grouping_signal_digest,
    grouping_signal_digest_path,
    write_grouping_signal,
)
from pds_core.grouping_signals import (
    GroupingSignalSet,
    grouping_signal_set_from_json,
)
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.workflows import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
    inspect_grouping_signal,
    list_grouping_signals,
    select_grouping_signal_dimension,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "core_grouping_signals" / "v1"


def _signal(name: str) -> GroupingSignalSet:
    return grouping_signal_set_from_json((FIXTURE_ROOT / name).read_bytes())


def _write_class(
    workspace: Path,
    class_id: str,
    students: tuple[tuple[str, str, str, str], ...],
) -> None:
    write_class_metadata_for_class(
        workspace,
        create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        workspace,
        create_roster(
            class_id,
            tuple(
                {
                    "student_id": student_id,
                    "last_name": last_name,
                    "first_name": first_name,
                    "period": period,
                }
                for student_id, last_name, first_name, period in students
            ),
        ),
    )


def _workspace(tmp_path: Path) -> Path:
    workspace = ensure_workspace_root(tmp_path / "workspace")
    _write_class(
        workspace,
        "english10_p2",
        (
            ("student_001", "Sample", "Ava", "2"),
            ("student_002", "Example", "Ben", "2"),
            ("student_003", "Demo", "Cora", "2"),
        ),
    )
    _write_class(
        workspace,
        "english10_p4",
        (("student_004", "Other", "Drew", "4"),),
    )
    return workspace


def _file_state(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_discovery_requires_exact_class_and_empty_collection_is_valid(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    assert list_grouping_signals("english10_p2", workspace_root=workspace) == ()

    with pytest.raises(ConcordWorkflowNotFoundError, match="Core class"):
        list_grouping_signals("missing_class", workspace_root=workspace)


def test_discovery_is_deterministic_and_preserves_core_identity(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    teacher = _signal("teacher_complete.json")
    module = _signal("module_multi_dimension.json")
    write_grouping_signal(workspace, teacher)
    write_grouping_signal(workspace, module)

    summaries = list_grouping_signals("english10_p2", workspace_root=workspace)
    assert tuple(item.signal_set_id for item in summaries) == (
        "module_multi_001",
        "teacher_complete_001",
    )
    module_summary, teacher_summary = summaries
    assert module_summary.source_kind == "module_generated"
    assert module_summary.source_module_id == "synthetic_module"
    assert module_summary.dimension_ids == (
        "reading_analysis",
        "writing_claim_evidence",
    )
    assert module_summary.digest == calculate_grouping_signal_digest(module)
    assert teacher_summary.source_kind == "teacher_authored"
    assert teacher_summary.source_module_id is None
    assert teacher_summary.dimension_ids == ("discussion_support",)
    assert teacher_summary.digest == calculate_grouping_signal_digest(teacher)


def test_inspection_preserves_core_diagnostics_without_mutation(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    signal = _signal("module_multi_dimension.json")
    write_grouping_signal(workspace, signal)
    before = _file_state(workspace)

    inspection = inspect_grouping_signal(
        "english10_p2",
        signal.signal_set_id,
        workspace_root=workspace,
    )

    assert _file_state(workspace) == before
    assert inspection.stored.signal == signal
    assert inspection.summary.digest == calculate_grouping_signal_digest(signal)
    assert inspection.summary.digest != signal.source.snapshot_digest
    assert inspection.diagnostics.has_errors is True
    assert inspection.diagnostics.has_warnings is True
    assert {finding.code for finding in inspection.diagnostics.findings} == {
        "wrong_class_student",
        "unknown_student",
        "missing_student_signal",
    }
    dimensions = {
        item.dimension_id: item for item in inspection.diagnostics.dimensions
    }
    reading = dimensions["reading_analysis"]
    assert reading.matched_student_count == 1
    assert reading.missing_student_count == 2
    assert reading.wrong_class_student_count == 1
    assert reading.unknown_student_count == 1
    assert reading.band_counts == ((1, 0), (2, 1), (3, 0), (4, 0))


def test_explicit_dimension_selection_accepts_clean_and_missing_only_signals(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    complete = _signal("teacher_complete.json")
    write_grouping_signal(workspace, complete)

    selected = select_grouping_signal_dimension(
        "english10_p2",
        complete.signal_set_id,
        "discussion_support",
        workspace_root=workspace,
    )
    assert selected.class_id == "english10_p2"
    assert selected.signal_set_id == "teacher_complete_001"
    assert selected.digest == calculate_grouping_signal_digest(complete)
    assert selected.dimension_id == "discussion_support"
    assert selected.dimension.band_count == 3
    assert selected.dimension_diagnostics.missing_student_count == 0

    partial = replace(
        complete,
        signal_set_id="teacher_partial_001",
        student_bands=complete.student_bands[:-1],
    )
    write_grouping_signal(workspace, partial)
    partial_selection = select_grouping_signal_dimension(
        "english10_p2",
        partial.signal_set_id,
        "discussion_support",
        workspace_root=workspace,
    )
    assert partial_selection.inspection.diagnostics.has_errors is False
    assert partial_selection.inspection.diagnostics.has_warnings is True
    assert partial_selection.dimension_diagnostics.missing_student_count == 1
    missing = tuple(
        finding.student_id
        for finding in partial_selection.inspection.diagnostics.findings
        if finding.code == "missing_student_signal"
    )
    assert missing == ("student_003",)


def test_selection_rejects_invalid_dimension_and_core_diagnostic_errors(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    complete = _signal("teacher_complete.json")
    module = _signal("module_multi_dimension.json")
    write_grouping_signal(workspace, complete)
    write_grouping_signal(workspace, module)

    with pytest.raises(ConcordWorkflowValidationError, match="not available"):
        select_grouping_signal_dimension(
            "english10_p2",
            complete.signal_set_id,
            "missing_dimension",
            workspace_root=workspace,
        )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="wrong_class_student.*unknown_student|unknown_student.*wrong_class_student",
    ):
        select_grouping_signal_dimension(
            "english10_p2",
            module.signal_set_id,
            "reading_analysis",
            workspace_root=workspace,
        )


def test_exact_signal_lookup_does_not_fall_back_across_classes(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    signal = _signal("teacher_complete.json")
    write_grouping_signal(workspace, signal)

    with pytest.raises(ConcordWorkflowNotFoundError, match="not available"):
        inspect_grouping_signal(
            "english10_p4",
            signal.signal_set_id,
            workspace_root=workspace,
        )


def test_read_workflows_fail_closed_on_core_storage_integrity(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    signal = _signal("teacher_complete.json")
    write_grouping_signal(workspace, signal)
    grouping_signal_digest_path(
        workspace,
        signal.class_id,
        signal.signal_set_id,
    ).write_text("0" * 64 + "\n", encoding="ascii", newline="\n")

    with pytest.raises(ConcordWorkflowValidationError, match="integrity"):
        list_grouping_signals(signal.class_id, workspace_root=workspace)
