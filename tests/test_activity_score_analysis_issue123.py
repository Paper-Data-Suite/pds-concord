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
    ArtifactInstance,
    ConcordRecordReference,
    CorrectionRecord,
    Criterion,
    Group,
    PrivacyPolicy,
    Provenance,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
    ScoringScaleLevel,
    Session,
)
from concord.workflows import (
    SCORE_ANALYSIS_BASIS,
    SCORE_HISTORY_BASIS,
    SCORE_HISTORY_SCOPE,
    TARGET_DETAIL_SCOPE,
    ActivityScoreAnalysis,
    ScoreHistoryAnalysis,
    StandardCriterionAnalysis,
    StandardScoreAnalysis,
    TargetScoreDetail,
    activity_score_analysis_from_context,
    score_history_analysis_from_context,
    target_score_detail_from_context,
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
    groups: tuple[Group, ...] = (),
    sessions: tuple[Session, ...] = (),
    artifacts: tuple[ArtifactInstance, ...] = (),
    corrections: tuple[CorrectionRecord, ...] = (),
) -> ActivityReadContext:
    activity = _activity()
    return ActivityReadContext(
        root=Path("/synthetic/read-only"),
        work=ModuleWorkRef("concord", "class-1", "activity-1"),
        snapshot_revision=11,
        snapshot_sha256="b" * 64,
        graph=ConcordRecordGraph(
            activities=(activity,),
            sessions=sessions,
            groups=groups,
            artifact_instances=artifacts,
            criteria=criteria,
            scoring_scales=scales,
            score_records=scores,
            correction_records=corrections,
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

def test_target_detail_is_current_head_only_and_preserves_exact_scale_context() -> None:
    first = _criterion("criterion-a", "Uses Evidence")
    second = _criterion("criterion-b", "Explains Reasoning")
    scale = _scale()
    target = _target("core_student", "student-1")
    predecessor = _score(
        "score-old", target=target, criterion_id=first.criterion_id, value=2
    )
    current = _score(
        "score-current",
        target=target,
        criterion_id=first.criterion_id,
        value=3,
        supersedes=predecessor.score_record_id,
    )
    deferred = _score(
        "score-deferred",
        target=target,
        criterion_id=second.criterion_id,
        disposition="deferred",
        value=None,
    )
    other = _score(
        "score-other",
        target=_target("core_student", "student-2"),
        criterion_id=first.criterion_id,
        value=4,
    )
    context = _context_with(
        criteria=(first, second),
        scales=(scale,),
        scores=(predecessor, current, deferred, other),
    )

    detail = target_score_detail_from_context(
        context,
        target,
        target_label_resolver=lambda item: "Jane Doe" if item == target else None,
    )

    assert isinstance(detail, TargetScoreDetail)
    assert detail.sharing_scope == TARGET_DETAIL_SCOPE == "teacher_local"
    assert detail.target_reference == target
    assert detail.target_label == "Jane Doe"
    assert detail.current_score_count == 2
    assert tuple(item.score_record_id for item in detail.results) == (
        "score-deferred",
        "score-current",
    )
    by_id = {item.score_record_id: item for item in detail.results}
    assert by_id["score-current"].criterion_label == "Uses Evidence"
    assert by_id["score-current"].scoring_scale_id == "scale-1"
    assert by_id["score-current"].scoring_scale_revision == 1
    assert by_id["score-current"].value == 3
    assert by_id["score-current"].value_label == "Secure"
    assert by_id["score-deferred"].disposition == "deferred"
    assert by_id["score-deferred"].value is None
    assert by_id["score-deferred"].value_label is None
    assert "score-old" not in by_id
    assert "score-other" not in by_id


def test_target_detail_does_not_infer_scores_for_unrecorded_target() -> None:
    target = _target("core_student", "student-without-score")
    detail = target_score_detail_from_context(_context(), target)

    assert detail.target_reference == target
    assert detail.target_label == "student-without-score"
    assert detail.current_score_count == 0
    assert detail.results == ()


def test_target_detail_uses_concord_native_labels_without_identity_rewrite() -> None:
    criterion = _criterion("criterion-1", "Reasoning")
    scale = _scale()
    group = Group(
        group_id="group-1",
        activity_id="activity-1",
        label="Blue Team",
        status="active",
        created_provenance=_provenance(),
    )
    session = Session(
        session_id="session-1",
        activity_id="activity-1",
        sequence=2,
        label="Round Two",
        status="active",
        created_provenance=_provenance(),
    )
    artifact = ArtifactInstance(
        artifact_instance_id="artifact-1",
        template_version_id="template-version-1",
        activity_id="activity-1",
        artifact_category="student_work",
        generation_status="completed",
        expected_return_status="returned_optional",
        artifact_status="completed",
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        page_ids=("page-1",),
        created_provenance=_provenance(),
    )
    targets = (
        _target("concord_group", group.group_id),
        _target("concord_session", session.session_id),
        _target("concord_activity", "activity-1"),
        _target("concord_artifact_instance", artifact.artifact_instance_id),
    )
    scores = tuple(
        _score(
            f"score-{index}",
            target=target,
            criterion_id=criterion.criterion_id,
            value=3,
        )
        for index, target in enumerate(targets, start=1)
    )
    context = _context_with(
        criteria=(criterion,),
        scales=(scale,),
        scores=scores,
        groups=(group,),
        sessions=(session,),
        artifacts=(artifact,),
    )

    details = tuple(
        target_score_detail_from_context(context, target) for target in targets
    )

    assert tuple(item.target_label for item in details) == (
        "Blue Team",
        "Round Two",
        "Synthetic Analysis Activity",
        "artifact-1",
    )
    assert tuple(item.target_reference for item in details) == targets


def test_target_detail_resolver_is_display_only() -> None:
    target = _target("core_student", "student-1")
    fallback = target_score_detail_from_context(_context(), target)
    resolved = target_score_detail_from_context(
        _context(),
        target,
        target_label_resolver=lambda _: "Readable Student",
    )

    assert fallback.target_label == "student-1"
    assert resolved.target_label == "Readable Student"
    assert resolved.target_reference == fallback.target_reference
    assert resolved.results == fallback.results
    assert resolved.current_score_count == fallback.current_score_count


def test_target_detail_contract_has_no_grade_or_proficiency_fields() -> None:
    result_type = type(
        target_score_detail_from_context(
            _context(),
            _target("core_student", "student-1"),
        ).results[0]
    )
    names = {
        item.name
        for model in (TargetScoreDetail, result_type)
        for item in fields(model)
    }
    forbidden = {
        "average",
        "grade",
        "mastery",
        "proficiency",
        "missing",
        "required",
    }
    assert not names.intersection(forbidden)

def _score_correction(
    correction_id: str,
    *,
    predecessor_id: str,
    successor_id: str,
    reason: str,
    corrected_at: str,
) -> CorrectionRecord:
    return CorrectionRecord(
        correction_id=correction_id,
        target_reference=ConcordRecordReference(
            record_kind="score_record",
            record_id=predecessor_id,
        ),
        correction_type="score_revision",
        reason=reason,
        correcting_actor=_actor(),
        corrected_at=corrected_at,
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        replacement_reference=ConcordRecordReference(
            record_kind="score_record",
            record_id=successor_id,
        ),
    )


def test_score_history_preserves_revision_chain_and_correction_audits() -> None:
    criterion = _criterion("criterion-history", "Historical Reasoning")
    scale_v1 = _scale(
        "scale-history-v1",
        lineage_id="scale-history",
        revision=1,
        name="History Scale v1",
    )
    scale_v2 = _scale(
        "scale-history-v2",
        lineage_id="scale-history",
        revision=2,
        name="History Scale v2",
        supersedes="scale-history-v1",
    )
    target = _target("core_student", "student-1")
    first = _score(
        "score-history-1",
        target=target,
        criterion_id=criterion.criterion_id,
        scoring_scale_id=scale_v1.scoring_scale_id,
        value=2,
    )
    second = _score(
        "score-history-2",
        target=target,
        criterion_id=criterion.criterion_id,
        scoring_scale_id=scale_v1.scoring_scale_id,
        value=3,
        supersedes=first.score_record_id,
    )
    third = _score(
        "score-history-3",
        target=target,
        criterion_id=criterion.criterion_id,
        scoring_scale_id=scale_v2.scoring_scale_id,
        value=4,
        supersedes=second.score_record_id,
    )
    corrections = (
        _score_correction(
            "correction-1",
            predecessor_id=first.score_record_id,
            successor_id=second.score_record_id,
            reason="Corrected initial judgment.",
            corrected_at="2026-10-03T14:00:00+00:00",
        ),
        _score_correction(
            "correction-2",
            predecessor_id=second.score_record_id,
            successor_id=third.score_record_id,
            reason="Applied revised rubric judgment.",
            corrected_at="2026-10-03T14:30:00+00:00",
        ),
    )
    context = _context_with(
        criteria=(criterion,),
        scales=(scale_v1, scale_v2),
        scores=(first, second, third),
        corrections=corrections,
    )

    history = score_history_analysis_from_context(
        context,
        target_label_resolver=lambda _: "Jane Doe",
    )

    assert isinstance(history, ScoreHistoryAnalysis)
    assert history.score_basis == SCORE_HISTORY_BASIS
    assert history.sharing_scope == SCORE_HISTORY_SCOPE == "teacher_local"
    assert history.lineage_count == 1
    assert history.revision_count == 3
    lineage = history.lineages[0]
    assert lineage.root_score_record_id == "score-history-1"
    assert lineage.current_score_record_id == "score-history-3"
    assert lineage.revision_count == 3
    assert tuple(item.revision_number for item in lineage.revisions) == (1, 2, 3)
    assert tuple(item.is_current for item in lineage.revisions) == (
        False,
        False,
        True,
    )
    assert tuple(item.target_label for item in lineage.revisions) == (
        "Jane Doe",
        "Jane Doe",
        "Jane Doe",
    )
    assert tuple(item.value_label for item in lineage.revisions) == (
        "Developing",
        "Secure",
        "Extending",
    )
    assert tuple(item.scoring_scale_revision for item in lineage.revisions) == (
        1,
        1,
        2,
    )
    assert lineage.revisions[0].correction_id is None
    assert lineage.revisions[1].correction_id == "correction-1"
    assert (
        lineage.revisions[1].correction_reason
        == "Corrected initial judgment."
    )
    assert lineage.revisions[2].correction_id == "correction-2"
    assert lineage.revisions[0].superseded_by_score_record_id == "score-history-2"
    assert lineage.revisions[2].superseded_by_score_record_id is None


def test_score_history_is_explicit_and_does_not_change_current_analysis() -> None:
    criterion = _criterion("criterion-history", "Historical Reasoning")
    target = _target("core_student", "student-1")
    first = _score(
        "score-history-1",
        target=target,
        criterion_id=criterion.criterion_id,
        value=2,
    )
    second = _score(
        "score-history-2",
        target=target,
        criterion_id=criterion.criterion_id,
        value=3,
        supersedes=first.score_record_id,
    )
    correction = _score_correction(
        "correction-1",
        predecessor_id=first.score_record_id,
        successor_id=second.score_record_id,
        reason="Revised judgment.",
        corrected_at="2026-10-03T14:00:00+00:00",
    )
    context = _context_with(
        criteria=(criterion,),
        scales=(_scale(),),
        scores=(first, second),
        corrections=(correction,),
    )

    current = activity_score_analysis_from_context(context)
    history = score_history_analysis_from_context(context)

    assert current.current_score_count == 1
    assert tuple(item.score_record_id for item in current.current_scores) == (
        "score-history-2",
    )
    assert history.revision_count == 2
    assert tuple(
        item.score_record_id
        for lineage in history.lineages
        for item in lineage.revisions
    ) == ("score-history-1", "score-history-2")


def test_score_history_preserves_non_score_disposition_without_coercion() -> None:
    criterion = _criterion("criterion-history", "Historical Reasoning")
    target = _target("concord_group", "group-1")
    record = _score(
        "score-deferred-history",
        target=target,
        criterion_id=criterion.criterion_id,
        disposition="deferred",
        value=None,
    )
    context = _context_with(
        criteria=(criterion,),
        scales=(_scale(),),
        scores=(record,),
    )

    history = score_history_analysis_from_context(context)

    revision = history.lineages[0].revisions[0]
    assert revision.disposition == "deferred"
    assert revision.value is None
    assert revision.value_label is None
    assert revision.is_current is True


def test_score_history_separates_independent_lineages_deterministically() -> None:
    criterion = _criterion("criterion-history", "Historical Reasoning")
    first_target = _target("core_student", "student-1")
    second_target = _target("core_student", "student-2")
    records = (
        _score(
            "score-z-root",
            target=second_target,
            criterion_id=criterion.criterion_id,
            value=4,
        ),
        _score(
            "score-a-root",
            target=first_target,
            criterion_id=criterion.criterion_id,
            value=3,
        ),
    )
    context = _context_with(
        criteria=(criterion,),
        scales=(_scale(),),
        scores=records,
    )

    history = score_history_analysis_from_context(context)

    assert tuple(item.root_score_record_id for item in history.lineages) == (
        "score-a-root",
        "score-z-root",
    )
    assert all(item.revision_count == 1 for item in history.lineages)


def test_score_history_contract_has_no_grade_or_proficiency_fields() -> None:
    criterion = _criterion("criterion-history", "Historical Reasoning")
    record = _score(
        "score-history",
        target=_target("core_student", "student-1"),
        criterion_id=criterion.criterion_id,
        value=3,
    )
    history = score_history_analysis_from_context(
        _context_with(
            criteria=(criterion,),
            scales=(_scale(),),
            scores=(record,),
        )
    )
    revision_type = type(history.lineages[0].revisions[0])
    names = {
        item.name
        for model in (ScoreHistoryAnalysis, revision_type)
        for item in fields(model)
    }
    forbidden = {
        "average",
        "grade",
        "mastery",
        "proficiency",
        "missing",
        "required",
    }
    assert not names.intersection(forbidden)
