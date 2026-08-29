from __future__ import annotations

from pathlib import Path

import pytest

from scripts import validate_repository as validator


def test_default_static_caches_remain_disposable(tmp_path: Path) -> None:
    ruff_cache, mypy_cache = validator._static_cache_directories(
        tmp_path,
        reuse_static_caches=False,
    )

    assert ruff_cache == tmp_path / "ruff-cache"
    assert mypy_cache == tmp_path / "mypy-cache"
    assert not ruff_cache.exists()
    assert not mypy_cache.exists()


def test_reusable_static_caches_use_explicit_external_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_root = tmp_path / "persistent"
    monkeypatch.setenv(
        validator.STATIC_CACHE_ROOT_ENV,
        str(cache_root),
    )

    ruff_cache, mypy_cache = validator._static_cache_directories(
        tmp_path / "disposable",
        reuse_static_caches=True,
    )

    assert ruff_cache == cache_root.resolve() / "ruff"
    assert mypy_cache == cache_root.resolve() / "mypy"
    assert ruff_cache.is_dir()
    assert mypy_cache.is_dir()


def test_reusable_static_cache_root_cannot_live_in_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        validator.STATIC_CACHE_ROOT_ENV,
        str(validator.ROOT / ".validation-cache"),
    )

    with pytest.raises(RuntimeError, match="outside the repository"):
        validator._static_cache_directories(
            validator.ROOT / "ignored",
            reuse_static_caches=True,
        )


def test_validator_cli_exposes_opt_in_cache_reuse() -> None:
    source = Path(validator.__file__).read_text(encoding="utf-8")

    assert '"--reuse-static-caches"' in source
    assert '"PDS_CONCORD_VALIDATION_CACHE_ROOT"' in source
    assert "reuse_static_caches=args.reuse_static_caches" in source
    assert "This affects speed only" in source
