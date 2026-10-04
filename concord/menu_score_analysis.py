"""Teacher-facing read-only Activity Score analysis navigation."""

from __future__ import annotations

import json
from collections.abc import Callable

from pds_core.classes import load_class_roster
from pds_core.rosters import RosterError, student_display_name, student_lookup

from concord.menu_context import CancelMenuAction
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import load_menu_standards_library, select_one, show_result
from concord.menu_score_analysis_export import launch_score_report_export
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import ScoreTargetReference
from concord.workflows import (
    ActivityScoreAnalysis,
    ActivitySummary,
    CriterionScaleTargetAnalysis,
    ScoreHistoryAnalysis,
    ScoreHistoryLineage,
    StandardScoreAnalysis,
    TargetScoreDetail,
    activity_score_analysis_from_context,
    score_history_analysis_from_context,
    target_score_detail_from_context,
)
from concord.workflows.activity import _load_activity_context
from concord.workflows.activity_read import ActivityReadContext

_TARGET_KIND_LABELS = {
    "core_student": "Students",
    "concord_group": "Groups",
    "concord_artifact_instance": "Artifacts",
    "concord_session": "Sessions",
    "concord_activity": "Activity",
}


def _student_label_resolver(
    context: ActivityReadContext,
) -> Callable[[ScoreTargetReference], str | None]:
    try:
        roster = load_class_roster(context.root, context.work.class_id)
    except RosterError:
        return lambda _target: None
    students = student_lookup(roster)

    def resolve(target: ScoreTargetReference) -> str | None:
        if target.target_kind != "core_student":
            return None
        student = students.get(target.target_id)
        return None if student is None else student_display_name(student)

    return resolve


def _native_target_label(
    context: ActivityReadContext,
    target: ScoreTargetReference,
) -> str | None:
    if target.target_kind == "concord_group":
        group = next(
            (
                item
                for item in context.graph.groups
                if item.group_id == target.target_id
            ),
            None,
        )
        return None if group is None else group.label
    if target.target_kind == "concord_session":
        session = next(
            (
                item
                for item in context.graph.sessions
                if item.session_id == target.target_id
            ),
            None,
        )
        if session is None:
            return None
        return session.label or f"Session {session.sequence}"
    if target.target_kind == "concord_activity":
        if target.target_id == context.activity.activity_id:
            return context.activity.title
    return None


def _target_label(
    context: ActivityReadContext,
    target: ScoreTargetReference,
    resolver: Callable[[ScoreTargetReference], str | None],
) -> str:
    resolved = resolver(target)
    if resolved is not None and resolved.strip():
        return resolved.strip()
    native = _native_target_label(context, target)
    return target.target_id if native is None else native


def _result_label(
    disposition: str,
    value: object,
    value_label: str | None,
) -> str:
    if disposition != "scored":
        return disposition.replace("_", " ")
    rendered = json.dumps(value)
    return rendered if value_label is None else f"{rendered} — {value_label}"


def _slice_lines(item: CriterionScaleTargetAnalysis) -> tuple[str, ...]:
    lines = [
        (
            f"{_TARGET_KIND_LABELS.get(item.target_kind, item.target_kind)} / "
            f"{item.scoring_scale_name} "
            f"(rev {item.scoring_scale_revision})"
        ),
        f"  Current judgments: {item.current_judgment_count}",
        f"  Scored: {item.scored_count}",
        f"  Non-score dispositions: {item.non_score_count}",
    ]
    if item.value_distributions:
        lines.append("  Values:")
        lines.extend(
            (
                f"    {json.dumps(value.value)} — {value.label}: "
                f"{value.count}/{value.denominator} "
                f"({value.percentage}%)"
            )
            for value in item.value_distributions
        )
    if item.disposition_distributions:
        lines.append("  Dispositions:")
        lines.extend(
            (
                f"    {value.disposition.replace('_', ' ')}: "
                f"{value.count}/{value.denominator} "
                f"({value.percentage}%)"
            )
            for value in item.disposition_distributions
        )
    return tuple(lines)


def _criterion_view(analysis: ActivityScoreAnalysis) -> None:
    if not analysis.criterion_analyses:
        show_result(
            "Criterion Analysis",
            ("No current Score records are available for Criterion analysis.",),
        )
        return
    selected = select_one(
        "Criterion Analysis",
        analysis.criterion_analyses,
        tuple(
            (
                f"{item.criterion_label} ({item.criterion_id}) — "
                f"{item.current_judgment_count} current judgment(s)"
            )
            for item in analysis.criterion_analyses
        ),
        help_text=(
            "Choose one represented Criterion. Counts include only current "
            "Score lineage heads."
        ),
    )
    lines = [
        f"Criterion: {selected.criterion_label}",
        f"Kind: {selected.criterion_kind}",
        f"Standard: {selected.standard_id or '-'}",
        f"Current recorded judgments: {selected.current_judgment_count}",
    ]
    for item in selected.slices:
        lines.append("")
        lines.extend(_slice_lines(item))
    show_result("Criterion Analysis", tuple(lines))


def _target_view(
    context: ActivityReadContext,
    analysis: ActivityScoreAnalysis,
    resolver: Callable[[ScoreTargetReference], str | None],
) -> None:
    targets = tuple(
        dict.fromkeys(item.target_reference for item in analysis.current_scores)
    )
    if not targets:
        show_result(
            "Target Detail",
            ("No current Score targets are available for this Activity.",),
        )
        return
    selected = select_one(
        "Target Detail",
        targets,
        tuple(
            (
                f"{_TARGET_KIND_LABELS.get(item.target_kind, item.target_kind)}: "
                f"{_target_label(context, item, resolver)}"
            )
            for item in targets
        ),
        help_text=(
            "Choose one exact current Score target. Group, Artifact, Session, "
            "Activity, and Student targets remain distinct."
        ),
    )
    detail = target_score_detail_from_context(
        context,
        selected,
        target_label_resolver=resolver,
    )
    _show_target_detail(detail)


def _show_target_detail(detail: TargetScoreDetail) -> None:
    lines = [
        f"Target: {detail.target_label}",
        f"Target kind: {detail.target_reference.target_kind}",
        f"Current Score records: {detail.current_score_count}",
        f"Scope: {detail.sharing_scope}",
        "Teacher-local descriptive view; not automatically share-safe.",
    ]
    for item in detail.results:
        lines.extend(
            (
                "",
                f"Criterion: {item.criterion_label}",
                (
                    f"Scale: {item.scoring_scale_name} "
                    f"(rev {item.scoring_scale_revision})"
                ),
                (
                    "Current result: "
                    + _result_label(
                        item.disposition,
                        item.value,
                        item.value_label,
                    )
                ),
            )
        )
    show_result("Target Detail", tuple(lines))


def _standard_view(analysis: ActivityScoreAnalysis) -> None:
    if not analysis.standard_analyses:
        show_result(
            "Standards / Criterion View",
            ("No current standard-backed Criteria are represented.",),
        )
        return
    selected = select_one(
        "Standards / Criterion View",
        analysis.standard_analyses,
        tuple(_standard_choice_label(item) for item in analysis.standard_analyses),
        help_text=(
            "Standards group existing standard-backed Criteria only. "
            "No proficiency or mastery value is calculated."
        ),
    )
    lines = [
        f"Standard: {selected.standard_label}",
        f"Durable ID: {selected.standard_id}",
    ]
    if selected.standard_short_name is not None:
        lines.append(f"Name: {selected.standard_short_name}")
    lines.extend(
        (
            "",
            "Concord does not convert these distributions into "
            "standards proficiency.",
        )
    )
    for criterion in selected.criteria:
        lines.extend(
            (
                "",
                f"Criterion: {criterion.criterion_label}",
                f"Current judgments: {criterion.current_judgment_count}",
            )
        )
        for item in criterion.slices:
            lines.extend(_slice_lines(item))
    show_result("Standards / Criterion View", tuple(lines))


def _standard_choice_label(item: StandardScoreAnalysis) -> str:
    if item.standard_short_name is None:
        return item.standard_label
    return f"{item.standard_label} — {item.standard_short_name}"


def _history_view(
    context: ActivityReadContext,
    resolver: Callable[[ScoreTargetReference], str | None],
) -> None:
    history = score_history_analysis_from_context(
        context,
        target_label_resolver=resolver,
    )
    if not history.lineages:
        show_result("Score History", ("No Score history exists for this Activity.",))
        return
    selected = select_one(
        "Score History",
        history.lineages,
        tuple(_history_choice_label(item) for item in history.lineages),
        help_text=(
            "History is explicit and separate from current analysis. "
            "Superseded revisions are never additional current judgments."
        ),
    )
    _show_history_lineage(history, selected.root_score_record_id)


def _history_choice_label(item: ScoreHistoryLineage) -> str:
    first = item.revisions[0]
    return (
        f"{first.target_label} — {first.criterion_label} — "
        f"{item.revision_count} revision(s)"
    )


def _show_history_lineage(
    history: ScoreHistoryAnalysis,
    root_score_record_id: str,
) -> None:
    lineage = next(
        item
        for item in history.lineages
        if item.root_score_record_id == root_score_record_id
    )
    first = lineage.revisions[0]
    lines = [
        f"Target: {first.target_label}",
        f"Criterion: {first.criterion_label}",
        f"Revisions: {lineage.revision_count}",
        f"Scope: {history.sharing_scope}",
    ]
    for item in lineage.revisions:
        state = "current" if item.is_current else "historical"
        lines.extend(
            (
                "",
                f"Revision {item.revision_number}: {state}",
                f"Score Record: {item.score_record_id}",
                f"Scored at: {item.scored_at}",
                (
                    f"Scale: {item.scoring_scale_name} "
                    f"(rev {item.scoring_scale_revision})"
                ),
                (
                    "Result: "
                    + _result_label(
                        item.disposition,
                        item.value,
                        item.value_label,
                    )
                ),
            )
        )
        if item.correction_reason is not None:
            lines.append(f"Revision reason: {item.correction_reason}")
    show_result("Score History", tuple(lines))


def _print_overview(analysis: ActivityScoreAnalysis) -> None:
    print(f"Activity: {analysis.activity_title}")
    print(f"Current Score records: {analysis.current_score_count}")
    print(f"Score basis: {analysis.score_basis}")
    print()
    print("By target kind:")
    if analysis.target_kind_counts:
        for item in analysis.target_kind_counts:
            label = _TARGET_KIND_LABELS.get(item.target_kind, item.target_kind)
            print(f"  {label}: {item.score_count}")
    else:
        print("  No current Score records.")
    print()
    print(f"Criteria represented: {analysis.represented_criterion_count}")
    print(
        "Scoring Scales represented: "
        f"{analysis.represented_scoring_scale_count}"
    )
    print()
    print(
        "Descriptive only: no Grade, proficiency/mastery, or required/missing "
        "Score inference."
    )
    print(
        "Current analysis uses current Score lineage heads; superseded "
        "revisions are available separately through Score History."
    )


def launch_score_analysis_menu(activity: ActivitySummary) -> None:
    """Review one exact Activity Score snapshot through read-only drill-downs."""
    try:
        context = _load_activity_context(
            activity.class_id,
            activity.activity_id,
        )
        resolver = _student_label_resolver(context)
        standards_library = load_menu_standards_library()
        analysis = activity_score_analysis_from_context(
            context,
            standards_library=standards_library,
        )
    except Exception as error:
        show_result("Score Analysis Error", (str(error),))
        return

    while True:
        clear_screen()
        print_menu_header("Review Score Analysis")
        _print_overview(analysis)
        print()
        print("1. Criterion Analysis")
        print("2. Target Detail")
        print("3. Standards / Criterion View")
        print("4. Score History")
        print("5. Export Report")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Score Analysis Help",
                (
                    "This view reports existing Concord Score records.",
                    "It calculates no Grade or proficiency/mastery.",
                    "It infers no required or missing Score cells.",
                    "Viewing analysis writes no canonical state.",
                ),
            )
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            try:
                _criterion_view(analysis)
            except CancelMenuAction:
                continue
        elif choice == "2":
            try:
                _target_view(context, analysis, resolver)
            except CancelMenuAction:
                continue
        elif choice == "3":
            try:
                _standard_view(analysis)
            except CancelMenuAction:
                continue
        elif choice == "4":
            try:
                _history_view(context, resolver)
            except CancelMenuAction:
                continue
        elif choice == "5":
            try:
                launch_score_report_export(
                    context,
                    analysis,
                    target_labeler=lambda target: _target_label(
                        context,
                        target,
                        resolver,
                    ),
                    target_label_resolver=resolver,
                    standards_library=standards_library,
                )
            except CancelMenuAction:
                continue
        else:
            print(navigation_hint_with_help())
            pause_for_user()


__all__ = ["launch_score_analysis_menu"]
