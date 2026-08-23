"""Pure deterministic placement for #55 missing-signal students."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass, replace

from pds_core.identifiers import IdentifierValidationError, validate_identifier

from concord.models import PlannedGroup

MISSING_SIGNAL_RANDOM_DOMAIN = (
    "pds-concord:group-plan-missing-signal-random:v1"
)


class MissingSignalRandomizationError(ValueError):
    """Raised when deterministic missing-signal placement inputs are invalid."""


@dataclass(frozen=True, slots=True)
class MissingSignalRandomizationResult:
    """Pure deterministic transformation of existing PlannedGroups."""

    proposed_groups: tuple[PlannedGroup, ...]
    placements: tuple[tuple[str, str], ...]
    group_sizes: tuple[int, ...]


def _require_seed(seed: str) -> str:
    if not isinstance(seed, str) or not seed.strip() or seed != seed.strip():
        raise MissingSignalRandomizationError(
            "seed must be a nonempty string without surrounding whitespace."
        )
    return seed


def _student_ids(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise MissingSignalRandomizationError(
            "missing_student_ids must be an iterable of student IDs."
        )
    try:
        raw = tuple(values)
    except TypeError as error:
        raise MissingSignalRandomizationError(
            "missing_student_ids must be iterable."
        ) from error

    normalized: list[str] = []
    for index, value in enumerate(raw):
        try:
            normalized.append(
                validate_identifier(
                    value,
                    f"missing_student_ids[{index}]",
                )
            )
        except IdentifierValidationError as error:
            raise MissingSignalRandomizationError(str(error)) from error
    if len(set(normalized)) != len(normalized):
        raise MissingSignalRandomizationError(
            "missing_student_ids must not contain duplicates."
        )
    return tuple(normalized)


def _groups(values: Iterable[PlannedGroup]) -> tuple[PlannedGroup, ...]:
    if isinstance(values, (str, bytes)):
        raise MissingSignalRandomizationError(
            "proposed_groups must be an iterable of PlannedGroup values."
        )
    try:
        groups = tuple(values)
    except TypeError as error:
        raise MissingSignalRandomizationError(
            "proposed_groups must be iterable."
        ) from error
    if not groups:
        raise MissingSignalRandomizationError(
            "random missing-signal distribution requires at least one PlannedGroup."
        )
    if any(not isinstance(group, PlannedGroup) for group in groups):
        raise MissingSignalRandomizationError(
            "proposed_groups must contain only PlannedGroup values."
        )
    keys = tuple(group.planned_group_key for group in groups)
    if len(set(keys)) != len(keys):
        raise MissingSignalRandomizationError(
            "proposed_groups must not duplicate planned_group_key."
        )
    return groups


def _rank(seed: str, student_id: str) -> bytes:
    payload = (
        MISSING_SIGNAL_RANDOM_DOMAIN.encode("utf-8")
        + b"\0"
        + seed.encode("utf-8")
        + b"\0"
        + student_id.encode("utf-8")
    )
    return hashlib.sha256(payload).digest()


def distribute_missing_signal_students(
    proposed_groups: Iterable[PlannedGroup],
    missing_student_ids: Iterable[str],
    *,
    seed: str,
) -> MissingSignalRandomizationResult:
    """Distribute exact missing students by frozen SHA-256 rank and smallest group.

    Existing memberships and PlannedGroup metadata are preserved. The function
    performs no workspace I/O, signal lookup, provenance creation, or randomness.
    """

    normalized_seed = _require_seed(seed)
    groups = _groups(proposed_groups)
    missing = _student_ids(missing_student_ids)

    assigned = {
        student_id
        for group in groups
        for student_id in group.student_ids
    }
    overlap = tuple(sorted(set(missing) & assigned))
    if overlap:
        raise MissingSignalRandomizationError(
            "missing students must be unresolved before random distribution: "
            + ", ".join(overlap)
        )

    ordered = tuple(
        sorted(
            missing,
            key=lambda student_id: (
                _rank(normalized_seed, student_id),
                student_id,
            ),
        )
    )
    result = list(groups)
    placements: list[tuple[str, str]] = []

    for student_id in ordered:
        index = min(
            range(len(result)),
            key=lambda item: (
                len(result[item].student_ids),
                result[item].planned_group_key,
            ),
        )
        group = result[index]
        result[index] = replace(
            group,
            student_ids=group.student_ids + (student_id,),
        )
        placements.append((student_id, group.planned_group_key))

    transformed = tuple(result)
    return MissingSignalRandomizationResult(
        proposed_groups=transformed,
        placements=tuple(placements),
        group_sizes=tuple(
            len(group.student_ids) for group in transformed
        ),
    )
