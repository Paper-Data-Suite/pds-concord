from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
)
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    EvidenceReference,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
    StatusReason,
    SubjectReference,
)
from concord.storage import load_current_record_graph
from concord.workflows import (
    AddArtifactReviewRequest,
    AddModerationRecordRequest,
    AddScoreRequest,
    ArtifactPagePlan,
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateGroupRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    PrepareArtifactPagesRequest,
    ReplaceScoreRequest,
    ScoreEvidenceLinkSpec,
    SelectActivityCriterionSetsRequest,
    WorkflowActor,
    add_artifact_review,
    add_moderation_record,
    add_score,
    create_activity_context,
    create_criterion_set,
    create_group,
    create_scoring_scale,
    list_current_score_heads,
    prepare_artifact_pages,
    replace_score,
    select_activity_criterion_sets,
    show_score,
)
from concord.workflows.context import actor_reference


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 18, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _standards() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="standard-1",
                code="SYN.1",
                source="synthetic",
                short_name="Synthetic standard",
                description="Privacy-safe standard used only by tests.",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-1",
                standards=("standard-1",),
                title="Synthetic standards profile",
            ),
        ),
    )


def _student_target() -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )


def _student_subject() -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id="student-1",
        owning_system="core",
    )


def _artifact_evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
        moderation_requirement="not_required",
    )


def _workspace(
    tmp_path: Path,
) -> tuple[Path, int, StandardsLibrary]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
                {
                    "student_id": "student-2",
                    "last_name": "Two",
                    "first_name": "Blair",
                    "period": "1",
                },
            ),
        ),
    )
    standards = _standards()
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Score Activity",
            activity_type="project",
            scoring_orientation="mixed",
            standards_profile_id="profile-1",
            focus_standard_ids=("standard-1",),
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(2),
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage",
            name="Four levels",
            revision=1,
            scale_type="ordinal",
            levels=(
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
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(3),
    )
    criterion_set = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage",
            name="Synthetic criteria",
            purpose="Exercise Score workflows.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=(
                CriterionSpec(
                    criterion_id="criterion-standard",
                    key="reasoning",
                    label="Reasoning",
                    definition="Uses evidence to support reasoning.",
                    criterion_kind="standard_backed",
                    standard_id="standard-1",
                    supported_target_kinds=("core_student",),
                    default_scoring_scale_id="scale-1",
                ),
                CriterionSpec(
                    criterion_id="criterion-local",
                    key="process",
                    label="Process",
                    definition="Uses an effective collaborative process.",
                    criterion_kind="local",
                    supported_target_kinds=("core_student",),
                    default_scoring_scale_id="scale-1",
                ),
            ),
            status="active",
            standards_profile_id="profile-1",
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(4),
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_ids=("set-1",),
            expected_snapshot_revision=criterion_set.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(5),
    )
    return root, selected.commit.snapshot_revision, standards


def test_professional_judgment_score_is_atomic_and_has_no_links(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    result = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="professional_judgment",
            rationale="Teacher observed sustained reasoning across the Activity.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    loaded = load_current_record_graph(
        root,
        result.commit.work,
        standards_library=standards,
    )
    assert len(loaded.graph.score_records) == 1
    assert loaded.graph.score_evidence_links == ()
    score = loaded.graph.score_records[0]
    assert score.score_kind == "standard_backed"
    assert score.standard_id == "standard-1"
    assert score.value == 3
    assert score.moderation_complete
    assert result.score_evidence_link_ids == ()


def test_non_score_requires_matching_status_reason(tmp_path: Path) -> None:
    root, revision, standards = _workspace(tmp_path)
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="requires StatusReason",
    ):
        add_score(
            AddScoreRequest(
                class_id="class-1",
                activity_id="activity-1",
                score_record_id="score-no-reason",
                target_reference=_student_target(),
                criterion_id="criterion-local",
                scoring_scale_id="scale-1",
                disposition="not_observed",
                basis="professional_judgment",
                rationale="No direct observation was available.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
            standards_library=standards,
        )

    wrong = StatusReason(
        reason_code="absent",
        recorded_by=actor_reference(_actor()),
        recorded_at=_clock(6).isoformat(),
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="must match",
    ):
        add_score(
            AddScoreRequest(
                class_id="class-1",
                activity_id="activity-1",
                score_record_id="score-wrong-reason",
                target_reference=_student_target(),
                criterion_id="criterion-local",
                scoring_scale_id="scale-1",
                disposition="not_observed",
                basis="professional_judgment",
                rationale="No direct observation was available.",
                status_reason=wrong,
                privacy_policy=_privacy(),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
            standards_library=standards,
        )


def test_score_revision_preserves_predecessor_and_creates_audit(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    first = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Initial teacher judgment.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    second = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-score-1",
            reason="Additional observation changed the teacher judgment.",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="professional_judgment",
            rationale="Revised teacher judgment after additional observation.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    loaded = load_current_record_graph(
        root,
        second.commit.work,
        standards_library=standards,
    )
    assert [item.score_record_id for item in loaded.graph.score_records] == [
        "score-1",
        "score-2",
    ]
    assert loaded.graph.score_records[1].supersedes_score_record_id == "score-1"
    assert len(loaded.graph.correction_records) == 1
    correction = loaded.graph.correction_records[0]
    assert correction.correction_type == "score_revision"
    assert correction.target_reference.record_id == "score-1"
    assert correction.replacement_reference is not None
    assert correction.replacement_reference.record_id == "score-2"

    heads = list_current_score_heads(
        "class-1",
        "activity-1",
        workspace_root=root,
        standards_library=standards,
    )
    assert [item.score_record_id for item in heads] == ["score-2"]

    detail = show_score(
        "class-1",
        "activity-1",
        "score-2",
        workspace_root=root,
        standards_library=standards,
    )
    assert detail.summary.value == 3
    assert "additional observation" in (detail.rationale or "")

    with pytest.raises(ConcordWorkflowConflictError):
        replace_score(
            ReplaceScoreRequest(
                class_id="class-1",
                activity_id="activity-1",
                score_record_id="score-1",
                replacement_score_record_id="score-branch",
                correction_id="correction-branch",
                reason="Invalid branch attempt.",
                target_reference=_student_target(),
                criterion_id="criterion-standard",
                scoring_scale_id="scale-1",
                disposition="scored",
                value=4,
                basis="professional_judgment",
                rationale="Invalid branch.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=second.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            standards_library=standards,
        )


def test_review_required_moderation_blocks_then_allows_linked_score(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=revision,
            actor=_actor(),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-1",
                    return_expected=False,
                    route_required=False,
                ),
            ),
            expected_return_status="return_not_expected",
            privacy_policy=_privacy(),
            session_id="session-1",
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    reviewed = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_review_id="review-1",
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="confirmed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="required",
            scoring_readiness="not_ready",
            review_outcome="moderation_required",
            privacy_policy=_privacy(),
            expected_snapshot_revision=prepared.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    link = ScoreEvidenceLinkSpec(
        score_evidence_link_id="link-1",
        evidence_reference=_artifact_evidence(),
        relevance_description="Observation directly supports the reasoning judgment.",
        subject_context=(_student_subject(),),
        significance="primary",
    )
    with pytest.raises(
        ConcordWorkflowValidationError,
        match="requires an explicit applicable current Moderation",
    ):
        add_score(
            AddScoreRequest(
                class_id="class-1",
                activity_id="activity-1",
                score_record_id="score-blocked",
                target_reference=_student_target(),
                criterion_id="criterion-standard",
                scoring_scale_id="scale-1",
                disposition="scored",
                value=3,
                basis="linked_evidence",
                evidence_links=(link,),
                privacy_policy=_privacy(),
                expected_snapshot_revision=reviewed.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            standards_library=standards,
        )

    moderated = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-1",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_student_subject(),),
            status="accepted",
            permitted_use="support_named_subject",
            rationale="The observation may support the named student's Score.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=reviewed.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(8),
    )
    accepted_link = ScoreEvidenceLinkSpec(
        score_evidence_link_id="link-1",
        evidence_reference=_artifact_evidence(),
        relevance_description="Observation directly supports the reasoning judgment.",
        subject_context=(_student_subject(),),
        significance="primary",
        moderation_record_id="moderation-1",
    )
    scored = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="linked_evidence",
            evidence_links=(accepted_link,),
            privacy_policy=_privacy(),
            expected_snapshot_revision=moderated.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(9),
    )
    loaded = load_current_record_graph(
        root,
        scored.commit.work,
        standards_library=standards,
    )
    assert len(loaded.graph.score_records) == 1
    assert len(loaded.graph.score_evidence_links) == 1
    assert loaded.graph.score_records[0].moderation_complete
    assert loaded.graph.score_evidence_links[0].moderation_record_id == "moderation-1"


def test_deferred_score_may_preserve_evidence_while_moderation_is_pending(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-deferred",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=revision,
            actor=_actor(),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-deferred",
                    return_expected=False,
                    route_required=False,
                ),
            ),
            expected_return_status="return_not_expected",
            privacy_policy=_privacy(),
            session_id="session-1",
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    reviewed = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-deferred",
            artifact_review_id="review-deferred",
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="confirmed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="required",
            scoring_readiness="not_ready",
            review_outcome="moderation_required",
            privacy_policy=_privacy(),
            expected_snapshot_revision=prepared.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    reason = StatusReason(
        reason_code="deferred",
        recorded_by=actor_reference(_actor()),
        recorded_at=_clock(8).isoformat(),
        note="Awaiting Moderation before a scored judgment.",
    )
    deferred = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-deferred",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="deferred",
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-deferred",
                    evidence_reference=EvidenceReference(
                        evidence_kind="artifact_instance",
                        owning_system="concord",
                        record_id="artifact-deferred",
                        moderation_requirement="not_required",
                    ),
                    relevance_description=(
                        "Evidence is retained while consequential use awaits "
                        "Moderation."
                    ),
                    subject_context=(_student_subject(),),
                    significance="primary",
                ),
            ),
            status_reason=reason,
            privacy_policy=_privacy(),
            expected_snapshot_revision=reviewed.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(8),
    )
    detail = show_score(
        "class-1",
        "activity-1",
        "score-deferred",
        workspace_root=root,
        standards_library=standards,
    )
    assert detail.summary.disposition == "deferred"
    assert detail.summary.value is None
    assert not detail.summary.moderation_complete
    assert len(detail.evidence_links) == 1
    assert deferred.score_evidence_link_ids == ("link-deferred",)

    moderated = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-deferred",
            target_evidence_reference=EvidenceReference(
                evidence_kind="artifact_instance",
                owning_system="concord",
                record_id="artifact-deferred",
                moderation_requirement="not_required",
            ),
            target_subject_references=(_student_subject(),),
            status="accepted",
            permitted_use="support_named_subject",
            rationale="Moderation now permits consequential use.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=deferred.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(9),
    )
    successor = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-deferred",
            replacement_score_record_id="score-deferred-scored",
            correction_id="correction-deferred-scored",
            reason="Required Moderation is now complete.",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-deferred-scored",
                    evidence_reference=EvidenceReference(
                        evidence_kind="artifact_instance",
                        owning_system="concord",
                        record_id="artifact-deferred",
                        moderation_requirement="not_required",
                    ),
                    relevance_description=(
                        "Moderated evidence now supports the scored judgment."
                    ),
                    subject_context=(_student_subject(),),
                    significance="primary",
                    moderation_record_id="moderation-deferred",
                ),
            ),
            privacy_policy=_privacy(),
            expected_snapshot_revision=moderated.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(10),
    )
    successor_detail = show_score(
        "class-1",
        "activity-1",
        successor.score_record_id,
        workspace_root=root,
        standards_library=standards,
    )
    predecessor_detail = show_score(
        "class-1",
        "activity-1",
        "score-deferred",
        workspace_root=root,
        standards_library=standards,
    )
    assert predecessor_detail.summary.disposition == "deferred"
    assert predecessor_detail.summary.value is None
    assert successor_detail.summary.disposition == "scored"
    assert successor_detail.summary.value == 3
    assert successor_detail.summary.moderation_complete
    assert successor_detail.evidence_links[0].moderation_record_id == (
        "moderation-deferred"
    )


def test_individual_score_can_use_explicit_multi_subject_external_evidence(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    group = create_group(
        CreateGroupRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-1",
            label="Synthetic Group",
            status="active",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    subjects = (
        _student_subject(),
        SubjectReference(
            subject_kind="concord_group",
            subject_id="group-1",
            owning_system="concord",
        ),
    )
    reference = EvidenceReference(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="result-multi-subject",
        immutable_source_version="result-multi-subject-v1",
        subject_context=subjects,
        moderation_requirement="not_required",
    )
    scored = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-multi-subject",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-multi-subject",
                    evidence_reference=reference,
                    relevance_description=(
                        "The teacher explicitly judged the named student's "
                        "reasoning within this multi-subject evidence."
                    ),
                    subject_context=subjects,
                    significance="primary",
                ),
            ),
            privacy_policy=_privacy(),
            expected_snapshot_revision=group.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    detail = show_score(
        "class-1",
        "activity-1",
        scored.score_record_id,
        workspace_root=root,
        standards_library=standards,
    )
    assert detail.summary.target_reference == _student_target()
    assert detail.evidence_links[0].subject_context == subjects
    assert "named student's" in detail.evidence_links[0].relevance_description


def test_one_immutable_source_can_support_independent_current_scores(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    reference = EvidenceReference(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="result-shared",
        immutable_source_version="result-shared-v7",
        moderation_requirement="not_required",
    )
    first = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-shared-a",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-shared-a",
                    evidence_reference=reference,
                    relevance_description=(
                        "Shared immutable result supports judgment A."
                    ),
                ),
            ),
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    second = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-shared-b",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-shared-b",
                    evidence_reference=reference,
                    relevance_description=(
                        "Shared immutable result supports judgment B."
                    ),
                ),
            ),
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    heads = list_current_score_heads(
        "class-1",
        "activity-1",
        workspace_root=root,
        standards_library=standards,
        target_reference=_student_target(),
        criterion_id="criterion-standard",
    )
    assert [item.score_record_id for item in heads] == [
        "score-shared-a",
        "score-shared-b",
    ]
    assert all(item.is_current for item in heads)
    assert second.commit.snapshot_revision > first.commit.snapshot_revision
    first_detail = show_score(
        "class-1",
        "activity-1",
        "score-shared-a",
        workspace_root=root,
        standards_library=standards,
    )
    second_detail = show_score(
        "class-1",
        "activity-1",
        "score-shared-b",
        workspace_root=root,
        standards_library=standards,
    )
    assert (
        first_detail.evidence_links[0].evidence_reference
        == second_detail.evidence_links[0].evidence_reference
        == reference
    )


def test_non_score_cross_cases_preserve_exceptional_state_and_session(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    actor = _actor()
    insufficient_reason = StatusReason(
        reason_code="insufficient_evidence",
        recorded_by=actor_reference(actor),
        recorded_at=_clock(6).isoformat(),
        note="The available evidence does not support a judgment.",
    )
    insufficient = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-insufficient",
            target_reference=_student_target(),
            criterion_id="criterion-local",
            scoring_scale_id="scale-1",
            disposition="insufficient_evidence",
            basis="professional_judgment",
            rationale="Teacher determined that evidence was insufficient.",
            status_reason=insufficient_reason,
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=actor,
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    absent_reason = StatusReason(
        reason_code="absent",
        recorded_by=actor_reference(actor),
        recorded_at=_clock(7).isoformat(),
        note="The selected Session has no observation.",
    )
    add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-session-absent",
            target_reference=_student_target(),
            criterion_id="criterion-local",
            scoring_scale_id="scale-1",
            disposition="absent",
            basis="professional_judgment",
            rationale="No judgment was made for the selected Session.",
            status_reason=absent_reason,
            privacy_policy=_privacy(),
            session_id="session-1",
            expected_snapshot_revision=insufficient.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    insufficient_detail = show_score(
        "class-1",
        "activity-1",
        "score-insufficient",
        workspace_root=root,
        standards_library=standards,
    )
    absent_detail = show_score(
        "class-1",
        "activity-1",
        "score-session-absent",
        workspace_root=root,
        standards_library=standards,
    )
    assert insufficient_detail.summary.value is None
    assert insufficient_detail.status_reason == insufficient_reason
    assert absent_detail.summary.value is None
    assert absent_detail.summary.session_id == "session-1"
    assert absent_detail.status_reason == absent_reason


def test_teacher_defined_scale_preserves_all_type_sensitive_values(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-types",
            lineage_id="scale-types-lineage",
            name="Type-sensitive values",
            revision=1,
            scale_type="teacher_defined",
            levels=(
                ScoringScaleLevel(
                    value=1,
                    label="Integer",
                    meaning="Integer one.",
                ),
                ScoringScaleLevel(
                    value=1.0,
                    label="Float",
                    meaning="Floating-point one.",
                ),
                ScoringScaleLevel(
                    value="1",
                    label="String",
                    meaning="String one.",
                ),
                ScoringScaleLevel(
                    value=True,
                    label="Boolean",
                    meaning="Boolean true.",
                ),
            ),
            status="active",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    expected = (
        ("score-type-int", 1, int),
        ("score-type-float", 1.0, float),
        ("score-type-string", "1", str),
        ("score-type-bool", True, bool),
    )
    current_revision = scale.commit.snapshot_revision
    for offset, (score_id, value, expected_type) in enumerate(expected, start=7):
        result = add_score(
            AddScoreRequest(
                class_id="class-1",
                activity_id="activity-1",
                score_record_id=score_id,
                target_reference=_student_target(),
                criterion_id="criterion-local",
                scoring_scale_id="scale-types",
                disposition="scored",
                value=value,
                basis="professional_judgment",
                rationale="Teacher deliberately selected this exact typed value.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=current_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            standards_library=standards,
            clock=lambda offset=offset: _clock(offset),
        )
        current_revision = result.commit.snapshot_revision
        detail = show_score(
            "class-1",
            "activity-1",
            score_id,
            workspace_root=root,
            standards_library=standards,
        )
        assert type(detail.summary.value) is expected_type


def test_score_revision_uses_fresh_links_and_can_correct_target_and_criterion(
    tmp_path: Path,
) -> None:
    root, revision, standards = _workspace(tmp_path)
    first_reference = EvidenceReference(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="result-before",
        immutable_source_version="result-before-v1",
        moderation_requirement="not_required",
    )
    first = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-before",
            target_reference=_student_target(),
            criterion_id="criterion-standard",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-before",
                    evidence_reference=first_reference,
                    relevance_description="Initial immutable evidence.",
                ),
            ),
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(6),
    )
    corrected_target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-2",
        owning_system="core",
    )
    second_reference = EvidenceReference(
        evidence_kind="quillan_response",
        owning_system="quillan",
        record_id="response-after",
        immutable_source_version="response-after-v2",
        moderation_requirement="not_required",
    )
    second = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-before",
            replacement_score_record_id="score-after",
            correction_id="correction-semantic",
            reason="Target and Criterion were identified incorrectly.",
            target_reference=corrected_target,
            criterion_id="criterion-local",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=3,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id="link-after",
                    evidence_reference=second_reference,
                    relevance_description="Fresh evidence for corrected semantics.",
                ),
            ),
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
        clock=lambda: _clock(7),
    )
    loaded = load_current_record_graph(
        root,
        second.commit.work,
        standards_library=standards,
    )
    scores = {item.score_record_id: item for item in loaded.graph.score_records}
    links = {
        item.score_evidence_link_id: item
        for item in loaded.graph.score_evidence_links
    }
    assert scores["score-before"].target_reference == _student_target()
    assert scores["score-before"].criterion_id == "criterion-standard"
    assert scores["score-after"].target_reference == corrected_target
    assert scores["score-after"].criterion_id == "criterion-local"
    assert scores["score-after"].standard_id is None
    assert links["link-before"].score_record_id == "score-before"
    assert links["link-after"].score_record_id == "score-after"
    assert links["link-before"].evidence_reference == first_reference
    assert links["link-after"].evidence_reference == second_reference
    correction = next(
        item
        for item in loaded.graph.correction_records
        if item.correction_id == "correction-semantic"
    )
    assert correction.correction_type == "score_revision"
    assert correction.target_reference.record_id == "score-before"
    assert correction.replacement_reference is not None
    assert correction.replacement_reference.record_id == "score-after"
