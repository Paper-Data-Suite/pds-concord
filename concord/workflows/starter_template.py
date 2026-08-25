"""Presentation-neutral installation workflows for packaged starter Templates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from concord.models import TemplateDefinition, TemplateVersion
from concord.starter_templates.catalog import (
    StarterTemplateCatalogEntry,
    StarterTemplateCatalogError,
    StarterTemplateNotFoundError,
    get_starter_template,
    list_starter_templates,
)
from concord.template_storage import (
    TemplateStorageConflictError,
    TemplateStorageError,
    TemplateStorageNotFoundError,
    TemplateStoragePartialSuccessError,
    create_template_library,
    load_current_template,
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
    ConcordWorkflowError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor

STARTER_INSTALLATION_MISSING = "missing"
STARTER_INSTALLATION_ALREADY_INSTALLED = "already_installed"
STARTER_INSTALLATION_CONFLICT = "conflict"
_STARTER_INSTALLATION_STATES = frozenset(
    {
        STARTER_INSTALLATION_MISSING,
        STARTER_INSTALLATION_ALREADY_INSTALLED,
        STARTER_INSTALLATION_CONFLICT,
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateStatus:
    """Read-only packaged-starter status against one workspace."""

    starter_key: str
    family: str
    display_name: str
    template_id: str
    template_version_id: str
    page_count: int
    orientation: str
    installation_state: str

    def __post_init__(self) -> None:
        if self.installation_state not in _STARTER_INSTALLATION_STATES:
            raise ConcordWorkflowValidationError(
                "starter installation state is invalid."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareStarterTemplateInstallRequest:
    starter_key: str
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareStarterTemplateInstallAllRequest:
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedStarterTemplateInstall:
    entry: StarterTemplateCatalogEntry
    initial_state: str
    rendering_sha256: str
    definition: TemplateDefinition | None = None
    version: TemplateVersion | None = None

    def __post_init__(self) -> None:
        if self.initial_state not in {
            STARTER_INSTALLATION_MISSING,
            STARTER_INSTALLATION_ALREADY_INSTALLED,
        }:
            raise ConcordWorkflowValidationError(
                "prepared starter installation state is invalid."
            )
        if self.initial_state == STARTER_INSTALLATION_MISSING:
            if self.definition is None or self.version is None:
                raise ConcordWorkflowValidationError(
                    "missing starter installation requires prepared records."
                )
        elif self.definition is not None or self.version is not None:
            raise ConcordWorkflowValidationError(
                "already-installed starter must not prepare replacement records."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedStarterTemplateInstallAll:
    items: tuple[PreparedStarterTemplateInstall, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateInstallResult:
    starter_key: str
    template_id: str
    template_version_id: str
    outcome: str
    snapshot_revision: int
    snapshot_sha256: str
    workspace_created: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in {
            "installed",
            STARTER_INSTALLATION_ALREADY_INSTALLED,
        }:
            raise ConcordWorkflowValidationError(
                "starter installation outcome is invalid."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateInstallAllResult:
    results: tuple[StarterTemplateInstallResult, ...]

    @property
    def installed_count(self) -> int:
        return sum(item.outcome == "installed" for item in self.results)

    @property
    def already_installed_count(self) -> int:
        return sum(
            item.outcome == STARTER_INSTALLATION_ALREADY_INSTALLED
            for item in self.results
        )


class StarterTemplateInstallAllPartialSuccessError(ConcordWorkflowError):
    """A multi-Template install stopped after earlier starters committed."""

    def __init__(
        self,
        message: str,
        *,
        completed_results: tuple[StarterTemplateInstallResult, ...],
        failed_starter_key: str,
    ) -> None:
        super().__init__(message)
        self.completed_results = completed_results
        self.failed_starter_key = failed_starter_key


def list_starter_template_statuses(
    *,
    workspace_root: str | Path | None = None,
) -> tuple[StarterTemplateStatus, ...]:
    """List all packaged starters without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    return tuple(
        _status(entry, _installation_state(root, entry)[0])
        for entry in list_starter_templates()
    )


def get_starter_template_status(
    starter_key: str,
    *,
    workspace_root: str | Path | None = None,
) -> StarterTemplateStatus:
    """Inspect one packaged starter without creating workspace state."""
    entry = _entry(starter_key)
    root = resolve_read_workspace_root(workspace_root)
    state, _ = _installation_state(root, entry)
    return _status(entry, state)


def prepare_starter_template_install(
    request: PrepareStarterTemplateInstallRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedStarterTemplateInstall:
    """Prepare one explicit starter installation without canonical mutation."""
    if not isinstance(request.actor, WorkflowActor):
        raise ConcordWorkflowValidationError("actor must be WorkflowActor.")
    entry = _entry(request.starter_key)
    root = resolve_read_workspace_root(workspace_root)
    state, _ = _installation_state(root, entry)
    if state == STARTER_INSTALLATION_CONFLICT:
        raise ConcordWorkflowConflictError(
            "starter Template identity exists with incompatible content: "
            f"{entry.template_id}"
        )
    return _prepare_entry(entry, state, request.actor, clock=clock)


def commit_starter_template_install(
    prepared: PreparedStarterTemplateInstall,
    *,
    workspace_root: str | Path | None = None,
) -> StarterTemplateInstallResult:
    """Install one reviewed packaged starter through #58 canonical storage."""
    entry, rendering = _revalidate_prepared(prepared)
    root = resolve_read_workspace_root(workspace_root)
    state, loaded = _installation_state(root, entry)
    if state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        assert loaded is not None
        return _result(entry, loaded, outcome=state)
    if state == STARTER_INSTALLATION_CONFLICT:
        raise ConcordWorkflowConflictError(
            "starter Template identity became incompatible before commit: "
            f"{entry.template_id}"
        )
    if prepared.initial_state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        raise ConcordWorkflowConflictError(
            "starter Template disappeared after preparation: "
            f"{entry.template_id}"
        )
    if prepared.definition is None or prepared.version is None:
        raise ConcordWorkflowValidationError(
            "prepared starter installation records are missing."
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
        state, raced = _installation_state(bootstrap.root, entry)
        if (
            state == STARTER_INSTALLATION_ALREADY_INSTALLED
            and raced is not None
        ):
            return _result(entry, raced, outcome=state)
        raise ConcordWorkflowConflictError(str(error)) from error
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    if not _matches_starter(loaded, entry):
        raise ConcordWorkflowValidationError(
            "installed starter failed exact post-commit verification."
        )
    return _result(
        entry,
        loaded,
        outcome="installed",
        workspace_created=bootstrap.created,
    )


def prepare_starter_template_install_all(
    request: PrepareStarterTemplateInstallAllRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedStarterTemplateInstallAll:
    """Preflight all packaged starters and prepare every missing lineage."""
    if not isinstance(request.actor, WorkflowActor):
        raise ConcordWorkflowValidationError("actor must be WorkflowActor.")
    root = resolve_read_workspace_root(workspace_root)
    inspected = tuple(
        (entry, _installation_state(root, entry)[0])
        for entry in list_starter_templates()
    )
    conflicts = tuple(
        entry.starter_key
        for entry, state in inspected
        if state == STARTER_INSTALLATION_CONFLICT
    )
    if conflicts:
        raise ConcordWorkflowConflictError(
            "starter install-all found incompatible Template identities: "
            + ", ".join(conflicts)
        )

    created = None
    if any(state == STARTER_INSTALLATION_MISSING for _, state in inspected):
        created = provenance(
            request.actor,
            clock=clock,
            source_kind="imported",
        )
    items: list[PreparedStarterTemplateInstall] = []
    for entry, state in inspected:
        if state == STARTER_INSTALLATION_MISSING:
            assert created is not None
            definition, version = entry.build_template_records(
                created_provenance=created,
                status="active",
            )
            items.append(
                PreparedStarterTemplateInstall(
                    entry=entry,
                    initial_state=state,
                    rendering_sha256=entry.rendering_sha256(),
                    definition=definition,
                    version=version,
                )
            )
        else:
            items.append(
                PreparedStarterTemplateInstall(
                    entry=entry,
                    initial_state=state,
                    rendering_sha256=entry.rendering_sha256(),
                )
            )
    return PreparedStarterTemplateInstallAll(items=tuple(items))


def commit_starter_template_install_all(
    prepared: PreparedStarterTemplateInstallAll,
    *,
    workspace_root: str | Path | None = None,
) -> StarterTemplateInstallAllResult:
    """Commit starters in deterministic catalog order with idempotent replay."""
    results: list[StarterTemplateInstallResult] = []
    for item in prepared.items:
        try:
            result = commit_starter_template_install(
                item,
                workspace_root=workspace_root,
            )
        except (
            ConcordWorkflowError,
            TemplateStoragePartialSuccessError,
        ) as error:
            if not results:
                raise
            raise StarterTemplateInstallAllPartialSuccessError(
                "starter install-all stopped after earlier Template commits; "
                "rerun safely to reconcile exact installed starters.",
                completed_results=tuple(results),
                failed_starter_key=item.entry.starter_key,
            ) from error
        results.append(result)
    return StarterTemplateInstallAllResult(results=tuple(results))


def _prepare_entry(
    entry: StarterTemplateCatalogEntry,
    state: str,
    actor: WorkflowActor,
    *,
    clock: Clock | None,
) -> PreparedStarterTemplateInstall:
    digest = entry.rendering_sha256()
    if state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        return PreparedStarterTemplateInstall(
            entry=entry,
            initial_state=state,
            rendering_sha256=digest,
        )
    created = provenance(actor, clock=clock, source_kind="imported")
    definition, version = entry.build_template_records(
        created_provenance=created,
        status="active",
    )
    return PreparedStarterTemplateInstall(
        entry=entry,
        initial_state=state,
        rendering_sha256=digest,
        definition=definition,
        version=version,
    )


def _entry(starter_key: str) -> StarterTemplateCatalogEntry:
    try:
        return get_starter_template(starter_key)
    except StarterTemplateNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except StarterTemplateCatalogError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _status(
    entry: StarterTemplateCatalogEntry,
    state: str,
) -> StarterTemplateStatus:
    return StarterTemplateStatus(
        starter_key=entry.starter_key,
        family=entry.family,
        display_name=entry.display_name,
        template_id=entry.template_id,
        template_version_id=entry.template_version_id,
        page_count=entry.page_count,
        orientation=entry.orientation,
        installation_state=state,
    )


def _installation_state(
    root: Path | None,
    entry: StarterTemplateCatalogEntry,
) -> tuple[str, LoadedTemplateLibrary | None]:
    if root is None:
        return STARTER_INSTALLATION_MISSING, None
    try:
        loaded = load_current_template(root, entry.template_id)
    except TemplateStorageNotFoundError:
        return STARTER_INSTALLATION_MISSING, None
    except TemplateStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if _matches_starter(loaded, entry):
        return STARTER_INSTALLATION_ALREADY_INSTALLED, loaded
    return STARTER_INSTALLATION_CONFLICT, loaded


def _matches_starter(
    loaded: LoadedTemplateLibrary,
    entry: StarterTemplateCatalogEntry,
) -> bool:
    if loaded.definition.artifact_category != entry.artifact_category:
        return False
    candidate = next(
        (
            version
            for version in loaded.versions
            if version.template_version_id == entry.template_version_id
        ),
        None,
    )
    if candidate is None:
        return False
    try:
        _, expected = entry.build_template_records(
            created_provenance=candidate.created_provenance,
            status="active",
        )
    except StarterTemplateCatalogError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return replace(candidate, status="active") == expected


def _revalidate_prepared(
    prepared: PreparedStarterTemplateInstall,
) -> tuple[StarterTemplateCatalogEntry, bytes]:
    current = _entry(prepared.entry.starter_key)
    if current != prepared.entry:
        raise ConcordWorkflowConflictError(
            "packaged starter metadata changed after preparation."
        )
    try:
        rendering = current.rendering_specification_bytes()
        digest = current.rendering_sha256()
    except StarterTemplateCatalogError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if digest != prepared.rendering_sha256:
        raise ConcordWorkflowConflictError(
            "packaged starter rendering bytes changed after preparation."
        )
    if prepared.definition is not None and prepared.version is not None:
        expected_definition, expected_version = current.build_template_records(
            created_provenance=prepared.definition.created_provenance,
            status="active",
        )
        if (
            expected_definition != prepared.definition
            or expected_version != prepared.version
        ):
            raise ConcordWorkflowConflictError(
                "packaged starter Template semantics changed after preparation."
            )
    return current, rendering


def _result(
    entry: StarterTemplateCatalogEntry,
    loaded: LoadedTemplateLibrary,
    *,
    outcome: str,
    workspace_created: bool = False,
) -> StarterTemplateInstallResult:
    return StarterTemplateInstallResult(
        starter_key=entry.starter_key,
        template_id=entry.template_id,
        template_version_id=entry.template_version_id,
        outcome=outcome,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        workspace_created=workspace_created,
    )


__all__ = [
    "STARTER_INSTALLATION_ALREADY_INSTALLED",
    "STARTER_INSTALLATION_CONFLICT",
    "STARTER_INSTALLATION_MISSING",
    "PrepareStarterTemplateInstallAllRequest",
    "PrepareStarterTemplateInstallRequest",
    "PreparedStarterTemplateInstall",
    "PreparedStarterTemplateInstallAll",
    "StarterTemplateInstallAllPartialSuccessError",
    "StarterTemplateInstallAllResult",
    "StarterTemplateInstallResult",
    "StarterTemplateStatus",
    "commit_starter_template_install",
    "commit_starter_template_install_all",
    "get_starter_template_status",
    "list_starter_template_statuses",
    "prepare_starter_template_install",
    "prepare_starter_template_install_all",
]
