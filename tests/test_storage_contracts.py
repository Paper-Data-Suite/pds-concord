from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef

from concord.storage_errors import (
    ConcordStorageReadError,
    ConcordStorageValidationError,
)
from concord.storage_models import (
    CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
    CONCORD_STORAGE_SCHEMA_VERSION,
    ConcordCurrentSnapshot,
    ConcordRecordRevisionRef,
    ConcordWorkMarker,
    ConcordWorkSnapshot,
)
from concord.storage_paths import (
    catalog_path,
    current_snapshot_path,
    record_revision_path,
    snapshot_path,
    work_marker_path,
)
from concord.storage_serialization import (
    canonical_json_bytes,
    marker_from_dict,
    serialize,
    strict_json_loads,
)


@pytest.fixture
def work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord", class_id="class-test", work_id="activity-test"
    )


def test_canonical_paths_are_exact_and_work_scoped(
    tmp_path: Path, work: ModuleWorkRef
) -> None:
    base = (
        tmp_path
        / "classes"
        / "class-test"
        / "modules"
        / "concord"
        / "work"
        / "activity-test"
        / "state"
    )
    assert work_marker_path(tmp_path, work) == base / "work.json"
    assert current_snapshot_path(tmp_path, work) == base / "current.json"
    assert snapshot_path(tmp_path, work, 2) == base / "snapshots" / "2.json"
    assert record_revision_path(tmp_path, work, "session", "session-1", 3) == (
        base / "records" / "session" / "session-1" / "revisions" / "3.json"
    )
    assert catalog_path(tmp_path, work) == base / "derived" / "catalog.sqlite"


@pytest.mark.parametrize("revision", [0, -1, True, 1.0, "1"])
def test_paths_reject_non_positive_integer_revisions(
    tmp_path: Path, work: ModuleWorkRef, revision: object
) -> None:
    with pytest.raises(ConcordStorageValidationError):
        snapshot_path(tmp_path, work, revision)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "record_id",
    ["", "../escape", "a/b", "a\\b", " C", "C ", "C:\\escape", "\x00"],
)
def test_paths_reject_unsafe_record_identifiers(
    tmp_path: Path, work: ModuleWorkRef, record_id: str
) -> None:
    with pytest.raises(ConcordStorageValidationError):
        record_revision_path(tmp_path, work, "session", record_id, 1)


def test_marker_serialization_is_deterministic(work: ModuleWorkRef) -> None:
    marker = ConcordWorkMarker(
        CONCORD_STORAGE_SCHEMA_VERSION,
        "concord_work",
        work,
        work.work_id,
        CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
    )
    data = serialize(marker)
    assert data.endswith(b"\n") and not data.endswith(b"\n\n")
    assert serialize(marker) == data
    assert marker_from_dict(strict_json_loads(data)) == marker


@pytest.mark.parametrize(
    "data",
    [
        b'{"a": 1, "a": 2}\n',
        b"\xef\xbb\xbf{}\n",
        b'{"value": NaN}\n',
        b"[]\n",
        b"\xff",
    ],
)
def test_strict_json_rejects_noncanonical_inputs(data: bytes) -> None:
    with pytest.raises(ConcordStorageReadError):
        strict_json_loads(data)


def test_snapshot_references_must_be_sorted_unique_and_valid(
    work: ModuleWorkRef,
) -> None:
    first = ConcordRecordRevisionRef("session", "session-2", 1, "a" * 64)
    second = ConcordRecordRevisionRef("activity", "activity-test", 1, "b" * 64)
    with pytest.raises(ConcordStorageValidationError):
        ConcordWorkSnapshot(
            CONCORD_STORAGE_SCHEMA_VERSION,
            "concord_work_snapshot",
            work,
            1,
            None,
            None,
            (first, second),
        )
    with pytest.raises(ConcordStorageValidationError):
        ConcordRecordRevisionRef("session", "session-1", 1, "A" * 64)


def test_current_pointer_rejects_boolean_revision(work: ModuleWorkRef) -> None:
    with pytest.raises(ConcordStorageValidationError):
        ConcordCurrentSnapshot(
            CONCORD_STORAGE_SCHEMA_VERSION,
            "concord_current_snapshot",
            work,
            True,
            "a" * 64,
        )


def test_canonical_json_rejects_non_finite_numbers() -> None:
    with pytest.raises(ConcordStorageValidationError):
        canonical_json_bytes({"value": float("inf")})
