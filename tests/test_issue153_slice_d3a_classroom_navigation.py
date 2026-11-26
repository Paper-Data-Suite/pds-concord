"""#153 D3a: local classroom planning navigation boundaries."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_group as group_menu
import concord.menu_group_plan as plan_menu
import concord.menu_responsibility as responsibility_menu
import concord.menu_role as role_menu
import concord.menu_session as session_menu
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.menu_prompts import select_one
from concord.workflows import ActivitySummary, SessionSummary, WorkflowActor

ACTIVITY = ActivitySummary(
    class_id="class-1",
    activity_id="activity-1",
    title="Synthetic Activity",
    status="draft",
    scoring_orientation="evidence_only",
    session_count=1,
    group_count=1,
    snapshot_revision=1,
)
SESSION = SessionSummary(
    class_id="class-1",
    activity_id="activity-1",
    session_id="session-1",
    sequence=1,
    label="Day 1",
    status="planned",
    scheduled_start=None,
    snapshot_revision=1,
)
ROUTES = (
    ("group", "_create_group", "prompt_text"),
    ("group", "_edit_group", "choose_group"),
    ("group", "_add_member", "choose_group"),
    ("group", "_end_member", "choose_membership"),
    ("group", "_reassign_member", "choose_membership"),
    ("session", "_add", "prompt_text"),
    ("session", "_edit_field", "prompt_text"),
    ("role", "_assign", "choose_student"),
    ("role", "_save_role_as_preset", "_choose_existing"),
    ("role", "_end", "_choose_existing"),
    ("role", "_reassign", "_choose_existing"),
    ("responsibility", "_assign", "_choose_assignee"),
    ("responsibility", "_save_responsibility_as_preset", "_choose_existing"),
    ("responsibility", "_end", "_choose_existing"),
    ("responsibility", "_reassign", "_choose_existing"),
    ("plan", "_create_manual", "prompt_text"),
    ("plan", "_create_random", "prompt_text"),
    ("plan", "_import_arrangement", "prompt_text"),
)
MODULES = {
    "group": group_menu,
    "session": session_menu,
    "role": role_menu,
    "responsibility": responsibility_menu,
    "plan": plan_menu,
}


def _forbidden(*_args: object, **_kwargs: object) -> None:
    pytest.fail("Navigation must not reach a mutation or operational error receipt")


def _choose(*_args: object, **_kwargs: object) -> str:
    return select_one("Synthetic choice", ("one",), ("One",), help_text="Choose one.")


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher"))


@pytest.mark.parametrize(("module_name", "action", "prompt"), ROUTES)
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_classroom_action_navigation_unwinds(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    action: str,
    prompt: str,
    choice: str,
) -> None:
    module = MODULES[module_name]
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)
    monkeypatch.setattr(module, "_latest", lambda *_a: ACTIVITY)
    monkeypatch.setattr(module, "_handle_error", _forbidden)
    monkeypatch.setattr(module, "show_result", _forbidden)
    monkeypatch.setattr(module, "confirm_actor_write", _forbidden)
    item = SimpleNamespace(status="active", sequence=1)
    for name in (
        "list_groups",
        "list_memberships",
        "list_roles",
        "list_responsibilities",
        "list_sessions",
    ):
        if hasattr(module, name):
            monkeypatch.setattr(module, name, lambda *_a: (item,))
    if hasattr(module, "resolve_workspace_root"):
        monkeypatch.setattr(module, "resolve_workspace_root", lambda: Path("synthetic"))
    monkeypatch.setattr(module, prompt, _choose)
    run = getattr(module, action)
    args = (
        (ACTIVITY, SESSION, _state(), "label")
        if action == "_edit_field"
        else (ACTIVITY, _state())
    )
    if choice == "b":
        assert run(*args) is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            run(*args)


@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_group_edit_nested_field_navigation_unwinds(
    monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    selected = SimpleNamespace(group_id="group-1", label="Cluster A")
    answers = iter(("1", choice))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(group_menu, "list_groups", lambda *_a: (selected,))
    monkeypatch.setattr(group_menu, "choose_group", lambda *_a, **_k: selected)
    monkeypatch.setattr(group_menu, "show_group", lambda *_a: SimpleNamespace())
    monkeypatch.setattr(group_menu, "_latest", lambda *_a: ACTIVITY)
    monkeypatch.setattr(group_menu, "prompt_text", _choose)
    monkeypatch.setattr(group_menu, "_handle_error", _forbidden)
    monkeypatch.setattr(group_menu, "show_result", _forbidden)
    monkeypatch.setattr(group_menu, "update_group", _forbidden)
    if choice == "b":
        assert group_menu._edit_group(ACTIVITY, _state()) is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            group_menu._edit_group(ACTIVITY, _state())
