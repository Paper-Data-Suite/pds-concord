# Concord #145 — Slice 5: saved assessments and typed Scale recommendation

## Qualified prerequisite and repository boundary

- Concord branch `145-teacher-first-criterion-sets-and-saved-assessment-setup`, HEAD `3e7b6c28db828c884641ca9456f2a3b20247887e`, committed Git tree `f7c8e1cc319706cc92cb18f55811df1345ae6b2e`.
- Published Core v0.6.6; no dependency upgrade or use of unshipped shared Core teacher-menu primitives.
- Open Core #235/#238–#244 own teacher-experience primitives, private Notes, roster custody, and reusable workspace management; this slice creates none.
- Open Suite #49/#51 own launcher compatibility, release qualifications and shared Teacher Experience Specification integration; this slice creates no Suite entrypoint or compatibility claim.
- Concord #143 already owns `prepare_criterion_set_preset_from_activity`, `save_criterion_set_preset_from_activity`, and exact saved-assessment materialization. This slice uses them without creating a parallel store, schema, or permission model.

## Source semantics and independently durable writes

1. A native Activity-owned Criterion Set (`scope='reusable'` or otherwise) is **not** a workspace reusable preset.
2. The guided menu's option **Save this assessment for another class** selects one exact existing native Set revision, including historical lineage revisions, with its selection/current status shown. This never modifies selected Activity Criterion Sets.
3. A single native default Scale may be recommended only when an already-saved active Scale-preset revision matches the source Scale exactly: canonical type, *typed* value of every ordered level, label, meaning, ordinal position, description, intended use, and aggregation guidance. No other Scale is offered as an equivalent mapping.
4. No default Scale means no recommendation required. Multiple *distinct* native default Scales cannot be encoded through the existing single recommended-Scale-preset contract; teacher review explicitly states the omission. A single default without an exact saved match is omitted, with a next action to separately save that native Scale via the existing Scale-preset workflow.
5. Saving the rubric creates a new reusable Criterion Set preset through the existing prepare/review-digest/save workflow. It does **not** configure a target class, copy native IDs or provenance, propagate Scores, or derive grades.
6. Confirmation `SAVE` is independent from the prior CREATE, USE, REVISE, or optional Scoring Scale preset save operations; a declined confirmation changes nothing.
7. After an interrupted save receipt, the menu attempts an exact preset read. An unknown outcome is labeled **unknown**, with the generated preset ID and a warning not to create a duplicate blindly; no automatic retry occurs. After a positive save, failure to reread is disclosed as **verification unavailable**, not falsely reported as a failed write.
8. The source Activity's snapshot/ordered selection is checked before review and again before save. The preset service additionally checks its review digest and selected native source. A concurrent change between that final menu reread and the service's durable write is not fully fenced by the service's present `enforce_expected_snapshot=False` save path; qualify that race and evaluate a service-level hardening in the adversarial Slice 6, rather than overclaiming that this menu alone makes the cross-store operation atomic.
9. Creation, Create-and-use, existing selection and revision success receipts point directly to option 5 for a separate saved-preset operation. Failure/unknown receipts do not trigger a save.

## Slice 5 bounded scope

- Add `concord/criterion_preset_guidance.py` (pure type-sensitive mapping/receipt presentation).
- Modify `concord/menu_scoring.py` only in its existing reusable-preset selection/save route, relevant success receipts and option 5's label; Advanced/CLI handlers, canonical Scoring Scale and Criterion models, and reusable-preset storage untouched.
- Add `tests/test_issue145_slice5_saved_assessment.py` with synthetic exact typed-level comparisons and menu save/decline/stale/unknown behavior.
- Next: Slice 6 qualifies two-class roundtrip and full installed producer boundaries. Release, tag, PR merge and class-data access remain forbidden here.
