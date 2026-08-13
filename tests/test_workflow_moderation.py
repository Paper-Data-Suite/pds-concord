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
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import ensure_workspace_root

from concord.models import (
    ConcordModelError,
    EffectiveContext,
    EvidenceReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.storage import load_current_record_graph
from concord.workflows import (
    AddArtifactReviewRequest,
    AddModerationRecordRequest,
    ArtifactPagePlan,
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    CreateActivityContextRequest,
    CreateGroupWithMembersRequest,
    GroupMemberSpec,
    PrepareArtifactPagesRequest,
    ReplaceModerationRecordRequest,
    WorkflowActor,
    add_artifact_review,
    add_moderation_record,
    assess_moderation_requirement,
    create_activity_context,
    create_group_with_members,
    list_applicable_moderation_records,
    list_moderation_records,
    prepare_artifact_pages,
    replace_moderation_record,
    show_moderation_record,
)


def _clock(day: int) -> datetime:
    return datetime(2026, 8, day, 16, 0, tzinfo=timezone.utc)


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="teacher-1",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _privacy() -> PrivacyPolicy:
    return PrivacyPolicy(classification="teacher_restricted")


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(
        module_id="concord",
        class_id="class-1",
        work_id="activity-1",
    )


def _student(student_id: str) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _group_subject() -> SubjectReference:
    return SubjectReference(
        subject_kind="concord_group",
        subject_id="group-a",
        owning_system="concord",
    )


def _artifact_evidence(*, required: bool = False) -> EvidenceReference:
    return EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system="concord",
        record_id="artifact-1",
        moderation_requirement="required" if required else "not_required",
    )


def _workspace(tmp_path: Path) -> tuple[Path, int]:
    root = ensure_workspace_root(tmp_path / "workspace")
    write_class_metadata_for_class(
        root,
        create_class_metadata("class-1", "2026-2027", created_at=_clock(1)),
    )
    write_class_roster(
        root,
        create_roster(
            "class-1",
            (
                {
                    "student_id": "student-1",
                    "last_name": "One",
                    "first_name": "Alex",
                    "period": "1",
                },
                {
                    "student_id": "student-2",
                    "last_name": "Two",
                    "first_name": "Blair",
                    "period": "1",
                },
            ),
        ),
    )
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Moderation Activity",
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(2),
    )
    context = EffectiveContext(
        activity_id="activity-1",
        session_ids=("session-1",),
    )
    grouped = create_group_with_members(
        CreateGroupWithMembersRequest(
            class_id="class-1",
            activity_id="activity-1",
            group_id="group-a",
            label="Group A",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
            status="active",
            effective_context=context,
            members=(
                GroupMemberSpec(
                    membership_id="membership-1",
                    student_id="student-1",
                    effective_context=context,
                ),
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(3),
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            template_version_id="template-1",
            artifact_category="observation",
            expected_snapshot_revision=grouped.commit.snapshot_revision,
            actor=_actor(),
            pages=(
                ArtifactPagePlan(
                    page_number=1,
                    artifact_page_id="page-1",
                    return_expected=False,
                    route_required=False,
                ),
            ),
            expected_return_status="return_not_expected",
            privacy_policy=_privacy(),
            group_id="group-a",
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(4),
    )
    return root, prepared.commit.snapshot_revision


def test_moderation_add_list_show_and_no_score_side_effect(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    result = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-1",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_student("student-1"),),
            status="accepted_with_qualification",
            permitted_use="support_named_subject",
            rationale="The observation is specific enough for qualified use.",
            qualification="It does not establish who designed the procedure.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    summaries = list_moderation_records(
        "class-1", "activity-1", workspace_root=root
    )
    assert len(summaries) == 1
    assert summaries[0].moderation_record_id == "moderation-1"
    assert not hasattr(summaries[0], "rationale")
    detail = show_moderation_record(
        "class-1",
        "activity-1",
        "moderation-1",
        workspace_root=root,
    )
    assert "specific enough" in detail.rationale
    loaded = load_current_record_graph(root, _work())
    assert result.commit.snapshot_revision == revision + 1
    assert loaded.graph.score_records == ()
    assert loaded.graph.score_evidence_links == ()
    assert loaded.graph.artifact_reviews == ()


def test_same_evidence_different_subject_scopes_can_coexist(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    first = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-a",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_student("student-1"),),
            status="accepted",
            permitted_use="support_named_subject",
            rationale="Applicable to student one.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    second = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-b",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_student("student-2"),),
            status="insufficient",
            permitted_use="corroborate_only",
            rationale="Insufficient for an independent judgment.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert second.commit.snapshot_revision == first.commit.snapshot_revision + 1
    assert len(
        list_moderation_records(
            "class-1",
            "activity-1",
            workspace_root=root,
        )
    ) == 2


def test_duplicate_scope_is_rejected_order_insensitively(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    first = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-1",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(
                _student("student-2"),
                _student("student-1"),
            ),
            status="accepted",
            permitted_use="corroborate_only",
            rationale="General corroboration within the selected scope.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    with pytest.raises(ConcordWorkflowConflictError, match="equivalent current"):
        add_moderation_record(
            AddModerationRecordRequest(
                class_id="class-1",
                activity_id="activity-1",
                moderation_record_id="moderation-2",
                target_evidence_reference=_artifact_evidence(),
                target_subject_references=(
                    _student("student-1"),
                    _student("student-2"),
                ),
                status="accepted",
                permitted_use="corroborate_only",
                rationale="Would create a competing head.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=first.commit.snapshot_revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_moderation_revision_is_atomic_and_scope_stable(tmp_path: Path) -> None:
    root, revision = _workspace(tmp_path)
    first = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-before",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_group_subject(),),
            status="disputed",
            permitted_use="formative_only",
            rationale="The Group account is disputed.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(5),
    )
    successor = replace_moderation_record(
        ReplaceModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-before",
            replacement_moderation_record_id="moderation-after",
            correction_id="correction-moderation-1",
            reason="The dispute was resolved with corroborating evidence.",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_group_subject(),),
            status="accepted",
            permitted_use="support_group_score",
            rationale="The Group-level evidence is sufficiently corroborated.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=first.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(6),
    )
    loaded = load_current_record_graph(root, _work())
    assert successor.commit.snapshot_revision == first.commit.snapshot_revision + 1
    assert len(loaded.graph.moderation_records) == 2
    correction = loaded.graph.correction_records[0]
    assert correction.correction_type == "moderation_revision"
    assert correction.target_reference.record_id == "moderation-before"
    assert correction.replacement_reference is not None
    assert correction.replacement_reference.record_id == "moderation-after"


def test_applicable_reader_returns_general_and_scoped_candidates(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    general = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-general",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(),
            status="accepted",
            permitted_use="corroborate_only",
            rationale="Evidence is generally usable as corroboration.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-student",
            target_evidence_reference=_artifact_evidence(),
            target_subject_references=(_student("student-1"),),
            status="accepted",
            permitted_use="support_named_subject",
            rationale="Specific use is permitted for student one.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=general.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    applicable = list_applicable_moderation_records(
        "class-1",
        "activity-1",
        _artifact_evidence(),
        subject_context=(_student("student-1"),),
        workspace_root=root,
    )
    assert [item.moderation_record_id for item in applicable] == [
        "moderation-general",
        "moderation-student",
    ]


def test_review_required_moderation_cannot_be_weakened_by_reference(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    review = add_artifact_review(
        AddArtifactReviewRequest(
            class_id="class-1",
            activity_id="activity-1",
            artifact_instance_id="artifact-1",
            artifact_review_id="review-required",
            readability_judgment="readable",
            page_completeness_judgment="complete",
            filing_judgment="correct",
            author_judgment="confirmed",
            subject_judgment="confirmed",
            privacy_judgment="teacher_restricted",
            relevance_judgment="relevant",
            moderation_requirement="required",
            scoring_readiness="not_ready",
            review_outcome="moderation_required",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assessment = assess_moderation_requirement(
        "class-1",
        "activity-1",
        _artifact_evidence(required=False),
        subject_context=(_student("student-1"),),
        workspace_root=root,
    )
    assert review.commit.snapshot_revision == revision + 1
    assert assessment.required
    assert assessment.artifact_review_requires_moderation
    assert not assessment.evidence_reference_requires_moderation
    assert assessment.artifact_review_id == "review-required"


@pytest.mark.parametrize(
    ("status", "permitted_use", "subjects"),
    (
        ("rejected", "support_named_subject", (_student("student-1"),)),
        ("not_used_for_scoring", "formative_only", ()),
        ("insufficient", "support_named_subject", (_student("student-1"),)),
        ("disputed", "support_group_score", (_group_subject(),)),
        ("accepted", "support_named_subject", ()),
        ("accepted", "support_group_score", (_student("student-1"),)),
    ),
)
def test_moderation_structural_coherence(
    tmp_path: Path,
    status: str,
    permitted_use: str,
    subjects: tuple[SubjectReference, ...],
) -> None:
    root, revision = _workspace(tmp_path)
    with pytest.raises(ConcordModelError):
        add_moderation_record(
            AddModerationRecordRequest(
                class_id="class-1",
                activity_id="activity-1",
                moderation_record_id="moderation-invalid",
                target_evidence_reference=_artifact_evidence(),
                target_subject_references=subjects,
                status=status,
                permitted_use=permitted_use,
                rationale="Synthetic invalid combination.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_invalid_student_scope_and_mutable_external_lineage_are_rejected(
    tmp_path: Path,
) -> None:
    root, revision = _workspace(tmp_path)
    with pytest.raises(ConcordWorkflowNotFoundError):
        add_moderation_record(
            AddModerationRecordRequest(
                class_id="class-1",
                activity_id="activity-1",
                moderation_record_id="moderation-missing-student",
                target_evidence_reference=_artifact_evidence(),
                target_subject_references=(_student("student-missing"),),
                status="accepted",
                permitted_use="corroborate_only",
                rationale="Synthetic.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
    with pytest.raises(ConcordModelError):
        EvidenceReference(
            evidence_kind="quillan_response",
            owning_system="quillan",
            record_id="response-1",
            immutable_source_version="latest",
        )

def test_core_publication_reference_is_verified_through_public_core_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from concord.models import CorePublicationReference
    from concord.workflows import moderation as moderation_workflow

    root, revision = _workspace(tmp_path)
    reference = EvidenceReference(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="result-1",
        source_publication_reference=CorePublicationReference(
            publication_id="pub_" + "0" * 32,
            publication_schema_version="1",
        ),
    )
    seen: list[str] = []

    def _publication(_root: Path, publication_id: str) -> object:
        seen.append(publication_id)
        return SimpleNamespace(
            schema_version="1",
            work=SimpleNamespace(module_id="scoreform"),
        )

    monkeypatch.setattr(
        moderation_workflow,
        "get_canonical_publication_record",
        _publication,
    )
    result = add_moderation_record(
        AddModerationRecordRequest(
            class_id="class-1",
            activity_id="activity-1",
            moderation_record_id="moderation-publication",
            target_evidence_reference=reference,
            target_subject_references=(),
            status="accepted",
            permitted_use="corroborate_only",
            rationale="The exact published result may corroborate other evidence.",
            privacy_policy=_privacy(),
            expected_snapshot_revision=revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    assert seen == ["pub_" + "0" * 32]
    assert result.moderation_record_id == "moderation-publication"


def test_core_publication_reference_rejects_schema_or_producer_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from concord.models import CorePublicationReference
    from concord.workflows import ConcordWorkflowValidationError
    from concord.workflows import moderation as moderation_workflow

    root, revision = _workspace(tmp_path)
    reference = EvidenceReference(
        evidence_kind="scoreform_result",
        owning_system="scoreform",
        record_id="result-1",
        source_publication_reference=CorePublicationReference(
            publication_id="pub_" + "1" * 32,
            publication_schema_version="1",
        ),
    )
    monkeypatch.setattr(
        moderation_workflow,
        "get_canonical_publication_record",
        lambda *_args: SimpleNamespace(
            schema_version="2",
            work=SimpleNamespace(module_id="quillan"),
        ),
    )
    with pytest.raises(ConcordWorkflowValidationError):
        add_moderation_record(
            AddModerationRecordRequest(
                class_id="class-1",
                activity_id="activity-1",
                moderation_record_id="moderation-bad-publication",
                target_evidence_reference=reference,
                target_subject_references=(),
                status="accepted",
                permitted_use="corroborate_only",
                rationale="Synthetic.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )


def test_missing_core_publication_reference_is_not_silently_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pds_core.registry_services import RegistryServiceNotFoundError

    from concord.models import CorePublicationReference
    from concord.workflows import moderation as moderation_workflow

    root, revision = _workspace(tmp_path)
    reference = EvidenceReference(
        evidence_kind="quillan_response",
        owning_system="quillan",
        record_id="response-1",
        source_publication_reference=CorePublicationReference(
            publication_id="pub_" + "2" * 32,
        ),
    )

    def _missing(*_args: object) -> object:
        raise RegistryServiceNotFoundError("Publication Record not found.")

    monkeypatch.setattr(
        moderation_workflow,
        "get_canonical_publication_record",
        _missing,
    )
    with pytest.raises(ConcordWorkflowNotFoundError, match="Publication"):
        add_moderation_record(
            AddModerationRecordRequest(
                class_id="class-1",
                activity_id="activity-1",
                moderation_record_id="moderation-missing-publication",
                target_evidence_reference=reference,
                target_subject_references=(),
                status="accepted",
                permitted_use="corroborate_only",
                rationale="Synthetic.",
                privacy_policy=_privacy(),
                expected_snapshot_revision=revision,
                actor=_actor(),
            ),
            workspace_root=root,
        )
