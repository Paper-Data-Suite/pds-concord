from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.module_profiles import (
    CORE_ROUTING_CONTRACT_VERSION,
    ModuleProfile,
    build_module_registry,
)
from pds_core.pds2 import parse_pds2_payload, serialize_pds2_payload
from pds_core.route_registrations import (
    RouteRegistrationNotFoundError,
    load_route_registration,
    resolve_route_registration,
    route_registration_path,
    write_route_registration,
)
from pds_core.routing_models import (
    PDS2_SCHEMA,
    ROUTE_REGISTRATION_SCHEMA_VERSION,
    ModuleRecordRef,
    ModuleWorkRef,
    RouteLocator,
    RouteRegistration,
    module_record_ref_to_dict,
    route_locator_to_dict,
)
from pds_core.scan_failure_metadata import (
    RoutingFailureMetadataReadError,
    load_routing_failure_metadata,
    routing_failure_metadata_from_dict,
    routing_failure_metadata_to_dict,
    write_routing_failure_metadata,
)
from pds_core.scan_resolution_metadata import SCAN_RESOLUTION_SCHEMA_VERSION
from pds_core.workspace import ensure_workspace_root

from concord import menu_artifact, menu_scan
from concord.cli_app.main import (
    EXIT_CONFLICT,
    EXIT_ERROR,
    EXIT_PARTIAL_SUCCESS,
    main,
)
from concord.menu_artifact import _list as list_pages_menu
from concord.menu_context import MenuSessionContext
from concord.menu_navigation import QuitPDS, ReturnToMainMenu
from concord.menu_scan import _review as review_menu
from concord.model_validation import collect_record_graph_issues
from concord.models import (
    ActorReference,
    ArtifactPage,
    ArtifactSubject,
    PrivacyPolicy,
    Provenance,
    ScanReference,
    SubjectReference,
)
from concord.pds_module import get_module_profile
from concord.routing import rendering, review
from concord.routing.rendering import (
    RenderArtifactPagesRequest,
    RenderPartialSuccessError,
    render_artifact_pages,
)
from concord.routing.review import (
    RoutingFailureSummary,
    RoutingResolutionPartialSuccessError,
    list_routing_failures,
    resolve_routing_failure_with_route,
)
from concord.routing.scan_intake import route_scan_sources
from concord.storage import commit_record_batch, load_current_record_graph
from concord.storage_errors import ConcordStorageConflictError
from concord.workflows import (
    ActivitySummary,
    CreateActivityContextRequest,
    CreateGroupRequest,
    WorkflowActor,
    create_activity_context,
    create_group,
    show_activity,
)
from concord.workflows import artifact_page as artifact_page_workflow
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    ArtifactRoutePreparationPartialSuccessError,
    PrepareArtifactPagesRequest,
    handle_concord_route,
    prepare_artifact_pages,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _clock() -> datetime:
    return datetime(2026, 8, 11, 12, 34, 56, 123456, tzinfo=timezone.utc)


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root, create_class_metadata("class-1", "2026-2027", created_at=_clock())
    )
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Hardening Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    return root


def _prepare(
    root: Path,
    *,
    artifact_id: str = "artifact-1",
    page_count: int = 1,
    route_last: bool = True,
    expected_snapshot_revision: int = 1,
    group_id: str | None = None,
    artifact_category: str = "observation",
):
    return prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id=artifact_id,
            template_version_id="template-1",
            artifact_category=artifact_category,
            expected_snapshot_revision=expected_snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=tuple(
                ArtifactPagePlan(
                    page_number=index,
                    artifact_page_id=f"{artifact_id}-page-{index}",
                    route_required=route_last or index < page_count,
                )
                for index in range(1, page_count + 1)
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            group_id=group_id,
        ),
        workspace_root=root,
        clock=_clock,
    )


@pytest.mark.parametrize(
    "unsafe",
    (
        "state/output.pdf",
        "routes/output.pdf",
        "other/output.pdf",
        "rendered/../state/output.pdf",
        "/rendered/output.pdf",
        r"C:\rendered\output.pdf",
        r"\\server\share\output.pdf",
    ),
)
def test_render_rejects_every_output_outside_rendered(
    tmp_path: Path, unsafe: str
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    with pytest.raises(ValueError, match="beneath rendered"):
        render_artifact_pages(
            RenderArtifactPagesRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=prepared.commit.snapshot_revision,
                actor=WorkflowActor(actor_id="teacher-1"),
                output_relative_path=unsafe,
            ),
            workspace_root=root,
        )


def test_render_only_transitions_pages_physically_in_route_pdf(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root, page_count=2, route_last=False)
    rendered = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            expected_snapshot_revision=prepared.commit.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
    )
    assert rendered.page_count == 1
    graph = load_current_record_graph(root, rendered.work).graph
    assert [page.page_status for page in graph.artifact_pages] == [
        "generated",
        "planned",
    ]
    assert graph.artifact_instances[0].generation_status == "planned"
    assert graph.artifact_instances[0].artifact_status == "planned"


def test_existing_identical_render_is_reused_without_overwrite(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    request = RenderArtifactPagesRequest(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        expected_snapshot_revision=prepared.commit.snapshot_revision,
        actor=WorkflowActor(actor_id="teacher-1"),
    )
    first = render_artifact_pages(request, workspace_root=root)
    second = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            artifact_instance_id=request.artifact_instance_id,
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=request.actor,
        ),
        workspace_root=root,
    )
    assert first.output_installed
    assert not second.output_installed
    assert second.output_path == first.output_path


def test_scan_intake_bootstraps_but_review_read_does_not(tmp_path: Path) -> None:
    absent_read = tmp_path / "read-only-workspace"
    assert list_routing_failures(workspace_root=absent_read) == ()
    assert not absent_read.exists()

    absent_write = tmp_path / "scan-workspace"
    source = tmp_path / "scan.png"
    source.write_bytes(b"synthetic")
    result = route_scan_sources(
        (source,), workspace_root=absent_write, decoder=lambda _: ((),)
    )
    assert absent_write.is_dir()
    assert result.failure_count == 1


def test_invalid_page_plan_precedes_workspace_publication(tmp_path: Path) -> None:
    absent = tmp_path / "absent"
    with pytest.raises(
        ConcordWorkflowValidationError, match="ordered and contiguous"
    ):
        prepare_artifact_pages(
            PrepareArtifactPagesRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-invalid",
                template_version_id="template-1",
                artifact_category="observation",
                expected_snapshot_revision=1,
                actor=WorkflowActor(actor_id="teacher-1"),
                pages=(ArtifactPagePlan(page_number=2),),
                privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            ),
            workspace_root=absent,
        )
    assert not absent.exists()


def test_preparation_stale_snapshot_conflicts_without_new_pages(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    with pytest.raises(ConcordStorageConflictError):
        prepare_artifact_pages(
            PrepareArtifactPagesRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-stale",
                template_version_id="template-1",
                artifact_category="observation",
                expected_snapshot_revision=0,
                actor=WorkflowActor(actor_id="teacher-1"),
                pages=(ArtifactPagePlan(page_number=1),),
                privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            ),
            workspace_root=root,
        )
    graph = load_current_record_graph(
        root, ModuleWorkRef("concord", "class-1", "activity-1")
    ).graph
    assert not graph.artifact_instances


def test_partial_route_preparation_retry_reuses_canonical_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _workspace(tmp_path)
    original = artifact_page_workflow._reconcile_route
    calls = []

    def fail_second(path: Path, registration: RouteRegistration) -> None:
        calls.append(registration.locator.route_id)
        if len(calls) == 2:
            raise OSError("injected route-store failure")
        original(path, registration)

    monkeypatch.setattr(artifact_page_workflow, "_reconcile_route", fail_second)
    with pytest.raises(ArtifactRoutePreparationPartialSuccessError) as raised:
        _prepare(root, artifact_id="artifact-partial", page_count=2)
    partial = raised.value.result
    assert partial.routes_verified == 1
    canonical_ids = tuple(
        (page.artifact_page_id, page.route_id) for page in partial.pages
    )

    monkeypatch.setattr(artifact_page_workflow, "_reconcile_route", original)
    retry = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-partial",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=partial.commit.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(
                ArtifactPagePlan(page_number=1),
                ArtifactPagePlan(page_number=2),
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
    )
    assert retry.commit.no_op
    assert retry.routes_verified == 2
    assert tuple((page.artifact_page_id, page.route_id) for page in retry.pages) == (
        canonical_ids
    )


def _scan_reference_for(page: ArtifactPage, **changes: object) -> ScanReference:
    values = {
        "scan_reference_id": "scanref-1",
        "activity_id": "activity-1",
        "artifact_page_id": page.artifact_page_id,
        "route_id": page.route_id,
        "source_scan_id": "scan-1",
        "source_page_number": 1,
        "retained_source_relative_path": (
            "scans/source/2026-08-11/"
            "20260811T123456123456Z__scan__aaaaaaaaaaaa.png"
        ),
        "retained_source_sha256": "a" * 64,
        "created_provenance": Provenance(
            actor=ActorReference(
                actor_kind="system", actor_id="core", owning_system="core"
            ),
            timestamp=_clock().isoformat(),
            source_kind="routed",
        ),
    }
    values.update(changes)
    return ScanReference(**values)


@pytest.mark.parametrize(
    ("changes", "expected_code"),
    (
        ({"artifact_page_id": "missing-page"}, "scan_reference.page.missing"),
        ({"activity_id": "other-activity"}, "scan_reference.activity.mismatch"),
        ({"route_id": "other-route"}, "scan_reference.route.mismatch"),
    ),
)
def test_scan_reference_target_graph_invariants(
    tmp_path: Path, changes: dict[str, object], expected_code: str
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    graph = load_current_record_graph(root, prepared.commit.work).graph
    scan = _scan_reference_for(graph.artifact_pages[0], **changes)
    issues = collect_record_graph_issues(replace(graph, scan_references=(scan,)))
    assert expected_code in {item.code for item in issues}


def test_scan_reference_occurrence_rules_allow_rescans_not_duplicates(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root, page_count=2)
    graph = load_current_record_graph(root, prepared.commit.work).graph
    first, second = graph.artifact_pages
    scan = _scan_reference_for(first)
    duplicate = replace(scan, scan_reference_id="scanref-duplicate")
    duplicate_issues = collect_record_graph_issues(
        replace(graph, scan_references=(scan, duplicate))
    )
    assert "scan_reference.occurrence.duplicate" in {
        item.code for item in duplicate_issues
    }

    contradictory = replace(
        scan,
        scan_reference_id="scanref-contradiction",
        artifact_page_id=second.artifact_page_id,
        route_id=second.route_id or "",
    )
    contradiction_issues = collect_record_graph_issues(
        replace(graph, scan_references=(scan, contradictory))
    )
    assert "scan_reference.physical_target.contradiction" in {
        item.code for item in contradiction_issues
    }

    rescan = replace(
        scan,
        scan_reference_id="scanref-rescan",
        source_scan_id="scan-2",
        retained_source_relative_path=(
            "scans/source/2026-08-11/"
            "20260811T123457123456Z__scan__bbbbbbbbbbbb.png"
        ),
        retained_source_sha256="b" * 64,
    )
    assert not collect_record_graph_issues(
        replace(graph, scan_references=(scan, rescan))
    )


def test_mixed_module_page_dispatch_is_opaque_and_needs_no_sibling_import(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root, create_class_metadata("class-1", "2026-2027", created_at=_clock())
    )
    work = ModuleWorkRef("synthetic", "class-1", "work-1")
    locator = RouteLocator(PDS2_SCHEMA, work, "route-1")
    registration = RouteRegistration(
        schema_version=ROUTE_REGISTRATION_SCHEMA_VERSION,
        locator=locator,
        target=ModuleRecordRef("synthetic", "page", "page-1", "1"),
        created_at=_clock().isoformat(),
        status="active",
        human_fallback="Synthetic page",
    )
    write_route_registration(root, registration)
    received = []
    profile = ModuleProfile(
        module_id="synthetic",
        display_name="Synthetic",
        supported_core_routing_contract_versions=frozenset(
            {CORE_ROUTING_CONTRACT_VERSION}
        ),
        supported_qr_schemas=frozenset({PDS2_SCHEMA}),
        supported_route_registration_schema_versions=frozenset(
            {ROUTE_REGISTRATION_SCHEMA_VERSION}
        ),
        dispatchable_route_statuses=frozenset({"active"}),
        route_handler=lambda resolution, retained, page: received.append(
            (resolution.locator, retained.source_scan_id, page)
        )
        or {"owned_by": "synthetic"},
    )
    registry = build_module_registry(
        explicit_profiles=(get_module_profile(), profile), discover_installed=False
    )
    source = tmp_path / "mixed.png"
    source.write_bytes(b"synthetic scan")
    result = route_scan_sources(
        (source,),
        workspace_root=root,
        registry=registry,
        decoder=lambda _: ((serialize_pds2_payload(locator),),),
    )
    assert result.dispatched_count == 1
    assert result.sources[0].pages[0].module_result == {"owned_by": "synthetic"}
    assert received[0][0] == locator


@pytest.mark.parametrize("suffix", (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"))
def test_scan_intake_accepts_each_core_supported_source_type(
    tmp_path: Path, suffix: str
) -> None:
    source = tmp_path / f"source{suffix}"
    source.write_bytes(b"synthetic")
    result = route_scan_sources(
        (source,), workspace_root=tmp_path / "workspace", decoder=lambda _: ((),)
    )
    assert result.sources[0].retained_source is not None
    assert result.sources[0].pages[0].source_page_number == 1
    assert result.sources[0].pages[0].status == "review"


def test_scan_intake_classifies_payload_edges_and_continues_pages(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    source = tmp_path / "multipage.pdf"
    source.write_bytes(b"synthetic")
    registry = build_module_registry(
        explicit_profiles=(get_module_profile(),), discover_installed=False
    )
    result = route_scan_sources(
        (source,),
        workspace_root=root,
        registry=registry,
        decoder=lambda _: (
            (),
            ("PDS2|malformed",),
            (payload, payload),
            (payload, payload.replace("r=", "r=other-")),
        ),
    )
    pages = result.sources[0].pages
    assert [page.source_page_number for page in pages] == [1, 2, 3, 4]
    assert [page.status for page in pages] == [
        "review",
        "review",
        "dispatched",
        "review",
    ]
    assert result.dispatched_count == 1
    assert result.failure_count == 3


def test_scan_folder_is_sorted_nonrecursive_and_rejects_linked_source(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "z.png").write_bytes(b"z")
    (folder / "a.png").write_bytes(b"a")
    nested = folder / "nested"
    nested.mkdir()
    (nested / "ignored.png").write_bytes(b"ignored")
    result = route_scan_sources(
        (folder,), workspace_root=tmp_path / "workspace", decoder=lambda _: ((),)
    )
    assert [item.source_path.name for item in result.sources] == ["a.png", "z.png"]

    target = tmp_path / "target.png"
    target.write_bytes(b"target")
    link = tmp_path / "link.png"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("filesystem cannot create a file symlink")
    linked = route_scan_sources(
        (link,), workspace_root=tmp_path / "linked-workspace", decoder=lambda _: ((),)
    )
    assert linked.sources[0].retained_source is None
    assert "non-symlink" in (linked.sources[0].source_error or "")


def test_direct_cli_maps_review_durability_partial_success_to_four(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, failure_id, locator, _ = _failure_and_route(tmp_path)
    monkeypatch.setattr(
        review,
        "dispatch_route",
        lambda *_args: SimpleNamespace(module_result={"filed": True}),
    )
    monkeypatch.setattr(review, "build_module_registry", lambda: object())
    monkeypatch.setattr(
        review,
        "write_scan_resolution_metadata",
        lambda *_args: (_ for _ in ()).throw(OSError("injected write failure")),
    )
    exit_code = main(
        (
            "scan",
            "review",
            "resolve",
            "--workspace-root",
            str(root),
            "--actor-id",
            "teacher-1",
            "--failure-id",
            failure_id,
            "--message",
            "Exact teacher-selected route.",
            "--module-id",
            locator.module_id,
            "--class-id",
            locator.class_id,
            "--work-id",
            locator.work_id,
            "--route-id",
            locator.route_id,
        )
    )
    assert exit_code == EXIT_PARTIAL_SUCCESS
    error = capsys.readouterr().err
    assert "Handler dispatch succeeded: yes" in error
    assert "Evidence filing occurred: yes" in error
    assert "Routing-resolution metadata persisted: no" in error


def _copy_failure_with_locator(
    root: Path,
    failure_id: str,
    locator: RouteLocator,
    *,
    new_failure_id: str,
    target: ModuleRecordRef | None = None,
) -> str:
    original = load_routing_failure_metadata(root, failure_id)
    selected_target = (
        load_route_registration(root, locator).target if target is None else target
    )
    data = routing_failure_metadata_to_dict(original)
    data["failure_id"] = new_failure_id
    data["route_locator"] = route_locator_to_dict(locator)
    data["target"] = module_record_ref_to_dict(selected_target)
    data["detected_payload"] = serialize_pds2_payload(locator)
    copied = routing_failure_metadata_from_dict(data)
    write_routing_failure_metadata(root, copied)
    return new_failure_id


def test_teacher_review_rejects_non_concord_route_even_when_active(
    tmp_path: Path,
) -> None:
    root, failure_id, _, _ = _failure_and_route(tmp_path)
    locator = RouteLocator(
        PDS2_SCHEMA, ModuleWorkRef("synthetic", "class-1", "work-1"), "route-1"
    )
    write_route_registration(
        root,
        RouteRegistration(
            schema_version=ROUTE_REGISTRATION_SCHEMA_VERSION,
            locator=locator,
            target=ModuleRecordRef("synthetic", "page", "page-1", "1"),
            created_at=_clock().isoformat(),
            status="active",
            human_fallback="Synthetic page",
        ),
    )
    with pytest.raises(ValueError, match="requires a Concord route"):
        resolve_routing_failure_with_route(
            failure_id,
            locator,
            message="Not a Concord correction.",
            workspace_root=root,
        )


@pytest.mark.parametrize("kind", ("inactive", "incompatible", "missing"))
def test_teacher_review_requires_exact_dispatchable_concord_artifact_page_route(
    tmp_path: Path, kind: str
) -> None:
    root, failure_id, canonical, _ = _failure_and_route(tmp_path)
    locator = RouteLocator(
        PDS2_SCHEMA,
        canonical.work,
        f"route-{kind}",
    )
    if kind != "missing":
        expected = load_route_registration(root, canonical)
        write_route_registration(
            root,
            replace(
                expected,
                locator=locator,
                status="inactive" if kind == "inactive" else "active",
                target=(
                    expected.target
                    if kind == "inactive"
                    else ModuleRecordRef("concord", "other", "page-other", "1")
                ),
            ),
        )
    expected_error = (
        RouteRegistrationNotFoundError
        if kind == "missing"
        else ConcordWorkflowValidationError
    )
    with pytest.raises(expected_error):
        resolve_routing_failure_with_route(
            failure_id,
            locator,
            message="Exact teacher-selected route.",
            workspace_root=root,
        )


def test_teacher_review_same_work_correction_and_cross_work_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, failure_id, locator, _ = _failure_and_route(tmp_path)
    linked_id = _copy_failure_with_locator(
        root, failure_id, locator, new_failure_id="failure-same-work"
    )
    monkeypatch.setattr(
        review,
        "dispatch_route",
        lambda *_args: SimpleNamespace(module_result={"filed": True}),
    )
    resolved = resolve_routing_failure_with_route(
        linked_id,
        locator,
        message="Same-work correction.",
        workspace_root=root,
    )
    assert resolved.schema_version == SCAN_RESOLUTION_SCHEMA_VERSION
    assert resolved.resolution_action == "route_corrected"

    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-2",
            title="Other Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-2",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    other = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-2",
            artifact_instance_id="artifact-2",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(ArtifactPagePlan(page_number=1),),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    other_locator = parse_pds2_payload(other.pages[0].pds2_payload or "")
    with pytest.raises(ValueError, match="another Activity work"):
        resolve_routing_failure_with_route(
            linked_id,
            other_locator,
            message="Cross-work correction.",
            workspace_root=root,
        )


def test_other_module_failure_cannot_be_reinterpreted_as_concord(
    tmp_path: Path,
) -> None:
    root, failure_id, concord_locator, _ = _failure_and_route(tmp_path)
    synthetic = RouteLocator(
        PDS2_SCHEMA, ModuleWorkRef("synthetic", "class-1", "work-1"), "route-1"
    )
    copied_id = _copy_failure_with_locator(
        root,
        failure_id,
        synthetic,
        new_failure_id="failure-other-module",
        target=ModuleRecordRef("synthetic", "page", "page-1", "1"),
    )
    with pytest.raises(ValueError, match="another module"):
        resolve_routing_failure_with_route(
            copied_id,
            concord_locator,
            message="Do not reinterpret module ownership.",
            workspace_root=root,
        )


def test_exact_existing_route_reconciles_and_contradiction_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root, artifact_id="artifact-exact")
    retry = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-exact",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=prepared.commit.snapshot_revision,
            actor=WorkflowActor(actor_id="teacher-1"),
            pages=(ArtifactPagePlan(page_number=1),),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
    )
    assert retry.commit.no_op
    assert retry.pages == prepared.pages

    original_write = artifact_page_workflow.write_route_registration

    def write_contradiction(path: Path, expected: RouteRegistration) -> None:
        original_write(
            path,
            replace(
                expected,
                target=replace(expected.target, record_id="contradictory-page"),
            ),
        )

    root2 = _workspace(tmp_path / "other")
    monkeypatch.setattr(
        artifact_page_workflow, "write_route_registration", write_contradiction
    )
    with pytest.raises(ArtifactRoutePreparationPartialSuccessError) as raised:
        _prepare(root2, artifact_id="artifact-contradictory")
    assert "contradictory immutable route" in str(raised.value.__cause__)


def test_render_requires_present_exact_registration(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    locator = parse_pds2_payload(prepared.pages[0].pds2_payload or "")
    registration = load_route_registration(root, locator)
    path = route_registration_path(root, locator)
    path.unlink()
    request = RenderArtifactPagesRequest(
        class_id="class-1",
        activity_id="activity-1",
        artifact_instance_id="artifact-1",
        expected_snapshot_revision=prepared.commit.snapshot_revision,
        actor=WorkflowActor(actor_id="teacher-1"),
    )
    with pytest.raises(RouteRegistrationNotFoundError):
        render_artifact_pages(request, workspace_root=root)

    write_route_registration(
        root,
        replace(
            registration,
            target=replace(registration.target, record_id="different-page"),
            module_details={
                **registration.module_details,
                "artifact_page_id": "different-page",
            },
        ),
    )
    with pytest.raises(RuntimeError, match="does not match canonical page"):
        render_artifact_pages(request, workspace_root=root)


def test_render_never_overwrites_different_output(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    target = (
        root
        / "classes"
        / "class-1"
        / "modules"
        / "concord"
        / "work"
        / "activity-1"
        / "rendered"
        / "custom.pdf"
    )
    target.parent.mkdir(parents=True)
    target.write_bytes(b"existing unrelated output")
    with pytest.raises(FileExistsError, match="different completed render"):
        render_artifact_pages(
            RenderArtifactPagesRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=prepared.commit.snapshot_revision,
                actor=WorkflowActor(actor_id="teacher-1"),
                output_relative_path="rendered/custom.pdf",
            ),
            workspace_root=root,
        )
    assert target.read_bytes() == b"existing unrelated output"


def test_render_lifecycle_failure_preserves_completed_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    monkeypatch.setattr(
        rendering,
        "commit_record_batch",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("injected lifecycle failure")
        ),
    )
    with pytest.raises(RenderPartialSuccessError) as raised:
        render_artifact_pages(
            RenderArtifactPagesRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                expected_snapshot_revision=prepared.commit.snapshot_revision,
                actor=WorkflowActor(actor_id="teacher-1"),
            ),
            workspace_root=root,
        )
    assert raised.value.output_path.is_file()
    assert raised.value.output_path.read_bytes().startswith(b"%PDF")


def test_handler_rejects_retained_source_path_substitution(tmp_path: Path) -> None:
    root, _, locator, retained = _failure_and_route(tmp_path)
    substitute = retained.retained_source_path.with_name("substitute.png")
    substitute.write_bytes(retained.retained_source_path.read_bytes())
    resolution = resolve_route_registration(root, locator)
    with pytest.raises(
        ConcordWorkflowValidationError, match="provenance is inconsistent"
    ):
        handle_concord_route(
            resolution,
            replace(retained, retained_source_path=substitute),
            1,
        )


def test_resolution_is_not_appended_when_dispatch_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, failure_id, locator, _ = _failure_and_route(tmp_path)
    monkeypatch.setattr(
        review,
        "dispatch_route",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("handler failed")),
    )
    with pytest.raises(RuntimeError, match="handler failed"):
        resolve_routing_failure_with_route(
            failure_id,
            locator,
            message="Will not resolve.",
            workspace_root=root,
        )
    resolution_dir = root / "scans" / "review" / "resolutions"
    assert not resolution_dir.exists()


def test_deferred_then_resolved_history_and_unscoped_listing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, failure_id, locator, _ = _failure_and_route(tmp_path)
    deferred = review.defer_routing_failure(
        failure_id, message="Wait for teacher review.", workspace_root=root
    )
    assert deferred.schema_version == SCAN_RESOLUTION_SCHEMA_VERSION
    assert deferred.resolution_status == "deferred"
    assert list_routing_failures(workspace_root=root)[0].failure_id == failure_id
    assert list_routing_failures(workspace_root=root)[0].activity_id is None

    monkeypatch.setattr(
        review,
        "dispatch_route",
        lambda *_args: SimpleNamespace(module_result={"filed": True}),
    )
    resolved = resolve_routing_failure_with_route(
        failure_id,
        locator,
        message="Exact route selected.",
        workspace_root=root,
    )
    assert resolved.resolution_status == "resolved"
    assert list_routing_failures(workspace_root=root) == ()
    all_items = list_routing_failures(workspace_root=root, state="all")
    assert all_items[0].latest_status == "resolved"
    files = tuple((root / "scans" / "review" / "resolutions").glob("*.json"))
    assert len(files) == 2


def _route_payload(root: Path, source: Path, payload: str):
    source.write_bytes(b"returned paper evidence")
    return route_scan_sources(
        (source,),
        workspace_root=root,
        registry=build_module_registry(
            explicit_profiles=(get_module_profile(),), discover_installed=False
        ),
        decoder=lambda _: ((payload,),),
    )


def test_non_student_observation_prepares_and_returns_without_roster(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root, artifact_category="observation")
    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    result = _route_payload(root, tmp_path / "observation.png", payload)
    assert result.dispatched_count == 1
    graph = load_current_record_graph(root, prepared.commit.work).graph
    assert len(graph.scan_references) == 1
    assert graph.artifact_authors == ()
    assert graph.artifact_subjects == ()


def test_group_artifact_route_identity_remains_group_agnostic(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    group = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-1",
            label="Observation Team",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
        clock=_clock,
    )
    prepared = _prepare(
        root,
        artifact_id="artifact-group",
        expected_snapshot_revision=group.commit.snapshot_revision,
        group_id="group-1",
        artifact_category="observation",
    )
    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    locator = parse_pds2_payload(payload)
    assert locator == RouteLocator(
        PDS2_SCHEMA,
        ModuleWorkRef("concord", "class-1", "activity-1"),
        prepared.pages[0].route_id or "",
    )
    assert "group" not in payload.casefold()
    assert _route_payload(root, tmp_path / "group.png", payload).dispatched_count == 1
    graph = load_current_record_graph(root, locator.work).graph
    assert graph.artifact_instances[0].group_id == "group-1"
    assert graph.artifact_authors == ()
    assert graph.artifact_subjects == ()


@pytest.mark.parametrize("subject_count", (0, 1, 3))
def test_subject_cardinality_does_not_change_page_routing(
    tmp_path: Path, subject_count: int
) -> None:
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    payload = prepared.pages[0].pds2_payload
    assert payload is not None
    before_locator = parse_pds2_payload(payload)
    subject_targets = (
        ("concord_activity", "activity-1"),
        ("concord_session", "session-1"),
        ("concord_artifact_instance", "artifact-1"),
    )
    subjects = tuple(
        ArtifactSubject(
            artifact_subject_id=f"artifact-subject-{index}",
            artifact_instance_id="artifact-1",
            subject_reference=SubjectReference(
                subject_kind=subject_targets[index][0],
                subject_id=subject_targets[index][1],
                owning_system="concord",
            ),
            subject_role="general_subject",
            confirmation_status="confirmed",
            assignment_source="teacher",
            created_provenance=Provenance(
                actor=ActorReference(
                    actor_kind="authorized_adult",
                    actor_id="teacher-1",
                    owning_system="concord",
                ),
                timestamp=_clock().isoformat(),
                source_kind="manual",
            ),
        )
        for index in range(subject_count)
    )
    if subjects:
        commit_record_batch(
            root,
            prepared.commit.work,
            subjects,
            expected_snapshot_revision=prepared.commit.snapshot_revision,
        )
    assert _route_payload(
        root, tmp_path / f"subjects-{subject_count}.png", payload
    ).dispatched_count == 1
    graph = load_current_record_graph(root, prepared.commit.work).graph
    page = graph.artifact_pages[0]
    assert page.route_id == before_locator.route_id
    assert serialize_pds2_payload(before_locator) == payload
    assert len(graph.artifact_subjects) == subject_count
    assert graph.artifact_authors == ()


@pytest.mark.parametrize("action", ("prepare", "render"))
def test_artifact_menu_stale_write_offers_read_only_reload_without_retry(
    tmp_path: Path,
    action: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    activity = show_activity("class-1", "activity-1", workspace_root=root).summary
    writes = []
    reloads = []
    if action == "prepare":
        monkeypatch.setattr(
            menu_artifact,
            "prepare_artifact_pages",
            lambda *_args, **_kwargs: writes.append(True)
            or (_ for _ in ()).throw(ConcordStorageConflictError("stale")),
        )
        answers = iter(("1", "artifact-menu", "template-1", "", "CREATE", "1"))
    else:
        monkeypatch.setattr(
            menu_artifact,
            "render_artifact_pages",
            lambda *_args, **_kwargs: writes.append(True)
            or (_ for _ in ()).throw(ConcordStorageConflictError("stale")),
        )
        answers = iter(("3", "artifact-menu", "RENDER", "1"))
    monkeypatch.setattr(
        menu_artifact,
        "show_activity",
        lambda *_args: reloads.append(True) or SimpleNamespace(summary=activity),
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        activity, MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    assert writes == [True]
    assert reloads == [True]
    output = capsys.readouterr().out
    assert "Activity Changed" in output
    assert "1. Reload" in output


def test_artifact_menu_shows_preparation_partial_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    activity = show_activity("class-1", "activity-1", workspace_root=root).summary
    result = SimpleNamespace(
        routes_verified=1,
        routes_expected=2,
        commit=SimpleNamespace(snapshot_revision=2, snapshot_sha256="a" * 64),
    )
    error = ArtifactRoutePreparationPartialSuccessError(
        result, OSError("injected")
    )
    monkeypatch.setattr(
        menu_artifact,
        "prepare_artifact_pages",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )
    answers = iter(("1", "artifact-menu", "template-1", "2", "CREATE", ""))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        activity, MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    output = capsys.readouterr().out
    assert "Artifact/Page snapshot was published" in output
    assert "Snapshot: 2" in output
    assert "Snapshot SHA-256: " + "a" * 64 in output
    assert "Routes verified: 1/2" in output
    assert "before retrying" in output


def test_artifact_menu_shows_render_partial_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _workspace(tmp_path)
    activity = show_activity("class-1", "activity-1", workspace_root=root).summary
    error = RenderPartialSuccessError(
        tmp_path / "rendered" / "artifact-menu.pdf", OSError("injected")
    )
    monkeypatch.setattr(
        menu_artifact,
        "render_artifact_pages",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error),
    )
    answers = iter(("3", "artifact-menu", "RENDER", ""))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_artifact.launch_artifact_page_menu(
        activity, MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    output = capsys.readouterr().out
    assert "Rendered output is installed and durable" in output
    assert "Output: artifact-menu.pdf" in output
    assert "Canonical lifecycle update is incomplete" in output
    assert "before retrying" in output


@pytest.mark.parametrize(
    ("action", "stage", "key", "expected"),
    (
        ("prepare", "prompt", "M", ReturnToMainMenu),
        ("prepare", "prompt", "Q", QuitPDS),
        ("prepare", "confirmation", "M", ReturnToMainMenu),
        ("prepare", "confirmation", "Q", QuitPDS),
        ("render", "prompt", "M", ReturnToMainMenu),
        ("render", "prompt", "Q", QuitPDS),
        ("render", "confirmation", "M", ReturnToMainMenu),
        ("render", "confirmation", "Q", QuitPDS),
    ),
)
def test_artifact_nested_navigation_unwinds_without_error_screen(
    action: str,
    stage: str,
    key: str,
    expected: type[BaseException],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = cast(
        ActivitySummary,
        SimpleNamespace(
            title="Navigation Activity",
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=1,
        ),
    )
    if action == "prepare":
        answers = (
            ("1", key)
            if stage == "prompt"
            else ("1", "artifact-1", "template-1", "", key)
        )
    else:
        answers = (
            ("3", key)
            if stage == "prompt"
            else ("3", "artifact-1", key)
        )
    responses = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    with pytest.raises(expected):
        menu_artifact.launch_artifact_page_menu(
            activity, MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
        )
    assert "Artifact Page Error" not in capsys.readouterr().out


@pytest.mark.parametrize(
    ("action", "stage"),
    (
        ("prepare", "prompt"),
        ("prepare", "confirmation"),
        ("render", "prompt"),
        ("render", "confirmation"),
    ),
)
def test_artifact_nested_back_cancels_without_write_or_error(
    action: str,
    stage: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    activity = cast(
        ActivitySummary,
        SimpleNamespace(
            title="Navigation Activity",
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=1,
        ),
    )
    writes: list[str] = []
    monkeypatch.setattr(
        menu_artifact,
        "prepare_artifact_pages",
        lambda *_args, **_kwargs: writes.append("prepare"),
    )
    monkeypatch.setattr(
        menu_artifact,
        "render_artifact_pages",
        lambda *_args, **_kwargs: writes.append("render"),
    )
    if action == "prepare":
        answers = (
            ("1", "B")
            if stage == "prompt"
            else ("1", "artifact-1", "template-1", "", "B")
        )
    else:
        answers = (
            ("3", "B")
            if stage == "prompt"
            else ("3", "artifact-1", "B")
        )
    responses = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))
    menu_artifact.launch_artifact_page_menu(
        activity, MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    assert writes == []
    assert "Artifact Page Error" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "error",
    (
        RoutingFailureMetadataReadError("corrupt failure metadata"),
        RouteRegistrationNotFoundError("missing selected route"),
    ),
)
def test_scan_menu_contains_expected_review_errors(
    error: Exception,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        menu_scan,
        "_review",
        lambda *_args: (_ for _ in ()).throw(error),
    )
    answers = iter(("2", "", "B"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    menu_scan.launch_scan_routing_menu(
        MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    output = capsys.readouterr().out
    assert "Scan Routing Error" in output
    assert str(error) in output


def _render_cli_args(root: Path, artifact_id: str, expected: int) -> tuple[str, ...]:
    return (
        "artifact",
        "render",
        "--workspace-root",
        str(root),
        "--expected-snapshot",
        str(expected),
        "--actor-id",
        "teacher-1",
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--artifact-instance-id",
        artifact_id,
    )


def test_direct_cli_missing_artifact_and_stale_render_are_typed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _workspace(tmp_path)
    assert main(_render_cli_args(root, "missing-artifact", 1)) == EXIT_ERROR
    assert "Artifact Instance is unavailable" in capsys.readouterr().err

    prepared = _prepare(root)
    assert main(_render_cli_args(root, "artifact-1", 1)) == EXIT_CONFLICT
    assert "Conflict:" in capsys.readouterr().err
    assert prepared.commit.snapshot_revision > 1


def test_direct_cli_review_read_and_missing_route_errors_return_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _workspace(tmp_path)
    assert (
        main(
            (
                "scan",
                "review",
                "show",
                "--workspace-root",
                str(root),
                "--failure-id",
                "failure-missing",
            )
        )
        == EXIT_ERROR
    )
    assert "Error:" in capsys.readouterr().err

    _, failure_id, locator, _ = _failure_and_route(tmp_path / "route")
    route_root = tmp_path / "route" / "workspace"
    assert (
        main(
            (
                "scan",
                "review",
                "resolve",
                "--workspace-root",
                str(route_root),
                "--actor-id",
                "teacher-1",
                "--failure-id",
                failure_id,
                "--message",
                "Exact missing route.",
                "--class-id",
                locator.class_id,
                "--work-id",
                locator.work_id,
                "--route-id",
                "route-missing",
            )
        )
        == EXIT_ERROR
    )
    assert "Error:" in capsys.readouterr().err


def test_direct_cli_corrupt_review_metadata_and_usage_are_typed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    review_dir = root / "scans" / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "failure-corrupt.json").write_text("{not-json", encoding="utf-8")
    assert (
        main(
            (
                "scan",
                "review",
                "show",
                "--workspace-root",
                str(root),
                "--failure-id",
                "failure-corrupt",
            )
        )
        == EXIT_ERROR
    )
    assert "Error:" in capsys.readouterr().err

    with pytest.raises(SystemExit) as incomplete:
        main(
            (
                "scan",
                "review",
                "resolve",
                "--workspace-root",
                str(root),
                "--actor-id",
                "teacher-1",
                "--failure-id",
                "failure-corrupt",
                "--message",
                "Incomplete route syntax.",
                "--class-id",
                "class-1",
            )
        )
    assert incomplete.value.code == 2


def _failure_and_route(tmp_path: Path):
    root = _workspace(tmp_path)
    prepared = _prepare(root)
    source = tmp_path / "returned.png"
    source.write_bytes(b"returned evidence")
    intake = route_scan_sources(
        (source,), workspace_root=root, decoder=lambda _: ((),)
    )
    failure_id = intake.sources[0].pages[0].failure_id
    assert failure_id is not None
    locator = parse_pds2_payload(prepared.pages[0].pds2_payload or "")
    retained = intake.sources[0].retained_source
    assert retained is not None
    return root, failure_id, locator, retained


def test_review_redispatch_recovers_core_intake_time_not_file_mtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, failure_id, locator, retained = _failure_and_route(tmp_path)
    os.utime(retained.retained_source_path, (1, 1))
    captured = []

    def dispatch(_root: Path, _registry: object, request: object):
        captured.append(request)
        return SimpleNamespace(module_result={"opaque": True})

    monkeypatch.setattr(review, "dispatch_route", dispatch)
    resolve_routing_failure_with_route(
        failure_id,
        locator,
        message="Exact teacher-selected route.",
        workspace_root=root,
        registry=build_module_registry(
            explicit_profiles=(get_module_profile(),), discover_installed=False
        ),
    )
    reconstructed = captured[0].retained_source
    assert reconstructed.intake_timestamp == retained.intake_timestamp
    assert reconstructed.intake_timestamp != datetime.fromtimestamp(
        1, timezone.utc
    )
    assert reconstructed.intake_date == retained.intake_date
    assert reconstructed.retained_source_relative_path == (
        retained.retained_source_relative_path
    )


def test_review_resolution_write_failure_is_structured_partial_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, failure_id, locator, _ = _failure_and_route(tmp_path)
    dispatches = []
    monkeypatch.setattr(
        review,
        "dispatch_route",
        lambda *_args: dispatches.append(True)
        or SimpleNamespace(module_result={"filed": True}),
    )
    monkeypatch.setattr(
        review,
        "write_scan_resolution_metadata",
        lambda *_args: (_ for _ in ()).throw(OSError("injected write failure")),
    )
    with pytest.raises(RoutingResolutionPartialSuccessError) as raised:
        resolve_routing_failure_with_route(
            failure_id,
            locator,
            message="Exact teacher-selected route.",
            workspace_root=root,
        )
    assert dispatches == [True]
    result = raised.value.result
    assert result.handler_dispatch_succeeded
    assert result.evidence_filing_occurred
    assert not result.resolution_metadata_persisted
    assert result.failure_id == failure_id
    assert result.selected_route == locator
    assert list_routing_failures(workspace_root=root)[0].latest_status is None


def test_artifact_menu_can_select_twelfth_page(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    pages = tuple(
        SimpleNamespace(
            artifact_page_id=f"page-{index}",
            artifact_instance_id="artifact-1",
            page_number=index,
            page_status="planned",
            route_id=f"route-{index}",
        )
        for index in range(1, 13)
    )
    monkeypatch.setattr("concord.menu_artifact.list_artifact_pages", lambda *_: pages)
    answers = iter(("N", "2", ""))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    activity = SimpleNamespace(class_id="class-1", activity_id="activity-1")
    list_pages_menu(activity)
    output = capsys.readouterr().out
    assert "Page 2 of 2" in output
    assert "Page: page-12" in output


def test_routing_review_menu_can_select_twelfth_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    failures = tuple(
        RoutingFailureSummary(
            failure_id=f"failure-{index}",
            category="payload_missing",
            stage="payload_parsing",
            source_filename=f"scan-{index}.png",
            source_page_number=1,
            activity_id=None,
            latest_status=None,
        )
        for index in range(1, 13)
    )
    monkeypatch.setattr("concord.menu_scan.list_routing_failures", lambda: failures)
    selected = []
    monkeypatch.setattr(
        "concord.menu_scan.defer_routing_failure",
        lambda failure_id, **_: selected.append(failure_id)
        or SimpleNamespace(resolution_id="resolution-1", resolution_action="deferred"),
    )
    answers = iter(("N", "2", "defer", "Review later.", "RESOLVE", ""))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    state = MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    review_menu(state)
    assert selected == ["failure-12"]
    assert "Page 2 of 2" in capsys.readouterr().out
