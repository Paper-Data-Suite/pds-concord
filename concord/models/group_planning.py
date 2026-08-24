"""Planning-only GroupPlan native records for Concord v0.3."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pds_core.routing_models import ModuleRecordRef

from concord.models.common import (
    ConcordModelError,
    EffectiveContext,
    Provenance,
    controlled,
    identifier,
    optional_positive_int,
    optional_text,
    require_text,
    tuple_of_identifiers,
    tuple_of_values,
)

GROUP_PLAN_STRATEGIES = frozenset(
    {
        "manual",
        "imported_arrangement",
        "random",
        "similar_signal",
        "mixed_signal",
    }
)
GROUP_PLAN_STATUSES = frozenset(
    {
        "draft",
        "previewed",
        "approved",
        "applied",
        "cancelled",
    }
)
_SIGNAL_STRATEGIES = frozenset({"similar_signal", "mixed_signal"})
MISSING_SIGNAL_DISPOSITIONS = frozenset(
    {"manual", "random", "leave_unassigned"}
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sorted_identifiers(value: tuple[str, ...], field_name: str) -> tuple[str, ...]:
    return tuple(sorted(tuple_of_identifiers(value, field_name)))


def _optional_provenance(value: Provenance | None, field_name: str) -> None:
    if value is not None and not isinstance(value, Provenance):
        raise ConcordModelError(f"{field_name} must be Provenance.")


@dataclass(frozen=True, slots=True, kw_only=True)
class PlannedGroup:
    """One plan-local proposed Group, never a canonical Concord Group."""

    planned_group_key: str
    label: str
    student_ids: tuple[str, ...] = ()
    description: str | None = None
    effective_context: EffectiveContext | None = None

    def __post_init__(self) -> None:
        identifier(self.planned_group_key, "planned_group_key")
        require_text(self.label, "label")
        object.__setattr__(
            self,
            "student_ids",
            _sorted_identifiers(self.student_ids, "student_ids"),
        )
        optional_text(self.description, "description")
        if self.effective_context is not None and not isinstance(
            self.effective_context,
            EffectiveContext,
        ):
            raise ConcordModelError(
                "effective_context must be an EffectiveContext."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class GroupPlan:
    """One Activity-owned grouping proposal with native revision history."""

    group_plan_id: str
    activity_id: str
    class_reference: ModuleRecordRef
    strategy: str
    status: str
    roster_student_ids: tuple[str, ...]
    proposed_groups: tuple[PlannedGroup, ...]
    unresolved_student_ids: tuple[str, ...]
    created_provenance: Provenance
    target_group_size: int | None = None
    target_group_count: int | None = None
    seed: str | None = None
    source_signal_set_id: str | None = None
    source_signal_set_digest: str | None = None
    source_signal_dimension_id: str | None = None
    missing_signal_disposition: str | None = None
    missing_signal_random_seed: str | None = None
    missing_signal_disposition_provenance: Provenance | None = None
    applied_application_id: str | None = None
    applied_application_digest: str | None = None
    updated_provenance: Provenance | None = None
    previewed_provenance: Provenance | None = None
    approved_provenance: Provenance | None = None
    cancelled_provenance: Provenance | None = None
    applied_provenance: Provenance | None = None

    def __post_init__(self) -> None:
        identifier(self.group_plan_id, "group_plan_id")
        identifier(self.activity_id, "activity_id")
        if not isinstance(self.class_reference, ModuleRecordRef):
            raise ConcordModelError(
                "class_reference must be a ModuleRecordRef."
            )
        if (
            self.class_reference.module_id != "core"
            or self.class_reference.record_kind != "class"
        ):
            raise ConcordModelError(
                "class_reference must identify a Core class."
            )

        strategy = controlled(
            self.strategy,
            "strategy",
            GROUP_PLAN_STRATEGIES,
        )
        status = controlled(self.status, "status", GROUP_PLAN_STATUSES)

        roster = _sorted_identifiers(
            self.roster_student_ids,
            "roster_student_ids",
        )
        if not roster:
            raise ConcordModelError("roster_student_ids must not be empty.")
        object.__setattr__(self, "roster_student_ids", roster)

        groups = tuple_of_values(
            self.proposed_groups,
            PlannedGroup,
            "proposed_groups",
        )
        object.__setattr__(self, "proposed_groups", groups)
        group_keys = tuple(item.planned_group_key for item in groups)
        if len(set(group_keys)) != len(group_keys):
            raise ConcordModelError(
                "proposed_groups must not duplicate planned_group_key."
            )

        unresolved = _sorted_identifiers(
            self.unresolved_student_ids,
            "unresolved_student_ids",
        )
        object.__setattr__(
            self,
            "unresolved_student_ids",
            unresolved,
        )

        assigned = tuple(
            student_id
            for group in groups
            for student_id in group.student_ids
        )
        if len(set(assigned)) != len(assigned):
            raise ConcordModelError(
                "a student must not appear in more than one PlannedGroup."
            )
        assigned_set = set(assigned)
        unresolved_set = set(unresolved)
        if assigned_set & unresolved_set:
            raise ConcordModelError(
                "a student must not be both grouped and unresolved."
            )
        if assigned_set | unresolved_set != set(roster):
            raise ConcordModelError(
                "proposed and unresolved students must exactly cover "
                "roster_student_ids."
            )

        size = optional_positive_int(
            self.target_group_size,
            "target_group_size",
        )
        count = optional_positive_int(
            self.target_group_count,
            "target_group_count",
        )
        if size is not None and count is not None:
            raise ConcordModelError(
                "target_group_size and target_group_count are mutually "
                "exclusive."
            )
        if status != "draft" and strategy in {
            "random",
            "similar_signal",
            "mixed_signal",
        }:
            if (size is None) == (count is None):
                raise ConcordModelError(
                    "generated previewed/terminal plans require exactly one "
                    "group-size/count target."
                )

        optional_text(self.seed, "seed")
        if self.seed is not None and strategy != "random":
            raise ConcordModelError("seed is reserved for random plans.")
        if status != "draft" and strategy == "random" and self.seed is None:
            raise ConcordModelError(
                "previewed/terminal random plans require an explicit seed."
            )

        signal_values = (
            self.source_signal_set_id,
            self.source_signal_set_digest,
            self.source_signal_dimension_id,
        )
        if any(value is not None for value in signal_values) and not all(
            value is not None for value in signal_values
        ):
            raise ConcordModelError(
                "signal-set ID, digest, and dimension must be supplied together."
            )
        if self.source_signal_set_id is not None:
            identifier(
                self.source_signal_set_id,
                "source_signal_set_id",
            )
            identifier(
                self.source_signal_dimension_id,
                "source_signal_dimension_id",
            )
            digest = self.source_signal_set_digest
            if (
                not isinstance(digest, str)
                or _SHA256.fullmatch(digest) is None
            ):
                raise ConcordModelError(
                    "source_signal_set_digest must be lowercase SHA-256 hex."
                )
            if strategy not in _SIGNAL_STRATEGIES:
                raise ConcordModelError(
                    "only signal-dependent strategies may bind a signal set."
                )
        elif status != "draft" and strategy in _SIGNAL_STRATEGIES:
            raise ConcordModelError(
                "previewed/terminal signal plans require an exact signal binding."
            )

        disposition = self.missing_signal_disposition
        if disposition is not None:
            disposition = controlled(
                disposition,
                "missing_signal_disposition",
                MISSING_SIGNAL_DISPOSITIONS,
            )
            if strategy not in _SIGNAL_STRATEGIES:
                raise ConcordModelError(
                    "missing-signal disposition is reserved for "
                    "signal-dependent strategies."
                )
            if self.source_signal_set_id is None:
                raise ConcordModelError(
                    "missing-signal disposition requires an exact signal binding."
                )
            if self.missing_signal_disposition_provenance is None:
                raise ConcordModelError(
                    "missing-signal disposition requires disposition provenance."
                )
        elif self.missing_signal_disposition_provenance is not None:
            raise ConcordModelError(
                "missing-signal disposition provenance requires a disposition."
            )

        optional_text(
            self.missing_signal_random_seed,
            "missing_signal_random_seed",
        )
        if disposition == "random":
            if self.missing_signal_random_seed is None:
                raise ConcordModelError(
                    "random missing-signal disposition requires an explicit seed."
                )
        elif self.missing_signal_random_seed is not None:
            raise ConcordModelError(
                "missing-signal random seed is allowed only for random disposition."
            )

        if self.applied_application_id is not None:
            identifier(self.applied_application_id, "applied_application_id")
        if self.applied_application_digest is not None:
            digest = self.applied_application_digest
            if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
                raise ConcordModelError(
                    "applied_application_digest must be lowercase SHA-256 hex."
                )

        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError(
                "created_provenance must be Provenance."
            )
        for field_name in (
            "missing_signal_disposition_provenance",
            "updated_provenance",
            "previewed_provenance",
            "approved_provenance",
            "cancelled_provenance",
            "applied_provenance",
        ):
            _optional_provenance(getattr(self, field_name), field_name)

        self._validate_status_provenance(status)

        application_values = (
            self.applied_application_id,
            self.applied_application_digest,
        )
        if status == "applied":
            if any(value is None for value in application_values):
                raise ConcordModelError(
                    "applied plan requires application ID and digest."
                )
        elif any(value is not None for value in application_values):
            raise ConcordModelError(
                "application ID and digest are only allowed on applied plans."
            )

        if status in {"approved", "applied"} and unresolved:
            if not (
                strategy in _SIGNAL_STRATEGIES
                and disposition == "leave_unassigned"
            ):
                raise ConcordModelError(
                    "approved/applied plans may retain unresolved students only "
                    "for leave_unassigned missing-signal disposition."
                )

    def _validate_status_provenance(self, status: str) -> None:
        if status == "draft":
            forbidden = (
                self.previewed_provenance,
                self.approved_provenance,
                self.cancelled_provenance,
                self.applied_provenance,
            )
            if any(value is not None for value in forbidden):
                raise ConcordModelError(
                    "draft plan cannot carry lifecycle-transition provenance."
                )
            return

        if status == "previewed":
            if self.previewed_provenance is None:
                raise ConcordModelError(
                    "previewed plan requires previewed_provenance."
                )
            if any(
                value is not None
                for value in (
                    self.approved_provenance,
                    self.cancelled_provenance,
                    self.applied_provenance,
                )
            ):
                raise ConcordModelError(
                    "previewed plan has incoherent later-state provenance."
                )
            return

        if status == "approved":
            if (
                self.previewed_provenance is None
                or self.approved_provenance is None
            ):
                raise ConcordModelError(
                    "approved plan requires preview and approval provenance."
                )
            if (
                self.cancelled_provenance is not None
                or self.applied_provenance is not None
            ):
                raise ConcordModelError(
                    "approved plan has incoherent terminal provenance."
                )
            return

        if status == "applied":
            if any(
                value is None
                for value in (
                    self.previewed_provenance,
                    self.approved_provenance,
                    self.applied_provenance,
                )
            ):
                raise ConcordModelError(
                    "applied plan requires preview, approval, and application "
                    "provenance."
                )
            if self.cancelled_provenance is not None:
                raise ConcordModelError(
                    "applied plan cannot also be cancelled."
                )
            return

        if self.cancelled_provenance is None:
            raise ConcordModelError(
                "cancelled plan requires cancelled_provenance."
            )
        if (
            self.approved_provenance is not None
            and self.previewed_provenance is None
        ):
            raise ConcordModelError(
                "cancelled plan cannot retain approval without preview provenance."
            )
        if self.applied_provenance is not None:
            raise ConcordModelError(
                "cancelled plan cannot also be applied."
            )
