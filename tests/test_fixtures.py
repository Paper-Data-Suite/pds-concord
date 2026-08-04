from __future__ import annotations

from pathlib import Path

import pytest
from conftest import FIXTURE_PATH, load_strict_json


def test_fixture_is_strict_utf8_and_private_data_free(
    baseline_context: dict[str, object],
) -> None:
    assert baseline_context["module_id"] == "concord"
    assert baseline_context["activity_id"] == baseline_context["record_id"]
    text = FIXTURE_PATH.read_bytes().decode("utf-8", errors="strict")
    forbidden = ("@", "password", "credential", "student name", "teacher name", "C:\\")
    assert not any(value.lower() in text.lower() for value in forbidden)


@pytest.mark.parametrize(
    "invalid_json",
    ['{"key": 1, "key": 2}', '{"value": NaN}', '{"value": Infinity}'],
)
def test_fixture_loader_rejects_duplicate_keys_and_nonstandard_numbers(
    invalid_json: str, tmp_path: Path
) -> None:
    fixture = tmp_path / "invalid.json"
    fixture.write_text(invalid_json, encoding="utf-8")
    with pytest.raises(ValueError):
        load_strict_json(fixture)


def test_fixture_loading_is_read_only(tmp_path: Path) -> None:
    before = FIXTURE_PATH.read_bytes()
    load_strict_json(FIXTURE_PATH)
    assert FIXTURE_PATH.read_bytes() == before
    assert not list(tmp_path.iterdir())
