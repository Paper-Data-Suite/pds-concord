"""#145 Slice 6D: disambiguate native rubric selection before opening it."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_scoring as menu
from concord.menu_context import CancelMenuAction, MenuSessionContext


def _summary(
    identity: str,
    *,
    name: str = "Synthetic discussion assessment",
    kind: str = "mixed",
    count: int = 2,
    selected: bool = False,
    current: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        criterion_set_id=identity,
        lineage_id=f"lineage-{identity}",
        name=name,
        revision=1,
        criterion_set_kind=kind,
        criterion_count=count,
        is_current=current,
        is_selected=selected,
    )


def _activity() -> SimpleNamespace:
    return SimpleNamespace(
        class_id="synthetic-class",
        activity_id="synthetic-activity",
        title="Synthetic discussion",
        scoring_orientation="mixed",
        snapshot_revision=14,
    )


def test_metadata_disambiguates_same_name_revision() -> None:
    first = _summary("mixed-two", selected=True)
    second = _summary("local-one", kind="local", count=1)
    labels = menu._native_rubric_choice_labels((first, second))
    assert labels == (
        "Synthetic discussion assessment (revision 1; mixed; 2 Criteria; "
        "current; selected)",
        "Synthetic discussion assessment (revision 1; local; 1 Criterion; "
        "current; not selected)",
    )
    assert len(set(labels)) == 2
    assert all("[exact ID:" not in label for label in labels)


def test_identical_metadata_disambiguates_by_exact_stable_id() -> None:
    first = _summary("set-a")
    second = _summary("set-b")
    labels = menu._native_rubric_choice_labels((first, second))
    assert len(set(labels)) == 2
    assert labels[0].endswith("[exact ID: set-a]")
    assert labels[1].endswith("[exact ID: set-b]")
    assert labels[0].startswith("Synthetic discussion assessment (revision 1;")
    assert labels[1].startswith("Synthetic discussion assessment (revision 1;")
    assert menu._native_rubric_choice_labels((second, first)) == labels[::-1]


def test_current_historical_and_selection_state_are_shown() -> None:
    labels = menu._native_rubric_choice_labels((
        _summary("current", selected=True),
        _summary("historical", current=False),
    ))
    assert "current; selected" in labels[0]
    assert "historical; not selected" in labels[1]
    assert "[exact ID:" not in labels[0]
    assert "[exact ID:" not in labels[1]


def test_sparse_legacy_test_doubles_do_not_invent_metadata() -> None:
    item = SimpleNamespace(
        criterion_set_id="old", name="Old rubric", revision=3,
        is_current=True, is_selected=False,
    )
    assert menu._native_rubric_choice_labels((item,)) == (
        "Old rubric (revision 3; current; not selected)",
    )


@pytest.mark.parametrize(
    ("method", "expected_title"),
    (
        ("_browse_criterion_sets", "Review an existing rubric"),
        (
            "_save_criterion_set_as_preset",
            "Save an existing assessment for another class",
        ),
        ("_use_existing_criterion_set", "Use an existing rubric"),
        ("_revise_criterion_set", "Revise a current rubric"),
    ),
)
@pytest.mark.parametrize("fully_colliding_metadata", (False, True))
def test_native_menu_choosers_disambiguate_before_any_write(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    expected_title: str,
    fully_colliding_metadata: bool,
) -> None:
    first = _summary("set-1", selected=False)
    second = (
        _summary("set-2") if fully_colliding_metadata
        else _summary("set-2", kind="local", count=1)
    )
    summaries = (first, second)
    observed: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(menu, "_latest", lambda _summary: _activity())
    monkeypatch.setattr(menu, "_library", lambda: None)
    monkeypatch.setattr(
        menu, "show_activity", lambda *args, **kwargs: SimpleNamespace(
            standards_profile_id=None, focus_standard_ids=(),
        ),
    )
    monkeypatch.setattr(
        menu, "read_activity_criterion_set_selection",
        lambda *args, **kwargs: SimpleNamespace(
            snapshot_revision=14, criterion_set_ids=(),
        ),
    )
    monkeypatch.setattr(menu, "list_criterion_sets", lambda *args, **kwargs: summaries)

    def choose(title: str, items: object, labels: tuple[str, ...], **kwargs: object):
        assert tuple(items) == summaries
        observed.append((title, tuple(labels)))
        raise CancelMenuAction

    monkeypatch.setattr(menu, "select_one", choose)
    monkeypatch.setattr(
        menu, "show_criterion_set",
        lambda *args, **kwargs: pytest.fail("Canceled choice must not read a rubric"),
    )
    monkeypatch.setattr(
        menu, "show_result",
        lambda *args, **kwargs: pytest.fail("Canceled choice must not show an error"),
    )
    monkeypatch.setattr(
        menu, "_handle_error",
        lambda *args, **kwargs: pytest.fail(
            "Canceled choice must not produce an error"
        ),
    )
    if method == "_browse_criterion_sets":
        menu._browse_criterion_sets(_activity())
    else:
        getattr(menu, method)(_activity(), MenuSessionContext())

    assert len(observed) == 1
    title, labels = observed[0]
    assert title == expected_title
    assert len(set(labels)) == 2
    assert all("revision 1" in label for label in labels)
    assert all("current; not selected" in label for label in labels)
    if fully_colliding_metadata:
        assert labels[0].endswith("[exact ID: set-1]")
        assert labels[1].endswith("[exact ID: set-2]")
    else:
        assert "mixed; 2 Criteria" in labels[0]
        assert "local; 1 Criterion" in labels[1]
        assert all("[exact ID:" not in label for label in labels)
