"""Side-effect-free command-line entry point for the Concord baseline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from concord import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the baseline command parser without touching workspace state."""
    parser = argparse.ArgumentParser(
        prog="concord",
        description=(
            "Concord is the Paper Data Suite module for paper-first collaborative "
            "classroom evidence. This package baseline does not yet implement the "
            "complete Activity workflow."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse baseline CLI arguments and return a process exit status."""
    build_parser().parse_args(argv)
    return 0
