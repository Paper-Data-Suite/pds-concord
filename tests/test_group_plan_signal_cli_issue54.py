from __future__ import annotations

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
    write_grouping_signal,
)
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
from concord.workflows.group_plan import show_group_plan


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
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
                for index in range(1, 6)
            ),
        ),
    )
    assert (
        main(
            [
                "activity",
                "create",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--title",
                "Signal Planning CLI",
                "--activity-type",
                "project",
                "--scoring-orientation",
                "evidence_only",
                "--session-id",
                "session-1",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    return root


def _signal() -> GroupingSignalSet:
    return GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id="signal-54",
        class_id="class-1",
        created_at=datetime(2026, 8, 20, 19, 0, tzinfo=timezone.utc),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id="synthetic_module",
            snapshot_id="snapshot-54",
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
            GroupingSignalStudentBand(
                student_id="student-3",
                dimension_id="collaboration-context",
                band=2,
            ),
            GroupingSignalStudentBand(
                student_id="student-4",
                dimension_id="collaboration-context",
                band=3,
            ),
        ),
    )


def _base(root: Path, command: str, plan_id: str) -> list[str]:
    return [
        "group-plan",
        command,
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--group-plan-id",
        plan_id,
        "--expected-snapshot",
        "1",
        "--actor-id",
        "teacher-1",
        "--actor-label",
        "Synthetic Teacher",
        "--actor-role",
        "teacher",
        "--signal-set-id",
        "signal-54",
        "--dimension-id",
        "collaboration-context",
    ]


@pytest.mark.parametrize(
    ("command", "strategy", "plan_id"),
    (
        ("create-similar-signal", "similar_signal", "similar-plan"),
        ("create-mixed-signal", "mixed_signal", "mixed-plan"),
    ),
)
def test_signal_create_cli_is_explicit_bounded_and_planning_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    strategy: str,
    plan_id: str,
) -> None:
    root = _workspace(tmp_path)
    signal = _signal()
    write_grouping_signal(root, signal)
    digest = calculate_grouping_signal_digest(signal)
    capsys.readouterr()

    assert main(_base(root, command, plan_id) + ["--target-group-count", "3"]) == 0
    output = capsys.readouterr().out

    assert "Committed snapshot 2." in output
    assert f"GroupPlan: {plan_id}" in output
    assert f"Strategy: {strategy}" in output
    assert "Status: draft" in output
    assert "Target group count: 3" in output
    assert "Signal set: signal-54" in output
    assert f"Signal digest: {digest}" in output
    assert "Signal dimension: collaboration-context" in output
    assert "Generated groups: 3" in output
    assert "Assigned students: 4" in output
    assert "Unresolved students: 1" in output
    assert "Group sizes: 2,1,1" in output
    assert "Canonical Groups created: no" in output
    assert "student-1" not in output
    assert "student-5" not in output
    assert signal.source.snapshot_digest not in output

    detail = show_group_plan(
        "class-1",
        "activity-1",
        plan_id,
        workspace_root=root,
    )
    assert detail.plan.strategy == strategy
    assert detail.plan.status == "draft"
    assert detail.plan.seed is None
    assert detail.plan.source_signal_set_id == "signal-54"
    assert detail.plan.source_signal_set_digest == digest
    assert detail.plan.source_signal_dimension_id == "collaboration-context"
    assert detail.plan.unresolved_student_ids == ("student-5",)

    assert (
        main(
            [
                "group",
                "list",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
            ]
        )
        == 0
    )
    assert "No Groups found." in capsys.readouterr().out


def test_signal_cli_size_target_uses_full_roster_count(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    write_grouping_signal(root, _signal())
    capsys.readouterr()

    assert (
        main(
            _base(root, "create-similar-signal", "size-plan")
            + ["--target-group-size", "2"]
        )
        == 0
    )
    output = capsys.readouterr().out
    assert "Target group size: 2" in output
    assert "Generated groups: 3" in output
    assert "Assigned students: 4" in output
    assert "Unresolved students: 1" in output
    assert "Group sizes: 2,1,1" in output


@pytest.mark.parametrize(
    "command",
    ("create-similar-signal", "create-mixed-signal"),
)
def test_signal_cli_parser_requires_exactly_one_target_and_has_no_seed(
    tmp_path: Path,
    command: str,
) -> None:
    root = _workspace(tmp_path)
    parser = build_parser()
    base = _base(root, command, "parser-plan")

    with pytest.raises(SystemExit):
        parser.parse_args(base)
    with pytest.raises(SystemExit):
        parser.parse_args(
            base
            + [
                "--target-group-size",
                "2",
                "--target-group-count",
                "3",
            ]
        )
    with pytest.raises(SystemExit):
        parser.parse_args(base + ["--target-group-count", "3", "--seed", "no"])
