# Concord #142 — Slice 5A: Quick Review menu authority

## Scope

Patch only the existing `_quick_review_selected` menu handler. This supports the
ordinary Quick Review option and the Review-next Quick Review path. The
Activity and selected Artifact must agree on the exact snapshot. The eligibility
inspection reads from the pinned Core workspace and must have matching
revision and snapshot SHA-256. Teacher confirmation is followed by the reusable
workspace/Standards revalidation; `record_routine_artifact_review` then receives
`workspace_root` and the canonical conditional `standards_library`.

The existing service remains authoritative for eligibility, first-Review-only
semantics, graph validation, and compare-and-swap publication. The menu does
not infer or record a Score, and there are no automatic retries.

## Evidence boundaries

Synthetic tests include an unreturned prepared observation. These demonstrate
that an ineligible Artifact cannot be passed to the routine Review writer, and
that cancellation and workspace drift do not write. A separate service spy
checks exact argument propagation with an explicitly synthetic eligibility
projection; it does **not** constitute positive acceptance of ready/assembled
returned student work. An end-to-end positive fixture for returned, assembled,
review-eligible synthetic work remains a qualification requirement in later
Slice 5 work. All synthetic Review simulations are explicitly labeled.

## Excluded from this slice

Routine Score recording, Score-another-Criterion continuation, next-score-ready
selection, Advanced Score, wider read-only menu ergonomics, immutable #140
audit dispositions, Core/Suite code, teacher data, staging, commits and pushes.
