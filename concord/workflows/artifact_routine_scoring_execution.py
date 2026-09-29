"""Canonical execution of one confirmed prepared routine Artifact Score."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from pds_core.standards import StandardsLibrary

from concord.workflows.artifact_routine_scoring_preparation import (
    ROUTINE_SCORE_BASIS,
    ROUTINE_SCORE_DISPOSITION,
    ROUTINE_SCORE_PRIVACY,
    RoutineScorePreview,
)
from concord.workflows.context import Clock
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import WorkflowActor
from concord.workflows.score_recording import (
    AddScoreRequest,
    ScoreEvidenceLinkSpec,
    ScoreMutationResult,
    add_score,
)


def _new_record_id(prefix: str) -> str:
    """Generate one opaque routine record identity immediately before mutation."""
    return f"{prefix}-{uuid4().hex}"


def _validate_routine_preview(preview: RoutineScorePreview) -> None:
    """Fail closed if a manually constructed preview escapes routine semantics."""
    if preview.disposition != ROUTINE_SCORE_DISPOSITION:
        raise ConcordWorkflowValidationError(
            "Routine Score execution requires the scored disposition."
        )
    if preview.basis != ROUTINE_SCORE_BASIS:
        raise ConcordWorkflowValidationError(
            "Routine Score execution requires linked-evidence basis."
        )
    if preview.rationale is not None or preview.status_reason is not None:
        raise ConcordWorkflowValidationError(
            "Routine scored linked-evidence preview forbids rationale/status reason."
        )
    if preview.privacy_policy != ROUTINE_SCORE_PRIVACY:
        raise ConcordWorkflowValidationError(
            "Routine Score preview carries an unexpected privacy policy."
        )
    if (
        type(preview.selected_level.value) is not type(preview.value)
        or preview.selected_level.value != preview.value
    ):
        raise ConcordWorkflowValidationError(
            "Routine Score preview value no longer matches its selected Scale level."
        )

    evidence = preview.evidence
    reference = evidence.evidence_reference
    if (
        reference.evidence_kind != "artifact_instance"
        or reference.owning_system != "concord"
        or reference.record_id != preview.artifact_instance_id
    ):
        raise ConcordWorkflowValidationError(
            "Routine Score evidence must identify the exact selected Concord Artifact."
        )
    if evidence.evidence_locator is not None:
        raise ConcordWorkflowValidationError(
            "Routine native Artifact evidence must not invent an Evidence Locator."
        )
    if evidence.moderation_required or evidence.moderation_record_id is not None:
        raise ConcordWorkflowValidationError(
            "Routine first-entry execution cannot bypass required Moderation."
        )
    if evidence.moderation_requirement not in {"not_required", "completed"}:
        raise ConcordWorkflowValidationError(
            "Routine Score preview has an invalid Moderation requirement state."
        )
    relevance = evidence.relevance_description
    if not relevance or relevance != relevance.strip():
        raise ConcordWorkflowValidationError(
            "Routine Score evidence relevance must remain a visible valid description."
        )


def record_prepared_routine_score(
    preview: RoutineScorePreview,
    *,
    actor: WorkflowActor,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ScoreMutationResult:
    """Commit one confirmed routine preview through canonical Score authority."""
    _validate_routine_preview(preview)
    if preview.existing_current_score_ids:
        raise ConcordWorkflowValidationError(
            "A current Score already exists for this routine target and Criterion; "
            "use Score revision or Advanced Score recording instead of creating a "
            "parallel current Score."
        )

    score_record_id = _new_record_id("score")
    score_evidence_link_id = _new_record_id("score-link")
    evidence = preview.evidence
    request = AddScoreRequest(
        class_id=preview.class_id,
        activity_id=preview.activity_id,
        score_record_id=score_record_id,
        target_reference=preview.target_reference,
        criterion_id=preview.criterion_id,
        scoring_scale_id=preview.scoring_scale_id,
        session_id=preview.session_id,
        disposition=preview.disposition,
        basis=preview.basis,
        privacy_policy=preview.privacy_policy,
        expected_snapshot_revision=preview.snapshot_revision,
        actor=actor,
        value=preview.value,
        rationale=preview.rationale,
        status_reason=preview.status_reason,
        evidence_links=(
            ScoreEvidenceLinkSpec(
                score_evidence_link_id=score_evidence_link_id,
                evidence_reference=evidence.evidence_reference,
                evidence_locator=evidence.evidence_locator,
                subject_context=evidence.subject_context,
                relevance_description=evidence.relevance_description,
                significance=evidence.significance,
                moderation_record_id=evidence.moderation_record_id,
            ),
        ),
    )
    return add_score(
        request,
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )


__all__ = ["record_prepared_routine_score"]
