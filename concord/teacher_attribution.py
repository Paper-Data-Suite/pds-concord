"""Concord-only, guarded teacher attribution preference (issue #148).

This preference supplies *self-declared provenance* to Concord. It is not
Core private Notes ownership, authentication, a role grant, or a shared PDS
profile. No user configuration is created by importing, reading or resolving.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import unicodedata
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, cast

from pds_core.identifiers import validate_identifier
from pds_core.workspace import get_workspace_config_path

if TYPE_CHECKING:
    from concord.workflows import WorkflowActor

SCHEMA_VERSION: Final = 1
MAX_PROFILE_BYTES: Final = 4096
_PROFILE_FILENAME: Final = "teacher-attribution-v1.json"
_LOCK_FILENAME: Final = ".teacher-attribution-v1.lock"


class TeacherAttributionError(Exception):
    """Base error for Concord's local convenience preference."""


class TeacherAttributionValidationError(TeacherAttributionError):
    """A preference or requested actor value is malformed or unsupported."""


class TeacherAttributionStorageError(TeacherAttributionError):
    """A private local preference cannot be safely accessed or persisted."""


class TeacherAttributionConflictError(TeacherAttributionError):
    """Another process changed the reviewed preference."""


class TeacherAttributionNotConfiguredError(TeacherAttributionError):
    """The teacher has not explicitly configured a Concord preference."""


def _name(value: object) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise TeacherAttributionValidationError("Teacher display name is required.")
    if len(value) > 160 or unicodedata.normalize("NFC", value) != value:
        raise TeacherAttributionValidationError(
            "Teacher display name must have at most 160 normalized characters."
        )
    if any(unicodedata.category(ch).startswith("C") for ch in value):
        raise TeacherAttributionValidationError(
            "Teacher display name contains a control or format character."
        )
    if any(ch in "/\\" for ch in value):
        raise TeacherAttributionValidationError(
            "Teacher display name cannot contain path separators."
        )
    return value


def _actor_id(value: object) -> str:
    if not isinstance(value, str) or len(value) > 128:
        raise TeacherAttributionValidationError(
            "Teacher actor ID must be a bounded Core-safe identifier."
        )
    try:
        return validate_identifier(value, "teacher actor ID")
    except (TypeError, ValueError) as error:
        raise TeacherAttributionValidationError(
            "Teacher actor ID must be a bounded Core-safe identifier."
        ) from error


def _utc(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.endswith("+00:00"):
        raise TeacherAttributionValidationError(f"{field} must be canonical UTC.")
    try:
        when = datetime.fromisoformat(value)
    except ValueError as error:
        raise TeacherAttributionValidationError(f"{field} is invalid.") from error
    offset = when.utcoffset()
    if when.tzinfo is None or offset is None:
        raise TeacherAttributionValidationError(f"{field} must be UTC.")
    if offset.total_seconds() != 0 or when.isoformat() != value:
        raise TeacherAttributionValidationError(f"{field} must be canonical UTC.")
    return value


def _now(clock: Callable[[], datetime]) -> str:
    result = clock()
    if not isinstance(result, datetime) or result.tzinfo is None:
        raise TeacherAttributionValidationError("Clock must be timezone-aware.")
    return result.astimezone(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class TeacherAttributionProfile:
    """One versioned, self-declared and non-authorizing actor preference."""

    revision: int
    actor_id: str
    display_name: str
    created_at: str
    updated_at: str
    schema_version: int = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version != SCHEMA_VERSION
        ):
            raise TeacherAttributionValidationError("Unsupported profile schema.")
        if type(self.revision) is not int or not 1 <= self.revision <= 1_000_000:
            raise TeacherAttributionValidationError("Invalid profile revision.")
        _actor_id(self.actor_id)
        _name(self.display_name)
        created = _utc(self.created_at, "created_at")
        updated = _utc(self.updated_at, "updated_at")
        if datetime.fromisoformat(updated) < datetime.fromisoformat(created):
            raise TeacherAttributionValidationError("Profile timestamps are reversed.")


@dataclass(frozen=True, slots=True)
class StoredTeacherAttribution:
    """Reviewed profile with its precise encoded-byte fingerprint."""

    profile: TeacherAttributionProfile
    sha256: str


@dataclass(frozen=True, slots=True)
class TeacherAttributionIdentity:
    """Validated actor values to use as native Concord provenance."""

    actor_id: str
    display_name: str
    source: Literal["saved", "temporary"]

    def __post_init__(self) -> None:
        _actor_id(self.actor_id)
        _name(self.display_name)
        if self.source not in ("saved", "temporary"):
            raise TeacherAttributionValidationError("Unsupported attribution source.")

    def workflow_actor(self) -> WorkflowActor:
        """Preserve historical WorkflowActor semantics and readable snapshot."""
        from concord.workflows import WorkflowActor

        return WorkflowActor(actor_id=self.actor_id, display_label=self.display_name)


def _pairs(values: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in values:
        if key in result:
            raise TeacherAttributionValidationError("Duplicate profile JSON field.")
        result[key] = value
    return result


def _encode(profile: TeacherAttributionProfile) -> bytes:
    payload = {
        "schema_version": profile.schema_version,
        "revision": profile.revision,
        "actor_id": profile.actor_id,
        "display_name": profile.display_name,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2)
    return (serialized + "\n").encode("utf-8")


def _decode(raw: bytes) -> TeacherAttributionProfile:
    if not 0 < len(raw) <= MAX_PROFILE_BYTES:
        raise TeacherAttributionValidationError("Profile exceeds its size limit.")
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs)
    except (UnicodeError, ValueError, TypeError) as error:
        raise TeacherAttributionValidationError("Profile JSON is invalid.") from error
    required = {
        "schema_version",
        "revision",
        "actor_id",
        "display_name",
        "created_at",
        "updated_at",
    }
    if not isinstance(data, dict) or set(data) != required:
        raise TeacherAttributionValidationError(
            "Profile fields do not match schema v1."
        )
    return TeacherAttributionProfile(
        revision=data["revision"],
        actor_id=data["actor_id"],
        display_name=data["display_name"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        schema_version=data["schema_version"],
    )


def _unsafe_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & reparse
    )


def _check_directory(path: Path) -> None:
    if _unsafe_link(path):
        raise TeacherAttributionStorageError("Local profile directory is a link.")
    try:
        info = path.lstat()
    except OSError as error:
        raise TeacherAttributionStorageError(
            "Cannot inspect local profile directory."
        ) from error
    if not stat.S_ISDIR(info.st_mode):
        raise TeacherAttributionStorageError(
            "Local profile directory is not a directory."
        )
    if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
        raise TeacherAttributionStorageError("Local profile directory is not private.")


def _read_file(path: Path) -> bytes | None:
    if _unsafe_link(path):
        raise TeacherAttributionStorageError("Local profile path is a link.")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None
    except OSError as error:
        raise TeacherAttributionStorageError(
            "Cannot safely read local profile."
        ) from error
    try:
        info = os.fstat(fd)
        try:
            seen = path.lstat()
        except OSError as error:
            raise TeacherAttributionStorageError(
                "Local profile changed during read."
            ) from error
        if _unsafe_link(path) or (info.st_dev, info.st_ino) != (
            seen.st_dev,
            seen.st_ino,
        ):
            raise TeacherAttributionStorageError("Local profile changed during read.")
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise TeacherAttributionStorageError(
                "Local profile must be a regular file."
            )
        if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
            raise TeacherAttributionStorageError("Local profile file is not private.")
        data = bytearray()
        while len(data) <= MAX_PROFILE_BYTES:
            chunk = os.read(fd, MAX_PROFILE_BYTES + 1 - len(data))
            if not chunk:
                return bytes(data)
            data.extend(chunk)
        raise TeacherAttributionValidationError("Profile exceeds its size limit.")
    finally:
        os.close(fd)


def _flush_dir(path: Path) -> None:
    if os.name == "nt":
        return  # Windows file flush/replace; directory fsync is unsupported.
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _file_lock(fd: int, *, unlock: bool) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        operation = cast(int, getattr(msvcrt, "LK_UNLCK" if unlock else "LK_LOCK"))
        cast(Callable[[int, int, int], None], getattr(msvcrt, "locking"))(
            fd, operation, 1
        )
    else:
        import fcntl

        operation = cast(int, getattr(fcntl, "LOCK_UN" if unlock else "LOCK_EX"))
        cast(Callable[[int, int], None], getattr(fcntl, "flock"))(fd, operation)


class ConcordTeacherAttributionStore:
    """Guarded Concord-local profile beneath Core's per-user config root.

    The scoped file belongs only to the current local user/Concord installation.
    A shared OS login is NOT a multi-teacher security boundary.
    """

    def __init__(
        self,
        *,
        config_directory: Path | None = None,
        clock: Callable[[], datetime] | None = None,
        actor_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._config_directory = config_directory
        self._clock = clock or (lambda: datetime.now(UTC))
        self._actor_id_factory = actor_id_factory or (
            lambda: "teacher-" + uuid.uuid4().hex
        )

    @property
    def directory(self) -> Path:
        try:
            root = (
                get_workspace_config_path().parent
                if self._config_directory is None
                else self._config_directory
            )
        except (OSError, ValueError) as error:
            raise TeacherAttributionStorageError(
                "Cannot resolve local config root."
            ) from error
        if not isinstance(root, Path) or not root.is_absolute() or ".." in root.parts:
            raise TeacherAttributionStorageError("Local config root must be absolute.")
        return root / "concord"

    @property
    def profile_path(self) -> Path:
        return self.directory / _PROFILE_FILENAME

    def _guard_directory(self, *, create: bool) -> bool:
        parent = self.directory.parent
        try:
            if _unsafe_link(parent):
                raise TeacherAttributionStorageError("Core config root is a link.")
            if not parent.exists():
                if not create:
                    return False
                parent.mkdir(parents=True, exist_ok=True)
            if _unsafe_link(parent) or not parent.is_dir():
                raise TeacherAttributionStorageError("Core config root is not safe.")
            own_dir = self.directory
            if not own_dir.exists():
                if _unsafe_link(own_dir):
                    raise TeacherAttributionStorageError("Profile directory is a link.")
                if not create:
                    return False
                own_dir.mkdir(mode=0o700, exist_ok=True)
            _check_directory(own_dir)
            return True
        except TeacherAttributionError:
            raise
        except OSError as error:
            raise TeacherAttributionStorageError(
                "Cannot access local config directory."
            ) from error

    def load(self) -> StoredTeacherAttribution | None:
        """Read only. Never mkdir, repair, create a lock or overwrite anything."""
        try:
            if not self._guard_directory(create=False):
                return None
            raw = _read_file(self.profile_path)
        except TeacherAttributionError:
            raise
        except OSError as error:
            raise TeacherAttributionStorageError("Cannot inspect profile.") from error
        if raw is None:
            return None
        profile = _decode(raw)
        return StoredTeacherAttribution(
            profile=profile, sha256=hashlib.sha256(raw).hexdigest()
        )

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self._guard_directory(create=True)
        path = self.directory / _LOCK_FILENAME
        if _unsafe_link(path):
            raise TeacherAttributionStorageError("Profile lock is a link.")
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags, 0o600)
        except OSError as error:
            raise TeacherAttributionStorageError("Cannot open profile lock.") from error
        try:
            info = os.fstat(fd)
            seen = path.lstat()
            if _unsafe_link(path) or (info.st_dev, info.st_ino) != (
                seen.st_dev,
                seen.st_ino,
            ):
                raise TeacherAttributionStorageError("Profile lock changed.")
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise TeacherAttributionStorageError(
                    "Profile lock is not a regular file."
                )
            if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
                raise TeacherAttributionStorageError("Profile lock is not private.")
            if os.name == "nt" and info.st_size == 0:
                os.write(fd, b"0")
                os.fsync(fd)
            _file_lock(fd, unlock=False)
            try:
                self._guard_directory(create=False)
                yield
            finally:
                _file_lock(fd, unlock=True)
        except TeacherAttributionError:
            raise
        except OSError as error:
            raise TeacherAttributionStorageError(
                "Cannot lock local profile."
            ) from error
        finally:
            os.close(fd)

    def _save(self, profile: TeacherAttributionProfile) -> StoredTeacherAttribution:
        raw = _encode(profile)
        if len(raw) > MAX_PROFILE_BYTES:
            raise TeacherAttributionValidationError("Profile exceeds its size limit.")
        path = self.profile_path
        if _unsafe_link(path):
            raise TeacherAttributionStorageError("Refusing a profile link.")
        temporary: Path | None = None
        try:
            fd, name = tempfile.mkstemp(
                prefix=".teacher-attribution-", suffix=".tmp", dir=self.directory
            )
            temporary = Path(name)
            with os.fdopen(fd, "wb") as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            if _unsafe_link(path):
                raise TeacherAttributionStorageError("Profile path became a link.")
            os.replace(temporary, path)
            temporary = None
            _flush_dir(self.directory)
        except TeacherAttributionError:
            raise
        except OSError as error:
            raise TeacherAttributionStorageError(
                "Local profile could not be saved."
            ) from error
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return StoredTeacherAttribution(profile, hashlib.sha256(raw).hexdigest())

    def _expected(
        self, expected: StoredTeacherAttribution
    ) -> TeacherAttributionProfile:
        if not isinstance(expected, StoredTeacherAttribution):
            raise TeacherAttributionValidationError(
                "Exact reviewed profile is required."
            )
        current = self.load()
        if current is None or (
            current.profile.revision != expected.profile.revision
            or current.sha256 != expected.sha256
        ):
            raise TeacherAttributionConflictError(
                "Profile changed; refresh before editing."
            )
        return current.profile

    def create(
        self, display_name: str, *, actor_id: str | None = None
    ) -> StoredTeacherAttribution:
        """Explicit confirmed first-use write, with stable ID generation if needed."""
        name = _name(display_name)
        actor = _actor_id(
            actor_id if actor_id is not None else self._actor_id_factory()
        )
        with self._locked():
            if self.load() is not None:
                raise TeacherAttributionConflictError("Profile already configured.")
            stamp = _now(self._clock)
            return self._save(TeacherAttributionProfile(1, actor, name, stamp, stamp))

    def update_display_name(
        self, expected: StoredTeacherAttribution, display_name: str
    ) -> StoredTeacherAttribution:
        name = _name(display_name)
        with self._locked():
            previous = self._expected(expected)
            if previous.display_name == name:
                return expected  # a true no-op, no revision or write
            return self._save(
                TeacherAttributionProfile(
                    previous.revision + 1,
                    previous.actor_id,
                    name,
                    previous.created_at,
                    _now(self._clock),
                )
            )

    def replace_identity(
        self,
        expected: StoredTeacherAttribution,
        *,
        display_name: str,
        actor_id: str | None = None,
        confirmed: bool = False,
    ) -> StoredTeacherAttribution:
        if not confirmed:
            raise TeacherAttributionValidationError(
                "Actor ID replacement requires explicit confirmation."
            )
        name = _name(display_name)
        actor = _actor_id(
            actor_id if actor_id is not None else self._actor_id_factory()
        )
        with self._locked():
            previous = self._expected(expected)
            if previous.actor_id == actor:
                raise TeacherAttributionValidationError(
                    "Replacement actor ID is unchanged."
                )
            return self._save(
                TeacherAttributionProfile(
                    previous.revision + 1,
                    actor,
                    name,
                    previous.created_at,
                    _now(self._clock),
                )
            )

    def reset(
        self, expected: StoredTeacherAttribution, *, confirmed: bool = False
    ) -> None:
        if not confirmed:
            raise TeacherAttributionValidationError(
                "Reset requires explicit confirmation."
            )
        with self._locked():
            self._expected(expected)
            try:
                self.profile_path.unlink()
                _flush_dir(self.directory)
            except OSError as error:
                raise TeacherAttributionStorageError(
                    "Could not reset local profile."
                ) from error


class ConcordTeacherAttributionProvider:
    """Injectable, read-only actor provider; never a permission mechanism."""

    def __init__(self, store: ConcordTeacherAttributionStore) -> None:
        self._store = store

    @property
    def store(self) -> ConcordTeacherAttributionStore:
        return self._store

    def resolve_with_fingerprint(self) -> tuple[TeacherAttributionIdentity, str]:
        current = self._store.load()
        if current is None:
            raise TeacherAttributionNotConfiguredError(
                "Configure Concord teacher attribution in Settings before authoring."
            )
        return (
            TeacherAttributionIdentity(
                current.profile.actor_id, current.profile.display_name, "saved"
            ),
            current.sha256,
        )

    def resolve(self) -> TeacherAttributionIdentity:
        identity, _fingerprint = self.resolve_with_fingerprint()
        return identity

    def resolve_actor(self) -> WorkflowActor:
        return self.resolve().workflow_actor()

    @staticmethod
    def temporary_override(
        *, actor_id: str, display_name: str
    ) -> TeacherAttributionIdentity:
        """Validate an alternative identity, but never persist or queue it."""
        return TeacherAttributionIdentity(actor_id, display_name, "temporary")


__all__ = [
    "SCHEMA_VERSION",
    "MAX_PROFILE_BYTES",
    "TeacherAttributionError",
    "TeacherAttributionValidationError",
    "TeacherAttributionStorageError",
    "TeacherAttributionConflictError",
    "TeacherAttributionNotConfiguredError",
    "TeacherAttributionProfile",
    "StoredTeacherAttribution",
    "TeacherAttributionIdentity",
    "ConcordTeacherAttributionStore",
    "ConcordTeacherAttributionProvider",
]
