"""#148 Slice 3C2: eight native scoring writes bind one reviewed actor.

Synthetic inputs only; no student data or external workspace is accessed.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_scoring as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    ("_create_scale", "CreateScoringScaleRequest"),
    ("_revise_scale", "ReviseScoringScaleRequest"),
    ("_import_saved_scale", "CreateScoringScaleRequest"),
    ("_create_criterion_set", "CreateCriterionSetRequest"),
    ("_revise_criterion_set_advanced", "ReviseCriterionSetRequest"),
    ("_select_criterion_sets_advanced", "SelectActivityCriterionSetsRequest"),
    ("_record_score", "AddScoreRequest"),
    ("_revise_score", "ReplaceScoreRequest"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        child
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        and isinstance(child.func, ast.Name)
        and child.func.id == name
    ]


@pytest.mark.parametrize(("function", "request_type"), TARGETS)
def test_one_reviewed_actor_reaches_exact_native_request(
    function: str, request_type: str
) -> None:
    source = (ROOT / "concord/menu_scoring.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function
    ]
    assert len(functions) == 1
    fn = functions[0]
    reviews = _calls(fn, "confirm_actor_write")
    requests = _calls(fn, request_type)
    assert len(reviews) == len(requests) == 1, function
    assert not _calls(fn, "confirm_write"), function
    kwargs = {kw.arg: kw.value for kw in reviews[0].keywords}
    assert set(kwargs) == {"state", "legacy_confirm"}
    assert isinstance(kwargs["state"], ast.Name)
    assert kwargs["state"].id == "state"
    assert isinstance(kwargs["legacy_confirm"], ast.Name)
    assert kwargs["legacy_confirm"].id == "confirm_write"
    actor_args = [kw for kw in requests[0].keywords if kw.arg == "actor"]
    assert len(actor_args) == 1
    assert isinstance(actor_args[0].value, ast.Name)
    assert actor_args[0].value.id == "actor"
    assignments = [
        node
        for node in ast.walk(fn)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "actor"
    ]
    assert len(assignments) == 1
    assert assignments[0].value is reviews[0]
    assert reviews[0].lineno < requests[0].lineno
    assert not _calls(fn, "actor_for_action")  # No queued identity override.


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-default"))


def _current() -> Any:
    return SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Synthetic Activity",
        snapshot_revision=4,
        scoring_orientation="local_criteria_only",
    )


@pytest.mark.parametrize("approved", [True, False])
def test_record_score_uses_reviewed_actor_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    state = _state()
    alternate = WorkflowActor(actor_id="teacher-alternate")
    observed: list[Any] = []
    reviews: list[tuple[str, str]] = []
    draft = SimpleNamespace(
        target=SimpleNamespace(target_kind="core_student", target_id="synthetic"),
        criterion=SimpleNamespace(criterion_id="criterion-synthetic"),
        scale=SimpleNamespace(scoring_scale_id="scale-synthetic"),
        session_id=None,
        disposition="scored",
        value="meeting",
        basis="synthetic",
        links=(),
        rationale=None,
        status_reason=None,
    )
    monkeypatch.setattr(menu, "_latest", lambda *_a: _current())
    monkeypatch.setattr(menu, "_score_components", lambda *_a: draft)
    monkeypatch.setattr(menu, "_identifier", lambda *_a: "score-synthetic")
    monkeypatch.setattr(menu, "_score_confirmation_lines", lambda *_a: ("synthetic",))
    monkeypatch.setattr(
        menu, "AddScoreRequest", lambda **kwargs: SimpleNamespace(**kwargs)
    )
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(menu, "show_result", lambda *_a: None)

    def confirm(title: str, expected: str, _lines: Any, **kwargs: Any) -> Any:
        assert kwargs["state"] is state
        assert kwargs["legacy_confirm"] is menu.confirm_write
        reviews.append((title, expected))
        return alternate if approved else None

    def record(write: Any, **kwargs: Any) -> Any:
        observed.append(write)
        assert kwargs == {"standards_library": None}
        return SimpleNamespace(score_evidence_link_ids=())

    monkeypatch.setattr(menu, "confirm_actor_write", confirm)
    monkeypatch.setattr(menu, "add_score", record)
    menu._record_score(_current(), state)
    assert reviews == [("Record a Score", "SCORE")]
    assert len(observed) == int(approved)
    if approved:
        assert observed[0].actor is alternate
    assert state.require_actor().actor_id == "teacher-default"


@pytest.mark.parametrize("approved", [True, False])
def test_advanced_criterion_selection_binds_review_and_cancel(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    state = _state()
    alternate = WorkflowActor(actor_id="teacher-alternate")
    observed: list[Any] = []
    current = _current()
    chosen = SimpleNamespace(
        name="Rubric",
        criterion_set_id="set-synthetic",
        revision=1,
        is_current=True,
    )
    monkeypatch.setattr(menu, "_latest", lambda *_a: current)
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *_a, **_kw: (chosen,))
    monkeypatch.setattr(menu, "select_many", lambda *_a, **_kw: (chosen,))
    monkeypatch.setattr(
        menu,
        "SelectActivityCriterionSetsRequest",
        lambda **kwargs: SimpleNamespace(**kwargs),
    )
    monkeypatch.setattr(menu, "show_result", lambda *_a: None)
    monkeypatch.setattr(
        menu,
        "confirm_actor_write",
        lambda _title, _action, _lines, **_kwargs: alternate if approved else None,
    )

    def select(write: Any, **kwargs: Any) -> Any:
        observed.append(write)
        assert kwargs == {"standards_library": None}
        return SimpleNamespace(
            criterion_set_ids=("set-synthetic",),
            commit=SimpleNamespace(snapshot_revision=5),
        )

    monkeypatch.setattr(menu, "select_activity_criterion_sets", select)
    menu._select_criterion_sets_advanced(current, state)
    assert len(observed) == int(approved)
    if approved:
        assert observed[0].actor is alternate
        assert observed[0].criterion_set_ids == ("set-synthetic",)
    assert state.require_actor().actor_id == "teacher-default"
