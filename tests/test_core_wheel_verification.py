from __future__ import annotations

import os
from pathlib import Path

import pds_core
import pytest

from scripts.verify_core_wheel import (
    EXPECTED_CORE_WHEEL_FILENAME,
    CoreVerificationError,
    verify_core_wheel,
    verify_installed_core,
)


def test_installed_core_identity() -> None:
    verify_installed_core()


def test_installed_core_version_agreement_is_accepted() -> None:
    assert isinstance(pds_core.__version__, str)
    verify_installed_core()


def test_imported_core_version_mismatch_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pds_core, "__version__", "0.6.1")
    with pytest.raises(CoreVerificationError, match="disagrees with installed"):
        verify_installed_core()


@pytest.mark.parametrize("invalid_version", [None, 600])
def test_imported_core_non_string_version_is_rejected(
    monkeypatch: pytest.MonkeyPatch, invalid_version: object
) -> None:
    monkeypatch.setattr(pds_core, "__version__", invalid_version)
    with pytest.raises(CoreVerificationError, match="must be a string"):
        verify_installed_core()


def test_imported_core_missing_version_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delattr(pds_core, "__version__")
    with pytest.raises(CoreVerificationError, match="is missing"):
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
