"""Core v1 adapter for Concord's native teacher-attention projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from pds_core.module_operations import (
    ModuleAttentionReport,
    ModuleAttentionSummary,
    ModuleOperationsNotice,
    ModuleOperationsRequest,
    ModuleOwnerActionRef,
    validate_module_attention_report,
)
from pds_core.routing_models import ModuleWorkRef
from pds_core.workspace import WorkspaceRootError

from concord.pds_contract import CONCORD_MODULE_ID
from concord.storage import list_activity_work_refs
from concord.storage_errors import ConcordStorageError
from concord.workflows.activity_attention import (
    ActivityAttentionItem,
    ActivityAttentionSummary,
    inspect_activity_attention,
)
from concord.workflows.context import (
    list_available_classes,
    resolve_read_workspace_root,
)
from concord.workflows.errors import ConcordWorkflowError

_PARTIAL_NOTICE_CODE: Final = "concord_attention_partial"
_UNAVAILABLE_NOTICE_CODE: Final = "concord_attention_unavailable"

# Stable aggregation order mirrors the native Plan -> Prepare -> Collect ->
# Review -> Score -> Share navigation convention. It is not urgency or priority.
_ATTENTION_CODE_ORDER: Final[tuple[str, ...]] = (
    "concord_plan_prepare",
    "concord_plan_unresolved_placements",
    "concord_plan_approve",
    "concord_plan_apply",
    "concord_prepare_materials",
    "concord_prepare_routes_pending",
    "concord_prepare_recovery",
    "concord_collect_assembly",
    "concord_collect_author_confirmation",
    "concord_collect_subject_confirmation",
    "concord_review_first",
    "concord_review_attention",
    "concord_review_moderation",
    "concord_review_post_moderation",
    "concord_score_ready",
    "concord_share_inspect",
    "concord_share_withdrawn",
    "concord_share_manifest",
    "concord_share_publish",
    "concord_share_supersede",
)
_ATTENTION_CODE_SET: Final = frozenset(_ATTENTION_CODE_ORDER)

_EXPECTED_SCOPE_ERRORS: Final = (
    ConcordStorageError,
    ConcordWorkflowError,
    WorkspaceRootError,
    OSError,
)


@dataclass(slots=True)
class _Aggregate:
    label: str
    action_id: str
    count: int = 0
    class_ids: set[str] = field(default_factory=set)
    work_refs: set[ModuleWorkRef] = field(default_factory=set)

    def add(
        self,
        item: ActivityAttentionItem,
        summary: ActivityAttentionSummary,
    ) -> None:
        if item.label != self.label or item.action_id != self.action_id:
            raise RuntimeError(
                "Concord attention code changed label or action identity during "
                "one evaluation."
            )
        self.count += item.count
        self.class_ids.add(summary.class_id)
        self.work_refs.add(
            ModuleWorkRef(
                module_id=CONCORD_MODULE_ID,
                class_id=summary.class_id,
                work_id=summary.activity_id,
            )
        )


class _AttentionAccumulator:
    def __init__(self) -> None:
        self._aggregates: dict[str, _Aggregate] = {}

    def add_summary(self, summary: ActivityAttentionSummary) -> None:
        for item in summary.items:
            if item.code not in _ATTENTION_CODE_SET:
                raise RuntimeError(
                    f"Unknown Concord native attention code: {item.code}"
                )
            aggregate = self._aggregates.get(item.code)
            if aggregate is None:
                aggregate = _Aggregate(
                    label=item.label,
                    action_id=item.action_id,
                )
                self._aggregates[item.code] = aggregate
            aggregate.add(item, summary)

    def summaries(
        self,
        request: ModuleOperationsRequest,
    ) -> tuple[ModuleAttentionSummary, ...]:
        result: list[ModuleAttentionSummary] = []
        for code in _ATTENTION_CODE_ORDER:
            aggregate = self._aggregates.get(code)
            if aggregate is None or aggregate.count <= 0:
                continue
            class_id, work_ref = _summary_context(aggregate, request)
            result.append(
                ModuleAttentionSummary(
                    code=code,
                    label=aggregate.label,
                    count=aggregate.count,
                    class_id=class_id,
                    work_ref=work_ref,
                    action=ModuleOwnerActionRef(
                        module_id=CONCORD_MODULE_ID,
                        action_id=aggregate.action_id,
                    ),
                )
            )
        return tuple(result)


def evaluate_concord_attention(
    request: ModuleOperationsRequest,
    /,
) -> ModuleAttentionReport:
    """Evaluate current Concord attention without creating or mutating state."""
    if not isinstance(request, ModuleOperationsRequest):
        raise TypeError("request must be a ModuleOperationsRequest.")

    if request.workspace_root is None:
        return _unavailable_report(
            "Concord attention requires an explicit workspace."
        )

    try:
        root = resolve_read_workspace_root(request.workspace_root)
    except (OSError, WorkspaceRootError):
        return _unavailable_report(
            "The supplied workspace cannot be inspected safely for Concord attention."
        )
    if root is None:
        return _unavailable_report(
            "The supplied workspace is not available for Concord attention."
        )

    work_refs, discovery_partial = _discover_work_refs(
        root,
        requested_class_id=request.class_id,
    )
    if work_refs is None:
        return _unavailable_report(
            "The requested Concord Activity scope cannot be inspected safely."
        )

    accumulator = _AttentionAccumulator()
    partial = discovery_partial
    for work_ref in work_refs:
        try:
            summary = inspect_activity_attention(
                work_ref.class_id,
                work_ref.work_id,
                workspace_root=root,
            )
        except _EXPECTED_SCOPE_ERRORS:
            partial = True
            continue
        accumulator.add_summary(summary)

    notices: tuple[ModuleOperationsNotice, ...] = ()
    if partial:
        notices = (
            ModuleOperationsNotice(
                code=_PARTIAL_NOTICE_CODE,
                summary=(
                    "Some Concord attention sources could not be inspected safely; "
                    "available summaries are partial."
                ),
            ),
        )

    report = ModuleAttentionReport(
        evaluation="evaluated",
        summaries=accumulator.summaries(request),
        notices=notices,
    )
    return validate_module_attention_report(
        report,
        expected_module_id=CONCORD_MODULE_ID,
    )


def _discover_work_refs(
    root: Path,
    *,
    requested_class_id: str | None,
) -> tuple[tuple[ModuleWorkRef, ...] | None, bool]:
    """Discover exact Concord work while isolating independent class failures."""
    if requested_class_id is not None:
        try:
            scoped_refs = list_activity_work_refs(root, requested_class_id)
        except _EXPECTED_SCOPE_ERRORS:
            return None, False
        return scoped_refs, False

    try:
        classes = list_available_classes(root)
    except _EXPECTED_SCOPE_ERRORS:
        return None, False

    discovered_refs: list[ModuleWorkRef] = []
    partial = False
    for class_summary in classes:
        try:
            discovered_refs.extend(
                list_activity_work_refs(root, class_summary.class_id)
            )
        except _EXPECTED_SCOPE_ERRORS:
            partial = True
    return (
        tuple(
            sorted(
                discovered_refs,
                key=lambda item: (item.class_id, item.work_id),
            )
        ),
        partial,
    )


def _summary_context(
    aggregate: _Aggregate,
    request: ModuleOperationsRequest,
) -> tuple[str | None, ModuleWorkRef | None]:
    class_id: str | None = None
    if request.class_id is not None:
        class_id = request.class_id
    elif len(aggregate.class_ids) == 1:
        class_id = next(iter(aggregate.class_ids))

    work_ref: ModuleWorkRef | None = None
    if len(aggregate.work_refs) == 1:
        work_ref = next(iter(aggregate.work_refs))
        if class_id is None:
            class_id = work_ref.class_id

    return class_id, work_ref


def _unavailable_report(summary: str) -> ModuleAttentionReport:
    report = ModuleAttentionReport(
        evaluation="unavailable",
        summaries=(),
        notices=(
            ModuleOperationsNotice(
                code=_UNAVAILABLE_NOTICE_CODE,
                summary=summary,
            ),
        ),
    )
    return validate_module_attention_report(
        report,
        expected_module_id=CONCORD_MODULE_ID,
    )


__all__ = ["evaluate_concord_attention"]
