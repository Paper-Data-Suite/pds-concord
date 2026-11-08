"""#148 Slice 1: Concord-local self-declared actor storage, no academic writes."""

from __future__ import annotations

import json
import os
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import concord.teacher_attribution as attribution
from concord.teacher_attribution import (
    ConcordTeacherAttributionProvider,
    ConcordTeacherAttributionStore,
    TeacherAttributionConflictError,
    TeacherAttributionNotConfiguredError,
    TeacherAttributionStorageError,
    TeacherAttributionValidationError,
)


def _store(tmp_path: Path) -> ConcordTeacherAttributionStore:
    return ConcordTeacherAttributionStore(
        config_directory=tmp_path,
        actor_id_factory=lambda: "teacher-generated-1",
    )


def _write_bad(store: ConcordTeacherAttributionStore, raw: bytes) -> None:
    store.directory.mkdir(mode=0o700)
    store.profile_path.write_bytes(raw)
    if os.name != "nt":
        store.profile_path.chmod(0o600)


def test_absent_load_and_provider_are_read_only(tmp_path: Path) -> None:
    store = _store(tmp_path)
    provider = ConcordTeacherAttributionProvider(store)
    assert store.load() is None
    with pytest.raises(TeacherAttributionNotConfiguredError):
        provider.resolve()
    assert list(tmp_path.iterdir()) == []


def test_explicit_create_and_fresh_store_reopen_retains_attribution(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    saved = store.create("Dr. Ñ. O'Connor")
    provider = ConcordTeacherAttributionProvider(_store(tmp_path))
    identity, fingerprint = provider.resolve_with_fingerprint()
    assert identity.actor_id == "teacher-generated-1"
    assert identity.display_name == "Dr. Ñ. O'Connor"
    assert identity.source == "saved"
    assert fingerprint == saved.sha256
    actor = provider.resolve_actor()
    assert actor.actor_id == identity.actor_id
    assert actor.display_label == identity.display_name
    assert actor.owning_system == "concord"
    assert actor.actor_kind == "authorized_adult"
    assert saved.profile.revision == 1
    assert len(saved.sha256) == 64
    assert store.profile_path.parent.name == "concord"
    assert sorted(x.name for x in tmp_path.iterdir()) == ["concord"]


def test_generated_id_can_be_replaced_by_explicit_core_valid_id(tmp_path: Path) -> None:
    store = _store(tmp_path)
    initial = store.create("Synthetic Person", actor_id="teacher-synthetic-99")
    assert initial.profile.actor_id == "teacher-synthetic-99"
    updated = store.replace_identity(
        initial, display_name="New Author", actor_id="teacher-new-7", confirmed=True
    )
    assert updated.profile.actor_id == "teacher-new-7"
    assert updated.profile.revision == 2
    assert initial.profile.actor_id == "teacher-synthetic-99"


def test_display_only_change_preserves_actor_id_and_noop_does_not_write(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    first = store.create("First Author")
    assert store.update_display_name(first, "First Author") == first
    assert store.load() == first
    changed = store.update_display_name(first, "Second Author")
    assert changed.profile.actor_id == first.profile.actor_id
    assert changed.profile.display_name == "Second Author"
    assert changed.profile.revision == 2
    assert changed.profile.created_at == first.profile.created_at
    assert store.load() == changed


def test_stale_expected_record_and_competing_creation_refuse(tmp_path: Path) -> None:
    store = _store(tmp_path)
    initial = store.create("One")
    with pytest.raises(TeacherAttributionConflictError):
        _store(tmp_path).create("Two")
    _store(tmp_path).update_display_name(initial, "Two")
    with pytest.raises(TeacherAttributionConflictError):
        store.update_display_name(initial, "Three")
    with pytest.raises(TeacherAttributionConflictError):
        store.reset(initial, confirmed=True)
    assert store.load().profile.display_name == "Two"  # type: ignore[union-attr]


def test_confirmation_is_mandatory_for_identity_reset_and_actor_replace(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    initial = store.create("One")
    with pytest.raises(TeacherAttributionValidationError):
        store.replace_identity(initial, display_name="Two")
    with pytest.raises(TeacherAttributionValidationError):
        store.reset(initial)
    assert store.load() == initial
    store.reset(initial, confirmed=True)
    assert store.load() is None
    assert not store.profile_path.exists()
    assert store.directory.exists()  # existing lock file is safe and not a stale lock


@pytest.mark.parametrize(
    "invalid",
    ["", "  First", "Last  ", "a" * 161, "a\nb", "bad/name", "bad\\name", "e\u0301"],
)
def test_invalid_display_names_do_not_create_settings(
    tmp_path: Path, invalid: str
) -> None:
    store = _store(tmp_path)
    with pytest.raises(TeacherAttributionValidationError):
        store.create(invalid)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("invalid", ["", "with spaces", "../teacher", "x" * 129])
def test_invalid_actor_identifiers_do_not_create_settings(
    tmp_path: Path, invalid: str
) -> None:
    store = _store(tmp_path)
    with pytest.raises(TeacherAttributionValidationError):
        store.create("Synthetic Teacher", actor_id=invalid)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "raw",
    [
        b"not json",
        b"{}",
        b'{"revision":1,"revision":2}',
        b"{" + b"x" * 5000 + b"}",
    ],
)
def test_corrupt_duplicate_missing_and_oversized_settings_fail_closed(
    tmp_path: Path, raw: bytes
) -> None:
    store = _store(tmp_path)
    _write_bad(store, raw)
    with pytest.raises(TeacherAttributionValidationError):
        store.load()
    assert store.profile_path.read_bytes() == raw


def test_unknown_schema_and_unexpected_field_are_not_accepted(tmp_path: Path) -> None:
    store = _store(tmp_path)
    original = store.create("One")
    data = json.loads(store.profile_path.read_text(encoding="utf-8"))
    for key, value in (("schema_version", 999), ("extra_field", "unexpected")):
        edited = {**data, key: value}
        raw = json.dumps(edited).encode()
        store.profile_path.write_bytes(raw)
        with pytest.raises(TeacherAttributionValidationError):
            store.load()
        assert store.profile_path.read_bytes() == raw
    assert original.profile.actor_id == "teacher-generated-1"


def test_profile_is_private_on_posix(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store.create("One")
    if os.name != "nt":
        assert stat.S_IMODE(store.directory.stat().st_mode) & 0o077 == 0
        assert stat.S_IMODE(store.profile_path.stat().st_mode) & 0o077 == 0
        store.profile_path.chmod(0o644)
        with pytest.raises(TeacherAttributionStorageError):
            store.load()


def test_symlink_and_nonregular_targets_are_refused(tmp_path: Path) -> None:
    store = _store(tmp_path)
    target = tmp_path / "foreign.json"
    target.write_text("not a profile", encoding="utf-8")
    store.directory.mkdir(mode=0o700)
    try:
        store.profile_path.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks unsupported in this environment")
    with pytest.raises(TeacherAttributionStorageError):
        store.load()
    with pytest.raises(TeacherAttributionStorageError):
        store.create("One")
    assert target.read_text(encoding="utf-8") == "not a profile"


def test_config_root_symlink_and_relative_root_refuse(tmp_path: Path) -> None:
    store = ConcordTeacherAttributionStore(config_directory=Path("relative"))
    with pytest.raises(TeacherAttributionStorageError):
        store.load()
    foreign = tmp_path / "real"
    foreign.mkdir()
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(foreign, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks unsupported in this environment")
    with pytest.raises(TeacherAttributionStorageError):
        ConcordTeacherAttributionStore(config_directory=alias).load()


def test_atomic_replace_failure_preserves_original_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = _store(tmp_path)
    initial = store.create("One")
    before = store.profile_path.read_bytes()

    def fail_replace(_a: object, _b: object) -> None:
        raise OSError("synthetic replacement refusal")

    monkeypatch.setattr(attribution.os, "replace", fail_replace)
    with pytest.raises(TeacherAttributionStorageError):
        store.update_display_name(initial, "Two")
    assert store.profile_path.read_bytes() == before
    assert sorted(x.name for x in store.directory.iterdir()) == [
        ".teacher-attribution-v1.lock",
        "teacher-attribution-v1.json",
    ]


def test_provider_temporary_identity_never_modifies_saved_default(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path)
    saved = store.create("Primary")
    override = ConcordTeacherAttributionProvider.temporary_override(
        actor_id="teacher-alt-9", display_name="Temporary Author"
    )
    assert override.source == "temporary"
    assert override.workflow_actor().actor_id == "teacher-alt-9"
    assert (
        ConcordTeacherAttributionProvider(store).resolve().actor_id
        == saved.profile.actor_id
    )
    assert store.load() == saved


def test_provider_does_not_change_core_or_meridian_neighbor_file(
    tmp_path: Path,
) -> None:
    config = tmp_path / "config.json"
    config.write_text('{"workspace_root":"synthetic"}', encoding="utf-8")
    meridian = tmp_path / "meridian"
    meridian.mkdir()
    neighbor = meridian / "teacher-profile-v1.json"
    neighbor.write_bytes(b"sentinel")
    before = config.read_bytes(), neighbor.read_bytes()
    _store(tmp_path).create("Synthetic")
    assert (config.read_bytes(), neighbor.read_bytes()) == before


def test_invalid_or_naive_clock_is_rejected_without_profile_content(
    tmp_path: Path,
) -> None:
    store = ConcordTeacherAttributionStore(
        config_directory=tmp_path,
        clock=lambda: datetime(2026, 11, 8),
    )
    with pytest.raises(TeacherAttributionValidationError):
        store.create("Synthetic")
    assert store.load() is None


def test_non_utc_clock_is_saved_as_canonical_utc(tmp_path: Path) -> None:
    def clock() -> datetime:
        return datetime(2026, 11, 8, 16, tzinfo=UTC) + timedelta(hours=0)

    store = ConcordTeacherAttributionStore(config_directory=tmp_path, clock=clock)
    saved = store.create("Synthetic")
    assert saved.profile.created_at == "2026-11-08T16:00:00+00:00"
    assert store.load() == saved
