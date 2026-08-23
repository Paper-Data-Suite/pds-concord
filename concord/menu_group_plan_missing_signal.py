"""Teacher-facing explicit decisions for signal-plan coverage gaps."""

from __future__ import annotations

from concord.group_plan_missing_signal import distribute_missing_signal_students
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_prompts import (
    confirm_write,
    prompt_exact_text,
    select_one,
    show_result,
)
from concord.menu_ui import clear_screen, pause_for_user, print_menu_header
from concord.workflows import (
    GroupPlanDetail,
    MissingSignalDispositionResult,
    MissingSignalPlanInspection,
    SetMissingSignalDispositionRequest,
    inspect_group_plan_missing_signal,
    set_missing_signal_disposition,
)


def _group_sizes(detail: GroupPlanDetail) -> tuple[int, ...]:
    return tuple(len(group.student_ids) for group in detail.plan.proposed_groups)


def _show_context(inspection: MissingSignalPlanInspection) -> None:
    clear_screen()
    print_menu_header("Resolve Missing-Signal Students")
    print(f"GroupPlan: {inspection.detail.plan.group_plan_id}")
    print(f"Signal set: {inspection.signal_set_id}")
    print(f"Core signal digest: {inspection.signal_set_digest}")
    print(f"Signal dimension: {inspection.dimension_id}")
    print(f"Roster students: {len(inspection.detail.plan.roster_student_ids)}")
    print(f"Missing-signal students: {len(inspection.missing_student_ids)}")
    print(f"Missing IDs: {', '.join(inspection.missing_student_ids) or '-'}")
    print(
        "Currently unresolved students: "
        f"{len(inspection.detail.plan.unresolved_student_ids)}"
    )
    if inspection.detail.plan.missing_signal_disposition is not None:
        print(
            "Current missing-signal disposition: "
            f"{inspection.detail.plan.missing_signal_disposition}"
        )
    print()
    print("No student band values are displayed or copied into the GroupPlan.")
    print()


def _show_random_preview(
    inspection: MissingSignalPlanInspection,
    *,
    seed: str,
) -> None:
    randomized = distribute_missing_signal_students(
        inspection.detail.plan.proposed_groups,
        inspection.missing_student_ids,
        seed=seed,
    )
    clear_screen()
    print_menu_header("Missing-Signal Random Distribution Preview")
    print(f"GroupPlan: {inspection.detail.plan.group_plan_id}")
    print(f"Signal set: {inspection.signal_set_id}")
    print(f"Core signal digest: {inspection.signal_set_digest}")
    print(f"Signal dimension: {inspection.dimension_id}")
    print(f"Affected missing-signal students: {len(inspection.missing_student_ids)}")
    print(f"Seed: {seed}")
    current_sizes = ",".join(str(size) for size in _group_sizes(inspection.detail))
    result_sizes = ",".join(str(size) for size in randomized.group_sizes)
    print(f"Current group sizes: {current_sizes}")
    print(f"Result group sizes: {result_sizes}")
    print("Resulting placements for affected students:")
    for student_id, planned_group_key in randomized.placements:
        print(f"  {student_id} -> {planned_group_key}")
    print()
    print("Students already represented by the selected signal will not move.")
    print("No canonical Groups or Memberships have been created.")
    print()
    pause_for_user()


def _result_lines(result: MissingSignalDispositionResult) -> tuple[str, ...]:
    lines = [
        f"GroupPlan: {result.mutation.group_plan_id}",
        f"Status: {result.mutation.status}",
        f"Missing-signal disposition: {result.disposition}",
        f"Missing-signal students: {result.missing_student_count}",
        f"Assigned students: {result.assigned_student_count}",
        f"Unresolved students: {result.unresolved_student_count}",
        f"Group sizes: {','.join(str(size) for size in result.group_sizes)}",
        f"Snapshot: {result.mutation.commit.snapshot_revision}",
    ]
    if result.random_seed is not None:
        lines.append(f"Random seed: {result.random_seed}")
    lines.append("Canonical Groups created: no")
    return tuple(lines)


def resolve_missing_signal_from_menu(
    detail: GroupPlanDetail,
    state: MenuSessionContext,
) -> None:
    """Require one explicit teacher decision for the exact current missing set."""

    try:
        inspection = inspect_group_plan_missing_signal(
            detail.summary.class_id,
            detail.summary.activity_id,
            detail.summary.group_plan_id,
        )
        _show_context(inspection)
        choice = select_one(
            "Resolve Missing-Signal Students",
            ("manual", "random", "leave_unassigned"),
            (
                "Confirm manual placement",
                "Distribute missing students randomly",
                "Leave missing students unassigned",
            ),
            help_text=(
                "The decision applies only to students Core diagnoses as missing "
                "from this GroupPlan's exact bound signal and dimension."
            ),
        )

        random_seed: str | None = None
        if choice == "manual":
            if not confirm_write(
                "Confirm Manual Missing-Signal Placement",
                "CONFIRM",
                (
                    f"GroupPlan: {inspection.detail.plan.group_plan_id}",
                    f"Missing IDs: {', '.join(inspection.missing_student_ids)}",
                    "Every exact missing-signal student must already be placed.",
                    "This records the explicit manual disposition only.",
                    "Canonical Groups created: no",
                ),
            ):
                return
        elif choice == "random":
            random_seed = prompt_exact_text(
                "Distribute Missing Students Randomly",
                "Seed",
                help_text=(
                    "Enter a nonblank reproducibility seed without surrounding "
                    "whitespace. Only currently unresolved missing-signal students "
                    "will be placed."
                ),
            )
            assert random_seed is not None
            _show_random_preview(inspection, seed=random_seed)
            if not confirm_write(
                "Distribute Missing Students Randomly",
                "DISTRIBUTE",
                (
                    f"GroupPlan: {inspection.detail.plan.group_plan_id}",
                    f"Affected students: {len(inspection.missing_student_ids)}",
                    f"Seed: {random_seed}",
                    "Existing represented-student placements will not move.",
                    "No canonical Groups or Memberships will be created.",
                ),
            ):
                return
        else:
            if not confirm_write(
                "Leave Missing Students Unassigned",
                "LEAVE",
                (
                    f"GroupPlan: {inspection.detail.plan.group_plan_id}",
                    f"Missing IDs: {', '.join(inspection.missing_student_ids)}",
                    "These students remain rostered and visibly unresolved.",
                    "No signal band will be inferred or synthesized.",
                    "Canonical Groups created: no",
                ),
            ):
                return

        result = set_missing_signal_disposition(
            SetMissingSignalDispositionRequest(
                class_id=inspection.detail.summary.class_id,
                activity_id=inspection.detail.summary.activity_id,
                group_plan_id=inspection.detail.summary.group_plan_id,
                disposition=choice,
                random_seed=random_seed,
                expected_snapshot_revision=inspection.detail.summary.snapshot_revision,
                actor=state.require_actor(),
            )
        )
        show_result("Missing-Signal Decision Result", _result_lines(result))
    except CancelMenuAction:
        return
