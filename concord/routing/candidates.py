"""Read-only teacher-selectable Concord route candidates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from pds_core.route_registrations import (
    RouteRegistrationPersistenceError,
    load_route_registration,
)
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator

from concord.models import (
    ActorReference,
    ArtifactAuthor,
    ArtifactSubject,
    ConcordRecordReference,
    ParticipantReference,
    SubjectReference,
)
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
from concord.workflows.participants import participant_display_label


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
    packet_target_kind: str | None = None
    packet_target_label: str | None = None
    author_labels: tuple[str, ...] = ()
    subject_labels: tuple[str, ...] = ()


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


def _qualified_relationship_label(
    label: str,
    status: str,
    *,
    confirmed_status: str,
) -> str:
    if status == confirmed_status:
        return label
    return f"{label} ({status.replace('_', ' ')})"


def _participant_label(
    context: ActivityReadContext,
    reference: ParticipantReference,
) -> str | None:
    return participant_display_label(
        context.root,
        context.work.class_id,
        reference,
    )


def _author_reference_label(
    context: ActivityReadContext,
    author: ArtifactAuthor,
    *,
    groups: Mapping[str, object],
    sessions: Mapping[str, object],
    activities: Mapping[str, object],
) -> str | None:
    reference = author.author_reference
    if reference is None:
        return None
    if isinstance(reference, ParticipantReference):
        return _participant_label(context, reference)
    if isinstance(reference, ActorReference):
        return reference.display_label_snapshot
    if isinstance(reference, ConcordRecordReference):
        if reference.record_kind == "group":
            value = groups.get(reference.record_id)
            return (
                None
                if value is None
                else str(getattr(value, "label", "") or "") or None
            )
        if reference.record_kind == "session":
            value = sessions.get(reference.record_id)
            if value is None:
                return None
            return str(getattr(value, "label", "") or "") or None
        if reference.record_kind == "activity":
            value = activities.get(reference.record_id)
            return (
                None
                if value is None
                else str(getattr(value, "title", "") or "") or None
            )
    return None


def _subject_reference_label(
    context: ActivityReadContext,
    reference: SubjectReference,
    *,
    groups: Mapping[str, object],
    sessions: Mapping[str, object],
    activities: Mapping[str, object],
) -> str | None:
    if (
        reference.subject_kind == "core_student"
        and reference.owning_system == "core"
    ):
        return _participant_label(
            context,
            ParticipantReference(
                participant_kind="core_student",
                participant_id=reference.subject_id,
                owning_system="core",
            ),
        )
    if reference.subject_kind == "concord_group":
        value = groups.get(reference.subject_id)
        return (
            None
            if value is None
            else str(getattr(value, "label", "") or "") or None
        )
    if reference.subject_kind == "concord_session":
        value = sessions.get(reference.subject_id)
        if value is None:
            return None
        return str(getattr(value, "label", "") or "") or None
    if reference.subject_kind == "concord_activity":
        value = activities.get(reference.subject_id)
        return (
            None
            if value is None
            else str(getattr(value, "title", "") or "") or None
        )
    return None


def _packet_target_context(
    context: ActivityReadContext,
    packet: object,
    *,
    groups: Mapping[str, object],
    activities: Mapping[str, object],
) -> tuple[str | None, str | None]:
    target = getattr(packet, "target_context", None)
    if target is None:
        return None, None
    kind = str(getattr(target, "audience_kind", ""))
    if kind == "participant":
        reference = getattr(target, "participant_reference", None)
        if isinstance(reference, ParticipantReference):
            return kind, _participant_label(context, reference)
    elif kind == "group":
        group_id = getattr(target, "group_id", None)
        value = groups.get(group_id) if isinstance(group_id, str) else None
        return (
            kind,
            None
            if value is None
            else str(getattr(value, "label", "") or "") or None,
        )
    elif kind == "teacher":
        reference = getattr(target, "actor_reference", None)
        if isinstance(reference, ActorReference):
            return kind, reference.display_label_snapshot
    elif kind == "activity":
        activity_id = getattr(target, "activity_id", None)
        value = activities.get(activity_id) if isinstance(activity_id, str) else None
        return (
            kind,
            None
            if value is None
            else str(getattr(value, "title", "") or "") or None,
        )
    elif kind == "role":
        role_key = getattr(target, "role_key", None)
        if isinstance(role_key, str):
            return kind, role_key.replace("_", " ")
    return (kind or None), None


def _candidate_sort_key(
    candidate: ConcordRouteCandidate,
) -> tuple[
    str,
    tuple[str, ...],
    tuple[str, ...],
    str,
    str,
    str,
    str,
    int,
    str,
    str,
]:
    return (
        candidate.packet_target_label.casefold()
        if candidate.packet_target_label
        else "",
        tuple(item.casefold() for item in candidate.subject_labels),
        tuple(item.casefold() for item in candidate.author_labels),
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
    activities = {item.activity_id: item for item in context.graph.activities}
    packets = {
        item.packet_instance_id: item for item in context.graph.packet_instances
    }

    superseded_author_ids = {
        item.supersedes_artifact_author_id
        for item in context.graph.artifact_authors
        if item.supersedes_artifact_author_id is not None
    }
    authors_by_artifact: dict[str, list[ArtifactAuthor]] = {}
    for author in context.graph.artifact_authors:
        if (
            author.artifact_author_id in superseded_author_ids
            or author.attribution_status == "superseded"
        ):
            continue
        authors_by_artifact.setdefault(author.artifact_instance_id, []).append(author)

    superseded_subject_ids = {
        item.supersedes_artifact_subject_id
        for item in context.graph.artifact_subjects
        if item.supersedes_artifact_subject_id is not None
    }
    subjects_by_artifact: dict[str, list[ArtifactSubject]] = {}
    for subject in context.graph.artifact_subjects:
        if (
            subject.artifact_subject_id in superseded_subject_ids
            or subject.confirmation_status == "superseded"
        ):
            continue
        subjects_by_artifact.setdefault(subject.artifact_instance_id, []).append(
            subject
        )

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

        author_labels: list[str] = []
        for author in authors_by_artifact.get(artifact.artifact_instance_id, []):
            label = _author_reference_label(
                context,
                author,
                groups=groups,
                sessions=sessions,
                activities=activities,
            )
            if label is not None:
                author_labels.append(
                    _qualified_relationship_label(
                        label,
                        author.attribution_status,
                        confirmed_status="confirmed",
                    )
                )

        subject_labels: list[str] = []
        for subject in subjects_by_artifact.get(artifact.artifact_instance_id, []):
            label = _subject_reference_label(
                context,
                subject.subject_reference,
                groups=groups,
                sessions=sessions,
                activities=activities,
            )
            if label is not None:
                subject_labels.append(
                    _qualified_relationship_label(
                        label,
                        subject.confirmation_status,
                        confirmed_status="confirmed",
                    )
                )

        packet_target_kind: str | None = None
        packet_target_label: str | None = None
        if artifact.packet_instance_id is not None:
            packet = packets.get(artifact.packet_instance_id)
            if packet is not None and any(
                binding.artifact_instance_id == artifact.artifact_instance_id
                for binding in packet.artifact_bindings
            ):
                packet_target_kind, packet_target_label = _packet_target_context(
                    context,
                    packet,
                    groups=groups,
                    activities=activities,
                )

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
                packet_target_kind=packet_target_kind,
                packet_target_label=packet_target_label,
                author_labels=tuple(sorted(set(author_labels), key=str.casefold)),
                subject_labels=tuple(sorted(set(subject_labels), key=str.casefold)),
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
