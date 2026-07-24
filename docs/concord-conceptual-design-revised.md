# pds-concord Conceptual Design

**Status:** Draft for foundation review  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Date:** July 23, 2026  
**Revision:** 3 — aligned with `pds-core` 0.5/PDS2 and ADR 0014

## 1. Purpose

`pds-concord` is a Paper Data Suite module for creating, organizing, printing, scanning, filing, reviewing, moderating, and scoring paper artifacts used during collaborative classroom activities.

The module exists because collaborative learning produces evidence that is often difficult to preserve. A teacher cannot observe every Group continuously, and important evidence may be distributed across discussion notes, shared organizers, peer observations, contribution records, teacher trackers, attached project work, and scoring forms.

Concord provides a paper-first workflow for turning those temporary classroom records into organized, reviewable evidence and teacher-approved judgments.

Paper Data Suite is predominantly standards-based. Concord therefore uses standards-based scoring as its primary academic scoring model while retaining legitimate local Criteria for collaborative procedures, roles, responsibilities, and Activity-specific expectations.

Concord is not a lesson-planning system. It begins after the teacher has already decided what Activity students will complete, what evidence would be useful, and—when the Activity is intended to produce academic judgments—which standards the Activity will evaluate.

This document defines Concord’s conceptual scope and architecture. More detailed record-level requirements are governed by:

- `docs/design/initial-concord-domain-model.md`;
- `docs/design/conceptual-data-contracts.md`;
- the accepted Concord ADRs, including ADR 0014;
- and the released `pds-core` 0.5/PDS2 contracts.

When this document conflicts with an accepted ADR or a later finalized conceptual contract, the accepted ADR or later contract governs.

## 2. Core Definition

> Concord is a paper-based collaborative-evidence and standards-scoring system.

It helps teachers create and manage scannable paper templates that document what happened during discussions, seminars, laboratories, projects, design activities, and other collaborative work.

The retained source scan remains the canonical evidence record. Concord may attach metadata, Review decisions, Moderation decisions, evidence links, and teacher-approved Scores to that source, but it does not attempt to interpret handwriting, transcribe discussion, infer student behavior, or assign Scores automatically.

For academic scoring, Concord normally organizes judgment through:

```text
collaborative evidence
    -> standard-backed Criterion
    -> teacher-approved Score
    -> future standards-based grading and reporting
```

Concord also supports local Criteria when an Activity needs to record or score an expectation that is not a direct standards judgment.

## 3. Scope

Concord is responsible for:

- configuring an already-planned collaborative Activity;
- declaring whether the Activity is evidence-only, standards-based, mixed, or local-criteria-only;
- selecting a Core-owned standards profile and ordered Focus Standards when standards-based scoring is used;
- generating printable collaborative-learning templates;
- combining related templates into versioned Activity packets;
- assigning generated Artifact Instances to Activities, Sessions, Groups, participants, or other supported contexts;
- creating an Artifact Page identity before printing each returnable page;
- registering page-level PDS2 routes and adding QR codes and human-readable fallback identifiers;
- receiving scanned pages or PDFs through Core’s source-retention and dispatch infrastructure;
- resolving routed pages to existing Artifact Page records;
- preserving the original scan as the source record;
- supporting teacher Review of scanned evidence;
- supporting Moderation when evidence requires a reliability, fairness, or permitted-use judgment;
- defining standard-backed and local Criteria;
- recording criterion-level teacher-approved Scores;
- distinguishing individual, Group, Artifact, Session, Activity, and component targets;
- recording who completed, observed, reviewed, moderated, corrected, or scored a record;
- linking Concord evidence to related Paper Data Suite records;
- preserving standards identity, scale identity, evidence provenance, and supersession history;
- making approved standard-backed Scores available through a future standards-result handoff contract;
- making local Scores and evidence references distinguishable from direct standards results;
- and supporting paper-first, local-first, and offline classroom workflows.

## 4. Non-Goals

Concord does not:

- perform optical mark recognition;
- replace `pds-scoreform`;
- recognize or interpret handwriting;
- evaluate extended written responses;
- replace `pds-quillan`;
- reimplement PDS Core workspace, roster, identifier, PDS2, route-registration, source-retention, dispatch, or standards infrastructure;
- create a competing standards library or standards-profile system;
- transcribe audio or video;
- create automated or AI-generated records of classroom discussion;
- perform automated scoring of collaborative behavior;
- infer a standards Score from the presence of evidence or standards metadata;
- infer mastery, proficiency, growth, or a course Grade from one Concord Score;
- convert ScoreForm or Quillan results into Concord Scores automatically;
- require every Activity to select standards or produce Scores;
- force every useful collaborative Criterion to be a standard;
- plan lessons or design units;
- calculate marking-period or course Grades;
- aggregate results across Activities, modules, courses, terms, or years;
- normalize or convert Scoring Scales automatically;
- generate report cards, parent reports, or longitudinal standards reports;
- manage formal safety, disciplinary, medical, disability, or counseling records;
- infer engagement, leadership, collaboration, or understanding from behavior alone;
- require audio, video, cloud services, or continuous connectivity;
- or function as a public participation leaderboard.

## 5. Relationship to Other Paper Data Suite Modules

### 5.1 `pds-core`

PDS Core owns shared infrastructure used across Paper Data Suite modules. Concord consumes that infrastructure rather than creating parallel workspace, identity, routing, source-retention, or standards systems.

The dependency direction is:

```text
pds-concord -> pds-core
```

Concord does not depend directly on ScoreForm or Quillan merely to access shared behavior. Cross-module relationships use public module-qualified identifiers and contracts.

PDS Core responsibilities relevant to Concord include:

- resolving and validating the Paper Data Suite workspace root;
- owning canonical class, roster, and student identity conventions;
- validating durable identifiers and constructing safe module-qualified paths;
- defining the PDS2 locator grammar;
- parsing and serializing PDS2 locators;
- owning Route Registration records;
- resolving a route to a module-owned record reference;
- retaining active source scans before module-specific processing;
- preserving provenance from routed derivatives to retained source scans and source pages;
- defining generic routing-failure and resolution metadata;
- dispatching a successful route to the registered module profile;
- owning the shared standards library;
- owning standards profiles and durable `standard_id` and `profile_id` references;
- validating standards and profile membership at workflow boundaries;
- and exposing shared contract-version information.

Concord owns:

- Concord Activities and Sessions;
- Activity-specific Groups, Memberships, Roles, and Responsibilities;
- Activity scoring orientation;
- selection of Core standards profiles and Focus Standards for Concord Activities;
- Template Definitions and immutable Template Versions;
- Packet Definitions, immutable Packet Versions, and Packet Components;
- generated Packet, Artifact, and Artifact Page records;
- Artifact Authors and Artifact Subjects;
- Concord-specific Scan References;
- Review, Moderation, correction, and supersession behavior;
- standard-backed and local Criteria;
- Concord Scoring Scales and Score Records;
- Score Evidence Links;
- Concord-specific standards-result handoff projections;
- and Concord’s teacher-facing workflow and interface.

#### PDS2 work identity

For Core routing and workspace identity:

```text
module_id = concord
class_id  = <Core class identifier>
work_id   = <Concord activity_id>
```

For Concord:

```text
work_id = activity_id
```

The effective module work identity is:

```text
module_id + class_id + work_id
```

Concord does not need a second Core-versus-Concord assignment identity for PDS2 routing.

The canonical Concord work root is conceptually:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
```

Concord must use Core helpers rather than construct this path from unvalidated strings.

#### PDS2 route target

A normal Concord Route Registration targets an existing Artifact Page:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

The Artifact Page must exist before its Route Registration and QR code are generated.

The normal resolution chain is:

```text
PDS2 locator
    -> Core Route Registration
    -> Concord Artifact Page
    -> Concord Artifact Instance
    -> optional Packet Instance
    -> Activity
    -> optional Session and Group context
    -> Artifact Authors
    -> Artifact Subjects
```

The QR code identifies the expected physical route. It does not encode the complete semantic graph.

### 5.2 `pds-scoreform`

ScoreForm owns machine-readable selected-response and OMR workflows.

Examples include:

- multiple-choice assessments;
- bubble-based ratings;
- structured response grids;
- machine-readable accountability checks;
- and OMR-based checklists.

ScoreForm may attach durable standards metadata to individual questions while preserving answer-key-based scoring.

Concord may reference a ScoreForm assignment or result as:

- an individual accountability check;
- a pre- or post-Activity content check;
- supporting evidence for a standard-backed Concord Score;
- contextual evidence;
- or a packet instruction.

Concord must not:

- implement a competing OMR system;
- copy ScoreForm answer keys or result ownership;
- treat question-level alignment as a Concord Score;
- convert percentage correct automatically into a Concord Scoring Scale value;
- or infer a standards judgment without explicit teacher approval.

When a ScoreForm result supports a Concord Score, the conceptual relationship is:

```text
ScoreForm result
    -> Concord External Reference
    -> Concord Evidence Reference
    -> Concord Score Evidence Link
    -> explicit Concord Score Record
```

### 5.3 `pds-quillan`

Quillan owns focused and extended written-response workflows.

Examples include:

- individual reflections;
- extended peer feedback;
- written defenses of Group decisions;
- analytical exit responses;
- explanations of learning;
- and substantial written self-assessment.

Quillan makes Focus Standards the organizing unit for its teacher review and standards-based result records.

Concord may reference a Quillan assignment, response, or standards result as:

- an individual reflection;
- supporting evidence;
- complementary written evidence;
- a follow-up explanation;
- or contextual evidence for a Concord judgment.

Concord must not:

- recreate Quillan’s review-unit workflow;
- copy Quillan-owned result records;
- assume a Quillan rating determines a Concord Score;
- or convert a Quillan result without an explicit Concord teacher judgment.

When a Quillan record supports a Concord Score, the conceptual relationship is:

```text
Quillan record
    -> Concord External Reference
    -> Concord Evidence Reference
    -> Concord Score Evidence Link
    -> explicit Concord Score Record
```

### 5.4 Future lesson-planning module

A future Paper Data Suite planning module may manage:

- objectives;
- instructional sequencing;
- standards alignment;
- materials;
- timing;
- differentiation;
- lesson plans;
- and unit plans.

Concord begins after the teacher has already planned the collaborative Activity.

A planning module may later propose:

- Activity title;
- class;
- Sessions;
- Groups;
- scoring orientation;
- standards profile;
- ordered Focus Standards;
- packet recommendation;
- Criteria;
- or linked ScoreForm and Quillan work.

Concord remains capable of operating independently.

### 5.5 Future grading and reporting module

A future Paper Data Suite grading and reporting module may combine:

- Concord standard-backed Scores;
- Concord local Scores under an explicit policy;
- ScoreForm results;
- Quillan standards results;
- teacher-entered results;
- project results;
- Scoring Scale semantics;
- grading policies;
- and reporting policies.

Concord records contextual evidence and teacher-approved judgments. It does not determine final Grades, mastery, growth, or longitudinal standards status.

A future standards-result handoff from Concord must make the following meaning available without reverse-engineering generic Criterion metadata:

- module, class, and Activity identity;
- optional Session identity;
- Score Record identity;
- target identity and target kind;
- governing `standard_id` for a standard-backed Score;
- Criterion identity;
- exact Scoring Scale revision;
- Score disposition;
- Score value when applicable;
- scorer and scoring time;
- evidence-link references;
- Moderation state;
- and supersession state.

Local Scores must remain distinguishable from direct standards results.

## 6. Design Principles

### 6.1 Paper-first

Printed Artifacts are central, not fallback exports from a digital system.

The workflow should remain useful when students have no devices and when the teacher chooses to conduct the Activity entirely on paper.

### 6.2 Human-reviewed and teacher-approved

Concord files and presents evidence for human interpretation.

The system does not decide:

- what handwriting means;
- whether a contribution was valuable;
- whether a peer judgment was fair;
- whether evidence proves a standard;
- or which Score value should be assigned.

A consequential Score is created only through an authorized teacher or scorer judgment.

### 6.3 Preserve the source Artifact

The Core-retained source scan is canonical evidence.

Metadata, notes, derived images, Reviews, Moderation Records, evidence links, and Scores are linked records. They do not replace or silently alter the retained source.

### 6.4 Clear module boundaries

Concord must not duplicate OMR, written-response evaluation, lesson planning, grading, reporting, identity, standards-library, or PDS2 infrastructure owned elsewhere.

### 6.5 Predominantly standards-based, not standards-exclusive

Standards-based scoring is Concord’s primary academic scoring model.

Activities intended to produce academic performance judgments should normally select:

- one Core standards profile;
- one or more ordered Focus Standards;
- standard-backed Criteria;
- and exact Scoring Scale revisions.

Concord also preserves local Criteria for legitimate Activity-specific, procedural, organizational, or collaborative expectations.

A local Criterion may be useful and scoreable without becoming a direct standards judgment.

### 6.6 Standards selection is not standards performance

Selecting a profile or Focus Standard establishes intended Activity scope.

It does not prove that the standard was:

- taught;
- practiced;
- assessed;
- demonstrated;
- mastered;
- or included in a final Grade.

A direct Concord standards result exists only through an explicit standard-backed Score Record.

### 6.7 One governing standard per direct standards judgment

A standard-backed Criterion has exactly one governing `standard_id`.

Therefore:

```text
one standard-backed Score
    -> one immutable Criterion
    -> one governing standard_id
```

When evidence is relevant to two standards, Concord should ordinarily use two Criteria and two Score Records.

A holistic multi-standard Criterion may exist as a local Criterion with non-governing alignment metadata, but one holistic Score must not be duplicated across several standards automatically.

### 6.8 Activity-specific evidence and Criteria

A Socratic seminar, laboratory Group, design challenge, debate, and programming team should not be forced into one universal rubric.

Teachers should be able to select or adapt:

- templates appropriate to the Activity;
- standard-backed Criteria that describe the Focus Standard in that context;
- local Criteria that capture legitimate non-standard expectations;
- and Scoring Scales appropriate to the judgment.

### 6.9 Separate evidence, Review, Moderation, Score, Grade, and report

These are distinct concepts:

- **Evidence:** a completed Artifact, teacher record, external result, Event, Attachment, or rationale that may support a judgment;
- **Review:** a human determination of filing, readability, attribution, relevance, completeness, privacy, and readiness;
- **Moderation:** a human determination of whether and how evidence may be used consequentially;
- **Score:** one teacher-approved judgment about one Criterion for one target;
- **Grade:** a broader academic calculation that may combine many judgments;
- **Report:** a presentation or communication of selected results.

Concord handles evidence, Review, Moderation, and Scoring. Grade calculation and cross-Activity or cross-module reporting belong elsewhere.

### 6.10 Provenance

Every Artifact and Score should preserve enough context to answer:

- who completed or represented it;
- whom or what it concerns;
- which Activity and Session produced it;
- which Group or component supplied context;
- which Template and Packet revisions were used;
- which standard and Criterion governed a direct standards Score;
- which Scoring Scale revision governed the value;
- who reviewed, moderated, corrected, or scored it;
- which evidence was deliberately used;
- and when those actions occurred.

### 6.11 Historical preservation

Printed, distributed, scanned, reviewed, moderated, scored, exported, or reported records must not be silently rewritten in ways that change their historical meaning.

Corrections and replacements preserve the earlier record and identify the superseding record.

### 6.12 Minimal classroom burden

Evidence collection should not interfere with the collaboration being documented.

Forms should be as short and focused as the Activity permits. A standards-based architecture does not require printing full standard text on every page or asking students to complete administrative metadata that Concord can resolve from linked records.

### 6.13 Privacy by default

Peer observations, contribution disputes, Moderation rationales, and teacher judgments may be sensitive.

Concord should avoid public rankings and should support record-specific restricted visibility.

### 6.14 Local-first

Concord should work within the Paper Data Suite local workspace model and should not require third-party cloud processing.

## 7. Core Domain Concepts

This section defines conceptual terms. It does not prescribe final Python classes, JSON schemas, filesystem records, or database tables.

### 7.1 Activity

An **Activity** is one already-planned collaborative classroom undertaking and Concord’s top-level module-owned work unit.

Examples include:

- Socratic seminar;
- science laboratory;
- collaborative coding task;
- literature circle;
- group research project;
- debate;
- engineering challenge;
- and peer-review workshop.

For PDS2 routing:

```text
work_id = activity_id
```

An Activity occurs in one or more Sessions.

An Activity declares one scoring orientation:

- `evidence_only`;
- `standards_based`;
- `mixed`;
- or `local_criteria_only`.

A standards-based or mixed Activity selects one Core standards profile and one or more ordered Focus Standards.

### 7.2 Scoring orientation

**Scoring orientation** states what kind of judgments an Activity is configured to produce.

#### `evidence_only`

The Activity collects, organizes, Reviews, or moderates evidence without creating Concord Score Records.

#### `standards_based`

The Activity’s scored judgments are direct judgments against selected Focus Standards through standard-backed Criteria.

#### `mixed`

The Activity uses both direct standard-backed Criteria and local Criteria.

#### `local_criteria_only`

The Activity produces local Score Records but no direct standards judgments.

Scoring orientation prevents later consumers from guessing whether generic Criteria represent standards performance.

### 7.3 Focus Standard

A **Focus Standard** is a durable Core-owned `standard_id` deliberately selected for a standards-based or mixed Activity.

An Activity’s ordered `focus_standard_ids`:

- define intended standards-scoring scope;
- belong to the selected Core standards profile;
- are ordered for teacher-facing workflow and later handoff;
- and do not by themselves create standards evidence or Scores.

### 7.4 Session

A **Session** is one occurrence or work period within an Activity.

A multi-day project may have several Sessions, each with different Groups, Memberships, Roles, Responsibilities, Artifacts, or evidence.

Even a single-period Activity has one explicit Session.

### 7.5 Group

A **Group** is an Activity-specific collaborative unit.

Groups are Concord-owned and are not added to the Core roster.

A Group may have a parent Group when a bounded subteam identity is needed.

### 7.6 Group Membership

A **Group Membership** associates one participant with one Group for a defined Activity context.

Membership is contextual and historical. A participant may belong to different Groups in different Sessions without rewriting earlier Membership records.

Membership does not establish:

- Artifact authorship;
- contribution;
- Role fulfillment;
- or a Score.

### 7.7 Role Assignment

A **Role Assignment** records a contextual function held by a participant.

Examples include:

- peer observer;
- discussion mapper;
- facilitator;
- recorder;
- materials manager;
- tester;
- debugger;
- or integration coordinator.

Roles are contextual functions, not personality labels or permanent classifications.

### 7.8 Responsibility Assignment

A **Responsibility Assignment** records a specific obligation assigned to a participant, Group, or child Group.

It records what was assigned. It does not prove completion, quality, contribution, or Role fulfillment.

### 7.9 Template Definition

A **Template Definition** is the stable lineage of one reusable printable design.

Examples include:

- discussion map;
- peer observation form;
- group process rubric;
- contribution record;
- teacher observation tracker;
- standards-scoring rubric;
- or Artifact cover sheet.

A Template Definition is not assigned to a specific class, Group, participant, or Activity.

### 7.10 Template Version

A **Template Version** is one immutable revision of a Template Definition.

Versioning is required because layout, prompts, page structure, QR placement, authorship expectations, subject expectations, supported Criteria, or return behavior may change.

A generated Artifact remains linked to the exact Template Version that produced it.

### 7.11 Packet Definition

A **Packet Definition** is the stable lineage of a reusable packet design.

It identifies the packet’s name, purpose, and revision family. Ordered composition belongs to Packet Version.

### 7.12 Packet Version

A **Packet Version** is one immutable ordered composition of Template Versions and optional external components.

Example:

```text
Socratic Seminar Packet — Version 3
├── Discussion map — Template Version 2
├── Peer observer sheet — Template Version 4
├── Teacher observation tracker — Template Version 3
├── Focus Standards scoring rubric — Template Version 1
└── Optional Quillan reflection reference
```

A Packet Version becomes immutable after it generates a Packet Instance.

### 7.13 Packet Component

A **Packet Component** is one ordered element of a Packet Version.

It may identify:

- an exact Concord Template Version;
- or an external component owned by another module or system.

Physical packet assembly does not transfer record ownership.

### 7.14 Packet Instance

A **Packet Instance** is one generated packet tied to a specific Activity context.

It may be associated with:

- Activity;
- Session;
- Group;
- participant;
- series or checkpoint;
- generator;
- and generation date.

### 7.15 Artifact Instance

An **Artifact Instance** is one generated copy of one Template Version.

Examples include:

- the discussion map generated for Group 3;
- one peer observation sheet assigned to a student observer;
- the teacher observation page for Period 2;
- or one project retrospective generated for a milestone.

Each Artifact Instance has stable identity and one or more Artifact Pages.

### 7.16 Artifact Page

An **Artifact Page** is one expected physical page within an Artifact Instance.

Every returned scannable page has stable identity before rendering.

When routing is required, the Artifact Page receives one immutable `route_id`, and Core stores a Route Registration targeting that Artifact Page.

### 7.17 Artifact Author

An **Artifact Author** is a durable association between an Artifact Instance and the person or collective that completed, produced, recorded, or formally represented it.

Examples include:

- individual student;
- co-authors;
- peer observer;
- Group recorder;
- collective Group;
- teacher;
- or another authorized adult.

The Author is not necessarily the Subject or Score target.

### 7.18 Artifact Subject

An **Artifact Subject** is a durable association between an Artifact Instance and the person, Group, Session, Activity, Event, component, or object that the Artifact concerns.

One Artifact may have several Subjects.

Subject does not establish authorship and does not automatically create a Score.

### 7.19 Scan Reference

A **Scan Reference** is Concord’s durable association between one Artifact Page and one page or region of a Core-retained source scan.

A Scan Reference preserves routing, readability, filing, Review, duplicate, rescan, conflict, and supersession semantics without replacing the retained source.

### 7.20 Review

A **Review** is a human examination of an Artifact Instance and its available routed evidence.

A Review may:

- confirm readability and completeness;
- confirm or correct filing;
- confirm or correct Authors and Subjects;
- confirm privacy;
- determine relevance;
- identify whether Moderation is required;
- and determine readiness for possible scoring.

Review does not determine performance and does not create a Score.

### 7.21 Moderation

A **Moderation Record** documents an authorized judgment about whether and how evidence may be used consequentially.

Moderation is especially important for:

- peer observations;
- disputed contribution claims;
- conflicting Group accounts;
- student-generated claims about other students;
- and incomplete or questionable evidence.

Moderation does not select the Criterion, Score target, standard, or Score value.

### 7.22 Criterion Set

A **Criterion Set** is one immutable revision of an ordered collection of related Criteria.

A Criterion Set is classified as:

- `standard_backed`;
- `local`;
- or `mixed`.

A standard-backed Set contains only standard-backed Criteria. A local Set contains only local Criteria. A mixed Set contains both.

### 7.23 Standard-backed Criterion

A **standard-backed Criterion** defines how one selected Focus Standard will be judged in the Concord Activity context.

It has exactly one governing `standard_id`.

Example:

```text
Focus Standard:
njsls-ela:SL.PE.9-10.1

Activity-specific Criterion:
Builds on peers’ ideas and responds substantively during collaborative discussion
```

The Criterion contextualizes the standard. It does not redefine the Core-owned standard.

### 7.24 Local Criterion

A **local Criterion** evaluates an Activity-specific, procedural, organizational, product, or collaborative expectation that is not a direct standards rating.

Examples include:

- performs the assigned observer rotation;
- returns shared materials to the agreed location;
- records a component handoff;
- maintains the Group version log;
- or follows a locally defined procedure.

A local Criterion may carry optional non-governing standards-alignment metadata.

A Score against a local Criterion is not a direct standards result.

### 7.25 Scoring Scale

A **Scoring Scale** is one immutable revision of the values permitted for Score Records.

A scale may be:

- ordinal;
- categorical;
- numeric;
- binary;
- rubric-based;
- or teacher-defined.

Concord does not assume that similarly numbered scales are semantically equivalent.

### 7.26 Score Record

A **Score Record** is one teacher-approved judgment about one Criterion for one target in one Activity context using one exact Scoring Scale revision.

A Score Record is classified as:

- `standard_backed` when its immutable Criterion has one governing standard;
- or `local` when its Criterion is local.

A standard-backed Score preserves or exposes one unambiguous governing `standard_id`.

A Score is not a course Grade, final mastery determination, or longitudinal proficiency claim.

### 7.27 Score Evidence Link

A **Score Evidence Link** records the deliberate use of one evidence source in one Score judgment.

One Score may use several evidence sources. One evidence source may support several Scores.

Evidence reuse does not make the resulting Scores equivalent.

### 7.28 Standards Result Handoff Projection

A **Standards Result Handoff Projection** is a future derived interoperability view of a canonical standard-backed Concord Score Record.

It makes standards meaning available to the future grading and reporting module without changing ownership of the Score Record.

It does not perform aggregation, weighting, scale conversion, mastery determination, or Grade calculation.

### 7.29 External Reference

An **External Reference** is a Concord-owned relationship to a record owned by another module or external system.

Examples include:

- ScoreForm result;
- Quillan response or standards result;
- external project Artifact;
- source-control record;
- cloud document;
- or future grading and reporting record.

The external owner remains authoritative.

## 8. Artifact Model

Concord Artifacts fall into three conceptual classes.

### 8.1 Structured Concord Artifacts

These are generated by Concord and contain stable page layouts, PDS2 QR codes, prompts, tables, rubrics, trackers, or graphic organizers.

Examples include:

- teacher observation sheet;
- peer observation form;
- standards-based scoring rubric;
- local process checklist;
- contribution log;
- decision map;
- concept map;
- project retrospective;
- and Artifact cover sheet.

Concord identifies and files these Artifacts but does not interpret handwritten content automatically.

### 8.2 Attached collaborative work

These are irregular or externally created Artifacts associated with a Concord Activity.

Examples include:

- poster;
- handwritten design sketch;
- annotated text;
- Group notes;
- chart paper;
- laboratory diagram;
- storyboard;
- printed source code;
- and collaborative digital document export.

They may be associated through:

- an Artifact cover sheet;
- QR label;
- Attachment record;
- External Reference;
- or companion identification page.

### 8.3 Instructional scaffolds

These are printable materials that support the Activity but may not need to return.

Examples include:

- Role cards;
- discussion stems;
- collaboration norms;
- protocol instructions;
- Group procedure cards;
- and peer-feedback guidance.

A Template Version declares whether each page is expected to return and whether it requires a PDS2 route.

## 9. Artifact Taxonomy

The initial taxonomy should support different subject areas without becoming a universal rubric or fixed curricular ontology.

### 9.1 `discussion_tracker`

Documents how ideas move through a discussion.

Examples:

- discussion web;
- question-response map;
- evidence-use tracker;
- idea-connection chart;
- and seminar observation map.

### 9.2 `teacher_observation`

Provides a paper interface for teacher observation.

Examples:

- roster grid;
- Group rotation sheet;
- anecdotal note form;
- Focus Standard tracker;
- targeted Criterion tracker;
- and conference record.

### 9.3 `peer_observation`

Allows a student to record evidence about another student or Group.

Examples:

- seminar observer sheet;
- teamwork observation form;
- Criterion-specific peer record;
- and peer conference notes.

Peer evidence may require Moderation before consequential use.

### 9.4 `group_process_rubric`

Supports evaluation of how the Group worked.

A Group-process rubric may contain:

- standard-backed Criteria when a selected Focus Standard governs the judgment;
- local Criteria for Activity-specific procedures;
- or both in a mixed Activity.

Examples:

- collaboration rubric;
- Group functioning rubric;
- project-team process rubric;
- and laboratory teamwork rubric.

### 9.5 `contribution_record`

Documents responsibilities, tasks, decisions, or contributions.

Examples:

- contribution chart;
- responsibility record;
- task-completion record;
- Artifact authorship sheet;
- and Role-fulfillment record.

A contribution record is evidence, not automatically a Score.

### 9.6 `group_graphic_organizer`

Structures shared thinking or problem solving.

Examples:

- K-W-L chart;
- concept map;
- cause-and-effect diagram;
- claim-evidence-reasoning chart;
- compare-and-contrast matrix;
- decision matrix;
- problem-solution organizer;
- and sequence chart.

### 9.7 `collaborative_work_log`

Provides a lightweight chronological record.

Examples:

- Session log;
- decision log;
- troubleshooting record;
- design-iteration log;
- milestone record;
- project checkpoint sheet;
- and component-handoff log.

### 9.8 `group_retrospective`

Helps the Group examine its process after or during the Activity.

Examples:

- plus/delta;
- start/stop/continue;
- team retrospective;
- process reflection grid;
- and next-Session improvement plan.

This category remains concise and structured. Extended individual writing belongs to Quillan.

### 9.9 `artifact_cover_sheet`

Associates irregular or externally created work with Concord metadata.

Examples:

- poster cover sheet;
- attached-work routing page;
- project Artifact identification page;
- and multi-page submission cover.

### 9.10 `moderation_record`

Documents teacher review of evidence use.

Examples:

- peer-evidence review form;
- conflicting-evidence resolution;
- attribution correction;
- accepted-with-qualification decision;
- and rejected-evidence record.

### 9.11 `scoring_rubric`

Supports criterion-level teacher scoring.

Examples:

- Focus Standards seminar rubric;
- standards-based laboratory-practice rubric;
- engineering-design Criterion rubric;
- mixed standards-and-local project rubric;
- local procedural checklist;
- and Group outcome rubric.

A rubric must make standard-backed and local Criteria distinguishable.

### 9.12 `correction_or_exception`

Handles unusual, damaged, corrected, or unresolved records.

Examples:

- missing-page form;
- incorrect Group assignment;
- absence note;
- disputed attribution;
- rescan request;
- unmatched Scan Reference;
- and Score revision record.

## 10. Packet Model

Concord treats packets as composable collections of versioned components rather than as lessons.

A packet may contain:

- student-facing Artifacts;
- Group-facing Artifacts;
- peer-observer Artifacts;
- teacher-facing Artifacts;
- standards-based scoring Artifacts;
- local process Artifacts;
- cover sheets;
- instructional scaffolds;
- and optional links to ScoreForm or Quillan work.

### 10.1 Example: Socratic seminar packet

```text
Socratic Seminar Packet
├── Group discussion map
├── Peer observation sheet
├── Teacher Focus Standards observation tracker
├── Standards-based seminar scoring rubric
├── Optional local observer-rotation checklist
└── Optional Quillan reflection reference
```

Possible direct standards judgments might include:

- builds on peers’ ideas;
- uses relevant textual evidence;
- and integrates information from the discussion.

The observer-rotation checklist may remain a local Criterion if it is not a direct standards judgment.

### 10.2 Example: Science laboratory packet

```text
Science Laboratory Packet
├── Shared prediction organizer
├── Group procedure organizer
├── Contribution record
├── Decision and troubleshooting log
├── Teacher standards observation sheet
├── Mixed standards-and-local rubric
└── Optional ScoreForm accountability check reference
```

The mixed rubric might include:

- a standard-backed Criterion for evaluating evidence or engineering constraints;
- and a local Criterion for completing a required equipment check.

### 10.3 Example: Programming or engineering project packet

```text
Collaborative Project Packet
├── Task and responsibility record
├── Design decision matrix
├── Work-Session log
├── Contribution record
├── Group retrospective
├── Focus Standards scoring rubric
├── Optional local handoff-protocol checklist
└── Artifact cover sheet
```

Source code, CAD files, and repository history remain externally owned evidence.

## 11. Artifact Lifecycle

The conceptual lifecycle is:

```text
Select Packet Version or Template Versions
        ↓
Configure Activity and scoring orientation
        ↓
Select standards profile and Focus Standards when required
        ↓
Select standard-backed and/or local Criteria
        ↓
Generate Packet and Artifact Instances
        ↓
Create Artifact Pages and PDS2 Route Registrations
        ↓
Print and distribute
        ↓
Complete Artifacts on paper
        ↓
Collect and scan
        ↓
Core retains source scans
        ↓
Resolve and file Artifact Pages
        ↓
Review scans and metadata
        ↓
Moderate evidence where required
        ↓
Record teacher-approved Scores when configured
        ↓
Project standards results or expose local Scores appropriately
        ↓
Retain or archive according to policy
```

Not every Activity or Artifact passes through every step.

Examples:

- an evidence-only Activity stops before scoring;
- a non-returned scaffold stops after distribution;
- a missing Artifact never reaches Scan Review;
- a peer observation may require Moderation;
- a teacher tracker may move directly from Review to scoring use;
- and a local-criteria-only Activity produces no direct standards-result projection.

### 11.1 Select

The teacher chooses one immutable Packet Version or one or more Template Versions.

### 11.2 Configure

The teacher supplies only the context necessary to generate and interpret Artifacts, such as:

- class;
- Activity;
- Sessions;
- Groups;
- participants;
- scoring orientation;
- standards profile and ordered Focus Standards when required;
- Criterion Sets;
- Scoring Scales;
- privacy policy;
- and linked ScoreForm or Quillan work.

This is Activity configuration, not lesson planning.

### 11.3 Generate

Concord creates:

- Packet Instance records;
- Artifact Instance records;
- Artifact Page records;
- printable PDFs;
- PDS2 Route Registrations for route-required pages;
- page-level QR codes;
- human-readable fallback identifiers;
- packet manifests;
- and page numbering.

### 11.4 Complete

Students and teachers write, draw, annotate, or mark the printed Artifacts.

### 11.5 Scan

Completed pages are scanned individually or in batches.

Core retains the selected source before Concord-specific filing.

### 11.6 Resolve and file

Core resolves the PDS2 locator to an Artifact Page registration and dispatches the route to Concord.

Concord creates a Scan Reference linking the routed source page to that Artifact Page.

This stage identifies the page. It does not interpret handwritten content.

### 11.7 Review

The teacher confirms or records:

- correct filing;
- scan quality;
- page completeness;
- Author and Subject attribution;
- relevance;
- privacy classification;
- Moderation requirement;
- and readiness for possible scoring.

### 11.8 Moderate

The teacher determines whether and how evidence may be used when reliability, fairness, attribution, or consequential use requires a separate judgment.

### 11.9 Score

The authorized scorer records one criterion-level judgment for one target using one exact Scoring Scale revision.

For a standard-backed Score, the governing standard is unambiguous through the immutable standard-backed Criterion and the Score contract.

For a local Score, the record remains explicitly local and is not projected as a direct standards result.

### 11.10 Handoff or link

Concord makes approved records available to other modules through explicit contracts:

- standard-backed Scores through a future Standards Result Handoff Projection;
- local Scores as local Criterion judgments;
- and evidence through module-qualified references.

## 12. PDS2 QR and Identification Design

Every returnable scannable page should normally contain its own PDS2 QR code.

Packet-level identification alone is insufficient because pages may be:

- separated;
- reordered;
- rescanned;
- submitted independently;
- attached to other work;
- or mixed with pages from other Groups.

### 12.1 PDS2 locator grammar

The PDS2 grammar is:

```text
PDS2|m=<module_id>|c=<class_id>|w=<work_id>|r=<route_id>
```

A Concord page uses:

```text
PDS2|m=concord|c=<class_id>|w=<activity_id>|r=<route_id>
```

### 12.2 QR purpose

The QR code identifies one expected physical page route.

It does not encode:

- student responses;
- Artifact Authors;
- Artifact Subjects;
- Group Membership;
- Score target;
- Criterion;
- standard;
- Scoring Scale;
- Score value;
- privacy graph;
- or the complete semantic context of the page.

Those meanings resolve through the registered Artifact Page and linked Concord records.

### 12.3 Route Registration

A route-required Artifact Page has one immutable `route_id`.

Core stores a Route Registration targeting:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

The Artifact Page must exist before registration and rendering.

### 12.4 Human-readable fallback

Each route-required page should contain a visible fallback label for manual resolution when:

- the QR code is damaged;
- the scan is incomplete;
- the code cannot be read;
- or the page must be handled without automated routing.

The fallback identifier must not expose unnecessary PII.

### 12.5 Page design

Templates should reserve stable areas for:

- QR code;
- fallback identifier;
- title;
- human-readable Activity or Session context where useful;
- student or Group display labels where pedagogically necessary;
- page number;
- and Template Version.

Printed display labels are not durable identities.

## 13. Scan and Filing Model

PDS Core owns shared source-scan retention, source-page provenance, route resolution, failure metadata, and generic dispatch.

Concord’s scan responsibility is the module-specific association between a routed source page and an expected Artifact Page.

### 13.1 Canonical source

The Core-retained source scan is canonical.

Concord-created derivatives may support Review, but they never replace the retained source.

### 13.2 Scan Reference

After successful dispatch, Concord creates a Scan Reference that may record:

- Artifact Page identity;
- Core source-scan identity;
- source-page position;
- optional routed derivative;
- routing status;
- readability status;
- filing status;
- Review status;
- preferred-for-use state;
- provenance;
- and supersession.

### 13.3 Independent states

Concord should not collapse all scan facts into one status.

A Scan Reference may separately represent:

- routing state;
- readability;
- filing correctness;
- Review state;
- preferred-for-use state;
- duplicate state;
- and supersession state.

### 13.4 Rescans and duplicates

A rescan creates a new retained source and a new Scan Reference.

A duplicate is preserved and may later be reclassified.

Neither silently erases an earlier source or association.

## 14. Review and Moderation Model

### 14.1 Review is not transcription

A teacher may enter a note or select a Review judgment, but Concord should not require the teacher to recreate all handwritten content digitally.

### 14.2 Review is not scoring

A Review may establish that evidence is readable, correctly filed, relevant, and ready for possible use.

It does not determine performance and does not create a Score.

### 14.3 Moderation status

Student-generated evidence may be moderated as:

- accepted;
- accepted with qualification;
- insufficient;
- disputed;
- rejected;
- or not used for scoring.

An accepted Moderation decision means that evidence may be used under the recorded conditions. It is not a high Score.

A rejected decision is not negative evidence against the Subject.

### 14.4 Missing and exceptional evidence

The system must distinguish:

- not observed;
- not applicable;
- absent;
- excused;
- deferred;
- incomplete Artifact;
- unreadable Artifact;
- misrouted evidence;
- unavailable external evidence;
- and insufficient evidence.

These conditions must not be converted automatically into zero, the lowest Scoring Scale value, or a mastery failure.

## 15. Scoring Model

### 15.1 Primary model

Concord’s primary academic scoring model is standards-based.

The normal academic relationship is:

```text
reviewed and permitted evidence
    -> standard-backed Criterion
    -> teacher-approved standard-backed Score
```

Concord remains standards-aware without being standards-exclusive.

Some Activities are evidence-only. Some use local Criteria only. Mixed Activities use both standard-backed and local Criteria.

### 15.2 Activity scoring orientations

Each Activity declares one scoring orientation.

#### `evidence_only`

The Activity produces no Concord Score Records.

It may still produce reviewed, moderated, and exportable evidence.

#### `standards_based`

The Activity produces direct standards judgments through standard-backed Criteria.

It requires:

- one valid `standards_profile_id`;
- one or more ordered `focus_standard_ids`;
- standard-backed Criteria;
- and exact Scoring Scale revisions.

#### `mixed`

The Activity produces both:

- direct standard-backed Scores;
- and local Criterion Scores.

It also requires one standards profile and one or more ordered Focus Standards.

#### `local_criteria_only`

The Activity produces local Scores but no direct standards judgments.

Local Scores may later affect a Grade only through an explicit downstream policy.

### 15.3 Focus Standards

Focus Standards define the Activity’s intended standards-scoring scope.

Rules include:

- standards identity remains Core-owned;
- `standards_profile_id` is one durable Core profile reference;
- `focus_standard_ids` is ordered and nonempty for standards-based and mixed Activities;
- duplicate Focus Standards are invalid;
- each Focus Standard should belong to the selected profile;
- and selection alone does not create a Score or mastery claim.

### 15.4 Criterion kinds

Every scored Criterion is classified as standard-backed or local.

#### Standard-backed Criterion

A standard-backed Criterion:

- has exactly one governing `standard_id`;
- uses a standard selected as an Activity Focus Standard;
- defines what that standard looks like in the Activity context;
- and may support one or more valid target kinds.

Example:

```text
Standard:
njsls-ela:SL.PE.9-10.1

Criterion:
Builds on peers’ ideas and responds substantively during collaborative discussion
```

#### Local Criterion

A local Criterion:

- has no governing `standard_id`;
- evaluates an Activity-specific or procedural expectation;
- may carry optional non-governing alignment metadata;
- and does not produce a direct standards result.

Example:

```text
Local Criterion:
Completes the assigned observer rotation and submits the observation form
```

#### Multi-standard holistic Criteria

One Score against a holistic Criterion must not be treated as several direct standards ratings.

When a behavior provides direct evidence for two standards, Concord should ordinarily use two standard-backed Criteria and two Score Records.

A holistic multi-standard Criterion may remain local with alignment metadata, or a later explicit composite contract may define another interpretation.

### 15.5 Score ownership and meaning

A Score is recorded by an authorized scorer, normally the teacher.

Student-generated peer ratings may be stored as evidence, but they do not become final Concord Scores without teacher approval.

One Score Record evaluates:

- exactly one Criterion;
- for exactly one target;
- in one Activity context;
- using one exact Scoring Scale revision.

A standard-backed Score is one contextual judgment about one governing standard.

A local Score is one contextual judgment about one local Criterion.

### 15.6 Score dispositions

A Score Record distinguishes:

- `scored`;
- `insufficient_evidence`;
- `absent`;
- `excused`;
- `not_observed`;
- `not_applicable`;
- and `deferred`.

When the disposition is `scored`, a valid value from the selected Scoring Scale is required.

When the disposition is not `scored`, a value is absent. Zero or the lowest level must not be inferred.

### 15.7 Score targets

A Score target may be:

- one Core student;
- one Concord Group;
- one Session;
- one Activity;
- one Artifact Instance;
- one Work Item;
- or another approved Activity component.

A target must be valid for the Criterion.

A Group Score does not become an individual Score for each member.

### 15.8 Evidence and Scores

One Score may use:

- several Concord Artifacts;
- one teacher tracker;
- peer evidence permitted through Moderation;
- an Attachment;
- an Activity Event;
- a Contribution Claim;
- a ScoreForm result;
- a Quillan response or result;
- another external record;
- professional judgment with rationale;
- or a mixed basis.

One evidence source may support several Scores through separate Score Evidence Links.

Group or multi-subject evidence may support an individual Score only when:

- the evidence is relevant to the individual target;
- required Moderation permits that use;
- the teacher makes an explicit individual judgment;
- and the evidence link or rationale explains the relevance.

Group evidence must never generate individual Scores automatically.

### 15.9 Scoring Scales

Concord does not impose one universal Scoring Scale.

Possible scales include:

- Developing / Approaching / Meeting / Exceeding;
- Beginning / Progressing / Proficient / Advanced;
- numeric ordinal levels;
- binary demonstrated/not-demonstrated where appropriate;
- categorical judgments;
- and teacher-defined labels.

A Scoring Scale revision preserves:

- permitted machine values;
- display labels;
- descriptions;
- ordering where applicable;
- semantic meaning;
- and historical revision identity.

Concord does not assume that one scale’s `3` means the same as another scale’s `3`.

### 15.10 Examples

#### Standards-based seminar

```text
Focus Standard: SL.PE.9-10.1
Criterion: Builds on peers’ ideas during discussion
Score: Meeting
Target: Student
Evidence: Teacher tracker + moderated peer observation
```

```text
Focus Standard: RL.CR.9-10.1
Criterion: Uses relevant textual evidence to support claims
Score: Approaching
Target: Student
Evidence: Discussion map + teacher observation
```

These are direct standards-based Concord judgments.

#### Mixed laboratory Activity

```text
Focus Standard: HS-ETS1-3
Standard-backed Criterion: Evaluates proposed solutions against constraints
Score: Proficient
Target: Group
```

```text
Local Criterion: Completes required equipment check
Score: Complete
Target: Group
```

The first Score is a direct standards result. The second is a local procedural judgment.

#### Local-only Activity

```text
Local Criterion: Maintains the Group handoff log
Score: Complete
Target: Group
```

This is a valid Concord Score but not a direct standards rating.

### 15.11 Standards-result handoff

A future grading and reporting module must be able to identify a standard-backed Concord result without guessing from display text or plural alignment metadata.

A standards-result handoff should expose:

```text
module_id
class_id
activity_id
optional session_id
score_record_id
target reference
standard_id
criterion_id
scoring_scale_id
score disposition
score value when applicable
scorer
scored_at
evidence-link references
moderation state
supersession state
```

The exact file, event, API, or storage contract remains later work.

### 15.12 Score is not Grade or mastery

A standard-backed Concord Score is one contextual teacher judgment.

It does not automatically establish:

- final mastery;
- permanent proficiency;
- marking-period performance;
- course-level attainment;
- growth;
- or a Grade.

The future grading and reporting module will define how contextual judgments are compared, weighted, combined, normalized, superseded, summarized, and reported.

## 16. Privacy and Access

### 16.1 Sensitive record types

The following may require restricted visibility:

- peer observations;
- contribution disputes;
- teacher Review notes;
- Moderation rationales;
- individual Score Records;
- evidence links;
- correction records;
- and exception records.

### 16.2 Record-specific privacy

Privacy is record-specific.

A Score may be less restrictive than some supporting evidence when that difference is deliberate.

For example:

- a teacher-restricted peer observation may support a student-visible standards Score;
- the student may receive the Score without receiving the observer’s identity;
- a Group Artifact may remain Group-and-teacher visible while individual Scores remain teacher-and-subject visible;
- and a Moderation rationale may remain more restricted than the resulting Score.

Access to a Score does not imply access to every supporting source.

### 16.3 Default visibility

Peer- and teacher-generated evidence should be private by default unless the teacher deliberately chooses another policy.

### 16.4 Public repository data

All examples, fixtures, screenshots, tests, and sample packets in the public repository must use synthetic students, classes, Activities, standards selections, and Scores.

### 16.5 Data minimization

QR payloads and records should contain only the identifiers and context required by their contracts.

Sensitive medical, disability, disciplinary, or counseling details must not be copied into Concord merely to explain a restriction or disposition.

## 17. Integration Model

Concord depends on PDS Core for suite-level infrastructure and references sibling-module records through public identifiers rather than package dependencies.

```text
pds-concord -> pds-core
pds-concord -/-> pds-scoreform
pds-concord -/-> pds-quillan
```

### 17.1 Shared Core concepts

Shared PDS Core concepts include:

- class identity;
- student identity;
- roster;
- identifier validation;
- module-qualified work identity;
- workspace paths;
- PDS2 locator;
- Route Registration;
- source-scan identity and provenance;
- generic route-resolution and failure metadata;
- standards library;
- standards profile;
- durable standard identity;
- and shared contract versions.

### 17.2 ScoreForm integration

Concord may reference a ScoreForm assignment or result as:

- an individual accountability check;
- a pre- or post-Activity content check;
- supporting evidence for one or several explicitly judged Concord Scores;
- or another OMR component.

The actual form generation, scanning, OMR extraction, correctness determination, and ScoreForm result remain ScoreForm responsibilities.

### 17.3 Quillan integration

Concord may reference a Quillan assignment, response, or standards result as:

- an individual reflection;
- written explanation;
- extended peer feedback;
- defense of a Group decision;
- analytical follow-up;
- or supporting evidence for an explicit Concord judgment.

The written-response workflow and Quillan result remain Quillan responsibilities.

### 17.4 Future planning integration

A future planning module may supply Activity configuration recommendations, including standards and packet selections.

Concord remains authoritative for the Concord Activity record and should still function independently.

### 17.5 Future grading and reporting integration

A future grading and reporting module may consume:

- standard-backed Concord Score projections;
- local Concord Scores under an explicit policy;
- ScoreForm and Quillan results;
- Activity metadata;
- Group and individual distinctions;
- exact scale semantics;
- evidence references;
- and supersession state.

The downstream module must not treat standards selection, local alignment, or evidence presence as a direct standards Score.

## 18. Representative Use Cases

### 18.1 Standards-based Socratic seminar

The teacher configures a `standards_based` seminar Activity.

The Activity selects:

- one Core ELA standards profile;
- ordered Focus Standards for collaborative discussion and textual evidence;
- standard-backed Criteria for those Focus Standards;
- and one teacher-approved Scoring Scale revision.

Students complete:

- a discussion map;
- and peer observation forms.

The teacher completes:

- a roaming Focus Standards observation tracker;
- and a standards-based scoring rubric.

The pages are scanned, retained by Core, resolved through PDS2, and filed by Artifact Page.

The teacher Reviews the Artifacts, moderates peer evidence, and creates separate standard-backed Scores for each directly evaluated Focus Standard.

An optional Quillan reflection may support one or more Scores through explicit evidence links, but it does not determine them automatically.

### 18.2 Mixed science laboratory

The teacher configures a `mixed` laboratory Activity.

The packet contains:

- prediction organizer;
- procedure organizer;
- decision and troubleshooting log;
- contribution record;
- teacher observation sheet;
- and mixed scoring rubric.

The Activity selects a science or engineering Focus Standard and defines a standard-backed Criterion for evaluating evidence or constraints.

It also defines a local equipment-check Criterion.

The teacher may create:

- a Group standard-backed Score for the selected practice standard;
- and a local Group Score for the equipment check.

An individual ScoreForm concept check may be linked as supporting evidence, but Concord does not convert it automatically into the Group or individual Concord Score.

### 18.3 Standards-based collaborative programming task

The teacher configures a `standards_based` or `mixed` project Activity.

The teacher generates:

- responsibility record;
- design decision matrix;
- debugging log;
- contribution record;
- Group retrospective;
- Focus Standards scoring rubric;
- and Artifact cover sheet.

Source code and repository history remain external evidence.

A standard-backed Criterion may evaluate documentation, testing, iterative improvement, or collaborative program development under one governing standard.

A local Criterion may evaluate a school-specific handoff protocol.

The teacher may use Group evidence to support an individual Score only through an explicit individual judgment and relevance explanation.

### 18.4 Evidence-only peer-review workshop

The teacher configures an `evidence_only` Activity.

Concord generates peer-feedback forms and a teacher Review tracker.

The completed forms are scanned, filed, and available as evidence for a later Quillan revision workflow.

Concord creates no Scores for the Activity.

### 18.5 Attached poster or chart paper

A Group creates work on a large sheet that is not a normal Concord Template.

A Concord Artifact cover sheet is generated and routed through PDS2. The poster is represented through an Attachment or External Reference.

The teacher may use the attached work as evidence for several separate standard-backed Scores and one local process Score.

The shared source does not force those Scores to have the same target, standard, Criterion, or value.

## 19. Initial Product Decisions

The following decisions are accepted for the conceptual design phase:

1. Concord is a paper-based collaborative-evidence and standards-scoring system.
2. Concord begins after Activity planning.
3. Concord generates Templates and Packets, not lesson plans.
4. Concord depends on PDS Core for shared workspace, identity, identifier, PDS2, route-registration, source-retention, dispatch, standards, and contract infrastructure.
5. Concord must not create a separate QR grammar or duplicate PDS Core contracts.
6. The effective PDS2 work identity is `module_id + class_id + activity_id`.
7. For Concord, `work_id = activity_id`.
8. A normal PDS2 Route Registration targets an existing Concord Artifact Page.
9. PDS2 identifies a physical route, not complete Artifact semantics.
10. Activity-specific Groups, Sessions, Memberships, Roles, Responsibilities, Artifacts, Criteria, Reviews, Moderation Records, and Scores remain Concord-owned.
11. Core owns standards libraries, profiles, and durable standards identity.
12. Concord’s primary academic scoring model is standards-based.
13. Concord is not standards-exclusive.
14. Every Activity declares one scoring orientation.
15. Standards-based and mixed Activities select one standards profile and ordered Focus Standards.
16. Standards selection or alignment does not create a standards Score.
17. A standard-backed Criterion has exactly one governing standard.
18. A local Criterion has no governing standard and may carry only non-governing alignment metadata.
19. One direct standards Score evaluates one standard-backed Criterion for one target.
20. A holistic multi-standard Score must not be duplicated across several standards automatically.
21. Local Scores remain distinguishable from direct standards results.
22. Group evidence may support an individual Score only through explicit teacher judgment.
23. A Group Score does not create individual Scores for Group members.
24. Missing or exceptional evidence states do not become zero or the lowest scale value automatically.
25. Concord records contextual Scores but does not determine Grades, mastery, growth, or longitudinal proficiency.
26. A future standards-result handoff must expose governing standards semantics without heuristic interpretation.
27. Template Definitions and immutable Template Versions are separate.
28. Packet Definitions and immutable Packet Versions are separate.
29. Artifact Authors and Artifact Subjects are separate association records.
30. Concord does not perform handwriting recognition, audio transcription, or automated behavior inference.
31. ScoreForm owns OMR workflows and Quillan owns focused written-response workflows.
32. External results may support Concord Scores but do not determine them automatically.
33. Concord preserves Core-retained scans as canonical evidence.
34. Review, Moderation, Scoring, Grading, and Reporting remain separate.
35. Student-generated evidence requires provenance and may require teacher Moderation.
36. Peer evidence is private by default.
37. Public repository examples use synthetic data.
38. Concord integrates through public references rather than duplicating sibling-module capabilities.
39. The minimum viable workflow remains useful without cloud services or student devices.
40. Corrections, rescans, revised attributions, Moderation decisions, and Scores preserve history.

## 20. Open Questions for Contract and Implementation Design

The foundational semantics are now substantially settled. The following questions remain for representative examples, implementation contracts, or later grading and reporting work:

1. What exact serialized schemas and schema-version fields should implement the accepted conceptual records?
2. Which identifier-generation helpers should Concord consume directly from Core?
3. What exact module-qualified filesystem paths should store each Concord record family beneath the Activity work root?
4. What human-readable fallback format should appear on route-required pages?
5. What packet-rendering manifest should connect Packet Version, Artifact Instance, Artifact Page, and Route Registration creation atomically?
6. Which Activity-scoring orientation should the user interface recommend by default without preventing deliberate alternatives?
7. How should reusable standard-backed Criterion Sets declare compatibility with different standards profiles or standard editions?
8. Should Score Records store a direct `standard_id` snapshot in addition to resolving it through the immutable Criterion?
9. What validation behavior should apply when a historical profile or standard becomes inactive, deprecated, or temporarily unavailable?
10. Which Scoring Scale revisions should ship as starter data?
11. How should the interface present two standard-backed Criteria based on the same evidence without encouraging duplicate or automatic Scores?
12. What exact workflow should record professional judgment when no formal evidence link exists?
13. What evidence-locator conventions are practical for multi-subject teacher trackers?
14. What exact privacy vocabulary should remain Concord-owned and what should later move to Core?
15. What exact exported file, event, or API contract will carry the Standards Result Handoff Projection?
16. How will the future grading and reporting module compare or combine results that use different Scoring Scale revisions?
17. Which local Scores, if any, may contribute to Grades under later explicit policy?
18. What is the smallest practical interface for reviewing scans, selecting evidence, and entering separate standards judgments efficiently?
19. Which starter Criterion Sets, Template Versions, and Packet Versions should ship without turning examples into universal domain requirements?
20. Which specialized Activity Event contracts, if any, are justified by representative records?

## 21. Recommended Next Step

Use this revised conceptual design, ADR 0014, the revised initial domain model, and the revised conceptual data contracts to create the representative contract examples required by issue `#12`.

The examples should include at least:

1. a standards-based Socratic seminar;
2. a mixed science laboratory Activity;
3. a standards-based or mixed collaborative programming or engineering project;
4. an evidence-only Activity or component;
5. a local-criteria-only judgment;
6. an individual standards Score;
7. a Group standards Score;
8. Group or multi-subject evidence supporting an individual Score through explicit teacher judgment;
9. one source supporting several separate standard-backed Scores;
10. a non-score disposition for a Focus Standard;
11. a ScoreForm result used as supporting evidence;
12. a Quillan result used as supporting evidence;
13. a local Criterion with optional alignment metadata that remains non-governing;
14. and PDS2 routing from Artifact Page registration through Scan Reference creation.

Those examples should test whether the architecture permits a future grading and reporting module to distinguish:

- standards selection from standards judgment;
- standard-backed Scores from local Scores;
- individual targets from Group targets;
- evidence from Scores;
- current Scores from superseded Scores;
- non-score dispositions from low performance;
- and Concord-owned judgments from external evidence.
