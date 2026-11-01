# Concord #143 — Slice 2: native-to-preset save qualification

**Baseline:** `143-fix-standards-correct-criterion-preset-roundtrips` at `0eb3721bfd339a40111daf814bfb81eef4a00832`, plus the **exact already-qualified Slice 1 tree** `b08b81ee8a7fb77b4db9fc4f7d2fa24071bb0c8e`. Slice 1 was independently qualified on Windows: 48 focused pytest cases, Ruff, and strict mypy (220 source files). Both production and test additions remain unstaged in the original checkout.

**Purpose:** Verify that correcting the three Standards identity fields actually unlocks the source native mixed Criterion Set → workspace-reusable Criterion Set preset path, from both the public workflow API and the existing ordinary teacher menu. No new production code is required if these checks pass; retain responsibility for the reusable preset contract inside Concord, not Core or Suite.

## Contract and boundaries

- Core `0.6.6` owns `StandardsLibrary`/profile/Focus/active status; use supplied canonical synthetic library for qualification. No new Core identity/validation implementation is introduced.
- Concord native `Criterion` and `CriterionSet` are Activity-owned; `CriterionSetPresetRevision` is a *definition*, not the source Activity's state. Copy ordered labels, kind, targets, exact Standard/profile/alignment IDs, and an **explicitly selected existing** Scale-preset recommendation only. Never copy native record IDs, Scoring Scale IDs, lineages, Score Records, Score Evidence Links, review judgments, student records or returned-paper claims.
- The four-level ordinal Scale values remain `1 Developing`, `2 Approaching`, `3 Meeting`, `4 Exceeding` with exact typed values and ordered labels.
- Save can be performed with or without a Scale recommendation. No recommendation means no fresh native default Scale implied by the saved Criterion preset.
- Preview and teacher cancel are read-only. A stale source Activity revision, malformed/mismatched Scale recommendation, duplicate preset ID, incompatible Core context or rejected digest must not create a new preset or mutate source Activity snapshots.
- **Repair 1, negative-test boundary:** a previously valid native Activity becomes invalid under a subsequently inactive Core alignment. The authoritative `load_current_record_graph` rejects that existing graph with `ConcordStorageGraphIntegrityError` *before* reusable-preset validation. Assert that exact integrity boundary and preserve the original graph/snapshots when re-read against the initial active Core library; do **not** weaken graph validation or reclassify the error as a workflow validation failure.
- Ordinary teacher menu witnesses call the actual `_save_criterion_set_as_preset` handler and actual underlying workflows; only their synthetic-workspace root binding, controlled menu selections and confirmation display are injected.

## Tests and scope

Add `tests/test_issue143_slice2_native_preset_save.py`. It creates **only** pytest temporary synthetic workspaces and covers native mixed individual-standard/Cluster-local Criterion Set creation with dotted governing and aligned IDs; existing Scale preset save; read-only native-to-preset preparation; reviewed commit; serialization/reload/validate; no-recommendation path; stale preview; tampered review digest; invalid Scale-preset field pair; duplicate preset; inactive Core alignment; positive real-menu save and menu cancellation. Assert exact source snapshot/graph preservation and zero Scores.

Run the focused original #64, native #129, Slice 1 and Slice 2 tests, then Ruff and strict source mypy inside a detached disposable worktree built from the verified Slice 1 tree. Only after all pass, copy exactly **two additive files** (new test + this audit) into the original checkout; its index stays empty. No production files are modified in Slice 2. The runner must reject unexpected repo dirt, extra files, a moved Git HEAD/remote head, wrong Core wheel, a changed Slice 1 Git tree, or ZIP digest mismatches.

## Explicitly not claimed

- Second-Activity materialization and fresh ID/Scale semantics are **Slice 3**, not part of this qualification.
- Full-branch pytest, wheel/sdist validation and Linux/Windows CI remain later release gates.
- No live classroom data, real student judgments, printed/returned scans, Meridian publication or cross-module upgrade has been tested.
- Core #238 and Suite #49 are independent development streams; no new dependency or duplicate implementation.
- Concord #145 (teacher-first rubric design), #152 (teacher-friendly Score labels) and #162 (independent audit signoff) retain their respective scope.

**Acceptance gate:** both the exact Core-authenticated source-level contract and actual-menu save/cancel paths pass; existing Focus, roster, snapshot, preview/digest and immutable provenance guards remain authoritative; original working tree contains the exact prior three Slice 1 files plus only this slice's two additive files, with nothing staged, committed or pushed.
