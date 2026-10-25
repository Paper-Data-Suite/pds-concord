# Concord #141 → #162 — Activity-edit source qualification handoff

**Evidence type:** additive automated source-level handoff; **not** an independent semantic-review signoff, published-wheel replay, or Suite integration certification.
**Observed local qualification date:** 2026-10-25 (user-supplied Windows PowerShell transcript).
**Branch:** `141-repair-activity-standards-context` (pre-commit parent `419f6aa36f9376befe5d45c3ed01b1c9fd8455a7`).
**Historical source baseline:** Concord `main` `40837d54376f70cffb9ca539d52f7e40453ec1e6` (#140 merged); frozen #140 audit artifacts remain unchanged.

## Frozen operation lineage

- Exact original operation ID: `concord/menu_activity.py::_update_activity_field::update_activity::1` (read from unchanged `docs/audits/issue140/teacher_operation_matrix.csv`).
- Original menu boundary: `concord/menu_activity.py::_update_activity_field` → `concord.workflows.update_activity`.
- The menu dispatch choices Title, Description, Status, Activity type, and Scoring orientation / Focus Standards converge on this operation; these are **five behavior cases**, not five distinct frozen service IDs.
- Original C1 failure: `tests/test_issue140_slice2_failing_before.py`, later converted to a positive source-level regression under #141.
- The source-line position in the frozen matrix refers to #140's historical code, not the modified working tree.

## Scope and contract outcome observed on the #141 source WIP

- Pin one exact workspace root through the Activity reader, structural graph read, authoritative Core Standards-library selection, and writer; reject mismatched structural workspace identity before writing.
- Preserve Core-owned active Standards/profile/Focus validation; graph-history requirements for Standards-backed Criteria/Score despite apparently neutral orientation; and Concord's guarded domain storage and snapshot/CAS checks.
- Verify the five ordinary edit choices with mixed/standards-based and neutral controls; orientation transitions, missing/wrong authority, cancellations, no-op, wrong-class isolation, and stale-snapshot refusal in disposable synthetic workspaces.
- The independently run cross-root diagnostic **before** Slice 5 reproduced a source write using a foreign Standards read (source snapshot +1); Slice 5 added specific identity/no-write regressions and was focused-qualified after repair.
- No teacher/student production data, paper packet, Core Notes private store, publisher state, or real workspace was used in these tests.

## Qualification observations (not a committed-SHA/CI attestation)

- **Full source pytest:** `2581 passed, 18 skipped` on Windows (fresh `%TEMP%` pytest root; user-supplied 2026-10-25 transcript).
- **Ruff:** full repository lint passed; exact 10 changed Python files passed format check. The committed project has unrelated pre-existing Ruff-format differences, so full-tree formatting was **not** represented as clean.
- **Mypy:** project-wide strict check passed, 269 source files.
- **Dependencies:** `python -m pip check` passed.
- **Historical #140:** frozen Slice 1 source census (3,685 operations / 10,182 calls) and Slice 4A guard (67 surfaces) passed by authenticated frozen-source replay, without updating original receipt bytes.
- **#141 Slice 0:** immutable source receipt check passed; `git diff --check` and exact twelve-file WIP scope passed.
- **Previous Windows transient:** one full-suite run failed with Core workspace metadata `PermissionError [WinError 5]` at atomic replace; three isolated module runs and later full suites passed. Root process of original denial not identified.

## Not qualified / follow-up owners

- **#162:** full teacher-operation semantic ledger and human reviewer attribution still pending; this handoff is **candidate source-level evidence**, not status `FIXED_IN_LATER_ISSUE` before #141 merges and the changed-code boundary is reviewed.
- **#142 / #143 / #152:** Artifact context propagation, Criterion preset identity and Score-label reliability are separate defects; neither is resolved by #141.
- **#154 / #155 / #159:** installed Concord wheel, exact Core composition, physical/returned-paper and downstream gates remain separately owned.
- **Core #238 / #242 and Suite #49 / #53:** transaction-scoped root pinning is not durable teacher-private workspace association; later Core shared-menu or Suite workspace changes must trigger producer context revalidation. No unreleased Core dependency was introduced.
- **GitHub:** PR CI, Linux/Python matrix, built-wheel/package checks and installed-wheel smoke remain **pending** until an exact committed branch undergoes CI.

## Pre-commit source inventory SHA-256 (captured after reported green source tests)

The following source digests are locally computed by this handoff script. They identify the exact twelve-file WIP at handoff creation; they do **not** independently prove the earlier pytest transcript ran these exact bytes.

| Relative file | SHA-256 |
|---|---|
| `concord/menu_activity.py` | `1c5fc951ac601fa89a9af2363ed14eec85e7e17d6cddb4c4daa31c4aa8cf7380` |
| `tests/test_issue140_slice2_failing_before.py` | `6990412491a6b9901bcddc15413773dc0fc010b3b568eafbf6cff4e82b1e400d` |
| `tests/test_issue140_slice4a_guard.py` | `c5e648ec8be76e70199232212e7bb118e6de354ba16ec3b68b240766064ca6fd` |
| `docs/audits/issue141/slice3_frozen_archive.json` | `0f383c189e3a1707afda56e24e61278bfd828de88bc27819f310f030de96b63c` |
| `scripts/issue141_historical_audit.py` | `e7b81b06f6f08f55d90606730d1ecdaacac34f69a5bea7c6f3ea92961f854226` |
| `tests/fixtures/issue140_frozen_source.zip` | `59612205119852b71d3ab732a15dc5c92b852ccd54824a99e73a8f7291f0237a` |
| `tests/issue141_frozen_audit.py` | `2eaa339dd1a59c43a636a7edb3ddbb1bbd9ac2a162fc245727b810cd37a3bc7a` |
| `tests/test_issue141_slice1_activity_context.py` | `92ad3bdb172bca95c1c506dd1e9700a87b689d4e11f8111c89d851d9541d1bfb` |
| `tests/test_issue141_slice2_graph_history.py` | `81e01a9dc681542c21c585522e957ff0551727c26e027a3b169c64f81f64976e` |
| `tests/test_issue141_slice3_historical_audit.py` | `f2518db06a52ebdf809e832eaba0a0d6656d7a9fb17deaa560da6b915ce7e301` |
| `tests/test_issue141_slice4_activity_edit_acceptance.py` | `50e59302935047cc017bdb19205e97dae7e3d6f2485f0cb8700452e2e08417dc` |
| `tests/test_issue141_slice5_workspace_identity.py` | `a321dc183f690738a9ea3b1acc9b4ac03a404af532113ec814e31c7190c8685d` |

## Review/merge protocol

Keep #140's frozen audit and original C1 lineage immutable. After PR merge, #162 should reconcile the original operation ID with the merged SHA, review actual contracts and test evidence, and record a genuine reviewer/disposition without inferred signoff. Qualify published wheels, independent audits and physical journeys only in their owning issues.
