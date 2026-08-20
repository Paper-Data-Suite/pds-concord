from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.module_profiles import (
    CORE_ROUTING_CONTRACT_VERSION,
    build_module_registry,
)
from pds_core.pds2 import parse_pds2_payload
from pds_core.rosters import create_roster
from pds_core.route_registrations import (
    load_route_registration,
    resolve_route_registration,
)
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator
from pds_core.scan_retention import RetainedSourceScan
from pds_core.workspace import ensure_workspace_root

from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import (
    ActorReference,
    ConcordModelError,
    PlannedGroup,
    PrivacyPolicy,
    Provenance,
    ScanReference,
)
from concord.pds_module import get_module_profile
from concord.routing.rendering import RenderArtifactPagesRequest, render_artifact_pages
from concord.routing.scan_intake import route_scan_sources
from concord.storage import load_current_record_graph
from concord.workflows import (
    CreateActivityContextRequest,
    CreateGroupPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_group_plan,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    handle_concord_route,
    prepare_artifact_pages,
)


def _clock() -> datetime:
    return datetime(2026, 8, 10, 16, 0, tzinfo=timezone.utc)


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root, create_class_metadata("class-1", "2026-2027", created_at=_clock())
    )
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _scan_reference(**overrides: object) -> ScanReference:
    values: dict[str, object] = {
        "scan_reference_id": "scanref-1",
        "activity_id": "activity-1",
        "artifact_page_id": "page-1",
        "route_id": "route-1",
        "source_scan_id": "scan-1",
        "source_page_number": 1,
        "retained_source_relative_path": "scans/source/2026-08-10/source.png",
        "retained_source_sha256": "a" * 64,
        "created_provenance": Provenance(
            actor=ActorReference(
                actor_kind="system", actor_id="core", owning_system="core"
            ),
            timestamp=_clock().isoformat(),
            source_kind="routed",
        ),
    }
    values.update(overrides)
    return ScanReference(**values)  # type: ignore[arg-type]


def test_scan_reference_exact_conversion_and_path_validation() -> None:
    record = _scan_reference()
    assert record_from_dict("scan_reference", record_to_dict(record)) == record
    with pytest.raises(ConcordModelError):
        _scan_reference(retained_source_relative_path="C:/private/source.png")
    with pytest.raises(ConcordModelError):
        _scan_reference(source_page_number=0)
    with pytest.raises(ConcordModelError):
        _scan_reference(retained_source_sha256="BAD")


def test_module_profile_is_repeatable_and_exact() -> None:
    first = get_module_profile()
    second = get_module_profile()
    assert first == second
    assert first.module_id == "concord"
    assert first.supported_core_routing_contract_versions == frozenset(
        {CORE_ROUTING_CONTRACT_VERSION}
    )
    assert first.supported_qr_schemas == frozenset({PDS2_SCHEMA})
    assert first.dispatchable_route_statuses == frozenset({"active"})


def test_prepare_and_dispatch_are_page_based_and_replay_safe(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(
                ArtifactPagePlan(page_number=1, artifact_page_id="page-1"),
                ArtifactPagePlan(page_number=2, artifact_page_id="page-2"),
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert prepared.routes_verified == prepared.routes_expected == 2
    assert prepared.pages[0].route_id != prepared.pages[1].route_id
    assert all(
        page.pds2_payload and "student" not in page.pds2_payload
        for page in prepared.pages
    )
    locator = parse_pds2_payload(prepared.pages[0].pds2_payload or "")
    assert locator.work == ModuleWorkRef("concord", "class-1", "activity-1")
    registration = load_route_registration(root, locator)
    assert registration.target.record_id == "page-1"
    assert registration.target.record_kind == "artifact_page"

    retained_path = root / "scans" / "source" / "2026-08-10" / "returned.png"
    retained_path.parent.mkdir(parents=True)
    retained_path.write_bytes(b"synthetic returned physical page")
    digest = hashlib.sha256(retained_path.read_bytes()).hexdigest()
    retained = RetainedSourceScan(
        source_scan_id="scan-returned-1",
        source_filename="returned.png",
        source_sha256=digest,
        retained_source_path=retained_path,
        retained_source_relative_path=retained_path.relative_to(root).as_posix(),
        intake_timestamp=_clock(),
        intake_date=date(2026, 8, 10),
    )
    resolution = resolve_route_registration(root, locator)
    filed = handle_concord_route(resolution, retained, 1)
    replay = handle_concord_route(resolution, retained, 1)
    assert not filed.replayed
    assert replay.replayed
    assert replay.scan_reference_id == filed.scan_reference_id
    graph = load_current_record_graph(root, locator.work).graph
    assert len(graph.scan_references) == 1
    assert graph.scan_references[0].artifact_page_id == "page-1"
    assert graph.artifact_pages[0].page_status == "returned"
    assert graph.artifact_authors == ()
    assert graph.artifact_subjects == ()


def test_route_validator_rejects_cross_module_locator() -> None:
    profile = get_module_profile()
    assert profile.registration_validator is not None
    # Core's model prevents internally inconsistent module identities before the
    # Concord validator runs; this proves the installed provider uses Core models.
    with pytest.raises(ValueError):
        RouteLocator(PDS2_SCHEMA, ModuleWorkRef("Concord", "class-1", "work-1"), "r-1")


def test_rendered_pdf_round_trips_through_retention_decode_and_dispatch(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-roundtrip",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(
                ArtifactPagePlan(page_number=1, artifact_page_id="roundtrip-page-1"),
                ArtifactPagePlan(page_number=2, artifact_page_id="roundtrip-page-2"),
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    rendered = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-roundtrip",
            expected_snapshot_revision=prepared.commit.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
    )
    assert rendered.output_path.is_file()
    assert rendered.output_path.read_bytes().startswith(b"%PDF")
    registry = build_module_registry(
        explicit_profiles=(get_module_profile(),), discover_installed=False
    )
    batch = route_scan_sources(
        (rendered.output_path,), workspace_root=root, registry=registry
    )
    assert batch.dispatched_count == 2
    assert batch.failure_count == 0
    graph = load_current_record_graph(
        root, ModuleWorkRef("concord", "class-1", "activity-1")
    ).graph
    assert len(graph.scan_references) == 2
    assert {item.source_page_number for item in graph.scan_references} == {1, 2}


def test_group_plan_is_excluded_from_artifact_and_pds2_metadata(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
            ),
        ),
    )
    plan = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="private-plan-marker",
            strategy="similar_signal",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            proposed_groups=(
                PlannedGroup(
                    planned_group_key="private-planned-group-marker",
                    label="Private Planning Group",
                    student_ids=("student-1",),
                ),
            ),
            target_group_count=1,
            source_signal_set_id="private-signal-set",
            source_signal_set_digest="f" * 64,
            source_signal_dimension_id="private-dimension",
        ),
        workspace_root=root,
        clock=_clock,
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-private-check",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=plan.commit.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-private-check",
                ),
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )

    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    locator = parse_pds2_payload(payload)
    registration = load_route_registration(root, locator)
    graph = load_current_record_graph(root, locator.work).graph
    artifact = next(
        item
        for item in graph.artifact_instances
        if item.artifact_instance_id == "artifact-private-check"
    )
    page = next(
        item
        for item in graph.artifact_pages
        if item.artifact_page_id == "page-private-check"
    )

    observable = "\n".join(
        (
            payload,
            repr(registration.module_details),
            repr(record_to_dict(artifact)),
            repr(record_to_dict(page)),
        )
    )
    for private_marker in (
        "private-plan-marker",
        "private-planned-group-marker",
        "private-signal-set",
        "private-dimension",
    ):
        assert private_marker not in observable
    assert set(registration.module_details) == {
        "activity_id",
        "artifact_instance_id",
        "artifact_page_id",
        "page_number",
    }
