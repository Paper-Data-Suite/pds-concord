# Issue #134 — Slice 3A: teacher-facing historical identity

**Source baseline:** `f56aaf1ee90daa94959ae1b6217e17a86dfc3deb`

**Scope:** Read-only teacher presentation. No canonical evidence, packet,
publication, review, moderation, scoring, storage, or viewer behavior is changed.

## Completed in this part

- Reusable Template and Packet pickers use names and current-version selection
  state rather than their technical IDs; identical labels have explicitly
  nonchronological, stable ordinal disambiguators.
- Template/Packet detail and version history expose human labels, revision
  sequences, version status, and the **selected current version** separately
  from the **latest revision**. Publication-like currentness is not inferred
  from revision order.
- Packet generation pickers distinguish planned generation dates from actual
  created-at timestamps, including repeated runs with the same planned date.
- Packet Instance browsing and inspection use the existing authorized
  participant/group audience projector rather than raw target keys, instance
  IDs, output relative paths, and digests. Creation time is labeled as such.
- Publication history identifies a withdrawn publication, a current selectable
  publication, structural head, and historical entries by canonical identity.
  A historical, nonwithdrawn publication is not mislabeled as current.

## Still required under Slice 3B

- Artifact Page/attribution author and subject detail, Review/Moderation/Score
  histories and confirmations, Group/Session/member navigation, routine Score
  targets, Preset forms, and advanced Template/Packet editing confirmations.
- Complete menu inventory resolution, privacy/consistency and latency review,
  plus installed and physical Windows viewer qualification in Slices 4–5.

## Chronology and authority

`generation_date` is a planned calendar date. `created_at` is the actual
record creation instant. Display conversion requires an aware timestamp;
missing or naive timestamps are never silently treated as local time.
Duplicate menu names get ordinal **display** labels, not creation ranks.
No publication or library version is called current from maximum revision.

## Validation

One focused pytest gate covering newly introduced presentation contracts and
existing Template, Packet, Packet generation and publication menu behavior.
Ruff, strict MyPy and exact staged-file Git checks run before any commit.
The full-suite/release qualification is reserved for Slice 5.
