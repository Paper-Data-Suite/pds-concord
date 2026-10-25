"""Integrity-checked #140 source snapshot for subsequent Concord repairs.

Frozen historical checks run against the archived source, not a changing menu.
Current-source regression tests and the successor #162 audit remain separate.
"""

from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Final

ARCHIVE: Final[str] = "tests/fixtures/issue140_frozen_source.zip"
MANIFEST: Final[str] = "docs/audits/issue141/slice3_frozen_archive.json"
BASE: Final[str] = "docs/audits/issue140"
ANCHOR: Final[str] = "40837d54376f70cffb9ca539d52f7e40453ec1e6"
# Exact Git blob identities of the immutable, squash-merged #140 audit receipts.
AUDIT_BLOBS: Final[dict[str, str]] = {
    "baseline.json": "290a8753673adc75f17e8bfbf489d12682ab026b",
    "baseline.md": "68af3f213a343dae18ed95f9c69c84b86de64213",
    "service_context_catalog.csv": "3d1971e53b19ea7f34e81952bbffb24aca75a482",
    "slice3a_candidate_boundaries.csv": "4ba8a15db722d2ded9fca09c103028c23ab2cd98",
    "slice3e_scoped_dispositions.csv": "a6003590bd958d8dd3227dc0ee1790730b54a3f3",
    "slice4b_surface_review_queue.csv": "3bfc1ad9ced81dfa1cc2bfdd1609cef54945e876",
    "slice4c_handoff.json": "d1200dfa586ebdf02bcc52f0aecc7f5938223e38",
    "slice4c_handoff.md": "bbb68534346cdca2726ebc44db8502753fa5f7c4",
    "surface_inventory.json": "f0bec0972acc63123441c0ea140df06088eadb3a",
    "teacher_operation_matrix.csv": "8826d9cb5772c1d2cbfaf599d3bf8c584841fc50",
}


class SnapshotError(ValueError):
    """The historical source or frozen evidence could not be authenticated."""


def git_blob_id(data: bytes) -> str:
    prefix = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(prefix + data).hexdigest()  # noqa: S324


def verify_receipts(repo: Path) -> None:
    for name, blob in AUDIT_BLOBS.items():
        path = repo / BASE / name
        if not path.is_file() or path.is_symlink():
            raise SnapshotError(f"Missing or unsafe frozen #140 receipt: {name}")
        if git_blob_id(path.read_bytes()) != blob:
            raise SnapshotError(f"Frozen #140 receipt differs from merge: {name}")


def materialize(repo: Path, target: Path) -> dict[str, object]:
    """Authenticate ZIP + receipts and safely extract to an empty test directory."""
    repo = repo.resolve()
    verify_receipts(repo)
    manifest_path = repo / MANIFEST
    archive_path = repo / ARCHIVE
    if not manifest_path.is_file() or not archive_path.is_file():
        raise SnapshotError("Historical archive or manifest is missing")
    parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise SnapshotError("Malformed historical archive manifest")
    manifest: dict[str, object] = parsed
    if (
        manifest.get("schema") != "concord.issue141.frozen140-source/1"
        or manifest.get("source_commit") != ANCHOR
        or manifest.get("audit_git_blobs") != AUDIT_BLOBS
    ):
        raise SnapshotError("Historical archive manifest or source ref changed")
    checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if checksum != manifest.get("archive_sha256"):
        raise SnapshotError("Historical source ZIP SHA-256 mismatch")
    if target.exists():
        raise SnapshotError("Historical extract target must not already exist")
    target.mkdir(parents=True)
    seen: set[str] = set()
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise SnapshotError("Historical source ZIP CRC mismatch")
        files = 0
        for info in archive.infolist():
            name = info.filename
            parts = PurePosixPath(name)
            if (
                parts.is_absolute()
                or not parts.parts
                or ".." in parts.parts
                or "\\" in name
                or ":" in name
                or name in seen
                or (stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK)
            ):
                raise SnapshotError("Unsafe or repeated frozen archive path")
            seen.add(name)
            if not (
                name.startswith("concord/")
                or name.startswith(BASE + "/")
                or name == "tests/test_issue140_slice3a_triage.py"
                or (info.is_dir() and name in {"docs/", "docs/audits/", "tests/"})
            ):
                raise SnapshotError("Unexpected archived source path")
            if not info.is_dir():
                files += 1
                if info.file_size > 6_000_000:
                    raise SnapshotError("Unexpectedly large frozen archive entry")
        if files != manifest.get("files") or files < 75:
            raise SnapshotError("Unexpected historical source file count")
        archive.extractall(target)
    verify_receipts(target)
    return manifest
