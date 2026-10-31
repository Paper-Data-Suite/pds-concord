# Concord #142 — Slice 4C: Historical Review and Moderation witness reconciliation

Scope: `tests/test_issue140_slice3b_menu_guard.py`, `tests/test_issue140_slice3d_review_score_boundaries.py`, and this additive #142 audit handoff. **No production source, frozen #140 audit records, or real classroom data.**

## Failure analysis following accepted Slice 4B

- Historical #140 Slice 3B Review's fabricated Artifact lacked `snapshot_revision`, now required by `_record_review_selected` before detailed review. Add the actual selected Activity's snapshot revision to the synthetic menu Artifact; do **not** bypass the guard.
- Review and Moderation first-write paths now carry the canonical Core Standards library. Both should reach the intentionally missing Artifact target and fail with `Artifact is not available`, not the old missing-Standards failure.
- Historical #140 Slice 3D successor adapter incorrectly required a `standards_library` keyword for neutral `evidence_only` Activities, while the repair correctly forwards no library when standards are not required. Give the adapter a `None` default; keep explicit root verification and service forwarding unchanged.

The first-Review and first-Moderation synthetic positive tests from Slice 4A, successor/correction tests from Slice 4B, prior #142 attribution tests, and frozen #140 audit data are preserved. These changes do not assert returned evidence or scoring-ready results. Teacher Review/Moderation must remain explicit human judgment.

## Acceptance gates

Dry-run guarded preflight followed by apply; 28 historical tests, 32 Slice 4A/4B tests, 67 prior accepted attribution/identity tests, Ruff, project-wide mypy. Do not stage or commit until all checks pass. If the user checkout differs at any exact hash or structural boundary, refuse rather than guessing or coercing state.
