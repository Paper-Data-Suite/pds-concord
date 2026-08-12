from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.pds2 import parse_pds2_payload
from pds_core.route_registrations import resolve_route_registration
from pds_core.routing_models import ModuleWorkRef
from pds_core.scan_retention import RetainedSourceScan
from pds_core.workspace import ensure_workspace_root
from PIL import Image

from concord.models import PrivacyPolicy
from concord.storage import (
    commit_record_batch,
    list_record_revisions,
    load_current_record_graph,
)
from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
)
from concord.workflows.artifact_assembly import (
    ArtifactAssemblyAmbiguityError,
    ArtifactAssemblyError,
    ArtifactAssemblyIncompleteError,
    ArtifactAssemblyIntegrityError,
    AssembleArtifactRequest,
    AssemblyPageSelection,
    assemble_returned_artifact,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    handle_concord_route,
    prepare_artifact_pages,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _clock() -> datetime:
    return datetime(2026, 8, 11, 17, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-1")


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root, create_class_metadata("class-1", "2026-2027", created_at=_clock())
    )
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Artifact assembly activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _prepare(
    root: Path,
    *,
    artifact_id: str = "artifact-1",
    pages: tuple[ArtifactPagePlan, ...] = (
        ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
    ),
) -> Any:
    return prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id=artifact_id,
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=1,
            actor=_actor(),
            pages=pages,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )


def _retained_image(
    root: Path,
    *,
    scan_id: str,
    filename: str,
    color: tuple[int, int, int],
) -> RetainedSourceScan:
    path = root / "scans" / "source" / "2026-08-11" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 120), color).save(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return RetainedSourceScan(
        source_scan_id=scan_id,
        source_filename=filename,
        source_sha256=digest,
        retained_source_path=path,
        retained_source_relative_path=path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 8, 11),
    )


def _file(
    root: Path,
    prepared: Any,
    page_index: int,
    retained: RetainedSourceScan,
) -> Any:
    payload = prepared.pages[page_index].pds2_payload
    assert payload is not None
    locator = parse_pds2_payload(payload)
    resolution = resolve_route_registration(root, locator)
    return handle_concord_route(resolution, retained, 1)


def test_return_rollup_partial_then_complete_and_replay_is_noop(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(
        root,
        pages=(
            ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
            ArtifactPagePlan(page_number=2, artifact_page_id="page-2"),
        ),
    )
    first = _retained_image(
        root, scan_id="scan-1", filename="first.png", color=(255, 0, 0)
    )
    _file(root, prepared, 0, first)
    graph = load_current_record_graph(root, _work()).graph
    artifact = graph.artifact_instances[0]
    assert artifact.artifact_status == "partially_returned"
    revisions_after_first = list_record_revisions(
        root, _work(), "artifact_instance", artifact.artifact_instance_id
    )

    replay = _file(root, prepared, 0, first)
    assert replay.replayed
    assert list_record_revisions(
        root, _work(), "artifact_instance", artifact.artifact_instance_id
    ) == revisions_after_first

    second = _retained_image(
        root, scan_id="scan-2", filename="second.png", color=(0, 255, 0)
    )
    _file(root, prepared, 1, second)
    graph = load_current_record_graph(root, _work()).graph
    assert graph.artifact_instances[0].artifact_status == "returned"


def test_non_return_expected_page_does_not_block_returned_status(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(
        root,
        pages=(
            ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
            ArtifactPagePlan(
                page_number=2,
                artifact_page_id="page-2",
                return_expected=False,
            ),
        ),
    )
    retained = _retained_image(
        root, scan_id="scan-1", filename="returned.png", color=(20, 30, 40)
    )
    _file(root, prepared, 0, retained)
    graph = load_current_record_graph(root, _work()).graph
    assert graph.artifact_instances[0].artifact_status == "returned"
    page_two = next(
        item for item in graph.artifact_pages if item.artifact_page_id == "page-2"
    )
    assert page_two.page_status == "planned"


def test_terminal_artifact_is_not_reopened_by_new_return(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    loaded = load_current_record_graph(root, _work())
    artifact = loaded.graph.artifact_instances[0]
    commit_record_batch(
        root,
        _work(),
        (replace(artifact, artifact_status="archived"),),
        expected_snapshot_revision=loaded.snapshot_revision,
    )
    retained = _retained_image(
        root, scan_id="scan-1", filename="late.png", color=(20, 30, 40)
    )
    with pytest.raises(ConcordWorkflowValidationError, match="lifecycle"):
        _file(root, prepared, 0, retained)


def test_assembly_uses_canonical_artifact_order_not_scan_order(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(
        root,
        pages=(
            ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
            ArtifactPagePlan(page_number=2, artifact_page_id="page-2"),
        ),
    )
    second = _retained_image(
        root, scan_id="scan-2", filename="second.png", color=(0, 255, 0)
    )
    first = _retained_image(
        root, scan_id="scan-1", filename="first.png", color=(255, 0, 0)
    )
    _file(root, prepared, 1, second)
    _file(root, prepared, 0, first)
    loaded = load_current_record_graph(root, _work())
    result = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert result.output_path.read_bytes().startswith(b"%PDF")
    manifest_text = result.manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    assert [
        item["artifact_page_id"] for item in manifest["ordered_pages"]
    ] == ["page-1", "page-2"]
    assert manifest["page_count"] == 2
    assert "artifact_authors" not in manifest
    assert "artifact_subjects" not in manifest
    assert "/Users/" not in manifest_text
    assert "C:\\" not in manifest_text

    replay = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert replay.reused
    assert replay.assembly_id == result.assembly_id
    assert replay.output_sha256 == result.output_sha256


def test_missing_required_page_blocks_completed_assembly(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(
        root,
        pages=(
            ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
            ArtifactPagePlan(page_number=2, artifact_page_id="page-2"),
        ),
    )
    first = _retained_image(
        root, scan_id="scan-1", filename="first.png", color=(255, 0, 0)
    )
    _file(root, prepared, 0, first)
    loaded = load_current_record_graph(root, _work())
    with pytest.raises(ArtifactAssemblyIncompleteError) as caught:
        assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=loaded.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        )
    assert caught.value.missing_pages == ((2, "page-2"),)


def test_multiple_scan_occurrences_require_exact_selection(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    first = _retained_image(
        root, scan_id="scan-1", filename="first.png", color=(255, 0, 0)
    )
    second = _retained_image(
        root, scan_id="scan-2", filename="second.png", color=(0, 255, 0)
    )
    first_result = _file(root, prepared, 0, first)
    second_result = _file(root, prepared, 0, second)
    loaded = load_current_record_graph(root, _work())
    request = AssembleArtifactRequest(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        expected_snapshot_revision=loaded.snapshot_revision,
        actor=_actor(),
    )
    with pytest.raises(ArtifactAssemblyAmbiguityError) as caught:
        assemble_returned_artifact(
            request,
            workspace_root=root,
            clock=_clock,
        )
    assert set(caught.value.ambiguities[0].scan_reference_ids) == {
        first_result.scan_reference_id,
        second_result.scan_reference_id,
    }

    selected = assemble_returned_artifact(
        replace(
            request,
            selections=(
                AssemblyPageSelection(
                    artifact_page_id="page-1",
                    scan_reference_id=second_result.scan_reference_id,
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    manifest = json.loads(selected.manifest_path.read_text(encoding="utf-8"))
    assert (
        manifest["ordered_pages"][0]["scan_reference_id"]
        == second_result.scan_reference_id
    )



def test_pdf_retained_source_assembles_exact_physical_page(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    path = root / "scans" / "source" / "2026-08-11" / "source.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 120), (40, 50, 60)).save(path, "PDF")
    retained = RetainedSourceScan(
        source_scan_id="scan-pdf",
        source_filename="source.pdf",
        source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        retained_source_path=path,
        retained_source_relative_path=path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 8, 11),
    )
    _file(root, prepared, 0, retained)
    loaded = load_current_record_graph(root, _work())
    result = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert result.output_path.read_bytes().startswith(b"%PDF")
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["ordered_pages"][0]["source_page_number"] == 1

def test_retained_source_tampering_is_rejected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root, scan_id="scan-1", filename="source.png", color=(20, 30, 40)
    )
    _file(root, prepared, 0, retained)
    retained.retained_source_path.write_bytes(b"tampered")
    loaded = load_current_record_graph(root, _work())
    with pytest.raises(ArtifactAssemblyIntegrityError, match="digest"):
        assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=loaded.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        )
def test_single_returned_image_assembly_preserves_route_and_creates_no_semantics(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root,
        scan_id="scan-single",
        filename="single.png",
        color=(10, 20, 30),
    )
    _file(root, prepared, 0, retained)
    before = load_current_record_graph(root, _work())
    route_id = before.graph.artifact_pages[0].route_id
    result = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=before.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert result.page_count == 1
    after = load_current_record_graph(root, _work())
    assert after.graph.artifact_pages[0].route_id == route_id
    assert after.graph.artifact_reviews == ()
    assert after.graph.moderation_records == ()
    assert after.graph.score_records == ()
    assert after.snapshot_revision == before.snapshot_revision


def test_mixed_pdf_image_assembly_omits_nonreturn_page(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(
        root,
        pages=(
            ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
            ArtifactPagePlan(page_number=2, artifact_page_id="page-2"),
            ArtifactPagePlan(
                page_number=3,
                artifact_page_id="page-3",
                return_expected=False,
            ),
        ),
    )
    image = _retained_image(
        root,
        scan_id="scan-image",
        filename="mixed-image.png",
        color=(200, 10, 10),
    )
    pdf_path = root / "scans" / "source" / "2026-08-11" / "mixed.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (80, 120), (10, 200, 10)).save(pdf_path, "PDF")
    pdf = RetainedSourceScan(
        source_scan_id="scan-pdf",
        source_filename="mixed.pdf",
        source_sha256=hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        retained_source_path=pdf_path,
        retained_source_relative_path=pdf_path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 8, 11),
    )
    _file(root, prepared, 1, pdf)
    _file(root, prepared, 0, image)
    loaded = load_current_record_graph(root, _work())
    result = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert [item["artifact_page_id"] for item in manifest["ordered_pages"]] == [
        "page-1",
        "page-2",
    ]
    assert manifest["page_count"] == 2


def test_wrong_scan_reference_target_is_rejected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(
        root,
        pages=(
            ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
            ArtifactPagePlan(page_number=2, artifact_page_id="page-2"),
        ),
    )
    first = _retained_image(
        root, scan_id="scan-1", filename="target-1.png", color=(1, 2, 3)
    )
    second = _retained_image(
        root, scan_id="scan-2", filename="target-2.png", color=(4, 5, 6)
    )
    _file(root, prepared, 0, first)
    second_result = _file(root, prepared, 1, second)
    loaded = load_current_record_graph(root, _work())
    with pytest.raises(ArtifactAssemblyError, match="does not belong"):
        assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=loaded.snapshot_revision,
                actor=_actor(),
                selections=(
                    AssemblyPageSelection(
                        artifact_page_id="page-1",
                        scan_reference_id=second_result.scan_reference_id,
                    ),
                ),
            ),
            workspace_root=root,
            clock=_clock,
        )


def test_image_scan_reference_physical_page_must_be_one(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root,
        scan_id="scan-page",
        filename="physical.png",
        color=(10, 20, 30),
    )
    _file(root, prepared, 0, retained)
    loaded = load_current_record_graph(root, _work())
    scan = loaded.graph.scan_references[0]
    committed = commit_record_batch(
        root,
        _work(),
        (replace(scan, source_page_number=2),),
        expected_snapshot_revision=loaded.snapshot_revision,
    )
    with pytest.raises(ArtifactAssemblyIntegrityError, match="physical page 1"):
        assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=committed.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        )


def test_retained_source_path_substitution_is_rejected(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root,
        scan_id="scan-original",
        filename="original.png",
        color=(10, 20, 30),
    )
    _file(root, prepared, 0, retained)
    alternate = _retained_image(
        root,
        scan_id="scan-unused",
        filename="alternate.png",
        color=(200, 210, 220),
    )
    loaded = load_current_record_graph(root, _work())
    scan = loaded.graph.scan_references[0]
    committed = commit_record_batch(
        root,
        _work(),
        (
            replace(
                scan,
                retained_source_relative_path=(
                    alternate.retained_source_relative_path
                ),
            ),
        ),
        expected_snapshot_revision=loaded.snapshot_revision,
    )
    with pytest.raises(ArtifactAssemblyIntegrityError, match="digest"):
        assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=committed.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        )


def test_retained_source_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root,
        scan_id="scan-link",
        filename="linked.png",
        color=(10, 20, 30),
    )
    _file(root, prepared, 0, retained)
    original = retained.retained_source_path
    backup = original.with_name("linked-backup.png")
    original.rename(backup)
    try:
        original.symlink_to(backup)
    except OSError as error:
        backup.rename(original)
        pytest.skip(f"filesystem cannot create a source symlink: {error}")
    loaded = load_current_record_graph(root, _work())
    with pytest.raises(ArtifactAssemblyIntegrityError, match="link-like"):
        assemble_returned_artifact(
            AssembleArtifactRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=loaded.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=_clock,
        )


def test_changed_explicit_source_selection_gets_new_assembly_identity(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    first = _retained_image(
        root, scan_id="scan-first", filename="select-1.png", color=(1, 2, 3)
    )
    second = _retained_image(
        root, scan_id="scan-second", filename="select-2.png", color=(4, 5, 6)
    )
    first_result = _file(root, prepared, 0, first)
    second_result = _file(root, prepared, 0, second)
    loaded = load_current_record_graph(root, _work())
    base = AssembleArtifactRequest(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        expected_snapshot_revision=loaded.snapshot_revision,
        actor=_actor(),
    )
    first_assembly = assemble_returned_artifact(
        replace(
            base,
            selections=(
                AssemblyPageSelection(
                    artifact_page_id="page-1",
                    scan_reference_id=first_result.scan_reference_id,
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    second_assembly = assemble_returned_artifact(
        replace(
            base,
            selections=(
                AssemblyPageSelection(
                    artifact_page_id="page-1",
                    scan_reference_id=second_result.scan_reference_id,
                ),
            ),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert first_assembly.assembly_id != second_assembly.assembly_id
    assert first_assembly.output_path != second_assembly.output_path


def test_conflicting_existing_assembly_bytes_are_not_overwritten(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    retained = _retained_image(
        root,
        scan_id="scan-conflict",
        filename="conflict.png",
        color=(10, 20, 30),
    )
    _file(root, prepared, 0, retained)
    loaded = load_current_record_graph(root, _work())
    request = AssembleArtifactRequest(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        expected_snapshot_revision=loaded.snapshot_revision,
        actor=_actor(),
    )
    result = assemble_returned_artifact(
        request,
        workspace_root=root,
        clock=_clock,
    )
    result.output_path.write_bytes(b"conflicting existing bytes")
    with pytest.raises(ArtifactAssemblyIntegrityError, match="digest"):
        assemble_returned_artifact(
            request,
            workspace_root=root,
            clock=_clock,
        )
    assert result.output_path.read_bytes() == b"conflicting existing bytes"
