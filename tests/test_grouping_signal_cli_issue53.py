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
from pds_core.grouping_signal_csv import grouping_signal_set_to_csv_bytes
from pds_core.grouping_signal_storage import (
    calculate_grouping_signal_digest,
    list_grouping_signal_ids,
    write_grouping_signal,
)
from pds_core.grouping_signals import (
    GroupingSignalSet,
    GroupingSignalStudentBand,
    grouping_signal_set_from_json,
)
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.cli import main
from concord.cli_app.parser import build_parser

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "core_grouping_signals" / "v1"


def _fixture(name: str) -> bytes:
    return (FIXTURE_ROOT / name).read_bytes()


def _signal(name: str) -> GroupingSignalSet:
    return grouping_signal_set_from_json(_fixture(name))


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


def _base(root: Path, action: str) -> list[str]:
    return [
        "grouping-signal",
        action,
        "--workspace-root",
        str(root),
        "--class-id",
        "english10_p2",
    ]


def _clean_multidimension_signal() -> GroupingSignalSet:
    source = _signal("module_multi_dimension.json")
    return replace(
        source,
        signal_set_id="module_clean_001",
        student_bands=(
            GroupingSignalStudentBand(
                student_id="student_001",
                dimension_id="reading_analysis",
                band=2,
            ),
            GroupingSignalStudentBand(
                student_id="student_002",
                dimension_id="reading_analysis",
                band=4,
            ),
            GroupingSignalStudentBand(
                student_id="student_003",
                dimension_id="reading_analysis",
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student_001",
                dimension_id="writing_claim_evidence",
                band=3,
            ),
            GroupingSignalStudentBand(
                student_id="student_002",
                dimension_id="writing_claim_evidence",
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student_003",
                dimension_id="writing_claim_evidence",
                band=2,
            ),
        ),
    )


def test_grouping_signal_parser_exposes_bounded_command_family() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "grouping-signal",
            "diagnose",
            "--class-id",
            "english10_p2",
            "--signal-set-id",
            "signal-1",
            "--dimension-id",
            "dimension-1",
        ]
    )
    assert args.grouping_signal_command == "diagnose"
    assert args.class_id == "english10_p2"
    assert args.signal_set_id == "signal-1"
    assert args.dimension_id == "dimension-1"


@pytest.mark.parametrize(
    ("action", "extra"),
    (
        ("list", ()),
        ("show", ("--signal-set-id", "signal-1")),
        (
            "diagnose",
            ("--signal-set-id", "signal-1", "--dimension-id", "dimension-1"),
        ),
        ("import-csv", ("--csv-path", "signal.csv")),
    ),
)
def test_grouping_signal_actions_require_class_id(
    action: str,
    extra: tuple[str, ...],
) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["grouping-signal", action, *extra])


def test_list_is_deterministic_and_does_not_dump_student_bands(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    teacher = _signal("teacher_complete.json")
    module = _signal("module_multi_dimension.json")
    write_grouping_signal(workspace, teacher)
    write_grouping_signal(workspace, module)

    assert main(_base(workspace, "list")) == 0
    output = capsys.readouterr().out
    lines = output.splitlines()
    assert lines[0].startswith("module_multi_001\t")
    assert lines[1].startswith("teacher_complete_001\t")
    assert "source=module_generated:synthetic_module" in output
    assert "discussion_support" in output
    assert "reading_analysis,writing_claim_evidence" in output
    assert calculate_grouping_signal_digest(teacher) in output
    assert "student_001" not in output
    assert "\tband=" not in output


def test_show_distinguishes_core_digest_from_source_digest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    signal = _signal("module_multi_dimension.json")
    write_grouping_signal(workspace, signal)

    assert main(
        [
            *_base(workspace, "show"),
            "--signal-set-id",
            signal.signal_set_id,
        ]
    ) == 0
    output = capsys.readouterr().out
    core_digest = calculate_grouping_signal_digest(signal)
    assert f"Core signal digest: {core_digest}" in output
    assert f"Source snapshot digest: {'b' * 64}" in output
    assert core_digest != signal.source.snapshot_digest
    assert "Dimension: reading_analysis\tband_count=4" in output
    assert "Dimension: writing_claim_evidence\tband_count=3" in output
    assert "Diagnostic errors: 2" in output
    assert "Diagnostic warnings: 3" in output
    assert "student_001" not in output


def test_diagnose_shows_problem_ids_but_not_matched_band_assignments(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    signal = _signal("module_multi_dimension.json")
    write_grouping_signal(workspace, signal)

    assert main(
        [
            *_base(workspace, "diagnose"),
            "--signal-set-id",
            signal.signal_set_id,
            "--dimension-id",
            "reading_analysis",
        ]
    ) == 0
    output = capsys.readouterr().out
    assert "Matched students: 1" in output
    assert "Missing students: 2" in output
    assert "Wrong-class students: 1" in output
    assert "Unknown students: 1" in output
    assert "Band 1: 0" in output
    assert "Band 2: 1" in output
    assert "Missing student ID: student_002" in output
    assert "Missing student ID: student_003" in output
    assert "Wrong-class student ID: student_004" in output
    assert "other_classes=english10_p4" in output
    assert "Unknown student ID: student_999" in output
    assert "student_001" not in output


def test_diagnose_invalid_dimension_returns_workflow_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    signal = _signal("teacher_complete.json")
    write_grouping_signal(workspace, signal)

    assert main(
        [
            *_base(workspace, "diagnose"),
            "--signal-set-id",
            signal.signal_set_id,
            "--dimension-id",
            "missing_dimension",
        ]
    ) == 1
    captured = capsys.readouterr()
    assert "Grouping-signal dimension is not available" in captured.err


def test_import_complete_signal_cli_is_class_level_and_idempotent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    csv_path = tmp_path / "teacher.csv"
    csv_path.write_bytes(_fixture("teacher_complete.csv"))
    args = [
        *_base(workspace, "import-csv"),
        "--csv-path",
        str(csv_path),
    ]

    assert main(args) == 0
    first = capsys.readouterr().out
    assert "Import disposition: created" in first
    assert "Signal set: teacher_complete_001" in first
    assert "Class: english10_p2" in first
    assert "Dimension: discussion_support" in first
    assert "Matched students: 3" in first
    assert "Missing students: 0" in first
    assert "Warnings: 0" in first
    assert "student_001" not in first

    assert main(args) == 0
    second = capsys.readouterr().out
    assert "Import disposition: existing" in second
    assert list_grouping_signal_ids(workspace, "english10_p2") == (
        "teacher_complete_001",
    )


def test_import_partial_signal_reports_warning_count_without_roster_dump(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    partial = _fixture("teacher_complete.csv").replace(
        b"signal_set_id=teacher_complete_001",
        b"signal_set_id=teacher_partial_cli_001",
    )
    partial = partial.replace(b"student_003,2\n", b"")
    csv_path = tmp_path / "partial.csv"
    csv_path.write_bytes(partial)

    assert main(
        [
            *_base(workspace, "import-csv"),
            "--csv-path",
            str(csv_path),
        ]
    ) == 0
    output = capsys.readouterr().out
    assert "Missing students: 1" in output
    assert "Warnings: 1" in output
    assert "student_003" not in output


def test_projection_cli_requires_explicit_identity_and_aware_time(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    source = _clean_multidimension_signal()
    csv_path = tmp_path / "projection.csv"
    csv_path.write_bytes(
        grouping_signal_set_to_csv_bytes(source, "reading_analysis")
    )

    base = [
        *_base(workspace, "import-csv"),
        "--csv-path",
        str(csv_path),
    ]
    assert main(base) == 1
    assert "requires both" in capsys.readouterr().err

    assert main(
        [
            *base,
            "--new-signal-set-id",
            "projection_cli_001",
            "--new-created-at",
            "2026-08-20T21:30:00",
        ]
    ) == 1
    assert "must be timezone-aware" in capsys.readouterr().err

    assert main(
        [
            *base,
            "--new-signal-set-id",
            "projection_cli_001",
            "--new-created-at",
            "2026-08-20T21:30:00+00:00",
        ]
    ) == 0
    output = capsys.readouterr().out
    assert "Import disposition: created" in output
    assert "Signal set: projection_cli_001" in output
    assert "Source module: synthetic_module" in output
    assert "Dimension: reading_analysis" in output


def test_import_wrong_class_is_nonmutating_cli_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    workspace = _workspace(tmp_path)
    csv_path = tmp_path / "teacher.csv"
    csv_path.write_bytes(_fixture("teacher_complete.csv"))

    assert main(
        [
            "grouping-signal",
            "import-csv",
            "--workspace-root",
            str(workspace),
            "--class-id",
            "english10_p4",
            "--csv-path",
            str(csv_path),
        ]
    ) == 1
    captured = capsys.readouterr()
    assert "class_mismatch" in captured.err
    assert list_grouping_signal_ids(workspace, "english10_p2") == ()
    assert list_grouping_signal_ids(workspace, "english10_p4") == ()
