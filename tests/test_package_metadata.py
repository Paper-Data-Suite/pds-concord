from __future__ import annotations

import zipfile
from email.parser import BytesParser
from pathlib import Path

from packaging.requirements import Requirement

from concord import __version__
from scripts.check_package import validate_wheel


def test_built_wheel_metadata_and_contents(built_wheel: Path) -> None:
    validate_wheel(built_wheel)
    with zipfile.ZipFile(built_wheel) as archive:
        names = archive.namelist()
        metadata_name = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        metadata = BytesParser().parsebytes(archive.read(metadata_name))
        entry_name = next(
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        )
        entry_points = archive.read(entry_name).decode("utf-8")
    assert metadata["Name"] == "pds-concord"
    assert metadata["Version"] == __version__
    assert metadata["Requires-Python"] == ">=3.11"
    runtime = [
        Requirement(item)
        for item in metadata.get_all("Requires-Dist", [])
        if Requirement(item).name == "pds-core" and Requirement(item).marker is None
    ]
    assert runtime == [Requirement("pds-core>=0.6.1,<0.7")]
    assert "concord/py.typed" in names
    assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
    assert "[console_scripts]\nconcord = concord.cli:main" in entry_points
    assert (
        "[paper_data_suite.modules]\nconcord = concord.pds_module:get_module_profile"
    ) in entry_points
    assert (
        "[paper_data_suite.publication_producers]\n"
        "concord = concord.pds_publication:get_publication_producer_profile"
    ) in entry_points
    assert entry_points.count(
        "concord = concord.pds_publication:get_publication_producer_profile"
    ) == 1


def test_wheel_contains_only_concord_package(built_wheel: Path) -> None:
    with zipfile.ZipFile(built_wheel) as archive:
        names = archive.namelist()
    package_roots = {
        name.split("/", 1)[0]
        for name in names
        if "/" in name and ".dist-info" not in name.split("/", 1)[0]
    }
    assert package_roots == {"concord"}
    forbidden = (
        "tests/",
        "pds_core/",
        "scoreform/",
        "quillan/",
        "portia/",
        "meridian/",
        "vitrine/",
    )
    assert not any(name.lower().startswith(forbidden) for name in names)
