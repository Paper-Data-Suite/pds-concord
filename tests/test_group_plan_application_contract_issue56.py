from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

import pytest
from pds_core.identifiers import validate_identifier
from pds_core.routing_models import ModuleRecordRef

from concord.group_plan_application import (
    GroupPlanApplicationError,
    application_digest,
    build_application_manifest,
    derive_application_specs,
    derive_group_id,
    derive_membership_id,
    new_application_id,
)
from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import (
    ActorReference,
    ConcordModelError,
    EffectiveContext,
    GroupPlan,
    PlannedGroup,
    Provenance,
)


def _provenance(day: int) -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp=datetime(
            2026,
            8,
            day,
            15,
            0,
            tzinfo=timezone.utc,
        ).isoformat(),
        source_kind="manual",
        application_version="0.3.0",
    )


def _approved_plan() -> GroupPlan:
    return GroupPlan(
        group_plan_id="plan-1",
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        strategy="manual",
        status="approved",
        roster_student_ids=("student-1",),
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1",),
            ),
        ),
        unresolved_student_ids=(),
        created_provenance=_provenance(1),
        previewed_provenance=_provenance(2),
        approved_provenance=_provenance(3),
    )


def test_applied_group_plan_requires_application_identity_and_digest() -> None:
    approved = _approved_plan()
    with pytest.raises(ConcordModelError, match="application ID and digest"):
        replace(
            approved,
            status="applied",
            applied_provenance=_provenance(4),
        )

    applied = replace(
        approved,
        status="applied",
        applied_provenance=_provenance(4),
        applied_application_id="apply-1",
        applied_application_digest="a" * 64,
    )
    assert record_from_dict("group_plan", record_to_dict(applied)) == applied


def test_application_fields_are_forbidden_before_applied_status() -> None:
    approved = _approved_plan()
    with pytest.raises(ConcordModelError, match="only allowed on applied"):
        replace(approved, applied_application_id="apply-1")
    with pytest.raises(ConcordModelError, match="only allowed on applied"):
        replace(approved, applied_application_digest="a" * 64)


def test_application_identity_and_digest_shape_are_strict() -> None:
    approved = _approved_plan()
    with pytest.raises(ConcordModelError, match="letters, numbers"):
        replace(approved, applied_application_id="apply/id")
    with pytest.raises(ConcordModelError, match="lowercase SHA-256"):
        replace(approved, applied_application_digest="A" * 64)


def test_pre_issue56_group_plan_payload_still_round_trips_without_new_fields() -> None:
    approved = _approved_plan()
    payload = record_to_dict(approved)
    assert "applied_application_id" not in payload
    assert "applied_application_digest" not in payload
    assert record_from_dict("group_plan", payload) == approved


def test_new_application_id_is_core_valid_and_injectable() -> None:
    application_id = new_application_id(
        uuid_factory=lambda: UUID("12345678-1234-5678-1234-567812345678")
    )
    assert application_id == "apply-12345678123456781234567812345678"
    assert validate_identifier(application_id) == application_id


def test_exact_v1_identity_derivation_fixture() -> None:
    group_id = derive_group_id("apply-123", "plan-1", "group-a")
    membership_id = derive_membership_id(
        "apply-123", "plan-1", "group-a", "student-1"
    )
    assert group_id == (
        "group-8a2e74422efc14ff462076747069b6b1b70717722325c4f558499b24b11eb36a"
    )
    assert membership_id == (
        "membership-ba0a166350a85edf01b3dec1c36a015f9609db33bc90853e902a36abfb05ffba"
    )
    assert group_id != "group-a"
    assert membership_id != "student-1"
    assert validate_identifier(group_id) == group_id
    assert validate_identifier(membership_id) == membership_id


def test_identity_derivation_changes_with_application_or_subject_inputs() -> None:
    baseline_group = derive_group_id("apply-1", "plan-1", "group-a")
    baseline_member = derive_membership_id(
        "apply-1", "plan-1", "group-a", "student-1"
    )
    assert derive_group_id("apply-2", "plan-1", "group-a") != baseline_group
    assert derive_group_id("apply-1", "plan-2", "group-a") != baseline_group
    assert derive_group_id("apply-1", "plan-1", "group-b") != baseline_group
    assert (
        derive_membership_id("apply-1", "plan-1", "group-a", "student-2")
        != baseline_member
    )


def test_application_specs_preserve_group_context_and_use_fallback_only_for_members(
) -> None:
    explicit = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-2",),
    )
    fallback = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )
    groups, memberships = derive_application_specs(
        application_id="apply-1",
        group_plan_id="plan-1",
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-b",
                label="B",
                student_ids=("student-2",),
                effective_context=explicit,
            ),
            PlannedGroup(
                planned_group_key="group-a",
                label="A",
                student_ids=("student-1",),
            ),
        ),
        fallback_effective_context=fallback,
    )
    assert tuple(item.planned_group_key for item in groups) == ("group-a", "group-b")
    assert groups[0].effective_context is None
    assert groups[1].effective_context == explicit
    by_student = {item.student_id: item for item in memberships}
    assert by_student["student-1"].effective_context == fallback
    assert by_student["student-2"].effective_context == explicit


def test_contextless_empty_group_does_not_require_fallback() -> None:
    groups, memberships = derive_application_specs(
        application_id="apply-1",
        group_plan_id="plan-1",
        proposed_groups=(
            PlannedGroup(planned_group_key="empty", label="Empty"),
        ),
        fallback_effective_context=None,
    )
    assert len(groups) == 1
    assert memberships == ()


def test_missing_or_irrelevant_fallback_context_is_rejected() -> None:
    group = PlannedGroup(
        planned_group_key="group-a",
        label="A",
        student_ids=("student-1",),
    )
    with pytest.raises(GroupPlanApplicationError, match="required"):
        derive_application_specs(
            application_id="apply-1",
            group_plan_id="plan-1",
            proposed_groups=(group,),
            fallback_effective_context=None,
        )

    explicit = replace(
        group,
        effective_context=EffectiveContext(
            activity_id="activity-1",
            session_ids=("session-1",),
        ),
    )
    with pytest.raises(GroupPlanApplicationError, match="not allowed"):
        derive_application_specs(
            application_id="apply-1",
            group_plan_id="plan-1",
            proposed_groups=(explicit,),
            fallback_effective_context=EffectiveContext(
                activity_id="activity-1",
                session_ids=("session-2",),
            ),
        )


def test_exact_application_manifest_digest_fixture_and_order_independence() -> None:
    fallback = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )
    groups, memberships = derive_application_specs(
        application_id="apply-123",
        group_plan_id="plan-1",
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="Group A",
                student_ids=("student-1",),
            ),
        ),
        fallback_effective_context=fallback,
    )
    manifest = build_application_manifest(
        application_id="apply-123",
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        group_plan_record_revision=4,
        expected_snapshot_revision=8,
        fallback_effective_context=fallback,
        groups=groups,
        memberships=memberships,
        unresolved_student_ids=(),
    )
    assert application_digest(manifest) == (
        "892ee4b1a0e928b696133a2718d9b0fc15e78af3050bec11f3b3b9d4cb2f3cd0"
    )

    reordered = build_application_manifest(
        application_id="apply-123",
        class_id="class-1",
        activity_id="activity-1",
        group_plan_id="plan-1",
        group_plan_record_revision=4,
        expected_snapshot_revision=8,
        fallback_effective_context=fallback,
        groups=tuple(reversed(groups)),
        memberships=tuple(reversed(memberships)),
        unresolved_student_ids=(),
    )
    assert application_digest(reordered) == application_digest(manifest)


def test_application_digest_changes_for_material_preview_inputs() -> None:
    fallback = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )
    groups, memberships = derive_application_specs(
        application_id="apply-1",
        group_plan_id="plan-1",
        proposed_groups=(
            PlannedGroup(
                planned_group_key="group-a",
                label="A",
                student_ids=("student-1",),
            ),
        ),
        fallback_effective_context=fallback,
    )

    def digest(**overrides: object) -> str:
        values: dict[str, object] = {
            "application_id": "apply-1",
            "class_id": "class-1",
            "activity_id": "activity-1",
            "group_plan_id": "plan-1",
            "group_plan_record_revision": 4,
            "expected_snapshot_revision": 8,
            "fallback_effective_context": fallback,
            "groups": groups,
            "memberships": memberships,
            "unresolved_student_ids": (),
        }
        values.update(overrides)
        return application_digest(build_application_manifest(**values))  # type: ignore[arg-type]

    baseline = digest()
    assert digest(application_id="apply-2") != baseline
    assert digest(group_plan_record_revision=5) != baseline
    assert digest(expected_snapshot_revision=9) != baseline
    assert digest(unresolved_student_ids=("student-2",)) != baseline
