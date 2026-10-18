"""Canonical Core Standards context for standards-backed teacher-menu writes.

The menu and workflow services resolve the same Core workspace. This module
only provides the context requested by a particular operation; it does not
change storage validation, cache Standards, or create a missing library.
"""

from __future__ import annotations

from typing import TypedDict

from pds_core.standards import StandardsLibrary

from concord.menu_prompts import load_menu_standards_library
from concord.workflows import (
    ActivitySummary,
    ConcordWorkflowValidationError,
    GroupPlanDetail,
    show_activity,
)


def standards_for_activity(activity: ActivitySummary) -> StandardsLibrary | None:
    """Resolve one canonical library before a standards-backed menu write.

    Evidence-only and local-criteria-only Activities do not require a library.
    Every downstream service still enforces its own exact graph and snapshot
    validation; this is not an alternative validation path.
    """
    if activity.scoring_orientation not in {"standards_based", "mixed"}:
        return None
    library = load_menu_standards_library()
    if library is None:
        raise ConcordWorkflowValidationError(
            "This Activity uses Focus Standards, but the Core Standards "
            "Library is unavailable in the current Paper Data Suite "
            "workspace. Configure or restore the canonical Core Standards "
            "Library, then reopen this Activity and retry. No GroupPlan "
            "was created."
        )
    return library


class StandardsWriteKwargs(TypedDict, total=False):
    standards_library: StandardsLibrary


def standards_kwargs_for_activity(
    activity: ActivitySummary,
) -> StandardsWriteKwargs:
    """Forward required Standards context without burdening neutral Activities."""
    library = standards_for_activity(activity)
    return {"standards_library": library} if library is not None else {}


def standards_kwargs_for_plan(
    detail: GroupPlanDetail,
) -> StandardsWriteKwargs:
    """Resolve the live Activity before validating a plan mutation.

    GroupPlan details intentionally omit scoring orientation; never infer it
    from plan strategy, cached IDs, or a prior Activity. The Activity
    summary reader is standards-neutral; service writes remain strict.
    """
    summary = show_activity(detail.summary.class_id, detail.summary.activity_id).summary
    return standards_kwargs_for_activity(summary)
