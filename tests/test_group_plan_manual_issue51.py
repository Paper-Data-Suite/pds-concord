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

from concord.models import PlannedGroup
from concord.storage import list_record_revisions, list_work_snapshots
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_group_plan,
    show_group_plan,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan_manual import (
    AddPlannedGroupRequest,
    CreateManualGroupPlanRequest,
    EditPlannedGroupRequest,
    PlaceStudentInPlanRequest,
    RefreshGroupPlanRosterRequest,
    RemovePlannedGroupRequest,
    UnassignStudentFromPlanRequest,
    add_planned_group,
    create_manual_group_plan,
    edit_planned_group,
    place_student_in_plan,
    refresh_group_plan_roster,
    remove_planned_group,
    unassign_student_from_plan,
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


def _manual(root: Path, revision: int):
    return create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )


def test_manual_create_add_place_move_unassign_and_remove(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = _manual(root, revision)
    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.plan.strategy == "manual"
    assert detail.plan.unresolved_student_ids == (
        "student-1",
        "student-2",
        "student-3",
    )

    a = add_planned_group(
        AddPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="a",
            label="Table A",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    b = add_planned_group(
        AddPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="b",
            label="Table B",
            expected_snapshot_revision=a.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    placed = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-1",
            planned_group_key="a",
            expected_snapshot_revision=b.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    before_move_revisions = list_record_revisions(
        root,
        created.commit.work,
        "group_plan",
        "plan-1",
    )
    moved = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-1",
            planned_group_key="b",
            expected_snapshot_revision=placed.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    after_move_revisions = list_record_revisions(
        root,
        created.commit.work,
        "group_plan",
        "plan-1",
    )
    assert len(after_move_revisions) == len(before_move_revisions) + 1
    assert moved.detail.plan.proposed_groups[0].student_ids == ()
    assert moved.detail.plan.proposed_groups[1].student_ids == ("student-1",)

    unassigned = unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-1",
            expected_snapshot_revision=moved.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(8),
    )
    assert "student-1" in unassigned.detail.plan.unresolved_student_ids

    removed = remove_planned_group(
        RemovePlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="a",
            expected_snapshot_revision=unassigned.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(9),
    )
    assert tuple(
        group.planned_group_key for group in removed.detail.plan.proposed_groups
    ) == ("b",)


def test_remove_populated_group_returns_students_to_unresolved(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="a",
                    label="A",
                    student_ids=("student-1", "student-2"),
                ),
            ),
        ),
        workspace_root=root,
    )
    result = remove_planned_group(
        RemovePlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="a",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert result.detail.plan.proposed_groups == ()
    assert result.detail.plan.unresolved_student_ids == (
        "student-1",
        "student-2",
        "student-3",
    )


def test_metadata_edit_keeps_key_and_noop_creates_no_history(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(PlannedGroup(planned_group_key="a", label="Old"),),
        ),
        workspace_root=root,
    )
    edited = edit_planned_group(
        EditPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="a",
            label="New",
            description="Teacher-facing note",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert edited.detail.plan.proposed_groups[0].planned_group_key == "a"
    assert edited.detail.plan.proposed_groups[0].label == "New"

    before = list_work_snapshots(root, created.commit.work)
    noop = edit_planned_group(
        EditPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="a",
            label="New",
            description="Teacher-facing note",
            expected_snapshot_revision=edited.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert noop.changed is False
    assert list_work_snapshots(root, created.commit.work) == before


def test_same_destination_and_already_unresolved_are_noops(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="a",
                    label="A",
                    student_ids=("student-1",),
                ),
            ),
        ),
        workspace_root=root,
    )
    before = list_work_snapshots(root, created.commit.work)
    same = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-1",
            planned_group_key="a",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert same.changed is False
    unresolved = unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-2",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert unresolved.changed is False
    assert list_work_snapshots(root, created.commit.work) == before


def test_targeted_edit_blocks_roster_drift_and_refresh_is_explicit(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="a",
                    label="A",
                    student_ids=("student-1", "student-3"),
                ),
            ),
        ),
        workspace_root=root,
    )
    write_class_roster(
        root,
        _roster("student-1", "student-2", "student-4"),
        overwrite=True,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="refresh"):
        add_planned_group(
            AddPlannedGroupRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                planned_group_key="b",
                label="B",
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    refreshed = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert refreshed.changed is True
    assert refreshed.detail.plan.roster_student_ids == (
        "student-1",
        "student-2",
        "student-4",
    )
    assert refreshed.detail.plan.proposed_groups[0].student_ids == ("student-1",)
    assert refreshed.detail.plan.unresolved_student_ids == (
        "student-2",
        "student-4",
    )


def test_manual_edit_preserves_random_and_signal_origin_metadata(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    random_created = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            strategy="random",
            target_group_count=2,
            seed="seed-7",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=(PlannedGroup(planned_group_key="a", label="A"),),
        ),
        workspace_root=root,
    )
    random_edit = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            student_id="student-1",
            planned_group_key="a",
            expected_snapshot_revision=random_created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert random_edit.detail.plan.strategy == "random"
    assert random_edit.detail.plan.seed == "seed-7"
    assert random_edit.detail.plan.target_group_count == 2

    signal_created = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            strategy="similar_signal",
            target_group_count=2,
            source_signal_set_id="signal-1",
            source_signal_set_digest="a" * 64,
            source_signal_dimension_id="dimension-1",
            expected_snapshot_revision=random_edit.detail.summary.snapshot_revision,
            actor=_actor(),
            proposed_groups=(PlannedGroup(planned_group_key="x", label="X"),),
        ),
        workspace_root=root,
    )
    signal_edit = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            student_id="student-2",
            planned_group_key="x",
            expected_snapshot_revision=signal_created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert signal_edit.detail.plan.strategy == "similar_signal"
    assert signal_edit.detail.plan.source_signal_set_id == "signal-1"
    assert signal_edit.detail.plan.source_signal_set_digest == "a" * 64
    assert signal_edit.detail.plan.source_signal_dimension_id == "dimension-1"


def test_terminal_plan_rejects_targeted_edit(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = _manual(root, revision)
    from concord.workflows import CancelGroupPlanRequest, cancel_group_plan

    cancelled = cancel_group_plan(
        CancelGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="draft or previewed"):
        add_planned_group(
            AddPlannedGroupRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                planned_group_key="a",
                label="A",
                expected_snapshot_revision=cancelled.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_unknown_student_and_group_are_rejected(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = _manual(root, revision)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="not in the current Core roster",
    ):
        place_student_in_plan(
            PlaceStudentInPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                student_id="student-99",
                planned_group_key="a",
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_editing_previewed_plan_returns_it_to_draft(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = _manual(root, revision)
    from concord.workflows import PreviewGroupPlanRequest, preview_group_plan

    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    edited = add_planned_group(
        AddPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            planned_group_key="a",
            label="A",
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert edited.detail.plan.status == "draft"
    assert edited.detail.plan.previewed_provenance is None
