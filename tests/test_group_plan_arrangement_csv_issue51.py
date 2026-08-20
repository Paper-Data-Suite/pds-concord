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

from concord.group_plan_arrangement_csv import (
    ArrangementCsvValidationError,
    parse_arrangement_csv_bytes,
    parse_arrangement_csv_text,
)
from concord.storage import list_record_revisions, list_work_snapshots
from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
)
from concord.workflows.group_plan_manual import (
    ImportArrangementGroupPlanRequest,
    PlaceStudentInPlanRequest,
    ReplaceArrangementGroupPlanRequest,
    import_arrangement_group_plan,
    place_student_in_plan,
    replace_group_plan_from_arrangement,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 15, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _roster(*student_ids: str):
    return create_roster(
        "class-1",
        tuple(
            {
                "student_id": student_id,
                "last_name": f"Last-{index}",
                "first_name": f"First-{index}",
                "period": "1",
            }
            for index, student_id in enumerate(student_ids, start=1)
        ),
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(root, _roster("student-1", "student-2", "student-3"))
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Planning Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    return root, created.commit.snapshot_revision


def test_parser_is_strict_deterministic_and_allows_partial_roster() -> None:
    roster = ("student-1", "student-2", "student-3", "student-4")
    first = parse_arrangement_csv_text(
        "student_id,group\nstudent-3,b\nstudent-1,a\nstudent-2,a\n",
        roster_student_ids=roster,
    )
    second = parse_arrangement_csv_text(
        "student_id,group\nstudent-2,a\nstudent-1,a\nstudent-3,b\n",
        roster_student_ids=roster,
    )
    assert first == second
    assert tuple(group.planned_group_key for group in first.proposed_groups) == (
        "a",
        "b",
    )
    assert first.proposed_groups[0].student_ids == ("student-1", "student-2")
    assert first.unresolved_student_ids == ("student-4",)
    assert first.data_row_count == 3
    assert first.assigned_student_count == 3


def test_utf8_bom_and_standard_csv_quoting_are_accepted() -> None:
    parsed = parse_arrangement_csv_bytes(
        b'\xef\xbb\xbfstudent_id,group\r\n"student-1","group-a"\r\n',
        roster_student_ids=("student-1", "student-2"),
    )
    assert parsed.proposed_groups[0].planned_group_key == "group-a"
    assert parsed.unresolved_student_ids == ("student-2",)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("Student_ID,group\nstudent-1,a\n", "expected header"),
        ("student_id,Group\nstudent-1,a\n", "expected header"),
        ("student_id,group,label\nstudent-1,a,A\n", "expected header"),
        ("student_id,group\nstudent-1\n", "exactly 2 columns"),
        ("student_id,group\nstudent-1,a,extra\n", "exactly 2 columns"),
        ("student_id,group\n,a\n", "student_id must not be empty"),
        ("student_id,group\nstudent-1,\n", "group must not be empty"),
        ("student_id,group\n student-1,a\n", "leading or trailing whitespace"),
        ("student_id,group\nstudent-1,group a\n", "letters, numbers"),
        ("student_id,group\nstudent-99,a\n", "not in Core roster"),
        (
            "student_id,group\nstudent-1,a\nstudent-1,a\n",
            "duplicate student_id",
        ),
        ("student_id,group\n", "at least one data row"),
    ],
)
def test_invalid_csv_cases_are_actionable(text: str, message: str) -> None:
    with pytest.raises(ArrangementCsvValidationError, match=message):
        parse_arrangement_csv_text(
            text,
            roster_student_ids=("student-1", "student-2"),
        )


def test_blank_physical_lines_are_ignored() -> None:
    parsed = parse_arrangement_csv_text(
        "\nstudent_id,group\n\nstudent-1,a\n\n",
        roster_student_ids=("student-1", "student-2"),
    )
    assert parsed.assigned_student_count == 1


def test_import_creates_draft_without_persisting_source_path(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    source = tmp_path / "private-user-path" / "arrangement.csv"
    source.parent.mkdir()
    source.write_text(
        "student_id,group\nstudent-1,a\nstudent-2,a\n",
        encoding="utf-8",
    )
    result = import_arrangement_group_plan(
        ImportArrangementGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            csv_path=source,
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    from concord.workflows import show_group_plan

    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.plan.strategy == "imported_arrangement"
    assert detail.plan.status == "draft"
    assert detail.plan.unresolved_student_ids == ("student-3",)
    assert result.proposed_group_count == 1
    assert result.assigned_student_count == 2
    assert result.unresolved_student_count == 1
    assert str(source) not in repr(detail.plan)

    from concord.storage import load_current_record_graph

    loaded = load_current_record_graph(root, result.mutation.commit.work)
    assert loaded.graph.groups == ()
    assert loaded.graph.memberships == ()


def test_imported_plan_remains_manually_editable_with_origin_preserved(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    source = tmp_path / "arrangement.csv"
    source.write_text("student_id,group\nstudent-1,a\n", encoding="utf-8")
    imported = import_arrangement_group_plan(
        ImportArrangementGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            csv_path=source,
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    edited = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-2",
            planned_group_key="a",
            expected_snapshot_revision=imported.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert edited.detail.plan.strategy == "imported_arrangement"
    assert edited.detail.plan.proposed_groups[0].student_ids == (
        "student-1",
        "student-2",
    )


def test_invalid_replace_is_atomic(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    good = tmp_path / "good.csv"
    good.write_text("student_id,group\nstudent-1,a\n", encoding="utf-8")
    imported = import_arrangement_group_plan(
        ImportArrangementGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            csv_path=good,
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    before_snapshots = list_work_snapshots(root, imported.mutation.commit.work)
    before_revisions = list_record_revisions(
        root,
        imported.mutation.commit.work,
        "group_plan",
        "plan-1",
    )
    bad = tmp_path / "bad.csv"
    bad.write_text(
        "student_id,group\nstudent-99,a\n",
        encoding="utf-8",
    )
    with pytest.raises(ArrangementCsvValidationError):
        replace_group_plan_from_arrangement(
            ReplaceArrangementGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                csv_path=bad,
                expected_snapshot_revision=imported.mutation.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    assert list_work_snapshots(root, imported.mutation.commit.work) == before_snapshots
    assert (
        list_record_revisions(
            root,
            imported.mutation.commit.work,
            "group_plan",
            "plan-1",
        )
        == before_revisions
    )


def test_replace_arrangement_changes_origin_and_clears_random_metadata(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    from concord.models import PlannedGroup
    from concord.workflows import (
        CreateGroupPlanRequest,
        create_group_plan,
        show_group_plan,
    )

    created = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            strategy="random",
            target_group_count=2,
            seed="seed-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(PlannedGroup(planned_group_key="x", label="X"),),
        ),
        workspace_root=root,
    )
    source = tmp_path / "replacement.csv"
    source.write_text("student_id,group\nstudent-1,a\n", encoding="utf-8")
    replaced = replace_group_plan_from_arrangement(
        ReplaceArrangementGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            csv_path=source,
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.plan.strategy == "imported_arrangement"
    assert detail.plan.seed is None
    assert detail.plan.target_group_count is None
    assert detail.plan.source_signal_set_id is None
    assert replaced.unresolved_student_count == 2
