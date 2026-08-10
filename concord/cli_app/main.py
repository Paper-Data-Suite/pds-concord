"""Top-level dispatch and stable exit-code handling for the Concord CLI."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from typing import cast

from pds_core.workspace import WorkspaceRootError

from concord.cli_app.parser import build_parser
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStorageError,
    ConcordStoragePartialSuccessError,
)
from concord.workflows import ConcordWorkflowConflictError, ConcordWorkflowError

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
    except ConcordStoragePartialSuccessError as error:
        _print_partial_success(error)
        return EXIT_PARTIAL_SUCCESS
    except (ConcordWorkflowConflictError, ConcordStorageConflictError) as error:
        print(f"Conflict: {error}", file=sys.stderr)
        return EXIT_CONFLICT
    except (ConcordWorkflowError, ConcordStorageError, WorkspaceRootError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return EXIT_ERROR
