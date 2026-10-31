# Concord #142 Slice 2C — #140 historical test compatibility

## Evidence observed

The teacher ran the original #140 Slice 3B, 3C and 3D tests after passing
#142 Slice 2B (49 focused tests, Ruff, mypy). Historical regression result:
**8 failed, 20 passed**. All eight failures came from #140 tests targeting
individual Author/Subject operations; the test adapter never selected the
fabricated Core workspace before calling the new #142 operation-context resolver.
Therefore the request was rejected as a missing Class/Activity before reaching
the intentionally absent Artifact or association.

## Minimal test-only correction

This patch updates the *executable historical tests* in:
- `tests/test_issue140_slice3b_menu_guard.py`
- `tests/test_issue140_slice3c_attribution_guards.py`

In both test modules, the synthetic fixture persists its fabricated Core
Standards library using the Core-owned writer; the menu's active workspace
resolver is pinned to the same temporary root; and the adapter forwards the
menu's actual `workspace_root` and `standards_library` keyword arguments to
the unmocked production service. A mismatched workspace root is refused.

Mixed Author/Subject additions and individual corrections/updates should now
clear the repaired Core Standards context boundary, reach their deliberately
absent Artifact or association, and fail without changing a Concord snapshot.
The untouched multi-Author, multi-Subject, and batch-confirm write boundaries
still expect the original missing-Standards guard, until #142 Slice 3 updates
them. The #140 Slice 3D Review/Moderation/routine-Score tests are unchanged.
The neutral-orientation missing-target controls and cancellation tests remain.

## Preservation and limitations

- No modification to **any** `docs/audits/issue140` frozen records, labels,
  historical disposition, or signoff state.
- No changes to production code, module services, or the real Core workspace.
- Nothing in this Slice 2C test reconciliation constitutes returned or
  assembled student evidence, business signoff, or #140-wide coverage.
- The failing historical tests were generated as historical defect witnesses;
  they are converted to forward-compatible regression assertions, not deleted
  or marked `xfail`.
- Test outcome, Ruff, mypy and broader pytest remain to be verified on the
  user's own Concord checkout; this package makes no acceptance claims.
