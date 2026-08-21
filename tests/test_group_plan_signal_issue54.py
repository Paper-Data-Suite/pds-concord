from __future__ import annotations

from typing import cast

import pytest

from concord.group_plan_signal import (
    SignalGroupPlanningError,
    generate_mixed_signal_group_plan_proposal,
    generate_similar_signal_group_plan_proposal,
)


def _students(count: int) -> tuple[str, ...]:
    return tuple(f"student-{index}" for index in range(1, count + 1))


def _bands() -> dict[str, int]:
    return {
        "student-1": 1,
        "student-2": 1,
        "student-3": 1,
        "student-4": 2,
        "student-5": 2,
        "student-6": 3,
        "student-7": 3,
        "student-8": 4,
    }


def _memberships(proposal) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (group.planned_group_key, group.student_ids)
        for group in proposal.proposed_groups
    )


def test_similar_signal_has_exact_contiguous_balanced_membership() -> None:
    proposal = generate_similar_signal_group_plan_proposal(
        _students(10),
        _bands(),
        target_group_count=3,
    )

    assert proposal.group_count == 3
    assert proposal.group_sizes == (3, 3, 2)
    assert proposal.assigned_student_count == 8
    assert proposal.unresolved_student_ids == ("student-10", "student-9")
    assert _memberships(proposal) == (
        ("similar-1", ("student-1", "student-2", "student-3")),
        ("similar-2", ("student-4", "student-5", "student-6")),
        ("similar-3", ("student-7", "student-8")),
    )


def test_mixed_signal_has_exact_descending_band_cyclic_membership() -> None:
    proposal = generate_mixed_signal_group_plan_proposal(
        _students(10),
        _bands(),
        target_group_count=3,
    )

    assert proposal.group_count == 3
    assert proposal.group_sizes == (3, 3, 2)
    assert proposal.assigned_student_count == 8
    assert proposal.unresolved_student_ids == ("student-10", "student-9")
    assert _memberships(proposal) == (
        ("mixed-1", ("student-2", "student-4", "student-8")),
        ("mixed-2", ("student-3", "student-5", "student-6")),
        ("mixed-3", ("student-1", "student-7")),
    )


def test_roster_and_mapping_input_order_do_not_change_either_strategy() -> None:
    roster = _students(10)
    bands = _bands()
    reversed_bands = dict(reversed(tuple(bands.items())))

    for planner in (
        generate_similar_signal_group_plan_proposal,
        generate_mixed_signal_group_plan_proposal,
    ):
        forward = planner(roster, bands, target_group_count=3)
        reversed_input = planner(
            tuple(reversed(roster)),
            reversed_bands,
            target_group_count=3,
        )
        assert forward == reversed_input


def test_target_size_resolves_group_count_from_full_roster() -> None:
    proposal = generate_similar_signal_group_plan_proposal(
        _students(10),
        _bands(),
        target_group_size=4,
    )

    assert proposal.group_count == 3
    assert proposal.group_sizes == (3, 3, 2)
    assert max(proposal.group_sizes) <= 4
    assert proposal.unresolved_student_count == 2


def test_matched_less_than_target_count_preserves_empty_groups() -> None:
    proposal = generate_mixed_signal_group_plan_proposal(
        _students(5),
        {"student-1": 2, "student-2": 1},
        target_group_count=4,
    )

    assert proposal.group_count == 4
    assert proposal.group_sizes == (1, 1, 0, 0)
    assert tuple(group.planned_group_key for group in proposal.proposed_groups) == (
        "mixed-1",
        "mixed-2",
        "mixed-3",
        "mixed-4",
    )
    assert proposal.unresolved_student_ids == (
        "student-3",
        "student-4",
        "student-5",
    )


def test_same_band_ties_use_exact_student_id() -> None:
    bands = {
        "student-3": 2,
        "student-1": 2,
        "student-2": 2,
    }
    similar = generate_similar_signal_group_plan_proposal(
        ("student-3", "student-1", "student-2"),
        bands,
        target_group_count=2,
    )
    mixed = generate_mixed_signal_group_plan_proposal(
        ("student-3", "student-1", "student-2"),
        bands,
        target_group_count=2,
    )

    assert _memberships(similar) == (
        ("similar-1", ("student-1", "student-2")),
        ("similar-2", ("student-3",)),
    )
    assert _memberships(mixed) == (
        ("mixed-1", ("student-1", "student-3")),
        ("mixed-2", ("student-2",)),
    )


def test_similar_and_mixed_strategies_are_behaviorally_distinct() -> None:
    similar = generate_similar_signal_group_plan_proposal(
        _students(8),
        _bands(),
        target_group_count=2,
    )
    mixed = generate_mixed_signal_group_plan_proposal(
        _students(8),
        _bands(),
        target_group_count=2,
    )

    assert _memberships(similar) != _memberships(mixed)


@pytest.mark.parametrize(
    "kwargs",
    (
        {},
        {"target_group_size": 2, "target_group_count": 2},
        {"target_group_size": 0},
        {"target_group_count": 0},
        {"target_group_count": 4},
    ),
)
def test_invalid_target_requests_fail(kwargs: dict[str, int]) -> None:
    with pytest.raises(SignalGroupPlanningError):
        generate_similar_signal_group_plan_proposal(
            _students(3),
            {"student-1": 1},
            **kwargs,
        )


def test_non_roster_signal_student_fails_closed() -> None:
    with pytest.raises(SignalGroupPlanningError, match="current-roster student IDs"):
        generate_similar_signal_group_plan_proposal(
            _students(3),
            {"student-1": 1, "student-4": 2},
            target_group_count=2,
        )


@pytest.mark.parametrize("band", (0, -1, True, 1.5))
def test_invalid_band_value_fails(band: object) -> None:
    with pytest.raises(SignalGroupPlanningError, match="positive integer"):
        generate_mixed_signal_group_plan_proposal(
            _students(3),
            {"student-1": cast(int, band)},
            target_group_count=2,
        )


def test_all_missing_is_explicit_and_keeps_full_target_shape() -> None:
    proposal = generate_similar_signal_group_plan_proposal(
        _students(4),
        {},
        target_group_count=3,
    )

    assert proposal.group_sizes == (0, 0, 0)
    assert proposal.assigned_student_count == 0
    assert proposal.unresolved_student_ids == _students(4)
    assert len(proposal.proposed_groups) == 3
