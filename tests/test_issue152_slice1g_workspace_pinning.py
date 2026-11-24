"""Concord #152 Slice 1G: workspace-pinned routine Score identities."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from test_issue142_slice6b_real_score_continuation import (
    ACTIVITY,
    ARTIFACT,
    CLASS,
    _setup_reviewed,
)

import concord.menu_artifact_scoring as menu
from concord.models import ScoreTargetReference, SubjectReference
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringContext,
    inspect_artifact_routine_scoring,
)
from concord.workflows.errors import ConcordWorkflowConflictError


def _context(root: Path) -> ArtifactRoutineScoringContext:
    return cast(
        ArtifactRoutineScoringContext,
        SimpleNamespace(
            workspace_root=root,
            class_id="class-1",
            activity_id="activity-1",
            snapshot_revision=8,
            snapshot_sha256="expected-snapshot-sha",
            artifact=SimpleNamespace(artifact_instance_id="artifact-1"),
        ),
    )


def _authority(root: Path) -> object:
    return SimpleNamespace(
        root=root,
        class_id="class-1",
        activity_id="activity-1",
        snapshot_revision=8,
        snapshot_sha256="expected-snapshot-sha",
    )


def test_pinned_student_and_subject_names_ignore_switched_active_workspace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    pinned = tmp_path / "school-one"
    context = _context(pinned)
    observed_roots: list[Path] = []

    def name(root: Path, _class: str, _reference: object) -> str:
        observed_roots.append(root)
        return "Alex Example"

    monkeypatch.setattr(menu, "participant_display_label", name)
    monkeypatch.setattr(
        menu, "resolve_read_workspace_root",
        lambda: pytest.fail("Active workspace must not supply pinned labels"),
    )
    activity = cast(
        object, SimpleNamespace(title="Synthetic discussion")
    )
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="private-student-1",
        owning_system="core",
    )
    subject = SubjectReference(
        subject_kind="core_student",
        subject_id="private-student-1",
        owning_system="core",
    )
    assert menu._target_label(activity, context, target) == (
        "Alex Example — student"
    )
    assert menu._subject_label(activity, context, subject) == (
        "Alex Example — student"
    )
    assert observed_roots == [pinned, pinned]


@pytest.mark.parametrize(
    "drift",
    ("workspace", "revision", "digest", "class", "activity"),
)
def test_context_drift_is_rejected_before_teacher_score_selection(
    drift: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    root = tmp_path / "school-one"
    context = cast(object, _context(root))
    if drift == "workspace":
        context.workspace_root = tmp_path / "school-two"
    elif drift == "revision":
        context.snapshot_revision = 9
    elif drift == "digest":
        context.snapshot_sha256 = "another-snapshot"
    elif drift == "class":
        context.class_id = "other-class"
    else:
        context.activity_id = "other-activity"

    activity = SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        title="Synthetic discussion",
        snapshot_revision=8,
    )
    monkeypatch.setattr(menu, "_current_activity", lambda _old: activity)
    monkeypatch.setattr(
        menu, "begin_artifact_write_context",
        lambda *_args, **_kw: _authority(root),
    )
    monkeypatch.setattr(
        menu, "inspect_artifact_routine_scoring",
        lambda *_args, **_kw: context,
    )

    def forbid(*_args: object, **_kwargs: object) -> None:
        pytest.fail("No Score selection, approval, or mutation on context drift")

    monkeypatch.setattr(menu, "_choose_target", forbid)
    monkeypatch.setattr(menu, "confirm_actor_write", forbid)
    monkeypatch.setattr(menu, "record_prepared_routine_score", forbid)

    with pytest.raises(
        ConcordWorkflowConflictError, match="label workspace or Activity snapshot"
    ):
        menu._record_selected_artifact_score(
            activity, "artifact-1", cast(object, SimpleNamespace())
        )


def test_real_inspection_pins_core_label_root_to_canonical_graph(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _standards = _setup_reviewed(tmp_path, monkeypatch)
    current = inspect_artifact_routine_scoring(
        CLASS, ACTIVITY, ARTIFACT, workspace_root=root
    )
    assert current.workspace_root is not None
    assert current.workspace_root.resolve() == root.resolve()

    # Even when active selection later points somewhere else, this read-only
    # label comes from the same root used to inspect Score preparation.
    other = tmp_path / "unrelated-school"
    monkeypatch.setattr(menu, "resolve_read_workspace_root", lambda: other)
    target = ScoreTargetReference(
        target_kind="core_student",
        target_id="student-1",
        owning_system="core",
    )
    label = menu._target_label(
        cast(object, SimpleNamespace(title="Synthetic discussion")),
        current,
        target,
    )
    assert label.endswith(" — student")
    assert "student-1" not in label
