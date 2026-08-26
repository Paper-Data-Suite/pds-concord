"Zero-write Activity-specific Packet generation planning for Concord v0.3."

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TypeAlias, cast

from pds_core.identifiers import IdentifierValidationError, validate_identifier
from pds_core.rosters import Roster, student_lookup
from pds_core.routing_models import ModuleWorkRef

from concord.model_validation import ConcordRecordGraph
from concord.models import (
    Activity,
    ActorReference,
    ConcordRecordReference,
    Group,
    GroupMembership,
    PacketComponent,
    PacketDefinition,
    PacketTargetContext,
    PacketVersion,
    ParticipantReference,
    PrivacyPolicy,
    RoleAssignment,
    Session,
    SubjectReference,
    TemplateRenderingInput,
    TemplateVersion,
)
from concord.packet_storage import (
    PacketStorageError,
    load_current_packet,
)
from concord.packet_storage_models import LoadedPacketLibrary
from concord.starter_templates.layout import (
    STARTER_LAYOUT_SCHEMA,
    StarterLayoutError,
    starter_layout_from_json_bytes,
)
from concord.storage import (
    load_current_snapshot,
    load_record_graph_at_snapshot,
)
from concord.storage_errors import ConcordStorageError
from concord.template_storage import (
    TemplateStorageError,
    load_current_template,
    load_template_rendering_specification,
)
from concord.workflows._collaboration import (
    ACTIVE_ASSIGNMENT_STATUSES,
    context_session_ids,
)
from concord.workflows.context import (
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import WorkflowActor
from concord.workflows.participants import (
    load_required_roster,
    participant_display_label,
)

RenderingScalar: TypeAlias = str | int | bool


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketComponentChoice:
    """Explicit teacher inclusion choice for one reusable Packet component."""

    packet_component_id: str
    include: bool

    def __post_init__(self) -> None:
        _identifier(self.packet_component_id, "packet_component_id")
        if type(self.include) is not bool:
            raise ConcordWorkflowValidationError("include must be a boolean.")


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketRenderingBinding:
    """Teacher-authored rendering value shared by a component's target copies."""

    packet_component_id: str
    input_key: str
    value: RenderingScalar

    def __post_init__(self) -> None:
        _identifier(self.packet_component_id, "packet_component_id")
        _identifier(self.input_key, "input_key")
        if not isinstance(self.value, (str, int, bool)):
            raise ConcordWorkflowValidationError(
                "rendering binding value must be a string, integer, or boolean."
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstantiationDiagnostic:
    """Structured preview diagnostic; blocking items prevent commit."""

    code: str
    message: str
    blocking: bool
    packet_component_id: str | None = None
    target_key: str | None = None
    input_key: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlannedRenderingInput:
    input_key: str
    source_kind: str
    value_kind: str
    status: str
    value: RenderingScalar | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlannedPacketArtifact:
    packet_component_id: str
    component_sequence: int
    copy_index: int
    template_id: str
    template_version_id: str
    artifact_category: str
    expected_return_status: str
    page_count: int
    route_count: int
    rendering_inputs: tuple[PlannedRenderingInput, ...]
    effective_privacy_policy: PrivacyPolicy
    authorship_mode: str | None
    proposed_author_reference: (
        ParticipantReference | ActorReference | ConcordRecordReference | None
    )
    proposed_subject_reference: SubjectReference | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstantiationTargetPlan:
    target_key: str
    target_context: PacketTargetContext
    artifacts: tuple[PlannedPacketArtifact, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PacketInstantiationComponentPreview:
    packet_component_id: str
    sequence: int
    requirement_level: str
    audience_kind: str
    eligible_target_count: int
    included_target_count: int
    artifact_count: int
    page_count: int
    route_count: int
    disposition: str
    reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedTemplateSource:
    template_id: str
    template_version_id: str
    snapshot_revision: int
    snapshot_sha256: str
    rendering_specification_sha256: str
    template_version: TemplateVersion
    rendering_specification: bytes


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparePacketInstantiationRequest:
    class_id: str
    activity_id: str
    session_id: str
    packet_definition_id: str
    packet_version_id: str
    actor: WorkflowActor
    component_choices: tuple[PacketComponentChoice, ...] = ()
    rendering_bindings: tuple[PacketRenderingBinding, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPacketInstantiation:
    request: PreparePacketInstantiationRequest
    activity: Activity
    session: Session
    packet_definition: PacketDefinition
    packet_version: PacketVersion
    activity_snapshot_revision: int
    activity_snapshot_sha256: str
    packet_snapshot_revision: int
    packet_snapshot_sha256: str
    roster_sha256: str | None
    generation_date: str
    template_sources: tuple[ResolvedTemplateSource, ...]
    component_previews: tuple[PacketInstantiationComponentPreview, ...]
    target_plans: tuple[PacketInstantiationTargetPlan, ...]
    diagnostics: tuple[PacketInstantiationDiagnostic, ...]
    review_digest: str

    @property
    def ready_for_commit(self) -> bool:
        return not any(item.blocking for item in self.diagnostics) and bool(
            self.target_plans
        )

    @property
    def packet_instance_count(self) -> int:
        return len(self.target_plans)

    @property
    def artifact_count(self) -> int:
        return sum(len(item.artifacts) for item in self.target_plans)

    @property
    def page_count(self) -> int:
        return sum(
            artifact.page_count
            for target in self.target_plans
            for artifact in target.artifacts
        )

    @property
    def route_count(self) -> int:
        return sum(
            artifact.route_count
            for target in self.target_plans
            for artifact in target.artifacts
        )


def prepare_packet_instantiation(
    request: PreparePacketInstantiationRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Callable[[], datetime] | None = None,
) -> PreparedPacketInstantiation:
    """Resolve an exact Packet into a deterministic zero-write generation preview."""
    _validate_request(request)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("workspace is not available.")

    generation_date = _generation_date(clock)
    work = ModuleWorkRef(
        module_id="concord",
        class_id=request.class_id,
        work_id=request.activity_id,
    )
    graph, activity_revision, activity_sha = _load_activity_graph(root, work)
    activity = _require_activity(graph, request.activity_id)
    if activity.class_reference.record_id != request.class_id:
        raise ConcordWorkflowValidationError(
            "Activity class does not match the requested Core class."
        )
    if activity.status in {"cancelled", "archived"}:
        raise ConcordWorkflowValidationError(
            f"Activity status {activity.status!r} does not permit "
            "new Packet generation."
        )
    session = _require_session(graph, request.session_id, activity.activity_id)
    if session.status in {"cancelled", "archived"}:
        raise ConcordWorkflowValidationError(
            f"Session status {session.status!r} does not permit Packet generation."
        )

    packet_library = _load_packet(root, request.packet_definition_id)
    packet_definition = packet_library.definition
    packet_version = _require_packet_version(
        packet_library,
        request.packet_version_id,
    )
    if packet_definition.status != "active":
        raise ConcordWorkflowValidationError(
            "new Packet generation requires an active Packet Definition."
        )
    if (
        packet_version.status != "active"
        or packet_library.current_packet_version_id
        != packet_version.packet_version_id
    ):
        raise ConcordWorkflowValidationError(
            "new Packet generation requires the exact current active Packet Version."
        )

    external = tuple(
        component
        for component in packet_version.components
        if component.component_kind == "external_component"
    )
    if external:
        component = external[0]
        reference = component.external_reference
        assert reference is not None
        raise ConcordWorkflowValidationError(
            "Packet generation does not yet support external_component "
            f"{component.packet_component_id} "
            f"({reference.module_id}:{reference.record_kind}:{reference.record_id})."
        )

    choices = _choice_index(request, packet_version)
    bindings = _binding_index(request, packet_version)
    roster = _load_roster_if_needed(root, request.class_id, packet_version)
    roster_sha = None if roster is None else _roster_sha256(roster)

    sources: dict[tuple[str, str], ResolvedTemplateSource] = {}
    for component in packet_version.components:
        assert component.template_id is not None
        assert component.template_version_id is not None
        source = _resolve_template_source(
            root,
            activity,
            component,
        )
        sources[(source.template_id, source.template_version_id)] = source

    applicable_roles = tuple(
        role
        for role in graph.role_assignments
        if _role_applies(graph, role, activity.activity_id, session.session_id)
    )
    groups = tuple(
        group
        for group in graph.groups
        if _group_applies(graph, group, activity.activity_id, session.session_id)
    )
    memberships = tuple(
        membership
        for membership in graph.memberships
        if _membership_applies(
            graph,
            membership,
            activity.activity_id,
            session.session_id,
            {item.group_id for item in groups},
        )
    )

    diagnostics: list[PacketInstantiationDiagnostic] = []
    previews: list[PacketInstantiationComponentPreview] = []
    target_artifacts: dict[PacketTargetContext, list[PlannedPacketArtifact]] = {}
    consumed_bindings: set[tuple[str, str]] = set()

    for component in packet_version.components:
        assert component.template_id is not None
        assert component.template_version_id is not None
        source = sources[
            (component.template_id, component.template_version_id)
        ]
        targets = _expand_targets(
            root,
            request.class_id,
            activity,
            session,
            component,
            request.actor,
            graph,
            groups,
            memberships,
            applicable_roles,
            roster,
        )
        selected_targets, disposition, reason = _apply_component_requirement(
            component,
            targets,
            choices,
            graph,
            session.session_id,
            applicable_roles,
            diagnostics,
        )

        artifact_count = 0
        page_count = 0
        route_count = 0
        for target in selected_targets:
            for copy_index in range(1, component.copies_per_target + 1):
                planned, used = _plan_artifact(
                    root,
                    request.class_id,
                    activity,
                    session,
                    component,
                    source.template_version,
                    target,
                    copy_index,
                    bindings,
                    diagnostics,
                    generation_date,
                    graph,
                )
                consumed_bindings.update(used)
                target_artifacts.setdefault(target, []).append(planned)
                artifact_count += 1
                page_count += planned.page_count
                route_count += planned.route_count

        previews.append(
            PacketInstantiationComponentPreview(
                packet_component_id=component.packet_component_id,
                sequence=component.sequence,
                requirement_level=component.requirement_level,
                audience_kind=component.audience_intent.audience_kind,
                eligible_target_count=len(targets),
                included_target_count=len(selected_targets),
                artifact_count=artifact_count,
                page_count=page_count,
                route_count=route_count,
                disposition=disposition,
                reason=reason,
            )
        )
        if component.requirement_level == "required" and not targets:
            diagnostics.append(
                PacketInstantiationDiagnostic(
                    code="required_component_no_targets",
                    message=(
                        "Required Packet component has no eligible target in the "
                        "selected Activity/Session."
                    ),
                    blocking=True,
                    packet_component_id=component.packet_component_id,
                )
            )

    unknown_bindings = sorted(set(bindings) - consumed_bindings)
    if unknown_bindings:
        component_id, input_key = unknown_bindings[0]
        raise ConcordWorkflowValidationError(
            "rendering binding does not match a teacher-resolved input used by "
            f"the selected exact Template: {component_id}:{input_key}"
        )

    target_plans = tuple(
        PacketInstantiationTargetPlan(
            target_key=_target_key(target),
            target_context=target,
            artifacts=tuple(
                sorted(
                    artifacts,
                    key=lambda item: (
                        item.component_sequence,
                        item.copy_index,
                        item.template_version_id,
                    ),
                )
            ),
        )
        for target, artifacts in sorted(
            target_artifacts.items(),
            key=lambda item: _target_sort_key(item[0]),
        )
        if artifacts
    )
    if not target_plans and not any(item.blocking for item in diagnostics):
        diagnostics.append(
            PacketInstantiationDiagnostic(
                code="generation_empty",
                message="Reviewed Packet generation would produce no output.",
                blocking=True,
            )
        )

    ordered_sources = tuple(
        sorted(
            sources.values(),
            key=lambda item: (item.template_id, item.template_version_id),
        )
    )
    ordered_diagnostics = tuple(
        sorted(
            diagnostics,
            key=lambda item: (
                not item.blocking,
                item.packet_component_id or "",
                item.target_key or "",
                item.input_key or "",
                item.code,
            ),
        )
    )
    review_digest = _review_digest(
        request=request,
        activity=activity,
        session=session,
        packet_definition=packet_definition,
        packet_version=packet_version,
        activity_revision=activity_revision,
        activity_sha=activity_sha,
        packet_revision=packet_library.snapshot_revision,
        packet_sha=packet_library.snapshot_sha256,
        roster_sha=roster_sha,
        generation_date=generation_date,
        template_sources=ordered_sources,
        component_previews=tuple(previews),
        target_plans=target_plans,
        diagnostics=ordered_diagnostics,
    )
    return PreparedPacketInstantiation(
        request=request,
        activity=activity,
        session=session,
        packet_definition=packet_definition,
        packet_version=packet_version,
        activity_snapshot_revision=activity_revision,
        activity_snapshot_sha256=activity_sha,
        packet_snapshot_revision=packet_library.snapshot_revision,
        packet_snapshot_sha256=packet_library.snapshot_sha256,
        roster_sha256=roster_sha,
        generation_date=generation_date,
        template_sources=ordered_sources,
        component_previews=tuple(previews),
        target_plans=target_plans,
        diagnostics=ordered_diagnostics,
        review_digest=review_digest,
    )


def _identifier(value: object, field_name: str) -> str:
    try:
        return validate_identifier(cast(str, value), field_name)
    except (IdentifierValidationError, TypeError, ValueError) as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _validate_request(request: PreparePacketInstantiationRequest) -> None:
    if not isinstance(request, PreparePacketInstantiationRequest):
        raise ConcordWorkflowValidationError(
            "request must be PreparePacketInstantiationRequest."
        )
    for name in (
        "class_id",
        "activity_id",
        "session_id",
        "packet_definition_id",
        "packet_version_id",
    ):
        _identifier(getattr(request, name), name)
    if not isinstance(request.actor, WorkflowActor):
        raise ConcordWorkflowValidationError("actor must be WorkflowActor.")
    if request.actor.actor_kind != "authorized_adult":
        raise ConcordWorkflowValidationError(
            "Packet generation requires an authorized-adult workflow actor."
        )


def _generation_date(clock: Callable[[], datetime] | None) -> str:
    value = datetime.now(timezone.utc) if clock is None else clock()
    if not isinstance(value, datetime):
        raise ConcordWorkflowValidationError(
            "workflow clock must return a datetime."
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise ConcordWorkflowValidationError(
            "workflow clock must return a timezone-aware datetime."
        )
    return value.date().isoformat()


def _load_activity_graph(
    root: Path,
    work: ModuleWorkRef,
) -> tuple[ConcordRecordGraph, int, str]:
    try:
        current = load_current_snapshot(root, work)
        loaded = load_record_graph_at_snapshot(
            root,
            work,
            current.snapshot_revision,
        )
    except ConcordStorageError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {work.work_id}"
        ) from error
    return (
        cast(ConcordRecordGraph, loaded.graph),
        loaded.snapshot_revision,
        loaded.snapshot_sha256,
    )


def _require_activity(graph: ConcordRecordGraph, activity_id: str) -> Activity:
    match = next(
        (item for item in graph.activities if item.activity_id == activity_id),
        None,
    )
    if match is None:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {activity_id}"
        )
    return match


def _require_session(
    graph: ConcordRecordGraph,
    session_id: str,
    activity_id: str,
) -> Session:
    match = next(
        (item for item in graph.sessions if item.session_id == session_id),
        None,
    )
    if match is None or match.activity_id != activity_id:
        raise ConcordWorkflowNotFoundError(
            f"Session is not available for the Activity: {session_id}"
        )
    return match


def _load_packet(
    root: Path,
    packet_definition_id: str,
) -> LoadedPacketLibrary:
    try:
        return load_current_packet(root, packet_definition_id)
    except PacketStorageError as error:
        raise ConcordWorkflowNotFoundError(
            f"Packet is not available: {packet_definition_id}"
        ) from error


def _require_packet_version(
    library: LoadedPacketLibrary,
    packet_version_id: str,
) -> PacketVersion:
    match = next(
        (
            item
            for item in library.versions
            if item.packet_version_id == packet_version_id
        ),
        None,
    )
    if match is None:
        raise ConcordWorkflowNotFoundError(
            f"Packet Version is not available: {packet_version_id}"
        )
    return match


def _choice_index(
    request: PreparePacketInstantiationRequest,
    packet_version: PacketVersion,
) -> dict[str, bool]:
    component_by_id = {
        item.packet_component_id: item for item in packet_version.components
    }
    result: dict[str, bool] = {}
    for choice in request.component_choices:
        if not isinstance(choice, PacketComponentChoice):
            raise ConcordWorkflowValidationError(
                "component_choices contains an invalid value."
            )
        if choice.packet_component_id in result:
            raise ConcordWorkflowValidationError(
                "component_choices must not duplicate packet_component_id."
            )
        component = component_by_id.get(choice.packet_component_id)
        if component is None:
            raise ConcordWorkflowValidationError(
                "component choice references an unknown Packet component: "
                f"{choice.packet_component_id}"
            )
        if component.requirement_level == "required" and not choice.include:
            raise ConcordWorkflowValidationError(
                "required Packet components cannot be explicitly omitted."
            )
        if (
            component.requirement_level == "conditional"
            and component.condition is not None
            and component.condition.condition_kind != "teacher_choice"
        ):
            raise ConcordWorkflowValidationError(
                "system-evaluated conditional components do not accept "
                "teacher inclusion choices."
            )
        result[choice.packet_component_id] = choice.include
    return result


def _binding_index(
    request: PreparePacketInstantiationRequest,
    packet_version: PacketVersion,
) -> dict[tuple[str, str], RenderingScalar]:
    component_ids = {
        item.packet_component_id for item in packet_version.components
    }
    result: dict[tuple[str, str], RenderingScalar] = {}
    for binding in request.rendering_bindings:
        if not isinstance(binding, PacketRenderingBinding):
            raise ConcordWorkflowValidationError(
                "rendering_bindings contains an invalid value."
            )
        if binding.packet_component_id not in component_ids:
            raise ConcordWorkflowValidationError(
                "rendering binding references an unknown Packet component: "
                f"{binding.packet_component_id}"
            )
        key = (binding.packet_component_id, binding.input_key)
        if key in result:
            raise ConcordWorkflowValidationError(
                "rendering_bindings must not duplicate component/input pairs."
            )
        result[key] = binding.value
    return result


def _load_roster_if_needed(
    root: Path,
    class_id: str,
    packet_version: PacketVersion,
) -> Roster | None:
    needs = any(
        component.audience_intent.audience_kind in {"participant", "role"}
        for component in packet_version.components
    )
    if not needs:
        return None
    return load_required_roster(root, class_id)


def _roster_sha256(roster: Roster) -> str:
    payload = {
        "class_id": roster.class_id,
        "columns": list(roster.columns),
        "students": [
            {
                "class_id": student.class_id,
                "student_id": student.student_id,
                "last_name": student.last_name,
                "first_name": student.first_name,
                "period": student.period,
                "extra_fields": dict(sorted(student.extra_fields.items())),
            }
            for student in roster.students
        ],
    }
    return _sha_json(payload)


def _resolve_template_source(
    root: Path,
    activity: Activity,
    component: PacketComponent,
) -> ResolvedTemplateSource:
    assert component.template_id is not None
    assert component.template_version_id is not None
    try:
        library = load_current_template(root, component.template_id)
        version = next(
            (
                item
                for item in library.versions
                if item.template_version_id == component.template_version_id
            ),
            None,
        )
        if version is None:
            raise ConcordWorkflowNotFoundError(
                "exact Template Version is not available: "
                f"{component.template_id}:{component.template_version_id}"
            )
        rendering = load_template_rendering_specification(
            root,
            component.template_id,
            component.template_version_id,
        )
    except TemplateStorageError as error:
        raise ConcordWorkflowNotFoundError(
            "exact Template dependency is not available: "
            f"{component.template_id}:{component.template_version_id}"
        ) from error

    if library.definition.status == "retired":
        raise ConcordWorkflowValidationError(
            f"Template Definition is retired: {component.template_id}"
        )
    if version.status not in {"active", "superseded"}:
        raise ConcordWorkflowValidationError(
            "new generation requires an active or superseded exact Template "
            f"Version; found {version.status!r} for {version.template_version_id}."
        )
    audience = component.audience_intent.audience_kind
    template_audience = "participant" if audience == "role" else audience
    if (
        version.compatibility.audience_kinds
        and template_audience not in version.compatibility.audience_kinds
    ):
        raise ConcordWorkflowValidationError(
            "Packet component audience is incompatible with exact Template "
            f"Version: {component.packet_component_id}"
        )
    if (
        version.compatibility.activity_type_keys
        and activity.activity_type not in version.compatibility.activity_type_keys
    ):
        raise ConcordWorkflowValidationError(
            "Template Version is incompatible with Activity type: "
            f"{version.template_version_id}"
        )
    if (
        version.compatibility.scoring_orientations
        and activity.scoring_orientation
        not in version.compatibility.scoring_orientations
    ):
        raise ConcordWorkflowValidationError(
            "Template Version is incompatible with Activity scoring orientation: "
            f"{version.template_version_id}"
        )
    if version.rendering_contract_version != STARTER_LAYOUT_SCHEMA:
        raise ConcordWorkflowValidationError(
            "unsupported Template rendering contract for Activity Packet "
            f"generation: {version.rendering_contract_version}"
        )
    try:
        layout = starter_layout_from_json_bytes(rendering)
    except StarterLayoutError as error:
        raise ConcordWorkflowValidationError(
            f"invalid exact Template rendering specification: {error}"
        ) from error
    manifest = tuple(
        (item.page_key, item.sequence) for item in version.page_manifest
    )
    layout_pages = tuple(
        (item.page_key, item.sequence) for item in layout.pages
    )
    if manifest != layout_pages:
        raise ConcordWorkflowValidationError(
            "Template page manifest disagrees with the exact rendering layout."
        )
    return ResolvedTemplateSource(
        template_id=component.template_id,
        template_version_id=component.template_version_id,
        snapshot_revision=library.snapshot_revision,
        snapshot_sha256=library.snapshot_sha256,
        rendering_specification_sha256=version.rendering_specification_sha256,
        template_version=version,
        rendering_specification=rendering,
    )


def _group_applies(
    graph: ConcordRecordGraph,
    group: Group,
    activity_id: str,
    session_id: str,
) -> bool:
    if group.activity_id != activity_id or group.status not in {"planned", "active"}:
        return False
    return (
        group.effective_context is None
        or session_id in context_session_ids(graph, group.effective_context)
    )


def _membership_applies(
    graph: ConcordRecordGraph,
    membership: GroupMembership,
    activity_id: str,
    session_id: str,
    group_ids: set[str],
) -> bool:
    return bool(
        membership.group_id in group_ids
        and membership.status in ACTIVE_ASSIGNMENT_STATUSES
        and membership.effective_context.activity_id == activity_id
        and session_id in context_session_ids(graph, membership.effective_context)
    )


def _role_applies(
    graph: ConcordRecordGraph,
    role: RoleAssignment,
    activity_id: str,
    session_id: str,
) -> bool:
    return bool(
        role.activity_id == activity_id
        and role.status in ACTIVE_ASSIGNMENT_STATUSES
        and session_id in context_session_ids(graph, role.effective_context)
    )


def _expand_targets(
    root: Path,
    class_id: str,
    activity: Activity,
    session: Session,
    component: PacketComponent,
    actor: WorkflowActor,
    graph: ConcordRecordGraph,
    groups: tuple[Group, ...],
    memberships: tuple[GroupMembership, ...],
    roles: tuple[RoleAssignment, ...],
    roster: Roster | None,
) -> tuple[PacketTargetContext, ...]:
    kind = component.audience_intent.audience_kind
    if kind == "activity":
        return (
            PacketTargetContext(
                audience_kind="activity",
                activity_id=activity.activity_id,
                session_id=session.session_id,
            ),
        )
    if kind == "teacher":
        return (
            PacketTargetContext(
                audience_kind="teacher",
                activity_id=activity.activity_id,
                session_id=session.session_id,
                actor_reference=ActorReference(
                    actor_kind=actor.actor_kind,
                    actor_id=actor.actor_id,
                    owning_system=actor.owning_system,
                    display_label_snapshot=actor.display_label,
                    role_snapshot=actor.role_label,
                ),
            ),
        )
    if kind == "group":
        return tuple(
            PacketTargetContext(
                audience_kind="group",
                activity_id=activity.activity_id,
                session_id=session.session_id,
                group_id=group.group_id,
            )
            for group in sorted(groups, key=lambda item: item.group_id)
        )
    if roster is None:
        raise ConcordWorkflowNotFoundError(
            "Core roster is required for participant/role Packet generation."
        )
    if kind == "participant":
        group_ids_by_student: dict[str, set[str]] = {}
        for membership in memberships:
            participant = membership.participant_reference
            if (
                participant.participant_kind == "core_student"
                and participant.owning_system == "core"
            ):
                group_ids_by_student.setdefault(
                    participant.participant_id, set()
                ).add(membership.group_id)
        result: list[PacketTargetContext] = []
        for student in sorted(roster.students, key=lambda item: item.student_id):
            groups_for_student = group_ids_by_student.get(student.student_id, set())
            group_id = (
                next(iter(groups_for_student))
                if len(groups_for_student) == 1
                else None
            )
            result.append(
                PacketTargetContext(
                    audience_kind="participant",
                    activity_id=activity.activity_id,
                    session_id=session.session_id,
                    group_id=group_id,
                    participant_reference=ParticipantReference(
                        participant_kind="core_student",
                        participant_id=student.student_id,
                        owning_system="core",
                    ),
                )
            )
        return tuple(result)
    role_keys = set(component.audience_intent.role_keys)
    result = []
    roster_ids = set(student_lookup(roster))
    for role in sorted(roles, key=lambda item: item.role_assignment_id):
        if role.role_key not in role_keys:
            continue
        participant = role.participant_reference
        if (
            participant.participant_kind == "core_student"
            and participant.participant_id not in roster_ids
        ):
            raise ConcordWorkflowValidationError(
                "Role Packet target references a student no longer in the Core roster: "
                f"{participant.participant_id}"
            )
        result.append(
            PacketTargetContext(
                audience_kind="role",
                activity_id=activity.activity_id,
                session_id=session.session_id,
                group_id=role.group_id,
                participant_reference=participant,
                role_assignment_id=role.role_assignment_id,
                role_key=role.role_key,
            )
        )
    return tuple(result)


def _apply_component_requirement(
    component: PacketComponent,
    targets: tuple[PacketTargetContext, ...],
    choices: dict[str, bool],
    graph: ConcordRecordGraph,
    session_id: str,
    roles: tuple[RoleAssignment, ...],
    diagnostics: list[PacketInstantiationDiagnostic],
) -> tuple[tuple[PacketTargetContext, ...], str, str | None]:
    component_id = component.packet_component_id
    if component.requirement_level == "required":
        return targets, "included", None
    if component.requirement_level == "recommended":
        if choices.get(component_id, True):
            return targets, "included", None
        return (), "skipped", "teacher omitted recommended component"

    condition = component.condition
    assert condition is not None
    if condition.condition_kind == "teacher_choice":
        if component_id not in choices:
            diagnostics.append(
                PacketInstantiationDiagnostic(
                    code="teacher_choice_required",
                    message=(
                        "Conditional Packet component requires an explicit teacher "
                        "include/omit choice."
                    ),
                    blocking=True,
                    packet_component_id=component_id,
                )
            )
            return (), "unresolved", "teacher choice required"
        if not choices[component_id]:
            return (), "skipped", "teacher omitted conditional component"
        return targets, "included", None

    selected = tuple(
        target
        for target in targets
        if _condition_matches(
            condition.condition_kind,
            condition.role_keys,
            target,
            graph,
            session_id,
            roles,
        )
    )
    if selected:
        return selected, "included", None
    return (), "skipped", f"condition {condition.condition_kind} did not match"


def _condition_matches(
    condition_kind: str,
    role_keys: tuple[str, ...],
    target: PacketTargetContext,
    graph: ConcordRecordGraph,
    session_id: str,
    roles: tuple[RoleAssignment, ...],
) -> bool:
    if condition_kind == "group_context_present":
        return target.group_id is not None
    if condition_kind == "participant_context_present":
        return target.participant_reference is not None
    if condition_kind == "matching_role_present":
        allowed = set(role_keys)
        for role in roles:
            if role.role_key not in allowed:
                continue
            if not _role_applies(
                graph,
                role,
                target.activity_id,
                session_id,
            ):
                continue
            if (
                target.participant_reference is not None
                and role.participant_reference != target.participant_reference
            ):
                continue
            if target.group_id is not None and role.group_id != target.group_id:
                continue
            return True
        return False
    raise ConcordWorkflowValidationError(
        f"unsupported Packet condition: {condition_kind}"
    )


def _plan_artifact(
    root: Path,
    class_id: str,
    activity: Activity,
    session: Session,
    component: PacketComponent,
    version: TemplateVersion,
    target: PacketTargetContext,
    copy_index: int,
    bindings: dict[tuple[str, str], RenderingScalar],
    diagnostics: list[PacketInstantiationDiagnostic],
    generation_date: str,
    graph: ConcordRecordGraph,
) -> tuple[PlannedPacketArtifact, set[tuple[str, str]]]:
    target_key = _target_key(target)
    used_input_keys = {
        key for page in version.page_manifest for key in page.rendering_input_keys
    }
    input_by_key = {item.input_key: item for item in version.rendering_inputs}
    planned_inputs: list[PlannedRenderingInput] = []
    consumed: set[tuple[str, str]] = set()
    for input_key in sorted(used_input_keys):
        declaration = input_by_key[input_key]
        binding_key = (component.packet_component_id, input_key)
        if declaration.source_kind in {"teacher_text", "criterion_label"}:
            supplied = bindings.get(binding_key)
            if supplied is None:
                status = "unresolved" if declaration.required else "omitted"
                value = None
                if declaration.required:
                    diagnostics.append(
                        PacketInstantiationDiagnostic(
                            code="required_rendering_input_missing",
                            message=(
                                "Required teacher rendering input is unresolved."
                            ),
                            blocking=True,
                            packet_component_id=component.packet_component_id,
                            target_key=target_key,
                            input_key=input_key,
                        )
                    )
            else:
                _validate_rendering_value(declaration, supplied)
                consumed.add(binding_key)
                status = "resolved"
                value = supplied
        else:
            if binding_key in bindings:
                raise ConcordWorkflowValidationError(
                    "teacher rendering binding cannot override system-controlled "
                    f"input: {component.packet_component_id}:{input_key}"
                )
            value, status = _resolve_system_input(
                root,
                class_id,
                activity,
                session,
                target,
                declaration.source_kind,
                generation_date,
                graph,
            )
            if status == "unresolved" and declaration.required:
                diagnostics.append(
                    PacketInstantiationDiagnostic(
                        code="required_system_input_unresolved",
                        message=(
                            "Required system rendering input cannot be resolved "
                            "for this target."
                        ),
                        blocking=True,
                        packet_component_id=component.packet_component_id,
                        target_key=target_key,
                        input_key=input_key,
                    )
                )
            if value is not None:
                _validate_rendering_value(declaration, value)
        planned_inputs.append(
            PlannedRenderingInput(
                input_key=input_key,
                source_kind=declaration.source_kind,
                value_kind=declaration.value_kind,
                status=status,
                value=value,
            )
        )

    author_mode, author, author_notice = _plan_author(version, target)
    if author_notice is not None:
        diagnostics.append(
            PacketInstantiationDiagnostic(
                code="authorship_deferred",
                message=author_notice,
                blocking=False,
                packet_component_id=component.packet_component_id,
                target_key=target_key,
            )
        )
    subject, subject_notice = _plan_subject(version, target, session)
    if subject_notice is not None:
        diagnostics.append(
            PacketInstantiationDiagnostic(
                code="subject_deferred",
                message=subject_notice,
                blocking=False,
                packet_component_id=component.packet_component_id,
                target_key=target_key,
            )
        )
    privacy = _effective_privacy(activity, version, target, subject)

    return (
        PlannedPacketArtifact(
            packet_component_id=component.packet_component_id,
            component_sequence=component.sequence,
            copy_index=copy_index,
            template_id=version.template_id,
            template_version_id=version.template_version_id,
            artifact_category=version.artifact_category,
            expected_return_status=version.default_expected_return_status,
            page_count=len(version.page_manifest),
            route_count=sum(
                page.route_required for page in version.page_manifest
            ),
            rendering_inputs=tuple(planned_inputs),
            effective_privacy_policy=privacy,
            authorship_mode=author_mode,
            proposed_author_reference=author,
            proposed_subject_reference=subject,
        ),
        consumed,
    )


def _resolve_system_input(
    root: Path,
    class_id: str,
    activity: Activity,
    session: Session,
    target: PacketTargetContext,
    source_kind: str,
    generation_date: str,
    graph: ConcordRecordGraph,
) -> tuple[RenderingScalar | None, str]:
    if source_kind == "activity_title":
        return activity.title, "resolved"
    if source_kind == "session_label":
        return session.label or f"Session {session.sequence}", "resolved"
    if source_kind == "group_label":
        if target.group_id is None:
            return None, "unresolved"
        group = next(
            (item for item in graph.groups if item.group_id == target.group_id),
            None,
        )
        return (None, "unresolved") if group is None else (group.label, "resolved")
    if source_kind == "participant_display_label":
        participant = target.participant_reference
        if participant is None:
            return None, "unresolved"
        label = participant_display_label(root, class_id, participant)
        return (None, "unresolved") if label is None else (label, "resolved")
    if source_kind == "current_date":
        return generation_date, "resolved"
    if source_kind in {"pds2_route_payload", "human_fallback"}:
        return None, "pending_route"
    raise ConcordWorkflowValidationError(
        f"unsupported system rendering input source: {source_kind}"
    )



def _validate_rendering_value(
    declaration: TemplateRenderingInput,
    value: RenderingScalar,
) -> None:
    kind = declaration.value_kind
    if kind in {"text", "multiline_text", "date"}:
        if not isinstance(value, str):
            raise ConcordWorkflowValidationError(
                f"rendering input {declaration.input_key} requires a string value."
            )
        if kind == "date":
            try:
                date.fromisoformat(value)
            except ValueError as error:
                raise ConcordWorkflowValidationError(
                    f"rendering input {declaration.input_key} requires ISO date."
                ) from error
        if declaration.max_length is not None and len(value) > declaration.max_length:
            raise ConcordWorkflowValidationError(
                f"rendering input {declaration.input_key} exceeds max_length "
                f"{declaration.max_length}."
            )
        return
    if kind == "integer":
        if type(value) is not int:
            raise ConcordWorkflowValidationError(
                f"rendering input {declaration.input_key} requires an integer."
            )
        return
    if kind == "boolean":
        if type(value) is not bool:
            raise ConcordWorkflowValidationError(
                f"rendering input {declaration.input_key} requires a boolean."
            )
        return
    raise ConcordWorkflowValidationError(
        f"unsupported rendering input value kind: {kind}"
    )


def _plan_author(
    version: TemplateVersion,
    target: PacketTargetContext,
) -> tuple[
    str | None,
    ParticipantReference | ActorReference | ConcordRecordReference | None,
    str | None,
]:
    expectation = version.default_authorship_expectation
    if expectation is None:
        return None, None, None
    mode = expectation.authorship_mode
    if mode == "individual_author" and target.participant_reference is not None:
        return mode, target.participant_reference, None
    if mode == "collective_group_author" and target.group_id is not None:
        return (
            mode,
            ConcordRecordReference(
                record_kind="group",
                record_id=target.group_id,
            ),
            None,
        )
    if mode in {"teacher_author", "authorized_adult_author"}:
        if target.actor_reference is not None:
            return mode, target.actor_reference, None
    if mode == "unknown":
        return mode, None, None
    if expectation.required:
        return (
            mode,
            None,
            "Template authorship expectation requires later human attribution; "
            "generation does not infer authorship from membership or Role state.",
        )
    return mode, None, None


def _plan_subject(
    version: TemplateVersion,
    target: PacketTargetContext,
    session: Session,
) -> tuple[SubjectReference | None, str | None]:
    expectation = version.default_subject_expectation
    if expectation is None:
        return None, None
    kind = expectation.subject_kind
    if kind == "core_student" and target.participant_reference is not None:
        participant = target.participant_reference
        if participant.participant_kind == "core_student":
            return (
                SubjectReference(
                    subject_kind="core_student",
                    subject_id=participant.participant_id,
                    owning_system="core",
                ),
                None,
            )
    if kind == "concord_group" and target.group_id is not None:
        return (
            SubjectReference(
                subject_kind="concord_group",
                subject_id=target.group_id,
                owning_system="concord",
            ),
            None,
        )
    if kind == "concord_session":
        return (
            SubjectReference(
                subject_kind="concord_session",
                subject_id=session.session_id,
                owning_system="concord",
            ),
            None,
        )
    if kind == "concord_activity":
        return (
            SubjectReference(
                subject_kind="concord_activity",
                subject_id=target.activity_id,
                owning_system="concord",
            ),
            None,
        )
    if expectation.required:
        return (
            None,
            "Template Subject expectation cannot be concretely resolved from "
            "the selected target and is deferred.",
        )
    return None, None


def _effective_privacy(
    activity: Activity,
    version: TemplateVersion,
    target: PacketTargetContext,
    subject: SubjectReference | None,
) -> PrivacyPolicy:
    template_policy = version.default_privacy_policy
    activity_policy = activity.privacy_policy
    if activity_policy is not None and activity_policy.classification in {
        "inherited",
        "external_policy",
    }:
        raise ConcordWorkflowValidationError(
            "Activity privacy uses an unresolved inherited/external policy; "
            "Packet generation will not guess its effective audience."
        )
    classification = template_policy.classification
    if activity_policy is not None:
        classification = _stricter_classification(
            classification,
            activity_policy.classification,
        )

    references: tuple[SubjectReference, ...] = ()
    if classification == "teacher_and_subjects":
        resolved = subject or _target_subject(target)
        if resolved is None:
            return PrivacyPolicy(classification="teacher_restricted")
        references = (resolved,)
    elif classification == "group_and_teacher":
        if target.group_id is None:
            return PrivacyPolicy(classification="teacher_restricted")
        references = (
            SubjectReference(
                subject_kind="concord_group",
                subject_id=target.group_id,
                owning_system="concord",
            ),
        )

    if (
        activity_policy is not None
        and activity_policy.classification == classification
        and activity_policy.audience_references
        and references
    ):
        allowed = set(activity_policy.audience_references)
        narrowed = tuple(item for item in references if item in allowed)
        if not narrowed:
            return PrivacyPolicy(classification="teacher_restricted")
        references = narrowed

    return PrivacyPolicy(
        classification=classification,
        audience_references=references,
    )


def _stricter_classification(left: str, right: str) -> str:
    if left == right:
        return left
    if "teacher_restricted" in {left, right}:
        return "teacher_restricted"
    if left == "classroom_shared":
        return right
    if right == "classroom_shared":
        return left
    # teacher_and_subjects and group_and_teacher are incomparable. Restrict.
    return "teacher_restricted"


def _target_subject(target: PacketTargetContext) -> SubjectReference | None:
    participant = target.participant_reference
    if (
        participant is not None
        and participant.participant_kind == "core_student"
    ):
        return SubjectReference(
            subject_kind="core_student",
            subject_id=participant.participant_id,
            owning_system="core",
        )
    if target.group_id is not None:
        return SubjectReference(
            subject_kind="concord_group",
            subject_id=target.group_id,
            owning_system="concord",
        )
    if target.audience_kind == "activity":
        return SubjectReference(
            subject_kind="concord_activity",
            subject_id=target.activity_id,
            owning_system="concord",
        )
    return None


def _target_key(target: PacketTargetContext) -> str:
    if target.audience_kind == "activity":
        return f"activity:{target.activity_id}"
    if target.audience_kind == "teacher":
        assert target.actor_reference is not None
        return f"teacher:{target.actor_reference.actor_id}"
    if target.audience_kind == "group":
        assert target.group_id is not None
        return f"group:{target.group_id}"
    if target.audience_kind == "participant":
        assert target.participant_reference is not None
        return f"participant:{target.participant_reference.participant_id}"
    assert target.role_assignment_id is not None
    return f"role:{target.role_assignment_id}"


def _target_sort_key(target: PacketTargetContext) -> tuple[int, str]:
    order = {
        "activity": 0,
        "group": 1,
        "participant": 2,
        "role": 3,
        "teacher": 4,
    }
    return order[target.audience_kind], _target_key(target)


def _review_digest(
    *,
    request: PreparePacketInstantiationRequest,
    activity: Activity,
    session: Session,
    packet_definition: PacketDefinition,
    packet_version: PacketVersion,
    activity_revision: int,
    activity_sha: str,
    packet_revision: int,
    packet_sha: str,
    roster_sha: str | None,
    generation_date: str,
    template_sources: tuple[ResolvedTemplateSource, ...],
    component_previews: tuple[PacketInstantiationComponentPreview, ...],
    target_plans: tuple[PacketInstantiationTargetPlan, ...],
    diagnostics: tuple[PacketInstantiationDiagnostic, ...],
) -> str:
    payload = {
        "request": {
            "class_id": request.class_id,
            "activity_id": request.activity_id,
            "session_id": request.session_id,
            "packet_definition_id": request.packet_definition_id,
            "packet_version_id": request.packet_version_id,
            "actor": {
                "actor_id": request.actor.actor_id,
                "actor_kind": request.actor.actor_kind,
                "owning_system": request.actor.owning_system,
                "display_label": request.actor.display_label,
                "role_label": request.actor.role_label,
            },
            "component_choices": [
                {
                    "packet_component_id": item.packet_component_id,
                    "include": item.include,
                }
                for item in sorted(
                    request.component_choices,
                    key=lambda item: item.packet_component_id,
                )
            ],
            "rendering_bindings": [
                {
                    "packet_component_id": item.packet_component_id,
                    "input_key": item.input_key,
                    "value": item.value,
                }
                for item in sorted(
                    request.rendering_bindings,
                    key=lambda item: (
                        item.packet_component_id,
                        item.input_key,
                    ),
                )
            ],
        },
        "activity": {
            "activity_id": activity.activity_id,
            "session_id": session.session_id,
            "snapshot_revision": activity_revision,
            "snapshot_sha256": activity_sha,
        },
        "packet": {
            "packet_definition_id": packet_definition.packet_definition_id,
            "packet_version_id": packet_version.packet_version_id,
            "snapshot_revision": packet_revision,
            "snapshot_sha256": packet_sha,
        },
        "roster_sha256": roster_sha,
        "generation_date": generation_date,
        "templates": [
            {
                "template_id": item.template_id,
                "template_version_id": item.template_version_id,
                "snapshot_revision": item.snapshot_revision,
                "snapshot_sha256": item.snapshot_sha256,
                "rendering_specification_sha256": (
                    item.rendering_specification_sha256
                ),
            }
            for item in template_sources
        ],
        "components": [
            {
                "packet_component_id": item.packet_component_id,
                "sequence": item.sequence,
                "disposition": item.disposition,
                "eligible_target_count": item.eligible_target_count,
                "included_target_count": item.included_target_count,
                "artifact_count": item.artifact_count,
                "page_count": item.page_count,
                "route_count": item.route_count,
            }
            for item in component_previews
        ],
        "targets": [
            {
                "target_key": target.target_key,
                "artifacts": [
                    {
                        "packet_component_id": artifact.packet_component_id,
                        "component_sequence": artifact.component_sequence,
                        "copy_index": artifact.copy_index,
                        "template_id": artifact.template_id,
                        "template_version_id": artifact.template_version_id,
                        "page_count": artifact.page_count,
                        "route_count": artifact.route_count,
                        "privacy": (
                            artifact.effective_privacy_policy.classification
                        ),
                        "inputs": [
                            {
                                "input_key": value.input_key,
                                "source_kind": value.source_kind,
                                "status": value.status,
                                "value": value.value,
                            }
                            for value in artifact.rendering_inputs
                        ],
                    }
                    for artifact in target.artifacts
                ],
            }
            for target in target_plans
        ],
        "diagnostics": [
            {
                "code": item.code,
                "blocking": item.blocking,
                "packet_component_id": item.packet_component_id,
                "target_key": item.target_key,
                "input_key": item.input_key,
            }
            for item in diagnostics
        ],
    }
    return _sha_json(payload)


def _sha_json(value: object) -> str:
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


__all__ = [
    "PacketComponentChoice",
    "PacketInstantiationComponentPreview",
    "PacketInstantiationDiagnostic",
    "PacketInstantiationTargetPlan",
    "PacketRenderingBinding",
    "PlannedPacketArtifact",
    "PlannedRenderingInput",
    "PreparedPacketInstantiation",
    "PreparePacketInstantiationRequest",
    "ResolvedTemplateSource",
    "prepare_packet_instantiation",
]
