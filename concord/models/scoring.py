"""Immutable criterion, scale, score, and evidence-link records."""

from __future__ import annotations

from dataclasses import dataclass

from concord.models.common import (
    ActorReference,
    ConcordModelError,
    EvidenceLocator,
    EvidenceReference,
    JsonScalar,
    PrivacyPolicy,
    Provenance,
    ScoreTargetReference,
    StatusReason,
    SubjectReference,
    controlled,
    identifier,
    optional_identifier,
    optional_text,
    positive_int,
    require_bool,
    require_text,
    scalar_key,
    timestamp,
    tuple_of_identifiers,
    tuple_of_values,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionSet:
    criterion_set_id: str
    lineage_id: str
    name: str
    purpose: str
    revision: int
    scope: str
    criterion_set_kind: str
    criterion_ids: tuple[str, ...]
    status: str
    created_provenance: Provenance
    standards_profile_id: str | None = None
    supersedes_criterion_set_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.criterion_set_id, "criterion_set_id")
        identifier(self.lineage_id, "lineage_id")
        require_text(self.name, "name")
        require_text(self.purpose, "purpose")
        positive_int(self.revision, "revision")
        controlled(self.scope, "scope", frozenset({"reusable", "activity_specific"}))
        controlled(
            self.criterion_set_kind,
            "criterion_set_kind",
            frozenset({"standard_backed", "local", "mixed"}),
        )
        optional_identifier(self.standards_profile_id, "standards_profile_id")
        object.__setattr__(
            self,
            "criterion_ids",
            tuple_of_identifiers(self.criterion_ids, "criterion_ids", nonempty=True),
        )
        controlled(
            self.status,
            "status",
            frozenset({"draft", "active", "inactive", "archived", "superseded"}),
        )
        optional_identifier(
            self.supersedes_criterion_set_id, "supersedes_criterion_set_id"
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError(
                "created_provenance must be Provenance."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Criterion:
    criterion_id: str
    criterion_set_id: str
    key: str
    label: str
    definition: str
    criterion_kind: str
    supported_target_kinds: tuple[str, ...]
    status: str
    created_provenance: Provenance
    standard_id: str | None = None
    alignment_standard_ids: tuple[str, ...] = ()
    default_scoring_scale_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.criterion_id, "criterion_id")
        identifier(self.criterion_set_id, "criterion_set_id")
        identifier(self.key, "key")
        require_text(self.label, "label")
        require_text(self.definition, "definition")
        kind = controlled(
            self.criterion_kind,
            "criterion_kind",
            frozenset({"standard_backed", "local"}),
        )
        optional_identifier(self.standard_id, "standard_id")
        object.__setattr__(
            self,
            "alignment_standard_ids",
            tuple_of_identifiers(self.alignment_standard_ids, "alignment_standard_ids"),
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
            controlled(target_kind, f"supported_target_kinds[{index}]", allowed_targets)
        object.__setattr__(self, "supported_target_kinds", target_kinds)
        optional_identifier(self.default_scoring_scale_id, "default_scoring_scale_id")
        controlled(
            self.status,
            "status",
            frozenset({"draft", "active", "inactive", "archived"}),
        )
        if kind == "standard_backed" and self.standard_id is None:
            raise ConcordModelError("standard-backed Criterion requires standard_id.")
        if kind == "local" and self.standard_id is not None:
            raise ConcordModelError("local Criterion forbids standard_id.")
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError(
                "created_provenance must be Provenance."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringScaleLevel:
    value: JsonScalar
    label: str
    meaning: str
    position: int | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        scalar_key(self.value)
        require_text(self.label, "label")
        require_text(self.meaning, "meaning")
        if self.position is not None:
            positive_int(self.position, "position")
        optional_text(self.description, "description")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringScale:
    scoring_scale_id: str
    lineage_id: str
    name: str
    revision: int
    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]
    status: str
    created_provenance: Provenance
    intended_use: str | None = None
    aggregation_guidance: str | None = None
    supersedes_scoring_scale_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.scoring_scale_id, "scoring_scale_id")
        identifier(self.lineage_id, "lineage_id")
        require_text(self.name, "name")
        positive_int(self.revision, "revision")
        scale_type = controlled(
            self.scale_type,
            "scale_type",
            frozenset(
                {"numeric", "ordinal", "categorical", "binary", "teacher_defined"}
            ),
        )
        levels = tuple_of_values(
            self.levels, ScoringScaleLevel, "levels", nonempty=True
        )
        object.__setattr__(self, "levels", levels)
        keys = tuple(scalar_key(level.value) for level in levels)
        if len(set(keys)) != len(keys):
            raise ConcordModelError(
                "Scale level values must be type-sensitively unique."
            )
        positions = tuple(
            level.position for level in levels if level.position is not None
        )
        if len(set(positions)) != len(positions):
            raise ConcordModelError("Scale level positions must be unique.")
        if positions and len(positions) != len(levels):
            raise ConcordModelError(
                "Scale level positions must be either complete or absent."
            )
        if scale_type == "numeric" and any(
            isinstance(level.value, bool)
            or not isinstance(level.value, (int, float))
            for level in levels
        ):
            raise ConcordModelError(
                "numeric Scale levels require finite int or float values."
            )
        if scale_type == "ordinal" and any(
            level.position is None for level in levels
        ):
            raise ConcordModelError(
                "ordinal Scale levels require explicit positions."
            )
        if scale_type == "binary" and len(levels) != 2:
            raise ConcordModelError(
                "binary Scale requires exactly two levels."
            )
        optional_text(self.intended_use, "intended_use")
        optional_text(self.aggregation_guidance, "aggregation_guidance")
        controlled(
            self.status,
            "status",
            frozenset({"draft", "active", "inactive", "archived", "superseded"}),
        )
        optional_identifier(
            self.supersedes_scoring_scale_id, "supersedes_scoring_scale_id"
        )
        if not isinstance(self.created_provenance, Provenance):
            raise ConcordModelError(
                "created_provenance must be Provenance."
            )

    def level_for_value(self, value: JsonScalar) -> ScoringScaleLevel | None:
        key = scalar_key(value)
        return next(
            (level for level in self.levels if scalar_key(level.value) == key), None
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreRecord:
    score_record_id: str
    activity_id: str
    target_reference: ScoreTargetReference
    criterion_id: str
    score_kind: str
    scoring_scale_id: str
    disposition: str
    basis: str
    scorer: ActorReference
    scored_at: str
    moderation_complete: bool
    privacy_policy: PrivacyPolicy
    session_id: str | None = None
    standard_id: str | None = None
    value: JsonScalar | None = None
    rationale: str | None = None
    status_reason: StatusReason | None = None
    supersedes_score_record_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.score_record_id, "score_record_id")
        identifier(self.activity_id, "activity_id")
        optional_identifier(self.session_id, "session_id")
        if not isinstance(self.target_reference, ScoreTargetReference):
            raise ConcordModelError("target_reference must be ScoreTargetReference.")
        identifier(self.criterion_id, "criterion_id")
        kind = controlled(
            self.score_kind, "score_kind", frozenset({"standard_backed", "local"})
        )
        optional_identifier(self.standard_id, "standard_id")
        identifier(self.scoring_scale_id, "scoring_scale_id")
        disposition = controlled(
            self.disposition,
            "disposition",
            frozenset(
                {
                    "scored",
                    "insufficient_evidence",
                    "absent",
                    "excused",
                    "not_observed",
                    "not_applicable",
                    "deferred",
                }
            ),
        )
        controlled(
            self.basis,
            "basis",
            frozenset({"linked_evidence", "professional_judgment", "mixed_basis"}),
        )
        if not isinstance(self.scorer, ActorReference):
            raise ConcordModelError("scorer must be ActorReference.")
        timestamp(self.scored_at, "scored_at")
        optional_text(self.rationale, "rationale")
        if self.status_reason is not None and not isinstance(
            self.status_reason, StatusReason
        ):
            raise ConcordModelError("status_reason must be StatusReason.")
        if not isinstance(self.privacy_policy, PrivacyPolicy):
            raise ConcordModelError("privacy_policy must be PrivacyPolicy.")
        require_bool(self.moderation_complete, "moderation_complete")
        optional_identifier(
            self.supersedes_score_record_id, "supersedes_score_record_id"
        )
        if disposition == "scored":
            if self.value is None:
                raise ConcordModelError("scored disposition requires value.")
            scalar_key(self.value)
            if self.status_reason is not None:
                raise ConcordModelError(
                    "scored disposition forbids status_reason."
                )
            if not self.moderation_complete:
                raise ConcordModelError(
                    "scored disposition requires moderation_complete."
                )
        elif self.value is not None:
            raise ConcordModelError("non-score dispositions forbid value.")
        if kind == "standard_backed" and self.standard_id is None:
            raise ConcordModelError("standard-backed Score requires standard_id.")
        if kind == "local" and self.standard_id is not None:
            raise ConcordModelError("local Score forbids standard_id.")
        if (
            self.basis in {"professional_judgment", "mixed_basis"}
            and self.rationale is None
        ):
            raise ConcordModelError(f"{self.basis} requires rationale.")


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreEvidenceLink:
    score_evidence_link_id: str
    score_record_id: str
    evidence_reference: EvidenceReference
    relevance_description: str
    status: str
    created_provenance: Provenance
    evidence_locator: EvidenceLocator | None = None
    subject_context: tuple[SubjectReference, ...] = ()
    significance: str | None = None
    moderation_record_id: str | None = None
    supersedes_score_evidence_link_id: str | None = None

    def __post_init__(self) -> None:
        identifier(self.score_evidence_link_id, "score_evidence_link_id")
        identifier(self.score_record_id, "score_record_id")
        if not isinstance(self.evidence_reference, EvidenceReference):
            raise ConcordModelError("evidence_reference must be EvidenceReference.")
        if self.evidence_locator is not None and not isinstance(
            self.evidence_locator, EvidenceLocator
        ):
            raise ConcordModelError("evidence_locator must be EvidenceLocator.")
        object.__setattr__(
            self,
            "subject_context",
            tuple_of_values(self.subject_context, SubjectReference, "subject_context"),
        )
        require_text(self.relevance_description, "relevance_description")
        if self.significance is not None:
            controlled(
                self.significance,
                "significance",
                frozenset(
                    {
                        "primary",
                        "corroborating",
                        "contextual",
                        "qualifying",
                        "counterevidence",
                        "background",
                    }
                ),
            )
        optional_identifier(self.moderation_record_id, "moderation_record_id")
        controlled(
            self.status,
            "status",
            frozenset({"active", "inactive", "superseded", "rejected"}),
        )
        optional_identifier(
            self.supersedes_score_evidence_link_id, "supersedes_score_evidence_link_id"
        )
