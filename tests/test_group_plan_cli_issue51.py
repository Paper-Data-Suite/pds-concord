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
from concord.workflows import (
    AddPlannedGroupRequest,
    ArrangementImportResult,
    CreateManualGroupPlanRequest,
    GroupPlanEditResult,
    PlaceStudentInPlanRequest,
    RefreshGroupPlanRosterRequest,
    add_planned_group,
    create_manual_group_plan,
    import_arrangement_group_plan,
    place_student_in_plan,
    refresh_group_plan_roster,
)


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
            [
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Student",
                    "period": "1",
                },
                {
                    "student_id": "student-2",
                    "last_name": "Two",
                    "first_name": "Student",
                    "period": "1",
                },
                {
                    "student_id": "student-3",
                    "last_name": "Three",
                    "first_name": "Student",
                    "period": "1",
                },
            ],
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
                "Planning CLI",
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


def _base_mutation(root: Path, command: str, expected: int) -> list[str]:
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
        "plan-1",
        "--expected-snapshot",
        str(expected),
        "--actor-id",
        "teacher-1",
    ]


def test_public_manual_authoring_api_is_exported() -> None:
    assert CreateManualGroupPlanRequest is not None
    assert AddPlannedGroupRequest is not None
    assert PlaceStudentInPlanRequest is not None
    assert RefreshGroupPlanRosterRequest is not None
    assert GroupPlanEditResult is not None
    assert ArrangementImportResult is not None
    assert create_manual_group_plan is not None
    assert add_planned_group is not None
    assert place_student_in_plan is not None
    assert refresh_group_plan_roster is not None
    assert import_arrangement_group_plan is not None


def test_group_plan_manual_direct_commands_and_noop_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    capsys.readouterr()

    assert main(_base_mutation(root, "create-manual", 1)) == 0
    created = capsys.readouterr().out
    assert "Committed snapshot 2." in created
    assert "GroupPlan: plan-1" in created
    assert "Status: draft" in created

    assert (
        main(
            _base_mutation(root, "add-group", 2)
            + [
                "--planned-group-key",
                "table-a",
                "--label",
                "Table A",
                "--description",
                "Keep this note",
                "--session-id",
                "session-1",
            ]
        )
        == 0
    )
    assert "Committed snapshot 3." in capsys.readouterr().out

    assert (
        main(
            _base_mutation(root, "edit-group", 3)
            + [
                "--planned-group-key",
                "table-a",
                "--label",
                "Renamed Table",
            ]
        )
        == 0
    )
    assert "Committed snapshot 4." in capsys.readouterr().out

    place_args = _base_mutation(root, "place-student", 4) + [
        "--student-id",
        "student-1",
        "--planned-group-key",
        "table-a",
    ]
    assert main(place_args) == 0
    placed = capsys.readouterr().out
    assert "Committed snapshot 5." in placed
    assert "Unresolved students: 2" in placed

    place_args[place_args.index("--expected-snapshot") + 1] = "5"
    assert main(place_args) == 0
    noop = capsys.readouterr().out
    assert "No changes were needed." in noop
    assert "Snapshot revision: 5" in noop

    assert (
        main(
            [
                "group-plan",
                "show",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--group-plan-id",
                "plan-1",
            ]
        )
        == 0
    )
    shown = capsys.readouterr().out
    assert "Planned group: table-a" in shown
    assert "label=Renamed Table" in shown
    assert "students=student-1" in shown
    assert "Description: Keep this note" in shown
    assert "Sessions: session-1" in shown
    assert "Unresolved student IDs: student-2,student-3" in shown


def test_arrangement_import_preview_approve_and_direct_group_remain_distinct(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    capsys.readouterr()
    csv_path = tmp_path / "arrangement.csv"
    csv_path.write_text(
        "student_id,group\n"
        "student-1,alpha\n"
        "student-2,alpha\n"
        "student-3,beta\n",
        encoding="utf-8",
    )

    common = [
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--group-plan-id",
        "import-1",
        "--actor-id",
        "teacher-1",
    ]
    assert (
        main(
            [
                "group-plan",
                "import-arrangement",
                *common,
                "--csv-path",
                str(csv_path),
                "--expected-snapshot",
                "1",
            ]
        )
        == 0
    )
    imported = capsys.readouterr().out
    assert "Committed snapshot 2." in imported
    assert "Proposed groups: 2" in imported
    assert "Assigned students: 3" in imported
    assert "Unresolved students: 0" in imported

    assert (
        main(
            [
                "group-plan",
                "preview",
                *common,
                "--expected-snapshot",
                "2",
            ]
        )
        == 0
    )
    previewed = capsys.readouterr().out
    assert "Persisted exact GroupPlan preview." in previewed
    assert "Status: previewed" in previewed
    assert "Snapshot revision: 3" in previewed

    assert (
        main(
            [
                "group-plan",
                "approve",
                *common,
                "--expected-snapshot",
                "3",
            ]
        )
        == 0
    )
    approved = capsys.readouterr().out
    assert "Committed snapshot 4." in approved
    assert "Status: approved" in approved
    assert "Canonical Groups created: no" in approved

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

    assert (
        main(
            [
                "group",
                "create",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--group-id",
                "direct-group",
                "--label",
                "Direct Group",
                "--expected-snapshot",
                "4",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )
    assert "Committed snapshot 5." in capsys.readouterr().out


def test_invalid_arrangement_direct_command_is_atomic(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    capsys.readouterr()
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text(
        "student_id,group\nstudent-99,alpha\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "group-plan",
                "import-arrangement",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--group-plan-id",
                "bad-plan",
                "--csv-path",
                str(csv_path),
                "--expected-snapshot",
                "1",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "not in Core roster" in captured.err

    assert (
        main(
            [
                "group-plan",
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
    assert "No GroupPlans found." in capsys.readouterr().out
