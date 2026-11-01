"""#143 Slice 5: hostile preset inputs refuse with byte-exact zero writes.

Use only synthetic pytest tmp_path Core classes, Activities and preset stores.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.workspace import ensure_workspace_root
from test_issue143_slice2_native_preset_save import (
    ALIGNMENT,
    PROFILE,
    STANDARD,
    _actor,
    _clock,
    _work,
)
from test_issue143_slice4_revision_serialization_cli import (
    PRESET_ID,
    _revision_request,
    _setup,
)

from concord.models import ConcordModelError
from concord.reusable_preset_storage import (
    ReusablePresetStorageIntegrityError,
    ReusablePresetStorageReadError,
    _preset_from_dict,
    _preset_to_dict,
    load_current_preset,
    preset_revision_path,
)
from concord.reusable_presets import CriterionPresetSpec
from concord.workflows.activity import create_activity_context
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import CreateActivityContextRequest
from concord.workflows.reusable_presets import (
    CreateCriterionSetPresetRequest,
    CriterionTargetIdentity,
    MaterializeScoringSetupRequest,
    create_criterion_set_preset,
    get_preset,
    materialize_scoring_setup,
    prepare_scoring_setup,
    revise_criterion_set_preset,
    validate_preset,
)


def _fingerprint(root: Path) -> tuple[tuple[str, str], ...]:
    """Verify both file inventory and file bytes after an expected refusal."""
    return tuple(
        sorted(
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in root.rglob("*")
            if path.is_file()
        )
    )


@pytest.mark.parametrize(
    "failure",
    ("no_library", "unknown_primary", "unknown_alignment", "wrong_profile"),
)
def test_revise_requires_current_core_authority_and_never_writes(
    tmp_path: Path, failure: str
) -> None:
    root, library, original = _setup(tmp_path)
    request = _revision_request(original)
    current_library = library
    if failure == "no_library":
        current_library = None
    elif failure == "wrong_profile":
        request = replace(request, standards_profile_id="unknown.profile:2026")
    else:
        first = original.criteria[0]
        if failure == "unknown_primary":
            first = replace(first, standard_id="UNKNOWN.DOTTED.1")
        else:
            first = replace(
                first,
                alignment_standard_ids=("UNKNOWN.DOTTED.ALIGNMENT",),
            )
        request = replace(request, criteria=(first, *original.criteria[1:]))
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowValidationError):
        revise_criterion_set_preset(
            request, workspace_root=root, standards_library=current_library
        )
    assert _fingerprint(root) == before
    assert get_preset("criterion_set", PRESET_ID, workspace_root=root) == original


def test_create_with_dotted_standard_without_core_library_is_zero_write(
    tmp_path: Path,
) -> None:
    root, _library, original = _setup(tmp_path)
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowValidationError, match="standards library"):
        create_criterion_set_preset(
            CreateCriterionSetPresetRequest(
                preset_id="unauthorized-s143",
                preset_revision_id="unauthorized-s143-v1",
                name="Unverified Standards",
                purpose="Must refuse without Core authority",
                criterion_set_kind=original.criterion_set_kind,
                criteria=original.criteria,
                standards_profile_id=PROFILE,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    assert _fingerprint(root) == before


def test_recommended_scale_revision_cannot_be_guessed_or_replaced(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    bad = tuple(
        replace(
            criterion,
            default_scoring_scale_preset_revision_id="missing-s143-scale-v9",
        )
        for criterion in original.criteria
    )
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowError):
        revise_criterion_set_preset(
            replace(_revision_request(original), criteria=bad),
            workspace_root=root,
            standards_library=library,
        )
    assert _fingerprint(root) == before


def test_unpaired_scale_reference_and_duplicate_alignment_stay_invalid(
    tmp_path: Path,
) -> None:
    root, _library, original = _setup(tmp_path)
    before = _fingerprint(root)
    with pytest.raises(ConcordModelError):
        replace(
            original.criteria[0],
            default_scoring_scale_preset_revision_id=None,
        )
    with pytest.raises(ConcordModelError):
        replace(
            original.criteria[0],
            alignment_standard_ids=(ALIGNMENT, f" {ALIGNMENT} "),
        )
    assert _fingerprint(root) == before


def test_corrupt_preset_revision_fails_closed_without_repairing_bytes(
    tmp_path: Path,
) -> None:
    root, _library, original = _setup(tmp_path)
    source_path = preset_revision_path(
        root, "criterion_set", PRESET_ID, original.revision
    )
    source_path.write_bytes(source_path.read_bytes() + b"\ncorrupt-s143")
    before = _fingerprint(root)
    with pytest.raises(ReusablePresetStorageReadError):
        load_current_preset(root, "criterion_set", PRESET_ID)
    assert _fingerprint(root) == before


def test_invalid_codec_type_does_not_relax_standards_grammar(
    tmp_path: Path,
) -> None:
    root, _library, original = _setup(tmp_path)
    encoded = _preset_to_dict(original)
    encoded["criteria"][0]["standard_id"] = [STANDARD]
    before = _fingerprint(root)
    with pytest.raises(ReusablePresetStorageIntegrityError):
        _preset_from_dict(encoded)
    assert _fingerprint(root) == before


def test_neutral_local_group_preset_needs_no_standards_authority(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "local-only")
    result = create_criterion_set_preset(
        CreateCriterionSetPresetRequest(
            preset_id="neutral-group-s143",
            preset_revision_id="neutral-group-s143-v1",
            name="Local group collaboration",
            purpose="Synthetic group-only criteria",
            criterion_set_kind="local",
            criteria=(
                CriterionPresetSpec(
                    key="teamwork",
                    label="Group textual analysis",
                    definition="Synthetic group collaboration only.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_group",),
                ),
            ),
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=None,
    )
    assert result.revision == 1
    before = _fingerprint(root)
    assert validate_preset(
        "criterion_set", "neutral-group-s143", workspace_root=root
    ).revision == 1
    assert _fingerprint(root) == before


def _target(
    root: Path, library: object, *, focus: tuple[str, ...] = (STANDARD,)
) -> tuple[str, str, int]:
    class_id = "synthetic-target-s143"
    activity_id = "target-mixed-s143"
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 1, tzinfo=timezone.utc),
        ),
    )
    result = create_activity_context(
        CreateActivityContextRequest(
            class_id=class_id,
            activity_id=activity_id,
            title="Synthetic second-class assessment target",
            activity_type="project",
            scoring_orientation="mixed",
            session_id="target-session-s143",
            standards_profile_id=PROFILE,
            focus_standard_ids=focus,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    return class_id, activity_id, result.commit.snapshot_revision


def _materialization(
    original: object, class_id: str, activity_id: str, revision: int
) -> MaterializeScoringSetupRequest:
    first = original.criteria[0]
    return MaterializeScoringSetupRequest(
        criterion_preset_id=original.preset_id,
        criterion_preset_revision_id=original.preset_revision_id,
        class_id=class_id,
        activity_id=activity_id,
        criterion_set_id="new-target-set-s143",
        criterion_set_lineage_id="new-target-set-lineage-s143",
        criterion_ids=tuple(
            CriterionTargetIdentity(
                criterion_key=item.key, criterion_id=f"new-target-{index}-s143"
            )
            for index, item in enumerate(original.criteria, 1)
        ),
        expected_snapshot_revision=revision,
        actor=_actor(),
        scoring_scale_preset_id=first.default_scoring_scale_preset_id,
        scoring_scale_preset_revision_id=(
            first.default_scoring_scale_preset_revision_id
        ),
        scoring_scale_id="new-target-scale-s143",
        scoring_scale_lineage_id="new-target-scale-lineage-s143",
    )


def test_materialization_adversarial_requests_never_create_partial_graph(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    class_id, activity_id, revision = _target(root, library)
    request = _materialization(original, class_id, activity_id, revision)
    before = _fingerprint(root)
    failures = (
        replace(request, expected_snapshot_revision=revision + 1),
        replace(request, criterion_preset_revision_id="not-a-real-revision-s143"),
        replace(request, scoring_scale_preset_revision_id="missing-scale-v9"),
        replace(request, scoring_scale_lineage_id=None),
        replace(request, criterion_ids=(request.criterion_ids[0],) * 2),
        replace(request, class_id=_work().class_id),
    )
    for candidate in failures:
        with pytest.raises(ConcordWorkflowError):
            prepare_scoring_setup(
                candidate,
                workspace_root=root,
                standards_library=library,
                clock=_clock,
            )
        assert _fingerprint(root) == before
    assert get_preset("criterion_set", PRESET_ID, workspace_root=root) == original


def test_stale_review_digest_cannot_materialize_a_partial_batch(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    class_id, activity_id, revision = _target(root, library)
    request = _materialization(original, class_id, activity_id, revision)
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert prepared.review_digest != "0" * 64
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowConflictError, match="review is stale"):
        materialize_scoring_setup(
            request,
            review_digest="0" * 64,
            workspace_root=root,
            standards_library=library,
            clock=_clock,
        )
    assert _fingerprint(root) == before


def test_target_focus_cannot_be_substituted_for_exact_core_standard(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    class_id, activity_id, revision = _target(root, library, focus=(ALIGNMENT,))
    request = _materialization(original, class_id, activity_id, revision)
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowValidationError, match="Focus Standard"):
        prepare_scoring_setup(
            request, workspace_root=root, standards_library=library, clock=_clock
        )
    assert _fingerprint(root) == before


def test_double_commit_with_stale_expected_revision_is_zero_write(
    tmp_path: Path,
) -> None:
    root, library, original = _setup(tmp_path)
    class_id, activity_id, revision = _target(root, library)
    request = _materialization(original, class_id, activity_id, revision)
    prepared = prepare_scoring_setup(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    receipt = materialize_scoring_setup(
        request,
        review_digest=prepared.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert receipt.commit.snapshot_revision == revision + 1
    before = _fingerprint(root)
    with pytest.raises(ConcordWorkflowConflictError):
        materialize_scoring_setup(
            request,
            review_digest=prepared.review_digest,
            workspace_root=root,
            standards_library=library,
            clock=_clock,
        )
    assert _fingerprint(root) == before
