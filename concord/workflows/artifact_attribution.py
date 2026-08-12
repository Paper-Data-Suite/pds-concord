"""Artifact Author and Subject application services."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TypeAlias

from pds_core.standards import StandardsLibrary

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    ActorReference,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactSubject,
    ConcordRecordReference,
    CorrectionRecord,
    ParticipantReference,
    PrivacyPolicy,
    SubjectReference,
)
from concord.storage import commit_record_batch
from concord.workflows._collaboration import (
    load_graph,
    require_group,
    require_new_identity,
    require_role,
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
from concord.workflows.participants import (
    core_student_participant,
    participant_display_label,
    validate_participant_reference,
)

AuthorWorkflowReference: TypeAlias = (
    ParticipantReference | ActorReference | ConcordRecordReference | None
)

_PARTICIPANT_AUTHORSHIP_MODES = frozenset(
    {
        "individual_author",
        "co_author",
        "observer",
        "recorder",
        "recorder_for_group",
    }
)
_ACTOR_AUTHORSHIP_MODES = frozenset({"teacher_author", "authorized_adult_author"})
_SUBJECT_ROLE_KINDS = {
    "observed_participant": "core_student",
    "represented_group": "concord_group",
    "activity_context": "concord_activity",
    "session_context": "concord_session",
    "evaluated_artifact": "concord_artifact_instance",
}


@dataclass(frozen=True, slots=True, kw_only=True)
class AddArtifactAuthorRequest:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_author_id: str
    authorship_mode: str
    attribution_status: str
    attribution_source: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    author_reference: AuthorWorkflowReference = None
    represented_group_id: str | None = None
    role_assignment_id: str | None = None
    representation_status: str | None = None
    privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateArtifactAuthorRequest:
    class_id: str
    activity_id: str
    artifact_author_id: str
    attribution_status: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceArtifactAuthorRequest:
    class_id: str
    activity_id: str
    artifact_author_id: str
    replacement_artifact_author_id: str
    correction_id: str
    reason: str
    authorship_mode: str
    attribution_status: str
    attribution_source: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    author_reference: AuthorWorkflowReference = None
    represented_group_id: str | None = None
    role_assignment_id: str | None = None
    representation_status: str | None = None
    privacy_policy: PrivacyPolicy | None = None
    correction_privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class AddArtifactSubjectRequest:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_subject_id: str
    subject_reference: SubjectReference
    subject_role: str
    confirmation_status: str
    assignment_source: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    criterion_id: str | None = None
    privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateArtifactSubjectRequest:
    class_id: str
    activity_id: str
    artifact_subject_id: str
    confirmation_status: str
    expected_snapshot_revision: int
    actor: WorkflowActor


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplaceArtifactSubjectRequest:
    class_id: str
    activity_id: str
    artifact_subject_id: str
    replacement_artifact_subject_id: str
    correction_id: str
    reason: str
    subject_reference: SubjectReference
    subject_role: str
    confirmation_status: str
    assignment_source: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    criterion_id: str | None = None
    privacy_policy: PrivacyPolicy | None = None
    correction_privacy_policy: PrivacyPolicy | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactAttributionMutationResult:
    commit: WorkflowCommitResult
    association_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactAuthorSummary:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_author_id: str
    author_reference: AuthorWorkflowReference
    reference_display_label: str | None
    authorship_mode: str
    attribution_status: str
    attribution_source: str
    represented_group_id: str | None
    role_assignment_id: str | None
    representation_status: str | None
    privacy_policy: PrivacyPolicy | None
    supersedes_artifact_author_id: str | None
    is_current: bool
    snapshot_revision: int


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactSubjectSummary:
    class_id: str
    activity_id: str
    artifact_instance_id: str
    artifact_subject_id: str
    subject_reference: SubjectReference
    reference_display_label: str | None
    subject_role: str
    confirmation_status: str
    assignment_source: str
    criterion_id: str | None
    privacy_policy: PrivacyPolicy | None
    supersedes_artifact_subject_id: str | None
    is_current: bool
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


def _require_author(
    graph: ConcordRecordGraph,
    artifact_author_id: str,
) -> ArtifactAuthor:
    author = next(
        (
            item
            for item in graph.artifact_authors
            if item.artifact_author_id == artifact_author_id
        ),
        None,
    )
    if author is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Author is not available: {artifact_author_id}"
        )
    return author


def _require_subject(
    graph: ConcordRecordGraph,
    artifact_subject_id: str,
) -> ArtifactSubject:
    subject = next(
        (
            item
            for item in graph.artifact_subjects
            if item.artifact_subject_id == artifact_subject_id
        ),
        None,
    )
    if subject is None:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Subject is not available: {artifact_subject_id}"
        )
    return subject


def _current_authors(graph: ConcordRecordGraph) -> tuple[ArtifactAuthor, ...]:
    superseded_ids = {
        item.supersedes_artifact_author_id
        for item in graph.artifact_authors
        if item.supersedes_artifact_author_id is not None
    }
    return tuple(
        item
        for item in graph.artifact_authors
        if item.artifact_author_id not in superseded_ids
        and item.attribution_status != "superseded"
    )


def _current_subjects(graph: ConcordRecordGraph) -> tuple[ArtifactSubject, ...]:
    superseded_ids = {
        item.supersedes_artifact_subject_id
        for item in graph.artifact_subjects
        if item.supersedes_artifact_subject_id is not None
    }
    return tuple(
        item
        for item in graph.artifact_subjects
        if item.artifact_subject_id not in superseded_ids
        and item.confirmation_status != "superseded"
    )


def _author_semantic_key(author: ArtifactAuthor) -> tuple[object, ...]:
    return (
        author.artifact_instance_id,
        author.author_reference,
        author.authorship_mode,
        author.represented_group_id,
        author.role_assignment_id,
        author.representation_status,
    )


def _subject_semantic_key(subject: ArtifactSubject) -> tuple[object, ...]:
    return (
        subject.artifact_instance_id,
        subject.subject_reference,
        subject.subject_role,
        subject.criterion_id,
    )


def _ensure_author_not_duplicate(
    graph: ConcordRecordGraph,
    candidate: ArtifactAuthor,
    *,
    exclude_id: str | None = None,
) -> None:
    key = _author_semantic_key(candidate)
    for existing in _current_authors(graph):
        if existing.artifact_author_id == exclude_id:
            continue
        if _author_semantic_key(existing) == key:
            raise ConcordWorkflowConflictError(
                "An equivalent current Artifact Author association already exists."
            )


def _ensure_subject_not_duplicate(
    graph: ConcordRecordGraph,
    candidate: ArtifactSubject,
    *,
    exclude_id: str | None = None,
) -> None:
    key = _subject_semantic_key(candidate)
    for existing in _current_subjects(graph):
        if existing.artifact_subject_id == exclude_id:
            continue
        if _subject_semantic_key(existing) == key:
            raise ConcordWorkflowConflictError(
                "An equivalent current Artifact Subject association already exists."
            )


def _require_current_author(
    graph: ConcordRecordGraph,
    author: ArtifactAuthor,
) -> None:
    if author not in _current_authors(graph):
        raise ConcordWorkflowConflictError(
            "Historical Artifact Author associations cannot be revised in place."
        )


def _require_current_subject(
    graph: ConcordRecordGraph,
    subject: ArtifactSubject,
) -> None:
    if subject not in _current_subjects(graph):
        raise ConcordWorkflowConflictError(
            "Historical Artifact Subject associations cannot be revised in place."
        )


def _validate_author_semantics(
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    artifact: ArtifactInstance,
    author: ArtifactAuthor,
) -> None:
    if author.attribution_status == "superseded":
        raise ConcordWorkflowValidationError(
            "superseded is historical state; use Artifact Author replacement."
        )
    reference = author.author_reference
    if reference is None:
        # The native model enforces the exact unknown-author state.
        return

    if isinstance(reference, ParticipantReference):
        validate_participant_reference(root, class_id, reference)
        if author.authorship_mode not in _PARTICIPANT_AUTHORSHIP_MODES:
            raise ConcordWorkflowValidationError(
                "Participant Authors require an individual, co-author, observer, "
                "recorder, or recorder-for-Group authorship mode."
            )
    elif isinstance(reference, ActorReference):
        if author.authorship_mode not in _ACTOR_AUTHORSHIP_MODES:
            raise ConcordWorkflowValidationError(
                "Actor Authors require teacher_author or authorized_adult_author."
            )
        if reference.actor_kind != "authorized_adult":
            raise ConcordWorkflowValidationError(
                "Teacher and authorized-adult authorship requires an "
                "authorized_adult Actor reference."
            )
    elif isinstance(reference, ConcordRecordReference):
        if (
            author.authorship_mode != "collective_group_author"
            or reference.record_kind != "group"
        ):
            raise ConcordWorkflowValidationError(
                "Concord Author references must identify a collective Group Author."
            )
        group = require_group(graph, reference.record_id)
        if group.activity_id != artifact.activity_id:
            raise ConcordWorkflowValidationError(
                "Collective Author Group belongs to a different Activity."
            )
    else:  # pragma: no cover - the native model rejects this first.
        raise ConcordWorkflowValidationError("Unsupported Artifact Author reference.")

    if author.represented_group_id is not None:
        if author.authorship_mode != "recorder_for_group":
            raise ConcordWorkflowValidationError(
                "represented_group_id is reserved for recorder_for_group authorship."
            )
        group = require_group(graph, author.represented_group_id)
        if group.activity_id != artifact.activity_id:
            raise ConcordWorkflowValidationError(
                "Represented Group belongs to a different Activity."
            )
    if author.authorship_mode == "recorder_for_group":
        if not isinstance(reference, ParticipantReference):
            raise ConcordWorkflowValidationError(
                "recorder_for_group requires an individual Participant reference."
            )
        if author.representation_status is None:
            raise ConcordWorkflowValidationError(
                "recorder_for_group requires an explicit representation_status."
            )

    if author.role_assignment_id is not None:
        if not isinstance(reference, ParticipantReference):
            raise ConcordWorkflowValidationError(
                "Role context is valid only for a Participant Author."
            )
        role = require_role(graph, author.role_assignment_id)
        if role.activity_id != artifact.activity_id:
            raise ConcordWorkflowValidationError(
                "Referenced Role belongs to a different Activity."
            )
        if role.participant_reference != reference:
            raise ConcordWorkflowValidationError(
                "Artifact Author and referenced Role participant differ."
            )
        if (
            author.represented_group_id is not None
            and role.group_id is not None
            and role.group_id != author.represented_group_id
        ):
            raise ConcordWorkflowValidationError(
                "Referenced Role Group differs from represented_group_id."
            )


def _validate_subject_semantics(
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    artifact: ArtifactInstance,
    subject: ArtifactSubject,
) -> None:
    if subject.confirmation_status == "superseded":
        raise ConcordWorkflowValidationError(
            "superseded is historical state; use Artifact Subject replacement."
        )
    reference = subject.subject_reference
    if reference.subject_kind == "core_student":
        if reference.owning_system != "core":
            raise ConcordWorkflowValidationError(
                "core_student Subjects must be owned by Core."
            )
        resolved = core_student_participant(root, class_id, reference.subject_id)
        if resolved.participant_id != reference.subject_id:
            raise ConcordWorkflowValidationError(
                "Core student Subject is inconsistent with the class roster."
            )
    elif reference.subject_kind == "concord_group":
        if reference.owning_system != "concord":
            raise ConcordWorkflowValidationError(
                "concord_group Subjects must be owned by Concord."
            )
        group = require_group(graph, reference.subject_id)
        if group.activity_id != artifact.activity_id:
            raise ConcordWorkflowValidationError(
                "Subject Group belongs to a different Activity."
            )
    elif reference.subject_kind == "concord_session":
        if reference.owning_system != "concord":
            raise ConcordWorkflowValidationError(
                "concord_session Subjects must be owned by Concord."
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
        if session.activity_id != artifact.activity_id:
            raise ConcordWorkflowValidationError(
                "Subject Session belongs to a different Activity."
            )
    elif reference.subject_kind == "concord_activity":
        if (
            reference.owning_system != "concord"
            or reference.subject_id != artifact.activity_id
        ):
            raise ConcordWorkflowValidationError(
                "Activity Subject must identify the Artifact's own Concord Activity."
            )
    elif reference.subject_kind == "concord_artifact_instance":
        if reference.owning_system != "concord":
            raise ConcordWorkflowValidationError(
                "concord_artifact_instance Subjects must be owned by Concord."
            )
        target = _require_artifact(
            graph,
            artifact.activity_id,
            reference.subject_id,
        )
        if target.activity_id != artifact.activity_id:  # defensive clarity
            raise ConcordWorkflowValidationError(
                "Subject Artifact belongs to a different Activity."
            )
    elif reference.subject_kind == "external_record":
        if reference.owning_system == "concord":
            raise ConcordWorkflowValidationError(
                "external_record Subjects must not pretend to be Concord-owned."
            )
    else:  # pragma: no cover - SubjectReference rejects unsupported kinds.
        raise ConcordWorkflowValidationError("Unsupported Artifact Subject kind.")

    expected_kind = _SUBJECT_ROLE_KINDS.get(subject.subject_role)
    if expected_kind is not None and reference.subject_kind != expected_kind:
        raise ConcordWorkflowValidationError(
            f"Subject role {subject.subject_role} requires {expected_kind}."
        )

    if subject.criterion_id is not None:
        criterion = next(
            (
                item
                for item in graph.criteria
                if item.criterion_id == subject.criterion_id
            ),
            None,
        )
        if criterion is None:
            raise ConcordWorkflowNotFoundError(
                f"Criterion is not available: {subject.criterion_id}"
            )
        activity = next(
            (
                item
                for item in graph.activities
                if item.activity_id == artifact.activity_id
            ),
            None,
        )
        if (
            activity is None
            or criterion.criterion_set_id not in activity.criterion_set_ids
        ):
            raise ConcordWorkflowValidationError(
                "Criterion-specific Subject context is outside the Artifact Activity."
            )


def _author_display_label(
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    author: ArtifactAuthor,
) -> str | None:
    reference = author.author_reference
    if reference is None:
        return None
    if isinstance(reference, ParticipantReference):
        return participant_display_label(root, class_id, reference)
    if isinstance(reference, ActorReference):
        return reference.display_label_snapshot
    if (
        isinstance(reference, ConcordRecordReference)
        and reference.record_kind == "group"
    ):
        group = next(
            (item for item in graph.groups if item.group_id == reference.record_id),
            None,
        )
        return None if group is None else group.label
    return None


def _subject_display_label(
    root: Path,
    class_id: str,
    graph: ConcordRecordGraph,
    reference: SubjectReference,
) -> str | None:
    if reference.subject_kind == "core_student":
        participant = ParticipantReference(
            participant_kind="core_student",
            participant_id=reference.subject_id,
            owning_system="core",
        )
        return participant_display_label(root, class_id, participant)
    if reference.subject_kind == "concord_group":
        group = next(
            (item for item in graph.groups if item.group_id == reference.subject_id),
            None,
        )
        return None if group is None else group.label
    if reference.subject_kind == "concord_session":
        session = next(
            (
                item
                for item in graph.sessions
                if item.session_id == reference.subject_id
            ),
            None,
        )
        return None if session is None else (session.label or session.session_id)
    if reference.subject_kind == "concord_activity":
        activity = next(
            (
                item
                for item in graph.activities
                if item.activity_id == reference.subject_id
            ),
            None,
        )
        return None if activity is None else activity.title
    return reference.subject_id


def add_artifact_author(
    request: AddArtifactAuthorRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactAttributionMutationResult:
    """Create one explicit Artifact Author association."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        request.artifact_instance_id,
    )
    require_new_identity(
        graph.artifact_authors,
        "artifact_author_id",
        request.artifact_author_id,
        "Artifact Author",
    )
    candidate = ArtifactAuthor(
        artifact_author_id=request.artifact_author_id,
        artifact_instance_id=artifact.artifact_instance_id,
        author_reference=request.author_reference,
        authorship_mode=request.authorship_mode,
        attribution_status=request.attribution_status,
        attribution_source=request.attribution_source,
        created_provenance=provenance(request.actor, clock=clock),
        represented_group_id=request.represented_group_id,
        role_assignment_id=request.role_assignment_id,
        representation_status=request.representation_status,
        privacy_policy=request.privacy_policy,
    )
    _validate_author_semantics(root, request.class_id, graph, artifact, candidate)
    _ensure_author_not_duplicate(graph, candidate)
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactAttributionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        association_id=candidate.artifact_author_id,
    )


def update_artifact_author(
    request: UpdateArtifactAuthorRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactAttributionMutationResult:
    """Revise only the state of the same semantic Author association."""
    if request.attribution_status == "superseded":
        raise ConcordWorkflowValidationError(
            "Use Artifact Author replacement rather than setting superseded directly."
        )
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = _require_author(graph, request.artifact_author_id)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        current.artifact_instance_id,
    )
    _require_current_author(graph, current)
    candidate = replace(current, attribution_status=request.attribution_status)
    _validate_author_semantics(root, request.class_id, graph, artifact, candidate)
    _ = clock
    _ = request.actor
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactAttributionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        association_id=candidate.artifact_author_id,
    )


def replace_artifact_author(
    request: ReplaceArtifactAuthorRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactAttributionMutationResult:
    """Replace a semantically wrong Author and record an auditable correction."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    predecessor = _require_author(graph, request.artifact_author_id)
    _require_current_author(graph, predecessor)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        predecessor.artifact_instance_id,
    )
    require_new_identity(
        graph.artifact_authors,
        "artifact_author_id",
        request.replacement_artifact_author_id,
        "Artifact Author",
    )
    require_new_identity(
        graph.correction_records,
        "correction_id",
        request.correction_id,
        "Correction",
    )
    successor = ArtifactAuthor(
        artifact_author_id=request.replacement_artifact_author_id,
        artifact_instance_id=predecessor.artifact_instance_id,
        author_reference=request.author_reference,
        authorship_mode=request.authorship_mode,
        attribution_status=request.attribution_status,
        attribution_source=request.attribution_source,
        created_provenance=provenance(request.actor, clock=clock),
        represented_group_id=request.represented_group_id,
        role_assignment_id=request.role_assignment_id,
        representation_status=request.representation_status,
        privacy_policy=request.privacy_policy,
        supersedes_artifact_author_id=predecessor.artifact_author_id,
    )
    _validate_author_semantics(root, request.class_id, graph, artifact, successor)
    if _author_semantic_key(successor) == _author_semantic_key(predecessor):
        raise ConcordWorkflowValidationError(
            "Replacement does not change Author semantics; use a status update instead."
        )
    _ensure_author_not_duplicate(
        graph,
        successor,
        exclude_id=predecessor.artifact_author_id,
    )
    correction_privacy = (
        request.correction_privacy_policy
        or successor.privacy_policy
        or predecessor.privacy_policy
        or artifact.privacy_policy
    )
    correction = CorrectionRecord(
        correction_id=request.correction_id,
        target_reference=ConcordRecordReference(
            record_kind="artifact_author",
            record_id=predecessor.artifact_author_id,
        ),
        correction_type="author_correction",
        reason=request.reason,
        correcting_actor=actor_reference(request.actor),
        corrected_at=workflow_timestamp(clock),
        privacy_policy=correction_privacy,
        replacement_reference=ConcordRecordReference(
            record_kind="artifact_author",
            record_id=successor.artifact_author_id,
        ),
    )
    result = commit_record_batch(
        root,
        work,
        (successor, correction),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactAttributionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        association_id=successor.artifact_author_id,
    )


def add_artifact_subject(
    request: AddArtifactSubjectRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactAttributionMutationResult:
    """Create one explicit Artifact Subject association."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        request.artifact_instance_id,
    )
    require_new_identity(
        graph.artifact_subjects,
        "artifact_subject_id",
        request.artifact_subject_id,
        "Artifact Subject",
    )
    candidate = ArtifactSubject(
        artifact_subject_id=request.artifact_subject_id,
        artifact_instance_id=artifact.artifact_instance_id,
        subject_reference=request.subject_reference,
        subject_role=request.subject_role,
        confirmation_status=request.confirmation_status,
        assignment_source=request.assignment_source,
        created_provenance=provenance(request.actor, clock=clock),
        criterion_id=request.criterion_id,
        privacy_policy=request.privacy_policy,
    )
    _validate_subject_semantics(root, request.class_id, graph, artifact, candidate)
    _ensure_subject_not_duplicate(graph, candidate)
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactAttributionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        association_id=candidate.artifact_subject_id,
    )


def update_artifact_subject(
    request: UpdateArtifactSubjectRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactAttributionMutationResult:
    """Revise only the state of the same semantic Subject association."""
    if request.confirmation_status == "superseded":
        raise ConcordWorkflowValidationError(
            "Use Artifact Subject replacement rather than setting superseded directly."
        )
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    current = _require_subject(graph, request.artifact_subject_id)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        current.artifact_instance_id,
    )
    _require_current_subject(graph, current)
    candidate = replace(current, confirmation_status=request.confirmation_status)
    _validate_subject_semantics(root, request.class_id, graph, artifact, candidate)
    _ = clock
    _ = request.actor
    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactAttributionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        association_id=candidate.artifact_subject_id,
    )


def replace_artifact_subject(
    request: ReplaceArtifactSubjectRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ArtifactAttributionMutationResult:
    """Replace a semantically wrong Subject and record an auditable correction."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, _, _ = load_graph(root, work, standards_library)
    predecessor = _require_subject(graph, request.artifact_subject_id)
    _require_current_subject(graph, predecessor)
    artifact = _require_artifact(
        graph,
        request.activity_id,
        predecessor.artifact_instance_id,
    )
    require_new_identity(
        graph.artifact_subjects,
        "artifact_subject_id",
        request.replacement_artifact_subject_id,
        "Artifact Subject",
    )
    require_new_identity(
        graph.correction_records,
        "correction_id",
        request.correction_id,
        "Correction",
    )
    successor = ArtifactSubject(
        artifact_subject_id=request.replacement_artifact_subject_id,
        artifact_instance_id=predecessor.artifact_instance_id,
        subject_reference=request.subject_reference,
        subject_role=request.subject_role,
        confirmation_status=request.confirmation_status,
        assignment_source=request.assignment_source,
        created_provenance=provenance(request.actor, clock=clock),
        criterion_id=request.criterion_id,
        privacy_policy=request.privacy_policy,
        supersedes_artifact_subject_id=predecessor.artifact_subject_id,
    )
    _validate_subject_semantics(root, request.class_id, graph, artifact, successor)
    if _subject_semantic_key(successor) == _subject_semantic_key(predecessor):
        raise ConcordWorkflowValidationError(
            "Replacement does not change Subject semantics; use a status update "
            "instead."
        )
    _ensure_subject_not_duplicate(
        graph,
        successor,
        exclude_id=predecessor.artifact_subject_id,
    )
    correction_privacy = (
        request.correction_privacy_policy
        or successor.privacy_policy
        or predecessor.privacy_policy
        or artifact.privacy_policy
    )
    correction = CorrectionRecord(
        correction_id=request.correction_id,
        target_reference=ConcordRecordReference(
            record_kind="artifact_subject",
            record_id=predecessor.artifact_subject_id,
        ),
        correction_type="subject_correction",
        reason=request.reason,
        correcting_actor=actor_reference(request.actor),
        corrected_at=workflow_timestamp(clock),
        privacy_policy=correction_privacy,
        replacement_reference=ConcordRecordReference(
            record_kind="artifact_subject",
            record_id=successor.artifact_subject_id,
        ),
    )
    result = commit_record_batch(
        root,
        work,
        (successor, correction),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ArtifactAttributionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        association_id=successor.artifact_subject_id,
    )


def list_artifact_authors(
    class_id: str,
    activity_id: str,
    *,
    artifact_instance_id: str | None = None,
    include_historical: bool = False,
    workspace_root: str | Path | None = None,
) -> tuple[ArtifactAuthorSummary, ...]:
    """List current Authors by default, preserving explicit historical access."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
    current_ids = {item.artifact_author_id for item in _current_authors(graph)}
    summaries: list[ArtifactAuthorSummary] = []
    for author in graph.artifact_authors:
        if artifact_instance_id is not None and (
            author.artifact_instance_id != artifact_instance_id
        ):
            continue
        is_current = author.artifact_author_id in current_ids
        if not include_historical and not is_current:
            continue
        summaries.append(
            ArtifactAuthorSummary(
                class_id=class_id,
                activity_id=activity_id,
                artifact_instance_id=author.artifact_instance_id,
                artifact_author_id=author.artifact_author_id,
                author_reference=author.author_reference,
                reference_display_label=_author_display_label(
                    root,
                    class_id,
                    graph,
                    author,
                ),
                authorship_mode=author.authorship_mode,
                attribution_status=author.attribution_status,
                attribution_source=author.attribution_source,
                represented_group_id=author.represented_group_id,
                role_assignment_id=author.role_assignment_id,
                representation_status=author.representation_status,
                privacy_policy=author.privacy_policy,
                supersedes_artifact_author_id=author.supersedes_artifact_author_id,
                is_current=is_current,
                snapshot_revision=revision,
            )
        )
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.artifact_instance_id,
                0 if item.is_current else 1,
                item.reference_display_label or "",
                item.artifact_author_id,
            ),
        )
    )


def show_artifact_author(
    class_id: str,
    activity_id: str,
    artifact_author_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactAuthorSummary:
    """Show one Author association, including historical associations by ID."""
    matches = tuple(
        item
        for item in list_artifact_authors(
            class_id,
            activity_id,
            include_historical=True,
            workspace_root=workspace_root,
        )
        if item.artifact_author_id == artifact_author_id
    )
    if not matches:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Author is not available: {artifact_author_id}"
        )
    return matches[0]


def list_artifact_subjects(
    class_id: str,
    activity_id: str,
    *,
    artifact_instance_id: str | None = None,
    include_historical: bool = False,
    workspace_root: str | Path | None = None,
) -> tuple[ArtifactSubjectSummary, ...]:
    """List current Subjects by default, preserving explicit historical access."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    graph, revision, _ = load_graph(root, work_ref(class_id, activity_id))
    current_ids = {item.artifact_subject_id for item in _current_subjects(graph)}
    summaries: list[ArtifactSubjectSummary] = []
    for subject in graph.artifact_subjects:
        if artifact_instance_id is not None and (
            subject.artifact_instance_id != artifact_instance_id
        ):
            continue
        is_current = subject.artifact_subject_id in current_ids
        if not include_historical and not is_current:
            continue
        summaries.append(
            ArtifactSubjectSummary(
                class_id=class_id,
                activity_id=activity_id,
                artifact_instance_id=subject.artifact_instance_id,
                artifact_subject_id=subject.artifact_subject_id,
                subject_reference=subject.subject_reference,
                reference_display_label=_subject_display_label(
                    root,
                    class_id,
                    graph,
                    subject.subject_reference,
                ),
                subject_role=subject.subject_role,
                confirmation_status=subject.confirmation_status,
                assignment_source=subject.assignment_source,
                criterion_id=subject.criterion_id,
                privacy_policy=subject.privacy_policy,
                supersedes_artifact_subject_id=subject.supersedes_artifact_subject_id,
                is_current=is_current,
                snapshot_revision=revision,
            )
        )
    return tuple(
        sorted(
            summaries,
            key=lambda item: (
                item.artifact_instance_id,
                0 if item.is_current else 1,
                item.reference_display_label or "",
                item.artifact_subject_id,
            ),
        )
    )


def show_artifact_subject(
    class_id: str,
    activity_id: str,
    artifact_subject_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ArtifactSubjectSummary:
    """Show one Subject association, including historical associations by ID."""
    matches = tuple(
        item
        for item in list_artifact_subjects(
            class_id,
            activity_id,
            include_historical=True,
            workspace_root=workspace_root,
        )
        if item.artifact_subject_id == artifact_subject_id
    )
    if not matches:
        raise ConcordWorkflowNotFoundError(
            f"Artifact Subject is not available: {artifact_subject_id}"
        )
    return matches[0]


__all__ = [
    "AddArtifactAuthorRequest",
    "AddArtifactSubjectRequest",
    "ArtifactAttributionMutationResult",
    "ArtifactAuthorSummary",
    "ArtifactSubjectSummary",
    "AuthorWorkflowReference",
    "ReplaceArtifactAuthorRequest",
    "ReplaceArtifactSubjectRequest",
    "UpdateArtifactAuthorRequest",
    "UpdateArtifactSubjectRequest",
    "add_artifact_author",
    "add_artifact_subject",
    "list_artifact_authors",
    "list_artifact_subjects",
    "replace_artifact_author",
    "replace_artifact_subject",
    "show_artifact_author",
    "show_artifact_subject",
    "update_artifact_author",
    "update_artifact_subject",
]
