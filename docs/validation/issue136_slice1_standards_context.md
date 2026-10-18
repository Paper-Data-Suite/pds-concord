# Concord #136 — Slice 1: Standards-context diagnosis and first repair

**Baseline:** `6472215e43a740d195257ecbe6b099b2d0648df5` (published v0.3.3).
**Branch:** `136-fix-standards-context-and-reusable-group-arrangements`.
**Target:** v0.3.4; **no version change in Slice 1**.
**Reported reproduction:** existing `mixed` discussion Activity, one Core Focus Standard, first Session persisted; `Student groups → Create manual GroupPlan → CREATE` fails with `standards_library is required for this Activity.`

## Proven defect and contract

`menu_group_plan._create_manual` sent `CreateManualGroupPlanRequest` to `create_manual_group_plan` without `standards_library`. `workflows/group_plan_manual.py` forwards that optional keyword into the underlying `create_group_plan` service. `storage._validate_loaded_graph_standards` correctly makes it mandatory for Activities with `scoring_orientation` `mixed` or `standards_based`, or standard-backed Criteria/Scores. The default `None` therefore failed before a GroupPlan mutation.

The existing `menu_prompts.load_menu_standards_library()` loads the canonical Core workspace library (no new cache or alternate identity representation). `menu_standards_context.standards_for_activity()` is the shared context boundary: it loads once for modes known to require it; it returns `None` for purely evidence/local modes; if required configuration is absent it gives an actionable prewrite error. Service-level graph validation, revision conflicts, roster checks and canonical commits are **unchanged**.

Slice 1 threads this helper through **only the manual GroupPlan creation path**. The menu still requires literal confirmation and preserves the current snapshot revision and actor. A success banner is shown only after successful service return. No evidence/Score/Group/Membership write is introduced. The original Activity can be resumed; this slice neither migrates it nor attempts to recreate it.

## Audit matrix — remaining scope (not yet repaired)

| Entry point | Existing service contract | Status / Slice 2+ gate |
| --- | --- | --- |
| Manual GroupPlan creation | `create_manual_group_plan(... standards_library=...)` | **Confirmed omission, fixed in Slice 1**; menu-level cross-mode regression added |
| Random/CSV arrangement GroupPlan creation and proposal edits | `create_random_group_plan`, `import_arrangement_group_plan`, `add/edit/remove/place/unassign/refresh/replace` | Same-module source-level omissions; characterize with actual menu dispatch, then fix in Slice 2 |
| GroupPlan preview/approve/cancel, signal proposals and missing-signal decisions | GroupPlan lifecycle and signal services | Suspected omissions; distinguish read-only/standards-neutral from standards-validated writes |
| Apply approved plan | Prepare/apply exact write set | Suspected omission; prove exact snapshot and standards context requirements before correction |
| Direct Groups/Memberships | Group and membership services | Suspected omissions; test create/update/add/end/reassign in both standards-backed modes |
| Session, Role, Responsibility | Native state writers | Suspected omissions; verify preset-to-assignment and direct teacher paths |
| Artifact, scoring, Packet, Share/publication, Templates/presets | Mixed readers/writers | Audit for missing *required* standards/actor/roster/snapshot context; **do not** blanket-load Standards for intentionally neutral reads |
| Direct CLI | `load_command_standards_library` | Existing canonical reader and explicit override path; retain and add parity tests |

**Important follow-up:** A standards-backed Activity can also contain standard-backed Criteria/Scores; mode alone is a cheap known-required preflight for this single action, not a replacement for the service's complete graph validation. Subsequent slices must verify other write paths in all four orientations and avoid per-student or per-row reloading of Core Standards.

## Slice 1 acceptance

- Focused teacher-menu tests check `mixed`, `standards_based`, `evidence_only`, `local_criteria_only`, **exact keyword forwarding**, one canonical read, original actor/snapshot, actionable missing-library failure before the service call, and cancellation without any write.
- Historical manual-menu test is updated only to permit the added keyword. Existing GroupPlan model and storage tests remain unchanged.
- No class arrangement persistence, new Group IDs, score propagation, or published version bump in this slice. Reusable grouping contracts and implementation follow in Slices 3–4.
- Gate: targeted pytest, Ruff check/format, strict mypy on touched production modules, pip check, diff check; stage/commit/push only after passing all gates. Full suite runs once at v0.3.4 release candidate.
