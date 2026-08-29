from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts import validate_repository as validator


def test_issue93_phase_timing_is_immutable() -> None:
    timing = validator.PhaseTiming("pytest", 12.5)
    assert timing.phase == "pytest"
    assert timing.elapsed_seconds == 12.5
    with pytest.raises(AttributeError):
        timing.phase = "changed"  # type: ignore[misc]


def test_issue93_run_records_timing_and_preserves_supplied_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    moments = iter((10.0, 12.5))
    observed: dict[str, Any] = {}

    monkeypatch.setattr(validator, "perf_counter", lambda: next(moments))

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        check: bool,
        env: dict[str, str],
    ) -> None:
        observed["command"] = command
        observed["cwd"] = cwd
        observed["check"] = check
        observed["env"] = env

    monkeypatch.setattr(validator.subprocess, "run", fake_run)

    timings: list[validator.PhaseTiming] = []
    supplied_env = {"PDS_TEST": "1"}
    validator._run(
        ["python", "-V"],
        phase="synthetic phase",
        timings=timings,
        cwd=tmp_path,
        env=supplied_env,
    )

    assert observed == {
        "command": ["python", "-V"],
        "cwd": tmp_path,
        "check": True,
        "env": supplied_env,
    }
    assert timings == [validator.PhaseTiming("synthetic phase", 2.5)]


def test_issue93_run_records_failed_phase_timing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    moments = iter((20.0, 23.25))
    monkeypatch.setattr(validator, "perf_counter", lambda: next(moments))

    def fail_run(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise subprocess.CalledProcessError(7, ["synthetic"])

    monkeypatch.setattr(validator.subprocess, "run", fail_run)

    timings: list[validator.PhaseTiming] = []
    with pytest.raises(subprocess.CalledProcessError):
        validator._run(
            ["synthetic"],
            phase="failed phase",
            timings=timings,
        )

    assert timings == [validator.PhaseTiming("failed phase", 3.25)]


def test_issue93_timing_summary_is_stable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    validator._print_timing_summary(
        [
            validator.PhaseTiming("pytest", 10.1254),
            validator.PhaseTiming("package build", 2.0),
        ],
        12.5,
    )

    assert capsys.readouterr().out == (
        "\n"
        "Validation timing summary:\n"
        "  pytest: 10.125s\n"
        "  package build: 2.000s\n"
        "  TOTAL: 12.500s\n"
    )


def test_issue93_complete_validator_exposes_required_measurement_phases() -> None:
    source = Path(validator.__file__).read_text(encoding="utf-8")
    for expected in (
        '"Core wheel verification"',
        '"Core grouping fixtures"',
        '"pip check"',
        '"pytest"',
        '"Ruff"',
        '"Mypy"',
        '"documentation validation"',
        '"release compatibility"',
        '"source tree copy"',
        '"package build"',
        '"Twine"',
        '"package content"',
        '"release artifacts"',
        '"installed-wheel smoke: base"',
        '"installed-wheel smoke: shared feature scenarios"',
        '"installed-wheel smoke: module operations"',
        '"git diff check"',
        '"--durations=25"',
        "validation_started = perf_counter()",
        "_print_timing_summary(",
    ):
        assert expected in source
