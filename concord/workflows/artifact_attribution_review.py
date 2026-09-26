"""Read-only Artifact Author/Subject review projection for routine confirmation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactAuthor, ArtifactSubject
from concord.workflows._collaboration import work_ref
from concord.workflows.activity_read import load_activity_read_context
from concord.workflows.artifact_attribution import (
    _author_display_label,
    _current_authors,
    _current_subjects,
    _ensure_author_not_duplicate,
    _ensure_subject_not_duplicate,
    _require_artifact,
    _subject_display_label,
    _validate_author_semantics,
    _validate_subject_semantics,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowError,
    ConcordWorkflowNotFoundError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactAuthorReviewItem:
    artifact_author_id: str
    reference_display_label: str | None
    authorship_mode: str
    attribution_status: str
    represented_group_id: str | None
    role_assignment_id: str | None
    representation_status: str | None
    disposition: str
    exception_code: str | None = None
    exception_message: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactSubjectReviewItem:
    artifact_subject_id: str
    reference_display_label: str | None
    subject_role: str
    confirmation_status: str
    criterion_id: str | None
    disposition: str
    exception_code: str | None = None
    exception_message: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactAttributionReviewGroup:
    artifact_instance_id: str
    template_version_id: str
    artifact_category: str
    group_id: str | None
    session_id: str | None
    authors: tuple[ArtifactAuthorReviewItem, ...]
    subjects: tuple[ArtifactSubjectReviewItem, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactAttributionReview:
    class_id: str
    activity_id: str
    snapshot_revision: int
    snapshot_sha256: str
    artifacts: tuple[ArtifactAttributionReviewGroup, ...]
    candidate_author_ids: tuple[str, ...]
    candidate_subject_ids: tuple[str, ...]
    confirmed_author_count: int
    confirmed_subject_count: int

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_author_ids) + len(self.candidate_subject_ids)

    @property
    def exception_count(self) -> int:
        count = 0
        for group in self.artifacts:
            for author in group.authors:
                if author.disposition == "exception":
                    count += 1
            for subject in group.subjects:
                if subject.disposition == "exception":
                    count += 1
        return count

    @property
    def confirmed_relationship_count(self) -> int:
        return self.confirmed_author_count + self.confirmed_subject_count


def _author_review_item(
    root: Path,
    class_id: str,
    activity_id: str,
    graph: ConcordRecordGraph,
    author: ArtifactAuthor,
) -> ArtifactAuthorReviewItem:
    artifact_author = author
    record_graph = graph
    artifact = _require_artifact(
        record_graph,
        activity_id,
        artifact_author.artifact_instance_id,
    )
    display_label = _author_display_label(
        root,
        class_id,
        record_graph,
        artifact_author,
    )
    disposition = "exception"
    exception_code: str | None
    exception_message: str | None

    if artifact_author.attribution_status == "proposed":
        candidate = replace(
            artifact_author,
            attribution_status="confirmed",
        )
        try:
            _validate_author_semantics(
                root,
                class_id,
                record_graph,
                artifact,
                candidate,
            )
            _ensure_author_not_duplicate(
                record_graph,
                candidate,
                exclude_id=artifact_author.artifact_author_id,
            )
        except ConcordWorkflowConflictError as error:
            exception_code = "conflicting_equivalent"
            exception_message = str(error)
        except ConcordWorkflowError as error:
            exception_code = "semantic_invalid"
            exception_message = str(error)
        else:
            disposition = "candidate"
            exception_code = None
            exception_message = None
    else:
        exception_code = artifact_author.attribution_status
        exception_message = (
            "This current Artifact Author requires individual attribution review."
        )

    return ArtifactAuthorReviewItem(
        artifact_author_id=artifact_author.artifact_author_id,
        reference_display_label=display_label,
        authorship_mode=artifact_author.authorship_mode,
        attribution_status=artifact_author.attribution_status,
        represented_group_id=artifact_author.represented_group_id,
        role_assignment_id=artifact_author.role_assignment_id,
        representation_status=artifact_author.representation_status,
        disposition=disposition,
        exception_code=exception_code,
        exception_message=exception_message,
    )


def _subject_review_item(
    root: Path,
    class_id: str,
    activity_id: str,
    graph: ConcordRecordGraph,
    subject: ArtifactSubject,
) -> ArtifactSubjectReviewItem:
    artifact_subject = subject
    record_graph = graph
    artifact = _require_artifact(
        record_graph,
        activity_id,
        artifact_subject.artifact_instance_id,
    )
    display_label = _subject_display_label(
        root,
        class_id,
        record_graph,
        artifact_subject.subject_reference,
    )
    disposition = "exception"
    exception_code: str | None
    exception_message: str | None

    if artifact_subject.confirmation_status == "proposed":
        candidate = replace(
            artifact_subject,
            confirmation_status="confirmed",
        )
        try:
            _validate_subject_semantics(
                root,
                class_id,
                record_graph,
                artifact,
                candidate,
            )
            _ensure_subject_not_duplicate(
                record_graph,
                candidate,
                exclude_id=artifact_subject.artifact_subject_id,
            )
        except ConcordWorkflowConflictError as error:
            exception_code = "conflicting_equivalent"
            exception_message = str(error)
        except ConcordWorkflowError as error:
            exception_code = "semantic_invalid"
            exception_message = str(error)
        else:
            disposition = "candidate"
            exception_code = None
            exception_message = None
    else:
        exception_code = artifact_subject.confirmation_status
        exception_message = (
            "This current Artifact Subject requires individual attribution review."
        )

    return ArtifactSubjectReviewItem(
        artifact_subject_id=artifact_subject.artifact_subject_id,
        reference_display_label=display_label,
        subject_role=artifact_subject.subject_role,
        confirmation_status=artifact_subject.confirmation_status,
        criterion_id=artifact_subject.criterion_id,
        disposition=disposition,
        exception_code=exception_code,
        exception_message=exception_message,
    )


def inspect_artifact_attribution_review(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactAttributionReview:
    """Project routine attribution attention from one exact current Activity state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Workspace is not available.")
    require_core_class(root, class_id)

    context = load_activity_read_context(root, work_ref(class_id, activity_id))
    graph = context.graph

    current_authors = _current_authors(graph)
    current_subjects = _current_subjects(graph)
    confirmed_author_count = sum(
        item.attribution_status == "confirmed" for item in current_authors
    )
    confirmed_subject_count = sum(
        item.confirmation_status == "confirmed" for item in current_subjects
    )

    author_items: dict[str, list[ArtifactAuthorReviewItem]] = {}
    for author in sorted(
        current_authors,
        key=lambda item: (item.artifact_instance_id, item.artifact_author_id),
    ):
        if author.attribution_status == "confirmed":
            continue
        author_items.setdefault(author.artifact_instance_id, []).append(
            _author_review_item(
                root,
                class_id,
                activity_id,
                graph,
                author,
            )
        )

    subject_items: dict[str, list[ArtifactSubjectReviewItem]] = {}
    for subject in sorted(
        current_subjects,
        key=lambda item: (item.artifact_instance_id, item.artifact_subject_id),
    ):
        if subject.confirmation_status == "confirmed":
            continue
        subject_items.setdefault(subject.artifact_instance_id, []).append(
            _subject_review_item(
                root,
                class_id,
                activity_id,
                graph,
                subject,
            )
        )

    active_artifact_ids = sorted(set(author_items) | set(subject_items))
    artifacts_by_id = {
        item.artifact_instance_id: item for item in graph.artifact_instances
    }
    groups: list[ArtifactAttributionReviewGroup] = []
    for artifact_instance_id in active_artifact_ids:
        artifact = artifacts_by_id[artifact_instance_id]
        groups.append(
            ArtifactAttributionReviewGroup(
                artifact_instance_id=artifact.artifact_instance_id,
                template_version_id=artifact.template_version_id,
                artifact_category=artifact.artifact_category,
                group_id=artifact.group_id,
                session_id=artifact.session_id,
                authors=tuple(author_items.get(artifact_instance_id, ())),
                subjects=tuple(subject_items.get(artifact_instance_id, ())),
            )
        )

    candidate_author_ids = tuple(
        item.artifact_author_id
        for group in groups
        for item in group.authors
        if item.disposition == "candidate"
    )
    candidate_subject_ids = tuple(
        item.artifact_subject_id
        for group in groups
        for item in group.subjects
        if item.disposition == "candidate"
    )
    return ArtifactAttributionReview(
        class_id=class_id,
        activity_id=activity_id,
        snapshot_revision=context.snapshot_revision,
        snapshot_sha256=context.snapshot_sha256,
        artifacts=tuple(groups),
        candidate_author_ids=candidate_author_ids,
        candidate_subject_ids=candidate_subject_ids,
        confirmed_author_count=confirmed_author_count,
        confirmed_subject_count=confirmed_subject_count,
    )


__all__ = [
    "ArtifactAttributionReview",
    "ArtifactAttributionReviewGroup",
    "ArtifactAuthorReviewItem",
    "ArtifactSubjectReviewItem",
    "inspect_artifact_attribution_review",
]
