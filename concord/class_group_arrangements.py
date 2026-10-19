"""Pure contracts for class-scoped, teacher-restricted reusable arrangements.

These records deliberately carry no Activity, Session, Group, Membership or Score ID.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from pds_core.identifiers import validate_identifier
from pds_core.school_years import validate_school_year

ARRANGEMENT_SCHEMA = "concord_class_group_arrangement_v1"
_SHA = re.compile(r"^[0-9a-f]{64}$")


class ArrangementValidationError(ValueError):
    """An arrangement or its exact-roster representation is invalid."""


def _id(value: str, field: str) -> str:
    try:
        return validate_identifier(value, field)
    except (TypeError, ValueError) as exc:
        raise ArrangementValidationError(f"Invalid {field}.") from exc


def _label(value: str | None, field: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > 500:
        raise ArrangementValidationError(
            f"{field} must be nonblank and at most 500 characters."
        )
    if value != value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ArrangementValidationError(f"{field} has unsafe whitespace or controls.")
    return value


def _ids(values: tuple[str, ...], field: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ArrangementValidationError(f"{field} must be a tuple of exact IDs.")
    validated = tuple(_id(x, field) for x in values)
    if len(set(validated)) != len(validated):
        raise ArrangementValidationError(f"{field} contains duplicates.")
    return validated


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedArrangementGroup:
    key: str
    label: str
    student_ids: tuple[str, ...]
    description: str | None = None

    def __post_init__(self) -> None:
        _id(self.key, "group key")
        _label(self.label, "group label")
        _label(self.description, "group description", optional=True)
        _ids(self.student_ids, "group students")


@dataclass(frozen=True, slots=True, kw_only=True)
class SavedArrangementRevision:
    arrangement_id: str
    class_id: str
    school_year: str
    revision: int
    name: str
    owner_actor_id: str
    created_by_actor_id: str
    created_at: str
    groups: tuple[SavedArrangementGroup, ...]
    roster_student_ids: tuple[str, ...]
    unresolved_student_ids: tuple[str, ...] = ()
    status: str = "active"
    predecessor_sha256: str | None = None

    def __post_init__(self) -> None:
        for field in (
            "arrangement_id",
            "class_id",
            "owner_actor_id",
            "created_by_actor_id",
        ):
            _id(getattr(self, field), field)
        try:
            validate_school_year(self.school_year)
        except (TypeError, ValueError) as exc:
            raise ArrangementValidationError("Invalid school_year.") from exc
        if type(self.revision) is not int or self.revision < 1:
            raise ArrangementValidationError("revision must be positive.")
        _label(self.name, "arrangement name")
        if self.status not in {"active", "retired"}:
            raise ArrangementValidationError("status must be active or retired.")
        try:
            stamp = datetime.fromisoformat(self.created_at)
        except (TypeError, ValueError) as exc:
            raise ArrangementValidationError(
                "created_at must be an ISO timestamp."
            ) from exc
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ArrangementValidationError("created_at must have a timezone.")
        if self.revision == 1 and self.predecessor_sha256 is not None:
            raise ArrangementValidationError(
                "first revision cannot have a predecessor."
            )
        if self.revision > 1 and (
            not isinstance(self.predecessor_sha256, str)
            or not _SHA.fullmatch(self.predecessor_sha256)
        ):
            raise ArrangementValidationError(
                "successor must identify predecessor SHA-256."
            )
        if not isinstance(self.groups, tuple) or not self.groups:
            raise ArrangementValidationError("At least one saved group is required.")
        if any(not isinstance(g, SavedArrangementGroup) for g in self.groups):
            raise ArrangementValidationError("groups must contain saved group records.")
        keys = [g.key for g in self.groups]
        if len(set(keys)) != len(keys):
            raise ArrangementValidationError("Duplicate group keys are forbidden.")
        roster = _ids(self.roster_student_ids, "roster students")
        unresolved = _ids(self.unresolved_student_ids, "unresolved students")
        assigned = [sid for g in self.groups for sid in g.student_ids]
        if len(set(assigned)) != len(assigned):
            raise ArrangementValidationError(
                "A student cannot belong to multiple groups."
            )
        if set(assigned) & set(unresolved):
            raise ArrangementValidationError(
                "Assigned students cannot also be unresolved."
            )
        if set(assigned) | set(unresolved) != set(roster):
            raise ArrangementValidationError(
                "Every captured Core-roster student must be assigned "
                "or explicitly unresolved."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ArrangementRosterComparison:
    newly_enrolled_ids: tuple[str, ...]
    departed_ids: tuple[str, ...]
    unresolved_ids: tuple[str, ...]
    retained_assigned_count: int

    @property
    def needs_teacher_review(self) -> bool:
        return bool(self.newly_enrolled_ids or self.departed_ids or self.unresolved_ids)


def compare_roster(
    revision: SavedArrangementRevision,
    *,
    target_class_id: str,
    target_school_year: str,
    target_student_ids: tuple[str, ...],
) -> ArrangementRosterComparison:
    """Read-only exact-ID reconciliation; no auto-placement or silent drops."""
    if _id(target_class_id, "target class") != revision.class_id:
        raise ArrangementValidationError("Saved grouping belongs to another class.")
    if target_school_year != revision.school_year:
        raise ArrangementValidationError(
            "Saved grouping belongs to another school year."
        )
    target = set(_ids(target_student_ids, "target roster"))
    old = set(revision.roster_student_ids)
    assigned = {sid for group in revision.groups for sid in group.student_ids}
    return ArrangementRosterComparison(
        newly_enrolled_ids=tuple(sorted(target - old)),
        departed_ids=tuple(sorted(old - target)),
        unresolved_ids=tuple(sorted(set(revision.unresolved_student_ids) & target)),
        retained_assigned_count=len(assigned & target),
    )
