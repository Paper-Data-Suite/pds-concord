# Issue #136 — Slice 5G: optional saved-grouping CSV interchange

**Predecessor:** `1c53ca14686fb60262a6d03d8363cd6a07e9f524` (Slice 5F).

Teacher-facing saving and reuse remain first-class and do not require CSV.
The optional CLI interchange reuses Concord's strict `student_id,group`
parser. CSV import produces a **new teacher-owned class-scoped arrangement**,
not Groups, Memberships, a GroupPlan, Scores or an Activity modification.
CSV export produces a new private local file and never overwrites an existing
file. Explicit `--authorize-roster-export` is required to write student IDs.

## Contract

- `csv-import-preview` reads exact Core class roster and CSV, validates header,
  IDs, unknown/duplicate students, and produces a deterministic review digest.
- `csv-import` revalidates source CSV bytes and roster, checks digest and
  requires `--acknowledge-unresolved` whenever the file omits roster students.
  Group tokens become saved keys **and** labels; unrepresented groups cannot
  be inferred. A new immutable library identity is created using existing
  owner, scope and storage guards. No Activity records are written.
- `csv-export-preview` validates expected grouping revision/SHA and summarizes
  what a CSV would contain without printing individual student IDs or writing.
- `csv-export` rechecks revision and review digest, requires an explicit
  roster-export authorization flag, and uses exclusive new-file creation.
  It fails rather than overwrite a preexisting path. Exporting a grouping
  with no assigned students fails because an importable data row is required.
- This interchange **preserves exact assigned student IDs and group keys**.
  The two-column CSV cannot preserve separate friendly labels, descriptions,
  empty groups, or unresolved students. Those omissions are surfaced in preview.
  For lossless preservation use Concord's immutable class-grouping library.
- Raw CSV bytes and exported student IDs are never written to repository docs,
  CI output, debug logs, or Git. Export files belong in restricted local storage.

## Acceptance

Synthetic six-group/29-student CSV round-trip and independent library identity;
strict malformed/unknown/duplicate rejection; enrollment drift and missing
student acknowledgment; changed CSV/digest and stale revision protection;
privacy-minimized preview and explicit output authorization; no overwrite,
no hidden source Activity mutations; existing menu and CLI regressions preserved.
