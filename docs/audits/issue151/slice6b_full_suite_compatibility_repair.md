# Concord #151 — Slice 6B: full-suite compatibility repair

## Evidence and baseline

Slice 6A's full Windows repository validation at feature commit
`a7aaa0692a507f8dc7b274a38b1c676092bf1d93` reported
**3,745 passed, 10 failed, 19 skipped**. The full pytest phase was
1,019.53 seconds; it stopped before Twine/installed-wheel smoke checks and
before the synthetic Windows viewer-dispatch probe.

## Scope — historical synthetic tests and current inventory only

- Issue #28 CLI scenarios testing Author/Subject mutation mechanics now declare
  a genuine **non-return** Artifact and non-return-expected page where the
  test never provides routed scans. The existing physical-return/assembly CLI
  test keeps the default return-expected fixture and checks actual routing.
- Issue #29 cross-case synthetic tests for independently confirmed observer,
  recorder, teacher tracker, and correction semantics use an explicit
  non-return fixture. The **incomplete returned-paper review** case remains
  return-expected and does not bypass any evidence requirement.
- Issue #28 occurrence-selection menu test stubs **only** the already separately
  tested Slice 3A read-only preflight. It still checks exact selected scan ID.
- Issue #113 mixed-response generated packet adds the reviewee as a
  **proposed** co-author before physical return; asserts both Author identities persist.
- Refresh #142's **current** 18-row source-boundary inventory to match the
  exact current AST callsites. The frozen #140 inventory and its hash remain
  unchanged; the inventory still marks all entries BLOCKED_OR_UNTESTED.

## Nonnegotiable safety boundaries

No production code changes. In particular, `artifact_confirmation_gate.py`,
its Author/Subject writer guards, required routed page coverage, and the
independent batch-writer check must remain unchanged. Do **not** rewrite
historical tests into passing xfails or opt out of the #151 gates.

## Qualification

Run focused tests across the four changed historical suites, the #140 census,
the #151 regressions (including former strict xfails), Ruff, formatting, Mypy,
`check_documentation.py`, and check staged file scope. Only commit and push after
all gates are green. Do not repeat the 17-minute full suite during this repair.

Then re-run Slice 6A full repository/wheel qualification exactly once.
The full-suite, isolated wheel, GitHub PR CI, native PDF display, and physical
scanner acceptance remain **pending until separately evidenced**.
