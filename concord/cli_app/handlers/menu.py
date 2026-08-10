"""CLI bridge to Concord's teacher-facing menu."""

from __future__ import annotations

import argparse


def handle_menu(_args: argparse.Namespace) -> int:
    """Launch the teacher-facing menu lazily."""
    from concord.menu import launch_menu

    return launch_menu()
