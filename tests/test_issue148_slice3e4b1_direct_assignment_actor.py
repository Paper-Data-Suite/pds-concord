"""#148 3E4B1: manual Role/Responsibility assignment uses reviewed actor.

Synthetic only: never consults an actual roster, classroom workspace, or profile.
Saved-preset branches use actor-exact review as of Slice 3E4B2.
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
    ("concord/menu_role.py", "AssignRoleRequest", "assign_role"),
    (
        "concord/menu_responsibility.py",
        "AssignResponsibilityRequest",
        "assign_responsibility",
    ),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == name
    ]


@pytest.mark.parametrize(("path", "request_type", "service"), CASES)
def test_direct_assignment_reviews_exact_request_and_preset_is_actor_reviewed(
    path: str, request_type: str, service: str
) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    fn = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_assign"
    )
    direct = _calls(fn, "confirm_actor_write")
    prepared = _calls(fn, "confirm_prepared_actor_write")
    writes = _calls(fn, service)
    assert len(direct) == len(prepared) == len(writes) == 1
    assert not _calls(fn, "confirm_write")
    assert direct[0].lineno < writes[0].lineno
    assert len(_calls(fn, request_type)) == 1
    direct_request = _calls(fn, request_type)[0]
    assert len(writes[0].args) == 1 and writes[0].args[0] is direct_request
    value = next(kw.value for kw in direct_request.keywords if kw.arg == "actor")
    assert isinstance(value, ast.Name) and value.id == "actor"
    assert {kw.arg for kw in direct[0].keywords} >= {"state", "legacy_confirm"}
    assert (
        len(
            [
                n
                for n in ast.walk(fn)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "require_actor"
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "state"
            ]
        )
        == 0
    )  # Neither branch reads a cached actor.


@pytest.mark.parametrize(("path", "request_type", "service"), CASES)
@pytest.mark.parametrize("approved", [True, False])
def test_direct_assignment_selected_actor_or_cancel_never_mutates_default(
    monkeypatch: pytest.MonkeyPatch,
    path: str,
    request_type: str,
    service: str,
    approved: bool,
) -> None:
    module: Any = menu_role if path.endswith("menu_role.py") else menu_responsibility
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(
        actor_id="adult-alternate", display_label="Alternate Adult"
    )
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=1,
    )
    records: list[Any] = []
    monkeypatch.setattr(module, "_latest", lambda _activity: activity)
    monkeypatch.setattr(module, "standards_kwargs_for_activity", lambda *_a: {})
    monkeypatch.setattr(module, "list_sessions", lambda *_a: ())
    context = SimpleNamespace(session_ids=())
    monkeypatch.setattr(module, "choose_effective_context", lambda *_a: context)
    monkeypatch.setattr(module, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        module,
        "_handle_error",
        lambda *_a, **_k: pytest.fail("Unexpected workflow exception"),
    )
    monkeypatch.setattr(module, "resolve_workspace_root", lambda: Path("/synthetic"))
    monkeypatch.setattr(
        module,
        "confirm_write",
        lambda *_a, **_k: pytest.fail("Legacy direct confirmation"),
    )
    monkeypatch.setattr(
        module,
        "confirm_actor_write",
        lambda *_a, **_k: alternate if approved else None,
    )
    monkeypatch.setattr(
        module, request_type, lambda **fields: SimpleNamespace(**fields)
    )
    monkeypatch.setattr(
        module,
        service,
        lambda request, **_k: (
            records.append(request)
            or SimpleNamespace(
                commit=SimpleNamespace(snapshot_revision=2),
                role_assignment_id="role-new",
                responsibility_assignment_id="responsibility-new",
            )
        ),
    )
    if path.endswith("menu_role.py"):
        monkeypatch.setattr(
            module,
            "choose_student",
            lambda *_a: SimpleNamespace(
                student_id="student-1", first_name="Student", last_name="One"
            ),
        )
        monkeypatch.setattr(module, "_choose_role_preset", lambda: None)
        monkeypatch.setattr(module, "_choose_role_key", lambda: "facilitator")
        monkeypatch.setattr(module, "_choose_optional_group", lambda *_a: None)
        monkeypatch.setattr(module, "core_student_participant", lambda *_a: object())
    else:
        monkeypatch.setattr(
            module,
            "_choose_assignee",
            lambda *_a: (object(), None, "Student One"),
        )
        monkeypatch.setattr(module, "_choose_responsibility_preset", lambda: None)
        monkeypatch.setattr(
            module,
            "prompt_text",
            lambda _title, name, **_k: (
                "Review notes" if name == "Responsibility" else None
            ),
        )
    module._assign(activity, state)
    assert len(records) == (1 if approved else 0)
    if records:
        assert records[0].actor == alternate
        assert records[0].expected_snapshot_revision == 1
    assert state.actor == default
