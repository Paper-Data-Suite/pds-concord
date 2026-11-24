"""Concord #152 Slice 1E: real individual versus Cluster Group Score isolation.

A synthetic returned/assembled/reviewed Artifact, authentic Core student roster,
and canonical Concord Group membership are used. No classroom records or scans.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.routing_models import ModuleWorkRef
from test_issue142_slice6b_real_score_continuation import (
    ACTIVITY,
    ACTOR,
    ARTIFACT,
    CLASS,
    _first_score,
    _revision,
    _setup_reviewed,
)

import concord.menu_artifact_scoring as scoring_menu
from concord.models import EffectiveContext, ScoreTargetReference, SubjectReference
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.workflows import (
    AddArtifactSubjectRequest,
    CreateCriterionSetRequest,
    CreateGroupWithMembersRequest,
    CriterionSpec,
    GroupMemberSpec,
    SelectActivityCriterionSetsRequest,
    add_artifact_subject,
    create_criterion_set,
    create_group_with_members,
    select_activity_criterion_sets,
    show_activity,
)
from concord.workflows.artifact_routine_scoring import inspect_artifact_routine_scoring
from concord.workflows.artifact_routine_scoring_preparation import (
    RoutineScorePreparationRequest,
    prepare_routine_score_preview,
)
from concord.workflows.artifact_routine_scoring_selection import (
    routine_criteria_for_target,
    routine_target_options,
)
from concord.workflows.errors import ConcordWorkflowValidationError

WORK = ModuleWorkRef("concord", CLASS, ACTIVITY)
GROUP_ID = "cluster-synthetic"
GROUP_CRITERION = "criterion-cluster-collaboration"


def _prepare_individual_and_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    standard_id: str = "standard-1",
) -> tuple[Path, object]:
    """Use existing physical-shaped synthetic fixture; add genuine Group data."""
    root, standards = _setup_reviewed(tmp_path, monkeypatch, standard_id=standard_id)
    effective = EffectiveContext(
        activity_id=ACTIVITY,
        session_ids=("session-1",),
    )
    create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            group_id=GROUP_ID,
            label="Synthetic Textual Analysis Cluster",
            status="active",
            effective_context=effective,
            members=(
                GroupMemberSpec(
                    membership_id="membership-student-1",
                    student_id="student-1",
                    effective_context=effective,
                ),
                GroupMemberSpec(
                    membership_id="membership-student-2",
                    student_id="student-2",
                    effective_context=effective,
                ),
            ),
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    create_criterion_set(
        CreateCriterionSetRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            criterion_set_id="set-cluster",
            lineage_id="lineage-cluster",
            name="Cluster Textual Analysis",
            purpose="Assess the Cluster as a collective, never its students.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="local",
            criteria=(
                CriterionSpec(
                    criterion_id=GROUP_CRITERION,
                    key="cluster-analysis",
                    label="Collaborative Textual Analysis",
                    definition="Cluster identifies and supports an interpretation.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_group",),
                    default_scoring_scale_id="scale-1",
                ),
            ),
            status="active",
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            criterion_set_ids=("set-1", "set-cluster"),
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            artifact_instance_id=ARTIFACT,
            artifact_subject_id="cluster-subject-1",
            subject_reference=SubjectReference(
                subject_kind="concord_group",
                subject_id=GROUP_ID,
                owning_system="concord",
            ),
            subject_role="represented_group",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=_revision(root),
            actor=ACTOR,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    return root, standards


def _group_target() -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="concord_group",
        target_id=GROUP_ID,
        owning_system="concord",
    )


def _group_menu_choices(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[str, ...]]:
    confirmed: list[tuple[str, ...]] = []
    monkeypatch.setattr(scoring_menu, "_choose_target", lambda *_a: _group_target())

    def criterion(context: object, _target: object) -> object:
        return next(
            item for item in context.eligible_criteria
            if item.criterion_id == GROUP_CRITERION
        )

    monkeypatch.setattr(scoring_menu, "_choose_criterion", criterion)
    monkeypatch.setattr(
        scoring_menu,
        "_choose_level",
        lambda scale: scale.levels[3],
    )

    def confirm(
        _title: str, _token: str, lines: tuple[str, ...]
    ) -> bool:
        confirmed.append(lines)
        return True

    monkeypatch.setattr(scoring_menu, "confirm_write", confirm)
    return confirmed


@pytest.mark.parametrize("standard_id", ("standard-1", "SL.PE.11-12.1"))
def test_real_student_and_cluster_scores_are_separate_native_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, standard_id: str
) -> None:
    root, standards = _prepare_individual_and_group(
        tmp_path, monkeypatch, standard_id=standard_id
    )
    context = inspect_artifact_routine_scoring(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert context.eligibility.routine_scoring_eligible
    options = routine_target_options(context)
    choices = {candidate.target_reference for candidate in options.candidates}
    individual = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )
    assert individual in choices
    assert _group_target() in choices
    assert {item.criterion_id for item in routine_criteria_for_target(
        context, _group_target()
    )} == {GROUP_CRITERION}
    assert GROUP_CRITERION not in {
        item.criterion_id for item in routine_criteria_for_target(
            context, individual
        )
    }
    with pytest.raises(ConcordWorkflowValidationError):
        prepare_routine_score_preview(
            context,
            RoutineScorePreparationRequest(
                target_reference=_group_target(),
                criterion_id="criterion-standard",
                scoring_scale_id="scale-1",
                value=3,
            ),
        )

    first = _first_score(root, monkeypatch)
    assert first.preview.target_reference == individual
    assert first.preview.score_kind == "standard_backed"
    assert first.preview.standard_id == standard_id
    prior_revision = _revision(root)

    confirms = _group_menu_choices(monkeypatch)
    second = scoring_menu._record_selected_artifact_score(
        show_activity(CLASS, ACTIVITY, workspace_root=root).summary,
        ARTIFACT,
        scoring_menu.MenuSessionContext(actor=ACTOR),
    )
    assert second is not None
    assert second.preview.target_reference == _group_target()
    assert second.preview.score_kind == "local"
    assert second.preview.standard_id is None
    assert second.preview.criterion_id == GROUP_CRITERION
    assert second.preview.value == 4
    assert _revision(root) == prior_revision + 1
    assert len(confirms) == 1
    assert "GROUP SCORE WARNING:" in confirms[0]
    assert "It creates no individual student Scores." in confirms[0]
    assert any("Review provenance" in line for line in confirms[0])

    graph = load_current_record_graph(
        root, WORK, standards_library=standards
    ).graph
    assert len(graph.score_records) == 2
    assert len(graph.score_evidence_links) == 2
    assert len(graph.memberships) == 2
    scores = {
        (item.target_reference.target_kind, item.target_reference.target_id): item
        for item in graph.score_records
    }
    assert set(scores) == {
        ("core_student", "student-1"),
        ("concord_group", GROUP_ID),
    }
    assert ("core_student", "student-2") not in scores
    assert scores[("core_student", "student-1")].criterion_id == (
        "criterion-standard"
    )
    student_score = scores[("core_student", "student-1")]
    group_score = scores[("concord_group", GROUP_ID)]
    assert student_score.standard_id == standard_id
    assert student_score.value == 3
    assert group_score.criterion_id == GROUP_CRITERION
    assert group_score.standard_id is None
    assert group_score.value == 4
    (student_link,) = (
        link for link in graph.score_evidence_links
        if link.score_record_id == student_score.score_record_id
    )
    assert student_link.evidence_reference.record_id == ARTIFACT
    assert {
        item.evidence_reference.record_id for item in graph.score_evidence_links
    } == {ARTIFACT}
    assert {item.score_record_id for item in graph.score_evidence_links} == {
        item.score_record_id for item in graph.score_records
    }


def test_unconfirmed_cluster_score_preserves_student_and_group_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, standards = _prepare_individual_and_group(tmp_path, monkeypatch)
    _first_score(root, monkeypatch)
    before = list_work_snapshots(root, WORK)
    monkeypatch.setattr(scoring_menu, "_choose_target", lambda *_a: _group_target())
    monkeypatch.setattr(
        scoring_menu, "_choose_criterion",
        lambda context, *_a: next(
            item for item in context.eligible_criteria
            if item.criterion_id == GROUP_CRITERION
        ),
    )
    monkeypatch.setattr(scoring_menu, "confirm_write", lambda *_a: False)

    def forbid(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Unconfirmed Cluster Score must not be committed.")

    monkeypatch.setattr(scoring_menu, "record_prepared_routine_score", forbid)
    result = scoring_menu._record_selected_artifact_score(
        show_activity(CLASS, ACTIVITY, workspace_root=root).summary,
        ARTIFACT,
        scoring_menu.MenuSessionContext(actor=ACTOR),
    )
    assert result is None
    assert list_work_snapshots(root, WORK) == before
    graph = load_current_record_graph(
        root, WORK, standards_library=standards
    ).graph
    assert len(graph.score_records) == 1
    assert len(graph.score_evidence_links) == 1
    assert graph.score_records[0].target_reference.target_kind == "core_student"
