"""Read-only teacher-selectable Concord route candidates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.route_registrations import (
    RouteRegistrationPersistenceError,
    load_route_registration,
)
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator

from concord.workflows.activity_read import (
    ActivityReadContext,
    load_activity_read_context,
)
from concord.workflows.artifact_page import validate_concord_route_target
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowError,
    ConcordWorkflowNotFoundError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRouteCandidate:
    """One current Concord Artifact Page bound to its exact immutable route."""

    locator: RouteLocator
    activity_id: str
    activity_title: str
    artifact_instance_id: str
    artifact_page_id: str
    page_number: int
    page_kind: str
    artifact_category: str
    human_fallback: str
    session_id: str | None
    session_label: str | None
    group_id: str | None
    group_label: str | None
    replayed_occurrence: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRouteCandidateDiagnostic:
    """Bounded technical detail for one page that cannot be offered."""

    artifact_page_id: str
    route_id: str
    reason: str
    detail: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRouteCandidateProjection:
    """Selectable destinations plus bounded integrity diagnostics."""

    work: ModuleWorkRef
    activity_title: str
    snapshot_revision: int
    snapshot_sha256: str
    candidates: tuple[ConcordRouteCandidate, ...]
    diagnostics: tuple[ConcordRouteCandidateDiagnostic, ...]


def _candidate_sort_key(
    candidate: ConcordRouteCandidate,
) -> tuple[str, str, str, str, int, str, str]:
    return (
        candidate.group_label.casefold() if candidate.group_label else "",
        candidate.session_label.casefold() if candidate.session_label else "",
        candidate.artifact_category.casefold(),
        candidate.artifact_instance_id,
        candidate.page_number,
        candidate.artifact_page_id,
        candidate.locator.route_id,
    )


def project_activity_route_candidates(
    context: ActivityReadContext,
    *,
    source_scan_id: str | None = None,
    source_page_number: int | None = None,
) -> ConcordRouteCandidateProjection:
    """Project exact selectable routes from one already-loaded Activity graph."""
    if (source_scan_id is None) != (source_page_number is None):
        raise ValueError(
            "source_scan_id and source_page_number must be supplied together."
        )

    artifacts = {
        item.artifact_instance_id: item for item in context.graph.artifact_instances
    }
    sessions = {item.session_id: item for item in context.graph.sessions}
    groups = {item.group_id: item for item in context.graph.groups}
    candidates: list[ConcordRouteCandidate] = []
    diagnostics: list[ConcordRouteCandidateDiagnostic] = []

    for page in sorted(
        context.graph.artifact_pages,
        key=lambda item: (
            item.artifact_instance_id,
            item.page_number,
            item.artifact_page_id,
        ),
    ):
        if not page.route_required:
            continue
        if page.route_id is None or page.human_fallback is None:
            # Current models prohibit this state. Keep the projection fail-closed
            # for historical/corrupt state rather than synthesizing route identity.
            diagnostics.append(
                ConcordRouteCandidateDiagnostic(
                    artifact_page_id=page.artifact_page_id,
                    route_id=page.route_id or "unavailable",
                    reason="page_route_identity_incomplete",
                    detail="Current Artifact Page route identity is incomplete.",
                )
            )
            continue

        artifact = artifacts.get(page.artifact_instance_id)
        if artifact is None:
            diagnostics.append(
                ConcordRouteCandidateDiagnostic(
                    artifact_page_id=page.artifact_page_id,
                    route_id=page.route_id,
                    reason="artifact_unavailable",
                    detail="Current ArtifactInstance is unavailable.",
                )
            )
            continue

        locator = RouteLocator(PDS2_SCHEMA, context.work, page.route_id)
        try:
            registration = load_route_registration(context.root, locator)
            target = validate_concord_route_target(
                context.graph,
                context.work,
                registration,
                source_scan_id=source_scan_id,
                source_page_number=source_page_number,
            )
            if target.page.artifact_page_id != page.artifact_page_id:
                raise ValueError(
                    "registered target does not match the candidate Artifact Page."
                )
        except RouteRegistrationPersistenceError as error:
            diagnostics.append(
                ConcordRouteCandidateDiagnostic(
                    artifact_page_id=page.artifact_page_id,
                    route_id=page.route_id,
                    reason="route_registration_unavailable",
                    detail=str(error),
                )
            )
            continue
        except (ConcordWorkflowError, ValueError) as error:
            diagnostics.append(
                ConcordRouteCandidateDiagnostic(
                    artifact_page_id=page.artifact_page_id,
                    route_id=page.route_id,
                    reason="route_inconsistent_or_ineligible",
                    detail=str(error),
                )
            )
            continue

        session = sessions.get(artifact.session_id) if artifact.session_id else None
        group = groups.get(artifact.group_id) if artifact.group_id else None
        candidates.append(
            ConcordRouteCandidate(
                locator=registration.locator,
                activity_id=context.activity.activity_id,
                activity_title=context.activity.title,
                artifact_instance_id=artifact.artifact_instance_id,
                artifact_page_id=page.artifact_page_id,
                page_number=page.page_number,
                page_kind=page.page_kind,
                artifact_category=artifact.artifact_category,
                human_fallback=page.human_fallback,
                session_id=artifact.session_id,
                session_label=None if session is None else session.label,
                group_id=artifact.group_id,
                group_label=None if group is None else group.label,
                replayed_occurrence=target.replay_scan_reference is not None,
            )
        )

    return ConcordRouteCandidateProjection(
        work=context.work,
        activity_title=context.activity.title,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        candidates=tuple(sorted(candidates, key=_candidate_sort_key)),
        diagnostics=tuple(diagnostics),
    )


def list_activity_route_candidates(
    work: ModuleWorkRef,
    *,
    workspace_root: str | Path | None = None,
    source_scan_id: str | None = None,
    source_page_number: int | None = None,
) -> ConcordRouteCandidateProjection:
    """Load one exact Activity graph and project its selectable routes."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("workspace is unavailable.")
    context = load_activity_read_context(root, work)
    return project_activity_route_candidates(
        context,
        source_scan_id=source_scan_id,
        source_page_number=source_page_number,
    )


__all__ = [
    "ConcordRouteCandidate",
    "ConcordRouteCandidateDiagnostic",
    "ConcordRouteCandidateProjection",
    "list_activity_route_candidates",
    "project_activity_route_candidates",
]
