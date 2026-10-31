# Concord #142 — Slice 5B1: First Routine Score Boundary

## Scope

Preserve the exact Core workspace identity and conditional canonical Standards Library
across the first routine Score path in `concord/menu_artifact_scoring.py`. The
predecessor is the fully verified Slice 5A4 worktree (136 regression tests,
Ruff, whitespace and mypy green). This slice changes no Score-recording
service, Criterion/Scale selection rule, moderation validation, Score schema,
Review semantics or Core persistence.

## Behavior

1. Bind the selected Activity to one canonical Core workspace before reading
   routine Score eligibility.
2. Inspect the exact Artifact against that root and verify snapshot revision,
   SHA-256 and Artifact identity before displaying any Score choices.
3. Keep target, Criterion, Scale value, Session, and Subject selection explicit.
4. Refuse an existing current Score for the same routine target/Criterion.
5. After the teacher confirms the exact preview, refuse mismatched Artifact,
   revision or SHA, then revalidate workspace and current Standards authority.
6. Call the existing native `record_prepared_routine_score` once with the
   revalidated `workspace_root` and conditional `standards_library`. Core and
   Concord's native service retain semantic validation and snapshot CAS.

## Test evidence and limits

The synthetic workspaces include four scoring orientations. A prepared,
**unreturned** Artifact is confirmed ineligible for routine Score. To verify
the positive argument-forwarding boundary without falsifying returned-work
readiness, selected tests replace eligibility with a synthetic spy and intercept
the final Score service: **no real Score or evidence link is written**. Tests
also cover cancellation, duplicate preview, mismatched Artifact and workspace
drift. Full positive persistence with genuinely returned, assembled and
reviewed synthetic evidence is deferred to qualification.

## Next slice

Slice 5B2 pins post-Score continuation reads and Score-another-Criterion to
the new post-commit snapshot and workspace, and preserves the explicit fresh
Criterion/Scale selection requirement. It is deliberately not bundled with
5B1 so that the first Score authority can be verified independently.

No staged changes, commits, pushes, OneDrive access or real classroom data.
