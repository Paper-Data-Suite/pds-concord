"""Teacher-facing application services for reusable Template management."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from concord.models import Provenance, TemplateDefinition, TemplateVersion
from concord.template_authoring import (
    PreparedSourceFile,
    TemplateAuthoringConflictError,
    TemplateAuthoringDocument,
    TemplateAuthoringError,
    load_template_authoring_source,
    prepare_source_file,
    verify_prepared_source,
)
from concord.template_storage import (
    TemplateStorageConflictError,
    TemplateStorageError,
    TemplateStorageNotFoundError,
    TemplateStoragePartialSuccessError,
    activate_template_version,
    create_successor_template_version,
    create_template_library,
    list_template_ids,
    load_current_template,
    retire_template,
    retire_template_version,
    update_template_definition,
)
from concord.template_storage_models import LoadedTemplateLibrary
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
class TemplateSummary:
    template_id: str
    name: str
    status: str
    artifact_category: str
    current_template_version_id: str | None
    head_template_version_id: str
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateDetail:
    summary: TemplateSummary
    definition: TemplateDefinition
    versions: tuple[TemplateVersion, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class TemplateMutationResult:
    template_id: str
    status: str
    snapshot_revision: int
    snapshot_sha256: str
    current_template_version_id: str | None
    head_template_version_id: str
    workspace_created: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareTemplateCreateRequest:
    template_id: str
    template_version_id: str
    authoring_file: Path
    rendering_specification: Path
    actor: WorkflowActor
    activate: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedTemplateCreate:
    definition: TemplateDefinition
    version: TemplateVersion
    authoring_source: PreparedSourceFile
    rendering_source: PreparedSourceFile


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareTemplateRevisionRequest:
    template_id: str
    template_version_id: str
    authoring_file: Path
    rendering_specification: Path
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedTemplateRevision:
    template_id: str
    expected_snapshot_revision: int
    version: TemplateVersion
    authoring_source: PreparedSourceFile
    rendering_source: PreparedSourceFile
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareTemplateActivationRequest:
    template_id: str
    template_version_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedTemplateActivation:
    template_id: str
    template_version_id: str
    expected_snapshot_revision: int
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareTemplateUpdateRequest:
    template_id: str
    name: str
    purpose: str
    description: str | None
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedTemplateUpdate:
    template_id: str
    definition: TemplateDefinition
    expected_snapshot_revision: int
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareTemplateRetireVersionRequest:
    template_id: str
    template_version_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedTemplateRetireVersion:
    template_id: str
    template_version_id: str
    expected_snapshot_revision: int
    operation_provenance: Provenance


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareTemplateRetireRequest:
    template_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedTemplateRetire:
    template_id: str
    expected_snapshot_revision: int
    operation_provenance: Provenance


def list_templates(
    *,
    workspace_root: str | Path | None = None,
) -> tuple[TemplateSummary, ...]:
    """List reusable Templates without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    try:
        return tuple(
            _summary(load_current_template(root, template_id))
            for template_id in list_template_ids(root)
        )
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def get_template(
    template_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateDetail:
    """Load one exact current Template library without writing state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Template is not available: {template_id}"
        )
    loaded = _load(root, template_id)
    return TemplateDetail(
        summary=_summary(loaded),
        definition=loaded.definition,
        versions=loaded.versions,
    )


def prepare_template_create(
    request: PrepareTemplateCreateRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedTemplateCreate:
    """Prepare initial reusable Template state without writing canonical data."""
    if not isinstance(request.activate, bool):
        raise ConcordWorkflowValidationError("activate must be a boolean.")
    document, authoring_source = _authoring(request.authoring_file)
    if document.definition is None:
        raise ConcordWorkflowValidationError(
            "initial Template creation requires authoring definition metadata."
        )
    rendering_source = _source(
        request.rendering_specification,
        "Template rendering specification",
    )
    root = resolve_read_workspace_root(workspace_root)
    if root is not None:
        try:
            load_current_template(root, request.template_id)
        except TemplateStorageNotFoundError:
            pass
        except TemplateStorageError as error:
            raise ConcordWorkflowValidationError(str(error)) from error
        else:
            raise ConcordWorkflowConflictError(
                f"Template identity already exists: {request.template_id}"
            )

    created = provenance(request.actor, clock=clock)
    status = "active" if request.activate else "draft"
    definition = TemplateDefinition(
        template_id=request.template_id,
        name=document.definition.name,
        purpose=document.definition.purpose,
        artifact_category=document.artifact_category,
        status=status,
        created_provenance=created,
        description=document.definition.description,
        owner_reference=created.actor,
    )
    version = _version_from_authoring(
        document,
        template_id=request.template_id,
        template_version_id=request.template_version_id,
        revision_sequence=1,
        predecessor=None,
        status=status,
        created_provenance=created,
        rendering_sha256=rendering_source.sha256,
    )
    return PreparedTemplateCreate(
        definition=definition,
        version=version,
        authoring_source=authoring_source,
        rendering_source=rendering_source,
    )


def commit_template_create(
    prepared: PreparedTemplateCreate,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateMutationResult:
    """Commit one reviewed initial Template after revalidating source files."""
    _verify_source(
        prepared.authoring_source,
        "Template authoring file",
    )
    rendering = _verify_source(
        prepared.rendering_source,
        "Template rendering specification",
    )
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    try:
        loaded = create_template_library(
            bootstrap.root,
            definition=prepared.definition,
            initial_version=prepared.version,
            rendering_specification=rendering,
        )
    except TemplateStoragePartialSuccessError:
        raise
    except TemplateStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded, workspace_created=bootstrap.created)


def prepare_template_revision(
    request: PrepareTemplateRevisionRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedTemplateRevision:
    """Prepare a fresh immutable draft successor from strict authoring input."""
    root = _required_read_root(workspace_root, request.template_id)
    loaded = _load(root, request.template_id)
    _expected(loaded.snapshot_revision, request.expected_snapshot_revision)
    document, authoring_source = _authoring(request.authoring_file)
    if document.definition is not None:
        raise ConcordWorkflowValidationError(
            "successor authoring must omit definition metadata; use Template "
            "update for name, purpose, or description changes."
        )
    if document.artifact_category != loaded.definition.artifact_category:
        raise ConcordWorkflowValidationError(
            "successor authoring artifact_category must match its Template."
        )
    rendering_source = _source(
        request.rendering_specification,
        "Template rendering specification",
    )
    operation_provenance = provenance(request.actor, clock=clock)
    version = _version_from_authoring(
        document,
        template_id=request.template_id,
        template_version_id=request.template_version_id,
        revision_sequence=loaded.head_version.revision_sequence + 1,
        predecessor=loaded.head_template_version_id,
        status="draft",
        created_provenance=operation_provenance,
        rendering_sha256=rendering_source.sha256,
    )
    return PreparedTemplateRevision(
        template_id=request.template_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        version=version,
        authoring_source=authoring_source,
        rendering_source=rendering_source,
        operation_provenance=operation_provenance,
    )


def commit_template_revision(
    prepared: PreparedTemplateRevision,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateMutationResult:
    """Commit one reviewed draft successor against the exact prepared snapshot."""
    _verify_source(
        prepared.authoring_source,
        "Template authoring file",
    )
    rendering = _verify_source(
        prepared.rendering_source,
        "Template rendering specification",
    )
    root = _required_read_root(workspace_root, prepared.template_id)
    try:
        loaded = create_successor_template_version(
            root,
            prepared.template_id,
            successor=prepared.version,
            rendering_specification=rendering,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=_provenance_value(
                prepared.operation_provenance
            ),
        )
    except TemplateStoragePartialSuccessError:
        raise
    except TemplateStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_template_activation(
    request: PrepareTemplateActivationRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedTemplateActivation:
    root = _required_read_root(workspace_root, request.template_id)
    loaded = _load(root, request.template_id)
    _expected(loaded.snapshot_revision, request.expected_snapshot_revision)
    candidate = next(
        (
            item
            for item in loaded.versions
            if item.template_version_id == request.template_version_id
        ),
        None,
    )
    if candidate is None:
        raise ConcordWorkflowNotFoundError(
            f"Template Version is not available: {request.template_version_id}"
        )
    if candidate.template_version_id != loaded.head_template_version_id:
        raise ConcordWorkflowConflictError(
            "only the exact current lineage head can be activated."
        )
    if candidate.status != "draft":
        raise ConcordWorkflowConflictError(
            "Template Version activation requires a draft head."
        )
    return PreparedTemplateActivation(
        template_id=request.template_id,
        template_version_id=request.template_version_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_template_activation(
    prepared: PreparedTemplateActivation,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateMutationResult:
    root = _required_read_root(workspace_root, prepared.template_id)
    try:
        loaded = activate_template_version(
            root,
            prepared.template_id,
            prepared.template_version_id,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=_provenance_value(
                prepared.operation_provenance
            ),
        )
    except TemplateStoragePartialSuccessError:
        raise
    except TemplateStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_template_update(
    request: PrepareTemplateUpdateRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedTemplateUpdate:
    root = _required_read_root(workspace_root, request.template_id)
    loaded = _load(root, request.template_id)
    _expected(loaded.snapshot_revision, request.expected_snapshot_revision)
    definition = replace(
        loaded.definition,
        name=request.name,
        purpose=request.purpose,
        description=request.description,
    )
    return PreparedTemplateUpdate(
        template_id=request.template_id,
        definition=definition,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_template_update(
    prepared: PreparedTemplateUpdate,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateMutationResult:
    root = _required_read_root(workspace_root, prepared.template_id)
    try:
        loaded = update_template_definition(
            root,
            prepared.template_id,
            definition=prepared.definition,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=_provenance_value(
                prepared.operation_provenance
            ),
        )
    except TemplateStoragePartialSuccessError:
        raise
    except TemplateStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_template_retire_version(
    request: PrepareTemplateRetireVersionRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedTemplateRetireVersion:
    root = _required_read_root(workspace_root, request.template_id)
    loaded = _load(root, request.template_id)
    _expected(loaded.snapshot_revision, request.expected_snapshot_revision)
    candidate = next(
        (
            item
            for item in loaded.versions
            if item.template_version_id == request.template_version_id
        ),
        None,
    )
    if candidate is None:
        raise ConcordWorkflowNotFoundError(
            f"Template Version is not available: {request.template_version_id}"
        )
    if candidate.template_version_id == loaded.current_template_version_id:
        raise ConcordWorkflowConflictError(
            "the active current Template Version cannot be retired independently."
        )
    if candidate.status != "draft":
        raise ConcordWorkflowConflictError(
            "only a non-current draft Template Version can be retired."
        )
    return PreparedTemplateRetireVersion(
        template_id=request.template_id,
        template_version_id=request.template_version_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_template_retire_version(
    prepared: PreparedTemplateRetireVersion,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateMutationResult:
    root = _required_read_root(workspace_root, prepared.template_id)
    try:
        loaded = retire_template_version(
            root,
            prepared.template_id,
            prepared.template_version_id,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=_provenance_value(
                prepared.operation_provenance
            ),
        )
    except TemplateStoragePartialSuccessError:
        raise
    except TemplateStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def prepare_template_retire(
    request: PrepareTemplateRetireRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedTemplateRetire:
    root = _required_read_root(workspace_root, request.template_id)
    loaded = _load(root, request.template_id)
    _expected(loaded.snapshot_revision, request.expected_snapshot_revision)
    if loaded.definition.status == "retired":
        raise ConcordWorkflowConflictError("Template is already retired.")
    return PreparedTemplateRetire(
        template_id=request.template_id,
        expected_snapshot_revision=request.expected_snapshot_revision,
        operation_provenance=provenance(request.actor, clock=clock),
    )


def commit_template_retire(
    prepared: PreparedTemplateRetire,
    *,
    workspace_root: str | Path | None = None,
) -> TemplateMutationResult:
    root = _required_read_root(workspace_root, prepared.template_id)
    try:
        loaded = retire_template(
            root,
            prepared.template_id,
            expected_snapshot_revision=prepared.expected_snapshot_revision,
            operation_provenance=_provenance_value(
                prepared.operation_provenance
            ),
        )
    except TemplateStoragePartialSuccessError:
        raise
    except TemplateStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return _mutation_result(loaded)


def _version_from_authoring(
    document: TemplateAuthoringDocument,
    *,
    template_id: str,
    template_version_id: str,
    revision_sequence: int,
    predecessor: str | None,
    status: str,
    created_provenance: Provenance,
    rendering_sha256: str,
) -> TemplateVersion:
    version = document.version
    return TemplateVersion(
        template_version_id=template_version_id,
        template_id=template_id,
        version_label=version.version_label,
        revision_sequence=revision_sequence,
        rendering_contract_version=version.rendering_contract_version,
        rendering_specification_reference=(
            version.rendering_specification_reference
        ),
        rendering_specification_sha256=rendering_sha256,
        artifact_category=document.artifact_category,
        page_manifest=version.page_manifest,
        rendering_inputs=version.rendering_inputs,
        default_expected_return_status=version.default_expected_return_status,
        default_privacy_policy=version.default_privacy_policy,
        compatibility=version.compatibility,
        created_provenance=_provenance_value(created_provenance),
        status=status,
        supersedes_template_version_id=predecessor,
        default_authorship_expectation=(
            version.default_authorship_expectation
        ),
        default_subject_expectation=version.default_subject_expectation,
    )


def _summary(loaded: LoadedTemplateLibrary) -> TemplateSummary:
    return TemplateSummary(
        template_id=loaded.definition.template_id,
        name=loaded.definition.name,
        status=loaded.definition.status,
        artifact_category=loaded.definition.artifact_category,
        current_template_version_id=loaded.current_template_version_id,
        head_template_version_id=loaded.head_template_version_id,
        snapshot_revision=loaded.snapshot_revision,
    )


def _mutation_result(
    loaded: LoadedTemplateLibrary,
    *,
    workspace_created: bool = False,
) -> TemplateMutationResult:
    return TemplateMutationResult(
        template_id=loaded.definition.template_id,
        status=loaded.definition.status,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        current_template_version_id=loaded.current_template_version_id,
        head_template_version_id=loaded.head_template_version_id,
        workspace_created=workspace_created,
    )


def _required_read_root(
    workspace_root: str | Path | None,
    template_id: str,
) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Template is not available: {template_id}"
        )
    return root


def _load(root: Path, template_id: str) -> LoadedTemplateLibrary:
    try:
        return load_current_template(root, template_id)
    except TemplateStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Template is not available: {template_id}"
        ) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _expected(actual: int, expected: int) -> None:
    if type(expected) is not int or expected < 1:
        raise ConcordWorkflowValidationError(
            "expected_snapshot_revision must be a positive integer."
        )
    if actual != expected:
        raise ConcordWorkflowConflictError(
            f"expected Template snapshot {expected}, found {actual}."
        )


def _authoring(
    path: Path,
) -> tuple[TemplateAuthoringDocument, PreparedSourceFile]:
    try:
        return load_template_authoring_source(path)
    except TemplateAuthoringConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateAuthoringError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _source(path: Path, description: str) -> PreparedSourceFile:
    try:
        return prepare_source_file(path, description=description)
    except TemplateAuthoringConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateAuthoringError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _verify_source(
    prepared: PreparedSourceFile,
    description: str,
) -> bytes:
    try:
        return verify_prepared_source(prepared, description=description)
    except TemplateAuthoringConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateAuthoringError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _provenance_value(value: Provenance) -> Provenance:
    if not isinstance(value, Provenance):
        raise ConcordWorkflowValidationError(
            "prepared operation provenance is invalid."
        )
    return value


__all__ = [
    "PrepareTemplateActivationRequest",
    "PrepareTemplateCreateRequest",
    "PrepareTemplateRetireRequest",
    "PrepareTemplateRetireVersionRequest",
    "PrepareTemplateRevisionRequest",
    "PrepareTemplateUpdateRequest",
    "PreparedTemplateActivation",
    "PreparedTemplateCreate",
    "PreparedTemplateRetire",
    "PreparedTemplateRetireVersion",
    "PreparedTemplateRevision",
    "PreparedTemplateUpdate",
    "TemplateDetail",
    "TemplateMutationResult",
    "TemplateSummary",
    "commit_template_activation",
    "commit_template_create",
    "commit_template_retire",
    "commit_template_retire_version",
    "commit_template_revision",
    "commit_template_update",
    "get_template",
    "list_templates",
    "prepare_template_activation",
    "prepare_template_create",
    "prepare_template_retire",
    "prepare_template_retire_version",
    "prepare_template_revision",
    "prepare_template_update",
]
