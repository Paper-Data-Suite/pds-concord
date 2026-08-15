from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError

import pytest
from pds_core.routing_models import ModuleWorkRef

import concord.academic_result_artifacts as artifacts_module
import concord.artifact_rendering as rendering_module
from concord.academic_result_artifacts import (
    AcademicResultArtifactAuthorizationDecision,
    AcademicResultArtifactAuthorizationRequest,
    AcademicResultArtifactAuthorProjection,
    AcademicResultArtifactPageProjection,
    AcademicResultArtifactProjection,
    AcademicResultArtifactSubjectProjection,
    AcademicResultParticipantReferenceProjection,
    AuthorizedAcademicResultArtifact,
    ConcordAcademicResultArtifactValidationError,
)
from concord.academic_result_manifest import (
    EvidenceReferenceProjection,
    PublicActor,
    RecordReferenceProjection,
    SubjectReferenceProjection,
)

EXPECTED_PUBLIC = {
    "AcademicResultArtifactAuthorizationDecision",
    "AcademicResultArtifactAuthorizationGate",
    "AcademicResultArtifactAuthorizationRequest",
    "AcademicResultArtifactAuthorProjection",
    "AcademicResultArtifactAuthorReference",
    "AcademicResultArtifactPageProjection",
    "AcademicResultArtifactProjection",
    "AcademicResultArtifactRepresentation",
    "AcademicResultArtifactSubjectProjection",
    "AcademicResultParticipantReferenceProjection",
    "ArtifactAuthorizationStatus",
    "AuthorizedAcademicResultArtifact",
    "ConcordAcademicResultArtifactAmbiguityError",
    "ConcordAcademicResultArtifactAuthorizationError",
    "ConcordAcademicResultArtifactError",
    "ConcordAcademicResultArtifactIntegrityError",
    "ConcordAcademicResultArtifactNotFoundError",
    "ConcordAcademicResultArtifactUnavailableError",
    "ConcordAcademicResultArtifactValidationError",
    "read_authorized_academic_result_artifact",
}


def _work() -> ModuleWorkRef:
    return ModuleWorkRef("concord", "class-1", "activity-1")


def _student(subject_id: str) -> SubjectReferenceProjection:
    return SubjectReferenceProjection(
        subject_kind="core_student",
        subject_id=subject_id,
        owning_system="core",
        contract_version=None,
    )


def _evidence(
    kind: str = "artifact_instance",
    record_id: str = "artifact-1",
    owner: str = "concord",
) -> EvidenceReferenceProjection:
    return EvidenceReferenceProjection(
        evidence_kind=kind,
        owning_system=owner,
        record_id=record_id,
        contract_version=None,
        source_publication_reference=None,
        immutable_source_version=(None if owner == "concord" else "1"),
        locator=None,
        subject_context=(_student("student-subject"),),
        moderation_requirement="not_required",
    )


def _artifact() -> AcademicResultArtifactProjection:
    return AcademicResultArtifactProjection(
        artifact_instance_id="artifact-1",
        artifact_category="laboratory_record",
        session_id="session-1",
        group_id="group-1",
        pages=(
            AcademicResultArtifactPageProjection("page-1", 1),
            AcademicResultArtifactPageProjection("page-2", 2),
        ),
        privacy_classification="group_and_teacher",
    )


def _author() -> AcademicResultArtifactAuthorProjection:
    return AcademicResultArtifactAuthorProjection(
        artifact_author_id="author-1",
        artifact_instance_id="artifact-1",
        author_reference=AcademicResultParticipantReferenceProjection(
            participant_kind="core_student",
            participant_id="student-author",
            owning_system="core",
        ),
        authorship_mode="recorder_for_group",
        attribution_status="confirmed",
        represented_group_id="group-1",
        representation_status="recorder_summary",
    )


def _subject_projection() -> AcademicResultArtifactSubjectProjection:
    return AcademicResultArtifactSubjectProjection(
        artifact_subject_id="subject-1",
        artifact_instance_id="artifact-1",
        subject_reference=_student("student-subject"),
        subject_role="observed_participant",
        confirmation_status="confirmed",
        criterion_id="criterion-standard",
    )


def _request(
    evidence: EvidenceReferenceProjection | None = None,
) -> AcademicResultArtifactAuthorizationRequest:
    return AcademicResultArtifactAuthorizationRequest(
        work=_work(),
        record_set_id="academic_results",
        record_set_revision=2,
        source_snapshot_revision=12,
        score_record_id="score-1",
        score_evidence_link_id="link-1",
        evidence_reference=evidence or _evidence(),
        purpose="authorized downstream Artifact review",
    )


def _result(
    evidence: EvidenceReferenceProjection | None = None,
) -> AuthorizedAcademicResultArtifact:
    content = b"%PDF-1.7\nsynthetic\n%%EOF\n"
    return AuthorizedAcademicResultArtifact(
        representation="returned_artifact_pdf",
        work=_work(),
        record_set_revision=2,
        source_snapshot_revision=12,
        score_record_id="score-1",
        score_evidence_link_id="link-1",
        evidence_reference=evidence or _evidence(),
        artifact=_artifact(),
        authors=(_author(),),
        subjects=(_subject_projection(),),
        media_type="application/pdf",
        sha256=hashlib.sha256(content).hexdigest(),
        byte_size=len(content),
        content=content,
    )


def test_public_artifact_contract_exports_exact_stable_surface() -> None:
    assert set(artifacts_module.__all__) == EXPECTED_PUBLIC


def test_authorization_request_is_manifest_derived_and_immutable() -> None:
    request = _request()
    assert request.work == _work()
    assert request.record_set_id == "academic_results"
    assert request.source_snapshot_revision == 12
    assert request.evidence_reference.evidence_kind == "artifact_instance"
    with pytest.raises(FrozenInstanceError):
        request.purpose = "changed"  # type: ignore[misc]


@pytest.mark.parametrize("status", ["allowed", "denied", "unresolved"])
def test_authorization_decision_accepts_only_closed_statuses(status: str) -> None:
    decision = AcademicResultArtifactAuthorizationDecision(
        status  # type: ignore[arg-type]
    )
    assert decision.status == status


def test_authorization_decision_rejects_unknown_status() -> None:
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AcademicResultArtifactAuthorizationDecision("maybe")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "evidence",
    [
        _evidence("scoreform_result", "result-1", "scoreform"),
        _evidence("quillan_response", "response-1", "quillan"),
        _evidence("external_record", "external-1", "external"),
        _evidence("teacher_rationale", "rationale-1", "concord"),
    ],
)
def test_authorization_request_rejects_non_concord_artifact_evidence(
    evidence: EvidenceReferenceProjection,
) -> None:
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        _request(evidence)


def test_authorization_request_rejects_wrong_work_or_record_set() -> None:
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AcademicResultArtifactAuthorizationRequest(
            work=ModuleWorkRef("other", "class-1", "activity-1"),
            record_set_id="academic_results",
            record_set_revision=1,
            source_snapshot_revision=1,
            score_record_id="score-1",
            score_evidence_link_id="link-1",
            evidence_reference=_evidence(),
            purpose="review",
        )
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AcademicResultArtifactAuthorizationRequest(
            work=_work(),
            record_set_id="other_results",
            record_set_revision=1,
            source_snapshot_revision=1,
            score_record_id="score-1",
            score_evidence_link_id="link-1",
            evidence_reference=_evidence(),
            purpose="review",
        )


@pytest.mark.parametrize("purpose", ["", " leading", "trailing ", "line\nbreak"])
def test_authorization_request_rejects_unsafe_purpose(purpose: str) -> None:
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AcademicResultArtifactAuthorizationRequest(
            work=_work(),
            record_set_id="academic_results",
            record_set_revision=1,
            source_snapshot_revision=1,
            score_record_id="score-1",
            score_evidence_link_id="link-1",
            evidence_reference=_evidence(),
            purpose=purpose,
        )


def test_public_artifact_projection_preserves_only_bounded_identity_context() -> None:
    artifact = _artifact()
    assert artifact.artifact_instance_id == "artifact-1"
    assert artifact.session_id == "session-1"
    assert artifact.group_id == "group-1"
    assert tuple(page.artifact_page_id for page in artifact.pages) == (
        "page-1",
        "page-2",
    )
    assert not hasattr(artifact, "route_id")
    assert not hasattr(artifact, "retained_source_relative_path")
    assert not hasattr(artifact, "retained_source_sha256")
    assert not hasattr(artifact, "created_provenance")


def test_author_and_subject_are_distinct_public_relationships() -> None:
    author = _author()
    subject = _subject_projection()
    assert isinstance(
        author.author_reference,
        AcademicResultParticipantReferenceProjection,
    )
    assert author.author_reference.participant_id == "student-author"
    assert subject.subject_reference.subject_id == "student-subject"
    assert (
        author.author_reference.participant_id
        != subject.subject_reference.subject_id
    )
    assert author.represented_group_id == "group-1"
    assert not hasattr(author, "role_assignment_id")
    assert not hasattr(subject, "assignment_source")
    assert not hasattr(subject, "privacy_policy")


def test_unknown_author_does_not_invent_identity_or_group_context() -> None:
    unknown = AcademicResultArtifactAuthorProjection(
        artifact_author_id="author-unknown",
        artifact_instance_id="artifact-1",
        author_reference=None,
        authorship_mode="unknown",
        attribution_status="unknown",
        represented_group_id=None,
        representation_status=None,
    )
    assert unknown.author_reference is None
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AcademicResultArtifactAuthorProjection(
            artifact_author_id="author-unknown",
            artifact_instance_id="artifact-1",
            author_reference=AcademicResultParticipantReferenceProjection(
                "core_student", "student-1", "core"
            ),
            authorship_mode="unknown",
            attribution_status="unknown",
            represented_group_id=None,
            representation_status=None,
        )


def test_author_reference_supports_public_actor_and_record_without_labels() -> None:
    actor = AcademicResultArtifactAuthorProjection(
        artifact_author_id="author-adult",
        artifact_instance_id="artifact-1",
        author_reference=PublicActor("authorized_adult", "teacher-1", "core"),
        authorship_mode="teacher_author",
        attribution_status="confirmed",
        represented_group_id=None,
        representation_status=None,
    )
    record = AcademicResultArtifactAuthorProjection(
        artifact_author_id="author-record",
        artifact_instance_id="artifact-1",
        author_reference=RecordReferenceProjection(
            module_id="concord",
            record_kind="group",
            record_id="group-1",
            contract_version=None,
        ),
        authorship_mode="collective_group_author",
        attribution_status="confirmed",
        represented_group_id="group-1",
        representation_status="unanimous_position",
    )
    assert isinstance(actor.author_reference, PublicActor)
    assert isinstance(record.author_reference, RecordReferenceProjection)


def test_authorized_result_binds_exact_pdf_bytes_and_public_relationships() -> None:
    result = _result()
    assert result.media_type == "application/pdf"
    assert result.byte_size == len(result.content)
    assert result.sha256 == hashlib.sha256(result.content).hexdigest()
    assert (
        result.authors[0].artifact_instance_id
        == result.artifact.artifact_instance_id
    )
    assert (
        result.subjects[0].artifact_instance_id
        == result.artifact.artifact_instance_id
    )
    assert not hasattr(result, "path")
    assert not hasattr(result, "retained_source_relative_path")


def test_authorized_result_supports_exact_artifact_page_evidence() -> None:
    result = _result(_evidence("artifact_page", "page-2", "concord"))
    assert result.evidence_reference.record_id == "page-2"


@pytest.mark.parametrize(
    "evidence",
    [
        _evidence("artifact_instance", "artifact-other", "concord"),
        _evidence("artifact_page", "page-other", "concord"),
    ],
)
def test_authorized_result_rejects_evidence_identity_mismatch(
    evidence: EvidenceReferenceProjection,
) -> None:
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        _result(evidence)


def test_authorized_result_rejects_digest_size_media_or_mutable_bytes() -> None:
    good = _result()
    common = dict(
        representation=good.representation,
        work=good.work,
        record_set_revision=good.record_set_revision,
        source_snapshot_revision=good.source_snapshot_revision,
        score_record_id=good.score_record_id,
        score_evidence_link_id=good.score_evidence_link_id,
        evidence_reference=good.evidence_reference,
        artifact=good.artifact,
        authors=good.authors,
        subjects=good.subjects,
    )
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AuthorizedAcademicResultArtifact(
            **common,
            media_type="application/pdf",
            sha256="0" * 64,
            byte_size=good.byte_size,
            content=good.content,
        )
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AuthorizedAcademicResultArtifact(
            **common,
            media_type="application/pdf",
            sha256=good.sha256,
            byte_size=good.byte_size + 1,
            content=good.content,
        )
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AuthorizedAcademicResultArtifact(
            **common,
            media_type="text/plain",
            sha256=good.sha256,
            byte_size=good.byte_size,
            content=good.content,
        )
    with pytest.raises(ConcordAcademicResultArtifactValidationError):
        AuthorizedAcademicResultArtifact(
            **common,
            media_type="application/pdf",
            sha256=good.sha256,
            byte_size=good.byte_size,
            content=bytearray(good.content),  # type: ignore[arg-type]
        )


def test_public_artifact_module_has_no_consumer_or_registry_dependency() -> None:
    source = artifacts_module.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read().lower()  # noqa: PTH123
    for forbidden in (
        "import meridian",
        "import vitrine",
        "import scoreform",
        "import quillan",
        "import portia",
        "concord.workflows",
        "registry_services",
        "academic_catalog",
        "publication_storage",
    ):
        assert forbidden not in text
    assert "load_current_snapshot" not in text
    assert "load_current_record_graph" not in text


def test_neutral_artifact_rendering_layer_has_no_workflow_dependency() -> None:
    source = rendering_module.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read().lower()  # noqa: PTH123
    assert "concord.workflows" not in text
    assert "registry_services" not in text
    assert "academic_catalog" not in text
    assert "publication_storage" not in text


def test_public_contract_exposes_authorized_artifact_read_function() -> None:
    assert callable(artifacts_module.read_authorized_academic_result_artifact)
