# ADR 0009: Many-to-Many Evidence-to-Score Relationships

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Concord records collaborative evidence and teacher-approved criterion-level Scores.

The relationship between evidence and Scores is not one-to-one.

A teacher may use several evidence sources when evaluating one Criterion for one target.

For example, a Score concerning a student’s contribution to a project may draw on:

* a teacher observation;
* a responsibility record;
* a testing and revision log;
* a moderated Contribution Claim;
* a handoff record;
* and a related Quillan or ScoreForm result.

Conversely, one evidence source may support several Scores.

For example, one teacher observation tracker may contain evidence concerning:

* several students;
* one or more Groups;
* several Criteria;
* several Sessions;
* and both individual and Group performance.

Likewise:

* one discussion map may support judgments about Group responsiveness, facilitation, and development of ideas;
* one laboratory troubleshooting log may support Scores concerning testing, communication, revision, and coordination;
* one project handoff record may support judgments about a contributor, a recipient, a subteam, and the Group;
* and one external ScoreForm or Quillan result may provide relevant context for several Concord judgments.

A model that places one `artifact_id` directly on a Score would not support these cases.

A model that places one `score_id` directly on an Artifact would also fail because the same evidence may be reused deliberately for several distinct judgments.

The relationship must therefore be represented explicitly.

## Decision

Concord will model the relationship between evidence and Scores as **many-to-many** through a first-class `ScoreEvidenceLink` association.

The conceptual relationship is:

```text id="f46rnv"
Score Record
    -> zero or more Score Evidence Links
        -> one typed Evidence Reference
```

Across the full model:

```text id="dtly84"
one Score Record
    may use
zero, one, or several evidence sources

one evidence source
    may support
zero, one, or several Score Records
```

A Score Evidence Link records that a specific evidence source was considered relevant to one specific Score Record.

It does not:

* copy the evidence;
* convert the evidence into a Score;
* imply automatic weighting;
* prove the evidence was decisive;
* or create another Score for any other target.

## Score Record

A Score Record remains one teacher-approved judgment about:

* exactly one Criterion;
* for exactly one target;
* using one exact Scoring Scale revision;
* in one Activity context.

A Score Record may have:

* no Score Evidence Links;
* one Score Evidence Link;
* or several Score Evidence Links.

The number of links does not change the Score Record’s core identity.

For example:

```text id="522vtc"
Score Record

Target:
Student A

Criterion:
Contributes to testing

Scale:
Four-level collaborative-performance scale

Value:
3

Supporting evidence:
- teacher observation tracker;
- testing and revision log;
- moderated handoff record.
```

The Score remains one judgment.

The three evidence sources do not create three separate Scores unless the teacher explicitly records separate judgments.

## Evidence Reference

Evidence is a domain role that may be played by several record types.

Possible evidence sources include:

* reviewed Artifact Instance;
* Artifact Page;
* teacher observation;
* moderated peer observation;
* reviewed Attachment;
* Contribution Claim;
* Activity Event;
* teacher-entered rationale;
* ScoreForm result;
* Quillan response;
* or another authorized external record.

A Score Evidence Link therefore uses a typed Evidence Reference rather than requiring every source to be copied into one universal Evidence entity.

A typed Evidence Reference should identify:

* evidence source type;
* owning module where applicable;
* durable source identifier;
* optional page or evidence location;
* optional Subject context;
* optional relevance description;
* and applicable Moderation state.

The evidence source remains owned by its original Concord concept, Paper Data Suite module, or authorized external system.

## Score Evidence Link

Each Score Evidence Link should have its own durable identity.

It should be capable of recording:

* durable `score_evidence_link_id`;
* parent `score_record_id`;
* typed Evidence Reference;
* optional evidence locator;
* relevance or use description;
* optional significance note;
* applicable Moderation status or decision reference;
* creation provenance;
* and correction or supersession history where required.

### Link identity

The link is a meaningful association, not merely an implementation join table.

It records a claim such as:

> This evidence source was considered when making this criterion-level judgment for this target.

That relationship may need to be:

* inspected;
* explained;
* corrected;
* removed from current use;
* superseded;
* or preserved as part of a historical Score.

The link therefore requires durable identity when it becomes part of a finalized or consequential Score.

### Link direction

A Score Evidence Link belongs to one Score Record and identifies one primary evidence source.

One evidence source may appear in several Score Evidence Links associated with different Score Records.

For example:

```text id="us59xo"
Teacher Observation Tracker
├── supports Score A: Student 1 — responds to peers
├── supports Score B: Student 2 — uses evidence
├── supports Score C: Group 1 — coordinates discussion
└── supports Score D: Student 3 — facilitates participation
```

Each link has its own:

* Score target;
* Criterion context;
* evidence locator;
* relevance description;
* and potentially different Moderation or privacy implications.

## One Score May Use Several Evidence Sources

A consequential Score should be able to synthesize several forms of evidence.

Examples include:

### Seminar Score

```text id="qc5r9a"
Student Score:
Responds substantively to peers

Evidence:
- teacher observation tracker;
- accepted peer observation;
- discussion map;
- teacher rationale.
```

### Laboratory Score

```text id="gt8j44"
Student Score:
Contributes to testing and verification

Evidence:
- Group setup and responsibility record;
- teacher laboratory observation;
- troubleshooting log;
- measurement-check evidence.
```

### Project Score

```text id="ky43zb"
Student Score:
Supports integration of dependent work

Evidence:
- responsibility and dependency map;
- contribution and handoff record;
- testing and revision log;
- teacher project observation;
- related external project-artifact reference.
```

No single evidence source is required to control the judgment.

The teacher may synthesize evidence that differs in:

* source type;
* author;
* Subject;
* Session;
* reliability;
* scope;
* and level of detail.

## One Evidence Source May Support Several Scores

A source Artifact or record may contain evidence relevant to several Criteria or targets.

Examples include:

### Multi-subject teacher tracker

One teacher observation tracker may concern:

* several students;
* one Group;
* several Criteria;
* and several rotations.

It remains one Artifact Instance.

Later individual and Group Score Records may each create distinct Score Evidence Links to that Artifact.

### Discussion map

One discussion map may support:

* a Group Score concerning development of ideas;
* a Group Score concerning responsiveness;
* an individual facilitation Score;
* and an individual Score concerning synthesis.

The Artifact itself is not duplicated.

### Project log

One testing and revision log may support:

* a Group quality-control Score;
* an individual testing-contribution Score;
* an individual communication Score;
* and a Group adaptation Score.

Each use requires a separate teacher-approved Score Record and separate evidence link.

## Evidence Locators

When an evidence source contains information about several Subjects or Criteria, the Score Evidence Link may include a locator.

Possible locators include:

* page number;
* row label;
* student label;
* Group label;
* Criterion column;
* Session;
* rotation;
* milestone;
* event identifier;
* Work Item;
* timestamp;
* section heading;
* or teacher-entered note.

For example:

```text id="oie038"
Evidence source:
Teacher Observation Tracker

Locator:
Page 1, Student A row, "responds to peers" column,
Rotation 2
```

The locator helps an authorized reviewer find the relevant portion of the source.

It does not create a new source Artifact.

### No required handwriting-region extraction

The initial architecture does not require:

* pixel coordinates;
* automatic handwriting segmentation;
* optical character recognition;
* or cropped per-student evidence images.

Human-readable locators are sufficient for the initial model.

A future implementation may support more precise locators without changing the many-to-many relationship.

### Locator scope

A locator should identify where the relevant evidence can be found.

It should not be used to:

* rewrite the source;
* claim that nearby content was ignored automatically;
* or imply machine interpretation of the marked region.

The teacher remains responsible for interpreting the source evidence.

## Relevance and Use Description

A Score Evidence Link may record how the evidence informed the Score.

Examples include:

* confirms repeated use of evidence during discussion;
* corroborates testing contribution;
* establishes Session context;
* documents reassignment caused by absence;
* supports Group-level coordination judgment;
* qualifies a peer observation;
* or provides counterevidence to a Contribution Claim.

This description is especially useful when:

* the evidence source is broad;
* the connection is not obvious;
* evidence is used with qualification;
* several evidence sources conflict;
* or the Score is later reviewed.

The relevance description is not a substitute for the Criterion definition or Score rationale.

## Evidence Significance

A Score Evidence Link may include an optional significance or use note.

Possible descriptions include:

* primary evidence;
* corroborating evidence;
* contextual evidence;
* qualifying evidence;
* counterevidence;
* or background reference.

The initial model should not require numeric weighting for individual evidence links.

A significance note must not automatically:

* calculate the Score;
* average evidence sources;
* convert evidence quantity into performance;
* or imply that more evidence links produce a higher Score.

The teacher’s final Score remains a holistic or criterion-specific professional judgment under the selected Scoring Scale.

## Moderation

Evidence requiring Moderation must not support a consequential Score until the applicable Moderation decision permits that use.

The Score Evidence Link should retain enough information to determine:

* whether Moderation was required;
* which Moderation Record applied;
* the Moderation outcome;
* any qualification;
* and the permitted Scoring use.

For example:

```text id="1q7nb8"
Evidence:
Peer observation

Moderation:
Accepted with qualification

Permitted use:
May corroborate teacher evidence for responsiveness;
must not independently determine the Score.
```

A Moderation decision applies to evidence use.

It does not determine the Score value.

### Rejected evidence

Rejected evidence may remain preserved in the Activity history.

It should not remain an active supporting link for a consequential Score.

If a Score was originally based on evidence later rejected, the teacher may need to:

* confirm that other evidence still supports the Score;
* revise the Score rationale;
* create a corrected Score Evidence Link;
* or create a superseding Score Record.

The historical relationship must remain discoverable.

## Teacher Professional Judgment Without One Controlling Artifact

A teacher may record a Score without one controlling Artifact.

This is necessary because teacher judgment may arise from:

* direct observation across an Activity;
* several brief interactions;
* professional synthesis;
* evidence not captured on one form;
* or knowledge of circumstances affecting the Activity.

Such a Score may have zero Score Evidence Links.

When a consequential Score has no linked evidence source, it should preserve:

* scorer identity;
* scoring timestamp;
* Activity and optional Session context;
* rationale;
* and any applicable Review or Moderation note.

The system must not create a fabricated Artifact merely to satisfy a technical evidence-link requirement.

### Zero links do not mean no basis

A Score with no formal links does not necessarily mean the judgment was arbitrary.

It means that no discrete durable evidence source was linked.

The rationale and scorer provenance remain required safeguards.

### Linked rationale

A teacher-entered rationale may itself be represented as a durable evidence source and linked where the contract chooses to formalize that record.

The initial architecture permits either:

* rationale stored directly on the Score Record;
* or a separately identified teacher-rationale evidence record.

The contract phase must avoid duplicating the same rationale ambiguously in both places.

## Group, Subteam, and Individual Scores

Individual, Group, and child-Group Scores may cite overlapping evidence.

For example, one project log may support:

* a Group Score for coordination;
* a child-Group Score for testing;
* and an individual Score for technical contribution.

Those Scores remain distinct because each has:

* its own target;
* its own Criterion;
* its own value or disposition;
* its own teacher judgment;
* and its own Score Evidence Links.

### No automatic propagation

Group evidence must not automatically populate individual Scores.

A Group Score must not automatically:

* copy its value to each Group member;
* create individual Score Records;
* distribute points;
* or imply equal individual contribution.

Likewise, an individual Score must not automatically determine a Group Score.

Each Score requires explicit teacher judgment.

### Group Membership is contextual, not dispositive

A participant’s Group Membership may establish that the student belonged to the Group when the evidence was produced.

It does not prove that Group evidence is relevant to every individual Criterion for that student.

The teacher must determine:

* whether the evidence applies to the student;
* how it applies;
* and whether additional individual evidence is required.

### Group evidence as context

Group-level evidence may serve as:

* direct support for a Group Score;
* contextual support for an individual Score;
* evidence of shared circumstances;
* or evidence of a collaborative process.

The Score Evidence Link’s relevance description should clarify the intended use when it is not self-evident.

## Artifact Author, Subject, and Score Target

Artifact Author, Artifact Subject, and Score target remain separate.

An evidence source may have:

* one or several Authors;
* one or several Subjects;
* and Score links to one or several targets.

For example:

```text id="xo8hae"
Artifact:
Teacher Observation Tracker

Author:
Teacher

Subjects:
Students A, B, C, D and Group 1

Later Score targets:
- Student A;
- Student C;
- Group 1.
```

The existence of an Artifact Subject does not automatically authorize a Score for that Subject.

The Score target must be selected explicitly.

Likewise, the Artifact Author is not automatically the Score target.

## Cross-Module Evidence

A Score Evidence Link may reference evidence owned by another Paper Data Suite module.

Possible examples include:

* ScoreForm result;
* Quillan response;
* or another future module record.

The link should identify:

* owning module;
* external record type;
* durable external identifier;
* availability status;
* relevant Subject or target context;
* and relationship purpose.

Concord should not copy the full external record when a durable reference is sufficient.

### External result is not automatically a Concord Score

A ScoreForm or Quillan result may support a Concord Score.

It does not become a Concord Score merely because it is linked.

The Concord teacher must still make the explicit criterion-level judgment.

### Unavailable external evidence

If an external reference becomes unavailable, the link should preserve:

* the external identity;
* prior availability or use where known;
* current unavailable status;
* and historical Score relationship.

Unavailable evidence must not be converted automatically into:

* missing student work;
* a low Score;
* or a zero.

A teacher may need to review whether the Score remains adequately supported.

## Conflicting Evidence

Several evidence sources may disagree.

For example:

* a peer observation may claim that a student did not contribute;
* a teacher observation may document substantial testing work;
* a Group retrospective may report disagreement;
* and a handoff record may show a completed technical contribution.

The many-to-many model permits the teacher to preserve and consider all relevant sources.

The system must not automatically:

* average conflicting claims;
* count the majority of sources;
* privilege the newest source;
* privilege a student-authored source over teacher evidence;
* or treat all evidence as equally reliable.

The teacher may:

* moderate disputed evidence;
* qualify a Score;
* defer Scoring;
* seek additional evidence;
* exclude an unreliable source;
* or document the conflict in the rationale.

## Evidence Quantity

The number of evidence sources is not a performance measure.

Concord must not infer that:

* more evidence links mean better performance;
* fewer evidence links mean weaker performance;
* repeated records constitute independent corroboration;
* or one long Artifact carries more weight than several concise observations.

Several links may refer to:

* duplicated information;
* one repeated claim;
* several views of the same event;
* or genuinely independent evidence.

The teacher determines their significance.

## Duplicate and Overlapping Evidence

Several evidence sources may overlap substantially.

Examples include:

* an original Artifact and a routed derivative;
* a source page and its parent Artifact;
* a Contribution Claim repeated in a Group retrospective;
* a teacher note copied into a later rubric;
* or a ScoreForm result summarized in another record.

Implementations should allow the teacher to identify overlapping evidence where useful.

The system must not treat every linked record as independent evidence automatically.

### Source and derivative

A source scan, Scan Reference, Artifact Page, and Artifact Instance may represent different layers of one evidentiary chain.

A Score should generally link to the most semantically appropriate durable evidence source.

For example:

* link to the Artifact Instance when the whole Artifact is relevant;
* link to the Artifact Page when one page is relevant;
* use a locator when a specific row or section matters;
* and retain source-scan provenance through the linked Artifact.

The Score does not need separate links to every provenance layer unless each layer has an independent evidentiary purpose.

## Link Creation

A Score Evidence Link should be created only when the teacher or authorized workflow deliberately associates evidence with a Score.

Possible creation workflows include:

* selecting evidence while entering a Score;
* adding evidence during later Review;
* linking a previously reviewed Artifact;
* attaching a teacher observation;
* referencing an external result;
* or creating links through a rubric interface that clearly displays the selected evidence.

### No hidden automatic linking

Concord may suggest candidate evidence based on:

* matching Activity;
* Session;
* Subject;
* Group;
* Criterion;
* or Artifact type.

A suggested link must not become part of a consequential Score without clear teacher confirmation.

The system must not silently attach all evidence associated with a Subject or Group.

### Generated scoring forms

A paper or digital scoring rubric may display references to expected evidence sources.

Completing the rubric may create Score Records and confirmed Score Evidence Links.

The implementation must still preserve the conceptual separation between:

* the scoring form as evidence or entry surface;
* the resulting Score Records;
* and the links to supporting evidence.

## Link Correction and Historical Preservation

A finalized Score’s evidence links are part of its historical basis.

They must not be silently changed.

If a link is discovered to be incorrect, the system should preserve:

* the original link;
* the correction reason;
* correcting actor;
* correction time;
* and replacement or superseding relationship.

Depending on the consequence, the teacher may:

* correct the link while preserving the original association;
* create a new Score Evidence Link;
* create a new Review or Moderation Record;
* or create a superseding Score Record.

### Retargeting evidence

An existing historical Score must not be silently retargeted from one evidence source to another.

For example, when an unreadable scan is replaced by a rescan, the original Score must not simply appear to have used the newer scan.

The teacher may create a revised Score or corrected link that explicitly references the rescan.

### Revised Scores

A superseding Score Record may use:

* the same evidence links;
* a corrected subset;
* additional evidence;
* or entirely different evidence.

The earlier Score and its original links remain preserved.

## Privacy and Access

A Score Evidence Link does not broaden access to the evidence source.

A user authorized to view a Score may not necessarily be authorized to view:

* peer-observer identity;
* full handwritten comments;
* disputed Contribution Claims;
* teacher notes;
* or another student’s evidence.

The system may display:

* the Score;
* a sanitized evidence description;
* a locator;
* or an unavailable/restricted indicator

without exposing the full source.

### Restricted evidence

A link to restricted evidence should preserve the evidence identity and relationship while enforcing the source record’s privacy rules.

The system must not copy sensitive content into the Score Record merely to bypass those restrictions.

### Reports and exports

A Report or downstream export may include:

* the Score identifier;
* evidence-reference count;
* selected evidence labels;
* or authorized evidence references.

It should not include restricted source content unless the recipient is authorized.

## Scoring Surface Neutrality

The many-to-many model must not depend on how the teacher records the Score.

The same conceptual records should be possible when the teacher uses:

* a scanned paper rubric;
* a terminal interface;
* a future graphical interface;
* a batch Scoring screen;
* or another local workflow.

The interaction surface may combine several actions for convenience.

The resulting records remain:

* one Score Record per Criterion and target;
* plus zero or more explicit Score Evidence Links.

## Consequences

### Positive consequences

* One Score can synthesize several evidence sources.
* One Artifact can support several distinct Scores.
* Teacher trackers remain one source Artifact rather than being duplicated per student.
* Group, child-Group, and individual Scores may use overlapping evidence without becoming equivalent.
* Evidence locators can identify relevant portions of multi-subject Artifacts.
* Teacher professional judgment remains possible without a fabricated controlling Artifact.
* External ScoreForm and Quillan results can support Concord Scores through durable references.
* Conflicting and qualifying evidence can be preserved.
* Score provenance becomes inspectable.
* Corrected evidence relationships can retain history.
* Restricted evidence can remain protected while still supporting an authorized Score.

### Negative consequences

* The domain requires explicit association records.
* Scoring interfaces must support selecting and explaining evidence.
* Multi-subject Artifacts require locators or relevance descriptions.
* Queries must distinguish evidence sources from evidence links.
* Historical Score correction becomes more complex.
* Privacy checks must cross the Score-to-evidence boundary.
* Overlapping evidence may be difficult to identify.
* Teachers may need guidance to avoid excessive or meaningless linking.
* Downstream systems may not understand the full evidentiary relationship without adapter contracts.

### Implementation consequences

Implementations must:

* create a durable Score Evidence Link association;
* permit zero-to-many links per Score Record;
* permit zero-to-many links per evidence source;
* use typed Evidence References;
* support evidence locators;
* support relevance or use descriptions;
* preserve applicable Moderation status;
* allow individual, Group, and child-Group Scores to cite overlapping evidence;
* prohibit automatic Group-to-individual Score propagation;
* preserve evidence-link history for finalized Scores;
* enforce source-record privacy;
* permit Scores without formal links when rationale and scorer provenance are present;
* and avoid automatic numeric weighting based on link count.

Teacher-facing interfaces should make common cases efficient, including:

* linking several selected Artifacts to one Score;
* linking one teacher tracker to several Scores;
* reusing a locator pattern across a rubric;
* and displaying which evidence sources already support a Score.

## Alternatives Considered

### Alternative 1: Store one evidence identifier on each Score

Rejected.

One identifier cannot represent a Score supported by:

* teacher observation;
* peer observation;
* Group Artifact;
* and external result

at the same time.

### Alternative 2: Store one Score identifier on each Artifact

Rejected.

One Artifact may support:

* several Criteria;
* several Subjects;
* several targets;
* and several Score Records.

The Artifact cannot have one controlling Score.

### Alternative 3: Duplicate an Artifact for every Score

Rejected.

Duplication would:

* break source provenance;
* create inconsistent copies;
* inflate storage;
* and obscure that several Scores relied on the same evidence.

### Alternative 4: Create one universal Evidence record for every source

Rejected for the initial model.

Evidence is a role played by several record types.

Forcing every source into one universal entity would:

* duplicate existing records;
* create ambiguous ownership;
* and require flattening different provenance and privacy models.

Typed Evidence References provide the required flexibility.

### Alternative 5: Require at least one evidence link for every Score

Rejected.

Teachers may make valid professional judgments based on:

* direct observation across time;
* several uncaptured interactions;
* or evidence that does not exist as one durable Artifact.

Such Scores require rationale and scorer provenance rather than fabricated evidence.

### Alternative 6: Treat the scoring rubric as the only evidence

Rejected.

A scoring rubric records the teacher’s judgment.

It may also be a paper entry surface, but it does not replace the underlying evidence used to reach that judgment.

### Alternative 7: Automatically link all evidence sharing the same Subject

Rejected.

Evidence concerning the same Subject may:

* address different Criteria;
* belong to another Session;
* be irrelevant;
* require Moderation;
* or concern Group rather than individual performance.

Links require deliberate teacher confirmation.

### Alternative 8: Automatically copy Group Scores to members

Rejected.

Group performance and individual performance are different judgments.

Group evidence may inform an individual Score, but it cannot generate one automatically.

### Alternative 9: Weight evidence numerically and calculate the Score

Rejected as the foundational model.

Evidence sources differ in:

* purpose;
* reliability;
* scope;
* specificity;
* and context.

The initial architecture preserves teacher judgment rather than imposing an automated evidence-weight formula.

### Alternative 10: Count evidence sources as corroboration

Rejected.

Several records may repeat the same claim or derive from the same source.

Link count does not establish independent corroboration.

### Alternative 11: Copy external evidence into Concord

Rejected.

ScoreForm, Quillan, and other systems retain ownership of their records.

Concord should store durable references when sufficient.

### Alternative 12: Remove rejected or superseded evidence links

Rejected.

Historical links may explain:

* an earlier Score;
* a revised judgment;
* or a later correction.

They should be superseded or marked inactive, not silently erased.

### Alternative 13: Expose all linked evidence whenever a Score is visible

Rejected.

Score visibility does not authorize access to every underlying source.

Privacy remains record-specific.

## Required Follow-Up

Later conceptual contracts must define:

* typed Evidence Reference structure;
* `ScoreEvidenceLink` fields;
* allowed evidence-source types;
* evidence locator representation;
* relevance and use descriptions;
* optional significance vocabulary;
* Moderation decision references;
* link lifecycle and status;
* correction and supersession behavior;
* privacy and authorization checks;
* external-module evidence references;
* Score-without-links rationale requirements;
* and historical behavior when evidence becomes unavailable, corrected, or rejected.

Representative contract examples should test at least:

* one Score supported by several Concord Artifacts;
* one Score supported by teacher observation and external evidence;
* one teacher tracker supporting several individual Scores;
* one discussion map supporting individual and Group Scores;
* one evidence source supporting several Criteria;
* one multi-subject Artifact using different locators for different Scores;
* one Score with no formal evidence links but a teacher rationale;
* one moderated peer observation used with qualification;
* one rejected evidence source removed from current Score support while preserving history;
* one Group Score and individual Score using overlapping evidence;
* one Group Artifact that does not create individual Scores automatically;
* one external evidence reference becoming unavailable;
* one corrected evidence link;
* and one revised Score using a different evidence set.

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
* [`docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`](0008-separate-review-moderation-scoring-grading-and-reporting.md)

## Notes

This ADR establishes the relationship between evidence sources and Score Records.

It does not define the full exceptional-evidence vocabulary, which is addressed in ADR 0010. It also does not define external-artifact ownership or cross-module ScoreForm and Quillan integration in full; those boundaries are addressed in ADRs 0011 and 0012.
