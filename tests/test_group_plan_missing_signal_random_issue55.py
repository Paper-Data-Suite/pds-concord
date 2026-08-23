from __future__ import annotations

import hashlib

import pytest

from concord.group_plan_missing_signal import (
    MISSING_SIGNAL_RANDOM_DOMAIN,
    MissingSignalRandomizationError,
    distribute_missing_signal_students,
)
from concord.models import PlannedGroup


def _group(
    key: str,
    *student_ids: str,
) -> PlannedGroup:
    return PlannedGroup(
        planned_group_key=key,
        label=key.upper(),
        student_ids=student_ids,
        description=f"metadata-{key}",
    )


def _mapping(result) -> dict[str, tuple[str, ...]]:
    return {
        group.planned_group_key: group.student_ids
        for group in result.proposed_groups
    }


def test_random_contract_uses_exact_domain_rank_and_smallest_group() -> None:
    groups = (
        _group("g-b", "student-2"),
        _group("g-c"),
        _group("g-a", "student-1"),
    )
    result = distribute_missing_signal_students(
        groups,
        ("student-5", "student-3", "student-4"),
        seed="seed-55",
    )

    expected_ranks = {
        student_id: hashlib.sha256(
            MISSING_SIGNAL_RANDOM_DOMAIN.encode("utf-8")
            + b"\0"
            + b"seed-55"
            + b"\0"
            + student_id.encode("utf-8")
        ).hexdigest()
        for student_id in ("student-3", "student-4", "student-5")
    }
    assert expected_ranks == {
        "student-3": (
            "84183d46166065b62507b19c20a63a6e276366e8e5b42019f750fa1d2d7bc3ee"
        ),
        "student-4": (
            "09ba73e79dbb5627e43d5667b8ce112df53069949f1659f08ae75c540d34cae1"
        ),
        "student-5": (
            "d5f958af9db780bb4a0f2f2a1ae89ce48e4380ef9820aaebba5732ff0e7de41c"
        ),
    }
    assert result.placements == (
        ("student-4", "g-c"),
        ("student-3", "g-a"),
        ("student-5", "g-b"),
    )
    assert _mapping(result) == {
        "g-a": ("student-1", "student-3"),
        "g-b": ("student-2", "student-5"),
        "g-c": ("student-4",),
    }


def test_random_membership_is_independent_of_input_orders() -> None:
    a = distribute_missing_signal_students(
        (
            _group("g-b", "student-2"),
            _group("g-c"),
            _group("g-a", "student-1"),
        ),
        ("student-5", "student-3", "student-4"),
        seed="same-seed",
    )
    b = distribute_missing_signal_students(
        (
            _group("g-a", "student-1"),
            _group("g-b", "student-2"),
            _group("g-c"),
        ),
        ("student-4", "student-5", "student-3"),
        seed="same-seed",
    )
    assert _mapping(a) == _mapping(b)
    assert a.placements == b.placements


def test_random_preserves_existing_memberships_and_group_metadata() -> None:
    original = (
        _group("g-1", "student-1", "student-2"),
        _group("g-2"),
    )
    result = distribute_missing_signal_students(
        original,
        ("student-3",),
        seed="seed",
    )
    mapping = _mapping(result)
    assert mapping["g-1"] == ("student-1", "student-2")
    assert mapping["g-2"] == ("student-3",)
    for before, after in zip(original, result.proposed_groups, strict=True):
        assert before.planned_group_key == after.planned_group_key
        assert before.label == after.label
        assert before.description == after.description


@pytest.mark.parametrize("seed", ("", " ", " seed", "seed "))
def test_random_rejects_invalid_seed(seed: str) -> None:
    with pytest.raises(MissingSignalRandomizationError, match="seed"):
        distribute_missing_signal_students(
            (_group("g-1"),),
            ("student-1",),
            seed=seed,
        )


def test_random_rejects_missing_student_already_assigned() -> None:
    with pytest.raises(MissingSignalRandomizationError, match="unresolved"):
        distribute_missing_signal_students(
            (_group("g-1", "student-1"),),
            ("student-1",),
            seed="seed",
        )


def test_random_rejects_no_groups_and_duplicate_missing_ids() -> None:
    with pytest.raises(MissingSignalRandomizationError, match="PlannedGroup"):
        distribute_missing_signal_students(
            (),
            ("student-1",),
            seed="seed",
        )
    with pytest.raises(MissingSignalRandomizationError, match="duplicates"):
        distribute_missing_signal_students(
            (_group("g-1"),),
            ("student-1", "student-1"),
            seed="seed",
        )
