"""Read-only target, Criterion, and Scale choices for routine Artifact scoring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from concord.models.common import (
    ConcordRecordReference,
    ParticipantReference,
    ScoreTargetReference,
    SubjectReference,
)
from concord.models.scoring import Criterion, ScoringScale
from concord.workflows.artifact_routine_scoring import ArtifactRoutineScoringContext
from concord.workflows.errors import ConcordWorkflowValidationError

_TARGET_KIND_ORDER: Final[tuple[str, ...]] = (
    "core_student",
    "concord_group",
    "concord_session",
    "concord_artifact_instance",
    "concord_activity",
)
_SUBJECT_TARGET_KINDS: Final[frozenset[str]] = frozenset(_TARGET_KIND_ORDER)
_DEFAULT_SCALE_STATUSES: Final[frozenset[str]] = frozenset(
    {"valid", "not_configured", "missing_or_historical", "not_active"}
)


@dataclass(frozen=True, slots=True)
class RoutineScoreTargetCandidate:
    """One current target candidate presented for an explicit teacher choice."""

    target_reference: ScoreTargetReference
    candidate_sources: tuple[str, ...]
    compatible_criterion_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoutineScoreTargetOptions:
    """Candidate targets plus every target kind supported by routine Criteria."""

    candidates: tuple[RoutineScoreTargetCandidate, ...]
    supported_target_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RoutineScoringScaleOptions:
    """Current active Scales and the exact configured Criterion default state."""

    scales: tuple[ScoringScale, ...]
    configured_default_scoring_scale_id: str | None
    default_scale: ScoringScale | None
    default_scale_status: str

    def __post_init__(self) -> None:
        if self.default_scale_status not in _DEFAULT_SCALE_STATUSES:
            raise ValueError("Unsupported routine default Scale status.")


def _require_routine_context(context: ArtifactRoutineScoringContext) -> None:
    if context.eligibility.routine_scoring_eligible:
        return
    detail = "; ".join(context.eligibility.exception_reasons)
    suffix = f": {detail}" if detail else "."
    raise ConcordWorkflowValidationError(
        f"Routine scoring is unavailable{suffix}"
    )


def _routine_criteria(
    context: ArtifactRoutineScoringContext,
) -> tuple[Criterion, ...]:
    """Return Criteria whose Activity semantics can legally support a Score."""
    orientation = context.scoring_orientation
    focus_standard_ids = frozenset(context.focus_standard_ids)
    candidates: list[Criterion] = []
    for criterion in context.eligible_criteria:
        if criterion.criterion_kind == "standard_backed":
            if orientation not in {"standards_based", "mixed"}:
                continue
            if criterion.standard_id not in focus_standard_ids:
                continue
        elif criterion.criterion_kind == "local":
            if orientation not in {"local_criteria_only", "mixed"}:
                continue
        else:  # pragma: no cover - native Criterion rejects unknown kinds.
            continue
        candidates.append(criterion)
    return tuple(candidates)


def _target_key(reference: ScoreTargetReference) -> tuple[str, str, str, str | None]:
    return (
        reference.target_kind,
        reference.owning_system,
        reference.target_id,
        reference.contract_version,
    )


def _target_from_subject(
    reference: SubjectReference,
) -> ScoreTargetReference | None:
    if reference.subject_kind not in _SUBJECT_TARGET_KINDS:
        return None
    if reference.subject_kind == "core_student":
        if reference.owning_system != "core":
            return None
    elif reference.owning_system != "concord":
        return None
    return ScoreTargetReference(
        target_kind=reference.subject_kind,
        target_id=reference.subject_id,
        owning_system=reference.owning_system,
        contract_version=reference.contract_version,
    )


def _target_from_author(author: object) -> tuple[ScoreTargetReference, ...]:
    if getattr(author, "attribution_status", None) != "confirmed":
        return ()
    targets: list[ScoreTargetReference] = []
    reference = getattr(author, "author_reference", None)
    if (
        isinstance(reference, ParticipantReference)
        and reference.participant_kind == "core_student"
        and reference.owning_system == "core"
    ):
        targets.append(
            ScoreTargetReference(
                target_kind="core_student",
                target_id=reference.participant_id,
                owning_system="core",
            )
        )
    elif (
        isinstance(reference, ConcordRecordReference)
        and reference.record_kind == "group"
    ):
        targets.append(
            ScoreTargetReference(
                target_kind="concord_group",
                target_id=reference.record_id,
                owning_system="concord",
                contract_version=reference.contract_version,
            )
        )
    represented_group_id = getattr(author, "represented_group_id", None)
    if represented_group_id is not None:
        targets.append(
            ScoreTargetReference(
                target_kind="concord_group",
                target_id=represented_group_id,
                owning_system="concord",
            )
        )
    return tuple(targets)


def _criterion_ids_for_kind(
    criteria: tuple[Criterion, ...],
    target_kind: str,
) -> tuple[str, ...]:
    return tuple(
        item.criterion_id
        for item in criteria
        if target_kind in item.supported_target_kinds
    )


def routine_target_options(
    context: ArtifactRoutineScoringContext,
) -> RoutineScoreTargetOptions:
    """Project likely current target candidates without selecting any target."""
    _require_routine_context(context)
    criteria = _routine_criteria(context)
    if not criteria:
        raise ConcordWorkflowValidationError(
            "Routine scoring has no Criterion compatible with the current Activity."
        )
    supported_target_kinds = tuple(
        kind
        for kind in _TARGET_KIND_ORDER
        if any(kind in item.supported_target_kinds for item in criteria)
    )
    supported = frozenset(supported_target_kinds)
    projected: dict[
        tuple[str, str, str, str | None],
        tuple[ScoreTargetReference, list[str]],
    ] = {}

    def add(reference: ScoreTargetReference, source: str) -> None:
        if reference.target_kind not in supported:
            return
        key = _target_key(reference)
        current = projected.get(key)
        if current is None:
            projected[key] = (reference, [source])
            return
        if source not in current[1]:
            current[1].append(source)

    for subject in context.subject_context_candidates:
        target = _target_from_subject(subject)
        if target is not None:
            add(target, "artifact_subject")

    for author in context.current_authors:
        for target in _target_from_author(author):
            add(target, "artifact_author")

    artifact_group_id = context.artifact.group_id
    if artifact_group_id is not None and any(
        item.group_id == artifact_group_id
        and item.activity_id == context.activity_id
        for item in context.current_groups
    ):
        add(
            ScoreTargetReference(
                target_kind="concord_group",
                target_id=artifact_group_id,
                owning_system="concord",
            ),
            "artifact_group",
        )

    artifact_session_id = context.artifact.session_id
    if artifact_session_id is not None and any(
        item.session_id == artifact_session_id
        and item.activity_id == context.activity_id
        for item in context.current_sessions
    ):
        add(
            ScoreTargetReference(
                target_kind="concord_session",
                target_id=artifact_session_id,
                owning_system="concord",
            ),
            "artifact_session",
        )

    add(
        ScoreTargetReference(
            target_kind="concord_artifact_instance",
            target_id=context.artifact.artifact_instance_id,
            owning_system="concord",
        ),
        "selected_artifact",
    )
    add(
        ScoreTargetReference(
            target_kind="concord_activity",
            target_id=context.activity_id,
            owning_system="concord",
        ),
        "current_activity",
    )

    candidates = tuple(
        RoutineScoreTargetCandidate(
            target_reference=reference,
            candidate_sources=tuple(sources),
            compatible_criterion_ids=_criterion_ids_for_kind(
                criteria,
                reference.target_kind,
            ),
        )
        for reference, sources in projected.values()
    )
    return RoutineScoreTargetOptions(
        candidates=candidates,
        supported_target_kinds=supported_target_kinds,
    )


def routine_criteria_for_target(
    context: ArtifactRoutineScoringContext,
    target_reference: ScoreTargetReference,
) -> tuple[Criterion, ...]:
    """Return routine Criteria compatible with one explicitly chosen candidate."""
    options = routine_target_options(context)
    key = _target_key(target_reference)
    candidate = next(
        (
            item
            for item in options.candidates
            if _target_key(item.target_reference) == key
        ),
        None,
    )
    if candidate is None:
        raise ConcordWorkflowValidationError(
            "Routine Score target must be explicitly chosen from current candidates."
        )
    allowed_ids = frozenset(candidate.compatible_criterion_ids)
    return tuple(
        item
        for item in _routine_criteria(context)
        if item.criterion_id in allowed_ids
    )


def routine_scale_options(
    context: ArtifactRoutineScoringContext,
    target_reference: ScoreTargetReference,
    criterion_id: str,
) -> RoutineScoringScaleOptions:
    """Resolve current active Scale choices after explicit target and Criterion."""
    criteria = routine_criteria_for_target(context, target_reference)
    criterion = next(
        (item for item in criteria if item.criterion_id == criterion_id),
        None,
    )
    if criterion is None:
        raise ConcordWorkflowValidationError(
            "Routine Criterion must support the explicitly selected Score target."
        )

    active_scales = tuple(
        item for item in context.current_scoring_scales if item.status == "active"
    )
    configured_id = criterion.default_scoring_scale_id
    if configured_id is None:
        return RoutineScoringScaleOptions(
            scales=active_scales,
            configured_default_scoring_scale_id=None,
            default_scale=None,
            default_scale_status="not_configured",
        )

    current_default = next(
        (
            item
            for item in context.current_scoring_scales
            if item.scoring_scale_id == configured_id
        ),
        None,
    )
    if current_default is None:
        status = "missing_or_historical"
        default_scale = None
    elif current_default.status != "active":
        status = "not_active"
        default_scale = None
    else:
        status = "valid"
        default_scale = current_default

    return RoutineScoringScaleOptions(
        scales=active_scales,
        configured_default_scoring_scale_id=configured_id,
        default_scale=default_scale,
        default_scale_status=status,
    )


__all__ = [
    "RoutineScoreTargetCandidate",
    "RoutineScoreTargetOptions",
    "RoutineScoringScaleOptions",
    "routine_criteria_for_target",
    "routine_scale_options",
    "routine_target_options",
]
