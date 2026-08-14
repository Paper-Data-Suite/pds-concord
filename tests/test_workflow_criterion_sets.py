from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

from concord.models import ScoringScaleLevel
from concord.storage import load_current_record_graph
from concord.workflows import (
    ConcordWorkflowConflictError,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    ReviseCriterionSetRequest,
    SelectActivityCriterionSetsRequest,
    WorkflowActor,
    create_activity_context,
    create_criterion_set,
    create_scoring_scale,
    list_criterion_sets,
    list_current_criterion_set_heads,
    revise_criterion_set,
    select_activity_criterion_sets,
    show_criterion_set,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 16, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _standards_library() -> StandardsLibrary:
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


def _workspace(tmp_path: Path) -> tuple[Path, int, StandardsLibrary]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    standards_library = _standards_library()
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Scoring Activity",
            activity_type="project",
            scoring_orientation="mixed",
            standards_profile_id="profile-1",
            focus_standard_ids=("standard-1",),
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards_library,
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
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=lambda: _clock(3),
    )
    return root, scale.commit.snapshot_revision, standards_library


def _criteria(prefix: str) -> tuple[CriterionSpec, ...]:
    return (
        CriterionSpec(
            criterion_id=f"{prefix}-standard",
            key="reasoning",
            label="Reasoning",
            definition="Uses evidence to support reasoning.",
            criterion_kind="standard_backed",
            standard_id="standard-1",
            supported_target_kinds=("core_student",),
            default_scoring_scale_id="scale-1",
        ),
        CriterionSpec(
            criterion_id=f"{prefix}-local",
            key="collaboration",
            label="Collaboration",
            definition="Coordinates the assigned work.",
            criterion_kind="local",
            supported_target_kinds=("concord_group",),
            default_scoring_scale_id="scale-1",
        ),
    )


def test_create_set_is_atomic_and_selection_is_explicit(tmp_path: Path) -> None:
    root, revision, standards_library = _workspace(tmp_path)
    created = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage",
            name="Synthetic criteria",
            purpose="Exercise mixed scoring.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=_criteria("criterion-v1"),
            status="active",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=lambda: _clock(4),
    )
    loaded = load_current_record_graph(
        root,
        created.commit.work,
        standards_library=standards_library,
    )
    assert created.commit.snapshot_revision == revision + 1
    assert len(loaded.graph.criterion_sets) == 1
    assert len(loaded.graph.criteria) == 2
    assert loaded.graph.activities[0].criterion_set_ids == ()

    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_ids=("set-1",),
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=lambda: _clock(5),
    )
    loaded = load_current_record_graph(
        root,
        selected.commit.work,
        standards_library=standards_library,
    )
    assert loaded.graph.activities[0].criterion_set_ids == ("set-1",)
    detail = show_criterion_set(
        "class-1",
        "activity-1",
        "set-1",
        workspace_root=root,
        standards_library=standards_library,
    )
    assert [item.key for item in detail.criteria] == [
        "reasoning",
        "collaboration",
    ]
    assert detail.summary.is_selected


def test_revision_preserves_lineage_and_current_head(tmp_path: Path) -> None:
    root, revision, standards_library = _workspace(tmp_path)
    first = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage",
            name="Synthetic criteria",
            purpose="Revision one.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=_criteria("criterion-v1"),
            status="active",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards_library,
    )
    second = revise_criterion_set(
        ReviseCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            replacement_criterion_set_id="set-2",
            name="Synthetic criteria",
            purpose="Revision two.",
            revision=2,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=_criteria("criterion-v2"),
            status="active",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards_library,
    )
    history = list_criterion_sets(
        "class-1",
        "activity-1",
        workspace_root=root,
        standards_library=standards_library,
    )
    heads = list_current_criterion_set_heads(
        "class-1",
        "activity-1",
        workspace_root=root,
        standards_library=standards_library,
    )
    assert [item.criterion_set_id for item in history] == ["set-1", "set-2"]
    assert [item.criterion_set_id for item in heads] == ["set-2"]
    assert heads[0].lineage_id == "set-lineage"
    assert second.commit.snapshot_revision == first.commit.snapshot_revision + 1

    with pytest.raises(ConcordWorkflowConflictError):
        revise_criterion_set(
            ReviseCriterionSetRequest(
                class_id="class-1",
                activity_id="activity-1",
                criterion_set_id="set-1",
                replacement_criterion_set_id="set-branch",
                name="Branch",
                purpose="Invalid branch.",
                revision=3,
                scope="activity_specific",
                criterion_set_kind="mixed",
                criteria=_criteria("criterion-branch"),
                status="active",
                expected_snapshot_revision=second.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            standards_library=standards_library,
        )
