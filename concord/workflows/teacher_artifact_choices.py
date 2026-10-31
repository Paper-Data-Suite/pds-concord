"""Snapshot-scoped, read-only labels for teacher Artifact selection.

Only canonical current Concord fields are used here. A label is a projection,
not an Artifact identity, participant attribution, or an evidence readiness check.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.workflows.artifact import (
    ArtifactSummary,
    _current_author_ids,
    _current_subject_ids,
    _load_artifact_graph,
)
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import ConcordWorkflowConflictError


@dataclass(frozen=True, slots=True, kw_only=True)
class TeacherArtifactChoice:
    """Display-only projection with exact canonical selection identity."""

    summary: ArtifactSummary
    label: str
    group_label: str
    session_label: str


def build_teacher_artifact_choices(
    graph: ConcordRecordGraph,
    *,
    class_id: str,
    activity_id: str,
    snapshot_revision: int,
) -> tuple[TeacherArtifactChoice, ...]:
    """Construct all choices in linear work from ONE validated record graph."""
    groups = {item.group_id: item for item in graph.groups}
    sessions = {item.session_id: item for item in graph.sessions}
    group_names: dict[str, list[str]] = defaultdict(list)
    for item in graph.groups:
        group_names[item.label].append(item.group_id)
    group_positions = {
        group_id: (index, len(group_names[label]))
        for label, ids in group_names.items()
        for index, group_id in enumerate(sorted(ids), start=1)
    }

    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    author_heads = _current_author_ids(graph)
    subject_heads = _current_subject_ids(graph)
    author_counts = Counter(
        item.artifact_instance_id
        for item in graph.artifact_authors
        if item.artifact_author_id in author_heads
    )
    subject_counts = Counter(
        item.artifact_instance_id
        for item in graph.artifact_subjects
        if item.artifact_subject_id in subject_heads
    )

    preliminary: list[tuple[ArtifactSummary, str, str, str]] = []
    for artifact in sorted(
        graph.artifact_instances, key=lambda item: item.artifact_instance_id
    ):
        if artifact.activity_id != activity_id:
            continue
        returned_pages = tuple(
            pages[page_id]
            for page_id in artifact.page_ids
            if page_id in pages and pages[page_id].return_expected
        )
        summary = ArtifactSummary(
            class_id=class_id,
            activity_id=activity_id,
            artifact_instance_id=artifact.artifact_instance_id,
            artifact_category=artifact.artifact_category,
            generation_status=artifact.generation_status,
            expected_return_status=artifact.expected_return_status,
            artifact_status=artifact.artifact_status,
            required_return_page_count=len(returned_pages),
            returned_required_page_count=sum(
                page.page_status == "returned" for page in returned_pages
            ),
            current_author_count=author_counts[artifact.artifact_instance_id],
            current_subject_count=subject_counts[artifact.artifact_instance_id],
            snapshot_revision=snapshot_revision,
        )
        group = (
            groups.get(artifact.group_id)
            if artifact.group_id is not None
            else None
        )
        if group is None:
            group_label = (
                "Group not recorded"
                if artifact.group_id is None
                else "Group no longer in current Activity"
            )
        else:
            group_label = group.label
            position, total = group_positions[group.group_id]
            if total > 1:
                group_label += f" (group {position} of {total} with this name)"

        session = (
            sessions.get(artifact.session_id)
            if artifact.session_id is not None
            else None
        )
        if session is None:
            session_label = (
                "Session not recorded"
                if artifact.session_id is None
                else "Session no longer in current Activity"
            )
        else:
            session_label = f"Session {session.sequence}"
            if session.label:
                session_label += f" - {session.label}"

        status = summary.artifact_status.replace("_", " ")
        base = (
            f"{group_label} | {session_label} | "
            f"returned {summary.returned_required_page_count}/"
            f"{summary.required_return_page_count} | {status}"
        )
        preliminary.append((summary, group_label, session_label, base))

    # A Copy number distinguishes otherwise identical choices. It is NOT a
    # creation-time or revision order, which is unavailable in this projection.
    totals = Counter(item[3] for item in preliminary)
    positions: Counter[str] = Counter()
    result: list[TeacherArtifactChoice] = []
    for summary, group_label, session_label, base in preliminary:
        positions[base] += 1
        label = base
        if totals[base] > 1:
            label += f" | work copy {positions[base]} of {totals[base]}"
        result.append(
            TeacherArtifactChoice(
                summary=summary,
                label=label,
                group_label=group_label,
                session_label=session_label,
            )
        )
    return tuple(result)


def list_teacher_artifact_choices(
    class_id: str,
    activity_id: str,
    *,
    expected_snapshot_revision: int | None = None,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> tuple[TeacherArtifactChoice, ...]:
    """Read the Activity graph once, then construct selection-safe labels."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = _load_artifact_graph(
        root, class_id, activity_id, standards_library=standards_library
    )
    if (
        expected_snapshot_revision is not None
        and expected_snapshot_revision != revision
    ):
        raise ConcordWorkflowConflictError(
            "The Activity changed while choosing returned work. "
            "Refresh it and choose the work again."
        )
    return build_teacher_artifact_choices(
        graph,
        class_id=class_id,
        activity_id=activity_id,
        snapshot_revision=revision,
    )


__all__ = [
    "TeacherArtifactChoice",
    "build_teacher_artifact_choices",
    "list_teacher_artifact_choices",
]
