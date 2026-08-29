from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_retains_all_supported_os_python_cells() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    for os_name in ("ubuntu-latest", "windows-latest"):
        for python in ("3.11", "3.12", "3.13", "3.14"):
            assert f"- os: {os_name}\n            python: \"{python}\"" in text

    assert text.count("          - os: ") == 8


def test_ci_complete_qualification_spans_os_and_python_range() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert (
        '- os: ubuntu-latest\n            python: "3.11"\n            complete: true'
        in text
    )
    assert (
        '- os: windows-latest\n            python: "3.14"\n            complete: true'
        in text
    )
    assert text.count("            complete: true") == 2
    assert text.count("            complete: false") == 6


def test_ci_compatibility_cells_keep_runtime_pytest_and_hygiene() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Run compatibility validation" in text
    assert "matrix.complete == false" in text
    assert "python scripts/verify_core_wheel.py --installed" in text
    assert "python -m pip check" in text
    assert 'python -c "import concord"' in text
    assert "python -m pytest" in text
    assert "--durations=25" in text
    assert "git diff --check" in text
    assert "git status --porcelain --untracked-files=all" in text


def test_ci_complete_cells_delegate_to_authoritative_validator() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "Run complete repository qualification" in text
    assert "matrix.complete == true" in text
    assert "python scripts/validate_repository.py" in text
    assert '--core-wheel "$env:PDS_CORE_WHEEL"' in text

    for duplicated_command in (
        "python -m ruff check .",
        "python -m mypy",
        "python -m build --outdir",
        "python -m twine check",
        "scripts/smoke_test_wheel.py",
        "scripts/smoke_test_activity_copying_wheel.py",
    ):
        assert duplicated_command not in text
