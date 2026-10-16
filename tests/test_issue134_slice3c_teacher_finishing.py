"""Focused presentation regressions for Concord #134 Slice 3C."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_scan as menu_scan
import concord.menu_scoring as menu_scoring
from concord.menu_score_teacher_labels import (
    ScoreTeacherLabels,
    build_score_teacher_labels,
)
from concord.models import Criterion, ScoreTargetReference
from concord.workflows import ActivitySummary, ScoringScaleSummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1",
        activity_id="activity-1",
        title="Evidence Discussion",
        status="active",
        scoring_orientation="local_criteria_only",
        session_count=1,
        group_count=2,
        snapshot_revision=7,
    )


def test_teacher_labels_are_exact_and_disambiguate_identical_group_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reads: list[str] = []

    def groups(*_args: object) -> tuple[object, ...]:
        reads.append("groups")
        return (
            SimpleNamespace(group_id="group-b", label="Group A"),
            SimpleNamespace(group_id="group-a", label="Group A"),
        )

    monkeypatch.setattr(
        "concord.menu_score_teacher_labels.list_groups", groups
    )
    monkeypatch.setattr(
        "concord.menu_score_teacher_labels.list_sessions",
        lambda *_args: (
            SimpleNamespace(
                session_id="session-1", sequence=2, label="Discussion"
            ),
        ),
    )
    monkeypatch.setattr(
        "concord.menu_score_teacher_labels.list_teacher_artifact_choices",
        lambda *_args, **_kwargs: (
            SimpleNamespace(
                summary=SimpleNamespace(artifact_instance_id="work-1"),
                label="Group A | Session 2 | returned 1/1",
            ),
        ),
    )
    monkeypatch.setattr(
        "concord.menu_score_teacher_labels.resolve_read_workspace_root",
        lambda: None,
    )
    labels = build_score_teacher_labels(_activity())
    assert reads == ["groups"]
    a = labels.target("concord_group", "group-a")
    b = labels.target("concord_group", "group-b")
    assert a != b
    assert "Group A" in a and "Group A" in b
    assert "group-a" not in a and "group-b" not in b
    assert labels.target("concord_artifact_instance", "work-1").startswith(
        "Group A | Session 2"
    )
    assert labels.session("session-1") == "Session 2 - Discussion"
    assert labels.target("concord_group", "unknown") == "Group name unavailable"
    assert labels.target("core_student", "unknown") == "Student name unavailable"


def test_score_confirmation_uses_names_not_identifiers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    labels = ScoreTeacherLabels(
        targets={("concord_group", "technical-group"): "Discussion Group"},
        sessions={"technical-session": "Session 2 - Discussion"},
    )
    calls: list[str] = []
    monkeypatch.setattr(
        menu_scoring,
        "build_score_teacher_labels",
        lambda activity: calls.append(activity.title) or labels,
    )
    target = ScoreTargetReference(
        target_kind="concord_group",
        target_id="technical-group",
        owning_system="concord",
    )
    criterion = cast(
        Criterion, SimpleNamespace(label="Reasoned Collaboration")
    )
    scale = cast(
        ScoringScaleSummary, SimpleNamespace(name="Four-Point Scale")
    )
    lines = menu_scoring._score_confirmation_lines(
        _activity(), target, criterion, scale, "technical-session",
        "scored", 3, "professional_judgment", 0,
    )
    text = "\n".join(lines)
    assert calls == ["Evidence Discussion"]
    assert "Discussion Group" in text
    assert "Reasoned Collaboration" in text
    assert "Four-Point Scale" in text
    assert "Session 2 - Discussion" in text
    assert "technical-group" not in text
    assert "technical-session" not in text
    assert "GROUP SCORE WARNING:" in text
    assert "It creates no individual student Scores." in text


def test_score_labels_do_not_guess_missing_evidence_identity() -> None:
    labels = ScoreTeacherLabels()
    assert labels.target("concord_artifact_instance", "hidden-id") == (
        "Work label unavailable"
    )
    assert labels.criterion("hidden-criterion") == "Criterion label unavailable"
    assert labels.scale("hidden-scale") == "Scoring Scale label unavailable"
    assert labels.session(None) == "No separate Session"


def test_scan_inbox_label_states_file_modification_not_receipt(
    tmp_path: Path,
) -> None:
    source = tmp_path / "student-work.pdf"
    source.write_bytes(b"synthetic")
    label = menu_scan._inbox_file_display(source)
    assert label.startswith("student-work.pdf - file modified ")
    assert "routed" not in label.casefold()
    assert "scanned" not in label.casefold()
    assert "received" not in label.casefold()
    source.unlink()
    assert menu_scan._inbox_file_display(source) == (
        "student-work.pdf - file modified time unavailable"
    )
