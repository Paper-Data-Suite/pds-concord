# ADR 0001: Concord Module Boundaries

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

`pds-concord` requires shared Paper Data Suite capabilities for:

* workspace discovery;
* class, roster, and student identity;
* durable identifiers;
* QR generation and parsing;
* scan-source retention;
* routing provenance;
* standards references;
* and shared local application behavior.

These capabilities are already owned, or are intended to be owned, by `pds-core`.

Concord also needs to coexist with:

* `pds-scoreform`, which handles optical mark recognition and machine-readable paper instruments;
* `pds-quillan`, which handles focused and extended written-response workflows;
* future lesson-planning modules;
* and future gradebook or reporting modules.

Without explicit boundaries, Concord could duplicate shared infrastructure, create incompatible QR or routing contracts, or absorb functionality that belongs to another module.

The intended dependency direction is:

```text
pds-concord -> pds-core
```

Concord may reference records produced by ScoreForm or Quillan, but it should not depend on either module for shared infrastructure.

## Decision

`pds-concord` will remain a separate Paper Data Suite module built on shared contracts and infrastructure provided by `pds-core`.

### Concord owns

Concord owns the concepts and workflows specific to collaborative classroom evidence, including:

* collaborative Activities and Sessions;
* activity-specific Groups and Group Memberships;
* contextual Role Assignments;
* optional Responsibility Assignments;
* Concord packet and template definitions;
* generated Packet Instances;
* generated Artifact Instances and Artifact Pages;
* artifact authorship and subject relationships;
* Concord-specific page identification and filing after Core source retention;
* routed Concord evidence references;
* Artifact Review;
* evidence Moderation;
* Concord Criteria and Scoring Scales;
* criterion-level Score Records;
* evidence-to-score relationships;
* Concord-specific privacy behavior;
* and Concord’s teacher-facing workflows.

### Core owns

`pds-core` owns shared suite-level infrastructure, including:

* Paper Data Suite workspace resolution;
* canonical shared workspace paths;
* class, roster, and student identity conventions;
* durable identifier validation;
* safe path construction;
* shared `PDS1` QR construction, parsing, validation, and routing contracts;
* active source-scan retention;
* provenance from module records back to retained source scans;
* shared scan-routing failure and resolution metadata;
* standards libraries and standards profiles;
* shared navigation behavior;
* and operating-system file and folder opening.

Concord must consume these contracts rather than creating parallel versions.

### ScoreForm owns

`pds-scoreform` owns:

* optical mark recognition;
* bubble-based ratings;
* multiple-choice answer processing;
* machine-readable checklists;
* structured accountability checks;
* and ScoreForm result processing.

Concord may reference a ScoreForm assignment or result. It must not implement a competing OMR workflow.

### Quillan owns

`pds-quillan` owns:

* focused written responses;
* extended reflections;
* substantial written peer feedback;
* analytical explanations;
* written defenses of decisions;
* and Quillan review and scoring workflows.

Concord may reference a Quillan assignment, response, or result. It must not reproduce Quillan’s writing workflow.

### Future modules own

Future lesson-planning modules may own:

* objectives;
* instructional sequencing;
* materials;
* timing;
* differentiation;
* lesson plans;
* and unit plans.

Future gradebook or reporting modules may own:

* score weighting;
* marking-period and course-grade calculation;
* reporting;
* parent-facing communication;
* and cross-module result aggregation.

Concord records collaborative evidence and scores. It does not plan instruction, calculate course grades, or produce formal reports.

### External systems remain authoritative

Concord may reference but does not replace:

* formal safety or disciplinary systems;
* source-control repositories;
* CAD or engineering-file systems;
* cloud-document histories;
* or other authoritative external records.

### Cross-module references

Cross-module relationships should use durable Paper Data Suite identifiers and shared contracts.

Concord must not:

* copy another module’s workflow merely to access its result;
* use synthetic student records to represent Groups or other non-student subjects;
* place Group identifiers into student identity fields;
* create a Concord-only QR grammar;
* or depend directly on ScoreForm or Quillan for behavior that belongs in Core.

## Consequences

### Positive consequences

* Shared infrastructure has one owner.
* QR and routing behavior can remain consistent across Paper Data Suite modules.
* Concord can focus on collaborative evidence rather than recreating workspace, identity, or scan-retention systems.
* ScoreForm and Quillan retain clear, non-overlapping responsibilities.
* Cross-module evidence can be linked without duplicating source records.
* Future modules can consume Concord scores without making Concord responsible for grading or reporting.
* Module testing and maintenance can follow explicit ownership boundaries.

### Negative consequences

* Concord implementation depends on compatible Core contracts.
* Some Concord work cannot proceed until Core supports `module=concord`.
* Core’s current QR model must be extended to support artifacts without one required student subject.
* Changes to shared Core contracts may require coordinated releases.
* Cross-module integration requires stable identifiers and compatibility policies.
* Some user workflows may span several modules instead of appearing as one self-contained Concord feature.

### Required follow-up

Before Concord implementation, Core integration work must address at least:

* registration of `module=concord`;
* routing of Group-, Session-, Activity-, Artifact-, Event-, and multi-subject records;
* QR behavior when no single `student_id` applies;
* appropriate shared route helpers;
* and preservation of provenance from Concord evidence back to Core-retained scans.

Those changes must be made through deliberate Core contract updates rather than Concord-specific workarounds.

## Alternatives Considered

### Alternative 1: Implement Concord inside `pds-core`

Rejected because Core should provide shared infrastructure, not activity-specific collaborative-learning workflows.

Placing Concord inside Core would expand Core’s responsibility to include:

* packet design;
* collaborative Groups;
* artifact types;
* evidence review;
* moderation;
* and scoring behavior.

That would weaken module separation and make Core dependent on one specialized instructional domain.

### Alternative 2: Make Concord a standalone application without Core

Rejected because Concord would need to recreate:

* workspace discovery;
* roster handling;
* identifier validation;
* QR contracts;
* source-scan retention;
* routing metadata;
* standards references;
* and shared navigation behavior.

This would produce duplication and increase the risk of incompatible Paper Data Suite conventions.

### Alternative 3: Make Concord depend directly on ScoreForm and Quillan

Rejected because ScoreForm and Quillan are sibling modules, not shared infrastructure providers.

Direct dependencies would:

* create unnecessary coupling;
* make installation and testing more complicated;
* and encourage modules to access shared behavior through one another rather than through Core.

Concord should reference their records through shared identifiers and contracts.

### Alternative 4: Absorb ScoreForm and Quillan functionality into Concord

Rejected because OMR and extended written-response evaluation are distinct domains with existing module ownership.

Combining them would:

* broaden Concord beyond collaborative evidence;
* duplicate established workflows;
* and create competing result formats.

### Alternative 5: Allow each module to define its own QR and routing contracts

Rejected because module-specific QR grammars would fragment the suite and complicate mixed-batch scanning, routing, validation, and provenance.

Shared QR and routing behavior belongs in Core.

## References

* [`docs/concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`docs/design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`docs/design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`docs/packet_models/socratic-seminar-packet-model.md`](../packet_models/socratic-seminar-packet-model.md)
* [`docs/packet_models/science-laboratory-group-packet-model.md`](../packet_models/science-laboratory-group-packet-model.md)
* [`docs/packet_models/collaborative-programming_engineering_project_packet_model.md`](../packet_models/collaborative-programming_engineering_project_packet_model.md)

## Notes

This ADR establishes ownership and dependency direction. It does not define the final Core API, QR payload, route structure, or release strategy required for Concord integration.
