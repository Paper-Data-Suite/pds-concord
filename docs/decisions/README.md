# Concord Documentation

This directory contains the design, architecture, and domain documentation for `pds-concord`.

Concord is the Paper Data Suite module responsible for paper-first evidence generated during collaborative classroom activities. Its documentation defines:

* the module’s scope and boundaries;
* the representative classroom workflows it must support;
* the shared domain concepts used across those workflows;
* the architectural decisions that constrain implementation;
* and the conceptual contracts that will guide schemas, storage, and interfaces.

## Current Status

The initial architecture phase is complete.

The repository now contains:

* a revised conceptual design;
* three representative packet models;
* a cross-case requirements analysis;
* an initial domain model;
* and thirteen accepted Architecture Decision Records.

The next phase should convert those decisions into explicit conceptual contracts and representative serialized examples.

## Recommended Reading Order

Readers approaching Concord for the first time should review the documents in this order.

### 1. Conceptual Design

[`concord-conceptual-design-revised.md`](concord-conceptual-design-revised.md)

Defines:

* Concord’s purpose;
* module boundaries;
* paper-first and human-reviewed principles;
* relationships with Core, ScoreForm, Quillan, and future modules;
* and the major conceptual areas requiring further design.

This is the best starting point for understanding what Concord is intended to do.

### 2. Representative Packet Models

The packet models test the design against concrete classroom cases.

* [`packet_models/socratic-seminar-packet-model.md`](packet_models/socratic-seminar-packet-model.md)
* [`packet_models/science-laboratory-group-packet-model.md`](packet_models/science-laboratory-group-packet-model.md)
* [`packet_models/collaborative-programming_engineering_project_packet_model.md`](packet_models/collaborative-programming_engineering_project_packet_model.md)

These documents show how Concord may support:

* short and long-running Activities;
* changing Groups, Memberships, Roles, and Responsibilities;
* individual, Group, and multi-subject evidence;
* peer and teacher observation;
* troubleshooting, testing, handoffs, and revision;
* external project Artifacts;
* and individual and Group Scoring.

The packet models are representative design cases, not mandatory packet specifications.

### 3. Cross-Case Requirements

[`design/cross-case-requirements.md`](design/cross-case-requirements.md)

Compares the representative packet models and separates their requirements into:

* universal Concord capabilities;
* common optional capabilities;
* activity-specific extensions;
* capabilities owned by other Paper Data Suite modules;
* and capabilities that remain outside Concord.

This document explains why certain concepts belong in the foundational model while others remain optional.

### 4. Initial Domain Model

[`design/initial-concord-domain-model.md`](design/initial-concord-domain-model.md)

Defines the initial conceptual model, including:

* Activities and Sessions;
* Groups, Memberships, Roles, and Responsibilities;
* Templates, Packets, Artifacts, and Pages;
* Authors and Subjects;
* scans, evidence, Review, and Moderation;
* Criteria, Scoring Scales, Scores, and evidence links;
* External References;
* optional Activity context;
* cardinalities;
* lifecycle relationships;
* and major invariants.

The domain model is a design specification. It does not yet prescribe final Python classes, JSON schemas, database tables, or command-line interfaces.

### 5. Architecture Decision Records

[`decisions/README.md`](decisions/README.md)

The Architecture Decision Records establish the accepted constraints that future contracts and implementations must follow.

The ADR set covers:

* module ownership and boundaries;
* paper-first and human-reviewed evidence;
* explicit Sessions;
* contextual collaboration structures;
* Artifact authorship and subject scope;
* Roles, Responsibilities, Tasks, and Contributions;
* source preservation and historical records;
* Review, Moderation, Scoring, Grading, and Reporting;
* evidence-to-Score cardinality;
* exceptional evidence and non-score states;
* external Artifacts and source-system ownership;
* ScoreForm and Quillan integration;
* and optional Activity-specific structures.

When an ADR conflicts with an earlier exploratory design statement, the accepted ADR governs.

## Documentation Structure

```text
docs/
├── README.md
├── concord-conceptual-design-revised.md
├── decisions/
│   ├── README.md
│   └── 0001-... through 0013-...
├── design/
│   ├── cross-case-requirements.md
│   └── initial-concord-domain-model.md
└── packet_models/
    ├── socratic-seminar-packet-model.md
    ├── science-laboratory-group-packet-model.md
    └── collaborative-programming_engineering_project_packet_model.md
```

Future documentation may add directories such as:

```text
docs/
├── contracts/
├── examples/
├── schemas/
└── workflows/
```

Those directories should be introduced only when their contents have a defined purpose and ownership.

## Document Authority

The documents have different roles.

### Accepted ADRs

The ADRs are the current authoritative architectural decisions.

Future implementation and contract work should conform to them unless an ADR is explicitly superseded.

### Conceptual Domain Model

The domain model consolidates the expected concepts, relationships, cardinalities, and lifecycle rules.

It should be updated when contract work exposes a necessary clarification, but it must remain consistent with accepted ADRs.

### Cross-Case Requirements

The cross-case analysis records the evidence used to distinguish universal, optional, external, and activity-specific capabilities.

It is primarily an architectural rationale and requirements-synthesis document.

### Packet Models

The packet models are representative cases used to test the architecture.

They may evolve as classroom workflows become clearer, but one packet model should not impose its specialized terminology on every Concord Activity.

### Conceptual Contracts

The planned conceptual contracts will define precise record structures, required fields, reference rules, validation behavior, and representative examples.

Once accepted, those contracts will become more specific than the broad domain-model descriptions while remaining subordinate to the ADRs.

### Implementation Documentation

Future schema, storage, CLI, and workflow documentation will describe how the accepted architecture is implemented.

Implementation convenience must not silently change the domain semantics established here.

## Foundational Principles

All future Concord work should preserve the following principles.

### Paper-first

Printed classroom Artifacts are primary workflow instruments, not fallback exports from a device-centered application.

### Human-reviewed

Concord organizes and presents evidence for teacher judgment. It does not interpret handwriting, infer behavior, or automate collaborative-performance Scoring.

### Source-preserving

Core-retained scans remain canonical digital evidence. Filing, attribution, Review, Moderation, and Scoring are linked records that preserve history.

### Contextual

Groups, Memberships, Roles, Responsibilities, Authors, Subjects, Contributions, and Scores are contextual relationships rather than permanent participant attributes.

### Explicitly scored

A Score is an explicit teacher-approved judgment about one Criterion for one target. Evidence, Review, Moderation, Score, Grade, and Report remain distinct.

### Modular

Concord consumes shared Core infrastructure and links to sibling modules without duplicating their responsibilities.

### Progressively structured

Simple Activities remain simple. Milestones, Work Items, dependencies, Events, subteams, Contribution Claims, Attachments, and similar structures are added only when the Activity requires them.

## Next Documentation Phase

The next phase should define conceptual contracts for the foundational records.

A practical sequence is:

1. Activity and Session;
2. Group, Group Membership, Role Assignment, and Responsibility Assignment;
3. Template Definition, Template Version, Packet Definition, and Packet Instance;
4. Artifact Instance, Artifact Page, Artifact Author, and Artifact Subject;
5. Scan Reference, Artifact Review, Moderation Record, and Correction Record;
6. Criterion Set, Criterion, Scoring Scale, Score Record, and Score Evidence Link;
7. External Reference and Attachment;
8. optional Activity Marker, Work Item, Dependency, Event, and Contribution Claim structures;
9. shared typed-reference conventions;
10. lifecycle, privacy, correction, and supersession rules.

Each contract should include:

* purpose;
* ownership;
* required and optional fields;
* field semantics;
* identifiers;
* cardinalities;
* invariants;
* lifecycle states;
* correction and supersession behavior;
* privacy considerations;
* validation rules;
* and representative valid and invalid examples.

## Contribution Guidance

When adding or revising documentation:

* preserve established terminology and capitalization;
* distinguish universal capabilities from mandatory record presence;
* identify the owning module for every cross-module concept;
* avoid treating identifiers, labels, paths, and display names as interchangeable;
* state cardinalities and invariants explicitly;
* preserve evidence and historical-record semantics;
* avoid adding automated interpretation or Scoring behavior;
* and update affected ADRs or contracts when a change alters an accepted architectural decision.

Significant architectural changes should be recorded through a new ADR that supersedes or amends the earlier decision rather than silently rewriting the project’s history.
