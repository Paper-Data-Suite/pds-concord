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

from concord.storage import load_current_record_graph
from concord.workflows import (
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    EditPlannedGroupRequest,
    PlaceStudentInPlanRequest,
    PreviewGroupPlanRequest,
    RefreshGroupPlanRosterRequest,
    WorkflowActor,
    approve_group_plan,
    create_activity_context,
    edit_planned_group,
    place_student_in_plan,
    preview_group_plan,
    refresh_group_plan_roster,
    show_group_plan,
)
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.group_plan_signal import (
    CreateSignalGroupPlanRequest,
    create_signal_group_plan,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 19, 0, tzinfo=timezone.utc)


def _actor(actor_id: str = "teacher-1") -> WorkflowActor:
    return WorkflowActor(
        actor_id=actor_id,
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


def _workspace(tmp_path: Path, *student_ids: str) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(root, _roster(*student_ids))
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Signal Plan Lifecycle",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    return root, created.commit.snapshot_revision


def _signal(
    bands: tuple[tuple[str, int], ...],
    *,
    signal_set_id: str = "signal-1",
) -> GroupingSignalSet:
    dimension_id = "collaboration-context"
    return GroupingSignalSet(
        schema_version="1",
        record_type="grouping_signal_set",
        signal_set_id=signal_set_id,
        class_id="class-1",
        created_at=_clock(2),
        source=GroupingSignalSource(
            kind="module_generated",
            module_id="synthetic_module",
            snapshot_id=f"snapshot-{signal_set_id}",
            snapshot_digest_algorithm="sha256",
            snapshot_digest="b" * 64,
        ),
        dimensions=(
            GroupingSignalDimension(
                dimension_id=dimension_id,
                band_count=4,
            ),
        ),
        student_bands=tuple(
            GroupingSignalStudentBand(
                student_id=student_id,
                dimension_id=dimension_id,
                band=band,
            )
            for student_id, band in bands
        ),
    )


def _create_signal_plan(
    root: Path,
    revision: int,
    signal: GroupingSignalSet,
    *,
    strategy: str = "similar_signal",
    group_plan_id: str = "signal-plan",
    target_group_count: int = 2,
):
    write_grouping_signal(root, signal)
    return create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id=group_plan_id,
            strategy=strategy,
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=target_group_count,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )


def _locations(detail) -> dict[str, str]:
    return {
        student_id: group.planned_group_key
        for group in detail.plan.proposed_groups
        for student_id in group.student_ids
    }


def _assert_signal_origin(detail, signal: GroupingSignalSet) -> None:
    assert detail.plan.source_signal_set_id == signal.signal_set_id
    assert detail.plan.source_signal_set_digest == calculate_grouping_signal_digest(
        signal
    )
    assert detail.plan.source_signal_dimension_id == "collaboration-context"
    assert detail.plan.seed is None


def test_previewed_signal_plan_edit_returns_to_draft_and_preserves_origin(
    tmp_path: Path,
) -> None:
    students = tuple(f"student-{index}" for index in range(1, 7))
    root, revision = _workspace(tmp_path, *students)
    signal = _signal(
        (
            ("student-1", 1),
            ("student-2", 1),
            ("student-3", 2),
            ("student-4", 2),
            ("student-5", 3),
            ("student-6", 4),
        )
    )
    created = _create_signal_plan(root, revision, signal)
    before = show_group_plan(
        "class-1", "activity-1", "signal-plan", workspace_root=root
    )
    before_locations = _locations(before)

    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    edited = edit_planned_group(
        EditPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            planned_group_key=previewed.plan.proposed_groups[0].planned_group_key,
            label="Teacher Table",
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )

    assert edited.detail.plan.status == "draft"
    assert edited.detail.plan.strategy == "similar_signal"
    assert edited.detail.plan.target_group_count == 2
    assert edited.detail.plan.proposed_groups[0].label == "Teacher Table"
    assert _locations(edited.detail) == before_locations
    _assert_signal_origin(edited.detail, signal)


def test_existing_manual_editor_can_place_unresolved_student_without_losing_origin(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
        "student-4",
    )
    signal = _signal(
        (("student-1", 4), ("student-2", 2), ("student-3", 1))
    )
    created = _create_signal_plan(
        root,
        revision,
        signal,
        strategy="mixed_signal",
    )
    before = show_group_plan(
        "class-1", "activity-1", "signal-plan", workspace_root=root
    )
    assert before.plan.unresolved_student_ids == ("student-4",)

    placed = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            student_id="student-4",
            planned_group_key=before.plan.proposed_groups[0].planned_group_key,
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )

    assert placed.detail.plan.strategy == "mixed_signal"
    assert placed.detail.plan.target_group_count == 2
    assert placed.detail.plan.unresolved_student_ids == ()
    assert "student-4" in placed.detail.plan.proposed_groups[0].student_ids
    _assert_signal_origin(placed.detail, signal)


def test_refresh_preserves_survivor_placements_empty_groups_and_exact_signal_binding(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
        "student-4",
        "student-5",
    )
    signal = _signal(
        (("student-1", 1), ("student-2", 2), ("student-3", 4))
    )
    created = _create_signal_plan(
        root,
        revision,
        signal,
        strategy="mixed_signal",
        target_group_count=4,
    )
    before = show_group_plan(
        "class-1", "activity-1", "signal-plan", workspace_root=root
    )
    assert tuple(len(group.student_ids) for group in before.plan.proposed_groups) == (
        1,
        1,
        1,
        0,
    )
    survivor_locations = {
        student_id: group_key
        for student_id, group_key in _locations(before).items()
        if student_id != "student-2"
    }
    original_keys = tuple(
        group.planned_group_key for group in before.plan.proposed_groups
    )

    newer_signal = _signal(
        (("student-1", 4), ("student-3", 1), ("student-6", 2)),
        signal_set_id="signal-2",
    )
    write_grouping_signal(root, newer_signal)
    write_class_roster(
        root,
        _roster("student-1", "student-3", "student-4", "student-5", "student-6"),
        overwrite=True,
    )

    refreshed = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )

    assert refreshed.detail.plan.status == "draft"
    assert refreshed.detail.plan.strategy == "mixed_signal"
    assert refreshed.detail.plan.target_group_count == 4
    assert tuple(
        group.planned_group_key for group in refreshed.detail.plan.proposed_groups
    ) == original_keys
    assert _locations(refreshed.detail) == survivor_locations
    assert refreshed.detail.plan.unresolved_student_ids == (
        "student-4",
        "student-5",
        "student-6",
    )
    assert any(not group.student_ids for group in refreshed.detail.plan.proposed_groups)
    _assert_signal_origin(refreshed.detail, signal)
    assert refreshed.detail.plan.source_signal_set_id != newer_signal.signal_set_id


def test_refresh_of_previewed_signal_plan_returns_to_draft(tmp_path: Path) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
    )
    signal = _signal(
        (("student-1", 1), ("student-2", 2), ("student-3", 3))
    )
    created = _create_signal_plan(root, revision, signal)
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    write_class_roster(
        root,
        _roster("student-1", "student-2", "student-3", "student-4"),
        overwrite=True,
    )

    refreshed = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    assert refreshed.detail.plan.status == "draft"
    assert refreshed.detail.plan.previewed_provenance is None
    assert refreshed.detail.plan.unresolved_student_ids == ("student-4",)
    _assert_signal_origin(refreshed.detail, signal)


def test_unresolved_signal_plan_may_preview_but_cannot_be_approved(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
    )
    signal = _signal((("student-1", 1), ("student-2", 4)))
    created = _create_signal_plan(root, revision, signal)

    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert previewed.plan.status == "previewed"
    assert previewed.plan.unresolved_student_ids == ("student-3",)
    _assert_signal_origin(previewed, signal)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="explicit missing-signal disposition",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                expected_snapshot_revision=previewed.summary.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = show_group_plan(
        "class-1", "activity-1", "signal-plan", workspace_root=root
    )
    assert after.plan.status == "previewed"
    _assert_signal_origin(after, signal)


def test_resolved_signal_plan_approval_preserves_binding_and_creates_no_groups(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
        "student-4",
    )
    signal = _signal(
        (
            ("student-1", 1),
            ("student-2", 2),
            ("student-3", 3),
            ("student-4", 4),
        )
    )
    created = _create_signal_plan(
        root,
        revision,
        signal,
        strategy="mixed_signal",
    )
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=previewed.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    detail = show_group_plan(
        "class-1", "activity-1", "signal-plan", workspace_root=root
    )

    assert approved.status == "approved"
    assert detail.plan.status == "approved"
    assert detail.plan.strategy == "mixed_signal"
    _assert_signal_origin(detail, signal)

    graph = load_current_record_graph(root, approved.commit.work).graph
    assert len(graph.group_plans) == 1
    assert graph.groups == ()
    assert graph.memberships == ()
    assert graph.role_assignments == ()
    assert graph.responsibility_assignments == ()
    assert graph.artifact_instances == ()
    assert graph.artifact_pages == ()
    assert graph.artifact_reviews == ()
    assert graph.moderation_records == ()
    assert graph.score_records == ()
