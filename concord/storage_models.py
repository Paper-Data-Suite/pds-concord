"""Versioned immutable metadata for canonical Concord storage."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal, TypeAlias

from pds_core.routing_models import ModuleWorkRef, validate_module_work_ref

from concord.record_registry import descriptor_for_kind
from concord.storage_errors import ConcordStorageValidationError

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)
CONCORD_STORAGE_SCHEMA_VERSION = "1"
CONCORD_NATIVE_RECORD_CONTRACT_VERSION = "1"
CONCORD_CATALOG_SCHEMA_VERSION = 1
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _work(value: object) -> ModuleWorkRef:
    if not isinstance(value, ModuleWorkRef):
        raise ConcordStorageValidationError("work must be a ModuleWorkRef.")
    try:
        result = validate_module_work_ref(value)
    except ValueError as error:
        raise ConcordStorageValidationError(str(error)) from error
    if result.module_id != "concord":
        raise ConcordStorageValidationError('work.module_id must be "concord".')
    return result


def _revision(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        raise ConcordStorageValidationError(f"{name} must be a positive integer.")
    return value


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ConcordStorageValidationError(
            f"{name} must be a lowercase SHA-256 digest."
        )
    return value


@dataclass(frozen=True, slots=True)
class ConcordWorkMarker:
    schema_version: str
    record_type: Literal["concord_work"]
    work: ModuleWorkRef
    activity_id: str
    native_record_contract_version: str

    def __post_init__(self) -> None:
        work = _work(self.work)
        if (
            self.schema_version != CONCORD_STORAGE_SCHEMA_VERSION
            or self.record_type != "concord_work"
        ):
            raise ConcordStorageValidationError(
                "unsupported Concord work marker schema."
            )
        if self.activity_id != work.work_id:
            raise ConcordStorageValidationError("activity_id must equal work.work_id.")
        if (
            self.native_record_contract_version
            != CONCORD_NATIVE_RECORD_CONTRACT_VERSION
        ):
            raise ConcordStorageValidationError(
                "unsupported native record contract version."
            )


@dataclass(frozen=True, slots=True)
class ConcordRecordRevision:
    schema_version: str
    record_type: Literal["concord_record_revision"]
    work: ModuleWorkRef
    record_kind: str
    record_id: str
    record_revision: int
    record_contract_version: str
    body: dict[str, JsonValue]

    def __post_init__(self) -> None:
        _work(self.work)
        descriptor_for_kind(self.record_kind)
        _revision(self.record_revision, "record_revision")
        if (
            self.schema_version != CONCORD_STORAGE_SCHEMA_VERSION
            or self.record_type != "concord_record_revision"
        ):
            raise ConcordStorageValidationError("unsupported record revision schema.")
        if self.record_contract_version != CONCORD_NATIVE_RECORD_CONTRACT_VERSION:
            raise ConcordStorageValidationError("unsupported record contract version.")
        if not isinstance(self.record_id, str) or not isinstance(self.body, dict):
            raise ConcordStorageValidationError(
                "record revision identity and body are invalid."
            )


@dataclass(frozen=True, slots=True, order=True)
class ConcordRecordRevisionRef:
    record_kind: str
    record_id: str
    record_revision: int
    sha256: str

    def __post_init__(self) -> None:
        descriptor_for_kind(self.record_kind)
        _revision(self.record_revision, "record_revision")
        _digest(self.sha256, "sha256")


@dataclass(frozen=True, slots=True)
class ConcordWorkSnapshot:
    schema_version: str
    record_type: Literal["concord_work_snapshot"]
    work: ModuleWorkRef
    snapshot_revision: int
    previous_snapshot_revision: int | None
    previous_snapshot_sha256: str | None
    records: tuple[ConcordRecordRevisionRef, ...]

    def __post_init__(self) -> None:
        _work(self.work)
        _revision(self.snapshot_revision, "snapshot_revision")
        if (
            self.schema_version != CONCORD_STORAGE_SCHEMA_VERSION
            or self.record_type != "concord_work_snapshot"
        ):
            raise ConcordStorageValidationError("unsupported work snapshot schema.")
        if self.snapshot_revision == 1:
            if (
                self.previous_snapshot_revision is not None
                or self.previous_snapshot_sha256 is not None
            ):
                raise ConcordStorageValidationError(
                    "initial snapshot must not have a predecessor."
                )
        else:
            if self.previous_snapshot_revision != self.snapshot_revision - 1:
                raise ConcordStorageValidationError(
                    "snapshot predecessor revision must be contiguous."
                )
            _digest(self.previous_snapshot_sha256, "previous_snapshot_sha256")
        if (
            type(self.records) is not tuple
            or tuple(sorted(self.records, key=lambda r: (r.record_kind, r.record_id)))
            != self.records
        ):
            raise ConcordStorageValidationError(
                "snapshot records must be deterministically ordered."
            )
        identities = [(r.record_kind, r.record_id) for r in self.records]
        if len(identities) != len(set(identities)):
            raise ConcordStorageValidationError(
                "snapshot record identities must be unique."
            )


@dataclass(frozen=True, slots=True)
class ConcordCurrentSnapshot:
    schema_version: str
    record_type: Literal["concord_current_snapshot"]
    work: ModuleWorkRef
    snapshot_revision: int
    snapshot_sha256: str

    def __post_init__(self) -> None:
        _work(self.work)
        _revision(self.snapshot_revision, "snapshot_revision")
        _digest(self.snapshot_sha256, "snapshot_sha256")
        if (
            self.schema_version != CONCORD_STORAGE_SCHEMA_VERSION
            or self.record_type != "concord_current_snapshot"
        ):
            raise ConcordStorageValidationError("unsupported current snapshot schema.")


@dataclass(frozen=True, slots=True)
class ConcordStorageCommitResult:
    work: ModuleWorkRef
    snapshot_revision: int
    snapshot_sha256: str
    created_record_revisions: tuple[ConcordRecordRevisionRef, ...]
    no_op: bool = False


@dataclass(frozen=True, slots=True)
class ConcordLoadedRecordGraph:
    graph: Any
    snapshot_revision: int
    snapshot_sha256: str
