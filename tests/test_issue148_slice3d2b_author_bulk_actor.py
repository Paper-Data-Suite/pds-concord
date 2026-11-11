"""#148 Slice 3D2B: reviewed Author/recorder separation and bulk attribution.

Synthetic-only assertions: no academic workspace, students, or durable records.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_artifact as menu
from concord.menu_context import MenuSessionContext
from concord.models import ActorReference
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("_add_author", "AddArtifactAuthorRequest"),
    ("_correct_author", "ReplaceArtifactAuthorRequest"),
    ("_commit_attribution_confirmation", "BatchConfirmArtifactAttributionRequest"),
    ("_add_multiple_authors", "AddArtifactAuthorsRequest"),
    ("_add_multiple_subjects", "AddArtifactSubjectsRequest"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


@pytest.mark.parametrize(("name", "request_type"), TARGETS)
def test_exact_reviewed_actor_reaches_one_canonical_artifact_request(
    name: str, request_type: str
) -> None:
    module = ast.parse((ROOT / "concord/menu_artifact.py").read_text(encoding="utf-8"))
    (fn,) = (
        item
        for item in module.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_type)
    assert len(reviews) == len(requests) == 1
    assert reviews[0].lineno < requests[0].lineno
    assert not _calls(fn, "confirm_write")
    review_keywords = {item.arg: item.value for item in reviews[0].keywords}
    assert set(review_keywords) == {"state", "legacy_confirm"}
    assert isinstance(review_keywords["state"], ast.Name)
    assert review_keywords["state"].id == "state"
    assert isinstance(review_keywords["legacy_confirm"], ast.Name)
    assert review_keywords["legacy_confirm"].id == "confirm_write"
    actor_values = [kw.value for kw in requests[0].keywords if kw.arg == "actor"]
    assert len(actor_values) == 1
    assert isinstance(actor_values[0], ast.Name)
    assert actor_values[0].id == "actor"
    cancellations = [
        node
        for node in ast.walk(fn)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "actor"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Is)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value is None
    ]
    assert len(cancellations) == 1
    assert len(cancellations[0].body) == 1
    assert isinstance(cancellations[0].body[0], ast.Return)
    assert cancellations[0].body[0].value is None


def _synthetic() -> tuple[SimpleNamespace, MenuSessionContext, WorkflowActor]:
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=7,
    )
    state = MenuSessionContext(
        actor=WorkflowActor(
            actor_id="teacher-original", display_label="Original Teacher"
        )
    )
    alternate = WorkflowActor(actor_id="adult-recorder", display_label="Second Adult")
    return activity, state, alternate


@pytest.mark.parametrize("approved", (True, False))
@pytest.mark.parametrize("operation", ("_add_author", "_correct_author"))
def test_current_teacher_author_does_not_become_alternate_recorder(
    monkeypatch: pytest.MonkeyPatch, approved: bool, operation: str
) -> None:
    activity, state, alternate = _synthetic()
    original_author = ActorReference(
        actor_kind="authorized_adult",
        actor_id="teacher-original",
        owning_system="concord",
        display_label_snapshot="Original Teacher",
    )
    captured: list[Any] = []
    review_lines: list[str] = []
    patch = monkeypatch.setattr
    patch(menu, "_latest", lambda _activity: activity)
    patch(menu, "begin_artifact_write_context", lambda *_a, **_k: object())
    patch(menu, "revalidate_artifact_write_context", lambda *_a, **_k: object())
    patch(menu, "artifact_write_kwargs", lambda *_a, **_k: {})
    patch(
        menu,
        "_choose_artifact",
        lambda *_a, **_k: SimpleNamespace(
            artifact_status="ready", artifact_instance_id="artifact-synthetic"
        ),
    )
    patch(
        menu,
        "_choose_author",
        lambda *_a, **_k: SimpleNamespace(artifact_author_id="author-existing"),
    )
    patch(menu, "prompt_text", lambda *_a, **_k: "synthetic-identifier")
    patch(
        menu,
        "_choose_author_semantics",
        lambda *_a, **_k: (
            original_author,
            "teacher_author",
            "confirmed",
            "teacher",
            None,
            None,
            None,
        ),
    )

    def reviewed(_title: str, _expected: str, lines: Any, **_kw: Any) -> Any:
        review_lines.extend(lines)
        return alternate if approved else None

    patch(menu, "confirm_actor_write", reviewed)
    patch(menu, "confirm_write", lambda *_a, **_k: True)
    patch(menu, "AddArtifactAuthorRequest", lambda **kw: SimpleNamespace(**kw))
    patch(menu, "ReplaceArtifactAuthorRequest", lambda **kw: SimpleNamespace(**kw))
    patch(menu, "add_artifact_author", lambda request, **_kw: captured.append(request))
    patch(
        menu,
        "replace_artifact_author",
        lambda request, **_kw: captured.append(request),
    )
    patch(menu, "show_result", lambda *_a, **_k: None)
    getattr(menu, operation)(activity, state)
    assert "Author Actor ID: teacher-original" in review_lines
    assert any(
        "Recorded by" in item and "does not change" in item for item in review_lines
    )
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == alternate
        assert captured[0].author_reference == original_author
    assert state.actor.actor_id == "teacher-original"


def test_non_actor_author_does_not_acquire_a_fabricated_actor_identity() -> None:
    assert menu._author_identity_review(None, "unknown") == ()
    assert menu._author_identity_review(None, "collective_group_author") == ()


@pytest.mark.parametrize("approved", (True, False))
def test_bulk_author_addition_keeps_reviewed_recorder_and_original_students(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    activity, state, alternate = _synthetic()
    captured: list[Any] = []
    patch = monkeypatch.setattr
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-synthetic", snapshot_revision=7
    )
    patch(menu, "_latest", lambda _activity: activity)
    patch(
        menu,
        "begin_artifact_write_context",
        lambda *_a, **_k: SimpleNamespace(root=Path("synthetic")),
    )
    patch(menu, "_choose_artifact", lambda *_a, **_k: artifact)
    patch(
        menu,
        "choose_students",
        lambda *_a, **_k: (
            SimpleNamespace(student_id="student-1"),
            SimpleNamespace(student_id="student-2"),
        ),
    )
    patch(menu, "_routine_multi_author_mode", lambda: "individual")
    patch(menu, "_routine_add_status", lambda **_kw: "confirmed")
    patch(
        menu,
        "confirm_actor_write",
        lambda *_a, **_k: alternate if approved else None,
    )
    patch(menu, "confirm_write", lambda *_a, **_k: True)
    patch(menu, "revalidate_artifact_write_context", lambda *_a, **_kw: object())
    patch(menu, "artifact_write_kwargs", lambda *_a, **_k: {})
    patch(menu, "AddArtifactAuthorsRequest", lambda **kw: SimpleNamespace(**kw))
    patch(
        menu,
        "add_artifact_authors",
        lambda request, **_kw: (
            captured.append(request)
            or SimpleNamespace(
                artifact_author_ids=("author-1", "author-2"),
                commit=SimpleNamespace(snapshot_revision=8),
            )
        ),
    )
    patch(menu, "show_result", lambda *_a, **_k: None)
    menu._add_multiple_authors(activity, state)
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].student_ids == ("student-1", "student-2")
        assert captured[0].actor == alternate
    assert state.actor.actor_id == "teacher-original"


@pytest.mark.parametrize("approved", (True, False))
def test_bulk_confirmation_uses_reviewed_recorder_and_never_reselects(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    activity, state, alternate = _synthetic()
    review = SimpleNamespace(
        class_id=activity.class_id,
        activity_id=activity.activity_id,
        snapshot_revision=7,
        snapshot_sha256="snapshot-sha",
        exception_count=0,
    )
    captured: list[Any] = []
    patch = monkeypatch.setattr
    patch(menu, "_latest", lambda _activity: activity)
    patch(
        menu,
        "begin_artifact_write_context",
        lambda *_a, **_k: SimpleNamespace(
            snapshot_revision=7, snapshot_sha256="snapshot-sha"
        ),
    )
    patch(
        menu,
        "confirm_actor_write",
        lambda *_a, **_k: alternate if approved else None,
    )
    patch(menu, "confirm_write", lambda *_a, **_k: True)
    patch(menu, "revalidate_artifact_write_context", lambda *_a, **_k: object())
    patch(menu, "artifact_write_kwargs", lambda *_a, **_k: {})
    patch(
        menu,
        "BatchConfirmArtifactAttributionRequest",
        lambda **kw: SimpleNamespace(**kw),
    )
    patch(
        menu,
        "batch_confirm_artifact_attribution",
        lambda request, **_kw: (
            captured.append(request)
            or SimpleNamespace(
                confirmed_author_count=1,
                confirmed_subject_count=1,
                commit=SimpleNamespace(snapshot_revision=8),
            )
        ),
    )
    patch(menu, "show_result", lambda *_a, **_k: None)
    menu._commit_attribution_confirmation(
        activity,
        review,
        state,
        artifact_author_ids=("author-1",),
        artifact_subject_ids=("subject-1",),
        unselected_candidate_count=0,
    )
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == alternate
        assert captured[0].artifact_author_ids == ("author-1",)
        assert captured[0].artifact_subject_ids == ("subject-1",)
    assert state.actor.actor_id == "teacher-original"
