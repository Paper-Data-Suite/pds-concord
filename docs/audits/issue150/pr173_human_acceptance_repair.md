# Concord #150 — PR #173 human-acceptance repair

**Base:** `47489cd21a4601d01a78e98c99dc5f5bc9e8e7e0`; official Core `0.6.6`.
**Status:** Source candidate, Windows focused qualification and refreshed PR CI **pending**. No merge, tag, release or schema change.

## Three observed findings and bounded repairs

1. **No configured teacher attribution on saved assessment setup (inherited P1):** The existing saved-Criterion Set path constructed a `MaterializeScoringSetupRequest` by calling `state.require_actor()` before the actor-aware review. The request is now built *only inside* the `confirm_prepared_actor_write` callback, after a reviewed actor exists. The same generated identities, exact preset revisions, current Activity snapshot, digest and `materialize_scoring_setup` owned writer remain. An unconfigured, provider-backed menu must explicitly choose a one-action alternate (A) and then type USE; cancel, missing/stale/corrupt profile, no actor or changed snapshot cannot write.
2. **Global M/Q navigation swallowed during resume (inherited P2):** `launch_guided_continue_setup`, the create guide and the target assessment owner-menu boundary now let Core `ReturnToMainMenu` / `QuitPDS` reach `concord.menu.launch_menu`. Ordinary bounded failures still report in context. `B` remains local. No global input interception or navigation framework added.
3. **Specialized target steps lost after reopen (#150 P2):** Resumed `Continue Classroom Setup` displays two non-numbered optional shortcuts: `C. Review or plan six target Clusters` and `R. Use saved rubric / target assessment setup`. These use the **same target-only preflight and owned writer** as the verified post-copy screens; normal numbered Session/GroupPlan/Materials/Assessment routes are unchanged. Core source/target identity, roster/snapshot checks, Score isolation, readback and partial-status receipts remain. Because copy provenance is deliberately *not* persisted, these target-class-safe shortcuts are available for any resumed Activity; they never infer its source or recopy it.

## Test gates

New synthetic menu regressions explicitly cover C/R visibility/dispatch without recopy or unreviewed writes, M/Q from an actual reentered guide, M/Q leaving the underlying assessment menu, an absent default choosing A for a temporary adult and typing USE, no-write cancel without attribution, and actor-dependent exact request reprepare. Existing #148 actor, #149 attention, #150 Slices 0–5 and #63/#65/packet regression families should remain green. The Windows runner must check pinned Git and source scope, official Core 0.6.6, Ruff, strict mypy and docs, the focused regression matrix, and only then commit/push.

**Not claimed:** Packet generation (Antigravity fixture missing), physical printing/scanning, human acceptance of the repaired build or refreshed PR CI. Run a targeted Antigravity retest with a seeded synthetic Packet/Template after the repair qualifies.
