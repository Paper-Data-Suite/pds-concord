# Science Laboratory Group Packet Model

**Status:** Draft for contract discovery
**Project:** Paper Data Suite
**Module:** `pds-concord`
**Location:** Intended for `local_work/packet_models/`
**Date:** July 11, 2026

## 1. Purpose

This document models one representative `pds-concord` packet for a collaborative science laboratory activity.

Its purpose is not to prescribe a particular laboratory method, supply scientific content, or produce final printable forms. It tests the Concord conceptual design against an activity involving:

* shared physical materials;
* coordinated procedures;
* multiple forms of contribution;
* observations and data collected over time;
* troubleshooting and revision;
* safety and equipment responsibilities;
* shared products;
* individual accountability; and
* possible work across several class sessions.

The model assumes that:

* the teacher has already planned the laboratory;
* the scientific procedure, content, materials, and instructional objectives exist before Concord is used;
* the class roster exists through `pds-core`;
* Concord generates paper artifacts used to document the collaborative process;
* students and teachers complete those artifacts by hand;
* completed pages are scanned and filed;
* Concord does not perform handwriting recognition, OMR, transcription, or AI analysis;
* the teacher reviews the evidence and records scores manually;
* substantive written laboratory explanations belong to `pds-quillan`; and
* machine-readable individual checks belong to `pds-scoreform`.

## 2. Baseline Laboratory Scenario

This representative case assumes students work in groups of three or four to conduct an investigation over one or two class sessions.

The laboratory includes:

* an initial group setup;
* shared equipment and materials;
* procedural stages;
* observations or measurements;
* decisions about invalid trials or unexpected results;
* division and rotation of responsibilities;
* a shared laboratory product or dataset;
* a brief group process review; and
* teacher scoring based on several sources of evidence.

The packet should also be adaptable to:

* demonstrations with student observation teams;
* inquiry laboratories;
* verification laboratories;
* engineering design challenges;
* field observations;
* mathematics or statistics investigations;
* collaborative simulations conducted without student devices; and
* longer experimental projects.

The packet does not assume that every laboratory uses assigned roles or every artifact listed below.

## 3. Activity Structure

### 3.1 Activity

A laboratory activity is associated with:

* one class;
* one investigation, experiment, or design task;
* one or more laboratory groups;
* one or more sessions;
* optional stages or phases;
* teacher-selected collaborative criteria;
* optional standards references from `pds-core`;
* optional Quillan work; and
* optional ScoreForm work.

The laboratory procedure itself remains teacher- or curriculum-owned. Concord stores only enough activity context to generate, identify, route, review, and score the collaborative artifacts.

### 3.2 Session

A session represents one class period or laboratory work period.

A multi-session activity may include:

* setup and prediction;
* initial trials;
* data collection;
* troubleshooting;
* revised trials;
* analysis;
* cleanup; and
* group review.

Group membership, roles, and responsibilities should be associated with a session or activity stage rather than assumed to remain fixed.

### 3.3 Group

A laboratory group is a set of students working together during a defined session or series of sessions.

The model must support:

* stable groups;
* temporary groups;
* students joining late;
* students leaving early;
* absent members;
* group reassignment;
* merged groups;
* and groups that divide into subteams for part of the work.

### 3.4 Participant roles and responsibilities

Possible roles include:

* materials manager;
* procedure reader;
* equipment operator;
* data recorder;
* measurement checker;
* safety monitor;
* timekeeper;
* analyst;
* cleanup coordinator; and
* group facilitator.

These are activity-specific responsibilities, not permanent student attributes.

A teacher may use responsibilities without formal role titles. Concord should therefore support both:

* named roles; and
* direct task assignments.

## 4. Packet Composition

The baseline packet contains seven Concord artifact types and two optional external references.

```text
Science Laboratory Group Packet
├── A. Group Setup and Responsibility Record
├── B. Shared Evidence and Observation Organizer
├── C. Experimental Decision and Troubleshooting Log
├── D. Teacher Laboratory Observation Tracker
├── E. Group Process Review
├── F. Teacher Scoring Rubric
├── G. Artifact Cover Sheet
├── H. Optional Quillan Laboratory Explanation Reference
└── I. Optional ScoreForm Individual Check Reference
```

### Required baseline artifacts

1. Group Setup and Responsibility Record
2. Teacher Laboratory Observation Tracker
3. Teacher Scoring Rubric

### Recommended artifacts

4. Shared Evidence and Observation Organizer
5. Experimental Decision and Troubleshooting Log
6. Group Process Review

### Conditional artifact

7. Artifact Cover Sheet

### External optional work

8. Quillan Laboratory Explanation Reference
9. ScoreForm Individual Check Reference

## 5. Artifact Inventory

| Artifact                                      | Primary author                    | Primary subject                 | Scope               | Scanned                  | Scored directly             | Moderation             |
| --------------------------------------------- | --------------------------------- | ------------------------------- | ------------------- | ------------------------ | --------------------------- | ---------------------- |
| Group Setup and Responsibility Record         | Group recorder or members         | Group and members               | Group/multi-subject | Yes                      | Possibly                    | Teacher review         |
| Shared Evidence and Observation Organizer     | Group recorder or several members | Group investigation             | Group/session       | Yes                      | Usually as product evidence | Teacher review         |
| Experimental Decision and Troubleshooting Log | Group members                     | Group process and investigation | Group/session       | Yes                      | Possibly                    | Teacher review         |
| Teacher Laboratory Observation Tracker        | Teacher                           | Several students and groups     | Multi-subject       | Yes                      | No, evidence source         | Teacher-authored       |
| Group Process Review                          | Group recorder or group consensus | Group and session               | Group               | Yes                      | Optional                    | Teacher review         |
| Teacher Scoring Rubric                        | Teacher                           | One student or group            | Individual/group    | Yes or digitally entered | Yes                         | Final teacher judgment |
| Artifact Cover Sheet                          | Group recorder or teacher         | Attached work                   | Group/artifact      | Yes                      | No                          | Filing review          |
| Quillan Laboratory Explanation                | Student or group                  | Individual or group response    | External            | Quillan workflow         | Quillan workflow            | Quillan workflow       |
| ScoreForm Individual Check                    | Student                           | Individual learning             | External            | ScoreForm workflow       | ScoreForm workflow          | ScoreForm workflow     |

## 6. Artifact A: Group Setup and Responsibility Record

### 6.1 Purpose

The Group Setup and Responsibility Record documents how the group begins and coordinates the laboratory.

It may record:

* group membership;
* initial responsibilities;
* role rotation;
* procedural stages;
* materials responsibility;
* expected handoffs;
* and changes made during the activity.

It is not a lesson plan or a replacement for the laboratory directions.

### 6.2 Author and subject

* **Author:** group recorder, several group members, or teacher;
* **Subject:** laboratory group and its members;
* **Scope:** group with individual responsibility references.

### 6.3 Suggested paper structure

Possible sections include:

* group identification;
* session or date;
* member list;
* role or responsibility table;
* activity stage;
* expected task;
* student responsible;
* partner or checker;
* completion or handoff note;
* role-change area;
* teacher initials or review area.

A simple structure might resemble:

| Stage   | Responsibility      | Primary student | Supporting student | Change or handoff |
| ------- | ------------------- | --------------- | ------------------ | ----------------- |
| Setup   | Assemble apparatus  | Student A       | Student B          |                   |
| Trial 1 | Record measurements | Student C       | Student D          |                   |
| Trial 2 | Operate equipment   | Student B       | Student A          |                   |
| Cleanup | Return materials    | Student D       | Group              |                   |

### 6.4 Scoring use

The form may provide evidence of:

* preparation;
* coordination;
* role fulfillment;
* reliability;
* equitable distribution of responsibilities;
* adaptation;
* and completion of necessary group tasks.

Being assigned a responsibility does not prove that the student fulfilled it.

The final score should rely on evidence of performance, not merely the printed assignment.

### 6.5 Contract implications

This artifact requires:

* group-level subject;
* multiple student references;
* role or responsibility assignments;
* stage or time context;
* optional supporting students;
* role changes;
* handoffs;
* and a distinction between planned responsibility and observed completion.

## 7. Artifact B: Shared Evidence and Observation Organizer

### 7.1 Purpose

The Shared Evidence and Observation Organizer gives the group a paper structure for recording observations, measurements, patterns, diagrams, or other activity evidence.

It may function as a:

* shared data table;
* observation chart;
* K-W-L chart;
* prediction-and-result organizer;
* claim-evidence-reasoning organizer;
* annotated diagram;
* comparison matrix;
* trial record;
* or group concept map.

Concord provides the paper structure and filing workflow. It does not interpret the handwritten or numeric content.

### 7.2 Relationship to subject-specific laboratory materials

This artifact should be used only when a reusable Concord organizer is appropriate.

If the teacher or curriculum already provides a specialized laboratory worksheet, Concord may instead associate it through an Artifact Cover Sheet.

Concord should not attempt to replace every discipline-specific laboratory form.

### 7.3 Author and subject

* **Author:** group recorder, several named contributors, or the group collectively;
* **Subject:** the group investigation, session, or trial;
* **Scope:** group.

### 7.4 Suggested paper structure

Depending on the selected template, the page may include:

* investigation question;
* initial prediction;
* observation or measurement table;
* sketch or diagram area;
* patterns noticed;
* conflicting observations;
* invalid or excluded trial notation;
* result summary;
* contributor or recorder identification;
* continuation-page reference.

### 7.5 Scoring use

This artifact may provide evidence concerning:

* completeness of the shared record;
* accuracy or integrity of data recording;
* organization;
* use of evidence;
* connection between observation and decision;
* and quality of the group product.

It should not automatically establish individual contribution or understanding.

### 7.6 Contract implications

This artifact requires:

* group authorship;
* optional multiple named contributors;
* session and trial references;
* continuation pages;
* optional teacher-provided template variants;
* group-level scoring;
* and links to individual accountability evidence elsewhere.

## 8. Artifact C: Experimental Decision and Troubleshooting Log

### 8.1 Purpose

The Experimental Decision and Troubleshooting Log documents important moments when the group:

* notices a problem;
* identifies an unexpected result;
* questions a procedure;
* detects equipment failure;
* rejects or repeats a trial;
* compares alternatives;
* requests teacher assistance;
* changes its method within allowed limits;
* or explains why it continued without changing the method.

This is not intended to record every minor action.

### 8.2 Author and subject

* **Author:** one recorder, several members, or teacher;
* **Subject:** group process, investigation, and specific event;
* **Scope:** group/session/event.

### 8.3 Suggested paper structure

A concise entry may include:

| Time or stage | What happened? | Evidence noticed | Group decision | Who contributed? | Teacher consulted? |
| ------------- | -------------- | ---------------- | -------------- | ---------------- | ------------------ |

The form may also include:

* equipment or material involved;
* trial number;
* result of the decision;
* unresolved issue;
* follow-up needed;
* and teacher notation.

### 8.4 Equipment and safety events

The log may document routine laboratory problems such as:

* apparatus not functioning;
* material unavailable;
* measurement inconsistency;
* sample contamination;
* procedural ambiguity;
* or trial interruption.

It should not replace required school or district safety-incident documentation.

A serious safety event may be referenced as requiring separate follow-up without storing unnecessary sensitive details in Concord.

### 8.5 Scoring use

The log may provide evidence of:

* collaborative problem solving;
* use of evidence;
* decision-making;
* adaptability;
* communication;
* responsibility;
* and appropriate help-seeking.

A group should not be penalized merely because equipment failed or an investigation produced unexpected results.

The relevant question is how the group recognized and responded to the situation.

### 8.6 Contract implications

This artifact introduces:

* event-level evidence;
* trial or stage identifiers;
* equipment or environmental context;
* group decisions;
* several contributors to one decision;
* teacher-intervention references;
* and exceptions that are not student-performance failures.

## 9. Artifact D: Teacher Laboratory Observation Tracker

### 9.1 Purpose

The Teacher Laboratory Observation Tracker allows the teacher to record brief evidence while moving among several groups.

It must remain fast enough to use while supervising materials, safety, procedure, and instruction.

### 9.2 Author and subject

* **Author:** teacher;
* **Subjects:** multiple students, multiple groups, or both;
* **Scope:** multi-subject and multi-group.

### 9.3 Suggested paper structure

Possible sections include:

* group roster;
* observation round or timestamp;
* selected criteria;
* short note cells;
* group-level process notes;
* individual contribution notes;
* support provided;
* follow-up needed;
* safety or equipment concern;
* not observed;
* insufficient evidence;
* absent;
* and excused.

The teacher may use one page for:

* one group;
* several groups;
* one class period;
* or one criterion across the class.

### 9.4 Candidate observation criteria

Possible teacher-selected criteria include:

* contributes to setup or procedure;
* handles materials responsibly;
* records or verifies evidence;
* communicates relevant information;
* fulfills an assigned responsibility;
* supports another member's understanding;
* participates in troubleshooting;
* uses evidence when making decisions;
* adapts appropriately;
* and contributes to cleanup or closure.

The tracker should recognize nonverbal and technical contributions.

### 9.5 Safety-related observations

Safety may be recorded when it is a relevant criterion or an immediate concern.

However:

* a blank safety field should not imply unsafe conduct;
* serious incidents may require a separate institutional process;
* Concord should avoid becoming a disciplinary incident system;
* and safety-related records may require restricted access.

### 9.6 Contract implications

This artifact reinforces the need for:

* one artifact with multiple groups and students as subjects;
* group-level and individual-level notes on the same page;
* contextual observation rounds;
* non-performance exception states;
* restricted privacy;
* and later links from one source artifact to several scores.

## 10. Artifact E: Group Process Review

### 10.1 Purpose

The Group Process Review captures a concise retrospective on how the group worked.

It should help the group identify:

* one effective practice;
* one problem;
* one important decision;
* one responsibility that was handled well;
* one adjustment for future work;
* and any unresolved disagreement.

It is not an extended scientific explanation or essay.

### 10.2 Author and subject

* **Author:** recorder acting for the group, several named students, or group consensus;
* **Subject:** laboratory group and session;
* **Scope:** group.

### 10.3 Suggested paper structure

Possible sections include:

* plus/delta;
* start/stop/continue;
* responsibilities completed;
* responsibilities redistributed;
* successful decision;
* obstacle;
* contribution type that was important but not obvious;
* next-session adjustment;
* consensus status;
* and recorder identification.

### 10.4 Scoring use

The artifact may support:

* formative feedback;
* group-process scoring;
* role adjustment;
* teacher conferencing;
* and planning of later collaborative activities.

It should not automatically produce identical individual scores for every group member.

### 10.5 Contract implications

This artifact requires:

* group authorship mode;
* consensus status;
* session reference;
* group-level score linkage;
* and optional links to specific responsibilities or troubleshooting events.

## 11. Artifact F: Teacher Scoring Rubric

### 11.1 Purpose

The Teacher Scoring Rubric records the teacher's criterion-level judgment after reviewing the laboratory evidence.

It separates evidence collection from final scoring.

### 11.2 Author and subject

* **Author/scorer:** teacher;
* **Subject:** one student or one group;
* **Scope:** individual or group.

### 11.3 Possible individual criteria

Individual criteria might include:

* fulfills responsibilities;
* contributes useful work;
* communicates relevant observations;
* supports accurate data collection;
* participates in troubleshooting;
* uses evidence in decisions;
* assists group coordination;
* handles materials appropriately;
* and contributes to closure or cleanup.

### 11.4 Possible group criteria

Group criteria might include:

* coordinates responsibilities;
* maintains a usable shared record;
* responds productively to unexpected results;
* makes evidence-based decisions;
* preserves data integrity;
* adapts without losing the purpose of the investigation;
* uses materials and equipment responsibly;
* and completes the shared outcome.

### 11.5 Evidence references

A score may reference:

* Group Setup and Responsibility Record;
* Shared Evidence and Observation Organizer;
* Experimental Decision and Troubleshooting Log;
* Teacher Laboratory Observation Tracker;
* Group Process Review;
* attached laboratory work;
* ScoreForm individual check;
* Quillan explanation;
* or teacher professional judgment.

### 11.6 Paper versus digital entry

The scoring rubric may be:

* printed, completed, scanned, and filed; or
* completed digitally while the teacher views scanned evidence.

Both workflows should produce the same conceptual score record.

### 11.7 Score is not grade

Concord may record:

```text
Role fulfillment: 3 of 4
Evidence-based decision-making: 4 of 4
Group coordination: 3 of 4
Shared laboratory record: 17 of 20
```

These are scores or activity components.

Concord does not determine how they affect a course grade.

## 12. Artifact G: Artifact Cover Sheet

### 12.1 Purpose

The Artifact Cover Sheet associates externally created or irregular laboratory work with the Concord activity.

Examples include:

* teacher-provided laboratory worksheet;
* graph paper;
* large diagram;
* chart paper;
* printed spreadsheet;
* photograph of a physical model;
* poster;
* handwritten calculation sheet;
* or curriculum-supplied data record.

### 12.2 Author and subject

* **Author:** group recorder or teacher;
* **Subject:** attached artifact and group;
* **Scope:** group/artifact.

### 12.3 Suggested paper structure

The cover sheet may include:

* activity;
* session;
* group;
* artifact title;
* artifact type;
* contributors;
* number of attached pages or images;
* relationship to scoring criteria;
* missing or damaged component note;
* and teacher filing confirmation.

### 12.4 Contract implications

This artifact requires:

* attachment relationships;
* one cover sheet linked to several files or pages;
* external artifact types;
* contributor lists;
* artifact completeness status;
* and provenance between the cover sheet and attached evidence.

## 13. External Reference H: Quillan Laboratory Explanation

Substantial written work belongs to Quillan.

Examples include:

* formal laboratory report;
* claim-evidence-reasoning response;
* explanation of unexpected results;
* analysis of error;
* written comparison of trials;
* individual reflection on learning;
* and extended defense of a group conclusion.

Concord may store:

* Quillan assignment ID;
* whether the response is individual or group-authored;
* its relationship to the laboratory activity;
* whether its score may inform Concord scoring;
* and which Concord criteria or artifacts it complements.

Concord should not reproduce Quillan's writing-review workflow.

## 14. External Reference I: ScoreForm Individual Check

An individual accountability check may be processed by ScoreForm.

Examples include:

* pre-lab safety or procedure check;
* post-lab concept quiz;
* interpretation of a graph;
* identification of variables;
* selection of a valid conclusion;
* and short structured self- or peer-rating using OMR.

Concord may store:

* ScoreForm assignment ID;
* relationship to the activity;
* whether the result is required;
* whether it informs individual accountability;
* and which Concord score component may reference it.

Concord should not perform OMR or duplicate ScoreForm result handling.

## 15. Packet Generation Model

### 15.1 Teacher configuration

The teacher supplies:

* class;
* activity ID and title;
* session or sessions;
* group membership;
* roles or responsibilities, if used;
* selected Concord templates;
* selected criteria;
* scoring scale;
* privacy settings;
* optional standards profile and standard IDs;
* optional ScoreForm reference;
* optional Quillan reference;
* and optional attached-artifact expectations.

This is activity instrumentation, not laboratory planning.

### 15.2 Generated artifact instances

For a group of four students, Concord might generate:

* one Group Setup and Responsibility Record;
* one Shared Evidence and Observation Organizer;
* one Experimental Decision and Troubleshooting Log;
* one Group Process Review;
* one Artifact Cover Sheet, if needed;
* four individual Teacher Scoring Rubrics or one group rubric;
* and a teacher tracker covering several groups.

Each scannable page receives:

* one artifact instance ID;
* one page-level QR code;
* one human-readable fallback code;
* template ID and version;
* activity and session context;
* group or student labels as appropriate;
* and page number.

## 16. QR and Routing Requirements

### 16.1 Shared Core contract

Concord must use the shared PDS Core QR and routing contract.

The science laboratory case requires the shared contract to support:

* group-level artifacts without one student subject;
* multi-student responsibility records;
* teacher-authored multi-group trackers;
* event-level troubleshooting records;
* attached-artifact cover sheets;
* individual scoring pages;
* and multi-session group work.

### 16.2 Required routing concepts

The shared payload or linked local record must resolve:

* module;
* class;
* activity or assignment-routing ID;
* session;
* group;
* artifact instance;
* packet instance;
* template and version;
* document type;
* page number and total pages;
* author or authorship mode;
* subject scope;
* student ID when applicable;
* stage or trial when useful;
* and privacy classification.

### 16.3 Avoided workarounds

Concord must not:

* use synthetic students to represent groups;
* place group IDs into `student_id`;
* treat the recorder as the sole owner of group work;
* encode laboratory content into the QR payload;
* or create a separate Concord QR grammar.

## 17. Scan and Filing Workflow

### 17.1 Intake

The teacher may scan:

* one group's packet;
* several group packets;
* an entire class batch;
* teacher observation sheets;
* attached curriculum pages;
* or photographs and paper cover sheets.

PDS Core retains the readable source scan before Concord-specific processing.

### 17.2 Concord processing

Concord:

* splits multi-page files when necessary;
* reads page QR codes;
* identifies artifact instances;
* routes pages to the activity, session, and group;
* preserves source provenance;
* associates cover sheets with attachments;
* flags missing, duplicate, or conflicting pages;
* and presents the evidence for teacher review.

Concord does not interpret handwritten data or scientific content.

### 17.3 Multi-session continuity

Artifacts may:

* continue across sessions;
* receive continuation pages;
* be replaced after an invalid trial;
* be supplemented by later pages;
* or be superseded by a rescan.

The system should preserve chronology and relationships without silently replacing earlier evidence.

## 18. Review Workflow

The teacher reviews artifacts for:

* correct class;
* correct activity;
* correct session;
* correct group;
* correct participants;
* correct author or recorder;
* scan readability;
* page completeness;
* attachment completeness;
* role changes;
* privacy;
* relevance;
* and readiness for scoring.

### 18.1 Responsibility review

The teacher may distinguish:

* assigned;
* completed;
* partially completed;
* reassigned;
* not applicable;
* not observed;
* and prevented by circumstances.

### 18.2 Troubleshooting review

An unsuccessful trial should not automatically count as poor performance.

The teacher reviews:

* what happened;
* what evidence the group noticed;
* whether the group's response was reasonable;
* whether assistance was needed;
* and whether the event was within the group's control.

### 18.3 Safety or equipment concerns

Concord may record that a concern occurred and that follow-up is required.

It should not replace official safety, disciplinary, medical, or incident-reporting systems.

## 19. Scoring Model

### 19.1 Individual score targets

Possible individual targets include:

* contribution to setup;
* role or responsibility fulfillment;
* data collection or verification;
* communication;
* evidence-based reasoning;
* troubleshooting;
* support for peers;
* materials responsibility;
* and participation in cleanup or closure.

### 19.2 Group score targets

Possible group targets include:

* coordination;
* shared-record quality;
* evidence integrity;
* decision-making;
* adaptability;
* responsibility for materials;
* completion of the investigation;
* and quality of the collaborative process.

### 19.3 Evidence-to-score relationship

A score may reference:

* several group artifacts;
* one teacher tracker;
* one individual record;
* one external Quillan response;
* one ScoreForm result;
* an attached laboratory product;
* or teacher professional judgment.

A group score and an individual score may rely on some of the same source artifacts while remaining separate judgments.

### 19.4 Missing and exceptional states

The scoring workflow should support:

* absent;
* excused;
* not observed;
* insufficient evidence;
* not applicable;
* equipment failure;
* activity interrupted;
* responsibility reassigned;
* and score deferred.

These conditions must not automatically become low scores.

## 20. Privacy Model

| Artifact                                  | Default privacy                  |
| ----------------------------------------- | -------------------------------- |
| Group Setup and Responsibility Record     | Group-and-teacher                |
| Shared Evidence and Observation Organizer | Group, class-limited, or teacher |
| Decision and Troubleshooting Log          | Group-and-teacher                |
| Teacher Laboratory Observation Tracker    | Teacher-restricted               |
| Group Process Review                      | Group-and-teacher                |
| Teacher Scoring Rubric                    | Teacher and scored subject       |
| Artifact Cover Sheet                      | Same as attached artifact        |
| Quillan Reference                         | Governed by Quillan              |
| ScoreForm Reference                       | Governed by ScoreForm            |

Safety concerns, disputes, and teacher notes may require more restrictive access than ordinary group artifacts.

## 21. Exception Cases

### 21.1 Absent student

An absent student may have:

* no assigned role;
* an excused role;
* a later alternate responsibility;
* no score;
* or a separate accountability activity.

### 21.2 Late arrival or early departure

A student may participate in only part of a session.

Roles and evidence need time or stage context.

### 21.3 Role change

Responsibilities may rotate by trial or stage.

The system must preserve the earlier assignment and the later reassignment.

### 21.4 Equipment failure

Equipment failure is contextual evidence, not automatic evidence of poor collaboration.

### 21.5 Invalid trial

A group may reject or repeat a trial.

The earlier record should remain part of the activity history.

### 21.6 Group reassignment

A student may move to another group because of absence, equipment availability, or teacher intervention.

Membership must be session- and time-sensitive.

### 21.7 One artifact, several contributors

A data sheet may be physically completed by one recorder while reflecting observations and decisions from the full group.

The model must not equate handwriting with sole authorship.

### 21.8 One tracker, several groups

A teacher observation sheet may span the entire class.

The source artifact must link to several later individual and group scores.

### 21.9 Attached artifact without QR code

An external laboratory worksheet may be routed through a Concord cover sheet or QR label.

### 21.10 Serious safety event

Concord may record that work stopped or that external documentation exists.

It should not become the authoritative safety-incident record.

## 22. Contract Requirements Discovered

This packet adds or reinforces requirements for:

1. activity stages or phases;
2. session-specific groups;
3. time- or stage-specific responsibilities;
4. role rotation and reassignment;
5. planned responsibility distinct from observed fulfillment;
6. group artifacts with multiple contributors;
7. group recorders who are not sole authors;
8. teacher artifacts spanning several groups;
9. event-level troubleshooting evidence;
10. trial identifiers;
11. equipment or environmental context;
12. circumstances outside student control;
13. external artifact attachments;
14. cover-sheet-to-attachment relationships;
15. continuation pages;
16. multi-session chronology;
17. group and individual scores derived from overlapping evidence;
18. subject-specific forms that remain outside Concord;
19. safety-related privacy and module boundaries;
20. retained source provenance through PDS Core;
21. external ScoreForm and Quillan references;
22. group-level QR routing;
23. multi-author and multi-subject artifacts;
24. nonverbal and technical contributions;
25. score-exception states;
26. and corrections or rescans that preserve history.

## 23. Provisional Cross-Case Comparison

| Requirement                          | Socratic seminar | Science laboratory    |
| ------------------------------------ | ---------------- | --------------------- |
| Student author distinct from subject | Central          | Sometimes             |
| Group-level artifact                 | Yes              | Yes                   |
| Multi-subject teacher tracker        | Yes              | Yes                   |
| Session-specific roles               | Yes              | Yes                   |
| Role rotation                        | Possible         | Common                |
| Physical materials                   | Limited          | Central               |
| Troubleshooting events               | Possible         | Central               |
| External artifact attachment         | Possible         | Common                |
| Peer evidence moderation             | Central          | Optional              |
| Group product evidence               | Moderate         | Central               |
| Individual accountability elsewhere  | Useful           | Often necessary       |
| Nonverbal contribution               | Important        | Essential             |
| Safety context                       | Rare             | Potentially important |
| Multi-session continuity             | Possible         | Common                |

## 24. Decisions Supported by This Model

The science laboratory case supports these provisional decisions:

1. Concord must distinguish roles from responsibilities.
2. Responsibilities need stage or time context.
3. Group artifacts may have multiple contributors without multiple physical writers.
4. A recorder is not automatically the sole author.
5. Teacher trackers may span several groups.
6. Concord needs an attachment model for external paper artifacts.
7. Troubleshooting should be represented as evidence-bearing events.
8. Circumstances outside student control must remain separate from performance.
9. Nonverbal, technical, organizational, and material contributions must be supported.
10. Extended laboratory writing belongs to Quillan.
11. Machine-readable individual checks belong to ScoreForm.
12. Concord does not replace subject-specific laboratory worksheets.
13. Safety notes may exist in Concord, but official incident management belongs elsewhere.
14. Group and individual scores may reference overlapping evidence without becoming the same score.
15. The PDS Core QR contract must support group, session, event, and multi-subject Concord artifacts.

## 25. Open Questions

1. Should Concord distinguish formally between a `role` and a `responsibility`, or model both through one assignment structure?
2. How much stage or timing precision is necessary for responsibility changes?
3. Should a troubleshooting entry be its own artifact record or an entry inside one log artifact?
4. How should one paper data sheet represent several contributors without requiring students to initial every field?
5. Should a teacher tracker spanning several groups be one artifact with many subjects or one scan with several derived evidence records?
6. Which laboratory organizers should ship as general Concord templates?
7. Where is the boundary between a reusable Concord organizer and a subject-specific laboratory worksheet?
8. How should external attachments be named and grouped after scanning?
9. Should photographs of physical products be treated as routed scan evidence or as a separate attachment type?
10. How should Concord represent a trial that was rejected, repeated, or invalidated?
11. Which safety-related metadata is appropriate without turning Concord into an incident system?
12. Should group process scores be assignable to individuals automatically, or only through an explicit teacher decision?
13. Should an individual responsibility score require at least one individual-specific source?
14. How should session continuity work when the group roster changes between days?
15. Which privacy classifications should be shared through PDS Core?

## 26. Next Cross-Case Test

The third representative packet should model a collaborative programming or engineering project.

That case should test:

* longer-duration projects;
* several work sessions;
* changing and overlapping responsibilities;
* external digital products;
* iterative design;
* versioned contributions;
* dependencies between students;
* partially independent subteams;
* milestone reviews;
* and contribution evidence that extends beyond one class period.

After that model is complete, the three cases should be compared in a formal cross-case requirements matrix before any data contracts are written.
