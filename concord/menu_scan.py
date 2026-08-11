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
from pds_core.routing_models import PDS2_SCHEMA, ModuleWorkRef, RouteLocator
from pds_core.scan_failure_metadata import (
    RoutingFailureMetadataReadError,
    RoutingFailureMetadataWriteError,
)
from pds_core.scan_resolution_metadata import (
    ScanResolutionMetadataReadError,
    ScanResolutionMetadataWriteError,
)
from pds_core.workspace import WorkspaceRootError

from concord.menu_context import CancelMenuAction, MenuSessionContext
from concord.menu_navigation import (
    ConcordMenuChoice,
    NavigationChoice,
    QuitPDS,
    ReturnToMainMenu,
    parse_menu_navigation,
)
from concord.menu_prompts import confirm_write, prompt_text, select_one, show_result
from concord.menu_ui import (
    clear_screen,
    pause_for_user,
    print_menu_header,
    print_navigation,
)
from concord.routing.review import (
    RoutingResolutionPartialSuccessError,
    defer_routing_failure,
    list_routing_failures,
    resolve_routing_failure_with_route,
)
from concord.routing.scan_intake import route_scan_sources
from concord.storage_errors import ConcordStorageError
from concord.workflows import ConcordWorkflowError


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
    raw = prompt_text(
        "Route Scans",
        "Source file paths (semicolon separated)",
        help_text=(
            "Each selected file is retained once before its physical pages are decoded."
        ),
    )
    assert raw is not None
    sources = tuple(Path(item.strip()) for item in raw.split(";") if item.strip())
    if not confirm_write("Route Scans", "ROUTE", (f"Source files: {len(sources)}",)):
        return
    result = route_scan_sources(sources)
    show_result(
        "Scan Routing Complete",
        (
            f"Sources: {len(result.sources)}",
            f"Dispatched: {result.dispatched_count}",
            f"Review required: {result.failure_count}",
        ),
    )


def _review(state: MenuSessionContext) -> None:
    failures = list_routing_failures()
    if not failures:
        clear_screen()
        print_menu_header("Routing Review")
        print("No routing failures found.")
        print()
        pause_for_user()
        return
    failure = select_one(
        "Routing Review",
        failures,
        [
            f"{item.failure_id}  {item.category}  "
            f"{item.latest_status or 'unresolved'}"
            for item in failures
        ],
        help_text="Navigate all failures and choose one exact listed identity.",
    )
    failure_id = failure.failure_id
    action = prompt_text(
        "Routing Review",
        "Action (defer or route)",
        help_text=(
            "Defer preserves the failure for later; route requires an exact route."
        ),
    )
    message = prompt_text(
        "Routing Review",
        "Resolution note",
        help_text="Record a concise teacher rationale.",
    )
    assert failure_id is not None and action is not None and message is not None
    locator: RouteLocator | None = None
    if action.casefold() == "route":
        class_id = prompt_text(
            "Select Exact Route",
            "Class ID",
            help_text="Enter the exact Core class identity.",
        )
        work_id = prompt_text(
            "Select Exact Route",
            "Work ID",
            help_text="For Concord this is the exact Activity ID.",
        )
        route_id = prompt_text(
            "Select Exact Route",
            "Route ID",
            help_text="The route must already exist and be active.",
        )
        assert all(item is not None for item in (class_id, work_id, route_id))
        locator = RouteLocator(
            PDS2_SCHEMA,
            ModuleWorkRef("concord", str(class_id), str(work_id)),
            str(route_id),
        )
    elif action.casefold() != "defer":
        show_result("Routing Review", ("Action must be defer or route.",))
        return
    if not confirm_write(
        "Resolve Routing Failure",
        "RESOLVE",
        (f"Failure: {failure_id}", f"Action: {action.casefold()}"),
    ):
        return
    actor = state.require_actor()
    if locator is None:
        result = defer_routing_failure(failure_id, message=message, reviewer=actor)
    else:
        try:
            result = resolve_routing_failure_with_route(
                failure_id,
                locator,
                message=message,
                reviewer=actor,
            )
        except RoutingResolutionPartialSuccessError as error:
            _show_routing_partial(error)
            return
    show_result(
        "Routing Resolution Saved",
        (
            f"Resolution: {result.resolution_id}",
            f"Action: {result.resolution_action}",
        ),
    )


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
