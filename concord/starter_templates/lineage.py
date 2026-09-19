"""Generic package-owned starter Template lineage reconciliation.

This module is intentionally independent of the current one-version starter
catalog. Issue #113 wires that catalog to this engine only after the engine's
compatibility behavior is qualified against synthetic v1 -> v2 lineages.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from concord.models import TemplateDefinition, TemplateVersion
from concord.template_storage import (
    TemplateStorageConflictError,
    TemplateStorageError,
    TemplateStorageNotFoundError,
    activate_template_version,
    create_successor_template_version,
    create_template_library,
    load_current_template,
    load_template_rendering_specification,
)
from concord.template_storage_models import LoadedTemplateLibrary

STARTER_LINEAGE_MISSING = "missing"
STARTER_LINEAGE_CURRENT = "current"
STARTER_LINEAGE_UPGRADE_AVAILABLE = "upgrade_available"
STARTER_LINEAGE_CONFLICT = "conflict"

_LINEAGE_STATES = frozenset(
    {
        STARTER_LINEAGE_MISSING,
        STARTER_LINEAGE_CURRENT,
        STARTER_LINEAGE_UPGRADE_AVAILABLE,
        STARTER_LINEAGE_CONFLICT,
    }
)


class StarterTemplateLineageError(RuntimeError):
    """Base failure for package-owned starter lineage reconciliation."""


class StarterTemplateLineageConflictError(StarterTemplateLineageError):
    """Workspace state cannot be reconciled to the reviewed package lineage."""


class StarterTemplateLineageValidationError(StarterTemplateLineageError):
    """A package-owned lineage descriptor is internally invalid."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PackagedStarterTemplateVersion:
    """One immutable package-owned Template Version and its exact render bytes."""

    version: TemplateVersion
    rendering_specification: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.version, TemplateVersion):
            raise StarterTemplateLineageValidationError(
                "version must be TemplateVersion."
            )
        if not isinstance(self.rendering_specification, bytes):
            raise StarterTemplateLineageValidationError(
                "rendering_specification must be exact bytes."
            )
        if not self.rendering_specification:
            raise StarterTemplateLineageValidationError(
                "rendering_specification must not be empty."
            )
        import hashlib

        digest = hashlib.sha256(self.rendering_specification).hexdigest()
        if digest != self.version.rendering_specification_sha256:
            raise StarterTemplateLineageValidationError(
                "rendering bytes do not match Template Version SHA-256."
            )
        if self.version.status != "active":
            raise StarterTemplateLineageValidationError(
                "packaged Template Version prototypes must use active status."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PackagedStarterTemplateLineage:
    """One package-owned logical starter with immutable version history."""

    starter_key: str
    definition: TemplateDefinition
    versions: tuple[PackagedStarterTemplateVersion, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.starter_key, str) or not self.starter_key.strip():
            raise StarterTemplateLineageValidationError(
                "starter_key must be a non-empty string."
            )
        if not isinstance(self.definition, TemplateDefinition):
            raise StarterTemplateLineageValidationError(
                "definition must be TemplateDefinition."
            )
        if self.definition.status != "active":
            raise StarterTemplateLineageValidationError(
                "packaged Template Definition prototypes must use active status."
            )
        if not self.versions:
            raise StarterTemplateLineageValidationError(
                "versions must contain at least one packaged Version."
            )
        if any(
            not isinstance(item, PackagedStarterTemplateVersion)
            for item in self.versions
        ):
            raise StarterTemplateLineageValidationError(
                "versions must contain PackagedStarterTemplateVersion values."
            )

        version_ids: list[str] = []
        rendering_references: list[str] = []
        for index, item in enumerate(self.versions, start=1):
            version = item.version
            if version.template_id != self.definition.template_id:
                raise StarterTemplateLineageValidationError(
                    "packaged Version template_id must match the Definition."
                )
            if version.artifact_category != self.definition.artifact_category:
                raise StarterTemplateLineageValidationError(
                    "packaged Version artifact_category must match the Definition."
                )
            if version.revision_sequence != index:
                raise StarterTemplateLineageValidationError(
                    "packaged Version revision_sequence must form contiguous 1..N."
                )
            expected_predecessor = (
                None
                if index == 1
                else self.versions[index - 2].version.template_version_id
            )
            if version.supersedes_template_version_id != expected_predecessor:
                raise StarterTemplateLineageValidationError(
                    "packaged Version predecessor chain must be linear and exact."
                )
            version_ids.append(version.template_version_id)
            rendering_references.append(
                version.rendering_specification_reference
            )

        if len(set(version_ids)) != len(version_ids):
            raise StarterTemplateLineageValidationError(
                "packaged Template Version IDs must be unique."
            )
        if len(set(rendering_references)) != len(rendering_references):
            raise StarterTemplateLineageValidationError(
                "packaged rendering references must be unique by Version."
            )

    @property
    def template_id(self) -> str:
        return self.definition.template_id

    @property
    def current_version(self) -> PackagedStarterTemplateVersion:
        return self.versions[-1]


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateLineageInspection:
    """Read-only comparison of one workspace lineage to one package lineage."""

    state: str
    loaded: LoadedTemplateLibrary | None
    matched_version_count: int
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.state not in _LINEAGE_STATES:
            raise StarterTemplateLineageValidationError(
                "lineage inspection state is invalid."
            )
        if (
            type(self.matched_version_count) is not int
            or self.matched_version_count < 0
        ):
            raise StarterTemplateLineageValidationError(
                "matched_version_count must be a non-negative integer."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedStarterTemplateLineageReconciliation:
    """Exact zero-write package reconciliation decision."""

    lineage: PackagedStarterTemplateLineage
    initial_state: str
    expected_snapshot_revision: int | None
    expected_snapshot_sha256: str | None

    def __post_init__(self) -> None:
        if self.initial_state not in {
            STARTER_LINEAGE_MISSING,
            STARTER_LINEAGE_CURRENT,
            STARTER_LINEAGE_UPGRADE_AVAILABLE,
        }:
            raise StarterTemplateLineageValidationError(
                "prepared lineage state is invalid."
            )
        if self.initial_state == STARTER_LINEAGE_MISSING:
            if (
                self.expected_snapshot_revision is not None
                or self.expected_snapshot_sha256 is not None
            ):
                raise StarterTemplateLineageValidationError(
                    "missing lineage preparation must not carry a snapshot."
                )
        elif (
            self.expected_snapshot_revision is None
            or self.expected_snapshot_sha256 is None
        ):
            raise StarterTemplateLineageValidationError(
                "existing lineage preparation requires an exact snapshot."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class StarterTemplateLineageReconciliationResult:
    """Result of one exact package-lineage reconciliation."""

    outcome: str
    loaded: LoadedTemplateLibrary

    def __post_init__(self) -> None:
        if self.outcome not in {"installed", "upgraded", "already_current"}:
            raise StarterTemplateLineageValidationError(
                "lineage reconciliation outcome is invalid."
            )


def inspect_packaged_starter_lineage(
    workspace_root: str | Path,
    lineage: PackagedStarterTemplateLineage,
) -> StarterTemplateLineageInspection:
    """Compare one workspace Template lineage to a package-owned exact prefix."""

    root = Path(workspace_root)
    if not root.exists():
        return StarterTemplateLineageInspection(
            state=STARTER_LINEAGE_MISSING,
            loaded=None,
            matched_version_count=0,
        )
    try:
        loaded = load_current_template(root, lineage.template_id)
    except TemplateStorageNotFoundError:
        return StarterTemplateLineageInspection(
            state=STARTER_LINEAGE_MISSING,
            loaded=None,
            matched_version_count=0,
        )
    except TemplateStorageError as error:
        raise StarterTemplateLineageValidationError(str(error)) from error

    if loaded.definition.artifact_category != lineage.definition.artifact_category:
        return _conflict(
            loaded,
            "Template Definition artifact_category conflicts with package ownership.",
        )

    if len(loaded.versions) > len(lineage.versions):
        return _conflict(
            loaded,
            "workspace lineage extends beyond the package-owned lineage.",
        )

    for index, candidate in enumerate(loaded.versions):
        expected = lineage.versions[index]
        if not _version_semantics_match(candidate, expected.version):
            return _conflict(
                loaded,
                "workspace Template Version does not match the package-owned "
                f"Version at revision {index + 1}.",
                matched=index,
            )
        try:
            rendering = load_template_rendering_specification(
                root,
                lineage.template_id,
                candidate.template_version_id,
            )
        except TemplateStorageError as error:
            raise StarterTemplateLineageValidationError(str(error)) from error
        if rendering != expected.rendering_specification:
            return _conflict(
                loaded,
                "workspace rendering bytes do not match the package-owned "
                f"Version at revision {index + 1}.",
                matched=index,
            )

    matched = len(loaded.versions)
    if matched == 0:
        return _conflict(
            loaded,
            "workspace Template lineage contains no Version.",
        )

    if matched == len(lineage.versions):
        if loaded.definition.status == "retired":
            return StarterTemplateLineageInspection(
                state=STARTER_LINEAGE_CURRENT,
                loaded=loaded,
                matched_version_count=matched,
                reason="exact package lineage is retired by teacher choice",
            )
        head = loaded.head_version
        if (
            head.status == "active"
            and loaded.current_template_version_id == head.template_version_id
        ):
            return StarterTemplateLineageInspection(
                state=STARTER_LINEAGE_CURRENT,
                loaded=loaded,
                matched_version_count=matched,
            )
        if _is_recoverable_draft_head(loaded):
            return StarterTemplateLineageInspection(
                state=STARTER_LINEAGE_UPGRADE_AVAILABLE,
                loaded=loaded,
                matched_version_count=matched,
                reason="exact package successor is present as an unactivated draft",
            )
        return _conflict(
            loaded,
            "complete package lineage has incompatible lifecycle state.",
            matched=matched,
        )

    if loaded.definition.status == "retired":
        return _conflict(
            loaded,
            "retired starter lineage will not be upgraded automatically.",
            matched=matched,
        )

    head = loaded.head_version
    if (
        head.status == "active"
        and loaded.current_template_version_id == head.template_version_id
    ) or _is_recoverable_draft_head(loaded):
        return StarterTemplateLineageInspection(
            state=STARTER_LINEAGE_UPGRADE_AVAILABLE,
            loaded=loaded,
            matched_version_count=matched,
        )

    return _conflict(
        loaded,
        "package prefix has incompatible lifecycle state.",
        matched=matched,
    )


def prepare_packaged_starter_lineage_reconciliation(
    workspace_root: str | Path,
    lineage: PackagedStarterTemplateLineage,
) -> PreparedStarterTemplateLineageReconciliation:
    """Prepare one package reconciliation without canonical mutation."""

    inspection = inspect_packaged_starter_lineage(workspace_root, lineage)
    if inspection.state == STARTER_LINEAGE_CONFLICT:
        raise StarterTemplateLineageConflictError(
            inspection.reason or "starter lineage conflicts with package ownership."
        )
    loaded = inspection.loaded
    return PreparedStarterTemplateLineageReconciliation(
        lineage=lineage,
        initial_state=inspection.state,
        expected_snapshot_revision=(
            None if loaded is None else loaded.snapshot_revision
        ),
        expected_snapshot_sha256=(
            None if loaded is None else loaded.snapshot_sha256
        ),
    )


def commit_packaged_starter_lineage_reconciliation(
    prepared: PreparedStarterTemplateLineageReconciliation,
    *,
    workspace_root: str | Path,
) -> StarterTemplateLineageReconciliationResult:
    """Commit only the exact package lineage reviewed by preparation."""

    root = Path(workspace_root)
    current = inspect_packaged_starter_lineage(root, prepared.lineage)
    if current.state == STARTER_LINEAGE_CONFLICT:
        raise StarterTemplateLineageConflictError(
            current.reason or "starter lineage became incompatible before commit."
        )

    if current.state == STARTER_LINEAGE_CURRENT:
        assert current.loaded is not None
        return StarterTemplateLineageReconciliationResult(
            outcome="already_current",
            loaded=current.loaded,
        )

    if prepared.initial_state == STARTER_LINEAGE_CURRENT:
        raise StarterTemplateLineageConflictError(
            "starter lineage changed after an already-current preview."
        )

    if prepared.initial_state == STARTER_LINEAGE_MISSING:
        if current.state != STARTER_LINEAGE_MISSING:
            raise StarterTemplateLineageConflictError(
                "starter lineage appeared after preparation."
            )
        if not root.exists() or not root.is_dir():
            raise StarterTemplateLineageValidationError(
                "workspace root must exist before package reconciliation."
            )
        loaded = _create_initial_package_version(root, prepared.lineage)
        loaded = _advance_to_package_head(root, prepared.lineage, loaded)
        return StarterTemplateLineageReconciliationResult(
            outcome="installed",
            loaded=loaded,
        )

    if current.state != STARTER_LINEAGE_UPGRADE_AVAILABLE:
        raise StarterTemplateLineageConflictError(
            "starter lineage changed after upgrade preparation."
        )
    assert current.loaded is not None
    if (
        current.loaded.snapshot_revision != prepared.expected_snapshot_revision
        or current.loaded.snapshot_sha256 != prepared.expected_snapshot_sha256
    ):
        raise StarterTemplateLineageConflictError(
            "starter Template snapshot changed after upgrade preparation."
        )
    loaded = _advance_to_package_head(root, prepared.lineage, current.loaded)
    return StarterTemplateLineageReconciliationResult(
        outcome="upgraded",
        loaded=loaded,
    )


def _create_initial_package_version(
    root: Path,
    lineage: PackagedStarterTemplateLineage,
) -> LoadedTemplateLibrary:
    initial = lineage.versions[0]
    try:
        return create_template_library(
            root,
            definition=lineage.definition,
            initial_version=initial.version,
            rendering_specification=initial.rendering_specification,
        )
    except TemplateStorageConflictError as error:
        raise StarterTemplateLineageConflictError(str(error)) from error
    except TemplateStorageError as error:
        raise StarterTemplateLineageValidationError(str(error)) from error


def _advance_to_package_head(
    root: Path,
    lineage: PackagedStarterTemplateLineage,
    loaded: LoadedTemplateLibrary,
) -> LoadedTemplateLibrary:
    """Recover an exact prefix and append/activate each missing package Version."""

    while True:
        if loaded.head_version.status == "draft":
            try:
                loaded = activate_template_version(
                    root,
                    lineage.template_id,
                    loaded.head_template_version_id,
                    expected_snapshot_revision=loaded.snapshot_revision,
                    operation_provenance=loaded.head_version.created_provenance,
                )
            except TemplateStorageConflictError as error:
                raise StarterTemplateLineageConflictError(str(error)) from error
            except TemplateStorageError as error:
                raise StarterTemplateLineageValidationError(str(error)) from error
            continue

        if len(loaded.versions) == len(lineage.versions):
            return loaded

        packaged = lineage.versions[len(loaded.versions)]
        successor = replace(packaged.version, status="draft")
        try:
            loaded = create_successor_template_version(
                root,
                lineage.template_id,
                successor=successor,
                rendering_specification=packaged.rendering_specification,
                expected_snapshot_revision=loaded.snapshot_revision,
                operation_provenance=successor.created_provenance,
            )
        except TemplateStorageConflictError as error:
            raise StarterTemplateLineageConflictError(str(error)) from error
        except TemplateStorageError as error:
            raise StarterTemplateLineageValidationError(str(error)) from error


def _version_semantics_match(
    candidate: TemplateVersion,
    expected: TemplateVersion,
) -> bool:
    normalized = replace(
        expected,
        created_provenance=candidate.created_provenance,
        status=candidate.status,
    )
    return candidate == normalized


def _is_recoverable_draft_head(loaded: LoadedTemplateLibrary) -> bool:
    head = loaded.head_version
    if head.status != "draft":
        return False
    if len(loaded.versions) < 2:
        return False
    previous = loaded.versions[-2]
    return (
        previous.status == "active"
        and loaded.current_template_version_id == previous.template_version_id
    )


def _conflict(
    loaded: LoadedTemplateLibrary,
    reason: str,
    *,
    matched: int = 0,
) -> StarterTemplateLineageInspection:
    return StarterTemplateLineageInspection(
        state=STARTER_LINEAGE_CONFLICT,
        loaded=loaded,
        matched_version_count=matched,
        reason=reason,
    )


__all__ = [
    "STARTER_LINEAGE_CONFLICT",
    "STARTER_LINEAGE_CURRENT",
    "STARTER_LINEAGE_MISSING",
    "STARTER_LINEAGE_UPGRADE_AVAILABLE",
    "PackagedStarterTemplateLineage",
    "PackagedStarterTemplateVersion",
    "PreparedStarterTemplateLineageReconciliation",
    "StarterTemplateLineageConflictError",
    "StarterTemplateLineageError",
    "StarterTemplateLineageInspection",
    "StarterTemplateLineageReconciliationResult",
    "StarterTemplateLineageValidationError",
    "commit_packaged_starter_lineage_reconciliation",
    "inspect_packaged_starter_lineage",
    "prepare_packaged_starter_lineage_reconciliation",
]
