"""Concord #148 Slice 3C1: reviewed actor reaches reusable-preset writes.

Synthetic records only; source contract guards every adopted confirmation.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_presets as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("_create_role", "CreateRolePresetRequest"),
    ("_create_responsibility", "CreateResponsibilityPresetRequest"),
    ("_create_scale", "CreateScoringScalePresetRequest"),
    ("_create_criterion", "CreateCriterionSetPresetRequest"),
    ("_edit_role", "ReviseRolePresetRequest"),
    ("_edit_responsibility", "ReviseResponsibilityPresetRequest"),
    ("_edit_scale", "ReviseScoringScalePresetRequest"),
    ("_edit_criterion", "ReviseCriterionSetPresetRequest"),
    ("_retire", "retire_preset"),
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
def test_exact_presets_operation_has_one_actor_review_and_dispatch(
    function: str, request_name: str
) -> None:
    tree = ast.parse((ROOT / "concord/menu_presets.py").read_text(encoding="utf-8"))
    methods = [
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function
    ]
    assert len(methods) == 1
    fn = methods[0]
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_name)
    assert len(reviews) == len(requests) == 1, function
    assert not _calls(fn, "confirm_write"), function
    kws = {kw.arg: kw.value for kw in reviews[0].keywords}
    assert set(kws) == {"state", "legacy_confirm"}
    assert isinstance(kws["state"], ast.Name) and kws["state"].id == "state"
    assert (
        isinstance(kws["legacy_confirm"], ast.Name)
        and kws["legacy_confirm"].id == "confirm_write"
    )
    actor_keywords = [kw for kw in requests[0].keywords if kw.arg == "actor"]
    assert len(actor_keywords) == 1
    assert (
        isinstance(actor_keywords[0].value, ast.Name)
        and actor_keywords[0].value.id == "actor"
    )
    assignments = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Assign)
        and len(n.targets) == 1
        and isinstance(n.targets[0], ast.Name)
        and n.targets[0].id == "actor"
    ]
    assert len(assignments) == 1
    assert assignments[0].value is reviews[0]
    assert reviews[0].lineno < requests[0].lineno


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-default"))


def test_created_role_preset_records_exact_reviewed_alternate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    alternate = WorkflowActor(actor_id="teacher-alternate", display_label="Alt")
    observed: list[Any] = []
    reviews: list[tuple[str, str]] = []
    monkeypatch.setattr(
        menu, "_preset_identity", lambda _title: ("Role", "role-1", "role-v1")
    )
    monkeypatch.setattr(menu, "_role_key", lambda: "facilitator")
    monkeypatch.setattr(menu, "_optional_text", lambda *_a, **_kw: None)

    def confirm(title: str, verb: str, _lines: Any, **kwargs: Any) -> WorkflowActor:
        assert kwargs["state"] is state
        assert kwargs["legacy_confirm"] is menu.confirm_write
        reviews.append((title, verb))
        return alternate

    state = _state()
    monkeypatch.setattr(menu, "confirm_actor_write", confirm)
    monkeypatch.setattr(
        menu,
        "create_role_preset",
        lambda request: observed.append(request) or SimpleNamespace(preset_id="role-1"),
    )
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_kw: None)
    menu._create_role(state)
    assert reviews == [("Create Role Preset", "CREATE")]
    assert len(observed) == 1
    assert observed[0].actor is alternate
    assert state.require_actor().actor_id == "teacher-default"


def test_cancelled_role_preset_never_dispatches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu, "_preset_identity", lambda _title: ("Role", "role-1", "role-v1")
    )
    monkeypatch.setattr(menu, "_role_key", lambda: "facilitator")
    monkeypatch.setattr(menu, "_optional_text", lambda *_a, **_kw: None)
    monkeypatch.setattr(menu, "confirm_actor_write", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        menu,
        "create_role_preset",
        lambda *_a, **_kw: pytest.fail("cancelled creation wrote a preset"),
    )
    menu._create_role(_state())


@pytest.mark.parametrize("approved", [True, False])
def test_role_preset_edit_reports_only_real_commit_and_uses_reviewed_actor(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    alternate = WorkflowActor(actor_id="teacher-alternate")
    current = SimpleNamespace(
        preset_id="role-1",
        revision=1,
        name="Role",
        role_key="facilitator",
        role_label=None,
        description=None,
        applicability_hints=(),
    )
    observed: list[Any] = []
    monkeypatch.setattr(menu, "RolePresetRevision", SimpleNamespace)
    monkeypatch.setattr(menu, "get_preset", lambda *_a: current)
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_kw: "Role revised")
    monkeypatch.setattr(menu, "_role_key", lambda *_a: "facilitator")
    monkeypatch.setattr(menu, "_optional_text", lambda *_a, **_kw: None)
    monkeypatch.setattr(menu, "_successor_id", lambda *_a: "role-v2")
    monkeypatch.setattr(
        menu,
        "confirm_actor_write",
        lambda *_a, **_kw: alternate if approved else None,
    )
    monkeypatch.setattr(
        menu, "revise_role_preset", lambda request: observed.append(request)
    )
    done = menu._edit_role(SimpleNamespace(preset_id="role-1"), _state())
    assert done is approved
    assert len(observed) == int(approved)
    if approved:
        assert observed[0].actor is alternate


def test_cancelled_edit_has_no_success_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(menu, "_choose_preset", lambda *_a, **_kw: object())
    monkeypatch.setattr(menu, "_edit_role", lambda *_a: False)
    monkeypatch.setattr(
        menu,
        "show_result",
        lambda *_a, **_kw: pytest.fail("false saved receipt"),
    )
    menu._edit("role", _state())


def test_retirement_receives_selected_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected = SimpleNamespace(preset_id="role-1")
    current = SimpleNamespace(preset_id="role-1", revision=2, name="Role")
    observed: list[tuple[Any, ...]] = []
    alternate = WorkflowActor(actor_id="teacher-alternate")
    monkeypatch.setattr(menu, "_choose_preset", lambda *_a, **_kw: selected)
    monkeypatch.setattr(menu, "get_preset", lambda *_a: current)
    monkeypatch.setattr(menu, "_successor_id", lambda *_a: "role-v3")
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        menu,
        "retire_preset",
        lambda *args, **kwargs: observed.append((*args, kwargs["actor"])),
    )
    monkeypatch.setattr(menu, "confirm_actor_write", lambda *_a, **_kw: None)
    menu._retire("role", _state())
    assert not observed
    monkeypatch.setattr(menu, "confirm_actor_write", lambda *_a, **_kw: alternate)
    menu._retire("role", _state())
    assert observed == [("role", "role-1", alternate)]
