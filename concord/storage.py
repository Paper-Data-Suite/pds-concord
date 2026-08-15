"""Strict reads and guarded batch commits for canonical Concord state."""

from __future__ import annotations

import hashlib
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Iterable, TypeVar, cast

from pds_core.class_metadata import load_class_metadata_for_class
from pds_core.routes import module_work_collection_dir
from pds_core.routing_models import ModuleWorkRef, module_work_ref_to_dict
from pds_core.workspace import inspect_workspace_root, resolve_workspace_root

from concord.model_conversion import Record, record_from_dict, record_to_dict
from concord.model_validation import (
    ConcordRecordGraph,
    validate_core_standards,
    validate_record_graph,
)
from concord.record_registry import (
    RECORD_DESCRIPTORS,
    descriptor_for_kind,
    descriptor_for_record,
)
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStorageError,
    ConcordStorageGraphIntegrityError,
    ConcordStorageIntegrityError,
    ConcordStorageNotFoundError,
    ConcordStoragePartialSuccessError,
    ConcordStorageReadError,
    ConcordStorageValidationError,
    ConcordStorageWriteError,
)
from concord.storage_models import (
    CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
    CONCORD_STORAGE_SCHEMA_VERSION,
    ConcordCurrentSnapshot,
    ConcordLoadedRecordGraph,
    ConcordRecordRevision,
    ConcordRecordRevisionRef,
    ConcordStorageCommitResult,
    ConcordWorkMarker,
    ConcordWorkSnapshot,
)
from concord.storage_paths import (
    current_snapshot_path,
    locks_path,
    record_revision_path,
    record_revisions_path,
    records_path,
    snapshot_path,
    snapshots_path,
    state_path,
    work_marker_path,
    work_root,
    write_lock_path,
)
from concord.storage_serialization import (
    canonical_json_bytes,
    current_from_dict,
    marker_from_dict,
    revision_from_dict,
    serialize,
    snapshot_from_dict,
    strict_json_loads,
)
from concord.validation_diagnostics import ConcordRecordGraphError

T = TypeVar("T")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_no_symlink_ancestors(path: Path) -> None:
    for ancestor in (path, *path.parents):
        try:
            if ancestor.is_symlink():
                raise ConcordStorageIntegrityError(
                    f"canonical path traverses a symlink: {ancestor}"
                )
        except OSError as error:
            raise ConcordStorageReadError(
                f"could not inspect canonical path {ancestor}: {error}"
            ) from error


def require_regular_nonsymlink_file(
    path: Path,
    *,
    missing: bool = False,
) -> None:
    _require_no_symlink_ancestors(path)
    try:
        if path.is_symlink() or not path.is_file():
            if not path.exists() and not path.is_symlink() and missing:
                raise ConcordStorageNotFoundError(f"canonical object not found: {path}")
            raise ConcordStorageIntegrityError(
                f"canonical path is not a regular non-symlink file: {path}"
            )
    except ConcordStorageNotFoundError:
        raise
    except OSError as error:
        raise ConcordStorageReadError(
            f"could not inspect canonical path {path}: {error}"
        ) from error


def read_canonical_bytes(path: Path, *, missing: bool = False) -> bytes:
    require_regular_nonsymlink_file(path, missing=missing)
    try:
        return path.read_bytes()
    except FileNotFoundError as error:
        raise ConcordStorageNotFoundError(
            f"canonical object not found: {path}"
        ) from error
    except OSError as error:
        raise ConcordStorageReadError(f"could not read {path}: {error}") from error


def _parse(
    path: Path, parser: Callable[[object], T], *, missing: bool = False
) -> tuple[T, bytes]:
    data = read_canonical_bytes(path, missing=missing)
    try:
        return parser(strict_json_loads(data)), data
    except (
        ConcordStorageReadError,
        ConcordStorageValidationError,
        ValueError,
    ) as error:
        raise ConcordStorageReadError(
            f"invalid canonical object at {path}: {error}"
        ) from error


def load_work_marker(
    workspace_root: str | Path, work: ModuleWorkRef
) -> ConcordWorkMarker:
    value, _ = _parse(
        work_marker_path(workspace_root, work), marker_from_dict, missing=True
    )
    if value.work != work:
        raise ConcordStorageIntegrityError(
            "work marker identity disagrees with its canonical path."
        )
    return value


def _record_revision_from_bytes(
    data: bytes,
    *,
    work: ModuleWorkRef,
    record_kind: str,
    record_id: str,
    record_revision: int,
) -> tuple[Record, ConcordRecordRevision]:
    """Parse and verify one already-read immutable record revision."""
    descriptor = descriptor_for_kind(record_kind)
    try:
        envelope = revision_from_dict(strict_json_loads(data))
    except (
        ConcordStorageReadError,
        ConcordStorageValidationError,
        ValueError,
    ) as error:
        raise ConcordStorageReadError(
            "invalid canonical record revision bytes."
        ) from error
    if (
        envelope.work != work
        or envelope.record_kind != record_kind
        or envelope.record_id != record_id
        or envelope.record_revision != record_revision
    ):
        raise ConcordStorageIntegrityError(
            "record envelope identity disagrees with its canonical path."
        )
    try:
        record = record_from_dict(record_kind, envelope.body)
    except ValueError as error:
        raise ConcordStorageReadError(
            "invalid canonical record body."
        ) from error
    if (
        getattr(record, descriptor.identity_field) != record_id
        or record_to_dict(record) != envelope.body
    ):
        raise ConcordStorageIntegrityError(
            "record body identity or round trip disagrees with its envelope."
        )
    return record, envelope


def load_record_revision(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    record_kind: str,
    record_id: str,
    record_revision: int,
) -> tuple[Record, ConcordRecordRevision]:
    path = record_revision_path(
        workspace_root, work, record_kind, record_id, record_revision
    )
    data = read_canonical_bytes(path, missing=True)
    return _record_revision_from_bytes(
        data,
        work=work,
        record_kind=record_kind,
        record_id=record_id,
        record_revision=record_revision,
    )

def _visible(path: Path, description: str) -> tuple[Path, ...]:
    try:
        _require_no_symlink_ancestors(path)
        entries = tuple(path.iterdir())
    except FileNotFoundError:
        return ()
    except OSError as error:
        raise ConcordStorageReadError(
            f"could not enumerate {description} {path}: {error}"
        ) from error
    return tuple(
        sorted((p for p in entries if not p.name.startswith(".")), key=lambda p: p.name)
    )


def list_record_revisions(
    workspace_root: str | Path, work: ModuleWorkRef, record_kind: str, record_id: str
) -> tuple[int, ...]:
    descriptor_for_kind(record_kind)
    result: list[int] = []
    for path in _visible(
        record_revisions_path(workspace_root, work, record_kind, record_id),
        "record revisions",
    ):
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.name.endswith(".json")
            or not path.stem.isdigit()
            or path.stem.startswith("0")
        ):
            raise ConcordStorageIntegrityError(
                f"unexpected record revision entry: {path}"
            )
        revision = int(path.stem)
        load_record_revision(workspace_root, work, record_kind, record_id, revision)
        result.append(revision)
    return tuple(sorted(result))


def list_record_identities(
    workspace_root: str | Path, work: ModuleWorkRef
) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for kind_path in _visible(records_path(workspace_root, work), "record kinds"):
        descriptor_for_kind(kind_path.name)
        if kind_path.is_symlink() or not kind_path.is_dir():
            raise ConcordStorageIntegrityError(
                f"unexpected record kind entry: {kind_path}"
            )
        for identity_path in _visible(kind_path, "record identities"):
            if identity_path.is_symlink() or not identity_path.is_dir():
                raise ConcordStorageIntegrityError(
                    f"unexpected record identity entry: {identity_path}"
                )
            children = _visible(identity_path, "record identity")
            if tuple(p.name for p in children) != ("revisions",):
                raise ConcordStorageIntegrityError(
                    f"unexpected record identity contents: {identity_path}"
                )
            list_record_revisions(
                workspace_root, work, kind_path.name, identity_path.name
            )
            result.append((kind_path.name, identity_path.name))
    return tuple(sorted(result))


def _load_snapshot_chain(
    workspace_root: str | Path, work: ModuleWorkRef, snapshot_revision: int
) -> tuple[ConcordWorkSnapshot, bytes]:
    target, target_bytes = _parse(
        snapshot_path(workspace_root, work, snapshot_revision),
        snapshot_from_dict,
        missing=True,
    )
    if target.work != work or target.snapshot_revision != snapshot_revision:
        raise ConcordStorageIntegrityError(
            "snapshot identity disagrees with its canonical path."
        )

    child = target
    for expected_revision in range(snapshot_revision - 1, 0, -1):
        predecessor, predecessor_bytes = _parse(
            snapshot_path(workspace_root, work, expected_revision),
            snapshot_from_dict,
            missing=True,
        )
        if (
            predecessor.work != work
            or predecessor.snapshot_revision != expected_revision
        ):
            raise ConcordStorageIntegrityError(
                "snapshot predecessor identity disagrees with its canonical path."
            )
        if child.previous_snapshot_revision != expected_revision:
            raise ConcordStorageIntegrityError(
                "snapshot predecessor revision mismatch."
            )
        if child.previous_snapshot_sha256 != _sha(predecessor_bytes):
            raise ConcordStorageIntegrityError("snapshot predecessor digest mismatch.")
        child = predecessor

    return target, target_bytes


def _validated_snapshot_graph(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    snapshot: ConcordWorkSnapshot,
) -> ConcordRecordGraph:
    """Materialize a graph from the exact bytes bound by one snapshot."""
    selected_records: list[Record] = []
    for ref in snapshot.records:
        record_path = record_revision_path(
            workspace_root,
            work,
            ref.record_kind,
            ref.record_id,
            ref.record_revision,
        )
        data = read_canonical_bytes(record_path, missing=True)
        if _sha(data) != ref.sha256:
            raise ConcordStorageIntegrityError(
                f"record digest mismatch for {ref.record_kind}:{ref.record_id}."
            )
        record, _ = _record_revision_from_bytes(
            data,
            work=work,
            record_kind=ref.record_kind,
            record_id=ref.record_id,
            record_revision=ref.record_revision,
        )
        selected_records.append(record)
    try:
        graph = _graph_from_records(selected_records)
        if len(graph.activities) != 1 or graph.activities[0].work_reference != work:
            raise ConcordStorageIntegrityError(
                "snapshot must contain exactly one matching Activity."
            )
        validate_record_graph(graph)
    except ConcordStorageIntegrityError:
        raise
    except ConcordRecordGraphError as error:
        raise ConcordStorageGraphIntegrityError(
            "snapshot graph is invalid.", issues=error.issues
        ) from error
    except ValueError as error:
        raise ConcordStorageIntegrityError(
            f"snapshot graph is invalid: {error}"
        ) from error
    return graph


def load_work_snapshot(
    workspace_root: str | Path, work: ModuleWorkRef, snapshot_revision: int
) -> tuple[ConcordWorkSnapshot, str]:
    value, data = _load_snapshot_chain(workspace_root, work, snapshot_revision)
    _validated_snapshot_graph(workspace_root, work, value)
    return value, _sha(data)


def load_record_graph_at_snapshot(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    snapshot_revision: int,
) -> ConcordLoadedRecordGraph:
    """Load one exact immutable historical graph without consulting current.json."""
    load_work_marker(workspace_root, work)
    snapshot, snapshot_bytes = _load_snapshot_chain(
        workspace_root,
        work,
        snapshot_revision,
    )
    graph = _validated_snapshot_graph(workspace_root, work, snapshot)
    return ConcordLoadedRecordGraph(
        graph,
        snapshot.snapshot_revision,
        _sha(snapshot_bytes),
    )

def list_work_snapshots(
    workspace_root: str | Path, work: ModuleWorkRef
) -> tuple[int, ...]:
    result: list[int] = []
    for path in _visible(snapshots_path(workspace_root, work), "snapshots"):
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.name.endswith(".json")
            or not path.stem.isdigit()
            or path.stem.startswith("0")
        ):
            raise ConcordStorageIntegrityError(f"unexpected snapshot entry: {path}")
        revision = int(path.stem)
        load_work_snapshot(workspace_root, work, revision)
        result.append(revision)
    return tuple(sorted(result))


def load_current_snapshot(
    workspace_root: str | Path, work: ModuleWorkRef
) -> ConcordCurrentSnapshot:
    value, _ = _parse(
        current_snapshot_path(workspace_root, work), current_from_dict, missing=True
    )
    if value.work != work:
        raise ConcordStorageIntegrityError(
            "current pointer work disagrees with canonical path."
        )
    _, digest = load_work_snapshot(workspace_root, work, value.snapshot_revision)
    if digest != value.snapshot_sha256:
        raise ConcordStorageIntegrityError("current pointer snapshot digest mismatch.")
    return value


def load_current_record_graph(
    workspace_root: str | Path, work: ModuleWorkRef, *, standards_library: Any = None
) -> ConcordLoadedRecordGraph:
    load_work_marker(workspace_root, work)
    current = load_current_snapshot(workspace_root, work)
    snapshot, snapshot_bytes = _load_snapshot_chain(
        workspace_root,
        work,
        current.snapshot_revision,
    )
    snapshot_sha256 = _sha(snapshot_bytes)
    if snapshot_sha256 != current.snapshot_sha256:
        raise ConcordStorageIntegrityError(
            "current pointer snapshot digest mismatch."
        )
    graph = _validated_snapshot_graph(workspace_root, work, snapshot)
    try:
        validate_record_graph(graph)
        requires_standards = (
            graph.activities[0].scoring_orientation in {"standards_based", "mixed"}
            or any(item.criterion_kind == "standard_backed" for item in graph.criteria)
            or any(item.score_kind == "standard_backed" for item in graph.score_records)
        )
        if requires_standards:
            if standards_library is None:
                raise ConcordStorageValidationError(
                    "standards_library is required for this Activity."
                )
            validate_core_standards(graph, standards_library)
    except ConcordStorageValidationError:
        raise
    except ConcordRecordGraphError as error:
        raise ConcordStorageGraphIntegrityError(
            "current graph is invalid.", issues=error.issues
        ) from error
    except ValueError as error:
        raise ConcordStorageIntegrityError(
            f"current graph is invalid: {error}"
        ) from error
    return ConcordLoadedRecordGraph(
        graph,
        current.snapshot_revision,
        snapshot_sha256,
    )

def load_current_record(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    record_kind: str,
    record_id: str,
) -> tuple[Record, ConcordRecordRevision]:
    current = load_current_snapshot(workspace_root, work)
    snapshot, snapshot_bytes = _load_snapshot_chain(
        workspace_root,
        work,
        current.snapshot_revision,
    )
    if _sha(snapshot_bytes) != current.snapshot_sha256:
        raise ConcordStorageIntegrityError(
            "current pointer snapshot digest mismatch."
        )
    ref = next(
        (
            item
            for item in snapshot.records
            if (item.record_kind, item.record_id) == (record_kind, record_id)
        ),
        None,
    )
    if ref is None:
        raise ConcordStorageNotFoundError(
            f"record is not selected by current snapshot: {record_kind}:{record_id}"
        )
    path = record_revision_path(
        workspace_root,
        work,
        ref.record_kind,
        ref.record_id,
        ref.record_revision,
    )
    data = read_canonical_bytes(path, missing=True)
    if _sha(data) != ref.sha256:
        raise ConcordStorageIntegrityError(
            f"record digest mismatch for {ref.record_kind}:{ref.record_id}."
        )
    return _record_revision_from_bytes(
        data,
        work=work,
        record_kind=ref.record_kind,
        record_id=ref.record_id,
        record_revision=ref.record_revision,
    )

def list_activity_work_refs(
    workspace_root: str | Path, class_id: str
) -> tuple[ModuleWorkRef, ...]:
    root = module_work_collection_dir(
        resolve_workspace_root(workspace_root), class_id, "concord"
    )
    result: list[ModuleWorkRef] = []
    for entry in _visible(root, "Concord work collection"):
        if entry.is_symlink() or not entry.is_dir():
            raise ConcordStorageIntegrityError(f"unexpected work entry: {entry}")
        work = ModuleWorkRef(module_id="concord", class_id=class_id, work_id=entry.name)
        marker = load_work_marker(workspace_root, work)
        if marker.work != work:
            raise ConcordStorageIntegrityError("discovered marker identity mismatch.")
        result.append(work)
    return tuple(sorted(result, key=lambda w: w.work_id))


def _validate_canonical_write_history(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    current_snapshot: ConcordWorkSnapshot | None,
) -> None:
    try:
        snapshot_revisions = list_work_snapshots(workspace_root, work)
        record_identities = list_record_identities(workspace_root, work)
    except ConcordStorageIntegrityError:
        raise
    except ConcordStorageError as error:
        raise ConcordStorageIntegrityError(
            "canonical history cannot be proven safe for writing."
        ) from error

    if current_snapshot is None:
        if snapshot_revisions or record_identities:
            raise ConcordStorageIntegrityError(
                "orphan canonical history blocks initial creation."
            )
        return

    expected_snapshots = tuple(range(1, current_snapshot.snapshot_revision + 1))
    if snapshot_revisions != expected_snapshots:
        raise ConcordStorageIntegrityError(
            "snapshot history is noncontiguous or contains orphan revisions."
        )

    selected = {
        (reference.record_kind, reference.record_id): reference
        for reference in current_snapshot.records
    }
    if record_identities != tuple(sorted(selected)):
        raise ConcordStorageIntegrityError(
            "canonical record identities disagree with the current snapshot."
        )

    for identity, reference in sorted(selected.items()):
        revisions = list_record_revisions(
            workspace_root,
            work,
            identity[0],
            identity[1],
        )
        expected_revisions = tuple(range(1, reference.record_revision + 1))
        if revisions != expected_revisions:
            raise ConcordStorageIntegrityError(
                "record history is noncontiguous or contains an orphan "
                f"revision for {identity[0]}:{identity[1]}."
            )


def _write_exclusive(path: Path, data: bytes) -> None:
    created = False
    file_synced = False
    try:
        _require_no_symlink_ancestors(path)
        with path.open("xb") as target:
            created = True
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
            file_synced = True
        _fsync_directory_if_supported(path.parent)
    except FileExistsError as error:
        raise ConcordStorageConflictError(
            f"immutable canonical file already exists: {path}"
        ) from error
    except OSError as error:
        if created and not file_synced:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                raise ConcordStoragePartialSuccessError(
                    "exclusive write failed and the partially written file "
                    "could not be removed.",
                    durable_paths=(str(path),),
                    pointer_published=False,
                    snapshot_revision=None,
                    snapshot_sha256=None,
                ) from cleanup_error
        if created and file_synced:
            raise ConcordStoragePartialSuccessError(
                "canonical file bytes were written and synchronized, but "
                "directory durability could not be confirmed.",
                durable_paths=(str(path),),
                pointer_published=False,
                snapshot_revision=None,
                snapshot_sha256=None,
            ) from error
        raise ConcordStorageWriteError(f"could not write {path}: {error}") from error


def _require_safe_storage_directories(
    workspace_root: str | Path, work: ModuleWorkRef
) -> None:
    root = resolve_workspace_root(workspace_root)
    canonical_work = work_root(root, work)
    try:
        canonical_work.relative_to(root)
    except ValueError as error:
        raise ConcordStorageIntegrityError(
            "Core work root is outside the resolved workspace root."
        ) from error
    state = state_path(root, work)
    for path in (
        canonical_work,
        state,
        records_path(root, work),
        snapshots_path(root, work),
        locks_path(root, work),
    ):
        if path.exists() and (path.is_symlink() or not path.is_dir()):
            raise ConcordStorageIntegrityError(
                f"canonical storage directory is unsafe: {path}"
            )


def _lock_bytes(work: ModuleWorkRef, purpose: str) -> bytes:
    return canonical_json_bytes(
        {
            "schema_version": "1",
            "record_type": "concord_storage_lock",
            "work": module_work_ref_to_dict(work),
            "purpose": purpose,
        }
    )


def _publish(path: Path, data: bytes) -> None:
    temp: Path | None = None
    try:
        _require_no_symlink_ancestors(path)
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
        raise ConcordStorageWriteError(
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


def _graph_from_records(records: Iterable[Record]) -> ConcordRecordGraph:
    collections: dict[str, list[Record]] = {
        d.graph_collection: [] for d in RECORD_DESCRIPTORS
    }
    for record in records:
        collections[descriptor_for_record(record).graph_collection].append(record)
    return ConcordRecordGraph(
        **cast(Any, {key: tuple(value) for key, value in collections.items()})
    )


def _records_by_identity(
    graph: ConcordRecordGraph,
) -> dict[tuple[str, str], Record]:
    return {
        (descriptor.kind, str(getattr(record, descriptor.identity_field))): record
        for descriptor in RECORD_DESCRIPTORS
        for record in getattr(graph, descriptor.graph_collection)
    }


def _validate_candidate(
    work: ModuleWorkRef, graph: ConcordRecordGraph, standards_library: Any
) -> None:
    if len(graph.activities) != 1 or graph.activities[0].work_reference != work:
        raise ConcordStorageValidationError(
            "candidate graph must contain exactly one Activity matching work."
        )
    try:
        validate_record_graph(graph)
    except ValueError as error:
        raise ConcordStorageValidationError(
            f"candidate graph is invalid: {error}"
        ) from error
    activity = graph.activities[0]
    requires_standards = (
        activity.scoring_orientation in {"standards_based", "mixed"}
        or any(item.criterion_kind == "standard_backed" for item in graph.criteria)
        or any(item.score_kind == "standard_backed" for item in graph.score_records)
    )
    if requires_standards:
        if standards_library is None:
            raise ConcordStorageValidationError(
                "standards_library is required for this Activity."
            )
        try:
            validate_core_standards(graph, standards_library)
        except ValueError as error:
            raise ConcordStorageValidationError(
                f"candidate standards selection is invalid: {error}"
            ) from error


def commit_record_batch(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    records: Iterable[Record],
    *,
    expected_snapshot_revision: int | None,
    standards_library: Any = None,
) -> ConcordStorageCommitResult:
    if not isinstance(work, ModuleWorkRef) or work.module_id != "concord":
        raise ConcordStorageValidationError("work must be a Concord ModuleWorkRef.")
    candidates = tuple(records)
    if not candidates:
        raise ConcordStorageValidationError(
            "records must contain one or more native records."
        )
    candidate_map: dict[tuple[str, str], Record] = {}
    for record in candidates:
        try:
            descriptor = descriptor_for_record(record)
        except ValueError as error:
            raise ConcordStorageValidationError(str(error)) from error
        identity = (descriptor.kind, str(getattr(record, descriptor.identity_field)))
        if identity in candidate_map:
            raise ConcordStorageValidationError(
                f"duplicate candidate identity {identity[0]}:{identity[1]}."
            )
        candidate_map[identity] = record
    if expected_snapshot_revision is not None and (
        type(expected_snapshot_revision) is not int or expected_snapshot_revision < 1
    ):
        raise ConcordStorageValidationError(
            "expected_snapshot_revision must be a positive integer or None."
        )
    status = inspect_workspace_root(workspace_root)
    if not status.exists or not status.is_dir or not status.is_writable:
        raise ConcordStorageWriteError(
            "an existing writable Core workspace is required."
        )
    try:
        metadata = load_class_metadata_for_class(status.root, work.class_id)
    except ValueError as error:
        raise ConcordStorageWriteError(
            "an existing matching Core class is required."
        ) from error
    if metadata.class_id != work.class_id:
        raise ConcordStorageValidationError("Core class identity mismatch.")
    _require_safe_storage_directories(status.root, work)
    lock_dir = locks_path(status.root, work)
    lock_dir.mkdir(parents=True, exist_ok=True)
    _require_safe_storage_directories(status.root, work)
    lock = write_lock_path(status.root, work)
    acquired = False
    pointer_published = False
    published_snapshot_revision: int | None = None
    published_snapshot_sha256: str | None = None
    durable: list[str] = []
    result: ConcordStorageCommitResult | None = None
    operation_error: Exception | None = None
    lock_cleanup_error: OSError | None = None

    class _CommitComplete(Exception):
        pass

    try:
        try:
            with lock.open("xb") as target:
                acquired = True
                target.write(_lock_bytes(work, "canonical_commit"))
                target.flush()
                os.fsync(target.fileno())

            _fsync_directory_if_supported(lock.parent)
        except FileExistsError as error:
            raise ConcordStorageConflictError(
                f"Concord write lock already exists: {lock}"
            ) from error
        except OSError as error:
            raise ConcordStorageWriteError(
                f"could not durably acquire Concord write lock {lock}: {error}"
            ) from error
        marker_exists = work_marker_path(status.root, work).exists()
        current_exists = current_snapshot_path(status.root, work).exists()
        if marker_exists != current_exists:
            raise ConcordStorageIntegrityError(
                "marker/current presence is contradictory."
            )
        if current_exists:
            loaded = load_current_record_graph(
                status.root, work, standards_library=standards_library
            )
            current_revision = loaded.snapshot_revision
            current_snapshot, _ = load_work_snapshot(
                status.root, work, current_revision
            )
            _validate_canonical_write_history(
                status.root,
                work,
                current_snapshot,
            )
            if expected_snapshot_revision is None:
                existing = _records_by_identity(loaded.graph)
                if existing == candidate_map:
                    result = ConcordStorageCommitResult(
                        work, current_revision, loaded.snapshot_sha256, (), True
                    )
                    raise _CommitComplete
                raise ConcordStorageConflictError(
                    "initial commit requested for existing work."
                )
            if current_revision != expected_snapshot_revision:
                raise ConcordStorageConflictError(
                    f"expected snapshot {expected_snapshot_revision}, "
                    f"found {current_revision}."
                )
            selected = {
                (r.record_kind, r.record_id): r for r in current_snapshot.records
            }
            all_records = _records_by_identity(loaded.graph)
        else:
            if expected_snapshot_revision is not None:
                raise ConcordStorageConflictError(
                    "no current snapshot exists for expected revision."
                )
            _validate_canonical_write_history(status.root, work, None)
            current_revision = 0
            selected = {}
            all_records = {}
        all_records.update(candidate_map)
        graph = _graph_from_records(all_records.values())
        _validate_candidate(work, graph, standards_library)
        changed: list[tuple[tuple[str, str], Record, int]] = []
        for identity, record in sorted(candidate_map.items()):
            ref = selected.get(identity)
            if ref is not None:
                old, _ = load_record_revision(
                    status.root, work, *identity, ref.record_revision
                )
                if record_to_dict(old) == record_to_dict(record):
                    continue
                revision = ref.record_revision + 1
            else:
                revision = 1
            if record_revision_path(status.root, work, *identity, revision).exists():
                raise ConcordStorageIntegrityError(
                    "orphan/colliding record revision blocks commit: "
                    f"{identity[0]}:{identity[1]}:{revision}"
                )
            changed.append((identity, record, revision))
        if not changed and current_revision:
            current = load_current_snapshot(status.root, work)
            result = ConcordStorageCommitResult(
                work, current.snapshot_revision, current.snapshot_sha256, (), True
            )
            raise _CommitComplete
        state_path(status.root, work).mkdir(parents=True, exist_ok=True)
        if not marker_exists:
            marker = ConcordWorkMarker(
                CONCORD_STORAGE_SCHEMA_VERSION,
                "concord_work",
                work,
                work.work_id,
                CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
            )
            path = work_marker_path(status.root, work)
            _write_exclusive(path, serialize(marker))
            durable.append(str(path))
        new_refs = dict(selected)
        created: list[ConcordRecordRevisionRef] = []
        for identity, record, revision in changed:
            path = record_revision_path(status.root, work, *identity, revision)
            _require_no_symlink_ancestors(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            envelope = ConcordRecordRevision(
                CONCORD_STORAGE_SCHEMA_VERSION,
                "concord_record_revision",
                work,
                identity[0],
                identity[1],
                revision,
                CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
                cast(Any, record_to_dict(record)),
            )
            data = serialize(envelope)
            _write_exclusive(path, data)
            durable.append(str(path))
            persisted, persisted_envelope = load_record_revision(
                status.root, work, identity[0], identity[1], revision
            )
            if persisted != record or persisted_envelope != envelope:
                raise ConcordStorageIntegrityError(
                    "newly written record revision failed exact verification."
                )
            ref = ConcordRecordRevisionRef(
                identity[0], identity[1], revision, _sha(data)
            )
            new_refs[identity] = ref
            created.append(ref)
        next_revision = current_revision + 1
        if snapshot_path(status.root, work, next_revision).exists():
            raise ConcordStorageIntegrityError(
                "orphan/colliding snapshot blocks commit."
            )
        previous_digest = None
        if current_revision:
            _, previous_digest = load_work_snapshot(status.root, work, current_revision)
        snapshot = ConcordWorkSnapshot(
            CONCORD_STORAGE_SCHEMA_VERSION,
            "concord_work_snapshot",
            work,
            next_revision,
            current_revision or None,
            previous_digest,
            tuple(
                sorted(new_refs.values(), key=lambda r: (r.record_kind, r.record_id))
            ),
        )
        snapshot_data = serialize(snapshot)
        _require_no_symlink_ancestors(snapshot_path(status.root, work, next_revision))
        snapshot_path(status.root, work, next_revision).parent.mkdir(
            parents=True, exist_ok=True
        )
        _write_exclusive(snapshot_path(status.root, work, next_revision), snapshot_data)
        durable.append(str(snapshot_path(status.root, work, next_revision)))
        verified_snapshot, verified_digest = load_work_snapshot(
            status.root, work, next_revision
        )
        if verified_snapshot != snapshot or verified_digest != _sha(snapshot_data):
            raise ConcordStorageIntegrityError(
                "newly written snapshot failed exact verification."
            )
        pointer = ConcordCurrentSnapshot(
            CONCORD_STORAGE_SCHEMA_VERSION,
            "concord_current_snapshot",
            work,
            next_revision,
            _sha(snapshot_data),
        )
        current_path = current_snapshot_path(status.root, work)
        _publish(current_path, serialize(pointer))
        pointer_published = True
        published_snapshot_revision = next_revision
        published_snapshot_sha256 = pointer.snapshot_sha256
        durable.append(str(current_path))
        _fsync_directory_if_supported(current_path.parent)
        verified = load_current_record_graph(
            status.root, work, standards_library=standards_library
        )
        if _records_by_identity(verified.graph) != _records_by_identity(graph):
            raise ConcordStorageIntegrityError(
                "published graph differs from validated candidate."
            )
        result = ConcordStorageCommitResult(
            work, next_revision, pointer.snapshot_sha256, tuple(created)
        )
    except _CommitComplete:
        pass
    except Exception as error:
        operation_error = error

    if acquired:
        try:
            lock.unlink()
            _fsync_directory_if_supported(lock.parent)
        except OSError as error:
            lock_cleanup_error = error

    reported_paths = list(durable)
    if isinstance(operation_error, ConcordStoragePartialSuccessError):
        reported_paths.extend(operation_error.durable_paths)
    if lock_cleanup_error is not None:
        reported_paths.append(str(lock))
    unique_paths = tuple(dict.fromkeys(reported_paths))

    if operation_error is not None:
        if pointer_published:
            raise ConcordStoragePartialSuccessError(
                "canonical current state was published, but final verification failed.",
                durable_paths=unique_paths,
                pointer_published=True,
                snapshot_revision=published_snapshot_revision,
                snapshot_sha256=published_snapshot_sha256,
            ) from operation_error
        if unique_paths:
            message = (
                str(operation_error)
                if isinstance(operation_error, ConcordStoragePartialSuccessError)
                else "commit stopped after canonical files may have become durable; "
                "current pointer was not advanced."
            )
            raise ConcordStoragePartialSuccessError(
                message,
                durable_paths=unique_paths,
                pointer_published=False,
                snapshot_revision=None,
                snapshot_sha256=None,
            ) from operation_error
        raise operation_error

    if lock_cleanup_error is not None:
        raise ConcordStoragePartialSuccessError(
            "storage operation succeeded, but write.lock could not be removed.",
            durable_paths=unique_paths,
            pointer_published=pointer_published,
            snapshot_revision=published_snapshot_revision,
            snapshot_sha256=published_snapshot_sha256,
        ) from lock_cleanup_error

    if result is None:
        raise ConcordStorageWriteError("storage operation produced no result.")
    return result
