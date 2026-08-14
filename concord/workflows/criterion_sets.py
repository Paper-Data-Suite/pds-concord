"""Criterion Set, Criterion, and Activity-selection application services."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import Activity, Criterion, CriterionSet
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
class CriterionSpec:
    criterion_id: str
    key: str
    label: str
    definition: str
    criterion_kind: str
    supported_target_kinds: tuple[str, ...]
    standard_id: str | None = None
    alignment_standard_ids: tuple[str, ...] = ()
    default_scoring_scale_id: str | None = None
    status: str = "active"


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateCriterionSetRequest:
    class_id: str
    activity_id: str
    criterion_set_id: str
    lineage_id: str
    name: str
    purpose: str
    revision: int
    scope: str
    criterion_set_kind: str
    criteria: tuple[CriterionSpec, ...]
    status: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    standards_profile_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviseCriterionSetRequest:
    class_id: str
    activity_id: str
    criterion_set_id: str
    replacement_criterion_set_id: str
    name: str
    purpose: str
    revision: int
    scope: str
    criterion_set_kind: str
    criteria: tuple[CriterionSpec, ...]
    status: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    standards_profile_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SelectActivityCriterionSetsRequest:
    class_id: str
    activity_id: str
    criterion_set_ids: tuple[str, ...]
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionSetMutationResult:
    commit: WorkflowCommitResult
    criterion_set_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionSetSelectionResult:
    commit: WorkflowCommitResult
    activity_id: str
    criterion_set_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionSetSummary:
    class_id: str
    activity_id: str
    criterion_set_id: str
    lineage_id: str
    revision: int
    name: str
    scope: str
    criterion_set_kind: str
    status: str
    criterion_count: int
    standards_profile_id: str | None
    supersedes_criterion_set_id: str | None
    is_current: bool
    is_selected: bool
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionSetDetail:
    summary: CriterionSetSummary
    purpose: str
    criteria: tuple[Criterion, ...]


def _criterion_set_heads(
    graph: ConcordRecordGraph,
) -> tuple[CriterionSet, ...]:
    superseded = {
        item.supersedes_criterion_set_id
        for item in graph.criterion_sets
        if item.supersedes_criterion_set_id is not None
    }
    return tuple(
        item
        for item in graph.criterion_sets
        if item.criterion_set_id not in superseded
    )


def _require_criterion_set(
    graph: ConcordRecordGraph,
    criterion_set_id: str,
) -> CriterionSet:
    value = next(
        (
            item
            for item in graph.criterion_sets
            if item.criterion_set_id == criterion_set_id
        ),
        None,
    )
    if value is None:
        raise ConcordWorkflowNotFoundError(
            f"Criterion Set is not available: {criterion_set_id}"
        )
    return value


def _validate_unique_specs(specs: tuple[CriterionSpec, ...]) -> None:
    if not specs:
        raise ConcordWorkflowValidationError(
            "Criterion Set requires at least one Criterion."
        )
    ids = tuple(item.criterion_id for item in specs)
    if len(set(ids)) != len(ids):
        raise ConcordWorkflowValidationError(
            "Criterion specifications contain duplicate Criterion IDs."
        )
    keys = tuple(item.key for item in specs)
    if len(set(keys)) != len(keys):
        raise ConcordWorkflowValidationError(
            "Criterion keys must be unique within one Criterion Set revision."
        )


def _build_set_and_criteria(
    *,
    criterion_set_id: str,
    lineage_id: str,
    name: str,
    purpose: str,
    revision: int,
    scope: str,
    criterion_set_kind: str,
    criteria: tuple[CriterionSpec, ...],
    status: str,
    standards_profile_id: str | None,
    supersedes_criterion_set_id: str | None,
    actor: WorkflowActor,
    clock: Clock | None,
) -> tuple[CriterionSet, tuple[Criterion, ...]]:
    _validate_unique_specs(criteria)
    created = provenance(actor, clock=clock)
    members = tuple(
        Criterion(
            criterion_id=spec.criterion_id,
            criterion_set_id=criterion_set_id,
            key=spec.key,
            label=spec.label,
            definition=spec.definition,
            criterion_kind=spec.criterion_kind,
            supported_target_kinds=spec.supported_target_kinds,
            status=spec.status,
            created_provenance=created,
            standard_id=spec.standard_id,
            alignment_standard_ids=spec.alignment_standard_ids,
            default_scoring_scale_id=spec.default_scoring_scale_id,
        )
        for spec in criteria
    )
    criterion_set = CriterionSet(
        criterion_set_id=criterion_set_id,
        lineage_id=lineage_id,
        name=name,
        purpose=purpose,
        revision=revision,
        scope=scope,
        criterion_set_kind=criterion_set_kind,
        criterion_ids=tuple(item.criterion_id for item in members),
        status=status,
        created_provenance=created,
        standards_profile_id=standards_profile_id,
        supersedes_criterion_set_id=supersedes_criterion_set_id,
    )
    kinds = {item.criterion_kind for item in members}
    if criterion_set.criterion_set_kind == "standard_backed" and kinds != {
        "standard_backed"
    }:
        raise ConcordWorkflowValidationError(
            "standard_backed Criterion Set may contain only standard-backed Criteria."
        )
    if criterion_set.criterion_set_kind == "local" and kinds != {"local"}:
        raise ConcordWorkflowValidationError(
            "local Criterion Set may contain only local Criteria."
        )
    return criterion_set, members


def _ensure_lineage_available(
    graph: ConcordRecordGraph,
    lineage_id: str,
) -> None:
    if any(item.lineage_id == lineage_id for item in graph.criterion_sets):
        raise ConcordWorkflowConflictError(
            f"Criterion Set lineage already exists: {lineage_id}"
        )


def _validate_selection(
    activity: Activity,
    selected: tuple[CriterionSet, ...],
    graph: ConcordRecordGraph,
) -> None:
    criteria = {item.criterion_id: item for item in graph.criteria}
    for criterion_set in selected:
        if (
            criterion_set.standards_profile_id is not None
            and criterion_set.standards_profile_id != activity.standards_profile_id
        ):
            raise ConcordWorkflowValidationError(
                "Criterion Set standards profile does not match the Activity."
            )
        members = tuple(
            criteria[item]
            for item in criterion_set.criterion_ids
            if item in criteria
        )
        if len(members) != len(criterion_set.criterion_ids):
            raise ConcordWorkflowValidationError(
                "Criterion Set has unresolved member Criteria."
            )
        has_standard = any(
            item.criterion_kind == "standard_backed" for item in members
        )
        has_local = any(item.criterion_kind == "local" for item in members)
        if has_standard and activity.scoring_orientation not in {
            "standards_based",
            "mixed",
        }:
            raise ConcordWorkflowValidationError(
                "Activity scoring orientation does not permit standard-backed Criteria."
            )
        if has_local and activity.scoring_orientation not in {
            "local_criteria_only",
            "mixed",
        }:
            raise ConcordWorkflowValidationError(
                "Activity scoring orientation does not permit local Criteria."
            )
        for criterion in members:
            if (
                criterion.criterion_kind == "standard_backed"
                and criterion.standard_id not in activity.focus_standard_ids
            ):
                raise ConcordWorkflowValidationError(
                    "Standard-backed Criterion does not govern an Activity Focus "
                    "Standard."
                )


def _used_criterion_set_ids(graph: ConcordRecordGraph) -> frozenset[str]:
    criteria = {item.criterion_id: item for item in graph.criteria}
    return frozenset(
        criteria[item.criterion_id].criterion_set_id
        for item in graph.score_records
        if item.criterion_id in criteria
    )


def _summary(
    *,
    class_id: str,
    activity: Activity,
    criterion_set: CriterionSet,
    current_ids: frozenset[str],
    snapshot_revision: int,
) -> CriterionSetSummary:
    return CriterionSetSummary(
        class_id=class_id,
        activity_id=activity.activity_id,
        criterion_set_id=criterion_set.criterion_set_id,
        lineage_id=criterion_set.lineage_id,
        revision=criterion_set.revision,
        name=criterion_set.name,
        scope=criterion_set.scope,
        criterion_set_kind=criterion_set.criterion_set_kind,
        status=criterion_set.status,
        criterion_count=len(criterion_set.criterion_ids),
        standards_profile_id=criterion_set.standards_profile_id,
        supersedes_criterion_set_id=criterion_set.supersedes_criterion_set_id,
        is_current=criterion_set.criterion_set_id in current_ids,
        is_selected=criterion_set.criterion_set_id in activity.criterion_set_ids,
        snapshot_revision=snapshot_revision,
    )


def create_criterion_set(
    request: CreateCriterionSetRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> CriterionSetMutationResult:
    """Create one complete Criterion Set revision atomically."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_activity(graph, request.activity_id)
    require_new_identity(
        graph.criterion_sets,
        "criterion_set_id",
        request.criterion_set_id,
        "Criterion Set",
    )
    _ensure_lineage_available(graph, request.lineage_id)
    for spec in request.criteria:
        require_new_identity(
            graph.criteria,
            "criterion_id",
            spec.criterion_id,
            "Criterion",
        )
    criterion_set, criteria = _build_set_and_criteria(
        criterion_set_id=request.criterion_set_id,
        lineage_id=request.lineage_id,
        name=request.name,
        purpose=request.purpose,
        revision=request.revision,
        scope=request.scope,
        criterion_set_kind=request.criterion_set_kind,
        criteria=request.criteria,
        status=request.status,
        standards_profile_id=request.standards_profile_id,
        supersedes_criterion_set_id=None,
        actor=request.actor,
        clock=clock,
    )
    result = commit_record_batch(
        root,
        work,
        (criterion_set, *criteria),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return CriterionSetMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        criterion_set_id=criterion_set.criterion_set_id,
    )


def revise_criterion_set(
    request: ReviseCriterionSetRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> CriterionSetMutationResult:
    """Create the explicit successor of one current Criterion Set revision."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_activity(graph, request.activity_id)
    predecessor = _require_criterion_set(graph, request.criterion_set_id)
    if predecessor not in _criterion_set_heads(graph):
        raise ConcordWorkflowConflictError(
            "Historical Criterion Set revisions cannot be revised as current heads."
        )
    if request.revision <= predecessor.revision:
        raise ConcordWorkflowValidationError(
            "Criterion Set successor revision must advance."
        )
    require_new_identity(
        graph.criterion_sets,
        "criterion_set_id",
        request.replacement_criterion_set_id,
        "Criterion Set",
    )
    for spec in request.criteria:
        require_new_identity(
            graph.criteria,
            "criterion_id",
            spec.criterion_id,
            "Criterion",
        )
    successor, criteria = _build_set_and_criteria(
        criterion_set_id=request.replacement_criterion_set_id,
        lineage_id=predecessor.lineage_id,
        name=request.name,
        purpose=request.purpose,
        revision=request.revision,
        scope=request.scope,
        criterion_set_kind=request.criterion_set_kind,
        criteria=request.criteria,
        status=request.status,
        standards_profile_id=request.standards_profile_id,
        supersedes_criterion_set_id=predecessor.criterion_set_id,
        actor=request.actor,
        clock=clock,
    )
    result = commit_record_batch(
        root,
        work,
        (successor, *criteria),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return CriterionSetMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        criterion_set_id=successor.criterion_set_id,
    )


def select_activity_criterion_sets(
    request: SelectActivityCriterionSetsRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> CriterionSetSelectionResult:
    """Select exact Criterion Set revisions for future Activity scoring."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    activity = require_activity(graph, request.activity_id)
    selected_ids = tuple(request.criterion_set_ids)
    if len(set(selected_ids)) != len(selected_ids):
        raise ConcordWorkflowValidationError(
            "Activity Criterion Set selection must not contain duplicates."
        )
    selected = tuple(
        _require_criterion_set(graph, criterion_set_id)
        for criterion_set_id in selected_ids
    )
    _validate_selection(activity, selected, graph)
    used_ids = _used_criterion_set_ids(graph)
    removed_used = used_ids - frozenset(selected_ids)
    if removed_used:
        rendered = ", ".join(sorted(removed_used))
        raise ConcordWorkflowValidationError(
            "Activity cannot deselect Criterion Set revisions used by historical "
            f"Scores: {rendered}"
        )
    candidate = replace(
        activity,
        criterion_set_ids=selected_ids,
        updated_provenance=provenance(request.actor, clock=clock),
    )
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return CriterionSetSelectionResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        activity_id=activity.activity_id,
        criterion_set_ids=selected_ids,
    )


def list_criterion_sets(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    current_only: bool = False,
) -> tuple[CriterionSetSummary, ...]:
    """List compact Criterion Set summaries without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, snapshot_revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    activity = require_activity(graph, activity_id)
    current_ids = frozenset(
        item.criterion_set_id for item in _criterion_set_heads(graph)
    )
    records = (
        tuple(
            item
            for item in graph.criterion_sets
            if item.criterion_set_id in current_ids
        )
        if current_only
        else graph.criterion_sets
    )
    return tuple(
        _summary(
            class_id=class_id,
            activity=activity,
            criterion_set=item,
            current_ids=current_ids,
            snapshot_revision=snapshot_revision,
        )
        for item in sorted(
            records,
            key=lambda value: (
                value.lineage_id,
                value.revision,
                value.criterion_set_id,
            ),
        )
    )


def show_criterion_set(
    class_id: str,
    activity_id: str,
    criterion_set_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> CriterionSetDetail:
    """Load one exact Criterion Set revision and its ordered Criteria."""
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
    activity = require_activity(graph, activity_id)
    criterion_set = _require_criterion_set(graph, criterion_set_id)
    criteria = {item.criterion_id: item for item in graph.criteria}
    ordered = tuple(criteria[item] for item in criterion_set.criterion_ids)
    current_ids = frozenset(
        item.criterion_set_id for item in _criterion_set_heads(graph)
    )
    return CriterionSetDetail(
        summary=_summary(
            class_id=class_id,
            activity=activity,
            criterion_set=criterion_set,
            current_ids=current_ids,
            snapshot_revision=snapshot_revision,
        ),
        purpose=criterion_set.purpose,
        criteria=ordered,
    )


def list_current_criterion_set_heads(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> tuple[CriterionSetSummary, ...]:
    """Return every explicit current Criterion Set lineage head."""
    return list_criterion_sets(
        class_id,
        activity_id,
        workspace_root=workspace_root,
        standards_library=standards_library,
        current_only=True,
    )
