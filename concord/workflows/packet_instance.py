"Read-only inspection services for Activity-specific Packet Instances."

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary, load_workspace_standards_library

from concord.model_validation import ConcordRecordGraph
from concord.models import PacketInstance
from concord.storage import load_current_record_graph
from concord.storage_errors import ConcordStorageError
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import ConcordWorkflowNotFoundError


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstanceSummary:
    packet_instance_id: str
    generation_id: str
    packet_definition_id: str
    packet_version_id: str
    activity_id: str
    session_id: str
    audience_kind: str
    target_key: str
    generation_status: str
    artifact_count: int
    page_count: int
    route_count: int
    output_relative_path: str | None
    output_sha256: str | None
    created_at: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstanceDetail:
    summary: PacketInstanceSummary
    packet_instance: PacketInstance
    artifact_instance_ids: tuple[str, ...]
    artifact_page_ids: tuple[str, ...]
    route_ids: tuple[str, ...]


def list_packet_instances(
    class_id: str,
    activity_id: str,
    *,
    generation_id: str | None = None,
    workspace_root: str | Path | None = None,
) -> tuple[PacketInstanceSummary, ...]:
    """List current Packet Instances without creating or mutating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
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

    packets = tuple(
        item
        for item in loaded.graph.packet_instances
        if generation_id is None or item.generation_id == generation_id
    )
    return tuple(
        _summary(loaded.graph, packet)
        for packet in sorted(
            packets,
            key=lambda item: (
                item.created_provenance.timestamp,
                item.generation_id,
                _target_key(item),
                item.packet_instance_id,
            ),
        )
    )


def show_packet_instance(
    class_id: str,
    activity_id: str,
    packet_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> PacketInstanceDetail:
    """Load one current Packet Instance and its bound Artifact/Page identities."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
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
    packet = next(
        (
            item
            for item in loaded.graph.packet_instances
            if item.packet_instance_id == packet_instance_id
        ),
        None,
    )
    if packet is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet Instance is not available: {packet_instance_id}"
        )
    artifacts = {
        item.artifact_instance_id: item for item in loaded.graph.artifact_instances
    }
    pages = {item.artifact_page_id: item for item in loaded.graph.artifact_pages}
    artifact_ids = tuple(
        binding.artifact_instance_id for binding in packet.artifact_bindings
    )
    page_ids: list[str] = []
    route_ids: list[str] = []
    for artifact_id in artifact_ids:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise ConcordWorkflowNotFoundError(
                f"Packet Artifact is not available: {artifact_id}"
            )
        page_ids.extend(artifact.page_ids)
        for page_id in artifact.page_ids:
            page = pages.get(page_id)
            if page is None:
                raise ConcordWorkflowNotFoundError(
                    f"Packet Artifact Page is not available: {page_id}"
                )
            if page.route_id is not None:
                route_ids.append(page.route_id)
    return PacketInstanceDetail(
        summary=_summary(loaded.graph, packet),
        packet_instance=packet,
        artifact_instance_ids=artifact_ids,
        artifact_page_ids=tuple(page_ids),
        route_ids=tuple(route_ids),
    )


def _summary(
    graph: ConcordRecordGraph,
    packet: PacketInstance,
) -> PacketInstanceSummary:
    artifacts = {
        item.artifact_instance_id: item for item in graph.artifact_instances
    }
    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    page_count = 0
    route_count = 0
    for binding in packet.artifact_bindings:
        artifact = artifacts.get(binding.artifact_instance_id)
        if artifact is None:
            continue
        page_count += len(artifact.page_ids)
        for page_id in artifact.page_ids:
            page = pages.get(page_id)
            if page is not None and page.route_required:
                route_count += 1
    return PacketInstanceSummary(
        packet_instance_id=packet.packet_instance_id,
        generation_id=packet.generation_id,
        packet_definition_id=packet.packet_definition_id,
        packet_version_id=packet.packet_version_id,
        activity_id=packet.activity_id,
        session_id=packet.session_id,
        audience_kind=packet.target_context.audience_kind,
        target_key=_target_key(packet),
        generation_status=packet.generation_status,
        artifact_count=len(packet.artifact_bindings),
        page_count=page_count,
        route_count=route_count,
        output_relative_path=packet.output_relative_path,
        output_sha256=packet.output_sha256,
        created_at=packet.created_provenance.timestamp,
    )


def _target_key(packet: PacketInstance) -> str:
    target = packet.target_context
    if target.audience_kind == "activity":
        return f"activity:{target.activity_id}"
    if target.audience_kind == "group":
        return f"group:{target.group_id or '-'}"
    if target.audience_kind == "participant":
        participant = target.participant_reference
        return (
            "participant:-"
            if participant is None
            else f"participant:{participant.participant_id}"
        )
    if target.audience_kind == "role":
        return f"role:{target.role_assignment_id or '-'}"
    actor = target.actor_reference
    return "teacher:-" if actor is None else f"teacher:{actor.actor_id}"


def _standards(root: Path) -> StandardsLibrary | None:
    try:
        return load_workspace_standards_library(root)
    except (FileNotFoundError, ValueError):
        return None


__all__ = [
    "PacketInstanceDetail",
    "PacketInstanceSummary",
    "list_packet_instances",
    "show_packet_instance",
]
