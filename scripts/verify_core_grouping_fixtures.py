"""Authenticate Concord's vendored Core v0.6.1 grouping-signal fixtures."""

from __future__ import annotations

import argparse
import hashlib
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Final

ROOT = Path(__file__).resolve().parents[1]
VENDORED_FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "core_grouping_signals" / "v1"
EXPECTED_ARCHIVE_FILENAME: Final[str] = (
    "pds-core-0.6.1-grouping-signal-fixtures.zip"
)
EXPECTED_ARCHIVE_SHA256: Final[str] = (
    "d8376292dd68ada48d35ab98233381de0008d41f868844e27e8507bf0d0f8f8d"
)
ARCHIVE_PREFIX: Final[str] = "grouping_signals_v1"
EXPECTED_FILE_DIGESTS: Final[dict[str, str]] = {
    "classes/english10_p2/roster.csv": (
        "115254d2e7aec832d568b46fd75144eb045c2acb60e4c2d7d00b38437e12217a"
    ),
    "classes/english10_p4/roster.csv": (
        "90c75ec23683259468a3c49d6c8a49df911054de54aba6708adbe8faa7f7a596"
    ),
    "module_multi_dimension.json": (
        "6d739870ac5e198fd61c5f0c238c50de8cdef4c637e4b45aa11e2912fd9fa459"
    ),
    "module_selected_dimension_projection.csv": (
        "d18e00112e3279704887ee8544abd20bcbef1de614d82550fd964d9f7f11786a"
    ),
    "teacher_complete.csv": (
        "72650f3bd6432f2aa5323f79686249814af599d8cf68d38698dbeae021877d45"
    ),
    "teacher_complete.json": (
        "333fa9a8fb51c36379d365f51a62953c3cd98496b404fff22e3bbedacf3e605b"
    ),
}
_SHA256_RE: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")


class CoreGroupingFixtureVerificationError(RuntimeError):
    """Raised when Core grouping-signal fixture authentication fails."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _expected_manifest_bytes() -> bytes:
    lines = [
        f"{digest}  {path}\n"
        for path, digest in sorted(EXPECTED_FILE_DIGESTS.items())
    ]
    return "".join(lines).encode("ascii")


def _manifest_entries(raw: bytes) -> dict[str, str]:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise CoreGroupingFixtureVerificationError(
            "Fixture SHA256SUMS.txt must be ASCII."
        ) from error
    entries: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        try:
            digest, relative = line.split("  ", maxsplit=1)
        except ValueError as error:
            raise CoreGroupingFixtureVerificationError(
                f"Malformed fixture checksum line {line_number}."
            ) from error
        if not _SHA256_RE.fullmatch(digest):
            raise CoreGroupingFixtureVerificationError(
                f"Malformed fixture SHA-256 at line {line_number}."
            )
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise CoreGroupingFixtureVerificationError(
                f"Unsafe fixture path at line {line_number}."
            )
        normalized = path.as_posix()
        if normalized in entries:
            raise CoreGroupingFixtureVerificationError(
                f"Duplicate fixture path {normalized!r}."
            )
        entries[normalized] = digest
    return entries


def verify_vendored_grouping_fixtures(
    fixture_root: Path = VENDORED_FIXTURE_ROOT,
) -> None:
    """Authenticate the byte-exact fixture payload committed to Concord."""
    if not fixture_root.is_dir():
        raise CoreGroupingFixtureVerificationError(
            f"Vendored fixture directory is missing: {fixture_root}"
        )
    manifest_path = fixture_root / "SHA256SUMS.txt"
    if not manifest_path.is_file():
        raise CoreGroupingFixtureVerificationError(
            "Vendored grouping fixtures are missing SHA256SUMS.txt."
        )
    manifest_bytes = manifest_path.read_bytes()
    if manifest_bytes != _expected_manifest_bytes():
        raise CoreGroupingFixtureVerificationError(
            "Vendored SHA256SUMS.txt differs from the released Core v0.6.1 manifest."
        )
    entries = _manifest_entries(manifest_bytes)
    if entries != EXPECTED_FILE_DIGESTS:
        raise CoreGroupingFixtureVerificationError(
            "Vendored fixture manifest entries differ from the released baseline."
        )

    actual_files = {
        path.relative_to(fixture_root).as_posix()
        for path in fixture_root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    if actual_files != set(EXPECTED_FILE_DIGESTS):
        missing = sorted(set(EXPECTED_FILE_DIGESTS) - actual_files)
        extra = sorted(actual_files - set(EXPECTED_FILE_DIGESTS))
        raise CoreGroupingFixtureVerificationError(
            "Vendored fixture file set differs from the released baseline: "
            f"missing={missing}, extra={extra}."
        )

    for relative, expected_digest in EXPECTED_FILE_DIGESTS.items():
        raw = (fixture_root / relative).read_bytes()
        if b"\r" in raw:
            raise CoreGroupingFixtureVerificationError(
                f"Vendored fixture must retain LF-only bytes: {relative}."
            )
        actual_digest = _sha256(raw)
        if actual_digest != expected_digest:
            raise CoreGroupingFixtureVerificationError(
                f"Vendored fixture SHA-256 mismatch: {relative}."
            )


def verify_released_fixture_archive(path: Path) -> None:
    """Authenticate the exact released Core v0.6.1 fixture ZIP asset."""
    if path.name != EXPECTED_ARCHIVE_FILENAME:
        raise CoreGroupingFixtureVerificationError(
            f"Fixture archive must be named {EXPECTED_ARCHIVE_FILENAME}."
        )
    try:
        raw_archive = path.read_bytes()
    except OSError as error:
        raise CoreGroupingFixtureVerificationError(
            f"Could not read fixture archive: {path}."
        ) from error
    if _sha256(raw_archive) != EXPECTED_ARCHIVE_SHA256:
        raise CoreGroupingFixtureVerificationError(
            "Fixture archive SHA-256 does not match the released Core v0.6.1 asset."
        )

    expected_members = {
        f"{ARCHIVE_PREFIX}/{relative}" for relative in EXPECTED_FILE_DIGESTS
    } | {f"{ARCHIVE_PREFIX}/SHA256SUMS.txt"}
    try:
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise CoreGroupingFixtureVerificationError(
                    "Released grouping fixture ZIP contains a corrupt member."
                )
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != expected_members:
                raise CoreGroupingFixtureVerificationError(
                    "Released grouping fixture ZIP member set is unexpected."
                )
            manifest_member = f"{ARCHIVE_PREFIX}/SHA256SUMS.txt"
            manifest = archive.read(manifest_member)
            if manifest != _expected_manifest_bytes():
                raise CoreGroupingFixtureVerificationError(
                    "Released fixture ZIP manifest differs from the expected "
                    "v0.6.1 manifest."
                )
            for relative, expected_digest in EXPECTED_FILE_DIGESTS.items():
                raw = archive.read(f"{ARCHIVE_PREFIX}/{relative}")
                if _sha256(raw) != expected_digest:
                    raise CoreGroupingFixtureVerificationError(
                        f"Released fixture ZIP member SHA-256 mismatch: {relative}."
                    )
                vendored = (VENDORED_FIXTURE_ROOT / relative).read_bytes()
                if raw != vendored:
                    raise CoreGroupingFixtureVerificationError(
                        "Vendored fixture differs from released ZIP member: "
                        f"{relative}."
                    )
    except zipfile.BadZipFile as error:
        raise CoreGroupingFixtureVerificationError(
            "Released grouping fixture asset is not a readable ZIP archive."
        ) from error


def main() -> int:
    """Verify vendored fixtures and optionally an exact released fixture ZIP."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        verify_vendored_grouping_fixtures()
        if args.archive is not None:
            verify_released_fixture_archive(args.archive)
    except CoreGroupingFixtureVerificationError as error:
        print(f"Core grouping fixture verification failed: {error}")
        return 1
    if args.archive is None:
        print("Core v0.6.1 vendored grouping fixtures verified.")
    else:
        print("Core v0.6.1 grouping fixture release asset and vendored copy verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
