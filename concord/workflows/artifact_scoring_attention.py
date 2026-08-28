"""Read-only scoring-readiness attention for Concord Artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from concord.workflows.activity import show_activity
from concord.workflows.artifact_review import current_artifact_review

_SCORING_READY_OUTCOMES: Final[frozenset[str]] = frozenset(
    {"ready", "ready_with_qualification"}
)
_SCORING_READY_STATES: Final[frozenset[str]] = frozenset(
    {"ready", "ready_with_qualification"}
)


@dataclass(frozen=True, slots=True)
class ArtifactScoringAttentionState:
    """Privacy-minimal mechanical Score readiness for one reviewed Artifact."""

    class_id: str
    activity_id: str
    artifact_instance_id: str
    scoring_ready: bool


def inspect_artifact_scoring_attention_state(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactScoringAttentionState:
    """Return whether explicit current Review state makes evidence score-ready.

    This does not infer that a Score is missing, due, or expected for any target.
    It also does not inspect Score records as a completion matrix because Concord
    supports several independent Score target kinds.
    """
    activity = show_activity(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    ).summary
    if activity.scoring_orientation == "evidence_only":
        return ArtifactScoringAttentionState(
            class_id=class_id,
            activity_id=activity_id,
            artifact_instance_id=artifact_instance_id,
            scoring_ready=False,
        )

    review = current_artifact_review(
        class_id,
        activity_id,
        artifact_instance_id,
        workspace_root=workspace_root,
    )
    ready = bool(
        review is not None
        and review.review_outcome in _SCORING_READY_OUTCOMES
        and review.scoring_readiness in _SCORING_READY_STATES
        and review.moderation_requirement != "required"
    )
    return ArtifactScoringAttentionState(
        class_id=class_id,
        activity_id=activity_id,
        artifact_instance_id=artifact_instance_id,
        scoring_ready=ready,
    )


__all__ = [
    "ArtifactScoringAttentionState",
    "inspect_artifact_scoring_attention_state",
]
