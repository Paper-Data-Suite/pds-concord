"""Safe, zero-write preparation and create-only commit for Activity copying."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.model_validation import (
    ConcordRecordGraph,
    validate_core_standards,
    validate_record_graph,
)
from concord.models import (
    Activity,
    ActorReference,
    ConcordRecordReference,
    PrivacyPolicy,
    Provenance,
    Session,
    SubjectReference,
)
from concord.storage import (
    commit_record_batch,
    list_activity_work_refs,
    load_current_record,
)
from concord.storage_errors import (
    ConcordStorageConflictError,
    ConcordStorageNotFoundError,
)
from concord.validation_diagnostics import ConcordRecordGraphError
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
from concord.workflows.models import (
    UNSET,
    OptionalTextUpdate,
    TextUpdate,
    WorkflowActor,
    WorkflowCommitResult,
)

_COPY_REVIEW_SCHEMA = "concord_activity_copy_review_v1"
_EXCLUDED_STATE = (
    "source lifecycle status and provenance/history",
    "source Sessions beyond the required fresh first target Session",
    "Groups, Memberships, GroupPlans, grouping signals, Roles, and Responsibilities",
    "PacketInstances/generations, Artifacts/Pages/routes, scans, and evidence",
    "Authors, Subjects, Reviews, Moderation, CriterionSets, ScoringScales, and Scores",
    "manifests, Academic Work Registration, publications, catalog history, "
    "and snapshots",
    "source external_reference_ids",
)

_PREVIEW_PROVENANCE = Provenance(
    actor=ActorReference(
        actor_kind="system",
        actor_id="activity-copy-preview",
        owning_system="concord",
    ),
    timestamp="1970-01-01T00:00:00+00:00",
    source_kind="system",
    application_version="preview",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityCopyDiagnostic:
    """One visible, deterministic preparation diagnostic."""

    code: str
    message: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PrepareActivityCopyRequest:
    """Explicit source/target inputs for zero-write Activity-copy preparation."""

    source_class_id: str
    source_activity_id: str
    target_class_id: str
    target_activity_id: str
    first_session_id: str
    title: TextUpdate = UNSET
    description: OptionalTextUpdate = UNSET
    first_session_label: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PreparedActivityCopy:
    """Exact teacher-review surface for one proposed independent Activity."""

    source_class_id: str
    source_activity_id: str
    source_status: str
    target_class_id: str
    target_activity_id: str
    title: str
    description: str | None
    activity_type: str
    scoring_orientation: str
    standards_profile_id: str | None
    focus_standard_ids: tuple[str, ...]
    privacy_policy: PrivacyPolicy | None
    first_session_id: str
    first_session_label: str | None
    diagnostics: tuple[ActivityCopyDiagnostic, ...]
    excluded_state: tuple[str, ...]
    review_digest: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CopyActivityRequest:
    """Commit request that must reproduce one exact reviewed preparation."""

    source_class_id: str
    source_activity_id: str
    target_class_id: str
    target_activity_id: str
    first_session_id: str
    actor: WorkflowActor
    review_digest: str
    title: TextUpdate = UNSET
    description: OptionalTextUpdate = UNSET
    first_session_label: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivityCopyResult:
    """Committed identity for a fresh copied Activity work graph."""

    commit: WorkflowCommitResult
    activity_id: str
    first_session_id: str
    review_digest: str


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef(module_id="concord", class_id=class_id, work_id=activity_id)


def _resolve_title(source: Activity, value: TextUpdate) -> str:
    if isinstance(value, str):
        return value
    return source.title


def _resolve_description(source: Activity, value: OptionalTextUpdate) -> str | None:
    if isinstance(value, str) or value is None:
        return value
    return source.description


def _subject_reference_payload(reference: SubjectReference) -> dict[str, Any]:
    return {
        "subject_kind": reference.subject_kind,
        "subject_id": reference.subject_id,
        "owning_system": reference.owning_system,
        "contract_version": reference.contract_version,
    }


def _module_reference_payload(
    reference: ModuleRecordRef | None,
) -> dict[str, Any] | None:
    if reference is None:
        return None
    return {
        "module_id": reference.module_id,
        "record_kind": reference.record_kind,
        "record_id": reference.record_id,
        "contract_version": reference.contract_version,
    }


def _concord_reference_payload(
    reference: ConcordRecordReference | None,
) -> dict[str, Any] | None:
    if reference is None:
        return None
    return {
        "record_kind": reference.record_kind,
        "record_id": reference.record_id,
        "contract_version": reference.contract_version,
    }


def _privacy_payload(policy: PrivacyPolicy | None) -> dict[str, Any] | None:
    if policy is None:
        return None
    return {
        "classification": policy.classification,
        "audience_references": [
            _subject_reference_payload(item) for item in policy.audience_references
        ],
        "policy_reference": _module_reference_payload(policy.policy_reference),
        "reason": policy.reason,
        "inherited_from": _concord_reference_payload(policy.inherited_from),
    }


def _resolve_privacy(
    policy: PrivacyPolicy | None,
) -> tuple[PrivacyPolicy | None, tuple[ActivityCopyDiagnostic, ...]]:
    if policy is None:
        return None, ()
    context_free = (
        not policy.audience_references
        and policy.policy_reference is None
        and policy.inherited_from is None
    )
    if context_free and policy.classification in {
        "teacher_restricted",
        "classroom_shared",
    }:
        return (
            PrivacyPolicy(classification=policy.classification),
            (),
        )
    return (
        PrivacyPolicy(classification="teacher_restricted"),
        (
            ActivityCopyDiagnostic(
                code="privacy_context_not_copied",
                message=(
                    "Source privacy depends on source-context audience or policy "
                    "references. The target is restricted to teacher_restricted; "
                    "source audience/reference state will not be copied."
                ),
            ),
        ),
    )


def _source_activity(
    root: Path,
    request: PrepareActivityCopyRequest,
) -> Activity:
    require_core_class(root, request.source_class_id)
    work = _work(request.source_class_id, request.source_activity_id)
    try:
        record, _ = load_current_record(
            root,
            work,
            "activity",
            request.source_activity_id,
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            "Source Activity is not available: "
            f"{request.source_class_id}/{request.source_activity_id}"
        ) from error
    if not isinstance(record, Activity):
        raise ConcordWorkflowNotFoundError(
            "Source Activity is not available: "
            f"{request.source_class_id}/{request.source_activity_id}"
        )
    if record.activity_id != request.source_activity_id:
        raise ConcordWorkflowValidationError(
            "Source Activity identity disagrees with its canonical work path."
        )
    return record


def _target_is_available(root: Path, request: PrepareActivityCopyRequest) -> None:
    if (
        request.source_class_id == request.target_class_id
        and request.source_activity_id == request.target_activity_id
    ):
        raise ConcordWorkflowValidationError(
            "The exact source Activity work cannot be its own copy destination."
        )
    require_core_class(root, request.target_class_id)
    target = _work(request.target_class_id, request.target_activity_id)
    if target in list_activity_work_refs(root, request.target_class_id):
        raise ConcordWorkflowConflictError(
            "Target Activity already exists: "
            f"{request.target_class_id}/{request.target_activity_id}"
        )


def _validate_prepared_graph(
    activity: Activity,
    session: Session,
    standards_library: StandardsLibrary | None,
) -> None:
    graph = ConcordRecordGraph(activities=(activity,), sessions=(session,))
    try:
        validate_record_graph(graph)
    except (ConcordRecordGraphError, ValueError) as error:
        raise ConcordWorkflowValidationError(
            f"Prepared target Activity is invalid: {error}"
        ) from error

    has_standards = (
        activity.standards_profile_id is not None or bool(activity.focus_standard_ids)
    )
    if not has_standards:
        return
    if activity.standards_profile_id is None:
        raise ConcordWorkflowValidationError(
            "Source Focus Standards cannot be copied without a standards profile."
        )
    if standards_library is None:
        raise ConcordWorkflowValidationError(
            "A current Core standards library is required to copy this Activity."
        )
    try:
        validate_core_standards(graph, standards_library)
    except (ConcordRecordGraphError, ValueError) as error:
        raise ConcordWorkflowValidationError(
            "Source Activity standards configuration is no longer valid in the "
            f"current Core standards library: {error}"
        ) from error


def _review_payload(
    source: Activity,
    request: PrepareActivityCopyRequest,
    *,
    title: str,
    description: str | None,
    privacy_policy: PrivacyPolicy | None,
) -> dict[str, Any]:
    title_from_source = request.title is UNSET
    description_from_source = request.description is UNSET
    return {
        "schema": _COPY_REVIEW_SCHEMA,
        "source": {
            "class_id": request.source_class_id,
            "activity_id": request.source_activity_id,
            "title": source.title if title_from_source else None,
            "description": source.description if description_from_source else None,
            "activity_type": source.activity_type,
            "scoring_orientation": source.scoring_orientation,
            "standards_profile_id": source.standards_profile_id,
            "focus_standard_ids": list(source.focus_standard_ids),
            "privacy_policy": _privacy_payload(source.privacy_policy),
        },
        "target": {
            "class_id": request.target_class_id,
            "activity_id": request.target_activity_id,
            "title_mode": "source" if title_from_source else "override",
            "title": title,
            "description_mode": "source" if description_from_source else "override",
            "description": description,
            "activity_type": source.activity_type,
            "scoring_orientation": source.scoring_orientation,
            "status": "draft",
            "standards_profile_id": source.standards_profile_id,
            "focus_standard_ids": list(source.focus_standard_ids),
            "criterion_set_ids": [],
            "privacy_policy": _privacy_payload(privacy_policy),
            "external_reference_ids": [],
            "first_session": {
                "session_id": request.first_session_id,
                "sequence": 1,
                "status": "planned",
                "label": request.first_session_label,
            },
        },
    }


def _review_digest(payload: dict[str, Any]) -> str:
    data = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def prepare_activity_copy(
    request: PrepareActivityCopyRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
) -> PreparedActivityCopy:
    """Prepare an exact Activity copy without creating or mutating any state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")

    source = _source_activity(root, request)
    _target_is_available(root, request)
    target_metadata = require_core_class(root, request.target_class_id)
    title = _resolve_title(source, request.title)
    description = _resolve_description(source, request.description)
    privacy_policy, diagnostics = _resolve_privacy(source.privacy_policy)

    target_activity = Activity(
        activity_id=request.target_activity_id,
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id=target_metadata.class_id,
        ),
        title=title,
        activity_type=source.activity_type,
        scoring_orientation=source.scoring_orientation,
        status="draft",
        created_provenance=_PREVIEW_PROVENANCE,
        standards_profile_id=source.standards_profile_id,
        focus_standard_ids=source.focus_standard_ids,
        description=description,
        criterion_set_ids=(),
        privacy_policy=privacy_policy,
        external_reference_ids=(),
    )
    first_session = Session(
        session_id=request.first_session_id,
        activity_id=target_activity.activity_id,
        sequence=1,
        status="planned",
        created_provenance=_PREVIEW_PROVENANCE,
        label=request.first_session_label,
    )
    _validate_prepared_graph(target_activity, first_session, standards_library)

    extra_diagnostics: list[ActivityCopyDiagnostic] = list(diagnostics)
    if source.criterion_set_ids:
        extra_diagnostics.append(
            ActivityCopyDiagnostic(
                code="criterion_sets_not_copied",
                message=(
                    "Source Activity Criterion Set selections are Activity-owned and "
                    "will not be copied. The target starts with criterion_set_ids=()."
                ),
            )
        )
    if source.external_reference_ids:
        extra_diagnostics.append(
            ActivityCopyDiagnostic(
                code="external_references_not_copied",
                message=(
                    "Source external_reference_ids are contextual relationships and "
                    "will not be copied."
                ),
            )
        )

    payload = _review_payload(
        source,
        request,
        title=title,
        description=description,
        privacy_policy=privacy_policy,
    )
    return PreparedActivityCopy(
        source_class_id=request.source_class_id,
        source_activity_id=request.source_activity_id,
        source_status=source.status,
        target_class_id=request.target_class_id,
        target_activity_id=request.target_activity_id,
        title=title,
        description=description,
        activity_type=source.activity_type,
        scoring_orientation=source.scoring_orientation,
        standards_profile_id=source.standards_profile_id,
        focus_standard_ids=source.focus_standard_ids,
        privacy_policy=privacy_policy,
        first_session_id=request.first_session_id,
        first_session_label=request.first_session_label,
        diagnostics=tuple(extra_diagnostics),
        excluded_state=_EXCLUDED_STATE,
        review_digest=_review_digest(payload),
    )


def _prepare_request(request: CopyActivityRequest) -> PrepareActivityCopyRequest:
    return PrepareActivityCopyRequest(
        source_class_id=request.source_class_id,
        source_activity_id=request.source_activity_id,
        target_class_id=request.target_class_id,
        target_activity_id=request.target_activity_id,
        first_session_id=request.first_session_id,
        title=request.title,
        description=request.description,
        first_session_label=request.first_session_label,
    )


def copy_activity(
    request: CopyActivityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ActivityCopyResult:
    """Commit one exact reviewed copy as a fresh Activity plus fresh first Session."""
    prepared = prepare_activity_copy(
        _prepare_request(request),
        workspace_root=workspace_root,
        standards_library=standards_library,
    )
    if request.review_digest != prepared.review_digest:
        raise ConcordWorkflowConflictError(
            "Activity copy review is stale or does not match the requested target. "
            "Run copy preparation again and review the new digest."
        )

    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    target_metadata = require_core_class(root, prepared.target_class_id)
    created = provenance(request.actor, clock=clock)
    activity = Activity(
        activity_id=prepared.target_activity_id,
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id=target_metadata.class_id,
        ),
        title=prepared.title,
        activity_type=prepared.activity_type,
        scoring_orientation=prepared.scoring_orientation,
        status="draft",
        created_provenance=created,
        standards_profile_id=prepared.standards_profile_id,
        focus_standard_ids=prepared.focus_standard_ids,
        description=prepared.description,
        criterion_set_ids=(),
        privacy_policy=prepared.privacy_policy,
        external_reference_ids=(),
    )
    session = Session(
        session_id=prepared.first_session_id,
        activity_id=activity.activity_id,
        sequence=1,
        status="planned",
        created_provenance=created,
        label=prepared.first_session_label,
    )

    try:
        result = commit_record_batch(
            root,
            activity.work_reference,
            (activity, session),
            expected_snapshot_revision=None,
            standards_library=standards_library,
        )
    except ConcordStorageConflictError as error:
        raise ConcordWorkflowConflictError(str(error)) from error
    if result.no_op:
        # A concurrent creator may have won the race after preparation. Treat even
        # byte-identical target state as a conflict: Activity copy is create-only.
        raise ConcordWorkflowConflictError(
            "Target Activity already exists; copy is create-only."
        )

    return ActivityCopyResult(
        commit=WorkflowCommitResult.from_storage(result),
        activity_id=activity.activity_id,
        first_session_id=session.session_id,
        review_digest=prepared.review_digest,
    )
