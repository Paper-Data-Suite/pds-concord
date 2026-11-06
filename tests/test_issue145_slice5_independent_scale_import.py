"""#145 Slice 5: independently import saved Scoring Scales to an Activity."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from concord import menu_scoring as scoring
from concord.menu_context import CancelMenuAction


def _level(value: object, label: str) -> SimpleNamespace:
    return SimpleNamespace(value=value, label=label, meaning=f"Meaning: {label}")


def _saved(name: str = "Four-Level Standards Rubric Scale") -> SimpleNamespace:
    return SimpleNamespace(
        preset_id="scale-preset-test", preset_revision_id="scale-revision-test",
        revision=2, status="active", name=name, scale_type="ordinal",
        levels=(
            _level(1, "Developing"), _level(2, "Approaching"),
            _level(3, "Meeting"), _level(4, "Exceeding"),
        ),
        intended_use="Students and Groups",
        aggregation_guidance="Interpret most recent evidence; no calculation",
    )


def test_saved_scale_menu_disambiguates_exact_collisions() -> None:
    a = _saved()
    b = _saved()
    b.preset_id = "scale-preset-other"
    labels = scoring._saved_scale_menu_labels((a, b))  # noqa: SLF001
    assert len(labels) == 2 and labels[0] != labels[1]
    assert "scale-preset-test" in labels[0]
    assert "scale-preset-other" in labels[1]
    b.name = "Other"
    names = scoring._saved_scale_menu_labels((a, b))  # noqa: SLF001
    assert all("Preset ID" not in item for item in names)


def test_saved_scale_preview_shows_exact_types_and_metadata() -> None:
    saved = _saved()
    saved.levels = (_level(1, "int"), _level(1.0, "float"),
                    _level("1", "string"), _level(True, "bool"))
    content = "\n".join(scoring._saved_scale_preview(saved))  # noqa: SLF001
    for expected in (
        saved.preset_id, saved.preset_revision_id, "ordinal", "Students and Groups",
        "Interpret most recent evidence", "[int]", "[float]", "[str]",
        "[bool]", "1.0", '"1"', "true",
    ):
        assert expected in content


def _harness(monkeypatch: pytest.MonkeyPatch, *, approve: bool = True,
             stale_activity: bool = False, stale_preset: bool = False,
             raise_write: bool = False, bad_readback: bool = False,
             raise_readback: bool = False, cancel_choose: bool = False,
             empty: bool = False) -> dict[str, object]:
    saved = _saved()
    summary = SimpleNamespace(
        preset_id=saved.preset_id, preset_revision_id=saved.preset_revision_id,
        revision=saved.revision,
    )
    snapshot = {"value": 7}
    events: dict[str, object] = {"writes": [], "displays": [], "reviews": []}
    current = SimpleNamespace(
        class_id="class-synthetic", activity_id="activity-synthetic",
        title="Synthetic Activity", snapshot_revision=7,
    )
    def latest(_: object) -> SimpleNamespace:
        return SimpleNamespace(
            **{**vars(current), "snapshot_revision": snapshot["value"]}
        )

    monkeypatch.setattr(scoring, "ScoringScalePresetRevision", SimpleNamespace)
    monkeypatch.setattr(scoring, "_latest", latest)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(
        scoring, "list_presets", lambda kind: () if empty else (summary,),
    )
    monkeypatch.setattr(
        scoring, "get_preset_revision", lambda *args: saved,
    )
    def get_head(kind: str, preset_id: str) -> SimpleNamespace:
        assert kind == "scoring_scale" and preset_id == saved.preset_id
        if stale_preset:
            return SimpleNamespace(**{**vars(saved), "revision": 3})
        return saved
    monkeypatch.setattr(scoring, "get_preset", get_head)

    def choose(title: str, values: object, labels: tuple[str, ...],
               **kwargs: object) -> SimpleNamespace:
        assert title == "Choose a Saved Scoring Scale"
        assert saved.preset_revision_id in vars(saved).values()
        if cancel_choose:
            raise CancelMenuAction
        return saved
    monkeypatch.setattr(scoring, "select_one", choose)
    def display(title: str, lines: object) -> None:
        events["displays"].append((title, tuple(lines)))  # type: ignore[attr-defined]
    monkeypatch.setattr(scoring, "show_result", display)

    def confirm(title: str, keyword: str, lines: object) -> bool:
        assert title == "Use Saved Scoring Scale" and keyword == "USE"
        entries = tuple(lines)  # type: ignore[arg-type]
        events["reviews"].append(entries)  # type: ignore[attr-defined]
        assert saved.preset_revision_id in "\n".join(entries)
        assert "No Criteria, Criterion Sets" in "\n".join(entries)
        if stale_activity:
            snapshot["value"] += 1
        return approve
    monkeypatch.setattr(scoring, "confirm_write", confirm)

    def create(request: object, **kwargs: object) -> SimpleNamespace:
        events["writes"].append(request)  # type: ignore[attr-defined]
        assert kwargs["standards_library"] is None
        assert request.expected_snapshot_revision == 7  # type: ignore[attr-defined]
        assert request.levels is saved.levels  # type: ignore[attr-defined]
        assert (
            request.aggregation_guidance  # type: ignore[attr-defined]
            == saved.aggregation_guidance
        )
        assert request.intended_use == saved.intended_use  # type: ignore[attr-defined]
        if raise_write:
            raise RuntimeError("Synthetic write uncertainty")
        snapshot["value"] = 8
        return SimpleNamespace(
            scoring_scale_id=request.scoring_scale_id,  # type: ignore[attr-defined]
            commit=SimpleNamespace(snapshot_revision=8),
        )
    monkeypatch.setattr(scoring, "create_scoring_scale", create)

    def show(class_id: str, activity_id: str, native_id: str,
             **kwargs: object) -> SimpleNamespace:
        assert len(events["writes"]) == 1  # type: ignore[arg-type]
        if raise_readback:
            raise RuntimeError("Read-back unavailable")
        request = events["writes"][0]  # type: ignore[index]
        same_levels = request.levels  # type: ignore[attr-defined]
        if bad_readback:
            same_levels = (_level(1.0, "Developing"), *same_levels[1:])
        return SimpleNamespace(
            summary=SimpleNamespace(
                scoring_scale_id=native_id,
                lineage_id=request.lineage_id,  # type: ignore[attr-defined]
                revision=1, scale_type=request.scale_type,  # type: ignore[attr-defined]
                name=request.name, status="active",  # type: ignore[attr-defined]
                intended_use=request.intended_use,  # type: ignore[attr-defined]
                snapshot_revision=8,
            ),
            levels=same_levels,
            aggregation_guidance=(
                request.aggregation_guidance  # type: ignore[attr-defined]
            ),
        )
    monkeypatch.setattr(scoring, "show_scoring_scale", show)
    errors: list[str] = []
    monkeypatch.setattr(
        scoring, "_handle_error", lambda activity, error: errors.append(str(error)),
    )
    events["errors"] = errors
    events["activity"] = current
    return events


@pytest.mark.parametrize(
    ("settings", "writes", "last_title"),
    (
        ({"approve": True}, 1, "Saved Scoring Scale Imported"),
        ({"approve": False}, 0, "Saved Scoring Scale — Read-only Preview"),
        ({"stale_activity": True}, 0, "Saved Scoring Scale — Read-only Preview"),
        ({"stale_preset": True}, 0, "Saved Scoring Scale — Read-only Preview"),
        ({"cancel_choose": True}, 0, None),
        ({"empty": True}, 0, "No Saved Scoring Scales"),
        ({"raise_write": True}, 1, "Saved Scoring Scale Import — Outcome Unconfirmed"),
        ({"raise_readback": True}, 1,
         "Saved Scoring Scale Imported — Verification Unavailable"),
        ({"bad_readback": True}, 1,
         "Saved Scoring Scale Imported — Verification Mismatch"),
    ),
)
def test_import_saved_scale_statuses(
    monkeypatch: pytest.MonkeyPatch, settings: dict[str, bool],
    writes: int, last_title: str | None,
) -> None:
    events = _harness(monkeypatch, **settings)
    scoring._import_saved_scale(  # noqa: SLF001
        events["activity"], SimpleNamespace(require_actor=lambda: "teacher")
    )
    actual_writes = events["writes"]
    assert isinstance(actual_writes, list) and len(actual_writes) == writes
    displays = events["displays"]
    assert isinstance(displays, list)
    if last_title is None:
        assert not displays
    else:
        assert displays[-1][0] == last_title
    if settings.get("stale_activity") or settings.get("stale_preset"):
        assert events["errors"]
    else:
        assert not events["errors"]
    if settings.get("approve", True) and not (
        settings.get("empty") or settings.get("cancel_choose")
        or settings.get("stale_activity") or settings.get("stale_preset")
    ):
        assert any(d[0] == "Saved Scoring Scale — Read-only Preview"
                   for d in displays)


def test_scale_menu_exposes_independent_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sequence = iter(("5", "B"))
    monkeypatch.setattr("builtins.input", lambda prompt="": next(sequence))
    monkeypatch.setattr(scoring, "clear_screen", lambda: None)
    choices: list[str] = []
    monkeypatch.setattr(
        scoring, "_import_saved_scale",
        lambda activity, state: choices.append("import"),
    )
    scoring._scale_menu(  # noqa: SLF001
        SimpleNamespace(), SimpleNamespace()
    )
    assert choices == ["import"]
