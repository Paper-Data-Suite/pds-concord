from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.module_dispatch import ModuleRouteHandlingError
from pds_core.module_profiles import ModuleRegistry
from pds_core.pds2 import parse_pds2_payload
from pds_core.route_registrations import load_route_registration
from pds_core.routes import route_registration_path
from pds_core.scan_failure_metadata import (
    ROUTING_FAILURE_SCHEMA_VERSION,
    RoutingFailureMetadata,
    routing_failure_metadata_path,
    write_routing_failure_metadata,
)
from pds_core.scan_retention import RetainedSourceScan, retain_source_scan
from pds_core.scan_routes import routing_review_dir
from pds_core.workspace import ensure_workspace_root

from concord.models import PrivacyPolicy
from concord.pds_module import get_module_profile
from concord.routing.review import resolve_routing_failure_with_route
from concord.storage import commit_record_batch, load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    WorkflowActor,
    create_activity_context,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _clock() -> datetime:
    return datetime(2026, 10, 4, 22, 30, tzinfo=timezone.utc)


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=_clock(),
        ),
    )
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Routing Review Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _prepared_route(root: Path):
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="student_work",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-1",
                ),
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    return parse_pds2_payload(payload)


def _retained(root: Path, tmp_path: Path) -> RetainedSourceScan:
    source = tmp_path / "teacher-return.png"
    source.write_bytes(b"routing-review-returned-page")
    return retain_source_scan(
        root,
        source,
        intake_timestamp=_clock(),
    )


def _failure(
    root: Path,
    retained: RetainedSourceScan,
    *,
    failure_id: str,
    source_scan_id: str | None = None,
) -> RoutingFailureMetadata:
    failure = RoutingFailureMetadata(
        schema_version=ROUTING_FAILURE_SCHEMA_VERSION,
        failure_id=failure_id,
        scope="page",
        stage="route_resolution",
        created_at=_clock().isoformat(),
        failure_category="payload_missing",
        failure_message="No usable route was detected.",
        source_filename=retained.source_filename,
        source_scan_id=(
            retained.source_scan_id if source_scan_id is None else source_scan_id
        ),
        source_sha256=retained.source_sha256,
        retained_source_path=retained.retained_source_relative_path,
        review_copy_path=None,
        source_page_number=1,
        detected_payload=None,
        route_locator=None,
        target=None,
        module_details={},
    )
    write_routing_failure_metadata(root, failure)
    return failure


def _registry() -> ModuleRegistry:
    return ModuleRegistry((get_module_profile(),))


def _route_inventory(root: Path, locator) -> tuple[tuple[str, bytes], ...]:
    directory = route_registration_path(root, locator).parent
    return tuple(
        (path.name, path.read_bytes())
        for path in sorted(directory.glob("*.json"))
        if path.is_file()
    )


def _resolution_files(root: Path) -> tuple[Path, ...]:
    directory = routing_review_dir(root) / "resolutions"
    if not directory.exists():
        return ()
    return tuple(sorted(path for path in directory.glob("*.json") if path.is_file()))


def test_successful_resolution_uses_existing_route_without_mutating_registration(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    locator = _prepared_route(root)
    retained = _retained(root, tmp_path)
    failure = _failure(
        root,
        retained,
        failure_id="failure-success-1",
    )

    registration_before = load_route_registration(root, locator)
    routes_before = _route_inventory(root, locator)
    failure_bytes_before = routing_failure_metadata_path(
        root,
        failure.failure_id,
    ).read_bytes()
    graph_before = load_current_record_graph(root, locator.work)

    resolution = resolve_routing_failure_with_route(
        failure.failure_id,
        locator,
        message="Teacher selected the exact existing destination.",
        workspace_root=root,
        registry=_registry(),
        reviewer=WorkflowActor(actor_id="teacher-1"),
    )

    graph_after = load_current_record_graph(root, locator.work)
    registration_after = load_route_registration(root, locator)

    assert registration_after == registration_before
    assert _route_inventory(root, locator) == routes_before
    assert routing_failure_metadata_path(
        root,
        failure.failure_id,
    ).read_bytes() == failure_bytes_before
    assert resolution.route_locator == locator
    assert resolution.target == registration_before.target
    assert resolution.resolution_status == "resolved"
    assert resolution.resolution_action == "route_selected"
    assert len(_resolution_files(root)) == 1
    assert graph_after.snapshot_revision == graph_before.snapshot_revision + 1
    assert len(graph_after.graph.scan_references) == 1
    scan = graph_after.graph.scan_references[0]
    assert scan.route_id == locator.route_id
    assert scan.source_scan_id == retained.source_scan_id
    assert scan.source_page_number == 1
    page = next(
        item
        for item in graph_after.graph.artifact_pages
        if item.artifact_page_id == "page-1"
    )
    assert page.page_status == "returned"


def test_exact_replay_does_not_duplicate_scan_reference_or_rewrite_route(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    locator = _prepared_route(root)
    retained = _retained(root, tmp_path)
    first = _failure(root, retained, failure_id="failure-replay-1")
    second = _failure(root, retained, failure_id="failure-replay-2")
    routes_before = _route_inventory(root, locator)

    resolve_routing_failure_with_route(
        first.failure_id,
        locator,
        message="First filing.",
        workspace_root=root,
        registry=_registry(),
    )
    after_first = load_current_record_graph(root, locator.work)

    second_resolution = resolve_routing_failure_with_route(
        second.failure_id,
        locator,
        message="Same retained occurrence reviewed again.",
        workspace_root=root,
        registry=_registry(),
    )
    after_second = load_current_record_graph(root, locator.work)

    assert second_resolution.resolution_status == "resolved"
    assert second_resolution.route_locator == locator
    assert after_second.snapshot_revision == after_first.snapshot_revision
    assert after_second.snapshot_sha256 == after_first.snapshot_sha256
    assert len(after_second.graph.scan_references) == 1
    assert _route_inventory(root, locator) == routes_before
    assert len(_resolution_files(root)) == 2


def test_destination_invalidated_after_selection_fails_closed_at_dispatch(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    locator = _prepared_route(root)
    retained = _retained(root, tmp_path)
    failure = _failure(
        root,
        retained,
        failure_id="failure-stale-destination-1",
    )
    routes_before = _route_inventory(root, locator)
    loaded = load_current_record_graph(root, locator.work)
    page = next(
        item
        for item in loaded.graph.artifact_pages
        if item.artifact_page_id == "page-1"
    )
    artifact = next(
        item
        for item in loaded.graph.artifact_instances
        if item.artifact_instance_id == "artifact-1"
    )
    commit_record_batch(
        root,
        locator.work,
        (
            replace(page, page_status="cancelled"),
            replace(artifact, artifact_status="cancelled"),
        ),
        expected_snapshot_revision=loaded.snapshot_revision,
    )
    invalidated = load_current_record_graph(root, locator.work)

    with pytest.raises(ModuleRouteHandlingError) as captured:
        resolve_routing_failure_with_route(
            failure.failure_id,
            locator,
            message="Destination was selected before cancellation.",
            workspace_root=root,
            registry=_registry(),
        )

    assert isinstance(captured.value.__cause__, ConcordWorkflowValidationError)
    assert "lifecycle" in str(captured.value.__cause__).casefold()
    after = load_current_record_graph(root, locator.work)
    assert after.snapshot_revision == invalidated.snapshot_revision
    assert after.snapshot_sha256 == invalidated.snapshot_sha256
    assert len(after.graph.scan_references) == 0
    assert _route_inventory(root, locator) == routes_before
    assert _resolution_files(root) == ()


def test_tampered_retained_bytes_fail_closed_without_resolution_or_route_change(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    locator = _prepared_route(root)
    retained = _retained(root, tmp_path)
    failure = _failure(
        root,
        retained,
        failure_id="failure-tampered-source-1",
    )
    routes_before = _route_inventory(root, locator)
    graph_before = load_current_record_graph(root, locator.work)
    retained.retained_source_path.write_bytes(b"tampered-after-retention")

    with pytest.raises(ModuleRouteHandlingError) as captured:
        resolve_routing_failure_with_route(
            failure.failure_id,
            locator,
            message="This must not file tampered evidence.",
            workspace_root=root,
            registry=_registry(),
        )

    assert isinstance(captured.value.__cause__, ConcordWorkflowValidationError)
    assert "digest mismatch" in str(captured.value.__cause__)
    graph_after = load_current_record_graph(root, locator.work)
    assert graph_after.snapshot_revision == graph_before.snapshot_revision
    assert graph_after.snapshot_sha256 == graph_before.snapshot_sha256
    assert len(graph_after.graph.scan_references) == 0
    assert _route_inventory(root, locator) == routes_before
    assert _resolution_files(root) == ()


def test_retained_scan_identity_mismatch_is_rejected_before_dispatch(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    locator = _prepared_route(root)
    retained = _retained(root, tmp_path)
    failure = _failure(
        root,
        retained,
        failure_id="failure-scan-identity-1",
        source_scan_id="scan_wrong_identity",
    )
    routes_before = _route_inventory(root, locator)
    graph_before = load_current_record_graph(root, locator.work)

    with pytest.raises(ValueError, match="scan identity"):
        resolve_routing_failure_with_route(
            failure.failure_id,
            locator,
            message="Invalid retained identity must not dispatch.",
            workspace_root=root,
            registry=_registry(),
        )

    graph_after = load_current_record_graph(root, locator.work)
    assert graph_after.snapshot_revision == graph_before.snapshot_revision
    assert graph_after.snapshot_sha256 == graph_before.snapshot_sha256
    assert len(graph_after.graph.scan_references) == 0
    assert _route_inventory(root, locator) == routes_before
    assert _resolution_files(root) == ()
