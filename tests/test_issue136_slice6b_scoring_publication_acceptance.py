"""#136 Slice 6B: saved-group reuse, individual/group Scores and neutral publication.

This is synthetic-only acceptance. No real teacher or student records are accessed.
The test reads the six-table fixture from Slice 6A rather than creating a second
unrelated classroom model that might hide cross-boundary regressions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef
from test_issue136_slice6a_classroom_acceptance import (
    ACTOR,
    CLASS,
    NEW_PLAN,
    SAVED,
    SOURCE,
    STUDENTS,
    TARGET,
    YEAR,
    _saved_source,
    _setup,
    _work,
)

from concord.academic_result_manifest_generation import (
    GenerateAcademicResultManifestRequest,
    load_academic_result_manifest_head,
)
from concord.academic_result_publication import publish_concord_academic_results
from concord.academic_result_reader import (
    list_academic_result_scores_for_target,
    read_academic_result_manifest,
)
from concord.academic_work_registration import register_concord_academic_work
from concord.class_group_arrangement_storage import load_current_arrangement
from concord.models import (
    EffectiveContext,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
)
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    AddScoreRequest,
    ApplyGroupPlanRequest,
    ApproveGroupPlanRequest,
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    PrepareGroupPlanApplicationRequest,
    PreviewGroupPlanRequest,
    SelectActivityCriterionSetsRequest,
    add_score,
    apply_group_plan,
    approve_group_plan,
    create_criterion_set,
    create_scoring_scale,
    prepare_group_plan_application,
    preview_group_plan,
    select_activity_criterion_sets,
    show_activity,
)
from concord.workflows.class_group_arrangements import (
    ReuseGroupingRequest,
    prepare_reuse_grouping,
    reuse_grouping,
)
from concord.workflows.errors import ConcordWorkflowConflictError


def _clock() -> datetime:
    return datetime(2026, 10, 18, 16, 0, tzinfo=timezone.utc)


def _approved_applied(
    root: Path, standards: object, target_revision: int
) -> tuple[str, int]:
    request = ReuseGroupingRequest(
        class_id=CLASS,
        activity_id=TARGET,
        arrangement_id=SAVED,
        new_group_plan_id=NEW_PLAN,
        expected_snapshot_revision=target_revision,
        actor=ACTOR,
    )
    before = list_work_snapshots(root, _work(TARGET))
    review = prepare_reuse_grouping(request, workspace_root=root)
    assert review.assigned_count == 29
    assert len(review.groups) == 6
    assert list_work_snapshots(root, _work(TARGET)) == before
    draft = reuse_grouping(
        request,
        review_digest=review.review_digest,
        workspace_root=root,
        standards_library=standards,
    )
    context = EffectiveContext(activity_id=TARGET, session_ids=(f"{TARGET}-session",))
    preview = preview_group_plan(
        PreviewGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            expected_snapshot_revision=draft.commit.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    approved = approve_group_plan(
        ApproveGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            expected_snapshot_revision=preview.summary.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    application = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            application_id="application-six-tables-publication",
            fallback_effective_context=context,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    assert application.group_count == 6
    assert application.membership_count == 29
    applied = apply_group_plan(
        ApplyGroupPlanRequest(
            class_id=CLASS,
            activity_id=TARGET,
            group_plan_id=NEW_PLAN,
            application_id=application.application_id,
            application_digest=application.application_digest,
            expected_snapshot_revision=approved.commit.snapshot_revision,
            fallback_effective_context=context,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    assert applied.group_count == 6
    assert applied.membership_count == 29
    assert len(set(applied.group_ids)) == 6
    assert len(set(applied.membership_ids)) == 29
    return applied.group_ids[0], applied.commit.snapshot_revision


@pytest.mark.parametrize("orientation", ("mixed", "standards_based"))
def test_saved_grouping_scores_and_publication_keep_targets_distinct(
    tmp_path: Path, orientation: str
) -> None:
    root, standards, source_revision, target_revision = _setup(tmp_path, orientation)
    _saved_source(root, standards, source_revision)
    source_before = show_activity(CLASS, SOURCE, workspace_root=root).summary
    saved_before = load_current_arrangement(
        root,
        class_id=CLASS,
        school_year=YEAR,
        arrangement_id=SAVED,
        actor_id=ACTOR.actor_id,
    )
    group_id, revision = _approved_applied(root, standards, target_revision)
    before_scoring = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    ).graph
    assert before_scoring.score_records == ()
    assert before_scoring.score_evidence_links == ()

    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id=CLASS,
            activity_id=TARGET,
            scoring_scale_id="scale-6b",
            lineage_id="scale-lineage-6b",
            name="Four performance levels",
            revision=1,
            scale_type="ordinal",
            levels=(
                ScoringScaleLevel(
                    value=1, label="Developing", meaning="Synthetic level 1", position=1
                ),
                ScoringScaleLevel(
                    value=2,
                    label="Approaching",
                    meaning="Synthetic level 2",
                    position=2,
                ),
                ScoringScaleLevel(
                    value=3, label="Meeting", meaning="Synthetic level 3", position=3
                ),
                ScoringScaleLevel(
                    value=4, label="Exceeding", meaning="Synthetic level 4", position=4
                ),
            ),
            status="active",
            expected_snapshot_revision=revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    criteria = (
        CriterionSpec(
            criterion_id="criterion-6b-standard",
            key="reasoning",
            label="Reasoning",
            definition="Synthetic individual evidence for reasoning.",
            criterion_kind="standard_backed",
            standard_id="standard-synthetic-discussion",
            supported_target_kinds=("core_student",),
            default_scoring_scale_id="scale-6b",
        ),
    )
    if orientation == "mixed":
        criteria += (
            CriterionSpec(
                criterion_id="criterion-6b-local",
                key="collaboration",
                label="Collaboration",
                definition="Synthetic group collaboration observation.",
                criterion_kind="local",
                supported_target_kinds=("concord_group",),
                default_scoring_scale_id="scale-6b",
            ),
        )
    created = create_criterion_set(
        CreateCriterionSetRequest(
            class_id=CLASS,
            activity_id=TARGET,
            criterion_set_id="set-6b",
            lineage_id="set-lineage-6b",
            name="Classroom assessment criteria",
            purpose="Verify group and individual score separation after reuse.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed" if orientation == "mixed" else "standard_backed",
            criteria=criteria,
            status="active",
            standards_profile_id="profile-synthetic-discussion",
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id=CLASS,
            activity_id=TARGET,
            criterion_set_ids=("set-6b",),
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    individual = add_score(
        AddScoreRequest(
            class_id=CLASS,
            activity_id=TARGET,
            score_record_id="score-6b-individual",
            target_reference=ScoreTargetReference(
                target_kind="core_student", target_id=STUDENTS[0], owning_system="core"
            ),
            criterion_id="criterion-6b-standard",
            scoring_scale_id="scale-6b",
            disposition="scored",
            value=3,
            basis="professional_judgment",
            rationale="Private individual synthetic observation.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=ACTOR,
            session_id=f"{TARGET}-session",
        ),
        workspace_root=root,
        standards_library=standards,
    )
    revision = individual.commit.snapshot_revision
    if orientation == "mixed":
        group_score = add_score(
            AddScoreRequest(
                class_id=CLASS,
                activity_id=TARGET,
                score_record_id="score-6b-group",
                target_reference=ScoreTargetReference(
                    target_kind="concord_group",
                    target_id=group_id,
                    owning_system="concord",
                ),
                criterion_id="criterion-6b-local",
                scoring_scale_id="scale-6b",
                disposition="scored",
                value=4,
                basis="professional_judgment",
                rationale="Private group observation, not an individual grade.",
                privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
                expected_snapshot_revision=revision,
                actor=ACTOR,
                session_id=f"{TARGET}-session",
            ),
            workspace_root=root,
            standards_library=standards,
        )
        revision = group_score.commit.snapshot_revision

    graph = load_current_record_graph(
        root, _work(TARGET), standards_library=standards
    ).graph
    assert len(graph.score_records) == (2 if orientation == "mixed" else 1)
    assert len(graph.groups) == 6
    assert len(graph.memberships) == 29
    assert graph.score_evidence_links == ()
    # Current native Score records have identities, not an insertion-order contract.
    native_scores = {score.score_record_id: score for score in graph.score_records}
    assert set(native_scores) == (
        {"score-6b-individual", "score-6b-group"}
        if orientation == "mixed"
        else {"score-6b-individual"}
    )
    student_score = native_scores["score-6b-individual"]
    assert student_score.target_reference.target_kind == "core_student"
    assert student_score.target_reference.target_id == STUDENTS[0]
    assert student_score.standard_id == "standard-synthetic-discussion"
    if orientation == "mixed":
        group_score_record = native_scores["score-6b-group"]
        assert group_score_record.target_reference.target_kind == "concord_group"
        assert group_score_record.target_reference.target_id == group_id
        assert group_score_record.standard_id is None

    registered = register_concord_academic_work(
        root, CLASS, TARGET, academic_intent="summative", lifecycle="active"
    )
    assert registered.registration.registration_revision == 1
    request = GenerateAcademicResultManifestRequest(
        class_id=CLASS,
        activity_id=TARGET,
        expected_snapshot_revision=revision,
        actor=ACTOR,
        revision_reason="initial",
    )
    published = publish_concord_academic_results(
        request,
        workspace_root=root,
        standards_library=standards,
        clock=_clock,
    )
    assert published.disposition == "created"
    assert published.compatibility.compatible
    assert published.publication.record_set_revision == 1
    generation = published.manifest_generation
    raw = generation.path.read_bytes()
    assert raw == generation.content
    parsed = read_academic_result_manifest(raw)
    assert parsed == generation.manifest
    assert len(parsed.scores) == (2 if orientation == "mixed" else 1)
    # Select projected Scores by stable identity, never their collection order.
    projected = {score.score_record_id: score for score in parsed.scores}
    assert set(projected) == (
        {"score-6b-individual", "score-6b-group"}
        if orientation == "mixed"
        else {"score-6b-individual"}
    )
    student_projection = projected["score-6b-individual"]
    assert student_projection.target_reference.target_kind == "core_student"
    assert student_projection.target_reference.target_id == STUDENTS[0]
    assert student_projection.standard_id == "standard-synthetic-discussion"
    assert {
        score.score_record_id
        for score in list_academic_result_scores_for_target(
            parsed, student_projection.target_reference
        )
    } == {"score-6b-individual"}
    assert not any(
        score.target_reference.target_id == STUDENTS[1] for score in parsed.scores
    )
    if orientation == "mixed":
        group_projection = projected["score-6b-group"]
        assert group_projection.target_reference.target_kind == "concord_group"
        assert group_projection.target_reference.target_id == group_id
        assert group_projection.standard_id is None
        assert {
            score.score_record_id
            for score in list_academic_result_scores_for_target(
                parsed, group_projection.target_reference
            )
        } == {"score-6b-group"}

    assert b"Private individual synthetic observation" not in raw
    assert b"Private group observation" not in raw
    assert NEW_PLAN.encode() not in raw
    assert b"group_plan" not in raw
    work = ModuleWorkRef(module_id="concord", class_id=CLASS, work_id=TARGET)
    head = load_academic_result_manifest_head(root, work)
    assert head is not None
    assert head.sha256 == generation.sha256
    replay = publish_concord_academic_results(
        request,
        workspace_root=root,
        standards_library=standards,
        clock=_clock,
    )
    assert replay.disposition == "existing"
    assert replay.publication == published.publication
    assert replay.manifest_generation.content == generation.content
    assert show_activity(CLASS, SOURCE, workspace_root=root).summary == source_before
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year=YEAR,
            arrangement_id=SAVED,
            actor_id=ACTOR.actor_id,
        )
        == saved_before
    )
    assert (
        load_current_record_graph(
            root, _work(SOURCE), standards_library=standards
        ).graph.score_records
        == ()
    )
    with pytest.raises(ConcordWorkflowConflictError):
        reuse_grouping(
            ReuseGroupingRequest(
                class_id=CLASS,
                activity_id=TARGET,
                arrangement_id=SAVED,
                new_group_plan_id="no-second-plan",
                expected_snapshot_revision=revision,
                actor=ACTOR,
            ),
            review_digest="0" * 64,
            workspace_root=root,
            standards_library=standards,
        )
    assert list_work_snapshots(root, _work(TARGET))[-1] == revision
