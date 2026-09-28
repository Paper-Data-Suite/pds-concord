from __future__ import annotations

import pytest

from concord.models import ConcordModelError, PrivacyPolicy
from concord.workflows.artifact_routine_review_profiles import (
    ArtifactRoutineReviewValues,
    routine_qualified_review_values,
    routine_ready_review_values,
)


def test_ready_profile_is_complete_and_uses_existing_legal_values() -> None:
    values = routine_ready_review_values()

    assert values == ArtifactRoutineReviewValues(
        readability_judgment="readable",
        page_completeness_judgment="complete",
        filing_judgment="correct",
        author_judgment="confirmed",
        subject_judgment="confirmed",
        privacy_judgment="teacher_restricted",
        relevance_judgment="relevant",
        moderation_requirement="not_required",
        scoring_readiness="ready",
        review_outcome="ready",
        notes=None,
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
    )


def test_ready_profile_is_only_a_proposed_value_bundle() -> None:
    values = routine_ready_review_values()

    assert not hasattr(values, "artifact_review_id")
    assert not hasattr(values, "artifact_instance_id")
    assert not hasattr(values, "reviewer")
    assert not hasattr(values, "reviewed_at")
    assert not hasattr(values, "supersedes_artifact_review_id")


def test_qualified_profile_preserves_ordinary_values_and_changes_only_qualification(
) -> None:
    ready = routine_ready_review_values()
    qualified = routine_qualified_review_values(
        "Readable and complete; minor scan shadow does not obscure student work."
    )

    assert qualified.readability_judgment == ready.readability_judgment
    assert qualified.page_completeness_judgment == ready.page_completeness_judgment
    assert qualified.filing_judgment == ready.filing_judgment
    assert qualified.author_judgment == ready.author_judgment
    assert qualified.subject_judgment == ready.subject_judgment
    assert qualified.privacy_judgment == ready.privacy_judgment
    assert qualified.relevance_judgment == ready.relevance_judgment
    assert qualified.moderation_requirement == ready.moderation_requirement
    assert qualified.privacy_policy == ready.privacy_policy
    assert qualified.scoring_readiness == "ready_with_qualification"
    assert qualified.review_outcome == "ready_with_qualification"
    assert qualified.notes is not None


@pytest.mark.parametrize("notes", ("", "   "))
def test_qualified_profile_requires_meaningful_teacher_note(notes: str) -> None:
    with pytest.raises(
        ConcordModelError,
        match="notes must be a nonempty string|leading or trailing whitespace",
    ):
        routine_qualified_review_values(notes)


def test_qualified_profile_rejects_missing_note_through_canonical_model() -> None:
    with pytest.raises(ConcordModelError, match="requires explanatory notes"):
        ArtifactRoutineReviewValues(
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="confirmed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="not_required",
            scoring_readiness="ready_with_qualification",
            review_outcome="ready_with_qualification",
            notes=None,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        )


def test_explicit_privacy_values_are_preserved_for_preview_and_later_write() -> None:
    policy = PrivacyPolicy(
        classification="teacher_and_subjects",
    )
    values = routine_ready_review_values(
        privacy_judgment="teacher_and_subjects",
        privacy_policy=policy,
    )

    assert values.privacy_judgment == "teacher_and_subjects"
    assert values.privacy_policy is policy


def test_illegal_review_combination_is_rejected_by_canonical_model_contract() -> None:
    with pytest.raises(ConcordModelError):
        ArtifactRoutineReviewValues(
            readability_judgment="unreadable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="confirmed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="not_required",
            scoring_readiness="ready",
            review_outcome="ready",
            notes=None,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        )
