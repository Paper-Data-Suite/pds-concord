from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.workflows.activity_attention as attention


def _context(
    *,
    group_plans: tuple[object, ...] = (),
    packet_instances: tuple[object, ...] = (),
    artifact_instances: tuple[object, ...] = (),
    artifact_authors: tuple[object, ...] = (),
    artifact_subjects: tuple[object, ...] = (),
    artifact_reviews: tuple[object, ...] = (),
    moderation_records: tuple[object, ...] = (),
    scoring_orientation: str = "evidence_only",
) -> Any:
    return SimpleNamespace(
        root=Path("workspace"),
        work=SimpleNamespace(class_id="class-1", work_id="activity-1"),
        activity=SimpleNamespace(
            activity_id="activity-1",
            status="active",
            scoring_orientation=scoring_orientation,
        ),
        graph=SimpleNamespace(
            group_plans=group_plans,
            packet_instances=packet_instances,
            artifact_instances=artifact_instances,
            artifact_authors=artifact_authors,
            artifact_subjects=artifact_subjects,
            artifact_reviews=artifact_reviews,
            moderation_records=moderation_records,
        ),
    )


def _plan(
    *,
    status: str,
    strategy: str = "manual",
    unresolved: tuple[str, ...] = (),
    disposition: str | None = None,
) -> object:
    return SimpleNamespace(
        status=status,
        strategy=strategy,
        unresolved_student_ids=unresolved,
        missing_signal_disposition=disposition,
    )


def test_optimized_group_plan_projection_preserves_lifecycle_and_signal_semantics(
) -> None:
    context = _context(
        group_plans=(
            _plan(status="draft", unresolved=("student-1",)),
            _plan(status="previewed"),
            _plan(status="approved"),
            _plan(
                status="draft",
                strategy="similar_signal",
                unresolved=("student-2",),
                disposition="leave_unassigned",
            ),
            _plan(status="applied"),
            _plan(status="cancelled"),
        )
    )

    assert attention._plan_attention_counts_from_context(context) == {
        "concord_plan_prepare": 2,
        "concord_plan_unresolved_placements": 1,
        "concord_plan_approve": 1,
        "concord_plan_apply": 1,
    }


def test_optimized_packet_projection_preserves_actionable_status_mapping() -> None:
    context = _context(
        packet_instances=(
            SimpleNamespace(generation_status="planned"),
            SimpleNamespace(generation_status="rendering"),
            SimpleNamespace(generation_status="routes_pending"),
            SimpleNamespace(generation_status="failed"),
            SimpleNamespace(generation_status="generated"),
            SimpleNamespace(generation_status="cancelled"),
        )
    )

    assert attention._prepare_attention_counts_from_context(context) == {
        "concord_prepare_materials": 2,
        "concord_prepare_routes_pending": 1,
        "concord_prepare_recovery": 1,
    }


def test_disposable_index_uses_only_current_author_subject_and_review_heads() -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        activity_id="activity-1",
    )
    old_author = SimpleNamespace(
        artifact_author_id="author-old",
        artifact_instance_id="artifact-1",
        attribution_status="confirmed",
        supersedes_artifact_author_id=None,
    )
    new_author = SimpleNamespace(
        artifact_author_id="author-new",
        artifact_instance_id="artifact-1",
        attribution_status="disputed",
        supersedes_artifact_author_id="author-old",
    )
    explicitly_superseded_author = SimpleNamespace(
        artifact_author_id="author-superseded",
        artifact_instance_id="artifact-1",
        attribution_status="superseded",
        supersedes_artifact_author_id=None,
    )
    old_subject = SimpleNamespace(
        artifact_subject_id="subject-old",
        artifact_instance_id="artifact-1",
        confirmation_status="proposed",
        supersedes_artifact_subject_id=None,
        subject_reference=SimpleNamespace(subject_id="old"),
    )
    new_subject = SimpleNamespace(
        artifact_subject_id="subject-new",
        artifact_instance_id="artifact-1",
        confirmation_status="confirmed",
        supersedes_artifact_subject_id="subject-old",
        subject_reference=SimpleNamespace(subject_id="new"),
    )
    explicitly_superseded_subject = SimpleNamespace(
        artifact_subject_id="subject-superseded",
        artifact_instance_id="artifact-1",
        confirmation_status="superseded",
        supersedes_artifact_subject_id=None,
        subject_reference=SimpleNamespace(subject_id="historical"),
    )
    old_review = SimpleNamespace(
        artifact_review_id="review-old",
        artifact_instance_id="artifact-1",
        supersedes_artifact_review_id=None,
    )
    new_review = SimpleNamespace(
        artifact_review_id="review-new",
        artifact_instance_id="artifact-1",
        supersedes_artifact_review_id="review-old",
    )

    index = attention._build_attention_index(
        _context(
            artifact_instances=(artifact,),
            artifact_authors=(
                old_author,
                new_author,
                explicitly_superseded_author,
            ),
            artifact_subjects=(
                old_subject,
                new_subject,
                explicitly_superseded_subject,
            ),
            artifact_reviews=(old_review, new_review),
        )
    )

    assert [
        item.artifact_author_id
        for item in index.authors_by_artifact["artifact-1"]
    ] == ["author-new"]
    assert [
        item.artifact_subject_id
        for item in index.subjects_by_artifact["artifact-1"]
    ] == ["subject-new"]
    assert index.reviews_by_artifact["artifact-1"].artifact_review_id == "review-new"


@pytest.mark.parametrize(
    ("orientation", "expected"),
    (
        ("evidence_only", False),
        ("local_criteria_only", True),
        ("standards_based", True),
        ("mixed", True),
    ),
)
def test_optimized_scoring_projection_preserves_orientation_semantics(
    orientation: str,
    expected: bool,
) -> None:
    review = SimpleNamespace(
        artifact_review_id="review-1",
        artifact_instance_id="artifact-1",
        supersedes_artifact_review_id=None,
        review_outcome="ready",
        scoring_readiness="ready",
        moderation_requirement="not_required",
    )
    context = _context(
        artifact_reviews=(review,),
        scoring_orientation=orientation,
    )
    index = attention._build_attention_index(context)

    result = attention._score_state_from_context(
        context,
        index,
        "artifact-1",
    )

    assert result.scoring_ready is expected


def test_optimized_collection_projection_ignores_superseded_pending_associations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        activity_id="activity-1",
    )
    old_author = SimpleNamespace(
        artifact_author_id="author-old",
        artifact_instance_id="artifact-1",
        attribution_status="proposed",
        supersedes_artifact_author_id=None,
    )
    new_author = SimpleNamespace(
        artifact_author_id="author-new",
        artifact_instance_id="artifact-1",
        attribution_status="confirmed",
        supersedes_artifact_author_id="author-old",
    )
    old_subject = SimpleNamespace(
        artifact_subject_id="subject-old",
        artifact_instance_id="artifact-1",
        confirmation_status="unresolved",
        supersedes_artifact_subject_id=None,
        subject_reference=SimpleNamespace(subject_id="old"),
    )
    new_subject = SimpleNamespace(
        artifact_subject_id="subject-new",
        artifact_instance_id="artifact-1",
        confirmation_status="confirmed",
        supersedes_artifact_subject_id="subject-old",
        subject_reference=SimpleNamespace(subject_id="new"),
    )
    context = _context(
        artifact_instances=(artifact,),
        artifact_authors=(old_author, new_author),
        artifact_subjects=(old_subject, new_subject),
    )
    index = attention._build_attention_index(context)
    monkeypatch.setattr(attention, "_assembly_state", lambda *_a, **_k: "assembled")

    state = attention._collection_state_from_context(
        context,
        index,
        "artifact-1",
    )

    assert not state.author_confirmation_pending
    assert not state.subject_confirmation_pending


@pytest.mark.parametrize(
    ("has_moderation", "moderation_pending", "post_pending"),
    (
        (False, True, False),
        (True, False, True),
    ),
)
def test_optimized_moderation_projection_preserves_pending_transition(
    monkeypatch: pytest.MonkeyPatch,
    has_moderation: bool,
    moderation_pending: bool,
    post_pending: bool,
) -> None:
    artifact = SimpleNamespace(
        artifact_instance_id="artifact-1",
        activity_id="activity-1",
    )
    review = SimpleNamespace(
        artifact_review_id="review-1",
        artifact_instance_id="artifact-1",
        supersedes_artifact_review_id=None,
        review_outcome="moderation_required",
        scoring_readiness="not_ready",
        moderation_requirement="required",
    )
    context = _context(
        artifact_instances=(artifact,),
        artifact_reviews=(review,),
    )
    index = attention._build_attention_index(context)
    monkeypatch.setattr(
        attention,
        "_validate_evidence_lineage",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        attention,
        "_validate_subjects",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        attention,
        "_applicable_records",
        lambda *_a, **_k: ((object(),) if has_moderation else ()),
    )
    collection = SimpleNamespace(assembly_state="assembled")

    state = attention._review_state_from_context(
        context,
        index,
        "artifact-1",
        collection,  # type: ignore[arg-type]
    )

    assert state.moderation_pending is moderation_pending
    assert state.post_moderation_review_pending is post_pending


def test_competing_current_review_heads_still_fail_closed() -> None:
    context = _context(
        artifact_reviews=(
            SimpleNamespace(
                artifact_review_id="review-a",
                artifact_instance_id="artifact-1",
                supersedes_artifact_review_id=None,
            ),
            SimpleNamespace(
                artifact_review_id="review-b",
                artifact_instance_id="artifact-1",
                supersedes_artifact_review_id=None,
            ),
        )
    )

    with pytest.raises(
        attention.ConcordWorkflowConflictError,
        match="competing current Review heads",
    ):
        attention._build_attention_index(context)
