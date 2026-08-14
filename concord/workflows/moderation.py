"""Teacher-controlled evidence Moderation application services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.registry_services import (
    RegistryServiceError,
    RegistryServiceNotFoundError,
    get_canonical_publication_record,
)
from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ArtifactInstance,
    ConcordRecordReference,
    CorrectionRecord,
    EvidenceReference,
    ModerationRecord,
    PrivacyPolicy,
    SubjectReference,
)
from concord.storage import commit_record_batch
from concord.workflows._collaboration import (
    load_graph,
    require_group,
    require_new_identity,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    actor_reference,
    ensure_mutating_workspace_root,
    require_core_class,
    resolve_read_workspace_root,
    workflow_timestamp,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult
from concord.workflows.participants import core_student_participant


@dataclass(frozen=True, slots=True, kw_only=True)
class AddModerationRecordRequest:
    class_id: str
    activity_id: str
    moderation_record_id: str
    target_evidence_reference: EvidenceReference
    target_subject_references: tuple[SubjectReference, ...]
    status: str
    permitted_use: str
    rationale: str
    privacy_policy: PrivacyPolicy
    expected_snapshot_revision: int
    actor: WorkflowActor
    qualification: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceModerationRecordRequest:
    class_id: str
    activity_id: str
    moderation_record_id: str
    replacement_moderation_record_id: str
    correction_id: str
    reason: str
    target_evidence_reference: EvidenceReference
    target_subject_references: tuple[SubjectReference, ...]
    status: str
    permitted_use: str
    rationale: str
    privacy_policy: PrivacyPolicy
    expected_snapshot_revision: int
    actor: WorkflowActor
    qualification: str | None = None
    correction_privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ModerationMutationResult:
    commit: WorkflowCommitResult
    moderation_record_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ModerationSummary:
    class_id: str
    activity_id: str
    moderation_record_id: str
    evidence_reference: EvidenceReference
    target_subject_references: tuple[SubjectReference, ...]
    moderator_display_label: str | None
    moderated_at: str
    status: str
    permitted_use: str
    qualification: str | None
    privacy_policy: PrivacyPolicy
    supersedes_moderation_record_id: str | None
    is_current: bool
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ModerationDetail:
    summary: ModerationSummary
    rationale: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ModerationRequirementAssessment:
    class_id: str
    activity_id: str
    evidence_reference: EvidenceReference
    evidence_reference_requires_moderation: bool
    artifact_review_requires_moderation: bool
    artifact_review_id: str | None
    required: bool
    applicable_moderation_records: tuple[ModerationSummary, ...]
    snapshot_revision: int


def _require_artifact(
    graph: ConcordRecordGraph,
    activity_id: str,
    artifact_instance_id: str,
) -> ArtifactInstance:
    artifact = next(
        (
            item
            for item in graph.artifact_instances
            if item.artifact_instance_id == artifact_instance_id
        ),
        None,
    )
    if artifact is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact is not available: {artifact_instance_id}"
        )
    if artifact.activity_id != activity_id:
        raise ConcordWorkflowValidationError(
            "Artifact belongs to a different Activity."
        )
    return artifact


def _validate_evidence(
    graph: ConcordRecordGraph,
    activity_id: str,
    reference: EvidenceReference,
) -> ArtifactInstance | None:
    if reference.owning_system != "concord":
        if reference.evidence_kind in {"artifact_instance", "artifact_page"}:
            raise ConcordWorkflowValidationError(
                "Artifact evidence owned outside Concord is not a local Artifact."
            )
        return None
    if reference.evidence_kind == "artifact_instance":
        return _require_artifact(graph, activity_id, reference.record_id)
    if reference.evidence_kind == "artifact_page":
        page = next(
            (
                item
                for item in graph.artifact_pages
                if item.artifact_page_id == reference.record_id
            ),
            None,
        )
        if page is None:
            raise ConcordWorkflowNotFoundError(
                f"Artifact Page is not available: {reference.record_id}"
            )
        return _require_artifact(graph, activity_id, page.artifact_instance_id)
    raise ConcordWorkflowValidationError(
        "Concord-owned Moderation evidence must identify an Artifact or Artifact Page."
    )



def _validate_core_publication_reference(
    root: Path,
    reference: EvidenceReference,
) -> None:
    publication_reference = reference.source_publication_reference
    if publication_reference is None:
        return
    try:
        publication = get_canonical_publication_record(
            root,
            publication_reference.publication_id,
        )
    except RegistryServiceNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            "Core Publication Record is not available: "
            f"{publication_reference.publication_id}"
        ) from error
    except RegistryServiceError as error:
        raise ConcordWorkflowValidationError(
            f"Core Publication Record could not be verified: {error}"
        ) from error

    expected_schema = publication_reference.publication_schema_version
    if expected_schema is not None and publication.schema_version != expected_schema:
        raise ConcordWorkflowValidationError(
            "Core Publication schema version does not match the evidence reference."
        )
    if publication.work.module_id != reference.owning_system:
        raise ConcordWorkflowValidationError(
            "Core Publication producer module does not match the evidence owner."
        )


def _validate_evidence_lineage(
    root: Path,
    graph: ConcordRecordGraph,
    activity_id: str,
    reference: EvidenceReference,
) -> ArtifactInstance | None:
    artifact = _validate_evidence(graph, activity_id, reference)
    _validate_core_publication_reference(root, reference)
    return artifact


def _validate_subjects(
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    activity_id: str,
    subjects: tuple[SubjectReference, ...],
) -> None:
    for reference in subjects:
        if reference.subject_kind == "core_student":
            if reference.owning_system != "core":
                raise ConcordWorkflowValidationError(
                    "core_student Moderation Subjects must be owned by Core."
                )
            core_student_participant(root, class_id, reference.subject_id)
        elif reference.subject_kind == "concord_group":
            if reference.owning_system != "concord":
                raise ConcordWorkflowValidationError(
                    "concord_group Moderation Subjects must be owned by Concord."
                )
            group = require_group(graph, reference.subject_id)
            if group.activity_id != activity_id:
                raise ConcordWorkflowValidationError(
                    "Moderation Subject Group belongs to a different Activity."
                )
        elif reference.subject_kind == "concord_session":
            if reference.owning_system != "concord":
                raise ConcordWorkflowValidationError(
                    "concord_session Moderation Subjects must be owned by Concord."
                )
            session = next(
                (
                    item
                    for item in graph.sessions
                    if item.session_id == reference.subject_id
                ),
                None,
            )
            if session is None:
                raise ConcordWorkflowNotFoundError(
                    f"Session is not available: {reference.subject_id}"
                )
            if session.activity_id != activity_id:
                raise ConcordWorkflowValidationError(
                    "Moderation Subject Session belongs to a different Activity."
                )
        elif reference.subject_kind == "concord_activity":
            if (
                reference.owning_system != "concord"
                or reference.subject_id != activity_id
            ):
                raise ConcordWorkflowValidationError(
                    "Moderation Activity Subject must identify the current Activity."
                )
        elif reference.subject_kind == "concord_artifact_instance":
            if reference.owning_system != "concord":
                raise ConcordWorkflowValidationError(
                    "Concord Artifact Subjects must be owned by Concord."
                )
            _require_artifact(graph, activity_id, reference.subject_id)
        elif reference.subject_kind == "external_record":
            if reference.owning_system == "concord":
                raise ConcordWorkflowValidationError(
                    "External Moderation Subjects must not pretend to be Concord-owned."
                )


def _moderation_heads(graph: ConcordRecordGraph) -> tuple[ModerationRecord, ...]:
    superseded = {
        item.supersedes_moderation_record_id
        for item in graph.moderation_records
        if item.supersedes_moderation_record_id is not None
    }
    return tuple(
        item
        for item in graph.moderation_records
        if item.moderation_record_id not in superseded
    )


def _semantic_key(
    moderation: ModerationRecord,
) -> tuple[EvidenceReference, tuple[SubjectReference, ...]]:
    return (
        moderation.target_evidence_reference,
        moderation.target_subject_references,
    )


def _require_moderation(
    graph: ConcordRecordGraph,
    moderation_record_id: str,
) -> ModerationRecord:
    moderation = next(
        (
            item
            for item in graph.moderation_records
            if item.moderation_record_id == moderation_record_id
        ),
        None,
    )
    if moderation is None:
        raise ConcordWorkflowNotFoundError(
            f"Moderation Record is not available: {moderation_record_id}"
        )
    return moderation


def _ensure_no_current_scope_duplicate(
    graph: ConcordRecordGraph,
    candidate: ModerationRecord,
    *,
    exclude_id: str | None = None,
) -> None:
    key = _semantic_key(candidate)
    for current in _moderation_heads(graph):
        if current.moderation_record_id == exclude_id:
            continue
        if _semantic_key(current) == key:
            raise ConcordWorkflowConflictError(
                "An equivalent current Moderation scope already exists."
            )


def _summary(
    class_id: str,
    activity_id: str,
    moderation: ModerationRecord,
    current_ids: frozenset[str],
    snapshot_revision: int,
) -> ModerationSummary:
    return ModerationSummary(
        class_id=class_id,
        activity_id=activity_id,
        moderation_record_id=moderation.moderation_record_id,
        evidence_reference=moderation.target_evidence_reference,
        target_subject_references=moderation.target_subject_references,
        moderator_display_label=moderation.moderator.display_label_snapshot,
        moderated_at=moderation.moderated_at,
        status=moderation.status,
        permitted_use=moderation.permitted_use,
        qualification=moderation.qualification,
        privacy_policy=moderation.privacy_policy,
        supersedes_moderation_record_id=moderation.supersedes_moderation_record_id,
        is_current=moderation.moderation_record_id in current_ids,
        snapshot_revision=snapshot_revision,
    )


def _build_moderation(
    request: AddModerationRecordRequest | ReplaceModerationRecordRequest,
    *,
    moderation_record_id: str,
    supersedes_moderation_record_id: str | None,
    clock: Clock | None,
) -> ModerationRecord:
    return ModerationRecord(
        moderation_record_id=moderation_record_id,
        target_evidence_reference=request.target_evidence_reference,
        target_subject_references=request.target_subject_references,
        moderator=actor_reference(request.actor),
        moderated_at=workflow_timestamp(clock),
        status=request.status,
        permitted_use=request.permitted_use,
        rationale=request.rationale,
        privacy_policy=request.privacy_policy,
        qualification=request.qualification,
        supersedes_moderation_record_id=supersedes_moderation_record_id,
    )


def add_moderation_record(
    request: AddModerationRecordRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ModerationMutationResult:
    """Record one current decision for an exact evidence + Subject scope."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    _validate_evidence_lineage(
        root,
        graph,
        request.activity_id,
        request.target_evidence_reference,
    )
    require_new_identity(
        graph.moderation_records,
        "moderation_record_id",
        request.moderation_record_id,
        "Moderation Record",
    )
    candidate = _build_moderation(
        request,
        moderation_record_id=request.moderation_record_id,
        supersedes_moderation_record_id=None,
        clock=clock,
    )
    _validate_subjects(
        root,
        request.class_id,
        graph,
        request.activity_id,
        candidate.target_subject_references,
    )
    _ensure_no_current_scope_duplicate(graph, candidate)
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ModerationMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        moderation_record_id=candidate.moderation_record_id,
    )


def replace_moderation_record(
    request: ReplaceModerationRecordRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ModerationMutationResult:
    """Record a successor decision for the exact same evidence + Subject scope."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    predecessor = _require_moderation(graph, request.moderation_record_id)
    if predecessor not in _moderation_heads(graph):
        raise ConcordWorkflowConflictError(
            "Historical Moderation Records cannot be replaced as a current head."
        )
    _validate_evidence_lineage(
        root,
        graph,
        request.activity_id,
        request.target_evidence_reference,
    )
    require_new_identity(
        graph.moderation_records,
        "moderation_record_id",
        request.replacement_moderation_record_id,
        "Moderation Record",
    )
    require_new_identity(
        graph.correction_records,
        "correction_id",
        request.correction_id,
        "Correction",
    )
    successor = _build_moderation(
        request,
        moderation_record_id=request.replacement_moderation_record_id,
        supersedes_moderation_record_id=predecessor.moderation_record_id,
        clock=clock,
    )
    _validate_subjects(
        root,
        request.class_id,
        graph,
        request.activity_id,
        successor.target_subject_references,
    )
    if _semantic_key(successor) != _semantic_key(predecessor):
        raise ConcordWorkflowValidationError(
            "Moderation revision must preserve exact evidence and Subject scope."
        )
    _ensure_no_current_scope_duplicate(
        graph,
        successor,
        exclude_id=predecessor.moderation_record_id,
    )
    correction = CorrectionRecord(
        correction_id=request.correction_id,
        target_reference=ConcordRecordReference(
            record_kind="moderation_record",
            record_id=predecessor.moderation_record_id,
        ),
        correction_type="moderation_revision",
        reason=request.reason,
        correcting_actor=actor_reference(request.actor),
        corrected_at=workflow_timestamp(clock),
        privacy_policy=request.correction_privacy_policy or successor.privacy_policy,
        replacement_reference=ConcordRecordReference(
            record_kind="moderation_record",
            record_id=successor.moderation_record_id,
        ),
    )
    result = commit_record_batch(
        root,
        work,
        (successor, correction),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ModerationMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        moderation_record_id=successor.moderation_record_id,
    )


def list_moderation_records(
    class_id: str,
    activity_id: str,
    *,
    include_historical: bool = True,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> tuple[ModerationSummary, ...]:
    """List Moderation summaries without exposing rationale."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    current_ids = frozenset(
        item.moderation_record_id for item in _moderation_heads(graph)
    )
    records = graph.moderation_records
    if not include_historical:
        records = tuple(
            item for item in records if item.moderation_record_id in current_ids
        )
    return tuple(
        _summary(class_id, activity_id, item, current_ids, revision)
        for item in sorted(records, key=lambda item: item.moderation_record_id)
    )


def show_moderation_record(
    class_id: str,
    activity_id: str,
    moderation_record_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> ModerationDetail:
    """Show one exact Moderation decision including its private rationale."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Moderation Record is not available: {moderation_record_id}"
        )
    graph, revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    record = _require_moderation(graph, moderation_record_id)
    current_ids = frozenset(
        item.moderation_record_id for item in _moderation_heads(graph)
    )
    return ModerationDetail(
        summary=_summary(class_id, activity_id, record, current_ids, revision),
        rationale=record.rationale,
    )


def _applicable_records(
    graph: ConcordRecordGraph,
    reference: EvidenceReference,
    subject_context: tuple[SubjectReference, ...],
) -> tuple[ModerationRecord, ...]:
    context = frozenset(subject_context)
    matches = []
    for record in _moderation_heads(graph):
        if record.target_evidence_reference != reference:
            continue
        scope = frozenset(record.target_subject_references)
        if not scope or (context and scope <= context):
            matches.append(record)
    return tuple(sorted(matches, key=lambda item: item.moderation_record_id))


def list_applicable_moderation_records(
    class_id: str,
    activity_id: str,
    evidence_reference: EvidenceReference,
    *,
    subject_context: tuple[SubjectReference, ...] = (),
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> tuple[ModerationSummary, ...]:
    """Return all current decisions applicable to exact evidence and Subject context."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    _validate_evidence_lineage(root, graph, activity_id, evidence_reference)
    _validate_subjects(root, class_id, graph, activity_id, subject_context)
    records = _applicable_records(graph, evidence_reference, subject_context)
    current_ids = frozenset(item.moderation_record_id for item in records)
    return tuple(
        _summary(class_id, activity_id, item, current_ids, revision)
        for item in records
    )


def assess_moderation_requirement(
    class_id: str,
    activity_id: str,
    evidence_reference: EvidenceReference,
    *,
    subject_context: tuple[SubjectReference, ...] = (),
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> ModerationRequirementAssessment:
    """Expose effective required-Moderation state for the later Score workflow."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(f"Activity is not available: {activity_id}")
    graph, revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    artifact = _validate_evidence_lineage(
        root,
        graph,
        activity_id,
        evidence_reference,
    )
    _validate_subjects(root, class_id, graph, activity_id, subject_context)
    evidence_requires = evidence_reference.moderation_requirement == "required"
    review_requires = False
    review_id = None
    if artifact is not None:
        superseded = {
            item.supersedes_artifact_review_id
            for item in graph.artifact_reviews
            if item.supersedes_artifact_review_id is not None
        }
        heads = tuple(
            item
            for item in graph.artifact_reviews
            if item.artifact_instance_id == artifact.artifact_instance_id
            and item.artifact_review_id not in superseded
        )
        if len(heads) > 1:
            raise ConcordWorkflowConflictError(
                "Artifact has competing current Review heads."
            )
        if heads:
            review_id = heads[0].artifact_review_id
            review_requires = heads[0].moderation_requirement == "required"
    applicable = _applicable_records(graph, evidence_reference, subject_context)
    current_ids = frozenset(item.moderation_record_id for item in applicable)
    summaries = tuple(
        _summary(class_id, activity_id, item, current_ids, revision)
        for item in applicable
    )
    return ModerationRequirementAssessment(
        class_id=class_id,
        activity_id=activity_id,
        evidence_reference=evidence_reference,
        evidence_reference_requires_moderation=evidence_requires,
        artifact_review_requires_moderation=review_requires,
        artifact_review_id=review_id,
        required=evidence_requires or review_requires,
        applicable_moderation_records=summaries,
        snapshot_revision=revision,
    )


__all__ = [
    "AddModerationRecordRequest",
    "ModerationDetail",
    "ModerationMutationResult",
    "ModerationRequirementAssessment",
    "ModerationSummary",
    "ReplaceModerationRecordRequest",
    "add_moderation_record",
    "assess_moderation_requirement",
    "list_applicable_moderation_records",
    "list_moderation_records",
    "replace_moderation_record",
    "show_moderation_record",
]
