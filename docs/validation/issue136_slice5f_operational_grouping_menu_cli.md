# Concord #136 — Slice 5F: operational grouping menu and direct CLI

**Source baseline:** `c9776f6c487312a5b026b31904b7f9b8d02d8aa7` (Slice 5E).

## Teacher-facing path

Student groups → Saved class groupings → **Save existing Groups**.

The teacher explicitly selects a source Session (rather than guessing across Sessions), names the arrangement, reviews each Group and roster placement, acknowledges unassigned students when present, and confirms **SAVE**. The operation delegates to the existing Slice 5E read-only preview and immutable class-library writer. It does not touch Activity-native Group/Membership records, Roles, Scores, or publications.

Existing menu options 1–3 remain unchanged; the new option is 4. The direct Groups menu and plan menu already offer access to Saved class groupings, so no additional path duplication is necessary.

## Direct CLI

- `concord saved-grouping save-groups-preview --class-id ... --activity-id ... --session-id ... --actor-id ... --expected-snapshot ... --arrangement-id ... --name ...`
- `concord saved-grouping save-groups` takes the same inputs plus `--review-digest` and, for incomplete coverage, `--acknowledge-unresolved`.
- `--show-members` on preview reveals exact Core student IDs only on an explicitly requested local review. Default preview shows group counts and review digest without member IDs.

CLI presentation does not bypass the service's strict source-snapshot and Session-scope checks or reimplement Group projection. It preserves standard exit codes and the existing reviewed two-step command design.

## Targeted regressions

Synthetic menu dispatch, two-step confirmations, unresolved-student acknowledgment, cancel/no-write, CLI parsing, explicit snapshots/digests, privacy defaults, and exact service delegation. Existing Slice 5E Core-integrated operational Group tests already cover six Groups with 29 students, overlapping/ended Memberships, and cross-Activity reuse.

## Out of scope

CSV interoperability and final installed-wheel/release acceptance belong to later #136 slices. This slice changes no scoring/publication contracts.
