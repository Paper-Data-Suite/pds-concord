# Issue #129 Native Standards Identity and Depiction Audit

## Scope

This audit covers native Concord fields that carry authoritative Core Standards
identity and the teacher-facing surfaces already inspected for Standards
depiction.

It does not change the public reader contract or Core dependency floor.

## Confirmed native identity fields

Before Issue #129 Slice 2, these native fields incorrectly used Concord's generic
routing/path identifier helpers:

- `Activity.standards_profile_id`
- `Activity.focus_standard_ids`
- `CriterionSet.standards_profile_id`
- `Criterion.standard_id`
- `Criterion.alignment_standard_ids`
- `ScoreRecord.standard_id`

Slice 2 moves only those fields to the dedicated Core Standards durable-identity
boundary in `concord.models.common`.

Unrelated record, route, Criterion, Score, Activity, Scale, Session, and contract
identifiers continue to use generic identifier validation.

## Standards authority after model construction

`concord.model_validation.validate_core_standards(...)` already compares the
native durable IDs directly against a caller-supplied Core `StandardsLibrary` and
uses Core `resolve_profile_standard_selection(...)` for Activity focus selection.

The model correction therefore removes the premature routing-grammar rejection;
it does not replace Core Standards-library validation.

## Persistence boundary

Concord's canonical record codec (`record_to_dict` / `record_from_dict`) carries
the durable Standards strings directly. Slice 2 regression coverage proves
Activity, Criterion Set, Criterion, and Score records retain the normalized
durable identities across that exact JSON-native conversion boundary.

Full workspace commit/reload qualification with a genuine Core Standards Library
remains a later Issue #129 slice.

## Teacher-facing depiction findings

The audit found three relevant presentation patterns.

### Activity detail

Routine Activity detail currently reports only the count of Focus Standards.
It does not replace durable identities with display labels and therefore does
not create an identity corruption risk.

### Activity copy review

The copy-review surface currently prints:

```text
Standards profile: <profile_id>
Focus Standards (ordered):
  1. <standard_id>
```

This is a teacher-facing depiction gap. When a Core Standards Library is
available, Slice 3 should prefer authoritative Profile title and Standard
`code` / `short_name`, while retaining durable identity only for technical or
fallback presentation.

### Activity Score Analysis

`activity_score_analysis._standard_display(...)` already resolves a matching
Core `StandardDefinition` and retains all three concepts separately:

- durable `standard_id`;
- `standard_code`;
- `standard_short_name`.

Its current primary `standard_label` is the Core `code`, with durable ID as the
fallback when no definition is available.

The PDF report still has a technical line:

```text
Standard ID: <standard_id>
```

and its Standards table uses only the primary display label. Slice 3 should
review that surface for ordinary teacher-facing depiction such as:

```text
RL.TS.11-12.4 — Analyze Text Structure
```

without replacing or mutating the durable identity in analysis data.

## Governing boundary for the next slice

Machine/native state:

```text
standard_id / profile_id
```

Teacher-facing presentation, when Core metadata is available:

```text
code / short_name / profile title
```

Fallback when metadata is unavailable:

```text
exact durable identity
```

No display-derived value becomes a durable key.
## Slice 3 depiction resolution

Issue #129 Slice 3 resolves the bounded teacher-facing presentation gaps found
by this audit without changing durable or public machine contracts.

A shared read-only `concord.standards_display` layer now keeps these concepts
separate:

```text
durable identity
    StandardDefinition.standard_id / StandardsProfile.profile_id

teacher depiction
    StandardDefinition.code + short_name / StandardsProfile.title

fallback
    exact durable identity
```

The presentation layer is used by:

- Activity copy review in the menu;
- direct CLI Activity copy preview;
- direct CLI Activity detail when Core Standards metadata is available;
- Activity Score Analysis PDF ordinary presentation.

Activity Score Analysis JSON/CSV continues to retain the durable `standard_id`
alongside its display metadata. `concord_academic_result_manifest_v1` is
unchanged.

No display label is written back into native Activity, Criterion, Score, or
Standards Profile identity fields.
