from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

import concord.storage as storage_module
from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationIntegrityError,
    _managed_activity_registration_context_from_verified_activity,
)
from concord.model_conversion import record_from_dict
from concord.models import Activity, Session
from concord.storage import commit_record_batch
from concord.workflows.activity_attention import inspect_activity_attention

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "evidence_only_activity.json"
)


def _workspace(tmp_path: Path) -> tuple[Path, Activity]:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    activity = record_from_dict("activity", fixture["records"][0]["body"])
    session = record_from_dict("session", fixture["records"][1]["body"])
    assert isinstance(activity, Activity)
    assert isinstance(session, Session)
    commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
    )
    return root, activity


def test_inactive_share_keeps_attention_at_one_verified_graph_load(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, activity = _workspace(tmp_path)

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

    result = inspect_activity_attention(
        activity.class_reference.record_id,
        activity.activity_id,
        workspace_root=root,
    )

    assert result.items == ()
    assert calls == {"chain": 1, "graph": 1, "validate": 1}


def test_verified_registration_context_rejects_wrong_work_identity(
    tmp_path: Path,
) -> None:
    root, activity = _workspace(tmp_path)
    wrong_work = ModuleWorkRef("concord", "class-1", "other-activity")

    with pytest.raises(
        ConcordAcademicWorkRegistrationIntegrityError,
        match="identity disagrees",
    ):
        _managed_activity_registration_context_from_verified_activity(
            root,
            wrong_work,
            activity,
            1,
        )
