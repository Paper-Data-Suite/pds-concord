"""#145 Slice 4: explicit same-lineage rubric revision selection."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_scoring as scoring


@pytest.mark.parametrize(
    ("selected", "chosen", "lineage", "replace", "expected"),
    (
        (("old", "other"), "new", frozenset({"old", "new"}),
         True, ("new", "other")),
        (("other", "old"), "new", frozenset({"old", "new"}),
         True, ("other", "new")),
        (("old", "other"), "new", frozenset({"old", "new"}),
         False, ("old", "other", "new")),
        (("old", "new", "other"), "new", frozenset({"old", "new"}),
         True, ("new", "other")),
        (("new", "old", "other"), "new", frozenset({"old", "new"}),
         False, ("new", "old", "other")),
        (("other",), "new", frozenset({"new"}),
         True, ("other", "new")),
        ((), "new", frozenset({"new"}), True, ("new",)),
    ),
)
def test_selection_planning_preserves_order_and_lineages(
    selected: tuple[str, ...],
    chosen: str,
    lineage: frozenset[str],
    replace: bool,
    expected: tuple[str, ...],
) -> None:
    actual = scoring._plan_existing_rubric_selection(  # noqa: SLF001
        selected, chosen, lineage, replace_prior_revisions=replace,
    )
    assert actual == expected


def test_review_lines_include_exact_ids_and_order() -> None:
    lines = scoring._describe_selected_rubric_revisions(  # noqa: SLF001
        ("a", "b"), {"a": "Rubric rev 1", "b": "Rubric rev 2"}
    )
    assert len(lines) == 2
    assert "1. Rubric rev 1" in lines[0]
    assert "exact ID: a" in lines[0]
    assert "2. Rubric rev 2" in lines[1]
    assert "exact ID: b" in lines[1]
    empty = scoring._describe_selected_rubric_revisions((), {})  # noqa: SLF001
    assert empty == ("  (none)",)


@pytest.mark.parametrize(
    ("choice", "expected"),
    (
        ("replace", ("new", "other")),
        ("retain", ("old", "other", "new")),
    ),
)
def test_use_existing_rubric_requires_explicit_choice_and_verifies(
    monkeypatch: pytest.MonkeyPatch,
    choice: str,
    expected: tuple[str, ...],
) -> None:
    current = SimpleNamespace(
        class_id="class", activity_id="activity",
        snapshot_revision=4, title="Synthetic",
    )
    older = SimpleNamespace(
        criterion_set_id="old", lineage_id="lineage", revision=1,
        name="Rubric", is_current=False, is_selected=True,
    )
    newer = SimpleNamespace(
        criterion_set_id="new", lineage_id="lineage", revision=2,
        name="Rubric", is_current=True, is_selected=False,
    )
    other = SimpleNamespace(
        criterion_set_id="other", lineage_id="another", revision=1,
        name="Other", is_current=True, is_selected=True,
    )
    summaries = (older, newer, other)
    state = {"ids": ("old", "other"), "snapshot": 4}
    observed: list[tuple[str, object]] = []

    monkeypatch.setattr(scoring, "_latest", lambda _: current)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring, "list_criterion_sets", lambda *args, **kwargs: summaries
    )
    monkeypatch.setattr(
        scoring, "show_criterion_set", lambda *args, **kwargs: SimpleNamespace()
    )
    monkeypatch.setattr(
        scoring, "project_native_criterion_set",
        lambda *args: SimpleNamespace(criterion_set_id="new"),
    )
    monkeypatch.setattr(
        scoring, "describe_native_criterion_set",
        lambda *args, **kwargs: ("Exact current rubric",),
    )

    def read(*args: object, **kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            criterion_set_ids=state["ids"],
            snapshot_revision=state["snapshot"],
        )

    monkeypatch.setattr(scoring, "read_activity_criterion_set_selection", read)

    def select(
        title: str, values: object, labels: object, **kwargs: object
    ) -> object:
        observed.append(("select", title))
        return newer if title == "Use an existing rubric" else choice

    monkeypatch.setattr(scoring, "select_one", select)

    def confirm(title: str, keyword: str, lines: tuple[str, ...]) -> bool:
        assert keyword == "USE"
        assert "Current selections (ordered):" in lines
        assert "Proposed selections (ordered):" in lines
        assert any("exact ID: old" in line for line in lines)
        assert any("exact ID: new" in line for line in lines)
        removed_count = 1 if choice == "replace" else 0
        assert f"Earlier selections to deselect: {removed_count}" in lines
        return True

    monkeypatch.setattr(scoring, "confirm_write", confirm)

    def write(request: object, **kwargs: object) -> object:
        assert getattr(request, "criterion_set_ids") == expected
        assert getattr(request, "expected_snapshot_revision") == 4
        state["ids"] = expected
        state["snapshot"] = 5
        return SimpleNamespace(commit=SimpleNamespace(snapshot_revision=5))

    monkeypatch.setattr(scoring, "select_activity_criterion_sets", write)
    monkeypatch.setattr(
        scoring, "show_result",
        lambda title, lines: observed.append(("receipt", title)),
    )
    monkeypatch.setattr(
        scoring, "_handle_error",
        lambda activity, error: pytest.fail(str(error)),
    )
    scoring._use_existing_criterion_set(  # noqa: SLF001
        SimpleNamespace(), SimpleNamespace(require_actor=lambda: "teacher")
    )
    assert ("select", "Using a revised rubric — Selection choice") in observed
    assert ("receipt", "Existing Rubric Selected") in observed


def test_score_protection_refuses_replacement_of_used_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = SimpleNamespace(
        class_id="c", activity_id="a", snapshot_revision=3,
        title="Synthetic",
    )
    old = SimpleNamespace(
        criterion_set_id="old", lineage_id="same", revision=1,
        name="Rubric", is_current=False, is_selected=True,
    )
    new = SimpleNamespace(
        criterion_set_id="new", lineage_id="same", revision=2,
        name="Rubric", is_current=True, is_selected=False,
    )
    selection = SimpleNamespace(criterion_set_ids=("old",), snapshot_revision=3)
    monkeypatch.setattr(scoring, "_latest", lambda _: current)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring, "list_criterion_sets", lambda *args, **kwargs: (old, new)
    )
    monkeypatch.setattr(
        scoring, "show_criterion_set", lambda *args, **kwargs: SimpleNamespace()
    )
    monkeypatch.setattr(
        scoring, "project_native_criterion_set",
        lambda *args: SimpleNamespace(criterion_set_id="new"),
    )
    monkeypatch.setattr(
        scoring, "describe_native_criterion_set", lambda *args, **kwargs: ()
    )
    monkeypatch.setattr(
        scoring, "read_activity_criterion_set_selection",
        lambda *args, **kwargs: selection,
    )
    monkeypatch.setattr(
        scoring, "select_one",
        lambda title, *args, **kwargs:
            new if title == "Use an existing rubric" else "replace",
    )
    monkeypatch.setattr(scoring, "confirm_write", lambda *args, **kwargs: True)

    def refuse(*args: object, **kwargs: object) -> object:
        raise ValueError("Cannot deselect revision used by historical Scores")

    monkeypatch.setattr(scoring, "select_activity_criterion_sets", refuse)
    notices: list[str] = []
    monkeypatch.setattr(
        scoring, "show_result", lambda title, lines: notices.append(title)
    )
    monkeypatch.setattr(
        scoring, "_handle_error",
        lambda activity, error: pytest.fail(str(error)),
    )
    scoring._use_existing_criterion_set(  # noqa: SLF001
        SimpleNamespace(), SimpleNamespace(require_actor=lambda: "teacher")
    )
    assert selection.criterion_set_ids == ("old",)
    assert notices == ["Existing Rubric Selection Not Verified"]
