from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    ActorReference,
    EffectiveContext,
    EvidenceReference,
    ParticipantReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.storage import load_current_record_graph
from concord.workflows import (
    AddArtifactAuthorRequest,
    AddArtifactReviewRequest,
    AddArtifactSubjectRequest,
    AddModerationRecordRequest,
    ArtifactPagePlan,
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    PrepareArtifactPagesRequest,
    ReplaceArtifactAuthorRequest,
    ReplaceArtifactReviewRequest,
    WorkflowActor,
    add_artifact_author,
    add_artifact_review,
    add_artifact_subject,
    add_moderation_record,
    create_activity_context,
    create_group_with_members,
    list_applicable_moderation_records,
    prepare_artifact_pages,
    replace_artifact_author,
    replace_artifact_review,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 20, 0, tzinfo=timezone.utc)


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


def _student(student_id: str) -> ParticipantReference:
    return ParticipantReference(
        participant_kind="core_student",
        participant_id=student_id,
        owning_system="core",
    )


def _subject(student_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _workspace(
    tmp_path: Path,
    *,
    artifact_id: str = "artifact-1",
    page_count: int = 1,
) -> tuple[Path, int]:
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
                {
                    "student_id": "student-2",
                    "last_name": "Two",
                    "first_name": "Blair",
                    "period": "1",
                },
                {
                    "student_id": "student-3",
                    "last_name": "Three",
                    "first_name": "Casey",
                    "period": "1",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Issue 29 representative cases",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    context = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )
    group = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=context,
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=context,
                ),
                GroupMemberSpec(
                    membership_id="membership-2",
                    student_id="student-2",
                    effective_context=context,
                ),
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id=artifact_id,
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=group.commit.snapshot_revision,
            actor=_actor(),
            pages=tuple(
                ArtifactPagePlan(
                    page_number=index,
                    artifact_page_id=f"{artifact_id}-page-{index}",
                    return_expected=True,
                    route_required=False,
                )
                for index in range(1, page_count + 1)
            ),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    return root, prepared.commit.snapshot_revision


def test_peer_observation_keeps_author_subject_review_and_moderation_separate(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-observer",
            author_reference=_student("student-1"),
            authorship_mode="observer",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    subject = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-observed",
            subject_reference=_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=author.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    review = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_review_id="review-peer",
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="confirmed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="required",
            scoring_readiness="not_ready",
            review_outcome="moderation_required",
            privacy_policy=_privacy(),
            expected_snapshot_revision=subject.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
        moderation_requirement="not_required",
    )
    moderated = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-peer",
            target_evidence_reference=evidence,
            target_subject_references=(_subject("student-2"),),
            status="accepted_with_qualification",
            permitted_use="support_named_subject",
            rationale="The peer observation is specific and corroborated.",
            qualification="Use only for the explicitly named observed student.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=review.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    graph = load_current_record_graph(root, _work()).graph
    assert graph.artifact_authors[0].author_reference == _student("student-1")
    assert graph.artifact_subjects[0].subject_reference == _subject("student-2")
    assert graph.artifact_reviews[0].moderation_requirement == "required"
    assert graph.moderation_records[0].target_subject_references == (
        _subject("student-2"),
    )
    assert moderated.commit.snapshot_revision == review.commit.snapshot_revision + 1
    assert not graph.score_records
    assert not graph.score_evidence_links


def test_recorder_for_group_does_not_infer_moderation_subject_scope(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-recorder",
            author_reference=_student("student-1"),
            authorship_mode="recorder_for_group",
            attribution_status="confirmed",
            attribution_source="teacher",
            represented_group_id="group-a",
            representation_status="recorder_summary",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    moderated = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-group",
            target_evidence_reference=evidence,
            target_subject_references=(
                SubjectReference(
                    subject_kind="concord_group",
                    subject_id="group-a",
                    owning_system="concord",
                ),
            ),
            status="accepted",
            permitted_use="support_group_score",
            rationale="The recorder summary is sufficiently representative.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=author.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    graph = load_current_record_graph(root, _work()).graph
    assert graph.artifact_authors[0].represented_group_id == "group-a"
    assert graph.moderation_records[0].target_subject_references == (
        SubjectReference(
            subject_kind="concord_group",
            subject_id="group-a",
            owning_system="concord",
        ),
    )
    assert moderated.commit.snapshot_revision == author.commit.snapshot_revision + 1


def test_teacher_tracker_can_concern_several_students_without_student_author(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-teacher",
            author_reference=ActorReference(
                actor_kind="authorized_adult",
                actor_id="teacher-1",
                owning_system="concord",
                display_label_snapshot="Synthetic Teacher",
            ),
            authorship_mode="teacher_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    first = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-1",
            subject_reference=_subject("student-1"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=author.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    second = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-2",
            subject_reference=_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    review = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_review_id="review-tracker",
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
            expected_snapshot_revision=second.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    graph = load_current_record_graph(root, _work()).graph
    assert isinstance(graph.artifact_authors[0].author_reference, ActorReference)
    assert {item.subject_reference.subject_id for item in graph.artifact_subjects} == {
        "student-1",
        "student-2",
    }
    assert review.commit.snapshot_revision == second.commit.snapshot_revision + 1
    assert not graph.score_records


def test_attribution_dispute_and_correction_do_not_rewrite_review_history(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-before",
            author_reference=_student("student-1"),
            authorship_mode="individual_author",
            attribution_status="disputed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    review = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_review_id="review-before",
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="disputed",
            subject_judgment="not_reviewed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="not_required",
            scoring_readiness="not_ready",
            review_outcome="awaiting_correction",
            notes="Authorship requires correction.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=author.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    corrected = replace_artifact_author(
        ReplaceArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_id="author-before",
            replacement_artifact_author_id="author-after",
            correction_id="correction-author",
            reason="The original authorship attribution was incorrect.",
            author_reference=_student("student-2"),
            authorship_mode="individual_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=review.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    successor = replace_artifact_review(
        ReplaceArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_review_id="review-before",
            replacement_artifact_review_id="review-after",
            correction_id="correction-review",
            reason="Authorship correction completed.",
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="not_reviewed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="not_required",
            scoring_readiness="ready",
            review_outcome="ready",
            privacy_policy=_privacy(),
            expected_snapshot_revision=corrected.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    graph = load_current_record_graph(root, _work()).graph
    assert len(graph.artifact_authors) == 2
    assert len(graph.artifact_reviews) == 2
    assert {item.correction_type for item in graph.correction_records} == {
        "author_correction",
        "review_correction",
    }
    assert successor.commit.snapshot_revision == corrected.commit.snapshot_revision + 1


def test_incomplete_evidence_review_can_receive_successor_without_artifact_mutation(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path, page_count=2)
    before = load_current_record_graph(root, _work()).graph.artifact_instances[0]
    first = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_review_id="review-incomplete",
            readability_judgment="readable",
            page_completeness_judgment="incomplete",
            filing_judgment="correct",
            author_judgment="not_reviewed",
            subject_judgment="not_reviewed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="not_required",
            scoring_readiness="not_ready",
            review_outcome="awaiting_additional_evidence",
            notes="One or more expected physical pages are still unavailable.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    second = replace_artifact_review(
        ReplaceArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_review_id="review-incomplete",
            replacement_artifact_review_id="review-followup",
            correction_id="correction-review-followup",
            reason="Additional evidence was checked by the teacher.",
            readability_judgment="readable",
            page_completeness_judgment="partially_complete",
            filing_judgment="correct",
            author_judgment="not_reviewed",
            subject_judgment="not_reviewed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="not_required",
            scoring_readiness="not_ready",
            review_outcome="incomplete",
            notes="Evidence remains administratively incomplete.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    graph = load_current_record_graph(root, _work()).graph
    after = graph.artifact_instances[0]
    assert before == after
    assert len(graph.artifact_reviews) == 2
    assert second.commit.snapshot_revision == first.commit.snapshot_revision + 1


def test_same_evidence_can_have_two_independent_subject_scopes(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    first = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-student-1",
            target_evidence_reference=evidence,
            target_subject_references=(_subject("student-1"),),
            status="accepted",
            permitted_use="support_named_subject",
            rationale="Applicable to the first student.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    second = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-student-2",
            target_evidence_reference=evidence,
            target_subject_references=(_subject("student-2"),),
            status="insufficient",
            permitted_use="corroborate_only",
            rationale="Insufficient for an independent judgment about student two.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    first_scope = list_applicable_moderation_records(
        "class-1",
        "activity-1",
        evidence,
        subject_context=(_subject("student-1"),),
        workspace_root=root,
    )
    second_scope = list_applicable_moderation_records(
        "class-1",
        "activity-1",
        evidence,
        subject_context=(_subject("student-2"),),
        workspace_root=root,
    )
    assert [item.moderation_record_id for item in first_scope] == [
        "moderation-student-1"
    ]
    assert [item.moderation_record_id for item in second_scope] == [
        "moderation-student-2"
    ]
    assert second.commit.snapshot_revision == first.commit.snapshot_revision + 1
