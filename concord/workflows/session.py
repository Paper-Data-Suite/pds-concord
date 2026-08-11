"""Application services for Session creation, inspection, and revision."""

from __future__ import annotations

from pathlib import Path

from pds_core.routing_models import ModuleWorkRef
from pds_core.standards import StandardsLibrary

from concord.models import Activity, Session
from concord.storage import (
    commit_record_batch,
    load_current_record,
    load_current_snapshot,
    load_record_revision,
    load_work_snapshot,
)
from concord.storage_errors import ConcordStorageNotFoundError
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
)
from concord.workflows.models import (
    CreateSessionRequest,
    SessionMutationResult,
    SessionSummary,
    UpdateSessionRequest,
    WorkflowCommitResult,
    resolve_update,
)


def _work(class_id: str, activity_id: str) -> ModuleWorkRef:
    return ModuleWorkRef(module_id="concord", class_id=class_id, work_id=activity_id)


def _require_activity(root: Path, work: ModuleWorkRef) -> Activity:
    try:
        record, _ = load_current_record(root, work, "activity", work.work_id)
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {work.work_id}"
        ) from error
    if not isinstance(record, Activity):
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {work.work_id}"
        )
    return record


def create_session(
    request: CreateSessionRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> SessionMutationResult:
    """Add one Session to an existing Activity."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = _work(request.class_id, request.activity_id)
    _require_activity(root, work)
    try:
        load_current_record(root, work, "session", request.session_id)
    except ConcordStorageNotFoundError:
        pass
    else:
        raise ConcordWorkflowConflictError(
            f"Session already exists: {request.session_id}"
        )
    session = Session(
        session_id=request.session_id,
        activity_id=request.activity_id,
        sequence=request.sequence,
        status=request.status,
        created_provenance=provenance(request.actor, clock=clock),
        label=request.label,
        scheduled_start=request.scheduled_start,
        scheduled_end=request.scheduled_end,
        actual_start=request.actual_start,
        actual_end=request.actual_end,
        status_reason=request.status_reason,
        notes=request.notes,
    )
    result = commit_record_batch(
        root,
        work,
        (session,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return SessionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        session_id=session.session_id,
    )


def list_sessions(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> tuple[SessionSummary, ...]:
    """List current Sessions ordered by sequence without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return ()
    work = _work(class_id, activity_id)
    try:
        current = load_current_snapshot(root, work)
        snapshot, _ = load_work_snapshot(root, work, current.snapshot_revision)
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Activity is not available: {activity_id}"
        ) from error
    summaries: list[SessionSummary] = []
    for reference in snapshot.records:
        if reference.record_kind != "session":
            continue
        record, _ = load_record_revision(
            root,
            work,
            reference.record_kind,
            reference.record_id,
            reference.record_revision,
        )
        if not isinstance(record, Session):
            continue
        summaries.append(
            SessionSummary(
                class_id=class_id,
                activity_id=activity_id,
                session_id=record.session_id,
                sequence=record.sequence,
                label=record.label,
                status=record.status,
                scheduled_start=record.scheduled_start,
                snapshot_revision=current.snapshot_revision,
            )
        )
    return tuple(sorted(summaries, key=lambda item: (item.sequence, item.session_id)))


def show_session(
    class_id: str,
    activity_id: str,
    session_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> Session:
    """Load one current Session without creating workspace state."""
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        raise ConcordWorkflowNotFoundError("Paper Data Suite workspace does not exist.")
    work = _work(class_id, activity_id)
    try:
        record, _ = load_current_record(root, work, "session", session_id)
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Session is not available: {session_id}"
        ) from error
    if not isinstance(record, Session):
        raise ConcordWorkflowNotFoundError(f"Session is not available: {session_id}")
    return record


def update_session(
    request: UpdateSessionRequest,
    *,
    workspace_root: str | Path | None = None,
    standards_library: StandardsLibrary | None = None,
    clock: Clock | None = None,
) -> SessionMutationResult:
    """Revise one Session under exact-snapshot concurrency control."""
    bootstrap = ensure_mutating_workspace_root(workspace_root)
    root = bootstrap.root
    require_core_class(root, request.class_id)
    work = _work(request.class_id, request.activity_id)
    _require_activity(root, work)
    try:
        current_record, _ = load_current_record(
            root,
            work,
            "session",
            request.session_id,
        )
    except ConcordStorageNotFoundError as error:
        raise ConcordWorkflowNotFoundError(
            f"Session is not available: {request.session_id}"
        ) from error
    if not isinstance(current_record, Session):
        raise ConcordWorkflowNotFoundError(
            f"Session is not available: {request.session_id}"
        )

    # Session currently has creation provenance only; storage history records later
    # revisions without fabricating a second provenance field not present in #24.
    candidate = Session(
        session_id=current_record.session_id,
        activity_id=current_record.activity_id,
        sequence=resolve_update(current_record.sequence, request.sequence),
        status=resolve_update(current_record.status, request.status),
        created_provenance=current_record.created_provenance,
        label=resolve_update(current_record.label, request.label),
        scheduled_start=resolve_update(
            current_record.scheduled_start,
            request.scheduled_start,
        ),
        scheduled_end=resolve_update(
            current_record.scheduled_end,
            request.scheduled_end,
        ),
        actual_start=resolve_update(current_record.actual_start, request.actual_start),
        actual_end=resolve_update(current_record.actual_end, request.actual_end),
        status_reason=resolve_update(
            current_record.status_reason,
            request.status_reason,
        ),
        notes=resolve_update(current_record.notes, request.notes),
    )
    # The #24 Session model has creation provenance only. Actor/clock remain part
    # of the workflow request surface for consistent mutating-command context, but
    # an ordinary storage revision must not invent a native updated-provenance field.

    result = commit_record_batch(
        root,
        work,
        (candidate,),
        expected_snapshot_revision=request.expected_snapshot_revision,
        standards_library=standards_library,
    )
    return SessionMutationResult(
        commit=WorkflowCommitResult.from_storage(
            result,
            workspace_created=bootstrap.created,
        ),
        session_id=candidate.session_id,
    )
