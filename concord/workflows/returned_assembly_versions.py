"""Read-only, exact-lineage history of verified returned Artifact PDFs.

A directory name, modification time, or arbitrary PDF is NEVER evidence of a
valid assembly. Every candidate is reconstructed from canonical scan identity
and verified against its manifest, PDF digest, and retained sources.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path
from typing import Any, cast

from pds_core.routes import safe_module_work_descendant
from pds_core.routing_models import ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance
from concord.storage import load_current_record_graph
from concord.storage_paths import work_root
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyIntegrityError,
    AssemblyPageSelection,
    _assembly_id,
    _assembly_paths,
    _assert_no_link_like_ancestors,
    _is_link_like,
    _load_manifest,
    _require_current_snapshot_unchanged,
    _select_lineage,
    _validate_retained_source,
    _verify_existing,
)
from concord.workflows.artifact_page import _standards
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
)
from concord.workflows.teacher_evidence_chronology import instant

_ASSEMBLY_NAME = re.compile(r"assembly_[0-9a-f]{32}\Z")
_MAX_ASSEMBLIES = 256


@dataclass(frozen=True, slots=True, kw_only=True)
class VerifiedAssemblyVersion:
    """An exact, verified historical combination. Not a Review/Score binding."""

    assembly_id: str
    assembled_at: str
    page_count: int
    selections: tuple[AssemblyPageSelection, ...]
    snapshot_revision: int
    newer_evidence_status: str


def _recorded_datetime(value: object) -> datetime:
    """Refuse unknown or timezone-naive manifest chronology."""
    if not isinstance(value, str):
        raise ArtifactAssemblyIntegrityError("Assembly creation time is invalid.")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ArtifactAssemblyIntegrityError(
            "Assembly creation time is invalid."
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ArtifactAssemblyIntegrityError("Assembly creation time has no timezone.")
    return parsed.astimezone(timezone.utc)


def _exact_manifest_selections(
    document: dict[str, Any],
) -> tuple[AssemblyPageSelection, ...]:
    pages = document.get("ordered_pages")
    if not isinstance(pages, list) or not pages:
        raise ArtifactAssemblyIntegrityError("Assembly page history is invalid.")
    selections: list[AssemblyPageSelection] = []
    for page in pages:
        if not isinstance(page, dict):
            raise ArtifactAssemblyIntegrityError("Assembly page history is invalid.")
        page_id = page.get("artifact_page_id")
        scan_id = page.get("scan_reference_id")
        if not isinstance(page_id, str) or not isinstance(scan_id, str):
            raise ArtifactAssemblyIntegrityError("Assembly page history is invalid.")
        selections.append(
            AssemblyPageSelection(
                artifact_page_id=page_id,
                scan_reference_id=scan_id,
            )
        )
    return tuple(selections)


def _existing_versions(
    root: Path,
    work: ModuleWorkRef,
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
    snapshot_revision: int,
) -> tuple[VerifiedAssemblyVersion, ...]:
    base = safe_module_work_descendant(
        root,
        work,
        f"attachments/artifacts/{artifact.artifact_instance_id}/assemblies",
    )
    _assert_no_link_like_ancestors(base, stop=work_root(root, work))
    if not base.exists():
        return ()
    if _is_link_like(base) or not base.is_dir():
        raise ArtifactAssemblyIntegrityError("Assembly history directory is unsafe.")

    entries = sorted(
        islice(base.iterdir(), _MAX_ASSEMBLIES + 1),
        key=lambda entry: entry.name,
    )
    if len(entries) > _MAX_ASSEMBLIES:
        raise ArtifactAssemblyIntegrityError(
            "Too many assembly versions to inspect safely."
        )
    scans = {scan.scan_reference_id: scan for scan in graph.scan_references}
    versions: list[VerifiedAssemblyVersion] = []
    for entry in entries:
        # The installer uses transient .assembly.* directories. Never confuse
        # incomplete preparations with durable historical assemblies.
        if _is_link_like(entry):
            raise ArtifactAssemblyIntegrityError(
                "Unexpected or unsafe entry in assembly history."
            )
        if entry.name.startswith(".assembly."):
            continue
        if not entry.is_dir() or not _ASSEMBLY_NAME.fullmatch(entry.name):
            raise ArtifactAssemblyIntegrityError(
                "Unexpected or unsafe entry in assembly history."
            )
        output, manifest = _assembly_paths(
            root, work, artifact.artifact_instance_id, entry.name
        )
        document = _load_manifest(manifest)
        selections = _exact_manifest_selections(document)
        lineage = _select_lineage(artifact, graph, selections)
        if len(selections) != len(lineage):
            raise ArtifactAssemblyIntegrityError(
                "Assembly history has incomplete page identity."
            )
        if _assembly_id(artifact.artifact_instance_id, lineage) != entry.name:
            raise ArtifactAssemblyIntegrityError(
                "Assembly history does not match canonical scan lineage."
            )
        for item in lineage:
            scan = scans.get(item.scan_reference_id)
            if scan is None:
                raise ArtifactAssemblyIntegrityError(
                    "Assembly source is absent from current evidence."
                )
            _validate_retained_source(root, scan)
        _verify_existing(
            output_path=output,
            manifest_path=manifest,
            work=work,
            artifact=artifact,
            assembly_id=entry.name,
            lineage=lineage,
        )
        created = document["created_provenance"]
        if not isinstance(created, dict):
            raise ArtifactAssemblyIntegrityError(
                "Assembly creation provenance is invalid."
            )
        timestamp = created.get("timestamp")
        _recorded_datetime(timestamp)
        assert isinstance(timestamp, str)
        selected_ids = {
            choice.artifact_page_id: choice.scan_reference_id
            for choice in selections
        }
        selected_times = {
            page_id: instant(scans[scan_id].created_provenance.timestamp)
            for page_id, scan_id in selected_ids.items()
        }
        has_newer = False
        has_uncertain = False
        for scan in graph.scan_references:
            chosen_id = selected_ids.get(scan.artifact_page_id)
            if chosen_id is None or chosen_id == scan.scan_reference_id:
                continue
            chosen_time = selected_times[scan.artifact_page_id]
            candidate_time = instant(scan.created_provenance.timestamp)
            if chosen_time is None or candidate_time is None:
                has_uncertain = True
            elif candidate_time > chosen_time:
                has_newer = True
            elif candidate_time == chosen_time:
                has_uncertain = True
        attention = (
            "newer" if has_newer
            else "additional_uncertain" if has_uncertain
            else "none"
        )
        versions.append(
            VerifiedAssemblyVersion(
                assembly_id=entry.name,
                assembled_at=timestamp,
                page_count=len(lineage),
                selections=selections,
                snapshot_revision=snapshot_revision,
                newer_evidence_status=attention,
            )
        )
    return tuple(
        sorted(
            versions,
            key=lambda item: (
                _recorded_datetime(item.assembled_at),
                item.assembly_id,
            ),
            reverse=True,
        )
    )


def list_verified_assembly_versions(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    expected_snapshot_revision: int | None = None,
    workspace_root: str | Path | None = None,
) -> tuple[VerifiedAssemblyVersion, ...]:
    """List ONLY verified assemblies, sorted newest *assembled* first.

    This is not a current Review/Score version determination. Opening one
    requires a separate snapshot-guarded `open_returned_artifact_evidence` call.
    """
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Workspace is unavailable.")
    require_core_class(root, class_id)
    work = ModuleWorkRef("concord", class_id, activity_id)
    loaded = load_current_record_graph(
        root, work, standards_library=_standards(root)
    )
    if (
        expected_snapshot_revision is not None
        and expected_snapshot_revision != loaded.snapshot_revision
    ):
        raise ConcordWorkflowConflictError(
            "Activity changed before assembly history was inspected."
        )
    graph = cast(ConcordRecordGraph, loaded.graph)
    artifact = next(
        (
            item for item in graph.artifact_instances
            if item.artifact_instance_id == artifact_instance_id
            and item.activity_id == activity_id
        ),
        None,
    )
    if artifact is None:
        raise ConcordWorkflowNotFoundError("Selected work is unavailable.")
    versions = _existing_versions(
        root, work, artifact, graph, loaded.snapshot_revision
    )
    _require_current_snapshot_unchanged(
        root,
        work,
        snapshot_revision=loaded.snapshot_revision,
        snapshot_sha256=loaded.snapshot_sha256,
    )
    return versions


__all__ = ["VerifiedAssemblyVersion", "list_verified_assembly_versions"]
