"""#136 Slice 4: cross-Activity grouping review and strict materialization.

All identifiers and student names here are entirely synthetic.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.workspace import ensure_workspace_root

from concord.class_group_arrangement_storage import (
    ArrangementConflictError,
    append_arrangement_revision,
    list_current_arrangements,
    load_current_arrangement,
)
from concord.models import PlannedGroup
from concord.workflows import (
    CreateActivityContextRequest,
    CreateManualGroupPlanRequest,
    WorkflowActor,
    create_activity_context,
    create_manual_group_plan,
    list_groups,
    show_activity,
    show_group_plan,
)
from concord.workflows.class_group_arrangements import (
    ReuseGroupingRequest,
    SaveGroupingRequest,
    StudentPlacementDecision,
    prepare_reuse_grouping,
    prepare_save_grouping,
    reuse_grouping,
    save_grouping,
)
from concord.workflows.errors import ConcordWorkflowConflictError

YEAR = "2026-2027"
CLASS = "class-1"
ACTOR = WorkflowActor(actor_id="teacher-1")
ROSTER = tuple(f"student-{i:02}" for i in range(1, 30))


def _core_roster(ids: tuple[str, ...]) -> object:
    return create_roster(
        CLASS,
        tuple(
            {
                "student_id": sid,
                "first_name": "Synthetic",
                "last_name": f"Student-{index}",
                "period": "1",
            }
            for index, sid in enumerate(ids, 1)
        ),
    )


def _setup(tmp_path: Path) -> tuple[Path, int, int]:
    root = ensure_workspace_root(tmp_path / "pds")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS,
            YEAR,
            created_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(root, _core_roster(ROSTER))  # type: ignore[arg-type]
    revisions: list[int] = []
    for activity_id in ("source-activity", "target-activity"):
        created = create_activity_context(
            CreateActivityContextRequest(
                class_id=CLASS,
                activity_id=activity_id,
                title=f"Synthetic {activity_id}",
                activity_type="project",
                scoring_orientation="evidence_only",
                session_id=f"{activity_id}-session-1",
                actor=ACTOR,
            ),
            workspace_root=root,
        )
        revisions.append(created.commit.snapshot_revision)
    return root, revisions[0], revisions[1]


def _groups(*, missing: tuple[str, ...] = ()) -> tuple[PlannedGroup, ...]:
    return tuple(
        PlannedGroup(
            planned_group_key=f"table-{number}",
            label=f"Table {number}",
            description=f"Synthetic group {number}",
            student_ids=tuple(
                student
                for index, student in enumerate(ROSTER)
                if index % 6 == number - 1 and student not in missing
            ),
        )
        for number in range(1, 7)
    )


def _source(root: Path, revision: int, *, missing: tuple[str, ...] = ()) -> int:
    saved = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=CLASS,
            activity_id="source-activity",
            group_plan_id="original-plan",
            expected_snapshot_revision=revision,
            actor=ACTOR,
            proposed_groups=_groups(missing=missing),
        ),
        workspace_root=root,
    )
    return saved.commit.snapshot_revision


def _save_request(revision: int) -> SaveGroupingRequest:
    return SaveGroupingRequest(
        class_id=CLASS,
        activity_id="source-activity",
        group_plan_id="original-plan",
        arrangement_id="english-12-six-tables",
        name="English 12 - Six Table Groups",
        expected_snapshot_revision=revision,
        actor=ACTOR,
    )


def _save(root: Path, revision: int) -> None:
    request = _save_request(revision)
    review = prepare_save_grouping(request, workspace_root=root)
    assert review.assigned_count <= 29
    save_grouping(request, review_digest=review.review_digest, workspace_root=root)


def _reuse_request(target_revision: int, **changes: object) -> ReuseGroupingRequest:
    request = ReuseGroupingRequest(
        class_id=CLASS,
        activity_id="target-activity",
        arrangement_id="english-12-six-tables",
        new_group_plan_id="new-activity-group-plan",
        expected_snapshot_revision=target_revision,
        actor=ACTOR,
    )
    return replace(request, **changes)


def test_six_groups_save_and_materialize_in_new_activity(tmp_path: Path) -> None:
    root, source_revision, target_revision = _setup(tmp_path)
    source_revision = _source(root, source_revision)
    source_work = show_activity(CLASS, "source-activity", workspace_root=root).summary
    save_request = _save_request(source_revision)
    prepared_save = prepare_save_grouping(save_request, workspace_root=root)
    assert len(prepared_save.groups) == 6
    assert prepared_save.assigned_count == 29
    assert prepared_save.unresolved_student_ids == ()
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=ACTOR.actor_id
        )
        == ()
    )
    saved = save_grouping(
        save_request,
        review_digest=prepared_save.review_digest,
        workspace_root=root,
    )
    assert saved.revision.name == "English 12 - Six Table Groups"
    assert len(saved.revision.groups) == 6
    assert (
        show_activity(CLASS, "source-activity", workspace_root=root).summary
        == source_work
    )

    reuse_request = _reuse_request(target_revision)
    review = prepare_reuse_grouping(reuse_request, workspace_root=root)
    assert review.assigned_count == 29
    assert len(review.groups) == 6
    result = reuse_grouping(
        reuse_request, review_digest=review.review_digest, workspace_root=root
    )
    assert result.status == "draft"
    target_plan = show_group_plan(
        CLASS, "target-activity", "new-activity-group-plan", workspace_root=root
    )
    source_plan = show_group_plan(
        CLASS, "source-activity", "original-plan", workspace_root=root
    )
    assert target_plan.plan.group_plan_id != source_plan.plan.group_plan_id
    assert len(target_plan.plan.proposed_groups) == 6
    assert target_plan.plan.roster_student_ids == tuple(sorted(ROSTER))
    assert all(item.status == "draft" for item in (source_plan.plan, target_plan.plan))
    assert list_groups(CLASS, "target-activity", workspace_root=root) == ()
    assert list_groups(CLASS, "source-activity", workspace_root=root) == ()
    assert (
        load_current_arrangement(
            root,
            class_id=CLASS,
            school_year=YEAR,
            arrangement_id="english-12-six-tables",
            actor_id=ACTOR.actor_id,
        )
        == saved
    )


def test_save_preview_is_read_only_and_forged_review_rejected(tmp_path: Path) -> None:
    root, source_revision, _ = _setup(tmp_path)
    source_revision = _source(root, source_revision)
    request = _save_request(source_revision)
    prepare_save_grouping(request, workspace_root=root)
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=ACTOR.actor_id
        )
        == ()
    )
    with pytest.raises(ConcordWorkflowConflictError, match="preview changed"):
        save_grouping(request, review_digest="0" * 64, workspace_root=root)
    assert (
        list_current_arrangements(
            root, class_id=CLASS, school_year=YEAR, actor_id=ACTOR.actor_id
        )
        == ()
    )


def test_source_snapshot_must_still_be_current_at_save(tmp_path: Path) -> None:
    root, source_revision, _ = _setup(tmp_path)
    source_revision = _source(root, source_revision)
    old = _save_request(source_revision)
    original = prepare_save_grouping(old, workspace_root=root)
    with pytest.raises(ConcordWorkflowConflictError, match="reopen"):
        prepare_save_grouping(
            replace(old, expected_snapshot_revision=source_revision - 1),
            workspace_root=root,
        )
    with pytest.raises(ConcordWorkflowConflictError, match="reopen"):
        save_grouping(
            replace(old, expected_snapshot_revision=source_revision - 1),
            review_digest=original.review_digest,
            workspace_root=root,
        )


def test_roster_drift_requires_exact_placed_and_departed_decisions(
    tmp_path: Path,
) -> None:
    root, source_revision, target_revision = _setup(tmp_path)
    _save(root, _source(root, source_revision))
    changed = tuple(s for s in ROSTER if s != "student-29") + ("student-30",)
    write_class_roster(root, _core_roster(changed), overwrite=True)  # type: ignore[arg-type]
    request = _reuse_request(target_revision)
    with pytest.raises(
        ConcordWorkflowConflictError, match="acknowledge every departed"
    ):
        prepare_reuse_grouping(request, workspace_root=root)
    with pytest.raises(ConcordWorkflowConflictError, match="placement"):
        prepare_reuse_grouping(
            replace(request, acknowledged_departed_student_ids=("student-29",)),
            workspace_root=root,
        )
    reconciled = replace(
        request,
        acknowledged_departed_student_ids=("student-29",),
        placement_decisions=(
            StudentPlacementDecision(student_id="student-30", group_key="table-6"),
        ),
    )
    preview = prepare_reuse_grouping(reconciled, workspace_root=root)
    assert preview.departed_student_ids == ("student-29",)
    assert preview.added_student_ids == ("student-30",)
    assert preview.assigned_count == 29
    assert any("student-30" in group.student_ids for group in preview.groups)
    reused = reuse_grouping(
        reconciled, review_digest=preview.review_digest, workspace_root=root
    )
    assert reused.status == "draft"
    assert "student-29" not in {
        student for group in preview.groups for student in group.student_ids
    }


def test_saved_unresolved_requires_explicit_choice(tmp_path: Path) -> None:
    root, source_revision, target_revision = _setup(tmp_path)
    _save(root, _source(root, source_revision, missing=("student-01",)))
    req = _reuse_request(target_revision)
    with pytest.raises(ConcordWorkflowConflictError, match="placement"):
        prepare_reuse_grouping(req, workspace_root=root)
    keep_unresolved = replace(
        req,
        placement_decisions=(
            StudentPlacementDecision(student_id="student-01", group_key=None),
        ),
    )
    preview = prepare_reuse_grouping(keep_unresolved, workspace_root=root)
    assert preview.unresolved_student_ids == ("student-01",)
    result = reuse_grouping(
        keep_unresolved, review_digest=preview.review_digest, workspace_root=root
    )
    assert result.status == "draft"
    assert show_group_plan(
        CLASS, "target-activity", "new-activity-group-plan", workspace_root=root
    ).plan.unresolved_student_ids == ("student-01",)


def test_reuse_rejects_stale_target_and_identity_collision(tmp_path: Path) -> None:
    root, source_revision, target_revision = _setup(tmp_path)
    _save(root, _source(root, source_revision))
    request = _reuse_request(target_revision)
    reviewed = prepare_reuse_grouping(request, workspace_root=root)
    with pytest.raises(
        ConcordWorkflowConflictError,
        match="preview|Activity changed|target Activity changed|Grouping or target",
    ):
        reuse_grouping(request, review_digest="f" * 64, workspace_root=root)
    assert list_groups(CLASS, "target-activity", workspace_root=root) == ()
    reuse_grouping(request, review_digest=reviewed.review_digest, workspace_root=root)
    with pytest.raises(ConcordWorkflowConflictError, match="changed|used"):
        prepare_reuse_grouping(request, workspace_root=root)


def test_existing_plan_requires_explicit_acknowledgment(tmp_path: Path) -> None:
    root, source_revision, target_revision = _setup(tmp_path)
    _save(root, _source(root, source_revision))
    first = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id=CLASS,
            activity_id="target-activity",
            group_plan_id="an-existing-plan",
            expected_snapshot_revision=target_revision,
            actor=ACTOR,
        ),
        workspace_root=root,
    )
    req = _reuse_request(first.commit.snapshot_revision)
    with pytest.raises(ConcordWorkflowConflictError, match="existing GroupPlans"):
        prepare_reuse_grouping(req, workspace_root=root)
    reviewed = prepare_reuse_grouping(
        replace(req, acknowledge_existing_plans=True), workspace_root=root
    )
    assert len(reviewed.groups) == 6


def test_owner_restriction_and_retirement_are_enforced(tmp_path: Path) -> None:
    root, source_revision, target_revision = _setup(tmp_path)
    _save(root, _source(root, source_revision))
    other = replace(
        _reuse_request(target_revision), actor=WorkflowActor(actor_id="teacher-2")
    )
    with pytest.raises(ArrangementConflictError, match="owning teacher"):
        prepare_reuse_grouping(other, workspace_root=root)
    first = load_current_arrangement(
        root,
        class_id=CLASS,
        school_year=YEAR,
        arrangement_id="english-12-six-tables",
        actor_id=ACTOR.actor_id,
    )
    append_arrangement_revision(
        root,
        replace(
            first.revision,
            revision=2,
            status="retired",
            created_at="2026-10-18T00:00:00+00:00",
            predecessor_sha256=first.sha256,
        ),
        actor_id=ACTOR.actor_id,
        expected_revision=1,
        expected_sha256=first.sha256,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="retired"):
        prepare_reuse_grouping(_reuse_request(target_revision), workspace_root=root)


def test_materialization_forwards_exact_standards_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord.workflows import class_group_arrangements as grouping

    actor = ACTOR
    request = _reuse_request(7)
    preview = grouping.PreparedGroupingReuse(
        class_id=CLASS,
        school_year=YEAR,
        target_activity_id="target-activity",
        target_snapshot_revision=7,
        target_roster_student_ids=ROSTER,
        arrangement_id="english-12-six-tables",
        arrangement_revision=1,
        arrangement_sha256="a" * 64,
        new_group_plan_id="fresh-plan",
        groups=(_groups()[0],),
        unresolved_student_ids=(),
        departed_student_ids=(),
        added_student_ids=(),
        review_digest="d" * 64,
    )
    monkeypatch.setattr(grouping, "prepare_reuse_grouping", lambda *a, **k: preview)
    captured: list[object] = []

    def fake_create(obj: object, **kwargs: object) -> object:
        captured.extend((obj, kwargs))
        return SimpleNamespace(status="draft")

    monkeypatch.setattr(grouping, "create_group_plan", fake_create)
    context = cast(object, SimpleNamespace(standards=()))
    grouping.reuse_grouping(
        request,
        review_digest=preview.review_digest,
        standards_library=cast(object, context),
    )  # type: ignore[arg-type]
    created, keywords = captured
    assert getattr(created, "group_plan_id") == "fresh-plan"
    assert getattr(created, "expected_roster_student_ids") == ROSTER
    assert getattr(created, "actor") is actor
    assert isinstance(keywords, dict) and keywords["standards_library"] is context
