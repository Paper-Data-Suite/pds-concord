"""#143 Slice 2: synthetic native mixed assessment -> saved reusable setup.

All mutating services receive a pytest temporary PDS workspace explicitly. These
are service/menu witnesses, NOT real student data, returned paper or Scores.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

from concord import menu_scoring
from concord.menu_context import MenuSessionContext
from concord.models import ScoringScaleLevel
from concord.reusable_preset_storage import load_current_preset
from concord.reusable_presets import (
    CriterionSetPresetRevision,
    ScoringScalePresetRevision,
)
from concord.storage import list_work_snapshots, load_current_record_graph
from concord.storage_errors import ConcordStorageGraphIntegrityError
from concord.workflows.activity import create_activity_context, show_activity
from concord.workflows.criterion_sets import (
    CreateCriterionSetRequest,
    CriterionSpec,
    create_criterion_set,
    list_criterion_sets,
    read_activity_criterion_set_selection,
    show_criterion_set,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import CreateActivityContextRequest, WorkflowActor
from concord.workflows.reusable_presets import (
    SaveCriterionSetPresetFromActivityRequest,
    SaveScoringScalePresetFromActivityRequest,
    get_preset,
    get_preset_revision,
    list_presets,
    prepare_criterion_set_preset_from_activity,
    prepare_scoring_scale_preset_from_activity,
    save_criterion_set_preset_from_activity,
    save_scoring_scale_preset_from_activity,
    validate_preset,
)
from concord.workflows.scoring_scales import (
    CreateScoringScaleRequest,
    create_scoring_scale,
    show_scoring_scale,
)

STANDARD = "SL.PE.11-12.1"
ALIGNMENT = "W.NW.11-12.3.D"
PROFILE = "njsls-ela:profile.2023:11-12"
CLASS = "synthetic-class-p2"
ACTIVITY = "synthetic-discussion-p2"
SCALE = "native-scale-s143"
SET = "native-set-s143"


def _clock() -> datetime:
    return datetime(2026, 10, 31, 17, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(actor_id="teacher-synthetic-143")


def _library(*, alignment_active: bool = True) -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD,
                code=STANDARD,
                source="synthetic-143",
                short_name="Synthetic discussion participation",
                description="Synthetic discussion evidence.",
                active=True,
                available_modules=("concord",),
            ),
            StandardDefinition(
                standard_id=ALIGNMENT,
                code=ALIGNMENT,
                source="synthetic-143",
                short_name="Synthetic writing alignment",
                description="Synthetic writing alignment.",
                active=alignment_active,
                available_modules=("concord",),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE,
                standards=(STANDARD, ALIGNMENT),
                title="Synthetic English 12 profile",
            ),
        ),
    )


def _fixture(tmp_path: Path) -> tuple[Path, StandardsLibrary, int]:
    root = ensure_workspace_root(tmp_path / "synthetic-workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata(CLASS, "2026-2027", created_at=_clock()),
    )
    library = _library()
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            title="Synthetic Jibara discussion",
            activity_type="project",
            scoring_orientation="mixed",
            session_id="synthetic-session-p2",
            actor=_actor(),
            standards_profile_id=PROFILE,
            focus_standard_ids=(STANDARD, ALIGNMENT),
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    levels = tuple(
        ScoringScaleLevel(
            value=value,
            label=label,
            meaning=f"Synthetic {label}",
            position=value,
        )
        for value, label in (
            (1, "Developing"),
            (2, "Approaching"),
            (3, "Meeting"),
            (4, "Exceeding"),
        )
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            scoring_scale_id=SCALE,
            lineage_id="native-scale-lineage-s143",
            name="Four-Level Standards Proficiency",
            revision=1,
            scale_type="ordinal",
            levels=levels,
            status="active",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    criterion_set = create_criterion_set(
        CreateCriterionSetRequest(
            class_id=CLASS,
            activity_id=ACTIVITY,
            criterion_set_id=SET,
            lineage_id="native-set-lineage-s143",
            name="Synthetic discussion assessment",
            purpose="Individual and Cluster analysis, without Scores",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=(
                CriterionSpec(
                    criterion_id="native-student-criterion-s143",
                    key="discussion_participation",
                    label="Individual discussion participation",
                    definition="Evidence of individual discussion.",
                    criterion_kind="standard_backed",
                    supported_target_kinds=("core_student",),
                    standard_id=STANDARD,
                    alignment_standard_ids=(ALIGNMENT,),
                    default_scoring_scale_id=SCALE,
                ),
                CriterionSpec(
                    criterion_id="native-cluster-criterion-s143",
                    key="collaborative_textual_analysis",
                    label="Cluster collaborative textual analysis",
                    definition="Shared interpretation and analysis.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_group",),
                    default_scoring_scale_id=SCALE,
                ),
            ),
            status="active",
            standards_profile_id=PROFILE,
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    return root, library, criterion_set.commit.snapshot_revision


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(module_id="concord", class_id=CLASS, work_id=ACTIVITY)


def _assert_source_untouched(
    root: Path,
    library: StandardsLibrary,
    snapshots_before: tuple[object, ...],
    graph_before: object,
) -> None:
    assert tuple(list_work_snapshots(root, _work())) == snapshots_before
    assert (
        load_current_record_graph(root, _work(), standards_library=library).graph
        == graph_before
    )


def _save_scale(root: Path, library: StandardsLibrary, revision: int) -> None:
    request = SaveScoringScalePresetFromActivityRequest(
        class_id=CLASS,
        activity_id=ACTIVITY,
        scoring_scale_id=SCALE,
        preset_id="saved-four-level",
        preset_revision_id="saved-four-level-v1",
        expected_snapshot_revision=revision,
        actor=_actor(),
    )
    preview = prepare_scoring_scale_preset_from_activity(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    save_scoring_scale_preset_from_activity(
        request,
        review_digest=preview.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    scale = get_preset("scoring_scale", "saved-four-level", workspace_root=root)
    assert isinstance(scale, ScoringScalePresetRevision)
    assert tuple((x.value, x.label) for x in scale.levels) == (
        (1, "Developing"),
        (2, "Approaching"),
        (3, "Meeting"),
        (4, "Exceeding"),
    )


def _request(
    revision: int,
    *,
    recommend_scale: bool = True,
    preset_id: str = "saved-discussion-assessment",
) -> SaveCriterionSetPresetFromActivityRequest:
    return SaveCriterionSetPresetFromActivityRequest(
        class_id=CLASS,
        activity_id=ACTIVITY,
        criterion_set_id=SET,
        preset_id=preset_id,
        preset_revision_id=f"{preset_id}-v1",
        expected_snapshot_revision=revision,
        actor=_actor(),
        recommended_scoring_scale_preset_id=(
            "saved-four-level" if recommend_scale else None
        ),
        recommended_scoring_scale_preset_revision_id=(
            "saved-four-level-v1" if recommend_scale else None
        ),
    )


def _assert_preset(preset: CriterionSetPresetRevision, recommend: bool) -> None:
    assert preset.criterion_set_kind == "mixed"
    assert preset.standards_profile_id == PROFILE
    assert len(preset.criteria) == 2
    individual, cluster = preset.criteria
    assert individual.key == "discussion_participation"
    assert individual.criterion_kind == "standard_backed"
    assert individual.standard_id == STANDARD
    assert individual.alignment_standard_ids == (ALIGNMENT,)
    assert individual.supported_target_kinds == ("core_student",)
    assert cluster.key == "collaborative_textual_analysis"
    assert cluster.criterion_kind == "local"
    assert cluster.standard_id is None
    assert cluster.supported_target_kinds == ("concord_group",)
    assert individual.default_scoring_scale_preset_id == (
        "saved-four-level" if recommend else None
    )
    assert cluster.default_scoring_scale_preset_id == (
        "saved-four-level" if recommend else None
    )
    assert not hasattr(preset, "score_records")


def test_native_to_reusable_save_preserves_semantics_and_source_history(
    tmp_path: Path,
) -> None:
    root, library, revision = _fixture(tmp_path)
    before = tuple(list_work_snapshots(root, _work()))
    graph_before = load_current_record_graph(
        root, _work(), standards_library=library
    ).graph
    assert graph_before.score_records == ()
    assert graph_before.score_evidence_links == ()
    _save_scale(root, library, revision)
    request = _request(revision)
    prepared = prepare_criterion_set_preset_from_activity(
        request, workspace_root=root, standards_library=library, clock=_clock
    )
    assert "Activity-native Criterion identities" in prepared.excluded_state
    assert "all Scores and Score Evidence Links" in prepared.excluded_state
    assert len(list_presets("criterion_set", workspace_root=root)) == 0
    _assert_source_untouched(root, library, before, graph_before)
    result = save_criterion_set_preset_from_activity(
        request,
        review_digest=prepared.review_digest,
        workspace_root=root,
        standards_library=library,
        clock=_clock,
    )
    assert result.revision == 1
    saved = load_current_preset(root, "criterion_set", request.preset_id).current
    assert isinstance(saved, CriterionSetPresetRevision)
    _assert_preset(saved, True)
    assert validate_preset(
        "criterion_set",
        request.preset_id,
        workspace_root=root,
        standards_library=library,
    ).revision == 1
    assert not hasattr(saved, "criterion_set_id")
    assert not hasattr(saved.criteria[0], "criterion_id")
    _assert_source_untouched(root, library, before, graph_before)


def test_native_save_without_scale_recommendation_is_legal(tmp_path: Path) -> None:
    root, library, revision = _fixture(tmp_path)
    request = _request(revision, recommend_scale=False)
    preview = prepare_criterion_set_preset_from_activity(
        request, workspace_root=root, standards_library=library
    )
    assert "Activity-native default Scoring Scale references" in preview.excluded_state
    save_criterion_set_preset_from_activity(
        request, review_digest=preview.review_digest,
        workspace_root=root, standards_library=library,
    )
    saved = load_current_preset(root, "criterion_set", request.preset_id).current
    assert isinstance(saved, CriterionSetPresetRevision)
    _assert_preset(saved, False)


@pytest.mark.parametrize(
    "failure", ("stale_revision", "changed_digest", "bad_scale_pair")
)
def test_preview_failure_or_mismatched_confirmation_makes_no_write(
    tmp_path: Path, failure: str
) -> None:
    root, library, revision = _fixture(tmp_path)
    _save_scale(root, library, revision)
    before = tuple(list_work_snapshots(root, _work()))
    graph_before = load_current_record_graph(
        root, _work(), standards_library=library
    ).graph
    request = _request(revision)
    if failure == "stale_revision":
        request = replace(request, expected_snapshot_revision=revision - 1)
        with pytest.raises(ConcordWorkflowConflictError):
            prepare_criterion_set_preset_from_activity(
                request, workspace_root=root, standards_library=library
            )
    elif failure == "bad_scale_pair":
        request = replace(request, recommended_scoring_scale_preset_revision_id=None)
        with pytest.raises(ConcordWorkflowValidationError):
            prepare_criterion_set_preset_from_activity(
                request, workspace_root=root, standards_library=library
            )
    else:
        preview = prepare_criterion_set_preset_from_activity(
            request, workspace_root=root, standards_library=library
        )
        with pytest.raises(ConcordWorkflowConflictError):
            save_criterion_set_preset_from_activity(
                request, review_digest="0" * 64,
                workspace_root=root, standards_library=library,
            )
        assert preview.review_digest != "0" * 64
    assert list_presets("criterion_set", workspace_root=root) == ()
    _assert_source_untouched(root, library, before, graph_before)


def test_reusing_same_preset_identity_is_refused_without_source_mutation(
    tmp_path: Path,
) -> None:
    root, library, revision = _fixture(tmp_path)
    _save_scale(root, library, revision)
    request = _request(revision)
    preview = prepare_criterion_set_preset_from_activity(
        request, workspace_root=root, standards_library=library
    )
    save_criterion_set_preset_from_activity(
        request, review_digest=preview.review_digest,
        workspace_root=root, standards_library=library,
    )
    before = tuple(list_work_snapshots(root, _work()))
    graph_before = load_current_record_graph(
        root, _work(), standards_library=library
    ).graph
    with pytest.raises((ConcordWorkflowConflictError, ConcordWorkflowValidationError)):
        prepare_criterion_set_preset_from_activity(
            request, workspace_root=root, standards_library=library
        )
    assert len(list_presets("criterion_set", workspace_root=root)) == 1
    _assert_source_untouched(root, library, before, graph_before)


def test_inactive_core_alignment_fails_closed_before_preset_save(
    tmp_path: Path,
) -> None:
    root, library, revision = _fixture(tmp_path)
    request = _request(revision, recommend_scale=False)
    before = tuple(list_work_snapshots(root, _work()))
    graph_before = load_current_record_graph(
        root, _work(), standards_library=library
    ).graph
    # The source was built under an active Standard. If its alignment becomes
    # inactive, the authoritative graph load must fail *before* preset logic;
    # treating an integrity error as a preset validation error would be wrong.
    with pytest.raises(
        ConcordStorageGraphIntegrityError, match="current graph is invalid"
    ):
        prepare_criterion_set_preset_from_activity(
            request,
            workspace_root=root,
            standards_library=_library(alignment_active=False),
        )
    assert list_presets("criterion_set", workspace_root=root) == ()
    _assert_source_untouched(root, library, before, graph_before)


def _wire_menu_to_synthetic_workspace(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    library: StandardsLibrary,
    *,
    save: bool,
    results: list[tuple[str, tuple[str, ...]]],
) -> None:
    monkeypatch.setattr(
        menu_scoring,
        "_latest",
        lambda _activity: show_activity(CLASS, ACTIVITY, workspace_root=root).summary,
    )
    monkeypatch.setattr(menu_scoring, "_library", lambda: library)
    monkeypatch.setattr(
        menu_scoring, "read_activity_criterion_set_selection",
        lambda class_id, activity_id, **kwargs: (
            read_activity_criterion_set_selection(
                class_id, activity_id, workspace_root=root, **kwargs
            )
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "list_criterion_sets",
        lambda class_id, activity_id, **kwargs: list_criterion_sets(
            class_id, activity_id, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "show_criterion_set",
        lambda class_id, activity_id, criterion_set_id, **kwargs: show_criterion_set(
            class_id, activity_id, criterion_set_id, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "show_scoring_scale",
        lambda class_id, activity_id, scoring_scale_id, **kwargs: (
            show_scoring_scale(
                class_id, activity_id, scoring_scale_id,
                workspace_root=root, **kwargs
            )
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "list_presets",
        lambda kind, **kwargs: list_presets(kind, workspace_root=root, **kwargs),
    )
    monkeypatch.setattr(
        menu_scoring, "get_preset_revision",
        lambda kind, preset_id, revision_id: get_preset_revision(
            kind, preset_id, revision_id, workspace_root=root
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "prepare_criterion_set_preset_from_activity",
        lambda request, **kwargs: prepare_criterion_set_preset_from_activity(
            request, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring, "save_criterion_set_preset_from_activity",
        lambda request, **kwargs: save_criterion_set_preset_from_activity(
            request, workspace_root=root, **kwargs
        ),
    )
    monkeypatch.setattr(
        menu_scoring,
        "select_one",
        lambda _title, values, *_args, **_kwargs: values[-1],
    )
    monkeypatch.setattr(menu_scoring, "confirm_write", lambda *_args, **_kwargs: save)
    monkeypatch.setattr(
        menu_scoring,
        "show_result",
        lambda title, lines: results.append((title, tuple(lines))),
    )
    monkeypatch.setattr(
        menu_scoring,
        "_handle_error",
        lambda _activity, error: pytest.fail(
            f"Actual teacher menu operation failed: {error}"
        ),
    )


@pytest.mark.parametrize("approve", (True, False))
def test_real_teacher_menu_save_uses_live_service_or_cancels_cleanly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, approve: bool
) -> None:
    root, library, revision = _fixture(tmp_path)
    _save_scale(root, library, revision)
    source_before = tuple(list_work_snapshots(root, _work()))
    graph_before = load_current_record_graph(
        root, _work(), standards_library=library
    ).graph
    results: list[tuple[str, tuple[str, ...]]] = []
    _wire_menu_to_synthetic_workspace(
        monkeypatch, root, library, save=approve, results=results
    )
    summary = show_activity(CLASS, ACTIVITY, workspace_root=root).summary
    menu_scoring._save_criterion_set_as_preset(
        summary,
        MenuSessionContext(actor=_actor()),
    )
    saved = list_presets("criterion_set", workspace_root=root)
    if approve:
        assert len(saved) == 1
        item = load_current_preset(root, "criterion_set", saved[0].preset_id).current
        assert isinstance(item, CriterionSetPresetRevision)
        _assert_preset(item, True)
        assert any(
            title == "Assessment Saved for Another Class"
            for title, _ in results
        )
    else:
        assert saved == ()
        assert not results
    _assert_source_untouched(root, library, source_before, graph_before)
