"""Immutable descriptive Activity Score analysis projections."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from pds_core.standards import StandardsLibrary

from concord.models import (
    CorrectionRecord,
    Criterion,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
)
from concord.models.common import JsonScalar, scalar_key
from concord.standards_display import resolve_standard_display
from concord.workflows._score_lineage import (
    current_score_lineage_heads,
    score_lineage_chains,
)
from concord.workflows.activity_read import ActivityReadContext

SCORE_ANALYSIS_BASIS: Final[str] = "current_score_lineage_heads"
SCORE_HISTORY_BASIS: Final[str] = "all_explicit_score_revisions"
SCORE_HISTORY_SCOPE: Final[str] = "teacher_local"
TARGET_DETAIL_SCOPE: Final[str] = "teacher_local"
TargetDisplayLabelResolver = Callable[[ScoreTargetReference], str | None]
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
class TargetScoreResult:
    """One exact current Score row in a teacher-local target detail view."""

    score_record_id: str
    criterion_id: str
    criterion_label: str
    criterion_kind: str
    standard_id: str | None
    scoring_scale_id: str
    scoring_scale_name: str
    scoring_scale_revision: int
    scoring_scale_type: str
    disposition: str
    value: JsonScalar | None
    value_label: str | None
    basis: str
    session_id: str | None
    scored_at: str


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetScoreDetail:
    """Current Score observations for one exact target, teacher-local by default."""

    class_id: str
    activity_id: str
    activity_title: str
    snapshot_revision: int
    snapshot_sha256: str
    score_basis: str
    sharing_scope: str
    target_reference: ScoreTargetReference
    target_label: str
    current_score_count: int
    results: tuple[TargetScoreResult, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetScoreDetailBatch:
    """Batch Target Detail projection from one current-head calculation."""

    details: tuple[TargetScoreDetail, ...]
    current_target_references: tuple[ScoreTargetReference, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreHistoryRevision:
    """One exact Score revision within an explicit historical lineage."""

    score_record_id: str
    revision_number: int
    is_current: bool
    target_reference: ScoreTargetReference
    target_label: str
    criterion_id: str
    criterion_label: str
    criterion_kind: str
    standard_id: str | None
    scoring_scale_id: str
    scoring_scale_name: str
    scoring_scale_revision: int
    scoring_scale_type: str
    disposition: str
    value: JsonScalar | None
    value_label: str | None
    basis: str
    session_id: str | None
    scored_at: str
    supersedes_score_record_id: str | None
    superseded_by_score_record_id: str | None
    correction_id: str | None
    correction_reason: str | None
    corrected_at: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreHistoryLineage:
    """One root-to-head Score revision chain."""

    root_score_record_id: str
    current_score_record_id: str
    revision_count: int
    revisions: tuple[ScoreHistoryRevision, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreHistoryAnalysis:
    """Explicit teacher-local Score history separate from current analysis."""

    class_id: str
    activity_id: str
    activity_title: str
    snapshot_revision: int
    snapshot_sha256: str
    score_basis: str
    sharing_scope: str
    lineage_count: int
    revision_count: int
    lineages: tuple[ScoreHistoryLineage, ...]


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
    display = resolve_standard_display(standard_id, standards_library)
    return display.code or display.standard_id, display.code, display.short_name


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


def _native_target_label(
    context: ActivityReadContext,
    target: ScoreTargetReference,
) -> str | None:
    if target.target_kind == "concord_group":
        group = next(
            (
                item
                for item in context.graph.groups
                if item.group_id == target.target_id
            ),
            None,
        )
        return None if group is None else group.label
    if target.target_kind == "concord_session":
        session = next(
            (
                item
                for item in context.graph.sessions
                if item.session_id == target.target_id
            ),
            None,
        )
        if session is None:
            return None
        return session.label or f"Session {session.sequence}"
    if target.target_kind == "concord_activity":
        if target.target_id == context.activity.activity_id:
            return context.activity.title
        return None
    return None


def _target_label(
    context: ActivityReadContext,
    target: ScoreTargetReference,
    resolver: TargetDisplayLabelResolver | None,
) -> str:
    if resolver is not None:
        resolved = resolver(target)
        if resolved is not None and resolved.strip():
            return resolved.strip()
    native = _native_target_label(context, target)
    return native if native is not None else target.target_id


def _target_score_detail_from_current_records(
    context: ActivityReadContext,
    target_reference: ScoreTargetReference,
    current: tuple[ScoreRecord, ...],
    *,
    criterion_by_id: dict[str, Criterion],
    scale_by_id: dict[str, ScoringScale],
    target_label_resolver: TargetDisplayLabelResolver | None,
) -> TargetScoreDetail:
    results: list[TargetScoreResult] = []
    for score in current:
        criterion = _require_criterion(criterion_by_id, score.criterion_id)
        scale = _require_scale(scale_by_id, score.scoring_scale_id)
        value_label: str | None = None
        if score.disposition == "scored":
            if score.value is None:
                raise ValueError(
                    "scored target-detail observation requires a value"
                )
            level = scale.level_for_value(score.value)
            if level is None:
                raise ValueError(
                    "Target detail encountered a scored value absent from its "
                    "exact Scale revision"
                )
            value_label = level.label
        results.append(
            TargetScoreResult(
                score_record_id=score.score_record_id,
                criterion_id=criterion.criterion_id,
                criterion_label=criterion.label,
                criterion_kind=criterion.criterion_kind,
                standard_id=criterion.standard_id,
                scoring_scale_id=scale.scoring_scale_id,
                scoring_scale_name=scale.name,
                scoring_scale_revision=scale.revision,
                scoring_scale_type=scale.scale_type,
                disposition=score.disposition,
                value=score.value,
                value_label=value_label,
                basis=score.basis,
                session_id=score.session_id,
                scored_at=score.scored_at,
            )
        )

    ordered = tuple(
        sorted(
            results,
            key=lambda item: (
                item.criterion_label.casefold(),
                item.criterion_id,
                item.scoring_scale_revision,
                item.scoring_scale_id,
                item.score_record_id,
            ),
        )
    )
    return TargetScoreDetail(
        class_id=context.work.class_id,
        activity_id=context.activity.activity_id,
        activity_title=context.activity.title,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        score_basis=SCORE_ANALYSIS_BASIS,
        sharing_scope=TARGET_DETAIL_SCOPE,
        target_reference=target_reference,
        target_label=_target_label(
            context,
            target_reference,
            target_label_resolver,
        ),
        current_score_count=len(ordered),
        results=ordered,
    )


def target_score_detail_batch_from_context(
    context: ActivityReadContext,
    target_references: tuple[ScoreTargetReference, ...],
    *,
    target_label_resolver: TargetDisplayLabelResolver | None = None,
) -> TargetScoreDetailBatch:
    """Project many Target Details from one exact current-head calculation."""
    criterion_by_id = {
        item.criterion_id: item for item in context.graph.criteria
    }
    scale_by_id = {
        item.scoring_scale_id: item for item in context.graph.scoring_scales
    }
    activity_records = tuple(
        item
        for item in context.graph.score_records
        if item.activity_id == context.activity.activity_id
    )
    current_heads = current_score_lineage_heads(activity_records)

    current_by_target: dict[ScoreTargetReference, list[ScoreRecord]] = {}
    for score in current_heads:
        current_by_target.setdefault(score.target_reference, []).append(score)

    details = tuple(
        _target_score_detail_from_current_records(
            context,
            target_reference,
            tuple(current_by_target.get(target_reference, ())),
            criterion_by_id=criterion_by_id,
            scale_by_id=scale_by_id,
            target_label_resolver=target_label_resolver,
        )
        for target_reference in target_references
    )
    current_target_references = tuple(
        sorted(
            current_by_target,
            key=lambda target: (
                _TARGET_KIND_RANK[target.target_kind],
                target.target_id,
                target.owning_system,
                target.contract_version or "",
            ),
        )
    )
    return TargetScoreDetailBatch(
        details=details,
        current_target_references=current_target_references,
    )


def target_score_detail_from_context(
    context: ActivityReadContext,
    target_reference: ScoreTargetReference,
    *,
    target_label_resolver: TargetDisplayLabelResolver | None = None,
) -> TargetScoreDetail:
    """Project one target's current Score heads without inferring requirements."""
    batch = target_score_detail_batch_from_context(
        context,
        (target_reference,),
        target_label_resolver=target_label_resolver,
    )
    return batch.details[0]

def _score_revision_correction(
    corrections: tuple[CorrectionRecord, ...],
    predecessor_id: str,
    successor_id: str,
) -> CorrectionRecord | None:
    matches = tuple(
        item
        for item in corrections
        if item.correction_type == "score_revision"
        and item.target_reference.record_kind == "score_record"
        and item.target_reference.record_id == predecessor_id
        and item.replacement_reference is not None
        and item.replacement_reference.record_kind == "score_record"
        and item.replacement_reference.record_id == successor_id
    )
    if len(matches) > 1:
        raise ValueError(
            "Score history encountered duplicate correction audits for "
            f"{predecessor_id} -> {successor_id}"
        )
    return None if not matches else matches[0]


def score_history_analysis_from_context(
    context: ActivityReadContext,
    *,
    target_label_resolver: TargetDisplayLabelResolver | None = None,
) -> ScoreHistoryAnalysis:
    """Project all explicit Score revisions without mixing them into current counts."""
    records = tuple(
        item
        for item in context.graph.score_records
        if item.activity_id == context.activity.activity_id
    )
    chains = score_lineage_chains(records)
    current_ids = {
        item.score_record_id
        for item in current_score_lineage_heads(records)
    }
    criterion_by_id = {
        item.criterion_id: item for item in context.graph.criteria
    }
    scale_by_id = {
        item.scoring_scale_id: item for item in context.graph.scoring_scales
    }

    lineages: list[ScoreHistoryLineage] = []
    for chain in chains:
        revisions: list[ScoreHistoryRevision] = []
        for index, score in enumerate(chain):
            criterion = _require_criterion(criterion_by_id, score.criterion_id)
            scale = _require_scale(scale_by_id, score.scoring_scale_id)
            successor_id = (
                chain[index + 1].score_record_id
                if index + 1 < len(chain)
                else None
            )
            correction: CorrectionRecord | None = None
            if score.supersedes_score_record_id is not None:
                correction = _score_revision_correction(
                    context.graph.correction_records,
                    score.supersedes_score_record_id,
                    score.score_record_id,
                )
            value_label: str | None = None
            if score.disposition == "scored":
                if score.value is None:
                    raise ValueError(
                        "scored Score history observation requires a value"
                    )
                level = scale.level_for_value(score.value)
                if level is None:
                    raise ValueError(
                        "Score history encountered a scored value absent from "
                        "its exact Scale revision"
                    )
                value_label = level.label
            revisions.append(
                ScoreHistoryRevision(
                    score_record_id=score.score_record_id,
                    revision_number=index + 1,
                    is_current=score.score_record_id in current_ids,
                    target_reference=score.target_reference,
                    target_label=_target_label(
                        context,
                        score.target_reference,
                        target_label_resolver,
                    ),
                    criterion_id=criterion.criterion_id,
                    criterion_label=criterion.label,
                    criterion_kind=criterion.criterion_kind,
                    standard_id=criterion.standard_id,
                    scoring_scale_id=scale.scoring_scale_id,
                    scoring_scale_name=scale.name,
                    scoring_scale_revision=scale.revision,
                    scoring_scale_type=scale.scale_type,
                    disposition=score.disposition,
                    value=score.value,
                    value_label=value_label,
                    basis=score.basis,
                    session_id=score.session_id,
                    scored_at=score.scored_at,
                    supersedes_score_record_id=score.supersedes_score_record_id,
                    superseded_by_score_record_id=successor_id,
                    correction_id=(
                        None if correction is None else correction.correction_id
                    ),
                    correction_reason=(
                        None if correction is None else correction.reason
                    ),
                    corrected_at=(
                        None if correction is None else correction.corrected_at
                    ),
                )
            )
        lineages.append(
            ScoreHistoryLineage(
                root_score_record_id=chain[0].score_record_id,
                current_score_record_id=chain[-1].score_record_id,
                revision_count=len(revisions),
                revisions=tuple(revisions),
            )
        )

    ordered = tuple(
        sorted(
            lineages,
            key=lambda item: item.root_score_record_id,
        )
    )
    return ScoreHistoryAnalysis(
        class_id=context.work.class_id,
        activity_id=context.activity.activity_id,
        activity_title=context.activity.title,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        score_basis=SCORE_HISTORY_BASIS,
        sharing_scope=SCORE_HISTORY_SCOPE,
        lineage_count=len(ordered),
        revision_count=sum(item.revision_count for item in ordered),
        lineages=ordered,
    )


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
    "SCORE_HISTORY_BASIS",
    "SCORE_HISTORY_SCOPE",
    "TARGET_DETAIL_SCOPE",
    "ActivityScoreAnalysis",
    "ActivityScoreObservation",
    "CriterionScaleTargetAnalysis",
    "CriterionScoreAnalysis",
    "DispositionDistribution",
    "ScaleValueDistribution",
    "ScoreHistoryAnalysis",
    "ScoreHistoryLineage",
    "ScoreHistoryRevision",
    "StandardCriterionAnalysis",
    "StandardScoreAnalysis",
    "TargetDisplayLabelResolver",
    "TargetKindScoreCount",
    "TargetScoreDetail",
    "TargetScoreDetailBatch",
    "TargetScoreResult",
    "activity_score_analysis_from_context",
    "score_history_analysis_from_context",
    "target_score_detail_batch_from_context",
    "target_score_detail_from_context",
]
