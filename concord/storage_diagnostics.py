"""Privacy-safe deterministic diagnostics for Concord storage."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pds_core.routing_models import ModuleWorkRef

from concord.storage import (
    list_record_identities,
    list_record_revisions,
    list_work_snapshots,
    load_current_record_graph,
    load_current_snapshot,
    read_canonical_bytes,
)
from concord.storage_catalog import _open_verified
from concord.storage_errors import (
    ConcordCatalogError,
    ConcordStorageError,
    ConcordStorageGraphIntegrityError,
    ConcordStorageIntegrityError,
    ConcordStorageNotFoundError,
    ConcordStorageReadError,
    ConcordStorageValidationError,
)
from concord.storage_paths import (
    catalog_lock_path,
    catalog_path,
    state_path,
    write_lock_path,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StorageIssue:
    code: str
    message: str
    severity: str = "error"
    work: ModuleWorkRef | None = None
    record_kind: str | None = None
    record_id: str | None = None
    record_revision: int | None = None
    snapshot_revision: int | None = None
    relative_path: str | None = None
    field_path: tuple[str | int, ...] = ()
    related_references: tuple[str, ...] = ()

    @property
    def sort_key(self) -> tuple[object, ...]:
        return (
            self.code,
            self.record_kind or "",
            self.record_id or "",
            self.record_revision or 0,
            self.snapshot_revision or 0,
            self.relative_path or "",
            tuple(str(part) for part in self.field_path),
        )


@dataclass(frozen=True, slots=True)
class LockObservation:
    path: Path
    present: bool
    byte_size: int | None
    sha256: str | None


def inspect_storage_locks(
    workspace_root: str | Path, work: ModuleWorkRef
) -> tuple[LockObservation, ...]:
    result = []
    for path in (
        write_lock_path(workspace_root, work),
        catalog_lock_path(workspace_root, work),
    ):
        if not path.exists() and not path.is_symlink():
            result.append(LockObservation(path, False, None, None))
            continue
        data = read_canonical_bytes(path)
        result.append(
            LockObservation(path, True, len(data), hashlib.sha256(data).hexdigest())
        )
    return tuple(result)


def inspect_catalog_status(workspace_root: str | Path, work: ModuleWorkRef) -> str:
    path = catalog_path(workspace_root, work)
    if not path.exists() and not path.is_symlink():
        return "missing"
    try:
        connection = _open_verified(workspace_root, work)
    except ConcordCatalogError as error:
        name = type(error).__name__.lower()
        return (
            "stale"
            if "source" in name
            else "incompatible"
            if "compatibility" in name
            else "corrupt"
        )
    connection.close()
    return "current"


def collect_storage_issues(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    *,
    standards_library: object | None = None,
) -> tuple[StorageIssue, ...]:
    issues: list[StorageIssue] = []
    try:
        loaded = load_current_record_graph(
            workspace_root, work, standards_library=standards_library
        )
        current = load_current_snapshot(workspace_root, work)
        snapshots = list_work_snapshots(workspace_root, work)
        selected_revisions: set[tuple[str, str, int]] = set()
        from concord.storage import load_work_snapshot

        for revision in snapshots:
            snapshot, _ = load_work_snapshot(workspace_root, work, revision)
            selected_revisions.update(
                (r.record_kind, r.record_id, r.record_revision)
                for r in snapshot.records
            )
        for kind, record_id in list_record_identities(workspace_root, work):
            revisions = list_record_revisions(workspace_root, work, kind, record_id)
            if revisions and revisions != tuple(range(1, max(revisions) + 1)):
                issues.append(
                    StorageIssue(
                        code="storage.record.revision_gap",
                        message="Record revision history has a gap.",
                        work=work,
                        record_kind=kind,
                        record_id=record_id,
                    )
                )
            for revision in revisions:
                if (kind, record_id, revision) not in selected_revisions:
                    issues.append(
                        StorageIssue(
                            code="storage.record.orphan_revision",
                            message=(
                                "Immutable record revision is not selected by any "
                                "snapshot."
                            ),
                            work=work,
                            record_kind=kind,
                            record_id=record_id,
                            record_revision=revision,
                        )
                    )
        for revision in snapshots:
            if revision > current.snapshot_revision:
                issues.append(
                    StorageIssue(
                        code="storage.snapshot.orphan",
                        message=(
                            "Immutable snapshot is not selected by the current chain."
                        ),
                        work=work,
                        snapshot_revision=revision,
                    )
                )
        if loaded.snapshot_revision != current.snapshot_revision:
            raise AssertionError
    except ConcordStorageGraphIntegrityError as error:
        for graph_issue in error.issues:
            issues.append(
                StorageIssue(
                    code=graph_issue.code,
                    message=graph_issue.message,
                    work=work,
                    record_kind=graph_issue.record_kind,
                    record_id=graph_issue.record_id,
                    field_path=graph_issue.field_path,
                    related_references=tuple(
                        f"{reference.record_kind}:{reference.record_id}"
                        for reference in graph_issue.related_references
                    ),
                )
            )
    except ConcordStorageNotFoundError:
        issues.append(
            StorageIssue(
                code="storage.current.missing",
                message="A required canonical storage object is missing.",
                work=work,
            )
        )
    except ConcordStorageReadError:
        issues.append(
            StorageIssue(
                code="storage.read.failed",
                message="Canonical Concord storage could not be read strictly.",
                work=work,
            )
        )
    except ConcordStorageIntegrityError:
        issues.append(
            StorageIssue(
                code="storage.integrity.invalid",
                message="Canonical Concord storage failed integrity validation.",
                work=work,
            )
        )
    except ConcordStorageValidationError as error:
        code = (
            "storage.standards_context.required"
            if "standards_library is required" in str(error)
            else "storage.validation.failed"
        )
        issues.append(
            StorageIssue(
                code=code,
                message="Canonical Concord storage validation could not complete.",
                work=work,
            )
        )
    except ConcordStorageError:
        issues.append(
            StorageIssue(
                code="storage.failed",
                message="Canonical Concord storage validation failed.",
                work=work,
            )
        )
    canonical_state = state_path(workspace_root, work)
    expected = {
        "work.json",
        "records",
        "snapshots",
        "current.json",
        "derived",
        ".locks",
    }
    try:
        for entry in canonical_state.iterdir():
            if entry.name in expected:
                continue
            issues.append(
                StorageIssue(
                    code="storage.path.unexpected_entry",
                    message="Storage-owned state contains an unexpected entry.",
                    work=work,
                    relative_path=entry.name,
                )
            )
    except FileNotFoundError:
        pass
    for observation in inspect_storage_locks(workspace_root, work):
        if observation.present:
            issues.append(
                StorageIssue(
                    code="storage.lock.present",
                    message=(
                        "A storage lock is present; age alone does not authorize "
                        "removal."
                    ),
                    severity="warning",
                    work=work,
                    relative_path=observation.path.name,
                )
            )
    status = inspect_catalog_status(workspace_root, work)
    if status != "current":
        issues.append(
            StorageIssue(
                code=f"storage.catalog.{status}",
                message=f"Derived catalog status is {status}.",
                severity="warning",
                work=work,
            )
        )
    return tuple(sorted(issues, key=lambda issue: issue.sort_key))


def validate_storage(
    workspace_root: str | Path,
    work: ModuleWorkRef,
    *,
    standards_library: object | None = None,
) -> None:
    issues = tuple(
        issue
        for issue in collect_storage_issues(
            workspace_root, work, standards_library=standards_library
        )
        if issue.severity == "error"
    )
    if issues:
        raise ConcordStorageError(
            f"Concord storage has {len(issues)} integrity issue(s)."
        )
