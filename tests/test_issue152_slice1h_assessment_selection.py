"""Concord #152 Slice 1H: teacher-safe assessment selection and recovery."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

import concord.menu_artifact_scoring as menu
from concord.models import Criterion, ScoreTargetReference, ScoringScale
from concord.workflows.artifact_routine_scoring import (
    ArtifactRoutineScoringContext,
)
from concord.workflows.artifact_routine_scoring_selection import (
    RoutineScoringScaleOptions,
)
from concord.workflows.errors import ConcordWorkflowValidationError


def _context() -> ArtifactRoutineScoringContext:
    return cast(
        ArtifactRoutineScoringContext,
        SimpleNamespace(activity_id="synthetic-activity"),
    )


def _target() -> ScoreTargetReference:
    return ScoreTargetReference(
        target_kind="concord_group",
        target_id="group-synthetic",
        owning_system="concord",
    )


def _criterion(identity: str, label: str) -> Criterion:
    return cast(
        Criterion,
        SimpleNamespace(
            criterion_id=identity,
            label=label,
            criterion_kind="local",
        ),
    )


def _scale(identity: str, name: str) -> ScoringScale:
    return cast(
        ScoringScale,
        SimpleNamespace(scoring_scale_id=identity, name=name),
    )


def _options(
    scales: tuple[ScoringScale, ...],
    *,
    default: ScoringScale | None = None,
    status: str = "not_configured",
) -> RoutineScoringScaleOptions:
    return RoutineScoringScaleOptions(
        scales=scales,
        configured_default_scoring_scale_id=(
            None if default is None else default.scoring_scale_id
        ),
        default_scale=default,
        default_scale_status=status,
    )


@pytest.mark.parametrize("label", ("", "  "))
def test_blank_criterion_prevents_any_teacher_choice(
    monkeypatch: pytest.MonkeyPatch, label: str,
) -> None:
    criterion = _criterion("private-criterion-id", label)
    monkeypatch.setattr(
        menu, "routine_criteria_for_target",
        lambda *_args: (criterion,),
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("No Criterion should be offered without a verified label.")

    monkeypatch.setattr(menu, "select_one", forbidden)
    with pytest.raises(ConcordWorkflowValidationError) as error:
        menu._choose_criterion(_context(), _target())
    assert "Criterion label" in str(error.value)
    assert "Assessment Setup" in str(error.value)
    assert "private-criterion-id" not in str(error.value)
    assert "no Score was recorded" in str(error.value)


def test_missing_compatible_criterion_has_recovery_instructions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu, "routine_criteria_for_target", lambda *_args: ()
    )
    monkeypatch.setattr(
        menu, "select_one",
        lambda *_a, **_kw: pytest.fail("No empty Criterion choice permitted"),
    )
    with pytest.raises(ConcordWorkflowValidationError) as error:
        menu._choose_criterion(_context(), _target())
    assert "No current compatible Criterion" in str(error.value)
    assert "Criterion Set" in str(error.value)


def test_duplicate_criteria_use_distinct_labels_and_exact_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _criterion("criterion-1", "Group collaboration")
    second = _criterion("criterion-2", "Group collaboration")
    monkeypatch.setattr(
        menu, "routine_criteria_for_target",
        lambda *_args: (first, second),
    )
    observed: list[tuple[str, ...]] = []

    def choose(
        title: str,
        items: tuple[Criterion, ...],
        labels: tuple[str, ...],
        **_kw: object,
    ) -> Criterion:
        assert title == "Choose Criterion"
        assert items == (first, second)
        observed.append(labels)
        return items[1]

    monkeypatch.setattr(menu, "select_one", choose)
    assert menu._choose_criterion(_context(), _target()) is second
    assert "1 of 2" in observed[0][0]
    assert "2 of 2" in observed[0][1]
    assert "criterion-1" not in " ".join(observed[0])
    assert "criterion-2" not in " ".join(observed[0])


def test_continuation_uses_same_criterion_label_integrity() -> None:
    first = _criterion("criterion-1", "Same")
    second = _criterion("criterion-2", "Same")
    labels = menu._criterion_choice_labels((first, second))
    assert "1 of 2" in labels[0]
    assert "2 of 2" in labels[1]
    with pytest.raises(ConcordWorkflowValidationError, match="Criterion label"):
        menu._criterion_choice_labels((_criterion("private", " "),))


@pytest.mark.parametrize("name", ("", "  "))
def test_blank_scale_blocks_selection_before_teacher_prompt(
    monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    scale = _scale("private-scale-id", name)
    monkeypatch.setattr(
        menu, "routine_scale_options",
        lambda *_args: _options((scale,)),
    )
    monkeypatch.setattr(
        menu, "select_one",
        lambda *_a, **_kw: pytest.fail("No blank Scale selection permitted"),
    )
    with pytest.raises(ConcordWorkflowValidationError) as error:
        menu._choose_scale(_context(), _target(), "criterion-1")
    assert "Scoring Scale label" in str(error.value)
    assert "Assessment Setup" in str(error.value)
    assert "private-scale-id" not in str(error.value)


def test_no_active_scale_refuses_empty_menu_with_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        menu, "routine_scale_options",
        lambda *_args: _options((), status="missing_or_historical"),
    )
    monkeypatch.setattr(
        menu, "select_one",
        lambda *_a, **_kw: pytest.fail("No empty Scale menu permitted"),
    )
    with pytest.raises(ConcordWorkflowValidationError) as error:
        menu._choose_scale(_context(), _target(), "criterion-1")
    assert "No current active Scoring Scale" in str(error.value)
    assert "Assessment Setup" in str(error.value)
    assert "no Score was recorded" in str(error.value)


def test_duplicate_scale_names_remain_distinct_without_opaque_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _scale("scale-private-1", "Four levels")
    second = _scale("scale-private-2", "Four levels")
    monkeypatch.setattr(
        menu, "routine_scale_options",
        lambda *_args: _options((first, second)),
    )
    seen: dict[str, object] = {}

    def choose(
        title: str,
        items: tuple[ScoringScale, ...],
        labels: tuple[str, ...],
        **_kwargs: object,
    ) -> ScoringScale:
        assert title == "Choose Scoring Scale"
        seen["labels"] = labels
        return items[1]

    monkeypatch.setattr(menu, "select_one", choose)
    assert menu._choose_scale(_context(), _target(), "criterion-1") is second
    labels = cast(tuple[str, ...], seen["labels"])
    assert "1 of 2" in labels[0]
    assert "2 of 2" in labels[1]
    assert "scale-private" not in " ".join(labels)


def test_stale_default_is_explained_but_not_silently_selected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active = _scale("scale-active", "Current rubric")
    monkeypatch.setattr(
        menu, "routine_scale_options",
        lambda *_args: _options((active,), status="missing_or_historical"),
    )
    seen: list[tuple[str, ...]] = []

    def choose(
        _title: str,
        items: tuple[ScoringScale, ...],
        labels: tuple[str, ...],
        *,
        help_text: str,
    ) -> ScoringScale:
        assert "missing or historical" in help_text
        assert "No Score value is selected" in help_text
        seen.append(labels)
        return items[0]

    monkeypatch.setattr(menu, "select_one", choose)
    assert menu._choose_scale(_context(), _target(), "criterion-1") is active
    assert seen == [("Current rubric",)]


def test_valid_default_is_labeled_not_auto_authorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    default = _scale("scale-default", "Performance rubric")
    other = _scale("scale-other", "Other current rubric")
    monkeypatch.setattr(
        menu, "routine_scale_options",
        lambda *_args: _options(
            (other, default), default=default, status="valid"
        ),
    )
    seen: list[str] = []

    def choose(
        _title: str,
        items: tuple[ScoringScale, ...],
        labels: tuple[str, ...],
        **_kwargs: object,
    ) -> ScoringScale:
        assert items[0] is default
        assert "[default]" in labels[0]
        seen.extend(labels)
        return items[1]

    monkeypatch.setattr(menu, "select_one", choose)
    assert menu._choose_scale(_context(), _target(), "criterion-1") is other
    assert len(seen) == 2
