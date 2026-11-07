"""#147 Slice 2: page-scoped selection and real Cluster-first menu acceptance."""

from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.classes import write_class_roster
from test_group_plan_manual_issue51 import _actor, _roster, _workspace

import concord.menu_group_plan_bulk as bulk_menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.models import PlannedGroup
from concord.storage import list_record_revisions, list_work_snapshots
from concord.workflows import show_group_plan
from concord.workflows.group_plan_manual import (
    CreateManualGroupPlanRequest,
    create_manual_group_plan,
)


def _choices(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(bulk_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(bulk_menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(bulk_menu, "print_navigation", lambda **_kw: None)
    monkeypatch.setattr(bulk_menu, "pause_for_user", lambda *_a: None)


def test_scoped_page_and_all_selection_persist_over_three_pages(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    items = tuple(range(29))
    labels = tuple(f"Synthetic Student {item}" for item in items)
    _choices(monkeypatch, ["v", "n", "v", "p", "2", "d"])
    chosen = bulk_menu.select_cluster_roster_students("Choose", items, labels)
    assert chosen == tuple(item for item in range(20) if item != 1)
    out = capsys.readouterr().out
    assert "Select eligible students visible on this page only" in out
    assert "Select ALL eligible students across EVERY page" in out
    assert "Selected: 20 of 29 eligible" in out

    _choices(monkeypatch, ["n", "a", "c", "v", "d"])
    selected = bulk_menu.select_cluster_roster_students("Choose", items, labels)
    assert selected == tuple(range(10, 20))
    _choices(monkeypatch, ["a", "d"])
    assert bulk_menu.select_cluster_roster_students("Choose", items, labels) == items


def test_selector_preserves_initial_selection_and_cancel_is_no_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    items = tuple(range(30))
    _choices(monkeypatch, ["n", "1", "d"])
    result = bulk_menu.select_cluster_roster_students(
        "Choose", items, tuple(map(str, items)), initial_selected=(0,)
    )
    assert result == (0, 10)
    _choices(monkeypatch, ["b"])
    with pytest.raises(CancelMenuAction):
        bulk_menu.select_cluster_roster_students(
            "Choose", items, tuple(map(str, items))
        )


def _plan(tmp_path: Path, count: int) -> tuple[Path, object]:
    root, snapshot = _workspace(tmp_path)
    write_class_roster(
        root,
        _roster(*(f"student-{item}" for item in range(1, count + 1))),
        overwrite=True,
    )
    created = create_manual_group_plan(
        CreateManualGroupPlanRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_plan_id="plan-1",
            proposed_groups=tuple(
                PlannedGroup(
                    planned_group_key=f"c{index}",
                    label=f"Cluster {index}",
                    student_ids=("student-1",) if index == 1 else (),
                )
                for index in range(1, 7)
            ),
            expected_snapshot_revision=snapshot,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    detail = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert detail.summary.snapshot_revision == created.commit.snapshot_revision
    return root, detail


@pytest.mark.parametrize("count", [29, 30])
def test_real_cluster_first_selection_is_one_plan_revision_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    count: int,
) -> None:
    root, detail = _plan(tmp_path, count)
    monkeypatch.setenv("PDS_WORKSPACE_ROOT", str(root))
    shown: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        bulk_menu,
        "show_result",
        lambda title, lines: shown.append((title, tuple(lines))),
    )
    _choices(monkeypatch, ["2", "1", "1", "n", "1", "d", "SAVE BATCH"])
    before_snapshots = len(list_work_snapshots(root, _work()))
    before_revisions = len(list_record_revisions(root, _work(), "group_plan", "plan-1"))
    bulk_menu.launch_cluster_bulk_editor(detail, MenuSessionContext(actor=_actor()))
    updated = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert len(list_work_snapshots(root, _work())) == before_snapshots + 1
    after_revisions = list_record_revisions(root, _work(), "group_plan", "plan-1")
    assert len(after_revisions) == before_revisions + 1
    assert sum(map(lambda g: len(g.student_ids), updated.plan.proposed_groups)) == 2
    assert len(updated.plan.unresolved_student_ids) == count - 2
    assert shown and shown[-1][0] == "Bulk Planning Result"
    assert any(
        "Canonical Groups and Core roster were not changed" in line
        for line in shown[-1][1]
    )


def _work():
    from pds_core.routing_models import ModuleWorkRef

    return ModuleWorkRef(module_id="concord", class_id="class-1", work_id="activity-1")


def test_impact_review_back_preserves_selected_ids(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, detail = _plan(tmp_path, 29)
    monkeypatch.setenv("PDS_WORKSPACE_ROOT", str(root))
    monkeypatch.setattr(bulk_menu, "show_result", lambda *_a, **_kw: None)
    _choices(monkeypatch, ["2", "1", "1", "d", "b", "d", "SAVE BATCH"])
    bulk_menu.launch_cluster_bulk_editor(detail, MenuSessionContext(actor=_actor()))
    after = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert after.record_revision == detail.record_revision + 1


def test_abandoned_selector_does_not_mutate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, detail = _plan(tmp_path, 29)
    monkeypatch.setenv("PDS_WORKSPACE_ROOT", str(root))
    _choices(monkeypatch, ["2", "1", "b"])
    before = len(list_work_snapshots(root, _work()))
    with pytest.raises(CancelMenuAction):
        bulk_menu.launch_cluster_bulk_editor(detail, MenuSessionContext(actor=_actor()))
    assert len(list_work_snapshots(root, _work())) == before


@pytest.mark.parametrize(
    ("count", "sizes"),
    ((29, (5, 5, 5, 5, 4, 5)), (30, (6, 5, 5, 3, 6, 5))),
)
def test_six_cluster_distributions_via_real_menu_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    count: int,
    sizes: tuple[int, ...],
) -> None:
    root, _ = _plan(tmp_path, count)
    monkeypatch.setenv("PDS_WORKSPACE_ROOT", str(root))
    monkeypatch.setattr(bulk_menu, "show_result", lambda *_a: None)
    assignments: dict[int, set[str]] = {}
    first = 1
    for index, size in enumerate(sizes, start=1):
        assignments[index] = {
            f"student-{student}" for student in range(first, first + size)
        }
        first += size

    def choose_for_cluster(title, students, _labels, *, initial_selected=()):
        _ = initial_selected
        cluster_number = int(title.split()[1])
        return tuple(
            student for student in students
            if student.student_id in assignments[cluster_number]
        )

    monkeypatch.setattr(
        bulk_menu, "select_cluster_roster_students", choose_for_cluster
    )
    inputs = iter(
        item
        for index in range(1, 7)
        for item in (str(index), "1", "SAVE BATCH")
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    before = len(list_record_revisions(root, _work(), "group_plan", "plan-1"))
    for _ in range(6):
        detail = show_group_plan(
            "class-1", "activity-1", "plan-1", workspace_root=root
        )
        bulk_menu.launch_cluster_bulk_editor(detail, MenuSessionContext(actor=_actor()))
    final = show_group_plan("class-1", "activity-1", "plan-1", workspace_root=root)
    assert tuple(len(g.student_ids) for g in final.plan.proposed_groups) == sizes
    assert final.plan.unresolved_student_ids == ()
    assigned = [s for g in final.plan.proposed_groups for s in g.student_ids]
    assert len(assigned) == len(set(assigned)) == count
    revisions = list_record_revisions(root, _work(), "group_plan", "plan-1")
    assert len(revisions) == before + 6
    from concord.workflows import show_activity

    summary = show_activity("class-1", "activity-1", workspace_root=root).summary
    assert summary.group_count == 0


def test_back_from_review_then_selector_cancels_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, detail = _plan(tmp_path, 29)
    monkeypatch.setenv("PDS_WORKSPACE_ROOT", str(root))
    _choices(monkeypatch, ["2", "1", "1", "d", "b", "b"])
    before = list_work_snapshots(root, _work())
    with pytest.raises(CancelMenuAction):
        bulk_menu.launch_cluster_bulk_editor(detail, MenuSessionContext(actor=_actor()))
    assert list_work_snapshots(root, _work()) == before


@pytest.mark.parametrize("command", ["m", "q"])
def test_parent_planned_cluster_menu_propagates_main_quit(
    monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    from types import SimpleNamespace

    import concord.menu_group_plan as parent_menu
    from concord.menu_navigation import QuitPDS, ReturnToMainMenu

    detail = SimpleNamespace(
        plan=SimpleNamespace(group_plan_id="plan-1", status="draft")
    )
    monkeypatch.setattr(parent_menu, "show_group_plan", lambda *_a: detail)
    monkeypatch.setattr(parent_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(parent_menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(parent_menu, "print_navigation", lambda: None)
    monkeypatch.setattr(
        parent_menu, "_manage_cluster_bulk", lambda *_a: _raise_nav(command)
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "4")
    error_type = ReturnToMainMenu if command == "m" else QuitPDS
    with pytest.raises(error_type):
        parent_menu._planned_group_menu(
            SimpleNamespace(class_id="class-1", activity_id="activity-1"),
            "plan-1",
            MenuSessionContext(actor=_actor()),
        )


def _raise_nav(command: str) -> None:
    from concord.menu_navigation import parse_menu_navigation

    parse_menu_navigation(command)


@pytest.mark.parametrize("command", ["m", "q"])
def test_top_level_group_plan_menu_propagates_main_quit(
    monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    from types import SimpleNamespace

    import concord.menu_group_plan as parent_menu
    from concord.menu_navigation import QuitPDS, ReturnToMainMenu

    activity = SimpleNamespace(
        class_id="class-1", activity_id="activity-1", title="Synthetic Activity"
    )
    monkeypatch.setattr(parent_menu, "_latest", lambda _a: activity)
    monkeypatch.setattr(parent_menu, "_select_plan", lambda *_a, **_kw: object())
    monkeypatch.setattr(parent_menu, "_open_plan", lambda *_a: _raise_nav(command))
    monkeypatch.setattr(parent_menu, "clear_screen", lambda: None)
    monkeypatch.setattr(parent_menu, "print_menu_header", lambda *_a: None)
    monkeypatch.setattr(parent_menu, "print_navigation", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "6")
    error_type = ReturnToMainMenu if command == "m" else QuitPDS
    with pytest.raises(error_type):
        parent_menu.launch_group_plan_menu(activity, MenuSessionContext(actor=_actor()))
