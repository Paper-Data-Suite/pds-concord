"""#148 3E6A: actor-exact Activity copy/edit, legacy COPY retained.

Synthetic-only: no actual student, teacher-profile or workspace data.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_activity
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]


def _fn(name: str) -> ast.FunctionDef:
    tree = ast.parse((ROOT / "concord/menu_activity.py").read_text(encoding="utf-8"))
    return next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
    )


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == name
    ]


def test_copy_uses_actor_from_review_and_preserves_special_copy_confirmation() -> None:
    fn = _fn("_copy_activity")
    reviewed = _calls(fn, "confirm_actor_write")
    write = _calls(fn, "copy_activity")
    request = _calls(fn, "CopyActivityRequest")
    assert len(reviewed) == len(write) == len(request) == 1
    assert reviewed[0].lineno < write[0].lineno
    assert write[0].args == [request[0]]
    actor = next(k.value for k in request[0].keywords if k.arg == "actor")
    assert isinstance(actor, ast.Name) and actor.id == "actor"
    confirm = next(k.value for k in reviewed[0].keywords if k.arg == "legacy_confirm")
    assert isinstance(confirm, ast.Lambda)
    assert len(_calls(confirm, "_confirm_copy")) == 1
    assert not any(
        isinstance(n, ast.Attribute) and n.attr == "require_actor" for n in ast.walk(fn)
    )


def test_edit_uses_reviewed_actor_before_workflow_write() -> None:
    fn = _fn("_update_activity_field")
    reviewed = _calls(fn, "confirm_actor_write")
    write = _calls(fn, "update_activity")
    assert len(reviewed) == len(write) == 1
    assert reviewed[0].lineno < write[0].lineno
    assert not _calls(fn, "confirm_write")
    sets = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Assign)
        and any(
            isinstance(t, ast.Subscript)
            and isinstance(t.value, ast.Name)
            and t.value.id == "values"
            and isinstance(t.slice, ast.Constant)
            and t.slice.value == "actor"
            for t in n.targets
        )
    ]
    assert len(sets) == 1
    assert reviewed[0].lineno < sets[0].lineno < write[0].lineno
    assert isinstance(sets[0].value, ast.Name) and sets[0].value.id == "actor"


@pytest.mark.parametrize("approved", [True, False])
def test_copy_exact_actor_or_cancel_without_write(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    default = WorkflowActor(actor_id="default-adult", display_label="Default Adult")
    alternate = WorkflowActor(
        actor_id="alternate-adult", display_label="Alternate Adult"
    )
    state = MenuSessionContext(actor=default)
    source = SimpleNamespace(
        class_id="class-src", activity_id="activity-src", title="Source", status="draft"
    )
    target = SimpleNamespace(class_id="class-target")
    detail = SimpleNamespace(summary=source, description="Existing description")
    saved: list[Any] = []
    monkeypatch.setattr(
        menu_activity, "resolve_read_workspace_root", lambda: Path("/synthetic")
    )
    monkeypatch.setattr(menu_activity, "list_available_classes", lambda *_a: (target,))
    monkeypatch.setattr(menu_activity, "list_activities", lambda **_k: (source,))
    monkeypatch.setattr(menu_activity, "select_one", lambda *_a, **_k: source)
    monkeypatch.setattr(menu_activity, "show_activity", lambda *_a, **_k: detail)
    monkeypatch.setattr(menu_activity, "choose_class", lambda *_a: target)
    monkeypatch.setattr(menu_activity, "_copy_title", lambda *_a: "Copied title")
    monkeypatch.setattr(menu_activity, "_copy_description", lambda *_a: None)
    monkeypatch.setattr(
        menu_activity,
        "prompt_text",
        lambda _t, name, **_k: (
            "activity-copy"
            if name == "New Activity ID"
            else "session-copy"
            if name == "First Session ID"
            else None
        ),
    )
    monkeypatch.setattr(menu_activity, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        menu_activity,
        "prepare_activity_copy",
        lambda *_a, **_k: SimpleNamespace(review_digest="d" * 64),
    )
    monkeypatch.setattr(
        menu_activity, "_copy_review_lines", lambda *_a, **_k: ("Copy review",)
    )
    monkeypatch.setattr(
        menu_activity,
        "_confirm_copy",
        lambda *_a: pytest.fail("COPY confirmation bypassed by mock"),
    )
    monkeypatch.setattr(
        menu_activity,
        "confirm_actor_write",
        lambda *_a, **_k: alternate if approved else None,
    )
    monkeypatch.setattr(
        menu_activity, "CopyActivityRequest", lambda **kw: SimpleNamespace(**kw)
    )
    monkeypatch.setattr(
        menu_activity,
        "copy_activity",
        lambda request, **_k: (
            saved.append(request)
            or SimpleNamespace(
                activity_id="activity-copy",
                first_session_id="session-copy",
                commit=SimpleNamespace(snapshot_revision=1),
            )
        ),
    )

    def show_copy_result(title: str, lines: object) -> None:
        if title == "Activity Copy Error":
            pytest.fail(f"Unexpected Activity Copy Error: {lines!r}")

    monkeypatch.setattr(menu_activity, "show_result", show_copy_result)
    monkeypatch.setattr(
        menu_activity,
        "show_partial_success",
        lambda *_a: pytest.fail("Unexpected partial success"),
    )
    menu_activity._copy_activity(state)
    assert len(saved) == int(approved)
    if saved:
        assert saved[0].actor == alternate
        assert saved[0].source_class_id == "class-src"
        assert saved[0].review_digest == "d" * 64
    assert state.actor == default


@pytest.mark.parametrize("approved", [True, False])
def test_edit_exact_actor_or_cancel_without_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, approved: bool
) -> None:
    default = WorkflowActor(actor_id="default-adult", display_label="Default Adult")
    alternate = WorkflowActor(
        actor_id="alternate-adult", display_label="Alternate Adult"
    )
    state = MenuSessionContext(actor=default)
    current = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Existing",
        scoring_orientation="evidence_only",
        status="draft",
        snapshot_revision=4,
    )
    detail = SimpleNamespace(summary=current, description="Existing description")
    saved: list[Any] = []
    monkeypatch.setattr(menu_activity, "resolve_read_workspace_root", lambda: tmp_path)
    monkeypatch.setattr(menu_activity, "show_activity", lambda *_a, **_k: detail)
    monkeypatch.setattr(menu_activity, "prompt_text", lambda *_a, **_k: "Updated")
    monkeypatch.setattr(
        menu_activity,
        "confirm_actor_write",
        lambda *_a, **_k: alternate if approved else None,
    )
    monkeypatch.setattr(
        menu_activity,
        "confirm_write",
        lambda *_a, **_k: pytest.fail("Unexpected legacy confirmation"),
    )
    monkeypatch.setattr(
        menu_activity,
        "_load_activity_context",
        lambda *_a, **_k: SimpleNamespace(
            root=tmp_path,
            snapshot_revision=4,
            graph=SimpleNamespace(criteria=(), score_records=()),
        ),
    )
    monkeypatch.setattr(
        menu_activity, "UpdateActivityRequest", lambda **kw: SimpleNamespace(**kw)
    )
    monkeypatch.setattr(
        menu_activity,
        "update_activity",
        lambda request, **_k: (
            saved.append(request)
            or SimpleNamespace(
                activity_id="activity-synthetic",
                commit=SimpleNamespace(no_op=False, snapshot_revision=5),
            )
        ),
    )
    monkeypatch.setattr(
        menu_activity, "handle_write_error", lambda exc, **_k: pytest.fail(str(exc))
    )
    monkeypatch.setattr(menu_activity, "show_result", lambda *_a, **_k: None)
    menu_activity._update_activity_field(current, state, "title")
    assert len(saved) == int(approved)
    if saved:
        assert saved[0].actor == alternate
        assert saved[0].title == "Updated"
        assert saved[0].expected_snapshot_revision == 4
    assert state.actor == default
