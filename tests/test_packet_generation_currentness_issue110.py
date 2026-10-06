from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.routing_models import ModuleWorkRef

from concord.cli_app.handlers import packet_runtime
from concord.storage_errors import ConcordStorageConflictError
from concord.workflows import packet_rendering
from concord.workflows.models import WorkflowActor


def _context(tmp_path: Path, *, revision: int = 9) -> object:
    packet = SimpleNamespace(
        generation_id="generation-1",
        packet_instance_id="packet-1",
        generation_status="rendering",
    )
    return SimpleNamespace(
        root=tmp_path,
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        library=None,
        snapshot_revision=revision,
        snapshot_sha256="b" * 64,
        graph=SimpleNamespace(packet_instances=(packet,)),
    )


def _install_generation_service_fakes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    context: object,
) -> list[str]:
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
    return prepared


def test_generation_request_expected_snapshot_is_optional() -> None:
    request = packet_rendering.RenderPacketGenerationRequest(
        class_id="class-1",
        activity_id="activity-1",
        generation_id="generation-1",
        actor=WorkflowActor(actor_id="teacher-1"),
    )
    assert request.expected_snapshot_revision is None


def test_generation_rejects_stale_reviewed_snapshot_before_output_work(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = _context(tmp_path, revision=10)
    prepared = _install_generation_service_fakes(
        monkeypatch,
        tmp_path,
        context,
    )
    pointer_checks: list[object] = []
    monkeypatch.setattr(
        packet_rendering,
        "load_current_snapshot_pointer",
        lambda *_args: pointer_checks.append(object()),
    )

    with pytest.raises(
        ConcordStorageConflictError,
        match="expected snapshot 9, found 10",
    ):
        packet_rendering.render_packet_generation(
            packet_rendering.RenderPacketGenerationRequest(
                class_id="class-1",
                activity_id="activity-1",
                generation_id="generation-1",
                actor=WorkflowActor(actor_id="teacher-1"),
                expected_snapshot_revision=9,
            ),
            workspace_root=tmp_path,
        )

    assert prepared == []
    assert pointer_checks == []


def test_generation_last_safe_point_rejects_changed_current_pointer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = _context(tmp_path, revision=9)
    prepared = _install_generation_service_fakes(
        monkeypatch,
        tmp_path,
        context,
    )
    monkeypatch.setattr(
        packet_rendering,
        "load_current_snapshot_pointer",
        lambda *_args: SimpleNamespace(
            snapshot_revision=10,
            snapshot_sha256="c" * 64,
        ),
    )

    with pytest.raises(
        ConcordStorageConflictError,
        match="reviewed snapshot 9 is no longer current",
    ):
        packet_rendering.render_packet_generation(
            packet_rendering.RenderPacketGenerationRequest(
                class_id="class-1",
                activity_id="activity-1",
                generation_id="generation-1",
                actor=WorkflowActor(actor_id="teacher-1"),
                expected_snapshot_revision=9,
            ),
            workspace_root=tmp_path,
        )

    assert prepared == []


def test_generation_last_safe_point_accepts_same_revision_and_sha(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = _context(tmp_path, revision=9)
    prepared = _install_generation_service_fakes(
        monkeypatch,
        tmp_path,
        context,
    )
    monkeypatch.setattr(
        packet_rendering,
        "load_current_snapshot_pointer",
        lambda *_args: SimpleNamespace(
            snapshot_revision=9,
            snapshot_sha256="b" * 64,
        ),
    )

    # Stop after the currentness gate without needing a synthetic render result.
    def stop_after_gate(_context: object, packet: object) -> object:
        prepared.append(cast(SimpleNamespace, packet).packet_instance_id)
        raise RuntimeError("after-currentness-gate")

    monkeypatch.setattr(
        packet_rendering,
        "_prepare_packet_render_from_context",
        stop_after_gate,
    )

    with pytest.raises(
        packet_rendering.PacketGenerationRenderPartialSuccessError
    ) as captured:
        packet_rendering.render_packet_generation(
            packet_rendering.RenderPacketGenerationRequest(
                class_id="class-1",
                activity_id="activity-1",
                generation_id="generation-1",
                actor=WorkflowActor(actor_id="teacher-1"),
                expected_snapshot_revision=9,
            ),
            workspace_root=tmp_path,
        )

    assert prepared == ["packet-1"]
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_direct_cli_reviews_generation_and_passes_exact_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    reviewed: list[tuple[str, str, str, object]] = []
    requests: list[packet_rendering.RenderPacketGenerationRequest] = []

    def show_generation(
        class_id: str,
        activity_id: str,
        generation_id: str,
        *,
        workspace_root: object,
    ) -> object:
        reviewed.append(
            (class_id, activity_id, generation_id, workspace_root)
        )
        return SimpleNamespace(snapshot_revision=27)

    monkeypatch.setattr(
        packet_runtime,
        "show_packet_generation",
        show_generation,
    )

    def render_generation(
        request: packet_rendering.RenderPacketGenerationRequest,
        *,
        workspace_root: object,
    ) -> object:
        assert workspace_root == str(tmp_path)
        requests.append(request)
        return SimpleNamespace(
            generation_id=request.generation_id,
            packets=(),
            page_count=0,
            route_count=0,
        )

    monkeypatch.setattr(
        packet_runtime,
        "render_packet_generation",
        render_generation,
    )

    args = Namespace(
        class_id="class-1",
        activity_id="activity-1",
        generation_id="generation-1",
        actor_id="teacher-1",
        actor_label=None,
        actor_role=None,
        workspace_root=str(tmp_path),
    )
    assert packet_runtime.handle_generation_render(args) == 0

    assert reviewed == [
        (
            "class-1",
            "activity-1",
            "generation-1",
            str(tmp_path),
        )
    ]
    assert len(requests) == 1
    assert requests[0].expected_snapshot_revision == 27
