# Concord #149 — Slice 1 applied GroupPlan evidence and alternative drafts

## Starting evidence

- Source-pinned parent commit: `e9eead5e990daee9a90421557bfdbeb9c7426665`.
- Slice 0 confirmed (84 passing, 3 strict XFAIL, 1 platform skip); `--runxfail` reproduced exactly 2 plan and 1 unreturned Artifact defect. No production code was changed in Slice 0.
- This slice repairs **only** the two applied-plan witnesses. The unreturned Artifact strict XFAIL remains intentionally pending for Slice 2.

## Decision: current operational evidence must be verifiable

A historical `GroupPlan.status == "applied"` alone cannot prove current operational grouping, especially after Core roster changes, membership edits or new applications. The candidate is treated as current only when:

1. Exactly one applied plan is in the verified Activity graph; its `applied_application_id` and planned group roster are present.
2. Every derived canonical Group ID (from `derive_group_id`) exists in the graph in the planned/active state.
3. Every derived canonical Membership ID (from `derive_membership_id`) still exists, is active, and refers to the exact Core student. No unexpected active Membership exists in those Groups or another operational Group in the Activity.
4. A **read-only** current Core class-roster load matches the applied plan's roster snapshot. If Core cannot be read, error propagates to the existing partial/unavailable attention handling; no implicit "ready" state is asserted.

If that proof holds, any other draft/previewed/approved plan is an **alternative proposal**, not a blocking task. The GroupPlan management menu still exposes it for optional inspection and explicit cancellation; historical and actor-attributed records remain intact. If proof fails, existing attention is preserved conservatively until Slice 3 provides explicit needs-inspection UI; no fake clean state is manufactured.

Do **not** infer student performance, printing, return, or re-publication from this proof. The previous #67 summary-only helper has no canonical group linkage or current Core roster, so cannot certify operational readiness; its existing behavior remains unchanged. The optimized current-graph projection is the real owner of this new judgment.

## Cancellation boundary

`concord/menu_group_plan.py::_cancel` already prompts for actor-reviewed `CANCEL` and calls canonical `cancel_group_plan(CancelGroupPlanRequest(... expected_snapshot_revision=..., actor=...))`, which restricts cancellation to draft, previewed or approved plans; terminal cancellation preserves history. No changes to service, authorization semantics, actor, Core roster, or write model in this slice. Existing native GroupPlan cancellation/validation tests and a source-boundary check qualify the reused operation. Optional cleanup discoverability in the new readiness view belongs to Slice 3.

## Qualification

- Tests that were strict-XFAIL for 29/30-student applied-grouping now use **real deterministic derived ID formats** and a mocked current Core roster; markers are deliberately retired and must pass. The unrelated 6-blank-Artifact witness remains XFAIL and must still fail when replayed with `--runxfail`.
- Added stale-membership, cancelled-group, extra applied-plan, changed Core roster, unavailable roster and cancellation ownership regression tests.
- No full-repository validator in this incremental slice; execute focused #149/#67/#104 and GroupPlan application/cancellation suite, Ruff, mypy; full validator at Slice 4 with official Core 0.6.6.
- No release, Core/Suite change, real student record or physical-paper claim.
