from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.grouping_signal_csv import grouping_signal_set_to_csv_bytes
from pds_core.grouping_signal_storage import (
    calculate_grouping_signal_digest,
    list_grouping_signal_ids,
)
from pds_core.grouping_signals import (
    GroupingSignalSet,
    GroupingSignalStudentBand,
    grouping_signal_set_from_json,
)
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.workflows import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
    ImportGroupingSignalCsvRequest,
    import_grouping_signal_csv,
    prepare_grouping_signal_csv_import,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "core_grouping_signals" / "v1"


def _fixture(name: str) -> bytes:
    return (FIXTURE_ROOT / name).read_bytes()


def _signal(name: str) -> GroupingSignalSet:
    return grouping_signal_set_from_json(_fixture(name))


def _write_class(
    workspace: Path,
    class_id: str,
    students: tuple[tuple[str, str, str, str], ...],
) -> None:
    write_class_metadata_for_class(
        workspace,
        create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        workspace,
        create_roster(
            class_id,
            tuple(
                {
                    "student_id": student_id,
                    "last_name": last_name,
                    "first_name": first_name,
                    "period": period,
                }
                for student_id, last_name, first_name, period in students
            ),
        ),
    )


def _workspace(tmp_path: Path) -> Path:
    workspace = ensure_workspace_root(tmp_path / "workspace")
    _write_class(
        workspace,
        "english10_p2",
        (
            ("student_001", "Sample", "Ava", "2"),
            ("student_002", "Example", "Ben", "2"),
            ("student_003", "Demo", "Cora", "2"),
        ),
    )
    _write_class(
        workspace,
        "english10_p4",
        (("student_004", "Other", "Drew", "4"),),
    )
    return workspace


def _csv_path(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def _signal_storage_state(workspace: Path, class_id: str) -> tuple[str, ...]:
    return list_grouping_signal_ids(workspace, class_id)


def _replace_csv_line(data: bytes, old: bytes, new: bytes) -> bytes:
    assert data.count(old) == 1
    return data.replace(old, new, 1)


def _clean_multidimension_signal() -> GroupingSignalSet:
    source = _signal("module_multi_dimension.json")
    entries = (
        GroupingSignalStudentBand(
            student_id="student_001",
            dimension_id="reading_analysis",
            band=2,
        ),
        GroupingSignalStudentBand(
            student_id="student_002",
            dimension_id="reading_analysis",
            band=4,
        ),
        GroupingSignalStudentBand(
            student_id="student_003",
            dimension_id="reading_analysis",
            band=1,
        ),
        GroupingSignalStudentBand(
            student_id="student_001",
            dimension_id="writing_claim_evidence",
            band=3,
        ),
        GroupingSignalStudentBand(
            student_id="student_002",
            dimension_id="writing_claim_evidence",
            band=1,
        ),
        GroupingSignalStudentBand(
            student_id="student_003",
            dimension_id="writing_claim_evidence",
            band=2,
        ),
    )
    return replace(
        source,
        signal_set_id="module_clean_001",
        student_bands=entries,
    )


def test_prepare_complete_signal_is_read_only_and_preserves_identity(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    csv_path = _csv_path(tmp_path, "teacher.csv", _fixture("teacher_complete.csv"))

    preview = prepare_grouping_signal_csv_import(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=csv_path,
        ),
        workspace_root=workspace,
    )

    assert preview.representation_scope == "complete_signal"
    assert preview.signal == _signal("teacher_complete.json")
    assert preview.signal.signal_set_id == "teacher_complete_001"
    assert preview.digest == calculate_grouping_signal_digest(preview.signal)
    assert preview.dimension.dimension_id == "discussion_support"
    assert preview.diagnostics.is_clean
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_complete_signal_rejects_projection_identity_overrides(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    csv_path = _csv_path(tmp_path, "teacher.csv", _fixture("teacher_complete.csv"))

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="complete_signal.*does not accept",
    ):
        prepare_grouping_signal_csv_import(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
                new_signal_set_id="replacement_001",
                new_created_at=datetime(2026, 8, 20, tzinfo=timezone.utc),
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_complete_import_is_immutable_and_idempotent(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    csv_path = _csv_path(tmp_path, "teacher.csv", _fixture("teacher_complete.csv"))
    request = ImportGroupingSignalCsvRequest(
        class_id="english10_p2",
        csv_path=csv_path,
    )

    first = import_grouping_signal_csv(request, workspace_root=workspace)
    second = import_grouping_signal_csv(request, workspace_root=workspace)

    assert first.disposition == "created"
    assert second.disposition == "existing"
    assert first.stored == second.stored
    assert first.stored.signal == _signal("teacher_complete.json")
    assert first.stored.digest == first.preview.digest
    assert _signal_storage_state(workspace, "english10_p2") == (
        "teacher_complete_001",
    )
    assert not (
        workspace / "classes" / "english10_p2" / "modules" / "concord"
    ).exists()


@pytest.mark.parametrize(
    ("old", "new", "message"),
    (
        (b"student_id,band", b"student_id,value", "header"),
        (b"student_003,2", b"student_003,9", "band"),
        (
            b"student_003,2\n",
            b"student_002,2\n",
            "duplicate student_id",
        ),
    ),
)
def test_structurally_invalid_csv_never_writes(
    tmp_path: Path,
    old: bytes,
    new: bytes,
    message: str,
) -> None:
    workspace = _workspace(tmp_path)
    invalid = _replace_csv_line(_fixture("teacher_complete.csv"), old, new)
    csv_path = _csv_path(tmp_path, "invalid.csv", invalid)

    with pytest.raises(ConcordWorkflowValidationError, match=message):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_import_rejects_wrong_requested_class_before_write(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    csv_path = _csv_path(tmp_path, "teacher.csv", _fixture("teacher_complete.csv"))

    with pytest.raises(ConcordWorkflowValidationError, match="class_mismatch"):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p4",
                csv_path=csv_path,
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()
    assert _signal_storage_state(workspace, "english10_p4") == ()


@pytest.mark.parametrize(
    ("student_id", "code"),
    (
        ("student_004", "wrong_class_student"),
        ("student_999", "unknown_student"),
    ),
)
def test_import_rejects_non_target_students_without_write(
    tmp_path: Path,
    student_id: str,
    code: str,
) -> None:
    workspace = _workspace(tmp_path)
    candidate = _replace_csv_line(
        _fixture("teacher_complete.csv"),
        b"student_003,2",
        f"{student_id},2".encode(),
    )
    candidate = _replace_csv_line(
        candidate,
        b"signal_set_id=teacher_complete_001",
        f"signal_set_id={code}_001".encode(),
    )
    csv_path = _csv_path(tmp_path, f"{code}.csv", candidate)

    with pytest.raises(ConcordWorkflowValidationError, match=code):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_missing_only_partial_coverage_is_visible_and_importable(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    partial = _replace_csv_line(
        _fixture("teacher_complete.csv"),
        b"signal_set_id=teacher_complete_001",
        b"signal_set_id=teacher_partial_001",
    )
    partial = partial.replace(b"student_003,2\n", b"")
    csv_path = _csv_path(tmp_path, "partial.csv", partial)

    preview = prepare_grouping_signal_csv_import(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=csv_path,
        ),
        workspace_root=workspace,
    )
    assert preview.diagnostics.has_errors is False
    assert preview.diagnostics.has_warnings is True
    missing = tuple(
        finding.student_id
        for finding in preview.diagnostics.findings
        if finding.code == "missing_student_signal"
    )
    assert missing == ("student_003",)

    result = import_grouping_signal_csv(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=csv_path,
        ),
        workspace_root=workspace,
    )
    assert result.disposition == "created"
    assert result.stored.signal.signal_set_id == "teacher_partial_001"


def test_projection_requires_new_identity_and_time_as_a_pair(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    source = _clean_multidimension_signal()
    projection = grouping_signal_set_to_csv_bytes(source, "reading_analysis")
    csv_path = _csv_path(tmp_path, "projection.csv", projection)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="requires both",
    ):
        prepare_grouping_signal_csv_import(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
            ),
            workspace_root=workspace,
        )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="requires both",
    ):
        prepare_grouping_signal_csv_import(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
                new_signal_set_id="projected_001",
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_projection_import_uses_explicit_new_identity_and_preserves_source(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    source = _clean_multidimension_signal()
    projection = grouping_signal_set_to_csv_bytes(source, "reading_analysis")
    csv_path = _csv_path(tmp_path, "projection.csv", projection)
    created_at = datetime(2026, 8, 20, 21, 15, tzinfo=timezone.utc)

    result = import_grouping_signal_csv(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=csv_path,
            new_signal_set_id="projected_001",
            new_created_at=created_at,
        ),
        workspace_root=workspace,
    )

    stored = result.stored.signal
    assert result.disposition == "created"
    assert result.preview.representation_scope == "dimension_projection"
    assert stored.signal_set_id == "projected_001"
    assert stored.created_at == created_at
    assert tuple(item.dimension_id for item in stored.dimensions) == (
        "reading_analysis",
    )
    assert stored.source == source.source
    assert stored.source.module_id == "synthetic_module"


def test_projection_cannot_reuse_source_signal_identity(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    source = _clean_multidimension_signal()
    projection = grouping_signal_set_to_csv_bytes(source, "reading_analysis")
    csv_path = _csv_path(tmp_path, "projection.csv", projection)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must differ",
    ):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
                new_signal_set_id=source.signal_set_id,
                new_created_at=datetime(
                    2026,
                    8,
                    20,
                    21,
                    15,
                    tzinfo=timezone.utc,
                ),
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_immutable_identity_conflict_does_not_overwrite(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    original_path = _csv_path(
        tmp_path,
        "original.csv",
        _fixture("teacher_complete.csv"),
    )
    original = import_grouping_signal_csv(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=original_path,
        ),
        workspace_root=workspace,
    )

    changed = _replace_csv_line(
        _fixture("teacher_complete.csv"),
        b"student_001,1",
        b"student_001,2",
    )
    changed_path = _csv_path(tmp_path, "changed.csv", changed)
    with pytest.raises(ConcordWorkflowConflictError, match="identity conflict"):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=changed_path,
            ),
            workspace_root=workspace,
        )

    assert _signal_storage_state(workspace, "english10_p2") == (
        "teacher_complete_001",
    )
    replay = import_grouping_signal_csv(
        ImportGroupingSignalCsvRequest(
            class_id="english10_p2",
            csv_path=original_path,
        ),
        workspace_root=workspace,
    )
    assert replay.disposition == "existing"
    assert replay.stored == original.stored


def test_missing_or_nonregular_import_path_fails_without_write(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)

    with pytest.raises(ConcordWorkflowNotFoundError, match="not available"):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=tmp_path / "missing.csv",
            ),
            workspace_root=workspace,
        )

    directory = tmp_path / "directory.csv"
    directory.mkdir()
    with pytest.raises(ConcordWorkflowValidationError, match="regular file"):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=directory,
            ),
            workspace_root=workspace,
        )
    assert _signal_storage_state(workspace, "english10_p2") == ()


def test_import_fails_if_valid_candidate_changes_after_review(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    csv_path = _csv_path(
        tmp_path,
        "reviewed.csv",
        _fixture("teacher_complete.csv"),
    )
    request = ImportGroupingSignalCsvRequest(
        class_id="english10_p2",
        csv_path=csv_path,
    )
    preview = prepare_grouping_signal_csv_import(
        request,
        workspace_root=workspace,
    )

    changed = _replace_csv_line(
        _fixture("teacher_complete.csv"),
        b"student_001,1",
        b"student_001,2",
    )
    csv_path.write_bytes(changed)

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="changed since preview",
    ):
        import_grouping_signal_csv(
            ImportGroupingSignalCsvRequest(
                class_id="english10_p2",
                csv_path=csv_path,
                expected_signal_digest=preview.digest,
            ),
            workspace_root=workspace,
        )

    assert _signal_storage_state(workspace, "english10_p2") == ()
