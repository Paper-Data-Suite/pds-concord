from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.cli import main
from concord.cli_app.parser import build_parser


def _workspace(tmp_path: Path, count: int = 6) -> Path:
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
                for index in range(1, count + 1)
            ),
        ),
    )
    assert main([
        "activity", "create", "--workspace-root", str(root),
        "--class-id", "class-1", "--activity-id", "activity-1",
        "--title", "Random Planning CLI", "--activity-type", "project",
        "--scoring-orientation", "evidence_only", "--session-id", "session-1",
        "--actor-id", "teacher-1",
    ]) == 0
    return root


def _random_base(root: Path, plan_id: str = "random-plan") -> list[str]:
    return [
        "group-plan", "create-random", "--workspace-root", str(root),
        "--class-id", "class-1", "--activity-id", "activity-1",
        "--group-plan-id", plan_id, "--expected-snapshot", "1",
        "--actor-id", "teacher-1", "--seed", "seed-52",
    ]


def test_create_random_count_cli_and_lifecycle_remain_planning_only(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    capsys.readouterr()
    assert main(_random_base(root) + ["--target-group-count", "2"]) == 0
    created = capsys.readouterr().out
    assert "Committed snapshot 2." in created
    assert "GroupPlan: random-plan" in created
    assert "Strategy: random" in created
    assert "Status: draft" in created
    assert "Target group count: 2" in created
    assert "Seed: seed-52" in created
    assert "Generated groups: 2" in created
    assert "Assigned students: 6" in created
    assert "Unresolved students: 0" in created
    assert "Group sizes: 3,3" in created
    assert "Canonical Groups created: no" in created
    assert "student-1" not in created

    common = [
        "--workspace-root", str(root), "--class-id", "class-1",
        "--activity-id", "activity-1", "--group-plan-id", "random-plan",
        "--actor-id", "teacher-1",
    ]
    assert main(["group-plan", "preview", *common, "--expected-snapshot", "2"]) == 0
    assert "Status: previewed" in capsys.readouterr().out
    assert main(["group-plan", "approve", *common, "--expected-snapshot", "3"]) == 0
    approved = capsys.readouterr().out
    assert "Status: approved" in approved
    assert "Canonical Groups created: no" in approved
    assert main([
        "group", "list", "--workspace-root", str(root), "--class-id", "class-1",
        "--activity-id", "activity-1",
    ]) == 0
    assert "No Groups found." in capsys.readouterr().out


def test_create_random_size_cli_preserves_size_target(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path, count=10)
    capsys.readouterr()
    assert main(_random_base(root) + ["--target-group-size", "4"]) == 0
    output = capsys.readouterr().out
    assert "Target group size: 4" in output
    assert "Generated groups: 3" in output
    assert "Group sizes: 4,3,3" in output


def test_create_random_parser_requires_exactly_one_target(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(_random_base(root))
    with pytest.raises(SystemExit):
        parser.parse_args(_random_base(root) + [
            "--target-group-size", "3", "--target-group-count", "2",
        ])


def test_create_random_invalid_count_is_nonmutating(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path, count=3)
    capsys.readouterr()
    assert main(_random_base(root) + ["--target-group-count", "4"]) == 1
    captured = capsys.readouterr()
    assert "must not exceed the current roster size" in captured.err
    assert main([
        "group-plan", "list", "--workspace-root", str(root),
        "--class-id", "class-1", "--activity-id", "activity-1",
    ]) == 0
    assert "No GroupPlans found." in capsys.readouterr().out
