"""#148 3E6B: guided Activity creation/copy and one-Template Packet attribution.

Only synthetic actors, classes, templates and Packet identities are used.
No teacher profile, actual roster, student records, or workspace is opened.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_guided_activity as guided
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]


def _actors() -> tuple[WorkflowActor, WorkflowActor, MenuSessionContext]:
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(actor_id="adult-alternate", display_label="Other Adult")
    return default, alternate, MenuSessionContext(actor=default)


def _call_names(node: ast.AST) -> list[str]:
    return [
        call.func.id
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    ]


def test_guided_writes_have_scoped_review_and_prepared_packet_callback() -> None:
    tree = ast.parse(
        (ROOT / "concord/menu_guided_activity.py").read_text(encoding="utf-8")
    )
    by_name = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    for name, service in (
        ("_create_fresh", "create_activity_context"),
        ("_create_from_activity", "copy_activity"),
    ):
        fn = by_name[name]
        calls = _call_names(fn)
        assert calls.count("confirm_actor_write") == 1
        assert calls.count(service) == 1
        assert "require_actor" not in calls
        assert "confirm_write" not in calls
        writes = [
            call
            for call in ast.walk(fn)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == service
        ]
        requests = [
            call
            for call in ast.walk(writes[0])
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id in ("CopyActivityRequest", "CreateActivityContextRequest")
        ]
        assert len(requests) == 1
        actor = next(k.value for k in requests[0].keywords if k.arg == "actor")
        assert isinstance(actor, ast.Name) and actor.id == "actor"
    fn = by_name["_start_packet_from_template"]
    calls = _call_names(fn)
    assert calls.count("confirm_prepared_actor_write") == 1
    assert calls.count("commit_packet_from_template") == 1
    assert "require_actor" not in calls
    callbacks = [
        n
        for n in ast.walk(fn)
        if isinstance(n, ast.FunctionDef) and n.name == "prepare_for_actor"
    ]
    assert len(callbacks) == 1
    callback_calls = _call_names(callbacks[0])
    assert callback_calls.count("prepare_packet_from_template") == 1
    request = next(
        n
        for n in ast.walk(callbacks[0])
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "PreparePacketFromTemplateRequest"
    )
    value = next(k.value for k in request.keywords if k.arg == "actor")
    assert isinstance(value, ast.Name) and value.id == "actor"


@pytest.mark.parametrize("approved", [True, False])
def test_guided_fresh_actor_override_or_cancel(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    default, alternate, state = _actors()
    choice = SimpleNamespace(class_id="class-synthetic")
    written: list[Any] = []
    monkeypatch.setattr(guided, "choose_class", lambda _items: choice)
    monkeypatch.setattr(guided, "_choose_activity_type", lambda: "project")
    monkeypatch.setattr(guided, "_choose_assessment", lambda: "evidence_only")
    monkeypatch.setattr(guided, "_standards_for", lambda _: (None, None, ()))
    monkeypatch.setattr(guided, "_fresh_id", lambda prefix: prefix + "-synthetic")
    monkeypatch.setattr(
        guided,
        "prompt_text",
        lambda _title, name, **_kw: {
            "Activity title": "Synthetic seminar",
            "Short description": None,
            "First session": "Day 1",
        }[name],
    )
    monkeypatch.setattr(
        guided, "confirm_write", lambda *_a, **_k: pytest.fail("Legacy bypass")
    )
    monkeypatch.setattr(
        guided,
        "confirm_actor_write",
        lambda *_a, **kw: alternate if approved else None,
    )
    monkeypatch.setattr(
        guided,
        "create_activity_context",
        lambda request, **_k: (
            written.append(request) or SimpleNamespace(activity_id=request.activity_id)
        ),
    )
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(summary=SimpleNamespace(title="Synthetic seminar")),
    )
    monkeypatch.setattr(guided, "_offer_after_creation", lambda *_a, **_k: None)
    guided._create_fresh(state, (choice,))
    assert len(written) == (1 if approved else 0)
    if written:
        assert written[0].actor == alternate
        assert written[0].session_id == "session-synthetic"
        assert written[0].class_id == choice.class_id
    assert state.actor == default


@pytest.mark.parametrize("approved", [True, False])
def test_guided_copy_actor_override_digest_or_cancel(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    default, alternate, state = _actors()
    source = SimpleNamespace(
        class_id="class-source",
        activity_id="activity-source",
        title="Source",
        status="draft",
    )
    target = SimpleNamespace(class_id="class-target")
    written: list[Any] = []
    digest = "f" * 64
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("/synthetic")
    )
    monkeypatch.setattr(guided, "list_activities", lambda **_kw: (source,))
    monkeypatch.setattr(guided, "_guided_activity_choice", lambda *_a, **_k: source)
    monkeypatch.setattr(guided, "choose_class", lambda _choices: target)
    monkeypatch.setattr(guided, "_fresh_id", lambda prefix: prefix + "-synthetic")
    monkeypatch.setattr(guided, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided,
        "prompt_text",
        lambda _title, name, **_kw: {
            "New Activity title": "Synthetic copy",
            "First session": "Day 1",
        }[name],
    )
    monkeypatch.setattr(
        guided,
        "prepare_activity_copy",
        lambda *_a, **_k: SimpleNamespace(
            activity_type="project",
            scoring_orientation="evidence_only",
            review_digest=digest,
        ),
    )
    monkeypatch.setattr(
        guided, "confirm_write", lambda *_a, **_k: pytest.fail("Legacy bypass")
    )
    monkeypatch.setattr(
        guided,
        "confirm_actor_write",
        lambda *_a, **kw: alternate if approved else None,
    )
    monkeypatch.setattr(
        guided,
        "copy_activity",
        lambda request, **_k: (
            written.append(request)
            or SimpleNamespace(activity_id=request.target_activity_id)
        ),
    )
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a: SimpleNamespace(
            summary=SimpleNamespace(
                title="Synthetic copy",
                class_id=target.class_id,
                activity_id="activity-synthetic",
            )
        ),
    )
    monkeypatch.setattr(guided, "_offer_after_creation", lambda *_a, **_k: None)
    guided._create_from_activity(state, (target,))
    assert len(written) == (1 if approved else 0)
    if written:
        assert written[0].actor == alternate
        assert written[0].review_digest == digest
        assert written[0].target_class_id == target.class_id
    assert state.actor == default


@pytest.mark.parametrize("choice", ["alternate", "default", "cancel"])
def test_guided_packet_reprepares_actor_and_commits_exact_review_or_cancels(
    monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    default, alternate, state = _actors()
    activity = SimpleNamespace(title="Synthetic lesson")
    template = SimpleNamespace(
        template_id="template-synthetic",
        name="Synthetic Template",
        status="active",
        current_template_version_id="version-synthetic",
        artifact_category="handout",
    )
    version = SimpleNamespace(template_version_id="version-synthetic")
    prepare_calls: list[Any] = []
    committed: list[Any] = []
    reviewed: list[Any] = []
    monkeypatch.setattr(guided, "list_templates", lambda: (template,))
    monkeypatch.setattr(guided, "select_one", lambda *_a, **_k: template)
    monkeypatch.setattr(
        guided, "get_template", lambda _id: SimpleNamespace(versions=(version,))
    )
    monkeypatch.setattr(guided, "_simple_template_audience", lambda _v: "activity")
    monkeypatch.setattr(guided, "prompt_text", lambda *_a, **_k: "Synthetic Packet")
    monkeypatch.setattr(guided, "_fresh_id", lambda p: p + "-synthetic")
    monkeypatch.setattr(
        guided,
        "prepare_packet_from_template",
        lambda request: (
            prepare_calls.append(request)
            or SimpleNamespace(
                recorded_actor=request.actor,
                packet_definition_id=request.packet_definition_id,
            )
        ),
    )

    def review(
        _title: str,
        _expected: str,
        *,
        state: Any,
        legacy_confirm: Any,
        prepare_for_actor: Any,
    ) -> Any:
        assert state.actor == default
        assert callable(legacy_confirm)
        first, first_lines = prepare_for_actor(default)
        second, second_lines = prepare_for_actor(alternate)
        assert first.recorded_actor == default
        assert second.recorded_actor == alternate
        assert first.packet_definition_id == second.packet_definition_id
        assert any("Synthetic Template" in line for line in first_lines)
        assert first_lines == second_lines
        if choice == "cancel":
            return None
        if choice == "default":
            third, _lines = prepare_for_actor(default)
            reviewed.append(third)
            return third
        reviewed.append(second)
        return second

    monkeypatch.setattr(guided, "confirm_prepared_actor_write", review)
    monkeypatch.setattr(
        guided, "confirm_write", lambda *_a, **_k: pytest.fail("Legacy bypass")
    )
    monkeypatch.setattr(
        guided,
        "commit_packet_from_template",
        lambda prepared: (
            committed.append(prepared)
            or SimpleNamespace(packet_definition_id=prepared.packet_definition_id)
        ),
    )
    monkeypatch.setattr(
        guided,
        "list_packets",
        lambda: (
            SimpleNamespace(
                packet_definition_id="packet-synthetic",
                name="Synthetic Packet",
            ),
        ),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(guided, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(guided, "print_navigation", lambda: None)
    guided._start_packet_from_template(activity, state)
    assert len(prepare_calls) == (3 if choice == "default" else 2)
    assert len(committed) == (0 if choice == "cancel" else 1)
    if committed:
        assert committed[0] is reviewed[0]
        assert committed[0].recorded_actor == (
            default if choice == "default" else alternate
        )
    assert state.actor == default
