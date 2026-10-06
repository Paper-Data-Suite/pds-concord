from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.routing_models import ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.storage_models import ConcordStorageCommitResult
from concord.workflows import packet_rendering
from concord.workflows.models import WorkflowActor


def _result(
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


@pytest.mark.parametrize("target_count", (1, 10, 30))
def test_generation_graph_materialization_and_commit_count_are_constant(
    target_count: int,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    packets = tuple(
        SimpleNamespace(
            generation_id="generation-1",
            packet_instance_id=f"packet-{index:02d}",
            generation_status="rendering",
        )
        for index in range(target_count)
    )
    graph = cast(
        ConcordRecordGraph,
        SimpleNamespace(
            packet_instances=packets,
            artifact_instances=(),
            artifact_pages=(),
        ),
    )
    graph_loads: list[tuple[Path, ModuleWorkRef]] = []
    pointer_loads: list[tuple[Path, ModuleWorkRef]] = []
    commits: list[tuple[int, int | None]] = []
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
    monkeypatch.setattr(packet_rendering, "_standards", lambda _root: None)

    def load_graph(
        root: Path,
        selected_work: ModuleWorkRef,
        *,
        standards_library: object,
    ) -> object:
        assert standards_library is None
        graph_loads.append((root, selected_work))
        return SimpleNamespace(
            graph=graph,
            snapshot_revision=9,
            snapshot_sha256="b" * 64,
        )

    monkeypatch.setattr(
        packet_rendering,
        "load_current_record_graph",
        load_graph,
    )

    def load_pointer(
        root: Path,
        selected_work: ModuleWorkRef,
    ) -> object:
        pointer_loads.append((root, selected_work))
        return SimpleNamespace(
            snapshot_revision=9,
            snapshot_sha256="b" * 64,
        )

    monkeypatch.setattr(
        packet_rendering,
        "load_current_snapshot_pointer",
        load_pointer,
    )
    monkeypatch.setattr(
        packet_rendering,
        "_target_key",
        lambda packet: (0, packet.packet_instance_id),
    )

    def prepare(
        _context: object,
        _dependencies: object,
        packet: object,
    ) -> object:
        packet_id = cast(SimpleNamespace, packet).packet_instance_id
        prepared.append(packet_id)
        return packet_rendering._PreparedPacketRender(
            result=_result(tmp_path, work, packet_id),
            updates=(object(),),  # type: ignore[arg-type]
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
        materialized = tuple(cast(tuple[object, ...], records))
        commits.append((len(materialized), expected_snapshot_revision))
        return ConcordStorageCommitResult(
            work=work,
            snapshot_revision=10,
            snapshot_sha256="d" * 64,
            created_record_revisions=(),
            no_op=False,
        )

    monkeypatch.setattr(packet_rendering, "commit_record_batch", commit)
    monkeypatch.setattr(
        packet_rendering,
        "render_packet_instance",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError(
                "generation qualification must not use the public instance loop"
            )
        ),
    )

    result = packet_rendering.render_packet_generation(
        packet_rendering.RenderPacketGenerationRequest(
            class_id="class-1",
            activity_id="activity-1",
            generation_id="generation-1",
            actor=WorkflowActor(actor_id="teacher-1"),
            expected_snapshot_revision=9,
        ),
        workspace_root=tmp_path,
    )

    assert graph_loads == [(tmp_path, work)]
    assert pointer_loads == [(tmp_path, work)]
    assert commits == [(target_count, 9)]
    assert prepared == [f"packet-{index:02d}" for index in range(target_count)]
    assert len(result.packets) == target_count


@pytest.mark.parametrize(
    ("target_count", "distinct_versions"),
    (
        (1, 1),
        (10, 1),
        (30, 1),
        (30, 3),
    ),
)
def test_template_layout_resolution_scales_with_distinct_versions(
    target_count: int,
    distinct_versions: int,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    loads: list[tuple[str, str]] = []
    versions = {
        f"version-{index}": (
            cast(packet_rendering.TemplateVersion, SimpleNamespace()),
            cast(packet_rendering.StarterLayoutDocument, SimpleNamespace()),
        )
        for index in range(distinct_versions)
    }
    context = cast(
        packet_rendering._PacketRenderContext,
        SimpleNamespace(root=tmp_path),
    )
    dependencies = packet_rendering._PacketRenderDependencies(
        template_layout_cache={}
    )

    def load_exact(
        _root: Path,
        template_id: str,
        template_version_id: str,
    ) -> tuple[
        packet_rendering.TemplateVersion,
        packet_rendering.StarterLayoutDocument,
    ]:
        loads.append((template_id, template_version_id))
        return versions[template_version_id]

    monkeypatch.setattr(packet_rendering, "_load_exact_layout", load_exact)

    for target_index in range(target_count):
        version_id = f"version-{target_index % distinct_versions}"
        packet_rendering._load_exact_layout_from_context(
            context,
            dependencies,
            "template-1",
            version_id,
        )

    assert len(loads) == distinct_versions
    assert loads == [
        ("template-1", f"version-{index}")
        for index in range(distinct_versions)
    ]


def test_generation_accumulator_retains_metadata_not_page_images() -> None:
    assert [field.name for field in fields(packet_rendering._PreparedPacketRender)] == [
        "result",
        "updates",
    ]
    assert "images" not in {
        field.name
        for field in fields(packet_rendering.RenderPacketInstanceResult)
    }
