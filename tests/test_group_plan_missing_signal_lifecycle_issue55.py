from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_storage import write_grouping_signal
from pds_core.grouping_signals import (
    GroupingSignalDimension,
    GroupingSignalSet,
    GroupingSignalSource,
    GroupingSignalStudentBand,
)
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.storage import commit_record_batch, load_current_record_graph
from concord.workflows import (
    ApproveGroupPlanRequest,
    CreateActivityContextRequest,
    CreateManualGroupPlanRequest,
    CreateSignalGroupPlanRequest,
    EditPlannedGroupRequest,
    PlaceStudentInPlanRequest,
    PreviewGroupPlanRequest,
    RefreshGroupPlanRosterRequest,
    SetMissingSignalDispositionRequest,
    UnassignStudentFromPlanRequest,
    WorkflowActor,
    approve_group_plan,
    create_activity_context,
    create_manual_group_plan,
    create_signal_group_plan,
    edit_planned_group,
    place_student_in_plan,
    preview_group_plan,
    refresh_group_plan_roster,
    set_missing_signal_disposition,
    show_group_plan,
    unassign_student_from_plan,
)
from concord.workflows._collaboration import work_ref
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 18, 0, tzinfo=timezone.utc)


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


def _workspace(
    tmp_path: Path,
    *student_ids: str,
    name: str = "workspace",
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
            title="Synthetic Signal Planning Activity",
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
            snapshot_id="snapshot-1",
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


def _partial_plan(
    tmp_path: Path,
    *,
    name: str = "partial",
) -> tuple[Path, int]:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
        "student-4",
        name=name,
    )
    signal = _signal((("student-1", 4), ("student-2", 1)))
    write_grouping_signal(root, signal)
    created = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            strategy="mixed_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=2,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    return root, created.mutation.commit.snapshot_revision


def _detail(root: Path):
    return show_group_plan(
        "class-1",
        "activity-1",
        "signal-plan",
        workspace_root=root,
    )


def _preview(root: Path) -> int:
    detail = _detail(root)
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=_actor("teacher-preview"),
        ),
        workspace_root=root,
        clock=lambda: _clock(8),
    )
    return previewed.summary.snapshot_revision


def _set_disposition(
    root: Path,
    disposition: str,
    *,
    seed: str | None = None,
) -> int:
    detail = _detail(root)
    result = set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            disposition=disposition,
            random_seed=seed,
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=_actor(f"teacher-{disposition}"),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    return result.mutation.commit.snapshot_revision


def test_ordinary_edit_preserves_missing_signal_disposition(tmp_path: Path) -> None:
    root, _ = _partial_plan(tmp_path)
    _set_disposition(root, "leave_unassigned")
    before = _detail(root)

    result = edit_planned_group(
        EditPlannedGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            planned_group_key="mixed-1",
            label="Teacher Label",
            expected_snapshot_revision=before.summary.snapshot_revision,
            actor=_actor("teacher-editor"),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )

    after = result.detail.plan
    assert after.status == "draft"
    assert after.missing_signal_disposition == "leave_unassigned"
    assert after.missing_signal_random_seed is None
    assert (
        after.missing_signal_disposition_provenance
        == before.plan.missing_signal_disposition_provenance
    )
    assert after.source_signal_set_id == before.plan.source_signal_set_id
    assert after.source_signal_set_digest == before.plan.source_signal_set_digest
    assert after.source_signal_dimension_id == before.plan.source_signal_dimension_id


def test_roster_refresh_clears_disposition_but_preserves_signal_binding(
    tmp_path: Path,
) -> None:
    root, _ = _partial_plan(tmp_path)
    _set_disposition(root, "leave_unassigned")
    before = _detail(root)

    write_class_roster(
        root,
        _roster(
            "student-1",
            "student-2",
            "student-3",
            "student-4",
            "student-5",
        ),
        overwrite=True,
    )
    result = refresh_group_plan_roster(
        RefreshGroupPlanRosterRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=before.summary.snapshot_revision,
            actor=_actor("teacher-refresh"),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )

    after = result.detail.plan
    assert after.status == "draft"
    assert after.missing_signal_disposition is None
    assert after.missing_signal_random_seed is None
    assert after.missing_signal_disposition_provenance is None
    assert after.source_signal_set_id == before.plan.source_signal_set_id
    assert after.source_signal_set_digest == before.plan.source_signal_set_digest
    assert after.source_signal_dimension_id == before.plan.source_signal_dimension_id
    assert "student-5" in after.unresolved_student_ids


def test_missing_signal_plan_without_disposition_cannot_be_approved(
    tmp_path: Path,
) -> None:
    root, _ = _partial_plan(tmp_path)
    revision = _preview(root)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="explicit missing-signal disposition",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                expected_snapshot_revision=revision,
                actor=_actor("teacher-approve"),
            ),
            workspace_root=root,
        )


def test_manual_disposition_approves_only_after_full_resolution(
    tmp_path: Path,
) -> None:
    root, _ = _partial_plan(tmp_path)
    for student_id, group_key in (
        ("student-3", "mixed-1"),
        ("student-4", "mixed-2"),
    ):
        detail = _detail(root)
        place_student_in_plan(
            PlaceStudentInPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                student_id=student_id,
                planned_group_key=group_key,
                expected_snapshot_revision=detail.summary.snapshot_revision,
                actor=_actor("teacher-place"),
            ),
            workspace_root=root,
        )
    _set_disposition(root, "manual")
    revision = _preview(root)
    result = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=revision,
            actor=_actor("teacher-approve"),
        ),
        workspace_root=root,
        clock=lambda: _clock(9),
    )
    assert result.status == "approved"
    assert _detail(root).plan.unresolved_student_ids == ()


def test_random_disposition_approves_when_every_student_is_resolved(
    tmp_path: Path,
) -> None:
    root, _ = _partial_plan(tmp_path)
    _set_disposition(root, "random", seed="approval-seed")
    revision = _preview(root)
    result = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=revision,
            actor=_actor("teacher-approve"),
        ),
        workspace_root=root,
    )
    approved = _detail(root).plan
    assert result.status == "approved"
    assert approved.missing_signal_disposition == "random"
    assert approved.missing_signal_random_seed == "approval-seed"
    assert approved.unresolved_student_ids == ()


def test_leave_unassigned_approves_exact_missing_population_without_groups(
    tmp_path: Path,
) -> None:
    root, _ = _partial_plan(tmp_path)
    _set_disposition(root, "leave_unassigned")
    revision = _preview(root)
    result = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=revision,
            actor=_actor("teacher-approve"),
        ),
        workspace_root=root,
    )
    approved = _detail(root).plan
    assert result.status == "approved"
    assert approved.unresolved_student_ids == ("student-3", "student-4")

    graph = load_current_record_graph(
        root,
        work_ref("class-1", "activity-1"),
    ).graph
    assert graph.groups == ()
    assert graph.memberships == ()


def test_leave_unassigned_rejects_extra_represented_unresolved_student(
    tmp_path: Path,
) -> None:
    root, _ = _partial_plan(tmp_path)
    _set_disposition(root, "leave_unassigned")
    detail = _detail(root)
    unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            student_id="student-1",
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=_actor("teacher-unassign"),
        ),
        workspace_root=root,
    )
    revision = _preview(root)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="exactly equal",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                expected_snapshot_revision=revision,
                actor=_actor("teacher-approve"),
            ),
            workspace_root=root,
        )


def test_complete_coverage_signal_plan_needs_no_disposition(tmp_path: Path) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        name="complete",
    )
    signal = _signal(
        (("student-1", 1), ("student-2", 2)),
        signal_set_id="signal-complete",
    )
    write_grouping_signal(root, signal)
    created = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            strategy="similar_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=1,
        ),
        workspace_root=root,
    )
    assert created.unresolved_student_count == 0
    revision = _preview(root)
    result = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=revision,
            actor=_actor("teacher-approve"),
        ),
        workspace_root=root,
    )
    assert result.status == "approved"
    assert _detail(root).plan.missing_signal_disposition is None


def test_non_signal_unresolved_approval_rule_is_unchanged(tmp_path: Path) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        name="manual",
    )
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="manual-plan",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="manual-plan",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor("teacher-preview"),
        ),
        workspace_root=root,
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="every roster student",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="manual-plan",
                expected_snapshot_revision=previewed.summary.snapshot_revision,
                actor=_actor("teacher-approve"),
            ),
            workspace_root=root,
        )


def test_approval_revalidates_exact_core_digest(tmp_path: Path) -> None:
    root, _ = _partial_plan(tmp_path)
    _set_disposition(root, "leave_unassigned")
    detail = _detail(root)
    corrupted = replace(
        detail.plan,
        source_signal_set_digest="c" * 64,
    )
    committed = commit_record_batch(
        root,
        work_ref("class-1", "activity-1"),
        (corrupted,),
        expected_snapshot_revision=detail.summary.snapshot_revision,
    )
    previewed = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            expected_snapshot_revision=committed.snapshot_revision,
            actor=_actor("teacher-preview-2"),
        ),
        workspace_root=root,
    )
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="canonical digest",
    ):
        approve_group_plan(
            ApproveGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                expected_snapshot_revision=previewed.summary.snapshot_revision,
                actor=_actor("teacher-approve"),
            ),
            workspace_root=root,
        )
