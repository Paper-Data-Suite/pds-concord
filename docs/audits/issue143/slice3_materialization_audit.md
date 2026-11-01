# Concord #143 — Slice 3: Exact cross-class saved scoring-setup materialization

**Status:** candidate for Windows qualification; not a release claim.

## Baseline and scope

- Git baseline and branch: `0eb3721bfd339a40111daf814bfb81eef4a00832`, `143-fix-standards-correct-criterion-preset-roundtrips`.
- Expected cumulative qualified Slice 1+2 tree: `7974ba5aa253e17adf1a70ea975e9db1908f411d`. Verify it by staging only the five exact prior changed/additive files in a detached throwaway Git worktree, never in the original index.
- Installed Core v0.6.6 and authentic Core wheel are required. No Core, Suite, ScoreForm, Quillan or Meridian repository modifications or unreleased contracts.
- Production changes in Slice 3: **none**. Add only this audit document and `tests/test_issue143_slice3_cross_class_materialization.py` if all checks pass.

## Acceptance witness

Use a synthetic Core workspace and **two different Core class IDs**. Source class P2 has a mixed Activity with exact NJSLS Standard `SL.PE.11-12.1`, alignment `W.NW.11-12.3.D`, native standard-backed individual discussion Criterion (`core_student`), and native local Cluster analysis Criterion (`concord_group`). A native four-level ordinal Scale uses exact typed values `1–4`, labeled Developing / Approaching / Meeting / Exceeding. Save the native Scale and Criterion Set under exact revision-pinned reusable preset identities via the Slice 2 services.

Target class P4 independently creates its own `mixed` Activity, then invokes `prepare_scoring_setup` and `materialize_scoring_setup` against the saved preset in its **current Core Standards profile**. On success, exactly one new target Activity snapshot is committed; target owns fresh Criterion Set, Criterion, Scoring Scale and lineage identities, selected on the target Activity. Ordered Criterion meanings, exact Standard/profile/alignment, per-Criterion target kinds, Scale type and typed level values survive. Source graph and snapshots are untouched. Neither Activity acquires a Score, Score Evidence Link, teacher judgment, publication, packet nor student attribution through setup.

Also test: choosing a different saved Scale is explicit and retains *its* typed levels; no recommendation allows intentionally no new Scale and no default reference; a recommendation cannot silently be omitted; wrong Focus and wrong profile reject; duplicate/missing Criterion identity mappings and unpaired Scale fields reject; bad review digest and stale Activity revision reject; retrying the same generated identities rejects, all without extra target writes; the real teacher-menu `Use saved assessment setup` route both commits on teacher confirmation and cancels with zero writes.

Use actual public workflow/graph/teacher-menu entry points. Monkeypatch only the selected test workspace and interactive prompts, not guarded storage, Core validation, or service commit logic. Audit remains synthetic-only. No real classroom paths.

## Boundary with subsequent tickets

Slice 3 proves stored assessment *definition* transfer and native, independent target materialization. It does **not** assert physical paper return, scored proficiency, cross-class student/group reuse, Meridian publication, or the broad teacher-first UI improvements owned by Concord #145/#152. Additional Core/Suite work is not a prerequisite. Later #143 slices should address remaining direct CLI parity, revision/retirement/serialization permutations, full repository tests, frozen #140/#162 evidence handoff and final release qualification.

## Qualification

Authenticate the exact Core 0.6.6 wheel/installed distribution; run historical #129/#64 tests plus #143 Slice 1, 2 and 3 tests, Ruff on affected production/test sources and strict mypy for `concord`. Guard exact Git file inventory, remote HEAD, previous cumulative Git tree, candidate-only writes, no source/target data outside synthetic pytest temp, and an empty original index. Do not claim qualification until Windows output confirms each gate.
