"""#148 3E3B: starter installation action-scoped preparation and no-op safety.

Uses synthetic starter statuses and actors; no classroom workspace or profile I/O.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from concord import menu_actor_action, menu_template
from concord.menu_context import MenuSessionContext
from concord.teacher_attribution import TeacherAttributionIdentity
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == name
    ]


@pytest.mark.parametrize(
    ("function_name", "prepare_name", "request_name", "commit_name"),
    [
        (
            "_install_starter",
            "prepare_starter_template_install",
            "PrepareStarterTemplateInstallRequest",
            "commit_starter_template_install",
        ),
        (
            "_install_all_starters",
            "prepare_starter_template_install_all",
            "PrepareStarterTemplateInstallAllRequest",
            "commit_starter_template_install_all",
        ),
    ],
)
def test_one_actor_exact_preparation_per_starter_write(
    function_name: str, prepare_name: str, request_name: str, commit_name: str
) -> None:
    tree = ast.parse((ROOT / "concord/menu_template.py").read_text(encoding="utf-8"))
    fn = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == function_name
    )
    assert len(_calls(fn, "confirm_prepared_actor_write")) == 1
    assert not _calls(fn, "confirm_write")
    assert len(_calls(fn, prepare_name)) == 2  # no-write probe and reviewed preparation
    assert len(_calls(fn, request_name)) == 2
    assert len(_calls(fn, commit_name)) == 1
    closure = next(
        n
        for n in fn.body
        if isinstance(n, ast.FunctionDef) and n.name == "_prepare_for_actor"
    )
    pending = _calls(closure, request_name)
    assert len(pending) == 1
    actor_arg = next(k.value for k in pending[0].keywords if k.arg == "actor")
    assert isinstance(actor_arg, ast.Name) and actor_arg.id == "actor"
    commit = _calls(fn, commit_name)[0]
    assert isinstance(commit.args[0], ast.Name) and commit.args[0].id == "prepared"
    confirm = _calls(fn, "confirm_prepared_actor_write")[0]
    assert confirm.lineno < commit.lineno
    assert any(
        kw.arg == "prepare_for_actor"
        and isinstance(kw.value, ast.Name)
        and kw.value.id == "_prepare_for_actor"
        for kw in confirm.keywords
    )


class _ActorContext:
    attribution_provider = object()

    def __init__(self) -> None:
        self.default = WorkflowActor(
            actor_id="adult-default", display_label="Default Adult"
        )
        self.labels: list[str] = []

    def require_actor(self) -> WorkflowActor:
        return self.default

    def actor_for_action(
        self,
        *,
        action_label: str,
        alternate: TeacherAttributionIdentity | None = None,
    ) -> WorkflowActor:
        self.labels.append(action_label)
        return self.default if alternate is None else alternate.workflow_actor()


def _setup(monkeypatch: pytest.MonkeyPatch, choices: list[str]) -> _ActorContext:
    ctx = _ActorContext()
    monkeypatch.setattr(menu_template, "show_result", lambda *_a: None)
    monkeypatch.setattr(
        menu_template, "_starter_detail_lines", lambda *_a: ("Synthetic starter",)
    )
    monkeypatch.setattr(
        menu_template,
        "_starter_install_result_lines",
        lambda *_a: ("Synthetic result",),
    )
    monkeypatch.setattr(
        menu_template, "_starter_install_all_lines", lambda *_a: ("Synthetic result",)
    )
    monkeypatch.setattr(
        menu_template,
        "confirm_write",
        lambda *_a: pytest.fail("legacy review unexpectedly used"),
    )
    monkeypatch.setattr(menu_actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_actor_action, "print_menu_header", lambda _t: None)
    monkeypatch.setattr(menu_actor_action, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_actor_action,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("adult-other", "Other Adult", "temporary"),
    )
    inputs = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    return ctx


@pytest.mark.parametrize(
    ("choices", "expected_ids"),
    [
        (["INSTALL"], ["adult-default", "adult-default"]),
        (["A", "INSTALL"], ["adult-default", "adult-default", "adult-other"]),
        (
            ["A", "D", "INSTALL"],
            ["adult-default", "adult-default", "adult-other", "adult-default"],
        ),
        ([""], ["adult-default", "adult-default"]),
    ],
)
def test_single_starter_reprepares_for_actor_and_cancel_no_write(
    monkeypatch: pytest.MonkeyPatch,
    choices: list[str],
    expected_ids: list[str],
) -> None:
    ctx = _setup(monkeypatch, choices)
    selected = SimpleNamespace(starter_key="starter-1", template_version_id="v2")
    monkeypatch.setattr(menu_template, "_choose_starter", lambda **_k: selected)
    calls: list[str] = []
    commits: list[Any] = []

    def prepare(request: Any) -> Any:
        calls.append(request.actor.actor_id)
        return SimpleNamespace(
            initial_state=menu_template.STARTER_INSTALLATION_MISSING,
            actor=request.actor,
        )

    monkeypatch.setattr(menu_template, "prepare_starter_template_install", prepare)
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install",
        lambda item: commits.append(item) or SimpleNamespace(),
    )
    menu_template._install_starter(cast(MenuSessionContext, ctx))
    assert calls == expected_ids
    assert len(commits) == (0 if choices[-1] == "" else 1)
    if commits:
        assert commits[0].actor.actor_id == expected_ids[-1]
    assert ctx.default.actor_id == "adult-default"


def test_single_starter_already_installed_never_prompts_or_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _setup(monkeypatch, [])
    selected = SimpleNamespace(starter_key="starter-1", template_version_id="v2")
    monkeypatch.setattr(menu_template, "_choose_starter", lambda **_k: selected)
    monkeypatch.setattr(
        menu_template,
        "prepare_starter_template_install",
        lambda _r: SimpleNamespace(
            initial_state=menu_template.STARTER_INSTALLATION_ALREADY_INSTALLED
        ),
    )
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install",
        lambda _r: pytest.fail("unexpected write"),
    )
    menu_template._install_starter(cast(MenuSessionContext, ctx))
    assert not ctx.labels


def test_single_starter_changed_during_review_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _setup(monkeypatch, ["INSTALL"])
    selected = SimpleNamespace(starter_key="starter-1", template_version_id="v2")
    monkeypatch.setattr(menu_template, "_choose_starter", lambda **_k: selected)
    states = iter(
        [
            menu_template.STARTER_INSTALLATION_MISSING,
            menu_template.STARTER_INSTALLATION_UPGRADE_AVAILABLE,
        ]
    )
    monkeypatch.setattr(
        menu_template,
        "prepare_starter_template_install",
        lambda _r: SimpleNamespace(initial_state=next(states)),
    )
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install",
        lambda _r: pytest.fail("unexpected write"),
    )
    with pytest.raises(Exception, match="changed during actor review"):
        menu_template._install_starter(cast(MenuSessionContext, ctx))


@pytest.mark.parametrize(
    ("choices", "expected_ids"),
    [
        (["INSTALL"], ["adult-default", "adult-default"]),
        (["A", "INSTALL"], ["adult-default", "adult-default", "adult-other"]),
        (
            ["A", "D", "INSTALL"],
            ["adult-default", "adult-default", "adult-other", "adult-default"],
        ),
        ([""], ["adult-default", "adult-default"]),
    ],
)
def test_install_all_reprepares_for_actor_and_cancel_no_write(
    monkeypatch: pytest.MonkeyPatch,
    choices: list[str],
    expected_ids: list[str],
) -> None:
    ctx = _setup(monkeypatch, choices)
    calls: list[str] = []
    commits: list[Any] = []

    def prepare(request: Any) -> Any:
        calls.append(request.actor.actor_id)
        return SimpleNamespace(
            actor=request.actor,
            items=(
                SimpleNamespace(
                    entry=SimpleNamespace(starter_key="starter-1"),
                    initial_state=menu_template.STARTER_INSTALLATION_MISSING,
                ),
                SimpleNamespace(
                    entry=SimpleNamespace(starter_key="starter-2"),
                    initial_state=menu_template.STARTER_INSTALLATION_ALREADY_INSTALLED,
                ),
            ),
        )

    monkeypatch.setattr(menu_template, "prepare_starter_template_install_all", prepare)
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install_all",
        lambda item: commits.append(item) or SimpleNamespace(),
    )
    menu_template._install_all_starters(cast(MenuSessionContext, ctx))
    assert calls == expected_ids
    assert len(commits) == (0 if choices[-1] == "" else 1)
    if commits:
        assert commits[0].actor.actor_id == expected_ids[-1]
    assert ctx.default.actor_id == "adult-default"


def test_install_all_current_never_prompts_or_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _setup(monkeypatch, [])
    monkeypatch.setattr(
        menu_template,
        "prepare_starter_template_install_all",
        lambda _r: SimpleNamespace(
            items=(
                SimpleNamespace(
                    entry=SimpleNamespace(starter_key="starter-1"),
                    initial_state=menu_template.STARTER_INSTALLATION_ALREADY_INSTALLED,
                ),
            )
        ),
    )
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install_all",
        lambda _r: pytest.fail("unexpected write"),
    )
    menu_template._install_all_starters(cast(MenuSessionContext, ctx))
    assert not ctx.labels


def test_install_all_changed_during_review_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ctx = _setup(monkeypatch, ["INSTALL"])
    count = 0

    def prepare(_request: Any) -> Any:
        nonlocal count
        count += 1
        status = (
            menu_template.STARTER_INSTALLATION_MISSING
            if count == 1
            else menu_template.STARTER_INSTALLATION_UPGRADE_AVAILABLE
        )
        return SimpleNamespace(
            items=(
                SimpleNamespace(
                    entry=SimpleNamespace(starter_key="starter-1"),
                    initial_state=status,
                ),
            )
        )

    monkeypatch.setattr(menu_template, "prepare_starter_template_install_all", prepare)
    monkeypatch.setattr(
        menu_template,
        "commit_starter_template_install_all",
        lambda _r: pytest.fail("unexpected write"),
    )
    with pytest.raises(Exception, match="changed during actor review"):
        menu_template._install_all_starters(cast(MenuSessionContext, ctx))
