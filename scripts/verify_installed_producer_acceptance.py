"""Installed clean-wheel producer acceptance for Concord academic results."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Literal, TypeVar

import pds_core
import pypdfium2
from pds_core.academic_catalog import (
    CatalogPublication,
    PublicationCatalogQuery,
    query_publication_catalog,
    rebuild_academic_catalog,
)
from pds_core.academic_work_registration_storage import (
    load_academic_work_registration_revision,
    load_current_academic_work_registration,
)
from pds_core.academic_work_registrations import AcademicWorkRegistration
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.classes import write_class_roster
from pds_core.module_profiles import discover_module_profiles
from pds_core.publication_compatibility import (
    discover_publication_producer_profiles,
    evaluate_publication_compatibility,
)
from pds_core.publication_records import (
    PublicationCapability,
    validate_publication_record_series,
)
from pds_core.publication_storage import (
    get_current_publication_record,
    list_publication_record_set,
    load_publication_record,
    load_publication_withdrawal,
    verify_publication_manifest,
)
from pds_core.registry_audit import RegistryAuditOptions, audit_academic_registry
from pds_core.registry_paths import (
    academic_work_registration_revision_path,
    publication_record_path,
    publication_withdrawal_path,
)
from pds_core.rosters import create_roster
from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import (
    StandardDefinition,
    StandardsLibrary,
    StandardsProfile,
    write_workspace_standards_library,
)
from pds_core.workspace import ensure_workspace_root
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.utils import canonicalize_name
from pip._vendor.packaging.version import Version

from concord.academic_result_artifacts import (
    AcademicResultArtifactAuthorizationDecision,
    AcademicResultArtifactAuthorizationRequest,
    read_authorized_academic_result_artifact,
)
from concord.academic_result_manifest import (
    AcademicResultManifest,
    TargetReferenceProjection,
    derive_manifest_capabilities,
)
from concord.academic_result_manifest_generation import (
    AcademicResultManifestGenerationResult,
    GenerateAcademicResultManifestRequest,
    generate_academic_result_manifest,
    list_academic_result_manifest_revisions,
)
from concord.academic_result_publication import (
    AcademicResultPublicationResult,
    AcademicResultWithdrawalResult,
    publish_concord_academic_results,
    supersede_concord_academic_results,
    withdraw_concord_academic_result_publication,
)
from concord.academic_result_reader import (
    list_academic_result_score_evidence_links,
    list_academic_result_scores_for_target,
    lookup_academic_result_moderation,
    lookup_academic_result_score,
    lookup_academic_result_score_evidence_link,
    read_academic_result_manifest,
)
from concord.academic_work_registration import (
    list_concord_academic_work_registration_revisions,
    load_current_concord_academic_work_registration,
    register_concord_academic_work,
)
from concord.models import (
    EffectiveContext,
    EvidenceReference,
    ParticipantReference,
    PrivacyPolicy,
    ScoreTargetReference,
    ScoringScaleLevel,
    StatusReason,
    SubjectReference,
)
from concord.pds_contract import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)
from concord.pds_module import get_module_profile
from concord.pds_publication import get_publication_producer_profile
from concord.routing.rendering import RenderArtifactPagesRequest, render_artifact_pages
from concord.routing.scan_intake import route_scan_sources
from concord.storage import (
    list_record_revisions,
    load_current_record_graph,
    load_record_graph_at_snapshot,
)
from concord.workflows import (
    AddArtifactAuthorRequest,
    AddArtifactReviewRequest,
    AddArtifactSubjectRequest,
    AddMembershipsRequest,
    AddModerationRecordRequest,
    AddScoreRequest,
    AssembleArtifactRequest,
    CreateActivityContextRequest,
    CreateCriterionSetRequest,
    CreateGroupRequest,
    CreateScoringScaleRequest,
    CriterionSpec,
    GroupMemberSpec,
    ReplaceScoreRequest,
    ScoreEvidenceLinkSpec,
    SelectActivityCriterionSetsRequest,
    UpdateSessionRequest,
    WorkflowActor,
    add_artifact_author,
    add_artifact_review,
    add_artifact_subject,
    add_memberships,
    add_moderation_record,
    add_score,
    assemble_returned_artifact,
    create_activity_context,
    create_criterion_set,
    create_group,
    create_scoring_scale,
    list_current_score_heads,
    replace_score,
    select_activity_criterion_sets,
    update_session,
)
from concord.workflows.artifact_page import (
    ArtifactPagePlan,
    PrepareArtifactPagesRequest,
    prepare_artifact_pages,
)
from concord.workflows.context import actor_reference

CLASS_ID = "acceptance_class"
ACTIVITY_ID = "acceptance_activity"
ACTIVITY_TITLE = "Synthetic collaborative acceptance activity"
SESSION_ID = "acceptance_session"
GROUP_ID = "acceptance_group"
STUDENT_1 = "synthetic_student_1"
STUDENT_2 = "synthetic_student_2"
STANDARD_ID = "acceptance_standard"
PROFILE_ID = "acceptance_profile"
ARTIFACT_ID = "acceptance_artifact"
ARTIFACT_PAGE_ID = "acceptance_artifact_page"
EVIDENCE_LINK_ID = "acceptance_evidence_link"
GROUP_SCORE_1 = "acceptance_group_score_1"
GROUP_SCORE_2 = "acceptance_group_score_2"
STUDENT_SCORE = "acceptance_student_score"
NON_SCORE = "acceptance_non_score"
PURPOSE = "installed producer acceptance"
CAPABILITIES: tuple[PublicationCapability, ...] = (
    "criterion_scores",
    "moderated_scores",
    "standards_ratings",
)
MANIFEST_CAPABILITIES: tuple[PublicationCapability, ...] = (
    "criterion_scores",
    "standards_ratings",
    "moderated_scores",
)
ScoreTargetIdentity = tuple[str, str, str]
ScorePopulationEntry = tuple[str, ScoreTargetIdentity]
REVISION_ONE_SCORE_POPULATION: tuple[ScorePopulationEntry, ...] = (
    (GROUP_SCORE_1, ("concord_group", GROUP_ID, "concord")),
    (STUDENT_SCORE, ("core_student", STUDENT_2, "core")),
    (NON_SCORE, ("core_student", STUDENT_1, "core")),
)
REVISION_TWO_SCORE_POPULATION: tuple[ScorePopulationEntry, ...] = (
    *REVISION_ONE_SCORE_POPULATION,
    (GROUP_SCORE_2, ("concord_group", GROUP_ID, "concord")),
)
REVISION_TWO_CURRENT_SCORE_POPULATION: tuple[ScorePopulationEntry, ...] = (
    (GROUP_SCORE_2, ("concord_group", GROUP_ID, "concord")),
    (STUDENT_SCORE, ("core_student", STUDENT_2, "core")),
    (NON_SCORE, ("core_student", STUDENT_1, "core")),
)

STAGES = (
    "installed provenance",
    "synthetic native workflow",
    "academic-work registration",
    "manifest revision 1",
    "public reader revision 1",
    "initial publication",
    "publication replay",
    "catalog revision 1",
    "Core verification revision 1",
    "authorized artifact revision 1",
    "native correction",
    "manifest revision 2",
    "supersession",
    "catalog revision 2",
    "Core verification revision 2",
    "historical artifact",
    "withdrawal",
    "final catalog",
    "registry audit",
    "immutability",
)

_T = TypeVar("_T")
CatalogState = Literal["current", "series_heads", "historical", "withdrawn", "all"]


class AcceptanceFailure(RuntimeError):
    """Bounded stage-specific failure without private native payload rendering."""

    def __init__(self, stage: str, message: str) -> None:
        if stage not in STAGES:
            raise ValueError("stage must be a known producer-acceptance stage.")
        if not message or "\n" in message or "\r" in message:
            raise ValueError("message must be a nonempty single line.")
        super().__init__(f"{stage}: {message}")
        self.stage = stage
        self.message = message


def _require(condition: bool, stage: str, message: str) -> None:
    if not condition:
        raise AcceptanceFailure(stage, message)


def _require_exact_score_population(
    actual: Iterable[ScorePopulationEntry],
    expected: tuple[ScorePopulationEntry, ...],
    *,
    stage: str,
) -> None:
    items = tuple(actual)
    actual_by_id = dict(items)
    expected_by_id = dict(expected)
    _require(
        len(items) == len(actual_by_id) == len(expected_by_id)
        and actual_by_id == expected_by_id,
        stage,
        "Score population contains an unexpected, missing, duplicate, or inferred "
        "Score target.",
    )


def _run_stage(stage: str, action: Callable[[], _T]) -> _T:
    print(f"Running: {stage}", flush=True)
    try:
        result = action()
    except AcceptanceFailure:
        raise
    except Exception as error:
        raise AcceptanceFailure(
            stage, f"production operation failed ({type(error).__name__})."
        ) from error
    print(f"PASSED: {stage}", flush=True)
    return result


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _module_origin(name: str) -> Path:
    module = importlib.import_module(name)
    origin = getattr(module, "__file__", None)
    if not isinstance(origin, str) or not origin:
        raise ValueError("installed module has no file origin")
    return Path(origin).resolve()


def _installed_origin(path: Path, repository: Path) -> bool:
    prefix = Path(sys.prefix).resolve()
    resolved = path.resolve()
    return (
        resolved.is_relative_to(prefix)
        and "site-packages" in {part.lower() for part in resolved.parts}
        and not resolved.is_relative_to(repository)
    )


def _package_bytes() -> dict[str, str]:
    root = _module_origin("concord").parent
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
    }


def _actor() -> WorkflowActor:
    return WorkflowActor(
        actor_id="synthetic_teacher",
        display_label="Synthetic Teacher",
        role_label="teacher",
    )


def _student_subject(student_id: str = STUDENT_2) -> SubjectReference:
    return SubjectReference(
        subject_kind="core_student",
        subject_id=student_id,
        owning_system="core",
    )


def _work() -> ModuleWorkRef:
    return ModuleWorkRef(CONCORD_MODULE_ID, CLASS_ID, ACTIVITY_ID)


def _standards() -> StandardsLibrary:
    return StandardsLibrary(
        standards=(
            StandardDefinition(
                standard_id=STANDARD_ID,
                code="SYN.ACCEPT.1",
                source="synthetic",
                short_name="Synthetic acceptance standard",
                description="Synthetic standard used only for installed acceptance.",
                available_modules=(CONCORD_MODULE_ID,),
            ),
        ),
        profiles=(
            StandardsProfile(
                profile_id=PROFILE_ID,
                standards=(STANDARD_ID,),
                title="Synthetic acceptance profile",
            ),
        ),
    )


def _evidence() -> EvidenceReference:
    return EvidenceReference(
        evidence_kind="artifact_instance",
        owning_system=CONCORD_MODULE_ID,
        record_id=ARTIFACT_ID,
        moderation_requirement="not_required",
    )


@dataclass(frozen=True, slots=True)
class NativeState:
    standards: StandardsLibrary
    snapshot_revision: int
    retained_path: Path
    retained_bytes: bytes


@dataclass(frozen=True, slots=True)
class _ExactAuthorizationGate:
    expected_request: AcademicResultArtifactAuthorizationRequest

    def authorize(
        self, request: AcademicResultArtifactAuthorizationRequest
    ) -> AcademicResultArtifactAuthorizationDecision:
        return AcademicResultArtifactAuthorizationDecision(
            "allowed" if request == self.expected_request else "denied"
        )


def _artifact_authorization_request(
    manifest: AcademicResultManifest,
    score_evidence_link_id: str,
    *,
    purpose: str,
) -> AcademicResultArtifactAuthorizationRequest:
    link = lookup_academic_result_score_evidence_link(
        manifest, score_evidence_link_id
    )
    return AcademicResultArtifactAuthorizationRequest(
        work=manifest.work,
        record_set_id=manifest.record_set.record_set_id,
        record_set_revision=manifest.record_set.revision,
        source_snapshot_revision=manifest.projection.source_snapshot_revision,
        score_record_id=link.score_record_id,
        score_evidence_link_id=link.score_evidence_link_id,
        evidence_reference=link.evidence_reference,
        purpose=purpose,
    )


def _installed_provenance(
    workspace: Path, repository: Path, *, version: str, core_version: str
) -> None:
    _require(
        workspace.is_dir() and not any(workspace.iterdir()),
        "installed provenance",
        "workspace must begin empty.",
    )
    _require(
        metadata.version("pds-concord") == version,
        "installed provenance",
        "installed Concord metadata version disagrees.",
    )
    _require(
        metadata.version("pds-core") == core_version == "0.6.0",
        "installed provenance",
        "installed Core version is not exactly 0.6.0.",
    )
    _require(
        getattr(pds_core, "__version__", None) == core_version,
        "installed provenance",
        "Core module and distribution versions disagree.",
    )
    requirements = tuple(
        Requirement(item) for item in (metadata.requires("pds-concord") or ())
    )
    core_requirements = tuple(
        item for item in requirements if canonicalize_name(item.name) == "pds-core"
    )
    _require(
        len(core_requirements) == 1
        and Version(core_version) in core_requirements[0].specifier,
        "installed provenance",
        "Concord dependency metadata rejects Core 0.6.0.",
    )
    modules = (
        "concord",
        "concord.academic_work_registration",
        "concord.academic_result_manifest",
        "concord.academic_result_manifest_generation",
        "concord.academic_result_publication",
        "concord.academic_result_reader",
        "concord.academic_result_artifacts",
        "concord.pds_module",
        "concord.pds_publication",
        "pds_core",
        "pds_core.academic_work_registration_storage",
        "pds_core.publication_storage",
        "pds_core.publication_compatibility",
        "pds_core.academic_catalog",
        "pds_core.registry_audit",
    )
    for name in modules:
        _require(
            _installed_origin(_module_origin(name), repository),
            "installed provenance",
            f"{name} did not import from isolated site-packages.",
        )
    routing = tuple(
        item
        for item in discover_module_profiles()
        if item.module_id == CONCORD_MODULE_ID
    )
    producers = tuple(
        item
        for item in discover_publication_producer_profiles()
        if item.module_id == CONCORD_MODULE_ID
    )
    routing_entries = tuple(
        item
        for item in metadata.entry_points(group="paper_data_suite.modules")
        if item.name == CONCORD_MODULE_ID
    )
    producer_entries = tuple(
        item
        for item in metadata.entry_points(
            group="paper_data_suite.publication_producers"
        )
        if item.name == CONCORD_MODULE_ID
    )
    _require(
        routing == (get_module_profile(),),
        "installed provenance",
        "Concord routing entry point did not resolve exactly once.",
    )
    _require(
        producers == (get_publication_producer_profile(),),
        "installed provenance",
        "Concord producer entry point did not resolve exactly once.",
    )
    _require(
        len(routing_entries) == 1
        and routing_entries[0].load() is get_module_profile
        and len(producer_entries) == 1
        and producer_entries[0].load() is get_publication_producer_profile,
        "installed provenance",
        "installed entry points do not target the production profile functions.",
    )
    forbidden = {"scoreform", "quillan", "portia", "meridian", "vitrine"}
    loaded = {name.split(".", 1)[0].lower() for name in sys.modules}
    _require(
        forbidden.isdisjoint(loaded),
        "installed provenance",
        "a sibling producer or consumer was imported.",
    )


def _native_workflow(workspace: Path) -> NativeState:
    stage = "synthetic native workflow"
    root = ensure_workspace_root(workspace)
    write_class_metadata_for_class(
        root,
        create_class_metadata(
            CLASS_ID,
            "2026-2027",
            created_at=datetime(2026, 8, 16, tzinfo=timezone.utc),
        ),
    )
    write_class_roster(
        root,
        create_roster(
            CLASS_ID,
            (
                {
                    "student_id": STUDENT_1,
                    "last_name": "Synthetic",
                    "first_name": "One",
                    "period": "acceptance",
                },
                {
                    "student_id": STUDENT_2,
                    "last_name": "Synthetic",
                    "first_name": "Two",
                    "period": "acceptance",
                },
            ),
        ),
    )
    standards = _standards()
    write_workspace_standards_library(root, standards)
    created = create_activity_context(
        CreateActivityContextRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            title=ACTIVITY_TITLE,
            activity_type="project",
            scoring_orientation="mixed",
            standards_profile_id=PROFILE_ID,
            focus_standard_ids=(STANDARD_ID,),
            session_id=SESSION_ID,
            actor=_actor(),
            activity_status="active",
            session_status="active",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    group = create_group(
        CreateGroupRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_id=GROUP_ID,
            label="Synthetic acceptance group",
            status="active",
            expected_snapshot_revision=created.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    memberships = add_memberships(
        AddMembershipsRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            group_id=GROUP_ID,
            members=tuple(
                GroupMemberSpec(
                    membership_id=f"acceptance_membership_{index}",
                    student_id=student,
                    effective_context=EffectiveContext(
                        activity_id=ACTIVITY_ID,
                        session_ids=(SESSION_ID,),
                    ),
                )
                for index, student in enumerate((STUDENT_1, STUDENT_2), 1)
            ),
            expected_snapshot_revision=group.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    prepared = prepare_artifact_pages(
        PrepareArtifactPagesRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            template_version_id="acceptance_template",
            artifact_category="observation",
            expected_snapshot_revision=memberships.commit.snapshot_revision,
            actor=_actor(),
            pages=(ArtifactPagePlan(page_number=1, artifact_page_id=ARTIFACT_PAGE_ID),),
            session_id=SESSION_ID,
            group_id=GROUP_ID,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    rendered = render_artifact_pages(
        RenderArtifactPagesRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            expected_snapshot_revision=prepared.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    routed = route_scan_sources((rendered.output_path,), workspace_root=root)
    _require(
        routed.dispatched_count == 1 and routed.failure_count == 0,
        stage,
        "PDS2 route/intake did not return exactly one page.",
    )
    loaded = load_current_record_graph(root, _work(), standards_library=standards)
    _require(
        loaded.graph.artifact_pages[0].page_status == "returned"
        and loaded.graph.artifact_instances[0].artifact_status == "returned",
        stage,
        "routed Artifact Page or Instance is not returned.",
    )
    assembled = assemble_returned_artifact(
        AssembleArtifactRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
    )
    _require(
        assembled.output_path.is_file() and assembled.manifest_path.is_file(),
        stage,
        "returned Artifact assembly did not create its bounded outputs.",
    )
    author = add_artifact_author(
        AddArtifactAuthorRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            artifact_author_id="acceptance_author",
            author_reference=ParticipantReference(
                participant_kind="core_student",
                participant_id=STUDENT_1,
                owning_system="core",
            ),
            authorship_mode="observer",
            attribution_status="confirmed",
            attribution_source="teacher",
            expected_snapshot_revision=loaded.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    subject = add_artifact_subject(
        AddArtifactSubjectRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            artifact_subject_id="acceptance_subject",
            subject_reference=_student_subject(),
            subject_role="observed_participant",
            confirmation_status="confirmed",
            assignment_source="teacher",
            expected_snapshot_revision=author.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    review = add_artifact_review(
        AddArtifactReviewRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            artifact_instance_id=ARTIFACT_ID,
            artifact_review_id="acceptance_review",
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
            notes="Synthetic private review note.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=subject.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    moderation = add_moderation_record(
        AddModerationRecordRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            moderation_record_id="acceptance_moderation",
            target_evidence_reference=_evidence(),
            target_subject_references=(_student_subject(),),
            status="accepted_with_qualification",
            permitted_use="support_named_subject",
            rationale="Synthetic private moderation rationale.",
            qualification="Synthetic use only for the named subject.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=review.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    scale = create_scoring_scale(
        CreateScoringScaleRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            scoring_scale_id="acceptance_scale",
            lineage_id="acceptance_scale_lineage",
            name="Synthetic acceptance scale",
            revision=1,
            scale_type="ordinal",
            levels=tuple(
                ScoringScaleLevel(
                    value=value,
                    label=label,
                    meaning=f"Synthetic {label.lower()} evidence.",
                    position=value,
                )
                for value, label in ((1, "Beginning"), (2, "Developing"), (3, "Secure"))
            ),
            status="active",
            expected_snapshot_revision=moderation.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    criteria = create_criterion_set(
        CreateCriterionSetRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            criterion_set_id="acceptance_criteria",
            lineage_id="acceptance_criteria_lineage",
            name="Synthetic acceptance criteria",
            purpose="Exercise local and standard-backed installed production.",
            revision=1,
            scope="activity_specific",
            criterion_set_kind="mixed",
            criteria=(
                CriterionSpec(
                    criterion_id="acceptance_group_criterion",
                    key="collaboration",
                    label="Collaboration",
                    definition="Synthetic group collaboration evidence.",
                    criterion_kind="local",
                    supported_target_kinds=("concord_group",),
                    default_scoring_scale_id="acceptance_scale",
                ),
                CriterionSpec(
                    criterion_id="acceptance_standard_criterion",
                    key="reasoning",
                    label="Reasoning",
                    definition="Synthetic standard-backed reasoning evidence.",
                    criterion_kind="standard_backed",
                    standard_id=STANDARD_ID,
                    supported_target_kinds=("core_student",),
                    default_scoring_scale_id="acceptance_scale",
                ),
            ),
            status="active",
            standards_profile_id=PROFILE_ID,
            expected_snapshot_revision=scale.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    selected = select_activity_criterion_sets(
        SelectActivityCriterionSetsRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            criterion_set_ids=("acceptance_criteria",),
            expected_snapshot_revision=criteria.commit.snapshot_revision,
            actor=_actor(),
        ),
        workspace_root=root,
        standards_library=standards,
    )
    group_score = add_score(
        AddScoreRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            score_record_id=GROUP_SCORE_1,
            target_reference=ScoreTargetReference(
                target_kind="concord_group",
                target_id=GROUP_ID,
                owning_system="concord",
            ),
            criterion_id="acceptance_group_criterion",
            scoring_scale_id="acceptance_scale",
            disposition="scored",
            value=2,
            basis="professional_judgment",
            rationale="Synthetic private group Score rationale.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=selected.commit.snapshot_revision,
            actor=_actor(),
            session_id=SESSION_ID,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    student_score = add_score(
        AddScoreRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            score_record_id=STUDENT_SCORE,
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id=STUDENT_2,
                owning_system="core",
            ),
            criterion_id="acceptance_standard_criterion",
            scoring_scale_id="acceptance_scale",
            disposition="scored",
            value=3,
            basis="linked_evidence",
            evidence_links=(
                ScoreEvidenceLinkSpec(
                    score_evidence_link_id=EVIDENCE_LINK_ID,
                    evidence_reference=_evidence(),
                    relevance_description=(
                        "Synthetic represented Artifact supports reasoning."
                    ),
                    subject_context=(_student_subject(),),
                    significance="primary",
                    moderation_record_id="acceptance_moderation",
                ),
            ),
            rationale="Synthetic private student Score rationale.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=group_score.commit.snapshot_revision,
            actor=_actor(),
            session_id=SESSION_ID,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    reason = StatusReason(
        reason_code="absent",
        recorded_by=actor_reference(_actor()),
        recorded_at=datetime(2026, 8, 16, 18, 0, tzinfo=timezone.utc).isoformat(),
        note="Synthetic private non-score note.",
    )
    non_score = add_score(
        AddScoreRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            score_record_id=NON_SCORE,
            target_reference=ScoreTargetReference(
                target_kind="core_student",
                target_id=STUDENT_1,
                owning_system="core",
            ),
            criterion_id="acceptance_standard_criterion",
            scoring_scale_id="acceptance_scale",
            disposition="absent",
            basis="professional_judgment",
            rationale="Synthetic private non-score rationale.",
            status_reason=reason,
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=student_score.commit.snapshot_revision,
            actor=_actor(),
            session_id=SESSION_ID,
        ),
        workspace_root=root,
        standards_library=standards,
    )
    graph = load_current_record_graph(root, _work(), standards_library=standards).graph
    scores = {item.score_record_id: item for item in graph.score_records}
    _require_exact_score_population(
        (
            (
                item.score_record_id,
                (
                    item.target_reference.target_kind,
                    item.target_reference.target_id,
                    item.target_reference.owning_system,
                ),
            )
            for item in graph.score_records
        ),
        REVISION_ONE_SCORE_POPULATION,
        stage=stage,
    )
    _require(
        len(graph.memberships) == 2
        and graph.artifact_authors[0].author_reference is not None
        and graph.artifact_authors[0].author_reference.participant_id == STUDENT_1
        and graph.artifact_subjects[0].subject_reference.subject_id == STUDENT_2
        and STUDENT_1 != STUDENT_2
        and scores[GROUP_SCORE_1].target_reference.target_kind == "concord_group"
        and scores[GROUP_SCORE_1].target_reference.target_id == GROUP_ID
        and scores[STUDENT_SCORE].target_reference.target_id == STUDENT_2
        and scores[NON_SCORE].value is None
        and scores[NON_SCORE].disposition == "absent"
        and all(
            item.supersedes_score_record_id is None for item in graph.score_records
        ),
        stage,
        "native collaboration, attribution, or Score distinctions collapsed.",
    )
    registry = root / "registry"
    _require(
        not (registry / "work").exists()
        and not (registry / "publications").exists()
        and not (registry / "withdrawals").exists()
        and not (registry / "catalog.sqlite").exists(),
        stage,
        "native workflow implicitly created academic registry state.",
    )
    scan = graph.scan_references[0]
    retained = root.joinpath(*scan.retained_source_relative_path.split("/"))
    content = retained.read_bytes()
    _require(
        _sha256(content) == scan.retained_source_sha256,
        stage,
        "retained source digest disagrees.",
    )
    _require(
        list_record_revisions(root, _work(), "session", SESSION_ID) == (1,),
        stage,
        "unexpected Session history exists before operational drift.",
    )
    return NativeState(standards, non_score.commit.snapshot_revision, retained, content)


def _register(workspace: Path) -> tuple[AcademicWorkRegistration, bytes]:
    result = register_concord_academic_work(
        workspace,
        CLASS_ID,
        ACTIVITY_ID,
        academic_intent="summative",
        lifecycle="active",
    )
    replay = register_concord_academic_work(
        workspace,
        CLASS_ID,
        ACTIVITY_ID,
        academic_intent="summative",
        lifecycle="active",
    )
    current = load_current_concord_academic_work_registration(
        workspace, CLASS_ID, ACTIVITY_ID
    )
    core_current = load_current_academic_work_registration(workspace, _work())
    registration = result.registration
    expected_source = ModuleRecordRef(
        module_id=CONCORD_MODULE_ID,
        record_kind=CONCORD_ACTIVITY_RECORD_KIND,
        record_id=ACTIVITY_ID,
        contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
    )
    _require(
        result.disposition == "created"
        and replay.disposition == "existing"
        and replay.registration == registration
        and current == registration
        and core_current == registration
        and registration.work == _work()
        and registration.registration_revision == 1
        and registration.producer_contract_version
        == CONCORD_ACADEMIC_WORK_CONTRACT_VERSION
        and registration.work_kind == CONCORD_ACADEMIC_WORK_KIND
        and registration.title == ACTIVITY_TITLE
        and registration.academic_intent == "summative"
        and registration.lifecycle == "active"
        and registration.source_records == (expected_source,)
        and list_concord_academic_work_registration_revisions(
            workspace, CLASS_ID, ACTIVITY_ID
        )
        == (1,),
        "academic-work registration",
        "explicit registration revision 1 or exact replay disagrees.",
    )
    path = academic_work_registration_revision_path(workspace, _work(), 1)
    return registration, path.read_bytes()


def _request(
    revision: int, reason: Literal["initial", "native_state_change"]
) -> GenerateAcademicResultManifestRequest:
    return GenerateAcademicResultManifestRequest(
        class_id=CLASS_ID,
        activity_id=ACTIVITY_ID,
        expected_snapshot_revision=revision,
        actor=_actor(),
        revision_reason=reason,
    )


def _generate_one(
    workspace: Path, native: NativeState
) -> AcademicResultManifestGenerationResult:
    result = generate_academic_result_manifest(
        _request(native.snapshot_revision, "initial"),
        workspace_root=workspace,
        standards_library=native.standards,
    )
    private = (
        b"private group",
        b"private student",
        b"private non-score",
        b"private moderation",
        b"private review",
    )
    _require(
        result.disposition == "created"
        and result.revision == 1
        and result.registration_revision == 1
        and result.source_snapshot_revision == native.snapshot_revision
        and result.path.read_bytes() == result.content
        and result.sha256 == _sha256(result.content)
        and derive_manifest_capabilities(result.manifest) == MANIFEST_CAPABILITIES
        and all(value not in result.content.lower() for value in private),
        "manifest revision 1",
        "initial immutable public projection or privacy boundary disagrees.",
    )
    return result


def _verify_reader(
    manifest: AcademicResultManifest, *, revision: int, stage: str
) -> None:
    expected_population = (
        REVISION_ONE_SCORE_POPULATION
        if revision == 1
        else REVISION_TWO_SCORE_POPULATION
    )
    _require_exact_score_population(
        (
            (
                item.score_record_id,
                (
                    item.target_reference.target_kind,
                    item.target_reference.target_id,
                    item.target_reference.owning_system,
                ),
            )
            for item in manifest.scores
        ),
        expected_population,
        stage=stage,
    )
    scores = {item.score_record_id: item for item in manifest.scores}
    group_scores = list_academic_result_scores_for_target(
        manifest,
        TargetReferenceProjection("concord_group", GROUP_ID, "concord", None),
    )
    student_scores = list_academic_result_scores_for_target(
        manifest,
        TargetReferenceProjection("core_student", STUDENT_2, "core", None),
    )
    non_score = lookup_academic_result_score(manifest, NON_SCORE)
    evidence = list_academic_result_score_evidence_links(manifest, STUDENT_SCORE)
    moderation = lookup_academic_result_moderation(manifest, "acceptance_moderation")
    expected_group = GROUP_SCORE_1 if revision == 1 else GROUP_SCORE_2
    _require(
        manifest.record_set.revision == revision
        and any(
            item.score_record_id == expected_group and item.current_state == "current"
            for item in group_scores
        )
        and any(
            item.score_record_id == STUDENT_SCORE and item.standard_id == STANDARD_ID
            for item in student_scores
        )
        and non_score.value is None
        and non_score.disposition == "absent"
        and len(evidence) == 1
        and evidence[0].moderation_record_id == "acceptance_moderation"
        and moderation.permitted_use == "support_named_subject"
        and scores[STUDENT_SCORE].current_state == "current"
        and scores[STUDENT_SCORE].supersedes_score_record_id is None
        and scores[NON_SCORE].current_state == "current"
        and scores[NON_SCORE].supersedes_score_record_id is None,
        stage,
        "public reader did not preserve Score, non-score, standard, or "
        "Moderation semantics.",
    )
    if revision == 1:
        _require(
            scores[GROUP_SCORE_1].current_state == "current"
            and scores[GROUP_SCORE_1].supersedes_score_record_id is None,
            stage,
            "revision-1 Score current-state history disagrees.",
        )
    else:
        predecessor = lookup_academic_result_score(manifest, GROUP_SCORE_1)
        successor = lookup_academic_result_score(manifest, GROUP_SCORE_2)
        _require(
            predecessor.current_state == "superseded"
            and predecessor.supersedes_score_record_id is None
            and successor.current_state == "current"
            and successor.supersedes_score_record_id == GROUP_SCORE_1,
            stage,
            "reader did not preserve native Score history.",
        )


def _read_generated(
    content: bytes, *, revision: int, stage: str
) -> AcademicResultManifest:
    manifest = read_academic_result_manifest(content)
    _verify_reader(manifest, revision=revision, stage=stage)
    return manifest


def _verify_publication(
    workspace: Path,
    result: AcademicResultPublicationResult,
    generated: AcademicResultManifestGenerationResult,
    *,
    revision: int,
    supersedes: str | None,
    stage: str,
) -> None:
    publication = result.publication
    canonical = load_publication_record(workspace, publication.publication_id)
    expected_source = ModuleRecordRef(
        module_id=CONCORD_MODULE_ID,
        record_kind=CONCORD_ACTIVITY_RECORD_KIND,
        record_id=ACTIVITY_ID,
        contract_version=CONCORD_ACTIVITY_CONTRACT_VERSION,
    )
    _require(
        canonical == publication
        and publication.work == _work()
        and publication.source_record == expected_source
        and publication.publication_kind == "academic_result_set"
        and tuple(publication.capabilities) == CAPABILITIES
        and publication.record_set_id == CONCORD_ACADEMIC_RESULT_RECORD_SET_ID
        and publication.record_set_revision == revision
        and publication.manifest_contract_version
        == ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION
        and publication.manifest_path == generated.relative_path
        and publication.manifest_digest_algorithm == "sha256"
        and publication.manifest_digest == generated.sha256
        and publication.academic_work_registration_revision == 1
        and publication.supersedes_publication_id == supersedes
        and result.registration.registration_revision == 1,
        stage,
        "Core Publication Record envelope disagrees with the producer manifest.",
    )


def _query(workspace: Path, state: CatalogState) -> tuple[CatalogPublication, ...]:
    return query_publication_catalog(
        workspace,
        PublicationCatalogQuery(
            class_id=CLASS_ID,
            module_id=CONCORD_MODULE_ID,
            work_id=ACTIVITY_ID,
            publication_kind="academic_result_set",
            required_capabilities=CAPABILITIES,
            manifest_contract_version=ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
            record_set_id=CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
            state=state,
        ),
    )


def _core_verified(
    workspace: Path,
    publication_id: str,
    generated: AcademicResultManifestGenerationResult,
    *,
    stage: str,
) -> bytes:
    publication = load_publication_record(workspace, publication_id)
    registration_revision = publication.academic_work_registration_revision
    if registration_revision is None:
        raise AcceptanceFailure(stage, "publication omitted registration revision.")
    registration = load_academic_work_registration_revision(
        workspace,
        publication.work,
        registration_revision,
    )
    series = list_publication_record_set(
        workspace,
        publication.work,
        publication.publication_kind,
        publication.record_set_id,
    )
    validate_publication_record_series(series)
    compatibility = evaluate_publication_compatibility(
        publication, get_publication_producer_profile(), registration
    )
    path = verify_publication_manifest(workspace, publication)
    content = path.read_bytes()
    _require(
        len(series) == generated.revision
        and compatibility.compatible
        and compatibility.codes == ()
        and load_publication_withdrawal(workspace, publication_id) is None
        and path.resolve(strict=True) == generated.path.resolve(strict=True)
        and content == generated.content
        and _sha256(content) == publication.manifest_digest,
        stage,
        "canonical reload, compatibility, path containment, or SHA-256 "
        "verification disagrees.",
    )
    return content


def _authorized_artifact(
    workspace: Path,
    manifest: AcademicResultManifest,
    *,
    retained_source_bytes: bytes,
    stage: str,
) -> bytes:
    expected_request = _artifact_authorization_request(
        manifest,
        EVIDENCE_LINK_ID,
        purpose=PURPOSE,
    )
    result = read_authorized_academic_result_artifact(
        workspace,
        manifest,
        EVIDENCE_LINK_ID,
        purpose=PURPOSE,
        authorization_gate=_ExactAuthorizationGate(expected_request),
    )
    projections: tuple[object, ...] = (
        result.artifact,
        *result.artifact.pages,
        *result.authors,
        *result.subjects,
    )
    private_source_fields = (
        "retained_source_relative_path",
        "retained_source_path",
        "retained_source_sha256",
        "scan_reference_id",
        "source_scan_id",
        "source_scan_reference_id",
        "source_filename",
        "route_id",
        "route_target",
        "route_metadata",
        "route_payload",
        "human_fallback",
        "human_fallback_text",
    )
    _require(
        result.representation == "returned_artifact_pdf"
        and result.work == expected_request.work
        and result.record_set_revision == expected_request.record_set_revision
        and result.source_snapshot_revision
        == expected_request.source_snapshot_revision
        and result.score_record_id == expected_request.score_record_id
        and result.score_evidence_link_id
        == expected_request.score_evidence_link_id
        and result.evidence_reference == expected_request.evidence_reference
        and result.media_type == "application/pdf"
        and result.content.startswith(b"%PDF")
        and result.byte_size == len(result.content)
        and result.sha256 == _sha256(result.content)
        and result.content != retained_source_bytes
        and _pdf_page_count(result.content) == 1
        and result.artifact.artifact_instance_id == ARTIFACT_ID
        and result.artifact.session_id == SESSION_ID
        and result.artifact.group_id == GROUP_ID
        and len(result.artifact.pages) == 1
        and result.artifact.pages[0].artifact_page_id == ARTIFACT_PAGE_ID
        and result.artifact.pages[0].page_number == 1
        and len(result.authors) == 1
        and len(result.subjects) == 1
        and result.authors[0].author_reference is not None
        and getattr(result.authors[0].author_reference, "participant_id", None)
        == STUDENT_1
        and result.subjects[0].subject_reference.subject_id == STUDENT_2
        and STUDENT_1 != STUDENT_2
        and all(
            not hasattr(projection, field)
            for projection in projections
            for field in private_source_fields
        ),
        stage,
        "authorized bounded Artifact projection or historical snapshot disagrees.",
    )
    return result.content


def _pdf_page_count(content: bytes) -> int:
    document = pypdfium2.PdfDocument(content)
    try:
        return len(document)
    finally:
        document.close()


def _correct(workspace: Path, native: NativeState) -> int:
    result = replace_score(
        ReplaceScoreRequest(
            class_id=CLASS_ID,
            activity_id=ACTIVITY_ID,
            score_record_id=GROUP_SCORE_1,
            replacement_score_record_id=GROUP_SCORE_2,
            correction_id="acceptance_group_correction",
            reason="Synthetic material correction.",
            target_reference=ScoreTargetReference(
                target_kind="concord_group",
                target_id=GROUP_ID,
                owning_system="concord",
            ),
            criterion_id="acceptance_group_criterion",
            scoring_scale_id="acceptance_scale",
            disposition="scored",
            value=3,
            basis="professional_judgment",
            rationale="Synthetic corrected private group rationale.",
            privacy_policy=PrivacyPolicy(classification="teacher_restricted"),
            expected_snapshot_revision=native.snapshot_revision,
            actor=_actor(),
            session_id=SESSION_ID,
        ),
        workspace_root=workspace,
        standards_library=native.standards,
    )
    graph = load_current_record_graph(
        workspace, _work(), standards_library=native.standards
    ).graph
    scores = {item.score_record_id: item for item in graph.score_records}
    _require_exact_score_population(
        (
            (
                item.score_record_id,
                (
                    item.target_reference.target_kind,
                    item.target_reference.target_id,
                    item.target_reference.owning_system,
                ),
            )
            for item in graph.score_records
        ),
        REVISION_TWO_SCORE_POPULATION,
        stage="native correction",
    )
    current = list_current_score_heads(
        CLASS_ID,
        ACTIVITY_ID,
        workspace_root=workspace,
        standards_library=native.standards,
    )
    _require_exact_score_population(
        (
            (
                item.score_record_id,
                (
                    item.target_reference.target_kind,
                    item.target_reference.target_id,
                    item.target_reference.owning_system,
                ),
            )
            for item in current
        ),
        REVISION_TWO_CURRENT_SCORE_POPULATION,
        stage="native correction",
    )
    _require(
        scores[GROUP_SCORE_1].supersedes_score_record_id is None
        and scores[GROUP_SCORE_2].supersedes_score_record_id == GROUP_SCORE_1
        and scores[GROUP_SCORE_2].value == 3,
        "native correction",
        "material replacement did not preserve exact native predecessor history.",
    )
    return result.commit.snapshot_revision


def _audit(workspace: Path) -> None:
    report = audit_academic_registry(
        workspace,
        options=RegistryAuditOptions(
            scopes=(
                "registrations",
                "publications",
                "manifests",
                "contracts",
                "catalog",
                "locks",
            ),
            class_id=CLASS_ID,
            module_id=CONCORD_MODULE_ID,
            work_id=ACTIVITY_ID,
            require_catalog=True,
            require_producer_profiles=True,
            discover_installed_producer_profiles=True,
        ),
    )
    counts = report.counts
    _require(
        report.ok
        and report.canonical_valid
        and report.manifests_valid is True
        and report.contracts_compatible is True
        and report.catalog_ready is True
        and counts.registration_works == 1
        and counts.registration_revisions == 1
        and counts.publication_records == 2
        and counts.publication_series == 1
        and counts.withdrawals == 1
        and counts.verified_manifests == 2
        and counts.error_findings == 0
        and counts.locks == 0,
        "registry audit",
        "Core bounded registry audit did not validate the exact lifecycle.",
    )


def run_acceptance(
    workspace: Path, repository: Path, *, version: str, expected_core_version: str
) -> None:
    workspace = workspace.resolve(strict=True)
    repository = repository.resolve(strict=True)
    package_before = _package_bytes()
    _run_stage(
        "installed provenance",
        lambda: _installed_provenance(
            workspace, repository, version=version, core_version=expected_core_version
        ),
    )
    native = _run_stage(
        "synthetic native workflow", lambda: _native_workflow(workspace)
    )
    registration, registration_bytes = _run_stage(
        "academic-work registration", lambda: _register(workspace)
    )
    manifest_one = _run_stage(
        "manifest revision 1", lambda: _generate_one(workspace, native)
    )
    manifest_one_bytes = bytes(manifest_one.content)
    parsed_one = _run_stage(
        "public reader revision 1",
        lambda: _read_generated(
            manifest_one.content, revision=1, stage="public reader revision 1"
        ),
    )
    published_one = _run_stage(
        "initial publication",
        lambda: publish_concord_academic_results(
            _request(native.snapshot_revision, "initial"),
            workspace_root=workspace,
            standards_library=native.standards,
        ),
    )
    _verify_publication(
        workspace,
        published_one,
        manifest_one,
        revision=1,
        supersedes=None,
        stage="initial publication",
    )
    publication_one_path = publication_record_path(
        workspace, published_one.publication.publication_id
    )
    publication_one_bytes = publication_one_path.read_bytes()

    def replay() -> None:
        result = publish_concord_academic_results(
            _request(native.snapshot_revision, "initial"),
            workspace_root=workspace,
            standards_library=native.standards,
        )
        _require(
            result.disposition == "existing"
            and result.publication == published_one.publication,
            "publication replay",
            "exact replay did not preserve Core publication identity.",
        )

    _run_stage("publication replay", replay)

    def catalog_one() -> None:
        rebuild_academic_catalog(workspace)
        rows = _query(workspace, "all")
        _require(
            len(rows) == 1
            and rows[0].publication_id == published_one.publication.publication_id
            and rows[0].is_series_head
            and rows[0].is_current_selectable
            and not rows[0].is_withdrawn,
            "catalog revision 1",
            "Core catalog revision-1 state disagrees.",
        )

    _run_stage("catalog revision 1", catalog_one)
    verified_one = _run_stage(
        "Core verification revision 1",
        lambda: _core_verified(
            workspace,
            published_one.publication.publication_id,
            manifest_one,
            stage="Core verification revision 1",
        ),
    )
    verified_manifest_one = _read_generated(
        verified_one,
        revision=1,
        stage="Core verification revision 1",
    )
    _require(
        verified_manifest_one == parsed_one,
        "Core verification revision 1",
        "reader semantics changed over Core-verified bytes.",
    )
    workspace_before_read = {
        path.relative_to(workspace).as_posix(): _sha256(path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    }
    _run_stage(
        "authorized artifact revision 1",
        lambda: _authorized_artifact(
            workspace,
            verified_manifest_one,
            retained_source_bytes=native.retained_bytes,
            stage="authorized artifact revision 1",
        ),
    )
    workspace_after_read = {
        path.relative_to(workspace).as_posix(): _sha256(path.read_bytes())
        for path in workspace.rglob("*")
        if path.is_file()
    }
    _require(
        workspace_before_read == workspace_after_read,
        "authorized artifact revision 1",
        "authorized Artifact read mutated workspace state.",
    )
    corrected_revision = _run_stage(
        "native correction", lambda: _correct(workspace, native)
    )

    def generate_two() -> AcademicResultManifestGenerationResult:
        result = generate_academic_result_manifest(
            _request(corrected_revision, "native_state_change"),
            workspace_root=workspace,
            standards_library=native.standards,
        )
        _require(
            result.disposition == "created"
            and result.revision == 2
            and result.sha256 != manifest_one.sha256
            and manifest_one.path.read_bytes() == manifest_one_bytes
            and list_academic_result_manifest_revisions(workspace, _work())[-1].revision
            == 2,
            "manifest revision 2",
            "material correction did not create one immutable successor manifest.",
        )
        _verify_reader(result.manifest, revision=2, stage="manifest revision 2")
        return result

    manifest_two = _run_stage("manifest revision 2", generate_two)
    manifest_two_bytes = bytes(manifest_two.content)
    published_two = _run_stage(
        "supersession",
        lambda: supersede_concord_academic_results(
            _request(corrected_revision, "native_state_change"),
            expected_current_publication_id=published_one.publication.publication_id,
            workspace_root=workspace,
            standards_library=native.standards,
        ),
    )
    _verify_publication(
        workspace,
        published_two,
        manifest_two,
        revision=2,
        supersedes=published_one.publication.publication_id,
        stage="supersession",
    )
    publication_two_path = publication_record_path(
        workspace, published_two.publication.publication_id
    )
    publication_two_bytes = publication_two_path.read_bytes()

    def catalog_two() -> None:
        rebuild_academic_catalog(workspace)
        current, historical, all_rows = (
            _query(workspace, "current"),
            _query(workspace, "historical"),
            _query(workspace, "all"),
        )
        _require(
            len(current) == 1
            and current[0].publication_id == published_two.publication.publication_id
            and len(historical) == 1
            and historical[0].publication_id == published_one.publication.publication_id
            and len(all_rows) == 2,
            "catalog revision 2",
            "Core catalog supersession state disagrees.",
        )

    _run_stage("catalog revision 2", catalog_two)
    verified_two = _run_stage(
        "Core verification revision 2",
        lambda: _core_verified(
            workspace,
            published_two.publication.publication_id,
            manifest_two,
            stage="Core verification revision 2",
        ),
    )
    parsed_two = _read_generated(
        verified_two, revision=2, stage="Core verification revision 2"
    )

    def historical() -> None:
        drift = update_session(
            UpdateSessionRequest(
                class_id=CLASS_ID,
                activity_id=ACTIVITY_ID,
                session_id=SESSION_ID,
                expected_snapshot_revision=corrected_revision,
                actor=_actor(),
                notes="Synthetic unrelated operational drift.",
            ),
            workspace_root=workspace,
            standards_library=native.standards,
        )
        _require(
            drift.commit.snapshot_revision
            > verified_manifest_one.projection.source_snapshot_revision,
            "historical artifact",
            "unrelated native drift did not advance current state.",
        )
        before = {
            path.relative_to(workspace).as_posix(): _sha256(path.read_bytes())
            for path in workspace.rglob("*")
            if path.is_file()
        }
        _authorized_artifact(
            workspace,
            verified_manifest_one,
            retained_source_bytes=native.retained_bytes,
            stage="historical artifact",
        )
        after = {
            path.relative_to(workspace).as_posix(): _sha256(path.read_bytes())
            for path in workspace.rglob("*")
            if path.is_file()
        }
        _require(
            before == after
            and list_academic_result_manifest_revisions(workspace, _work())[-1].revision
            == 2,
            "historical artifact",
            "historical Artifact read fell forward or mutated producer state.",
        )

    _run_stage("historical artifact", historical)

    def withdraw() -> AcademicResultWithdrawalResult:
        result = withdraw_concord_academic_result_publication(
            CLASS_ID,
            ACTIVITY_ID,
            publication_id=published_two.publication.publication_id,
            reason="Synthetic final-head acceptance withdrawal.",
            workspace_root=workspace,
        )
        replay = withdraw_concord_academic_result_publication(
            CLASS_ID,
            ACTIVITY_ID,
            publication_id=published_two.publication.publication_id,
            reason="Synthetic final-head acceptance withdrawal.",
            workspace_root=workspace,
        )
        current = get_current_publication_record(
            workspace,
            _work(),
            "academic_result_set",
            CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
        )
        _require(
            result.disposition == "created"
            and replay.disposition == "existing"
            and replay.withdrawal == result.withdrawal
            and result.manifest_verification == "verified"
            and current is None,
            "withdrawal",
            "final-head withdrawal/replay or non-reactivation boundary disagrees.",
        )
        return result

    withdrawal = _run_stage("withdrawal", withdraw)
    withdrawal_path = publication_withdrawal_path(
        workspace, published_two.publication.publication_id
    )
    withdrawal_bytes = withdrawal_path.read_bytes()

    def final_catalog() -> None:
        rebuild_academic_catalog(workspace)
        current, historical_rows, withdrawn_rows, all_rows = (
            _query(workspace, "current"),
            _query(workspace, "historical"),
            _query(workspace, "withdrawn"),
            _query(workspace, "all"),
        )
        _require(
            current == ()
            and len(historical_rows) == 1
            and historical_rows[0].publication_id
            == published_one.publication.publication_id
            and len(withdrawn_rows) == 1
            and withdrawn_rows[0].publication_id
            == published_two.publication.publication_id
            and len(all_rows) == 2,
            "final catalog",
            "withdrawn final catalog state disagrees with canonical history.",
        )

    _run_stage("final catalog", final_catalog)
    _run_stage("registry audit", lambda: _audit(workspace))

    def immutable() -> None:
        loaded_one = load_record_graph_at_snapshot(
            workspace,
            _work(),
            verified_manifest_one.projection.source_snapshot_revision,
        )
        score_ids = {item.score_record_id for item in loaded_one.graph.score_records}
        _require(
            academic_work_registration_revision_path(workspace, _work(), 1).read_bytes()
            == registration_bytes
            and load_academic_work_registration_revision(workspace, _work(), 1)
            == registration
            and manifest_one.path.read_bytes() == manifest_one_bytes
            and manifest_two.path.read_bytes() == manifest_two_bytes
            and publication_one_path.read_bytes() == publication_one_bytes
            and publication_two_path.read_bytes() == publication_two_bytes
            and withdrawal_path.read_bytes() == withdrawal_bytes
            and load_publication_withdrawal(
                workspace, published_two.publication.publication_id
            )
            == withdrawal.withdrawal
            and native.retained_path.read_bytes() == native.retained_bytes
            and GROUP_SCORE_1 in score_ids
            and STUDENT_SCORE in score_ids
            and any(
                item.moderation_record_id == "acceptance_moderation"
                for item in loaded_one.graph.moderation_records
            )
            and any(
                item.score_evidence_link_id == EVIDENCE_LINK_ID
                for item in loaded_one.graph.score_evidence_links
            )
            and _package_bytes() == package_before,
            "immutability",
            "registration, manifests, publications, retained source, native "
            "history, or installed package bytes changed.",
        )
        _require(
            parsed_two.record_set.revision == 2,
            "immutability",
            "revision-2 verified reader state was not retained.",
        )

    _run_stage("immutability", immutable)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--expected-core-version", default="0.6.0")
    args = parser.parse_args()
    try:
        run_acceptance(
            args.workspace,
            args.repository,
            version=args.version,
            expected_core_version=args.expected_core_version,
        )
    except AcceptanceFailure as error:
        print(f"FAILED: {error.stage}: {error.message}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "FAILED: unexpected installed producer-acceptance harness error.",
            file=sys.stderr,
        )
        return 1
    print("Installed Concord producer acceptance passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
