# Concord #151 — Slice 5A: Review continuation and recovery guidance

**Baseline:** `77782d68e759cb7a8203b449de93b10650871709` on
`151-authoritative-collect-returned-evidence`.

## Teacher journey

- Ordinary **Collect** now presents `N. Continue to Review (no automatic Review)`.
- The handoff invokes the existing `launch_review_work_menu` with the refreshed,
  exact current Class/Activity and the caller's `MenuSessionContext`. It creates
  no pending durable wizard, bridge record, or academic write.
- Child `B` returns to Collect. `M` and `Q` remain Core-owned navigation
  signals and propagate to their existing owner. No movement is inferred from
  a screen visit or successful PDF viewer request.
- The previous `R` scan handoff and `S` read-only collection status remain
  independent and usable following a return from Review.

## Pending attribution recovery

- Where the authoritative attribution projection reports
  `exception_code="return_evidence_pending"`, both Author and Subject rows
  explicitly tell the teacher to return to Collect, route or resolve scans
  using `R`, then refresh stage via `S` before attempting confirmation.
- Disputed, invalid, and historical relationships retain separate meanings;
  they are not presented as missing paper solely because they are exceptions.
- The help text explains that both semantic validity **and complete canonical
  routed return evidence** are required. Proposals can remain pending.
- This slice does not change the Slice 4A confirmation gate, Core retention,
  assembled PDF identity, review and score writers, or file-open service.

## Recovery semantics and negative assertions

- `N` performs an exact Activity refresh and rejects any cross-Activity or
  cross-Class result before entering Review.
- A canceled or failed child menu does not establish a Review or Score.
  Independent durable operations remain recoverable through their original
  menus; the parent reopens current read models on the next action.
- Collection status continues to distinguish print/distribution as not tracked.
- Test fixtures are entirely synthetic and run without a physical scanner.

## Qualification (native runner)

- Native branch/remote/SHA guardrails, read-only preflight, unique anchors,
  exact changed-file scope, Ruff, Mypy, documentation, and focused pytest.
- No PR merge, tag, release, package-version increase, or physical-classroom
  acceptance is performed.
- **Not equivalent to physical acceptance:** actual returned paper, printer
  output, scanner retention, and native Windows deep-path PDF opening require
  separate Slice 6 qualification.
