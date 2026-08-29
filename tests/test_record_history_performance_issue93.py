from __future__ import annotations

import json
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.workspace import ensure_workspace_root

import concord.storage as storage_module
from concord.model_conversion import record_from_dict
from concord.models import Activity, Session
from concord.storage import commit_record_batch, list_record_identities
from concord.storage_errors import ConcordStorageReadError
from concord.storage_paths import record_revision_path

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "evidence_only_activity.json"
)


@pytest.fixture
def storage_case(tmp_path: Path) -> tuple[Path, Activity, Session]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    activity = record_from_dict("activity", fixture["records"][0]["body"])
    session = record_from_dict("session", fixture["records"][1]["body"])
    assert isinstance(activity, Activity)
    assert isinstance(session, Session)
    return root, activity, session


def _three_snapshots(root: Path, activity: Activity, session: Session) -> None:
    result = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    for revision in range(2, 4):
        result = commit_record_batch(
            root,
            activity.work_reference,
            (replace(session, notes=f"Synthetic revision {revision}."),),
            expected_snapshot_revision=result.snapshot_revision,
        )
    assert result.snapshot_revision == 3


def test_write_history_loads_each_record_revision_once(
    storage_case: tuple[Path, Activity, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)
    _, current_snapshot, _, _ = storage_module._load_current_snapshot_state(
        root,
        activity.work_reference,
    )

    original = storage_module.load_record_revision
    calls: list[tuple[str, str, int]] = []

    def counted(
        workspace_root: str | Path,
        work: Any,
        record_kind: str,
        record_id: str,
        record_revision: int,
    ) -> Any:
        calls.append((record_kind, record_id, record_revision))
        return original(
            workspace_root,
            work,
            record_kind,
            record_id,
            record_revision,
        )

    monkeypatch.setattr(storage_module, "load_record_revision", counted)

    storage_module._validate_canonical_write_history(
        root,
        activity.work_reference,
        current_snapshot,
    )

    expected = {
        ("activity", activity.activity_id, 1),
        ("session", session.session_id, 1),
        ("session", session.session_id, 2),
        ("session", session.session_id, 3),
    }
    assert set(calls) == expected
    assert Counter(calls) == Counter({item: 1 for item in expected})


def test_public_record_identity_listing_preserves_validation(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)

    assert list_record_identities(root, activity.work_reference) == (
        ("activity", activity.activity_id),
        ("session", session.session_id),
    )

    historical = record_revision_path(
        root,
        activity.work_reference,
        "session",
        session.session_id,
        1,
    )
    historical.write_bytes(b"{not-json")

    with pytest.raises(ConcordStorageReadError):
        list_record_identities(root, activity.work_reference)
