from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.verify_release_artifacts import (
    EXPECTED_SDIST,
    EXPECTED_WHEEL,
    REQUIRED_SDIST_FILES,
    REQUIRED_WHEEL_FILES,
    ArtifactValidationError,
    normalized_member,
    validate_release_artifacts,
    validate_sdist,
    validate_wheel,
)

METADATA = """Metadata-Version: 2.4
Name: pds-concord
Version: 0.3.0
Requires-Python: >=3.11
Requires-Dist: pds-core<0.7,>=0.6.3
Requires-Dist: Pillow<13,>=11
Requires-Dist: qrcode<9,>=8
Requires-Dist: pypdfium2<5,>=4.30
Requires-Dist: zxing-cpp<3,>=2.3

Synthetic test package.
"""
ENTRY_POINTS = """[console_scripts]
concord = concord.cli:main

[paper_data_suite.modules]
concord = concord.pds_module:get_module_profile

[paper_data_suite.publication_producers]
concord = concord.pds_publication:get_publication_producer_profile

[paper_data_suite.module_operations]
concord = concord.pds_operations:get_module_operations_profile
"""
PYPROJECT = """[project]
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
VERSION_SOURCE = '__version__ = "0.3.0"\n'


def _write_wheel(
    path: Path, *, omit: str | None = None, metadata: str = METADATA
) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name in sorted(REQUIRED_WHEEL_FILES):
            if name != omit:
                archive.writestr(name, "")
        archive.writestr("pds_concord-0.3.0.dist-info/METADATA", metadata)
        archive.writestr(
            "pds_concord-0.3.0.dist-info/entry_points.txt",
            ENTRY_POINTS,
        )


def _tar_file(archive: tarfile.TarFile, name: str, content: str) -> None:
    raw = content.encode("utf-8")
    info = tarfile.TarInfo(name)
    info.size = len(raw)
    archive.addfile(info, io.BytesIO(raw))


def _write_sdist(
    path: Path,
    *,
    omit: str | None = None,
    metadata: str = METADATA,
    pyproject: str = PYPROJECT,
    version_source: str = VERSION_SOURCE,
) -> None:
    root = "pds_concord-0.3.0"
    with tarfile.open(path, "w:gz") as archive:
        _tar_file(archive, f"{root}/PKG-INFO", metadata)
        fixture_root = f"{root}/tests/fixtures/core_grouping_signals/v1"
        _tar_file(
            archive,
            f"{fixture_root}/SHA256SUMS.txt",
            "synthetic fixture checksum manifest\n",
        )
        _tar_file(
            archive,
            f"{fixture_root}/classes/english10_p2/roster.csv",
            "class_id,student_id\n"
            "synthetic_class,synthetic_student\n",
        )
        for name in sorted(REQUIRED_SDIST_FILES):
            if name == omit:
                continue
            content = ""
            if name == "pyproject.toml":
                content = pyproject
            elif name == "concord/_version.py":
                content = version_source
            _tar_file(archive, f"{root}/{name}", content)


def test_synthetic_release_artifacts_pass(tmp_path: Path) -> None:
    _write_wheel(tmp_path / EXPECTED_WHEEL)
    _write_sdist(tmp_path / EXPECTED_SDIST)
    validate_release_artifacts(tmp_path)


def test_release_directory_rejects_wrong_name_and_extra_artifact(
    tmp_path: Path,
) -> None:
    _write_wheel(tmp_path / "pds_concord-0.2.1-py3-none-any.whl")
    _write_sdist(tmp_path / EXPECTED_SDIST)
    with pytest.raises(ArtifactValidationError):
        validate_release_artifacts(tmp_path)

    (tmp_path / "pds_concord-0.2.1-py3-none-any.whl").rename(tmp_path / EXPECTED_WHEEL)
    (tmp_path / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ArtifactValidationError):
        validate_release_artifacts(tmp_path)


def test_wheel_rejects_wrong_metadata_version(tmp_path: Path) -> None:
    wrong = METADATA.replace("Version: 0.3.0", "Version: 0.2.1")
    path = tmp_path / EXPECTED_WHEEL
    _write_wheel(path, metadata=wrong)
    with pytest.raises(ArtifactValidationError):
        validate_wheel(path)


def test_wheel_rejects_missing_required_public_module(tmp_path: Path) -> None:
    path = tmp_path / EXPECTED_WHEEL
    _write_wheel(path, omit="concord/academic_result_reader.py")
    with pytest.raises(ArtifactValidationError):
        validate_wheel(path)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/absolute"])
def test_dangerous_archive_member_is_rejected(name: str) -> None:
    with pytest.raises(ArtifactValidationError):
        normalized_member(name)


@pytest.mark.parametrize(
    "metadata",
    [
        METADATA.replace(
            "Requires-Dist: pds-core<0.7,>=0.6.3",
            "Requires-Dist: pds-core<0.7,>=0.6",
        ),
        METADATA.replace(
            "\n\nSynthetic test package.",
            "\nRequires-Dist: pds-meridian>=0.1\n\nSynthetic test package.",
        ),
    ],
)
def test_wheel_rejects_core_and_sibling_dependency_drift(
    tmp_path: Path,
    metadata: str,
) -> None:
    path = tmp_path / EXPECTED_WHEEL
    _write_wheel(path, metadata=metadata)
    with pytest.raises(ArtifactValidationError):
        validate_wheel(path)


@pytest.mark.parametrize(
    "metadata",
    [
        METADATA.replace("Requires-Dist: qrcode<9,>=8\n", ""),
        METADATA.replace(
            "Requires-Dist: Pillow<13,>=11",
            "Requires-Dist: Pillow<12,>=11",
        ),
        METADATA.replace(
            "Requires-Dist: zxing-cpp<3,>=2.3",
            "Requires-Dist: zxing-cpp<3,>=2.3; python_version<'3.14'",
        ),
    ],
)
def test_wheel_rejects_direct_runtime_dependency_drift(
    tmp_path: Path, metadata: str
) -> None:
    path = tmp_path / EXPECTED_WHEEL
    _write_wheel(path, metadata=metadata)
    with pytest.raises(ArtifactValidationError):
        validate_wheel(path)


def test_sdist_rejects_direct_runtime_dependency_drift(tmp_path: Path) -> None:
    path = tmp_path / EXPECTED_SDIST
    wrong = PYPROJECT.replace(
        '    "pypdfium2>=4.30,<5",\n',
        "",
    )
    _write_sdist(path, pyproject=wrong)
    with pytest.raises(ArtifactValidationError):
        validate_sdist(path)


def test_sdist_rejects_missing_required_public_module(tmp_path: Path) -> None:
    path = tmp_path / EXPECTED_SDIST
    _write_sdist(path, omit="concord/academic_result_reader.py")
    with pytest.raises(ArtifactValidationError):
        validate_sdist(path)


def test_sdist_rejects_source_metadata_drift(tmp_path: Path) -> None:
    path = tmp_path / EXPECTED_SDIST
    wrong = PYPROJECT.replace(
        'concord = "concord.pds_module:get_module_profile"',
        'concord = "concord.pds_module:wrong_profile"',
    )
    _write_sdist(path, pyproject=wrong)
    with pytest.raises(ArtifactValidationError):
        validate_sdist(path)


def test_sdist_rejects_wrong_authoritative_version_source(tmp_path: Path) -> None:
    path = tmp_path / EXPECTED_SDIST
    _write_sdist(path, version_source='__version__ = "0.2.0"\n')
    with pytest.raises(ArtifactValidationError):
        validate_sdist(path)
