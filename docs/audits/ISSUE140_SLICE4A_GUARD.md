# Concord #140 — Slice 4A: read-only drift and evidence-crosswalk guard

**Starting branch commit:** `7d8ab6f5e8f0a9341f9f8dd7eaff48227491561e` (qualified Slice 3E). **Audit-only:** no Concord/Core production changes, no real classes, no workspace access, no publication or scoring.

## What this increment enforces

The new `scripts/issue140_slice4a_guard.py --repo . --check` is **read-only**. It runs a bounded crosscheck over the existing checked-in Slice 1 census and the Slice 3A/3E scoped ledger:

- Re-enumerates the complete Slice 1 menu/CLI surface set, handlers, and every AST callsite (including excluded `OTHER_CALL` entries). New modules, added calls *inside old modules*, changed targets/import resolution, removed calls, and line shifts generate short added/missing diagnostics rather than silently accepting changed coverage.
- Validates that every inventoried handler and every `WORKFLOW_CALL`/`MENU_DELEGATION` corresponds to exactly one stable `operation_id` in the source matrix. Detects duplicate/missing/unmapped IDs, broken boundary kind, source/line changes, and service-alias mismatches. The original matrix remains immutable at this stage.
- Cross-checks **all 18** #138 P0.2 family rows against their original candidate source coordinates and the actual operations in the large matrix, including both first/continued `record_prepared_routine_score` callsites. The per-family behavioral status remains in Slice 3E, not backfilled into the frozen Slice 1 source census.
- Registers one **narrow, evidence-backed internal-resolution mechanism**: `prepare_artifact_pages` calls `_standards(root)` and forwards the resolved `library` to guarded graph loading and record commits. A focused Slice 3A test must still exist. This proves a forwarding mechanism only, **not** an end-to-end returned-page acceptance or universal `NEUTRAL_VERIFIED` classification.

### Classification discipline

The guard treats unreviewed entries as *identified audit debt*, not as passing tests. It does not infer that a visible omitted Standards keyword is a bug, that dynamic dispatch is resolved, or that a passing AST check establishes correct authorization or record semantics. Do not suppress source drift or change an operation ID to make a test pass. Review the change, update the separate controlled audit baseline with approval in a later slice, and assign missing behavioral evidence to an explicit child/human gate.

The 18-family breakdown remains 13 context-first menu failures, two Score-label display degradations, and three unqualified positive paths, with the exact owner/test identities in `slice3e_scoped_dispositions.csv`.

### Run and test

```powershell
python scripts/issue140_slice1_census.py --repo . --check
python scripts/issue140_slice3a_triage.py --repo . --check
python scripts/issue140_slice3e_dispositions.py --repo . --check
python scripts/issue140_slice4a_guard.py --repo . --check
python -m pytest -q tests/test_issue140_slice4a_guard.py
```

### Limits and next slice

This is **Slice 4A**, not #140 completion. Slice 4B must add reviewer-assigned contract dispositions beyond the 18 known P0.2 sites, acknowledge unresolved `OTHER_CALL` dynamic delegation and incomplete activity-mode/roster/actor/CAS/privacy classification, consolidate a handoff report, and record installed-wheel and Windows/physical acceptance limitations. The guard deliberately **cannot** convert those unknowns into confirmed neutral operations. It neither reads a live Core workspace nor produces a new privileged allowlist.
