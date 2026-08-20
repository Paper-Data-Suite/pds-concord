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

from concord.storage import load_current_record_graph
from concord.workflows import (
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    CreateRandomGroupPlanRequest,
    EditPlannedGroupRequest,
    PlaceStudentInPlanRequest,
    PreviewGroupPlanRequest,
    RefreshGroupPlanRosterRequest,
    UnassignStudentFromPlanRequest,
    WorkflowActor,
    approve_group_plan,
    create_activity_context,
    create_random_group_plan,
    edit_planned_group,
    place_student_in_plan,
    preview_group_plan,
    refresh_group_plan_roster,
    show_group_plan,
    unassign_student_from_plan,
)
from concord.workflows.errors import ConcordWorkflowConflictError


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 17, 0, tzinfo=timezone.utc)


def _actor(actor_id: str = "teacher-1") -> WorkflowActor:
    return WorkflowActor(actor_id=actor_id, role_label="teacher")


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


def _workspace(
    tmp_path: Path,
    *,
    name: str = "workspace",
    student_ids: tuple[str, ...] = (
        "student-1",
        "student-2",
        "student-3",
        "student-4",
        "student-5",
        "student-6",
    ),
) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / name)
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(root, _roster(*student_ids))
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Random Planning Boundary",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    return root, created.commit.snapshot_revision


def _membership(detail) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (group.planned_group_key, group.student_ids)
        for group in detail.plan.proposed_groups
    )


def test_random_arrangement_does_not_depend_on_plan_actor_or_clock(
    tmp_path: Path,
) -> None:
    root_a, revision_a = _workspace(tmp_path, name="a")
    root_b, revision_b = _workspace(tmp_path, name="b")

    create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-a",
            expected_snapshot_revision=revision_a,
            actor=_actor("teacher-a"),
            seed="same-seed",
            target_group_count=3,
        ),
        workspace_root=root_a,
        clock=lambda: _clock(3),
    )
    create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="different-plan-id",
            expected_snapshot_revision=revision_b,
            actor=_actor("teacher-b"),
            seed="same-seed",
            target_group_count=3,
        ),
        workspace_root=root_b,
        clock=lambda: _clock(9),
    )

    a = show_group_plan(
        "class-1",
        "activity-1",
        "plan-a",
        workspace_root=root_a,
    )
    b = show_group_plan(
        "class-1",
        "activity-1",
        "different-plan-id",
        workspace_root=root_b,
    )
    assert _membership(a) == _membership(b)


def test_random_plan_manual_edits_preserve_origin_metadata(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed-52",
            target_group_count=2,
        ),
        workspace_root=root,
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "random-plan",
        workspace_root=root,
    )
    first, second = detail.plan.proposed_groups

    renamed = edit_planned_group(
        EditPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            planned_group_key=first.planned_group_key,
            label="Teacher Table",
            expected_snapshot_revision=(
                created.mutation.commit.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
    )
    student_id = renamed.detail.plan.proposed_groups[0].student_ids[0]

    unassigned = unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            student_id=student_id,
            expected_snapshot_revision=(
                renamed.detail.summary.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
    )
    replaced = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            student_id=student_id,
            planned_group_key=second.planned_group_key,
            expected_snapshot_revision=(
                unassigned.detail.summary.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
    )

    assert replaced.detail.plan.strategy == "random"
    assert replaced.detail.plan.seed == "seed-52"
    assert replaced.detail.plan.target_group_count == 2
    assert replaced.detail.plan.proposed_groups[0].label == "Teacher Table"
    assert replaced.detail.plan.unresolved_student_ids == ()


def test_explicit_refresh_preserves_random_origin_and_does_not_rerandomize(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(
        tmp_path,
        student_ids=(
            "student-1",
            "student-2",
            "student-3",
            "student-4",
        ),
    )
    created = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed-52",
            target_group_count=2,
        ),
        workspace_root=root,
    )
    before = show_group_plan(
        "class-1",
        "activity-1",
        "random-plan",
        workspace_root=root,
    )
    departed = before.plan.proposed_groups[0].student_ids[0]
    survivors = {
        student_id: group.planned_group_key
        for group in before.plan.proposed_groups
        for student_id in group.student_ids
        if student_id != departed
    }
    current_students = tuple(
        student_id
        for student_id in before.plan.roster_student_ids
        if student_id != departed
    ) + ("student-9",)
    write_class_roster(root, _roster(*current_students), overwrite=True)

    refreshed = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=(
                created.mutation.commit.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
    )

    assert refreshed.detail.plan.strategy == "random"
    assert refreshed.detail.plan.seed == "seed-52"
    assert refreshed.detail.plan.target_group_count == 2
    assert refreshed.detail.plan.unresolved_student_ids == ("student-9",)

    after_locations = {
        student_id: group.planned_group_key
        for group in refreshed.detail.plan.proposed_groups
        for student_id in group.student_ids
    }
    assert after_locations == survivors


def test_random_preview_and_approval_create_only_group_plan_state(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed-52",
            target_group_count=2,
        ),
        workspace_root=root,
    )
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=(
                created.mutation.commit.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
    )
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=(
                previewed.summary.snapshot_revision
            ),
            actor=_actor(),
        ),
        workspace_root=root,
    )

    graph = load_current_record_graph(root, approved.commit.work).graph
    assert len(graph.group_plans) == 1
    assert graph.group_plans[0].status == "approved"
    assert graph.group_plans[0].strategy == "random"
    assert graph.groups == ()
    assert graph.memberships == ()
    assert graph.role_assignments == ()
    assert graph.responsibility_assignments == ()
    assert graph.artifact_instances == ()
    assert graph.artifact_pages == ()
    assert graph.scan_references == ()
    assert graph.artifact_authors == ()
    assert graph.artifact_subjects == ()
    assert graph.artifact_reviews == ()
    assert graph.moderation_records == ()
    assert graph.criterion_sets == ()
    assert graph.criteria == ()
    assert graph.scoring_scales == ()
    assert graph.score_records == ()
    assert graph.score_evidence_links == ()
    assert graph.correction_records == ()


def test_random_workflow_respects_snapshot_and_plan_identity_conflicts(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="random-plan",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed-52",
            target_group_count=2,
        ),
        workspace_root=root,
    )

    with pytest.raises(ConcordWorkflowConflictError):
        create_random_group_plan(
            CreateRandomGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="second-plan",
                expected_snapshot_revision=revision,
                actor=_actor(),
                seed="seed-52",
                target_group_count=2,
            ),
            workspace_root=root,
        )

    with pytest.raises(ConcordWorkflowConflictError):
        create_random_group_plan(
            CreateRandomGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="random-plan",
                expected_snapshot_revision=(
                    created.mutation.commit.snapshot_revision
                ),
                actor=_actor(),
                seed="seed-52",
                target_group_count=2,
            ),
            workspace_root=root,
        )
