"""Pure deterministic random GroupPlan proposal generation for Concord v0.3."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from pds_core.identifiers import IdentifierValidationError, validate_identifier

from concord.group_plan_targets import (
    GroupPlanTargetError,
    balanced_group_sizes,
    resolve_group_count,
)
from concord.models import PlannedGroup

RANDOM_PLANNING_DOMAIN = "pds-concord:group-plan-random:v1"
_DOMAIN_BYTES = RANDOM_PLANNING_DOMAIN.encode("utf-8") + b"\0"


class RandomGroupPlanningError(ValueError):
    """Raised when deterministic random-planning inputs are invalid."""


@dataclass(frozen=True, slots=True)
class RandomGroupPlanProposal:
    """One complete deterministic planning proposal before persistence."""

    roster_student_ids: tuple[str, ...]
    proposed_groups: tuple[PlannedGroup, ...]
    group_sizes: tuple[int, ...]
    group_count: int

    @property
    def assigned_student_count(self) -> int:
        return len(self.roster_student_ids)


def _require_seed(seed: str) -> str:
    if not isinstance(seed, str) or not seed.strip():
        raise RandomGroupPlanningError("seed must be a nonempty string.")
    if seed != seed.strip():
        raise RandomGroupPlanningError(
            "seed must not contain leading or trailing whitespace."
        )
    return seed


def _canonical_roster(student_ids: tuple[str, ...]) -> tuple[str, ...]:
    if not student_ids:
        raise RandomGroupPlanningError("random planning requires a nonempty roster.")
    validated: list[str] = []
    for student_id in student_ids:
        try:
            validated.append(validate_identifier(student_id, "student_id"))
        except (IdentifierValidationError, TypeError, ValueError) as error:
            raise RandomGroupPlanningError(str(error)) from error
    if len(set(validated)) != len(validated):
        raise RandomGroupPlanningError(
            "random planning roster must not contain duplicate student IDs."
        )
    return tuple(sorted(validated))


def _rank_digest(seed: str, student_id: str) -> bytes:
    payload = (
        _DOMAIN_BYTES
        + seed.encode("utf-8")
        + b"\0"
        + student_id.encode("utf-8")
    )
    return sha256(payload).digest()


def deterministic_random_student_order(
    student_ids: tuple[str, ...],
    seed: str,
) -> tuple[str, ...]:
    """Return the v1 deterministic seed-ranked exact student order."""

    canonical = _canonical_roster(student_ids)
    exact_seed = _require_seed(seed)
    return tuple(
        sorted(
            canonical,
            key=lambda student_id: (
                _rank_digest(exact_seed, student_id),
                student_id,
            ),
        )
    )


def generate_random_group_plan_proposal(
    student_ids: tuple[str, ...],
    *,
    seed: str,
    target_group_size: int | None = None,
    target_group_count: int | None = None,
) -> RandomGroupPlanProposal:
    """Generate a complete balanced proposal with no persistence side effects."""

    canonical = _canonical_roster(student_ids)
    exact_seed = _require_seed(seed)
    try:
        group_count = resolve_group_count(
            len(canonical),
            target_group_size=target_group_size,
            target_group_count=target_group_count,
        )
    except GroupPlanTargetError as error:
        raise RandomGroupPlanningError(str(error)) from error

    ordered = tuple(
        sorted(
            canonical,
            key=lambda student_id: (
                _rank_digest(exact_seed, student_id),
                student_id,
            ),
        )
    )
    group_sizes = balanced_group_sizes(len(ordered), group_count)

    offset = 0
    groups: list[PlannedGroup] = []
    for index, group_size in enumerate(group_sizes, start=1):
        students = ordered[offset : offset + group_size]
        offset += group_size
        groups.append(
            PlannedGroup(
                planned_group_key=f"random-{index}",
                label=f"Group {index}",
                student_ids=students,
            )
        )

    return RandomGroupPlanProposal(
        roster_student_ids=canonical,
        proposed_groups=tuple(groups),
        group_sizes=group_sizes,
        group_count=group_count,
    )
