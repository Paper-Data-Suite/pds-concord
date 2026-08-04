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
    ModerationRecord,
    ResponsibilityAssignment,
    RoleAssignment,
    ScoreEvidenceLink,
    ScoreRecord,
    ScoringScale,
    Session,
)
from concord.validation_diagnostics import ConcordRecordGraphError, ValidationIssue

Record = (
    Activity
    | Session
    | Group
    | GroupMembership
    | RoleAssignment
    | ResponsibilityAssignment
    | ArtifactInstance
    | ArtifactPage
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

_COLLECTIONS: tuple[tuple[str, type[Any], str, str], ...] = (
    ("activities", Activity, "activity", "activity_id"),
    ("sessions", Session, "session", "session_id"),
    ("groups", Group, "group", "group_id"),
    ("memberships", GroupMembership, "group_membership", "membership_id"),
    ("role_assignments", RoleAssignment, "role_assignment", "role_assignment_id"),
    (
        "responsibility_assignments",
        ResponsibilityAssignment,
        "responsibility_assignment",
        "responsibility_assignment_id",
    ),
    (
        "artifact_instances",
        ArtifactInstance,
        "artifact_instance",
        "artifact_instance_id",
    ),
    ("artifact_pages", ArtifactPage, "artifact_page", "artifact_page_id"),
    ("artifact_authors", ArtifactAuthor, "artifact_author", "artifact_author_id"),
    ("artifact_subjects", ArtifactSubject, "artifact_subject", "artifact_subject_id"),
    ("artifact_reviews", ArtifactReview, "artifact_review", "artifact_review_id"),
    (
        "moderation_records",
        ModerationRecord,
        "moderation_record",
        "moderation_record_id",
    ),
    ("criterion_sets", CriterionSet, "criterion_set", "criterion_set_id"),
    ("criteria", Criterion, "criterion", "criterion_id"),
    ("scoring_scales", ScoringScale, "scoring_scale", "scoring_scale_id"),
    ("score_records", ScoreRecord, "score_record", "score_record_id"),
    (
        "score_evidence_links",
        ScoreEvidenceLink,
        "score_evidence_link",
        "score_evidence_link_id",
    ),
    ("correction_records", CorrectionRecord, "correction", "correction_id"),
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcordRecordGraph:
    activities: tuple[Activity, ...] = ()
    sessions: tuple[Session, ...] = ()
    groups: tuple[Group, ...] = ()
    memberships: tuple[GroupMembership, ...] = ()
    role_assignments: tuple[RoleAssignment, ...] = ()
    responsibility_assignments: tuple[ResponsibilityAssignment, ...] = ()
    artifact_instances: tuple[ArtifactInstance, ...] = ()
    artifact_pages: tuple[ArtifactPage, ...] = ()
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
    artifacts = _index(graph.artifact_instances, "artifact_instance_id")
    pages = _index(graph.artifact_pages, "artifact_page_id")
    criteria = _index(graph.criteria, "criterion_id")
    criterion_sets = _index(graph.criterion_sets, "criterion_set_id")
    scales = _index(graph.scoring_scales, "scoring_scale_id")
    scores = _index(graph.score_records, "score_record_id")
    moderations = _index(graph.moderation_records, "moderation_record_id")

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
            elif (
                hasattr(author.author_reference, "participant_id")
                and author_role.participant_reference.participant_id
                != author.author_reference.participant_id
            ):
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
        if link.status == "active":
            active_links[link.score_record_id].append(link)
        _validate_evidence_reference(
            issues,
            link.evidence_reference,
            artifacts,
            pages,
            "score_evidence_link",
            link.score_evidence_link_id,
        )
        if link.evidence_reference.moderation_requirement == "required":
            link_moderation = moderations.get(link.moderation_record_id or "")
            if link_moderation is None:
                _issue(
                    issues,
                    "score.evidence.moderation_required",
                    "Evidence use requires an applicable Moderation Record.",
                    "score_evidence_link",
                    link.score_evidence_link_id,
                    "moderation_record_id",
                )
            elif link_moderation.status not in {
                "accepted",
                "accepted_with_qualification",
            } or link_moderation.permitted_use in {
                "not_be_used_for_scoring",
                "formative_only",
            }:
                _issue(
                    issues,
                    "moderation.use.not_permitted",
                    "Moderation decision does not permit this "
                    "consequential evidence use.",
                    "score_evidence_link",
                    link.score_evidence_link_id,
                    "moderation_record_id",
                )
        if link.moderation_record_id and link.moderation_record_id not in moderations:
            _issue(
                issues,
                "score.evidence.moderation_missing",
                "Evidence Link references a missing Moderation Record.",
                "score_evidence_link",
                link.score_evidence_link_id,
                "moderation_record_id",
            )
        elif link.moderation_record_id:
            link_moderation = moderations[link.moderation_record_id]
            if link_moderation.target_evidence_reference != link.evidence_reference:
                _issue(
                    issues,
                    "moderation.evidence.mismatch",
                    "Moderation Record concerns different evidence.",
                    "score_evidence_link",
                    link.score_evidence_link_id,
                    "moderation_record_id",
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
                "group_membership": ("group_id",),
                "role_assignment": ("activity_id",),
                "responsibility_assignment": ("activity_id",),
                "artifact_instance": ("activity_id",),
                "artifact_author": ("artifact_instance_id",),
                "artifact_subject": ("artifact_instance_id",),
                "artifact_review": ("artifact_instance_id",),
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
        if kind == "score_record" and predecessor_id in index:
            before = datetime.fromisoformat(
                index[predecessor_id].scored_at.replace("Z", "+00:00")
            )
            after = datetime.fromisoformat(value.scored_at.replace("Z", "+00:00"))
            if after < before:
                _issue(
                    issues,
                    "supersession.time.backward",
                    "Successor Score time precedes predecessor.",
                    kind,
                    record_id,
                    "scored_at",
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
