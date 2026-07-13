# ADR 0002: Paper-First, Human-Reviewed Evidence

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Concord exists to preserve evidence produced during collaborative classroom activities.

That evidence is often created while students and teachers are:

* discussing a text;
* conducting a laboratory investigation;
* handling physical materials;
* building or testing a product;
* observing peers;
* documenting decisions;
* or coordinating responsibilities.

Requiring a device during those activities could interfere with the collaboration being documented, create inequitable access requirements, and make Concord dependent on continuous connectivity or third-party services.

Paper provides a low-friction medium that:

* works without student devices;
* supports handwriting, drawing, diagrams, maps, tables, and annotations;
* can move among participants;
* remains usable during physical and discussion-centered activities;
* and can be collected as a stable classroom record.

After completion, the paper artifacts must be identified, scanned, filed, reviewed, and used as evidence.

Some of that workflow can be automated safely. Concord can generate forms, create QR codes, identify pages, split scans, route artifacts, detect missing pages, and present evidence for review.

Other parts require professional judgment. Software cannot reliably determine from a handwritten page:

* what a student intended;
* whether a contribution was valuable;
* whether a peer observation was fair;
* whether silence indicated disengagement;
* whether a failed trial represented poor performance;
* whether a contribution claim was credible;
* or what score the evidence justifies.

Concord therefore needs an explicit boundary between administrative processing and interpretation.

## Decision

Concord will be a **paper-first, human-reviewed collaborative-evidence system**.

### Paper-first workflow

Printed artifacts are a primary interaction medium, not fallback exports from a digital-first application.

The normal Concord workflow is:

```text
select and configure templates
    -> generate printable artifacts
    -> complete artifacts during collaborative work
    -> collect and scan completed pages
    -> identify and file the scans
    -> review the evidence
    -> moderate evidence when required
    -> record teacher-approved scores
```

Concord must remain useful when:

* students have no devices;
* the classroom has no internet connection;
* the teacher chooses not to use student technology;
* or the activity is better served by physical paper.

Paper-first does not mean paper-only.

Concord may also support:

* digital teacher configuration;
* digital review interfaces;
* digital score entry;
* teacher-entered notes;
* external evidence references;
* and future interfaces operating on the same conceptual records.

A paper scoring rubric and a digitally completed scoring interface should be capable of producing the same conceptual Score Record.

### Primary evidence

For a completed paper artifact, the retained source scan is the authoritative representation of that artifact.

Concord may associate the scan with:

* filing metadata;
* authors;
* subjects;
* activity and Session context;
* privacy settings;
* reviews;
* moderation decisions;
* evidence locators;
* and Score Records.

Those associated records do not replace or silently alter the scanned artifact.

Source-scan retention and suite-level provenance remain Core responsibilities. Concord stores routed references back to the Core-retained source.

### Human-reviewed evidence

Concord presents evidence for human interpretation.

The teacher or another authorized reviewer remains responsible for determining:

* whether the scan is readable and complete;
* whether it has been filed under the correct Activity, Session, Group, author, and subject;
* whether the artifact is relevant;
* whether student-generated evidence is credible or fair;
* whether exceptional circumstances affect its interpretation;
* whether the evidence may be used for scoring;
* and what criterion-level judgment the evidence supports.

Evidence requiring moderation must not affect a consequential Score until an authorized human has completed the required moderation.

### Permitted automation

Concord may automate administrative and deterministic operations, including:

* generating printable PDFs;
* generating page-level QR codes;
* creating human-readable fallback identifiers;
* creating packet manifests;
* splitting PDFs or images into pages;
* reading QR codes;
* matching pages to Artifact Instances;
* associating pages with known Activity context;
* detecting duplicate or missing pages;
* validating identifiers and references;
* flagging routing conflicts;
* retaining processing provenance;
* and presenting organized evidence for review.

These operations identify, organize, and validate records. They do not interpret the academic or collaborative meaning of handwritten content.

### Prohibited automated interpretation

Concord will not automatically:

* recognize or interpret handwriting;
* transcribe handwritten responses;
* transcribe classroom discussion from audio or video;
* create AI-generated records of classroom interaction;
* infer student engagement, leadership, collaboration, effort, or understanding;
* infer sole authorship from handwriting, account ownership, or file ownership;
* decide whether a contribution was valuable;
* determine whether peer evidence was fair;
* assign collaboration scores;
* or convert missing evidence into a negative judgment.

OMR remains a ScoreForm responsibility. Extended written-response review remains a Quillan responsibility.

Any future proposal to add automated interpretation or behavioral inference must be evaluated through a new ADR that explicitly supersedes or narrows this decision.

### Evidence sources beyond paper

Paper artifacts are central to Concord, but they are not the only permissible evidence references.

Concord may also reference:

* teacher-entered observations;
* teacher professional judgment;
* reviewed physical or digital attachments;
* ScoreForm results;
* Quillan responses;
* and other authorized external evidence.

These sources remain human-reviewed before consequential use unless their owning module already provides an accepted human-review or scoring result.

### Minimal classroom burden

Paper evidence collection must remain proportionate to the activity.

Concord templates should:

* collect only evidence that has a clear purpose;
* avoid requiring students to document every minor action;
* avoid rewarding groups merely for producing more paperwork;
* minimize teacher writing during active supervision;
* and permit the teacher to omit artifacts that are unnecessary for a particular activity.

The evidence system should support collaboration rather than displace it.

## Consequences

### Positive consequences

* Concord remains usable without student devices or continuous connectivity.
* Teachers can use the system during discussions, laboratories, projects, and other physical or verbal activities.
* The completed artifact remains inspectable rather than being reduced immediately to extracted metadata or a score.
* Human judgment remains accountable and reviewable.
* The system avoids unsupported behavioral inference.
* Peer observations and disputed claims can be moderated before consequential use.
* Deterministic automation can reduce filing burden without replacing teacher interpretation.
* Paper and digital teacher interfaces can share the same conceptual evidence and scoring model.
* The architecture supports local-first and privacy-conscious operation.
* Teachers can preserve diagrams, maps, annotations, and other evidence that does not fit machine-readable fields.

### Negative consequences

* Reviewing evidence requires teacher time.
* Handwritten content cannot be searched or aggregated automatically.
* Concord cannot automatically generate detailed participation analytics.
* Scans may be unreadable, incomplete, damaged, or incorrectly routed.
* Manual interpretation may vary among reviewers.
* Students and teachers may need clear instructions for completing and identifying paper artifacts.
* Large activities may produce substantial scanning and review workloads.
* The system cannot promise automatic scoring or instant feedback from handwritten collaborative evidence.
* Accessibility needs may require alternate artifact formats or teacher-entered records.

### Operational consequences

Implementations must provide:

* readable print layouts;
* stable page identity;
* human-readable fallback identifiers;
* clear scan and filing states;
* visible provenance;
* review interfaces;
* moderation states;
* correction workflows;
* explicit scoring-readiness status;
* and non-score states for missing or insufficient evidence.

Implementations should also support batch-oriented review where appropriate so that human review does not require unnecessary repeated actions.

## Alternatives Considered

### Alternative 1: Digital-first workflow with printable exports

Rejected as the primary architecture.

A digital-first system would make devices the normal interaction medium and treat paper as an export format. That would:

* increase classroom technology requirements;
* weaken offline use;
* interfere with some discussion and physical-work activities;
* and make paper evidence secondary to a digital application model.

Concord may provide digital teacher interfaces, but student-facing collaborative evidence remains paper-first.

### Alternative 2: Paper-only workflow

Rejected.

A strictly paper-only model would prevent useful digital capabilities such as:

* packet configuration;
* QR generation;
* scan filing;
* digital review;
* digital score entry;
* external-module references;
* and evidence export.

Paper is the primary classroom interaction medium, but digital processing and teacher interfaces remain part of the system.

### Alternative 3: Automatic handwriting recognition and transcription

Rejected.

Handwriting recognition could produce inaccurate or misleading representations of:

* student names;
* observations;
* diagrams;
* mathematical notation;
* scientific data;
* and nuanced peer comments.

A transcription may also appear more authoritative than the source artifact even when it is incorrect.

The retained scan remains the evidence record. Any manually entered transcription is a linked secondary record and must not replace the source.

### Alternative 4: Automated AI interpretation of collaborative behavior

Rejected.

Automatically inferring collaboration, engagement, leadership, effort, or understanding would introduce:

* validity concerns;
* fairness concerns;
* privacy risks;
* opaque judgment;
* and pressure to treat uncertain inferences as objective evidence.

These judgments remain the responsibility of an authorized human reviewer.

### Alternative 5: Continuous audio or video capture

Rejected as a Concord requirement.

Audio or video capture would:

* change the nature of the classroom activity;
* create substantial privacy and consent concerns;
* require more storage and processing;
* introduce transcription and interpretation problems;
* and undermine Concord’s local, paper-first design.

Concord does not require audio or video evidence.

### Alternative 6: Automatic scoring from routed artifacts

Rejected.

Correctly identifying and filing a page does not establish:

* what its handwriting means;
* whether its claims are credible;
* whether exceptional circumstances apply;
* or what criterion-level score is justified.

Routing readiness and scoring readiness must remain separate states.

### Alternative 7: Public participation analytics or leaderboards

Rejected.

Raw participation counts or visible rankings could:

* privilege frequent speaking over substantive contribution;
* disregard listening, testing, organization, and support work;
* expose sensitive peer or teacher judgments;
* and distort the collaborative activity.

Concord supports evidence review and teacher scoring, not public behavioral rankings.

## Required Follow-Up

Later contracts and implementation work must define:

* Core source-scan references;
* Concord Scan References;
* Artifact Review records;
* moderation requirements and statuses;
* scoring-readiness states;
* correction and rescan workflows;
* privacy defaults;
* and explicit missing- or insufficient-evidence states.

Template and interface design should also be evaluated for classroom burden before being treated as production-ready.

## References

* [`docs/concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`docs/research/pds-concord-research-findings.md`](../research/pds-concord-research-findings.md)
* [`docs/design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`docs/design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`docs/packet_models/socratic-seminar-packet-model.md`](../packet_models/socratic-seminar-packet-model.md)
* [`docs/packet_models/science-laboratory-group-packet-model.md`](../packet_models/science-laboratory-group-packet-model.md)
* [`docs/packet_models/collaborative-programming_engineering_project_packet_model.md`](../packet_models/collaborative-programming_engineering_project_packet_model.md)
* [`docs/decisions/0001-concord-module-boundaries.md`](0001-concord-module-boundaries.md)

## Notes

This ADR establishes the medium and judgment model for Concord.

It does not define the detailed separation among Review, Moderation, Score, Grade, and Report; that separation is recorded in a later ADR. It also does not define the full source-preservation and supersession model, which is addressed separately.
