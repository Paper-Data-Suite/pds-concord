"""Read-only preparation of one explicit routine Artifact Score preview."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from concord.models import (
    EvidenceReference,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
    SubjectReference,
)
from concord.workflows.artifact_routine_scoring import ArtifactRoutineScoringContext
from concord.workflows.artifact_routine_scoring_selection import (
    routine_criteria_for_target,
    routine_scale_options,
)
from concord.workflows.errors import ConcordWorkflowValidationError

ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION: Final[str] = (
    "Returned Artifact evidence for this Score."
)
ROUTINE_SCORE_BASIS: Final[str] = "linked_evidence"
ROUTINE_SCORE_DISPOSITION: Final[str] = "scored"
ROUTINE_SCORE_PRIVACY: Final[PrivacyPolicy] = PrivacyPolicy(
    classification="teacher_restricted"
)
_ALLOWED_SIGNIFICANCE: Final[frozenset[str]] = frozenset(
    {
        "primary",
        "corroborating",
        "contextual",
        "qualifying",
        "counterevidence",
        "background",
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutineScorePreparationRequest:
    """Explicit teacher choices required to prepare one routine Score preview."""

    target_reference: ScoreTargetReference
    criterion_id: str
    scoring_scale_id: str
    value: str | int | float | bool
    session_id: str | None = None
    subject_context: tuple[SubjectReference, ...] = ()
    relevance_description: str = ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION
    significance: str | None = None


@dataclass(frozen=True, slots=True)
class RoutineScoreEvidencePreview:
    """The exact idless native Artifact Evidence Link semantics to be written."""

    evidence_reference: EvidenceReference
    subject_context: tuple[SubjectReference, ...]
    relevance_description: str
    significance: str | None
    evidence_locator: None
    moderation_required: bool
    moderation_requirement: str
    moderation_record_id: None


@dataclass(frozen=True, slots=True)
class RoutineScorePreview:
    """Complete teacher-significant routine Score proposal before mutation."""

    class_id: str
    activity_id: str
    artifact_instance_id: str
    target_reference: ScoreTargetReference
    criterion_id: str
    criterion_label: str
    score_kind: str
    standard_id: str | None
    scoring_scale_id: str
    scoring_scale_name: str
    value: str | int | float | bool
    selected_level: ScoringScaleLevel
    session_id: str | None
    disposition: str
    basis: str
    rationale: None
    status_reason: None
    privacy_policy: PrivacyPolicy
    evidence: RoutineScoreEvidencePreview
    existing_current_score_ids: tuple[str, ...]
    snapshot_revision: int
    snapshot_sha256: str


def _subject_key(
    reference: SubjectReference,
) -> tuple[str, str, str, str | None]:
    return (
        reference.subject_kind,
        reference.owning_system,
        reference.subject_id,
        reference.contract_version,
    )


def _criterion_subject_options(
    context: ArtifactRoutineScoringContext,
    criterion_id: str,
) -> tuple[SubjectReference, ...]:
    """Return confirmed current Subjects applicable to this exact Criterion."""
    candidates: list[SubjectReference] = []
    seen: set[tuple[str, str, str, str | None]] = set()
    for subject in context.current_subjects:
        if subject.confirmation_status != "confirmed":
            continue
        if subject.criterion_id not in {None, criterion_id}:
            continue
        reference = subject.subject_reference
        key = _subject_key(reference)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(reference)
    return tuple(candidates)


def routine_subject_context_options(
    context: ArtifactRoutineScoringContext,
    target_reference: ScoreTargetReference,
    criterion_id: str,
) -> tuple[SubjectReference, ...]:
    """Expose typed Subject choices after explicit target and Criterion choice."""
    criteria = routine_criteria_for_target(context, target_reference)
    if not any(item.criterion_id == criterion_id for item in criteria):
        raise ConcordWorkflowValidationError(
            "Routine Criterion must support the explicitly selected Score target."
        )
    return _criterion_subject_options(context, criterion_id)


def _validate_subject_context(
    context: ArtifactRoutineScoringContext,
    target_reference: ScoreTargetReference,
    criterion_id: str,
    selected: tuple[SubjectReference, ...],
) -> tuple[SubjectReference, ...]:
    options = routine_subject_context_options(
        context,
        target_reference,
        criterion_id,
    )
    allowed = {_subject_key(item) for item in options}
    seen: set[tuple[str, str, str, str | None]] = set()
    result: list[SubjectReference] = []
    for reference in selected:
        key = _subject_key(reference)
        if key in seen:
            raise ConcordWorkflowValidationError(
                "Routine Subject context must not contain duplicates."
            )
        if key not in allowed:
            raise ConcordWorkflowValidationError(
                "Routine Subject context must be explicitly selected from current "
                "confirmed Artifact Subjects applicable to this Criterion."
            )
        seen.add(key)
        result.append(reference)
    return tuple(result)


def _validate_session(
    context: ArtifactRoutineScoringContext,
    session_id: str | None,
) -> str | None:
    if session_id is None:
        return None
    if any(
        item.session_id == session_id and item.activity_id == context.activity_id
        for item in context.current_sessions
    ):
        return session_id
    raise ConcordWorkflowValidationError(
        "Routine Score Session must identify a current Session in this Activity."
    )


def _validate_relevance(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ConcordWorkflowValidationError(
            "Routine evidence relevance must be nonempty without surrounding "
            "whitespace."
        )
    return value


def _validate_significance(value: str | None) -> str | None:
    if value is None:
        return None
    if value not in _ALLOWED_SIGNIFICANCE:
        raise ConcordWorkflowValidationError(
            "Routine evidence significance is not a canonical Score Evidence "
            "Link value."
        )
    return value


def _matching_current_score_ids(
    context: ArtifactRoutineScoringContext,
    target_reference: ScoreTargetReference,
    criterion_id: str,
) -> tuple[str, ...]:
    """Surface existing current Scores without treating them as completion state."""
    return tuple(
        item.score_record_id
        for item in context.current_scores
        if item.target_reference == target_reference
        and item.criterion_id == criterion_id
    )


def prepare_routine_score_preview(
    context: ArtifactRoutineScoringContext,
    request: RoutineScorePreparationRequest,
) -> RoutineScorePreview:
    """Prepare one exact scored/linked-evidence proposal without mutation."""
    criteria = routine_criteria_for_target(context, request.target_reference)
    criterion = next(
        (item for item in criteria if item.criterion_id == request.criterion_id),
        None,
    )
    if criterion is None:
        raise ConcordWorkflowValidationError(
            "Routine Criterion must support the explicitly selected Score target."
        )

    scale_options = routine_scale_options(
        context,
        request.target_reference,
        request.criterion_id,
    )
    scale = next(
        (
            item
            for item in scale_options.scales
            if item.scoring_scale_id == request.scoring_scale_id
        ),
        None,
    )
    if scale is None:
        raise ConcordWorkflowValidationError(
            "Routine Scoring Scale must be an explicitly selected current active "
            "Scale."
        )
    level = scale.level_for_value(request.value)
    if level is None:
        raise ConcordWorkflowValidationError(
            "Routine Score value must match one exact level in the explicitly "
            "selected Scale revision."
        )

    session_id = _validate_session(context, request.session_id)
    subjects = _validate_subject_context(
        context,
        request.target_reference,
        request.criterion_id,
        request.subject_context,
    )
    relevance = _validate_relevance(request.relevance_description)
    significance = _validate_significance(request.significance)

    review = context.current_review
    review_requirement = None if review is None else review.moderation_requirement
    evidence_requires = context.evidence_reference.moderation_requirement == "required"
    moderation_required = evidence_requires or review_requirement == "required"
    if moderation_required:
        raise ConcordWorkflowValidationError(
            "Routine scored Artifact evidence still requires Moderation; use the "
            "current Moderation/Advanced Score path before recording a Score."
        )
    moderation_requirement = (
        "completed" if review_requirement == "completed" else "not_required"
    )

    evidence = RoutineScoreEvidencePreview(
        evidence_reference=context.evidence_reference,
        subject_context=subjects,
        relevance_description=relevance,
        significance=significance,
        evidence_locator=None,
        moderation_required=False,
        moderation_requirement=moderation_requirement,
        moderation_record_id=None,
    )
    return RoutineScorePreview(
        class_id=context.class_id,
        activity_id=context.activity_id,
        artifact_instance_id=context.artifact.artifact_instance_id,
        target_reference=request.target_reference,
        criterion_id=criterion.criterion_id,
        criterion_label=criterion.label,
        score_kind=criterion.criterion_kind,
        standard_id=criterion.standard_id,
        scoring_scale_id=scale.scoring_scale_id,
        scoring_scale_name=scale.name,
        value=request.value,
        selected_level=level,
        session_id=session_id,
        disposition=ROUTINE_SCORE_DISPOSITION,
        basis=ROUTINE_SCORE_BASIS,
        rationale=None,
        status_reason=None,
        privacy_policy=ROUTINE_SCORE_PRIVACY,
        evidence=evidence,
        existing_current_score_ids=_matching_current_score_ids(
            context,
            request.target_reference,
            request.criterion_id,
        ),
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
    )


__all__ = [
    "ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION",
    "ROUTINE_SCORE_BASIS",
    "ROUTINE_SCORE_DISPOSITION",
    "ROUTINE_SCORE_PRIVACY",
    "RoutineScoreEvidencePreview",
    "RoutineScorePreparationRequest",
    "RoutineScorePreview",
    "prepare_routine_score_preview",
    "routine_subject_context_options",
]
