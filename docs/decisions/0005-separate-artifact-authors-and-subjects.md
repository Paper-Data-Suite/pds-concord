# ADR 0005: Separate Artifact Authors and Subjects

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

A Concord Artifact may be completed by one person while describing, evaluating, representing, or documenting someone or something else.

Examples include:

* a student observer completing a peer observation about another student;
* a discussion mapper documenting a Group and Session;
* a teacher completing one observation tracker about several students;
* a recorder writing a response that represents a Group;
* several students jointly completing one design-decision record;
* a teacher scoring one student or one Group;
* or an Artifact concerning an Activity, Session, milestone, event, component, or external project artifact.

In these cases, the person whose handwriting appears on the page is not necessarily the person whom the Artifact concerns.

Likewise:

* the person holding the paper is not necessarily its author;
* the recorder is not necessarily the sole contributor;
* all Group members are not automatically co-authors;
* and the student named on the page is not necessarily the person who completed it.

A data model that stores only one `student_id` on an Artifact cannot represent these cases accurately.

It would be ambiguous whether that identifier meant:

* the student who completed the Artifact;
* the student being observed;
* the student being scored;
* a representative of the Group;
* the owner of a digital file;
* or merely the student used for routing.

The representative packet models establish that authorship and subject are independent relationships with different meanings and cardinalities.

## Decision

Concord will model **Artifact Authors** and **Artifact Subjects** as separate association records.

An Artifact Author identifies who completed, produced, recorded, or formally represented the Artifact.

An Artifact Subject identifies whom or what the Artifact concerns.

Neither relationship may be inferred automatically from the other.

### Artifact Author

An Artifact Author associates an Artifact Instance with a person or collective responsible for producing the Artifact.

Possible author forms include:

* one student author;
* several student co-authors;
* one student observer;
* one recorder;
* one recorder acting for a Group;
* several named contributors;
* a collective Group author;
* a teacher;
* another authorized adult;
* or an unknown author pending review.

An Artifact Author relationship should be capable of recording:

* durable association identity;
* `artifact_instance_id`;
* typed author reference;
* authorship mode;
* optional Role Assignment context;
* optional represented Group;
* attribution status;
* source of the attribution;
* and correction or supersession history.

### Artifact Subject

An Artifact Subject associates an Artifact Instance with the person, collective, context, event, or object that the Artifact describes or concerns.

Supported subject types may include:

* student;
* Group;
* Session;
* Activity;
* Activity Marker;
* Work Item;
* Activity Event;
* Attachment;
* external artifact;
* or another supported contextual entity.

An Artifact Subject relationship should be capable of recording:

* durable association identity;
* `artifact_instance_id`;
* typed subject reference;
* subject role or relationship;
* optional Criterion context;
* confirmation status;
* source of the subject assignment;
* and correction or supersession history.

### Independent cardinality

Artifact Author and Artifact Subject relationships have independent cardinality.

An Artifact Instance may have:

* zero Authors and zero Subjects while generated or unresolved;
* one Author and one Subject;
* one Author and several Subjects;
* several Authors and one Subject;
* several Authors and several Subjects;
* no student Author;
* no student Subject;
* or no confirmed Author or Subject while awaiting review.

The conceptual cardinality is:

```text id="ty0pxx"
Artifact Instance
├── zero or more Artifact Authors
└── zero or more Artifact Subjects
```

A reviewed evidence-bearing Artifact should normally have:

* at least one confirmed Author;
* an explicit collective-author status;
* or an explicit unknown-author status.

It should also have:

* at least one confirmed Subject;
* an explicit Activity- or Group-level scope;
* or an explicit unresolved-subject status.

### Authors and Subjects may be the same

The separation does not prohibit the same person or Group from appearing in both relationships.

Examples include:

* a student self-assessment;
* an individual reflection;
* a Group retrospective authored collectively by the same Group it concerns;
* or a teacher note about the teacher’s own intervention.

When Author and Subject are the same, both relationships should still be represented deliberately where both meanings matter.

The system must not assume sameness merely because the identifiers match.

### Authors and Subjects may differ

Examples include:

#### Peer observation

```text id="wvgahi"
Author: Student observer
Subject: Observed student
Context: Seminar Group and Session
```

#### Discussion map

```text id="ecf859"
Authors: Student mapper, several mappers, or teacher
Subjects: Seminar Group and Session
```

#### Teacher observation tracker

```text id="9qvaae"
Author: Teacher
Subjects: Several students, one Group, or both
```

#### Group process review

```text id="68xg66"
Author: Recorder acting for Group, named contributors, or collective Group
Subjects: Group and Session
```

These are normal Concord cases, not exceptions.

### Student identity is not required for every Subject

A Concord Artifact may concern:

* a Group;
* a Session;
* an Activity;
* an event;
* a task or component;
* an external project artifact;
* or several contextual entities.

Such an Artifact must not be forced to use:

* a synthetic student;
* a placeholder student;
* the recorder’s student identity;
* or one arbitrarily selected Group member

as its Subject.

Group and contextual subjects require their own typed references.

### Group Membership does not establish authorship

A participant’s Group Membership shows that the participant belonged to a collaborative unit during a defined context.

It does not prove that the participant:

* completed a particular Artifact;
* contributed to every part of it;
* agreed with its content;
* or should be listed as an Author.

Likewise, a Group-level Artifact does not automatically make every Group member a co-author.

Authorship must be recorded from:

* the generated assignment;
* the completed Artifact;
* a teacher review;
* an explicit Group representation statement;
* or another reliable attribution source.

### Role Assignment does not establish authorship automatically

A Role Assignment may provide relevant context, but it is not conclusive authorship evidence.

For example:

* a designated recorder may be absent;
* another student may physically complete the form;
* several students may collaborate on the response;
* or the Group may revise the recorder’s draft by consensus.

Concord may use a Role Assignment as a proposed attribution source, but the Artifact Author relationship remains independently reviewable.

### Recorder and represented Group must remain distinguishable

When one person writes on behalf of a Group, Concord should preserve both:

* the identity of the physical recorder where known; and
* the collective or represented Group authorship status.

Possible representation states include:

* individual recorder’s own response;
* recorder summary of Group discussion;
* majority Group position;
* unanimous Group position;
* several named individual views;
* or no consensus.

The recorder’s handwriting must not erase the Group representation context.

### Physical or digital possession does not establish sole authorship

The following must not automatically create or confirm sole authorship:

* handwriting;
* possession of the paper;
* scanning the page;
* generating the packet;
* device ownership;
* account ownership;
* repository ownership;
* file ownership;
* upload identity;
* or the location where an external file is stored.

These may be provenance signals, but they are not sufficient authorship determinations.

### Teacher-authored evidence

Teachers and other authorized adults may be Artifact Authors.

Teacher-authored Artifacts may concern:

* one student;
* several students;
* one Group;
* several Groups;
* one Session;
* or the Activity as a whole.

Teacher authorship does not remove the need for explicit Subjects.

### Multi-subject Artifacts remain single source Artifacts

A teacher observation tracker or similar document may concern several students and Groups.

The initial model will represent this as:

* one Artifact Instance;
* one or more Artifact Pages;
* one teacher Author;
* and several Artifact Subject relationships.

Concord will not require:

* duplicating the source Artifact once per student;
* creating synthetic student-specific scans;
* or extracting handwriting regions automatically.

Later Score Evidence Links may identify a relevant location through values such as:

* page number;
* row label;
* student label;
* Criterion column;
* rotation number;
* or teacher-entered note.

The retained scan remains one source record.

### Author and Subject are distinct from Score target

Artifact Author, Artifact Subject, and Score target are separate concepts.

A peer observation may have:

* an observer as Author;
* an observed student as Subject;
* and no direct Score.

A teacher tracker may have:

* the teacher as Author;
* several students as Subjects;
* and later support several individual Score Records.

A Group process Artifact may have:

* a recorder and Group as Authors;
* the Group and Session as Subjects;
* and support a Group Score or no Score.

The presence of an Artifact Subject does not automatically require a Score for that Subject.

### Author and Subject are distinct from contribution

Authorship records who produced or represented the Artifact.

It does not necessarily prove who contributed to the broader collaborative work documented by the Artifact.

For example:

* a recorder may author the form without performing every documented task;
* a student may contribute substantial technical work without writing on the Artifact;
* or several students may contribute to a project while one student prepares the summary.

Contribution evidence remains a separate concern.

### Review and correction

Author and Subject relationships may initially be:

* assigned during generation;
* proposed from a QR payload;
* entered manually;
* inferred from the template configuration;
* or unresolved.

Human review must be able to:

* confirm the proposed Author;
* add or remove Authors;
* change authorship mode;
* confirm the Subject;
* add or remove Subjects;
* record collective representation;
* mark attribution unknown;
* and document uncertainty or disagreement.

Corrections must not silently overwrite the prior attribution.

The earlier association and the reason for correction must remain available for provenance.

### Privacy

Author and Subject relationships may carry sensitive information, particularly for:

* peer observations;
* contribution disputes;
* teacher notes;
* moderation records;
* and critical Group feedback.

The visibility of an Artifact must not be inferred solely from the visibility of its Authors or Subjects.

For example:

* a peer observer’s identity may remain teacher-restricted;
* selected feedback may be shared with the Subject;
* and the full source Artifact may remain more restricted than a derived Score.

Privacy decisions remain record-specific.

### QR and routing implications

Concord’s QR and routing contracts must support Artifacts that:

* have no student Subject;
* have several student Subjects;
* have a Group Subject;
* have a Session or Activity Subject;
* or do not yet have confirmed Subjects.

Concord must not work around shared QR limitations by:

* placing a `group_id` into `student_id`;
* selecting an arbitrary student as the routing Subject;
* creating synthetic students;
* or using the Author as the Subject by default.

The QR payload may carry enough information to locate the Artifact Instance without encoding every Author and Subject relationship.

Full attribution should be resolved through the Artifact Instance and related association records.

## Consequences

### Positive consequences

* Peer observations can distinguish observer from observed student.
* Teacher trackers can represent several Subjects without duplicating source scans.
* Group- and Session-level Artifacts do not require synthetic students.
* Recorder identity can coexist with collective Group representation.
* Several Authors and several Subjects can be represented accurately.
* Authorship can be corrected without changing the source Artifact.
* QR routing no longer determines the semantic Subject of the Artifact.
* Group Membership and Role Assignment remain distinct from authorship.
* Score targets remain distinct from Artifact Subjects.
* Privacy can be applied appropriately to peer- and teacher-generated evidence.
* The model can support future activity types without assuming every Artifact is student-to-self.

### Negative consequences

* Artifact attribution requires association records rather than one student field.
* Queries for “the student attached to this Artifact” become intentionally invalid unless the relationship type is specified.
* Review interfaces must distinguish Authors from Subjects clearly.
* Multi-subject Artifacts require more complex display and filtering.
* QR payloads cannot contain all relevant attribution in a simple single-subject format.
* Collective and representative authorship require carefully defined status values.
* Corrections to attribution require historical records.
* External systems that expect exactly one student per record may require adapter logic.

### Implementation consequences

Implementations must:

* provide distinct Author and Subject association records;
* use typed references;
* support zero-to-many cardinality for both relationships;
* allow student, Group, teacher, Session, Activity, and other supported contextual references;
* distinguish individual, collective, representative, and unknown authorship;
* allow several Subjects on one Artifact;
* preserve attribution source and confirmation status;
* support correction and supersession;
* prevent Group identifiers from being stored as student identifiers;
* and keep Score targets separate from Artifact Subjects.

Teacher-facing interfaces should use explicit language such as:

* **Completed by**;
* **Recorded by**;
* **Represents**;
* **Observed student**;
* **Artifact concerns**;
* or **Subjects**.

A generic unlabeled “Student” field should not be used where the relationship is ambiguous.

## Alternatives Considered

### Alternative 1: Store one `student_id` on every Artifact

Rejected.

One student identifier cannot distinguish:

* observer from observed student;
* recorder from represented Group;
* teacher Author from student Subjects;
* or one student Subject from several Subjects.

It would also prevent Group-, Session-, and Activity-level Artifacts.

### Alternative 2: Treat the Author as the Subject

Rejected.

This works only for self-authored, self-subject Artifacts.

It fails for:

* peer observation;
* teacher observation;
* discussion mapping;
* Group representation;
* and external artifact documentation.

### Alternative 3: Treat the Subject as the Author

Rejected.

The person or Group being evaluated may not have completed or approved the Artifact.

This would falsely attribute peer comments and teacher observations to their Subjects.

### Alternative 4: Treat every Group member as an Author

Rejected.

Group Membership does not establish contribution to a particular Artifact.

Automatically assigning all members would:

* overstate authorship;
* conceal recorder or consensus status;
* include absent students;
* and make authorship unreliable as provenance.

### Alternative 5: Treat only the recorder as Author

Rejected.

The physical recorder may be writing:

* a Group consensus;
* a majority view;
* several individual views;
* or a teacher-directed summary.

Recorder-only authorship would lose the represented collective context.

### Alternative 6: Duplicate multi-subject Artifacts once per Subject

Rejected.

Duplicating a teacher tracker or similar source would:

* create several apparent source Artifacts from one physical page;
* complicate provenance;
* risk inconsistent copies;
* and obscure that several later Scores relied on the same source evidence.

One source Artifact with several Subject relationships preserves the evidence accurately.

### Alternative 7: Split multi-subject scans into handwriting regions

Rejected as a requirement.

Automatic or mandatory region extraction would:

* increase implementation complexity;
* depend on layout-specific interpretation;
* risk altering the relationship to the source page;
* and conflict with Concord’s human-reviewed model.

Optional evidence locators are sufficient for the initial architecture.

### Alternative 8: Infer authorship from handwriting or digital ownership

Rejected.

Those signals may be incomplete or misleading and cannot establish:

* collective authorship;
* co-authorship;
* represented Group status;
* or actual contribution.

Authorship remains an explicit, reviewable relationship.

### Alternative 9: Encode all Authors and Subjects directly in the QR payload

Rejected.

The complete attribution set may:

* be large;
* change after generation;
* require correction;
* include several entity types;
* or remain unknown until review.

The QR payload should identify and route the Artifact. The linked Artifact record should hold full semantic attribution.

### Alternative 10: Use Artifact Subject as the Score target automatically

Rejected.

Artifacts may be:

* unscored;
* supporting evidence only;
* multi-subject;
* Group-level;
* or relevant to a Score target different from their broad Subject set.

Score creation requires explicit teacher judgment.

## Required Follow-Up

Later conceptual contracts must define:

* typed Author reference structure;
* typed Subject reference structure;
* authorship modes;
* collective and representative authorship states;
* attribution confirmation statuses;
* subject relationship types;
* unresolved or unknown attribution states;
* correction and supersession behavior;
* privacy treatment for Author identities;
* evidence locators for multi-subject Artifacts;
* and QR routing support for non-student and multi-subject Artifacts.

Representative contract examples should test at least:

* one student Author and a different student Subject;
* one teacher Author and several student Subjects;
* several student Authors and one Group Subject;
* one recorder representing a Group;
* one Group collective Author;
* one Group Artifact with no individual student Subject;
* one Artifact concerning a Session and Activity;
* one unresolved Author;
* one corrected Subject;
* and one Artifact supporting Scores for several Subjects.

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

## Notes

This ADR establishes the semantic separation between who produced an Artifact and whom or what the Artifact concerns.

It does not fully define demonstrated contribution, which remains separate from Artifact authorship and is addressed in ADR 0006. It also does not define the many-to-many relationship between evidence and Scores, which is addressed in ADR 0009.
