"""#148 3E4A: exact action-scoped recorder for Role/Responsibility end/reassign.

Uses synthetic Activity and Actor values; no Core workspace, student record,
user profile, or network access. The real canonical service is never invoked.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_responsibility, menu_role
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("concord/menu_role.py", "_end", "EndRoleRequest", "end_role"),
    ("concord/menu_role.py", "_reassign", "ReassignRoleRequest", "reassign_role"),
    (
        "concord/menu_responsibility.py",
        "_end",
        "EndResponsibilityRequest",
        "end_responsibility",
    ),
    (
        "concord/menu_responsibility.py",
        "_reassign",
        "ReassignResponsibilityRequest",
        "reassign_responsibility",
    ),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


@pytest.mark.parametrize(("path", "operation", "request_type", "service"), CASES)
def test_exact_reviewed_actor_reaches_canonical_assignment_request(
    path: str, operation: str, request_type: str, service: str
) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == operation
    )
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_type)
    writes = _calls(fn, service)
    assert len(reviews) == len(requests) == len(writes) == 1
    assert reviews[0].lineno < writes[0].lineno <= requests[0].lineno
    assert requests[0] in writes[0].args
    assert not _calls(fn, "confirm_write")
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_actor"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "state"
        for node in ast.walk(fn)
    )
    bound_actor = next(kw.value for kw in requests[0].keywords if kw.arg == "actor")
    assert isinstance(bound_actor, ast.Name) and bound_actor.id == "actor"
    assert any(
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "actor"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Is)
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value is None
        for node in ast.walk(fn)
    )
    assert any(kw.arg == "state" for kw in reviews[0].keywords)
    assert any(kw.arg == "legacy_confirm" for kw in reviews[0].keywords)


@pytest.mark.parametrize(("path", "operation", "request_type", "service"), CASES)
@pytest.mark.parametrize("approved", [True, False])
def test_actor_override_is_one_write_and_cancellation_is_no_write(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    operation: str,
    request_type: str,
    service: str,
    approved: bool,
) -> None:
    module: Any = menu_role if path.endswith("menu_role.py") else menu_responsibility
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(actor_id="adult-alt", display_label="Alternate Adult")
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=1,
    )
    original = SimpleNamespace(
        snapshot_revision=1,
        status="active",
        role_assignment_id="role-old",
        role_key="recorder",
        group_id=None,
        participant_display_label="Student Z",
        participant_reference=SimpleNamespace(participant_id="student-z"),
        responsibility_assignment_id="responsibility-old",
        description="Document the meeting",
        assignee_display_label="Student Z",
        assignee_reference=object(),
    )
    writes: list[Any] = []
    monkeypatch.setattr(module, "_latest", lambda _activity: activity)
    monkeypatch.setattr(module, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(module, "standards_kwargs_for_activity", lambda *_a: {})
    monkeypatch.setattr(
        module,
        "_handle_error",
        lambda *_a, **_k: pytest.fail("Unexpected workflow exception"),
    )
    monkeypatch.setattr(
        module,
        "confirm_write",
        lambda *_a, **_k: pytest.fail("Unexpected legacy confirmation"),
    )
    monkeypatch.setattr(
        module,
        "confirm_actor_write",
        lambda *_a, **_k: alternate if approved else None,
    )
    monkeypatch.setattr(module, "_choose_existing", lambda *_a: original)
    monkeypatch.setattr(
        module, "choose_assignment_end_status", lambda *_a, **_k: "completed"
    )
    monkeypatch.setattr(module, "assignment_end_review", lambda *_a, **_k: ("Review",))
    monkeypatch.setattr(
        module, request_type, lambda **fields: SimpleNamespace(**fields)
    )
    monkeypatch.setattr(
        module,
        service,
        lambda request, **_k: (
            writes.append(request)
            or SimpleNamespace(
                commit=SimpleNamespace(snapshot_revision=2),
                role_assignment_id="role-next",
                predecessor_role_assignment_id="role-old",
                responsibility_assignment_id="responsibility-next",
                predecessor_responsibility_assignment_id="responsibility-old",
            )
        ),
    )
    if path.endswith("menu_role.py"):
        monkeypatch.setattr(module, "list_roles", lambda *_a: (original,))
    else:
        monkeypatch.setattr(module, "list_responsibilities", lambda *_a: (original,))
    if operation == "_reassign":
        monkeypatch.setattr(
            module, "resolve_workspace_root", lambda: Path("/synthetic")
        )
        monkeypatch.setattr(module, "list_sessions", lambda *_a: ())
        monkeypatch.setattr(module, "choose_effective_context", lambda *_a: object())
        if path.endswith("menu_role.py"):
            monkeypatch.setattr(
                module,
                "choose_student",
                lambda *_a: SimpleNamespace(
                    student_id="student-new", first_name="New", last_name="Student"
                ),
            )
            monkeypatch.setattr(module, "_choose_role_key", lambda: "facilitator")
            monkeypatch.setattr(module, "_choose_optional_group", lambda *_a: None)
            monkeypatch.setattr(
                module, "core_student_participant", lambda *_a: object()
            )
        else:
            monkeypatch.setattr(
                module, "_choose_assignee", lambda *_a: (object(), None, "Student Z")
            )
            monkeypatch.setattr(module, "prompt_text", lambda *_a, **_k: "Take notes")
    getattr(module, operation)(activity, state)
    assert len(writes) == (1 if approved else 0)
    if approved:
        assert writes[0].actor == alternate
        assert writes[0].expected_snapshot_revision == 1
    assert state.actor == default
