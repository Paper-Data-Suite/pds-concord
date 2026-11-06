"""#145 Slice 4A: inspect exact native Set revisions with zero writes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import concord.menu_scoring as menu
from concord.criterion_revision_guidance import (
    NativeRubricReviewError,
    describe_native_criterion_set,
    project_native_criterion_set,
)
from concord.workflows import ActivityCriterionSetSelectionSnapshot, ActivitySummary


def _criterion(**updates: object) -> SimpleNamespace:
    values = dict(
        criterion_id="criterion-1",
        criterion_set_id="native-r1",
        key="discussion-participation",
        label="Individual discussion participation",
        definition="Evidence of discussion engagement",
        criterion_kind="standard_backed",
        supported_target_kinds=("core_student",),
        standard_id="SL.PE.11-12.1",
        alignment_standard_ids=("RL.CS.11-12.4",),
        default_scoring_scale_id="scale-ordinal-1",
        status="active",
    )
    values.update(updates)
    return SimpleNamespace(**values)


def _detail(**updates: object) -> SimpleNamespace:
    summary = SimpleNamespace(
        class_id="class-1",
        activity_id="activity-1",
        criterion_set_id="native-r1",
        lineage_id="native-discussion",
        revision=1,
        name="Jíbara Discussion Assessment",
        purpose="Discuss and analyze a text",
        criterion_set_kind="mixed",
        scope="reusable",
        status="active",
        criterion_count=2,
        standards_profile_id="profile-english-12",
        supersedes_criterion_set_id=None,
        is_current=False,
        is_selected=True,
        snapshot_revision=14,
    )
    values = dict(
        summary=summary,
        purpose="Discuss and analyze a text",
        criteria=(
            _criterion(),
            _criterion(
                criterion_id="criterion-2",
                key="cluster-analysis",
                label="Cluster collaborative analysis",
                definition="Evaluate the Group's shared textual reasoning",
                criterion_kind="local",
                supported_target_kinds=("concord_group",),
                standard_id=None,
                alignment_standard_ids=(),
                default_scoring_scale_id=None,
            ),
        ),
    )
    values.update(updates)
    return SimpleNamespace(**values)


def _selection(*ids: str, revision: int = 14):
    return ActivityCriterionSetSelectionSnapshot(
        criterion_set_ids=ids, snapshot_revision=revision
    )


def test_historical_selected_revision_preserves_every_editable_field() -> None:
    source = _detail()
    review = project_native_criterion_set(
        source, _selection("other", "native-r1")
    )
    assert review.criterion_set_id == "native-r1"
    assert review.lineage_id == "native-discussion"
    assert review.is_current is False
    assert review.is_selected is True
    assert review.selected_position == 2
    assert review.revision == 1
    assert review.original_criterion_ids == ("criterion-1", "criterion-2")
    assert review.draft.name == "Jíbara Discussion Assessment"
    assert review.draft.purpose == "Discuss and analyze a text"
    assert review.draft.scope == "reusable"
    assert review.draft.criterion_set_kind == "mixed"
    first, second = review.draft.criteria
    assert first.key == "discussion-participation"
    assert first.standard_id == "SL.PE.11-12.1"
    assert first.alignment_standard_ids == ("RL.CS.11-12.4",)
    assert first.default_scoring_scale_id == "scale-ordinal-1"
    assert first.supported_target_kinds == ("core_student",)
    assert first.status == "active"
    assert second.criterion_kind == "local"
    assert second.standard_id is None
    assert second.supported_target_kinds == ("concord_group",)
    assert second.default_scoring_scale_id is None
    # Native source objects were not changed or replaced.
    assert source.criteria[0].criterion_id == "criterion-1"
    assert source.summary.revision == 1


def test_review_has_no_fake_draft_or_preset_saved_receipt() -> None:
    review = project_native_criterion_set(_detail(), _selection("native-r1"))
    lines = describe_native_criterion_set(
        review,
        native_scale_names={"scale-ordinal-1": "Four-level proficiency"},
    )
    text = "\n".join(lines)
    assert "historical" in text
    assert "Selected for future Scores: yes" in text
    assert "Selection position: 1" in text
    assert "SL.PE.11-12.1 [Core definition not loaded]" in text
    assert "RL.CS.11-12.4 [Core definition not loaded]" in text
    assert "Cluster Group (concord_group)" in text
    assert "Four-level proficiency [native Scale ID: scale-ordinal-1]" in text
    assert "not a saved preset" in text
    assert "Read only:" in text
    assert "No Activity selection" in text
    assert "Draft only" not in text
    assert "Rubric created" not in text


def test_known_core_standard_is_labeled_from_source_without_guessing() -> None:
    lib = SimpleNamespace(standards=(SimpleNamespace(
        standard_id="SL.PE.11-12.1", code="SL.PE.11-12.1",
        short_name="Discussion participation", active=True, tags=(),
    ),))
    review = project_native_criterion_set(_detail(), _selection("native-r1"))
    text = "\n".join(describe_native_criterion_set(
        review, standards_library=lib,
    ))
    assert "Discussion participation [Core ID: SL.PE.11-12.1; active]" in text
    assert "RL.CS.11-12.4 [Core definition unavailable]" in text


def test_inactive_historical_standard_not_misrepresented_as_current() -> None:
    lib = SimpleNamespace(standards=(SimpleNamespace(
        standard_id="SL.PE.11-12.1", code="SL.PE.11-12.1",
        short_name="Historical discussion", active=False, tags=(),
    ),))
    review = project_native_criterion_set(_detail(), _selection("native-r1"))
    text = "\n".join(describe_native_criterion_set(
        review, standards_library=lib,
    ))
    assert "inactive/deprecated" in text
    assert "Historical discussion" in text


@pytest.mark.parametrize("selection", [
    _selection("native-r1", revision=15),
    _selection("native-r1", "native-r1"),
    _selection("unrelated"),
])
def test_mismatched_snapshot_selection_or_duplicate_refuses(selection) -> None:
    with pytest.raises(NativeRubricReviewError):
        project_native_criterion_set(_detail(), selection)


def test_member_count_and_membership_are_guarded() -> None:
    detail = _detail()
    detail.summary.criterion_count = 3
    with pytest.raises(NativeRubricReviewError, match="incomplete"):
        project_native_criterion_set(detail, _selection("native-r1"))
    detail = _detail()
    detail.criteria = (
        _criterion(criterion_set_id="another-set"),
        detail.criteria[1],
    )
    with pytest.raises(NativeRubricReviewError, match="does not belong"):
        project_native_criterion_set(detail, _selection("native-r1"))
    detail = _detail()
    detail.criteria = (
        detail.criteria[0],
        _criterion(criterion_id="criterion-1"),
    )
    with pytest.raises(NativeRubricReviewError, match="unique"):
        project_native_criterion_set(detail, _selection("native-r1"))


def _activity() -> ActivitySummary:
    return ActivitySummary(
        class_id="class-1", activity_id="activity-1",
        title="Jíbara (synthetic)", status="active",
        scoring_orientation="mixed", session_count=1,
        group_count=2, snapshot_revision=14,
    )


def test_teacher_browse_shows_exact_order_and_never_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    detail = _detail()
    receipts = []
    monkeypatch.setattr(menu, "_latest", lambda _: _activity())
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selection("other", "native-r1"),
    )
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *a, **k: (
        detail.summary,
    ))
    monkeypatch.setattr(menu, "select_one", lambda *a, **k: detail.summary)
    monkeypatch.setattr(menu, "show_criterion_set", lambda *a, **k: detail)
    monkeypatch.setattr(menu, "list_scoring_scales", lambda *a, **k: ())
    monkeypatch.setattr(menu, "show_result", lambda title, lines: (
        receipts.append((title, tuple(lines)))
    ))
    monkeypatch.setattr(menu, "create_criterion_set", lambda *a, **k: (
        pytest.fail("Browse must not create records")
    ))
    monkeypatch.setattr(menu, "select_activity_criterion_sets", lambda *a, **k: (
        pytest.fail("Browse must not change selection")
    ))
    menu._browse_criterion_sets(_activity())
    assert receipts[0][0] == "Existing Rubric — Read Only"
    rendered = "\n".join(receipts[0][1])
    assert rendered.index("Individual discussion participation") < rendered.index(
        "Cluster collaborative analysis"
    )
    assert "historical" in rendered
    assert "Selection position: 2" in rendered


def test_teacher_browse_empty_has_explanatory_next_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipts = []
    monkeypatch.setattr(menu, "_latest", lambda _: _activity())
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selection(),
    )
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *a, **k: ())
    monkeypatch.setattr(menu, "show_result", lambda title, lines: (
        receipts.append((title, tuple(lines)))
    ))
    monkeypatch.setattr(menu, "select_one", lambda *a, **k: (
        pytest.fail("No selection is available")
    ))
    menu._browse_criterion_sets(_activity())
    assert receipts[0][0] == "No Rubrics Yet"
    assert "Create and use" in " ".join(receipts[0][1])


def test_teacher_browse_refuses_stale_selection_without_displaying_definition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipts = []
    monkeypatch.setattr(menu, "_latest", lambda _: _activity())
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *a, **k: _selection("native-r1", revision=15),
    )
    monkeypatch.setattr(menu, "show_result", lambda title, lines: (
        receipts.append((title, tuple(lines)))
    ))
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *a, **k: (
        pytest.fail("Stale state must be reloaded")
    ))
    menu._browse_criterion_sets(_activity())
    assert receipts[0][0] == "Criterion Set Error"
    assert "changed" in " ".join(receipts[0][1])
