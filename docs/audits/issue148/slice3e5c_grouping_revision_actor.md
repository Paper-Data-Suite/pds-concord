# Concord #148 — Slice 3E5C: Saved grouping revision attribution

Starting branch: `148-persistent-reviewable-teacher-attribution`
Pinned base: `3a88bda9073dae3847c90a6111d523e63eceb89f`

## Scope

Three existing class-scoped saved-grouping revision actions (`rename`,
`replace_from_plan`, and `retire`) use `confirm_prepared_actor_write` rather
than creating one request/digest for the saved default and subsequently showing
an actor-independent confirmation. An actor selection now re-runs
`prepare_grouping_change` for exactly the actor under substantive review. The
review returns a pair `(ChangeGroupingRequest, review_digest)` and only this
paired result is passed to `change_grouping` after confirmation.

Ownership is **not** bypassed or retargeted: the canonical preparation already
loads the grouping under `request.actor.actor_id` and rejects a mismatched
owner. An alternate actor without access therefore fails before any write.
The existing immutable-history, exact revision/SHA checks, source GroupPlan
snapshot/roster checks, validation, and copy-on-write service remain unchanged.

The GroupPlan-placement display on `replace_from_plan` stays inside the actor's
review callback. A switch to an alternate actor re-renders the placements
before that actor's write can be confirmed. Cancellation returns `False`
and does not call the writer. No changes to the read-only saved-grouping
browser or history view, other services, Core, storage contracts, or UI menu
numbers.

## Files

- Production: `concord/menu_saved_grouping_revisions.py`
- New tests: `tests/test_issue148_slice3e5c_grouping_revision_actor.py`
- This audit: `docs/audits/issue148/slice3e5c_grouping_revision_actor.md`

## Qualification

The paired source-only and runner-only archives enforce pinned Git blobs, clean
baseline and exact source-member checks; make an isolated Ruff/strict mypy
projection; run syntax checks, Ruff, installed Core verification, and focused
saved-grouping/actor regression suites; verify diff scope; then (on explicit
`--commit-and-push`) commit and push only following all green gates.

Tests use synthetic Actors, Activities, GroupPlan summaries, and revision
preparations. No teacher profile, student roster, or production workspace data
is accessed.
