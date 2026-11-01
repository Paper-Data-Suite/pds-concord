# Concord #143 — Slice 6: frozen operation lineage and final qualification gate

## Qualification identity

- Scope: the narrow Core-compatible Standards identity change in `concord/reusable_presets.py`, five qualified additive test/audit slices, and this additive successor handoff.
- Development branch: `143-fix-standards-correct-criterion-preset-roundtrips`.
- Verified development HEAD/remote `main` base: `0eb3721bfd339a40111daf814bfb81eef4a00832` (post-#142 merge).
- #142 post-merge CI run `41211502653`: `completed` / `success`, checked 2026-10-31.
- Expected qualified Slice 1–5 cumulative Git tree: `cddf772e0def2257cc0bcb4804165ab7ff140105`.
- Core 0.6.6 published wheel: `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301` (SHA-256).
- #140 frozen teacher-operation matrix SHA-256: `dc9b7d003422e58ba965da5fac82d2b11e90c566a7cc360dc74004e9751689b0`.
- Previous qualified Windows gates (from runner receipts, not independently replayed here): Slice 3, 71 tests; Slice 4, 76 tests; Slice 5, 85 tests, with the stated focused linters and Core authentication. These counts are from separate overlapping suites and **must not be summed into a unique-test total**.

## Exact frozen #140 operation IDs — #162 successor locator

These twelve identities were retrieved from the immutable `docs/audits/issue140/teacher_operation_matrix.csv` at base `0eb3721…`. They are **location/ownership references**, not independent human review, and do not reclassify the 3,685 frozen operation rows. The final runner checks the unchanged source matrix's digest and requires every exact ID.

| Boundary | Frozen `operation_id` |
|---|---|
| CLI create | `concord/cli_app/handlers/reusable_presets.py::handle_criterion_create::create_criterion_set_preset::1` |
| CLI revise | `concord/cli_app/handlers/reusable_presets.py::handle_criterion_revise::revise_criterion_set_preset::1` |
| CLI save commit | `concord/cli_app/handlers/reusable_presets.py::handle_criterion_save::save_criterion_set_preset_from_activity::1` |
| CLI save preview | `concord/cli_app/handlers/reusable_presets.py::handle_criterion_save_preview::prepare_criterion_set_preset_from_activity::1` |
| CLI materialization commit | `concord/cli_app/handlers/reusable_presets.py::handle_scoring_apply::materialize_scoring_setup::1` |
| CLI materialization preview | `concord/cli_app/handlers/reusable_presets.py::handle_scoring_apply_preview::prepare_scoring_setup::1` |
| Preset menu create | `concord/menu_presets.py::_create_criterion::create_criterion_set_preset::1` |
| Preset menu revise | `concord/menu_presets.py::_edit_criterion::revise_criterion_set_preset::1` |
| Activity menu save preview | `concord/menu_scoring.py::_save_criterion_set_as_preset::prepare_criterion_set_preset_from_activity::1` |
| Activity menu save commit | `concord/menu_scoring.py::_save_criterion_set_as_preset::save_criterion_set_preset_from_activity::1` |
| Activity menu use commit | `concord/menu_scoring.py::_use_saved_scoring_setup::materialize_scoring_setup::1` |
| Activity menu use preview | `concord/menu_scoring.py::_use_saved_scoring_setup::prepare_scoring_setup::1` |

The underlying #140 matrix still marks review work pending; no review status, reviewer, signature, or disposition has been changed by this handoff. The frozen baseline's 7,466 other AST calls remain outside the narrowed operation matrix. Source line numbers are not treated as durable identities across changes.

## Fixed-after evidence and boundaries

- Existing Slice 1 model changes apply the native Standards helpers to Standards-typed preset fields only. Native routing, Criterion keys, preset IDs and Scale revision IDs remain strict.
- Slice 2 covers save-from-native and teacher create/save lifecycle with exact dotted Standards, native Scale versus reusable Scale-preset identities and zero copied operational evidence.
- Slice 3 covers independent synthetic Class/Activity materialization and recommended, explicit-alternate, and permitted no-Scale paths. A new native graph and zero inherited Scores are required.
- Slice 4 covers immutable revision, stored JSON and direct CLI paths.
- Slice 5 covers fail-closed adverse Core, target, Scale, review, CAS, duplicate and codec paths; a byte-exact synthetic workspace fingerprint guards refusal cases.
- Separate existing #63, #64, #129, #136, #141, #142 regressions are covered at the full-repository gate, not asserted as independently reviewed #162 operation rows.

## Final gate and limitations

The guarded runner constructs a detached candidate worktree at the pinned #142 merge HEAD, copies exactly the eleven qualified Slice 1–5 files, validates the expected cumulative tree, adds only this document, and runs **one** `scripts/validate_repository.py --core-wheel ... --allow-dirty` full qualification. This existing tool includes full pytest, Ruff, mypy, documentation, release compatibility, build, package verification, isolated installed-wheel smokes and Core grouping fixtures. It also runs one targeted installed Core 0.6.6 + candidate Concord wheel smoke with the exact `SL.PE.11-12.1` mixed Criterion preset in a temporary isolated environment. All evidence/logs remain outside the developer repository. No class/student/roster records are read from any real workspace.

**Not yet established at documentation time:** results of the Windows final gate, an independently authenticated replay of the original published Concord 0.3.4 wheel for #143, Ubuntu/Windows PR CI, human reviewer approval, any merge, post-merge CI, branch reconciliation, or a new release. Passing one local runner does not constitute full Suite composition or authorize grading/publication. Attach exact runtime results, candidate tree and wheel SHA to the PR only after they actually pass.

Frozen #140 files, #162's independent review ledger, and Core/Suite/Meridian/release metadata are deliberately untouched.
