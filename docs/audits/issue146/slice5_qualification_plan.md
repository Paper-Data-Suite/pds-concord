# Concord #146 — Slice 5 consolidated qualification and teacher walkthrough

**Branch:** `146-teacher-first-status-choices-and-enum-audit`
**Prerequisite commit:** `82b238ee7486b8bff9d4899bf0ff0aa2a1c27114`
**Scope:** synthetic acceptance and qualification evidence only; **no production code changes**.
**Core contract:** published `pds-core` **0.6.6** wheel; no Core #238 source-only APIs, Suite launch changes, or Meridian changes.

## Completion to date

- Slice 0: six failing-before status-prompt witnesses established; baseline evidence was read-only.
- Slice 1: Activity `draft/configured/active/completed/cancelled/archived` teacher picker, confirmation and Core Standards guard.
- Slice 2: Session `planned/active/completed/cancelled/interrupted/archived` picker, separate time/reason fields.
- Slice 3: Membership/Role/Responsibility End constrained to `completed/withdrawn/cancelled`, without Reassign semantics.
- Slice 4: Group `planned/active/inactive/completed/cancelled/archived/superseded` picker and exact-lifecycle audit. Marking `superseded` does not generate a successor Group.
- Last verified Slice 4 targeted run: **123 passed, zero XFAIL**, commit `82b238e`, pushed to the #146 branch.

## New acceptance in Slice 5

`tests/test_issue146_slice5_consolidated.py` exercises a single real multi-surface Activity → Session → Group workflow under each of **three orientations**: `evidence_only`, `mixed`, and `standards_based`. It asserts independent canonical records, current and requested statuses, focus-standards retention, Session time/reason neutrality, explicit Group non-lineage, and expected immutable Activity snapshot progression. Additional tests call real **direct CLI** handlers with exact status strings, check the unchanged conflict exit code and verify the three assignment-ending CLI command families retain their exact status choices and reject Reassign-only values.

Prior Slice 1–4 menu/service acceptance covers the full 3×3 ending matrix, status-menu navigation, declined confirmation, stale targets, wrong Core authority, and history/lineage. Slice 5 does not repeat the physical classroom/scan qualification owned by #155.

## Exact qualification gate

Runner `concord146_slice5_runner.py` requires clean #146 branch HEAD `82b238e...`, checks important `git rev-parse HEAD:path` blobs, authenticates the source archive and exact **released Core 0.6.6 wheel**, and refuses preexisting modified or untracked files. It adds only this test and audit to the checkout, then invokes:

1. Python compile and focused Ruff on the new test file.
2. Focused `pytest` for the new synthetic cross-surface tests, prior #146 Slices 0–4, the #141 Activity fix, and direct CLI workflow parity.
3. The existing `scripts/validate_repository.py --core-wheel <official-wheel> --allow-dirty` at the **final milestone**. This script already verifies the Core wheel and installed package, authenticates vendored Core fixtures, runs `pip check`, builds the candidate Concord wheel, full pytest, Ruff, strict mypy, documentation checks, release compatibility, Twine/package checks, installed-wheel smokes, and the existing isolated Core 0.6.6 acceptance harness. `--allow-dirty` is necessary because this test/doc-only Slice 5 is applied but not yet committed; it does *not* skip checks.
4. Staged-only whitespace/content check; precisely scoped commit and push only if every command succeeds; clean-tree verification afterwards.

**Do not claim passing qualification until the runner prints `QUALIFIED` and `PUSHED`.** Failing gates must stop without committing or pushing. Avoid installing unreleased Core/Suite sources to make a test pass.

## Human acceptance / PR CI boundary

After the runner qualifies and pushes, create a PR from `146-teacher-first-status-choices-and-enum-audit` into Concord `main`. The PR triggers `.github/workflows/ci.yml` on Linux/Windows Python 3.11–3.14, with the full validator on Linux 3.11 and Windows 3.14. Local successful validation does **not** establish PR CI success or a real teacher walkthrough.

A quick **teacher walkthrough**, using only fabricated test records, should verify that Activity, Session, Group and the three End screens each display a numbered choice, current state, short explanation and current → requested confirmation. Try **B** to back out, **H** for help and a current-state selection, and confirm that any cancel/no-op leaves the Activity snapshot unchanged. Check that GroupPlan Preview/Approve/Apply remain separate actions and changing status does not produce packet, Score, Grade, or publication records. Record these as human evidence separately; do not claim this automated runner performed an interactive physical acceptance.

## Exit decision

- **Local gate:** full validator green; exact two-file source-only change committed and pushed; no external repository changes.
- **PR gate:** all supported CI matrix jobs green; address any independent failures in their owning tickets instead of broadening #146.
- **Teacher-experience gate:** manual synthetic menu walkthrough recorded, or explicitly labeled outstanding for #155.
- **Merge:** only after PR inspection and applicable gates; do not automatically merge, tag, or release in this slice.
