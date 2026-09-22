from __future__ import annotations

import hashlib
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
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

import concord.storage as storage_module
from concord.model_conversion import record_from_dict
from concord.models import Activity, Session
from concord.storage import (
    commit_record_batch,
    load_current_record_graph,
    load_current_snapshot_graph,
)
from concord.storage_errors import (
    ConcordStorageIntegrityError,
    ConcordStorageValidationError,
)
from concord.workflows.activity import create_activity_context, show_activity
from concord.workflows.models import CreateActivityContextRequest, WorkflowActor

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "native_records"
    / "evidence_only_activity.json"
)


def _workspace(tmp_path: Path, class_id: str = "class-1") -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        class_id,
        "2026-2027",
        created_at=datetime(2026, 9, 21, tzinfo=timezone.utc),
    )
    write_class_metadata_for_class(root, metadata)
    return root


def _evidence_only_activity(root: Path) -> tuple[Activity, Session]:
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
    return activity, session


def _three_snapshots(
    root: Path,
    activity: Activity,
    session: Session,
) -> None:
    second = commit_record_batch(
        root,
        activity.work_reference,
        (replace(session, notes="Issue 104 revision two."),),
        expected_snapshot_revision=1,
    )
    commit_record_batch(
        root,
        activity.work_reference,
        (replace(session, notes="Issue 104 revision three."),),
        expected_snapshot_revision=second.snapshot_revision,
    )


def _standards_library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="standard-1",
                code="S1",
                source="synthetic",
                short_name="Standard 1",
                description="Synthetic standard one.",
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-1",
                standards=("standard-1",),
                source="synthetic",
                title="Synthetic profile",
            ),
        ),
    )


def _fingerprint(root: Path) -> tuple[tuple[str, int, str], ...]:
    rows: list[tuple[str, int, str]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        data = path.read_bytes()
        rows.append(
            (
                path.relative_to(root).as_posix(),
                len(data),
                hashlib.sha256(data).hexdigest(),
            )
        )
    return tuple(rows)


def test_show_activity_materializes_one_exact_current_graph(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    activity, session = _evidence_only_activity(root)
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

    detail = show_activity(
        activity.class_reference.record_id,
        activity.activity_id,
        workspace_root=root,
    )

    assert detail.summary.activity_id == activity.activity_id
    assert detail.summary.title == activity.title
    assert detail.summary.status == activity.status
    assert detail.summary.scoring_orientation == activity.scoring_orientation
    assert detail.summary.session_count == 1
    assert detail.summary.group_count == 0
    assert detail.summary.snapshot_revision == 3
    assert detail.description == activity.description
    assert detail.activity_type == activity.activity_type
    assert calls == {"chain": 1, "graph": 1, "validate": 1}


def test_current_snapshot_graph_is_structural_and_standards_neutral(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path, "class-standards")
    library = _standards_library()
    result = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-standards",
            activity_id="standards-activity",
            title="Standards Activity",
            activity_type="project",
            scoring_orientation="standards_based",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
            standards_profile_id="profile-1",
            focus_standard_ids=("standard-1",),
        ),
        workspace_root=root,
        standards_library=library,
    )

    work = ModuleWorkRef("concord", "class-standards", "standards-activity")
    loaded = load_current_snapshot_graph(root, work)
    assert loaded.snapshot_revision == result.commit.snapshot_revision

    detail = show_activity(
        "class-standards",
        "standards-activity",
        workspace_root=root,
    )
    assert detail.summary.scoring_orientation == "standards_based"

    with pytest.raises(
        ConcordStorageValidationError,
        match="standards_library is required",
    ):
        load_current_record_graph(root, work)


def test_show_activity_does_not_invoke_standards_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    activity, _ = _evidence_only_activity(root)

    def unexpected(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "show_activity must not add a standards-library requirement"
        )

    monkeypatch.setattr(
        storage_module,
        "_validate_loaded_graph_standards",
        unexpected,
    )

    detail = show_activity(
        activity.class_reference.record_id,
        activity.activity_id,
        workspace_root=root,
    )
    assert detail.summary.activity_id == activity.activity_id


def test_show_activity_still_fails_closed_on_predecessor_corruption(
    tmp_path: Path,
) -> None:
    from concord.storage_paths import snapshot_path

    root = _workspace(tmp_path)
    activity, session = _evidence_only_activity(root)
    _three_snapshots(root, activity, session)

    predecessor = snapshot_path(root, activity.work_reference, 1)
    predecessor.write_bytes(predecessor.read_bytes() + b"\n")

    with pytest.raises(
        ConcordStorageIntegrityError,
        match="snapshot predecessor digest mismatch",
    ):
        show_activity(
            activity.class_reference.record_id,
            activity.activity_id,
            workspace_root=root,
        )


def test_show_activity_read_context_is_read_only(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    activity, session = _evidence_only_activity(root)
    _three_snapshots(root, activity, session)
    before = _fingerprint(root)

    show_activity(
        activity.class_reference.record_id,
        activity.activity_id,
        workspace_root=root,
    )

    assert _fingerprint(root) == before
