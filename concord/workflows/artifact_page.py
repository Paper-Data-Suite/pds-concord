"""Artifact Page preparation and returned-page filing services."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, cast
from uuid import uuid4

from pds_core.pds2 import serialize_pds2_payload
from pds_core.route_ids import generate_route_id
from pds_core.route_registrations import (
    RouteRegistrationNotFoundError,
    RouteRegistrationWriteError,
    load_route_registration,
    write_route_registration,
)
from pds_core.routing_models import (
    PDS2_SCHEMA,
    ROUTE_REGISTRATION_SCHEMA_VERSION,
    ModuleRecordRef,
    ModuleWorkRef,
    RouteLocator,
    RouteRegistration,
    RouteResolution,
)
from pds_core.scan_retention import RetainedSourceScan
from pds_core.standards import StandardsLibrary, load_workspace_standards_library

from concord import __version__
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ActorReference,
    ArtifactInstance,
    ArtifactPage,
    PrivacyPolicy,
    Provenance,
    ScanReference,
)
from concord.storage import commit_record_batch, load_current_record_graph
from concord.storage_models import ConcordStorageCommitResult
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult

CONCORD_MODULE_ID: Final[str] = "concord"
ARTIFACT_PAGE_KIND: Final[str] = "artifact_page"
ARTIFACT_PAGE_CONTRACT_VERSION: Final[str] = "1"
ACTIVE_ROUTE_STATUS: Final[str] = "active"
_ROUTABLE_PAGE_STATUSES: Final[frozenset[str]] = frozenset(
    {
        "planned",
        "generated",
        "distributed",
        "returned",
        "missing",
        "duplicate",
        "damaged",
    }
)

_TERMINAL_ARTIFACT_STATUSES: Final[frozenset[str]] = frozenset(
    {"completed", "cancelled", "archived", "superseded"}
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPagePlan:
    page_number: int
    page_kind: str = "primary"
    return_expected: bool = True
    route_required: bool = True
    artifact_page_id: str | None = None
    continuation_of_page_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareArtifactPagesRequest:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    template_version_id: str
    artifact_category: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    pages: tuple[ArtifactPagePlan, ...]
    expected_return_status: str = "returned_expected"
    privacy_policy: PrivacyPolicy
    session_id: str | None = None
    group_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPage:
    artifact_page_id: str
    page_number: int
    route_id: str | None
    pds2_payload: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareArtifactPagesResult:
    commit: WorkflowCommitResult
    artifact_instance_id: str
    pages: tuple[PreparedPage, ...]
    routes_expected: int
    routes_verified: int


class ArtifactRoutePreparationPartialSuccessError(RuntimeError):
    """Artifact state was published but one or more immutable routes are absent."""

    def __init__(self, result: PrepareArtifactPagesResult, cause: Exception) -> None:
        super().__init__(
            f"Artifact Pages are durable, but only {result.routes_verified} of "
            f"{result.routes_expected} routes were verified."
        )
        self.result = result
        self.__cause__ = cause


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactPageSummary:
    artifact_instance_id: str
    artifact_page_id: str
    page_number: int
    page_kind: str
    page_status: str
    route_id: str | None
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRouteDispatchResult:
    work: ModuleWorkRef
    artifact_instance_id: str
    artifact_page_id: str
    route_id: str
    scan_reference_id: str
    source_scan_id: str
    source_page_number: int
    snapshot_revision: int
    snapshot_sha256: str
    replayed: bool


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef(CONCORD_MODULE_ID, class_id, activity_id)


def _standards(root: Path) -> StandardsLibrary | None:
    try:
        return load_workspace_standards_library(root)
    except FileNotFoundError:
        return None
    except ValueError:
        return None


def _returned_artifact_state(
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
    returned_page: ArtifactPage,
) -> ArtifactInstance:
    pages = {item.artifact_page_id: item for item in graph.artifact_pages}
    required: list[ArtifactPage] = []
    for page_id in artifact.page_ids:
        page = (
            returned_page
            if page_id == returned_page.artifact_page_id
            else pages.get(page_id)
        )
        if page is None or page.artifact_instance_id != artifact.artifact_instance_id:
            raise ConcordWorkflowValidationError(
                "Artifact declared page structure is inconsistent."
            )
        if page.return_expected:
            required.append(page)
    if not required:
        return artifact
    returned_count = sum(page.page_status == "returned" for page in required)
    if returned_count == 0:
        return artifact
    status = "returned" if returned_count == len(required) else "partially_returned"
    return artifact if artifact.artifact_status == status else replace(
        artifact, artifact_status=status
    )


def _registration(work: ModuleWorkRef, page: ArtifactPage) -> RouteRegistration:
    if page.route_id is None or page.human_fallback is None:
        raise ConcordWorkflowValidationError("routable page identity is incomplete.")
    return RouteRegistration(
        schema_version=ROUTE_REGISTRATION_SCHEMA_VERSION,
        locator=RouteLocator(PDS2_SCHEMA, work, page.route_id),
        target=ModuleRecordRef(
            CONCORD_MODULE_ID,
            ARTIFACT_PAGE_KIND,
            page.artifact_page_id,
            ARTIFACT_PAGE_CONTRACT_VERSION,
        ),
        created_at=page.created_provenance.timestamp,
        status=ACTIVE_ROUTE_STATUS,
        human_fallback=page.human_fallback,
        module_details={
            "activity_id": work.work_id,
            "artifact_instance_id": page.artifact_instance_id,
            "artifact_page_id": page.artifact_page_id,
            "page_number": page.page_number,
        },
    )


def concord_route_registration(
    work: ModuleWorkRef,
    page: ArtifactPage,
) -> RouteRegistration:
    """Build the exact immutable Core registration for one Concord page."""
    return _registration(work, page)


def reconcile_concord_route_registration(
    workspace_root: str | Path,
    registration: RouteRegistration,
) -> None:
    """Create or exactly reconcile one immutable Concord-owned Core route."""
    root = Path(workspace_root)
    validate_concord_route_registration(registration)
    _reconcile_route(root, registration)


def validate_concord_route_registration(registration: RouteRegistration, /) -> None:
    """Validate Concord-owned registration structure without reading state."""
    if not isinstance(registration, RouteRegistration):
        raise ConcordWorkflowValidationError(
            "registration must be a RouteRegistration."
        )
    locator = registration.locator
    target = registration.target
    if (
        locator.module_id != CONCORD_MODULE_ID
        or locator.work.module_id != CONCORD_MODULE_ID
    ):
        raise ConcordWorkflowValidationError("Concord registration has a wrong module.")
    if (
        target.module_id != CONCORD_MODULE_ID
        or target.record_kind != ARTIFACT_PAGE_KIND
    ):
        raise ConcordWorkflowValidationError("Concord route must target artifact_page.")
    if target.contract_version != ARTIFACT_PAGE_CONTRACT_VERSION:
        raise ConcordWorkflowValidationError(
            "unsupported Artifact Page contract version."
        )
    if registration.schema_version != ROUTE_REGISTRATION_SCHEMA_VERSION:
        raise ConcordWorkflowValidationError("unsupported route-registration schema.")
    if locator.schema != PDS2_SCHEMA:
        raise ConcordWorkflowValidationError("unsupported QR schema.")
    if registration.status != ACTIVE_ROUTE_STATUS:
        raise ConcordWorkflowValidationError("Concord route is not active.")
    expected_keys = {
        "activity_id",
        "artifact_instance_id",
        "artifact_page_id",
        "page_number",
    }
    details = registration.module_details
    if set(details) != expected_keys:
        raise ConcordWorkflowValidationError("malformed Concord module_details.")
    if (
        details["activity_id"] != locator.work_id
        or details["artifact_page_id"] != target.record_id
        or not isinstance(details["artifact_instance_id"], str)
        or type(details["page_number"]) is not int
        or details["page_number"] < 1
    ):
        raise ConcordWorkflowValidationError("inconsistent Concord module_details.")


def _reconcile_route(root: Path, expected: RouteRegistration) -> None:
    try:
        actual = load_route_registration(root, expected.locator)
    except RouteRegistrationNotFoundError:
        try:
            write_route_registration(root, expected)
        except RouteRegistrationWriteError:
            # A concurrent creator may have won the exclusive write. Only the
            # exact immutable registration below makes that race a reconciliation.
            pass
        actual = load_route_registration(root, expected.locator)
    if actual != expected:
        raise ConcordWorkflowValidationError(
            f"contradictory immutable route: {expected.locator.route_id}"
        )
    validate_concord_route_registration(actual)


def prepare_artifact_pages(
    request: PrepareArtifactPagesRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PrepareArtifactPagesResult:
    """Publish native page identities, then reconcile every immutable Core route."""
    if not request.pages:
        raise ConcordWorkflowValidationError("pages must not be empty.")
    supplied_page_ids = tuple(page.artifact_page_id for page in request.pages)
    if any(supplied_page_ids) and not all(supplied_page_ids):
        raise ConcordWorkflowValidationError(
            "artifact_page_id must be supplied for every page or for none."
        )
    numbers = tuple(page.page_number for page in request.pages)
    if numbers != tuple(range(1, len(numbers) + 1)):
        raise ConcordWorkflowValidationError(
            "page numbers must be ordered and contiguous."
        )
    root = ensure_mutating_workspace_root(workspace_root).root
    require_core_class(root, request.class_id)
    work = _work(request.class_id, request.activity_id)
    library = standards_library if standards_library is not None else _standards(root)
    loaded = load_current_record_graph(root, work, standards_library=library)
    graph = cast(ConcordRecordGraph, loaded.graph)
    if loaded.snapshot_revision != request.expected_snapshot_revision:
        from concord.storage_errors import ConcordStorageConflictError

        raise ConcordStorageConflictError(
            f"expected snapshot {request.expected_snapshot_revision}, "
            f"found {loaded.snapshot_revision}."
        )
    existing = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == request.artifact_instance_id
        ),
        None,
    )
    if existing is not None:
        pages = tuple(
            sorted(
                (
                    item
                    for item in graph.artifact_pages
                    if item.artifact_instance_id == existing.artifact_instance_id
                ),
                key=lambda item: item.page_number,
            )
        )
        if len(pages) != len(request.pages):
            raise ConcordWorkflowValidationError(
                "existing Artifact page plan conflicts with retry."
            )
        expected_ids = tuple(plan.artifact_page_id for plan in request.pages)
        if any(expected_ids) and expected_ids != tuple(
            page.artifact_page_id for page in pages
        ):
            raise ConcordWorkflowValidationError(
                "existing Artifact Page identities conflict with retry."
            )
        if (
            existing.template_version_id != request.template_version_id
            or existing.artifact_category != request.artifact_category
            or existing.expected_return_status != request.expected_return_status
            or existing.session_id != request.session_id
            or existing.group_id != request.group_id
            or existing.privacy_policy != request.privacy_policy
            or any(
                page.page_number != plan.page_number
                or page.page_kind != plan.page_kind
                or page.return_expected != plan.return_expected
                or page.route_required != plan.route_required
                or page.continuation_of_page_id != plan.continuation_of_page_id
                for page, plan in zip(pages, request.pages, strict=True)
            )
        ):
            raise ConcordWorkflowValidationError(
                "existing Artifact page plan conflicts with retry."
            )
        commit = ConcordStorageCommitResult(
            work, loaded.snapshot_revision, loaded.snapshot_sha256, (), True
        )
    else:
        created = provenance(request.actor, clock=clock, source_kind="generated")
        pages = tuple(
            ArtifactPage(
                artifact_page_id=plan.artifact_page_id or f"page_{uuid4().hex}",
                artifact_instance_id=request.artifact_instance_id,
                page_number=plan.page_number,
                expected_page_count=len(request.pages),
                page_kind=plan.page_kind,
                return_expected=plan.return_expected,
                route_required=plan.route_required,
                route_id=generate_route_id() if plan.route_required else None,
                human_fallback=(
                    f"Concord {request.activity_id} page {plan.page_number}"
                    if plan.route_required
                    else None
                ),
                continuation_of_page_id=plan.continuation_of_page_id,
                page_status="planned",
                created_provenance=created,
            )
            for plan in request.pages
        )
        artifact = ArtifactInstance(
            artifact_instance_id=request.artifact_instance_id,
            template_version_id=request.template_version_id,
            activity_id=request.activity_id,
            artifact_category=request.artifact_category,
            generation_status="planned",
            expected_return_status=request.expected_return_status,
            artifact_status="planned",
            privacy_policy=request.privacy_policy,
            page_ids=tuple(page.artifact_page_id for page in pages),
            created_provenance=created,
            session_id=request.session_id,
            group_id=request.group_id,
        )
        commit = commit_record_batch(
            root,
            work,
            (artifact, *pages),
            expected_snapshot_revision=request.expected_snapshot_revision,
            standards_library=library,
        )
    verified = 0
    expected_routes = sum(page.route_required for page in pages)
    prepared = tuple(
        PreparedPage(
            artifact_page_id=page.artifact_page_id,
            page_number=page.page_number,
            route_id=page.route_id,
            pds2_payload=(
                serialize_pds2_payload(_registration(work, page).locator)
                if page.route_required
                else None
            ),
        )
        for page in pages
    )
    result = PrepareArtifactPagesResult(
        commit=WorkflowCommitResult.from_storage(commit),
        artifact_instance_id=request.artifact_instance_id,
        pages=prepared,
        routes_expected=expected_routes,
        routes_verified=0,
    )
    try:
        for page in pages:
            if page.route_required:
                _reconcile_route(root, _registration(work, page))
                verified += 1
    except Exception as error:
        raise ArtifactRoutePreparationPartialSuccessError(
            replace(result, routes_verified=verified), error
        ) from error
    return replace(result, routes_verified=verified)


def list_artifact_pages(
    class_id: str, activity_id: str, *, workspace_root: str | Path | None = None
) -> tuple[ArtifactPageSummary, ...]:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = _work(class_id, activity_id)
    loaded = load_current_record_graph(root, work, standards_library=_standards(root))
    graph = cast(ConcordRecordGraph, loaded.graph)
    return tuple(
        ArtifactPageSummary(
            artifact_instance_id=page.artifact_instance_id,
            artifact_page_id=page.artifact_page_id,
            page_number=page.page_number,
            page_kind=page.page_kind,
            page_status=page.page_status,
            route_id=page.route_id,
            snapshot_revision=loaded.snapshot_revision,
        )
        for page in sorted(
            graph.artifact_pages,
            key=lambda item: (item.artifact_instance_id, item.page_number),
        )
    )


def handle_concord_route(
    resolution: RouteResolution,
    retained_source: RetainedSourceScan,
    source_page_number: int,
    /,
) -> ConcordRouteDispatchResult:
    """File one exact retained physical page against its canonical Artifact Page."""
    if not isinstance(resolution, RouteResolution):
        raise ConcordWorkflowValidationError("resolution must be RouteResolution.")
    if not isinstance(retained_source, RetainedSourceScan):
        raise ConcordWorkflowValidationError(
            "retained_source must be RetainedSourceScan."
        )
    if type(source_page_number) is not int or source_page_number < 1:
        raise ConcordWorkflowValidationError("source_page_number must be positive.")
    validate_concord_route_registration(resolution.registration)
    work = resolution.locator.work
    root = resolution.class_root.parent.parent
    try:
        retained_path = retained_source.retained_source_path.resolve(strict=True)
        expected_path = (root / retained_source.retained_source_relative_path).resolve(
            strict=True
        )
        retained_path.relative_to(root.resolve(strict=True))
    except (OSError, RuntimeError, ValueError) as error:
        raise ConcordWorkflowValidationError(
            "retained source is outside the workspace."
        ) from error
    if retained_path != expected_path or not retained_path.is_file():
        raise ConcordWorkflowValidationError(
            "retained-source provenance is inconsistent."
        )
    digest = hashlib.sha256(retained_path.read_bytes()).hexdigest()
    if digest != retained_source.source_sha256:
        raise ConcordWorkflowValidationError("retained-source digest mismatch.")
    library = _standards(root)
    loaded = load_current_record_graph(root, work, standards_library=library)
    graph = cast(ConcordRecordGraph, loaded.graph)
    page = next(
        (
            item
            for item in graph.artifact_pages
            if item.artifact_page_id == resolution.registration.target.record_id
        ),
        None,
    )
    if page is None:
        raise ConcordWorkflowNotFoundError("routed Artifact Page is unavailable.")
    artifact = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == page.artifact_instance_id
        ),
        None,
    )
    if artifact is None or artifact.activity_id != work.work_id:
        raise ConcordWorkflowValidationError(
            "routed Artifact Page belongs to another Activity."
        )
    if page.route_id != resolution.locator.route_id:
        raise ConcordWorkflowValidationError(
            "route and canonical Artifact Page disagree."
        )
    if page.page_status not in _ROUTABLE_PAGE_STATUSES:
        raise ConcordWorkflowValidationError(
            "Artifact Page lifecycle does not allow return filing."
        )
    occurrence = next(
        (
            item
            for item in graph.scan_references
            if item.source_scan_id == retained_source.source_scan_id
            and item.source_page_number == source_page_number
            and item.route_id == resolution.locator.route_id
        ),
        None,
    )
    if occurrence is not None:
        return ConcordRouteDispatchResult(
            work=work,
            artifact_instance_id=artifact.artifact_instance_id,
            artifact_page_id=page.artifact_page_id,
            route_id=page.route_id,
            scan_reference_id=occurrence.scan_reference_id,
            source_scan_id=occurrence.source_scan_id,
            source_page_number=occurrence.source_page_number,
            snapshot_revision=loaded.snapshot_revision,
            snapshot_sha256=loaded.snapshot_sha256,
            replayed=True,
        )
    if artifact.artifact_status in _TERMINAL_ARTIFACT_STATUSES:
        raise ConcordWorkflowValidationError(
            "Artifact lifecycle does not allow new return filing."
        )
    occurrence_key = (
        f"{retained_source.source_scan_id}|{source_page_number}|{page.route_id}"
    ).encode("utf-8")
    scan_id = f"scanref_{hashlib.sha256(occurrence_key).hexdigest()[:32]}"
    created = Provenance(
        actor=ActorReference(
            actor_kind="system", actor_id="pds_core_dispatch", owning_system="core"
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source_kind="routed",
        source_reference=resolution.registration.target,
        application_version=__version__,
    )
    scan = ScanReference(
        scan_reference_id=scan_id,
        activity_id=work.work_id,
        artifact_page_id=page.artifact_page_id,
        route_id=page.route_id,
        source_scan_id=retained_source.source_scan_id,
        source_page_number=source_page_number,
        retained_source_relative_path=retained_source.retained_source_relative_path,
        retained_source_sha256=retained_source.source_sha256,
        created_provenance=created,
    )
    returned_page = (
        page
        if page.page_status == "returned"
        else replace(page, page_status="returned")
    )
    returned_artifact = _returned_artifact_state(artifact, graph, returned_page)
    records: tuple[
        ScanReference | ArtifactPage | ArtifactInstance, ...
    ] = (scan,)
    if returned_page != page:
        records += (returned_page,)
    if returned_artifact != artifact:
        records += (returned_artifact,)
    commit = commit_record_batch(
        root,
        work,
        records,
        expected_snapshot_revision=loaded.snapshot_revision,
        standards_library=library,
    )
    return ConcordRouteDispatchResult(
        work=work,
        artifact_instance_id=artifact.artifact_instance_id,
        artifact_page_id=page.artifact_page_id,
        route_id=page.route_id,
        scan_reference_id=scan.scan_reference_id,
        source_scan_id=scan.source_scan_id,
        source_page_number=source_page_number,
        snapshot_revision=commit.snapshot_revision,
        snapshot_sha256=commit.snapshot_sha256,
        replayed=False,
    )


__all__ = [
    "ArtifactPagePlan",
    "ArtifactPageSummary",
    "ArtifactRoutePreparationPartialSuccessError",
    "ConcordRouteDispatchResult",
    "PrepareArtifactPagesRequest",
    "PrepareArtifactPagesResult",
    "PreparedPage",
    "handle_concord_route",
    "list_artifact_pages",
    "prepare_artifact_pages",
    "validate_concord_route_registration",
]
