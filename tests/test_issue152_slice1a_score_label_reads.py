"""#152 Slice 1A: scoring labels use authoritative reads and fail visibly."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import concord.menu_score_teacher_labels as label_menu
import concord.menu_scoring as scoring_menu
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic discussion",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=1,
        snapshot_revision=8,
    )


@pytest.fixture
def authoritative_labels(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[object, list[tuple[str, dict[str, Any]]]]:
    root = tmp_path / "synthetic-workspace"
    library = object()
    calls: list[tuple[str, dict[str, Any]]] = []

    def record(name: str, value: object):
        def reader(*_args: object, **kwargs: Any) -> object:
            calls.append((name, kwargs))
            return value

        return reader

    monkeypatch.setattr(label_menu, "resolve_read_workspace_root", lambda: root)
    monkeypatch.setattr(label_menu, "standards_for_activity", lambda _act: library)
    monkeypatch.setattr(
        label_menu, "list_groups",
        record("groups", (SimpleNamespace(group_id="g-1", label="Cluster One"),)),
    )
    monkeypatch.setattr(
        label_menu, "list_sessions",
        record(
            "sessions",
            (SimpleNamespace(session_id="s-1", sequence=1, label="Seminar"),),
        ),
    )
    monkeypatch.setattr(
        label_menu, "list_teacher_artifact_choices",
        record(
            "artifacts",
            (
                SimpleNamespace(
                    label="Returned discussion",
                    summary=SimpleNamespace(artifact_instance_id="a-1"),
                ),
            ),
        ),
    )
    monkeypatch.setattr(
        label_menu,
        "load_class_roster",
        record("roster", SimpleNamespace(
            students=(SimpleNamespace(student_id="student-1"),),
        )),
    )
    monkeypatch.setattr(
        label_menu, "student_display_name", lambda _student: "Student Example",
    )
    monkeypatch.setattr(
        label_menu, "list_scoring_scales",
        record(
            "scales",
            (SimpleNamespace(scoring_scale_id="scale-1", name="Four levels"),),
        ),
    )
    monkeypatch.setattr(
        label_menu, "list_criterion_sets",
        record(
            "sets", (SimpleNamespace(criterion_set_id="set-1"),),
        ),
    )
    monkeypatch.setattr(
        label_menu, "show_criterion_set",
        record(
            "set detail",
            SimpleNamespace(
                criteria=(SimpleNamespace(
                    criterion_id="criterion-1", label="Discussion",
                ),),
            ),
        ),
    )
    return library, calls


def test_scoring_history_reads_share_exact_workspace_and_core_standards(
    authoritative_labels: tuple[object, list[tuple[str, dict[str, Any]]]],
) -> None:
    library, calls = authoritative_labels
    result = label_menu.build_score_teacher_labels(
        _activity(), include_score_definitions=True
    )
    assert result.target("concord_group", "g-1") == "Cluster One"
    assert result.target("core_student", "student-1") == "Student Example"
    assert result.target("concord_artifact_instance", "a-1") == "Returned discussion"
    assert result.session("s-1") == "Session 1 - Seminar"
    assert result.criterion("criterion-1") == "Discussion"
    assert result.scale("scale-1") == "Four levels"
    assert {name for name, _ in calls} == {
        "groups", "sessions", "artifacts", "roster", "scales", "sets", "set detail"
    }
    workspaces = {
        str(kwargs["workspace_root"])
        for name, kwargs in calls
        if name != "roster"
    }
    assert len(workspaces) == 1
    for name, kwargs in calls:
        if name in {"artifacts", "scales", "sets", "set detail"}:
            assert kwargs["standards_library"] is library
    artifact_kwargs = next(kwargs for name, kwargs in calls if name == "artifacts")
    assert artifact_kwargs["expected_snapshot_revision"] == 8


@pytest.mark.parametrize(
    ("service", "source"),
    (
        ("list_groups", "Cluster Group"),
        ("list_sessions", "Session"),
        ("list_teacher_artifact_choices", "Returned work"),
        ("load_class_roster", "Core student roster"),
        ("list_scoring_scales", "Scoring Scale"),
        ("list_criterion_sets", "Criterion Set"),
        ("show_criterion_set", "Criterion Set"),
    ),
)
def test_failed_canonical_reads_are_not_silently_swallowed(
    monkeypatch: pytest.MonkeyPatch,
    authoritative_labels: tuple[object, list[tuple[str, dict[str, Any]]]],
    service: str,
    source: str,
) -> None:
    def broken(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("private filesystem information")

    monkeypatch.setattr(label_menu, service, broken)
    with pytest.raises(ConcordWorkflowValidationError) as error:
        label_menu.build_score_teacher_labels(
            _activity(), include_score_definitions=True
        )
    assert source in str(error.value)
    assert "no Score was recorded" in str(error.value)
    assert "private filesystem information" not in str(error.value)


def test_stale_work_choice_preserves_conflict_classification(
    monkeypatch: pytest.MonkeyPatch,
    authoritative_labels: tuple[object, list[tuple[str, dict[str, Any]]]],
) -> None:
    def stale(*_args: object, **_kwargs: object) -> None:
        raise ConcordWorkflowConflictError("hidden revision")

    monkeypatch.setattr(label_menu, "list_teacher_artifact_choices", stale)
    with pytest.raises(ConcordWorkflowConflictError, match="Reopen the Activity"):
        label_menu.build_score_teacher_labels(_activity())


def test_score_history_requires_a_selected_workspace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(label_menu, "resolve_read_workspace_root", lambda: None)
    with pytest.raises(ConcordWorkflowValidationError, match="workspace"):
        label_menu.build_score_teacher_labels(
            _activity(), include_score_definitions=True
        )


def test_missing_core_standards_blocks_scoring_label_reads(
    monkeypatch: pytest.MonkeyPatch,
    authoritative_labels: tuple[object, list[tuple[str, dict[str, Any]]]],
) -> None:
    def missing(_activity: ActivitySummary) -> None:
        raise ConcordWorkflowValidationError("Core Standards Library unavailable")

    def forbid(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("no label read after missing required Standards")

    monkeypatch.setattr(label_menu, "standards_for_activity", missing)
    monkeypatch.setattr(label_menu, "list_groups", forbid)
    with pytest.raises(ConcordWorkflowValidationError, match="Standards"):
        label_menu.build_score_teacher_labels(
            _activity(), include_score_definitions=True
        )


def test_scoring_history_menu_displays_failure_before_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: list[tuple[str, tuple[str, ...]]] = []

    # The synthetic Activity is not stored; this case isolates label
    # failure after successful Activity refresh, not missing-Activity handling.
    monkeypatch.setattr(scoring_menu, "_latest", lambda activity: activity)
    monkeypatch.setattr(scoring_menu, "_library", lambda: None)
    monkeypatch.setattr(
        scoring_menu, "list_scores", lambda *_args, **_kwargs: (object(),)
    )

    def unavailable(*_args: object, **_kwargs: object) -> None:
        raise ConcordWorkflowValidationError(
            "Scoring Scale labels could not be verified."
        )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("no Score selection or mutation on label failure")

    monkeypatch.setattr(scoring_menu, "build_score_teacher_labels", unavailable)
    monkeypatch.setattr(scoring_menu, "select_one", forbidden)
    monkeypatch.setattr(scoring_menu, "add_score", forbidden)
    monkeypatch.setattr(
        scoring_menu,
        "show_result",
        lambda title, lines: recorded.append((title, tuple(lines))),
    )
    scoring_menu._browse_scores(_activity())
    assert recorded == [(
        "Score Error", ("Scoring Scale labels could not be verified.",),
    )]
