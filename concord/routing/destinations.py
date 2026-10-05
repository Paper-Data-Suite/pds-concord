"""Read-only routing-review destination discovery and display projection."""

from __future__ import annotations

from pathlib import Path

from pds_core.routing_models import ModuleWorkRef

from concord.routing.candidates import (
    ConcordRouteCandidate,
    ConcordRouteCandidateProjection,
    list_activity_route_candidates,
)
from concord.routing.review import RoutingFailureReview
from concord.workflows.activity import list_activities
from concord.workflows.context import list_available_classes
from concord.workflows.errors import ConcordWorkflowValidationError
from concord.workflows.models import ActivitySummary, ClassSummary


def _require_route_choice(review: RoutingFailureReview) -> tuple[str, int]:
    if not review.route_action_available:
        detail = review.route_action_unavailable_detail or (
            "Route correction is not available for this routing failure."
        )
        raise ConcordWorkflowValidationError(detail)
    source_scan_id = review.failure.source_scan_id
    source_page_number = review.failure.source_page_number
    if source_scan_id is None or source_page_number is None:
        raise ConcordWorkflowValidationError(
            "Retained physical-page identity is unavailable for route selection."
        )
    return source_scan_id, source_page_number


def list_routing_destination_classes(
    review: RoutingFailureReview,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[ClassSummary, ...]:
    """List selectable Core classes only for an unbound routing failure."""
    _require_route_choice(review)
    if review.bound_work is not None:
        return ()
    return list_available_classes(workspace_root)


def list_routing_destination_activities(
    review: RoutingFailureReview,
    class_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[ActivitySummary, ...]:
    """List selectable Concord Activities for an unbound failure and one class."""
    _require_route_choice(review)
    if review.bound_work is not None:
        raise ConcordWorkflowValidationError(
            "This failure is already bound to a Concord Activity; alternate "
            "Activities must not be browsed."
        )
    return list_activities(workspace_root=workspace_root, class_id=class_id)


def project_routing_destination_candidates(
    review: RoutingFailureReview,
    work: ModuleWorkRef,
    *,
    workspace_root: str | Path | None = None,
) -> ConcordRouteCandidateProjection:
    """Project exact current Artifact Page routes for one allowed Activity work."""
    source_scan_id, source_page_number = _require_route_choice(review)
    if work.module_id != "concord":
        raise ConcordWorkflowValidationError(
            "Routing Review can select only Concord destination pages."
        )
    if review.bound_work is not None and work != review.bound_work:
        raise ConcordWorkflowValidationError(
            "The failed Concord route is bound to another Activity; alternate "
            "Activities cannot be substituted."
        )
    return list_activity_route_candidates(
        work,
        workspace_root=workspace_root,
        source_scan_id=source_scan_id,
        source_page_number=source_page_number,
    )


def routing_destination_class_label(summary: ClassSummary) -> str:
    """Return the least-technical available class label from Core metadata."""
    return f"{summary.school_year} — {summary.class_id}"


def routing_destination_activity_label(summary: ActivitySummary) -> str:
    """Return a teacher-readable Activity label without exposing work identity."""
    return f"{summary.title} — {summary.status.replace('_', ' ')}"


def routing_destination_candidate_label(candidate: ConcordRouteCandidate) -> str:
    """Return a teacher-readable page label; fallback text remains display-only."""
    parts: list[str] = []
    if candidate.group_label:
        parts.append(candidate.group_label)
    elif candidate.session_label:
        parts.append(candidate.session_label)
    parts.extend(
        (
            candidate.artifact_category.replace("_", " "),
            f"page {candidate.page_number}",
            candidate.human_fallback,
        )
    )
    if candidate.replayed_occurrence:
        parts.append("already filed from this scan page")
    return " — ".join(parts)


__all__ = [
    "list_routing_destination_activities",
    "list_routing_destination_classes",
    "project_routing_destination_candidates",
    "routing_destination_activity_label",
    "routing_destination_candidate_label",
    "routing_destination_class_label",
]
