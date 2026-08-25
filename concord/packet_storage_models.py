"""Immutable storage envelopes for the reusable Concord Packet library."""

from __future__ import annotations

import re
from dataclasses import dataclass

from concord.models import PacketDefinition, PacketVersion, Provenance

PACKET_LIBRARY_STORAGE_SCHEMA = "concord_packet_library_storage_v1"
PACKET_LIBRARY_RECORD_KINDS = frozenset(
    {"packet_definition", "packet_version"}
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PacketStorageModelError(ValueError):
    """Reusable Packet storage metadata is invalid."""


def _identifier(value: object, name: str) -> str:
    from pds_core.identifiers import validate_identifier

    try:
        return validate_identifier(value, name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise PacketStorageModelError(str(error)) from error


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise PacketStorageModelError(f"{name} must be a positive integer.")
    return value


def _sha(value: object, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise PacketStorageModelError(
            f"{name} must be exactly 64 lowercase hexadecimal characters."
        )
    return value


def _schema(value: object) -> str:
    if value != PACKET_LIBRARY_STORAGE_SCHEMA:
        raise PacketStorageModelError(
            "storage_schema_version must be "
            f"{PACKET_LIBRARY_STORAGE_SCHEMA!r}."
        )
    return PACKET_LIBRARY_STORAGE_SCHEMA


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketLibraryMarker:
    storage_schema_version: str
    packet_definition_id: str
    created_provenance: Provenance

    def __post_init__(self) -> None:
        _schema(self.storage_schema_version)
        _identifier(self.packet_definition_id, "packet_definition_id")
        if not isinstance(self.created_provenance, Provenance):
            raise PacketStorageModelError(
                "created_provenance must be Provenance."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketRecordRevision:
    storage_schema_version: str
    packet_definition_id: str
    record_kind: str
    record_id: str
    record_revision: int
    operation: str
    operation_provenance: Provenance
    body: dict[str, object]

    def __post_init__(self) -> None:
        _schema(self.storage_schema_version)
        _identifier(self.packet_definition_id, "packet_definition_id")
        if self.record_kind not in PACKET_LIBRARY_RECORD_KINDS:
            raise PacketStorageModelError(
                f"unsupported reusable record kind {self.record_kind!r}."
            )
        _identifier(self.record_id, "record_id")
        _positive(self.record_revision, "record_revision")
        _identifier(self.operation, "operation")
        if not isinstance(self.operation_provenance, Provenance):
            raise PacketStorageModelError(
                "operation_provenance must be Provenance."
            )
        if not isinstance(self.body, dict):
            raise PacketStorageModelError("body must be a JSON object.")


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketRecordRevisionRef:
    record_kind: str
    record_id: str
    record_revision: int
    sha256: str

    def __post_init__(self) -> None:
        if self.record_kind not in PACKET_LIBRARY_RECORD_KINDS:
            raise PacketStorageModelError(
                f"unsupported reusable record kind {self.record_kind!r}."
            )
        _identifier(self.record_id, "record_id")
        _positive(self.record_revision, "record_revision")
        _sha(self.sha256, "sha256")


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketLibrarySnapshot:
    storage_schema_version: str
    packet_definition_id: str
    snapshot_revision: int
    records: tuple[PacketRecordRevisionRef, ...]
    current_packet_version_id: str | None
    head_packet_version_id: str
    previous_snapshot_revision: int | None
    previous_snapshot_sha256: str | None
    operation: str
    operation_provenance: Provenance

    def __post_init__(self) -> None:
        _schema(self.storage_schema_version)
        _identifier(self.packet_definition_id, "packet_definition_id")
        revision = _positive(self.snapshot_revision, "snapshot_revision")
        if not self.records:
            raise PacketStorageModelError(
                "records must contain at least one revision reference."
            )
        if any(
            not isinstance(item, PacketRecordRevisionRef)
            for item in self.records
        ):
            raise PacketStorageModelError(
                "records must contain PacketRecordRevisionRef values."
            )
        identities = tuple(
            (item.record_kind, item.record_id) for item in self.records
        )
        if len(set(identities)) != len(identities):
            raise PacketStorageModelError(
                "snapshot records must not duplicate logical identities."
            )
        if identities != tuple(sorted(identities)):
            raise PacketStorageModelError(
                "snapshot records must be in canonical identity order."
            )
        if self.current_packet_version_id is not None:
            _identifier(
                self.current_packet_version_id,
                "current_packet_version_id",
            )
        _identifier(self.head_packet_version_id, "head_packet_version_id")
        if revision == 1:
            if (
                self.previous_snapshot_revision is not None
                or self.previous_snapshot_sha256 is not None
            ):
                raise PacketStorageModelError(
                    "first snapshot must not identify a predecessor."
                )
        else:
            if self.previous_snapshot_revision != revision - 1:
                raise PacketStorageModelError(
                    "snapshot predecessor revision must be exactly N-1."
                )
            _sha(
                self.previous_snapshot_sha256,
                "previous_snapshot_sha256",
            )
        _identifier(self.operation, "operation")
        if not isinstance(self.operation_provenance, Provenance):
            raise PacketStorageModelError(
                "operation_provenance must be Provenance."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketCurrentSnapshot:
    storage_schema_version: str
    packet_definition_id: str
    snapshot_revision: int
    snapshot_sha256: str

    def __post_init__(self) -> None:
        _schema(self.storage_schema_version)
        _identifier(self.packet_definition_id, "packet_definition_id")
        _positive(self.snapshot_revision, "snapshot_revision")
        _sha(self.snapshot_sha256, "snapshot_sha256")


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedPacketLibrary:
    definition: PacketDefinition
    versions: tuple[PacketVersion, ...]
    snapshot_revision: int
    snapshot_sha256: str
    current_packet_version_id: str | None
    head_packet_version_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.definition, PacketDefinition):
            raise PacketStorageModelError(
                "definition must be PacketDefinition."
            )
        if not self.versions or any(
            not isinstance(item, PacketVersion) for item in self.versions
        ):
            raise PacketStorageModelError(
                "versions must contain PacketVersion values."
            )
        _positive(self.snapshot_revision, "snapshot_revision")
        _sha(self.snapshot_sha256, "snapshot_sha256")
        if self.current_packet_version_id is not None:
            _identifier(
                self.current_packet_version_id,
                "current_packet_version_id",
            )
        _identifier(self.head_packet_version_id, "head_packet_version_id")

    @property
    def current_version(self) -> PacketVersion | None:
        if self.current_packet_version_id is None:
            return None
        return next(
            (
                item
                for item in self.versions
                if item.packet_version_id == self.current_packet_version_id
            ),
            None,
        )

    @property
    def head_version(self) -> PacketVersion:
        value = next(
            (
                item
                for item in self.versions
                if item.packet_version_id == self.head_packet_version_id
            ),
            None,
        )
        if value is None:
            raise PacketStorageModelError(
                "head_packet_version_id does not resolve."
            )
        return value


__all__ = [
    "LoadedPacketLibrary",
    "PACKET_LIBRARY_RECORD_KINDS",
    "PACKET_LIBRARY_STORAGE_SCHEMA",
    "PacketCurrentSnapshot",
    "PacketLibraryMarker",
    "PacketLibrarySnapshot",
    "PacketRecordRevision",
    "PacketRecordRevisionRef",
    "PacketStorageModelError",
]
