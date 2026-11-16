# Concord #148 — Slice 3B2: missing-signal and actor-bound bulk review

**Pinned baseline:** `587a5d94a2de202585c98bb6a6254ea68f9a975f` (qualified 3B1). **Dependency:** officially installed Core 0.6.6. No Core, Suite or Meridian source changes.

## Teacher-facing contract

The three missing-signal decisions (confirm manual, distribute randomly, leave unassigned) now use the same `confirm_actor_write` mechanism as other reviewed GroupPlan writes. A temporary adult actor is confirmed once for the exact disposition; `B`, cancellation and stale-profile errors perform no write. Existing explicit legacy sessions retain their `confirm_write` callback.

Bulk placement uses its established multistep review (`SAVE BATCH`, pages N/P, Back retaining selection) rather than introducing a second generic confirmation. An advanced `A` selection of a temporary alternate actor, or `D` to restore the saved default, recomputes the read-only `prepare_bulk_planned_group_edit` request and digest **before** showing the confirmation again. The teacher sees the exact actor ID, updated digest and student effects on the same review screen. The final immutable commit uses the identical returned request and digest. `A`/`D` never saves the local profile or queues an actor for a future operation.

## Critical digest boundary

The existing #147 service incorporates `repr(request.actor)` into `_bulk_review_digest`; swapping actor **only at commit** would fail replay protection or attribute a decision without matching the reviewed digest. Therefore a replacement `BulkPlannedGroupEditRequest` is prepared before the final `SAVE BATCH` and the review page is redrawn. Profile fingerprint is revalidated at final confirmation; any mutation of the saved default aborts. `B` discards the current review-local alternate and returns to student selection without saving. Existing review page order and canonical proposal-only effects remain unchanged. No actor or student data is copied to Core Notes ownership.

## Scope and qualification

Only `concord/menu_group_plan_bulk.py` and `concord/menu_group_plan_missing_signal.py` change in production. Add one synthetic regression module with actor/digest binding, restore, cancellation, concurrent profile change, three missing-signal actor handoffs, and zero-write refusals; retain the #147 six-Cluster real-menu tests. Repo-wide audit of Activity, Artifacts, Scoring, Presets and Publication remains outstanding and must not be declared complete by this slice.
