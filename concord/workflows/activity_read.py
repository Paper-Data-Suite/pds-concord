"""Operation-scoped exact Activity read context for Concord projections."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pds_core.routing_models import ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.models import Activity
from concord.storage import load_current_snapshot_graph
from concord.workflows.models import ActivityDetail, ActivitySummary


@dataclass(frozen=True, slots=True)
class ActivityReadContext:
    """One exact verified current Activity state for one logical read operation."""

    root: Path
    work: ModuleWorkRef
    snapshot_revision: int
    snapshot_sha256: str
    graph: ConcordRecordGraph
    activity: Activity


def load_activity_read_context(
    root: Path,
    work: ModuleWorkRef,
) -> ActivityReadContext:
    """Load one verified current graph without Core standards context."""
    loaded = load_current_snapshot_graph(root, work)
    graph = cast(ConcordRecordGraph, loaded.graph)
    activity = graph.activities[0]
    return ActivityReadContext(
        root=root,
        work=work,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        graph=graph,
        activity=activity,
    )


def activity_summary_from_context(
    context: ActivityReadContext,
) -> ActivitySummary:
    """Project the compact Activity summary from one exact read context."""
    activity = context.activity
    return ActivitySummary(
        class_id=context.work.class_id,
        activity_id=activity.activity_id,
        title=activity.title,
        status=activity.status,
        scoring_orientation=activity.scoring_orientation,
        session_count=len(context.graph.sessions),
        group_count=len(context.graph.groups),
        snapshot_revision=context.snapshot_revision,
    )


def activity_detail_from_context(
    context: ActivityReadContext,
) -> ActivityDetail:
    """Project Activity detail from the same exact state as its summary."""
    activity = context.activity
    return ActivityDetail(
        summary=activity_summary_from_context(context),
        description=activity.description,
        activity_type=activity.activity_type,
        standards_profile_id=activity.standards_profile_id,
        focus_standard_ids=activity.focus_standard_ids,
    )


__all__ = [
    "ActivityReadContext",
    "activity_detail_from_context",
    "activity_summary_from_context",
    "load_activity_read_context",
]
