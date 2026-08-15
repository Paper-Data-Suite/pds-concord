from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pds_core.class_metadata import (
    create_class_metadata,
    write_class_metadata_for_class,
)
from pds_core.workspace import ensure_workspace_root

from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationConflictError,
    ConcordAcademicWorkRegistrationNotFoundError,
    ConcordAcademicWorkRegistrationValidationError,
    ManagedActivityRegistrationContext,
    build_concord_academic_work_registration_request,
    list_concord_academic_work_registration_revisions,
    load_concord_academic_work_registration_revision,
    load_current_concord_academic_work_registration,
    load_managed_activity_registration_context,
    register_concord_academic_work,
    update_concord_academic_work_registration,
)
from concord.pds_contract import (
    ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION,
    ACADEMIC_RESULT_MANIFEST_RECORD_TYPE,
    CONCORD_ACADEMIC_RESULT_RECORD_SET_ID,
    CONCORD_ACADEMIC_WORK_CONTRACT_VERSION,
    CONCORD_ACADEMIC_WORK_KIND,
    CONCORD_ACTIVITY_CONTRACT_VERSION,
    CONCORD_ACTIVITY_RECORD_KIND,
    CONCORD_MODULE_ID,
)
from concord.workflows import (
    CreateActivityContextRequest,
    UpdateActivityRequest,
    WorkflowActor,
    create_activity_context,
    update_activity,
)


def _clock(hour: int) -> datetime:
    return datetime(2026, 8, 14, hour, 0, tzinfo=timezone.utc)


def _workspace(tmp_path: Path, *, title: str = "Synthetic Activity") -> Path:
    root = ensure_workspace_root(tmp_path / "workspace")
    metadata = create_class_metadata(
        "class-1",
        "2026-2027",
        created_at=_clock(12),
    )
    write_class_metadata_for_class(root, metadata)
    create_activity_context(
        CreateActivityContextRequest(
            class_id="class-1",
            activity_id="activity-1",
            title=title,
            activity_type="project",
            scoring_orientation="evidence_only",
            session_id="session-1",
            actor=WorkflowActor(actor_id="teacher-1"),
            activity_status="active",
            session_status="active",
        ),
        workspace_root=root,
        clock=lambda: _clock(13),
    )
    return root


def test_public_contract_identities_are_stable() -> None:
    assert CONCORD_MODULE_ID == "concord"
    assert CONCORD_ACADEMIC_WORK_CONTRACT_VERSION == (
        "concord_academic_work_v1"
    )
    assert CONCORD_ACADEMIC_WORK_KIND == "collaborative_activity"
    assert CONCORD_ACTIVITY_RECORD_KIND == "activity"
    assert CONCORD_ACTIVITY_CONTRACT_VERSION == "concord_activity_v1"
    assert ACADEMIC_RESULT_MANIFEST_CONTRACT_VERSION == (
        "concord_academic_result_manifest_v1"
    )
    assert ACADEMIC_RESULT_MANIFEST_RECORD_TYPE == (
        "concord_academic_result_manifest"
    )
    assert CONCORD_ACADEMIC_RESULT_RECORD_SET_ID == "academic_results"


def test_registration_context_and_request_use_exact_activity_source(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    context = load_managed_activity_registration_context(
        root, "class-1", "activity-1"
    )
    request = build_concord_academic_work_registration_request(
        context,
        academic_intent="summative",
        lifecycle="active",
    )

    assert context.work.module_id == "concord"
    assert context.work.class_id == "class-1"
    assert context.work.work_id == "activity-1"
    assert context.snapshot_revision == 1
    assert context.source_record.module_id == "concord"
    assert context.source_record.record_kind == "activity"
    assert context.source_record.record_id == "activity-1"
    assert context.source_record.contract_version == "concord_activity_v1"

    assert request.work == context.work
    assert request.title == "Synthetic Activity"
    assert request.work_kind == "collaborative_activity"
    assert request.producer_contract_version == "concord_academic_work_v1"
    assert request.academic_intent == "summative"
    assert request.lifecycle == "active"
    assert request.source_records == (context.source_record,)


def test_registration_is_explicit_idempotent_and_versioned(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)

    assert (
        load_current_concord_academic_work_registration(
            root, "class-1", "activity-1"
        )
        is None
    )
    assert (
        load_managed_activity_registration_context(
            root, "class-1", "activity-1"
        ).snapshot_revision
        == 1
    )

    first = register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )
    assert first.disposition == "created"
    assert first.registration.registration_revision == 1

    replay = register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )
    assert replay.disposition == "existing"
    assert replay.registration == first.registration
    assert list_concord_academic_work_registration_revisions(
        root, "class-1", "activity-1"
    ) == (1,)

    with pytest.raises(ConcordAcademicWorkRegistrationConflictError):
        register_concord_academic_work(
            root,
            "class-1",
            "activity-1",
            academic_intent="formative",
            lifecycle="active",
        )


def test_activity_change_does_not_mutate_registration_until_explicit_update(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    first = register_concord_academic_work(
        root,
        "class-1",
        "activity-1",
        academic_intent="summative",
        lifecycle="active",
    )

    updated_activity = update_activity(
        UpdateActivityRequest(
            class_id="class-1",
            activity_id="activity-1",
            expected_snapshot_revision=1,
            actor=WorkflowActor(actor_id="teacher-1"),
            title="Revised Activity Title",
        ),
        workspace_root=root,
        clock=lambda: _clock(14),
    )
    assert updated_activity.commit.snapshot_revision == 2

    unchanged_registration = load_current_concord_academic_work_registration(
        root, "class-1", "activity-1"
    )
    assert unchanged_registration == first.registration
    assert unchanged_registration is not None
    assert unchanged_registration.title == "Synthetic Activity"

    second = update_concord_academic_work_registration(
        root,
        "class-1",
        "activity-1",
        academic_intent="formative",
        lifecycle="closed",
        expected_current_revision=1,
    )
    assert second.disposition == "updated"
    assert second.registration.registration_revision == 2
    assert second.registration.title == "Revised Activity Title"
    assert second.registration.academic_intent == "formative"
    assert second.registration.lifecycle == "closed"
    assert second.registration.created_at == first.registration.created_at
    assert second.registration.updated_at >= first.registration.updated_at

    assert list_concord_academic_work_registration_revisions(
        root, "class-1", "activity-1"
    ) == (1, 2)
    historical = load_concord_academic_work_registration_revision(
        root, "class-1", "activity-1", 1
    )
    assert historical == first.registration

    stale_replay = update_concord_academic_work_registration(
        root,
        "class-1",
        "activity-1",
        academic_intent="formative",
        lifecycle="closed",
        expected_current_revision=1,
    )
    assert stale_replay.disposition == "existing"
    assert stale_replay.registration == second.registration

    with pytest.raises(ConcordAcademicWorkRegistrationConflictError):
        update_concord_academic_work_registration(
            root,
            "class-1",
            "activity-1",
            academic_intent="diagnostic",
            lifecycle="active",
            expected_current_revision=1,
        )

    with pytest.raises(ConcordAcademicWorkRegistrationConflictError):
        update_concord_academic_work_registration(
            root,
            "class-1",
            "activity-1",
            academic_intent="diagnostic",
            lifecycle="active",
            expected_current_revision=99,
        )


def test_registration_rejects_missing_activity_and_invalid_public_title(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)

    with pytest.raises(ConcordAcademicWorkRegistrationNotFoundError):
        load_managed_activity_registration_context(
            root, "class-1", "activity-missing"
        )

    context = load_managed_activity_registration_context(
        root, "class-1", "activity-1"
    )
    unsafe = ManagedActivityRegistrationContext(
        work=context.work,
        source_record=context.source_record,
        title="Unsafe\nTitle",
        snapshot_revision=context.snapshot_revision,
    )
    with pytest.raises(ConcordAcademicWorkRegistrationValidationError):
        build_concord_academic_work_registration_request(
            unsafe,
            academic_intent="summative",
            lifecycle="active",
        )


def test_academic_intent_and_lifecycle_are_not_inferred_from_activity(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    context = load_managed_activity_registration_context(
        root, "class-1", "activity-1"
    )

    formative_closed = build_concord_academic_work_registration_request(
        context,
        academic_intent="formative",
        lifecycle="closed",
    )
    reporting_planned = build_concord_academic_work_registration_request(
        context,
        academic_intent="reporting_only",
        lifecycle="planned",
    )

    assert formative_closed.academic_intent == "formative"
    assert formative_closed.lifecycle == "closed"
    assert reporting_planned.academic_intent == "reporting_only"
    assert reporting_planned.lifecycle == "planned"
