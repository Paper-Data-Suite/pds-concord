"""Teacher-facing saved classroom groupings for one Concord Activity (#136)."""

from __future__ import annotations

from pds_core.rosters import student_display_name, student_lookup
from pds_core.workspace import resolve_workspace_root

from concord.class_group_arrangement_storage import (
    LoadedArrangement,
    list_current_arrangements,
)
from concord.class_group_arrangements import (
    SavedArrangementGroup,
    compare_roster,
)
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    confirm_write,
    handle_write_error,
    prompt_text,
    select_one,
    show_result,
    slug_identifier,
)
from concord.menu_standards_context import standards_kwargs_for_activity
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import PlannedGroup
from concord.workflows import ActivitySummary, list_group_plans, show_activity
from concord.workflows.class_group_arrangements import (
    PreparedGroupingReuse,
    ReuseGroupingRequest,
    SaveGroupingRequest,
    StudentPlacementDecision,
    prepare_reuse_grouping,
    prepare_save_grouping,
    reuse_grouping,
    save_grouping,
)
from concord.workflows.context import require_core_class
from concord.workflows.participants import load_required_roster


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _saved(
    activity: ActivitySummary, state: MenuSessionContext
) -> tuple[LoadedArrangement, ...]:
    root = resolve_workspace_root()
    year = require_core_class(root, activity.class_id).school_year
    return list_current_arrangements(
        root,
        class_id=activity.class_id,
        school_year=year,
        actor_id=state.require_actor().actor_id,
    )


def _select_saved(
    activity: ActivitySummary, state: MenuSessionContext
) -> LoadedArrangement | None:
    available = _saved(activity, state)
    active = tuple(item for item in available if item.revision.status == "active")
    if not active:
        show_result(
            "Saved groupings",
            ("No active saved groupings belong to this teacher and class.",),
        )
        return None
    return select_one(
        "Use saved grouping",
        active,
        [
            f"{item.revision.name} - {len(item.revision.groups)} groups; "
            f"{sum(len(g.student_ids) for g in item.revision.groups)} assigned"
            for item in active
        ],
        help_text="Choose a grouping saved for this exact Core class and school year.",
    )


def _names(activity: ActivitySummary) -> dict[str, str]:
    roster = load_required_roster(resolve_workspace_root(), activity.class_id)
    return {
        student_id: student_display_name(student)
        for student_id, student in student_lookup(roster).items()
    }


def _show_placements(
    activity: ActivitySummary,
    groups: tuple[SavedArrangementGroup, ...] | tuple[PlannedGroup, ...],
    unresolved: tuple[str, ...],
    *,
    title: str,
) -> None:
    """Show sensitive member details only in an explicit teacher review."""
    names = _names(activity)
    clear_screen()
    print_menu_header(title)
    print(f"Class: {activity.class_id}")
    print(f"Groups: {len(groups)}")
    print()
    for group in groups:
        label = group.label
        students = group.student_ids
        print(f"{label} - {len(students)} students")
        for sid in students:
            print(f"  {names.get(sid, 'Departed / unknown student (' + sid + ')')}")
    if unresolved:
        print()
        print(f"Explicitly unresolved: {len(unresolved)}")
        for sid in unresolved:
            print(f"  {names.get(sid, 'Departed / unknown student (' + sid + ')')}")
    print()
    pause_for_user()


def save_grouping_from_plan(
    activity: ActivitySummary,
    state: MenuSessionContext,
    *,
    group_plan_id: str | None = None,
) -> None:
    """Save an exact editable proposal, using one reviewed confirmation."""
    try:
        current = _latest(activity)
        if group_plan_id is None:
            plans = tuple(
                p
                for p in list_group_plans(current.class_id, current.activity_id)
                if p.status in {"draft", "previewed"}
            )
            if not plans:
                show_result(
                    "Save current grouping",
                    ("Create or edit a GroupPlan before saving its grouping.",),
                )
                return
            selected = select_one(
                "Select grouping source",
                plans,
                [
                    f"{p.group_plan_id} - {p.proposed_group_count} groups; "
                    f"{p.assigned_student_count} assigned"
                    for p in plans
                ],
                help_text="Only editable GroupPlans can be saved in this workflow.",
            )
            group_plan_id = selected.group_plan_id
        name = prompt_text(
            "Save current grouping",
            "Grouping name",
            help_text="Use a readable class grouping name, e.g. Six Table Groups.",
        )
        assert name is not None
        arrangement_id = prompt_text(
            "Save current grouping",
            "Grouping identifier",
            help_text="A stable identifier for this class grouping library entry.",
            default=slug_identifier(name, "saved-grouping"),
        )
        assert arrangement_id is not None
        request = SaveGroupingRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            group_plan_id=group_plan_id,
            arrangement_id=arrangement_id,
            name=name,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
        )
        preview = prepare_save_grouping(request)
        _show_placements(
            current,
            preview.groups,
            preview.unresolved_student_ids,
            title="Review grouping before saving",
        )
        if not confirm_write(
            "Save current grouping",
            "SAVE",
            (
                f"Grouping: {preview.name}",
                f"Groups: {len(preview.groups)}",
                f"Assigned students: {preview.assigned_count}",
                f"Unresolved students: {len(preview.unresolved_student_ids)}",
                "Only grouping choices are saved; no Scores or Activity state.",
            ),
        ):
            return
        saved = save_grouping(request, review_digest=preview.review_digest)
        show_result(
            "Saved grouping",
            (
                f"Saved: {saved.revision.name}",
                f"Groups: {len(saved.revision.groups)}",
                "Available for later Activities in this exact class.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        handle_write_error(
            error,
            reload=lambda: _latest(activity),
            error_title="Saved grouping error",
        )


def _collect_decisions(
    activity: ActivitySummary, saved: LoadedArrangement
) -> tuple[tuple[StudentPlacementDecision, ...], tuple[str, ...]] | None:
    root = resolve_workspace_root()
    year = require_core_class(root, activity.class_id).school_year
    roster = load_required_roster(root, activity.class_id)
    comparison = compare_roster(
        saved.revision,
        target_class_id=activity.class_id,
        target_school_year=year,
        target_student_ids=tuple(sorted(s.student_id for s in roster.students)),
    )
    names = _names(activity)
    departed = comparison.departed_ids
    if departed:
        if not confirm_write(
            "Review departed students",
            "ACKNOWLEDGE",
            (
                f"Saved students no longer enrolled: {len(departed)}",
                *[f"  {sid}" for sid in departed],
                "These students will not be copied into the new Activity plan.",
            ),
        ):
            return None
    needs = tuple(
        sorted(set(comparison.newly_enrolled_ids) | set(comparison.unresolved_ids))
    )
    decisions: list[StudentPlacementDecision] = []
    options: tuple[str | None, ...] = (
        None,
        *(group.key for group in saved.revision.groups),
    )
    labels = ("Leave explicitly unresolved",) + tuple(
        group.label for group in saved.revision.groups
    )
    for sid in needs:
        selection = select_one(
            f"Place {names.get(sid, sid)}",
            options,
            labels,
            help_text=(
                "This newly enrolled or previously unresolved student needs "
                "an explicit group or unresolved decision. The final "
                "plan still requires one separate CREATE confirmation."
            ),
        )
        decisions.append(StudentPlacementDecision(student_id=sid, group_key=selection))
    return tuple(decisions), departed


def _preview_reuse(activity: ActivitySummary, preview: PreparedGroupingReuse) -> None:
    _show_placements(
        activity,
        preview.groups,
        preview.unresolved_student_ids,
        title="Review fresh GroupPlan placement",
    )


def use_saved_grouping(activity: ActivitySummary, state: MenuSessionContext) -> None:
    """Materialize a fresh *draft* after roster review and one explicit write."""
    try:
        current = _latest(activity)
        saved = _select_saved(current, state)
        if saved is None:
            return
        _show_placements(
            current,
            saved.revision.groups,
            saved.revision.unresolved_student_ids,
            title=f"Saved grouping: {saved.revision.name}",
        )
        proposed_id = slug_identifier(
            f"{current.activity_id}-{saved.revision.name}", "group-plan"
        )
        new_id = prompt_text(
            "Use saved grouping",
            "New GroupPlan identifier",
            help_text="New Activity-owned plan ID, never the saved library identity.",
            default=proposed_id,
        )
        assert new_id is not None
        current_plans = list_group_plans(current.class_id, current.activity_id)
        acknowledged = False
        if current_plans:
            acknowledged = confirm_write(
                "Review existing Activity plans",
                "ACKNOWLEDGE",
                (
                    f"Existing plans: {len(current_plans)}",
                    "Creating a new separate draft will not replace them.",
                    "Review existing plans first if you are unsure.",
                ),
            )
            if not acknowledged:
                return
        reconciliation = _collect_decisions(current, saved)
        if reconciliation is None:
            return
        decisions, departed = reconciliation
        request = ReuseGroupingRequest(
            class_id=current.class_id,
            activity_id=current.activity_id,
            arrangement_id=saved.revision.arrangement_id,
            new_group_plan_id=new_id,
            expected_snapshot_revision=current.snapshot_revision,
            actor=state.require_actor(),
            placement_decisions=decisions,
            acknowledged_departed_student_ids=departed,
            acknowledge_existing_plans=acknowledged,
        )
        prepared = prepare_reuse_grouping(request)
        _preview_reuse(current, prepared)
        if not confirm_write(
            "Create Activity grouping draft",
            "CREATE",
            (
                f"Saved grouping: {saved.revision.name}",
                f"New GroupPlan: {new_id}",
                f"Groups: {len(prepared.groups)}",
                f"Assigned students: {prepared.assigned_count}",
                f"Unresolved students: {len(prepared.unresolved_student_ids)}",
                "Creates one editable draft, not canonical Groups or Scores.",
            ),
        ):
            return
        result = reuse_grouping(
            request,
            review_digest=prepared.review_digest,
            **standards_kwargs_for_activity(current),
        )
        show_result(
            "Saved grouping reused",
            (
                f"New draft GroupPlan: {result.group_plan_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
                "Open this plan to edit, preview, approve and apply it.",
                "Canonical Groups created: no",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        handle_write_error(
            error,
            reload=lambda: _latest(activity),
            error_title="Saved grouping error",
        )


def manage_saved_groupings(
    activity: ActivitySummary, state: MenuSessionContext
) -> None:
    """Authorized browsing; revision and retirement actions follow separately."""
    try:
        available = _saved(activity, state)
        if not available:
            show_result("Saved groupings", ("No saved groupings for this class.",))
            return
        selected = select_one(
            "Manage saved groupings",
            available,
            [
                f"{item.revision.name} - {item.revision.status}; "
                f"revision {item.revision.revision}; "
                f"{len(item.revision.groups)} groups"
                for item in available
            ],
            help_text="Browse only saved groupings owned by this teacher and class.",
        )
        _show_placements(
            activity,
            selected.revision.groups,
            selected.revision.unresolved_student_ids,
            title=f"{selected.revision.name} ({selected.revision.status})",
        )
        show_result(
            "Saved grouping details",
            (
                f"Name: {selected.revision.name}",
                f"Status: {selected.revision.status}",
                f"Revision: {selected.revision.revision}",
                f"Groups: {len(selected.revision.groups)}",
                "Rename, revise, retire, and history commands follow in a later slice.",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        show_result("Saved grouping error", (str(error),))


def launch_saved_groupings_menu(
    activity: ActivitySummary, state: MenuSessionContext
) -> None:
    """Primary teacher entry: normal reuse never requires a CSV or raw IDs."""
    while True:
        clear_screen()
        print_menu_header("Saved class groupings")
        print(f"Activity: {activity.title}")
        print()
        print("1. Use saved grouping")
        print("2. Save current grouping")
        print("3. Manage saved groupings")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Saved groupings help",
                (
                    "Save an editable Activity GroupPlan for later classroom use.",
                    "Reuse produces a fresh editable GroupPlan for this Activity.",
                    "Review, approve, and apply separately to create real Groups.",
                    "Scores and evidence are never reused with a grouping.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            use_saved_grouping(activity, state)
        elif choice == "2":
            save_grouping_from_plan(activity, state)
        elif choice == "3":
            manage_saved_groupings(activity, state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()
