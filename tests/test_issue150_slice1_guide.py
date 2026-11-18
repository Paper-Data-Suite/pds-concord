"""Concord #150 Slice 1: independent target-aware reuse handoff.

All states, actors and Activity IDs in this file are synthetic.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided
from concord.menu_context import MenuSessionContext
from concord.workflows.models import ActivitySummary, ClassSummary


def _activity(*, revision: int = 3) -> ActivitySummary:
    return ActivitySummary(
        class_id="class-target",
        activity_id="new-activity",
        title="Synthetic target seminar",
        status="draft",
        scoring_orientation="mixed",
        session_count=1,
        group_count=0,
        snapshot_revision=revision,
    )


def _prepared(**values: object) -> SimpleNamespace:
    data: dict[str, object] = {
        "activity_type": "socratic_seminar",
        "scoring_orientation": "mixed",
        "title": "New independent seminar",
        "privacy_policy": SimpleNamespace(classification="teacher_restricted"),
        "first_session_label": "Day 1",
        "standards_profile_id": "ela-profile",
        "focus_standard_ids": ("SL.PE.11-12.1",),
        "diagnostics": (
            SimpleNamespace(message="Source context audience was not copied."),
        ),
    }
    data.update(values)
    return SimpleNamespace(**data)


def test_review_is_explicit_about_saved_definitions_and_all_excluded_history() -> None:
    source = _activity()
    target = ClassSummary(class_id="class-target", school_year="2026-2027")
    lines = guided._cross_class_copy_review(source, target, _prepared())
    joined = "\n".join(lines)
    for term in (
        "Source lesson",
        "Target class",
        "SAVED DEFINITIONS TO CHOOSE LATER, NOT COPIED",
        "Saved Packet",
        "saved rubric",
        "source roster",
        "Memberships",
        "returned",
        "QR/scan routes",
        "Scores",
        "Grades",
        "source external references",
        "teacher restricted",
        "Source context audience was not copied",
        "Target Focus Standards retained and validated: 1",
    ):
        assert term in joined
    assert "student-secret" not in joined
    assert "review digest" not in joined.lower()


@pytest.mark.parametrize(
    ("choice", "owner"),
    (("3", "groups"), ("4", "materials"), ("5", "assessment"), ("6", "review")),
)
def test_post_copy_owned_stage_uses_refreshed_target_without_inferred_write(
    choice: str, owner: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    fresh = _activity(revision=14)
    observed: list[tuple[str, object]] = []
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    answers = iter((choice, "2"))
    monkeypatch.setattr(
        guided,
        "show_activity",
        lambda cls, aid: (
            observed.append(("reloaded", (cls, aid))),
            SimpleNamespace(summary=fresh),
        )[1],
    )
    for name, kind in (
        ("_launch_target_cluster_planning", "groups"),
        ("_launch_target_materials", "materials"),
        ("_launch_assessment", "assessment"),
        ("launch_guided_setup_for_activity", "review"),
    ):
        monkeypatch.setattr(
            guided,
            name,
            lambda a, _state, kind=kind: observed.append((kind, a)),
        )
    guided._offer_after_creation(
        _activity(revision=3), MenuSessionContext(), copied=True
    )
    assert observed == [
        ("reloaded", ("class-target", "new-activity")),
        (owner, fresh),
    ]


def test_fresh_create_remains_one_continue_or_finish_choice(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")
    guided._offer_after_creation(_activity(), MenuSessionContext(), copied=False)
    text = capsys.readouterr().out
    assert "1. Continue setup now" in text
    assert "2. Finish for now" in text
    assert "3. Plan target Clusters" not in text


def test_post_copy_finish_is_no_write_and_no_implicit_stage_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")
    for name in (
        "show_activity",
        "_launch_groups",
        "_launch_target_cluster_planning",
        "_launch_target_materials",
        "_launch_materials",
        "_launch_assessment",
        "launch_guided_setup_for_activity",
    ):
        monkeypatch.setattr(
            guided,
            name,
            lambda *_a, **_k: pytest.fail("No hidden stage work on Finish for now"),
        )
    guided._offer_after_creation(_activity(), MenuSessionContext(), copied=True)


def test_help_does_not_attempt_core_notes_or_roster_write(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        guided,
        "_classes",
        lambda: (ClassSummary(class_id="class-target", school_year="2026-2027"),),
    )
    monkeypatch.setattr(guided, "clear_screen", lambda: None)
    monkeypatch.setattr(guided, "pause_for_user", lambda: None)
    answers = iter(("h", "b"))
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    guided.launch_guided_activity_menu(MenuSessionContext())
    output = capsys.readouterr().out
    assert "Use this lesson with another class" in output
    assert "same class with a fresh Activity" in output
    assert "B. Back" in output
    assert "M. Main Menu" in output
    assert "Q. Quit" in output
