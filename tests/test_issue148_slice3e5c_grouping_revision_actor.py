"""#148 Slice 3E5C: saved grouping revisions use exact reviewed actors/digests.

Synthetic records only. No roster, workspace, or teacher profile is accessed.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_saved_grouping_revisions as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = ("rename", "replace_from_plan", "retire")
MODES = ("default", "alternate", "cancel")


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


def test_revision_request_and_digest_are_prepared_in_the_actor_callback() -> None:
    tree = ast.parse(
        (ROOT / "concord/menu_saved_grouping_revisions.py").read_text(encoding="utf-8")
    )
    operation = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == "_change"
    )
    callbacks = [
        item
        for item in ast.walk(operation)
        if isinstance(item, ast.FunctionDef) and item.name == "_prepare_for_actor"
    ]
    assert len(callbacks) == 1
    callback = callbacks[0]
    assert len(_calls(callback, "ChangeGroupingRequest")) == 1
    assert len(_calls(callback, "prepare_grouping_change")) == 1
    assert len(_calls(operation, "confirm_prepared_actor_write")) == 1
    assert len(_calls(operation, "change_grouping")) == 1
    assert not _calls(operation, "confirm_actor_write")
    confirm = _calls(operation, "confirm_prepared_actor_write")[0]
    assert {kw.arg for kw in confirm.keywords} >= {
        "state",
        "legacy_confirm",
        "prepare_for_actor",
    }
    write = _calls(operation, "change_grouping")[0]
    assert isinstance(write.args[0], ast.Name)
    assert write.args[0].id == "request"
    digest = next(kw.value for kw in write.keywords if kw.arg == "review_digest")
    assert isinstance(digest, ast.Name) and digest.id == "review_digest"
    assert confirm.lineno < write.lineno


@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("mode", MODES)
def test_revision_actor_switch_keeps_canonical_request_and_digest_paired(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    mode: str,
) -> None:
    saved_actor = WorkflowActor(actor_id="teacher-default", display_label="Default")
    alternate = WorkflowActor(actor_id="teacher-alternate", display_label="Alternate")
    state = MenuSessionContext(actor=saved_actor)
    activity = SimpleNamespace(
        class_id="synthetic-class", activity_id="activity-one", snapshot_revision=7
    )
    selected = SimpleNamespace(
        sha256="a" * 64,
        revision=SimpleNamespace(
            arrangement_id="six-tables", revision=3, name="Six Tables"
        ),
    )
    reviews: list[tuple[Any, str]] = []
    writes: list[tuple[Any, str]] = []
    displayed: list[object] = []
    monkeypatch.setattr(menu, "show_result", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        menu,
        "confirm_write",
        lambda *_a, **_kw: pytest.fail("Legacy confirmation"),
    )
    monkeypatch.setattr(
        menu,
        "prompt_text",
        lambda *_a, **_kw: "Six Tables Revised",
    )
    monkeypatch.setattr(
        menu,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=activity),
    )
    monkeypatch.setattr(
        menu,
        "list_group_plans",
        lambda *_a: (
            SimpleNamespace(
                group_plan_id="source-plan",
                status="draft",
                proposed_group_count=6,
                assigned_student_count=30,
            ),
        ),
    )
    monkeypatch.setattr(menu, "select_one", lambda _title, items, *_a, **_kw: items[0])

    def prepare(request: Any) -> Any:
        assert request.class_id == "synthetic-class"
        assert request.arrangement_id == "six-tables"
        assert request.expected_revision == 3
        assert request.expected_sha256 == "a" * 64
        assert request.action == action
        if action == "rename":
            assert request.new_name == "Six Tables Revised"
        if action == "replace_from_plan":
            assert request.source_group_plan_id == "source-plan"
            assert request.source_activity_id == "activity-one"
            assert request.expected_source_snapshot_revision == 7
        digest = hashlib.sha256(
            f"{action}:{request.actor.actor_id}:3".encode()
        ).hexdigest()
        reviews.append((request, digest))
        return SimpleNamespace(
            review_digest=digest,
            name="Six Tables Revised" if action == "rename" else "Six Tables",
            previous_revision=3,
            new_revision=4,
            groups=(SimpleNamespace(label="Table A", student_ids=("s1",)),),
            assigned_count=1,
            unresolved_student_ids=(),
            status="retired" if action == "retire" else "active",
        )

    monkeypatch.setattr(menu, "prepare_grouping_change", prepare)

    def confirm(_title: str, expected: str, **kwargs: Any) -> Any:
        assert (
            expected
            == {
                "rename": "RENAME",
                "replace_from_plan": "REVISE",
                "retire": "RETIRE",
            }[action]
        )
        assert kwargs["state"] is state
        assert kwargs["legacy_confirm"] is menu.confirm_write
        seq = (saved_actor,) if mode == "default" else (saved_actor, alternate)
        pending = None
        for actor in seq:
            pending, lines = kwargs["prepare_for_actor"](actor)
            assert len(lines) >= 7
            assert all(isinstance(line, str) for line in lines)
        return None if mode == "cancel" else pending

    monkeypatch.setattr(menu, "confirm_prepared_actor_write", confirm)

    def commit(request: Any, *, review_digest: str) -> Any:
        assert reviews
        assert request is reviews[-1][0]
        assert review_digest == reviews[-1][1]
        writes.append((request, review_digest))
        return SimpleNamespace(
            revision=SimpleNamespace(
                name="Six Tables Revised",
                revision=4,
                status="retired" if action == "retire" else "active",
            ),
        )

    monkeypatch.setattr(menu, "change_grouping", commit)
    result = menu._change(
        activity,
        state,
        selected,
        action,
        show_placements=lambda *_a, **_kw: displayed.append(True),
    )
    assert result is (mode != "cancel")
    assert len(reviews) == (1 if mode == "default" else 2)
    assert len(writes) == (0 if mode == "cancel" else 1)
    if mode != "cancel":
        expected_actor = saved_actor if mode == "default" else alternate
        assert writes[0][0].actor == expected_actor
    assert len(displayed) == (len(reviews) if action == "replace_from_plan" else 0)
    assert state.actor == saved_actor


def test_revision_denied_alternate_owner_does_not_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_actor = WorkflowActor(actor_id="teacher-default")
    alternate = WorkflowActor(actor_id="teacher-alternate")
    activity = SimpleNamespace(class_id="synthetic-class", activity_id="one")
    selected = SimpleNamespace(
        sha256="a" * 64,
        revision=SimpleNamespace(
            arrangement_id="six-tables", revision=1, name="Six Tables"
        ),
    )
    state = MenuSessionContext(actor=saved_actor)
    monkeypatch.setattr(menu, "prompt_text", lambda *_a, **_kw: "Renamed")
    writes: list[object] = []

    def prepare(request: Any) -> Any:
        if request.actor == alternate:
            raise PermissionError("Grouping is not owned by the selected actor")
        return SimpleNamespace(
            review_digest="a" * 64,
            name="Renamed",
            previous_revision=1,
            new_revision=2,
            groups=(),
            assigned_count=0,
            unresolved_student_ids=(),
            status="active",
        )

    monkeypatch.setattr(menu, "prepare_grouping_change", prepare)
    monkeypatch.setattr(
        menu,
        "confirm_prepared_actor_write",
        lambda _title, _expected, **kw: (
            kw["prepare_for_actor"](saved_actor),
            kw["prepare_for_actor"](alternate),
        ),
    )
    monkeypatch.setattr(menu, "change_grouping", lambda *_a, **_kw: writes.append(True))
    with pytest.raises(PermissionError, match="not owned"):
        menu._change(
            activity,
            state,
            selected,
            "rename",
            show_placements=lambda *_a, **_kw: None,
        )
    assert writes == []
    assert state.actor == saved_actor
