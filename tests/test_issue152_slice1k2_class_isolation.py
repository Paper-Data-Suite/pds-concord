"""#152 Slice 1K2: native Score isolation across two synthetic classrooms."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from issue140_slice2_fixtures import (
    ACTIVITY_ID,
    ACTOR,
    PROFILE_ID,
    STANDARD_ID,
    SyntheticClass,
    WitnessWorkspace,
    build_workspace,
)
from pds_core.routing_models import ModuleWorkRef

from concord.models import (
    EffectiveContext,
    EvidenceReference,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
)
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    AddScoreRequest,
    ArtifactPagePlan,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateGroupWithMembersRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    GroupMemberSpec,
    PrepareArtifactPagesRequest,
    ScoreEvidenceLinkSpec,
    SelectActivityCriterionSetsRequest,
    add_score,
    create_activity_context,
    create_criterion_set,
    create_group_with_members,
    create_scoring_scale,
    prepare_artifact_pages,
    select_activity_criterion_sets,
    show_activity,
)
from concord.workflows.errors import ConcordWorkflowNotFoundError

PRIVACY = PrivacyPolicy(classification="teacher_restricted")


def _work(section: SyntheticClass) -> ModuleWorkRef:
    return ModuleWorkRef("concord", section.class_id, ACTIVITY_ID)


def _revision(root: Path, section: SyntheticClass) -> int:
    return show_activity(
        section.class_id, ACTIVITY_ID, workspace_root=root
    ).summary.snapshot_revision


def _setup(fixture: WitnessWorkspace, section: SyntheticClass) -> None:
    root, library = fixture.root, fixture.standards
    cid = section.class_id
    if section == fixture.target:
        create_activity_context(
            CreateActivityContextRequest(
                class_id=cid,
                activity_id=ACTIVITY_ID,
                title="Independent synthetic discussion",
                activity_type="socratic_seminar",
                scoring_orientation="mixed",
                standards_profile_id=PROFILE_ID,
                focus_standard_ids=(STANDARD_ID,),
                session_id="issue140-synthetic-session",
                actor=ACTOR,
            ),
            workspace_root=root,
            standards_library=library,
        )
    effective = EffectiveContext(
        activity_id=ACTIVITY_ID, session_ids=("issue140-synthetic-session",)
    )
    for index, members in enumerate(section.cluster_members, start=1):
        create_group_with_members(
            CreateGroupWithMembersRequest(
                class_id=cid,
                activity_id=ACTIVITY_ID,
                group_id=f"{cid}-cluster-{index}",
                label=f"Cluster {index}",
                status="active",
                effective_context=effective,
                members=tuple(
                    GroupMemberSpec(
                        membership_id=f"member-{student}",
                        student_id=student,
                        effective_context=effective,
                    )
                    for student in members
                ),
                expected_snapshot_revision=_revision(root, section),
                actor=ACTOR,
            ),
            workspace_root=root,
            standards_library=library,
        )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id=cid,
            activity_id=ACTIVITY_ID,
            scoring_scale_id=f"{cid}-scale",
            lineage_id=f"{cid}-scale-lineage",
            name="Four levels",
            revision=1,
            scale_type="ordinal",
            levels=tuple(
                ScoringScaleLevel(
                    value=i, label=f"Level {i}", meaning=f"Level {i}", position=i
                )
                for i in range(1, 5)
            ),
            status="active",
            expected_snapshot_revision=_revision(root, section),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
    )
    criteria = create_criterion_set(
        CreateCriterionSetRequest(
            class_id=cid,
            activity_id=ACTIVITY_ID,
            criterion_set_id=f"{cid}-set",
            lineage_id=f"{cid}-set-lineage",
            name="Discussion criteria",
            purpose="Independent individual and Cluster judgments.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=(
                CriterionSpec(
                    criterion_id=f"{cid}-individual",
                    key="discussion",
                    label="Discussion",
                    definition="Individual discussion participation.",
                    criterion_kind="standard_backed",
                    standard_id=STANDARD_ID,
                    supported_target_kinds=("core_student",),
                    default_scoring_scale_id=f"{cid}-scale",
                ),
                CriterionSpec(
                    criterion_id=f"{cid}-group",
                    key="analysis",
                    label="Analysis",
                    definition="Collective textual analysis.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_group",),
                    default_scoring_scale_id=f"{cid}-scale",
                ),
            ),
            status="active",
            standards_profile_id=PROFILE_ID,
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id=cid,
            activity_id=ACTIVITY_ID,
            criterion_set_ids=(f"{cid}-set",),
            expected_snapshot_revision=criteria.commit.snapshot_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=library,
    )
    prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=cid,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=f"{cid}-evidence",
            template_version_id="synthetic-observation-template",
            artifact_category="observation",
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=ACTOR,
            privacy_policy=PRIVACY,
            expected_return_status="return_not_expected",
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id=f"{cid}-page",
                    return_expected=False,
                    route_required=False,
                ),
            ),
        ),
        workspace_root=root,
        standards_library=library,
    )


def _request(
    fixture: WitnessWorkspace, section: SyntheticClass, *, group: bool
) -> AddScoreRequest:
    cid = section.class_id
    kind = "group" if group else "individual"
    return AddScoreRequest(
        class_id=cid,
        activity_id=ACTIVITY_ID,
        score_record_id=f"{cid}-score-{kind}",
        target_reference=ScoreTargetReference(
            target_kind="concord_group" if group else "core_student",
            target_id=f"{cid}-cluster-1" if group else section.students[0],
            owning_system="concord" if group else "core",
        ),
        criterion_id=f"{cid}-{kind}",
        scoring_scale_id=f"{cid}-scale",
        disposition="scored",
        value=4 if group else 3,
        basis="linked_evidence",
        evidence_links=(
            ScoreEvidenceLinkSpec(
                score_evidence_link_id=f"{cid}-link-{kind}",
                evidence_reference=EvidenceReference(
                    evidence_kind="artifact_instance",
                    owning_system="concord",
                    record_id=f"{cid}-evidence",
                    moderation_requirement="not_required",
                ),
                relevance_description="Synthetic teacher observation.",
            ),
        ),
        privacy_policy=PRIVACY,
        expected_snapshot_revision=_revision(fixture.root, section),
        actor=ACTOR,
    )


def test_two_class_native_scores_and_evidence_are_isolated(tmp_path: Path) -> None:
    fixture = build_workspace(tmp_path)
    root, library = fixture.root, fixture.standards
    a, b = fixture.source, fixture.target
    assert (len(a.students), len(b.students)) == (29, 30)
    assert not set(a.students) & set(b.students)
    for section in (a, b):
        _setup(fixture, section)

    def snapshots(section: SyntheticClass):
        return list_work_snapshots(root, _work(section))

    def graph(section: SyntheticClass):
        return load_current_record_graph(
            root, _work(section), standards_library=library
        ).graph

    for section, other in ((a, b), (b, a)):
        before = snapshots(other)
        other_graph = graph(other)
        for group in (False, True):
            add_score(
                _request(fixture, section, group=group),
                workspace_root=root,
                standards_library=library,
            )
        assert snapshots(other) == before
        assert graph(other) == other_graph
        actual = graph(section)
        assert len(actual.groups) == 6
        assert len(actual.memberships) == len(section.students)
        assert len(actual.score_records) == len(actual.score_evidence_links) == 2
        assert {score.target_reference.target_id for score in actual.score_records} == {
            section.students[0],
            f"{section.class_id}-cluster-1",
        }
        for score in actual.score_records:
            individual = score.target_reference.target_kind == "core_student"
            assert score.standard_id == (STANDARD_ID if individual else None)
            assert score.value == (3 if individual else 4)
            assert score.scoring_scale_id == f"{section.class_id}-scale"
        assert {
            link.evidence_reference.record_id for link in actual.score_evidence_links
        } == {f"{section.class_id}-evidence"}
        assert {link.score_record_id for link in actual.score_evidence_links} == {
            score.score_record_id for score in actual.score_records
        }

    before = (snapshots(a), snapshots(b), graph(a), graph(b))
    for section, foreign in ((a, b), (b, a)):
        valid = _request(fixture, section, group=False)
        group = _request(fixture, section, group=True)
        attempts = (
            replace(
                valid,
                target_reference=_request(fixture, foreign, group=False).target_reference,
            ),
            replace(
                group,
                target_reference=_request(fixture, foreign, group=True).target_reference,
            ),
            replace(valid, criterion_id=f"{foreign.class_id}-individual"),
            replace(valid, scoring_scale_id=f"{foreign.class_id}-scale"),
        )
        for index, attempt in enumerate(attempts):
            attempt = replace(
                attempt,
                score_record_id=f"{section.class_id}-rejected-{index}",
                evidence_links=(),
                basis="professional_judgment",
                rationale="Synthetic invalid cross-class judgment.",
            )
            with pytest.raises(ConcordWorkflowNotFoundError):
                add_score(attempt, workspace_root=root, standards_library=library)
            assert (snapshots(a), snapshots(b), graph(a), graph(b)) == before
