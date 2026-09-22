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
from concord.routing.review import (
    RoutingResolutionPartialSuccessError,
    defer_routing_failure,
    list_routing_failures,
    resolve_routing_failure_with_route,
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
