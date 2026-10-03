from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    Activity,
    ActorReference,
    PrivacyPolicy,
    Provenance,
    ScoreRecord,
    ScoreTargetReference,
)
from concord.workflows import (
    SCORE_ANALYSIS_BASIS,
    ActivityScoreAnalysis,
    activity_score_analysis_from_context,
)
from concord.workflows._score_lineage import current_score_lineage_heads
from concord.workflows.activity_read import ActivityReadContext


def _actor() -> ActorReference:
    return ActorReference(
        actor_kind="authorized_adult",
        actor_id="teacher-1",
        owning_system="concord",
        display_label_snapshot="Synthetic Teacher",
    )


def _provenance() -> Provenance:
    return Provenance(
        actor=_actor(),
        timestamp="2026-10-03T13:00:00+00:00",
        source_kind="manual",
    )


def _target(kind: str, target_id: str) -> ScoreTargetReference:
    owning_system = "core" if kind == "core_student" else "concord"
    return ScoreTargetReference(
        target_kind=kind,
        target_id=target_id,
        owning_system=owning_system,
    )


def _score(
    score_record_id: str,
    *,
    target: ScoreTargetReference,
    criterion_id: str,
    disposition: str = "scored",
    value: str | int | float | bool | None = 3,
    supersedes: str | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        score_record_id=score_record_id,
        activity_id="activity-1",
        target_reference=target,
        criterion_id=criterion_id,
        score_kind="local",
        scoring_scale_id="scale-1",
        disposition=disposition,
        value=value,
        basis="professional_judgment",
        scorer=_actor(),
        scored_at="2026-10-03T13:30:00+00:00",
        rationale="Synthetic teacher judgment.",
        moderation_complete=disposition == "scored",
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        supersedes_score_record_id=supersedes,
    )


def _context() -> ActivityReadContext:
    activity = Activity(
        activity_id="activity-1",
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id="class-1",
        ),
        title="Synthetic Analysis Activity",
        activity_type="project",
        scoring_orientation="local_criteria_only",
        status="active",
        created_provenance=_provenance(),
    )
    predecessor = _score(
        "score-student-old",
        target=_target("core_student", "student-1"),
        criterion_id="criterion-1",
        value=2,
    )
    successor = _score(
        "score-student-current",
        target=_target("core_student", "student-1"),
        criterion_id="criterion-1",
        value=3,
        supersedes=predecessor.score_record_id,
    )
    group = _score(
        "score-group-current",
        target=_target("concord_group", "group-1"),
        criterion_id="criterion-2",
        disposition="deferred",
        value=None,
    )
    return ActivityReadContext(
        root=Path("/synthetic/read-only"),
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        snapshot_revision=7,
        snapshot_sha256="a" * 64,
        graph=ConcordRecordGraph(
            activities=(activity,),
            score_records=(predecessor, successor, group),
        ),
        activity=activity,
    )


def test_current_score_lineage_heads_exclude_superseded_records() -> None:
    context = _context()

    heads = current_score_lineage_heads(context.graph.score_records)

    assert tuple(item.score_record_id for item in heads) == (
        "score-student-current",
        "score-group-current",
    )
    assert tuple(item.score_record_id for item in context.graph.score_records) == (
        "score-student-old",
        "score-student-current",
        "score-group-current",
    )


def test_activity_analysis_uses_one_context_and_current_heads_only() -> None:
    context = _context()

    analysis = activity_score_analysis_from_context(context)

    assert isinstance(analysis, ActivityScoreAnalysis)
    assert analysis.class_id == "class-1"
    assert analysis.activity_id == "activity-1"
    assert analysis.activity_title == "Synthetic Analysis Activity"
    assert analysis.snapshot_revision == 7
    assert analysis.snapshot_sha256 == "a" * 64
    assert analysis.score_basis == SCORE_ANALYSIS_BASIS
    assert analysis.current_score_count == 2
    assert tuple(
        (item.target_kind, item.score_count)
        for item in analysis.target_kind_counts
    ) == (
        ("core_student", 1),
        ("concord_group", 1),
    )
    assert tuple(item.score_record_id for item in analysis.current_scores) == (
        "score-group-current",
        "score-student-current",
    )
    assert "score-student-old" not in {
        item.score_record_id for item in analysis.current_scores
    }


def test_activity_analysis_does_not_infer_unrecorded_scores() -> None:
    analysis = activity_score_analysis_from_context(_context())

    assert analysis.current_score_count == len(analysis.current_scores) == 2
    assert sum(item.score_count for item in analysis.target_kind_counts) == 2
    assert {item.criterion_id for item in analysis.current_scores} == {
        "criterion-1",
        "criterion-2",
    }
    assert all(
        item.value is not None or item.disposition != "scored"
        for item in analysis.current_scores
    )


def test_activity_analysis_models_are_frozen() -> None:
    analysis = activity_score_analysis_from_context(_context())

    with pytest.raises(FrozenInstanceError):
        analysis.current_score_count = 99  # type: ignore[misc]
