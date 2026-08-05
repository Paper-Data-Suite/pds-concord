from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

import concord.storage as storage_module
import concord.storage_catalog as storage_catalog_module
from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import Activity, Session
from concord.storage import (
    commit_record_batch,
    list_record_revisions,
    list_work_snapshots,
    load_current_record_graph,
    load_current_snapshot,
    load_record_revision,
    load_work_snapshot,
)
from concord.storage_catalog import (
    _open_verified,
    query_catalog_records,
    rebuild_catalog,
)
from concord.storage_diagnostics import (
    collect_storage_issues,
    inspect_catalog_status,
    inspect_storage_locks,
    validate_storage,
)
from concord.storage_errors import (
    ConcordCatalogBuildError,
    ConcordCatalogIntegrityError,
    ConcordStorageConflictError,
    ConcordStorageIntegrityError,
    ConcordStoragePartialSuccessError,
    ConcordStorageValidationError,
    ConcordStorageWriteError,
)
from concord.storage_models import (
    CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
    CONCORD_STORAGE_SCHEMA_VERSION,
    ConcordCurrentSnapshot,
    ConcordRecordRevision,
    ConcordWorkSnapshot,
)
from concord.storage_paths import (
    catalog_lock_path,
    catalog_path,
    current_snapshot_path,
    record_revision_path,
    snapshot_path,
    write_lock_path,
)
from concord.storage_serialization import (
    serialize,
    snapshot_from_dict,
    strict_json_loads,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "evidence_only_activity.json"
)
STANDARDS_FIXTURE = FIXTURE.with_name("standards_activity.json")


def _commit_initial(root: Path, activity: Activity, session: Session) -> None:
    commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )


def _three_snapshots(root: Path, activity: Activity, session: Session) -> Session:
    _commit_initial(root, activity, session)
    second_session = replace(session, notes="Synthetic revision two.")
    commit_record_batch(
        root,
        activity.work_reference,
        (second_session,),
        expected_snapshot_revision=1,
    )
    third_session = replace(session, notes="Synthetic revision three.")
    commit_record_batch(
        root,
        activity.work_reference,
        (third_session,),
        expected_snapshot_revision=2,
    )
    return third_session


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink creation is unavailable: {error}")


def _standards_library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="standard-1",
                code="SYN.1",
                source="synthetic",
                short_name="Synthetic standard",
                description="Privacy-safe standard used only by tests.",
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-1",
                standards=("standard-1",),
                title="Synthetic standards profile",
            ),
        ),
    )


@pytest.fixture
def storage_case(tmp_path: Path) -> tuple[Path, Activity, Session]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    activity = record_from_dict("activity", fixture["records"][0]["body"])
    session = record_from_dict("session", fixture["records"][1]["body"])
    assert isinstance(activity, Activity)
    assert isinstance(session, Session)
    return root, activity, session


def test_initial_commit_and_strict_graph_load(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    result = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    loaded = load_current_record_graph(root, activity.work_reference)
    assert result.snapshot_revision == loaded.snapshot_revision == 1
    assert loaded.graph.activities == (activity,)
    assert loaded.graph.sessions == (session,)
    assert current_snapshot_path(root, activity.work_reference).is_file()


def test_initial_activity_only_is_rejected_before_canonical_writes(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, _ = storage_case
    with pytest.raises(ConcordStorageValidationError):
        commit_record_batch(
            root,
            activity.work_reference,
            (activity,),
            expected_snapshot_revision=None,
        )
    assert not current_snapshot_path(root, activity.work_reference).exists()


def test_revision_history_noop_and_stale_guard(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    first = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    changed = replace(session, notes="Synthetic follow-up note.")
    second = commit_record_batch(
        root,
        activity.work_reference,
        (changed,),
        expected_snapshot_revision=first.snapshot_revision,
    )
    replay = commit_record_batch(
        root,
        activity.work_reference,
        (changed,),
        expected_snapshot_revision=second.snapshot_revision,
    )
    assert second.snapshot_revision == 2
    assert replay.no_op
    assert list_record_revisions(
        root, activity.work_reference, "session", session.session_id
    ) == (1, 2)
    assert list_work_snapshots(root, activity.work_reference) == (1, 2)
    old, _ = load_record_revision(
        root, activity.work_reference, "session", session.session_id, 1
    )
    assert old == session
    with pytest.raises(ConcordStorageConflictError):
        commit_record_batch(
            root,
            activity.work_reference,
            (replace(changed, notes="Another note."),),
            expected_snapshot_revision=1,
        )


def test_catalog_rebuild_is_derived_and_supports_history(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    rebuild_catalog(root, activity.work_reference)
    current = query_catalog_records(root, activity.work_reference, snapshot_revision=1)
    assert {(row.record_kind, row.record_id) for row in current} == {
        ("activity", activity.activity_id),
        ("session", session.session_id),
    }


def test_record_digest_tampering_is_rejected(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    path = record_revision_path(
        root, activity.work_reference, "session", session.session_id, 1
    )
    path.write_bytes(path.read_bytes().replace(b"active", b"planned"))
    with pytest.raises(Exception, match="digest mismatch"):
        load_current_record_graph(root, activity.work_reference)


def test_newer_orphan_record_revision_blocks_commit(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    revision_one = record_revision_path(
        root, activity.work_reference, "session", session.session_id, 1
    )
    revision_three = record_revision_path(
        root, activity.work_reference, "session", session.session_id, 3
    )
    revision_three.write_bytes(revision_one.read_bytes())

    with pytest.raises(ConcordStorageIntegrityError):
        commit_record_batch(
            root,
            activity.work_reference,
            (replace(session, notes="Blocked revision."),),
            expected_snapshot_revision=1,
        )

    assert load_current_snapshot(root, activity.work_reference).snapshot_revision == 1
    assert not record_revision_path(
        root, activity.work_reference, "session", session.session_id, 2
    ).exists()


def test_newer_orphan_snapshot_blocks_commit(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    first, _ = load_work_snapshot(root, activity.work_reference, 1)
    orphan = ConcordWorkSnapshot(
        CONCORD_STORAGE_SCHEMA_VERSION,
        "concord_work_snapshot",
        activity.work_reference,
        3,
        2,
        "a" * 64,
        first.records,
    )
    snapshot_path(root, activity.work_reference, 3).write_bytes(serialize(orphan))

    with pytest.raises(ConcordStorageIntegrityError):
        commit_record_batch(
            root,
            activity.work_reference,
            (replace(session, notes="Blocked snapshot."),),
            expected_snapshot_revision=1,
        )

    assert not snapshot_path(root, activity.work_reference, 2).exists()
    assert load_current_snapshot(root, activity.work_reference).snapshot_revision == 1


@pytest.mark.parametrize("orphan_kind", ["record", "snapshot"])
def test_initial_creation_rejects_orphan_canonical_history(
    storage_case: tuple[Path, Activity, Session], orphan_kind: str
) -> None:
    root, activity, session = storage_case
    if orphan_kind == "record":
        envelope = ConcordRecordRevision(
            CONCORD_STORAGE_SCHEMA_VERSION,
            "concord_record_revision",
            activity.work_reference,
            "session",
            session.session_id,
            1,
            CONCORD_NATIVE_RECORD_CONTRACT_VERSION,
            record_to_dict(session),
        )
        path = record_revision_path(
            root, activity.work_reference, "session", session.session_id, 1
        )
    else:
        envelope = ConcordWorkSnapshot(
            CONCORD_STORAGE_SCHEMA_VERSION,
            "concord_work_snapshot",
            activity.work_reference,
            1,
            None,
            None,
            (),
        )
        path = snapshot_path(root, activity.work_reference, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(serialize(envelope))

    with pytest.raises(ConcordStorageIntegrityError):
        commit_record_batch(
            root,
            activity.work_reference,
            (activity, session),
            expected_snapshot_revision=None,
        )
    assert not current_snapshot_path(root, activity.work_reference).exists()


def test_failed_file_fsync_removes_partial_file(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    marker = storage_module.work_marker_path(root, activity.work_reference)
    file_syncs = 0

    def fail_fsync(_descriptor: int) -> None:
        nonlocal file_syncs
        file_syncs += 1
        if file_syncs == 2:
            raise OSError("synthetic file fsync failure")

    monkeypatch.setattr(storage_module.os, "fsync", fail_fsync)
    monkeypatch.setattr(
        storage_module, "_fsync_directory_if_supported", lambda _path: None
    )
    with pytest.raises(Exception, match="could not write"):
        _commit_initial(root, activity, session)
    assert not marker.exists()
    assert not current_snapshot_path(root, activity.work_reference).exists()


def test_failed_partial_file_cleanup_is_reported(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    marker = storage_module.work_marker_path(root, activity.work_reference)
    original_unlink = Path.unlink
    file_syncs = 0

    def fail_fsync(_descriptor: int) -> None:
        nonlocal file_syncs
        file_syncs += 1
        if file_syncs == 2:
            raise OSError("synthetic file fsync failure")

    def selective_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == marker:
            raise OSError("synthetic partial cleanup failure")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(storage_module.os, "fsync", fail_fsync)
    monkeypatch.setattr(
        storage_module, "_fsync_directory_if_supported", lambda _path: None
    )
    monkeypatch.setattr(Path, "unlink", selective_unlink)
    with pytest.raises(ConcordStoragePartialSuccessError) as captured:
        _commit_initial(root, activity, session)
    assert str(marker) in captured.value.durable_paths
    assert captured.value.pointer_published is False


def test_directory_fsync_failure_reports_synchronized_path(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    marker = storage_module.work_marker_path(root, activity.work_reference)

    def fail_directory_sync(path: Path) -> None:
        if path == marker.parent:
            raise OSError("synthetic directory fsync failure")

    monkeypatch.setattr(
        storage_module, "_fsync_directory_if_supported", fail_directory_sync
    )
    with pytest.raises(ConcordStoragePartialSuccessError) as captured:
        _commit_initial(root, activity, session)
    assert marker.exists()
    assert str(marker) in captured.value.durable_paths
    assert captured.value.pointer_published is False


def test_current_pointer_directory_fsync_failure_reports_published_state(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    current = current_snapshot_path(root, activity.work_reference)
    state_syncs = 0

    def fail_current_directory_sync(path: Path) -> None:
        nonlocal state_syncs
        if path != current.parent:
            return
        state_syncs += 1
        if state_syncs == 2:
            raise OSError("synthetic current pointer directory fsync failure")

    with monkeypatch.context() as fault:
        fault.setattr(
            storage_module,
            "_fsync_directory_if_supported",
            fail_current_directory_sync,
        )
        with pytest.raises(ConcordStoragePartialSuccessError) as captured:
            _commit_initial(root, activity, session)

    pointer = load_current_snapshot(root, activity.work_reference)
    assert captured.value.pointer_published is True
    assert captured.value.snapshot_revision == pointer.snapshot_revision == 1
    assert captured.value.snapshot_sha256 == pointer.snapshot_sha256
    graph = load_current_record_graph(root, activity.work_reference).graph
    assert graph.activities == (activity,)
    assert graph.sessions == (session,)


def test_write_lock_content_failure_does_not_leave_lock(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    lock = write_lock_path(root, activity.work_reference)
    current = current_snapshot_path(root, activity.work_reference)

    def fail_lock_content(*_args: object, **_kwargs: object) -> bytes:
        raise OSError("synthetic write lock content failure")

    monkeypatch.setattr(storage_module, "_lock_bytes", fail_lock_content)
    with pytest.raises(ConcordStorageWriteError, match="durably acquire"):
        _commit_initial(root, activity, session)

    assert not lock.exists()
    assert not current.exists()


def test_post_pointer_verification_failure_reports_committed_state(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case

    def fail_verification(*_args: object, **_kwargs: object) -> object:
        raise ConcordStorageIntegrityError("synthetic final verification failure")

    with monkeypatch.context() as fault:
        fault.setattr(storage_module, "load_current_record_graph", fail_verification)
        with pytest.raises(ConcordStoragePartialSuccessError) as captured:
            _commit_initial(root, activity, session)

    current = load_current_snapshot(root, activity.work_reference)
    assert captured.value.pointer_published is True
    assert captured.value.snapshot_revision == current.snapshot_revision == 1
    assert captured.value.snapshot_sha256 == current.snapshot_sha256
    assert load_current_record_graph(root, activity.work_reference).graph.sessions == (
        session,
    )


def test_write_lock_cleanup_failure_after_success_is_partial(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    lock = write_lock_path(root, activity.work_reference)
    original_unlink = Path.unlink

    def selective_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock:
            raise OSError("synthetic lock cleanup failure")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "unlink", selective_unlink)
        with pytest.raises(ConcordStoragePartialSuccessError) as captured:
            _commit_initial(root, activity, session)
    assert captured.value.pointer_published is True
    assert str(lock) in captured.value.durable_paths
    assert load_current_snapshot(root, activity.work_reference).snapshot_revision == 1
    original_unlink(lock)


def test_write_lock_cleanup_failure_after_noop_is_partial(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    lock = write_lock_path(root, activity.work_reference)
    original_unlink = Path.unlink

    def selective_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock:
            raise OSError("synthetic no-op lock cleanup failure")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "unlink", selective_unlink)
        with pytest.raises(ConcordStoragePartialSuccessError) as captured:
            commit_record_batch(
                root,
                activity.work_reference,
                (session,),
                expected_snapshot_revision=1,
            )
    assert captured.value.pointer_published is False
    assert str(lock) in captured.value.durable_paths
    original_unlink(lock)


def test_catalog_excludes_complete_record_bodies(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    path = rebuild_catalog(root, activity.work_reference)
    connection = sqlite3.connect(path)
    try:
        columns = tuple(
            row[1] for row in connection.execute("PRAGMA table_info(record_revisions)")
        )
    finally:
        connection.close()
    assert columns == (
        "record_kind",
        "record_id",
        "record_revision",
        "sha256",
        "relative_path",
    )
    assert "body_json" not in columns
    assert query_catalog_records(root, activity.work_reference, state="current")
    assert (
        query_catalog_records(root, activity.work_reference, state="historical") == ()
    )
    assert query_catalog_records(root, activity.work_reference, state="all")
    assert query_catalog_records(root, activity.work_reference, snapshot_revision=1)


def test_catalog_lock_cleanup_failure_after_install_is_reported(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    lock = catalog_lock_path(root, activity.work_reference)
    original_unlink = Path.unlink

    def selective_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path == lock:
            raise OSError("synthetic catalog lock cleanup failure")
        original_unlink(path, *args, **kwargs)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "unlink", selective_unlink)
        with pytest.raises(ConcordCatalogBuildError, match="installed successfully"):
            rebuild_catalog(root, activity.work_reference)
    assert catalog_path(root, activity.work_reference).is_file()
    _open_verified(root, activity.work_reference).close()
    original_unlink(lock)


def test_catalog_lock_content_failure_does_not_leave_lock(
    storage_case: tuple[Path, Activity, Session], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    lock = catalog_lock_path(root, activity.work_reference)
    catalog = catalog_path(root, activity.work_reference)
    original_canonical_json_bytes = storage_catalog_module.canonical_json_bytes

    def fail_catalog_lock_content(value: object) -> bytes:
        if isinstance(value, dict) and value.get("purpose") == "catalog_rebuild":
            raise OSError("synthetic catalog lock content failure")
        return original_canonical_json_bytes(value)

    monkeypatch.setattr(
        storage_catalog_module,
        "canonical_json_bytes",
        fail_catalog_lock_content,
    )
    with pytest.raises(ConcordCatalogBuildError, match="catalog rebuild failed"):
        rebuild_catalog(root, activity.work_reference)

    assert not lock.exists()
    assert not catalog.exists()


def test_snapshot_predecessor_work_identity_mismatch_is_rejected(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)
    work = activity.work_reference
    second_path = snapshot_path(root, work, 2)
    third_path = snapshot_path(root, work, 3)
    second = snapshot_from_dict(strict_json_loads(second_path.read_bytes()))
    other_work = ModuleWorkRef(
        module_id="concord", class_id="other-class", work_id=work.work_id
    )
    altered_second = replace(second, work=other_work)
    altered_second_bytes = serialize(altered_second)
    second_path.write_bytes(altered_second_bytes)
    third = snapshot_from_dict(strict_json_loads(third_path.read_bytes()))
    third_path.write_bytes(
        serialize(
            replace(
                third,
                previous_snapshot_sha256=hashlib.sha256(
                    altered_second_bytes
                ).hexdigest(),
            )
        )
    )
    with pytest.raises(ConcordStorageIntegrityError, match="predecessor identity"):
        load_work_snapshot(root, work, 3)


def test_snapshot_predecessor_revision_identity_mismatch_is_rejected(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)
    work = activity.work_reference
    second_path = snapshot_path(root, work, 2)
    third_path = snapshot_path(root, work, 3)
    original_third_bytes = third_path.read_bytes()
    second_path.write_bytes(original_third_bytes)
    third = snapshot_from_dict(strict_json_loads(original_third_bytes))
    third_path.write_bytes(
        serialize(
            replace(
                third,
                previous_snapshot_sha256=hashlib.sha256(
                    original_third_bytes
                ).hexdigest(),
            )
        )
    )
    with pytest.raises(ConcordStorageIntegrityError, match="predecessor identity"):
        load_work_snapshot(root, work, 3)


def test_intermediate_snapshot_digest_corruption_is_rejected(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)
    first_path = snapshot_path(root, activity.work_reference, 1)
    first_path.write_bytes(first_path.read_bytes() + b" ")
    with pytest.raises(ConcordStorageIntegrityError, match="predecessor digest"):
        load_work_snapshot(root, activity.work_reference, 3)


def test_symlinked_current_pointer_is_rejected(
    storage_case: tuple[Path, Activity, Session], tmp_path: Path
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    current = current_snapshot_path(root, activity.work_reference)
    external = tmp_path / "external-current.json"
    external.write_bytes(current.read_bytes())
    current.unlink()
    _symlink_or_skip(current, external)
    with pytest.raises(ConcordStorageIntegrityError):
        load_current_snapshot(root, activity.work_reference)


def test_symlinked_write_lock_is_rejected(
    storage_case: tuple[Path, Activity, Session], tmp_path: Path
) -> None:
    root, activity, _ = storage_case
    lock = write_lock_path(root, activity.work_reference)
    lock.parent.mkdir(parents=True, exist_ok=True)
    external = tmp_path / "external-lock.json"
    external.write_text("{}\n", encoding="utf-8")
    _symlink_or_skip(lock, external)
    with pytest.raises(ConcordStorageIntegrityError):
        inspect_storage_locks(root, activity.work_reference)


def test_symlinked_catalog_is_rejected(
    storage_case: tuple[Path, Activity, Session], tmp_path: Path
) -> None:
    root, activity, session = storage_case
    _commit_initial(root, activity, session)
    catalog = rebuild_catalog(root, activity.work_reference)
    external = tmp_path / "external-catalog.sqlite"
    external.write_bytes(catalog.read_bytes())
    catalog.unlink()
    _symlink_or_skip(catalog, external)
    with pytest.raises(ConcordCatalogIntegrityError):
        query_catalog_records(root, activity.work_reference)


def test_broken_symlinked_catalog_is_not_reported_missing(
    storage_case: tuple[Path, Activity, Session], tmp_path: Path
) -> None:
    root, activity, _ = storage_case
    catalog = catalog_path(root, activity.work_reference)
    catalog.parent.mkdir(parents=True, exist_ok=True)
    external = tmp_path / "nonexistent-external-catalog.sqlite"
    _symlink_or_skip(catalog, external)

    assert inspect_catalog_status(root, activity.work_reference) == "corrupt"


def test_storage_validation_accepts_required_standards_context(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, _, _ = storage_case
    fixture = json.loads(STANDARDS_FIXTURE.read_text(encoding="utf-8"))
    records = tuple(
        record_from_dict(envelope["record_kind"], envelope["body"])
        for envelope in fixture["records"]
    )
    activity = next(record for record in records if isinstance(record, Activity))
    library = _standards_library()
    commit_record_batch(
        root,
        activity.work_reference,
        records,
        expected_snapshot_revision=None,
        standards_library=library,
    )

    validate_storage(root, activity.work_reference, standards_library=library)
    without_context = collect_storage_issues(root, activity.work_reference)
    assert "storage.standards_context.required" in {
        issue.code for issue in without_context
    }


def test_graph_diagnostics_preserve_native_issue_identity_and_privacy(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    sensitive_note = "SENSITIVE-NOTE-MUST-NOT-APPEAR"
    _commit_initial(root, activity, replace(session, notes=sensitive_note))
    work = activity.work_reference
    snapshot_file = snapshot_path(root, work, 1)
    snapshot = snapshot_from_dict(strict_json_loads(snapshot_file.read_bytes()))
    activity_only = tuple(
        reference
        for reference in snapshot.records
        if reference.record_kind == "activity"
    )
    altered_snapshot = replace(snapshot, records=activity_only)
    altered_bytes = serialize(altered_snapshot)
    snapshot_file.write_bytes(altered_bytes)
    pointer = ConcordCurrentSnapshot(
        CONCORD_STORAGE_SCHEMA_VERSION,
        "concord_current_snapshot",
        work,
        1,
        hashlib.sha256(altered_bytes).hexdigest(),
    )
    current_snapshot_path(root, work).write_bytes(serialize(pointer))

    issues = collect_storage_issues(root, work)
    graph_issue = next(
        issue for issue in issues if issue.code == "activity.session.required"
    )
    assert graph_issue.record_kind == "activity"
    assert graph_issue.record_id == activity.activity_id
    assert graph_issue.field_path == ("activity_id",)
    rendered = "\n".join(
        f"{issue.code} {issue.message} {issue.related_references}" for issue in issues
    )
    assert sensitive_note not in rendered
    assert "Moderation rationale" not in rendered
    assert "raw evidence" not in rendered
