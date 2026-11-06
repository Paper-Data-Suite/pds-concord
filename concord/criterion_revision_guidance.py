"""Read-only teacher projections of exact native Criterion Set revisions.

Historical native revisions, their Criteria, and their typed Scale references
must not be regenerated or silently upgraded while a teacher is browsing them.
This presentation adapter owns neither Core Standards nor Concord storage.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pds_core.standards import StandardsLibrary

from concord.criterion_guidance import (
    CriterionDraft,
    CriterionSetDraft,
    target_choice,
)
from concord.workflows.criterion_sets import (
    ActivityCriterionSetSelectionSnapshot,
    CriterionSetDetail,
)


class NativeRubricReviewError(ValueError):
    """The two read-only snapshots are not a coherent native rubric view."""


@dataclass(frozen=True, slots=True)
class NativeRubricReview:
    """Exact native revision and its unchanged in-memory editable projection."""

    criterion_set_id: str
    lineage_id: str
    revision: int
    supersedes_criterion_set_id: str | None
    status: str
    is_current: bool
    is_selected: bool
    selected_position: int | None
    snapshot_revision: int
    original_criterion_ids: tuple[str, ...]
    draft: CriterionSetDraft


def project_native_criterion_set(
    detail: CriterionSetDetail,
    selection: ActivityCriterionSetSelectionSnapshot,
) -> NativeRubricReview:
    """Copy *all* editable Criterion content, without authorizing a mutation.

    The copied draft has no native IDs. Original IDs and lineage are kept as
    read-only metadata; a future revision must allocate new durable identities.
    """
    summary = detail.summary
    if detail.summary.snapshot_revision != selection.snapshot_revision:
        raise NativeRubricReviewError(
            "Activity selection changed during rubric review. Reload the Activity."
        )
    if len(set(selection.criterion_set_ids)) != len(selection.criterion_set_ids):
        raise NativeRubricReviewError(
            "Activity has duplicate Criterion Set selections."
        )
    actual_selected = summary.criterion_set_id in selection.criterion_set_ids
    if summary.is_selected != actual_selected:
        raise NativeRubricReviewError(
            "Criterion Set selection status changed during review. Reload."
        )
    if not detail.criteria or summary.criterion_count != len(detail.criteria):
        raise NativeRubricReviewError(
            "The native Criterion Set has incomplete ordered Criterion details."
        )
    criterion_ids = tuple(item.criterion_id for item in detail.criteria)
    if len(criterion_ids) != len(set(criterion_ids)):
        raise NativeRubricReviewError("Native Criterion IDs must be unique.")
    if any(
        item.criterion_set_id != summary.criterion_set_id
        for item in detail.criteria
    ):
        raise NativeRubricReviewError(
            "A Criterion does not belong to this exact native Set revision."
        )
    draft = CriterionSetDraft(
        name=summary.name,
        purpose=detail.purpose,
        criterion_set_kind=summary.criterion_set_kind,
        scope=summary.scope,
        criteria=tuple(
            CriterionDraft(
                key=item.key,
                label=item.label,
                definition=item.definition,
                criterion_kind=item.criterion_kind,
                supported_target_kinds=item.supported_target_kinds,
                standard_id=item.standard_id,
                alignment_standard_ids=item.alignment_standard_ids,
                default_scoring_scale_id=item.default_scoring_scale_id,
                status=item.status,
            )
            for item in detail.criteria
        ),
    )
    position = (
        selection.criterion_set_ids.index(summary.criterion_set_id) + 1
        if actual_selected
        else None
    )
    return NativeRubricReview(
        criterion_set_id=summary.criterion_set_id,
        lineage_id=summary.lineage_id,
        revision=summary.revision,
        supersedes_criterion_set_id=summary.supersedes_criterion_set_id,
        status=summary.status,
        is_current=summary.is_current,
        is_selected=actual_selected,
        selected_position=position,
        snapshot_revision=selection.snapshot_revision,
        original_criterion_ids=criterion_ids,
        draft=draft,
    )


def _standard_label(
    standard_id: str,
    library: StandardsLibrary | None,
) -> str:
    """Never infer a code/name or imply that a historical ID is still active."""
    if library is None:
        return f"{standard_id} [Core definition not loaded]"
    match = next(
        (item for item in library.standards if item.standard_id == standard_id),
        None,
    )
    if match is None:
        return f"{standard_id} [Core definition unavailable]"
    lifecycle = (
        "active"
        if match.active and "deprecated" not in match.tags
        else "inactive/deprecated"
    )
    return (
        f"{match.code} — {match.short_name} "
        f"[Core ID: {standard_id}; {lifecycle}]"
    )


def describe_native_criterion_set(
    review: NativeRubricReview,
    *,
    standards_library: StandardsLibrary | None = None,
    native_scale_names: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Teacher-facing read-only preview of one immutable native revision."""
    labels = native_scale_names if native_scale_names is not None else {}
    draft = review.draft
    lines: tuple[str, ...] = (
        f"Native rubric: {draft.name}",
        f"Purpose: {draft.purpose}",
        f"Exact Criterion Set: {review.criterion_set_id}",
        f"Lineage: {review.lineage_id}; revision: {review.revision}",
        f"Revision status: {'current head' if review.is_current else 'historical'}",
        f"Selected for future Scores: {'yes' if review.is_selected else 'no'}",
        (
            f"Selection position: {review.selected_position}"
            if review.is_selected
            else "Selection position: not selected"
        ),
        f"Activity snapshot: {review.snapshot_revision}",
        f"Set status: {review.status}",
        f"Assessment type: {draft.criterion_set_kind}",
        f"Semantic scope: {draft.scope} (not a saved preset)",
        f"Supersedes: {review.supersedes_criterion_set_id or 'none'}",
        f"Ordered Criteria: {len(draft.criteria)}",
    )
    for position, (native_id, criterion) in enumerate(
        zip(review.original_criterion_ids, draft.criteria, strict=True), 1
    ):
        targets = ", ".join(
            target_choice(kind).label + f" ({kind})"
            for kind in criterion.supported_target_kinds
        )
        governing = (
            _standard_label(criterion.standard_id, standards_library)
            if criterion.standard_id is not None
            else "local — no governing Standard"
        )
        alignment_labels = (
            ", ".join(
                _standard_label(standard, standards_library)
                for standard in criterion.alignment_standard_ids
            )
            or "none"
        )
        scale_id = criterion.default_scoring_scale_id
        scale = (
            f"{labels[scale_id]} [native Scale ID: {scale_id}]"
            if scale_id is not None and scale_id in labels
            else (f"{scale_id} [native Scale ID]" if scale_id else "none")
        )
        lines += (
            f"{position}. {criterion.label} ({criterion.key})",
            f"   Exact Criterion ID: {native_id}",
            f"   Definition: {criterion.definition}",
            f"   Type/status: {criterion.criterion_kind} / {criterion.status}",
            f"   Permitted Score targets: {targets}",
            f"   Governing Standard: {governing}",
            f"   Alignment Standards: {alignment_labels}",
            f"   Native default Scale: {scale}",
        )
    return lines + (
        "Read only: this exact historical/current definition was not revised.",
        "No Activity selection, reusable preset, Scores, Grades, or evidence changed.",
    )
