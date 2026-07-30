# ADR 0014: Make Standards-Based Scoring the Primary Concord Scoring Model

**Status:** Accepted
**Date:** July 22, 2026
**Amended:** July 29, 2026 — cross-references ADR 0015, Core publication, and `pds-meridian`
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Paper Data Suite is predominantly a standards-based assessment and grading system.

Its assignment modules collect different kinds of evidence:

* `pds-scoreform` processes machine-readable selected-response evidence;
* `pds-quillan` supports teacher review of written-response evidence;
* `pds-concord` supports collaborative evidence from discussions, laboratories, group projects, design activities, and other collaborative work;
* and `pds-meridian` applies explicit grading and reporting policy to approved results across assignments, modules, courses, Academic Periods, and time.

Since this ADR was accepted, Meridian has established the downstream grading and reporting boundary, and Core has established typed Academic Work Registration and immutable publication-registry contracts. ADR 0015 defines how Concord publishes versioned Academic Result Manifests through that Core registry.

Concord must therefore preserve enough standards-specific meaning for Meridian to determine:

* which standard a teacher evaluated;
* which student, Group, or other target received the judgment;
* which Activity and optional Session supplied the context;
* which scale revision governed the judgment;
* which evidence supported it;
* whether required Moderation was completed;
* whether the teacher made a scored judgment or recorded a non-score disposition;
* and whether a later judgment superseded an earlier one.

Concord’s existing foundational documents already establish several necessary pieces:

* PDS Core owns shared standards definitions, standards profiles, durable `standard_id` references, and module-neutral standards validation;
* Concord may select Criteria and Criterion Sets;
* a Score Record represents one teacher-approved judgment about one Criterion for one target;
* Score Records may cite several evidence sources;
* Review, Moderation, Scoring, Grading, and Reporting are separate concepts;
* missing or exceptional evidence states must not become low Scores automatically;
* and grading and cross-module reporting remain outside Concord.

Those decisions are necessary but not sufficient to establish standards-based scoring.

The current generic model can be summarized as:

```text
evidence
    -> Criterion
    -> teacher-approved Score
```

A Criterion may carry one or more optional standards references, but the model does not yet define whether those references mean:

* the Criterion directly evaluates one standard;
* the Criterion evaluates several standards simultaneously;
* the standards are contextual alignments only;
* the Criterion is local to the Activity;
* or the resulting Score may be treated as a direct standards result.

That ambiguity would force Meridian to infer standards meaning from generic Criterion metadata.

For example, consider this Criterion:

```text
Uses evidence while responding to peers
```

Suppose it references:

```text
njsls-ela:SL.PE.9-10.1
njsls-ela:RL.CR.9-10.1
```

A Score of `3` against that Criterion would not reveal whether:

* both standards received a rating of `3`;
* only the speaking-and-listening standard was directly evaluated;
* the reading standard was supporting context;
* the Score was holistic and cannot be separated;
* or the standards were merely attached for instructional alignment.

Meridian must not guess.

Paper Data Suite’s existing modules demonstrate two compatible standards-integration patterns.

### Quillan pattern

Quillan makes Focus Standards the organizing structure for teacher review:

```text
student evidence
    -> review unit
    -> Focus Standard
    -> teacher judgment
    -> feedback and assignment-local reporting
```

Quillan assignments explicitly select:

* one standards profile;
* one ordered set of Focus Standards;
* and one standards-rating scale.

Its teacher-confirmed overall Focus Standard ratings are direct standards-based judgments.

### ScoreForm pattern

ScoreForm attaches durable standards references to individual questions.

The selected-response score remains governed by the answer key. Standards metadata does not change whether an answer is correct.

Question-level standards alignment and question-level response results can later provide standards-relevant evidence, but ScoreForm does not automatically determine longitudinal mastery, course Grades, or cross-module standards results.

### Concord’s distinct need

Concord should not copy either module’s complete workflow.

Concord’s distinctive domain includes:

* individual and Group targets;
* changing Group Membership;
* shared and individual evidence;
* Artifact Authors and Subjects;
* teacher and peer observation;
* Moderation;
* contribution evidence;
* collaborative process Criteria;
* Activity-specific local Criteria;
* and evidence that may concern several students, Groups, Sessions, or components.

Concord therefore needs a standards architecture that:

1. makes direct standards judgments unambiguous;
2. preserves Criterion-level scoring;
3. supports Group and individual targets;
4. retains legitimate local collaborative Criteria;
5. avoids forcing every Activity into standards scoring;
6. does not make standards alignment equivalent to mastery;
7. and provides a clean publication and Meridian-consumption boundary.

## Decision

Concord will use **standards-based scoring as its primary academic scoring model**.

Concord will be **predominantly standards-based but not standards-exclusive**.

Activities intended to produce academic performance judgments should normally select Focus Standards and use standard-backed Criteria.

Concord will continue to support:

* evidence-only Activities;
* local collaborative Criteria;
* Group-process Criteria;
* Activity-component Criteria;
* operational or procedural Criteria;
* and formative Activities that produce no standards Scores.

The central standards-based scoring relationship will be:

```text
collaborative evidence
    -> standard-backed Criterion
    -> teacher-approved Score
    -> Concord Academic Result Manifest revision
    -> Core Publication Record
    -> Meridian standards-based grading and reporting
```

For a direct standards judgment:

```text
one Score Record
    -> one immutable standard-backed Criterion
    -> exactly one governing standard_id
    -> exactly one Score target
    -> exactly one Scoring Scale revision
```

## Standards ownership

PDS Core remains authoritative for:

* shared standard definitions;
* durable `standard_id` values;
* standards profiles;
* durable `profile_id` values;
* standards-library storage;
* standards browsing and selection;
* profile-membership validation;
* standard display metadata;
* active, inactive, and deprecated status;
* and module-neutral standards reference validation.

Concord owns:

* selecting Focus Standards for an Activity;
* defining or selecting Concord Criteria;
* declaring whether a Criterion is standard-backed or local;
* selecting Concord Scoring Scales;
* recording teacher-approved Score Records;
* linking evidence to those Scores;
* applying Concord Review and Moderation requirements;
* producing immutable Concord Academic Result Manifest revisions containing standards-result and other valid Concord result projections;
* and presenting standards-based scoring workflows to the teacher.

Core additionally owns:

* Academic Work Registration identity and revision;
* immutable Publication Records;
* publication kinds and capabilities;
* manifest-path and digest validation;
* publication supersession and withdrawal;
* and the derived publication catalog.

Meridian owns:

* published-result eligibility;
* standards-evidence and attempt selection;
* proficiency calculation;
* Grade-item and Academic Period membership;
* Grade calculation;
* overrides of Meridian-derived results;
* and formal report snapshots and reports.

Concord must not:

* create a competing standards library;
* copy full standard definitions into Activity or Score records;
* use display codes as durable identities;
* silently substitute one standard for another;
* or mutate Core standards while creating or reviewing Concord records.

## Activity scoring orientation

Each Activity will declare its intended scoring orientation.

The initial semantic orientations are:

```text
evidence_only
standards_based
mixed
local_criteria_only
```

The exact serialized values belong to the conceptual and later persisted contracts, but these distinctions are required.

### `evidence_only`

The Activity collects, organizes, reviews, or moderates evidence without producing Concord Score Records.

Examples include:

* an unscored discussion map;
* a formative Group retrospective;
* a teacher observation collection used only for planning;
* or a collaborative record retained for later reference.

An evidence-only Activity does not require Focus Standards, Criteria, or a Scoring Scale.

### `standards_based`

The Activity’s scored judgments are direct judgments against selected Focus Standards.

A standards-based Activity must select:

* one `standards_profile_id`;
* one or more ordered `focus_standard_ids`;
* one or more standard-backed Criteria;
* and applicable Scoring Scale revisions.

Local unscored context records may still exist, but scored Criteria should ordinarily be standard-backed.

### `mixed`

The Activity uses both:

* direct standard-backed Criteria;
* and local Concord Criteria.

Examples include:

* a laboratory Activity that scores a science-practice standard and also records a local equipment-management Criterion;
* a seminar that scores speaking-and-listening standards and separately records an ungraded facilitation responsibility;
* or a programming project that scores computational-thinking standards while also evaluating a local handoff protocol.

A mixed Activity must select a standards profile and one or more Focus Standards.

### `local_criteria_only`

The Activity produces Score Records, but those Scores are not direct standards judgments.

Examples may include:

* a local procedural check;
* a school-specific team protocol;
* an extracurricular collaborative Activity;
* or a temporary Activity component whose Criteria are not intended for standards reporting.

Local-criteria scoring remains teacher-controlled and may later contribute to a Grade only through an explicit downstream policy.

It must not be presented as direct standards performance.

## Activity Focus Standards

An Activity using `standards_based` or `mixed` scoring must identify:

```text
standards_profile_id
focus_standard_ids
```

### `standards_profile_id`

The Activity’s `standards_profile_id` identifies the Core-owned standards profile from which its Focus Standards were selected.

Rules:

* it must be a durable Core `profile_id`;
* it must resolve through the active workspace standards library at creation and validation boundaries;
* Concord stores the reference but does not own the profile;
* and missing or inactive profile metadata must not cause silent mutation of the Activity.

### `focus_standard_ids`

The Activity’s `focus_standard_ids` identify the standards that the Activity is deliberately configured to evaluate.

Rules:

* the list must be nonempty for `standards_based` and `mixed` Activities;
* every entry must be a durable Core `standard_id`;
* duplicate IDs are invalid;
* every selected standard should belong to the selected profile;
* ordering is meaningful for teacher-facing scoring, publication, and Meridian workflows;
* and a selected Focus Standard does not by itself prove that the standard was taught, practiced, assessed, demonstrated, or mastered.

The Focus Standards define the Activity’s intended standards-scoring scope.

A standard becomes direct Concord performance evidence only through an explicit teacher-approved standard-backed Score Record or another later contract that deliberately defines a standards-result event.

## Criterion classifications

Every Criterion used for scoring will declare whether it is:

```text
standard_backed
local
```

The exact serialized field name and values belong to the conceptual data contract, but this distinction is mandatory.

## Standard-backed Criterion

A **standard-backed Criterion** defines how one selected standard will be judged in the Concord Activity context.

It has exactly one governing `standard_id`.

Conceptually:

```text
criterion_kind: standard_backed
standard_id: <one Core standard_id>
```

Examples include:

```text
Standard:
njsls-ela:SL.PE.9-10.1

Activity-specific Criterion:
Builds on peers’ ideas and responds substantively during collaborative discussion
```

```text
Standard:
ngss:HS-ETS1-3

Activity-specific Criterion:
Evaluates proposed solutions against relevant constraints and evidence
```

```text
Standard:
csta:2-AP-17

Activity-specific Criterion:
Provides useful documentation that supports collaborative program development
```

The Activity-specific Criterion may clarify what the selected standard looks like in:

* a seminar;
* a laboratory;
* a programming project;
* an engineering challenge;
* or another collaborative context.

It does not redefine the shared standard.

### Exactly one governing standard

A standard-backed Criterion must identify exactly one governing standard.

This preserves an unambiguous relationship:

```text
Score
    -> Criterion
    -> one standard_id
```

If the teacher intends to make direct judgments about two standards, Concord should ordinarily use:

* two Criteria;
* and two Score Records.

A user interface may display or enter those judgments together, but the persisted judgments remain separate.

### Multi-standard or holistic Criteria

A Criterion may describe a complex behavior aligned to several standards, but one Score against such a Criterion must not be treated as several direct standards ratings.

A multi-standard holistic Criterion must therefore be modeled as:

* a local Criterion with non-governing alignment references;
* several separate standard-backed Criteria;
* or another explicitly defined future composite contract.

Meridian must not split one holistic Score across several standards automatically.

### Focus Standard membership

When a standard-backed Criterion is used by an Activity:

* its `standard_id` must appear in the Activity’s `focus_standard_ids`;
* the standard should belong to the Activity’s selected standards profile;
* and any unresolved, inactive, or deprecated reference must be reported explicitly.

Historical Criteria and Scores remain preserved even if a standard later becomes inactive or deprecated.

## Local Criterion

A **local Criterion** evaluates an Activity-specific, procedural, organizational, or collaborative expectation that is not a direct standards rating.

Conceptually:

```text
criterion_kind: local
standard_id: absent
```

Examples include:

* returns shared materials to the agreed location;
* completes a designated equipment check;
* records a component handoff;
* follows a locally defined discussion protocol;
* maintains the Group’s version log;
* or completes an Activity-specific procedural responsibility.

A local Criterion may include optional alignment metadata such as:

```text
alignment_standard_ids
```

when the teacher wants to document instructional relevance.

Such alignment is non-governing.

A Score against a local Criterion must not be reported as a direct rating for any aligned standard unless the teacher separately creates a standard-backed Score.

## Criterion Sets

A Criterion Set may contain:

* only standard-backed Criteria;
* only local Criteria;
* or both.

A Criterion Set should identify its intended orientation and scope.

For example:

```text
Seminar Focus Standards
├── SL.PE.9-10.1 — Builds on peers’ ideas
├── SL.II.9-10.2 — Integrates information from discussion
└── RL.CR.9-10.1 — Uses relevant textual evidence
```

A mixed Criterion Set may also contain:

```text
Local seminar-process Criterion:
Performs the assigned observer rotation
```

The local Criterion remains distinguishable from the direct standards judgments.

Criterion Sets and Criteria used by Scores remain immutable under the existing historical-preservation decisions.

Changing:

* a governing standard;
* a Criterion definition;
* target applicability;
* scoring interpretation;
* or standard/local classification

requires a new Criterion revision or identity under the later finalized contract.

## Score Record semantics

The existing Score Record model remains:

> One teacher-approved judgment about one Criterion for one target in one defined Activity context using one exact Scoring Scale revision.

This ADR adds standards semantics to that model.

### Standard-backed Score

A Score against a standard-backed Criterion is a direct Concord judgment about the Criterion’s one governing standard.

It must preserve or expose unambiguously:

* `activity_id`;
* optional `session_id`;
* one Score target;
* one Criterion;
* one governing `standard_id`;
* one Scoring Scale revision;
* one Score disposition;
* one value when scored;
* scorer identity;
* scoring timestamp;
* applicable evidence links;
* required Moderation state;
* optional rationale;
* and correction or supersession history.

The later serialized contract may:

1. store `standard_id` directly on the Score Record as a historical snapshot;
2. resolve it through the immutable referenced Criterion;
3. or do both.

Whichever representation is chosen, the public contract must make the governing standard:

* unambiguous;
* reproducible;
* historically stable;
* and available without heuristic interpretation.

### Local Score

A Score against a local Criterion remains a valid Concord Score.

It must be identifiable as a local-criterion judgment and must not be interpreted as a direct standard rating.

ADR 0015 permits local Scores to appear in the broader Concord Academic Result Manifest so that an explicit conventional or hybrid Meridian policy may consider them. They remain excluded from the standards-specific projection and retain no governing `standard_id`.

### Score dispositions

The existing universal Score dispositions remain applicable:

```text
scored
insufficient_evidence
absent
excused
not_observed
not_applicable
deferred
```

Standards-based scoring does not alter the rule that exceptional states are not low Scores.

For a standard-backed Score:

* `scored` requires a valid value from the selected Scoring Scale;
* all non-score dispositions require no score value;
* zero or the lowest level must not be inferred from missing or exceptional evidence;
* and a later valid judgment may supersede an earlier non-score disposition while preserving history.

### Standards selection is not a Score

The following do not create a standards Score:

* selecting a Focus Standard;
* placing a Standard Reference on an Activity;
* printing a rubric that names a standard;
* generating an Artifact linked to a standard-backed Criterion;
* receiving a completed Artifact;
* reviewing evidence;
* approving evidence as readable;
* accepting evidence through Moderation;
* attaching a standard to an external ScoreForm question;
* or linking a Quillan assignment to the Activity.

A standards Score exists only when an authorized scorer records the teacher-approved criterion-level judgment.

## Scoring Scales

Concord will not impose one universal standards-rating scale.

A standards-based Activity may use an exact immutable Scoring Scale revision such as:

* Developing / Approaching / Meeting / Exceeding;
* Beginning / Progressing / Proficient / Advanced;
* a numeric ordinal scale;
* a binary demonstrated/not-demonstrated scale where appropriate;
* or another teacher- or organization-approved scale.

The Scoring Scale must preserve:

* permitted values;
* display labels;
* descriptions;
* ordering where applicable;
* revision identity;
* and historical reproducibility.

Meridian must not assume that similarly numbered scales are semantically equivalent.

For example:

```text
Concord Scale A:
1 = Developing
2 = Approaching
3 = Meeting
4 = Exceeding
```

is not automatically equivalent to:

```text
External Scale B:
1 = Beginning
2 = Developing
3 = Proficient
4 = Advanced
```

Cross-scale conversion, normalization, weighting, and mastery policies belong to explicit, versioned Meridian contracts.

## Evidence and standards Scores

The existing many-to-many evidence model remains unchanged.

One standard-backed Score may use:

* zero formal evidence links with a required professional-judgment rationale;
* one evidence source;
* or several evidence sources.

One evidence source may support:

* several standards Scores;
* several targets;
* Group and individual judgments;
* or both standard-backed and local Criteria.

Each use requires a separate deliberate Score Evidence Link.

### Group evidence and individual standards Scores

Group or multi-subject evidence may support an individual standards Score when:

* the evidence is relevant to that individual target;
* the applicable evidence location or Subject context is identified where useful;
* any required Moderation permits that use;
* the teacher makes an explicit individual judgment;
* and the evidence-link description or Score rationale explains the relevance.

Group evidence must not generate individual standards Scores automatically.

### Group standards Scores

A standard-backed Score may target a Group when:

* the governing standard validly supports Group-level judgment;
* the Criterion identifies Group applicability;
* and the teacher deliberately selects the Group target.

A Group standards Score does not become an individual standards Score for every Group member.

Meridian must preserve that distinction unless an explicit, versioned Meridian policy defines a conversion.

### Authors and Subjects

Standards-based scoring does not collapse:

* Artifact Author;
* Artifact Subject;
* Score target;
* standard;
* and scorer

into one relationship.

For example:

```text
Artifact Author:
Student observer

Artifact Subject:
Observed student

Score target:
Observed student

Standard:
Speaking-and-listening participation standard

Scorer:
Teacher
```

or:

```text
Artifact Authors:
Group recorder and represented Group

Artifact Subjects:
Group and Session

Score target:
Group

Standard:
Engineering design-practice standard

Scorer:
Teacher
```

These relationships remain explicit and independent.

## Review and Moderation

Standards-based scoring does not bypass Review or Moderation.

Review continues to determine whether evidence is:

* correctly identified;
* readable;
* complete;
* properly filed;
* correctly attributed;
* relevant;
* and ready for possible use.

Moderation continues to determine whether evidence is:

* reliable;
* fair;
* credible;
* sufficiently specific;
* appropriately qualified;
* and permissible for the proposed consequential use.

Neither Review nor Moderation creates a standards Score.

An accepted Moderation decision means only that the evidence may be used under the recorded conditions.

The teacher still chooses:

* the standard-backed Criterion;
* the Score target;
* the Scoring Scale value;
* the evidence links;
* and the final rationale where applicable.

## Integration with Quillan

Quillan’s standards-based review records remain Quillan-owned.

A Quillan overall Focus Standard rating may be referenced by Concord as:

* supporting evidence;
* contextual evidence;
* complementary individual evidence;
* a follow-up reflection result;
* or another explicit External Reference purpose.

Concord must not:

* copy Quillan’s review record into a Concord-owned review;
* recreate Quillan’s review-unit workflow;
* assume that a Quillan rating automatically determines a Concord Score;
* or convert a Quillan result without explicit teacher judgment.

When a Quillan result contributes to a Concord Score:

```text
Quillan standard result
    -> Concord External Reference
    -> Concord Evidence Reference
    -> Concord Score Evidence Link
    -> explicit Concord Score Record
```

The Quillan record remains authoritative for the Quillan judgment.

The Concord Score remains authoritative for the Concord Activity judgment.

## Integration with ScoreForm

ScoreForm’s question-level standards alignment and selected-response results remain ScoreForm-owned.

A ScoreForm result may contribute to a Concord standards Score when it is relevant to the governing standard and Activity context.

For example:

```text
ScoreForm evidence:
Individual procedure-check result

Concord Focus Standard:
Uses appropriate scientific procedures and evidence

Concord judgment:
Teacher-approved standard-backed Score using the ScoreForm result
with laboratory observations and Group records
```

Concord must not:

* perform ScoreForm OMR processing;
* copy ScoreForm answer keys;
* treat a question-level standard alignment as a Concord Score;
* convert percentage correct automatically into a Concord rating;
* or infer a standard judgment from a ScoreForm result without teacher approval.

The integration path remains:

```text
ScoreForm result
    -> Concord External Reference
    -> Concord Evidence Reference
    -> Concord Score Evidence Link
    -> explicit Concord Score Record
```

When Concord publishes a Score supported by ScoreForm or Quillan evidence, the manifest must preserve the originating module-qualified record lineage. Meridian may also ingest the originating producer publication directly and therefore requires that lineage to apply an explicit overlap or deduplication policy.

## Publication and Meridian handoff

ADR 0015 operationalizes the handoff anticipated by this ADR.

Concord publishes selected results as immutable, revision-addressable **Concord Academic Result Manifests** registered through Core as `academic_result_set` publications.

The broader manifest may include:

* standard-backed Score Records;
* local Score Records;
* explicit non-score dispositions;
* Criterion definitions;
* exact Scoring Scale revisions;
* Score Evidence Links and module-qualified source lineage;
* applicable Moderation state;
* native Score supersession;
* and current-versus-superseded projection state.

The standards-specific projection defined by this ADR remains a subset of that manifest. It includes only standard-backed Scores and their governing standards.

A published standards result must make available:

```text
module_id
class_id
activity_id
optional session_id
score_record_id
target reference
standard_id
criterion_id
scoring_scale_id and exact revision semantics
score disposition
score value when applicable
scorer
scored_at
evidence lineage
moderation state
native Score supersession state
```

Core records publication of the exact immutable manifest bytes, path, contract version, digest, record-set identity, and revision. Core does not interpret the standards result.

Meridian determines:

* whether the publication is eligible under a policy;
* which standard-backed observations are selected;
* how repeated observations and reassessment are handled;
* whether local Scores participate in conventional or hybrid grading;
* which Academic Period applies;
* and how selected results contribute to proficiency, Grades, overrides, and Reports.

Publication does not imply Grade inclusion, Academic Period membership, mastery, or reporting.

Concord must not perform:

* cross-Activity aggregation;
* cross-module aggregation;
* marking-period calculations;
* course-grade calculations;
* mastery determination;
* standards-growth reporting;
* score weighting;
* scale normalization;
* report-card generation;
* parent reporting;
* or longitudinal reporting.

## No automatic mastery determination

A standard-backed Concord Score is one contextual teacher judgment.

It does not automatically establish:

* final mastery;
* permanent proficiency;
* course-level attainment;
* marking-period performance;
* or a Grade.

A student may receive several judgments for the same standard:

* in different Activities;
* in different Sessions;
* through different modules;
* using different evidence;
* or using different Scoring Scale revisions.

Meridian must determine how those judgments are:

* compared;
* weighted;
* combined;
* superseded;
* summarized;
* or reported.

Concord supplies the contextual standards result. It does not define the broader academic policy.

## Missing, inactive, or deprecated standards

Concord will preserve teacher-owned records when a standards reference no longer resolves cleanly.

### Missing standards library

Validation should report that shared standards infrastructure is unavailable.

Concord must not create a competing library merely to satisfy validation.

Existing Activity, Criterion, and Score records remain unchanged.

### Missing profile

Validation should identify the unresolved `standards_profile_id`.

Concord must not silently choose another profile.

### Missing standard

Validation should identify the unresolved `standard_id`.

Concord must not delete, replace, or reinterpret the Criterion or Score.

### Inactive or deprecated standard

Historical references remain valid provenance.

Teacher-facing displays should identify the standard as inactive or deprecated where Core supplies that metadata.

New Activity configuration should ordinarily prefer active standards unless the teacher deliberately chooses otherwise under an authorized workflow.

## Privacy

Standards-based Scores may be sensitive student records.

Privacy must remain record-specific.

A standards Score may be less restrictive than some of its supporting evidence, but that difference must be deliberate.

For example:

* a teacher-restricted peer observation may support a student-visible standards rating;
* the student may receive the Score and feedback without receiving the observer’s identity;
* a Group Artifact may remain Group-and-teacher visible while individual Score Records remain teacher-and-subject visible;
* and a Moderation rationale may remain more restricted than the resulting Score.

Meridian must not infer that access to a Score grants access to every supporting source.

## Consequences

### Positive consequences

* Concord’s standards-based purpose becomes explicit.
* Meridian can consume published Concord results without guessing how generic Criteria relate to standards.
* Direct standards judgments identify exactly one governing `standard_id`.
* Activity Focus Standards provide a clear scoring scope.
* Standard-backed and local Criteria remain distinguishable.
* Concord can support standards-based academic evaluation without forcing every Activity to produce Scores.
* Group and individual standards Scores remain explicit and separate.
* Existing Review, Moderation, evidence, and provenance decisions remain intact.
* Core remains the single owner of standards identity and profiles.
* Quillan, ScoreForm, and Concord can contribute different evidence forms without duplicating one another’s workflows.
* Missing evidence and non-score dispositions remain distinct from low performance.
* Historical standards results remain reproducible through immutable Criteria and Scoring Scale revisions.
* Meridian can distinguish direct standards results from contextual alignment during cross-module grading and reporting.

### Negative consequences

* Activity configuration becomes more explicit.
* Criteria require a standard-backed/local classification.
* Standard-backed Criteria cannot use several governing standards for one Score.
* Teachers may need to enter separate judgments when one classroom behavior reflects several standards.
* Criterion and Score validation becomes more complex.
* Reusable Criterion Sets must be checked against Activity Focus Standards.
* The user interface must distinguish direct standards judgments from local criteria clearly.
* Published manifests must preserve standard identity, scale identity, target type, and contextual provenance.
* Cross-scale comparison remains unavailable until the grading and reporting module defines an explicit policy.
* Existing generic points-based examples may require revision or relabeling.

## Compatibility with prior decisions

This ADR supplements rather than replaces the existing Concord architecture.

### ADR 0001: Concord Module Boundaries

Core still owns shared standards infrastructure.

Concord still owns its Activity configuration, Criteria, Scoring Scales, Score Records, and scoring workflows.

### ADR 0005: Separate Artifact Authors and Subjects

Author, Subject, Score target, scorer, and standard remain separate concepts.

### ADR 0007: Preserve Source Evidence and History

Standard-backed Scores, Criteria, evidence links, and revisions retain non-destructive history.

### ADR 0008: Separate Review, Moderation, Scoring, Grading, and Reporting

Standards-based Scoring remains separate from Grading and Reporting.

This ADR clarifies the semantic content of Concord Scores. It does not move Grade calculation or cross-module Reporting into Concord.

### ADR 0009: Many-to-Many Evidence-to-Score Relationships

The many-to-many evidence model remains unchanged.

One source may support several standards Scores, and one standards Score may use several sources.

### ADR 0010: Exceptional Evidence States Are Not Low Scores

Non-score dispositions remain explicit and never become inferred zeros or lowest proficiency levels.

### ADR 0012: Link ScoreForm and Quillan Without Duplication

External standards-related records remain owned by their source modules.

Concord references and uses them through explicit evidence relationships.

### ADR 0013: Keep Activity-Specific Structures Optional

Not every Activity requires Focus Standards, Criteria, or Scores.

Standards-based scoring is the primary academic scoring model, not a universal record-presence requirement.

### ADR 0015: Publish Versioned Concord Academic Result Manifests Through the Core Registry

ADR 0015 operationalizes this ADR's downstream handoff.

It preserves the standards-specific projection as a subset of a broader immutable Concord Academic Result Manifest, permits clearly identified local Scores to be published without converting them into standards ratings, and assigns publication discovery to Core and grading/reporting policy to Meridian.

## Alternatives considered

### Alternative 1: Retain generic Criteria with optional standards references

Rejected because Meridian or another authorized consumer could not determine whether a Score was:

* a direct judgment of one standard;
* a holistic judgment across several standards;
* a local Criterion;
* or merely standards-aligned.

Optional references are sufficient for instructional alignment but insufficient for unambiguous standards results.

### Alternative 2: Require every Concord Criterion to be a standard

Rejected because Concord also needs legitimate local Criteria for:

* Activity-specific procedures;
* collaboration protocols;
* equipment or material responsibilities;
* project handoffs;
* operational checks;
* and nonacademic collaborative contexts.

Making all Criteria standards-backed would either eliminate useful local judgments or encourage false standards mappings.

### Alternative 3: Permit one direct Score to govern several standards

Rejected because one value could not be apportioned defensibly among the standards.

A later reporting module would be forced to:

* duplicate the value across all standards;
* select one standard arbitrarily;
* average or divide the value;
* or discard the Score.

None of those interpretations should occur without a teacher decision.

### Alternative 4: Defer standards semantics until the grading and reporting module

Rejected because the reporting module cannot recover meaning that Concord failed to preserve.

The distinction between a direct standard judgment and a local Criterion must be recorded when the Activity and Score are created.

### Alternative 5: Copy Quillan’s standards-based review-unit model

Rejected because Concord evidence is not organized primarily around written review units.

Concord must support:

* Groups;
* Sessions;
* shared Artifacts;
* multi-subject evidence;
* teacher trackers;
* Activity Events;
* Attachments;
* contribution evidence;
* and changing Memberships.

Concord should share the principle of Focus Standard–centered teacher judgment without copying Quillan’s writing-specific workflow.

### Alternative 6: Treat ScoreForm or Quillan results as automatic Concord Scores

Rejected because external module results have their own:

* evidence context;
* target;
* scale;
* scoring method;
* and semantic scope.

External results may support a Concord judgment, but they do not determine it automatically.

### Alternative 7: Make standards-based scoring mandatory for every Activity

Rejected because some Concord Activities are:

* evidence-only;
* formative;
* procedural;
* extracurricular;
* or intentionally local.

The foundational domain must support standards-based scoring without requiring meaningless standards records.

## Required follow-up

When this ADR was accepted, the following documentation updates were required. ADR 0015 and the revised foundational documents have since expanded the handoff from a standards-only projection to an immutable Concord Academic Result Manifest published through Core. The remaining example and foundation-review work must validate both decisions together.

### Conceptual data contracts

Revise `docs/design/conceptual-data-contracts.md` to add or clarify:

* Activity scoring orientation;
* `standards_profile_id`;
* ordered `focus_standard_ids`;
* standard-backed and local Criterion classifications;
* exactly one governing `standard_id` for a standard-backed Criterion;
* optional non-governing alignment references for local Criteria;
* standards semantics for Score Records;
* the standards-specific projection within the broader Concord Academic Result Manifest;
* standards-specific validation invariants;
* Core Academic Work Registration and Publication Record relationships;
* manifest revision, digest binding, supersession, and withdrawal;
* Meridian consumption and Academic Period boundaries;
* and issue #12 representative examples.

### Initial domain model

Revise `docs/design/initial-concord-domain-model.md` so that:

* Focus Standards are explicit Activity configuration;
* standard-backed Criteria are distinguished from local Criteria;
* direct standards Scores are unambiguous;
* and generic points-based Criteria are not presented as the sole or primary scoring architecture.

### Cross-case requirements

Revise `docs/design/cross-case-requirements.md` to require representative support for:

* standards profile selection;
* ordered Focus Standards;
* standard-backed Criteria;
* local Criteria;
* Group standards Scores;
* individual standards Scores supported by Group or multi-subject evidence;
* non-score dispositions by standard;
* Concord Academic Result Manifest publication through Core;
* the standards-specific projection within that manifest;
* and Meridian consumption without inferred Grade inclusion.

### Conceptual design

Revise `docs/concord-conceptual-design-revised.md` to state explicitly that:

* Concord’s primary academic scoring model is standards-based;
* local collaborative Criteria remain valid;
* Score is distinct from Grade and mastery;
* and Meridian will combine contextual standards results under explicit, versioned policies.

### Representative contract examples

Issue `#12` must include examples that demonstrate:

1. a standards-based Activity;
2. a mixed Activity containing standard-backed and local Criteria;
3. an evidence-only Activity or evidence-bearing component;
4. an individual standards Score;
5. a Group standards Score;
6. Group evidence supporting an individual standards Score through explicit teacher judgment;
7. one evidence source supporting several standard-backed Scores;
8. separate Criteria when one Artifact contains evidence relevant to several standards;
9. a non-score disposition for a Focus Standard;
10. an external ScoreForm result used as supporting evidence;
11. an external Quillan standards result used as supporting evidence;
12. a local Criterion that carries optional alignment metadata but is not interpreted as a direct standards rating;
13. an immutable Concord Academic Result Manifest containing both standard-backed and clearly local Score projections;
14. a Core Publication Record bound to the exact manifest digest;
15. cross-producer ScoreForm or Quillan lineage sufficient for Meridian overlap policy;
16. publication supersession or withdrawal distinct from native Score supersession; and
17. publication that remains separate from Meridian Grade and Academic Period membership.

### Foundation review

Issue `#13` must verify that the proposed contracts allow Meridian to distinguish:

* direct standard-backed Scores;
* local Criterion Scores;
* evidence-only records;
* standard alignment without judgment;
* non-score dispositions;
* Group versus individual targets;
* current versus superseded Scores;
* and external evidence versus Concord-owned judgments.

## References

* [`docs/concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`docs/design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`docs/design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`docs/design/conceptual-data-contracts.md`](../design/conceptual-data-contracts.md)
* [`docs/decisions/0001-concord-module-boundaries.md`](0001-concord-module-boundaries.md)
* [`docs/decisions/0005-separate-artifact-authors-and-subjects.md`](0005-separate-artifact-authors-and-subjects.md)
* [`docs/decisions/0007-preserve-source-evidence-and-history.md`](0007-preserve-source-evidence-and-history.md)
* [`docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`](0008-separate-review-moderation-scoring-grading-and-reporting.md)
* [`docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`](0009-many-to-many-evidence-to-score-relationships.md)
* [`docs/decisions/0010-exceptional-evidence-states-are-not-low-scores.md`](0010-exceptional-evidence-states-are-not-low-scores.md)
* [`docs/decisions/0012-link-scoreform-and-quillan-without-duplication.md`](0012-link-scoreform-and-quillan-without-duplication.md)
* [`docs/decisions/0013-keep-activity-specific-structures-optional.md`](0013-keep-activity-specific-structures-optional.md)
* [`docs/decisions/0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md`](0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md)
* `pds-core/docs/module_standards_integration.md`
* `pds-core/docs/standards_contract.md`
* `pds-quillan/docs/adr/0001-standards-based-review-model.md`
* `pds-quillan/docs/assignment_contract.md`
* `pds-quillan/docs/review_record_contract.md`
* `pds-quillan/docs/assignment_reporting_contract.md`
* `pds-scoreform/docs/schema_contracts.md`
