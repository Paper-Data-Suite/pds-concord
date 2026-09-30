"""Read-only deterministic navigation to another score-ready Artifact."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from concord.models import ArtifactInstance
from concord.workflows._collaboration import work_ref
from concord.workflows.activity_read import (
    ActivityReadContext,
    load_activity_read_context,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import ConcordWorkflowConflictError

if TYPE_CHECKING:
    from concord.workflows.activity_attention import _ActivityAttentionIndex
    from concord.workflows.artifact_scoring_attention import (
        ArtifactScoringAttentionState,
    )


@dataclass(frozen=True, slots=True)
class ArtifactScoringNext:
    """Another current score-ready Artifact from one exact Activity snapshot."""

    class_id: str
    activity_id: str
    artifact: ArtifactInstance
    snapshot_revision: int
    snapshot_sha256: str


def _build_attention_index(
    context: ActivityReadContext,
) -> _ActivityAttentionIndex:
    """Lazily reuse canonical Activity-attention indexing."""
    from concord.workflows.activity_attention import (
        _build_attention_index as build_attention_index,
    )

    return build_attention_index(context)


def _score_state_from_context(
    context: ActivityReadContext,
    index: _ActivityAttentionIndex,
    artifact_instance_id: str,
) -> ArtifactScoringAttentionState:
    """Lazily reuse canonical score-ready semantics without an import cycle."""
    from concord.workflows.activity_attention import (
        _score_state_from_context as score_state_from_context,
    )

    return score_state_from_context(
        context,
        index,
        artifact_instance_id,
    )


def _score_ready_artifacts_from_context(
    context: ActivityReadContext,
) -> tuple[ArtifactInstance, ...]:
    """Return current score-ready Artifacts in deterministic identity order."""
    index = _build_attention_index(context)
    ready: list[ArtifactInstance] = []
    for artifact in sorted(
        context.graph.artifact_instances,
        key=lambda item: item.artifact_instance_id,
    ):
        state = _score_state_from_context(
            context,
            index,
            artifact.artifact_instance_id,
        )
        if state.scoring_ready:
            ready.append(artifact)
    return tuple(ready)


def _next_score_ready_artifact_from_context(
    context: ActivityReadContext,
    *,
    after_artifact_instance_id: str | None = None,
) -> ArtifactScoringNext | None:
    """Return one deterministic current score-ready Artifact.

    When an operation-local current Artifact is supplied, select another ready
    Artifact after it in identity order, wrapping once to the first other ready
    Artifact. The current Artifact itself is never selected as its own "next"
    item. No Score records are consulted as completion state.
    """
    ready = _score_ready_artifacts_from_context(context)
    if not ready:
        return None

    selected: ArtifactInstance | None = None
    if after_artifact_instance_id is None:
        selected = ready[0]
    else:
        artifact_ids = {
            item.artifact_instance_id for item in context.graph.artifact_instances
        }
        if after_artifact_instance_id not in artifact_ids:
            raise ConcordWorkflowConflictError(
                "Current scoring Artifact is no longer available in this Activity."
            )
        following = tuple(
            item
            for item in ready
            if item.artifact_instance_id > after_artifact_instance_id
        )
        preceding = tuple(
            item
            for item in ready
            if item.artifact_instance_id < after_artifact_instance_id
        )
        candidates = (*following, *preceding)
        if not candidates:
            return None
        selected = candidates[0]

    assert selected is not None
    return ArtifactScoringNext(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        artifact=selected,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
    )


def inspect_next_score_ready_artifact(
    class_id: str,
    activity_id: str,
    *,
    after_artifact_instance_id: str | None = None,
    minimum_snapshot_revision: int | None = None,
    workspace_root: str | Path | None = None,
) -> ArtifactScoringNext | None:
    """Reload current state and select another canonical score-ready Artifact."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return None
    require_core_class(root, class_id)
    context = load_activity_read_context(
        root,
        work_ref(class_id, activity_id),
    )
    if (
        minimum_snapshot_revision is not None
        and context.snapshot_revision < minimum_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Current Activity snapshot predates the completed Score mutation."
        )
    return _next_score_ready_artifact_from_context(
        context,
        after_artifact_instance_id=after_artifact_instance_id,
    )


__all__ = [
    "ArtifactScoringNext",
    "inspect_next_score_ready_artifact",
]
