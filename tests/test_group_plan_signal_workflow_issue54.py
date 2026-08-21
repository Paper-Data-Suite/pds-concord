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
    CreateActivityContextRequest,
    CreateSignalGroupPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_signal_group_plan,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan import list_group_plans, show_group_plan


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
    dimension_id: str = "collaboration-context",
) -> GroupingSignalSet:
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


def _memberships(detail) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (group.planned_group_key, group.student_ids)
        for group in detail.plan.proposed_groups
    )


def test_similar_workflow_persists_exact_core_signal_binding(tmp_path: Path) -> None:
    students = tuple(f"student-{index}" for index in range(1, 7))
    root, revision = _workspace(tmp_path, *students)
    signal = _signal(
        (
            ("student-1", 1),
            ("student-2", 1),
            ("student-3", 2),
            ("student-4", 2),
            ("student-5", 3),
            ("student-6", 3),
        )
    )
    write_grouping_signal(root, signal)
    canonical_digest = calculate_grouping_signal_digest(signal)

    result = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="similar-plan",
            strategy="similar_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=2,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "similar-plan",
        workspace_root=root,
    )

    assert result.strategy == "similar_signal"
    assert result.group_count == 2
    assert result.assigned_student_count == 6
    assert result.unresolved_student_count == 0
    assert result.group_sizes == (3, 3)
    assert result.signal_set_digest == canonical_digest
    assert result.signal_set_digest != signal.source.snapshot_digest
    assert detail.plan.status == "draft"
    assert detail.plan.strategy == "similar_signal"
    assert detail.plan.seed is None
    assert detail.plan.source_signal_set_id == signal.signal_set_id
    assert detail.plan.source_signal_set_digest == canonical_digest
    assert detail.plan.source_signal_dimension_id == "collaboration-context"
    assert detail.plan.unresolved_student_ids == ()
    assert _memberships(detail) == (
        ("similar-1", ("student-1", "student-2", "student-3")),
        ("similar-2", ("student-4", "student-5", "student-6")),
    )


def test_partial_mixed_plan_uses_full_roster_target_and_keeps_missing_unresolved(
    tmp_path: Path,
) -> None:
    students = tuple(f"student-{index}" for index in range(1, 6))
    root, revision = _workspace(tmp_path, *students)
    signal = _signal((("student-1", 4), ("student-2", 1)))
    write_grouping_signal(root, signal)

    result = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="mixed-plan",
            strategy="mixed_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_size=2,
        ),
        workspace_root=root,
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "mixed-plan",
        workspace_root=root,
    )

    assert result.group_count == 3
    assert result.group_sizes == (1, 1, 0)
    assert result.assigned_student_count == 2
    assert result.unresolved_student_count == 3
    assert detail.plan.target_group_size == 2
    assert detail.plan.target_group_count is None
    assert detail.plan.unresolved_student_ids == (
        "student-3",
        "student-4",
        "student-5",
    )
    assert tuple(len(group.student_ids) for group in detail.plan.proposed_groups) == (
        1,
        1,
        0,
    )


def test_signal_membership_is_independent_of_actor_clock_and_plan_id(
    tmp_path: Path,
) -> None:
    students = tuple(f"student-{index}" for index in range(1, 7))
    signal = _signal(
        (
            ("student-1", 1),
            ("student-2", 4),
            ("student-3", 2),
            ("student-4", 3),
            ("student-5", 1),
            ("student-6", 4),
        )
    )
    root_a, revision_a = _workspace(tmp_path, *students, name="a")
    root_b, revision_b = _workspace(tmp_path, *students, name="b")
    write_grouping_signal(root_a, signal)
    write_grouping_signal(root_b, signal)

    create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-a",
            strategy="mixed_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision_a,
            actor=_actor("teacher-a"),
            target_group_count=3,
        ),
        workspace_root=root_a,
        clock=lambda: _clock(3),
    )
    create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="different-plan-id",
            strategy="mixed_signal",
            signal_set_id=signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=revision_b,
            actor=_actor("teacher-b"),
            target_group_count=3,
        ),
        workspace_root=root_b,
        clock=lambda: _clock(9),
    )

    a = show_group_plan("class-1", "activity-1", "plan-a", workspace_root=root_a)
    b = show_group_plan(
        "class-1",
        "activity-1",
        "different-plan-id",
        workspace_root=root_b,
    )
    assert _memberships(a) == _memberships(b)


def test_unsupported_strategy_and_unknown_dimension_create_no_plan(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2")
    signal = _signal((("student-1", 1), ("student-2", 2)))
    write_grouping_signal(root, signal)

    with pytest.raises(ConcordWorkflowValidationError, match="strategy"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="bad-strategy",
                strategy="random",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=1,
            ),
            workspace_root=root,
        )

    with pytest.raises(ConcordWorkflowValidationError, match="not available"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="bad-dimension",
                strategy="similar_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="missing-dimension",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=1,
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_core_diagnostic_error_is_rejected_through_selection(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2")
    signal = _signal((("student-1", 1), ("student-999", 2)))
    write_grouping_signal(root, signal)

    with pytest.raises(ConcordWorkflowValidationError, match="unknown_student"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="invalid-signal-plan",
                strategy="similar_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=1,
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_roster_change_during_signal_selection_fails_before_proposal_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2", "student-3")
    signal = _signal((("student-1", 1), ("student-2", 2), ("student-3", 3)))
    write_grouping_signal(root, signal)

    import concord.workflows.group_plan_signal as workflow_module

    original_select = workflow_module.select_grouping_signal_dimension

    def select_then_mutate(*args, **kwargs):
        selection = original_select(*args, **kwargs)
        write_class_roster(
            root,
            _roster("student-1", "student-2", "student-3", "student-4"),
            overwrite=True,
        )
        return selection

    monkeypatch.setattr(
        workflow_module,
        "select_grouping_signal_dimension",
        select_then_mutate,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="while selecting"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="race-plan",
                strategy="similar_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=2,
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_roster_change_between_proposal_and_create_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2", "student-3")
    signal = _signal((("student-1", 1), ("student-2", 2), ("student-3", 3)))
    write_grouping_signal(root, signal)

    import concord.workflows.group_plan_signal as workflow_module

    original_create = workflow_module.create_group_plan

    def mutate_roster_then_create(request, **kwargs):
        write_class_roster(
            root,
            _roster("student-1", "student-2", "student-3", "student-4"),
            overwrite=True,
        )
        return original_create(request, **kwargs)

    monkeypatch.setattr(workflow_module, "create_group_plan", mutate_roster_then_create)
    with pytest.raises(ConcordWorkflowConflictError, match="roster changed"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="race-plan",
                strategy="mixed_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=2,
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_stale_activity_snapshot_creates_no_plan(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2")
    signal = _signal((("student-1", 1), ("student-2", 2)))
    write_grouping_signal(root, signal)

    with pytest.raises(ConcordWorkflowConflictError, match="expected snapshot"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="stale-plan",
                strategy="similar_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision + 1,
                actor=_actor(),
                target_group_count=1,
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_signal_plan_creation_creates_no_canonical_collaboration_state(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2", "student-3")
    signal = _signal((("student-1", 1), ("student-2", 2), ("student-3", 3)))
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
    )

    graph = load_current_record_graph(root, created.mutation.commit.work).graph
    assert len(graph.group_plans) == 1
    assert graph.groups == ()
    assert graph.memberships == ()
    assert graph.role_assignments == ()
    assert graph.responsibility_assignments == ()


def test_preview_roster_precondition_rejects_changed_roster(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2", "student-3")
    signal = _signal(
        (("student-1", 1), ("student-2", 2), ("student-3", 3))
    )
    write_grouping_signal(root, signal)

    with pytest.raises(ConcordWorkflowConflictError, match="since the signal"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="stale-preview-roster",
                strategy="similar_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=2,
                expected_roster_student_ids=("student-1", "student-2"),
            ),
            workspace_root=root,
        )

    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_preview_signal_digest_precondition_rejects_mismatch(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path, "student-1", "student-2", "student-3")
    signal = _signal(
        (
            ("student-1", 1),
            ("student-2", 2),
            ("student-3", 3),
        )
    )
    write_grouping_signal(root, signal)

    with pytest.raises(ConcordWorkflowConflictError, match="signal changed"):
        create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="stale-preview-signal",
                strategy="mixed_signal",
                signal_set_id=signal.signal_set_id,
                dimension_id="collaboration-context",
                expected_snapshot_revision=revision,
                actor=_actor(),
                target_group_count=2,
                expected_roster_student_ids=(
                    "student-1",
                    "student-2",
                    "student-3",
                ),
                expected_signal_set_digest="0" * 64,
            ),
            workspace_root=root,
        )

    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()
