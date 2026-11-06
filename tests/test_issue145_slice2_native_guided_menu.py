"""#145 Slice 2: guided menu is draft-only until canonical CREATE approval."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord.criterion_guidance import CriterionDraft, CriterionSetDraft
from concord.menu_context import CancelMenuAction
from concord.menu_criterion_guidance import _kind_choices, guide_native_criterion_set
from concord.workflows.models import WorkflowActor


def _local_draft() -> CriterionSetDraft:
    return CriterionSetDraft(
        name="Synthetic discussion rubric",
        purpose="Describe evidence of collaboration",
        criterion_set_kind="local",
        criteria=(
            CriterionDraft(
                key="group-analysis",
                label="Cluster collaborative analysis",
                definition="Quality of the Group's text analysis",
                criterion_kind="local",
                supported_target_kinds=("concord_group",),
            ),
        ),
    )


def _activity() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="synthetic_class_a",
        activity_id="synthetic_activity_a",
        title="Synthetic discussion",
        scoring_orientation="local_criteria_only",
        snapshot_revision=7,
    )


def test_orientation_choices_fail_closed() -> None:
    assert _kind_choices("mixed") == ("standard_backed", "local")
    assert _kind_choices("local_criteria_only") == ("local",)
    assert _kind_choices("standards_based") == ("standard_backed",)
    with pytest.raises(ValueError, match="cannot receive"):
        _kind_choices("evidence_only")


def test_local_guided_draft_stays_in_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    import concord.menu_criterion_guidance as guide

    prompted = iter(
        ("Synthetic discussion rubric", "Explain group analysis",
         "Group work", "Shared analysis")
    )
    actions = iter(("activity_specific", "add", "review"))
    monkeypatch.setattr(guide, "prompt_text", lambda *a, **k: next(prompted))
    monkeypatch.setattr(guide, "select_one", lambda *a, **k: next(actions))
    monkeypatch.setattr(guide, "select_many", lambda *a, **k: ("concord_group",))
    monkeypatch.setattr(guide, "slug_identifier", lambda *a, **k: "group-work")
    monkeypatch.setattr(guide, "clear_screen", lambda: None)
    monkeypatch.setattr(guide, "print_menu_header", lambda title: None)
    draft, focus = guide_native_criterion_set(
        orientation="local_criteria_only",
        standards_library=None,
        standards_profile_id=None,
        focus_standard_ids=(),
        choose_scale=lambda: None,
    )
    assert focus == ()
    assert draft.criterion_set_kind == "local"
    assert draft.criteria[0].supported_target_kinds == ("concord_group",)
    assert draft.criteria[0].key == "group-work"
    assert draft.criteria[0].standard_id is None


def test_menu_back_cancels_in_memory_draft(monkeypatch: pytest.MonkeyPatch) -> None:
    import concord.menu_criterion_guidance as guide

    def cancelled(*args, **kwargs):
        raise CancelMenuAction

    monkeypatch.setattr(guide, "prompt_text", cancelled)
    with pytest.raises(CancelMenuAction):
        guide_native_criterion_set(
            orientation="local_criteria_only",
            standards_library=None,
            standards_profile_id=None,
            focus_standard_ids=(),
            choose_scale=lambda: None,
        )


def _setup_native(monkeypatch: pytest.MonkeyPatch, *, approve: bool):
    import concord.menu_scoring as menu

    activity = _activity()
    actor = WorkflowActor(actor_id="synthetic-teacher")
    state = SimpleNamespace(require_actor=lambda: actor)
    detail = SimpleNamespace(standards_profile_id=None, focus_standard_ids=())
    monkeypatch.setattr(menu, "_latest", lambda a: activity)
    monkeypatch.setattr(menu, "show_activity", lambda *a: detail)
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "guide_native_criterion_set", lambda **k: (_local_draft(), ())
    )
    confirmations = []

    def confirm(title, expected, lines):
        confirmations.append((title, expected, tuple(lines)))
        return approve

    monkeypatch.setattr(menu, "confirm_write", confirm)
    commits = []

    def commit(request, *, standards_library=None):
        commits.append(request)
        return SimpleNamespace(
            criterion_set_id=request.criterion_set_id,
            commit=SimpleNamespace(snapshot_revision=8),
        )

    monkeypatch.setattr(menu, "create_criterion_set", commit)
    notices = []
    monkeypatch.setattr(
        menu, "show_result", lambda name, lines: notices.append((name, lines))
    )
    failures = []
    monkeypatch.setattr(menu, "_handle_error", lambda a, e: failures.append(str(e)))
    return menu, activity, state, confirmations, commits, notices, failures


def test_declined_preview_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    menu, activity, state, previews, commits, notices, failures = _setup_native(
        monkeypatch, approve=False
    )
    menu._create_guided_criterion_set(activity, state)
    assert len(previews) == 1
    assert previews[0][1] == "CREATE"
    assert "CREATE ONLY" in "\n".join(previews[0][2])
    assert commits == [] and notices == [] and failures == []


def test_approved_native_creation_is_explicitly_not_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    menu, activity, state, previews, commits, notices, failures = _setup_native(
        monkeypatch, approve=True
    )
    menu._create_guided_criterion_set(activity, state)
    assert len(previews) == len(commits) == len(notices) == 1
    assert failures == []
    request = commits[0]
    assert request.class_id == activity.class_id
    assert request.expected_snapshot_revision == 7
    assert request.criterion_set_kind == "local"
    assert request.standards_profile_id is None
    assert request.criteria[0].supported_target_kinds == ("concord_group",)
    assert request.criteria[0].standard_id is None
    assert notices[0][0] == "Rubric Created — Not Yet Selected"
    assert "not automatically selected" in "\n".join(notices[0][1])


def test_snapshot_drift_refuses_approved_create(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    menu, activity, state, previews, commits, notices, failures = _setup_native(
        monkeypatch, approve=True
    )
    calls = 0

    # SimpleNamespace cannot be used with dataclasses.replace; create a fresh view.
    def changed_summary(current):
        nonlocal calls
        calls += 1
        if calls == 1:
            return activity
        return SimpleNamespace(**{**vars(activity), "snapshot_revision": 8})

    monkeypatch.setattr(menu, "_latest", changed_summary)
    menu._create_guided_criterion_set(activity, state)
    assert len(previews) == 1
    assert commits == [] and notices == []
    assert len(failures) == 1
    assert "changed after rubric review" in failures[0]


def test_cancelled_create_from_menu_preserves_advanced_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import concord.menu_scoring as menu

    choices = iter(("6", "B"))
    advanced = []
    guided = []
    monkeypatch.setattr("builtins.input", lambda prompt: next(choices))
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "print_menu_header", lambda _: None)
    monkeypatch.setattr(menu, "print_navigation", lambda: None)
    monkeypatch.setattr(menu, "_create_criterion_set", lambda *a: advanced.append(True))
    monkeypatch.setattr(
        menu, "_create_guided_criterion_set", lambda *a: guided.append(True)
    )
    menu._criterion_set_menu(_activity(), SimpleNamespace())
    assert advanced == [True] and guided == []


def test_ordinary_menu_routes_to_guided_only(monkeypatch: pytest.MonkeyPatch) -> None:
    import concord.menu_scoring as menu

    choices = iter(("1", "B"))
    advanced = []
    guided = []
    monkeypatch.setattr("builtins.input", lambda prompt: next(choices))
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "print_menu_header", lambda _: None)
    monkeypatch.setattr(menu, "print_navigation", lambda: None)
    monkeypatch.setattr(menu, "_create_criterion_set", lambda *a: advanced.append(True))
    monkeypatch.setattr(
        menu, "_create_and_use_guided_criterion_set", lambda *a: guided.append(True)
    )
    menu._criterion_set_menu(_activity(), SimpleNamespace())
    assert advanced == [] and guided == [True]
