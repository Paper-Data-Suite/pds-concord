"""#144 Slice 5: exact Scale scalars and historical JSON/CLI regression.

All writes use synthetic pytest-owned temporary workspaces, never real school data.
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.workspace import ensure_workspace_root

from concord.cli import main
from concord.model_conversion import record_from_dict, record_to_dict
from concord.models import ConcordModelError, ScoringScale, ScoringScaleLevel
from concord.reusable_preset_storage import (
    _preset_from_dict,
    _preset_to_dict,
    load_current_preset,
    preset_revision_path,
)
from concord.reusable_presets import ScoringScalePresetRevision
from concord.scale_guidance import (
    GuidedScaleInputError,
    format_typed_value,
    four_level_proficiency,
    parse_typed_value,
    yes_no_scale,
)
from concord.workflows.context import provenance
from concord.workflows.errors import ConcordWorkflowConflictError
from concord.workflows.models import WorkflowActor
from concord.workflows.reusable_presets import (
    CreateScoringScalePresetRequest,
    ReviseScoringScalePresetRequest,
    create_scoring_scale_preset,
    get_preset_revision,
    revise_scoring_scale_preset,
)


def _clock() -> datetime:
    return datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="synthetic-teacher")


def _mixed_levels() -> tuple[ScoringScaleLevel, ...]:
    return tuple(
        ScoringScaleLevel(
            value=value,
            label=label,
            meaning=f"Synthetic {label} meaning",
            description=f"Description for {label}",
        )
        for value, label in (
            (1, "Integer"),
            (1.0, "Float"),
            ("1", "Text"),
            (True, "Boolean"),
            ("jíbára", "Unicode"),
        )
    )


def _model(
    levels: tuple[ScoringScaleLevel, ...],
    *,
    scale_type: str = "teacher_defined",
) -> ScoringScale:
    return ScoringScale(
        scoring_scale_id="scale-synthetic",
        lineage_id="scale-synthetic-lineage",
        name="Synthetic typed Scale",
        revision=1,
        scale_type=scale_type,
        levels=levels,
        status="active",
        created_provenance=provenance(_actor(), clock=_clock),
        intended_use="Synthetic classroom guidance",
        aggregation_guidance="No automated grade conversion",
    )


@pytest.mark.parametrize(
    ("kind", "raw"),
    [
        ("integer", "1.0"),
        ("integer", "01"),
        ("integer", "1,000"),
        ("decimal", "0.1"),
        ("decimal", "nan"),
        ("decimal", "Infinity"),
        ("decimal", "1e9999"),
        ("decimal", "1e-9999"),
        ("decimal", "1,5"),
        ("yes_no", "1"),
        ("yes_no", "falsehood"),
        ("category", " leading"),
        ("text", " "),
    ],
)
def test_invalid_or_lossy_input_refuses_without_a_durable_write(
    tmp_path: Path, kind: str, raw: str
) -> None:
    root = tmp_path / "missing-workspace"
    with pytest.raises(GuidedScaleInputError):
        parse_typed_value(raw, kind)  # type: ignore[arg-type]
    assert not root.exists()


def test_reviewed_decimal_rounding_is_explicit_and_nonfinite_is_rejected() -> None:
    approved = parse_typed_value(
        "0.1", "decimal", accept_float_approximation=True
    )
    assert type(approved.value) is float
    assert approved.precision_notice is not None
    assert "0.1" in approved.precision_notice
    assert parse_typed_value("-0.125", "decimal").value == -0.125


@pytest.mark.parametrize("bad", [None, [], {}, float("nan"), float("inf")])
def test_model_rejects_non_json_or_nonfinite_level_values(bad: object) -> None:
    with pytest.raises(ConcordModelError):
        ScoringScaleLevel(
            value=bad, label="Invalid", meaning="Invalid"
        )  # type: ignore[arg-type]


def test_type_sensitive_scale_values_survive_native_json_roundtrip() -> None:
    model = _model(_mixed_levels())
    payload = record_to_dict(model)
    restored = record_from_dict(
        "scoring_scale", json.loads(json.dumps(payload, ensure_ascii=False))
    )
    assert isinstance(restored, ScoringScale)
    assert restored == model
    assert [(type(item.value), item.value) for item in restored.levels] == [
        (type(item.value), item.value) for item in model.levels
    ]
    for value, label in ((1, "Integer"), (1.0, "Float"),
                         ("1", "Text"), (True, "Boolean")):
        matched = restored.level_for_value(value)
        assert matched is not None and matched.label == label
    assert restored.level_for_value(False) is None
    assert restored.level_for_value("true") is None
    assert restored.levels[-1].description == "Description for Unicode"
    assert "[boolean]" in format_typed_value(True)


def test_duplicate_values_and_incompatible_type_refuse() -> None:
    original = _mixed_levels()[0]
    with pytest.raises(ConcordModelError, match="unique"):
        _model((original, replace(original, label="Duplicate")))
    with pytest.raises(ConcordModelError, match="numeric"):
        _model(_mixed_levels(), scale_type="numeric")
    with pytest.raises(ConcordModelError, match="binary"):
        _model(four_level_proficiency().levels, scale_type="binary")
    assert tuple(type(item.value) for item in yes_no_scale().levels) == (
        bool, bool
    )


def test_native_json_codec_rejects_value_type_and_schema_tampering() -> None:
    model = _model(_mixed_levels())
    payload = record_to_dict(model)
    malformed = json.loads(json.dumps(payload))
    malformed["levels"][0]["value"] = {"bad": "object"}
    with pytest.raises(ConcordModelError):
        record_from_dict("scoring_scale", malformed)
    extra = json.loads(json.dumps(payload))
    extra["unknown_override"] = 1
    with pytest.raises(ConcordModelError, match="unknown"):
        record_from_dict("scoring_scale", extra)


def test_preset_codec_and_immutable_revisions_preserve_typed_values(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    levels = _mixed_levels()
    result1 = create_scoring_scale_preset(
        CreateScoringScalePresetRequest(
            preset_id="typed-scale",
            preset_revision_id="typed-scale-v1",
            name="Typed synthetic Scale",
            scale_type="teacher_defined",
            levels=levels,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert result1.revision == 1
    before = load_current_preset(root, "scoring_scale", "typed-scale").current
    assert isinstance(before, ScoringScalePresetRevision)
    serial = _preset_to_dict(before)
    restored = _preset_from_dict(json.loads(json.dumps(serial, ensure_ascii=False)))
    assert restored == before
    assert tuple(type(item.value) for item in restored.levels) == tuple(
        type(item.value) for item in levels
    )
    result2 = revise_scoring_scale_preset(
        ReviseScoringScalePresetRequest(
            preset_id="typed-scale",
            preset_revision_id="typed-scale-v2",
            expected_revision=1,
            name="Typed synthetic Scale revised",
            scale_type="teacher_defined",
            levels=levels[:-1] + (
                replace(levels[-1], meaning="New future meaning"),
            ),
            actor=_actor(),
        ),
        workspace_root=root,
        clock=_clock,
    )
    assert result2.revision == 2
    old = get_preset_revision(
        "scoring_scale", "typed-scale", "typed-scale-v1", workspace_root=root
    )
    current = load_current_preset(root, "scoring_scale", "typed-scale").current
    assert old == before
    assert old.levels[-1].meaning == "Synthetic Unicode meaning"
    assert current.levels[-1].meaning == "New future meaning"
    assert preset_revision_path(root, "scoring_scale", "typed-scale", 1).is_file()
    assert preset_revision_path(root, "scoring_scale", "typed-scale", 2).is_file()
    with pytest.raises(ConcordWorkflowConflictError):
        revise_scoring_scale_preset(
            ReviseScoringScalePresetRequest(
                preset_id="typed-scale",
                preset_revision_id="typed-scale-v3",
                expected_revision=1,
                name="Stale type test",
                scale_type="teacher_defined",
                levels=levels,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    assert load_current_preset(root, "scoring_scale", "typed-scale").current == current


def test_advanced_cli_preserves_typed_json_and_never_opens_a_menu(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    definition = tmp_path / "scale-definition.json"
    definition.write_text(
        json.dumps(
            {
                "name": "Synthetic direct typed scale",
                "scale_type": "teacher_defined",
                "levels": [
                    {"value": level.value, "label": level.label,
                     "meaning": level.meaning, "description": level.description}
                    for level in _mixed_levels()
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "builtins.input", lambda *_args, **_kw: pytest.fail("CLI prompted")
    )
    args = [
        "--workspace-root", str(root),
        "--preset-id", "cli-typed-scale",
        "--preset-revision-id", "cli-typed-scale-v1",
        "--definition", str(definition),
        "--actor-id", "synthetic-teacher",
    ]
    assert main(["scale-preset", "create", *args]) == 0
    capsys.readouterr()
    saved = load_current_preset(root, "scoring_scale", "cli-typed-scale").current
    assert tuple(type(item.value) for item in saved.levels) == tuple(
        type(level.value) for level in _mixed_levels()
    )
    assert [item.value for item in saved.levels] == [
        item.value for item in _mixed_levels()
    ]
    assert main([
        "scale-preset", "show", "--workspace-root", str(root),
        "--preset-id", "cli-typed-scale"
    ]) == 0
    capsys.readouterr()
