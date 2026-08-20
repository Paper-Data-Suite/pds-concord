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
    ApproveGroupPlanRequest,
    CancelGroupPlanRequest,
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
    CreateActivityContextRequest,
    CreateGroupPlanRequest,
    CreateGroupRequest,
    PreviewGroupPlanRequest,
    ReplaceGroupPlanProposalRequest,
    WorkflowActor,
    approve_group_plan,
    cancel_group_plan,
    create_activity_context,
    create_group,
    create_group_plan,
    list_group_plans,
    preview_group_plan,
    replace_group_plan_proposal,
    show_group_plan,
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
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(1),
    )
    write_class_metadata_for_class(root, metadata)
    write_class_roster(
        root,
        _roster("student-1", "student-2", "student-3"),
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


def _all_assigned_groups() -> tuple[PlannedGroup, ...]:
    return (
        PlannedGroup(
            planned_group_key="a",
            label="Group A",
            student_ids=("student-1", "student-2"),
        ),
        PlannedGroup(
            planned_group_key="b",
            label="Group B",
            student_ids=("student-3",),
        ),
    )


def _create(
    root: Path,
    revision: int,
    *,
    groups: tuple[PlannedGroup, ...] = (),
):
    return create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            strategy="manual",
            expected_snapshot_revision=revision,
            actor=_actor(),
            proposed_groups=groups,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )


def test_create_derives_exact_roster_and_creates_no_group_state(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(
        root,
        revision,
        groups=(
            PlannedGroup(
                planned_group_key="a",
                label="Group A",
                student_ids=("student-2", "student-1"),
            ),
        ),
    )
    assert created.status == "draft"
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    assert detail.plan.roster_student_ids == (
        "student-1",
        "student-2",
        "student-3",
    )
    assert detail.plan.unresolved_student_ids == ("student-3",)
    assert list_group_plans(
        "class-1",
        "activity-1",
        workspace_root=root,
    )[0].assigned_student_count == 2

    from concord.storage import load_current_record_graph

    loaded = load_current_record_graph(
        root,
        created.commit.work,
    )
    assert loaded.graph.groups == ()
    assert loaded.graph.memberships == ()


def test_show_is_read_only_and_preview_returns_exact_persisted_revision(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    before = list_work_snapshots(root, created.commit.work)
    first = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    second = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    assert first == second
    assert list_work_snapshots(root, created.commit.work) == before

    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    persisted = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    assert previewed == persisted
    assert previewed.plan.status == "previewed"
    assert previewed.record_revision == 2


def test_preview_edit_resets_to_draft_and_requires_preview_again(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    replaced = replace_group_plan_proposal(
        ReplaceGroupPlanProposalRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            strategy="manual",
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="whole",
                    label="Whole Group",
                    student_ids=(
                        "student-1",
                        "student-2",
                        "student-3",
                    ),
                ),
            ),
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    assert replaced.status == "draft"
    assert detail.plan.previewed_provenance is None
    assert detail.plan.updated_provenance is not None
    with pytest.raises(ConcordWorkflowConflictError, match="previewed"):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=replaced.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(6),
        )


def test_approval_requires_resolved_students_and_creates_no_groups(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision)
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="every roster student",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=previewed.summary.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )


def test_happy_path_approval_freezes_proposal_without_applying(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
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
        clock=lambda: _clock(5),
    )
    assert approved.status == "approved"
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    assert detail.plan.approved_provenance is not None
    assert detail.plan.applied_provenance is None
    assert list_record_revisions(
        root,
        approved.commit.work,
        "group_plan",
        "plan-1",
    ) == (1, 2, 3)

    from concord.storage import load_current_record_graph

    loaded = load_current_record_graph(root, approved.commit.work)
    assert loaded.graph.groups == ()
    assert loaded.graph.memberships == ()

    with pytest.raises(ConcordWorkflowConflictError, match="draft or previewed"):
        replace_group_plan_proposal(
            ReplaceGroupPlanProposalRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                strategy="manual",
                proposed_groups=_all_assigned_groups(),
                expected_snapshot_revision=approved.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(6),
        )


def test_roster_drift_blocks_preview_and_approval(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    write_class_roster(
        root,
        _roster(
            "student-1",
            "student-2",
            "student-3",
            "student-4",
        ),
        overwrite=True,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="roster changed"):
        preview_group_plan(
            PreviewGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(4),
        )

    root2, revision2 = _workspace(tmp_path / "second")
    created2 = _create(root2, revision2, groups=_all_assigned_groups())
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created2.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root2,
        clock=lambda: _clock(4),
    )
    write_class_roster(
        root2,
        _roster(
            "student-1",
            "student-2",
            "student-3",
            "student-4",
        ),
        overwrite=True,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="roster changed"):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=previewed.summary.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root2,
            clock=lambda: _clock(5),
        )


def test_unrelated_work_change_after_preview_requires_new_preview(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    group = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="unrelated-group",
            label="Unrelated Group",
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="changed after GroupPlan preview",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=group.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(6),
        )


@pytest.mark.parametrize("cancel_from", ["draft", "previewed", "approved"])
def test_cancellation_is_terminal_and_preserves_history(
    tmp_path: Path,
    cancel_from: str,
) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    current_revision = created.commit.snapshot_revision
    if cancel_from in {"previewed", "approved"}:
        previewed = preview_group_plan(
            PreviewGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=current_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(4),
        )
        current_revision = previewed.summary.snapshot_revision
    if cancel_from == "approved":
        approved = approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=current_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )
        current_revision = approved.commit.snapshot_revision

    cancelled = cancel_group_plan(
        CancelGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=current_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    assert cancelled.status == "cancelled"
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-1",
        workspace_root=root,
    )
    assert detail.plan.cancelled_provenance is not None
    with pytest.raises(ConcordWorkflowConflictError):
        preview_group_plan(
            PreviewGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=cancelled.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(7),
        )


def test_public_workflow_has_no_generic_applied_transition() -> None:
    import concord.workflows as workflows

    assert not hasattr(workflows, "apply_group_plan")
    assert not hasattr(workflows, "mark_group_plan_applied")
    assert not hasattr(workflows, "set_group_plan_status")


def test_group_plan_summary_is_privacy_minimized() -> None:
    from dataclasses import fields

    from concord.workflows import GroupPlanSummary

    names = {field.name for field in fields(GroupPlanSummary)}
    assert "student_ids" not in names
    assert "roster_student_ids" not in names
    assert "proposed_groups" not in names
    assert "source_signal_set_id" not in names
    assert "source_signal_set_digest" not in names
    assert "source_signal_dimension_id" not in names


def test_approval_rejects_a_stale_expected_snapshot(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    created = _create(root, revision, groups=_all_assigned_groups())
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert previewed.summary.snapshot_revision > created.commit.snapshot_revision
    with pytest.raises(ConcordWorkflowConflictError, match="expected snapshot"):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-1",
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(5),
        )
