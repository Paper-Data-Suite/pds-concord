"""Read-only Concord Activity attention and next-action projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias

from concord.academic_result_share_attention import (
    AcademicResultShareAttentionState,
    _inspect_academic_result_share_attention_state_from_registration_context,
)
from concord.academic_work_registration import (
    _managed_activity_registration_context_from_verified_activity,
)
from concord.models import (
    ArtifactAuthor,
    ArtifactReview,
    ArtifactSubject,
    EvidenceReference,
)
from concord.workflows.activity import _load_activity_context, list_activities
from concord.workflows.activity_read import (
    ActivityReadContext,
    activity_summary_from_context,
)
from concord.workflows.artifact import ArtifactSummary
from concord.workflows.artifact_attribution import _current_authors, _current_subjects
from concord.workflows.artifact_collection import (
    ArtifactCollectionState,
    _assembly_state,
    inspect_artifact_collection_state,
)
from concord.workflows.artifact_review import _review_heads
from concord.workflows.artifact_review_attention import (
    ArtifactReviewAttentionState,
    inspect_artifact_review_attention_state,
)
from concord.workflows.artifact_scoring_attention import (
    ArtifactScoringAttentionState,
    inspect_artifact_scoring_attention_state,
)
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.group_plan import (
    GroupPlanSummary,
    show_group_plan,
)
from concord.workflows.moderation import (
    _applicable_records,
    _validate_evidence_lineage,
    _validate_subjects,
)
from concord.workflows.packet_instance import (
    PacketInstanceSummary,
)

ActivityAttentionTask: TypeAlias = Literal[
    "plan",
    "prepare",
    "collect",
    "review",
    "score",
    "share",
]

# This is a navigation convention only; it is not urgency or educational priority.
_TASK_ORDER: Final[dict[ActivityAttentionTask, int]] = {
    "plan": 0,
    "prepare": 1,
    "collect": 2,
    "review": 3,
    "score": 4,
    "share": 5,
}

_PLAN_ACTIVE_ACTIVITY_STATUSES: Final[frozenset[str]] = frozenset(
    {"draft", "configured", "active"}
)
_SIGNAL_GROUP_PLAN_STRATEGIES: Final[frozenset[str]] = frozenset(
    {"similar_signal", "mixed_signal"}
)


@dataclass(frozen=True, slots=True)
class ActivityAttentionItem:
    """One privacy-minimal, presentation-neutral Concord attention fact."""

    code: str
    label: str
    task: ActivityAttentionTask
    count: int
    action_id: str

    def __post_init__(self) -> None:
        if not self.code or not self.code.strip():
            raise ValueError("code must be nonempty.")
        if not self.label or not self.label.strip():
            raise ValueError("label must be nonempty.")
        if self.task not in _TASK_ORDER:
            raise ValueError("task must be a supported Concord attention task.")
        if (
            isinstance(self.count, bool)
            or not isinstance(self.count, int)
            or self.count <= 0
        ):
            raise ValueError("count must be a positive integer.")
        if not self.action_id or not self.action_id.strip():
            raise ValueError("action_id must be nonempty.")


@dataclass(frozen=True, slots=True)
class ActivityAttentionSummary:
    """Current attention picture for one Activity; never persisted as state."""

    class_id: str
    activity_id: str
    title: str
    items: tuple[ActivityAttentionItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))

    @property
    def next_item(self) -> ActivityAttentionItem | None:
        """Return the first truthful item in Concord's deterministic task order."""
        return self.items[0] if self.items else None


@dataclass(frozen=True, slots=True)
class _AttentionDefinition:
    code: str
    label: str
    task: ActivityAttentionTask
    action_id: str
    category_order: int


_ATTENTION_DEFINITIONS: Final[tuple[_AttentionDefinition, ...]] = (
    _AttentionDefinition(
        code="concord_plan_prepare",
        label="Group plans still need preparation",
        task="plan",
        action_id="open_activity_plan",
        category_order=0,
    ),
    _AttentionDefinition(
        code="concord_plan_unresolved_placements",
        label="Student group placements remain unresolved",
        task="plan",
        action_id="open_activity_plan",
        category_order=1,
    ),
    _AttentionDefinition(
        code="concord_plan_approve",
        label="Group plans are waiting for teacher approval",
        task="plan",
        action_id="open_activity_plan",
        category_order=2,
    ),
    _AttentionDefinition(
        code="concord_plan_apply",
        label="Approved group plans are ready to apply",
        task="plan",
        action_id="open_activity_plan",
        category_order=3,
    ),
    _AttentionDefinition(
        code="concord_prepare_materials",
        label="Packet materials still need preparation",
        task="prepare",
        action_id="open_activity_prepare",
        category_order=0,
    ),
    _AttentionDefinition(
        code="concord_prepare_routes_pending",
        label="Packet routing preparation needs recovery",
        task="prepare",
        action_id="open_activity_prepare",
        category_order=1,
    ),
    _AttentionDefinition(
        code="concord_prepare_recovery",
        label="Packet generation needs teacher recovery",
        task="prepare",
        action_id="open_activity_prepare",
        category_order=2,
    ),
    _AttentionDefinition(
        code="concord_collect_assembly",
        label="Returned evidence awaits assembly",
        task="collect",
        action_id="open_activity_collect",
        category_order=0,
    ),
    _AttentionDefinition(
        code="concord_collect_author_confirmation",
        label="Returned evidence needs author confirmation",
        task="collect",
        action_id="open_activity_collect",
        category_order=1,
    ),
    _AttentionDefinition(
        code="concord_collect_subject_confirmation",
        label="Returned evidence needs Subject confirmation",
        task="collect",
        action_id="open_activity_collect",
        category_order=2,
    ),
    _AttentionDefinition(
        code="concord_review_first",
        label="Assembled evidence is ready for Review",
        task="review",
        action_id="open_activity_review",
        category_order=0,
    ),
    _AttentionDefinition(
        code="concord_review_attention",
        label="Current evidence Review needs teacher attention",
        task="review",
        action_id="open_activity_review",
        category_order=1,
    ),
    _AttentionDefinition(
        code="concord_review_moderation",
        label="Reviewed evidence requires Moderation",
        task="review",
        action_id="open_activity_review",
        category_order=2,
    ),
    _AttentionDefinition(
        code="concord_review_post_moderation",
        label="Review needs update after Moderation",
        task="review",
        action_id="open_activity_review",
        category_order=3,
    ),
    _AttentionDefinition(
        code="concord_score_ready",
        label="Reviewed evidence is ready for scoring",
        task="score",
        action_id="open_activity_score",
        category_order=0,
    ),
    _AttentionDefinition(
        code="concord_share_inspect",
        label="Sharing state needs teacher inspection",
        task="share",
        action_id="open_activity_share",
        category_order=0,
    ),
    _AttentionDefinition(
        code="concord_share_withdrawn",
        label="Withdrawn publication needs teacher review",
        task="share",
        action_id="open_activity_share",
        category_order=1,
    ),
    _AttentionDefinition(
        code="concord_share_manifest",
        label="Current registered result needs a publication manifest",
        task="share",
        action_id="open_activity_share",
        category_order=2,
    ),
    _AttentionDefinition(
        code="concord_share_publish",
        label="Current result is ready for explicit publication",
        task="share",
        action_id="open_activity_share",
        category_order=3,
    ),
    _AttentionDefinition(
        code="concord_share_supersede",
        label="Newer current result is ready to supersede publication",
        task="share",
        action_id="open_activity_share",
        category_order=4,
    ),
)

_DEFINITION_BY_CODE: Final[dict[str, _AttentionDefinition]] = {
    definition.code: definition for definition in _ATTENTION_DEFINITIONS
}


def _definition_order(definition: _AttentionDefinition) -> tuple[int, int, str]:
    return (
        _TASK_ORDER[definition.task],
        definition.category_order,
        definition.code,
    )


def _items_from_counts(counts: dict[str, int]) -> tuple[ActivityAttentionItem, ...]:
    items: list[ActivityAttentionItem] = []
    definitions = sorted(_ATTENTION_DEFINITIONS, key=_definition_order)
    for definition in definitions:
        count = counts.get(definition.code, 0)
        if count <= 0:
            continue
        items.append(
            ActivityAttentionItem(
                code=definition.code,
                label=definition.label,
                task=definition.task,
                count=count,
                action_id=definition.action_id,
            )
        )
    return tuple(items)


def _unresolved_placements_need_attention(
    summary: GroupPlanSummary,
    *,
    workspace_root: str | Path | None,
) -> bool:
    """Return whether unresolved placements still require a teacher action."""
    if summary.unresolved_student_count <= 0:
        return False
    if summary.status not in {"draft", "previewed"}:
        return False
    if summary.strategy not in _SIGNAL_GROUP_PLAN_STRATEGIES:
        return True

    detail = show_group_plan(
        summary.class_id,
        summary.activity_id,
        summary.group_plan_id,
        workspace_root=workspace_root,
    )
    return detail.plan.missing_signal_disposition != "leave_unassigned"


def _plan_attention_counts(
    plans: tuple[GroupPlanSummary, ...],
    *,
    workspace_root: str | Path | None,
) -> dict[str, int]:
    counts: dict[str, int] = {}

    def add(code: str) -> None:
        if code not in _DEFINITION_BY_CODE:
            raise ValueError(f"Unknown Concord attention code: {code}")
        counts[code] = counts.get(code, 0) + 1

    for plan in plans:
        if plan.status == "draft":
            add("concord_plan_prepare")
        elif plan.status == "previewed":
            add("concord_plan_approve")
        elif plan.status == "approved":
            add("concord_plan_apply")
        elif plan.status in {"applied", "cancelled"}:
            continue

        if _unresolved_placements_need_attention(
            plan,
            workspace_root=workspace_root,
        ):
            # Count affected plans, not students. This remains safe when several
            # plan proposals overlap the same roster.
            add("concord_plan_unresolved_placements")

    return counts


def _prepare_attention_counts(
    packets: tuple[PacketInstanceSummary, ...],
) -> dict[str, int]:
    """Count current actionable Packet Instances without exposing target details."""
    counts: dict[str, int] = {}

    def add(code: str) -> None:
        if code not in _DEFINITION_BY_CODE:
            raise ValueError(f"Unknown Concord attention code: {code}")
        counts[code] = counts.get(code, 0) + 1

    for packet in packets:
        if packet.generation_status in {"planned", "rendering"}:
            add("concord_prepare_materials")
        elif packet.generation_status == "routes_pending":
            add("concord_prepare_routes_pending")
        elif packet.generation_status == "failed":
            add("concord_prepare_recovery")
        elif packet.generation_status in {"generated", "cancelled"}:
            continue

    return counts


def _collect_attention_counts(
    artifacts: tuple[ArtifactSummary, ...],
    *,
    workspace_root: str | Path | None,
) -> dict[str, int]:
    """Count affected Artifacts, never people or association records."""
    counts: dict[str, int] = {}

    def add(code: str) -> None:
        if code not in _DEFINITION_BY_CODE:
            raise ValueError(f"Unknown Concord attention code: {code}")
        counts[code] = counts.get(code, 0) + 1

    for artifact in artifacts:
        state: ArtifactCollectionState = inspect_artifact_collection_state(
            artifact.class_id,
            artifact.activity_id,
            artifact.artifact_instance_id,
            workspace_root=workspace_root,
        )
        if state.assembly_state in {
            "ready",
            "selection_required",
            "needs_recovery",
        }:
            add("concord_collect_assembly")
        if state.author_confirmation_pending:
            add("concord_collect_author_confirmation")
        if state.subject_confirmation_pending:
            add("concord_collect_subject_confirmation")

    return counts



def _review_attention_counts(
    artifacts: tuple[ArtifactSummary, ...],
    *,
    workspace_root: str | Path | None,
) -> dict[str, int]:
    """Count affected Artifacts using current Review-head/Moderation authority."""
    counts: dict[str, int] = {}

    def add(code: str) -> None:
        if code not in _DEFINITION_BY_CODE:
            raise ValueError(f"Unknown Concord attention code: {code}")
        counts[code] = counts.get(code, 0) + 1

    for artifact in artifacts:
        state: ArtifactReviewAttentionState = (
            inspect_artifact_review_attention_state(
                artifact.class_id,
                artifact.activity_id,
                artifact.artifact_instance_id,
                workspace_root=workspace_root,
            )
        )
        if state.first_review_pending:
            add("concord_review_first")
        if state.review_attention_pending:
            add("concord_review_attention")
        if state.moderation_pending:
            add("concord_review_moderation")
        if state.post_moderation_review_pending:
            add("concord_review_post_moderation")

    return counts


def _score_attention_counts(
    artifacts: tuple[ArtifactSummary, ...],
    *,
    workspace_root: str | Path | None,
) -> dict[str, int]:
    """Count reviewed Artifacts explicitly ready for scoring.

    The count unit is affected reviewed evidence items. It is not a count of
    missing Score records, students, targets, criteria, or required judgments.
    """
    count = 0
    for artifact in artifacts:
        state: ArtifactScoringAttentionState = (
            inspect_artifact_scoring_attention_state(
                artifact.class_id,
                artifact.activity_id,
                artifact.artifact_instance_id,
                workspace_root=workspace_root,
            )
        )
        if state.scoring_ready:
            count += 1
    return {} if count == 0 else {"concord_score_ready": count}


def _share_attention_counts(
    state: AcademicResultShareAttentionState,
) -> dict[str, int]:
    """Map one Activity publication-series state to at most one Share fact."""
    code_by_status = {
        "manifest_needed": "concord_share_manifest",
        "publish_ready": "concord_share_publish",
        "supersede_ready": "concord_share_supersede",
        "withdrawn": "concord_share_withdrawn",
        "needs_inspection": "concord_share_inspect",
    }
    code = code_by_status.get(state.status)
    return {} if code is None else {code: 1}


def _share_attention_from_context(
    context: ActivityReadContext,
) -> AcademicResultShareAttentionState:
    """Project Share state without re-reading the verified Activity graph."""
    registration_context = (
        _managed_activity_registration_context_from_verified_activity(
            context.root,
            context.work,
            context.activity,
            context.snapshot_revision,
        )
    )
    return _inspect_academic_result_share_attention_state_from_registration_context(
        registration_context,
        workspace_root=context.root,
    )


@dataclass(frozen=True, slots=True)
class _ActivityAttentionIndex:
    """Disposable indexes over one already-verified current Activity graph."""

    authors_by_artifact: dict[str, tuple[ArtifactAuthor, ...]]
    subjects_by_artifact: dict[str, tuple[ArtifactSubject, ...]]
    reviews_by_artifact: dict[str, ArtifactReview]


def _build_attention_index(context: ActivityReadContext) -> _ActivityAttentionIndex:
    author_lists: dict[str, list[ArtifactAuthor]] = {}
    for author in _current_authors(context.graph):
        author_lists.setdefault(author.artifact_instance_id, []).append(author)

    subject_lists: dict[str, list[ArtifactSubject]] = {}
    for subject in _current_subjects(context.graph):
        subject_lists.setdefault(subject.artifact_instance_id, []).append(subject)

    reviews: dict[str, ArtifactReview] = {}
    for review in _review_heads(context.graph):
        artifact_id = review.artifact_instance_id
        if artifact_id in reviews:
            raise ConcordWorkflowConflictError(
                "Artifact has competing current Review heads."
            )
        reviews[artifact_id] = review

    return _ActivityAttentionIndex(
        authors_by_artifact={
            key: tuple(value) for key, value in author_lists.items()
        },
        subjects_by_artifact={
            key: tuple(value) for key, value in subject_lists.items()
        },
        reviews_by_artifact=reviews,
    )


def _add_count(counts: dict[str, int], code: str) -> None:
    if code not in _DEFINITION_BY_CODE:
        raise ValueError(f"Unknown Concord attention code: {code}")
    counts[code] = counts.get(code, 0) + 1


def _plan_attention_counts_from_context(
    context: ActivityReadContext,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for plan in context.graph.group_plans:
        if plan.status == "draft":
            _add_count(counts, "concord_plan_prepare")
        elif plan.status == "previewed":
            _add_count(counts, "concord_plan_approve")
        elif plan.status == "approved":
            _add_count(counts, "concord_plan_apply")
        elif plan.status in {"applied", "cancelled"}:
            continue

        unresolved = bool(plan.unresolved_student_ids)
        actionable_status = plan.status in {"draft", "previewed"}
        signal_strategy = plan.strategy in _SIGNAL_GROUP_PLAN_STRATEGIES
        leave_unassigned = plan.missing_signal_disposition == "leave_unassigned"
        if unresolved and actionable_status and not (
            signal_strategy and leave_unassigned
        ):
            _add_count(counts, "concord_plan_unresolved_placements")
    return counts


def _prepare_attention_counts_from_context(
    context: ActivityReadContext,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for packet in context.graph.packet_instances:
        if packet.generation_status in {"planned", "rendering"}:
            _add_count(counts, "concord_prepare_materials")
        elif packet.generation_status == "routes_pending":
            _add_count(counts, "concord_prepare_routes_pending")
        elif packet.generation_status == "failed":
            _add_count(counts, "concord_prepare_recovery")
    return counts


def _collection_state_from_context(
    context: ActivityReadContext,
    index: _ActivityAttentionIndex,
    artifact_instance_id: str,
) -> ArtifactCollectionState:
    artifact = next(
        item
        for item in context.graph.artifact_instances
        if item.artifact_instance_id == artifact_instance_id
    )
    authors = index.authors_by_artifact.get(artifact_instance_id, ())
    subjects = index.subjects_by_artifact.get(artifact_instance_id, ())
    return ArtifactCollectionState(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        artifact_instance_id=artifact_instance_id,
        assembly_state=_assembly_state(
            context.root,
            context.work.class_id,
            context.work.work_id,
            artifact,
            context.graph,
        ),
        author_confirmation_pending=any(
            item.attribution_status in {"proposed", "disputed"}
            for item in authors
        ),
        subject_confirmation_pending=any(
            item.confirmation_status in {"proposed", "disputed", "unresolved"}
            for item in subjects
        ),
    )


def _review_state_from_context(
    context: ActivityReadContext,
    index: _ActivityAttentionIndex,
    artifact_instance_id: str,
    collection: ArtifactCollectionState,
) -> ArtifactReviewAttentionState:
    current = index.reviews_by_artifact.get(artifact_instance_id)
    if current is None:
        return ArtifactReviewAttentionState(
            class_id=context.work.class_id,
            activity_id=context.work.work_id,
            artifact_instance_id=artifact_instance_id,
            first_review_pending=collection.assembly_state == "assembled",
            review_attention_pending=False,
            moderation_pending=False,
            post_moderation_review_pending=False,
        )

    review_attention_pending = (
        current.review_outcome
        in {
            "incomplete",
            "unreadable",
            "misrouted",
            "duplicate",
            "awaiting_correction",
            "awaiting_additional_evidence",
        }
    )
    moderation_pending = False
    post_moderation_review_pending = False
    if current.moderation_requirement == "required":
        subject_context = tuple(
            item.subject_reference
            for item in index.subjects_by_artifact.get(artifact_instance_id, ())
        )
        reference = EvidenceReference(
            evidence_kind="artifact_instance",
            owning_system="concord",
            record_id=artifact_instance_id,
        )
        _validate_evidence_lineage(
            context.root,
            context.graph,
            context.work.work_id,
            reference,
        )
        _validate_subjects(
            context.root,
            context.work.class_id,
            context.graph,
            context.work.work_id,
            subject_context,
        )
        if _applicable_records(context.graph, reference, subject_context):
            post_moderation_review_pending = True
        else:
            moderation_pending = True

    return ArtifactReviewAttentionState(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        artifact_instance_id=artifact_instance_id,
        first_review_pending=False,
        review_attention_pending=review_attention_pending,
        moderation_pending=moderation_pending,
        post_moderation_review_pending=post_moderation_review_pending,
    )


def _score_state_from_context(
    context: ActivityReadContext,
    index: _ActivityAttentionIndex,
    artifact_instance_id: str,
) -> ArtifactScoringAttentionState:
    review = index.reviews_by_artifact.get(artifact_instance_id)
    ready = bool(
        context.activity.scoring_orientation != "evidence_only"
        and review is not None
        and review.review_outcome in {"ready", "ready_with_qualification"}
        and review.scoring_readiness in {"ready", "ready_with_qualification"}
        and review.moderation_requirement != "required"
    )
    return ArtifactScoringAttentionState(
        class_id=context.work.class_id,
        activity_id=context.work.work_id,
        artifact_instance_id=artifact_instance_id,
        scoring_ready=ready,
    )


def _attention_counts_from_context(
    context: ActivityReadContext,
) -> dict[str, int]:
    """Project all local Activity attention from one exact verified graph."""
    counts: dict[str, int] = {}
    if context.activity.status in _PLAN_ACTIVE_ACTIVITY_STATUSES:
        counts.update(_plan_attention_counts_from_context(context))
    counts.update(_prepare_attention_counts_from_context(context))

    index = _build_attention_index(context)
    for artifact in sorted(
        context.graph.artifact_instances,
        key=lambda item: item.artifact_instance_id,
    ):
        artifact_id = artifact.artifact_instance_id
        collection = _collection_state_from_context(context, index, artifact_id)
        if collection.assembly_state in {
            "ready",
            "selection_required",
            "needs_recovery",
        }:
            _add_count(counts, "concord_collect_assembly")
        if collection.author_confirmation_pending:
            _add_count(counts, "concord_collect_author_confirmation")
        if collection.subject_confirmation_pending:
            _add_count(counts, "concord_collect_subject_confirmation")

        review = _review_state_from_context(
            context,
            index,
            artifact_id,
            collection,
        )
        if review.first_review_pending:
            _add_count(counts, "concord_review_first")
        if review.review_attention_pending:
            _add_count(counts, "concord_review_attention")
        if review.moderation_pending:
            _add_count(counts, "concord_review_moderation")
        if review.post_moderation_review_pending:
            _add_count(counts, "concord_review_post_moderation")

        if _score_state_from_context(context, index, artifact_id).scoring_ready:
            _add_count(counts, "concord_score_ready")

    share_state = _share_attention_from_context(context)
    counts.update(_share_attention_counts(share_state))
    return counts


def _inspect_activity_attention_from_context(
    context: ActivityReadContext,
) -> ActivityAttentionSummary:
    summary = activity_summary_from_context(context)
    return ActivityAttentionSummary(
        class_id=summary.class_id,
        activity_id=summary.activity_id,
        title=summary.title,
        items=_items_from_counts(_attention_counts_from_context(context)),
    )


def inspect_activity_attention(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ActivityAttentionSummary:
    """Derive current attention from one exact operation-scoped Activity state."""
    context = _load_activity_context(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    return _inspect_activity_attention_from_context(context)


def list_activity_attention(
    *,
    workspace_root: str | Path | None = None,
    class_id: str | None = None,
) -> tuple[ActivityAttentionSummary, ...]:
    """List Activity attention in stable ordinary display order."""
    summaries = [
        inspect_activity_attention(
            activity.class_id,
            activity.activity_id,
            workspace_root=workspace_root,
        )
        for activity in list_activities(
            workspace_root=workspace_root,
            class_id=class_id,
        )
    ]
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.class_id,
                item.title.casefold(),
                item.activity_id,
            ),
        )
    )


__all__ = [
    "ActivityAttentionItem",
    "ActivityAttentionSummary",
    "ActivityAttentionTask",
    "inspect_activity_attention",
    "list_activity_attention",
]
