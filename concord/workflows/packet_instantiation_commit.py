"Durable Activity Packet generation and Core PDS2 route reconciliation."

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, time, timezone
from pathlib import Path
from uuid import uuid4

from pds_core.identifiers import IdentifierValidationError, validate_identifier
from pds_core.pds2 import serialize_pds2_payload
from pds_core.route_ids import generate_route_id
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary, load_workspace_standards_library

from concord.model_conversion import Record
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactSubject,
    PacketInstance,
    PacketInstanceArtifactBinding,
    PacketRenderingValue,
    PacketTargetContext,
    Provenance,
    SubjectReference,
    TemplatePageDefinition,
)
from concord.storage import commit_record_batch, load_current_record_graph
from concord.storage_errors import ConcordStorageConflictError, ConcordStorageError
from concord.storage_models import ConcordLoadedRecordGraph
from concord.workflows.artifact_page import (
    concord_route_registration,
    reconcile_concord_route_registration,
)
from concord.workflows.context import Clock, provenance, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowCommitResult
from concord.workflows.packet_instantiation import (
    PlannedPacketArtifact,
    PreparedPacketInstantiation,
    prepare_packet_instantiation,
)

_GENERATION_PREFIX = "generation_"
_PACKET_INSTANCE_PREFIX = "packet_instance_"
_ARTIFACT_PREFIX = "artifact_"
_PAGE_PREFIX = "page_"
_AUTHOR_PREFIX = "artifact_author_"
_SUBJECT_PREFIX = "artifact_subject_"


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketCommittedPage:
    packet_instance_id: str
    artifact_instance_id: str
    artifact_page_id: str
    page_number: int
    route_id: str | None
    pds2_payload: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstantiationCommitResult:
    generation_id: str
    review_digest: str
    native_commit: WorkflowCommitResult
    lifecycle_commit: WorkflowCommitResult | None
    packet_instance_ids: tuple[str, ...]
    artifact_instance_ids: tuple[str, ...]
    pages: tuple[PacketCommittedPage, ...]
    routes_expected: int
    routes_verified: int
    replayed: bool

    @property
    def artifact_page_ids(self) -> tuple[str, ...]:
        return tuple(item.artifact_page_id for item in self.pages)

    @property
    def route_ids(self) -> tuple[str, ...]:
        return tuple(
            item.route_id for item in self.pages if item.route_id is not None
        )


class PacketInstantiationPartialSuccessError(ConcordWorkflowError):
    """Native generation state is durable but later reconciliation is incomplete."""

    def __init__(
        self,
        message: str,
        *,
        stage: str,
        result: PacketInstantiationCommitResult,
        cause: Exception,
    ) -> None:
        super().__init__(message)
        self.stage = stage
        self.result = result
        self.__cause__ = cause


@dataclass(frozen=True, slots=True)
class _BuiltGeneration:
    records: tuple[Record, ...]
    packet_instance_ids: tuple[str, ...]


def commit_packet_instantiation(
    prepared: PreparedPacketInstantiation,
    *,
    workspace_root: str | Path | None = None,
    generation_id: str | None = None,
    clock: Clock | None = None,
) -> PacketInstantiationCommitResult:
    """Commit one reviewed generation, then reconcile its immutable Core routes."""
    if not isinstance(prepared, PreparedPacketInstantiation):
        raise ConcordWorkflowValidationError(
            "prepared must be PreparedPacketInstantiation."
        )
    if not prepared.ready_for_commit:
        raise ConcordWorkflowValidationError(
            "Packet generation preview contains unresolved blocking diagnostics."
        )
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("workspace is not available.")

    requested_generation_id = (
        None if generation_id is None else _identifier(generation_id, "generation_id")
    )
    work = _work(prepared.request.class_id, prepared.request.activity_id)
    loaded = _load_graph(root, work)
    existing = _generation_packets(loaded.graph, requested_generation_id)
    if existing:
        if any(item.review_digest != prepared.review_digest for item in existing):
            raise ConcordWorkflowConflictError(
                "generation_id belongs to a different reviewed Packet generation."
            )
        return _resume_durable_generation(
            root,
            work,
            requested_generation_id or "",
            loaded.graph,
            loaded.snapshot_revision,
            loaded.snapshot_sha256,
            replayed=True,
        )

    reviewed = _revalidate_review(prepared, root)
    generation = requested_generation_id or _new_id(_GENERATION_PREFIX)
    if _generation_packets(loaded.graph, generation):
        raise ConcordWorkflowConflictError(
            f"generation identity already exists: {generation}"
        )

    created = provenance(prepared.request.actor, clock=clock, source_kind="generated")
    built = _build_generation(reviewed, generation, created)

    try:
        committed = commit_record_batch(
            root,
            work,
            built.records,
            expected_snapshot_revision=reviewed.activity_snapshot_revision,
            standards_library=_standards(root),
        )
    except ConcordStorageConflictError as error:
        raise ConcordWorkflowConflictError(
            "Activity state changed after Packet generation review."
        ) from error

    native_commit = WorkflowCommitResult.from_storage(committed)
    durable = _load_graph(root, work)
    return _resume_durable_generation(
        root,
        work,
        generation,
        durable.graph,
        durable.snapshot_revision,
        durable.snapshot_sha256,
        replayed=False,
        native_commit=native_commit,
    )


def resume_packet_instantiation(
    class_id: str,
    activity_id: str,
    generation_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> PacketInstantiationCommitResult:
    """Resume route/lifecycle reconciliation from durable native generation state."""
    class_key = _identifier(class_id, "class_id")
    activity_key = _identifier(activity_id, "activity_id")
    generation_key = _identifier(generation_id, "generation_id")
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("workspace is not available.")
    work = _work(class_key, activity_key)
    loaded = _load_graph(root, work)
    if not _generation_packets(loaded.graph, generation_key):
        raise ConcordWorkflowNotFoundError(
            f"Packet generation is not available: {generation_key}"
        )
    return _resume_durable_generation(
        root,
        work,
        generation_key,
        loaded.graph,
        loaded.snapshot_revision,
        loaded.snapshot_sha256,
        replayed=True,
    )


def _identifier(value: object, field_name: str) -> str:
    try:
        return validate_identifier(value, field_name)  # type: ignore[arg-type]
    except (IdentifierValidationError, TypeError, ValueError) as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _new_id(prefix: str) -> str:
    return prefix + uuid4().hex


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef("concord", class_id, activity_id)


def _standards(root: Path) -> StandardsLibrary | None:
    try:
        return load_workspace_standards_library(root)
    except (FileNotFoundError, ValueError):
        return None


def _load_graph(root: Path, work: ModuleWorkRef) -> ConcordLoadedRecordGraph:
    try:
        return load_current_record_graph(
            root,
            work,
            standards_library=_standards(root),
        )
    except (ConcordStorageError, FileNotFoundError, ValueError) as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {work.work_id}"
        ) from error


def _generation_packets(
    graph: ConcordRecordGraph,
    generation_id: str | None,
) -> tuple[PacketInstance, ...]:
    if generation_id is None:
        return ()
    return tuple(
        sorted(
            (
                item
                for item in graph.packet_instances
                if item.generation_id == generation_id
            ),
            key=lambda item: _target_key(item.target_context),
        )
    )


def _revalidate_review(
    prepared: PreparedPacketInstantiation,
    root: Path,
) -> PreparedPacketInstantiation:
    reviewed_date = date.fromisoformat(prepared.generation_date)
    def fixed_clock() -> datetime:
        return datetime.combine(
            reviewed_date,
            time(hour=12),
            tzinfo=timezone.utc,
        )
    current = prepare_packet_instantiation(
        prepared.request,
        workspace_root=root,
        clock=fixed_clock,
    )
    if current.review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "reviewed Packet generation is stale; prepare a new preview."
        )
    return current


def _build_generation(
    prepared: PreparedPacketInstantiation,
    generation_id: str,
    created: Provenance,
) -> _BuiltGeneration:
    source_by_version = {
        item.template_version_id: item.template_version
        for item in prepared.template_sources
    }
    records: list[Record] = []
    packet_ids: list[str] = []

    for target_plan in prepared.target_plans:
        packet_instance_id = _new_id(_PACKET_INSTANCE_PREFIX)
        packet_ids.append(packet_instance_id)
        bindings: list[PacketInstanceArtifactBinding] = []

        for planned in target_plan.artifacts:
            template_version = source_by_version.get(planned.template_version_id)
            if template_version is None:
                raise ConcordWorkflowValidationError(
                    "reviewed generation lost exact Template Version provenance."
                )
            artifact_id = _new_id(_ARTIFACT_PREFIX)
            pages = _build_pages(
                prepared.request.activity_id,
                artifact_id,
                template_version.page_manifest,
                created,
            )
            artifact = ArtifactInstance(
                artifact_instance_id=artifact_id,
                template_version_id=planned.template_version_id,
                activity_id=prepared.request.activity_id,
                artifact_category=planned.artifact_category,
                generation_status="planned",
                expected_return_status=planned.expected_return_status,
                artifact_status="planned",
                privacy_policy=planned.effective_privacy_policy,
                page_ids=tuple(item.artifact_page_id for item in pages),
                created_provenance=created,
                packet_instance_id=packet_instance_id,
                session_id=prepared.request.session_id,
                group_id=target_plan.target_context.group_id,
            )
            records.append(artifact)
            records.extend(pages)

            bindings.append(
                PacketInstanceArtifactBinding(
                    packet_component_id=planned.packet_component_id,
                    component_sequence=planned.component_sequence,
                    copy_index=planned.copy_index,
                    template_id=planned.template_id,
                    template_version_id=planned.template_version_id,
                    artifact_instance_id=artifact_id,
                    rendering_values=_frozen_rendering_values(planned),
                )
            )
            author = _build_author(
                artifact_id,
                planned,
                created,
            )
            if author is not None:
                records.append(author)
            subject = _build_subject(artifact_id, planned, created)
            if subject is not None:
                records.append(subject)

        packet = PacketInstance(
            packet_instance_id=packet_instance_id,
            generation_id=generation_id,
            packet_definition_id=prepared.packet_definition.packet_definition_id,
            packet_version_id=prepared.packet_version.packet_version_id,
            activity_id=prepared.request.activity_id,
            session_id=prepared.request.session_id,
            target_context=target_plan.target_context,
            artifact_bindings=tuple(bindings),
            generation_status="routes_pending",
            created_provenance=created,
            review_digest=prepared.review_digest,
            generation_date=prepared.generation_date,
        )
        records.append(packet)

    return _BuiltGeneration(tuple(records), tuple(packet_ids))


def _build_pages(
    activity_id: str,
    artifact_instance_id: str,
    manifest: tuple[TemplatePageDefinition, ...],
    created: Provenance,
) -> tuple[ArtifactPage, ...]:
    pages: list[ArtifactPage] = []
    count = len(manifest)
    for definition in manifest:
        page_id = _new_id(_PAGE_PREFIX)
        route_id = generate_route_id() if definition.route_required else None
        fallback = (
            f"Concord {activity_id} page {page_id}"
            if definition.route_required
            else None
        )
        pages.append(
            ArtifactPage(
                artifact_page_id=page_id,
                artifact_instance_id=artifact_instance_id,
                page_number=definition.sequence,
                page_kind=definition.page_kind,
                return_expected=definition.return_expected,
                route_required=definition.route_required,
                page_status="planned",
                created_provenance=created,
                expected_page_count=count,
                route_id=route_id,
                human_fallback=fallback,
            )
        )
    return tuple(pages)


def _frozen_rendering_values(
    planned: PlannedPacketArtifact,
) -> tuple[PacketRenderingValue, ...]:
    values: list[PacketRenderingValue] = []
    for item in planned.rendering_inputs:
        if item.status != "resolved":
            continue
        if item.value is None:
            raise ConcordWorkflowValidationError(
                "resolved rendering input is missing its exact value."
            )
        if item.source_kind in {"pds2_route_payload", "human_fallback"}:
            continue
        values.append(
            PacketRenderingValue(
                input_key=item.input_key,
                source_kind=item.source_kind,
                value_kind=item.value_kind,
                value=item.value,
            )
        )
    return tuple(values)


def _build_author(
    artifact_instance_id: str,
    planned: PlannedPacketArtifact,
    created: Provenance,
) -> ArtifactAuthor | None:
    reference = planned.proposed_author_reference
    mode = planned.authorship_mode
    if reference is None or mode is None:
        return None
    return ArtifactAuthor(
        artifact_author_id=_new_id(_AUTHOR_PREFIX),
        artifact_instance_id=artifact_instance_id,
        author_reference=reference,
        authorship_mode=mode,
        attribution_status="proposed",
        attribution_source="system",
        created_provenance=created,
        privacy_policy=planned.effective_privacy_policy,
    )


def _build_subject(
    artifact_instance_id: str,
    planned: PlannedPacketArtifact,
    created: Provenance,
) -> ArtifactSubject | None:
    reference = planned.proposed_subject_reference
    if reference is None:
        return None
    return ArtifactSubject(
        artifact_subject_id=_new_id(_SUBJECT_PREFIX),
        artifact_instance_id=artifact_instance_id,
        subject_reference=reference,
        subject_role=_subject_role(reference),
        confirmation_status="proposed",
        assignment_source="system",
        created_provenance=created,
        privacy_policy=planned.effective_privacy_policy,
    )


def _subject_role(reference: SubjectReference) -> str:
    return {
        "core_student": "observed_participant",
        "concord_group": "represented_group",
        "concord_session": "session_context",
        "concord_activity": "activity_context",
    }.get(reference.subject_kind, "general_subject")


def _resume_durable_generation(
    root: Path,
    work: ModuleWorkRef,
    generation_id: str,
    graph: ConcordRecordGraph,
    snapshot_revision: int,
    snapshot_sha256: str,
    *,
    replayed: bool,
    native_commit: WorkflowCommitResult | None = None,
) -> PacketInstantiationCommitResult:
    packets = _generation_packets(graph, generation_id)
    if not packets:
        raise ConcordWorkflowNotFoundError(
            f"Packet generation is not available: {generation_id}"
        )
    _validate_durable_generation(graph, packets)

    no_op_native = WorkflowCommitResult(
        work=work,
        snapshot_revision=snapshot_revision,
        snapshot_sha256=snapshot_sha256,
        changed_records=(),
        no_op=True,
    )
    initial_commit = native_commit or no_op_native
    pages = _generation_pages(graph, packets)
    routes_expected = sum(item.route_required for item in pages)
    verified = 0

    result = _commit_result(
        work=work,
        graph=graph,
        packets=packets,
        pages=pages,
        native_commit=initial_commit,
        lifecycle_commit=None,
        routes_expected=routes_expected,
        routes_verified=0,
        replayed=replayed,
    )
    try:
        for page in pages:
            if not page.route_required:
                continue
            registration = concord_route_registration(work, page)
            reconcile_concord_route_registration(root, registration)
            verified += 1
    except Exception as error:
        raise PacketInstantiationPartialSuccessError(
            "Packet generation state is durable, but Core route reconciliation "
            f"stopped after {verified} of {routes_expected} routes.",
            stage="route_reconciliation",
            result=replace(result, routes_verified=verified),
            cause=error,
        ) from error

    current = _load_graph(root, work)
    current_packets = _generation_packets(current.graph, generation_id)
    _validate_durable_generation(current.graph, current_packets)

    invalid_status = tuple(
        item.generation_status
        for item in current_packets
        if item.generation_status not in {"routes_pending", "rendering", "generated"}
    )
    if invalid_status:
        raise ConcordWorkflowConflictError(
            "Packet generation lifecycle is not recoverable from its current state."
        )

    updates = tuple(
        replace(item, generation_status="rendering")
        for item in current_packets
        if item.generation_status == "routes_pending"
    )
    lifecycle_commit: WorkflowCommitResult
    if updates:
        try:
            committed = commit_record_batch(
                root,
                work,
                updates,
                expected_snapshot_revision=current.snapshot_revision,
                standards_library=_standards(root),
            )
        except Exception as error:
            partial = _commit_result(
                work=work,
                graph=current.graph,
                packets=current_packets,
                pages=_generation_pages(current.graph, current_packets),
                native_commit=initial_commit,
                lifecycle_commit=None,
                routes_expected=routes_expected,
                routes_verified=verified,
                replayed=replayed,
            )
            raise PacketInstantiationPartialSuccessError(
                "All Core routes are durable, but Packet generation lifecycle "
                "did not advance to rendering readiness.",
                stage="lifecycle_transition",
                result=partial,
                cause=error,
            ) from error
        lifecycle_commit = WorkflowCommitResult.from_storage(committed)
    else:
        lifecycle_commit = WorkflowCommitResult(
            work=work,
            snapshot_revision=current.snapshot_revision,
            snapshot_sha256=current.snapshot_sha256,
            changed_records=(),
            no_op=True,
        )

    final = _load_graph(root, work)
    final_packets = _generation_packets(final.graph, generation_id)
    _validate_durable_generation(final.graph, final_packets)
    final_pages = _generation_pages(final.graph, final_packets)
    return _commit_result(
        work=work,
        graph=final.graph,
        packets=final_packets,
        pages=final_pages,
        native_commit=initial_commit,
        lifecycle_commit=lifecycle_commit,
        routes_expected=routes_expected,
        routes_verified=verified,
        replayed=replayed,
    )


def _validate_durable_generation(
    graph: ConcordRecordGraph,
    packets: tuple[PacketInstance, ...],
) -> None:
    review_digests = {item.review_digest for item in packets}
    generation_dates = {item.generation_date for item in packets}
    packet_contracts = {
        (
            item.packet_definition_id,
            item.packet_version_id,
            item.activity_id,
            item.session_id,
        )
        for item in packets
    }
    if None in review_digests or None in generation_dates:
        raise ConcordWorkflowConflictError(
            "durable Packet generation lacks reviewed generation metadata."
        )
    if len(review_digests) != 1 or len(generation_dates) != 1:
        raise ConcordWorkflowConflictError(
            "durable Packet generation has contradictory review metadata."
        )
    if len(packet_contracts) != 1:
        raise ConcordWorkflowConflictError(
            "durable Packet generation has contradictory Packet context."
        )

    artifacts = {
        item.artifact_instance_id: item for item in graph.artifact_instances
    }
    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    bound: set[str] = set()
    for packet in packets:
        for binding in packet.artifact_bindings:
            if binding.artifact_instance_id in bound:
                raise ConcordWorkflowConflictError(
                    "durable generation reuses one Artifact across Packet Instances."
                )
            bound.add(binding.artifact_instance_id)
            artifact = artifacts.get(binding.artifact_instance_id)
            if (
                artifact is None
                or artifact.packet_instance_id != packet.packet_instance_id
                or artifact.template_version_id != binding.template_version_id
                or artifact.activity_id != packet.activity_id
                or artifact.session_id != packet.session_id
            ):
                raise ConcordWorkflowConflictError(
                    "durable Packet/Artifact provenance is contradictory."
                )
            artifact_pages = [pages.get(page_id) for page_id in artifact.page_ids]
            if any(page is None for page in artifact_pages):
                raise ConcordWorkflowConflictError(
                    "durable Packet generation is missing an Artifact Page."
                )
            for page in artifact_pages:
                assert page is not None
                if page.artifact_instance_id != artifact.artifact_instance_id:
                    raise ConcordWorkflowConflictError(
                        "durable Artifact Page ownership is contradictory."
                    )


def _generation_pages(
    graph: ConcordRecordGraph,
    packets: tuple[PacketInstance, ...],
) -> tuple[ArtifactPage, ...]:
    artifact_ids = {
        binding.artifact_instance_id
        for packet in packets
        for binding in packet.artifact_bindings
    }
    page_ids = {
        page_id
        for artifact in graph.artifact_instances
        if artifact.artifact_instance_id in artifact_ids
        for page_id in artifact.page_ids
    }
    return tuple(
        sorted(
            (
                page
                for page in graph.artifact_pages
                if page.artifact_page_id in page_ids
            ),
            key=lambda item: (item.artifact_instance_id, item.page_number),
        )
    )


def _commit_result(
    *,
    work: ModuleWorkRef,
    graph: ConcordRecordGraph,
    packets: tuple[PacketInstance, ...],
    pages: tuple[ArtifactPage, ...],
    native_commit: WorkflowCommitResult,
    lifecycle_commit: WorkflowCommitResult | None,
    routes_expected: int,
    routes_verified: int,
    replayed: bool,
) -> PacketInstantiationCommitResult:
    artifact_ids = tuple(
        binding.artifact_instance_id
        for packet in packets
        for binding in packet.artifact_bindings
    )
    packet_by_artifact = {
        binding.artifact_instance_id: packet.packet_instance_id
        for packet in packets
        for binding in packet.artifact_bindings
    }
    page_values = tuple(
        PacketCommittedPage(
            packet_instance_id=packet_by_artifact[page.artifact_instance_id],
            artifact_instance_id=page.artifact_instance_id,
            artifact_page_id=page.artifact_page_id,
            page_number=page.page_number,
            route_id=page.route_id,
            pds2_payload=(
                serialize_pds2_payload(
                    concord_route_registration(work, page).locator
                )
                if page.route_required
                else None
            ),
        )
        for page in pages
    )
    review_digest = packets[0].review_digest
    assert review_digest is not None
    return PacketInstantiationCommitResult(
        generation_id=packets[0].generation_id,
        review_digest=review_digest,
        native_commit=native_commit,
        lifecycle_commit=lifecycle_commit,
        packet_instance_ids=tuple(item.packet_instance_id for item in packets),
        artifact_instance_ids=artifact_ids,
        pages=page_values,
        routes_expected=routes_expected,
        routes_verified=routes_verified,
        replayed=replayed,
    )


def _target_key(target: PacketTargetContext) -> str:
    if target.audience_kind == "activity":
        return f"activity:{target.activity_id}"
    if target.audience_kind == "teacher":
        if target.actor_reference is None:
            raise ConcordWorkflowConflictError("teacher Packet target is incomplete.")
        return f"teacher:{target.actor_reference.actor_id}"
    if target.audience_kind == "group":
        if target.group_id is None:
            raise ConcordWorkflowConflictError("group Packet target is incomplete.")
        return f"group:{target.group_id}"
    if target.audience_kind == "participant":
        participant = target.participant_reference
        if participant is None:
            raise ConcordWorkflowConflictError(
                "participant Packet target is incomplete."
            )
        return f"participant:{participant.participant_id}"
    if target.role_assignment_id is None:
        raise ConcordWorkflowConflictError("role Packet target is incomplete.")
    return f"role:{target.role_assignment_id}"


__all__ = [
    "PacketCommittedPage",
    "PacketInstantiationCommitResult",
    "PacketInstantiationPartialSuccessError",
    "commit_packet_instantiation",
    "resume_packet_instantiation",
]
