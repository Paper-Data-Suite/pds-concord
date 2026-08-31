from __future__ import annotations

from dataclasses import fields, replace

import pytest

from concord.model_conversion import record_to_dict
from concord.models import (
    ActorReference,
    ArtifactInstance,
    ConcordModelError,
    ConcordRecordReference,
    PrivacyPolicy,
    Provenance,
    TemplateAuthorshipExpectation,
    TemplateCompatibility,
    TemplateDefinition,
    TemplatePageDefinition,
    TemplateRenderingInput,
    TemplateResponseRegion,
    TemplateSubjectExpectation,
    TemplateVersion,
)
from concord.record_registry import RECORD_DESCRIPTORS


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-08-24T17:00:00-04:00",
        source_kind="manual",
        application_version="0.3.0",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _inputs() -> tuple[TemplateRenderingInput, ...]:
    return (
        TemplateRenderingInput(
            input_key="route-payload",
            label="PDS2 route payload",
            source_kind="pds2_route_payload",
            value_kind="text",
            required=True,
        ),
        TemplateRenderingInput(
            input_key="human-fallback",
            label="Human fallback",
            source_kind="human_fallback",
            value_kind="text",
            required=True,
        ),
        TemplateRenderingInput(
            input_key="group-label",
            label="Group label",
            source_kind="group_label",
            value_kind="text",
            required=True,
            max_length=80,
        ),
    )


def _page(
    *,
    page_key: str = "page-1",
    sequence: int = 1,
    route_required: bool = True,
    return_expected: bool = True,
) -> TemplatePageDefinition:
    if route_required:
        keys = ("route-payload", "human-fallback", "group-label")
        route_key = "route-payload"
        fallback_key = "human-fallback"
    else:
        keys = ("group-label",)
        route_key = None
        fallback_key = None
    return TemplatePageDefinition(
        page_key=page_key,
        sequence=sequence,
        page_kind="primary",
        return_expected=return_expected,
        route_required=route_required,
        rendering_input_keys=keys,
        response_regions=(
            TemplateResponseRegion(
                region_key=f"response-{sequence}",
                label="Student notes",
                region_kind="free_response",
                required=False,
            ),
        ),
        route_payload_input_key=route_key,
        human_fallback_input_key=fallback_key,
    )


def _version(**changes: object) -> TemplateVersion:
    kwargs: dict[str, object] = {
        "template_version_id": "template-version-1",
        "template_id": "template-1",
        "version_label": "v1",
        "revision_sequence": 1,
        "rendering_contract_version": "concord-template-rendering-v1",
        "rendering_specification_reference": "rendering-spec-seminar-v1",
        "rendering_specification_sha256": "a" * 64,
        "artifact_category": "discussion_record",
        "page_manifest": (_page(),),
        "rendering_inputs": _inputs(),
        "default_expected_return_status": "returned_expected",
        "default_privacy_policy": _privacy(),
        "compatibility": TemplateCompatibility(
            audience_kinds=("group",),
            activity_type_keys=("socratic_seminar",),
            scoring_orientations=("evidence_only", "mixed"),
            criterion_kinds=("local", "standard_backed"),
        ),
        "created_provenance": _provenance(),
        "status": "active",
        "default_authorship_expectation": TemplateAuthorshipExpectation(
            authorship_mode="recorder_for_group",
        ),
        "default_subject_expectation": TemplateSubjectExpectation(
            subject_kind="concord_group",
        ),
    }
    kwargs.update(changes)
    return TemplateVersion(**kwargs)  # type: ignore[arg-type]


def test_template_definition_validates_reusable_identity_and_owner() -> None:
    definition = TemplateDefinition(
        template_id="template-1",
        name="Seminar Discussion Map",
        purpose="Capture collaborative seminar evidence.",
        artifact_category="discussion_record",
        status="active",
        created_provenance=_provenance(),
        description="Reusable synthetic starter.",
        owner_reference=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
    )
    assert definition.template_id == "template-1"


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("template_id", "../bad"),
        ("name", "  bad"),
        ("purpose", ""),
        ("artifact_category", "not valid"),
        ("status", "distributed"),
    ),
)
def test_template_definition_rejects_invalid_fields(
    field_name: str,
    value: object,
) -> None:
    kwargs: dict[str, object] = {
        "template_id": "template-1",
        "name": "Name",
        "purpose": "Purpose",
        "artifact_category": "discussion_record",
        "status": "draft",
        "created_provenance": _provenance(),
    }
    kwargs[field_name] = value
    with pytest.raises(ConcordModelError):
        TemplateDefinition(**kwargs)  # type: ignore[arg-type]


def test_template_definition_rejects_core_student_owner() -> None:
    with pytest.raises(ConcordModelError, match="Core student"):
        TemplateDefinition(
            template_id="template-1",
            name="Name",
            purpose="Purpose",
            artifact_category="discussion_record",
            status="draft",
            created_provenance=_provenance(),
            owner_reference=ActorReference(
                actor_kind="core_student",
                actor_id="student-1",
                owning_system="core",
            ),
        )


def test_template_models_contain_no_instance_or_signal_fields() -> None:
    forbidden = {
        "class_id",
        "class_reference",
        "activity_id",
        "session_id",
        "group_id",
        "group_plan_id",
        "planned_group_key",
        "membership_id",
        "student_id",
        "participant_reference",
        "source_signal_set_id",
        "source_signal_set_digest",
        "source_signal_dimension_id",
        "band",
        "packet_instance_id",
        "artifact_instance_id",
        "artifact_page_id",
        "route_id",
        "scan_reference_id",
        "score_record_id",
        "publication_id",
    }
    for model in (
        TemplateDefinition,
        TemplateVersion,
        TemplatePageDefinition,
        TemplateRenderingInput,
        TemplateResponseRegion,
        TemplateCompatibility,
    ):
        assert forbidden.isdisjoint(field.name for field in fields(model))


def test_template_version_canonicalizes_order_and_preserves_exact_digest() -> None:
    page_2 = TemplatePageDefinition(
        page_key="page-2",
        sequence=2,
        page_kind="instructional",
        return_expected=False,
        route_required=False,
        rendering_input_keys=("group-label",),
    )
    version = _version(page_manifest=(page_2, _page()))
    assert tuple(page.sequence for page in version.page_manifest) == (1, 2)
    assert tuple(item.input_key for item in version.rendering_inputs) == (
        "group-label",
        "human-fallback",
        "route-payload",
    )
    assert version.rendering_specification_sha256 == "a" * 64


def test_template_version_requires_lowercase_sha256() -> None:
    with pytest.raises(ConcordModelError, match="SHA-256"):
        _version(rendering_specification_sha256="A" * 64)


@pytest.mark.parametrize("revision", (0, -1, True))
def test_template_version_requires_positive_revision_sequence(
    revision: object,
) -> None:
    with pytest.raises(ConcordModelError, match="positive integer"):
        _version(revision_sequence=revision)


def test_first_version_forbids_predecessor_and_successor_requires_one() -> None:
    with pytest.raises(ConcordModelError, match="first Template Version"):
        _version(supersedes_template_version_id="template-version-0")
    successor = _version(
        template_version_id="template-version-2",
        revision_sequence=2,
        supersedes_template_version_id="template-version-1",
    )
    assert successor.supersedes_template_version_id == "template-version-1"
    with pytest.raises(ConcordModelError, match="successor Template Versions"):
        _version(template_version_id="template-version-2", revision_sequence=2)


def test_template_version_rejects_duplicate_or_noncontiguous_pages() -> None:
    with pytest.raises(ConcordModelError, match="duplicate page_key"):
        _version(page_manifest=(_page(), replace(_page(), sequence=2)))
    with pytest.raises(ConcordModelError, match="contiguous"):
        _version(
            page_manifest=(
                _page(),
                TemplatePageDefinition(
                    page_key="page-3",
                    sequence=3,
                    page_kind="instructional",
                    return_expected=False,
                    route_required=False,
                    rendering_input_keys=("group-label",),
                ),
            )
        )


def test_route_required_page_needs_return_and_both_binding_slots() -> None:
    with pytest.raises(ConcordModelError, match="expected to return"):
        _page(return_expected=False)
    with pytest.raises(ConcordModelError, match="route payload"):
        TemplatePageDefinition(
            page_key="page-1",
            sequence=1,
            page_kind="primary",
            return_expected=True,
            route_required=True,
            rendering_input_keys=("group-label",),
        )


def test_nonroute_page_forbids_route_binding_slots() -> None:
    with pytest.raises(ConcordModelError, match="non-route"):
        TemplatePageDefinition(
            page_key="page-1",
            sequence=1,
            page_kind="instructional",
            return_expected=False,
            route_required=False,
            rendering_input_keys=("route-payload",),
            route_payload_input_key="route-payload",
        )


def test_template_version_requires_declared_inputs_and_correct_sources() -> None:
    with pytest.raises(ConcordModelError, match="undeclared"):
        _version(
            page_manifest=(
                replace(
                    _page(),
                    rendering_input_keys=(
                        "route-payload",
                        "human-fallback",
                        "missing-input",
                    ),
                ),
            )
        )
    wrong = tuple(
        replace(item, source_kind="teacher_text")
        if item.input_key == "route-payload"
        else item
        for item in _inputs()
    )
    with pytest.raises(ConcordModelError, match="pds2_route_payload"):
        _version(rendering_inputs=wrong)


def test_response_region_keys_are_unique_across_template_version() -> None:
    duplicate_region = TemplateResponseRegion(
        region_key="response-1",
        label="Second region",
        region_kind="annotation",
        required=False,
    )
    page_2 = TemplatePageDefinition(
        page_key="page-2",
        sequence=2,
        page_kind="instructional",
        return_expected=False,
        route_required=False,
        rendering_input_keys=("group-label",),
        response_regions=(duplicate_region,),
    )
    with pytest.raises(ConcordModelError, match="region keys"):
        _version(page_manifest=(_page(), page_2))


def test_rendering_input_vocab_is_bounded_and_nonexecutable() -> None:
    with pytest.raises(ConcordModelError):
        TemplateRenderingInput(
            input_key="unsafe",
            label="Unsafe",
            source_kind="python_expression",
            value_kind="text",
            required=True,
        )
    with pytest.raises(ConcordModelError):
        TemplateRenderingInput(
            input_key="unsafe",
            label="Unsafe",
            source_kind="teacher_text",
            value_kind="object",
            required=True,
        )
    with pytest.raises(ConcordModelError, match="max_length"):
        TemplateRenderingInput(
            input_key="number",
            label="Number",
            source_kind="teacher_text",
            value_kind="integer",
            required=True,
            max_length=10,
        )


def test_identity_free_template_privacy_only() -> None:
    version = _version(
        default_privacy_policy=PrivacyPolicy(
            classification="group_and_teacher",
        )
    )
    assert version.default_privacy_policy.classification == "group_and_teacher"
    with pytest.raises(ConcordModelError, match="identity-free"):
        _version(
            default_privacy_policy=PrivacyPolicy(
                classification="inherited",
                inherited_from=ConcordRecordReference(
                    record_kind="activity",
                    record_id="activity-1",
                ),
            )
        )


def test_expectations_are_kinds_not_concrete_associations() -> None:
    authorship = TemplateAuthorshipExpectation(
        authorship_mode="collective_group_author",
    )
    subject = TemplateSubjectExpectation(subject_kind="concord_group")
    assert not hasattr(authorship, "author_reference")
    assert not hasattr(subject, "subject_id")


def test_template_compatibility_is_identity_free_and_deterministic() -> None:
    compatibility = TemplateCompatibility(
        audience_kinds=("teacher", "group"),
        activity_type_keys=("project", "socratic_seminar"),
        scoring_orientations=("mixed", "evidence_only"),
        criterion_kinds=("standard_backed", "local"),
    )
    assert compatibility.audience_kinds == ("group", "teacher")
    assert compatibility.scoring_orientations == ("evidence_only", "mixed")
    assert not hasattr(compatibility, "criterion_ids")
    with pytest.raises(ConcordModelError, match="duplicates"):
        TemplateCompatibility(audience_kinds=("group", "group"))


def test_expected_return_status_and_page_manifest_must_agree() -> None:
    nonreturn_page = _page(route_required=False, return_expected=False)
    version = _version(
        page_manifest=(nonreturn_page,),
        default_expected_return_status="return_not_expected",
    )
    assert version.default_expected_return_status == "return_not_expected"
    with pytest.raises(ConcordModelError, match="cannot contain"):
        _version(default_expected_return_status="return_not_expected")
    with pytest.raises(ConcordModelError, match="at least one"):
        _version(
            page_manifest=(nonreturn_page,),
            default_expected_return_status="returned_optional",
        )


def test_template_contract_is_not_activity_native_persistence_yet() -> None:
    registered_types = {descriptor.model_type for descriptor in RECORD_DESCRIPTORS}
    assert TemplateDefinition not in registered_types
    assert TemplateVersion not in registered_types
    with pytest.raises(ConcordModelError, match="registered Concord record"):
        record_to_dict(  # type: ignore[arg-type]
            TemplateDefinition(
                template_id="template-1",
                name="Name",
                purpose="Purpose",
                artifact_category="discussion_record",
                status="draft",
                created_provenance=_provenance(),
            )
        )


def test_existing_artifact_instance_contract_remains_opaque_and_unchanged() -> None:
    artifact = ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="legacy-template-version",
        activity_id="activity-1",
        artifact_category="discussion_record",
        generation_status="planned",
        expected_return_status="returned_expected",
        artifact_status="planned",
        privacy_policy=_privacy(),
        page_ids=("page-1",),
        created_provenance=_provenance(),
    )
    assert artifact.template_version_id == "legacy-template-version"
