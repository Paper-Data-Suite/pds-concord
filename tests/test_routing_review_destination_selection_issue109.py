from __future__ import annotations

from typing import Any

import pytest
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator
from pds_core.scan_failure_metadata import RoutingFailureMetadata

import concord.menu_scan as menu_scan
import concord.routing.destinations as destination_module
from concord.routing.candidates import (
    ConcordRouteCandidate,
    ConcordRouteCandidateProjection,
)
from concord.routing.destinations import (
    list_routing_destination_activities,
    list_routing_destination_classes,
    project_routing_destination_candidates,
    routing_destination_candidate_label,
)
from concord.routing.review import RoutingFailureReview
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import ActivitySummary, ClassSummary


def _review(*, bound_work: ModuleWorkRef | None = None) -> RoutingFailureReview:
    locator = (
        None
        if bound_work is None
        else RouteLocator(PDS2_SCHEMA, bound_work, "route-1")
    )
    failure = RoutingFailureMetadata(
        schema_version="2",
        failure_id="failure_1",
        scope="page",
        stage="route_resolution",
        created_at="2026-10-04T22:00:00+00:00",
        failure_category="route_unknown",
        failure_message="Synthetic routing failure.",
        source_filename="teacher-scan.pdf",
        source_scan_id="scan_test_1",
        source_sha256="a" * 64,
        retained_source_path="scans/retained/teacher-scan.pdf",
        review_copy_path=None,
        source_page_number=2,
        detected_payload=None,
        route_locator=locator,
        target=None,
        module_details={},
    )
    return RoutingFailureReview(
        failure=failure,
        latest_status=None,
        activity_title="Known Activity" if bound_work is not None else None,
        bound_work=bound_work,
        retained_provenance_complete=True,
        route_action_available=True,
        route_action_unavailable_reason=None,
        route_action_unavailable_detail=None,
    )


def _candidate(work: ModuleWorkRef) -> ConcordRouteCandidate:
    return ConcordRouteCandidate(
        locator=RouteLocator(PDS2_SCHEMA, work, "route-2"),
        activity_id=work.work_id,
        activity_title="Routing Activity",
        artifact_instance_id="artifact-1",
        artifact_page_id="page-1",
        page_number=3,
        page_kind="response",
        artifact_category="student_work",
        human_fallback="Group Blue response page 3",
        session_id="session-1",
        session_label="Day 1",
        group_id="group-blue",
        group_label="Group Blue",
        replayed_occurrence=False,
    )


def _projection(work: ModuleWorkRef) -> ConcordRouteCandidateProjection:
    return ConcordRouteCandidateProjection(
        work=work,
        activity_title="Routing Activity",
        snapshot_revision=7,
        snapshot_sha256="b" * 64,
        candidates=(_candidate(work),),
        diagnostics=(),
    )


def test_known_activity_does_not_offer_class_or_activity_browsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    review = _review(bound_work=work)
    monkeypatch.setattr(
        menu_scan,
        "list_routing_destination_classes",
        lambda *_args, **_kwargs: pytest.fail("class browser must be skipped"),
    )
    monkeypatch.setattr(
        menu_scan,
        "list_routing_destination_activities",
        lambda *_args, **_kwargs: pytest.fail("Activity browser must be skipped"),
    )
    monkeypatch.setattr(
        menu_scan,
        "project_routing_destination_candidates",
        lambda current_review, current_work: _projection(current_work),
    )
    selected_titles: list[str] = []

    def choose(title: str, items: Any, labels: Any, *, help_text: str) -> Any:
        selected_titles.append(title)
        assert tuple(labels) == (
            "Group Blue — student work — page 3 — Group Blue response page 3",
        )
        return tuple(items)[0]

    monkeypatch.setattr(menu_scan, "select_one", choose)

    selected = menu_scan._select_routing_destination(review)

    assert selected == _candidate(work).locator
    assert selected_titles == ["Select Destination — Known Activity"]


def test_unbound_failure_navigates_class_then_activity_then_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review = _review()
    class_summary = ClassSummary(class_id="class-1", school_year="2026-2027")
    activity = ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Transformation Lab",
        status="active",
        scoring_orientation="evidence_only",
        session_count=1,
        group_count=6,
        snapshot_revision=4,
    )
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    monkeypatch.setattr(
        menu_scan,
        "list_routing_destination_classes",
        lambda current_review: (class_summary,),
    )
    monkeypatch.setattr(
        menu_scan,
        "list_routing_destination_activities",
        lambda current_review, class_id: (activity,),
    )
    monkeypatch.setattr(
        menu_scan,
        "project_routing_destination_candidates",
        lambda current_review, current_work: _projection(current_work),
    )
    selections: list[tuple[str, tuple[str, ...]]] = []

    def choose(title: str, items: Any, labels: Any, *, help_text: str) -> Any:
        selections.append((title, tuple(labels)))
        return tuple(items)[0]

    monkeypatch.setattr(menu_scan, "select_one", choose)

    selected = menu_scan._select_routing_destination(review)

    assert selected == _candidate(work).locator
    assert [title for title, _labels in selections] == [
        "Select Class",
        "Select Activity",
        "Select Destination — Transformation Lab",
    ]
    assert selections[0][1] == ("2026-2027 — class-1",)
    assert selections[1][1] == ("Transformation Lab — active",)


def test_known_activity_service_rejects_lateral_activity_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bound = ModuleWorkRef("concord", "class-1", "activity-1")
    other = ModuleWorkRef("concord", "class-1", "activity-2")
    review = _review(bound_work=bound)
    monkeypatch.setattr(
        destination_module,
        "list_activity_route_candidates",
        lambda *_args, **_kwargs: pytest.fail("candidate load must not occur"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="alternate Activities cannot be substituted",
    ):
        project_routing_destination_candidates(review, other)


def test_candidate_projection_carries_exact_failed_physical_page_occurrence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    review = _review()
    observed: dict[str, object] = {}

    def project(
        current_work: ModuleWorkRef,
        *,
        workspace_root: object = None,
        source_scan_id: str | None = None,
        source_page_number: int | None = None,
    ) -> ConcordRouteCandidateProjection:
        observed.update(
            work=current_work,
            workspace_root=workspace_root,
            source_scan_id=source_scan_id,
            source_page_number=source_page_number,
        )
        return _projection(current_work)

    monkeypatch.setattr(destination_module, "list_activity_route_candidates", project)

    result = project_routing_destination_candidates(
        review,
        work,
        workspace_root="workspace-root",
    )

    assert result.work == work
    assert observed == {
        "work": work,
        "workspace_root": "workspace-root",
        "source_scan_id": "scan_test_1",
        "source_page_number": 2,
    }


def test_bound_failure_class_list_is_empty_and_activity_browser_is_forbidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    review = _review(bound_work=work)
    monkeypatch.setattr(
        destination_module,
        "list_available_classes",
        lambda *_args, **_kwargs: pytest.fail("class listing must be skipped"),
    )
    monkeypatch.setattr(
        destination_module,
        "list_activities",
        lambda *_args, **_kwargs: pytest.fail("Activity listing must be skipped"),
    )

    assert list_routing_destination_classes(review) == ()
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="alternate Activities must not be browsed",
    ):
        list_routing_destination_activities(review, "class-1")


def test_candidate_label_keeps_exact_ids_out_of_routine_display() -> None:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    candidate = _candidate(work)

    label = routing_destination_candidate_label(candidate)

    assert label == (
        "Group Blue — student work — page 3 — Group Blue response page 3"
    )
    assert candidate.artifact_page_id not in label
    assert candidate.artifact_instance_id not in label
    assert candidate.locator.route_id not in label
