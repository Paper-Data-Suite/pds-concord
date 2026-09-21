from __future__ import annotations

import json
from pathlib import Path

import pytest

from concord.models import (
    ARTIFACT_SUBJECT_ROLES,
    ActorReference,
    ArtifactSubject,
    ConcordModelError,
    Provenance,
    SubjectReference,
    TemplateSubjectExpectation,
    TemplateSubjectResolutionExpectation,
)
from concord.models.templates import TEMPLATE_SUBJECT_ROLES
from concord.template_authoring import (
    TEMPLATE_AUTHORING_SCHEMA,
    load_template_authoring_source,
)


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-09-19T02:00:00-04:00",
        source_kind="manual",
        application_version="0.3.0",
    )


def _authoring_document(subject_expectation: dict[str, object]) -> bytes:
    value = {
        "schema_version": "concord_template_authoring_v1",
        "artifact_category": "student_work",
        "version": {
            "version_label": "v2",
            "rendering_contract_version": "concord-template-rendering-v1",
            "rendering_specification_reference": "relationship-aware-layout-v2",
            "page_manifest": [],
            "rendering_inputs": [],
            "default_expected_return_status": "returned_expected",
            "default_privacy_policy": {
                "classification": "teacher_restricted",
            },
            "compatibility": {},
            "default_subject_expectation": subject_expectation,
        },
    }
    return (json.dumps(value, sort_keys=True) + "\n").encode("utf-8")


def test_authoring_schema_stays_v1_for_additive_subject_contract() -> None:
    assert TEMPLATE_AUTHORING_SCHEMA == "concord_template_authoring_v1"


def test_authoring_still_loads_legacy_subject_expectation(tmp_path: Path) -> None:
    path = tmp_path / "legacy.json"
    path.write_bytes(
        _authoring_document(
            {
                "subject_kind": "core_student",
                "required": True,
                "multiple_allowed": False,
            }
        )
    )

    document, prepared = load_template_authoring_source(path)

    expectation = document.version.default_subject_expectation
    assert isinstance(expectation, TemplateSubjectExpectation)
    assert expectation.subject_kind == "core_student"
    assert prepared.data == path.read_bytes()


def test_authoring_loads_relationship_aware_subject_expectation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "relationship-aware.json"
    path.write_bytes(
        _authoring_document(
            {
                "subject_kinds": ["concord_group", "core_student"],
                "resolution_mode": "explicit",
                "subject_role": "reviewed_subject",
                "required": True,
                "multiple_allowed": False,
                "allow_target_subject_match": False,
            }
        )
    )

    document, _prepared = load_template_authoring_source(path)

    expectation = document.version.default_subject_expectation
    assert isinstance(expectation, TemplateSubjectResolutionExpectation)
    assert expectation.subject_kinds == ("concord_group", "core_student")
    assert expectation.resolution_mode == "explicit"
    assert expectation.subject_role == "reviewed_subject"
    assert expectation.allow_target_subject_match is False


def test_authoring_union_remains_strict_for_mixed_subject_shapes(
    tmp_path: Path,
) -> None:
    path = tmp_path / "mixed.json"
    path.write_bytes(
        _authoring_document(
            {
                "subject_kind": "core_student",
                "subject_kinds": ["core_student"],
                "resolution_mode": "explicit",
                "subject_role": "reviewed_subject",
            }
        )
    )

    with pytest.raises(ValueError, match="invalid Template authoring file"):
        load_template_authoring_source(path)


def test_template_and_artifact_subject_roles_share_one_authority() -> None:
    expected = frozenset(
        {
            "observed_participant",
            "represented_group",
            "activity_context",
            "session_context",
            "evaluated_artifact",
            "reviewed_subject",
            "general_subject",
        }
    )
    assert ARTIFACT_SUBJECT_ROLES == expected
    assert TEMPLATE_SUBJECT_ROLES is ARTIFACT_SUBJECT_ROLES


def _artifact_subject(subject_role: str) -> ArtifactSubject:
    return ArtifactSubject(
        artifact_subject_id="artifact-subject-1",
        artifact_instance_id="artifact-1",
        subject_reference=SubjectReference(
            subject_kind="core_student",
            subject_id="student-1",
            owning_system="core",
        ),
        subject_role=subject_role,
        confirmation_status="proposed",
        assignment_source="system",
        created_provenance=_provenance(),
    )


def test_artifact_subject_accepts_new_reviewed_subject_role() -> None:
    assert _artifact_subject("reviewed_subject").subject_role == "reviewed_subject"


def test_artifact_subject_preserves_existing_subject_roles() -> None:
    assert (
        _artifact_subject("observed_participant").subject_role
        == "observed_participant"
    )


def test_artifact_subject_rejects_undeclared_subject_role() -> None:
    with pytest.raises(ConcordModelError):
        _artifact_subject("review_partner")
