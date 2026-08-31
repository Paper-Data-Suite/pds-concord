from __future__ import annotations

import pytest

from scripts.verify_release_artifacts import (
    EXPECTED_ENTRY_POINTS,
    REQUIRED_SDIST_FILES,
    REQUIRED_WHEEL_FILES,
    ArtifactValidationError,
    validate_entry_points,
    validate_sdist_project,
)

ENTRY_POINTS_WITH_OPERATIONS = """[console_scripts]
concord = concord.cli:main

[paper_data_suite.modules]
concord = concord.pds_module:get_module_profile

[paper_data_suite.publication_producers]
concord = concord.pds_publication:get_publication_producer_profile

[paper_data_suite.module_operations]
concord = concord.pds_operations:get_module_operations_profile
"""

PYPROJECT_WITH_OPERATIONS = """[project]
name = "pds-concord"
dynamic = ["version"]
requires-python = ">=3.11"
dependencies = [
    "pds-core>=0.6.3,<0.7",
    "Pillow>=11,<13",
    "qrcode>=8,<9",
    "pypdfium2>=4.30,<5",
    "zxing-cpp>=2.3,<3",
]

[project.scripts]
concord = "concord.cli:main"

[project.entry-points."paper_data_suite.modules"]
concord = "concord.pds_module:get_module_profile"

[project.entry-points."paper_data_suite.publication_producers"]
concord = "concord.pds_publication:get_publication_producer_profile"

[project.entry-points."paper_data_suite.module_operations"]
concord = "concord.pds_operations:get_module_operations_profile"

[tool.setuptools.dynamic]
version = { attr = "concord._version.__version__" }
"""


def test_release_contract_freezes_module_operations_surface() -> None:
    assert EXPECTED_ENTRY_POINTS["paper_data_suite.module_operations"] == {
        "concord": "concord.pds_operations:get_module_operations_profile"
    }
    assert "concord/pds_operations.py" in REQUIRED_WHEEL_FILES
    assert "concord/pds_operations.py" in REQUIRED_SDIST_FILES


def test_wheel_entry_points_reject_missing_module_operations() -> None:
    without_operations = ENTRY_POINTS_WITH_OPERATIONS.replace(
        "\n[paper_data_suite.module_operations]\n"
        "concord = concord.pds_operations:get_module_operations_profile\n",
        "",
    )
    with pytest.raises(
        ArtifactValidationError,
        match="paper_data_suite.module_operations",
    ):
        validate_entry_points(without_operations, "wheel")


def test_sdist_project_rejects_missing_module_operations() -> None:
    without_operations = PYPROJECT_WITH_OPERATIONS.replace(
        "\n[project.entry-points.\"paper_data_suite.module_operations\"]\n"
        "concord = \"concord.pds_operations:get_module_operations_profile\"\n",
        "",
    )
    with pytest.raises(
        ArtifactValidationError,
        match="paper_data_suite.module_operations",
    ):
        validate_sdist_project(without_operations)
