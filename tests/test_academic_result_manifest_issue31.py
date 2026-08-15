from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

from concord.academic_result_manifest import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    AcademicResultManifest,
    ActivityContextProjection,
    ConcordAcademicResultManifestDecodeError,
    ConcordAcademicResultManifestValidationError,
    CorePublicationReferenceProjection,
    CriterionProjection,
    CriterionSetProjection,
    EvidenceLocatorProjection,
    EvidenceReferenceProjection,
    ManifestProjection,
    ManifestRecordSet,
    ModerationProjection,
    PrivacyProjection,
    PublicActor,
    RecordReferenceProjection,
    ScaleLevelProjection,
    ScoreEvidenceLinkProjection,
    ScoreProjection,
    ScoringScaleProjection,
    StandardsResultProjection,
    StatusReasonProjection,
    SubjectReferenceProjection,
    TargetReferenceProjection,
    academic_result_manifest_from_bytes,
    academic_result_manifest_from_dict,
    academic_result_manifest_to_bytes,
    academic_result_manifest_to_dict,
    calculate_semantic_projection_digest,
    derive_manifest_capabilities,
    validate_academic_result_manifest,
    with_semantic_projection_digest,
)


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 14, hour, 0, tzinfo=timezone.utc)


def _actor(actor_id: str = "teacher-1") -> PublicActor:
    return PublicActor(
        actor_kind="authorized_adult",
        actor_id=actor_id,
        owning_system="concord",
    )


def _external_evidence() -> EvidenceReferenceProjection:
    student = SubjectReferenceProjection(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
        contract_version=None,
    )
    return EvidenceReferenceProjection(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="result-1",
        contract_version="scoreform_result_v1",
        source_publication_reference=CorePublicationReferenceProjection(
            publication_id="pub_" + ("a" * 32),
            publication_schema_version="1",
        ),
        immutable_source_version=None,
        locator=EvidenceLocatorProjection(
            page_number=1,
            source_page_index=0,
            section_label="Question 1",
            row_label=None,
            column_label=None,
            participant_label=None,
            session_id="session-1",
        ),
        subject_context=(student,),
        moderation_requirement="required",
    )


def _manifest() -> AcademicResultManifest:
    work = ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )
    source = ModuleRecordRef(
        module_id="concord",
        record_kind="activity",
        record_id="activity-1",
        contract_version="concord_activity_v1",
    )
    teacher = _actor()
    external = _external_evidence()
    student = SubjectReferenceProjection(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
        contract_version=None,
    )

    local_set = CriterionSetProjection(
        criterion_set_id="set-local",
        lineage_id="lineage-local",
        revision=1,
        criterion_set_kind="local",
        scope="activity_specific",
        criterion_ids=("criterion-local",),
        status="active",
        supersedes_criterion_set_id=None,
        standards_profile_id=None,
    )
    standard_set = CriterionSetProjection(
        criterion_set_id="set-standard",
        lineage_id="lineage-standard",
        revision=1,
        criterion_set_kind="standard_backed",
        scope="activity_specific",
        criterion_ids=("criterion-standard",),
        status="active",
        supersedes_criterion_set_id=None,
        standards_profile_id="profile-1",
    )
    local_criterion = CriterionProjection(
        criterion_id="criterion-local",
        criterion_set_id="set-local",
        key="collaboration",
        label="Collaboration",
        definition="Demonstrates effective collaborative practice.",
        criterion_kind="local",
        supported_target_kinds=("concord_group",),
        status="active",
        standard_id=None,
        alignment_standard_ids=("standard-2",),
        default_scoring_scale_id="scale-local",
    )
    standard_criterion = CriterionProjection(
        criterion_id="criterion-standard",
        criterion_set_id="set-standard",
        key="analysis",
        label="Analysis",
        definition="Uses evidence to support analysis.",
        criterion_kind="standard_backed",
        supported_target_kinds=("core_student",),
        status="active",
        standard_id="standard-1",
        alignment_standard_ids=(),
        default_scoring_scale_id="scale-standard",
    )
    local_scale = ScoringScaleProjection(
        scoring_scale_id="scale-local",
        lineage_id="scale-lineage-local",
        name="Typed local scale",
        revision=1,
        scale_type="teacher_defined",
        levels=(
            ScaleLevelProjection(1, "Integer", "Integer one.", None, None),
            ScaleLevelProjection(1.0, "Float", "Float one.", None, None),
            ScaleLevelProjection("1", "Text", "Text one.", None, None),
            ScaleLevelProjection(True, "Boolean", "Boolean true.", None, None),
        ),
        status="active",
        supersedes_scoring_scale_id=None,
    )
    standard_scale = ScoringScaleProjection(
        scoring_scale_id="scale-standard",
        lineage_id="scale-lineage-standard",
        name="Standards scale",
        revision=1,
        scale_type="ordinal",
        levels=(
            ScaleLevelProjection(
                "developing", "Developing", "Developing evidence.", 1, None
            ),
            ScaleLevelProjection(
                "meets", "Meets", "Meets the criterion.", 2, None
            ),
        ),
        status="active",
        supersedes_scoring_scale_id=None,
    )
    local_score = ScoreProjection(
        score_record_id="score-local",
        activity_id="activity-1",
        session_id=None,
        target_reference=TargetReferenceProjection(
            target_kind="concord_group",
            target_id="group-1",
            owning_system="concord",
            contract_version=None,
        ),
        criterion_id="criterion-local",
        score_kind="local",
        standard_id=None,
        scoring_scale_id="scale-local",
        disposition="scored",
        value=True,
        basis="professional_judgment",
        scorer=teacher,
        scored_at=_time(13),
        moderation_complete=True,
        status_reason=None,
        supersedes_score_record_id=None,
        current_state="current",
    )
    standard_score = ScoreProjection(
        score_record_id="score-standard",
        activity_id="activity-1",
        session_id="session-1",
        target_reference=TargetReferenceProjection(
            target_kind="core_student",
            target_id="student-1",
            owning_system="core",
            contract_version=None,
        ),
        criterion_id="criterion-standard",
        score_kind="standard_backed",
        standard_id="standard-1",
        scoring_scale_id="scale-standard",
        disposition="scored",
        value="meets",
        basis="linked_evidence",
        scorer=teacher,
        scored_at=_time(13),
        moderation_complete=True,
        status_reason=None,
        supersedes_score_record_id=None,
        current_state="current",
    )
    moderation = ModerationProjection(
        moderation_record_id="moderation-1",
        target_evidence_reference=external,
        target_subject_references=(student,),
        status="accepted",
        permitted_use="support_named_subject",
        qualification=None,
        supersedes_moderation_record_id=None,
        current_state="current",
    )
    link = ScoreEvidenceLinkProjection(
        score_evidence_link_id="link-1",
        score_record_id="score-standard",
        evidence_reference=external,
        evidence_locator=EvidenceLocatorProjection(
            page_number=1,
            source_page_index=0,
            section_label="Question 1",
            row_label=None,
            column_label=None,
            participant_label=None,
            session_id="session-1",
        ),
        subject_context=(student,),
        relevance_description="Direct evidence for the selected criterion.",
        significance="primary",
        moderation_record_id="moderation-1",
        status="active",
        supersedes_score_evidence_link_id=None,
    )
    manifest = AcademicResultManifest(
        record_type=ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
        contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
        producer_module_id="concord",
        generated_at=_time(14),
        record_set=ManifestRecordSet("academic_results", 1),
        work=work,
        source_activity=source,
        projection=ManifestProjection(
            source_snapshot_revision=12,
            projection_digest_algorithm="sha256",
            projection_digest="0" * 64,
            generated_by=teacher,
            revision_reason="initial",
        ),
        activity_context=ActivityContextProjection(
            activity_id="activity-1",
            class_id="class-1",
            title="Synthetic Collaborative Activity",
            scoring_orientation="mixed",
            standards_profile_id="profile-1",
            focus_standard_ids=("standard-1",),
            criterion_set_ids=("set-standard", "set-local"),
        ),
        criterion_sets=(local_set, standard_set),
        criteria=(local_criterion, standard_criterion),
        scoring_scales=(local_scale, standard_scale),
        scores=(local_score, standard_score),
        score_evidence_links=(link,),
        moderation_records=(moderation,),
        standards_result_projection=(
            StandardsResultProjection("score-standard", "standard-1"),
        ),
        privacy=PrivacyProjection(
            classification="teacher_and_subjects",
            audience_references=(student,),
            policy_reference=None,
            inherited_from=None,
        ),
    )
    return with_semantic_projection_digest(manifest)


def test_manifest_round_trip_is_exact_and_canonical() -> None:
    manifest = _manifest()
    data = academic_result_manifest_to_bytes(manifest)

    assert data.endswith(b"\n")
    assert not data.endswith(b"\n\n")
    assert data == academic_result_manifest_to_bytes(
        academic_result_manifest_from_bytes(data)
    )
    assert academic_result_manifest_from_bytes(data) == manifest

    native = academic_result_manifest_to_dict(manifest)
    assert academic_result_manifest_from_dict(native) == manifest


def test_manifest_preserves_type_sensitive_scale_values() -> None:
    restored = academic_result_manifest_from_bytes(
        academic_result_manifest_to_bytes(_manifest())
    )
    levels = restored.scoring_scales[0].levels

    assert type(levels[0].value) is int
    assert type(levels[1].value) is float
    assert type(levels[2].value) is str
    assert type(levels[3].value) is bool
    assert [level.value for level in levels] == [1, 1.0, "1", True]
    assert type(restored.scores[0].value) is bool


def test_capabilities_are_derived_from_exact_manifest_semantics() -> None:
    manifest = _manifest()
    assert derive_manifest_capabilities(manifest) == (
        "criterion_scores",
        "standards_ratings",
        "moderated_scores",
    )

    unmoderated_evidence = replace(
        manifest.score_evidence_links[0].evidence_reference,
        moderation_requirement="not_required",
    )
    unmoderated_link = replace(
        manifest.score_evidence_links[0],
        evidence_reference=unmoderated_evidence,
        moderation_record_id=None,
    )
    no_moderation = replace(
        manifest,
        score_evidence_links=(unmoderated_link,),
        moderation_records=(),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    no_moderation = with_semantic_projection_digest(no_moderation)
    assert derive_manifest_capabilities(no_moderation) == (
        "criterion_scores",
        "standards_ratings",
    )


def test_semantic_digest_ignores_revision_envelope_only() -> None:
    manifest = _manifest()
    original = calculate_semantic_projection_digest(manifest)

    envelope_change = replace(
        manifest,
        generated_at=_time(16),
        record_set=ManifestRecordSet("academic_results", 9),
        projection=replace(
            manifest.projection,
            source_snapshot_revision=99,
            generated_by=_actor("teacher-2"),
            revision_reason="native_state_change",
            projection_digest="0" * 64,
        ),
    )
    assert calculate_semantic_projection_digest(envelope_change) == original

    changed_score = replace(manifest.scores[0], value="1")
    semantic_change = replace(
        manifest,
        scores=(changed_score, manifest.scores[1]),
        projection=replace(
            manifest.projection,
            projection_digest="0" * 64,
        ),
    )
    assert calculate_semantic_projection_digest(semantic_change) != original


def test_manifest_rejects_unknown_or_private_fields() -> None:
    native = academic_result_manifest_to_dict(_manifest())
    score = native["scores"][0]
    assert isinstance(score, dict)
    score["rationale"] = "This must not be public."

    with pytest.raises(ConcordAcademicResultManifestValidationError):
        academic_result_manifest_from_dict(native)


def test_manifest_projection_omits_private_narrative_fields() -> None:
    native = academic_result_manifest_to_dict(_manifest())
    encoded = repr(native)

    assert "rationale" not in encoded
    assert "'note'" not in encoded
    assert "aggregation_guidance" not in encoded
    assert "created_provenance" not in encoded
    assert "display_label_snapshot" not in encoded
    assert "role_snapshot" not in encoded


def test_non_score_requires_matching_minimized_status_reason() -> None:
    manifest = _manifest()
    local = manifest.scores[0]
    absent = replace(
        local,
        disposition="absent",
        value=None,
        status_reason=StatusReasonProjection(
            reason_code="absent",
            recorded_by=_actor(),
            recorded_at=_time(13),
            related_record=RecordReferenceProjection(
                module_id="concord",
                record_kind="session",
                record_id="session-1",
                contract_version=None,
            ),
        ),
    )
    candidate = replace(
        manifest,
        scores=(absent, manifest.scores[1]),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    validated = with_semantic_projection_digest(candidate)
    assert validated.scores[0].value is None
    assert validated.scores[0].status_reason is not None
    assert validated.scores[0].status_reason.reason_code == "absent"

    native = academic_result_manifest_to_dict(validated)
    first_score = native["scores"][0]
    assert isinstance(first_score, dict)
    assert "value" not in first_score
    assert "status_reason" in first_score

    scored_native = academic_result_manifest_to_dict(manifest)
    scored = scored_native["scores"][0]
    assert isinstance(scored, dict)
    assert "value" in scored
    assert "status_reason" not in scored

    moderation = scored_native["moderation_records"][0]
    assert isinstance(moderation, dict)
    assert "qualification" not in moderation

    with pytest.raises(ConcordAcademicResultManifestValidationError):
        replace(absent, status_reason=None)


def test_score_value_must_match_scale_type_sensitively() -> None:
    manifest = _manifest()
    local = manifest.scores[0]

    # True is an exact level; a different unsupported value is not.
    invalid = replace(local, value=False)
    candidate = replace(
        manifest,
        scores=(invalid, manifest.scores[1]),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    candidate = replace(
        candidate,
        projection=replace(
            candidate.projection,
            projection_digest=calculate_semantic_projection_digest(candidate),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(candidate)


def test_standards_projection_is_exact_standard_backed_subset() -> None:
    manifest = _manifest()

    missing = replace(
        manifest,
        standards_result_projection=(),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    missing = replace(
        missing,
        projection=replace(
            missing.projection,
            projection_digest=calculate_semantic_projection_digest(missing),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(missing)

    extra = replace(
        manifest,
        standards_result_projection=(
            StandardsResultProjection("score-local", "standard-2"),
            StandardsResultProjection("score-standard", "standard-1"),
        ),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    extra = replace(
        extra,
        projection=replace(
            extra.projection,
            projection_digest=calculate_semantic_projection_digest(extra),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(extra)


def test_current_state_derives_only_from_explicit_score_supersession() -> None:
    manifest = _manifest()
    predecessor = replace(
        manifest.scores[0],
        score_record_id="score-local-1",
        current_state="superseded",
    )
    successor = replace(
        manifest.scores[0],
        score_record_id="score-local-2",
        supersedes_score_record_id="score-local-1",
        current_state="current",
        scored_at=_time(14),
    )
    candidate = replace(
        manifest,
        scores=(predecessor, successor, manifest.scores[1]),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    validated = with_semantic_projection_digest(candidate)
    assert [item.current_state for item in validated.scores[:2]] == [
        "superseded",
        "current",
    ]

    wrong = replace(
        validated,
        scores=(
            replace(predecessor, current_state="current"),
            successor,
            validated.scores[2],
        ),
        projection=replace(
            validated.projection, projection_digest="0" * 64
        ),
    )
    wrong = replace(
        wrong,
        projection=replace(
            wrong.projection,
            projection_digest=calculate_semantic_projection_digest(wrong),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(wrong)


def test_manifest_rejects_evidence_only_or_empty_score_projection() -> None:
    manifest = _manifest()

    evidence_only = replace(
        manifest,
        activity_context=replace(
            manifest.activity_context,
            scoring_orientation="evidence_only",
        ),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    evidence_only = replace(
        evidence_only,
        projection=replace(
            evidence_only.projection,
            projection_digest=calculate_semantic_projection_digest(
                evidence_only
            ),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(evidence_only)

    empty = replace(
        manifest,
        scores=(),
        score_evidence_links=(),
        moderation_records=(),
        standards_result_projection=(),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    empty = replace(
        empty,
        projection=replace(
            empty.projection,
            projection_digest=calculate_semantic_projection_digest(empty),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(empty)


def test_strict_decoder_rejects_duplicate_keys_and_noncanonical_json() -> None:
    data = academic_result_manifest_to_bytes(_manifest())

    duplicate = data.replace(
        b'{"activity_context":',
        b'{"activity_context":null,"activity_context":',
        1,
    )
    with pytest.raises(ConcordAcademicResultManifestDecodeError):
        academic_result_manifest_from_bytes(duplicate)

    noncanonical = data.replace(b":", b": ", 1)
    with pytest.raises(ConcordAcademicResultManifestDecodeError):
        academic_result_manifest_from_bytes(noncanonical)


def test_identity_and_exact_moderation_evidence_are_cross_validated() -> None:
    manifest = _manifest()

    wrong_source = replace(
        manifest,
        source_activity=ModuleRecordRef(
            module_id="concord",
            record_kind="activity",
            record_id="activity-other",
            contract_version="concord_activity_v1",
        ),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    wrong_source = replace(
        wrong_source,
        projection=replace(
            wrong_source.projection,
            projection_digest=calculate_semantic_projection_digest(
                wrong_source
            ),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(wrong_source)

    other_evidence = replace(
        manifest.score_evidence_links[0].evidence_reference,
        record_id="result-other",
    )
    wrong_moderation = replace(
        manifest.moderation_records[0],
        target_evidence_reference=other_evidence,
    )
    mismatch = replace(
        manifest,
        moderation_records=(wrong_moderation,),
        projection=replace(
            manifest.projection, projection_digest="0" * 64
        ),
    )
    mismatch = replace(
        mismatch,
        projection=replace(
            mismatch.projection,
            projection_digest=calculate_semantic_projection_digest(mismatch),
        ),
    )
    with pytest.raises(ConcordAcademicResultManifestValidationError):
        validate_academic_result_manifest(mismatch)
