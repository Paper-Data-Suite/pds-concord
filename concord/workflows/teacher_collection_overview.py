"""Read-only, snapshot-scoped teacher view of one Activity's Collect stage.

This is a *projection*, never a new durable collection status. Core retains
physical scan sources and owns PDS2 routing; Concord owns the canonical graph,
exact assembly and separate attribution/review/score decisions.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from concord.models import ArtifactPage, ScanReference
from concord.workflows._collaboration import work_ref
from concord.workflows.activity_read import load_activity_read_context
from concord.workflows.artifact import _current_author_ids, _current_subject_ids
from concord.workflows.artifact_assembly import ArtifactAssemblyIntegrityError
from concord.workflows.artifact_collection import _assembly_state
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
)
from concord.workflows.teacher_artifact_choices import build_teacher_artifact_choices

CollectionStage = Literal[
    "not_return_expected",
    "awaiting_return",
    "partially_returned",
    "ready_to_assemble",
    "choose_occurrences",
    "assembled",
    "needs_recovery",
]

_STAGE_LABELS: dict[CollectionStage, str] = {
    "not_return_expected": "No paper return required",
    "awaiting_return": "Awaiting returned pages",
    "partially_returned": "Partially returned",
    "ready_to_assemble": "Ready to assemble",
    "choose_occurrences": "Choose exact scanned occurrences",
    "assembled": "Verified assembly available",
    "needs_recovery": "Evidence needs inspection",
}

_NEXT_ACTIONS: dict[CollectionStage, str] = {
    "not_return_expected": "Continue the observation workflow if needed",
    "awaiting_return": "Route returned scans when paper arrives",
    "partially_returned": "Route or resolve missing returned pages",
    "ready_to_assemble": "Assemble returned work",
    "choose_occurrences": "Choose the exact occurrence for each repeated page",
    "assembled": "Open returned work, then review it explicitly",
    "needs_recovery": "Inspect evidence and use existing recovery tools",
}


@dataclass(frozen=True, slots=True)
class CollectionWorkItem:
    """One exact, current Artifact; labels are presentation, not identity."""

    artifact_instance_id: str
    label: str
    group_label: str
    session_label: str
    stage: CollectionStage
    required_return_pages: int
    routed_return_pages: int
    routed_occurrences: int
    pending_author_count: int
    pending_subject_count: int
    confirmed_author_count: int
    confirmed_subject_count: int

    @property
    def stage_label(self) -> str:
        return _STAGE_LABELS[self.stage]

    @property
    def next_action(self) -> str:
        return _NEXT_ACTIONS[self.stage]

    @property
    def attribution_note(self) -> str:
        pending = self.pending_author_count + self.pending_subject_count
        if not pending:
            return "No current unconfirmed Author/Subject relationships"
        if self.required_return_pages and self.routed_return_pages == 0:
            return "Unconfirmed attribution only; no routed returned evidence"
        if (
            self.required_return_pages
            and self.routed_return_pages < self.required_return_pages
        ):
            return "Unconfirmed attribution; returned evidence is incomplete"
        return "Author/Subject relationships require explicit review"


@dataclass(frozen=True, slots=True)
class TeacherCollectionOverview:
    """One consistent canonical Activity read; no inferred physical delivery."""

    class_id: str
    activity_id: str
    snapshot_revision: int
    snapshot_sha256: str
    items: tuple[CollectionWorkItem, ...]
    print_distribution_state: Literal["not_tracked"] = "not_tracked"


def _return_page_occurrences(
    *,
    pages: Mapping[str, ArtifactPage],
    scans_by_page: Mapping[str, tuple[ScanReference, ...]],
    activity_id: str,
    artifact_id: str,
    page_ids: tuple[str, ...],
) -> tuple[int, int, int]:
    """Count exact routed ScanReferences, never generated/page-status flags.

    These are *canonical route references*, not a claim that every retained
    source remains readable on disk. Exact source integrity is verified by the
    existing assembly owner before an assembled PDF can be trusted/opened.
    """
    for page_id in page_ids:
        page = pages.get(page_id)
        if page is None or page.artifact_instance_id != artifact_id:
            raise ArtifactAssemblyIntegrityError(
                "Artifact page identity is inconsistent with the Activity."
            )
    required = {
        page_id: pages[page_id]
        for page_id in page_ids
        if pages[page_id].return_expected
    }

    occurrence_ids: dict[str, set[str]] = defaultdict(set)
    for page_id, page in required.items():
        for scan in scans_by_page.get(page_id, ()):
            if (
                scan.activity_id != activity_id
                or not page.route_id
                or scan.route_id != page.route_id
            ):
                raise ArtifactAssemblyIntegrityError(
                    "A Scan Reference contradicts the returned Artifact's route."
                )
            occurrence_ids[page_id].add(scan.scan_reference_id)
    return (
        len(required),
        len(occurrence_ids),
        sum(len(items) for items in occurrence_ids.values()),
    )


def _stage(
    *,
    required: int,
    routed: int,
    assembly: str,
) -> CollectionStage:
    if required == 0:
        return "not_return_expected"
    if routed == 0:
        return "awaiting_return"
    if routed < required:
        return "partially_returned"
    states: dict[str, CollectionStage] = {
        "ready": "ready_to_assemble",
        "selection_required": "choose_occurrences",
        "assembled": "assembled",
        "needs_recovery": "needs_recovery",
        "not_ready": "needs_recovery",
        "not_applicable": "needs_recovery",
    }
    return states[assembly]


def inspect_teacher_collection_overview(
    class_id: str,
    activity_id: str,
    *,
    expected_snapshot_revision: int | None = None,
    workspace_root: str | Path | None = None,
) -> TeacherCollectionOverview:
    """Inspect all collection work from one exact snapshot, without writes.

    A synthetic/opened Packet or its page ``status`` alone never proves return.
    Returned means that a matching canonical route/ScanReference is present.
    No page, author or subject is attributed to another class by display label.
    """
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Selected PDS workspace is unavailable.")
    require_core_class(root, class_id)
    context = load_activity_read_context(root, work_ref(class_id, activity_id))
    if (
        expected_snapshot_revision is not None
        and context.snapshot_revision != expected_snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Collection state changed. Refresh the Activity before continuing."
        )
    graph = context.graph
    choices = build_teacher_artifact_choices(
        graph,
        class_id=class_id,
        activity_id=activity_id,
        snapshot_revision=context.snapshot_revision,
    )
    artifacts = {
        item.artifact_instance_id: item
        for item in graph.artifact_instances
        if item.activity_id == activity_id
    }
    pages = {page.artifact_page_id: page for page in graph.artifact_pages}
    scan_index: dict[str, list[ScanReference]] = defaultdict(list)
    for scan in graph.scan_references:
        scan_index[scan.artifact_page_id].append(scan)
    scans_by_page = {key: tuple(value) for key, value in scan_index.items()}
    author_heads = _current_author_ids(graph)
    subject_heads = _current_subject_ids(graph)
    authors: dict[str, Counter[str]] = defaultdict(Counter)
    subjects: dict[str, Counter[str]] = defaultdict(Counter)
    for author in graph.artifact_authors:
        if author.artifact_author_id in author_heads:
            authors[author.artifact_instance_id][author.attribution_status] += 1
    for subject in graph.artifact_subjects:
        if subject.artifact_subject_id in subject_heads:
            subjects[subject.artifact_instance_id][subject.confirmation_status] += 1

    # Disambiguate same Group/Session without displaying internal identifiers.
    label_totals = Counter(
        (choice.group_label, choice.session_label) for choice in choices
    )
    label_positions: Counter[tuple[str, str]] = Counter()
    result: list[CollectionWorkItem] = []
    for choice in choices:
        artifact_id = choice.summary.artifact_instance_id
        artifact = artifacts[artifact_id]
        required, routed, occurrences = _return_page_occurrences(
            pages=pages,
            scans_by_page=scans_by_page,
            activity_id=activity_id,
            artifact_id=artifact_id,
            page_ids=artifact.page_ids,
        )
        if required and routed == required:
            assembly_state = _assembly_state(
                root, class_id, activity_id, artifact, graph
            )
        else:
            assembly_state = "not_ready"
        pair = (choice.group_label, choice.session_label)
        label_positions[pair] += 1
        label = " | ".join(pair)
        if label_totals[pair] > 1:
            label += (
                f" | work {label_positions[pair]} of {label_totals[pair]} "
                "(not chronological)"
            )
        result.append(
            CollectionWorkItem(
                artifact_instance_id=artifact_id,
                label=label,
                group_label=choice.group_label,
                session_label=choice.session_label,
                stage=_stage(required=required, routed=routed, assembly=assembly_state),
                required_return_pages=required,
                routed_return_pages=routed,
                routed_occurrences=occurrences,
                pending_author_count=sum(
                    authors[artifact_id][status]
                    for status in ("proposed", "disputed", "unknown")
                ),
                pending_subject_count=sum(
                    subjects[artifact_id][status]
                    for status in ("proposed", "disputed", "unresolved")
                ),
                confirmed_author_count=authors[artifact_id]["confirmed"],
                confirmed_subject_count=subjects[artifact_id]["confirmed"],
            )
        )
    return TeacherCollectionOverview(
        class_id=class_id,
        activity_id=activity_id,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        items=tuple(result),
    )


__all__ = [
    "CollectionStage",
    "CollectionWorkItem",
    "TeacherCollectionOverview",
    "inspect_teacher_collection_overview",
]
