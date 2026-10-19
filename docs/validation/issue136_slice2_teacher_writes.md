# Concord #136 — Slice 2: Teacher-menu Standards context propagation

**Base:** `3a606ed93ae6ecc5b21371ad45f90dcb3068a1a4` (Slice 1).
**Release target:** v0.3.4; version remains v0.3.3 during development.

## Verified failure class and fix

Slice 1 reproduced the live `mixed` Activity manual GroupPlan failure and repaired that entry point. Inspection of the other teacher menus showed the same boundary omission in service calls that accept `standards_library`. On standards-backed Activities, `storage._validate_loaded_graph_standards` correctly refuses the write when this is absent. Slice 2 does not change the storage validator or workflow models.

This slice adds canonical library propagation to all remaining GroupPlan creation/edit/lifecycle services (random, imported CSV, signals, missing-signal decisions, preview/approve/cancel), the approved-plan **prepare and apply** pair, direct Group/Membership create/update/end/reassign, Session create/update, and Role/Responsibility create/end/reassign and existing reusable-preset prepare/save/application paths.

The shared context uses the same Core workspace standards loader introduced in Slice 1. `standards_kwargs_for_activity` uses the known scoring orientation; `standards_kwargs_for_plan` uses the live persisted Activity summary because a GroupPlan detail does not carry its Activity's scoring orientation. Neither function constructs a new Standards Library, caches identities, changes the storage validation rules, or mutates Concord state.

`StandardsWriteKwargs` is a typed optional keyword-only expansion: standards-backed modes supply the exact library; purely evidence/local-criteria modes pass no additional keyword and do not need a canonical library. The actual write service always retains final responsibility for validating the complete graph and Focus Standard identities. A missing library for standards-backed Activities fails before a menu write with the actionable Slice 1 diagnostic.

For two-phase preview/commit actions (approved-plan apply, Role/Responsibility preset application and extracting saved presets), the same resolved library is reused across both service calls. Exact snapshot, review digest, actor, roster and canonical write guard semantics are unchanged. A teacher declining confirmation still does not write.

## Focused service boundary audit

| Teacher surface | Scope in Slice 2 | Context behavior |
| --- | --- | --- |
| Manual GroupPlan | Slice 1 | Preserved |
| Random and CSV-import GroupPlans | Creation | Canonical context forwarded after confirmation |
| Similar/mixed signal GroupPlans | Creation | Canonical context forwarded to write, unchanged signal preview |
| Missing-signal resolution | Disposition mutation | Context forwarded; read-only inspection remains neutral |
| Plan edit/roster/arrangement | Group add/edit/remove, place/unassign, refresh/replace | Context from live Activity, no alternate roster identity |
| Plan lifecycle | Preview, approve, cancel | Canonical context; no hidden apply |
| Approved-plan apply | Prepare and apply | One context resolution reused for exact preview and guarded commit |
| Direct Group/Membership | Create, update, add, end, reassign | Canonical Activity context |
| Session | Add, update | Canonical Activity context |
| Role and Responsibility | Assign, end, reassign | Canonical Activity context |
| Role and Responsibility presets | Prepare/save, prepare/apply | One context resolution per two-phase action |
| Listing/showing, neutral reads | Intentionally unchanged | No global Standards load imposed |

## Regression and operational boundaries

- AST-level per-service boundary checks guard 37 exact teacher-menu calls against context omission, in addition to synthetic teacher-menu dispatch tests for random GroupPlan, direct Group, Session, and plan preview with exact actor/snapshot assertions.
- Both `mixed` and `standards_based` require one canonical library; evidence-only and local-criteria-only modes avoid Standards loads. A missing required library fails before service invocation.
- Historical mock menu tests are updated only to supply a neutral context for synthetic GroupPlan details that intentionally lack persisted Activities.
- No GroupPlan model, Group state, Scores, academic-result producer/reader contract, PDS2 route, Core workspace schema, or class-specific saved arrangements are altered in this slice.
- This is not the full issue-level acceptance. Saved six-group class arrangements, persistence/revision semantics, cross-Activity reuse, teacher menu integration, and integrated scoring/publication qualification follow in later slices. Wider artifact/material/scoring/Share audits remain open; do not treat this focused matrix as a proof they are all clean.
- The runner uses Ruff, strict mypy, targeted teacher-menu tests, pip check, and Git whitespace/diff gates before committing and pushing this exact slice. The full suite is reserved for the final release candidate.
