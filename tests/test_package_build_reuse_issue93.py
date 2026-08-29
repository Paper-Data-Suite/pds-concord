from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_package_fixture_accepts_validator_supplied_wheel_without_build_dependency(
) -> None:
    source = (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")

    assert 'os.environ.get("PDS_CONCORD_TEST_WHEEL")' in source
    assert "def built_wheel(request: pytest.FixtureRequest)" in source
    assert 'request.getfixturevalue("built_dist")' in source
    assert "def built_wheel(built_dist: Path)" not in source


def test_complete_validator_builds_once_before_pytest_and_supplies_exact_wheel(
) -> None:
    source = (ROOT / "scripts" / "validate_repository.py").read_text(
        encoding="utf-8"
    )

    build_marker = 'phase="package build"'
    pytest_marker = '"pytest",'
    supplied_marker = (
        'env["PDS_CONCORD_TEST_WHEEL"] = str(wheels[0].resolve())'
    )

    assert source.count(build_marker) == 1
    assert supplied_marker in source
    assert source.index(build_marker) < source.index(pytest_marker)
    assert source.index(supplied_marker) < source.index(pytest_marker)
