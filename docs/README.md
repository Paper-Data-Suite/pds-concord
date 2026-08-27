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
The v0.2.0 vertical slice, installed acceptance, release audit, compatibility
freeze, and milestone closeout remain historically qualified against `pds-core`
v0.6.0. Phase 1 v0.3.0 work is tracked by umbrella #47. Issue #48 froze the
reusable-versus-instance boundaries; issue #49 establishes `0.3.0.dev0`,
the neutral Core `grouping_signal_set_v1` consumer baseline without adding a
Meridian runtime dependency. Current v0.3 development now targets the latest
released Core baseline, `pds-core>=0.6.3,<0.7`. Issue #50 now adds the
native planning-only GroupPlan/PlannedGroup record, immutable history, and typed
create/replace/read/preview/approve/cancel lifecycle services. Issue #51 now
implements manual plan-local authoring, exact roster placement and refresh,
strict `student_id,group` arrangement import/replacement, the direct
`concord group-plan ...` family, and a bounded teacher-menu planning path.
Issue #52 now adds exact seeded deterministic random proposals with explicit
size/count targets and balanced partitioning. Issue #53 now implements exact
Core grouping-signal discovery, bounded inspection/diagnostics, explicit
dimension selection, and teacher-controlled `grouping_signal_csv_v1` import.
Issue #54 now implements deterministic `similar_signal` and `mixed_signal` drafts
with full-roster targets, exact Core signal/dimension binding, explicit unresolved
missing coverage, bounded direct/menu UX, and no Meridian runtime dependency.
Issue #55 implements explicit manual/random/leave-unassigned missing-signal
decisions and approval revalidation. Issue #56 now implements exact read-only
application preparation, deterministic canonical identity derivation, digest- and
snapshot-bound atomic Group/GroupMembership application, and the terminal
`approved -> applied` GroupPlan transition. Issue #57 now defines the public,
immutable, cross-Activity reusable Template Definition/Version contract,
including typed page manifests, rendering-input declarations, response regions,
identity-free defaults/compatibility, and exact rendering-specification digest
binding. Issue #58 now implements canonical workspace-level Template persistence,
strict revision/snapshot history, rendering-specification storage, head/current
selection, successor/activation/retirement workflows, and direct/menu management.
Issue #59 now defines the public immutable reusable Packet Definition/Version
contract with exact Template Version composition, source-owned external references,
deterministic ordering/copy semantics, identity-free audience/role intent, bounded
conditions, and typed packet-level rendering rules. Issue #60 now implements
canonical workspace-level Packet persistence, strict immutable revision/snapshot
history, exact Template dependency validation, head/current selection,
successor/activation/retirement workflows, and direct/menu Packet management.
Issue #61 now ships a deterministic package-owned catalog of 30 synthetic
collaborative-learning starter Templates, strict `concord_starter_layout_v1`
assets, explicit/idempotent installation through #58 canonical Template storage,
direct CLI and teacher-menu browsing/install, and installed-wheel package-data
qualification. Issue #62 now implements exact Activity-specific Packet
instantiation, review-digest-bound commit, fresh Packet/Artifact/Page/Core PDS2
identity allocation, deterministic starter PDF rendering, typed recovery/reprint,
direct CLI and opened-Activity menu workflows, installed-wheel smoke, and the
accepted all-30-starter visual-review gate. Issue #63 now implements safe
Activity copying with explicit source/target identity, positive reusable
configuration selection, privacy tightening, deterministic review digest,
create-only Activity/Session commit, direct CLI, and teacher `COPY` flow.

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
* a native planning-only GroupPlan/PlannedGroup contract integrated with the
  existing immutable record-revision and Activity-work snapshot machinery;
* teacher-controlled manual GroupPlan editing, explicit Core-roster refresh,
  strict deterministic arrangement CSV import/replacement, and shared direct/menu
  planning surfaces with no canonical Group/Membership side effects;
* deterministic seeded random GroupPlan generation with exact target semantics,
  stable SHA-256 v1 ordering, balanced sizes, and no signal dependency;
* exact Core grouping-signal discovery, canonical-digest inspection, explicit
  dimension diagnostics/selection, and immutable teacher-controlled Core CSV
  import with no Activity/GroupPlan or sibling-module side effects;
* deterministic similar-signal and mixed-signal GroupPlan generation with shared
  full-roster target semantics, exact signal provenance, visible unresolved missing
  coverage, explicit teacher review, and no canonical Group/Membership side effects;
* explicit missing-signal `manual`, seeded `random`, and `leave_unassigned`
  dispositions with exact Core-diagnostic authority, preview invalidation, and
  narrow approval semantics;
* exact approved-GroupPlan application preview plus one-snapshot atomic creation
  of canonical Groups/Memberships and the terminal applied GroupPlan revision,
  with deterministic IDs, explicit fallback context, stale/digest rejection, and
  no signal-band leakage into operational records;
* public immutable reusable Template Definition/Version contracts with typed
  page manifests, rendering inputs, response regions, privacy/authorship/subject
  defaults, compatibility metadata, exact rendering-source integrity binding,
  and a strict separation from Activity-native persistence;
* canonical reusable Template storage under `shared/concord/templates/` with
  immutable record revisions, digest-linked snapshots, exact rendering bytes,
  explicit head/current Version state, guarded successor/activation/retirement
  workflows, and shared direct CLI/teacher-menu services;
* public immutable reusable Packet Definition/Version/Component contracts with
  exact Template identities, typed source-owned external references, contiguous
  ordering, positive copies-per-target, identity-free audience/role intent,
  bounded non-executable conditions, deterministic rendering rules, and no
  Activity-native persistence;
* canonical reusable Packet storage under `shared/concord/packets/` with strict
  typed serialization, immutable record revisions, digest-linked snapshots,
  explicit head/current Version state, exact Template dependency eligibility,
  guarded successor/activation/retirement workflows, and shared direct
  CLI/teacher-menu services;
* a deterministic package-owned 30-form collaborative-learning starter Template
  catalog with strict non-executable `concord_starter_layout_v1` JSON assets,
  stable identities/digests, identity-free reusable defaults, explicit/idempotent
  installation through #58 canonical Template storage, direct CLI/menu browsing,
  and installed-wheel package-data qualification;
* Activity-owned PacketInstance/PacketTargetContext generation with exact
  reusable Packet/Template provenance, zero-write preparation, review-digest
  commit, deterministic target/copy expansion, fresh Artifact/Page/Core PDS2
  identities, `concord_starter_layout_v1` PDF rendering, explicit recovery and
  exact reprint, runtime direct CLI/menu surfaces, and privacy-safe route data;
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
issue #33 full installed Activity-to-publication-to-consumer acceptance path and
issue #34 release closeout are complete. The current v0.3.0 work adds reusable
planning/setup layers without rewriting the accepted v0.2.0 operational history.

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

### 24. v0.3.0 reusable-versus-instance boundary audit

[`v0.3.0-reusable-instance-boundary-audit.md`](v0.3.0-reusable-instance-boundary-audit.md)

Freezes which current and planned fields are reusable definitions/defaults,
Activity-specific configuration, planning-only state, shared references, or
operational/history state. It is the normative #48 handoff for #50-#64.

### 25. v0.3.0 Core grouping-signal integration

[`v0.3.0-core-grouping-signal-integration.md`](v0.3.0-core-grouping-signal-integration.md)

Documents the released Core 0.6.1 qualification artifact, public
`grouping_signal_set_v1` model/CSV/storage/diagnostic boundary, authenticated
synthetic fixtures, immutable signal identity/digest semantics, contextual
ordinal bands, exact roster diagnostics, privacy constraints, and the #50/#53
planning handoff without a Meridian runtime dependency.

### 26. v0.3.0 GroupPlan contract

[`v0.3.0-group-plan-contract.md`](v0.3.0-group-plan-contract.md)

Defines the planning-only GroupPlan/PlannedGroup native contract, stable
identity through native record revisions, exact roster coverage, strategy and
signal-reference boundaries, lifecycle invariants, privacy exclusions, and the
#51-#56 handoffs. Issue #50 implements the native contract plus typed
create/replace/read/preview/approve/cancel services; `approved -> applied`
remains reserved for #56.

### 27. v0.3.0 manual Group planning and arrangement import

[`v0.3.0-manual-group-planning.md`](v0.3.0-manual-group-planning.md)

Documents issue #51's manual GroupPlan authoring, plan-local group editing,
exact Core-roster student placement, fail-closed roster drift, explicit roster
refresh, strict deterministic `student_id,group` CSV import/replacement,
direct CLI and bounded teacher-menu surfaces, lifecycle reuse, privacy
constraints, and the hard separation from canonical Group/Membership creation.

### 28. v0.3.0 deterministic random Group planning

[`v0.3.0-random-group-planning.md`](v0.3.0-random-group-planning.md)

Documents issue #52's exact seed contract, versioned SHA-256 ranking,
target-size/count formulas, balanced partitioning, stable plan-local group
identity, exact-roster race protection, manual-edit/refresh behavior, direct
CLI/menu creation, privacy boundary, and #53-#56 handoffs.

### 29. v0.3.0 grouping-signal discovery, diagnostics, and import

[`v0.3.0-grouping-signal-workflows.md`](v0.3.0-grouping-signal-workflows.md)

Documents issue #53's exact Core signal discovery, canonical digest/source
provenance distinction, explicit dimension selection, roster diagnostics,
complete/projection CSV import, immutable replay/conflict semantics,
review-to-write digest binding, direct CLI/menu surfaces, privacy boundary, and
#54-#56 handoffs without a Meridian runtime dependency.

### 30. v0.3.0 signal-backed Group planning

[`v0.3.0-signal-group-planning.md`](v0.3.0-signal-group-planning.md)

Documents issue #54's deterministic `similar_signal` and `mixed_signal` algorithms,
shared full-roster size/count targets, exact Core signal/dimension/digest binding,
partial-coverage and unresolved semantics, roster/preview race protection, direct
CLI and explicit teacher-menu review, lifecycle reuse, privacy constraints, sibling
isolation, and the #55/#56 handoffs.

### 31. v0.3.0 missing-signal disposition

[`v0.3.0-missing-signal-disposition.md`](v0.3.0-missing-signal-disposition.md)

Documents issue #55's exact Core `missing_student_signal` authority, structured
`manual`/`random`/`leave_unassigned` state, versioned missing-only seeded random
placement, edit/refresh/preview lifecycle behavior, narrow approval exception,
direct CLI and teacher-menu decisions, privacy exclusions, and the #56 boundary.

### 32. v0.3.0 approved GroupPlan application

[`v0.3.0-group-plan-application.md`](v0.3.0-group-plan-application.md)

Documents issue #56's approved-only eligibility, deterministic application and
canonical record identities, exact semantic preview digest, roster/signal
revalidation, explicit Membership fallback context, empty-group and
leave-unassigned behavior, one-batch application, terminal applied metadata,
privacy exclusions, direct CLI commands, and teacher `APPLY` confirmation.

### 33. v0.3.0 immutable Template Definition contract

[`v0.3.0-template-definition-contract.md`](v0.3.0-template-definition-contract.md)

Documents issue #57's stable Template lineage, exact immutable Template Version,
typed page/rendering-input/response-region contracts, identity-free privacy and
authorship/Subject expectations, compatibility metadata, rendering-source
SHA-256 binding, existing Artifact compatibility, grouping-signal exclusions,
and the deliberate #58 storage/revision handoff.

### 34. v0.3.0 Template storage and revision workflows

[`v0.3.0-template-storage-revision-workflows.md`](v0.3.0-template-storage-revision-workflows.md)

Documents issue #58's `shared/concord/templates/` authority,
`concord_template_library_storage_v1`, strict Template serialization,
rendering-specification byte integrity, immutable record/snapshot history,
head/current Version distinction, exact expected-snapshot concurrency,
`concord_template_authoring_v1`, direct `concord template ...` commands,
workspace-level Template Library menu, retirement semantics, and #59/#62
handoffs.

### 35. v0.3.0 reusable Packet Definition contract

[`v0.3.0-packet-definition-contract.md`](v0.3.0-packet-definition-contract.md)

Documents issue #59's stable Packet lineage, immutable Packet Versions, ordered
Packet Components, exact Template Definition/Version references, producer-owned
external `ModuleRecordRef` components, positive copies-per-target,
identity-free audience/role intent, bounded conditional semantics, typed
deterministic rendering rules, existing Artifact compatibility, GroupPlan/signal
privacy exclusion, and the deliberate #60 storage / #62 generation handoffs.

### 36. v0.3.0 Packet storage and revision workflows

[`v0.3.0-packet-storage-revision-workflows.md`](v0.3.0-packet-storage-revision-workflows.md)

Documents issue #60's `shared/concord/packets/` authority,
`concord_packet_library_storage_v1`, strict Packet serialization, immutable
record/snapshot history, exact head/current Version state, Template dependency
eligibility, `concord_packet_authoring_v1`, exact expected-snapshot concurrency,
direct `concord packet ...` commands, workspace-level Packet Library menu,
retirement semantics, structural-only external `ModuleRecordRef` handling, and
the #62 generation handoff.

### 37. v0.3.0 starter collaborative-learning Template library

[`v0.3.0-starter-template-library.md`](v0.3.0-starter-template-library.md)

Documents issue #61's 30 shipped synthetic starters, shared copier-safe paper
design, strict `concord_starter_layout_v1` asset contract, stable package-owned
identities/digests, explicit read-only browse versus canonical installation,
idempotence/collision/partial-success semantics, privacy/authorship/Subject
defaults, direct `concord template starter-*` commands, teacher `INSTALL` flow,
wheel/package qualification, and the #62/#64 authority boundaries.

### 38. v0.3.0 Activity-specific Packet instantiation and PDS2 rendering

[`v0.3.0-packet-instantiation-rendering.md`](v0.3.0-packet-instantiation-rendering.md)

Documents issue #62's Activity-owned `PacketInstance` runtime state, exact
Packet/Template provenance, zero-write target/input preview, review-digest-bound
commit, canonical Group/Membership/Role resolution, fresh Artifact/Page/Core PDS2
allocation, deterministic `concord_starter_layout_v1` PDF rendering, privacy and
authorship boundaries, typed partial-success recovery, exact reprint, direct
runtime Packet commands, opened-Activity `GENERATE` flow, installed-wheel smoke,
and the accepted 30-starter / 35-QR visual-review gate.

### 39. v0.3.0 safe Activity copying

[`v0.3.0-activity-copying.md`](v0.3.0-activity-copying.md)

Documents issue #63's exact source/target identity, positive copy allowlist, fresh first Session, privacy resolution, review-digest concurrency, create-only persistence, direct CLI, teacher `COPY` workflow, Core 0.6.3 development baseline, and installed-wheel qualification.

### Future v0.3.0 Group Planning / Template / Packet plan

[`pds-group-planning-interoperability-development-plan.md`](pds-group-planning-interoperability-development-plan.md)

This remains the roadmap for future v0.3.0 issues beyond the implemented
#48-#63 foundations. Issue #57 defines the reusable Template contract, #58
implements its canonical storage/management layer, #59 defines the reusable
Packet contract, #60 implements Packet storage/management, #61 ships the
starter collaborative-learning Template library, #62 implements Activity-
specific Packet generation/rendering, and #63 implements safe Activity
copying. Reusable presets, guided Activity setup, and final integrated
teacher UI behavior remain later work.

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
├── v0.3.0-reusable-instance-boundary-audit.md
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

The complete v0.2.0 teacher-local vertical slice, installed producer
acceptance, release audit, compatibility freeze, and milestone closeout are
complete. The v0.3.0 work begins from that released boundary and must preserve
its operational identities, immutable history, and downstream consumer contract
while adding reusable planning/setup layers deliberately.

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
