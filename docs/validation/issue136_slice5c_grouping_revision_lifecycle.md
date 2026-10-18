# Concord #136 — Slice 5C: reviewed immutable grouping revisions

**Baseline:** `9164f4121d3ff9cd197a90dbc911fe57094a5bab` (Slice 5B).
**Branch:** `136-fix-standards-context-and-reusable-group-arrangements`.
**Target release:** v0.3.4; version unchanged here.

## Contract

`concord.workflows.class_group_arrangement_revision` exposes
`ChangeGroupingRequest`, `prepare_grouping_change`, and `change_grouping`.
An owning teacher can explicitly request one of:

- `rename`: change the human-readable name but preserve every group, student ID,
  unresolved ID, and existing Activity.
- `replace_from_plan`: review an exact **editable** source Activity GroupPlan and
  save its group labels, descriptions, and Core student IDs as the next revision.
  This requires an exact source Activity snapshot and current matching Core roster.
- `retire`: append a terminal revision without deleting any prior revision or
  changing any Activity; retired arrangements cannot be selected for reuse.

Each operation has a **read-only preview** and a separate committed write. The
preview binds the owner, original immutable SHA-256, expected revision, chosen
operation, new name, source identifiers/snapshot when relevant, new roster,
explicitly unresolved students, and all placements into a deterministic
`review_digest`. The write repeats all checks, requires that exact digest,
then delegates to `append_arrangement_revision`'s locked compare-and-swap.

**No-op revisions** and unauthorized teachers are rejected before committing.
The previous revision remains intact and readable from its numbered file.
Existing Activity Groups/Memberships, Scores, Artifacts, publications, and
GroupPlans are never changed by this service. No student names appear in
machine-readable output or test fixtures.

### Core roster drift distinction

`append_arrangement_revision` now checks the **current** Core roster only if
saved group assignments, the captured roster, or unresolved-student choices
change. Pure renaming or retirement retains the original frozen roster and is
allowed even when enrollment has changed. Reusing that historical arrangement
still requires the separately reviewed target-roster reconciliation. This
avoids making an outdated saved arrangement impossible to retire.

### Boundaries and next steps

This slice adds service-level revision support, not UI or CLI exposure. The
existing saved-grouping menu and direct-CLI read and reuse contracts remain
unchanged. The following slice can expose **Rename**, **Save new revision**,
**Retire**, and **Revision history** through existing teacher and direct-CLI
surfaces, without a competing storage writer.

Gate: exact branch/remote HEAD and clean-tree guards, focused Slice 5C/Slice 3/
Slice 4 tests, Ruff, strict mypy, pip check, staged whitespace, then automatic
commit/push only after all gates pass. Full suite runs at the final release
candidate, not again for unchanged slices.
