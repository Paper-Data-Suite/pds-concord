"""Issue #142 Slice 6A: genuinely returned, assembled synthetic evidence.

Creates only disposable Core/Concord workspaces under pytest tmp_path.
The source image contains fabricated pixels, not schoolwork. Evidence-only
Activities are explicitly prohibited from creating Scores.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from test_workflow_artifact_assembly import (
    _actor,
    _clock,
    _file,
    _prepare,
    _retained_image,
    _work,
    _workspace,
)

import concord.menu_artifact as artifact_menu
import concord.menu_artifact_write_context as authority
from concord.models import ParticipantReference, SubjectReference
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    AddArtifactAuthorRequest,
    AddArtifactSubjectRequest,
    add_artifact_author,
    add_artifact_subject,
    show_activity,
)
from concord.workflows.artifact import list_artifacts
from concord.workflows.artifact_assembly import (
    AssembleArtifactRequest,
    assemble_returned_artifact,
)
from concord.workflows.artifact_routine_review import inspect_artifact_routine_review
from concord.workflows.artifact_routine_scoring import inspect_artifact_routine_scoring

CLASS = "class-1"
ACTIVITY = "activity-1"
ARTIFACT = "artifact-1"


def _revision(root: Path) -> int:
    return show_activity(CLASS, ACTIVITY, workspace_root=root).summary.snapshot_revision


def _setup_returned(tmp_path: Path, *, assemble: bool) -> Path:
    root = _workspace(tmp_path)
    write_class_roster(
        root,
        create_roster(
            CLASS,
            (
                {
                    "student_id": "student-1",
                    "first_name": "Synthetic",
                    "last_name": "One",
                    "period": "1",
                },
                {
                    "student_id": "student-2",
                    "first_name": "Synthetic",
                    "last_name": "Two",
                    "period": "1",
                },
            ),
        ),
    )
    prepared = _prepare(root)
    before = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert not before.eligibility.quick_review_eligible
    assert before.assembly_state != "assembled"
    image = _retained_image(
        root,
        scan_id="synthetic-source-1",
        filename="synthetic-returned.png",
        color=(12, 24, 36),
    )
    _file(root, prepared, 0, image)
    loaded = load_current_record_graph(root, _work())
    assert loaded.graph.artifact_instances[0].artifact_status == "returned"
    if assemble:
        assembled = assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id=CLASS,
                activity_id=ACTIVITY,
                artifact_instance_id=ARTIFACT,
                expected_snapshot_revision=loaded.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        )
        assert assembled.output_path.read_bytes().startswith(b"%PDF")
        assert assembled.manifest_path.is_file()
    return root


def _confirm_attribution(root: Path) -> None:
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            artifact_author_id="synthetic-author-1",
            author_reference=ParticipantReference(
                participant_kind="core_student",
                participant_id="student-1",
                owning_system="core",
            ),
            authorship_mode="individual_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=_revision(root),
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert author.commit.snapshot_revision == _revision(root)
    subject = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            artifact_subject_id="synthetic-subject-1",
            subject_reference=SubjectReference(
                subject_kind="core_student",
                subject_id="student-2",
                owning_system="core",
            ),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=_revision(root),
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert subject.commit.snapshot_revision == _revision(root)


def _active_workspace(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    monkeypatch.setattr(
        authority,
        "resolve_read_workspace_root",
        lambda explicit=None: root if explicit is None else Path(explicit),
    )


@pytest.mark.parametrize("profile", ("ready", "ready_with_qualification"))
def test_real_assembled_returned_evidence_receives_one_explicit_quick_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, profile: str
) -> None:
    root = _setup_returned(tmp_path, assemble=True)
    _confirm_attribution(root)
    context = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert context.assembly_state == "assembled"
    assert context.first_review_pending
    assert context.eligibility.quick_review_eligible
    assert len(context.current_authors) == 1
    assert len(context.current_subjects) == 1
    assert not context.eligibility.exception_reasons

    _active_workspace(monkeypatch, root)
    calls: list[str] = []

    def select(title: str, items: object, labels: object, **kwargs: object) -> str:
        calls.append(title)
        return "continue" if len(calls) == 1 else profile

    monkeypatch.setattr(artifact_menu, "select_one", select)
    monkeypatch.setattr(
        artifact_menu, "prompt_text", lambda *a, **kw: "Synthetic readable evidence."
    )
    monkeypatch.setattr(artifact_menu, "confirm_write", lambda *a, **kw: True)
    monkeypatch.setattr(artifact_menu, "show_result", lambda *a, **kw: None)
    activity = show_activity(CLASS, ACTIVITY, workspace_root=root).summary
    artifact, = list_artifacts(CLASS, ACTIVITY, workspace_root=root)
    before = list_work_snapshots(root, _work())
    assert artifact_menu._quick_review_selected(
        activity, artifact, artifact_menu.MenuSessionContext(actor=_actor())
    )
    assert len(list_work_snapshots(root, _work())) == len(before) + 1
    assert len(calls) == 2

    latest = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert latest.current_review is not None
    assert latest.current_review.scoring_readiness == profile
    assert not latest.first_review_pending
    assert not latest.eligibility.quick_review_eligible

    score = inspect_artifact_routine_scoring(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert not score.eligibility.routine_scoring_eligible
    assert any(
        "Evidence-only" in reason
        for reason in score.eligibility.exception_reasons
    )
    assert load_current_record_graph(root, _work()).graph.score_records == ()


def test_returned_but_unassembled_work_is_not_eligible_even_with_attribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _setup_returned(tmp_path, assemble=False)
    _confirm_attribution(root)
    context = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert context.assembly_state != "assembled"
    assert not context.eligibility.quick_review_eligible
    _active_workspace(monkeypatch, root)
    monkeypatch.setattr(artifact_menu, "select_one", lambda *a, **kw: "continue")
    monkeypatch.setattr(artifact_menu, "show_result", lambda *a, **kw: None)
    monkeypatch.setattr(
        artifact_menu, "confirm_write",
        lambda *a, **kw: pytest.fail("Unassembled evidence reached confirmation"),
    )
    activity = show_activity(CLASS, ACTIVITY, workspace_root=root).summary
    artifact, = list_artifacts(CLASS, ACTIVITY, workspace_root=root)
    before = list_work_snapshots(root, _work())
    assert not artifact_menu._quick_review_selected(
        activity, artifact, artifact_menu.MenuSessionContext(actor=_actor())
    )
    assert list_work_snapshots(root, _work()) == before


def test_assembled_evidence_without_confirmed_attribution_refuses_quick_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _setup_returned(tmp_path, assemble=True)
    context = inspect_artifact_routine_review(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert context.assembly_state == "assembled"
    assert not context.eligibility.quick_review_eligible
    assert any("Author" in reason for reason in context.eligibility.exception_reasons)
    assert any("Subject" in reason for reason in context.eligibility.exception_reasons)
    _active_workspace(monkeypatch, root)
    monkeypatch.setattr(artifact_menu, "select_one", lambda *a, **kw: "continue")
    monkeypatch.setattr(artifact_menu, "show_result", lambda *a, **kw: None)
    monkeypatch.setattr(
        artifact_menu, "confirm_write",
        lambda *a, **kw: pytest.fail("Unattributed evidence reached confirmation"),
    )
    activity = show_activity(CLASS, ACTIVITY, workspace_root=root).summary
    artifact, = list_artifacts(CLASS, ACTIVITY, workspace_root=root)
    before = list_work_snapshots(root, _work())
    assert not artifact_menu._quick_review_selected(
        activity, artifact, artifact_menu.MenuSessionContext(actor=_actor())
    )
    assert list_work_snapshots(root, _work()) == before
