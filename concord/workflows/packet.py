"""Teacher-facing application services for reusable Packet management."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from concord.models import PacketDefinition, PacketVersion, Provenance
from concord.packet_authoring import (
    PacketAuthoringConflictError,
    PacketAuthoringDocument,
    PacketAuthoringError,
    PreparedPacketSourceFile,
    load_packet_authoring_source,
    verify_prepared_packet_source,
)
from concord.packet_storage import (
    PacketStorageConflictError,
    PacketStorageDependencyError,
    PacketStorageError,
    PacketStorageNotFoundError,
    PacketStoragePartialSuccessError,
    activate_packet_version,
    create_packet_library,
    create_successor_packet_version,
    list_packet_ids,
    load_current_packet,
    retire_packet,
    retire_packet_version,
    update_packet_definition,
    validate_packet_template_dependencies,
)
from concord.packet_storage_models import LoadedPacketLibrary
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    provenance,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketSummary:
    packet_definition_id: str
    name: str
    status: str
    current_packet_version_id: str | None
    head_packet_version_id: str
    snapshot_revision: int
    component_count: int


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketDetail:
    summary: PacketSummary
    definition: PacketDefinition
    versions: tuple[PacketVersion, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketMutationResult:
    packet_definition_id: str
    status: str
    snapshot_revision: int
    snapshot_sha256: str
    current_packet_version_id: str | None
    head_packet_version_id: str
    workspace_created: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketCreateRequest:
    packet_definition_id: str
    packet_version_id: str
    authoring_file: Path
    actor: WorkflowActor
    activate: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketCreate:
    definition: PacketDefinition
    version: PacketVersion
    authoring_source: PreparedPacketSourceFile


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketRevisionRequest:
    packet_definition_id: str
    packet_version_id: str
    authoring_file: Path
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketRevision:
    packet_definition_id: str
    expected_snapshot_revision: int
    version: PacketVersion
    authoring_source: PreparedPacketSourceFile
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketActivationRequest:
    packet_definition_id: str
    packet_version_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketActivation:
    packet_definition_id: str
    packet_version_id: str
    expected_snapshot_revision: int
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketUpdateRequest:
    packet_definition_id: str
    name: str
    purpose: str
    description: str | None
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketUpdate:
    packet_definition_id: str
    definition: PacketDefinition
    expected_snapshot_revision: int
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketRetireVersionRequest:
    packet_definition_id: str
    packet_version_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketRetireVersion:
    packet_definition_id: str
    packet_version_id: str
    expected_snapshot_revision: int
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketRetireRequest:
    packet_definition_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketRetire:
    packet_definition_id: str
    expected_snapshot_revision: int
    operation_provenance: Provenance


def list_packets(
    *,
    workspace_root: str | Path | None = None,
) -> tuple[PacketSummary, ...]:
    """List reusable Packets without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    try:
        return tuple(
            _summary(load_current_packet(root, packet_id))
            for packet_id in list_packet_ids(root)
        )
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def get_packet(
    packet_definition_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> PacketDetail:
    """Load one exact current Packet library without writing state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet is not available: {packet_definition_id}"
        )
    loaded = _load(root, packet_definition_id)
    return PacketDetail(
        summary=_summary(loaded),
        definition=loaded.definition,
        versions=loaded.versions,
    )


def prepare_packet_create(
    request: PreparePacketCreateRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedPacketCreate:
    """Prepare initial reusable Packet state without canonical mutation."""
    if not isinstance(request.activate, bool):
        raise ConcordWorkflowValidationError("activate must be a boolean.")
    document, authoring_source = _authoring(request.authoring_file)
    if document.definition is None:
        raise ConcordWorkflowValidationError(
            "initial Packet creation requires authoring definition metadata."
        )
    root = resolve_read_workspace_root(workspace_root)
    if root is not None:
        try:
            load_current_packet(root, request.packet_definition_id)
        except PacketStorageNotFoundError:
            pass
        except PacketStorageError as error:
            raise ConcordWorkflowValidationError(str(error)) from error
        else:
            raise ConcordWorkflowConflictError(
                "Packet identity already exists: "
                f"{request.packet_definition_id}"
            )

    created = provenance(request.actor, clock=clock)
    status = "active" if request.activate else "draft"
    definition = PacketDefinition(
        packet_definition_id=request.packet_definition_id,
        name=document.definition.name,
        purpose=document.definition.purpose,
        status=status,
        created_provenance=created,
        description=document.definition.description,
    )
    version = _version_from_authoring(
        document,
        packet_definition_id=request.packet_definition_id,
        packet_version_id=request.packet_version_id,
        revision_sequence=1,
        predecessor=None,
        status=status,
        created_provenance=created,
    )
    if root is None and _uses_templates(version):
        raise ConcordWorkflowValidationError(
            "Template-backed Packet authoring requires an existing workspace "
            "containing the exact reusable Template dependencies."
        )
    if root is not None:
        _validate_dependencies(
            root,
            version,
            for_activation=request.activate,
        )
    return PreparedPacketCreate(
        definition=definition,
        version=version,
        authoring_source=authoring_source,
    )


def commit_packet_create(
    prepared: PreparedPacketCreate,
    *,
    workspace_root: str | Path | None = None,
) -> PacketMutationResult:
    """Commit one reviewed initial Packet after revalidating authoring input."""
    _verify_source(prepared.authoring_source)
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    try:
        loaded = create_packet_library(
            bootstrap.root,
            definition=prepared.definition,
            initial_version=prepared.version,
        )
    except PacketStoragePartialSuccessError:
        raise
    except PacketStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded, workspace_created=bootstrap.created)


def prepare_packet_revision(
    request: PreparePacketRevisionRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedPacketRevision:
    """Prepare one fresh immutable draft Packet successor."""
    root = _required_read_root(
        workspace_root,
        request.packet_definition_id,
    )
    loaded = _load(root, request.packet_definition_id)
    _expected(
        loaded.snapshot_revision,
        request.expected_snapshot_revision,
    )
    document, authoring_source = _authoring(request.authoring_file)
    if document.definition is not None:
        raise ConcordWorkflowValidationError(
            "successor authoring must omit definition metadata; use Packet "
            "update for name, purpose, or description changes."
        )
    operation_provenance = provenance(request.actor, clock=clock)
    version = _version_from_authoring(
        document,
        packet_definition_id=request.packet_definition_id,
        packet_version_id=request.packet_version_id,
        revision_sequence=loaded.head_version.revision_sequence + 1,
        predecessor=loaded.head_packet_version_id,
        status="draft",
        created_provenance=operation_provenance,
    )
    _validate_dependencies(root, version, for_activation=False)
    return PreparedPacketRevision(
        packet_definition_id=request.packet_definition_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        version=version,
        authoring_source=authoring_source,
        operation_provenance=operation_provenance,
    )


def commit_packet_revision(
    prepared: PreparedPacketRevision,
    *,
    workspace_root: str | Path | None = None,
) -> PacketMutationResult:
    """Commit one reviewed draft successor against exact prepared state."""
    _verify_source(prepared.authoring_source)
    root = _required_read_root(
        workspace_root,
        prepared.packet_definition_id,
    )
    try:
        loaded = create_successor_packet_version(
            root,
            prepared.packet_definition_id,
            successor=prepared.version,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=prepared.operation_provenance,
        )
    except PacketStoragePartialSuccessError:
        raise
    except PacketStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_packet_activation(
    request: PreparePacketActivationRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedPacketActivation:
    root = _required_read_root(
        workspace_root,
        request.packet_definition_id,
    )
    loaded = _load(root, request.packet_definition_id)
    _expected(
        loaded.snapshot_revision,
        request.expected_snapshot_revision,
    )
    candidate = next(
        (
            item
            for item in loaded.versions
            if item.packet_version_id == request.packet_version_id
        ),
        None,
    )
    if candidate is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet Version is not available: {request.packet_version_id}"
        )
    if candidate.packet_version_id != loaded.head_packet_version_id:
        raise ConcordWorkflowConflictError(
            "only the exact current lineage head can be activated."
        )
    if candidate.status != "draft":
        raise ConcordWorkflowConflictError(
            "Packet Version activation requires a draft head."
        )
    _validate_dependencies(root, candidate, for_activation=True)
    return PreparedPacketActivation(
        packet_definition_id=request.packet_definition_id,
        packet_version_id=request.packet_version_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_packet_activation(
    prepared: PreparedPacketActivation,
    *,
    workspace_root: str | Path | None = None,
) -> PacketMutationResult:
    root = _required_read_root(
        workspace_root,
        prepared.packet_definition_id,
    )
    try:
        loaded = activate_packet_version(
            root,
            prepared.packet_definition_id,
            prepared.packet_version_id,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=prepared.operation_provenance,
        )
    except PacketStoragePartialSuccessError:
        raise
    except PacketStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_packet_update(
    request: PreparePacketUpdateRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedPacketUpdate:
    root = _required_read_root(
        workspace_root,
        request.packet_definition_id,
    )
    loaded = _load(root, request.packet_definition_id)
    _expected(
        loaded.snapshot_revision,
        request.expected_snapshot_revision,
    )
    definition = replace(
        loaded.definition,
        name=request.name,
        purpose=request.purpose,
        description=request.description,
    )
    return PreparedPacketUpdate(
        packet_definition_id=request.packet_definition_id,
        definition=definition,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_packet_update(
    prepared: PreparedPacketUpdate,
    *,
    workspace_root: str | Path | None = None,
) -> PacketMutationResult:
    root = _required_read_root(
        workspace_root,
        prepared.packet_definition_id,
    )
    try:
        loaded = update_packet_definition(
            root,
            prepared.packet_definition_id,
            definition=prepared.definition,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=prepared.operation_provenance,
        )
    except PacketStoragePartialSuccessError:
        raise
    except PacketStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_packet_retire_version(
    request: PreparePacketRetireVersionRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedPacketRetireVersion:
    root = _required_read_root(
        workspace_root,
        request.packet_definition_id,
    )
    loaded = _load(root, request.packet_definition_id)
    _expected(
        loaded.snapshot_revision,
        request.expected_snapshot_revision,
    )
    candidate = next(
        (
            item
            for item in loaded.versions
            if item.packet_version_id == request.packet_version_id
        ),
        None,
    )
    if candidate is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet Version is not available: {request.packet_version_id}"
        )
    if candidate.packet_version_id == loaded.current_packet_version_id:
        raise ConcordWorkflowConflictError(
            "the active current Packet Version cannot be retired independently."
        )
    if candidate.status != "draft":
        raise ConcordWorkflowConflictError(
            "only a non-current draft Packet Version can be retired."
        )
    return PreparedPacketRetireVersion(
        packet_definition_id=request.packet_definition_id,
        packet_version_id=request.packet_version_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_packet_retire_version(
    prepared: PreparedPacketRetireVersion,
    *,
    workspace_root: str | Path | None = None,
) -> PacketMutationResult:
    root = _required_read_root(
        workspace_root,
        prepared.packet_definition_id,
    )
    try:
        loaded = retire_packet_version(
            root,
            prepared.packet_definition_id,
            prepared.packet_version_id,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=prepared.operation_provenance,
        )
    except PacketStoragePartialSuccessError:
        raise
    except PacketStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_packet_retire(
    request: PreparePacketRetireRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedPacketRetire:
    root = _required_read_root(
        workspace_root,
        request.packet_definition_id,
    )
    loaded = _load(root, request.packet_definition_id)
    _expected(
        loaded.snapshot_revision,
        request.expected_snapshot_revision,
    )
    if loaded.definition.status == "retired":
        raise ConcordWorkflowConflictError("Packet is already retired.")
    return PreparedPacketRetire(
        packet_definition_id=request.packet_definition_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_packet_retire(
    prepared: PreparedPacketRetire,
    *,
    workspace_root: str | Path | None = None,
) -> PacketMutationResult:
    root = _required_read_root(
        workspace_root,
        prepared.packet_definition_id,
    )
    try:
        loaded = retire_packet(
            root,
            prepared.packet_definition_id,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=prepared.operation_provenance,
        )
    except PacketStoragePartialSuccessError:
        raise
    except PacketStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def _version_from_authoring(
    document: PacketAuthoringDocument,
    *,
    packet_definition_id: str,
    packet_version_id: str,
    revision_sequence: int,
    predecessor: str | None,
    status: str,
    created_provenance: Provenance,
) -> PacketVersion:
    return PacketVersion(
        packet_version_id=packet_version_id,
        packet_definition_id=packet_definition_id,
        version_label=document.version.version_label,
        revision_sequence=revision_sequence,
        components=document.version.components,
        rendering_rules=document.version.rendering_rules,
        created_provenance=created_provenance,
        status=status,
        supersedes_packet_version_id=predecessor,
    )


def _summary(loaded: LoadedPacketLibrary) -> PacketSummary:
    return PacketSummary(
        packet_definition_id=loaded.definition.packet_definition_id,
        name=loaded.definition.name,
        status=loaded.definition.status,
        current_packet_version_id=loaded.current_packet_version_id,
        head_packet_version_id=loaded.head_packet_version_id,
        snapshot_revision=loaded.snapshot_revision,
        component_count=len(loaded.head_version.components),
    )


def _mutation_result(
    loaded: LoadedPacketLibrary,
    *,
    workspace_created: bool = False,
) -> PacketMutationResult:
    return PacketMutationResult(
        packet_definition_id=loaded.definition.packet_definition_id,
        status=loaded.definition.status,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        current_packet_version_id=loaded.current_packet_version_id,
        head_packet_version_id=loaded.head_packet_version_id,
        workspace_created=workspace_created,
    )


def _load(root: Path, packet_definition_id: str) -> LoadedPacketLibrary:
    try:
        return load_current_packet(root, packet_definition_id)
    except PacketStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _required_read_root(
    workspace_root: str | Path | None,
    packet_definition_id: str,
) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet is not available: {packet_definition_id}"
        )
    return root


def _expected(actual: int, expected: int) -> None:
    if type(expected) is not int or expected < 1:
        raise ConcordWorkflowValidationError(
            "expected_snapshot_revision must be a positive integer."
        )
    if actual != expected:
        raise ConcordWorkflowConflictError(
            f"expected Packet snapshot {expected}, found {actual}."
        )


def _authoring(
    path: Path,
) -> tuple[PacketAuthoringDocument, PreparedPacketSourceFile]:
    try:
        return load_packet_authoring_source(path)
    except PacketAuthoringConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketAuthoringError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _verify_source(prepared: PreparedPacketSourceFile) -> None:
    try:
        verify_prepared_packet_source(
            prepared,
            description="Packet authoring file",
        )
    except PacketAuthoringConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except PacketAuthoringError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _validate_dependencies(
    root: Path,
    version: PacketVersion,
    *,
    for_activation: bool,
) -> None:
    try:
        validate_packet_template_dependencies(
            root,
            version,
            for_activation=for_activation,
        )
    except PacketStorageDependencyError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    except PacketStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _uses_templates(version: PacketVersion) -> bool:
    return any(
        item.component_kind == "concord_template"
        for item in version.components
    )


__all__ = [
    "PacketDetail",
    "PacketMutationResult",
    "PacketSummary",
    "PreparePacketActivationRequest",
    "PreparePacketCreateRequest",
    "PreparePacketRetireRequest",
    "PreparePacketRetireVersionRequest",
    "PreparePacketRevisionRequest",
    "PreparePacketUpdateRequest",
    "PreparedPacketActivation",
    "PreparedPacketCreate",
    "PreparedPacketRetire",
    "PreparedPacketRetireVersion",
    "PreparedPacketRevision",
    "PreparedPacketUpdate",
    "commit_packet_activation",
    "commit_packet_create",
    "commit_packet_retire",
    "commit_packet_retire_version",
    "commit_packet_revision",
    "commit_packet_update",
    "get_packet",
    "list_packets",
    "prepare_packet_activation",
    "prepare_packet_create",
    "prepare_packet_retire",
    "prepare_packet_retire_version",
    "prepare_packet_revision",
    "prepare_packet_update",
]
