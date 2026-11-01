# Concord #143 — Slice 5: Adversarial fail-closed qualification

## Qualification baseline

- Branch: `143-fix-standards-correct-criterion-preset-roundtrips`.
- HEAD and remote `main` / branch expected: `0eb3721bfd339a40111daf814bfb81eef4a00832`.
- #142 post-merge `main` CI run `41211502653` was independently checked: completed with `success` at the unchanged HEAD.
- Qualified cumulative Slice 1–4 tree: `09304c239a9056b9104a628581164bcbb0b07f07`.
- Core published wheel: `pds-core==0.6.6` (locally SHA-256 authenticated and installed verifier invoked by runner).
- This slice adds **only** `tests/test_issue143_slice5_adversarial_fail_closed.py` and this audit record; no runtime/model/CLI changes or cross-repository edits.
- All test workspaces, classes, Activities, native records, and presets are synthetic and temporary.

## Fail-closed matrix

| Boundary | Injected adverse condition | Required outcome |
|---|---|---|
| Revision/Core | No Core library; unknown punctuation-bearing primary Standard; unknown alignment; unknown profile | Structured validation refusal; byte-identical workspace and unchanged preset |
| Creation/Core | Dotted, structurally valid Standard with no authoritative Core library | No preset created or hidden workspace mutation |
| Revision/Scale | Exact recommended Scale revision is missing | Refusal; no guessed latest Scale revision |
| Model | Unpaired Scale reference; duplicate normalized alignment | Model refuses before storage |
| Storage | Manually corrupt one synthetic current revision JSON file | Read refuses; corrupt bytes are not auto-repaired or migrated |
| Codec | Serialized primary Standard changed to a non-string value | Typed decode refuses; no persistence effects |
| Neutral preset | Local-only group Criterion with no Standards identity or library | Valid direct create and read/validate; no unnecessary Core dependency |
| Target/preview | Wrong expected Activity CAS, unknown exact preset revision, missing Scale revision, incomplete Scale IDs, duplicate Criterion identity mapping, cross-Class Activity identity | Preview refuses; byte-exact prior state |
| Target/approval | Changed review digest after successful preview | Commit refuses; no partial Criterion Set, Criteria, Scale, or snapshot |
| Target/CAS | Replay an already successful reviewed request | Second commit refuses; no extra snapshot or partial write |
| Target/Focus | Compatible profile but Focus only contains alignment, not the governing primary Standard | Exact governing Focus check refuses; no target mutation |

`_fingerprint` checks relative file inventory plus SHA-256 of every existing file in the synthetic workspace around each refused operation. This detects byte changes and new files, including unintended preset revisions, native records, snapshots and Core metadata. It does **not** claim an independent atomic transaction across preset-store writes and Activity graph commits; separate positive and concurrency gates remain necessary.

## Risk controls

1. Runner verifies clean index, exact branch and HEAD, pinned `origin`, current remote branch heads, permitted prior changed/untracked files, published Core wheel and exact cumulative staged Git tree **before** running tests.
2. Runner creates a detached candidate worktree and copies the prior nine qualified files from the existing checkout (one modified model file and eight additive tests/audits) without staging or modifying the original.
3. Focused pytest runs only Slice 5 and selected historical #63/#64/#129/#141/#142 regressions, **not** the full repository. Ruff checks the new test plus prior changed runtime model; mypy on unchanged production code is deliberately deferred to final integration rather than re-run without a source change.
4. Failure preserves logs/worktree and leaves original checkout unchanged. After success, re-run full original guards; mirror only two additive files, with empty original Git index and byte-exact candidate/original verification.
5. No commit, push, PR, merge, branch deletion or version/release assertion in this slice.

## #140 / #162 audit boundary

This record is additive to the frozen #140 evidence and does not modify or reclassify the 3,685-row census. **No individual operation ID is asserted here without inspecting the corresponding frozen row and canonical #162 mapping.** Independent successor review and full installed Windows/Ubuntu qualification remain pending; this slice is not reviewer sign-off.

## Next gate

After qualified Slice 5, review coverage gaps against #143 issue Sections E/F, inspect the complete bounded diff and current Core/Suite status, then run a **single** proportional full integration/build/install qualification before commit/push/PR and later PR CI. If any test fails, classify the failure against source contracts before changing production code.
