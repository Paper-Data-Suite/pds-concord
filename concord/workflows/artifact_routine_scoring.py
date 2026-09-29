"""Read-only routine scoring projection for one reviewed native Artifact."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from concord.models import (
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactReview,
    ArtifactSubject,
    Criterion,
    CriterionSet,
    EvidenceReference,
    Group,
    GroupMembership,
    ScoreRecord,
    ScoringScale,
    Session,
    SubjectReference,
)
from concord.workflows._collaboration import work_ref
from concord.workflows.activity_read import (
    ActivityReadContext,
    load_activity_read_context,
)
from concord.workflows.artifact_attribution import (
    _current_authors,
    _current_subjects,
    _ensure_author_not_duplicate,
    _ensure_subject_not_duplicate,
    _require_artifact,
    _validate_author_semantics,
    _validate_subject_semantics,
)
from concord.workflows.artifact_review import _current_review_for_artifact
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.criterion_sets import _criterion_set_heads
from concord.workflows.errors import ConcordWorkflowError, ConcordWorkflowNotFoundError
from concord.workflows.score_recording import _score_heads
from concord.workflows.scoring_scales import _scale_heads

_SCORING_READY_OUTCOMES: Final[frozenset[str]] = frozenset(
    {"ready", "ready_with_qualification"}
)
_SCORING_READY_STATES: Final[frozenset[str]] = frozenset(
    {"ready", "ready_with_qualification"}
)


@dataclass(frozen=True, slots=True)
class ArtifactRoutineScoringEligibility:
    """Mechanical eligibility for the reviewed-Artifact routine scoring path."""

    routine_scoring_eligible: bool
    exception_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArtifactRoutineScoringContext:
    """One selected Artifact projected from one exact verified Activity snapshot."""

    class_id: str
    activity_id: str
    artifact: ArtifactInstance
    current_review: ArtifactReview | None
    current_authors: tuple[ArtifactAuthor, ...]
    current_subjects: tuple[ArtifactSubject, ...]
    subject_context_candidates: tuple[SubjectReference, ...]
    evidence_reference: EvidenceReference
    selected_criterion_sets: tuple[CriterionSet, ...]
    eligible_criteria: tuple[Criterion, ...]
    current_scoring_scales: tuple[ScoringScale, ...]
    current_sessions: tuple[Session, ...]
    current_groups: tuple[Group, ...]
    current_memberships: tuple[GroupMembership, ...]
    current_scores: tuple[ScoreRecord, ...]
    eligibility: ArtifactRoutineScoringEligibility
    snapshot_revision: int
    snapshot_sha256: str


def native_artifact_evidence_reference(
    artifact: ArtifactInstance,
) -> EvidenceReference:
    """Return the exact native Concord evidence identity for one Artifact."""
    return EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id=artifact.artifact_instance_id,
    )


def _append_once(reasons: list[str], message: str) -> None:
    if message not in reasons:
        reasons.append(message)


def _subject_reference_key(
    reference: SubjectReference,
) -> tuple[str, str, str, str | None]:
    """Return the stable semantic identity of one Subject reference."""
    return (
        reference.subject_kind,
        reference.owning_system,
        reference.subject_id,
        reference.contract_version,
    )


def _relationship_projection(
    context: ActivityReadContext,
    artifact: ArtifactInstance,
    authors: tuple[ArtifactAuthor, ...],
    subjects: tuple[ArtifactSubject, ...],
) -> tuple[tuple[SubjectReference, ...], tuple[str, ...]]:
    reasons: list[str] = []
    subject_candidates: list[SubjectReference] = []
    seen_subject_candidate_keys: set[tuple[str, str, str, str | None]] = set()

    for author in authors:
        try:
            _validate_author_semantics(
                context.root,
                context.work.class_id,
                context.graph,
                artifact,
                author,
            )
            _ensure_author_not_duplicate(
                context.graph,
                author,
                exclude_id=author.artifact_author_id,
            )
        except ConcordWorkflowError:
            _append_once(
                reasons,
                "Current Artifact Author state is invalid or conflicting.",
            )

    for subject in subjects:
        valid = True
        try:
            _validate_subject_semantics(
                context.root,
                context.work.class_id,
                context.graph,
                artifact,
                subject,
            )
            _ensure_subject_not_duplicate(
                context.graph,
                subject,
                exclude_id=subject.artifact_subject_id,
            )
        except ConcordWorkflowError:
            valid = False
            _append_once(
                reasons,
                "Current Artifact Subject state is invalid or conflicting.",
            )
        if valid and subject.confirmation_status == "confirmed":
            reference = subject.subject_reference
            key = _subject_reference_key(reference)
            if key not in seen_subject_candidate_keys:
                seen_subject_candidate_keys.add(key)
                subject_candidates.append(reference)

    return tuple(subject_candidates), tuple(reasons)


def _selected_scoring_contracts(
    context: ActivityReadContext,
) -> tuple[
    tuple[CriterionSet, ...],
    tuple[Criterion, ...],
    tuple[ScoringScale, ...],
    tuple[str, ...],
]:
    reasons: list[str] = []
    selected_ids = frozenset(context.activity.criterion_set_ids)
    criterion_set_heads = _criterion_set_heads(context.graph)
    head_ids = frozenset(item.criterion_set_id for item in criterion_set_heads)
    selected_sets = tuple(
        item for item in criterion_set_heads if item.criterion_set_id in selected_ids
    )

    if selected_ids - head_ids:
        reasons.append(
            "Selected Criterion Set state is missing or historical; use Advanced "
            "Score recording after correcting Activity scoring setup."
        )
    if any(item.status != "active" for item in selected_sets):
        reasons.append(
            "Selected Criterion Set state is not active; use Advanced Score "
            "recording after correcting Activity scoring setup."
        )

    active_set_ids = frozenset(
        item.criterion_set_id for item in selected_sets if item.status == "active"
    )
    eligible_criteria = tuple(
        item
        for item in context.graph.criteria
        if item.criterion_set_id in active_set_ids and item.status == "active"
    )
    if not eligible_criteria:
        reasons.append(
            "No active scoring Criterion is available for the current Activity."
        )

    current_scales = _scale_heads(context.graph)
    if not any(item.status == "active" for item in current_scales):
        reasons.append(
            "No active current Scoring Scale is available for routine scoring."
        )

    return selected_sets, eligible_criteria, current_scales, tuple(reasons)


def _project_artifact_routine_scoring_from_context(
    context: ActivityReadContext,
    artifact_instance_id: str,
) -> ArtifactRoutineScoringContext:
    """Project one reviewed Artifact without reloading the verified Activity graph."""
    artifact = _require_artifact(
        context.graph,
        context.work.work_id,
        artifact_instance_id,
    )
    current_review = _current_review_for_artifact(
        context.graph,
        artifact.artifact_instance_id,
    )
    current_authors = tuple(
        item
        for item in _current_authors(context.graph)
        if item.artifact_instance_id == artifact.artifact_instance_id
    )
    current_subjects = tuple(
        item
        for item in _current_subjects(context.graph)
        if item.artifact_instance_id == artifact.artifact_instance_id
    )
    subject_context_candidates, relationship_reasons = _relationship_projection(
        context,
        artifact,
        current_authors,
        current_subjects,
    )
    evidence_reference = native_artifact_evidence_reference(artifact)
    (
        selected_criterion_sets,
        eligible_criteria,
        current_scoring_scales,
        scoring_contract_reasons,
    ) = _selected_scoring_contracts(context)

    reasons: list[str] = []
    if context.activity.scoring_orientation == "evidence_only":
        reasons.append("Evidence-only Activities cannot record Scores.")
    if current_review is None:
        reasons.append(
            "A current explicit Artifact Review is required before routine scoring."
        )
    else:
        if current_review.review_outcome not in _SCORING_READY_OUTCOMES:
            reasons.append(
                "The current Artifact Review outcome does not permit routine scoring."
            )
        if current_review.scoring_readiness not in _SCORING_READY_STATES:
            reasons.append(
                "The current Artifact Review is not ready for scoring."
            )
        if current_review.moderation_requirement == "required":
            reasons.append(
                "The current Artifact Review still requires Moderation before scoring."
            )
    reasons.extend(relationship_reasons)
    reasons.extend(scoring_contract_reasons)

    eligibility = ArtifactRoutineScoringEligibility(
        routine_scoring_eligible=not reasons,
        exception_reasons=tuple(reasons),
    )
    return ArtifactRoutineScoringContext(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        artifact=artifact,
        current_review=current_review,
        current_authors=current_authors,
        current_subjects=current_subjects,
        subject_context_candidates=subject_context_candidates,
        evidence_reference=evidence_reference,
        selected_criterion_sets=selected_criterion_sets,
        eligible_criteria=eligible_criteria,
        current_scoring_scales=current_scoring_scales,
        current_sessions=context.graph.sessions,
        current_groups=context.graph.groups,
        current_memberships=context.graph.memberships,
        current_scores=_score_heads(context.graph),
        eligibility=eligibility,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
    )


def inspect_artifact_routine_scoring(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactRoutineScoringContext:
    """Inspect routine scoring state from one exact current Activity snapshot."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    require_core_class(root, class_id)
    context = load_activity_read_context(
        root,
        work_ref(class_id, activity_id),
    )
    return _project_artifact_routine_scoring_from_context(
        context,
        artifact_instance_id,
    )


__all__ = [
    "ArtifactRoutineScoringContext",
    "ArtifactRoutineScoringEligibility",
    "inspect_artifact_routine_scoring",
    "native_artifact_evidence_reference",
]
