"""Validate built Concord distribution metadata and archive isolation."""

from __future__ import annotations

import argparse
import zipfile
from email.message import Message
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement

EXPECTED_CORE_REQUIREMENT = Requirement("pds-core>=0.6,<0.7")
FORBIDDEN_PREFIXES = (
    "tests/",
    "pds_core/",
    "scoreform/",
    "quillan/",
    "portia/",
    "meridian/",
    "vitrine/",
    ".venv/",
    "build/",
)
FORBIDDEN_PARTS = ("__pycache__", ".pytest_cache", ".mypy_cache", "credentials")
FORBIDDEN_RUNTIME_DEPENDENCIES = {
    "pds-scoreform",
    "pds-quillan",
    "pds-portia",
    "pds-meridian",
    "pds-vitrine",
}


class PackageValidationError(ValueError):
    """Raised when a built package violates the distribution boundary."""


def _single_member(names: list[str], suffix: str) -> str:
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise PackageValidationError(f"Expected one {suffix}, found {len(matches)}.")
    return matches[0]


def _metadata(archive: zipfile.ZipFile, names: list[str]) -> Message:
    return BytesParser().parsebytes(
        archive.read(_single_member(names, ".dist-info/METADATA"))
    )


def validate_wheel(path: str | Path) -> None:
    """Validate metadata, intended files, and required integration entry points."""
    wheel = Path(path)
    try:
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            if archive.testzip() is not None:
                raise PackageValidationError("Wheel contains a corrupt ZIP member.")
            metadata = _metadata(archive, names)
            entry_name = _single_member(names, ".dist-info/entry_points.txt")
            entry_points = archive.read(entry_name).decode("utf-8")
    except zipfile.BadZipFile as error:
        raise PackageValidationError("Wheel is not a readable ZIP archive.") from error

    if metadata["Name"] != "pds-concord":
        raise PackageValidationError("Distribution name must be pds-concord.")
    if metadata["Requires-Python"] != ">=3.11":
        raise PackageValidationError("Requires-Python must be >=3.11.")
    requirements = [Requirement(item) for item in metadata.get_all("Requires-Dist", [])]
    runtime = [
        item for item in requirements if item.name == "pds-core" and item.marker is None
    ]
    if runtime != [EXPECTED_CORE_REQUIREMENT]:
        raise PackageValidationError(
            "Runtime Core requirement must be pds-core>=0.6,<0.7."
        )
    runtime_names = {item.name for item in requirements if item.marker is None}
    forbidden_runtime = runtime_names & FORBIDDEN_RUNTIME_DEPENDENCIES
    if forbidden_runtime:
        raise PackageValidationError(
            "Sibling PDS runtime dependencies are forbidden: "
            + ", ".join(sorted(forbidden_runtime))
        )
    if "[console_scripts]\nconcord = concord.cli:main" not in entry_points:
        raise PackageValidationError("The concord console script is missing.")
    expected_routing = (
        "[paper_data_suite.modules]\nconcord = concord.pds_module:get_module_profile"
    )
    if expected_routing not in entry_points:
        raise PackageValidationError("The Concord routing entry point is missing.")
    expected_publication = (
        "[paper_data_suite.publication_producers]\n"
        "concord = concord.pds_publication:get_publication_producer_profile"
    )
    if expected_publication not in entry_points:
        raise PackageValidationError(
            "The Concord publication-producer entry point is missing."
        )
    if entry_points.count(
        "concord = concord.pds_publication:get_publication_producer_profile"
    ) != 1:
        raise PackageValidationError(
            "The Concord publication-producer entry point must occur exactly once."
        )
    required = {"concord/__init__.py", "concord/cli.py", "concord/py.typed"}
    if not required.issubset(names):
        raise PackageValidationError("Wheel is missing intended Concord package files.")
    if not any(name.endswith(".dist-info/licenses/LICENSE") for name in names):
        raise PackageValidationError("Wheel does not include the MIT license file.")
    for name in names:
        lowered = name.lower()
        if lowered.startswith(FORBIDDEN_PREFIXES) or any(
            part in lowered for part in FORBIDDEN_PARTS
        ):
            raise PackageValidationError(f"Wheel contains forbidden content: {name}")


def main() -> int:
    """Validate one built Concord wheel."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    validate_wheel(args.wheel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
