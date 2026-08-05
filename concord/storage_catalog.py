"""Disposable per-Activity SQLite catalog rebuilt from canonical JSON."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from pds_core.routing_models import ModuleWorkRef, module_work_ref_to_dict

from concord.storage import (
    _fsync_directory_if_supported,
    list_record_identities,
    list_record_revisions,
    list_work_snapshots,
    load_current_snapshot,
    load_record_revision,
    load_work_marker,
    load_work_snapshot,
    read_canonical_bytes,
    require_regular_nonsymlink_file,
)
from concord.storage_errors import (
    ConcordCatalogBuildError,
    ConcordCatalogCompatibilityError,
    ConcordCatalogConflictError,
    ConcordCatalogIntegrityError,
    ConcordCatalogNotFoundError,
    ConcordCatalogSourceError,
    ConcordStorageError,
    ConcordStorageNotFoundError,
)
from concord.storage_models import CONCORD_CATALOG_SCHEMA_VERSION
from concord.storage_paths import catalog_lock_path, catalog_path
from concord.storage_serialization import canonical_json_bytes

CATALOG_APPLICATION_ID = 0x434F4E43


@dataclass(frozen=True, slots=True)
class CatalogRecordRow:
    record_kind: str
    record_id: str
    record_revision: int
    sha256: str
    selected_snapshot_revision: int | None
    is_current: bool


def canonical_source_inventory(
    workspace_root: str | Path, work: ModuleWorkRef
) -> tuple[tuple[str, int, str], ...]:
    load_work_marker(workspace_root, work)
    load_current_snapshot(workspace_root, work)
    paths: list[Path] = []
    from concord.storage_paths import (
        current_snapshot_path,
        record_revision_path,
        snapshot_path,
        state_path,
        work_marker_path,
    )

    paths.append(work_marker_path(workspace_root, work))
    for kind, record_id in list_record_identities(workspace_root, work):
        for revision in list_record_revisions(workspace_root, work, kind, record_id):
            paths.append(
                record_revision_path(workspace_root, work, kind, record_id, revision)
            )
    for revision in list_work_snapshots(workspace_root, work):
        paths.append(snapshot_path(workspace_root, work, revision))
    paths.append(current_snapshot_path(workspace_root, work))
    base = state_path(workspace_root, work)
    result = []
    for path in paths:
        data = read_canonical_bytes(path, missing=True)
        result.append(
            (
                path.relative_to(base).as_posix(),
                len(data),
                hashlib.sha256(data).hexdigest(),
            )
        )
    return tuple(sorted(result))


def source_inventory_digest(inventory: tuple[tuple[str, int, str], ...]) -> str:
    digest = hashlib.sha256()
    for relative, size, sha in inventory:
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(size.to_bytes(8, "big"))
        digest.update(bytes.fromhex(sha))
    return digest.hexdigest()


def rebuild_catalog(workspace_root: str | Path, work: ModuleWorkRef) -> Path:
    target = catalog_path(workspace_root, work)
    for ancestor in (target, *target.parents):
        if ancestor.is_symlink():
            raise ConcordCatalogSourceError(
                f"catalog path traverses a symlink: {ancestor}"
            )
    target.parent.mkdir(parents=True, exist_ok=True)
    lock = catalog_lock_path(workspace_root, work)
    lock.parent.mkdir(parents=True, exist_ok=True)
    acquired = False
    installed = False
    temporary: Path | None = None
    result: Path | None = None
    operation_error: Exception | None = None
    lock_cleanup_error: OSError | None = None
    try:
        try:
            with lock.open("xb") as output:
                acquired = True
                output.write(
                    canonical_json_bytes(
                        {
                            "schema_version": "1",
                            "record_type": "concord_storage_lock",
                            "work": module_work_ref_to_dict(work),
                            "purpose": "catalog_rebuild",
                        }
                    )
                )
                output.flush()
                os.fsync(output.fileno())

            _fsync_directory_if_supported(lock.parent)
        except FileExistsError as error:
            raise ConcordCatalogConflictError(
                f"catalog lock already exists: {lock}"
            ) from error
        before = canonical_source_inventory(workspace_root, work)
        source_digest = source_inventory_digest(before)
        current = load_current_snapshot(workspace_root, work)
        selected: dict[tuple[str, str, int], list[int]] = {}
        digests: dict[tuple[str, str, int], str] = {}
        for snapshot_revision in list_work_snapshots(workspace_root, work):
            snapshot, _ = load_work_snapshot(workspace_root, work, snapshot_revision)
            for ref in snapshot.records:
                key = (ref.record_kind, ref.record_id, ref.record_revision)
                selected.setdefault(key, []).append(snapshot_revision)
                digests[key] = ref.sha256
        fd, name = tempfile.mkstemp(
            prefix=".catalog.sqlite.", suffix=".tmp", dir=target.parent
        )
        os.close(fd)
        temporary = Path(name)
        connection = sqlite3.connect(temporary)
        try:
            connection.executescript("""
                PRAGMA journal_mode=DELETE;
                PRAGMA application_id=1129270851;
                CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE record_revisions (
                    record_kind TEXT NOT NULL, record_id TEXT NOT NULL,
                    record_revision INTEGER NOT NULL, sha256 TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    PRIMARY KEY(record_kind, record_id, record_revision));
                CREATE TABLE snapshot_records (
                    snapshot_revision INTEGER NOT NULL, record_kind TEXT NOT NULL,
                    record_id TEXT NOT NULL, record_revision INTEGER NOT NULL,
                    is_current INTEGER NOT NULL,
                    PRIMARY KEY(snapshot_revision, record_kind, record_id));
                CREATE INDEX snapshot_records_identity
                    ON snapshot_records(record_kind, record_id, record_revision);
            """)
            identity_count = len(list_record_identities(workspace_root, work))
            revision_count = sum(
                len(list_record_revisions(workspace_root, work, kind, record_id))
                for kind, record_id in list_record_identities(workspace_root, work)
            )
            connection.executemany(
                "INSERT INTO metadata VALUES (?, ?)",
                (
                    ("schema_version", str(CONCORD_CATALOG_SCHEMA_VERSION)),
                    ("application_id", str(CATALOG_APPLICATION_ID)),
                    ("built_at_utc", datetime.now(timezone.utc).isoformat()),
                    ("work_module_id", work.module_id),
                    ("work_class_id", work.class_id),
                    ("work_id", work.work_id),
                    ("source_digest", source_digest),
                    ("source_file_count", str(len(before))),
                    ("current_snapshot_revision", str(current.snapshot_revision)),
                    ("current_snapshot_sha256", current.snapshot_sha256),
                    ("record_identity_count", str(identity_count)),
                    ("record_revision_count", str(revision_count)),
                    (
                        "snapshot_count",
                        str(len(list_work_snapshots(workspace_root, work))),
                    ),
                ),
            )
            for kind, record_id in list_record_identities(workspace_root, work):
                for revision in list_record_revisions(
                    workspace_root, work, kind, record_id
                ):
                    _, envelope = load_record_revision(
                        workspace_root, work, kind, record_id, revision
                    )
                    sha = digests.get((kind, record_id, revision))
                    if sha is None:
                        from concord.storage_serialization import serialize

                        sha = hashlib.sha256(serialize(envelope)).hexdigest()
                    connection.execute(
                        "INSERT INTO record_revisions VALUES (?, ?, ?, ?, ?)",
                        (
                            kind,
                            record_id,
                            revision,
                            sha,
                            (f"records/{kind}/{record_id}/revisions/{revision}.json"),
                        ),
                    )
            for key, snapshots in selected.items():
                for snapshot_revision in snapshots:
                    connection.execute(
                        "INSERT INTO snapshot_records VALUES (?, ?, ?, ?, ?)",
                        (
                            snapshot_revision,
                            *key,
                            int(snapshot_revision == current.snapshot_revision),
                        ),
                    )
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise ConcordCatalogIntegrityError(
                    "replacement catalog failed integrity_check."
                )
        finally:
            connection.close()
        after = canonical_source_inventory(workspace_root, work)
        if after != before:
            raise ConcordCatalogConflictError(
                "canonical source changed during catalog rebuild."
            )
        os.replace(temporary, target)
        installed = True
        temporary = None
        _open_verified(workspace_root, work).close()
        result = target
    except (ConcordCatalogConflictError, ConcordCatalogIntegrityError) as error:
        operation_error = error
    except Exception as error:
        operation_error = ConcordCatalogBuildError(f"catalog rebuild failed: {error}")

    if temporary is not None:
        try:
            temporary.unlink()
        except OSError as error:
            if operation_error is None:
                operation_error = ConcordCatalogBuildError(
                    "catalog rebuild failed and its temporary file remains."
                )
                operation_error.__cause__ = error

    if acquired:
        try:
            lock.unlink()
            _fsync_directory_if_supported(lock.parent)
        except OSError as error:
            lock_cleanup_error = error

    if lock_cleanup_error is not None:
        if installed:
            raise ConcordCatalogBuildError(
                "catalog was installed successfully, but catalog.lock could not "
                "be removed."
            ) from lock_cleanup_error
        raise ConcordCatalogBuildError(
            "catalog rebuild failed and catalog.lock could not be removed; the "
            "lock may remain."
        ) from lock_cleanup_error

    if operation_error is not None:
        raise operation_error
    if result is None:
        raise ConcordCatalogBuildError("catalog rebuild produced no result.")
    return result


def _open_verified(
    workspace_root: str | Path, work: ModuleWorkRef
) -> sqlite3.Connection:
    path = catalog_path(workspace_root, work)
    try:
        require_regular_nonsymlink_file(path, missing=True)
    except ConcordStorageNotFoundError as error:
        raise ConcordCatalogNotFoundError(f"catalog not found: {path}") from error
    except ConcordStorageError as error:
        raise ConcordCatalogIntegrityError(f"catalog path is unsafe: {path}") from error
    try:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if metadata.get("schema_version") != str(CONCORD_CATALOG_SCHEMA_VERSION):
            raise ConcordCatalogCompatibilityError(
                "catalog schema version is incompatible."
            )
        application_id = connection.execute("PRAGMA application_id").fetchone()
        if application_id != (CATALOG_APPLICATION_ID,):
            raise ConcordCatalogCompatibilityError(
                "catalog application identifier is incompatible."
            )
        expected_work = (work.module_id, work.class_id, work.work_id)
        actual_work = (
            metadata.get("work_module_id"),
            metadata.get("work_class_id"),
            metadata.get("work_id"),
        )
        if actual_work != expected_work:
            raise ConcordCatalogIntegrityError(
                "catalog work identity differs from its canonical path."
            )
        actual = source_inventory_digest(
            canonical_source_inventory(workspace_root, work)
        )
        if metadata.get("source_digest") != actual:
            raise ConcordCatalogSourceError(
                "catalog is stale relative to canonical storage."
            )
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ConcordCatalogIntegrityError("catalog is corrupt.")
        return connection
    except (
        ConcordCatalogCompatibilityError,
        ConcordCatalogSourceError,
        ConcordCatalogIntegrityError,
    ):
        try:
            connection.close()
        except UnboundLocalError:
            pass
        raise
    except sqlite3.Error as error:
        raise ConcordCatalogIntegrityError(f"catalog is corrupt: {error}") from error


def query_catalog_records(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    *,
    snapshot_revision: int | None = None,
    state: str = "all",
) -> tuple[CatalogRecordRow, ...]:
    if state not in {"all", "current", "historical"}:
        raise ValueError("state must be current, historical, or all.")
    if snapshot_revision is not None and state != "all":
        raise ValueError("state filtering cannot be combined with snapshot_revision.")
    connection = _open_verified(workspace_root, work)
    try:
        if snapshot_revision is None:
            current_clause = {
                "all": "",
                "current": "WHERE EXISTS (SELECT 1 FROM snapshot_records x "
                "WHERE x.record_kind=r.record_kind AND x.record_id=r.record_id "
                "AND x.record_revision=r.record_revision AND x.is_current=1)",
                "historical": "WHERE NOT EXISTS (SELECT 1 FROM snapshot_records x "
                "WHERE x.record_kind=r.record_kind AND x.record_id=r.record_id "
                "AND x.record_revision=r.record_revision AND x.is_current=1)",
            }[state]
            sql = f"""SELECT r.record_kind,r.record_id,r.record_revision,r.sha256,
                (SELECT MAX(x.snapshot_revision) FROM snapshot_records x
                 WHERE x.record_kind=r.record_kind AND x.record_id=r.record_id
                 AND x.record_revision=r.record_revision),
                EXISTS (SELECT 1 FROM snapshot_records x
                 WHERE x.record_kind=r.record_kind AND x.record_id=r.record_id
                 AND x.record_revision=r.record_revision AND x.is_current=1)
                FROM record_revisions r {current_clause} ORDER BY 1,2,3"""
            params: tuple[object, ...] = ()
        else:
            if type(snapshot_revision) is not int or snapshot_revision < 1:
                raise ValueError("snapshot_revision must be positive.")
            sql = """SELECT r.record_kind,r.record_id,r.record_revision,r.sha256,
                s.snapshot_revision,s.is_current FROM snapshot_records s
                JOIN record_revisions r USING(record_kind,record_id,record_revision)
                WHERE s.snapshot_revision=? ORDER BY 1,2,3"""
            params = (snapshot_revision,)
        return tuple(
            CatalogRecordRow(row[0], row[1], row[2], row[3], row[4], bool(row[5]))
            for row in connection.execute(sql, params)
        )
    finally:
        connection.close()
