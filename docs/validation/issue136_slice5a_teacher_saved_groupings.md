# Concord #136 — Slice 5A: Teacher-menu saved grouping workflow

**Base:** `72cca482a33ce1f2af219bb32a99ea261b83a3eb` (Slice 4).
**Target:** v0.3.4; no version bump in this slice.

## Teacher outcome

An authorized teacher can enter **Student groups → Saved class groupings** (also available via **Plan groups → Saved class groupings** or the direct Group surface). Existing numbered options are unchanged.

- **Save current grouping:** choose an editable draft/previewed GroupPlan, enter a readable name (identifier defaults automatically), inspect the exact member placement, confirm SAVE. Delegates to the Slice 4 reviewed save service, which persists a distinct class/year/owner-bound immutable revision. No Activity Group, Membership, Score or evidence writes occur.
- **Use saved grouping:** select a named active grouping from the same class and authorized teacher; see the saved placement; choose a new Activity GroupPlan name; explicitly acknowledge any departed students or existing target plans; resolve only *new/previously-unresolved* students by placement or explicit unresolved; inspect the complete proposed placement, confirm CREATE. Delegates to the Slice 4 reviewed reuse service with the exact review digest, current Activity snapshot, roster, and Slice 2 Core Standards Library context. The result is a fresh editable draft, not canonical Groups.
- **Manage saved groupings:** browse an owner-restricted, class-specific list with names, status, revision and group counts; open an individual grouping for authorized membership review. Does **not** currently rename, revise, retire, or show history; those are reserved for subsequent slices.
- Within an editable GroupPlan, choose the newly appended **Save current grouping** option. For a manual plan, this is option 11, and for signal plans, option 12. Previously published choices are retained.

## Safeguards and remaining scope

No roster student is silently assigned or dropped. There is one final CREATE review for normal same-roster reuse, not per-student confirmations; when the roster actually changed, an explicit placement choice is needed only for each affected new or previously unresolved student. Departed IDs and preexisting plans are acknowledged before materialization. The service checks again before canonical GroupPlan write and refuses a stale digest/snapshot or newly changed roster. Teacher-readable names are shown only in detailed authorized review, never in general library listings or CI fixtures.

**Not yet in Slice 5A:** direct CLI commands, storage revision management (rename/revise/retire), saving from already-applied operational Groups with effective-context disambiguation, CSV import/export for saved library, and installed-wheel/release acceptance. Those remain required for issue #136 and will be implemented in later slices.

Gate: focused menu/legacy tests, Ruff, strict mypy on touched production code, pip check, staged diff integrity, guarded push. No full-suite rerun in a slice.
