"""#143 Slice 4: exact mixed preset revision, serialization and CLI contracts.

All writes target pytest temporary synthetic workspaces; no classroom data.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from test_issue143_slice2_native_preset_save import (
    ALIGNMENT,
    PROFILE,
    STANDARD,
    _actor,
    _clock,
    _fixture,
    _work,
)
from test_issue143_slice3_cross_class_materialization import _save_source

from concord.cli import main
from concord.cli_app.handlers import reusable_presets as cli_presets
from concord.reusable_preset_storage import (
    _preset_from_dict,
    _preset_to_dict,
    load_current_preset,
)
from concord.reusable_presets import CriterionSetPresetRevision
from concord.storage import list_work_snapshots
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.reusable_presets import (
    ReviseCriterionSetPresetRequest,
    get_preset,
    get_preset_revision,
    revise_criterion_set_preset,
    validate_preset,
)

PRESET_ID = "saved-discussion-assessment"
REVISION1 = f"{PRESET_ID}-v1"
REVISION2 = f"{PRESET_ID}-v2"


def _setup(tmp_path: Path):
    root, library, source_revision = _fixture(tmp_path)
    _save_source(root, library, source_revision, recommend=True)
    original = get_preset("criterion_set", PRESET_ID, workspace_root=root)
    assert isinstance(original, CriterionSetPresetRevision)
    return root, library, original


def _revision_request(
    original: CriterionSetPresetRevision,
    *,
    revision_id: str = REVISION2,
    expected: int = 1,
) -> ReviseCriterionSetPresetRequest:
    return ReviseCriterionSetPresetRequest(
        preset_id=PRESET_ID,
        preset_revision_id=revision_id,
        expected_revision=expected,
        name="Revised synthetic discussion assessment",
        purpose="Synthetic individual and group evidence, revised guidance",
        criterion_set_kind="mixed",
        criteria=(
            replace(original.criteria[0], label="Revised discussion participation"),
            original.criteria[1],
        ),
        standards_profile_id=PROFILE,
        actor=_actor(),
    )


def test_exact_revision_and_persisted_serialization_preserve_dotted_ids(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    before = tuple(list_work_snapshots(root, _work()))
    receipt = revise_criterion_set_preset(
        _revision_request(original),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert receipt.revision == 2
    assert receipt.preset_revision_id == REVISION2
    current = load_current_preset(root, "criterion_set", PRESET_ID).current
    assert current == get_preset("criterion_set", PRESET_ID, workspace_root=root)
    assert current.revision == 2
    assert current.supersedes_preset_revision_id == REVISION1
    assert current.standards_profile_id == PROFILE
    assert current.criterion_set_kind == "mixed"
    student = next(c for c in current.criteria if c.key == "discussion_participation")
    group = next(
        c for c in current.criteria if c.key == "collaborative_textual_analysis"
    )
    assert student.standard_id == STANDARD
    assert student.alignment_standard_ids == (ALIGNMENT,)
    assert student.supported_target_kinds == ("core_student",)
    assert student.default_scoring_scale_preset_id == "saved-four-level"
    assert group.standard_id is None
    assert group.supported_target_kinds == ("concord_group",)
    assert group.default_scoring_scale_preset_id == "saved-four-level"
    old = get_preset_revision(
        "criterion_set", PRESET_ID, REVISION1, workspace_root=root
    )
    assert old == original
    assert old.criteria[0].label != student.label
    assert old.supersedes_preset_revision_id is None
    summary = validate_preset(
        "criterion_set", PRESET_ID, workspace_root=root, standards_library=library
    )
    assert summary.revision == 2
    assert tuple(list_work_snapshots(root, _work())) == before


def test_revised_preset_rejects_stale_version_without_storage_writes(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    revise_criterion_set_preset(
        _revision_request(original),
        workspace_root=root,
        standards_library=library,
    )
    before = get_preset("criterion_set", PRESET_ID, workspace_root=root)
    with pytest.raises(ConcordWorkflowConflictError):
        revise_criterion_set_preset(
            _revision_request(original, revision_id="stale-v3", expected=1),
            workspace_root=root,
            standards_library=library,
        )
    assert get_preset("criterion_set", PRESET_ID, workspace_root=root) == before
    assert get_preset_revision(
        "criterion_set", PRESET_ID, REVISION1, workspace_root=root
    ) == original


def test_revise_rejects_unknown_dotted_standard_without_new_revision(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    invalid_criteria = (
        replace(original.criteria[0], standard_id="UNKNOWN.DOTTED.1"),
        original.criteria[1],
    )
    request = replace(_revision_request(original), criteria=invalid_criteria)
    before = get_preset("criterion_set", PRESET_ID, workspace_root=root)
    with pytest.raises(ConcordWorkflowValidationError):
        revise_criterion_set_preset(
            request, workspace_root=root, standards_library=library
        )
    assert get_preset("criterion_set", PRESET_ID, workspace_root=root) == before


def test_exact_json_codec_retains_punctuation_and_profile_without_loss(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    revise_criterion_set_preset(
        _revision_request(original),
        workspace_root=root,
        standards_library=library,
    )
    for revision_id in (REVISION1, REVISION2):
        revision = get_preset_revision(
            "criterion_set", PRESET_ID, revision_id, workspace_root=root
        )
        exported = _preset_to_dict(revision)
        restored = _preset_from_dict(json.loads(json.dumps(exported)))
        assert restored == revision
        assert exported["standards_profile_id"] == PROFILE
        first = next(
            c for c in exported["criteria"]
            if c["key"] == "discussion_participation"
        )
        assert first["standard_id"] == STANDARD
        assert first["alignment_standard_ids"] == [ALIGNMENT]
        assert restored.criteria[0].default_scoring_scale_preset_id == (
            "saved-four-level"
        )


def test_cli_create_revise_list_show_and_validate_dotted_standards(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, library, existing = _setup(tmp_path)
    monkeypatch.setattr(
        cli_presets, "load_command_standards_library", lambda _args: library
    )
    monkeypatch.setattr(
        "builtins.input", lambda *_args, **_kwargs: pytest.fail("CLI prompted")
    )
    definition = {
        "name": "CLI Synthetic Mixed Assessment",
        "purpose": "Synthetic direct command contract",
        "criterion_set_kind": "mixed",
        "standards_profile_id": PROFILE,
        "criteria": [asdict(c) for c in existing.criteria],
    }
    path = tmp_path / "cli-preset-definition.json"
    path.write_text(json.dumps(definition), encoding="utf-8")
    base = ["--workspace-root", str(root)]
    name = "cli-s143-dotted-standards"
    assert main([
        "criterion-preset", "create", *base,
        "--preset-id", name,
        "--preset-revision-id", f"{name}-v1",
        "--definition", str(path), "--actor-id", "synthetic-teacher",
    ]) == 0
    capsys.readouterr()
    created = get_preset("criterion_set", name, workspace_root=root)
    assert created.standards_profile_id == PROFILE
    assert created.criteria[0].standard_id == STANDARD
    assert created.criteria[0].alignment_standard_ids == (ALIGNMENT,)
    definition["purpose"] = "Revised synthetic CLI definition"
    revised_path = tmp_path / "cli-revised.json"
    revised_path.write_text(json.dumps(definition), encoding="utf-8")
    assert main([
        "criterion-preset", "revise", *base,
        "--preset-id", name,
        "--preset-revision-id", f"{name}-v2",
        "--expected-preset-revision", "1",
        "--definition", str(revised_path),
        "--actor-id", "synthetic-teacher",
    ]) == 0
    capsys.readouterr()
    assert main(["criterion-preset", "list", *base]) == 0
    listed = capsys.readouterr().out
    assert f"{name}-v2" in listed
    assert main([
        "criterion-preset", "show", *base, "--preset-id", name
    ]) == 0
    details = capsys.readouterr().out
    assert "Revision: 2" in details
    assert f"Standards profile: {PROFILE}" in details
    assert main([
        "criterion-preset", "validate", *base, "--preset-id", name
    ]) == 0
    assert "Validation: valid" in capsys.readouterr().out
    current = get_preset("criterion_set", name, workspace_root=root)
    assert current.purpose == definition["purpose"]
    assert get_preset_revision(
        "criterion_set", name, f"{name}-v1", workspace_root=root
    ).purpose != current.purpose
