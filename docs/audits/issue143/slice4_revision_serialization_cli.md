# Concord #143 — Slice 4: Preset revision, JSON codec, and direct CLI

## Baseline and boundaries

- Branch: `143-fix-standards-correct-criterion-preset-roundtrips`
- HEAD: `0eb3721bfd339a40111daf814bfb81eef4a00832`
- Exact qualified Slice 1–3 cumulative Git tree: `af82f479c48705fa0a82438da42fd8033981ab75`.
- Required Core release: `pds-core==0.6.6`, authenticated by repository verifier.
- Additive tests and this audit record only; **no production change** in Slice 4.
- Synthetic temporary PDS workspaces only; no real student roster, Score, evidence, Core, Suite, or Meridian mutations.

## Contract under test

1. Native mixed Criterion Set saved from synthetic English 12 Activity contains the exact Core Standards identifiers `SL.PE.11-12.1`, `W.NW.11-12.3.D`, and the profile `njsls-ela:profile.2023:11-12`.
2. Revised Criterion Set preset retains the original immutable revision while recording the new revision and supersession link. The standard-backed Criterion retains `core_student` targets, and the local Criterion retains `concord_group` targets. Scale recommendation is a reusable preset identifier, **not** a copied Activity-native Scale identifier.
3. JSON encoder/decoder round trips both exact revisions without loss of dotted identity, alignment order, profile, target kinds, Scale reference or source semantics. The tested codec is the same internal schema codec used by on-disk preset persistence.
4. Stale revision and unknown Core Standard fail without changing the current preset.
5. The actual direct CLI handles `criterion-preset create`, `revise`, `list`, `show`, and `validate` using a current synthetic Core library, exact JSON definition and expected revision; no interactive prompts.
6. No score or Activity snapshot side effects arise from preset-only operations.

## Qualification gates

- Fail closed before writing to the original repository unless the local branch, exact commit, remote `main` and #143 branch, source inventory, empty index, Core wheel and cumulative Slice 1–3 tree all match.
- ZIP must have only the two additive files, `manifest.json`, and `README.md`, with per-member SHA-256 verification and no duplicate ZIP names.
- Candidate is a detached Git worktree. Copy previous seven qualified files, stage and prove exact cumulative tree, then add only the two Slice 4 files.
- Focused pytest includes issue #129 and #64 baseline plus #143 Slices 1–4; Ruff examines touched Python; mypy uses repository configuration for `concord` source. No full-repository pytest in this slice.
- Repeat original preflight after qualification; copy only two additive source files, do not stage, commit or push, and byte-check the resulting inventory.
- On failure, leave the original repository untouched and preserve logs in the disposable qualification directory.

## Subsequent gates

Slice 5 should prioritize hostile inputs, stale/cancel, negative/no-write recovery and cross-entry-point validation. Full-repository tests should be reserved for the final integration/merge qualification, not repeated per slice.
