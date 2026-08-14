"""Teacher-controlled Score recording and revision services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ConcordRecordReference,
    CorrectionRecord,
    Criterion,
    EvidenceLocator,
    EvidenceReference,
    PrivacyPolicy,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoreTargetReference,
    ScoringScale,
    StatusReason,
    SubjectReference,
)
from concord.storage import commit_record_batch
from concord.workflows._collaboration import (
    load_graph,
    require_activity,
    require_group,
    require_new_identity,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    actor_reference,
    ensure_mutating_workspace_root,
    provenance,
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
from concord.workflows.moderation import (
    ModerationRequirementAssessment,
    assess_moderation_requirement,
)
from concord.workflows.participants import core_student_participant


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreEvidenceLinkSpec:
    score_evidence_link_id: str
    evidence_reference: EvidenceReference
    relevance_description: str
    evidence_locator: EvidenceLocator | None = None
    subject_context: tuple[SubjectReference, ...] = ()
    significance: str | None = None
    moderation_record_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AddScoreRequest:
    class_id: str
    activity_id: str
    score_record_id: str
    target_reference: ScoreTargetReference
    criterion_id: str
    scoring_scale_id: str
    disposition: str
    basis: str
    privacy_policy: PrivacyPolicy
    expected_snapshot_revision: int
    actor: WorkflowActor
    session_id: str | None = None
    value: str | int | float | bool | None = None
    rationale: str | None = None
    status_reason: StatusReason | None = None
    evidence_links: tuple[ScoreEvidenceLinkSpec, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceScoreRequest:
    class_id: str
    activity_id: str
    score_record_id: str
    replacement_score_record_id: str
    correction_id: str
    reason: str
    target_reference: ScoreTargetReference
    criterion_id: str
    scoring_scale_id: str
    disposition: str
    basis: str
    privacy_policy: PrivacyPolicy
    expected_snapshot_revision: int
    actor: WorkflowActor
    session_id: str | None = None
    value: str | int | float | bool | None = None
    rationale: str | None = None
    status_reason: StatusReason | None = None
    evidence_links: tuple[ScoreEvidenceLinkSpec, ...] = ()
    correction_privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreMutationResult:
    commit: WorkflowCommitResult
    score_record_id: str
    score_evidence_link_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreSummary:
    class_id: str
    activity_id: str
    score_record_id: str
    target_reference: ScoreTargetReference
    criterion_id: str
    score_kind: str
    standard_id: str | None
    scoring_scale_id: str
    disposition: str
    value: str | int | float | bool | None
    basis: str
    session_id: str | None
    scored_at: str
    moderation_complete: bool
    supersedes_score_record_id: str | None
    is_current: bool
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreDetail:
    summary: ScoreSummary
    rationale: str | None
    status_reason: StatusReason | None
    privacy_policy: PrivacyPolicy
    evidence_links: tuple[ScoreEvidenceLink, ...]


def _score_heads(graph: ConcordRecordGraph) -> tuple[ScoreRecord, ...]:
    superseded = {
        item.supersedes_score_record_id
        for item in graph.score_records
        if item.supersedes_score_record_id is not None
    }
    return tuple(
        item
        for item in graph.score_records
        if item.score_record_id not in superseded
    )


def _require_score(
    graph: ConcordRecordGraph,
    score_record_id: str,
) -> ScoreRecord:
    score = next(
        (
            item
            for item in graph.score_records
            if item.score_record_id == score_record_id
        ),
        None,
    )
    if score is None:
        raise ConcordWorkflowNotFoundError(
            f"Score Record is not available: {score_record_id}"
        )
    return score


def _require_criterion(
    graph: ConcordRecordGraph,
    criterion_id: str,
) -> Criterion:
    criterion = next(
        (item for item in graph.criteria if item.criterion_id == criterion_id),
        None,
    )
    if criterion is None:
        raise ConcordWorkflowNotFoundError(
            f"Criterion is not available: {criterion_id}"
        )
    return criterion


def _require_scale(
    graph: ConcordRecordGraph,
    scoring_scale_id: str,
) -> ScoringScale:
    scale = next(
        (
            item
            for item in graph.scoring_scales
            if item.scoring_scale_id == scoring_scale_id
        ),
        None,
    )
    if scale is None:
        raise ConcordWorkflowNotFoundError(
            f"Scoring Scale is not available: {scoring_scale_id}"
        )
    return scale


def _validate_target(
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    activity_id: str,
    target: ScoreTargetReference,
) -> None:
    if target.target_kind == "core_student":
        if target.owning_system != "core":
            raise ConcordWorkflowValidationError(
                "core_student Score targets must be owned by Core."
            )
        core_student_participant(root, class_id, target.target_id)
        return
    if target.owning_system != "concord":
        raise ConcordWorkflowValidationError(
            "Concord Score targets must be owned by Concord."
        )
    if target.target_kind == "concord_group":
        group = require_group(graph, target.target_id)
        if group.activity_id != activity_id:
            raise ConcordWorkflowValidationError(
                "Score target Group belongs to another Activity."
            )
        return
    if target.target_kind == "concord_session":
        session = next(
            (item for item in graph.sessions if item.session_id == target.target_id),
            None,
        )
        if session is None:
            raise ConcordWorkflowNotFoundError(
                f"Session is not available: {target.target_id}"
            )
        if session.activity_id != activity_id:
            raise ConcordWorkflowValidationError(
                "Score target Session belongs to another Activity."
            )
        return
    if target.target_kind == "concord_activity":
        if target.target_id != activity_id:
            raise ConcordWorkflowValidationError(
                "Score target Activity must identify the current Activity."
            )
        return
    if target.target_kind == "concord_artifact_instance":
        artifact = next(
            (
                item
                for item in graph.artifact_instances
                if item.artifact_instance_id == target.target_id
            ),
            None,
        )
        if artifact is None:
            raise ConcordWorkflowNotFoundError(
                f"Artifact is not available: {target.target_id}"
            )
        if artifact.activity_id != activity_id:
            raise ConcordWorkflowValidationError(
                "Score target Artifact belongs to another Activity."
            )


def _validate_session(
    graph: ConcordRecordGraph,
    activity_id: str,
    session_id: str | None,
) -> None:
    if session_id is None:
        return
    session = next(
        (item for item in graph.sessions if item.session_id == session_id),
        None,
    )
    if session is None:
        raise ConcordWorkflowNotFoundError(
            f"Session is not available: {session_id}"
        )
    if session.activity_id != activity_id:
        raise ConcordWorkflowValidationError(
            "Score Session belongs to another Activity."
        )


def _validate_criterion_and_scale(
    graph: ConcordRecordGraph,
    activity_id: str,
    criterion_id: str,
    scoring_scale_id: str,
    target: ScoreTargetReference,
    disposition: str,
    value: str | int | float | bool | None,
) -> Criterion:
    activity = require_activity(graph, activity_id)
    criterion = _require_criterion(graph, criterion_id)
    criterion_set = next(
        (
            item
            for item in graph.criterion_sets
            if item.criterion_set_id == criterion.criterion_set_id
        ),
        None,
    )
    if criterion_set is None:
        raise ConcordWorkflowValidationError(
            "Criterion parent Set is not available."
        )
    if criterion_set.criterion_set_id not in activity.criterion_set_ids:
        raise ConcordWorkflowValidationError(
            "Criterion belongs to a Set not selected by the Activity."
        )
    if target.target_kind not in criterion.supported_target_kinds:
        raise ConcordWorkflowValidationError(
            "Criterion does not support the selected Score target kind."
        )
    if criterion.criterion_kind == "standard_backed":
        if activity.scoring_orientation not in {"standards_based", "mixed"}:
            raise ConcordWorkflowValidationError(
                "Activity scoring orientation forbids standard-backed Scores."
            )
        if criterion.standard_id not in activity.focus_standard_ids:
            raise ConcordWorkflowValidationError(
                "Standard-backed Criterion does not govern an Activity Focus Standard."
            )
    elif activity.scoring_orientation not in {"local_criteria_only", "mixed"}:
        raise ConcordWorkflowValidationError(
            "Activity scoring orientation forbids local Scores."
        )
    if activity.scoring_orientation == "evidence_only":
        raise ConcordWorkflowValidationError(
            "Evidence-only Activity cannot record Scores."
        )
    scale = _require_scale(graph, scoring_scale_id)
    if disposition == "scored":
        if value is None or scale.level_for_value(value) is None:
            raise ConcordWorkflowValidationError(
                "Scored value must match one exact level in the selected "
                "Scale revision."
            )
    elif value is not None:
        raise ConcordWorkflowValidationError(
            "Non-score dispositions forbid a Score value."
        )
    return criterion


def _validate_status_reason(
    request: AddScoreRequest | ReplaceScoreRequest,
) -> None:
    reason = request.status_reason
    if request.disposition == "scored":
        if reason is not None:
            raise ConcordWorkflowValidationError(
                "Scored disposition forbids a non-score StatusReason."
            )
        return
    if reason is None:
        raise ConcordWorkflowValidationError(
            "Non-score disposition requires StatusReason."
        )
    if reason.reason_code != request.disposition:
        raise ConcordWorkflowValidationError(
            "StatusReason code must match the non-score disposition."
        )
    if reason.recorded_by != actor_reference(request.actor):
        raise ConcordWorkflowValidationError(
            "StatusReason recorded_by must match the scoring actor."
        )


def _validate_link_specs(
    specs: tuple[ScoreEvidenceLinkSpec, ...],
    basis: str,
) -> None:
    if basis == "professional_judgment" and specs:
        raise ConcordWorkflowValidationError(
            "Professional judgment requires zero Evidence Links."
        )
    if basis in {"linked_evidence", "mixed_basis"} and not specs:
        raise ConcordWorkflowValidationError(
            f"{basis} requires at least one Evidence Link."
        )
    ids = tuple(item.score_evidence_link_id for item in specs)
    if len(set(ids)) != len(ids):
        raise ConcordWorkflowValidationError(
            "Score Evidence Link IDs must be unique."
        )
    sources = tuple(
        (item.evidence_reference.owning_system, item.evidence_reference.record_id)
        for item in specs
    )
    if len(set(sources)) != len(sources):
        raise ConcordWorkflowValidationError(
            "One Score must not use duplicate links to the same primary source."
        )


def _selected_moderation_is_valid(
    assessment: ModerationRequirementAssessment,
    moderation_record_id: str,
    target: ScoreTargetReference,
) -> bool:
    selected = next(
        (
            item
            for item in assessment.applicable_moderation_records
            if item.moderation_record_id == moderation_record_id
        ),
        None,
    )
    if selected is None:
        return False
    if selected.status not in {"accepted", "accepted_with_qualification"}:
        return False
    if selected.permitted_use in {"not_be_used_for_scoring", "formative_only"}:
        return False
    if selected.permitted_use == "support_named_subject":
        return (
            target.target_kind == "core_student"
            and any(
                subject.subject_kind == "core_student"
                and subject.owning_system == "core"
                and subject.subject_id == target.target_id
                for subject in selected.target_subject_references
            )
        )
    if selected.permitted_use == "support_group_score":
        return (
            target.target_kind == "concord_group"
            and any(
                subject.subject_kind == "concord_group"
                and subject.owning_system == "concord"
                and subject.subject_id == target.target_id
                for subject in selected.target_subject_references
            )
        )
    return True


def _validate_locator(
    graph: ConcordRecordGraph,
    activity_id: str,
    locator: EvidenceLocator | None,
) -> None:
    if locator is None or locator.session_id is None:
        return
    session = next(
        (
            item
            for item in graph.sessions
            if item.session_id == locator.session_id
        ),
        None,
    )
    if session is None or session.activity_id != activity_id:
        raise ConcordWorkflowValidationError(
            "Evidence locator Session must belong to the Score Activity."
        )


def _build_links(
    *,
    root: Path,
    graph: ConcordRecordGraph,
    class_id: str,
    activity_id: str,
    score_record_id: str,
    target: ScoreTargetReference,
    disposition: str,
    specs: tuple[ScoreEvidenceLinkSpec, ...],
    actor: WorkflowActor,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
) -> tuple[tuple[ScoreEvidenceLink, ...], bool]:
    links = []
    moderation_complete = disposition == "scored"
    for spec in specs:
        _validate_locator(graph, activity_id, spec.evidence_locator)
        assessment = assess_moderation_requirement(
            class_id,
            activity_id,
            spec.evidence_reference,
            subject_context=spec.subject_context,
            workspace_root=root,
            standards_library=standards_library,
        )
        valid_moderation = False
        if spec.moderation_record_id is not None:
            valid_moderation = _selected_moderation_is_valid(
                assessment,
                spec.moderation_record_id,
                target,
            )
            if not valid_moderation:
                raise ConcordWorkflowValidationError(
                    "Selected Moderation Record is not current, applicable, "
                    "accepted, or permitted for this Score target."
                )
        if disposition == "scored" and assessment.required and not valid_moderation:
            raise ConcordWorkflowValidationError(
                "Scored evidence use requires an explicit applicable current "
                "Moderation Record."
            )
        if disposition != "scored":
            moderation_complete = False
        links.append(
            ScoreEvidenceLink(
                score_evidence_link_id=spec.score_evidence_link_id,
                score_record_id=score_record_id,
                evidence_reference=spec.evidence_reference,
                evidence_locator=spec.evidence_locator,
                subject_context=spec.subject_context,
                relevance_description=spec.relevance_description,
                significance=spec.significance,
                moderation_record_id=spec.moderation_record_id,
                status="active",
                created_provenance=provenance(actor, clock=clock),
            )
        )
    return tuple(links), moderation_complete


def _build_score_and_links(
    request: AddScoreRequest | ReplaceScoreRequest,
    *,
    score_record_id: str,
    supersedes_score_record_id: str | None,
    root: Path,
    graph: ConcordRecordGraph,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
) -> tuple[ScoreRecord, tuple[ScoreEvidenceLink, ...]]:
    _validate_target(
        root,
        request.class_id,
        graph,
        request.activity_id,
        request.target_reference,
    )
    _validate_session(graph, request.activity_id, request.session_id)
    criterion = _validate_criterion_and_scale(
        graph,
        request.activity_id,
        request.criterion_id,
        request.scoring_scale_id,
        request.target_reference,
        request.disposition,
        request.value,
    )
    _validate_status_reason(request)
    _validate_link_specs(request.evidence_links, request.basis)
    links, moderation_complete = _build_links(
        root=root,
        graph=graph,
        class_id=request.class_id,
        activity_id=request.activity_id,
        score_record_id=score_record_id,
        target=request.target_reference,
        disposition=request.disposition,
        specs=request.evidence_links,
        actor=request.actor,
        standards_library=standards_library,
        clock=clock,
    )
    score = ScoreRecord(
        score_record_id=score_record_id,
        activity_id=request.activity_id,
        session_id=request.session_id,
        target_reference=request.target_reference,
        criterion_id=criterion.criterion_id,
        score_kind=criterion.criterion_kind,
        standard_id=criterion.standard_id,
        scoring_scale_id=request.scoring_scale_id,
        disposition=request.disposition,
        value=request.value,
        basis=request.basis,
        scorer=actor_reference(request.actor),
        scored_at=workflow_timestamp(clock),
        rationale=request.rationale,
        status_reason=request.status_reason,
        moderation_complete=moderation_complete,
        privacy_policy=request.privacy_policy,
        supersedes_score_record_id=supersedes_score_record_id,
    )
    return score, links


def _summary(
    class_id: str,
    score: ScoreRecord,
    current_ids: frozenset[str],
    snapshot_revision: int,
) -> ScoreSummary:
    return ScoreSummary(
        class_id=class_id,
        activity_id=score.activity_id,
        score_record_id=score.score_record_id,
        target_reference=score.target_reference,
        criterion_id=score.criterion_id,
        score_kind=score.score_kind,
        standard_id=score.standard_id,
        scoring_scale_id=score.scoring_scale_id,
        disposition=score.disposition,
        value=score.value,
        basis=score.basis,
        session_id=score.session_id,
        scored_at=score.scored_at,
        moderation_complete=score.moderation_complete,
        supersedes_score_record_id=score.supersedes_score_record_id,
        is_current=score.score_record_id in current_ids,
        snapshot_revision=snapshot_revision,
    )


def add_score(
    request: AddScoreRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ScoreMutationResult:
    """Record one explicit Score and its complete initial evidence-link set."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    require_new_identity(
        graph.score_records,
        "score_record_id",
        request.score_record_id,
        "Score Record",
    )
    for spec in request.evidence_links:
        require_new_identity(
            graph.score_evidence_links,
            "score_evidence_link_id",
            spec.score_evidence_link_id,
            "Score Evidence Link",
        )
    score, links = _build_score_and_links(
        request,
        score_record_id=request.score_record_id,
        supersedes_score_record_id=None,
        root=root,
        graph=graph,
        standards_library=standards_library,
        clock=clock,
    )
    result = commit_record_batch(
        root,
        work,
        (score, *links),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ScoreMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        score_record_id=score.score_record_id,
        score_evidence_link_ids=tuple(
            item.score_evidence_link_id for item in links
        ),
    )


def replace_score(
    request: ReplaceScoreRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ScoreMutationResult:
    """Record an explicit successor Score with fresh evidence-link identities."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    predecessor = _require_score(graph, request.score_record_id)
    if predecessor not in _score_heads(graph):
        raise ConcordWorkflowConflictError(
            "Historical Score Records cannot be replaced as current heads."
        )
    require_new_identity(
        graph.score_records,
        "score_record_id",
        request.replacement_score_record_id,
        "Score Record",
    )
    require_new_identity(
        graph.correction_records,
        "correction_id",
        request.correction_id,
        "Correction",
    )
    for spec in request.evidence_links:
        require_new_identity(
            graph.score_evidence_links,
            "score_evidence_link_id",
            spec.score_evidence_link_id,
            "Score Evidence Link",
        )
    successor, links = _build_score_and_links(
        request,
        score_record_id=request.replacement_score_record_id,
        supersedes_score_record_id=predecessor.score_record_id,
        root=root,
        graph=graph,
        standards_library=standards_library,
        clock=clock,
    )
    correction = CorrectionRecord(
        correction_id=request.correction_id,
        target_reference=ConcordRecordReference(
            record_kind="score_record",
            record_id=predecessor.score_record_id,
        ),
        correction_type="score_revision",
        reason=request.reason,
        correcting_actor=actor_reference(request.actor),
        corrected_at=workflow_timestamp(clock),
        privacy_policy=request.correction_privacy_policy or successor.privacy_policy,
        replacement_reference=ConcordRecordReference(
            record_kind="score_record",
            record_id=successor.score_record_id,
        ),
    )
    result = commit_record_batch(
        root,
        work,
        (successor, *links, correction),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ScoreMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        score_record_id=successor.score_record_id,
        score_evidence_link_ids=tuple(
            item.score_evidence_link_id for item in links
        ),
    )


def list_scores(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    current_only: bool = False,
    target_reference: ScoreTargetReference | None = None,
    criterion_id: str | None = None,
) -> tuple[ScoreSummary, ...]:
    """List compact Score summaries without exposing private rationale."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    current_ids = frozenset(item.score_record_id for item in _score_heads(graph))
    records = graph.score_records
    if current_only:
        records = tuple(
            item for item in records if item.score_record_id in current_ids
        )
    if target_reference is not None:
        records = tuple(
            item
            for item in records
            if item.target_reference == target_reference
        )
    if criterion_id is not None:
        records = tuple(
            item for item in records if item.criterion_id == criterion_id
        )
    return tuple(
        _summary(class_id, item, current_ids, revision)
        for item in sorted(records, key=lambda item: item.score_record_id)
    )


def show_score(
    class_id: str,
    activity_id: str,
    score_record_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> ScoreDetail:
    """Show one exact Score including private rationale and evidence links."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"Score Record is not available: {score_record_id}"
        )
    graph, revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    score = _require_score(graph, score_record_id)
    current_ids = frozenset(item.score_record_id for item in _score_heads(graph))
    links = tuple(
        item
        for item in graph.score_evidence_links
        if item.score_record_id == score_record_id
    )
    return ScoreDetail(
        summary=_summary(class_id, score, current_ids, revision),
        rationale=score.rationale,
        status_reason=score.status_reason,
        privacy_policy=score.privacy_policy,
        evidence_links=tuple(
            sorted(links, key=lambda item: item.score_evidence_link_id)
        ),
    )


def list_current_score_heads(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    target_reference: ScoreTargetReference | None = None,
    criterion_id: str | None = None,
) -> tuple[ScoreSummary, ...]:
    """Return every explicit current Score lineage head matching the filters."""
    return list_scores(
        class_id,
        activity_id,
        workspace_root=workspace_root,
        standards_library=standards_library,
        current_only=True,
        target_reference=target_reference,
        criterion_id=criterion_id,
    )


__all__ = [
    "AddScoreRequest",
    "ReplaceScoreRequest",
    "ScoreDetail",
    "ScoreEvidenceLinkSpec",
    "ScoreMutationResult",
    "ScoreSummary",
    "add_score",
    "list_current_score_heads",
    "list_scores",
    "replace_score",
    "show_score",
]
