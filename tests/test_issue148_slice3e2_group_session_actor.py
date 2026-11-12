"""#148 3E2: synthetically qualify reviewed Group, Membership and Session writes.

The actor is the adult recorder. These tests never touch a Core workspace,
student roster, user profile, or network resource.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_group as group
import concord.menu_session as session_menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("concord/menu_group.py", "_create_group", "CreateGroupRequest"),
    ("concord/menu_group.py", "_edit_group", "UpdateGroupRequest"),
    ("concord/menu_group.py", "_add_member", "AddMembershipsRequest"),
    ("concord/menu_group.py", "_end_member", "EndMembershipRequest"),
    ("concord/menu_group.py", "_reassign_member", "ReassignMembershipRequest"),
    ("concord/menu_session.py", "_add", "CreateSessionRequest"),
    ("concord/menu_session.py", "_edit_field", "UpdateSessionRequest"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


def _actor_kw(request: ast.Call) -> ast.expr | None:
    return next((kw.value for kw in request.keywords if kw.arg == "actor"), None)


@pytest.mark.parametrize(("path", "function", "request_type"), CASES)
def test_review_precedes_exact_canonical_group_or_session_write(
    path: str, function: str, request_type: str
) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    )
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_type)
    assert len(reviews) == len(requests) == 1
    assert reviews[0].lineno < requests[0].lineno
    assert not _calls(fn, "confirm_write")
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_actor"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "state"
        for node in ast.walk(fn)
    )
    review_kw = {kw.arg: kw.value for kw in reviews[0].keywords}
    assert isinstance(review_kw["state"], ast.Name)
    assert review_kw["state"].id == "state"
    assert isinstance(review_kw["legacy_confirm"], ast.Name)
    assert review_kw["legacy_confirm"].id == "confirm_write"
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
    if function in {"_edit_group", "_edit_field"}:
        assert any(
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "values"
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "actor"
                for target in node.targets
            )
            and isinstance(node.value, ast.Name)
            and node.value.id == "actor"
            and node.lineno > reviews[0].lineno
            for node in ast.walk(fn)
        )
    else:
        actor_arg = _actor_kw(requests[0])
        assert isinstance(actor_arg, ast.Name) and actor_arg.id == "actor"


def _fixtures(
    monkeypatch: pytest.MonkeyPatch, module: Any, approved: bool
) -> tuple[Any, Any, Any, list[Any]]:
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(actor_id="adult-other", display_label="Other Adult")
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=1,
    )
    captured: list[Any] = []
    monkeypatch.setattr(module, "_latest", lambda _activity: activity)
    monkeypatch.setattr(
        module,
        "confirm_actor_write",
        lambda *_a, **_kw: alternate if approved else None,
    )
    monkeypatch.setattr(
        module,
        "confirm_write",
        lambda *_a, **_kw: pytest.fail("unexpected legacy confirmation"),
    )
    monkeypatch.setattr(module, "show_result", lambda *_a, **_kw: None)
    monkeypatch.setattr(module, "standards_kwargs_for_activity", lambda *_a, **_kw: {})
    monkeypatch.setattr(
        module,
        "_handle_error",
        lambda *_a, **_kw: pytest.fail("unexpected exception in workflow"),
    )
    return state, activity, alternate, captured


@pytest.mark.parametrize("approved", [True, False])
def test_group_creation_exact_recorder_and_no_write_on_cancel(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    state, activity, alternate, captured = _fixtures(monkeypatch, group, approved)
    monkeypatch.setattr(
        group,
        "prompt_text",
        lambda _title, label, **_kw: (
            None
            if label == "Description"
            else "Group One"
            if label == "Group label"
            else "group-one"
        ),
    )

    def create(request: Any, **_kw: Any) -> Any:
        captured.append(request)
        return SimpleNamespace(
            group_id=request.group_id,
            commit=SimpleNamespace(snapshot_revision=2, no_op=False),
        )

    monkeypatch.setattr(group, "create_group", create)
    group._create_group(activity, state)
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == alternate
    assert state.actor.actor_id == "adult-default"


@pytest.mark.parametrize("approved", [True, False])
def test_session_creation_exact_recorder_and_no_write_on_cancel(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    state, activity, alternate, captured = _fixtures(
        monkeypatch, session_menu, approved
    )
    monkeypatch.setattr(session_menu, "list_sessions", lambda *_a: ())
    monkeypatch.setattr(
        session_menu,
        "prompt_text",
        lambda _title, label, **_kw: (
            "Session One" if label == "Session label" else "session-one"
        ),
    )
    monkeypatch.setattr(session_menu, "prompt_positive_int", lambda *_a, **_kw: 1)

    def create(request: Any, **_kw: Any) -> Any:
        captured.append(request)
        return SimpleNamespace(
            session_id=request.session_id,
            commit=SimpleNamespace(snapshot_revision=2, no_op=False),
        )

    monkeypatch.setattr(session_menu, "create_session", create)
    session_menu._add(activity, state)
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == alternate
    assert state.actor.actor_id == "adult-default"


@pytest.mark.parametrize("approved", [True, False])
def test_session_field_edit_rebinds_dict_after_review(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    state, activity, alternate, captured = _fixtures(
        monkeypatch, session_menu, approved
    )
    selected = SimpleNamespace(
        session_id="session-one",
        sequence=1,
        label="Old Label",
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        snapshot_revision=1,
    )
    monkeypatch.setattr(session_menu, "prompt_text", lambda *_a, **_kw: "New Label")

    def update(request: Any, **_kw: Any) -> Any:
        captured.append(request)
        return SimpleNamespace(
            session_id=request.session_id,
            commit=SimpleNamespace(snapshot_revision=2, no_op=False),
        )

    monkeypatch.setattr(session_menu, "update_session", update)
    session_menu._edit_field(activity, selected, state, "label")
    assert len(captured) == (1 if approved else 0)
    if approved:
        assert captured[0].actor == alternate
        assert captured[0].label == "New Label"
    assert state.actor.actor_id == "adult-default"
