"""Presentation-neutral reconciliation workflows for packaged starter Templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from concord.models import Provenance, TemplateDefinition, TemplateVersion
from concord.starter_templates.catalog import (
    StarterTemplateCatalogEntry,
    StarterTemplateCatalogError,
    StarterTemplateNotFoundError,
    get_starter_template,
    list_starter_templates,
)
from concord.starter_templates.catalog_lineage import (
    build_starter_template_lineage,
    current_packaged_template_version_id,
)
from concord.starter_templates.lineage import (
    STARTER_LINEAGE_CONFLICT,
    STARTER_LINEAGE_CURRENT,
    STARTER_LINEAGE_MISSING,
    STARTER_LINEAGE_UPGRADE_AVAILABLE,
    PackagedStarterTemplateLineage,
    PreparedStarterTemplateLineageReconciliation,
    StarterTemplateLineageConflictError,
    StarterTemplateLineageValidationError,
    commit_packaged_starter_lineage_reconciliation,
    inspect_packaged_starter_lineage,
    prepare_packaged_starter_lineage_reconciliation,
)
from concord.template_storage import (
    TemplateStorageError,
    TemplateStorageNotFoundError,
    TemplateStoragePartialSuccessError,
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
STARTER_INSTALLATION_UPGRADE_AVAILABLE = "upgrade_available"
STARTER_INSTALLATION_CONFLICT = "conflict"
_STARTER_INSTALLATION_STATES = frozenset(
    {
        STARTER_INSTALLATION_MISSING,
        STARTER_INSTALLATION_ALREADY_INSTALLED,
        STARTER_INSTALLATION_UPGRADE_AVAILABLE,
        STARTER_INSTALLATION_CONFLICT,
    }
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateStatus:
    """Read-only package reconciliation status against one workspace."""

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
    lineage: PackagedStarterTemplateLineage | None = None
    lineage_reconciliation: (
        PreparedStarterTemplateLineageReconciliation | None
    ) = None

    def __post_init__(self) -> None:
        if self.initial_state not in {
            STARTER_INSTALLATION_MISSING,
            STARTER_INSTALLATION_ALREADY_INSTALLED,
            STARTER_INSTALLATION_UPGRADE_AVAILABLE,
        }:
            raise ConcordWorkflowValidationError(
                "prepared starter installation state is invalid."
            )
        if self.initial_state == STARTER_INSTALLATION_MISSING:
            if (
                self.definition is None
                or self.version is None
                or self.lineage is None
                or self.lineage_reconciliation is None
            ):
                raise ConcordWorkflowValidationError(
                    "missing starter installation requires prepared lineage records."
                )
        elif self.initial_state == STARTER_INSTALLATION_UPGRADE_AVAILABLE:
            if (
                self.definition is not None
                or self.version is not None
                or self.lineage is None
                or self.lineage_reconciliation is None
            ):
                raise ConcordWorkflowValidationError(
                    "starter upgrade requires a prepared lineage only."
                )
        elif (
            self.definition is not None
            or self.version is not None
            or self.lineage is not None
            or self.lineage_reconciliation is not None
        ):
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
            "upgraded",
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
    def upgraded_count(self) -> int:
        return sum(item.outcome == "upgraded" for item in self.results)

    @property
    def already_installed_count(self) -> int:
        return sum(
            item.outcome == STARTER_INSTALLATION_ALREADY_INSTALLED
            for item in self.results
        )


class StarterTemplateInstallAllPartialSuccessError(ConcordWorkflowError):
    """A multi-Template reconciliation stopped after earlier commits."""

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
    """Prepare one explicit package reconciliation without canonical mutation."""
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
    return _prepare_entry(
        entry,
        state,
        request.actor,
        root=root,
        clock=clock,
    )


def commit_starter_template_install(
    prepared: PreparedStarterTemplateInstall,
    *,
    workspace_root: str | Path | None = None,
) -> StarterTemplateInstallResult:
    """Reconcile one reviewed packaged starter through canonical Template storage."""
    entry = _revalidate_prepared(prepared)
    root = resolve_read_workspace_root(workspace_root)
    state, loaded = _installation_state(root, entry)

    if prepared.initial_state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        if state == STARTER_INSTALLATION_ALREADY_INSTALLED and loaded is not None:
            return _result(
                entry,
                loaded,
                outcome=STARTER_INSTALLATION_ALREADY_INSTALLED,
            )
        raise ConcordWorkflowConflictError(
            "starter Template changed after already-installed preparation: "
            f"{entry.template_id}"
        )

    if state == STARTER_INSTALLATION_CONFLICT:
        raise ConcordWorkflowConflictError(
            "starter Template identity became incompatible before commit: "
            f"{entry.template_id}"
        )

    if prepared.lineage_reconciliation is None or prepared.lineage is None:
        raise ConcordWorkflowValidationError(
            "prepared starter lineage reconciliation is missing."
        )

    bootstrap = ensure_mutating_workspace_root(workspace_root)
    try:
        reconciled = commit_packaged_starter_lineage_reconciliation(
            prepared.lineage_reconciliation,
            workspace_root=bootstrap.root,
        )
    except TemplateStoragePartialSuccessError:
        raise
    except StarterTemplateLineageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except StarterTemplateLineageValidationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    outcome = {
        "installed": "installed",
        "upgraded": "upgraded",
        "already_current": STARTER_INSTALLATION_ALREADY_INSTALLED,
    }[reconciled.outcome]
    verified_state, verified_loaded = _installation_state(
        bootstrap.root,
        entry,
    )
    if (
        verified_state != STARTER_INSTALLATION_ALREADY_INSTALLED
        or verified_loaded is None
    ):
        raise ConcordWorkflowValidationError(
            "starter reconciliation failed exact post-commit verification."
        )
    return _result(
        entry,
        verified_loaded,
        outcome=outcome,
        workspace_created=bootstrap.created,
    )


def prepare_starter_template_install_all(
    request: PrepareStarterTemplateInstallAllRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PreparedStarterTemplateInstallAll:
    """Preflight and prepare every missing or package-upgradable starter."""
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

    writes_required = any(
        state
        in {
            STARTER_INSTALLATION_MISSING,
            STARTER_INSTALLATION_UPGRADE_AVAILABLE,
        }
        for _, state in inspected
    )
    created = (
        provenance(
            request.actor,
            clock=clock,
            source_kind="imported",
        )
        if writes_required
        else None
    )

    items: list[PreparedStarterTemplateInstall] = []
    for entry, state in inspected:
        items.append(
            _prepare_entry(
                entry,
                state,
                request.actor,
                root=root,
                clock=clock,
                created_provenance=created,
            )
        )
    return PreparedStarterTemplateInstallAll(items=tuple(items))


def commit_starter_template_install_all(
    prepared: PreparedStarterTemplateInstallAll,
    *,
    workspace_root: str | Path | None = None,
) -> StarterTemplateInstallAllResult:
    """Commit reconciliations in deterministic catalog order with safe replay."""
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
                "rerun safely to reconcile exact packaged lineages.",
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
    root: Path | None,
    clock: Clock | None,
    created_provenance: Provenance | None = None,
) -> PreparedStarterTemplateInstall:
    if state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        return PreparedStarterTemplateInstall(
            entry=entry,
            initial_state=state,
            rendering_sha256=entry.rendering_sha256(),
        )
    if state == STARTER_INSTALLATION_CONFLICT:
        raise ConcordWorkflowConflictError(
            "starter Template identity exists with incompatible content: "
            f"{entry.template_id}"
        )

    created = (
        created_provenance
        if created_provenance is not None
        else provenance(actor, clock=clock, source_kind="imported")
    )
    lineage = _build_lineage(entry, created)
    head_digest = lineage.current_version.version.rendering_specification_sha256

    if root is None:
        reconciliation = PreparedStarterTemplateLineageReconciliation(
            lineage=lineage,
            initial_state=STARTER_LINEAGE_MISSING,
            expected_snapshot_revision=None,
            expected_snapshot_sha256=None,
        )
    else:
        try:
            reconciliation = prepare_packaged_starter_lineage_reconciliation(
                root,
                lineage,
            )
        except StarterTemplateLineageConflictError as error:
            raise ConcordWorkflowConflictError(str(error)) from error
        except StarterTemplateLineageValidationError as error:
            raise ConcordWorkflowValidationError(str(error)) from error

    if state == STARTER_INSTALLATION_MISSING:
        initial = lineage.versions[0].version
        return PreparedStarterTemplateInstall(
            entry=entry,
            initial_state=state,
            rendering_sha256=head_digest,
            definition=lineage.definition,
            version=initial,
            lineage=lineage,
            lineage_reconciliation=reconciliation,
        )

    if state != STARTER_INSTALLATION_UPGRADE_AVAILABLE:
        raise ConcordWorkflowValidationError(
            "unsupported starter preparation state."
        )
    return PreparedStarterTemplateInstall(
        entry=entry,
        initial_state=state,
        rendering_sha256=head_digest,
        lineage=lineage,
        lineage_reconciliation=reconciliation,
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
        template_version_id=current_packaged_template_version_id(entry),
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

    try:
        lineage = _build_lineage(
            entry,
            loaded.versions[0].created_provenance,
        )
        inspection = inspect_packaged_starter_lineage(root, lineage)
    except StarterTemplateLineageValidationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    state = {
        STARTER_LINEAGE_MISSING: STARTER_INSTALLATION_MISSING,
        STARTER_LINEAGE_CURRENT: STARTER_INSTALLATION_ALREADY_INSTALLED,
        STARTER_LINEAGE_UPGRADE_AVAILABLE: (
            STARTER_INSTALLATION_UPGRADE_AVAILABLE
        ),
        STARTER_LINEAGE_CONFLICT: STARTER_INSTALLATION_CONFLICT,
    }[inspection.state]
    return state, inspection.loaded


def _build_lineage(
    entry: StarterTemplateCatalogEntry,
    created_provenance: Provenance,
) -> PackagedStarterTemplateLineage:
    try:
        return build_starter_template_lineage(
            entry,
            created_provenance=created_provenance,
        )
    except StarterTemplateCatalogError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    except StarterTemplateLineageValidationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _revalidate_prepared(
    prepared: PreparedStarterTemplateInstall,
) -> StarterTemplateCatalogEntry:
    current = _entry(prepared.entry.starter_key)
    if current != prepared.entry:
        raise ConcordWorkflowConflictError(
            "packaged starter metadata changed after preparation."
        )

    if prepared.initial_state == STARTER_INSTALLATION_ALREADY_INSTALLED:
        if current.rendering_sha256() != prepared.rendering_sha256:
            raise ConcordWorkflowConflictError(
                "packaged starter rendering bytes changed after preparation."
            )
        return current

    if prepared.lineage is None:
        raise ConcordWorkflowValidationError(
            "prepared starter lineage is missing."
        )
    expected = _build_lineage(
        current,
        prepared.lineage.definition.created_provenance,
    )
    if expected != prepared.lineage:
        raise ConcordWorkflowConflictError(
            "packaged starter lineage changed after preparation."
        )
    if (
        expected.current_version.version.rendering_specification_sha256
        != prepared.rendering_sha256
    ):
        raise ConcordWorkflowConflictError(
            "packaged starter rendering bytes changed after preparation."
        )
    return current


def _result(
    entry: StarterTemplateCatalogEntry,
    loaded: LoadedTemplateLibrary,
    *,
    outcome: str,
    workspace_created: bool = False,
) -> StarterTemplateInstallResult:
    version_id = (
        loaded.current_template_version_id
        if loaded.current_template_version_id is not None
        else loaded.head_template_version_id
    )
    return StarterTemplateInstallResult(
        starter_key=entry.starter_key,
        template_id=entry.template_id,
        template_version_id=version_id,
        outcome=outcome,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
        workspace_created=workspace_created,
    )


__all__ = [
    "STARTER_INSTALLATION_ALREADY_INSTALLED",
    "STARTER_INSTALLATION_CONFLICT",
    "STARTER_INSTALLATION_MISSING",
    "STARTER_INSTALLATION_UPGRADE_AVAILABLE",
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
