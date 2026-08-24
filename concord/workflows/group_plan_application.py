"""Preparation and atomic application for one approved GroupPlan."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path

from pds_core.standards import StandardsLibrary

from concord.group_plan_application import (
    ApplicationGroupSpec,
    ApplicationMembershipSpec,
    GroupPlanApplicationError,
    application_digest,
    build_application_manifest,
    derive_application_specs,
    new_application_id,
)
from concord.model_validation import ConcordRecordGraph, collect_record_graph_issues
from concord.models import (
    EffectiveContext,
    Group,
    GroupMembership,
    GroupPlan,
    Provenance,
)
from concord.storage import commit_record_batch, load_current_snapshot
from concord.workflows._collaboration import (
    load_graph,
    require_new_identity,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.group import (
    _ensure_membership_context_available,
    _require_membership_within_group_context,
)
from concord.workflows.group_plan import show_group_plan
from concord.workflows.group_plan_missing_signal import (
    inspect_group_plan_missing_signal,
)
from concord.workflows.models import WorkflowActor, WorkflowCommitResult
from concord.workflows.participants import (
    core_student_participant,
    load_required_roster,
)

_SIGNAL_STRATEGIES = frozenset({"similar_signal", "mixed_signal"})
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareGroupPlanApplicationRequest:
    """Prepare one exact zero-write application preview."""

    class_id: str
    activity_id: str
    group_plan_id: str
    application_id: str | None = None
    fallback_effective_context: EffectiveContext | None = None


@dataclass(frozen=True, slots=True)
class GroupPlanApplicationPreview:
    """Exact canonical write-set preview for one approved GroupPlan."""

    application_id: str
    application_digest: str
    class_id: str
    activity_id: str
    group_plan_id: str
    group_plan_record_revision: int
    expected_snapshot_revision: int
    fallback_effective_context: EffectiveContext | None
    groups: tuple[ApplicationGroupSpec, ...]
    memberships: tuple[ApplicationMembershipSpec, ...]
    unresolved_student_ids: tuple[str, ...]

    @property
    def group_count(self) -> int:
        return len(self.groups)

    @property
    def membership_count(self) -> int:
        return len(self.memberships)

    @property
    def unresolved_count(self) -> int:
        return len(self.unresolved_student_ids)


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplyGroupPlanRequest:
    """Apply exactly one previously prepared approved GroupPlan preview."""

    class_id: str
    activity_id: str
    group_plan_id: str
    application_id: str
    application_digest: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    fallback_effective_context: EffectiveContext | None = None


@dataclass(frozen=True, slots=True)
class GroupPlanApplicationResult:
    """Bounded result of one atomic approved-to-applied transition."""

    commit: WorkflowCommitResult
    group_plan_id: str
    status: str
    application_id: str
    application_digest: str
    group_ids: tuple[str, ...]
    membership_ids: tuple[str, ...]
    unresolved_count: int

    @property
    def group_count(self) -> int:
        return len(self.group_ids)

    @property
    def membership_count(self) -> int:
        return len(self.membership_ids)


def _required_root(workspace_root: str | Path | None) -> Path:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            "Paper Data Suite workspace does not exist."
        )
    return root


def _roster_student_ids(root: Path, class_id: str) -> tuple[str, ...]:
    roster = load_required_roster(root, class_id)
    return tuple(sorted(student.student_id for student in roster.students))


def _require_plan_application_state(
    root: Path,
    plan: GroupPlan,
    *,
    class_id: str,
    activity_id: str,
    snapshot_revision: int,
) -> None:
    if plan.status == "applied":
        raise ConcordWorkflowConflictError("GroupPlan has already been applied.")
    if plan.status != "approved":
        raise ConcordWorkflowConflictError(
            "Only an approved GroupPlan may be prepared for application."
        )
    if plan.activity_id != activity_id or plan.class_reference.record_id != class_id:
        raise ConcordWorkflowValidationError(
            "GroupPlan identity does not match the selected class and Activity."
        )

    roster = _roster_student_ids(root, class_id)
    if roster != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed since this GroupPlan was approved."
        )

    if plan.strategy in _SIGNAL_STRATEGIES:
        inspection = inspect_group_plan_missing_signal(
            class_id,
            activity_id,
            plan.group_plan_id,
            workspace_root=root,
        )
        if inspection.detail.summary.snapshot_revision != snapshot_revision:
            raise ConcordWorkflowConflictError(
                "Activity changed while revalidating the GroupPlan signal binding."
            )
        if inspection.detail.plan != plan:
            raise ConcordWorkflowConflictError(
                "GroupPlan changed while revalidating its signal binding."
            )
        missing = inspection.missing_student_ids
        if missing:
            disposition = plan.missing_signal_disposition
            if disposition is None:
                raise ConcordWorkflowValidationError(
                    "Signal-backed GroupPlan application requires the approved "
                    "missing-signal disposition to remain valid."
                )
            if disposition in {"manual", "random"}:
                if plan.unresolved_student_ids:
                    raise ConcordWorkflowValidationError(
                        "Manual/random missing-signal disposition requires every "
                        "roster student to remain resolved at application."
                    )
            elif disposition == "leave_unassigned":
                if set(plan.unresolved_student_ids) != set(missing):
                    raise ConcordWorkflowValidationError(
                        "leave_unassigned application requires unresolved students "
                        "to exactly equal the current missing-signal population."
                    )
            else:
                raise ConcordWorkflowValidationError(
                    "Signal-backed GroupPlan has an invalid missing-signal disposition."
                )
        elif plan.unresolved_student_ids:
            raise ConcordWorkflowValidationError(
                "GroupPlan application requires every roster student to be resolved."
            )
    elif plan.unresolved_student_ids:
        raise ConcordWorkflowValidationError(
            "GroupPlan application requires every roster student to be resolved."
        )

    if _roster_student_ids(root, class_id) != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed while preparing GroupPlan application."
        )


def _native_candidate_records(
    *,
    root: Path,
    class_id: str,
    plan: GroupPlan,
    graph: ConcordRecordGraph,
    groups: tuple[ApplicationGroupSpec, ...],
    memberships: tuple[ApplicationMembershipSpec, ...],
    created_provenance: Provenance,
) -> tuple[tuple[Group, ...], tuple[GroupMembership, ...]]:
    native_groups: list[Group] = []
    groups_by_id: dict[str, Group] = {}
    for group_spec in groups:
        require_new_identity(
            graph.groups,
            "group_id",
            group_spec.group_id,
            "Group",
        )
        group_candidate = Group(
            group_id=group_spec.group_id,
            activity_id=plan.activity_id,
            label=group_spec.label,
            status="planned",
            created_provenance=created_provenance,
            description=group_spec.description,
            parent_group_id=None,
            effective_context=group_spec.effective_context,
        )
        native_groups.append(group_candidate)
        groups_by_id[group_candidate.group_id] = group_candidate

    native_memberships: list[GroupMembership] = []
    for membership_spec in memberships:
        require_new_identity(
            graph.memberships,
            "membership_id",
            membership_spec.membership_id,
            "Group Membership",
        )
        group = groups_by_id.get(membership_spec.group_id)
        if group is None:
            raise ConcordWorkflowValidationError(
                "Application Membership references an unknown derived Group."
            )
        membership_candidate = GroupMembership(
            membership_id=membership_spec.membership_id,
            group_id=membership_spec.group_id,
            participant_reference=core_student_participant(
                root,
                class_id,
                membership_spec.student_id,
            ),
            effective_context=membership_spec.effective_context,
            status="active",
            created_provenance=created_provenance,
        )
        _require_membership_within_group_context(
            graph,
            group,
            membership_candidate,
        )
        _ensure_membership_context_available(
            graph,
            tuple(graph.memberships) + tuple(native_memberships),
            membership_candidate,
        )
        native_memberships.append(membership_candidate)

    candidate_graph = replace(
        graph,
        groups=(*graph.groups, *native_groups),
        memberships=(*graph.memberships, *native_memberships),
    )
    issues = collect_record_graph_issues(candidate_graph)
    if issues:
        details = "; ".join(
            f"{issue.code}: {issue.message}" for issue in issues[:5]
        )
        raise ConcordWorkflowValidationError(
            "Native Group/Membership application candidate is invalid: " + details
        )
    return tuple(native_groups), tuple(native_memberships)


def prepare_group_plan_application(
    request: PrepareGroupPlanApplicationRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> GroupPlanApplicationPreview:
    """Prepare the exact application write set without mutating Concord state."""

    root = _required_root(workspace_root)
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    detail = show_group_plan(
        request.class_id,
        request.activity_id,
        request.group_plan_id,
        workspace_root=root,
    )
    if detail.summary.snapshot_revision != snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Activity changed while loading the GroupPlan application preview."
        )
    plan = detail.plan
    _require_plan_application_state(
        root,
        plan,
        class_id=request.class_id,
        activity_id=request.activity_id,
        snapshot_revision=snapshot_revision,
    )

    if (
        request.fallback_effective_context is not None
        and request.fallback_effective_context.activity_id != request.activity_id
    ):
        raise ConcordWorkflowValidationError(
            "Fallback Membership Effective Context must identify the selected Activity."
        )

    application_id = request.application_id or new_application_id()
    try:
        groups, memberships = derive_application_specs(
            application_id=application_id,
            group_plan_id=plan.group_plan_id,
            proposed_groups=plan.proposed_groups,
            fallback_effective_context=request.fallback_effective_context,
        )
    except GroupPlanApplicationError as error:
        raise ConcordWorkflowValidationError(str(error)) from error

    approval_provenance = plan.approved_provenance
    if approval_provenance is None:
        raise ConcordWorkflowValidationError(
            "Approved GroupPlan is missing approval provenance."
        )
    _native_candidate_records(
        root=root,
        class_id=request.class_id,
        plan=plan,
        graph=graph,
        groups=groups,
        memberships=memberships,
        created_provenance=approval_provenance,
    )

    if _roster_student_ids(root, request.class_id) != plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed while validating GroupPlan application candidates."
        )
    current = load_current_snapshot(root, work)
    if current.snapshot_revision != snapshot_revision:
        raise ConcordWorkflowConflictError(
            "Activity changed while preparing the GroupPlan application preview."
        )

    manifest = build_application_manifest(
        application_id=application_id,
        class_id=request.class_id,
        activity_id=request.activity_id,
        group_plan_id=plan.group_plan_id,
        group_plan_record_revision=detail.record_revision,
        expected_snapshot_revision=snapshot_revision,
        fallback_effective_context=request.fallback_effective_context,
        groups=groups,
        memberships=memberships,
        unresolved_student_ids=plan.unresolved_student_ids,
    )
    return GroupPlanApplicationPreview(
        application_id=application_id,
        application_digest=application_digest(manifest),
        class_id=request.class_id,
        activity_id=request.activity_id,
        group_plan_id=plan.group_plan_id,
        group_plan_record_revision=detail.record_revision,
        expected_snapshot_revision=snapshot_revision,
        fallback_effective_context=request.fallback_effective_context,
        groups=groups,
        memberships=memberships,
        unresolved_student_ids=plan.unresolved_student_ids,
    )


def _plan_from_graph(graph: ConcordRecordGraph, group_plan_id: str) -> GroupPlan:
    for plan in graph.group_plans:
        if plan.group_plan_id == group_plan_id:
            return plan
    raise ConcordWorkflowNotFoundError(
        f"GroupPlan is not available: {group_plan_id}"
    )


def _require_expected_snapshot(actual: int, expected: int) -> None:
    if type(expected) is not int or expected < 1:
        raise ConcordWorkflowValidationError(
            "expected_snapshot_revision must be a positive integer."
        )
    if actual != expected:
        raise ConcordWorkflowConflictError(
            "Activity changed since the application preview; prepare it again."
        )


def _require_application_digest(value: str) -> None:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ConcordWorkflowValidationError(
            "application_digest must be lowercase 64-character SHA-256 hex."
        )


def _validate_complete_application_graph(
    graph: ConcordRecordGraph,
    applied_plan: GroupPlan,
    groups: tuple[Group, ...],
    memberships: tuple[GroupMembership, ...],
) -> None:
    candidate = replace(
        graph,
        group_plans=tuple(
            applied_plan if item.group_plan_id == applied_plan.group_plan_id else item
            for item in graph.group_plans
        ),
        groups=(*graph.groups, *groups),
        memberships=(*graph.memberships, *memberships),
    )
    issues = collect_record_graph_issues(candidate)
    if issues:
        details = "; ".join(
            f"{issue.code}: {issue.message}" for issue in issues[:5]
        )
        raise ConcordWorkflowValidationError(
            "Complete GroupPlan application candidate is invalid: " + details
        )


def apply_group_plan(
    request: ApplyGroupPlanRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> GroupPlanApplicationResult:
    """Atomically create canonical Groups/Memberships and mark the plan applied."""

    _require_application_digest(request.application_digest)
    root = _required_root(workspace_root)
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)

    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    current_plan = _plan_from_graph(graph, request.group_plan_id)
    if current_plan.status == "applied":
        raise ConcordWorkflowConflictError("GroupPlan has already been applied.")
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    if current_plan.status != "approved":
        raise ConcordWorkflowConflictError(
            "Only an approved GroupPlan may be applied."
        )

    preview = prepare_group_plan_application(
        PrepareGroupPlanApplicationRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            group_plan_id=request.group_plan_id,
            application_id=request.application_id,
            fallback_effective_context=request.fallback_effective_context,
        ),
        workspace_root=root,
        standards_library=standards_library,
    )
    _require_expected_snapshot(
        preview.expected_snapshot_revision,
        request.expected_snapshot_revision,
    )
    if preview.application_digest != request.application_digest:
        raise ConcordWorkflowConflictError(
            "Application digest does not match the exact current application preview."
        )

    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_expected_snapshot(
        snapshot_revision,
        request.expected_snapshot_revision,
    )
    current_plan = _plan_from_graph(graph, request.group_plan_id)
    if current_plan.status != "approved":
        if current_plan.status == "applied":
            raise ConcordWorkflowConflictError("GroupPlan has already been applied.")
        raise ConcordWorkflowConflictError(
            "GroupPlan is no longer approved for application."
        )

    _require_plan_application_state(
        root,
        current_plan,
        class_id=request.class_id,
        activity_id=request.activity_id,
        snapshot_revision=snapshot_revision,
    )

    applied_provenance = provenance(request.actor, clock=clock)
    groups, memberships = _native_candidate_records(
        root=root,
        class_id=request.class_id,
        plan=current_plan,
        graph=graph,
        groups=preview.groups,
        memberships=preview.memberships,
        created_provenance=applied_provenance,
    )
    applied_plan = replace(
        current_plan,
        status="applied",
        applied_provenance=applied_provenance,
        applied_application_id=request.application_id,
        applied_application_digest=request.application_digest,
    )
    _validate_complete_application_graph(
        graph,
        applied_plan,
        groups,
        memberships,
    )

    if _roster_student_ids(root, request.class_id) != current_plan.roster_student_ids:
        raise ConcordWorkflowConflictError(
            "Core roster changed immediately before GroupPlan application."
        )
    current_snapshot = load_current_snapshot(root, work)
    _require_expected_snapshot(
        current_snapshot.snapshot_revision,
        request.expected_snapshot_revision,
    )

    result = commit_record_batch(
        root,
        work,
        (applied_plan, *groups, *memberships),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return GroupPlanApplicationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=False,
        ),
        group_plan_id=applied_plan.group_plan_id,
        status=applied_plan.status,
        application_id=request.application_id,
        application_digest=request.application_digest,
        group_ids=tuple(item.group_id for item in groups),
        membership_ids=tuple(item.membership_id for item in memberships),
        unresolved_count=len(applied_plan.unresolved_student_ids),
    )


__all__ = [
    "ApplyGroupPlanRequest",
    "GroupPlanApplicationPreview",
    "GroupPlanApplicationResult",
    "PrepareGroupPlanApplicationRequest",
    "apply_group_plan",
    "prepare_group_plan_application",
]
