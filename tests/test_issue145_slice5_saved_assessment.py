"""Issue #145 Slice 5: exact reusable assessment save and Scale mapping."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest

import concord.criterion_preset_guidance as guidance
import concord.menu_scoring as menu
from concord.models import ScoringScaleLevel
from concord.reusable_presets import ScoringScalePresetRevision
from concord.workflows.context import provenance
from concord.workflows.models import WorkflowActor
from concord.workflows.scoring_scales import ScoringScaleDetail


def _levels(*values: object) -> tuple[ScoringScaleLevel, ...]:
    return tuple(
        ScoringScaleLevel(
            value=cast(str | int | float | bool, value),
            label=f"Level {index}",
            meaning="Synthetic evaluation",
            position=index,
        )
        for index, value in enumerate(values, 1)
    )


def _native(*values: object) -> ScoringScaleDetail:
    return cast(
        ScoringScaleDetail,
        SimpleNamespace(
            summary=SimpleNamespace(
                scale_type="ordinal", intended_use="Class discussion",
            ),
            levels=_levels(*values),
            aggregation_guidance=None,
        ),
    )


def _preset(*values: object) -> ScoringScalePresetRevision:
    return ScoringScalePresetRevision(
        preset_id="saved-scale", preset_revision_id="saved-scale-r1",
        revision=1, name="Discussion scale", scale_type="ordinal",
        status="active", levels=_levels(*values),
        created_provenance=provenance(
            WorkflowActor(actor_id="synthetic-scale-teacher")
        ),
        intended_use="Class discussion", aggregation_guidance=None,
    )


def _criterion(default: str | None) -> SimpleNamespace:
    return SimpleNamespace(default_scoring_scale_id=default)


def test_default_scale_assessment_retains_first_seen_order() -> None:
    assessment = guidance.assess_native_defaults(
        (_criterion("scale-b"), _criterion(None), _criterion("scale-a"),
         _criterion("scale-b"))
    )
    assert assessment.default_ids == ("scale-b", "scale-a")
    assert assessment.native_scale_id is None
    assert "Multiple distinct" in assessment.notice
    assert "excluded" in assessment.notice
    assert "Omitted native" in guidance.scale_mapping_receipt(
        assessment, preset_id=None, preset_revision_id=None
    )[-2]


def test_no_scale_and_one_scale_have_distinct_outcomes() -> None:
    no_default = guidance.assess_native_defaults((_criterion(None),))
    assert no_default.default_ids == ()
    assert no_default.native_scale_id is None
    assert "No Scoring Scale preset" in guidance.scale_mapping_receipt(
        no_default, preset_id=None, preset_revision_id=None
    )[-1]
    one = guidance.assess_native_defaults(
        (_criterion("scale-1"), _criterion("scale-1"))
    )
    assert one.native_scale_id == "scale-1"
    assert guidance.scale_mapping_receipt(
        one, preset_id="preset-1", preset_revision_id="preset-1-v1"
    )[2] == "Exact matched preset: preset-1 / preset-1-v1"


def test_bad_scale_mapping_never_crosses_kind_or_pair_boundary() -> None:
    many = guidance.assess_native_defaults(
        (_criterion("scale-1"), _criterion("scale-2"))
    )
    with pytest.raises(ValueError, match="single native Scale"):
        guidance.scale_mapping_receipt(
            many, preset_id="preset", preset_revision_id="preset-v1"
        )
    one = guidance.assess_native_defaults((_criterion("scale-1"),))
    with pytest.raises(ValueError, match="both exact preset IDs"):
        guidance.scale_mapping_receipt(
            one, preset_id="preset", preset_revision_id=None
        )


def test_exact_typed_scale_definition_matches_without_native_identity() -> None:
    native = _native(1, 1.0, "1", True)
    saved = _preset(1, 1.0, "1", True)
    assert guidance.matches_native_scale(native, saved)
    assert not guidance.matches_native_scale(native, _preset(1, 2, "1", True))
    assert not guidance.matches_native_scale(native, _preset(True, 1.0, "1", 1))
    assert not guidance.matches_native_scale(native, _preset(1, "1", 1.0, True))
    assert not guidance.matches_native_scale(
        native, cast(ScoringScalePresetRevision, replace(
            saved, scale_type="teacher_defined"
        ))
    )
    assert not guidance.matches_native_scale(
        native, cast(ScoringScalePresetRevision, replace(
            saved, status="retired"
        ))
    )


def test_exact_match_requires_label_meaning_position_description_and_guidance() -> None:
    original = _preset(1, 2)
    native = _native(1, 2)
    assert guidance.matches_native_scale(native, original)
    for changed in (
        replace(original.levels[0], label="Different"),
        replace(original.levels[0], meaning="Different"),
        replace(original.levels[0], position=4),
        replace(original.levels[0], description="Extra"),
    ):
        assert not guidance.matches_native_scale(
            native, cast(ScoringScalePresetRevision, replace(
                original, levels=(changed, *original.levels[1:])
            ))
        )
    assert not guidance.matches_native_scale(
        native, cast(ScoringScalePresetRevision, replace(
            original, aggregation_guidance="Average scores"
        ))
    )
    assert not guidance.matches_native_scale(
        native, cast(ScoringScalePresetRevision, replace(
            original, intended_use="Another task"
        ))
    )


def _activity() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="synthetic-class", activity_id="synthetic-activity",
        title="Synthetic discussion", snapshot_revision=12,
    )


def _old_set() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="synthetic-class", activity_id="synthetic-activity",
        criterion_set_id="set-r1", name="Discussion rubric", revision=1,
        is_current=False, is_selected=True, snapshot_revision=12,
    )


def _fixture(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    activity = _activity()
    old = _old_set()
    selection = SimpleNamespace(snapshot_revision=12, criterion_set_ids=("set-r1",))
    detail = SimpleNamespace(
        summary=old, criteria=(_criterion(None),)
    )
    calls: dict[str, object] = {"receipts": []}
    monkeypatch.setattr(menu, "_latest", lambda _activity: activity)
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection", lambda *a, **k: selection
    )
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *a, **k: (old,))
    monkeypatch.setattr(menu, "show_criterion_set", lambda *a, **k: detail)
    monkeypatch.setattr(menu, "select_one", lambda title, items, labels, **k: items[0])
    monkeypatch.setattr(
        menu, "show_result",
        lambda title, lines: cast(list[tuple[str, tuple[str, ...]]],
                                  calls["receipts"]).append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        menu, "prepare_criterion_set_preset_from_activity",
        lambda request, **kw: SimpleNamespace(
            name="Synthetic preset", reusable_fields=("Criterion definitions",),
            excluded_state=("Scores and identities",), review_digest="a" * 64
        ),
    )
    monkeypatch.setattr(menu, "CriterionSetPresetRevision", SimpleNamespace)
    monkeypatch.setattr(
        menu, "get_preset_revision",
        lambda kind, preset_id, revision_id: SimpleNamespace(
            preset_id=preset_id, preset_revision_id=revision_id
        ),
    )
    return calls


def test_saving_historical_rubric_is_reviewed_and_separately_authorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _fixture(monkeypatch)

    def confirm(title: str, expected: str, lines: tuple[str, ...]) -> bool:
        captured["confirmation"] = (title, expected, lines)
        return True

    monkeypatch.setattr(menu, "confirm_write", confirm)

    def save(request: object, *, review_digest: str, **kwargs: object) -> object:
        captured["request"] = request
        assert review_digest == "a" * 64
        return SimpleNamespace(
            preset_id=getattr(request, "preset_id"),
            preset_revision_id=getattr(request, "preset_revision_id"),
        )

    monkeypatch.setattr(menu, "save_criterion_set_preset_from_activity", save)
    menu._save_criterion_set_as_preset(
        cast(menu.ActivitySummary, _activity()),
        cast(menu.MenuSessionContext, SimpleNamespace(
            require_actor=lambda: SimpleNamespace(actor_id="synthetic-teacher")
        )),
    )
    request = captured["request"]
    assert getattr(request, "criterion_set_id") == "set-r1"
    assert getattr(request, "expected_snapshot_revision") == 12
    assert getattr(request, "recommended_scoring_scale_preset_id") is None
    title, word, lines = cast(tuple[str, str, tuple[str, ...]],
                              captured["confirmation"])
    assert title == "Save this assessment for another class"
    assert word == "SAVE"
    assert any("historical" in line for line in lines)
    assert any("Scores, Grades, student/Group IDs" in line for line in lines)
    receipts = cast(list[tuple[str, tuple[str, ...]]], captured["receipts"])
    assert receipts[-1][0] == "Assessment Saved for Another Class"
    assert any("Use 'Use saved assessment setup'" in line
               for line in receipts[-1][1])


def test_decline_save_makes_no_service_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _fixture(monkeypatch)
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: False)
    monkeypatch.setattr(
        menu, "save_criterion_set_preset_from_activity",
        lambda *a, **k: pytest.fail("No save approved"),
    )
    menu._save_criterion_set_as_preset(
        cast(menu.ActivitySummary, _activity()),
        cast(menu.MenuSessionContext, SimpleNamespace(
            require_actor=lambda: SimpleNamespace(actor_id="synthetic-teacher")
        )),
    )
    assert captured["receipts"] == []


def test_unknown_save_outcome_does_not_auto_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _fixture(monkeypatch)
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: True)
    attempts: list[str] = []

    def fail(request: object, **kwargs: object) -> object:
        attempts.append(getattr(request, "preset_id"))
        raise OSError("receipt interrupted")

    monkeypatch.setattr(menu, "save_criterion_set_preset_from_activity", fail)
    monkeypatch.setattr(
        menu, "get_preset_revision", lambda *a, **k: (_ for _ in ()).throw(
            FileNotFoundError("cannot inspect")
        ),
    )
    menu._save_criterion_set_as_preset(
        cast(menu.ActivitySummary, _activity()),
        cast(menu.MenuSessionContext, SimpleNamespace(
            require_actor=lambda: SimpleNamespace(actor_id="synthetic-teacher")
        )),
    )
    assert len(attempts) == 1
    receipts = cast(list[tuple[str, tuple[str, ...]]], captured["receipts"])
    assert receipts[-1][0] == "Reusable Assessment Save Outcome Unknown"
    assert any("Do not create a duplicate" in line for line in receipts[-1][1])


def test_stale_activity_refuses_save_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _fixture(monkeypatch)
    current = _activity()
    monkeypatch.setattr(
        menu, "_latest", lambda _activity: SimpleNamespace(
            **{**vars(current), "snapshot_revision": 13}
        ),
    )
    monkeypatch.setattr(menu, "confirm_write", lambda *a, **k: True)
    monkeypatch.setattr(
        menu, "save_criterion_set_preset_from_activity",
        lambda *a, **k: pytest.fail("Stale save should refuse"),
    )
    errors: list[str] = []
    monkeypatch.setattr(
        menu, "_handle_error", lambda activity, error: errors.append(str(error))
    )
    menu._save_criterion_set_as_preset(
        cast(menu.ActivitySummary, _activity()),
        cast(menu.MenuSessionContext, SimpleNamespace(
            require_actor=lambda: SimpleNamespace(actor_id="synthetic-teacher")
        )),
    )
    assert errors and "changed before saved-rubric review" in errors[0]
    assert captured["receipts"] == []


def test_recommendation_only_offers_exact_matching_saved_scale(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = _native(1, 2, 3, 4)
    exact = _preset(1, 2, 3, 4)
    mismatched = replace(exact, preset_id="wrong-scale", levels=_levels(1, 2, 3, 5))
    saved = (
        SimpleNamespace(preset_id="wrong-scale", preset_revision_id="saved-scale-r1"),
        SimpleNamespace(preset_id="saved-scale", preset_revision_id="saved-scale-r1"),
    )
    selected: list[tuple[object, ...]] = []
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(menu, "show_scoring_scale", lambda *a, **k: native)
    monkeypatch.setattr(menu, "list_presets", lambda *a, **k: saved)
    monkeypatch.setattr(
        menu, "get_preset_revision",
        lambda _kind, preset_id, _revision: (
            mismatched if preset_id == "wrong-scale" else exact
        ),
    )

    def choose(title: str, items: tuple[object, ...], labels: object, **k: object):
        selected.append(items)
        return items[-1]

    monkeypatch.setattr(menu, "select_one", choose)
    detail = cast(menu.CriterionSetDetail, SimpleNamespace(
        summary=SimpleNamespace(
            class_id="synthetic-class", activity_id="synthetic-activity"
        ),
        criteria=(_criterion("native-scale-1"),),
    ))
    ids = menu._recommended_scale_for_native_set(detail)
    assert ids == ("saved-scale", "saved-scale-r1")
    assert len(selected) == 1 and selected[0] == (None, exact)


def test_mismatched_scale_cannot_be_recommended(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved = _preset(1, 2)
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(menu, "show_scoring_scale", lambda *a, **k: _native(1, 3))
    monkeypatch.setattr(
        menu, "list_presets",
        lambda *a, **k: (SimpleNamespace(
            preset_id="saved-scale", preset_revision_id="saved-scale-r1"
        ),),
    )
    monkeypatch.setattr(menu, "get_preset_revision", lambda *a, **k: saved)
    monkeypatch.setattr(
        menu, "select_one", lambda *a, **k: pytest.fail(
            "Mismatched Scale must never become a selectable candidate"
        ),
    )
    notices: list[str] = []
    monkeypatch.setattr(
        menu, "show_result", lambda title, lines: notices.append(title)
    )
    detail = cast(menu.CriterionSetDetail, SimpleNamespace(
        summary=SimpleNamespace(
            class_id="synthetic-class", activity_id="synthetic-activity"
        ),
        criteria=(_criterion("native-scale-1"),),
    ))
    assert menu._recommended_scale_for_native_set(detail) == (None, None)
    assert notices == ["No Exact Reusable Scale Match"]
