# Issue #148 — Slice 3E5A: class grouping save/reuse actor review

Pinned baseline: `39caf7f54f838c2744a05a08b4fdd7c129bb3e5d`.

## Scope

Two teacher-facing, digest-backed actions in `concord/menu_saved_groupings.py`:

1. Save an editable GroupPlan as a class-scoped reusable grouping.
2. Reuse an existing saved grouping to create a fresh Activity-owned draft GroupPlan.

Both now invoke `confirm_prepared_actor_write` with a callback that constructs
an exact-actor canonical request, prepares its digest, displays its placement
preview, and returns the request/preview pair for commitment after confirmation.
The current default teacher identity is not rewritten. Cancellation commits
nothing. Source snapshot, placement decisions, departure acknowledgments,
existing Activity-plan acknowledgment, and Standards forwarding are retained.

## Deliberately excluded

`_saved` and related ownership-scoped reads, nonwriting acknowledgments,
operational Group/Membership capture, and saved-grouping rename/replace/retire
remain as separate audited surfaces. A temporary attribution override is not
an authorization mechanism; canonical service ownership controls still apply.

## Qualification

The guarded runner authenticates the source ZIP and Git blobs, performs Ruff
and mypy temporary-source preflight, runs installed Core verification and
focused previous/new pytest regressions, and commits/pushes only after success.
No actual teacher data are embedded or used in synthetic tests.
