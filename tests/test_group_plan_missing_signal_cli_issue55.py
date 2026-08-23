from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_storage import write_grouping_signal
from pds_core.grouping_signals import (
    GroupingSignalDimension,
    GroupingSignalSet,
    GroupingSignalSource,
    GroupingSignalStudentBand,
)
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.cli import main
from concord.cli_app.parser import build_parser
from concord.workflows import show_group_plan


def _workspace(tmp_path: Path, name: str) -> Path:
    root = ensure_workspace_root(tmp_path / name)
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=datetime(2026, 8, 22, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            tuple(
                {
                    "student_id": f"student-{index}",
                    "last_name": f"Last-{index}",
                    "first_name": f"First-{index}",
                    "period": "1",
                }
                for index in range(1, 5)
            ),
        ),
    )
    assert main(
        [
            "activity", "create",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--title", "Missing Signal CLI",
            "--activity-type", "project",
            "--scoring-orientation", "evidence_only",
            "--session-id", "session-1",
            "--actor-id", "teacher-1",
        ]
    ) == 0

    signal = GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id="signal-55",
        class_id="class-1",
        created_at=datetime(2026, 8, 22, 19, 0, tzinfo=timezone.utc),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id="synthetic_module",
            snapshot_id="snapshot-55",
            snapshot_digest_algorithm="sha256",
            snapshot_digest="b" * 64,
        ),
        dimensions=(
            GroupingSignalDimension(
                dimension_id="collaboration-context",
                band_count=4,
            ),
        ),
        student_bands=(
            GroupingSignalStudentBand(
                student_id="student-1",
                dimension_id="collaboration-context",
                band=1,
            ),
            GroupingSignalStudentBand(
                student_id="student-2",
                dimension_id="collaboration-context",
                band=4,
            ),
        ),
    )
    write_grouping_signal(root, signal)
    assert main(
        [
            "group-plan", "create-similar-signal",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "signal-plan",
            "--expected-snapshot", "1",
            "--actor-id", "teacher-1",
            "--signal-set-id", "signal-55",
            "--dimension-id", "collaboration-context",
            "--target-group-count", "2",
        ]
    ) == 0
    return root


def _decision_args(root: Path, command: str, expected: int) -> list[str]:
    return [
        "group-plan", command,
        "--workspace-root", str(root),
        "--class-id", "class-1",
        "--activity-id", "activity-1",
        "--group-plan-id", "signal-plan",
        "--expected-snapshot", str(expected),
        "--actor-id", "teacher-1",
    ]


def test_leave_and_random_missing_cli_are_explicit_and_planning_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    leave_root = _workspace(tmp_path, "leave")
    capsys.readouterr()
    assert main(_decision_args(leave_root, "leave-missing-unassigned", 2)) == 0
    leave_output = capsys.readouterr().out
    assert "Missing-signal disposition: leave_unassigned" in leave_output
    assert "Missing-signal students: 2" in leave_output
    assert "Unresolved students: 2" in leave_output
    assert "Canonical Groups created: no" in leave_output
    assert "student-3" not in leave_output

    random_root = _workspace(tmp_path, "random")
    capsys.readouterr()
    assert main(
        _decision_args(random_root, "distribute-missing-random", 2)
        + ["--seed", "missing-seed"]
    ) == 0
    random_output = capsys.readouterr().out
    assert "Missing-signal disposition: random" in random_output
    assert "Random seed: missing-seed" in random_output
    assert "Assigned students: 4" in random_output
    assert "Unresolved students: 0" in random_output
    assert "Group sizes: 2,2" in random_output
    detail = show_group_plan(
        "class-1", "activity-1", "signal-plan", workspace_root=random_root
    )
    assert detail.plan.seed is None
    assert detail.plan.missing_signal_random_seed == "missing-seed"


@pytest.mark.parametrize(
    "command",
    (
        "confirm-missing-manual",
        "distribute-missing-random",
        "leave-missing-unassigned",
    ),
)
def test_missing_signal_cli_uses_frozen_plan_binding(command: str) -> None:
    parser = build_parser()
    args = [
        "group-plan", command,
        "--workspace-root", "workspace",
        "--class-id", "class-1",
        "--activity-id", "activity-1",
        "--group-plan-id", "signal-plan",
        "--expected-snapshot", "2",
        "--actor-id", "teacher-1",
    ]
    if command == "distribute-missing-random":
        args += ["--seed", "seed"]
    with pytest.raises(SystemExit):
        parser.parse_args(args + ["--signal-set-id", "other-signal"])


def test_random_missing_cli_requires_seed() -> None:
    parser = build_parser()
    common = [
        "--workspace-root", "workspace",
        "--class-id", "class-1",
        "--activity-id", "activity-1",
        "--group-plan-id", "signal-plan",
        "--expected-snapshot", "2",
        "--actor-id", "teacher-1",
    ]
    with pytest.raises(SystemExit):
        parser.parse_args(["group-plan", "distribute-missing-random", *common])
    parser.parse_args(["group-plan", "confirm-missing-manual", *common])
    parser.parse_args(["group-plan", "leave-missing-unassigned", *common])
