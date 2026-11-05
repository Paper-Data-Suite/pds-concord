"""#145 Slice 1: guided Scale creation generates native IDs without prompts."""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from concord import menu_scoring as scoring


@pytest.mark.parametrize("approve", (False, True))
def test_guided_create_scale_generates_ids_without_identity_prompts(
    monkeypatch: pytest.MonkeyPatch, approve: bool
) -> None:
    current = SimpleNamespace(
        class_id="synthetic-class", activity_id="synthetic-activity",
        snapshot_revision=4, title="Synthetic Assessment",
    )
    monkeypatch.setattr(scoring, "_latest", lambda activity: current)
    monkeypatch.setattr(scoring, "_library", lambda: None)
    monkeypatch.setattr(scoring, "provenance", lambda actor: "synthetic-provenance")

    asked: list[str] = []

    def name_prompt(title: str, label: str, **kwargs: object) -> str:
        asked.append(label)
        assert label == "Scale name", f"Unexpected teacher-facing prompt: {label}"
        return "Four-Level Standards Rubric Scale"

    monkeypatch.setattr(scoring, "prompt_text", name_prompt)
    monkeypatch.setattr(scoring, "_optional_text", lambda *args: None)
    monkeypatch.setattr(
        scoring, "prompt_scale_combining_notes", lambda *args: None
    )
    draft = SimpleNamespace(scale_type="ordinal", levels=())
    guided = SimpleNamespace(draft=draft, precision_notices=())
    monkeypatch.setattr(scoring, "guide_scale_levels", lambda **kwargs: guided)
    monkeypatch.setattr(scoring, "validate_draft", lambda *args, **kwargs: None)
    monkeypatch.setattr(scoring, "describe_draft", lambda draft: ())

    review_lines: list[str] = []

    def confirmation(title: str, keyword: str, lines: tuple[str, ...]) -> bool:
        assert keyword == "CREATE"
        review_lines.extend(lines)
        return approve

    monkeypatch.setattr(scoring, "confirm_write", confirmation)
    created: list[object] = []

    def save(request: object, **kwargs: object) -> object:
        created.append(request)
        return SimpleNamespace(
            scoring_scale_id=request.scoring_scale_id,  # type: ignore[attr-defined]
            commit=SimpleNamespace(snapshot_revision=5),
        )

    monkeypatch.setattr(scoring, "create_scoring_scale", save)
    receipts: list[str] = []
    monkeypatch.setattr(
        scoring, "show_result", lambda title, lines: receipts.append(title)
    )
    monkeypatch.setattr(
        scoring, "_handle_error",
        lambda activity, error: pytest.fail(f"Unexpected creation error: {error}"),
    )

    result = scoring._create_scale(  # noqa: SLF001 - targeted menu acceptance
        SimpleNamespace(), SimpleNamespace(require_actor=lambda: "teacher")
    )
    assert asked == ["Scale name"]
    assert any("generated automatically" in line for line in review_lines)
    assert not any("New native ID:" in line for line in review_lines)
    if not approve:
        assert created == []
        assert result is None
        return

    assert len(created) == 1
    request = created[0]
    scale_id = getattr(request, "scoring_scale_id")
    assert re.fullmatch(r"scale-[0-9a-f]{32}", scale_id)
    lineage_id = getattr(request, "lineage_id")
    assert re.fullmatch(r"scale-lineage-[0-9a-f]{32}", lineage_id)
    assert result == scale_id
    assert receipts == ["Scoring Scale Created"]
