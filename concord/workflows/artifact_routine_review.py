"""Read-only routine Artifact Review projection and Quick Review eligibility."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from concord.models import (
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactReview,
    ArtifactSubject,
    EvidenceReference,
    ModerationRecord,
)
from concord.workflows._collaboration import work_ref
from concord.workflows.activity_read import (
    ActivityReadContext,
    load_activity_read_context,
)
from concord.workflows.artifact_attribution import (
    _current_authors,
    _current_subjects,
    _ensure_author_not_duplicate,
    _ensure_subject_not_duplicate,
    _require_artifact,
    _validate_author_semantics,
    _validate_subject_semantics,
)
from concord.workflows.artifact_collection import (
    ArtifactAssemblyState,
    _assembly_state,
)
from concord.workflows.artifact_review import _current_review_for_artifact
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowError,
    ConcordWorkflowNotFoundError,
)
from concord.workflows.moderation import _applicable_records


@dataclass(frozen=True, slots=True)
class ArtifactRoutineReviewEligibility:
    """Mechanical eligibility for the routine first-Review form."""

    quick_review_eligible: bool
    exception_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ArtifactRoutineReviewContext:
    """One selected Artifact projected from one exact verified Activity snapshot."""

    class_id: str
    activity_id: str
    artifact: ArtifactInstance
    current_review: ArtifactReview | None
    assembly_state: ArtifactAssemblyState
    current_authors: tuple[ArtifactAuthor, ...]
    current_subjects: tuple[ArtifactSubject, ...]
    applicable_moderation_records: tuple[ModerationRecord, ...]
    first_review_pending: bool
    eligibility: ArtifactRoutineReviewEligibility
    snapshot_revision: int
    snapshot_sha256: str


def _append_once(reasons: list[str], message: str) -> None:
    if message not in reasons:
        reasons.append(message)


def _assembly_exception_reason(state: ArtifactAssemblyState) -> str | None:
    if state == "assembled":
        return None
    if state == "not_ready":
        return "Returned evidence is incomplete; use Detailed Review when appropriate."
    if state == "selection_required":
        return (
            "Returned evidence has an unresolved occurrence selection; "
            "resolve collection before Quick Review."
        )
    if state == "needs_recovery":
        return (
            "Returned evidence assembly needs recovery before Quick Review."
        )
    if state == "ready":
        return "Returned evidence must be assembled before Quick Review."
    return "This Artifact has no reviewable returned assembly for Quick Review."


def _author_exception_reasons(
    context: ActivityReadContext,
    artifact: ArtifactInstance,
    authors: tuple[ArtifactAuthor, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not authors:
        return (
            "Attribution needs attention before Quick Review: "
            "no current Author relationship.",
        )

    for author in authors:
        if author.attribution_status != "confirmed":
            _append_once(
                reasons,
                "Attribution needs attention before Quick Review: "
                "Author attribution is not confirmed.",
            )
            continue
        try:
            _validate_author_semantics(
                context.root,
                context.work.class_id,
                context.graph,
                artifact,
                author,
            )
            _ensure_author_not_duplicate(
                context.graph,
                author,
                exclude_id=author.artifact_author_id,
            )
        except ConcordWorkflowError:
            _append_once(
                reasons,
                "Attribution needs attention before Quick Review: "
                "Author attribution is invalid or conflicting.",
            )
    return tuple(reasons)


def _subject_exception_reasons(
    context: ActivityReadContext,
    artifact: ArtifactInstance,
    subjects: tuple[ArtifactSubject, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not subjects:
        return (
            "Attribution needs attention before Quick Review: "
            "no current Subject relationship.",
        )

    for subject in subjects:
        if subject.confirmation_status != "confirmed":
            _append_once(
                reasons,
                "Attribution needs attention before Quick Review: "
                "Subject attribution is not confirmed.",
            )
            continue
        try:
            _validate_subject_semantics(
                context.root,
                context.work.class_id,
                context.graph,
                artifact,
                subject,
            )
            _ensure_subject_not_duplicate(
                context.graph,
                subject,
                exclude_id=subject.artifact_subject_id,
            )
        except ConcordWorkflowError:
            _append_once(
                reasons,
                "Attribution needs attention before Quick Review: "
                "Subject attribution is invalid or conflicting.",
            )
    return tuple(reasons)


def _project_artifact_routine_review_from_context(
    context: ActivityReadContext,
    artifact_instance_id: str,
) -> ArtifactRoutineReviewContext:
    """Project one Artifact without reloading the verified Activity graph."""
    artifact = _require_artifact(
        context.graph,
        context.work.work_id,
        artifact_instance_id,
    )
    current_review = _current_review_for_artifact(
        context.graph,
        artifact.artifact_instance_id,
    )
    assembly_state = _assembly_state(
        context.root,
        context.work.class_id,
        context.work.work_id,
        artifact,
        context.graph,
    )
    current_authors = tuple(
        item
        for item in _current_authors(context.graph)
        if item.artifact_instance_id == artifact.artifact_instance_id
    )
    current_subjects = tuple(
        item
        for item in _current_subjects(context.graph)
        if item.artifact_instance_id == artifact.artifact_instance_id
    )

    evidence_reference = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id=artifact.artifact_instance_id,
    )
    subject_context = tuple(
        item.subject_reference for item in current_subjects
    )
    applicable_moderation_records = _applicable_records(
        context.graph,
        evidence_reference,
        subject_context,
    )

    reasons: list[str] = []
    assembly_reason = _assembly_exception_reason(assembly_state)
    if assembly_reason is not None:
        reasons.append(assembly_reason)
    if current_review is not None:
        reasons.append(
            "A current Review already exists; use the successor/correction workflow."
        )
    reasons.extend(
        _author_exception_reasons(
            context,
            artifact,
            current_authors,
        )
    )
    reasons.extend(
        _subject_exception_reasons(
            context,
            artifact,
            current_subjects,
        )
    )
    if applicable_moderation_records:
        reasons.append(
            "Current Moderation state requires Detailed Review."
        )

    first_review_pending = (
        current_review is None and assembly_state == "assembled"
    )
    eligibility = ArtifactRoutineReviewEligibility(
        quick_review_eligible=first_review_pending and not reasons,
        exception_reasons=tuple(reasons),
    )
    return ArtifactRoutineReviewContext(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        artifact=artifact,
        current_review=current_review,
        assembly_state=assembly_state,
        current_authors=current_authors,
        current_subjects=current_subjects,
        applicable_moderation_records=applicable_moderation_records,
        first_review_pending=first_review_pending,
        eligibility=eligibility,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
    )


def inspect_artifact_routine_review(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactRoutineReviewContext:
    """Inspect routine Review eligibility from one exact current Activity state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    require_core_class(root, class_id)
    context = load_activity_read_context(
        root,
        work_ref(class_id, activity_id),
    )
    return _project_artifact_routine_review_from_context(
        context,
        artifact_instance_id,
    )


__all__ = [
    "ArtifactRoutineReviewContext",
    "ArtifactRoutineReviewEligibility",
    "inspect_artifact_routine_review",
]
