"""Read-only target Activity materials checkpoint for cross-class lesson reuse.

This view consumes existing Concord generation projections. It never opens a
source Activity, allocates a route, produces a Packet, or claims paper custody.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from concord.workflows.activity import show_activity
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
)
from concord.workflows.packet_generation import (
    PacketGenerationSummary,
    list_packet_generations,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetMaterialsCheckpoint:
    """One target-only, no-write, point-in-time observation."""

    class_id: str
    activity_id: str
    title: str
    snapshot_revision: int
    generations: tuple[PacketGenerationSummary, ...]

    @property
    def has_generations(self) -> bool:
        return bool(self.generations)

    @property
    def requires_recovery(self) -> bool:
        return any(
            row.routes_pending_count
            or row.planned_count
            or row.rendering_count
            or row.failed_count
            or row.cancelled_count
            for row in self.generations
        )

    @property
    def ready_to_print(self) -> int:
        return sum(row.generated_count for row in self.generations)

    @property
    def generation_ids(self) -> frozenset[str]:
        return frozenset(row.generation_id for row in self.generations)


def inspect_target_materials(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> TargetMaterialsCheckpoint:
    """Inspect only the exact target Class/Activity and its native generations."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Target workspace is not available.")
    require_core_class(root, class_id)
    activity = show_activity(class_id, activity_id, workspace_root=root).summary
    if activity.class_id != class_id or activity.activity_id != activity_id:
        raise ConcordWorkflowConflictError("Target Activity identity changed.")
    generations = list_packet_generations(class_id, activity_id, workspace_root=root)
    ids: set[str] = set()
    for row in generations:
        if row.class_id != class_id or row.activity_id != activity_id:
            raise ConcordWorkflowConflictError(
                "A prepared generation refers to another class or Activity."
            )
        if row.snapshot_revision != activity.snapshot_revision:
            raise ConcordWorkflowConflictError(
                "Target Activity changed during materials inspection. Reopen it."
            )
        if row.generation_id in ids:
            raise ConcordWorkflowConflictError(
                "Target generation projection contains duplicate identities."
            )
        ids.add(row.generation_id)
    return TargetMaterialsCheckpoint(
        class_id=class_id,
        activity_id=activity_id,
        title=activity.title,
        snapshot_revision=activity.snapshot_revision,
        generations=generations,
    )


def new_target_generations(
    before: TargetMaterialsCheckpoint,
    after: TargetMaterialsCheckpoint,
) -> tuple[PacketGenerationSummary, ...]:
    """Report new target records only; never infer external print or QR custody."""
    if (before.class_id, before.activity_id) != (after.class_id, after.activity_id):
        raise ConcordWorkflowConflictError(
            "Cannot compare materials from different target Activities."
        )
    if not before.generation_ids.issubset(after.generation_ids):
        raise ConcordWorkflowConflictError(
            "Previously observed generations disappeared; inspect target history."
        )
    existing = before.generation_ids
    return tuple(row for row in after.generations if row.generation_id not in existing)
