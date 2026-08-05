"""Containment-safe canonical paths beneath a Core module work root."""

from __future__ import annotations

from pathlib import Path

from pds_core.identifiers import validate_identifier
from pds_core.routes import module_work_dir, safe_module_work_descendant
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import resolve_workspace_root

from concord.record_registry import descriptor_for_kind
from concord.storage_errors import ConcordStorageValidationError


def _work(work: ModuleWorkRef) -> ModuleWorkRef:
    if not isinstance(work, ModuleWorkRef) or work.module_id != "concord":
        raise ConcordStorageValidationError("work must identify the concord module.")
    return work


def _revision(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise ConcordStorageValidationError(f"{name} must be a positive integer.")
    return value


def work_root(root: str | Path, work: ModuleWorkRef) -> Path:
    return module_work_dir(resolve_workspace_root(root), _work(work))


def state_path(root: str | Path, work: ModuleWorkRef, *parts: str) -> Path:
    relative = "/".join(("state", *parts))
    try:
        return safe_module_work_descendant(
            resolve_workspace_root(root), _work(work), relative
        )
    except ValueError as error:
        raise ConcordStorageValidationError(str(error)) from error


def work_marker_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return state_path(root, work, "work.json")


def records_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return state_path(root, work, "records")


def record_identity_path(
    root: str | Path, work: ModuleWorkRef, kind: str, record_id: str
) -> Path:
    descriptor_for_kind(kind)
    try:
        validated_id = validate_identifier(record_id, "record_id")
    except ValueError as error:
        raise ConcordStorageValidationError(str(error)) from error
    return state_path(root, work, "records", kind, validated_id)


def record_revisions_path(
    root: str | Path, work: ModuleWorkRef, kind: str, record_id: str
) -> Path:
    return record_identity_path(root, work, kind, record_id) / "revisions"


def record_revision_path(
    root: str | Path, work: ModuleWorkRef, kind: str, record_id: str, revision: int
) -> Path:
    return (
        record_revisions_path(root, work, kind, record_id)
        / f"{_revision(revision, 'record_revision')}.json"
    )


def snapshots_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return state_path(root, work, "snapshots")


def snapshot_path(root: str | Path, work: ModuleWorkRef, revision: int) -> Path:
    return (
        snapshots_path(root, work) / f"{_revision(revision, 'snapshot_revision')}.json"
    )


def current_snapshot_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return state_path(root, work, "current.json")


def derived_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return state_path(root, work, "derived")


def catalog_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return derived_path(root, work) / "catalog.sqlite"


def locks_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return state_path(root, work, ".locks")


def write_lock_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return locks_path(root, work) / "write.lock"


def catalog_lock_path(root: str | Path, work: ModuleWorkRef) -> Path:
    return locks_path(root, work) / "catalog.lock"
