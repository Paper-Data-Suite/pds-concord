"""Teacher-facing Activity workflows and open-Activity navigation."""

from __future__ import annotations

from pds_core.standards import StandardsLibrary
from pds_core.workspace import WorkspaceRootError

from concord.menu_artifact import launch_artifact_page_menu
from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_group import launch_group_menu
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_packet_generation import launch_packet_generation_menu
from concord.menu_prompts import (
    choose_class,
    choose_focus_standards,
    choose_standards_profile,
    confirm_write,
    handle_write_error,
    load_menu_standards_library,
    prompt_text,
    select_one,
    show_partial_success,
    show_result,
    slug_identifier,
)
from concord.menu_publication import launch_publication_menu
from concord.menu_responsibility import launch_responsibility_menu
from concord.menu_role import launch_role_menu
from concord.menu_scoring import launch_scoring_menu
from concord.menu_session import launch_session_menu
from concord.menu_ui import (
    clear_screen,
    page_count,
    page_items,
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
    UpdateActivityRequest,
    copy_activity,
    create_activity_context,
    list_activities,
    list_available_classes,
    list_groups,
    list_memberships,
    list_responsibilities,
    list_roles,
    list_sessions,
    prepare_activity_copy,
    resolve_read_workspace_root,
    show_activity,
    update_activity,
)
from concord.workflows.models import UNSET, OptionalTextUpdate, TextUpdate

_ACTIVITY_TYPES = ("socratic_seminar", "laboratory", "project")
_SCORING_ORIENTATIONS = (
    "evidence_only",
    "standards_based",
    "mixed",
    "local_criteria_only",
)


def _activity_help() -> None:
    clear_screen()
    print_menu_header("Activity Help")
    print("An Activity is the durable collaboration context for classroom work.")
    print("Every Activity has at least one Session.")
    print("Groups, Memberships, Roles, and Responsibilities stay contextual.")
    print("Assignment does not itself prove authorship, contribution, or performance.")
    print()
    pause_for_user()


def _selection_help() -> None:
    clear_screen()
    print_menu_header("Activity Selection Help")
    print("Choose the Activity you want to open.")
    print("Only compact identity and status information is shown here.")
    print("N/P change pages when more than ten Activities are available.")
    print()
    pause_for_user()


def _selection_hint(page_index: int, pages: int) -> str:
    commands: list[str] = []
    if page_index + 1 < pages:
        commands.append("N")
    if page_index > 0:
        commands.append("P")
    commands.extend(("H", "B", "M", "Q"))
    if len(commands) == 1:
        suffix = commands[0]
    elif len(commands) == 2:
        suffix = f"{commands[0]} or {commands[1]}"
    else:
        suffix = ", ".join(commands[:-1]) + f", or {commands[-1]}"
    return f"Please choose a listed option, {suffix}."


def _print_summary(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Activity Summary")
    try:
        detail = show_activity(activity.class_id, activity.activity_id)
    except ConcordWorkflowError as error:
        print(f"Activity could not be loaded: {error}")
    else:
        summary = detail.summary
        print(f"Class: {summary.class_id}")
        print(f"Activity: {summary.activity_id}")
        print(f"Title: {summary.title}")
        print(f"Status: {summary.status}")
        print(f"Type: {detail.activity_type}")
        print(f"Scoring: {summary.scoring_orientation}")
        print(f"Sessions: {summary.session_count}")
        print(f"Groups: {summary.group_count}")
        print(f"Snapshot: {summary.snapshot_revision}")
        if detail.description:
            print(f"Description: {detail.description}")
        if detail.focus_standard_ids:
            print(f"Focus Standards: {len(detail.focus_standard_ids)}")
    print()
    pause_for_user()


def _read_context_counts(activity: ActivitySummary) -> None:
    clear_screen()
    print_menu_header("Collaboration Context")
    try:
        sessions = list_sessions(activity.class_id, activity.activity_id)
        groups = list_groups(activity.class_id, activity.activity_id)
        memberships = list_memberships(activity.class_id, activity.activity_id)
        roles = list_roles(activity.class_id, activity.activity_id)
        responsibilities = list_responsibilities(
            activity.class_id, activity.activity_id
        )
    except ConcordWorkflowError as error:
        print(f"Context could not be loaded: {error}")
    else:
        print(f"Sessions: {len(sessions)}")
        print(f"Groups: {len(groups)}")
        print(f"Memberships: {len(memberships)}")
        print(f"Roles: {len(roles)}")
        print(f"Responsibilities: {len(responsibilities)}")
    print()
    pause_for_user()


def _choose_activity_type() -> str:
    builtins = tuple(_ACTIVITY_TYPES)
    labels = tuple(item.replace("_", " ").title() for item in builtins)
    clear_screen()
    print_menu_header("Activity Type")
    for index, label in enumerate(labels, start=1):
        print(f"{index}. {label}")
    print("4. Custom namespaced type")
    print_navigation()
    print()
    while True:
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Activity Type Help")
            print("Choose a built-in type or enter a valid namespaced extension key.")
            print()
            pause_for_user()
            return _choose_activity_type()
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw.isdigit():
            index = int(raw)
            if 1 <= index <= len(builtins):
                return builtins[index - 1]
            if index == 4:
                custom = prompt_text(
                    "Custom Activity Type",
                    "Activity type",
                    help_text="Enter a valid namespace-qualified Activity type key.",
                )
                assert custom is not None
                return custom
        print(navigation_hint_with_help())
        pause_for_user()
        return _choose_activity_type()


def _choose_scoring_orientation() -> str:
    labels = (
        "Evidence only - collect collaboration evidence without Scores",
        "Standards based - use Core Focus Standards",
        "Mixed - standards plus local criteria later",
        "Local criteria only - no Core standards required",
    )
    return select_one(
        "Scoring Orientation",
        _SCORING_ORIENTATIONS,
        labels,
        help_text=(
            "Scoring orientation controls what kinds of later Concord scoring "
            "records may be added. Concord does not calculate Grades."
        ),
    )


def _standards_selection(
    orientation: str,
) -> tuple[StandardsLibrary | None, str | None, tuple[str, ...]]:
    if orientation not in {"standards_based", "mixed"}:
        return None, None, ()
    library = load_menu_standards_library()
    if library is None:
        raise ConcordWorkflowError(
            "A Core standards library is required for this scoring orientation."
        )
    profile = choose_standards_profile(library)
    standards = choose_focus_standards(library, profile)
    return library, profile.profile_id, standards


def _create_activity(state: MenuSessionContext) -> None:
    try:
        root = resolve_read_workspace_root()
        classes: tuple[ClassSummary, ...]
        if root is None:
            # Workspace mutation is allowed here; class creation remains Core-owned.
            classes = ()
        else:
            classes = list_available_classes(root)
        if not classes:
            show_result(
                "Create an Activity",
                (
                    "No classes are available yet.",
                    "Create or import the class and roster through Paper Data Suite,",
                    "then return here.",
                ),
            )
            return
        selected_class = choose_class(classes)
        title = prompt_text(
            "Create an Activity",
            "Title",
            help_text="Use the teacher-facing Activity title.",
        )
        assert title is not None
        activity_id = prompt_text(
            "Create an Activity",
            "Activity ID",
            help_text="The durable Activity ID may be edited before creation.",
            default=slug_identifier(title, "activity"),
        )
        assert activity_id is not None
        activity_type = _choose_activity_type()
        orientation = _choose_scoring_orientation()
        library, profile_id, focus_ids = _standards_selection(orientation)
        description = prompt_text(
            "Create an Activity",
            "Description",
            help_text="Optional short description of the Activity.",
            optional=True,
        )
        session_id = prompt_text(
            "First Session",
            "Session ID",
            help_text="Every Activity is created atomically with its first Session.",
            default=slug_identifier(f"{activity_id}-session-1", "session-1"),
        )
        assert session_id is not None
        session_label = prompt_text(
            "First Session",
            "Session label",
            help_text="Optional teacher-facing label for the first Session.",
            optional=True,
        )
        actor = state.require_actor()
        review = [
            f"Class: {selected_class.class_id}",
            f"Activity: {title}",
            f"Activity ID: {activity_id}",
            f"Type: {activity_type}",
            f"Scoring: {orientation}",
            f"First Session: {session_label or session_id}",
        ]
        if focus_ids:
            review.append(f"Focus Standards: {len(focus_ids)}")
        if not confirm_write("Create an Activity", "CREATE", tuple(review)):
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
        lines = []
        if result.commit.workspace_created:
            lines.append("Created the Paper Data Suite workspace.")
        lines.extend(
            (
                "Activity created.",
                f"Activity: {result.activity_id}",
                f"First Session: {result.first_session_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            )
        )
        show_result("Activity Result", tuple(lines))
    except CancelMenuAction:
        return
    except ConcordStoragePartialSuccessError as error:
        show_partial_success(error)
    except Exception as error:
        show_result("Activity Error", (str(error),))


def _copy_title(source_title: str) -> TextUpdate:
    while True:
        clear_screen()
        print_menu_header("Copy Activity Title")
        print(f"Source: {source_title}")
        print()
        print("1. Keep source title")
        print("2. Replace title")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Copy Activity Title Help")
            print("Keep the source title as a reviewed copied value, or replace it.")
            print("Either choice affects only the new Activity.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            return UNSET
        if raw == "2":
            replacement = prompt_text(
                "Copy Activity Title",
                "New title",
                help_text=(
                    "Enter the starting teacher-facing title for the new Activity."
                ),
            )
            assert replacement is not None
            return replacement
        print(navigation_hint_with_help())
        pause_for_user()


def _copy_description(source_description: str | None) -> OptionalTextUpdate:
    while True:
        clear_screen()
        print_menu_header("Copy Activity Description")
        source_label = source_description if source_description is not None else "-"
        print(f"Source: {source_label}")
        print()
        print("1. Keep source description")
        print("2. Replace description")
        print("3. Clear description")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Copy Activity Description Help")
            print("Choose whether the new Activity starts with the source description,")
            print("a replacement, or no description. The source is never changed.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw == "1":
            return UNSET
        if raw == "2":
            replacement = prompt_text(
                "Copy Activity Description",
                "New description",
                help_text="Enter the starting description for the new Activity.",
            )
            assert replacement is not None
            return replacement
        if raw == "3":
            return None
        print(navigation_hint_with_help())
        pause_for_user()


def _copy_review_lines(prepared: PreparedActivityCopy) -> tuple[str, ...]:
    privacy = (
        prepared.privacy_policy.classification
        if prepared.privacy_policy is not None
        else "none"
    )
    description = prepared.description if prepared.description is not None else "-"
    lines = [
        f"Source: {prepared.source_class_id}/{prepared.source_activity_id}",
        f"Source status (not copied): {prepared.source_status}",
        f"Target: {prepared.target_class_id}/{prepared.target_activity_id}",
        f"Title: {prepared.title}",
        f"Description: {description}",
        f"Type / scoring: {prepared.activity_type} / {prepared.scoring_orientation}",
        f"Target privacy: {privacy}",
        f"First Session: {prepared.first_session_label or prepared.first_session_id}",
    ]
    if prepared.standards_profile_id is not None:
        lines.append(f"Standards profile: {prepared.standards_profile_id}")
        lines.append("Focus Standards (ordered):")
        lines.extend(
            f"  {index}. {standard_id}"
            for index, standard_id in enumerate(prepared.focus_standard_ids, start=1)
        )
    for diagnostic in prepared.diagnostics:
        lines.append(f"Notice: {diagnostic.message}")
    lines.extend(
        (
            "NOT COPIED: source Sessions/Groups/Memberships/GroupPlans/signals/roles",
            "NOT COPIED: Packets/Artifacts/routes/scans/evidence/reviews/moderation",
            "NOT COPIED: Criterion Sets/Scales/Scores/publications/history/provenance",
            f"Review digest: {prepared.review_digest}",
        )
    )
    return tuple(lines)


def _confirm_copy(lines: tuple[str, ...]) -> bool:
    while True:
        clear_screen()
        print_menu_header("Copy an Activity")
        for line in lines:
            print(line)
        print()
        print(
            "Type COPY exactly to create the independent Activity, "
            "or Enter to cancel."
        )
        print_navigation()
        print()
        raw = input("Confirmation: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            clear_screen()
            print_menu_header("Copy an Activity Help")
            print("COPY creates a new draft Activity and one fresh planned Session.")
            print("It does not clone prior classroom state or history.")
            print()
            pause_for_user()
            continue
        if navigation is NavigationChoice.BACK or not raw:
            return False
        if raw == "COPY":
            return True
        print("Type uppercase COPY exactly, or use H, B, M, or Q.")
        pause_for_user()


def _copy_activity(state: MenuSessionContext) -> None:
    try:
        root = resolve_read_workspace_root()
        if root is None:
            show_result(
                "Copy an Activity",
                ("The Paper Data Suite workspace does not exist yet.",),
            )
            return
        classes = list_available_classes(root)
        activities = list_activities(workspace_root=root)
        if not classes or not activities:
            show_result(
                "Copy an Activity",
                ("An existing Core class and source Concord Activity are required.",),
            )
            return
        source = select_one(
            "Copy Source Activity",
            activities,
            tuple(
                f"{item.title} ({item.class_id} / {item.activity_id}) - {item.status}"
                for item in activities
            ),
            help_text=(
                "Choose the exact canonical Activity whose configuration "
                "starts the copy."
            ),
        )
        detail = show_activity(source.class_id, source.activity_id, workspace_root=root)
        target_class = choose_class(classes)
        target_id = prompt_text(
            "Copy an Activity",
            "New Activity ID",
            help_text="Choose a fresh class-qualified Activity ID for the target.",
            default=slug_identifier(f"{source.activity_id}-copy", "activity-copy"),
        )
        assert target_id is not None
        title = _copy_title(detail.summary.title)
        description = _copy_description(detail.description)
        session_id = prompt_text(
            "Copy an Activity",
            "First Session ID",
            help_text="The copied Activity receives one fresh planned Session.",
            default=slug_identifier(f"{target_id}-session-1", "session-1"),
        )
        assert session_id is not None
        session_label = prompt_text(
            "Copy an Activity",
            "First Session label",
            help_text="Optional target-only label; no source Session label is copied.",
            optional=True,
        )
        library = load_menu_standards_library()
        prepare_request = PrepareActivityCopyRequest(
            source_class_id=source.class_id,
            source_activity_id=source.activity_id,
            target_class_id=target_class.class_id,
            target_activity_id=target_id,
            first_session_id=session_id,
            title=title,
            description=description,
            first_session_label=session_label,
        )
        prepared = prepare_activity_copy(
            prepare_request,
            workspace_root=root,
            standards_library=library,
        )
        if not _confirm_copy(_copy_review_lines(prepared)):
            return
        result = copy_activity(
            CopyActivityRequest(
                source_class_id=prepare_request.source_class_id,
                source_activity_id=prepare_request.source_activity_id,
                target_class_id=prepare_request.target_class_id,
                target_activity_id=prepare_request.target_activity_id,
                first_session_id=prepare_request.first_session_id,
                actor=state.require_actor(),
                review_digest=prepared.review_digest,
                title=prepare_request.title,
                description=prepare_request.description,
                first_session_label=prepare_request.first_session_label,
            ),
            workspace_root=root,
            standards_library=library,
        )
        show_result(
            "Activity Copy Result",
            (
                "Independent draft Activity created.",
                f"Activity: {result.activity_id}",
                f"First Session: {result.first_session_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except ConcordStoragePartialSuccessError as error:
        show_partial_success(error)
    except Exception as error:
        show_result("Activity Copy Error", (str(error),))


def _update_activity_field(
    activity: ActivitySummary,
    state: MenuSessionContext,
    field: str,
) -> None:
    try:
        detail = show_activity(activity.class_id, activity.activity_id)
        current = detail.summary
        values: dict[str, object] = {
            "class_id": current.class_id,
            "activity_id": current.activity_id,
            "expected_snapshot_revision": current.snapshot_revision,
            "actor": state.require_actor(),
        }
        library: StandardsLibrary | None = None
        change = field.replace("_", " ").title()
        if field == "title":
            value = prompt_text(
                "Edit Activity",
                "Title",
                help_text="Change only the teacher-facing Activity title.",
                default=current.title,
            )
            assert value is not None
            values["title"] = value
        elif field == "description":
            values["description"] = prompt_text(
                "Edit Activity",
                "Description",
                help_text="Change or add the short Activity description.",
                default=detail.description,
                optional=True,
            )
        elif field == "status":
            value = prompt_text(
                "Edit Activity",
                "Status",
                help_text=(
                    "Valid statuses include draft, configured, active, completed, "
                    "cancelled, and archived."
                ),
                default=current.status,
            )
            assert value is not None
            values["status"] = value
        elif field == "activity_type":
            values["activity_type"] = _choose_activity_type()
        elif field == "scoring_orientation":
            orientation = _choose_scoring_orientation()
            library, profile_id, focus_ids = _standards_selection(orientation)
            values["scoring_orientation"] = orientation
            values["standards_profile_id"] = profile_id
            values["focus_standard_ids"] = focus_ids
        else:
            raise ConcordWorkflowError(f"Unsupported Activity edit field: {field}")
        if not confirm_write(
            "Edit Activity",
            "UPDATE",
            (f"Activity: {current.title}", f"Change: {change}"),
        ):
            return
        result = update_activity(
            UpdateActivityRequest(**values),  # type: ignore[arg-type]
            standards_library=library,
        )
        show_result(
            "Activity Result",
            (
                "No changes were needed." if result.commit.no_op else "Activity saved.",
                f"Activity: {result.activity_id}",
                f"Snapshot: {result.commit.snapshot_revision}",
            ),
        )
    except CancelMenuAction:
        return
    except Exception as error:
        handle_write_error(
            error,
            reload=lambda: show_activity(activity.class_id, activity.activity_id),
            error_title="Activity Error",
        )


def _edit_activity(activity: ActivitySummary, state: MenuSessionContext) -> None:
    while True:
        clear_screen()
        print_menu_header("Edit Activity")
        print(f"Activity: {activity.title}")
        print()
        print("1. Title")
        print("2. Description")
        print("3. Status")
        print("4. Activity type")
        print("5. Scoring orientation / Focus Standards")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _activity_help()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _update_activity_field(activity, state, "title")
            return
        elif choice == "2":
            _update_activity_field(activity, state, "description")
            return
        elif choice == "3":
            _update_activity_field(activity, state, "status")
            return
        elif choice == "4":
            _update_activity_field(activity, state, "activity_type")
            return
        elif choice == "5":
            _update_activity_field(activity, state, "scoring_orientation")
            return
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def launch_activity_context_menu(
    activity: ActivitySummary,
    state: MenuSessionContext | None = None,
) -> None:
    """Open one Activity with only essential persistent context in the header."""
    session_state = MenuSessionContext() if state is None else state
    while True:
        try:
            activity = show_activity(activity.class_id, activity.activity_id).summary
        except ConcordWorkflowError:
            pass
        clear_screen()
        print_menu_header(f"Activity: {activity.title}")
        print(f"Class: {activity.class_id}")
        print(f"Status: {activity.status}")
        print()
        print("1. View Activity summary")
        print("2. View collaboration counts")
        print("3. Sessions")
        print("4. Groups and participants")
        print("5. Roles")
        print("6. Responsibilities")
        print("7. Artifact Pages")
        print("8. Scoring")
        print("9. Publication")
        print("10. Edit Activity")
        print("11. Prepare / Generate Packet")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _activity_help()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _print_summary(activity)
        elif choice == "2":
            _read_context_counts(activity)
        elif choice == "3":
            launch_session_menu(activity, session_state)
        elif choice == "4":
            launch_group_menu(activity, session_state)
        elif choice == "5":
            launch_role_menu(activity, session_state)
        elif choice == "6":
            launch_responsibility_menu(activity, session_state)
        elif choice == "7":
            launch_artifact_page_menu(activity, session_state)
        elif choice == "8":
            launch_scoring_menu(activity, session_state)
        elif choice == "9":
            launch_publication_menu(activity, session_state)
        elif choice == "10":
            _edit_activity(activity, session_state)
        elif choice == "11":
            launch_packet_generation_menu(activity, session_state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()


def select_activity() -> ActivitySummary | None:
    """Select one Activity from a paginated compact list."""
    try:
        root = resolve_read_workspace_root()
        classes: tuple[ClassSummary, ...]
        if root is None:
            clear_screen()
            print_menu_header("Open an Activity")
            print("The Paper Data Suite workspace does not exist yet.")
            print()
            pause_for_user()
            return None
        classes = list_available_classes(root)
        if not classes:
            clear_screen()
            print_menu_header("Open an Activity")
            print("No classes are available yet.")
            print()
            print("Create or import the class and roster through Paper Data Suite,")
            print("then return here.")
            print()
            pause_for_user()
            return None
        activities = list_activities(workspace_root=root)
    except (ConcordWorkflowError, WorkspaceRootError) as error:
        clear_screen()
        print_menu_header("Open an Activity")
        print(f"Activities could not be loaded: {error}")
        print()
        pause_for_user()
        return None
    if not activities:
        clear_screen()
        print_menu_header("Open an Activity")
        print("No Concord Activities are available yet.")
        print()
        pause_for_user()
        return None

    page_index = 0
    while True:
        clear_screen()
        print_menu_header("Open an Activity")
        page = page_items(activities, page_index)
        for index, activity in enumerate(page, start=1):
            print(
                f"{index}. {activity.title} "
                f"({activity.class_id} / {activity.activity_id}) - {activity.status}"
            )
        pages = page_count(len(activities))
        if pages > 1:
            print()
            print(f"Page {page_index + 1} of {pages}")
            if page_index + 1 < pages:
                print("N. Next page")
            if page_index > 0:
                print("P. Previous page")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _selection_help()
            continue
        if navigation is NavigationChoice.BACK:
            return None
        normalized = choice.casefold()
        if normalized == "n" and page_index + 1 < pages:
            page_index += 1
            continue
        if normalized == "p" and page_index > 0:
            page_index -= 1
            continue
        if choice.isdigit():
            selected = int(choice)
            if 1 <= selected <= len(page):
                return page[selected - 1]
        print(_selection_hint(page_index, pages))
        pause_for_user()


def launch_activity_management_menu(
    state: MenuSessionContext | None = None,
) -> None:
    """Run Activity creation, listing, and open-Activity workflows."""
    session_state = MenuSessionContext() if state is None else state
    while True:
        clear_screen()
        print_menu_header("Activity Management")
        print("1. Create an Activity")
        print("2. Copy an Activity")
        print("3. List Activities")
        print("4. Open an Activity")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        if navigation is ConcordMenuChoice.HELP:
            _activity_help()
        elif navigation is NavigationChoice.BACK:
            return
        elif choice == "1":
            _create_activity(session_state)
        elif choice == "2":
            _copy_activity(session_state)
        elif choice == "3":
            activity = select_activity()
            if activity is not None:
                _print_summary(activity)
        elif choice == "4":
            activity = select_activity()
            if activity is not None:
                launch_activity_context_menu(activity, session_state)
        else:
            print(navigation_hint_with_help())
            pause_for_user()
