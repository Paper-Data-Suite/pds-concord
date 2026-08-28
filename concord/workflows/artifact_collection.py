"""Read-only collection-stage interpretation for returned Concord Artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance
from concord.workflows._collaboration import load_graph, work_ref
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyAmbiguityError,
    ArtifactAssemblyError,
    ArtifactAssemblyIncompleteError,
    ArtifactAssemblyIntegrityError,
    _assembly_id,
    _assembly_paths,
    _select_lineage,
    _verify_existing,
)
from concord.workflows.artifact_attribution import (
    list_artifact_authors,
    list_artifact_subjects,
)
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import ConcordWorkflowNotFoundError

ArtifactAssemblyState: TypeAlias = Literal[
    "not_applicable",
    "not_ready",
    "ready",
    "selection_required",
    "assembled",
    "needs_recovery",
]


@dataclass(frozen=True, slots=True)
class ArtifactCollectionState:
    """Privacy-minimal current collection state for one Artifact."""

    class_id: str
    activity_id: str
    artifact_instance_id: str
    assembly_state: ArtifactAssemblyState
    author_confirmation_pending: bool
    subject_confirmation_pending: bool


def _artifact(
    graph: ConcordRecordGraph,
    artifact_instance_id: str,
) -> ArtifactInstance:
    artifact = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == artifact_instance_id
        ),
        None,
    )
    if artifact is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    return artifact


def _assembly_state(
    root: Path,
    class_id: str,
    activity_id: str,
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
) -> ArtifactAssemblyState:
    """Interpret exact assembly readiness without creating or repairing output."""
    try:
        lineage = _select_lineage(artifact, graph, ())
    except ArtifactAssemblyIncompleteError:
        # Some or all required paper has not returned yet. Assembly is not a
        # truthful teacher action until the existing assembly service can act.
        return "not_ready"
    except ArtifactAssemblyAmbiguityError:
        # All required evidence exists, but an exact returned occurrence still
        # needs teacher selection before assembly can proceed.
        return "selection_required"
    except ArtifactAssemblyError:
        # Includes Artifacts with no return-expected pages.
        return "not_applicable"

    assembly_id = _assembly_id(artifact.artifact_instance_id, lineage)
    output_path, manifest_path = _assembly_paths(
        root,
        work_ref(class_id, activity_id),
        artifact.artifact_instance_id,
        assembly_id,
    )
    if not output_path.parent.exists():
        return "ready"
    try:
        _verify_existing(
            output_path=output_path,
            manifest_path=manifest_path,
            work=work_ref(class_id, activity_id),
            artifact=artifact,
            assembly_id=assembly_id,
            lineage=lineage,
        )
    except ArtifactAssemblyIntegrityError:
        return "needs_recovery"
    return "assembled"


def inspect_artifact_collection_state(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactCollectionState:
    """Inspect current assembly/confirmation state without mutating workspace data."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    graph, _, _ = load_graph(root, work_ref(class_id, activity_id))
    artifact = _artifact(graph, artifact_instance_id)
    if artifact.activity_id != activity_id:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )

    authors = list_artifact_authors(
        class_id,
        activity_id,
        artifact_instance_id=artifact_instance_id,
        workspace_root=root,
    )
    subjects = list_artifact_subjects(
        class_id,
        activity_id,
        artifact_instance_id=artifact_instance_id,
        workspace_root=root,
    )
    return ArtifactCollectionState(
        class_id=class_id,
        activity_id=activity_id,
        artifact_instance_id=artifact_instance_id,
        assembly_state=_assembly_state(
            root,
            class_id,
            activity_id,
            artifact,
            graph,
        ),
        author_confirmation_pending=any(
            item.attribution_status in {"proposed", "disputed"}
            for item in authors
        ),
        subject_confirmation_pending=any(
            item.confirmation_status in {"proposed", "disputed", "unresolved"}
            for item in subjects
        ),
    )


__all__ = [
    "ArtifactAssemblyState",
    "ArtifactCollectionState",
    "inspect_artifact_collection_state",
]
