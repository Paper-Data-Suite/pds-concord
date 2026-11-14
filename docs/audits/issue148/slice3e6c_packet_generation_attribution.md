# Concord #148 — Slice 3E6C Packet generation / render attribution

Starting branch: `148-persistent-reviewable-teacher-attribution`
Starting commit: `24a31bc5f5cdf9ed56f5231799f859a9fc246971`

## Scope

This slice changes only `concord/menu_packet_generation.py` and adds a synthetic regression module. Three canonical operations adopt the action-scoped teacher actor review:

1. Generate a Packet: collect conditional component choices and explicit rendering/subject bindings once, then reprepare the exact Packet instantiation for each reviewed actor. The final committed prepared object and immediate render both forward the actor from the approved preparation. The source preview, count checks, review digest, and ready-for-commit gate are preserved.
2. Render/reprint a complete Packet generation: retain existing eligibility and CAS snapshot checks; forward the reviewed actor in `RenderPacketGenerationRequest`.
3. Render/reprint one Packet Instance: retain existing target/status review; forward the reviewed actor in `RenderPacketInstanceRequest`.

Read-only views and the route-recovery helper remain separate; no new actor identity authority, scoring inference, route allocation, direct-CLI default, student lookup, or Notes ownership is added. A temporary actor choice never changes the saved teacher default.

## Safety and test coverage

New synthetic tests verify approved/default/alternate/canceled preparation, consistent actor in generation commit and immediate render, generation-reprint snapshot forwarding, single-Instance rendering, and AST-level callsite wiring. Existing Packet generation, rendering, instantiation, actor review, and menu tests are included in the focused acceptance list. All real classroom data, saved teacher profiles, and OS workspaces are excluded from the tests.

## Remaining #148 dispositions

This change is not the final callsite census or full suite gate. Still review and disposition `menu_group_plan_bulk` delegated commit, `menu_grouping_signal` CSV import, `menu_scan` routing, Core registration/publication calls without a native `WorkflowActor`, and miscellaneous action-less actor-resolution helpers. Run the complete source-wide census and authoritative full-repo/installed-wheel qualification only after those dispositions are closed.

Qualification status: local syntax and source transformation only; Windows Ruff/mypy/Core/pytest, commit/push and CI evidence are pending until the guarded runner succeeds.
