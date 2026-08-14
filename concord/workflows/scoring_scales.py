"""Immutable native Scoring Scale application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import ScoringScale, ScoringScaleLevel
from concord.storage import commit_record_batch
from concord.workflows._collaboration import (
    load_graph,
    require_activity,
    require_new_identity,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateScoringScaleRequest:
    class_id: str
    activity_id: str
    scoring_scale_id: str
    lineage_id: str
    name: str
    revision: int
    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]
    status: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    intended_use: str | None = None
    aggregation_guidance: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviseScoringScaleRequest:
    class_id: str
    activity_id: str
    scoring_scale_id: str
    replacement_scoring_scale_id: str
    name: str
    revision: int
    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]
    status: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    intended_use: str | None = None
    aggregation_guidance: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringScaleMutationResult:
    commit: WorkflowCommitResult
    scoring_scale_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringScaleSummary:
    class_id: str
    activity_id: str
    scoring_scale_id: str
    lineage_id: str
    revision: int
    name: str
    scale_type: str
    status: str
    level_count: int
    intended_use: str | None
    supersedes_scoring_scale_id: str | None
    is_current: bool
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoringScaleDetail:
    summary: ScoringScaleSummary
    levels: tuple[ScoringScaleLevel, ...]
    aggregation_guidance: str | None


def _scale_heads(graph: ConcordRecordGraph) -> tuple[ScoringScale, ...]:
    superseded = {
        item.supersedes_scoring_scale_id
        for item in graph.scoring_scales
        if item.supersedes_scoring_scale_id is not None
    }
    return tuple(
        item
        for item in graph.scoring_scales
        if item.scoring_scale_id not in superseded
    )


def _require_scale(
    graph: ConcordRecordGraph,
    scoring_scale_id: str,
) -> ScoringScale:
    scale = next(
        (
            item
            for item in graph.scoring_scales
            if item.scoring_scale_id == scoring_scale_id
        ),
        None,
    )
    if scale is None:
        raise ConcordWorkflowNotFoundError(
            f"Scoring Scale is not available: {scoring_scale_id}"
        )
    return scale


def _ensure_lineage_available(
    graph: ConcordRecordGraph,
    lineage_id: str,
) -> None:
    if any(item.lineage_id == lineage_id for item in graph.scoring_scales):
        raise ConcordWorkflowConflictError(
            f"Scoring Scale lineage already exists: {lineage_id}"
        )


def _summary(
    *,
    class_id: str,
    activity_id: str,
    scale: ScoringScale,
    current_ids: frozenset[str],
    snapshot_revision: int,
) -> ScoringScaleSummary:
    return ScoringScaleSummary(
        class_id=class_id,
        activity_id=activity_id,
        scoring_scale_id=scale.scoring_scale_id,
        lineage_id=scale.lineage_id,
        revision=scale.revision,
        name=scale.name,
        scale_type=scale.scale_type,
        status=scale.status,
        level_count=len(scale.levels),
        intended_use=scale.intended_use,
        supersedes_scoring_scale_id=scale.supersedes_scoring_scale_id,
        is_current=scale.scoring_scale_id in current_ids,
        snapshot_revision=snapshot_revision,
    )


def _build_scale(
    *,
    scoring_scale_id: str,
    lineage_id: str,
    name: str,
    revision: int,
    scale_type: str,
    levels: tuple[ScoringScaleLevel, ...],
    status: str,
    intended_use: str | None,
    aggregation_guidance: str | None,
    supersedes_scoring_scale_id: str | None,
    actor: WorkflowActor,
    clock: Clock | None,
) -> ScoringScale:
    return ScoringScale(
        scoring_scale_id=scoring_scale_id,
        lineage_id=lineage_id,
        name=name,
        revision=revision,
        scale_type=scale_type,
        levels=levels,
        status=status,
        created_provenance=provenance(actor, clock=clock),
        intended_use=intended_use,
        aggregation_guidance=aggregation_guidance,
        supersedes_scoring_scale_id=supersedes_scoring_scale_id,
    )


def create_scoring_scale(
    request: CreateScoringScaleRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ScoringScaleMutationResult:
    """Create one exact immutable Scoring Scale revision."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_activity(graph, request.activity_id)
    require_new_identity(
        graph.scoring_scales,
        "scoring_scale_id",
        request.scoring_scale_id,
        "Scoring Scale",
    )
    _ensure_lineage_available(graph, request.lineage_id)
    scale = _build_scale(
        scoring_scale_id=request.scoring_scale_id,
        lineage_id=request.lineage_id,
        name=request.name,
        revision=request.revision,
        scale_type=request.scale_type,
        levels=request.levels,
        status=request.status,
        intended_use=request.intended_use,
        aggregation_guidance=request.aggregation_guidance,
        supersedes_scoring_scale_id=None,
        actor=request.actor,
        clock=clock,
    )
    result = commit_record_batch(
        root,
        work,
        (scale,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ScoringScaleMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        scoring_scale_id=scale.scoring_scale_id,
    )


def revise_scoring_scale(
    request: ReviseScoringScaleRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ScoringScaleMutationResult:
    """Create the explicit successor of one current Scale revision."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_activity(graph, request.activity_id)
    predecessor = _require_scale(graph, request.scoring_scale_id)
    if predecessor not in _scale_heads(graph):
        raise ConcordWorkflowConflictError(
            "Historical Scoring Scale revisions cannot be revised as current heads."
        )
    if request.revision <= predecessor.revision:
        raise ConcordWorkflowValidationError(
            "Scoring Scale successor revision must advance."
        )
    require_new_identity(
        graph.scoring_scales,
        "scoring_scale_id",
        request.replacement_scoring_scale_id,
        "Scoring Scale",
    )
    successor = _build_scale(
        scoring_scale_id=request.replacement_scoring_scale_id,
        lineage_id=predecessor.lineage_id,
        name=request.name,
        revision=request.revision,
        scale_type=request.scale_type,
        levels=request.levels,
        status=request.status,
        intended_use=request.intended_use,
        aggregation_guidance=request.aggregation_guidance,
        supersedes_scoring_scale_id=predecessor.scoring_scale_id,
        actor=request.actor,
        clock=clock,
    )
    result = commit_record_batch(
        root,
        work,
        (successor,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ScoringScaleMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        scoring_scale_id=successor.scoring_scale_id,
    )


def list_scoring_scales(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    current_only: bool = False,
) -> tuple[ScoringScaleSummary, ...]:
    """List compact Scale summaries without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, snapshot_revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    require_activity(graph, activity_id)
    current_ids = frozenset(item.scoring_scale_id for item in _scale_heads(graph))
    records = (
        tuple(
            item
            for item in graph.scoring_scales
            if item.scoring_scale_id in current_ids
        )
        if current_only
        else graph.scoring_scales
    )
    return tuple(
        _summary(
            class_id=class_id,
            activity_id=activity_id,
            scale=item,
            current_ids=current_ids,
            snapshot_revision=snapshot_revision,
        )
        for item in sorted(
            records,
            key=lambda value: (
                value.lineage_id,
                value.revision,
                value.scoring_scale_id,
            ),
        )
    )


def show_scoring_scale(
    class_id: str,
    activity_id: str,
    scoring_scale_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> ScoringScaleDetail:
    """Load one exact Scoring Scale revision."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    graph, snapshot_revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    require_activity(graph, activity_id)
    scale = _require_scale(graph, scoring_scale_id)
    current_ids = frozenset(item.scoring_scale_id for item in _scale_heads(graph))
    return ScoringScaleDetail(
        summary=_summary(
            class_id=class_id,
            activity_id=activity_id,
            scale=scale,
            current_ids=current_ids,
            snapshot_revision=snapshot_revision,
        ),
        levels=scale.levels,
        aggregation_guidance=scale.aggregation_guidance,
    )


def list_current_scoring_scale_heads(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> tuple[ScoringScaleSummary, ...]:
    """Return every explicit current Scoring Scale lineage head."""
    return list_scoring_scales(
        class_id,
        activity_id,
        workspace_root=workspace_root,
        standards_library=standards_library,
        current_only=True,
    )
