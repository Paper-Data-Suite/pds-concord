"""Validate the current Concord v0.3.0.dev0 development artifacts."""

from __future__ import annotations

import argparse
import ast
import configparser
import stat
import tarfile
import tomllib
import zipfile
from email import policy
from email.message import Message
from email.parser import Parser
from pathlib import Path, PurePosixPath

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

RELEASE_VERSION = "0.3.0.dev0"
EXPECTED_WHEEL = "pds_concord-0.3.0.dev0-py3-none-any.whl"
EXPECTED_SDIST = "pds_concord-0.3.0.dev0.tar.gz"
EXPECTED_DIST_INFO = "pds_concord-0.3.0.dev0.dist-info"
EXPECTED_CORE_SPECIFIER = SpecifierSet(">=0.6.3,<0.7")
EXPECTED_PYTHON_SPECIFIER = SpecifierSet(">=3.11")
EXPECTED_ENTRY_POINTS = {
    "console_scripts": {"concord": "concord.cli:main"},
    "paper_data_suite.modules": {"concord": "concord.pds_module:get_module_profile"},
    "paper_data_suite.publication_producers": {
        "concord": "concord.pds_publication:get_publication_producer_profile"
    },
}
REQUIRED_WHEEL_FILES = frozenset(
    {
        "concord/__init__.py",
        "concord/_version.py",
        "concord/pds_contract.py",
        "concord/pds_module.py",
        "concord/pds_publication.py",
        "concord/academic_result_manifest.py",
        "concord/academic_result_reader.py",
        "concord/academic_result_artifacts.py",
        "concord/artifact_rendering.py",
        "concord/py.typed",
    }
)
REQUIRED_SDIST_FILES = REQUIRED_WHEEL_FILES | frozenset({"pyproject.toml"})
FORBIDDEN_PARTS = frozenset(
    {
        ".git",
        ".venv",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "build",
        "dist",
        "classes",
        "local_outputs",
        "scans",
        "scans_inbox",
        "credentials",
    }
)
FORBIDDEN_SIBLING_PARTS = frozenset(
    {
        "pds_core",
        "pds-core",
        "scoreform",
        "pds_scoreform",
        "pds-scoreform",
        "quillan",
        "pds_quillan",
        "pds-quillan",
        "portia",
        "pds_portia",
        "pds-portia",
        "meridian",
        "pds_meridian",
        "pds-meridian",
        "vitrine",
        "pds_vitrine",
        "pds-vitrine",
    }
)
FORBIDDEN_FILENAMES = frozenset(
    {".env", "coverage.xml", "results.csv", "sha256sums.txt"}
)
FORBIDDEN_SUFFIXES = frozenset({".pyc", ".pyo", ".pem", ".key", ".p12"})
SIBLING_DISTRIBUTIONS = frozenset(
    {
        "pds-scoreform",
        "scoreform",
        "pds-quillan",
        "quillan",
        "pds-portia",
        "portia",
        "pds-meridian",
        "meridian",
        "pds-vitrine",
        "vitrine",
    }
)


class ArtifactValidationError(RuntimeError):
    """Raised when release artifacts violate the frozen boundary."""


class _CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr: str) -> str:
        return optionstr


def normalized_member(name: str) -> PurePosixPath:
    """Normalize and reject absolute or parent-traversing archive members."""
    member = PurePosixPath(name.replace("\\", "/"))
    if member.is_absolute() or ".." in member.parts or not member.parts:
        raise ArtifactValidationError(f"unsafe archive member: {name}")
    if member.parts[0].endswith(":"):
        raise ArtifactValidationError(f"unsafe archive member: {name}")
    return member


def _is_vendored_grouping_fixture(member: PurePosixPath) -> bool:
    needle = ("tests", "fixtures", "core_grouping_signals", "v1")
    lowered = tuple(part.lower() for part in member.parts)
    return any(
        lowered[index : index + len(needle)] == needle
        for index in range(len(lowered) - len(needle) + 1)
    )


def validate_member_names(names: list[str]) -> None:
    if len(names) != len(set(names)):
        raise ArtifactValidationError("artifact contains duplicate member names")
    for name in names:
        member = normalized_member(name)
        grouping_fixture = _is_vendored_grouping_fixture(member)
        lowered_parts = {part.lower() for part in member.parts}
        lowered_name = member.name.lower()
        siblings = sorted(lowered_parts & FORBIDDEN_SIBLING_PARTS)
        if siblings:
            raise ArtifactValidationError(
                f"artifact bundles Core/sibling package {siblings[0]}: {name}"
            )
        if lowered_parts & FORBIDDEN_PARTS and not grouping_fixture:
            raise ArtifactValidationError(f"forbidden build/workspace member: {name}")
        if lowered_name in FORBIDDEN_FILENAMES and not grouping_fixture:
            raise ArtifactValidationError(
                f"forbidden generated/credential member: {name}"
            )
        if member.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise ArtifactValidationError(f"forbidden cache/credential member: {name}")
        if lowered_name.startswith("debug_") or lowered_name.endswith("_results.csv"):
            raise ArtifactValidationError(f"forbidden generated member: {name}")


def _single_metadata_value(message: Message, field: str, label: str) -> str:
    values = message.get_all(field, [])
    if len(values) != 1:
        raise ArtifactValidationError(
            f"{label} metadata must contain exactly one {field} field"
        )
    return str(values[0]).strip()


def validate_requirements(values: list[str], label: str) -> None:
    requirements: list[Requirement] = []
    for value in values:
        try:
            requirements.append(Requirement(value))
        except InvalidRequirement as error:
            raise ArtifactValidationError(
                f"{label} has invalid Requires-Dist: {value}"
            ) from error
    core = [
        item
        for item in requirements
        if canonicalize_name(item.name) == canonicalize_name("pds-core")
    ]
    if len(core) != 1 or core[0].specifier != EXPECTED_CORE_SPECIFIER:
        raise ArtifactValidationError(
            f"{label} must require exactly pds-core>=0.6.3,<0.7"
        )
    if core[0].url is not None or core[0].marker is not None or core[0].extras:
        raise ArtifactValidationError(
            f"{label} pds-core requirement cannot use URL, marker, or extras"
        )
    siblings = sorted(
        item.name
        for item in requirements
        if canonicalize_name(item.name)
        in {canonicalize_name(name) for name in SIBLING_DISTRIBUTIONS}
    )
    if siblings:
        raise ArtifactValidationError(
            f"{label} has sibling runtime dependencies: " + ", ".join(siblings)
        )


def validate_package_metadata(text: str, label: str) -> None:
    message = Parser(policy=policy.default).parsestr(text)
    if canonicalize_name(
        _single_metadata_value(message, "Name", label)
    ) != canonicalize_name("pds-concord"):
        raise ArtifactValidationError(f"{label} distribution name must be pds-concord")
    raw_version = _single_metadata_value(message, "Version", label)
    try:
        if Version(raw_version) != Version(RELEASE_VERSION):
            raise ArtifactValidationError(f"{label} version must be {RELEASE_VERSION}")
    except InvalidVersion as error:
        raise ArtifactValidationError(
            f"{label} version is invalid: {raw_version}"
        ) from error
    raw_python = _single_metadata_value(message, "Requires-Python", label)
    try:
        python_specifier = SpecifierSet(raw_python)
    except InvalidSpecifier as error:
        raise ArtifactValidationError(
            f"{label} Requires-Python is invalid: {raw_python}"
        ) from error
    if python_specifier != EXPECTED_PYTHON_SPECIFIER:
        raise ArtifactValidationError(f"{label} Requires-Python must be exactly >=3.11")
    validate_requirements(
        [str(value) for value in message.get_all("Requires-Dist", [])], label
    )


def validate_entry_points(text: str, label: str) -> None:
    parser = _CaseSensitiveConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(text)
    except configparser.Error as error:
        raise ArtifactValidationError(
            f"{label} entry points are invalid: {error}"
        ) from error
    for group, expected in EXPECTED_ENTRY_POINTS.items():
        if not parser.has_section(group):
            raise ArtifactValidationError(
                f"{label} is missing entry-point group {group}"
            )
        if dict(parser.items(group)) != expected:
            raise ArtifactValidationError(f"{label} {group} entry points changed")



def _project_table(data: dict[str, object], label: str) -> dict[str, object]:
    project = data.get("project")
    if not isinstance(project, dict):
        raise ArtifactValidationError(f"{label} pyproject has no project table")
    return project


def validate_sdist_project(text: str, label: str = "sdist") -> None:
    """Validate the source metadata that must reproduce the release package."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ArtifactValidationError(f"{label} pyproject is invalid TOML") from error

    project = _project_table(data, label)
    if canonicalize_name(str(project.get("name", ""))) != canonicalize_name(
        "pds-concord"
    ):
        raise ArtifactValidationError(
            f"{label} pyproject distribution name must be pds-concord"
        )

    raw_python = project.get("requires-python")
    if not isinstance(raw_python, str):
        raise ArtifactValidationError(
            f"{label} pyproject Requires-Python must be a string"
        )
    try:
        python_specifier = SpecifierSet(raw_python)
    except InvalidSpecifier as error:
        raise ArtifactValidationError(
            f"{label} pyproject Requires-Python is invalid: {raw_python}"
        ) from error
    if python_specifier != EXPECTED_PYTHON_SPECIFIER:
        raise ArtifactValidationError(
            f"{label} pyproject Requires-Python must be exactly >=3.11"
        )

    raw_dependencies = project.get("dependencies")
    if not isinstance(raw_dependencies, list) or not all(
        isinstance(value, str) for value in raw_dependencies
    ):
        raise ArtifactValidationError(
            f"{label} pyproject dependencies must be a string list"
        )
    validate_requirements(raw_dependencies, f"{label} pyproject")

    scripts = project.get("scripts")
    if scripts != EXPECTED_ENTRY_POINTS["console_scripts"]:
        raise ArtifactValidationError(
            f"{label} pyproject console script changed"
        )

    entry_points = project.get("entry-points")
    if not isinstance(entry_points, dict):
        raise ArtifactValidationError(
            f"{label} pyproject has no project.entry-points table"
        )
    for group in (
        "paper_data_suite.modules",
        "paper_data_suite.publication_producers",
    ):
        if entry_points.get(group) != EXPECTED_ENTRY_POINTS[group]:
            raise ArtifactValidationError(
                f"{label} pyproject entry point changed: {group}"
            )

    if project.get("dynamic") != ["version"]:
        raise ArtifactValidationError(
            f"{label} pyproject must keep version as its only dynamic project field"
        )
    tool = data.get("tool")
    setuptools = tool.get("setuptools") if isinstance(tool, dict) else None
    dynamic = setuptools.get("dynamic") if isinstance(setuptools, dict) else None
    version = dynamic.get("version") if isinstance(dynamic, dict) else None
    if (
        not isinstance(version, dict)
        or version.get("attr") != "concord._version.__version__"
    ):
        raise ArtifactValidationError(
            f"{label} pyproject version must resolve from "
            "concord._version.__version__"
        )


def validate_version_source(text: str, label: str = "sdist") -> None:
    """Require one exact package-version literal in the source distribution."""
    try:
        tree = ast.parse(text)
    except SyntaxError as error:
        raise ArtifactValidationError(
            f"{label} concord/_version.py is invalid Python"
        ) from error

    values: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if (
            any(
                isinstance(target, ast.Name) and target.id == "__version__"
                for target in targets
            )
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            values.append(value.value)
    if values != [RELEASE_VERSION]:
        raise ArtifactValidationError(
            f"{label} must contain exactly one __version__ = "
            f"{RELEASE_VERSION!r} literal"
        )


def _zip_member_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)


def validate_wheel(path: Path) -> None:
    if path.name != EXPECTED_WHEEL:
        raise ArtifactValidationError(f"wheel must be named {EXPECTED_WHEEL}")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            validate_member_names(names)
            if archive.testzip() is not None:
                raise ArtifactValidationError("wheel contains a corrupt ZIP member")
            if any(_zip_member_is_symlink(info) for info in infos):
                raise ArtifactValidationError("wheel contains a symbolic link")
            allowed_roots = {"concord", EXPECTED_DIST_INFO}
            for name in names:
                root = normalized_member(name).parts[0]
                if root not in allowed_roots:
                    raise ArtifactValidationError(
                        f"wheel contains a non-runtime package root: {name}"
                    )
            if not REQUIRED_WHEEL_FILES.issubset(names):
                missing = sorted(REQUIRED_WHEEL_FILES - set(names))
                raise ArtifactValidationError(
                    "wheel is missing required public files: " + ", ".join(missing)
                )
            metadata_names = [
                name for name in names if name.endswith(".dist-info/METADATA")
            ]
            entry_names = [
                name for name in names if name.endswith(".dist-info/entry_points.txt")
            ]
            if len(metadata_names) != 1 or len(entry_names) != 1:
                raise ArtifactValidationError(
                    "wheel must contain one METADATA and one entry_points.txt"
                )
            validate_package_metadata(
                archive.read(metadata_names[0]).decode("utf-8"), "wheel"
            )
            validate_entry_points(archive.read(entry_names[0]).decode("utf-8"), "wheel")
    except zipfile.BadZipFile as error:
        raise ArtifactValidationError("wheel is not a readable ZIP archive") from error


def validate_sdist(path: Path) -> None:
    if path.name != EXPECTED_SDIST:
        raise ArtifactValidationError(f"sdist must be named {EXPECTED_SDIST}")
    expected_root = f"pds_concord-{RELEASE_VERSION}"
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            members = archive.getmembers()
            names = [member.name for member in members]
            validate_member_names(names)
            for member in members:
                normalized = normalized_member(member.name)
                if normalized.parts[0] != expected_root:
                    raise ArtifactValidationError(
                        f"sdist member is outside {expected_root}: {member.name}"
                    )
                if member.issym() or member.islnk():
                    raise ArtifactValidationError(
                        f"sdist contains a symbolic/hard link: {member.name}"
                    )
                if not (member.isfile() or member.isdir()):
                    raise ArtifactValidationError(
                        f"sdist contains an unsupported member type: {member.name}"
                    )
            relative_names = {
                str(PurePosixPath(*normalized_member(name).parts[1:]))
                for name in names
                if len(normalized_member(name).parts) > 1
            }
            missing_sources = sorted(REQUIRED_SDIST_FILES - relative_names)
            if missing_sources:
                raise ArtifactValidationError(
                    "sdist is missing required release source files: "
                    + ", ".join(missing_sources)
                )

            metadata_name = f"{expected_root}/PKG-INFO"
            pyproject_name = f"{expected_root}/pyproject.toml"
            version_name = f"{expected_root}/concord/_version.py"
            if metadata_name not in names:
                raise ArtifactValidationError("sdist is missing PKG-INFO")

            metadata_file = archive.extractfile(metadata_name)
            pyproject_file = archive.extractfile(pyproject_name)
            version_file = archive.extractfile(version_name)
            if (
                metadata_file is None
                or pyproject_file is None
                or version_file is None
            ):
                raise ArtifactValidationError("sdist release metadata is unreadable")

            validate_package_metadata(metadata_file.read().decode("utf-8"), "sdist")
            validate_sdist_project(pyproject_file.read().decode("utf-8"))
            validate_version_source(version_file.read().decode("utf-8"))
    except (tarfile.TarError, OSError) as error:
        raise ArtifactValidationError(
            "sdist is not a readable gzip tar archive"
        ) from error


def validate_release_artifacts(directory: Path) -> None:
    if not directory.is_dir():
        raise ArtifactValidationError(
            f"release artifact directory does not exist: {directory}"
        )
    files = sorted(path.name for path in directory.iterdir() if path.is_file())
    expected = sorted([EXPECTED_WHEEL, EXPECTED_SDIST])
    if files != expected:
        raise ArtifactValidationError(
            f"release directory must contain exactly {expected!r}; found {files!r}"
        )
    validate_wheel(directory / EXPECTED_WHEEL)
    validate_sdist(directory / EXPECTED_SDIST)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_directory", type=Path)
    args = parser.parse_args()
    try:
        validate_release_artifacts(args.dist_directory)
    except ArtifactValidationError as error:
        print(f"Release artifact validation failed: {error}")
        return 1
    print(f"Validated exact {EXPECTED_WHEEL} and {EXPECTED_SDIST} release artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
