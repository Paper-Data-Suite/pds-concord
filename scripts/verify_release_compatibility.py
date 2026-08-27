"""Verify the current Concord development package and frozen public boundary."""

from __future__ import annotations

import ast
import inspect
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

import concord.academic_result_artifacts as artifacts
import concord.academic_result_reader as reader
from concord.pds_contract import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)
from concord.pds_publication import get_publication_producer_profile

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_VERSION = "0.3.0.dev0"
EXPECTED_CORE_SPECIFIER = SpecifierSet(">=0.6.3,<0.7")
EXPECTED_PYTHON_SPECIFIER = SpecifierSet(">=3.11")
EXPECTED_CAPABILITIES = frozenset(
    {"criterion_scores", "moderated_scores", "standards_ratings"}
)
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
SIBLING_IMPORT_ROOTS = frozenset(
    {
        "scoreform",
        "pds_scoreform",
        "quillan",
        "pds_quillan",
        "portia",
        "pds_portia",
        "meridian",
        "pds_meridian",
        "vitrine",
        "pds_vitrine",
    }
)


class ReleaseCompatibilityError(RuntimeError):
    """Raised when the v0.2.0 release boundary has drifted."""


@dataclass(frozen=True, slots=True)
class ReleaseContractValues:
    module_id: str
    work_contract: str
    work_kind: str
    activity_record_kind: str
    activity_contract: str
    manifest_contract: str
    manifest_record_type: str
    record_set_id: str


@dataclass(frozen=True, slots=True)
class ProducerProfileValues:
    module_id: str
    core_schema_versions: frozenset[str]
    work_contracts: frozenset[str]
    support_row_count: int
    publication_kind: str
    manifest_contracts: frozenset[str]
    capabilities: frozenset[str]
    source_record_kind: str
    source_contracts: frozenset[str]
    source_allows_unversioned: bool
    allows_missing_source_record: bool


def _read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise ReleaseCompatibilityError(f"missing release file: {relative}")
    return path.read_text(encoding="utf-8")


def source_version_literals(source: str) -> tuple[str, ...]:
    """Return literal assignments to ``__version__`` in Python source."""
    tree = ast.parse(source)
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
    return tuple(values)


def validate_release_metadata(project: Mapping[str, object], version: str) -> None:
    """Validate release identity and dependency metadata from parsed TOML."""
    if project.get("name") != "pds-concord":
        raise ReleaseCompatibilityError("distribution name must be pds-concord")
    if version != DEVELOPMENT_VERSION:
        raise ReleaseCompatibilityError(f"source version must be {DEVELOPMENT_VERSION}")
    if project.get("requires-python") != str(EXPECTED_PYTHON_SPECIFIER):
        raise ReleaseCompatibilityError("Requires-Python must be exactly >=3.11")
    raw_dependencies = project.get("dependencies")
    if not isinstance(raw_dependencies, list) or not all(
        isinstance(item, str) for item in raw_dependencies
    ):
        raise ReleaseCompatibilityError("project dependencies must be a string list")
    dependencies = tuple(Requirement(item) for item in raw_dependencies)
    core = tuple(
        item
        for item in dependencies
        if canonicalize_name(item.name) == canonicalize_name("pds-core")
    )
    if len(core) != 1 or core[0].specifier != EXPECTED_CORE_SPECIFIER:
        raise ReleaseCompatibilityError("Core requirement must be exactly >=0.6.3,<0.7")
    if core[0].url is not None or core[0].marker is not None or core[0].extras:
        raise ReleaseCompatibilityError(
            "Core requirement cannot use URL, marker, or extras"
        )
    siblings = sorted(
        item.name
        for item in dependencies
        if canonicalize_name(item.name)
        in {canonicalize_name(name) for name in SIBLING_DISTRIBUTIONS}
    )
    if siblings:
        raise ReleaseCompatibilityError(
            "sibling runtime dependencies are forbidden: " + ", ".join(siblings)
        )


def validate_contract_values(values: ReleaseContractValues) -> None:
    expected = ReleaseContractValues(
        module_id="concord",
        work_contract="concord_academic_work_v1",
        work_kind="collaborative_activity",
        activity_record_kind="activity",
        activity_contract="concord_activity_v1",
        manifest_contract="concord_academic_result_manifest_v1",
        manifest_record_type="concord_academic_result_manifest",
        record_set_id="academic_results",
    )
    if values != expected:
        raise ReleaseCompatibilityError(
            f"public Concord contract identity changed: {values!r}"
        )


def validate_profile_values(values: ProducerProfileValues) -> None:
    expected = ProducerProfileValues(
        module_id="concord",
        core_schema_versions=frozenset({"1"}),
        work_contracts=frozenset({"concord_academic_work_v1"}),
        support_row_count=1,
        publication_kind="academic_result_set",
        manifest_contracts=frozenset({"concord_academic_result_manifest_v1"}),
        capabilities=EXPECTED_CAPABILITIES,
        source_record_kind="activity",
        source_contracts=frozenset({"concord_activity_v1"}),
        source_allows_unversioned=False,
        allows_missing_source_record=False,
    )
    if values != expected:
        raise ReleaseCompatibilityError(
            f"publication producer profile changed: {values!r}"
        )


def _import_roots(tree: ast.AST) -> tuple[tuple[str, int], ...]:
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                (alias.name.split(".", 1)[0], node.lineno) for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module.split(".", 1)[0], node.lineno))
    return tuple(imports)


def _import_modules(tree: ast.AST) -> frozenset[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return frozenset(modules)


def validate_sibling_import_isolation(root: Path = ROOT) -> None:
    offenders: list[str] = []
    for path in sorted((root / "concord").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for imported, line in _import_roots(tree):
            if imported in SIBLING_IMPORT_ROOTS:
                offenders.append(f"{path.relative_to(root)}:{line} imports {imported}")
    if offenders:
        raise ReleaseCompatibilityError(
            "production Concord imports sibling modules: " + "; ".join(offenders)
        )


def validate_reader_and_artifact_boundary() -> None:
    reader_public = frozenset(getattr(reader, "__all__", ()))
    required_reader = {
        "read_academic_result_manifest",
        "validate_academic_result_manifest",
        "lookup_academic_result_score",
        "list_academic_result_scores_for_target",
    }
    if not required_reader.issubset(reader_public):
        raise ReleaseCompatibilityError("public manifest reader surface is incomplete")
    forbidden_policy = (
        "latest",
        "highest",
        "best",
        "official",
        "grade",
        "proficiency",
        "mastery",
        "expand_group",
    )
    leaked = sorted(
        name
        for name in reader_public
        if any(fragment in name.lower() for fragment in forbidden_policy)
    )
    if leaked:
        raise ReleaseCompatibilityError(
            "consumer selection/calculation policy leaked into reader API: "
            + ", ".join(leaked)
        )
    if tuple(inspect.signature(reader.read_academic_result_manifest).parameters) != (
        "value",
    ):
        raise ReleaseCompatibilityError("manifest byte reader signature changed")
    reader_tree = ast.parse(
        inspect.getsource(reader), filename=str(Path(reader.__file__ or ""))
    )
    forbidden_reader_imports = (
        "concord.storage",
        "concord.workflows",
        "pds_core.workspace",
    )
    if any(
        imported == prefix or imported.startswith(prefix + ".")
        for imported in _import_modules(reader_tree)
        for prefix in forbidden_reader_imports
    ):
        raise ReleaseCompatibilityError(
            "public reader imports native storage/workspace"
        )

    artifact_public = frozenset(getattr(artifacts, "__all__", ()))
    required_artifact = {
        "AcademicResultArtifactAuthorizationGate",
        "AcademicResultArtifactAuthorizationRequest",
        "AcademicResultArtifactAuthorizationDecision",
        "read_authorized_academic_result_artifact",
    }
    if not required_artifact.issubset(artifact_public):
        raise ReleaseCompatibilityError(
            "separate Artifact authorization API is incomplete"
        )
    parameters = inspect.signature(
        artifacts.read_authorized_academic_result_artifact
    ).parameters
    if "authorization_gate" not in parameters or "workspace_root" not in parameters:
        raise ReleaseCompatibilityError(
            "Artifact read no longer requires its separate gate"
        )
    if "read_authorized_academic_result_artifact" in reader_public:
        raise ReleaseCompatibilityError("Artifact read leaked into manifest reader API")


def validate_structural_policy_absence(root: Path = ROOT) -> None:
    """Reject bounded producer APIs that would cross release policy boundaries."""
    forbidden_definitions = (
        "calculate_grade",
        "calculate_proficiency",
        "calculate_mastery",
        "select_latest_score",
        "select_highest_score",
        "select_best_score",
        "select_official_score",
        "expand_group_score",
        "individualize_group_score",
    )
    offenders: list[str] = []
    for path in sorted((root / "concord").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                node.name == name or node.name.startswith(name + "_")
                for name in forbidden_definitions
            ):
                offenders.append(f"{path.relative_to(root)}:{node.lineno} {node.name}")
    if offenders:
        raise ReleaseCompatibilityError(
            "forbidden grading/selection/group-expansion API exists: "
            + "; ".join(offenders)
        )


def validate_release_compatibility() -> None:
    project_data = tomllib.loads(_read("pyproject.toml"))
    project = project_data.get("project")
    if not isinstance(project, dict):
        raise ReleaseCompatibilityError("pyproject.toml has no project table")
    version_literals: list[str] = []
    for path in sorted((ROOT / "concord").rglob("*.py")):
        version_literals.extend(
            source_version_literals(path.read_text(encoding="utf-8"))
        )
    if version_literals != [DEVELOPMENT_VERSION]:
        raise ReleaseCompatibilityError(
            "Concord must have exactly one authoritative 0.3.0.dev0 version literal"
        )
    validate_release_metadata(project, version_literals[0])
    validate_sibling_import_isolation()
    validate_contract_values(
        ReleaseContractValues(
            CONCORD_MODULE_ID,
            CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
            CONCORD_ACADEMIC_WORK_KIND,
            CONCORD_ACTIVITY_RECORD_KIND,
            CONCORD_ACTIVITY_CONTRACT_VERSION,
            ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
            ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
        )
    )
    profile = get_publication_producer_profile()
    if len(profile.publication_contracts) != 1:
        raise ReleaseCompatibilityError("Concord must expose exactly one support row")
    support = profile.publication_contracts[0]
    if len(support.source_record_contracts) != 1:
        raise ReleaseCompatibilityError(
            "Concord must require one Activity source contract"
        )
    source = support.source_record_contracts[0]
    validate_profile_values(
        ProducerProfileValues(
            profile.module_id,
            profile.supported_core_publication_schema_versions,
            profile.supported_academic_work_contract_versions,
            len(profile.publication_contracts),
            support.publication_kind,
            support.manifest_contract_versions,
            support.supported_capabilities,
            source.record_kind,
            source.contract_versions,
            source.allows_unversioned,
            support.allows_missing_source_record,
        )
    )
    validate_reader_and_artifact_boundary()
    validate_structural_policy_absence()


def main() -> int:
    try:
        validate_release_compatibility()
    except (
        OSError,
        SyntaxError,
        ValueError,
        KeyError,
        ReleaseCompatibilityError,
    ) as error:
        print(f"Development compatibility audit failed: {error}")
        return 1
    print(
        "Concord v0.3.0.dev0 development compatibility passed: Core >=0.6.3,<0.7; "
        "contracts/profile exact; reader consumer-neutral; Artifact gate separate; "
        "sibling and grading/selection policy absent."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
