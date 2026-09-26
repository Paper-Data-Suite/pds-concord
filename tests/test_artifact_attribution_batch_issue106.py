from __future__ import annotations

from dataclasses import replace
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

import concord.workflows.artifact_attribution as attribution
from concord.models import (
    ArtifactAuthor,
    ArtifactSubject,
    ParticipantReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.storage import commit_record_batch, load_current_record_graph
from concord.workflows import (
    ArtifactPagePlan,
    BatchConfirmArtifactAttributionRequest,
    CreateActivityContextRequest,
    PrepareArtifactPagesRequest,
    WorkflowActor,
    batch_confirm_artifact_attribution,
    create_activity_context,
    inspect_artifact_attribution_review,
    prepare_artifact_pages,
)
from concord.workflows.artifact_collection import inspect_artifact_collection_state
from concord.workflows.context import provenance

CLASS_ID = "class-issue106-batch"
ACTIVITY_ID = "activity-issue106-batch"


def _clock() -> datetime:
    return datetime(2026, 9, 24, 23, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-issue106-batch",
        display_label="Synthetic Batch Teacher",
        role_label="teacher",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id=CLASS_ID,
        work_id=ACTIVITY_ID,
    )


def _student_author(student_id: str) -> ParticipantReference:
    return ParticipantReference(
        participant_kind="core_student",
        participant_id=student_id,
        owning_system="core",
    )


def _student_subject(student_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _workspace_with_proposals(
    tmp_path: Path,
    artifact_count: int,
) -> tuple[Path, int, tuple[str, ...], tuple[str, ...]]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS_ID,
            "2026-2027",
            created_at=_clock(),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS_ID,
            tuple(
                {
                    "student_id": f"student-{index:03}",
                    "last_name": f"Student{index:03}",
                    "first_name": "Synthetic",
                    "period": "1",
                }
                for index in range(1, artifact_count + 1)
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            title="Issue 106 Activity-Wide Batch",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-issue106-batch",
            actor=_actor(),
            activity_status="active",
            session_status="active",
        ),
        workspace_root=root,
        clock=_clock,
    )
    revision = created.commit.snapshot_revision
    for index in range(1, artifact_count + 1):
        prepared = prepare_artifact_pages(
            PrepareArtifactPagesRequest(
                class_id=CLASS_ID,
                activity_id=ACTIVITY_ID,
                artifact_instance_id=f"artifact-{index:03}",
                template_version_id="template-issue106-batch",
                artifact_category="observation",
                expected_snapshot_revision=revision,
                actor=_actor(),
                expected_return_status="return_not_expected",
                privacy_policy=_privacy(),
                pages=(
                    ArtifactPagePlan(
                        page_number=1,
                        page_kind="observation",
                        return_expected=False,
                        route_required=False,
                    ),
                ),
            ),
            workspace_root=root,
            clock=_clock,
        )
        revision = prepared.commit.snapshot_revision

    created_provenance = provenance(_actor(), clock=_clock)
    author_ids: list[str] = []
    subject_ids: list[str] = []
    records: list[ArtifactAuthor | ArtifactSubject] = []
    for index in range(1, artifact_count + 1):
        artifact_id = f"artifact-{index:03}"
        student_id = f"student-{index:03}"
        author_id = f"author-{index:03}"
        subject_id = f"subject-{index:03}"
        author_ids.append(author_id)
        subject_ids.append(subject_id)
        records.append(
            ArtifactAuthor(
                artifact_author_id=author_id,
                artifact_instance_id=artifact_id,
                author_reference=_student_author(student_id),
                authorship_mode="individual_author",
                attribution_status="proposed",
                attribution_source="teacher",
                created_provenance=created_provenance,
                privacy_policy=_privacy(),
            )
        )
        records.append(
            ArtifactSubject(
                artifact_subject_id=subject_id,
                artifact_instance_id=artifact_id,
                subject_reference=_student_subject(student_id),
                subject_role="observed_participant",
                confirmation_status="proposed",
                assignment_source="teacher",
                created_provenance=created_provenance,
                privacy_policy=_privacy(),
            )
        )

    seeded = commit_record_batch(
        root,
        _work(),
        tuple(records),
        expected_snapshot_revision=revision,
    )
    return root, seeded.snapshot_revision, tuple(author_ids), tuple(subject_ids)


def _counted_batch(
    monkeypatch: pytest.MonkeyPatch,
    request: BatchConfirmArtifactAttributionRequest,
    root: Path,
) -> tuple[object, dict[str, int]]:
    calls = {"load": 0, "commit": 0}
    real_load = attribution.load_graph
    real_commit = attribution.commit_record_batch

    def counted_load(*args: object, **kwargs: object) -> object:
        calls["load"] += 1
        return real_load(*args, **kwargs)

    def counted_commit(*args: object, **kwargs: object) -> object:
        calls["commit"] += 1
        return real_commit(*args, **kwargs)

    monkeypatch.setattr(attribution, "load_graph", counted_load)
    monkeypatch.setattr(attribution, "commit_record_batch", counted_commit)
    result = batch_confirm_artifact_attribution(
        request,
        workspace_root=root,
    )
    return result, calls


def test_issue106_activity_wide_40_relationships_use_one_load_and_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision, author_ids, subject_ids = _workspace_with_proposals(
        tmp_path,
        20,
    )
    review = inspect_artifact_attribution_review(
        CLASS_ID,
        ACTIVITY_ID,
        workspace_root=root,
    )
    assert review.snapshot_revision == revision
    assert review.candidate_count == 40
    assert len(review.candidate_author_ids) == 20
    assert len(review.candidate_subject_ids) == 20
    assert set(review.candidate_author_ids) == set(author_ids)
    assert set(review.candidate_subject_ids) == set(subject_ids)

    before = load_current_record_graph(root, _work())
    before_authors = {
        item.artifact_author_id: item for item in before.graph.artifact_authors
    }
    before_subjects = {
        item.artifact_subject_id: item for item in before.graph.artifact_subjects
    }

    result, calls = _counted_batch(
        monkeypatch,
        BatchConfirmArtifactAttributionRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_author_ids=review.candidate_author_ids,
            artifact_subject_ids=review.candidate_subject_ids,
            expected_snapshot_revision=review.snapshot_revision,
            actor=_actor(),
        ),
        root,
    )

    assert calls == {"load": 1, "commit": 1}
    assert result.confirmed_author_count == 20
    assert result.confirmed_subject_count == 20
    assert result.commit.snapshot_revision == revision + 1
    assert len(result.commit.changed_records) == 40

    after = load_current_record_graph(root, _work())
    after_authors = {
        item.artifact_author_id: item for item in after.graph.artifact_authors
    }
    after_subjects = {
        item.artifact_subject_id: item for item in after.graph.artifact_subjects
    }
    for author_id in author_ids:
        assert after_authors[author_id] == replace(
            before_authors[author_id],
            attribution_status="confirmed",
        )
    for subject_id in subject_ids:
        assert after_subjects[subject_id] == replace(
            before_subjects[subject_id],
            confirmation_status="confirmed",
        )
    assert after.graph.correction_records == ()
    assert after.graph.artifact_reviews == ()
    assert after.graph.moderation_records == ()
    assert after.graph.score_records == ()
    assert after.graph.score_evidence_links == ()

    collection = inspect_artifact_collection_state(
        CLASS_ID,
        ACTIVITY_ID,
        "artifact-001",
        workspace_root=root,
    )
    assert not collection.author_confirmation_pending
    assert not collection.subject_confirmation_pending


def test_issue106_one_relationship_has_same_one_load_one_commit_shape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision, author_ids, subject_ids = _workspace_with_proposals(
        tmp_path,
        1,
    )
    result, calls = _counted_batch(
        monkeypatch,
        BatchConfirmArtifactAttributionRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_author_ids=(author_ids[0],),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        root,
    )

    assert calls == {"load": 1, "commit": 1}
    assert result.confirmed_author_count == 1
    assert result.confirmed_subject_count == 0
    assert len(result.commit.changed_records) == 1
    after = load_current_record_graph(root, _work())
    author = next(
        item
        for item in after.graph.artifact_authors
        if item.artifact_author_id == author_ids[0]
    )
    subject = next(
        item
        for item in after.graph.artifact_subjects
        if item.artifact_subject_id == subject_ids[0]
    )
    assert author.attribution_status == "confirmed"
    assert subject.confirmation_status == "proposed"
