# Concord #145 — Slice 6: synthetic cross-class and installed qualification

## Checkpoint and ownership

- Immutable starting commit: `a05a568d6135c2ac0e568afa11549acea0677753`
- Starting Git tree: `8ee701e3b29bdc1d82dc80daf2186e3f065b884e`
- Branch: `145-teacher-first-criterion-sets-and-saved-assessment-setup`
- Scope: **test-only qualification changes**: two additive #145 files and one narrow #143 legacy test-fixture compatibility repair; no changes to production modules, Core, or Suite.
- Published Core dependency remains verified `pds_core-0.6.6-py3-none-any.whl` (SHA-256 pinned by runner).

## Evidence and expected assertions

1. A synthetic source Core class hosts a mixed Jíbara-style Activity using one standards-backed individual Criterion (`SL.PE.11-12.1`) and one local Cluster Group Criterion, both on the typed integer 1–4 Scale.
2. The teacher-facing #145 projection retains exact native identities, Standard IDs, alignment IDs, Criterion target kinds, selected order, and semantic draft metadata **without writing**.
3. The canonical selection service selects the exact source Criterion Set. No Score, Grade, evidence, or Group/student transfer is implied by this selection.
4. Existing reviewed #143 save services extract a Criterion Set preset and exact matching Scale preset. The #145 matching helper rejects a modified Scale definition. Preset exclusions omit native identities and historical Scores/evidence.
5. A second synthetic Core class materializes the prepared exact preset revision under *fresh* native Criterion Set, Criterion, and Scale identities. The target Activity's selection matches the fresh Criterion Set revision; the source Activity stays byte/snapshot identical. Original typed four-level integers, order, target kinds, Standards and alignments are retained.
6. A stale digest for either preset save or target materialization refuses with byte-exact zero writes. A no-recommendation scenario drops native Scale IDs from the reusable preset and creates no Scale on the destination.
7. Focused #143, #144, and #145 tests execute in the same isolated detached-worktree qualification; these tests include native revision/serialization, CLI, cancellation, conflict, tampering, and partial-receipt regression coverage.
8. An isolated wheel build and noneditable `--target` installation inspect installed-package import provenance and ensure the new #145 modules are included. No wheel is installed into the teacher venv or the source checkout.

## Limitations and final-stage handoff

- This is a **synthetic service-backed** qualification, not a claim that a physical classroom, paper return, or live 29/30-student roster was exercised.
- Source and installed smoke tests are not a public release. No student roster, Score, Group membership, publication, or personally identifiable data is copied.
- Full repository Ruff, strict mypy, pytest, broad installed CLI qualification, and GitHub matrix CI remain for the **Final** stage; the targeted suite does not substitute for them.
- Stage evidence is written by the runner to a unique external working directory; no commit, push, PR, or release is performed.

## Slice 6 Repair 1 — #143 synthetic menu fixture compatibility

- The #143 menu test was written before #145 added read-only Activity selection, exact native Scale, and saved-preset revision rereads.
- Its three new reads are redirected to the same pytest-owned temporary workspace as the pre-existing test services; the actual #143 workflow calls and approved/canceled writes remain real.
- The approved-save assertion recognizes the new teacher receipt 'Assessment Saved for Another Class' instead of the older heading.
- No production implementation or Core/Suite code changes. The original test file's Git blob is pinned before replacement.
