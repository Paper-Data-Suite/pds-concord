from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import ConcordModelError, PrivacyPolicy
from concord.storage import load_current_record_graph
from concord.workflows import (
    AddArtifactReviewRequest,
    ArtifactPagePlan,
    ConcordWorkflowConflictError,
    CreateActivityContextRequest,
    PrepareArtifactPagesRequest,
    ReplaceArtifactReviewRequest,
    WorkflowActor,
    add_artifact_review,
    create_activity_context,
    current_artifact_review,
    list_artifact_reviews,
    prepare_artifact_pages,
    replace_artifact_review,
    show_artifact_review,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 15, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Review Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-1",
                    return_expected=True,
                    route_required=False,
                ),
                ArtifactPagePlan(
                    page_number=2,
                    artifact_page_id="page-2",
                    return_expected=True,
                    route_required=False,
                ),
            ),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    return root, prepared.commit.snapshot_revision


def _request(revision: int, **overrides: object) -> AddArtifactReviewRequest:
    values: dict[str, object] = {
        "class_id": "class-1",
        "activity_id": "activity-1",
        "artifact_instance_id": "artifact-1",
        "artifact_review_id": "review-1",
        "readability_judgment": "readable",
        "page_completeness_judgment": "incomplete",
        "filing_judgment": "correct",
        "author_judgment": "unknown",
        "subject_judgment": "unresolved",
        "privacy_judgment": "teacher_restricted",
        "relevance_judgment": "relevant",
        "moderation_requirement": "not_required",
        "scoring_readiness": "not_ready",
        "review_outcome": "awaiting_additional_evidence",
        "privacy_policy": _privacy(),
        "expected_snapshot_revision": revision,
        "actor": _actor(),
        "notes": "Only part of the expected evidence is available.",
    }
    values.update(overrides)
    return AddArtifactReviewRequest(**values)  # type: ignore[arg-type]


def test_review_is_independent_from_artifact_return_state(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    before = load_current_record_graph(root, _work())
    result = add_artifact_review(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    after = load_current_record_graph(root, _work())
    assert result.commit.snapshot_revision == revision + 1
    assert after.graph.artifact_instances == before.graph.artifact_instances
    assert after.graph.artifact_pages == before.graph.artifact_pages
    assert after.graph.scan_references == ()
    assert len(after.graph.artifact_reviews) == 1
    assert after.graph.moderation_records == ()
    assert after.graph.score_records == ()


def test_review_readers_and_second_current_root_rejected(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    add_artifact_review(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    current = current_artifact_review(
        "class-1",
        "activity-1",
        "artifact-1",
        workspace_root=root,
    )
    assert current is not None
    assert current.artifact_review_id == "review-1"
    assert current.is_current
    assert (
        show_artifact_review(
            "class-1",
            "activity-1",
            "review-1",
            workspace_root=root,
        )
        == current
    )
    assert len(
        list_artifact_reviews(
            "class-1",
            "activity-1",
            workspace_root=root,
        )
    ) == 1
    with pytest.raises(ConcordWorkflowConflictError, match="current Review"):
        add_artifact_review(
            _request(
                revision + 1,
                artifact_review_id="review-independent",
            ),
            workspace_root=root,
        )


def test_review_successor_and_correction_preserve_history(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    first = add_artifact_review(
        _request(revision),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    replacement = replace_artifact_review(
        ReplaceArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_review_id="review-1",
            replacement_artifact_review_id="review-2",
            correction_id="correction-review-1",
            reason="Additional evidence was reviewed.",
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
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    loaded = load_current_record_graph(root, _work())
    assert replacement.commit.snapshot_revision == first.commit.snapshot_revision + 1
    assert len(loaded.graph.artifact_reviews) == 2
    assert len(loaded.graph.correction_records) == 1
    correction = loaded.graph.correction_records[0]
    assert correction.correction_type == "review_correction"
    assert correction.target_reference.record_id == "review-1"
    assert correction.replacement_reference is not None
    assert correction.replacement_reference.record_id == "review-2"
    history = list_artifact_reviews(
        "class-1", "activity-1", workspace_root=root
    )
    assert [item.is_current for item in history] == [False, True]


@pytest.mark.parametrize(
    "overrides",
    (
        {
            "review_outcome": "ready",
            "scoring_readiness": "ready",
            "moderation_requirement": "required",
        },
        {
            "review_outcome": "ready_with_qualification",
            "scoring_readiness": "ready_with_qualification",
            "notes": None,
        },
        {
            "review_outcome": "moderation_required",
            "moderation_requirement": "not_required",
        },
        {
            "review_outcome": "incomplete",
            "scoring_readiness": "ready",
        },
    ),
)
def test_review_structural_coherence_rejects_contradictions(
    tmp_path: Path,
    overrides: dict[str, object],
) -> None:
    root, revision = _workspace(tmp_path)
    with pytest.raises(ConcordModelError):
        add_artifact_review(
            _request(revision, **overrides),
            workspace_root=root,
        )


def test_review_list_does_not_create_absent_workspace(tmp_path: Path) -> None:
    root = tmp_path / "absent"
    assert (
        list_artifact_reviews(
            "class-1",
            "activity-1",
            workspace_root=root,
        )
        == ()
    )
    assert not root.exists()
