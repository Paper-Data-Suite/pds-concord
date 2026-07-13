# ADR 0004: Contextual Groups, Memberships, and Roles

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Collaborative classroom structures are not fixed extensions of the class roster.

Across Concord’s representative packet models:

* seminar participants may rotate between active participant, observer, mapper, facilitator, and recorder roles;
* laboratory Groups may remain stable, change members, merge, split temporarily, or rotate responsibilities;
* project Groups may create temporary subteams and reorganize work across Sessions;
* students may arrive late, leave early, be absent, or be reassigned;
* several students may share one role;
* one student may hold several roles;
* and roles may change without changing the broader Activity.

The Core roster establishes durable class and student identity. It does not describe how students are organized for one Concord Activity or how that organization changes during the Activity.

A simple member list stored directly on a Group would not preserve:

* when a student joined or left;
* which Session the membership applied to;
* why a reassignment occurred;
* which earlier Artifacts were created under the previous arrangement;
* or which roles were active at a particular time.

Similarly, storing a role as a permanent student attribute would misrepresent contextual functions such as:

* peer observer;
* discussion mapper;
* materials manager;
* data recorder;
* tester;
* debugger;
* facilitator;
* or integration coordinator.

Concord therefore requires explicit, contextual records for Groups, Group Memberships, and Role Assignments.

## Decision

Concord will model **Groups, Group Memberships, and Role Assignments as separate, activity-specific, historically preserved concepts**.

### Groups are Activity-specific

A Group is a collaborative unit defined within one Concord Activity.

A Group:

* belongs to exactly one Activity;
* has its own durable `group_id`;
* is not added to the permanent Core class roster;
* has a teacher-facing label that may change without changing identity;
* may exist for the full Activity or only part of it;
* and may have a parent Group when it represents a temporary subteam.

Examples include:

* Seminar Group 2;
* Laboratory Table 4;
* Project Team C;
* Hardware Subteam;
* or Outer Circle Group 1.

The Group’s identity represents the teacher-defined collaborative unit, not merely its current list of members.

### Group identity is separate from membership composition

Changing one or more members does not automatically create a new Group.

The same Group may persist when:

* one student is absent;
* a student joins late;
* a student leaves early;
* a member is reassigned;
* or the teacher substitutes one participant for another.

A new Group should be created when the teacher intends to establish a distinct collaborative unit rather than revise the membership of an existing one.

Examples include:

* dividing one Group into two independent Groups;
* merging two Groups into a newly identified team;
* creating a temporary subteam with its own Artifacts;
* or reorganizing the class into a new Group structure for a later phase.

Earlier Groups and their Membership records must remain available after a split, merge, replacement, or reorganization.

### Group Membership is an explicit association

A Group Membership associates one participant with one Group for a defined context.

It is not:

* a field copied from the Core roster;
* a permanent student characteristic;
* a list entry that may be overwritten;
* or an inference from an Artifact.

Each Group Membership should have a durable `membership_id` and identify:

* the Group;
* the participant;
* the effective Session or Session range;
* membership status;
* creation provenance;
* an optional reason for change;
* and an optional superseding record.

The participant will normally be identified through a Core student reference. The model may also support another authorized participant type where required.

### Membership is Session-contextual

Membership must be associated with one or more explicit Sessions.

A participant may therefore:

* belong to Group A in Session 1;
* move to Group B in Session 2;
* participate only during part of the Activity;
* join a temporary subteam during one project phase;
* or be absent from one Session while remaining part of the broader Activity.

A change in membership must not rewrite the membership context of earlier Sessions.

For example:

```text
Session 1
- Student A -> Group 1
- Student B -> Group 1
- Student C -> Group 1

Session 2
- Student A -> Group 1
- Student B -> Group 2
- Student C -> Group 1
```

The Session 1 record remains valid after Student B moves to Group 2.

### Membership status is not evidence of performance

Membership records may indicate contextual states such as:

* active;
* joined late;
* left early;
* reassigned;
* absent;
* excused;
* or inactive.

These statuses describe participation context.

They do not establish:

* contribution;
* role fulfillment;
* quality of work;
* engagement;
* or a Score.

Performance judgments require reviewed evidence.

### Roles are contextual assignments

A Role Assignment records a function held by a participant within an Activity context.

Examples include:

* seminar participant;
* peer observer;
* discussion mapper;
* student facilitator;
* recorder;
* materials manager;
* safety monitor;
* tester;
* debugger;
* project coordinator;
* or quality reviewer.

A Role Assignment should identify:

* durable `role_assignment_id`;
* participant or Group Membership;
* role key or role-definition reference;
* parent Activity;
* applicable Session or Session range;
* optional Group context;
* optional stage or sequence context;
* assignment status;
* assignment source or assigner where relevant;
* and optional supersession relationship.

### Roles may overlap and change

The model must support:

* one participant holding several roles;
* several participants sharing one role;
* a participant changing roles between Sessions;
* a participant changing roles within one Session;
* a participant contributing outside an assigned role;
* and a role remaining unused in an Activity.

Role changes must preserve earlier assignments.

For example:

```text
Session 1, Rotation 1
- Student A: participant
- Student B: peer observer

Session 1, Rotation 2
- Student A: peer observer
- Student B: participant
```

Both assignments remain part of the Activity history.

### Roles are not permanent student attributes

Roles describe what a participant was assigned to do in a particular collaborative context.

They must not be used as permanent labels such as:

* leader;
* weak contributor;
* quiet student;
* technical student;
* or disengaged student.

A participant’s role in one Activity does not imply the same role in another Activity.

### Roles are distinct from responsibilities

A role is a named function.

A responsibility is a specific obligation, task, deliverable, decision, or duty.

For example:

* `data recorder` may be a role;
* `record the measurements for Trial 2` may be a responsibility.

An Activity may use:

* roles without explicit responsibilities;
* responsibilities without named roles;
* both roles and responsibilities;
* or neither.

Responsibility Assignment is an optional Concord capability and remains separate from Role Assignment.

The fuller distinction among roles, responsibilities, tasks, and contributions is recorded in ADR 0006.

### Temporary subteams use the Group model

A temporary subteam will initially be represented as a Group with:

* its own durable `group_id`;
* a `parent_group_id`;
* its own Membership records;
* bounded Session or Activity-marker context;
* and links back to the parent Group.

For example:

```text
Project Group A
├── Hardware Subteam
└── Software Subteam
```

A separate Subteam entity is not required in the initial model.

The child Group approach allows subteams to use the same:

* membership;
* role;
* Artifact;
* evidence;
* privacy;
* and Score-target relationships

already available to other Groups.

### Group records do not prove collective authorship

Group Membership and Role Assignment establish collaborative context. They do not automatically establish Artifact authorship.

A student may be a Group member without contributing to a particular Artifact.

Likewise:

* the recorder is not necessarily the sole author;
* all Group members are not automatically co-authors;
* and Group Membership alone does not establish an individual contribution.

Artifact Author and Artifact Subject relationships remain separate.

### Group records do not produce Scores automatically

Group Membership and Role Assignment are not Score records.

Concord must not automatically:

* award credit because a role was assigned;
* penalize a participant because a role changed;
* assign identical individual Scores to every Group member;
* or infer contribution from membership duration.

Scores require explicit teacher judgment supported by appropriate evidence.

### Relationship to Core

Core continues to own:

* canonical class identity;
* roster membership;
* durable student identity;
* and shared identity conventions.

Concord references those identities when creating Activity-specific Group Memberships and Role Assignments.

Concord must not:

* create duplicate student identities;
* modify the Core roster to reflect temporary Groups;
* represent a Group as a synthetic student;
* or place a `group_id` into a student identity field.

## Consequences

### Positive consequences

* Temporary classroom organization remains separate from the permanent roster.
* Membership and role changes can be represented without rewriting history.
* One-period and multi-period Activities use the same collaboration model.
* Absence, late arrival, early departure, and reassignment can be represented in the correct Session.
* Students may hold multiple or shared roles.
* Temporary subteams reuse the Group model rather than requiring a separate parallel hierarchy.
* Artifact authorship remains distinct from Group Membership.
* Role assignment remains distinct from performance evidence.
* Earlier Artifacts and Scores retain their original Group and Session context.
* Group labels may change without breaking durable references.

### Negative consequences

* Group organization requires more records than an embedded list of student IDs.
* Implementations must resolve Memberships for a particular Session.
* Role history adds temporal and supersession complexity.
* Teachers may need interfaces that make Group changes easy to record.
* Split and merge workflows require deliberate creation of new Groups and Memberships.
* Temporary subteams require parent-child Group validation.
* Queries for “current Group members” must distinguish current context from historical membership.

### Implementation consequences

Implementations must:

* assign durable identifiers to Groups, Memberships, and Role Assignments;
* associate every Group with one Activity;
* associate Memberships with effective Sessions or Session ranges;
* preserve superseded Membership and Role records;
* allow one participant to hold several roles;
* allow several participants to share one role;
* support Group parent-child relationships;
* prevent child Groups from crossing Activity boundaries;
* distinguish current from historical membership;
* avoid treating labels as identifiers;
* and keep Group Membership separate from authorship, contribution, and scoring.

Teacher-facing workflows should make ordinary cases simple.

For example, an implementation may:

* copy an initial Group arrangement across several Sessions;
* display the prior Session’s membership as a starting point;
* or create a temporary child Group through a concise action.

Such conveniences must still produce explicit historical records.

## Alternatives Considered

### Alternative 1: Store Groups in the Core roster

Rejected.

Core’s roster represents durable class and student identity. Concord Groups are temporary instructional structures that may change by Activity, Session, phase, or rotation.

Adding them to the Core roster would:

* mix permanent identity with temporary collaboration;
* make Core activity-aware;
* and create cleanup and history problems when Groups change.

### Alternative 2: Store member IDs directly on the Group

Rejected.

An embedded mutable member list would show only one state.

It would not preserve:

* Session-specific membership;
* joins and departures;
* reassignments;
* reasons for change;
* or the original context of earlier Artifacts.

Membership requires its own association record.

### Alternative 3: Create a new Group for every Session

Rejected as the default.

A Group may persist across several Sessions even while one or two members change.

Creating a new Group for every Session would:

* fragment Group history;
* duplicate stable Group context;
* and make longitudinal evidence harder to follow.

New Groups should represent genuinely distinct collaborative units, not every routine Session occurrence.

### Alternative 4: Infer Group Membership from generated Artifacts

Rejected.

Artifact assignment and completed evidence may be:

* missing;
* incorrect;
* incomplete;
* group-level;
* or unrelated to every participant.

Membership must exist independently so Concord can generate, route, review, and interpret Artifacts in the correct context.

### Alternative 5: Treat roles as fields on student records

Rejected.

Roles are contextual and may change repeatedly.

Storing a role on the student would:

* imply permanence;
* permit only one current role;
* and lose Activity, Session, Group, and historical context.

### Alternative 6: Store roles only as free text on Artifacts

Rejected.

Artifact-local text would not provide a consistent record of:

* who held a role;
* when the role applied;
* whether it changed;
* or how several Artifacts relate to the same assignment.

Templates may display role labels, but the assignment itself requires a contextual record.

### Alternative 7: Create a separate Subteam entity

Rejected for the initial model.

Subteams exhibit the same essential behavior as Groups:

* they have members;
* may have roles;
* may produce Artifacts;
* may be Subjects of evidence;
* and may receive Scores.

A bounded child Group supplies those capabilities with less conceptual duplication.

A separate entity may be reconsidered if later contract examples demonstrate materially different behavior.

### Alternative 8: Overwrite Memberships and roles when they change

Rejected.

Overwriting would break provenance for earlier:

* Artifacts;
* observations;
* contribution claims;
* Reviews;
* and Scores.

Changes must create new or superseding records while preserving the earlier context.

### Alternative 9: Treat every class member as part of one implicit Group

Rejected.

Whole-class Activities may use a Group representing the whole collaborative unit, but that Group must still be explicit when Group context matters.

An implicit class-wide Group would create inconsistent behavior between whole-class and small-Group Activities and would blur the boundary between the Core class roster and Concord collaboration context.

## Required Follow-Up

Later conceptual contracts must define:

* required Group fields;
* Group lifecycle and merge/split conventions;
* parent-child Group validation;
* Group Membership status values;
* effective Session and Session-range representation;
* Role Assignment status values;
* shared or module-specific role-definition vocabularies;
* reassignment and supersession behavior;
* authorized non-student participant references;
* and how Group and Session context participate in QR routing.

The contract examples should test at least:

* stable Groups across several Sessions;
* one student moving between Groups;
* late arrival and early departure;
* absence during one Session;
* one role shared by several students;
* one student holding several roles;
* role rotation within a Session;
* temporary child Groups;
* Group split and merge cases;
* and Artifacts whose authors do not match the full Group membership.

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

## Notes

This ADR defines the contextual organization of participants.

It does not define Artifact authorship and subject relationships, which are addressed in ADR 0005. It also does not fully define the distinction among roles, responsibilities, tasks, and demonstrated contributions, which is addressed in ADR 0006.
