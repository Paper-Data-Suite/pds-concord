# Concord #142 — Slice 5B2: Routine Score continuation authority

## Boundary repaired

`menu_artifact_scoring.py` originally restarted post-Score readers and subsequent
routine Score commits without the pinned Core workspace or conditional Core
Standards Library. The first Score succeeds against one verified snapshot, but
`reload_routine_scoring_after_score`, `inspect_next_score_ready_artifact`, and
`record_prepared_routine_score` for another Criterion must operate against the
*new* snapshot, not the predecessor snapshot and never a silently changed root.

## Changes

- Associate the exact first-Score `ArtifactWriteContext` with the successful
  internal `_RoutineScoreMenuResult`. A direct second-Score attempt with no
  original authority is rejected.
- Refresh subsequent authority by reading the Activity from the original root,
  verifying any active-workspace binding and reloading canonical Standards
  according to actual scoring orientation and graph.
- Require the refreshed snapshot to match the post-Score routine-scoring
  projection. On a new Criterion, revalidate again after teacher confirmation
  and pass the verified root and conditional Standards Library to the existing
  canonical Score service; do not change its schema or grading semantics.
- Pass the pinned root to post-Score continuation reload and next score-ready
  Artifact discovery. Preserve the `minimum_snapshot_revision` check.
- Preserve explicit Score target, Criterion, Scale, value, Session, evidence
  Subject context and duplicate-score refusal. Don't convert Review readiness
  into a Score or infer a new target.

## Synthetic qualification

`tests/test_issue142_slice5b2_score_continuation.py` uses disposable Core
classes and an Artifact prepared but never returned. A genuine administrative
Review with `not_ready` advances the synthetic Activity revision for snapshot-
transition tests; it is **not** a Score. Positive Score forwarding is tested
using a service spy and synthetic eligibility overrides, not a false claim of
successful scoring on unreturned work. The tests cover:

1. Fresh snapshot rebasing in standards and evidence-only orientations.
2. Active-workspace switch and stale projection rejection.
3. Canonical root and optional Standards forwarding in all four orientations.
4. Cancellation, duplicate Score refusal, stale preview refusal, absent authority.
5. Next score-ready navigation using the original root and fresh snapshot.

## Acceptance gates

The runner must preflight the precise accepted uncommitted Slice 5B1A
predecessor, complete source reconstruction, branch, HEAD, working tree scope,
manifest, and synthetic test files before writing. Run the focused Slice 5B2
tests, accepted Slice 5B1A (13), Slice 5A (9), historical #140 (28), earlier
#142 and #141 tests; run repository-wide Ruff, `git diff --check`, and mypy.

End-to-end real returned-assembly Score lifecycle remains for the subsequent
qualification stage; the source-only bundle creates no such fixture.

No student data, actual teacher workspace, commit, stage, push, or external
network action is performed by the runner.
