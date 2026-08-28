"""Read-only attention interpretation for Concord academic-result sharing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from concord.academic_result_manifest import RevisionReason
from concord.academic_result_manifest_generation import (
    ConcordManifestGenerationError,
    GenerateAcademicResultManifestRequest,
    preview_academic_result_manifest,
)
from concord.academic_result_publication import (
    ConcordAcademicResultPublicationError,
    load_concord_publication_series_status,
)
from concord.academic_work_registration import (
    ConcordAcademicWorkRegistrationError,
    load_current_concord_academic_work_registration,
    load_managed_activity_registration_context,
)
from concord.workflows.context import resolve_read_workspace_root
from concord.workflows.models import WorkflowActor

AcademicResultShareAttentionStatus: TypeAlias = Literal[
    "inactive",
    "manifest_needed",
    "publish_ready",
    "supersede_ready",
    "current",
    "withdrawn",
    "needs_inspection",
]

_ATTENTION_ACTOR = WorkflowActor(
    actor_id="attention_projection",
    actor_kind="system",
    owning_system="concord",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class AcademicResultShareAttentionState:
    """Privacy-minimal current state for one Activity publication series."""

    class_id: str
    activity_id: str
    status: AcademicResultShareAttentionStatus


def _state(
    class_id: str,
    activity_id: str,
    status: AcademicResultShareAttentionStatus,
) -> AcademicResultShareAttentionState:
    return AcademicResultShareAttentionState(
        class_id=class_id,
        activity_id=activity_id,
        status=status,
    )


def inspect_academic_result_share_attention_state(
    class_id: str,
    activity_id: str,
    *,
    workspace_root: str | Path | None = None,
) -> AcademicResultShareAttentionState:
    """Interpret existing Share workflow state without generating or publishing.

    No Academic Work Registration means the teacher has not entered Concord's
    explicit Share workflow, so publication absence alone is not attention.
    Once registration exists, this reader reuses the manifest preview and
    publication-series reconciliation authorities rather than recreating their
    comparison rules.
    """
    root = resolve_read_workspace_root(workspace_root)
    if root is None:
        return _state(class_id, activity_id, "inactive")

    try:
        registration = load_current_concord_academic_work_registration(
            root,
            class_id,
            activity_id,
        )
    except ConcordAcademicWorkRegistrationError:
        return _state(class_id, activity_id, "needs_inspection")
    if registration is None:
        return _state(class_id, activity_id, "inactive")

    try:
        context = load_managed_activity_registration_context(
            root,
            class_id,
            activity_id,
        )
        series = load_concord_publication_series_status(
            class_id,
            activity_id,
            workspace_root=root,
        )
    except (
        ConcordAcademicWorkRegistrationError,
        ConcordAcademicResultPublicationError,
    ):
        return _state(class_id, activity_id, "needs_inspection")

    # A structurally current withdrawn head is explicit Share state. Keep that
    # recovery/review fact distinct from the absence of publication history.
    if series.core_head_withdrawal is not None:
        return _state(class_id, activity_id, "withdrawn")

    revision_reason: RevisionReason = (
        "initial" if series.producer_head is None else "native_state_change"
    )
    try:
        preview = preview_academic_result_manifest(
            GenerateAcademicResultManifestRequest(
                class_id=class_id,
                activity_id=activity_id,
                expected_snapshot_revision=context.snapshot_revision,
                actor=_ATTENTION_ACTOR,
                revision_reason=revision_reason,
            ),
            workspace_root=root,
        )
    except ConcordManifestGenerationError:
        # Registration exists, so Share has begun; a state that cannot be
        # safely previewed requires inspection rather than a fabricated action.
        return _state(class_id, activity_id, "needs_inspection")

    if preview.disposition == "would_create":
        return _state(class_id, activity_id, "manifest_needed")

    head = series.core_head
    if head is None:
        return _state(class_id, activity_id, "publish_ready")
    if (
        preview.revision == head.record_set_revision
        and preview.sha256 == head.manifest_digest
    ):
        return _state(class_id, activity_id, "current")
    if preview.revision > head.record_set_revision:
        return _state(class_id, activity_id, "supersede_ready")
    return _state(class_id, activity_id, "needs_inspection")


__all__ = [
    "AcademicResultShareAttentionState",
    "AcademicResultShareAttentionStatus",
    "inspect_academic_result_share_attention_state",
]
