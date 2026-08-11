"""Public command-line entry point for Concord."""

from __future__ import annotations

from collections.abc import Sequence

from concord.cli_app.main import main as _main
from concord.cli_app.parser import build_parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run direct commands or the teacher menu for bare invocation."""
    return _main(argv)


__all__ = ["build_parser", "main"]
