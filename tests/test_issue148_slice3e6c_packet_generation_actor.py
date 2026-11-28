"""#148 Slice 3E6C: exact actor attribution in Packet generation/reprint.

All inputs are synthetic. No classroom workspace, user profile, or actual PDFs.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from concord import menu_packet_generation as menu
from concord.menu_context import MenuSessionContext
from concord.workflows import WorkflowActor

ROOT = Path(__file__).resolve().parents[1]


def _actors() -> tuple[WorkflowActor, WorkflowActor, MenuSessionContext]:
    default = WorkflowActor(actor_id="adult-default", display_label="Default Adult")
    alternate = WorkflowActor(
        actor_id="adult-alternate", display_label="Alternate Adult"
    )
    return default, alternate, MenuSessionContext(actor=default)


def _activity() -> Any:
    return SimpleNamespace(class_id="class-synthetic", activity_id="activity-synthetic")


def _no_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def result(title: str, *_args: Any, **_kwargs: Any) -> None:
        if "Error" in title or "Partial Success" in title:
            pytest.fail(f"Unexpected workflow error: {title}")

    monkeypatch.setattr(menu, "show_result", result)


def _function(name: str) -> ast.FunctionDef:
    tree = ast.parse(
        (ROOT / "concord/menu_packet_generation.py").read_text(encoding="utf-8")
    )
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _calls(node: ast.AST, name: str) -> list[ast.Call]:
    return [
        call
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == name
    ]


def test_source_review_is_bound_to_canonical_packet_writes() -> None:
    generated = _function("_generate")
    reviews = _calls(generated, "confirm_prepared_actor_write")
    writes = _calls(generated, "commit_packet_instantiation")
    render = _calls(generated, "RenderPacketGenerationRequest")
    assert len(reviews) == len(writes) == len(render) == 1
    assert isinstance(writes[0].args[0], ast.Name)
    assert writes[0].args[0].id == "reviewed"
    assert any(
        kw.arg == "actor"
        and isinstance(kw.value, ast.Attribute)
        and kw.value.attr == "actor"
        and isinstance(kw.value.value, ast.Attribute)
        and kw.value.value.attr == "request"
        for kw in render[0].keywords
    )
    for fn, request_name in (
        ("_render_generation", "RenderPacketGenerationRequest"),
        ("_render_instance", "RenderPacketInstanceRequest"),
    ):
        node = _function(fn)
        assert len(_calls(node, "confirm_actor_write")) == 1
        requests = _calls(node, request_name)
        assert len(requests) == 1
        assert any(
            kw.arg == "actor"
            and isinstance(kw.value, ast.Name)
            and kw.value.id == "actor"
            for kw in requests[0].keywords
        )


@pytest.mark.parametrize("choice", ["alternate", "default", "cancel"])
def test_packet_generate_reprepares_and_renders_with_approved_actor(
    monkeypatch: pytest.MonkeyPatch, choice: str
) -> None:
    default, alternate, state = _actors()
    activity = _activity()
    summary = SimpleNamespace(packet_definition_id="packet-synthetic")
    version = SimpleNamespace(packet_version_id="version-synthetic", components=())
    detail = SimpleNamespace(
        summary=SimpleNamespace(current_packet_version_id="version-synthetic"),
        versions=(version,),
    )
    session = SimpleNamespace(session_id="session-synthetic")
    prepared_requests: list[Any] = []
    committed: list[Any] = []
    rendered: list[Any] = []
    shown: list[Any] = []

    monkeypatch.setattr(menu, "_choose_active_packet", lambda: summary)
    monkeypatch.setattr(menu, "get_packet", lambda *_a: detail)
    monkeypatch.setattr(menu, "_choose_session", lambda *_a: session)
    monkeypatch.setattr(menu, "_component_choices", lambda *_a: ())

    def prepare(request: Any) -> Any:
        prepared_requests.append(request)
        return SimpleNamespace(
            request=request,
            ready_for_commit=True,
            diagnostics=(),
            review_digest=request.actor.actor_id + "-digest",
        )

    monkeypatch.setattr(menu, "prepare_packet_instantiation", prepare)
    monkeypatch.setattr(menu, "_prompt_missing_bindings", lambda *_a: ())
    monkeypatch.setattr(menu, "_prompt_missing_subject_bindings", lambda *_a: ())
    monkeypatch.setattr(
        menu, "_preview_lines", lambda p: ("Review: " + p.request.actor.actor_id,)
    )

    def confirm(
        title: str,
        expected: str,
        *,
        state: MenuSessionContext,
        legacy_confirm: Any,
        prepare_for_actor: Any,
        prepare_details: Any,
        legacy_details_confirm: Any,
    ) -> Any:
        assert (title, expected) == ("Generate Packet", "GENERATE")
        assert state.actor == default
        assert callable(legacy_confirm)
        first, first_lines = prepare_for_actor(default)
        second, second_lines = prepare_for_actor(alternate)
        assert first.request.actor == default
        assert second.request.actor == alternate
        assert first.request.packet_definition_id == second.request.packet_definition_id
        assert first_lines != second_lines
        assert callable(legacy_details_confirm)
        assert prepare_details(first) == (f"Review digest: {first.review_digest}",)
        assert prepare_details(second) == (f"Review digest: {second.review_digest}",)
        if choice == "cancel":
            return None
        if choice == "default":
            third, _ = prepare_for_actor(default)
            return third
        return second

    monkeypatch.setattr(menu, "confirm_prepared_actor_write", confirm)
    monkeypatch.setattr(
        menu,
        "confirm_write",
        lambda *_a, **_kw: pytest.fail("Legacy confirmation bypassed actor review"),
    )
    monkeypatch.setattr(
        menu,
        "commit_packet_instantiation",
        lambda p: committed.append(p) or SimpleNamespace(generation_id="gen-1"),
    )
    monkeypatch.setattr(
        menu,
        "render_packet_generation",
        lambda req: rendered.append(req) or SimpleNamespace(generation_id="gen-1"),
    )
    monkeypatch.setattr(
        menu, "_post_generation_open_menu", lambda *_a: shown.append(True)
    )
    _no_error(monkeypatch)
    menu._generate(activity, state)
    assert len(committed) == len(rendered) == len(shown) == int(choice != "cancel")
    assert len(prepared_requests) >= 3
    if committed:
        expected = alternate if choice == "alternate" else default
        assert committed[0].request.actor == expected
        assert rendered[0].actor == expected
        assert rendered[0].generation_id == "gen-1"
    assert state.actor == default


@pytest.mark.parametrize("approved", [True, False])
def test_generation_reprint_forwards_reviewed_actor_and_snapshot(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    default, alternate, state = _actors()
    selected = SimpleNamespace(
        routes_pending_count=0,
        planned_count=0,
        failed_count=0,
        cancelled_count=0,
        generated_count=2,
        instance_count=2,
        rendering_count=0,
        packet_name="Synthetic Packets",
        packet_version_label="1.0",
        session_label="Session Synthetic",
        page_count=8,
        route_count=2,
        generation_id="generation-synthetic",
        snapshot_revision=19,
    )
    writes: list[Any] = []
    monkeypatch.setattr(menu, "_choose_generation", lambda *_a, **_k: selected)

    def confirm(title: str, expected: str, lines: Any, **kw: Any) -> Any:
        assert (title, expected) == ("Reprint Packet Generation", "REPRINT")
        assert any("Existing Packet" in line for line in lines)
        assert kw["state"] is state
        return alternate if approved else None

    monkeypatch.setattr(menu, "confirm_actor_write", confirm)
    monkeypatch.setattr(
        menu,
        "confirm_write",
        lambda *_a, **_kw: pytest.fail("Legacy review bypassed actor choice"),
    )
    monkeypatch.setattr(
        menu,
        "render_packet_generation",
        lambda request: (
            writes.append(request)
            or SimpleNamespace(packets=("one", "two"), page_count=8, route_count=2)
        ),
    )
    _no_error(monkeypatch)
    menu._render_generation(_activity(), state)
    assert len(writes) == int(approved)
    if writes:
        assert writes[0].actor == alternate
        assert writes[0].expected_snapshot_revision == 19
        assert writes[0].generation_id == "generation-synthetic"
    assert state.actor == default


@pytest.mark.parametrize("approved", [True, False])
def test_instance_render_forwards_reviewed_actor_or_cancels(
    monkeypatch: pytest.MonkeyPatch, approved: bool
) -> None:
    default, alternate, state = _actors()
    instance = SimpleNamespace(
        packet_instance_id="instance-synthetic",
        target_key="participant-synthetic",
        generation_status="generated",
    )
    writes: list[Any] = []
    monkeypatch.setattr(menu, "_choose_instance", lambda *_a, **_k: instance)

    def confirm(title: str, expected: str, lines: Any, **kw: Any) -> Any:
        assert (title, expected) == ("Render / Reprint Packet", "REPRINT")
        assert any("participant-synthetic" in line for line in lines)
        assert kw["state"] is state
        return alternate if approved else None

    monkeypatch.setattr(menu, "confirm_actor_write", confirm)
    monkeypatch.setattr(
        menu,
        "confirm_write",
        lambda *_a, **_kw: pytest.fail("Legacy review bypassed actor choice"),
    )
    monkeypatch.setattr(
        menu,
        "render_packet_instance",
        lambda req: (
            writes.append(req)
            or SimpleNamespace(
                output_path=Path("/synthetic/packet.pdf"),
                output_sha256="e" * 64,
                page_count=2,
                route_count=1,
                replayed=True,
            )
        ),
    )
    _no_error(monkeypatch)
    receipts: list[tuple[str, Any, Any]] = []
    monkeypatch.setattr(
        menu,
        "show_result_with_details",
        lambda title, lines, details: receipts.append((title, lines, details)),
    )
    menu._render_instance(_activity(), state)
    assert len(receipts) == int(approved)
    if receipts:
        assert "Output SHA-256" not in "\n".join(receipts[0][1])
        assert receipts[0][2] == (f"Output SHA-256: {'e' * 64}",)
    assert len(writes) == int(approved)
    if writes:
        assert writes[0].actor == alternate
        assert writes[0].packet_instance_id == "instance-synthetic"
    assert state.actor == default
