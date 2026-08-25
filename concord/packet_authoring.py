"""Strict noncanonical authoring inputs for reusable Concord Packets."""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from concord.models import PacketComponent, PacketRenderingRules
from concord.packet_serialization import (
    PacketSerializationError,
    dataclass_from_dict,
    strict_json_loads,
)

PACKET_AUTHORING_SCHEMA = "concord_packet_authoring_v1"


class PacketAuthoringError(ValueError):
    """A Packet authoring source is invalid."""


class PacketAuthoringConflictError(PacketAuthoringError):
    """A prepared Packet authoring source changed before commit."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketDefinitionAuthoring:
    name: str
    purpose: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise PacketAuthoringError("definition.name must be non-empty.")
        if not isinstance(self.purpose, str) or not self.purpose.strip():
            raise PacketAuthoringError("definition.purpose must be non-empty.")
        if self.description is not None and (
            not isinstance(self.description, str)
            or not self.description.strip()
        ):
            raise PacketAuthoringError(
                "definition.description must be non-empty when supplied."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketVersionAuthoring:
    version_label: str
    components: tuple[PacketComponent, ...]
    rendering_rules: PacketRenderingRules

    def __post_init__(self) -> None:
        if not isinstance(self.version_label, str) or not self.version_label.strip():
            raise PacketAuthoringError("version.version_label must be non-empty.")
        if not self.components or any(
            not isinstance(item, PacketComponent) for item in self.components
        ):
            raise PacketAuthoringError(
                "version.components must contain PacketComponent values."
            )
        if not isinstance(self.rendering_rules, PacketRenderingRules):
            raise PacketAuthoringError(
                "version.rendering_rules must be PacketRenderingRules."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketAuthoringDocument:
    schema_version: str
    version: PacketVersionAuthoring
    definition: PacketDefinitionAuthoring | None = None

    def __post_init__(self) -> None:
        if self.schema_version != PACKET_AUTHORING_SCHEMA:
            raise PacketAuthoringError(
                f"schema_version must be {PACKET_AUTHORING_SCHEMA!r}."
            )
        if not isinstance(self.version, PacketVersionAuthoring):
            raise PacketAuthoringError(
                "version must be PacketVersionAuthoring."
            )
        if self.definition is not None and not isinstance(
            self.definition,
            PacketDefinitionAuthoring,
        ):
            raise PacketAuthoringError(
                "definition must be PacketDefinitionAuthoring or null."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketSourceFile:
    path: Path
    sha256: str
    size: int
    mtime_ns: int
    device: int
    inode: int
    data: bytes


def prepare_packet_source_file(
    path: str | Path,
    *,
    description: str,
) -> PreparedPacketSourceFile:
    """Read one exact ordinary source file and capture a stable fingerprint."""
    source = Path(path)
    before = _safe_source_stat(source, description)
    try:
        data = source.read_bytes()
    except OSError as error:
        raise PacketAuthoringError(
            f"could not read {description} {source}: {error}"
        ) from error
    after = _safe_source_stat(source, description)
    if _fingerprint(before) != _fingerprint(after) or len(data) != after.st_size:
        raise PacketAuthoringConflictError(
            f"{description} changed while it was being read: {source}"
        )
    return PreparedPacketSourceFile(
        path=source,
        sha256=hashlib.sha256(data).hexdigest(),
        size=after.st_size,
        mtime_ns=after.st_mtime_ns,
        device=after.st_dev,
        inode=after.st_ino,
        data=data,
    )


def verify_prepared_packet_source(
    prepared: PreparedPacketSourceFile,
    *,
    description: str,
) -> bytes:
    """Re-read a prepared source and require the exact reviewed fingerprint."""
    current = prepare_packet_source_file(
        prepared.path,
        description=description,
    )
    if (
        current.sha256 != prepared.sha256
        or current.size != prepared.size
        or current.mtime_ns != prepared.mtime_ns
        or current.device != prepared.device
        or current.inode != prepared.inode
    ):
        raise PacketAuthoringConflictError(
            f"{description} changed after preparation: {prepared.path}"
        )
    return current.data


def load_packet_authoring_source(
    path: str | Path,
) -> tuple[PacketAuthoringDocument, PreparedPacketSourceFile]:
    """Parse one strict Packet authoring transport document."""
    prepared = prepare_packet_source_file(
        path,
        description="Packet authoring file",
    )
    try:
        parsed = strict_json_loads(
            prepared.data,
            description="Packet authoring file",
        )
        document = dataclass_from_dict(PacketAuthoringDocument, parsed)
    except (PacketSerializationError, ValueError) as error:
        raise PacketAuthoringError(
            f"invalid Packet authoring file {prepared.path}: {error}"
        ) from error
    return document, prepared


def _safe_source_stat(path: Path, description: str) -> os.stat_result:
    _require_no_link_like_ancestors(path, description)
    try:
        info = path.stat()
    except FileNotFoundError as error:
        raise PacketAuthoringError(
            f"{description} does not exist: {path}"
        ) from error
    except OSError as error:
        raise PacketAuthoringError(
            f"could not inspect {description} {path}: {error}"
        ) from error
    if not stat.S_ISREG(info.st_mode):
        raise PacketAuthoringError(
            f"{description} must be an ordinary regular file: {path}"
        )
    return info


def _require_no_link_like_ancestors(path: Path, description: str) -> None:
    candidate = path.absolute()
    for item in (candidate, *candidate.parents):
        try:
            if item.is_symlink():
                raise PacketAuthoringError(
                    f"{description} path traverses a symlink: {item}"
                )
            info = item.lstat()
        except FileNotFoundError:
            if item == candidate:
                continue
            raise PacketAuthoringError(
                f"{description} parent path does not exist: {item}"
            )
        except OSError as error:
            raise PacketAuthoringError(
                f"could not inspect {description} path {item}: {error}"
            ) from error
        attributes = getattr(info, "st_file_attributes", 0)
        reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if reparse and attributes & reparse:
            raise PacketAuthoringError(
                f"{description} path traverses a reparse point: {item}"
            )


def _fingerprint(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_mode,
    )


__all__ = [
    "PACKET_AUTHORING_SCHEMA",
    "PacketAuthoringConflictError",
    "PacketAuthoringDocument",
    "PacketAuthoringError",
    "PacketDefinitionAuthoring",
    "PacketVersionAuthoring",
    "PreparedPacketSourceFile",
    "load_packet_authoring_source",
    "prepare_packet_source_file",
    "verify_prepared_packet_source",
]
