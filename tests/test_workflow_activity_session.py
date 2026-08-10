from __future__ import annotations

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

from concord.storage import (
    list_record_revisions,
    list_work_snapshots,
    load_current_record_graph,
)
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStorageValidationError,
)
from concord.storage_paths import current_snapshot_path
from concord.workflows import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    CreateActivityContextRequest,
    CreateSessionRequest,
    UpdateActivityRequest,
    UpdateSessionRequest,
    WorkflowActor,
    create_activity_context,
    create_session,
    list_activities,
    list_available_classes,
    list_sessions,
    show_activity,
    show_session,
    update_activity,
    update_session,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 14, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


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


def _workspace_with_class(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(1),
    )
    write_class_metadata_for_class(root, metadata)
    return root


def _create_request(**overrides: object) -> CreateActivityContextRequest:
    values: dict[str, object] = {
        "class_id": "class-1",
        "activity_id": "activity-1",
        "title": "Synthetic Activity",
        "activity_type": "socratic_seminar",
        "scoring_orientation": "evidence_only",
        "session_id": "session-1",
        "actor": _actor(),
        "session_label": "Opening Session",
    }
    values.update(overrides)
    return CreateActivityContextRequest(**values)  # type: ignore[arg-type]


def test_read_only_listing_does_not_create_workspace(tmp_path: Path) -> None:
    root = tmp_path / "absent-workspace"
    assert list_available_classes(root) == ()
    assert list_activities(workspace_root=root) == ()
    assert not root.exists()


def test_mutating_bootstrap_creates_workspace_before_missing_class_error(
    tmp_path: Path,
) -> None:
    root = tmp_path / "new-workspace"
    with pytest.raises(ConcordWorkflowNotFoundError):
        create_activity_context(
            _create_request(),
            workspace_root=root,
            clock=lambda: _clock(2),
        )
    assert (root / ".pds" / "workspace.json").is_file()
    assert (root / "classes").is_dir()


def test_class_listing_uses_core_metadata(tmp_path: Path) -> None:
    root = _workspace_with_class(tmp_path)
    classes = list_available_classes(root)
    assert len(classes) == 1
    assert classes[0].class_id == "class-1"
    assert classes[0].school_year == "2026-2027"


def test_create_activity_context_commits_activity_and_first_session_atomically(
    tmp_path: Path,
) -> None:
    root = _workspace_with_class(tmp_path)
    result = create_activity_context(
        _create_request(),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    assert result.commit.snapshot_revision == 1
    assert not result.commit.no_op
    assert {item.record_kind for item in result.commit.changed_records} == {
        "activity",
        "session",
    }
    loaded = load_current_record_graph(root, result.commit.work)
    assert len(loaded.graph.activities) == 1
    assert len(loaded.graph.sessions) == 1
    assert loaded.graph.sessions[0].session_id == "session-1"


def test_standards_activity_requires_library_before_pointer_publication(
    tmp_path: Path,
) -> None:
    root = _workspace_with_class(tmp_path)
    request = _create_request(
        scoring_orientation="standards_based",
        standards_profile_id="profile-1",
        focus_standard_ids=("standard-1",),
    )
    with pytest.raises(ConcordStorageValidationError):
        create_activity_context(
            request,
            workspace_root=root,
            clock=lambda: _clock(2),
        )
    expected_pointer = current_snapshot_path(
        root,
        ModuleWorkRef(
            module_id="concord",
            class_id="class-1",
            work_id="activity-1",
        ),
    )
    assert not expected_pointer.exists()


def test_standards_activity_commits_with_explicit_library(tmp_path: Path) -> None:
    root = _workspace_with_class(tmp_path)
    result = create_activity_context(
        _create_request(
            scoring_orientation="standards_based",
            standards_profile_id="profile-1",
            focus_standard_ids=("standard-1",),
        ),
        workspace_root=root,
        standards_library=_standards_library(),
        clock=lambda: _clock(2),
    )
    assert result.commit.snapshot_revision == 1
    # Compact read paths do not require the standards library merely to summarize.
    summaries = list_activities(workspace_root=root, class_id="class-1")
    assert summaries[0].scoring_orientation == "standards_based"


def test_activity_show_and_noop_update_do_not_advance_snapshot(tmp_path: Path) -> None:
    root = _workspace_with_class(tmp_path)
    create_activity_context(
        _create_request(),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    detail = show_activity("class-1", "activity-1", workspace_root=root)
    assert detail.summary.session_count == 1
    assert detail.summary.group_count == 0

    result = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=1,
            actor=_actor(),
            title="Synthetic Activity",
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    assert result.commit.no_op
    assert result.commit.snapshot_revision == 1
    assert list_work_snapshots(root, result.commit.work) == (1,)


def test_activity_update_records_updated_provenance_and_stale_guard(
    tmp_path: Path,
) -> None:
    root = _workspace_with_class(tmp_path)
    created = create_activity_context(
        _create_request(),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    updated = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            title="Revised Synthetic Activity",
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    assert updated.commit.snapshot_revision == 2
    loaded = load_current_record_graph(root, updated.commit.work)
    activity = loaded.graph.activities[0]
    assert activity.title == "Revised Synthetic Activity"
    assert activity.updated_provenance is not None
    assert activity.updated_provenance.timestamp == _clock(3).isoformat()

    with pytest.raises(ConcordStorageConflictError):
        update_activity(
            UpdateActivityRequest(
                class_id="class-1",
                activity_id="activity-1",
                expected_snapshot_revision=1,
                actor=_actor(),
                title="Stale update",
            ),
            workspace_root=root,
            clock=lambda: _clock(4),
        )


def test_session_create_list_show_update_and_history(tmp_path: Path) -> None:
    root = _workspace_with_class(tmp_path)
    created = create_activity_context(
        _create_request(),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    added = create_session(
        CreateSessionRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-2",
            sequence=2,
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            label="Second Session",
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    assert added.commit.snapshot_revision == 2
    sessions = list_sessions("class-1", "activity-1", workspace_root=root)
    assert [item.session_id for item in sessions] == ["session-1", "session-2"]
    assert show_session(
        "class-1", "activity-1", "session-2", workspace_root=root
    ).label == "Second Session"

    revised = update_session(
        UpdateSessionRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-2",
            expected_snapshot_revision=2,
            actor=_actor(),
            notes="Synthetic follow-up notes.",
            status="active",
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert revised.commit.snapshot_revision == 3
    current = show_session(
        "class-1", "activity-1", "session-2", workspace_root=root
    )
    assert current.status == "active"
    assert current.notes == "Synthetic follow-up notes."
    assert list_record_revisions(
        root,
        revised.commit.work,
        "session",
        "session-2",
    ) == (1, 2)



def test_create_session_rejects_existing_identity(tmp_path: Path) -> None:
    root = _workspace_with_class(tmp_path)
    created = create_activity_context(
        _create_request(),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    with pytest.raises(ConcordWorkflowConflictError):
        create_session(
            CreateSessionRequest(
                class_id="class-1",
                activity_id="activity-1",
                session_id="session-1",
                sequence=2,
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(3),
        )
    assert list_work_snapshots(root, created.commit.work) == (1,)

def test_duplicate_session_sequence_is_rejected_without_pointer_advance(
    tmp_path: Path,
) -> None:
    root = _workspace_with_class(tmp_path)
    created = create_activity_context(
        _create_request(),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    with pytest.raises(ConcordStorageValidationError):
        create_session(
            CreateSessionRequest(
                class_id="class-1",
                activity_id="activity-1",
                session_id="session-duplicate-sequence",
                sequence=1,
                expected_snapshot_revision=created.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
            clock=lambda: _clock(3),
        )
    assert list_work_snapshots(root, created.commit.work) == (1,)


def test_show_missing_activity_or_session_is_workflow_not_found(tmp_path: Path) -> None:
    root = _workspace_with_class(tmp_path)
    with pytest.raises(ConcordWorkflowNotFoundError):
        show_activity("class-1", "missing-activity", workspace_root=root)
    with pytest.raises(ConcordWorkflowNotFoundError):
        show_session(
            "class-1",
            "missing-activity",
            "missing-session",
            workspace_root=root,
        )
