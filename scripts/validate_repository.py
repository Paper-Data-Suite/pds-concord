"""Run the principal local checks mirrored by continuous integration."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
STATIC_CACHE_ROOT_ENV = "PDS_CONCORD_VALIDATION_CACHE_ROOT"


@dataclass(frozen=True, slots=True)
class PhaseTiming:
    """Elapsed time for one repository-validation phase."""

    phase: str
    elapsed_seconds: float


def _run(
    command: list[str],
    *,
    phase: str,
    timings: list[PhaseTiming],
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> None:
    """Run one validation command and record elapsed time even on failure."""
    print("+", subprocess.list2cmdline(command), flush=True)
    started = perf_counter()
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            env=(
                env
                if env is not None
                else {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
            ),
        )
    finally:
        elapsed = perf_counter() - started
        timings.append(PhaseTiming(phase=phase, elapsed_seconds=elapsed))
        print(f"TIMING {phase}: {elapsed:.3f}s", flush=True)


def _copy_build_source(
    source_root: Path,
    destination: Path,
    *,
    timings: list[PhaseTiming],
) -> None:
    """Copy the clean build source while recording its standalone cost."""
    started = perf_counter()
    try:
        shutil.copytree(
            source_root,
            destination,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                "build",
                "dist",
                "*.egg-info",
                "__pycache__",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
            ),
        )
    finally:
        elapsed = perf_counter() - started
        timings.append(
            PhaseTiming(
                phase="source tree copy",
                elapsed_seconds=elapsed,
            )
        )
        print(f"TIMING source tree copy: {elapsed:.3f}s", flush=True)


def _print_timing_summary(
    timings: list[PhaseTiming],
    total_seconds: float,
) -> None:
    """Print stable diagnostic timing output for completed validation phases."""
    print("", flush=True)
    print("Validation timing summary:", flush=True)
    for timing in timings:
        print(f"  {timing.phase}: {timing.elapsed_seconds:.3f}s", flush=True)
    print(f"  TOTAL: {total_seconds:.3f}s", flush=True)


def _static_cache_directories(
    temp: Path,
    *,
    reuse_static_caches: bool,
) -> tuple[Path, Path]:
    """Resolve disposable or opt-in persistent Ruff and Mypy cache directories."""
    if not reuse_static_caches:
        return temp / "ruff-cache", temp / "mypy-cache"

    configured = os.environ.get(STATIC_CACHE_ROOT_ENV)
    cache_root = (
        Path(configured).expanduser()
        if configured
        else Path(tempfile.gettempdir()) / "pds-concord-validation-cache"
    ).resolve()
    repository_root = ROOT.resolve()
    if cache_root == repository_root or cache_root.is_relative_to(repository_root):
        raise RuntimeError(
            f"{STATIC_CACHE_ROOT_ENV} must resolve outside the repository."
        )

    ruff_cache = cache_root / "ruff"
    mypy_cache = cache_root / "mypy"
    ruff_cache.mkdir(parents=True, exist_ok=True)
    mypy_cache.mkdir(parents=True, exist_ok=True)
    print(f"Reusing static-analysis caches from {cache_root}", flush=True)
    return ruff_cache, mypy_cache


def validate(
    core_wheel: Path,
    *,
    allow_dirty: bool,
    reuse_static_caches: bool = False,
) -> None:
    """Run tests, static checks, builds, package checks, and smoke validation."""
    python = sys.executable
    timings: list[PhaseTiming] = []
    validation_started = perf_counter()
    try:
        _run(
            [python, "scripts/verify_core_wheel.py", str(core_wheel), "--installed"],
            phase="Core wheel verification",
            timings=timings,
        )
        _run(
            [python, "scripts/verify_core_grouping_fixtures.py"],
            phase="Core grouping fixtures",
            timings=timings,
        )
        _run(
            [python, "-m", "pip", "check"],
            phase="pip check",
            timings=timings,
        )
        with tempfile.TemporaryDirectory(
            prefix="pds-concord-validation-"
        ) as raw_temp:
            temp = Path(raw_temp)
            ruff_cache, mypy_cache = _static_cache_directories(
                temp,
                reuse_static_caches=reuse_static_caches,
            )
            env = {
                **os.environ,
                "TMP": str(temp),
                "TEMP": str(temp),
                "PDS_CORE_WHEEL": str(core_wheel.resolve()),
                "PYTHONDONTWRITEBYTECODE": "1",
                "RUFF_CACHE_DIR": str(ruff_cache),
                "MYPY_CACHE_DIR": str(mypy_cache),
            }

            dist = temp / "dist"
            source = temp / "source"
            _copy_build_source(ROOT, source, timings=timings)

            _run(
                [python, "-m", "build", "--outdir", str(dist)],
                phase="package build",
                timings=timings,
                cwd=source,
            )
            artifacts = sorted(dist.iterdir())
            wheels = list(dist.glob("*.whl"))
            if len(wheels) != 1:
                raise RuntimeError("Expected exactly one built Concord wheel.")
            env["PDS_CONCORD_TEST_WHEEL"] = str(wheels[0].resolve())

            commands = (
                (
                    "pytest",
                    [
                        python,
                        "-m",
                        "pytest",
                        "--basetemp",
                        str(temp / "pytest"),
                        "-o",
                        f"cache_dir={temp / 'pytest-cache'}",
                        "--durations=25",
                    ],
                ),
                ("Ruff", [python, "-m", "ruff", "check", "."]),
                ("Mypy", [python, "-m", "mypy"]),
                (
                    "documentation validation",
                    [python, "scripts/check_documentation.py"],
                ),
                (
                    "release compatibility",
                    [python, "scripts/verify_release_compatibility.py"],
                ),
            )
            for phase, command in commands:
                _run(
                    command,
                    phase=phase,
                    timings=timings,
                    cwd=ROOT,
                    env=env,
                )

            _run(
                [python, "-m", "twine", "check", *map(str, artifacts)],
                phase="Twine",
                timings=timings,
            )

            wheel = str(wheels[0])
            core = str(core_wheel)
            _run(
                [python, "scripts/check_package.py", wheel],
                phase="package content",
                timings=timings,
            )
            _run(
                [python, "scripts/verify_release_artifacts.py", str(dist)],
                phase="release artifacts",
                timings=timings,
            )
            _run(
                [python, "scripts/smoke_test_wheel.py", wheel, core],
                phase="installed-wheel smoke: base",
                timings=timings,
            )
            _run(
                [python, "scripts/smoke_test_feature_wheels.py", wheel, core],
                phase="installed-wheel smoke: shared feature scenarios",
                timings=timings,
            )
            _run(
                [
                    python,
                    "scripts/smoke_test_attention_provider_wheel.py",
                    wheel,
                    core,
                ],
                phase="installed-wheel smoke: module operations",
                timings=timings,
            )

        _run(
            ["git", "diff", "--check"],
            phase="git diff check",
            timings=timings,
        )
        if not allow_dirty:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                raise RuntimeError(
                    "Repository validation left or found working-tree residue."
                )
    finally:
        _print_timing_summary(
            timings,
            perf_counter() - validation_started,
        )


def main() -> int:
    """Parse arguments and validate the repository."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-wheel", required=True, type=Path)
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument(
        "--reuse-static-caches",
        action="store_true",
        help=(
            "Reuse Ruff and Mypy caches outside the repository. "
            "This affects speed only and does not change qualification coverage."
        ),
    )
    args = parser.parse_args()
    validate(
        args.core_wheel,
        allow_dirty=args.allow_dirty,
        reuse_static_caches=args.reuse_static_caches,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
