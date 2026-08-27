"""Application services for reusable Concord configuration presets."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass, replace
from pathlib import Path
from typing import TypeVar

from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary
from pds_core.standards_selection import (
    resolve_profile_selection,
    resolve_profile_standard_selection,
    resolve_standard_selection,
)

from concord.model_validation import (
    ConcordRecordGraph,
    Record,
    validate_core_standards,
    validate_record_graph,
)
from concord.models import (
    Activity,
    Criterion,
    CriterionSet,
    EffectiveContext,
    ParticipantReference,
    ResponsibilityAssignment,
    RoleAssignment,
    ScoringScale,
    ScoringScaleLevel,
    StatusReason,
)
from concord.reusable_preset_storage import (
    LoadedReusablePreset,
    ReusablePresetStorageConflictError,
    ReusablePresetStorageError,
    ReusablePresetStorageNotFoundError,
    append_preset_revision,
    create_preset_library,
    list_preset_ids,
    load_current_preset,
    load_preset_revision_by_id,
)
from concord.reusable_presets import (
    CriterionPresetSpec,
    CriterionSetPresetRevision,
    PresetRevision,
    ResponsibilityPresetRevision,
    RolePresetRevision,
    ScoringScalePresetRevision,
)
from concord.storage import commit_record_batch
from concord.validation_diagnostics import ConcordRecordGraphError
from concord.workflows._collaboration import (
    load_graph,
    require_activity,
    require_new_identity,
    work_ref,
)
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import (
    ConcordWorkflowConflictError,
    ConcordWorkflowNotFoundError,
    ConcordWorkflowValidationError,
)
from concord.workflows.models import (
    AssignResponsibilityRequest,
    AssignRoleRequest,
    ResponsibilityMutationResult,
    RoleMutationResult,
    WorkflowActor,
    WorkflowAssigneeReference,
    WorkflowCommitResult,
)
from concord.workflows.responsibility import (
    _build_responsibility,
    assign_responsibility,
)
from concord.workflows.role import _build_role, assign_role

PresetT = TypeVar("PresetT", bound=PresetRevision)


@dataclass(frozen=True, slots=True, kw_only=True)
class PresetSummary:
    preset_kind: str
    preset_id: str
    preset_revision_id: str
    revision: int
    name: str
    status: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PresetMutationResult:
    preset_kind: str
    preset_id: str
    preset_revision_id: str
    revision: int
    status: str
    workspace_created: bool = False


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRolePresetRequest:
    preset_id: str
    preset_revision_id: str
    name: str
    role_key: str
    actor: WorkflowActor
    role_label: str | None = None
    description: str | None = None
    applicability_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviseRolePresetRequest:
    preset_id: str
    preset_revision_id: str
    expected_revision: int
    name: str
    role_key: str
    actor: WorkflowActor
    role_label: str | None = None
    description: str | None = None
    applicability_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateResponsibilityPresetRequest:
    preset_id: str
    preset_revision_id: str
    name: str
    description: str
    actor: WorkflowActor
    expected_output: str | None = None
    applicability_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviseResponsibilityPresetRequest:
    preset_id: str
    preset_revision_id: str
    expected_revision: int
    name: str
    description: str
    actor: WorkflowActor
    expected_output: str | None = None
    applicability_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateScoringScalePresetRequest:
    preset_id: str
    preset_revision_id: str
    name: str
    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]
    actor: WorkflowActor
    intended_use: str | None = None
    aggregation_guidance: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviseScoringScalePresetRequest:
    preset_id: str
    preset_revision_id: str
    expected_revision: int
    name: str
    scale_type: str
    levels: tuple[ScoringScaleLevel, ...]
    actor: WorkflowActor
    intended_use: str | None = None
    aggregation_guidance: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateCriterionSetPresetRequest:
    preset_id: str
    preset_revision_id: str
    name: str
    purpose: str
    criterion_set_kind: str
    criteria: tuple[CriterionPresetSpec, ...]
    actor: WorkflowActor
    standards_profile_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviseCriterionSetPresetRequest:
    preset_id: str
    preset_revision_id: str
    expected_revision: int
    name: str
    purpose: str
    criterion_set_kind: str
    criteria: tuple[CriterionPresetSpec, ...]
    actor: WorkflowActor
    standards_profile_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SaveRolePresetFromAssignmentRequest:
    class_id: str
    activity_id: str
    role_assignment_id: str
    preset_id: str
    preset_revision_id: str
    name: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    description: str | None = None
    applicability_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class SaveResponsibilityPresetFromAssignmentRequest:
    class_id: str
    activity_id: str
    responsibility_assignment_id: str
    preset_id: str
    preset_revision_id: str
    name: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    applicability_hints: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, kw_only=True)
class SaveScoringScalePresetFromActivityRequest:
    class_id: str
    activity_id: str
    scoring_scale_id: str
    preset_id: str
    preset_revision_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    name: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SaveCriterionSetPresetFromActivityRequest:
    class_id: str
    activity_id: str
    criterion_set_id: str
    preset_id: str
    preset_revision_id: str
    expected_snapshot_revision: int
    actor: WorkflowActor
    name: str | None = None
    recommended_scoring_scale_preset_id: str | None = None
    recommended_scoring_scale_preset_revision_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplyRolePresetRequest:
    preset_id: str
    preset_revision_id: str
    class_id: str
    activity_id: str
    role_assignment_id: str
    participant_reference: ParticipantReference
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "active"
    membership_id: str | None = None
    group_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ApplyResponsibilityPresetRequest:
    preset_id: str
    preset_revision_id: str
    class_id: str
    activity_id: str
    responsibility_assignment_id: str
    assignee_reference: WorkflowAssigneeReference
    effective_context: EffectiveContext
    expected_snapshot_revision: int
    actor: WorkflowActor
    status: str = "active"
    group_id: str | None = None
    work_item_id: str | None = None
    status_reason: StatusReason | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class CriterionTargetIdentity:
    criterion_key: str
    criterion_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class MaterializeScoringSetupRequest:
    criterion_preset_id: str
    criterion_preset_revision_id: str
    class_id: str
    activity_id: str
    criterion_set_id: str
    criterion_set_lineage_id: str
    criterion_ids: tuple[CriterionTargetIdentity, ...]
    expected_snapshot_revision: int
    actor: WorkflowActor
    scoring_scale_preset_id: str | None = None
    scoring_scale_preset_revision_id: str | None = None
    scoring_scale_id: str | None = None
    scoring_scale_lineage_id: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class MaterializeScoringSetupResult:
    commit: WorkflowCommitResult
    criterion_set_id: str
    criterion_ids: tuple[str, ...]
    scoring_scale_id: str | None


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedPresetSave:
    preset_kind: str
    preset_id: str
    preset_revision_id: str
    source_class_id: str
    source_activity_id: str
    source_record_kind: str
    source_record_id: str
    name: str
    reusable_fields: tuple[str, ...]
    excluded_state: tuple[str, ...]
    review_digest: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedRolePresetApplication:
    request: ApplyRolePresetRequest
    preset_name: str
    role_key: str
    role_label: str | None
    review_digest: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedResponsibilityPresetApplication:
    request: ApplyResponsibilityPresetRequest
    preset_name: str
    description: str
    expected_output: str | None
    review_digest: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedScoringSetup:
    request: MaterializeScoringSetupRequest
    criterion_preset_name: str
    criterion_count: int
    scoring_scale_preset_name: str | None
    recommended_scoring_scale_preset_id: str | None
    recommended_scoring_scale_preset_revision_id: str | None
    recommended_scoring_scale_preset_name: str | None
    standards_profile_id: str | None
    review_digest: str


@dataclass(frozen=True, slots=True, kw_only=True)
class _BuiltScoringSetup:
    root: Path
    graph: ConcordRecordGraph
    snapshot_revision: int
    work: ModuleWorkRef
    criterion_preset: CriterionSetPresetRevision
    recommended_scale_preset: ScoringScalePresetRevision | None
    scale_preset: ScoringScalePresetRevision | None
    scale: ScoringScale | None
    criterion_set: CriterionSet
    criteria: tuple[Criterion, ...]
    updated_activity: Activity


def _jsonable(value: object) -> object:
    if is_dataclass(value):
        return {
            field.name: _jsonable(getattr(value, field.name))
            for field in fields(value)
            if field.name not in {"created_provenance", "updated_provenance"}
        }
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _review_digest(*values: object) -> str:
    encoded = json.dumps(
        [_jsonable(value) for value in values],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _require_review_digest(value: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ConcordWorkflowValidationError(
            "review_digest must be a lowercase SHA-256 hexadecimal digest."
        )
    return value


def _require_activity_revision(actual: int, expected: int) -> None:
    if actual != expected:
        raise ConcordWorkflowConflictError(
            "target Activity changed after the preset application was reviewed."
        )


def _validate_candidate_graph(
    graph: ConcordRecordGraph,
    standards_library: StandardsLibrary | None,
) -> None:
    try:
        validate_record_graph(graph)
        if standards_library is not None:
            validate_core_standards(graph, standards_library)
    except ConcordRecordGraphError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _criterion_standard_ids(
    preset: CriterionSetPresetRevision,
) -> tuple[str, ...]:
    result: list[str] = []
    for criterion in preset.criteria:
        if criterion.standard_id is not None:
            result.append(criterion.standard_id)
        result.extend(criterion.alignment_standard_ids)
    return tuple(dict.fromkeys(result))


def _validate_criterion_preset_standards(
    preset: CriterionSetPresetRevision,
    standards_library: StandardsLibrary | None,
    *,
    activity: object | None = None,
) -> None:
    standard_ids = _criterion_standard_ids(preset)
    if not standard_ids and preset.standards_profile_id is None:
        return
    if standards_library is None:
        raise ConcordWorkflowValidationError(
            "Criterion Set preset standards references require a current Core "
            "standards library."
        )
    try:
        if activity is not None:
            activity_profile = getattr(activity, "standards_profile_id")
            if activity_profile is None:
                raise ConcordWorkflowValidationError(
                    "standard-backed Criterion presets require a target Activity "
                    "standards profile."
                )
            if (
                preset.standards_profile_id is not None
                and preset.standards_profile_id != activity_profile
            ):
                raise ConcordWorkflowValidationError(
                    "Criterion preset standards profile does not match the target "
                    "Activity."
                )
            items = resolve_profile_standard_selection(
                standards_library,
                profile_id=activity_profile,
                selected_standard_ids=standard_ids,
            )
        elif preset.standards_profile_id is not None:
            resolve_profile_selection(
                standards_library,
                preset.standards_profile_id,
            )
            items = resolve_profile_standard_selection(
                standards_library,
                profile_id=preset.standards_profile_id,
                selected_standard_ids=standard_ids,
            )
        else:
            items = tuple(
                resolve_standard_selection(standards_library, standard_id)
                for standard_id in standard_ids
            )
    except ValueError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    inactive = tuple(item.standard_id for item in items if not item.active)
    if inactive:
        raise ConcordWorkflowValidationError(
            "Criterion Set preset references inactive Core Standards: "
            + ", ".join(inactive)
        )
    if activity is not None:
        focus_standard_ids = frozenset(getattr(activity, "focus_standard_ids"))
        for criterion in preset.criteria:
            if (
                criterion.criterion_kind == "standard_backed"
                and criterion.standard_id not in focus_standard_ids
            ):
                raise ConcordWorkflowValidationError(
                    "Standard-backed Criterion preset does not govern a target "
                    "Activity Focus Standard."
                )


def _validate_target_scoring_orientation(
    activity: object,
    preset: CriterionSetPresetRevision,
) -> None:
    kinds = {criterion.criterion_kind for criterion in preset.criteria}
    orientation = getattr(activity, "scoring_orientation")
    if "standard_backed" in kinds and orientation not in {
        "standards_based",
        "mixed",
    }:
        raise ConcordWorkflowValidationError(
            "target Activity scoring orientation does not permit standard-backed "
            "Criteria."
        )
    if "local" in kinds and orientation not in {"local_criteria_only", "mixed"}:
        raise ConcordWorkflowValidationError(
            "target Activity scoring orientation does not permit local Criteria."
        )


def _summary(loaded: LoadedReusablePreset) -> PresetSummary:
    value = loaded.current
    return PresetSummary(
        preset_kind=loaded.preset_kind,
        preset_id=value.preset_id,
        preset_revision_id=value.preset_revision_id,
        revision=value.revision,
        name=value.name,
        status=value.status,
    )


def list_presets(
    preset_kind: str,
    *,
    workspace_root: str | Path | None = None,
    include_retired: bool = False,
) -> tuple[PresetSummary, ...]:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    try:
        values = tuple(
            _summary(load_current_preset(root, preset_kind, preset_id))
            for preset_id in list_preset_ids(root, preset_kind)
        )
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return tuple(
        value for value in values if include_retired or value.status == "active"
    )


def get_preset(
    preset_kind: str,
    preset_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> PresetRevision:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(f"preset is not available: {preset_id}")
    try:
        return load_current_preset(root, preset_kind, preset_id).current
    except ReusablePresetStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def validate_preset(
    preset_kind: str,
    preset_id: str,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> PresetSummary:
    """Validate one current preset, including current Core references when needed."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {preset_id}"
        )
    try:
        loaded = load_current_preset(root, preset_kind, preset_id)
    except ReusablePresetStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if isinstance(loaded.current, CriterionSetPresetRevision):
        _validate_criterion_preset_standards(
            loaded.current,
            standards_library,
        )
    return _summary(loaded)


def get_preset_revision(
    preset_kind: str,
    preset_id: str,
    preset_revision_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> PresetRevision:
    """Load one exact immutable preset revision without requiring it to be current."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {preset_id}"
        )
    try:
        return load_preset_revision_by_id(
            root,
            preset_kind,
            preset_id,
            preset_revision_id,
        )
    except ReusablePresetStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error


def _commit_create(
    value: PresetRevision,
    *,
    workspace_root: str | Path | None,
) -> PresetMutationResult:
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    try:
        loaded = create_preset_library(bootstrap.root, value)
    except ReusablePresetStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return PresetMutationResult(
        preset_kind=loaded.preset_kind,
        preset_id=value.preset_id,
        preset_revision_id=value.preset_revision_id,
        revision=value.revision,
        status=value.status,
        workspace_created=bootstrap.created,
    )


def _commit_revision(
    value: PresetRevision,
    *,
    expected_revision: int,
    workspace_root: str | Path | None,
) -> PresetMutationResult:
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    try:
        loaded = append_preset_revision(
            bootstrap.root,
            value,
            expected_revision=expected_revision,
        )
    except ReusablePresetStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    return PresetMutationResult(
        preset_kind=loaded.preset_kind,
        preset_id=value.preset_id,
        preset_revision_id=value.preset_revision_id,
        revision=value.revision,
        status=value.status,
        workspace_created=bootstrap.created,
    )


def _current_typed(
    root: Path,
    kind: str,
    preset_id: str,
    expected_type: type[PresetT],
) -> PresetT:
    try:
        value = load_current_preset(root, kind, preset_id).current
    except ReusablePresetStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if not isinstance(value, expected_type):
        raise ConcordWorkflowValidationError("preset type disagrees with its library.")
    return value


def _exact_typed(
    root: Path,
    kind: str,
    preset_id: str,
    preset_revision_id: str,
    expected_type: type[PresetT],
) -> PresetT:
    try:
        current = load_current_preset(root, kind, preset_id).current
        value = load_preset_revision_by_id(
            root,
            kind,
            preset_id,
            preset_revision_id,
        )
    except ReusablePresetStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(str(error)) from error
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if not isinstance(value, expected_type):
        raise ConcordWorkflowValidationError("preset type disagrees with its library.")
    if current.status != "active" or value.status != "active":
        raise ConcordWorkflowValidationError("retired preset cannot be applied.")
    return value


def _recommended_scale_preset(
    root: Path,
    preset: CriterionSetPresetRevision,
) -> ScoringScalePresetRevision | None:
    references = {
        (
            item.default_scoring_scale_preset_id,
            item.default_scoring_scale_preset_revision_id,
        )
        for item in preset.criteria
        if item.default_scoring_scale_preset_id is not None
    }
    if not references:
        return None
    if len(references) != 1:
        raise ConcordWorkflowValidationError(
            "Criterion Set preset has conflicting default Scoring Scale references."
        )
    preset_id, revision_id = next(iter(references))
    assert preset_id is not None and revision_id is not None
    return _exact_typed(
        root,
        "scoring_scale",
        preset_id,
        revision_id,
        ScoringScalePresetRevision,
    )



def _require_new_preset_identity(root: Path, kind: str, preset_id: str) -> None:
    try:
        existing = list_preset_ids(root, kind)
    except ReusablePresetStorageError as error:
        raise ConcordWorkflowValidationError(str(error)) from error
    if preset_id in existing:
        raise ConcordWorkflowConflictError(
            f"preset identity already exists: {preset_id}"
        )


def _source_graph(
    root: Path,
    *,
    class_id: str,
    activity_id: str,
    standards_library: StandardsLibrary | None,
) -> tuple[ConcordRecordGraph, int]:
    require_core_class(root, class_id)
    graph, snapshot_revision, _ = load_graph(
        root,
        work_ref(class_id, activity_id),
        standards_library,
    )
    require_activity(graph, activity_id)
    return graph, snapshot_revision


def _initial_source_revision(actual: int, expected: int) -> None:
    if actual != expected:
        raise ConcordWorkflowConflictError(
            "source Activity changed before the preset save was prepared."
        )


def _source_role(
    graph: ConcordRecordGraph,
    role_assignment_id: str,
) -> RoleAssignment:
    value = next(
        (
            item
            for item in graph.role_assignments
            if item.role_assignment_id == role_assignment_id
        ),
        None,
    )
    if value is None:
        raise ConcordWorkflowNotFoundError(
            f"Role Assignment is not available: {role_assignment_id}"
        )
    return value


def _source_responsibility(
    graph: ConcordRecordGraph,
    responsibility_assignment_id: str,
) -> ResponsibilityAssignment:
    value = next(
        (
            item
            for item in graph.responsibility_assignments
            if item.responsibility_assignment_id == responsibility_assignment_id
        ),
        None,
    )
    if value is None:
        raise ConcordWorkflowNotFoundError(
            "Responsibility Assignment is not available: "
            f"{responsibility_assignment_id}"
        )
    return value


def _source_scale(graph: ConcordRecordGraph, scoring_scale_id: str) -> ScoringScale:
    value = next(
        (
            item
            for item in graph.scoring_scales
            if item.scoring_scale_id == scoring_scale_id
        ),
        None,
    )
    if value is None:
        raise ConcordWorkflowNotFoundError(
            f"Scoring Scale is not available: {scoring_scale_id}"
        )
    return value


def _source_criterion_set(
    graph: ConcordRecordGraph,
    criterion_set_id: str,
) -> tuple[CriterionSet, tuple[Criterion, ...]]:
    value = next(
        (
            item
            for item in graph.criterion_sets
            if item.criterion_set_id == criterion_set_id
        ),
        None,
    )
    if value is None:
        raise ConcordWorkflowNotFoundError(
            f"Criterion Set is not available: {criterion_set_id}"
        )
    by_id = {item.criterion_id: item for item in graph.criteria}
    try:
        criteria = tuple(by_id[item] for item in value.criterion_ids)
    except KeyError as error:
        raise ConcordWorkflowValidationError(
            "source Criterion Set has unresolved member Criteria."
        ) from error
    return value, criteria


def _role_save_candidate(
    request: SaveRolePresetFromAssignmentRequest,
    *,
    root: Path,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
    enforce_expected_snapshot: bool,
) -> tuple[PreparedPresetSave, RolePresetRevision]:
    graph, snapshot_revision = _source_graph(
        root,
        class_id=request.class_id,
        activity_id=request.activity_id,
        standards_library=standards_library,
    )
    if enforce_expected_snapshot:
        _initial_source_revision(
            snapshot_revision,
            request.expected_snapshot_revision,
        )
    source = _source_role(graph, request.role_assignment_id)
    _require_new_preset_identity(root, "role", request.preset_id)
    candidate = RolePresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=request.name,
        role_key=source.role_key,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        role_label=source.role_label_snapshot,
        description=request.description,
        applicability_hints=request.applicability_hints,
    )
    digest = _review_digest(
        "save-role-preset-v1",
        request,
        source.role_key,
        source.role_label_snapshot,
        request.description,
        request.applicability_hints,
    )
    return (
        PreparedPresetSave(
            preset_kind="role",
            preset_id=request.preset_id,
            preset_revision_id=request.preset_revision_id,
            source_class_id=request.class_id,
            source_activity_id=request.activity_id,
            source_record_kind="role_assignment",
            source_record_id=request.role_assignment_id,
            name=request.name,
            reusable_fields=(
                f"Role key: {source.role_key}",
                f"Role label: {source.role_label_snapshot or '-'}",
                f"Description: {request.description or '-'}",
            ),
            excluded_state=(
                "participant/assignee identity",
                "Group and Membership identity",
                "Effective Context and Session scope",
                "assignment lifecycle status and supersession history",
                "assignment actor/provenance",
            ),
            review_digest=digest,
        ),
        candidate,
    )


def prepare_role_preset_from_assignment(
    request: SaveRolePresetFromAssignmentRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedPresetSave:
    """Preview safe Role semantics extracted from one exact assignment."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, _ = _role_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=True,
    )
    return prepared


def save_role_preset_from_assignment(
    request: SaveRolePresetFromAssignmentRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    """Create one reviewed Role preset using only reusable assignment fields."""
    expected_digest = _require_review_digest(review_digest)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, candidate = _role_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=False,
    )
    if prepared.review_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Role preset save review is stale; prepare and review it again."
        )
    return _commit_create(candidate, workspace_root=root)


def _responsibility_save_candidate(
    request: SaveResponsibilityPresetFromAssignmentRequest,
    *,
    root: Path,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
    enforce_expected_snapshot: bool,
) -> tuple[PreparedPresetSave, ResponsibilityPresetRevision]:
    graph, snapshot_revision = _source_graph(
        root,
        class_id=request.class_id,
        activity_id=request.activity_id,
        standards_library=standards_library,
    )
    if enforce_expected_snapshot:
        _initial_source_revision(
            snapshot_revision,
            request.expected_snapshot_revision,
        )
    source = _source_responsibility(
        graph,
        request.responsibility_assignment_id,
    )
    _require_new_preset_identity(root, "responsibility", request.preset_id)
    candidate = ResponsibilityPresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=request.name,
        description=source.description,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        expected_output=source.expected_output,
        applicability_hints=request.applicability_hints,
    )
    digest = _review_digest(
        "save-responsibility-preset-v1",
        request,
        source.description,
        source.expected_output,
        request.applicability_hints,
    )
    return (
        PreparedPresetSave(
            preset_kind="responsibility",
            preset_id=request.preset_id,
            preset_revision_id=request.preset_revision_id,
            source_class_id=request.class_id,
            source_activity_id=request.activity_id,
            source_record_kind="responsibility_assignment",
            source_record_id=request.responsibility_assignment_id,
            name=request.name,
            reusable_fields=(
                f"Responsibility: {source.description}",
                f"Expected output: {source.expected_output or '-'}",
            ),
            excluded_state=(
                "participant/Group assignee identity",
                "Group and work-item identity",
                "Effective Context and Session scope",
                "assignment lifecycle/status reason and supersession history",
                "assignment actor/provenance",
            ),
            review_digest=digest,
        ),
        candidate,
    )


def prepare_responsibility_preset_from_assignment(
    request: SaveResponsibilityPresetFromAssignmentRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedPresetSave:
    """Preview safe Responsibility semantics from one exact assignment."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, _ = _responsibility_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=True,
    )
    return prepared


def save_responsibility_preset_from_assignment(
    request: SaveResponsibilityPresetFromAssignmentRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    """Create one reviewed Responsibility preset from reusable source fields."""
    expected_digest = _require_review_digest(review_digest)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, candidate = _responsibility_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=False,
    )
    if prepared.review_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Responsibility preset save review is stale; prepare it again."
        )
    return _commit_create(candidate, workspace_root=root)


def _scale_save_candidate(
    request: SaveScoringScalePresetFromActivityRequest,
    *,
    root: Path,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
    enforce_expected_snapshot: bool,
) -> tuple[PreparedPresetSave, ScoringScalePresetRevision]:
    graph, snapshot_revision = _source_graph(
        root,
        class_id=request.class_id,
        activity_id=request.activity_id,
        standards_library=standards_library,
    )
    if enforce_expected_snapshot:
        _initial_source_revision(
            snapshot_revision,
            request.expected_snapshot_revision,
        )
    source = _source_scale(graph, request.scoring_scale_id)
    _require_new_preset_identity(root, "scoring_scale", request.preset_id)
    name = source.name if request.name is None else request.name
    candidate = ScoringScalePresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=name,
        scale_type=source.scale_type,
        levels=source.levels,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        intended_use=source.intended_use,
        aggregation_guidance=source.aggregation_guidance,
    )
    digest = _review_digest(
        "save-scale-preset-v1",
        request,
        name,
        source.scale_type,
        source.levels,
        source.intended_use,
        source.aggregation_guidance,
    )
    return (
        PreparedPresetSave(
            preset_kind="scoring_scale",
            preset_id=request.preset_id,
            preset_revision_id=request.preset_revision_id,
            source_class_id=request.class_id,
            source_activity_id=request.activity_id,
            source_record_kind="scoring_scale",
            source_record_id=request.scoring_scale_id,
            name=name,
            reusable_fields=(
                f"Scale type: {source.scale_type}",
                f"Levels: {len(source.levels)} exact values",
                f"Intended use: {source.intended_use or '-'}",
                f"Aggregation guidance: {source.aggregation_guidance or '-'}",
            ),
            excluded_state=(
                "Activity-native Scoring Scale identity and lineage",
                "Activity-native revision/lifecycle status",
                "Activity provenance and supersession history",
                "all Scores and Score Evidence Links",
            ),
            review_digest=digest,
        ),
        candidate,
    )


def prepare_scoring_scale_preset_from_activity(
    request: SaveScoringScalePresetFromActivityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedPresetSave:
    """Preview reusable semantics from one exact Activity-native Scale."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, _ = _scale_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=True,
    )
    return prepared


def save_scoring_scale_preset_from_activity(
    request: SaveScoringScalePresetFromActivityRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    """Create one reviewed Scale preset without source Activity identities."""
    expected_digest = _require_review_digest(review_digest)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, candidate = _scale_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=False,
    )
    if prepared.review_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Scoring Scale preset save review is stale; prepare it again."
        )
    return _commit_create(candidate, workspace_root=root)


def _criterion_save_specs(
    root: Path,
    source_criteria: tuple[Criterion, ...],
    request: SaveCriterionSetPresetFromActivityRequest,
) -> tuple[
    tuple[CriterionPresetSpec, ...],
    ScoringScalePresetRevision | None,
    tuple[str, ...],
]:
    preset_id = request.recommended_scoring_scale_preset_id
    revision_id = request.recommended_scoring_scale_preset_revision_id
    if (preset_id is None) != (revision_id is None):
        raise ConcordWorkflowValidationError(
            "recommended Scale preset ID and revision ID must be supplied together."
        )
    source_defaults = {
        item.default_scoring_scale_id
        for item in source_criteria
        if item.default_scoring_scale_id is not None
    }
    mapped: ScoringScalePresetRevision | None = None
    if preset_id is not None:
        assert revision_id is not None
        if not source_defaults:
            raise ConcordWorkflowValidationError(
                "source Criterion Set has no default Scoring Scale to map."
            )
        if len(source_defaults) > 1:
            raise ConcordWorkflowValidationError(
                "source Criterion Set uses multiple native default Scoring Scales; "
                "save without a recommendation or normalize the source first."
            )
        mapped = _exact_typed(
            root,
            "scoring_scale",
            preset_id,
            revision_id,
            ScoringScalePresetRevision,
        )
    specs = tuple(
        CriterionPresetSpec(
            key=item.key,
            label=item.label,
            definition=item.definition,
            criterion_kind=item.criterion_kind,
            supported_target_kinds=item.supported_target_kinds,
            standard_id=item.standard_id,
            alignment_standard_ids=item.alignment_standard_ids,
            default_scoring_scale_preset_id=(
                None
                if mapped is None or item.default_scoring_scale_id is None
                else mapped.preset_id
            ),
            default_scoring_scale_preset_revision_id=(
                None
                if mapped is None or item.default_scoring_scale_id is None
                else mapped.preset_revision_id
            ),
            status=item.status,
        )
        for item in source_criteria
    )
    exclusions: list[str] = [
        "Activity-native Criterion Set identity and lineage",
        "Activity-native Criterion identities",
        "Activity-native revision/scope/lifecycle provenance",
        "all Scores and Score Evidence Links",
    ]
    if source_defaults and mapped is None:
        exclusions.append("Activity-native default Scoring Scale references")
    return specs, mapped, tuple(exclusions)


def _criterion_save_candidate(
    request: SaveCriterionSetPresetFromActivityRequest,
    *,
    root: Path,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
    enforce_expected_snapshot: bool,
) -> tuple[PreparedPresetSave, CriterionSetPresetRevision]:
    graph, snapshot_revision = _source_graph(
        root,
        class_id=request.class_id,
        activity_id=request.activity_id,
        standards_library=standards_library,
    )
    if enforce_expected_snapshot:
        _initial_source_revision(
            snapshot_revision,
            request.expected_snapshot_revision,
        )
    source, source_criteria = _source_criterion_set(
        graph,
        request.criterion_set_id,
    )
    _require_new_preset_identity(root, "criterion_set", request.preset_id)
    specs, mapped_scale, exclusions = _criterion_save_specs(
        root,
        source_criteria,
        request,
    )
    name = source.name if request.name is None else request.name
    candidate = CriterionSetPresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=name,
        purpose=source.purpose,
        criterion_set_kind=source.criterion_set_kind,
        criteria=specs,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        standards_profile_id=source.standards_profile_id,
    )
    _validate_criterion_preset_standards(candidate, standards_library)
    digest = _review_digest(
        "save-criterion-set-preset-v1",
        request,
        name,
        source.purpose,
        source.criterion_set_kind,
        source.standards_profile_id,
        specs,
        mapped_scale,
    )
    fields = [
        f"Purpose: {source.purpose}",
        f"Criterion Set kind: {source.criterion_set_kind}",
        f"Criteria: {len(specs)} ordered definitions",
        f"Standards profile: {source.standards_profile_id or '-'}",
    ]
    if mapped_scale is not None:
        fields.append(f"Recommended Scale: {mapped_scale.name}")
    return (
        PreparedPresetSave(
            preset_kind="criterion_set",
            preset_id=request.preset_id,
            preset_revision_id=request.preset_revision_id,
            source_class_id=request.class_id,
            source_activity_id=request.activity_id,
            source_record_kind="criterion_set",
            source_record_id=request.criterion_set_id,
            name=name,
            reusable_fields=tuple(fields),
            excluded_state=exclusions,
            review_digest=digest,
        ),
        candidate,
    )


def prepare_criterion_set_preset_from_activity(
    request: SaveCriterionSetPresetFromActivityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedPresetSave:
    """Preview positive-allowlist extraction from one native Criterion Set."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, _ = _criterion_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=True,
    )
    return prepared


def save_criterion_set_preset_from_activity(
    request: SaveCriterionSetPresetFromActivityRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    """Create one reviewed Criterion preset without Activity-native identities."""
    expected_digest = _require_review_digest(review_digest)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    prepared, candidate = _criterion_save_candidate(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
        enforce_expected_snapshot=False,
    )
    if prepared.review_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Criterion Set preset save review is stale; prepare it again."
        )
    return _commit_create(candidate, workspace_root=root)

def create_role_preset(
    request: CreateRolePresetRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    value = RolePresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=request.name,
        role_key=request.role_key,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        role_label=request.role_label,
        description=request.description,
        applicability_hints=request.applicability_hints,
    )
    return _commit_create(value, workspace_root=workspace_root)


def revise_role_preset(
    request: ReviseRolePresetRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {request.preset_id}"
        )
    current = _current_typed(root, "role", request.preset_id, RolePresetRevision)
    if current.status != "active":
        raise ConcordWorkflowValidationError("retired preset cannot be revised.")
    if current.revision != request.expected_revision:
        raise ConcordWorkflowConflictError("preset changed after it was reviewed.")
    value = RolePresetRevision(
        preset_id=current.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=current.revision + 1,
        name=request.name,
        role_key=request.role_key,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        role_label=request.role_label,
        description=request.description,
        applicability_hints=request.applicability_hints,
        supersedes_preset_revision_id=current.preset_revision_id,
    )
    return _commit_revision(
        value,
        expected_revision=request.expected_revision,
        workspace_root=workspace_root,
    )


def create_responsibility_preset(
    request: CreateResponsibilityPresetRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    value = ResponsibilityPresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=request.name,
        description=request.description,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        expected_output=request.expected_output,
        applicability_hints=request.applicability_hints,
    )
    return _commit_create(value, workspace_root=workspace_root)


def revise_responsibility_preset(
    request: ReviseResponsibilityPresetRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {request.preset_id}"
        )
    current = _current_typed(
        root,
        "responsibility",
        request.preset_id,
        ResponsibilityPresetRevision,
    )
    if current.status != "active":
        raise ConcordWorkflowValidationError("retired preset cannot be revised.")
    if current.revision != request.expected_revision:
        raise ConcordWorkflowConflictError("preset changed after it was reviewed.")
    value = ResponsibilityPresetRevision(
        preset_id=current.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=current.revision + 1,
        name=request.name,
        description=request.description,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        expected_output=request.expected_output,
        applicability_hints=request.applicability_hints,
        supersedes_preset_revision_id=current.preset_revision_id,
    )
    return _commit_revision(
        value,
        expected_revision=request.expected_revision,
        workspace_root=workspace_root,
    )


def create_scoring_scale_preset(
    request: CreateScoringScalePresetRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    value = ScoringScalePresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=request.name,
        scale_type=request.scale_type,
        levels=request.levels,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        intended_use=request.intended_use,
        aggregation_guidance=request.aggregation_guidance,
    )
    return _commit_create(value, workspace_root=workspace_root)


def revise_scoring_scale_preset(
    request: ReviseScoringScalePresetRequest,
    *,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {request.preset_id}"
        )
    current = _current_typed(
        root,
        "scoring_scale",
        request.preset_id,
        ScoringScalePresetRevision,
    )
    if current.status != "active":
        raise ConcordWorkflowValidationError("retired preset cannot be revised.")
    if current.revision != request.expected_revision:
        raise ConcordWorkflowConflictError("preset changed after it was reviewed.")
    value = ScoringScalePresetRevision(
        preset_id=current.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=current.revision + 1,
        name=request.name,
        scale_type=request.scale_type,
        levels=request.levels,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        intended_use=request.intended_use,
        aggregation_guidance=request.aggregation_guidance,
        supersedes_preset_revision_id=current.preset_revision_id,
    )
    return _commit_revision(
        value,
        expected_revision=request.expected_revision,
        workspace_root=workspace_root,
    )


def create_criterion_set_preset(
    request: CreateCriterionSetPresetRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    value = CriterionSetPresetRevision(
        preset_id=request.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=1,
        name=request.name,
        purpose=request.purpose,
        criterion_set_kind=request.criterion_set_kind,
        criteria=request.criteria,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        standards_profile_id=request.standards_profile_id,
    )
    _validate_criterion_preset_standards(value, standards_library)
    root = resolve_read_workspace_root(workspace_root)
    if any(
        item.default_scoring_scale_preset_id is not None
        for item in value.criteria
    ):
        if root is None:
            raise ConcordWorkflowNotFoundError(
                "recommended Scoring Scale preset is not available."
            )
        _recommended_scale_preset(root, value)
    return _commit_create(value, workspace_root=workspace_root)


def revise_criterion_set_preset(
    request: ReviseCriterionSetPresetRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {request.preset_id}"
        )
    current = _current_typed(
        root,
        "criterion_set",
        request.preset_id,
        CriterionSetPresetRevision,
    )
    if current.status != "active":
        raise ConcordWorkflowValidationError("retired preset cannot be revised.")
    if current.revision != request.expected_revision:
        raise ConcordWorkflowConflictError("preset changed after it was reviewed.")
    value = CriterionSetPresetRevision(
        preset_id=current.preset_id,
        preset_revision_id=request.preset_revision_id,
        revision=current.revision + 1,
        name=request.name,
        purpose=request.purpose,
        criterion_set_kind=request.criterion_set_kind,
        criteria=request.criteria,
        status="active",
        created_provenance=provenance(request.actor, clock=clock),
        standards_profile_id=request.standards_profile_id,
        supersedes_preset_revision_id=current.preset_revision_id,
    )
    _validate_criterion_preset_standards(value, standards_library)
    _recommended_scale_preset(root, value)
    return _commit_revision(
        value,
        expected_revision=request.expected_revision,
        workspace_root=workspace_root,
    )


def retire_preset(
    preset_kind: str,
    preset_id: str,
    *,
    preset_revision_id: str,
    expected_revision: int,
    actor: WorkflowActor,
    workspace_root: str | Path | None = None,
    clock: Clock | None = None,
) -> PresetMutationResult:
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError(
            f"preset is not available: {preset_id}"
        )
    current = get_preset(preset_kind, preset_id, workspace_root=root)
    if current.status != "active":
        raise ConcordWorkflowValidationError("preset is already retired.")
    if current.revision != expected_revision:
        raise ConcordWorkflowConflictError("preset changed after it was reviewed.")
    created = provenance(actor, clock=clock)
    if isinstance(current, RolePresetRevision):
        successor: PresetRevision = RolePresetRevision(
            preset_id=current.preset_id,
            preset_revision_id=preset_revision_id,
            revision=current.revision + 1,
            name=current.name,
            role_key=current.role_key,
            status="retired",
            created_provenance=created,
            role_label=current.role_label,
            description=current.description,
            applicability_hints=current.applicability_hints,
            supersedes_preset_revision_id=current.preset_revision_id,
        )
    elif isinstance(current, ResponsibilityPresetRevision):
        successor = ResponsibilityPresetRevision(
            preset_id=current.preset_id,
            preset_revision_id=preset_revision_id,
            revision=current.revision + 1,
            name=current.name,
            description=current.description,
            status="retired",
            created_provenance=created,
            expected_output=current.expected_output,
            applicability_hints=current.applicability_hints,
            supersedes_preset_revision_id=current.preset_revision_id,
        )
    elif isinstance(current, ScoringScalePresetRevision):
        successor = ScoringScalePresetRevision(
            preset_id=current.preset_id,
            preset_revision_id=preset_revision_id,
            revision=current.revision + 1,
            name=current.name,
            scale_type=current.scale_type,
            levels=current.levels,
            status="retired",
            created_provenance=created,
            intended_use=current.intended_use,
            aggregation_guidance=current.aggregation_guidance,
            supersedes_preset_revision_id=current.preset_revision_id,
        )
    elif isinstance(current, CriterionSetPresetRevision):
        successor = CriterionSetPresetRevision(
            preset_id=current.preset_id,
            preset_revision_id=preset_revision_id,
            revision=current.revision + 1,
            name=current.name,
            purpose=current.purpose,
            criterion_set_kind=current.criterion_set_kind,
            criteria=current.criteria,
            status="retired",
            created_provenance=created,
            standards_profile_id=current.standards_profile_id,
            supersedes_preset_revision_id=current.preset_revision_id,
        )
    else:
        raise ConcordWorkflowValidationError("unsupported preset type.")
    return _commit_revision(
        successor,
        expected_revision=expected_revision,
        workspace_root=workspace_root,
    )

def prepare_role_preset_application(
    request: ApplyRolePresetRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedRolePresetApplication:
    """Prepare one exact Role preset application without writing canonical state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    require_core_class(root, request.class_id)
    graph, snapshot_revision, _ = load_graph(
        root,
        work_ref(request.class_id, request.activity_id),
        standards_library,
    )
    _require_activity_revision(snapshot_revision, request.expected_snapshot_revision)
    require_activity(graph, request.activity_id)
    preset = _exact_typed(
        root,
        "role",
        request.preset_id,
        request.preset_revision_id,
        RolePresetRevision,
    )
    require_new_identity(
        graph.role_assignments,
        "role_assignment_id",
        request.role_assignment_id,
        "Role Assignment",
    )
    role = _build_role(
        root=root,
        class_id=request.class_id,
        graph=graph,
        role_assignment_id=request.role_assignment_id,
        participant_reference=request.participant_reference,
        role_key=preset.role_key,
        effective_context=request.effective_context,
        status=request.status,
        actor=request.actor,
        membership_id=request.membership_id,
        group_id=request.group_id,
        role_label_snapshot=preset.role_label or preset.name,
        supersedes_role_assignment_id=None,
        clock=clock,
    )
    if role.activity_id != request.activity_id:
        raise ConcordWorkflowValidationError(
            "Role Effective Context must identify the selected Activity."
        )
    _validate_candidate_graph(
        replace(graph, role_assignments=(*graph.role_assignments, role)),
        standards_library,
    )
    return PreparedRolePresetApplication(
        request=request,
        preset_name=preset.name,
        role_key=preset.role_key,
        role_label=preset.role_label,
        review_digest=_review_digest(
            "role-preset-application-v1",
            request,
            preset,
            snapshot_revision,
        ),
    )


def apply_role_preset(
    request: ApplyRolePresetRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> RoleMutationResult:
    """Apply one reviewed Role preset as a fresh Role Assignment."""
    expected_digest = _require_review_digest(review_digest)
    prepared = prepare_role_preset_application(
        request,
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )
    if prepared.review_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Role preset application review is stale; prepare and review it again."
        )
    root = resolve_read_workspace_root(workspace_root)
    assert root is not None
    preset = _exact_typed(
        root,
        "role",
        request.preset_id,
        request.preset_revision_id,
        RolePresetRevision,
    )
    return assign_role(
        AssignRoleRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            role_assignment_id=request.role_assignment_id,
            participant_reference=request.participant_reference,
            role_key=preset.role_key,
            role_label_snapshot=preset.role_label or preset.name,
            effective_context=request.effective_context,
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            status=request.status,
            membership_id=request.membership_id,
            group_id=request.group_id,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )


def prepare_responsibility_preset_application(
    request: ApplyResponsibilityPresetRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedResponsibilityPresetApplication:
    """Prepare one Responsibility preset application without canonical writes."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    require_core_class(root, request.class_id)
    graph, snapshot_revision, _ = load_graph(
        root,
        work_ref(request.class_id, request.activity_id),
        standards_library,
    )
    _require_activity_revision(snapshot_revision, request.expected_snapshot_revision)
    require_activity(graph, request.activity_id)
    preset = _exact_typed(
        root,
        "responsibility",
        request.preset_id,
        request.preset_revision_id,
        ResponsibilityPresetRevision,
    )
    require_new_identity(
        graph.responsibility_assignments,
        "responsibility_assignment_id",
        request.responsibility_assignment_id,
        "Responsibility Assignment",
    )
    responsibility = _build_responsibility(
        root=root,
        class_id=request.class_id,
        graph=graph,
        responsibility_assignment_id=request.responsibility_assignment_id,
        assignee_reference=request.assignee_reference,
        description=preset.description,
        effective_context=request.effective_context,
        status=request.status,
        actor=request.actor,
        group_id=request.group_id,
        work_item_id=request.work_item_id,
        expected_output=preset.expected_output,
        status_reason=request.status_reason,
        supersedes_responsibility_assignment_id=None,
        clock=clock,
    )
    if responsibility.activity_id != request.activity_id:
        raise ConcordWorkflowValidationError(
            "Responsibility Effective Context must identify the selected Activity."
        )
    _validate_candidate_graph(
        replace(
            graph,
            responsibility_assignments=(
                *graph.responsibility_assignments,
                responsibility,
            ),
        ),
        standards_library,
    )
    return PreparedResponsibilityPresetApplication(
        request=request,
        preset_name=preset.name,
        description=preset.description,
        expected_output=preset.expected_output,
        review_digest=_review_digest(
            "responsibility-preset-application-v1",
            request,
            preset,
            snapshot_revision,
        ),
    )


def apply_responsibility_preset(
    request: ApplyResponsibilityPresetRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ResponsibilityMutationResult:
    """Apply one reviewed Responsibility preset as a fresh assignment."""
    expected_digest = _require_review_digest(review_digest)
    prepared = prepare_responsibility_preset_application(
        request,
        workspace_root=workspace_root,
        standards_library=standards_library,
        clock=clock,
    )
    if prepared.review_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Responsibility preset application review is stale; prepare it again."
        )
    root = resolve_read_workspace_root(workspace_root)
    assert root is not None
    preset = _exact_typed(
        root,
        "responsibility",
        request.preset_id,
        request.preset_revision_id,
        ResponsibilityPresetRevision,
    )
    return assign_responsibility(
        AssignResponsibilityRequest(
            class_id=request.class_id,
            activity_id=request.activity_id,
            responsibility_assignment_id=request.responsibility_assignment_id,
            assignee_reference=request.assignee_reference,
            description=preset.description,
            effective_context=request.effective_context,
            expected_snapshot_revision=request.expected_snapshot_revision,
            actor=request.actor,
            status=request.status,
            group_id=request.group_id,
            work_item_id=request.work_item_id,
            expected_output=preset.expected_output,
            status_reason=request.status_reason,
        ),
        workspace_root=root,
        standards_library=standards_library,
        clock=clock,
    )


def _build_scoring_setup(
    request: MaterializeScoringSetupRequest,
    *,
    root: Path,
    standards_library: StandardsLibrary | None,
    clock: Clock | None,
) -> _BuiltScoringSetup:
    require_core_class(root, request.class_id)
    work = work_ref(request.class_id, request.activity_id)
    graph, snapshot_revision, _ = load_graph(root, work, standards_library)
    _require_activity_revision(snapshot_revision, request.expected_snapshot_revision)
    activity = require_activity(graph, request.activity_id)
    criterion_preset = _exact_typed(
        root,
        "criterion_set",
        request.criterion_preset_id,
        request.criterion_preset_revision_id,
        CriterionSetPresetRevision,
    )
    _validate_criterion_preset_standards(
        criterion_preset,
        standards_library,
        activity=activity,
    )
    recommended_scale_preset = _recommended_scale_preset(root, criterion_preset)
    _validate_target_scoring_orientation(activity, criterion_preset)

    identities = {
        item.criterion_key: item.criterion_id for item in request.criterion_ids
    }
    if len(identities) != len(request.criterion_ids):
        raise ConcordWorkflowValidationError(
            "target Criterion identity mapping contains duplicate keys."
        )
    expected_keys = {item.key for item in criterion_preset.criteria}
    if set(identities) != expected_keys:
        raise ConcordWorkflowValidationError(
            "target Criterion identity mapping must cover every preset "
            "Criterion exactly."
        )

    scale_fields = (
        request.scoring_scale_preset_id,
        request.scoring_scale_preset_revision_id,
        request.scoring_scale_id,
        request.scoring_scale_lineage_id,
    )
    if any(value is not None for value in scale_fields) and not all(
        value is not None for value in scale_fields
    ):
        raise ConcordWorkflowValidationError(
            "Scoring Scale preset application requires all Scale identity fields."
        )

    scale: ScoringScale | None = None
    scale_preset: ScoringScalePresetRevision | None = None
    created = provenance(request.actor, clock=clock)
    if request.scoring_scale_preset_id is not None:
        assert request.scoring_scale_preset_revision_id is not None
        assert request.scoring_scale_id is not None
        assert request.scoring_scale_lineage_id is not None
        scale_preset = _exact_typed(
            root,
            "scoring_scale",
            request.scoring_scale_preset_id,
            request.scoring_scale_preset_revision_id,
            ScoringScalePresetRevision,
        )
        require_new_identity(
            graph.scoring_scales,
            "scoring_scale_id",
            request.scoring_scale_id,
            "Scoring Scale",
        )
        if any(
            item.lineage_id == request.scoring_scale_lineage_id
            for item in graph.scoring_scales
        ):
            raise ConcordWorkflowConflictError(
                "Scoring Scale lineage already exists: "
                f"{request.scoring_scale_lineage_id}"
            )
        scale = ScoringScale(
            scoring_scale_id=request.scoring_scale_id,
            lineage_id=request.scoring_scale_lineage_id,
            name=scale_preset.name,
            revision=1,
            scale_type=scale_preset.scale_type,
            levels=scale_preset.levels,
            status="active",
            created_provenance=created,
            intended_use=scale_preset.intended_use,
            aggregation_guidance=scale_preset.aggregation_guidance,
        )

    require_new_identity(
        graph.criterion_sets,
        "criterion_set_id",
        request.criterion_set_id,
        "Criterion Set",
    )
    if any(
        item.lineage_id == request.criterion_set_lineage_id
        for item in graph.criterion_sets
    ):
        raise ConcordWorkflowConflictError(
            f"Criterion Set lineage already exists: {request.criterion_set_lineage_id}"
        )
    for criterion_id in identities.values():
        require_new_identity(graph.criteria, "criterion_id", criterion_id, "Criterion")

    if recommended_scale_preset is not None and scale is None:
        raise ConcordWorkflowValidationError(
            "Criterion preset recommends a Scoring Scale; select the recommended "
            "Scale or an explicit alternative."
        )
    default_scale_id = None if scale is None else scale.scoring_scale_id
    criteria: list[Criterion] = []
    for spec in criterion_preset.criteria:
        criteria.append(
            Criterion(
                criterion_id=identities[spec.key],
                criterion_set_id=request.criterion_set_id,
                key=spec.key,
                label=spec.label,
                definition=spec.definition,
                criterion_kind=spec.criterion_kind,
                supported_target_kinds=spec.supported_target_kinds,
                status=spec.status,
                created_provenance=created,
                standard_id=spec.standard_id,
                alignment_standard_ids=spec.alignment_standard_ids,
                default_scoring_scale_id=default_scale_id,
            )
        )
    criterion_set = CriterionSet(
        criterion_set_id=request.criterion_set_id,
        lineage_id=request.criterion_set_lineage_id,
        name=criterion_preset.name,
        purpose=criterion_preset.purpose,
        revision=1,
        scope="activity_specific",
        criterion_set_kind=criterion_preset.criterion_set_kind,
        criterion_ids=tuple(item.criterion_id for item in criteria),
        status="active",
        created_provenance=created,
        standards_profile_id=criterion_preset.standards_profile_id,
    )
    selected_ids = (*activity.criterion_set_ids, criterion_set.criterion_set_id)
    if len(set(selected_ids)) != len(selected_ids):
        raise ConcordWorkflowConflictError(
            "target Activity already selects the requested Criterion Set identity."
        )
    updated_activity = replace(
        activity,
        criterion_set_ids=selected_ids,
        updated_provenance=created,
    )
    candidate = replace(
        graph,
        activities=tuple(
            updated_activity if item.activity_id == activity.activity_id else item
            for item in graph.activities
        ),
        criterion_sets=(*graph.criterion_sets, criterion_set),
        criteria=(*graph.criteria, *criteria),
        scoring_scales=(
            graph.scoring_scales
            if scale is None
            else (*graph.scoring_scales, scale)
        ),
    )
    _validate_candidate_graph(candidate, standards_library)
    return _BuiltScoringSetup(
        root=root,
        graph=graph,
        snapshot_revision=snapshot_revision,
        work=work,
        criterion_preset=criterion_preset,
        recommended_scale_preset=recommended_scale_preset,
        scale_preset=scale_preset,
        scale=scale,
        criterion_set=criterion_set,
        criteria=tuple(criteria),
        updated_activity=updated_activity,
    )


def prepare_scoring_setup(
    request: MaterializeScoringSetupRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> PreparedScoringSetup:
    """Prepare an exact scoring-preset materialization without canonical writes."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    built = _build_scoring_setup(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )
    return PreparedScoringSetup(
        request=request,
        criterion_preset_name=built.criterion_preset.name,
        criterion_count=len(built.criteria),
        scoring_scale_preset_name=(
            None if built.scale_preset is None else built.scale_preset.name
        ),
        recommended_scoring_scale_preset_id=(
            None
            if built.recommended_scale_preset is None
            else built.recommended_scale_preset.preset_id
        ),
        recommended_scoring_scale_preset_revision_id=(
            None
            if built.recommended_scale_preset is None
            else built.recommended_scale_preset.preset_revision_id
        ),
        recommended_scoring_scale_preset_name=(
            None
            if built.recommended_scale_preset is None
            else built.recommended_scale_preset.name
        ),
        standards_profile_id=built.criterion_preset.standards_profile_id,
        review_digest=_review_digest(
            "scoring-preset-materialization-v1",
            request,
            built.criterion_preset,
            built.recommended_scale_preset,
            built.scale_preset,
            built.snapshot_revision,
        ),
    )


def materialize_scoring_setup(
    request: MaterializeScoringSetupRequest,
    *,
    review_digest: str,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> MaterializeScoringSetupResult:
    """Commit one reviewed, fresh Activity-native scoring setup atomically."""
    expected_digest = _require_review_digest(review_digest)
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    built = _build_scoring_setup(
        request,
        root=root,
        standards_library=standards_library,
        clock=clock,
    )
    current_digest = _review_digest(
        "scoring-preset-materialization-v1",
        request,
        built.criterion_preset,
        built.recommended_scale_preset,
        built.scale_preset,
        built.snapshot_revision,
    )
    if current_digest != expected_digest:
        raise ConcordWorkflowConflictError(
            "Scoring preset review is stale; prepare and review it again."
        )
    records: list[Record] = []
    if built.scale is not None:
        records.append(built.scale)
    records.extend(
        (built.criterion_set, *built.criteria, built.updated_activity)
    )
    result = commit_record_batch(
        root,
        built.work,
        tuple(records),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return MaterializeScoringSetupResult(
        commit=WorkflowCommitResult.from_storage(result),
        criterion_set_id=built.criterion_set.criterion_set_id,
        criterion_ids=built.criterion_set.criterion_ids,
        scoring_scale_id=(
            None if built.scale is None else built.scale.scoring_scale_id
        ),
    )


__all__ = [
    "ApplyResponsibilityPresetRequest",
    "ApplyRolePresetRequest",
    "CreateCriterionSetPresetRequest",
    "CreateResponsibilityPresetRequest",
    "CreateRolePresetRequest",
    "CreateScoringScalePresetRequest",
    "CriterionTargetIdentity",
    "MaterializeScoringSetupRequest",
    "MaterializeScoringSetupResult",
    "PreparedRolePresetApplication",
    "PreparedResponsibilityPresetApplication",
    "PreparedScoringSetup",
    "PreparedPresetSave",
    "SaveCriterionSetPresetFromActivityRequest",
    "SaveResponsibilityPresetFromAssignmentRequest",
    "SaveRolePresetFromAssignmentRequest",
    "SaveScoringScalePresetFromActivityRequest",
    "PresetMutationResult",
    "PresetSummary",
    "ReviseCriterionSetPresetRequest",
    "ReviseResponsibilityPresetRequest",
    "ReviseRolePresetRequest",
    "ReviseScoringScalePresetRequest",
    "apply_responsibility_preset",
    "prepare_responsibility_preset_application",
    "apply_role_preset",
    "prepare_role_preset_application",
    "create_criterion_set_preset",
    "create_responsibility_preset",
    "create_role_preset",
    "create_scoring_scale_preset",
    "get_preset",
    "get_preset_revision",
    "list_presets",
    "materialize_scoring_setup",
    "prepare_scoring_setup",
    "prepare_criterion_set_preset_from_activity",
    "prepare_responsibility_preset_from_assignment",
    "prepare_role_preset_from_assignment",
    "prepare_scoring_scale_preset_from_activity",
    "save_criterion_set_preset_from_activity",
    "save_responsibility_preset_from_assignment",
    "save_role_preset_from_assignment",
    "save_scoring_scale_preset_from_activity",
    "retire_preset",
    "validate_preset",
    "revise_criterion_set_preset",
    "revise_responsibility_preset",
    "revise_role_preset",
    "revise_scoring_scale_preset",
]
