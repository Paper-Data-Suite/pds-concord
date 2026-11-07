"""Teacher-facing, Cluster-first manual GroupPlan bulk placement.

Only a Concord proposal is changed; Core rosters and operational Groups are not.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from pds_core.classes import load_class_roster
from pds_core.rosters import StudentRecord, student_display_name, student_sort_name
from pds_core.workspace import resolve_workspace_root

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    parse_menu_navigation,
)
from concord.menu_prompts import select_one, show_result
from concord.menu_standards_context import standards_kwargs_for_plan
from concord.menu_teacher_history import distinguish_equal_labels
from concord.menu_ui import (
    clear_screen,
    page_count,
    page_items,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.workflows import GroupPlanDetail
from concord.workflows.group_plan_manual import (
    BulkPlannedGroupEditPreview,
    BulkPlannedGroupEditRequest,
    commit_bulk_planned_group_edit,
    prepare_bulk_planned_group_edit,
)

T = TypeVar("T")


def select_cluster_roster_students(
    title: str,
    items: Sequence[T],
    labels: Sequence[str],
    *,
    initial_selected: tuple[T, ...] = (),
) -> tuple[T, ...]:
    """Choose students with explicit visible-page and all-pages scopes.

    Keep this local to GroupPlan; shared select_many(A) retains its old meaning.
    """
    if len(items) != len(labels):
        raise ValueError("Roster choices and labels must have equal length.")
    if not items:
        return ()
    selected = {
        index for index, item in enumerate(items) if item in initial_selected
    }
    page = 0
    while True:
        clear_screen()
        print_menu_header(title)
        start = page * 10
        visible = page_items(items, page)
        for offset, label in enumerate(page_items(labels, page)):
            index = start + offset
            marker = "x" if index in selected else " "
            print(f"{offset + 1}. [{marker}] {label}")
        print()
        print(f"Page {page + 1} of {page_count(len(items))}")
        print(f"Selected: {len(selected)} of {len(items)} eligible")
        if page < page_count(len(items)) - 1:
            print("N. Next page")
        if page:
            print("P. Previous page")
        print("V. Select eligible students visible on this page only")
        print("A. Select ALL eligible students across EVERY page")
        print("C. Clear selections across all pages")
        print("D. Review selected students")
        print_navigation()
        raw = input("Choose an item or action: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Bulk Selection Help")
            print("A selects every eligible student on every page; V only this page.")
            print("Numbers toggle a student. N/P navigate without losing selections.")
            print("D reviews; B abandons this selection without saving anything.")
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        action = raw.casefold()
        if action == "n" and page < page_count(len(items)) - 1:
            page += 1
        elif action == "p" and page:
            page -= 1
        elif action == "v":
            selected.update(range(start, start + len(visible)))
        elif action == "a":
            selected.update(range(len(items)))
        elif action == "c":
            selected.clear()
        elif action == "d":
            return tuple(item for index, item in enumerate(items) if index in selected)
        elif raw.isdigit() and 1 <= int(raw) <= len(visible):
            index = start + int(raw) - 1
            if index in selected:
                selected.remove(index)
            else:
                selected.add(index)
        else:
            print("Choose a listed student, V, A, C, D, N, P, H, B, M or Q.")
            pause_for_user()


def _group_names(detail: GroupPlanDetail) -> dict[str | None, str]:
    names: dict[str | None, str] = {None: "Unresolved"}
    for group in detail.plan.proposed_groups:
        names[group.planned_group_key] = (
            f"{group.label} ({group.planned_group_key})"
        )
    return names


def _review_batch(
    detail: GroupPlanDetail,
    preview: BulkPlannedGroupEditPreview,
    names: dict[str, str],
) -> bool:
    """Show the exact zero-write review; Back retains selection in caller."""
    groups = _group_names(detail)
    added = sum(
        item.from_group_key is None for item in preview.changes
    )
    moved = sum(
        item.from_group_key is not None and item.to_group_key is not None
        for item in preview.changes
    )
    removed = sum(item.to_group_key is None for item in preview.changes)
    page = 0
    while True:
        clear_screen()
        print_menu_header("Review Planned Cluster Batch")
        print(f"Class: {preview.class_id}; Activity: {preview.activity_id}")
        print(f"GroupPlan: {preview.group_plan_id}; strategy: manual")
        print(f"Target: {groups[preview.planned_group_key]}")
        print(f"Status: {preview.original_status}")
        print(
            f"Snapshot: {preview.snapshot_revision}; "
            f"GroupPlan revision: {preview.record_revision}"
        )
        print(f"Core roster students: {len(preview.roster_student_ids)}")
        print(
            f"Selected: {len(preview.selected_student_ids)}; "
            f"added: {added}; moved: {moved}; removed: {removed}; "
            f"unchanged: {preview.unchanged_count}; conflicts: 0"
        )
        print(
            f"Unresolved: {preview.unresolved_before} -> "
            f"{preview.unresolved_after}"
        )
        before = dict(preview.before_sizes)
        for key, after in preview.after_sizes:
            print(f"{groups[key]}: {before[key]} -> {after}")
        print("Student changes (source -> destination):")
        for item in page_items(preview.changes, page):
            display = names.get(item.student_id, item.student_id)
            print(
                f"  {display} ({item.student_id}): "
                f"{groups[item.from_group_key]} -> {groups[item.to_group_key]}"
            )
        print(f"Changes page {page + 1} of {page_count(len(preview.changes))}")
        print(f"Review digest: {preview.review_digest}")
        if preview.original_status == "previewed":
            print("Saving returns this previewed GroupPlan to draft.")
        print("Only the planning proposal changes. Core roster, operational")
        print("Groups/Memberships, approval and application remain unchanged.")
        print("SAVE BATCH. Confirm the exact reviewed proposal change")
        if page < page_count(len(preview.changes)) - 1:
            print("N. Next changes page")
        if page:
            print("P. Previous changes page")
        print("B. Back to selection (keep selected students)")
        print_navigation(back=False)
        raw = input("Choose SAVE BATCH or navigation: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            print("Only SAVE BATCH commits this plan edit; Back changes selections.")
            pause_for_user()
        elif navigation is NavigationChoice.BACK:
            # parse_menu_navigation recognizes B only when enabled; here handle
            # B explicitly because the UI's review-specific Back is local.
            return False
        elif raw.casefold() == "b":
            return False
        elif raw.casefold() == "save batch":
            return True
        elif raw.casefold() == "n" and page < page_count(len(preview.changes)) - 1:
            page += 1
        elif raw.casefold() == "p" and page:
            page -= 1
        else:
            print("Choose SAVE BATCH, B, N, P, H, M or Q.")
            pause_for_user()


def launch_cluster_bulk_editor(
    detail: GroupPlanDetail, state: MenuSessionContext
) -> None:
    """Open a planned Cluster, review students, and save one proposal revision."""
    plan = detail.plan
    if plan.strategy != "manual" or plan.status not in {"draft", "previewed"}:
        show_result(
            "Bulk Planning Unavailable",
            (
                "Only draft or previewed manual GroupPlans support this bulk edit.",
                "Other plan strategies and approved/applied plans remain unchanged.",
            ),
        )
        return
    if not plan.proposed_groups:
        show_result("Bulk Planning", ("Add a planned Cluster first.",))
        return
    group = select_one(
        "Choose Planned Cluster for Bulk Placement",
        plan.proposed_groups,
        [
            f"{item.label} ({item.planned_group_key}); "
            f"current members: {len(item.student_ids)}"
            for item in plan.proposed_groups
        ],
        help_text="Choose a plan-local Cluster, not a canonical Group.",
    )
    operation = select_one(
        "Choose Batch Action",
        ("place_or_move", "unassign_from_target"),
        (
            "Add or move roster students INTO this planned Cluster",
            "Remove selected members to unresolved (not from Core roster)",
        ),
        help_text="Both actions change a GroupPlan proposal only.",
    )
    root = resolve_workspace_root()
    roster = load_class_roster(root, detail.summary.class_id)
    names = {
        student.student_id: student_display_name(student)
        for student in roster.students
    }
    assignment = {
        student_id: item.planned_group_key
        for item in plan.proposed_groups for student_id in item.student_ids
    }
    groups = _group_names(detail)
    students = tuple(
        sorted(
            (
                student for student in roster.students
                if operation == "place_or_move"
                or student.student_id in group.student_ids
            ),
            key=lambda student: (student_sort_name(student), student.student_id),
        )
    )
    labels = distinguish_equal_labels(
        tuple(
            f"{names[item.student_id]} ({item.student_id}); "
            f"currently {groups[assignment.get(item.student_id)]}"
            for item in students
        ),
        noun="roster student",
    )
    if not students:
        show_result("Bulk Planning", ("No eligible students for this action.",))
        return
    selected: tuple[StudentRecord, ...] = ()
    while True:
        selected = select_cluster_roster_students(
            f"{group.label} — Bulk Student Selection",
            students,
            labels,
            initial_selected=selected,
        )
        if not selected:
            show_result("Bulk Planning", ("No students selected; no changes saved.",))
            return
        request = BulkPlannedGroupEditRequest(
            class_id=detail.summary.class_id,
            activity_id=detail.summary.activity_id,
            group_plan_id=detail.summary.group_plan_id,
            planned_group_key=group.planned_group_key,
            operation=operation,
            student_ids=tuple(student.student_id for student in selected),
            expected_snapshot_revision=detail.summary.snapshot_revision,
            expected_record_revision=detail.record_revision,
            actor=state.require_actor(),
        )
        standards = standards_kwargs_for_plan(detail)
        preview = prepare_bulk_planned_group_edit(
            request, workspace_root=root, **standards
        )
        if preview.no_op:
            show_result("Bulk Planning", ("No assignments would change.",))
            return
        if not _review_batch(detail, preview, names):
            continue
        saved = commit_bulk_planned_group_edit(
            request, review_digest=preview.review_digest,
            workspace_root=root, **standards
        )
        show_result(
            "Bulk Planning Result",
            (
                "Batch saved." if saved.changed else "No changes were needed.",
                f"GroupPlan: {saved.detail.plan.group_plan_id}",
                f"Status: {saved.detail.plan.status}",
                f"Activity snapshot: {saved.detail.summary.snapshot_revision}",
                f"Plan record revision: {saved.detail.record_revision}",
                f"Changed students: {len(preview.changes)}",
                f"Unresolved: {saved.detail.summary.unresolved_student_count}",
                "Next: continue editing or preview the GroupPlan separately.",
                "Canonical Groups and Core roster were not changed.",
            ),
        )
        return
