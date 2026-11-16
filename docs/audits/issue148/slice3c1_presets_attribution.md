# Concord #148 — Slice 3C1: reviewed reusable-preset attribution

Baseline: `43ed246ee445083019685de6a4736b91cf31c74a` on `148-persistent-reviewable-teacher-attribution`. Dependency remains published Core 0.6.6; no Core, Suite, Meridian, direct CLI, or academic workspace contract change.

## Adopted teacher-menu operations

The nine local reusable-preset write confirmations in `concord/menu_presets.py` now use `confirm_actor_write` and pass the *returned, immediately reviewed* `WorkflowActor` into exactly one downstream workflow request:

- Create: Role, Responsibility, Scoring Scale, Criterion Set presets.
- Revise: Role, Responsibility, Scoring Scale, Criterion Set presets.
- Retire: one selected kind of preset.

The confirmation title, verb, educational substance, version/preset IDs, and immutable-version behavior are retained. Provider-backed sessions offer an alternate adult for this action only. Legacy explicitly supplied actor sessions keep the old `confirm_write` pathway; direct CLI remains explicit and noninteractive. This is attribution, not authorization, Core Notes owner selection, or a shared PDS identity authority.

Pre-review Scoring Scale draft validation continues to use the saved/default actor for provisional validation inputs; the persisted request actor is the actor selected at the consequential confirmation. Temporary alternatives are never queued or saved.

## Cancellation correction

The existing Role/Responsibility/Criterion Set `_edit()` dispatcher unconditionally displayed a success receipt after an editor returned without writing. These three editors now return a simple boolean indicating actual dispatch. The dispatcher shows `Preset Updated` only on `True`. The Scoring Scale editor already manages its own success/no-op/cancellation receipt and is unchanged in this respect.

## Qualification

Tests assert the exact nine actor-confirmation-to-write flows at AST level, and dynamically test the selected Role create/revise/retire actor, cancellations and no false edit receipt. Qualification runs Ruff, strict mypy, installed Core verification, focused regressions and a clean-scoped commit/push. No production data or local teacher profile is touched by these tests.

## Outstanding

This slice does **not** claim that all Concord action actor callsites have migrated. Continue with Activity-native Scoring/Criteria and Artifact/Review, role/responsibility assignments, publication and other consequential writes. Run final exhaustive callsite census, full regression, safety and Windows teacher-menu acceptance before closing #148.
