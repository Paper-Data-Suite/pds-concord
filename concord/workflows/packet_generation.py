"""Read-only exact-snapshot projections for Packet generations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary, load_workspace_standards_library

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance, ArtifactPage, PacketInstance, Session
from concord.packet_storage import PacketStorageError, load_current_packet
from concord.packet_storage_models import LoadedPacketLibrary
from concord.storage import load_current_record_graph
from concord.storage_errors import ConcordStorageError
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketGenerationSummary:
    """Teacher-facing summary of one exact Activity-owned Packet generation."""

    class_id: str
    activity_id: str
    generation_id: str
    packet_definition_id: str
    packet_version_id: str
    packet_name: str
    packet_version_label: str
    session_id: str
    session_label: str
    session_sequence: int
    generation_date: str | None
    created_at: str
    instance_count: int
    artifact_count: int
    page_count: int
    route_count: int
    planned_count: int
    routes_pending_count: int
    rendering_count: int
    generated_count: int
    failed_count: int
    cancelled_count: int
    snapshot_revision: int
    snapshot_sha256: str


@dataclass(frozen=True, slots=True)
class _PacketGenerationReadContext:
    root: Path
    work: ModuleWorkRef
    snapshot_revision: int
    snapshot_sha256: str
    graph: ConcordRecordGraph
    artifact_index: dict[str, ArtifactInstance]
    page_index: dict[str, ArtifactPage]
    session_index: dict[str, Session]


def list_packet_generations(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[PacketGenerationSummary, ...]:
    """List complete generation projections from one exact Activity snapshot."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    context = _load_generation_read_context(root, class_id, activity_id)

    grouped: dict[str, list[PacketInstance]] = {}
    for packet in context.graph.packet_instances:
        grouped.setdefault(packet.generation_id, []).append(packet)

    packet_libraries: dict[str, LoadedPacketLibrary] = {}
    summaries = tuple(
        _generation_summary(
            context,
            generation_id,
            tuple(packets),
            packet_libraries,
        )
        for generation_id, packets in grouped.items()
    )
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.created_at,
                item.generation_id,
            ),
        )
    )


def show_packet_generation(
    class_id: str,
    activity_id: str,
    generation_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> PacketGenerationSummary:
    """Project one exact Packet generation without mutating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet generation is not available: {generation_id}"
        )
    context = _load_generation_read_context(root, class_id, activity_id)
    packets = tuple(
        item
        for item in context.graph.packet_instances
        if item.generation_id == generation_id
    )
    if not packets:
        raise ConcordWorkflowNotFoundError(
            f"Packet generation is not available: {generation_id}"
        )
    return _generation_summary(
        context,
        generation_id,
        packets,
        {},
    )


def _load_generation_read_context(
    root: Path,
    class_id: str,
    activity_id: str,
) -> _PacketGenerationReadContext:
    work = ModuleWorkRef("concord", class_id, activity_id)
    try:
        loaded = load_current_record_graph(
            root,
            work,
            standards_library=_standards(root),
        )
    except ConcordStorageError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {activity_id}"
        ) from error

    graph = cast(ConcordRecordGraph, loaded.graph)
    return _PacketGenerationReadContext(
        root=root,
        work=work,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        graph=graph,
        artifact_index={
            item.artifact_instance_id: item
            for item in graph.artifact_instances
        },
        page_index={
            item.artifact_page_id: item
            for item in graph.artifact_pages
        },
        session_index={
            item.session_id: item
            for item in graph.sessions
        },
    )


def _generation_summary(
    context: _PacketGenerationReadContext,
    generation_id: str,
    packets: tuple[PacketInstance, ...],
    packet_libraries: dict[str, LoadedPacketLibrary],
) -> PacketGenerationSummary:
    if not packets:
        raise ConcordWorkflowNotFoundError(
            f"Packet generation is not available: {generation_id}"
        )

    definition_ids = {item.packet_definition_id for item in packets}
    version_ids = {item.packet_version_id for item in packets}
    activity_ids = {item.activity_id for item in packets}
    session_ids = {item.session_id for item in packets}
    generation_dates = {item.generation_date for item in packets}
    if len(definition_ids) != 1:
        raise _generation_conflict(generation_id, "Packet definition")
    if len(version_ids) != 1:
        raise _generation_conflict(generation_id, "Packet version")
    if activity_ids != {context.work.work_id}:
        raise _generation_conflict(generation_id, "Activity")
    if len(session_ids) != 1:
        raise _generation_conflict(generation_id, "Session")
    if len(generation_dates) != 1:
        raise _generation_conflict(generation_id, "generation date")

    packet_definition_id = next(iter(definition_ids))
    packet_version_id = next(iter(version_ids))
    session_id = next(iter(session_ids))
    generation_date = next(iter(generation_dates))

    session = context.session_index.get(session_id)
    if session is None or session.activity_id != context.work.work_id:
        raise ConcordWorkflowConflictError(
            "Packet generation references an unavailable or contradictory Session."
        )

    library = packet_libraries.get(packet_definition_id)
    if library is None:
        try:
            library = load_current_packet(
                context.root,
                packet_definition_id,
            )
        except PacketStorageError as error:
            raise ConcordWorkflowNotFoundError(
                "Packet dependency is unavailable for generation "
                f"{generation_id}."
            ) from error
        packet_libraries[packet_definition_id] = library

    version = next(
        (
            item
            for item in library.versions
            if item.packet_version_id == packet_version_id
        ),
        None,
    )
    if version is None or version.packet_definition_id != packet_definition_id:
        raise ConcordWorkflowNotFoundError(
            "Exact Packet Version is unavailable for generation "
            f"{generation_id}."
        )

    status_counts = {
        "planned": 0,
        "routes_pending": 0,
        "rendering": 0,
        "generated": 0,
        "failed": 0,
        "cancelled": 0,
    }
    artifact_count = 0
    page_count = 0
    route_count = 0
    seen_artifacts: set[str] = set()
    seen_pages: set[str] = set()

    for packet in packets:
        status_counts[packet.generation_status] += 1
        for binding in packet.artifact_bindings:
            artifact_id = binding.artifact_instance_id
            if artifact_id in seen_artifacts:
                raise ConcordWorkflowConflictError(
                    "Packet generation reuses one Artifact across multiple targets."
                )
            seen_artifacts.add(artifact_id)
            artifact = context.artifact_index.get(artifact_id)
            if (
                artifact is None
                or artifact.packet_instance_id != packet.packet_instance_id
                or artifact.activity_id != context.work.work_id
                or artifact.session_id != session_id
                or artifact.template_version_id != binding.template_version_id
            ):
                raise ConcordWorkflowConflictError(
                    "Packet generation contains contradictory Artifact provenance."
                )
            artifact_count += 1
            for page_id in artifact.page_ids:
                if page_id in seen_pages:
                    raise ConcordWorkflowConflictError(
                        "Packet generation reuses one Artifact Page."
                    )
                seen_pages.add(page_id)
                page = context.page_index.get(page_id)
                if (
                    page is None
                    or page.artifact_instance_id != artifact_id
                ):
                    raise ConcordWorkflowConflictError(
                        "Packet generation contains contradictory Artifact Page "
                        "provenance."
                    )
                page_count += 1
                if page.route_required:
                    route_count += 1

    return PacketGenerationSummary(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        generation_id=generation_id,
        packet_definition_id=packet_definition_id,
        packet_version_id=packet_version_id,
        packet_name=library.definition.name,
        packet_version_label=version.version_label,
        session_id=session_id,
        session_label=session.label or f"Session {session.sequence}",
        session_sequence=session.sequence,
        generation_date=generation_date,
        created_at=min(item.created_provenance.timestamp for item in packets),
        instance_count=len(packets),
        artifact_count=artifact_count,
        page_count=page_count,
        route_count=route_count,
        planned_count=status_counts["planned"],
        routes_pending_count=status_counts["routes_pending"],
        rendering_count=status_counts["rendering"],
        generated_count=status_counts["generated"],
        failed_count=status_counts["failed"],
        cancelled_count=status_counts["cancelled"],
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
    )


def _generation_conflict(
    generation_id: str,
    field: str,
) -> ConcordWorkflowConflictError:
    return ConcordWorkflowConflictError(
        f"Packet generation {generation_id} has contradictory {field} identity."
    )


def _standards(root: Path) -> StandardsLibrary | None:
    try:
        return load_workspace_standards_library(root)
    except (FileNotFoundError, ValueError):
        return None


__all__ = [
    "PacketGenerationSummary",
    "list_packet_generations",
    "show_packet_generation",
]
