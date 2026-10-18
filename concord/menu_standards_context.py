"""Canonical Core Standards context for standards-backed teacher-menu writes.

The menu and workflow services resolve the same Core workspace. This module
only provides the context requested by a particular operation; it does not
change storage validation, cache Standards, or create a missing library.
"""

from __future__ import annotations

from pds_core.standards import StandardsLibrary

from concord.menu_prompts import load_menu_standards_library
from concord.workflows import ActivitySummary, ConcordWorkflowValidationError


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
