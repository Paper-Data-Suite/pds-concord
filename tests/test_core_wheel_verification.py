from __future__ import annotations

import os
from pathlib import Path

import pytest

from scripts.verify_core_wheel import (
    EXPECTED_CORE_WHEEL_FILENAME,
    CoreVerificationError,
    verify_core_wheel,
    verify_installed_core,
)


def test_installed_core_identity() -> None:
    verify_installed_core()


def test_official_core_wheel_authentication_when_supplied() -> None:
    raw_path = os.environ.get("PDS_CORE_WHEEL")
    if raw_path is None:
        pytest.skip("PDS_CORE_WHEEL is supplied by release validation and CI")
    verify_core_wheel(Path(raw_path))


def test_verifier_rejects_wrong_filename(tmp_path: Path) -> None:
    wrong = tmp_path / "rebuilt.whl"
    wrong.write_bytes(b"not a wheel")
    with pytest.raises(CoreVerificationError, match=EXPECTED_CORE_WHEEL_FILENAME):
        verify_core_wheel(wrong)
