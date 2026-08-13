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
    ScoreEvidenceLink,
    ScoreRecord,
    ScoreTargetReference,
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
        timestamp="2026-08-12T19:00:00-04:00",
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
        title="Synthetic score handoff",
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


def _student(student_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _evidence(*, required: bool = False) -> EvidenceReference:
    return EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
        moderation_requirement="required" if required else "not_required",
    )


def _score(*, target_id: str = "student-1") -> ScoreRecord:
    return ScoreRecord(
        score_record_id="score-1",
        activity_id="activity-1",
        target_reference=ScoreTargetReference(
            target_kind="core_student",
            target_id=target_id,
            owning_system="core",
        ),
        criterion_id="criterion-missing",
        score_kind="local",
        scoring_scale_id="scale-missing",
        disposition="scored",
        basis="linked_evidence",
        scorer=_actor(),
        scored_at="2026-08-12T19:20:00-04:00",
        moderation_complete=True,
        privacy_policy=_privacy(),
        value=1,
    )


def _link(
    reference: EvidenceReference,
    *,
    moderation_record_id: str | None = None,
    subject_context: tuple[SubjectReference, ...] = (),
) -> ScoreEvidenceLink:
    return ScoreEvidenceLink(
        score_evidence_link_id="link-1",
        score_record_id="score-1",
        evidence_reference=reference,
        relevance_description="Synthetic evidence link.",
        created_provenance=_provenance(),
        subject_context=subject_context,
        moderation_record_id=moderation_record_id,
        status="active",
    )


def _review_required() -> ArtifactReview:
    return ArtifactReview(
        artifact_review_id="review-required",
        artifact_instance_id="artifact-1",
        reviewer=_actor(),
        reviewed_at="2026-08-12T19:10:00-04:00",
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
    )


def _moderation(
    moderation_id: str,
    reference: EvidenceReference,
    *,
    subject: SubjectReference | None = None,
    status: str = "accepted",
    permitted_use: str = "support_named_subject",
    predecessor: str | None = None,
) -> ModerationRecord:
    return ModerationRecord(
        moderation_record_id=moderation_id,
        target_evidence_reference=reference,
        target_subject_references=() if subject is None else (subject,),
        moderator=_actor(),
        moderated_at="2026-08-12T19:15:00-04:00",
        status=status,
        permitted_use=permitted_use,
        rationale="Synthetic Moderation decision.",
        privacy_policy=_privacy(),
        supersedes_moderation_record_id=predecessor,
    )


def _graph(
    *,
    reference: EvidenceReference,
    moderation_records: tuple[ModerationRecord, ...] = (),
    moderation_record_id: str | None = None,
    review: ArtifactReview | None = None,
    subject_context: tuple[SubjectReference, ...] = (),
    score: ScoreRecord | None = None,
) -> ConcordRecordGraph:
    score_record = _score() if score is None else score
    reviews = () if review is None else (review,)
    return ConcordRecordGraph(
        activities=(_activity(),),
        sessions=(_session(),),
        artifact_instances=(_artifact(),),
        artifact_pages=(_page(),),
        artifact_reviews=reviews,
        moderation_records=moderation_records,
        score_records=(score_record,),
        score_evidence_links=(
            _link(
                reference,
                moderation_record_id=moderation_record_id,
                subject_context=subject_context,
            ),
        ),
    )


def _codes(graph: ConcordRecordGraph) -> set[str]:
    return {issue.code for issue in collect_record_graph_issues(graph)}


def test_current_review_requirement_cannot_be_bypassed_by_reference_flag() -> None:
    graph = _graph(reference=_evidence(required=False), review=_review_required())
    assert "score.evidence.moderation_required" in _codes(graph)


def test_matching_current_moderation_satisfies_review_requirement() -> None:
    reference = _evidence(required=False)
    moderation = _moderation(
        "moderation-current",
        reference,
        subject=_student("student-1"),
    )
    graph = _graph(
        reference=reference,
        review=_review_required(),
        moderation_records=(moderation,),
        moderation_record_id="moderation-current",
        subject_context=(_student("student-1"),),
    )
    codes = _codes(graph)
    assert "score.evidence.moderation_required" not in codes
    assert "moderation.subject_scope.not_applicable" not in codes
    assert "moderation.use.target_mismatch" not in codes


def test_historical_moderation_does_not_satisfy_required_use() -> None:
    reference = _evidence(required=True)
    before = _moderation(
        "moderation-before",
        reference,
        subject=_student("student-1"),
    )
    after = _moderation(
        "moderation-after",
        reference,
        subject=_student("student-1"),
        predecessor="moderation-before",
    )
    graph = _graph(
        reference=reference,
        moderation_records=(before, after),
        moderation_record_id="moderation-before",
        subject_context=(_student("student-1"),),
    )
    codes = _codes(graph)
    assert "moderation.current.required" in codes
    assert "score.evidence.moderation_required" in codes


def test_wrong_subject_scope_does_not_satisfy_required_use() -> None:
    reference = _evidence(required=True)
    moderation = _moderation(
        "moderation-wrong-subject",
        reference,
        subject=_student("student-2"),
    )
    graph = _graph(
        reference=reference,
        moderation_records=(moderation,),
        moderation_record_id="moderation-wrong-subject",
        subject_context=(_student("student-1"),),
    )
    codes = _codes(graph)
    assert "moderation.subject_scope.not_applicable" in codes
    assert "score.evidence.moderation_required" in codes


def test_formative_only_moderation_does_not_satisfy_required_use() -> None:
    reference = _evidence(required=True)
    moderation = _moderation(
        "moderation-formative",
        reference,
        subject=None,
        permitted_use="formative_only",
    )
    graph = _graph(
        reference=reference,
        moderation_records=(moderation,),
        moderation_record_id="moderation-formative",
    )
    codes = _codes(graph)
    assert "moderation.use.not_permitted" in codes
    assert "score.evidence.moderation_required" in codes


def test_named_subject_permission_must_match_score_target() -> None:
    reference = _evidence(required=True)
    moderation = _moderation(
        "moderation-student-two",
        reference,
        subject=_student("student-2"),
    )
    graph = _graph(
        reference=reference,
        moderation_records=(moderation,),
        moderation_record_id="moderation-student-two",
        score=_score(target_id="student-1"),
        subject_context=(_student("student-2"),),
    )
    codes = _codes(graph)
    assert "moderation.use.target_mismatch" in codes
    assert "score.evidence.moderation_required" in codes


def test_wrong_evidence_moderation_does_not_satisfy_required_use() -> None:
    link_reference = _evidence(required=True)
    page_reference = EvidenceReference(
        evidence_kind="artifact_page",
        owning_system="concord",
        record_id="page-1",
        moderation_requirement="required",
    )
    moderation = _moderation(
        "moderation-page",
        page_reference,
        subject=_student("student-1"),
    )
    graph = _graph(
        reference=link_reference,
        moderation_records=(moderation,),
        moderation_record_id="moderation-page",
        subject_context=(_student("student-1"),),
    )
    codes = _codes(graph)
    assert "moderation.evidence.mismatch" in codes
    assert "score.evidence.moderation_required" in codes
