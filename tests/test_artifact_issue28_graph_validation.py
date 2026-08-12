from __future__ import annotations

from dataclasses import replace

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues
from concord.models import (
    Activity,
    ActorReference,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactSubject,
    ConcordRecordReference,
    CorrectionRecord,
    Group,
    ParticipantReference,
    PrivacyPolicy,
    Provenance,
    Session,
    SubjectReference,
)


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-12T17:00:00-04:00",
        source_kind="manual",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _activity(activity_id: str) -> Activity:
    return Activity(
        activity_id=activity_id,
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        title=f"Activity {activity_id}",
        activity_type="project",
        scoring_orientation="evidence_only",
        status="active",
        created_provenance=_provenance(),
    )


def _session(activity_id: str) -> Session:
    return Session(
        session_id=f"session-{activity_id}",
        activity_id=activity_id,
        sequence=1,
        status="active",
        created_provenance=_provenance(),
    )


def _artifact(
    *,
    status: str = "planned",
    page_ids: tuple[str, ...] = ("page-1",),
) -> ArtifactInstance:
    return ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="template-1",
        activity_id="activity-1",
        artifact_category="observation",
        generation_status="completed",
        expected_return_status="returned_expected",
        artifact_status=status,
        privacy_policy=_privacy(),
        page_ids=page_ids,
        created_provenance=_provenance(),
    )


def _page(
    page_id: str,
    number: int,
    *,
    status: str = "planned",
    return_expected: bool = True,
) -> ArtifactPage:
    return ArtifactPage(
        artifact_page_id=page_id,
        artifact_instance_id="artifact-1",
        page_number=number,
        page_kind="primary" if number == 1 else "continuation",
        return_expected=return_expected,
        route_required=False,
        page_status=status,
        created_provenance=_provenance(),
    )


def _student(student_id: str = "student-1") -> ParticipantReference:
    return ParticipantReference(
        participant_kind="core_student",
        participant_id=student_id,
        owning_system="core",
    )


def _codes(graph: ConcordRecordGraph) -> set[str]:
    return {item.code for item in collect_record_graph_issues(graph)}


@pytest.mark.parametrize(
    ("artifact_status", "page_statuses"),
    (
        ("planned", ("returned", "planned")),
        ("partially_returned", ("returned", "returned")),
        ("returned", ("returned", "planned")),
        ("returned", ("planned", "planned")),
    ),
)
def test_graph_rejects_incoherent_return_rollup(
    artifact_status: str,
    page_statuses: tuple[str, str],
) -> None:
    graph = ConcordRecordGraph(
        activities=(_activity("activity-1"),),
        sessions=(_session("activity-1"),),
        artifact_instances=(
            _artifact(
                status=artifact_status,
                page_ids=("page-1", "page-2"),
            ),
        ),
        artifact_pages=(
            _page("page-1", 1, status=page_statuses[0]),
            _page("page-2", 2, status=page_statuses[1]),
        ),
    )
    assert "artifact.return_state.incoherent" in _codes(graph)


def test_terminal_artifact_state_can_preserve_prior_return_history() -> None:
    graph = ConcordRecordGraph(
        activities=(_activity("activity-1"),),
        sessions=(_session("activity-1"),),
        artifact_instances=(_artifact(status="archived"),),
        artifact_pages=(_page("page-1", 1, status="returned"),),
    )
    assert "artifact.return_state.incoherent" not in _codes(graph)


def test_graph_rejects_duplicate_current_author_and_subject_associations() -> None:
    author_one = ArtifactAuthor(
        artifact_author_id="author-1",
        artifact_instance_id="artifact-1",
        author_reference=_student(),
        authorship_mode="observer",
        attribution_status="confirmed",
        attribution_source="teacher",
        created_provenance=_provenance(),
    )
    author_two = replace(author_one, artifact_author_id="author-2")
    subject_one = ArtifactSubject(
        artifact_subject_id="subject-1",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-2",
            owning_system="core",
        ),
        subject_role="observed_participant",
        confirmation_status="confirmed",
        assignment_source="teacher",
        created_provenance=_provenance(),
    )
    subject_two = replace(subject_one, artifact_subject_id="subject-2")
    graph = ConcordRecordGraph(
        activities=(_activity("activity-1"),),
        sessions=(_session("activity-1"),),
        artifact_instances=(_artifact(),),
        artifact_pages=(_page("page-1", 1),),
        artifact_authors=(author_one, author_two),
        artifact_subjects=(subject_one, subject_two),
    )
    codes = _codes(graph)
    assert "author.current.duplicate" in codes
    assert "subject.current.duplicate" in codes


def test_graph_validates_collective_and_recorder_author_context() -> None:
    group = Group(
        group_id="group-other",
        activity_id="activity-2",
        label="Other Group",
        status="active",
        created_provenance=_provenance(),
    )
    collective = ArtifactAuthor(
        artifact_author_id="author-group",
        artifact_instance_id="artifact-1",
        author_reference=ConcordRecordReference(
            record_kind="group",
            record_id="group-other",
        ),
        authorship_mode="collective_group_author",
        attribution_status="confirmed",
        attribution_source="teacher",
        created_provenance=_provenance(),
    )
    recorder = ArtifactAuthor(
        artifact_author_id="author-recorder",
        artifact_instance_id="artifact-1",
        author_reference=_student(),
        authorship_mode="recorder_for_group",
        attribution_status="confirmed",
        attribution_source="teacher",
        created_provenance=_provenance(),
        represented_group_id="group-other",
    )
    graph = ConcordRecordGraph(
        activities=(_activity("activity-1"), _activity("activity-2")),
        sessions=(_session("activity-1"), _session("activity-2")),
        groups=(group,),
        artifact_instances=(_artifact(),),
        artifact_pages=(_page("page-1", 1),),
        artifact_authors=(collective, recorder),
    )
    codes = _codes(graph)
    assert "author.reference.group_invalid" in codes
    assert "author.group.invalid" in codes
    assert "author.recorder.representation_required" in codes


def test_graph_validates_subject_activity_role_and_owner() -> None:
    other_group = Group(
        group_id="group-other",
        activity_id="activity-2",
        label="Other Group",
        status="active",
        created_provenance=_provenance(),
    )
    wrong_activity = ArtifactSubject(
        artifact_subject_id="subject-other-group",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="concord_group",
            subject_id="group-other",
            owning_system="concord",
        ),
        subject_role="represented_group",
        confirmation_status="confirmed",
        assignment_source="teacher",
        created_provenance=_provenance(),
    )
    wrong_role = ArtifactSubject(
        artifact_subject_id="subject-role",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="concord_group",
            subject_id="group-other",
            owning_system="concord",
        ),
        subject_role="observed_participant",
        confirmation_status="confirmed",
        assignment_source="teacher",
        created_provenance=_provenance(),
    )
    wrong_owner = ArtifactSubject(
        artifact_subject_id="subject-owner",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-1",
            owning_system="external",
        ),
        subject_role="observed_participant",
        confirmation_status="confirmed",
        assignment_source="teacher",
        created_provenance=_provenance(),
    )
    graph = ConcordRecordGraph(
        activities=(_activity("activity-1"), _activity("activity-2")),
        sessions=(_session("activity-1"), _session("activity-2")),
        groups=(other_group,),
        artifact_instances=(_artifact(),),
        artifact_pages=(_page("page-1", 1),),
        artifact_subjects=(wrong_activity, wrong_role, wrong_owner),
    )
    codes = _codes(graph)
    assert "subject.reference.activity_mismatch" in codes
    assert "subject.role.reference_mismatch" in codes
    assert "subject.reference.owner_mismatch" in codes


def test_graph_ties_author_correction_type_to_author_replacement() -> None:
    predecessor = ArtifactAuthor(
        artifact_author_id="author-before",
        artifact_instance_id="artifact-1",
        author_reference=_student("student-1"),
        authorship_mode="observer",
        attribution_status="confirmed",
        attribution_source="teacher",
        created_provenance=_provenance(),
    )
    successor = ArtifactAuthor(
        artifact_author_id="author-after",
        artifact_instance_id="artifact-1",
        author_reference=_student("student-2"),
        authorship_mode="observer",
        attribution_status="confirmed",
        attribution_source="teacher",
        created_provenance=_provenance(),
        supersedes_artifact_author_id="author-before",
    )
    correction = CorrectionRecord(
        correction_id="correction-1",
        target_reference=ConcordRecordReference(
            record_kind="artifact_author",
            record_id="author-before",
        ),
        correction_type="subject_correction",
        reason="Synthetic mismatch.",
        correcting_actor=_provenance().actor,
        corrected_at="2026-08-12T17:01:00-04:00",
        privacy_policy=_privacy(),
        replacement_reference=ConcordRecordReference(
            record_kind="artifact_author",
            record_id="author-after",
        ),
    )
    graph = ConcordRecordGraph(
        activities=(_activity("activity-1"),),
        sessions=(_session("activity-1"),),
        artifact_instances=(_artifact(),),
        artifact_pages=(_page("page-1", 1),),
        artifact_authors=(predecessor, successor),
        correction_records=(correction,),
    )
    assert "correction.type.target_mismatch" in _codes(graph)
