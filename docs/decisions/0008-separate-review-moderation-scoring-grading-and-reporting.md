# ADR 0008: Separate Review, Moderation, Scoring, Grading, and Reporting

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Concord manages evidence produced during collaborative classroom activities.

Once evidence enters the system, several different human actions may occur:

* a teacher checks whether a scanned Artifact is readable and filed correctly;
* a teacher decides whether a peer observation is sufficiently reliable to use;
* a teacher evaluates one Criterion for one student or Group;
* an academic policy combines several Scores into an assignment or course Grade;
* and a teacher, school, or reporting system communicates selected results.

These actions are related, but they answer different questions.

| Concept        | Primary question                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------- |
| **Review**     | Is this evidence correctly identified, complete, readable, relevant, and ready for further use?      |
| **Moderation** | Is this evidence sufficiently reliable, fair, and appropriate for the proposed consequential use?    |
| **Scoring**    | What teacher-approved judgment does the available evidence support for one Criterion and one target? |
| **Grading**    | How should one or more Scores be combined or transformed under an academic policy?                   |
| **Reporting**  | Which results or evidence should be communicated, to whom, and in what form?                         |

Collapsing these actions into one record or status would create ambiguity.

For example:

* a readable and correctly filed peer observation may still be unfair or disputed;
* accepted evidence may support several different Scores;
* a Score may be formative and never become part of a Grade;
* a Grade may combine Concord, ScoreForm, Quillan, and teacher-entered results;
* and a Report may present only selected parts of a Grade, Score, or evidence record.

The system must preserve these distinctions so that teachers and downstream modules can determine:

* what evidence existed;
* whether it was reviewed;
* whether it required moderation;
* what judgment the teacher made;
* how another system used that judgment;
* and what was later communicated.

## Decision

Concord will model **Review, Moderation, and Scoring as separate Concord-owned records and workflows**.

**Grading and Reporting will remain outside Concord.**

The general relationship is:

```text id="3r2w3e"
Evidence
    -> Review
    -> optional Moderation
    -> optional Score
    -> external Grade calculation
    -> external Report or communication
```

This diagram represents a common progression, not a mandatory linear pipeline.

Not every evidence source requires every step.

For example:

* an unreadable Artifact may stop after Review;
* teacher-authored evidence may not require separate Moderation;
* a reviewed Artifact may remain unscored;
* a teacher may record a Score using professional judgment without one controlling Artifact;
* a formative Score may never be used in a Grade;
* and evidence may be reported without being converted into a Grade.

## Evidence

Evidence is the material or record considered during human judgment.

Possible Concord evidence sources include:

* reviewed Artifact Instances;
* Artifact Pages;
* teacher observations;
* moderated peer observations;
* Contribution Claims;
* Activity Events;
* reviewed Attachments;
* teacher-entered rationales;
* ScoreForm results;
* Quillan responses;
* and other authorized external references.

Evidence is not itself:

* a Review;
* a Moderation decision;
* a Score;
* a Grade;
* or a Report.

A completed page does not become a Score merely because it contains marks, ratings, notes, or a rubric layout.

The source evidence and all later judgments remain distinguishable records.

## Review

### Purpose

A Review records a human examination of an Artifact Instance or other routed evidence.

Review determines whether the evidence is administratively and evidentially ready for possible use.

A Review may evaluate:

* scan readability;
* page completeness;
* correct Artifact identification;
* correct Activity and Session filing;
* correct Group context;
* Author attribution;
* Subject attribution;
* privacy classification;
* relevance;
* duplicate or rescan status;
* need for correction;
* need for Moderation;
* and readiness for possible scoring.

### Review questions

A Review answers questions such as:

* Is this the expected Artifact?
* Is the scan readable?
* Are all expected pages present?
* Is the page assigned to the correct Activity and Session?
* Are the Authors and Subjects correct?
* Does the Artifact contain sensitive information?
* Is the evidence relevant to the intended use?
* Does it require Moderation?
* Is it ready to be considered during Scoring?

### Review outcomes

Possible Review outcomes may include:

* ready;
* ready with qualification;
* incomplete;
* unreadable;
* misrouted;
* duplicate;
* awaiting correction;
* awaiting additional evidence;
* moderation required;
* or not suitable for scoring.

The final vocabulary belongs in later contracts.

### Review does not determine performance

A Review does not answer:

* whether a student collaborated effectively;
* whether the work meets a Criterion;
* whether a peer claim is fair;
* what Score should be assigned;
* or what Grade should result.

A Review may conclude that an Artifact is readable and properly filed while making no judgment about performance.

### Review does not modify the source

A Review may confirm or correct metadata.

It must not modify the Core-retained source scan.

Corrections to:

* filing;
* Authors;
* Subjects;
* privacy;
* or Artifact relationships

must occur through linked records and preserved history.

### Review history

One Artifact may have several Reviews.

Later Reviews may:

* supplement an earlier Review;
* correct it;
* resolve an earlier uncertainty;
* or supersede it.

Earlier Reviews remain available for provenance.

## Moderation

### Purpose

Moderation records an authorized human judgment about the:

* reliability;
* fairness;
* relevance;
* credibility;
* qualification;
* or permissible consequential use

of evidence.

Moderation is narrower than general Review.

It is invoked when correctly filed evidence still requires judgment about whether and how it may be used.

### Evidence likely to require Moderation

Moderation is particularly important for:

* peer observations;
* student-created claims about another student;
* disputed Contribution Claims;
* conflicting Group accounts;
* contested authorship;
* reports of unequal participation;
* evidence that assigns blame;
* incomplete or questionable evidence;
* and evidence whose use could produce an unfair individual judgment.

Teacher-authored evidence may ordinarily proceed through normal Review without a separate Moderation Record, unless:

* it is disputed;
* policy requires another reviewer;
* it contains unresolved uncertainty;
* or the teacher deliberately invokes Moderation.

### Moderation questions

Moderation answers questions such as:

* Is the observation credible?
* Is the claim sufficiently specific?
* Is the evidence relevant to this Subject?
* Does another account conflict with it?
* Is the student being judged on circumstances outside the student’s control?
* May the evidence support an individual Score?
* May it support only a Group Score?
* Should it be used only with qualification?
* Should it be excluded from Scoring?

### Moderation outcomes

Possible outcomes include:

* accepted;
* accepted with qualification;
* insufficient;
* disputed;
* rejected;
* or not used for scoring.

An accepted-with-qualification decision should preserve the qualification.

For example:

```text id="nphlo1"
Accepted with qualification:
The observation confirms that the student assisted with testing,
but it does not establish who designed the test procedure.
```

### Moderation does not create a Score

A Moderation decision establishes whether evidence may be used and under what restrictions.

It does not determine:

* the Criterion being evaluated;
* the Score target;
* the permitted scale value;
* the final judgment;
* or the academic consequence.

For example, `accepted` does not mean high performance.

Likewise:

* `insufficient` is not a low Score;
* `disputed` is not a failing Score;
* and `rejected` evidence is not negative evidence against its Subject.

### Required Moderation before consequential use

When a Review or evidence type indicates that Moderation is required, that evidence must not support a consequential Score until an applicable Moderation decision exists.

This requirement applies to the evidence source, not necessarily to the entire Activity.

Other reviewed and permissible evidence may still support a Score independently.

### Moderation history

A later Moderation Record may supersede an earlier one when:

* additional evidence becomes available;
* a dispute is resolved;
* an attribution is corrected;
* or the proposed use changes.

The earlier decision and rationale must remain preserved.

## Scoring

### Purpose

A Score Record is one teacher-approved judgment about:

* one Criterion;
* for one target;
* in one defined Activity context;
* using one exact Scoring Scale revision.

A Score is more specific than a general evaluation of an Artifact or Activity.

### Score components

A Score Record should identify:

* durable `score_record_id`;
* Activity;
* optional Session;
* typed Score target;
* exact Criterion;
* exact Scoring Scale revision;
* Score disposition;
* Score value when applicable;
* scorer;
* scoring timestamp;
* optional rationale;
* Moderation-complete status where applicable;
* supporting Score Evidence Links;
* and optional superseded Score Record.

### Score targets

Possible Score targets include:

* student;
* Group;
* child Group or subteam;
* Session;
* Artifact Instance;
* Work Item or activity component;
* or Activity.

A Score target is distinct from:

* Artifact Author;
* Artifact Subject;
* Group Membership;
* evidence Author;
* and evidence Subject.

The teacher must choose the target deliberately.

### Criterion-level judgment

Each Score Record evaluates exactly one Criterion for exactly one target.

Examples include:

```text id="zyz07s"
Target:
Student A

Criterion:
Uses evidence in collaborative decisions

Scale:
4-level collaborative-performance scale

Value:
3
```

```text id="81kjpa"
Target:
Project Group 2

Criterion:
Coordinates dependent work

Scale:
Emerging / Developing / Effective / Exemplary

Value:
Effective
```

A rubric containing several Criteria should produce several conceptual Score Records rather than one opaque combined score.

A convenience interface may display or enter those records together.

### Score disposition

A Score Record must distinguish a scored judgment from a non-score condition.

Possible dispositions include:

* scored;
* insufficient evidence;
* absent;
* excused;
* not observed;
* not applicable;
* or deferred.

When the disposition is `scored`, a valid Scoring Scale value is required.

When the disposition is not `scored`, Concord must not infer:

* zero;
* failure;
* the lowest scale level;
* or any other negative performance judgment.

Additional exception handling is addressed in ADR 0010.

### Evidence links

A Score may cite:

* zero evidence sources;
* one evidence source;
* or several evidence sources.

A teacher may enter a Score through professional judgment without one controlling Artifact.

When no controlling Artifact exists, the Score should preserve:

* scorer identity;
* rationale;
* Activity context;
* and any available supporting references.

When evidence is linked, the Score must identify the evidence deliberately through Score Evidence Links.

The many-to-many evidence-to-Score relationship is addressed in ADR 0009.

### Scoring does not follow automatically from Review

A Review status of `ready for scoring` means only that the evidence may be considered.

It does not create, recommend, or populate a Score automatically.

The teacher may:

* use the evidence;
* use it with other evidence;
* decline to Score it;
* use it formatively;
* or determine that more evidence is needed.

### Scoring does not follow automatically from Moderation

An accepted Moderation decision permits a defined use.

It does not dictate:

* which Criterion to Score;
* which target to Score;
* or which scale value to assign.

### Group Scores and individual Scores

A Group Score does not automatically generate individual Scores.

Group evidence may be relevant to individual judgment, but each individual Score requires an explicit teacher-approved decision.

Likewise, an individual Score does not automatically alter a Group Score.

### Score revision

A finalized, referenced, exported, or reported Score must not be edited destructively.

A revised Score should:

* receive its own identity;
* record the new judgment;
* preserve its evidence links;
* identify the earlier Score it supersedes;
* and retain the reason for revision where applicable.

## Grading

### Definition

A Grade is a broader academic result created by combining, weighting, transforming, or interpreting one or more Scores under an academic policy.

Examples include:

* an assignment Grade;
* project Grade;
* marking-period Grade;
* course Grade;
* standards-based proficiency summary;
* or another institutionally defined result.

### Grading operations

Grading may involve:

* weighting Criteria;
* combining several Concord Scores;
* combining Concord, ScoreForm, Quillan, and teacher-entered results;
* applying category weights;
* dropping or replacing results;
* applying late-work policy;
* applying reassessment policy;
* converting scale levels to points;
* calculating percentages;
* applying institutional rounding;
* or determining marking-period and course results.

These operations belong to a future gradebook or reporting module or another authorized institutional system.

### Concord’s grading boundary

Concord may:

* create Criterion-level Score Records;
* preserve optional aggregation guidance in a Scoring Scale;
* export Scores;
* link a Score to a future gradebook record;
* and display contextual summaries for teacher review.

Concord must not own:

* course-grade calculation;
* marking-period weighting;
* category weighting;
* institutional grading policy;
* report-card calculations;
* or final Grade authority.

### Aggregation guidance is not a Grade calculation

A Criterion Set or Scoring Scale may contain optional guidance such as:

* all Criteria should be considered;
* one Criterion is formative;
* or Group and individual Scores should remain separate.

Such guidance helps downstream interpretation.

It does not make Concord the authoritative grading system.

### Scores may remain ungraded

A Concord Score may be:

* formative;
* diagnostic;
* practice;
* feedback-only;
* locally informational;
* or excluded from academic grading.

The existence of a Score does not require a Grade.

### Grade changes do not rewrite Concord Scores

A downstream system may recalculate a Grade because:

* weights changed;
* another Score was added;
* a policy changed;
* or the teacher granted an exception.

That change must not alter the original Concord Score unless the underlying criterion judgment itself is revised.

## Reporting

### Definition

A Report is a selected presentation or communication of:

* evidence;
* Review status;
* Moderation outcome;
* Scores;
* Grades;
* progress;
* or related summaries.

Possible audiences include:

* teacher;
* student;
* parent or guardian;
* administrator;
* support team;
* or another authorized system.

### Reporting is not the source record

A Report is a representation of underlying records at a particular time.

It is not the authoritative replacement for:

* the source Artifact;
* Review;
* Moderation Record;
* Score Record;
* or Grade record.

Reports should retain enough identifiers or provenance to locate the underlying records where appropriate.

### Reporting may be selective

A Report may intentionally omit:

* restricted peer comments;
* observer identity;
* rejected evidence;
* superseded Scores;
* internal teacher notes;
* or Moderation rationale.

Selection and redaction do not modify the source records.

### Reporting may transform presentation

A reporting system may:

* summarize several Scores;
* display trends;
* convert internal identifiers to names;
* show only current records;
* group results by Criterion;
* or produce a parent-facing explanation.

Those presentation choices must not be mistaken for new Scoring or Grading judgments unless the reporting system explicitly creates such records under its own contract.

### Concord’s reporting boundary

Concord may provide teacher-facing operational views for:

* reviewing evidence;
* checking Scoring readiness;
* entering Scores;
* and inspecting provenance.

These workflow views are not formal academic Reports.

Concord may also export:

* Score Records;
* evidence references;
* Review status;
* or selected summaries

for another module.

Formal parent-facing, report-card, transcript, or cross-course reporting remains outside Concord.

## Ownership Boundaries

### Concord owns

Concord owns:

* Artifact Review records;
* Moderation Records;
* Criterion definitions;
* Criterion Sets;
* Scoring Scales;
* Score Records;
* Score Evidence Links;
* Scoring provenance;
* and Concord-specific correction and supersession history.

### Future gradebook or reporting modules own

A future gradebook or reporting module may own:

* Grade records;
* Grade calculations;
* weight configurations;
* academic-policy application;
* cross-module aggregation;
* reporting templates;
* audience-specific reports;
* parent-facing communication;
* report-card output;
* and downstream correction workflows.

### Other modules

ScoreForm and Quillan own their own:

* evidence-processing workflows;
* Review behavior;
* and Score or result records.

Concord may reference those results as evidence.

It must not reclassify them as Concord-owned Scores merely to include them in an Activity.

Core owns shared identity, source-scan retention, and provenance infrastructure. Core does not own Concord’s Review, Moderation, or Scoring judgments.

## Workflow Rules

### Common teacher-authored evidence workflow

```text id="6bx9ew"
Teacher observation
    -> Review
    -> Score consideration
    -> optional Score
```

A separate Moderation step is not automatically required.

### Peer-observation workflow

```text id="95r9qv"
Peer observation
    -> Review
    -> Moderation required
    -> accepted, qualified, or excluded
    -> optional Score consideration
```

### Incomplete evidence workflow

```text id="ewwzx2"
Artifact
    -> Review: incomplete or unreadable
    -> correction or rescan
    -> new Review
    -> optional Moderation
    -> optional Score
```

### Professional-judgment workflow

```text id="o41inm"
Teacher professional judgment
    -> Score with rationale and scorer provenance
```

This path does not require a fabricated controlling Artifact.

### External evidence workflow

```text id="u9b5d3"
ScoreForm or Quillan result
    -> durable External Reference
    -> Concord relevance and use decision
    -> optional Concord Score
```

The external result remains owned by its originating module.

### Downstream grading workflow

```text id="y26qhm"
Concord Score
    -> export or reference
    -> external Grade calculation
    -> external Report
```

Concord remains authoritative for its Score Record. The downstream system remains authoritative for its Grade and Report records.

## Privacy

Review, Moderation, Score, Grade, and Report records may have different visibility.

For example:

* a source peer observation may be teacher-restricted;
* a Moderation rationale may remain internal;
* a derived Score may be visible to the student;
* a Grade may be visible to the student and parent;
* and a Report may omit the observer’s identity.

Visibility must therefore be assigned by record and use.

The system must not assume that:

* evidence visibility determines Score visibility;
* Score visibility determines source-evidence visibility;
* or a parent-facing Grade authorizes access to all underlying peer evidence.

Superseded, rejected, or disputed records may require equal or greater restriction than current records.

## Historical Preservation

Review, Moderation, and Score records are historical judgments.

Once durable or consequential, they must not be silently overwritten.

A later record may:

* supplement;
* correct;
* qualify;
* or supersede

an earlier record.

The earlier record remains available under its privacy controls.

Downstream Grade and Report systems should likewise preserve their own history, but their detailed requirements are outside this ADR.

## Consequences

### Positive consequences

* Correct filing is not confused with valid evidence use.
* Evidence reliability is not confused with student performance.
* Moderation outcomes do not masquerade as Scores.
* Criterion-level Scores remain independently interpretable.
* Formative Scores can exist without becoming Grades.
* Grade policy can evolve without changing Concord evidence.
* Reporting can be audience-specific without altering source records.
* Peer evidence can be moderated before consequential use.
* Different modules retain clear ownership.
* Cross-module aggregation remains possible through durable references.
* Revised decisions preserve provenance.
* Teachers can explain how evidence became a Score and how a Score later became part of a Grade.

### Negative consequences

* The suite requires several related record types and workflows.
* Teacher-facing interfaces must communicate the distinctions clearly.
* A single Artifact may accumulate Reviews, Moderation Records, Scores, and external references.
* Downstream Grade and Report functionality cannot be completed entirely inside Concord.
* Cross-module integration requires durable identifiers and compatibility policies.
* Users accustomed to one combined “graded” status may find the model more complex.
* Privacy must be evaluated separately for each layer.
* Corrections may require coordinated changes across several modules.

### Implementation consequences

Concord implementations must:

* keep Review records separate from Moderation Records;
* keep Moderation Records separate from Score Records;
* prevent Review status from automatically creating a Score;
* prevent Moderation status from automatically creating a Score;
* require applicable Moderation before consequential use of flagged evidence;
* preserve Criterion and Scoring Scale revisions;
* represent non-score dispositions explicitly;
* preserve Score revision history;
* expose durable Score references for downstream systems;
* avoid implementing course-grade policy;
* avoid presenting operational views as formal Reports;
* and preserve record-specific privacy.

Interfaces may combine related actions on one screen for efficiency.

For example, a teacher may review an Artifact, moderate a peer claim, and enter a Score during one interaction.

The resulting domain records must nevertheless remain separate.

## Alternatives Considered

### Alternative 1: Use one “evaluation” record for Review, Moderation, and Score

Rejected.

One generic record would not distinguish:

* filing confirmation;
* evidence credibility;
* criterion judgment;
* and academic result.

It would also make status values ambiguous and complicate correction history.

### Alternative 2: Treat a reviewed Artifact as automatically accepted evidence

Rejected.

A page may be readable and correctly filed while still being:

* disputed;
* biased;
* irrelevant;
* incomplete;
* or inappropriate for individual Scoring.

### Alternative 3: Treat Moderation outcomes as Scores

Rejected.

Moderation evaluates the evidence, not the student’s performance.

`Accepted`, `disputed`, or `rejected` are evidence-use decisions, not performance levels.

### Alternative 4: Record only final Grades

Rejected.

A final Grade would conceal:

* the original Criteria;
* separate individual and Group judgments;
* evidence provenance;
* non-score conditions;
* and formative uses.

Concord requires Criterion-level Score Records.

### Alternative 5: Calculate Grades inside Concord

Rejected.

Grade calculation may combine:

* Concord Scores;
* ScoreForm results;
* Quillan results;
* teacher-entered work;
* institutional policies;
* category weights;
* and marking-period rules.

That responsibility extends beyond collaborative evidence and belongs in another module.

### Alternative 6: Treat every Score as graded work

Rejected.

Teachers may use Concord Scores for:

* formative feedback;
* diagnostics;
* conferencing;
* reflection;
* or instructional planning.

A Score does not inherently carry a Grade consequence.

### Alternative 7: Generate formal Reports directly from source evidence

Rejected as Concord’s responsibility.

Formal communication requires:

* audience selection;
* privacy policy;
* result aggregation;
* institutional wording;
* and often Grade context.

Concord may export or display operational evidence, but formal reporting belongs elsewhere.

### Alternative 8: Allow Reports to become the only retained result

Rejected.

Reports are selective presentations.

They may omit evidence, qualifications, superseded records, or internal rationale. The underlying records must remain authoritative.

### Alternative 9: Require Moderation for every evidence source

Rejected.

Routine teacher-authored evidence may not require a separate Moderation step.

Moderation must exist as a foundational capability but should be invoked conditionally.

### Alternative 10: Allow any accepted evidence to generate a Score automatically

Rejected.

Accepted evidence may:

* support several Criteria;
* concern several Subjects;
* be relevant only contextually;
* or remain unscored.

A Score requires an explicit teacher-approved judgment.

### Alternative 11: Store only the current Review, Moderation decision, or Score

Rejected.

Earlier judgments may explain:

* corrections;
* revised evidence use;
* changed Scores;
* and prior exports.

Supersession must preserve history.

## Required Follow-Up

Later conceptual contracts must define:

* Artifact Review fields and statuses;
* Review readiness and correction states;
* Moderation Record fields and statuses;
* evidence types that require Moderation by default;
* permitted-scoring-use representation;
* Criterion and Criterion Set structures;
* Scoring Scale versioning;
* Score Record structure;
* non-score dispositions;
* scorer and reviewer identity;
* Score Evidence Links;
* correction and supersession behavior;
* privacy classifications for each record type;
* downstream Grade references;
* Report or export references;
* and cross-module correction behavior.

Representative contract examples should test at least:

* a readable teacher-authored Artifact requiring no separate Moderation;
* a peer observation requiring Moderation;
* evidence accepted with qualification;
* rejected evidence that produces no negative Score;
* one Artifact remaining unscored;
* one Score supported by several evidence sources;
* one teacher-judgment Score without a controlling Artifact;
* one Group Score that does not create individual Scores;
* one non-score disposition;
* one revised Score;
* one Concord Score used in an external Grade;
* and one restricted evidence source summarized in a less-restricted Report.

## References

* [`docs/concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`docs/design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`docs/design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`docs/packet_models/socratic-seminar-packet-model.md`](../packet_models/socratic-seminar-packet-model.md)
* [`docs/packet_models/science-laboratory-group-packet-model.md`](../packet_models/science-laboratory-group-packet-model.md)
* [`docs/packet_models/collaborative-programming_engineering_project_packet_model.md`](../packet_models/collaborative-programming_engineering_project_packet_model.md)
* [`docs/decisions/0001-concord-module-boundaries.md`](0001-concord-module-boundaries.md)
* [`docs/decisions/0002-paper-first-human-reviewed-evidence.md`](0002-paper-first-human-reviewed-evidence.md)
* [`docs/decisions/0003-activities-require-explicit-sessions.md`](0003-activities-require-explicit-sessions.md)
* [`docs/decisions/0004-contextual-groups-memberships-and-roles.md`](0004-contextual-groups-memberships-and-roles.md)
* [`docs/decisions/0005-separate-artifact-authors-and-subjects.md`](0005-separate-artifact-authors-and-subjects.md)
* [`docs/decisions/0006-distinguish-roles-responsibilities-tasks-and-contributions.md`](0006-distinguish-roles-responsibilities-tasks-and-contributions.md)
* [`docs/decisions/0007-preserve-source-evidence-and-history.md`](0007-preserve-source-evidence-and-history.md)

## Notes

This ADR establishes the conceptual and ownership boundaries among Review, Moderation, Scoring, Grading, and Reporting.

It does not fully define the many-to-many relationship between evidence and Scores, which is addressed in ADR 0009. It also does not define the complete exceptional-evidence vocabulary, which is addressed in ADR 0010.
