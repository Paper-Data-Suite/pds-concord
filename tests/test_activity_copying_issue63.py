from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import StandardDefinition, StandardsLibrary, StandardsProfile
from pds_core.workspace import ensure_workspace_root

from concord.models import ConcordRecordReference, PrivacyPolicy, SubjectReference
from concord.storage import load_current_record_graph, load_current_snapshot
from concord.storage_errors import ConcordStorageNotFoundError
from concord.workflows.activity import create_activity_context, update_activity
from concord.workflows.activity_copy import (
    CopyActivityRequest,
    PrepareActivityCopyRequest,
    copy_activity,
    prepare_activity_copy,
)
from concord.workflows.criterion_sets import (
    CreateCriterionSetRequest,
    CriterionSpec,
    SelectActivityCriterionSetsRequest,
    create_criterion_set,
    select_activity_criterion_sets,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group import create_group
from concord.workflows.group_plan import CreateGroupPlanRequest, create_group_plan
from concord.workflows.models import (
    CreateActivityContextRequest,
    CreateGroupRequest,
    UpdateActivityRequest,
    WorkflowActor,
)


def _workspace(tmp_path: Path) -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    for class_id in ("class-a", "class-b"):
        metadata = create_class_metadata(
            class_id,
            "2026-2027",
            created_at=datetime(2026, 8, 26, tzinfo=timezone.utc),
        )
        write_class_metadata_for_class(root, metadata)
        roster = create_roster(
            class_id,
            (
                {
                    "student_id": f"{class_id}-student-1",
                    "last_name": "Student",
                    "first_name": "Synthetic",
                    "period": "1",
                },
            ),
        )
        write_class_roster(root, roster)
    return root


def _standards_library(
    *,
    profile_standards: tuple[str, ...] = ("standard-1", "standard-2"),
    include_profile: bool = True,
) -> StandardsLibrary:
    standards = (
        StandardDefinition(
            standard_id="standard-1",
            code="S1",
            source="synthetic",
            short_name="Standard 1",
            description="Synthetic standard one.",
        ),
        StandardDefinition(
            standard_id="standard-2",
            code="S2",
            source="synthetic",
            short_name="Standard 2",
            description="Synthetic standard two.",
        ),
    )
    profiles = (
        StandardsProfile(
            profile_id="profile-1",
            standards=profile_standards,
            source="synthetic",
            title="Synthetic profile",
        ),
    ) if include_profile else ()
    return StandardsLibrary(standards=standards, profiles=profiles)


def _standards_source(
    root: Path, library: StandardsLibrary
) -> WorkflowActor:
    actor = WorkflowActor(actor_id="teacher-standards")
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-a",
            activity_id="standards-activity",
            title="Standards Activity",
            activity_type="project",
            scoring_orientation="standards_based",
            session_id="standards-session",
            actor=actor,
            standards_profile_id="profile-1",
            focus_standard_ids=("standard-2", "standard-1"),
        ),
        workspace_root=root,
        standards_library=library,
    )
    return actor


def _source(
    root: Path, *, privacy: PrivacyPolicy | None = None
) -> tuple[WorkflowActor, int]:
    actor = WorkflowActor(actor_id="teacher-1", display_label="Teacher One")
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-a",
            activity_id="seminar-1",
            title="Seminar One",
            description="Reusable seminar configuration.",
            activity_type="socratic_seminar",
            scoring_orientation="evidence_only",
            session_id="source-session",
            actor=actor,
            activity_status="completed",
            session_status="completed",
            privacy_policy=privacy,
            external_reference_ids=("source-external",),
        ),
        workspace_root=root,
    )
    return actor, created.commit.snapshot_revision


def test_prepare_is_zero_write_and_copy_is_fresh_positive_allowlist(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    actor, _ = _source(
        root,
        privacy=PrivacyPolicy(classification="teacher_restricted"),
    )
    source_work = ModuleWorkRef(
        module_id="concord", class_id="class-a", work_id="seminar-1"
    )
    source_before = load_current_snapshot(root, source_work)

    request = PrepareActivityCopyRequest(
        source_class_id="class-a",
        source_activity_id="seminar-1",
        target_class_id="class-b",
        target_activity_id="seminar-copy",
        first_session_id="copy-session",
        first_session_label="First copied session",
    )
    prepared = prepare_activity_copy(request, workspace_root=root)

    assert prepared.source_status == "completed"
    assert prepared.title == "Seminar One"
    assert prepared.description == "Reusable seminar configuration."
    assert prepared.activity_type == "socratic_seminar"
    assert prepared.scoring_orientation == "evidence_only"
    assert prepared.privacy_policy == PrivacyPolicy(classification="teacher_restricted")
    assert len(prepared.review_digest) == 64
    assert load_current_snapshot(root, source_work) == source_before
    with pytest.raises(ConcordStorageNotFoundError):
        load_current_snapshot(
            root,
            ModuleWorkRef(
                module_id="concord", class_id="class-b", work_id="seminar-copy"
            ),
        )

    result = copy_activity(
        CopyActivityRequest(
            source_class_id=request.source_class_id,
            source_activity_id=request.source_activity_id,
            target_class_id=request.target_class_id,
            target_activity_id=request.target_activity_id,
            first_session_id=request.first_session_id,
            first_session_label=request.first_session_label,
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    loaded = load_current_record_graph(root, result.commit.work)
    assert len(loaded.graph.activities) == 1
    assert len(loaded.graph.sessions) == 1
    assert not loaded.graph.groups
    target = loaded.graph.activities[0]
    session = loaded.graph.sessions[0]
    assert target.activity_id == "seminar-copy"
    assert target.class_reference.record_id == "class-b"
    assert target.status == "draft"
    assert target.title == "Seminar One"
    assert target.description == "Reusable seminar configuration."
    assert target.criterion_set_ids == ()
    assert target.external_reference_ids == ()
    source_activity = load_current_record_graph(root, source_work).graph.activities[0]
    assert target.created_provenance != source_activity.created_provenance
    assert target.updated_provenance is None
    assert session.session_id == "copy-session"
    assert session.sequence == 1
    assert session.status == "planned"
    assert session.label == "First copied session"
    assert load_current_snapshot(root, source_work) == source_before


def test_selected_activity_owned_criterion_set_is_explicitly_not_copied(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    actor = WorkflowActor(actor_id="teacher-criteria")
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-a",
            activity_id="criteria-source",
            title="Criteria Source",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="criteria-session",
            actor=actor,
        ),
        workspace_root=root,
    )
    criterion = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-a",
            activity_id="criteria-source",
            criterion_set_id="source-criterion-set",
            lineage_id="source-criterion-lineage",
            name="Source Criteria",
            purpose="Synthetic source-only local criteria.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="local",
            criteria=(
                CriterionSpec(
                    criterion_id="source-local-criterion",
                    key="local_quality",
                    label="Local Quality",
                    definition="Synthetic local criterion.",
                    criterion_kind="local",
                    supported_target_kinds=("core_student",),
                ),
            ),
            status="active",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id="class-a",
            activity_id="criteria-source",
            criterion_set_ids=("source-criterion-set",),
            expected_snapshot_revision=criterion.commit.snapshot_revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    assert selected.criterion_set_ids == ("source-criterion-set",)

    request = PrepareActivityCopyRequest(
        source_class_id="class-a",
        source_activity_id="criteria-source",
        target_class_id="class-b",
        target_activity_id="criteria-copy",
        first_session_id="criteria-copy-session",
    )
    prepared = prepare_activity_copy(request, workspace_root=root)
    assert "criterion_sets_not_copied" in {item.code for item in prepared.diagnostics}
    copied = copy_activity(
        CopyActivityRequest(
            source_class_id=request.source_class_id,
            source_activity_id=request.source_activity_id,
            target_class_id=request.target_class_id,
            target_activity_id=request.target_activity_id,
            first_session_id=request.first_session_id,
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    target = load_current_record_graph(root, copied.commit.work)
    assert target.graph.activities[0].criterion_set_ids == ()
    assert not target.graph.criterion_sets
    assert not target.graph.criteria


def test_review_digest_ignores_unrelated_operational_state(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    actor, revision = _source(root)
    request = PrepareActivityCopyRequest(
        source_class_id="class-a",
        source_activity_id="seminar-1",
        target_class_id="class-b",
        target_activity_id="seminar-copy",
        first_session_id="copy-session",
    )
    prepared = prepare_activity_copy(request, workspace_root=root)
    repeated = prepare_activity_copy(request, workspace_root=root)
    assert repeated.review_digest == prepared.review_digest
    group = create_group(
        CreateGroupRequest(
            class_id="class-a",
            activity_id="seminar-1",
            group_id="new-operational-group",
            label="Operational Group",
            expected_snapshot_revision=revision,
            actor=actor,
        ),
        workspace_root=root,
    )
    assert group.commit.snapshot_revision > revision
    plan = create_group_plan(
        CreateGroupPlanRequest(
            class_id="class-a",
            activity_id="seminar-1",
            group_plan_id="signal-sentinel-plan",
            strategy="similar_signal",
            expected_snapshot_revision=group.commit.snapshot_revision,
            actor=actor,
            source_signal_set_id="privacy-sentinel-signal",
            source_signal_set_digest="a" * 64,
            source_signal_dimension_id="privacy-sentinel-dimension",
        ),
        workspace_root=root,
    )
    assert plan.commit.snapshot_revision > group.commit.snapshot_revision

    copied = copy_activity(
        CopyActivityRequest(
            source_class_id=request.source_class_id,
            source_activity_id=request.source_activity_id,
            target_class_id=request.target_class_id,
            target_activity_id=request.target_activity_id,
            first_session_id=request.first_session_id,
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    target = load_current_record_graph(root, copied.commit.work)
    assert not target.graph.groups
    assert not target.graph.group_plans


def test_copy_relevant_source_change_invalidates_review(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    actor, revision = _source(root)
    request = PrepareActivityCopyRequest(
        source_class_id="class-a",
        source_activity_id="seminar-1",
        target_class_id="class-b",
        target_activity_id="seminar-copy",
        first_session_id="copy-session",
    )
    prepared = prepare_activity_copy(request, workspace_root=root)
    update_activity(
        UpdateActivityRequest(
            class_id="class-a",
            activity_id="seminar-1",
            expected_snapshot_revision=revision,
            actor=actor,
            title="Changed source title",
        ),
        workspace_root=root,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="review is stale"):
        copy_activity(
            CopyActivityRequest(
                source_class_id=request.source_class_id,
                source_activity_id=request.source_activity_id,
                target_class_id=request.target_class_id,
                target_activity_id=request.target_activity_id,
                first_session_id=request.first_session_id,
                actor=actor,
                review_digest=prepared.review_digest,
            ),
            workspace_root=root,
        )


def test_overridden_title_is_not_bound_to_later_source_title_changes(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    actor, revision = _source(root)
    request = PrepareActivityCopyRequest(
        source_class_id="class-a",
        source_activity_id="seminar-1",
        target_class_id="class-b",
        target_activity_id="seminar-copy",
        first_session_id="copy-session",
        title="Independent target title",
        description=None,
    )
    prepared = prepare_activity_copy(request, workspace_root=root)
    update_activity(
        UpdateActivityRequest(
            class_id="class-a",
            activity_id="seminar-1",
            expected_snapshot_revision=revision,
            actor=actor,
            title="Changed source title",
        ),
        workspace_root=root,
    )
    copied = copy_activity(
        CopyActivityRequest(
            source_class_id=request.source_class_id,
            source_activity_id=request.source_activity_id,
            target_class_id=request.target_class_id,
            target_activity_id=request.target_activity_id,
            first_session_id=request.first_session_id,
            title="Independent target title",
            description=None,
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    target = load_current_record_graph(root, copied.commit.work).graph.activities[0]
    assert target.title == "Independent target title"
    assert target.description is None


def test_context_free_privacy_copies_classification_without_source_reason(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _source(
        root,
        privacy=PrivacyPolicy(
            classification="teacher_restricted",
            reason="Source-only rationale",
        ),
    )
    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-b",
            target_activity_id="seminar-copy",
            first_session_id="copy-session",
        ),
        workspace_root=root,
    )
    assert prepared.privacy_policy == PrivacyPolicy(
        classification="teacher_restricted"
    )


def test_contextual_privacy_is_tightened_and_source_audience_is_not_copied(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _source(
        root,
        privacy=PrivacyPolicy(
            classification="teacher_and_subjects",
            audience_references=(
                SubjectReference(
                    subject_kind="core_student",
                    subject_id="student-source",
                    owning_system="core",
                ),
            ),
        ),
    )
    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-b",
            target_activity_id="seminar-copy",
            first_session_id="copy-session",
        ),
        workspace_root=root,
    )
    assert prepared.privacy_policy == PrivacyPolicy(classification="teacher_restricted")
    assert [item.code for item in prepared.diagnostics] == [
        "privacy_context_not_copied",
        "external_references_not_copied",
    ]


@pytest.mark.parametrize(
    ("source_policy", "expected_classification", "expects_privacy_diagnostic"),
    (
        (None, None, False),
        (
            PrivacyPolicy(classification="teacher_restricted"),
            "teacher_restricted",
            False,
        ),
        (PrivacyPolicy(classification="classroom_shared"), "classroom_shared", False),
        (
            PrivacyPolicy(
                classification="group_and_teacher",
                audience_references=(
                    SubjectReference(
                        subject_kind="concord_group",
                        subject_id="source-group",
                        owning_system="concord",
                    ),
                ),
            ),
            "teacher_restricted",
            True,
        ),
        (
            PrivacyPolicy(
                classification="inherited",
                inherited_from=ConcordRecordReference(
                    record_kind="group",
                    record_id="source-group",
                ),
            ),
            "teacher_restricted",
            True,
        ),
        (
            PrivacyPolicy(
                classification="external_policy",
                policy_reference=ModuleRecordRef(
                    module_id="core",
                    record_kind="privacy_policy",
                    record_id="source-policy",
                ),
            ),
            "teacher_restricted",
            True,
        ),
    ),
)
def test_privacy_resolution_matrix(
    tmp_path: Path,
    source_policy: PrivacyPolicy | None,
    expected_classification: str | None,
    expects_privacy_diagnostic: bool,
) -> None:
    root = _workspace(tmp_path)
    _source(root, privacy=source_policy)
    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-b",
            target_activity_id="seminar-copy",
            first_session_id="copy-session",
        ),
        workspace_root=root,
    )
    actual_classification = (
        None
        if prepared.privacy_policy is None
        else prepared.privacy_policy.classification
    )
    assert actual_classification == expected_classification
    privacy_codes = {
        item.code
        for item in prepared.diagnostics
        if item.code == "privacy_context_not_copied"
    }
    assert bool(privacy_codes) is expects_privacy_diagnostic

def test_destination_is_create_only_and_exact_source_cannot_be_target(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    actor, _ = _source(root)
    with pytest.raises(ConcordWorkflowValidationError, match="cannot be its own"):
        prepare_activity_copy(
            PrepareActivityCopyRequest(
                source_class_id="class-a",
                source_activity_id="seminar-1",
                target_class_id="class-a",
                target_activity_id="seminar-1",
                first_session_id="copy-session",
            ),
            workspace_root=root,
        )

    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-b",
            target_activity_id="seminar-1",
            first_session_id="copy-session",
        ),
        workspace_root=root,
    )
    copy_activity(
        CopyActivityRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-b",
            target_activity_id="seminar-1",
            first_session_id="copy-session",
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="already exists"):
        prepare_activity_copy(
            PrepareActivityCopyRequest(
                source_class_id="class-a",
                source_activity_id="seminar-1",
                target_class_id="class-b",
                target_activity_id="seminar-1",
                first_session_id="another-session",
            ),
            workspace_root=root,
        )


def test_standards_references_are_revalidated_and_order_is_preserved(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    library = _standards_library()
    actor = _standards_source(root, library)
    request = PrepareActivityCopyRequest(
        source_class_id="class-a",
        source_activity_id="standards-activity",
        target_class_id="class-b",
        target_activity_id="standards-copy",
        first_session_id="copy-session",
    )
    prepared = prepare_activity_copy(
        request, workspace_root=root, standards_library=library
    )
    assert prepared.standards_profile_id == "profile-1"
    assert prepared.focus_standard_ids == ("standard-2", "standard-1")
    result = copy_activity(
        CopyActivityRequest(
            source_class_id=request.source_class_id,
            source_activity_id=request.source_activity_id,
            target_class_id=request.target_class_id,
            target_activity_id=request.target_activity_id,
            first_session_id=request.first_session_id,
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
        standards_library=library,
    )
    target = load_current_record_graph(
        root, result.commit.work, standards_library=library
    ).graph.activities[0]
    assert target.standards_profile_id == "profile-1"
    assert target.focus_standard_ids == ("standard-2", "standard-1")


@pytest.mark.parametrize(
    "stale_library",
    (
        _standards_library(include_profile=False),
        _standards_library(profile_standards=("standard-2",)),
    ),
)
def test_invalid_current_standards_block_before_target_mutation(
    tmp_path: Path, stale_library: StandardsLibrary
) -> None:
    root = _workspace(tmp_path)
    valid_library = _standards_library()
    _standards_source(root, valid_library)
    target_work = ModuleWorkRef("concord", "class-b", "standards-copy")
    with pytest.raises(ConcordWorkflowValidationError, match="standards"):
        prepare_activity_copy(
            PrepareActivityCopyRequest(
                source_class_id="class-a",
                source_activity_id="standards-activity",
                target_class_id="class-b",
                target_activity_id="standards-copy",
                first_session_id="copy-session",
            ),
            workspace_root=root,
            standards_library=stale_library,
        )
    with pytest.raises(ConcordStorageNotFoundError):
        load_current_snapshot(root, target_work)


@pytest.mark.parametrize(
    "source_status",
    ("draft", "configured", "active", "completed", "cancelled", "archived"),
)
def test_source_lifecycle_is_display_only_and_target_always_starts_draft(
    tmp_path: Path, source_status: str
) -> None:
    root = _workspace(tmp_path)
    actor = WorkflowActor(actor_id="teacher-status")
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-a",
            activity_id="status-source",
            title="Lifecycle source",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="source-session",
            actor=actor,
            activity_status=source_status,
        ),
        workspace_root=root,
    )
    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id="class-a",
            source_activity_id="status-source",
            target_class_id="class-b",
            target_activity_id="status-copy",
            first_session_id="target-session",
        ),
        workspace_root=root,
    )
    assert prepared.source_status == source_status
    result = copy_activity(
        CopyActivityRequest(
            source_class_id="class-a",
            source_activity_id="status-source",
            target_class_id="class-b",
            target_activity_id="status-copy",
            first_session_id="target-session",
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    target = load_current_record_graph(root, result.commit.work)
    assert target.graph.activities[0].status == "draft"
    assert target.graph.sessions[0].status == "planned"
    assert created.commit.work != result.commit.work


def test_same_class_copy_requires_only_a_fresh_activity_id(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    actor, _ = _source(root)
    prepared = prepare_activity_copy(
        PrepareActivityCopyRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-a",
            target_activity_id="seminar-repeat",
            first_session_id="repeat-session",
        ),
        workspace_root=root,
    )
    result = copy_activity(
        CopyActivityRequest(
            source_class_id="class-a",
            source_activity_id="seminar-1",
            target_class_id="class-a",
            target_activity_id="seminar-repeat",
            first_session_id="repeat-session",
            actor=actor,
            review_digest=prepared.review_digest,
        ),
        workspace_root=root,
    )
    assert result.commit.work == ModuleWorkRef(
        "concord", "class-a", "seminar-repeat"
    )
