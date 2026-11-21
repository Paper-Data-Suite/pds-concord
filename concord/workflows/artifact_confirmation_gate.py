"""Canonical routed-return eligibility for explicit Artifact confirmation.

A graph-only predicate over one validated Activity snapshot. It does not
read/modify Core custody or assert that a PDF is assembled, opened or scored.
"""

from __future__ import annotations

from concord.model_validation import ConcordRecordGraph
from concord.models import ArtifactInstance, ArtifactPage
from concord.workflows.errors import ConcordWorkflowConflictError


def return_evidence_confirmable(
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
) -> bool:
    """Require all return-expected pages to have routed Scan References.

    A genuine non-return Artifact is independent of physical scan handling.
    Generated pages, page status, intended authors, and assembly directory
    names are not evidence of a routed physical return.
    """
    pages = {page.artifact_page_id: page for page in graph.artifact_pages}
    required: dict[str, ArtifactPage] = {}
    for page_id in artifact.page_ids:
        page = pages.get(page_id)
        if page is None or page.artifact_instance_id != artifact.artifact_instance_id:
            raise ConcordWorkflowConflictError(
                "Artifact page identity changed. Refresh current Activity evidence."
            )
        if page.return_expected:
            required[page_id] = page

    if artifact.expected_return_status == "return_not_expected":
        return not required
    if not required:
        # Optional/expected physical-return status is not a non-return claim.
        return False

    routed: set[str] = set()
    for scan in graph.scan_references:
        page = required.get(scan.artifact_page_id)
        if page is None:
            continue
        if (
            scan.activity_id != artifact.activity_id
            or not page.route_id
            or scan.route_id != page.route_id
        ):
            raise ConcordWorkflowConflictError(
                "Returned-page route identity is inconsistent. Review Scan Routing."
            )
        routed.add(page.artifact_page_id)
    return len(routed) == len(required)


def require_confirmable_return(
    artifact: ArtifactInstance,
    graph: ConcordRecordGraph,
) -> None:
    """Fail closed before any confirmed Author/Subject is committed."""
    if not return_evidence_confirmable(artifact, graph):
        raise ConcordWorkflowConflictError(
            "Required paper returns have not all been routed for this Artifact. "
            "Confirm attribution only after routed returned evidence is available."
        )


__all__ = ["return_evidence_confirmable", "require_confirmable_return"]
