"""Strict canonical serialization for reusable Concord Packet contracts."""

from __future__ import annotations

from typing import TypeAlias, TypeVar

from concord.models import PacketDefinition, PacketVersion
from concord.template_serialization import TemplateSerializationError
from concord.template_serialization import (
    canonical_json_bytes as _canonical_json_bytes,
)
from concord.template_serialization import (
    dataclass_from_dict as _dataclass_from_dict,
)
from concord.template_serialization import (
    dataclass_to_dict as _dataclass_to_dict,
)
from concord.template_serialization import (
    strict_json_loads as _strict_json_loads,
)

PacketRecord: TypeAlias = PacketDefinition | PacketVersion
T = TypeVar("T")


class PacketSerializationError(ValueError):
    """Reusable Packet data is not strict canonical JSON."""


def canonical_json_bytes(value: object) -> bytes:
    """Serialize one JSON-compatible value deterministically."""
    try:
        return _canonical_json_bytes(value)
    except TemplateSerializationError as error:
        raise PacketSerializationError(str(error)) from error


def strict_json_loads(data: bytes, *, description: str = "JSON") -> object:
    """Parse strict UTF-8 JSON and reject duplicates/non-JSON constants."""
    try:
        return _strict_json_loads(data, description=description)
    except TemplateSerializationError as error:
        raise PacketSerializationError(str(error)) from error


def dataclass_to_dict(value: object) -> dict[str, object]:
    """Convert one typed dataclass instance to canonical JSON-native values."""
    try:
        return _dataclass_to_dict(value)
    except TemplateSerializationError as error:
        raise PacketSerializationError(str(error)) from error


def dataclass_from_dict(cls: type[T], value: object) -> T:
    """Strictly construct one typed dataclass from a JSON object."""
    try:
        return _dataclass_from_dict(cls, value)
    except TemplateSerializationError as error:
        raise PacketSerializationError(str(error)) from error


def packet_to_dict(record: PacketRecord) -> dict[str, object]:
    """Return the exact mapping for one reusable Packet record."""
    if not isinstance(record, (PacketDefinition, PacketVersion)):
        raise PacketSerializationError(
            "record must be PacketDefinition or PacketVersion."
        )
    return dataclass_to_dict(record)


def packet_from_dict(record_kind: str, value: object) -> PacketRecord:
    """Strictly parse one reusable Packet record body."""
    if record_kind == "packet_definition":
        return dataclass_from_dict(PacketDefinition, value)
    if record_kind == "packet_version":
        return dataclass_from_dict(PacketVersion, value)
    raise PacketSerializationError(
        f"unsupported reusable Packet record kind {record_kind!r}."
    )


def packet_to_json_bytes(record: PacketRecord) -> bytes:
    """Return deterministic canonical Packet body bytes."""
    return canonical_json_bytes(packet_to_dict(record))


def packet_from_json_bytes(
    record_kind: str,
    data: bytes,
    *,
    description: str | None = None,
) -> PacketRecord:
    """Parse canonical Packet body bytes and reject noncanonical encoding."""
    label = description or f"{record_kind} JSON"
    value = strict_json_loads(data, description=label)
    record = packet_from_dict(record_kind, value)
    if packet_to_json_bytes(record) != data:
        raise PacketSerializationError(f"{label} is not canonical.")
    return record


__all__ = [
    "PacketRecord",
    "PacketSerializationError",
    "canonical_json_bytes",
    "dataclass_from_dict",
    "dataclass_to_dict",
    "packet_from_dict",
    "packet_from_json_bytes",
    "packet_to_dict",
    "packet_to_json_bytes",
    "strict_json_loads",
]
