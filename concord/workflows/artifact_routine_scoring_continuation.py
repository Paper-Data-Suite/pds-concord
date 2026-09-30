"""Post-commit reload and continuation for routine Artifact scoring."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from concord.models import Criterion, ScoreTargetReference, SubjectReference
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringContext,
    inspect_artifact_routine_scoring,
)
from concord.workflows.artifact_routine_scoring_preparation import (
    ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
    RoutineScorePreparationRequest,
    RoutineScorePreview,
    prepare_routine_score_preview,
)
from concord.workflows.artifact_routine_scoring_selection import (
    routine_criteria_for_target,
    routine_target_options,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.score_recording import ScoreMutationResult


@dataclass(frozen=True, slots=True)
class RoutineScoringContinuation:
    """Fresh post-commit state for an optional Score-another-Criterion flow."""

    context: ArtifactRoutineScoringContext
    completed_score_record_id: str
    completed_criterion_id: str
    retained_target_reference: ScoreTargetReference | None
    retained_session_id: str | None
    target_context_retained: bool
    session_context_retained: bool
    available_criteria: tuple[Criterion, ...]
    dropped_context_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContinuedRoutineScorePreparationRequest:
    """Fresh academic choices for another Score on the reloaded Artifact context."""

    criterion_id: str
    scoring_scale_id: str
    value: str | int | float | bool
    subject_context: tuple[SubjectReference, ...] = ()
    relevance_description: str = ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION
    significance: str | None = None


def _validate_completed_mutation(
    preview: RoutineScorePreview,
    result: ScoreMutationResult,
) -> None:
    if result.commit.no_op:
        raise ConcordWorkflowValidationError(
            "Routine scoring continuation requires a successful Score mutation."
        )
    if result.commit.snapshot_revision <= preview.snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Successful routine Score mutation did not advance the Activity snapshot."
        )
    if len(result.score_evidence_link_ids) != 1:
        raise ConcordWorkflowValidationError(
            "Routine scoring continuation requires exactly one canonical Evidence Link."
        )


def _retained_session(
    context: ArtifactRoutineScoringContext,
    prior_session_id: str | None,
) -> tuple[str | None, bool, str | None]:
    if prior_session_id is None:
        return None, True, None
    if any(
        item.session_id == prior_session_id
        and item.activity_id == context.activity_id
        for item in context.current_sessions
    ):
        return prior_session_id, True, None
    return (
        None,
        False,
        "The previously selected Session is no longer current in this Activity.",
    )


def reload_routine_scoring_after_score(
    preview: RoutineScorePreview,
    result: ScoreMutationResult,
    *,
    workspace_root: str | Path | None = None,
) -> RoutineScoringContinuation:
    """Reload canonical Activity state after one successful routine Score commit."""
    _validate_completed_mutation(preview, result)
    context = inspect_artifact_routine_scoring(
        preview.class_id,
        preview.activity_id,
        preview.artifact_instance_id,
        workspace_root=workspace_root,
    )
    if context.snapshot_revision < result.commit.snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Reloaded routine scoring state predates the completed Score mutation."
        )
    if context.snapshot_revision <= preview.snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Routine scoring continuation did not reload state newer than its preview."
        )

    dropped: list[str] = []
    retained_target: ScoreTargetReference | None = None
    criteria: tuple[Criterion, ...] = ()
    if context.eligibility.routine_scoring_eligible:
        try:
            options = routine_target_options(context)
            retained_target = next(
                (
                    item.target_reference
                    for item in options.candidates
                    if item.target_reference == preview.target_reference
                ),
                None,
            )
            if retained_target is None:
                dropped.append(
                    "The previously selected Score target is no longer a current "
                    "routine candidate."
                )
            else:
                criteria = routine_criteria_for_target(context, retained_target)
        except ConcordWorkflowValidationError as error:
            retained_target = None
            criteria = ()
            dropped.append(
                "Current routine target/Criterion context could not be retained: "
                f"{error}"
            )
    else:
        detail = "; ".join(context.eligibility.exception_reasons)
        dropped.append(
            "Routine scoring is no longer eligible after reload"
            + (f": {detail}" if detail else ".")
        )

    retained_session, session_retained, session_reason = _retained_session(
        context,
        preview.session_id,
    )
    if session_reason is not None:
        dropped.append(session_reason)

    return RoutineScoringContinuation(
        context=context,
        completed_score_record_id=result.score_record_id,
        completed_criterion_id=preview.criterion_id,
        retained_target_reference=retained_target,
        retained_session_id=retained_session,
        target_context_retained=retained_target is not None,
        session_context_retained=session_retained,
        available_criteria=criteria,
        dropped_context_reasons=tuple(dropped),
    )


def prepare_next_routine_score_preview(
    continuation: RoutineScoringContinuation,
    request: ContinuedRoutineScorePreparationRequest,
) -> RoutineScorePreview:
    """Prepare another explicit Criterion/value from the fresh post-commit state."""
    if not continuation.context.eligibility.routine_scoring_eligible:
        raise ConcordWorkflowValidationError(
            "Routine scoring is no longer eligible after the completed Score."
        )
    target = continuation.retained_target_reference
    if target is None:
        raise ConcordWorkflowValidationError(
            "The prior Score target is no longer current; choose a target again."
        )
    if not continuation.session_context_retained:
        raise ConcordWorkflowValidationError(
            "The prior Session context changed; review Session context before another "
            "routine Score."
        )
    if request.criterion_id == continuation.completed_criterion_id:
        raise ConcordWorkflowValidationError(
            "Score another Criterion requires a fresh Criterion; use Score revision "
            "or Advanced Score recording for the completed Criterion."
        )

    return prepare_routine_score_preview(
        continuation.context,
        RoutineScorePreparationRequest(
            target_reference=target,
            criterion_id=request.criterion_id,
            scoring_scale_id=request.scoring_scale_id,
            value=request.value,
            session_id=continuation.retained_session_id,
            subject_context=request.subject_context,
            relevance_description=request.relevance_description,
            significance=request.significance,
        ),
    )


__all__ = [
    "ContinuedRoutineScorePreparationRequest",
    "RoutineScoringContinuation",
    "prepare_next_routine_score_preview",
    "reload_routine_scoring_after_score",
]
