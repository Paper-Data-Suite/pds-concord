"""Validate built Concord distribution metadata and archive isolation."""

from __future__ import annotations

import argparse
import zipfile
from email.message import Message
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement

EXPECTED_CORE_REQUIREMENT = Requirement("pds-core>=0.6.3,<0.7")
EXPECTED_VERSION = "0.3.0.dev0"
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
    "paper-data-suite",
    "pds-scoreform",
    "pds-quillan",
    "pds-portia",
    "pds-meridian",
    "pds-vitrine",
}
STARTER_ASSET_NAMES = (
    "claim_evidence_reasoning.json",
    "collaborative_annotation.json",
    "collaborative_problem_solving.json",
    "collaborative_work_reflection.json",
    "comparison_matrix.json",
    "concept_map.json",
    "decision_matrix.json",
    "discussion_map.json",
    "fishbowl_observer.json",
    "four_corners.json",
    "gallery_walk.json",
    "group_kwl.json",
    "group_roles.json",
    "jigsaw_expert.json",
    "lab_investigation.json",
    "peer_design_code_review.json",
    "peer_review_presentation.json",
    "peer_review_writing.json",
    "project_check_in.json",
    "project_plan.json",
    "reciprocal_reading.json",
    "save_last_word.json",
    "see_think_wonder.json",
    "socratic_seminar.json",
    "structured_academic_controversy.json",
    "talk_moves_observer.json",
    "team_contract.json",
    "team_health_check.json",
    "think_pair_share.json",
    "venn_comparison.json",
)


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
    if metadata["Version"] != EXPECTED_VERSION:
        raise PackageValidationError(f"Version must be {EXPECTED_VERSION}.")
    if metadata["Requires-Python"] != ">=3.11":
        raise PackageValidationError("Requires-Python must be >=3.11.")
    requirements = [Requirement(item) for item in metadata.get_all("Requires-Dist", [])]
    runtime = [
        item for item in requirements if item.name == "pds-core" and item.marker is None
    ]
    if runtime != [EXPECTED_CORE_REQUIREMENT]:
        raise PackageValidationError(
            "Runtime Core requirement must be pds-core>=0.6.3,<0.7."
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
    expected_operations = (
        "[paper_data_suite.module_operations]\n"
        "concord = concord.pds_operations:get_module_operations_profile"
    )
    if expected_operations not in entry_points:
        raise PackageValidationError(
            "The Concord module-operations entry point is missing."
        )
    if entry_points.count("[paper_data_suite.module_operations]") != 1:
        raise PackageValidationError(
            "The module-operations entry-point group must occur exactly once."
        )
    if entry_points.count(
        "concord = concord.pds_operations:get_module_operations_profile"
    ) != 1:
        raise PackageValidationError(
            "The Concord module-operations entry point must occur exactly once."
        )
    required = {
        "concord/__init__.py",
        "concord/academic_result_artifacts.py",
        "concord/academic_result_reader.py",
        "concord/academic_result_share_attention.py",
        "concord/attention_provider.py",
        "concord/menu_attention.py",
        "concord/pds_operations.py",
        "concord/workflows/activity_attention.py",
        "concord/workflows/artifact_collection.py",
        "concord/workflows/artifact_review_attention.py",
        "concord/workflows/artifact_scoring_attention.py",
        "concord/artifact_rendering.py",
        "concord/cli.py",
        "concord/cli_app/handlers/reusable_presets.py",
        "concord/menu_guided_activity.py",
        "concord/menu_presets.py",
        "concord/reusable_preset_storage.py",
        "concord/reusable_presets.py",
        "concord/workflows/guided_activity_setup.py",
        "concord/workflows/reusable_presets.py",
        "concord/py.typed",
        "concord/starter_templates/__init__.py",
        "concord/starter_templates/catalog.py",
        "concord/starter_templates/layout.py",
    }
    if not required.issubset(names):
        raise PackageValidationError("Wheel is missing intended Concord package files.")
    starter_prefix = "concord/starter_templates/assets/"
    expected_starter_assets = {
        starter_prefix + name for name in STARTER_ASSET_NAMES
    }
    actual_starter_assets = {
        name
        for name in names
        if name.startswith(starter_prefix) and name.endswith(".json")
    }
    if actual_starter_assets != expected_starter_assets:
        missing = sorted(expected_starter_assets - actual_starter_assets)
        extra = sorted(actual_starter_assets - expected_starter_assets)
        raise PackageValidationError(
            "Wheel starter Template assets do not match the required 30-file "
            f"catalog; missing={missing}, extra={extra}."
        )
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
