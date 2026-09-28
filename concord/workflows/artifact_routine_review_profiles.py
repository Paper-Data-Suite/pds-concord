"""Explicit non-persistent routine Artifact Review value bundles."""

from __future__ import annotations

from dataclasses import dataclass

from concord.models import ActorReference, ArtifactReview, PrivacyPolicy

_DEFAULT_PRIVACY = PrivacyPolicy(classification="teacher_restricted")
_VALIDATION_REVIEWER = ActorReference(
    actor_kind="authorized_adult",
    actor_id="routine-review-validation",
    owning_system="concord",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactRoutineReviewValues:
    """Complete explicit Review values proposed for teacher approval."""

    readability_judgment: str
    page_completeness_judgment: str
    filing_judgment: str
    author_judgment: str
    subject_judgment: str
    privacy_judgment: str
    relevance_judgment: str
    moderation_requirement: str
    scoring_readiness: str
    review_outcome: str
    privacy_policy: PrivacyPolicy
    notes: str | None = None

    def __post_init__(self) -> None:
        # Reuse the canonical ArtifactReview model as the legality authority
        # without creating or persisting canonical state.
        ArtifactReview(
            artifact_review_id="routine-review-validation",
            artifact_instance_id="routine-artifact-validation",
            reviewer=_VALIDATION_REVIEWER,
            reviewed_at="2000-01-01T00:00:00+00:00",
            readability_judgment=self.readability_judgment,
            page_completeness_judgment=self.page_completeness_judgment,
            filing_judgment=self.filing_judgment,
            author_judgment=self.author_judgment,
            subject_judgment=self.subject_judgment,
            privacy_judgment=self.privacy_judgment,
            relevance_judgment=self.relevance_judgment,
            moderation_requirement=self.moderation_requirement,
            scoring_readiness=self.scoring_readiness,
            review_outcome=self.review_outcome,
            notes=self.notes,
            privacy_policy=self.privacy_policy,
        )


def routine_ready_review_values(
    *,
    privacy_judgment: str = "teacher_restricted",
    privacy_policy: PrivacyPolicy | None = None,
) -> ArtifactRoutineReviewValues:
    """Return the complete ordinary ready-for-scoring Review proposal."""
    return ArtifactRoutineReviewValues(
        readability_judgment="readable",
        page_completeness_judgment="complete",
        filing_judgment="correct",
        author_judgment="confirmed",
        subject_judgment="confirmed",
        privacy_judgment=privacy_judgment,
        relevance_judgment="relevant",
        moderation_requirement="not_required",
        scoring_readiness="ready",
        review_outcome="ready",
        notes=None,
        privacy_policy=privacy_policy or _DEFAULT_PRIVACY,
    )


def routine_qualified_review_values(
    notes: str,
    *,
    privacy_judgment: str = "teacher_restricted",
    privacy_policy: PrivacyPolicy | None = None,
) -> ArtifactRoutineReviewValues:
    """Return the complete ready-with-qualification Review proposal."""
    return ArtifactRoutineReviewValues(
        readability_judgment="readable",
        page_completeness_judgment="complete",
        filing_judgment="correct",
        author_judgment="confirmed",
        subject_judgment="confirmed",
        privacy_judgment=privacy_judgment,
        relevance_judgment="relevant",
        moderation_requirement="not_required",
        scoring_readiness="ready_with_qualification",
        review_outcome="ready_with_qualification",
        notes=notes,
        privacy_policy=privacy_policy or _DEFAULT_PRIVACY,
    )


__all__ = [
    "ArtifactRoutineReviewValues",
    "routine_qualified_review_values",
    "routine_ready_review_values",
]
