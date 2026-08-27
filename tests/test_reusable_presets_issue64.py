from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
)
from pds_core.workspace import ensure_workspace_root

from concord.models import EffectiveContext, ParticipantReference, ScoringScaleLevel
from concord.reusable_preset_storage import (
    ReusablePresetStorageIntegrityError,
    load_current_preset,
    preset_library_root,
    preset_revision_path,
)
from concord.reusable_presets import CriterionPresetSpec
from concord.workflows.activity import create_activity_context
from concord.workflows.criterion_sets import (
    CreateCriterionSetRequest,
    CriterionSpec,
    create_criterion_set,
    list_criterion_sets,
    show_criterion_set,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import (
    AssignResponsibilityRequest,
    AssignRoleRequest,
    CreateActivityContextRequest,
    CreateSessionRequest,
    WorkflowActor,
)
from concord.workflows.responsibility import (
    assign_responsibility,
    list_responsibilities,
)
from concord.workflows.reusable_presets import (
    ApplyResponsibilityPresetRequest,
    ApplyRolePresetRequest,
    CreateCriterionSetPresetRequest,
    CreateResponsibilityPresetRequest,
    CreateRolePresetRequest,
    CreateScoringScalePresetRequest,
    CriterionTargetIdentity,
    MaterializeScoringSetupRequest,
    ReviseRolePresetRequest,
    ReviseScoringScalePresetRequest,
    SaveCriterionSetPresetFromActivityRequest,
    SaveResponsibilityPresetFromAssignmentRequest,
    SaveRolePresetFromAssignmentRequest,
    SaveScoringScalePresetFromActivityRequest,
    apply_responsibility_preset,
    apply_role_preset,
    create_criterion_set_preset,
    create_responsibility_preset,
    create_role_preset,
    create_scoring_scale_preset,
    list_presets,
    materialize_scoring_setup,
    prepare_criterion_set_preset_from_activity,
    prepare_responsibility_preset_application,
    prepare_responsibility_preset_from_assignment,
    prepare_role_preset_application,
    prepare_role_preset_from_assignment,
    prepare_scoring_scale_preset_from_activity,
    prepare_scoring_setup,
    retire_preset,
    revise_role_preset,
    revise_scoring_scale_preset,
    save_criterion_set_preset_from_activity,
    save_responsibility_preset_from_assignment,
    save_role_preset_from_assignment,
    save_scoring_scale_preset_from_activity,
)
from concord.workflows.role import assign_role, list_roles
from concord.workflows.scoring_scales import (
    CreateScoringScaleRequest,
    create_scoring_scale,
    list_scoring_scales,
    show_scoring_scale,
)
from concord.workflows.session import create_session


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 17, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    result = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Preset Test Activity",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    return root, result.commit.snapshot_revision


def _context() -> EffectiveContext:
    return EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )


def _participant() -> ParticipantReference:
    return ParticipantReference(
        participant_kind="authorized_actor",
        participant_id="teacher-helper",
        owning_system="concord",
    )


def _levels() -> tuple[ScoringScaleLevel, ...]:
    return (
        ScoringScaleLevel(
            value="developing",
            label="Developing",
            meaning="Developing evidence",
            position=1,
        ),
        ScoringScaleLevel(
            value="proficient",
            label="Proficient",
            meaning="Proficient evidence",
            position=2,
        ),
    )


def test_preset_discovery_is_read_only_when_workspace_is_missing(
    tmp_path: Path,
) -> None:
    root = tmp_path / "missing"
    assert list_presets("role", workspace_root=root) == ()
    assert not root.exists()


def test_role_and_responsibility_presets_materialize_fresh_assignments(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    create_role_preset(
        CreateRolePresetRequest(
            preset_id="discussion-leader",
            preset_revision_id="discussion-leader-v1",
            name="Discussion Leader",
            role_key="facilitator",
            role_label="Discussion Leader",
            description="Keeps the discussion moving.",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    role_request = ApplyRolePresetRequest(
        preset_id="discussion-leader",
        preset_revision_id="discussion-leader-v1",
        class_id="class-1",
        activity_id="activity-1",
        role_assignment_id="role-assignment-1",
        participant_reference=_participant(),
        effective_context=_context(),
        expected_snapshot_revision=revision,
        actor=_actor(),
    )
    prepared_role = prepare_role_preset_application(
        role_request,
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert list_roles("class-1", "activity-1", workspace_root=root) == ()
    role_result = apply_role_preset(
        role_request,
        review_digest=prepared_role.review_digest,
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    roles = list_roles("class-1", "activity-1", workspace_root=root)
    assert [item.role_assignment_id for item in roles] == ["role-assignment-1"]
    assert roles[0].role_key == "facilitator"
    assert role_result.commit.snapshot_revision == revision + 1

    create_responsibility_preset(
        CreateResponsibilityPresetRequest(
            preset_id="capture-evidence",
            preset_revision_id="capture-evidence-v1",
            name="Capture Evidence",
            description="Record the group's strongest evidence.",
            expected_output="A concise evidence list",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    responsibility_request = ApplyResponsibilityPresetRequest(
        preset_id="capture-evidence",
        preset_revision_id="capture-evidence-v1",
        class_id="class-1",
        activity_id="activity-1",
        responsibility_assignment_id="responsibility-1",
        assignee_reference=_participant(),
        effective_context=_context(),
        expected_snapshot_revision=role_result.commit.snapshot_revision,
        actor=_actor(),
    )
    prepared_responsibility = prepare_responsibility_preset_application(
        responsibility_request,
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    assert list_responsibilities(
        "class-1",
        "activity-1",
        workspace_root=root,
    ) == ()
    responsibility_result = apply_responsibility_preset(
        responsibility_request,
        review_digest=prepared_responsibility.review_digest,
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    responsibilities = list_responsibilities(
        "class-1",
        "activity-1",
        workspace_root=root,
    )
    assert [item.responsibility_assignment_id for item in responsibilities] == [
        "responsibility-1"
    ]
    assert responsibilities[0].description == "Record the group's strongest evidence."
    assert responsibility_result.commit.snapshot_revision == revision + 2

    role_preset = load_current_preset(root, "role", "discussion-leader").current
    assert not hasattr(role_preset, "participant_reference")
    responsibility_preset = load_current_preset(
        root,
        "responsibility",
        "capture-evidence",
    ).current
    assert not hasattr(responsibility_preset, "assignee_reference")


def test_scoring_presets_materialize_activity_native_state_atomically(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    create_scoring_scale_preset(
        CreateScoringScalePresetRequest(
            preset_id="two-level-proficiency",
            preset_revision_id="two-level-proficiency-v1",
            name="Two-Level Proficiency",
            scale_type="ordinal",
            levels=_levels(),
            intended_use="Quick local rubric",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    create_criterion_set_preset(
        CreateCriterionSetPresetRequest(
            preset_id="discussion-rubric",
            preset_revision_id="discussion-rubric-v1",
            name="Discussion Rubric",
            purpose="Assess discussion evidence",
            criterion_set_kind="local",
            criteria=(
                CriterionPresetSpec(
                    key="evidence",
                    label="Evidence",
                    definition="Uses relevant evidence.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_activity",),
                    default_scoring_scale_preset_id="two-level-proficiency",
                    default_scoring_scale_preset_revision_id=(
                        "two-level-proficiency-v1"
                    ),
                ),
                CriterionPresetSpec(
                    key="reasoning",
                    label="Reasoning",
                    definition="Explains the evidence.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_activity",),
                    default_scoring_scale_preset_id="two-level-proficiency",
                    default_scoring_scale_preset_revision_id=(
                        "two-level-proficiency-v1"
                    ),
                ),
            ),
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )

    scoring_request = MaterializeScoringSetupRequest(
        criterion_preset_id="discussion-rubric",
        criterion_preset_revision_id="discussion-rubric-v1",
        class_id="class-1",
        activity_id="activity-1",
        criterion_set_id="activity-rubric-1",
        criterion_set_lineage_id="activity-rubric-lineage",
        criterion_ids=(
            CriterionTargetIdentity(
                criterion_key="evidence",
                criterion_id="activity-criterion-evidence",
            ),
            CriterionTargetIdentity(
                criterion_key="reasoning",
                criterion_id="activity-criterion-reasoning",
            ),
        ),
        scoring_scale_preset_id="two-level-proficiency",
        scoring_scale_preset_revision_id="two-level-proficiency-v1",
        scoring_scale_id="activity-scale-1",
        scoring_scale_lineage_id="activity-scale-lineage",
        expected_snapshot_revision=revision,
        actor=_actor(),
    )
    assert list_criterion_sets(
        "class-1",
        "activity-1",
        workspace_root=root,
    ) == ()
    assert list_scoring_scales(
        "class-1",
        "activity-1",
        workspace_root=root,
    ) == ()
    prepared_scoring = prepare_scoring_setup(
        scoring_request,
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert list_criterion_sets(
        "class-1",
        "activity-1",
        workspace_root=root,
    ) == ()
    assert list_scoring_scales(
        "class-1",
        "activity-1",
        workspace_root=root,
    ) == ()
    result = materialize_scoring_setup(
        scoring_request,
        review_digest=prepared_scoring.review_digest,
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert result.commit.snapshot_revision == revision + 1
    scale = show_scoring_scale(
        "class-1",
        "activity-1",
        "activity-scale-1",
        workspace_root=root,
    )
    criterion_set = show_criterion_set(
        "class-1",
        "activity-1",
        "activity-rubric-1",
        workspace_root=root,
    )
    assert scale.summary.name == "Two-Level Proficiency"
    assert [item.criterion_id for item in criterion_set.criteria] == [
        "activity-criterion-evidence",
        "activity-criterion-reasoning",
    ]
    assert {
        item.default_scoring_scale_id for item in criterion_set.criteria
    } == {"activity-scale-1"}
    assert preset_library_root(root).is_dir()
    assert "shared" in preset_library_root(root).parts
    assert "activity-1" not in preset_library_root(root).parts

    revise_scoring_scale_preset(
        ReviseScoringScalePresetRequest(
            preset_id="two-level-proficiency",
            preset_revision_id="two-level-proficiency-v2",
            expected_revision=1,
            name="Two-Level Proficiency Revised",
            scale_type="ordinal",
            levels=_levels(),
            intended_use="Revised future default",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    unchanged = show_scoring_scale(
        "class-1",
        "activity-1",
        "activity-scale-1",
        workspace_root=root,
    )
    assert unchanged.summary.name == "Two-Level Proficiency"
    assert unchanged.summary.intended_use == "Quick local rubric"


def test_retiring_preset_preserves_immutable_history(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path)
    create_role_preset(
        CreateRolePresetRequest(
            preset_id="speaker-preset",
            preset_revision_id="speaker-preset-v1",
            name="Speaker",
            role_key="speaker",
            actor=_actor(),
        ),
        workspace_root=root,
    )
    retired = retire_preset(
        "role",
        "speaker-preset",
        preset_revision_id="speaker-preset-v2",
        expected_revision=1,
        actor=_actor(),
        workspace_root=root,
    )
    assert retired.revision == 2
    assert retired.status == "retired"
    current = load_current_preset(root, "role", "speaker-preset").current
    assert current.supersedes_preset_revision_id == "speaker-preset-v1"
    assert preset_revision_path(root, "role", "speaker-preset", 1).exists()
    assert preset_revision_path(root, "role", "speaker-preset", 2).exists()
    assert list_presets("role", workspace_root=root) == ()
    assert len(list_presets("role", workspace_root=root, include_retired=True)) == 1


def test_preset_identity_create_only_and_revision_concurrency(
    tmp_path: Path,
) -> None:
    root, _ = _workspace(tmp_path)
    created = create_role_preset(
        CreateRolePresetRequest(
            preset_id="create-only-role",
            preset_revision_id="create-only-role-v1",
            name="Create Only Role",
            role_key="facilitator",
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert created.revision == 1

    with pytest.raises(ConcordWorkflowConflictError):
        create_role_preset(
            CreateRolePresetRequest(
                preset_id="create-only-role",
                preset_revision_id="duplicate-v1",
                name="Duplicate",
                role_key="recorder",
                actor=_actor(),
            ),
            workspace_root=root,
        )

    with pytest.raises(ConcordWorkflowConflictError):
        revise_role_preset(
            ReviseRolePresetRequest(
                preset_id="create-only-role",
                preset_revision_id="create-only-role-v2",
                expected_revision=2,
                name="Stale Revision",
                role_key="facilitator",
                actor=_actor(),
            ),
            workspace_root=root,
        )

    with pytest.raises(ValueError):
        create_role_preset(
            CreateRolePresetRequest(
                preset_id="../escape",
                preset_revision_id="escape-v1",
                name="Invalid",
                role_key="facilitator",
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_canonical_revision_rejects_unknown_fields(tmp_path: Path) -> None:
    root, _ = _workspace(tmp_path)
    create_role_preset(
        CreateRolePresetRequest(
            preset_id="recorder-preset",
            preset_revision_id="recorder-preset-v1",
            name="Recorder",
            role_key="recorder",
            actor=_actor(),
        ),
        workspace_root=root,
    )
    path = preset_revision_path(root, "role", "recorder-preset", 1)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["student_id"] = "forbidden-student"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ReusablePresetStorageIntegrityError, match="unexpected"):
        load_current_preset(root, "role", "recorder-preset")


def _standards_library() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id="std-evidence",
                code="STD.EVIDENCE",
                source="synthetic",
                short_name="Evidence",
                description="Use evidence.",
                active=True,
            ),
            StandardDefinition(
                standard_id="std-reasoning",
                code="STD.REASONING",
                source="synthetic",
                short_name="Reasoning",
                description="Explain reasoning.",
                active=True,
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id="profile-1",
                standards=("std-evidence", "std-reasoning"),
                title="Synthetic Profile",
            ),
        ),
    )


def test_reviewed_role_application_blocks_stale_activity_snapshot(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    create_role_preset(
        CreateRolePresetRequest(
            preset_id="facilitator-preset",
            preset_revision_id="facilitator-preset-v1",
            name="Facilitator",
            role_key="facilitator",
            actor=_actor(),
        ),
        workspace_root=root,
    )
    request = ApplyRolePresetRequest(
        preset_id="facilitator-preset",
        preset_revision_id="facilitator-preset-v1",
        class_id="class-1",
        activity_id="activity-1",
        role_assignment_id="role-stale",
        participant_reference=_participant(),
        effective_context=_context(),
        expected_snapshot_revision=revision,
        actor=_actor(),
    )
    prepared = prepare_role_preset_application(request, workspace_root=root)
    session_result = create_session(
        CreateSessionRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-2",
            sequence=2,
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert session_result.commit.snapshot_revision == revision + 1
    with pytest.raises(ConcordWorkflowConflictError, match="changed"):
        apply_role_preset(
            request,
            review_digest=prepared.review_digest,
            workspace_root=root,
        )
    assert list_roles("class-1", "activity-1", workspace_root=root) == ()


def test_standard_backed_criterion_preset_requires_current_core_validation(
    tmp_path: Path,
) -> None:
    root, _ = _workspace(tmp_path)
    request = CreateCriterionSetPresetRequest(
        preset_id="standard-rubric",
        preset_revision_id="standard-rubric-v1",
        name="Standard Rubric",
        purpose="Assess evidence",
        criterion_set_kind="standard_backed",
        standards_profile_id="profile-1",
        criteria=(
            CriterionPresetSpec(
                key="evidence",
                label="Evidence",
                definition="Uses evidence.",
                criterion_kind="standard_backed",
                supported_target_kinds=("concord_activity",),
                standard_id="std-evidence",
            ),
        ),
        actor=_actor(),
    )
    with pytest.raises(ConcordWorkflowValidationError, match="standards library"):
        create_criterion_set_preset(request, workspace_root=root)
    created = create_criterion_set_preset(
        request,
        workspace_root=root,
        standards_library=_standards_library(),
    )
    assert created.revision == 1


def test_standard_backed_scoring_preset_must_govern_target_focus_standard(
    tmp_path: Path,
) -> None:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    library = _standards_library()
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Standards Activity",
            activity_type="project",
            scoring_orientation="standards_based",
            session_id="session-1",
            actor=_actor(),
            standards_profile_id="profile-1",
            focus_standard_ids=("std-reasoning",),
        ),
        workspace_root=root,
        standards_library=library,
    )
    create_criterion_set_preset(
        CreateCriterionSetPresetRequest(
            preset_id="evidence-rubric",
            preset_revision_id="evidence-rubric-v1",
            name="Evidence Rubric",
            purpose="Assess evidence",
            criterion_set_kind="standard_backed",
            standards_profile_id="profile-1",
            criteria=(
                CriterionPresetSpec(
                    key="evidence",
                    label="Evidence",
                    definition="Uses evidence.",
                    criterion_kind="standard_backed",
                    supported_target_kinds=("concord_activity",),
                    standard_id="std-evidence",
                ),
            ),
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=library,
    )
    request = MaterializeScoringSetupRequest(
        criterion_preset_id="evidence-rubric",
        criterion_preset_revision_id="evidence-rubric-v1",
        class_id="class-1",
        activity_id="activity-1",
        criterion_set_id="activity-evidence-rubric",
        criterion_set_lineage_id="activity-evidence-lineage",
        criterion_ids=(
            CriterionTargetIdentity(
                criterion_key="evidence",
                criterion_id="activity-evidence-criterion",
            ),
        ),
        expected_snapshot_revision=activity.commit.snapshot_revision,
        actor=_actor(),
    )
    with pytest.raises(ConcordWorkflowValidationError, match="Focus Standard"):
        prepare_scoring_setup(
            request,
            workspace_root=root,
            standards_library=library,
        )
    assert list_criterion_sets(
        "class-1",
        "activity-1",
        workspace_root=root,
        standards_library=library,
    ) == ()



def test_save_role_and_responsibility_presets_use_positive_allowlists(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    role_result = assign_role(
        AssignRoleRequest(
            class_id="class-1",
            activity_id="activity-1",
            role_assignment_id="source-role",
            participant_reference=_participant(),
            role_key="facilitator",
            role_label_snapshot="Discussion Leader",
            effective_context=_context(),
            expected_snapshot_revision=revision,
            actor=_actor(),
            group_id=None,
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    role_request = SaveRolePresetFromAssignmentRequest(
        class_id="class-1",
        activity_id="activity-1",
        role_assignment_id="source-role",
        preset_id="saved-role",
        preset_revision_id="saved-role-v1",
        name="Saved Discussion Leader",
        description="Keeps discussion moving.",
        expected_snapshot_revision=role_result.commit.snapshot_revision,
        actor=_actor(),
    )
    prepared_role = prepare_role_preset_from_assignment(
        role_request,
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    assert list_presets("role", workspace_root=root) == ()

    unrelated = create_session(
        CreateSessionRequest(
            class_id="class-1",
            activity_id="activity-1",
            session_id="session-2",
            sequence=2,
            expected_snapshot_revision=role_result.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    saved_role = save_role_preset_from_assignment(
        role_request,
        review_digest=prepared_role.review_digest,
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    assert saved_role.preset_id == "saved-role"
    role_preset = load_current_preset(root, "role", "saved-role").current
    assert role_preset.role_key == "facilitator"
    assert role_preset.role_label == "Discussion Leader"
    assert not hasattr(role_preset, "participant_reference")
    assert not hasattr(role_preset, "effective_context")

    responsibility_result = assign_responsibility(
        AssignResponsibilityRequest(
            class_id="class-1",
            activity_id="activity-1",
            responsibility_assignment_id="source-responsibility",
            assignee_reference=_participant(),
            description="Capture the group's evidence.",
            expected_output="Evidence notes",
            effective_context=_context(),
            expected_snapshot_revision=unrelated.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    responsibility_request = SaveResponsibilityPresetFromAssignmentRequest(
        class_id="class-1",
        activity_id="activity-1",
        responsibility_assignment_id="source-responsibility",
        preset_id="saved-responsibility",
        preset_revision_id="saved-responsibility-v1",
        name="Capture Evidence",
        expected_snapshot_revision=(
            responsibility_result.commit.snapshot_revision
        ),
        actor=_actor(),
    )
    prepared_responsibility = prepare_responsibility_preset_from_assignment(
        responsibility_request,
        workspace_root=root,
        clock=lambda: _clock(7),
    )
    saved_responsibility = save_responsibility_preset_from_assignment(
        responsibility_request,
        review_digest=prepared_responsibility.review_digest,
        workspace_root=root,
        clock=lambda: _clock(8),
    )
    assert saved_responsibility.preset_id == "saved-responsibility"
    responsibility_preset = load_current_preset(
        root,
        "responsibility",
        "saved-responsibility",
    ).current
    assert responsibility_preset.description == "Capture the group's evidence."
    assert responsibility_preset.expected_output == "Evidence notes"
    assert not hasattr(responsibility_preset, "assignee_reference")
    assert not hasattr(responsibility_preset, "group_id")


def test_save_native_scale_and_criterion_set_rewrites_reusable_scale_reference(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    scale_result = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="native-scale",
            lineage_id="native-scale-lineage",
            name="Native Proficiency",
            revision=1,
            scale_type="ordinal",
            levels=_levels(),
            status="active",
            intended_use="Native Activity scoring",
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    scale_save_request = SaveScoringScalePresetFromActivityRequest(
        class_id="class-1",
        activity_id="activity-1",
        scoring_scale_id="native-scale",
        preset_id="saved-scale",
        preset_revision_id="saved-scale-v1",
        expected_snapshot_revision=scale_result.commit.snapshot_revision,
        actor=_actor(),
    )
    prepared_scale = prepare_scoring_scale_preset_from_activity(
        scale_save_request,
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    save_scoring_scale_preset_from_activity(
        scale_save_request,
        review_digest=prepared_scale.review_digest,
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    scale_preset = load_current_preset(
        root,
        "scoring_scale",
        "saved-scale",
    ).current
    assert scale_preset.name == "Native Proficiency"
    assert scale_preset.levels == _levels()
    assert not hasattr(scale_preset, "scoring_scale_id")

    criterion_result = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="native-rubric",
            lineage_id="native-rubric-lineage",
            name="Native Discussion Rubric",
            purpose="Assess discussion reasoning",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="local",
            criteria=(
                CriterionSpec(
                    criterion_id="native-evidence",
                    key="evidence",
                    label="Evidence",
                    definition="Uses relevant evidence.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_activity",),
                    default_scoring_scale_id="native-scale",
                ),
            ),
            status="active",
            expected_snapshot_revision=scale_result.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    criterion_request = SaveCriterionSetPresetFromActivityRequest(
        class_id="class-1",
        activity_id="activity-1",
        criterion_set_id="native-rubric",
        preset_id="saved-rubric",
        preset_revision_id="saved-rubric-v1",
        expected_snapshot_revision=criterion_result.commit.snapshot_revision,
        actor=_actor(),
        recommended_scoring_scale_preset_id="saved-scale",
        recommended_scoring_scale_preset_revision_id="saved-scale-v1",
    )
    prepared_criterion = prepare_criterion_set_preset_from_activity(
        criterion_request,
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    assert "Activity-native Criterion identities" in prepared_criterion.excluded_state
    save_criterion_set_preset_from_activity(
        criterion_request,
        review_digest=prepared_criterion.review_digest,
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    criterion_preset = load_current_preset(
        root,
        "criterion_set",
        "saved-rubric",
    ).current
    assert criterion_preset.criteria[0].key == "evidence"
    assert criterion_preset.criteria[0].default_scoring_scale_preset_id == "saved-scale"
    assert (
        criterion_preset.criteria[0].default_scoring_scale_preset_revision_id
        == "saved-scale-v1"
    )
    serialized = json.dumps(
        {
            "preset": criterion_preset.preset_id,
            "criterion": criterion_preset.criteria[0].key,
            "scale": criterion_preset.criteria[0].default_scoring_scale_preset_id,
        }
    )
    assert "native-rubric" not in serialized
    assert "native-evidence" not in serialized
    assert "native-scale" not in serialized
