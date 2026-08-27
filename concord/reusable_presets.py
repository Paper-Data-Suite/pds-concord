"""Typed workspace-level reusable preset contracts for Concord."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, TypeAlias

from concord.models.collaboration import ROLE_KEYS
from concord.models.common import (
    ConcordModelError,
    Provenance,
    controlled,
    controlled_key,
    identifier,
    optional_identifier,
    optional_text,
    positive_int,
    require_text,
    tuple_of_identifiers,
    tuple_of_values,
)
from concord.models.scoring import ScoringScaleLevel

PRESET_SCHEMA_VERSION: Final[str] = "1"
PRESET_KINDS: Final[frozenset[str]] = frozenset(
    {
        "role",
        "responsibility",
        "criterion_set",
        "scoring_scale",
    }
)
PRESET_STATUSES: Final[frozenset[str]] = frozenset({"active", "retired"})


def _hints(value: tuple[str, ...]) -> tuple[str, ...]:
    items = tuple(require_text(item, "applicability_hints[]") for item in value)
    if len(set(items)) != len(items):
        raise ConcordModelError("applicability_hints must not contain duplicates.")
    return items


@dataclass(frozen=True, slots=True, kw_only=True)
class RolePresetRevision:
    preset_id: str
    preset_revision_id: str
    revision: int
    name: str
    role_key: str
    status: str
    created_provenance: Provenance
    role_label: str | None = None
    description: str | None = None
    applicability_hints: tuple[str, ...] = ()
    supersedes_preset_revision_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.preset_id, "preset_id")
        identifier(self.preset_revision_id, "preset_revision_id")
        positive_int(self.revision, "revision")
        require_text(self.name, "name")
        controlled_key(self.role_key, "role_key", ROLE_KEYS)
        controlled(self.status, "status", PRESET_STATUSES)
        optional_text(self.role_label, "role_label")
        optional_text(self.description, "description")
        object.__setattr__(
            self,
            "applicability_hints",
            _hints(self.applicability_hints),
        )
        optional_identifier(
            self.supersedes_preset_revision_id,
            "supersedes_preset_revision_id",
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.revision == 1 and self.supersedes_preset_revision_id is not None:
            raise ConcordModelError("initial preset revision cannot supersede another.")
        if self.revision > 1 and self.supersedes_preset_revision_id is None:
            raise ConcordModelError(
                "successor preset revision requires predecessor ID."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResponsibilityPresetRevision:
    preset_id: str
    preset_revision_id: str
    revision: int
    name: str
    description: str
    status: str
    created_provenance: Provenance
    expected_output: str | None = None
    applicability_hints: tuple[str, ...] = ()
    supersedes_preset_revision_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.preset_id, "preset_id")
        identifier(self.preset_revision_id, "preset_revision_id")
        positive_int(self.revision, "revision")
        require_text(self.name, "name")
        require_text(self.description, "description")
        controlled(self.status, "status", PRESET_STATUSES)
        optional_text(self.expected_output, "expected_output")
        object.__setattr__(
            self,
            "applicability_hints",
            _hints(self.applicability_hints),
        )
        optional_identifier(
            self.supersedes_preset_revision_id,
            "supersedes_preset_revision_id",
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.revision == 1 and self.supersedes_preset_revision_id is not None:
            raise ConcordModelError("initial preset revision cannot supersede another.")
        if self.revision > 1 and self.supersedes_preset_revision_id is None:
            raise ConcordModelError(
                "successor preset revision requires predecessor ID."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringScalePresetRevision:
    preset_id: str
    preset_revision_id: str
    revision: int
    name: str
    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]
    status: str
    created_provenance: Provenance
    intended_use: str | None = None
    aggregation_guidance: str | None = None
    supersedes_preset_revision_id: str | None = None

    def __post_init__(self) -> None:
        from concord.models.scoring import ScoringScale

        identifier(self.preset_id, "preset_id")
        identifier(self.preset_revision_id, "preset_revision_id")
        positive_int(self.revision, "revision")
        require_text(self.name, "name")
        controlled(self.status, "status", PRESET_STATUSES)
        object.__setattr__(
            self,
            "levels",
            tuple_of_values(self.levels, ScoringScaleLevel, "levels", nonempty=True),
        )
        optional_text(self.intended_use, "intended_use")
        optional_text(self.aggregation_guidance, "aggregation_guidance")
        optional_identifier(
            self.supersedes_preset_revision_id,
            "supersedes_preset_revision_id",
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        if self.revision == 1 and self.supersedes_preset_revision_id is not None:
            raise ConcordModelError("initial preset revision cannot supersede another.")
        if self.revision > 1 and self.supersedes_preset_revision_id is None:
            raise ConcordModelError(
                "successor preset revision requires predecessor ID."
            )
        # Reuse native Scale validation without turning the preset into Activity state.
        ScoringScale(
            scoring_scale_id=self.preset_revision_id,
            lineage_id=self.preset_id,
            name=self.name,
            revision=self.revision,
            scale_type=self.scale_type,
            levels=self.levels,
            status="active" if self.status == "active" else "archived",
            created_provenance=self.created_provenance,
            intended_use=self.intended_use,
            aggregation_guidance=self.aggregation_guidance,
            supersedes_scoring_scale_id=self.supersedes_preset_revision_id,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionPresetSpec:
    key: str
    label: str
    definition: str
    criterion_kind: str
    supported_target_kinds: tuple[str, ...]
    standard_id: str | None = None
    alignment_standard_ids: tuple[str, ...] = ()
    default_scoring_scale_preset_id: str | None = None
    default_scoring_scale_preset_revision_id: str | None = None
    status: str = "active"

    def __post_init__(self) -> None:
        identifier(self.key, "key")
        require_text(self.label, "label")
        require_text(self.definition, "definition")
        kind = controlled(
            self.criterion_kind,
            "criterion_kind",
            frozenset({"standard_backed", "local"}),
        )
        target_kinds = tuple(self.supported_target_kinds)
        if not target_kinds or len(set(target_kinds)) != len(target_kinds):
            raise ConcordModelError(
                "supported_target_kinds must be nonempty and unique."
            )
        allowed_targets = frozenset(
            {
                "core_student",
                "concord_group",
                "concord_session",
                "concord_activity",
                "concord_artifact_instance",
            }
        )
        for index, target_kind in enumerate(target_kinds):
            controlled(
                target_kind,
                f"supported_target_kinds[{index}]",
                allowed_targets,
            )
        object.__setattr__(self, "supported_target_kinds", target_kinds)
        object.__setattr__(
            self,
            "alignment_standard_ids",
            tuple_of_identifiers(
                self.alignment_standard_ids,
                "alignment_standard_ids",
            ),
        )
        optional_identifier(self.standard_id, "standard_id")
        controlled(
            self.status,
            "status",
            frozenset({"draft", "active", "inactive", "archived"}),
        )
        if kind == "standard_backed" and self.standard_id is None:
            raise ConcordModelError(
                "standard-backed Criterion preset requires standard_id."
            )
        if kind == "local" and self.standard_id is not None:
            raise ConcordModelError("local Criterion preset forbids standard_id.")
        optional_identifier(
            self.default_scoring_scale_preset_id,
            "default_scoring_scale_preset_id",
        )
        optional_identifier(
            self.default_scoring_scale_preset_revision_id,
            "default_scoring_scale_preset_revision_id",
        )
        if (self.default_scoring_scale_preset_id is None) != (
            self.default_scoring_scale_preset_revision_id is None
        ):
            raise ConcordModelError(
                "default Scale preset ID and revision ID must be supplied together."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionSetPresetRevision:
    preset_id: str
    preset_revision_id: str
    revision: int
    name: str
    purpose: str
    criterion_set_kind: str
    criteria: tuple[CriterionPresetSpec, ...]
    status: str
    created_provenance: Provenance
    standards_profile_id: str | None = None
    supersedes_preset_revision_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.preset_id, "preset_id")
        identifier(self.preset_revision_id, "preset_revision_id")
        positive_int(self.revision, "revision")
        require_text(self.name, "name")
        require_text(self.purpose, "purpose")
        controlled(
            self.criterion_set_kind,
            "criterion_set_kind",
            frozenset({"standard_backed", "local", "mixed"}),
        )
        criteria = tuple_of_values(
            self.criteria,
            CriterionPresetSpec,
            "criteria",
            nonempty=True,
        )
        if len({item.key for item in criteria}) != len(criteria):
            raise ConcordModelError("Criterion preset keys must be unique.")
        object.__setattr__(self, "criteria", criteria)
        scale_references = {
            (
                item.default_scoring_scale_preset_id,
                item.default_scoring_scale_preset_revision_id,
            )
            for item in criteria
            if item.default_scoring_scale_preset_id is not None
        }
        if len(scale_references) > 1:
            raise ConcordModelError(
                "Criterion Set preset may recommend at most one Scoring Scale preset."
            )
        controlled(self.status, "status", PRESET_STATUSES)
        optional_identifier(self.standards_profile_id, "standards_profile_id")
        optional_identifier(
            self.supersedes_preset_revision_id,
            "supersedes_preset_revision_id",
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError("created_provenance must be Provenance.")
        kinds = {item.criterion_kind for item in criteria}
        if self.criterion_set_kind == "standard_backed" and kinds != {
            "standard_backed"
        }:
            raise ConcordModelError(
                "standard_backed preset may contain only standard-backed Criteria."
            )
        if self.criterion_set_kind == "local" and kinds != {"local"}:
            raise ConcordModelError(
                "local preset may contain only local Criteria."
            )
        if self.revision == 1 and self.supersedes_preset_revision_id is not None:
            raise ConcordModelError("initial preset revision cannot supersede another.")
        if self.revision > 1 and self.supersedes_preset_revision_id is None:
            raise ConcordModelError(
                "successor preset revision requires predecessor ID."
            )


PresetRevision: TypeAlias = (
    RolePresetRevision
    | ResponsibilityPresetRevision
    | CriterionSetPresetRevision
    | ScoringScalePresetRevision
)


def preset_kind(value: PresetRevision) -> str:
    if isinstance(value, RolePresetRevision):
        return "role"
    if isinstance(value, ResponsibilityPresetRevision):
        return "responsibility"
    if isinstance(value, CriterionSetPresetRevision):
        return "criterion_set"
    if isinstance(value, ScoringScalePresetRevision):
        return "scoring_scale"
    raise ConcordModelError("unsupported preset revision type.")


__all__ = [
    "PRESET_KINDS",
    "PRESET_SCHEMA_VERSION",
    "PRESET_STATUSES",
    "CriterionPresetSpec",
    "CriterionSetPresetRevision",
    "PresetRevision",
    "ResponsibilityPresetRevision",
    "RolePresetRevision",
    "ScoringScalePresetRevision",
    "preset_kind",
]
