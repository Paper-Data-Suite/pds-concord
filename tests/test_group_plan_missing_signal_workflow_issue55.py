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
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.storage import commit_record_batch, load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupPlanRequest,
    CreateSignalGroupPlanRequest,
    PlaceStudentInPlanRequest,
    SetMissingSignalDispositionRequest,
    UnassignStudentFromPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_group_plan,
    create_signal_group_plan,
    inspect_group_plan_missing_signal,
    place_student_in_plan,
    set_missing_signal_disposition,
    unassign_student_from_plan,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan import show_group_plan


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


def _workspace(
    tmp_path: Path,
    *student_ids: str,
    name: str = "workspace",
) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / name)
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=_clock(1),
        ),
    )
    write_class_roster(root, _roster(*student_ids))
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Missing-Signal Activity",
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
    name: str = "workspace",
) -> tuple[Path, int, GroupingSignalSet]:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        "student-3",
        "student-4",
        "student-5",
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
    return root, created.mutation.commit.snapshot_revision, signal


def _detail(root: Path):
    return show_group_plan(
        "class-1",
        "activity-1",
        "signal-plan",
        workspace_root=root,
    )


def test_inspection_uses_exact_bound_signal_and_core_missing_findings(
    tmp_path: Path,
) -> None:
    root, _, signal = _partial_plan(tmp_path)
    inspection = inspect_group_plan_missing_signal(
        "class-1",
        "activity-1",
        "signal-plan",
        workspace_root=root,
    )
    assert inspection.signal_set_id == signal.signal_set_id
    assert inspection.signal_set_digest == calculate_grouping_signal_digest(signal)
    assert inspection.signal_set_digest != signal.source.snapshot_digest
    assert inspection.dimension_id == "collaboration-context"
    assert inspection.missing_student_ids == (
        "student-3",
        "student-4",
        "student-5",
    )
    assert inspection.missing_assigned_student_ids == ()
    assert inspection.missing_unresolved_student_ids == inspection.missing_student_ids


def test_leave_unassigned_records_explicit_provenance_without_group_side_effects(
    tmp_path: Path,
) -> None:
    root, revision, _ = _partial_plan(tmp_path)
    result = set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            disposition="leave_unassigned",
            expected_snapshot_revision=revision,
            actor=_actor("teacher-leave"),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    detail = _detail(root)
    assert result.disposition == "leave_unassigned"
    assert result.missing_student_count == 3
    assert result.unresolved_student_count == 3
    assert detail.plan.status == "draft"
    assert detail.plan.unresolved_student_ids == (
        "student-3",
        "student-4",
        "student-5",
    )
    assert detail.plan.missing_signal_disposition == "leave_unassigned"
    assert detail.plan.missing_signal_random_seed is None
    provenance = detail.plan.missing_signal_disposition_provenance
    assert provenance is not None
    assert provenance.actor.actor_id == "teacher-leave"

    graph = load_current_record_graph(
        root,
        ModuleWorkRef(
            module_id="concord",
            class_id="class-1",
            work_id="activity-1",
        ),
    ).graph
    assert graph.groups == ()
    assert graph.memberships == ()


def test_manual_disposition_requires_explicit_placement_then_confirmation(
    tmp_path: Path,
) -> None:
    root, revision, _ = _partial_plan(tmp_path)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="placed first",
    ):
        set_missing_signal_disposition(
            SetMissingSignalDispositionRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                disposition="manual",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    for student_id, key in (
        ("student-3", "mixed-1"),
        ("student-4", "mixed-2"),
        ("student-5", "mixed-1"),
    ):
        edited = place_student_in_plan(
            PlaceStudentInPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                student_id=student_id,
                planned_group_key=key,
                expected_snapshot_revision=_detail(root).summary.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
        assert edited.changed

    before = _detail(root)
    assert before.plan.unresolved_student_ids == ()
    assert before.plan.missing_signal_disposition is None

    set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            disposition="manual",
            expected_snapshot_revision=before.summary.snapshot_revision,
            actor=_actor("teacher-manual"),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    after = _detail(root)
    assert after.plan.missing_signal_disposition == "manual"
    assert after.plan.missing_signal_random_seed is None
    assert after.plan.strategy == "mixed_signal"
    assert after.plan.unresolved_student_ids == ()


def test_random_disposition_is_deterministic_and_uses_separate_seed(
    tmp_path: Path,
) -> None:
    root, revision, _ = _partial_plan(tmp_path)
    result = set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            disposition="random",
            random_seed="missing-seed",
            expected_snapshot_revision=revision,
            actor=_actor("teacher-random"),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    detail = _detail(root)
    assert result.group_sizes == (3, 2)
    assert result.unresolved_student_count == 0
    assert detail.plan.strategy == "mixed_signal"
    assert detail.plan.seed is None
    assert detail.plan.missing_signal_disposition == "random"
    assert detail.plan.missing_signal_random_seed == "missing-seed"
    assert detail.plan.proposed_groups[0].student_ids == (
        "student-1",
        "student-3",
        "student-5",
    )
    assert detail.plan.proposed_groups[1].student_ids == (
        "student-2",
        "student-4",
    )


def test_random_rejects_missing_student_that_teacher_already_placed(
    tmp_path: Path,
) -> None:
    root, _, _ = _partial_plan(tmp_path)
    detail = _detail(root)
    place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            student_id="student-3",
            planned_group_key="mixed-1",
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    detail = _detail(root)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="unresolved first",
    ):
        set_missing_signal_disposition(
            SetMissingSignalDispositionRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                disposition="random",
                random_seed="seed",
                expected_snapshot_revision=detail.summary.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_random_places_only_missing_and_leaves_represented_unresolved(
    tmp_path: Path,
) -> None:
    root, _, _ = _partial_plan(tmp_path)
    detail = _detail(root)
    unassign_student_from_plan(
        UnassignStudentFromPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            student_id="student-1",
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    detail = _detail(root)
    set_missing_signal_disposition(
        SetMissingSignalDispositionRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            disposition="random",
            random_seed="seed",
            expected_snapshot_revision=detail.summary.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    after = _detail(root)
    assert after.plan.unresolved_student_ids == ("student-1",)
    assigned = {
        student_id
        for group in after.plan.proposed_groups
        for student_id in group.student_ids
    }
    assert {"student-3", "student-4", "student-5"} <= assigned
    assert "student-1" not in assigned


def test_disposition_rejects_stale_snapshot_and_zero_missing_population(
    tmp_path: Path,
) -> None:
    root, revision, _ = _partial_plan(tmp_path)
    with pytest.raises(ConcordWorkflowConflictError, match="expected snapshot"):
        set_missing_signal_disposition(
            SetMissingSignalDispositionRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                disposition="leave_unassigned",
                expected_snapshot_revision=revision - 1,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    full_root, initial = _workspace(
        tmp_path,
        "student-1",
        "student-2",
        name="complete",
    )
    full_signal = _signal(
        (("student-1", 1), ("student-2", 2)),
        signal_set_id="signal-complete",
    )
    write_grouping_signal(full_root, full_signal)
    created = create_signal_group_plan(
        CreateSignalGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            strategy="similar_signal",
            signal_set_id=full_signal.signal_set_id,
            dimension_id="collaboration-context",
            expected_snapshot_revision=initial,
            actor=_actor(),
            target_group_count=1,
        ),
        workspace_root=full_root,
    )
    with pytest.raises(ConcordWorkflowValidationError, match="no missing"):
        set_missing_signal_disposition(
            SetMissingSignalDispositionRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                disposition="leave_unassigned",
                expected_snapshot_revision=created.mutation.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=full_root,
        )


def test_exact_core_digest_mismatch_fails_closed(tmp_path: Path) -> None:
    root, _, _ = _partial_plan(tmp_path)
    detail = _detail(root)
    corrupted = replace(
        detail.plan,
        source_signal_set_digest="c" * 64,
    )
    commit_record_batch(
        root,
        ModuleWorkRef(
            module_id="concord",
            class_id="class-1",
            work_id="activity-1",
        ),
        (corrupted,),
        expected_snapshot_revision=detail.summary.snapshot_revision,
    )
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="canonical digest",
    ):
        inspect_group_plan_missing_signal(
            "class-1",
            "activity-1",
            "signal-plan",
            workspace_root=root,
        )


def test_core_diagnostic_error_fails_through_exact_selection(tmp_path: Path) -> None:
    root, revision = _workspace(
        tmp_path,
        "student-1",
        "student-2",
    )
    invalid_signal = _signal(
        (("student-1", 1), ("student-999", 2)),
        signal_set_id="signal-invalid",
    )
    write_grouping_signal(root, invalid_signal)
    digest = calculate_grouping_signal_digest(invalid_signal)
    created = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="signal-plan",
            strategy="similar_signal",
            expected_snapshot_revision=revision,
            actor=_actor(),
            target_group_count=1,
            source_signal_set_id=invalid_signal.signal_set_id,
            source_signal_set_digest=digest,
            source_signal_dimension_id="collaboration-context",
        ),
        workspace_root=root,
    )
    assert created.status == "draft"
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="unknown_student",
    ):
        inspect_group_plan_missing_signal(
            "class-1",
            "activity-1",
            "signal-plan",
            workspace_root=root,
        )


@pytest.mark.parametrize(
    ("disposition", "seed", "message"),
    (
        ("bogus", None, "disposition must be"),
        ("manual", "seed", "allowed only"),
        ("leave_unassigned", "seed", "allowed only"),
        ("random", None, "explicit seed"),
    ),
)
def test_disposition_input_contract(
    tmp_path: Path,
    disposition: str,
    seed: str | None,
    message: str,
) -> None:
    root, revision, _ = _partial_plan(tmp_path)
    with pytest.raises(ConcordWorkflowValidationError, match=message):
        set_missing_signal_disposition(
            SetMissingSignalDispositionRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="signal-plan",
                disposition=disposition,
                random_seed=seed,
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
