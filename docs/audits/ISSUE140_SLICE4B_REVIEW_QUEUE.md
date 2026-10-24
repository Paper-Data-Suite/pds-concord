# Concord #140 — Slice 4B: surface-level semantic-review queue and reviewer protocol

**Starting commit:** `b979a3761b83756302d36d8dbbb8a067fe35d656` (qualified Slice 4A). Frozen comparison: Concord v0.3.4 / Core v0.6.6. **Audit-only; no production code or teacher workspace access.**

## Purpose and exact limits

Slice 1 froze a deterministic census of **67 teacher/CLI source surfaces**, **3,685 menu/CLI operation entries** and **10,182 AST calls**. Slice 4A established exact source- and operation-drift detection; it did **not** verify those 3,685 routes semantically. Slice 3E separately reconciled the **18** specifically named P0.2 families (13 real menu context-first guard reproductions, 2 demonstrated label degradations and 3 unqualified positive paths).

This slice adds a **create-only surface review queue**, not a second large operation matrix. `scripts/issue140_slice4b_review_queue.py` reads the frozen `surface_inventory.json`, `teacher_operation_matrix.csv` and `slice3e_scoped_dispositions.csv`. It accounts for **every** original surface, handler, workflow boundary, menu delegation and other AST call, reconciles the exact 18 scoped statuses by source file, and records the number of operations whose contextual contract fields still require review.

The generated `docs/audits/issue140/slice4b_surface_review_queue.csv` contains one row per audited source file. Every row is **`REVIEW_REQUIRED`**, with `human_reviewer=UNASSIGNED` and an empty review date. Suggested child-issue owner values are only **routing proposals**, not an approval, issue assignment, bug claim or guarantee of a safe operation. No call in `OTHER_CALL` is silently counted as a verified standards-neutral path: it remains visible as `other_calls_unclassified`, with the exact AST detail in the original source inventory.

## Reviewer protocol

1. Run the read-only source, matrix, scoped evidence and queue guards *on the exact baseline*. Inspect the intended file and its route through the ordinary menu or CLI. `source_inventory.json` includes the other/unresolved calls excluded from the narrower operation CSV.
2. For each source-file queue row, review all constituent **operation IDs** in `teacher_operation_matrix.csv`, including function-entry records and workflow/menu delegation records. Confirm reachability, import aliases/wrappers/`**kwargs`, and whether a delegated service loads canonical Standards internally or uses a properly neutral read. **Do not** treat missing visible `standards_library` as sufficient failure evidence.
3. Record the applicable Activity mode and actual graph conditions (orientation, Standards-backed Criteria and Score history), canonical Core Standards and roster authority, owning class/Session/Group context, teacher actor, workspace root, source provenance, and privacy authority. Establish whether each route reads, previews, mutates, triggers a cross-store follow-up, or requires a human physical gate. Document CAS/digest/stale/cancel/recovery and no-write behavior.
4. Only promote a disposition with a precise **operation ID**, downstream contract review, reproducible evidence/test reference, before-and-after record/snapshot check where relevant, owner, reviewer/date, and clear distinction between **menu-reproduced**, **source-only suspected**, **deliberately internal resolution**, **neutral verified**, or **blocked/human gate**. Conduct positive returned/assembled and Score tests only with legal synthetic evidence, not fake student work or inferred judgments.
5. Make updates in a separately reviewed **successor** matrix/ledger, never by silently rewriting Slice 0–4A create-only evidence. Re-run 4A and 4B consistency checks; changed source requires controlled re-baselining and explicit review, not blanket AST exceptions.

## Routing of currently identified work

- **#141:** Activity lifecycle/edit Standards propagation (Slice 2 C1).
- **#142:** Artifact attribution, Detailed Review, Moderation and routine Score context (13 context-first witnesses; first/continued Score and Quick Review positive path remain unqualified).
- **#143:** Valid dotted Core Standard identity in Criterion Set reusable preset (Slice 2 C2).
- **#145/#152:** assessment/scoring human usability and accurate, non-suppressed Score/Criteria labels (Slice 3A).
- **#147/#148/#149/#150/#151/#153:** grouping, identity, stage attention, cross-class reuse, collection and navigation/operational review as their own contractual follow-ups.
- **#155/#159:** end-to-end, installed release, real returned-scan and physical/Windows/Core/Meridian acceptance. No physical success is claimed.
- **#156/#157:** Corbeau/Gemini independent review; no external attestation is invented here.

The proposed mapping is intentionally broad for shared modules. Each review item still needs its actual owner and evidence validated. Do not infer that a routing proposal constitutes acceptance of the corresponding issue.

## Offline commands

```powershell
python scripts/issue140_slice1_census.py --repo . --check
python scripts/issue140_slice3a_triage.py --repo . --check
python scripts/issue140_slice3e_dispositions.py --repo . --check
python scripts/issue140_slice4a_guard.py --repo . --check
python scripts/issue140_slice4b_review_queue.py --repo . --check
python -m pytest -q tests/test_issue140_slice4b_review_queue.py
```

For **first creation only**, replace the review-queue `--check` with `--generate`. It fails instead of overwriting if a different queue already exists; `--check` never writes. The script imports no Concord/Core modules, accesses no classroom workspace, does not inspect a user's OneDrive, and performs no network or publication calls.

## Remaining #140 closure work

Slice 4C must consolidate source/installed-wheel limitations, no-fake-signoff review debt and this queue with the 18 scoped dispositions, attach a cross-issue evidence handoff for #141–#143, and specify exact outstanding independent review, full-test, returned-work and physical gates. This queue is a **review assignment and coverage accounting artifact**, not a completed semantic audit of every route. Neither the released Concord wheel (not provided in Slice 0) nor an installed-wheel replay has been independently qualified by this work.
