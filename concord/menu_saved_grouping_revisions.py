"""Teacher-facing reviewed revision actions for class-scoped saved groupings."""

from __future__ import annotations

from collections.abc import Callable

from pds_core.workspace import resolve_workspace_root

from concord.class_group_arrangement_storage import (
    LoadedArrangement,
    list_arrangement_history,
    load_current_arrangement,
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
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.workflows import ActivitySummary, list_group_plans, show_activity
from concord.workflows.class_group_arrangement_revision import (
    ChangeGroupingRequest,
    change_grouping,
    prepare_grouping_change,
)
from concord.workflows.context import require_core_class

PlacementViewer = Callable[..., None]


def _current(
    activity: ActivitySummary,
    state: MenuSessionContext,
    arrangement_id: str,
) -> LoadedArrangement:
    root = resolve_workspace_root()
    school_year = require_core_class(root, activity.class_id).school_year
    return load_current_arrangement(
        root,
        class_id=activity.class_id,
        school_year=school_year,
        arrangement_id=arrangement_id,
        actor_id=state.require_actor().actor_id,
    )


def _change(
    activity: ActivitySummary,
    state: MenuSessionContext,
    selected: LoadedArrangement,
    action: str,
    *,
    show_placements: PlacementViewer,
) -> bool:
    """Return True only after an immutable revision was committed."""
    request_args: dict[str, object] = {
        "class_id": activity.class_id,
        "arrangement_id": selected.revision.arrangement_id,
        "expected_revision": selected.revision.revision,
        "expected_sha256": selected.sha256,
        "actor": state.require_actor(),
        "action": action,
    }
    if action == "rename":
        name = prompt_text(
            "Rename saved grouping",
            "New grouping name",
            help_text="Change only this grouping's teacher-facing name.",
            default=selected.revision.name,
        )
        assert name is not None
        request_args["new_name"] = name
    elif action == "replace_from_plan":
        current_activity = show_activity(
            activity.class_id, activity.activity_id
        ).summary
        plans = tuple(
            p
            for p in list_group_plans(activity.class_id, activity.activity_id)
            if p.status in {"draft", "previewed"}
        )
        if not plans:
            show_result(
                "Revise saved grouping",
                ("No editable GroupPlan exists for this Activity.",),
            )
            return False
        chosen = select_one(
            "Replace from editable GroupPlan",
            plans,
            [
                f"{p.group_plan_id} - {p.proposed_group_count} groups; "
                f"{p.assigned_student_count} assigned"
                for p in plans
            ],
            help_text=(
                "Take one exact snapshot from this Activity's editable plan. "
                "Existing Activities will not change."
            ),
        )
        request_args.update(
            source_activity_id=current_activity.activity_id,
            source_group_plan_id=chosen.group_plan_id,
            expected_source_snapshot_revision=current_activity.snapshot_revision,
        )
    request = ChangeGroupingRequest(**request_args)  # type: ignore[arg-type]
    prepared = prepare_grouping_change(request)
    if action == "replace_from_plan":
        show_placements(
            activity,
            prepared.groups,
            prepared.unresolved_student_ids,
            title="Review new saved grouping placements",
        )
    label = {
        "rename": "RENAME",
        "replace_from_plan": "REVISE",
        "retire": "RETIRE",
    }[action]
    if not confirm_write(
        f"Review saved grouping: {action.replace('_', ' ')}",
        label,
        (
            f"Grouping: {prepared.name}",
            f"Revision: {prepared.previous_revision} -> {prepared.new_revision}",
            f"Groups: {len(prepared.groups)}",
            f"Assigned: {prepared.assigned_count}",
            f"Unresolved: {len(prepared.unresolved_student_ids)}",
            f"New status: {prepared.status}",
            "Earlier revisions and existing Activities are unchanged.",
        ),
    ):
        return False
    written = change_grouping(request, review_digest=prepared.review_digest)
    show_result(
        "Saved grouping updated",
        (
            f"Grouping: {written.revision.name}",
            f"Current revision: {written.revision.revision}",
            f"Status: {written.revision.status}",
            "Existing Activity Groups, Memberships, and Scores unchanged.",
        ),
    )
    return True


def _show_history(
    activity: ActivitySummary,
    state: MenuSessionContext,
    item: LoadedArrangement,
) -> None:
    root = resolve_workspace_root()
    school_year = require_core_class(root, activity.class_id).school_year
    revisions = list_arrangement_history(
        root,
        class_id=activity.class_id,
        school_year=school_year,
        arrangement_id=item.revision.arrangement_id,
        actor_id=state.require_actor().actor_id,
    )
    show_result(
        "Saved grouping history",
        (
            f"Grouping: {item.revision.arrangement_id}",
            *(
                f"Revision {r.revision.revision}: {r.revision.name} "
                f"({r.revision.status}; {len(r.revision.groups)} groups)"
                for r in revisions
            ),
            "Historical revisions are immutable; no Activity was modified.",
        ),
    )


def manage_grouping_revision(
    activity: ActivitySummary,
    state: MenuSessionContext,
    initial: LoadedArrangement,
    *,
    show_placements: PlacementViewer,
) -> None:
    """Manage one teacher-owned saved grouping with non-destructive navigation."""
    arrangement_id = initial.revision.arrangement_id
    while True:
        try:
            selected = _current(activity, state, arrangement_id)
            clear_screen()
            print_menu_header("Manage saved grouping")
            print(f"Name: {selected.revision.name}")
            print(f"Status: {selected.revision.status}")
            print(f"Revision: {selected.revision.revision}")
            print(f"Groups: {len(selected.revision.groups)}")
            print()
            print("1. Review saved placements")
            print("2. View revision history")
            if selected.revision.status == "active":
                print("3. Rename saved grouping")
                print("4. Replace membership from editable GroupPlan")
                print("5. Retire saved grouping")
            print_navigation()
            print()
            choice = input("Select an option: ").strip()
            navigation = parse_menu_navigation(choice)
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Saved grouping management help",
                    (
                        "Rename updates the label in a new immutable revision.",
                        "Replace requires an editable GroupPlan and exact roster.",
                        "Retire prevents future reuse without deleting history.",
                        "Existing Activities never change with these actions.",
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                show_placements(
                    activity,
                    selected.revision.groups,
                    selected.revision.unresolved_student_ids,
                    title=f"Saved grouping: {selected.revision.name}",
                )
            elif choice == "2":
                _show_history(activity, state, selected)
            elif selected.revision.status == "active" and choice in {"3", "4", "5"}:
                action = {"3": "rename", "4": "replace_from_plan", "5": "retire"}[
                    choice
                ]
                _change(
                    activity,
                    state,
                    selected,
                    action,
                    show_placements=show_placements,
                )
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except Exception as error:
            handle_write_error(
                error,
                reload=lambda: show_activity(activity.class_id, activity.activity_id),
                error_title="Saved grouping revision error",
            )
            return


__all__ = ["manage_grouping_revision"]
