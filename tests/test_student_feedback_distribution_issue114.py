from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from pds_core.rosters import Roster, StudentRecord
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

import concord.workflows.activity_score_analysis as score_analysis
import concord.workflows.student_feedback_distribution as distribution
from concord.model_validation import ConcordRecordGraph
from concord.models import (
    Activity,
    ActorReference,
    Criterion,
    PrivacyPolicy,
    Provenance,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
    ScoringScaleLevel,
)
from concord.workflows import (
    FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    FEEDBACK_AVAILABILITY_NONE,
    FEEDBACK_AVAILABILITY_UNRESOLVED,
    STUDENT_FEEDBACK_PREPARATION_SCOPE,
    load_student_feedback_roster_preparation,
    student_feedback_roster_preparation_from_context,
)
from concord.workflows.activity_read import ActivityReadContext
from concord.workflows.errors import ConcordWorkflowValidationError


def _actor() -> ActorReference:
    return ActorReference(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="concord",
    )


def _provenance() -> Provenance:
    return Provenance(
        actor=_actor(),
        timestamp="2026-10-07T19:00:00+00:00",
        source_kind="manual",
    )


def _target(
    target_kind: str,
    target_id: str,
    *,
    owning_system: str | None = None,
) -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind=target_kind,
        target_id=target_id,
        owning_system=(
            owning_system
            if owning_system is not None
            else ("core" if target_kind == "core_student" else "concord")
        ),
    )


def _activity() -> Activity:
    return Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        title="Memoir Revision",
        activity_type="project",
        scoring_orientation="local_criteria_only",
        status="active",
        created_provenance=_provenance(),
    )


def _criterion() -> Criterion:
    return Criterion(
        criterion_id="criterion-1",
        criterion_set_id="set-1",
        key="criterion-1",
        label="Use of Evidence",
        definition="Synthetic criterion.",
        criterion_kind="local",
        supported_target_kinds=(
            "core_student",
            "concord_group",
        ),
        status="active",
        created_provenance=_provenance(),
        default_scoring_scale_id="scale-1",
    )


def _scale() -> ScoringScale:
    return ScoringScale(
        scoring_scale_id="scale-1",
        lineage_id="scale-lineage",
        name="Four Levels",
        revision=1,
        scale_type="ordinal",
        levels=(
            ScoringScaleLevel(
                value=2,
                label="Developing",
                meaning="Developing evidence",
                position=1,
            ),
            ScoringScaleLevel(
                value=3,
                label="Meeting",
                meaning="Meeting evidence",
                position=2,
            ),
            ScoringScaleLevel(
                value=4,
                label="Exceeding",
                meaning="Exceeding evidence",
                position=3,
            ),
        ),
        status="active",
        created_provenance=_provenance(),
    )


def _score(
    score_id: str,
    target: ScoreTargetReference,
    *,
    value: int | None = 3,
    disposition: str = "scored",
    supersedes: str | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        score_record_id=score_id,
        activity_id="activity-1",
        target_reference=target,
        criterion_id="criterion-1",
        score_kind="local",
        scoring_scale_id="scale-1",
        disposition=disposition,
        basis="professional_judgment",
        scorer=_actor(),
        scored_at="2026-10-07T19:05:00+00:00",
        moderation_complete=disposition == "scored",
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        value=value,
        rationale="Teacher-only rationale.",
        supersedes_score_record_id=supersedes,
    )


def _context(
    extra_scores: tuple[ScoreRecord, ...] = (),
) -> ActivityReadContext:
    activity = _activity()
    old = _score(
        "score-old",
        _target("core_student", "student-1"),
        value=2,
    )
    current = _score(
        "score-current",
        _target("core_student", "student-1"),
        value=3,
        supersedes=old.score_record_id,
    )
    non_score = _score(
        "score-student-3",
        _target("core_student", "student-3"),
        value=None,
        disposition="absent",
    )
    group_score = _score(
        "score-group",
        _target("concord_group", "group-1"),
        value=4,
    )
    return ActivityReadContext(
        root=Path("/synthetic/read-only"),
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        snapshot_revision=10,
        snapshot_sha256="b" * 64,
        graph=ConcordRecordGraph(
            activities=(activity,),
            criteria=(_criterion(),),
            scoring_scales=(_scale(),),
            score_records=(old, current, non_score, group_score, *extra_scores),
        ),
        activity=activity,
    )


def _student(
    student_id: str,
    first_name: str,
    last_name: str,
) -> StudentRecord:
    return StudentRecord(
        class_id="class-1",
        student_id=student_id,
        last_name=last_name,
        first_name=first_name,
        period="2",
        extra_fields={},
    )


def _roster(
    *,
    unsafe_second_name: bool = False,
) -> Roster:
    second_first = r"C:\Users\Teacher" if unsafe_second_name else "John"
    return Roster(
        class_id="class-1",
        students=(
            _student("student-1", "Jane", "Doe"),
            _student("student-2", second_first, "Smith"),
            _student("student-3", "Alex", "Rivera"),
        ),
        columns=("class_id", "student_id", "last_name", "first_name", "period"),
    )


def test_roster_preparation_partitions_in_authoritative_roster_order() -> None:
    prepared = student_feedback_roster_preparation_from_context(
        _context(),
        _roster(),
    )

    assert prepared.sharing_scope == STUDENT_FEEDBACK_PREPARATION_SCOPE
    assert prepared.roster_count == 3
    assert prepared.distributable_count == 2
    assert prepared.no_feedback_count == 1
    assert prepared.unresolved_count == 0

    assert tuple(item.student_id for item in prepared.entries) == (
        "student-1",
        "student-2",
        "student-3",
    )
    assert tuple(item.availability for item in prepared.entries) == (
        FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
        FEEDBACK_AVAILABILITY_NONE,
        FEEDBACK_AVAILABILITY_DISTRIBUTABLE,
    )

    first = prepared.entries[0]
    assert first.projection is not None
    assert first.projection.current_score_count == 1
    assert first.projection.results[0].value == 3
    assert first.projection.results[0].value_label == "Meeting"

    second = prepared.entries[1]
    assert second.projection is not None
    assert second.projection.current_score_count == 0

    third = prepared.entries[2]
    assert third.projection is not None
    assert third.projection.results[0].disposition == "absent"
    assert third.projection.results[0].value is None

    with pytest.raises(FrozenInstanceError):
        prepared.class_id = "changed"  # type: ignore[misc]


def test_group_score_does_not_fan_out_to_roster_student() -> None:
    prepared = student_feedback_roster_preparation_from_context(
        _context(),
        _roster(),
    )

    student_two = prepared.entries[1]
    assert student_two.student_id == "student-2"
    assert student_two.availability == FEEDBACK_AVAILABILITY_NONE
    assert student_two.projection is not None
    assert student_two.projection.results == ()


def test_roster_preparation_calculates_current_heads_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = score_analysis.current_score_lineage_heads
    calls = 0

    def counting(records: object) -> tuple[ScoreRecord, ...]:
        nonlocal calls
        calls += 1
        return original(records)  # type: ignore[arg-type]

    monkeypatch.setattr(
        score_analysis,
        "current_score_lineage_heads",
        counting,
    )

    student_feedback_roster_preparation_from_context(
        _context(),
        _roster(),
    )

    assert calls == 1


def test_load_preparation_loads_core_roster_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    roster = _roster()

    def fake_load(root: object, class_id: str) -> Roster:
        nonlocal calls
        calls += 1
        assert class_id == "class-1"
        return roster

    monkeypatch.setattr(
        distribution,
        "load_required_roster",
        fake_load,
    )

    prepared = load_student_feedback_roster_preparation(_context())

    assert calls == 1
    assert prepared.roster_count == 3


def test_unsafe_student_visible_semantics_are_unresolved() -> None:
    prepared = student_feedback_roster_preparation_from_context(
        _context(),
        _roster(unsafe_second_name=True),
    )

    unresolved = prepared.entries[1]
    assert unresolved.student_id == "student-2"
    assert unresolved.student_display_name is None
    assert unresolved.availability == FEEDBACK_AVAILABILITY_UNRESOLVED
    assert unresolved.projection is None
    assert unresolved.unresolved_reason == "unsafe_student_feedback_semantics"
    assert prepared.unresolved_count == 1
    assert prepared.no_feedback_count == 0


def test_orphan_current_student_target_fails_closed() -> None:
    orphan = _score(
        "score-orphan",
        _target("core_student", "student-not-in-roster"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="cannot be resolved",
    ):
        student_feedback_roster_preparation_from_context(
            _context((orphan,)),
            _roster(),
        )


def test_non_core_owned_student_target_fails_closed() -> None:
    unresolved = _score(
        "score-external-student",
        _target(
            "core_student",
            "student-1",
            owning_system="external",
        ),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="cannot be resolved",
    ):
        student_feedback_roster_preparation_from_context(
            _context((unresolved,)),
            _roster(),
        )


def test_mismatched_roster_fails_closed() -> None:
    roster = Roster(
        class_id="different-class",
        students=(
            StudentRecord(
                class_id="different-class",
                student_id="student-1",
                last_name="Doe",
                first_name="Jane",
                period="2",
                extra_fields={},
            ),
        ),
        columns=("class_id", "student_id", "last_name", "first_name", "period"),
    )

    with pytest.raises(
        ConcordWorkflowValidationError,
        match="does not match",
    ):
        student_feedback_roster_preparation_from_context(
            _context(),
            roster,
        )
