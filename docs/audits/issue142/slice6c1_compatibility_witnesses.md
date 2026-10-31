# Concord #142 — Slice 6C1: historical fixture reconciliation

Source: full-repository Windows pytest, 2026-10-28, 2,683 passed, 42 failed, 18 skipped, zero setup errors after short temp path.

## Exact narrow scope

- #134: two historical teacher-choice unit tests monkeypatched `work_ref` and
  `load_graph`. The accepted #142 production reader now delegates to the
  `_load_artifact_graph` helper. Retarget the mocks to that specific read-only
  projection boundary, retaining single-load and stale-snapshot assertions.
- #136: two historical missing-library assertions expected GroupPlan-specific
  error text. Update only that string expectation to the revised accurate Core
  Standards Library message. No authorizing logic changes.
- #142 Slice 0: its six collected pre-repair/neutral/cancellation cases were
  run against post-repair code with no active-workspace root injected. The
  captured historical Slice 0 source-only ZIP remains unchanged; the current
  successor test now pins only the synthetic active Core root and checks
  actual forwarded authority / proposed Author mutation / no-write cancellation.

## Deliberately unresolved

- Frozen #140 Slice 3A source-derived equality is *expected to drift* as
  production call sites change, and must not be re-generated over frozen data.
  Do not edit original #140 CSVs, inventory, test or source ZIP. Preserve a
  separate exact historical-baseline qualification/disposition in #162.
- Historical menu-only mock tests for #28/#29/#106/#107/#108 (31 cases) still
  require contract-scoped reconciliation. Do not relax production guards or
  convert any pass into a claim of real student-work acceptance.

No production source changes, teacher data reads, repository staging,
committing or pushing are authorized in this slice.
