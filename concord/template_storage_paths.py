"""Canonical workspace-level paths for reusable Concord Templates."""

from __future__ import annotations

from pathlib import Path

from pds_core.identifiers import validate_identifier
from pds_core.workspace import resolve_workspace_root


class TemplateStoragePathError(ValueError):
    """A reusable Template storage path request is invalid."""


def _id(value: object, name: str) -> str:
    try:
        return validate_identifier(value, name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise TemplateStoragePathError(str(error)) from error


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise TemplateStoragePathError(f"{name} must be a positive integer.")
    return value


def template_library_root(workspace_root: str | Path) -> Path:
    return (
        resolve_workspace_root(workspace_root)
        / "shared"
        / "concord"
        / "templates"
    )


def template_root(workspace_root: str | Path, template_id: str) -> Path:
    return template_library_root(workspace_root) / _id(template_id, "template_id")


def template_state_root(workspace_root: str | Path, template_id: str) -> Path:
    return template_root(workspace_root, template_id) / "state"


def template_marker_path(workspace_root: str | Path, template_id: str) -> Path:
    return template_state_root(workspace_root, template_id) / "library.json"


def template_records_root(workspace_root: str | Path, template_id: str) -> Path:
    return template_state_root(workspace_root, template_id) / "records"


def template_record_identity_root(
    workspace_root: str | Path,
    template_id: str,
    record_kind: str,
    record_id: str,
) -> Path:
    if record_kind not in {"template_definition", "template_version"}:
        raise TemplateStoragePathError(
            f"unsupported reusable Template record kind {record_kind!r}."
        )
    return (
        template_records_root(workspace_root, template_id)
        / record_kind
        / _id(record_id, "record_id")
    )


def template_record_revision_path(
    workspace_root: str | Path,
    template_id: str,
    record_kind: str,
    record_id: str,
    record_revision: int,
) -> Path:
    return (
        template_record_identity_root(
            workspace_root,
            template_id,
            record_kind,
            record_id,
        )
        / "revisions"
        / f"{_positive(record_revision, 'record_revision')}.json"
    )


def template_snapshots_root(
    workspace_root: str | Path,
    template_id: str,
) -> Path:
    return template_state_root(workspace_root, template_id) / "snapshots"


def template_snapshot_path(
    workspace_root: str | Path,
    template_id: str,
    snapshot_revision: int,
) -> Path:
    return (
        template_snapshots_root(workspace_root, template_id)
        / f"{_positive(snapshot_revision, 'snapshot_revision')}.json"
    )


def template_current_path(
    workspace_root: str | Path,
    template_id: str,
) -> Path:
    return template_state_root(workspace_root, template_id) / "current.json"


def template_locks_root(
    workspace_root: str | Path,
    template_id: str,
) -> Path:
    return template_state_root(workspace_root, template_id) / ".locks"


def template_write_lock_path(
    workspace_root: str | Path,
    template_id: str,
) -> Path:
    return template_locks_root(workspace_root, template_id) / "write.lock"


def template_rendering_root(
    workspace_root: str | Path,
    template_id: str,
) -> Path:
    return template_root(workspace_root, template_id) / "rendering-specifications"


def template_rendering_specification_path(
    workspace_root: str | Path,
    template_id: str,
    rendering_specification_reference: str,
) -> Path:
    reference = _id(
        rendering_specification_reference,
        "rendering_specification_reference",
    )
    return template_rendering_root(workspace_root, template_id) / f"{reference}.bin"


__all__ = [
    "TemplateStoragePathError",
    "template_current_path",
    "template_library_root",
    "template_locks_root",
    "template_marker_path",
    "template_record_identity_root",
    "template_record_revision_path",
    "template_records_root",
    "template_rendering_root",
    "template_rendering_specification_path",
    "template_root",
    "template_snapshot_path",
    "template_snapshots_root",
    "template_state_root",
    "template_write_lock_path",
]
