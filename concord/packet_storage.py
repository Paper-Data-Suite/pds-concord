"""Strict immutable workspace storage for reusable Concord Packets."""

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

from concord.models import PacketDefinition, PacketVersion, Provenance
from concord.packet_serialization import (
    PacketSerializationError,
    canonical_json_bytes,
    dataclass_from_dict,
    dataclass_to_dict,
    packet_from_dict,
    packet_to_dict,
    strict_json_loads,
)
from concord.packet_storage_models import (
    PACKET_LIBRARY_STORAGE_SCHEMA,
    LoadedPacketLibrary,
    PacketCurrentSnapshot,
    PacketLibraryMarker,
    PacketLibrarySnapshot,
    PacketRecordRevision,
    PacketRecordRevisionRef,
)
from concord.packet_storage_paths import (
    packet_current_path,
    packet_library_root,
    packet_marker_path,
    packet_record_revision_path,
    packet_records_root,
    packet_root,
    packet_snapshot_path,
    packet_snapshots_root,
    packet_write_lock_path,
)
from concord.template_storage import (
    TemplateStorageError,
    load_current_template,
)

T = TypeVar("T")


class PacketStorageError(RuntimeError):
    """Base reusable Packet storage failure."""


class PacketStorageReadError(PacketStorageError):
    """Canonical reusable Packet state could not be read safely."""


class PacketStorageIntegrityError(PacketStorageReadError):
    """Canonical reusable Packet state is internally inconsistent."""


class PacketStorageNotFoundError(PacketStorageReadError):
    """An explicitly requested reusable Packet does not exist."""


class PacketStorageWriteError(PacketStorageError):
    """Reusable Packet state could not be committed safely."""


class PacketStorageConflictError(PacketStorageWriteError):
    """A create-only Packet identity already exists."""


class PacketStorageDependencyError(PacketStorageWriteError):
    """A reusable Packet dependency is unavailable or incompatible."""


def list_packet_ids(workspace_root: str | Path) -> tuple[str, ...]:
    """List strictly verified Packets by display name and stable ID."""
    root = _workspace_root(workspace_root, for_write=False)
    collection = packet_library_root(root)
    _require_safe_descendant(root, collection, allow_missing=True)
    if not os.path.lexists(collection):
        return ()
    if _is_link_like(collection) or not collection.is_dir():
        raise PacketStorageIntegrityError(
            f"Packet library root is not a canonical directory: {collection}"
        )
    try:
        entries = tuple(collection.iterdir())
    except OSError as error:
        raise PacketStorageReadError(
            f"could not enumerate Packet library {collection}: {error}"
        ) from error

    loaded: list[LoadedPacketLibrary] = []
    for entry in entries:
        if entry.name.startswith("."):
            continue
        if _is_link_like(entry) or not entry.is_dir():
            raise PacketStorageIntegrityError(
                f"unexpected visible Packet library entry: {entry}"
            )
        _validate_identifier(entry.name, "packet_definition_id")
        loaded.append(load_current_packet(root, entry.name))

    loaded.sort(
        key=lambda item: (
            item.definition.name.casefold(),
            item.definition.packet_definition_id,
        )
    )
    return tuple(
        item.definition.packet_definition_id for item in loaded
    )


def load_current_packet(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> LoadedPacketLibrary:
    """Strictly load one Packet through its guarded current snapshot."""
    root = _workspace_root(workspace_root, for_write=False)
    packet_definition_id = _validate_identifier(
        packet_definition_id,
        "packet_definition_id",
    )
    _load_marker(root, packet_definition_id)
    current = _load_dataclass_file(
        root,
        packet_current_path(root, packet_definition_id),
        PacketCurrentSnapshot,
        "Packet current pointer",
        missing=True,
    )
    if current.packet_definition_id != packet_definition_id:
        raise PacketStorageIntegrityError(
            "Packet current pointer identity disagrees with its canonical path."
        )
    snapshot, digest = load_packet_snapshot(
        root,
        packet_definition_id,
        current.snapshot_revision,
    )
    if digest != current.snapshot_sha256:
        raise PacketStorageIntegrityError(
            "Packet current pointer snapshot digest mismatch."
        )
    return _materialize_snapshot(root, snapshot, digest)


def load_packet_snapshot(
    workspace_root: str | Path,
    packet_definition_id: str,
    snapshot_revision: int,
) -> tuple[PacketLibrarySnapshot, str]:
    """Load and verify one exact digest-linked historical Packet snapshot."""
    root = _workspace_root(workspace_root, for_write=False)
    packet_definition_id = _validate_identifier(
        packet_definition_id,
        "packet_definition_id",
    )
    if type(snapshot_revision) is not int or snapshot_revision < 1:
        raise PacketStorageReadError(
            "snapshot_revision must be a positive integer."
        )
    _load_marker(root, packet_definition_id)

    target: PacketLibrarySnapshot | None = None
    target_bytes: bytes | None = None
    child: PacketLibrarySnapshot | None = None

    for revision in range(snapshot_revision, 0, -1):
        path = packet_snapshot_path(
            root,
            packet_definition_id,
            revision,
        )
        snapshot, raw = _load_dataclass_file_with_bytes(
            root,
            path,
            PacketLibrarySnapshot,
            "Packet snapshot",
            missing=True,
        )
        if (
            snapshot.packet_definition_id != packet_definition_id
            or snapshot.snapshot_revision != revision
        ):
            raise PacketStorageIntegrityError(
                "Packet snapshot identity disagrees with its canonical path."
            )
        if child is not None:
            if child.previous_snapshot_revision != revision:
                raise PacketStorageIntegrityError(
                    "Packet snapshot predecessor revision mismatch."
                )
            if (
                child.previous_snapshot_sha256
                != hashlib.sha256(raw).hexdigest()
            ):
                raise PacketStorageIntegrityError(
                    "Packet snapshot predecessor digest mismatch."
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
        raise PacketStorageIntegrityError(
            "Packet snapshot history does not terminate at revision 1."
        )
    return target, hashlib.sha256(target_bytes).hexdigest()


def list_packet_versions(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> tuple[PacketVersion, ...]:
    """Return every exact Version selected by the current Packet snapshot."""
    return load_current_packet(
        workspace_root,
        packet_definition_id,
    ).versions


def load_packet_version(
    workspace_root: str | Path,
    packet_definition_id: str,
    packet_version_id: str,
) -> PacketVersion:
    """Resolve one exact Packet Version from current reusable history."""
    version_id = _validate_identifier(
        packet_version_id,
        "packet_version_id",
    )
    match = next(
        (
            item
            for item in list_packet_versions(
                workspace_root,
                packet_definition_id,
            )
            if item.packet_version_id == version_id
        ),
        None,
    )
    if match is None:
        raise PacketStorageNotFoundError(
            f"Packet Version not found: {version_id}"
        )
    return match


def load_current_packet_version(
    workspace_root: str | Path,
    packet_definition_id: str,
) -> PacketVersion | None:
    """Resolve the explicitly selected active Packet Version, if any."""
    return load_current_packet(
        workspace_root,
        packet_definition_id,
    ).current_version


def validate_packet_template_dependencies(
    workspace_root: str | Path,
    version: PacketVersion,
    *,
    for_activation: bool,
) -> None:
    """Resolve exact Template pairs and enforce reusable eligibility."""
    if not isinstance(version, PacketVersion):
        raise PacketStorageDependencyError(
            "version must be PacketVersion."
        )
    root = _workspace_root(workspace_root, for_write=False)
    for component in version.components:
        if component.component_kind != "concord_template":
            continue
        assert component.template_id is not None
        assert component.template_version_id is not None
        try:
            library = load_current_template(root, component.template_id)
        except TemplateStorageError as error:
            raise PacketStorageDependencyError(
                "could not resolve exact Template dependency "
                f"{component.template_id}:{component.template_version_id}: "
                f"{error}"
            ) from error
        if library.definition.status == "retired":
            raise PacketStorageDependencyError(
                "Packet dependency Template Definition is retired: "
                f"{component.template_id}"
            )
        template_version = next(
            (
                item
                for item in library.versions
                if item.template_version_id
                == component.template_version_id
            ),
            None,
        )
        if template_version is None:
            raise PacketStorageDependencyError(
                "Packet dependency Template Version not found: "
                f"{component.template_id}:"
                f"{component.template_version_id}"
            )
        if template_version.template_id != component.template_id:
            raise PacketStorageDependencyError(
                "Packet dependency Template Version belongs to another "
                "Template Definition."
            )
        if template_version.status == "retired":
            raise PacketStorageDependencyError(
                "Packet dependency Template Version is retired: "
                f"{component.template_version_id}"
            )
        if for_activation and template_version.status not in {
            "active",
            "superseded",
        }:
            raise PacketStorageDependencyError(
                "active Packet Version requires each Template dependency "
                "to be active or superseded; found "
                f"{template_version.status!r} for "
                f"{component.template_version_id}."
            )
        audience = component.audience_intent.audience_kind
        template_audience = (
            "participant" if audience == "role" else audience
        )
        if (
            template_audience
            not in template_version.compatibility.audience_kinds
        ):
            raise PacketStorageDependencyError(
                "Packet component audience is incompatible with exact "
                "Template Version: "
                f"{audience!r} is not supported by "
                f"{component.template_version_id}."
            )


def create_packet_library(
    workspace_root: str | Path,
    *,
    definition: PacketDefinition,
    initial_version: PacketVersion,
) -> LoadedPacketLibrary:
    """Create one Packet lineage; current.json is installed last."""
    root = _workspace_root(workspace_root, for_write=True)
    if not isinstance(definition, PacketDefinition):
        raise PacketStorageWriteError(
            "definition must be PacketDefinition."
        )
    if not isinstance(initial_version, PacketVersion):
        raise PacketStorageWriteError(
            "initial_version must be PacketVersion."
        )
    _validate_initial_pair(definition, initial_version)
    validate_packet_template_dependencies(
        root,
        initial_version,
        for_activation=initial_version.status == "active",
    )

    packet_id = definition.packet_definition_id
    collection = packet_library_root(root)
    target_root = packet_root(root, packet_id)
    _require_safe_descendant(root, collection, allow_missing=True)
    if os.path.lexists(target_root):
        raise PacketStorageConflictError(
            f"Packet identity already exists: {packet_id}"
        )

    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        _ensure_directory_chain(root, collection, created_dirs)
        try:
            target_root.mkdir()
        except FileExistsError as error:
            raise PacketStorageConflictError(
                f"Packet identity already exists: {packet_id}"
            ) from error
        created_dirs.append(target_root)
        _require_safe_descendant(root, target_root)

        marker_path = packet_marker_path(root, packet_id)
        definition_path = packet_record_revision_path(
            root,
            packet_id,
            "packet_definition",
            definition.packet_definition_id,
            1,
        )
        version_path = packet_record_revision_path(
            root,
            packet_id,
            "packet_version",
            initial_version.packet_version_id,
            1,
        )
        snapshot_path = packet_snapshot_path(root, packet_id, 1)
        current_path = packet_current_path(root, packet_id)

        for parent in (
            marker_path.parent,
            definition_path.parent,
            version_path.parent,
            snapshot_path.parent,
        ):
            _ensure_directory_chain(root, parent, created_dirs)

        marker = PacketLibraryMarker(
            storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
            packet_definition_id=packet_id,
            created_provenance=definition.created_provenance,
        )
        marker_bytes = canonical_json_bytes(dataclass_to_dict(marker))

        definition_revision = PacketRecordRevision(
            storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
            packet_definition_id=packet_id,
            record_kind="packet_definition",
            record_id=definition.packet_definition_id,
            record_revision=1,
            operation="create",
            operation_provenance=definition.created_provenance,
            body=packet_to_dict(definition),
        )
        definition_bytes = canonical_json_bytes(
            dataclass_to_dict(definition_revision)
        )
        version_revision = PacketRecordRevision(
            storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
            packet_definition_id=packet_id,
            record_kind="packet_version",
            record_id=initial_version.packet_version_id,
            record_revision=1,
            operation="create",
            operation_provenance=initial_version.created_provenance,
            body=packet_to_dict(initial_version),
        )
        version_bytes = canonical_json_bytes(
            dataclass_to_dict(version_revision)
        )

        refs = tuple(
            sorted(
                (
                    PacketRecordRevisionRef(
                        record_kind="packet_definition",
                        record_id=definition.packet_definition_id,
                        record_revision=1,
                        sha256=hashlib.sha256(
                            definition_bytes
                        ).hexdigest(),
                    ),
                    PacketRecordRevisionRef(
                        record_kind="packet_version",
                        record_id=initial_version.packet_version_id,
                        record_revision=1,
                        sha256=hashlib.sha256(
                            version_bytes
                        ).hexdigest(),
                    ),
                ),
                key=lambda item: (item.record_kind, item.record_id),
            )
        )
        current_version_id = (
            initial_version.packet_version_id
            if initial_version.status == "active"
            else None
        )
        snapshot = PacketLibrarySnapshot(
            storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
            packet_definition_id=packet_id,
            snapshot_revision=1,
            records=refs,
            current_packet_version_id=current_version_id,
            head_packet_version_id=initial_version.packet_version_id,
            previous_snapshot_revision=None,
            previous_snapshot_sha256=None,
            operation="create",
            operation_provenance=definition.created_provenance,
        )
        snapshot_bytes = canonical_json_bytes(dataclass_to_dict(snapshot))
        current = PacketCurrentSnapshot(
            storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
            packet_definition_id=packet_id,
            snapshot_revision=1,
            snapshot_sha256=hashlib.sha256(snapshot_bytes).hexdigest(),
        )
        current_bytes = canonical_json_bytes(dataclass_to_dict(current))

        for path, data in (
            (marker_path, marker_bytes),
            (definition_path, definition_bytes),
            (version_path, version_bytes),
            (snapshot_path, snapshot_bytes),
        ):
            _write_exclusive(root, path, data)
            created_files.append(path)

        _load_marker(root, packet_id)
        _load_record_revision(
            root,
            packet_id,
            "packet_definition",
            definition.packet_definition_id,
            1,
        )
        _load_record_revision(
            root,
            packet_id,
            "packet_version",
            initial_version.packet_version_id,
            1,
        )
        loaded_snapshot, loaded_digest = load_packet_snapshot(
            root,
            packet_id,
            1,
        )
        if (
            loaded_snapshot != snapshot
            or loaded_digest != current.snapshot_sha256
        ):
            raise PacketStorageWriteError(
                "new Packet snapshot did not verify before commit."
            )

        _write_exclusive(root, current_path, current_bytes)
        created_files.append(current_path)
        loaded = load_current_packet(root, packet_id)
        if (
            loaded.definition != definition
            or loaded.versions != (initial_version,)
            or loaded.snapshot_revision != 1
        ):
            raise PacketStorageWriteError(
                "persisted Packet differs from requested initial state."
            )
        return loaded
    except PacketStorageError:
        _rollback_created(created_files, created_dirs)
        raise
    except (OSError, ValueError, PacketSerializationError) as error:
        _rollback_created(created_files, created_dirs)
        raise PacketStorageWriteError(
            f"Packet creation did not commit: {error}"
        ) from error


def _materialize_snapshot(
    root: Path,
    snapshot: PacketLibrarySnapshot,
    snapshot_digest: str,
) -> LoadedPacketLibrary:
    selected: list[PacketDefinition | PacketVersion] = []
    for ref in snapshot.records:
        record, raw = _load_record_revision(
            root,
            snapshot.packet_definition_id,
            ref.record_kind,
            ref.record_id,
            ref.record_revision,
        )
        if hashlib.sha256(raw).hexdigest() != ref.sha256:
            raise PacketStorageIntegrityError(
                f"record digest mismatch for "
                f"{ref.record_kind}:{ref.record_id}."
            )
        selected.append(record)

    definitions = [
        item for item in selected if isinstance(item, PacketDefinition)
    ]
    versions = [
        item for item in selected if isinstance(item, PacketVersion)
    ]
    if len(definitions) != 1:
        raise PacketStorageIntegrityError(
            "Packet snapshot must select exactly one PacketDefinition."
        )
    definition = definitions[0]
    if definition.packet_definition_id != snapshot.packet_definition_id:
        raise PacketStorageIntegrityError(
            "Packet Definition identity disagrees with snapshot."
        )
    if not versions:
        raise PacketStorageIntegrityError(
            "Packet snapshot must select at least one PacketVersion."
        )
    versions.sort(key=lambda item: item.revision_sequence)
    ordered_versions = tuple(versions)
    _validate_lineage(definition, ordered_versions, snapshot)

    return LoadedPacketLibrary(
        definition=definition,
        versions=ordered_versions,
        snapshot_revision=snapshot.snapshot_revision,
        snapshot_sha256=snapshot_digest,
        current_packet_version_id=snapshot.current_packet_version_id,
        head_packet_version_id=snapshot.head_packet_version_id,
    )


def _validate_lineage(
    definition: PacketDefinition,
    versions: tuple[PacketVersion, ...],
    snapshot: PacketLibrarySnapshot,
) -> None:
    expected_sequences = tuple(range(1, len(versions) + 1))
    actual_sequences = tuple(item.revision_sequence for item in versions)
    if actual_sequences != expected_sequences:
        raise PacketStorageIntegrityError(
            "Packet Version revision_sequence must form contiguous 1..N history."
        )
    ids = tuple(item.packet_version_id for item in versions)
    if len(set(ids)) != len(ids):
        raise PacketStorageIntegrityError(
            "Packet Version identities must be unique within one lineage."
        )
    for index, version in enumerate(versions):
        if (
            version.packet_definition_id
            != definition.packet_definition_id
        ):
            raise PacketStorageIntegrityError(
                "Packet Version belongs to another Packet Definition."
            )
        expected_predecessor = (
            None
            if index == 0
            else versions[index - 1].packet_version_id
        )
        if version.supersedes_packet_version_id != expected_predecessor:
            raise PacketStorageIntegrityError(
                "Packet Version predecessor chain is not linear and exact."
            )

    if snapshot.head_packet_version_id != versions[-1].packet_version_id:
        raise PacketStorageIntegrityError(
            "head_packet_version_id does not identify the lineage head."
        )

    active = tuple(item for item in versions if item.status == "active")
    if snapshot.current_packet_version_id is None:
        if active:
            raise PacketStorageIntegrityError(
                "Packet snapshot has active Version(s) but no current selection."
            )
    else:
        if len(active) != 1:
            raise PacketStorageIntegrityError(
                "Packet snapshot must have exactly one active current Version."
            )
        if active[0].packet_version_id != snapshot.current_packet_version_id:
            raise PacketStorageIntegrityError(
                "current_packet_version_id does not identify active Version."
            )

    if (
        definition.status == "draft"
        and snapshot.current_packet_version_id is not None
    ):
        raise PacketStorageIntegrityError(
            "draft Packet Definition must not have a current active Version."
        )
    if (
        definition.status == "active"
        and snapshot.current_packet_version_id is None
    ):
        raise PacketStorageIntegrityError(
            "active Packet Definition requires a current active Version."
        )
    if (
        definition.status == "retired"
        and snapshot.current_packet_version_id is not None
    ):
        raise PacketStorageIntegrityError(
            "retired Packet Definition must not have a current Version."
        )


def _validate_initial_pair(
    definition: PacketDefinition,
    version: PacketVersion,
) -> None:
    if (
        definition.packet_definition_id
        != version.packet_definition_id
    ):
        raise PacketStorageWriteError(
            "initial Packet Definition and Version must share "
            "packet_definition_id."
        )
    if (
        version.revision_sequence != 1
        or version.supersedes_packet_version_id is not None
    ):
        raise PacketStorageWriteError(
            "initial Packet Version must be revision 1 with no predecessor."
        )
    if (definition.status, version.status) not in {
        ("draft", "draft"),
        ("active", "active"),
    }:
        raise PacketStorageWriteError(
            "initial Packet status must be draft/draft or active/active."
        )


def _load_marker(
    root: Path,
    packet_definition_id: str,
) -> PacketLibraryMarker:
    marker = _load_dataclass_file(
        root,
        packet_marker_path(root, packet_definition_id),
        PacketLibraryMarker,
        "Packet library marker",
        missing=True,
    )
    if marker.packet_definition_id != packet_definition_id:
        raise PacketStorageIntegrityError(
            "Packet marker identity disagrees with its canonical path."
        )
    return marker


def _load_record_revision(
    root: Path,
    packet_definition_id: str,
    record_kind: str,
    record_id: str,
    revision: int,
) -> tuple[PacketDefinition | PacketVersion, bytes]:
    path = packet_record_revision_path(
        root,
        packet_definition_id,
        record_kind,
        record_id,
        revision,
    )
    envelope, raw = _load_dataclass_file_with_bytes(
        root,
        path,
        PacketRecordRevision,
        "Packet record revision",
        missing=True,
    )
    if (
        envelope.packet_definition_id != packet_definition_id
        or envelope.record_kind != record_kind
        or envelope.record_id != record_id
        or envelope.record_revision != revision
    ):
        raise PacketStorageIntegrityError(
            "Packet record envelope identity disagrees with canonical path."
        )
    try:
        record = packet_from_dict(record_kind, envelope.body)
    except PacketSerializationError as error:
        raise PacketStorageIntegrityError(
            f"invalid reusable Packet record body: {error}"
        ) from error
    expected_id = (
        record.packet_definition_id
        if isinstance(record, PacketDefinition)
        else record.packet_version_id
    )
    if expected_id != record_id:
        raise PacketStorageIntegrityError(
            "Packet record body identity disagrees with its envelope."
        )
    if (
        record.packet_definition_id != packet_definition_id
        or packet_to_dict(record) != envelope.body
    ):
        raise PacketStorageIntegrityError(
            "Packet record body disagrees with canonical typed round trip."
        )
    return record, raw


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
    except (PacketSerializationError, ValueError) as error:
        raise PacketStorageIntegrityError(
            f"invalid canonical {description} at {path}: {error}"
        ) from error
    if canonical != data:
        raise PacketStorageIntegrityError(
            f"{description} is not canonical at {path}."
        )
    return model, data


def _workspace_root(
    workspace_root: str | Path,
    *,
    for_write: bool,
) -> Path:
    try:
        root = resolve_workspace_root(workspace_root)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        raise PacketStorageError(
            f"invalid workspace root {workspace_root!r}: {error}"
        ) from error
    if not os.path.lexists(root):
        raise PacketStorageError(f"workspace root does not exist: {root}")
    if _is_link_like(root) or not root.is_dir():
        raise PacketStorageError(
            f"workspace root must be an ordinary non-link directory: {root}"
        )
    if for_write and not os.access(root, os.W_OK):
        raise PacketStorageWriteError(
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
            raise PacketStorageNotFoundError(
                f"{description} not found: {path}"
            )
        raise PacketStorageIntegrityError(
            f"{description} is missing: {path}"
        )
    if _is_link_like(path) or not path.is_file():
        raise PacketStorageIntegrityError(
            f"{description} must be an ordinary non-link file: {path}"
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise PacketStorageReadError(
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
        raise PacketStorageIntegrityError(
            f"Packet path escapes workspace root: {path}"
        ) from error

    if _is_link_like(root) or not root.is_dir():
        raise PacketStorageIntegrityError(
            f"workspace root is not a safe directory: {root}"
        )
    current = root
    for index, part in enumerate(relative.parts):
        current = current / part
        leaf = index == len(relative.parts) - 1
        if not os.path.lexists(current):
            if allow_missing:
                return
            raise PacketStorageIntegrityError(
                f"canonical Packet path component is missing: {current}"
            )
        if _is_link_like(current):
            raise PacketStorageIntegrityError(
                "canonical Packet path traverses a link-like object: "
                f"{current}"
            )
        if not leaf and not current.is_dir():
            raise PacketStorageIntegrityError(
                "canonical Packet path ancestor is not a directory: "
                f"{current}"
            )


def _is_link_like(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as error:
        raise PacketStorageIntegrityError(
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
        raise PacketStorageWriteError(
            f"Packet directory escapes workspace root: {target}"
        ) from error

    current = root
    for part in relative.parts:
        current = current / part
        if os.path.lexists(current):
            if _is_link_like(current) or not current.is_dir():
                raise PacketStorageIntegrityError(
                    f"Packet directory path is unsafe: {current}"
                )
            continue
        try:
            current.mkdir()
        except FileExistsError:
            if _is_link_like(current) or not current.is_dir():
                raise PacketStorageIntegrityError(
                    f"Packet directory raced to unsafe object: {current}"
                )
        except OSError as error:
            raise PacketStorageWriteError(
                f"could not create Packet directory {current}: {error}"
            ) from error
        else:
            created.append(current)
        if _is_link_like(current) or not current.is_dir():
            raise PacketStorageIntegrityError(
                f"created Packet directory is unsafe: {current}"
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
        raise PacketStorageConflictError(
            f"immutable canonical file already exists: {path}"
        ) from error
    except OSError as error:
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise PacketStorageWriteError(
            f"could not create immutable canonical file {path}: {error}"
        ) from error


def _rollback_created(
    files: list[Path],
    directories: list[Path],
) -> None:
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
        raise PacketStorageReadError(str(error)) from error


class PacketStoragePartialSuccessError(PacketStorageWriteError):
    """A Packet mutation published durable state but could not finish cleanly."""

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


def create_successor_packet_version(
    workspace_root: str | Path,
    packet_definition_id: str,
    *,
    successor: PacketVersion,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedPacketLibrary:
    """Append one exact draft successor without changing current selection."""

    def plan(
        loaded: LoadedPacketLibrary,
    ) -> tuple[
        tuple[PacketDefinition | PacketVersion, ...],
        str | None,
        str,
        bool,
    ]:
        head = loaded.head_version
        if loaded.definition.status == "retired":
            raise PacketStorageWriteError(
                "retired Packet Definitions cannot receive successors."
            )
        if (
            successor.packet_definition_id
            != loaded.definition.packet_definition_id
        ):
            raise PacketStorageWriteError(
                "successor packet_definition_id must match "
                "the Packet Definition."
            )
        if successor.status != "draft":
            raise PacketStorageWriteError(
                "new Packet successors must begin in draft status."
            )
        if successor.packet_version_id in {
            item.packet_version_id for item in loaded.versions
        }:
            raise PacketStorageConflictError(
                "successor packet_version_id already exists."
            )
        if successor.revision_sequence != head.revision_sequence + 1:
            raise PacketStorageWriteError(
                "successor revision_sequence must be exactly head + 1."
            )
        if (
            successor.supersedes_packet_version_id
            != head.packet_version_id
        ):
            raise PacketStorageWriteError(
                "successor must supersede the exact current lineage head."
            )
        validate_packet_template_dependencies(
            workspace_root,
            successor,
            for_activation=False,
        )
        return (
            (successor,),
            loaded.current_packet_version_id,
            successor.packet_version_id,
            False,
        )

    return _commit_packet_mutation(
        workspace_root,
        packet_definition_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="revise",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def activate_packet_version(
    workspace_root: str | Path,
    packet_definition_id: str,
    packet_version_id: str,
    *,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedPacketLibrary:
    """Activate the draft lineage head and supersede previous current Version."""
    target_id = _validate_identifier(
        packet_version_id,
        "packet_version_id",
    )

    def plan(
        loaded: LoadedPacketLibrary,
    ) -> tuple[
        tuple[PacketDefinition | PacketVersion, ...],
        str | None,
        str,
        bool,
    ]:
        if loaded.definition.status == "retired":
            raise PacketStorageWriteError(
                "retired Packet Definitions cannot be activated."
            )
        candidate = next(
            (
                item
                for item in loaded.versions
                if item.packet_version_id == target_id
            ),
            None,
        )
        if candidate is None:
            raise PacketStorageNotFoundError(
                f"Packet Version not found: {target_id}"
            )
        if candidate.packet_version_id != loaded.head_packet_version_id:
            raise PacketStorageConflictError(
                "only the exact current lineage head can be activated."
            )
        if candidate.status != "draft":
            raise PacketStorageConflictError(
                "Packet Version activation requires a draft head."
            )

        validate_packet_template_dependencies(
            workspace_root,
            candidate,
            for_activation=True,
        )

        changes: list[PacketDefinition | PacketVersion] = [
            replace(candidate, status="active")
        ]
        if loaded.current_version is not None:
            if loaded.current_version.status != "active":
                raise PacketStorageIntegrityError(
                    "current Packet Version is not active."
                )
            changes.append(
                replace(loaded.current_version, status="superseded")
            )
        if loaded.definition.status == "draft":
            changes.append(replace(loaded.definition, status="active"))
        elif loaded.definition.status != "active":
            raise PacketStorageIntegrityError(
                "Packet Definition lifecycle is incompatible with activation."
            )
        return (
            tuple(changes),
            candidate.packet_version_id,
            loaded.head_packet_version_id,
            False,
        )

    return _commit_packet_mutation(
        workspace_root,
        packet_definition_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="activate",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def update_packet_definition(
    workspace_root: str | Path,
    packet_definition_id: str,
    *,
    definition: PacketDefinition,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedPacketLibrary:
    """Persist an immutable metadata revision of one Packet Definition."""

    def plan(
        loaded: LoadedPacketLibrary,
    ) -> tuple[
        tuple[PacketDefinition | PacketVersion, ...],
        str | None,
        str,
        bool,
    ]:
        current = loaded.definition
        if current.status == "retired":
            raise PacketStorageWriteError(
                "retired Packet Definitions cannot be updated."
            )
        immutable_same = (
            definition.packet_definition_id
            == current.packet_definition_id
            and definition.created_provenance == current.created_provenance
            and definition.status == current.status
        )
        if not immutable_same:
            raise PacketStorageWriteError(
                "Packet Definition update may change only name, purpose, "
                "and description."
            )
        if definition == current:
            return (
                (),
                loaded.current_packet_version_id,
                loaded.head_packet_version_id,
                True,
            )
        return (
            (definition,),
            loaded.current_packet_version_id,
            loaded.head_packet_version_id,
            False,
        )

    return _commit_packet_mutation(
        workspace_root,
        packet_definition_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="update",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def retire_packet_version(
    workspace_root: str | Path,
    packet_definition_id: str,
    packet_version_id: str,
    *,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedPacketLibrary:
    """Retire one non-current draft Packet Version without deleting history."""
    target_id = _validate_identifier(
        packet_version_id,
        "packet_version_id",
    )

    def plan(
        loaded: LoadedPacketLibrary,
    ) -> tuple[
        tuple[PacketDefinition | PacketVersion, ...],
        str | None,
        str,
        bool,
    ]:
        if loaded.definition.status == "retired":
            raise PacketStorageWriteError(
                "the whole Packet Definition is already retired."
            )
        candidate = next(
            (
                item
                for item in loaded.versions
                if item.packet_version_id == target_id
            ),
            None,
        )
        if candidate is None:
            raise PacketStorageNotFoundError(
                f"Packet Version not found: {target_id}"
            )
        if candidate.packet_version_id == loaded.current_packet_version_id:
            raise PacketStorageConflictError(
                "the active current Packet Version cannot be retired "
                "independently."
            )
        if candidate.status != "draft":
            raise PacketStorageConflictError(
                "only a non-current draft Packet Version can be retired."
            )
        return (
            (replace(candidate, status="retired"),),
            loaded.current_packet_version_id,
            loaded.head_packet_version_id,
            False,
        )

    return _commit_packet_mutation(
        workspace_root,
        packet_definition_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="retire-version",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def retire_packet(
    workspace_root: str | Path,
    packet_definition_id: str,
    *,
    expected_snapshot_revision: int,
    operation_provenance: Provenance,
) -> LoadedPacketLibrary:
    """Retire one Packet Definition and clear its current selection."""

    def plan(
        loaded: LoadedPacketLibrary,
    ) -> tuple[
        tuple[PacketDefinition | PacketVersion, ...],
        str | None,
        str,
        bool,
    ]:
        if loaded.definition.status == "retired":
            return (
                (),
                None,
                loaded.head_packet_version_id,
                True,
            )
        changes: list[PacketDefinition | PacketVersion] = [
            replace(loaded.definition, status="retired")
        ]
        if loaded.current_version is not None:
            if loaded.current_version.status != "active":
                raise PacketStorageIntegrityError(
                    "current Packet Version is not active."
                )
            changes.append(
                replace(loaded.current_version, status="retired")
            )
        return (
            tuple(changes),
            None,
            loaded.head_packet_version_id,
            False,
        )

    return _commit_packet_mutation(
        workspace_root,
        packet_definition_id,
        expected_snapshot_revision=expected_snapshot_revision,
        operation="retire",
        operation_provenance=operation_provenance,
        planner=plan,
    )


def _commit_packet_mutation(
    workspace_root: str | Path,
    packet_definition_id: str,
    *,
    expected_snapshot_revision: int,
    operation: str,
    operation_provenance: Provenance,
    planner: Callable[
        [LoadedPacketLibrary],
        tuple[
            tuple[PacketDefinition | PacketVersion, ...],
            str | None,
            str,
            bool,
        ],
    ],
) -> LoadedPacketLibrary:
    if (
        type(expected_snapshot_revision) is not int
        or expected_snapshot_revision < 1
    ):
        raise PacketStorageWriteError(
            "expected_snapshot_revision must be a positive integer."
        )
    if not isinstance(operation_provenance, Provenance):
        raise PacketStorageWriteError(
            "operation_provenance must be Provenance."
        )
    operation = _validate_identifier(operation, "operation")
    root = _workspace_root(workspace_root, for_write=True)
    packet_definition_id = _validate_identifier(
        packet_definition_id,
        "packet_definition_id",
    )
    _load_marker(root, packet_definition_id)
    lock = _acquire_packet_lock(root, packet_definition_id, operation)
    pointer_published = False
    published_revision: int | None = None
    published_digest: str | None = None
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    operation_error: Exception | None = None
    result: LoadedPacketLibrary | None = None

    try:
        loaded = load_current_packet(root, packet_definition_id)
        if loaded.snapshot_revision != expected_snapshot_revision:
            raise PacketStorageConflictError(
                f"expected Packet snapshot {expected_snapshot_revision}, "
                f"found {loaded.snapshot_revision}."
            )
        current_snapshot, current_digest = load_packet_snapshot(
            root,
            packet_definition_id,
            loaded.snapshot_revision,
        )
        _validate_packet_write_history(
            root,
            packet_definition_id,
            current_snapshot,
        )

        changes, next_current, next_head, no_op = planner(loaded)
        if no_op:
            result = loaded
        else:
            selected = {
                (item.record_kind, item.record_id): item
                for item in current_snapshot.records
            }
            next_refs: dict[
                tuple[str, str],
                PacketRecordRevisionRef,
            ] = dict(selected)

            for record in changes:
                if isinstance(record, PacketDefinition):
                    kind = "packet_definition"
                    record_id = record.packet_definition_id
                else:
                    kind = "packet_version"
                    record_id = record.packet_version_id
                identity = (kind, record_id)
                old_ref = selected.get(identity)
                if old_ref is None:
                    next_record_revision = 1
                else:
                    old_record, _ = _load_record_revision(
                        root,
                        packet_definition_id,
                        kind,
                        record_id,
                        old_ref.record_revision,
                    )
                    if packet_to_dict(old_record) == packet_to_dict(record):
                        continue
                    next_record_revision = old_ref.record_revision + 1
                path = packet_record_revision_path(
                    root,
                    packet_definition_id,
                    kind,
                    record_id,
                    next_record_revision,
                )
                if os.path.lexists(path):
                    raise PacketStorageIntegrityError(
                        "orphan/colliding Packet record revision blocks "
                        f"commit: {kind}:{record_id}:"
                        f"{next_record_revision}"
                    )
                _ensure_directory_chain(root, path.parent, created_dirs)
                envelope = PacketRecordRevision(
                    storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
                    packet_definition_id=packet_definition_id,
                    record_kind=kind,
                    record_id=record_id,
                    record_revision=next_record_revision,
                    operation=operation,
                    operation_provenance=operation_provenance,
                    body=packet_to_dict(record),
                )
                data = canonical_json_bytes(dataclass_to_dict(envelope))
                _write_exclusive(root, path, data)
                created_files.append(path)
                persisted, persisted_bytes = _load_record_revision(
                    root,
                    packet_definition_id,
                    kind,
                    record_id,
                    next_record_revision,
                )
                if persisted != record or persisted_bytes != data:
                    raise PacketStorageIntegrityError(
                        "new Packet record revision failed exact verification."
                    )
                next_refs[identity] = PacketRecordRevisionRef(
                    record_kind=kind,
                    record_id=record_id,
                    record_revision=next_record_revision,
                    sha256=hashlib.sha256(data).hexdigest(),
                )

            next_revision = loaded.snapshot_revision + 1
            next_snapshot_path = packet_snapshot_path(
                root,
                packet_definition_id,
                next_revision,
            )
            if os.path.lexists(next_snapshot_path):
                raise PacketStorageIntegrityError(
                    "orphan/colliding Packet snapshot blocks commit."
                )
            snapshot = PacketLibrarySnapshot(
                storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
                packet_definition_id=packet_definition_id,
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
                current_packet_version_id=next_current,
                head_packet_version_id=next_head,
                previous_snapshot_revision=loaded.snapshot_revision,
                previous_snapshot_sha256=current_digest,
                operation=operation,
                operation_provenance=operation_provenance,
            )
            snapshot_data = canonical_json_bytes(dataclass_to_dict(snapshot))
            _write_exclusive(root, next_snapshot_path, snapshot_data)
            created_files.append(next_snapshot_path)
            verified_snapshot, verified_digest = load_packet_snapshot(
                root,
                packet_definition_id,
                next_revision,
            )
            if verified_snapshot != snapshot:
                raise PacketStorageIntegrityError(
                    "new Packet snapshot failed exact verification."
                )
            _materialize_snapshot(
                root,
                verified_snapshot,
                verified_digest,
            )

            pointer = PacketCurrentSnapshot(
                storage_schema_version=PACKET_LIBRARY_STORAGE_SCHEMA,
                packet_definition_id=packet_definition_id,
                snapshot_revision=next_revision,
                snapshot_sha256=verified_digest,
            )
            current_path = packet_current_path(
                root,
                packet_definition_id,
            )
            _publish_packet_current(
                root,
                current_path,
                canonical_json_bytes(dataclass_to_dict(pointer)),
            )
            pointer_published = True
            published_revision = next_revision
            published_digest = verified_digest
            _fsync_directory_if_supported(current_path.parent)
            result = load_current_packet(root, packet_definition_id)
    except Exception as error:
        operation_error = error
        if not pointer_published:
            _rollback_created(created_files, created_dirs)
    finally:
        cleanup_error = _release_packet_lock(lock)

    if operation_error is not None:
        if pointer_published:
            raise PacketStoragePartialSuccessError(
                "Packet current state was published, but final verification "
                "did not complete cleanly.",
                pointer_published=True,
                snapshot_revision=published_revision,
                snapshot_sha256=published_digest,
            ) from operation_error
        raise operation_error
    if cleanup_error is not None:
        raise PacketStoragePartialSuccessError(
            "Packet mutation succeeded, but write.lock could not be removed.",
            pointer_published=pointer_published,
            snapshot_revision=published_revision,
            snapshot_sha256=published_digest,
        ) from cleanup_error
    if result is None:
        raise PacketStorageWriteError(
            "Packet mutation produced no result."
        )
    return result


def _validate_packet_write_history(
    root: Path,
    packet_definition_id: str,
    current_snapshot: PacketLibrarySnapshot,
) -> None:
    snapshots = _visible_entries(
        root,
        packet_snapshots_root(root, packet_definition_id),
        "Packet snapshots",
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
            raise PacketStorageIntegrityError(
                f"unexpected Packet snapshot entry: {path}"
            )
        revisions.append(int(path.stem))
    if tuple(sorted(revisions)) != tuple(
        range(1, current_snapshot.snapshot_revision + 1)
    ):
        raise PacketStorageIntegrityError(
            "Packet snapshot history is noncontiguous or contains orphans."
        )

    selected = {
        (item.record_kind, item.record_id): item
        for item in current_snapshot.records
    }
    records_root = packet_records_root(root, packet_definition_id)
    discovered: set[tuple[str, str]] = set()
    for kind_path in _visible_entries(
        root,
        records_root,
        "Packet record kinds",
    ):
        if (
            kind_path.name not in {"packet_definition", "packet_version"}
            or _is_link_like(kind_path)
            or not kind_path.is_dir()
        ):
            raise PacketStorageIntegrityError(
                f"unexpected Packet record kind entry: {kind_path}"
            )
        for identity_path in _visible_entries(
            root,
            kind_path,
            "Packet record identities",
        ):
            if _is_link_like(identity_path) or not identity_path.is_dir():
                raise PacketStorageIntegrityError(
                    f"unexpected Packet record identity entry: {identity_path}"
                )
            _validate_identifier(identity_path.name, "record_id")
            identity = (kind_path.name, identity_path.name)
            discovered.add(identity)
            ref = selected.get(identity)
            if ref is None:
                raise PacketStorageIntegrityError(
                    "orphan Packet record identity blocks mutation: "
                    f"{identity[0]}:{identity[1]}"
                )
            revisions_root = identity_path / "revisions"
            revision_entries = _visible_entries(
                root,
                revisions_root,
                "Packet record revisions",
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
                    raise PacketStorageIntegrityError(
                        "unexpected Packet record revision entry: "
                        f"{revision_path}"
                    )
                record_revisions.append(int(revision_path.stem))
            if tuple(sorted(record_revisions)) != tuple(
                range(1, ref.record_revision + 1)
            ):
                raise PacketStorageIntegrityError(
                    "Packet record history is noncontiguous or contains "
                    f"orphans for {identity[0]}:{identity[1]}."
                )
    if discovered != set(selected):
        raise PacketStorageIntegrityError(
            "Packet record identities disagree with current snapshot."
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
        raise PacketStorageIntegrityError(
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
        raise PacketStorageReadError(
            f"could not enumerate {description} {path}: {error}"
        ) from error


def _packet_lock_bytes(
    packet_definition_id: str,
    purpose: str,
) -> bytes:
    return canonical_json_bytes(
        {
            "record_type": "concord_packet_storage_lock",
            "schema_version": "1",
            "packet_definition_id": packet_definition_id,
            "purpose": purpose,
        }
    )


def _acquire_packet_lock(
    root: Path,
    packet_definition_id: str,
    purpose: str,
) -> Path:
    lock = packet_write_lock_path(root, packet_definition_id)
    _ensure_directory_chain(root, lock.parent, [])
    try:
        with lock.open("xb") as target:
            target.write(
                _packet_lock_bytes(packet_definition_id, purpose)
            )
            target.flush()
            os.fsync(target.fileno())
        _fsync_directory_if_supported(lock.parent)
    except FileExistsError as error:
        raise PacketStorageConflictError(
            f"Packet write lock already exists: {lock}"
        ) from error
    except OSError as error:
        raise PacketStorageWriteError(
            f"could not durably acquire Packet write lock {lock}: {error}"
        ) from error
    return lock


def _release_packet_lock(lock: Path) -> OSError | None:
    try:
        lock.unlink()
        _fsync_directory_if_supported(lock.parent)
    except OSError as error:
        return error
    return None


def _publish_packet_current(
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
        raise PacketStorageWriteError(
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
    "PacketStorageConflictError",
    "PacketStorageDependencyError",
    "PacketStorageError",
    "PacketStorageIntegrityError",
    "PacketStorageNotFoundError",
    "PacketStoragePartialSuccessError",
    "PacketStorageReadError",
    "PacketStorageWriteError",
    "activate_packet_version",
    "create_packet_library",
    "create_successor_packet_version",
    "list_packet_ids",
    "list_packet_versions",
    "load_current_packet",
    "load_current_packet_version",
    "load_packet_snapshot",
    "load_packet_version",
    "retire_packet",
    "retire_packet_version",
    "update_packet_definition",
    "validate_packet_template_dependencies",
]
