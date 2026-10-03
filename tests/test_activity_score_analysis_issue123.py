from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import StandardDefinition, StandardsLibrary

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
    SCORE_ANALYSIS_BASIS,
    ActivityScoreAnalysis,
    StandardCriterionAnalysis,
    StandardScoreAnalysis,
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


def _criterion(
    criterion_id: str,
    label: str,
    *,
    supported_target_kinds: tuple[str, ...] = (
        "core_student",
        "concord_group",
        "concord_artifact_instance",
        "concord_session",
        "concord_activity",
    ),
    standard_id: str | None = None,
) -> Criterion:
    return Criterion(
        criterion_id=criterion_id,
        criterion_set_id="set-1",
        key=criterion_id,
        label=label,
        definition=f"Synthetic definition for {label}.",
        criterion_kind="standard_backed" if standard_id is not None else "local",
        supported_target_kinds=supported_target_kinds,
        status="active",
        created_provenance=_provenance(),
        standard_id=standard_id,
        default_scoring_scale_id="scale-1",
    )


def _scale(
    scoring_scale_id: str = "scale-1",
    *,
    lineage_id: str = "scale-lineage",
    revision: int = 1,
    name: str = "Four levels",
    levels: tuple[ScoringScaleLevel, ...] | None = None,
    supersedes: str | None = None,
) -> ScoringScale:
    return ScoringScale(
        scoring_scale_id=scoring_scale_id,
        lineage_id=lineage_id,
        name=name,
        revision=revision,
        scale_type="ordinal" if levels is None else "teacher_defined",
        levels=levels
        or (
            ScoringScaleLevel(
                value=1,
                label="Beginning",
                meaning="Beginning evidence",
                position=1,
            ),
            ScoringScaleLevel(
                value=2,
                label="Developing",
                meaning="Developing evidence",
                position=2,
            ),
            ScoringScaleLevel(
                value=3,
                label="Secure",
                meaning="Secure evidence",
                position=3,
            ),
            ScoringScaleLevel(
                value=4,
                label="Extending",
                meaning="Extending evidence",
                position=4,
            ),
        ),
        status="active",
        created_provenance=_provenance(),
        supersedes_scoring_scale_id=supersedes,
    )


def _score(
    score_record_id: str,
    *,
    target: ScoreTargetReference,
    criterion_id: str,
    scoring_scale_id: str = "scale-1",
    disposition: str = "scored",
    value: str | int | float | bool | None = 3,
    supersedes: str | None = None,
    standard_id: str | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        score_record_id=score_record_id,
        activity_id="activity-1",
        target_reference=target,
        criterion_id=criterion_id,
        score_kind="standard_backed" if standard_id is not None else "local",
        standard_id=standard_id,
        scoring_scale_id=scoring_scale_id,
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


def _activity() -> Activity:
    return Activity(
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


def _context() -> ActivityReadContext:
    activity = _activity()
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
            criteria=(
                _criterion("criterion-1", "Reasoning"),
                _criterion("criterion-2", "Process"),
            ),
            scoring_scales=(_scale(),),
            score_records=(predecessor, successor, group),
        ),
        activity=activity,
    )


def _context_with(
    *,
    criteria: tuple[Criterion, ...],
    scales: tuple[ScoringScale, ...],
    scores: tuple[ScoreRecord, ...],
) -> ActivityReadContext:
    activity = _activity()
    return ActivityReadContext(
        root=Path("/synthetic/read-only"),
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        snapshot_revision=11,
        snapshot_sha256="b" * 64,
        graph=ConcordRecordGraph(
            activities=(activity,),
            criteria=criteria,
            scoring_scales=scales,
            score_records=scores,
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
    assert analysis.represented_criterion_count == 2
    assert analysis.represented_scoring_scale_count == 1
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


def test_criterion_distributions_use_exact_denominators_and_rounding() -> None:
    criterion = _criterion("criterion-1", "Reasoning")
    scores = (
        _score(
            "score-01",
            target=_target("core_student", "student-01"),
            criterion_id=criterion.criterion_id,
            value=3,
        ),
        _score(
            "score-02",
            target=_target("core_student", "student-02"),
            criterion_id=criterion.criterion_id,
            value=3,
        ),
        _score(
            "score-03",
            target=_target("core_student", "student-03"),
            criterion_id=criterion.criterion_id,
            value=4,
        ),
        *tuple(
            _score(
                f"score-non-{index}",
                target=_target("core_student", f"student-non-{index}"),
                criterion_id=criterion.criterion_id,
                disposition=disposition,
                value=None,
            )
            for index, disposition in enumerate(
                (
                    "insufficient_evidence",
                    "absent",
                    "excused",
                    "not_observed",
                    "not_applicable",
                    "deferred",
                ),
                start=1,
            )
        ),
    )
    analysis = activity_score_analysis_from_context(
        _context_with(criteria=(criterion,), scales=(_scale(),), scores=scores)
    )

    criterion_analysis = analysis.criterion_analyses[0]
    score_slice = criterion_analysis.slices[0]
    assert criterion_analysis.current_judgment_count == 9
    assert score_slice.current_judgment_count == 9
    assert score_slice.scored_count == 3
    assert score_slice.non_score_count == 6
    assert tuple(
        (item.value, item.label, item.count, item.denominator, item.percentage)
        for item in score_slice.value_distributions
    ) == (
        (3, "Secure", 2, 3, "66.7"),
        (4, "Extending", 1, 3, "33.3"),
    )
    assert tuple(
        (item.disposition, item.count, item.denominator, item.percentage)
        for item in score_slice.disposition_distributions
    ) == (
        ("scored", 3, 9, "33.3"),
        ("insufficient_evidence", 1, 9, "11.1"),
        ("absent", 1, 9, "11.1"),
        ("excused", 1, 9, "11.1"),
        ("not_observed", 1, 9, "11.1"),
        ("not_applicable", 1, 9, "11.1"),
        ("deferred", 1, 9, "11.1"),
    )


def test_criterion_distributions_separate_scale_revisions_and_target_kinds() -> None:
    criterion = _criterion("criterion-1", "Reasoning")
    scale_v1 = _scale(
        "scale-v1",
        lineage_id="shared-scale-lineage",
        revision=1,
        name="Scale revision 1",
    )
    scale_v2 = _scale(
        "scale-v2",
        lineage_id="shared-scale-lineage",
        revision=2,
        name="Scale revision 2",
        supersedes="scale-v1",
    )
    scores = (
        _score(
            "score-old-scale",
            target=_target("core_student", "student-1"),
            criterion_id=criterion.criterion_id,
            scoring_scale_id="scale-v1",
            value=4,
        ),
        _score(
            "score-new-scale",
            target=_target("core_student", "student-2"),
            criterion_id=criterion.criterion_id,
            scoring_scale_id="scale-v2",
            value=4,
        ),
        _score(
            "score-group",
            target=_target("concord_group", "group-1"),
            criterion_id=criterion.criterion_id,
            scoring_scale_id="scale-v2",
            value=4,
        ),
    )
    analysis = activity_score_analysis_from_context(
        _context_with(
            criteria=(criterion,),
            scales=(scale_v1, scale_v2),
            scores=scores,
        )
    )

    criterion_analysis = analysis.criterion_analyses[0]
    assert analysis.represented_scoring_scale_count == 2
    assert tuple(
        (
            item.scoring_scale_id,
            item.scoring_scale_revision,
            item.target_kind,
            item.current_judgment_count,
        )
        for item in criterion_analysis.slices
    ) == (
        ("scale-v1", 1, "core_student", 1),
        ("scale-v2", 2, "core_student", 1),
        ("scale-v2", 2, "concord_group", 1),
    )
    assert all(item.current_judgment_count == 1 for item in criterion_analysis.slices)


def test_scale_value_distribution_preserves_type_sensitive_native_values() -> None:
    criterion = _criterion("criterion-types", "Typed values")
    levels = (
        ScoringScaleLevel(value=1, label="Integer", meaning="Integer one."),
        ScoringScaleLevel(value=1.0, label="Float", meaning="Float one."),
        ScoringScaleLevel(value="1", label="String", meaning="String one."),
        ScoringScaleLevel(value=True, label="Boolean", meaning="Boolean true."),
    )
    scale = _scale(
        "scale-types",
        lineage_id="scale-types-lineage",
        name="Type-sensitive values",
        levels=levels,
    )
    typed_values: tuple[tuple[str, int | float | str | bool, type[object]], ...] = (
        ("int", 1, int),
        ("float", 1.0, float),
        ("string", "1", str),
        ("bool", True, bool),
    )
    scores = tuple(
        _score(
            f"score-{suffix}",
            target=_target("core_student", f"student-{suffix}"),
            criterion_id=criterion.criterion_id,
            scoring_scale_id=scale.scoring_scale_id,
            value=value,
        )
        for suffix, value, _ in typed_values
    )
    analysis = activity_score_analysis_from_context(
        _context_with(criteria=(criterion,), scales=(scale,), scores=scores)
    )

    values = analysis.criterion_analyses[0].slices[0].value_distributions
    assert tuple(item.label for item in values) == (
        "Integer",
        "Float",
        "String",
        "Boolean",
    )
    assert tuple(type(item.value) for item in values) == tuple(
        expected_type for _, _, expected_type in typed_values
    )
    assert all(item.count == 1 for item in values)
    assert all(item.denominator == 4 for item in values)
    assert all(item.percentage == "25.0" for item in values)


def test_superseded_score_is_not_counted_in_criterion_distribution() -> None:
    analysis = activity_score_analysis_from_context(_context())

    criterion_analysis = next(
        item
        for item in analysis.criterion_analyses
        if item.criterion_id == "criterion-1"
    )
    score_slice = criterion_analysis.slices[0]
    assert criterion_analysis.current_judgment_count == 1
    assert tuple(
        (item.value, item.count) for item in score_slice.value_distributions
    ) == ((3, 1),)


def test_analysis_contract_exposes_no_grade_or_completion_inference_fields() -> None:
    names = {
        field.name
        for model in (
            ActivityScoreAnalysis,
            type(
                activity_score_analysis_from_context(_context()).criterion_analyses[0]
            ),
            type(
                activity_score_analysis_from_context(_context())
                .criterion_analyses[0]
                .slices[0]
            ),
        )
        for field in fields(model)
    }
    forbidden_fragments = (
        "average",
        "grade",
        "mastery",
        "proficiency",
        "missing",
        "required",
    )
    assert not any(
        fragment in name
        for name in names
        for fragment in forbidden_fragments
    )

def test_standards_view_groups_criteria_without_collapsing_scale_slices() -> None:
    standard_id = "standard-1"
    first = _criterion(
        "criterion-a",
        "Uses Evidence",
        standard_id=standard_id,
    )
    second = _criterion(
        "criterion-b",
        "Explains Reasoning",
        standard_id=standard_id,
    )
    local = _criterion("criterion-local", "Local Process")
    scale_a = _scale(
        "scale-a",
        lineage_id="scale-a-lineage",
        name="Evidence rubric",
    )
    scale_b = _scale(
        "scale-b",
        lineage_id="scale-b-lineage",
        name="Reasoning rubric",
    )
    scores = (
        _score(
            "score-a",
            target=_target("core_student", "student-a"),
            criterion_id=first.criterion_id,
            scoring_scale_id=scale_a.scoring_scale_id,
            value=3,
            standard_id=standard_id,
        ),
        _score(
            "score-b",
            target=_target("core_student", "student-b"),
            criterion_id=second.criterion_id,
            scoring_scale_id=scale_b.scoring_scale_id,
            value=4,
            standard_id=standard_id,
        ),
        _score(
            "score-local",
            target=_target("core_student", "student-c"),
            criterion_id=local.criterion_id,
            scoring_scale_id=scale_a.scoring_scale_id,
            value=2,
        ),
    )
    analysis = activity_score_analysis_from_context(
        _context_with(
            criteria=(first, second, local),
            scales=(scale_a, scale_b),
            scores=scores,
        )
    )

    assert len(analysis.standard_analyses) == 1
    standard = analysis.standard_analyses[0]
    assert isinstance(standard, StandardScoreAnalysis)
    assert standard.standard_id == standard_id
    assert standard.standard_label == standard_id
    assert standard.standard_code is None
    assert standard.standard_short_name is None
    assert tuple(item.criterion_id for item in standard.criteria) == (
        "criterion-a",
        "criterion-b",
    )
    assert all(
        isinstance(item, StandardCriterionAnalysis)
        for item in standard.criteria
    )
    assert tuple(
        item.slices[0].scoring_scale_id for item in standard.criteria
    ) == ("scale-a", "scale-b")
    assert "criterion-local" not in {
        item.criterion_id
        for group in analysis.standard_analyses
        for item in group.criteria
    }


def test_core_standard_label_resolution_is_presentation_only() -> None:
    standard_id = "standard-1"
    criterion = _criterion(
        "criterion-standard",
        "Uses Evidence",
        standard_id=standard_id,
    )
    score = _score(
        "score-standard",
        target=_target("core_student", "student-1"),
        criterion_id=criterion.criterion_id,
        value=3,
        standard_id=standard_id,
    )
    context = _context_with(
        criteria=(criterion,),
        scales=(_scale(),),
        scores=(score,),
    )
    library = StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=standard_id,
                code="SYN.1",
                source="synthetic",
                short_name="Synthetic Standard",
                description="Synthetic standard used only by tests.",
            ),
        )
    )

    fallback = activity_score_analysis_from_context(context)
    resolved = activity_score_analysis_from_context(
        context,
        standards_library=library,
    )

    assert fallback.standard_analyses[0].standard_label == standard_id
    assert fallback.standard_analyses[0].standard_code is None
    assert fallback.standard_analyses[0].standard_short_name is None
    assert resolved.standard_analyses[0].standard_label == "SYN.1"
    assert resolved.standard_analyses[0].standard_code == "SYN.1"
    assert resolved.standard_analyses[0].standard_short_name == "Synthetic Standard"
    assert resolved.criterion_analyses == fallback.criterion_analyses
    assert resolved.current_scores == fallback.current_scores
    assert resolved.current_score_count == fallback.current_score_count


def test_missing_core_standard_definition_falls_back_to_durable_id() -> None:
    standard_id = "standard-unavailable"
    criterion = _criterion(
        "criterion-standard",
        "Uses Evidence",
        standard_id=standard_id,
    )
    score = _score(
        "score-standard",
        target=_target("core_student", "student-1"),
        criterion_id=criterion.criterion_id,
        value=3,
        standard_id=standard_id,
    )
    unrelated_library = StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="other-standard",
                code="OTHER.1",
                source="synthetic",
                short_name="Other Standard",
                description="Unrelated synthetic standard.",
            ),
        )
    )

    analysis = activity_score_analysis_from_context(
        _context_with(
            criteria=(criterion,),
            scales=(_scale(),),
            scores=(score,),
        ),
        standards_library=unrelated_library,
    )

    standard = analysis.standard_analyses[0]
    assert standard.standard_id == standard_id
    assert standard.standard_label == standard_id
    assert standard.standard_code is None
    assert standard.standard_short_name is None


def test_standards_analysis_contract_has_no_proficiency_or_mastery_rollup() -> None:
    standard_fields = {item.name for item in fields(StandardScoreAnalysis)}
    criterion_fields = {item.name for item in fields(StandardCriterionAnalysis)}
    forbidden = {
        "average",
        "grade",
        "mastery",
        "proficiency",
        "level",
        "rate",
    }
    assert not standard_fields.intersection(forbidden)
    assert not criterion_fields.intersection(forbidden)
