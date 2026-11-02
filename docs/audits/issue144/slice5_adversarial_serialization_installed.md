# Concord #144 — Slice 5 adversarial, serialization and installed qualification

**Scope:** additive synthetic regression tests and an installed-wheel smoke program; no production implementation changes, no migration, no grading rules, and no Core or Suite edits. This is a candidate qualification slice, not a release.

## Evidence targeted

- Guided integer/decimal/text/category/Yes–No input refuses malformed values, nonfinite numbers, lossy decimals without explicit review, ambiguous separators, underflow, oversized input and unsupported types. Source model refuses null/dict/list and nonfinite values.
- Native `ScoringScale` JSON record codec preserves type-specific distinctions among `1`, `1.0`, `"1"`, `true`, and Unicode text, along with labels/meanings/descriptions, and `level_for_value` finds only the exact type.
- Scale model rejects same-type duplicate values, incompatible numeric/binary shapes, and unknown codec fields.
- Reusable preset create/revise survives canonical JSON serialization and storage/reload; revisions remain immutable, stale `expected_revision` refuses and no Score is synthesized.
- Existing direct `scale-preset` CLI creates and shows a typed JSON preset noninteractively. Existing older CLI-native and #143 regression suites are run unchanged.
- Wheel is built from an isolated source copy of the qualified candidate, verified to contain exact source bytes of the four impacted Concord modules, installed to a private target and imported with `python -I` while executing from outside the repository. Synthetic installed smoke writes only to an isolated temporary workspace.

## Explicit limitations

Focused Slice 5 evidence does not replace the final **full-repository** pytest, Ruff, strict mypy, sdist/wheel+Twine and Windows/Linux CI acceptance. It does not prove a real student/Group Score path end-to-end nor that any results were graded or published; prior Score history and #143 regressions remain a separate gate. Physical classroom acceptance, cross-module installed Suite support, signed distribution and the independent #162 audit remain out of scope.

The runner checks exact existing qualified cumulative tree `ed6c1dbc70de9c521203700070243bdc3b5635b0` before adding these files and refuses unexpected branch, file, or remote changes. It never commits or pushes.
