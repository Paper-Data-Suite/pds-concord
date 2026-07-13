# ADR 0013: Keep Activity-Specific Structures Optional

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Concord supports several kinds of collaborative classroom Activities.

Representative cases include:

* Socratic seminars;
* laboratory investigations;
* collaborative programming projects;
* engineering challenges;
* debates;
* literature circles;
* peer-review workshops;
* design activities;
* and other teacher-defined collaborative work.

These Activities share a common evidence workflow, but they do not share every internal structure.

For example, a seminar may use:

* participant and observer rotations;
* discussion moves;
* observer-target pairings;
* a discussion map;
* and a Group process review.

A laboratory investigation may use:

* trials;
* apparatus or material references;
* measurement tables;
* invalid-trial reasons;
* troubleshooting events;
* and equipment-failure context.

A programming or engineering project may use:

* milestones;
* components;
* subteams;
* Work Items;
* dependencies;
* handoffs;
* build or prototype labels;
* testing events;
* external project Artifacts;
* and revision history.

These structures are useful when they match the Activity.

They become harmful when the system requires them universally.

A teacher conducting a one-period discussion should not have to create:

* milestones;
* tasks;
* dependencies;
* handoffs;
* contribution claims;
* external Artifact references;
* or project components

merely to generate and review one discussion map.

Likewise, a teacher conducting a short laboratory activity should not be required to model:

* formal subteams;
* project phases;
* Work Item hierarchies;
* or long-running milestone records

unless those concepts are relevant.

The opposite design failure is also possible.

If every Activity-specific concept is stored only as unstructured notes or template-specific text, Concord cannot reliably:

* link evidence to a milestone;
* preserve changing task assignments;
* represent blocked dependencies;
* identify a troubleshooting event;
* associate an Attachment with a component;
* or reuse the same concept across several packet types.

Concord therefore needs a layered domain model that supports recurring structures without forcing them into every Activity.

## Decision

Concord will distinguish among:

1. **universal capabilities** supported by the foundational domain;
2. **common optional concepts** that may be instantiated when an Activity requires them; and
3. **activity-specific extensions** that normally remain in templates, configurable vocabularies, Artifact subtypes, or namespaced extension data.

The base Activity model will remain stable and broadly applicable.

Activity-specific complexity will be added progressively rather than imposed universally.

The conceptual layering is:

```text
Universal Activity and evidence model
    -> optional reusable context concepts
        -> activity-specific templates and vocabularies
```

## Capability Versus Record Presence

A capability being universal does not mean that every Activity must contain a record of that type.

For example, Concord must universally support:

* Groups;
* Group Memberships;
* Role Assignments;
* Artifact Review;
* Moderation;
* Criteria;
* Score Records;
* and External References.

However, a particular Activity may contain:

* no explicit Groups;
* no Role Assignments;
* no Moderation Records;
* no Scores;
* and no External References.

The distinction is:

> The domain must be capable of representing the concept when needed, but an Activity must not create meaningless records merely to satisfy the model.

### Required Activity records

Every Activity requires:

* durable Activity identity;
* Activity lifecycle state;
* relevant Core class or assignment-routing context;
* and one or more explicit Sessions.

Other records are required only when the selected Activity configuration or evidence workflow uses them.

### Conditionally required records

Some records become required because another selected record depends on them.

Examples include:

* a Group Membership requires a Group and effective Session context;
* a child Group requires a parent Group;
* a Work-Item Dependency requires two Work Items;
* a Score Record requires one Criterion and one Scoring Scale revision;
* a Score Evidence Link requires one Score Record and one Evidence Reference;
* and a generated Artifact Instance requires an exact Template Version.

Conditional requirements must be validated without making the concepts universally mandatory.

## Minimum Activity Structure

A simple Concord Activity may contain only:

```text
Activity
└── Session
    └── one or more generated Artifacts
        └── optional Review and Scores
```

For example, a teacher may create:

* one Activity;
* one Session;
* one teacher observation tracker;
* one Group-level discussion map;
* and several later individual Scores.

That Activity does not require:

* Activity Markers;
* Work Items;
* dependencies;
* handoffs;
* contribution claims;
* subteams;
* external Artifacts;
* or formal responsibility tracking.

The absence of those structures is valid and intentional.

## Progressively Structured Activities

A more structured Activity may add only the concepts it needs.

For example:

```text
Activity
├── Sessions
├── Groups and Memberships
├── Role Assignments
├── Responsibility Assignments
├── Artifacts
└── Reviews and Scores
```

A long-running project may add further context:

```text
Activity
├── Sessions
├── Groups
│   └── child Groups or subteams
├── Activity Markers
├── Work Items
│   └── Work-Item Dependencies
├── Activity Events
├── Contribution Claims
├── Attachments and External References
├── Artifacts
└── Reviews, Moderation, and Scores
```

The second model extends the first.

It does not replace it with a separate incompatible Activity architecture.

## Universal Foundational Concepts

The foundational Concord domain must support the concepts established by the preceding ADRs, including:

* Activity;
* explicit Session;
* Activity-specific Group;
* Group Membership;
* Role Assignment;
* reusable Template Definition and immutable Template Version;
* Packet Definition and Packet Instance;
* Artifact Instance and Artifact Page;
* Artifact Author;
* Artifact Subject;
* Scan Reference;
* Artifact Review;
* Moderation Record;
* Correction and supersession history;
* Criterion Set;
* Criterion;
* Scoring Scale;
* Score Record;
* Score Evidence Link;
* External Reference;
* privacy;
* and explicit non-score dispositions.

Universal support does not imply universal instantiation.

For example:

* every Activity has a Session;
* not every Activity has a Score;
* every evidence-bearing Artifact can be reviewed;
* not every Artifact requires Moderation;
* every Activity may use Groups;
* not every Activity requires explicit Group records;
* and every Score may link to evidence;
* not every Score requires a formal Evidence Reference when teacher rationale and provenance are sufficient.

## Common Optional Concepts

The following concepts recur across several Activity types and belong in the Concord domain as optional structures.

### Responsibility Assignment

A Responsibility Assignment records a specific obligation assigned to:

* participant;
* Group;
* or child Group.

It is useful when the Activity explicitly divides work.

It is not required when:

* roles provide enough structure;
* the Activity is informal;
* the teacher does not need assignment-level evidence;
* or responsibilities are not relevant to the selected Criteria.

Responsibility Assignment remains distinct from:

* Role Assignment;
* Work Item;
* Contribution;
* and Score.

### Activity Marker

An Activity Marker provides an ordered or named context within an Activity.

Possible marker types include:

* phase;
* stage;
* milestone;
* checkpoint;
* rotation;
* or iteration.

An Activity Marker may be used when a named progression matters.

It is not required merely because the Activity has several Sessions.

Sessions represent occurrences.

Markers represent an optional instructional or work-structure context.

### Work Item

A Work Item represents a bounded unit of collaborative work, such as:

* task;
* component;
* deliverable;
* test;
* research question;
* construction step;
* or project element.

Work Items may contextualize:

* Responsibilities;
* Artifacts;
* Attachments;
* Activity Events;
* Contribution Claims;
* and Scores.

They are not required for Activities that do not need task decomposition.

### Work-Item Dependency

A Work-Item Dependency represents a relationship between two Work Items.

It is useful when:

* one component depends on another;
* one student or subteam must complete a handoff;
* delayed work blocks another Work Item;
* or dependency management is relevant evidence.

Dependencies are not required for every Work Item.

An Activity with Work Items may contain no dependency records.

### Activity Event

An Activity Event represents a meaningful evidence-bearing occurrence.

Possible event types include:

* decision;
* troubleshooting episode;
* test;
* invalid trial;
* revision;
* handoff;
* teacher intervention;
* interruption;
* or another teacher-defined occurrence.

An Activity should not create an Event for every routine action.

Events are appropriate when the occurrence is useful for:

* evidence;
* chronology;
* explanation;
* or later Scoring.

### Contribution Claim

A Contribution Claim records a statement that a participant or Group made a particular Contribution.

It is useful when:

* contribution is not otherwise visible;
* several participants dispute what occurred;
* a retrospective identifies important work;
* or one participant records work completed by another.

Contribution Claims are not required for every participant or Activity.

When present, they remain:

* evidence;
* reviewable;
* potentially subject to Moderation;
* and distinct from Scores.

### Attachment

An Attachment represents physical or digital work associated with the Activity but not generated as a normal Concord Artifact Page.

Examples include:

* poster;
* photograph;
* graph paper;
* screenshot;
* printed source code;
* project diagram;
* external worksheet;
* or digital file.

Attachments are optional.

A paper-only Activity using only Concord-generated Artifacts does not need them.

### Child Groups or subteams

Temporary subteams may be represented as child Groups.

They are useful when a parent Group divides into smaller collaborative units with their own:

* Memberships;
* Responsibilities;
* Artifacts;
* events;
* or evidence.

A Group does not require child Groups merely because its members perform different work.

### Consensus or representation status

A Group-authored Artifact may optionally identify whether it represents:

* unanimous agreement;
* majority agreement;
* recorder summary;
* several individual positions;
* or no consensus.

This structure is useful for Group reviews, decisions, and retrospectives.

It is not required for every Group Artifact.

### Continuation pages and long-lived logs

Some Artifacts continue across:

* several pages;
* Sessions;
* trials;
* milestones;
* or project phases.

Continuation-page and long-lived-log structures are optional capabilities.

A one-page Artifact should not require placeholder continuation records.

### Contextual exception reasons

Detailed causes such as:

* equipment failure;
* interrupted work;
* invalid trial;
* blocked dependency;
* or external-tool failure

may be recorded when relevant.

They are not required for every non-score disposition or incomplete Work Item.

## Optional Does Not Mean Unstructured

An optional concept remains a defined domain concept when it is used.

For example, an optional Work Item must still have:

* durable identity;
* parent Activity;
* valid lifecycle state;
* and valid references.

An optional Activity Marker must still have:

* parent Activity;
* type;
* label;
* sequence;
* and appropriate historical behavior.

An optional Activity Event must still preserve:

* Activity context;
* event type;
* chronology;
* contributors or Subjects where applicable;
* and supersession history.

Optional records must not become arbitrary dictionaries with no validation simply because they are not universally required.

## Optional Does Not Mean Disposable

When an optional record becomes part of the evidence chain, it must follow the same historical-preservation rules as universal records.

For example:

* a milestone cited by a Score;
* a Work Item linked to a Responsibility;
* a dependency used to explain blocked work;
* an Event cited as evidence;
* a Contribution Claim used during Moderation;
* or an Attachment supporting a Score

must not be silently rewritten or deleted.

Corrections and supersession must preserve the earlier state where it was durable or consequential.

## No Placeholder Records

Concord must not create meaningless placeholder records such as:

* milestone `none`;
* Work Item `general`;
* dependency `not applicable`;
* synthetic subteam;
* empty Contribution Claim;
* Activity Event `other` with no description;
* or Attachment with no identified object

merely to satisfy a schema.

When an optional concept is unused, the corresponding relationship should be absent.

The system should not confuse:

* no record because the concept was not used;
* missing record because required configuration is incomplete;
* and unavailable evidence.

Those states have different meanings.

## Template-Declared Context Requirements

A Template Version or Packet Component may declare that it requires certain context.

For example:

* a milestone retrospective may require an Activity Marker;
* a responsibility map may require Group or participant assignments;
* a testing log may optionally use Work Item and build labels;
* a handoff form may require contributor and recipient references;
* and an Artifact Cover Sheet may require an Attachment or External Reference.

Generation should validate the context required by the selected template.

This does not make that context required for unrelated templates or Activities.

### Required and optional bindings

A Template Version may classify a context binding as:

* required;
* optional;
* repeatable;
* or unsupported.

For example:

```text
Template:
Project Milestone Retrospective

Required:
- Activity
- Session
- Group
- Activity Marker of type milestone

Optional:
- Work Items
- Attachments
- Contribution Claims
```

The final contract may encode these requirements through:

* template metadata;
* packet-component generation rules;
* or another validated configuration mechanism.

### No silent fabrication

When required template context is missing, Concord should:

* request the missing configuration;
* prevent invalid generation;
* or allow the teacher to choose another template.

It must not silently fabricate a milestone, Group, Work Item, or participant.

## Activity Type Is Classification, Not a Mandatory Schema

An Activity may have a teacher-facing type or category such as:

* seminar;
* laboratory;
* project;
* debate;
* design challenge;
* or other.

That classification may assist with:

* template discovery;
* default packet suggestions;
* terminology;
* and interface organization.

It must not force every Activity of that type into one rigid schema.

For example:

* not every seminar uses inner and outer circles;
* not every laboratory uses numbered trials;
* not every project uses milestones;
* not every engineering challenge uses subteams;
* and not every debate uses the same speaking roles.

Activity type is guidance and configuration context.

It is not a substitute for the actual records selected by the teacher.

## No Activity-Type Inheritance Hierarchy

The initial architecture will not require separate foundational entities such as:

* `SeminarActivity`;
* `LaboratoryActivity`;
* `ProgrammingProjectActivity`;
* `EngineeringActivity`;
* or `DebateActivity`.

All use the common Activity model.

Activity-specific behavior should normally be supplied through:

* selected Template Versions;
* Packet Definitions;
* optional domain records;
* activity-specific vocabularies;
* and namespaced extension data.

A specialized first-class entity may be introduced later only when contract examples demonstrate behavior that cannot be represented accurately through the shared model.

## Activity-Specific Extensions

Concepts that are narrow to one Activity family should normally remain outside the mandatory base schema.

### Seminar-specific extensions

Examples include:

* inner-circle and outer-circle labels;
* discussion-move vocabulary;
* speaker-response mapping;
* observer-target pairing rules;
* seminar text references;
* and discussion-map legends.

These may live in:

* Template Version configuration;
* Artifact subtype metadata;
* role vocabularies;
* Activity Marker types;
* or namespaced seminar extension data.

### Laboratory-specific extensions

Examples include:

* trial numbering;
* apparatus references;
* material or sample labels;
* measurement-table structure;
* invalid-trial reasons;
* routine safety prompts;
* and procedure-specific organizer fields.

The base model may provide:

* Activity Markers;
* Work Items;
* Events;
* Attachments;
* and contextual exception reasons.

It should not require apparatus or sample fields for non-laboratory Activities.

### Programming- or engineering-specific extensions

Examples include:

* build labels;
* prototype identifiers;
* test-case fields;
* regression labels;
* defect severity;
* integration terminology;
* repository locations;
* CAD references;
* and design-review fields.

These may use:

* Work Items;
* Events;
* Attachments;
* External References;
* and teacher-defined vocabularies.

Concord must not make software- or engineering-specific terminology universal.

## Configurable Vocabularies

Many Activity-specific values should be configurable rather than fixed in the base schema.

Examples include:

* role names;
* contribution categories;
* Event types;
* Work Item types;
* Activity Marker types;
* consensus statuses;
* exception reasons;
* test-result labels;
* and activity-specific decision statuses.

A configurable vocabulary should provide stable keys and teacher-facing labels where records need durable meaning.

The schema should not require a new field every time a teacher introduces a new classroom term.

### Stable semantics

Configurable values should not become uncontrolled prose when they are used for:

* filtering;
* validation;
* linking;
* Scoring;
* or history.

The contract may distinguish:

* stable system-defined values;
* Activity-defined values;
* Template-defined values;
* and free-text descriptions.

## Namespaced Extension Data

Some narrowly activity-specific data may remain in a namespaced extension structure.

For example:

```text
extension namespace:
concord.seminar

data:
- rotation structure
- discussion-map legend
```

or:

```text
extension namespace:
concord.lab

data:
- apparatus label
- sample identifier
- trial condition
```

Namespaced extension data must be:

* explicitly associated with a record;
* versioned or contract-qualified;
* validated when a contract exists;
* preserved historically when consequential;
* and ignored safely by implementations that do not understand it.

### Extension data must not replace foundational concepts

A foundational concept should not be hidden inside extension data merely to avoid defining it properly.

For example:

* Group Membership belongs in the Group Membership model;
* Artifact Subject belongs in the Artifact Subject model;
* Score belongs in the Score Record model;
* and an evidence link belongs in the Score Evidence Link model.

Extension data is appropriate for narrow details, not for bypassing shared contracts.

## Promotion to a Common Concept

An activity-specific structure may later be promoted into a common optional domain concept.

Promotion should be considered when the structure:

* recurs across several Activity families;
* requires durable identity;
* has its own lifecycle;
* is referenced by several other records;
* requires correction or supersession;
* participates in privacy or provenance;
* or cannot be represented safely as template metadata.

For example, Work Items are common optional concepts because they may be referenced by:

* Responsibilities;
* Events;
* Attachments;
* Contribution Claims;
* Artifacts;
* and Scores.

A narrow seminar legend does not currently require that level of domain identity.

Promotion should require:

* representative contract examples;
* documented semantics;
* migration implications;
* and an ADR when the architectural effect is significant.

## Common Event Envelope

The initial model will prefer one common Activity Event envelope over a separate first-class entity for every event type.

For example, the following may initially share one structure:

* decision;
* test;
* troubleshooting episode;
* revision;
* handoff;
* interruption;
* teacher intervention;
* and invalid trial.

The shared envelope may contain:

* event identity;
* type;
* Activity and optional Session;
* optional Group, Marker, or Work Item;
* contributors;
* Subjects;
* concise description;
* status or outcome;
* chronology;
* and supersession.

Type-specific details may remain in:

* Artifact records;
* validated extension data;
* or event-specific metadata.

A dedicated entity should be introduced only when a type develops materially different:

* identity;
* lifecycle;
* relationships;
* validation;
* privacy;
* or evidence behavior.

## User-Interface Progressive Disclosure

Teacher-facing interfaces should expose complexity progressively.

A simple Activity workflow should emphasize:

* Activity;
* Session;
* participants or Groups where needed;
* selected templates;
* packet generation;
* scan intake;
* Review;
* and optional Scoring.

Additional controls should appear only when the teacher uses features such as:

* milestones;
* subteams;
* Responsibilities;
* Work Items;
* dependencies;
* contribution tracking;
* external Artifacts;
* or Activity Events.

### Defaults

Defaults should reduce burden without creating false records.

For example, Concord may:

* create the required default Session;
* copy Group Memberships forward as a proposed configuration;
* suggest a packet based on Activity type;
* or offer a concise role vocabulary.

It should not automatically create:

* project phases;
* tasks;
* dependencies;
* contribution claims;
* subteams;
* or Scores.

### Editing complexity

A teacher should be able to begin with a simple Activity and add structure later.

For example:

```text
Initial configuration:
Activity + Session + Groups

Later addition:
Milestone markers

Later addition:
Work Items and dependencies
```

Adding optional structure must not require replacing the Activity or invalidating earlier evidence.

Earlier records retain the context that existed when they were created.

## Query and Reporting Behavior

Queries must distinguish between:

* the concept being unsupported;
* the concept being supported but unused;
* the record being expected but missing;
* and the record existing but being unavailable or superseded.

For example:

* no Work Items may mean the Activity did not use task decomposition;
* an expected Work Item with no completion evidence is a different condition;
* and a superseded Work Item remains historical.

Reports and exports should not imply that an absent optional record represents:

* nonperformance;
* incomplete configuration;
* or missing evidence

unless the relevant contract explicitly establishes that expectation.

## Contract and Serialization Principles

Later contracts should follow these principles:

### Omitted optional collections

A valid Activity may contain zero records of an optional type.

Contracts should not require placeholder objects.

### Valid references

When optional records are present, references must resolve to compatible records.

Examples include:

* Activity Marker belongs to the same Activity;
* Work Item belongs to the same Activity;
* dependency endpoints belong to the same Activity unless a later contract explicitly permits otherwise;
* child Group and parent Group belong to the same Activity;
* and Event context must be compatible with its Activity and Session.

### Stable identity

Optional records that may be referenced elsewhere require durable identifiers.

### Historical behavior

Optional records used by durable evidence or Scores require correction and supersession history.

### Versioned extension contracts

Namespaced extension data should identify the applicable contract or schema revision when validation depends on it.

### Safe ignorance

An implementation that does not understand a particular optional extension should preserve it without:

* interpreting it incorrectly;
* deleting it;
* or treating the complete parent record as invalid solely because of an unknown noncritical extension.

## Boundaries

Keeping Activity-specific structures optional does not mean that Concord should become:

* a generic project-management system;
* a lesson-planning system;
* a laboratory-information-management system;
* a source-control system;
* a CAD manager;
* an LMS;
* a behavior-monitoring platform;
* or an unrestricted schema-building framework.

Optional structures exist to contextualize collaborative evidence.

They should remain no more detailed than required for:

* generation;
* routing;
* Review;
* Moderation;
* Scoring;
* provenance;
* and teacher interpretation.

## Consequences

### Positive consequences

* Simple Activities remain simple.
* Teachers are not required to configure irrelevant project structures.
* Seminars, laboratories, and projects share one foundational model.
* Common recurring concepts can be referenced consistently.
* Activity-specific vocabulary does not pollute the universal schema.
* New Activity types can be supported without redesigning the entire domain.
* Teachers can add complexity progressively.
* Templates may validate only the context they actually require.
* Optional structures retain stable identity and provenance when used.
* Concord avoids becoming a general project-management application.
* The architecture supports future promotion of recurring structures.
* Implementations can provide focused interfaces for different Activity types without fragmenting the underlying records.

### Negative consequences

* Implementations must handle many valid combinations of record presence.
* Template generation requires context-requirement validation.
* Queries cannot assume that milestones, tasks, Events, or Attachments exist.
* Activity-specific extensions require naming and versioning discipline.
* Different templates may use different optional context combinations.
* User interfaces must balance discoverability with progressive disclosure.
* Promoting an extension to a common concept may require migration.
* Generic Events may eventually prove too broad for some specialized cases.
* Testing must cover simple, intermediate, and complex Activities.
* Export consumers must tolerate absent optional structures.

### Implementation consequences

Implementations must:

* distinguish capability support from record presence;
* enforce one or more Sessions without requiring unrelated structures;
* permit zero Groups, Roles, Scores, Moderation Records, and External References where valid;
* implement optional Responsibility Assignments;
* implement optional Activity Markers;
* implement optional Work Items and dependencies;
* implement optional Activity Events;
* implement optional Contribution Claims;
* implement optional Attachments;
* support child Groups without requiring them;
* validate template-declared context requirements;
* prohibit placeholder records;
* preserve optional-record history when consequential;
* support configurable vocabularies;
* support namespaced extension data safely;
* and present advanced structures through progressive disclosure.

Implementations should test capability combinations rather than assuming one canonical Activity shape.

## Alternatives Considered

### Alternative 1: Require every domain concept for every Activity

Rejected.

This would force teachers to create irrelevant:

* Groups;
* Roles;
* Responsibilities;
* milestones;
* tasks;
* Events;
* Attachments;
* and Scores.

The resulting records would add burden without improving evidence quality.

### Alternative 2: Use one maximal Activity schema with every possible field

Rejected.

A maximal schema would contain large numbers of:

* null fields;
* empty collections;
* activity-specific columns;
* and misleading placeholders.

It would also become difficult to evolve safely.

### Alternative 3: Create a separate Activity entity for every Activity type

Rejected.

Separate seminar, laboratory, debate, programming, and engineering models would duplicate:

* Sessions;
* Groups;
* Artifacts;
* Review;
* Moderation;
* Scoring;
* and provenance.

Cross-Activity tools would require type-specific logic for every operation.

### Alternative 4: Store all optional structure in one unvalidated metadata object

Rejected.

That would prevent reliable:

* references;
* validation;
* history;
* filtering;
* evidence linkage;
* and migration.

Recurring concepts require explicit optional domain records.

### Alternative 5: Make Work Items mandatory

Rejected.

Many seminars, discussions, and short collaborative Activities do not require task decomposition.

### Alternative 6: Treat Sessions as optional like other structures

Rejected.

Every Activity requires one or more explicit Sessions under ADR 0003.

Sessions provide the consistent occurrence context on which other optional records may depend.

### Alternative 7: Infer milestones, tasks, or Events from Artifact text

Rejected.

Concord does not interpret handwriting or arbitrary content automatically.

Contextual structures must be configured or recorded explicitly.

### Alternative 8: Use free-text labels instead of common optional concepts

Rejected as the sole model.

Free text may describe a task or milestone but cannot provide:

* durable identity;
* cross-record references;
* lifecycle;
* dependency relationships;
* or supersession.

### Alternative 9: Put all subject-specific fields into the base schema

Rejected.

Fields such as:

* apparatus;
* sample;
* test-case severity;
* speaker-response move;
* or repository path

do not apply universally.

### Alternative 10: Require a new ADR and entity for every new template field

Rejected.

Templates and namespaced extensions need room for narrow, validated variation.

Only structures with significant cross-domain or lifecycle implications require promotion into the common model.

### Alternative 11: Create feature flags without explicit records

Rejected.

A flag such as `uses_milestones: true` does not identify:

* the milestones;
* their order;
* their status;
* or their relationships.

Feature declarations may assist interfaces, but actual domain meaning requires records.

### Alternative 12: Allow optional records to be overwritten freely

Rejected.

Optional records may become consequential evidence context.

Their history must be preserved when relied upon.

### Alternative 13: Implement a full project-management model

Rejected.

Concord’s Work Items, dependencies, and milestones exist to contextualize evidence.

They do not justify adding:

* resource planning;
* time sheets;
* workload forecasting;
* sprint management;
* automated scheduling;
* or portfolio management.

### Alternative 14: Require every template to support every context type

Rejected.

Templates should declare only the context they use.

A peer observation form does not need project dependency fields, and a testing log does not need seminar discussion-move fields.

## Required Follow-Up

Later conceptual contracts must define:

* the minimum valid Activity structure;
* which universal records are required versus merely supported;
* optional-record presence semantics;
* Responsibility Assignment fields;
* Activity Marker fields and types;
* Work Item fields and hierarchy;
* Work-Item Dependency fields;
* Activity Event envelope;
* Contribution Claim fields;
* Attachment fields;
* child-Group validation;
* consensus or representation status;
* continuation-page and long-lived-log behavior;
* configurable vocabulary structure;
* namespaced extension representation;
* extension schema versioning;
* unknown-extension preservation;
* template context requirements;
* Packet Component generation rules;
* validation when required context is missing;
* progressive-disclosure interface behavior;
* and criteria for promoting an extension into a common domain concept.

Representative contract examples should test at least:

* one minimal one-Session Activity;
* one Activity with no explicit Groups;
* one Activity with Groups but no Role Assignments;
* one seminar with rotations but no Work Items;
* one laboratory Activity with trials and equipment context but no milestones;
* one project with milestones but no dependencies;
* one project with Work Items and dependencies;
* one temporary child Group;
* one Activity Event with activity-specific extension data;
* one Contribution Claim requiring Moderation;
* one Attachment linked to a Work Item;
* one Template Version requiring an Activity Marker;
* one Packet Component with optional Work Item context;
* one invalid generation attempt missing required template context;
* one Activity that adds optional structure after earlier evidence exists;
* one unknown extension preserved by a compatible implementation;
* and one optional structure later promoted into a shared contract without rewriting historical evidence.

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
* [`docs/decisions/0010-exceptional-evidence-states-are-not-low-scores.md`](0010-exceptional-evidence-states-are-not-low-scores.md)
* [`docs/decisions/0011-link-external-artifacts-without-managing-source-systems.md`](0011-link-external-artifacts-without-managing-source-systems.md)
* [`docs/decisions/0012-link-scoreform-and-quillan-without-duplication.md`](0012-link-scoreform-and-quillan-without-duplication.md)

## Notes

This ADR completes the initial set of foundational Concord architecture decisions.

It establishes the layering principle that should guide the next contract phase:

```text
stable universal model
    + optional reusable concepts
    + activity-specific extensions
```

The exact JSON schemas, storage layout, command surfaces, and interface flows remain implementation and contract decisions.
