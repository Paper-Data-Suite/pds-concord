"""#152 Slice 1D: teacher Review provenance and native evidence-link preview."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_artifact_scoring as scoring_menu
from concord.models import EvidenceReference
from concord.workflows.artifact_routine_scoring import ArtifactRoutineScoringContext
from concord.workflows.artifact_routine_scoring_preparation import (
    RoutineScorePreview,
)
from concord.workflows.errors import ConcordWorkflowConflictError


def _context_and_preview() -> tuple[
    ArtifactRoutineScoringContext, RoutineScorePreview
]:
    source = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    context = cast(
        ArtifactRoutineScoringContext,
        SimpleNamespace(
            class_id="class-synthetic",
            activity_id="activity-synthetic",
            snapshot_revision=8,
            snapshot_sha256="synthetic-sha",
            artifact=SimpleNamespace(
                artifact_instance_id="artifact-1",
                artifact_status="returned",
            ),
            current_review=SimpleNamespace(
                artifact_instance_id="artifact-1",
                reviewer=SimpleNamespace(
                    actor_kind="authorized_adult",
                    actor_id="private-teacher-id",
                    display_label_snapshot="Teacher Example",
                ),
                reviewed_at="2026-11-22T15:00:00+00:00",
                review_outcome="ready_with_qualification",
                scoring_readiness="ready_with_qualification",
                author_judgment="qualified",
                subject_judgment="confirmed",
            ),
            evidence_reference=source,
            eligibility=SimpleNamespace(routine_scoring_eligible=True),
        ),
    )
    preview = cast(
        RoutineScorePreview,
        SimpleNamespace(
            class_id="class-synthetic",
            activity_id="activity-synthetic",
            artifact_instance_id="artifact-1",
            snapshot_revision=8,
            snapshot_sha256="synthetic-sha",
            evidence=SimpleNamespace(evidence_reference=source),
        ),
    )
    return context, preview


def test_review_and_evidence_are_truthfully_distinguished() -> None:
    context, preview = _context_and_preview()
    lines = scoring_menu._review_evidence_lines(context, preview)
    assert lines[0] == (
        "Review provenance (preview only): explicit current Artifact Review"
    )
    assert lines[1] == (
        "Review outcome/readiness: "
        "ready with qualification / ready with qualification"
    )
    assert lines[2] == "Reviewed by: Teacher Example"
    assert lines[3].startswith("Reviewed ")
    assert " at " in lines[3]
    assert lines[4] == "Review author/subject judgments: qualified / confirmed"
    assert "not independent proof of a Core scan receipt" in lines[5]
    assert "no exact scanned-file or assembled-PDF version linked" in lines[6]
    assert all("private-teacher-id" not in line for line in lines)
    assert all("artifact-1" not in line for line in lines)


@pytest.mark.parametrize(
    "change",
    (
        "missing_review",
        "wrong_review_artifact",
        "wrong_preview_artifact",
        "wrong_preview_class",
        "wrong_preview_activity",
        "wrong_revision",
        "wrong_sha",
        "changed_source",
        "changed_link",
        "not_eligible",
    ),
)
def test_mismatched_review_or_evidence_refuses_teacher_preview(
    change: str,
) -> None:
    context, preview = _context_and_preview()
    wrong_ref = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="unrelated-artifact",
    )
    if change == "missing_review":
        context.current_review = None
    elif change == "wrong_review_artifact":
        context.current_review.artifact_instance_id = "unrelated-artifact"
    elif change == "wrong_preview_artifact":
        preview.artifact_instance_id = "unrelated-artifact"
    elif change == "wrong_preview_class":
        preview.class_id = "unrelated-class"
    elif change == "wrong_preview_activity":
        preview.activity_id = "unrelated-activity"
    elif change == "wrong_revision":
        preview.snapshot_revision = 9
    elif change == "wrong_sha":
        preview.snapshot_sha256 = "unrelated-sha"
    elif change == "changed_source":
        context.evidence_reference = wrong_ref
    elif change == "changed_link":
        preview.evidence.evidence_reference = wrong_ref
    elif change == "not_eligible":
        context.eligibility.routine_scoring_eligible = False

    with pytest.raises(
        ConcordWorkflowConflictError,
        match="no Score was recorded",
    ):
        scoring_menu._review_evidence_lines(context, preview)


def test_missing_reviewer_snapshot_is_not_replaced_with_raw_identity() -> None:
    context, preview = _context_and_preview()
    context.current_review.reviewer.display_label_snapshot = None
    lines = scoring_menu._review_evidence_lines(context, preview)
    assert "Reviewed by: Reviewer display name not recorded" in lines
    assert not any("private-teacher-id" in line for line in lines)


def test_system_reviewer_cannot_be_mislabeled_as_a_teacher() -> None:
    context, preview = _context_and_preview()
    context.current_review.reviewer.actor_kind = "system"
    lines = scoring_menu._review_evidence_lines(context, preview)
    assert "Reviewed by: Reviewer display name not recorded" in lines
    assert "Teacher Example" not in " ".join(lines)
