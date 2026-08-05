from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import (
    Activity,
    ActorReference,
    ArtifactPage,
    ConcordModelError,
    Criterion,
    EvidenceReference,
    Provenance,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
    ScoringScaleLevel,
    Session,
)


@pytest.fixture
def provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="actor-1",
            owning_system="core",
        ),
        timestamp="2026-08-04T12:00:00-04:00",
        source_kind="manual",
    )


def test_activity_is_immutable_and_maps_to_core_work(provenance: Provenance) -> None:
    activity = Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core", record_kind="class", record_id="class-1"
        ),
        title="Synthetic activity",
        activity_type="local:seminar",
        scoring_orientation="mixed",
        standards_profile_id="profile-1",
        focus_standard_ids=["standard-1"],
        status="active",
        created_provenance=provenance,
    )
    assert activity.focus_standard_ids == ("standard-1",)
    assert activity.work_reference.work_id == activity.activity_id
    with pytest.raises(FrozenInstanceError):
        activity.title = "changed"  # type: ignore[misc]


def test_activity_orientation_and_timestamp_are_structural(
    provenance: Provenance,
) -> None:
    with pytest.raises(ConcordModelError):
        Activity(
            activity_id="activity-1",
            class_reference=ModuleRecordRef(
                module_id="core", record_kind="class", record_id="class-1"
            ),
            title="Synthetic activity",
            activity_type="local:seminar",
            scoring_orientation="standards_based",
            status="draft",
            created_provenance=provenance,
        )
    with pytest.raises(ConcordModelError):
        Provenance(
            actor=provenance.actor,
            timestamp="2026-08-04T12:00:00",
            source_kind="manual",
        )


def test_page_route_conditionals(provenance: Provenance) -> None:
    with pytest.raises(ConcordModelError):
        ArtifactPage(
            artifact_page_id="page-1",
            artifact_instance_id="artifact-1",
            page_number=1,
            page_kind="primary",
            return_expected=True,
            route_required=True,
            page_status="planned",
            created_provenance=provenance,
        )


def test_scale_values_are_type_sensitive_and_finite(provenance: Provenance) -> None:
    with pytest.raises(ConcordModelError):
        ScoringScale(
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage",
            name="Invalid",
            revision=1,
            scale_type="teacher_defined",
            levels=(
                ScoringScaleLevel(value=1, label="One", meaning="Integer"),
                ScoringScaleLevel(value=1, label="Again", meaning="Duplicate"),
            ),
            status="active",
            created_provenance=provenance,
        )
    scale = ScoringScale(
        scoring_scale_id="scale-2",
        lineage_id="scale-lineage-2",
        name="Typed",
        revision=1,
        scale_type="teacher_defined",
        levels=(
            ScoringScaleLevel(value=True, label="Yes", meaning="Boolean"),
            ScoringScaleLevel(value=1, label="One", meaning="Integer"),
        ),
        status="active",
        created_provenance=provenance,
    )
    assert scale.level_for_value(True) != scale.level_for_value(1)
    with pytest.raises(ConcordModelError):
        ScoringScaleLevel(value=math.inf, label="Bad", meaning="Not finite")


def test_score_non_score_dispositions_forbid_values(provenance: Provenance) -> None:
    with pytest.raises(ConcordModelError):
        ScoreRecord(
            score_record_id="score-1",
            activity_id="activity-1",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            score_kind="local",
            scoring_scale_id="scale-1",
            disposition="not_observed",
            value=0,
            basis="professional_judgment",
            scorer=provenance.actor,
            scored_at=provenance.timestamp,
            rationale="No observation was available.",
            moderation_complete=True,
            privacy_policy=_privacy(),
        )


def test_exact_mapping_round_trip_and_schema_rejection(provenance: Provenance) -> None:
    session = Session(
        session_id="session-1",
        activity_id="activity-1",
        sequence=1,
        status="planned",
        created_provenance=provenance,
    )
    data = record_to_dict(session)
    assert record_from_dict("session", data) == session
    with pytest.raises(ConcordModelError, match="unknown field"):
        record_from_dict("session", {**data, "surprise": True})
    del data["sequence"]
    with pytest.raises(ConcordModelError, match="missing required"):
        record_from_dict("session", data)


def test_external_evidence_requires_immutable_lineage() -> None:
    with pytest.raises(ConcordModelError):
        EvidenceReference(
            evidence_kind="scoreform_result",
            owning_system="scoreform",
            record_id="result-1",
        )


def test_local_criterion_does_not_acquire_governing_standard(
    provenance: Provenance,
) -> None:
    with pytest.raises(ConcordModelError):
        Criterion(
            criterion_id="criterion-1",
            criterion_set_id="set-1",
            key="clarity",
            label="Clarity",
            definition="Communicates a coherent result.",
            criterion_kind="local",
            standard_id="standard-1",
            supported_target_kinds=("concord_group",),
            status="active",
            created_provenance=provenance,
        )


def _privacy():
    from concord.models import PrivacyPolicy

    return PrivacyPolicy(classification="teacher_restricted")
