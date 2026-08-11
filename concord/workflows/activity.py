"""Application services for Activity creation, inspection, and revision."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from pds_core.routing_models import ModuleRecordRef, ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.models import Activity, Session
from concord.storage import (
    commit_record_batch,
    list_activity_work_refs,
    load_current_record,
    load_current_snapshot,
    load_work_snapshot,
)
from concord.storage_errors import ConcordStorageNotFoundError
from concord.workflows.context import (
    Clock,
    ensure_mutating_workspace_root,
    list_available_classes,
    provenance,
    require_core_class,
    resolve_read_workspace_root,
)
from concord.workflows.errors import ConcordWorkflowNotFoundError
from concord.workflows.models import (
    ActivityContextResult,
    ActivityDetail,
    ActivitySummary,
    ActivityUpdateResult,
    CreateActivityContextRequest,
    UpdateActivityRequest,
    WorkflowCommitResult,
    resolve_update,
)


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef(module_id="concord", class_id=class_id, work_id=activity_id)


def _activity_and_counts(
    root: Path,
    work: ModuleWorkRef,
) -> tuple[Activity, int, int, int]:
    current = load_current_snapshot(root, work)
    snapshot, _ = load_work_snapshot(root, work, current.snapshot_revision)
    activity_record, _ = load_current_record(
        root,
        work,
        "activity",
        work.work_id,
    )
    if not isinstance(activity_record, Activity):
        raise ConcordWorkflowNotFoundError(
            f"Current Activity record is unavailable: {work.work_id}"
        )
    session_count = sum(item.record_kind == "session" for item in snapshot.records)
    group_count = sum(item.record_kind == "group" for item in snapshot.records)
    return activity_record, session_count, group_count, current.snapshot_revision


def _summary(root: Path, work: ModuleWorkRef) -> ActivitySummary:
    activity, session_count, group_count, snapshot_revision = _activity_and_counts(
        root, work
    )
    return ActivitySummary(
        class_id=work.class_id,
        activity_id=activity.activity_id,
        title=activity.title,
        status=activity.status,
        scoring_orientation=activity.scoring_orientation,
        session_count=session_count,
        group_count=group_count,
        snapshot_revision=snapshot_revision,
    )


def create_activity_context(
    request: CreateActivityContextRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ActivityContextResult:
    """Create one Activity and its required first Session atomically."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    metadata = require_core_class(root, request.class_id)
    created = provenance(request.actor, clock=clock)
    activity = Activity(
        activity_id=request.activity_id,
        class_reference=ModuleRecordRef(
            module_id="core",
            record_kind="class",
            record_id=metadata.class_id,
        ),
        title=request.title,
        activity_type=request.activity_type,
        scoring_orientation=request.scoring_orientation,
        status=request.activity_status,
        created_provenance=created,
        standards_profile_id=request.standards_profile_id,
        focus_standard_ids=request.focus_standard_ids,
        description=request.description,
        privacy_policy=request.privacy_policy,
        external_reference_ids=request.external_reference_ids,
    )
    session = Session(
        session_id=request.session_id,
        activity_id=activity.activity_id,
        sequence=request.session_sequence,
        status=request.session_status,
        created_provenance=created,
        label=request.session_label,
        scheduled_start=request.scheduled_start,
        scheduled_end=request.scheduled_end,
        notes=request.session_notes,
    )
    result = commit_record_batch(
        root,
        activity.work_reference,
        (activity, session),
        expected_snapshot_revision=None,
        standards_library=standards_library,
    )
    return ActivityContextResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        activity_id=activity.activity_id,
        first_session_id=session.session_id,
    )


def list_activities(
    *,
    workspace_root: str | Path | None = None,
    class_id: str | None = None,
) -> tuple[ActivitySummary, ...]:
    """List compact Activity summaries without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    class_ids: tuple[str, ...]
    if class_id is not None:
        class_ids = (class_id,)
    else:
        class_ids = tuple(item.class_id for item in list_available_classes(root))
    summaries: list[ActivitySummary] = []
    for current_class_id in class_ids:
        for work in list_activity_work_refs(root, current_class_id):
            summaries.append(_summary(root, work))
    return tuple(sorted(summaries, key=lambda item: (item.class_id, item.activity_id)))


def show_activity(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> ActivityDetail:
    """Load one compact Activity detail view without requiring SQLite."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    work = _work(class_id, activity_id)
    try:
        activity, session_count, group_count, snapshot_revision = _activity_and_counts(
            root, work
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {activity_id}"
        ) from error
    summary = ActivitySummary(
        class_id=class_id,
        activity_id=activity.activity_id,
        title=activity.title,
        status=activity.status,
        scoring_orientation=activity.scoring_orientation,
        session_count=session_count,
        group_count=group_count,
        snapshot_revision=snapshot_revision,
    )
    return ActivityDetail(
        summary=summary,
        description=activity.description,
        activity_type=activity.activity_type,
        standards_profile_id=activity.standards_profile_id,
        focus_standard_ids=activity.focus_standard_ids,
    )


def update_activity(
    request: UpdateActivityRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> ActivityUpdateResult:
    """Revise one existing Activity under exact-snapshot concurrency control."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = _work(request.class_id, request.activity_id)
    try:
        current_record, _ = load_current_record(
            root, work, "activity", request.activity_id
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {request.activity_id}"
        ) from error
    if not isinstance(current_record, Activity):
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {request.activity_id}"
        )

    candidate = Activity(
        activity_id=current_record.activity_id,
        class_reference=current_record.class_reference,
        title=resolve_update(current_record.title, request.title),
        activity_type=resolve_update(
            current_record.activity_type, request.activity_type
        ),
        scoring_orientation=resolve_update(
            current_record.scoring_orientation,
            request.scoring_orientation,
        ),
        status=resolve_update(current_record.status, request.status),
        created_provenance=current_record.created_provenance,
        standards_profile_id=resolve_update(
            current_record.standards_profile_id,
            request.standards_profile_id,
        ),
        focus_standard_ids=resolve_update(
            current_record.focus_standard_ids,
            request.focus_standard_ids,
        ),
        description=resolve_update(current_record.description, request.description),
        criterion_set_ids=current_record.criterion_set_ids,
        privacy_policy=resolve_update(
            current_record.privacy_policy,
            request.privacy_policy,
        ),
        updated_provenance=current_record.updated_provenance,
        external_reference_ids=resolve_update(
            current_record.external_reference_ids,
            request.external_reference_ids,
        ),
    )
    if candidate != current_record:
        candidate = replace(
            candidate,
            updated_provenance=provenance(request.actor, clock=clock),
        )

    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return ActivityUpdateResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        activity_id=candidate.activity_id,
    )
