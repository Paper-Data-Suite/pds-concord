"""Strict immutable workspace storage for reusable Concord Templates."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import TypeVar

from pds_core.identifiers import validate_identifier
from pds_core.workspace import resolve_workspace_root

from concord.models import Provenance, TemplateDefinition, TemplateVersion
from concord.template_serialization import (
    TemplateSerializationError,
    canonical_json_bytes,
    dataclass_from_dict,
    dataclass_to_dict,
    strict_json_loads,
    template_from_dict,
    template_to_dict,
)
from concord.template_storage_models import (
    TEMPLATE_LIBRARY_STORAGE_SCHEMA,
    LoadedTemplateLibrary,
    TemplateCurrentSnapshot,
    TemplateLibraryMarker,
    TemplateLibrarySnapshot,
    TemplateRecordRevision,
    TemplateRecordRevisionRef,
)
from concord.template_storage_paths import (
    template_current_path,
    template_library_root,
    template_marker_path,
    template_record_revision_path,
    template_records_root,
    template_rendering_specification_path,
    template_root,
    template_snapshot_path,
    template_snapshots_root,
    template_write_lock_path,
)

T = TypeVar("T")


class TemplateStorageError(RuntimeError):
    """Base reusable Template storage failure."""


class TemplateStorageReadError(TemplateStorageError):
    """Canonical reusable Template state could not be read safely."""


class TemplateStorageIntegrityError(TemplateStorageReadError):
    """Canonical reusable Template state is internally inconsistent."""


class TemplateStorageNotFoundError(TemplateStorageReadError):
    """An explicitly requested reusable Template does not exist."""


class TemplateStorageWriteError(TemplateStorageError):
    """Reusable Template state could not be committed safely."""


class TemplateStorageConflictError(TemplateStorageWriteError):
    """A create-only Template identity already exists."""


def calculate_rendering_specification_sha256(data: bytes) -> str:
    """Return lowercase SHA-256 for exact rendering specification bytes."""
    if not isinstance(data, bytes):
        raise TemplateStorageWriteError(
            "rendering specification must be exact bytes."
        )
    return hashlib.sha256(data).hexdigest()


def list_template_ids(workspace_root: str | Path) -> tuple[str, ...]:
    """List strictly verified Templates by display name and stable ID."""
    root = _workspace_root(workspace_root, for_write=False)
    collection = template_library_root(root)
    _require_safe_descendant(root, collection, allow_missing=True)
    if not os.path.lexists(collection):
        return ()
    if _is_link_like(collection) or not collection.is_dir():
        raise TemplateStorageIntegrityError(
            f"Template library root is not a canonical directory: {collection}"
        )

    try:
        entries = tuple(collection.iterdir())
    except OSError as error:
        raise TemplateStorageReadError(
            f"could not enumerate Template library {collection}: {error}"
        ) from error

    loaded: list[LoadedTemplateLibrary] = []
    for entry in entries:
        if entry.name.startswith("."):
            continue
        if _is_link_like(entry) or not entry.is_dir():
            raise TemplateStorageIntegrityError(
                f"unexpected visible Template library entry: {entry}"
            )
        _validate_identifier(entry.name, "template_id")
        loaded.append(load_current_template(root, entry.name))

    loaded.sort(
        key=lambda item: (
            item.definition.name.casefold(),
            item.definition.template_id,
        )
    )
    return tuple(item.definition.template_id for item in loaded)


def load_current_template(
    workspace_root: str | Path,
    template_id: str,
) -> LoadedTemplateLibrary:
    """Strictly load one Template through its guarded current snapshot."""
    root = _workspace_root(workspace_root, for_write=False)
    template_id = _validate_identifier(template_id, "template_id")
    _load_marker(root, template_id)
    current = _load_dataclass_file(
        root,
        template_current_path(root, template_id),
        TemplateCurrentSnapshot,
        "Template current pointer",
        missing=True,
    )
    if current.template_id != template_id:
        raise TemplateStorageIntegrityError(
            "Template current pointer identity disagrees with its canonical path."
        )
    snapshot, digest = load_template_snapshot(
        root,
        template_id,
        current.snapshot_revision,
    )
    if digest != current.snapshot_sha256:
        raise TemplateStorageIntegrityError(
            "Template current pointer snapshot digest mismatch."
        )
    return _materialize_snapshot(root, snapshot, digest)


def load_template_snapshot(
    workspace_root: str | Path,
    template_id: str,
    snapshot_revision: int,
) -> tuple[TemplateLibrarySnapshot, str]:
    """Load and verify one exact digest-linked historical Template snapshot."""
    root = _workspace_root(workspace_root, for_write=False)
    template_id = _validate_identifier(template_id, "template_id")
    if type(snapshot_revision) is not int or snapshot_revision < 1:
        raise TemplateStorageReadError(
            "snapshot_revision must be a positive integer."
        )
    _load_marker(root, template_id)

    target: TemplateLibrarySnapshot | None = None
    target_bytes: bytes | None = None
    child: TemplateLibrarySnapshot | None = None

    for revision in range(snapshot_revision, 0, -1):
        path = template_snapshot_path(root, template_id, revision)
        snapshot, raw = _load_dataclass_file_with_bytes(
            root,
            path,
            TemplateLibrarySnapshot,
            "Template snapshot",
            missing=True,
        )
        if (
            snapshot.template_id != template_id
            or snapshot.snapshot_revision != revision
        ):
            raise TemplateStorageIntegrityError(
                "Template snapshot identity disagrees with its canonical path."
            )
        if child is not None:
            if child.previous_snapshot_revision != revision:
                raise TemplateStorageIntegrityError(
                    "Template snapshot predecessor revision mismatch."
                )
            if child.previous_snapshot_sha256 != hashlib.sha256(raw).hexdigest():
                raise TemplateStorageIntegrityError(
                    "Template snapshot predecessor digest mismatch."
                )
        if revision == snapshot_revision:
            target = snapshot
            target_bytes = raw
        child = snapshot

    assert target is not None and target_bytes is not None
    assert child is not None
    if (
        child.snapshot_revision != 1
        or child.previous_snapshot_revision is not None
        or child.previous_snapshot_sha256 is not None
    ):
        raise TemplateStorageIntegrityError(
            "Template snapshot history does not terminate at revision 1."
        )
    return target, hashlib.sha256(target_bytes).hexdigest()


def list_template_versions(
    workspace_root: str | Path,
    template_id: str,
) -> tuple[TemplateVersion, ...]:
    """Return every exact Version selected by the current Template snapshot."""
    return load_current_template(workspace_root, template_id).versions


def load_template_version(
    workspace_root: str | Path,
    template_id: str,
    template_version_id: str,
) -> TemplateVersion:
    """Resolve one exact Template Version from the current library history."""
    version_id = _validate_identifier(
        template_version_id,
        "template_version_id",
    )
    match = next(
        (
            item
            for item in list_template_versions(workspace_root, template_id)
            if item.template_version_id == version_id
        ),
        None,
    )
    if match is None:
        raise TemplateStorageNotFoundError(
            f"Template Version not found: {version_id}"
        )
    return match


def load_current_template_version(
    workspace_root: str | Path,
    template_id: str,
) -> TemplateVersion | None:
    """Resolve the explicitly selected active Version, if one exists."""
    return load_current_template(workspace_root, template_id).current_version


def create_template_library(
    workspace_root: str | Path,
    *,
    definition: TemplateDefinition,
    initial_version: TemplateVersion,
    rendering_specification: bytes,
) -> LoadedTemplateLibrary:
    """Create one Template lineage; current.json is installed last."""
    root = _workspace_root(workspace_root, for_write=True)
    if not isinstance(definition, TemplateDefinition):
        raise TemplateStorageWriteError(
            "definition must be TemplateDefinition."
        )
    if not isinstance(initial_version, TemplateVersion):
        raise TemplateStorageWriteError(
            "initial_version must be TemplateVersion."
        )
    if not isinstance(rendering_specification, bytes):
        raise TemplateStorageWriteError(
            "rendering_specification must be exact bytes."
        )
    _validate_initial_pair(definition, initial_version, rendering_specification)

    template_id = definition.template_id
    collection = template_library_root(root)
    target_root = template_root(root, template_id)
    _require_safe_descendant(root, collection, allow_missing=True)
    if os.path.lexists(target_root):
        raise TemplateStorageConflictError(
            f"Template identity already exists: {template_id}"
        )

    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        _ensure_directory_chain(root, collection, created_dirs)
        try:
            target_root.mkdir()
        except FileExistsError as error:
            raise TemplateStorageConflictError(
                f"Template identity already exists: {template_id}"
            ) from error
        created_dirs.append(target_root)
        _require_safe_descendant(root, target_root)

        marker_path = template_marker_path(root, template_id)
        definition_path = template_record_revision_path(
            root,
            template_id,
            "template_definition",
            definition.template_id,
            1,
        )
        version_path = template_record_revision_path(
            root,
            template_id,
            "template_version",
            initial_version.template_version_id,
            1,
        )
        asset_path = template_rendering_specification_path(
            root,
            template_id,
            initial_version.rendering_specification_reference,
        )
        snapshot_path = template_snapshot_path(root, template_id, 1)
        current_path = template_current_path(root, template_id)

        for parent in (
            marker_path.parent,
            definition_path.parent,
            version_path.parent,
            asset_path.parent,
            snapshot_path.parent,
        ):
            _ensure_directory_chain(root, parent, created_dirs)

        marker = TemplateLibraryMarker(
            storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
            template_id=template_id,
            created_provenance=definition.created_provenance,
        )
        marker_bytes = canonical_json_bytes(dataclass_to_dict(marker))

        definition_revision = TemplateRecordRevision(
            storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
            template_id=template_id,
            record_kind="template_definition",
            record_id=definition.template_id,
            record_revision=1,
            operation="create",
            operation_provenance=definition.created_provenance,
            body=template_to_dict(definition),
        )
        definition_bytes = canonical_json_bytes(
            dataclass_to_dict(definition_revision)
        )
        version_revision = TemplateRecordRevision(
            storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
            template_id=template_id,
            record_kind="template_version",
            record_id=initial_version.template_version_id,
            record_revision=1,
            operation="create",
            operation_provenance=initial_version.created_provenance,
            body=template_to_dict(initial_version),
        )
        version_bytes = canonical_json_bytes(
            dataclass_to_dict(version_revision)
        )

        refs = tuple(
            sorted(
                (
                    TemplateRecordRevisionRef(
                        record_kind="template_definition",
                        record_id=definition.template_id,
                        record_revision=1,
                        sha256=hashlib.sha256(definition_bytes).hexdigest(),
                    ),
                    TemplateRecordRevisionRef(
                        record_kind="template_version",
                        record_id=initial_version.template_version_id,
                        record_revision=1,
                        sha256=hashlib.sha256(version_bytes).hexdigest(),
                    ),
                ),
                key=lambda item: (item.record_kind, item.record_id),
            )
        )
        current_version_id = (
            initial_version.template_version_id
            if initial_version.status == "active"
            else None
        )
        snapshot = TemplateLibrarySnapshot(
            storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
            template_id=template_id,
            snapshot_revision=1,
            records=refs,
            current_template_version_id=current_version_id,
            head_template_version_id=initial_version.template_version_id,
            previous_snapshot_revision=None,
            previous_snapshot_sha256=None,
            operation="create",
            operation_provenance=definition.created_provenance,
        )
        snapshot_bytes = canonical_json_bytes(dataclass_to_dict(snapshot))
        current = TemplateCurrentSnapshot(
            storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
            template_id=template_id,
            snapshot_revision=1,
            snapshot_sha256=hashlib.sha256(snapshot_bytes).hexdigest(),
        )
        current_bytes = canonical_json_bytes(dataclass_to_dict(current))

        for path, data in (
            (marker_path, marker_bytes),
            (definition_path, definition_bytes),
            (version_path, version_bytes),
            (asset_path, rendering_specification),
            (snapshot_path, snapshot_bytes),
        ):
            _write_exclusive(root, path, data)
            created_files.append(path)

        _load_marker(root, template_id)
        _load_record_revision(
            root,
            template_id,
            "template_definition",
            definition.template_id,
            1,
        )
        _load_record_revision(
            root,
            template_id,
            "template_version",
            initial_version.template_version_id,
            1,
        )
        _verify_rendering_asset(root, template_id, initial_version)
        loaded_snapshot, loaded_digest = load_template_snapshot(
            root,
            template_id,
            1,
        )
        if loaded_snapshot != snapshot or loaded_digest != current.snapshot_sha256:
            raise TemplateStorageWriteError(
                "new Template snapshot did not verify before commit."
            )

        _write_exclusive(root, current_path, current_bytes)
        created_files.append(current_path)
        loaded = load_current_template(root, template_id)
        if (
            loaded.definition != definition
            or loaded.versions != (initial_version,)
            or loaded.snapshot_revision != 1
        ):
            raise TemplateStorageWriteError(
                "persisted Template differs from the requested initial state."
            )
        return loaded
    except TemplateStorageError:
        _rollback_created(created_files, created_dirs)
        raise
    except (OSError, ValueError, TemplateSerializationError) as error:
        _rollback_created(created_files, created_dirs)
        raise TemplateStorageWriteError(
            f"Template creation did not commit: {error}"
        ) from error


def _materialize_snapshot(
    root: Path,
    snapshot: TemplateLibrarySnapshot,
    snapshot_digest: str,
) -> LoadedTemplateLibrary:
    selected: list[TemplateDefinition | TemplateVersion] = []
    for ref in snapshot.records:
        record, raw = _load_record_revision(
            root,
            snapshot.template_id,
            ref.record_kind,
            ref.record_id,
            ref.record_revision,
        )
        if hashlib.sha256(raw).hexdigest() != ref.sha256:
            raise TemplateStorageIntegrityError(
                f"record digest mismatch for {ref.record_kind}:{ref.record_id}."
            )
        selected.append(record)

    definitions = [
        item for item in selected if isinstance(item, TemplateDefinition)
    ]
    versions = [
        item for item in selected if isinstance(item, TemplateVersion)
    ]
    if len(definitions) != 1:
        raise TemplateStorageIntegrityError(
            "Template snapshot must select exactly one TemplateDefinition."
        )
    definition = definitions[0]
    if definition.template_id != snapshot.template_id:
        raise TemplateStorageIntegrityError(
            "Template Definition identity disagrees with snapshot."
        )
    if not versions:
        raise TemplateStorageIntegrityError(
            "Template snapshot must select at least one TemplateVersion."
        )
    versions.sort(key=lambda item: item.revision_sequence)
    ordered_versions = tuple(versions)
    _validate_lineage(definition, ordered_versions, snapshot)
    for version in ordered_versions:
        _verify_rendering_asset(root, snapshot.template_id, version)

    return LoadedTemplateLibrary(
        definition=definition,
        versions=ordered_versions,
        snapshot_revision=snapshot.snapshot_revision,
        snapshot_sha256=snapshot_digest,
        current_template_version_id=snapshot.current_template_version_id,
        head_template_version_id=snapshot.head_template_version_id,
    )


def _validate_lineage(
    definition: TemplateDefinition,
    versions: tuple[TemplateVersion, ...],
    snapshot: TemplateLibrarySnapshot,
) -> None:
    expected_sequences = tuple(range(1, len(versions) + 1))
    actual_sequences = tuple(item.revision_sequence for item in versions)
    if actual_sequences != expected_sequences:
        raise TemplateStorageIntegrityError(
            "Template Version revision_sequence must form contiguous 1..N history."
        )
    ids = tuple(item.template_version_id for item in versions)
    if len(set(ids)) != len(ids):
        raise TemplateStorageIntegrityError(
            "Template Version identities must be unique within one lineage."
        )
    for index, version in enumerate(versions):
        if version.template_id != definition.template_id:
            raise TemplateStorageIntegrityError(
                "Template Version belongs to another Template Definition."
            )
        if version.artifact_category != definition.artifact_category:
            raise TemplateStorageIntegrityError(
                "Template Version artifact_category disagrees with its Definition."
            )
        expected_predecessor = (
            None
            if index == 0
            else versions[index - 1].template_version_id
        )
        if version.supersedes_template_version_id != expected_predecessor:
            raise TemplateStorageIntegrityError(
                "Template Version predecessor chain is not linear and exact."
            )

    if snapshot.head_template_version_id != versions[-1].template_version_id:
        raise TemplateStorageIntegrityError(
            "head_template_version_id does not identify the lineage head."
        )

    active = tuple(item for item in versions if item.status == "active")
    if snapshot.current_template_version_id is None:
        if active:
            raise TemplateStorageIntegrityError(
                "Template snapshot has active Version(s) but no current selection."
            )
    else:
        if len(active) != 1:
            raise TemplateStorageIntegrityError(
                "Template snapshot must have exactly one active current Version."
            )
        if active[0].template_version_id != snapshot.current_template_version_id:
            raise TemplateStorageIntegrityError(
                "current_template_version_id does not identify the active Version."
            )

    if (
        definition.status == "draft"
        and snapshot.current_template_version_id is not None
    ):
        raise TemplateStorageIntegrityError(
            "draft Template Definition must not have a current active Version."
        )
    if (
        definition.status == "active"
        and snapshot.current_template_version_id is None
    ):
        raise TemplateStorageIntegrityError(
            "active Template Definition requires a current active Version."
        )
    if (
        definition.status == "retired"
        and snapshot.current_template_version_id is not None
    ):
        raise TemplateStorageIntegrityError(
            "retired Template Definition must not have a current Version."
        )


def _validate_initial_pair(
    definition: TemplateDefinition,
    version: TemplateVersion,
    rendering_specification: bytes,
) -> None:
    if definition.template_id != version.template_id:
        raise TemplateStorageWriteError(
            "initial Template Definition and Version must share template_id."
        )
    if definition.artifact_category != version.artifact_category:
        raise TemplateStorageWriteError(
            "initial Template Definition and Version artifact_category must match."
        )
    if (
        version.revision_sequence != 1
        or version.supersedes_template_version_id is not None
    ):
        raise TemplateStorageWriteError(
            "initial Template Version must be revision 1 with no predecessor."
        )
    if (definition.status, version.status) not in {
        ("draft", "draft"),
        ("active", "active"),
    }:
        raise TemplateStorageWriteError(
            "initial Template status must be draft/draft or active/active."
        )
    digest = calculate_rendering_specification_sha256(rendering_specification)
    if digest != version.rendering_specification_sha256:
        raise TemplateStorageWriteError(
            "rendering specification bytes do not match "
            "rendering_specification_sha256."
        )


def _load_marker(root: Path, template_id: str) -> TemplateLibraryMarker:
    marker = _load_dataclass_file(
        root,
        template_marker_path(root, template_id),
        TemplateLibraryMarker,
        "Template library marker",
        missing=True,
    )
    if marker.template_id != template_id:
        raise TemplateStorageIntegrityError(
            "Template marker identity disagrees with its canonical path."
        )
    return marker


def _load_record_revision(
    root: Path,
    template_id: str,
    record_kind: str,
    record_id: str,
    revision: int,
) -> tuple[TemplateDefinition | TemplateVersion, bytes]:
    path = template_record_revision_path(
        root,
        template_id,
        record_kind,
        record_id,
        revision,
    )
    envelope, raw = _load_dataclass_file_with_bytes(
        root,
        path,
        TemplateRecordRevision,
        "Template record revision",
        missing=True,
    )
    if (
        envelope.template_id != template_id
        or envelope.record_kind != record_kind
        or envelope.record_id != record_id
        or envelope.record_revision != revision
    ):
        raise TemplateStorageIntegrityError(
            "Template record envelope identity disagrees with its canonical path."
        )
    try:
        record = template_from_dict(record_kind, envelope.body)
    except TemplateSerializationError as error:
        raise TemplateStorageIntegrityError(
            f"invalid reusable Template record body: {error}"
        ) from error
    expected_id = (
        record.template_id
        if isinstance(record, TemplateDefinition)
        else record.template_version_id
    )
    if expected_id != record_id:
        raise TemplateStorageIntegrityError(
            "Template record body identity disagrees with its envelope."
        )
    if (
        record.template_id != template_id
        or template_to_dict(record) != envelope.body
    ):
        raise TemplateStorageIntegrityError(
            "Template record body disagrees with canonical typed round trip."
        )
    return record, raw


def _verify_rendering_asset(
    root: Path,
    template_id: str,
    version: TemplateVersion,
) -> bytes:
    path = template_rendering_specification_path(
        root,
        template_id,
        version.rendering_specification_reference,
    )
    data = _read_regular_file(
        root,
        path,
        "Template rendering specification",
        missing=True,
    )
    digest = hashlib.sha256(data).hexdigest()
    if digest != version.rendering_specification_sha256:
        raise TemplateStorageIntegrityError(
            "Template rendering specification digest mismatch for "
            f"{version.template_version_id}."
        )
    return data


def _load_dataclass_file(
    root: Path,
    path: Path,
    cls: type[T],
    description: str,
    *,
    missing: bool,
) -> T:
    value, _ = _load_dataclass_file_with_bytes(
        root,
        path,
        cls,
        description,
        missing=missing,
    )
    return value


def _load_dataclass_file_with_bytes(
    root: Path,
    path: Path,
    cls: type[T],
    description: str,
    *,
    missing: bool,
) -> tuple[T, bytes]:
    data = _read_regular_file(root, path, description, missing=missing)
    try:
        parsed = strict_json_loads(data, description=description)
        model = dataclass_from_dict(cls, parsed)
        canonical = canonical_json_bytes(dataclass_to_dict(model))
    except (TemplateSerializationError, ValueError) as error:
        raise TemplateStorageIntegrityError(
            f"invalid canonical {description} at {path}: {error}"
        ) from error
    if canonical != data:
        raise TemplateStorageIntegrityError(
            f"{description} is not canonical at {path}."
        )
    return model, data


def _workspace_root(workspace_root: str | Path, *, for_write: bool) -> Path:
    try:
        root = resolve_workspace_root(workspace_root)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise TemplateStorageError(
            f"invalid workspace root {workspace_root!r}: {error}"
        ) from error
    if not os.path.lexists(root):
        raise TemplateStorageError(f"workspace root does not exist: {root}")
    if _is_link_like(root) or not root.is_dir():
        raise TemplateStorageError(
            f"workspace root must be an ordinary non-link directory: {root}"
        )
    if for_write and not os.access(root, os.W_OK):
        raise TemplateStorageWriteError(
            f"workspace root is not writable: {root}"
        )
    return root


def _read_regular_file(
    root: Path,
    path: Path,
    description: str,
    *,
    missing: bool,
) -> bytes:
    _require_safe_descendant(root, path, allow_missing=missing)
    if not os.path.lexists(path):
        if missing:
            raise TemplateStorageNotFoundError(
                f"{description} not found: {path}"
            )
        raise TemplateStorageIntegrityError(
            f"{description} is missing: {path}"
        )
    if _is_link_like(path) or not path.is_file():
        raise TemplateStorageIntegrityError(
            f"{description} must be an ordinary non-link file: {path}"
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise TemplateStorageReadError(
            f"could not read {description} {path}: {error}"
        ) from error


def _require_safe_descendant(
    root: Path,
    path: Path,
    *,
    allow_missing: bool = False,
) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise TemplateStorageIntegrityError(
            f"Template path escapes workspace root: {path}"
        ) from error

    if _is_link_like(root) or not root.is_dir():
        raise TemplateStorageIntegrityError(
            f"workspace root is not a safe directory: {root}"
        )
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        leaf = index == len(relative.parts) - 1
        if not os.path.lexists(current):
            if allow_missing:
                return
            raise TemplateStorageIntegrityError(
                f"canonical Template path component is missing: {current}"
            )
        if _is_link_like(current):
            raise TemplateStorageIntegrityError(
                f"canonical Template path traverses a link-like object: {current}"
            )
        if not leaf and not current.is_dir():
            raise TemplateStorageIntegrityError(
                f"canonical Template path ancestor is not a directory: {current}"
            )


def _is_link_like(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise TemplateStorageIntegrityError(
            f"could not inspect canonical path {path}: {error}"
        ) from error
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse and attributes & reparse)


def _ensure_directory_chain(
    root: Path,
    target: Path,
    created: list[Path],
) -> None:
    try:
        relative = target.relative_to(root)
    except ValueError as error:
        raise TemplateStorageWriteError(
            f"Template directory escapes workspace root: {target}"
        ) from error

    current = root
    for part in relative.parts:
        current = current / part
        if os.path.lexists(current):
            if _is_link_like(current) or not current.is_dir():
                raise TemplateStorageIntegrityError(
                    f"Template directory path is unsafe: {current}"
                )
            continue
        try:
            current.mkdir()
        except FileExistsError:
            if _is_link_like(current) or not current.is_dir():
                raise TemplateStorageIntegrityError(
                    f"Template directory raced to an unsafe object: {current}"
                )
        except OSError as error:
            raise TemplateStorageWriteError(
                f"could not create Template directory {current}: {error}"
            ) from error
        else:
            created.append(current)
        if _is_link_like(current) or not current.is_dir():
            raise TemplateStorageIntegrityError(
                f"created Template directory is unsafe: {current}"
            )


def _write_exclusive(root: Path, path: Path, data: bytes) -> None:
    _require_safe_descendant(root, path.parent)
    created = False
    try:
        with path.open("xb") as target:
            created = True
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
    except FileExistsError as error:
        raise TemplateStorageConflictError(
            f"immutable canonical file already exists: {path}"
        ) from error
    except OSError as error:
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise TemplateStorageWriteError(
            f"could not create immutable canonical file {path}: {error}"
        ) from error


def _rollback_created(files: list[Path], directories: list[Path]) -> None:
    for path in reversed(files):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass
    for path in reversed(directories):
        try:
            path.rmdir()
        except OSError:
            pass


def _validate_identifier(value: object, name: str) -> str:
    try:
        return validate_identifier(value, name)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise TemplateStorageReadError(str(error)) from error

class TemplateStoragePartialSuccessError(TemplateStorageWriteError):
    """A Template mutation published durable state but could not finish cleanly."""

    def __init__(
        self,
        message: str,
        *,
        pointer_published: bool,
        snapshot_revision: int | None,
        snapshot_sha256: str | None,
    ) -> None:
        super().__init__(message)
        self.pointer_published = pointer_published
        self.snapshot_revision = snapshot_revision
        self.snapshot_sha256 = snapshot_sha256


def create_successor_template_version(
    workspace_root: str | Path,
    template_id: str,
    *,
    successor: TemplateVersion,
    rendering_specification: bytes,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedTemplateLibrary:
    """Append one exact draft successor without changing current selection."""

    def plan(
        loaded: LoadedTemplateLibrary,
    ) -> tuple[
        tuple[TemplateDefinition | TemplateVersion, ...],
        str | None,
        str,
        tuple[str, bytes] | None,
        bool,
    ]:
        head = loaded.head_version
        if loaded.definition.status == "retired":
            raise TemplateStorageWriteError(
                "retired Template Definitions cannot receive successors."
            )
        if successor.template_id != loaded.definition.template_id:
            raise TemplateStorageWriteError(
                "successor template_id must match the Template Definition."
            )
        if successor.artifact_category != loaded.definition.artifact_category:
            raise TemplateStorageWriteError(
                "successor artifact_category must match the Template Definition."
            )
        if successor.status != "draft":
            raise TemplateStorageWriteError(
                "new Template successors must begin in draft status."
            )
        if successor.template_version_id in {
            item.template_version_id for item in loaded.versions
        }:
            raise TemplateStorageConflictError(
                "successor template_version_id already exists."
            )
        if successor.revision_sequence != head.revision_sequence + 1:
            raise TemplateStorageWriteError(
                "successor revision_sequence must be exactly head + 1."
            )
        if successor.supersedes_template_version_id != head.template_version_id:
            raise TemplateStorageWriteError(
                "successor must supersede the exact current lineage head."
            )
        digest = calculate_rendering_specification_sha256(
            rendering_specification
        )
        if digest != successor.rendering_specification_sha256:
            raise TemplateStorageWriteError(
                "rendering specification bytes do not match the successor digest."
            )
        return (
            (successor,),
            loaded.current_template_version_id,
            successor.template_version_id,
            (
                successor.rendering_specification_reference,
                rendering_specification,
            ),
            False,
        )

    return _commit_template_mutation(
        workspace_root,
        template_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="revise",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def activate_template_version(
    workspace_root: str | Path,
    template_id: str,
    template_version_id: str,
    *,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedTemplateLibrary:
    """Activate the draft lineage head and supersede the previous current Version."""
    target_id = _validate_identifier(
        template_version_id,
        "template_version_id",
    )

    def plan(
        loaded: LoadedTemplateLibrary,
    ) -> tuple[
        tuple[TemplateDefinition | TemplateVersion, ...],
        str | None,
        str,
        tuple[str, bytes] | None,
        bool,
    ]:
        if loaded.definition.status == "retired":
            raise TemplateStorageWriteError(
                "retired Template Definitions cannot be activated."
            )
        candidate = next(
            (
                item
                for item in loaded.versions
                if item.template_version_id == target_id
            ),
            None,
        )
        if candidate is None:
            raise TemplateStorageNotFoundError(
                f"Template Version not found: {target_id}"
            )
        if candidate.template_version_id != loaded.head_template_version_id:
            raise TemplateStorageConflictError(
                "only the exact current lineage head can be activated."
            )
        if candidate.status != "draft":
            raise TemplateStorageConflictError(
                "Template Version activation requires a draft head."
            )

        changes: list[TemplateDefinition | TemplateVersion] = [
            replace(candidate, status="active")
        ]
        if loaded.current_version is not None:
            if loaded.current_version.status != "active":
                raise TemplateStorageIntegrityError(
                    "current Template Version is not active."
                )
            changes.append(
                replace(loaded.current_version, status="superseded")
            )
        if loaded.definition.status == "draft":
            changes.append(replace(loaded.definition, status="active"))
        elif loaded.definition.status != "active":
            raise TemplateStorageIntegrityError(
                "Template Definition lifecycle is incompatible with activation."
            )
        return (
            tuple(changes),
            candidate.template_version_id,
            loaded.head_template_version_id,
            None,
            False,
        )

    return _commit_template_mutation(
        workspace_root,
        template_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="activate",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def update_template_definition(
    workspace_root: str | Path,
    template_id: str,
    *,
    definition: TemplateDefinition,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedTemplateLibrary:
    """Persist an immutable metadata revision of one Template Definition."""

    def plan(
        loaded: LoadedTemplateLibrary,
    ) -> tuple[
        tuple[TemplateDefinition | TemplateVersion, ...],
        str | None,
        str,
        tuple[str, bytes] | None,
        bool,
    ]:
        current = loaded.definition
        if current.status == "retired":
            raise TemplateStorageWriteError(
                "retired Template Definitions cannot be updated."
            )
        immutable_same = (
            definition.template_id == current.template_id
            and definition.artifact_category == current.artifact_category
            and definition.created_provenance == current.created_provenance
            and definition.owner_reference == current.owner_reference
            and definition.status == current.status
        )
        if not immutable_same:
            raise TemplateStorageWriteError(
                "Template Definition update may change only name, purpose, "
                "and description."
            )
        if definition == current:
            return (
                (),
                loaded.current_template_version_id,
                loaded.head_template_version_id,
                None,
                True,
            )
        return (
            (definition,),
            loaded.current_template_version_id,
            loaded.head_template_version_id,
            None,
            False,
        )

    return _commit_template_mutation(
        workspace_root,
        template_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="update",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def retire_template_version(
    workspace_root: str | Path,
    template_id: str,
    template_version_id: str,
    *,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedTemplateLibrary:
    """Retire one non-current draft Template Version without deleting history."""
    target_id = _validate_identifier(
        template_version_id,
        "template_version_id",
    )

    def plan(
        loaded: LoadedTemplateLibrary,
    ) -> tuple[
        tuple[TemplateDefinition | TemplateVersion, ...],
        str | None,
        str,
        tuple[str, bytes] | None,
        bool,
    ]:
        if loaded.definition.status == "retired":
            raise TemplateStorageWriteError(
                "the whole Template Definition is already retired."
            )
        candidate = next(
            (
                item
                for item in loaded.versions
                if item.template_version_id == target_id
            ),
            None,
        )
        if candidate is None:
            raise TemplateStorageNotFoundError(
                f"Template Version not found: {target_id}"
            )
        if candidate.template_version_id == loaded.current_template_version_id:
            raise TemplateStorageConflictError(
                "the active current Template Version cannot be retired "
                "independently."
            )
        if candidate.status != "draft":
            raise TemplateStorageConflictError(
                "only a non-current draft Template Version can be retired."
            )
        return (
            (replace(candidate, status="retired"),),
            loaded.current_template_version_id,
            loaded.head_template_version_id,
            None,
            False,
        )

    return _commit_template_mutation(
        workspace_root,
        template_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="retire-version",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def retire_template(
    workspace_root: str | Path,
    template_id: str,
    *,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedTemplateLibrary:
    """Retire one Template Definition and clear its current selection."""

    def plan(
        loaded: LoadedTemplateLibrary,
    ) -> tuple[
        tuple[TemplateDefinition | TemplateVersion, ...],
        str | None,
        str,
        tuple[str, bytes] | None,
        bool,
    ]:
        if loaded.definition.status == "retired":
            return (
                (),
                None,
                loaded.head_template_version_id,
                None,
                True,
            )
        changes: list[TemplateDefinition | TemplateVersion] = [
            replace(loaded.definition, status="retired")
        ]
        if loaded.current_version is not None:
            if loaded.current_version.status != "active":
                raise TemplateStorageIntegrityError(
                    "current Template Version is not active."
                )
            changes.append(
                replace(loaded.current_version, status="retired")
            )
        return (
            tuple(changes),
            None,
            loaded.head_template_version_id,
            None,
            False,
        )

    return _commit_template_mutation(
        workspace_root,
        template_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="retire",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def _commit_template_mutation(
    workspace_root: str | Path,
    template_id: str,
    *,
    expected_snapshot_revision: int,
    operation: str,
    operation_provenance: Provenance,
    planner: Callable[
        [LoadedTemplateLibrary],
        tuple[
            tuple[TemplateDefinition | TemplateVersion, ...],
            str | None,
            str,
            tuple[str, bytes] | None,
            bool,
        ],
    ],
) -> LoadedTemplateLibrary:
    if (
        type(expected_snapshot_revision) is not int
        or expected_snapshot_revision < 1
    ):
        raise TemplateStorageWriteError(
            "expected_snapshot_revision must be a positive integer."
        )
    if not isinstance(operation_provenance, Provenance):
        raise TemplateStorageWriteError(
            "operation_provenance must be Provenance."
        )
    operation = _validate_identifier(operation, "operation")
    root = _workspace_root(workspace_root, for_write=True)
    template_id = _validate_identifier(template_id, "template_id")
    _load_marker(root, template_id)
    lock = _acquire_template_lock(root, template_id, operation)
    pointer_published = False
    published_revision: int | None = None
    published_digest: str | None = None
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    operation_error: Exception | None = None
    result: LoadedTemplateLibrary | None = None

    try:
        loaded = load_current_template(root, template_id)
        if loaded.snapshot_revision != expected_snapshot_revision:
            raise TemplateStorageConflictError(
                f"expected Template snapshot {expected_snapshot_revision}, "
                f"found {loaded.snapshot_revision}."
            )
        current_snapshot, current_digest = load_template_snapshot(
            root,
            template_id,
            loaded.snapshot_revision,
        )
        _validate_template_write_history(
            root,
            template_id,
            current_snapshot,
        )

        changes, next_current, next_head, asset, no_op = planner(loaded)
        if no_op:
            result = loaded
        else:
            selected = {
                (item.record_kind, item.record_id): item
                for item in current_snapshot.records
            }
            next_refs: dict[
                tuple[str, str],
                TemplateRecordRevisionRef,
            ] = dict(selected)

            for record in changes:
                if isinstance(record, TemplateDefinition):
                    kind = "template_definition"
                    record_id = record.template_id
                else:
                    kind = "template_version"
                    record_id = record.template_version_id
                identity = (kind, record_id)
                old_ref = selected.get(identity)
                if old_ref is None:
                    next_record_revision = 1
                else:
                    old_record, _ = _load_record_revision(
                        root,
                        template_id,
                        kind,
                        record_id,
                        old_ref.record_revision,
                    )
                    if template_to_dict(old_record) == template_to_dict(record):
                        continue
                    next_record_revision = old_ref.record_revision + 1
                path = template_record_revision_path(
                    root,
                    template_id,
                    kind,
                    record_id,
                    next_record_revision,
                )
                if os.path.lexists(path):
                    raise TemplateStorageIntegrityError(
                        "orphan/colliding Template record revision blocks commit: "
                        f"{kind}:{record_id}:{next_record_revision}"
                    )
                _ensure_directory_chain(root, path.parent, created_dirs)
                envelope = TemplateRecordRevision(
                    storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
                    template_id=template_id,
                    record_kind=kind,
                    record_id=record_id,
                    record_revision=next_record_revision,
                    operation=operation,
                    operation_provenance=operation_provenance,
                    body=template_to_dict(record),
                )
                data = canonical_json_bytes(dataclass_to_dict(envelope))
                _write_exclusive(root, path, data)
                created_files.append(path)
                persisted, persisted_bytes = _load_record_revision(
                    root,
                    template_id,
                    kind,
                    record_id,
                    next_record_revision,
                )
                if persisted != record or persisted_bytes != data:
                    raise TemplateStorageIntegrityError(
                        "new Template record revision failed exact verification."
                    )
                next_refs[identity] = TemplateRecordRevisionRef(
                    record_kind=kind,
                    record_id=record_id,
                    record_revision=next_record_revision,
                    sha256=hashlib.sha256(data).hexdigest(),
                )

            if asset is not None:
                reference, data = asset
                asset_path = template_rendering_specification_path(
                    root,
                    template_id,
                    reference,
                )
                _ensure_directory_chain(root, asset_path.parent, created_dirs)
                if os.path.lexists(asset_path):
                    existing = _read_regular_file(
                        root,
                        asset_path,
                        "Template rendering specification",
                        missing=False,
                    )
                    if existing != data:
                        raise TemplateStorageConflictError(
                            "rendering specification reference already exists "
                            "with different bytes."
                        )
                else:
                    _write_exclusive(root, asset_path, data)
                    created_files.append(asset_path)

            next_revision = loaded.snapshot_revision + 1
            next_snapshot_path = template_snapshot_path(
                root,
                template_id,
                next_revision,
            )
            if os.path.lexists(next_snapshot_path):
                raise TemplateStorageIntegrityError(
                    "orphan/colliding Template snapshot blocks commit."
                )
            snapshot = TemplateLibrarySnapshot(
                storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
                template_id=template_id,
                snapshot_revision=next_revision,
                records=tuple(
                    sorted(
                        next_refs.values(),
                        key=lambda item: (
                            item.record_kind,
                            item.record_id,
                        ),
                    )
                ),
                current_template_version_id=next_current,
                head_template_version_id=next_head,
                previous_snapshot_revision=loaded.snapshot_revision,
                previous_snapshot_sha256=current_digest,
                operation=operation,
                operation_provenance=operation_provenance,
            )
            snapshot_data = canonical_json_bytes(dataclass_to_dict(snapshot))
            _write_exclusive(root, next_snapshot_path, snapshot_data)
            created_files.append(next_snapshot_path)
            verified_snapshot, verified_digest = load_template_snapshot(
                root,
                template_id,
                next_revision,
            )
            if verified_snapshot != snapshot:
                raise TemplateStorageIntegrityError(
                    "new Template snapshot failed exact verification."
                )
            pointer = TemplateCurrentSnapshot(
                storage_schema_version=TEMPLATE_LIBRARY_STORAGE_SCHEMA,
                template_id=template_id,
                snapshot_revision=next_revision,
                snapshot_sha256=verified_digest,
            )
            current_path = template_current_path(root, template_id)
            _publish_template_current(
                root,
                current_path,
                canonical_json_bytes(dataclass_to_dict(pointer)),
            )
            pointer_published = True
            published_revision = next_revision
            published_digest = verified_digest
            _fsync_directory_if_supported(current_path.parent)
            result = load_current_template(root, template_id)
    except Exception as error:
        operation_error = error
        if not pointer_published:
            _rollback_created(created_files, created_dirs)
    finally:
        cleanup_error = _release_template_lock(lock)

    if operation_error is not None:
        if pointer_published:
            raise TemplateStoragePartialSuccessError(
                "Template current state was published, but final verification "
                "did not complete cleanly.",
                pointer_published=True,
                snapshot_revision=published_revision,
                snapshot_sha256=published_digest,
            ) from operation_error
        raise operation_error
    if cleanup_error is not None:
        raise TemplateStoragePartialSuccessError(
            "Template mutation succeeded, but write.lock could not be removed.",
            pointer_published=pointer_published,
            snapshot_revision=published_revision,
            snapshot_sha256=published_digest,
        ) from cleanup_error
    if result is None:
        raise TemplateStorageWriteError(
            "Template mutation produced no result."
        )
    return result


def _validate_template_write_history(
    root: Path,
    template_id: str,
    current_snapshot: TemplateLibrarySnapshot,
) -> None:
    snapshots = _visible_entries(
        root,
        template_snapshots_root(root, template_id),
        "Template snapshots",
    )
    revisions: list[int] = []
    for path in snapshots:
        if (
            _is_link_like(path)
            or not path.is_file()
            or not path.name.endswith(".json")
            or not path.stem.isdigit()
            or path.stem.startswith("0")
        ):
            raise TemplateStorageIntegrityError(
                f"unexpected Template snapshot entry: {path}"
            )
        revisions.append(int(path.stem))
    if tuple(sorted(revisions)) != tuple(
        range(1, current_snapshot.snapshot_revision + 1)
    ):
        raise TemplateStorageIntegrityError(
            "Template snapshot history is noncontiguous or contains orphans."
        )

    selected = {
        (item.record_kind, item.record_id): item
        for item in current_snapshot.records
    }
    records_root = template_records_root(root, template_id)
    discovered: set[tuple[str, str]] = set()
    for kind_path in _visible_entries(
        root,
        records_root,
        "Template record kinds",
    ):
        if (
            kind_path.name not in {"template_definition", "template_version"}
            or _is_link_like(kind_path)
            or not kind_path.is_dir()
        ):
            raise TemplateStorageIntegrityError(
                f"unexpected Template record kind entry: {kind_path}"
            )
        for identity_path in _visible_entries(
            root,
            kind_path,
            "Template record identities",
        ):
            if _is_link_like(identity_path) or not identity_path.is_dir():
                raise TemplateStorageIntegrityError(
                    f"unexpected Template record identity entry: {identity_path}"
                )
            _validate_identifier(identity_path.name, "record_id")
            identity = (kind_path.name, identity_path.name)
            discovered.add(identity)
            ref = selected.get(identity)
            if ref is None:
                raise TemplateStorageIntegrityError(
                    "orphan Template record identity blocks mutation: "
                    f"{identity[0]}:{identity[1]}"
                )
            revisions_root = identity_path / "revisions"
            revision_entries = _visible_entries(
                root,
                revisions_root,
                "Template record revisions",
            )
            record_revisions: list[int] = []
            for revision_path in revision_entries:
                if (
                    _is_link_like(revision_path)
                    or not revision_path.is_file()
                    or not revision_path.name.endswith(".json")
                    or not revision_path.stem.isdigit()
                    or revision_path.stem.startswith("0")
                ):
                    raise TemplateStorageIntegrityError(
                        "unexpected Template record revision entry: "
                        f"{revision_path}"
                    )
                record_revisions.append(int(revision_path.stem))
            if tuple(sorted(record_revisions)) != tuple(
                range(1, ref.record_revision + 1)
            ):
                raise TemplateStorageIntegrityError(
                    "Template record history is noncontiguous or contains "
                    f"orphans for {identity[0]}:{identity[1]}."
                )
    if discovered != set(selected):
        raise TemplateStorageIntegrityError(
            "Template record identities disagree with the current snapshot."
        )


def _visible_entries(
    root: Path,
    path: Path,
    description: str,
) -> tuple[Path, ...]:
    _require_safe_descendant(root, path, allow_missing=True)
    if not os.path.lexists(path):
        return ()
    if _is_link_like(path) or not path.is_dir():
        raise TemplateStorageIntegrityError(
            f"{description} path is not a safe directory: {path}"
        )
    try:
        return tuple(
            sorted(
                (
                    item
                    for item in path.iterdir()
                    if not item.name.startswith(".")
                ),
                key=lambda item: item.name,
            )
        )
    except OSError as error:
        raise TemplateStorageReadError(
            f"could not enumerate {description} {path}: {error}"
        ) from error


def _template_lock_bytes(template_id: str, purpose: str) -> bytes:
    return canonical_json_bytes(
        {
            "record_type": "concord_template_storage_lock",
            "schema_version": "1",
            "template_id": template_id,
            "purpose": purpose,
        }
    )


def _acquire_template_lock(
    root: Path,
    template_id: str,
    purpose: str,
) -> Path:
    lock = template_write_lock_path(root, template_id)
    _ensure_directory_chain(root, lock.parent, [])
    try:
        with lock.open("xb") as target:
            target.write(_template_lock_bytes(template_id, purpose))
            target.flush()
            os.fsync(target.fileno())
        _fsync_directory_if_supported(lock.parent)
    except FileExistsError as error:
        raise TemplateStorageConflictError(
            f"Template write lock already exists: {lock}"
        ) from error
    except OSError as error:
        raise TemplateStorageWriteError(
            f"could not durably acquire Template write lock {lock}: {error}"
        ) from error
    return lock


def _release_template_lock(lock: Path) -> OSError | None:
    try:
        lock.unlink()
        _fsync_directory_if_supported(lock.parent)
    except OSError as error:
        return error
    return None


def _publish_template_current(
    root: Path,
    path: Path,
    data: bytes,
) -> None:
    _require_safe_descendant(root, path.parent)
    temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            delete=False,
            dir=path.parent,
            prefix=".current.json.",
            suffix=".tmp",
        ) as target:
            temp = Path(target.name)
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temp, path)
        temp = None
    except OSError as error:
        raise TemplateStorageWriteError(
            f"could not atomically publish {path}: {error}"
        ) from error
    finally:
        if temp is not None:
            try:
                temp.unlink()
            except OSError:
                pass


def _fsync_directory_if_supported(path: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


__all__ = [
    "TemplateStorageConflictError",
    "TemplateStorageError",
    "TemplateStorageIntegrityError",
    "TemplateStorageNotFoundError",
    "TemplateStoragePartialSuccessError",
    "TemplateStorageReadError",
    "TemplateStorageWriteError",
    "activate_template_version",
    "calculate_rendering_specification_sha256",
    "create_successor_template_version",
    "create_template_library",
    "list_template_ids",
    "list_template_versions",
    "load_current_template",
    "load_current_template_version",
    "load_template_snapshot",
    "load_template_version",
    "retire_template",
    "retire_template_version",
    "update_template_definition",
]
