"""#153 D2: preserve Core navigation across consequential action boundaries."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_activity as activity_menu
import concord.menu_packet_generation as packet_menu
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.menu_prompts import select_one
from concord.workflows import ActivitySummary, WorkflowActor

ACTIVITY = ActivitySummary(
    class_id="class-1",
    activity_id="activity-1",
    title="Synthetic Activity",
    status="draft",
    scoring_orientation="evidence_only",
    session_count=1,
    group_count=0,
    snapshot_revision=1,
)
ROUTES = (
    "create",
    "copy",
    "edit",
    "generate",
    "open",
    "render-generation",
    "inspect",
    "render-instance",
    "resume",
)


def _choose(*_args: object, **_kwargs: object) -> str:
    return select_one("Synthetic selection", ("one",), ("One",), help_text="Choose one.")


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_nested_action_navigation_never_becomes_error_or_write(
    monkeypatch: pytest.MonkeyPatch, route: str, choice: str
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Navigation must not cause a write, viewer launch or error receipt")

    for name in ("create_activity_context", "copy_activity", "update_activity"):
        monkeypatch.setattr(activity_menu, name, forbidden)
    for name in (
        "commit_packet_instantiation",
        "render_packet_generation",
        "render_packet_instance",
        "resume_packet_instantiation",
        "open_rendered_packet_output",
    ):
        monkeypatch.setattr(packet_menu, name, forbidden)
    monkeypatch.setattr(activity_menu, "show_result", forbidden)
    monkeypatch.setattr(activity_menu, "handle_write_error", forbidden)
    monkeypatch.setattr(packet_menu, "show_result", forbidden)
    monkeypatch.setattr(
        activity_menu, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(activity_menu, "list_available_classes", lambda *_a: (object(),))
    monkeypatch.setattr(activity_menu, "list_activities", lambda **_k: (ACTIVITY,))
    monkeypatch.setattr(
        activity_menu,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=ACTIVITY),
    )
    monkeypatch.setattr(activity_menu, "choose_class", _choose)
    monkeypatch.setattr(activity_menu, "select_one", _choose)
    monkeypatch.setattr(activity_menu, "prompt_text", _choose)
    monkeypatch.setattr(packet_menu, "_choose_active_packet", _choose)
    monkeypatch.setattr(packet_menu, "_choose_ready_instance", _choose)
    monkeypatch.setattr(packet_menu, "_choose_generation", _choose)
    monkeypatch.setattr(packet_menu, "_choose_instance", _choose)
    monkeypatch.setattr(packet_menu, "select_one", _choose)
    monkeypatch.setattr(
        packet_menu,
        "list_packet_instances",
        lambda *_a: (
            SimpleNamespace(
                generation_id="generation-1", generation_status="routes_pending"
            ),
        ),
    )
    actions = {
        "create": lambda: activity_menu._create_activity(state),
        "copy": lambda: activity_menu._copy_activity(state),
        "edit": lambda: activity_menu._update_activity_field(ACTIVITY, state, "title"),
        "generate": lambda: packet_menu._generate(ACTIVITY, state),
        "open": lambda: packet_menu._open_ready_packet(ACTIVITY),
        "render-generation": lambda: packet_menu._render_generation(ACTIVITY, state),
        "inspect": lambda: packet_menu._inspect_instance(ACTIVITY),
        "render-instance": lambda: packet_menu._render_instance(ACTIVITY, state),
        "resume": lambda: packet_menu._resume_generation(ACTIVITY),
    }
    if choice == "b":
        assert actions[route]() is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            actions[route]()


@pytest.mark.parametrize("choice", ("b", "m", "q"))
def test_render_review_navigation_never_authorizes_render(
    monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    state = MenuSessionContext(actor=WorkflowActor(actor_id="synthetic-teacher"))
    instance = SimpleNamespace(
        generation_status="generated",
        packet_instance_id="packet-instance-1",
        target_key="synthetic-target",
    )
    monkeypatch.setattr(packet_menu, "_choose_instance", lambda *_a, **_k: instance)
    monkeypatch.setattr("builtins.input", lambda _prompt="": choice)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Navigation from confirmation must not render or show an error")

    monkeypatch.setattr(packet_menu, "render_packet_instance", forbidden)
    monkeypatch.setattr(packet_menu, "show_result", forbidden)
    if choice == "b":
        assert packet_menu._render_instance(ACTIVITY, state) is None
    else:
        error = ReturnToMainMenu if choice == "m" else QuitPDS
        with pytest.raises(error):
            packet_menu._render_instance(ACTIVITY, state)
