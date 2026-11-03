# Concord #145 — Slice 4B: existing rubric management and immutable revision

## Qualified prerequisite

- Branch: `145-teacher-first-criterion-sets-and-saved-assessment-setup`.
- HEAD: `217162b7ee7dbf7555030782cc080fe54032966a` (Slices 0/1–3 checkpoint).
- Qualified, still-uncommitted Slice 4A cumulative tree:
  `548dcc0b2a93a9b527dcd6e1e9f9eabc6dd6784b`.
- Published Core interface: Core v0.6.6. The Git HEAD is not a substitute for the
  installed package or future Core teacher-interface contracts.

## Changes

- Teacher menu option 3: guided revision of one **current lineage head**.
  The existing `revise_criterion_set` workflow remains the only write service.
  New Set and child Criterion identities are generated; predecessor IDs,
  lineage/history, selected Set revisions, and historical Score records remain intact.
- Teacher menu option 4: select one exact existing current or historical Set
  revision. The existing `select_activity_criterion_sets` service remains the
  only Activity selection write service. Prior selected IDs retain their order.
- Advanced revision and multiselection remain accessible as options 8 and 9.
  No changes to published direct CLI syntax, models, or record schemas.
- Existing immutable Criterion content is seeded into a **zero-write** draft.
  A truly unchanged draft is a no-op, including legacy mixed Set-kind metadata.
- All writes require explicit confirmation and fresh authoritative Activity
  snapshot checks; revision additionally requires that the original is still
  a current head. Service exceptions may follow a durable commit. The menu
  re-reads before reporting success and otherwise says the outcome is unknown
  or not verified; it never blindly retries or creates a duplicate.
- A revised Set is **not** automatically selected. The teacher explicitly
  selects the new revision separately. A previously selected historical
  revision remains selected, including where historical Scores exist.

## Cross-repository boundaries

- Core #235/#242 retain shared teacher-interface and classroom authority.
  Core Standards identity remains unchanged; the guided successor is validated
  against the canonical Core Standards library and Activity Focus at write time.
- Suite #49/#51 own launch/compatibility and suite-wide experience adoption.
  No Suite routing, installation, dependency pin, or conformance claim changes.
- Concord #143 owns native-to-preset correctness; no implicit preset creation.
  Concord #144 owns typed Scales; this slice preserves exact native Scale IDs.
- Score record history, grouping, grades, student rosters, evidence, and
  publication remain unchanged. All tests use synthetic actor/class IDs.

## Qualification

Before mirroring new files, the runner must verify both archives, the published
Core wheel, unchanged remote checkpoint, exact original Slice 4A cumulative
working tree, frozen #140 audit file, exact reconstructed 4A candidate tree,
patch anchors, changed-file inventory, Ruff, strict mypy, and focused pytest.
No automatic staging/commit/push/PR/merge/release or classroom-data access.
