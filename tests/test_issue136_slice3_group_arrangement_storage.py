"""Synthetic class-only tests; no source Activity or student data persisted here."""

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
    ArrangementIntegrityError,
    ArrangementNotFoundError,
    append_arrangement_revision,
    create_arrangement,
    list_current_arrangements,
    load_current_arrangement,
    review_arrangement_roster,
)
from concord.class_group_arrangements import (
    ArrangementValidationError,
    SavedArrangementGroup,
    SavedArrangementRevision,
    compare_roster,
)

YEAR = "2026-2027"
ACTOR = "teacher-1"


def _roster(class_id: str, ids: tuple[str, ...]):
    return create_roster(
        class_id,
        tuple(
            {
                "student_id": sid,
                "last_name": f"Synthetic-{index}",
                "first_name": "Student",
                "period": "1",
            }
            for index, sid in enumerate(ids, 1)
        ),
    )


def _root(tmp_path: Path, class_id: str = "class-1") -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            class_id,
            YEAR,
            created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        root, _roster(class_id, tuple(f"student-{i:02}" for i in range(1, 30)))
    )
    return root


def _first() -> SavedArrangementRevision:
    ids = tuple(f"student-{i:02}" for i in range(1, 30))
    groups = tuple(
        SavedArrangementGroup(
            key=f"table-{n}",
            label=f"Table {n}",
            student_ids=tuple(ids[i] for i in range(n - 1, 29, 6)),
        )
        for n in range(1, 7)
    )
    return SavedArrangementRevision(
        arrangement_id="six-tables",
        class_id="class-1",
        school_year=YEAR,
        revision=1,
        name="English 12 Six Table Groups",
        owner_actor_id=ACTOR,
        created_by_actor_id=ACTOR,
        created_at="2026-10-17T21:00:00-04:00",
        groups=groups,
        roster_student_ids=ids,
    )


def _next(
    previous: SavedArrangementRevision, digest: str, **kw: object
) -> SavedArrangementRevision:
    return replace(
        previous,
        revision=previous.revision + 1,
        predecessor_sha256=digest,
        created_at="2026-10-17T22:00:00-04:00",
        **kw,
    )


def test_save_six_groups_29_students_and_restart_read(tmp_path: Path) -> None:
    root = _root(tmp_path)
    saved = create_arrangement(root, _first(), actor_id=ACTOR)
    assert saved.revision.revision == 1
    assert len(saved.revision.groups) == 6
    assert sum(len(g.student_ids) for g in saved.revision.groups) == 29
    discovered = list_current_arrangements(
        root, class_id="class-1", school_year=YEAR, actor_id=ACTOR
    )
    assert len(discovered) == 1
    assert discovered[0] == load_current_arrangement(
        root,
        class_id="class-1",
        school_year=YEAR,
        arrangement_id="six-tables",
        actor_id=ACTOR,
    )
    # A reusable configuration does not create Activity-native Groups, Scores or work.
    assert not (root / "classes" / "class-1" / "work").exists()


def test_immutable_revision_rename_and_retire(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = create_arrangement(root, _first(), actor_id=ACTOR)
    second = append_arrangement_revision(
        root,
        _next(first.revision, first.sha256, name="Six Discussion Tables"),
        actor_id=ACTOR,
        expected_revision=1,
        expected_sha256=first.sha256,
    )
    assert second.revision.name == "Six Discussion Tables"
    assert (
        root
        / "shared"
        / "concord"
        / "class-group-arrangements"
        / YEAR
        / "class-1"
        / "six-tables"
        / "revisions"
        / "00000001.json"
    ).is_file()
    assert first.revision.name == "English 12 Six Table Groups"
    retired = append_arrangement_revision(
        root,
        _next(second.revision, second.sha256, status="retired"),
        actor_id=ACTOR,
        expected_revision=2,
        expected_sha256=second.sha256,
    )
    assert retired.revision.status == "retired"
    with pytest.raises(ArrangementConflictError, match="Retired"):
        append_arrangement_revision(
            root,
            _next(retired.revision, retired.sha256),
            actor_id=ACTOR,
            expected_revision=3,
            expected_sha256=retired.sha256,
        )


def test_stale_revision_and_owner_blocked_without_new_revision(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = create_arrangement(root, _first(), actor_id=ACTOR)
    with pytest.raises(ArrangementConflictError, match="changed"):
        append_arrangement_revision(
            root,
            _next(first.revision, first.sha256),
            actor_id=ACTOR,
            expected_revision=1,
            expected_sha256="f" * 64,
        )
    with pytest.raises(ArrangementConflictError, match="owning teacher"):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id="teacher-2",
        )
    assert (
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )
        == first
    )


def test_scope_restrictions_and_empty_list(tmp_path: Path) -> None:
    root = _root(tmp_path)
    assert (
        list_current_arrangements(
            root, class_id="class-1", school_year=YEAR, actor_id=ACTOR
        )
        == ()
    )
    create_arrangement(root, _first(), actor_id=ACTOR)
    assert (
        list_current_arrangements(
            root, class_id="class-1", school_year=YEAR, actor_id="teacher-2"
        )
        == ()
    )
    with pytest.raises(ArrangementConflictError, match="school year"):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year="2025-2026",
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )
    with pytest.raises(ArrangementConflictError):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="../six-tables",
            actor_id=ACTOR,
        )


def test_duplicate_or_unreviewed_roster_fails_contract() -> None:
    original = _first()
    first = original.groups[0]
    duplicated = replace(
        first, student_ids=first.student_ids + original.groups[1].student_ids[:1]
    )
    with pytest.raises(ArrangementValidationError, match="multiple"):
        replace(original, groups=(duplicated, *original.groups[1:]))
    with pytest.raises(
        ArrangementValidationError, match="assigned or explicitly unresolved"
    ):
        replace(
            original,
            groups=(
                replace(first, student_ids=first.student_ids[1:]),
                *original.groups[1:],
            ),
        )


def test_explicit_unresolved_and_new_or_departed_roster() -> None:
    original = _first()
    first = original.groups[0]
    removed = first.student_ids[0]
    unresolved = replace(
        original,
        groups=(
            replace(first, student_ids=first.student_ids[1:]),
            *original.groups[1:],
        ),
        unresolved_student_ids=(removed,),
    )
    target = tuple(s for s in original.roster_student_ids if s != "student-29") + (
        "student-30",
    )
    comparison = compare_roster(
        unresolved,
        target_class_id="class-1",
        target_school_year=YEAR,
        target_student_ids=target,
    )
    assert comparison.newly_enrolled_ids == ("student-30",)
    assert comparison.departed_ids == ("student-29",)
    assert comparison.unresolved_ids == (removed,)
    assert comparison.needs_teacher_review is True
    with pytest.raises(ArrangementValidationError, match="another class"):
        compare_roster(
            original,
            target_class_id="class-2",
            target_school_year=YEAR,
            target_student_ids=target,
        )


def test_changed_core_roster_rejected_before_create(tmp_path: Path) -> None:
    root = _root(tmp_path)
    write_class_roster(
        root, _roster("class-1", ("student-01", "student-30")), overwrite=True
    )
    with pytest.raises(ArrangementConflictError, match="Core roster changed"):
        create_arrangement(root, _first(), actor_id=ACTOR)
    assert (
        list_current_arrangements(
            root, class_id="class-1", school_year=YEAR, actor_id=ACTOR
        )
        == ()
    )


def test_roster_review_is_read_only(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = create_arrangement(root, _first(), actor_id=ACTOR)
    write_class_roster(
        root,
        _roster(
            "class-1", tuple(f"student-{i:02}" for i in range(1, 29)) + ("student-30",)
        ),
        overwrite=True,
    )
    loaded, differences = review_arrangement_roster(
        root,
        class_id="class-1",
        school_year=YEAR,
        arrangement_id="six-tables",
        actor_id=ACTOR,
    )
    assert loaded == first
    assert differences.newly_enrolled_ids == ("student-30",)
    assert differences.departed_ids == ("student-29",)
    assert (
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )
        == first
    )


def test_detect_tampering_and_orphan_revisions(tmp_path: Path) -> None:
    root = _root(tmp_path)
    create_arrangement(root, _first(), actor_id=ACTOR)
    revisions = (
        root
        / "shared"
        / "concord"
        / "class-group-arrangements"
        / YEAR
        / "class-1"
        / "six-tables"
        / "revisions"
    )
    (revisions / "00000002.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ArrangementIntegrityError, match="orphan"):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )
    (revisions / "00000002.json").unlink()
    (revisions / "00000001.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ArrangementIntegrityError):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )


def test_linked_arrangement_directory_is_rejected(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    collection = (
        root / "shared" / "concord" / "class-group-arrangements" / YEAR / "class-1"
    )
    collection.mkdir(parents=True)
    try:
        (collection / "six-tables").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Windows account cannot create symbolic links")
    with pytest.raises(ArrangementIntegrityError, match="link or reparse"):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )


def test_missing_saved_grouping_and_duplicate_create(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(ArrangementNotFoundError):
        load_current_arrangement(
            root,
            class_id="class-1",
            school_year=YEAR,
            arrangement_id="six-tables",
            actor_id=ACTOR,
        )
    create_arrangement(root, _first(), actor_id=ACTOR)
    with pytest.raises(ArrangementConflictError, match="already exists"):
        create_arrangement(root, _first(), actor_id=ACTOR)
