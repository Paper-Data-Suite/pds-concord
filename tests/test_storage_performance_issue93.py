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


def _three_snapshots(root: Path, activity: Activity, session: Session) -> None:
    first = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    second_session = replace(session, notes="Synthetic revision two.")
    second = commit_record_batch(
        root,
        activity.work_reference,
        (second_session,),
        expected_snapshot_revision=first.snapshot_revision,
    )
    third_session = replace(session, notes="Synthetic revision three.")
    commit_record_batch(
        root,
        activity.work_reference,
        (third_session,),
        expected_snapshot_revision=second.snapshot_revision,
    )


def test_current_graph_materializes_verified_state_once(
    storage_case: tuple[Path, Activity, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)

    original_chain = storage_module._load_snapshot_chain
    original_graph = storage_module._validated_snapshot_graph
    original_validate = storage_module.validate_record_graph
    calls = {"chain": 0, "graph": 0, "validate": 0}

    def counted_chain(*args: Any, **kwargs: Any) -> Any:
        calls["chain"] += 1
        return original_chain(*args, **kwargs)

    def counted_graph(*args: Any, **kwargs: Any) -> Any:
        calls["graph"] += 1
        return original_graph(*args, **kwargs)

    def counted_validate(*args: Any, **kwargs: Any) -> Any:
        calls["validate"] += 1
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(storage_module, "_load_snapshot_chain", counted_chain)
    monkeypatch.setattr(storage_module, "_validated_snapshot_graph", counted_graph)
    monkeypatch.setattr(storage_module, "validate_record_graph", counted_validate)

    loaded = load_current_record_graph(root, activity.work_reference)

    assert loaded.snapshot_revision == 3
    assert calls == {"chain": 1, "graph": 1, "validate": 1}


def test_current_graph_still_rejects_predecessor_digest_corruption(
    storage_case: tuple[Path, Activity, Session],
) -> None:
    root, activity, session = storage_case
    _three_snapshots(root, activity, session)

    predecessor = snapshot_path(root, activity.work_reference, 1)
    predecessor.write_bytes(predecessor.read_bytes() + b"\n")

    with pytest.raises(
        ConcordStorageIntegrityError,
        match="snapshot predecessor digest mismatch",
    ):
        load_current_record_graph(root, activity.work_reference)
