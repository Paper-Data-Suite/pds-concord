from __future__ import annotations

import tomllib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.academic_catalog import AcademicCatalogBuildError
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.publication_records import PUBLICATION_RECORD_SCHEMA_VERSION
from pds_core.publication_storage import (
    get_current_publication_record,
    load_publication_withdrawal,
)
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleRecordRef
from pds_core.workspace import ensure_workspace_root

import concord.academic_result_publication as publication_module
from concord.academic_result_manifest import RevisionReason
from concord.academic_result_manifest_generation import (
    GenerateAcademicResultManifestRequest,
    load_academic_result_manifest_revision,
)
from concord.academic_result_publication import (
    ConcordAcademicResultPublicationConflictError,
    ConcordAcademicResultPublicationIntegrityError,
    ConcordAcademicResultPublicationNotFoundError,
    ConcordAcademicResultPublicationPartialSuccessError,
    load_concord_publication_series_status,
    publish_concord_academic_results,
    query_concord_publication_catalog,
    rebuild_concord_publication_catalog,
    republish_concord_academic_results_after_withdrawal,
    supersede_concord_academic_results,
    withdraw_concord_academic_result_publication,
)
from concord.academic_work_registration import register_concord_academic_work
from concord.models import PrivacyPolicy, ScoreTargetReference, ScoringScaleLevel
from concord.pds_contract import (
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_DISPLAY_NAME,
    CONCORD_MODULE_ID,
)
from concord.pds_publication import get_publication_producer_profile
from concord.workflows import (
    AddScoreRequest,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    ReplaceScoreRequest,
    SelectActivityCriterionSetsRequest,
    WorkflowActor,
    add_score,
    create_activity_context,
    create_criterion_set,
    create_scoring_scale,
    replace_score,
    select_activity_criterion_sets,
)


def _clock(hour: int) -> datetime:
    return datetime(2026, 8, 14, hour, 0, tzinfo=timezone.utc)


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
        create_class_metadata(
            "class-1",
            "2026-2027",
            created_at=_clock(8),
        ),
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
            ),
        ),
    )
    activity = create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title="Synthetic Publication Activity",
            activity_type="project",
            scoring_orientation="local_criteria_only",
            session_id="session-1",
            actor=_actor(),
            activity_status="active",
            session_status="active",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
        ),
        workspace_root=root,
        clock=lambda: _clock(9),
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id="class-1",
            activity_id="activity-1",
            scoring_scale_id="scale-1",
            lineage_id="scale-lineage",
            name="Local scale",
            revision=1,
            scale_type="teacher_defined",
            levels=(
                ScoringScaleLevel(
                    value=1,
                    label="One",
                    meaning="First exact level.",
                ),
                ScoringScaleLevel(
                    value=2,
                    label="Two",
                    meaning="Second exact level.",
                ),
            ),
            status="active",
            expected_snapshot_revision=activity.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(10),
    )
    criterion_set = create_criterion_set(
        CreateCriterionSetRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_id="set-1",
            lineage_id="set-lineage",
            name="Local criteria",
            purpose="Synthetic publication validation.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="local",
            criteria=(
                CriterionSpec(
                    criterion_id="criterion-1",
                    key="collaboration",
                    label="Collaboration",
                    definition="Demonstrates collaborative practice.",
                    criterion_kind="local",
                    supported_target_kinds=("core_student",),
                    default_scoring_scale_id="scale-1",
                ),
            ),
            status="active",
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(11),
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id="class-1",
            activity_id="activity-1",
            criterion_set_ids=("set-1",),
            expected_snapshot_revision=criterion_set.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        clock=lambda: _clock(12),
    )
    scored = add_score(
        AddScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=1,
            basis="professional_judgment",
            rationale="Private publication rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(13),
    )
    register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )
    return root, scored.commit.snapshot_revision


def _request(
    revision: int,
    *,
    reason: RevisionReason = "initial",
) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id="class-1",
        activity_id="activity-1",
        expected_snapshot_revision=revision,
        actor=_actor(),
        revision_reason=reason,
    )


def test_publication_producer_profile_and_entry_point_are_exact() -> None:
    profile = get_publication_producer_profile()
    assert profile.module_id == CONCORD_MODULE_ID
    assert profile.display_name == CONCORD_DISPLAY_NAME
    assert profile.supported_core_publication_schema_versions == frozenset(
        {PUBLICATION_RECORD_SCHEMA_VERSION}
    )
    assert profile.supported_academic_work_contract_versions == frozenset(
        {CONCORD_ACADEMIC_WORK_CONTRACT_VERSION}
    )
    assert len(profile.publication_contracts) == 1
    support = profile.publication_contracts[0]
    assert support.publication_kind == "academic_result_set"
    assert support.manifest_contract_versions == frozenset(
        {"concord_academic_result_manifest_v1"}
    )
    assert support.supported_capabilities == frozenset(
        {"criterion_scores", "moderated_scores", "standards_ratings"}
    )
    assert not support.allows_missing_source_record
    assert len(support.source_record_contracts) == 1
    source = support.source_record_contracts[0]
    assert source.record_kind == CONCORD_ACTIVITY_RECORD_KIND
    assert source.contract_versions == frozenset(
        {CONCORD_ACTIVITY_CONTRACT_VERSION}
    )
    assert not source.allows_unversioned

    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    entry_points = data["project"]["entry-points"]
    assert entry_points["paper_data_suite.publication_producers"] == {
        "concord": "concord.pds_publication:get_publication_producer_profile"
    }
    assert entry_points["paper_data_suite.modules"] == {
        "concord": "concord.pds_module:get_module_profile"
    }


def test_first_publication_exact_mapping_and_replay(tmp_path: Path) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    request = _request(snapshot_revision)
    created = publish_concord_academic_results(
        request,
        workspace_root=root,
        clock=lambda: _clock(14),
    )

    publication = created.publication
    generation = created.manifest_generation
    expected_source = ModuleRecordRef(
        module_id=CONCORD_MODULE_ID,
        record_kind=CONCORD_ACTIVITY_RECORD_KIND,
        record_id="activity-1",
        contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
    )
    assert created.disposition == "created"
    assert publication.publication_id.startswith("pub_")
    assert publication.work == generation.manifest.work
    assert publication.source_record == expected_source
    assert publication.publication_kind == "academic_result_set"
    assert publication.capabilities == ("criterion_scores",)
    assert publication.record_set_id == CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
    assert publication.record_set_revision == 1
    assert publication.manifest_contract_version == (
        "concord_academic_result_manifest_v1"
    )
    assert publication.manifest_path == generation.relative_path
    assert publication.manifest_digest_algorithm == "sha256"
    assert publication.manifest_digest == generation.sha256
    assert publication.academic_work_registration_revision == 1
    assert publication.supersedes_publication_id is None
    assert created.registration.registration_revision == 1
    assert created.compatibility.compatible
    assert created.compatibility.codes == ()
    assert generation.path.read_bytes() == generation.content
    assert b"Private publication rationale" not in generation.content

    replay = publish_concord_academic_results(
        request,
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    assert replay.disposition == "existing"
    assert replay.publication == publication
    assert replay.manifest_generation.disposition == "existing"
    assert replay.manifest_generation.revision == 1
    assert replay.manifest_generation.content == generation.content


def test_first_publication_never_silently_supersedes_existing_series(
    tmp_path: Path,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    first_bytes = first.manifest_generation.path.read_bytes()

    replaced = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-1",
            reason="Additional observation changed teacher judgment.",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Private revised rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(15),
    )

    with pytest.raises(ConcordAcademicResultPublicationConflictError):
        publish_concord_academic_results(
            _request(
                replaced.commit.snapshot_revision,
                reason="native_state_change",
            ),
            workspace_root=root,
            clock=lambda: _clock(16),
        )

    unpublished = load_academic_result_manifest_revision(
        root,
        first.publication.work,
        2,
    )
    assert unpublished.revision == 2
    assert unpublished.path.exists()
    assert unpublished.manifest.scores[-1].value == 2
    assert first.manifest_generation.path.read_bytes() == first_bytes


def test_explicit_supersession_exact_mapping_replay_and_immutability(
    tmp_path: Path,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    first_manifest_bytes = first.manifest_generation.path.read_bytes()
    first_record_path = (
        root
        / "registry"
        / "publications"
        / f"{first.publication.publication_id}.json"
    )
    first_record_bytes = first_record_path.read_bytes()

    replaced = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-1",
            reason="Additional observation changed teacher judgment.",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Private revised rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    successor_request = _request(
        replaced.commit.snapshot_revision,
        reason="native_state_change",
    )
    created = supersede_concord_academic_results(
        successor_request,
        expected_current_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(16),
    )

    assert created.disposition == "created"
    assert created.publication.record_set_revision == 2
    assert created.publication.supersedes_publication_id == (
        first.publication.publication_id
    )
    assert created.publication.source_record == first.publication.source_record
    assert created.publication.work == first.publication.work
    assert created.publication.publication_kind == "academic_result_set"
    assert created.publication.record_set_id == (
        CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
    )
    assert created.publication.capabilities == ("criterion_scores",)
    assert created.manifest_generation.manifest.scores[-1].value == 2
    assert first.manifest_generation.path.read_bytes() == first_manifest_bytes
    assert first_record_path.read_bytes() == first_record_bytes

    successor_manifest_bytes = created.manifest_generation.path.read_bytes()
    replay = supersede_concord_academic_results(
        successor_request,
        expected_current_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    assert replay.disposition == "existing"
    assert replay.publication == created.publication
    assert replay.manifest_generation.disposition == "existing"
    assert replay.manifest_generation.revision == 2
    assert replay.manifest_generation.path.read_bytes() == successor_manifest_bytes
    assert first.manifest_generation.path.read_bytes() == first_manifest_bytes
    assert first_record_path.read_bytes() == first_record_bytes


def test_supersession_rejects_stale_expected_head_before_core_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    first_record_path = (
        root
        / "registry"
        / "publications"
        / f"{first.publication.publication_id}.json"
    )
    first_record_bytes = first_record_path.read_bytes()
    replaced = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-1",
            reason="Material change before stale supersession test.",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Private stale-head rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    successor_request = _request(
        replaced.commit.snapshot_revision,
        reason="native_state_change",
    )
    real_supersede = publication_module.supersede_manifest_revision
    core_called = False

    def forbidden(*args: object, **kwargs: object) -> object:
        nonlocal core_called
        core_called = True
        raise AssertionError("Core supersession must not run for a stale head")

    monkeypatch.setattr(
        publication_module,
        "supersede_manifest_revision",
        forbidden,
    )
    with pytest.raises(ConcordAcademicResultPublicationConflictError):
        supersede_concord_academic_results(
            successor_request,
            expected_current_publication_id="pub_" + ("0" * 32),
            workspace_root=root,
            clock=lambda: _clock(16),
        )
    assert not core_called
    assert first_record_path.read_bytes() == first_record_bytes
    unpublished = load_academic_result_manifest_revision(
        root,
        first.publication.work,
        2,
    )
    assert unpublished.manifest.scores[-1].value == 2

    monkeypatch.setattr(
        publication_module,
        "supersede_manifest_revision",
        real_supersede,
    )
    recovered = supersede_concord_academic_results(
        successor_request,
        expected_current_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    assert recovered.disposition == "created"
    assert recovered.manifest_generation.disposition == "existing"
    assert recovered.manifest_generation.revision == 2
    assert recovered.publication.supersedes_publication_id == (
        first.publication.publication_id
    )


def test_supersession_requires_a_later_material_public_projection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    core_called = False

    def forbidden(*args: object, **kwargs: object) -> object:
        nonlocal core_called
        core_called = True
        raise AssertionError("Core supersession must not run without a successor")

    monkeypatch.setattr(
        publication_module,
        "supersede_manifest_revision",
        forbidden,
    )
    with pytest.raises(ConcordAcademicResultPublicationConflictError):
        supersede_concord_academic_results(
            _request(snapshot_revision, reason="native_state_change"),
            expected_current_publication_id=first.publication.publication_id,
            workspace_root=root,
            clock=lambda: _clock(15),
        )
    assert not core_called
    assert first.manifest_generation.path.read_bytes() == (
        first.manifest_generation.content
    )
    assert tuple(first.manifest_generation.path.parent.glob("*.json")) == (
        first.manifest_generation.path,
    )


def test_withdrawal_is_idempotent_and_never_reactivates_predecessor(
    tmp_path: Path,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    first_record_path = (
        root
        / "registry"
        / "publications"
        / f"{first.publication.publication_id}.json"
    )
    first_record_bytes = first_record_path.read_bytes()
    first_manifest_bytes = first.manifest_generation.path.read_bytes()

    replaced = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-withdrawal-1",
            reason="Material correction before withdrawal.",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Private withdrawal rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    second = supersede_concord_academic_results(
        _request(
            replaced.commit.snapshot_revision,
            reason="native_state_change",
        ),
        expected_current_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    second_record_path = (
        root
        / "registry"
        / "publications"
        / f"{second.publication.publication_id}.json"
    )
    second_record_bytes = second_record_path.read_bytes()
    second_manifest_bytes = second.manifest_generation.path.read_bytes()

    withdrawn = withdraw_concord_academic_result_publication(
        "class-1",
        "activity-1",
        publication_id=second.publication.publication_id,
        reason="Teacher requested correction before reuse.",
        workspace_root=root,
    )
    assert withdrawn.disposition == "created"
    assert withdrawn.publication == second.publication
    assert withdrawn.withdrawal.publication_id == second.publication.publication_id
    assert withdrawn.manifest_verification == "verified"
    assert get_current_publication_record(
        root,
        second.publication.work,
        "academic_result_set",
        CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    ) is None
    assert first_record_path.read_bytes() == first_record_bytes
    assert second_record_path.read_bytes() == second_record_bytes
    assert first.manifest_generation.path.read_bytes() == first_manifest_bytes
    assert second.manifest_generation.path.read_bytes() == second_manifest_bytes

    replay = withdraw_concord_academic_result_publication(
        "class-1",
        "activity-1",
        publication_id=second.publication.publication_id,
        reason="Teacher requested correction before reuse.",
        workspace_root=root,
    )
    assert replay.disposition == "existing"
    assert replay.withdrawal == withdrawn.withdrawal
    assert get_current_publication_record(
        root,
        second.publication.work,
        "academic_result_set",
        CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    ) is None


def test_withdrawal_rejects_different_reason_on_replay(tmp_path: Path) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    withdraw_concord_academic_result_publication(
        "class-1",
        "activity-1",
        publication_id=first.publication.publication_id,
        reason="Original withdrawal reason.",
        workspace_root=root,
    )
    with pytest.raises(ConcordAcademicResultPublicationConflictError):
        withdraw_concord_academic_result_publication(
            "class-1",
            "activity-1",
            publication_id=first.publication.publication_id,
            reason="Contradictory withdrawal reason.",
            workspace_root=root,
        )


def test_withdrawal_remains_possible_when_bound_manifest_is_missing(
    tmp_path: Path,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    publication_path = (
        root
        / "registry"
        / "publications"
        / f"{first.publication.publication_id}.json"
    )
    publication_bytes = publication_path.read_bytes()
    first.manifest_generation.path.unlink()

    withdrawn = withdraw_concord_academic_result_publication(
        "class-1",
        "activity-1",
        publication_id=first.publication.publication_id,
        reason="Manifest requires repair before any future publication.",
        workspace_root=root,
    )
    assert withdrawn.disposition == "created"
    assert withdrawn.manifest_verification == "missing"
    assert publication_path.read_bytes() == publication_bytes
    assert load_publication_withdrawal(
        root,
        first.publication.publication_id,
    ) == withdrawn.withdrawal
    assert get_current_publication_record(
        root,
        first.publication.work,
        "academic_result_set",
        CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    ) is None


def test_corrected_republication_explicitly_supersedes_withdrawn_head(
    tmp_path: Path,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    withdrawn = withdraw_concord_academic_result_publication(
        "class-1",
        "activity-1",
        publication_id=first.publication.publication_id,
        reason="Correction required.",
        workspace_root=root,
    )
    first_record_path = (
        root
        / "registry"
        / "publications"
        / f"{first.publication.publication_id}.json"
    )
    first_record_bytes = first_record_path.read_bytes()
    first_manifest_bytes = first.manifest_generation.path.read_bytes()

    with pytest.raises(ConcordAcademicResultPublicationConflictError):
        republish_concord_academic_results_after_withdrawal(
            _request(snapshot_revision, reason="projection_correction"),
            expected_withdrawn_head_publication_id=(
                first.publication.publication_id
            ),
            workspace_root=root,
            clock=lambda: _clock(15),
        )
    assert tuple(first.manifest_generation.path.parent.glob("*.json")) == (
        first.manifest_generation.path,
    )

    replaced = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-republish-1",
            reason="Correct withdrawn academic result.",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Private corrected rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    corrected_request = _request(
        replaced.commit.snapshot_revision,
        reason="native_state_change",
    )
    corrected = republish_concord_academic_results_after_withdrawal(
        corrected_request,
        expected_withdrawn_head_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(17),
    )
    assert corrected.disposition == "created"
    assert corrected.publication.record_set_revision == 2
    assert corrected.publication.supersedes_publication_id == (
        first.publication.publication_id
    )
    assert corrected.manifest_generation.revision == 2
    assert load_publication_withdrawal(
        root,
        first.publication.publication_id,
    ) == withdrawn.withdrawal
    assert first_record_path.read_bytes() == first_record_bytes
    assert first.manifest_generation.path.read_bytes() == first_manifest_bytes
    assert get_current_publication_record(
        root,
        first.publication.work,
        "academic_result_set",
        CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    ) == corrected.publication

    replay = republish_concord_academic_results_after_withdrawal(
        corrected_request,
        expected_withdrawn_head_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(18),
    )
    assert replay.disposition == "existing"
    assert replay.publication == corrected.publication
    assert replay.manifest_generation.disposition == "existing"
    assert replay.manifest_generation.revision == 2


def test_series_status_reports_missing_catalog_without_creating_it(
    tmp_path: Path,
) -> None:
    root, _snapshot_revision = _workspace(tmp_path)

    state = load_concord_publication_series_status(
        "class-1",
        "activity-1",
        workspace_root=root,
    )

    assert state.producer_revisions == ()
    assert state.producer_head is None
    assert state.producer_head_projection_digest is None
    assert state.publications == ()
    assert state.withdrawals == ()
    assert state.core_head is None
    assert state.core_head_withdrawal is None
    assert state.current_selectable_publication is None
    assert state.current_registration_revision == 1
    assert not state.catalog_available
    assert state.catalog_rows == ()

    with pytest.raises(ConcordAcademicResultPublicationNotFoundError):
        query_concord_publication_catalog(
            "class-1",
            "activity-1",
            state="all",
            workspace_root=root,
        )


def test_catalog_rebuild_query_and_series_state_follow_canonical_lifecycle(
    tmp_path: Path,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    first = publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    first_row = first.catalog.publication
    assert first_row.publication_id == first.publication.publication_id
    assert first_row.is_series_head
    assert not first_row.is_withdrawn
    assert first_row.is_current_selectable

    current = query_concord_publication_catalog(
        "class-1",
        "activity-1",
        required_capabilities=("criterion_scores",),
        state="current",
        workspace_root=root,
    )
    assert current == (first_row,)
    assert query_concord_publication_catalog(
        "class-1",
        "activity-1",
        required_capabilities=("standards_ratings",),
        state="current",
        workspace_root=root,
    ) == ()

    replaced = replace_score(
        ReplaceScoreRequest(
            class_id="class-1",
            activity_id="activity-1",
            score_record_id="score-1",
            replacement_score_record_id="score-2",
            correction_id="correction-catalog",
            reason="Material catalog lifecycle change.",
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id="student-1",
                owning_system="core",
            ),
            criterion_id="criterion-1",
            scoring_scale_id="scale-1",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Private catalog lifecycle rationale.",
            privacy_policy=PrivacyPolicy(
                classification="teacher_restricted"
            ),
            expected_snapshot_revision=snapshot_revision,
            actor=_actor(),
            session_id="session-1",
        ),
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    second = supersede_concord_academic_results(
        _request(
            replaced.commit.snapshot_revision,
            reason="native_state_change",
        ),
        expected_current_publication_id=first.publication.publication_id,
        workspace_root=root,
        clock=lambda: _clock(16),
    )
    assert second.catalog.publication.is_series_head
    assert second.catalog.publication.is_current_selectable

    superseded_state = load_concord_publication_series_status(
        "class-1",
        "activity-1",
        workspace_root=root,
    )
    assert superseded_state.producer_revisions == (1, 2)
    assert superseded_state.producer_head_revision == 2
    assert superseded_state.producer_head_projection_digest == (
        second.manifest_generation.manifest.projection.projection_digest
    )
    assert superseded_state.core_head == second.publication
    assert superseded_state.current_selectable_publication == second.publication
    assert superseded_state.catalog_available
    assert len(superseded_state.catalog_rows) == 2
    by_id = {
        row.publication_id: row for row in superseded_state.catalog_rows
    }
    assert not by_id[first.publication.publication_id].is_series_head
    assert not by_id[first.publication.publication_id].is_current_selectable
    assert by_id[second.publication.publication_id].is_series_head
    assert by_id[second.publication.publication_id].is_current_selectable

    withdrawn = withdraw_concord_academic_result_publication(
        "class-1",
        "activity-1",
        publication_id=second.publication.publication_id,
        reason="Teacher requested correction before republication.",
        workspace_root=root,
    )
    assert withdrawn.catalog.publication.is_series_head
    assert withdrawn.catalog.publication.is_withdrawn
    assert not withdrawn.catalog.publication.is_current_selectable

    withdrawn_state = load_concord_publication_series_status(
        "class-1",
        "activity-1",
        workspace_root=root,
    )
    assert withdrawn_state.core_head == second.publication
    assert withdrawn_state.core_head_withdrawal == withdrawn.withdrawal
    assert withdrawn_state.current_selectable_publication is None
    assert withdrawn_state.catalog_available
    withdrawn_row = next(
        row
        for row in withdrawn_state.catalog_rows
        if row.publication_id == second.publication.publication_id
    )
    assert withdrawn_row.is_series_head
    assert withdrawn_row.is_withdrawn
    assert not withdrawn_row.is_current_selectable

    rebuilt = rebuild_concord_publication_catalog(
        "class-1",
        "activity-1",
        publication_id=second.publication.publication_id,
        workspace_root=root,
    )
    assert rebuilt.publication == withdrawn_row


def test_series_status_rejects_catalog_rows_that_disagree_with_canonical_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    publish_concord_academic_results(
        _request(snapshot_revision),
        workspace_root=root,
        clock=lambda: _clock(14),
    )

    monkeypatch.setattr(
        publication_module,
        "query_publication_catalog",
        lambda *_args, **_kwargs: (),
    )
    with pytest.raises(ConcordAcademicResultPublicationIntegrityError):
        load_concord_publication_series_status(
            "class-1",
            "activity-1",
            workspace_root=root,
        )


def test_catalog_failure_after_canonical_publish_is_recoverable_partial_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, snapshot_revision = _workspace(tmp_path)
    request = _request(snapshot_revision)
    real_rebuild = publication_module.rebuild_academic_catalog

    def fail_rebuild(*_args: object, **_kwargs: object) -> object:
        raise AcademicCatalogBuildError("Synthetic catalog rebuild failure.")

    monkeypatch.setattr(
        publication_module,
        "rebuild_academic_catalog",
        fail_rebuild,
    )
    with pytest.raises(
        ConcordAcademicResultPublicationPartialSuccessError
    ) as captured:
        publish_concord_academic_results(
            request,
            workspace_root=root,
            clock=lambda: _clock(14),
        )

    state = captured.value.state
    assert state.canonical_state == "confirmed"
    assert state.publication is not None
    assert state.catalog_rebuild_attempted
    assert not state.catalog_replacement_completed
    assert not state.catalog_verification_completed
    assert state.catalog_build is None
    assert isinstance(state.catalog_error, AcademicCatalogBuildError)
    assert get_current_publication_record(
        root,
        state.publication.work,
        "academic_result_set",
        CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    ) == state.publication

    monkeypatch.setattr(
        publication_module,
        "rebuild_academic_catalog",
        real_rebuild,
    )
    recovered = publish_concord_academic_results(
        request,
        workspace_root=root,
        clock=lambda: _clock(15),
    )
    assert recovered.disposition == "existing"
    assert recovered.publication == state.publication
    assert recovered.manifest_generation.disposition == "existing"
    assert recovered.catalog.publication.is_current_selectable
    final_state = load_concord_publication_series_status(
        "class-1",
        "activity-1",
        workspace_root=root,
    )
    assert len(final_state.publications) == 1
    assert final_state.catalog_available
