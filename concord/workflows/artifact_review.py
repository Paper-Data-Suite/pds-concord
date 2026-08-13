"""Teacher-controlled Artifact Review application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ArtifactInstance,
    ArtifactReview,
    ConcordRecordReference,
    CorrectionRecord,
    PrivacyPolicy,
)
from concord.storage import commit_record_batch
from concord.workflows._collaboration import load_graph, require_new_identity, work_ref
from concord.workflows.context import (
    Clock,
    actor_reference,
    ensure_mutating_workspace_root,
    require_core_class,
    resolve_read_workspace_root,
    workflow_timestamp,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult


@dataclass(frozen=True, slots=True, kw_only=True)
class AddArtifactReviewRequest:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_review_id: str
    readability_judgment: str
    page_completeness_judgment: str
    filing_judgment: str
    author_judgment: str
    subject_judgment: str
    privacy_judgment: str
    relevance_judgment: str
    moderation_requirement: str
    scoring_readiness: str
    review_outcome: str
    privacy_policy: PrivacyPolicy
    expected_snapshot_revision: int
    actor: WorkflowActor
    notes: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceArtifactReviewRequest:
    class_id: str
    activity_id: str
    artifact_review_id: str
    replacement_artifact_review_id: str
    correction_id: str
    reason: str
    readability_judgment: str
    page_completeness_judgment: str
    filing_judgment: str
    author_judgment: str
    subject_judgment: str
    privacy_judgment: str
    relevance_judgment: str
    moderation_requirement: str
    scoring_readiness: str
    review_outcome: str
    privacy_policy: PrivacyPolicy
    expected_snapshot_revision: int
    actor: WorkflowActor
    notes: str | None = None
    correction_privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactReviewMutationResult:
    commit: WorkflowCommitResult
    artifact_review_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactReviewSummary:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_review_id: str
    reviewer_display_label: str | None
    reviewed_at: str
    readability_judgment: str
    page_completeness_judgment: str
    filing_judgment: str
    author_judgment: str
    subject_judgment: str
    privacy_judgment: str
    relevance_judgment: str
    moderation_requirement: str
    scoring_readiness: str
    review_outcome: str
    notes: str | None
    privacy_policy: PrivacyPolicy
    supersedes_artifact_review_id: str | None
    is_current: bool
    snapshot_revision: int


def _require_artifact(
    graph: ConcordRecordGraph,
    activity_id: str,
    artifact_instance_id: str,
) -> ArtifactInstance:
    artifact = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == artifact_instance_id
        ),
        None,
    )
    if artifact is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    if artifact.activity_id != activity_id:
        raise ConcordWorkflowValidationError(
            "Artifact belongs to a different Activity."
        )
    return artifact


def _review_heads(graph: ConcordRecordGraph) -> tuple[ArtifactReview, ...]:
    superseded = {
        item.supersedes_artifact_review_id
        for item in graph.artifact_reviews
        if item.supersedes_artifact_review_id is not None
    }
    return tuple(
        item
        for item in graph.artifact_reviews
        if item.artifact_review_id not in superseded
    )


def _current_review_for_artifact(
    graph: ConcordRecordGraph,
    artifact_instance_id: str,
) -> ArtifactReview | None:
    heads = tuple(
        item
        for item in _review_heads(graph)
        if item.artifact_instance_id == artifact_instance_id
    )
    if len(heads) > 1:
        raise ConcordWorkflowConflictError(
            "Artifact has competing current Review heads."
        )
    return None if not heads else heads[0]


def _require_review(
    graph: ConcordRecordGraph,
    artifact_review_id: str,
) -> ArtifactReview:
    review = next(
        (
            item
            for item in graph.artifact_reviews
            if item.artifact_review_id == artifact_review_id
        ),
        None,
    )
    if review is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Review is not available: {artifact_review_id}"
        )
    return review


def _summary(
    class_id: str,
    activity_id: str,
    review: ArtifactReview,
    current_ids: frozenset[str],
    snapshot_revision: int,
) -> ArtifactReviewSummary:
    return ArtifactReviewSummary(
        class_id=class_id,
        activity_id=activity_id,
        artifact_instance_id=review.artifact_instance_id,
        artifact_review_id=review.artifact_review_id,
        reviewer_display_label=review.reviewer.display_label_snapshot,
        reviewed_at=review.reviewed_at,
        readability_judgment=review.readability_judgment,
        page_completeness_judgment=review.page_completeness_judgment,
        filing_judgment=review.filing_judgment,
        author_judgment=review.author_judgment,
        subject_judgment=review.subject_judgment,
        privacy_judgment=review.privacy_judgment,
        relevance_judgment=review.relevance_judgment,
        moderation_requirement=review.moderation_requirement,
        scoring_readiness=review.scoring_readiness,
        review_outcome=review.review_outcome,
        notes=review.notes,
        privacy_policy=review.privacy_policy,
        supersedes_artifact_review_id=review.supersedes_artifact_review_id,
        is_current=review.artifact_review_id in current_ids,
        snapshot_revision=snapshot_revision,
    )


def _build_review(
    request: AddArtifactReviewRequest | ReplaceArtifactReviewRequest,
    *,
    artifact_instance_id: str,
    artifact_review_id: str,
    supersedes_artifact_review_id: str | None,
    clock: Clock | None,
) -> ArtifactReview:
    return ArtifactReview(
        artifact_review_id=artifact_review_id,
        artifact_instance_id=artifact_instance_id,
        reviewer=actor_reference(request.actor),
        reviewed_at=workflow_timestamp(clock),
        readability_judgment=request.readability_judgment,
        page_completeness_judgment=request.page_completeness_judgment,
        filing_judgment=request.filing_judgment,
        author_judgment=request.author_judgment,
        subject_judgment=request.subject_judgment,
        privacy_judgment=request.privacy_judgment,
        relevance_judgment=request.relevance_judgment,
        moderation_requirement=request.moderation_requirement,
        scoring_readiness=request.scoring_readiness,
        review_outcome=request.review_outcome,
        notes=request.notes,
        privacy_policy=request.privacy_policy,
        supersedes_artifact_review_id=supersedes_artifact_review_id,
    )


def add_artifact_review(
    request: AddArtifactReviewRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactReviewMutationResult:
    """Record the first/current administrative Review for one Artifact."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        request.artifact_instance_id,
    )
    if _current_review_for_artifact(graph, artifact.artifact_instance_id) is not None:
        raise ConcordWorkflowConflictError(
            "Artifact already has a current Review; use Review replacement."
        )
    require_new_identity(
        graph.artifact_reviews,
        "artifact_review_id",
        request.artifact_review_id,
        "Artifact Review",
    )
    review = _build_review(
        request,
        artifact_instance_id=artifact.artifact_instance_id,
        artifact_review_id=request.artifact_review_id,
        supersedes_artifact_review_id=None,
        clock=clock,
    )
    result = commit_record_batch(
        root,
        work,
        (review,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactReviewMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        artifact_review_id=review.artifact_review_id,
    )


def replace_artifact_review(
    request: ReplaceArtifactReviewRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactReviewMutationResult:
    """Record a successor Review and its correction audit atomically."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    predecessor = _require_review(graph, request.artifact_review_id)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        predecessor.artifact_instance_id,
    )
    current = _current_review_for_artifact(graph, artifact.artifact_instance_id)
    if current is None or current.artifact_review_id != predecessor.artifact_review_id:
        raise ConcordWorkflowConflictError(
            "Historical Artifact Reviews cannot be replaced as the current head."
        )
    require_new_identity(
        graph.artifact_reviews,
        "artifact_review_id",
        request.replacement_artifact_review_id,
        "Artifact Review",
    )
    require_new_identity(
        graph.correction_records,
        "correction_id",
        request.correction_id,
        "Correction",
    )
    successor = _build_review(
        request,
        artifact_instance_id=artifact.artifact_instance_id,
        artifact_review_id=request.replacement_artifact_review_id,
        supersedes_artifact_review_id=predecessor.artifact_review_id,
        clock=clock,
    )
    correction = CorrectionRecord(
        correction_id=request.correction_id,
        target_reference=ConcordRecordReference(
            record_kind="artifact_review",
            record_id=predecessor.artifact_review_id,
        ),
        correction_type="review_correction",
        reason=request.reason,
        correcting_actor=actor_reference(request.actor),
        corrected_at=workflow_timestamp(clock),
        privacy_policy=request.correction_privacy_policy or successor.privacy_policy,
        replacement_reference=ConcordRecordReference(
            record_kind="artifact_review",
            record_id=successor.artifact_review_id,
        ),
    )
    result = commit_record_batch(
        root,
        work,
        (successor, correction),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactReviewMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        artifact_review_id=successor.artifact_review_id,
    )


def list_artifact_reviews(
    class_id: str,
    activity_id: str,
    *,
    artifact_instance_id: str | None = None,
    include_historical: bool = True,
    workspace_root: str | Path | None = None,
) -> tuple[ArtifactReviewSummary, ...]:
    """List Artifact Reviews without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
    current_ids = frozenset(item.artifact_review_id for item in _review_heads(graph))
    records = tuple(
        item
        for item in graph.artifact_reviews
        if artifact_instance_id is None
        or item.artifact_instance_id == artifact_instance_id
    )
    if not include_historical:
        records = tuple(
            item for item in records if item.artifact_review_id in current_ids
        )
    return tuple(
        _summary(class_id, activity_id, item, current_ids, revision)
        for item in sorted(
            records,
            key=lambda item: (item.artifact_instance_id, item.artifact_review_id),
        )
    )


def show_artifact_review(
    class_id: str,
    activity_id: str,
    artifact_review_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactReviewSummary:
    """Show one exact Artifact Review."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Review is not available: {artifact_review_id}"
        )
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
    review = _require_review(graph, artifact_review_id)
    _require_artifact(graph, activity_id, review.artifact_instance_id)
    current_ids = frozenset(item.artifact_review_id for item in _review_heads(graph))
    return _summary(class_id, activity_id, review, current_ids, revision)


def current_artifact_review(
    class_id: str,
    activity_id: str,
    artifact_instance_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactReviewSummary | None:
    """Return the explicit current Review head for one Artifact."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return None
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
    _require_artifact(graph, activity_id, artifact_instance_id)
    review = _current_review_for_artifact(graph, artifact_instance_id)
    if review is None:
        return None
    return _summary(
        class_id,
        activity_id,
        review,
        frozenset({review.artifact_review_id}),
        revision,
    )


__all__ = [
    "AddArtifactReviewRequest",
    "ArtifactReviewMutationResult",
    "ArtifactReviewSummary",
    "ReplaceArtifactReviewRequest",
    "add_artifact_review",
    "current_artifact_review",
    "list_artifact_reviews",
    "replace_artifact_review",
    "show_artifact_review",
]
