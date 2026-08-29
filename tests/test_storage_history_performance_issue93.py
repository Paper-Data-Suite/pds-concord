from __future__ import annotations

import json
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
from concord.storage import commit_record_batch, list_work_snapshots
from concord.storage_errors import ConcordStorageIntegrityError
from concord.storage_paths import snapshot_path

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


def _five_snapshots(root: Path, activity: Activity, session: Session) -> None:
    result = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    for revision in range(2, 6):
        result = commit_record_batch(
            root,
            activity.work_reference,
            (replace(session, notes=f"Synthetic revision {revision}."),),
            expected_snapshot_revision=result.snapshot_revision,
        )
    assert result.snapshot_revision == 5


def test_list_work_snapshots_parses_each_snapshot_once(
    storage_case: tuple[Path, Activity, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, activity, session = storage_case
    _five_snapshots(root, activity, session)

    original = storage_module._parse
    parsed_snapshot_revisions: list[int] = []

    def counted(path: Path, parser: Any, *, missing: bool = False) -> Any:
        if path.parent == snapshot_path(
            root,
            activity.work_reference,
            1,
        ).parent:
            parsed_snapshot_revisions.append(int(path.stem))
        return original(path, parser, missing=missing)

    monkeypatch.setattr(storage_module, "_parse", counted)

    assert list_work_snapshots(root, activity.work_reference) == (1, 2, 3, 4, 5)
    assert parsed_snapshot_revisions == [1, 2, 3, 4, 5]


def test_list_work_snapshots_still_rejects_predecessor_digest_corruption(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _five_snapshots(root, activity, session)

    predecessor = snapshot_path(root, activity.work_reference, 3)
    predecessor.write_bytes(predecessor.read_bytes() + b"\n")

    with pytest.raises(
        ConcordStorageIntegrityError,
        match="snapshot predecessor digest mismatch",
    ):
        list_work_snapshots(root, activity.work_reference)


def test_list_work_snapshots_still_rejects_noncontiguous_history(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _five_snapshots(root, activity, session)

    snapshot_path(root, activity.work_reference, 4).unlink()

    with pytest.raises(
        ConcordStorageIntegrityError,
        match="noncontiguous",
    ):
        list_work_snapshots(root, activity.work_reference)
