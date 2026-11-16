"""#148 3E5B: actor-exact operational grouping save; synthetic classroom data only."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_saved_operational_grouping as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor
from concord.workflows.errors import ConcordWorkflowConflictError

ROOT = Path(__file__).resolve().parents[1]


def test_exact_actor_prepare_and_digest_share_one_confirmed_result() -> None:
    tree = ast.parse(
        (ROOT / "concord/menu_saved_operational_grouping.py").read_text(
            encoding="utf-8"
        )
    )
    fn = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "save_grouping_from_existing_groups"
    )
    calls = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    reviewers = [n for n in calls if n.func.id == "confirm_prepared_actor_write"]
    commits = [n for n in calls if n.func.id == "save_operational_grouping"]
    requests = [n for n in calls if n.func.id == "SaveOperationalGroupingRequest"]
    assert len(reviewers) == len(commits) == 1
    assert len(requests) == 2  # Inspection followed by exact actor-specific request.
    assert reviewers[0].lineno < commits[0].lineno
    assert {x.arg for x in reviewers[0].keywords} >= {
        "state",
        "legacy_confirm",
        "prepare_for_actor",
    }
    callback = next(
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.FunctionDef) and n.name == "_prepare_for_actor"
    )
    callback_requests = [
        n
        for n in ast.walk(callback)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "SaveOperationalGroupingRequest"
    ]
    assert len(callback_requests) == 1
    actor_arg = next(k.value for k in callback_requests[0].keywords if k.arg == "actor")
    assert isinstance(actor_arg, ast.Name) and actor_arg.id == "actor"
    assert any(
        n.func.id == "prepare_save_operational_grouping"
        for n in ast.walk(callback)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    )
    commit = commits[0]
    assert len(commit.args) == 1
    assert isinstance(commit.args[0], ast.Name) and commit.args[0].id == "request"
    digest_arg = next(k.value for k in commit.keywords if k.arg == "review_digest")
    assert isinstance(digest_arg, ast.Attribute) and digest_arg.attr == "review_digest"


def _setup(
    monkeypatch: pytest.MonkeyPatch,
    *,
    unresolved: bool = False,
    shift_projection: bool = False,
) -> tuple[MenuSessionContext, WorkflowActor, list[tuple[str, Any]]]:
    state = MenuSessionContext(
        actor=WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    )
    alternate = WorkflowActor(actor_id="adult-alt", display_label="Other Adult")
    current = SimpleNamespace(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        snapshot_revision=4,
        title="Synthetic Activity",
    )
    session = SimpleNamespace(session_id="session-1", label="First Session")
    events: list[tuple[str, Any]] = []
    monkeypatch.setattr(
        menu, "show_activity", lambda *_a: SimpleNamespace(summary=current)
    )
    monkeypatch.setattr(menu, "list_sessions", lambda *_a: (session,))
    monkeypatch.setattr(menu, "choose_session", lambda *_a, **_k: session)
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda _title, label, **_k: (
            "Six Tables" if label == "Grouping name" else "six-tables"
        ),
    )
    monkeypatch.setattr(
        menu, "_review_placements", lambda *_a: events.append(("placements", None))
    )
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_k: None)
    monkeypatch.setattr(
        menu,
        "handle_write_error",
        lambda error, **_k: events.append(("error", error)),
    )
    count = 0

    def prepare(req: Any) -> Any:
        nonlocal count
        count += 1
        events.append(("prepare", req))
        groups = (SimpleNamespace(label="Table 1", student_ids=("synthetic-1",)),)
        if shift_projection and count > 1:
            groups = (SimpleNamespace(label="Changed", student_ids=("synthetic-2",)),)
        return SimpleNamespace(
            name=req.name,
            source_activity_id=req.activity_id,
            source_session_id=req.session_id,
            source_snapshot_revision=req.expected_snapshot_revision,
            groups=groups,
            assigned_count=1,
            unresolved_student_ids=("synthetic-2",) if unresolved else (),
            review_digest=f"digest:{req.actor.actor_id}",
        )

    monkeypatch.setattr(menu, "prepare_save_operational_grouping", prepare)
    monkeypatch.setattr(
        menu,
        "save_operational_grouping",
        lambda req, *, review_digest: (
            events.append(("commit", (req, review_digest)))
            or SimpleNamespace(revision=SimpleNamespace(name="Six Tables", groups=(1,)))
        ),
    )
    return state, alternate, events


@pytest.mark.parametrize("choice", ["alternate", "default", "cancel"])
def test_actor_switch_prepare_digest_and_cancel(
    monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    state, alternate, events = _setup(monkeypatch)

    def review(_title: str, _action: str, **kw: Any) -> Any:
        cb = kw["prepare_for_actor"]
        cb(state.actor)
        if choice != "default":
            cb(alternate)
        if choice == "cancel":
            return None
        if choice == "default":
            return cb(state.actor)[0]
        return cb(alternate)[0]

    monkeypatch.setattr(menu, "confirm_prepared_actor_write", review)
    monkeypatch.setattr(
        menu,
        "confirm_write",
        lambda *_a, **_k: pytest.fail("unexpected acknowledgment"),
    )
    menu.save_grouping_from_existing_groups(
        SimpleNamespace(class_id="class-synthetic", activity_id="activity-synthetic"),
        state,
    )
    commits = [e for e in events if e[0] == "commit"]
    assert len(commits) == (0 if choice == "cancel" else 1)
    if commits:
        request, digest = commits[0][1]
        expected = state.actor if choice == "default" else alternate
        assert request.actor == expected
        assert digest == f"digest:{expected.actor_id}"
        assert request.acknowledge_unresolved is True
        assert request.expected_snapshot_revision == 4
    assert state.actor.actor_id == "adult-default"


def test_unassigned_student_acknowledgment_refusal_prevents_review_and_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, _, events = _setup(monkeypatch, unresolved=True)
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: False)
    monkeypatch.setattr(
        menu,
        "confirm_prepared_actor_write",
        lambda *_a, **_k: pytest.fail("no final SAVE after refused acknowledgment"),
    )
    menu.save_grouping_from_existing_groups(
        SimpleNamespace(class_id="class-synthetic", activity_id="activity-synthetic"),
        state,
    )
    assert [x[0] for x in events] == ["prepare", "placements"]


def test_unassigned_student_acknowledgment_survives_actor_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, alternate, events = _setup(monkeypatch, unresolved=True)
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: True)
    monkeypatch.setattr(
        menu,
        "confirm_prepared_actor_write",
        lambda *_a, **kw: kw["prepare_for_actor"](alternate)[0],
    )
    menu.save_grouping_from_existing_groups(
        SimpleNamespace(class_id="class-synthetic", activity_id="activity-synthetic"),
        state,
    )
    request, digest = next(x[1] for x in events if x[0] == "commit")
    assert request.actor == alternate
    assert request.acknowledge_unresolved is True
    assert digest == "digest:adult-alt"


def test_changed_placements_fail_closed_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, alternate, events = _setup(monkeypatch, shift_projection=True)
    monkeypatch.setattr(menu, "confirm_write", lambda *_a, **_k: True)
    monkeypatch.setattr(
        menu,
        "confirm_prepared_actor_write",
        lambda *_a, **kw: kw["prepare_for_actor"](alternate)[0],
    )
    menu.save_grouping_from_existing_groups(
        SimpleNamespace(class_id="class-synthetic", activity_id="activity-synthetic"),
        state,
    )
    errors = [x[1] for x in events if x[0] == "error"]
    assert len(errors) == 1
    assert isinstance(errors[0], ConcordWorkflowConflictError)
    assert not any(x[0] == "commit" for x in events)
