"""#145 Slice 3: distinct, exact, read-only saved assessment selection."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_scoring as scoring
from concord.menu_context import CancelMenuAction


def _criterion(*, name: str = "Discussion Participation") -> SimpleNamespace:
    return SimpleNamespace(
        key="discussion-participation",
        label=name,
        definition="Respond with textual evidence and listen to peers.",
        criterion_kind="standard_backed",
        standard_id="SL.PE.11-12.1",
        alignment_standard_ids=("RL.CR.11-12.1",),
        supported_target_kinds=("core_student", "concord_group"),
        default_scoring_scale_preset_id="scale-preset-123",
        default_scoring_scale_preset_revision_id="scale-revision-123",
    )


def _saved(value: str) -> SimpleNamespace:
    return SimpleNamespace(
        preset_id=f"criterion-preset-{value}",
        preset_revision_id=f"criterion-revision-{value}",
        revision=1,
        name="Jíbara Discussion Assessment",
        purpose="Evaluate discussion and collaborative analysis.",
        status="active",
        criterion_set_kind="mixed",
        standards_profile_id="english-12",
        criteria=(_criterion(),),
    )


def test_duplicate_names_show_stable_exact_distinctions() -> None:
    first, second = _saved("first"), _saved("second")
    labels = scoring._saved_criteria_menu_labels((first, second))
    assert len(labels) == 2
    assert labels[0] != labels[1]
    assert first.preset_id in labels[0]
    assert second.preset_id in labels[1]
    assert all("1 Criteria" in label for label in labels)
    assert all("saved revision 1" in label for label in labels)
    assert all("mixed" in label for label in labels)


def test_distinct_definitions_need_no_extra_id_on_menu() -> None:
    first, second = _saved("first"), _saved("second")
    second.criteria = (_criterion(), _criterion(name="Group Analysis"))
    labels = scoring._saved_criteria_menu_labels((first, second))
    assert labels[0] != labels[1]
    assert "Preset ID" not in labels[0] + labels[1]


def test_read_only_preview_includes_exact_revision_and_criterion_meaning() -> None:
    value = _saved("first")
    preview = "\n".join(scoring._saved_criteria_preview(value))
    for expected in (
        value.preset_id,
        value.preset_revision_id,
        "Evaluate discussion and collaborative analysis.",
        "Discussion Participation",
        "Respond with textual evidence",
        "core student, concord group",
        "SL.PE.11-12.1",
        "RL.CR.11-12.1",
        "scale-preset-123",
        "scale-revision-123",
    ):
        assert expected in preview


@pytest.mark.parametrize("approve", (False, True))
def test_saved_criteria_selection_previews_exact_selected_revision_before_write(
    monkeypatch: pytest.MonkeyPatch, approve: bool
) -> None:
    first, second = _saved("first"), _saved("second")
    summaries = tuple(
        SimpleNamespace(
            preset_id=value.preset_id,
            preset_revision_id=value.preset_revision_id,
            revision=value.revision,
        )
        for value in (first, second)
    )
    current = SimpleNamespace(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic Activity",
        snapshot_revision=7,
    )
    monkeypatch.setattr(scoring, "CriterionSetPresetRevision", SimpleNamespace)
    monkeypatch.setattr(scoring, "_latest", lambda activity: current)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring, "list_presets",
        lambda kind: summaries if kind == "criterion_set" else (),
    )
    requested: list[tuple[str, str, str]] = []

    def fetch(kind: str, preset_id: str, revision_id: str) -> SimpleNamespace:
        requested.append((kind, preset_id, revision_id))
        found = {first.preset_id: first, second.preset_id: second}
        result = found[preset_id]
        assert result.preset_revision_id == revision_id
        return result

    monkeypatch.setattr(scoring, "get_preset_revision", fetch)
    seen_labels: list[str] = []

    def choose(
        title: str, values: object, labels: tuple[str, ...], **kwargs: object
    ) -> SimpleNamespace:
        assert title == "Choose Saved Assessment"
        seen_labels.extend(labels)
        assert len(values) == 2  # type: ignore[arg-type]
        return second

    monkeypatch.setattr(scoring, "select_one", choose)
    monkeypatch.setattr(scoring, "_choose_saved_scale_for_preset", lambda value: None)
    displayed: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(
        scoring, "show_result",
        lambda title, lines: displayed.append((title, tuple(lines))),
    )
    prepared = SimpleNamespace(
        review_digest="synthetic-review-digest",
        criterion_preset_name=second.name,
        criterion_count=1,
        scoring_scale_preset_name=None,
        standards_profile_id="english-12",
    )
    monkeypatch.setattr(scoring, "prepare_scoring_setup", lambda *args, **kw: prepared)
    reviews: list[tuple[str, ...]] = []

    def confirm(title: str, keyword: str, lines: tuple[str, ...]) -> bool:
        assert title == "Use Saved Scoring Setup"
        assert keyword == "USE"
        reviews.append(tuple(lines))
        return approve

    monkeypatch.setattr(scoring, "confirm_write", confirm)
    materialized: list[object] = []

    def materialize(request: object, **kwargs: object) -> SimpleNamespace:
        materialized.append(request)
        assert kwargs["review_digest"] == "synthetic-review-digest"
        return SimpleNamespace(
            criterion_set_id=request.criterion_set_id,  # type: ignore[attr-defined]
            criterion_ids=request.criterion_ids,  # type: ignore[attr-defined]
            scoring_scale_id=None,
            commit=SimpleNamespace(snapshot_revision=8),
        )

    monkeypatch.setattr(scoring, "materialize_scoring_setup", materialize)
    monkeypatch.setattr(
        scoring, "_handle_error", lambda activity, error: pytest.fail(str(error))
    )
    scoring._use_saved_scoring_setup(
        SimpleNamespace(), SimpleNamespace(require_actor=lambda: "teacher")
    )
    assert requested == [
        ("criterion_set", first.preset_id, first.preset_revision_id),
        ("criterion_set", second.preset_id, second.preset_revision_id),
    ]
    assert seen_labels[0] != seen_labels[1]
    assert displayed[0][0] == "Saved Assessment — Read-only Preview"
    assert second.preset_revision_id in "\n".join(displayed[0][1])
    assert first.preset_revision_id not in "\n".join(displayed[0][1])
    assert reviews and second.preset_revision_id in "\n".join(reviews[0])
    assert len(materialized) == int(approve)
    if approve:
        request = materialized[0]
        assert getattr(request, "criterion_preset_id") == second.preset_id
        assert getattr(request, "criterion_preset_revision_id") == (
            second.preset_revision_id
        )
        assert displayed[-1][0] == "Scoring Setup Added"
    else:
        assert len(displayed) == 1


def test_back_from_scale_selection_does_not_prepare_or_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    value = _saved("first")
    summary = SimpleNamespace(
        preset_id=value.preset_id,
        preset_revision_id=value.preset_revision_id,
        revision=value.revision,
    )
    monkeypatch.setattr(scoring, "CriterionSetPresetRevision", SimpleNamespace)
    monkeypatch.setattr(
        scoring, "_latest", lambda activity: SimpleNamespace(snapshot_revision=7)
    )
    monkeypatch.setattr(scoring, "list_presets", lambda kind: (summary,))
    monkeypatch.setattr(scoring, "get_preset_revision", lambda *args: value)
    monkeypatch.setattr(scoring, "select_one", lambda *args, **kwargs: value)
    monkeypatch.setattr(scoring, "show_result", lambda *args: None)

    def back(value: object) -> None:
        raise CancelMenuAction

    monkeypatch.setattr(scoring, "_choose_saved_scale_for_preset", back)
    monkeypatch.setattr(
        scoring, "prepare_scoring_setup",
        lambda *a, **k: pytest.fail("Unexpected write preparation"),
    )
    monkeypatch.setattr(
        scoring, "_handle_error", lambda *args: pytest.fail("Unexpected error")
    )
    scoring._use_saved_scoring_setup(
        SimpleNamespace(), SimpleNamespace(require_actor=lambda: "teacher")
    )
