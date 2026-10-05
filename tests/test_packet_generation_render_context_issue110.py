from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.workflows import packet_rendering
from concord.workflows.models import WorkflowActor


def test_packet_render_context_carries_one_exact_loaded_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    library = cast(StandardsLibrary, object())
    graph = cast(ConcordRecordGraph, SimpleNamespace())
    loaded = SimpleNamespace(
        snapshot_revision=17,
        snapshot_sha256="a" * 64,
        graph=graph,
    )
    calls: list[tuple[Path, ModuleWorkRef, object]] = []

    monkeypatch.setattr(packet_rendering, "_standards", lambda _root: library)

    def load_graph(
        root: Path,
        selected_work: ModuleWorkRef,
        *,
        standards_library: object,
    ) -> object:
        calls.append((root, selected_work, standards_library))
        return loaded

    monkeypatch.setattr(packet_rendering, "load_current_record_graph", load_graph)

    context = packet_rendering._load_packet_render_context(tmp_path, work)

    assert calls == [(tmp_path, work, library)]
    assert context.root == tmp_path
    assert context.work == work
    assert context.library is library
    assert context.snapshot_revision == 17
    assert context.snapshot_sha256 == "a" * 64
    assert context.graph is graph


def test_generated_generation_reprint_uses_one_context_not_public_instance_loop(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packet_b = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-b",
        generation_status="generated",
    )
    packet_a = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-a",
        generation_status="generated",
    )
    context = SimpleNamespace(
        root=tmp_path,
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        library=None,
        snapshot_revision=9,
        snapshot_sha256="b" * 64,
        graph=SimpleNamespace(packet_instances=(packet_b, packet_a)),
    )
    context_loads: list[tuple[Path, ModuleWorkRef]] = []
    rendered: list[str] = []

    monkeypatch.setattr(
        packet_rendering,
        "ensure_mutating_workspace_root",
        lambda _root: SimpleNamespace(root=tmp_path),
    )
    monkeypatch.setattr(
        packet_rendering,
        "require_core_class",
        lambda _root, _class_id: None,
    )

    def load_context(root: Path, work: ModuleWorkRef) -> object:
        context_loads.append((root, work))
        return context

    monkeypatch.setattr(
        packet_rendering,
        "_load_packet_render_context",
        load_context,
    )
    monkeypatch.setattr(
        packet_rendering,
        "_target_key",
        lambda packet: (0, packet.packet_instance_id),
    )
    monkeypatch.setattr(
        packet_rendering,
        "_packet_lifecycle_complete",
        lambda _graph, _packet: True,
    )

    def render_from_context(_context: object, packet: object) -> object:
        packet_id = cast(SimpleNamespace, packet).packet_instance_id
        rendered.append(packet_id)
        return SimpleNamespace(
            packet_instance_id=packet_id,
            page_count=1,
            route_count=1,
        )

    monkeypatch.setattr(
        packet_rendering,
        "_render_packet_from_context",
        render_from_context,
    )

    def public_instance_loop(*_args: object, **_kwargs: object) -> object:
        raise AssertionError(
            "generated generation replay must not call render_packet_instance()"
        )

    monkeypatch.setattr(
        packet_rendering,
        "render_packet_instance",
        public_instance_loop,
    )

    result = packet_rendering.render_packet_generation(
        packet_rendering.RenderPacketGenerationRequest(
            class_id="class-1",
            activity_id="activity-1",
            generation_id="generation-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=tmp_path,
    )

    assert context_loads == [
        (
            tmp_path,
            ModuleWorkRef("concord", "class-1", "activity-1"),
        )
    ]
    assert rendered == ["packet-a", "packet-b"]
    assert [item.packet_instance_id for item in result.packets] == [
        "packet-a",
        "packet-b",
    ]
