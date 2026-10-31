"""Pinned, read-only Core authority for one confirmed Artifact write.

This menu boundary is not write authorization. Native Concord services still
validate every candidate graph, immutable correction, evidence relationship,
roster binding and compare-and-swap before publishing an Activity snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.menu_prompts import load_menu_standards_library
from concord.model_validation import validate_core_standards
from concord.storage_errors import ConcordStorageNotFoundError
from concord.validation_diagnostics import ConcordRecordGraphError
from concord.workflows.activity_read import (
    ActivityReadContext,
    load_activity_read_context,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import ActivitySummary

_REQUIRED_ORIENTATIONS = frozenset({"mixed", "standards_based"})


class ArtifactWriteKwargs(TypedDict, total=False):
    workspace_root: Path
    standards_library: StandardsLibrary


@dataclass(frozen=True, slots=True)
class ArtifactWriteContext:
    """Preview authority for a single selected Activity in one workspace."""

    root: Path
    class_id: str
    activity_id: str
    snapshot_revision: int
    snapshot_sha256: str
    standards_library: StandardsLibrary | None
    standards_required: bool
    candidate_standard_backed: bool
    active_workspace_binding: bool


def _refusal(operation: str, message: str) -> ConcordWorkflowValidationError:
    return ConcordWorkflowValidationError(
        f"{operation}: {message} Reopen the Activity and retry. "
        f"No {operation} was saved."
    )


def _operation_name(operation: str) -> str:
    if not isinstance(operation, str) or not operation.strip():
        raise ConcordWorkflowValidationError("Artifact operation name is required.")
    return operation.strip()


def _canonical_root(root: Path, operation: str) -> Path:
    try:
        return root.resolve(strict=True)
    except OSError as error:
        raise _refusal(
            operation, "The selected Core workspace is unavailable."
        ) from error


def _structural_context(
    root: Path,
    class_id: str,
    activity_id: str,
    operation: str,
) -> ActivityReadContext:
    # Core class metadata and Concord's exact structural snapshot remain
    # authoritative. Neither this read nor the library read creates a workspace.
    try:
        require_core_class(root, class_id)
        context = load_activity_read_context(
            root, ModuleWorkRef("concord", class_id, activity_id)
        )
    except (ConcordWorkflowNotFoundError, ConcordStorageNotFoundError) as error:
        raise _refusal(
            operation,
            "The selected Class or Activity is unavailable in this workspace.",
        ) from error
    if (
        context.work.class_id != class_id
        or context.work.work_id != activity_id
        or context.activity.activity_id != activity_id
        or context.activity.class_reference.record_id != class_id
        or _canonical_root(context.root, operation) != root
    ):
        raise _refusal(operation, "The selected Class or Activity changed identity.")
    return context


def _needs_standards(
    context: ActivityReadContext, *, candidate_standard_backed: bool
) -> bool:
    graph = context.graph
    return (
        context.activity.scoring_orientation in _REQUIRED_ORIENTATIONS
        or any(item.criterion_kind == "standard_backed" for item in graph.criteria)
        or any(item.score_kind == "standard_backed" for item in graph.score_records)
        or candidate_standard_backed
    )


def _library_for_context(
    context: ActivityReadContext,
    operation: str,
    *,
    candidate_standard_backed: bool,
) -> tuple[bool, StandardsLibrary | None]:
    required = _needs_standards(
        context, candidate_standard_backed=candidate_standard_backed
    )
    if not required:
        return False, None
    try:
        library = load_menu_standards_library(context.root)
    except (OSError, ValueError) as error:
        raise _refusal(
            operation, "The canonical Core Standards Library cannot be read."
        ) from error
    if library is None:
        raise _refusal(operation, "The canonical Core Standards Library is missing.")
    if candidate_standard_backed and (
        context.activity.standards_profile_id is None
        or not context.activity.focus_standard_ids
    ):
        raise _refusal(
            operation,
            "This proposed Standards-backed operation lacks an Activity "
            "profile or Focus Standards.",
        )
    try:
        validate_core_standards(context.graph, library)
    except (ConcordRecordGraphError, ValueError) as error:
        raise _refusal(
            operation, "The current Core Standards profile or Focus IDs are invalid."
        ) from error
    return True, library


def begin_artifact_write_context(
    selected: ActivitySummary,
    *,
    operation: str,
    workspace_root: str | Path | None = None,
    candidate_standard_backed: bool = False,
) -> ArtifactWriteContext:
    """Pin a selected teacher Activity and its canonical workspace for preview.

    Explicit-root calls support disposable tests and delegated CLI operations;
    menu callers omit ``workspace_root`` and are bound to the *active* root.
    A stale selected Activity must be refreshed, never silently substituted.
    """
    name = _operation_name(operation)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise _refusal(name, "The Core workspace does not exist.")
    canonical = _canonical_root(root, name)
    context = _structural_context(
        canonical, selected.class_id, selected.activity_id, name
    )
    if context.snapshot_revision != selected.snapshot_revision:
        raise _refusal(name, "The Activity snapshot has changed since selection.")
    required, library = _library_for_context(
        context, name, candidate_standard_backed=candidate_standard_backed
    )
    return ArtifactWriteContext(
        root=canonical,
        class_id=selected.class_id,
        activity_id=selected.activity_id,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        standards_library=library,
        standards_required=required,
        candidate_standard_backed=candidate_standard_backed,
        active_workspace_binding=workspace_root is None,
    )


def revalidate_artifact_write_context(
    preview: ArtifactWriteContext,
    *,
    operation: str,
    expected_snapshot_revision: int,
) -> ArtifactWriteContext:
    """Refresh before an exact guarded commit, rejecting any context drift.

    No automatic retry and no side effects: callers pass the refreshed result
    to the canonical write, which separately owns its native snapshot/CAS gate.
    """
    name = _operation_name(operation)
    if expected_snapshot_revision != preview.snapshot_revision:
        raise _refusal(name, "The confirmed request has a different revision.")
    root = resolve_read_workspace_root(
        None if preview.active_workspace_binding else preview.root
    )
    if root is None or _canonical_root(root, name) != preview.root:
        raise _refusal(name, "The active Core workspace has changed.")
    context = _structural_context(
        preview.root, preview.class_id, preview.activity_id, name
    )
    if (
        context.snapshot_revision != preview.snapshot_revision
        or context.snapshot_sha256 != preview.snapshot_sha256
    ):
        raise _refusal(name, "The Activity snapshot changed after preview.")
    required, library = _library_for_context(
        context, name, candidate_standard_backed=preview.candidate_standard_backed
    )
    if required != preview.standards_required:
        raise _refusal(name, "The Activity Standards requirement changed.")
    return ArtifactWriteContext(
        root=preview.root,
        class_id=preview.class_id,
        activity_id=preview.activity_id,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        standards_library=library,
        standards_required=required,
        candidate_standard_backed=preview.candidate_standard_backed,
        active_workspace_binding=preview.active_workspace_binding,
    )


def artifact_write_kwargs(context: ArtifactWriteContext) -> ArtifactWriteKwargs:
    """Pass exactly the pinned root and conditional Core authority to a mutator."""
    result: ArtifactWriteKwargs = {"workspace_root": context.root}
    if context.standards_required and context.standards_library is None:
        raise ConcordWorkflowValidationError(
            "Artifact Standards authority is missing; no write is permitted."
        )
    if context.standards_library is not None:
        result["standards_library"] = context.standards_library
    return result


__all__ = [
    "ArtifactWriteContext",
    "ArtifactWriteKwargs",
    "artifact_write_kwargs",
    "begin_artifact_write_context",
    "revalidate_artifact_write_context",
    "resolve_read_workspace_root",
]
