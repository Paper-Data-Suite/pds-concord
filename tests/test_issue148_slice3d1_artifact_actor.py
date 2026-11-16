"""Issue #148 Slice 3D1: reviewed direct Artifact/Subject write boundaries.

No classroom data or filesystem writes; the runtime tests substitute canonical
services with synthetic captures. Existing menu confirmations remain available
for explicit legacy MenuSessionContext callers.
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
    ("_prepare", "PrepareArtifactPagesRequest"),
    ("_render", "RenderArtifactPagesRequest"),
    ("_assemble", "AssembleArtifactRequest"),
    ("_add_subject", "AddArtifactSubjectRequest"),
    ("_update_subject", "UpdateArtifactSubjectRequest"),
    ("_correct_subject", "ReplaceArtifactSubjectRequest"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


@pytest.mark.parametrize(("function", "request_name"), TARGETS)
def test_reviewed_actor_is_forwarded_to_exact_artifact_request(
    function: str, request_name: str
) -> None:
    tree = ast.parse((ROOT / "concord/menu_artifact.py").read_text(encoding="utf-8"))
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ]
    assert len(matches) == 1
    fn = matches[0]
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_name)
    assert len(reviews) == len(requests) == 1
    assert not _calls(fn, "confirm_write")
    review = reviews[0]
    assert review.lineno < requests[0].lineno
    args = {kw.arg: kw.value for kw in review.keywords}
    assert set(args) == {"state", "legacy_confirm"}
    assert isinstance(args["state"], ast.Name) and args["state"].id == "state"
    assert isinstance(args["legacy_confirm"], ast.Name)
    assert args["legacy_confirm"].id == "confirm_write"
    actors = [kw.value for kw in requests[0].keywords if kw.arg == "actor"]
    assert len(actors) == 1
    assert isinstance(actors[0], ast.Name) and actors[0].id == "actor"
    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "actor"
        and isinstance(node.test.ops[0], ast.Is)
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value is None
        for node in ast.walk(fn)
    )


@pytest.mark.parametrize("reviewed", [True, False])
def test_prepare_uses_only_reviewed_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch, reviewed: bool
) -> None:
    default = WorkflowActor(actor_id="adult-default")
    chosen = WorkflowActor(actor_id="adult-reviewed", display_label="Other Adult")
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="class-one",
        activity_id="activity-one",
        title="Synthetic Activity",
        snapshot_revision=1,
    )
    captured: list[Any] = []
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda _title, label, **_kwargs: (
            "artifact-one" if label == "Artifact Instance ID" else "template-one"
        ),
    )
    monkeypatch.setattr(menu, "prompt_positive_int", lambda *_a, **_k: 1)
    monkeypatch.setattr(
        menu,
        "confirm_actor_write",
        lambda *_a, **_k: chosen if reviewed else None,
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: True)

    def save(request: Any) -> Any:
        captured.append(request)
        return SimpleNamespace(
            artifact_instance_id="artifact-one",
            routes_verified=1,
            routes_expected=1,
            commit=SimpleNamespace(snapshot_revision=2),
        )

    monkeypatch.setattr(menu, "prepare_artifact_pages", save)
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    menu._prepare(activity, state)
    assert len(captured) == (1 if reviewed else 0)
    if reviewed:
        assert captured[0].actor == chosen
    assert state.actor == default


@pytest.mark.parametrize("reviewed", [True, False])
def test_render_uses_exact_reviewed_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch, reviewed: bool
) -> None:
    default = WorkflowActor(actor_id="adult-default")
    chosen = WorkflowActor(actor_id="adult-reviewed", display_label="Other Adult")
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="class-one",
        activity_id="activity-one",
        title="Synthetic Activity",
        snapshot_revision=1,
    )
    captured: list[Any] = []
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_k: "artifact-one")
    monkeypatch.setattr(
        menu,
        "confirm_actor_write",
        lambda *_a, **_k: chosen if reviewed else None,
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: True)

    def save(request: Any) -> Any:
        captured.append(request)
        return SimpleNamespace(
            artifact_instance_id="artifact-one",
            page_count=1,
            output_path=Path("synthetic-render.pdf"),
        )

    monkeypatch.setattr(menu, "render_artifact_pages", save)
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    menu._render(activity, state)
    assert len(captured) == (1 if reviewed else 0)
    if reviewed:
        assert captured[0].actor == chosen
    assert state.actor == default
