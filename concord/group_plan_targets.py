"""Shared pure target arithmetic for generated Concord GroupPlans."""

from __future__ import annotations


class GroupPlanTargetError(ValueError):
    """Raised when a generated GroupPlan target is invalid."""


def _positive_int(value: int | None, field_name: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GroupPlanTargetError(f"{field_name} must be a positive integer.")
    return value


def resolve_group_count(
    roster_size: int,
    *,
    target_group_size: int | None,
    target_group_count: int | None,
) -> int:
    """Resolve an exact generated-plan group count against the full roster."""

    if (
        isinstance(roster_size, bool)
        or not isinstance(roster_size, int)
        or roster_size <= 0
    ):
        raise GroupPlanTargetError("roster_size must be a positive integer.")

    size = _positive_int(target_group_size, "target_group_size")
    count = _positive_int(target_group_count, "target_group_count")
    if (size is None) == (count is None):
        raise GroupPlanTargetError(
            "exactly one of target_group_size or target_group_count is required."
        )
    if count is not None:
        if count > roster_size:
            raise GroupPlanTargetError(
                "target_group_count must not exceed the current roster size."
            )
        return count

    assert size is not None
    return (roster_size + size - 1) // size


def balanced_group_sizes(item_count: int, group_count: int) -> tuple[int, ...]:
    """Return deterministic left-heavy balanced sizes, permitting empty groups."""

    if (
        isinstance(item_count, bool)
        or not isinstance(item_count, int)
        or item_count < 0
    ):
        raise GroupPlanTargetError("item_count must be a nonnegative integer.")
    if (
        isinstance(group_count, bool)
        or not isinstance(group_count, int)
        or group_count <= 0
    ):
        raise GroupPlanTargetError("group_count must be a positive integer.")

    base_size, extra = divmod(item_count, group_count)
    return tuple(
        base_size + (1 if index < extra else 0)
        for index in range(group_count)
    )
