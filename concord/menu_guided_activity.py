"""Guided, low-density classroom Activity creation and resume workflow."""

from __future__ import annotations

import uuid

from pds_core.standards import StandardsLibrary

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_group import launch_direct_group_menu
from concord.menu_group_plan import launch_group_plan_menu
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_packet import launch_packet_library_menu
from concord.menu_packet_generation import generate_saved_packet
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
from concord.menu_scoring import launch_scoring_menu
from concord.menu_session import launch_session_menu
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
    copy_activity,
    create_activity_context,
    list_activities,
    list_available_classes,
    prepare_activity_copy,
    resolve_read_workspace_root,
    show_activity,
)
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
    PreparePacketFromTemplateRequest,
    commit_packet_from_template,
    list_packets,
    prepare_packet_from_template,
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
    actor = state.require_actor()
    if not confirm_write("Create Classroom Activity", "CREATE", review):
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
    review = (
        f"Starting from: {source.title}",
        f"New Activity: {target_title}",
        f"Class: {target_class.class_id}",
        f"What students are doing: {activity_type_label(prepared.activity_type)}",
        f"Assessment: {scoring_orientation_label(prepared.scoring_orientation)}",
        "Carries forward: Activity settings and selected standards.",
        "Does not carry forward: groups, assignments, collected work, Scores,",
        "or review and publication history.",
    )
    actor = state.require_actor()
    if not confirm_write("Create Classroom Activity", "CREATE", review):
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
    created = show_activity(target_class.class_id, result.activity_id).summary
    _offer_after_creation(
        created,
        state,
        copied=True,
    )



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
            print("Student groups, assignments, work, Scores, and history")
            print("were not copied.")
        print()
        print("1. Continue setup now")
        print("2. Finish for now")
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
            print("2. Start from another Activity")
            print_navigation()
            print()
            choice = input("Select an option: ").strip()
            navigation = parse_menu_navigation(choice)
            if navigation is ConcordMenuChoice.HELP:
                clear_screen()
                print_menu_header("Create Classroom Activity Help")
                print("Start fresh for new classroom work.")
                print("Start from another Activity to reuse safe starting settings.")
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
    prepared = prepare_packet_from_template(
        PreparePacketFromTemplateRequest(
            packet_definition_id=_fresh_id("packet"),
            packet_version_id=_fresh_id("packet-version"),
            packet_component_id=_fresh_id("component"),
            name=packet_name,
            purpose="Classroom materials created from a saved Template.",
            template_id=selected.template_id,
            template_version_id=version_id,
            audience_kind=audience_kind,
            actor=state.require_actor(),
        )
    )
    audience_labels = {
        "activity": "whole Activity",
        "group": "each group",
        "participant": "each student",
        "teacher": "teacher",
    }
    if not confirm_write(
        "Save Classroom Packet",
        "SAVE",
        (
            f"Template: {selected.name}",
            f"Saved Packet: {packet_name}",
            f"Copies for: {audience_labels[audience_kind]}",
            "The saved Packet keeps an exact reference to this Template version.",
        ),
    ):
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
        print(
            "Approach: "
            f"{scoring_orientation_label(activity.scoring_orientation)}"
        )
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
            launch_scoring_menu(activity, state)
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
            print(
                f"{index}. {item.label} — "
                f"{setup_status_label(item.status)}"
            )
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
        _launch_materials(activity, state)
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
            _launch_materials(activity, state)
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
        except Exception as error:
            show_result("Continue Classroom Setup", (str(error),))
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
    except Exception as error:
        show_result("Continue Classroom Setup", (str(error),))


__all__ = [
    "launch_guided_activity_menu",
    "launch_guided_continue_setup",
    "launch_guided_setup_for_activity",
]
