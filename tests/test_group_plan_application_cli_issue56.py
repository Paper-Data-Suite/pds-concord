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
from concord.workflows import list_groups, list_memberships, show_group_plan


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
                {
                    "student_id": "student-2",
                    "last_name": "Two",
                    "first_name": "Blair",
                    "period": "1",
                },
            ),
        ),
    )
    assert main(
        [
            "activity", "create",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--title", "Application CLI",
            "--activity-type", "project",
            "--scoring-orientation", "evidence_only",
            "--session-id", "session-1",
            "--actor-id", "teacher-1",
        ]
    ) == 0
    assert main(
        [
            "group-plan", "create-manual",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--expected-snapshot", "1",
            "--actor-id", "teacher-1",
        ]
    ) == 0
    assert main(
        [
            "group-plan", "add-group",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--planned-group-key", "group-a",
            "--label", "Group A",
            "--expected-snapshot", "2",
            "--actor-id", "teacher-1",
        ]
    ) == 0
    for snapshot, student_id in ((3, "student-1"), (4, "student-2")):
        assert main(
            [
                "group-plan", "place-student",
                "--workspace-root", str(root),
                "--class-id", "class-1",
                "--activity-id", "activity-1",
                "--group-plan-id", "plan-1",
                "--student-id", student_id,
                "--planned-group-key", "group-a",
                "--expected-snapshot", str(snapshot),
                "--actor-id", "teacher-1",
            ]
        ) == 0
    assert main(
        [
            "group-plan", "preview",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--expected-snapshot", "5",
            "--actor-id", "teacher-1",
        ]
    ) == 0
    assert main(
        [
            "group-plan", "approve",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--expected-snapshot", "6",
            "--actor-id", "teacher-1",
        ]
    ) == 0
    return root


def test_application_cli_preview_then_apply_exact_write_set(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    capsys.readouterr()
    assert main(
        [
            "group-plan", "application-preview",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--application-id", "apply-cli-1",
            "--session-id", "session-1",
        ]
    ) == 0
    preview_output = capsys.readouterr().out
    assert "Application ID: apply-cli-1" in preview_output
    assert "Expected Activity snapshot: 7" in preview_output
    assert "Canonical Groups to create: 1" in preview_output
    assert "Canonical Memberships to create: 2" in preview_output
    assert "No changes have been written." in preview_output
    assert "student-1 -> membership-" in preview_output
    assert "student-2 -> membership-" in preview_output
    digest = next(
        line.split(": ", 1)[1]
        for line in preview_output.splitlines()
        if line.startswith("Application digest: ")
    )
    assert len(digest) == 64
    assert show_group_plan(
        "class-1", "activity-1", "plan-1", workspace_root=root
    ).plan.status == "approved"
    assert list_groups("class-1", "activity-1", workspace_root=root) == ()

    assert main(
        [
            "group-plan", "apply",
            "--workspace-root", str(root),
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--application-id", "apply-cli-1",
            "--application-digest", digest,
            "--session-id", "session-1",
            "--expected-snapshot", "7",
            "--actor-id", "teacher-apply",
        ]
    ) == 0
    output = capsys.readouterr().out
    assert "Status: applied" in output
    assert "Groups created: 1" in output
    assert "Memberships created: 2" in output
    assert "Students left unresolved: 0" in output
    assert "Committed snapshot 8." in output
    assert len(list_groups("class-1", "activity-1", workspace_root=root)) == 1
    assert len(list_memberships("class-1", "activity-1", workspace_root=root)) == 2


def test_application_cli_contract_is_explicit() -> None:
    parser = build_parser()
    preview = parser.parse_args(
        [
            "group-plan", "application-preview",
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--application-id", "apply-cli-1",
            "--session-id", "session-1",
        ]
    )
    assert preview.application_id == "apply-cli-1"
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "group-plan", "apply",
                "--class-id", "class-1",
                "--activity-id", "activity-1",
                "--group-plan-id", "plan-1",
                "--application-id", "apply-cli-1",
                "--application-digest", "a" * 64,
                "--expected-snapshot", "7",
            ]
        )
    applied = parser.parse_args(
        [
            "group-plan", "apply",
            "--class-id", "class-1",
            "--activity-id", "activity-1",
            "--group-plan-id", "plan-1",
            "--application-id", "apply-cli-1",
            "--application-digest", "a" * 64,
            "--expected-snapshot", "7",
            "--actor-id", "teacher-1",
            "--session-id", "session-1",
        ]
    )
    assert applied.application_digest == "a" * 64
