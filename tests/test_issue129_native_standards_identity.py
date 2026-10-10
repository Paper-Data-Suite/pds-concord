from __future__ import annotations

from dataclasses import replace

import pytest
from pds_core.routing_models import ModuleRecordRef

from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import (
    Activity,
    ActorReference,
    ConcordModelError,
    Criterion,
    CriterionSet,
    PrivacyPolicy,
    Provenance,
    ScoreRecord,
    ScoreTargetReference,
)

PROFILE_ID = "njsls-ela:profile.2023:11-12"
PRIMARY_STANDARD_ID = "njsls-ela:2023:rl-ts-11-12-4"
ALIGNMENT_STANDARD_ID = "W.NW.11-12.3.D"


def _provenance() -> Provenance:
    return Provenance(
        actor=ActorReference(
            actor_kind="authorized_adult",
            actor_id="teacher-1",
            owning_system="concord",
        ),
        timestamp="2026-10-08T12:00:00-04:00",
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
        title="Standards-backed Activity",
        activity_type="project",
        scoring_orientation="standards_based",
        status="active",
        created_provenance=_provenance(),
        standards_profile_id=PROFILE_ID,
        focus_standard_ids=(PRIMARY_STANDARD_ID, ALIGNMENT_STANDARD_ID),
        criterion_set_ids=("set-1",),
    )


def _criterion_set() -> CriterionSet:
    return CriterionSet(
        criterion_set_id="set-1",
        lineage_id="set-lineage",
        name="Standards criteria",
        purpose="Issue #129 native Standards identity regression.",
        revision=1,
        scope="activity_specific",
        criterion_set_kind="standard_backed",
        criterion_ids=("criterion-1",),
        status="active",
        created_provenance=_provenance(),
        standards_profile_id=PROFILE_ID,
    )


def _criterion() -> Criterion:
    return Criterion(
        criterion_id="criterion-1",
        criterion_set_id="set-1",
        key="analysis",
        label="Analysis",
        definition="Uses evidence to support analysis.",
        criterion_kind="standard_backed",
        supported_target_kinds=("core_student",),
        status="active",
        created_provenance=_provenance(),
        standard_id=PRIMARY_STANDARD_ID,
        alignment_standard_ids=(ALIGNMENT_STANDARD_ID,),
        default_scoring_scale_id="scale-1",
    )


def _score() -> ScoreRecord:
    return ScoreRecord(
        score_record_id="score-1",
        activity_id="activity-1",
        target_reference=ScoreTargetReference(
            target_kind="core_student",
            target_id="student-1",
            owning_system="core",
        ),
        criterion_id="criterion-1",
        score_kind="standard_backed",
        scoring_scale_id="scale-1",
        disposition="scored",
        basis="professional_judgment",
        scorer=_provenance().actor,
        scored_at="2026-10-08T12:30:00-04:00",
        moderation_complete=True,
        privacy_policy=PrivacyPolicy(
            classification="teacher_and_subjects",
        ),
        standard_id=PRIMARY_STANDARD_ID,
        value="meeting",
        rationale="Synthetic teacher judgment.",
    )


@pytest.mark.parametrize(
    ("record_kind", "record"),
    (
        ("activity", _activity()),
        ("criterion_set", _criterion_set()),
        ("criterion", _criterion()),
        ("score_record", _score()),
    ),
)
def test_issue129_native_records_round_trip_exact_standards_identities(
    record_kind: str,
    record: object,
) -> None:
    data = record_to_dict(record)  # type: ignore[arg-type]
    restored = record_from_dict(record_kind, data)

    assert restored == record
    assert record_to_dict(restored) == data


def test_issue129_native_models_accept_punctuation_bearing_standards_ids() -> None:
    activity = _activity()
    criterion_set = _criterion_set()
    criterion = _criterion()
    score = _score()

    assert activity.standards_profile_id == PROFILE_ID
    assert activity.focus_standard_ids == (
        PRIMARY_STANDARD_ID,
        ALIGNMENT_STANDARD_ID,
    )
    assert criterion_set.standards_profile_id == PROFILE_ID
    assert criterion.standard_id == PRIMARY_STANDARD_ID
    assert criterion.alignment_standard_ids == (ALIGNMENT_STANDARD_ID,)
    assert score.standard_id == PRIMARY_STANDARD_ID


def test_issue129_native_standards_identities_follow_core_text_normalization() -> None:
    padded_primary = f"  {PRIMARY_STANDARD_ID}  "
    padded_profile = f"  {PROFILE_ID}  "

    activity = replace(
        _activity(),
        standards_profile_id=padded_profile,
        focus_standard_ids=(padded_primary,),
    )
    criterion_set = replace(
        _criterion_set(),
        standards_profile_id=padded_profile,
    )
    criterion = replace(
        _criterion(),
        standard_id=padded_primary,
        alignment_standard_ids=(f" {ALIGNMENT_STANDARD_ID} ",),
    )
    score = replace(
        _score(),
        standard_id=padded_primary,
    )

    assert activity.standards_profile_id == PROFILE_ID
    assert activity.focus_standard_ids == (PRIMARY_STANDARD_ID,)
    assert criterion_set.standards_profile_id == PROFILE_ID
    assert criterion.standard_id == PRIMARY_STANDARD_ID
    assert criterion.alignment_standard_ids == (ALIGNMENT_STANDARD_ID,)
    assert score.standard_id == PRIMARY_STANDARD_ID


def test_issue129_native_standards_collections_reject_duplicates_after_normalization(
) -> None:
    with pytest.raises(ConcordModelError, match="duplicates"):
        replace(
            _activity(),
            focus_standard_ids=(
                PRIMARY_STANDARD_ID,
                f" {PRIMARY_STANDARD_ID} ",
            ),
        )

    with pytest.raises(ConcordModelError, match="duplicates"):
        replace(
            _criterion(),
            alignment_standard_ids=(
                ALIGNMENT_STANDARD_ID,
                f" {ALIGNMENT_STANDARD_ID} ",
            ),
        )


@pytest.mark.parametrize("invalid", ("", " ", "\t", "\n"))
def test_issue129_native_standards_identity_rejects_blank_text(
    invalid: str,
) -> None:
    with pytest.raises(ConcordModelError):
        replace(_criterion(), standard_id=invalid)

    with pytest.raises(ConcordModelError):
        replace(_activity(), standards_profile_id=invalid)


def test_issue129_native_standards_identity_rejects_non_string_values() -> None:
    with pytest.raises(ConcordModelError):
        replace(
            _criterion(),
            standard_id=123,  # type: ignore[arg-type]
        )

    with pytest.raises(ConcordModelError):
        replace(
            _activity(),
            focus_standard_ids=(123,),  # type: ignore[arg-type]
        )


def test_issue129_unrelated_native_identifiers_remain_routing_safe() -> None:
    with pytest.raises(ConcordModelError):
        replace(
            _activity(),
            activity_id="unsafe/activity:RL.TS.11-12.4",
        )
