# pds-concord Conceptual Design

**Status:** Draft for review  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Date:** July 11, 2026  
**Revision:** 2 — aligned with current `pds-core` contracts

## 1. Purpose

`pds-concord` is a Paper Data Suite module for creating, organizing, printing, scanning, filing, reviewing, and scoring paper artifacts used during collaborative classroom activities.

The module exists because collaborative learning produces evidence that is often difficult to preserve. A teacher cannot observe every group continuously, and important evidence may be distributed across discussion notes, group organizers, peer observations, contribution records, rubrics, and teacher annotations.

Concord provides a paper-first workflow for turning those temporary classroom records into organized, reviewable evidence.

Concord is not a lesson-planning system. It begins after the teacher has already decided what activity students will complete and what evidence would be useful.

## 2. Core Definition

> Concord is a paper-based collaborative-evidence system.

It helps teachers create and manage scannable paper templates that document what happened during group activities, discussions, seminars, projects, laboratories, and other collaborative work.

The scanned artifact remains the primary evidence. Concord may attach metadata and scores to that artifact, but it does not attempt to interpret handwriting, transcribe discussion, or infer student behavior automatically.

## 3. Scope

Concord is responsible for:

- generating printable collaborative-learning templates;
- combining related templates into activity packets;
- assigning artifact instances to activities, sessions, groups, or students;
- adding page-level QR codes and human-readable identifiers;
- receiving scanned pages or PDFs;
- identifying and filing scanned artifacts;
- preserving the original scan as the source record;
- supporting teacher review of scanned evidence;
- recording criterion-level or component-level scores;
- distinguishing individual, group, and activity-level evidence;
- recording who completed, observed, reviewed, or scored an artifact;
- linking Concord artifacts to related Paper Data Suite records;
- exporting scores or evidence references for use by other modules; and
- supporting paper-first and offline classroom workflows.

## 4. Non-Goals

Concord does not:

- perform optical mark recognition;
- replace `pds-scoreform`;
- recognize or interpret handwriting;
- evaluate extended written responses;
- replace `pds-quillan`;
- reimplement PDS Core workspace, roster, identifier, QR-contract, source-retention, routing-metadata, or standards infrastructure;
- transcribe audio or video;
- create automated or AI-generated records of classroom discussion;
- perform automated scoring of collaborative behavior;
- plan lessons or design units;
- calculate marking-period or course grades;
- generate report cards or parent reports;
- infer engagement, leadership, collaboration, or understanding from behavior;
- require audio, video, cloud services, or continuous connectivity; or
- function as a public participation leaderboard.

## 5. Relationship to Other Paper Data Suite Modules

### 5.1 `pds-core`

PDS Core owns, or is designated to own, shared infrastructure used across Paper Data Suite modules. Concord should consume that infrastructure rather than create parallel workspace, identity, QR, routing, scan-retention, or standards systems.

The intended dependency direction is:

```text
pds-concord -> pds-core
```

Concord should not depend directly on ScoreForm or Quillan merely to access shared behavior. Cross-module relationships should use shared Paper Data Suite identifiers and contracts wherever possible.

PDS Core responsibilities relevant to Concord include:

- resolving and validating the Paper Data Suite workspace root;
- maintaining shared baseline workspace paths;
- validating durable identifiers and constructing safe paths;
- owning canonical class, assignment, roster, and student identity conventions;
- providing canonical student display helpers while preserving `student_id` as the durable identity;
- defining shared `PDS1` QR construction, parsing, validation, and routing contracts;
- retaining active source scans before module-specific processing;
- preserving provenance from routed evidence back to retained source scans;
- defining shared scan-routing failure and resolution metadata;
- owning the shared standards library, standards profiles, and durable `standard_id` and `profile_id` references;
- providing shared teacher-facing menu navigation behavior; and
- opening existing local files or folders through the operating system without giving modules separate platform-specific implementations.

Concord should use PDS Core for these concerns. Concord should continue to own:

- Concord packet, template, and artifact schemas;
- collaborative artifact PDF layouts;
- activity-specific groups and group membership;
- sessions, participant roles, artifact authors, and artifact subjects;
- Concord-specific criteria and rubrics;
- Concord-specific artifact review and moderation behavior;
- score-entry and scoring workflows;
- module-specific routed evidence and result formats; and
- Concord's teacher-facing workflow and interface.

PDS Core's active-scan contract separates shared retention from module-specific processing. Concord should use Core to retain source scans and preserve provenance before processing them. Concord remains responsible for QR extraction, PDF or image splitting, Concord-specific routing, teacher review, scoring, and routed evidence assembly.

PDS Core also establishes two important constraints for Concord's future contract work:

1. The current shared `PDS1` QR contract recognizes ScoreForm and Quillan but does not yet register Concord.
2. The current `PDS1` contract requires a `student_id`, while Concord must support group-level, teacher-level, session-level, and activity-level artifacts that may have no single student subject.

Concord must not work around those constraints by inventing a separate QR grammar, placing group identifiers in `student_id`, or creating synthetic students. Before implementation, the shared Core QR contract should be extended deliberately to register `module=concord` and represent non-student artifact subjects.

Similarly, PDS Core owns canonical class and assignment routes, while Concord will need module-specific storage for group and activity artifacts. The contract phase must determine which new route helpers belong in Core and which Concord-specific subdirectories may safely live inside the canonical assignment structure.

Relevant Core contracts include:

- [`README.md`](https://github.com/Paper-Data-Suite/pds-core/blob/main/README.md)
- [`docs/qr_payload_and_routing_contract.md`](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/qr_payload_and_routing_contract.md)
- [`docs/roster_workspace_contract.md`](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/roster_workspace_contract.md)
- [`docs/active_scan_contract.md`](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/active_scan_contract.md)
- [`docs/module_standards_integration.md`](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/module_standards_integration.md)

### 5.2 `pds-scoreform`

ScoreForm owns machine-readable OMR workflows.

Examples include:

- multiple-choice assessments;
- bubble-based ratings;
- structured response grids;
- machine-readable accountability checks; and
- OMR-based checklists.

Concord may link to a ScoreForm assignment or include a packet instruction directing students to complete one. Concord must not implement a competing OMR system.

### 5.3 `pds-quillan`

Quillan owns focused written-response workflows.

Examples include:

- individual reflections;
- extended peer feedback;
- written defenses of group decisions;
- analytical exit responses;
- explanations of learning; and
- substantial written self-assessment.

Concord may link a collaborative activity to a Quillan response. Concord may also generate short labels, prompts, captions, or structured note areas, but it should not become a written-response evaluation system.

### 5.4 Future lesson-planning module

A future Paper Data Suite module may manage:

- objectives;
- instructional sequencing;
- standards alignment;
- materials;
- timing;
- differentiation;
- lesson plans; and
- unit plans.

Concord begins after the teacher has already planned the collaborative activity. It creates the paper instrumentation used to enact, observe, document, and assess the activity.

### 5.5 Future reporting or gradebook modules

A future reporting or gradebook module may combine:

- Concord scores;
- ScoreForm scores;
- Quillan scores;
- teacher-entered scores;
- project results; and
- grading policies.

Concord records scores and evidence. It does not determine final grades.

## 6. Design Principles

### 6.1 Paper-first

Printed artifacts are central, not fallback exports from a digital system.

The workflow should remain useful when students have no devices and when the teacher chooses to conduct the activity entirely on paper.

### 6.2 Human-reviewed

Concord files and presents evidence for human interpretation.

The system does not decide what handwriting means, whether a contribution was valuable, or whether a peer judgment is fair.

### 6.3 Preserve the source artifact

The scan is the canonical evidence record.

Metadata, notes, transcriptions entered manually, reviews, and scores are linked records. They do not replace or silently alter the original scan.

### 6.4 Clear module boundaries

Concord must not duplicate OMR, written-response evaluation, lesson planning, grading, or reporting functionality owned by other modules.

### 6.5 Activity-specific evidence

A Socratic seminar, laboratory group, design challenge, debate, and programming team should not be forced into one universal rubric.

Teachers should be able to select or adapt templates appropriate to the activity.

### 6.6 Separate evidence, review, score, grade, and report

These are distinct concepts:

- **Evidence:** the completed paper artifact or teacher record;
- **Review:** a human interpretation or moderation step;
- **Score:** a judgment about a criterion or activity component;
- **Grade:** a broader academic calculation that may combine many scores;
- **Report:** a presentation or communication of selected results.

Concord handles evidence, review, and scoring. Grade calculation and reporting belong elsewhere.

### 6.7 Provenance

Every artifact and score should preserve enough context to answer:

- who completed it;
- whom or what it concerns;
- which activity and session produced it;
- which template version was used;
- who reviewed or scored it;
- and when those actions occurred.

### 6.8 Minimal classroom burden

Evidence collection should not interfere with the collaboration being documented.

Forms should be as short and focused as the activity permits.

### 6.9 Privacy by default

Peer observations, contribution disputes, and teacher judgments may be sensitive.

Concord should avoid public rankings and should support restricted visibility for peer- and teacher-generated records.

### 6.10 Local-first

Concord should work within the Paper Data Suite local workspace model and should not require third-party cloud processing.

## 7. Core Domain Concepts

This section defines conceptual terms. It does not prescribe final classes, JSON schemas, or database tables.

### 7.1 Activity

An already-planned collaborative classroom task.

Examples:

- Socratic seminar;
- science laboratory;
- collaborative coding task;
- literature circle;
- group research project;
- debate;
- engineering challenge; and
- peer review workshop.

An activity may occur in one or more sessions.

### 7.2 Session

One occurrence or work period within an activity.

A multi-day project may have several sessions, each with different groups, roles, or artifacts.

### 7.3 Template

A reusable printable design.

Examples:

- discussion map;
- peer observation form;
- group process rubric;
- contribution record;
- teacher observation sheet;
- project retrospective; and
- artifact cover sheet.

A template is not yet assigned to a specific class, group, or student.

### 7.4 Template version

A fixed revision of a template.

Versioning is necessary because layout, prompts, QR placement, scoring criteria, or page structure may change over time.

A scanned artifact must remain linked to the exact template version that generated it.

### 7.5 Packet definition

A reusable collection of templates assembled for one kind of activity.

Example:

```text
Socratic Seminar Packet
├── Discussion map
├── Peer observer sheet
├── Group process rubric
└── Teacher scoring rubric
```

A packet definition is reusable and unassigned.

### 7.6 Packet instance

A generated packet tied to a specific classroom context.

A packet instance may be associated with:

- course or class;
- activity;
- session;
- group;
- student;
- teacher; and
- generation date.

### 7.7 Artifact instance

A particular generated copy of one template.

Examples:

- the discussion map generated for Group 3;
- the peer observation sheet assigned to Student A;
- the teacher observation page for Period 2;
- the retrospective sheet for the laboratory group.

Each artifact instance must have a stable identifier.

### 7.8 Artifact author

The person or group that completed the artifact.

Examples:

- an individual student;
- a peer observer;
- a group recorder;
- the full group;
- the teacher; or
- another authorized adult.

The author is not necessarily the subject.

### 7.9 Artifact subject

The person, group, session, or activity described by the artifact.

Examples:

- Student B;
- Group 4;
- the whole-class seminar;
- one project session; or
- one group product.

### 7.10 Scan

A digital image or PDF representation of the completed paper artifact.

A scan may contain:

- one artifact page;
- several pages;
- an entire packet;
- a mixed batch from multiple groups; or
- an attachment paired with a Concord cover sheet.

### 7.11 Filing metadata

The information used to associate a scan with its proper context.

Typical metadata may include:

- artifact instance ID;
- packet instance ID;
- template ID and version;
- activity ID;
- session ID;
- class ID;
- group ID;
- student ID;
- author role;
- subject type;
- page number; and
- privacy classification.

### 7.12 Review

A human examination of a scanned artifact.

A review may:

- confirm that the scan is complete;
- correct filing metadata;
- identify the author or subject;
- note missing or unreadable sections;
- accept or reject peer evidence;
- add a teacher note;
- flag the artifact for follow-up; or
- approve it for scoring.

### 7.13 Criterion

A defined aspect of performance or evidence.

Examples:

- responds to peers' ideas;
- supports claims with evidence;
- fulfills assigned responsibilities;
- advances group decision-making;
- contributes to the shared product; and
- helps the group revise its approach.

Criteria may be qualitative or scored.

### 7.14 Score

A teacher-approved judgment attached to a criterion or activity component.

A score may apply to:

- an individual;
- a group;
- an artifact;
- a session;
- an activity component; or
- a final collaborative outcome.

A score is not a grade.

### 7.15 Moderation

A review step in which the teacher evaluates the reliability or relevance of evidence before it affects a score.

Moderation may be especially important for:

- peer observations;
- disputed contribution records;
- conflicting group accounts;
- incomplete artifacts; and
- evidence created by students about other students.

### 7.16 External reference

A link to a related record owned by another Paper Data Suite module.

Examples:

- ScoreForm individual accountability check;
- Quillan written reflection;
- shared roster record;
- standards record;
- future lesson-plan record;
- future report or gradebook record.

## 8. Artifact Model

Concord artifacts fall into three conceptual classes.

### 8.1 Structured Concord artifacts

These are generated specifically by Concord and contain stable page layouts, QR codes, prompts, tables, rubrics, or graphic organizers.

Examples:

- teacher observation sheet;
- peer observation form;
- group process rubric;
- contribution log;
- decision map;
- concept map;
- project retrospective; and
- scoring rubric.

Concord identifies and files these artifacts but does not interpret handwritten content automatically.

### 8.2 Attached collaborative work

These are irregular or teacher-created artifacts associated with a Concord activity.

Examples:

- poster;
- handwritten design sketch;
- annotated text;
- group notes;
- chart paper;
- laboratory diagram;
- storyboard;
- project planning page; and
- printed collaborative document.

These may be filed using:

- a Concord cover sheet;
- a QR label;
- a companion artifact slip; or
- another page-level identifier.

### 8.3 Instructional scaffolds

These are printable materials that support the activity but may not need to be scanned.

Examples:

- role cards;
- discussion stems;
- collaboration norms;
- protocol instructions;
- group procedure cards; and
- peer-feedback guidance.

Some scaffolds may become evidence-bearing if students write on them. The template definition should declare whether a scaffold is expected to return to the system.

## 9. Artifact Taxonomy

The initial taxonomy should be broad enough to support different subjects without becoming a universal rubric.

### 9.1 `discussion_tracker`

Documents how ideas move through a discussion.

Examples:

- discussion web;
- question-response map;
- evidence-use tracker;
- idea-connection chart;
- seminar observation map.

### 9.2 `teacher_observation`

Provides a paper interface for teacher observation.

Examples:

- roster grid;
- group rotation sheet;
- anecdotal note form;
- targeted criterion tracker;
- conference record.

### 9.3 `peer_observation`

Allows a student to record evidence about another student or group.

Examples:

- seminar observer sheet;
- teamwork observation form;
- criterion-specific peer record;
- peer conference notes.

### 9.4 `group_process_rubric`

Supports evaluation of how the group worked.

Examples:

- collaboration rubric;
- group functioning rubric;
- project-team process rubric;
- laboratory teamwork rubric.

### 9.5 `contribution_record`

Documents responsibilities, tasks, decisions, or contributions.

Examples:

- contribution chart;
- responsibility record;
- task-completion record;
- artifact authorship sheet;
- role fulfillment record.

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
- sequence chart.

### 9.7 `collaborative_work_log`

Provides a lightweight chronological record.

Examples:

- session log;
- decision log;
- troubleshooting record;
- design iteration log;
- milestone record;
- project checkpoint sheet.

### 9.8 `group_retrospective`

Helps the group examine its process after or during the activity.

Examples:

- plus/delta;
- start/stop/continue;
- team retrospective;
- process reflection grid;
- next-session improvement plan.

This category should remain concise and structured. Extended individual writing belongs to Quillan.

### 9.9 `artifact_cover_sheet`

Associates irregular or externally created work with Concord metadata.

Examples:

- poster cover sheet;
- attached work routing page;
- project artifact identification page;
- multi-page submission cover.

### 9.10 `moderation_record`

Documents teacher review of evidence.

Examples:

- peer-evidence review form;
- conflicting-evidence resolution;
- attribution correction;
- accepted/rejected evidence record.

### 9.11 `scoring_rubric`

Supports criterion-level teacher scoring.

Examples:

- individual collaboration rubric;
- group outcome rubric;
- seminar performance rubric;
- project contribution rubric.

### 9.12 `correction_or_exception`

Handles unusual or damaged records.

Examples:

- missing-page form;
- incorrect group assignment;
- absence note;
- disputed attribution;
- rescan request;
- unmatched scan routing sheet.

## 10. Packet Model

Concord should treat packets as composable collections of artifacts rather than as lessons.

A packet may contain:

- student-facing artifacts;
- group-facing artifacts;
- peer-observer artifacts;
- teacher-facing artifacts;
- scoring artifacts;
- cover sheets; and
- optional links to ScoreForm or Quillan work.

### 10.1 Example: Socratic seminar packet

```text
Socratic Seminar Packet
├── Group discussion map
├── Peer observation sheet
├── Teacher observation tracker
├── Seminar scoring rubric
└── Optional Quillan reflection reference
```

### 10.2 Example: Science laboratory packet

```text
Science Laboratory Packet
├── Shared K-W-L or prediction chart
├── Group procedure organizer
├── Contribution record
├── Decision and troubleshooting log
├── Teacher observation sheet
├── Group process rubric
└── Optional ScoreForm accountability check reference
```

### 10.3 Example: Programming or engineering project packet

```text
Collaborative Project Packet
├── Task and responsibility record
├── Design decision matrix
├── Work-session log
├── Contribution record
├── Group retrospective
├── Teacher scoring rubric
└── Artifact cover sheet
```

## 11. Artifact Lifecycle

The conceptual lifecycle is:

```text
Select packet or templates
        ↓
Configure activity context
        ↓
Generate packet and artifact instances
        ↓
Print and distribute
        ↓
Complete artifacts on paper
        ↓
Collect and scan
        ↓
Identify and file pages
        ↓
Review scans and metadata
        ↓
Moderate evidence where needed
        ↓
Record scores
        ↓
Export or link scores elsewhere
        ↓
Retain, archive, or delete according to policy
```

### 11.1 Select

The teacher chooses a reusable packet definition or individual templates.

### 11.2 Configure

The teacher supplies only the context necessary to generate artifacts, such as:

- class;
- activity;
- session;
- groups;
- students;
- criteria;
- scorer;
- privacy setting; and
- linked ScoreForm or Quillan work.

This is configuration, not lesson planning.

### 11.3 Generate

Concord creates:

- printable PDFs;
- page-level QR codes;
- human-readable fallback identifiers;
- packet manifests;
- artifact instance records; and
- page numbering.

### 11.4 Complete

Students and teachers write, draw, annotate, or mark the printed artifacts.

### 11.5 Scan

Completed pages are scanned individually or in batches.

### 11.6 Identify and file

Concord reads page-level identifiers and associates each scan with its artifact instance.

This stage identifies the page. It does not interpret handwritten content.

### 11.7 Review

The teacher confirms:

- correct filing;
- scan quality;
- completeness;
- author and subject;
- relevance;
- privacy classification; and
- readiness for scoring.

### 11.8 Moderate

The teacher reviews student-generated evidence when it may affect a consequential score.

### 11.9 Score

The teacher records criterion or component scores while viewing the source artifact.

### 11.10 Export or link

Concord makes approved scores or evidence references available to other Paper Data Suite modules.

## 12. QR and Identification Design

Every scannable page should normally contain its own QR code.

Packet-level identification alone is insufficient because pages may be:

- separated;
- reordered;
- rescanned;
- submitted independently;
- attached to other work; or
- mixed with pages from other groups.

### 12.1 QR purpose

The QR code identifies and routes the artifact instance.

It does not encode student responses or scoring results.

### 12.2 Shared `PDS1` alignment

Concord QR codes should use the shared PDS Core `PDS1` contract rather than a Concord-specific payload grammar.

The shared payload should identify enough context to route the page, while Concord's local artifact record provides the complete module-specific meaning. Likely shared or Concord-specific references include:

- `module=concord`;
- class ID;
- assignment or activity-routing ID;
- page number and total pages;
- document or artifact type;
- template ID and version;
- artifact instance ID;
- packet instance ID;
- session ID;
- group ID, when applicable;
- student ID, when applicable;
- author or subject type; and
- privacy classification.

The exact field set cannot be finalized until PDS Core extends `PDS1` for Concord. The current contract requires `student_id`, but many Concord pages concern a group, teacher observation, session, or activity rather than one student. The shared contract must represent those cases directly without fake student records or overloaded fields.

QR payloads should contain only routing identifiers and minimal metadata. Names and other unnecessary personally identifiable information should remain outside the payload.

### 12.3 Human-readable fallback

Each page should also contain a visible short code or label for manual filing when:

- the QR code is damaged;
- the scan is incomplete;
- the code cannot be read; or
- the page must be handled without software.

### 12.4 Page design

Templates should reserve stable areas for:

- QR code;
- short identifier;
- title;
- activity and session context;
- student or group identification, when needed;
- page number;
- teacher review status; and
- template version.

## 13. Scan and Filing Model

PDS Core owns the shared active source-scan retention and provenance contract. Concord should retain each readable selected source through Core before Concord-specific QR extraction, page splitting, identification, filing, review, or scoring.

Concord's module-specific scanning responsibility is identification and filing, not content extraction.

### 13.1 Canonical source

The original scan should be preserved as the canonical artifact image or PDF.

### 13.2 Derived records

The following may be linked to the scan:

- corrected metadata;
- teacher notes;
- review status;
- moderation decisions;
- criterion scores;
- component scores;
- external references; and
- audit history.

### 13.3 Filing states

A scan may move through states such as:

- received;
- identified;
- unmatched;
- partially matched;
- filed;
- needs review;
- reviewed;
- approved for scoring;
- scored;
- superseded by rescan; and
- archived.

Final state names should be decided during contract design.

### 13.4 Rescans

A rescan should not silently erase the earlier image.

The later scan may supersede the earlier one while preserving:

- the original file;
- the reason for replacement;
- the date;
- the user who performed the action; and
- the relationship between versions.

## 14. Review and Moderation Model

### 14.1 Review is not transcription

A teacher may write a note or select a review status, but Concord should not require the teacher to recreate all handwritten content digitally.

### 14.2 Moderation status

Student-generated evidence may be marked conceptually as:

- unreviewed;
- accepted;
- accepted with qualification;
- rejected;
- disputed;
- insufficient;
- or not applicable.

The final set of states should remain small and understandable.

### 14.3 Missing evidence

The system must distinguish:

- not observed;
- not applicable;
- absent;
- incomplete artifact;
- unreadable artifact;
- insufficient evidence;
- and not demonstrated.

These conditions should not automatically receive the same score.

## 15. Scoring Model

### 15.1 Score ownership

A score is recorded by an authorized scorer, normally the teacher.

Student-generated peer ratings may be stored as evidence, but they should not become final Concord scores without teacher review.

### 15.2 Score targets

A score may target:

- one student;
- one group;
- one artifact;
- one criterion;
- one session;
- one activity component;
- or one shared outcome.

### 15.3 Score components

A conceptual score record may need:

- scorer;
- subject;
- criterion;
- scale;
- value;
- maximum or level set;
- artifact source;
- activity and session;
- individual or group scope;
- date;
- moderation status;
- note or rationale;
- superseded status; and
- export status.

### 15.4 Scoring scales

Concord should not impose one universal scale.

Possible scales include:

- binary;
- ordinal levels;
- numeric points;
- rubric bands;
- completion status;
- proficiency categories; and
- teacher-defined labels.

### 15.5 Score is not grade

Concord may record:

```text
Uses evidence in discussion: 3 of 4
Responds to peers' ideas: 2 of 4
Group process: 15 of 20
Shared product: 18 of 20
```

These are scores.

A future gradebook or reporting module may decide:

- how scores are weighted;
- whether they are combined;
- whether they are dropped;
- how they affect a course grade; and
- how they are reported.

Concord should not make those decisions.

## 16. Privacy and Access

### 16.1 Sensitive artifact types

The following may require restricted visibility:

- peer observations;
- contribution disputes;
- teacher moderation notes;
- individual scoring rubrics;
- correction records; and
- exception records.

### 16.2 Default visibility

Peer- and teacher-generated evidence should be private by default unless the teacher deliberately chooses another policy.

### 16.3 Public repository data

All examples, fixtures, screenshots, tests, and sample packets in the public repository must use synthetic students, classes, and activities.

### 16.4 Data minimization

QR payloads and artifact records should contain only the identifiers necessary to route and interpret the page.

## 17. Integration Model

Concord should depend on PDS Core for suite-level infrastructure and reference other module records through shared identifiers rather than direct package dependencies.

```text
pds-concord -> pds-core
pds-concord -/-> pds-scoreform
pds-concord -/-> pds-quillan
```

Concord may link to ScoreForm or Quillan work, but it should not import those modules merely to obtain shared workspace, roster, QR, routing, scan-retention, or standards behavior.

Shared PDS Core concepts include:

- student;
- class;
- teacher;
- roster;
- standard;
- assignment or activity;
- workspace;
- file location;
- export destination; and
- audit metadata.

### 17.1 ScoreForm integration

Concord may reference a ScoreForm assignment as:

- an individual accountability check;
- a pre- or post-activity content check;
- a structured peer or self-rating instrument; or
- another OMR artifact.

The actual form generation, scanning, OMR extraction, and scoring remain ScoreForm responsibilities.

### 17.2 Quillan integration

Concord may reference a Quillan assignment as:

- an individual reflection;
- written explanation;
- extended peer feedback;
- defense of a group decision; or
- analytical follow-up.

The actual written-response workflow remains Quillan's responsibility.

### 17.3 Future lesson-planning integration

A future planning module may supply Concord with:

- activity title;
- class;
- date;
- groups;
- selected criteria;
- packet recommendation; and
- related standards.

Concord should still function independently.

### 17.4 Future reporting integration

A future reporting module may consume:

- approved scores;
- criterion summaries;
- activity metadata;
- group and individual distinctions; and
- artifact references.

## 18. Representative Use Cases

### 18.1 Socratic seminar

The teacher selects a seminar packet and assigns peer observers.

Students complete:

- a discussion map;
- a peer observation form; and
- a group process rubric.

The teacher completes:

- a roaming observation sheet; and
- a scoring rubric.

The pages are scanned, identified, and filed by artifact instance. The teacher reviews the peer evidence, scores selected criteria, and optionally links a Quillan reflection.

### 18.2 Science laboratory

The teacher generates one group packet per laboratory team.

The packet contains:

- a K-W-L or prediction organizer;
- a decision and troubleshooting log;
- a contribution record;
- a group process rubric; and
- a teacher observation sheet.

The final laboratory explanation may be handled by Quillan, while an individual concept check may be handled by ScoreForm.

### 18.3 Collaborative programming task

The teacher generates:

- a responsibility record;
- a design decision matrix;
- a debugging log;
- a contribution record;
- a group retrospective; and
- a teacher scoring rubric.

The completed paper artifacts are scanned and filed. Concord stores the collaborative evidence and scores, while source code remains an external project artifact.

### 18.4 Attached poster or chart paper

The group creates work on a large sheet that is not itself a Concord template.

A Concord artifact cover sheet is completed and scanned with a photograph or scan of the poster. Concord files both under the same artifact relationship.

## 19. Initial Product Decisions

The following decisions are accepted for the conceptual design phase:

1. Concord is a paper-based collaborative-evidence system.
2. Concord begins after activity planning.
3. Concord generates templates and packets, not lesson plans.
4. Concord depends on PDS Core for shared workspace, roster, identifier, QR-contract, active scan-retention, routing-metadata, standards, and navigation infrastructure.
5. Concord must not create a separate QR grammar or duplicate PDS Core contracts.
6. PDS Core's shared QR contract must be extended before Concord implementation to register Concord and support artifacts without a single student subject.
7. Activity-specific groups, sessions, roles, packet definitions, artifacts, criteria, moderation, and scores remain Concord-owned.
8. Concord does not perform handwriting recognition.
9. Concord does not perform audio or video transcription.
10. Concord does not generate AI records of classroom discussion.
11. ScoreForm owns OMR workflows.
12. Quillan owns focused written-response workflows.
13. Concord preserves scans as canonical evidence while using PDS Core's retained source-scan and provenance contract.
14. QR codes identify and route artifact instances rather than encode responses.
15. Every scannable page should normally carry its own QR code.
16. Concord supports both individual- and group-level evidence.
17. Concord separates evidence, review, moderation, score, grade, and report.
18. Concord records scores but does not calculate course grades.
19. Concord uses activity-specific templates rather than one universal collaboration rubric.
20. Student-generated evidence requires provenance and may require teacher moderation.
21. Peer evidence is private by default.
22. Public repository examples use synthetic data.
23. Concord should integrate through shared references rather than duplicate sibling-module capabilities.
24. The minimum viable workflow must remain useful without cloud services or student devices.

## 20. Open Questions for Contract Design

The conceptual model leaves several questions for the next phase:

1. What is the minimum required metadata for every artifact instance?
2. Which metadata belongs in the QR payload, the QR-linked local record, and the visible printed page?
3. How should PDS Core extend `PDS1` to register `module=concord`?
4. How should `PDS1` represent group-, teacher-, session-, and activity-level artifacts that do not have one `student_id`?
5. Should Concord's `activity_id` map to PDS Core's existing `assignment_id`, or does the suite need a broader shared work-item concept?
6. Which Concord routes require new PDS Core helpers, and which module-specific subdirectories may safely live inside the canonical assignment folder?
7. Which identifiers and validation rules should be shared through PDS Core, and which identifiers remain Concord-specific?
8. How should packet definitions represent optional and repeated artifacts?
9. How should one artifact represent multiple authors or subjects?
10. How should changing group membership across sessions be represented?
11. Should artifact categories be a fixed enumeration, extensible identifiers, or both?
12. How should custom teacher-created templates declare their printable fields and filing metadata?
13. How should Concord represent irregular attachments and multi-page artifacts?
14. Which review and moderation states are necessary without overcomplicating the workflow?
15. How should scores reference one or several source artifacts?
16. How should corrected scores and rescored artifacts preserve history?
17. How should Concord use PDS Core standards profiles and durable `standard_id` references without moving Concord-specific criteria into Core?
18. How should Concord export scores without making assumptions about grading systems?
19. What privacy controls are required for peer observations and disputes?
20. What is the smallest practical user interface for reviewing scanned pages and entering scores?
21. Which three representative packets should be modeled first to test the contracts?

## 21. Recommended Next Step

Before creating schemas, model three representative packet types in detail:

1. a Socratic seminar;
2. a science laboratory group; and
3. a collaborative programming or engineering project.

For each packet, identify:

- templates;
- authors;
- subjects;
- pages;
- QR context;
- scan workflow;
- review states;
- scoring targets;
- cross-module references; and
- privacy requirements.

The common requirements that survive all three cases should become the basis of the first Concord data contracts.
