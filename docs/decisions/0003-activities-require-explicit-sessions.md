# ADR 0003: Activities Require Explicit Sessions

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

A Concord Activity represents an already-planned collaborative classroom undertaking, such as:

* a Socratic seminar;
* a laboratory investigation;
* a collaborative programming project;
* a design challenge;
* a debate;
* or another group task.

Some Activities occur during one class period. Others continue across several periods, rotations, workdays, or checkpoints.

Across the representative packet models, important collaborative context can change while the broader Activity remains the same.

Examples include:

* seminar participants rotating between observer and participant roles;
* laboratory students changing responsibilities between trials;
* students joining late or leaving early;
* Groups being merged or reassigned;
* project Groups creating temporary subteams;
* work moving from design to testing or revision;
* an Artifact being completed during one work period and reviewed during another;
* and evidence or Scores referring to a particular occurrence rather than the Activity as a whole.

If Sessions are optional, implementations must support two competing representations:

1. one-period Activities with context attached directly to the Activity; and
2. multi-period Activities with context attached to a Session.

That would create ambiguity and repeated special cases in:

* Group Membership;
* Role Assignment;
* Responsibility Assignment;
* Artifact generation and routing;
* evidence provenance;
* chronology;
* absence and participation status;
* and scoring context.

A consistent Activity-to-Session structure is therefore required.

## Decision

Every Concord Activity will contain **one or more explicit Sessions**.

A Session represents one occurrence, rotation, meeting, work period, or other bounded participation context within an Activity.

The minimum relationship is:

```text id="6qjv3t"
Activity
└── Session 1
```

A multi-period Activity may contain:

```text id="vcot46"
Activity
├── Session 1
├── Session 2
├── Session 3
└── Session 4
```

### Session identity

Every Session must have its own durable `session_id`.

A Session belongs to exactly one Activity.

A Session should carry enough information to establish its place within that Activity, including:

* parent `activity_id`;
* stable ordering or sequence;
* optional date and time context;
* optional teacher-facing label;
* lifecycle status;
* and optional contextual notes.

A date or timestamp alone is not a substitute for Session identity.

### Single-period activities

A one-period Activity still has one explicit Session.

The teacher should not be required to perform unnecessary configuration merely to satisfy this rule. An implementation may automatically create a default Session when an Activity is created.

For example:

```text id="4prmwe"
Activity: Period 2 Socratic Seminar
Session: Seminar Session 1
```

The automatically created Session remains a normal first-class record. It is not a nullable placeholder or an implementation-only fiction.

### Multi-period activities

A multi-period Activity has a distinct Session for each meaningful occurrence or work period.

Examples include:

```text id="otfw66"
Laboratory Activity
├── Session 1: Setup and Initial Trials
└── Session 2: Revised Trials and Review
```

```text id="3pgg09"
Programming Project
├── Session 1: Requirements and Design
├── Session 2: Implementation
├── Session 3: Testing and Revision
└── Session 4: Final Demonstration
```

Session boundaries should reflect meaningful classroom occurrences. Concord does not require a new Session for every minor task, decision, or change within one work period.

### Session ordering

Sessions must have an explicit and stable order within their parent Activity.

Chronology must not depend only on:

* filenames;
* scan order;
* creation timestamps;
* or display labels.

A sequence value or equivalent ordering contract must allow Concord to reconstruct the intended Activity chronology.

Dates and times may supplement that ordering but are not sufficient by themselves.

### Session-contextual records

A Session may contextualize:

* Group Memberships;
* Role Assignments;
* Responsibility Assignments;
* temporary child Groups or subteams;
* Packet Instances;
* Artifact Instances;
* Activity Events;
* evidence;
* Reviews;
* Score Records;
* and exception states.

A participant may therefore:

* belong to one Group in Session 1 and another Group in Session 2;
* serve as an observer during one rotation and a participant during another;
* receive a responsibility in one Session and have it reassigned later;
* be absent for one Session while participating in the rest of the Activity;
* or contribute to different project components across Sessions.

Earlier Session records must remain unchanged when later context changes.

### Activity-wide records

Requiring Sessions does not mean that every Concord record must belong to exactly one Session.

Some records may concern:

* the entire Activity;
* several Sessions;
* a Group across the Activity;
* a long-running Artifact;
* or a final cumulative Score.

Examples include:

* an Activity-wide criterion set;
* a project responsibility map that continues across Sessions;
* a Group retrospective covering several work periods;
* or a final collaborative outcome Score.

Such records may remain Activity-wide or reference several Sessions where the later contract permits it.

The decision requires an explicit Session structure for every Activity. It does not force every record into one and only one Session.

### Sessions are not stages or milestones

A Session represents an occurrence or work period.

It is distinct from:

* a stage;
* a phase;
* a milestone;
* a checkpoint;
* a trial;
* an iteration;
* or a task.

These concepts may overlap in practice but are not interchangeable.

For example:

* one Session may contain several laboratory trials;
* one project milestone may span several Sessions;
* one Session may include design, testing, and revision;
* and one seminar Session may contain several rotations.

Optional Activity Markers or Work Items may represent those other structures without replacing Sessions.

### Sessions are not lesson plans

A Session does not define:

* instructional objectives;
* teaching procedures;
* detailed timing;
* materials;
* differentiation;
* or lesson-plan content.

Those concerns remain teacher-, curriculum-, or future lesson-planning-module responsibilities.

Concord stores only enough Session context to generate, route, review, and score collaborative evidence.

### Relationship to Core

Sessions are Concord-owned Activity context.

They are not permanent additions to:

* the Core class roster;
* a school timetable;
* or a shared calendar.

A Session may reference Core class and assignment-routing context through its parent Activity, but Core does not own Concord’s Session lifecycle.

## Consequences

### Positive consequences

* One-period and multi-period Activities use the same conceptual structure.
* Group Membership, roles, responsibilities, Artifacts, and evidence have a consistent contextual anchor.
* Implementations avoid nullable or dual-path Session logic.
* Membership and role changes can be preserved without rewriting earlier records.
* Absence, late arrival, and partial participation can be recorded for the correct occurrence.
* Artifact routing can distinguish pages produced during different work periods.
* Multi-session chronology remains explicit.
* Scores and evidence can refer to a specific occurrence when necessary.
* Long-running Activities can preserve changes in Group structure and responsibility.
* Optional stages, milestones, trials, and tasks can remain separate from occurrence context.

### Negative consequences

* Even a one-period Activity requires a Session record.
* Activity creation may involve one additional generated identifier and record.
* Implementations must maintain Session ordering.
* Teachers may see what appears to be redundant Session information for simple Activities.
* Records covering several Sessions require a deliberate Activity-wide or multi-session representation.
* Changing an Activity’s planned schedule may require updating Session metadata without changing Session identity.

### Implementation consequences

Implementations must:

* create at least one Session for every Activity;
* prevent an Activity from reaching an active state without a Session;
* assign each Session a durable identifier;
* preserve Session order;
* allow optional date, time, and labels;
* allow Groups and participant context to vary by Session;
* preserve earlier Session records after later changes;
* distinguish Session context from stages, milestones, trials, and tasks;
* and support Activity-wide records that are not limited to one Session.

When the teacher creates a simple Activity without configuring Sessions manually, Concord should create a sensible default Session.

## Alternatives Considered

### Alternative 1: Make Sessions optional

Rejected.

This would create two competing models:

* context attached directly to an Activity for simple cases; and
* context attached to Sessions for complex cases.

Every relationship involving membership, roles, Artifacts, evidence, or Scores would then need to handle both paths.

The apparent simplicity for one-period Activities would produce greater contract and implementation complexity overall.

### Alternative 2: Create Sessions only for multi-period Activities

Rejected.

This retains the same dual model as optional Sessions and makes an Activity’s structure change if it later expands from one period to several.

A teacher might begin with a one-day plan and continue the Activity the next day. The system would then need to migrate existing Activity-level context into a newly created Session.

Explicit Sessions from the beginning avoid that migration.

### Alternative 3: Use the Activity itself as the first Session

Rejected.

An Activity and a Session have different meanings and lifecycles:

* the Activity represents the complete collaborative undertaking;
* the Session represents one occurrence within it.

Treating the Activity as both concepts would make later expansion ambiguous and complicate references to Activity-wide evidence.

### Alternative 4: Use dates or class periods instead of Session records

Rejected.

Dates and class periods are descriptive values, not durable contextual identities.

They do not adequately support:

* several rotations during one period;
* several simultaneous Groups;
* an unscheduled continuation;
* a Session without a finalized date;
* or corrections to schedule metadata.

Changing a date should not change the identity of the occurrence.

### Alternative 5: Treat each stage, milestone, or trial as a Session

Rejected.

Stages, milestones, and trials describe the structure or progress of work. A Session describes when or during which occurrence that work happened.

The relationships are not consistently one-to-one:

* several trials may occur in one Session;
* one milestone may span several Sessions;
* and one Session may include several stages.

### Alternative 6: Infer Sessions from scanned packets

Rejected.

Scan order and generation timestamps cannot reliably establish the intended classroom occurrence.

Pages may be:

* scanned out of order;
* rescanned later;
* completed across several periods;
* combined in a mixed batch;
* or generated before the Session occurs.

Session context must exist independently of the scan workflow.

## Required Follow-Up

Later conceptual contracts must define:

* required Session fields;
* Session identifier conventions;
* Session lifecycle states;
* stable ordering;
* optional date and time representation;
* default Session creation;
* Session ranges for membership and responsibility records;
* Activity-wide versus Session-specific Artifact context;
* and how much Session context belongs in the shared QR payload versus the linked Artifact record.

The Core integration work must also determine how Concord Session references participate in shared routing without making Sessions a Core-owned roster or scheduling concept.

## References

* [`docs/concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`docs/design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`docs/design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`docs/packet_models/socratic-seminar-packet-model.md`](../packet_models/socratic-seminar-packet-model.md)
* [`docs/packet_models/science-laboratory-group-packet-model.md`](../packet_models/science-laboratory-group-packet-model.md)
* [`docs/packet_models/collaborative-programming_engineering_project_packet_model.md`](../packet_models/collaborative-programming_engineering_project_packet_model.md)
* [`docs/decisions/0001-concord-module-boundaries.md`](0001-concord-module-boundaries.md)
* [`docs/decisions/0002-paper-first-human-reviewed-evidence.md`](0002-paper-first-human-reviewed-evidence.md)

## Notes

This ADR establishes that every Activity has one or more explicit Sessions.

It does not fully define contextual Group Membership, Role Assignment, or temporary subteam behavior. Those decisions are addressed in the next ADR.
