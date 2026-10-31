"""#142 Slice 3: genuine multi-attribution and exact status-only confirmation.

All participants, activities, and Artifacts are synthetic and confined to pytest
``tmp_path``. Prepared paper is not a returned scan, Score, or proficiency.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    SOURCE_CLASS,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import (
    load_workspace_standards_library,
    write_workspace_standards_library,
)

import concord.menu_artifact as menu
import concord.menu_artifact_write_context as authority
from concord.models import PrivacyPolicy
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import show_activity
from concord.workflows.artifact_attribution_review import (
    inspect_artifact_attribution_review,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)

ARTIFACT_ID = "issue142-synthetic-planned-batch-artifact"
STUDENTS = tuple(f"{SOURCE_CLASS}-student-{n:02d}" for n in (1, 2))


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _standards(root: Path, orientation: str) -> Any:
    if orientation in {"mixed", "standards_based"}:
        return load_workspace_standards_library(root)
    return None


def _snapshot(root: Path, orientation: str) -> Any:
    return load_current_record_graph(
        root, _work(), standards_library=_standards(root, orientation)
    ).graph


def _fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    orientation: str = "mixed",
) -> Path:
    witness = build_workspace(tmp_path, orientation=orientation)
    root = witness.root
    if orientation in {"mixed", "standards_based"}:
        write_workspace_standards_library(root, witness.standards)
    current = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
    ).summary
    prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            template_version_id="issue142-synthetic-template",
            artifact_category="observation",
            expected_snapshot_revision=current.snapshot_revision,
            actor=ACTOR,
            expected_return_status="return_not_expected",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            pages=(
                ArtifactPagePlan(
                    page_number=1, return_expected=False, route_required=False
                ),
            ),
        ),
        workspace_root=root,
        standards_library=_standards(root, orientation),
    )

    monkeypatch.setattr(
        menu,
        "_latest",
        lambda activity: show_activity(
            activity.class_id, activity.activity_id, workspace_root=root
        ).summary,
    )
    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit=None: root if explicit is None else Path(explicit),
    )
    monkeypatch.setattr(
        menu, "_require_workspace", lambda: root
    )
    monkeypatch.setattr(
        menu, "select_one", lambda _title, choices, _labels, **_kw: choices[0]
    )
    monkeypatch.setattr(
        menu,
        "choose_students",
        lambda selected_root, class_id: (
            _selected_students(selected_root, class_id, root)
        ),
    )
    monkeypatch.setattr(
        menu, "_routine_multi_author_mode", lambda: "individual_author"
    )
    monkeypatch.setattr(
        menu, "_routine_multi_subject_role", lambda: "observed_participant"
    )
    monkeypatch.setattr(
        menu, "_routine_add_status", lambda **_kw: "proposed"
    )
    monkeypatch.setattr(menu, "prompt_text", lambda *a, **kw: None)
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(menu, "show_result", lambda *a, **kw: None)
    return root


def _selected_students(selected_root: Path, class_id: str, root: Path) -> Any:
    assert Path(selected_root).resolve() == root.resolve()
    assert class_id == SOURCE_CLASS
    return tuple(SimpleNamespace(student_id=sid) for sid in STUDENTS)


def _activity(root: Path) -> Any:
    return show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
    ).summary


def _add(root: Path, kind: str) -> None:
    handler = {
        "authors": menu._add_multiple_authors,
        "subjects": menu._add_multiple_subjects,
    }[kind]
    handler(_activity(root), menu.MenuSessionContext(actor=ACTOR))


def _review(root: Path) -> Any:
    return inspect_artifact_attribution_review(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=root
    )


def _confirm(
    root: Path,
    *,
    author_ids: tuple[str, ...],
    subject_ids: tuple[str, ...],
    review: Any | None = None,
) -> None:
    chosen_review = _review(root) if review is None else review
    menu._commit_attribution_confirmation(
        _activity(root),
        chosen_review,
        menu.MenuSessionContext(actor=ACTOR),
        artifact_author_ids=author_ids,
        artifact_subject_ids=subject_ids,
        unselected_candidate_count=(
            chosen_review.candidate_count - len(author_ids) - len(subject_ids)
        ),
    )


@pytest.mark.parametrize("kind", ("authors", "subjects"))
@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_two_homogeneous_student_associations_commit_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    orientation: str,
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation=orientation)
    before = list_work_snapshots(root, _work())
    _add(root, kind)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = _snapshot(root, orientation)
    assert graph.artifact_instances[0].artifact_status == "planned"
    assert graph.scan_references == ()
    assert graph.score_records == ()
    assert graph.artifact_reviews == ()
    if kind == "authors":
        assert len(graph.artifact_authors) == 2
        assert len(graph.artifact_subjects) == 0
        assert {
            item.author_reference.participant_id for item in graph.artifact_authors
        } == set(STUDENTS)
        assert {item.attribution_status for item in graph.artifact_authors} == {
            "proposed"
        }
    else:
        assert len(graph.artifact_subjects) == 2
        assert len(graph.artifact_authors) == 0
        assert {
            item.subject_reference.subject_id for item in graph.artifact_subjects
        } == set(STUDENTS)
        assert {item.confirmation_status for item in graph.artifact_subjects} == {
            "proposed"
        }


@pytest.mark.parametrize("orientation", ("mixed", "evidence_only"))
def test_batch_confirmation_updates_exact_current_associations_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    root = _fixture(tmp_path, monkeypatch, orientation=orientation)
    _add(root, "authors")
    _add(root, "subjects")
    review = _review(root)
    assert len(review.candidate_author_ids) == 2
    assert len(review.candidate_subject_ids) == 2
    selected_author = review.candidate_author_ids[0]
    selected_subject = review.candidate_subject_ids[0]
    before = list_work_snapshots(root, _work())
    _confirm(
        root,
        author_ids=(selected_author,),
        subject_ids=(selected_subject,),
        review=review,
    )
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = _snapshot(root, orientation)
    assert len(graph.artifact_authors) == len(graph.artifact_subjects) == 2
    assert graph.correction_records == ()
    assert graph.score_records == ()
    author_statuses = {
        a.artifact_author_id: a.attribution_status for a in graph.artifact_authors
    }
    assert author_statuses == {
        a: ("confirmed" if a == selected_author else "proposed")
        for a in review.candidate_author_ids
    }
    assert {
        s.artifact_subject_id: s.confirmation_status for s in graph.artifact_subjects
    } == {
        s: ("confirmed" if s == selected_subject else "proposed")
        for s in review.candidate_subject_ids
    }


@pytest.mark.parametrize("kind", ("authors", "subjects", "confirm"))
def test_cancellation_never_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root = _fixture(tmp_path, monkeypatch)
    if kind == "confirm":
        _add(root, "authors")
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: False)
    if kind == "confirm":
        review = _review(root)
        _confirm(root, author_ids=review.candidate_author_ids, subject_ids=())
    else:
        _add(root, kind)
    assert list_work_snapshots(root, _work()) == before


def test_duplicate_roster_selection_rejects_whole_batch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        menu,
        "choose_students",
        lambda *a, **kw: (
            SimpleNamespace(student_id=STUDENTS[0]),
            SimpleNamespace(student_id=STUDENTS[0]),
        ),
    )
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="duplicate student IDs"):
        _add(root, "authors")
    assert list_work_snapshots(root, _work()) == before


def test_foreign_roster_student_is_not_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch)
    foreign_student = f"{SOURCE_CLASS}-invalid-student"
    monkeypatch.setattr(
        menu,
        "choose_students",
        lambda *a, **kw: (SimpleNamespace(student_id=foreign_student),),
    )
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception):
        _add(root, "subjects")
    assert list_work_snapshots(root, _work()) == before


def test_stale_attribution_review_rejected_before_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch)
    _add(root, "authors")
    old_review = _review(root)
    _add(root, "subjects")
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception, match="changed|revision|stale"):
        _confirm(
            root,
            author_ids=old_review.candidate_author_ids,
            subject_ids=(),
            review=old_review,
        )
    assert list_work_snapshots(root, _work()) == before


def test_workspace_drift_during_batch_confirmation_rejects_both_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch)
    foreign = build_workspace(tmp_path / "foreign", orientation="mixed")
    _add(root, "authors")
    review = _review(root)
    before = list_work_snapshots(root, _work())
    foreign_before = list_work_snapshots(foreign.root, _work())

    def confirm_and_switch(*_a: Any, **_kw: Any) -> bool:
        monkeypatch.setattr(
            authority,
            "resolve_read_workspace_root",
            lambda explicit=None: (
                foreign.root if explicit is None else Path(explicit)
            ),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", confirm_and_switch)
    with pytest.raises(Exception, match="workspace has changed"):
        _confirm(root, author_ids=review.candidate_author_ids, subject_ids=())
    assert list_work_snapshots(root, _work()) == before
    assert list_work_snapshots(foreign.root, _work()) == foreign_before


def test_no_proposals_has_no_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _fixture(tmp_path, monkeypatch)
    before = list_work_snapshots(root, _work())
    menu._commit_attribution_confirmation(
        _activity(root),
        SimpleNamespace(snapshot_revision=_activity(root).snapshot_revision),
        menu.MenuSessionContext(actor=ACTOR),
        artifact_author_ids=(),
        artifact_subject_ids=(),
        unselected_candidate_count=0,
    )
    assert list_work_snapshots(root, _work()) == before
