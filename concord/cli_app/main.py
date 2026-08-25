"""Top-level dispatch and stable exit-code handling for the Concord CLI."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from typing import cast

from pds_core.module_dispatch import ModuleDispatchError
from pds_core.module_profiles import ModuleDiscoveryError, ModuleRegistryError
from pds_core.registry_services import (
    RegistryServiceConflictError,
    RegistryServiceError,
    RegistryServicePartialSuccessError,
)
from pds_core.route_registrations import RouteRegistrationPersistenceError
from pds_core.scan_failure_metadata import (
    RoutingFailureMetadataReadError,
    RoutingFailureMetadataWriteError,
)
from pds_core.scan_resolution_metadata import (
    ScanResolutionMetadataReadError,
    ScanResolutionMetadataWriteError,
)
from pds_core.workspace import WorkspaceRootError

from concord.academic_result_manifest_generation import (
    ConcordManifestGenerationConflictError,
    ConcordManifestGenerationError,
    ConcordManifestGenerationPartialSuccessError,
)
from concord.academic_result_publication import (
    ConcordAcademicResultPublicationConflictError,
    ConcordAcademicResultPublicationError,
    ConcordAcademicResultPublicationPartialSuccessError,
)
from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationError,
)
from concord.cli_app.parser import build_parser
from concord.packet_storage import PacketStoragePartialSuccessError
from concord.routing.rendering import RenderPartialSuccessError
from concord.routing.review import RoutingResolutionPartialSuccessError
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStorageError,
    ConcordStoragePartialSuccessError,
)
from concord.template_storage import TemplateStoragePartialSuccessError
from concord.workflows import ConcordWorkflowConflictError, ConcordWorkflowError
from concord.workflows.artifact_page import ArtifactRoutePreparationPartialSuccessError
from concord.workflows.starter_template import (
    StarterTemplateInstallAllPartialSuccessError,
)

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_CONFLICT = 3
EXIT_PARTIAL_SUCCESS = 4

CommandHandler = Callable[[argparse.Namespace], int]


def _print_partial_success(error: ConcordStoragePartialSuccessError) -> None:
    print(f"Partial success: {error}", file=sys.stderr)
    print(
        f"Current pointer published: {'yes' if error.pointer_published else 'no'}",
        file=sys.stderr,
    )
    if error.snapshot_revision is not None:
        print(f"Snapshot revision: {error.snapshot_revision}", file=sys.stderr)
    if error.snapshot_sha256 is not None:
        print(f"Snapshot SHA-256: {error.snapshot_sha256}", file=sys.stderr)
    if error.durable_paths:
        print(f"Durable paths: {len(error.durable_paths)}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and dispatch direct Concord commands without interactive prompts."""
    effective_argv = tuple(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not effective_argv:
        from concord.menu import launch_menu

        return launch_menu()

    args = parser.parse_args(effective_argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_OK

    try:
        return cast(CommandHandler, handler)(args)
    except ConcordAcademicResultPublicationPartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(
            f"Canonical state: {error.state.canonical_state}",
            file=sys.stderr,
        )
        print(error.state.recommended_next_action, file=sys.stderr)
        return EXIT_PARTIAL_SUCCESS
    except ConcordManifestGenerationPartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(f"Manifest revision: {error.state.revision}", file=sys.stderr)
        return EXIT_PARTIAL_SUCCESS
    except RegistryServicePartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        return EXIT_PARTIAL_SUCCESS
    except (
        ConcordAcademicResultPublicationConflictError,
        ConcordManifestGenerationConflictError,
        RegistryServiceConflictError,
    ) as error:
        print(f"Conflict: {error}", file=sys.stderr)
        return EXIT_CONFLICT
    except ConcordAcademicWorkRegistrationError as error:
        name = error.__class__.__name__
        if name.endswith("PartialSuccessError"):
            print(f"Partial success: {error}", file=sys.stderr)
            return EXIT_PARTIAL_SUCCESS
        if name.endswith("ConflictError"):
            print(f"Conflict: {error}", file=sys.stderr)
            return EXIT_CONFLICT
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except (
        ConcordAcademicResultPublicationError,
        ConcordManifestGenerationError,
        RegistryServiceError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except ArtifactRoutePreparationPartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(
            f"Routes verified: {error.result.routes_verified}/"
            f"{error.result.routes_expected}",
            file=sys.stderr,
        )
        return EXIT_PARTIAL_SUCCESS
    except RenderPartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(f"Output: {error.output_path}", file=sys.stderr)
        return EXIT_PARTIAL_SUCCESS
    except RoutingResolutionPartialSuccessError as error:
        result = error.result
        print(f"Partial success: {error}", file=sys.stderr)
        print("Handler dispatch succeeded: yes", file=sys.stderr)
        print("Evidence filing occurred: yes", file=sys.stderr)
        print("Routing-resolution metadata persisted: no", file=sys.stderr)
        print(f"Failure: {result.failure_id}", file=sys.stderr)
        print(f"Selected route: {result.selected_route.route_id}", file=sys.stderr)
        return EXIT_PARTIAL_SUCCESS
    except PacketStoragePartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(
            "Current pointer published: "
            f"{'yes' if error.pointer_published else 'no'}",
            file=sys.stderr,
        )
        if error.snapshot_revision is not None:
            print(
                f"Snapshot revision: {error.snapshot_revision}",
                file=sys.stderr,
            )
        if error.snapshot_sha256 is not None:
            print(
                f"Snapshot SHA-256: {error.snapshot_sha256}",
                file=sys.stderr,
            )
        return EXIT_PARTIAL_SUCCESS
    except StarterTemplateInstallAllPartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(
            f"Completed starter installs: {len(error.completed_results)}",
            file=sys.stderr,
        )
        print(
            f"Failed starter: {error.failed_starter_key}",
            file=sys.stderr,
        )
        return EXIT_PARTIAL_SUCCESS
    except TemplateStoragePartialSuccessError as error:
        print(f"Partial success: {error}", file=sys.stderr)
        print(
            "Current pointer published: "
            f"{'yes' if error.pointer_published else 'no'}",
            file=sys.stderr,
        )
        if error.snapshot_revision is not None:
            print(
                f"Snapshot revision: {error.snapshot_revision}",
                file=sys.stderr,
            )
        if error.snapshot_sha256 is not None:
            print(
                f"Snapshot SHA-256: {error.snapshot_sha256}",
                file=sys.stderr,
            )
        return EXIT_PARTIAL_SUCCESS
    except ConcordStoragePartialSuccessError as error:
        _print_partial_success(error)
        return EXIT_PARTIAL_SUCCESS
    except (ConcordWorkflowConflictError, ConcordStorageConflictError) as error:
        print(f"Conflict: {error}", file=sys.stderr)
        return EXIT_CONFLICT
    except (ConcordWorkflowError, ConcordStorageError, WorkspaceRootError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except (
        RouteRegistrationPersistenceError,
        RoutingFailureMetadataReadError,
        RoutingFailureMetadataWriteError,
        ScanResolutionMetadataReadError,
        ScanResolutionMetadataWriteError,
        ModuleDispatchError,
        ModuleRegistryError,
        ModuleDiscoveryError,
    ) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
