"""Guided, low-density classroom Activity creation and resume workflow."""

from __future__ import annotations

import uuid

from pds_core.standards import StandardsLibrary

from concord.menu_actor_action import confirm_actor_write, confirm_prepared_actor_write
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_group import launch_direct_group_menu
from concord.menu_group_plan import launch_group_plan_menu
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    QuitPDS,
    ReturnToMainMenu,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_packet import launch_packet_library_menu
from concord.menu_packet_generation import (
    generate_saved_packet,
    launch_packet_generation_menu,
)
from concord.menu_prompts import (
    choose_class,
    choose_focus_standards,
    choose_standards_profile,
    confirm_write,
    load_menu_standards_library,
    prompt_text,
    select_one,
    show_result,
)
from concord.menu_responsibility import launch_responsibility_menu
from concord.menu_role import launch_role_menu
from concord.menu_scoring import launch_assessment_setup_menu
from concord.menu_session import launch_session_menu
from concord.menu_standards_context import standards_for_activity
from concord.menu_template import launch_template_library_menu
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.storage_errors import ConcordStoragePartialSuccessError
from concord.workflows import (
    ActivitySummary,
    ClassSummary,
    ConcordWorkflowError,
    CopyActivityRequest,
    CreateActivityContextRequest,
    PrepareActivityCopyRequest,
    PreparedActivityCopy,
    WorkflowActor,
    copy_activity,
    create_activity_context,
    list_activities,
    list_available_classes,
    prepare_activity_copy,
    resolve_read_workspace_root,
    show_activity,
)
from concord.workflows.group_plan import show_group_plan
from concord.workflows.guided_activity_setup import (
    GuidedActivitySetup,
    SetupStatus,
    activity_type_label,
    inspect_guided_activity_setup,
    scoring_orientation_label,
    setup_status_label,
)
from concord.workflows.models import UNSET
from concord.workflows.packet import (
    PacketSummary,
    PreparedPacketFromTemplate,
    PreparePacketFromTemplateRequest,
    commit_packet_from_template,
    list_packets,
    prepare_packet_from_template,
)
from concord.workflows.target_assessment_preflight import (
    inspect_target_assessment,
    verify_target_assessment_delta,
)
from concord.workflows.target_cluster_preflight import (
    create_target_six_cluster_draft,
    inspect_target_cluster_preflight,
)
from concord.workflows.target_materials_preflight import (
    TargetMaterialsCheckpoint,
    inspect_target_materials,
    new_target_generations,
)
from concord.workflows.template import get_template, list_templates

_ACTIVITY_CHOICES = (
    "socratic_seminar",
    "laboratory",
    "project",
)
_ACTIVITY_LABELS = (
    "Discussion / seminar",
    "Lab / investigation",
    "Project / collaborative work",
)
_SCORING_CHOICES = (
    "evidence_only",
    "standards_based",
    "mixed",
    "local_criteria_only",
)
_SCORING_LABELS = (
    "Collect evidence without scoring",
    "Use standards-based assessment",
    "Use standards and local criteria",
    "Use local classroom criteria",
)


def _fresh_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _classes() -> tuple[ClassSummary, ...]:
    root = resolve_read_workspace_root()
    if root is None:
        return ()
    return list_available_classes(root)


def _choose_activity_type() -> str:
    return select_one(
        "What are students doing?",
        _ACTIVITY_CHOICES,
        _ACTIVITY_LABELS,
        help_text=(
            "Choose the classroom activity that best matches this work. "
            "Advanced Activity tools remain available for custom extension types."
        ),
    )


def _choose_assessment() -> str:
    return select_one(
        "How will you assess this activity?",
        _SCORING_CHOICES,
        _SCORING_LABELS,
        help_text=(
            "Choose the broad assessment approach. Detailed criteria and scales "
            "can be set up now or later. Concord does not calculate Grades."
        ),
    )


def _standards_for(
    orientation: str,
) -> tuple[StandardsLibrary | None, str | None, tuple[str, ...]]:
    if orientation not in {"standards_based", "mixed"}:
        return None, None, ()
    library = load_menu_standards_library()
    if library is None:
        raise ConcordWorkflowError(
            "Standards are not available in this workspace yet. "
            "Add them through Core, then return to this Activity."
        )
    profile = choose_standards_profile(library)
    standards = choose_focus_standards(library, profile)
    return library, profile.profile_id, standards


def _guided_activity_choice(
    activities: tuple[ActivitySummary, ...],
    *,
    title: str,
) -> ActivitySummary:
    return select_one(
        title,
        activities,
        tuple(
            f"{item.title} — {item.class_id} — {item.status.title()}"
            for item in activities
        ),
        help_text=(
            "Choose the classroom Activity by title and class. Internal IDs stay "
            "hidden unless advanced tools are needed."
        ),
    )


def _create_fresh(state: MenuSessionContext, classes: tuple[ClassSummary, ...]) -> None:
    selected_class = choose_class(classes)
    title = prompt_text(
        "Create Classroom Activity",
        "Activity title",
        help_text="Use the name you would recognize in your lesson plan.",
    )
    assert title is not None
    activity_type = _choose_activity_type()
    orientation = _choose_assessment()
    library, profile_id, focus_ids = _standards_for(orientation)
    description = prompt_text(
        "Create Classroom Activity",
        "Short description",
        help_text="Optional: briefly describe what students will do.",
        optional=True,
    )
    session_label = prompt_text(
        "Create Classroom Activity",
        "First session",
        help_text="Use a classroom-facing label such as Day 1 or Workshop Day.",
        default="Day 1",
    )
    assert session_label is not None
    activity_id = _fresh_id("activity")
    session_id = _fresh_id("session")
    review = (
        f"Class: {selected_class.class_id}",
        f"Activity: {title}",
        f"What students are doing: {activity_type_label(activity_type)}",
        f"Assessment: {scoring_orientation_label(orientation)}",
        f"First session: {session_label}",
    )
    actor = confirm_actor_write(
        "Create Classroom Activity",
        "CREATE",
        review,
        state=state,
        legacy_confirm=confirm_write,
    )
    if actor is None:
        return
    result = create_activity_context(
        CreateActivityContextRequest(
            class_id=selected_class.class_id,
            activity_id=activity_id,
            title=title,
            activity_type=activity_type,
            scoring_orientation=orientation,
            session_id=session_id,
            actor=actor,
            description=description,
            standards_profile_id=profile_id,
            focus_standard_ids=focus_ids,
            session_label=session_label,
        ),
        standards_library=library,
    )
    created = show_activity(selected_class.class_id, result.activity_id).summary
    _offer_after_creation(created, state)


def _cross_class_copy_review(
    source: ActivitySummary,
    target_class: ClassSummary,
    prepared: PreparedActivityCopy,
) -> tuple[str, ...]:
    """Teacher-facing review of the already validated, *create-only* copy.

    Saved definitions can be chosen later; neither selected definitions nor
    any student/returned-paper state are transferred by Activity copy.
    """
    policy = getattr(prepared, "privacy_policy", None)
    classification = getattr(policy, "classification", None)
    privacy = (
        classification.replace("_", " ")
        if isinstance(classification, str)
        else "Activity default"
    )
    title = getattr(prepared, "title", None) or source.title
    first_session = (
        getattr(prepared, "first_session_label", None) or "Planned first session"
    )
    lines = [
        f"Source lesson: {source.title} ({source.class_id})",
        f"Target class: {target_class.class_id}",
        f"New Activity: {title}",
        f"New first Session: {first_session} (planned, fresh)",
        f"What students are doing: {activity_type_label(prepared.activity_type)}",
        f"Assessment: {scoring_orientation_label(prepared.scoring_orientation)}",
        f"Target privacy: {privacy}",
        "WILL CARRY: reviewed lesson settings and exact compatible Core Standards.",
        "WILL CREATE: independent draft Activity and one fresh planned Session.",
        "SAVED DEFINITIONS TO CHOOSE LATER, NOT COPIED:",
        "  Saved Packet / Template; saved rubric, Scale, Criterion Set; "
        "optional roles.",
        "WILL NOT CARRY: source roster or student identities, Groups, Memberships,",
        "  GroupPlans, source Sessions, assigned roles, generated or returned",
        "  Artifacts/PDFs, QR/scan routes, Authors, Subjects, evidence, reviews,",
        "  Scores, Grades, publications, history or source external references.",
        "The new class requires its own target Clusters, packets and rubric setup.",
        "Printing, distribution and returned work are NOT verified by copying.",
    ]
    if getattr(prepared, "standards_profile_id", None) is not None:
        focus = getattr(prepared, "focus_standard_ids", ())
        lines.append(f"Target Focus Standards retained and validated: {len(focus)}")
    for diagnostic in getattr(prepared, "diagnostics", ()):
        lines.append(f"Review notice: {diagnostic.message}")
    return tuple(lines)


def _create_from_activity(
    state: MenuSessionContext,
    classes: tuple[ClassSummary, ...],
) -> None:
    root = resolve_read_workspace_root()
    if root is None:
        raise ConcordWorkflowError("No Concord Activities are available yet.")
    activities = list_activities(workspace_root=root)
    if not activities:
        raise ConcordWorkflowError("No Concord Activities are available to start from.")
    source = _guided_activity_choice(activities, title="Start from another Activity")
    target_class = choose_class(classes)
    target_title = prompt_text(
        "Create Classroom Activity",
        "New Activity title",
        help_text="Name the new independent Activity.",
        default=f"{source.title} - Copy",
    )
    assert target_title is not None
    session_label = prompt_text(
        "Create Classroom Activity",
        "First session",
        help_text="The new Activity starts with one fresh Session.",
        default="Day 1",
    )
    assert session_label is not None
    target_id = _fresh_id("activity")
    session_id = _fresh_id("session")
    library = load_menu_standards_library()
    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id=source.class_id,
            source_activity_id=source.activity_id,
            target_class_id=target_class.class_id,
            target_activity_id=target_id,
            first_session_id=session_id,
            title=target_title,
            description=UNSET,
            first_session_label=session_label,
        ),
        workspace_root=root,
        standards_library=library,
    )
    review = _cross_class_copy_review(source, target_class, prepared)
    actor = confirm_actor_write(
        "Create Classroom Activity",
        "CREATE",
        review,
        state=state,
        legacy_confirm=confirm_write,
    )
    if actor is None:
        return
    result = copy_activity(
        CopyActivityRequest(
            source_class_id=source.class_id,
            source_activity_id=source.activity_id,
            target_class_id=target_class.class_id,
            target_activity_id=target_id,
            first_session_id=session_id,
            actor=actor,
            review_digest=prepared.review_digest,
            title=target_title,
            description=UNSET,
            first_session_label=session_label,
        ),
        workspace_root=root,
        standards_library=library,
    )
    # The create-only copy has returned. If the terminal or readback fails,
    # never start another copy implicitly: inspect this exact target first.
    try:
        created = show_activity(target_class.class_id, result.activity_id).summary
        if (
            created.class_id != target_class.class_id
            or created.activity_id != result.activity_id
        ):
            raise ConcordWorkflowError("Copied target identity did not match.")
    except Exception:
        show_result(
            "Target Copy Outcome Unconfirmed",
            (
                "The copy service returned, but target readback was unconfirmed.",
                f"Target class: {target_class.class_id}",
                f"Requested lesson: {target_title}",
                "Do not copy again. Open Continue Classroom Setup and inspect",
                "the existing target before taking another action.",
            ),
        )
        return
    try:
        _offer_after_creation(created, state, copied=True)
    except EOFError:
        show_result(
            "Target Saved — Continuation Interrupted",
            (
                "The independent target was verified before the menu closed.",
                "Reopen Continue Classroom Setup and select this exact target.",
                "Do not start a new copy merely to resume preparation.",
            ),
        )


def _launch_target_cluster_planning(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Review the *target* Core roster; never carry source placements forward.

    Creating six empty planned Clusters is one explicit guarded GroupPlan write.
    Existing plan editing, student placement and application stay in their
    separate owner menus. Cancel, Back and status review remain read-only.
    """
    while True:
        try:
            root = resolve_read_workspace_root()
            reviewed = inspect_target_cluster_preflight(
                activity.class_id, activity.activity_id, workspace_root=root
            )
        except Exception:
            show_result(
                "Plan Target Clusters",
                (
                    "Target class, Activity, roster or existing plans could not be",
                    "verified. No Clusters were created by this inspection.",
                    "Reopen the target Activity after resolving the Core roster.",
                ),
            )
            return

        clear_screen()
        print_menu_header("Plan Target Clusters")
        print(f"Target Activity: {reviewed.title}")
        print(f"Target class: {reviewed.class_id}")
        print(f"Verified Core roster: {reviewed.roster_count} students")
        print(f"Current Groups: {reviewed.current_group_count}")
        print(f"Existing GroupPlans: {reviewed.existing_plan_count}")
        print()
        print("Six-Cluster size reference (not assigned or required):")
        print(" / ".join(str(n) for n in reviewed.six_cluster_size_reference))
        print("No source-class student IDs, memberships or saved groupings are reused.")
        print("Only target Core roster members may be placed in these Clusters.")
        print("No operational Groups or Memberships are created by a draft.")
        print()
        if reviewed.can_create_new_shape:
            print("1. Create six empty draft Clusters for this target")
            print("2. Open target GroupPlan tools (manual, CSV, saved grouping)")
            print("3. Decide later")
        else:
            print("This target has existing Groups or GroupPlans.")
            print("1. Review existing target grouping in GroupPlan tools")
            print("2. Decide later")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Plan Target Clusters Help")
            print("These are six proposed empty Clusters, not student assignments.")
            print("The reference sizes come from this target class's Core roster.")
            print("Place target students using the existing bulk editor, then")
            print("review, approve, and separately apply the GroupPlan.")
            print("Saved class groupings remain scoped to their own Core class.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        if reviewed.can_create_new_shape and raw == "3":
            return
        if not reviewed.can_create_new_shape and raw == "2":
            return
        if (reviewed.can_create_new_shape and raw == "2") or (
            not reviewed.can_create_new_shape and raw == "1"
        ):
            if resolve_read_workspace_root() != root:
                show_result(
                    "Plan Target Clusters",
                    (
                        "Workspace changed; reopen the target Activity",
                        "before continuing.",
                    ),
                )
                return
            current = show_activity(
                reviewed.class_id, reviewed.activity_id, workspace_root=root
            ).summary
            launch_group_plan_menu(current, state)
            continue
        if reviewed.can_create_new_shape and raw == "1":
            plan_id = _fresh_id("group-plan")
            actor = confirm_actor_write(
                "Create Target Cluster Draft",
                "CREATE",
                (
                    f"Target class: {reviewed.class_id}",
                    f"Target Activity: {reviewed.title}",
                    f"Verified Core roster: {reviewed.roster_count} students",
                    "Create six EMPTY planned Clusters; all roster students",
                    "will remain unresolved until explicitly placed.",
                    "Do not copy any source students, Scores or returned work.",
                    "This creates one draft GroupPlan, not operational Groups.",
                ),
                state=state,
                legacy_confirm=confirm_write,
            )
            if actor is None:
                continue
            try:
                # The service rechecks exact target revision and roster, and
                # the canonical GroupPlan writer checks both at commit.
                if resolve_read_workspace_root() != root:
                    raise ConcordWorkflowError(
                        "Workspace changed during the reviewed Cluster setup."
                    )
                current = show_activity(
                    reviewed.class_id, reviewed.activity_id, workspace_root=root
                ).summary
                standards = standards_for_activity(current)
                result = create_target_six_cluster_draft(
                    reviewed,
                    group_plan_id=plan_id,
                    actor=actor,
                    workspace_root=root,
                    standards_library=standards,
                )
                detail = show_group_plan(
                    reviewed.class_id,
                    reviewed.activity_id,
                    result.group_plan_id,
                    workspace_root=root,
                )
                if (
                    detail.summary.status != "draft"
                    or detail.summary.proposed_group_count != 6
                    or detail.summary.assigned_student_count != 0
                    or detail.summary.unresolved_student_count != reviewed.roster_count
                ):
                    raise ConcordWorkflowError(
                        "Target GroupPlan receipt did not match saved state."
                    )
            except Exception:
                show_result(
                    "Target Cluster Draft Needs Inspection",
                    (
                        "The requested GroupPlan was not fully verified.",
                        "A guarded write may have completed. Inspect existing",
                        "target GroupPlans before attempting any new plan.",
                        "Do not retry blindly or recreate the Activity.",
                    ),
                )
                continue
            show_result(
                "Target Cluster Draft Saved",
                (
                    "Six empty draft Clusters were saved for the target class.",
                    f"Unresolved target students: {reviewed.roster_count}",
                    f"Activity snapshot: {result.commit.snapshot_revision}",
                    "Next: open GroupPlan tools to place target students,",
                    "then preview, approve and apply only by explicit choice.",
                    "No source memberships or operational Groups were copied.",
                ),
            )
            continue
        print(navigation_hint_with_help())
        pause_for_user()


def _target_material_receipt(
    before: TargetMaterialsCheckpoint,
    after: TargetMaterialsCheckpoint,
) -> tuple[str, ...]:
    """Report only the target's independently reread canonical generation state."""
    added = new_target_generations(before, after)
    if not added:
        return (
            "No new target generation was verified.",
            "A cancelled operation may leave no new records; a saved reusable",
            "Packet definition is separate from generating classroom copies.",
            "Inspect the current target materials before trying another run.",
        )
    if len(added) != 1:
        return (
            "Multiple new target generations appeared during this action.",
            "Inspect the target Activity's preparation history individually.",
            "No single generation is assumed to represent the entire action.",
        )
    row = added[0]
    status = (
        "Needs recovery or further rendering"
        if (
            row.routes_pending_count
            or row.planned_count
            or row.rendering_count
            or row.failed_count
            or row.cancelled_count
        )
        else "Recorded as generated"
        if row.generated_count == row.instance_count
        else "Requires inspection"
    )
    return (
        "One new target generation is present in canonical Concord state.",
        f"Target: {after.title} ({after.class_id})",
        f"Saved Packet: {row.packet_name}; Session: {row.session_label}",
        f"Packet Instances: {row.instance_count}; pages: {row.page_count}",
        f"Ready to print: {row.generated_count}",
        f"Route-required pages: {row.route_count}",
        f"Preparation state: {status}",
        "This projection is not proof of printing, distribution, return,",
        "or independent physical-paper/QR route custody verification.",
    )


def _launch_target_materials(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Guide a target-only materials restart; delegate all mutations to owners."""
    while True:
        try:
            root = resolve_read_workspace_root()
            reviewed = inspect_target_materials(
                activity.class_id, activity.activity_id, workspace_root=root
            )
        except Exception:
            show_result(
                "Prepare Target Classroom Materials",
                (
                    "Target Activity or prepared material state could not be",
                    "verified. No new generation was requested by this screen.",
                    "Reopen the target Activity and inspect its saved state.",
                ),
            )
            return

        clear_screen()
        print_menu_header("Prepare Target Classroom Materials")
        print(f"Target Activity: {reviewed.title}")
        print(f"Target class: {reviewed.class_id}")
        print(f"Existing target generations: {len(reviewed.generations)}")
        print(f"Ready to print (recorded): {reviewed.ready_to_print}")
        print("Printed, distributed and returned are NOT verified by preparation.")
        print("Source class papers, students, scans and routes are not reused.")
        print()
        if reviewed.requires_recovery:
            print("Existing target preparation requires attention or recovery.")
            print("1. Inspect/recover existing target Packet generations")
            print("2. Finish for now")
        elif reviewed.has_generations:
            print("Existing target materials are already recorded.")
            print("1. Inspect/reprint existing target materials")
            print("2. Prepare ADDITIONAL target copies (a new generation)")
            print("3. Finish for now")
        else:
            print("1. Choose a saved Packet or Template to prepare")
            print("2. Finish for now")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Target Classroom Materials Help")
            print("Existing prepared copies are never silently regenerated.")
            print("Recover pending routes and render existing work first.")
            print("New copies require a separate saved Packet/Template selection")
            print("and the existing Packet generation review and confirmation.")
            print("PDF generation does not establish printing or distribution.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        finish_choice = (
            "3" if reviewed.has_generations and not reviewed.requires_recovery else "2"
        )
        if raw == finish_choice:
            return

        open_existing = reviewed.has_generations and raw == "1"
        start_new = (not reviewed.has_generations and raw == "1") or (
            reviewed.has_generations and not reviewed.requires_recovery and raw == "2"
        )
        if not (open_existing or start_new):
            print(navigation_hint_with_help())
            pause_for_user()
            continue
        try:
            if resolve_read_workspace_root() != root:
                raise ConcordWorkflowError(
                    "Workspace changed. Reopen the target Activity."
                )
            fresh = inspect_target_materials(
                reviewed.class_id, reviewed.activity_id, workspace_root=root
            )
            if (
                fresh.snapshot_revision != reviewed.snapshot_revision
                or fresh.generation_ids != reviewed.generation_ids
            ):
                raise ConcordWorkflowError(
                    "Target materials changed since the displayed review."
                )
            current = show_activity(
                reviewed.class_id, reviewed.activity_id, workspace_root=root
            ).summary
            if current.snapshot_revision != fresh.snapshot_revision:
                raise ConcordWorkflowError(
                    "Target Activity changed. Reopen its materials screen."
                )
        except Exception:
            show_result(
                "Target Materials Changed",
                (
                    "The target workspace, Activity or generations changed.",
                    "No new preparation was requested by this screen.",
                    "Reload the current target and review before continuing.",
                ),
            )
            return
        if open_existing:
            launch_packet_generation_menu(current, state)
            continue
        if fresh.requires_recovery:
            show_result(
                "Recover Target Materials First",
                ("Existing preparation needs recovery before new copies.",),
            )
            continue
        # This existing menu owns independent Packet/Template choice, preview,
        # actor authorization, PDS2 route registration and partial recovery.
        _launch_materials(current, state)
        try:
            after = inspect_target_materials(
                reviewed.class_id, reviewed.activity_id, workspace_root=root
            )
            lines = _target_material_receipt(fresh, after)
        except Exception:
            lines = (
                "Could not reconcile current target preparation after return.",
                "A new generation may have been committed; do not blindly retry.",
                "Inspect target Packet generations and routes before continuing.",
            )
        show_result("Target Materials Checkpoint", lines)


def _launch_target_assessment(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Configure the target's typed Scales and Criteria, never record Scores.

    Existing owned preset services retain all authorization and writes. This
    guide only inspects target-only canonical state before and after the menu.
    """
    try:
        root = resolve_read_workspace_root()
        if root is None:
            raise ConcordWorkflowError("Target workspace unavailable.")
        current = show_activity(
            activity.class_id, activity.activity_id, workspace_root=root
        ).summary
        standards = standards_for_activity(current)
        before = inspect_target_assessment(
            current.class_id,
            current.activity_id,
            workspace_root=root,
            standards_library=standards,
        )
        if before.snapshot_revision != current.snapshot_revision:
            raise ConcordWorkflowError(
                "Target Activity changed during assessment review."
            )
    except Exception:
        show_result(
            "Target Assessment Needs Attention",
            (
                "Target class, Activity, Standards or native assessment state",
                "could not be verified. No assessment setup was started.",
                "Resolve the target records and reopen this Activity.",
            ),
        )
        return

    if before.scoring_orientation == "evidence_only":
        show_result(
            "Target Assessment",
            (
                "This target Activity collects evidence without scoring.",
                "No rubric or Scale setup is required by this orientation.",
                "No target Score was recorded by this guide.",
            ),
        )
        return

    while True:
        clear_screen()
        print_menu_header("Use Saved Rubric with Target Class")
        print(f"Target Activity: {before.title}")
        print(f"Target class: {before.class_id}")
        print(f"Native Scoring Scales: {len(before.scale_ids)}")
        print(f"Native Criterion Sets: {len(before.criterion_set_ids)}")
        print(f"Selected Criterion Sets: {len(before.selected_criterion_set_ids)}")
        print(f"Existing target Score records: {len(before.score_record_ids)}")
        print()
        print("Saved Scale/Criteria definitions must be selected and reviewed.")
        print("Source Scores, evaluations and student evidence were not copied.")
        print("Using saved setup creates fresh target native records only.")
        if before.has_configuration:
            print("Existing target configuration is preserved unless you")
            print("explicitly select or create another assessed definition.")
        print()
        print("1. Open saved rubric, Scale or Criteria setup")
        print("2. Finish for now")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Target Assessment Help")
            print("Select exact saved revisions inside the owned setup menu.")
            print("Its actor-reviewed services create native definitions only.")
            print("Scores remain a separate teacher judgment workflow.")
            print("No Grade is created by Concord assessment setup.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "2":
            return
        if raw != "1":
            print(navigation_hint_with_help())
            pause_for_user()
            continue

        try:
            if resolve_read_workspace_root() != root:
                raise ConcordWorkflowError("Target workspace changed before setup.")
            latest = show_activity(
                before.class_id, before.activity_id, workspace_root=root
            ).summary
            if latest.snapshot_revision != before.snapshot_revision:
                raise ConcordWorkflowError("Target Activity changed before setup.")
            launch_assessment_setup_menu(latest, state)
        except CancelMenuAction:
            return
        except (ReturnToMainMenu, QuitPDS):
            raise
        except Exception:
            show_result(
                "Target Assessment Outcome Unconfirmed",
                (
                    "Assessment setup did not return a verifiable result.",
                    "Inspect the target's saved Scales and Criteria before retrying.",
                    "No Score or Grade status is inferred from this menu error.",
                ),
            )
            return
        try:
            after = inspect_target_assessment(
                before.class_id,
                before.activity_id,
                workspace_root=root,
                standards_library=standards,
            )
            delta = verify_target_assessment_delta(before, after)
        except Exception:
            show_result(
                "Target Assessment Outcome Unconfirmed",
                (
                    "Assessment unconfirmed: canonical readback failed or changed.",
                    "Inspect target Scales, Criteria and Scores before retrying.",
                    "No successful import or no-Score result is asserted.",
                ),
            )
            return
        lines = [
            f"{delta.new_scales} fresh Scoring Scale"
            f"{'s' if delta.new_scales != 1 else ''} verified for target.",
            f"{delta.new_criterion_sets} fresh Criterion Set"
            f"{'s' if delta.new_criterion_sets != 1 else ''} verified for target.",
            f"Target Criterion Sets selected: {delta.final_selected_count}",
            f"Criteria across target Set revisions: {delta.final_criterion_count}",
            "Target rubric selection changed: "
            + ("yes" if delta.selection_changed else "no"),
            "No Score records changed during this setup.",
            "No source-class Scores or evidence were transferred.",
        ]
        if delta.new_scales == 0 and delta.new_criterion_sets == 0:
            lines.append("No new target Scale or Criterion Set was verified.")
        show_result("Target Assessment Verification", tuple(lines))
        return


def _offer_after_creation(
    activity: ActivitySummary,
    state: MenuSessionContext,
    *,
    copied: bool = False,
) -> None:
    """Acknowledge the durable Activity without forcing later setup writes."""
    while True:
        clear_screen()
        print_menu_header("Classroom Activity Created")
        print(f"Activity: {activity.title}")
        print()
        print("Your confirmed work is saved.")
        if copied:
            print("This target Activity has its own first planned Session.")
            print("Source students, Groups, returned work, Scores, and history")
            print("were not copied. Printing/distribution is not verified.")
        print()
        print("1. Continue setup now")
        print("2. Finish for now")
        if copied:
            print("3. Plan target Clusters")
            print("4. Choose saved classroom materials")
            print("5. Use saved rubric / assessment setup")
            print("6. Review target setup")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Classroom Activity Created Help")
            print("Continue setup works through the remaining classroom decisions.")
            print("Finish for now keeps the Activity exactly as it is.")
            print("You can return through Continue setup for an Activity.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "2":
            return
        if raw == "1":
            launch_guided_setup_for_activity(activity, state)
            return
        if copied and raw in {"3", "4", "5", "6"}:
            # Reload the just-created *target* before any further teacher choice.
            # Existing task menus own their guarded writes and authorization.
            try:
                current = show_activity(activity.class_id, activity.activity_id).summary
                if (
                    current.class_id != activity.class_id
                    or current.activity_id != activity.activity_id
                ):
                    raise ConcordWorkflowError("Target identity changed.")
            except Exception:
                show_result(
                    "Target Stage Outcome Unconfirmed",
                    (
                        "The selected target could not be verified for this stage.",
                        "No new stage was launched by the guide.",
                        "Reopen Continue Classroom Setup for the existing target.",
                    ),
                )
                return
            if raw == "3":
                _launch_target_cluster_planning(current, state)
            elif raw == "4":
                _launch_target_materials(current, state)
            elif raw == "5":
                _launch_target_assessment(current, state)
            else:
                launch_guided_setup_for_activity(current, state)
            continue
        print(navigation_hint_with_help())
        pause_for_user()


def launch_guided_activity_menu(state: MenuSessionContext) -> None:
    """Create a classroom Activity through teacher-facing guided decisions."""
    try:
        classes = _classes()
        if not classes:
            show_result(
                "Create Classroom Activity",
                (
                    "No classes are available yet.",
                    "Create or import the class and roster through Paper Data Suite,",
                    "then return here.",
                ),
            )
            return
        while True:
            clear_screen()
            print_menu_header("Create Classroom Activity")
            print("How would you like to begin?")
            print()
            print("1. Start fresh")
            print("2. Use this lesson with another class")
            print_navigation()
            print()
            choice = input("Select an option: ").strip()
            navigation = parse_menu_navigation(choice)
            if navigation is ConcordMenuChoice.HELP:
                clear_screen()
                print_menu_header("Create Classroom Activity Help")
                print("Start fresh for new classroom work.")
                print("Use this lesson with another class to begin with safe settings.")
                print("You may also use the same class with a fresh Activity identity.")
                print("Choose saved packets and rubrics later for the target class.")
                print(
                    "Student groups, assignments, work, Scores, and history "
                    "are not copied."
                )
                print()
                pause_for_user()
                continue
            if navigation is NavigationChoice.BACK:
                return
            if choice == "1":
                _create_fresh(state, classes)
                return
            if choice == "2":
                _create_from_activity(state, classes)
                return
            print(navigation_hint_with_help())
            pause_for_user()
    except CancelMenuAction:
        return
    except (ReturnToMainMenu, QuitPDS):
        raise
    except ConcordStoragePartialSuccessError:
        show_result(
            "Activity Needs Attention",
            (
                "Part of the confirmed Activity work was saved, but follow-up work",
                "did not finish cleanly. Open the Activity and continue from its",
                "current saved state before trying the step again.",
            ),
        )
    except Exception as error:
        show_result("Create Classroom Activity", (str(error),))


def _status_group(
    summary: GuidedActivitySetup,
    status: SetupStatus,
) -> tuple[str, ...]:
    return tuple(
        item.label
        for item in summary.areas
        if item.status == status and item.key != "activity"
    )


def _print_setup(summary: GuidedActivitySetup) -> None:
    print_menu_header("Continue Classroom Setup")
    print(f"Activity: {summary.title}")
    print(f"Class: {summary.class_id}")
    print()
    statuses: tuple[SetupStatus, ...] = (
        "ready",
        "needs_attention",
        "not_set_up",
        "not_used",
    )
    for status in statuses:
        labels = _status_group(summary, status)
        if labels:
            print(f"{setup_status_label(status)}: {', '.join(labels)}")


def _launch_assignments(activity: ActivitySummary, state: MenuSessionContext) -> None:
    while True:
        clear_screen()
        print_menu_header("Roles and Responsibilities")
        print(f"Activity: {activity.title}")
        print()
        print("1. Who has which role?")
        print("2. What does each person need to do?")
        print("3. Decide later")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Roles and Responsibilities Help")
            print("Roles describe a student's function in the activity.")
            print("Responsibilities describe what a person or group needs to do.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "3":
            return
        if raw == "1":
            launch_role_menu(activity, state)
            continue
        if raw == "2":
            launch_responsibility_menu(activity, state)
            continue
        print(navigation_hint_with_help())
        pause_for_user()


def _active_packets() -> tuple[PacketSummary, ...]:
    return tuple(
        item
        for item in list_packets()
        if item.status == "active" and item.current_packet_version_id is not None
    )


def _use_saved_packet(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    packets = _active_packets()
    if not packets:
        show_result(
            "Classroom Materials",
            (
                "No saved classroom Packets are ready to use yet.",
                "You can start with a saved Template or manage saved materials.",
            ),
        )
        return
    packet = select_one(
        "Choose Classroom Materials",
        packets,
        tuple(
            f"{item.name} — {item.component_count} "
            f"{'part' if item.component_count == 1 else 'parts'}"
            for item in packets
        ),
        help_text=(
            "Choose the saved classroom Packet you want to prepare. "
            "Internal Packet and Version IDs stay hidden here."
        ),
    )
    generate_saved_packet(activity, state, packet)


def _simple_template_audience(version: object) -> str:
    compatibility = getattr(version, "compatibility")
    supported = set(getattr(compatibility, "audience_kinds"))
    choices = tuple(
        (key, label)
        for key, label in (
            ("activity", "One set for the whole Activity"),
            ("group", "One set for each group"),
            ("participant", "One set for each student"),
            ("teacher", "Teacher copy"),
        )
        if key in supported
    )
    if not choices:
        raise ConcordWorkflowError(
            "This Template does not support a simple classroom Packet audience."
        )
    return select_one(
        "Who needs a copy?",
        tuple(key for key, _label in choices),
        tuple(label for _key, label in choices),
        help_text="Choose who should receive this one-part classroom Packet.",
    )


def _start_packet_from_template(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    templates = tuple(
        item
        for item in list_templates()
        if item.status == "active" and item.current_template_version_id is not None
    )
    if not templates:
        show_result(
            "Classroom Materials",
            (
                "No saved Templates are ready to use yet.",
                "Open Manage saved materials to install or create one.",
            ),
        )
        return
    selected = select_one(
        "Choose a Saved Template",
        templates,
        tuple(
            f"{item.name} — {item.artifact_category.replace('_', ' ').title()}"
            for item in templates
        ),
        help_text=(
            "Choose one saved Template. Concord will save a reusable one-part "
            "Packet before preparing classroom copies."
        ),
    )
    detail = get_template(selected.template_id)
    version_id = selected.current_template_version_id
    assert version_id is not None
    version = next(
        item for item in detail.versions if item.template_version_id == version_id
    )
    audience_kind = _simple_template_audience(version)
    packet_name = prompt_text(
        "Save Classroom Packet",
        "Packet name",
        help_text="Use a name you will recognize when reusing these materials.",
        default=f"{selected.name} — {activity.title}",
    )
    assert packet_name is not None
    packet_definition_id = _fresh_id("packet")
    packet_version_id = _fresh_id("packet-version")
    packet_component_id = _fresh_id("component")
    audience_labels = {
        "activity": "whole Activity",
        "group": "each group",
        "participant": "each student",
        "teacher": "teacher",
    }

    def prepare_for_actor(
        actor: WorkflowActor,
    ) -> tuple[PreparedPacketFromTemplate, tuple[str, ...]]:
        pending = prepare_packet_from_template(
            PreparePacketFromTemplateRequest(
                packet_definition_id=packet_definition_id,
                packet_version_id=packet_version_id,
                packet_component_id=packet_component_id,
                name=packet_name,
                purpose="Classroom materials created from a saved Template.",
                template_id=selected.template_id,
                template_version_id=version_id,
                audience_kind=audience_kind,
                actor=actor,
            )
        )
        return pending, (
            f"Template: {selected.name}",
            f"Saved Packet: {packet_name}",
            f"Copies for: {audience_labels[audience_kind]}",
            "The saved Packet keeps an exact reference to this Template version.",
        )

    prepared = confirm_prepared_actor_write(
        "Save Classroom Packet",
        "SAVE",
        state=state,
        legacy_confirm=confirm_write,
        prepare_for_actor=prepare_for_actor,
    )
    if prepared is None:
        return
    result = commit_packet_from_template(prepared)
    packet = next(
        item
        for item in list_packets()
        if item.packet_definition_id == result.packet_definition_id
    )
    while True:
        clear_screen()
        print_menu_header("Classroom Packet Saved")
        print(f"Packet: {packet.name}")
        print()
        print("1. Prepare these materials now")
        print("2. Return to classroom materials")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Classroom Packet Saved Help")
            print("The reusable Packet is saved even if you prepare copies later.")
            print("Preparing copies still has its own review and confirmation.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "2":
            return
        if raw == "1":
            generate_saved_packet(activity, state, packet)
            return
        print(navigation_hint_with_help())
        pause_for_user()


def _manage_saved_materials(state: MenuSessionContext) -> None:
    while True:
        clear_screen()
        print_menu_header("Manage Saved Materials")
        print("1. Saved Packets")
        print("2. Saved Templates")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Manage Saved Materials Help")
            print("Packets combine one or more saved classroom material parts.")
            print("Templates define individual reusable printable materials.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        if raw == "1":
            launch_packet_library_menu(state)
            continue
        if raw == "2":
            launch_template_library_menu(state)
            continue
        print(navigation_hint_with_help())
        pause_for_user()


def _launch_materials(activity: ActivitySummary, state: MenuSessionContext) -> None:
    while True:
        clear_screen()
        print_menu_header("Classroom Materials")
        print(f"Activity: {activity.title}")
        print()
        print("1. Use a saved Packet")
        print("2. Start with a saved Template")
        print("3. Manage saved materials")
        print("4. Decide later")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Classroom Materials Help")
            print("A saved Packet is ready to prepare for this Activity.")
            print("A saved Template can become a reusable one-part Packet first.")
            print("Preparing classroom copies always keeps its own review step.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "4":
            return
        try:
            if raw == "1":
                _use_saved_packet(activity, state)
                continue
            if raw == "2":
                _start_packet_from_template(activity, state)
                continue
            if raw == "3":
                _manage_saved_materials(state)
                continue
        except CancelMenuAction:
            continue
        except Exception as error:
            show_result("Classroom Materials", (str(error),))
            continue
        print(navigation_hint_with_help())
        pause_for_user()


def launch_classroom_materials_menu(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Open the reusable teacher-facing classroom-material chooser."""
    _launch_materials(activity, state)


def launch_manage_saved_materials_menu(state: MenuSessionContext) -> None:
    """Open saved Packet and Template management without Activity writes."""
    _manage_saved_materials(state)


def _launch_groups(activity: ActivitySummary, state: MenuSessionContext) -> None:
    while True:
        clear_screen()
        print_menu_header("Student Groups")
        print(f"Activity: {activity.title}")
        print()
        if activity.group_count:
            print(f"Current groups: {activity.group_count}")
            print()
            print("1. Keep the groups already set up")
            print("2. Create or edit groups directly")
            print("3. Make or review a group plan")
            print("4. Decide later")
        else:
            print("How would you like students to work?")
            print()
            print("1. Create groups directly")
            print("2. Make or review a group plan")
            print("3. Decide later")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Student Groups Help")
            print("Create groups directly when you already know the arrangement.")
            print("A group plan lets you prepare and review an arrangement first.")
            print("A plan never becomes classroom group state without approval.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        if activity.group_count:
            if raw in {"1", "4"}:
                return
            if raw == "2":
                launch_direct_group_menu(activity, state)
                continue
            if raw == "3":
                launch_group_plan_menu(activity, state)
                continue
        else:
            if raw == "1":
                launch_direct_group_menu(activity, state)
                continue
            if raw == "2":
                launch_group_plan_menu(activity, state)
                continue
            if raw == "3":
                return
        print(navigation_hint_with_help())
        pause_for_user()


def _launch_assessment(activity: ActivitySummary, state: MenuSessionContext) -> None:
    if activity.scoring_orientation == "evidence_only":
        show_result(
            "Assessment",
            (
                "This Activity is set to collect evidence without scoring.",
                "No assessment setup is required.",
            ),
        )
        return
    while True:
        clear_screen()
        print_menu_header("Assessment")
        print(f"Activity: {activity.title}")
        print(f"Approach: {scoring_orientation_label(activity.scoring_orientation)}")
        print()
        print("1. Set up or change assessment")
        print("2. Decide later")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Assessment Help")
            print("Set up criteria and a scoring scale for this Activity.")
            print("Saved assessment setups remain reusable starting points.")
            print("No Score is created during Activity setup.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "2":
            return
        if raw == "1":
            launch_assessment_setup_menu(activity, state)
            continue
        print(navigation_hint_with_help())
        pause_for_user()


def _choose_setup_area(summary: GuidedActivitySetup) -> str | None:
    areas = tuple(
        item
        for item in summary.areas
        if item.key in {"session", "materials", "groups", "assignments", "assessment"}
    )
    while True:
        clear_screen()
        print_menu_header("Choose a Setup Area")
        print(f"Activity: {summary.title}")
        print()
        for index, item in enumerate(areas, start=1):
            print(f"{index}. {item.label} — {setup_status_label(item.status)}")
        print("6. Finish for now")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Choose a Setup Area Help")
            print("Choose only the part of classroom setup you want to work on.")
            print("Confirmed work in other areas remains unchanged.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or raw == "6":
            return None
        if raw.isdigit():
            index = int(raw) - 1
            if 0 <= index < len(areas):
                return areas[index].key
        print(navigation_hint_with_help())
        pause_for_user()


def _launch_setup_area(
    key: str,
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    if key == "session":
        launch_session_menu(activity, state)
    elif key == "materials":
        _launch_target_materials(activity, state)
    elif key == "groups":
        _launch_groups(activity, state)
    elif key == "assignments":
        _launch_assignments(activity, state)
    elif key == "assessment":
        _launch_assessment(activity, state)


def _review_setup(
    setup: GuidedActivitySetup,
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> bool:
    """Return True when the teacher chooses to finish setup for now."""
    while True:
        clear_screen()
        print_menu_header("Review Classroom Setup")
        print(f"Activity: {setup.title}")
        print(f"Class: {setup.class_id}")
        print()
        for area in setup.areas:
            print(f"{area.label}: {setup_status_label(area.status)}")
            print(f"  {area.detail}")
        print()
        print("1. Prepare materials now")
        print("2. Change a setup area")
        print("3. Finish for now")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Review Classroom Setup Help")
            print("This review reads the Activity's current saved state.")
            print("Preparing materials still has its own review and confirmation.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return False
        if raw == "1":
            _launch_target_materials(activity, state)
            return False
        if raw == "2":
            key = _choose_setup_area(setup)
            if key is not None:
                _launch_setup_area(key, activity, state)
            return False
        if raw == "3":
            return True
        print(navigation_hint_with_help())
        pause_for_user()


def launch_guided_setup_for_activity(
    activity: ActivitySummary,
    state: MenuSessionContext,
) -> None:
    """Resume setup by deriving every status from current canonical records."""
    while True:
        try:
            current = show_activity(activity.class_id, activity.activity_id).summary
            standards = load_menu_standards_library()
            setup = inspect_guided_activity_setup(
                current.class_id,
                current.activity_id,
                standards_library=standards,
            )
            if (
                current.class_id != activity.class_id
                or current.activity_id != activity.activity_id
                or setup.class_id != current.class_id
                or setup.activity_id != current.activity_id
            ):
                raise ConcordWorkflowError("Resumed target identity changed.")
        except Exception:
            show_result(
                "Continue Classroom Setup — Verification Unavailable",
                (
                    "The selected target or its current setup could not be verified.",
                    "No new stage was launched. Earlier saved work is not undone.",
                    "Reselect the target Activity and inspect its current records.",
                ),
            )
            return

        recommended = setup.recommended_area()
        clear_screen()
        _print_setup(setup)
        print()
        if recommended is not None:
            print(f"Next: {recommended.label}")
            print()
            print(f"1. Continue with {recommended.label}")
            print("2. Choose another setup area")
            print("3. Review setup")
            print("4. Finish for now")
        else:
            print("The recorded setup has no unfinished required area.")
            print()
            print("1. Review setup")
            print("2. Choose a setup area")
            print("3. Finish for now")
        print("C. Review or plan six target Clusters")
        print("R. Use saved rubric / target assessment setup")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Continue Classroom Setup Help")
            print("Concord reads the Activity's current saved state each time.")
            print("Confirmed work stays saved if you finish and return later.")
            print("There is no separate setup checklist to get out of sync.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            return
        if raw.casefold() == "c":
            _launch_target_cluster_planning(current, state)
            continue
        if raw.casefold() == "r":
            _launch_target_assessment(current, state)
            continue

        if recommended is not None:
            if raw == "1":
                _launch_setup_area(recommended.key, current, state)
                continue
            if raw == "2":
                key = _choose_setup_area(setup)
                if key is not None:
                    _launch_setup_area(key, current, state)
                continue
            if raw == "3":
                if _review_setup(setup, current, state):
                    return
                continue
            if raw == "4":
                return
        else:
            if raw == "1":
                if _review_setup(setup, current, state):
                    return
                continue
            if raw == "2":
                key = _choose_setup_area(setup)
                if key is not None:
                    _launch_setup_area(key, current, state)
                continue
            if raw == "3":
                return

        print(navigation_hint_with_help())
        pause_for_user()


def launch_guided_continue_setup(state: MenuSessionContext) -> None:
    """Select an existing Activity and resume from its current canonical state."""
    try:
        root = resolve_read_workspace_root()
        if root is None:
            show_result(
                "Continue Classroom Setup",
                ("No Concord Activities are available yet.",),
            )
            return
        activities = list_activities(workspace_root=root)
        if not activities:
            show_result(
                "Continue Classroom Setup",
                ("No Concord Activities are available yet.",),
            )
            return
        activity = _guided_activity_choice(
            activities,
            title="Continue Classroom Setup",
        )
        launch_guided_setup_for_activity(activity, state)
    except CancelMenuAction:
        return
    except (ReturnToMainMenu, QuitPDS):
        raise
    except Exception as error:
        show_result("Continue Classroom Setup", (str(error),))


__all__ = [
    "launch_guided_activity_menu",
    "launch_guided_continue_setup",
    "launch_guided_setup_for_activity",
]
