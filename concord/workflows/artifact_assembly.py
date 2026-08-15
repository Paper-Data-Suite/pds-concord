"""Returned Artifact assembly from exact Core-retained scan lineage."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat as stat_module
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from pds_core.routes import safe_module_work_descendant
from pds_core.routing_models import ModuleWorkRef

from concord.artifact_rendering import (
    ReturnedArtifactRenderIntegrityError,
    VerifiedRetainedSource,
    encode_returned_artifact_pdf,
    render_retained_source_page,
    validate_retained_source,
)
from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance, ArtifactPage, ScanReference
from concord.storage import load_current_record_graph
from concord.storage_errors import ConcordStorageConflictError
from concord.storage_paths import work_root
from concord.workflows.artifact_page import _standards
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    provenance,
    require_core_class,
)
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor

_ASSEMBLY_SCHEMA_VERSION = "1"
_ASSEMBLY_FILENAME = "artifact.pdf"
_MANIFEST_FILENAME = "manifest.json"
_SHA256_LENGTH = 64
_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff"})


@dataclass(frozen=True, slots=True, kw_only=True)
class AssemblyPageSelection:
    artifact_page_id: str
    scan_reference_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AssemblyPageLineage:
    artifact_page_id: str
    logical_page_number: int
    scan_reference_id: str
    source_scan_id: str
    source_page_number: int
    retained_source_relative_path: str
    retained_source_sha256: str


@dataclass(frozen=True, slots=True, kw_only=True)
class AssemblyAmbiguity:
    artifact_page_id: str
    logical_page_number: int
    scan_reference_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class AssembleArtifactRequest:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    selections: tuple[AssemblyPageSelection, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class AssembleArtifactResult:
    work: ModuleWorkRef
    artifact_instance_id: str
    assembly_id: str
    output_path: Path
    manifest_path: Path
    page_count: int
    output_sha256: str
    reused: bool


class ArtifactAssemblyError(ConcordWorkflowValidationError):
    """Base class for expected returned-Artifact assembly failures."""


class ArtifactAssemblyIncompleteError(ArtifactAssemblyError):
    def __init__(self, missing_pages: tuple[tuple[int, str], ...]) -> None:
        self.missing_pages = missing_pages
        summary = ", ".join(
            f"{page_number} ({page_id})" for page_number, page_id in missing_pages
        )
        super().__init__(f"Artifact is missing required returned pages: {summary}")


class ArtifactAssemblyAmbiguityError(ArtifactAssemblyError):
    def __init__(self, ambiguities: tuple[AssemblyAmbiguity, ...]) -> None:
        self.ambiguities = ambiguities
        summary = ", ".join(
            f"{item.logical_page_number} ({item.artifact_page_id})"
            for item in ambiguities
        )
        super().__init__(
            "Artifact has multiple returned occurrences requiring exact selection: "
            f"{summary}"
        )


class ArtifactAssemblyIntegrityError(ArtifactAssemblyError):
    """Canonical retained-source or derived-output integrity failed."""


def _lineage_dict(lineage: AssemblyPageLineage) -> dict[str, object]:
    return {
        "artifact_page_id": lineage.artifact_page_id,
        "logical_page_number": lineage.logical_page_number,
        "scan_reference_id": lineage.scan_reference_id,
        "source_scan_id": lineage.source_scan_id,
        "source_page_number": lineage.source_page_number,
        "retained_source_relative_path": lineage.retained_source_relative_path,
        "retained_source_sha256": lineage.retained_source_sha256,
    }


def _assembly_id(
    artifact_instance_id: str, lineage: tuple[AssemblyPageLineage, ...]
) -> str:
    identity = {
        "schema_version": _ASSEMBLY_SCHEMA_VERSION,
        "artifact_instance_id": artifact_instance_id,
        "ordered_pages": [_lineage_dict(item) for item in lineage],
    }
    raw = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return f"assembly_{hashlib.sha256(raw).hexdigest()[:32]}"


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = int(getattr(path.lstat(), "st_file_attributes", 0))
    except OSError:
        return False
    reparse = int(getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    return bool(reparse and attributes & reparse)


def _assert_no_link_like_ancestors(path: Path, *, stop: Path) -> None:
    current = path
    while True:
        if os.path.lexists(current) and _is_link_like(current):
            raise ArtifactAssemblyIntegrityError(
                f"assembly path traverses a link-like filesystem object: {current}"
            )
        if current == stop:
            return
        if stop not in current.parents:
            raise ArtifactAssemblyIntegrityError(
                "assembly path escaped the Concord work root."
            )
        current = current.parent


def _validate_retained_source(
    root: Path,
    scan: ScanReference,
) -> VerifiedRetainedSource:
    try:
        return validate_retained_source(root, scan)
    except ReturnedArtifactRenderIntegrityError as error:
        raise ArtifactAssemblyIntegrityError(str(error)) from error

def _page_image(
    source: VerifiedRetainedSource,
    source_page_number: int,
) -> Any:
    try:
        return render_retained_source_page(source, source_page_number)
    except ReturnedArtifactRenderIntegrityError as error:
        raise ArtifactAssemblyIntegrityError(str(error)) from error

def _pdf_bytes(images: tuple[Any, ...], created_at: str) -> bytes:
    try:
        return encode_returned_artifact_pdf(images, created_at)
    except ReturnedArtifactRenderIntegrityError as error:
        raise ArtifactAssemblyIntegrityError(str(error)) from error

def _selection_map(
    selections: tuple[AssemblyPageSelection, ...],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for selection in selections:
        if selection.artifact_page_id in result:
            raise ArtifactAssemblyError(
                "only one Scan Reference selection may be supplied per Artifact Page."
            )
        result[selection.artifact_page_id] = selection.scan_reference_id
    return result


def _required_pages(
    artifact: ArtifactInstance, graph: ConcordRecordGraph
) -> tuple[ArtifactPage, ...]:
    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    ordered: list[ArtifactPage] = []
    for page_id in artifact.page_ids:
        page = pages.get(page_id)
        if page is None or page.artifact_instance_id != artifact.artifact_instance_id:
            raise ArtifactAssemblyIntegrityError(
                "Artifact declared page structure is inconsistent."
            )
        if page.return_expected:
            ordered.append(page)
    if not ordered:
        raise ArtifactAssemblyError(
            "Artifact has no return-expected pages to assemble."
        )
    return tuple(ordered)


def _select_lineage(
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
    selections: tuple[AssemblyPageSelection, ...],
) -> tuple[AssemblyPageLineage, ...]:
    required = _required_pages(artifact, graph)
    required_ids = {page.artifact_page_id for page in required}
    supplied = _selection_map(selections)
    extra = sorted(set(supplied) - required_ids)
    if extra:
        raise ArtifactAssemblyError(
            "Scan Reference selection targets a non-required Artifact Page: "
            + ", ".join(extra)
        )

    scans_by_page: dict[str, list[ScanReference]] = {
        page.artifact_page_id: [] for page in required
    }
    for scan in graph.scan_references:
        if scan.artifact_page_id in scans_by_page:
            scans_by_page[scan.artifact_page_id].append(scan)

    missing: list[tuple[int, str]] = []
    ambiguous: list[AssemblyAmbiguity] = []
    selected: list[AssemblyPageLineage] = []
    for page in required:
        candidates = tuple(
            sorted(
                scans_by_page[page.artifact_page_id],
                key=lambda item: item.scan_reference_id,
            )
        )
        requested = supplied.get(page.artifact_page_id)
        if not candidates:
            missing.append((page.page_number, page.artifact_page_id))
            continue
        if requested is None and len(candidates) > 1:
            ambiguous.append(
                AssemblyAmbiguity(
                    artifact_page_id=page.artifact_page_id,
                    logical_page_number=page.page_number,
                    scan_reference_ids=tuple(
                        item.scan_reference_id for item in candidates
                    ),
                )
            )
            continue
        if requested is None:
            chosen = candidates[0]
        else:
            selected_candidate = next(
                (
                    item
                    for item in candidates
                    if item.scan_reference_id == requested
                ),
                None,
            )
            if selected_candidate is None:
                raise ArtifactAssemblyError(
                    "selected Scan Reference does not belong to the requested "
                    f"Artifact Page: {page.artifact_page_id}"
                )
            chosen = selected_candidate
        if (
            chosen.activity_id != artifact.activity_id
            or chosen.artifact_page_id != page.artifact_page_id
            or chosen.route_id != page.route_id
        ):
            raise ArtifactAssemblyIntegrityError(
                "Scan Reference contradicts the canonical Artifact Page."
            )
        selected.append(
            AssemblyPageLineage(
                artifact_page_id=page.artifact_page_id,
                logical_page_number=page.page_number,
                scan_reference_id=chosen.scan_reference_id,
                source_scan_id=chosen.source_scan_id,
                source_page_number=chosen.source_page_number,
                retained_source_relative_path=chosen.retained_source_relative_path,
                retained_source_sha256=chosen.retained_source_sha256,
            )
        )
    if missing:
        raise ArtifactAssemblyIncompleteError(tuple(missing))
    if ambiguous:
        raise ArtifactAssemblyAmbiguityError(tuple(ambiguous))
    return tuple(selected)


def _manifest_provenance(
    actor: WorkflowActor, *, clock: Clock | None
) -> dict[str, str]:
    created = provenance(actor, clock=clock, source_kind="generated")
    return {
        "actor_kind": created.actor.actor_kind,
        "actor_id": created.actor.actor_id,
        "owning_system": created.actor.owning_system,
        "timestamp": created.timestamp,
        "source_kind": created.source_kind,
        "application_version": created.application_version or "",
    }


def _manifest_document(
    *,
    work: ModuleWorkRef,
    artifact: ArtifactInstance,
    assembly_id: str,
    lineage: tuple[AssemblyPageLineage, ...],
    source_snapshot_revision: int,
    source_snapshot_sha256: str,
    output_sha256: str,
    created_provenance: dict[str, str],
) -> dict[str, object]:
    return {
        "schema_version": _ASSEMBLY_SCHEMA_VERSION,
        "assembly_id": assembly_id,
        "work": {
            "module_id": work.module_id,
            "class_id": work.class_id,
            "work_id": work.work_id,
        },
        "artifact_instance_id": artifact.artifact_instance_id,
        "source_snapshot_revision": source_snapshot_revision,
        "source_snapshot_sha256": source_snapshot_sha256,
        "ordered_pages": [_lineage_dict(item) for item in lineage],
        "output_filename": _ASSEMBLY_FILENAME,
        "output_sha256": output_sha256,
        "page_count": len(lineage),
        "privacy_classification": artifact.privacy_policy.classification,
        "created_provenance": created_provenance,
    }


def _manifest_bytes(document: dict[str, object]) -> bytes:
    try:
        text = json.dumps(
            document,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ArtifactAssemblyIntegrityError(
            "assembly manifest is not strict JSON."
        ) from error
    return (text + "\n").encode("utf-8")


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_strict_pairs,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ArtifactAssemblyIntegrityError(
            "existing assembly manifest is invalid."
        ) from error
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ArtifactAssemblyIntegrityError(
            "existing assembly manifest must be a JSON object."
        )
    return cast(dict[str, Any], value)


def _assembly_paths(
    root: Path, work: ModuleWorkRef, artifact_instance_id: str, assembly_id: str
) -> tuple[Path, Path]:
    relative_root = (
        f"attachments/artifacts/{artifact_instance_id}/assemblies/{assembly_id}"
    )
    target = safe_module_work_descendant(root, work, relative_root)
    _assert_no_link_like_ancestors(target, stop=work_root(root, work))
    return target / _ASSEMBLY_FILENAME, target / _MANIFEST_FILENAME


def _verify_existing(
    *,
    output_path: Path,
    manifest_path: Path,
    work: ModuleWorkRef,
    artifact: ArtifactInstance,
    assembly_id: str,
    lineage: tuple[AssemblyPageLineage, ...],
) -> str:
    if (
        _is_link_like(output_path)
        or _is_link_like(manifest_path)
        or not output_path.is_file()
        or not manifest_path.is_file()
    ):
        raise ArtifactAssemblyIntegrityError(
            "existing assembly is incomplete or link-like."
        )
    document = _load_manifest(manifest_path)
    expected_keys = {
        "schema_version",
        "assembly_id",
        "work",
        "artifact_instance_id",
        "source_snapshot_revision",
        "source_snapshot_sha256",
        "ordered_pages",
        "output_filename",
        "output_sha256",
        "page_count",
        "privacy_classification",
        "created_provenance",
    }
    if set(document) != expected_keys:
        raise ArtifactAssemblyIntegrityError(
            "existing assembly manifest has an unexpected schema."
        )
    if (
        document["schema_version"] != _ASSEMBLY_SCHEMA_VERSION
        or document["assembly_id"] != assembly_id
        or document["artifact_instance_id"] != artifact.artifact_instance_id
        or document["work"]
        != {
            "module_id": work.module_id,
            "class_id": work.class_id,
            "work_id": work.work_id,
        }
        or document["ordered_pages"] != [_lineage_dict(item) for item in lineage]
        or document["output_filename"] != _ASSEMBLY_FILENAME
        or document["page_count"] != len(lineage)
        or document["privacy_classification"]
        != artifact.privacy_policy.classification
    ):
        raise ArtifactAssemblyIntegrityError(
            "existing assembly manifest contradicts canonical source lineage."
        )
    revision = document["source_snapshot_revision"]
    snapshot_sha = document["source_snapshot_sha256"]
    if (
        type(revision) is not int
        or revision < 1
        or not isinstance(snapshot_sha, str)
        or len(snapshot_sha) != _SHA256_LENGTH
    ):
        raise ArtifactAssemblyIntegrityError(
            "existing assembly manifest has invalid source snapshot lineage."
        )
    expected_output_sha = document["output_sha256"]
    if (
        not isinstance(expected_output_sha, str)
        or len(expected_output_sha) != _SHA256_LENGTH
    ):
        raise ArtifactAssemblyIntegrityError(
            "existing assembly manifest has an invalid output digest."
        )
    try:
        actual_output_sha = hashlib.sha256(output_path.read_bytes()).hexdigest()
    except OSError as error:
        raise ArtifactAssemblyIntegrityError(
            "existing assembly PDF could not be read."
        ) from error
    if actual_output_sha != expected_output_sha:
        raise ArtifactAssemblyIntegrityError(
            "existing assembly PDF digest does not match its manifest."
        )
    return expected_output_sha


def _write_file(path: Path, data: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def _install_assembly(
    *,
    root: Path,
    work: ModuleWorkRef,
    artifact: ArtifactInstance,
    assembly_id: str,
    lineage: tuple[AssemblyPageLineage, ...],
    pdf_bytes: bytes,
    manifest_bytes: bytes,
) -> tuple[Path, Path, bool]:
    output_path, manifest_path = _assembly_paths(
        root, work, artifact.artifact_instance_id, assembly_id
    )
    target = output_path.parent
    parent = target.parent
    _assert_no_link_like_ancestors(parent, stop=work_root(root, work))
    parent.mkdir(parents=True, exist_ok=True)
    _assert_no_link_like_ancestors(parent, stop=work_root(root, work))
    if target.exists():
        return output_path, manifest_path, True

    temporary = Path(tempfile.mkdtemp(prefix=".assembly.", dir=parent))
    try:
        _write_file(temporary / _ASSEMBLY_FILENAME, pdf_bytes)
        _write_file(temporary / _MANIFEST_FILENAME, manifest_bytes)
        try:
            os.rename(temporary, target)
        except OSError as error:
            if target.exists():
                shutil.rmtree(temporary, ignore_errors=True)
                return output_path, manifest_path, True
            raise ArtifactAssemblyIntegrityError(
                "completed assembly could not be installed."
            ) from error
        return output_path, manifest_path, False
    finally:
        if temporary.exists():
            shutil.rmtree(temporary, ignore_errors=True)


def assemble_returned_artifact(
    request: AssembleArtifactRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> AssembleArtifactResult:
    """Assemble exact returned pages without changing canonical evidence identity."""
    root = ensure_mutating_workspace_root(workspace_root).root
    require_core_class(root, request.class_id)
    work = ModuleWorkRef("concord", request.class_id, request.activity_id)
    library = _standards(root)
    loaded = load_current_record_graph(root, work, standards_library=library)
    if loaded.snapshot_revision != request.expected_snapshot_revision:
        raise ConcordStorageConflictError(
            f"expected snapshot {request.expected_snapshot_revision}, "
            f"found {loaded.snapshot_revision}."
        )
    graph = cast(ConcordRecordGraph, loaded.graph)
    artifact = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == request.artifact_instance_id
        ),
        None,
    )
    if artifact is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Instance is unavailable: {request.artifact_instance_id}"
        )
    if artifact.activity_id != request.activity_id:
        raise ArtifactAssemblyError("Artifact belongs to another Activity.")

    lineage = _select_lineage(artifact, graph, request.selections)
    images: list[Any] = []
    scans = {item.scan_reference_id: item for item in graph.scan_references}
    for item in lineage:
        scan = scans.get(item.scan_reference_id)
        if scan is None:
            raise ArtifactAssemblyIntegrityError(
                "selected Scan Reference disappeared from canonical state."
            )
        path = _validate_retained_source(root, scan)
        images.append(_page_image(path, scan.source_page_number))

    assembly_id = _assembly_id(artifact.artifact_instance_id, lineage)
    output_path, manifest_path = _assembly_paths(
        root, work, artifact.artifact_instance_id, assembly_id
    )
    if output_path.parent.exists():
        output_sha = _verify_existing(
            output_path=output_path,
            manifest_path=manifest_path,
            work=work,
            artifact=artifact,
            assembly_id=assembly_id,
            lineage=lineage,
        )
        return AssembleArtifactResult(
            work=work,
            artifact_instance_id=artifact.artifact_instance_id,
            assembly_id=assembly_id,
            output_path=output_path,
            manifest_path=manifest_path,
            page_count=len(lineage),
            output_sha256=output_sha,
            reused=True,
        )

    pdf = _pdf_bytes(tuple(images), artifact.created_provenance.timestamp)
    output_sha = hashlib.sha256(pdf).hexdigest()
    created = _manifest_provenance(request.actor, clock=clock)
    document = _manifest_document(
        work=work,
        artifact=artifact,
        assembly_id=assembly_id,
        lineage=lineage,
        source_snapshot_revision=loaded.snapshot_revision,
        source_snapshot_sha256=loaded.snapshot_sha256,
        output_sha256=output_sha,
        created_provenance=created,
    )
    manifest = _manifest_bytes(document)

    current = load_current_record_graph(root, work, standards_library=library)
    if current.snapshot_revision != loaded.snapshot_revision:
        raise ConcordStorageConflictError(
            "Concord state changed while the returned Artifact was being assembled."
        )
    installed_output, installed_manifest, raced = _install_assembly(
        root=root,
        work=work,
        artifact=artifact,
        assembly_id=assembly_id,
        lineage=lineage,
        pdf_bytes=pdf,
        manifest_bytes=manifest,
    )
    verified_sha = _verify_existing(
        output_path=installed_output,
        manifest_path=installed_manifest,
        work=work,
        artifact=artifact,
        assembly_id=assembly_id,
        lineage=lineage,
    )
    if not raced and verified_sha != output_sha:
        raise ArtifactAssemblyIntegrityError(
            "installed returned Artifact differs from prepared PDF bytes."
        )
    return AssembleArtifactResult(
        work=work,
        artifact_instance_id=artifact.artifact_instance_id,
        assembly_id=assembly_id,
        output_path=installed_output,
        manifest_path=installed_manifest,
        page_count=len(lineage),
        output_sha256=verified_sha,
        reused=raced,
    )


__all__ = [
    "AssembleArtifactRequest",
    "AssembleArtifactResult",
    "AssemblyAmbiguity",
    "AssemblyPageLineage",
    "AssemblyPageSelection",
    "ArtifactAssemblyAmbiguityError",
    "ArtifactAssemblyError",
    "ArtifactAssemblyIncompleteError",
    "ArtifactAssemblyIntegrityError",
    "assemble_returned_artifact",
]
