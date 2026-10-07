from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from concord.workflows import packet_generation
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
)


def _packet(
    packet_id: str,
    *,
    generation_id: str = "generation-1",
    packet_version_id: str = "packet-version-1",
    status: str = "generated",
    artifact_id: str | None = None,
    created_at: str = "2026-10-05T18:00:00+00:00",
) -> SimpleNamespace:
    artifact = artifact_id or f"artifact-{packet_id}"
    return SimpleNamespace(
        packet_instance_id=packet_id,
        generation_id=generation_id,
        packet_definition_id="packet-1",
        packet_version_id=packet_version_id,
        activity_id="activity-1",
        session_id="session-1",
        generation_date="2026-10-05",
        generation_status=status,
        artifact_bindings=(
            SimpleNamespace(
                artifact_instance_id=artifact,
                template_version_id="template-version-1",
            ),
        ),
        created_provenance=SimpleNamespace(timestamp=created_at),
    )


def _artifact(
    packet: SimpleNamespace,
    *,
    page_ids: tuple[str, ...],
) -> SimpleNamespace:
    binding = packet.artifact_bindings[0]
    return SimpleNamespace(
        artifact_instance_id=binding.artifact_instance_id,
        packet_instance_id=packet.packet_instance_id,
        activity_id="activity-1",
        session_id="session-1",
        template_version_id=binding.template_version_id,
        page_ids=page_ids,
    )


def _page(
    page_id: str,
    artifact_id: str,
    *,
    route_required: bool,
) -> SimpleNamespace:
    return SimpleNamespace(
        artifact_page_id=page_id,
        artifact_instance_id=artifact_id,
        route_required=route_required,
    )


def _graph() -> SimpleNamespace:
    packet_a = _packet("packet-a", status="generated")
    packet_b = _packet(
        "packet-b",
        status="rendering",
        created_at="2026-10-05T18:00:01+00:00",
    )
    artifact_a = _artifact(packet_a, page_ids=("page-a1", "page-a2"))
    artifact_b = _artifact(packet_b, page_ids=("page-b1",))
    return SimpleNamespace(
        packet_instances=(packet_b, packet_a),
        artifact_instances=(artifact_a, artifact_b),
        artifact_pages=(
            _page("page-a1", artifact_a.artifact_instance_id, route_required=True),
            _page("page-a2", artifact_a.artifact_instance_id, route_required=False),
            _page("page-b1", artifact_b.artifact_instance_id, route_required=True),
        ),
        sessions=(
            SimpleNamespace(
                session_id="session-1",
                activity_id="activity-1",
                sequence=1,
                label="Seminar Session 1",
            ),
        ),
    )


def _packet_library() -> SimpleNamespace:
    return SimpleNamespace(
        definition=SimpleNamespace(
            packet_definition_id="packet-1",
            name="Seminar Reflection",
        ),
        versions=(
            SimpleNamespace(
                packet_version_id="packet-version-1",
                packet_definition_id="packet-1",
                version_label="v1",
            ),
        ),
    )


def _install_read_fakes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    graph: SimpleNamespace,
) -> list[str]:
    packet_loads: list[str] = []
    monkeypatch.setattr(
        packet_generation,
        "resolve_read_workspace_root",
        lambda _root: tmp_path,
    )
    monkeypatch.setattr(
        packet_generation,
        "_standards",
        lambda _root: None,
    )
    monkeypatch.setattr(
        packet_generation,
        "load_current_record_graph",
        lambda *_args, **_kwargs: SimpleNamespace(
            graph=graph,
            snapshot_revision=31,
            snapshot_sha256="a" * 64,
        ),
    )

    def load_packet(_root: Path, packet_definition_id: str) -> object:
        packet_loads.append(packet_definition_id)
        return _packet_library()

    monkeypatch.setattr(
        packet_generation,
        "load_current_packet",
        load_packet,
    )
    return packet_loads


def test_generation_projection_carries_teacher_metadata_counts_and_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    packet_loads = _install_read_fakes(
        monkeypatch,
        tmp_path,
        _graph(),
    )

    summaries = packet_generation.list_packet_generations(
        "class-1",
        "activity-1",
        workspace_root=tmp_path,
    )

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.packet_name == "Seminar Reflection"
    assert summary.packet_version_label == "v1"
    assert summary.session_label == "Seminar Session 1"
    assert summary.generation_date == "2026-10-05"
    assert summary.instance_count == 2
    assert summary.artifact_count == 2
    assert summary.page_count == 3
    assert summary.route_count == 2
    assert summary.generated_count == 1
    assert summary.rendering_count == 1
    assert summary.planned_count == 0
    assert summary.routes_pending_count == 0
    assert summary.failed_count == 0
    assert summary.cancelled_count == 0
    assert summary.snapshot_revision == 31
    assert summary.snapshot_sha256 == "a" * 64
    assert packet_loads == ["packet-1"]


def test_generation_projection_reuses_packet_library_across_generations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    graph = _graph()
    first = graph.packet_instances[0]
    second_generation = _packet(
        "packet-c",
        generation_id="generation-2",
        status="generated",
        artifact_id="artifact-packet-c",
        created_at="2026-10-05T19:00:00+00:00",
    )
    second_artifact = _artifact(
        second_generation,
        page_ids=("page-c1",),
    )
    graph = SimpleNamespace(
        packet_instances=graph.packet_instances + (second_generation,),
        artifact_instances=graph.artifact_instances + (second_artifact,),
        artifact_pages=graph.artifact_pages
        + (
            _page(
                "page-c1",
                second_artifact.artifact_instance_id,
                route_required=True,
            ),
        ),
        sessions=graph.sessions,
    )
    packet_loads = _install_read_fakes(
        monkeypatch,
        tmp_path,
        graph,
    )

    summaries = packet_generation.list_packet_generations(
        "class-1",
        "activity-1",
        workspace_root=tmp_path,
    )

    assert [item.generation_id for item in summaries] == [
        "generation-1",
        "generation-2",
    ]
    assert packet_loads == ["packet-1"]
    assert first.packet_definition_id == summaries[0].packet_definition_id


def test_generation_projection_fails_closed_on_mixed_packet_version(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    graph = _graph()
    packet_a, packet_b = graph.packet_instances
    contradictory = _packet(
        packet_b.packet_instance_id,
        packet_version_id="packet-version-2",
        status=packet_b.generation_status,
        artifact_id=packet_b.artifact_bindings[0].artifact_instance_id,
        created_at=packet_b.created_provenance.timestamp,
    )
    graph = SimpleNamespace(
        packet_instances=(packet_a, contradictory),
        artifact_instances=graph.artifact_instances,
        artifact_pages=graph.artifact_pages,
        sessions=graph.sessions,
    )
    _install_read_fakes(monkeypatch, tmp_path, graph)

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="contradictory Packet version",
    ):
        packet_generation.list_packet_generations(
            "class-1",
            "activity-1",
            workspace_root=tmp_path,
        )


def test_generation_projection_fails_closed_on_missing_page(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    graph = _graph()
    graph = SimpleNamespace(
        packet_instances=graph.packet_instances,
        artifact_instances=graph.artifact_instances,
        artifact_pages=graph.artifact_pages[:-1],
        sessions=graph.sessions,
    )
    _install_read_fakes(monkeypatch, tmp_path, graph)

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="Artifact Page provenance",
    ):
        packet_generation.list_packet_generations(
            "class-1",
            "activity-1",
            workspace_root=tmp_path,
        )


def test_show_generation_rejects_unknown_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _install_read_fakes(monkeypatch, tmp_path, _graph())

    with pytest.raises(
        ConcordWorkflowNotFoundError,
        match="generation-missing",
    ):
        packet_generation.show_packet_generation(
            "class-1",
            "activity-1",
            "generation-missing",
            workspace_root=tmp_path,
        )
