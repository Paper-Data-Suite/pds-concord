"""#152 Slice 1C: exact Score-history and historical assessment versions."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import concord.menu_score_teacher_labels as label_menu
import concord.menu_scoring as score_menu
from concord.menu_score_teacher_labels import ScoreTeacherLabels
from concord.models import PrivacyPolicy, ScoreTargetReference
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowConflictError,
    ScoreDetail,
    ScoreSummary,
)


def _activity(revision: int = 12) -> ActivitySummary:
    return ActivitySummary(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic discussion",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=1,
        snapshot_revision=revision,
    )


def _score(revision: int = 12, current: bool = False) -> ScoreSummary:
    return ScoreSummary(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        score_record_id="score-exact",
        target_reference=ScoreTargetReference(
            target_kind="concord_group",
            target_id="group-1",
            owning_system="concord",
        ),
        criterion_id="criterion-1",
        score_kind="local",
        standard_id=None,
        scoring_scale_id="scale-1",
        disposition="scored",
        value=3,
        basis="professional_judgment",
        session_id=None,
        scored_at="2026-11-22T15:00:00Z",
        moderation_complete=True,
        supersedes_score_record_id=None,
        is_current=current,
        snapshot_revision=revision,
    )


def _detail(item: ScoreSummary) -> ScoreDetail:
    return ScoreDetail(
        summary=item,
        rationale="Synthetic group analysis.",
        status_reason=None,
        privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        evidence_links=(),
    )


def _labels() -> ScoreTeacherLabels:
    return ScoreTeacherLabels(
        targets={("concord_group", "group-1"): "Cluster One"},
        criteria={"criterion-1": "Group analysis"},
        scales={"scale-1": "Four levels"},
        criterion_versions={"criterion-1": "rubric revision 1; historical"},
        scale_versions={"scale-1": "revision 2; historical"},
    )


def test_history_detail_preserves_versions_and_group_warning() -> None:
    item = _score()
    lines = score_menu._score_history_detail_lines(
        item, _detail(item), _labels()
    )
    assert "Score state: historical" in lines
    assert "Criterion Set version: rubric revision 1; historical" in lines
    assert "Scale version: revision 2; historical" in lines
    assert "Group Score only; no individual student Score is implied." in lines
    assert "Evidence Links: 0" in lines
    assert all("score-exact" not in line for line in lines)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("score_record_id", "other-score"),
        ("snapshot_revision", 13),
        ("is_current", True),
    ),
)
def test_history_rejects_stale_detail(
    field: str, replacement: str | int | bool,
) -> None:
    item = _score()
    other = replace(item, **{field: replacement})
    with pytest.raises(ConcordWorkflowConflictError, match="Score history changed"):
        score_menu._score_history_detail_lines(item, _detail(other), _labels())


def test_history_refreshes_activity_before_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[str] = []
    item = _score()
    monkeypatch.setattr(score_menu, "_latest", lambda _old: _activity())
    monkeypatch.setattr(score_menu, "_library", lambda: None)
    monkeypatch.setattr(
        score_menu, "list_scores", lambda *_a, **_kw: (item,)
    )

    def labels(activity: ActivitySummary, **kwargs: object) -> ScoreTeacherLabels:
        assert activity.snapshot_revision == 12
        assert kwargs["include_score_definitions"] is True
        observed.append("labels")
        return _labels()

    monkeypatch.setattr(score_menu, "build_score_teacher_labels", labels)
    monkeypatch.setattr(score_menu, "select_one", lambda *_a, **_kw: item)
    monkeypatch.setattr(score_menu, "show_score", lambda *_a, **_kw: _detail(item))
    monkeypatch.setattr(
        score_menu, "show_result",
        lambda title, _lines: observed.append(title),
    )
    score_menu._browse_scores(_activity(3))
    assert observed == ["labels", "Score Detail"]


def test_stale_score_list_blocks_choice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    monkeypatch.setattr(score_menu, "_latest", lambda _old: _activity())
    monkeypatch.setattr(score_menu, "_library", lambda: None)
    monkeypatch.setattr(
        score_menu, "list_scores", lambda *_a, **_kw: (_score(11),)
    )
    monkeypatch.setattr(
        score_menu, "build_score_teacher_labels",
        lambda *_a, **_kw: _labels(),
    )

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("must not select a stale Score")

    monkeypatch.setattr(score_menu, "select_one", refuse)
    monkeypatch.setattr(
        score_menu, "show_result",
        lambda _title, lines: errors.extend(lines),
    )
    score_menu._browse_scores(_activity(3))
    assert len(errors) == 1
    assert "changed before selection" in errors[0]


def test_history_version_labels_use_exact_records(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        label_menu, "resolve_read_workspace_root",
        lambda: tmp_path / "workspace",
    )
    monkeypatch.setattr(
        label_menu, "standards_for_activity", lambda _activity: object()
    )
    monkeypatch.setattr(label_menu, "list_groups", lambda *_a, **_kw: ())
    monkeypatch.setattr(label_menu, "list_sessions", lambda *_a, **_kw: ())
    monkeypatch.setattr(
        label_menu, "list_teacher_artifact_choices", lambda *_a, **_kw: ()
    )
    monkeypatch.setattr(
        label_menu, "load_class_roster",
        lambda *_a, **_kw: SimpleNamespace(students=()),
    )
    monkeypatch.setattr(
        label_menu, "list_scoring_scales",
        lambda *_a, **_kw: (
            SimpleNamespace(
                scoring_scale_id="scale-old", name="Four levels",
                revision=1, is_current=False,
            ),
            SimpleNamespace(
                scoring_scale_id="scale-new", name="Four levels",
                revision=2, is_current=True,
            ),
        ),
    )
    monkeypatch.setattr(
        label_menu, "list_criterion_sets",
        lambda *_a, **_kw: (
            SimpleNamespace(
                criterion_set_id="set-old", revision=1, is_current=False,
            ),
            SimpleNamespace(
                criterion_set_id="set-new", revision=2, is_current=True,
            ),
        ),
    )

    def detail(_cls: str, _act: str, identity: str, **_kw: object) -> object:
        cid = "criterion-old" if identity == "set-old" else "criterion-new"
        return SimpleNamespace(
            criteria=(SimpleNamespace(criterion_id=cid, label="Analysis"),)
        )

    monkeypatch.setattr(label_menu, "show_criterion_set", detail)
    labels = label_menu.build_score_teacher_labels(
        _activity(), include_score_definitions=True
    )
    assert labels.scale_version("scale-old") == "revision 1; historical"
    assert labels.scale_version("scale-new") == "revision 2; current"
    assert labels.criterion_version("criterion-old") == (
        "rubric revision 1; historical"
    )
    assert labels.criterion_version("criterion-new") == (
        "rubric revision 2; current"
    )
    assert labels.scale("scale-old") != labels.scale("scale-new")
