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
    work = ModuleWorkRef("concord", "class-1", "activity-1")
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
        work=work,
        library=None,
        snapshot_revision=9,
        snapshot_sha256="b" * 64,
        graph=SimpleNamespace(packet_instances=(packet_b, packet_a)),
    )
    context_loads: list[tuple[Path, ModuleWorkRef]] = []
    prepared: list[str] = []

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

    def load_context(root: Path, selected_work: ModuleWorkRef) -> object:
        context_loads.append((root, selected_work))
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
        "_require_renderable_packet",
        lambda _packet: None,
    )

    def prepare(_context: object, packet: object) -> object:
        packet_id = cast(SimpleNamespace, packet).packet_instance_id
        prepared.append(packet_id)
        result = _issue110_result(tmp_path, work, packet_id)
        return packet_rendering._PreparedPacketRender(
            result=packet_rendering.RenderPacketInstanceResult(
                work=result.work,
                packet_instance_id=result.packet_instance_id,
                generation_id=result.generation_id,
                output_path=result.output_path,
                output_sha256=result.output_sha256,
                page_count=result.page_count,
                route_count=result.route_count,
                payloads=result.payloads,
                commit=result.commit,
                output_installed=False,
                replayed=True,
            ),
            updates=(),
        )

    monkeypatch.setattr(
        packet_rendering,
        "_prepare_packet_render_from_context",
        prepare,
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
    monkeypatch.setattr(
        packet_rendering,
        "commit_record_batch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("generated replay must not commit lifecycle state")
        ),
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

    assert context_loads == [(tmp_path, work)]
    assert prepared == ["packet-a", "packet-b"]
    assert [item.packet_instance_id for item in result.packets] == [
        "packet-a",
        "packet-b",
    ]
    assert all(item.replayed for item in result.packets)
    assert all(item.commit.no_op for item in result.packets)
def _issue110_result(
    tmp_path: Path,
    work: ModuleWorkRef,
    packet_instance_id: str,
) -> packet_rendering.RenderPacketInstanceResult:
    return packet_rendering.RenderPacketInstanceResult(
        work=work,
        packet_instance_id=packet_instance_id,
        generation_id="generation-1",
        output_path=tmp_path / f"{packet_instance_id}.pdf",
        output_sha256="c" * 64,
        page_count=1,
        route_count=1,
        payloads=(f"PDS2:{packet_instance_id}",),
        commit=packet_rendering.WorkflowCommitResult(
            work=work,
            snapshot_revision=9,
            snapshot_sha256="b" * 64,
            changed_records=(),
            no_op=True,
        ),
        output_installed=True,
        replayed=False,
    )


def test_first_render_generation_uses_one_context_and_one_lifecycle_commit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from concord.storage_models import ConcordStorageCommitResult

    work = ModuleWorkRef("concord", "class-1", "activity-1")
    packet_b = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-b",
        generation_status="rendering",
    )
    packet_a = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-a",
        generation_status="rendering",
    )
    context = SimpleNamespace(
        root=tmp_path,
        work=work,
        library=None,
        snapshot_revision=9,
        snapshot_sha256="b" * 64,
        graph=SimpleNamespace(packet_instances=(packet_b, packet_a)),
    )
    context_loads: list[tuple[Path, ModuleWorkRef]] = []
    prepared_ids: list[str] = []
    commits: list[tuple[tuple[object, ...], int | None]] = []
    update_a = object()
    update_b = object()

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

    def load_context(root: Path, selected_work: ModuleWorkRef) -> object:
        context_loads.append((root, selected_work))
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
        "_require_renderable_packet",
        lambda _packet: None,
    )

    def prepare(_context: object, packet: object) -> object:
        packet_id = cast(SimpleNamespace, packet).packet_instance_id
        prepared_ids.append(packet_id)
        update = update_a if packet_id == "packet-a" else update_b
        return packet_rendering._PreparedPacketRender(
            result=_issue110_result(tmp_path, work, packet_id),
            updates=(update,),  # type: ignore[arg-type]
        )

    monkeypatch.setattr(
        packet_rendering,
        "_prepare_packet_render_from_context",
        prepare,
    )

    def commit(
        _root: Path,
        selected_work: ModuleWorkRef,
        records: object,
        *,
        expected_snapshot_revision: int | None,
        standards_library: object,
    ) -> ConcordStorageCommitResult:
        assert selected_work == work
        assert standards_library is None
        materialized = tuple(
            cast(object, item)
            for item in cast(tuple[object, ...], records)
        )
        commits.append((materialized, expected_snapshot_revision))
        return ConcordStorageCommitResult(
            work=work,
            snapshot_revision=10,
            snapshot_sha256="d" * 64,
            created_record_revisions=(),
            no_op=False,
        )

    monkeypatch.setattr(packet_rendering, "commit_record_batch", commit)

    def public_instance_loop(*_args: object, **_kwargs: object) -> object:
        raise AssertionError(
            "generation first render must not call render_packet_instance()"
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

    assert context_loads == [(tmp_path, work)]
    assert prepared_ids == ["packet-a", "packet-b"]
    assert commits == [((update_a, update_b), 9)]
    assert [item.packet_instance_id for item in result.packets] == [
        "packet-a",
        "packet-b",
    ]
    assert all(item.commit.snapshot_revision == 10 for item in result.packets)
    assert all(not item.commit.no_op for item in result.packets)


def test_generation_lifecycle_commit_failure_reports_all_durable_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from concord.storage_errors import ConcordStorageConflictError

    work = ModuleWorkRef("concord", "class-1", "activity-1")
    packets = tuple(
        SimpleNamespace(
            generation_id="generation-1",
            packet_instance_id=f"packet-{index}",
            generation_status="rendering",
        )
        for index in (1, 2)
    )
    context = SimpleNamespace(
        root=tmp_path,
        work=work,
        library=None,
        snapshot_revision=9,
        snapshot_sha256="b" * 64,
        graph=SimpleNamespace(packet_instances=packets),
    )

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
    monkeypatch.setattr(
        packet_rendering,
        "_load_packet_render_context",
        lambda _root, _work: context,
    )
    monkeypatch.setattr(
        packet_rendering,
        "_target_key",
        lambda packet: (0, packet.packet_instance_id),
    )
    monkeypatch.setattr(
        packet_rendering,
        "_require_renderable_packet",
        lambda _packet: None,
    )
    monkeypatch.setattr(
        packet_rendering,
        "_prepare_packet_render_from_context",
        lambda _context, packet: packet_rendering._PreparedPacketRender(
            result=_issue110_result(
                tmp_path,
                work,
                cast(SimpleNamespace, packet).packet_instance_id,
            ),
            updates=(object(),),  # type: ignore[arg-type]
        ),
    )
    monkeypatch.setattr(
        packet_rendering,
        "commit_record_batch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            ConcordStorageConflictError("synthetic concurrent change")
        ),
    )

    with pytest.raises(
        packet_rendering.PacketGenerationLifecyclePartialSuccessError
    ) as captured:
        packet_rendering.render_packet_generation(
            packet_rendering.RenderPacketGenerationRequest(
                class_id="class-1",
                activity_id="activity-1",
                generation_id="generation-1",
                actor=WorkflowActor(actor_id="teacher-1"),
            ),
            workspace_root=tmp_path,
        )

    error = captured.value
    assert error.generation_id == "generation-1"
    assert [item.packet_instance_id for item in error.completed] == [
        "packet-1",
        "packet-2",
    ]
    assert all(item.output_installed for item in error.completed)
    assert isinstance(error.__cause__, ConcordStorageConflictError)


def test_generation_rejects_nonrenderable_member_before_output_preparation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    packet_ready = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-a",
        generation_status="rendering",
    )
    packet_pending = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-b",
        generation_status="routes_pending",
    )
    context = SimpleNamespace(
        root=tmp_path,
        work=work,
        library=None,
        snapshot_revision=9,
        snapshot_sha256="b" * 64,
        graph=SimpleNamespace(packet_instances=(packet_ready, packet_pending)),
    )
    prepared: list[str] = []

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
    monkeypatch.setattr(
        packet_rendering,
        "_load_packet_render_context",
        lambda _root, _work: context,
    )
    monkeypatch.setattr(
        packet_rendering,
        "_target_key",
        lambda packet: (0, packet.packet_instance_id),
    )
    monkeypatch.setattr(
        packet_rendering,
        "_prepare_packet_render_from_context",
        lambda _context, packet: prepared.append(
            cast(SimpleNamespace, packet).packet_instance_id
        ),
    )

    with pytest.raises(
        packet_rendering.ConcordWorkflowValidationError,
        match="routes are not ready",
    ):
        packet_rendering.render_packet_generation(
            packet_rendering.RenderPacketGenerationRequest(
                class_id="class-1",
                activity_id="activity-1",
                generation_id="generation-1",
                actor=WorkflowActor(actor_id="teacher-1"),
            ),
            workspace_root=tmp_path,
        )

    assert prepared == []
