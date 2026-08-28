"""Read-only Review and Moderation attention for Concord Artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from concord.models import EvidenceReference
from concord.workflows.artifact_attribution import list_artifact_subjects
from concord.workflows.artifact_collection import inspect_artifact_collection_state
from concord.workflows.artifact_review import current_artifact_review
from concord.workflows.moderation import assess_moderation_requirement

# These outcomes explicitly leave the current Review in a teacher-actionable
# administrative state. ``not_suitable_for_scoring`` is deliberately absent:
# it may be a completed judgment rather than unfinished Review work.
_ACTIONABLE_REVIEW_OUTCOMES: Final[frozenset[str]] = frozenset(
    {
        "incomplete",
        "unreadable",
        "misrouted",
        "duplicate",
        "awaiting_correction",
        "awaiting_additional_evidence",
    }
)


@dataclass(frozen=True, slots=True)
class ArtifactReviewAttentionState:
    """Privacy-minimal current Review/Moderation state for one Artifact."""

    class_id: str
    activity_id: str
    artifact_instance_id: str
    first_review_pending: bool
    review_attention_pending: bool
    moderation_pending: bool
    post_moderation_review_pending: bool


def inspect_artifact_review_attention_state(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactReviewAttentionState:
    """Interpret current Review/Moderation state without writing workspace data."""
    current = current_artifact_review(
        class_id,
        activity_id,
        artifact_instance_id,
        workspace_root=workspace_root,
    )
    if current is None:
        collection = inspect_artifact_collection_state(
            class_id,
            activity_id,
            artifact_instance_id,
            workspace_root=workspace_root,
        )
        # A merely existing or expected Artifact is not Review attention. The
        # exact returned evidence must already have reached a valid assembly.
        return ArtifactReviewAttentionState(
            class_id=class_id,
            activity_id=activity_id,
            artifact_instance_id=artifact_instance_id,
            first_review_pending=collection.assembly_state == "assembled",
            review_attention_pending=False,
            moderation_pending=False,
            post_moderation_review_pending=False,
        )

    review_attention_pending = (
        current.review_outcome in _ACTIONABLE_REVIEW_OUTCOMES
    )
    moderation_pending = False
    post_moderation_review_pending = False
    if current.moderation_requirement == "required":
        subjects = list_artifact_subjects(
            class_id,
            activity_id,
            artifact_instance_id=artifact_instance_id,
            workspace_root=workspace_root,
        )
        subject_context = tuple(item.subject_reference for item in subjects)
        assessment = assess_moderation_requirement(
            class_id,
            activity_id,
            EvidenceReference(
                evidence_kind="artifact_instance",
                owning_system="concord",
                record_id=artifact_instance_id,
            ),
            subject_context=subject_context,
            workspace_root=workspace_root,
        )
        # assess_moderation_requirement already limits these to current records
        # applicable to the exact evidence + Subject scope. Any such explicit
        # decision satisfies the *need to moderate*; whether it permits scoring
        # remains a separate Score concern owned by score_recording.
        if assessment.applicable_moderation_records:
            post_moderation_review_pending = True
        else:
            moderation_pending = True

    return ArtifactReviewAttentionState(
        class_id=class_id,
        activity_id=activity_id,
        artifact_instance_id=artifact_instance_id,
        first_review_pending=False,
        review_attention_pending=review_attention_pending,
        moderation_pending=moderation_pending,
        post_moderation_review_pending=post_moderation_review_pending,
    )


__all__ = [
    "ArtifactReviewAttentionState",
    "inspect_artifact_review_attention_state",
]
