from __future__ import annotations

import csv
import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_csv import (
    GROUPING_SIGNAL_CSV_CONTRACT_NAME,
    GroupingSignalCsvError,
    grouping_signal_csv_to_signal_set,
    grouping_signal_set_from_csv,
    grouping_signal_set_to_csv_bytes,
    parse_grouping_signal_csv,
)
from pds_core.grouping_signal_diagnostics import (
    GROUPING_SIGNAL_DIAGNOSTIC_CODES,
    diagnose_grouping_signal,
)
from pds_core.grouping_signal_storage import (
    GROUPING_SIGNAL_DIGEST_ALGORITHM,
    GroupingSignalConflictError,
    calculate_grouping_signal_digest,
    list_grouping_signal_ids,
    load_grouping_signal,
    write_grouping_signal,
)
from pds_core.grouping_signals import (
    GROUPING_SIGNAL_CONTRACT_NAME,
    GROUPING_SIGNAL_RECORD_TYPE,
    GROUPING_SIGNAL_SCHEMA_VERSION,
    GroupingSignalSet,
    grouping_signal_set_from_json,
    grouping_signal_set_to_json_bytes,
)
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from scripts.verify_core_grouping_fixtures import (
    EXPECTED_ARCHIVE_FILENAME,
    EXPECTED_ARCHIVE_SHA256,
    EXPECTED_FILE_DIGESTS,
    VENDORED_FIXTURE_ROOT,
    verify_vendored_grouping_fixtures,
)
from scripts.verify_release_compatibility import validate_sibling_import_isolation

FIXTURE_ROOT = VENDORED_FIXTURE_ROOT


def _fixture(name: str) -> bytes:
    return (FIXTURE_ROOT / name).read_bytes()


def _signal(name: str) -> GroupingSignalSet:
    return grouping_signal_set_from_json(_fixture(name))


def _fixture_roster_rows(relative: str) -> tuple[dict[str, str], ...]:
    path = FIXTURE_ROOT / relative
    with path.open("r", encoding="utf-8", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def _write_fixture_class(workspace: Path, relative: str) -> None:
    rows = _fixture_roster_rows(relative)
    assert rows
    class_id = rows[0]["class_id"]
    assert all(row["class_id"] == class_id for row in rows)
    write_class_metadata_for_class(
        workspace,
        create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 19, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        workspace,
        create_roster(
            class_id,
            tuple(
                {
                    "student_id": row["student_id"],
                    "last_name": row["last_name"],
                    "first_name": row["first_name"],
                    "period": row["period"],
                }
                for row in rows
            ),
        ),
    )


def _workspace_with_fixture_rosters(tmp_path: Path) -> Path:
    workspace = ensure_workspace_root(tmp_path / "workspace")
    _write_fixture_class(workspace, "classes/english10_p2/roster.csv")
    _write_fixture_class(workspace, "classes/english10_p4/roster.csv")
    return workspace


def _file_digests(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_released_fixture_payload_is_byte_exact_and_synthetic() -> None:
    verify_vendored_grouping_fixtures()
    assert EXPECTED_ARCHIVE_FILENAME == "pds-core-0.6.1-grouping-signal-fixtures.zip"
    assert EXPECTED_ARCHIVE_SHA256 == (
        "d8376292dd68ada48d35ab98233381de0008d41f868844e27e8507bf0d0f8f8d"
    )
    assert set(EXPECTED_FILE_DIGESTS) == {
        "classes/english10_p2/roster.csv",
        "classes/english10_p4/roster.csv",
        "module_multi_dimension.json",
        "module_selected_dimension_projection.csv",
        "teacher_complete.csv",
        "teacher_complete.json",
    }
    assert all(b"\r" not in _fixture(path) for path in EXPECTED_FILE_DIGESTS)


def test_core_public_grouping_contract_and_teacher_fixture_are_exact() -> None:
    assert GROUPING_SIGNAL_CONTRACT_NAME == "grouping_signal_set_v1"
    assert GROUPING_SIGNAL_SCHEMA_VERSION == "1"
    assert GROUPING_SIGNAL_RECORD_TYPE == "grouping_signal_set"
    assert GROUPING_SIGNAL_CSV_CONTRACT_NAME == "grouping_signal_csv_v1"
    assert GROUPING_SIGNAL_DIGEST_ALGORITHM == "sha256"
    assert GROUPING_SIGNAL_DIAGNOSTIC_CODES == frozenset(
        {
            "class_mismatch",
            "wrong_class_student",
            "unknown_student",
            "missing_student_signal",
        }
    )

    raw = _fixture("teacher_complete.json")
    signal = grouping_signal_set_from_json(raw)
    assert grouping_signal_set_to_json_bytes(signal) == raw
    assert signal.signal_set_id == "teacher_complete_001"
    assert signal.class_id == "english10_p2"
    assert signal.source.kind == "teacher_authored"
    assert signal.source.module_id is None
    assert tuple(item.dimension_id for item in signal.dimensions) == (
        "discussion_support",
    )
    assert signal.dimensions[0].band_count == 3
    assert tuple(item.band for item in signal.student_bands) == (1, 3, 2)


def test_complete_csv_round_trip_uses_core_without_identity_change() -> None:
    raw_csv = _fixture("teacher_complete.csv")
    signal = _signal("teacher_complete.json")
    document = parse_grouping_signal_csv(raw_csv)
    assert document.representation_scope == "complete_signal"
    assert document.requires_new_identity is False
    assert grouping_signal_set_from_csv(raw_csv) == signal
    assert grouping_signal_set_to_csv_bytes(signal, "discussion_support") == raw_csv


def test_multidimension_projection_requires_explicit_new_identity() -> None:
    source = _signal("module_multi_dimension.json")
    assert source.source.kind == "module_generated"
    assert source.source.module_id == "synthetic_module"
    assert tuple(item.dimension_id for item in source.dimensions) == (
        "reading_analysis",
        "writing_claim_evidence",
    )
    assert grouping_signal_set_to_csv_bytes(source, "reading_analysis") == _fixture(
        "module_selected_dimension_projection.csv"
    )

    document = parse_grouping_signal_csv(
        _fixture("module_selected_dimension_projection.csv")
    )
    assert document.representation_scope == "dimension_projection"
    assert document.requires_new_identity is True
    with pytest.raises(GroupingSignalCsvError, match="requires a new signal_set_id"):
        grouping_signal_csv_to_signal_set(document)

    projected = grouping_signal_csv_to_signal_set(
        document,
        new_signal_set_id="concord_projection_test_001",
        new_created_at=datetime(2026, 9, 2, 12, 0, tzinfo=timezone.utc),
    )
    assert projected.signal_set_id == "concord_projection_test_001"
    assert projected.signal_set_id != source.signal_set_id
    assert tuple(item.dimension_id for item in projected.dimensions) == (
        "reading_analysis",
    )


def test_core_storage_is_immutable_exact_and_digest_bound(tmp_path: Path) -> None:
    workspace = ensure_workspace_root(tmp_path / "workspace")
    signal = _signal("teacher_complete.json")

    first = write_grouping_signal(workspace, signal)
    assert first.disposition == "created"
    assert first.stored.signal == signal
    assert first.stored.digest_algorithm == "sha256"
    assert first.stored.digest == calculate_grouping_signal_digest(signal)

    replay = write_grouping_signal(workspace, signal)
    assert replay.disposition == "existing"
    assert replay.stored == first.stored
    assert list_grouping_signal_ids(workspace, signal.class_id) == (
        signal.signal_set_id,
    )
    assert load_grouping_signal(
        workspace, signal.class_id, signal.signal_set_id
    ) == first.stored

    changed_entries = list(signal.student_bands)
    changed_entries[0] = replace(changed_entries[0], band=2)
    conflicting = replace(signal, student_bands=tuple(changed_entries))
    with pytest.raises(GroupingSignalConflictError):
        write_grouping_signal(workspace, conflicting)

    assert not (
        workspace
        / "classes"
        / signal.class_id
        / "modules"
        / "concord"
    ).exists()


def test_source_snapshot_digest_is_not_the_core_signal_digest() -> None:
    signal = _signal("module_multi_dimension.json")
    assert signal.source.snapshot_digest == "b" * 64
    core_digest = calculate_grouping_signal_digest(signal)
    assert core_digest != signal.source.snapshot_digest
    assert len(core_digest) == 64


def test_core_diagnostics_preserve_wrong_unknown_and_missing_identity(
    tmp_path: Path,
) -> None:
    workspace = _workspace_with_fixture_rosters(tmp_path)
    signal = _signal("module_multi_dimension.json")
    before = _file_digests(workspace)
    report = diagnose_grouping_signal(workspace, signal)
    after = _file_digests(workspace)
    assert after == before

    findings = {
        (item.code, item.student_id, item.dimension_id): item
        for item in report.findings
    }
    wrong = findings[("wrong_class_student", "student_004", "reading_analysis")]
    assert wrong.other_class_ids == ("english10_p4",)
    assert ("unknown_student", "student_999", "reading_analysis") in findings
    assert ("missing_student_signal", "student_002", "reading_analysis") in findings
    assert ("missing_student_signal", "student_003", "reading_analysis") in findings
    assert (
        "missing_student_signal",
        "student_003",
        "writing_claim_evidence",
    ) in findings

    by_dimension = {item.dimension_id: item for item in report.dimensions}
    reading = by_dimension["reading_analysis"]
    assert reading.matched_student_count == 1
    assert reading.wrong_class_student_count == 1
    assert reading.unknown_student_count == 1
    assert reading.missing_student_count == 2
    assert reading.band_counts == ((1, 0), (2, 1), (3, 0), (4, 0))


def test_diagnostics_use_exact_student_id_not_name_or_case_guessing(
    tmp_path: Path,
) -> None:
    workspace = _workspace_with_fixture_rosters(tmp_path)
    signal = _signal("teacher_complete.json")
    changed_entries = list(signal.student_bands)
    changed_entries[0] = replace(changed_entries[0], student_id="Student_001")
    changed = replace(
        signal,
        signal_set_id="case_sensitive_signal_001",
        student_bands=tuple(changed_entries),
    )
    report = diagnose_grouping_signal(workspace, changed)
    keys = {(item.code, item.student_id) for item in report.findings}
    assert ("unknown_student", "Student_001") in keys
    assert ("missing_student_signal", "student_001") in keys


def test_explicit_target_class_mismatch_is_reported_not_repaired(
    tmp_path: Path,
) -> None:
    workspace = _workspace_with_fixture_rosters(tmp_path)
    report = diagnose_grouping_signal(
        workspace,
        _signal("teacher_complete.json"),
        expected_class_id="english10_p4",
    )
    assert any(item.code == "class_mismatch" for item in report.findings)
    assert report.signal_class_id == "english10_p2"
    assert report.target_class_id == "english10_p4"


def test_concord_production_has_no_sibling_import_dependency() -> None:
    validate_sibling_import_isolation()
