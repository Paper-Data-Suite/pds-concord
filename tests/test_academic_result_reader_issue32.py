from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

import concord.academic_result_reader as reader_module
from concord.academic_result_manifest import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    AcademicResultManifest,
    ActivityContextProjection,
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
    ScaleLevelProjection,
    ScoreEvidenceLinkProjection,
    ScoreProjection,
    ScoringScaleProjection,
    StandardsResultProjection,
    SubjectReferenceProjection,
    TargetReferenceProjection,
    academic_result_manifest_to_bytes,
    academic_result_manifest_to_dict,
    with_semantic_projection_digest,
)
from concord.academic_result_reader import (
    ConcordAcademicResultReaderDecodeError,
    ConcordAcademicResultReaderNotFoundError,
    ConcordAcademicResultReaderValidationError,
    list_academic_result_score_evidence_links,
    list_academic_result_scores_for_target,
    lookup_academic_result_criterion,
    lookup_academic_result_criterion_set,
    lookup_academic_result_moderation,
    lookup_academic_result_scale_level,
    lookup_academic_result_score,
    lookup_academic_result_score_evidence_link,
    lookup_academic_result_scoring_scale,
    read_academic_result_manifest,
    validate_academic_result_manifest,
)

EXPECTED_PUBLIC = {
    "AcademicResultManifest",
    "ConcordAcademicResultReaderDecodeError",
    "ConcordAcademicResultReaderError",
    "ConcordAcademicResultReaderNotFoundError",
    "ConcordAcademicResultReaderValidationError",
    "CriterionProjection",
    "CriterionSetProjection",
    "JsonScalar",
    "ModerationProjection",
    "ScaleLevelProjection",
    "ScoreEvidenceLinkProjection",
    "ScoreProjection",
    "ScoringScaleProjection",
    "TargetReferenceProjection",
    "list_academic_result_score_evidence_links",
    "list_academic_result_scores_for_target",
    "lookup_academic_result_criterion",
    "lookup_academic_result_criterion_set",
    "lookup_academic_result_moderation",
    "lookup_academic_result_scale_level",
    "lookup_academic_result_score",
    "lookup_academic_result_score_evidence_link",
    "lookup_academic_result_scoring_scale",
    "read_academic_result_manifest",
    "validate_academic_result_manifest",
}


def _time(hour: int) -> datetime:
    return datetime(2026, 8, 15, hour, 0, tzinfo=timezone.utc)


def _actor() -> PublicActor:
    return PublicActor(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="concord",
    )


def _manifest() -> AcademicResultManifest:
    work = ModuleWorkRef("concord", "class-1", "activity-1")
    source = ModuleRecordRef(
        module_id="concord",
        record_kind="activity",
        record_id="activity-1",
        contract_version="concord_activity_v1",
    )
    teacher = _actor()
    student = SubjectReferenceProjection(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
        contract_version=None,
    )
    external = EvidenceReferenceProjection(
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
        alignment_standard_ids=(),
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
    group_target = TargetReferenceProjection(
        target_kind="concord_group",
        target_id="group-1",
        owning_system="concord",
        contract_version=None,
    )
    local_score = ScoreProjection(
        score_record_id="score-local",
        activity_id="activity-1",
        session_id=None,
        target_reference=group_target,
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
        evidence_locator=external.locator,
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


def _bytes() -> bytes:
    return academic_result_manifest_to_bytes(_manifest())


def test_public_reader_exports_exact_stable_surface() -> None:
    assert set(reader_module.__all__) == EXPECTED_PUBLIC
    assert reader_module.AcademicResultManifest is AcademicResultManifest


def test_exact_canonical_manifest_reads_and_model_validation_is_identity() -> None:
    manifest = _manifest()
    restored = read_academic_result_manifest(
        academic_result_manifest_to_bytes(manifest)
    )
    assert restored == manifest
    assert validate_academic_result_manifest(restored) is restored

    with pytest.raises(ConcordAcademicResultReaderValidationError):
        validate_academic_result_manifest(object())  # type: ignore[arg-type]


def test_reader_requires_exact_immutable_bytes_type() -> None:
    with pytest.raises(
        ConcordAcademicResultReaderValidationError, match="immutable bytes"
    ):
        read_academic_result_manifest("not bytes")  # type: ignore[arg-type]
    with pytest.raises(
        ConcordAcademicResultReaderValidationError, match="immutable bytes"
    ):
        read_academic_result_manifest(bytearray(_bytes()))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw",
    [
        b"not json\n",
        b"\xff\n",
        b'{"record_type":"a","record_type":"b"}\n',
        b'{"number":NaN}\n',
    ],
)
def test_decode_failures_are_normalized_without_payload_leak(raw: bytes) -> None:
    with pytest.raises(
        ConcordAcademicResultReaderDecodeError, match="bytes are invalid"
    ) as caught:
        read_academic_result_manifest(raw)
    assert str(caught.value) == "Academic-result manifest bytes are invalid."


def test_semantic_invalid_bytes_are_decode_failures_without_value_leak() -> None:
    data = academic_result_manifest_to_dict(_manifest())
    data["producer_module_id"] = "private-producer-value"
    raw = (
        json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")

    with pytest.raises(ConcordAcademicResultReaderDecodeError) as caught:
        read_academic_result_manifest(raw)
    assert "private-producer-value" not in str(caught.value)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: (
            json.dumps(
                json.loads(raw),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            )
            + "\n"
        ).encode("utf-8"),
        lambda raw: (
            json.dumps(
                dict(reversed(list(json.loads(raw).items()))),
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8"),
        lambda raw: raw.removesuffix(b"\n"),
        lambda raw: raw.removesuffix(b"\n") + b" \n",
        lambda raw: raw.replace(b".000000Z", b"Z", 1),
    ],
    ids=[
        "alternate-whitespace",
        "alternate-key-order",
        "missing-final-newline",
        "trailing-whitespace",
        "timestamp-rendering",
    ],
)
def test_semantically_equivalent_noncanonical_bytes_fail_validation(mutation) -> None:
    with pytest.raises(
        ConcordAcademicResultReaderValidationError, match="not canonical"
    ):
        read_academic_result_manifest(mutation(_bytes()))


def test_exact_contract_lookups_return_embedded_objects() -> None:
    manifest = _manifest()

    assert lookup_academic_result_criterion_set(manifest, "set-local") is (
        manifest.criterion_sets[0]
    )
    assert lookup_academic_result_criterion(manifest, "criterion-standard") is (
        manifest.criteria[1]
    )
    assert lookup_academic_result_scoring_scale(manifest, "scale-local") is (
        manifest.scoring_scales[0]
    )
    assert lookup_academic_result_score(manifest, "score-standard") is (
        manifest.scores[1]
    )
    assert lookup_academic_result_score_evidence_link(manifest, "link-1") is (
        manifest.score_evidence_links[0]
    )
    assert lookup_academic_result_moderation(manifest, "moderation-1") is (
        manifest.moderation_records[0]
    )


def test_type_sensitive_scale_lookup_does_not_coerce_equal_looking_values() -> None:
    manifest = _manifest()
    expected_types = (int, float, str, bool)
    values = (1, 1.0, "1", True)

    for value, expected_type in zip(values, expected_types, strict=True):
        level = lookup_academic_result_scale_level(
            manifest,
            "scale-local",
            value,
        )
        assert type(level.value) is expected_type
        assert type(level.value) is type(value)

    with pytest.raises(ConcordAcademicResultReaderNotFoundError):
        lookup_academic_result_scale_level(manifest, "scale-standard", 1)
    with pytest.raises(ConcordAcademicResultReaderValidationError):
        lookup_academic_result_scale_level(
            manifest,
            "scale-local",
            float("nan"),
        )


def test_relation_lists_preserve_manifest_semantics_without_selection() -> None:
    manifest = _manifest()
    standard_links = list_academic_result_score_evidence_links(
        manifest,
        "score-standard",
    )
    local_links = list_academic_result_score_evidence_links(
        manifest,
        "score-local",
    )
    group_scores = list_academic_result_scores_for_target(
        manifest,
        manifest.scores[0].target_reference,
    )

    assert standard_links == (manifest.score_evidence_links[0],)
    assert local_links == ()
    assert group_scores == (manifest.scores[0],)
    assert group_scores[0].target_reference.target_kind == "concord_group"
    assert group_scores[0].value is True


def test_missing_and_malformed_lookups_fail_privacy_safely() -> None:
    manifest = _manifest()
    secret = "missing-private-id"

    with pytest.raises(ConcordAcademicResultReaderNotFoundError) as caught:
        lookup_academic_result_score(manifest, secret)
    assert secret not in str(caught.value)

    for lookup in (
        lookup_academic_result_criterion_set,
        lookup_academic_result_criterion,
        lookup_academic_result_scoring_scale,
        lookup_academic_result_score,
        lookup_academic_result_score_evidence_link,
        lookup_academic_result_moderation,
    ):
        with pytest.raises(ConcordAcademicResultReaderValidationError):
            lookup(manifest, "../unsafe")

    with pytest.raises(ConcordAcademicResultReaderValidationError):
        list_academic_result_scores_for_target(
            manifest,
            object(),  # type: ignore[arg-type]
        )


def test_reader_source_has_no_workspace_registry_catalog_or_consumer_boundary() -> None:
    source = Path("concord/academic_result_reader.py").read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "meridian",
        "vitrine",
        "scoreform",
        "quillan",
        "portia",
        "academic_result_manifest_generation",
        "academic_result_publication",
        "academic_work_registration",
        "concord.storage",
        "concord.workflows",
        "publication_storage",
        "academic_catalog",
        "registry_services",
    ):
        assert forbidden not in lowered
    assert "open(" not in source
    assert "Path(" not in source


def test_reader_public_functions_do_not_print(capsys) -> None:
    manifest = read_academic_result_manifest(_bytes())
    lookup_academic_result_criterion_set(manifest, "set-local")
    lookup_academic_result_criterion(manifest, "criterion-local")
    lookup_academic_result_scoring_scale(manifest, "scale-local")
    lookup_academic_result_scale_level(manifest, "scale-local", True)
    lookup_academic_result_score(manifest, "score-local")
    list_academic_result_score_evidence_links(manifest, "score-local")
    list_academic_result_scores_for_target(
        manifest,
        manifest.scores[0].target_reference,
    )
    assert capsys.readouterr() == ("", "")
