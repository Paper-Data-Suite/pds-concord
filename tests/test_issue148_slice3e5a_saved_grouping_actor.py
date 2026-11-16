"""#148 Slice 3E5A: action-review, reprepare and digest consistency for class groupings.

All runtime inputs are synthetic; no real class roster or saved grouping is read.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_saved_groupings as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("function", "service", "request_type"),
    (
        ("save_grouping_from_plan", "save_grouping", "SaveGroupingRequest"),
        ("use_saved_grouping", "reuse_grouping", "ReuseGroupingRequest"),
    ),
)
def test_save_and_reuse_bind_preparation_to_reviewed_actor(
    function: str, service: str, request_type: str
) -> None:
    source = (ROOT / "concord/menu_saved_groupings.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    operation = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    )
    callbacks = [
        node
        for node in ast.walk(operation)
        if isinstance(node, ast.FunctionDef) and node.name == "_prepare_for_actor"
    ]
    assert len(callbacks) == 1
    calls = [
        node
        for node in ast.walk(operation)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]

    def named(name: str) -> list[ast.Call]:
        return [
            node
            for node in calls
            if isinstance(node.func, ast.Name) and node.func.id == name
        ]

    assert len(named("confirm_prepared_actor_write")) == 1
    assert len(named(request_type)) == 1
    assert len(named(service)) == 1
    assert named("confirm_prepared_actor_write")[0].lineno < named(service)[0].lineno
    request_call = named(request_type)[0]
    assert request_call in ast.walk(callbacks[0])
    actor = next(k.value for k in request_call.keywords if k.arg == "actor")
    assert isinstance(actor, ast.Name) and actor.id == "actor"
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "require_actor"
        for node in ast.walk(operation)
    )
    # The only other confirmations in reuse are preliminary acknowledgments.
    assert len(named("confirm_write")) == (0 if service == "save_grouping" else 1)


@pytest.mark.parametrize("kind", ("save", "reuse"))
@pytest.mark.parametrize("approved", (True, False))
def test_actor_switch_reprepares_exact_preview_digest_or_cancels(
    monkeypatch: pytest.MonkeyPatch, kind: str, approved: bool
) -> None:
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(
        actor_id="adult-alternate", display_label="Alternate Adult"
    )
    state = MenuSessionContext(actor=default)
    activity = SimpleNamespace(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic activity",
        snapshot_revision=8,
    )
    preparations: list[Any] = []
    writes: list[Any] = []
    monkeypatch.setattr(menu, "_latest", lambda *_a: activity)
    monkeypatch.setattr(menu, "_show_placements", lambda *_a, **_k: None)
    monkeypatch.setattr(menu, "_preview_reuse", lambda *_a, **_k: None)
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        menu, "handle_write_error", lambda err, **_k: pytest.fail(str(err))
    )
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_k: "synthetic-group")
    monkeypatch.setattr(menu, "slug_identifier", lambda *_a: "synthetic-group")
    monkeypatch.setattr(menu, "standards_kwargs_for_activity", lambda *_a: {})

    def prepare(request: Any) -> Any:
        preparations.append(request)
        return SimpleNamespace(
            name="Synthetic grouping",
            groups=(),
            unresolved_student_ids=(),
            assigned_count=0,
            review_digest=f"digest-{request.actor.actor_id}",
        )

    def verify_commit(request: Any, *, review_digest: str, **_kw: Any) -> Any:
        assert request.actor == alternate
        assert review_digest == f"digest-{alternate.actor_id}"
        assert request.expected_snapshot_revision == 8
        writes.append(request)
        if kind == "save":
            return SimpleNamespace(
                revision=SimpleNamespace(name="Synthetic grouping", groups=())
            )
        return SimpleNamespace(
            group_plan_id="new-draft", commit=SimpleNamespace(snapshot_revision=9)
        )

    def reviewed(
        _title: str, _expected: str, *, prepare_for_actor: Any, **_kw: Any
    ) -> Any:
        first, first_lines = prepare_for_actor(default)
        second, second_lines = prepare_for_actor(alternate)
        assert first[0].actor == default
        assert second[0].actor == alternate
        assert first[1].review_digest != second[1].review_digest
        assert first_lines == second_lines  # Same placement, changed attribution.
        return second if approved else None

    monkeypatch.setattr(menu, "confirm_prepared_actor_write", reviewed)
    monkeypatch.setattr(
        menu, "confirm_write", lambda *_a, **_k: pytest.fail("Legacy final review")
    )
    if kind == "save":
        monkeypatch.setattr(menu, "prepare_save_grouping", prepare)
        monkeypatch.setattr(menu, "save_grouping", verify_commit)
        menu.save_grouping_from_plan(activity, state, group_plan_id="synthetic-plan")
    else:
        saved = SimpleNamespace(
            revision=SimpleNamespace(
                arrangement_id="synthetic-arrangement",
                name="Synthetic grouping",
                groups=(),
                unresolved_student_ids=(),
            )
        )
        monkeypatch.setattr(menu, "_select_saved", lambda *_a: saved)
        monkeypatch.setattr(menu, "list_group_plans", lambda *_a: ())
        monkeypatch.setattr(menu, "_collect_decisions", lambda *_a: ((), ()))
        monkeypatch.setattr(menu, "prepare_reuse_grouping", prepare)
        monkeypatch.setattr(menu, "reuse_grouping", verify_commit)
        menu.use_saved_grouping(activity, state)
    assert [request.actor for request in preparations] == [default, alternate]
    assert len(writes) == int(approved)
    assert state.actor == default
