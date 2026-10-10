# Issue #129 — publication and reporting qualification

## Purpose

Slice 6 qualifies the corrected Core Standards identity boundary through real
Concord persistence, publication, public reading, and teacher reporting while
running on the Core 0.6.5 source contract adopted earlier in Issue #129.

No manifest schema or reader API changes are introduced here.

## Qualified producer path

The acceptance fixture uses identities whose durable values deliberately differ
from the teacher-facing Standard code:

```text
profile_id:
    njsls-ela:profile.2023:11-12

standard_id:
    njsls-ela:2023:rl-ts-11-12-4

code:
    RL.TS.11-12.4

short_name:
    Analyze Text Structure
```

The test exercises:

```text
Core StandardsLibrary
-> Concord Activity persistence
-> standard-backed Criterion Set / Criterion
-> standard-backed Score
-> Core Academic Work Registration
-> Concord Academic Result Manifest generation
-> Core Publication Record publication/compatibility
-> concord_academic_result_reader_v1 readback
```

The exact durable Profile/Standard identities must survive every machine-facing
stage unchanged.

## Reporting boundary

Activity Score Analysis is separately qualified with the same persisted state.

Machine-readable report data retains:

```text
standard_id = njsls-ela:2023:rl-ts-11-12-4
```

while display metadata carries:

```text
standard_label      = RL.TS.11-12.4
standard_code       = RL.TS.11-12.4
standard_short_name = Analyze Text Structure
```

CSV likewise keeps the durable `standard_id` in its dedicated column and uses
the code only as the display label.

The ordinary PDF presentation uses:

```text
RL.TS.11-12.4 — Analyze Text Structure
```

and no longer presents a raw `Standard ID:` line as the ordinary teacher label.

This is intentional separation, not duplication drift:

```text
durable identity -> machine relationships / publication / reader
Core display metadata -> teacher-facing depiction
```

## Compatibility result

The published Core Publication Record remains compatible under the Concord
producer profile, advertises `criterion_scores` and `standards_ratings`, and
resolves exactly to:

```text
distribution = pds-concord
manifest     = concord_academic_result_manifest_v1
reader       = concord_academic_result_reader_v1
```

Exact package-version provenance remains separate and will be qualified in the
later installed-wheel slice.
