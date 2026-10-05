"""Global teacher-facing retained-scan routing surface."""

from __future__ import annotations

from pathlib import Path

from pds_core.module_dispatch import ModuleDispatchError
from pds_core.module_profiles import (
    ModuleDiscoveryError,
    ModuleRegistryError,
    UnsupportedModuleError,
)
from pds_core.route_registrations import RouteRegistrationPersistenceError
from pds_core.routing_models import ModuleWorkRef, RouteLocator
from pds_core.scan_failure_metadata import (
    RoutingFailureMetadataReadError,
    RoutingFailureMetadataWriteError,
)
from pds_core.scan_resolution_metadata import (
    ScanResolutionMetadataReadError,
    ScanResolutionMetadataWriteError,
)
from pds_core.scan_routes import scans_inbox_dir
from pds_core.workspace import WorkspaceRootError, inspect_workspace_root

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    QuitPDS,
    ReturnToMainMenu,
    navigation_hint_with_help,
    parse_menu_navigation,
)
from concord.menu_prompts import confirm_write, prompt_text, select_one, show_result
from concord.menu_ui import (
    clear_screen,
    page_count,
    page_items,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.routing.candidates import ConcordRouteCandidate
from concord.routing.destinations import (
    list_routing_destination_activities,
    list_routing_destination_classes,
    project_routing_destination_candidates,
    routing_destination_activity_label,
    routing_destination_candidate_label,
    routing_destination_class_label,
)
from concord.routing.review import (
    RoutingFailureReview,
    RoutingResolutionPartialSuccessError,
    defer_routing_failure,
    list_routing_failures,
    resolve_routing_failure_with_route,
    review_routing_failure,
    routing_failure_summary_label,
)
from concord.routing.scan_intake import (
    SUPPORTED_SCAN_EXTENSIONS,
    ScanBatchResult,
    route_scan_sources,
)
from concord.storage_errors import ConcordStorageError
from concord.workflows import ConcordWorkflowError


def _scan_inbox_sources(
    workspace_root: str | Path,
) -> tuple[Path, tuple[Path, ...]]:
    """Return the shared inbox and its routable top-level regular files."""
    inbox = scans_inbox_dir(workspace_root)
    if not inbox.exists():
        return inbox, ()
    if not inbox.is_dir():
        raise NotADirectoryError(
            f"Shared scan inbox is not a directory: {inbox}"
        )
    sources = tuple(
        sorted(
            (
                path
                for path in inbox.iterdir()
                if not path.is_symlink()
                and path.is_file()
                and path.suffix.casefold() in SUPPORTED_SCAN_EXTENSIONS
            ),
            key=lambda path: (path.name.casefold(), path.name),
        )
    )
    return inbox, sources


def _custom_route_sources() -> tuple[Path, ...]:
    """Collect one or more explicit power-user scan sources."""
    while True:
        raw = prompt_text(
            "Route Scans — Custom Path",
            "Source file/folder paths (semicolon separated)",
            help_text=(
                "Enter one or more explicit scan files or folders. "
                "Separate several sources with semicolons."
            ),
        )
        assert raw is not None
        sources = tuple(
            Path(item.strip())
            for item in raw.split(";")
            if item.strip()
        )
        if sources:
            return sources
        show_result(
            "Route Scans — Custom Path",
            ("Enter at least one file or folder path.",),
        )


def _choose_route_sources() -> tuple[Path, ...]:
    """Choose one exact inbox scan or explicit custom source paths."""
    status = inspect_workspace_root()
    if status.exists and not status.is_dir:
        raise WorkspaceRootError(
            f"Workspace root is not a directory: {status.root}"
        )
    workspace_root = status.root
    page_index = 0
    while True:
        inbox, sources = _scan_inbox_sources(workspace_root)
        pages = page_count(len(sources))
        page_index = min(page_index, pages - 1)
        visible = page_items(sources, page_index)

        clear_screen()
        print_menu_header("Scan Routing — Route Scans")
        print("Scan inbox:")
        print(inbox)
        print()
        if visible:
            print("Available scans:")
            print()
            for index, source in enumerate(visible, start=1):
                print(f"{index}. {source.name}")
        else:
            print("No supported scans were found.")
            print()
            print(
                "Place scanned PDFs or images in the scan inbox, "
                "then choose Refresh."
            )

        if pages > 1:
            print()
            print(f"Page {page_index + 1} of {pages}")
            if page_index + 1 < pages:
                print("N. Next page")
            if page_index > 0:
                print("P. Previous page")

        print()
        print("C. Choose custom file/folder path")
        print("R. Refresh")
        print_navigation()
        print()
        raw = input("Select scan: ").strip()
        navigation = parse_menu_navigation(raw)

        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Route Scans Help",
                (
                    "Choose a listed scan from the shared Paper Data Suite inbox.",
                    "Use Custom Path when a scan is stored somewhere else.",
                    (
                        "Routing retains the source and lets Core PDS2 determine "
                        "page ownership."
                    ),
                    "Browsing and selection do not route or modify scan files.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction

        normalized = raw.casefold()
        if normalized == "r":
            page_index = 0
            continue
        if normalized == "c":
            return _custom_route_sources()
        if normalized == "n" and page_index + 1 < pages:
            page_index += 1
            continue
        if normalized == "p" and page_index > 0:
            page_index -= 1
            continue
        if raw.isdigit():
            selected = int(raw)
            if 1 <= selected <= len(visible):
                return (visible[selected - 1],)

        print(navigation_hint_with_help())
        pause_for_user()


def _show_scan_batch_result(result: ScanBatchResult) -> None:
    """Show truthful routing counts plus any source-level failures."""
    source_errors = tuple(
        source
        for source in result.sources
        if source.source_error is not None
    )
    lines = [
        f"Sources: {len(result.sources)}",
        f"Dispatched: {result.dispatched_count}",
        f"Review required: {result.failure_count}",
    ]
    if source_errors:
        lines.append(f"Source errors: {len(source_errors)}")
        for source in source_errors:
            lines.append(f"{source.source_path}: {source.source_error}")
    show_result(
        (
            "Scan Routing Completed with Source Errors"
            if source_errors
            else "Scan Routing Complete"
        ),
        tuple(lines),
    )


def _show_routing_partial(error: RoutingResolutionPartialSuccessError) -> None:
    partial = error.result
    show_result(
        "Routing Resolution Partial Success",
        (
            "Handler dispatch succeeded: yes",
            "Evidence filing occurred: yes",
            "Resolution metadata persisted: no",
            f"Failure: {partial.failure_id}",
            f"Route: {partial.selected_route.route_id}",
            "Retry only after reviewing the durable filing.",
        ),
    )


def _route() -> None:
    sources = _choose_route_sources()
    review_lines: tuple[str, ...]
    if len(sources) == 1:
        review_lines = (
            f"Source: {sources[0]}",
            (
                "This scan will be retained and its physical pages routed "
                "through Paper Data Suite."
            ),
        )
    else:
        review_lines = (
            f"Source files/folders: {len(sources)}",
            (
                "These sources will be retained and their physical pages routed "
                "through Paper Data Suite."
            ),
        )
    if not confirm_write("Route Scans", "ROUTE", review_lines):
        return
    result = route_scan_sources(sources)
    _show_scan_batch_result(result)


def _select_routing_destination_candidate(
    review: RoutingFailureReview,
) -> ConcordRouteCandidate:
    """Browse teacher-readable routing destinations without writing state."""
    if review.bound_work is not None:
        work = review.bound_work
        projection = project_routing_destination_candidates(review, work)
        activity_title = review.activity_title or work.work_id
    else:
        classes = list_routing_destination_classes(review)
        selected_class = select_one(
            "Select Class",
            classes,
            [routing_destination_class_label(item) for item in classes],
            help_text=(
                "Choose the class that owns the intended Concord Activity. "
                "This browsing step does not change routing state."
            ),
        )
        activities = list_routing_destination_activities(
            review, selected_class.class_id
        )
        selected_activity = select_one(
            "Select Activity",
            activities,
            [routing_destination_activity_label(item) for item in activities],
            help_text=(
                "Choose the Activity that owns the intended physical page. "
                "Only current Concord Activities are listed."
            ),
        )
        work = ModuleWorkRef(
            "concord", selected_class.class_id, selected_activity.activity_id
        )
        projection = project_routing_destination_candidates(review, work)
        activity_title = selected_activity.title

    if not projection.candidates:
        diagnostic_note = (
            f" {len(projection.diagnostics)} page candidate(s) were withheld by "
            "route integrity checks; use Technical details for diagnostics."
            if projection.diagnostics
            else ""
        )
        raise ConcordWorkflowError(
            "No current routable Concord pages are available for this Activity."
            + diagnostic_note
        )

    selected = select_one(
        f"Select Destination — {activity_title}",
        projection.candidates,
        [
            routing_destination_candidate_label(candidate)
            for candidate in projection.candidates
        ],
        help_text=(
            "Choose the exact current Artifact Page for this physical scan page. "
            "Routine labels hide route IDs; no routing change occurs until the "
            "later explicit RESOLVE confirmation."
        ),
    )
    return selected


def _select_routing_destination(review: RoutingFailureReview) -> RouteLocator:
    """Return the exact locator carried by the selected candidate."""
    return _select_routing_destination_candidate(review).locator


def _routing_review_context_lines(
    review: RoutingFailureReview,
) -> tuple[str, ...]:
    failure = review.failure
    page = (
        str(failure.source_page_number)
        if failure.source_page_number is not None
        else "Not available"
    )
    return (
        f"Source: {failure.source_filename}",
        f"Physical page: {page}",
        f"Problem: {review.problem_label}",
        f"Activity: {review.activity_label}",
        f"Status: {review.status_label}",
    )


def _routing_route_unavailable_message(review: RoutingFailureReview) -> str | None:
    reason = review.route_action_unavailable_reason
    if reason is None:
        return None
    messages = {
        "already_resolved": "This routing failure has already been resolved.",
        "known_other_module": (
            "This failed route belongs to another Paper Data Suite module, so "
            "Concord route correction is not available."
        ),
        "known_concord_activity_unavailable": (
            "The exact Concord Activity recorded by this failure is not currently "
            "available, so Concord will not substitute another Activity."
        ),
        "retained_provenance_incomplete": (
            "Retained physical-page provenance is incomplete, so Concord cannot "
            "safely re-dispatch this page."
        ),
    }
    return messages.get(
        reason,
        "Concord route correction is not available for this routing failure.",
    )


def _routing_technical_detail_lines(
    review: RoutingFailureReview,
) -> tuple[str, ...]:
    failure = review.failure
    lines = [
        f"Failure ID: {failure.failure_id}",
        f"Category: {failure.failure_category}",
        f"Stage: {failure.stage}",
        f"Status: {review.status_label}",
        f"Failure message: {failure.failure_message}",
        f"Source scan ID: {failure.source_scan_id or 'Not available'}",
        f"Source SHA-256: {failure.source_sha256 or 'Not available'}",
        f"Retained source path: {failure.retained_source_path or 'Not available'}",
    ]
    locator = failure.route_locator
    if locator is None:
        lines.append("Recorded route: none")
    else:
        lines.extend(
            (
                f"Route module: {locator.module_id}",
                f"Route class: {locator.class_id}",
                f"Route work: {locator.work_id}",
                f"Route ID: {locator.route_id}",
            )
        )
    if failure.target is not None:
        lines.extend(
            (
                f"Target kind: {failure.target.record_kind}",
                f"Target ID: {failure.target.record_id}",
            )
        )
    if review.route_action_unavailable_reason is not None:
        lines.append(
            "Route action status: " + review.route_action_unavailable_reason
        )
        if review.route_action_unavailable_detail:
            lines.append(
                "Route action detail: " + review.route_action_unavailable_detail
            )
    return tuple(lines)


def _show_routing_technical_details(review: RoutingFailureReview) -> None:
    show_result(
        "Routing Review — Technical Details",
        _routing_technical_detail_lines(review),
    )


def _choose_routing_review_action(review: RoutingFailureReview) -> str:
    while True:
        clear_screen()
        print_menu_header("Routing Review")
        for line in _routing_review_context_lines(review):
            print(line)
        unavailable = _routing_route_unavailable_message(review)
        if unavailable is not None:
            print()
            print(unavailable)

        actions: list[tuple[str, str]] = []
        if "route" in review.available_actions:
            actions.append(("route", "Route to an existing Concord page"))
        if "defer" in review.available_actions:
            actions.append(("defer", "Defer for later"))
        if "technical_details" in review.available_actions:
            actions.append(("technical_details", "Technical details"))

        print()
        for index, (_action, label) in enumerate(actions, start=1):
            print(f"{index}. {label}")
        print_navigation()
        print()
        raw = input("Select an option: ").strip()
        navigation = parse_menu_navigation(raw)
        if navigation is ConcordMenuChoice.HELP:
            show_result(
                "Routing Review Help",
                (
                    "Route selects one existing exact Concord Artifact Page.",
                    "Defer keeps this failure available for later review.",
                    "Technical details shows machine identities and diagnostics.",
                    "No routing change occurs until DEFER or RESOLVE is confirmed.",
                ),
            )
            continue
        if navigation is NavigationChoice.BACK:
            raise CancelMenuAction
        if raw.isdigit():
            selected = int(raw) - 1
            if 0 <= selected < len(actions):
                action = actions[selected][0]
                if action == "technical_details":
                    _show_routing_technical_details(review)
                    continue
                return action
        print(navigation_hint_with_help())
        pause_for_user()


def _review(state: MenuSessionContext) -> None:
    while True:
        failures = list_routing_failures()
        if not failures:
            clear_screen()
            print_menu_header("Routing Review")
            print("No routing failures found.")
            print()
            pause_for_user()
            return
        try:
            summary = select_one(
                "Routing Review",
                failures,
                [routing_failure_summary_label(item) for item in failures],
                help_text=(
                    "Choose the retained physical page that needs teacher review. "
                    "Routine rows use source/page context rather than failure IDs."
                ),
            )
        except CancelMenuAction:
            return

        while True:
            review = review_routing_failure(summary.failure_id)
            try:
                action = _choose_routing_review_action(review)
            except CancelMenuAction:
                break

            if action == "defer":
                try:
                    message = prompt_text(
                        "Defer Routing Failure",
                        "Resolution note",
                        help_text=(
                            "Edit the note if useful. Deferring preserves the "
                            "failure for later Routing Review."
                        ),
                        default="Deferred for later teacher review.",
                    )
                except CancelMenuAction:
                    continue
                assert message is not None
                if not confirm_write(
                    "Defer Routing Failure",
                    "DEFER",
                    (
                        *_routing_review_context_lines(review),
                        f"Resolution note: {message}",
                    ),
                ):
                    continue
                result = defer_routing_failure(
                    summary.failure_id,
                    message=message,
                    reviewer=state.require_actor(),
                )
                show_result(
                    "Routing Failure Deferred",
                    (
                        "This failure remains available for later review.",
                        f"Status: {result.resolution_status}",
                    ),
                )
                return

            if action == "route":
                try:
                    candidate = _select_routing_destination_candidate(review)
                    destination_label = routing_destination_candidate_label(candidate)
                    message = prompt_text(
                        "Resolve Routing Failure",
                        "Resolution note",
                        help_text=(
                            "Edit the note if useful. RESOLVE will re-dispatch the "
                            "retained physical page through this exact existing route."
                        ),
                        default=(
                            "Teacher confirmed this retained page belongs to the "
                            "selected existing Concord page."
                        ),
                    )
                except CancelMenuAction:
                    continue
                assert message is not None
                if not confirm_write(
                    "Resolve Routing Failure",
                    "RESOLVE",
                    (
                        *_routing_review_context_lines(review),
                        f"Destination: {destination_label}",
                        f"Resolution note: {message}",
                    ),
                ):
                    continue
                try:
                    result = resolve_routing_failure_with_route(
                        summary.failure_id,
                        candidate.locator,
                        message=message,
                        reviewer=state.require_actor(),
                    )
                except RoutingResolutionPartialSuccessError as error:
                    _show_routing_partial(error)
                    return
                show_result(
                    "Routing Resolution Saved",
                    (
                        "The retained page was routed to the selected Concord page.",
                        f"Destination: {destination_label}",
                        f"Action: {result.resolution_action}",
                    ),
                )
                return

            raise AssertionError(f"unsupported routing review action: {action}")

def launch_scan_routing_menu(state: MenuSessionContext | None = None) -> None:
    session_state = MenuSessionContext() if state is None else state
    while True:
        clear_screen()
        print_menu_header("Scan Routing")
        print("1. Route scans")
        print("2. Routing review")
        print_navigation()
        print()
        choice = input("Select an option: ").strip()
        navigation = parse_menu_navigation(choice)
        try:
            if navigation is ConcordMenuChoice.HELP:
                show_result(
                    "Scan Routing Help",
                    ("Retained physical pages route through Core PDS2.",),
                )
            elif navigation is NavigationChoice.BACK:
                return
            elif choice == "1":
                _route()
            elif choice == "2":
                _review(session_state)
            else:
                pause_for_user()
        except CancelMenuAction:
            continue
        except RoutingResolutionPartialSuccessError as error:
            _show_routing_partial(error)
        except (ReturnToMainMenu, QuitPDS, KeyboardInterrupt, EOFError):
            raise
        except (
            ConcordWorkflowError,
            ConcordStorageError,
            WorkspaceRootError,
            RouteRegistrationPersistenceError,
            RoutingFailureMetadataReadError,
            RoutingFailureMetadataWriteError,
            ScanResolutionMetadataReadError,
            ScanResolutionMetadataWriteError,
            ModuleDispatchError,
            ModuleRegistryError,
            ModuleDiscoveryError,
            UnsupportedModuleError,
            OSError,
            TypeError,
            ValueError,
        ) as error:
            show_result("Scan Routing Error", (str(error),))


__all__ = ["launch_scan_routing_menu"]
