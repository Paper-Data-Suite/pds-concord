from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from pds_core.routing_models import (
    PDS2_SCHEMA,
    ModuleRecordRef,
    ModuleWorkRef,
    RouteLocator,
)
from pds_core.scan_failure_metadata import (
    ROUTING_FAILURE_SCHEMA_VERSION,
    RoutingFailureMetadata,
    write_routing_failure_metadata,
)
from pds_core.scan_resolution_metadata import (
    create_scan_resolution_metadata,
    write_scan_resolution_metadata,
)
from pds_core.workspace import ensure_workspace_root

import concord.menu_scan as menu_scan
import concord.routing.review as review_module
from concord.routing.candidates import ConcordRouteCandidate
from concord.routing.review import (
    RoutingFailureAlreadyResolvedError,
    RoutingFailureReview,
    RoutingFailureSummary,
    defer_routing_failure,
    resolve_routing_failure_with_route,
)
from concord.workflows.models import WorkflowActor


def _workspace(tmp_path: Path) -> Path:
    return ensure_workspace_root(tmp_path / "workspace")


def _failure(root: Path) -> RoutingFailureMetadata:
    retained_relative = "scans/retained/stale-review.pdf"
    retained = root / retained_relative
    retained.parent.mkdir(parents=True, exist_ok=True)
    retained.write_bytes(b"synthetic retained scan")
    failure = RoutingFailureMetadata(
        schema_version=ROUTING_FAILURE_SCHEMA_VERSION,
        failure_id="failure_stale_1",
        scope="page",
        stage="route_resolution",
        created_at="2026-01-01T00:00:00+00:00",
        failure_category="route_unknown",
        failure_message="Synthetic routing failure.",
        source_filename="stale-review.pdf",
        source_scan_id="scan_stale_1",
        source_sha256="a" * 64,
        retained_source_path=retained_relative,
        review_copy_path=None,
        source_page_number=2,
        detected_payload=None,
        route_locator=None,
        target=None,
        module_details={},
    )
    write_routing_failure_metadata(root, failure)
    return failure


def _locator() -> RouteLocator:
    return RouteLocator(
        PDS2_SCHEMA,
        ModuleWorkRef("concord", "class-1", "activity-1"),
        "route-1",
    )


def _target() -> ModuleRecordRef:
    return ModuleRecordRef("concord", "artifact_page", "page-1")


def _append_resolution(
    root: Path,
    failure: RoutingFailureMetadata,
    *,
    resolution_id: str,
    status: str,
) -> None:
    if status == "resolved":
        resolution = create_scan_resolution_metadata(
            failure,
            resolution_id=resolution_id,
            resolution_status="resolved",
            resolution_action="route_selected",
            resolved_at="2026-01-02T00:00:00+00:00",
            resolution_message="Resolved elsewhere.",
            route_locator=_locator(),
            target=_target(),
        )
    else:
        resolution = create_scan_resolution_metadata(
            failure,
            resolution_id=resolution_id,
            resolution_status="deferred",
            resolution_action="deferred",
            resolved_at="2026-01-02T00:00:00+00:00",
            resolution_message="Deferred for later review.",
        )
    write_scan_resolution_metadata(root, resolution)


def _resolution_files(root: Path) -> tuple[str, ...]:
    directory = root / "routing_review" / "resolutions"
    if not directory.exists():
        return ()
    return tuple(sorted(path.name for path in directory.glob("*.json")))


def _patch_route_prerequisites(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        review_module,
        "load_route_registration",
        lambda _root, _locator: SimpleNamespace(target=_target()),
    )
    monkeypatch.setattr(
        review_module,
        "validate_concord_route_registration",
        lambda _registration: None,
    )
    monkeypatch.setattr(
        review_module,
        "_retained_intake_provenance",
        lambda _failure, _path: (
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            date(2026, 1, 1),
        ),
    )


def test_already_resolved_failure_cannot_be_deferred_again(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    failure = _failure(root)
    _append_resolution(
        root,
        failure,
        resolution_id="resolution_resolved_1",
        status="resolved",
    )
    before = _resolution_files(root)

    with pytest.raises(
        RoutingFailureAlreadyResolvedError,
        match="already resolved",
    ):
        defer_routing_failure(
            failure.failure_id,
            message="Stale defer attempt.",
            workspace_root=root,
        )

    assert _resolution_files(root) == before


def test_resolve_rechecks_persisted_status_immediately_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    failure = _failure(root)
    _append_resolution(
        root,
        failure,
        resolution_id="resolution_resolved_1",
        status="resolved",
    )
    _patch_route_prerequisites(monkeypatch)
    before = _resolution_files(root)
    monkeypatch.setattr(
        review_module,
        "dispatch_route",
        lambda *_args, **_kwargs: pytest.fail(
            "already-resolved stale failure must not dispatch"
        ),
    )

    with pytest.raises(
        RoutingFailureAlreadyResolvedError,
        match="already resolved",
    ):
        resolve_routing_failure_with_route(
            failure.failure_id,
            _locator(),
            message="Stale resolve attempt.",
            workspace_root=root,
            registry=object(),  # type: ignore[arg-type]
        )

    assert _resolution_files(root) == before


def test_deferred_failure_remains_eligible_for_later_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    failure = _failure(root)
    _append_resolution(
        root,
        failure,
        resolution_id="resolution_deferred_1",
        status="deferred",
    )
    _patch_route_prerequisites(monkeypatch)
    dispatches: list[tuple[RouteLocator, int]] = []

    def dispatch(_root: Path, _registry: object, request: Any) -> object:
        dispatches.append((request.locator, request.source_page_number))
        return SimpleNamespace(module_result="synthetic-dispatch")

    monkeypatch.setattr(review_module, "dispatch_route", dispatch)

    resolution = resolve_routing_failure_with_route(
        failure.failure_id,
        _locator(),
        message="Teacher selected the exact destination.",
        workspace_root=root,
        registry=object(),  # type: ignore[arg-type]
    )

    assert dispatches == [(_locator(), 2)]
    assert resolution.resolution_status == "resolved"
    assert resolution.resolution_action == "route_selected"
    assert review_module._latest_resolution_status(root, failure.failure_id) == (
        "resolved"
    )


def _menu_review() -> RoutingFailureReview:
    failure = RoutingFailureMetadata(
        schema_version=ROUTING_FAILURE_SCHEMA_VERSION,
        failure_id="failure_stale_1",
        scope="page",
        stage="route_resolution",
        created_at="2026-01-01T00:00:00+00:00",
        failure_category="route_unknown",
        failure_message="Synthetic routing failure.",
        source_filename="stale-review.pdf",
        source_scan_id="scan_stale_1",
        source_sha256="a" * 64,
        retained_source_path="scans/retained/stale-review.pdf",
        review_copy_path=None,
        source_page_number=2,
        detected_payload=None,
        route_locator=None,
        target=None,
        module_details={},
    )
    return RoutingFailureReview(
        failure=failure,
        latest_status=None,
        activity_title=None,
        bound_work=None,
        retained_provenance_complete=True,
        route_action_available=True,
        route_action_unavailable_reason=None,
        route_action_unavailable_detail=None,
    )


def _menu_candidate() -> ConcordRouteCandidate:
    locator = _locator()
    return ConcordRouteCandidate(
        locator=locator,
        activity_id=locator.work_id,
        activity_title="Stale Review Activity",
        artifact_instance_id="artifact-1",
        artifact_page_id="page-1",
        page_number=1,
        page_kind="response",
        artifact_category="student_work",
        human_fallback="Stale Review Activity page 1",
        session_id=None,
        session_label=None,
        group_id=None,
        group_label=None,
        replayed_occurrence=False,
    )


def test_stale_route_menu_reports_changed_state_without_success_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary = RoutingFailureSummary(
        failure_id="failure_stale_1",
        category="route_unknown",
        stage="route_resolution",
        source_filename="stale-review.pdf",
        source_page_number=2,
        activity_id=None,
        latest_status=None,
    )
    review = _menu_review()
    candidate = _menu_candidate()
    shown: list[tuple[str, tuple[str, ...]]] = []

    monkeypatch.setattr(menu_scan, "list_routing_failures", lambda: (summary,))
    monkeypatch.setattr(menu_scan, "select_one", lambda *a, **k: summary)
    monkeypatch.setattr(menu_scan, "review_routing_failure", lambda _id: review)
    monkeypatch.setattr(menu_scan, "_choose_routing_review_action", lambda _r: "route")
    monkeypatch.setattr(
        menu_scan,
        "_select_routing_destination_candidate",
        lambda _r: candidate,
    )
    monkeypatch.setattr(menu_scan, "prompt_text", lambda *a, **k: "Teacher note")
    monkeypatch.setattr(menu_scan, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(
        menu_scan,
        "resolve_routing_failure_with_route",
        lambda *a, **k: (_ for _ in ()).throw(
            RoutingFailureAlreadyResolvedError("failure_stale_1")
        ),
    )
    monkeypatch.setattr(
        menu_scan,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    state = SimpleNamespace(
        require_actor=lambda: WorkflowActor(actor_id="teacher-1")
    )

    menu_scan._review(state)  # type: ignore[arg-type]

    assert shown == [
        (
            "Routing Review Changed",
            (
                "This routing failure is already resolved. Reload Routing Review "
                "before taking another action.",
                "No additional routing action was performed.",
            ),
        )
    ]
