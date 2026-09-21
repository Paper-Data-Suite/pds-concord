from __future__ import annotations

from pathlib import Path

import pytest
from pds_core.scan_routes import scans_inbox_dir

import concord.menu_scan as menu_scan


def test_scan_inbox_sources_uses_core_shared_inbox_and_does_not_create(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    expected = scans_inbox_dir(workspace)

    inbox, sources = menu_scan._scan_inbox_sources(workspace)

    assert inbox == expected
    assert sources == ()
    assert not expected.exists()


def test_scan_inbox_sources_filters_supported_top_level_regular_files(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)

    supported = (
        inbox / "A.PDF",
        inbox / "b.png",
        inbox / "c.JPG",
        inbox / "d.jpeg",
        inbox / "e.TIF",
        inbox / "f.tiff",
    )
    for path in supported:
        path.write_bytes(b"synthetic scan")

    (inbox / "ignore.txt").write_text("not a scan", encoding="utf-8")
    (inbox / "ignore.csv").write_text("not a scan", encoding="utf-8")
    nested = inbox / "nested"
    nested.mkdir()
    (nested / "nested.pdf").write_bytes(b"nested scan")

    resolved_inbox, sources = menu_scan._scan_inbox_sources(workspace)

    assert resolved_inbox == inbox
    assert sources == supported


def test_scan_inbox_sources_sorts_case_insensitively_with_stable_tiebreaker(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    for name in ("scan-c.pdf", "Scan-B.pdf", "scan-a.pdf", "alpha.PDF"):
        (inbox / name).write_bytes(name.encode("utf-8"))

    _, sources = menu_scan._scan_inbox_sources(workspace)

    assert tuple(path.name for path in sources) == (
        "alpha.PDF",
        "scan-a.pdf",
        "Scan-B.pdf",
        "scan-c.pdf",
    )


def test_scan_inbox_sources_does_not_offer_symlinked_file(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    backing = tmp_path / "backing.pdf"
    backing.write_bytes(b"synthetic scan")
    linked = inbox / "linked.pdf"
    try:
        linked.symlink_to(backing)
    except OSError as error:
        pytest.skip(f"filesystem cannot create scan symlink: {error}")

    _, sources = menu_scan._scan_inbox_sources(workspace)

    assert sources == ()


def test_scan_inbox_sources_rejects_non_directory_inbox(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    inbox = scans_inbox_dir(workspace)
    inbox.write_bytes(b"not a directory")

    with pytest.raises(
        NotADirectoryError,
        match="Shared scan inbox is not a directory",
    ):
        menu_scan._scan_inbox_sources(workspace)


def test_scan_inbox_sources_is_read_only_for_existing_files(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    inbox = scans_inbox_dir(workspace)
    inbox.mkdir(parents=True)
    first = inbox / "first.pdf"
    second = inbox / "second.png"
    first.write_bytes(b"first bytes")
    second.write_bytes(b"second bytes")
    before = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (first, second)
    }

    _, sources = menu_scan._scan_inbox_sources(workspace)

    after = {
        path.name: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (first, second)
    }
    assert sources == (first, second)
    assert after == before
