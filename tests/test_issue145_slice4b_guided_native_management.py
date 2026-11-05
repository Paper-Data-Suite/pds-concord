"""#145 Slice 4B: exact revision selection and guarded native successor behavior."""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

import concord.menu_criterion_guidance as editor
import concord.menu_scoring as menu
from concord.criterion_guidance import CriterionDraft, CriterionSetDraft
from concord.menu_context import MenuSessionContext
from concord.workflows import ActivitySummary, WorkflowActor
from concord.workflows.criterion_sets import ActivityCriterionSetSelectionSnapshot


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-synthetic",
        activity_id="activity-synthetic",
        title="Jíbara (synthetic)",
        status="active",
        scoring_orientation="local_criteria_only",
        session_count=1,
        group_count=2,
        snapshot_revision=14,
    )


def _state() -> MenuSessionContext:
    return MenuSessionContext(actor=WorkflowActor(actor_id="teacher-synthetic"))


def _draft() -> CriterionSetDraft:
    return CriterionSetDraft(
        name="Discussion assessment",
        purpose="Evaluate discussion",
        criterion_set_kind="local",
        scope="activity_specific",
        criteria=(CriterionDraft(
            key="collaboration",
            label="Collaborative analysis",
            definition="Quality of Group reasoning",
            criterion_kind="local",
            supported_target_kinds=("concord_group",),
            status="active",
        ),),
    )


def _review(*, current: bool = True, selected: bool = False):
    return SimpleNamespace(
        criterion_set_id="set-old",
        lineage_id="lineage-discussion",
        revision=3,
        is_current=current,
        is_selected=selected,
        draft=_draft(),
    )


def _selected(*ids: str, snap: int = 14):
    return ActivityCriterionSetSelectionSnapshot(
        criterion_set_ids=ids, snapshot_revision=snap
    )


def _head():
    return SimpleNamespace(
        criterion_set_id="set-old",
        lineage_id="lineage-discussion",
        name="Discussion assessment",
        revision=3,
        is_current=True,
        is_selected=False,
    )


def _common(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple[str, ...]]]:
    messages: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(menu, "_latest", lambda _a: _activity())
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "show_activity", lambda *a: SimpleNamespace(
            standards_profile_id=None, focus_standard_ids=()
        ),
    )
    monkeypatch.setattr(
        menu, "show_result",
        lambda title, lines: messages.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        menu, "_handle_error",
        lambda _activity, error, **kw: messages.append(
            ("Scoring Error", (str(error),))
        ),
    )
    monkeypatch.setattr(
        menu,
        "describe_native_criterion_set",
        lambda *a, **k: ("Exact predecessor revision",),
    )
    monkeypatch.setattr(
        menu,
        "describe_criterion_draft",
        lambda *a, **k: ("Reviewed successor draft",),
    )
    monkeypatch.setattr(menu, "project_native_criterion_set", lambda *a: _review())
    monkeypatch.setattr(menu, "show_criterion_set", lambda *a, **k: object())
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *a, **k: (_head(),))
    monkeypatch.setattr(menu, "select_one", lambda *a, **k: _head())
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: True)
    return messages


def test_existing_draft_is_not_regenerated_or_mutated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft = _draft()
    monkeypatch.setattr(editor, "clear_screen", lambda: None)
    monkeypatch.setattr(editor, "print_menu_header", lambda *a: None)
    monkeypatch.setattr(editor, "prompt_text", lambda *a, **k: k["default"])

    def choose(title: str, *args: object, **kw: object):
        return draft.scope if title == "Rubric scope" else "review"

    monkeypatch.setattr(editor, "select_one", choose)
    returned, choices = editor.guide_native_criterion_set(
        orientation="local_criteria_only",
        standards_library=None,
        standards_profile_id=None,
        focus_standard_ids=(),
        choose_scale=lambda: pytest.fail("No Scale selection in no-op review"),
        existing=draft,
    )
    assert returned is draft
    assert returned.criteria[0] is draft.criteria[0]
    assert choices == ()


def test_unchanged_mixed_legacy_shape_does_not_become_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    draft = replace(_draft(), criterion_set_kind="mixed")
    monkeypatch.setattr(editor, "clear_screen", lambda: None)
    monkeypatch.setattr(editor, "print_menu_header", lambda *a: None)
    monkeypatch.setattr(editor, "prompt_text", lambda *a, **k: k["default"])
    monkeypatch.setattr(
        editor, "select_one",
        lambda title, *a, **kw: (
            draft.scope if title == "Rubric scope" else "review"
        ),
    )
    result, _ = editor.guide_native_criterion_set(
        orientation="mixed",
        standards_library=None,
        standards_profile_id=None,
        focus_standard_ids=(),
        choose_scale=lambda: None,
        existing=draft,
    )
    assert result is draft
    assert result.criterion_set_kind == "mixed"


def test_metadata_only_edit_keeps_legacy_mixed_set_kind(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = replace(_draft(), criterion_set_kind="mixed")
    monkeypatch.setattr(editor, "clear_screen", lambda: None)
    monkeypatch.setattr(editor, "print_menu_header", lambda *a: None)
    monkeypatch.setattr(
        editor, "prompt_text",
        lambda title, label, **kw: (
            "Revised assessment title"
            if label == "Assessment/rubric name"
            else kw["default"]
        ),
    )
    monkeypatch.setattr(
        editor, "select_one",
        lambda title, *a, **kw: (
            original.scope if title == "Rubric scope" else "review"
        ),
    )
    result, _ = editor.guide_native_criterion_set(
        orientation="mixed",
        standards_library=None,
        standards_profile_id=None,
        focus_standard_ids=(),
        choose_scale=lambda: None,
        existing=original,
    )
    assert result.name == "Revised assessment title"
    assert result.criterion_set_kind == "mixed"
    assert result.criteria == original.criteria


def test_use_existing_preserves_selection_order_and_exact_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    state = iter((_selected("historical-old"), _selected("historical-old"),
                  _selected("historical-old", "set-old", snap=15)))
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: next(state),
    )
    requests = []

    def select(request, **kw):
        requests.append(request)
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=15))

    monkeypatch.setattr(menu, "select_activity_criterion_sets", select)
    menu._use_existing_criterion_set(_activity(), _state())
    assert len(requests) == 1
    assert requests[0].criterion_set_ids == ("historical-old", "set-old")
    assert requests[0].expected_snapshot_revision == 14
    assert messages[-1][0] == "Existing Rubric Selected"
    assert "Selected rubric revisions now: 2" in messages[-1][1]
    assert "Earlier selections deselected: 0" in messages[-1][1]
    assert "Selected revisions (ordered):" in messages[-1][1]
    assert any("exact ID: historical-old" in line for line in messages[-1][1])
    assert any("exact ID: set-old" in line for line in messages[-1][1])


def test_already_selected_is_no_op_without_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selected("set-old"),
    )
    monkeypatch.setattr(
        menu, "select_activity_criterion_sets",
        lambda *a, **kw: pytest.fail("Already selected must not write"),
    )
    menu._use_existing_criterion_set(_activity(), _state())
    assert messages[-1][0] == "Rubric Already Selected — No Change"


def test_refused_approval_changes_no_native_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selected(),
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **kw: False)
    monkeypatch.setattr(
        menu, "select_activity_criterion_sets",
        lambda *a, **kw: pytest.fail("Canceled selection must not write"),
    )
    menu._use_existing_criterion_set(_activity(), _state())
    assert not messages


def test_stale_existing_selection_refuses_before_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    selection = iter((_selected(), _selected(snap=15)))
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: next(selection),
    )
    monkeypatch.setattr(
        menu, "select_activity_criterion_sets",
        lambda *a, **kw: pytest.fail("Stale state must not write"),
    )
    menu._use_existing_criterion_set(_activity(), _state())
    assert any("changed" in " ".join(lines) for _, lines in messages)


def test_revision_draft_noop_never_creates_successor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selected(),
    )
    monkeypatch.setattr(
        menu, "guide_native_criterion_set",
        lambda **kw: (kw["existing"], ()),
    )
    monkeypatch.setattr(
        menu, "revise_criterion_set",
        lambda *a, **kw: pytest.fail("No-op revision must not write"),
    )
    menu._revise_criterion_set(_activity(), _state())
    assert messages[-1][0] == "Rubric Unchanged — No Revision Created"


def test_historical_revision_is_not_an_editable_current_head(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selected(),
    )
    monkeypatch.setattr(
        menu, "project_native_criterion_set",
        lambda *a: _review(current=False),
    )
    monkeypatch.setattr(
        menu, "guide_native_criterion_set",
        lambda **kw: pytest.fail("Historical revision must not be edited"),
    )
    menu._revise_criterion_set(_activity(), _state())
    assert any("historical" in " ".join(lines) for _, lines in messages)


def test_successor_uses_same_lineage_new_id_and_does_not_select(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    reads = iter((
        _selected("set-old"),
        _selected("set-old"),
        _selected("set-old", snap=15),
    ))
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: next(reads),
    )
    monkeypatch.setattr(
        menu, "guide_native_criterion_set",
        lambda **kw: (
            replace(kw["existing"], purpose="Revised purpose"), ()
        ),
    )
    monkeypatch.setattr(menu, "validate_criterion_draft", lambda *a, **kw: None)
    requests = []

    def revision(request, **kw):
        requests.append(request)
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=15))

    monkeypatch.setattr(menu, "revise_criterion_set", revision)
    monkeypatch.setattr(
        menu, "select_activity_criterion_sets",
        lambda *a, **kw: pytest.fail("Revision must not select"),
    )

    def show(*a, **kw):
        return SimpleNamespace(summary=SimpleNamespace(
            lineage_id="lineage-discussion",
            revision=4,
            supersedes_criterion_set_id="set-old",
            snapshot_revision=15,
            is_current=True,
        ))

    monkeypatch.setattr(menu, "show_criterion_set", show)
    menu._revise_criterion_set(_activity(), _state())
    assert len(requests) == 1
    request = requests[0]
    assert request.criterion_set_id == "set-old"
    assert request.replacement_criterion_set_id != "set-old"
    assert request.revision == 4
    assert request.expected_snapshot_revision == 14
    assert request.criteria[0].criterion_id != "old-criterion-id"
    assert request.criteria[0].definition == "Quality of Group reasoning"
    assert request.criteria[0].supported_target_kinds == ("concord_group",)
    assert messages[-1][0] == "Rubric Revised — Successor Not Yet Selected"
    assert any("remain selected" in line for line in messages[-1][1])


def test_revision_stale_after_review_does_not_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    messages = _common(monkeypatch)
    selection = iter((_selected(), _selected(snap=15)))
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: next(selection),
    )
    monkeypatch.setattr(
        menu, "guide_native_criterion_set",
        lambda **kw: (
            replace(kw["existing"], purpose="Revised purpose"), ()
        ),
    )
    monkeypatch.setattr(menu, "validate_criterion_draft", lambda *a, **kw: None)
    monkeypatch.setattr(
        menu, "revise_criterion_set",
        lambda *a, **kw: pytest.fail("Stale revision must not write"),
    )
    menu._revise_criterion_set(_activity(), _state())
    assert any("changed" in " ".join(lines) for _, lines in messages)


def test_native_management_menu_preserves_advanced_routes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    monkeypatch.setattr(menu, "clear_screen", lambda: None)
    monkeypatch.setattr(menu, "print_menu_header", lambda *a: None)
    monkeypatch.setattr(menu, "print_navigation", lambda: None)
    monkeypatch.setattr(menu, "_revise_criterion_set", lambda *a: calls.append(3))
    monkeypatch.setattr(menu, "_use_existing_criterion_set", lambda *a: calls.append(4))
    monkeypatch.setattr(
        menu, "_revise_criterion_set_advanced", lambda *a: calls.append(8)
    )
    monkeypatch.setattr(
        menu, "_select_criterion_sets_advanced", lambda *a: calls.append(9)
    )
    choices = iter(("3", "4", "8", "9", "B"))
    monkeypatch.setattr("builtins.input", lambda *a: next(choices))
    menu._criterion_set_menu(_activity(), _state())
    assert calls == [3, 4, 8, 9]
