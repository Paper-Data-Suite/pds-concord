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

import concord.group_plan_random as random_planning
from concord.group_plan_random import (
    RandomGroupPlanningError,
    deterministic_random_student_order,
    generate_random_group_plan_proposal,
)
from concord.workflows import (
    CreateActivityContextRequest,
    CreateRandomGroupPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_random_group_plan,
    list_group_plans,
    show_group_plan,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group_plan_manual import (
    PlaceStudentInPlanRequest,
    place_student_in_plan,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 15, 0, tzinfo=timezone.utc)


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


def _students(count: int) -> tuple[str, ...]:
    return tuple(f"student-{index}" for index in range(1, count + 1))


def _memberships(proposal) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (group.planned_group_key, group.student_ids)
        for group in proposal.proposed_groups
    )


def test_fixed_seed_fixture_has_exact_v1_membership() -> None:
    proposal = generate_random_group_plan_proposal(
        _students(10),
        seed="seed-7",
        target_group_count=3,
    )
    assert proposal.group_sizes == (4, 3, 3)
    assert _memberships(proposal) == (
        ("random-1", ("student-1", "student-2", "student-3", "student-6")),
        ("random-2", ("student-10", "student-4", "student-9")),
        ("random-3", ("student-5", "student-7", "student-8")),
    )
    assert tuple(group.label for group in proposal.proposed_groups) == (
        "Group 1",
        "Group 2",
        "Group 3",
    )


def test_roster_input_order_does_not_change_proposal() -> None:
    forward = generate_random_group_plan_proposal(
        _students(10),
        seed="same-seed",
        target_group_count=4,
    )
    reversed_roster = generate_random_group_plan_proposal(
        tuple(reversed(_students(10))),
        seed="same-seed",
        target_group_count=4,
    )
    assert forward == reversed_roster


def test_rank_collision_uses_exact_student_id_as_tie_breaker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(random_planning, "_rank_digest", lambda seed, student: b"x")
    assert deterministic_random_student_order(
        ("student-3", "student-1", "student-2"),
        "seed",
    ) == ("student-1", "student-2", "student-3")


@pytest.mark.parametrize(
    ("count", "target", "expected_sizes"),
    (
        (10, 3, (4, 3, 3)),
        (10, 4, (3, 3, 2, 2)),
        (7, 7, (1, 1, 1, 1, 1, 1, 1)),
        (7, 1, (7,)),
    ),
)
def test_target_count_balances_exactly(
    count: int,
    target: int,
    expected_sizes: tuple[int, ...],
) -> None:
    proposal = generate_random_group_plan_proposal(
        _students(count),
        seed="balance",
        target_group_count=target,
    )
    assert proposal.group_count == target
    assert proposal.group_sizes == expected_sizes
    assert max(proposal.group_sizes) - min(proposal.group_sizes) <= 1


@pytest.mark.parametrize(
    ("count", "target", "expected_sizes"),
    (
        (10, 4, (4, 3, 3)),
        (8, 3, (3, 3, 2)),
        (7, 1, (1, 1, 1, 1, 1, 1, 1)),
        (7, 7, (7,)),
        (7, 20, (7,)),
    ),
)
def test_target_size_uses_ceiling_count_and_balances(
    count: int,
    target: int,
    expected_sizes: tuple[int, ...],
) -> None:
    proposal = generate_random_group_plan_proposal(
        _students(count),
        seed="balance",
        target_group_size=target,
    )
    assert proposal.group_sizes == expected_sizes
    assert max(proposal.group_sizes) <= target
    assert max(proposal.group_sizes) - min(proposal.group_sizes) <= 1


@pytest.mark.parametrize(
    "kwargs",
    (
        {},
        {"target_group_size": 2, "target_group_count": 2},
        {"target_group_size": 0},
        {"target_group_size": -1},
        {"target_group_count": 0},
        {"target_group_count": 4},
    ),
)
def test_invalid_target_requests_fail(kwargs: dict[str, int]) -> None:
    with pytest.raises(RandomGroupPlanningError):
        generate_random_group_plan_proposal(
            _students(3),
            seed="seed",
            **kwargs,
        )


@pytest.mark.parametrize("seed", ("", " ", " seed", "seed "))
def test_invalid_seed_fails(seed: str) -> None:
    with pytest.raises(RandomGroupPlanningError):
        generate_random_group_plan_proposal(
            _students(3),
            seed=seed,
            target_group_count=2,
        )


def test_empty_and_duplicate_rosters_fail() -> None:
    with pytest.raises(RandomGroupPlanningError, match="nonempty roster"):
        generate_random_group_plan_proposal(
            (),
            seed="seed",
            target_group_count=1,
        )
    with pytest.raises(RandomGroupPlanningError, match="duplicate student IDs"):
        generate_random_group_plan_proposal(
            ("student-1", "student-1"),
            seed="seed",
            target_group_count=1,
        )


def test_workflow_creates_complete_random_draft(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, *_students(10))
    result = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-random",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed-7",
            target_group_count=3,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-random",
        workspace_root=root,
    )
    assert result.group_count == 3
    assert result.assigned_student_count == 10
    assert result.group_sizes == (4, 3, 3)
    assert detail.plan.strategy == "random"
    assert detail.plan.status == "draft"
    assert detail.plan.seed == "seed-7"
    assert detail.plan.target_group_count == 3
    assert detail.plan.target_group_size is None
    assert detail.plan.unresolved_student_ids == ()
    assert detail.plan.source_signal_set_id is None
    assert detail.plan.source_signal_set_digest is None
    assert detail.plan.source_signal_dimension_id is None


def test_size_target_is_preserved_instead_of_derived_count(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, *_students(10))
    create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-random",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed",
            target_group_size=4,
        ),
        workspace_root=root,
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-random",
        workspace_root=root,
    )
    assert detail.plan.target_group_size == 4
    assert detail.plan.target_group_count is None
    assert tuple(len(group.student_ids) for group in detail.plan.proposed_groups) == (
        4,
        3,
        3,
    )


def test_generated_random_plan_remains_manually_editable(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, *_students(6))
    created = create_random_group_plan(
        CreateRandomGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-random",
            expected_snapshot_revision=revision,
            actor=_actor(),
            seed="seed",
            target_group_count=2,
        ),
        workspace_root=root,
    )
    detail = show_group_plan(
        "class-1",
        "activity-1",
        "plan-random",
        workspace_root=root,
    )
    source = detail.plan.proposed_groups[0]
    destination = detail.plan.proposed_groups[1]
    student_id = source.student_ids[0]
    edited = place_student_in_plan(
        PlaceStudentInPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-random",
            student_id=student_id,
            planned_group_key=destination.planned_group_key,
            expected_snapshot_revision=created.mutation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert edited.detail.plan.strategy == "random"
    assert edited.detail.plan.seed == "seed"
    assert edited.detail.plan.target_group_count == 2


def test_workflow_validation_failure_creates_no_plan(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path, *_students(3))
    with pytest.raises(ConcordWorkflowValidationError, match="exactly one"):
        create_random_group_plan(
            CreateRandomGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-random",
                expected_snapshot_revision=revision,
                actor=_actor(),
                seed="seed",
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()


def test_roster_change_between_generation_and_commit_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision = _workspace(tmp_path, *_students(3))
    import concord.workflows.group_plan_random as workflow_module

    original_create = workflow_module.create_group_plan

    def mutate_roster_then_create(request, **kwargs):
        write_class_roster(
            root,
            _roster("student-1", "student-2", "student-3", "student-4"),
            overwrite=True,
        )
        return original_create(request, **kwargs)

    monkeypatch.setattr(
        workflow_module,
        "create_group_plan",
        mutate_roster_then_create,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="roster changed"):
        create_random_group_plan(
            CreateRandomGroupPlanRequest(
                class_id="class-1",
                activity_id="activity-1",
                group_plan_id="plan-random",
                expected_snapshot_revision=revision,
                actor=_actor(),
                seed="seed",
                target_group_count=2,
            ),
            workspace_root=root,
        )
    assert list_group_plans("class-1", "activity-1", workspace_root=root) == ()
