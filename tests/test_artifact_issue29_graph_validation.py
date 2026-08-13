from __future__ import annotations

from pds_core.routing_models import ModuleRecordRef

from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues
from concord.models import (
    Activity,
    ActorReference,
    ArtifactInstance,
    ArtifactPage,
    ArtifactReview,
    EvidenceReference,
    ModerationRecord,
    PrivacyPolicy,
    Provenance,
    Session,
    SubjectReference,
)


def _actor() -> ActorReference:
    return ActorReference(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="concord",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _provenance() -> Provenance:
    return Provenance(
        actor=_actor(),
        timestamp="2026-08-12T18:00:00-04:00",
        source_kind="manual",
    )


def _activity() -> Activity:
    return Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        title="Synthetic",
        activity_type="project",
        scoring_orientation="evidence_only",
        status="active",
        created_provenance=_provenance(),
    )


def _session() -> Session:
    return Session(
        session_id="session-1",
        activity_id="activity-1",
        sequence=1,
        status="active",
        created_provenance=_provenance(),
    )


def _artifact() -> ArtifactInstance:
    return ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="template-1",
        activity_id="activity-1",
        artifact_category="observation",
        generation_status="completed",
        expected_return_status="return_not_expected",
        artifact_status="generated",
        privacy_policy=_privacy(),
        page_ids=("page-1",),
        created_provenance=_provenance(),
    )


def _page() -> ArtifactPage:
    return ArtifactPage(
        artifact_page_id="page-1",
        artifact_instance_id="artifact-1",
        page_number=1,
        page_kind="observation",
        return_expected=False,
        route_required=False,
        page_status="generated",
        created_provenance=_provenance(),
    )


def _review(review_id: str, predecessor: str | None = None) -> ArtifactReview:
    return ArtifactReview(
        artifact_review_id=review_id,
        artifact_instance_id="artifact-1",
        reviewer=_actor(),
        reviewed_at="2026-08-12T18:10:00-04:00",
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
        supersedes_artifact_review_id=predecessor,
    )


def _base(**overrides: object) -> ConcordRecordGraph:
    values: dict[str, object] = {
        "activities": (_activity(),),
        "sessions": (_session(),),
        "artifact_instances": (_artifact(),),
        "artifact_pages": (_page(),),
    }
    values.update(overrides)
    return ConcordRecordGraph(**values)  # type: ignore[arg-type]


def _codes(graph: ConcordRecordGraph) -> set[str]:
    return {item.code for item in collect_record_graph_issues(graph)}


def test_graph_rejects_competing_review_heads() -> None:
    graph = _base(artifact_reviews=(_review("review-1"), _review("review-2")))
    assert "review.current.multiple_heads" in _codes(graph)


def test_graph_accepts_linear_review_head() -> None:
    graph = _base(
        artifact_reviews=(
            _review("review-1"),
            _review("review-2", "review-1"),
        )
    )
    assert "review.current.multiple_heads" not in _codes(graph)


def test_graph_rejects_competing_moderation_scope_heads() -> None:
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    subject = SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )
    records = tuple(
        ModerationRecord(
            moderation_record_id=f"moderation-{index}",
            target_evidence_reference=evidence,
            target_subject_references=(subject,),
            moderator=_actor(),
            moderated_at=f"2026-08-12T18:1{index}:00-04:00",
            status="accepted",
            permitted_use="support_named_subject",
            rationale=f"Synthetic decision {index}.",
            privacy_policy=_privacy(),
        )
        for index in (1, 2)
    )
    graph = _base(moderation_records=records)
    assert "moderation.current.duplicate_scope" in _codes(graph)


def test_moderation_subject_order_is_canonical() -> None:
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    first = SubjectReference(
        subject_kind="core_student",
        subject_id="student-2",
        owning_system="core",
    )
    second = SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )
    moderation = ModerationRecord(
        moderation_record_id="moderation-1",
        target_evidence_reference=evidence,
        target_subject_references=(first, second),
        moderator=_actor(),
        moderated_at="2026-08-12T18:15:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic.",
        privacy_policy=_privacy(),
    )
    assert [item.subject_id for item in moderation.target_subject_references] == [
        "student-1",
        "student-2",
    ]

def test_graph_requires_exact_revision_correction_records() -> None:
    review_before = _review("review-before")
    review_after = _review("review-after", "review-before")
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    moderation_before = ModerationRecord(
        moderation_record_id="moderation-before",
        target_evidence_reference=evidence,
        target_subject_references=(),
        moderator=_actor(),
        moderated_at="2026-08-12T18:15:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic.",
        privacy_policy=_privacy(),
    )
    moderation_after = ModerationRecord(
        moderation_record_id="moderation-after",
        target_evidence_reference=evidence,
        target_subject_references=(),
        moderator=_actor(),
        moderated_at="2026-08-12T18:16:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic successor.",
        privacy_policy=_privacy(),
        supersedes_moderation_record_id="moderation-before",
    )
    codes = _codes(
        _base(
            artifact_reviews=(review_before, review_after),
            moderation_records=(moderation_before, moderation_after),
        )
    )
    assert "review.correction.missing" in codes
    assert "moderation.correction.missing" in codes


def test_graph_rejects_backward_review_and_moderation_times() -> None:
    review_before = _review("review-before")
    review_after = ArtifactReview(
        artifact_review_id="review-after",
        artifact_instance_id="artifact-1",
        reviewer=_actor(),
        reviewed_at="2026-08-12T18:09:00-04:00",
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
        supersedes_artifact_review_id="review-before",
    )
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    moderation_before = ModerationRecord(
        moderation_record_id="moderation-before",
        target_evidence_reference=evidence,
        target_subject_references=(),
        moderator=_actor(),
        moderated_at="2026-08-12T18:15:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic.",
        privacy_policy=_privacy(),
    )
    moderation_after = ModerationRecord(
        moderation_record_id="moderation-after",
        target_evidence_reference=evidence,
        target_subject_references=(),
        moderator=_actor(),
        moderated_at="2026-08-12T18:14:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic successor.",
        privacy_policy=_privacy(),
        supersedes_moderation_record_id="moderation-before",
    )
    issues = collect_record_graph_issues(
        _base(
            artifact_reviews=(review_before, review_after),
            moderation_records=(moderation_before, moderation_after),
        )
    )
    backward_kinds = {
        issue.record_kind
        for issue in issues
        if issue.code == "supersession.time.backward"
    }
    assert {"artifact_review", "moderation_record"} <= backward_kinds


def test_graph_rejects_moderation_revision_scope_change() -> None:
    evidence = EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
    )
    student_one = SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )
    student_two = SubjectReference(
        subject_kind="core_student",
        subject_id="student-2",
        owning_system="core",
    )
    before = ModerationRecord(
        moderation_record_id="moderation-before",
        target_evidence_reference=evidence,
        target_subject_references=(student_one,),
        moderator=_actor(),
        moderated_at="2026-08-12T18:15:00-04:00",
        status="accepted",
        permitted_use="support_named_subject",
        rationale="Synthetic.",
        privacy_policy=_privacy(),
    )
    after = ModerationRecord(
        moderation_record_id="moderation-after",
        target_evidence_reference=evidence,
        target_subject_references=(student_two,),
        moderator=_actor(),
        moderated_at="2026-08-12T18:16:00-04:00",
        status="accepted",
        permitted_use="support_named_subject",
        rationale="Synthetic changed scope.",
        privacy_policy=_privacy(),
        supersedes_moderation_record_id="moderation-before",
    )
    assert "supersession.context_mismatch" in _codes(
        _base(moderation_records=(before, after))
    )


def test_graph_rejects_invalid_moderation_evidence_owner_pairs() -> None:
    local_external_kind = ModerationRecord(
        moderation_record_id="moderation-local-external-kind",
        target_evidence_reference=EvidenceReference(
            evidence_kind="scoreform_result",
            owning_system="concord",
            record_id="result-1",
        ),
        target_subject_references=(),
        moderator=_actor(),
        moderated_at="2026-08-12T18:15:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic.",
        privacy_policy=_privacy(),
    )
    external_artifact = ModerationRecord(
        moderation_record_id="moderation-external-artifact",
        target_evidence_reference=EvidenceReference(
            evidence_kind="artifact_instance",
            owning_system="external_system",
            record_id="artifact-elsewhere",
            immutable_source_version="revision-1",
        ),
        target_subject_references=(),
        moderator=_actor(),
        moderated_at="2026-08-12T18:16:00-04:00",
        status="accepted",
        permitted_use="corroborate_only",
        rationale="Synthetic.",
        privacy_policy=_privacy(),
    )
    codes = _codes(
        _base(moderation_records=(local_external_kind, external_artifact))
    )
    assert "moderation.evidence.local_kind_invalid" in codes
    assert "moderation.evidence.owner_mismatch" in codes
