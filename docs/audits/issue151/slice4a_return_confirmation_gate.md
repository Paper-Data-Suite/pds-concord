# Concord #151 — Slice 4A: authoritative return-gated confirmation

## Baseline

Feature branch `151-authoritative-collect-returned-evidence` at
`10f5ac5b38088b6ddff80ae438f178b4349f415b`.

## Scope

- A pure, validated-graph return-eligibility predicate shared by the routine
  attribution read projection and all Author/Subject semantic writer validators.
- An additional independent batch-writer gate *before* any `commit_record_batch`.
- Existing `proposed`, `disputed`, `unknown`, and historical relationships remain
  available for correction; the gate runs only when status becomes `confirmed`.
- An actual `return_not_expected` Artifact with no return-expected pages keeps
  the established #106 observation confirmation contract.
- A return-expected or return-optional Artifact requires canonical routed
  ScanReference coverage for **every** return-expected page. Partial, generated,
  distributed, or manually marked returned status is not enough.
- A route or Activity contradiction stops confirmation rather than inventing
  evidence. Repeated valid occurrences remain eligible, without selecting a
  preferred occurrence.
- Two formerly strict-xfail Slice 0 witnesses become ordinary required tests.

## Ownership and limits

The rule operates on the *already loaded* Concord Activity graph. Core remains
owner of scan retention and PDS2 dispatch. No second graph read is introduced in
the batch writer; #106 single-load/single-commit behavior remains required.

A canonical ScanReference is a routed-return claim validated by the graph;
this predicate does not independently open the retained source file or prove
its current hash. Existing assembly and viewer services retain those separate
checks. It neither assembles nor creates Reviews, Scores, or Grades.

This slice does not change existing historical confirmations. Fully integrated
Windows and physical-source acceptance remain part of #151 Slice 6.
