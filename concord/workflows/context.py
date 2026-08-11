"""Core-owned workspace, class, actor, and provenance workflow helpers."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    ClassMetadata,
    ClassMetadataError,
    load_class_metadata_for_class,
)
from pds_core.classes import list_class_folders
from pds_core.identifiers import IdentifierValidationError, validate_identifier
from pds_core.workspace import (
    WorkspaceRootError,
    ensure_workspace_root,
    inspect_workspace_root,
    resolve_workspace_root,
)

from concord import __version__
from concord.models import ActorReference, Provenance
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import (
    ClassSummary,
    WorkflowActor,
    WorkspaceBootstrapResult,
)

Clock = Callable[[], datetime]


def resolve_read_workspace_root(
    explicit_root: str | Path | None = None,
) -> Path | None:
    """Resolve a workspace for reading without creating filesystem state."""
    status = inspect_workspace_root(explicit_root)
    if not status.exists:
        return None
    if not status.is_dir:
        raise WorkspaceRootError(f"Workspace root is not a directory: {status.root}")
    return status.root


def ensure_mutating_workspace_root(
    explicit_root: str | Path | None = None,
) -> WorkspaceBootstrapResult:
    """Resolve and initialize the Core workspace for an explicit write workflow."""
    status = inspect_workspace_root(explicit_root)
    root = resolve_workspace_root(explicit_root)
    ensured = ensure_workspace_root(root)
    return WorkspaceBootstrapResult(root=ensured, created=not status.exists)


def list_available_classes(
    explicit_root: str | Path | None = None,
) -> tuple[ClassSummary, ...]:
    """List valid Core classes with metadata without creating workspace state."""
    root = resolve_read_workspace_root(explicit_root)
    if root is None:
        return ()
    summaries: list[ClassSummary] = []
    for folder in list_class_folders(
        root,
        require_metadata=True,
        load_metadata=True,
    ):
        if folder.metadata is None:
            continue
        summaries.append(
            ClassSummary(
                class_id=folder.class_id,
                school_year=folder.metadata.school_year,
            )
        )
    return tuple(summaries)


def require_core_class(root: str | Path, class_id: str) -> ClassMetadata:
    """Load one exact Core class or raise a structured workflow error."""
    try:
        validate_identifier(class_id, "class_id")
    except IdentifierValidationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    try:
        return load_class_metadata_for_class(root, class_id)
    except ClassMetadataError as error:
        raise ConcordWorkflowNotFoundError(
            f"Core class is not available: {class_id}"
        ) from error


def actor_reference(actor: WorkflowActor) -> ActorReference:
    """Convert a validated workflow actor to the native actor reference."""
    return ActorReference(
        actor_kind=actor.actor_kind,
        actor_id=actor.actor_id,
        owning_system=actor.owning_system,
        display_label_snapshot=actor.display_label,
        role_snapshot=actor.role_label,
    )


def workflow_timestamp(clock: Clock | None = None) -> str:
    """Return an offset-aware ISO timestamp, allowing deterministic tests."""
    value = datetime.now(timezone.utc) if clock is None else clock()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ConcordWorkflowValidationError(
            "workflow clock must return a timezone-aware datetime."
        )
    return value.isoformat()


def provenance(
    actor: WorkflowActor,
    *,
    clock: Clock | None = None,
    source_kind: str = "manual",
) -> Provenance:
    """Build native provenance for one workflow-authored record transition."""
    return Provenance(
        actor=actor_reference(actor),
        timestamp=workflow_timestamp(clock),
        source_kind=source_kind,
        application_version=__version__,
    )
