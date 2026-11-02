# Concord #144 — Slice 4: native Scale next steps and independent reuse

## Scope

After `Create Scoring Scale` successfully writes a native Scale, its caller in the
Scales menu offers an optional, explicit continuation. The native creation itself
remains a single write with unchanged prompt/confirmation semantics; direct
callers still receive the same confirmation, write, and receipt sequence. A
cancel before creation writes nothing. A cancel after creation **does not** undo
native creation.

The continuation offers (1) Back to Scales, (2) open the existing Criterion Sets
menu to configure Criteria, or (3) save the exact just-created native Scale as a
reusable definition. This is **not** a new Criterion wizard (#145) and does not
pretend the Scale was linked automatically. In existing Criterion creation, the
teacher must select the exact Scale and independently commit a Criterion Set.

## Native-to-preset write authority

`_save_scale_id_as_preset` creates a fresh `SaveScoringScalePresetFromActivityRequest`
with the selected native ID, canonical current Activity identity, **fresh**
snapshot revision, and teacher actor. It calls existing
`prepare_scoring_scale_preset_from_activity` and shows its source, reusable fields,
excluded fields, expected snapshot, and the fact that this is a separate write.
Only an explicit `SAVE` approval calls `save_scoring_scale_preset_from_activity`
with the prepared `review_digest`. The result's returned `preset_id` is the only
basis for a reusable-save success receipt.

The older `Save Scoring Scale as Preset` menu uses this same guarded helper. It
still lets teachers explicitly choose any current native Scale.

## Truthful outcomes

- Native creation success alone: exists but **not yet linked to a Criterion**.
- Criteria continuation: opens the existing Criterion Sets menu; does not claim
  linking. If the existing menu throws, show a specific receipt without claiming
  the Scale was undone or any link was created.
- Reuse approval declined: native Scale exists, reusable preset **not saved**.
- Reuse success: native Scale and new reusable preset IDs are shown separately;
  no native ID, Score, evidence, or student/Group record was copied.
- Unexpected reuse exception: native Scale remains; **preset outcome unconfirmed**.
  Do not claim rollback: inspect the current reusable preset library before
  retrying. This preserves honest partial-outcome reporting even if an error
  occurs near or after the second write boundary.

## Boundaries

No Core, Suite, Meridian, or storage/model changes. No automatic Score or Grade.
No automatic native Criterion binding, no new cross-Class lesson replication,
and no grade mapping. Frozen #140 operation inventory remains untouched; #162
independent semantic review is not assumed to be complete. The existing direct
CLI remains unchanged. Preset creation remains a separate immutable saved
revision, not a native Scale rewrite. Core 0.6.6 is the pinned wheel baseline.

## Tests and qualification

Focused tests cover separate approval, exact native ID and review digest, no
write on cancel, snapshot refresh, linked-Criterion disclaimers, success and
partial-failure receipts, reuse of the original standalone Save-as-Preset menu,
and continuation being invoked only when native creation succeeds. Full final
qualification, installed-wheel work, and Linux/Windows CI remain future gates.
