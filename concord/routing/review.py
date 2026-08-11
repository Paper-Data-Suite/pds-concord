"""Append-only routing-review services over Core v2 metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4

from pds_core.module_dispatch import RouteDispatchRequest, dispatch_route
from pds_core.module_profiles import ModuleRegistry, build_module_registry
from pds_core.route_registrations import load_route_registration
from pds_core.routing_models import RouteLocator
from pds_core.scan_failure_metadata import (
    RoutingFailureMetadata,
    load_routing_failure_metadata,
)
from pds_core.scan_resolution_metadata import (
    ScanResolutionMetadata,
    create_scan_resolution_metadata,
    load_scan_resolution_metadata,
    write_scan_resolution_metadata,
)
from pds_core.scan_retention import RetainedSourceScan
from pds_core.scan_routes import build_retained_source_filename, routing_review_dir
from pds_core.workspace import resolve_workspace_root

from concord.workflows.artifact_page import validate_concord_route_registration
from concord.workflows.models import WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingFailureSummary:
    failure_id: str
    category: str
    stage: str
    source_filename: str
    source_page_number: int | None
    activity_id: str | None
    latest_status: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingResolutionPartialSuccess:
    failure_id: str
    selected_route: RouteLocator
    handler_dispatch_succeeded: bool = True
    evidence_filing_occurred: bool = True
    resolution_metadata_persisted: bool = False


class RoutingResolutionPartialSuccessError(RuntimeError):
    def __init__(
        self, result: RoutingResolutionPartialSuccess, cause: Exception
    ) -> None:
        super().__init__(
            "Handler dispatch succeeded and evidence filing occurred, but routing "
            "resolution metadata was not persisted."
        )
        self.result = result
        self.__cause__ = cause


_RETAINED_TIMESTAMP = re.compile(
    r"^(?P<timestamp>\d{8}T\d{12}Z)__.*__"
    r"(?P<digest>[0-9a-f]{12})\.[^.]+$"
)


def _retained_intake_provenance(
    failure: RoutingFailureMetadata, path: Path
) -> tuple[datetime, date]:
    """Recover Core's intake event from its immutable retained-source identity."""
    match = _RETAINED_TIMESTAMP.fullmatch(path.name)
    if match is None:
        raise ValueError("retained source filename lacks Core intake provenance.")
    timestamp = datetime.strptime(
        match.group("timestamp"), "%Y%m%dT%H%M%S%fZ"
    ).replace(tzinfo=timezone.utc)
    intake_date = date.fromisoformat(path.parent.name)
    if timestamp.date() != intake_date:
        raise ValueError(
            "retained source date bucket contradicts its intake timestamp."
        )
    if (
        failure.source_sha256 is None
        or match.group("digest") != failure.source_sha256[:12].lower()
    ):
        raise ValueError("retained source filename contradicts its SHA-256 identity.")
    expected_scan_id = f"scan_{path.stem}"
    if failure.source_scan_id != expected_scan_id:
        raise ValueError("retained source filename contradicts its scan identity.")
    expected_filename = build_retained_source_filename(
        intake_timestamp=timestamp,
        original_filename=failure.source_filename,
        sha256_hex=failure.source_sha256,
    )
    if path.name != expected_filename:
        raise ValueError("retained source filename is not Core-canonical.")
    return timestamp, intake_date


def _resolution_ids(root: Path) -> tuple[str, ...]:
    directory = routing_review_dir(root) / "resolutions"
    if not directory.exists():
        return ()
    return tuple(
        sorted(
            path.stem
            for path in directory.glob("*.json")
            if path.is_file() and not path.is_symlink()
        )
    )


def list_routing_failures(
    *,
    workspace_root: str | Path | None = None,
    activity_id: str | None = None,
    state: str = "open",
) -> tuple[RoutingFailureSummary, ...]:
    if state not in {"open", "all"}:
        raise ValueError("state must be open or all.")
    root = resolve_workspace_root(workspace_root)
    resolutions: dict[str, list[ScanResolutionMetadata]] = {}
    for resolution_id in _resolution_ids(root):
        value = load_scan_resolution_metadata(root, resolution_id)
        resolutions.setdefault(value.failure_id, []).append(value)
    directory = routing_review_dir(root)
    if not directory.exists():
        return ()
    result = []
    for path in sorted(directory.glob("*.json"), key=lambda item: item.name):
        if path.is_symlink() or not path.is_file():
            continue
        failure = load_routing_failure_metadata(root, path.stem)
        candidate_activity = (
            failure.route_locator.work_id
            if failure.route_locator and failure.route_locator.module_id == "concord"
            else None
        )
        if activity_id is not None and candidate_activity != activity_id:
            continue
        linked = sorted(
            resolutions.get(failure.failure_id, ()), key=lambda item: item.resolved_at
        )
        latest = linked[-1].resolution_status if linked else None
        if state == "open" and latest == "resolved":
            continue
        result.append(
            RoutingFailureSummary(
                failure_id=failure.failure_id,
                category=failure.failure_category,
                stage=failure.stage,
                source_filename=failure.source_filename,
                source_page_number=failure.source_page_number,
                activity_id=candidate_activity,
                latest_status=latest,
            )
        )
    return tuple(result)


def show_routing_failure(
    failure_id: str, *, workspace_root: str | Path | None = None
) -> RoutingFailureMetadata:
    return load_routing_failure_metadata(
        resolve_workspace_root(workspace_root), failure_id
    )


def defer_routing_failure(
    failure_id: str,
    *,
    message: str,
    workspace_root: str | Path | None = None,
    reviewer: WorkflowActor | None = None,
) -> ScanResolutionMetadata:
    root = resolve_workspace_root(workspace_root)
    failure = load_routing_failure_metadata(root, failure_id)
    resolution = create_scan_resolution_metadata(
        failure,
        resolution_id=f"resolution_{uuid4().hex}",
        resolution_status="deferred",
        resolution_action="deferred",
        resolved_at=datetime.now(timezone.utc).isoformat(),
        resolution_message=message,
        module_details={
            "review_module": "concord",
            **({} if reviewer is None else {"review_actor_id": reviewer.actor_id}),
        },
    )
    write_scan_resolution_metadata(root, resolution)
    return resolution


def resolve_routing_failure_with_route(
    failure_id: str,
    locator: RouteLocator,
    *,
    message: str,
    workspace_root: str | Path | None = None,
    registry: ModuleRegistry | None = None,
    reviewer: WorkflowActor | None = None,
) -> ScanResolutionMetadata:
    """Explicitly re-dispatch through an existing route, then append resolution."""
    root = resolve_workspace_root(workspace_root)
    failure = load_routing_failure_metadata(root, failure_id)
    if locator.module_id != "concord":
        raise ValueError("teacher route correction requires a Concord route.")
    if (
        failure.route_locator is not None
        and failure.route_locator.module_id != "concord"
    ):
        raise ValueError(
            "another module's failed route cannot be reinterpreted as Concord evidence."
        )
    if (
        failure.source_scan_id is None
        or failure.source_sha256 is None
        or failure.retained_source_path is None
        or failure.source_page_number is None
    ):
        raise ValueError(
            "failure lacks retained-page provenance required for re-dispatch."
        )
    registration = load_route_registration(root, locator)
    validate_concord_route_registration(registration)
    if (
        failure.route_locator is not None
        and failure.route_locator.module_id == "concord"
        and locator.work != failure.route_locator.work
    ):
        raise ValueError("selected Concord route belongs to another Activity work.")
    path = (root / failure.retained_source_path).resolve(strict=True)
    path.relative_to(root.resolve(strict=True))
    timestamp, intake_date = _retained_intake_provenance(failure, path)
    retained = RetainedSourceScan(
        source_scan_id=failure.source_scan_id,
        source_filename=failure.source_filename,
        source_sha256=failure.source_sha256,
        retained_source_path=path,
        retained_source_relative_path=failure.retained_source_path,
        intake_timestamp=timestamp,
        intake_date=intake_date,
    )
    dispatched = dispatch_route(
        root,
        registry or build_module_registry(),
        RouteDispatchRequest(locator, retained, failure.source_page_number),
    )
    action = (
        "route_corrected" if failure.route_locator is not None else "route_selected"
    )
    resolution = create_scan_resolution_metadata(
        failure,
        resolution_id=f"resolution_{uuid4().hex}",
        resolution_status="resolved",
        resolution_action=action,
        resolved_at=datetime.now(timezone.utc).isoformat(),
        resolution_message=message,
        route_locator=locator,
        target=registration.target,
        module_details={
            "review_module": "concord",
            "handler_succeeded": True,
            **({} if reviewer is None else {"review_actor_id": reviewer.actor_id}),
        },
    )
    try:
        write_scan_resolution_metadata(root, resolution)
    except Exception as error:
        raise RoutingResolutionPartialSuccessError(
            RoutingResolutionPartialSuccess(
                failure_id=failure.failure_id,
                selected_route=locator,
            ),
            error,
        ) from error
    _ = dispatched.module_result
    return resolution


__all__ = [
    "RoutingFailureSummary",
    "RoutingResolutionPartialSuccess",
    "RoutingResolutionPartialSuccessError",
    "defer_routing_failure",
    "list_routing_failures",
    "resolve_routing_failure_with_route",
    "show_routing_failure",
]
