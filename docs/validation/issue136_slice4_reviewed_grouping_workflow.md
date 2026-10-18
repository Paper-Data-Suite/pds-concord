# Concord #136 — Slice 4: reviewed class grouping workflow services

**Baseline:** `4dfcafddb02cae863816c952a7b04b08b409e14d` (Slice 3, branch `136-fix-standards-context-and-reusable-group-arrangements`).

**Scope:** Add a presentation-neutral service for saving a named grouping from a *current editable GroupPlan* and materializing a selected active saved grouping into a fresh *draft GroupPlan* belonging to another Activity for the exact same Core class and year. This is an application-service slice, not menu/CLI wiring or a release/version change.

## Save: explicit prepare, review, confirm

- `prepare_save_grouping` loads the exact Core class metadata, current Core roster, Activity snapshot and editable GroupPlan. It rejects stale snapshots, changed rosters, zero-group plans and unsuitable plan status; it previews the exact six-or-other planned group labels and membership choices, including unresolved students.
- `save_grouping` reruns the source validation, requires the matching SHA-256 review digest, then uses the Slice 3 `create_arrangement` create-only immutable library. Saved records carry exact Core student IDs, class/year, teacher owner, labels, descriptions, roster coverage, unresolved IDs and revision metadata. No Activity ID, Session ID, GroupPlan ID, canonical Group/Membership ID, Score, Role, Artifact or Publication is copied into the saved revision.
- The target library's storage remains separate from the source Activity graph. No source write or Activity mutation occurs on save.

## Reuse: explicit roster reconciliation and a single native Activity write

- `prepare_reuse_grouping` authenticates current owner and class/year, active revision/digest, target Activity revision, no existing canonical Groups and any existing GroupPlans. It refuses to silently override, merge or end a target Group or plan.
- New students and retained-but-unresolved students must each receive **one explicit placement decision**: one of the named groups, or `None` to deliberately remain unresolved in a new editable plan. Every departed ID must be **explicitly acknowledged**. Extra or duplicate decisions fail. No name-based reconciliation, guessing or silent omission.
- An Activity with prior plans requires `acknowledge_existing_plans=True`. The newly chosen `new_group_plan_id` must be unused; this is an additional plan, **not** a replacement. Already-created canonical Groups block the flow until a separately designed safe choice exists.
- `reuse_grouping` reruns the complete preview, checks the exact review digest, then delegates the only native Activity mutation to the existing `create_group_plan(CreateGroupPlanRequest(...))`, with exact target snapshot, roster precondition, actor, optional Standards Library, six-or-other proposed groups, and `strategy="manual"`. The GroupPlan remains editable and unapplied. Application continues through the established preview → approval → guarded apply boundary, which creates fresh operational IDs.
- A source save and a new Activity Graph commit occur in distinct stores; the service does not promise a cross-store transaction. Within reuse, the native Activity writer rechecks exact expected snapshot, canonical Core roster, and standards before writing. There is no background recovery, inferred retry or hidden merge.

## Qualifying synthetic scenarios

29 exact Core students in six groups; source vs target separation; save/no-write preview; tampered or stale review digest; stale Activity; 29-to-29 roster drift with an explicit departure acknowledgment and new-student placement; an explicitly unresolved student; existing target plans; teacher owner restriction; retired revision; standards keyword forwarding to native GroupPlan service.

**Not implemented in Slice 4:** teacher menu and CLI commands, save from existing operational Groups/Memberships (requires exact session/effective-context disambiguation), named revision/rename/retire teacher commands, optional CSV interchange, audit of other teacher surfaces, score/publication acceptance, or v0.3.4 release. These follow on the issue branch. The new service must not be advertised as a complete teacher feature until menu and direct CLI exposure exists.

**Gate:** one focused pytest run (Slice 3 + Slice 4 integration and minimal prior context regressions), Ruff, strict mypy, `pip check`, and staged whitespace; then stage exactly the three additive files and commit/push only on success. No full suite in this slice.
