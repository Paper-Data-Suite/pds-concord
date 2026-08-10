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

from concord.cli import build_parser, main


@pytest.fixture
def cli_workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 8, 9, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    roster = create_roster(
        "class-1",
        [
            {
                "student_id": "student-1",
                "last_name": "Doe",
                "first_name": "Jane",
                "period": "2",
            },
            {
                "student_id": "student-2",
                "last_name": "Smith",
                "first_name": "Marcus",
                "period": "2",
            },
        ],
    )
    write_class_roster(root, roster)
    return root


def _activity_create_args(root: Path) -> list[str]:
    return [
        "activity",
        "create",
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--title",
        "Synthetic Activity",
        "--activity-type",
        "socratic_seminar",
        "--scoring-orientation",
        "evidence_only",
        "--session-id",
        "session-1",
        "--session-label",
        "Opening Session",
        "--actor-id",
        "teacher-1",
    ]


def test_parser_construction_is_side_effect_free(tmp_path: Path) -> None:
    target = tmp_path / "workspace-that-must-not-exist"
    build_parser()
    assert not target.exists()


def test_direct_activity_create_list_show_and_update(
    cli_workspace: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "builtins.input",
        lambda *_args, **_kwargs: pytest.fail("direct CLI must not prompt"),
    )
    assert main(_activity_create_args(cli_workspace)) == 0
    created = capsys.readouterr()
    assert "Committed snapshot 1." in created.out
    assert "First Session: session-1" in created.out
    assert created.err == ""

    assert (
        main(
            [
                "activity",
                "list",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
            ]
        )
        == 0
    )
    listed = capsys.readouterr()
    assert "activity-1" in listed.out
    assert "sessions=1" in listed.out

    assert (
        main(
            [
                "activity",
                "show",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
            ]
        )
        == 0
    )
    shown = capsys.readouterr()
    assert "Title: Synthetic Activity" in shown.out
    assert "Snapshot revision: 1" in shown.out

    assert (
        main(
            [
                "activity",
                "update",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--expected-snapshot",
                "1",
                "--actor-id",
                "teacher-1",
                "--title",
                "Revised Activity",
            ]
        )
        == 0
    )
    updated = capsys.readouterr()
    assert "Committed snapshot 2." in updated.out


def test_direct_session_group_membership_role_and_responsibility_chain(
    cli_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(_activity_create_args(cli_workspace)) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "session",
                "add",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--session-id",
                "session-2",
                "--sequence",
                "2",
                "--expected-snapshot",
                "1",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    assert "Committed snapshot 2." in capsys.readouterr().out

    assert (
        main(
            [
                "group",
                "create",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--group-id",
                "group-1",
                "--label",
                "Group One",
                "--status",
                "active",
                "--expected-snapshot",
                "2",
                "--actor-id",
                "teacher-1",
                "--session-id",
                "session-1",
                "--session-id",
                "session-2",
            ]
        )
        == 0
    )
    assert "Committed snapshot 3." in capsys.readouterr().out

    assert (
        main(
            [
                "group",
                "member",
                "add",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--group-id",
                "group-1",
                "--student-id",
                "student-1",
                "--student-id",
                "student-2",
                "--membership-id",
                "membership-1",
                "--membership-id",
                "membership-2",
                "--session-id",
                "session-1",
                "--session-id",
                "session-2",
                "--expected-snapshot",
                "3",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    membership_output = capsys.readouterr().out
    assert "Membership: membership-1" in membership_output
    assert "Membership: membership-2" in membership_output

    assert (
        main(
            [
                "role",
                "assign",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--role-assignment-id",
                "role-1",
                "--student-id",
                "student-1",
                "--role-key",
                "facilitator",
                "--membership-id",
                "membership-1",
                "--group-id",
                "group-1",
                "--session-id",
                "session-1",
                "--session-id",
                "session-2",
                "--expected-snapshot",
                "4",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    assert "Committed snapshot 5." in capsys.readouterr().out

    assert (
        main(
            [
                "responsibility",
                "assign",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--responsibility-assignment-id",
                "responsibility-1",
                "--student-id",
                "student-1",
                "--description",
                "Summarize the discussion.",
                "--group-id",
                "group-1",
                "--session-id",
                "session-1",
                "--session-id",
                "session-2",
                "--expected-snapshot",
                "5",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    assert "Committed snapshot 6." in capsys.readouterr().out

    assert (
        main(
            [
                "role",
                "list",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
            ]
        )
        == 0
    )
    assert "role-1" in capsys.readouterr().out

    assert (
        main(
            [
                "responsibility",
                "list",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
            ]
        )
        == 0
    )
    assert "responsibility-1" in capsys.readouterr().out


def test_direct_stale_expected_snapshot_returns_conflict_status(
    cli_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(_activity_create_args(cli_workspace)) == 0
    capsys.readouterr()

    result = main(
        [
            "session",
            "add",
            "--workspace-root",
            str(cli_workspace),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--session-id",
            "session-2",
            "--sequence",
            "2",
            "--expected-snapshot",
            "99",
            "--actor-id",
            "teacher-1",
        ]
    )
    captured = capsys.readouterr()
    assert result == 3
    assert captured.out == ""
    assert "Conflict:" in captured.err


def test_read_only_workspace_show_does_not_create_root(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "absent-workspace"
    assert main(["workspace", "show", "--workspace-root", str(root)]) == 0
    captured = capsys.readouterr()
    assert "Exists: no" in captured.out
    assert not root.exists()


def test_missing_required_cli_argument_is_usage_error() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["activity", "create"])
    assert exit_info.value.code == 2


@pytest.mark.parametrize(
    "arguments",
    [
        ["activity", "--help"],
        ["session", "--help"],
        ["group", "--help"],
        ["group", "member", "--help"],
        ["role", "--help"],
        ["responsibility", "--help"],
        ["workspace", "--help"],
    ],
)
def test_every_direct_command_family_has_help(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(arguments)
    assert exit_info.value.code == 0


def test_membership_batch_ids_must_match_students(
    cli_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(_activity_create_args(cli_workspace)) == 0
    capsys.readouterr()
    assert (
        main(
            [
                "group",
                "create",
                "--workspace-root",
                str(cli_workspace),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--group-id",
                "group-1",
                "--label",
                "Group One",
                "--expected-snapshot",
                "1",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    capsys.readouterr()
    result = main(
        [
            "group",
            "member",
            "add",
            "--workspace-root",
            str(cli_workspace),
            "--class-id",
            "class-1",
            "--activity-id",
            "activity-1",
            "--group-id",
            "group-1",
            "--student-id",
            "student-1",
            "--student-id",
            "student-2",
            "--membership-id",
            "membership-1",
            "--session-id",
            "session-1",
            "--expected-snapshot",
            "2",
            "--actor-id",
            "teacher-1",
        ]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert "Repeat --membership-id exactly once" in captured.err
