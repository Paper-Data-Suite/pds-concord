"""Deterministic canonical JSON and strict storage-envelope conversion."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Callable, Literal, TypeVar, cast

from pds_core.routing_models import module_work_ref_from_dict, module_work_ref_to_dict

from concord.model_conversion import record_from_dict, record_to_dict
from concord.record_registry import descriptor_for_kind
from concord.storage_errors import (
    ConcordStorageReadError,
    ConcordStorageValidationError,
)
from concord.storage_models import (
    ConcordCurrentSnapshot,
    ConcordRecordRevision,
    ConcordRecordRevisionRef,
    ConcordWorkMarker,
    ConcordWorkSnapshot,
    JsonValue,
)

T = TypeVar("T")


def canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise ConcordStorageValidationError(
            f"value is not canonical JSON: {error}"
        ) from error


def strict_json_loads(data: bytes) -> dict[str, Any]:
    if data.startswith(b"\xef\xbb\xbf"):
        raise ConcordStorageReadError(
            "canonical JSON must not contain a byte-order mark."
        )
    try:
        text = data.decode("utf-8", errors="strict")
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ConcordStorageReadError(f"invalid canonical JSON: {error}") from error
    if not isinstance(value, dict):
        raise ConcordStorageReadError("canonical JSON top level must be an object.")
    return value


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}.")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant {value}.")


def _mapping(value: object, keys: set[str], name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(k, str) for k in value):
        raise ConcordStorageValidationError(
            f"{name} must be an object with string keys."
        )
    actual = set(cast(Mapping[str, object], value))
    if actual != keys:
        raise ConcordStorageValidationError(
            f"{name} fields differ from the supported schema."
        )
    return cast(Mapping[str, object], value)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ConcordStorageValidationError(f"{name} must be a string.")
    return value


def _int(value: object, name: str) -> int:
    if type(value) is not int:
        raise ConcordStorageValidationError(f"{name} must be an integer.")
    return value


def marker_to_dict(value: ConcordWorkMarker) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "record_type": value.record_type,
        "work": module_work_ref_to_dict(value.work),
        "activity_id": value.activity_id,
        "native_record_contract_version": value.native_record_contract_version,
    }


def marker_from_dict(data: object) -> ConcordWorkMarker:
    m = _mapping(
        data,
        {
            "schema_version",
            "record_type",
            "work",
            "activity_id",
            "native_record_contract_version",
        },
        "work marker",
    )
    return ConcordWorkMarker(
        _string(m["schema_version"], "schema_version"),
        cast(Literal["concord_work"], _string(m["record_type"], "record_type")),
        module_work_ref_from_dict(m["work"]),
        _string(m["activity_id"], "activity_id"),
        _string(m["native_record_contract_version"], "native_record_contract_version"),
    )


def revision_to_dict(value: ConcordRecordRevision) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "record_type": value.record_type,
        "work": module_work_ref_to_dict(value.work),
        "record_kind": value.record_kind,
        "record_id": value.record_id,
        "record_revision": value.record_revision,
        "record_contract_version": value.record_contract_version,
        "body": value.body,
    }


def revision_from_dict(data: object) -> ConcordRecordRevision:
    m = _mapping(
        data,
        {
            "schema_version",
            "record_type",
            "work",
            "record_kind",
            "record_id",
            "record_revision",
            "record_contract_version",
            "body",
        },
        "record revision",
    )
    kind = _string(m["record_kind"], "record_kind")
    descriptor = descriptor_for_kind(kind)
    body = m["body"]
    if not isinstance(body, dict) or any(not isinstance(k, str) for k in body):
        raise ConcordStorageValidationError("body must be an object.")
    record = record_from_dict(kind, body)
    if record_to_dict(record) != body:
        raise ConcordStorageValidationError("record body does not round-trip exactly.")
    record_id = _string(m["record_id"], "record_id")
    if getattr(record, descriptor.identity_field) != record_id:
        raise ConcordStorageValidationError(
            "record body identity differs from envelope."
        )
    return ConcordRecordRevision(
        _string(m["schema_version"], "schema_version"),
        cast(
            Literal["concord_record_revision"],
            _string(m["record_type"], "record_type"),
        ),
        module_work_ref_from_dict(m["work"]),
        kind,
        record_id,
        _int(m["record_revision"], "record_revision"),
        _string(m["record_contract_version"], "record_contract_version"),
        cast(dict[str, JsonValue], body),
    )


def ref_to_dict(value: ConcordRecordRevisionRef) -> dict[str, object]:
    return {
        "record_kind": value.record_kind,
        "record_id": value.record_id,
        "record_revision": value.record_revision,
        "sha256": value.sha256,
    }


def ref_from_dict(data: object) -> ConcordRecordRevisionRef:
    m = _mapping(
        data,
        {"record_kind", "record_id", "record_revision", "sha256"},
        "record revision reference",
    )
    return ConcordRecordRevisionRef(
        _string(m["record_kind"], "record_kind"),
        _string(m["record_id"], "record_id"),
        _int(m["record_revision"], "record_revision"),
        _string(m["sha256"], "sha256"),
    )


def snapshot_to_dict(value: ConcordWorkSnapshot) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "record_type": value.record_type,
        "work": module_work_ref_to_dict(value.work),
        "snapshot_revision": value.snapshot_revision,
        "previous_snapshot_revision": value.previous_snapshot_revision,
        "previous_snapshot_sha256": value.previous_snapshot_sha256,
        "records": [ref_to_dict(r) for r in value.records],
    }


def snapshot_from_dict(data: object) -> ConcordWorkSnapshot:
    m = _mapping(
        data,
        {
            "schema_version",
            "record_type",
            "work",
            "snapshot_revision",
            "previous_snapshot_revision",
            "previous_snapshot_sha256",
            "records",
        },
        "work snapshot",
    )
    records = m["records"]
    if not isinstance(records, list):
        raise ConcordStorageValidationError("records must be an array.")
    prev_rev = m["previous_snapshot_revision"]
    prev_digest = m["previous_snapshot_sha256"]
    if prev_rev is not None:
        prev_rev = _int(prev_rev, "previous_snapshot_revision")
    if prev_digest is not None:
        prev_digest = _string(prev_digest, "previous_snapshot_sha256")
    return ConcordWorkSnapshot(
        _string(m["schema_version"], "schema_version"),
        cast(
            Literal["concord_work_snapshot"],
            _string(m["record_type"], "record_type"),
        ),
        module_work_ref_from_dict(m["work"]),
        _int(m["snapshot_revision"], "snapshot_revision"),
        prev_rev,
        prev_digest,
        tuple(ref_from_dict(r) for r in records),
    )


def current_to_dict(value: ConcordCurrentSnapshot) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "record_type": value.record_type,
        "work": module_work_ref_to_dict(value.work),
        "snapshot_revision": value.snapshot_revision,
        "snapshot_sha256": value.snapshot_sha256,
    }


def current_from_dict(data: object) -> ConcordCurrentSnapshot:
    m = _mapping(
        data,
        {
            "schema_version",
            "record_type",
            "work",
            "snapshot_revision",
            "snapshot_sha256",
        },
        "current snapshot",
    )
    return ConcordCurrentSnapshot(
        _string(m["schema_version"], "schema_version"),
        cast(
            Literal["concord_current_snapshot"],
            _string(m["record_type"], "record_type"),
        ),
        module_work_ref_from_dict(m["work"]),
        _int(m["snapshot_revision"], "snapshot_revision"),
        _string(m["snapshot_sha256"], "snapshot_sha256"),
    )


def serialize(value: object) -> bytes:
    converters: tuple[tuple[type[object], Callable[[Any], dict[str, object]]], ...] = (
        (ConcordWorkMarker, marker_to_dict),
        (ConcordRecordRevision, revision_to_dict),
        (ConcordWorkSnapshot, snapshot_to_dict),
        (ConcordCurrentSnapshot, current_to_dict),
    )
    for cls, converter in converters:
        if isinstance(value, cls):
            return canonical_json_bytes(converter(value))
    raise ConcordStorageValidationError(
        f"unsupported storage model {type(value).__name__}."
    )
