"""Concord #148 Slice 3C3A: reviewed actor for guided native rubric writes.

Purely synthetic Activity and Criterion data; no academic workspace writes.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_scoring as scoring
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("_create_guided_criterion_set", "CreateCriterionSetRequest"),
    ("_revise_criterion_set", "ReviseCriterionSetRequest"),
    ("_use_existing_criterion_set", "SelectActivityCriterionSetsRequest"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


def _function(name: str) -> ast.FunctionDef:
    tree = ast.parse((ROOT / "concord/menu_scoring.py").read_text(encoding="utf-8"))
    matches = [
        child
        for child in tree.body
        if isinstance(child, ast.FunctionDef) and child.name == name
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize(("function_name", "write_type"), TARGETS)
def test_exact_guided_review_actor_reaches_canonical_request(
    function_name: str, write_type: str
) -> None:
    fn = _function(function_name)
    reviews = _calls(fn, "confirm_actor_write")
    writes = _calls(fn, write_type)
    assert len(reviews) == len(writes) == 1
    assert not _calls(fn, "confirm_write")
    call = reviews[0]
    assert {item.arg for item in call.keywords} == {"state", "legacy_confirm"}
    assert call.lineno < writes[0].lineno
    actor_kw = [item for item in writes[0].keywords if item.arg == "actor"]
    assert len(actor_kw) == 1
    assert isinstance(actor_kw[0].value, ast.Name)
    assert actor_kw[0].value.id == "actor"
    assert not any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and isinstance(child.func.value, ast.Name)
        and child.func.value.id == "state"
        and child.func.attr == "require_actor"
        and child.lineno > call.lineno
        for child in ast.walk(fn)
    )


@pytest.mark.parametrize(
    "function_name", ("_create_guided_criterion_set", "_revise_criterion_set")
)
def test_alternate_actor_is_revalidated_before_write(function_name: str) -> None:
    fn = _function(function_name)
    reviews = _calls(fn, "confirm_actor_write")
    validations = _calls(fn, "validate_criterion_draft")
    assert len(reviews) == 1
    assert len(validations) == 2
    assert validations[0].lineno < reviews[0].lineno < validations[1].lineno
    guards = [
        node
        for node in ast.walk(fn)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "actor"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.NotEq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Name)
        and node.test.comparators[0].id == "initial_actor"
    ]
    assert len(guards) == 1
    assert validations[1] in list(ast.walk(guards[0]))


def test_guided_create_and_use_reuses_one_reviewed_actor_for_both_writes() -> None:
    fn = _function("_create_guided_criterion_set")
    helper_calls = _calls(fn, "_complete_guided_criterion_selection")
    assert len(helper_calls) == 1
    assert isinstance(helper_calls[0].args[1], ast.Name)
    assert helper_calls[0].args[1].id == "actor"
    helper = _function("_complete_guided_criterion_selection")
    selection_requests = _calls(helper, "SelectActivityCriterionSetsRequest")
    assert len(selection_requests) == 1
    kw = [item for item in selection_requests[0].keywords if item.arg == "actor"]
    assert len(kw) == 1
    assert isinstance(kw[0].value, ast.Name) and kw[0].value.id == "actor"


def _synthetic_guided(
    monkeypatch: pytest.MonkeyPatch, *, selected: bool
) -> tuple[MenuSessionContext, WorkflowActor, list[WorkflowActor], list[object]]:
    original = WorkflowActor(actor_id="adult-default", display_label="Default")
    alternate = WorkflowActor(actor_id="adult-alternate", display_label="Alternate")
    current = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Discussion",
        scoring_orientation="local_criteria_only",
        snapshot_revision=1,
    )
    details = SimpleNamespace(standards_profile_id=None, focus_standard_ids=())
    draft = SimpleNamespace(
        name="Discussion Evidence",
        purpose="Synthetic Assessment",
        scope="activity_specific",
        criterion_set_kind="local",
        criteria=(),
    )
    monkeypatch.setattr(scoring, "_latest", lambda _item: current)
    monkeypatch.setattr(scoring, "show_activity", lambda *_a, **_k: details)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring,
        "guide_native_criterion_set",
        lambda **_kw: (draft, ()),
    )
    monkeypatch.setattr(scoring, "describe_criterion_draft", lambda *_a, **_k: ())
    monkeypatch.setattr(scoring, "criterion_specs", lambda *_a: ())
    monkeypatch.setattr(scoring, "CreateCriterionSetRequest", SimpleNamespace)
    monkeypatch.setattr(scoring, "SelectActivityCriterionSetsRequest", SimpleNamespace)
    monkeypatch.setattr(scoring, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        scoring,
        "_handle_error",
        lambda *_a: pytest.fail("unexpected guided-rubric workflow error"),
    )
    monkeypatch.setattr(
        scoring,
        "confirm_write",
        lambda *_a, **_k: pytest.fail("unexpected legacy confirmation"),
    )
    validated: list[object] = []
    monkeypatch.setattr(
        scoring,
        "validate_criterion_draft",
        lambda _draft, **kwargs: validated.append(kwargs["created_provenance"]),
    )
    writes: list[WorkflowActor] = []

    def create(request: Any, **_kw: object) -> SimpleNamespace:
        writes.append(request.actor)
        return SimpleNamespace(
            criterion_set_id=request.criterion_set_id,
            commit=SimpleNamespace(snapshot_revision=2),
        )

    def select(request: Any, **_kw: object) -> SimpleNamespace:
        writes.append(request.actor)
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=3))

    monkeypatch.setattr(scoring, "create_criterion_set", create)
    monkeypatch.setattr(scoring, "select_activity_criterion_sets", select)
    if selected:
        reads = iter(
            (
                SimpleNamespace(snapshot_revision=1, criterion_set_ids=()),
                SimpleNamespace(snapshot_revision=2, criterion_set_ids=()),
                SimpleNamespace(snapshot_revision=3, criterion_set_ids=()),
            )
        )

        def read(*_a: object, **_kw: object) -> SimpleNamespace:
            value = next(reads)
            if value.snapshot_revision == 3:
                return SimpleNamespace(
                    snapshot_revision=3, criterion_set_ids=(created_id[0],)
                )
            return value

        created_id: list[str] = []
        old_create = create

        def track_create(request: Any, **kw: object) -> SimpleNamespace:
            created_id.append(request.criterion_set_id)
            return old_create(request, **kw)

        monkeypatch.setattr(scoring, "create_criterion_set", track_create)
        monkeypatch.setattr(scoring, "read_activity_criterion_set_selection", read)
    return MenuSessionContext(actor=original), alternate, writes, validated


def test_reviewed_alternate_reaches_both_guided_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, alternate, writes, validated = _synthetic_guided(monkeypatch, selected=True)
    monkeypatch.setattr(scoring, "confirm_actor_write", lambda *_a, **_kw: alternate)
    scoring._create_guided_criterion_set(
        SimpleNamespace(), state, use_after_create=True
    )
    assert writes == [alternate, alternate]
    assert len(validated) == 2
    assert state.require_actor().actor_id == "adult-default"


def test_cancelled_guided_review_writes_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _alternate, writes, validated = _synthetic_guided(
        monkeypatch, selected=False
    )
    monkeypatch.setattr(scoring, "confirm_actor_write", lambda *_a, **_kw: None)
    scoring._create_guided_criterion_set(SimpleNamespace(), state)
    assert writes == []
    assert len(validated) == 1
