"""Immutable, integrity-checked class-scoped saved grouping storage (#136).

No Activity operational records are read or written by this module.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, cast

from pds_core.identifiers import validate_identifier
from pds_core.workspace import resolve_workspace_root

from concord.class_group_arrangements import (
    ARRANGEMENT_SCHEMA,
    ArrangementRosterComparison,
    SavedArrangementGroup,
    SavedArrangementRevision,
    compare_roster,
)
from concord.workflows.context import require_core_class
from concord.workflows.participants import load_required_roster


class ArrangementStorageError(RuntimeError):
    """Base storage failure."""


class ArrangementIntegrityError(ArrangementStorageError):
    """Stored data or storage path cannot be trusted."""


class ArrangementConflictError(ArrangementStorageError):
    """Revision, ownership or lock conflict."""


class ArrangementNotFoundError(ArrangementStorageError):
    """No complete saved grouping with the requested exact identity."""


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedArrangement:
    revision: SavedArrangementRevision
    sha256: str


def _canonical(data: Mapping[str, object]) -> bytes:
    rendered = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return (rendered + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _group_to_dict(group: SavedArrangementGroup) -> dict[str, object]:
    return {
        "key": group.key,
        "label": group.label,
        "description": group.description,
        "student_ids": list(group.student_ids),
    }


def _revision_to_dict(revision: SavedArrangementRevision) -> dict[str, object]:
    return {
        "schema": ARRANGEMENT_SCHEMA,
        "arrangement_id": revision.arrangement_id,
        "class_id": revision.class_id,
        "school_year": revision.school_year,
        "revision": revision.revision,
        "name": revision.name,
        "owner_actor_id": revision.owner_actor_id,
        "created_by_actor_id": revision.created_by_actor_id,
        "created_at": revision.created_at,
        "status": revision.status,
        "predecessor_sha256": revision.predecessor_sha256,
        "groups": [_group_to_dict(group) for group in revision.groups],
        "roster_student_ids": list(revision.roster_student_ids),
        "unresolved_student_ids": list(revision.unresolved_student_ids),
    }


def _exact(data: object, keys: set[str]) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != keys:
        raise ArrangementIntegrityError(
            "Saved grouping document has an invalid schema."
        )
    return cast(dict[str, Any], data)


REVISION_KEYS = frozenset(
    {
        "schema",
        "arrangement_id",
        "class_id",
        "school_year",
        "revision",
        "name",
        "owner_actor_id",
        "created_by_actor_id",
        "created_at",
        "status",
        "predecessor_sha256",
        "groups",
        "roster_student_ids",
        "unresolved_student_ids",
    }
)


def _revision_from_bytes(raw: bytes) -> SavedArrangementRevision:
    try:
        data = _exact(json.loads(raw.decode("utf-8")), set(REVISION_KEYS))
        if data["schema"] != ARRANGEMENT_SCHEMA:
            raise ArrangementIntegrityError("Unsupported grouping schema.")
        groups_raw = data["groups"]
        if not isinstance(groups_raw, list):
            raise ArrangementIntegrityError("Saved groups must be an array.")
        groups = []
        for g in groups_raw:
            obj = _exact(g, {"key", "label", "description", "student_ids"})
            if not isinstance(obj["student_ids"], list):
                raise ArrangementIntegrityError("Group member IDs must be an array.")
            groups.append(
                SavedArrangementGroup(
                    key=obj["key"],
                    label=obj["label"],
                    description=obj["description"],
                    student_ids=tuple(obj["student_ids"]),
                )
            )
        if not isinstance(data["roster_student_ids"], list) or not isinstance(
            data["unresolved_student_ids"], list
        ):
            raise ArrangementIntegrityError("Roster and unresolved IDs must be arrays.")
        result = SavedArrangementRevision(
            arrangement_id=data["arrangement_id"],
            class_id=data["class_id"],
            school_year=data["school_year"],
            revision=data["revision"],
            name=data["name"],
            owner_actor_id=data["owner_actor_id"],
            created_by_actor_id=data["created_by_actor_id"],
            created_at=data["created_at"],
            groups=tuple(groups),
            roster_student_ids=tuple(data["roster_student_ids"]),
            unresolved_student_ids=tuple(data["unresolved_student_ids"]),
            status=data["status"],
            predecessor_sha256=data["predecessor_sha256"],
        )
        if _canonical(_revision_to_dict(result)) != raw:
            raise ArrangementIntegrityError("Saved grouping revision is noncanonical.")
        return result
    except (UnicodeError, ValueError, TypeError, KeyError) as exc:
        raise ArrangementIntegrityError(
            "Saved grouping revision failed validation."
        ) from exc


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _path_guard(root: Path, target: Path) -> None:
    try:
        relative = target.relative_to(root)
    except ValueError as exc:
        raise ArrangementIntegrityError("Grouping path escapes the workspace.") from exc
    if _is_reparse(root):
        raise ArrangementIntegrityError("Workspace root is a link or reparse point.")
    current = root
    for component in relative.parts:
        current = current / component
        if _is_reparse(current):
            raise ArrangementIntegrityError(
                "Grouping path contains a link or reparse point."
            )


def _collection(root: Path, school_year: str, class_id: str) -> Path:
    return (
        root
        / "shared"
        / "concord"
        / "class-group-arrangements"
        / school_year
        / class_id
    )


def _directory(
    root: Path, school_year: str, class_id: str, arrangement_id: str
) -> Path:
    return _collection(root, school_year, class_id) / arrangement_id


def _root(workspace_root: str | Path, class_id: str, school_year: str) -> Path:
    root = resolve_workspace_root(workspace_root)
    metadata = require_core_class(root, class_id)
    if metadata.school_year != school_year:
        raise ArrangementConflictError(
            "Saved grouping school year does not match the Core class."
        )
    return root


def _read(root: Path, path: Path) -> bytes:
    _path_guard(root, path)
    if not path.is_file():
        raise ArrangementNotFoundError("Saved grouping state is missing.")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ArrangementStorageError("Unable to read saved grouping.") from exc


def _revision_path(directory: Path, revision: int) -> Path:
    return directory / "revisions" / f"{revision:08d}.json"


def _pointer(revision: int, digest: str) -> bytes:
    return _canonical(
        {"schema": ARRANGEMENT_SCHEMA, "revision": revision, "sha256": digest}
    )


def _exclusive(root: Path, path: Path, data: bytes) -> None:
    _path_guard(root, path)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        with os.fdopen(os.open(path, flags, 0o600), "wb") as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
    except FileExistsError as exc:
        raise ArrangementConflictError(
            "Immutable grouping state already exists."
        ) from exc


def _publish(root: Path, path: Path, data: bytes) -> None:
    _path_guard(root, path)
    fd, name = tempfile.mkstemp(prefix=".current-", suffix=".tmp", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _path_guard(root, temp)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@contextmanager
def _locked(root: Path, directory: Path) -> Iterator[None]:
    lock = directory / ".write.lock"
    _exclusive(root, lock, b"concord arrangement write lock\n")
    try:
        yield
    finally:
        try:
            lock.unlink()
        except OSError as exc:
            raise ArrangementStorageError(
                "Grouping write lock requires recovery."
            ) from exc


def _load_unguarded(
    root: Path, directory: Path, *, expected_id: str
) -> LoadedArrangement:
    _path_guard(root, directory)
    if not directory.is_dir():
        raise ArrangementNotFoundError("Saved grouping not found.")
    try:
        marker = _exact(
            json.loads(_read(root, directory / "library.json").decode("utf-8")),
            {"schema", "class_id", "school_year", "arrangement_id", "owner_actor_id"},
        )
    except (UnicodeError, ValueError) as exc:
        raise ArrangementIntegrityError("Grouping marker is unreadable.") from exc
    if (
        marker["schema"] != ARRANGEMENT_SCHEMA
        or marker["arrangement_id"] != expected_id
    ):
        raise ArrangementIntegrityError("Grouping marker identity mismatch.")
    try:
        current = _exact(
            json.loads(_read(root, directory / "current.json").decode("utf-8")),
            {"schema", "revision", "sha256"},
        )
    except (UnicodeError, ValueError) as exc:
        raise ArrangementIntegrityError("Grouping pointer is unreadable.") from exc
    if (
        current["schema"] != ARRANGEMENT_SCHEMA
        or type(current["revision"]) is not int
        or current["revision"] < 1
        or not isinstance(current["sha256"], str)
        or len(current["sha256"]) != 64
    ):
        raise ArrangementIntegrityError("Invalid grouping current pointer.")
    expected_numbers = [f"{n:08d}.json" for n in range(1, current["revision"] + 1)]
    rev_dir = directory / "revisions"
    _path_guard(root, rev_dir)
    if (
        not rev_dir.is_dir()
        or sorted(x.name for x in rev_dir.iterdir()) != expected_numbers
    ):
        raise ArrangementIntegrityError(
            "Grouping revision history has missing or orphan files."
        )
    prior: str | None = None
    loaded: LoadedArrangement | None = None
    for number in range(1, current["revision"] + 1):
        raw = _read(root, _revision_path(directory, number))
        record = _revision_from_bytes(raw)
        if (
            record.arrangement_id != expected_id
            or record.class_id != marker["class_id"]
            or record.school_year != marker["school_year"]
            or record.owner_actor_id != marker["owner_actor_id"]
            or record.revision != number
            or record.predecessor_sha256 != prior
        ):
            raise ArrangementIntegrityError(
                "Grouping revision history or class scope is invalid."
            )
        prior = _sha(raw)
        loaded = LoadedArrangement(revision=record, sha256=prior)
    assert loaded is not None
    if current["sha256"] != loaded.sha256:
        raise ArrangementIntegrityError("Grouping current pointer digest mismatch.")
    permitted = {"library.json", "current.json", "revisions", ".write.lock"}
    if set(x.name for x in directory.iterdir()) - permitted:
        raise ArrangementIntegrityError("Unexpected grouping storage entries.")
    return loaded


def _load(
    root: Path,
    school_year: str,
    class_id: str,
    arrangement_id: str,
    actor_id: str,
) -> LoadedArrangement:
    try:
        validate_identifier(arrangement_id, "arrangement_id")
        validate_identifier(actor_id, "actor_id")
    except (TypeError, ValueError) as exc:
        raise ArrangementConflictError("Invalid saved grouping identity.") from exc
    directory = _directory(root, school_year, class_id, arrangement_id)
    result = _load_unguarded(root, directory, expected_id=arrangement_id)
    if (
        result.revision.class_id != class_id
        or result.revision.school_year != school_year
    ):
        raise ArrangementConflictError("Grouping belongs to another class or year.")
    if result.revision.owner_actor_id != actor_id:
        raise ArrangementConflictError("Grouping is restricted to its owning teacher.")
    return result


def load_current_arrangement(
    workspace_root: str | Path,
    *,
    class_id: str,
    school_year: str,
    arrangement_id: str,
    actor_id: str,
) -> LoadedArrangement:
    """Read and authenticate the complete immutable revision history."""
    root = _root(workspace_root, class_id, school_year)
    return _load(root, school_year, class_id, arrangement_id, actor_id)


def list_current_arrangements(
    workspace_root: str | Path,
    *,
    class_id: str,
    school_year: str,
    actor_id: str,
) -> tuple[LoadedArrangement, ...]:
    """List only the named teacher's saved groupings; never list member details."""
    root = _root(workspace_root, class_id, school_year)
    collection = _collection(root, school_year, class_id)
    _path_guard(root, collection)
    if not collection.exists():
        return ()
    if not collection.is_dir():
        raise ArrangementIntegrityError("Grouping collection is not a directory.")
    found = []
    for path in sorted(collection.iterdir()):
        _path_guard(root, path)
        if not path.is_dir():
            raise ArrangementIntegrityError("Unexpected grouping collection entry.")
        item = _load_unguarded(root, path, expected_id=path.name)
        if (
            item.revision.class_id != class_id
            or item.revision.school_year != school_year
        ):
            raise ArrangementIntegrityError("Saved grouping class scope changed.")
        if item.revision.owner_actor_id == actor_id:
            found.append(item)
    return tuple(
        sorted(
            found,
            key=lambda item: (
                item.revision.name.casefold(),
                item.revision.arrangement_id,
            ),
        )
    )


def create_arrangement(
    workspace_root: str | Path,
    revision: SavedArrangementRevision,
    *,
    actor_id: str,
) -> LoadedArrangement:
    """Create only after exact current Core-class roster validation."""
    if revision.revision != 1 or revision.status != "active":
        raise ArrangementConflictError("New grouping must start at active revision 1.")
    if actor_id != revision.owner_actor_id or actor_id != revision.created_by_actor_id:
        raise ArrangementConflictError("Only the owning teacher may create a grouping.")
    root = _root(workspace_root, revision.class_id, revision.school_year)
    roster = load_required_roster(root, revision.class_id)
    if set(revision.roster_student_ids) != {s.student_id for s in roster.students}:
        raise ArrangementConflictError(
            "Core roster changed; review grouping before saving."
        )
    directory = _directory(
        root, revision.school_year, revision.class_id, revision.arrangement_id
    )
    _path_guard(root, directory)
    collection = directory.parent
    collection.mkdir(parents=True, exist_ok=True, mode=0o700)
    _path_guard(root, collection)
    try:
        directory.mkdir(mode=0o700)
    except FileExistsError as exc:
        raise ArrangementConflictError(
            "Saved grouping already exists or requires recovery."
        ) from exc
    (directory / "revisions").mkdir(mode=0o700)
    marker = _canonical(
        {
            "schema": ARRANGEMENT_SCHEMA,
            "arrangement_id": revision.arrangement_id,
            "class_id": revision.class_id,
            "school_year": revision.school_year,
            "owner_actor_id": revision.owner_actor_id,
        }
    )
    raw = _canonical(_revision_to_dict(revision))
    _exclusive(root, directory / "library.json", marker)
    _exclusive(root, _revision_path(directory, 1), raw)
    _publish(root, directory / "current.json", _pointer(1, _sha(raw)))
    return _load(
        root,
        revision.school_year,
        revision.class_id,
        revision.arrangement_id,
        actor_id,
    )


def append_arrangement_revision(
    workspace_root: str | Path,
    revision: SavedArrangementRevision,
    *,
    actor_id: str,
    expected_revision: int,
    expected_sha256: str,
) -> LoadedArrangement:
    """Compare-and-swap successor append; old revisions remain intact."""
    if actor_id != revision.owner_actor_id or actor_id != revision.created_by_actor_id:
        raise ArrangementConflictError("Only the owning teacher may revise a grouping.")
    root = _root(workspace_root, revision.class_id, revision.school_year)
    directory = _directory(
        root, revision.school_year, revision.class_id, revision.arrangement_id
    )
    _path_guard(root, directory)
    # Verify ownership and existing integrity before creating even a lock file.
    _load(
        root,
        revision.school_year,
        revision.class_id,
        revision.arrangement_id,
        actor_id,
    )
    with _locked(root, directory):
        current = _load(
            root,
            revision.school_year,
            revision.class_id,
            revision.arrangement_id,
            actor_id,
        )
        if current.revision.status == "retired":
            raise ArrangementConflictError("Retired groupings cannot be revised.")
        if (
            current.revision.revision != expected_revision
            or current.sha256 != expected_sha256
        ):
            raise ArrangementConflictError(
                "Saved grouping changed; reload before revising."
            )
        if (
            revision.revision != expected_revision + 1
            or revision.predecessor_sha256 != current.sha256
        ):
            raise ArrangementConflictError(
                "Grouping successor revision is stale or invalid."
            )
        if (
            revision.owner_actor_id != current.revision.owner_actor_id
            or revision.class_id != current.revision.class_id
            or revision.school_year != current.revision.school_year
            or revision.arrangement_id != current.revision.arrangement_id
        ):
            raise ArrangementConflictError(
                "Grouping identity or class scope cannot change."
            )
        roster = load_required_roster(root, revision.class_id)
        if set(revision.roster_student_ids) != {s.student_id for s in roster.students}:
            raise ArrangementConflictError(
                "Core roster changed; review grouping before revision."
            )
        raw = _canonical(_revision_to_dict(revision))
        _exclusive(root, _revision_path(directory, revision.revision), raw)
        _publish(
            root,
            directory / "current.json",
            _pointer(revision.revision, _sha(raw)),
        )
    return _load(
        root,
        revision.school_year,
        revision.class_id,
        revision.arrangement_id,
        actor_id,
    )


def review_arrangement_roster(
    workspace_root: str | Path,
    *,
    class_id: str,
    school_year: str,
    arrangement_id: str,
    actor_id: str,
) -> tuple[LoadedArrangement, ArrangementRosterComparison]:
    """Inspect differences; never resolve by matching names or changing membership."""
    loaded = load_current_arrangement(
        workspace_root,
        class_id=class_id,
        school_year=school_year,
        arrangement_id=arrangement_id,
        actor_id=actor_id,
    )
    roster = load_required_roster(workspace_root, class_id)
    compared = compare_roster(
        loaded.revision,
        target_class_id=class_id,
        target_school_year=school_year,
        target_student_ids=tuple(s.student_id for s in roster.students),
    )
    return loaded, compared
