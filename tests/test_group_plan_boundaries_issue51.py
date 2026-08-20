from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.models import PlannedGroup
from concord.storage import list_record_revisions, load_current_record_graph
from concord.workflows import (
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    CreateGroupRequest,
    CreateManualGroupPlanRequest,
    PlaceStudentInPlanRequest,
    PreviewGroupPlanRequest,
    WorkflowActor,
    approve_group_plan,
    create_activity_context,
    create_group,
    create_manual_group_plan,
    place_student_in_plan,
    preview_group_plan,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 16, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1", role_label="teacher")


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
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
            ),
        ),
    )
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


def test_group_plan_authoring_preview_and_approval_create_only_plan_state(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            proposed_groups=(
                PlannedGroup(planned_group_key="a", label="Group A"),
                PlannedGroup(planned_group_key="b", label="Group B"),
            ),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    placed1 = place_student_in_plan(
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
        clock=lambda: _clock(4),
    )
    placed2 = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            student_id="student-2",
            planned_group_key="b",
            expected_snapshot_revision=placed1.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=placed2.detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    loaded = load_current_record_graph(root, approved.commit.work)
    graph = loaded.graph
    assert len(graph.group_plans) == 1
    assert graph.group_plans[0].status == "approved"
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


def test_direct_group_creation_remains_independent_of_group_plan_history(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created_plan = create_manual_group_plan(
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
    before = list_record_revisions(
        root,
        created_plan.commit.work,
        "group_plan",
        "plan-1",
    )
    created_group = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="direct-group",
            label="Direct Group",
            expected_snapshot_revision=created_plan.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    after = list_record_revisions(
        root,
        created_group.commit.work,
        "group_plan",
        "plan-1",
    )
    assert after == before == (1,)
    loaded = load_current_record_graph(root, created_group.commit.work)
    assert tuple(group.group_id for group in loaded.graph.groups) == ("direct-group",)
    assert tuple(plan.group_plan_id for plan in loaded.graph.group_plans) == ("plan-1",)
