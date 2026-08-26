"Packet-backed printable rendering for Activity-specific Concord output."

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pds_core.pds2 import serialize_pds2_payload
from pds_core.route_registrations import load_route_registration
from pds_core.routes import safe_module_work_descendant
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary, load_workspace_standards_library
from PIL import Image

from concord.model_conversion import Record
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ArtifactInstance,
    ArtifactPage,
    PacketInstance,
    PacketInstanceArtifactBinding,
    TemplateVersion,
)
from concord.routing.starter_layout_pdf import (
    StarterPageRenderContext,
    render_starter_layout_images,
    starter_images_to_pdf,
)
from concord.starter_templates.layout import (
    STARTER_LAYOUT_SCHEMA,
    StarterLayoutDocument,
    starter_layout_from_json_bytes,
)
from concord.storage import commit_record_batch, load_current_record_graph
from concord.storage_errors import ConcordStorageConflictError
from concord.template_storage import (
    TemplateStorageError,
    load_current_template,
    load_template_rendering_specification,
)
from concord.workflows.artifact_page import (
    concord_route_registration,
    validate_concord_route_registration,
)
from concord.workflows.context import (
    ensure_mutating_workspace_root,
    require_core_class,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderPacketInstanceRequest:
    class_id: str
    activity_id: str
    packet_instance_id: str
    actor: WorkflowActor
    expected_snapshot_revision: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderPacketInstanceResult:
    work: ModuleWorkRef
    packet_instance_id: str
    generation_id: str
    output_path: Path
    output_sha256: str
    page_count: int
    route_count: int
    payloads: tuple[str, ...]
    commit: WorkflowCommitResult
    output_installed: bool
    replayed: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderPacketGenerationRequest:
    class_id: str
    activity_id: str
    generation_id: str
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class RenderPacketGenerationResult:
    generation_id: str
    packets: tuple[RenderPacketInstanceResult, ...]

    @property
    def page_count(self) -> int:
        return sum(item.page_count for item in self.packets)

    @property
    def route_count(self) -> int:
        return sum(item.route_count for item in self.packets)


class PacketRenderPartialSuccessError(ConcordWorkflowError):
    """Packet PDF is durable but final native lifecycle state is incomplete."""

    def __init__(
        self,
        *,
        result: RenderPacketInstanceResult,
        cause: Exception,
    ) -> None:
        super().__init__(
            "Packet PDF is durable, but generated lifecycle state was not committed."
        )
        self.result = result
        self.__cause__ = cause


class PacketGenerationRenderPartialSuccessError(ConcordWorkflowError):
    """Some target-specific Packet PDFs completed before a later target failed."""

    def __init__(
        self,
        *,
        generation_id: str,
        completed: tuple[RenderPacketInstanceResult, ...],
        cause: Exception,
    ) -> None:
        super().__init__(
            f"Packet generation {generation_id} rendered "
            f"{len(completed)} target Packet(s) before failure."
        )
        self.generation_id = generation_id
        self.completed = completed
        self.__cause__ = cause


@dataclass(frozen=True, slots=True)
class _RenderableArtifact:
    binding: PacketInstanceArtifactBinding
    artifact: ArtifactInstance
    pages: tuple[ArtifactPage, ...]
    template_version: TemplateVersion
    layout: StarterLayoutDocument


def render_packet_instance(
    request: RenderPacketInstanceRequest,
    *,
    workspace_root: str | Path | None = None,
) -> RenderPacketInstanceResult:
    """Render/re-render one exact Packet Instance without allocating new routes."""
    if not isinstance(request, RenderPacketInstanceRequest):
        raise ConcordWorkflowValidationError(
            "request must be RenderPacketInstanceRequest."
        )
    if not isinstance(request.actor, WorkflowActor):
        raise ConcordWorkflowValidationError("actor must be WorkflowActor.")

    root = ensure_mutating_workspace_root(workspace_root).root
    require_core_class(root, request.class_id)
    work = ModuleWorkRef("concord", request.class_id, request.activity_id)
    library = _standards(root)
    loaded = load_current_record_graph(
        root,
        work,
        standards_library=library,
    )
    if (
        request.expected_snapshot_revision is not None
        and loaded.snapshot_revision != request.expected_snapshot_revision
    ):
        raise ConcordStorageConflictError(
            f"expected snapshot {request.expected_snapshot_revision}, "
            f"found {loaded.snapshot_revision}."
        )
    graph = cast(ConcordRecordGraph, loaded.graph)
    packet = _require_packet(
        graph,
        request.packet_instance_id,
        request.activity_id,
    )
    if packet.generation_status == "routes_pending":
        raise ConcordWorkflowValidationError(
            "Packet routes are not ready; resume Packet instantiation first."
        )
    if packet.generation_status not in {"rendering", "generated"}:
        raise ConcordWorkflowValidationError(
            "Packet Instance is not in a renderable lifecycle state."
        )

    renderables = _resolve_renderables(root, work, graph, packet)
    images: list[Image.Image] = []
    payloads: list[str] = []
    for renderable in renderables:
        contexts, artifact_payloads = _render_contexts(
            root,
            work,
            renderable,
        )
        images.extend(
            render_starter_layout_images(
                renderable.layout,
                contexts,
            )
        )
        payloads.extend(artifact_payloads)

    data = starter_images_to_pdf(
        tuple(images),
        created_at=packet.created_provenance.timestamp,
    )
    digest = hashlib.sha256(data).hexdigest()
    relative = f"rendered/packets/{packet.packet_instance_id}.pdf"

    if packet.generation_status == "generated":
        if (
            packet.output_relative_path != relative
            or packet.output_sha256 != digest
        ):
            raise ConcordWorkflowConflictError(
                "generated Packet output metadata contradicts deterministic re-render."
            )

    target = _packet_output_target(root, work, relative)
    installed = _safe_install(target, data)
    base_result = RenderPacketInstanceResult(
        work=work,
        packet_instance_id=packet.packet_instance_id,
        generation_id=packet.generation_id,
        output_path=target,
        output_sha256=digest,
        page_count=len(images),
        route_count=len(payloads),
        payloads=tuple(payloads),
        commit=WorkflowCommitResult(
            work=work,
            snapshot_revision=loaded.snapshot_revision,
            snapshot_sha256=loaded.snapshot_sha256,
            changed_records=(),
            no_op=True,
        ),
        output_installed=installed,
        replayed=packet.generation_status == "generated",
    )

    updates = _lifecycle_updates(packet, renderables, relative, digest)
    if not updates:
        return base_result
    try:
        committed = commit_record_batch(
            root,
            work,
            updates,
            expected_snapshot_revision=loaded.snapshot_revision,
            standards_library=library,
        )
    except Exception as error:
        raise PacketRenderPartialSuccessError(
            result=base_result,
            cause=error,
        ) from error
    return RenderPacketInstanceResult(
        work=work,
        packet_instance_id=packet.packet_instance_id,
        generation_id=packet.generation_id,
        output_path=target,
        output_sha256=digest,
        page_count=len(images),
        route_count=len(payloads),
        payloads=tuple(payloads),
        commit=WorkflowCommitResult.from_storage(committed),
        output_installed=installed,
        replayed=False,
    )


def render_packet_generation(
    request: RenderPacketGenerationRequest,
    *,
    workspace_root: str | Path | None = None,
) -> RenderPacketGenerationResult:
    """Render every target Packet in stable target order.

    Partial success is surfaced explicitly if a later target fails.
    """
    if not isinstance(request, RenderPacketGenerationRequest):
        raise ConcordWorkflowValidationError(
            "request must be RenderPacketGenerationRequest."
        )
    root = ensure_mutating_workspace_root(workspace_root).root
    require_core_class(root, request.class_id)
    work = ModuleWorkRef("concord", request.class_id, request.activity_id)
    loaded = load_current_record_graph(
        root,
        work,
        standards_library=_standards(root),
    )
    graph = cast(ConcordRecordGraph, loaded.graph)
    packets = tuple(
        sorted(
            (
                item
                for item in graph.packet_instances
                if item.generation_id == request.generation_id
            ),
            key=lambda item: _target_key(item),
        )
    )
    if not packets:
        raise ConcordWorkflowNotFoundError(
            f"Packet generation is unavailable: {request.generation_id}"
        )

    completed: list[RenderPacketInstanceResult] = []
    try:
        for packet in packets:
            completed.append(
                render_packet_instance(
                    RenderPacketInstanceRequest(
                        class_id=request.class_id,
                        activity_id=request.activity_id,
                        packet_instance_id=packet.packet_instance_id,
                        actor=request.actor,
                    ),
                    workspace_root=root,
                )
            )
    except Exception as error:
        raise PacketGenerationRenderPartialSuccessError(
            generation_id=request.generation_id,
            completed=tuple(completed),
            cause=error,
        ) from error
    return RenderPacketGenerationResult(
        generation_id=request.generation_id,
        packets=tuple(completed),
    )



def _standards(root: Path) -> StandardsLibrary | None:
    try:
        return load_workspace_standards_library(root)
    except (FileNotFoundError, ValueError):
        return None


def _require_packet(
    graph: ConcordRecordGraph,
    packet_instance_id: str,
    activity_id: str,
) -> PacketInstance:
    packet = next(
        (
            item
            for item in graph.packet_instances
            if item.packet_instance_id == packet_instance_id
        ),
        None,
    )
    if packet is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet Instance is unavailable: {packet_instance_id}"
        )
    if packet.activity_id != activity_id:
        raise ConcordWorkflowValidationError(
            "Packet Instance belongs to another Activity."
        )
    return packet


def _resolve_renderables(
    root: Path,
    work: ModuleWorkRef,
    graph: ConcordRecordGraph,
    packet: PacketInstance,
) -> tuple[_RenderableArtifact, ...]:
    artifacts = {
        item.artifact_instance_id: item for item in graph.artifact_instances
    }
    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    result: list[_RenderableArtifact] = []
    for binding in packet.artifact_bindings:
        artifact = artifacts.get(binding.artifact_instance_id)
        if (
            artifact is None
            or artifact.packet_instance_id != packet.packet_instance_id
            or artifact.template_version_id != binding.template_version_id
        ):
            raise ConcordWorkflowConflictError(
                "Packet/Artifact provenance is contradictory."
            )
        artifact_pages = tuple(
            pages[page_id]
            for page_id in artifact.page_ids
            if page_id in pages
        )
        if len(artifact_pages) != len(artifact.page_ids):
            raise ConcordWorkflowConflictError(
                "Packet Artifact is missing one or more canonical Pages."
            )
        if tuple(item.page_number for item in artifact_pages) != tuple(
            range(1, len(artifact_pages) + 1)
        ):
            raise ConcordWorkflowConflictError(
                "Packet Artifact page order is not contiguous."
            )
        version, layout = _load_exact_layout(
            root,
            binding.template_id,
            binding.template_version_id,
        )
        if len(version.page_manifest) != len(artifact_pages):
            raise ConcordWorkflowConflictError(
                "Template page manifest disagrees with generated Artifact."
            )
        for definition, page in zip(
            version.page_manifest,
            artifact_pages,
            strict=True,
        ):
            if (
                definition.sequence != page.page_number
                or definition.page_kind != page.page_kind
                or definition.return_expected != page.return_expected
                or definition.route_required != page.route_required
            ):
                raise ConcordWorkflowConflictError(
                    "Template page contract disagrees with generated Artifact Page."
                )
        result.append(
            _RenderableArtifact(
                binding=binding,
                artifact=artifact,
                pages=artifact_pages,
                template_version=version,
                layout=layout,
            )
        )
    return tuple(result)


def _load_exact_layout(
    root: Path,
    template_id: str,
    template_version_id: str,
) -> tuple[TemplateVersion, StarterLayoutDocument]:
    try:
        library = load_current_template(root, template_id)
        version = next(
            (
                item
                for item in library.versions
                if item.template_version_id == template_version_id
            ),
            None,
        )
        if version is None:
            raise ConcordWorkflowNotFoundError(
                f"Template Version is unavailable: {template_version_id}"
            )
        data = load_template_rendering_specification(
            root,
            template_id,
            template_version_id,
        )
    except TemplateStorageError as error:
        raise ConcordWorkflowNotFoundError(
            f"Template dependency is unavailable: {template_id}:{template_version_id}"
        ) from error
    if version.rendering_contract_version != STARTER_LAYOUT_SCHEMA:
        raise ConcordWorkflowValidationError(
            "Packet renderer does not support Template rendering contract "
            f"{version.rendering_contract_version!r}."
        )
    layout = starter_layout_from_json_bytes(data)
    return version, layout


def _render_contexts(
    root: Path,
    work: ModuleWorkRef,
    renderable: _RenderableArtifact,
) -> tuple[tuple[StarterPageRenderContext, ...], tuple[str, ...]]:
    base_values = {
        item.input_key: item.value
        for item in renderable.binding.rendering_values
    }
    contexts: list[StarterPageRenderContext] = []
    payloads: list[str] = []
    for layout_page, artifact_page in zip(
        renderable.layout.pages,
        renderable.pages,
        strict=True,
    ):
        values = dict(base_values)
        if artifact_page.route_required:
            expected = concord_route_registration(work, artifact_page)
            actual = load_route_registration(root, expected.locator)
            validate_concord_route_registration(actual)
            if actual != expected:
                raise ConcordWorkflowConflictError(
                    "Core route registration contradicts generated Artifact Page."
                )
            payload = serialize_pds2_payload(actual.locator)
            values["pds2_route_payload"] = payload
            values["human_fallback"] = actual.human_fallback
            payloads.append(payload)
        else:
            values.pop("pds2_route_payload", None)
            values.pop("human_fallback", None)

        required = set(layout_page.header_input_keys)
        missing = sorted(
            key
            for key in required
            if key not in values
            and key not in {"teacher_prompt", "session_label", "current_date"}
        )
        if missing:
            raise ConcordWorkflowValidationError(
                "Packet rendering is missing required header values: "
                + ", ".join(missing)
            )
        contexts.append(
            StarterPageRenderContext(
                page_key=layout_page.page_key,
                values=tuple(sorted(values.items())),
            )
        )
    return tuple(contexts), tuple(payloads)


def _lifecycle_updates(
    packet: PacketInstance,
    renderables: tuple[_RenderableArtifact, ...],
    relative: str,
    digest: str,
) -> tuple[Record, ...]:
    updates: list[Record] = []
    for renderable in renderables:
        artifact = renderable.artifact
        revised_pages = tuple(
            (
                page
                if page.page_status != "planned"
                else _replace_page_generated(page)
            )
            for page in renderable.pages
        )
        updates.extend(
            page
            for old, page in zip(
                renderable.pages,
                revised_pages,
                strict=True,
            )
            if page != old
        )
        revised_artifact = artifact
        if artifact.generation_status == "planned":
            revised_artifact = _replace_artifact_generated(revised_artifact)
        if revised_artifact.artifact_status == "planned":
            revised_artifact = _replace_artifact_status_generated(
                revised_artifact
            )
        if revised_artifact != artifact:
            updates.append(revised_artifact)

    revised_packet = packet
    if packet.generation_status == "rendering":
        revised_packet = _replace_packet_generated(
            packet,
            relative,
            digest,
        )
    if revised_packet != packet:
        updates.append(revised_packet)
    return tuple(updates)


def _replace_page_generated(page: ArtifactPage) -> ArtifactPage:
    from dataclasses import replace

    return replace(page, page_status="generated")


def _replace_artifact_generated(
    artifact: ArtifactInstance,
) -> ArtifactInstance:
    from dataclasses import replace

    return replace(artifact, generation_status="completed")


def _replace_artifact_status_generated(
    artifact: ArtifactInstance,
) -> ArtifactInstance:
    from dataclasses import replace

    return replace(artifact, artifact_status="generated")


def _replace_packet_generated(
    packet: PacketInstance,
    relative: str,
    digest: str,
) -> PacketInstance:
    from dataclasses import replace

    return replace(
        packet,
        generation_status="generated",
        output_relative_path=relative,
        output_sha256=digest,
    )


def _packet_output_target(
    root: Path,
    work: ModuleWorkRef,
    relative: str,
) -> Path:
    target = safe_module_work_descendant(root, work, relative)
    rendered_root = safe_module_work_descendant(root, work, "rendered")
    try:
        target.resolve(strict=False).relative_to(
            rendered_root.resolve(strict=False)
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise ConcordWorkflowValidationError(
            "Packet output must remain beneath rendered/."
        ) from error
    if target.suffix.lower() != ".pdf":
        raise ConcordWorkflowValidationError("Packet output must be a PDF.")
    return target


def _safe_install(target: Path, data: bytes) -> bool:
    current = target
    while True:
        if current.is_symlink():
            raise ConcordWorkflowValidationError(
                f"Packet render path traverses a symlink: {current}"
            )
        if current == current.parent:
            break
        current = current.parent
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file() or target.read_bytes() != data:
            raise ConcordWorkflowConflictError(
                f"different Packet render already exists: {target}"
            )
        return False

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=target.parent,
            prefix=".packet-render.",
            suffix=".tmp",
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if target.exists():
            if target.is_file() and target.read_bytes() == data:
                temporary.unlink(missing_ok=True)
                temporary = None
                return False
            raise ConcordWorkflowConflictError(
                f"Packet render appeared concurrently: {target}"
            )
        os.replace(temporary, target)
        temporary = None
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _target_key(packet: PacketInstance) -> tuple[int, str]:
    target = packet.target_context
    order = {
        "activity": 0,
        "group": 1,
        "participant": 2,
        "role": 3,
        "teacher": 4,
    }
    if target.audience_kind == "activity":
        key = target.activity_id
    elif target.audience_kind == "group":
        key = target.group_id or ""
    elif target.audience_kind == "participant":
        key = (
            ""
            if target.participant_reference is None
            else target.participant_reference.participant_id
        )
    elif target.audience_kind == "role":
        key = target.role_assignment_id or ""
    else:
        key = (
            ""
            if target.actor_reference is None
            else target.actor_reference.actor_id
        )
    return order[target.audience_kind], key


__all__ = [
    "PacketGenerationRenderPartialSuccessError",
    "PacketRenderPartialSuccessError",
    "RenderPacketGenerationRequest",
    "RenderPacketGenerationResult",
    "RenderPacketInstanceRequest",
    "RenderPacketInstanceResult",
    "render_packet_generation",
    "render_packet_instance",
]
