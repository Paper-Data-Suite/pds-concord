"""#136 release gate: checkout-safe isolated builds and deep viewer fixtures."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from scripts.probe_issue136_windows_viewer import _files_digest, _fixtures, _units
from scripts.run_issue136_installed_acceptance import _copy_tracked_source


def test_installed_acceptance_copies_only_git_tracked_files(tmp_path: Path) -> None:
    repo = tmp_path / "source-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "pyproject.toml").write_text(
        "[project]\nname='synthetic'\n", encoding="utf-8"
    )
    (repo / "concord").mkdir()
    (repo / "concord/__init__.py").write_text("VERSION = 1\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "--", "pyproject.toml", "concord/__init__.py"],
        cwd=repo,
        check=True,
    )
    residue = repo / "pds_concord.egg-info"
    residue.mkdir()
    (residue / "SOURCES.txt").write_text("existing build evidence", encoding="utf-8")
    (repo / "scratch-private.txt").write_text("untracked", encoding="utf-8")
    destination = tmp_path / "isolated-build-source"
    _copy_tracked_source(repo, destination)
    assert (
        (destination / "pyproject.toml")
        .read_text(encoding="utf-8")
        .startswith("[project]")
    )
    assert (destination / "concord/__init__.py").is_file()
    assert not (destination / "pds_concord.egg-info").exists()
    assert not (destination / "scratch-private.txt").exists()
    assert (residue / "SOURCES.txt").read_text(
        encoding="utf-8"
    ) == "existing build evidence"


def test_deep_synthetic_pdf_html_and_folder_are_source_stable(tmp_path: Path) -> None:
    pdf, html, folder = _fixtures(tmp_path / "synthetic-only")
    assert folder.is_dir() and pdf.is_file() and html.is_file()
    assert all(_units(item) >= 296 for item in (pdf, html, folder))
    assert pdf.read_bytes().startswith(b"%PDF")
    assert "CONCORD #136" in html.read_text(encoding="utf-8")
    before = _files_digest(pdf, html)
    assert _files_digest(pdf, html) == before


def test_physical_viewer_requires_human_confirmation_and_exact_alias_identity() -> None:
    from scripts import probe_issue136_windows_viewer as source_module

    source = Path(source_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    attribute_names = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert {"samefile", "resolve", "read_bytes"} <= attribute_names
    assert "startfile" in source
    assert "open_local_path(target)" in source
    assert 'confirmed.strip() != "YES"' in source
    assert "Alias dispatch is NOT human-confirmed application display." in source
