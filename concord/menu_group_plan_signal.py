"""Teacher-facing creation of deterministic signal-backed GroupPlans."""

from __future__ import annotations

from pds_core.workspace import resolve_workspace_root

from concord.group_plan_signal import (
    SignalGroupPlanProposal,
    generate_mixed_signal_group_plan_proposal,
    generate_similar_signal_group_plan_proposal,
)
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_prompts import (
    confirm_write,
    handle_write_error,
    prompt_positive_int,
    prompt_text,
    select_one,
    show_result,
    slug_identifier,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
)
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowConflictError,
    CreateSignalGroupPlanRequest,
    GroupingSignalDimensionSelection,
    SignalGroupPlanCreationResult,
    create_signal_group_plan,
    list_grouping_signals,
    load_required_roster,
    select_grouping_signal_dimension,
    show_activity,
)

_SIGNAL_LABELS = {
    "similar_signal": "Similar-signal",
    "mixed_signal": "Mixed-signal",
}


def _latest(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _handle_error(activity: ActivitySummary, error: Exception) -> None:
    handle_write_error(
        error,
        reload=lambda: _latest(activity),
        error_title="GroupPlan Error",
    )


def _roster_student_ids(class_id: str) -> tuple[str, ...]:
    root = resolve_workspace_root()
    roster = load_required_roster(root, class_id)
    return tuple(sorted(student.student_id for student in roster.students))


def _select_signal_dimension(
    activity: ActivitySummary,
) -> tuple[GroupingSignalDimensionSelection, tuple[str, ...]]:
    summaries = list_grouping_signals(activity.class_id)
    if not summaries:
        raise ValueError(
            "No grouping signals are available for this class. Import or create "
            "a Core grouping signal before creating a signal-backed GroupPlan."
        )
    signal = select_one(
        "Choose a Grouping Signal",
        summaries,
        tuple(
            (
                f"{item.signal_set_id} - {item.source_kind}; "
                f"dimensions: {len(item.dimension_ids)}"
            )
            for item in summaries
        ),
        help_text=(
            "Choose one exact immutable Core signal snapshot. Concord never "
            "chooses a latest or current signal automatically."
        ),
    )
    dimension_id = select_one(
        "Choose a Signal Dimension",
        signal.dimension_ids,
        tuple(f"{item}" for item in signal.dimension_ids),
        help_text=(
            "Choose the exact ordinal-band dimension for this plan. Concord never "
            "combines dimensions or selects the first dimension automatically."
        ),
    )

    before = _roster_student_ids(activity.class_id)
    selection = select_grouping_signal_dimension(
        activity.class_id,
        signal.signal_set_id,
        dimension_id,
    )
    after = _roster_student_ids(activity.class_id)
    if before != after:
        raise ConcordWorkflowConflictError(
            "Core roster changed while preparing the signal GroupPlan preview; "
            "reload and retry."
        )
    return selection, after


def _show_signal_diagnostics(
    selection: GroupingSignalDimensionSelection,
) -> None:
    diagnostics = selection.dimension_diagnostics
    clear_screen()
    print_menu_header("Signal Planning Diagnostics")
    print(f"Signal set: {selection.signal_set_id}")
    print(f"Core signal digest: {selection.digest}")
    print(f"Dimension: {selection.dimension_id}")
    print(f"Roster students: {diagnostics.roster_student_count}")
    print(f"Matched students: {diagnostics.matched_student_count}")
    print(f"Missing students: {diagnostics.missing_student_count}")
    print()
    print("Band distribution:")
    for band, count in diagnostics.band_counts:
        print(f"Band {band}: {count}")
    print()
    print("Missing signal coverage remains unresolved; it is never treated as a band.")
    print("Ordinal bands are contextual planning inputs, not learner labels.")
    print()
    pause_for_user()


def _choose_target(
    strategy: str,
    roster_count: int,
) -> tuple[int | None, int | None, str]:
    label = _SIGNAL_LABELS[strategy]
    target_kind = select_one(
        f"{label} Group Target",
        ("size", "count"),
        ("Target group size", "Target group count"),
        help_text=(
            "The target is resolved against the full current Core roster. "
            "Students missing the selected signal dimension remain unresolved."
        ),
    )
    if target_kind == "size":
        size = prompt_positive_int(
            f"Create {label} GroupPlan",
            "Target group size",
            help_text=(
                "Concord will create ceil(full roster size / target size) planned "
                "groups. Missing signal coverage does not reduce that group count."
            ),
            default=4,
        )
        return size, None, f"Target group size: {size}"

    default_count = min(4, roster_count)
    count = prompt_positive_int(
        f"Create {label} GroupPlan",
        "Target group count",
        help_text=(
            "Concord will create exactly this many planned groups. The count cannot "
            "exceed the full current Core roster size; empty planned groups may "
            "remain when signal coverage is partial."
        ),
        default=default_count,
    )
    return None, count, f"Target group count: {count}"


def _signal_bands(
    selection: GroupingSignalDimensionSelection,
) -> dict[str, int]:
    return {
        entry.student_id: entry.band
        for entry in selection.inspection.stored.signal.student_bands
        if entry.dimension_id == selection.dimension_id
    }


def _proposal(
    strategy: str,
    roster_student_ids: tuple[str, ...],
    selection: GroupingSignalDimensionSelection,
    *,
    target_group_size: int | None,
    target_group_count: int | None,
) -> SignalGroupPlanProposal:
    bands = _signal_bands(selection)
    if strategy == "similar_signal":
        return generate_similar_signal_group_plan_proposal(
            roster_student_ids,
            bands,
            target_group_size=target_group_size,
            target_group_count=target_group_count,
        )
    return generate_mixed_signal_group_plan_proposal(
        roster_student_ids,
        bands,
        target_group_size=target_group_size,
        target_group_count=target_group_count,
    )


def _show_preview(
    strategy: str,
    selection: GroupingSignalDimensionSelection,
    proposal: SignalGroupPlanProposal,
    target_line: str,
) -> None:
    label = _SIGNAL_LABELS[strategy]
    clear_screen()
    print_menu_header(f"{label} GroupPlan Preview")
    print(f"Signal set: {selection.signal_set_id}")
    print(f"Core signal digest: {selection.digest}")
    print(f"Dimension: {selection.dimension_id}")
    print(target_line)
    print(f"Planned groups: {proposal.group_count}")
    print(f"Assigned students: {proposal.assigned_student_count}")
    print(f"Unresolved students: {proposal.unresolved_student_count}")
    print(f"Group sizes: {','.join(str(size) for size in proposal.group_sizes)}")
    print()
    print("Planned memberships:")
    for group in proposal.proposed_groups:
        students = ", ".join(group.student_ids) or "-"
        print(f"{group.label} ({group.planned_group_key}): {students}")
    if proposal.unresolved_student_ids:
        print()
        print(f"Unresolved IDs: {', '.join(proposal.unresolved_student_ids)}")
    print()
    print("Group numbers do not represent academic rank or a permanent learner label.")
    print("No canonical Groups or Memberships have been created.")
    print()
    pause_for_user()


def _result_lines(
    result: SignalGroupPlanCreationResult,
    target_line: str,
) -> tuple[str, ...]:
    label = _SIGNAL_LABELS[result.strategy]
    mutation = result.mutation
    return (
        f"{label} GroupPlan created.",
        f"GroupPlan: {mutation.group_plan_id}",
        f"Strategy: {result.strategy}",
        f"Status: {mutation.status}",
        f"Signal set: {result.signal_set_id}",
        f"Core signal digest: {result.signal_set_digest}",
        f"Dimension: {result.dimension_id}",
        target_line,
        f"Planned groups: {result.group_count}",
        f"Assigned students: {result.assigned_student_count}",
        f"Unresolved students: {result.unresolved_student_count}",
        f"Group sizes: {','.join(str(size) for size in result.group_sizes)}",
        f"Snapshot: {mutation.commit.snapshot_revision}",
        "Canonical Groups created: no",
    )


def create_signal_group_plan_from_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
    strategy: str,
) -> None:
    """Preview and persist one exact signal-backed planning proposal."""

    if strategy not in _SIGNAL_LABELS:
        raise ValueError(f"Unsupported signal GroupPlan strategy: {strategy}")
    try:
        current = _latest(activity)
        label = _SIGNAL_LABELS[strategy]
        plan_id = prompt_text(
            f"Create {label} GroupPlan",
            "GroupPlan ID",
            help_text="Use a durable identifier for this planning proposal.",
            default=slug_identifier(
                f"{current.activity_id}-{strategy.replace('_signal', '')}",
                "group-plan",
            ),
        )
        assert plan_id is not None
        selection, roster_student_ids = _select_signal_dimension(current)
        _show_signal_diagnostics(selection)

        target_size, target_count, target_line = _choose_target(
            strategy,
            len(roster_student_ids),
        )
        proposal = _proposal(
            strategy,
            roster_student_ids,
            selection,
            target_group_size=target_size,
            target_group_count=target_count,
        )
        _show_preview(strategy, selection, proposal, target_line)

        if not confirm_write(
            f"Create {label} GroupPlan",
            "CREATE",
            (
                f"Activity: {current.title}",
                f"GroupPlan: {plan_id}",
                f"Strategy: {strategy}",
                f"Signal set: {selection.signal_set_id}",
                f"Core signal digest: {selection.digest}",
                f"Dimension: {selection.dimension_id}",
                target_line,
                f"Planned groups: {proposal.group_count}",
                f"Assigned students: {proposal.assigned_student_count}",
                f"Unresolved students: {proposal.unresolved_student_count}",
                "The displayed preview must still match the current Core roster.",
                "No canonical Groups or Memberships will be created.",
            ),
        ):
            return

        result = create_signal_group_plan(
            CreateSignalGroupPlanRequest(
                class_id=current.class_id,
                activity_id=current.activity_id,
                group_plan_id=plan_id,
                strategy=strategy,
                signal_set_id=selection.signal_set_id,
                dimension_id=selection.dimension_id,
                expected_snapshot_revision=current.snapshot_revision,
                actor=state.require_actor(),
                target_group_size=target_size,
                target_group_count=target_count,
                expected_roster_student_ids=proposal.roster_student_ids,
                expected_signal_set_digest=selection.digest,
            )
        )
        show_result("GroupPlan Result", _result_lines(result, target_line))
    except CancelMenuAction:
        return
    except Exception as error:
        _handle_error(activity, error)
