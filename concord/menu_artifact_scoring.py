"""Teacher-facing routine scoring from one already-selected Artifact."""

from __future__ import annotations

import json
from collections.abc import Callable

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    QuitPDS,
    ReturnToMainMenu,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import (
    confirm_write,
    handle_write_error,
    prompt_text,
    select_many,
    select_one,
    show_result,
)
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.models import (
    Criterion,
    ParticipantReference,
    ScoreTargetReference,
    ScoringScale,
    ScoringScaleLevel,
    SubjectReference,
)
from concord.workflows.activity import show_activity
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringContext,
    inspect_artifact_routine_scoring,
)
from concord.workflows.artifact_routine_scoring_execution import (
    record_prepared_routine_score,
)
from concord.workflows.artifact_routine_scoring_preparation import (
    ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
    RoutineScorePreparationRequest,
    RoutineScorePreview,
    prepare_routine_score_preview,
    routine_subject_context_options,
)
from concord.workflows.artifact_routine_scoring_selection import (
    RoutineScoreTargetCandidate,
    routine_criteria_for_target,
    routine_scale_options,
    routine_target_options,
)
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.models import ActivitySummary
from concord.workflows.participants import participant_display_label

SelectedWorkOpener = Callable[[ActivitySummary, str], bool]


def _current_activity(activity: ActivitySummary) -> ActivitySummary:
    return show_activity(activity.class_id, activity.activity_id).summary


def _launch_advanced_score(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Lazily preserve the existing Advanced Score path without an import cycle."""
    from concord.menu_scoring import launch_score_menu

    launch_score_menu(activity, state)


def _student_label(class_id: str, student_id: str) -> str:
    root = resolve_read_workspace_root()
    if root is None:
        return student_id
    reference = ParticipantReference(
        participant_kind="core_student",
        participant_id=student_id,
        owning_system="core",
    )
    return participant_display_label(root, class_id, reference) or student_id


def _group_label(context: ArtifactRoutineScoringContext, group_id: str) -> str:
    group = next(
        (item for item in context.current_groups if item.group_id == group_id),
        None,
    )
    return group_id if group is None else group.label


def _session_label(context: ArtifactRoutineScoringContext, session_id: str) -> str:
    session = next(
        (item for item in context.current_sessions if item.session_id == session_id),
        None,
    )
    if session is None:
        return session_id
    label = session.label or session.session_id
    return f"{session.sequence}. {label}"


def _target_label(
    activity: ActivitySummary,
    context: ArtifactRoutineScoringContext,
    reference: ScoreTargetReference,
) -> str:
    kind = reference.target_kind
    if kind == "core_student":
        return f"{_student_label(context.class_id, reference.target_id)} — student"
    if kind == "concord_group":
        return f"{_group_label(context, reference.target_id)} — group"
    if kind == "concord_session":
        return f"{_session_label(context, reference.target_id)} — session"
    if kind == "concord_artifact_instance":
        if reference.target_id == context.artifact.artifact_instance_id:
            return "This Artifact"
        return f"Artifact {reference.target_id}"
    if kind == "concord_activity":
        return f"{activity.title} — Activity"
    return f"{reference.target_id} — {kind.replace('_', ' ')}"


def _subject_label(
    activity: ActivitySummary,
    context: ArtifactRoutineScoringContext,
    reference: SubjectReference,
) -> str:
    kind = reference.subject_kind
    if kind == "core_student":
        return f"{_student_label(context.class_id, reference.subject_id)} — student"
    if kind == "concord_group":
        return f"{_group_label(context, reference.subject_id)} — group"
    if kind == "concord_session":
        return f"{_session_label(context, reference.subject_id)} — session"
    if kind == "concord_activity":
        return f"{activity.title} — Activity"
    if kind == "concord_artifact_instance":
        if reference.subject_id == context.artifact.artifact_instance_id:
            return "This Artifact"
        return f"Artifact {reference.subject_id}"
    return f"{reference.subject_id} — external record"


def _choose_target(
    activity: ActivitySummary,
    context: ArtifactRoutineScoringContext,
) -> ScoreTargetReference | None:
    options = routine_target_options(context)
    items: tuple[RoutineScoreTargetCandidate | None, ...] = (
        *options.candidates,
        None,
    )
    labels = tuple(
        _target_label(activity, context, item.target_reference)
        for item in options.candidates
    ) + ("Other supported target... — Advanced Score recording",)
    selected = select_one(
        "Choose Score Target",
        items,
        labels,
        help_text=(
            "Choose exactly whom or what this Score applies to. Candidate order "
            "does not select a target. Use Advanced Score recording for other "
            "supported target identities."
        ),
    )
    return None if selected is None else selected.target_reference


def _choose_criterion(
    context: ArtifactRoutineScoringContext,
    target: ScoreTargetReference,
) -> Criterion:
    criteria = routine_criteria_for_target(context, target)
    return select_one(
        "Choose Criterion",
        criteria,
        tuple(f"{item.label} [{item.criterion_kind}]" for item in criteria),
        help_text=(
            "Choose one explicit Criterion compatible with the selected target. "
            "Concord does not infer a Criterion from the Artifact."
        ),
    )


def _choose_scale(
    context: ArtifactRoutineScoringContext,
    target: ScoreTargetReference,
    criterion_id: str,
) -> ScoringScale:
    options = routine_scale_options(context, target, criterion_id)
    default_id = (
        None
        if options.default_scale is None
        else options.default_scale.scoring_scale_id
    )
    ordered = tuple(
        sorted(
            options.scales,
            key=lambda item: (
                0 if item.scoring_scale_id == default_id else 1,
                item.name.casefold(),
                item.scoring_scale_id,
            ),
        )
    )
    labels = tuple(
        item.name + (" [default]" if item.scoring_scale_id == default_id else "")
        for item in ordered
    )
    default_note = {
        "valid": "The configured current default is marked [default].",
        "not_configured": "This Criterion has no configured default Scale.",
        "missing_or_historical": (
            "The configured default is missing or historical; choose a current "
            "active Scale explicitly."
        ),
        "not_active": (
            "The configured default is not active; choose a current active "
            "Scale explicitly."
        ),
    }[options.default_scale_status]
    return select_one(
        "Choose Scoring Scale",
        ordered,
        labels,
        help_text=(
            f"{default_note} No Score value is selected by the Scale default."
        ),
    )


def _choose_level(scale: ScoringScale) -> ScoringScaleLevel:
    return select_one(
        "Choose Exact Score Value",
        scale.levels,
        tuple(
            f"{json.dumps(item.value)} — {item.label}: {item.meaning}"
            for item in scale.levels
        ),
        help_text=(
            "Choose one exact native Scale value. Concord does not translate "
            "Review readiness into a Score value."
        ),
    )


def _choose_session(
    context: ArtifactRoutineScoringContext,
) -> str | None:
    if not context.current_sessions:
        return None
    items = (None, *context.current_sessions)
    labels = ["No separate Score Session context"]
    for session in context.current_sessions:
        label = _session_label(context, session.session_id)
        if session.session_id == context.artifact.session_id:
            label += " [Artifact context]"
        labels.append(label)
    selected = select_one(
        "Score Session Context",
        items,
        tuple(labels),
        help_text=(
            "Choose a Session explicitly or choose no separate Score Session. "
            "The Artifact's Session is shown only as context and is not guessed."
        ),
    )
    return None if selected is None else selected.session_id


def _choose_subject_context(
    activity: ActivitySummary,
    context: ArtifactRoutineScoringContext,
    target: ScoreTargetReference,
    criterion_id: str,
) -> tuple[SubjectReference, ...]:
    options = routine_subject_context_options(context, target, criterion_id)
    if not options:
        return ()
    mode = select_one(
        "Evidence Subject Context",
        ("none", "select"),
        (
            "No Subject context",
            "Choose from current confirmed Artifact Subjects",
        ),
        help_text=(
            "Subject context is optional and explicit. It is never inferred from "
            "Artifact Authors or from the selected Score target."
        ),
    )
    if mode == "none":
        return ()
    return select_many(
        "Choose Evidence Subjects",
        options,
        tuple(_subject_label(activity, context, item) for item in options),
        help_text=(
            "Choose only current confirmed Artifact Subjects that apply to this "
            "evidence use."
        ),
    )


def _choose_relevance() -> str:
    mode = select_one(
        "Evidence Relevance",
        ("default", "edit"),
        (
            f"Use routine default: {ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION}",
            "Edit relevance description",
        ),
        help_text=(
            "The routine default is visible and deterministic. Edit it when the "
            "exact evidence relationship needs a different description."
        ),
    )
    if mode == "default":
        return ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION
    value = prompt_text(
        "Evidence Relevance",
        "Relevance description",
        help_text="Explain how this reviewed Artifact supports this exact Score.",
        default=ROUTINE_ARTIFACT_RELEVANCE_DESCRIPTION,
    )
    assert value is not None
    return value


def _session_preview_label(
    context: ArtifactRoutineScoringContext,
    session_id: str | None,
) -> str:
    return "None" if session_id is None else _session_label(context, session_id)


def _subject_preview_label(
    activity: ActivitySummary,
    context: ArtifactRoutineScoringContext,
    subjects: tuple[SubjectReference, ...],
) -> str:
    if not subjects:
        return "None"
    return ", ".join(_subject_label(activity, context, item) for item in subjects)


def _preview_lines(
    activity: ActivitySummary,
    context: ArtifactRoutineScoringContext,
    preview: RoutineScorePreview,
) -> tuple[str, ...]:
    lines = [
        "Artifact: this reviewed Artifact",
        f"Target: {_target_label(activity, context, preview.target_reference)}",
        f"Criterion: {preview.criterion_label}",
        f"Scale: {preview.scoring_scale_name}",
        (
            "Value: "
            f"{json.dumps(preview.value)} — {preview.selected_level.label}"
        ),
        f"Disposition: {preview.disposition}",
        f"Basis: {preview.basis}",
        "Evidence: this reviewed Artifact",
        (
            "Subject context: "
            + _subject_preview_label(
                activity,
                context,
                preview.evidence.subject_context,
            )
        ),
        f"Session: {_session_preview_label(context, preview.session_id)}",
        f"Moderation: {preview.evidence.moderation_requirement}",
        f"Relevance: {preview.evidence.relevance_description}",
    ]
    if preview.target_reference.target_kind == "concord_group":
        lines.extend(
            (
                "GROUP SCORE WARNING:",
                "This Score applies only to the Group.",
                "It creates no individual student Scores.",
            )
        )
    return tuple(lines)


def _record_selected_artifact_score(
    activity: ActivitySummary,
    artifact_instance_id: str,
    state: MenuSessionContext,
) -> bool:
    current = _current_activity(activity)
    context = inspect_artifact_routine_scoring(
        current.class_id,
        current.activity_id,
        artifact_instance_id,
    )
    if not context.eligibility.routine_scoring_eligible:
        reasons = context.eligibility.exception_reasons or (
            "This Artifact is not currently eligible for routine scoring.",
        )
        show_result(
            "Score this work",
            (
                "Routine scoring is not available for this reviewed Artifact.",
                *reasons,
                "Use Review, Moderation, or Advanced Score recording as needed.",
            ),
        )
        return False

    target = _choose_target(current, context)
    if target is None:
        _launch_advanced_score(current, state)
        return False
    criterion = _choose_criterion(context, target)
    scale = _choose_scale(context, target, criterion.criterion_id)
    level = _choose_level(scale)
    session_id = _choose_session(context)
    subjects = _choose_subject_context(
        current,
        context,
        target,
        criterion.criterion_id,
    )
    relevance = _choose_relevance()
    preview = prepare_routine_score_preview(
        context,
        RoutineScorePreparationRequest(
            target_reference=target,
            criterion_id=criterion.criterion_id,
            scoring_scale_id=scale.scoring_scale_id,
            value=level.value,
            session_id=session_id,
            subject_context=subjects,
            relevance_description=relevance,
        ),
    )
    if preview.existing_current_score_ids:
        show_result(
            "Score this work",
            (
                "A current Score already exists for this target and Criterion.",
                "Routine first-entry scoring will not create a parallel Score.",
                "Use Advanced Score recording to inspect or revise current Scores.",
            ),
        )
        return False
    if not confirm_write(
        "Score this work",
        "SCORE",
        _preview_lines(current, context, preview),
    ):
        return False

    result = record_prepared_routine_score(
        preview,
        actor=state.require_actor(),
    )
    show_result(
        "Score Recorded",
        (
            "The explicit Score and native Artifact Evidence Link were recorded.",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )
    return True


def launch_selected_artifact_scoring(
    activity: ActivitySummary,
    artifact_instance_id: str,
    state: MenuSessionContext,
    *,
    open_selected_work: SelectedWorkOpener,
) -> None:
    """Score one already-selected reviewed Artifact without selecting it again."""
    while True:
        current = _current_activity(activity)
        context = inspect_artifact_routine_scoring(
            current.class_id,
            current.activity_id,
            artifact_instance_id,
        )
        clear_screen()
        print_menu_header("Score this work")
        print(f"Activity: {current.title}")
        print("Artifact: selected reviewed work")
        review = context.current_review
        review_label = "none" if review is None else review.scoring_readiness
        print(f"Review: {review_label.replace('_', ' ')}")
        print()
        print("1. Score this work")
        print("O. Open returned work")
        print("A. Advanced Score recording")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Score this work Help",
                    (
                        "Routine scoring uses this exact selected reviewed Artifact.",
                        "Target, Criterion, Scale value, Subject context, and Session "
                        "remain explicit teacher choices.",
                        "Opening returned work changes no workflow state.",
                        "Advanced Score recording preserves external, multiple-"
                        "evidence, mixed-basis, and revision workflows.",
                    ),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif raw == "1":
                if _record_selected_artifact_score(
                    current,
                    artifact_instance_id,
                    state,
                ):
                    return
            elif raw.casefold() == "o":
                refreshed = _current_activity(current)
                open_selected_work(refreshed, artifact_instance_id)
            elif raw.casefold() == "a":
                _launch_advanced_score(current, state)
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            continue
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            handle_write_error(
                error,
                reload=lambda: _current_activity(current),
                error_title="Score this work Error",
            )


__all__ = ["launch_selected_artifact_scoring"]
