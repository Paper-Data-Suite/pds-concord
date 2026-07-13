# ADR 0007: Preserve Source Evidence and History

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Concord processes evidence produced during collaborative classroom activities.

A typical paper workflow includes:

1. generating an Artifact;
2. completing the printed Artifact;
3. scanning one or more completed pages;
4. retaining the source scan;
5. identifying and routing pages;
6. reviewing filing and attribution;
7. moderating evidence where required;
8. recording Scores;
9. and sometimes correcting or revising earlier records.

Errors and changes are expected.

Examples include:

* a page being routed to the wrong Artifact;
* an incorrect student or Group Subject;
* an incomplete author list;
* an unreadable scan;
* a page being scanned twice;
* several Artifacts appearing in one source PDF;
* pages being scanned out of order;
* a missing continuation page;
* a corrected Group Membership;
* a revised moderation judgment;
* a teacher changing a Score after reviewing additional evidence;
* or a later record superseding an earlier decision.

If Concord corrects these situations by overwriting or deleting the earlier records, it becomes difficult or impossible to determine:

* what source evidence originally entered the system;
* how Concord routed it;
* what metadata was initially assigned;
* what a reviewer saw;
* why a correction was made;
* which evidence supported an earlier Score;
* or whether a later judgment differs from the original.

The retained source must therefore remain distinguishable from all derived records and interpretations.

## Decision

Concord will preserve the Core-retained source scan and maintain an explicit, non-destructive history of routing, attribution, review, moderation, correction, and scoring decisions.

The evidence chain will distinguish:

```text
physical classroom artifact
    -> Core-retained source scan
    -> Concord Scan Reference and routed representation
    -> Artifact metadata and attribution
    -> Review
    -> Moderation where required
    -> Score and evidence links
```

Each layer has a different purpose.

A later layer may describe, qualify, correct, or supersede an earlier decision. It must not silently alter the earlier source or erase the historical relationship.

## Evidence Layers

### Physical classroom artifact

The physical paper completed in the classroom is the original classroom object.

Concord does not assume that the physical page will be retained indefinitely after scanning. Physical-retention policies remain outside this ADR.

Once scanned, the system’s authoritative digital representation of that intake is the Core-retained source scan.

### Core-retained source scan

The **source scan** is the canonical digital evidence record for the material received during one scan-intake operation.

Core owns:

* source-scan retention;
* source-scan identity;
* intake provenance;
* shared routing-failure metadata;
* and shared resolution metadata.

The source scan may be:

* a PDF;
* an image;
* a multi-page document;
* a mixed batch;
* a duplicate intake;
* a rescan;
* or a scan later determined to be incomplete or unreadable.

Its evidentiary role does not depend on whether Concord routes it correctly on the first attempt.

### Concord Scan Reference

A **Scan Reference** is Concord’s association between an Artifact Page and a page or region from a Core-retained source scan.

A Scan Reference may identify:

* Core source-scan identifier;
* source page index;
* optional routed representation;
* expected Artifact Page;
* routing status;
* filing status;
* readability status;
* review status;
* and supersession relationship.

A Scan Reference does not become the source scan.

It points back to the retained source and records how Concord interpreted or routed part of that source.

### Routed representation

Concord may create a derived file for convenient review or filing, such as:

* one extracted PDF page;
* a cropped page image;
* a combined Artifact PDF;
* a reordered review copy;
* or another module-specific derivative.

A routed representation is an operational convenience.

It must retain provenance to:

* the Core source scan;
* the relevant source page;
* the Concord Scan Reference;
* and the intended Artifact Page.

A routed derivative must not be presented as though it were the only surviving source.

### Artifact metadata

Artifact metadata describes how the routed evidence relates to Concord concepts.

It may include:

* Activity;
* Session;
* Group;
* Artifact Instance;
* Artifact Page;
* Authors;
* Subjects;
* privacy classification;
* template version;
* and expected-return context.

Metadata is reviewable and correctable.

It is not embedded truth extracted from the scan.

### Review

A Review records a human examination of the Artifact and routed evidence.

It may determine:

* whether the scan is readable;
* whether all expected pages are present;
* whether filing is correct;
* whether Authors and Subjects are correct;
* whether privacy requires adjustment;
* whether the evidence is relevant;
* whether moderation is required;
* and whether the Artifact is ready for possible scoring use.

A Review describes a judgment made at a particular time.

It does not alter the source scan.

### Moderation

A Moderation Record determines whether evidence may be used consequentially and under what qualifications.

Moderation may apply to:

* peer observations;
* disputed Contribution Claims;
* conflicting Group accounts;
* contested authorship;
* incomplete evidence;
* or other evidence requiring human evaluation.

A later moderation decision may supersede an earlier one, but the earlier decision and rationale remain part of the record.

### Score

A Score Record is a teacher-approved criterion-level judgment.

It may cite one or more evidence sources.

A revised Score must not overwrite the earlier Score if the earlier record was finalized, exported, reported, or otherwise used.

Instead, the newer Score supersedes the earlier Score while preserving:

* the original value;
* the original scorer;
* the original evidence links;
* the original timestamp;
* and the reason for revision where applicable.

## Source Preservation Rules

### The source scan is not modified

Concord must not modify the retained source scan to:

* correct a student name;
* change an Artifact Subject;
* remove an unwanted page;
* reorder pages;
* improve legibility;
* redact ordinary filing errors;
* replace an incorrect QR code;
* or incorporate teacher annotations.

Corrections belong in linked metadata or new derived records.

### Derivatives do not replace the source

Concord may create derivatives for:

* splitting;
* routing;
* display;
* printing;
* redaction where authorized;
* or convenient Artifact assembly.

Every derivative must remain traceable to the retained source.

Deleting or regenerating a derivative must not delete or alter the Core source scan.

### Manual transcription is secondary

A teacher may manually enter:

* a transcription;
* a summary;
* a label;
* a note;
* or an evidence locator.

That record is secondary metadata.

It must not be represented as an exact replacement for the handwriting, drawing, diagram, or other source content.

### Image enhancement does not replace the source

A future implementation may create a view with:

* rotation correction;
* contrast adjustment;
* cropping;
* or other non-destructive display enhancement.

The enhanced view remains a derivative.

The original source scan must remain available.

### Redaction creates a derivative

When a redacted copy is needed for authorized sharing, Concord should create a redacted derivative.

The restricted source remains retained under its applicable privacy controls.

Redaction must not destroy the unredacted source unless an external legal or institutional retention requirement explicitly requires deletion.

Such a requirement would need separate policy and architecture work.

## Rescans

A rescan creates a new Core-retained source scan and a new or revised Concord Scan Reference.

It does not overwrite the earlier scan.

A rescan may be requested because the earlier scan was:

* unreadable;
* incomplete;
* incorrectly oriented;
* cropped;
* missing a page;
* associated with the wrong Artifact;
* or otherwise unsuitable.

The relationship should preserve:

* the earlier source-scan reference;
* the later source-scan reference;
* the reason for rescanning;
* the actor requesting or performing the rescan where available;
* the time of the rescan;
* and which Scan Reference is currently preferred for review or scoring.

The earlier scan may be marked:

* superseded for normal use;
* duplicate;
* unreadable;
* incomplete;
* or retained for provenance.

It remains part of the history.

## Duplicate Scans

Duplicate scans must remain representable.

The system may identify one Scan Reference as the preferred active reference while marking another as a duplicate.

Duplicate detection must not silently delete evidence because:

* apparently identical pages may contain subtle differences;
* one may be a later correction;
* one may be more readable;
* or the duplicate classification itself may be wrong.

A reviewer should be able to confirm or reverse the duplicate determination.

## Misrouted Evidence

A misrouted page remains associated with its source scan.

Correcting a misroute should:

1. preserve the original Scan Reference or routing attempt;
2. record that the earlier route was incorrect;
3. create or activate the corrected Scan Reference;
4. identify the actor and time of correction;
5. and preserve the reason where appropriate.

The source page itself does not change.

A correction must not make it appear that the page was always routed correctly.

## Missing and Unreadable Evidence

Missing and unreadable states describe evidence availability.

They must not be represented by:

* fabricated Artifacts;
* empty replacement scans;
* deletion of the expected Artifact Page;
* or automatic low Scores.

The system should preserve the distinction among:

* expected but not returned;
* returned but not scanned;
* scanned but unreadable;
* partially readable;
* missing page;
* duplicate page;
* unidentified page;
* conflicting route;
* and confirmed absent evidence.

A later scan may resolve the condition without erasing the earlier status history.

## Correction and Supersession

### Correction Record

Concord should support a general Correction Record or equivalent append-only correction relationship.

A Correction should identify:

* durable `correction_id`;
* target record type;
* target record identifier;
* correction type;
* reason;
* correcting actor;
* timestamp;
* replacement or superseding record where applicable;
* and optional explanatory note.

Corrections may apply to:

* filing metadata;
* Author attribution;
* Subject attribution;
* Group Membership;
* Role Assignment;
* Responsibility Assignment;
* Scan Reference;
* Artifact Review;
* Moderation Record;
* Score Record;
* Activity Event;
* Work Item;
* Contribution Claim;
* or another evidence-related record.

### Corrected versus superseded

A record is **corrected** when an error in its metadata or interpretation is identified.

A record is **superseded** when a later record intentionally replaces it as the current governing record.

Examples include:

* correcting a misspelled label;
* correcting an incorrect Subject;
* replacing an unreadable scan with a rescan;
* revising a moderation decision after additional evidence;
* or replacing a Score after reconsideration.

The contract phase may determine whether correction and supersession use:

* one generic record;
* record-specific fields;
* or both.

The semantic requirement is that the relationship remains explicit and historical.

### Current does not mean only

The system may designate one record as:

* current;
* active;
* preferred;
* effective;
* or governing.

That designation is a retrieval convenience.

It must not imply that earlier records have been deleted or never existed.

## Historical Records

The following records require preserved history once they have been used, relied upon, reviewed, or linked:

* source scans;
* Scan References;
* routed-evidence associations;
* Artifact Author relationships;
* Artifact Subject relationships;
* Group Memberships;
* Role Assignments;
* Responsibility Assignments;
* Reviews;
* Moderation Records;
* Contribution Claims;
* Score Records;
* and evidence links.

### Generated definitions and instances

Template Versions used to generate Artifacts must remain reproducible.

Once a Template Version has generated an Artifact Instance, changes to:

* wording;
* layout;
* page structure;
* QR placement;
* authorship expectations;
* subject expectations;
* or supported Criteria

require a new Template Version.

Packet Definitions used to generate Packet Instances must likewise retain their exact composition or revision.

A later template improvement must not make it appear that an earlier Artifact was generated from the new version.

### Draft records

This ADR does not require preserving every uncommitted interface edit or abandoned draft field.

An implementation may permit ordinary editing before a record becomes durable.

The preservation boundary begins when a record is:

* finalized;
* used as evidence;
* referenced by another durable record;
* reviewed;
* moderated;
* scored;
* exported;
* or otherwise treated as part of the Activity history.

The exact lifecycle transition must be defined in the conceptual contracts.

### Deletion

Routine user correction should not physically delete preserved evidence or durable history.

Records may instead be marked:

* cancelled;
* void;
* duplicate;
* invalid;
* rejected;
* superseded;
* or withdrawn.

Physical deletion may still be required for:

* test data;
* accidental imports containing no legitimate classroom evidence;
* legal obligations;
* institutional retention policy;
* privacy requirements;
* or administrative cleanup authorized outside the ordinary correction workflow.

Such deletion must be deliberate, permission-controlled, and auditable where technically feasible.

This ADR does not establish a final legal or institutional retention policy.

## Provenance Requirements

Concord must preserve enough provenance to reconstruct the evidence chain.

Depending on record type, provenance should identify:

* durable record identifier;
* source record or parent record;
* Activity and Session context;
* Artifact Instance and Artifact Page;
* Template Version;
* Core source-scan reference;
* source page index;
* routed representation;
* creating or correcting actor;
* reviewer;
* moderator;
* scorer;
* creation or decision timestamp;
* superseded record;
* superseding record;
* and reason for correction or change.

The exact fields belong in later contracts.

The architectural requirement is that a teacher or maintainer can determine:

* where the evidence came from;
* how it entered Concord;
* how it was classified;
* what changed;
* who made the change;
* and which record is currently governing.

## Evidence Links and Historical Scores

A Score Evidence Link should reference durable evidence identities.

If the evidence’s metadata is later corrected, the Score must remain traceable to:

* the evidence source used;
* the applicable review or moderation state;
* and the historical context in which the Score was made.

A later correction may require:

* no Score change;
* a new Review;
* a new Moderation Record;
* a revised Score;
* or a new evidence link.

The system must not silently retarget an existing Score to different evidence.

For example, if a Score originally cited Scan Reference A and a rescan creates Scan Reference B, Concord must not replace A with B inside the historical Score without recording that change.

A revised Score may cite B and supersede the earlier Score.

## Export and Reporting Implications

When Concord exports Scores or evidence references, the export should preserve stable identifiers sufficient to reconnect the exported result to its source history.

If a Score is later superseded:

* the historical export remains an accurate statement of what was exported at that time;
* the current Concord state identifies the newer Score;
* and downstream systems may receive a correction or replacement through a future integration contract.

Concord must not rewrite prior external exports as though the newer decision had always existed.

Grade calculation and formal reporting remain outside Concord.

## Privacy and History

Historical preservation does not mean unrestricted visibility.

Earlier or superseded records may require equal or greater privacy protection than current records.

Examples include:

* disputed peer observations;
* corrected Subject assignments;
* withdrawn Contribution Claims;
* teacher notes;
* rejected moderation evidence;
* and superseded Scores.

Access control should consider:

* record type;
* privacy classification;
* current or superseded state;
* Author;
* Subject;
* and authorized role.

Superseded or rejected evidence must not become more visible merely because it is no longer current.

## Consequences

### Positive consequences

* Original digital evidence remains inspectable.
* Filing and attribution errors can be corrected without altering the source.
* Rescans and duplicates can be compared.
* Review and moderation decisions remain accountable.
* Revised Scores can be explained.
* Earlier exports can be interpreted accurately.
* Template and packet history remains reproducible.
* Evidence provenance survives routing and file reorganization.
* Audit and troubleshooting workflows have reliable historical context.
* Teachers can determine what changed and why.
* Later implementation changes cannot silently rewrite earlier classroom records.

### Negative consequences

* Storage use increases because source scans, derivatives, rescans, and superseded records are retained.
* Data contracts require identifiers, statuses, timestamps, and supersession relationships.
* Queries must distinguish current records from historical records.
* User interfaces must avoid overwhelming teachers with obsolete versions.
* Correction workflows are more complex than direct editing.
* Privacy controls must apply to historical as well as current evidence.
* Export corrections require explicit downstream behavior.
* Retention and deletion policies will require additional institutional decisions.

### Implementation consequences

Implementations must:

* retain Core source-scan references;
* distinguish source scans from routed derivatives;
* prevent Concord from modifying Core-retained source files;
* maintain provenance from derivatives to source pages;
* create new records for rescans and consequential corrections;
* support duplicate, unreadable, incomplete, conflicting, and misrouted states;
* support current or preferred-record resolution;
* preserve superseded Reviews, Moderation Records, and Scores;
* preserve Template Versions and Packet Definition revisions used by generated instances;
* avoid silently retargeting evidence links;
* and provide teacher-facing history where correction context matters.

Normal interfaces may display the current effective record by default, but they must make historical records discoverable to authorized users.

## Alternatives Considered

### Alternative 1: Replace the source scan after correction

Rejected.

Replacing the source would destroy evidence of what originally entered the system and prevent later verification of routing, interpretation, or correction.

### Alternative 2: Store only routed Artifact files

Rejected.

Routed files may be:

* split;
* cropped;
* reordered;
* combined;
* renamed;
* or regenerated.

Without the retained source, Concord could not reliably reconstruct the original intake or investigate routing errors.

### Alternative 3: Modify the scan to correct metadata

Rejected.

Names, Authors, Subjects, Activity context, and filing decisions are metadata.

Editing the image or PDF would blur the distinction between the completed Artifact and later administrative interpretation.

### Alternative 4: Delete unreadable or duplicate scans

Rejected as the ordinary workflow.

An unreadable scan may explain why evidence was unavailable, and an apparent duplicate may later prove to be a correction or distinct page.

Such records should be classified, not silently removed.

### Alternative 5: Overwrite Reviews and moderation decisions

Rejected.

A changed judgment may affect evidence use and Scores.

Preserving the earlier decision and rationale is necessary to explain later changes.

### Alternative 6: Edit finalized Scores in place

Rejected.

A finalized or exported Score is a historical judgment.

A revised Score should supersede it so that the original value, evidence, and scorer remain recoverable.

### Alternative 7: Preserve source scans but overwrite all metadata

Rejected.

Source preservation alone is insufficient.

Without metadata history, Concord could not explain:

* why a page moved;
* why an Author changed;
* why evidence became restricted;
* or why a Score was revised.

### Alternative 8: Use filenames and folder locations as provenance

Rejected.

Files may be:

* renamed;
* reorganized;
* copied;
* exported;
* or restored.

Durable identifiers and explicit references are required.

### Alternative 9: Preserve every transient interface edit

Rejected.

Maintaining every keystroke or abandoned draft would impose complexity without corresponding evidentiary value.

History becomes mandatory when a record is durable, relied upon, or linked to evidence.

### Alternative 10: Keep only the newest record

Rejected.

The newest record may be current, but it does not explain:

* previous decisions;
* earlier exports;
* changed attributions;
* or the provenance of revised Scores.

### Alternative 11: Treat a rescan as the same source scan

Rejected.

A rescan is a separate intake event and may differ in:

* completeness;
* legibility;
* orientation;
* page boundaries;
* or content.

It requires its own source identity and relationship to the earlier scan.

## Required Follow-Up

Later conceptual contracts must define:

* Core source-scan reference structure;
* Concord Scan Reference structure;
* source-page indexing;
* routed-derivative provenance;
* routing, readability, filing, duplicate, and missing-page statuses;
* rescan relationships;
* Correction Record structure;
* supersession fields;
* current-record resolution;
* immutable Template Version and Packet Definition references;
* revised Review, Moderation Record, and Score behavior;
* evidence-link history;
* privacy controls for superseded records;
* and authorized deletion or retention-policy hooks.

Representative contract examples should test at least:

* one mixed-batch source scan producing several Artifact Pages;
* one multi-page Artifact assembled from several source pages;
* one page routed incorrectly and later corrected;
* one unreadable scan followed by a rescan;
* one duplicate scan;
* one missing continuation page later supplied;
* one corrected Author;
* one corrected Subject;
* one superseded Review;
* one revised moderation decision;
* one revised Score retaining the earlier Score;
* and one exported Score later superseded.

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

## Notes

This ADR establishes the preservation and historical-integrity model.

It does not fully define the semantic separation among Review, Moderation, Score, Grade, and Report, which is addressed in ADR 0008. It also does not establish final institutional retention periods, legal deletion requirements, or backup policy.
