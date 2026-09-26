"""Explicit routine Artifact Review persistence bound to an inspected snapshot."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from pds_core.standards import StandardsLibrary

from concord.workflows.artifact_review import (
    AddArtifactReviewRequest,
    ArtifactReviewMutationResult,
    add_artifact_review,
)
from concord.workflows.artifact_routine_review import ArtifactRoutineReviewContext
from concord.workflows.artifact_routine_review_profiles import (
    ArtifactRoutineReviewValues,
)
from concord.workflows.context import Clock
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import WorkflowActor

_ROUTINE_FIXED_VALUES = {
    "readability_judgment": "readable",
    "page_completeness_judgment": "complete",
    "filing_judgment": "correct",
    "author_judgment": "confirmed",
    "subject_judgment": "confirmed",
    "relevance_judgment": "relevant",
    "moderation_requirement": "not_required",
}
_ROUTINE_OUTCOMES = frozenset(
    {
        ("ready", "ready"),
        ("ready_with_qualification", "ready_with_qualification"),
    }
)


def _new_artifact_review_id() -> str:
    return f"artifact-review-{uuid4().hex}"


def _require_routine_values(values: ArtifactRoutineReviewValues) -> None:
    for field_name, required_value in _ROUTINE_FIXED_VALUES.items():
        if getattr(values, field_name) != required_value:
            raise ConcordWorkflowValidationError(
                "Routine Artifact Review can record only the explicit ready or "
                "ready-with-qualification profile."
            )
    if (values.scoring_readiness, values.review_outcome) not in _ROUTINE_OUTCOMES:
        raise ConcordWorkflowValidationError(
            "Routine Artifact Review can record only the explicit ready or "
            "ready-with-qualification profile."
        )


def record_routine_artifact_review(
    context: ArtifactRoutineReviewContext,
    values: ArtifactRoutineReviewValues,
    *,
    actor: WorkflowActor,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactReviewMutationResult:
    """Record one explicitly approved routine Review from an exact read snapshot."""
    if not context.eligibility.quick_review_eligible:
        reasons = "; ".join(context.eligibility.exception_reasons)
        detail = f" Reasons: {reasons}" if reasons else ""
        raise ConcordWorkflowValidationError(
            "Artifact is not eligible for routine Quick Review." + detail
        )
    if context.current_review is not None or not context.first_review_pending:
        raise ConcordWorkflowValidationError(
            "Routine Quick Review may record only an Artifact's first Review."
        )

    _require_routine_values(values)

    return add_artifact_review(
        AddArtifactReviewRequest(
            class_id=context.class_id,
            activity_id=context.activity_id,
            artifact_instance_id=context.artifact.artifact_instance_id,
            artifact_review_id=_new_artifact_review_id(),
            readability_judgment=values.readability_judgment,
            page_completeness_judgment=values.page_completeness_judgment,
            filing_judgment=values.filing_judgment,
            author_judgment=values.author_judgment,
            subject_judgment=values.subject_judgment,
            privacy_judgment=values.privacy_judgment,
            relevance_judgment=values.relevance_judgment,
            moderation_requirement=values.moderation_requirement,
            scoring_readiness=values.scoring_readiness,
            review_outcome=values.review_outcome,
            privacy_policy=values.privacy_policy,
            expected_snapshot_revision=context.snapshot_revision,
            actor=actor,
            notes=values.notes,
        ),
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )


__all__ = ["record_routine_artifact_review"]
