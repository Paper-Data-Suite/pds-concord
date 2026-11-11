"""#148 3C3B: digest preparation follows the reviewed actor, not a stale default.

All data and actors here are synthetic. No PDS academic workspace is touched.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from concord import menu_actor_action
from concord.menu_context import MenuSessionContext
from concord.teacher_attribution import TeacherAttributionIdentity
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ("_save_scale_id_as_preset", "save_scoring_scale_preset_from_activity"),
    ("_save_criterion_set_as_preset", "save_criterion_set_preset_from_activity"),
    ("_use_saved_scoring_setup", "materialize_scoring_setup"),
)


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        item
        for item in ast.walk(node)
        if isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == name
    ]


@pytest.mark.parametrize(("function_name", "write_name"), CASES)
def test_digest_review_keeps_exact_prepared_request_and_digest(
    function_name: str, write_name: str
) -> None:
    path = ROOT / "concord" / "menu_scoring.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == function_name
    )
    assert len(_calls(function, "confirm_prepared_actor_write")) == 1
    assert len(_calls(function, "confirm_write")) == 0
    assert len(_calls(function, "replace")) == 1
    assert len(_calls(function, write_name)) == 1
    save = _calls(function, write_name)[0]
    assert len(save.args) >= 1 and isinstance(save.args[0], ast.Name)
    assert save.args[0].id == "request"
    digest = next(kw.value for kw in save.keywords if kw.arg == "review_digest")
    assert isinstance(digest, ast.Attribute) and digest.attr == "review_digest"
    assert isinstance(digest.value, ast.Name) and digest.value.id == "prepared"
    assignments = [
        item
        for item in ast.walk(function)
        if isinstance(item, ast.Assign)
        and len(item.targets) == 1
        and isinstance(item.targets[0], ast.Tuple)
        and [part.id for part in item.targets[0].elts if isinstance(part, ast.Name)]
        == ["request", "prepared"]
    ]
    assert len(assignments) == 1
    reviewed = assignments[0].value
    assert isinstance(reviewed, ast.Name) and reviewed.id == "reviewed"
    actor_preparations = _calls(function, "replace")
    assert any(
        kw.arg == "actor" and isinstance(kw.value, ast.Name) and kw.value.id == "actor"
        for kw in actor_preparations[0].keywords
    )


class _FakeReviewState:
    attribution_provider = object()

    def __init__(self) -> None:
        self.default = WorkflowActor(
            actor_id="adult-default", display_label="Default Adult"
        )
        self.last_label: str | None = None

    def require_actor(self) -> WorkflowActor:
        return self.default

    def actor_for_action(
        self, *, action_label: str, alternate: TeacherAttributionIdentity | None = None
    ) -> WorkflowActor:
        self.last_label = action_label
        return self.default if alternate is None else alternate.workflow_actor()


def _digest(actor: WorkflowActor) -> str:
    value = f"{actor.actor_id}|{actor.display_label}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@pytest.mark.parametrize(
    ("choices", "expected_ids"),
    [
        (["SAVE"], ["adult-default"]),
        (["A", "SAVE"], ["adult-default", "adult-other"]),
        (["A", "D", "SAVE"], ["adult-default", "adult-other", "adult-default"]),
    ],
)
def test_actor_switch_reprepares_review_and_returns_matching_digest(
    choices: list[str],
    expected_ids: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state = _FakeReviewState()
    inputs = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(menu_actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_actor_action, "print_menu_header", lambda _title: None)
    monkeypatch.setattr(menu_actor_action, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_actor_action,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("adult-other", "Other Adult", "temporary"),
    )
    prepared_ids: list[str] = []

    def prepare(actor: WorkflowActor) -> tuple[SimpleNamespace, tuple[str, ...]]:
        prepared_ids.append(actor.actor_id)
        payload = SimpleNamespace(actor=actor, review_digest=_digest(actor))
        return payload, (f"Review digest: {payload.review_digest}",)

    result = menu_actor_action.confirm_prepared_actor_write(
        "Save Synthetic Preset",
        "SAVE",
        state=cast(MenuSessionContext, state),
        legacy_confirm=lambda *_args: pytest.fail("unexpected legacy confirmation"),
        prepare_for_actor=prepare,
    )
    assert result is not None
    assert prepared_ids == expected_ids
    assert result.actor.actor_id == expected_ids[-1]
    assert result.review_digest == _digest(result.actor)
    assert f"Review digest: {result.review_digest}" in capsys.readouterr().out
    assert state.last_label == "Save Synthetic Preset"


@pytest.mark.parametrize("choices", [[""], ["A", "B"]])
def test_cancel_never_returns_a_digest_bound_write(
    choices: list[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _FakeReviewState()
    inputs = iter(choices)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(menu_actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_actor_action, "print_menu_header", lambda _title: None)
    monkeypatch.setattr(menu_actor_action, "print_navigation", lambda: None)
    monkeypatch.setattr(
        menu_actor_action,
        "_choose_temporary_actor",
        lambda: TeacherAttributionIdentity("adult-other", "Other Adult", "temporary"),
    )
    result = menu_actor_action.confirm_prepared_actor_write(
        "Save Synthetic Preset",
        "SAVE",
        state=cast(MenuSessionContext, state),
        legacy_confirm=lambda *_args: pytest.fail("unexpected legacy confirmation"),
        prepare_for_actor=lambda actor: (
            SimpleNamespace(actor=actor, review_digest=_digest(actor)),
            ("Synthetic preview only",),
        ),
    )
    assert result is None


def test_legacy_explicit_actor_keeps_one_existing_confirmation() -> None:
    actor = WorkflowActor(actor_id="adult-legacy", display_label="Legacy Adult")
    state = MenuSessionContext(actor=actor)
    reviews: list[tuple[str, ...]] = []

    def legacy(_title: str, _token: str, lines: tuple[str, ...]) -> bool:
        reviews.append(lines)
        return True

    result = menu_actor_action.confirm_prepared_actor_write(
        "Synthetic Preset",
        "SAVE",
        state=state,
        legacy_confirm=legacy,
        prepare_for_actor=lambda selected: (
            SimpleNamespace(actor=selected, review_digest=_digest(selected)),
            (f"Digest: {_digest(selected)}",),
        ),
    )
    assert result is not None and result.actor == actor
    assert reviews == [(f"Digest: {_digest(actor)}",)]


def test_actor_changed_between_preview_and_confirmation_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _FakeReviewState()
    replacement = WorkflowActor(actor_id="adult-new", display_label="New Adult")
    count = 0

    def changing_actor(
        *, action_label: str, alternate: TeacherAttributionIdentity | None = None
    ) -> WorkflowActor:
        nonlocal count
        count += 1
        return replacement if count >= 3 else state.default

    monkeypatch.setattr(state, "actor_for_action", changing_actor)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "SAVE")
    monkeypatch.setattr(menu_actor_action, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_actor_action, "print_menu_header", lambda _title: None)
    monkeypatch.setattr(menu_actor_action, "print_navigation", lambda: None)
    with pytest.raises(RuntimeError, match="Reviewed actor differs"):
        menu_actor_action.confirm_prepared_actor_write(
            "Synthetic Preset",
            "SAVE",
            state=cast(MenuSessionContext, state),
            legacy_confirm=lambda *_args: True,
            prepare_for_actor=lambda actor: (
                SimpleNamespace(actor=actor, review_digest=_digest(actor)),
                ("Read-only preview",),
            ),
        )
