"""Teacher-facing Artifact Page preparation and rendering workflow."""

from __future__ import annotations

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
    prompt_positive_int,
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
from concord.models import PrivacyPolicy
from concord.routing.rendering import (
    RenderArtifactPagesRequest,
    RenderPartialSuccessError,
    render_artifact_pages,
)
from concord.workflows import ActivitySummary, show_activity
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    ArtifactRoutePreparationPartialSuccessError,
    PrepareArtifactPagesRequest,
    list_artifact_pages,
    prepare_artifact_pages,
)


def _handle_error(activity: ActivitySummary, error: Exception) -> None:
    if isinstance(error, ArtifactRoutePreparationPartialSuccessError):
        result = error.result
        show_result(
            "Artifact Preparation Partial Success",
            (
                "Artifact/Page snapshot was published.",
                f"Snapshot: {result.commit.snapshot_revision}",
                f"Snapshot SHA-256: {result.commit.snapshot_sha256}",
                f"Routes verified: {result.routes_verified}/{result.routes_expected}",
                "Review canonical routes before retrying preparation.",
            ),
        )
        return
    if isinstance(error, RenderPartialSuccessError):
        show_result(
            "Artifact Render Partial Success",
            (
                "Rendered output is installed and durable.",
                f"Output: {error.output_path.name}",
                "Canonical lifecycle update is incomplete.",
                "Review canonical state before retrying rendering.",
            ),
        )
        return
    handle_write_error(
        error,
        reload=lambda: show_activity(activity.class_id, activity.activity_id),
        error_title="Artifact Page Error",
    )


def _prepare(activity: ActivitySummary, state: MenuSessionContext) -> None:
    artifact_id = prompt_text(
        "Prepare Artifact Pages",
        "Artifact Instance ID",
        help_text="Enter a durable synthetic identifier for this physical page set.",
    )
    template_id = prompt_text(
        "Prepare Artifact Pages",
        "Template version ID",
        help_text="Identify the template version used for this page set.",
    )
    count = prompt_positive_int(
        "Prepare Artifact Pages",
        "Physical page count",
        help_text="Each physical page receives its own durable route.",
        default=1,
    )
    assert artifact_id is not None and template_id is not None
    if not confirm_write(
        "Prepare Artifact Pages",
        "CREATE",
        (f"Activity: {activity.title}", f"Artifact: {artifact_id}", f"Pages: {count}"),
    ):
        return
    result = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=activity.class_id,
            activity_id=activity.activity_id,
            artifact_instance_id=artifact_id,
            template_version_id=template_id,
            artifact_category="student_work",
            expected_snapshot_revision=activity.snapshot_revision,
            actor=state.require_actor(),
            pages=tuple(
                ArtifactPagePlan(page_number=index) for index in range(1, count + 1)
            ),
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        )
    )
    show_result(
        "Artifact Pages Prepared",
        (
            f"Artifact: {result.artifact_instance_id}",
            f"Routes verified: {result.routes_verified}/{result.routes_expected}",
            f"Snapshot: {result.commit.snapshot_revision}",
        ),
    )


def _list(activity: ActivitySummary) -> None:
    pages = list_artifact_pages(activity.class_id, activity.activity_id)
    if not pages:
        clear_screen()
        print_menu_header("Artifact Pages")
        print("No Artifact Pages have been prepared.")
        print()
        pause_for_user()
        return
    page = select_one(
        "Artifact Pages",
        pages,
        [
            f"{item.artifact_page_id}  page {item.page_number}  [{item.page_status}]"
            for item in pages
        ],
        help_text="Navigate every prepared page, then choose one for compact detail.",
    )
    show_result(
        "Artifact Page Detail",
        (
            f"Page: {page.artifact_page_id}",
            f"Artifact: {page.artifact_instance_id}",
            f"Physical page: {page.page_number}",
            f"Status: {page.page_status}",
            f"Route: {page.route_id or '-'}",
        ),
    )


def _render(activity: ActivitySummary, state: MenuSessionContext) -> None:
    artifact_id = prompt_text(
        "Render Artifact Pages",
        "Artifact Instance ID",
        help_text="Enter an already prepared Artifact Instance ID.",
    )
    assert artifact_id is not None
    if not confirm_write(
        "Render Artifact Pages",
        "RENDER",
        (f"Activity: {activity.title}", f"Artifact: {artifact_id}"),
    ):
        return
    result = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id=activity.class_id,
            activity_id=activity.activity_id,
            artifact_instance_id=artifact_id,
            expected_snapshot_revision=activity.snapshot_revision,
            actor=state.require_actor(),
        )
    )
    show_result(
        "Artifact Pages Rendered",
        (
            f"Artifact: {result.artifact_instance_id}",
            f"Pages: {result.page_count}",
            f"Output: {result.output_path.name}",
        ),
    )


def launch_artifact_page_menu(
    activity: ActivitySummary, state: MenuSessionContext
) -> None:
    while True:
        clear_screen()
        print_menu_header("Artifact Pages")
        print(f"Activity: {activity.title}")
        print()
        print("1. Prepare Artifact Pages")
        print("2. List / inspect Artifact Pages")
        print("3. Render prepared pages")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Artifact Page Help", ("Pages are canonical before QR rendering.",)
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _prepare(activity, state)
                return
            elif choice == "2":
                _list(activity)
            elif choice == "3":
                _render(activity, state)
                return
            else:
                print(navigation_hint_with_help())
                pause_for_user()
        except CancelMenuAction:
            return
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except Exception as error:
            _handle_error(activity, error)
            return


__all__ = ["launch_artifact_page_menu"]
