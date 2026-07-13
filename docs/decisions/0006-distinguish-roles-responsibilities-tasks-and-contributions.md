# ADR 0006: Distinguish Roles, Responsibilities, Tasks, and Contributions

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Collaborative classroom work involves several related but distinct concepts.

A student may:

* hold a named role;
* be assigned a specific responsibility;
* work on one or more tasks;
* make contributions outside the assigned role;
* assist another student or subteam;
* complete only part of an assigned responsibility;
* be prevented from completing work by an external condition;
* or contribute useful work that is not visible in the final product.

These distinctions appear throughout Concord’s representative packet models.

For example:

* `tester` may be a role;
* `execute the test plan during Session 3` may be a responsibility;
* `test the login component` may be a task;
* discovering and documenting a regression may be a contribution.

Likewise:

* `data recorder` may be a laboratory role;
* `record measurements for Trial 2` may be a responsibility;
* `Trial 2 measurement table` may be a task or work item;
* noticing an inconsistent measurement and requesting a retrial may be a contribution.

Treating these concepts as interchangeable would create several problems.

It could cause Concord to assume that:

* receiving a role proves that the role was fulfilled;
* being assigned a task proves that the task was completed;
* writing on a page proves that the writer performed all documented work;
* file ownership proves technical contribution;
* a completed Group product proves equal contribution by every member;
* a failed task proves poor effort;
* or only visible production counts as meaningful participation.

Concord therefore requires distinct records for intended organization and observed or claimed work.

## Decision

Concord will model **roles, responsibilities, tasks, and contributions as separate concepts with explicit relationships**.

They may refer to one another, but none automatically proves the others.

The conceptual distinction is:

| Concept               | Meaning                                               | Example                                                                |
| --------------------- | ----------------------------------------------------- | ---------------------------------------------------------------------- |
| **Role**              | A named contextual function                           | Tester                                                                 |
| **Responsibility**    | A specific assigned obligation                        | Verify the prototype before the milestone review                       |
| **Task or Work Item** | A bounded unit of work                                | Run load test on prototype B                                           |
| **Contribution**      | Work, support, judgment, or action actually performed | Identified a structural weakness and documented the failure conditions |

### Role

A Role describes a named function within an Activity context.

Examples include:

* facilitator;
* peer observer;
* recorder;
* materials manager;
* equipment operator;
* safety monitor;
* researcher;
* designer;
* programmer;
* tester;
* debugger;
* quality reviewer;
* or integration coordinator.

A Role Assignment records:

* who was assigned the role;
* the applicable Activity;
* the applicable Session, Session range, Group, or stage;
* assignment status;
* assignment provenance;
* and correction or supersession history.

Roles are contextual assignments.

They are not:

* permanent student attributes;
* personality descriptions;
* proof of performance;
* proof of authorship;
* or Scores.

### Responsibility

A Responsibility is a specific obligation assigned to a participant, Group, or child Group.

Examples include:

* prepare the materials;
* facilitate the first discussion rotation;
* record measurements for Trial 2;
* implement the navigation component;
* verify another subteam’s output;
* conduct the final test;
* or prepare the handoff package.

A Responsibility Assignment may refer to:

* a Role Assignment;
* a Session;
* a Group;
* an Activity Marker;
* a Work Item;
* an expected output;
* or another relevant Activity context.

Responsibilities are optional.

An Activity may use:

* formal roles without specific Responsibility records;
* direct Responsibilities without named roles;
* both;
* or neither.

### Task or Work Item

A Task, represented conceptually as a **Work Item**, is a bounded unit of collaborative work.

A Work Item may represent:

* a task;
* a component;
* a deliverable;
* a test;
* a research question;
* a design element;
* a physical construction step;
* or another identifiable unit of work.

A Work Item may contain:

* durable `work_item_id`;
* parent Activity;
* optional parent Work Item;
* Work Item type;
* concise label and description;
* optional Group context;
* optional Activity Marker;
* status;
* dependencies;
* and supersession history.

Work Items exist to contextualize:

* Responsibilities;
* Artifacts;
* Activity Events;
* Attachments;
* handoffs;
* Contribution Claims;
* and evidence.

Concord will not become a general project-management or scheduling system.

It does not need to provide:

* time tracking;
* workload optimization;
* resource forecasting;
* sprint management;
* automated scheduling;
* or comprehensive dependency planning.

### Contribution

A Contribution is useful work, support, judgment, communication, or action actually performed within the Activity.

Contributions may include:

* discussion;
* observation;
* questioning;
* synthesis;
* facilitation;
* implementation;
* construction;
* design;
* research;
* testing;
* debugging;
* documentation;
* measurement;
* verification;
* organization;
* integration;
* peer support;
* resource preparation;
* cleanup;
* quality review;
* troubleshooting;
* decision-making;
* or adaptation when plans change.

A Contribution may be evidenced by:

* an Artifact;
* a teacher observation;
* a moderated peer observation;
* an Activity Event;
* a Contribution Claim;
* a handoff record;
* a reviewed Attachment;
* a ScoreForm result;
* a Quillan response;
* or teacher professional judgment.

A Contribution is not automatically a Score.

### Contribution Claim

A Contribution Claim is a statement that a participant or Group made a particular Contribution.

A Contribution Claim may identify:

* claimant or recorder;
* claimed contributor;
* Activity and Session context;
* optional Role Assignment;
* optional Responsibility Assignment;
* optional Work Item;
* optional Activity Event;
* contribution category;
* concise description;
* corroboration status;
* moderation requirement;
* and correction or supersession history.

A Contribution Claim is evidence requiring review.

It is not accepted as fact merely because:

* a student wrote it;
* a Group recorder included it;
* it appears on a retrospective;
* or it matches an assigned Responsibility.

Claims about another student require teacher review before consequential use.

## Required Semantic Distinctions

### Assignment does not prove fulfillment

A Role or Responsibility Assignment records an intended organizational arrangement.

It does not prove that the participant:

* performed the work;
* completed the obligation;
* completed it independently;
* completed it well;
* or made the most significant Contribution.

Evidence of fulfillment must be recorded separately.

For example:

```text id="8jmk8b"
Role:
Tester

Responsibility:
Execute the prototype test plan during Session 3

Evidence:
Testing log, teacher observation, and documented defect

Teacher judgment:
Responsibility fulfilled
```

The Role and Responsibility establish context. The evidence supports the judgment.

### Contribution does not require prior assignment

Students may make valid Contributions outside their assigned Roles or Responsibilities.

Examples include:

* a recorder identifying a safety problem;
* a tester helping repair a component;
* a researcher mediating a Group disagreement;
* a programmer assisting with documentation;
* a student without a formal role asking a question that changes the design;
* or one subteam helping another overcome a dependency.

Concord must permit a Contribution to exist without a matching Role Assignment or Responsibility Assignment.

### Responsibility does not require a named role

A teacher may divide work through direct assignments without assigning formal role titles.

For example:

```text id="crjsc4"
Student A:
Record the Group’s measurements.

Student B:
Check each measurement.

Student C:
Prepare the next trial.
```

These are Responsibilities even when the teacher does not define `recorder`, `checker`, or `materials manager` as formal Roles.

### A role may contain several responsibilities

One Role may be associated with several Responsibilities.

For example, a project coordinator may be responsible for:

* checking progress;
* identifying blocked tasks;
* coordinating handoffs;
* and preparing the milestone review.

Each Responsibility should remain independently representable where the Activity requires that level of detail.

### A responsibility may be shared

Several participants or a Group may share one Responsibility.

Shared assignment does not imply:

* equal effort;
* identical Contributions;
* or identical individual Scores.

The resulting evidence must support any later distinction among individual Contributions.

### A task may have several responsible participants

One Work Item may be assigned to:

* one student;
* several students;
* one Group;
* one child Group;
* or different participants at different times.

Assignments may change while the Work Item retains its identity.

### A participant may contribute to several tasks

One Contribution may support:

* one Work Item;
* several related Work Items;
* a handoff;
* Group coordination;
* or the Activity generally.

The model must not force every Contribution into exactly one task.

### Completion and quality are separate

A Responsibility or Work Item may be complete but poor in quality.

It may also be incomplete while still producing useful evidence of:

* testing;
* troubleshooting;
* adaptation;
* communication;
* or sound decision-making.

Completion status must not substitute for criterion-level evaluation.

### Authorship and contribution are separate

Artifact authorship records who produced or formally represented an Artifact.

It does not prove who performed all of the work documented by that Artifact.

Examples include:

* one recorder documenting several participants’ Contributions;
* one student writing a Group decision reached collectively;
* a teacher recording a Contribution that produced no student-authored paper;
* or a contributor performing technical work while another student prepares the summary.

Artifact Author relationships and Contribution evidence must remain distinct.

### Group Membership and contribution are separate

Membership establishes that a participant belonged to a Group during a defined context.

It does not prove that the participant:

* contributed to every Work Item;
* helped produce every Group Artifact;
* fulfilled a Responsibility;
* or should receive the same Score as every other member.

### Account or file ownership and contribution are separate

Ownership of:

* a repository;
* a document;
* a device;
* a CAD file;
* a cloud file;
* or another digital resource

does not establish sole Contribution.

Concord may retain external references or provenance, but contribution judgments require contextual evidence.

## Responsibility and Work-Item Status

Responsibility and Work Item records should support statuses that describe workflow context without acting as Scores.

Possible statuses may include:

* assigned;
* accepted;
* active;
* completed;
* partially completed;
* reassigned;
* handed off;
* blocked;
* interrupted;
* cancelled;
* superseded;
* or not completed.

The contract phase may refine this vocabulary.

A status must not imply academic quality automatically.

For example:

* `completed` does not mean high quality;
* `not completed` does not necessarily mean poor performance;
* `reassigned` does not necessarily mean failure;
* and `blocked` requires contextual explanation.

## Reassignment and Historical Preservation

Role and Responsibility changes must preserve history.

A reassignment should record:

* original assignment;
* new assignment;
* effective context;
* reason where appropriate;
* actor making the change;
* and supersession relationship.

The original assignment must remain available because earlier:

* Artifacts;
* observations;
* Work Items;
* handoffs;
* Contribution Claims;
* and Scores

may depend on it.

A student should not appear to have held a Responsibility retroactively merely because the assignment changed later.

## Dependencies, Handoffs, and Blocked Work

Work Items may depend on other Work Items.

A participant may be unable to complete an assigned Responsibility because:

* another task is unfinished;
* equipment fails;
* required materials are unavailable;
* an external file cannot be accessed;
* a teammate is absent;
* teacher approval is delayed;
* or the Activity is interrupted.

These states must remain distinguishable from:

* neglect;
* refusal;
* low-quality work;
* or lack of understanding.

A handoff may document:

* contributor;
* recipient;
* Work Item or component;
* transferred material or information;
* completion state;
* verification or acceptance;
* follow-up requirement;
* and problems discovered later.

Acceptance of a handoff does not automatically prove quality.

A contributor must not automatically be blamed for a later integration failure without contextual evidence.

## Contribution Categories

Concord may support configurable Contribution categories.

The categories must not privilege only visible production.

A useful starter taxonomy may include:

* conceptual;
* communicative;
* organizational;
* technical;
* material;
* observational;
* analytical;
* testing;
* verification;
* integration;
* supportive;
* and reflective.

Activity-specific templates may use more precise terms.

For example:

* seminar templates may use questioning, synthesis, response, and facilitation;
* laboratory templates may use measurement, apparatus operation, safety, and verification;
* project templates may use implementation, testing, debugging, integration, and documentation.

These vocabularies are configuration data, not mandatory universal schema fields.

## Review and Moderation

Contribution evidence may vary in reliability.

Teacher-authored observations may be usable directly after normal review.

Student-created evidence may require moderation, particularly when it:

* evaluates another student;
* claims unequal participation;
* disputes authorship;
* assigns blame;
* describes a failed handoff;
* or conflicts with another account.

Moderation may result in statuses such as:

* accepted;
* accepted with qualification;
* insufficient;
* disputed;
* rejected;
* or not used for scoring.

Evidence requiring moderation must not affect a consequential Score until the required human judgment is recorded.

## Scoring Implications

Concord may define Criteria concerning:

* fulfills assigned Responsibilities;
* contributes useful work;
* communicates progress;
* manages dependencies;
* supports Group coordination;
* verifies or tests work;
* adapts when plans change;
* or assists others.

However:

* a Role Assignment does not create a Score;
* a Responsibility Assignment does not create a Score;
* Work Item completion does not create a Score;
* a Contribution Claim does not create a Score;
* and a Group product does not create identical individual Scores.

A Score Record remains an explicit teacher-approved judgment about one Criterion for one target.

The teacher may consider:

* assigned context;
* reviewed Contribution evidence;
* barriers outside the student’s control;
* quality;
* consistency;
* independence;
* support provided;
* and the relationship between individual and Group work.

## Consequences

### Positive consequences

* Planned organization remains separate from demonstrated work.
* Students can receive credit for Contributions outside assigned Roles.
* Direct Responsibilities can be used without formal role titles.
* Less-visible Contributions such as testing, coordination, verification, and support remain representable.
* Reassignment can be documented without rewriting history.
* Blocked work can be distinguished from neglected work.
* Group Membership does not become automatic evidence of Contribution.
* Artifact authorship does not become automatic evidence of broader work.
* Work Items can contextualize evidence without turning Concord into a project-management system.
* Contribution Claims can be reviewed and moderated before consequential use.
* Individual Scores remain explicit teacher judgments.

### Negative consequences

* The domain requires several related concepts instead of one generic assignment record.
* Teacher interfaces must explain the distinctions clearly.
* Detailed Responsibility or Work Item tracking may create classroom burden if overused.
* Contribution evidence may remain incomplete or disputed.
* Querying “what a student did” may require combining several evidence sources.
* Reassignment, handoff, and dependency history add complexity.
* Activity-specific Contribution vocabularies require configuration.
* Teachers must avoid treating the existence of records as proof of quality.

### Implementation consequences

Implementations must:

* keep Role Assignment and Responsibility Assignment separate;
* represent Work Items only when the Activity requires them;
* allow Contributions without prior assignments;
* allow assignments without confirmed Contributions;
* preserve reassignment history;
* support typed links among Roles, Responsibilities, Work Items, Events, Artifacts, and Contribution Claims;
* provide explicit blocked and exceptional states;
* keep Contribution Claims separate from Scores;
* support moderation of student-generated claims;
* and avoid automatic scoring from assignment or completion status.

Teacher-facing workflows should permit simple Activities to use Roles alone without requiring Work Items or Contribution Claims.

More structured Activities may progressively add:

```text id="f8qm1u"
Roles
    -> Responsibilities
    -> Work Items
    -> Activity Events and Artifacts
    -> Contribution evidence
    -> Teacher judgment
```

The presence of later layers is optional.

## Alternatives Considered

### Alternative 1: Use one generic “assignment” concept

Rejected.

A single record would blur:

* named function;
* specific obligation;
* unit of work;
* and demonstrated action.

It would make it difficult to determine whether a record described intent or evidence.

### Alternative 2: Treat roles as collections of responsibilities

Rejected as the universal model.

Some Roles imply general functions without enumerated obligations, and several Responsibilities may exist without a named Role.

Roles and Responsibilities may be linked, but neither should be structurally reduced to the other.

### Alternative 3: Treat tasks as responsibilities

Rejected.

A Task or Work Item identifies the work itself.

A Responsibility identifies who is expected to act in relation to that work.

One Work Item may have several assignees or changing assignees, so the two concepts require separate identity.

### Alternative 4: Treat completed tasks as contributions

Rejected.

Completion status does not identify:

* who actually performed the work;
* who assisted;
* what quality was achieved;
* whether the task was shared;
* or whether useful Contributions occurred despite noncompletion.

Contribution requires evidence.

### Alternative 5: Infer contribution from assigned responsibility

Rejected.

Assignment records intention, not performance.

The student may:

* be absent;
* encounter a blocker;
* exchange Responsibilities;
* receive help;
* or contribute elsewhere.

### Alternative 6: Infer contribution from Artifact authorship

Rejected.

The recorder or writer may be documenting work performed by several participants.

Conversely, a participant may contribute substantially without authoring an Artifact.

### Alternative 7: Infer contribution from digital file ownership

Rejected.

Account, repository, or file ownership does not establish who designed, tested, reviewed, explained, or integrated the work.

External provenance may support review but does not settle Contribution automatically.

### Alternative 8: Record only final-product contributions

Rejected.

This would undervalue:

* planning;
* questioning;
* measurement;
* testing;
* debugging;
* coordination;
* integration;
* peer support;
* verification;
* and response to failure.

Concord must support process Contributions as well as product Contributions.

### Alternative 9: Make Work Items mandatory for every Activity

Rejected.

Seminars and many short collaborative Activities do not require task decomposition.

Work Items remain optional contextual extensions.

### Alternative 10: Turn Concord into a full project-management system

Rejected.

Concord documents collaborative evidence.

It does not need comprehensive:

* scheduling;
* workload balancing;
* resource management;
* time tracking;
* sprint planning;
* or project forecasting.

### Alternative 11: Accept student Contribution Claims without review

Rejected.

Claims may be incomplete, disputed, self-serving, or based on different understandings of the work.

Student-created claims remain evidence subject to human review and, where necessary, moderation.

## Required Follow-Up

Later conceptual contracts must define:

* Role reference and Role Assignment structure;
* Responsibility Assignment structure;
* Work Item and optional dependency structure;
* Contribution Claim structure;
* Contribution category representation;
* assignment, completion, blocked, and reassignment statuses;
* links among Responsibilities, Work Items, Activity Events, Artifacts, and Attachments;
* handoff representation;
* moderation requirements;
* correction and supersession behavior;
* and how these records may support Score Evidence Links.

Representative contract examples should test at least:

* one Role with several Responsibilities;
* one Responsibility without a named Role;
* one shared Responsibility;
* one Work Item with changing assignees;
* one participant contributing outside an assigned Role;
* one incomplete Work Item with useful Contributions;
* one blocked Responsibility caused by an external dependency;
* one handoff involving two participants or subteams;
* one disputed Contribution Claim;
* one less-visible testing or coordination Contribution;
* and one Artifact whose author is not the only contributor to the documented work.

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

## Notes

This ADR distinguishes intended organization from demonstrated work.

It does not define the complete source-evidence retention and correction model, which is addressed in ADR 0007. It also does not define the many-to-many relationship between evidence and Scores, which is addressed in ADR 0009.
