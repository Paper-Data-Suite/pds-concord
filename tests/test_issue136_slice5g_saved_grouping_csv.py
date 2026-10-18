"""#136 Slice 5G: optional private CSV roundtrip and direct CLI guard tests."""

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
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.class_group_arrangement_storage import (
    ArrangementConflictError,
    create_arrangement,
    list_current_arrangements,
    load_current_arrangement,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    SavedArrangementRevision,
)
from concord.cli_app.main import main
from concord.cli_app.parser import build_parser
from concord.group_plan_arrangement_csv import ArrangementCsvValidationError
from concord.workflows.class_group_arrangement_csv import (
    CsvExportRequest,
    CsvImportRequest,
    export_csv_grouping,
    import_csv_grouping,
    prepare_csv_export,
    prepare_csv_import,
)
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import WorkflowActor

YEAR = "2026-2027"
CLASS = "class-csv-synthetic"
TEACHER = WorkflowActor(actor_id="teacher-synthetic")
ROSTER = tuple(f"student-{index:02}" for index in range(1, 30))


def _roster(ids: tuple[str, ...]) -> object:
    return create_roster(
        CLASS,
        tuple(
            {
                "student_id": sid,
                "first_name": "Synthetic",
                "last_name": f"Student-{index}",
                "period": "1",
            }
            for index, sid in enumerate(ids, 1)
        ),
    )


def _setup(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "pds")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS,
            YEAR,
            created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(root, _roster(ROSTER))  # type: ignore[arg-type]
    return root


def _first(*, missing: tuple[str, ...] = ()) -> SavedArrangementRevision:
    return SavedArrangementRevision(
        arrangement_id="source-six-tables",
        class_id=CLASS,
        school_year=YEAR,
        revision=1,
        name="Six Tables - Teacher Labels",
        owner_actor_id=TEACHER.actor_id,
        created_by_actor_id=TEACHER.actor_id,
        created_at="2026-10-18T15:00:00-04:00",
        groups=tuple(
            SavedArrangementGroup(
                key=f"table-{number}",
                label=f"Table {number} - Friendly",
                description="Synthetic optional description",
                student_ids=tuple(
                    sid
                    for index, sid in enumerate(ROSTER)
                    if index % 6 == number - 1 and sid not in missing
                ),
            )
            for number in range(1, 7)
        ),
        roster_student_ids=ROSTER,
        unresolved_student_ids=missing,
    )


def _export(saved: object) -> CsvExportRequest:
    return CsvExportRequest(
        class_id=CLASS,
        arrangement_id="source-six-tables",
        expected_revision=getattr(saved, "revision").revision,
        expected_sha256=getattr(saved, "sha256"),
        actor=TEACHER,
    )


def _import(path: Path, **changes: object) -> CsvImportRequest:
    return replace(
        CsvImportRequest(
            class_id=CLASS,
            arrangement_id="csv-imported-six-tables",
            name="Imported Six Tables",
            csv_path=path,
            actor=TEACHER,
        ),
        **changes,
    )


def test_six_groups_29_students_roundtrip_and_no_operational_copy(
    tmp_path: Path,
) -> None:
    root = _setup(tmp_path)
    saved = create_arrangement(root, _first(), actor_id=TEACHER.actor_id)
    request = _export(saved)
    preview = prepare_csv_export(request, workspace_root=root)
    assert preview.group_count == 6
    assert preview.assigned_count == 29
    assert preview.omitted_empty_group_count == 0
    assert preview.omitted_unresolved_count == 0
    csv_path = tmp_path / "grouping.csv"
    assert not csv_path.exists()
    export_csv_grouping(
        request,
        output_path=csv_path,
        review_digest=preview.review_digest,
        workspace_root=root,
    )
    raw = csv_path.read_text(encoding="utf-8")
    assert raw.startswith("student_id,group\n")
    assert len(raw.splitlines()) == 30
    importing = _import(csv_path)
    reviewed = prepare_csv_import(importing, workspace_root=root)
    assert reviewed.assigned_count == 29
    assert reviewed.unresolved_student_ids == ()
    imported = import_csv_grouping(
        importing,
        review_digest=reviewed.review_digest,
        workspace_root=root,
    )
    assert imported.revision.arrangement_id != saved.revision.arrangement_id
    assert len(imported.revision.groups) == 6
    assert imported.revision.groups[0].label == "table-1"
    for previous, following in zip(saved.revision.groups, imported.revision.groups):
        assert set(previous.student_ids) == set(following.student_ids)
    assert imported.revision.status == "active"
    assert (
        len(
            list_current_arrangements(
                root, class_id=CLASS, school_year=YEAR, actor_id=TEACHER.actor_id
            )
        )
        == 2
    )
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year=YEAR,
            arrangement_id="source-six-tables",
            actor_id=TEACHER.actor_id,
        )
        == saved
    )
    assert not (root / "classes" / CLASS / "work").exists()


def test_unresolved_and_empty_groups_loss_is_explicit(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    original = _first(missing=(ROSTER[0],))
    first = original.groups[5]
    # An empty group may exist in saved library but not in two-column CSV.
    removed = first.student_ids
    revised = replace(
        original,
        groups=tuple(
            replace(group, student_ids=()) if index == 5 else group
            for index, group in enumerate(original.groups)
        ),
        unresolved_student_ids=tuple(sorted((ROSTER[0], *removed))),
    )
    saved = create_arrangement(root, revised, actor_id=TEACHER.actor_id)
    preview = prepare_csv_export(_export(saved), workspace_root=root)
    assert preview.omitted_empty_group_count == 1
    assert preview.omitted_unresolved_count == len(revised.unresolved_student_ids)
    path = tmp_path / "subset.csv"
    export_csv_grouping(
        _export(saved),
        output_path=path,
        review_digest=preview.review_digest,
        workspace_root=root,
    )
    request = _import(path)
    imported_preview = prepare_csv_import(request, workspace_root=root)
    assert len(imported_preview.groups) == 5
    assert len(imported_preview.unresolved_student_ids) == len(
        revised.unresolved_student_ids
    )
    with pytest.raises(ConcordWorkflowConflictError, match="Acknowledge"):
        import_csv_grouping(
            request,
            review_digest=imported_preview.review_digest,
            workspace_root=root,
        )
    import_csv_grouping(
        replace(request, acknowledge_unresolved=True),
        review_digest=imported_preview.review_digest,
        workspace_root=root,
    )


@pytest.mark.parametrize(
    "content",
    [
        "wrong,header\nstudent-01,table-a\n",
        "student_id,group\nstudent-01,table-a\nstudent-01,table-b\n",
        "student_id,group\nunknown-student,table-a\n",
        "student_id,group\nstudent-01,table-a,unexpected\n",
        "student_id,group\n",
    ],
)
def test_strict_csv_rejections_do_not_write(tmp_path: Path, content: str) -> None:
    root = _setup(tmp_path)
    source = tmp_path / "bad.csv"
    source.write_text(content, encoding="utf-8")
    with pytest.raises(ArrangementCsvValidationError):
        prepare_csv_import(_import(source), workspace_root=root)
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=TEACHER.actor_id
        )
        == ()
    )


def test_csv_changes_and_forged_digests_fail_closed(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    source = tmp_path / "import.csv"
    source.write_text("student_id,group\nstudent-01,table-1\n", encoding="utf-8")
    request = _import(source, acknowledge_unresolved=True)
    preview = prepare_csv_import(request, workspace_root=root)
    source.write_text("student_id,group\nstudent-02,table-1\n", encoding="utf-8")
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        import_csv_grouping(
            request, review_digest=preview.review_digest, workspace_root=root
        )
    assert not list_current_arrangements(
        root, class_id=CLASS, school_year=YEAR, actor_id=TEACHER.actor_id
    )


def test_export_no_overwrite_owner_and_stale_revision(tmp_path: Path) -> None:
    root = _setup(tmp_path)
    saved = create_arrangement(root, _first(), actor_id=TEACHER.actor_id)
    request = _export(saved)
    preview = prepare_csv_export(request, workspace_root=root)
    target = tmp_path / "existing.csv"
    target.write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(ConcordWorkflowConflictError, match="already exists"):
        export_csv_grouping(
            request,
            output_path=target,
            review_digest=preview.review_digest,
            workspace_root=root,
        )
    assert target.read_text(encoding="utf-8") == "do not overwrite"
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        prepare_csv_export(
            replace(request, expected_sha256="f" * 64), workspace_root=root
        )
    with pytest.raises(ArrangementConflictError, match="owning teacher"):
        prepare_csv_export(
            replace(request, actor=WorkflowActor(actor_id="other-teacher")),
            workspace_root=root,
        )
    with pytest.raises(ConcordWorkflowConflictError, match="preview changed"):
        export_csv_grouping(
            request,
            output_path=tmp_path / "not-created.csv",
            review_digest="e" * 64,
            workspace_root=root,
        )
    assert not (tmp_path / "not-created.csv").exists()


def test_cli_argparse_preview_privacy_and_explicit_export_authorization(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _setup(tmp_path)
    saved = create_arrangement(root, _first(), actor_id=TEACHER.actor_id)
    base = [
        "saved-grouping",
        "csv-export-preview",
        "--workspace-root",
        str(root),
        "--class-id",
        CLASS,
        "--arrangement-id",
        "source-six-tables",
        "--actor-id",
        TEACHER.actor_id,
        "--expected-revision",
        "1",
        "--expected-sha256",
        saved.sha256,
    ]
    parsed = build_parser().parse_args(base)
    assert parsed.saved_grouping_command == "csv-export-preview"
    assert parsed.handler(parsed) == 0
    captured = capsys.readouterr().out
    assert "Assigned students to export: 29" in captured
    assert "student-01" not in captured
    destination = tmp_path / "private.csv"
    args = base.copy()
    args[1] = "csv-export"
    args += ["--review-digest", "1" * 64, "--output-path", str(destination)]
    assert main(args) == 1
    assert "authorize-roster-export" in capsys.readouterr().err
    assert not destination.exists()


def test_cli_import_preview_does_not_write_and_requires_acknowledgment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _setup(tmp_path)
    path = tmp_path / "one-student.csv"
    path.write_text("student_id,group\nstudent-01,table-1\n", encoding="utf-8")
    args = [
        "saved-grouping",
        "csv-import-preview",
        "--workspace-root",
        str(root),
        "--class-id",
        CLASS,
        "--arrangement-id",
        "csv-new",
        "--actor-id",
        TEACHER.actor_id,
        "--name",
        "Synthetic CSV",
        "--csv-path",
        str(path),
    ]
    assert main(args) == 0
    out = capsys.readouterr().out
    assert "Unresolved students: 28" in out
    assert "student-01" not in out
    assert not list_current_arrangements(
        root, class_id=CLASS, school_year=YEAR, actor_id=TEACHER.actor_id
    )
    assert (
        main(["saved-grouping", "csv-import", *args[2:], "--review-digest", "f" * 64])
        == 3
    )
    assert not list_current_arrangements(
        root, class_id=CLASS, school_year=YEAR, actor_id=TEACHER.actor_id
    )
