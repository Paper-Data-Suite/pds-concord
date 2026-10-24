"""Issue #140 Slice 0: capture an exact, privacy-safe, read-only source baseline.

The only intended writes are the two create-only evidence files under --output-dir.
No Core workspace, class roster, or application records are accessed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import tomllib
import zipfile
from datetime import datetime, timezone
from email.parser import BytesParser
from pathlib import Path
from typing import Any, Final

EXPECTED_REPO: Final[str] = "Paper-Data-Suite/pds-concord"
EXPECTED_BRANCH: Final[str] = "140-freeze-baseline-and-teacher-context-audit"
BASELINE_COMMIT: Final[str] = "68ddd804d2733fa900ee396ac7a2ba6bd98aa819"
BASELINE_TAG: Final[str] = "v0.3.4"
BASELINE_VERSION: Final[str] = "0.3.4"
CORE_VERSION: Final[str] = "0.6.6"
CORE_SHA256: Final[str] = (
    "d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301"
)
CONCORD_WHEEL_SHA256: Final[str] = (
    "35fbebf4338420c83047f0cb4a09d06b22bb493abf4d67e6082e59ae4fc35b23"
)
REQUIRED_PREVIOUS: Final[tuple[str, ...]] = (
    "scripts/audit_issue134_teacher_surfaces.py",
    "scripts/run_issue134_installed_acceptance.py",
    "scripts/run_issue136_installed_acceptance.py",
    "scripts/verify_core_wheel.py",
    "scripts/validate_repository.py",
    "tests/test_issue136_slice1_menu_standards.py",
    "tests/test_issue136_slice2_teacher_context.py",
    "tests/test_issue134_slice0_audit.py",
    "tests/test_issue134_slice4a_viewer_handoff.py",
    "tests/test_issue136_slice7d_release_harness_viewer.py",
    "concord/menu_standards_context.py",
    "concord/storage.py",
    "concord/menu_activity.py",
    "concord/menu_artifact.py",
    "concord/menu_artifact_scoring.py",
    "concord/menu_score_teacher_labels.py",
    "concord/reusable_presets.py",
    "concord/workflows/artifact_page.py",
)


class BaselineError(ValueError):
    """A checked premise is false: do not publish a misleading baseline."""


def _run(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        # Do not serialize local paths or Git's potentially private error text.
        raise BaselineError(f"Git command failed: {' '.join(args)}")
    return result.stdout.strip()


def _git_identity(repo: Path) -> dict[str, Any]:
    if Path(_run(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise BaselineError("--repo must be the exact checkout root")
    branch = _run(repo, "branch", "--show-current")
    head = _run(repo, "rev-parse", "HEAD")
    main = _run(repo, "rev-parse", "refs/heads/main")
    tag_object = _run(repo, "rev-parse", "refs/tags/" + BASELINE_TAG)
    tag_kind = _run(repo, "cat-file", "-t", "refs/tags/" + BASELINE_TAG)
    tag_peeled = _run(repo, "rev-parse", "refs/tags/" + BASELINE_TAG + "^{commit}")
    if branch != EXPECTED_BRANCH:
        raise BaselineError(f"Unexpected branch: {branch!r}")
    if head != BASELINE_COMMIT or main != BASELINE_COMMIT:
        raise BaselineError("Branch/main no longer match the frozen v0.3.4 commit")
    if tag_kind != "tag" or tag_peeled != BASELINE_COMMIT:
        raise BaselineError("Annotated v0.3.4 tag does not peel to the frozen commit")
    origin = _run(repo, "remote", "get-url", "origin")
    normalized = origin.removesuffix(".git").rstrip("/")
    if not (
        normalized.endswith("github.com/" + EXPECTED_REPO)
        or normalized == "git@github.com:" + EXPECTED_REPO
        or normalized.endswith("github.com:" + EXPECTED_REPO)
    ):
        raise BaselineError("Origin is not the expected Concord repository")
    tracked_dirty = bool(_run(repo, "status", "--porcelain=v1", "--untracked-files=no"))
    if tracked_dirty:
        raise BaselineError("Preexisting tracked changes prevent exact source freeze")
    # Untracked Slice 0 files are expected before their first commit. Record a
    # count rather than paths, which might include unrelated private filenames.
    untracked = _run(repo, "ls-files", "--others", "--exclude-standard")
    return {
        "branch": branch,
        "head": head,
        "main_local": main,
        "tag": BASELINE_TAG,
        "tag_object": tag_object,
        "tag_object_type": tag_kind,
        "tag_peeled_commit": tag_peeled,
        "origin_repository": EXPECTED_REPO,
        "tracked_files_clean": True,
        "untracked_file_count": len(untracked.splitlines()) if untracked else 0,
        "remote_refs": "checked separately by guarded PowerShell runner",
    }


def _hash_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _distribution(name: str) -> dict[str, Any]:
    try:
        dist = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError:
        return {"status": "not_installed", "name": name}
    direct = dist.read_text("direct_url.json")
    editable: bool | None = None
    if direct:
        try:
            data = json.loads(direct)
            editable = bool(data.get("dir_info", {}).get("editable", False))
        except (ValueError, AttributeError, TypeError):
            editable = None
    return {
        "status": "metadata_present",
        "name": name,
        "version": dist.version,
        "editable": editable,
        "dependencies": sorted(dist.requires or []),
    }


def _metadata_from_wheel(path: Path) -> tuple[str, str]:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise BaselineError("Wheel ZIP CRC failed")
        entries = [
            n
            for n in archive.namelist()
            if n.count("/") == 1 and n.endswith(".dist-info/METADATA")
        ]
        if len(entries) != 1:
            raise BaselineError("Wheel has no unique distribution metadata")
        message = BytesParser().parsebytes(archive.read(entries[0]))
        return str(message.get("Name")), str(message.get("Version"))


def _wheel(
    path: Path | None, *, filename: str, digest: str, distribution: str, version: str
) -> dict[str, Any]:
    if path is None:
        return {"status": "not_provided", "expected_filename": filename}
    if not path.is_file():
        raise BaselineError(f"Expected {filename} wheel was not found")
    if path.name != filename:
        raise BaselineError(f"Unexpected wheel filename; expected {filename}")
    actual = _hash_file(path)
    if actual != digest:
        raise BaselineError(f"Published wheel SHA-256 mismatch: {filename}")
    name, real_version = _metadata_from_wheel(path)
    if name.lower().replace("_", "-") != distribution or real_version != version:
        raise BaselineError(f"Published wheel METADATA identity mismatch: {filename}")
    return {
        "status": "verified_published_bytes_and_metadata",
        "filename": filename,
        "sha256": actual,
        "distribution": name,
        "version": real_version,
    }


def _source_contract(repo: Path) -> dict[str, Any]:
    with (repo / "pyproject.toml").open("rb") as f:
        project = tomllib.load(f)["project"]
    version_text = (repo / "concord/_version.py").read_text(encoding="utf-8")
    if f'__version__ = "{BASELINE_VERSION}"' not in version_text:
        raise BaselineError("Source Concord version is not frozen v0.3.4")
    if "pds-core>=0.6.6,<0.7" not in project["dependencies"]:
        raise BaselineError("Core requirement changed from frozen v0.3.4 contract")
    return {
        "name": project["name"],
        "version": BASELINE_VERSION,
        "requires_python": project["requires-python"],
        "dependencies": project["dependencies"],
        "source_version_sha256": _hash_file(repo / "concord/_version.py"),
        "pyproject_sha256": _hash_file(repo / "pyproject.toml"),
    }


def _inventory(repo: Path) -> dict[str, Any]:
    def names(glob: str) -> list[str]:
        return sorted(
            p.relative_to(repo).as_posix() for p in repo.glob(glob) if p.is_file()
        )

    groups = {
        "teacher_menu_modules": names("concord/menu_*.py") + ["concord/menu.py"],
        "direct_cli_modules": names("concord/cli_app/**/*.py") + ["concord/cli.py"],
        "workflow_modules": names("concord/workflows/*.py"),
        "prior_issue134_tests": names("tests/test_issue134_*.py"),
        "prior_issue136_tests": names("tests/test_issue136_*.py"),
        "other_menu_tests": names("tests/test_menu_*.py"),
    }
    groups = {key: sorted(set(value)) for key, value in groups.items()}
    absent = [rel for rel in REQUIRED_PREVIOUS if not (repo / rel).is_file()]
    if absent:
        raise BaselineError("Required #134/#136 baseline file missing: " + absent[0])
    previous_hashes = {rel: _hash_file(repo / rel) for rel in REQUIRED_PREVIOUS}
    return {
        "source_surfaces": groups,
        "counts": {key: len(paths) for key, paths in groups.items()},
        "prior_regression_and_contract_sha256": previous_hashes,
        "prior_tests_rerun_status": "not_claimed_by_capture",
        "historical_physical_returned_work_long_path": "not_proven_by_baseline",
    }


def capture(
    repo: Path, *, core_wheel: Path | None, concord_wheel: Path | None
) -> dict[str, Any]:
    repo = repo.resolve()
    git = _git_identity(repo)
    source = _source_contract(repo)
    artifacts = {
        "core_v0_6_6_wheel": _wheel(
            core_wheel,
            filename="pds_core-0.6.6-py3-none-any.whl",
            digest=CORE_SHA256,
            distribution="pds-core",
            version=CORE_VERSION,
        ),
        "concord_v0_3_4_wheel": _wheel(
            concord_wheel,
            filename="pds_concord-0.3.4-py3-none-any.whl",
            digest=CONCORD_WHEEL_SHA256,
            distribution="pds-concord",
            version=BASELINE_VERSION,
        ),
    }
    installed = {
        "concord": _distribution("pds-concord"),
        "core": _distribution("pds-core"),
    }
    # Installing a matching distribution does NOT itself authenticate a wheel.
    # In particular, an editable installation is not an installed-wheel witness.
    return {
        "schema": "concord_issue140_slice0_baseline_v1",
        "captured_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository": EXPECTED_REPO,
        "git": git,
        "source": source,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "system": platform.system(),
            "release": platform.release(),
            "machine_architecture": platform.machine(),
            "venv_active": sys.prefix != sys.base_prefix,
            "installed_distributions": installed,
        },
        "published_artifacts": artifacts,
        "inventory": _inventory(repo),
        "limits": {
            "physical_print_scan_return": "unperformed",
            "windows_returned_artifact_long_path": "unperformed",
            "meridian_live_ingestion": "unperformed",
            "teacher_menu_bug_reproductions": "deferred_to_slice_2",
            "systematic_route_classifications": "deferred_to_slice_1_and_3",
            "source_git_remote_live_comparison": "guarded_runner_only",
        },
    }


def _markdown(record: dict[str, Any]) -> str:
    git = record["git"]
    art = record["published_artifacts"]
    env = record["environment"]
    counts = record["inventory"]["counts"]
    lines = [
        "# Concord #140 Slice 0 — Baseline Receipt",
        "",
        "> Nonproduction, metadata-only audit. No classroom workspace was read.",
        "",
        f"- Captured (UTC): `{record['captured_utc']}`",
        f"- Repository: `{record['repository']}`",
        f"- Branch: `{git['branch']}`",
        f"- HEAD and local main: `{git['head']}`",
        f"- Annotated tag: `{git['tag']}` object `{git['tag_object']}`",
        f"- Tag peels to: `{git['tag_peeled_commit']}`",
        f"- Tracked source clean when captured: `{git['tracked_files_clean']}`",
        (
            f"- Concord source: `{record['source']['version']}`; "
            "Core requirement: `>=0.6.6,<0.7`"
        ),
        (
            f"- Python: `{env['python']}`; platform: `{env['system']}` "
            f"/ `{env['machine_architecture']}`"
        ),
        "",
        "## Published wheel verification",
        "",
    ]
    for name, details in art.items():
        lines.append(f"- {name}: **{details['status']}**")
        if "sha256" in details:
            lines.append(f"  - SHA-256: `{details['sha256']}`")
    lines += [
        "",
        "Installed distribution metadata is separately captured in the JSON; it is",
        "**not** equivalent to published-byte authentication or a clean-wheel test.",
        "",
        "## Source inventory (classification deferred to Slice 1)",
        "",
    ]
    for key, count in sorted(counts.items()):
        lines.append(f"- `{key}`: {count} files")
    lines += [
        "",
        "Exact relative file lists and #134/#136 SHA-256 fingerprints are in the JSON.",
        "The existing bounded #136 AST dispatch tests are **not** a full menu audit.",
        "",
        "## Provenance / scope limitations",
        "",
        (
            "- Remote Git refs must be compared by the runner; "
            "this script verifies local commit and tag objects."
        ),
        (
            "- No live Activity, Core roster, teacher workspace "
            "or OneDrive location was opened."
        ),
        "- No installed-wheel smoke tests are claimed by this receipt.",
        "- Windows physical returned-work opening, real print/QR/scan intake and",
        "  actual Meridian ingestion remain **unperformed**; opening a prepared PDF",
        "  is not a returned-evidence acceptance witness.",
        "- Reproduce #138 P0 Activity Edit and Criterion preset bugs in Slice 2,",
        "  rather than mislabeling source inspection as a menu reproduction.",
        "- The detailed audited menu/context matrix is due in Slice 1; suspects",
        "  remain unverified until operation-specific evidence is recorded.",
        "",
        "## Reproduction command",
        "",
        "```powershell",
        (
            "python scripts/issue140_slice0_baseline.py --repo . "
            "--output-dir docs/audits/issue140"
        ),
        "```",
        "",
        "Pass `--core-wheel` and `--concord-wheel` for published-byte validation.",
        "Capture again only to a new output location: baseline files are create-only.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--core-wheel", type=Path)
    parser.add_argument("--concord-wheel", type=Path)
    args = parser.parse_args()
    try:
        output = args.output_dir.resolve()
        json_path, md_path = output / "baseline.json", output / "baseline.md"
        if json_path.exists() or md_path.exists():
            raise BaselineError(
                "Slice 0 baseline receipt already exists; refusing overwrite"
            )
        record = capture(
            args.repo, core_wheel=args.core_wheel, concord_wheel=args.concord_wheel
        )
        # Prepare both renderings before any write; create-only, never mutate.
        body = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode("utf-8")
        prose = _markdown(record).encode("utf-8")
        output.mkdir(parents=True, exist_ok=True)
        with json_path.open("xb") as f:
            f.write(body)
        try:
            with md_path.open("xb") as f:
                f.write(prose)
        except Exception:
            json_path.unlink()
            raise
        print("Slice 0 baseline captured (source-only inventory; no teacher data).")
        print(
            "Core wheel: "
            f"{record['published_artifacts']['core_v0_6_6_wheel']['status']}"
        )
        print(
            "Concord wheel: "
            f"{record['published_artifacts']['concord_v0_3_4_wheel']['status']}"
        )
        print(
            "Next: run the prior regression tests using the guarded PowerShell runner."
        )
        return 0
    except (BaselineError, OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"Issue #140 Slice 0 FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
