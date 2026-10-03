"""Immutable descriptive Activity Score analysis projections."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Final

from concord.models import ScoreTargetReference
from concord.workflows._score_lineage import current_score_lineage_heads
from concord.workflows.activity_read import ActivityReadContext

SCORE_ANALYSIS_BASIS: Final[str] = "current_score_lineage_heads"
_TARGET_KIND_ORDER: Final[tuple[str, ...]] = (
    "core_student",
    "concord_group",
    "concord_artifact_instance",
    "concord_session",
    "concord_activity",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetKindScoreCount:
    """Count of explicit current Score heads for one exact target kind."""

    target_kind: str
    score_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityScoreObservation:
    """Privacy-minimized descriptive projection of one current Score head."""

    score_record_id: str
    target_reference: ScoreTargetReference
    criterion_id: str
    score_kind: str
    standard_id: str | None
    scoring_scale_id: str
    disposition: str
    value: str | int | float | bool | None
    basis: str
    session_id: str | None
    scored_at: str
    supersedes_score_record_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityScoreAnalysis:
    """One immutable descriptive view of current Scores at one Activity state."""

    class_id: str
    activity_id: str
    activity_title: str
    snapshot_revision: int
    snapshot_sha256: str
    score_basis: str
    current_score_count: int
    target_kind_counts: tuple[TargetKindScoreCount, ...]
    current_scores: tuple[ActivityScoreObservation, ...]


def activity_score_analysis_from_context(
    context: ActivityReadContext,
) -> ActivityScoreAnalysis:
    """Project current explicit Score heads from one exact verified context."""
    activity_id = context.activity.activity_id
    activity_records = tuple(
        item
        for item in context.graph.score_records
        if item.activity_id == activity_id
    )
    current_heads = tuple(
        sorted(
            current_score_lineage_heads(activity_records),
            key=lambda item: item.score_record_id,
        )
    )

    counts = Counter(item.target_reference.target_kind for item in current_heads)
    target_kind_counts = tuple(
        TargetKindScoreCount(target_kind=target_kind, score_count=counts[target_kind])
        for target_kind in _TARGET_KIND_ORDER
        if counts[target_kind]
    )
    observations = tuple(
        ActivityScoreObservation(
            score_record_id=item.score_record_id,
            target_reference=item.target_reference,
            criterion_id=item.criterion_id,
            score_kind=item.score_kind,
            standard_id=item.standard_id,
            scoring_scale_id=item.scoring_scale_id,
            disposition=item.disposition,
            value=item.value,
            basis=item.basis,
            session_id=item.session_id,
            scored_at=item.scored_at,
            supersedes_score_record_id=item.supersedes_score_record_id,
        )
        for item in current_heads
    )
    return ActivityScoreAnalysis(
        class_id=context.work.class_id,
        activity_id=activity_id,
        activity_title=context.activity.title,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        score_basis=SCORE_ANALYSIS_BASIS,
        current_score_count=len(observations),
        target_kind_counts=target_kind_counts,
        current_scores=observations,
    )


__all__ = [
    "SCORE_ANALYSIS_BASIS",
    "ActivityScoreAnalysis",
    "ActivityScoreObservation",
    "TargetKindScoreCount",
    "activity_score_analysis_from_context",
]
