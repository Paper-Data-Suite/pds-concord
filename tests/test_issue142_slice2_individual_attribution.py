"""#142 Slice 2: real menu handlers, disposable Core/Concord authoring context.

Paper preparation and proposed associations are NOT returned student work.
All decisions below are fabricated teacher inputs and never publish proficiency.
"""

from __future__ import annotations

from pathlib import Path
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
from concord.menu_context import MenuSessionContext
from concord.models import ParticipantReference, PrivacyPolicy, SubjectReference
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import show_activity
from concord.workflows.artifact_attribution import (
    list_artifact_authors,
    list_artifact_subjects,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)
from concord.workflows.teacher_artifact_choices import list_teacher_artifact_choices

ORIGINAL_MENU_CHOOSE_ARTIFACT = menu._choose_artifact
ORIGINAL_MENU_CHOOSE_AUTHOR = menu._choose_author
ORIGINAL_MENU_CHOOSE_SUBJECT = menu._choose_subject


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _prepare(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    orientation: str = "mixed",
) -> tuple[Path, str]:
    fixture = build_workspace(tmp_path, orientation=orientation)
    root = fixture.root
    if orientation in {"mixed", "standards_based"}:
        write_workspace_standards_library(root, fixture.standards)
    original = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=SOURCE_CLASS,
            activity_id=ACTIVITY_ID,
            artifact_instance_id="synthetic-planned-artifact",
            template_version_id="synthetic-template",
            artifact_category="observation",
            expected_snapshot_revision=original.snapshot_revision,
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
        standards_library=(
            fixture.standards if orientation in {"mixed", "standards_based"} else None
        ),
    )
    assert prepared.commit.snapshot_revision > original.snapshot_revision

    # Replace only the ambient menu read boundary with a pinned test workspace.
    # begin/revalidate and the underlying canonical mutators remain REAL.
    monkeypatch.setattr(
        menu,
        "_latest",
        lambda activity: (
            show_activity(
                activity.class_id, activity.activity_id, workspace_root=root
            ).summary
        ),
    )
    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit=None: root if explicit is None else Path(explicit),
    )
    monkeypatch.setattr(
        menu,
        "_choose_artifact",
        lambda *a, **kw: (
            list_teacher_artifact_choices(
                SOURCE_CLASS,
                ACTIVITY_ID,
                workspace_root=root,
                standards_library=(
                    load_workspace_standards_library(root)
                    if orientation in {"mixed", "standards_based"}
                    else None
                ),
            )[0].summary
        ),
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(menu, "show_result", lambda *a, **kw: None)
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda title, label, **kw: {
            "Artifact Author ID": "synthetic-author-original",
            "Artifact Subject ID": "synthetic-subject-original",
            "Replacement Artifact Author ID": "synthetic-author-successor",
            "Replacement Artifact Subject ID": "synthetic-subject-successor",
            "Correction ID": (
                "synthetic-correction-author"
                if "Author" in title
                else "synthetic-correction-subject"
            ),
            "Reason": "Synthetic teacher correction of relationship semantics",
        }[label],
    )
    student_id = fixture.source.students[0]
    monkeypatch.setattr(
        menu,
        "_choose_author_semantics",
        lambda *a, **kw: (
            ParticipantReference(
                participant_kind="core_student",
                participant_id=student_id,
                owning_system="core",
            ),
            "individual_author",
            "proposed",
            "teacher",
            None,
            None,
            None,
        ),
    )
    monkeypatch.setattr(
        menu,
        "_choose_subject_semantics",
        lambda *a, **kw: (
            SubjectReference(
                subject_kind="core_student",
                subject_id=student_id,
                owning_system="core",
            ),
            "observed_participant",
            "proposed",
            "teacher",
            None,
        ),
    )
    monkeypatch.setattr(
        menu,
        "_choose_author",
        lambda *a, **kw: list_artifact_authors(
            SOURCE_CLASS,
            ACTIVITY_ID,
            workspace_root=root,
            standards_library=(
                load_workspace_standards_library(root)
                if orientation in {"mixed", "standards_based"}
                else None
            ),
        )[0],
    )
    monkeypatch.setattr(
        menu,
        "_choose_subject",
        lambda *a, **kw: list_artifact_subjects(
            SOURCE_CLASS,
            ACTIVITY_ID,
            workspace_root=root,
            standards_library=(
                load_workspace_standards_library(root)
                if orientation in {"mixed", "standards_based"}
                else None
            ),
        )[0],
    )
    return root, student_id


def _call(kind: str, root: Path) -> None:
    selected = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    handler = {
        "add_author": menu._add_author,
        "update_author": menu._update_author,
        "correct_author": menu._correct_author,
        "add_subject": menu._add_subject,
        "update_subject": menu._update_subject,
        "correct_subject": menu._correct_subject,
    }[kind]
    handler(selected, MenuSessionContext(actor=ACTOR))


@pytest.mark.parametrize("kind", ("author", "subject"))
@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_real_menu_creates_exact_proposed_association(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, orientation: str
) -> None:
    root, student_id = _prepare(tmp_path, monkeypatch, orientation=orientation)
    before = list_work_snapshots(root, _work())
    _call("add_" + kind, root)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    # A planned page never becomes returned evidence or a Score.
    loaded = load_current_record_graph(
        root,
        _work(),
        standards_library=(
            load_workspace_standards_library(root)
            if orientation in {"mixed", "standards_based"}
            else None
        ),
    )
    graph = loaded.graph
    assert not graph.score_records
    assert not graph.artifact_reviews
    assert graph.artifact_instances[0].artifact_status == "planned"
    if kind == "author":
        assert len(graph.artifact_authors) == 1
        record = graph.artifact_authors[0]
        assert record.attribution_status == "proposed"
        assert record.author_reference.participant_id == student_id
        assert record.created_provenance.actor.actor_id == ACTOR.actor_id
    else:
        assert len(graph.artifact_subjects) == 1
        record = graph.artifact_subjects[0]
        assert record.confirmation_status == "proposed"
        assert record.subject_reference.subject_id == student_id
        assert record.created_provenance.actor.actor_id == ACTOR.actor_id


@pytest.mark.parametrize("kind", ("author", "subject"))
def test_real_menu_status_update_keeps_same_association_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    _call("add_" + kind, root)
    before = list_work_snapshots(root, _work())
    monkeypatch.setattr(
        menu,
        "_author_status" if kind == "author" else "_subject_status",
        lambda: "disputed",
    )
    _call("update_" + kind, root)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = load_current_record_graph(
        root, _work(), standards_library=load_workspace_standards_library(root)
    ).graph
    if kind == "author":
        assert len(graph.artifact_authors) == 1
        assert (
            graph.artifact_authors[0].artifact_author_id == "synthetic-author-original"
        )
        assert graph.artifact_authors[0].attribution_status == "disputed"
    else:
        assert len(graph.artifact_subjects) == 1
        assert (
            graph.artifact_subjects[0].artifact_subject_id
            == "synthetic-subject-original"
        )
        assert graph.artifact_subjects[0].confirmation_status == "disputed"
    assert not graph.correction_records


@pytest.mark.parametrize("kind", ("author", "subject"))
def test_real_menu_correction_creates_one_immutable_successor_and_correction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    _call("add_" + kind, root)
    original = load_current_record_graph(
        root, _work(), standards_library=load_workspace_standards_library(root)
    ).graph
    before = list_work_snapshots(root, _work())
    if kind == "author":
        old = original.artifact_authors[0]
        monkeypatch.setattr(
            menu,
            "_choose_author_semantics",
            lambda *a, **kw: (
                old.author_reference,
                "co_author",
                "proposed",
                "teacher",
                None,
                None,
                None,
            ),
        )
    else:
        old = original.artifact_subjects[0]
        monkeypatch.setattr(
            menu,
            "_choose_subject_semantics",
            lambda *a, **kw: (
                old.subject_reference,
                "general_subject",
                "proposed",
                "teacher",
                None,
            ),
        )
    _call("correct_" + kind, root)
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = load_current_record_graph(
        root, _work(), standards_library=load_workspace_standards_library(root)
    ).graph
    assert len(graph.correction_records) == 1
    correction = graph.correction_records[0]
    if kind == "author":
        assert len(graph.artifact_authors) == 2
        assert graph.artifact_authors[0].artifact_author_id == old.artifact_author_id
        successor = next(
            a
            for a in graph.artifact_authors
            if a.artifact_author_id != old.artifact_author_id
        )
        assert successor.supersedes_artifact_author_id == old.artifact_author_id
        assert successor.authorship_mode == "co_author"
        assert (
            correction.replacement_reference.record_id == successor.artifact_author_id
        )
    else:
        assert len(graph.artifact_subjects) == 2
        successor = next(
            s
            for s in graph.artifact_subjects
            if s.artifact_subject_id != old.artifact_subject_id
        )
        assert successor.supersedes_artifact_subject_id == old.artifact_subject_id
        assert successor.subject_role == "general_subject"
        assert (
            correction.replacement_reference.record_id == successor.artifact_subject_id
        )


@pytest.mark.parametrize(
    "kind",
    (
        "add_author",
        "update_author",
        "correct_author",
        "add_subject",
        "update_subject",
        "correct_subject",
    ),
)
def test_cancel_is_exact_no_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    if not kind.startswith("add_"):
        _call("add_" + kind.split("_")[1], root)
    before = list_work_snapshots(root, _work())
    if kind == "update_author":
        monkeypatch.setattr(menu, "_author_status", lambda: "disputed")
    elif kind == "update_subject":
        monkeypatch.setattr(menu, "_subject_status", lambda: "disputed")
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: False)
    _call(kind, root)
    assert list_work_snapshots(root, _work()) == before


def test_stale_revision_rejected_after_teacher_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    before = list_work_snapshots(root, _work())
    real = authority.revalidate_artifact_write_context

    def stale(preview: Any, *, operation: str, expected_snapshot_revision: int) -> Any:
        return real(
            preview,
            operation=operation,
            expected_snapshot_revision=expected_snapshot_revision + 1,
        )

    monkeypatch.setattr(menu, "revalidate_artifact_write_context", stale)
    with pytest.raises(Exception, match="different revision"):
        _call("add_author", root)
    assert list_work_snapshots(root, _work()) == before


def test_teacher_selection_from_other_core_class_is_rejected_without_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    foreign = build_workspace(tmp_path / "other", orientation="mixed")
    other_student = foreign.target.students[0]
    monkeypatch.setattr(
        menu,
        "_choose_author_semantics",
        lambda *a, **kw: (
            ParticipantReference(
                participant_kind="core_student",
                participant_id=other_student,
                owning_system="core",
            ),
            "individual_author",
            "proposed",
            "teacher",
            None,
            None,
            None,
        ),
    )
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception):
        _call("add_author", root)
    assert list_work_snapshots(root, _work()) == before


def test_duplicate_existing_author_association_is_not_recreated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    _call("add_author", root)
    before = list_work_snapshots(root, _work())
    with pytest.raises(Exception):
        _call("add_author", root)
    assert list_work_snapshots(root, _work()) == before


def test_active_root_drift_during_confirmation_refuses_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    foreign = build_workspace(tmp_path / "other", orientation="mixed")
    before = list_work_snapshots(root, _work())
    foreign_before = list_work_snapshots(
        foreign.root, ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)
    )

    def confirm_and_drift(*args: Any, **kwargs: Any) -> bool:
        monkeypatch.setattr(
            authority,
            "resolve_read_workspace_root",
            lambda explicit=None: foreign.root if explicit is None else Path(explicit),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", confirm_and_drift)
    with pytest.raises(Exception, match="active Core workspace has changed"):
        _call("add_subject", root)
    assert list_work_snapshots(root, _work()) == before
    assert (
        list_work_snapshots(
            foreign.root, ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)
        )
        == foreign_before
    )


def test_concurrent_activity_snapshot_change_blocks_author_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concord.workflows import UpdateActivityRequest, update_activity

    root, _ = _prepare(tmp_path, monkeypatch)
    before = list_work_snapshots(root, _work())

    def confirm_after_other_teacher_write(*args: Any, **kwargs: Any) -> bool:
        current = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
        update_activity(
            UpdateActivityRequest(
                class_id=SOURCE_CLASS,
                activity_id=ACTIVITY_ID,
                expected_snapshot_revision=current.snapshot_revision,
                actor=ACTOR,
                status="configured",
            ),
            workspace_root=root,
            standards_library=load_workspace_standards_library(root),
        )
        return True

    monkeypatch.setattr(menu, "confirm_write", confirm_after_other_teacher_write)
    with pytest.raises(Exception, match="snapshot changed after preview"):
        _call("add_author", root)
    # Exactly one unrelated Activity update; no additional attribution write.
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    graph = load_current_record_graph(
        root, _work(), standards_library=load_workspace_standards_library(root)
    ).graph
    assert not graph.artifact_authors


@pytest.mark.parametrize(
    "orientation", ("mixed", "standards_based", "evidence_only", "local_criteria_only")
)
def test_production_artifact_selector_uses_pinned_canonical_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, orientation: str
) -> None:
    actual_select = ORIGINAL_MENU_CHOOSE_ARTIFACT
    root, _ = _prepare(tmp_path, monkeypatch, orientation=orientation)
    monkeypatch.setattr(menu, "_choose_artifact", actual_select)
    monkeypatch.setattr(menu, "select_one", lambda title, items, labels, **kw: items[0])
    selected = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    preview = authority.begin_artifact_write_context(
        selected, operation="Test selection"
    )
    before = list_work_snapshots(root, _work())
    chosen = menu._choose_artifact(
        selected, title="Synthetic Artifact", write_context=preview
    )
    assert chosen.artifact_instance_id == "synthetic-planned-artifact"
    assert chosen.snapshot_revision == selected.snapshot_revision
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("kind", ("author", "subject"))
def test_production_attribution_selector_uses_pinned_canonical_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    root, _ = _prepare(tmp_path, monkeypatch)
    _call("add_" + kind, root)
    original = (
        ORIGINAL_MENU_CHOOSE_AUTHOR
        if kind == "author"
        else ORIGINAL_MENU_CHOOSE_SUBJECT
    )
    monkeypatch.setattr(menu, "_choose_" + kind, original)
    monkeypatch.setattr(menu, "select_one", lambda title, items, labels, **kw: items[0])
    selected = show_activity(SOURCE_CLASS, ACTIVITY_ID, workspace_root=root).summary
    preview = authority.begin_artifact_write_context(
        selected, operation="Test association selection"
    )
    before = list_work_snapshots(root, _work())
    chosen = original(selected, title="Synthetic association", write_context=preview)
    actual_id = (
        chosen.artifact_author_id if kind == "author" else chosen.artifact_subject_id
    )
    assert actual_id == f"synthetic-{kind}-original"
    assert chosen.snapshot_revision == selected.snapshot_revision
    assert list_work_snapshots(root, _work()) == before
