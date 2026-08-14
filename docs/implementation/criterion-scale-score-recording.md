# Criterion, Scale, and Score Recording

**Status:** Implemented for issue #30 on the v0.2.0 development line.

## Purpose

Concord records teacher-approved scoring state without collapsing evidence,
Review, Moderation, Score, Grade, publication, or reporting into one record.

Issue #30 activates and hardens the native:

```text
CriterionSet
Criterion
ScoringScale
ScoringScaleLevel
ScoreRecord
ScoreEvidenceLink
ScoreTargetReference
EvidenceReference
EvidenceLocator
StatusReason
CorrectionRecord
```

contracts.

The conceptual boundary is:

```text
Evidence
    -> optional Review
    -> optional/required Moderation
    -> optional teacher-approved Score
    -> optional Concord publication (#31)
    -> optional Meridian policy/reporting
```

This is not an automatic pipeline. Evidence does not imply a Score. Review does
not imply a Score. Accepted Moderation does not imply a Score. Concord does not
calculate Grades.

## Criterion Sets and Criteria

A `CriterionSet` is one immutable revision of an ordered Criterion collection.
Creation commits the Set and its complete member list atomically.

A successor Set:

- receives a new `criterion_set_id`;
- preserves `lineage_id`;
- advances `revision`;
- explicitly supersedes the current lineage head;
- preserves the predecessor; and
- atomically includes the complete revised Criterion collection.

Current Set state derives from explicit supersession rather than timestamps,
IDs, filesystem order, or maximum revision heuristics. Branches, cycles,
missing/self predecessors, duplicate current heads, lineage changes, and
non-advancing revisions are invalid.

`scope=reusable` is semantic metadata in v0.2.0. Issue #30 does not create a
cross-Activity Criterion library, catalog, or storage root.

Criteria remain either:

```text
standard_backed
local
```

A standard-backed Criterion governs exactly one Core standard. When used by an
Activity, that standard must resolve through Core, fit the Activity standards
profile, and be one of the Activity Focus Standards.

A local Criterion has no governing standard. Its optional
`alignment_standard_ids` are instructional alignments only and never convert a
local Score into a standards result.

Supported target kinds remain explicit:

```text
core_student
concord_group
concord_session
concord_activity
concord_artifact_instance
```

## Activity Criterion-Set selection

The teacher explicitly selects exact Criterion Set revisions through:

```text
Activity.criterion_set_ids
```

A Score follows the exact path:

```text
ScoreRecord
    -> Criterion
    -> CriterionSet
    -> Activity.criterion_set_ids
```

Matching a Focus Standard is not enough. An arbitrary unselected Criterion is
invalid even when its standard happens to match.

Selecting a newer Set revision does not rewrite historical Scores. Exact Set
revisions required by existing Scores remain selected/resolvable.

## Scoring Scales

A `ScoringScale` is one immutable native Scale revision. Supported types are:

```text
numeric
ordinal
categorical
binary
teacher_defined
```

Each `ScoringScaleLevel` preserves its exact JSON scalar value, label, meaning,
optional position, and optional description.

Value identity is type-sensitive:

```text
1 != 1.0 != "1" != true
```

Concord never converts native Scale values to percentages, points, Grades, or a
universal proficiency scale.

Type coherence is enforced:

- numeric values are finite integers/floats and never bool;
- ordinal levels have positive unique positions;
- binary Scales contain exactly two distinct typed values;
- categorical/teacher-defined values remain exact and unique.

A revised Scale receives a new `scoring_scale_id`, preserves lineage, advances
revision, and explicitly supersedes the current lineage head. Historical Scores
continue to name the exact Scale revision actually used.

`Criterion.default_scoring_scale_id` is convenience metadata only. Score entry
still requires an exact Scale selection.

## Score Records

A `ScoreRecord` is one teacher-approved judgment:

```text
one Activity
+ one explicit target
+ one Criterion
+ one exact Scale revision
+ one disposition
+ one basis
```

Score creation is always deliberate. Artifact creation, Artifact Author,
Artifact Subject, Group Membership, Role, Responsibility, route identity,
Review, Moderation, and evidence existence do not create or prepopulate a Score.

### Explicit targets

Core-student targets require:

```text
target_kind = core_student
owning_system = core
```

and exact membership in the Core-owned class roster.

Concord targets require `owning_system=concord` and same-Activity existence.

Concord never infers the target from Author, Subject, Membership, Role,
Responsibility, route/QR identity, Review, Moderation scope, or evidence Subject
context.

A Group Score is only a Group Score. It never creates, copies, or populates
individual student Scores.

### Score kind and Activity orientation

A standard-backed Score requires:

```text
Criterion.criterion_kind = standard_backed
Score.standard_id = Criterion.standard_id
standard_id in Activity.focus_standard_ids
Activity.scoring_orientation in {standards_based, mixed}
```

A local Score requires:

```text
Criterion.criterion_kind = local
Score.standard_id = absent
Activity.scoring_orientation in {local_criteria_only, mixed}
```

`scoring_orientation=evidence_only` rejects Score writes.

## Dispositions and Status Reasons

Supported dispositions are:

```text
scored
insufficient_evidence
absent
excused
not_observed
not_applicable
deferred
```

A scored disposition requires one exact native Scale value and
`moderation_complete=true`.

Every non-score disposition has no value. The teacher-facing workflows require
an explicit matching `StatusReason`. The universal disposition is kept separate
from optional contextual notes.

Concord never substitutes zero or the lowest Scale level for an exceptional
state.

Sensitive medical, disability, disciplinary, counseling, or family details
should not be copied into Score records.

## Score basis

Supported bases are:

```text
linked_evidence
professional_judgment
mixed_basis
```

`linked_evidence` requires one or more active Score Evidence Links.

`professional_judgment` requires zero active links and a nonempty Score
rationale. Concord does not fabricate a `teacher_rationale` Evidence Reference.

`mixed_basis` requires both active evidence links and a nonempty professional
judgment rationale.

## Atomic Score creation

A new Score and its complete initial evidence-link set are committed in one
guarded batch:

```text
ScoreRecord
+ zero-to-many ScoreEvidenceLink records
```

There is no valid intermediate state where a linked Score is committed before
its required links.

Every write uses exact `class_id`, `activity_id`, actor provenance, and expected
snapshot revision. Concord never force-writes, silently merges, or retries a
stale mutation against a newer snapshot.

## Score Evidence Links

A `ScoreEvidenceLink` is a first-class durable association between one exact
Score revision and one exact evidence source.

It records:

- exact `EvidenceReference`;
- optional human-readable `EvidenceLocator`;
- explicit Subject context;
- relevance description;
- descriptive significance;
- optional exact Moderation Record; and
- explicit link supersession when administratively corrected.

A link does not copy evidence, calculate the Score, imply numeric weighting,
imply that more evidence means a higher Score, or create another Score.

Current active link state derives from explicit link supersession. Historical
links remain attached to the exact historical Score revision they supported.

## Evidence sources and immutable lineage

Issue #30 supports at least:

```text
concord artifact_instance
concord artifact_page
scoreform_result
quillan_response
external_record
```

Concord-owned Artifact/Page evidence must exist in the same Activity.

External evidence preserves exact immutable lineage with
`immutable_source_version` and/or an exact Core Publication reference. Mutable
aliases such as `latest`, `current`, and `mutable` are rejected.

Concord does not import ScoreForm, Quillan, Meridian, or other sibling packages
to interpret their private storage.

## Review and Moderation handoff

Effective Moderation is required when either:

```text
EvidenceReference.moderation_requirement == required
```

or the current Artifact Review requires Moderation.

A current scored use that requires Moderation must identify an exact current,
applicable decision whose status is accepted/accepted-with-qualification and
whose permitted use allows the Score target.

A caller cannot bypass a Review requirement by reconstructing an otherwise
equivalent Evidence Reference with `moderation_requirement=not_required`.

A non-score `deferred` record may preserve its evidence relationship while
Moderation is still pending. It remains valueless with
`moderation_complete=false`. A later scored successor must revalidate the
current Moderation state.

Historical Scores preserve the exact historical Moderation they actually used;
newer Moderation state does not rewrite history.

## Score revisions and correction history

A Score successor:

- receives a new `score_record_id`;
- explicitly names its predecessor;
- uses a non-backward `scored_at`;
- supplies a completely fresh evidence-link set; and
- atomically creates `CorrectionRecord(correction_type="score_revision")`.

Predecessor links are never reparented or silently carried forward.

Multiple independent current Score lineages may exist for the same target and
Criterion. Concord does not choose a universal latest, highest, or most recent
Score.

## Direct CLI

The direct commands are:

```text
concord criterion-set create
concord criterion-set list
concord criterion-set show
concord criterion-set revise
concord criterion-set select

concord scale create
concord scale list
concord scale show
concord scale revise

concord score add
concord score list
concord score show
concord score replace
```

Criterion Set and Scale commands consume narrow JSON definition files rather
than generic canonical-record blobs.

Score entry uses `--value-json` so scalar identity remains type-sensitive.
Evidence Links use a narrow JSON array supplied before the atomic Score commit.

Broad Score listing omits private rationale and evidence free text. Exact
`score show` displays the selected Score revision and its exact links.

All direct commands preserve the standard exit-code contract:

```text
0 success
1 validation/read/write/integrity failure
2 command-line usage error
3 expected-revision or lock conflict
4 structured partial success
```

## Teacher menu

An opened Activity now includes:

```text
8. Scoring
```

The Scoring menu provides:

- Criterion Set create/browse/revise/select;
- Scoring Scale create/browse/revise;
- explicit Score recording;
- Score browsing; and
- explicit Score revision.

Selectors use the shared ten-row pagination and H/B/M/Q navigation.

The teacher deliberately selects Criterion, target, exact Scale revision,
optional Session context, disposition, basis, exact Scale value when scored,
evidence links, and applicable Moderation. The UI never recommends or infers a
Score value from evidence.

Score creation requires the literal confirmation:

```text
SCORE
```

A Group target displays:

```text
GROUP SCORE WARNING:
This Score applies only to the Group.
It creates no individual student Scores.
```

Stale writes use the existing Reload workflow and are never force-overwritten.

## Pure graph integrity

Pure graph validation covers:

- Criterion Set and Scale supersession lineage/revision integrity;
- unique current definition heads;
- Activity-selected Criterion enforcement;
- Score target ownership and same-Activity context;
- Criterion kind, governing standard, Focus Standard, and orientation;
- exact Scale value membership;
- disposition/value coherence;
- basis/evidence-link cardinality;
- duplicate evidence-source rejection;
- active-link state from explicit link supersession;
- Score Evidence Link parent continuity;
- #29 Moderation applicability/current-use rules;
- Score successor time ordering; and
- exact `score_revision` correction linkage.

Validation reports contradictions. It does not repair or reinterpret teacher
judgments.

## Native fixture

The integrated synthetic standards Activity fixture demonstrates that these
identities remain independent:

```text
Artifact Author
Artifact Subject
route target
Score target
Criterion
Scale
evidence Subject scope
Moderation scope
Score
```

It includes:

- a standard-backed individual Score with moderated Artifact evidence;
- a Group/local professional-judgment Score;
- a non-score Group disposition;
- a Score Evidence Link; and
- a corrected Score successor with preserved predecessor/correction history.

The Group Score creates no student Scores. Fixture data is synthetic and
PII-free.

## Installed-wheel acceptance

The isolated installed-wheel smoke now continues the existing:

```text
Activity
-> Artifact
-> PDS2 route
-> retained source / Scan Reference
-> Author / Subject
-> Review
-> Moderation
```

path through:

```text
local Scoring Scale
-> local Criterion Set
-> explicit Activity Set selection
-> explicit Group Score
-> canonical reload
```

The smoke proves that the installed package persists the Score, keeps the target
as the Group, creates no individual Scores, creates no Score Evidence Links for
professional judgment, and still declares no Concord publication-producer entry
point.

## Ownership boundary and #31 handoff

Core remains authoritative for workspace/class/roster identities, standards,
PDS2 routing, retained scans, Academic Work Registration, and Publication
Records.

Concord owns Criterion Sets, Criteria, Scoring Scales, Scores, Score Evidence
Links, Review, Moderation, and native history.

Meridian owns evidence/attempt selection policy, scale mapping, proficiency,
Grade items, Academic Period membership, Grade calculation, weighting,
derived-result overrides, and reporting.

Issue #30 deliberately does **not** publish Concord academic results. Issue #31
will project the already teacher-approved canonical Concord scoring state into
the versioned Concord Academic Result Manifest without rewriting the native
history implemented here.
