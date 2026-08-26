"""Pure cross-record validation for Concord-native record graphs."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, TypeVar

from pds_core.standards import StandardsLibrary
from pds_core.standards_selection import resolve_profile_standard_selection

from concord.models import (
    Activity,
    ActorReference,
    ArtifactAuthor,
    ArtifactInstance,
    ArtifactPage,
    ArtifactReview,
    ArtifactSubject,
    ConcordModelError,
    ConcordRecordReference,
    CorrectionRecord,
    Criterion,
    CriterionSet,
    Group,
    GroupMembership,
    GroupPlan,
    ModerationRecord,
    PacketInstance,
    ParticipantReference,
    ResponsibilityAssignment,
    RoleAssignment,
    ScanReference,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoringScale,
    Session,
)
from concord.record_registry import RECORD_DESCRIPTORS
from concord.validation_diagnostics import ConcordRecordGraphError, ValidationIssue

Record = (
    Activity
    | Session
    | GroupPlan
    | Group
    | GroupMembership
    | RoleAssignment
    | ResponsibilityAssignment
    | PacketInstance
    | ArtifactInstance
    | ArtifactPage
    | ScanReference
    | ArtifactAuthor
    | ArtifactSubject
    | ArtifactReview
    | ModerationRecord
    | CriterionSet
    | Criterion
    | ScoringScale
    | ScoreRecord
    | ScoreEvidenceLink
    | CorrectionRecord
)
T = TypeVar("T")

_COLLECTIONS: tuple[tuple[str, type[Any], str, str], ...] = tuple(
    (
        descriptor.graph_collection,
        descriptor.model_type,
        descriptor.kind,
        descriptor.identity_field,
    )
    for descriptor in RECORD_DESCRIPTORS
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRecordGraph:
    activities: tuple[Activity, ...] = ()
    sessions: tuple[Session, ...] = ()
    group_plans: tuple[GroupPlan, ...] = ()
    groups: tuple[Group, ...] = ()
    memberships: tuple[GroupMembership, ...] = ()
    role_assignments: tuple[RoleAssignment, ...] = ()
    responsibility_assignments: tuple[ResponsibilityAssignment, ...] = ()
    packet_instances: tuple[PacketInstance, ...] = ()
    artifact_instances: tuple[ArtifactInstance, ...] = ()
    artifact_pages: tuple[ArtifactPage, ...] = ()
    scan_references: tuple[ScanReference, ...] = ()
    artifact_authors: tuple[ArtifactAuthor, ...] = ()
    artifact_subjects: tuple[ArtifactSubject, ...] = ()
    artifact_reviews: tuple[ArtifactReview, ...] = ()
    moderation_records: tuple[ModerationRecord, ...] = ()
    criterion_sets: tuple[CriterionSet, ...] = ()
    criteria: tuple[Criterion, ...] = ()
    scoring_scales: tuple[ScoringScale, ...] = ()
    score_records: tuple[ScoreRecord, ...] = ()
    score_evidence_links: tuple[ScoreEvidenceLink, ...] = ()
    correction_records: tuple[CorrectionRecord, ...] = ()

    def __post_init__(self) -> None:
        identities: set[tuple[str, str]] = set()
        for collection_name, expected, kind, id_field in _COLLECTIONS:
            values = tuple(getattr(self, collection_name))
            if any(not isinstance(value, expected) for value in values):
                raise ConcordModelError(
                    f"{collection_name} contains an invalid record."
                )
            object.__setattr__(self, collection_name, values)
            for value in values:
                identity = (kind, str(getattr(value, id_field)))
                if identity in identities:
                    raise ConcordModelError(
                        f"duplicate record identity {kind}:{identity[1]}."
                    )
                identities.add(identity)


def _index(values: Iterable[T], attribute: str) -> dict[str, T]:
    return {str(getattr(value, attribute)): value for value in values}


def _issue(
    issues: list[ValidationIssue],
    code: str,
    message: str,
    kind: str,
    record_id: str,
    *path: str | int,
) -> None:
    issues.append(
        ValidationIssue(
            code=code,
            message=message,
            record_kind=kind,
            record_id=record_id,
            field_path=path,
        )
    )


def _check_context(
    issues: list[ValidationIssue],
    context: Any,
    sessions: dict[str, Session],
    kind: str,
    record_id: str,
) -> None:
    for index, session_id in enumerate(context.session_ids):
        session = sessions.get(session_id)
        if session is None:
            _issue(
                issues,
                "effective_context.session.missing",
                "Effective Context references a missing Session.",
                kind,
                record_id,
                "effective_context",
                "session_ids",
                index,
            )
        elif session.activity_id != context.activity_id:
            _issue(
                issues,
                "effective_context.session.activity_mismatch",
                "Effective Context Session belongs to another Activity.",
                kind,
                record_id,
                "effective_context",
                "session_ids",
                index,
            )
    selected = [
        sessions[item].sequence for item in context.session_ids if item in sessions
    ]
    if (
        context.sequence_start is not None
        and selected
        and min(selected) < context.sequence_start
    ):
        _issue(
            issues,
            "effective_context.sequence.outside_bounds",
            "A referenced Session precedes sequence_start.",
            kind,
            record_id,
            "effective_context",
            "sequence_start",
        )
    if (
        context.sequence_end is not None
        and selected
        and max(selected) > context.sequence_end
    ):
        _issue(
            issues,
            "effective_context.sequence.outside_bounds",
            "A referenced Session follows sequence_end.",
            kind,
            record_id,
            "effective_context",
            "sequence_end",
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
_ACTOR_AUTHORSHIP_MODES = frozenset(
    {"teacher_author", "authorized_adult_author"}
)
_SUBJECT_ROLE_KINDS = {
    "observed_participant": "core_student",
    "represented_group": "concord_group",
    "activity_context": "concord_activity",
    "session_context": "concord_session",
    "evaluated_artifact": "concord_artifact_instance",
}
_PRE_RETURN_ARTIFACT_STATUSES = frozenset(
    {"planned", "generated", "distributed"}
)


def _artifact_author_semantic_key(author: ArtifactAuthor) -> tuple[object, ...]:
    return (
        author.artifact_instance_id,
        author.author_reference,
        author.authorship_mode,
        author.represented_group_id,
        author.role_assignment_id,
        author.representation_status,
    )


def _artifact_subject_semantic_key(subject: ArtifactSubject) -> tuple[object, ...]:
    return (
        subject.artifact_instance_id,
        subject.subject_reference,
        subject.subject_role,
        subject.criterion_id,
    )


def _validate_issue28_return_graph(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
    pages: dict[str, ArtifactPage],
) -> None:
    for artifact in graph.artifact_instances:
        declared: list[ArtifactPage] = []
        complete = True
        for page_id in artifact.page_ids:
            page = pages.get(page_id)
            if (
                page is None
                or page.artifact_instance_id != artifact.artifact_instance_id
            ):
                complete = False
                continue
            if page.return_expected:
                declared.append(page)
        if not complete:
            continue
        required_count = len(declared)
        returned_count = sum(page.page_status == "returned" for page in declared)
        status = artifact.artifact_status
        coherent = True
        if status in _PRE_RETURN_ARTIFACT_STATUSES:
            coherent = returned_count == 0
        elif status == "partially_returned":
            coherent = 0 < returned_count < required_count
        elif status == "returned":
            coherent = required_count > 0 and returned_count == required_count
        if not coherent:
            _issue(
                issues,
                "artifact.return_state.incoherent",
                "Artifact return state disagrees with its return-expected Pages.",
                "artifact_instance",
                artifact.artifact_instance_id,
                "artifact_status",
            )


def _validate_issue28_author_graph(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
    artifacts: dict[str, ArtifactInstance],
    groups: dict[str, Group],
    roles: dict[str, RoleAssignment],
) -> None:
    predecessor_ids = {
        item.supersedes_artifact_author_id
        for item in graph.artifact_authors
        if item.supersedes_artifact_author_id is not None
    }
    current = tuple(
        item
        for item in graph.artifact_authors
        if item.artifact_author_id not in predecessor_ids
        and item.attribution_status != "superseded"
    )
    counts = Counter(_artifact_author_semantic_key(item) for item in current)
    for author in current:
        if counts[_artifact_author_semantic_key(author)] > 1:
            _issue(
                issues,
                "author.current.duplicate",
                "Equivalent current Artifact Author associations are duplicated.",
                "artifact_author",
                author.artifact_author_id,
            )

    for author in graph.artifact_authors:
        artifact = artifacts.get(author.artifact_instance_id)
        reference = author.author_reference
        if (
            author.authorship_mode in _PARTICIPANT_AUTHORSHIP_MODES
            and not isinstance(reference, ParticipantReference)
        ):
            _issue(
                issues,
                "author.reference.mode_mismatch",
                "Participant authorship mode requires a Participant reference.",
                "artifact_author",
                author.artifact_author_id,
                "author_reference",
            )
        if (
            author.authorship_mode in _ACTOR_AUTHORSHIP_MODES
            and not isinstance(reference, ActorReference)
        ):
            _issue(
                issues,
                "author.reference.mode_mismatch",
                "Adult authorship mode requires an Actor reference.",
                "artifact_author",
                author.artifact_author_id,
                "author_reference",
            )
        if isinstance(reference, ActorReference) and (
            author.authorship_mode in _ACTOR_AUTHORSHIP_MODES
            and reference.actor_kind != "authorized_adult"
        ):
            _issue(
                issues,
                "author.actor.invalid",
                "Teacher/adult authorship requires an authorized-adult Actor.",
                "artifact_author",
                author.artifact_author_id,
                "author_reference",
            )
        if author.authorship_mode == "collective_group_author":
            if not (
                isinstance(reference, ConcordRecordReference)
                and reference.record_kind == "group"
            ):
                _issue(
                    issues,
                    "author.collective_group.invalid",
                    "Collective Group Author must reference one Concord Group.",
                    "artifact_author",
                    author.artifact_author_id,
                    "author_reference",
                )
        if (
            isinstance(reference, ConcordRecordReference)
            and reference.record_kind == "group"
            and artifact is not None
        ):
            group = groups.get(reference.record_id)
            if group is None or group.activity_id != artifact.activity_id:
                _issue(
                    issues,
                    "author.reference.group_invalid",
                    "Collective Author Group is invalid for the Artifact Activity.",
                    "artifact_author",
                    author.artifact_author_id,
                    "author_reference",
                )
        if (
            author.represented_group_id is not None
            and author.authorship_mode != "recorder_for_group"
        ):
            _issue(
                issues,
                "author.represented_group.mode_mismatch",
                "represented_group_id is reserved for recorder-for-Group authorship.",
                "artifact_author",
                author.artifact_author_id,
                "represented_group_id",
            )
        if author.authorship_mode == "recorder_for_group":
            if not isinstance(reference, ParticipantReference):
                _issue(
                    issues,
                    "author.recorder.invalid",
                    "Recorder-for-Group requires an individual Participant reference.",
                    "artifact_author",
                    author.artifact_author_id,
                    "author_reference",
                )
            if author.representation_status is None:
                _issue(
                    issues,
                    "author.recorder.representation_required",
                    "Recorder-for-Group requires explicit representation status.",
                    "artifact_author",
                    author.artifact_author_id,
                    "representation_status",
                )
        if author.role_assignment_id is not None:
            role = roles.get(author.role_assignment_id)
            if (
                role is not None
                and author.represented_group_id is not None
                and role.group_id is not None
                and role.group_id != author.represented_group_id
            ):
                _issue(
                    issues,
                    "author.role.group_mismatch",
                    "Author Role Group differs from the represented Group.",
                    "artifact_author",
                    author.artifact_author_id,
                    "role_assignment_id",
                )


def _validate_issue28_subject_graph(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
    activities: dict[str, Activity],
    sessions: dict[str, Session],
    groups: dict[str, Group],
    artifacts: dict[str, ArtifactInstance],
    criteria: dict[str, Criterion],
) -> None:
    predecessor_ids = {
        item.supersedes_artifact_subject_id
        for item in graph.artifact_subjects
        if item.supersedes_artifact_subject_id is not None
    }
    current = tuple(
        item
        for item in graph.artifact_subjects
        if item.artifact_subject_id not in predecessor_ids
        and item.confirmation_status != "superseded"
    )
    counts = Counter(_artifact_subject_semantic_key(item) for item in current)
    for subject in current:
        if counts[_artifact_subject_semantic_key(subject)] > 1:
            _issue(
                issues,
                "subject.current.duplicate",
                "Equivalent current Artifact Subject associations are duplicated.",
                "artifact_subject",
                subject.artifact_subject_id,
            )

    for subject in graph.artifact_subjects:
        artifact = artifacts.get(subject.artifact_instance_id)
        reference = subject.subject_reference
        if (
            reference.subject_kind == "core_student"
            and reference.owning_system != "core"
        ):
            _issue(
                issues,
                "subject.reference.owner_mismatch",
                "Core student Subject must be owned by Core.",
                "artifact_subject",
                subject.artifact_subject_id,
                "subject_reference",
            )
        if (
            reference.subject_kind == "external_record"
            and reference.owning_system == "concord"
        ):
            _issue(
                issues,
                "subject.reference.owner_mismatch",
                "External Subject must not pretend to be Concord-owned.",
                "artifact_subject",
                subject.artifact_subject_id,
                "subject_reference",
            )
        target: Activity | Session | Group | ArtifactInstance | None = None
        if reference.subject_kind == "concord_activity":
            target = activities.get(reference.subject_id)
        elif reference.subject_kind == "concord_session":
            target = sessions.get(reference.subject_id)
        elif reference.subject_kind == "concord_group":
            target = groups.get(reference.subject_id)
        elif reference.subject_kind == "concord_artifact_instance":
            target = artifacts.get(reference.subject_id)
        if (
            artifact is not None
            and target is not None
            and target.activity_id != artifact.activity_id
        ):
            _issue(
                issues,
                "subject.reference.activity_mismatch",
                "Subject target belongs to another Activity.",
                "artifact_subject",
                subject.artifact_subject_id,
                "subject_reference",
            )
        expected_kind = _SUBJECT_ROLE_KINDS.get(subject.subject_role)
        if expected_kind is not None and reference.subject_kind != expected_kind:
            _issue(
                issues,
                "subject.role.reference_mismatch",
                "Built-in Subject role is incompatible with its reference kind.",
                "artifact_subject",
                subject.artifact_subject_id,
                "subject_role",
            )
        if subject.criterion_id is not None:
            criterion = criteria.get(subject.criterion_id)
            if criterion is None:
                _issue(
                    issues,
                    "subject.criterion.missing",
                    "Artifact Subject references a missing Criterion.",
                    "artifact_subject",
                    subject.artifact_subject_id,
                    "criterion_id",
                )
            elif artifact is not None:
                activity = activities.get(artifact.activity_id)
                if (
                    activity is None
                    or criterion.criterion_set_id not in activity.criterion_set_ids
                ):
                    _issue(
                        issues,
                        "subject.criterion.activity_mismatch",
                        "Subject Criterion is outside the Artifact Activity.",
                        "artifact_subject",
                        subject.artifact_subject_id,
                        "criterion_id",
                    )


def _validate_issue28_correction_types(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    expected_targets = {
        "author_correction": "artifact_author",
        "subject_correction": "artifact_subject",
    }
    expected_types = {
        "artifact_author": "author_correction",
        "artifact_subject": "subject_correction",
    }
    for correction in graph.correction_records:
        target_kind = correction.target_reference.record_kind
        expected_target = expected_targets.get(correction.correction_type)
        expected_type = expected_types.get(target_kind)
        if (
            expected_target is not None
            and target_kind != expected_target
        ) or (
            expected_type is not None
            and correction.correction_type != expected_type
        ):
            _issue(
                issues,
                "correction.type.target_mismatch",
                "Author/Subject correction type disagrees with its target.",
                "correction",
                correction.correction_id,
                "correction_type",
            )
        if (
            correction.correction_type in expected_targets
            and correction.replacement_reference is None
        ):
            _issue(
                issues,
                "correction.replacement.required",
                "Author/Subject semantic correction requires a replacement.",
                "correction",
                correction.correction_id,
                "replacement_reference",
            )


def _review_heads(graph: ConcordRecordGraph) -> tuple[ArtifactReview, ...]:
    predecessor_ids = {
        item.supersedes_artifact_review_id
        for item in graph.artifact_reviews
        if item.supersedes_artifact_review_id is not None
    }
    return tuple(
        item
        for item in graph.artifact_reviews
        if item.artifact_review_id not in predecessor_ids
    )


def _moderation_scope_key(
    record: ModerationRecord,
) -> tuple[object, tuple[object, ...]]:
    return (
        record.target_evidence_reference,
        tuple(record.target_subject_references),
    )


def _moderation_heads(graph: ConcordRecordGraph) -> tuple[ModerationRecord, ...]:
    predecessor_ids = {
        item.supersedes_moderation_record_id
        for item in graph.moderation_records
        if item.supersedes_moderation_record_id is not None
    }
    return tuple(
        item
        for item in graph.moderation_records
        if item.moderation_record_id not in predecessor_ids
    )


def _moderation_activity_id(
    graph: ConcordRecordGraph,
    record: ModerationRecord,
    artifacts: dict[str, ArtifactInstance],
    pages: dict[str, ArtifactPage],
) -> str | None:
    reference = record.target_evidence_reference
    if reference.owning_system == "concord":
        if reference.evidence_kind == "artifact_instance":
            artifact = artifacts.get(reference.record_id)
            return None if artifact is None else artifact.activity_id
        if reference.evidence_kind == "artifact_page":
            page = pages.get(reference.record_id)
            artifact = (
                artifacts.get(page.artifact_instance_id)
                if page is not None
                else None
            )
            return None if artifact is None else artifact.activity_id
    if len(graph.activities) == 1:
        return graph.activities[0].activity_id
    return None


def _subject_activity_id(
    reference: Any,
    activities: dict[str, Activity],
    sessions: dict[str, Session],
    groups: dict[str, Group],
    artifacts: dict[str, ArtifactInstance],
) -> str | None:
    if reference.subject_kind == "concord_activity":
        return reference.subject_id if reference.subject_id in activities else None
    if reference.subject_kind == "concord_session":
        session = sessions.get(reference.subject_id)
        return None if session is None else session.activity_id
    if reference.subject_kind == "concord_group":
        group = groups.get(reference.subject_id)
        return None if group is None else group.activity_id
    if reference.subject_kind == "concord_artifact_instance":
        artifact = artifacts.get(reference.subject_id)
        return None if artifact is None else artifact.activity_id
    return None


def _validate_issue29_review_graph(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    heads = _review_heads(graph)
    counts = Counter(item.artifact_instance_id for item in heads)
    for review in heads:
        if counts[review.artifact_instance_id] > 1:
            _issue(
                issues,
                "review.current.multiple_heads",
                "Artifact has more than one current Review head.",
                "artifact_review",
                review.artifact_review_id,
                "supersedes_artifact_review_id",
            )


def _validate_issue29_moderation_graph(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
    activities: dict[str, Activity],
    sessions: dict[str, Session],
    groups: dict[str, Group],
    artifacts: dict[str, ArtifactInstance],
    pages: dict[str, ArtifactPage],
) -> None:
    heads = _moderation_heads(graph)
    counts = Counter(_moderation_scope_key(item) for item in heads)
    for moderation in heads:
        if counts[_moderation_scope_key(moderation)] > 1:
            _issue(
                issues,
                "moderation.current.duplicate_scope",
                "Evidence and Subject scope has competing current Moderation heads.",
                "moderation_record",
                moderation.moderation_record_id,
            )

    for moderation in graph.moderation_records:
        activity_id = _moderation_activity_id(
            graph,
            moderation,
            artifacts,
            pages,
        )
        for index, subject in enumerate(moderation.target_subject_references):
            _validate_subject(
                issues,
                subject.subject_kind,
                subject.subject_id,
                subject.owning_system,
                activities,
                sessions,
                groups,
                artifacts,
                "moderation_record",
                moderation.moderation_record_id,
            )
            subject_activity_id = _subject_activity_id(
                subject,
                activities,
                sessions,
                groups,
                artifacts,
            )
            if (
                activity_id is not None
                and subject_activity_id is not None
                and subject_activity_id != activity_id
            ):
                _issue(
                    issues,
                    "moderation.subject.activity_mismatch",
                    "Moderation Subject belongs to another Activity.",
                    "moderation_record",
                    moderation.moderation_record_id,
                    "target_subject_references",
                    index,
                )


def _validate_issue29_correction_types(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    expected_targets = {
        "review_correction": "artifact_review",
        "moderation_revision": "moderation_record",
    }
    expected_types = {
        "artifact_review": "review_correction",
        "moderation_record": "moderation_revision",
    }
    for correction in graph.correction_records:
        target_kind = correction.target_reference.record_kind
        expected_target = expected_targets.get(correction.correction_type)
        expected_type = expected_types.get(target_kind)
        if (
            expected_target is not None
            and target_kind != expected_target
        ) or (
            expected_type is not None
            and correction.correction_type != expected_type
        ):
            _issue(
                issues,
                "correction.type.target_mismatch",
                "Review/Moderation correction type disagrees with its target.",
                "correction",
                correction.correction_id,
                "correction_type",
            )
        if (
            correction.correction_type in expected_targets
            and correction.replacement_reference is None
        ):
            _issue(
                issues,
                "correction.replacement.required",
                "Review/Moderation revision requires a replacement.",
                "correction",
                correction.correction_id,
                "replacement_reference",
            )



def _issue29_revision_correction_exists(
    graph: ConcordRecordGraph,
    *,
    correction_type: str,
    record_kind: str,
    predecessor_id: str,
    successor_id: str,
) -> bool:
    return any(
        correction.correction_type == correction_type
        and correction.target_reference.record_kind == record_kind
        and correction.target_reference.record_id == predecessor_id
        and correction.replacement_reference is not None
        and correction.replacement_reference.record_kind == record_kind
        and correction.replacement_reference.record_id == successor_id
        for correction in graph.correction_records
    )


def _validate_issue29_revision_audits(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    for review in graph.artifact_reviews:
        predecessor_id = review.supersedes_artifact_review_id
        if predecessor_id is None:
            continue
        if not _issue29_revision_correction_exists(
            graph,
            correction_type="review_correction",
            record_kind="artifact_review",
            predecessor_id=predecessor_id,
            successor_id=review.artifact_review_id,
        ):
            _issue(
                issues,
                "review.correction.missing",
                "Review successor lacks its exact review_correction audit record.",
                "artifact_review",
                review.artifact_review_id,
                "supersedes_artifact_review_id",
            )

    for moderation in graph.moderation_records:
        predecessor_id = moderation.supersedes_moderation_record_id
        if predecessor_id is None:
            continue
        if not _issue29_revision_correction_exists(
            graph,
            correction_type="moderation_revision",
            record_kind="moderation_record",
            predecessor_id=predecessor_id,
            successor_id=moderation.moderation_record_id,
        ):
            _issue(
                issues,
                "moderation.correction.missing",
                "Moderation successor lacks its exact revision audit record.",
                "moderation_record",
                moderation.moderation_record_id,
                "supersedes_moderation_record_id",
            )


def _validate_issue29_moderation_reference_integrity(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    for moderation in graph.moderation_records:
        reference = moderation.target_evidence_reference
        if (
            reference.owning_system == "concord"
            and reference.evidence_kind not in {"artifact_instance", "artifact_page"}
        ):
            _issue(
                issues,
                "moderation.evidence.local_kind_invalid",
                "Concord-owned Moderation evidence must be an Artifact or Page.",
                "moderation_record",
                moderation.moderation_record_id,
                "target_evidence_reference",
            )
        if (
            reference.owning_system != "concord"
            and reference.evidence_kind in {"artifact_instance", "artifact_page"}
        ):
            _issue(
                issues,
                "moderation.evidence.owner_mismatch",
                "Artifact evidence used by Moderation must be Concord-owned.",
                "moderation_record",
                moderation.moderation_record_id,
                "target_evidence_reference",
            )
        for index, subject in enumerate(moderation.target_subject_references):
            if (
                subject.subject_kind == "core_student"
                and subject.owning_system != "core"
            ):
                _issue(
                    issues,
                    "moderation.subject.owner_mismatch",
                    "Core-student Moderation Subject must be owned by Core.",
                    "moderation_record",
                    moderation.moderation_record_id,
                    "target_subject_references",
                    index,
                )
            if (
                subject.subject_kind == "external_record"
                and subject.owning_system == "concord"
            ):
                _issue(
                    issues,
                    "moderation.subject.owner_mismatch",
                    "External Moderation Subject must not be Concord-owned.",
                    "moderation_record",
                    moderation.moderation_record_id,
                    "target_subject_references",
                    index,
                )


def _artifact_for_issue29_evidence(
    reference: Any,
    artifacts: dict[str, ArtifactInstance],
    pages: dict[str, ArtifactPage],
) -> ArtifactInstance | None:
    if reference.owning_system != "concord":
        return None
    if reference.evidence_kind == "artifact_instance":
        return artifacts.get(reference.record_id)
    if reference.evidence_kind == "artifact_page":
        page = pages.get(reference.record_id)
        return None if page is None else artifacts.get(page.artifact_instance_id)
    return None


def _issue29_review_requires_moderation(
    graph: ConcordRecordGraph,
    reference: Any,
    artifacts: dict[str, ArtifactInstance],
    pages: dict[str, ArtifactPage],
) -> bool:
    artifact = _artifact_for_issue29_evidence(reference, artifacts, pages)
    if artifact is None:
        return False
    return any(
        review.artifact_instance_id == artifact.artifact_instance_id
        and review.moderation_requirement == "required"
        for review in _review_heads(graph)
    )


def _issue29_subject_matches_score_target(
    subject: Any,
    score: ScoreRecord,
) -> bool:
    target = score.target_reference
    expected_owner = "core" if target.target_kind == "core_student" else "concord"
    return bool(
        subject.subject_kind == target.target_kind
        and subject.subject_id == target.target_id
        and subject.owning_system == expected_owner
    )


def _issue29_moderation_scope_applies(
    moderation: ModerationRecord,
    link: ScoreEvidenceLink,
    score: ScoreRecord | None,
) -> bool:
    scope = frozenset(moderation.target_subject_references)
    if not scope:
        return True
    context = frozenset(link.subject_context)
    if context and scope <= context:
        return True
    return (
        score is not None
        and len(scope) == 1
        and _issue29_subject_matches_score_target(next(iter(scope)), score)
    )


def _issue29_moderation_use_matches_target(
    moderation: ModerationRecord,
    score: ScoreRecord | None,
) -> bool:
    if moderation.permitted_use == "support_named_subject":
        return (
            score is not None
            and score.target_reference.target_kind == "core_student"
            and any(
                _issue29_subject_matches_score_target(subject, score)
                for subject in moderation.target_subject_references
            )
        )
    if moderation.permitted_use == "support_group_score":
        return (
            score is not None
            and score.target_reference.target_kind == "concord_group"
            and any(
                _issue29_subject_matches_score_target(subject, score)
                for subject in moderation.target_subject_references
            )
        )
    return True


def _validate_issue29_score_link_moderation(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
    link: ScoreEvidenceLink,
    scores: dict[str, ScoreRecord],
    moderations: dict[str, ModerationRecord],
    artifacts: dict[str, ArtifactInstance],
    pages: dict[str, ArtifactPage],
    *,
    score_is_current: bool,
) -> None:
    moderation = moderations.get(link.moderation_record_id or "")
    current_ids = {
        record.moderation_record_id for record in _moderation_heads(graph)
    }
    score = scores.get(link.score_record_id)

    evidence_requires = link.evidence_reference.moderation_requirement == "required"
    review_requires = _issue29_review_requires_moderation(
        graph,
        link.evidence_reference,
        artifacts,
        pages,
    )
    required = evidence_requires or review_requires
    consequential = score is not None and score.disposition == "scored"
    current_consequential = score_is_current and consequential

    if link.moderation_record_id and moderation is None:
        _issue(
            issues,
            "score.evidence.moderation_missing",
            "Evidence Link references a missing Moderation Record.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )

    current = (
        moderation is not None
        and moderation.moderation_record_id in current_ids
    )
    evidence_matches = (
        moderation is not None
        and moderation.target_evidence_reference == link.evidence_reference
    )
    scope_applies = (
        moderation is not None
        and _issue29_moderation_scope_applies(moderation, link, score)
    )
    target_use_matches = (
        moderation is not None
        and _issue29_moderation_use_matches_target(moderation, score)
    )
    status_satisfies_required = (
        moderation is not None
        and moderation.status in {"accepted", "accepted_with_qualification"}
    )
    scoring_use_allowed = (
        moderation is not None
        and moderation.permitted_use
        not in {"not_be_used_for_scoring", "formative_only"}
    )

    if current_consequential and moderation is not None and not current:
        _issue(
            issues,
            "moderation.current.required",
            "Score Evidence Link references a historical Moderation decision.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )
    if moderation is not None and not evidence_matches:
        _issue(
            issues,
            "moderation.evidence.mismatch",
            "Moderation Record concerns different evidence.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )
    if moderation is not None and not scope_applies:
        _issue(
            issues,
            "moderation.subject_scope.not_applicable",
            "Moderation Subject scope does not apply to this Score evidence use.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )
    if moderation is not None and not target_use_matches:
        _issue(
            issues,
            "moderation.use.target_mismatch",
            "Moderation permitted use does not match the Score target.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )
    if consequential and moderation is not None and not scoring_use_allowed:
        _issue(
            issues,
            "moderation.use.not_permitted",
            "Moderation decision forbids this consequential evidence use.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )

    satisfies_required = (
        (current or not score_is_current)
        and evidence_matches
        and scope_applies
        and target_use_matches
        and status_satisfies_required
        and scoring_use_allowed
    )
    if consequential and required and not satisfies_required:
        _issue(
            issues,
            "score.evidence.moderation_required",
            "Evidence use requires an applicable current Moderation Record.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )
    if (
        consequential
        and required
        and moderation is not None
        and not status_satisfies_required
        and scoring_use_allowed
    ):
        _issue(
            issues,
            "moderation.use.not_permitted",
            "Moderation status does not satisfy required consequential use.",
            "score_evidence_link",
            link.score_evidence_link_id,
            "moderation_record_id",
        )


def _validate_issue30_definition_revisions(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    definitions: tuple[
        tuple[str, tuple[Any, ...], str, str, str, str],
        ...,
    ] = (
        (
            "criterion_set",
            graph.criterion_sets,
            "criterion_set_id",
            "lineage_id",
            "revision",
            "supersedes_criterion_set_id",
        ),
        (
            "scoring_scale",
            graph.scoring_scales,
            "scoring_scale_id",
            "lineage_id",
            "revision",
            "supersedes_scoring_scale_id",
        ),
    )
    for (
        kind,
        records,
        identity_field,
        lineage_field,
        revision_field,
        predecessor_field,
    ) in definitions:
        index = {
            str(getattr(record, identity_field)): record
            for record in records
        }
        superseded = {
            str(getattr(record, predecessor_field))
            for record in records
            if getattr(record, predecessor_field) is not None
        }
        heads: defaultdict[str, list[Any]] = defaultdict(list)
        for record in records:
            record_id = str(getattr(record, identity_field))
            lineage_id = str(getattr(record, lineage_field))
            if record_id not in superseded:
                heads[lineage_id].append(record)
            predecessor_id = getattr(record, predecessor_field)
            if predecessor_id is None:
                continue
            predecessor = index.get(str(predecessor_id))
            if predecessor is None:
                continue
            if getattr(record, lineage_field) != getattr(
                predecessor, lineage_field
            ):
                _issue(
                    issues,
                    f"{kind}.lineage.mismatch",
                    "Definition successor must preserve its lineage.",
                    kind,
                    record_id,
                    lineage_field,
                )
            if (
                getattr(record, revision_field)
                <= getattr(predecessor, revision_field)
            ):
                _issue(
                    issues,
                    f"{kind}.revision.not_advanced",
                    "Successor revision must advance within its lineage.",
                    kind,
                    record_id,
                    revision_field,
                )
        for current in heads.values():
            if len(current) <= 1:
                continue
            for record in current:
                _issue(
                    issues,
                    f"{kind}.current.multiple_heads",
                    "Definition lineage has multiple current heads.",
                    kind,
                    str(getattr(record, identity_field)),
                    lineage_field,
                )


def _issue30_score_revision_correction_exists(
    graph: ConcordRecordGraph,
    predecessor_id: str,
    successor_id: str,
) -> bool:
    return any(
        correction.correction_type == "score_revision"
        and correction.target_reference.record_kind == "score_record"
        and correction.target_reference.record_id == predecessor_id
        and correction.replacement_reference is not None
        and correction.replacement_reference.record_kind == "score_record"
        and correction.replacement_reference.record_id == successor_id
        for correction in graph.correction_records
    )


def _validate_issue30_score_audits(
    issues: list[ValidationIssue],
    graph: ConcordRecordGraph,
) -> None:
    scores = {item.score_record_id: item for item in graph.score_records}
    for correction in graph.correction_records:
        target_kind = correction.target_reference.record_kind
        if (
            correction.correction_type == "score_revision"
            and target_kind != "score_record"
        ) or (
            target_kind == "score_record"
            and correction.correction_type != "score_revision"
        ):
            _issue(
                issues,
                "correction.type.target_mismatch",
                "Score correction type disagrees with its target.",
                "correction",
                correction.correction_id,
                "correction_type",
            )
        if (
            correction.correction_type == "score_revision"
            and (
                correction.replacement_reference is None
                or correction.replacement_reference.record_kind
                != "score_record"
            )
        ):
            _issue(
                issues,
                "correction.replacement.required",
                "Score revision requires a replacement Score reference.",
                "correction",
                correction.correction_id,
                "replacement_reference",
            )

    for score in graph.score_records:
        predecessor_id = score.supersedes_score_record_id
        if predecessor_id is None:
            continue
        predecessor = scores.get(predecessor_id)
        if predecessor is not None:
            before = datetime.fromisoformat(
                predecessor.scored_at.replace("Z", "+00:00")
            )
            after = datetime.fromisoformat(
                score.scored_at.replace("Z", "+00:00")
            )
            if after < before:
                _issue(
                    issues,
                    "score.supersession.time_backwards",
                    "Score successor cannot precede its predecessor.",
                    "score_record",
                    score.score_record_id,
                    "scored_at",
                )
        if not _issue30_score_revision_correction_exists(
            graph,
            predecessor_id,
            score.score_record_id,
        ):
            _issue(
                issues,
                "score.correction.missing",
                "Score successor lacks its exact score_revision audit record.",
                "score_record",
                score.score_record_id,
                "supersedes_score_record_id",
            )

    links = {
        item.score_evidence_link_id: item
        for item in graph.score_evidence_links
    }
    for link in graph.score_evidence_links:
        predecessor_id = link.supersedes_score_evidence_link_id
        if predecessor_id is None:
            continue
        predecessor_link = links.get(predecessor_id)
        if (
            predecessor_link is not None
            and predecessor_link.score_record_id != link.score_record_id
        ):
            _issue(
                issues,
                "score_evidence.supersession.score_mismatch",
                "Evidence Link successor must preserve its parent Score.",
                "score_evidence_link",
                link.score_evidence_link_id,
                "score_record_id",
            )



def collect_record_graph_issues(
    graph: ConcordRecordGraph,
) -> tuple[ValidationIssue, ...]:
    """Return every cross-record issue in deterministic order."""
    if not isinstance(graph, ConcordRecordGraph):
        raise TypeError("graph must be a ConcordRecordGraph.")
    issues: list[ValidationIssue] = []
    activities = _index(graph.activities, "activity_id")
    sessions = _index(graph.sessions, "session_id")
    groups = _index(graph.groups, "group_id")
    memberships = _index(graph.memberships, "membership_id")
    roles = _index(graph.role_assignments, "role_assignment_id")
    packet_instances = _index(graph.packet_instances, "packet_instance_id")
    artifacts = _index(graph.artifact_instances, "artifact_instance_id")
    pages = _index(graph.artifact_pages, "artifact_page_id")
    criteria = _index(graph.criteria, "criterion_id")
    criterion_sets = _index(graph.criterion_sets, "criterion_set_id")
    scales = _index(graph.scoring_scales, "scoring_scale_id")
    scores = _index(graph.score_records, "score_record_id")
    moderations = _index(graph.moderation_records, "moderation_record_id")

    occurrence_targets: dict[tuple[str, int, str], str] = {}
    physical_targets: dict[tuple[str, int], str] = {}
    for scan in graph.scan_references:
        page = pages.get(scan.artifact_page_id)
        artifact = artifacts.get(page.artifact_instance_id) if page else None
        if page is None:
            _issue(
                issues,
                "scan_reference.page.missing",
                "Scan Reference targets a missing Artifact Page.",
                "scan_reference",
                scan.scan_reference_id,
                "artifact_page_id",
            )
        elif artifact is None or artifact.activity_id != scan.activity_id:
            _issue(
                issues,
                "scan_reference.activity.mismatch",
                "Scan Reference and Artifact Page must belong to the same Activity.",
                "scan_reference",
                scan.scan_reference_id,
                "activity_id",
            )
        if page is not None and page.route_id != scan.route_id:
            _issue(
                issues,
                "scan_reference.route.mismatch",
                "Scan Reference route must equal the Artifact Page route.",
                "scan_reference",
                scan.scan_reference_id,
                "route_id",
            )
        occurrence = (scan.source_scan_id, scan.source_page_number, scan.route_id)
        existing = occurrence_targets.setdefault(occurrence, scan.artifact_page_id)
        if (
            existing != scan.artifact_page_id
            or sum(
                (item.source_scan_id, item.source_page_number, item.route_id)
                == occurrence
                for item in graph.scan_references
            )
            > 1
        ):
            _issue(
                issues,
                "scan_reference.occurrence.duplicate",
                "One exact retained physical occurrence must not be filed twice.",
                "scan_reference",
                scan.scan_reference_id,
            )
        physical = (scan.source_scan_id, scan.source_page_number)
        prior_target = physical_targets.setdefault(physical, scan.artifact_page_id)
        if prior_target != scan.artifact_page_id:
            _issue(
                issues,
                "scan_reference.physical_target.contradiction",
                "One retained physical page cannot target contradictory pages.",
                "scan_reference",
                scan.scan_reference_id,
            )

    session_counts = Counter(session.activity_id for session in graph.sessions)
    for activity in graph.activities:
        if session_counts[activity.activity_id] == 0:
            _issue(
                issues,
                "activity.session.required",
                "Activity requires at least one Session.",
                "activity",
                activity.activity_id,
                "activity_id",
            )
        for index, set_id in enumerate(activity.criterion_set_ids):
            if set_id not in criterion_sets:
                _issue(
                    issues,
                    "activity.criterion_set.missing",
                    "Activity references a missing Criterion Set.",
                    "activity",
                    activity.activity_id,
                    "criterion_set_ids",
                    index,
                )
            else:
                criterion_set = criterion_sets[set_id]
                for criterion_id in criterion_set.criterion_ids:
                    activity_criterion = criteria.get(criterion_id)
                    if (
                        activity_criterion is not None
                        and activity_criterion.criterion_kind == "standard_backed"
                        and activity_criterion.standard_id
                        not in activity.focus_standard_ids
                    ):
                        _issue(
                            issues,
                            "criterion.standard.not_focus",
                            "Activity Criterion does not govern a Focus Standard.",
                            "criterion",
                            activity_criterion.criterion_id,
                            "standard_id",
                        )

    for activity_id, activity_sessions in _group_by(
        graph.sessions, "activity_id"
    ).items():
        counts = Counter(session.sequence for session in activity_sessions)
        for session in activity_sessions:
            if counts[session.sequence] > 1:
                _issue(
                    issues,
                    "session.sequence.duplicate",
                    "Session sequence is duplicated within the Activity.",
                    "session",
                    session.session_id,
                    "sequence",
                )
    for session in graph.sessions:
        if session.activity_id not in activities:
            _issue(
                issues,
                "session.activity.missing",
                "Session references a missing Activity.",
                "session",
                session.session_id,
                "activity_id",
            )

    for plan in graph.group_plans:
        plan_activity = activities.get(plan.activity_id)
        if plan_activity is None:
            _issue(
                issues,
                "group_plan.activity.missing",
                "GroupPlan references a missing Activity.",
                "group_plan",
                plan.group_plan_id,
                "activity_id",
            )
        elif plan.class_reference != plan_activity.class_reference:
            _issue(
                issues,
                "group_plan.class.mismatch",
                "GroupPlan Core class differs from its Activity class.",
                "group_plan",
                plan.group_plan_id,
                "class_reference",
            )
        for index, proposed_group in enumerate(plan.proposed_groups):
            context = proposed_group.effective_context
            if context is None:
                continue
            _check_context(
                issues,
                context,
                sessions,
                "group_plan",
                plan.group_plan_id,
            )
            if context.activity_id != plan.activity_id:
                _issue(
                    issues,
                    "group_plan.context.activity_mismatch",
                    "PlannedGroup context belongs to another Activity.",
                    "group_plan",
                    plan.group_plan_id,
                    "proposed_groups",
                    index,
                    "effective_context",
                    "activity_id",
                )

    for group in graph.groups:
        if group.activity_id not in activities:
            _issue(
                issues,
                "group.activity.missing",
                "Group references a missing Activity.",
                "group",
                group.group_id,
                "activity_id",
            )
        if group.parent_group_id:
            parent = groups.get(group.parent_group_id)
            if parent is None:
                _issue(
                    issues,
                    "group.parent.missing",
                    "Parent Group does not exist.",
                    "group",
                    group.group_id,
                    "parent_group_id",
                )
            elif parent.activity_id != group.activity_id:
                _issue(
                    issues,
                    "group.parent.activity_mismatch",
                    "Parent Group belongs to another Activity.",
                    "group",
                    group.group_id,
                    "parent_group_id",
                )
        if group.effective_context is not None:
            _check_context(
                issues, group.effective_context, sessions, "group", group.group_id
            )
            if group.effective_context.activity_id != group.activity_id:
                _issue(
                    issues,
                    "group.context.activity_mismatch",
                    "Group context belongs to another Activity.",
                    "group",
                    group.group_id,
                    "effective_context",
                    "activity_id",
                )
    _check_parent_cycles(issues, graph.groups, groups)

    for membership in graph.memberships:
        membership_group = groups.get(membership.group_id)
        if membership_group is None:
            _issue(
                issues,
                "membership.group.missing",
                "Membership references a missing Group.",
                "group_membership",
                membership.membership_id,
                "group_id",
            )
        elif membership_group.activity_id != membership.effective_context.activity_id:
            _issue(
                issues,
                "membership.activity.mismatch",
                "Membership Group and context disagree on Activity.",
                "group_membership",
                membership.membership_id,
                "effective_context",
                "activity_id",
            )
        _check_context(
            issues,
            membership.effective_context,
            sessions,
            "group_membership",
            membership.membership_id,
        )

    for role in graph.role_assignments:
        _check_context(
            issues,
            role.effective_context,
            sessions,
            "role_assignment",
            role.role_assignment_id,
        )
        if role.activity_id != role.effective_context.activity_id:
            _issue(
                issues,
                "role.context.activity_mismatch",
                "Role and context disagree on Activity.",
                "role_assignment",
                role.role_assignment_id,
                "effective_context",
                "activity_id",
            )
        if role.group_id:
            role_group = groups.get(role.group_id)
            if role_group is None or role_group.activity_id != role.activity_id:
                _issue(
                    issues,
                    "role.group.invalid",
                    "Role Group is missing or belongs to another Activity.",
                    "role_assignment",
                    role.role_assignment_id,
                    "group_id",
                )
        if role.membership_id:
            role_membership = memberships.get(role.membership_id)
            if role_membership is None:
                _issue(
                    issues,
                    "role.membership.missing",
                    "Role references a missing Membership.",
                    "role_assignment",
                    role.role_assignment_id,
                    "membership_id",
                )
            else:
                if role_membership.participant_reference != role.participant_reference:
                    _issue(
                        issues,
                        "role.membership.participant_mismatch",
                        "Role participant differs from Membership participant.",
                        "role_assignment",
                        role.role_assignment_id,
                        "participant_reference",
                    )
                if role.group_id and role_membership.group_id != role.group_id:
                    _issue(
                        issues,
                        "role.membership.group_mismatch",
                        "Role and Membership Groups differ.",
                        "role_assignment",
                        role.role_assignment_id,
                        "group_id",
                    )

    for responsibility in graph.responsibility_assignments:
        _check_context(
            issues,
            responsibility.effective_context,
            sessions,
            "responsibility_assignment",
            responsibility.responsibility_assignment_id,
        )
        if responsibility.activity_id != responsibility.effective_context.activity_id:
            _issue(
                issues,
                "responsibility.context.activity_mismatch",
                "Responsibility and context disagree on Activity.",
                "responsibility_assignment",
                responsibility.responsibility_assignment_id,
                "effective_context",
                "activity_id",
            )
        if responsibility.group_id:
            responsibility_group = groups.get(responsibility.group_id)
            if (
                responsibility_group is None
                or responsibility_group.activity_id != responsibility.activity_id
            ):
                _issue(
                    issues,
                    "responsibility.group.invalid",
                    "Responsibility Group is invalid.",
                    "responsibility_assignment",
                    responsibility.responsibility_assignment_id,
                    "group_id",
                )
        if isinstance(responsibility.assignee_reference, ConcordRecordReference):
            if responsibility.assignee_reference.record_kind != "group":
                _issue(
                    issues,
                    "responsibility.assignee.invalid",
                    "Concord assignee references must identify a Group.",
                    "responsibility_assignment",
                    responsibility.responsibility_assignment_id,
                    "assignee_reference",
                )


    generation_contracts: dict[str, tuple[str, str, str, str]] = {}
    generation_targets: set[tuple[str, object]] = set()
    packet_bound_artifacts: dict[str, str] = {}
    for packet in graph.packet_instances:
        if packet.activity_id not in activities:
            _issue(
                issues,
                "packet_instance.activity.missing",
                "Packet Instance references a missing Activity.",
                "packet_instance",
                packet.packet_instance_id,
                "activity_id",
            )
        packet_session = sessions.get(packet.session_id)
        if packet_session is None or packet_session.activity_id != packet.activity_id:
            _issue(
                issues,
                "packet_instance.session.invalid",
                "Packet Instance Session is missing or belongs to another Activity.",
                "packet_instance",
                packet.packet_instance_id,
                "session_id",
            )
        packet_target = packet.target_context
        if packet_target.group_id is not None:
            packet_group = groups.get(packet_target.group_id)
            if packet_group is None or packet_group.activity_id != packet.activity_id:
                _issue(
                    issues,
                    "packet_instance.packet_target.group_invalid",
                    "Packet target Group is missing or belongs to another Activity.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "target_context",
                    "group_id",
                )
        if packet_target.role_assignment_id is not None:
            packet_role = roles.get(packet_target.role_assignment_id)
            if (
                packet_role is None
                or packet_role.activity_id != packet.activity_id
                or packet_role.participant_reference
                != packet_target.participant_reference
                or packet_role.role_key != packet_target.role_key
                or (
                    packet_target.group_id is not None
                    and packet_role.group_id != packet_target.group_id
                )
            ):
                _issue(
                    issues,
                    "packet_instance.packet_target.role_invalid",
                    "Packet target Role does not match canonical Activity context.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "target_context",
                    "role_assignment_id",
                )

        contract = (
            packet.packet_definition_id,
            packet.packet_version_id,
            packet.activity_id,
            packet.session_id,
        )
        prior_contract = generation_contracts.setdefault(packet.generation_id, contract)
        if prior_contract != contract:
            _issue(
                issues,
                "packet_instance.generation.contract_mismatch",
                "One generation_id must preserve one exact Packet/Activity/Session.",
                "packet_instance",
                packet.packet_instance_id,
                "generation_id",
            )
        target_key = (packet.generation_id, packet.target_context)
        if target_key in generation_targets:
            _issue(
                issues,
                "packet_instance.generation.target_duplicate",
                "One generation_id must not duplicate a concrete Packet packet_target.",
                "packet_instance",
                packet.packet_instance_id,
                "target_context",
            )
        generation_targets.add(target_key)

        for index, binding in enumerate(packet.artifact_bindings):
            artifact = artifacts.get(binding.artifact_instance_id)
            if artifact is None:
                _issue(
                    issues,
                    "packet_instance.artifact.missing",
                    "Packet binding references a missing Artifact Instance.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "artifact_bindings",
                    index,
                    "artifact_instance_id",
                )
                continue
            previous_packet = packet_bound_artifacts.setdefault(
                artifact.artifact_instance_id,
                packet.packet_instance_id,
            )
            if previous_packet != packet.packet_instance_id:
                _issue(
                    issues,
                    "packet_instance.artifact.multiple_packets",
                    "Artifact is bound by more than one Packet Instance.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "artifact_bindings",
                    index,
                    "artifact_instance_id",
                )
            if artifact.packet_instance_id != packet.packet_instance_id:
                _issue(
                    issues,
                    "packet_instance.artifact.packet_mismatch",
                    "Artifact packet_instance_id disagrees with its Packet binding.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "artifact_bindings",
                    index,
                    "artifact_instance_id",
                )
            if (
                artifact.activity_id != packet.activity_id
                or artifact.session_id != packet.session_id
            ):
                _issue(
                    issues,
                    "packet_instance.artifact.context_mismatch",
                    "Packet-bound Artifact belongs to another Activity/Session.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "artifact_bindings",
                    index,
                    "artifact_instance_id",
                )
            if artifact.template_version_id != binding.template_version_id:
                _issue(
                    issues,
                    "packet_instance.artifact.template_mismatch",
                    "Artifact Template Version disagrees with Packet provenance.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "artifact_bindings",
                    index,
                    "template_version_id",
                )
            if (
                packet_target.group_id is not None
                and artifact.group_id != packet_target.group_id
            ):
                _issue(
                    issues,
                    "packet_instance.artifact.group_mismatch",
                    "Packet-bound Artifact Group disagrees with its packet_target.",
                    "packet_instance",
                    packet.packet_instance_id,
                    "artifact_bindings",
                    index,
                    "artifact_instance_id",
                )

    for artifact in graph.artifact_instances:
        packet_id = artifact.packet_instance_id
        if packet_id is None:
            continue
        runtime_packet = packet_instances.get(packet_id)
        if runtime_packet is None:
            continue
        binding_count = sum(
            binding.artifact_instance_id == artifact.artifact_instance_id
            for binding in runtime_packet.artifact_bindings
        )
        if binding_count != 1:
            _issue(
                issues,
                "packet_instance.artifact.unbound",
                "Runtime Packet Artifact must have exactly one provenance binding.",
                "artifact_instance",
                artifact.artifact_instance_id,
                "packet_instance_id",
            )

    route_counts = Counter(
        page.route_id for page in graph.artifact_pages if page.route_id
    )
    page_owners: defaultdict[str, list[str]] = defaultdict(list)
    for artifact in graph.artifact_instances:
        if artifact.activity_id not in activities:
            _issue(
                issues,
                "artifact.activity.missing",
                "Artifact references a missing Activity.",
                "artifact_instance",
                artifact.artifact_instance_id,
                "activity_id",
            )
        if artifact.session_id:
            artifact_session = sessions.get(artifact.session_id)
            if (
                artifact_session is None
                or artifact_session.activity_id != artifact.activity_id
            ):
                _issue(
                    issues,
                    "artifact.session.invalid",
                    "Artifact Session is missing or belongs to another Activity.",
                    "artifact_instance",
                    artifact.artifact_instance_id,
                    "session_id",
                )
        if artifact.group_id:
            artifact_group = groups.get(artifact.group_id)
            if (
                artifact_group is None
                or artifact_group.activity_id != artifact.activity_id
            ):
                _issue(
                    issues,
                    "artifact.group.invalid",
                    "Artifact Group is missing or belongs to another Activity.",
                    "artifact_instance",
                    artifact.artifact_instance_id,
                    "group_id",
                )
        for index, page_id in enumerate(artifact.page_ids):
            page_owners[page_id].append(artifact.artifact_instance_id)
            page = pages.get(page_id)
            if page is None:
                _issue(
                    issues,
                    "artifact.page.missing",
                    "Declared Artifact Page does not exist.",
                    "artifact_instance",
                    artifact.artifact_instance_id,
                    "page_ids",
                    index,
                )
            elif page.artifact_instance_id != artifact.artifact_instance_id:
                _issue(
                    issues,
                    "artifact.page.mismatch",
                    "Artifact Page belongs to another Artifact.",
                    "artifact_instance",
                    artifact.artifact_instance_id,
                    "page_ids",
                    index,
                )
    for page in graph.artifact_pages:
        if page.artifact_instance_id not in artifacts:
            _issue(
                issues,
                "artifact_page.artifact.missing",
                "Page references a missing Artifact.",
                "artifact_page",
                page.artifact_page_id,
                "artifact_instance_id",
            )
        if page.route_id and route_counts[page.route_id] > 1:
            _issue(
                issues,
                "artifact.route.duplicate",
                "Route ID identifies more than one Page.",
                "artifact_page",
                page.artifact_page_id,
                "route_id",
            )
        if len(page_owners[page.artifact_page_id]) > 1:
            _issue(
                issues,
                "artifact.page.multiple_owners",
                "Page is declared by multiple Artifacts.",
                "artifact_page",
                page.artifact_page_id,
                "artifact_instance_id",
            )
        if page.continuation_of_page_id:
            previous = pages.get(page.continuation_of_page_id)
            if (
                previous is None
                or previous.artifact_instance_id != page.artifact_instance_id
            ):
                _issue(
                    issues,
                    "artifact.page.continuation.invalid",
                    "Continuation Page must reference a Page in the same Artifact.",
                    "artifact_page",
                    page.artifact_page_id,
                    "continuation_of_page_id",
                )

    for author in graph.artifact_authors:
        author_artifact = artifacts.get(author.artifact_instance_id)
        if author_artifact is None:
            _issue(
                issues,
                "author.artifact.missing",
                "Author association references a missing Artifact.",
                "artifact_author",
                author.artifact_author_id,
                "artifact_instance_id",
            )
        if author.represented_group_id:
            author_group = groups.get(author.represented_group_id)
            if (
                author_artifact is None
                or author_group is None
                or author_group.activity_id != author_artifact.activity_id
            ):
                _issue(
                    issues,
                    "author.group.invalid",
                    "Represented Group is invalid for the Artifact Activity.",
                    "artifact_author",
                    author.artifact_author_id,
                    "represented_group_id",
                )
        if isinstance(author.author_reference, ConcordRecordReference):
            if author.author_reference.record_kind != "group":
                _issue(
                    issues,
                    "author.reference.invalid",
                    "Concord Author references must identify a Group.",
                    "artifact_author",
                    author.artifact_author_id,
                    "author_reference",
                )
        if author.role_assignment_id:
            author_role = roles.get(author.role_assignment_id)
            if (
                author_role is None
                or author_artifact is None
                or author_role.activity_id != author_artifact.activity_id
            ):
                _issue(
                    issues,
                    "author.role.invalid",
                    "Referenced Role is invalid for the Artifact.",
                    "artifact_author",
                    author.artifact_author_id,
                    "role_assignment_id",
                )
            elif not isinstance(
                author.author_reference, ParticipantReference
            ):
                _issue(
                    issues,
                    "author.role.reference_invalid",
                    "Author Role context requires a Participant Author.",
                    "artifact_author",
                    author.artifact_author_id,
                    "author_reference",
                )
            elif author_role.participant_reference != author.author_reference:
                _issue(
                    issues,
                    "author.role.participant_mismatch",
                    "Author and Role participant differ.",
                    "artifact_author",
                    author.artifact_author_id,
                    "author_reference",
                )

    for subject in graph.artifact_subjects:
        subject_artifact = artifacts.get(subject.artifact_instance_id)
        if subject_artifact is None:
            _issue(
                issues,
                "subject.artifact.missing",
                "Subject association references a missing Artifact.",
                "artifact_subject",
                subject.artifact_subject_id,
                "artifact_instance_id",
            )
        _validate_subject(
            issues,
            subject.subject_reference.subject_kind,
            subject.subject_reference.subject_id,
            subject.subject_reference.owning_system,
            activities,
            sessions,
            groups,
            artifacts,
            "artifact_subject",
            subject.artifact_subject_id,
        )

    _validate_issue28_return_graph(issues, graph, pages)
    _validate_issue28_author_graph(issues, graph, artifacts, groups, roles)
    _validate_issue28_subject_graph(
        issues,
        graph,
        activities,
        sessions,
        groups,
        artifacts,
        criteria,
    )

    for review in graph.artifact_reviews:
        if review.artifact_instance_id not in artifacts:
            _issue(
                issues,
                "review.artifact.missing",
                "Review references a missing Artifact.",
                "artifact_review",
                review.artifact_review_id,
                "artifact_instance_id",
            )
    for moderation in graph.moderation_records:
        _validate_evidence_reference(
            issues,
            moderation.target_evidence_reference,
            artifacts,
            pages,
            "moderation_record",
            moderation.moderation_record_id,
        )
    _validate_issue29_review_graph(issues, graph)
    _validate_issue29_moderation_graph(
        issues,
        graph,
        activities,
        sessions,
        groups,
        artifacts,
        pages,
    )
    _validate_issue29_moderation_reference_integrity(issues, graph)
    _validate_issue29_revision_audits(issues, graph)
    _validate_issue30_definition_revisions(issues, graph)
    _validate_issue30_score_audits(issues, graph)

    for criterion_set in graph.criterion_sets:
        members = [criteria.get(item) for item in criterion_set.criterion_ids]
        for index, criterion in enumerate(members):
            if criterion is None:
                _issue(
                    issues,
                    "criterion_set.criterion.missing",
                    "Criterion Set references a missing Criterion.",
                    "criterion_set",
                    criterion_set.criterion_set_id,
                    "criterion_ids",
                    index,
                )
            elif criterion.criterion_set_id != criterion_set.criterion_set_id:
                _issue(
                    issues,
                    "criterion_set.criterion.mismatch",
                    "Criterion identifies a different parent Set.",
                    "criterion_set",
                    criterion_set.criterion_set_id,
                    "criterion_ids",
                    index,
                )
            elif (
                criterion_set.criterion_set_kind != "mixed"
                and criterion.criterion_kind != criterion_set.criterion_set_kind
            ):
                _issue(
                    issues,
                    "criterion_set.kind.mismatch",
                    "Criterion kind is not allowed by its Set kind.",
                    "criterion_set",
                    criterion_set.criterion_set_id,
                    "criterion_ids",
                    index,
                )
    for criterion in graph.criteria:
        if criterion.criterion_set_id not in criterion_sets:
            _issue(
                issues,
                "criterion.set.missing",
                "Criterion references a missing Criterion Set.",
                "criterion",
                criterion.criterion_id,
                "criterion_set_id",
            )
        if (
            criterion.default_scoring_scale_id
            and criterion.default_scoring_scale_id not in scales
        ):
            _issue(
                issues,
                "criterion.scale.missing",
                "Criterion default Scale does not exist.",
                "criterion",
                criterion.criterion_id,
                "default_scoring_scale_id",
            )

    active_links: defaultdict[str, list[ScoreEvidenceLink]] = defaultdict(list)
    superseded_link_ids = {
        item.supersedes_score_evidence_link_id
        for item in graph.score_evidence_links
        if item.supersedes_score_evidence_link_id is not None
    }
    superseded_score_ids = {
        item.supersedes_score_record_id
        for item in graph.score_records
        if item.supersedes_score_record_id is not None
    }
    for link in graph.score_evidence_links:
        if link.score_record_id not in scores:
            _issue(
                issues,
                "score_evidence.score.missing",
                "Evidence Link references a missing Score.",
                "score_evidence_link",
                link.score_evidence_link_id,
                "score_record_id",
            )
        is_current = link.score_evidence_link_id not in superseded_link_ids
        if is_current and link.status == "active":
            active_links[link.score_record_id].append(link)
        _validate_evidence_reference(
            issues,
            link.evidence_reference,
            artifacts,
            pages,
            "score_evidence_link",
            link.score_evidence_link_id,
        )
        if is_current and link.status == "active":
            _validate_issue29_score_link_moderation(
                issues,
                graph,
                link,
                scores,
                moderations,
                artifacts,
                pages,
                score_is_current=(
                    link.score_record_id not in superseded_score_ids
                ),
            )

    for score_id, score_links in active_links.items():
        source_counts = Counter(
            (
                link.evidence_reference.owning_system,
                link.evidence_reference.record_id,
            )
            for link in score_links
        )
        for link in score_links:
            source_key = (
                link.evidence_reference.owning_system,
                link.evidence_reference.record_id,
            )
            if source_counts[source_key] > 1:
                _issue(
                    issues,
                    "score.evidence.source_duplicate",
                    "One Score uses duplicate representations of an evidence source.",
                    "score_evidence_link",
                    link.score_evidence_link_id,
                    "evidence_reference",
                )

    for score in graph.score_records:
        score_activity = activities.get(score.activity_id)
        criterion = criteria.get(score.criterion_id)
        scale = scales.get(score.scoring_scale_id)
        if score_activity is None:
            _issue(
                issues,
                "score.activity.missing",
                "Score references a missing Activity.",
                "score_record",
                score.score_record_id,
                "activity_id",
            )
        if score.session_id:
            score_session = sessions.get(score.session_id)
            if score_session is None or score_session.activity_id != score.activity_id:
                _issue(
                    issues,
                    "score.session.invalid",
                    "Score Session is missing or belongs to another Activity.",
                    "score_record",
                    score.score_record_id,
                    "session_id",
                )
        target = score.target_reference
        expected_owner = (
            "core" if target.target_kind == "core_student" else "concord"
        )
        if target.owning_system != expected_owner:
            _issue(
                issues,
                "score.target.owner_mismatch",
                "Score target ownership is incompatible with its target kind.",
                "score_record",
                score.score_record_id,
                "target_reference",
                "owning_system",
            )
        if criterion is None:
            _issue(
                issues,
                "score.criterion.missing",
                "Score references a missing Criterion.",
                "score_record",
                score.score_record_id,
                "criterion_id",
            )
        else:
            if criterion.criterion_kind != score.score_kind:
                _issue(
                    issues,
                    "score.kind.mismatch",
                    "Score kind differs from Criterion kind.",
                    "score_record",
                    score.score_record_id,
                    "score_kind",
                )
            if criterion.standard_id != score.standard_id:
                _issue(
                    issues,
                    "score.standard.mismatch",
                    "Score standard differs from Criterion governing standard.",
                    "score_record",
                    score.score_record_id,
                    "standard_id",
                )
            if (
                score.target_reference.target_kind
                not in criterion.supported_target_kinds
            ):
                _issue(
                    issues,
                    "score.target.unsupported",
                    "Criterion does not support this target kind.",
                    "score_record",
                    score.score_record_id,
                    "target_reference",
                    "target_kind",
                )
        if score_activity and criterion is not None:
            if criterion.criterion_set_id not in score_activity.criterion_set_ids:
                _issue(
                    issues,
                    "score.criterion.not_selected",
                    "Score Criterion Set is not selected by the Activity.",
                    "score_record",
                    score.score_record_id,
                    "criterion_id",
                )
        if (
            score.disposition != "scored"
            and score.status_reason is not None
            and score.status_reason.reason_code != score.disposition
        ):
            _issue(
                issues,
                "score.status_reason.mismatch",
                "Non-score StatusReason must match the Score disposition.",
                "score_record",
                score.score_record_id,
                "status_reason",
                "reason_code",
            )
        if score_activity:
            if (
                score.score_kind == "standard_backed"
                and score.standard_id not in score_activity.focus_standard_ids
            ):
                _issue(
                    issues,
                    "criterion.standard.not_focus",
                    "Standard-backed Score is not for an Activity Focus Standard.",
                    "score_record",
                    score.score_record_id,
                    "standard_id",
                )
            if score_activity.scoring_orientation == "evidence_only":
                _issue(
                    issues,
                    "activity.score.forbidden",
                    "Evidence-only Activity cannot contain Scores.",
                    "score_record",
                    score.score_record_id,
                    "activity_id",
                )
            if (
                score_activity.scoring_orientation == "local_criteria_only"
                and score.score_kind == "standard_backed"
            ):
                _issue(
                    issues,
                    "activity.standard_score.forbidden",
                    "Local-criteria-only Activity cannot contain "
                    "standard-backed Scores.",
                    "score_record",
                    score.score_record_id,
                    "score_kind",
                )
            if (
                score_activity.scoring_orientation == "standards_based"
                and score.score_kind == "local"
            ):
                _issue(
                    issues,
                    "activity.local_score.forbidden",
                    "Standards-based Activity cannot contain local Scores.",
                    "score_record",
                    score.score_record_id,
                    "score_kind",
                )
        if scale is None:
            _issue(
                issues,
                "score.scale.missing",
                "Score references a missing Scale revision.",
                "score_record",
                score.score_record_id,
                "scoring_scale_id",
            )
        elif (
            score.disposition == "scored"
            and score.value is not None
            and scale.level_for_value(score.value) is None
        ):
            _issue(
                issues,
                "score.value.invalid",
                "Score value is absent from the exact Scale revision.",
                "score_record",
                score.score_record_id,
                "value",
            )
        _validate_score_target(issues, score, activities, sessions, groups, artifacts)
        count = len(active_links[score.score_record_id])
        if score.basis == "linked_evidence" and count == 0:
            _issue(
                issues,
                "score.evidence.required",
                "Linked-evidence basis requires an active Evidence Link.",
                "score_record",
                score.score_record_id,
                "basis",
            )
        elif score.basis == "professional_judgment" and count != 0:
            _issue(
                issues,
                "score.evidence.forbidden",
                "Professional judgment requires zero active Evidence Links.",
                "score_record",
                score.score_record_id,
                "basis",
            )
        elif score.basis == "mixed_basis" and count == 0:
            _issue(
                issues,
                "score.evidence.required",
                "Mixed basis requires an active Evidence Link.",
                "score_record",
                score.score_record_id,
                "basis",
            )

    for collection_name, _, kind, id_field in _COLLECTIONS:
        values = tuple(getattr(graph, collection_name))
        predecessor_field = (
            next(
                (
                    model_field.name
                    for model_field in fields(values[0])
                    if model_field.name.startswith("supersedes_")
                ),
                None,
            )
            if values
            else None
        )
        if predecessor_field:
            _validate_supersession(issues, values, kind, id_field, predecessor_field)
    _validate_correction_replacements(issues, graph)
    _validate_issue28_correction_types(issues, graph)
    _validate_issue29_correction_types(issues, graph)
    return tuple(sorted(issues, key=lambda item: item.sort_key))


def validate_record_graph(graph: ConcordRecordGraph) -> None:
    issues = collect_record_graph_issues(graph)
    if issues:
        raise ConcordRecordGraphError(issues)


def collect_core_standards_issues(
    graph: ConcordRecordGraph, library: StandardsLibrary
) -> tuple[ValidationIssue, ...]:
    """Validate caller-supplied Core standards without loading or mutating storage."""
    issues: list[ValidationIssue] = []
    standards = {item.standard_id: item for item in library.standards}
    profiles = {item.profile_id: item for item in library.profiles}
    for activity in graph.activities:
        if activity.standards_profile_id is None:
            continue
        profile = profiles.get(activity.standards_profile_id)
        if profile is None:
            _issue(
                issues,
                "standards.profile.missing",
                "Core standards profile does not exist.",
                "activity",
                activity.activity_id,
                "standards_profile_id",
            )
            continue
        try:
            resolve_profile_standard_selection(
                library,
                profile_id=profile.profile_id,
                selected_standard_ids=activity.focus_standard_ids,
            )
        except ValueError:
            for index, standard_id in enumerate(activity.focus_standard_ids):
                if standard_id not in standards:
                    code = "standards.standard.missing"
                elif standard_id not in profile.standards:
                    code = "standards.standard.outside_profile"
                else:
                    continue
                _issue(
                    issues,
                    code,
                    "Focus Standard is unavailable in the selected profile.",
                    "activity",
                    activity.activity_id,
                    "focus_standard_ids",
                    index,
                )
        for index, standard_id in enumerate(activity.focus_standard_ids):
            definition = standards.get(standard_id)
            if definition and not definition.active:
                _issue(
                    issues,
                    "standards.standard.inactive",
                    "Focus Standard is inactive.",
                    "activity",
                    activity.activity_id,
                    "focus_standard_ids",
                    index,
                )
            if definition and "deprecated" in definition.tags:
                _issue(
                    issues,
                    "standards.standard.deprecated",
                    "Focus Standard is deprecated.",
                    "activity",
                    activity.activity_id,
                    "focus_standard_ids",
                    index,
                )
        for set_id in activity.criterion_set_ids:
            criterion_set = next(
                (
                    item
                    for item in graph.criterion_sets
                    if item.criterion_set_id == set_id
                ),
                None,
            )
            if (
                criterion_set
                and criterion_set.standards_profile_id
                and criterion_set.standards_profile_id != profile.profile_id
            ):
                _issue(
                    issues,
                    "standards.criterion.profile_mismatch",
                    "Criterion Set is bound to another standards profile.",
                    "criterion_set",
                    criterion_set.criterion_set_id,
                    "standards_profile_id",
                )
            if criterion_set:
                for criterion_id in criterion_set.criterion_ids:
                    criterion = next(
                        (
                            item
                            for item in graph.criteria
                            if item.criterion_id == criterion_id
                        ),
                        None,
                    )
                    if criterion is None or criterion.standard_id is None:
                        continue
                    if criterion.standard_id not in standards:
                        code = "standards.criterion.standard_missing"
                    elif criterion.standard_id not in profile.standards:
                        code = "standards.criterion.outside_profile"
                    elif not standards[criterion.standard_id].active:
                        code = "standards.criterion.inactive"
                    elif "deprecated" in standards[criterion.standard_id].tags:
                        code = "standards.criterion.deprecated"
                    else:
                        continue
                    _issue(
                        issues,
                        code,
                        "Criterion governing Standard is unavailable in the profile.",
                        "criterion",
                        criterion.criterion_id,
                        "standard_id",
                    )
    return tuple(sorted(issues, key=lambda item: item.sort_key))


def validate_core_standards(
    graph: ConcordRecordGraph, library: StandardsLibrary
) -> None:
    issues = collect_core_standards_issues(graph, library)
    if issues:
        raise ConcordRecordGraphError(issues)


def _group_by(values: Iterable[T], attribute: str) -> dict[str, list[T]]:
    result: defaultdict[str, list[T]] = defaultdict(list)
    for value in values:
        result[str(getattr(value, attribute))].append(value)
    return dict(result)


def _check_parent_cycles(
    issues: list[ValidationIssue], values: tuple[Group, ...], index: dict[str, Group]
) -> None:
    for group in values:
        seen: set[str] = set()
        current: Group | None = group
        while current and current.parent_group_id:
            if current.group_id in seen or current.parent_group_id == group.group_id:
                _issue(
                    issues,
                    "group.parent.cycle",
                    "Group parent graph contains a cycle.",
                    "group",
                    group.group_id,
                    "parent_group_id",
                )
                break
            seen.add(current.group_id)
            current = index.get(current.parent_group_id)


def _validate_subject(
    issues: list[ValidationIssue],
    kind: str,
    record_id: str,
    owner: str,
    activities: dict[str, Activity],
    sessions: dict[str, Session],
    groups: dict[str, Group],
    artifacts: dict[str, ArtifactInstance],
    record_kind: str,
    association_id: str,
) -> None:
    targets: dict[str, dict[str, Any]] = {
        "concord_activity": activities,
        "concord_session": sessions,
        "concord_group": groups,
        "concord_artifact_instance": artifacts,
    }
    if kind.startswith("concord_") and (
        owner != "concord" or record_id not in targets[kind]
    ):
        _issue(
            issues,
            "subject.reference.invalid",
            "Concord Subject is missing or has the wrong owner.",
            record_kind,
            association_id,
            "subject_reference",
        )


def _validate_evidence_reference(
    issues: list[ValidationIssue],
    reference: Any,
    artifacts: dict[str, ArtifactInstance],
    pages: dict[str, ArtifactPage],
    kind: str,
    record_id: str,
) -> None:
    if reference.owning_system == "concord":
        target = (
            artifacts
            if reference.evidence_kind == "artifact_instance"
            else pages
            if reference.evidence_kind == "artifact_page"
            else None
        )
        if target is not None and reference.record_id not in target:
            _issue(
                issues,
                "evidence.reference.missing",
                "Concord-owned evidence does not resolve.",
                kind,
                record_id,
                "evidence_reference",
            )


def _validate_score_target(
    issues: list[ValidationIssue],
    score: ScoreRecord,
    activities: dict[str, Activity],
    sessions: dict[str, Session],
    groups: dict[str, Group],
    artifacts: dict[str, ArtifactInstance],
) -> None:
    ref = score.target_reference
    targets: dict[str, dict[str, Any]] = {
        "concord_activity": activities,
        "concord_session": sessions,
        "concord_group": groups,
        "concord_artifact_instance": artifacts,
    }
    if ref.target_kind.startswith("concord_"):
        target = targets[ref.target_kind].get(ref.target_id)
        if ref.owning_system != "concord" or target is None:
            _issue(
                issues,
                "score.target.missing",
                "Concord Score target does not resolve.",
                "score_record",
                score.score_record_id,
                "target_reference",
            )
            return
        target_activity_id = target.activity_id
        if target_activity_id != score.activity_id:
            _issue(
                issues,
                "score.target.activity_mismatch",
                "Score target belongs to another Activity.",
                "score_record",
                score.score_record_id,
                "target_reference",
            )


def _validate_supersession(
    issues: list[ValidationIssue],
    values: tuple[Any, ...],
    kind: str,
    id_field: str,
    predecessor_field: str,
) -> None:
    index = {getattr(value, id_field): value for value in values}
    successors: defaultdict[str, list[Any]] = defaultdict(list)
    for value in values:
        predecessor_id = getattr(value, predecessor_field)
        record_id = getattr(value, id_field)
        if predecessor_id is None:
            continue
        if predecessor_id == record_id:
            _issue(
                issues,
                "supersession.self",
                "Record cannot supersede itself.",
                kind,
                record_id,
                predecessor_field,
            )
        elif predecessor_id not in index:
            _issue(
                issues,
                "supersession.predecessor_missing",
                "Superseded predecessor does not exist.",
                kind,
                record_id,
                predecessor_field,
            )
        successors[predecessor_id].append(value)
        if predecessor_id in index:
            predecessor = index[predecessor_id]
            stable_fields: dict[str, tuple[str, ...]] = {
                "group": ("activity_id",),
                "group_membership": ("participant_reference",),
                "role_assignment": ("activity_id",),
                "responsibility_assignment": ("activity_id",),
                "artifact_instance": ("activity_id",),
                "artifact_author": ("artifact_instance_id",),
                "artifact_subject": ("artifact_instance_id",),
                "artifact_review": ("artifact_instance_id",),
                "moderation_record": (
                    "target_evidence_reference",
                    "target_subject_references",
                ),
                "criterion_set": ("lineage_id",),
                "scoring_scale": ("lineage_id",),
                "score_record": ("activity_id",),
                "score_evidence_link": ("score_record_id",),
            }
            if any(
                getattr(predecessor, field_name) != getattr(value, field_name)
                for field_name in stable_fields.get(kind, ())
            ):
                _issue(
                    issues,
                    "supersession.context_mismatch",
                    "Successor changes the stable context of its predecessor.",
                    kind,
                    record_id,
                    predecessor_field,
                )
        time_fields = {
            "score_record": "scored_at",
            "artifact_review": "reviewed_at",
            "moderation_record": "moderated_at",
        }
        time_field = time_fields.get(kind)
        if time_field is not None and predecessor_id in index:
            before_value = getattr(index[predecessor_id], time_field)
            after_value = getattr(value, time_field)
            before = datetime.fromisoformat(before_value.replace("Z", "+00:00"))
            after = datetime.fromisoformat(after_value.replace("Z", "+00:00"))
            if after < before:
                _issue(
                    issues,
                    "supersession.time.backward",
                    "Successor decision time precedes predecessor.",
                    kind,
                    record_id,
                    time_field,
                )
    for predecessor_id, following in successors.items():
        if len(following) > 1:
            for value in following:
                _issue(
                    issues,
                    "supersession.branch",
                    "One predecessor has multiple successors.",
                    kind,
                    getattr(value, id_field),
                    predecessor_field,
                )
    for value in values:
        seen: set[str] = set()
        current = value
        while current is not None:
            record_id = getattr(current, id_field)
            if record_id in seen:
                _issue(
                    issues,
                    "supersession.cycle",
                    "Supersession chain contains a cycle.",
                    kind,
                    getattr(value, id_field),
                    predecessor_field,
                )
                break
            seen.add(record_id)
            predecessor_id = getattr(current, predecessor_field)
            current = index.get(predecessor_id) if predecessor_id else None


def _validate_correction_replacements(
    issues: list[ValidationIssue], graph: ConcordRecordGraph
) -> None:
    records: dict[tuple[str, str], Any] = {}
    for collection_name, _, kind, id_field in _COLLECTIONS:
        for value in getattr(graph, collection_name):
            records[(kind, getattr(value, id_field))] = value
    for correction in graph.correction_records:
        if (
            correction.target_reference.record_kind,
            correction.target_reference.record_id,
        ) not in records:
            _issue(
                issues,
                "correction.target.missing",
                "Correction target does not exist.",
                "correction",
                correction.correction_id,
                "target_reference",
            )
        replacement = correction.replacement_reference
        if replacement is None:
            continue
        if replacement.record_kind != correction.target_reference.record_kind:
            _issue(
                issues,
                "correction.replacement.kind_mismatch",
                "Correction replacement must have the target record kind.",
                "correction",
                correction.correction_id,
                "replacement_reference",
            )
        successor = records.get((replacement.record_kind, replacement.record_id))
        if successor is None:
            _issue(
                issues,
                "correction.replacement.missing",
                "Correction replacement does not exist.",
                "correction",
                correction.correction_id,
                "replacement_reference",
            )
            continue
        predecessor_fields = [
            field.name
            for field in fields(successor)
            if field.name.startswith("supersedes_")
        ]
        if (
            not predecessor_fields
            or getattr(successor, predecessor_fields[0])
            != correction.target_reference.record_id
        ):
            _issue(
                issues,
                "correction.replacement.mismatch",
                "Replacement does not supersede the Correction target.",
                "correction",
                correction.correction_id,
                "replacement_reference",
            )


__all__ = [
    "ConcordRecordGraph",
    "collect_core_standards_issues",
    "collect_record_graph_issues",
    "validate_core_standards",
    "validate_record_graph",
]
