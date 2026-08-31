from __future__ import annotations

import tomllib
from pathlib import Path

from scripts.check_package import (
    EXPECTED_RUNTIME_REQUIREMENTS as PACKAGE_RUNTIME_REQUIREMENTS,
)
from scripts.check_package import (
    validate_runtime_requirements as validate_package_runtime_requirements,
)
from scripts.verify_release_artifacts import (
    EXPECTED_RUNTIME_REQUIREMENTS as ARTIFACT_RUNTIME_REQUIREMENTS,
)
from scripts.verify_release_artifacts import (
    validate_requirements as validate_artifact_runtime_requirements,
)
from scripts.verify_release_compatibility import (
    EXPECTED_RUNTIME_REQUIREMENTS as COMPAT_RUNTIME_REQUIREMENTS,
)

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = (
    "pds-core>=0.6.3,<0.7",
    "Pillow>=11,<13",
    "qrcode>=8,<9",
    "pypdfium2>=4.30,<5",
    "zxing-cpp>=2.3,<3",
)


def test_release_validators_share_exact_direct_runtime_contract() -> None:
    assert PACKAGE_RUNTIME_REQUIREMENTS == EXPECTED
    assert ARTIFACT_RUNTIME_REQUIREMENTS == EXPECTED
    assert COMPAT_RUNTIME_REQUIREMENTS == EXPECTED


def test_pyproject_matches_exact_direct_runtime_contract() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    assert tuple(project["dependencies"]) == EXPECTED



def test_wheel_validators_ignore_optional_dev_extra_metadata() -> None:
    metadata_requirements = [
        *EXPECTED,
        'build; extra == "dev"',
        'pytest; extra == "dev"',
        'ruff; extra == "dev"',
    ]

    validate_package_runtime_requirements(metadata_requirements)
    validate_artifact_runtime_requirements(metadata_requirements, "wheel")
