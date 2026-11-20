"""Concord #150 Slice 2: authoritative target-only six-Cluster planning.

Synthetic Core rosters and target Activities; no real students or workspace writes.
Normal GroupPlan placement/approval/application remains with existing services.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided
import concord.workflows.target_cluster_preflight as planning
from concord.menu_context import MenuSessionContext
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import ActivitySummary, WorkflowActor


def _activity(*, revision: int = 3, groups: int = 0) -> ActivitySummary:
    return ActivitySummary(
        class_id="target-b",
        activity_id="lesson-target",
        title="Target Seminar",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=groups,
        snapshot_revision=revision,
    )


def _reviewed(
    count: int = 29,
    *,
    revision: int = 3,
    plan_count: int = 0,
    group_count: int = 0,
) -> planning.TargetClusterPreflight:
    return planning.TargetClusterPreflight(
        class_id="target-b",
        activity_id="lesson-target",
        title="Target Seminar",
        snapshot_revision=revision,
        roster_student_ids=tuple(f"b-student-{i:02d}" for i in range(count)),
        current_group_count=group_count,
        existing_plan_count=plan_count,
        six_cluster_size_reference=planning.six_cluster_size_reference(count),
    )


@pytest.mark.parametrize(
    ("count", "sizes"),
    ((29, (5, 5, 5, 5, 5, 4)), (30, (5, 5, 5, 5, 5, 5))),
)
def test_six_cluster_reference_is_a_shape_not_memberships(
    count: int, sizes: tuple[int, ...]
) -> None:
    assert planning.six_cluster_size_reference(count) == sizes
    assert sum(sizes) == count
    groups = planning.six_empty_planned_clusters()
    assert len(groups) == 6
    assert tuple(group.label for group in groups) == tuple(
        f"Cluster {i}" for i in range(1, 7)
    )
    assert all(group.student_ids == () for group in groups)
    assert all(group.effective_context is None for group in groups)


def test_invalid_reference_counts_do_not_infer_students() -> None:
    with pytest.raises(ValueError):
        planning.six_cluster_size_reference(-1)
    with pytest.raises(TypeError):
        planning.six_cluster_size_reference(True)


@pytest.mark.parametrize("count", (29, 30))
def test_target_preflight_reads_only_target_core_roster(
    count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[str, str]] = []
    target = _activity(revision=12)
    monkeypatch.setattr(
        planning, "resolve_read_workspace_root", lambda *_a: Path("synthetic-root")
    )
    monkeypatch.setattr(
        planning,
        "require_core_class",
        lambda _root, class_id: calls.append(("class", class_id)),
    )
    monkeypatch.setattr(
        planning,
        "show_activity",
        lambda class_id, activity_id, **_k: (
            calls.append(("activity", class_id)),
            SimpleNamespace(summary=target),
        )[1],
    )
    monkeypatch.setattr(
        planning,
        "load_required_roster",
        lambda _root, class_id: (
            calls.append(("roster", class_id)),
            SimpleNamespace(
                students=tuple(
                    SimpleNamespace(student_id=f"target-person-{i:02d}")
                    for i in range(count)
                )
            ),
        )[1],
    )
    monkeypatch.setattr(
        planning,
        "list_group_plans",
        lambda class_id, activity_id, **_k: (
            calls.append(("plans", class_id)),
            (),
        )[1],
    )
    report = planning.inspect_target_cluster_preflight("target-b", "lesson-target")
    assert report.roster_count == count
    assert report.snapshot_revision == 12
    assert report.can_create_new_shape
    assert all(class_id == "target-b" for _kind, class_id in calls)
    assert {kind for kind, _class_id in calls} == {
        "class",
        "activity",
        "roster",
        "plans",
    }
    assert "source" not in str(report)


def test_target_preflight_rejects_duplicate_roster_and_cross_class_plans(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        planning, "resolve_read_workspace_root", lambda *_a: Path("synthetic-root")
    )
    monkeypatch.setattr(planning, "require_core_class", lambda *_a: None)
    monkeypatch.setattr(
        planning,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=_activity()),
    )
    monkeypatch.setattr(
        planning,
        "load_required_roster",
        lambda *_a: SimpleNamespace(
            students=(
                SimpleNamespace(student_id="dup"),
                SimpleNamespace(student_id="dup"),
            )
        ),
    )
    monkeypatch.setattr(planning, "list_group_plans", lambda *_a, **_k: ())
    with pytest.raises(Exception, match="duplicate"):
        planning.inspect_target_cluster_preflight("target-b", "lesson-target")
    monkeypatch.setattr(
        planning,
        "load_required_roster",
        lambda *_a: SimpleNamespace(students=(SimpleNamespace(student_id="only"),)),
    )
    monkeypatch.setattr(
        planning,
        "list_group_plans",
        lambda *_a, **_k: (
            SimpleNamespace(class_id="source-a", activity_id="lesson-target"),
        ),
    )
    with pytest.raises(Exception, match="ownership"):
        planning.inspect_target_cluster_preflight("target-b", "lesson-target")


@pytest.mark.parametrize("count", (29, 30))
def test_create_draft_pins_target_roster_and_zero_students(
    count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    approved = _reviewed(count)
    actor = WorkflowActor(actor_id="synthetic-teacher")
    observed: list[object] = []
    monkeypatch.setattr(
        planning, "inspect_target_cluster_preflight", lambda *_a, **_k: approved
    )

    def capture(request: object, **kwargs: object) -> SimpleNamespace:
        observed.append((request, kwargs))
        return SimpleNamespace(group_plan_id="new-plan", status="draft")

    monkeypatch.setattr(planning, "create_group_plan", capture)
    result = planning.create_target_six_cluster_draft(
        approved,
        group_plan_id="new-plan",
        actor=actor,
        workspace_root=Path("synthetic"),
    )
    assert result.status == "draft"
    assert len(observed) == 1
    request, kwargs = observed[0]  # type: ignore[misc]
    assert request.class_id == "target-b"
    assert request.activity_id == "lesson-target"
    assert request.strategy == "manual"
    assert request.expected_snapshot_revision == 3
    assert request.expected_roster_student_ids == approved.roster_student_ids
    assert request.target_group_count == 6
    assert len(request.proposed_groups) == 6
    assert all(not group.student_ids for group in request.proposed_groups)
    assert kwargs["workspace_root"] == Path("synthetic")


@pytest.mark.parametrize(
    "changed",
    (
        _reviewed(revision=4),
        _reviewed(30),
        _reviewed(plan_count=1),
        _reviewed(group_count=6),
    ),
)
def test_stale_or_already_planned_target_never_calls_writer(
    changed: planning.TargetClusterPreflight, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _reviewed()
    monkeypatch.setattr(
        planning, "inspect_target_cluster_preflight", lambda *_a, **_k: changed
    )
    monkeypatch.setattr(
        planning,
        "create_group_plan",
        lambda *_a, **_k: pytest.fail("no write on stale or existing target"),
    )
    with pytest.raises(ConcordWorkflowConflictError):
        planning.create_target_six_cluster_draft(
            original, group_plan_id="fresh", actor=WorkflowActor(actor_id="teacher")
        )


def test_finish_target_cluster_setup_does_not_prompt_actor_or_write(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided, "inspect_target_cluster_preflight", lambda *_a, **_k: _reviewed()
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "3")
    monkeypatch.setattr(
        guided,
        "confirm_actor_write",
        lambda *_a, **_k: pytest.fail("no actor request before chosen action"),
    )
    monkeypatch.setattr(
        guided,
        "create_target_six_cluster_draft",
        lambda *_a, **_k: pytest.fail("no write during finish"),
    )
    guided._launch_target_cluster_planning(_activity(), MenuSessionContext())
    output = capsys.readouterr().out
    assert "Verified Core roster: 29 students" in output
    assert "5 / 5 / 5 / 5 / 5 / 4" in output
    assert "not assigned or required" in output
    assert "source-class student IDs" in output


def test_create_target_draft_is_explicit_and_receipted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before, after = _reviewed(), _reviewed(revision=4, plan_count=1)
    reads = iter((before, after))
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided, "inspect_target_cluster_preflight", lambda *_a, **_k: next(reads)
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    answers = iter(("1", "2"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    monkeypatch.setattr(guided, "_fresh_id", lambda prefix: f"{prefix}-test")
    review: list[tuple[str, ...]] = []
    monkeypatch.setattr(
        guided,
        "confirm_actor_write",
        lambda _title, _verb, lines, **_k: (
            review.append(tuple(lines)),
            WorkflowActor(actor_id="teacher"),
        )[1],
    )
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=_activity()),
    )
    monkeypatch.setattr(guided, "standards_for_activity", lambda _a: None)
    writes: list[object] = []
    monkeypatch.setattr(
        guided,
        "create_target_six_cluster_draft",
        lambda read, **_k: (
            writes.append(read),
            SimpleNamespace(
                group_plan_id="group-plan-test",
                commit=SimpleNamespace(snapshot_revision=4),
            ),
        )[1],
    )
    monkeypatch.setattr(
        guided,
        "show_group_plan",
        lambda *_a, **_k: SimpleNamespace(
            summary=SimpleNamespace(
                status="draft",
                proposed_group_count=6,
                assigned_student_count=0,
                unresolved_student_count=29,
            )
        ),
    )
    monkeypatch.setattr(guided, "show_result", lambda *_a: None)
    guided._launch_target_cluster_planning(_activity(), MenuSessionContext())
    assert len(review) == 1
    assert len(writes) == 1
    assert writes[0] == before
    assert "target-b" in " ".join(review[0])
    assert "source students" in " ".join(review[0]).lower()


def test_existing_plan_cannot_be_recreated_by_shortcut(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[object] = []
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided,
        "inspect_target_cluster_preflight",
        lambda *_a, **_k: _reviewed(plan_count=1),
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda *_a, **_k: SimpleNamespace(summary=_activity()),
    )
    monkeypatch.setattr(
        guided,
        "launch_group_plan_menu",
        lambda a, _state: observed.append(a),
    )
    monkeypatch.setattr(
        guided,
        "create_target_six_cluster_draft",
        lambda *_a, **_k: pytest.fail("never create over existing target plans"),
    )
    answers = iter(("1", "2"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    guided._launch_target_cluster_planning(_activity(), MenuSessionContext())
    assert len(observed) == 1
    assert observed[0].class_id == "target-b"


def test_read_error_halts_without_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        guided, "resolve_read_workspace_root", lambda: Path("synthetic")
    )
    monkeypatch.setattr(
        guided,
        "inspect_target_cluster_preflight",
        lambda *_a, **_k: (_ for _ in ()).throw(ValueError("confidential path")),
    )
    results: list[str] = []
    monkeypatch.setattr(
        guided, "show_result", lambda _title, lines: results.extend(lines)
    )
    monkeypatch.setattr(
        guided,
        "create_target_six_cluster_draft",
        lambda *_a, **_k: pytest.fail("failed read must never write"),
    )
    guided._launch_target_cluster_planning(_activity(), MenuSessionContext())
    assert results
    assert "confidential path" not in " ".join(results)
