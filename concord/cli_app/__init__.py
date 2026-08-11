"""Noninteractive Concord command-line implementation."""

from concord.cli_app.main import main
from concord.cli_app.parser import build_parser

__all__ = ["build_parser", "main"]
