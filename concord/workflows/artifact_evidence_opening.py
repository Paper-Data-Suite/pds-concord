"""Read-only opening of verified returned-Artifact evidence."""

from __future__ import annotations

from pathlib import Path

from pds_core.local_open import LocalOpenError, open_local_path

from concord.workflows.artifact_assembly import (
    AssemblyPageSelection,
    ResolvedReturnedArtifactAssembly,
    resolve_returned_artifact_assembly,
)
from concord.workflows.errors import ConcordWorkflowOpenError


def open_returned_artifact_evidence(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    selections: tuple[AssemblyPageSelection, ...] = (),
    workspace_root: str | Path | None = None,
) -> ResolvedReturnedArtifactAssembly:
    """Verify and open one exact existing returned-Artifact PDF.

    Resolution and integrity verification always precede Core's local-open
    boundary. This operation never assembles, repairs, rewrites, Reviews,
    Moderates, Scores, publishes, or records that evidence was viewed.
    """
    resolved = resolve_returned_artifact_assembly(
        class_id,
        activity_id,
        artifact_instance_id,
        selections=selections,
        workspace_root=workspace_root,
    )
    try:
        open_local_path(resolved.output_path)
    except LocalOpenError as error:
        raise ConcordWorkflowOpenError(
            "Concord verified the returned Artifact PDF, but the system could "
            "not open it with the default application."
        ) from error
    return resolved


__all__ = ["open_returned_artifact_evidence"]
