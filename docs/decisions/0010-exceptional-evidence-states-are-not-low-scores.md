# ADR 0010: Exceptional Evidence States Are Not Low Scores

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Collaborative classroom evidence is frequently incomplete, unavailable, ambiguous, or affected by circumstances outside the evaluated participant’s control.

Examples include:

* a student being absent for one Session;
* an excused participant missing an Activity;
* a teacher not observing a particular behavior;
* an observer lacking enough evidence to make a claim;
* a scanned page being unreadable;
* an expected Artifact not being returned;
* a Criterion not applying to a participant’s role or context;
* Scoring being postponed until additional evidence becomes available;
* work being blocked by an unfinished dependency;
* laboratory equipment failing;
* required materials being unavailable;
* a project tool or external file becoming inaccessible;
* a class period being interrupted;
* a trial being invalidated;
* or a Group producing an unexpected result despite following a reasonable process.

These conditions do not all have the same meaning.

They may describe:

* evidence availability;
* observation opportunity;
* Activity context;
* workflow status;
* Moderation outcome;
* or a reason that a Score cannot yet be recorded.

None of them automatically establishes poor performance.

A simple numeric field cannot preserve these distinctions.

If Concord converts a blank, missing Artifact, unreadable scan, absence, or lack of observation into zero or the lowest scale level, it creates a performance judgment that the teacher did not make.

That would be particularly misleading in collaborative Activities because:

* one Artifact may concern several students;
* one student may participate in some Sessions but not others;
* Group work may be blocked by another task;
* a failed trial may demonstrate strong testing or adaptation;
* and an unavailable external Artifact may say nothing about the quality of the student’s work.

Concord therefore needs explicit non-score dispositions and separate contextual exception reasons.

## Decision

Concord will represent exceptional evidence and participation states explicitly.

A missing, unavailable, unreadable, inapplicable, deferred, blocked, or otherwise exceptional condition will **not automatically become a low Score, zero, or lowest performance level**.

A Score Record will distinguish between:

1. a teacher-approved scored judgment; and
2. a non-score disposition explaining why no valid Score value is recorded.

The conceptual rule is:

```text id="5uynbx"
scored disposition
    -> valid Scoring Scale value required

non-score disposition
    -> Score value absent
    -> no zero or lowest level inferred
```

Contextual causes will be recorded separately from the universal Score disposition when additional explanation is required.

## Three Distinct Layers

Exceptional situations may appear in three different layers.

### Evidence state

An evidence state describes the availability or condition of a source.

Examples include:

* expected but not returned;
* missing page;
* unreadable;
* incomplete;
* duplicate;
* misrouted;
* external reference unavailable;
* awaiting rescan;
* disputed;
* or rejected for Scoring use.

These states belong primarily to:

* Artifact lifecycle;
* Scan Reference;
* Artifact Review;
* External Reference;
* or Moderation Record.

They do not constitute Scores.

### Contextual exception

A contextual exception explains an Activity, Session, Work Item, or environmental circumstance.

Examples include:

* absence;
* excusal;
* late arrival;
* early departure;
* interrupted Session;
* equipment failure;
* material unavailable;
* invalid trial;
* dependency failure;
* blocked Work Item;
* external tool unavailable;
* teacher-directed reassignment;
* or Activity cancellation.

These conditions may explain why evidence is missing or incomplete.

They do not themselves determine performance.

### Score disposition

A Score disposition records whether the teacher made a valid criterion-level judgment.

The initial universal vocabulary is:

* `scored`;
* `insufficient_evidence`;
* `absent`;
* `excused`;
* `not_observed`;
* `not_applicable`;
* and `deferred`.

The contract phase may refine exact serialized names, but these semantic distinctions are required.

## Scored Disposition

A Score Record with the disposition `scored` represents an explicit teacher-approved judgment.

It must contain:

* one target;
* one Criterion;
* one exact Scoring Scale revision;
* one permitted Score value;
* scorer identity;
* scoring timestamp;
* and appropriate rationale or evidence provenance.

A value of zero or the lowest scale level is permitted only when:

* that value exists in the selected Scoring Scale;
* the teacher deliberately selects it;
* and it represents the teacher’s actual criterion-level judgment.

Zero must never serve as a technical substitute for:

* blank;
* missing;
* absent;
* not observed;
* insufficient evidence;
* not applicable;
* deferred;
* blocked;
* unavailable;
* or unresolved.

## Insufficient Evidence

`insufficient_evidence` means that the available evidence does not support a valid criterion-level judgment.

Possible causes include:

* too little evidence;
* conflicting evidence that has not been resolved;
* an unreadable Artifact;
* a missing page;
* an incomplete observation;
* an unmoderated peer claim;
* an unavailable external source;
* insufficient opportunity to demonstrate the Criterion;
* or evidence that is too broad to support the intended target.

This disposition does not mean that the target performed poorly.

It means that Concord does not contain a defensible Score for that Criterion and context.

### Insufficient evidence is not evidence of insufficiency

The phrase refers to the adequacy of the evidence, not the quality of the participant.

For example:

```text id="dx7ti8"
Disposition:
Insufficient evidence

Meaning:
The teacher cannot make a valid judgment.

Not implied:
The student demonstrated insufficient performance.
```

### Later evidence

If additional evidence becomes available, the teacher may create a scored judgment.

When the earlier non-score record was finalized or relied upon, the new Score Record should supersede it while preserving history.

## Absent

`absent` means that the target was not present for the relevant Activity, Session, or evaluative opportunity.

Absence must be attached to an appropriate scope.

For example:

* absent for Session 2;
* absent for the complete Activity;
* absent during the observed seminar rotation;
* or absent when a particular Work Item was completed.

Absence during one Session does not automatically establish absence from the entire Activity.

### Absence is not a performance judgment

The `absent` disposition does not mean:

* failed;
* refused;
* disengaged;
* made no contribution during the entire Activity;
* or earned zero.

A teacher or downstream gradebook system may apply an institutional attendance, make-up, or late-work policy outside Concord.

Concord preserves the evidence and Score state without inventing that policy.

### Group evidence and absent members

A Group Artifact produced while a student was absent must not automatically:

* count as individual evidence for that student;
* create an individual Score;
* or create a low Score because the student did not appear on the Artifact.

The teacher must determine the appropriate individual judgment.

## Excused

`excused` means that an authorized decision exempts the target from the particular evaluative expectation.

Possible reasons may include:

* approved absence;
* accommodation;
* alternate assignment;
* schedule conflict;
* teacher decision;
* or another institutionally recognized exception.

Concord should record only the minimum necessary reason or an authorized external reference.

It should not duplicate sensitive:

* medical;
* disability;
* disciplinary;
* counseling;
* or administrative records.

### Excused is not zero

An excused Score Record has no Score value.

A future gradebook or reporting system may decide how an excused result affects aggregation.

Concord must export the explicit disposition rather than substitute zero.

## Not Observed

`not_observed` means that the authorized observer did not obtain relevant evidence concerning the target and Criterion during the specified context.

Possible causes include:

* the teacher was attending to another Group;
* the behavior did not occur during the observation window;
* the student participated during another rotation;
* the observation form was incomplete;
* or the observer lacked a reasonable opportunity to see the behavior.

### Not observed is not not demonstrated

`not_observed` means:

> No valid observation was made.

It does not mean:

> The participant failed to demonstrate the Criterion.

The distinction is required.

For example:

```text id="bv76ko"
Not observed:
The teacher did not see whether Student A tested the component.

Not demonstrated:
The teacher observed the relevant work period and concluded that
Student A did not demonstrate the expected testing behavior.
```

The second statement may become evidence considered during Scoring.

It still does not automatically create the lowest Score. The teacher must make the criterion-level judgment deliberately.

### Silence and visibility

Concord must not infer poor collaboration merely because a student:

* was not recorded speaking;
* did not write on the Group Artifact;
* was not named in one observation;
* or performed less-visible work.

Listening, testing, verification, organization, and support may not produce highly visible evidence.

## Not Applicable

`not_applicable` means that the Criterion does not validly apply to the target in the defined context.

Examples include:

* a safety-monitor Criterion in an Activity without that responsibility;
* a presentation Criterion when the participant was not assigned or expected to present;
* an equipment-operation Criterion in a simulation without equipment;
* a component-specific Criterion for a Group that did not work on that component;
* or a Session-specific Criterion outside the participant’s effective membership.

Not applicable means the judgment should not be made.

It is not:

* failure;
* exemption after poor performance;
* missing work;
* or insufficient evidence.

### Applicability is contextual

A Criterion may apply:

* to one target but not another;
* during one Session but not another;
* to one Group role but not every role;
* or to one Activity configuration but not another.

The Criterion definition and selected target types should constrain applicability where possible.

The teacher retains authority to mark a specific Score context as not applicable.

## Deferred

`deferred` means that the Score decision has intentionally been postponed.

Possible reasons include:

* additional evidence is expected;
* Moderation is incomplete;
* a rescan is pending;
* a related Session has not occurred;
* the teacher intends to observe another opportunity;
* an external result has not arrived;
* or a dispute remains unresolved.

Deferred is a temporary decision state.

It must not be converted automatically to:

* zero;
* insufficient evidence;
* absent;
* or not applicable.

### Deferred lifecycle

A deferred Score Record may later be superseded by:

* a scored record;
* another non-score disposition;
* or a continued deferral with an updated reason.

The earlier state remains preserved when it has become durable.

## Contextual Exception Reasons

The universal Score-disposition vocabulary should remain small and stable.

Detailed causes should normally be stored as contextual reasons rather than creating a new Score disposition for every scenario.

Possible exception-reason categories include:

* missing Artifact;
* missing page;
* unreadable scan;
* incomplete Artifact;
* awaiting rescan;
* evidence conflict;
* Moderation pending;
* observer lacked opportunity;
* target absent;
* target excused;
* Criterion inapplicable;
* Activity interrupted;
* Session cancelled;
* Work Item blocked;
* unmet dependency;
* equipment failure;
* material unavailable;
* sample contamination;
* invalid trial;
* external tool unavailable;
* external Artifact unavailable;
* teacher approval delayed;
* Group reassignment;
* or other teacher-defined reason.

A reason may be associated with:

* Review;
* Score Record;
* Work Item;
* Activity Event;
* Session;
* External Reference;
* or another relevant record.

### Reason and disposition are separate

Two cases may share one Score disposition but have different reasons.

For example:

```text id="ay49mh"
Disposition:
Insufficient evidence

Reason:
Scan unreadable
```

```text id="598m82"
Disposition:
Insufficient evidence

Reason:
Conflicting peer observations awaiting resolution
```

Likewise, the same contextual event may lead to different Score outcomes.

For example, equipment failure may result in:

* a deferred Score;
* insufficient evidence;
* not applicable;
* or a valid scored judgment about problem-solving.

The teacher determines the outcome.

## Blocked Work

A Work Item or Responsibility may be blocked because:

* a predecessor task is unfinished;
* another subteam has not completed a handoff;
* required equipment is unavailable;
* required materials are missing;
* an external service is unavailable;
* teacher approval is pending;
* or the Activity is interrupted.

`blocked` is a workflow or contextual state.

It is not a Score disposition by itself.

### Blocked does not mean neglected

Concord must distinguish:

* blocked work;
* incomplete work;
* abandoned work;
* cancelled work;
* and neglected work.

A student or Group may respond to blocked work by:

* communicating the issue;
* adapting the plan;
* assisting another task;
* documenting the dependency;
* seeking appropriate help;
* or revising the design.

Those responses may provide positive evidence for Criteria concerning:

* communication;
* coordination;
* adaptability;
* troubleshooting;
* or responsibility.

### Responsibility assignment

A student assigned to blocked work must not automatically receive a low Score for noncompletion.

The teacher should consider:

* whether the blocker was within the student’s control;
* whether the student communicated the problem;
* whether reasonable alternatives existed;
* and how the student responded.

## Interrupted Activities

An Activity or Session may be interrupted by:

* schedule changes;
* emergency procedures;
* testing schedules;
* room changes;
* technology failure;
* teacher absence;
* safety concerns;
* or insufficient class time.

An interruption may affect:

* evidence completeness;
* observation opportunity;
* task completion;
* or the applicability of a Criterion.

The interruption should be recorded as context.

It must not automatically become a negative judgment about the participants.

## Equipment, Material, and Environmental Failure

Laboratory and engineering Activities may encounter:

* apparatus failure;
* material unavailability;
* sample contamination;
* measurement inconsistency;
* power failure;
* environmental interference;
* or unsafe operating conditions.

These events may invalidate a trial or prevent completion.

They are not automatically evidence of poor performance.

The relevant evidence may instead concern how the Group:

* recognized the problem;
* documented it;
* protected safety;
* evaluated the result;
* requested help;
* revised the procedure;
* or planned another trial.

### Student-caused failure

An equipment or material problem may sometimes result from student action.

Concord must still avoid automatically converting the event into a low Score.

The teacher must determine:

* which Criterion is relevant;
* whether the action was within the target’s responsibility;
* what evidence supports the judgment;
* whether the failure was accidental, negligent, or part of normal experimentation;
* and what response followed.

Formal safety or disciplinary consequences remain outside Concord.

## Failed Trials, Bugs, and Unsuccessful Products

A failed trial, software bug, structural weakness, or unsuccessful prototype is not itself negative collaborative evidence.

Such outcomes are normal in:

* experimentation;
* programming;
* engineering;
* design;
* testing;
* and iterative problem-solving.

The teacher may evaluate:

* quality of the original reasoning;
* systematic testing;
* recognition of failure;
* use of evidence;
* revision;
* persistence;
* communication;
* and adaptation.

A technically unsuccessful outcome may coexist with strong performance on collaborative Criteria.

Likewise, a successful final product does not automatically prove:

* equal contribution;
* sound collaboration;
* careful testing;
* or fulfillment of individual Responsibilities.

## Invalid or Excluded Trials

A trial may be marked invalid or excluded because:

* equipment malfunctioned;
* the procedure was not followed;
* the sample was contaminated;
* measurement conditions changed;
* required data was missing;
* or the result cannot be interpreted reliably.

Invalidity is an evidence-quality judgment about the trial.

It is not automatically a Score about the Group or participants.

The trial may still provide evidence concerning:

* recognition of limitations;
* documentation quality;
* troubleshooting;
* or decision-making.

## Unavailable External Evidence

An External Reference may become unavailable because:

* a file was moved;
* a service is offline;
* access permission changed;
* a repository is inaccessible;
* an external module is unavailable;
* or the referenced Artifact was never supplied.

Concord must preserve the reference and its availability state.

It must not automatically convert an unavailable external source into:

* missing student work;
* insufficient contribution;
* a zero;
* or a lowest-level Score.

The teacher may determine whether:

* other evidence is sufficient;
* the Score should be deferred;
* the Score should use `insufficient_evidence`;
* or no change is necessary.

## Missing Artifacts and Missing Evidence

An expected Artifact may be:

* not returned;
* returned but not scanned;
* scanned but unreadable;
* misrouted;
* missing one page;
* or unavailable because the template did not require its return.

These are distinct states.

A missing Artifact does not automatically establish that:

* no work occurred;
* the student did not participate;
* the Group failed;
* or the relevant Criterion deserves the lowest Score.

Evidence may exist elsewhere through:

* teacher observation;
* another Artifact;
* an Activity Event;
* an Attachment;
* ScoreForm;
* Quillan;
* or teacher professional judgment.

## Blank Fields

A blank field on an Artifact is ambiguous.

It may mean:

* not observed;
* not applicable;
* no response;
* insufficient time;
* skipped accidentally;
* missing evidence;
* or poor performance.

Concord must not interpret a blank automatically.

Templates should provide explicit options where distinctions matter, such as:

* observed;
* not observed;
* insufficient evidence;
* absent;
* excused;
* not applicable;
* or follow-up required.

Human Review determines the applicable meaning.

## Moderation States Are Not Scores

Moderation outcomes include states such as:

* accepted;
* accepted with qualification;
* insufficient;
* disputed;
* rejected;
* or not used for scoring.

These states evaluate evidence use.

They do not evaluate participant performance.

In particular:

* rejected peer evidence is not negative evidence against the Author;
* disputed evidence is not a low Score for the Subject;
* insufficient evidence is not insufficient performance;
* and accepted evidence does not imply a high Score.

The teacher must create a separate Score Record when a criterion-level judgment is appropriate.

## Review States Are Not Scores

Review outcomes such as:

* incomplete;
* unreadable;
* duplicate;
* misrouted;
* awaiting correction;
* or not ready for scoring

describe evidence processing.

They must not populate a Score value.

A later correction or rescan may change evidence readiness without changing any participant’s performance.

## Workflow Status Is Not Score Disposition

A Work Item may be:

* assigned;
* active;
* completed;
* partially completed;
* blocked;
* handed off;
* reassigned;
* cancelled;
* or superseded.

These statuses describe work progression.

They are not Score values.

For example:

* `completed` does not automatically mean exemplary;
* `partially completed` does not automatically mean developing;
* `blocked` does not automatically mean failing;
* and `reassigned` does not automatically mean the original assignee failed.

Scoring requires explicit Criterion interpretation.

## Artifact Status Is Not Score Disposition

An Artifact may be:

* generated;
* expected;
* returned;
* missing;
* scanned;
* reviewed;
* incomplete;
* or archived.

Artifact lifecycle does not determine a Score.

A returned Artifact may contain weak evidence.

A missing Artifact may be offset by other evidence.

A reviewed Artifact may remain unscored.

## Absence of Evidence and Negative Evidence

Concord will preserve the distinction between:

* **absence of evidence**; and
* **evidence supporting a negative judgment**.

Absence of evidence includes:

* not observed;
* missing Artifact;
* unreadable scan;
* unavailable external source;
* or insufficient opportunity.

Negative evidence requires an affirmative, reviewed basis for concluding that the target did not meet the Criterion.

For example:

```text id="8yuchf"
Absence of evidence:
The teacher did not observe whether the student checked measurements.

Potential negative evidence:
The teacher observed the student repeatedly recording measurements
without performing the assigned verification step.
```

Even negative evidence does not create a Score automatically.

The teacher must consider:

* the Criterion definition;
* full Activity context;
* other evidence;
* applicable Moderation;
* and the Scoring Scale.

## Score Value Nullability

The Score Record contract must enforce the relationship between disposition and value.

### When disposition is scored

* `score_value` is required.
* The value must be permitted by the exact Scoring Scale revision.

### When disposition is not scored

* `score_value` must be absent or null.
* Zero must not be inserted.
* The lowest ordinal level must not be inserted.
* A blank display must not be exported as zero.
* Downstream systems must receive the explicit disposition.

The contract should reject contradictory records such as:

```text id="gj8x56"
disposition: absent
score_value: 0
```

or:

```text id="07xeai"
disposition: scored
score_value: null
```

## Optional Reason and Notes

A non-score Score Record should permit:

* optional reason code;
* optional teacher note;
* optional related Review;
* optional Moderation reference;
* optional Session or Event;
* optional Work Item or dependency;
* and optional external reference.

A reason should not be required when the disposition itself is sufficiently explanatory.

For example, `absent` may need no additional note.

Sensitive details should be minimized.

## Downstream Gradebook and Reporting Behavior

Concord does not determine how a non-score disposition affects:

* assignment Grade;
* marking-period Grade;
* course Grade;
* make-up policy;
* late-work policy;
* or report-card presentation.

A downstream module may apply an authorized policy.

However, Concord must export:

* the explicit disposition;
* the absence of a Score value;
* the target;
* Criterion;
* context;
* and relevant reason where authorized.

It must not simplify every exceptional state into zero before export.

### Downstream coercion

A downstream system may choose to transform a non-score state under an explicit grading policy.

That transformation belongs to the downstream system and should preserve provenance back to the Concord disposition.

It must not alter the historical Concord Score Record.

## Aggregation

Non-score dispositions must not be included automatically in numeric or ordinal aggregation.

For example:

* `absent` is not numeric zero;
* `not_observed` is not the lowest ordinal level;
* `not_applicable` is not part of the denominator automatically;
* and `deferred` is not a temporary failing Score.

A future gradebook or reporting module must define how each disposition affects aggregation.

Concord may provide optional aggregation guidance but does not calculate the Grade.

## User Interface Requirements

Teacher-facing interfaces must display non-score states distinctly from scored values.

They should not use one blank cell for all conditions.

A practical interface may provide:

* a Score value selector;
* a separate non-score disposition selector;
* contextual reason options;
* notes;
* and links to unresolved evidence.

### Visual distinction

The interface should make it difficult to confuse:

* zero;
* lowest scale level;
* blank;
* not observed;
* absent;
* excused;
* insufficient evidence;
* not applicable;
* and deferred.

### Defaults

The system must not default an unresolved Score to zero.

A draft record may begin with:

* no disposition;
* or an explicit pending state outside the finalized Score vocabulary.

A Score must not become finalized until the teacher chooses a valid disposition.

### Batch entry

Batch Scoring interfaces must preserve the same distinctions.

For example, leaving several cells blank must not silently create zeros when the batch is saved.

## Historical Preservation

A finalized non-score disposition may later be replaced by a valid Score.

Examples include:

* a deferred Score completed after another Session;
* an insufficient-evidence record replaced after a rescan;
* a not-observed record replaced after a later observation;
* or an absent record followed by a make-up Activity.

The later Score should supersede the earlier record when the earlier record was durable.

The earlier disposition remains part of the history.

A later Score must not make it appear that evidence existed at the earlier time.

## Privacy

Exception reasons may contain sensitive information.

Concord should avoid storing unnecessary details about:

* health;
* disability;
* family circumstances;
* discipline;
* immigration status;
* counseling;
* or other protected information.

Where a reason must reference such circumstances, Concord should prefer:

* a general category;
* an authorized external-record reference;
* or a restricted teacher note.

Formal medical, disciplinary, accommodation, or administrative records remain outside Concord.

The visible Score disposition may be less detailed than the restricted reason.

## Consequences

### Positive consequences

* Missing evidence is not mistaken for poor performance.
* Zero remains an intentional Score rather than a placeholder.
* Absence and excusal remain distinct.
* Not observed remains distinct from not demonstrated.
* Criteria can be marked inapplicable without penalizing the target.
* Teachers can defer judgment while awaiting evidence or Moderation.
* Equipment failure and interrupted work can be represented fairly.
* Failed trials and unsuccessful prototypes may still support positive process judgments.
* Blocked work remains distinct from neglect.
* External evidence failure does not become student failure.
* Downstream gradebook systems receive semantically meaningful states.
* Revised judgments preserve historical context.

### Negative consequences

* Score Records require a disposition in addition to an optional value.
* Interfaces must present several states clearly.
* Downstream systems must understand non-score dispositions.
* Aggregation cannot treat every record as numeric.
* Teachers may need to select a reason in ambiguous cases.
* Contextual exception vocabularies require governance.
* Historical supersession adds complexity when later evidence becomes available.
* Privacy controls may be required for detailed reasons.

### Implementation consequences

Implementations must:

* enforce disposition-value consistency;
* prohibit automatic zero substitution;
* support the universal non-score vocabulary;
* represent contextual reasons separately;
* distinguish evidence, Review, Moderation, workflow, Artifact, and Score states;
* preserve Session and target scope;
* support later superseding Scores;
* export explicit dispositions;
* prevent non-score states from entering aggregation automatically;
* minimize sensitive reason details;
* and make zero visibly distinct from no valid Score.

## Alternatives Considered

### Alternative 1: Use zero for missing evidence

Rejected.

Zero is a performance value when permitted by the Scoring Scale.

Using it for missing evidence creates a judgment the teacher did not make.

### Alternative 2: Use the lowest rubric level for every exceptional state

Rejected.

The lowest level describes performance.

Absence, excusal, lack of observation, and equipment failure do not establish that performance level.

### Alternative 3: Leave every exceptional case blank

Rejected.

A blank does not explain whether the cause was:

* absence;
* insufficient evidence;
* inapplicability;
* deferral;
* or accidental omission.

Explicit dispositions are required.

### Alternative 4: Put every exception into one `not_scored` state

Rejected.

A single state would lose important distinctions needed for:

* teacher workflow;
* later follow-up;
* privacy;
* aggregation;
* and reporting.

### Alternative 5: Create a separate Score disposition for every possible cause

Rejected.

This would create an unstable and excessively large vocabulary.

Universal Score dispositions should remain small, while detailed causes are represented through contextual reason codes and related records.

### Alternative 6: Treat not observed as not demonstrated

Rejected.

Lack of observation does not prove lack of performance.

### Alternative 7: Treat a missing Artifact as missing work

Rejected.

The Artifact may be:

* optional;
* lost during scanning;
* misrouted;
* unreadable;
* or only one of several evidence sources.

Missing work is an instructional or grading judgment outside the Artifact’s technical state.

### Alternative 8: Treat Group evidence as evidence for every member

Rejected.

Group Membership does not establish individual contribution, and an absent participant may not have participated in the evidence-producing context.

### Alternative 9: Penalize failed trials or prototypes automatically

Rejected.

Failure may be a normal and productive part of experimentation and design.

The teacher should evaluate reasoning and response rather than outcome alone.

### Alternative 10: Penalize blocked work automatically

Rejected.

A dependency, equipment problem, or external failure may be outside the target’s control.

### Alternative 11: Allow Moderation states to populate Scores

Rejected.

Moderation evaluates evidence reliability and permissible use, not performance.

### Alternative 12: Let downstream systems infer dispositions from null values

Rejected.

A null value alone cannot distinguish absent, excused, not observed, insufficient evidence, not applicable, and deferred.

### Alternative 13: Store detailed medical or disciplinary reasons in Concord

Rejected.

Those records belong to authorized institutional systems.

Concord should retain only the minimum contextual information necessary for evidence and Scoring.

### Alternative 14: Revise a finalized non-score record in place

Rejected.

When a durable record is later replaced by a scored judgment, supersession should preserve the earlier state and chronology.

## Required Follow-Up

Later conceptual contracts must define:

* exact serialized Score-disposition values;
* disposition-value validation rules;
* optional exception-reason structure;
* Review and evidence-status vocabularies;
* Activity, Session, Work Item, and external-availability reason codes;
* not-observed versus not-demonstrated representation;
* finalized versus draft Score behavior;
* supersession when later evidence arrives;
* export behavior;
* downstream compatibility expectations;
* aggregation safeguards;
* privacy treatment for sensitive reasons;
* and display requirements for paper and digital Scoring surfaces.

Representative contract examples should test at least:

* one valid zero Score;
* one lowest-level ordinal Score;
* one insufficient-evidence record with no value;
* one absent Session-specific Score;
* one excused Activity-level Score;
* one not-observed record;
* one not-applicable Criterion;
* one deferred Score awaiting Moderation;
* one unreadable scan producing insufficient evidence;
* one missing Artifact with other usable evidence;
* one blocked Work Item that does not produce a low Score;
* one equipment failure followed by positive problem-solving evidence;
* one unsuccessful prototype with a strong process Score;
* one unavailable external reference;
* one non-score record later superseded by a scored record;
* and one downstream export that preserves the disposition without converting it to zero.

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
* [`docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`](0009-many-to-many-evidence-to-score-relationships.md)

## Notes

This ADR establishes the semantics of non-score and exceptional evidence states.

It does not define external Artifact ownership or external-system availability contracts in full; those are addressed in ADR 0011. It also does not define ScoreForm or Quillan integration behavior, which is addressed in ADR 0012.
