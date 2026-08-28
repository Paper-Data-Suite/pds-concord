from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.module_dispatch import (
    ModuleRouteHandlingError,
    RouteDispatchFailure,
    RouteDispatchRequest,
    RouteDispatchSuccess,
    dispatch_route,
    dispatch_routes,
)
from pds_core.module_profiles import (
    CORE_ROUTING_CONTRACT_VERSION,
    ModuleProfile,
    ModuleRegistry,
    UnsupportedModuleError,
)
from pds_core.route_registrations import write_route_registration
from pds_core.routes import module_work_dir
from pds_core.routing_models import (
    PDS2_SCHEMA,
    ROUTE_REGISTRATION_SCHEMA_VERSION,
    ModuleRecordRef,
    ModuleWorkRef,
    RouteLocator,
    RouteRegistration,
    RouteResolution,
)
from pds_core.scan_retention import RetainedSourceScan, retain_source_scan
from pds_core.workspace import ensure_workspace_root

from concord.models import PrivacyPolicy
from concord.pds_module import get_module_profile as get_concord_profile
from concord.workflows.activity import create_activity_context
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    ConcordRouteDispatchResult,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)
from concord.workflows.models import (
    CreateActivityContextRequest,
    WorkflowActor,
)

ForeignHandler = Callable[
    [RouteResolution, RetainedSourceScan, int],
    object,
]


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    timestamp = datetime(2026, 8, 28, tzinfo=timezone.utc)
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=timestamp,
    )
    write_class_metadata_for_class(root, metadata)
    return root


def _prepare_concord_route(root: Path) -> RouteLocator:
    actor = WorkflowActor(actor_id="teacher-1")
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=actor,
        ),
        workspace_root=root,
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-v1",
            artifact_category="student_work",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=actor,
            pages=(ArtifactPagePlan(page_number=1),),
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
        ),
        workspace_root=root,
    )
    route_id = prepared.pages[0].route_id
    assert route_id is not None
    return RouteLocator(
        PDS2_SCHEMA,
        ModuleWorkRef("concord", "class-1", "activity-1"),
        route_id,
    )


def _foreign_locator(
    root: Path,
    *,
    route_id: str = "foreign-route-1",
) -> RouteLocator:
    locator = RouteLocator(
        PDS2_SCHEMA,
        ModuleWorkRef("foreign", "class-1", "foreign-work-1"),
        route_id,
    )
    write_route_registration(
        root,
        RouteRegistration(
            schema_version=ROUTE_REGISTRATION_SCHEMA_VERSION,
            locator=locator,
            target=ModuleRecordRef(
                "foreign",
                "foreign_page",
                "foreign-page-1",
                "1",
            ),
            created_at="2026-08-28T12:00:00+00:00",
            status="active",
            human_fallback="Synthetic foreign page",
            module_details={},
        ),
    )
    return locator


def _foreign_profile(handler: ForeignHandler) -> ModuleProfile:
    return ModuleProfile(
        module_id="foreign",
        display_name="Synthetic Foreign",
        supported_core_routing_contract_versions=frozenset(
            {CORE_ROUTING_CONTRACT_VERSION}
        ),
        supported_qr_schemas=frozenset({PDS2_SCHEMA}),
        supported_route_registration_schema_versions=frozenset(
            {ROUTE_REGISTRATION_SCHEMA_VERSION}
        ),
        dispatchable_route_statuses=frozenset({"active"}),
        route_handler=handler,
    )


def _retained_source(root: Path, tmp_path: Path) -> RetainedSourceScan:
    source = tmp_path / "mixed-return.png"
    source.write_bytes(b"synthetic mixed returned paper bytes")
    return retain_source_scan(
        root,
        source,
        intake_timestamp=datetime(
            2026,
            8,
            28,
            12,
            30,
            tzinfo=timezone.utc,
        ),
    )


def _tree_fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        values.append(
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return tuple(values)


def test_mixed_dispatch_preserves_exact_ownership_and_concord_replay(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    concord_locator = _prepare_concord_route(root)
    foreign_locator = _foreign_locator(root)
    retained = _retained_source(root, tmp_path)
    seen: list[tuple[str, int]] = []

    def _foreign_handler(
        resolution: RouteResolution,
        _retained: RetainedSourceScan,
        source_page_number: int,
    ) -> object:
        seen.append((resolution.locator.route_id, source_page_number))
        return {"owner": "foreign", "page": source_page_number}

    registry = ModuleRegistry(
        (
            get_concord_profile(),
            _foreign_profile(_foreign_handler),
        )
    )
    initial = dispatch_route(
        root,
        registry,
        RouteDispatchRequest(
            locator=concord_locator,
            retained_source=retained,
            source_page_number=1,
        ),
    )
    assert isinstance(initial.module_result, ConcordRouteDispatchResult)
    assert initial.module_result.replayed is False
    assert initial.module_result.source_page_number == 1

    concord_work = module_work_dir(root, concord_locator.work)
    before = _tree_fingerprint(concord_work)

    outcomes = dispatch_routes(
        root,
        registry,
        (
            RouteDispatchRequest(
                locator=foreign_locator,
                retained_source=retained,
                source_page_number=2,
            ),
            RouteDispatchRequest(
                locator=concord_locator,
                retained_source=retained,
                source_page_number=1,
            ),
        ),
    )

    assert all(isinstance(item, RouteDispatchSuccess) for item in outcomes)
    assert outcomes[0].profile.module_id == "foreign"
    assert outcomes[1].profile.module_id == "concord"
    assert seen == [("foreign-route-1", 2)]

    replay = outcomes[1].module_result
    assert isinstance(replay, ConcordRouteDispatchResult)
    assert replay.replayed is True
    assert replay.source_page_number == 1
    assert _tree_fingerprint(concord_work) == before


def test_foreign_handler_failure_does_not_block_later_concord_dispatch(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    concord_locator = _prepare_concord_route(root)
    foreign_locator = _foreign_locator(root)
    retained = _retained_source(root, tmp_path)

    def _foreign_handler(
        _resolution: RouteResolution,
        _retained: RetainedSourceScan,
        _source_page_number: int,
    ) -> object:
        raise RuntimeError("synthetic foreign failure")

    registry = ModuleRegistry(
        (
            get_concord_profile(),
            _foreign_profile(_foreign_handler),
        )
    )
    outcomes = dispatch_routes(
        root,
        registry,
        (
            RouteDispatchRequest(
                locator=foreign_locator,
                retained_source=retained,
                source_page_number=2,
            ),
            RouteDispatchRequest(
                locator=concord_locator,
                retained_source=retained,
                source_page_number=1,
            ),
        ),
    )

    assert isinstance(outcomes[0], RouteDispatchFailure)
    assert isinstance(outcomes[0].error, ModuleRouteHandlingError)
    assert isinstance(outcomes[1], RouteDispatchSuccess)
    assert outcomes[1].profile.module_id == "concord"
    result = outcomes[1].module_result
    assert isinstance(result, ConcordRouteDispatchResult)
    assert result.replayed is False


def test_concord_failure_does_not_block_foreign_or_claim_absent_module(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    concord_locator = _prepare_concord_route(root)
    foreign_locator = _foreign_locator(root)
    retained = _retained_source(root, tmp_path)
    bad_retained = replace(retained, source_sha256="0" * 64)
    seen: list[int] = []

    def _foreign_handler(
        _resolution: RouteResolution,
        _retained: RetainedSourceScan,
        source_page_number: int,
    ) -> object:
        seen.append(source_page_number)
        return "foreign-ok"

    registry = ModuleRegistry(
        (
            get_concord_profile(),
            _foreign_profile(_foreign_handler),
        )
    )
    absent_locator = RouteLocator(
        PDS2_SCHEMA,
        ModuleWorkRef("absent", "class-1", "foreign-work-2"),
        "absent-route-1",
    )
    outcomes = dispatch_routes(
        root,
        registry,
        (
            RouteDispatchRequest(
                locator=concord_locator,
                retained_source=bad_retained,
                source_page_number=1,
            ),
            RouteDispatchRequest(
                locator=absent_locator,
                retained_source=retained,
                source_page_number=2,
            ),
            RouteDispatchRequest(
                locator=foreign_locator,
                retained_source=retained,
                source_page_number=3,
            ),
        ),
    )

    assert isinstance(outcomes[0], RouteDispatchFailure)
    assert isinstance(outcomes[0].error, ModuleRouteHandlingError)
    assert isinstance(outcomes[1], RouteDispatchFailure)
    assert isinstance(outcomes[1].error, UnsupportedModuleError)
    assert isinstance(outcomes[2], RouteDispatchSuccess)
    assert outcomes[2].profile.module_id == "foreign"
    assert seen == [3]
