"""Immutable descriptive Activity Score analysis projections."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Final

from pds_core.standards import StandardsLibrary

from concord.models import Criterion, ScoreRecord, ScoreTargetReference, ScoringScale
from concord.models.common import JsonScalar, scalar_key
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
_TARGET_KIND_RANK: Final[dict[str, int]] = {
    value: index for index, value in enumerate(_TARGET_KIND_ORDER)
}
_DISPOSITION_ORDER: Final[tuple[str, ...]] = (
    "scored",
    "insufficient_evidence",
    "absent",
    "excused",
    "not_observed",
    "not_applicable",
    "deferred",
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
class ScaleValueDistribution:
    """One exact native Scale value count within one analysis slice."""

    value: JsonScalar
    label: str
    count: int
    denominator: int
    percentage: str


@dataclass(frozen=True, slots=True, kw_only=True)
class DispositionDistribution:
    """One Score disposition count within one analysis slice."""

    disposition: str
    count: int
    denominator: int
    percentage: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionScaleTargetAnalysis:
    """Descriptive counts for one exact Criterion/Scale/target-kind slice."""

    criterion_id: str
    criterion_label: str
    criterion_kind: str
    standard_id: str | None
    scoring_scale_id: str
    scoring_scale_lineage_id: str
    scoring_scale_name: str
    scoring_scale_revision: int
    scoring_scale_type: str
    target_kind: str
    current_judgment_count: int
    scored_count: int
    non_score_count: int
    value_distributions: tuple[ScaleValueDistribution, ...]
    disposition_distributions: tuple[DispositionDistribution, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionScoreAnalysis:
    """All represented current Score slices for one exact Criterion."""

    criterion_id: str
    criterion_label: str
    criterion_kind: str
    standard_id: str | None
    current_judgment_count: int
    slices: tuple[CriterionScaleTargetAnalysis, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardCriterionAnalysis:
    """One represented standard-backed Criterion without proficiency inference."""

    criterion_id: str
    criterion_label: str
    current_judgment_count: int
    slices: tuple[CriterionScaleTargetAnalysis, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class StandardScoreAnalysis:
    """Descriptive grouping of represented Criteria for one durable Standard ID."""

    standard_id: str
    standard_label: str
    standard_code: str | None
    standard_short_name: str | None
    criteria: tuple[StandardCriterionAnalysis, ...]


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
    represented_criterion_count: int
    represented_scoring_scale_count: int
    criterion_analyses: tuple[CriterionScoreAnalysis, ...]
    standard_analyses: tuple[StandardScoreAnalysis, ...]
    current_scores: tuple[ActivityScoreObservation, ...]


def _percentage(count: int, denominator: int) -> str:
    """Return a deterministic one-decimal percentage using integer half-up rounding."""
    if denominator <= 0:
        raise ValueError("percentage denominator must be positive")
    scaled, remainder = divmod(count * 1000, denominator)
    if remainder * 2 >= denominator:
        scaled += 1
    return f"{scaled // 10}.{scaled % 10}"


def _require_criterion(
    criterion_by_id: dict[str, Criterion],
    criterion_id: str,
) -> Criterion:
    try:
        return criterion_by_id[criterion_id]
    except KeyError as error:
        raise ValueError(
            f"Score analysis references unavailable Criterion: {criterion_id}"
        ) from error


def _require_scale(
    scale_by_id: dict[str, ScoringScale],
    scoring_scale_id: str,
) -> ScoringScale:
    try:
        return scale_by_id[scoring_scale_id]
    except KeyError as error:
        raise ValueError(
            f"Score analysis references unavailable Scoring Scale: {scoring_scale_id}"
        ) from error


def _value_distributions(
    records: tuple[ScoreRecord, ...],
    scale: ScoringScale,
) -> tuple[ScaleValueDistribution, ...]:
    scored = tuple(item for item in records if item.disposition == "scored")
    denominator = len(scored)
    if denominator == 0:
        return ()

    counts: Counter[tuple[type[object], JsonScalar]] = Counter()
    for score in scored:
        if score.value is None:
            raise ValueError("scored Score analysis observation requires a value")
        counts[scalar_key(score.value)] += 1

    distributions: list[ScaleValueDistribution] = []
    represented_count = 0
    for level in scale.levels:
        count = counts.get(scalar_key(level.value), 0)
        if count == 0:
            continue
        represented_count += count
        distributions.append(
            ScaleValueDistribution(
                value=level.value,
                label=level.label,
                count=count,
                denominator=denominator,
                percentage=_percentage(count, denominator),
            )
        )
    if represented_count != denominator:
        raise ValueError(
            "Score analysis encountered a scored value absent from its "
            "exact Scale revision"
        )
    return tuple(distributions)


def _disposition_distributions(
    records: tuple[ScoreRecord, ...],
) -> tuple[DispositionDistribution, ...]:
    denominator = len(records)
    if denominator == 0:
        return ()
    counts = Counter(item.disposition for item in records)
    return tuple(
        DispositionDistribution(
            disposition=disposition,
            count=counts[disposition],
            denominator=denominator,
            percentage=_percentage(counts[disposition], denominator),
        )
        for disposition in _DISPOSITION_ORDER
        if counts[disposition]
    )


def _criterion_analyses(
    context: ActivityReadContext,
    current_heads: tuple[ScoreRecord, ...],
) -> tuple[CriterionScoreAnalysis, ...]:
    criterion_by_id = {
        item.criterion_id: item for item in context.graph.criteria
    }
    scale_by_id = {
        item.scoring_scale_id: item for item in context.graph.scoring_scales
    }
    grouped: dict[tuple[str, str, str], list[ScoreRecord]] = defaultdict(list)
    for score in current_heads:
        grouped[
            (
                score.criterion_id,
                score.scoring_scale_id,
                score.target_reference.target_kind,
            )
        ].append(score)

    slices_by_criterion: dict[
        str, list[CriterionScaleTargetAnalysis]
    ] = defaultdict(list)
    for criterion_id, scoring_scale_id, target_kind in sorted(
        grouped,
        key=lambda item: (
            item[0],
            item[1],
            _TARGET_KIND_RANK[item[2]],
            item[2],
        ),
    ):
        criterion = _require_criterion(criterion_by_id, criterion_id)
        scale = _require_scale(scale_by_id, scoring_scale_id)
        records = tuple(
            sorted(
                grouped[(criterion_id, scoring_scale_id, target_kind)],
                key=lambda item: item.score_record_id,
            )
        )
        scored_count = sum(item.disposition == "scored" for item in records)
        slices_by_criterion[criterion_id].append(
            CriterionScaleTargetAnalysis(
                criterion_id=criterion.criterion_id,
                criterion_label=criterion.label,
                criterion_kind=criterion.criterion_kind,
                standard_id=criterion.standard_id,
                scoring_scale_id=scale.scoring_scale_id,
                scoring_scale_lineage_id=scale.lineage_id,
                scoring_scale_name=scale.name,
                scoring_scale_revision=scale.revision,
                scoring_scale_type=scale.scale_type,
                target_kind=target_kind,
                current_judgment_count=len(records),
                scored_count=scored_count,
                non_score_count=len(records) - scored_count,
                value_distributions=_value_distributions(records, scale),
                disposition_distributions=_disposition_distributions(records),
            )
        )

    analyses: list[CriterionScoreAnalysis] = []
    for criterion_id in sorted(slices_by_criterion):
        criterion = _require_criterion(criterion_by_id, criterion_id)
        slices = tuple(slices_by_criterion[criterion_id])
        analyses.append(
            CriterionScoreAnalysis(
                criterion_id=criterion.criterion_id,
                criterion_label=criterion.label,
                criterion_kind=criterion.criterion_kind,
                standard_id=criterion.standard_id,
                current_judgment_count=sum(
                    item.current_judgment_count for item in slices
                ),
                slices=slices,
            )
        )
    return tuple(analyses)


def _standard_display(
    standard_id: str,
    standards_library: StandardsLibrary | None,
) -> tuple[str, str | None, str | None]:
    if standards_library is None:
        return standard_id, None, None
    definition = next(
        (
            item
            for item in standards_library.standards
            if item.standard_id == standard_id
        ),
        None,
    )
    if definition is None:
        return standard_id, None, None
    return definition.code, definition.code, definition.short_name


def _standard_analyses(
    criterion_analyses: tuple[CriterionScoreAnalysis, ...],
    standards_library: StandardsLibrary | None,
) -> tuple[StandardScoreAnalysis, ...]:
    grouped: dict[str, list[CriterionScoreAnalysis]] = defaultdict(list)
    for criterion in criterion_analyses:
        if criterion.criterion_kind != "standard_backed":
            continue
        if criterion.standard_id is None:
            raise ValueError(
                "standard-backed Criterion analysis requires durable standard_id"
            )
        grouped[criterion.standard_id].append(criterion)

    result: list[StandardScoreAnalysis] = []
    for standard_id in sorted(grouped):
        standard_label, standard_code, standard_short_name = _standard_display(
            standard_id,
            standards_library,
        )
        criteria = tuple(
            StandardCriterionAnalysis(
                criterion_id=item.criterion_id,
                criterion_label=item.criterion_label,
                current_judgment_count=item.current_judgment_count,
                slices=item.slices,
            )
            for item in sorted(
                grouped[standard_id],
                key=lambda value: value.criterion_id,
            )
        )
        result.append(
            StandardScoreAnalysis(
                standard_id=standard_id,
                standard_label=standard_label,
                standard_code=standard_code,
                standard_short_name=standard_short_name,
                criteria=criteria,
            )
        )
    return tuple(result)


def activity_score_analysis_from_context(
    context: ActivityReadContext,
    *,
    standards_library: StandardsLibrary | None = None,
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
    criterion_analyses = _criterion_analyses(context, current_heads)
    standard_analyses = _standard_analyses(
        criterion_analyses,
        standards_library,
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
        represented_criterion_count=len(criterion_analyses),
        represented_scoring_scale_count=len(
            {item.scoring_scale_id for item in current_heads}
        ),
        criterion_analyses=criterion_analyses,
        standard_analyses=standard_analyses,
        current_scores=observations,
    )


__all__ = [
    "SCORE_ANALYSIS_BASIS",
    "ActivityScoreAnalysis",
    "ActivityScoreObservation",
    "CriterionScaleTargetAnalysis",
    "CriterionScoreAnalysis",
    "DispositionDistribution",
    "ScaleValueDistribution",
    "StandardCriterionAnalysis",
    "StandardScoreAnalysis",
    "TargetKindScoreCount",
    "activity_score_analysis_from_context",
]
