"""Read-only Concord Activity attention and next-action projection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, TypeAlias

from concord.academic_result_share_attention import (
    AcademicResultShareAttentionState,
    inspect_academic_result_share_attention_state,
)
from concord.workflows.activity import list_activities, show_activity
from concord.workflows.artifact import ArtifactSummary, list_artifacts
from concord.workflows.artifact_collection import (
    ArtifactCollectionState,
    inspect_artifact_collection_state,
)
from concord.workflows.artifact_review_attention import (
    ArtifactReviewAttentionState,
    inspect_artifact_review_attention_state,
)
from concord.workflows.artifact_scoring_attention import (
    ArtifactScoringAttentionState,
    inspect_artifact_scoring_attention_state,
)
from concord.workflows.group_plan import (
    GroupPlanSummary,
    list_group_plans,
    show_group_plan,
)
from concord.workflows.packet_instance import (
    PacketInstanceSummary,
    list_packet_instances,
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


def inspect_activity_attention(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ActivityAttentionSummary:
    """Derive current attention for one Activity from authoritative state only."""
    detail = show_activity(class_id, activity_id, workspace_root=workspace_root)

    counts: dict[str, int] = {}
    if detail.summary.status in _PLAN_ACTIVE_ACTIVITY_STATUSES:
        plans = list_group_plans(
            class_id,
            activity_id,
            workspace_root=workspace_root,
        )
        counts.update(
            _plan_attention_counts(plans, workspace_root=workspace_root)
        )

    packets = list_packet_instances(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    counts.update(_prepare_attention_counts(packets))

    artifacts = list_artifacts(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    counts.update(
        _collect_attention_counts(
            artifacts,
            workspace_root=workspace_root,
        )
    )
    counts.update(
        _review_attention_counts(
            artifacts,
            workspace_root=workspace_root,
        )
    )
    counts.update(
        _score_attention_counts(
            artifacts,
            workspace_root=workspace_root,
        )
    )

    share_state = inspect_academic_result_share_attention_state(
        class_id,
        activity_id,
        workspace_root=workspace_root,
    )
    counts.update(_share_attention_counts(share_state))

    return ActivityAttentionSummary(
        class_id=detail.summary.class_id,
        activity_id=detail.summary.activity_id,
        title=detail.summary.title,
        items=_items_from_counts(counts),
    )


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
