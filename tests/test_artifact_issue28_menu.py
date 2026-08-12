from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from concord import menu_artifact
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.workflows import ActivitySummary, WorkflowActor


def _activity() -> ActivitySummary:
    return cast(
        ActivitySummary,
        SimpleNamespace(
            title="Issue 28 Menu",
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=7,
        ),
    )


def test_artifact_menu_preserves_issue27_choices_and_adds_issue28_surfaces(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": "B")
    menu_artifact.launch_artifact_page_menu(
        _activity(),
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    output = capsys.readouterr().out
    assert "1. Prepare Artifact Pages" in output
    assert "2. List / inspect Artifact Pages" in output
    assert "3. Render prepared pages" in output
    assert "4. List / inspect Artifacts" in output
    assert "5. Assemble returned Artifact" in output
    assert "6. Authors" in output
    assert "7. Subjects" in output


@pytest.mark.parametrize(("key", "expected"), (("M", ReturnToMainMenu), ("Q", QuitPDS)))
def test_author_nested_navigation_unwinds(
    key: str,
    expected: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_status="returned",
        returned_required_page_count=1,
        required_return_page_count=1,
    )
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "list_artifacts",
        lambda *_args, **_kwargs: (artifact,),
    )
    answers = iter(("6", "2", key))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    with pytest.raises(expected):
        menu_artifact.launch_artifact_page_menu(
            _activity(),
            MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
        )
    assert "Artifact Author Error" not in capsys.readouterr().out


def test_unknown_author_menu_creates_reference_free_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_status="returned",
        returned_required_page_count=1,
        required_return_page_count=1,
    )
    captured = []
    result = SimpleNamespace(
        association_id="author-generated",
        commit=SimpleNamespace(snapshot_revision=8),
    )
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "list_artifacts",
        lambda *_args, **_kwargs: (artifact,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "add_artifact_author",
        lambda request: captured.append(request) or result,
    )
    answers = iter(
        (
            "6",
            "2",
            "1",
            "",
            "5",
            "ADD",
            "",
            "B",
            "B",
        )
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        _activity(),
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    assert len(captured) == 1
    request = captured[0]
    assert request.author_reference is None
    assert request.authorship_mode == "unknown"
    assert request.attribution_status == "unknown"
    assert request.attribution_source == "unknown"


def test_assembly_menu_selects_exact_ambiguous_occurrence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_status="returned",
        returned_required_page_count=1,
        required_return_page_count=1,
    )
    occurrences = (
        SimpleNamespace(
            artifact_page_id="page-1",
            logical_page_number=1,
            scan_reference_id="scanref-1",
            source_scan_id="scan-1",
            source_page_number=1,
        ),
        SimpleNamespace(
            artifact_page_id="page-1",
            logical_page_number=1,
            scan_reference_id="scanref-2",
            source_scan_id="scan-2",
            source_page_number=1,
        ),
    )
    captured = []
    result = SimpleNamespace(
        artifact_instance_id="artifact-1",
        assembly_id="assembly-1",
        page_count=1,
        output_path=SimpleNamespace(name="artifact.pdf"),
        reused=False,
    )
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "list_artifacts",
        lambda *_args, **_kwargs: (artifact,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "list_artifact_scan_occurrences",
        lambda *_args, **_kwargs: occurrences,
    )
    monkeypatch.setattr(
        menu_artifact,
        "assemble_returned_artifact",
        lambda request: captured.append(request) or result,
    )
    answers = iter(("5", "1", "2", "ASSEMBLE", ""))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        _activity(),
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    assert len(captured) == 1
    selections = captured[0].selections
    assert len(selections) == 1
    assert selections[0].artifact_page_id == "page-1"
    assert selections[0].scan_reference_id == "scanref-2"
def test_subject_menu_adds_group_subject_without_collapsing_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_status="returned",
        returned_required_page_count=1,
        required_return_page_count=1,
    )
    group = SimpleNamespace(group_id="group-a", label="Group A")
    captured = []
    result = SimpleNamespace(
        association_id="subject-generated",
        commit=SimpleNamespace(snapshot_revision=8),
    )
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "list_artifacts",
        lambda *_args, **_kwargs: (artifact,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "list_groups",
        lambda *_args, **_kwargs: (group,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "add_artifact_subject",
        lambda request: captured.append(request) or result,
    )
    answers = iter(
        (
            "7",
            "2",
            "1",
            "",
            "2",
            "1",
            "",
            "",
            "1",
            "ADD",
            "",
            "B",
            "B",
        )
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        _activity(),
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    assert len(captured) == 1
    request = captured[0]
    assert request.subject_reference.subject_kind == "concord_group"
    assert request.subject_reference.subject_id == "group-a"
    assert request.subject_role == "represented_group"


def test_coauthor_and_recorder_for_group_menu_flows_are_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        artifact_status="returned",
        returned_required_page_count=1,
        required_return_page_count=1,
    )
    student = SimpleNamespace(student_id="student-1")
    group = SimpleNamespace(group_id="group-a", label="Group A")
    captured = []
    results = iter(
        (
            SimpleNamespace(
                association_id="author-co",
                commit=SimpleNamespace(snapshot_revision=8),
            ),
            SimpleNamespace(
                association_id="author-recorder",
                commit=SimpleNamespace(snapshot_revision=9),
            ),
        )
    )
    monkeypatch.setattr(menu_artifact, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        menu_artifact,
        "list_artifacts",
        lambda *_args, **_kwargs: (artifact,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "choose_student",
        lambda *_args, **_kwargs: student,
    )
    monkeypatch.setattr(
        menu_artifact,
        "_require_workspace",
        lambda: Path("."),
    )
    monkeypatch.setattr(
        menu_artifact,
        "list_groups",
        lambda *_args, **_kwargs: (group,),
    )
    monkeypatch.setattr(
        menu_artifact,
        "add_artifact_author",
        lambda request: captured.append(request) or next(results),
    )
    answers = iter(
        (
            "6",
            "2",
            "1",
            "",
            "1",
            "2",
            "",
            "1",
            "ADD",
            "",
            "2",
            "1",
            "",
            "1",
            "5",
            "1",
            "2",
            "",
            "1",
            "ADD",
            "",
            "B",
            "B",
        )
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        _activity(),
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1")),
    )
    assert len(captured) == 2
    assert captured[0].authorship_mode == "co_author"
    assert captured[1].authorship_mode == "recorder_for_group"
    assert captured[1].represented_group_id == "group-a"
    assert captured[1].representation_status == "recorder_summary"
