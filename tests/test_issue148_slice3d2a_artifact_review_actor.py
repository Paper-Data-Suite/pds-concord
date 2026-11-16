"""Issue #148 Slice 3D2A: reviewed Artifact status, Review, Moderation writes.

Regression tests use synthetic requests and no academic workspace or student data.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_artifact as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("_update_author", "UpdateArtifactAuthorRequest", False),
    ("_quick_review_selected", "record_routine_artifact_review", True),
    ("_record_review_selected", "AddArtifactReviewRequest", True),
    ("_replace_review", "ReplaceArtifactReviewRequest", False),
    ("_record_moderation", "AddModerationRecordRequest", False),
    ("_replace_moderation", "ReplaceModerationRecordRequest", False),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


@pytest.mark.parametrize(("function", "request_name", "returns_bool"), TARGETS)
def test_artifact_review_and_moderation_bind_one_actor_to_one_service(
    function: str, request_name: str, returns_bool: bool
) -> None:
    source = (ROOT / "concord/menu_artifact.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    fns = [
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ]
    assert len(fns) == 1
    fn = fns[0]
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_name)
    assert len(reviews) == len(requests) == 1
    assert not _calls(fn, "confirm_write")
    assert reviews[0].lineno < requests[0].lineno
    args = {kw.arg: kw.value for kw in reviews[0].keywords}
    assert set(args) == {"state", "legacy_confirm"}
    assert isinstance(args["state"], ast.Name) and args["state"].id == "state"
    assert isinstance(args["legacy_confirm"], ast.Name)
    assert args["legacy_confirm"].id == "confirm_write"
    actor_values = [kw.value for kw in requests[0].keywords if kw.arg == "actor"]
    assert len(actor_values) == 1
    assert isinstance(actor_values[0], ast.Name) and actor_values[0].id == "actor"
    cancellation = [
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
    assert len(cancellation) == 1
    assert len(cancellation[0].body) == 1
    assert isinstance(cancellation[0].body[0], ast.Return)
    value = cancellation[0].body[0].value
    if returns_bool:
        assert isinstance(value, ast.Constant) and value.value is False
    else:
        assert value is None


def _synthetic() -> tuple[SimpleNamespace, MenuSessionContext, WorkflowActor]:
    default = WorkflowActor(actor_id="adult-default")
    chosen = WorkflowActor(actor_id="adult-reviewed", display_label="Second Adult")
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=2,
    )
    return activity, MenuSessionContext(actor=default), chosen


@pytest.mark.parametrize("approved", (True, False))
def test_update_author_uses_reviewed_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    current, state, chosen = _synthetic()
    captured: list[Any] = []
    monkeypatch.setattr(menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        menu, "begin_artifact_write_context", lambda *_a, **_k: object()
    )
    monkeypatch.setattr(
        menu,
        "_choose_author",
        lambda *_a, **_k: SimpleNamespace(
            artifact_author_id="author-synthetic", reference_display_label="Student"
        ),
    )
    monkeypatch.setattr(menu, "_author_status", lambda: "confirmed")
    monkeypatch.setattr(
        menu, "confirm_actor_write", lambda *_a, **_k: chosen if approved else None
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: True)
    monkeypatch.setattr(
        menu, "revalidate_artifact_write_context", lambda *_a, **_k: object()
    )
    monkeypatch.setattr(menu, "artifact_write_kwargs", lambda *_a, **_k: {})
    monkeypatch.setattr(
        menu, "UpdateArtifactAuthorRequest", lambda **kw: SimpleNamespace(**kw)
    )
    monkeypatch.setattr(
        menu, "update_artifact_author", lambda request, **_kw: captured.append(request)
    )
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    menu._update_author(current, state)
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == chosen
    assert state.actor.actor_id == "adult-default"


@pytest.mark.parametrize("approved", (True, False))
def test_quick_review_preserves_boolean_receipt_and_reviewed_actor(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    current, state, chosen = _synthetic()
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-synthetic", snapshot_revision=2
    )
    context = SimpleNamespace(
        snapshot_revision=2,
        snapshot_sha256="abc123",
        eligibility=SimpleNamespace(quick_review_eligible=True),
    )
    snapshot = SimpleNamespace(
        snapshot_revision=2, snapshot_sha256="abc123", root=Path("synthetic")
    )
    captured: list[WorkflowActor] = []
    monkeypatch.setattr(
        menu, "begin_artifact_write_context", lambda *_a, **_kw: snapshot
    )
    monkeypatch.setattr(
        menu,
        "select_one",
        lambda title, *_a, **_kw: "continue" if title.endswith("Evidence") else "ready",
    )
    monkeypatch.setattr(
        menu, "inspect_artifact_routine_review", lambda *_a, **_kw: context
    )
    monkeypatch.setattr(menu, "routine_ready_review_values", lambda: object())
    monkeypatch.setattr(menu, "_routine_review_value_lines", lambda _v: ("synthetic",))
    monkeypatch.setattr(
        menu, "confirm_actor_write", lambda *_a, **_kw: chosen if approved else None
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_kw: True)
    monkeypatch.setattr(
        menu, "revalidate_artifact_write_context", lambda *_a, **_kw: object()
    )
    monkeypatch.setattr(menu, "artifact_write_kwargs", lambda *_a, **_kw: {})
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_kw: None)

    def recorded(
        _context: Any, _values: Any, *, actor: WorkflowActor, **_kw: Any
    ) -> Any:
        captured.append(actor)
        return SimpleNamespace(
            artifact_review_id="review-synthetic",
            commit=SimpleNamespace(snapshot_revision=3),
        )

    monkeypatch.setattr(menu, "record_routine_artifact_review", recorded)
    assert menu._quick_review_selected(current, artifact, state) is approved
    assert captured == ([chosen] if approved else [])
    assert state.actor.actor_id == "adult-default"


@pytest.mark.parametrize("approved", (True, False))
def test_record_moderation_uses_reviewed_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    current, state, chosen = _synthetic()
    captured: list[Any] = []
    evidence = SimpleNamespace(
        owning_system="concord", evidence_kind="artifact", record_id="art-1"
    )
    monkeypatch.setattr(menu, "_latest", lambda _activity: current)
    monkeypatch.setattr(
        menu, "begin_artifact_write_context", lambda *_a, **_kw: object()
    )
    monkeypatch.setattr(
        menu, "_choose_moderation_evidence", lambda *_a, **_kw: evidence
    )
    monkeypatch.setattr(menu, "_choose_moderation_subjects", lambda *_a, **_kw: ())
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_kw: "moderation-synthetic")
    monkeypatch.setattr(
        menu,
        "_moderation_values",
        lambda: (
            "accepted",
            "allow",
            "Reason",
            None,
            SimpleNamespace(classification="teacher_restricted"),
        ),
    )
    monkeypatch.setattr(
        menu, "confirm_actor_write", lambda *_a, **_kw: chosen if approved else None
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_kw: True)
    monkeypatch.setattr(
        menu, "revalidate_artifact_write_context", lambda *_a, **_kw: object()
    )
    monkeypatch.setattr(menu, "artifact_write_kwargs", lambda *_a, **_kw: {})
    monkeypatch.setattr(
        menu, "AddModerationRecordRequest", lambda **kw: SimpleNamespace(**kw)
    )
    monkeypatch.setattr(
        menu,
        "add_moderation_record",
        lambda request, **_kw: (
            captured.append(request)
            or SimpleNamespace(
                moderation_record_id="moderation-synthetic",
                commit=SimpleNamespace(snapshot_revision=3),
            )
        ),
    )
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_kw: None)
    menu._record_moderation(current, state)
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == chosen
    assert state.actor.actor_id == "adult-default"
