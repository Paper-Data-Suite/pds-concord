"""#142 Slice 6B reader qualification with actual disposable workspaces."""

from __future__ import annotations

from pathlib import Path

import pytest
from test_issue142_slice6b_real_score_continuation import (
    ACTIVITY,
    ARTIFACT,
    CLASS,
    WORK,
    _setup_reviewed,
)
from test_workflow_artifact_assembly import _prepare, _workspace

import concord.workflows.artifact as artifact_reader
from concord.storage import list_work_snapshots
from concord.storage_errors import ConcordStorageValidationError
from concord.workflows.artifact import (
    list_artifact_scan_occurrences,
    list_artifacts,
    show_artifact,
)
from concord.workflows.teacher_artifact_choices import list_teacher_artifact_choices


def test_standards_backed_public_artifact_readers_use_canonical_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _standards = _setup_reviewed(tmp_path, monkeypatch)
    before = list_work_snapshots(root, WORK)
    (artifact,) = list_artifacts(CLASS, ACTIVITY, workspace_root=root)
    detail = show_artifact(CLASS, ACTIVITY, ARTIFACT, workspace_root=root)
    (choice,) = list_teacher_artifact_choices(
        CLASS,
        ACTIVITY,
        expected_snapshot_revision=artifact.snapshot_revision,
        workspace_root=root,
    )
    (scan,) = list_artifact_scan_occurrences(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert artifact.artifact_instance_id == ARTIFACT
    assert detail.summary == artifact
    assert choice.summary == artifact
    assert artifact.current_author_count == 1
    assert artifact.current_subject_count == 1
    assert artifact.returned_required_page_count == 1
    assert scan.artifact_page_id == "page-1"
    assert list_work_snapshots(root, WORK) == before


def test_missing_standards_context_fails_closed_for_mixed_readers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _standards = _setup_reviewed(tmp_path, monkeypatch)
    before = list_work_snapshots(root, WORK)
    monkeypatch.setattr(
        artifact_reader, "load_workspace_standards_library", lambda _root: None
    )
    with pytest.raises(ConcordStorageValidationError, match="standards_library"):
        list_artifacts(CLASS, ACTIVITY, workspace_root=root)
    with pytest.raises(ConcordStorageValidationError, match="standards_library"):
        list_teacher_artifact_choices(CLASS, ACTIVITY, workspace_root=root)
    assert list_work_snapshots(root, WORK) == before


def test_evidence_only_readers_do_not_require_a_standards_library(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _prepare(root)
    (artifact,) = list_artifacts("class-1", "activity-1", workspace_root=root)
    (choice,) = list_teacher_artifact_choices(
        "class-1", "activity-1", workspace_root=root
    )
    assert choice.summary == artifact
    assert artifact.artifact_instance_id == "artifact-1"
