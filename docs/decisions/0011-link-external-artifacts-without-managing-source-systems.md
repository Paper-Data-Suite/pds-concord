# ADR 0011: Link External Artifacts Without Managing Source Systems

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Collaborative classroom work frequently produces evidence outside Concord’s normal generated-paper workflow.

Examples include:

* source code;
* repository content;
* digital documents;
* presentation slides;
* spreadsheets;
* CAD drawings;
* engineering files;
* photographs;
* screenshots;
* videos;
* diagrams;
* schematics;
* posters;
* physical models;
* laboratory graphs;
* printed worksheets;
* planning boards;
* test outputs;
* cloud documents;
* learning-management-system submissions;
* and files created in subject-specific applications.

These materials may be relevant to Concord because they document:

* a Group product;
* an individual Contribution;
* a design decision;
* a testing result;
* a handoff;
* a milestone;
* an Activity Event;
* or evidence considered during Scoring.

However, those materials are often owned and managed by another system.

Examples of authoritative source systems include:

* a source-control repository;
* a cloud-document platform;
* a learning-management system;
* a CAD application or project repository;
* a school file server;
* a local project directory;
* a media-management system;
* another Paper Data Suite module;
* or a physical classroom storage process.

Concord cannot become the authoritative manager for every external format or source system.

Doing so would require Concord to implement or duplicate:

* file synchronization;
* repository cloning;
* source-control history;
* cloud-document revision history;
* access-control systems;
* CAD-file parsing;
* native application previews;
* project-file validation;
* media processing;
* document collaboration;
* and format-specific version management.

That work is outside Concord’s purpose as a paper-first collaborative-evidence system.

At the same time, storing only an informal note such as “see project file” would provide inadequate provenance.

Concord must be able to identify:

* what external work was considered;
* where it was located;
* which Activity or component it concerned;
* which version or snapshot was reviewed;
* whether it remained available;
* who was claimed to have contributed;
* and how it informed a later judgment.

The architecture therefore needs a clear boundary between **linking external work** and **managing the system that owns that work**.

## Decision

Concord may create durable records that identify, contextualize, and reference external physical or digital Artifacts.

Concord will not become the authoritative:

* source repository;
* version-control system;
* cloud-document manager;
* CAD or engineering-file manager;
* learning-management system;
* native-format inspector;
* or digital edit-history service

for those Artifacts.

The normal relationship is:

```text
authoritative external system or physical object
    -> Concord External Reference or Attachment
    -> optional reviewed snapshot, printout, photograph, or cover sheet
    -> optional Score Evidence Link
```

The authoritative source remains external.

Concord records the relationship and the classroom-evidence context.

## Core Concepts

### External artifact

An **external artifact** is physical or digital work relevant to a Concord Activity but not generated as a normal Concord Artifact Page.

Examples include:

* a software repository;
* one source-code file;
* a cloud document;
* a slide deck;
* a spreadsheet;
* a CAD model;
* a schematic;
* a photograph of a prototype;
* a printed graph;
* a teacher-provided laboratory worksheet;
* a physical poster;
* or a project demonstration file.

“External” describes ownership and lifecycle, not importance.

An external Artifact may be central evidence for a Score while still remaining outside Concord’s management authority.

### External Reference

An **External Reference** represents a durable Concord relationship to a record, file, object, location, or identifier owned elsewhere.

An External Reference should be capable of recording:

* durable `external_reference_id`;
* owning module, system, or source category;
* external record or artifact type;
* external identifier, path, URI, or human-entered location;
* relationship purpose;
* related Concord Activity;
* optional Session;
* optional Group;
* optional Work Item;
* optional Activity Event;
* optional Artifact Instance;
* optional Criterion or Score;
* descriptive label;
* version, revision, build, iteration, or snapshot label where known;
* availability status;
* access or privacy classification;
* creation provenance;
* last-confirmed timestamp where applicable;
* and correction or supersession history.

The external identifier may be:

* a repository identifier;
* commit or tag supplied by the teacher;
* cloud-document identifier;
* LMS submission identifier;
* local path;
* shared-drive path;
* file label;
* cabinet or physical-storage location;
* another module’s durable record identifier;
* or another appropriate source-specific locator.

The precise field structure belongs in later contracts.

### Attachment

An **Attachment** represents physical or digital work associated with Concord that is not a normal generated Concord Artifact Page.

An Attachment may identify:

* poster;
* graph paper;
* photograph;
* screenshot;
* printed source code;
* diagram;
* schematic;
* project file;
* teacher-created worksheet;
* external digital file;
* or another related item.

An Attachment should be capable of recording:

* durable `attachment_id`;
* parent Activity;
* optional Session, Group, Work Item, Event, or Artifact context;
* attachment type;
* title or label;
* contributor references;
* physical or digital location reference;
* version or iteration label;
* availability status;
* privacy classification;
* provenance;
* and optional related External References.

An Attachment may represent:

1. a locally retained evidence object;
2. metadata about a physical object;
3. a teacher-supplied snapshot of external work;
4. or a Concord record linking related work to the Activity.

### Artifact Cover Sheet

An **Artifact Cover Sheet** is a Concord-generated Artifact used to associate external or attached work with Concord context.

A cover sheet may record:

* external Artifact title;
* Artifact type;
* Activity;
* Session;
* Group;
* project component;
* Work Item;
* milestone;
* claimed contributors;
* version or iteration;
* number of attached pages or files;
* external location;
* related Concord Artifacts;
* privacy classification;
* and teacher filing confirmation.

The cover sheet is a Concord Artifact.

The work it identifies remains an Attachment or external Artifact.

For example:

```text
Concord Artifact:
Artifact Cover Sheet

External artifact:
CAD model for bridge prototype

External location:
Teacher-entered project-folder reference

Snapshot:
Printed CAD view attached to the cover sheet

Context:
Project Group 2, Design Milestone
```

The cover sheet does not make Concord the owner of the CAD model.

## Distinction from Scan Reference

An Attachment or External Reference is not a Scan Reference.

A **Scan Reference** links:

* one Core-retained source scan or source page;
* to one Concord Artifact Page.

An **Attachment** identifies related physical or digital work that may have:

* its own file;
* photograph;
* printout;
* cover sheet;
* or external location.

An **External Reference** identifies a relationship to a source record or location owned elsewhere.

These concepts may be connected.

For example:

```text
External repository
    -> External Reference

Printed source-code excerpt
    -> Attachment

Artifact Cover Sheet
    -> Concord Artifact Page
    -> Core-retained scan
    -> Scan Reference
```

The existence of a scanned printout does not transfer authority over the repository to Concord.

Likewise, a repository link does not replace the retained scan of a submitted printout.

## Source-System Authority

The originating system remains authoritative for its native records and lifecycle.

Examples include:

* Git or another source-control system for repository content and commit history;
* a cloud-document platform for collaborative revision history;
* a CAD system for native design files;
* an LMS for authoritative submission records;
* a school file server for stored project files;
* ScoreForm for ScoreForm records;
* Quillan for Quillan records;
* and the teacher’s physical storage process for an unscanned physical object.

Concord may record:

* a stable identifier;
* a location;
* a teacher-supplied version label;
* a teacher-supplied commit or revision identifier;
* a reviewed snapshot;
* a printed derivative;
* or a description.

Concord must not claim that its record is the authoritative native history when that history belongs elsewhere.

## Prohibited Source-System Management

Concord will not, as part of its foundational responsibility:

* clone repositories;
* pull or push source-control changes;
* create branches;
* inspect commit histories automatically;
* calculate contribution from commit counts;
* synchronize cloud-document content;
* reproduce cloud-document revision history;
* edit external project files;
* manage CAD assemblies;
* parse arbitrary native engineering formats;
* manage LMS submissions;
* provide collaborative document editing;
* track file locks;
* resolve external merge conflicts;
* maintain external access permissions;
* manage external-system accounts;
* or replace the source system’s backup and recovery process.

Future integrations may retrieve narrowly defined metadata through deliberate contracts.

Such integrations must not silently expand Concord into the owning system.

## Native-Format Interpretation

Concord is not required to understand the internal semantics of external native formats.

It does not need to determine automatically:

* whether source code is correct;
* whether a repository builds;
* whether a CAD file is structurally valid;
* whether a spreadsheet formula is accurate;
* whether a cloud document contains substantial revisions;
* whether a presentation is complete;
* or whether an engineering file matches a physical product.

Those judgments remain:

* human-reviewed;
* owned by a subject-specific tool;
* or handled by another authorized system.

Concord may store a teacher-entered description or reviewed result without parsing the native file itself.

## Stable Reference When Sufficient

When a durable external identifier is sufficient, Concord should store a reference rather than copy the full external record.

For example:

```text
Owning system:
Source-control repository

External record type:
Commit

External identifier:
Teacher-supplied commit hash

Relationship:
Version reviewed during Milestone 3
```

A stable reference reduces:

* duplication;
* stale copies;
* storage burden;
* conflicting versions;
* and ambiguity about the authoritative system.

However, a reference is sufficient only when it gives the teacher an appropriate, durable way to identify the reviewed work.

## Snapshots and Captured Derivatives

Concord may retain a teacher-supplied snapshot or derivative when useful for evidence preservation.

Examples include:

* screenshot;
* exported PDF;
* printed source-code excerpt;
* photograph of a prototype;
* image of a planning board;
* CAD printout;
* test-output capture;
* or downloaded document version.

A captured derivative should preserve:

* capture or submission timestamp;
* source-system reference where available;
* version or iteration label;
* capturing or submitting actor;
* privacy classification;
* relationship to the parent Activity;
* and a clear indication that it is a snapshot or derivative.

### Snapshot is not live source

A retained snapshot represents the state captured at a particular time.

It does not guarantee that:

* the external source remains unchanged;
* the current external file still matches;
* the location remains available;
* or the snapshot includes the source’s complete history.

The interface should distinguish:

* external current location;
* last confirmed location;
* captured snapshot;
* printed derivative;
* and authoritative source.

### Concord does not synchronize snapshots

Concord does not need to monitor the external system continuously or replace the snapshot automatically when the source changes.

A later snapshot should become a new or superseding Attachment or reference state with preserved chronology.

## Version and Iteration Context

Concord may store human-entered contextual labels such as:

* iteration 2;
* prototype B;
* build 4;
* revision C;
* code version tested;
* file label;
* document revision supplied by teacher;
* or teacher-supplied commit identifier.

These labels help identify the work that was reviewed.

They are not substitutes for the authoritative source system’s full version history.

For example:

```text
Concord version label:
Prototype B

External system:
CAD project directory

Meaning:
The teacher reviewed the item identified in class as Prototype B.

Not implied:
Concord manages the CAD revision graph.
```

## External-Reference Availability

An External Reference or Attachment may become:

* available;
* unavailable;
* moved;
* inaccessible;
* permission restricted;
* deleted externally;
* replaced;
* superseded;
* archived;
* or not yet supplied.

Availability must be represented explicitly.

An unavailable source must not automatically be treated as:

* missing student performance;
* nonparticipation;
* a failed task;
* insufficient contribution;
* a zero;
* or the lowest Score.

The teacher may determine that:

* a retained snapshot remains sufficient;
* other evidence is sufficient;
* the Score should be deferred;
* evidence is insufficient;
* or no Score change is needed.

Exceptional Score behavior remains governed by ADR 0010.

### Link checking

A future implementation may check whether a local path or supported external reference appears reachable.

That check determines technical availability only.

It does not establish:

* authenticity;
* completeness;
* authorship;
* quality;
* currentness;
* or relevance.

A failed reachability check must not alter a Score automatically.

## Authorship and Contribution

External ownership metadata does not establish Artifact authorship or student Contribution.

Concord must not infer sole authorship from:

* repository ownership;
* account ownership;
* upload identity;
* document ownership;
* file creator metadata;
* local filesystem owner;
* commit count;
* most recent editor;
* device ownership;
* folder location;
* or the person who supplied the link.

These may be provenance signals.

They are not conclusive evidence of who:

* designed;
* researched;
* wrote;
* built;
* tested;
* debugged;
* revised;
* explained;
* reviewed;
* or integrated the work.

### Explicit contributor records

An Attachment or Artifact Cover Sheet may list claimed contributors.

Those claims may come from:

* the contributor;
* a Group recorder;
* the teacher;
* a Group consensus statement;
* a handoff record;
* or another reviewed source.

Contributor records remain distinct from:

* Artifact Authors;
* Group Membership;
* repository metadata;
* and Score targets.

A disputed or student-created claim may require Moderation before consequential use.

### File ownership is not sole contribution

A file stored under one student’s account may represent:

* Group work;
* a handoff;
* a shared device;
* imported work;
* a teacher-provided starting file;
* or a final integration performed by one participant.

Likewise, a student may have made a significant Contribution without owning or editing the final file.

## External Artifacts as Evidence

An external Artifact, Attachment, snapshot, or External Reference may function as evidence after appropriate Review.

Review may determine:

* whether the reference resolves;
* whether the item matches the intended Activity;
* which version was examined;
* whether the snapshot is readable;
* whether claimed contributors are plausible;
* which Subjects or components it concerns;
* whether privacy restrictions apply;
* whether Moderation is required;
* and whether it is suitable for Scoring consideration.

An external Artifact does not become a Score automatically.

### Score Evidence Links

A Score Record may link to an external Artifact through:

* an Attachment Evidence Reference;
* an External Reference;
* a reviewed Artifact Cover Sheet;
* a captured snapshot;
* or another authorized evidence record.

The Score Evidence Link should identify:

* the specific evidence source;
* optional version or snapshot;
* relevant component or Work Item;
* use or relevance description;
* and applicable Moderation state.

For example:

```text
Score:
Student A — contributes to testing

Evidence:
Attachment representing test-output screenshot

External reference:
Project repository, teacher-supplied tested revision

Use:
Corroborates teacher observation that Student A executed and
documented the test procedure.
```

The link does not mean that Concord inspected the repository or proved authorship automatically.

## External Artifact as Subject

An external Artifact may be an Artifact Subject.

For example, an Artifact Cover Sheet or teacher Review may concern:

* one project file;
* one prototype;
* one code component;
* one diagram;
* one presentation;
* or one repository state.

The external Artifact’s typed Subject reference must remain distinct from:

* the people who authored the cover sheet;
* the people claimed to have contributed;
* and the later Score targets.

## Physical Artifacts

Some external Artifacts are physical.

Examples include:

* model;
* poster;
* prototype;
* laboratory setup;
* construction;
* notebook;
* planning board;
* or display.

Concord may identify a physical Artifact through:

* Attachment record;
* photograph;
* cover sheet;
* teacher-entered location;
* storage label;
* or other evidence reference.

Concord does not need to become a physical inventory-management system.

It is not responsible for:

* long-term storage;
* check-in/check-out;
* asset depreciation;
* maintenance scheduling;
* or loss-prevention tracking.

A location such as `Room 214, project shelf B` is evidence context, not a guaranteed inventory record.

## Printed External Work

External digital work may be printed and returned with a Concord cover sheet.

Examples include:

* source-code printout;
* CAD view;
* spreadsheet output;
* slide handout;
* document excerpt;
* or test report.

The scanned printout becomes retained evidence of the submitted representation.

It does not become the authoritative native external file.

The system should preserve both relationships when available:

```text
Printed representation
    -> scanned and retained through Core provenance

External original
    -> External Reference
```

The teacher can then determine whether the printed representation is sufficient or whether the external original must also be reviewed.

## Privacy and Access Control

External references may point to restricted material.

Concord must not:

* bypass source-system permissions;
* store passwords;
* store access tokens in ordinary evidence records;
* expose private repository links to unauthorized users;
* make restricted cloud documents public;
* or copy sensitive external content merely to simplify access.

### Source-system permissions

The external system remains authoritative for access to its native record.

Concord may separately control access to:

* the External Reference metadata;
* local snapshot;
* cover sheet;
* contributor claim;
* Review;
* and Score Evidence Link.

Access to a Concord Score does not automatically authorize access to the complete external source.

### Link secrecy is not access control

A URL or local path should not be treated as secure merely because it is difficult to guess.

Privacy classification and authorization remain explicit.

### Sensitive locations

External-location records may reveal:

* student account names;
* internal server paths;
* private repository names;
* classroom storage locations;
* or restricted document identifiers.

Interfaces and exports should disclose only the minimum necessary information.

## Local-First Operation

Concord’s core workflow must remain usable without continuous access to an external service.

A teacher may:

* enter an External Reference while offline;
* retain a snapshot or printout;
* record a version label;
* review locally available evidence;
* and later update availability.

Concord does not require cloud synchronization to create or preserve the relationship.

A live external source may provide additional evidence, but the foundational Activity record must not depend on continuous connectivity.

## Corrections and History

External References and Attachments may require correction.

Examples include:

* incorrect path;
* wrong repository;
* incorrect version label;
* mistaken component relationship;
* changed availability;
* corrected contributor list;
* or a replacement snapshot.

Consequential corrections must preserve:

* earlier reference;
* correction reason;
* correcting actor;
* correction timestamp;
* replacement or superseding record;
* and historical Score relationships.

### External changes

The external source may change without Concord being notified.

Concord does not claim to preserve every external change.

It preserves:

* what reference was recorded;
* what snapshot was retained;
* what version label was supplied;
* what the reviewer examined;
* and what evidence was used at the time of Scoring.

### Historical Scores

A historical Score must remain linked to the external evidence state used when the Score was made.

If a later external revision is reviewed, the teacher may:

* leave the Score unchanged;
* add new evidence;
* revise the rationale;
* or create a superseding Score.

The system must not silently retarget the historical Score to the newest external version.

## System-Specific Integrations

A future integration may provide limited functionality for a particular source system.

Examples include:

* resolving a repository identifier;
* reading a supplied commit label;
* confirming that a cloud-document identifier exists;
* retrieving a permitted preview;
* or opening an existing local file.

Such functionality requires a deliberate contract defining:

* supported source system;
* accepted identifiers;
* authentication boundary;
* retrieved metadata;
* failure behavior;
* privacy behavior;
* caching behavior;
* and ownership.

A system-specific adapter must not change the foundational rule that the external system remains authoritative.

## Relationship to Other Paper Data Suite Modules

ScoreForm, Quillan, Core, and future Paper Data Suite modules may also own records referenced by Concord.

Those records use the same general External Reference principle:

* store the owning module;
* store the external record type;
* store the durable external identifier;
* record the relationship purpose;
* preserve availability;
* and avoid copying the full record when a stable reference is sufficient.

The more specific boundary between Concord, ScoreForm, and Quillan is recorded in ADR 0012.

## Consequences

### Positive consequences

* Concord can use external project work as evidence.
* Source-control, CAD, cloud-document, LMS, and other systems retain clear authority.
* Native project files do not need to be imported into Concord.
* Stable references reduce duplication and stale copies.
* Snapshots and printouts can preserve the reviewed state when necessary.
* Physical and digital work can use a shared Attachment concept.
* Artifact Cover Sheets provide a paper-first connection to external work.
* External unavailability remains distinct from student performance.
* Authorship is not inferred from account or file ownership.
* Scores can retain provenance to the reviewed version or snapshot.
* Local-first workflows remain possible.
* Future integrations can be added without changing fundamental ownership.

### Negative consequences

* Concord cannot guarantee that an external reference remains accessible.
* Teachers may need to record version or snapshot context manually.
* Native external history may require opening another system.
* A link may become stale or permission restricted.
* Concord may retain both a reference and a snapshot, requiring clear interface labels.
* External-source privacy rules add integration complexity.
* Teachers must review contributor claims rather than relying on file metadata.
* Format-specific validation remains outside Concord.
* Historical evidence may require preserving references to versions no longer available externally.
* Cross-system corrections may require coordinated workflows.

### Implementation consequences

Implementations must:

* distinguish External References, Attachments, Artifact Pages, and Scan References;
* assign durable identifiers to External References and Attachments;
* record the owning source or system;
* support physical and digital locations;
* support version, revision, build, iteration, or snapshot labels;
* support explicit availability states;
* allow optional captured derivatives;
* mark snapshots as time-bounded representations;
* preserve provenance;
* prohibit automatic authorship inference;
* support contributor references separately;
* permit external evidence in Score Evidence Links;
* enforce record-specific privacy;
* avoid storing ordinary credentials in evidence metadata;
* preserve corrections and supersession;
* and avoid treating unavailable external work as a low Score.

Teacher-facing interfaces should make the source boundary explicit with labels such as:

* **External source**;
* **Authoritative location**;
* **Captured snapshot**;
* **Printed representation**;
* **Version reviewed**;
* **Last confirmed available**;
* **Claimed contributors**;
* and **Teacher-confirmed contributors**.

## Alternatives Considered

### Alternative 1: Import every external file into Concord

Rejected.

This would:

* duplicate authoritative files;
* create stale copies;
* increase storage requirements;
* complicate privacy;
* and imply ownership of formats Concord does not manage.

Snapshots may be retained selectively, but wholesale import is not the default architecture.

### Alternative 2: Store only a URL or path string

Rejected.

A bare location does not preserve:

* owning system;
* relationship purpose;
* version reviewed;
* availability;
* Activity context;
* privacy;
* or provenance.

External References require structured metadata.

### Alternative 3: Clone source repositories

Rejected.

Repository cloning would make Concord responsible for:

* synchronization;
* branch state;
* authentication;
* storage;
* conflicts;
* and repository lifecycle.

Source control remains authoritative.

### Alternative 4: Inspect commit history to calculate Contribution

Rejected.

Commit history does not fully represent:

* design;
* testing;
* debugging;
* pair programming;
* research;
* verbal coordination;
* physical construction;
* or work performed under a shared account.

Contribution remains a human-reviewed evidence question.

### Alternative 5: Parse all native project formats

Rejected.

Supporting arbitrary:

* CAD;
* engineering;
* presentation;
* spreadsheet;
* media;
* and project formats

would turn Concord into a collection of subject-specific applications.

### Alternative 6: Infer authorship from file or account ownership

Rejected.

Ownership metadata is not proof of authorship or Contribution.

### Alternative 7: Treat the newest external version as the version historically scored

Rejected.

The source may change after Scoring.

Historical Scores must remain connected to the version, snapshot, or reference state actually reviewed.

### Alternative 8: Snapshot every external source automatically

Rejected.

Automatic snapshotting would:

* create storage burden;
* duplicate sensitive content;
* require broad authentication;
* and create uncertainty about synchronization.

Snapshots remain deliberate and contextual.

### Alternative 9: Never retain snapshots

Rejected.

A reference may later become unavailable or change.

Teacher-supplied snapshots, exports, printouts, or photographs may be necessary to preserve the reviewed evidence state.

### Alternative 10: Treat an unavailable external source as missing student work

Rejected.

Technical unavailability does not establish nonperformance.

### Alternative 11: Require all external work to be converted into a Concord Artifact

Rejected.

Concord should not force source code, CAD models, cloud documents, or physical products into a generic generated form.

A cover sheet or Attachment relationship is sufficient.

### Alternative 12: Use Scan Reference for all external work

Rejected.

A Scan Reference has the specific purpose of linking a Core-retained source scan to a Concord Artifact Page.

It is not a general external-system reference.

### Alternative 13: Make Concord a physical inventory system

Rejected.

Physical location may be recorded as evidence context, but asset management is outside Concord.

### Alternative 14: Bypass source-system permissions by copying content

Rejected.

Copying restricted content to avoid the authoritative system’s access rules creates privacy and governance risks.

### Alternative 15: Require continuous external connectivity

Rejected.

Concord is paper-first and local-first.

External integration must not prevent offline Activity, evidence review, or preservation of previously captured records.

## Required Follow-Up

Later conceptual contracts must define:

* `ExternalReference` structure;
* `Attachment` structure;
* relationship between Attachments and External References;
* allowed source-system categories;
* external identifier and location representation;
* availability statuses;
* version, build, iteration, revision, and snapshot context;
* captured-derivative provenance;
* Artifact Cover Sheet relationships;
* physical-location representation;
* contributor and authorship-review behavior;
* privacy and authorization rules;
* external-evidence Review;
* Score Evidence Links to external sources;
* correction and supersession behavior;
* behavior when an external source moves or becomes unavailable;
* and optional adapter boundaries for supported systems.

Representative contract examples should test at least:

* one local external file;
* one repository reference with a teacher-supplied commit identifier;
* one cloud-document reference;
* one CAD model with a printed snapshot;
* one photograph of a physical prototype;
* one teacher-provided worksheet attached through a cover sheet;
* one external Artifact with several claimed contributors;
* one file owned by one account but reviewed as Group work;
* one unavailable external reference with a retained snapshot;
* one moved external location;
* one replacement snapshot;
* one external Artifact supporting several Scores;
* one historical Score tied to an older external version;
* one restricted external source referenced by a less-restricted Score;
* and one offline workflow using a human-entered external location.

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

## Notes

This ADR establishes how Concord relates to physical and digital work owned outside its normal Artifact workflow.

It does not fully define the specialized relationship between Concord, ScoreForm, and Quillan. That decision is addressed in ADR 0012.
