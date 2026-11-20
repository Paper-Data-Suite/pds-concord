"""Read-only target Activity assessment checkpoint for cross-class lesson reuse.

No saved preset is applied by this module. The existing Scoring Scale and
Criterion Set services retain typed revision, approval, and write authority.
Only opaque record identities/counts cross the inspection boundary; no Score
values, student names, target references, or source-class records are emitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.workflows import (
    list_criterion_sets,
    list_scores,
    list_scoring_scales,
    read_activity_criterion_set_selection,
    show_activity,
)
from concord.workflows.context import require_core_class, resolve_read_workspace_root
from concord.workflows.criterion_sets import CriterionSetSummary
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
)
from concord.workflows.score_recording import ScoreSummary
from concord.workflows.scoring_scales import ScoringScaleSummary


@dataclass(frozen=True, slots=True)
class TargetAssessmentCheckpoint:
    """Exact Activity-owned assessment identities from one stable snapshot."""

    class_id: str
    activity_id: str
    title: str
    scoring_orientation: str
    snapshot_revision: int
    scale_ids: tuple[str, ...]
    criterion_set_ids: tuple[str, ...]
    selected_criterion_set_ids: tuple[str, ...]
    score_record_ids: tuple[str, ...]
    criterion_count: int

    @property
    def has_configuration(self) -> bool:
        return bool(self.scale_ids or self.criterion_set_ids)


def _unique(values: tuple[str, ...], *, label: str) -> None:
    if len(values) != len(set(values)):
        raise ConcordWorkflowConflictError(
            f"Target assessment {label} is duplicated; reopen this Activity."
        )


def inspect_target_assessment(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> TargetAssessmentCheckpoint:
    """Read one verified target Activity; never query a source Activity."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Core workspace unavailable for target assessment."
        )
    require_core_class(root, class_id)
    activity = show_activity(class_id, activity_id, workspace_root=root).summary
    if (activity.class_id, activity.activity_id) != (class_id, activity_id):
        raise ConcordWorkflowConflictError(
            "Target assessment Activity identity changed."
        )
    scales = list_scoring_scales(
        class_id,
        activity_id,
        workspace_root=root,
        standards_library=standards_library,
    )
    criteria = list_criterion_sets(
        class_id,
        activity_id,
        workspace_root=root,
        standards_library=standards_library,
    )
    selection = read_activity_criterion_set_selection(
        class_id,
        activity_id,
        workspace_root=root,
        standards_library=standards_library,
    )
    scores = list_scores(
        class_id,
        activity_id,
        workspace_root=root,
        standards_library=standards_library,
    )
    revision = activity.snapshot_revision
    rows: tuple[ScoringScaleSummary | CriterionSetSummary | ScoreSummary, ...] = (
        *scales,
        *criteria,
        *scores,
    )
    for row in rows:
        if (
            row.class_id != class_id
            or row.activity_id != activity_id
            or row.snapshot_revision != revision
        ):
            raise ConcordWorkflowConflictError(
                "Target assessment read was cross-class or changed during review."
            )
    if selection.snapshot_revision != revision:
        raise ConcordWorkflowConflictError(
            "Target rubric selection changed during review."
        )
    scale_ids = tuple(value.scoring_scale_id for value in scales)
    criterion_ids = tuple(value.criterion_set_id for value in criteria)
    selected = tuple(selection.criterion_set_ids)
    score_ids = tuple(value.score_record_id for value in scores)
    for label, values in (
        ("Scale identities", scale_ids),
        ("Criterion Set identities", criterion_ids),
        ("selected Criterion Set identities", selected),
        ("Score identities", score_ids),
    ):
        _unique(values, label=label)
    if not set(selected).issubset(criterion_ids):
        raise ConcordWorkflowConflictError(
            "Target rubric selection refers to a missing Criterion Set."
        )
    return TargetAssessmentCheckpoint(
        class_id=class_id,
        activity_id=activity_id,
        title=activity.title,
        scoring_orientation=activity.scoring_orientation,
        snapshot_revision=revision,
        scale_ids=scale_ids,
        criterion_set_ids=criterion_ids,
        selected_criterion_set_ids=selected,
        score_record_ids=score_ids,
        criterion_count=sum(item.criterion_count for item in criteria),
    )


@dataclass(frozen=True, slots=True)
class TargetAssessmentDelta:
    """Proof of changes in target assessment definitions, not source Scores."""

    new_scales: int
    new_criterion_sets: int
    selection_changed: bool
    final_selected_count: int
    final_criterion_count: int


def verify_target_assessment_delta(
    before: TargetAssessmentCheckpoint,
    after: TargetAssessmentCheckpoint,
) -> TargetAssessmentDelta:
    """Fail closed on missing definitions, changed Scores or ambiguous identity."""
    if (before.class_id, before.activity_id) != (after.class_id, after.activity_id):
        raise ConcordWorkflowConflictError("Target assessment changed Activity/class.")
    if after.snapshot_revision < before.snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Target assessment snapshot moved backwards."
        )
    if not set(before.scale_ids).issubset(after.scale_ids) or not set(
        before.criterion_set_ids
    ).issubset(after.criterion_set_ids):
        raise ConcordWorkflowConflictError(
            "Target assessment history was replaced; reopen and verify."
        )
    if before.score_record_ids != after.score_record_ids:
        raise ConcordWorkflowConflictError(
            "Target Score records changed during setup; no no-Score claim is valid."
        )
    return TargetAssessmentDelta(
        new_scales=len(set(after.scale_ids) - set(before.scale_ids)),
        new_criterion_sets=len(
            set(after.criterion_set_ids) - set(before.criterion_set_ids)
        ),
        selection_changed=(
            before.selected_criterion_set_ids != after.selected_criterion_set_ids
        ),
        final_selected_count=len(after.selected_criterion_set_ids),
        final_criterion_count=after.criterion_count,
    )
