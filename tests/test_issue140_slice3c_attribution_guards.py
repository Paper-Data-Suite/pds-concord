"""Issue #140 Slice 3C: exact menu-to-workflow Attribution Standards guards.

Use only disposable Core classes and synthetically absent association targets.
A passing guard witness is NOT successful Artifact/Score business acceptance.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from issue140_slice2_fixtures import ACTIVITY_ID, ACTOR, SOURCE_CLASS, build_workspace
from pds_core.routing_models import ModuleWorkRef

import concord.menu_artifact as menu
from concord.models import SubjectReference
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    add_artifact_authors,
    add_artifact_subjects,
    batch_confirm_artifact_attribution,
    replace_artifact_author,
    replace_artifact_subject,
    show_activity,
    update_artifact_author,
    update_artifact_subject,
)

KINDS = (
    "update_author",
    "correct_author",
    "update_subject",
    "correct_subject",
    "multi_author",
    "multi_subject",
    "batch_confirm",
)
ARTIFACT_ID = "issue140-3c-artifact-not-created"
ASSOCIATION_ID = "issue140-3c-association-not-created"

SERVICES = {
    "update_author": ("update_artifact_author", update_artifact_author),
    "correct_author": ("replace_artifact_author", replace_artifact_author),
    "update_subject": ("update_artifact_subject", update_artifact_subject),
    "correct_subject": ("replace_artifact_subject", replace_artifact_subject),
    "multi_author": ("add_artifact_authors", add_artifact_authors),
    "multi_subject": ("add_artifact_subjects", add_artifact_subjects),
    "batch_confirm": (
        "batch_confirm_artifact_attribution",
        batch_confirm_artifact_attribution,
    ),
}


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", SOURCE_CLASS, ACTIVITY_ID)


def _exercise(
    *,
    kind: str,
    activity: Any,
    root: Path,
    students: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
    captured: list[Any],
    approve: bool = True,
) -> None:
    """Invoke the actual menu handler, adapting only its local I/O boundary."""
    state = menu.MenuSessionContext(actor=ACTOR)
    reference = SubjectReference(
        subject_kind="core_student", owning_system="core", subject_id=students[0]
    )
    artifact = SimpleNamespace(
        artifact_instance_id=ARTIFACT_ID,
        artifact_status="planned",
        snapshot_revision=activity.snapshot_revision,
    )
    author = SimpleNamespace(
        artifact_author_id=ASSOCIATION_ID,
        reference_display_label="Fabricated unrecorded Author",
    )
    subject = SimpleNamespace(
        artifact_subject_id=ASSOCIATION_ID,
        reference_display_label="Fabricated unrecorded Subject",
    )
    monkeypatch.setattr(menu, "_latest", lambda _activity: activity)
    monkeypatch.setattr(menu, "_choose_artifact", lambda *a, **kw: artifact)
    monkeypatch.setattr(menu, "_choose_author", lambda *a, **kw: author)
    monkeypatch.setattr(menu, "_choose_subject", lambda *a, **kw: subject)
    monkeypatch.setattr(menu, "_author_status", lambda: "confirmed")
    monkeypatch.setattr(menu, "_subject_status", lambda: "confirmed")
    monkeypatch.setattr(menu, "prompt_text", lambda *a, **kw: "issue140-3c-correction")
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: approve)
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda *a, **kw: pytest.fail("Unexpected result presentation"),
    )
    monkeypatch.setattr(
        menu,
        "_choose_author_semantics",
        lambda *a, **kw: (
            None,
            "teacher_author",
            "proposed",
            "manual",
            None,
            None,
            None,
        ),
    )
    monkeypatch.setattr(
        menu,
        "_choose_subject_semantics",
        lambda *a, **kw: (
            reference,
            "observed_participant",
            "proposed",
            "manual",
            None,
        ),
    )
    monkeypatch.setattr(menu, "_require_workspace", lambda: root)
    monkeypatch.setattr(
        menu,
        "choose_students",
        lambda selected_root, class_id: (
            SimpleNamespace(student_id=students[0]),
            SimpleNamespace(student_id=students[1]),
        ),
    )
    monkeypatch.setattr(menu, "_routine_multi_author_mode", lambda: "individual_author")
    monkeypatch.setattr(
        menu, "_routine_multi_subject_role", lambda: "observed_participant"
    )
    monkeypatch.setattr(menu, "_routine_add_status", lambda **kw: "proposed")

    handlers = {
        "update_author": partial(menu._update_author, activity, state),
        "correct_author": partial(menu._correct_author, activity, state),
        "update_subject": partial(menu._update_subject, activity, state),
        "correct_subject": partial(menu._correct_subject, activity, state),
        "multi_author": partial(menu._add_multiple_authors, activity, state),
        "multi_subject": partial(menu._add_multiple_subjects, activity, state),
        "batch_confirm": partial(
            menu._commit_attribution_confirmation,
            activity,
            SimpleNamespace(
                snapshot_revision=activity.snapshot_revision, exception_count=0
            ),
            state,
            artifact_author_ids=(ASSOCIATION_ID,),
            artifact_subject_ids=(),
            unselected_candidate_count=0,
        ),
    }
    service_name, service = SERVICES[kind]

    def real_service(request: Any) -> Any:
        captured.append(request)
        return service(request, workspace_root=root)

    monkeypatch.setattr(menu, service_name, real_service)
    handlers[kind]()


@pytest.mark.parametrize("kind", KINDS)
def test_mixed_menu_write_hits_standards_guard_before_missing_relationship(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    before_graph = load_current_record_graph(
        fixture.root, _work(), standards_library=fixture.standards
    ).graph
    before_snapshots = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []

    with pytest.raises(
        Exception, match="standards_library is required for this Activity"
    ):
        _exercise(
            kind=kind,
            activity=activity,
            root=fixture.root,
            students=fixture.source.students,
            monkeypatch=monkeypatch,
            captured=captured,
        )
    assert len(captured) == 1, "Teacher handler did not reach its intended real service"
    assert captured[0].class_id == SOURCE_CLASS
    assert captured[0].activity_id == ACTIVITY_ID
    assert captured[0].expected_snapshot_revision == activity.snapshot_revision

    # Exact same request, now given the authoritative Library, must cross the
    # Standards gate before rejecting the deliberately nonexistent target.
    service = SERVICES[kind][1]
    with pytest.raises(Exception) as failure:
        service(
            captured[0],
            workspace_root=fixture.root,
            standards_library=fixture.standards,
        )
    assert "standards_library" not in str(failure.value)
    assert isinstance(failure.value, Exception)
    assert list_work_snapshots(fixture.root, _work()) == before_snapshots
    assert (
        load_current_record_graph(
            fixture.root, _work(), standards_library=fixture.standards
        ).graph
        == before_graph
    )


@pytest.mark.parametrize("kind", ("update_author", "multi_subject", "batch_confirm"))
def test_neutral_mode_reaches_missing_target_without_standards_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="evidence_only")
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    before = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    with pytest.raises(Exception) as failure:
        _exercise(
            kind=kind,
            activity=activity,
            root=fixture.root,
            students=fixture.source.students,
            monkeypatch=monkeypatch,
            captured=captured,
        )
    assert len(captured) == 1
    assert "standards_library" not in str(failure.value)
    assert list_work_snapshots(fixture.root, _work()) == before


@pytest.mark.parametrize("kind", ("multi_author", "multi_subject", "batch_confirm"))
def test_cancel_before_attribution_commit_does_not_call_service(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fixture = build_workspace(tmp_path, orientation="mixed")
    activity = show_activity(
        SOURCE_CLASS, ACTIVITY_ID, workspace_root=fixture.root
    ).summary
    before = list_work_snapshots(fixture.root, _work())
    captured: list[Any] = []
    _exercise(
        kind=kind,
        activity=activity,
        root=fixture.root,
        students=fixture.source.students,
        monkeypatch=monkeypatch,
        captured=captured,
        approve=False,
    )
    assert captured == []
    assert list_work_snapshots(fixture.root, _work()) == before
