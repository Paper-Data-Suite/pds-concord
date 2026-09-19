from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace

import pytest

from concord.models import (
    ActorReference,
    ConcordModelError,
    PrivacyPolicy,
    Provenance,
    TemplateAuthorshipExpectation,
    TemplateCompatibility,
    TemplatePageDefinition,
    TemplateRenderingInput,
    TemplateSubjectExpectation,
    TemplateSubjectResolutionExpectation,
    TemplateVersion,
)
from concord.template_serialization import (
    template_from_json_bytes,
    template_to_json_bytes,
)


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-09-18T22:30:00-04:00",
        source_kind="manual",
        application_version="0.3.0",
    )


def _inputs() -> tuple[TemplateRenderingInput, ...]:
    return (
        TemplateRenderingInput(
            input_key="human-fallback",
            label="Human fallback",
            source_kind="human_fallback",
            value_kind="text",
            required=True,
            max_length=160,
        ),
        TemplateRenderingInput(
            input_key="route-payload",
            label="PDS2 route payload",
            source_kind="pds2_route_payload",
            value_kind="text",
            required=True,
        ),
    )


def _page() -> TemplatePageDefinition:
    return TemplatePageDefinition(
        page_key="page-1",
        sequence=1,
        page_kind="primary",
        return_expected=True,
        route_required=True,
        rendering_input_keys=("human-fallback", "route-payload"),
        route_payload_input_key="route-payload",
        human_fallback_input_key="human-fallback",
    )


def _version(
    subject_expectation: (
        TemplateSubjectExpectation | TemplateSubjectResolutionExpectation
    ),
) -> TemplateVersion:
    return TemplateVersion(
        template_version_id="template-version-1",
        template_id="template-1",
        version_label="v1",
        revision_sequence=1,
        rendering_contract_version="concord-template-rendering-v1",
        rendering_specification_reference="rendering-spec-v1",
        rendering_specification_sha256="a" * 64,
        artifact_category="observation",
        page_manifest=(_page(),),
        rendering_inputs=_inputs(),
        default_expected_return_status="returned_expected",
        default_privacy_policy=PrivacyPolicy(
            classification="teacher_and_subjects"
        ),
        compatibility=TemplateCompatibility(
            audience_kinds=("participant",),
        ),
        created_provenance=_provenance(),
        status="active",
        default_authorship_expectation=TemplateAuthorshipExpectation(
            authorship_mode="individual_author",
        ),
        default_subject_expectation=subject_expectation,
    )


def test_legacy_subject_expectation_serializes_with_exact_historical_shape() -> None:
    version = _version(
        TemplateSubjectExpectation(
            subject_kind="core_student",
            required=True,
            multiple_allowed=False,
        )
    )

    encoded = template_to_json_bytes(version)
    parsed = json.loads(encoded)

    assert parsed["default_subject_expectation"] == {
        "multiple_allowed": False,
        "required": True,
        "subject_kind": "core_student",
    }
    assert b'"resolution_mode"' not in encoded
    assert b'"subject_kinds"' not in encoded
    assert b'"subject_role"' not in encoded
    assert b'"allow_target_subject_match"' not in encoded

    loaded = template_from_json_bytes("template_version", encoded)
    assert isinstance(loaded, TemplateVersion)
    assert isinstance(
        loaded.default_subject_expectation,
        TemplateSubjectExpectation,
    )
    assert template_to_json_bytes(loaded) == encoded


def test_relationship_aware_subject_expectation_round_trips_distinctly() -> None:
    expectation = TemplateSubjectResolutionExpectation(
        subject_kinds=("concord_group", "core_student"),
        resolution_mode="explicit",
        subject_role="reviewed_subject",
        required=True,
        multiple_allowed=False,
        allow_target_subject_match=False,
    )
    version = _version(expectation)

    assert expectation.subject_kinds == ("concord_group", "core_student")
    encoded = template_to_json_bytes(version)
    parsed = json.loads(encoded)
    assert parsed["default_subject_expectation"] == {
        "allow_target_subject_match": False,
        "multiple_allowed": False,
        "required": True,
        "resolution_mode": "explicit",
        "subject_kinds": ["concord_group", "core_student"],
        "subject_role": "reviewed_subject",
    }

    loaded = template_from_json_bytes("template_version", encoded)
    assert isinstance(loaded, TemplateVersion)
    assert isinstance(
        loaded.default_subject_expectation,
        TemplateSubjectResolutionExpectation,
    )
    assert template_to_json_bytes(loaded) == encoded


def test_relationship_aware_expectation_supports_session_observation() -> None:
    expectation = TemplateSubjectResolutionExpectation(
        subject_kinds=("concord_session",),
        resolution_mode="session",
        subject_role="session_context",
    )
    assert expectation.subject_kinds == ("concord_session",)
    assert expectation.allow_target_subject_match is True


def test_explicit_resolution_can_name_existing_artifact_subject_kind() -> None:
    expectation = TemplateSubjectResolutionExpectation(
        subject_kinds=("concord_artifact_instance",),
        resolution_mode="explicit",
        subject_role="evaluated_artifact",
    )
    assert expectation.subject_kinds == ("concord_artifact_instance",)


@pytest.mark.parametrize(
    "expectation",
    (
        lambda: TemplateSubjectResolutionExpectation(
            subject_kinds=(),
            resolution_mode="explicit",
            subject_role="reviewed_subject",
        ),
        lambda: TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student",),
            resolution_mode="session",
            subject_role="session_context",
        ),
        lambda: TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student",),
            resolution_mode="target_group",
            subject_role="represented_group",
        ),
        lambda: TemplateSubjectResolutionExpectation(
            subject_kinds=("external_record",),
            resolution_mode="target",
            subject_role="general_subject",
        ),
        lambda: TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student",),
            resolution_mode="guess",
            subject_role="reviewed_subject",
        ),
        lambda: TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student",),
            resolution_mode="explicit",
            subject_role="reviewee",
        ),
    ),
)
def test_relationship_aware_expectation_rejects_invalid_contracts(
    expectation: Callable[[], TemplateSubjectResolutionExpectation],
) -> None:
    with pytest.raises(ConcordModelError):
        expectation()


def test_template_version_accepts_both_subject_expectation_contracts() -> None:
    legacy = _version(TemplateSubjectExpectation(subject_kind="core_student"))
    relationship_aware = replace(
        legacy,
        default_subject_expectation=TemplateSubjectResolutionExpectation(
            subject_kinds=("core_student",),
            resolution_mode="explicit",
            subject_role="reviewed_subject",
            allow_target_subject_match=False,
        ),
    )

    assert isinstance(
        legacy.default_subject_expectation,
        TemplateSubjectExpectation,
    )
    assert isinstance(
        relationship_aware.default_subject_expectation,
        TemplateSubjectResolutionExpectation,
    )

def test_relationship_aware_expectation_fails_closed_under_legacy_subject_kind_access(
) -> None:
    expectation = TemplateSubjectResolutionExpectation(
        subject_kinds=("core_student",),
        resolution_mode="explicit",
        subject_role="reviewed_subject",
        allow_target_subject_match=False,
    )

    with pytest.raises(ConcordModelError, match="subject-resolution planning"):
        _ = expectation.subject_kind

