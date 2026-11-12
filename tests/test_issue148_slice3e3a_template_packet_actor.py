"""#148 3E3A: actor-exact prepared Template/Packet creation and lifecycle.

Pure AST and synthetic menu interactions. No profile or student data is loaded.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from concord import menu_actor_action, menu_packet, menu_template
from concord.menu_context import MenuSessionContext
from concord.teacher_attribution import TeacherAttributionIdentity
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
CASES = tuple(
    (path, function, f"prepare_{domain}_{verb}", f"commit_{domain}_{verb}")
    for domain, path in (
        ("template", "concord/menu_template.py"),
        ("packet", "concord/menu_packet.py"),
    )
    for function, verb in (
        ("_create", "create"),
        ("_revise", "revision"),
        ("_activate", "activation"),
        ("_update", "update"),
        ("_retire_version", "retire_version"),
        ("_retire", "retire"),
    )
)


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(tree)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


@pytest.mark.parametrize(("path", "function", "prepare_name", "commit_name"), CASES)
def test_exact_actor_preparation_is_reviewed_before_canonical_commit(
    path: str, function: str, prepare_name: str, commit_name: str
) -> None:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    fn = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == function
    )
    assert len(_calls(fn, "confirm_prepared_actor_write")) == 1
    assert len(_calls(fn, "confirm_write")) == 0
    assert len(_calls(fn, prepare_name)) == 1
    assert len(_calls(fn, commit_name)) == 1
    assert not any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Attribute)
        and item.func.attr == "require_actor"
        for item in ast.walk(fn)
    )
    closure = next(
        item
        for item in fn.body
        if isinstance(item, ast.FunctionDef) and item.name == "_prepare_for_actor"
    )
    request_calls = [
        item
        for item in ast.walk(closure)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id.startswith("Prepare")
        and item.func.id.endswith("Request")
    ]
    assert len(request_calls) == 1
    actor = next(kw.value for kw in request_calls[0].keywords if kw.arg == "actor")
    assert isinstance(actor, ast.Name) and actor.id == "actor"
    confirm = _calls(fn, "confirm_prepared_actor_write")[0]
    assert any(
        kw.arg == "prepare_for_actor"
        and isinstance(kw.value, ast.Name)
        and kw.value.id == "_prepare_for_actor"
        for kw in confirm.keywords
    )
    commit = _calls(fn, commit_name)[0]
    assert len(commit.args) == 1
    assert isinstance(commit.args[0], ast.Name) and commit.args[0].id == "prepared"
    assert confirm.lineno < commit.lineno
    assert any(
        isinstance(item, ast.If)
        and isinstance(item.test, ast.Compare)
        and isinstance(item.test.left, ast.Name)
        and item.test.left.id == "prepared"
        and any(isinstance(op, ast.Is) for op in item.test.ops)
        and any(
            isinstance(rhs, ast.Constant) and rhs.value is None
            for rhs in item.test.comparators
        )
        for item in fn.body
    )


class _SyntheticActorContext:
    attribution_provider = object()

    def __init__(self) -> None:
        self.default = WorkflowActor(
            actor_id="adult-default", display_label="Default Adult"
        )
        self.seen_labels: list[str] = []

    def require_actor(self) -> WorkflowActor:
        return self.default

    def actor_for_action(
        self, *, action_label: str, alternate: TeacherAttributionIdentity | None = None
    ) -> WorkflowActor:
        self.seen_labels.append(action_label)
        return self.default if alternate is None else alternate.workflow_actor()


@pytest.mark.parametrize(
    "module", [menu_template, menu_packet], ids=["template", "packet"]
)
@pytest.mark.parametrize(
    ("choices", "expected_ids"),
    [
        (["ACTIVATE"], ["adult-default"]),
        (["A", "ACTIVATE"], ["adult-default", "adult-other"]),
        (["A", "D", "ACTIVATE"], ["adult-default", "adult-other", "adult-default"]),
        ([""], ["adult-default"]),
    ],
)
def test_activation_reprepares_exact_selected_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch,
    module: Any,
    choices: list[str],
    expected_ids: list[str],
) -> None:
    context = _SyntheticActorContext()
    domain = "template" if module is menu_template else "packet"
    prefix = "Template" if domain == "template" else "Packet"
    id_field = "template_id" if domain == "template" else "packet_definition_id"
    head_field = (
        "head_template_version_id" if domain == "template" else "head_packet_version_id"
    )
    selected = SimpleNamespace(**{id_field: f"{domain}-example"})
    detail = SimpleNamespace(
        summary=SimpleNamespace(**{head_field: "version-v2", "snapshot_revision": 4})
    )
    prepared_ids: list[str] = []
    commits: list[Any] = []
    monkeypatch.setattr(module, f"_choose_{domain}", lambda **_k: selected)
    monkeypatch.setattr(module, f"get_{domain}", lambda _id: detail)
    monkeypatch.setattr(
        module, "_version_preview_lines", lambda *_a: ("Synthetic preview",)
    )
    monkeypatch.setattr(module, "_mutation_lines", lambda *_a: ("Synthetic result",))
    monkeypatch.setattr(module, "show_result", lambda *_a: None)
    monkeypatch.setattr(
        module,
        f"prepare_{domain}_activation",
        lambda request: _prepare_synthetic(request, prepared_ids),
    )
    monkeypatch.setattr(
        module,
        f"commit_{domain}_activation",
        lambda prepared: commits.append(prepared) or SimpleNamespace(),
    )
    monkeypatch.setattr(
        module, "confirm_write", lambda *_a: pytest.fail("unexpected legacy prompt")
    )
    monkeypatch.setattr(menu_actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_actor_action, "print_menu_header", lambda _title: None)
    monkeypatch.setattr(menu_actor_action, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_actor_action,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("adult-other", "Other Adult", "temporary"),
    )
    inputs = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    module._activate(cast(MenuSessionContext, context))
    assert prepared_ids == expected_ids
    assert len(commits) == (0 if choices[-1] == "" else 1)
    if commits:
        assert commits[0].actor.actor_id == expected_ids[-1]
    assert context.default.actor_id == "adult-default"
    assert "Activate " + prefix + " Version" in context.seen_labels


def _prepare_synthetic(request: Any, history: list[str]) -> Any:
    history.append(request.actor.actor_id)
    return SimpleNamespace(actor=request.actor)
