"""Direct workspace commands backed by pds-core."""

from __future__ import annotations

import argparse

from pds_core.workspace import (
    clear_saved_workspace_root,
    ensure_workspace_root,
    inspect_workspace_root,
    resolve_workspace_root,
    save_workspace_root,
)


def handle_show(args: argparse.Namespace) -> int:
    status = inspect_workspace_root(args.workspace_root)
    print(f"Workspace: {status.root}")
    print(f"Source: {status.source}")
    print(f"Exists: {'yes' if status.exists else 'no'}")
    print(f"Directory: {'yes' if status.is_dir else 'no'}")
    print(f"Writable: {'yes' if status.is_writable else 'no'}")
    print(f"Config: {status.config_path}")
    print(f"Default: {status.default_root}")
    return 0


def handle_set(args: argparse.Namespace) -> int:
    root = ensure_workspace_root(args.path)
    saved = save_workspace_root(root)
    print(f"Saved Paper Data Suite workspace: {saved}")
    return 0


def handle_validate(args: argparse.Namespace) -> int:
    root = resolve_workspace_root(args.workspace_root)
    validated = ensure_workspace_root(root)
    print(f"Workspace validated: {validated}")
    return 0


def handle_reset(_args: argparse.Namespace) -> int:
    cleared = clear_saved_workspace_root()
    if cleared:
        print("Saved workspace preference cleared.")
    else:
        print("No saved workspace preference was set.")
    print("No workspace files were deleted.")
    return 0
