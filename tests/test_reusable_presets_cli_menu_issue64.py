from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.cli import main
from concord.reusable_preset_storage import load_current_preset
from concord.reusable_presets import CriterionSetPresetRevision
from concord.storage import load_current_record_graph
from concord.workflows.reusable_presets import PresetSummary


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=datetime(2026, 8, 27, tzinfo=timezone.utc),
        ),
    )
    return root


def _create_activity(root: Path) -> None:
    assert (
        main(
            [
                "activity",
                "create",
                "--workspace-root",
                str(root),
                "--class-id",
                "class-1",
                "--activity-id",
                "activity-1",
                "--title",
                "Preset CLI Activity",
                "--activity-type",
                "project",
                "--scoring-orientation",
                "local_criteria_only",
                "--session-id",
                "session-1",
                "--actor-id",
                "teacher-1",
            ]
        )
        == 0
    )


def test_preset_direct_commands_have_help() -> None:
    for command in (
        "role-preset",
        "responsibility-preset",
        "criterion-preset",
        "scale-preset",
    ):
        with pytest.raises(SystemExit) as exit_info:
            main([command, "--help"])
        assert exit_info.value.code == 0


def test_direct_scoring_preset_preview_and_apply_are_noninteractive(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _workspace(tmp_path)
    _create_activity(root)
    capsys.readouterr()
    scale_definition = tmp_path / "scale.json"
    scale_definition.write_text(
        json.dumps(
            {
                "name": "Two-Level Proficiency",
                "scale_type": "ordinal",
                "levels": [
                    {
                        "value": "developing",
                        "label": "Developing",
                        "meaning": "Developing evidence",
                        "position": 1,
                    },
                    {
                        "value": "proficient",
                        "label": "Proficient",
                        "meaning": "Proficient evidence",
                        "position": 2,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    criterion_definition = tmp_path / "criteria.json"
    criterion_definition.write_text(
        json.dumps(
            {
                "name": "Discussion Rubric",
                "purpose": "Assess discussion evidence",
                "criterion_set_kind": "local",
                "criteria": [
                    {
                        "key": "evidence",
                        "label": "Evidence",
                        "definition": "Uses relevant evidence.",
                        "criterion_kind": "local",
                        "supported_target_kinds": ["concord_activity"],
                        "default_scoring_scale_preset_id": "two-level",
                        "default_scoring_scale_preset_revision_id": "two-level-v1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    actor = ["--actor-id", "teacher-1"]
    assert (
        main(
            [
                "scale-preset",
                "create",
                "--workspace-root",
                str(root),
                "--preset-id",
                "two-level",
                "--preset-revision-id",
                "two-level-v1",
                "--definition",
                str(scale_definition),
                *actor,
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "criterion-preset",
                "create",
                "--workspace-root",
                str(root),
                "--preset-id",
                "discussion-rubric",
                "--preset-revision-id",
                "discussion-rubric-v1",
                "--definition",
                str(criterion_definition),
                *actor,
            ]
        )
        == 0
    )
    capsys.readouterr()
    monkeypatch.setattr(
        "builtins.input",
        lambda *_args, **_kwargs: pytest.fail("direct preset command must not prompt"),
    )
    common = [
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--expected-snapshot",
        "1",
        "--preset-id",
        "discussion-rubric",
        "--preset-revision-id",
        "discussion-rubric-v1",
        "--criterion-set-id",
        "activity-rubric",
        "--criterion-set-lineage-id",
        "activity-rubric-lineage",
        "--criterion-target",
        "evidence=activity-evidence",
        "--scoring-scale-preset-id",
        "two-level",
        "--scoring-scale-preset-revision-id",
        "two-level-v1",
        "--scoring-scale-id",
        "activity-scale",
        "--scoring-scale-lineage-id",
        "activity-scale-lineage",
        *actor,
    ]
    assert main(["criterion-preset", "apply-preview", *common]) == 0
    preview = capsys.readouterr()
    assert preview.err == ""
    assert "Writes: none" in preview.out
    match = re.search(r"Review digest: ([0-9a-f]{64})", preview.out)
    assert match is not None
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    ).graph
    assert graph.criterion_sets == ()
    assert graph.scoring_scales == ()

    assert (
        main(
            [
                "criterion-preset",
                "apply",
                *common,
                "--review-digest",
                match.group(1),
            ]
        )
        == 0
    )
    committed = capsys.readouterr()
    assert committed.err == ""
    assert "Criterion Set: activity-rubric" in committed.out
    graph = load_current_record_graph(
        root,
        ModuleWorkRef("concord", "class-1", "activity-1"),
    ).graph
    assert [item.criterion_set_id for item in graph.criterion_sets] == [
        "activity-rubric"
    ]
    assert [item.scoring_scale_id for item in graph.scoring_scales] == [
        "activity-scale"
    ]
    assert graph.score_records == ()

    scale_save = [
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--expected-snapshot",
        "2",
        "--source-scoring-scale-id",
        "activity-scale",
        "--preset-id",
        "saved-activity-scale",
        "--preset-revision-id",
        "saved-activity-scale-v1",
        *actor,
    ]
    assert main(["scale-preset", "save-preview", *scale_save]) == 0
    scale_preview = capsys.readouterr()
    scale_match = re.search(
        r"Review digest: ([0-9a-f]{64})",
        scale_preview.out,
    )
    assert scale_match is not None
    assert "Activity-native Scoring Scale identity" in scale_preview.out
    assert (
        main(
            [
                "scale-preset",
                "save",
                *scale_save,
                "--review-digest",
                scale_match.group(1),
            ]
        )
        == 0
    )
    capsys.readouterr()

    criterion_save = [
        "--workspace-root",
        str(root),
        "--class-id",
        "class-1",
        "--activity-id",
        "activity-1",
        "--expected-snapshot",
        "2",
        "--source-criterion-set-id",
        "activity-rubric",
        "--preset-id",
        "saved-activity-rubric",
        "--preset-revision-id",
        "saved-activity-rubric-v1",
        "--recommended-scoring-scale-preset-id",
        "saved-activity-scale",
        "--recommended-scoring-scale-preset-revision-id",
        "saved-activity-scale-v1",
        *actor,
    ]
    assert main(["criterion-preset", "save-preview", *criterion_save]) == 0
    criterion_preview = capsys.readouterr()
    criterion_match = re.search(
        r"Review digest: ([0-9a-f]{64})",
        criterion_preview.out,
    )
    assert criterion_match is not None
    assert "Activity-native Criterion identities" in criterion_preview.out
    assert (
        main(
            [
                "criterion-preset",
                "save",
                *criterion_save,
                "--review-digest",
                criterion_match.group(1),
            ]
        )
        == 0
    )
    capsys.readouterr()
    saved = load_current_preset(
        root,
        "criterion_set",
        "saved-activity-rubric",
    ).current
    assert isinstance(saved, CriterionSetPresetRevision)
    criterion = saved.criteria[0]
    assert criterion.default_scoring_scale_preset_id == "saved-activity-scale"
    assert criterion.default_scoring_scale_preset_revision_id == (
        "saved-activity-scale-v1"
    )


def test_role_and_responsibility_menu_source_choices_hide_revision_mechanics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from concord import menu_responsibility, menu_role

    role = PresetSummary(
        preset_kind="role",
        preset_id="facilitator",
        preset_revision_id="facilitator-v2",
        revision=2,
        name="Discussion Leader",
        status="active",
    )
    responsibility = PresetSummary(
        preset_kind="responsibility",
        preset_id="evidence",
        preset_revision_id="evidence-v3",
        revision=3,
        name="Capture Evidence",
        status="active",
    )
    monkeypatch.setattr(menu_role, "list_presets", lambda _kind: (role,))
    monkeypatch.setattr(
        menu_role,
        "select_one",
        lambda *_args, **_kwargs: role,
    )
    monkeypatch.setattr(menu_role, "clear_screen", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "1")
    assert menu_role._choose_role_preset() == role

    monkeypatch.setattr(
        menu_responsibility,
        "list_presets",
        lambda _kind: (responsibility,),
    )
    monkeypatch.setattr(
        menu_responsibility,
        "select_one",
        lambda *_args, **_kwargs: responsibility,
    )
    monkeypatch.setattr(menu_responsibility, "clear_screen", lambda: None)
    assert menu_responsibility._choose_responsibility_preset() == responsibility
