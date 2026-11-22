"""#152 Slice 1B: essential Score labels before confirmation and revision."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_scoring as scoring_menu
from concord.menu_context import MenuSessionContext
from concord.menu_score_teacher_labels import ScoreTeacherLabels, _label_unique
from concord.models import Criterion, ScoreTargetReference
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowValidationError,
    ScoreSummary,
    ScoringScaleSummary,
    WorkflowActor,
)


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-test",
        activity_id="activity-test",
        title="Synthetic score validation",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=1,
        snapshot_revision=9,
    )


def _labels() -> ScoreTeacherLabels:
    return ScoreTeacherLabels(
        targets={
            ("core_student", "student-1"): "Sample Student",
            ("concord_group", "group-1"): "Cluster One",
        },
        sessions={"session-1": "Session 1 - Seminar"},
        criteria={"criterion-1": "Discussion participation"},
        scales={"scale-1": "Four-level proficiency"},
    )


def _target(kind: str = "concord_group") -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind=kind,
        target_id="student-1" if kind == "core_student" else "group-1",
        owning_system="core" if kind == "core_student" else "concord",
    )


def _criterion() -> Criterion:
    return cast(
        Criterion,
        SimpleNamespace(criterion_id="criterion-1", label="Discussion participation"),
    )


def _scale() -> ScoringScaleSummary:
    return cast(
        ScoringScaleSummary,
        SimpleNamespace(scoring_scale_id="scale-1", name="Four-level proficiency"),
    )


def _head() -> ScoreSummary:
    return cast(
        ScoreSummary,
        SimpleNamespace(
            score_record_id="score-1",
            target_reference=_target(),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            session_id="session-1",
            scored_at="2026-11-22T15:00:00Z",
            is_current=True,
            value=3,
            disposition="scored",
        ),
    )


@pytest.mark.parametrize(
    ("method", "args", "source"),
    (
        ("require_target", ("concord_group", "missing"), "Score target"),
        ("require_target", ("core_student", "missing"), "Score target"),
        ("require_session", ("missing",), "Score Session"),
        ("require_criterion", ("missing",), "Score Criterion"),
        ("require_scale", ("missing",), "Scoring Scale"),
    ),
)
def test_missing_essential_identity_never_falls_back(
    method: str,
    args: tuple[str, ...],
    source: str,
) -> None:
    with pytest.raises(ConcordWorkflowValidationError) as error:
        getattr(_labels(), method)(*args)
    assert source in str(error.value)
    assert "missing" not in str(error.value)
    assert "no Score was recorded" in str(error.value)


def test_ambiguous_or_blank_essential_definition_is_not_actionable() -> None:
    labels = ScoreTeacherLabels(
        criteria={"criterion-1": "Criterion label ambiguous across revisions"},
        scales={"scale-1": "   "},
    )
    with pytest.raises(ConcordWorkflowValidationError, match="Score Criterion"):
        labels.require_criterion("criterion-1")
    with pytest.raises(ConcordWorkflowValidationError, match="Scoring Scale"):
        labels.require_scale("scale-1")


def test_duplicate_definition_names_have_distinct_deterministic_labels() -> None:
    labels = _label_unique(
        ("scale-a", "scale-b"), ("Same name", "Same name"), "Scoring Scale"
    )
    assert labels["scale-a"] != labels["scale-b"]
    assert "1 of 2" in labels["scale-a"]
    assert "2 of 2" in labels["scale-b"]


def test_score_confirmation_requires_exact_target_and_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        scoring_menu,
        "build_score_teacher_labels",
        lambda _activity: _labels(),
    )
    lines = scoring_menu._score_confirmation_lines(
        _activity(), _target(), _criterion(), _scale(),
        "session-1", "scored", 3, "linked_evidence", 1,
    )
    assert "Target: Cluster One" in lines
    assert "Session context: Session 1 - Seminar" in lines
    assert "GROUP SCORE WARNING:" in lines

    monkeypatch.setattr(
        scoring_menu, "build_score_teacher_labels",
        lambda _activity: ScoreTeacherLabels(),
    )
    with pytest.raises(ConcordWorkflowValidationError, match="Score target"):
        scoring_menu._score_confirmation_lines(
            _activity(), _target(), _criterion(), _scale(),
            None, "scored", 3, "linked_evidence", 1,
        )
    monkeypatch.setattr(
        scoring_menu, "build_score_teacher_labels",
        lambda _activity: ScoreTeacherLabels(
            targets={("concord_group", "group-1"): "Cluster One"}
        ),
    )
    with pytest.raises(ConcordWorkflowValidationError, match="Score Session"):
        scoring_menu._score_confirmation_lines(
            _activity(), _target(), _criterion(), _scale(),
            "session-1", "scored", 3, "linked_evidence", 1,
        )


def test_unlabeled_selected_criterion_or_scale_blocks_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        scoring_menu, "build_score_teacher_labels", lambda _act: _labels()
    )
    for criterion_label, scale_label in (
        ("", "Four-level proficiency"),
        ("Discussion", ""),
    ):
        criterion = cast(Criterion, SimpleNamespace(label=criterion_label))
        scale = cast(ScoringScaleSummary, SimpleNamespace(name=scale_label))
        with pytest.raises(ConcordWorkflowValidationError, match="Criterion or Scale"):
            scoring_menu._score_confirmation_lines(
                _activity(), _target(), criterion, scale,
                None, "scored", 3, "linked_evidence", 1,
            )


def test_score_entry_never_authorizes_when_target_name_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(scoring_menu, "_latest", lambda activity: activity)
    monkeypatch.setattr(
        scoring_menu, "_score_components", lambda *_args: SimpleNamespace(
            target=_target(),
            criterion=_criterion(),
            scale=_scale(),
            session_id=None,
            disposition="scored",
            basis="professional_judgment",
            value=3,
            links=(),
        ),
    )
    monkeypatch.setattr(scoring_menu, "_identifier", lambda *_args: "score-test")
    monkeypatch.setattr(
        scoring_menu,
        "build_score_teacher_labels",
        lambda _activity: ScoreTeacherLabels(),
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("no authorization or Score write on label failure")

    monkeypatch.setattr(scoring_menu, "confirm_actor_write", forbidden)
    monkeypatch.setattr(scoring_menu, "add_score", forbidden)
    monkeypatch.setattr(
        scoring_menu, "_handle_error",
        lambda _activity, error: errors.append(str(error)),
    )
    scoring_menu._record_score(
        _activity(), MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    assert len(errors) == 1
    assert "Score target" in errors[0]


def test_revision_choice_includes_exact_target_criterion_and_scale() -> None:
    label = scoring_menu._revisable_score_label(_head(), _labels())
    assert "Cluster Group: Cluster One" in label
    assert "Discussion participation" in label
    assert "Four-level proficiency" in label
    assert "score-1" not in label
    assert "group-1" not in label


@pytest.mark.parametrize(
    "missing",
    ("target", "criterion", "scale", "session"),
)
def test_revision_menu_blocks_unverified_head_before_selection(
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    errors: list[str] = []
    verified = _labels()
    labels = ScoreTeacherLabels(
        targets={} if missing == "target" else verified.targets,
        criteria={} if missing == "criterion" else verified.criteria,
        scales={} if missing == "scale" else verified.scales,
        sessions={} if missing == "session" else verified.sessions,
    )
    monkeypatch.setattr(scoring_menu, "_latest", lambda activity: activity)
    monkeypatch.setattr(scoring_menu, "_library", lambda: None)
    monkeypatch.setattr(
        scoring_menu, "list_current_score_heads",
        lambda *_args, **_kwargs: (_head(),),
    )
    monkeypatch.setattr(
        scoring_menu, "build_score_teacher_labels",
        lambda *_args, **_kwargs: labels,
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("no selection or replacement with missing labels")

    monkeypatch.setattr(scoring_menu, "select_one", forbidden)
    monkeypatch.setattr(scoring_menu, "replace_score", forbidden)
    monkeypatch.setattr(
        scoring_menu, "_handle_error",
        lambda _activity, error: errors.append(str(error)),
    )
    scoring_menu._revise_score(
        _activity(), MenuSessionContext(actor=WorkflowActor(actor_id="teacher-1"))
    )
    assert len(errors) == 1
    assert "missing or ambiguous" in errors[0]
