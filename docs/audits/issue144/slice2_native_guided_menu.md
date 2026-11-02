# Concord #144 — Slice 2: guided native Scoring Scale creation and revision

## Pinned baseline and scope

- Issue: #144; parent #139. Branch: `144-guided-type-safe-scale-creation-and-editing`.
- Squash-merged #143 Concord main/branch baseline: `e47c88654b239ccc4ee7d305e95ce822d67a9d0f`; Git tree: `8fd05b00acbb397dc0bf57cde561deaf7211b84b`.
- Qualified Slice 1 cumulative tree (source-only mirrored, not committed): `e2adb59f29206e6504f9e3bb480e59e3914596a7`. Focused Slice 1 Windows qualification: **59 passed**, Ruff clean, strict mypy clean, official Core 0.6.6 wheel verified. The local original index remained empty.
- Official Core v0.6.6 wheel SHA-256: `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`.
- This slice changes *only* `concord/menu_scoring.py` and adds `concord/menu_scale_guidance.py`, a native-menu-focused test, and this audit. It does not modify `concord/models/*`, workflows, native/preset storage, Core, Suite, Meridian, CLI files, release metadata, or frozen #140 evidence.

## Source-confirmed menu path

Prior native Create/Revise routes asked teachers for an `Exact JSON value` for each Scale level through `_build_levels` / `_prompt_json_scalar` in `concord/menu_scoring.py`. The direct CLI's typed JSON-file interface is deliberately distinct. This is a source-confirmed usability gap, **not** evidence that preexisting Scale persistence was broken. The historical `_parse_json_scalar` helper is retained to avoid changing independent regression expectations; there is no ordinary native Scale menu call to it.

`menu_scoring._create_scale -> CreateScoringScaleRequest -> workflows.scoring_scales.create_scoring_scale -> commit_record_batch`, and `menu_scoring._revise_scale -> ReviseScoringScaleRequest -> workflows.scoring_scales.revise_scoring_scale -> commit_record_batch`, remain the only native write authorities. The menu continues passing the canonical `_library()` and actual `expected_snapshot_revision`; Core's authoritative class/Standards guards and immutable native revision history remain untouched.

## Slice 2 teacher experience

1. Native Scale creation offers four-level numeric/ordinal proficiency, custom Number, literal Text, Yes–No Boolean, Category code, ordered or advanced mixed types. These are **teacher input choices**, not new `ScoringScale.scale_type` values. The in-memory editor uses qualified Slice 1 parsing, exact value formatting and `ScoringScale` validation.
2. A teacher may edit one level, add, remove, or reorder a draft before final approval; in-memory edit is neither a saved Scale nor a Score. Any invalid draft can be corrected before the menu returns to the native commit step. Each exact stored value/type, ordinal position, display label, meaning and description is displayed in the final `CREATE` or `REVISE` review.
3. Decimal values not exactly representable by Python's supported finite `float` refuse silently lossy conversion. The menu explicitly offers re-entry or separately confirmed approximation; a notice is carried into the final review when still applicable.
4. Native revision offers **Keep all existing exact levels** rather than rebuilding them. Existing values, display metadata, type and sequence are retained, and optional intended-use/aggregation fields can be explicitly kept, revised or cleared. A successor remains a separate immutable native record with a new ID, original lineage, greater revision and predecessor link.
5. The post-create receipt explicitly says **Scale created; not yet linked to a Criterion**, with a truthful next action to Assessment Setup → Criteria. Saving the native Scale as a separate reusable preset remains a separate reviewed operation; the full Create-and-use/optional Save-for-reuse continuation belongs to #144 Slice 4 and Criterion-guidance wizard belongs to Concord #145.

## Frozen operation lineage (locators, not independent #162 review)

These are unchanged frozen #140 operation IDs; no row, review disposition or signature is modified:

- `concord/menu_scoring.py::_create_scale::create_scoring_scale::1`
- `concord/menu_scoring.py::_revise_scale::revise_scoring_scale::1`
- `concord/menu_scoring.py::_save_scale_as_preset::prepare_scoring_scale_preset_from_activity::1`
- `concord/menu_scoring.py::_save_scale_as_preset::save_scoring_scale_preset_from_activity::1`

## Qualification and noncollision

The additive tests cover numeric starter, Boolean starter, historical mixed-type keep, typed custom decimal, category code, explicit float precision acceptance, refusal/retry, complete native Create/Revise approvals, cancellation, stale conflict routing, snapshot/identity forwarding and zero Score writes. Run historical Slice 1, native Scales, #30 menu, #64 preset CLI/menu and #143 Standards regressions where practical. The full repository/build/isolated wheel acceptance remains the *final* #144 integration gate, not a requirement to repeat for each slice.

Core #238–#244 continue private Notes/roster/menu services; Suite #49/#51–#54 continue trusted launch/integration and teacher home; Concord #145 owns the Criterion Set wizard, #152 owns Score-entry labeling/UX, and Meridian #128 owns grading mappings. This slice neither imports unqualified new Core terminal APIs nor creates a competing shared input framework; `menu_scale_guidance.py` is Concord-local to Scale drafting.

**Not a release claim:** This document records the planned guards, not a completed Windows qualification. Record pass/fail evidence only from the user's exact runner output. Nothing in this slice generates individual/Group Scores, publication, evidence, grades, or copies live classroom data.
