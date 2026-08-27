"""Protected immutable workspace storage for reusable Concord presets."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, cast

from pds_core.identifiers import validate_identifier
from pds_core.workspace import resolve_workspace_root

from concord.models import ActorReference, Provenance, ScoringScaleLevel
from concord.reusable_presets import (
    PRESET_KINDS,
    PRESET_SCHEMA_VERSION,
    CriterionPresetSpec,
    CriterionSetPresetRevision,
    PresetRevision,
    ResponsibilityPresetRevision,
    RolePresetRevision,
    ScoringScalePresetRevision,
    preset_kind,
)

_STORAGE_SCHEMA: Final[str] = "concord_reusable_preset_library_v1"


class ReusablePresetStorageError(RuntimeError):
    """Base reusable preset storage failure."""


class ReusablePresetStorageReadError(ReusablePresetStorageError):
    """Canonical reusable preset data could not be read."""


class ReusablePresetStorageIntegrityError(ReusablePresetStorageReadError):
    """Canonical reusable preset data is internally inconsistent."""


class ReusablePresetStorageNotFoundError(ReusablePresetStorageReadError):
    """The requested reusable preset does not exist."""


class ReusablePresetStorageWriteError(ReusablePresetStorageError):
    """Reusable preset state could not be committed safely."""


class ReusablePresetStorageConflictError(ReusablePresetStorageWriteError):
    """A create-only preset identity or revision already exists."""


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedReusablePreset:
    preset_kind: str
    preset_id: str
    current: PresetRevision
    current_sha256: str

    @property
    def revision(self) -> int:
        return self.current.revision


@dataclass(frozen=True, slots=True, kw_only=True)
class _Marker:
    storage_schema_version: str
    preset_kind: str
    preset_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class _Current:
    storage_schema_version: str
    preset_kind: str
    preset_id: str
    revision: int
    preset_revision_id: str
    revision_sha256: str


def preset_library_root(workspace_root: str | Path) -> Path:
    return (
        resolve_workspace_root(workspace_root)
        / "shared"
        / "concord"
        / "reusable-presets"
    )


def preset_kind_root(workspace_root: str | Path, kind: str) -> Path:
    return preset_library_root(workspace_root) / _kind(kind)


def preset_root(workspace_root: str | Path, kind: str, preset_id: str) -> Path:
    return preset_kind_root(workspace_root, kind) / _id(preset_id, "preset_id")


def preset_marker_path(workspace_root: str | Path, kind: str, preset_id: str) -> Path:
    return preset_root(workspace_root, kind, preset_id) / "library.json"


def preset_revisions_root(
    workspace_root: str | Path,
    kind: str,
    preset_id: str,
) -> Path:
    return preset_root(workspace_root, kind, preset_id) / "revisions"


def preset_revision_path(
    workspace_root: str | Path,
    kind: str,
    preset_id: str,
    revision: int,
) -> Path:
    return (
        preset_revisions_root(workspace_root, kind, preset_id)
        / f"{_positive(revision)}.json"
    )


def preset_current_path(workspace_root: str | Path, kind: str, preset_id: str) -> Path:
    return preset_root(workspace_root, kind, preset_id) / "current.json"


def list_preset_ids(workspace_root: str | Path, kind: str) -> tuple[str, ...]:
    root = resolve_workspace_root(workspace_root)
    collection = preset_kind_root(root, kind)
    _safe_descendant(root, collection, allow_missing=True)
    if not os.path.lexists(collection):
        return ()
    if _is_link_like(collection) or not collection.is_dir():
        raise ReusablePresetStorageIntegrityError(
            f"preset collection is not a canonical directory: {collection}"
        )
    loaded: list[LoadedReusablePreset] = []
    try:
        entries = tuple(collection.iterdir())
    except OSError as error:
        raise ReusablePresetStorageReadError(
            f"could not enumerate preset collection: {error}"
        ) from error
    for entry in entries:
        if entry.name.startswith("."):
            continue
        if _is_link_like(entry) or not entry.is_dir():
            raise ReusablePresetStorageIntegrityError(
                f"unexpected preset collection entry: {entry}"
            )
        loaded.append(load_current_preset(root, kind, entry.name))
    loaded.sort(key=lambda item: (item.current.name.casefold(), item.preset_id))
    return tuple(item.preset_id for item in loaded)


def load_current_preset(
    workspace_root: str | Path,
    kind: str,
    preset_id: str,
) -> LoadedReusablePreset:
    root = resolve_workspace_root(workspace_root)
    kind = _kind(kind)
    preset_id = _id(preset_id, "preset_id")
    marker = _load_marker(root, kind, preset_id)
    current_data = _read_json(
        root,
        preset_current_path(root, kind, preset_id),
        missing=True,
    )
    current = _current_from_dict(current_data)
    if (
        current.preset_kind != marker.preset_kind
        or current.preset_id != marker.preset_id
    ):
        raise ReusablePresetStorageIntegrityError(
            "preset current pointer identity disagrees with its library marker."
        )
    revision, digest = load_preset_revision(root, kind, preset_id, current.revision)
    if revision.preset_revision_id != current.preset_revision_id:
        raise ReusablePresetStorageIntegrityError(
            "preset current pointer revision identity mismatch."
        )
    if digest != current.revision_sha256:
        raise ReusablePresetStorageIntegrityError(
            "preset current pointer revision digest mismatch."
        )
    return LoadedReusablePreset(
        preset_kind=kind,
        preset_id=preset_id,
        current=revision,
        current_sha256=digest,
    )


def load_preset_revision(
    workspace_root: str | Path,
    kind: str,
    preset_id: str,
    revision: int,
) -> tuple[PresetRevision, str]:
    root = resolve_workspace_root(workspace_root)
    kind = _kind(kind)
    preset_id = _id(preset_id, "preset_id")
    _load_marker(root, kind, preset_id)
    raw = _read_bytes(
        root,
        preset_revision_path(root, kind, preset_id, revision),
        missing=True,
    )
    data = _strict_json(raw)
    value = _preset_from_dict(data)
    if (
        preset_kind(value) != kind
        or value.preset_id != preset_id
        or value.revision != revision
    ):
        raise ReusablePresetStorageIntegrityError(
            "preset revision identity disagrees with its canonical path."
        )
    return value, hashlib.sha256(raw).hexdigest()


def load_preset_revision_by_id(
    workspace_root: str | Path,
    kind: str,
    preset_id: str,
    preset_revision_id: str,
) -> PresetRevision:
    exact_id = _id(preset_revision_id, "preset_revision_id")
    loaded = load_current_preset(workspace_root, kind, preset_id)
    for number in range(loaded.revision, 0, -1):
        value, _ = load_preset_revision(workspace_root, kind, preset_id, number)
        if value.preset_revision_id == exact_id:
            return value
    raise ReusablePresetStorageNotFoundError(
        f"preset revision is not available: {preset_revision_id}"
    )


def create_preset_library(
    workspace_root: str | Path,
    revision: PresetRevision,
) -> LoadedReusablePreset:
    if revision.revision != 1 or revision.supersedes_preset_revision_id is not None:
        raise ReusablePresetStorageWriteError(
            "initial preset creation requires revision 1 with no predecessor."
        )
    root = resolve_workspace_root(workspace_root)
    kind = preset_kind(revision)
    target = preset_root(root, kind, revision.preset_id)
    _safe_descendant(root, target, allow_missing=True)
    if os.path.lexists(target):
        raise ReusablePresetStorageConflictError(
            f"preset identity already exists: {revision.preset_id}"
        )
    try:
        preset_revisions_root(root, kind, revision.preset_id).mkdir(
            parents=True,
            exist_ok=False,
        )
    except FileExistsError as error:
        raise ReusablePresetStorageConflictError(
            f"preset identity already exists: {revision.preset_id}"
        ) from error
    _safe_descendant(root, target)
    marker = _Marker(
        storage_schema_version=_STORAGE_SCHEMA,
        preset_kind=kind,
        preset_id=revision.preset_id,
    )
    revision_bytes = _canonical_json(_preset_to_dict(revision))
    digest = hashlib.sha256(revision_bytes).hexdigest()
    current = _Current(
        storage_schema_version=_STORAGE_SCHEMA,
        preset_kind=kind,
        preset_id=revision.preset_id,
        revision=1,
        preset_revision_id=revision.preset_revision_id,
        revision_sha256=digest,
    )
    try:
        _exclusive_write(
            root,
            preset_marker_path(root, kind, revision.preset_id),
            _canonical_json(_marker_to_dict(marker)),
        )
        _exclusive_write(
            root,
            preset_revision_path(root, kind, revision.preset_id, 1),
            revision_bytes,
        )
        _atomic_replace(
            root,
            preset_current_path(root, kind, revision.preset_id),
            _canonical_json(_current_to_dict(current)),
        )
    except Exception:
        # Preserve any possibly durable state; callers receive the real failure.
        raise
    return load_current_preset(root, kind, revision.preset_id)


def append_preset_revision(
    workspace_root: str | Path,
    revision: PresetRevision,
    *,
    expected_revision: int,
) -> LoadedReusablePreset:
    root = resolve_workspace_root(workspace_root)
    kind = preset_kind(revision)
    current = load_current_preset(root, kind, revision.preset_id)
    if current.revision != expected_revision:
        raise ReusablePresetStorageConflictError(
            "preset changed after it was reviewed."
        )
    if revision.revision != current.revision + 1:
        raise ReusablePresetStorageWriteError(
            "successor preset revision must advance by exactly one."
        )
    if revision.supersedes_preset_revision_id != current.current.preset_revision_id:
        raise ReusablePresetStorageWriteError(
            "successor preset revision must identify the current predecessor."
        )
    for number in range(1, current.revision + 1):
        historical, _ = load_preset_revision(
            root,
            kind,
            revision.preset_id,
            number,
        )
        if historical.preset_revision_id == revision.preset_revision_id:
            raise ReusablePresetStorageConflictError(
                "preset revision identity already exists: "
                f"{revision.preset_revision_id}"
            )
    revision_bytes = _canonical_json(_preset_to_dict(revision))
    digest = hashlib.sha256(revision_bytes).hexdigest()
    revision_path = preset_revision_path(
        root,
        kind,
        revision.preset_id,
        revision.revision,
    )
    if os.path.lexists(revision_path):
        raise ReusablePresetStorageConflictError(
            f"preset revision already exists: {revision.revision}"
        )
    # Recheck immediately before first canonical write.
    latest = load_current_preset(root, kind, revision.preset_id)
    if (
        latest.revision != expected_revision
        or latest.current_sha256 != current.current_sha256
    ):
        raise ReusablePresetStorageConflictError(
            "preset changed after it was reviewed."
        )
    _exclusive_write(root, revision_path, revision_bytes)
    pointer = _Current(
        storage_schema_version=_STORAGE_SCHEMA,
        preset_kind=kind,
        preset_id=revision.preset_id,
        revision=revision.revision,
        preset_revision_id=revision.preset_revision_id,
        revision_sha256=digest,
    )
    _atomic_replace(
        root,
        preset_current_path(root, kind, revision.preset_id),
        _canonical_json(_current_to_dict(pointer)),
    )
    return load_current_preset(root, kind, revision.preset_id)


def _kind(value: str) -> str:
    if value not in PRESET_KINDS:
        raise ReusablePresetStorageReadError(f"unsupported preset kind: {value!r}")
    return value


def _id(value: str, name: str) -> str:
    try:
        return validate_identifier(value, name)
    except (TypeError, ValueError) as error:
        raise ReusablePresetStorageReadError(str(error)) from error


def _positive(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ReusablePresetStorageReadError("revision must be a positive integer.")
    return value


def _load_marker(root: Path, kind: str, preset_id: str) -> _Marker:
    data = _read_json(root, preset_marker_path(root, kind, preset_id), missing=True)
    marker = _marker_from_dict(data)
    if marker.preset_kind != kind or marker.preset_id != preset_id:
        raise ReusablePresetStorageIntegrityError(
            "preset library marker identity disagrees with its canonical path."
        )
    return marker


def _read_json(root: Path, path: Path, *, missing: bool) -> dict[str, Any]:
    return _strict_json(_read_bytes(root, path, missing=missing))


def _read_bytes(root: Path, path: Path, *, missing: bool) -> bytes:
    _safe_descendant(root, path, allow_missing=missing)
    if not os.path.lexists(path):
        if missing:
            raise ReusablePresetStorageNotFoundError(
                f"preset state is not available: {path}"
            )
        raise ReusablePresetStorageReadError(f"preset state is missing: {path}")
    if _is_link_like(path) or not path.is_file():
        raise ReusablePresetStorageIntegrityError(
            f"preset state is not a canonical file: {path}"
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise ReusablePresetStorageReadError(
            f"could not read preset state: {error}"
        ) from error


def _strict_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReusablePresetStorageIntegrityError("preset JSON is invalid.") from error
    if not isinstance(value, dict):
        raise ReusablePresetStorageIntegrityError("preset JSON root must be an object.")
    return cast(dict[str, Any], value)


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    rendered = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return (rendered + "\n").encode("utf-8")


def _exclusive_write(root: Path, path: Path, data: bytes) -> None:
    _safe_descendant(root, path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe_descendant(root, path.parent)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as error:
        raise ReusablePresetStorageConflictError(
            f"create-only preset state already exists: {path}"
        ) from error
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        raise


def _atomic_replace(root: Path, path: Path, data: bytes) -> None:
    _safe_descendant(root, path, allow_missing=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    _safe_descendant(root, path.parent)
    fd, raw_temp = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(raw_temp)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _safe_descendant(root, temp_path)
        os.replace(temp_path, path)
    finally:
        if os.path.lexists(temp_path):
            try:
                temp_path.unlink()
            except OSError:
                pass


def _safe_descendant(root: Path, path: Path, *, allow_missing: bool = False) -> None:
    root = resolve_workspace_root(root)
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ReusablePresetStorageIntegrityError(
            f"preset path escapes workspace root: {path}"
        ) from error
    current = root
    parts = path.relative_to(root).parts
    for index, part in enumerate(parts):
        current = current / part
        if not os.path.lexists(current):
            if allow_missing:
                return
            raise ReusablePresetStorageIntegrityError(
                f"preset path component is missing: {current}"
            )
        if _is_link_like(current):
            raise ReusablePresetStorageIntegrityError(
                f"preset path contains link-like component: {current}"
            )
        if index < len(parts) - 1 and not current.is_dir():
            raise ReusablePresetStorageIntegrityError(
                f"preset path ancestor is not a directory: {current}"
            )


def _is_link_like(path: Path) -> bool:
    try:
        info = path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse and attributes & reparse)


def _marker_to_dict(value: _Marker) -> dict[str, Any]:
    return {
        "storage_schema_version": value.storage_schema_version,
        "preset_kind": value.preset_kind,
        "preset_id": value.preset_id,
    }


def _marker_from_dict(data: dict[str, Any]) -> _Marker:
    _exact_keys(
        data,
        {"storage_schema_version", "preset_kind", "preset_id"},
        "preset marker",
    )
    if data["storage_schema_version"] != _STORAGE_SCHEMA:
        raise ReusablePresetStorageIntegrityError("unsupported preset storage schema.")
    if not isinstance(data["preset_kind"], str) or not isinstance(
        data["preset_id"], str
    ):
        raise ReusablePresetStorageIntegrityError("preset marker fields are invalid.")
    return _Marker(
        storage_schema_version=_STORAGE_SCHEMA,
        preset_kind=_kind(data["preset_kind"]),
        preset_id=_id(data["preset_id"], "preset_id"),
    )


def _current_to_dict(value: _Current) -> dict[str, Any]:
    return {
        "storage_schema_version": value.storage_schema_version,
        "preset_kind": value.preset_kind,
        "preset_id": value.preset_id,
        "revision": value.revision,
        "preset_revision_id": value.preset_revision_id,
        "revision_sha256": value.revision_sha256,
    }


def _current_from_dict(data: dict[str, Any]) -> _Current:
    _exact_keys(
        data,
        {
            "storage_schema_version",
            "preset_kind",
            "preset_id",
            "revision",
            "preset_revision_id",
            "revision_sha256",
        },
        "preset current pointer",
    )
    if data["storage_schema_version"] != _STORAGE_SCHEMA:
        raise ReusablePresetStorageIntegrityError("unsupported preset storage schema.")
    if (
        not isinstance(data["preset_kind"], str)
        or not isinstance(data["preset_id"], str)
        or not isinstance(data["preset_revision_id"], str)
        or not isinstance(data["revision_sha256"], str)
    ):
        raise ReusablePresetStorageIntegrityError(
            "preset current pointer fields are invalid."
        )
    revision = data["revision"]
    if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
        raise ReusablePresetStorageIntegrityError("preset current revision is invalid.")
    digest = data["revision_sha256"]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ReusablePresetStorageIntegrityError("preset current digest is invalid.")
    return _Current(
        storage_schema_version=_STORAGE_SCHEMA,
        preset_kind=_kind(data["preset_kind"]),
        preset_id=_id(data["preset_id"], "preset_id"),
        revision=revision,
        preset_revision_id=_id(data["preset_revision_id"], "preset_revision_id"),
        revision_sha256=digest,
    )


def _provenance_to_dict(value: Provenance) -> dict[str, Any]:
    if value.source_reference is not None:
        raise ReusablePresetStorageWriteError(
            "reusable preset provenance must not embed an operational source reference."
        )
    return {
        "actor": {
            "actor_kind": value.actor.actor_kind,
            "actor_id": value.actor.actor_id,
            "owning_system": value.actor.owning_system,
            "display_label_snapshot": value.actor.display_label_snapshot,
            "role_snapshot": value.actor.role_snapshot,
        },
        "timestamp": value.timestamp,
        "source_kind": value.source_kind,
        "source_reference": None,
        "application_version": value.application_version,
        "note": value.note,
    }


def _provenance_from_dict(data: Any) -> Provenance:
    if not isinstance(data, dict):
        raise ReusablePresetStorageIntegrityError(
            "preset provenance must be an object."
        )
    _exact_keys(
        data,
        {
            "actor",
            "timestamp",
            "source_kind",
            "source_reference",
            "application_version",
            "note",
        },
        "preset provenance",
    )
    actor_data = data["actor"]
    if not isinstance(actor_data, dict):
        raise ReusablePresetStorageIntegrityError("preset actor must be an object.")
    _exact_keys(
        actor_data,
        {
            "actor_kind",
            "actor_id",
            "owning_system",
            "display_label_snapshot",
            "role_snapshot",
        },
        "preset actor",
    )
    if data["source_reference"] is not None:
        raise ReusablePresetStorageIntegrityError(
            "reusable preset provenance must not embed an operational source reference."
        )
    try:
        actor = ActorReference(**actor_data)
        return Provenance(
            actor=actor,
            timestamp=data["timestamp"],
            source_kind=data["source_kind"],
            source_reference=None,
            application_version=data["application_version"],
            note=data["note"],
        )
    except (TypeError, ValueError) as error:
        raise ReusablePresetStorageIntegrityError(str(error)) from error


def _level_to_dict(value: ScoringScaleLevel) -> dict[str, Any]:
    return {
        "value": value.value,
        "label": value.label,
        "meaning": value.meaning,
        "position": value.position,
        "description": value.description,
    }


def _level_from_dict(data: Any) -> ScoringScaleLevel:
    if not isinstance(data, dict):
        raise ReusablePresetStorageIntegrityError(
            "Scale preset level must be an object."
        )
    _exact_keys(
        data,
        {"value", "label", "meaning", "position", "description"},
        "Scale preset level",
    )
    try:
        return ScoringScaleLevel(**data)
    except (TypeError, ValueError) as error:
        raise ReusablePresetStorageIntegrityError(str(error)) from error


def _criterion_to_dict(value: CriterionPresetSpec) -> dict[str, Any]:
    return {
        "key": value.key,
        "label": value.label,
        "definition": value.definition,
        "criterion_kind": value.criterion_kind,
        "supported_target_kinds": list(value.supported_target_kinds),
        "standard_id": value.standard_id,
        "alignment_standard_ids": list(value.alignment_standard_ids),
        "default_scoring_scale_preset_id": value.default_scoring_scale_preset_id,
        "default_scoring_scale_preset_revision_id": (
            value.default_scoring_scale_preset_revision_id
        ),
        "status": value.status,
    }


def _criterion_from_dict(data: Any) -> CriterionPresetSpec:
    if not isinstance(data, dict):
        raise ReusablePresetStorageIntegrityError(
            "Criterion preset member must be an object."
        )
    _exact_keys(
        data,
        {
            "key",
            "label",
            "definition",
            "criterion_kind",
            "supported_target_kinds",
            "standard_id",
            "alignment_standard_ids",
            "default_scoring_scale_preset_id",
            "default_scoring_scale_preset_revision_id",
            "status",
        },
        "Criterion preset member",
    )
    try:
        return CriterionPresetSpec(
            key=data["key"],
            label=data["label"],
            definition=data["definition"],
            criterion_kind=data["criterion_kind"],
            supported_target_kinds=tuple(data["supported_target_kinds"]),
            standard_id=data["standard_id"],
            alignment_standard_ids=tuple(data["alignment_standard_ids"]),
            default_scoring_scale_preset_id=data["default_scoring_scale_preset_id"],
            default_scoring_scale_preset_revision_id=(
                data["default_scoring_scale_preset_revision_id"]
            ),
            status=data["status"],
        )
    except (TypeError, ValueError) as error:
        raise ReusablePresetStorageIntegrityError(str(error)) from error


def _common(value: PresetRevision) -> dict[str, Any]:
    return {
        "schema_version": PRESET_SCHEMA_VERSION,
        "preset_kind": preset_kind(value),
        "preset_id": value.preset_id,
        "preset_revision_id": value.preset_revision_id,
        "revision": value.revision,
        "name": value.name,
        "status": value.status,
        "created_provenance": _provenance_to_dict(value.created_provenance),
        "supersedes_preset_revision_id": value.supersedes_preset_revision_id,
    }


def _preset_to_dict(value: PresetRevision) -> dict[str, Any]:
    data = _common(value)
    if isinstance(value, RolePresetRevision):
        data.update(
            {
                "role_key": value.role_key,
                "role_label": value.role_label,
                "description": value.description,
                "applicability_hints": list(value.applicability_hints),
            }
        )
    elif isinstance(value, ResponsibilityPresetRevision):
        data.update(
            {
                "description": value.description,
                "expected_output": value.expected_output,
                "applicability_hints": list(value.applicability_hints),
            }
        )
    elif isinstance(value, ScoringScalePresetRevision):
        data.update(
            {
                "scale_type": value.scale_type,
                "levels": [_level_to_dict(item) for item in value.levels],
                "intended_use": value.intended_use,
                "aggregation_guidance": value.aggregation_guidance,
            }
        )
    elif isinstance(value, CriterionSetPresetRevision):
        data.update(
            {
                "purpose": value.purpose,
                "criterion_set_kind": value.criterion_set_kind,
                "criteria": [_criterion_to_dict(item) for item in value.criteria],
                "standards_profile_id": value.standards_profile_id,
            }
        )
    else:
        raise ReusablePresetStorageWriteError("unsupported preset type.")
    return data


def _preset_from_dict(data: dict[str, Any]) -> PresetRevision:
    kind_value = data.get("preset_kind")
    if not isinstance(kind_value, str):
        raise ReusablePresetStorageIntegrityError("preset_kind is invalid.")
    kind = _kind(kind_value)
    common_keys = {
        "schema_version",
        "preset_kind",
        "preset_id",
        "preset_revision_id",
        "revision",
        "name",
        "status",
        "created_provenance",
        "supersedes_preset_revision_id",
    }
    extras: set[str]
    if kind == "role":
        extras = {"role_key", "role_label", "description", "applicability_hints"}
    elif kind == "responsibility":
        extras = {"description", "expected_output", "applicability_hints"}
    elif kind == "criterion_set":
        extras = {"purpose", "criterion_set_kind", "criteria", "standards_profile_id"}
    else:
        extras = {"scale_type", "levels", "intended_use", "aggregation_guidance"}
    _exact_keys(data, common_keys | extras, f"{kind} preset revision")
    if data["schema_version"] != PRESET_SCHEMA_VERSION:
        raise ReusablePresetStorageIntegrityError("unsupported reusable preset schema.")
    common = dict(
        preset_id=data["preset_id"],
        preset_revision_id=data["preset_revision_id"],
        revision=data["revision"],
        name=data["name"],
        status=data["status"],
        created_provenance=_provenance_from_dict(data["created_provenance"]),
        supersedes_preset_revision_id=data["supersedes_preset_revision_id"],
    )
    try:
        if kind == "role":
            return RolePresetRevision(
                **common,
                role_key=data["role_key"],
                role_label=data["role_label"],
                description=data["description"],
                applicability_hints=tuple(data["applicability_hints"]),
            )
        if kind == "responsibility":
            return ResponsibilityPresetRevision(
                **common,
                description=data["description"],
                expected_output=data["expected_output"],
                applicability_hints=tuple(data["applicability_hints"]),
            )
        if kind == "criterion_set":
            return CriterionSetPresetRevision(
                **common,
                purpose=data["purpose"],
                criterion_set_kind=data["criterion_set_kind"],
                criteria=tuple(_criterion_from_dict(item) for item in data["criteria"]),
                standards_profile_id=data["standards_profile_id"],
            )
        return ScoringScalePresetRevision(
            **common,
            scale_type=data["scale_type"],
            levels=tuple(_level_from_dict(item) for item in data["levels"]),
            intended_use=data["intended_use"],
            aggregation_guidance=data["aggregation_guidance"],
        )
    except (TypeError, ValueError) as error:
        raise ReusablePresetStorageIntegrityError(str(error)) from error


def _exact_keys(data: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(data)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ReusablePresetStorageIntegrityError(
            f"{label} fields are invalid; missing={missing}, unexpected={extra}."
        )


__all__ = [
    "LoadedReusablePreset",
    "ReusablePresetStorageConflictError",
    "ReusablePresetStorageError",
    "ReusablePresetStorageIntegrityError",
    "ReusablePresetStorageNotFoundError",
    "ReusablePresetStorageReadError",
    "ReusablePresetStorageWriteError",
    "append_preset_revision",
    "create_preset_library",
    "list_preset_ids",
    "load_current_preset",
    "load_preset_revision",
    "load_preset_revision_by_id",
    "preset_current_path",
    "preset_kind_root",
    "preset_library_root",
    "preset_marker_path",
    "preset_revision_path",
    "preset_revisions_root",
    "preset_root",
]
