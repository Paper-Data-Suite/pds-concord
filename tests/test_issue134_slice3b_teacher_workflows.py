"""Teacher-facing identity minimization without changing exact model selections."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from concord import (
    menu_artifact,
    menu_group,
    menu_presets,
    menu_prompts,
    menu_scoring,
    menu_session,
)


def _record(**values: object) -> Any:
    return SimpleNamespace(**values)


def test_duplicate_group_names_preserve_exact_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    groups = (
        _record(
            group_id="opaque-group-a", label="Workshop", status="active", member_count=3
        ),
        _record(
            group_id="opaque-group-b", label="Workshop", status="active", member_count=3
        ),
    )
    seen: list[str] = []

    def select(_title: str, items: object, labels: object, **_kw: object) -> Any:
        seen.extend(labels)
        return items[1]

    monkeypatch.setattr(menu_prompts, "select_one", select)
    selected = menu_prompts.choose_group(groups, title="Choose Group")
    assert selected is groups[1]
    assert len(set(seen)) == 2
    assert all("opaque-group" not in label for label in seen)
    assert all("display order, not chronological" in label for label in seen)


def test_duplicate_student_names_preserve_exact_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    students = (
        _record(student_id="private-student-1", name="Same Name"),
        _record(student_id="private-student-2", name="Same Name"),
    )
    seen: list[str] = []
    monkeypatch.setattr(
        menu_prompts, "load_class_roster", lambda *_a: _record(students=students)
    )
    monkeypatch.setattr(menu_prompts, "student_sort_name", lambda s: s.name)
    monkeypatch.setattr(menu_prompts, "student_display_name", lambda s: s.name)

    def select(_title: str, items: object, labels: object, **_kw: object) -> Any:
        seen.extend(labels)
        return items[1]

    monkeypatch.setattr(menu_prompts, "select_one", select)
    selected = menu_prompts.choose_student(
        None,
        "class",
    )  # type: ignore[arg-type]
    assert selected is students[1]
    assert len(set(seen)) == 2
    assert all("private-student" not in label for label in seen)


def test_review_and_moderation_labels_are_bounded() -> None:
    review = _record(
        artifact_instance_id="secret-artifact",
        reviewed_at="2026-10-12T19:58:00-04:00",
        review_outcome="accepted",
        scoring_readiness="ready",
        is_current=False,
    )
    review_label = menu_artifact._review_label(review)
    assert "secret-artifact" not in review_label
    assert "historical" in review_label
    assert "Reviewed" in review_label

    decision = _record(
        moderated_at="2026-10-12T19:58:00-04:00",
        evidence_reference=_record(
            evidence_kind="artifact_instance",
            owning_system="concord",
            record_id="secret-evidence-id",
        ),
        status="approved",
        permitted_use="scoring",
        is_current=True,
    )
    label = menu_artifact._moderation_label(decision)
    assert "secret-evidence-id" not in label
    assert "current" in label


def test_score_label_uses_actual_recorded_time_not_id() -> None:
    score = _record(
        score_record_id="private-score-uuid",
        target_reference=_record(
            target_kind="core_student", target_id="secret-student"
        ),
        scored_at="2026-10-12T19:58:00-04:00",
        disposition="scored",
        value=3,
        is_current=True,
    )
    label = menu_scoring._score_label(score)
    assert "private-score" not in label
    assert "secret-student" not in label
    assert "Scored" in label
    assert "current" in label


def test_artifact_page_selection_hides_technical_route_and_page_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pages = (
        _record(
            artifact_page_id="secret-page-a",
            page_number=1,
            page_status="returned",
            route_id="secret-route",
            artifact_instance_id="a",
        ),
        _record(
            artifact_page_id="secret-page-b",
            page_number=1,
            page_status="returned",
            route_id=None,
            artifact_instance_id="b",
        ),
    )
    labels_seen: list[str] = []
    shown: list[str] = []
    monkeypatch.setattr(menu_artifact, "list_artifact_pages", lambda *_a: pages)

    def select(_title: str, items: object, labels: object, **_kw: object) -> Any:
        labels_seen.extend(labels)
        return items[1]

    monkeypatch.setattr(menu_artifact, "select_one", select)
    monkeypatch.setattr(
        menu_artifact, "show_result", lambda _title, lines: shown.extend(lines)
    )
    menu_artifact._list_pages(_record(class_id="class", activity_id="activity"))
    assert len(set(labels_seen)) == 2
    assert "secret-" not in " ".join(labels_seen + shown)
    assert "Route prepared: not yet" in shown


def test_session_and_preset_results_hide_ids() -> None:
    lines = menu_session._result_lines(23, "secret-session-id", no_op=False)
    assert "Session saved." in lines
    assert "secret-session-id" not in " ".join(lines)
    assert "23" not in " ".join(lines)
    preset = _record(
        name="Comparison Criteria",
        preset_id="private-preset",
        status="active",
        revision=4,
    )
    label = menu_presets._summary_label(preset)
    assert "Comparison Criteria" in label
    assert "revision 4" in label
    assert "private-preset" not in label


def test_group_list_preserves_duplicate_names_without_ids(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    groups = (
        _record(
            group_id="secret-group-1",
            label="Discussion",
            member_count=2,
            status="active",
        ),
        _record(
            group_id="secret-group-2",
            label="Discussion",
            member_count=2,
            status="active",
        ),
    )
    monkeypatch.setattr(menu_group, "list_groups", lambda *_a: groups)
    monkeypatch.setattr(menu_group, "clear_screen", lambda: None)
    monkeypatch.setattr(menu_group, "pause_for_user", lambda: None)
    menu_group._list_groups(_record(class_id="class", activity_id="activity"))
    output = capsys.readouterr().out
    assert "secret-group" not in output
    assert "group choice 1 of 2" in output
    assert "group choice 2 of 2" in output
