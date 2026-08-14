from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.workspace import ensure_workspace_root

from concord.models import ConcordModelError, ScoringScale, ScoringScaleLevel
from concord.workflows import (
    ConcordWorkflowConflictError,
    CreateActivityContextRequest,
    CreateScoringScaleRequest,
    ReviseScoringScaleRequest,
    WorkflowActor,
    create_activity_context,
    create_scoring_scale,
    list_current_scoring_scale_heads,
    list_scoring_scales,
    revise_scoring_scale,
    show_scoring_scale,
)
from concord.workflows.context import provenance


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 17, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Scale Activity",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    return root, created.commit.snapshot_revision


def _ordinal_levels() -> tuple[ScoringScaleLevel, ...]:
    return (
        ScoringScaleLevel(
            value="developing",
            label="Developing",
            meaning="Developing evidence",
            position=1,
        ),
        ScoringScaleLevel(
            value="secure",
            label="Secure",
            meaning="Secure evidence",
            position=2,
        ),
    )


def test_scale_create_revise_and_current_head(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    first = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage",
            name="Two levels",
            revision=1,
            scale_type="ordinal",
            levels=_ordinal_levels(),
            status="active",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    second = revise_scoring_scale(
        ReviseScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            replacement_scoring_scale_id="scale-2",
            name="Two levels revised",
            revision=2,
            scale_type="ordinal",
            levels=_ordinal_levels(),
            status="active",
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    history = list_scoring_scales(
        "class-1",
        "activity-1",
        workspace_root=root,
    )
    heads = list_current_scoring_scale_heads(
        "class-1",
        "activity-1",
        workspace_root=root,
    )
    detail = show_scoring_scale(
        "class-1",
        "activity-1",
        "scale-2",
        workspace_root=root,
    )
    assert [item.scoring_scale_id for item in history] == ["scale-1", "scale-2"]
    assert [item.scoring_scale_id for item in heads] == ["scale-2"]
    assert detail.summary.revision == 2
    assert [item.value for item in detail.levels] == ["developing", "secure"]
    assert second.commit.snapshot_revision == first.commit.snapshot_revision + 1

    with pytest.raises(ConcordWorkflowConflictError):
        revise_scoring_scale(
            ReviseScoringScaleRequest(
                class_id="class-1",
                activity_id="activity-1",
                scoring_scale_id="scale-1",
                replacement_scoring_scale_id="scale-branch",
                name="Invalid branch",
                revision=3,
                scale_type="ordinal",
                levels=_ordinal_levels(),
                status="active",
                expected_snapshot_revision=second.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_scale_type_coherence_is_native_and_type_sensitive() -> None:
    created = provenance(_actor(), clock=lambda: _clock(1))
    with pytest.raises(ConcordModelError, match="numeric"):
        ScoringScale(
            scoring_scale_id="numeric-bool",
            lineage_id="numeric-lineage",
            name="Numeric",
            revision=1,
            scale_type="numeric",
            levels=(
                ScoringScaleLevel(
                    value=True,
                    label="Yes",
                    meaning="Boolean is not numeric here",
                ),
            ),
            status="active",
            created_provenance=created,
        )
    with pytest.raises(ConcordModelError, match="ordinal"):
        ScoringScale(
            scoring_scale_id="ordinal-no-position",
            lineage_id="ordinal-lineage",
            name="Ordinal",
            revision=1,
            scale_type="ordinal",
            levels=(
                ScoringScaleLevel(
                    value=1,
                    label="One",
                    meaning="Missing explicit position",
                ),
            ),
            status="active",
            created_provenance=created,
        )
    with pytest.raises(ConcordModelError, match="binary"):
        ScoringScale(
            scoring_scale_id="binary-three",
            lineage_id="binary-lineage",
            name="Binary",
            revision=1,
            scale_type="binary",
            levels=(
                ScoringScaleLevel(value=0, label="No", meaning="No"),
                ScoringScaleLevel(value=1, label="Yes", meaning="Yes"),
                ScoringScaleLevel(value=2, label="Maybe", meaning="Maybe"),
            ),
            status="active",
            created_provenance=created,
        )
