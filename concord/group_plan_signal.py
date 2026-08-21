"""Pure deterministic signal-backed GroupPlan proposal generation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pds_core.identifiers import IdentifierValidationError, validate_identifier

from concord.group_plan_targets import (
    GroupPlanTargetError,
    balanced_group_sizes,
    resolve_group_count,
)
from concord.models import PlannedGroup


class SignalGroupPlanningError(ValueError):
    """Raised when deterministic signal-planning inputs are invalid."""


@dataclass(frozen=True, slots=True)
class SignalGroupPlanProposal:
    """One deterministic signal-backed proposal before persistence."""

    roster_student_ids: tuple[str, ...]
    proposed_groups: tuple[PlannedGroup, ...]
    unresolved_student_ids: tuple[str, ...]
    group_sizes: tuple[int, ...]
    group_count: int

    @property
    def assigned_student_count(self) -> int:
        return sum(self.group_sizes)

    @property
    def unresolved_student_count(self) -> int:
        return len(self.unresolved_student_ids)


def _canonical_roster(student_ids: tuple[str, ...]) -> tuple[str, ...]:
    if not student_ids:
        raise SignalGroupPlanningError(
            "signal planning requires a nonempty current roster."
        )
    validated: list[str] = []
    for student_id in student_ids:
        try:
            validated.append(validate_identifier(student_id, "student_id"))
        except (IdentifierValidationError, TypeError, ValueError) as error:
            raise SignalGroupPlanningError(str(error)) from error
    if len(set(validated)) != len(validated):
        raise SignalGroupPlanningError(
            "signal planning roster must not contain duplicate student IDs."
        )
    return tuple(sorted(validated))


def _validated_signal_bands(
    roster_student_ids: tuple[str, ...],
    signal_bands: Mapping[str, int],
) -> dict[str, int]:
    if not isinstance(signal_bands, Mapping):
        raise SignalGroupPlanningError(
            "signal_bands must be a student-to-band mapping."
        )

    roster_set = set(roster_student_ids)
    validated: dict[str, int] = {}
    for raw_student_id, band in signal_bands.items():
        try:
            student_id = validate_identifier(raw_student_id, "student_id")
        except (IdentifierValidationError, TypeError, ValueError) as error:
            raise SignalGroupPlanningError(str(error)) from error
        if student_id not in roster_set:
            raise SignalGroupPlanningError(
                "signal_bands must contain only exact current-roster student IDs."
            )
        if isinstance(band, bool) or not isinstance(band, int) or band <= 0:
            raise SignalGroupPlanningError(
                f"signal band for {student_id!r} must be a positive integer."
            )
        validated[student_id] = band
    return validated


def _group_count(
    roster_size: int,
    *,
    target_group_size: int | None,
    target_group_count: int | None,
) -> int:
    try:
        return resolve_group_count(
            roster_size,
            target_group_size=target_group_size,
            target_group_count=target_group_count,
        )
    except GroupPlanTargetError as error:
        raise SignalGroupPlanningError(str(error)) from error


def _proposal(
    roster_student_ids: tuple[str, ...],
    signal_bands: Mapping[str, int],
    *,
    strategy: str,
    target_group_size: int | None,
    target_group_count: int | None,
) -> SignalGroupPlanProposal:
    roster = _canonical_roster(roster_student_ids)
    bands = _validated_signal_bands(roster, signal_bands)
    group_count = _group_count(
        len(roster),
        target_group_size=target_group_size,
        target_group_count=target_group_count,
    )
    unresolved = tuple(
        student_id for student_id in roster if student_id not in bands
    )

    if strategy == "similar_signal":
        ordered = tuple(
            student_id
            for student_id, _band in sorted(
                bands.items(),
                key=lambda item: (item[1], item[0]),
            )
        )
        group_sizes = balanced_group_sizes(len(ordered), group_count)
        groups: list[PlannedGroup] = []
        offset = 0
        for index, group_size in enumerate(group_sizes, start=1):
            students = ordered[offset : offset + group_size]
            offset += group_size
            groups.append(
                PlannedGroup(
                    planned_group_key=f"similar-{index}",
                    label=f"Group {index}",
                    student_ids=students,
                )
            )
    elif strategy == "mixed_signal":
        ordered = tuple(
            student_id
            for student_id, _band in sorted(
                bands.items(),
                key=lambda item: (-item[1], item[0]),
            )
        )
        buckets: list[list[str]] = [[] for _index in range(group_count)]
        for position, student_id in enumerate(ordered):
            buckets[position % group_count].append(student_id)
        group_sizes = tuple(len(bucket) for bucket in buckets)
        groups = [
            PlannedGroup(
                planned_group_key=f"mixed-{index}",
                label=f"Group {index}",
                student_ids=tuple(bucket),
            )
            for index, bucket in enumerate(buckets, start=1)
        ]
    else:
        raise SignalGroupPlanningError(
            "strategy must be 'similar_signal' or 'mixed_signal'."
        )

    return SignalGroupPlanProposal(
        roster_student_ids=roster,
        proposed_groups=tuple(groups),
        unresolved_student_ids=unresolved,
        group_sizes=group_sizes,
        group_count=group_count,
    )


def generate_similar_signal_group_plan_proposal(
    roster_student_ids: tuple[str, ...],
    signal_bands: Mapping[str, int],
    *,
    target_group_size: int | None = None,
    target_group_count: int | None = None,
) -> SignalGroupPlanProposal:
    """Cluster equal/nearby ordinal bands by deterministic contiguous partition."""

    return _proposal(
        roster_student_ids,
        signal_bands,
        strategy="similar_signal",
        target_group_size=target_group_size,
        target_group_count=target_group_count,
    )


def generate_mixed_signal_group_plan_proposal(
    roster_student_ids: tuple[str, ...],
    signal_bands: Mapping[str, int],
    *,
    target_group_size: int | None = None,
    target_group_count: int | None = None,
) -> SignalGroupPlanProposal:
    """Distribute ordinal bands by deterministic descending-band round robin."""

    return _proposal(
        roster_student_ids,
        signal_bands,
        strategy="mixed_signal",
        target_group_size=target_group_size,
        target_group_count=target_group_count,
    )
