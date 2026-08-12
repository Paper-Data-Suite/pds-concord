"""Read-only Artifact Instance summaries for Concord workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance
from concord.workflows._collaboration import load_graph, work_ref
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import ConcordWorkflowNotFoundError


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactSummary:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_category: str
    generation_status: str
    expected_return_status: str
    artifact_status: str
    required_return_page_count: int
    returned_required_page_count: int
    current_author_count: int
    current_subject_count: int
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactDetail:
    summary: ArtifactSummary
    template_version_id: str
    page_ids: tuple[str, ...]
    session_id: str | None
    group_id: str | None
    privacy_classification: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactScanOccurrenceSummary:
    artifact_page_id: str
    logical_page_number: int
    scan_reference_id: str
    source_scan_id: str
    source_page_number: int
    snapshot_revision: int


def _current_author_ids(graph: ConcordRecordGraph) -> frozenset[str]:
    superseded = {
        item.supersedes_artifact_author_id
        for item in graph.artifact_authors
        if item.supersedes_artifact_author_id is not None
    }
    return frozenset(
        item.artifact_author_id
        for item in graph.artifact_authors
        if item.artifact_author_id not in superseded
        and item.attribution_status != "superseded"
    )


def _current_subject_ids(graph: ConcordRecordGraph) -> frozenset[str]:
    superseded = {
        item.supersedes_artifact_subject_id
        for item in graph.artifact_subjects
        if item.supersedes_artifact_subject_id is not None
    }
    return frozenset(
        item.artifact_subject_id
        for item in graph.artifact_subjects
        if item.artifact_subject_id not in superseded
        and item.confirmation_status != "superseded"
    )


def _summary(
    class_id: str,
    activity_id: str,
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
    snapshot_revision: int,
) -> ArtifactSummary:
    pages = {
        item.artifact_page_id: item
        for item in graph.artifact_pages
        if item.artifact_instance_id == artifact.artifact_instance_id
    }
    required = tuple(
        pages[page_id]
        for page_id in artifact.page_ids
        if page_id in pages and pages[page_id].return_expected
    )
    returned = sum(page.page_status == "returned" for page in required)
    current_authors = _current_author_ids(graph)
    current_subjects = _current_subject_ids(graph)
    return ArtifactSummary(
        class_id=class_id,
        activity_id=activity_id,
        artifact_instance_id=artifact.artifact_instance_id,
        artifact_category=artifact.artifact_category,
        generation_status=artifact.generation_status,
        expected_return_status=artifact.expected_return_status,
        artifact_status=artifact.artifact_status,
        required_return_page_count=len(required),
        returned_required_page_count=returned,
        current_author_count=sum(
            item.artifact_instance_id == artifact.artifact_instance_id
            and item.artifact_author_id in current_authors
            for item in graph.artifact_authors
        ),
        current_subject_count=sum(
            item.artifact_instance_id == artifact.artifact_instance_id
            and item.artifact_subject_id in current_subjects
            for item in graph.artifact_subjects
        ),
        snapshot_revision=snapshot_revision,
    )


def list_artifacts(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[ArtifactSummary, ...]:
    """List current Artifact Instances without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
    return tuple(
        _summary(class_id, activity_id, artifact, graph, revision)
        for artifact in sorted(
            graph.artifact_instances,
            key=lambda item: item.artifact_instance_id,
        )
    )


def show_artifact(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactDetail:
    """Show one exact Artifact Instance without exposing the raw record graph."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
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
    return ArtifactDetail(
        summary=_summary(class_id, activity_id, artifact, graph, revision),
        template_version_id=artifact.template_version_id,
        page_ids=artifact.page_ids,
        session_id=artifact.session_id,
        group_id=artifact.group_id,
        privacy_classification=artifact.privacy_policy.classification,
    )


def list_artifact_scan_occurrences(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[ArtifactScanOccurrenceSummary, ...]:
    """List exact returned occurrences for return-expected Artifact Pages."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
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
    pages = {
        item.artifact_page_id: item
        for item in graph.artifact_pages
        if item.artifact_instance_id == artifact_instance_id
        and item.return_expected
    }
    page_order = {
        page_id: index
        for index, page_id in enumerate(artifact.page_ids)
        if page_id in pages
    }
    occurrences = []
    for scan in graph.scan_references:
        page = pages.get(scan.artifact_page_id)
        if page is None:
            continue
        occurrences.append(
            ArtifactScanOccurrenceSummary(
                artifact_page_id=page.artifact_page_id,
                logical_page_number=page.page_number,
                scan_reference_id=scan.scan_reference_id,
                source_scan_id=scan.source_scan_id,
                source_page_number=scan.source_page_number,
                snapshot_revision=revision,
            )
        )
    return tuple(
        sorted(
            occurrences,
            key=lambda item: (
                page_order[item.artifact_page_id],
                item.scan_reference_id,
            ),
        )
    )


__all__ = [
    "ArtifactDetail",
    "ArtifactScanOccurrenceSummary",
    "ArtifactSummary",
    "list_artifact_scan_occurrences",
    "list_artifacts",
    "show_artifact",
]
