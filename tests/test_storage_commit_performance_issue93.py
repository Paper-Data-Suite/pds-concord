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
from concord.storage import commit_record_batch, load_current_record_graph

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


def test_update_commit_does_not_reload_current_snapshot_for_refs_or_digest(
    storage_case: tuple[Path, Activity, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, activity, session = storage_case
    first = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )

    original = storage_module.load_work_snapshot
    calls: list[int] = []

    def counted(
        workspace_root: str | Path,
        work: Any,
        snapshot_revision: int,
    ) -> Any:
        calls.append(snapshot_revision)
        return original(workspace_root, work, snapshot_revision)

    monkeypatch.setattr(storage_module, "load_work_snapshot", counted)

    updated = commit_record_batch(
        root,
        activity.work_reference,
        (replace(session, notes="Second revision."),),
        expected_snapshot_revision=first.snapshot_revision,
    )

    assert updated.snapshot_revision == 2
    # Slice 5 validates existing snapshot history directly in one linear pass,
    # so load_work_snapshot() is now needed only to verify the newly written
    # revision-2 snapshot. Current refs and predecessor digest still reuse the
    # state already verified by _load_current_snapshot_state().
    assert calls == [2]


def test_update_commit_retains_final_post_publication_graph_verification(
    storage_case: tuple[Path, Activity, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, activity, session = storage_case
    first = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )

    original = storage_module.load_current_record_graph
    calls = 0

    def counted(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(storage_module, "load_current_record_graph", counted)

    result = commit_record_batch(
        root,
        activity.work_reference,
        (replace(session, notes="Verified after publication."),),
        expected_snapshot_revision=first.snapshot_revision,
    )

    assert result.snapshot_revision == 2
    assert calls == 1
    loaded = load_current_record_graph(root, activity.work_reference)
    assert loaded.snapshot_revision == 2
