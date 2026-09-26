"""Read-only deterministic selection of the next Artifact awaiting first Review."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from concord.models import ArtifactInstance
from concord.workflows._collaboration import work_ref
from concord.workflows.activity_attention import (
    _build_attention_index,
    _collection_state_from_context,
    _review_state_from_context,
)
from concord.workflows.activity_read import (
    ActivityReadContext,
    load_activity_read_context,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root


@dataclass(frozen=True, slots=True)
class ArtifactReviewNext:
    """Current first-Review work item derived from canonical Review attention."""

    class_id: str
    activity_id: str
    artifact: ArtifactInstance
    snapshot_revision: int
    snapshot_sha256: str


def _next_artifact_review_from_context(
    context: ActivityReadContext,
) -> ArtifactReviewNext | None:
    """Return the deterministic first `concord_review_first` Artifact."""
    index = _build_attention_index(context)
    for artifact in sorted(
        context.graph.artifact_instances,
        key=lambda item: item.artifact_instance_id,
    ):
        collection = _collection_state_from_context(
            context,
            index,
            artifact.artifact_instance_id,
        )
        review_state = _review_state_from_context(
            context,
            index,
            artifact.artifact_instance_id,
            collection,
        )
        if review_state.first_review_pending:
            return ArtifactReviewNext(
                class_id=context.work.class_id,
                activity_id=context.work.work_id,
                artifact=artifact,
                snapshot_revision=context.snapshot_revision,
                snapshot_sha256=context.snapshot_sha256,
            )
    return None


def inspect_next_artifact_review(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactReviewNext | None:
    """Reload current state and return the next Artifact awaiting first Review."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return None
    require_core_class(root, class_id)
    context = load_activity_read_context(
        root,
        work_ref(class_id, activity_id),
    )
    return _next_artifact_review_from_context(context)


__all__ = [
    "ArtifactReviewNext",
    "inspect_next_artifact_review",
]
