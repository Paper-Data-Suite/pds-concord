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
    AddArtifactSubjectRequest,
    ArtifactPagePlan,
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
    add_artifact_subject,
    core_student_participant,
    create_activity_context,
    create_group_with_members,
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
