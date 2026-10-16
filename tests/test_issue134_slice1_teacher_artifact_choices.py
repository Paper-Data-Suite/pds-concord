"""Slice 1: teacher display without inferred identity or extra graph loads."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord.workflows import artifact as artifact_workflow
from concord.workflows import teacher_artifact_choices as display
from concord.workflows.errors import ConcordWorkflowConflictError


def _artifact(
    identity: str,
    *,
    group_id: str | None = "group-a",
    session_id: str | None = "session-a",
    page_ids: tuple[str, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instance_id=identity,
        activity_id="activity-one",
        artifact_category="student_work",
        generation_status="completed",
        expected_return_status="returned_expected",
        artifact_status="returned",
        group_id=group_id,
        session_id=session_id,
        page_ids=page_ids,
    )


def _graph(*artifacts: Any) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_instances=artifacts,
        artifact_pages=(),
        artifact_authors=(),
        artifact_subjects=(),
        groups=(
            SimpleNamespace(group_id="group-a", label="Blue Group"),
            SimpleNamespace(group_id="group-b", label="Blue Group"),
        ),
        sessions=(
            SimpleNamespace(session_id="session-a", sequence=1, label="Workshop"),
        ),
    )


def _build(graph: Any) -> tuple[display.TeacherArtifactChoice, ...]:
    return display.build_teacher_artifact_choices(
        graph,
        class_id="english-ten",
        activity_id="activity-one",
        snapshot_revision=4,
    )


def test_group_and_session_are_named_not_machine_identifiers() -> None:
    choices = _build(_graph(_artifact("artifact-opaque-one")))
    assert len(choices) == 1
    selected = choices[0]
    assert selected.summary.artifact_instance_id == "artifact-opaque-one"
    assert "Blue Group (group 1 of 2 with this name)" in selected.label
    assert "Session 1 - Workshop" in selected.label
    assert "returned 0/0" in selected.label
    assert "artifact-opaque-one" not in selected.label
    assert "group-a" not in selected.label


def test_duplicate_work_labels_receive_nonchronological_copy_disambiguation() -> None:
    choices = _build(
        _graph(_artifact("artifact-b"), _artifact("artifact-a"))
    )
    assert [item.summary.artifact_instance_id for item in choices] == [
        "artifact-a",
        "artifact-b",
    ]
    assert "work copy 1 of 2" in choices[0].label
    assert "work copy 2 of 2" in choices[1].label
    assert "newest" not in choices[0].label.casefold()


def test_missing_associations_are_not_fabricated() -> None:
    choices = _build(
        _graph(
            _artifact("missing-associations", group_id=None, session_id=None),
            _artifact(
                "dangling-associations",
                group_id="unknown-group",
                session_id="unknown-session",
            ),
        )
    )
    labels = {item.summary.artifact_instance_id: item.label for item in choices}
    assert "Group not recorded" in labels["missing-associations"]
    assert "Session not recorded" in labels["missing-associations"]
    assert "Group no longer in current Activity" in labels["dangling-associations"]
    assert "Session no longer in current Activity" in labels["dangling-associations"]
    assert "unknown-group" not in labels["dangling-associations"]


def test_precomputed_summary_matches_existing_artifact_summary() -> None:
    page = SimpleNamespace(
        artifact_page_id="page-one",
        artifact_instance_id="artifact-a",
        return_expected=True,
        page_status="returned",
    )
    graph = _graph(_artifact("artifact-a", page_ids=("page-one",)))
    graph.artifact_pages = (page,)
    choice = _build(graph)[0]
    old_summary = artifact_workflow._summary(
        "english-ten", "activity-one", graph.artifact_instances[0], graph, 4
    )
    assert choice.summary == old_summary
    assert "returned 1/1" in choice.label


def test_projection_reads_only_one_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []
    graph = _graph(*(_artifact(f"artifact-{n}") for n in range(40)))
    monkeypatch.setattr(display, "resolve_read_workspace_root", lambda _: Path("."))
    monkeypatch.setattr(display, "work_ref", lambda *_: "work-ref")

    def load_once(*args: object) -> tuple[Any, int, str]:
        calls.append(args)
        return graph, 4, "digest"

    monkeypatch.setattr(display, "load_graph", load_once)
    result = display.list_teacher_artifact_choices(
        "english-ten", "activity-one", expected_snapshot_revision=4
    )
    assert len(result) == 40
    assert len(calls) == 1
    assert len(set(item.label for item in result)) == 40


def test_stale_snapshot_is_not_silently_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(display, "resolve_read_workspace_root", lambda _: Path("."))
    monkeypatch.setattr(display, "work_ref", lambda *_: "work-ref")
    monkeypatch.setattr(display, "load_graph", lambda *_: (_graph(), 5, "digest"))
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        display.list_teacher_artifact_choices(
            "english-ten", "activity-one", expected_snapshot_revision=4
        )


def test_empty_workspace_has_no_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(display, "resolve_read_workspace_root", lambda _: None)
    assert display.list_teacher_artifact_choices("english-ten", "activity-one") == ()

def test_review_next_choice_uses_one_projection_and_exact_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord import menu_artifact

    activity = SimpleNamespace(
        class_id="english-ten", activity_id="activity-one", snapshot_revision=4
    )
    unrelated = SimpleNamespace(artifact_instance_id="work-b", snapshot_revision=4)
    selected = SimpleNamespace(artifact_instance_id="work-a", snapshot_revision=4)
    calls: list[tuple[str, str, int | None]] = []

    def projection(
        class_id: str, activity_id: str, *, expected_snapshot_revision: int | None
    ) -> tuple[display.TeacherArtifactChoice, ...]:
        calls.append((class_id, activity_id, expected_snapshot_revision))
        return (
            display.TeacherArtifactChoice(
                summary=unrelated, label="Group B",
                group_label="Group B", session_label="Session 1"
            ),
            display.TeacherArtifactChoice(
                summary=selected, label="Group A",
                group_label="Group A", session_label="Session 1"
            ),
        )

    monkeypatch.setattr(menu_artifact, "list_teacher_artifact_choices", projection)
    monkeypatch.setattr(
        menu_artifact,
        "_review_next_artifact_summary",
        lambda *_: pytest.fail("Review-next must not load the graph twice"),
    )
    result = menu_artifact._review_next_artifact_choice(activity, "work-a")
    assert result.summary is selected
    assert result.label == "Group A"
    assert calls == [("english-ten", "activity-one", 4)]


def test_review_next_choice_rejects_contradictory_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord import menu_artifact

    activity = SimpleNamespace(
        class_id="english-ten", activity_id="activity-one", snapshot_revision=4
    )
    stale = SimpleNamespace(artifact_instance_id="work-a", snapshot_revision=5)
    choice = display.TeacherArtifactChoice(
        summary=stale, label="Group 1", group_label="Group 1",
        session_label="Session 1"
    )
    monkeypatch.setattr(
        menu_artifact,
        "list_teacher_artifact_choices",
        lambda *args, **kwargs: (choice,),
    )
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        menu_artifact._review_next_artifact_choice(activity, "work-a")


def test_review_next_choice_missing_or_ambiguous_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord import menu_artifact
    from concord.workflows.errors import ConcordWorkflowNotFoundError

    activity = SimpleNamespace(
        class_id="english-ten", activity_id="activity-one", snapshot_revision=4
    )
    work = SimpleNamespace(artifact_instance_id="work-a", snapshot_revision=4)
    choice = display.TeacherArtifactChoice(
        summary=work, label="Group 1", group_label="Group 1",
        session_label="Session 1"
    )
    monkeypatch.setattr(
        menu_artifact, "list_teacher_artifact_choices", lambda *a, **k: ()
    )
    with pytest.raises(ConcordWorkflowNotFoundError, match="no longer available"):
        menu_artifact._review_next_artifact_choice(activity, "work-a")

    monkeypatch.setattr(
        menu_artifact, "list_teacher_artifact_choices", lambda *a, **k: (choice, choice)
    )
    with pytest.raises(ConcordWorkflowConflictError, match="not unique"):
        menu_artifact._review_next_artifact_choice(activity, "work-a")
