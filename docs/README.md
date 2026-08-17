# Concord Documentation

This directory contains the design, architecture, and domain documentation for `pds-concord`.

Concord is the Paper Data Suite module responsible for paper-first evidence generated during collaborative classroom activities. Its documentation defines:

* the module’s scope and boundaries;
* the representative classroom workflows it must support;
* the shared domain concepts used across those workflows;
* the architectural decisions that constrain implementation;
* the Core integration requirements needed to support Concord as a first-class Paper Data Suite module;
* and the conceptual contracts that will guide schemas, storage, and interfaces.

## Current Status

The architecture and conceptual-contract phase is complete. The skeptical
foundation review concluded with the verdict `APPROVED WITH NONBLOCKING FOLLOW-UP`.
The v0.2.0 vertical slice and issue #33 installed acceptance are complete.
Issue #34 governs the release audit, compatibility freeze, qualification, and
release closeout against the released `pds-core` v0.6.0 integration baseline.

The repository now contains:

* a revised conceptual design;
* three representative packet models;
* a cross-case requirements analysis;
* an initial domain model;
* complete conceptual data contracts and representative contract examples;
* a completed skeptical foundation review;
* fifteen accepted Architecture Decision Records;
* a detailed `pds-core` integration requirements specification covering
  released PDS2 routing and academic-registry contracts;
* an implemented immutable native record, exact mapping-conversion, and pure
  graph-validation layer;
* canonical guarded persistence with immutable history, atomic snapshots,
  strict reads, diagnostics, and a disposable catalog;
* typed Activity, Session, and Group collaboration workflow services;
* contextual Membership, Role, and Responsibility workflow services;
* a fully noninteractive direct CLI;
* a teacher-facing H/B/M/Q menu with low-information-density screens;
* native Scan References with immutable history and catalog projection; and
* Core PDS2 Artifact Page preparation, rendering, retained scan dispatch, and
  append-only routing review;
* Artifact-level return-state reconciliation and reproducible returned-PDF
  assembly from exact retained Scan Reference lineage; and
* explicit Artifact Author/Subject creation, state revision, correction, and
  history workflows; and
* explicit Artifact Review and evidence Moderation with preserved history,
  exact evidence/Subject scope, and a guarded Score handoff; and
* teacher-controlled Criterion Set, Scoring Scale, Score Record, Score Evidence
  Link, non-score disposition, and Score revision workflows; and
* explicit Core Academic Work Registration, immutable Concord Academic Result
  Manifest generation, Publication Record supersession/withdrawal, publication
  producer discovery, and Core academic-catalog reconciliation; and
* a consumer-neutral canonical Academic Result Manifest reader plus a separately
  authorization-gated, historical-snapshot-bound bounded Artifact reader; and
* clean-wheel installed producer acceptance spanning synthetic collaboration,
  PDS2 return, registration, two manifest/publication revisions, Core
  verification, authorized historical Artifact access, withdrawal, and audit.

Implementation follows the v0.2.0 vertical-slice sequence tracked by
[`Paper-Data-Suite/pds-concord#22`](https://github.com/Paper-Data-Suite/pds-concord/issues/22).
The package baseline, foundational native models, persistence substrate, and
teacher-local collaboration-context, PDS2 Artifact Page routing, returned Artifact
assembly, Author/Subject, Review/Moderation, Criterion/Scale/Score, and academic
publication workflows and the issue #32 consumer-neutral readers are complete.
Concord declares separate routing and publication-producer entry points. The
issue #33 full installed Activity-to-publication-to-consumer acceptance path is
complete; issue #34 owns final release audit and closeout.

### 21. v0.2.0 release audit

[`v0.2.0-release-audit.md`](v0.2.0-release-audit.md)

Records the implementation evidence and result for every accepted ADR, the #22
exit-condition audit, privacy/policy observations, and deliberately deferred
surfaces.

### 22. v0.2.0 release compatibility

[`v0.2.0-release-compatibility.md`](v0.2.0-release-compatibility.md)

Freezes the exact distribution, Core range, Academic Work/Activity/manifest
contracts, producer profile, reader, and separate Artifact authorization
boundary expected by downstream consumers.

### 23. Release checklist

[`release_checklist.md`](release_checklist.md)

Separates release-preparation PR work, exact post-merge qualification,
tag/GitHub Release publication, and fresh-download verification.

### Future v0.3.0 Group Planning / Template / Packet plan

[`pds-group-planning-interoperability-development-plan.md`](pds-group-planning-interoperability-development-plan.md)

This remains future v0.3.0 planning. It is not current v0.2.0 implementation
and does not add production models, a Meridian dependency, or packet-oriented
teacher UI in issue #34.

### 14. PDS2 Artifact Page integration

[`implementation/pds2-artifact-page-integration.md`](implementation/pds2-artifact-page-integration.md)

Documents route identity, canonical-before-render ordering, immutable route
reconciliation, retained-source intake, Scan References, dispatch/replay,
routing review, privacy, partial success, and the handoff to issue #28.


### 15. Artifact assembly and Author/Subject management

[`implementation/artifact-assembly-author-subject-management.md`](implementation/artifact-assembly-author-subject-management.md)

Documents Artifact return-state roll-up, exact retained-source assembly,
immutable lineage manifests, explicit Author/Subject workflows, correction
history, privacy, identity separation, and the handoff to issue #29.

### 16. Artifact Review and Moderation

[`implementation/artifact-review-moderation.md`](implementation/artifact-review-moderation.md)

Documents explicit human Review, Moderation evidence and Subject scope, preserved
decision history, Core Publication-reference verification, direct/menu
workflows, Score-handoff validation, and installed-wheel acceptance.

### 17. Criterion, Scale, and Score recording

[`implementation/criterion-scale-score-recording.md`](implementation/criterion-scale-score-recording.md)

Documents immutable Criterion Set and Scale revisions, explicit Activity Set
selection, type-sensitive native Scale values, teacher-approved Score and
non-score workflows, durable evidence links, Review/Moderation handoff, Score
history, direct/menu surfaces, and installed-wheel acceptance.

### 18. Academic result publication

[`implementation/academic-result-publication.md`](implementation/academic-result-publication.md)

Documents explicit Core Academic Work Registration, the immutable
`concord_academic_result_manifest_v1` projection, semantic projection digests,
producer revisioning, privacy minimization, publication-producer compatibility,
first publication, replay, supersession, withdrawal, catalog reconciliation,
partial-success recovery, direct CLI/menu behavior, and the #32/#33/Meridian
boundaries.

### 19. Academic result consumer reader

[`implementation/academic-result-reader.md`](implementation/academic-result-reader.md)

Documents canonical immutable manifest reading, exact producer-native lookup,
type-sensitive Scale values, authorization-before-I/O, historical snapshot
binding, bounded Artifact PDF representations, retained-source integrity,
privacy minimization, consumer ownership boundaries, and the #33 handoff.

### 20. Installed end-to-end acceptance

[`implementation/installed-end-to-end-acceptance.md`](implementation/installed-end-to-end-acceptance.md)

Documents clean-wheel isolation, the exact Core qualification artifact, the
complete two-revision producer lifecycle, separately authorized historical
Artifact access, Core catalog/audit expectations, immutable-history checks, and
the policy deliberately left outside issue #33.

### 10. Native model implementation

[`implementation/native-record-models.md`](implementation/native-record-models.md)

Documents the supported Python imports, structural and graph-validation split,
exact mapping conversion, Core standards validation boundary, controlled
extensions, supersession semantics, and deliberately deferred operations.

### 11. Canonical storage implementation

[`implementation/canonical-storage.md`](implementation/canonical-storage.md)

Documents storage ownership, exact layout and versions, immutable revisions and
snapshots, atomic pointer semantics, expected-revision commits, strict reads,
standards validation, catalog nonauthority, diagnostics, interruption, and
conservative recovery.

### 12. Collaboration workflow implementation

[`implementation/activity-session-group-workflows.md`](implementation/activity-session-group-workflows.md)

Documents Activity, Session, Group, Membership, Role, and Responsibility
services; Core workspace/class/roster ownership; standards selection; exact
expected-snapshot concurrency; non-destructive reassignment; teacher workflows;
and installed-wheel acceptance coverage.

### 13. CLI and teacher-menu contract

[`cli-contract.md`](cli-contract.md)

Documents bare menu behavior, the complete direct command inventory, actor and
workspace requirements, exit codes, H/B/M/Q navigation, confirmations, and the
low-information-density interaction contract.

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

### 5. Conceptual Data Contracts

[`design/conceptual-data-contracts.md`](design/conceptual-data-contracts.md)

Defines the completed implementation-neutral record contracts, identity,
cardinality, lifecycle, provenance, privacy, and invariants that implementation
must preserve.

### 6. Representative Contract Examples

[`design/examples/README.md`](design/examples/README.md)

Indexes the exact representative seminar, laboratory, and project contract
examples and their cross-example validation.

### 7. Skeptical Foundation Review

[`design/foundation-review.md`](design/foundation-review.md)

Records the adversarial review matrix, corrections, final approval verdict, and
nonblocking follow-up concerns.

### 8. Architecture Decision Records

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

### 9. PDS Core Integration Requirements

[`design/pds-core-integration-requirements.md`](design/pds-core-integration-requirements.md)

Translates the accepted Concord architecture into explicit requirements for `pds-core` and coordinated migration requirements for the current Paper Data Suite modules.

It defines:

* the PDS2 page-locator QR contract;
* durable route registration for every expected returned page;
* module-qualified class and work identity;
* generic module-owned route targets;
* module-scoped workspace paths;
* generalized routing-failure and resolution metadata;
* retained-source scan and provenance requirements;
* ScoreForm and Quillan migration requirements;
* Concord Artifact Page routing requirements;
* package and contract versioning requirements;
* and compatibility with a future suite assignment registry.

This document should be read after the ADRs because it applies their architectural constraints to the shared Core contracts and cross-repository migration plan.

## Documentation Structure

```text
docs/
├── README.md
├── cli-contract.md
├── concord-conceptual-design-revised.md
├── decisions/
│   ├── README.md
│   └── 0001-... through 0015-...
├── design/
│   ├── cross-case-requirements.md
│   ├── initial-concord-domain-model.md
│   └── pds-core-integration-requirements.md
├── implementation/
│   ├── native-record-models.md
│   ├── canonical-storage.md
│   └── activity-session-group-workflows.md
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

### Core Integration Requirements

The Core integration requirements specify how the accepted Concord architecture must be supported by shared Paper Data Suite identity, QR, routing, workspace, provenance, failure, and package contracts.

The integration specification:

* is subordinate to accepted ADRs;
* is more specific than the broad conceptual domain model for Core-facing concerns;
* governs the coordinated Core, ScoreForm, Quillan, and Concord migration unless superseded;
* and must remain consistent with later accepted Core ADRs and implemented shared contracts.

If implementation work exposes a necessary architectural change, the relevant ADRs and integration requirements must be revised deliberately rather than bypassed through module-specific workarounds.

### Cross-Case Requirements

The cross-case analysis records the evidence used to distinguish universal, optional, external, and activity-specific capabilities.

It is primarily an architectural rationale and requirements-synthesis document.

### Packet Models

The packet models are representative cases used to test the architecture.

They may evolve as classroom workflows become clearer, but one packet model should not impose its specialized terminology on every Concord Activity.

### Conceptual Contracts

The completed conceptual contracts define precise record structures, required
fields, reference rules, validation behavior, and representative examples.

They are more specific than the broad domain-model descriptions while remaining
subordinate to the ADRs.

Where a conceptual contract depends on Core identity, routing, or provenance, it must also conform to the accepted Core integration requirements and the implemented Core contract version.

### Implementation Documentation

Implementation documents describe the native model layer, canonical storage,
collaboration-context workflows, routing, Artifact management, Review,
Moderation, Criterion/Scale/Score recording, publication, consumer-neutral
manifest/Artifact reading, and CLI/menu contracts that are now implemented.

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

## v0.2.0 Release-Closeout Contract

The complete v0.2.0 teacher-local vertical slice and installed producer
acceptance are implemented. Issue #34 governs the release audit, compatibility
freeze, packaging qualification, exact-main qualification, release publication,
and post-release verification. Tagging and GitHub Release publication occur
only after review, hosted CI, merge, and exact-main requalification.

Each implementation issue must preserve the accepted contract ownership,
read-only import behavior, exact compatibility declarations, privacy-safe test
data, and the separation between routing, publication, and grading policy.

## Contribution Guidance

When adding or revising documentation:

* preserve established terminology and capitalization;
* distinguish universal capabilities from mandatory record presence;
* identify the owning module for every cross-module concept;
* avoid treating identifiers, labels, paths, and display names as interchangeable;
* state cardinalities and invariants explicitly;
* preserve evidence and historical-record semantics;
* keep route identity separate from Author, Subject, student, evidence, and Score-target identity;
* avoid adding automated interpretation or Scoring behavior;
* verify consistency with the Core integration requirements when a change affects QR, routing, workspace paths, scan provenance, or cross-module identity;
* and update affected ADRs or contracts when a change alters an accepted architectural decision.

Significant architectural changes should be recorded through a new ADR that supersedes or amends the earlier decision rather than silently rewriting the project’s history.
