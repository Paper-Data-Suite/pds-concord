from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator
from pds_core.scan_failure_metadata import (
    ROUTING_FAILURE_SCHEMA_VERSION,
    RoutingFailureMetadata,
    write_routing_failure_metadata,
)
from pds_core.workspace import ensure_workspace_root

from concord.routing.review import (
    list_routing_failures,
    review_routing_failure,
    routing_failure_summary_label,
)
from concord.workflows.activity import create_activity_context
from concord.workflows.models import CreateActivityContextRequest, WorkflowActor


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 10, 4, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    return root


def _activity(root: Path, activity_id: str = "activity-1") -> ModuleWorkRef:
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id=activity_id,
            title="Seminar Reflection",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
        ),
        workspace_root=root,
    )
    return ModuleWorkRef("concord", "class-1", activity_id)


def _failure(
    root: Path,
    *,
    failure_id: str,
    locator: RouteLocator | None = None,
    category: str = "payload_missing",
    complete_provenance: bool = True,
) -> RoutingFailureMetadata:
    failure = RoutingFailureMetadata(
        schema_version=ROUTING_FAILURE_SCHEMA_VERSION,
        failure_id=failure_id,
        scope="page",
        stage="route_resolution",
        created_at="2026-10-04T21:30:00+00:00",
        failure_category=category,
        failure_message="No usable PDS2 route was detected.",
        source_filename="seminar-period2.pdf",
        source_scan_id="scan-source-1" if complete_provenance else None,
        source_sha256="a" * 64 if complete_provenance else None,
        retained_source_path=(
            "scans/source/2026-10-04/retained.pdf"
            if complete_provenance
            else None
        ),
        review_copy_path=None,
        source_page_number=4,
        detected_payload=None,
        route_locator=locator,
        target=None,
        module_details={},
    )
    write_routing_failure_metadata(root, failure)
    return failure


def _fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    )


def test_failure_list_label_leads_with_teacher_context_not_failure_id(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _failure(root, failure_id="failure-machine-identity")

    summary = list_routing_failures(workspace_root=root)[0]
    label = routing_failure_summary_label(summary)

    assert label == (
        "seminar-period2.pdf — page 4 — QR/PDS2 route missing — unresolved"
    )
    assert "failure-machine-identity" not in label


def test_known_concord_work_is_bound_and_activity_title_is_exact_and_read_only(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    work = _activity(root)
    locator = RouteLocator(PDS2_SCHEMA, work, "route-failed-1")
    _failure(root, failure_id="failure-known-concord", locator=locator)
    before = _fingerprint(root)

    review = review_routing_failure(
        "failure-known-concord",
        workspace_root=root,
    )

    assert _fingerprint(root) == before
    assert review.bound_work == work
    assert review.activity_title == "Seminar Reflection"
    assert review.activity_label == "Seminar Reflection"
    assert review.problem_label == "QR/PDS2 route missing"
    assert review.status_label == "unresolved"
    assert review.retained_provenance_complete is True
    assert review.route_action_available is True
    assert review.route_action_unavailable_reason is None
    assert review.available_actions == ("route", "defer", "technical_details")


def test_unknown_activity_failure_can_route_without_inventing_activity_context(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _failure(root, failure_id="failure-no-route", locator=None)

    review = review_routing_failure("failure-no-route", workspace_root=root)

    assert review.bound_work is None
    assert review.activity_title is None
    assert review.activity_label == "Not determined"
    assert review.route_action_available is True
    assert review.available_actions == ("route", "defer", "technical_details")


def test_known_other_module_never_offers_concord_route_correction(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    foreign = RouteLocator(
        PDS2_SCHEMA,
        ModuleWorkRef("foreign", "class-1", "work-1"),
        "foreign-route-1",
    )
    _failure(root, failure_id="failure-foreign", locator=foreign)

    review = review_routing_failure("failure-foreign", workspace_root=root)

    assert review.bound_work is None
    assert review.activity_title is None
    assert review.route_action_available is False
    assert review.route_action_unavailable_reason == "known_other_module"
    assert review.available_actions == ("defer", "technical_details")


def test_incomplete_retained_provenance_hides_impossible_route_action(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _failure(
        root,
        failure_id="failure-incomplete-provenance",
        complete_provenance=False,
    )

    review = review_routing_failure(
        "failure-incomplete-provenance",
        workspace_root=root,
    )

    assert review.retained_provenance_complete is False
    assert review.route_action_available is False
    assert review.route_action_unavailable_reason == "retained_provenance_incomplete"
    assert review.available_actions == ("defer", "technical_details")


def test_known_concord_missing_activity_does_not_fall_back_to_another_activity(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _activity(root, "other-activity")
    missing_work = ModuleWorkRef("concord", "class-1", "missing-activity")
    locator = RouteLocator(PDS2_SCHEMA, missing_work, "route-failed-1")
    _failure(root, failure_id="failure-missing-activity", locator=locator)

    review = review_routing_failure(
        "failure-missing-activity",
        workspace_root=root,
    )

    assert review.bound_work == missing_work
    assert review.activity_title is None
    assert review.activity_label == "Not determined"
    assert review.route_action_available is False
    assert review.route_action_unavailable_reason == (
        "known_concord_activity_unavailable"
    )
    assert review.available_actions == ("defer", "technical_details")
