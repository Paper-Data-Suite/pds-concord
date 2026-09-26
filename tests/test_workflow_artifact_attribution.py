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

import concord.workflows.artifact_attribution_review as attribution_review
from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import (
    ActorReference,
    ArtifactAuthor,
    ConcordModelError,
    ConcordRecordReference,
    EffectiveContext,
    ParticipantReference,
    PrivacyPolicy,
    Provenance,
    SubjectReference,
)
from concord.storage import list_record_revisions, load_current_record_graph
from concord.workflows import (
    AddArtifactAuthorRequest,
    AddArtifactAuthorsRequest,
    AddArtifactSubjectRequest,
    AddArtifactSubjectsRequest,
    ArtifactPagePlan,
    BatchConfirmArtifactAttributionRequest,
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    GroupRoleSpec,
    PrepareArtifactPagesRequest,
    ReplaceArtifactAuthorRequest,
    ReplaceArtifactSubjectRequest,
    UpdateArtifactAuthorRequest,
    UpdateArtifactSubjectRequest,
    WorkflowActor,
    add_artifact_author,
    add_artifact_authors,
    add_artifact_subject,
    add_artifact_subjects,
    batch_confirm_artifact_attribution,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
    inspect_artifact_attribution_review,
    list_artifact_authors,
    list_artifact_subjects,
    prepare_artifact_pages,
    replace_artifact_author,
    replace_artifact_subject,
    show_artifact_author,
    show_artifact_subject,
    update_artifact_author,
    update_artifact_subject,
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


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )


def _workspace_with_artifact(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(1),
    )
    write_class_metadata_for_class(root, metadata)
    roster = create_roster(
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
    )
    write_class_roster(root, roster)
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Observation Activity",
            activity_type="socratic_seminar",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
            session_label="Session One",
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    student_one = core_student_participant(root, "class-1", "student-1")
    grouped = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=_context(),
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=_context(),
                ),
                GroupMemberSpec(
                    membership_id="membership-2",
                    student_id="student-2",
                    effective_context=_context(),
                ),
            ),
            roles=(
                GroupRoleSpec(
                    role_assignment_id="role-recorder",
                    participant_reference=student_one,
                    role_key="recorder",
                    effective_context=_context(),
                    membership_id="membership-1",
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
            artifact_instance_id="artifact-1",
            template_version_id="template-v1",
            artifact_category="observation",
            expected_snapshot_revision=grouped.commit.snapshot_revision,
            actor=_actor(),
            expected_return_status="return_not_expected",
            privacy_policy=_privacy(),
            group_id="group-a",
            session_id="session-1",
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
        clock=lambda: _clock(4),
    )
    return root, prepared.commit.snapshot_revision


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


def test_unknown_author_round_trips_without_placeholder_identity() -> None:
    provenance = Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp=_clock(1).isoformat(),
        source_kind="manual",
    )
    author = ArtifactAuthor(
        artifact_author_id="author-unknown",
        artifact_instance_id="artifact-1",
        authorship_mode="unknown",
        attribution_status="unknown",
        attribution_source="teacher",
        created_provenance=provenance,
    )
    data = record_to_dict(author)
    assert "author_reference" not in data
    assert record_from_dict("artifact_author", data) == author

    with pytest.raises(ConcordModelError, match="require an author_reference"):
        ArtifactAuthor(
            artifact_author_id="author-invalid",
            artifact_instance_id="artifact-1",
            authorship_mode="individual_author",
            attribution_status="proposed",
            attribution_source="teacher",
            created_provenance=provenance,
        )
    with pytest.raises(ConcordModelError, match="unknown authorship"):
        ArtifactAuthor(
            artifact_author_id="author-invalid-2",
            artifact_instance_id="artifact-1",
            author_reference=_student_author("student-1"),
            authorship_mode="unknown",
            attribution_status="unknown",
            attribution_source="teacher",
            created_provenance=provenance,
        )


def test_author_add_list_show_update_and_duplicate_guard(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    assert list_artifact_authors(
        "class-1", "activity-1", workspace_root=root
    ) == ()

    added = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-1",
            author_reference=_student_author("student-1"),
            authorship_mode="observer",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    listed = list_artifact_authors(
        "class-1",
        "activity-1",
        artifact_instance_id="artifact-1",
        workspace_root=root,
    )
    assert len(listed) == 1
    assert listed[0].reference_display_label == "Alex One"
    assert listed[0].is_current

    updated = update_artifact_author(
        UpdateArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_id="author-1",
            attribution_status="confirmed",
            expected_snapshot_revision=added.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    assert show_artifact_author(
        "class-1", "activity-1", "author-1", workspace_root=root
    ).attribution_status == "confirmed"
    assert list_record_revisions(root, _work(), "artifact_author", "author-1") == (
        1,
        2,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="equivalent current"):
        add_artifact_author(
            AddArtifactAuthorRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_author_id="author-duplicate",
                author_reference=_student_author("student-1"),
                authorship_mode="observer",
                attribution_status="confirmed",
                attribution_source="teacher",
                expected_snapshot_revision=updated.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_author_reference_modes_and_role_context_are_explicit(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    recorder = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-recorder",
            author_reference=_student_author("student-1"),
            authorship_mode="recorder_for_group",
            attribution_status="confirmed",
            attribution_source="teacher",
            represented_group_id="group-a",
            role_assignment_id="role-recorder",
            representation_status="recorder_summary",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert recorder.association_id == "author-recorder"

    collective = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-group",
            author_reference=ConcordRecordReference(
                record_kind="group",
                record_id="group-a",
            ),
            authorship_mode="collective_group_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            representation_status="unanimous_position",
            expected_snapshot_revision=recorder.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    teacher = add_artifact_author(
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
                role_snapshot="teacher",
            ),
            authorship_mode="teacher_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=collective.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    labels = {
        item.artifact_author_id: item.reference_display_label
        for item in list_artifact_authors(
            "class-1", "activity-1", workspace_root=root
        )
    }
    assert labels["author-group"] == "Group A"
    assert labels["author-teacher"] == "Synthetic Teacher"
    assert teacher.commit.snapshot_revision > revision

    with pytest.raises(ConcordWorkflowValidationError, match="participant differ"):
        add_artifact_author(
            AddArtifactAuthorRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_author_id="author-role-mismatch",
                author_reference=_student_author("student-2"),
                authorship_mode="recorder_for_group",
                attribution_status="confirmed",
                attribution_source="teacher",
                represented_group_id="group-a",
                role_assignment_id="role-recorder",
                representation_status="recorder_summary",
                expected_snapshot_revision=teacher.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_unknown_author_can_be_replaced_without_rewriting_history(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    unknown = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-unknown",
            authorship_mode="unknown",
            attribution_status="unknown",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    replaced = replace_artifact_author(
        ReplaceArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_id="author-unknown",
            replacement_artifact_author_id="author-known",
            correction_id="correction-author-1",
            reason="Returned page identifies the student observer.",
            author_reference=_student_author("student-1"),
            authorship_mode="observer",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=unknown.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    current = list_artifact_authors(
        "class-1", "activity-1", workspace_root=root
    )
    assert [item.artifact_author_id for item in current] == ["author-known"]
    history = list_artifact_authors(
        "class-1",
        "activity-1",
        include_historical=True,
        workspace_root=root,
    )
    by_id = {item.artifact_author_id: item for item in history}
    assert not by_id["author-unknown"].is_current
    assert by_id["author-known"].is_current
    assert by_id["author-known"].supersedes_artifact_author_id == "author-unknown"

    loaded = load_current_record_graph(root, _work())
    assert len(loaded.graph.correction_records) == 1
    correction = loaded.graph.correction_records[0]
    assert correction.correction_type == "author_correction"
    assert correction.target_reference.record_id == "author-unknown"
    assert correction.replacement_reference is not None
    assert correction.replacement_reference.record_id == "author-known"
    assert loaded.graph.artifact_reviews == ()
    assert loaded.graph.score_records == ()
    assert replaced.commit.snapshot_revision == loaded.snapshot_revision


def test_roster_and_membership_do_not_establish_authorship(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    assert list_artifact_authors(
        "class-1", "activity-1", workspace_root=root
    ) == ()
    with pytest.raises(ConcordWorkflowNotFoundError, match="Student"):
        add_artifact_author(
            AddArtifactAuthorRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_author_id="author-invalid-student",
                author_reference=_student_author("group-a"),
                authorship_mode="individual_author",
                attribution_status="confirmed",
                attribution_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    assert list_artifact_authors(
        "class-1", "activity-1", workspace_root=root
    ) == ()


def test_subjects_are_independent_many_to_one_associations(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    first = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-student",
            subject_reference=_student_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="proposed",
            assignment_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    second = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-group",
            subject_reference=SubjectReference(
                subject_kind="concord_group",
                subject_id="group-a",
                owning_system="concord",
            ),
            subject_role="represented_group",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    subjects = list_artifact_subjects(
        "class-1",
        "activity-1",
        artifact_instance_id="artifact-1",
        workspace_root=root,
    )
    assert {item.artifact_subject_id for item in subjects} == {
        "subject-student",
        "subject-group",
    }
    assert {item.reference_display_label for item in subjects} == {
        "Blair Two",
        "Group A",
    }
    loaded = load_current_record_graph(root, _work())
    assert len(loaded.graph.artifact_instances) == 1
    assert len(loaded.graph.artifact_pages) == 1
    assert loaded.graph.artifact_authors == ()
    assert loaded.graph.score_records == ()
    assert second.commit.snapshot_revision == loaded.snapshot_revision


def test_subject_reference_and_role_semantics_are_validated(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    with pytest.raises(ConcordWorkflowNotFoundError, match="Student"):
        add_artifact_subject(
            AddArtifactSubjectRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_subject_id="subject-fake-student",
                subject_reference=_student_subject("group-a"),
                subject_role="observed_participant",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    with pytest.raises(ConcordWorkflowValidationError, match="represented_group"):
        add_artifact_subject(
            AddArtifactSubjectRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_subject_id="subject-role-mismatch",
                subject_reference=_student_subject("student-1"),
                subject_role="represented_group",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    with pytest.raises(ConcordWorkflowValidationError, match="Concord-owned"):
        add_artifact_subject(
            AddArtifactSubjectRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_subject_id="subject-fake-external",
                subject_reference=SubjectReference(
                    subject_kind="external_record",
                    subject_id="record-1",
                    owning_system="concord",
                ),
                subject_role="general_subject",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_subject_status_update_and_semantic_replacement_preserve_history(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    added = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-1",
            subject_reference=_student_subject("student-1"),
            subject_role="observed_participant",
            confirmation_status="proposed",
            assignment_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    updated = update_artifact_subject(
        UpdateArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_subject_id="subject-1",
            confirmation_status="confirmed",
            expected_snapshot_revision=added.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    assert show_artifact_subject(
        "class-1", "activity-1", "subject-1", workspace_root=root
    ).confirmation_status == "confirmed"

    replaced = replace_artifact_subject(
        ReplaceArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_subject_id="subject-1",
            replacement_artifact_subject_id="subject-2",
            correction_id="correction-subject-1",
            reason="Teacher corrected the observed participant.",
            subject_reference=_student_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=updated.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    assert [
        item.artifact_subject_id
        for item in list_artifact_subjects(
            "class-1", "activity-1", workspace_root=root
        )
    ] == ["subject-2"]
    history = list_artifact_subjects(
        "class-1",
        "activity-1",
        include_historical=True,
        workspace_root=root,
    )
    by_id = {item.artifact_subject_id: item for item in history}
    assert not by_id["subject-1"].is_current
    assert by_id["subject-2"].is_current
    assert by_id["subject-2"].supersedes_artifact_subject_id == "subject-1"
    loaded = load_current_record_graph(root, _work())
    correction = next(
        item
        for item in loaded.graph.correction_records
        if item.correction_id == "correction-subject-1"
    )
    assert correction.correction_type == "subject_correction"
    assert correction.replacement_reference is not None
    assert correction.replacement_reference.record_id == "subject-2"
    assert replaced.commit.snapshot_revision == loaded.snapshot_revision


def test_subject_context_kinds_do_not_collapse_into_student_identity(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    cases = (
        (
            "subject-session",
            SubjectReference(
                subject_kind="concord_session",
                subject_id="session-1",
                owning_system="concord",
            ),
            "session_context",
        ),
        (
            "subject-activity",
            SubjectReference(
                subject_kind="concord_activity",
                subject_id="activity-1",
                owning_system="concord",
            ),
            "activity_context",
        ),
        (
            "subject-artifact",
            SubjectReference(
                subject_kind="concord_artifact_instance",
                subject_id="artifact-1",
                owning_system="concord",
            ),
            "evaluated_artifact",
        ),
        (
            "subject-external",
            SubjectReference(
                subject_kind="external_record",
                subject_id="external-1",
                owning_system="scoreform",
                contract_version="1",
            ),
            "general_subject",
        ),
    )
    current_revision = revision
    for index, (subject_id, reference, role) in enumerate(cases, start=5):
        result = add_artifact_subject(
            AddArtifactSubjectRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_subject_id=subject_id,
                subject_reference=reference,
                subject_role=role,
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=current_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda index=index: _clock(index),
        )
        current_revision = result.commit.snapshot_revision
    subjects = list_artifact_subjects(
        "class-1", "activity-1", workspace_root=root
    )
    assert {item.subject_reference.subject_kind for item in subjects} == {
        "concord_session",
        "concord_activity",
        "concord_artifact_instance",
        "external_record",
    }


def test_superseded_status_requires_replacement_workflow(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-1",
            author_reference=_student_author("student-1"),
            authorship_mode="individual_author",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    with pytest.raises(ConcordWorkflowValidationError, match="replacement"):
        update_artifact_author(
            UpdateArtifactAuthorRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_author_id="author-1",
                attribution_status="superseded",
                expected_snapshot_revision=author.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
def test_coauthors_recorder_and_authorized_adult_are_distinct_authors(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    requests = (
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-co-1",
            author_reference=_student_author("student-1"),
            authorship_mode="co_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-co-2",
            author_reference=_student_author("student-2"),
            authorship_mode="co_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=0,
            actor=_actor(),
        ),
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-recorder-individual",
            author_reference=_student_author("student-3"),
            authorship_mode="recorder",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=0,
            actor=_actor(),
        ),
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-adult",
            author_reference=ActorReference(
                actor_kind="authorized_adult",
                actor_id="adult-2",
                owning_system="concord",
                display_label_snapshot="Synthetic Adult",
            ),
            authorship_mode="authorized_adult_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=0,
            actor=_actor(),
        ),
    )
    current_revision = revision
    for index, request in enumerate(requests, start=5):
        result = add_artifact_author(
            replace(request, expected_snapshot_revision=current_revision),
            workspace_root=root,
            clock=lambda index=index: _clock(index),
        )
        current_revision = result.commit.snapshot_revision
    authors = list_artifact_authors(
        "class-1", "activity-1", workspace_root=root
    )
    assert {item.authorship_mode for item in authors} == {
        "co_author",
        "recorder",
        "authorized_adult_author",
    }
    assert sum(item.authorship_mode == "co_author" for item in authors) == 2
    assert list_artifact_subjects(
        "class-1", "activity-1", workspace_root=root
    ) == ()


def test_multiple_student_subjects_other_artifact_and_duplicate_guard(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    second_artifact = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-2",
            template_version_id="template-v1",
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
        clock=lambda: _clock(5),
    )
    first = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-student-1",
            subject_reference=_student_subject("student-1"),
            subject_role="observed_participant",
            confirmation_status="proposed",
            assignment_source="teacher",
            expected_snapshot_revision=second_artifact.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    second = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-student-2",
            subject_reference=_student_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    other_artifact = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-artifact-2",
            subject_reference=SubjectReference(
                subject_kind="concord_artifact_instance",
                subject_id="artifact-2",
                owning_system="concord",
            ),
            subject_role="evaluated_artifact",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=second.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(8),
    )
    disputed = update_artifact_subject(
        UpdateArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_subject_id="subject-student-1",
            confirmation_status="unresolved",
            expected_snapshot_revision=other_artifact.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(9),
    )
    with pytest.raises(ConcordWorkflowConflictError, match="equivalent current"):
        add_artifact_subject(
            AddArtifactSubjectRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                artifact_subject_id="subject-duplicate",
                subject_reference=_student_subject("student-2"),
                subject_role="observed_participant",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=disputed.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    subjects = list_artifact_subjects(
        "class-1", "activity-1", workspace_root=root
    )
    assert len(subjects) == 3
    assert {
        item.subject_reference.subject_id
        for item in subjects
    } == {"student-1", "student-2", "artifact-2"}
    loaded = load_current_record_graph(root, _work())
    assert len(loaded.graph.artifact_instances) == 2
    assert loaded.graph.scan_references == ()
    assert loaded.graph.artifact_authors == ()


def test_peer_observation_and_self_reflection_keep_author_subject_separate(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    observer = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-observer",
            author_reference=_student_author("student-1"),
            authorship_mode="observer",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    observed = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-observed",
            subject_reference=_student_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=observer.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    self_subject = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-self",
            subject_reference=_student_subject("student-1"),
            subject_role="general_subject",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=observed.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    loaded = load_current_record_graph(root, _work())
    assert loaded.snapshot_revision == self_subject.commit.snapshot_revision
    author = loaded.graph.artifact_authors[0]
    subjects = loaded.graph.artifact_subjects
    assert author.author_reference == _student_author("student-1")
    assert {item.subject_reference.subject_id for item in subjects} == {
        "student-1",
        "student-2",
    }
    assert len(loaded.graph.artifact_instances) == 1


def _issue106_proposed_attribution_set(root: Path, revision: int) -> int:
    author_one = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-batch-1",
            author_reference=_student_author("student-1"),
            authorship_mode="observer",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(10),
    )
    author_two = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-batch-2",
            author_reference=_student_author("student-2"),
            authorship_mode="observer",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=author_one.commit.snapshot_revision,
            actor=_actor(),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(11),
    )
    subject_one = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-batch-1",
            subject_reference=_student_subject("student-2"),
            subject_role="observed_participant",
            confirmation_status="proposed",
            assignment_source="teacher",
            expected_snapshot_revision=author_two.commit.snapshot_revision,
            actor=_actor(),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(12),
    )
    subject_two = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-batch-2",
            subject_reference=_student_subject("student-3"),
            subject_role="observed_participant",
            confirmation_status="proposed",
            assignment_source="teacher",
            expected_snapshot_revision=subject_one.commit.snapshot_revision,
            actor=_actor(),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(13),
    )
    return subject_two.commit.snapshot_revision


def test_issue106_batch_confirmation_is_one_mixed_atomic_status_commit(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)
    before = load_current_record_graph(root, _work())
    before_authors = {
        item.artifact_author_id: item for item in before.graph.artifact_authors
    }
    before_subjects = {
        item.artifact_subject_id: item for item in before.graph.artifact_subjects
    }

    result = batch_confirm_artifact_attribution(
        BatchConfirmArtifactAttributionRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_ids=("author-batch-1", "author-batch-2"),
            artifact_subject_ids=("subject-batch-1", "subject-batch-2"),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    after = load_current_record_graph(root, _work())
    assert result.confirmed_author_count == 2
    assert result.confirmed_subject_count == 2
    assert result.commit.snapshot_revision == revision + 1
    assert after.snapshot_revision == result.commit.snapshot_revision
    assert len(result.commit.changed_records) == 4

    after_authors = {
        item.artifact_author_id: item for item in after.graph.artifact_authors
    }
    after_subjects = {
        item.artifact_subject_id: item for item in after.graph.artifact_subjects
    }
    for artifact_author_id in ("author-batch-1", "author-batch-2"):
        assert after_authors[artifact_author_id] == replace(
            before_authors[artifact_author_id],
            attribution_status="confirmed",
        )
        assert list_record_revisions(
            root,
            _work(),
            "artifact_author",
            artifact_author_id,
        ) == (1, 2)
    for artifact_subject_id in ("subject-batch-1", "subject-batch-2"):
        assert after_subjects[artifact_subject_id] == replace(
            before_subjects[artifact_subject_id],
            confirmation_status="confirmed",
        )
        assert list_record_revisions(
            root,
            _work(),
            "artifact_subject",
            artifact_subject_id,
        ) == (1, 2)

    assert after.graph.correction_records == ()
    assert after.graph.artifact_reviews == ()
    assert after.graph.score_records == ()


def test_issue106_batch_rejects_exception_without_partial_confirmation(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)
    disputed = update_artifact_author(
        UpdateArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_id="author-batch-2",
            attribution_status="disputed",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="proposed"):
        batch_confirm_artifact_attribution(
            BatchConfirmArtifactAttributionRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_author_ids=("author-batch-1", "author-batch-2"),
                expected_snapshot_revision=disputed.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == disputed.commit.snapshot_revision
    authors = {
        item.artifact_author_id: item for item in after.graph.artifact_authors
    }
    assert authors["author-batch-1"].attribution_status == "proposed"
    assert authors["author-batch-2"].attribution_status == "disputed"


def test_issue106_batch_is_bound_to_exact_expected_snapshot(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)
    advanced = update_artifact_subject(
        UpdateArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_subject_id="subject-batch-2",
            confirmation_status="disputed",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        batch_confirm_artifact_attribution(
            BatchConfirmArtifactAttributionRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_author_ids=("author-batch-1",),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == advanced.commit.snapshot_revision
    author = next(
        item
        for item in after.graph.artifact_authors
        if item.artifact_author_id == "author-batch-1"
    )
    assert author.attribution_status == "proposed"


def test_issue106_batch_requires_nonempty_unique_selection(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)

    with pytest.raises(ConcordWorkflowValidationError, match="At least one"):
        batch_confirm_artifact_attribution(
            BatchConfirmArtifactAttributionRequest(
                class_id="class-1",
                activity_id="activity-1",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    with pytest.raises(ConcordWorkflowValidationError, match="duplicate"):
        batch_confirm_artifact_attribution(
            BatchConfirmArtifactAttributionRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_author_ids=("author-batch-1", "author-batch-1"),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    assert load_current_record_graph(root, _work()).snapshot_revision == revision

def test_issue106_review_projection_separates_candidates_exceptions_and_resolved(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)
    disputed = update_artifact_author(
        UpdateArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_id="author-batch-2",
            attribution_status="disputed",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    unresolved = update_artifact_subject(
        UpdateArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_subject_id="subject-batch-2",
            confirmation_status="unresolved",
            expected_snapshot_revision=disputed.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    confirmed_author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-confirmed",
            author_reference=_student_author("student-3"),
            authorship_mode="observer",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=unresolved.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    confirmed_subject = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-confirmed",
            subject_reference=_student_subject("student-1"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=confirmed_author.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    review = inspect_artifact_attribution_review(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert review.snapshot_revision == confirmed_subject.commit.snapshot_revision
    assert review.candidate_author_ids == ("author-batch-1",)
    assert review.candidate_subject_ids == ("subject-batch-1",)
    assert review.candidate_count == 2
    assert review.exception_count == 2
    assert review.confirmed_author_count == 1
    assert review.confirmed_subject_count == 1
    assert review.confirmed_relationship_count == 2
    assert len(review.artifacts) == 1

    group = review.artifacts[0]
    assert group.artifact_instance_id == "artifact-1"
    assert tuple(item.artifact_author_id for item in group.authors) == (
        "author-batch-1",
        "author-batch-2",
    )
    assert tuple(item.artifact_subject_id for item in group.subjects) == (
        "subject-batch-1",
        "subject-batch-2",
    )
    author_rows = {item.artifact_author_id: item for item in group.authors}
    subject_rows = {item.artifact_subject_id: item for item in group.subjects}
    assert author_rows["author-batch-1"].disposition == "candidate"
    assert author_rows["author-batch-2"].exception_code == "disputed"
    assert subject_rows["subject-batch-1"].disposition == "candidate"
    assert subject_rows["subject-batch-2"].exception_code == "unresolved"
    assert "author-confirmed" not in author_rows
    assert "subject-confirmed" not in subject_rows


def test_issue106_review_projection_revalidates_proposed_roster_semantics(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)
    reduced_roster = create_roster(
        "class-1",
        (
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
    )
    write_class_roster(root, reduced_roster, overwrite=True)

    review = inspect_artifact_attribution_review(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert review.snapshot_revision == revision
    assert "author-batch-1" not in review.candidate_author_ids
    assert review.candidate_author_ids == ("author-batch-2",)
    author_rows = {
        item.artifact_author_id: item
        for group in review.artifacts
        for item in group.authors
    }
    invalid = author_rows["author-batch-1"]
    assert invalid.disposition == "exception"
    assert invalid.exception_code == "semantic_invalid"
    assert invalid.exception_message is not None
    assert "Core roster" in invalid.exception_message


def test_issue106_review_projection_uses_one_exact_activity_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    revision = _issue106_proposed_attribution_set(root, revision)
    real_load = attribution_review.load_activity_read_context
    calls = 0

    def counted_load(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return real_load(*args, **kwargs)

    monkeypatch.setattr(
        attribution_review,
        "load_activity_read_context",
        counted_load,
    )

    review = inspect_artifact_attribution_review(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert calls == 1
    assert review.snapshot_revision == revision
    assert review.candidate_author_ids == (
        "author-batch-1",
        "author-batch-2",
    )
    assert review.candidate_subject_ids == (
        "subject-batch-1",
        "subject-batch-2",
    )


def test_issue106_review_projection_excludes_historical_attribution(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    first = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-historical",
            author_reference=_student_author("student-1"),
            authorship_mode="observer",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    replacement = replace_artifact_author(
        ReplaceArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_id="author-historical",
            replacement_artifact_author_id="author-current",
            correction_id="correction-issue106-review",
            reason="Correct the observer identity.",
            author_reference=_student_author("student-3"),
            authorship_mode="observer",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    review = inspect_artifact_attribution_review(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert review.snapshot_revision == replacement.commit.snapshot_revision
    assert review.candidate_author_ids == ("author-current",)
    visible_ids = {
        item.artifact_author_id
        for group in review.artifacts
        for item in group.authors
    }
    assert "author-historical" not in visible_ids

def test_issue106_multi_add_authors_is_one_atomic_commit(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)

    result = add_artifact_authors(
        AddArtifactAuthorsRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            student_ids=("student-1", "student-2", "student-3"),
            authorship_mode="co_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(20),
    )

    after = load_current_record_graph(root, _work())
    assert result.commit.snapshot_revision == revision + 1
    assert after.snapshot_revision == result.commit.snapshot_revision
    assert len(result.commit.changed_records) == 3
    assert len(result.artifact_author_ids) == 3
    assert len(set(result.artifact_author_ids)) == 3
    assert all(item.startswith("author_") for item in result.artifact_author_ids)

    authors = {
        item.author_reference.participant_id: item
        for item in after.graph.artifact_authors
        if isinstance(item.author_reference, ParticipantReference)
    }
    assert set(authors) == {"student-1", "student-2", "student-3"}
    for student_id, author in authors.items():
        assert author.artifact_author_id in result.artifact_author_ids
        assert author.artifact_instance_id == "artifact-1"
        assert author.author_reference == _student_author(student_id)
        assert author.authorship_mode == "co_author"
        assert author.attribution_status == "confirmed"
        assert author.attribution_source == "teacher"
        assert author.privacy_policy == _privacy()
        assert author.created_provenance.timestamp == _clock(20).isoformat()
        assert list_record_revisions(
            root,
            _work(),
            "artifact_author",
            author.artifact_author_id,
        ) == (1,)

    assert after.graph.artifact_subjects == ()
    assert after.graph.correction_records == ()
    assert after.graph.artifact_reviews == ()
    assert after.graph.score_records == ()


def test_issue106_multi_add_subjects_is_one_atomic_commit(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)

    result = add_artifact_subjects(
        AddArtifactSubjectsRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            student_ids=("student-1", "student-2", "student-3"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
        clock=lambda: _clock(21),
    )

    after = load_current_record_graph(root, _work())
    assert result.commit.snapshot_revision == revision + 1
    assert after.snapshot_revision == result.commit.snapshot_revision
    assert len(result.commit.changed_records) == 3
    assert len(result.artifact_subject_ids) == 3
    assert len(set(result.artifact_subject_ids)) == 3
    assert all(item.startswith("subject_") for item in result.artifact_subject_ids)

    subjects = {
        item.subject_reference.subject_id: item
        for item in after.graph.artifact_subjects
    }
    assert set(subjects) == {"student-1", "student-2", "student-3"}
    for student_id, subject in subjects.items():
        assert subject.artifact_subject_id in result.artifact_subject_ids
        assert subject.artifact_instance_id == "artifact-1"
        assert subject.subject_reference == _student_subject(student_id)
        assert subject.subject_role == "observed_participant"
        assert subject.confirmation_status == "confirmed"
        assert subject.assignment_source == "teacher"
        assert subject.privacy_policy == _privacy()
        assert subject.created_provenance.timestamp == _clock(21).isoformat()
        assert list_record_revisions(
            root,
            _work(),
            "artifact_subject",
            subject.artifact_subject_id,
        ) == (1,)

    assert after.graph.artifact_authors == ()
    assert after.graph.correction_records == ()
    assert after.graph.artifact_reviews == ()
    assert after.graph.score_records == ()


def test_issue106_multi_add_rejects_duplicate_author_students(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="duplicate student IDs",
    ):
        add_artifact_authors(
            AddArtifactAuthorsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-1"),
                authorship_mode="co_author",
                attribution_status="confirmed",
                attribution_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == revision
    assert after.graph.artifact_authors == ()


def test_issue106_multi_add_rejects_duplicate_subject_students(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="duplicate student IDs",
    ):
        add_artifact_subjects(
            AddArtifactSubjectsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-1"),
                subject_role="observed_participant",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == revision
    assert after.graph.artifact_subjects == ()


def test_issue106_multi_add_author_conflict_is_atomic(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    existing = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-existing",
            author_reference=_student_author("student-1"),
            authorship_mode="co_author",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="equivalent current"):
        add_artifact_authors(
            AddArtifactAuthorsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-2"),
                authorship_mode="co_author",
                attribution_status="confirmed",
                attribution_source="teacher",
                expected_snapshot_revision=existing.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == existing.commit.snapshot_revision
    assert tuple(
        item.artifact_author_id for item in after.graph.artifact_authors
    ) == ("author-existing",)


def test_issue106_multi_add_subject_conflict_is_atomic(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    existing = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_subject_id="subject-existing",
            subject_reference=_student_subject("student-1"),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="equivalent current"):
        add_artifact_subjects(
            AddArtifactSubjectsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-2"),
                subject_role="observed_participant",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=existing.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == existing.commit.snapshot_revision
    assert tuple(
        item.artifact_subject_id for item in after.graph.artifact_subjects
    ) == ("subject-existing",)


def test_issue106_multi_add_rejects_complex_author_mode(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="Routine multi-Author",
    ):
        add_artifact_authors(
            AddArtifactAuthorsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-2"),
                authorship_mode="recorder_for_group",
                attribution_status="confirmed",
                attribution_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    assert load_current_record_graph(root, _work()).snapshot_revision == revision


def test_issue106_multi_add_is_bound_to_exact_snapshot(tmp_path: Path) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    advanced = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-advanced",
            author_reference=_student_author("student-3"),
            authorship_mode="observer",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    with pytest.raises(ConcordWorkflowConflictError, match="stale"):
        add_artifact_subjects(
            AddArtifactSubjectsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-2"),
                subject_role="observed_participant",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == advanced.commit.snapshot_revision
    assert after.graph.artifact_subjects == ()


def test_issue106_batch_preserves_recorder_for_group_semantics(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)
    added = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_author_id="author-recorder-group-issue106",
            author_reference=_student_author("student-1"),
            authorship_mode="recorder_for_group",
            attribution_status="proposed",
            attribution_source="teacher",
            expected_snapshot_revision=revision,
            actor=_actor(),
            represented_group_id="group-a",
            role_assignment_id="role-recorder",
            representation_status="recorder_summary",
            privacy_policy=_privacy(),
        ),
        workspace_root=root,
    )
    before_graph = load_current_record_graph(root, _work()).graph
    before = next(
        item
        for item in before_graph.artifact_authors
        if item.artifact_author_id == "author-recorder-group-issue106"
    )

    result = batch_confirm_artifact_attribution(
        BatchConfirmArtifactAttributionRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_author_ids=("author-recorder-group-issue106",),
            expected_snapshot_revision=added.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )

    after_graph = load_current_record_graph(root, _work()).graph
    after = next(
        item
        for item in after_graph.artifact_authors
        if item.artifact_author_id == "author-recorder-group-issue106"
    )
    assert after == replace(before, attribution_status="confirmed")
    assert after.represented_group_id == "group-a"
    assert after.role_assignment_id == "role-recorder"
    assert after.representation_status == "recorder_summary"
    assert result.confirmed_author_count == 1


def test_issue106_multi_add_keeps_core_roster_authoritative(
    tmp_path: Path,
) -> None:
    root, revision = _workspace_with_artifact(tmp_path)

    with pytest.raises(ConcordWorkflowNotFoundError, match="Core roster"):
        add_artifact_authors(
            AddArtifactAuthorsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-1", "student-missing"),
                authorship_mode="co_author",
                attribution_status="confirmed",
                attribution_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    with pytest.raises(ConcordWorkflowNotFoundError, match="Core roster"):
        add_artifact_subjects(
            AddArtifactSubjectsRequest(
                class_id="class-1",
                activity_id="activity-1",
                artifact_instance_id="artifact-1",
                student_ids=("student-2", "student-missing"),
                subject_role="observed_participant",
                confirmation_status="confirmed",
                assignment_source="teacher",
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )

    after = load_current_record_graph(root, _work())
    assert after.snapshot_revision == revision
    assert after.graph.artifact_authors == ()
    assert after.graph.artifact_subjects == ()
