"""Canonical workspace-level paths for reusable Concord Packets."""

from __future__ import annotations

from pathlib import Path

from pds_core.identifiers import validate_identifier
from pds_core.workspace import resolve_workspace_root


class PacketStoragePathError(ValueError):
    """A reusable Packet storage path request is invalid."""


def _id(value: object, name: str) -> str:
    try:
        return validate_identifier(value, name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise PacketStoragePathError(str(error)) from error


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise PacketStoragePathError(f"{name} must be a positive integer.")
    return value


def packet_library_root(workspace_root: str | Path) -> Path:
    return (
        resolve_workspace_root(workspace_root)
        / "shared"
        / "concord"
        / "packets"
    )


def packet_root(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_library_root(workspace_root) / _id(
        packet_definition_id,
        "packet_definition_id",
    )


def packet_state_root(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_root(workspace_root, packet_definition_id) / "state"


def packet_marker_path(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_state_root(
        workspace_root,
        packet_definition_id,
    ) / "library.json"


def packet_records_root(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_state_root(
        workspace_root,
        packet_definition_id,
    ) / "records"


def packet_record_identity_root(
    workspace_root: str | Path,
    packet_definition_id: str,
    record_kind: str,
    record_id: str,
) -> Path:
    if record_kind not in {"packet_definition", "packet_version"}:
        raise PacketStoragePathError(
            f"unsupported reusable Packet record kind {record_kind!r}."
        )
    return (
        packet_records_root(workspace_root, packet_definition_id)
        / record_kind
        / _id(record_id, "record_id")
    )


def packet_record_revision_path(
    workspace_root: str | Path,
    packet_definition_id: str,
    record_kind: str,
    record_id: str,
    record_revision: int,
) -> Path:
    return (
        packet_record_identity_root(
            workspace_root,
            packet_definition_id,
            record_kind,
            record_id,
        )
        / "revisions"
        / f"{_positive(record_revision, 'record_revision')}.json"
    )


def packet_snapshots_root(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_state_root(
        workspace_root,
        packet_definition_id,
    ) / "snapshots"


def packet_snapshot_path(
    workspace_root: str | Path,
    packet_definition_id: str,
    snapshot_revision: int,
) -> Path:
    return (
        packet_snapshots_root(workspace_root, packet_definition_id)
        / f"{_positive(snapshot_revision, 'snapshot_revision')}.json"
    )


def packet_current_path(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_state_root(
        workspace_root,
        packet_definition_id,
    ) / "current.json"


def packet_locks_root(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_state_root(
        workspace_root,
        packet_definition_id,
    ) / ".locks"


def packet_write_lock_path(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> Path:
    return packet_locks_root(
        workspace_root,
        packet_definition_id,
    ) / "write.lock"


__all__ = [
    "PacketStoragePathError",
    "packet_current_path",
    "packet_library_root",
    "packet_locks_root",
    "packet_marker_path",
    "packet_record_identity_root",
    "packet_record_revision_path",
    "packet_records_root",
    "packet_root",
    "packet_snapshot_path",
    "packet_snapshots_root",
    "packet_state_root",
    "packet_write_lock_path",
]
