"""#150 Slice 0: precisely scoped RED witnesses for teacher-facing cross-class reuse.

All synthetic inputs; no workspace is created and no academic writes occur.
The three strict XFAIL markers are retired in the implementing slice(s). Execute
`pytest --runxfail` to reproduce the actual missing teacher journey.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_guided_activity as guided_menu
from concord.menu_context import MenuSessionContext
from concord.workflows.models import ActivitySummary


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="source-class",
        activity_id="seminar-source",
        title="Synthetic Seminar",
        status="active",
        scoring_orientation="mixed",
        session_count=1,
        group_count=6,
        snapshot_revision=7,
    )


def _capture_existing_copy_preview(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[str, ...]:
    source = _activity()
    target = SimpleNamespace(class_id="target-class")
    monkeypatch.setattr(
        guided_menu, "resolve_read_workspace_root", lambda: "synthetic-root"
    )
    monkeypatch.setattr(guided_menu, "list_activities", lambda **_kwargs: (source,))
    monkeypatch.setattr(
        guided_menu, "_guided_activity_choice", lambda *_args, **_kwargs: source
    )
    monkeypatch.setattr(guided_menu, "choose_class", lambda _classes: target)
    monkeypatch.setattr(
        guided_menu,
        "prompt_text",
        lambda *_args, **kwargs: kwargs.get("default", "Synthetic target"),
    )
    monkeypatch.setattr(guided_menu, "_fresh_id", lambda prefix: f"new-{prefix}")
    monkeypatch.setattr(guided_menu, "load_menu_standards_library", lambda: None)
    monkeypatch.setattr(
        guided_menu,
        "prepare_activity_copy",
        lambda *_args, **_kwargs: SimpleNamespace(
            activity_type="socratic_seminar",
            scoring_orientation="mixed",
            review_digest="a" * 64,
        ),
    )
    observed: list[tuple[str, ...]] = []

    def capture(
        _title: str, _verb: str, lines: tuple[str, ...], **_kwargs: object
    ) -> None:
        observed.append(tuple(lines))
        return None

    monkeypatch.setattr(guided_menu, "confirm_actor_write", capture)
    monkeypatch.setattr(
        guided_menu,
        "copy_activity",
        lambda *_args, **_kwargs: pytest.fail("No copy before approval."),
    )
    guided_menu._create_from_activity(MenuSessionContext(), (target,))
    assert len(observed) == 1
    return observed[0]


@pytest.mark.xfail(
    strict=True, reason="#150 Slice 1: explicit teacher cross-class entry"
)
def test_teachers_can_find_use_this_lesson_with_another_class(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        guided_menu,
        "_classes",
        lambda: (SimpleNamespace(class_id="target-class"),),
    )
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "b")
    guided_menu.launch_guided_activity_menu(MenuSessionContext())
    rendered = capsys.readouterr().out.casefold()
    assert "use this lesson with another class" in rendered


@pytest.mark.xfail(strict=True, reason="#150 Slice 1: explicit carry/exclusion preview")
def test_cross_class_review_separates_saved_definitions_from_returned_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lines = _capture_existing_copy_preview(monkeypatch)
    preview = "\n".join(lines).casefold()
    # Teacher must see what will be selected separately rather than copied.
    assert "saved packet" in preview
    assert "source roster" in preview
    assert "returned" in preview
    assert "target" in preview


@pytest.mark.xfail(
    strict=True, reason="#150 Slice 1: teacher reuse-oriented continuation"
)
def test_after_copy_presents_target_preparation_stages(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(guided_menu, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "2")
    guided_menu._offer_after_creation(_activity(), MenuSessionContext(), copied=True)
    rendered = capsys.readouterr().out.casefold()
    assert "plan target clusters" in rendered
    assert "saved" in rendered and "materials" in rendered
    assert "rubric" in rendered
