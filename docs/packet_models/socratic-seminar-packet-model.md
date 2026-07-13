# Socratic Seminar Packet Model

**Status:** Draft for contract discovery  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Location:** `docs/packet_models/`  
**Date:** July 11, 2026

## 1. Purpose

This document models one representative `pds-concord` packet for a Socratic seminar.

Its purpose is not to prescribe one seminar method or produce final printable forms. It tests the Concord conceptual design against a realistic discussion-centered classroom activity so that later data contracts reflect actual paper, scan, filing, review, moderation, and scoring needs.

The model assumes that:

- the teacher has already planned the seminar;
- the class roster already exists through `pds-core`;
- Concord generates the paper instruments used during the seminar;
- students and the teacher complete those instruments by hand;
- the completed pages are scanned and filed;
- Concord does not perform handwriting recognition, transcription, OMR, or AI analysis;
- the teacher reviews the scanned evidence and records scores manually; and
- any extended individual written reflection belongs to `pds-quillan`.

## 2. Baseline Seminar Scenario

This representative case uses a fishbowl or rotating-circle Socratic seminar because it produces several different kinds of collaborative evidence:

- active participants discuss a text or problem;
- peer observers document specific discussion behaviors;
- one observer maps the movement of ideas across the group;
- the teacher circulates, observes, and records evidence;
- the group completes a concise process review; and
- the teacher scores selected individual and group criteria after reviewing the artifacts.

The packet should also be adaptable to:

- a whole-class seminar;
- several simultaneous small seminars;
- partner-led seminars;
- student-facilitated seminars; and
- multi-session seminar cycles.

The representative model does not require all teachers to use every artifact.

## 3. Activity Structure

### 3.1 Activity

A single Socratic seminar activity associated with:

- one class;
- one discussion topic, text, problem, or question set;
- one or more seminar groups;
- one or more sessions;
- an optional standards profile and selected standards from `pds-core`;
- teacher-selected Concord criteria; and
- optional references to related ScoreForm or Quillan assignments.

### 3.2 Session

A session represents one actual seminar occurrence.

A session may contain:

- one whole-class seminar;
- one inner-circle and outer-circle rotation;
- several simultaneous small-group seminars; or
- one part of a multi-day seminar.

Group membership and student roles must be attached to the session rather than assumed to remain fixed for the entire activity.

### 3.3 Participants and roles

Possible session roles include:

- seminar participant;
- peer observer;
- discussion mapper;
- student facilitator;
- group recorder;
- teacher observer; and
- absent or excused participant.

Roles are contextual assignments, not permanent student attributes.

## 4. Packet Composition

The baseline packet contains five Concord artifact types and one optional external reference.

```text
Socratic Seminar Packet
├── A. Peer Observation Sheet
├── B. Discussion Map
├── C. Teacher Observation Tracker
├── D. Group Process Review
├── E. Teacher Scoring Rubric
└── F. Optional Quillan Reflection Reference
```

### Required baseline artifacts

1. Peer Observation Sheet
2. Teacher Observation Tracker
3. Teacher Scoring Rubric

### Recommended artifacts

4. Discussion Map
5. Group Process Review

### External optional work

6. Quillan Reflection Reference

The Quillan reflection is not a Concord artifact and is not included as a Concord writing-response page.

## 5. Artifact Inventory

| Artifact | Primary author | Primary subject | Scope | Scanned | Scored directly | Moderation |
|---|---|---|---|---|---|---|
| Peer Observation Sheet | Student observer | One student participant | Individual | Yes | No, by default | Required before consequential use |
| Discussion Map | Student observer or mapper | Seminar group and session | Group/session | Yes | Usually no | Teacher review |
| Teacher Observation Tracker | Teacher | Several students or one group | Multi-subject | Yes | No, evidence source | Teacher-authored |
| Group Process Review | Group recorder or group consensus | Seminar group and session | Group | Yes | Optional | Teacher review |
| Teacher Scoring Rubric | Teacher | One student or one group | Individual or group | Yes or digitally entered | Yes | Final teacher judgment |
| Quillan Reflection | Student | Self | Individual | Quillan workflow | Quillan workflow | Quillan workflow |

## 6. Artifact A: Peer Observation Sheet

### 6.1 Purpose

The Peer Observation Sheet captures evidence that the teacher may not directly observe while attending to the entire seminar.

It should focus on concrete discussion behavior rather than general personality judgments.

### 6.2 Author and subject

- **Author:** one student observer;
- **Subject:** one student seminar participant;
- **Context:** one seminar group and one session.

The observer and subject must remain distinct in the data model.

### 6.3 Suggested paper structure

A single-subject page is preferred for the baseline model.

Possible sections:

- observer identification;
- observed student identification;
- activity and session label;
- selected observation criteria;
- brief evidence boxes;
- one concise commendation;
- one concise next step;
- `not observed`;
- `insufficient evidence`; and
- teacher review area.

The page should not use bubbles or machine-readable rating fields. If a teacher wants OMR-based peer ratings, that belongs to ScoreForm.

### 6.4 Candidate observation criteria

The teacher should choose a small subset, such as:

- advances a relevant idea;
- supports a claim with evidence;
- asks a productive question;
- responds to another speaker's idea;
- clarifies or synthesizes;
- revises or qualifies thinking;
- helps include other participants; and
- listens in a way demonstrated by a substantive response.

### 6.5 Review and moderation

Peer observations should be treated as evidence, not final scores.

Before they affect a consequential score, the teacher should be able to mark the artifact as:

- accepted;
- accepted with qualification;
- insufficient;
- disputed;
- rejected; or
- not used for scoring.

### 6.6 Privacy

Default visibility should be restricted to the teacher.

A teacher may later share selected feedback with the observed student, but Concord should not assume that the peer observer's identity or full handwritten comments are automatically disclosed.

### 6.7 Contract implications

This artifact requires:

- one artifact author;
- one artifact subject;
- both author and subject as student references;
- a session role for the author;
- criterion references;
- moderation status;
- privacy classification; and
- a clear distinction between raw peer evidence and teacher-approved score data.

## 7. Artifact B: Discussion Map

### 7.1 Purpose

The Discussion Map documents how ideas moved through the seminar.

It is a collaborative graphic organizer, not a transcript.

### 7.2 Author and subject

- **Author:** one student discussion mapper, several mappers, or a teacher;
- **Subject:** the seminar group and session;
- **Scope:** group-level.

### 7.3 Suggested paper structure

The page may contain:

- participant names or initials positioned around a circle;
- arrows connecting responses;
- short notes identifying claims, questions, challenges, or syntheses;
- a central seminar question;
- a legend for teacher-selected discussion moves;
- a space for major ideas that emerged; and
- a space for unresolved questions.

The mapper writes or draws directly on the page. Concord files the scan but does not interpret the markings.

### 7.4 Scoring use

The map should usually function as supporting evidence rather than as a directly scored artifact.

It may support teacher judgments about:

- responsiveness;
- distribution of discussion;
- development of ideas;
- synthesis;
- facilitation; and
- group-level discussion quality.

It should not be used to infer that silence automatically means disengagement.

### 7.5 Privacy

The map may be visible to the class if it contains only names, initials, and academic discussion evidence. The teacher should still be able to classify it as restricted when necessary.

### 7.6 Contract implications

This artifact requires:

- group-level subject support;
- session-level context;
- optional multiple authors;
- no required student subject;
- artifact-level privacy;
- optional links to several later scores; and
- QR routing that does not require one `student_id`.

## 8. Artifact C: Teacher Observation Tracker

### 8.1 Purpose

The Teacher Observation Tracker gives the teacher a low-friction paper interface for recording targeted evidence during the seminar.

It should not require the teacher to complete a full rubric while facilitating the activity.

### 8.2 Author and subject

- **Author:** teacher;
- **Subjects:** several students, one seminar group, or both;
- **Scope:** multi-subject.

### 8.3 Suggested paper structure

A roster-style grid may include:

- student names;
- selected criteria;
- short note cells;
- observation timestamps or rotation numbers;
- `observed`;
- `not observed`;
- `follow up`;
- `insufficient evidence`; and
- group-level notes.

The form should minimize writing burden and allow brief annotations.

### 8.4 Scoring use

The tracker is an evidence source, not necessarily the final scoring form.

A teacher may later consult it while completing individual scoring rubrics.

### 8.5 Important distinction

The tracker must distinguish:

- not observed;
- not demonstrated;
- absent;
- excused;
- insufficient evidence; and
- not applicable.

A blank cell must not automatically mean poor performance.

### 8.6 Contract implications

This artifact exposes a major modeling requirement:

> One Concord artifact may concern several student subjects.

The data model therefore cannot assume that every artifact has exactly one subject.

Possible representations include:

- one artifact with a list of subjects;
- one artifact with group scope and embedded subject references;
- one scan linked to several evidence records; or
- derived teacher evidence entries that reference regions of one source artifact.

The contract phase must select one approach without requiring handwriting-region extraction.

## 9. Artifact D: Group Process Review

### 9.1 Purpose

The Group Process Review captures a concise group-level evaluation of how the seminar functioned.

It is not an extended written reflection.

### 9.2 Author and subject

- **Author:** one recorder acting for the group, several named contributors, or the group by consensus;
- **Subject:** seminar group and session;
- **Scope:** group.

### 9.3 Suggested paper structure

A structured one-page form may include:

- one process strength;
- one discussion move the group used effectively;
- one barrier or missed opportunity;
- one adjustment for the next seminar;
- consensus status;
- unresolved disagreement; and
- recorder identification.

The form may use compact tables, check areas, or graphic organizers, but it should not become an essay prompt.

### 9.4 Consensus status

The artifact should indicate whether the response represents:

- unanimous agreement;
- majority agreement;
- recorder summary;
- several individual views; or
- no consensus.

### 9.5 Scoring use

Possible uses include:

- formative group feedback;
- evidence for a group-process criterion;
- planning the next seminar cycle; or
- identifying a need for teacher intervention.

It should not automatically produce an individual score for every group member.

### 9.6 Contract implications

This artifact requires:

- group-level subject;
- one or multiple authors;
- a declared authorship mode;
- consensus status;
- optional group score linkage; and
- session-specific group membership.

## 10. Artifact E: Teacher Scoring Rubric

### 10.1 Purpose

The Teacher Scoring Rubric records the teacher's final criterion-level judgment after reviewing available evidence.

It separates scoring from evidence collection.

### 10.2 Author and subject

- **Author/scorer:** teacher;
- **Subject:** one student or one group;
- **Scope:** individual or group.

### 10.3 Suggested paper structure

Possible sections:

- student or group identification;
- selected criteria;
- teacher-defined scoring scale;
- score per criterion;
- evidence-source references;
- insufficient-evidence option;
- brief rationale or note;
- date and scorer;
- moderation complete;
- revised or superseding score reference.

### 10.4 Evidence sources

A score may reference:

- teacher observation tracker;
- one or more peer observation sheets;
- discussion map;
- group process review;
- related ScoreForm result;
- related Quillan response;
- another external artifact; or
- teacher professional judgment.

Concord should preserve those references rather than flattening everything into one number.

### 10.5 Score is not grade

The scoring rubric may generate:

- criterion scores;
- an individual seminar component score;
- a group-process score; or
- an activity outcome score.

It does not calculate the student's marking-period or course grade.

### 10.6 Paper versus digital entry

The first implementation may support either:

1. a printable scoring rubric that is later scanned and filed; or
2. a teacher scoring interface completed while viewing the scanned evidence.

Both should produce the same conceptual score record.

## 11. External Reference F: Quillan Reflection

A teacher may assign an individual seminar reflection such as:

- explain how your thinking changed;
- evaluate one claim from the discussion;
- defend or revise your initial position;
- analyze how the group used evidence; or
- identify the most important unresolved question.

That work belongs to Quillan.

Concord may store:

- the Quillan assignment ID;
- the purpose of the relationship;
- whether the reflection is required;
- whether the Quillan result may inform Concord scoring; and
- which Concord activity or session it follows.

Concord should not generate or evaluate the extended written response.

## 12. Packet Generation Model

### 12.1 Teacher configuration

The teacher supplies:

- class;
- activity ID;
- activity title;
- seminar date;
- session;
- seminar groups;
- participant roles;
- selected Concord templates;
- selected criteria;
- privacy settings;
- scoring scale;
- optional standards profile and standard IDs;
- optional ScoreForm reference; and
- optional Quillan reference.

This is packet configuration, not lesson planning.

### 12.2 Generated artifact instances

For one seminar group of eight participants and eight observers, Concord might generate:

- eight Peer Observation Sheets;
- one Discussion Map;
- one Group Process Review;
- one Teacher Observation Tracker section or page;
- eight individual Teacher Scoring Rubrics; and
- optional external-reference pages or instructions.

Each scannable page receives:

- one Concord artifact instance ID;
- one page-level QR code;
- one human-readable fallback code;
- template ID and version;
- activity and session context; and
- appropriate author or subject labels.

## 13. QR and Routing Requirements

### 13.1 Shared Core contract

Concord must use the PDS Core `PDS1` contract.

The current shared contract will need extension before implementation because Socratic seminar artifacts include:

- one student author and one different student subject;
- one group subject with no student subject;
- multiple student subjects on one teacher tracker;
- teacher-authored artifacts;
- group-authored artifacts; and
- pages tied primarily to a session.

### 13.2 Required routing concepts

The shared or linked record must be able to resolve:

- module;
- class;
- activity or assignment-routing ID;
- session;
- artifact instance;
- template and version;
- document type;
- page number;
- packet instance;
- author identity or author mode;
- subject identity or subject scope;
- group, when applicable; and
- privacy classification.

### 13.3 Avoided workarounds

Concord must not:

- place a group ID into `student_id`;
- create synthetic student records for groups;
- treat the observer as the observed student;
- omit provenance because the page is group-level; or
- create a Concord-only QR grammar.

## 14. Scan and Filing Workflow

### 14.1 Intake

The teacher scans:

- individual pages;
- one group's packet;
- the entire class packet; or
- a mixed batch.

PDS Core retains the readable source scan and its provenance before Concord-specific processing.

### 14.2 Concord processing

Concord:

- extracts page images if necessary;
- reads page QR codes;
- identifies artifact instances;
- routes pages to the correct activity and session;
- creates routed evidence references;
- flags unmatched or conflicting pages; and
- presents filed scans for teacher review.

Concord does not interpret the handwriting.

### 14.3 Suggested routed organization

The final path contract is not yet decided, but the conceptual organization must support:

```text
activity
└── session
    ├── groups
    ├── artifacts
    ├── reviews
    └── scores
```

PDS Core should continue to own canonical workspace and assignment path rules.

## 15. Review Workflow

The teacher reviews each artifact or artifact batch for:

- correct class;
- correct activity and session;
- correct author;
- correct subject;
- correct group;
- scan readability;
- page completeness;
- privacy;
- moderation need; and
- scoring readiness.

### 15.1 Peer evidence review

The teacher may:

- accept;
- qualify;
- reject;
- dispute;
- mark insufficient; or
- exclude from scoring.

### 15.2 Multi-subject tracker review

The teacher confirms that the roster and session membership match the page.

Concord should not attempt to extract handwritten notes for individual students automatically.

### 15.3 Missing or conflicting evidence

Examples include:

- observer completed the wrong target's form;
- participant changed groups;
- duplicate peer observation;
- missing group review;
- unreadable page;
- QR damaged;
- page scanned under the wrong session;
- absent student;
- no observer assigned; and
- student joined after the seminar began.

These conditions should be correctable without altering the retained source scan.

## 16. Scoring Model

### 16.1 Individual criteria

Possible individual score targets:

- substantive contribution;
- reasoning and evidence;
- questioning;
- responsiveness;
- listening demonstrated through response;
- synthesis;
- facilitation; and
- revision of thinking.

### 16.2 Group criteria

Possible group score targets:

- collective use of evidence;
- development of ideas;
- equitable opportunity to contribute;
- responsiveness across members;
- synthesis or conclusion;
- process improvement; and
- quality of collaborative norms.

### 16.3 Evidence-to-score relationship

A score may have:

- one source artifact;
- several source artifacts;
- no single source artifact but a teacher note;
- accepted peer evidence;
- group-level evidence;
- an external ScoreForm or Quillan reference; and
- a rationale.

No automatic weighting formula is required.

### 16.4 Missing evidence

The scoring interface must allow:

- insufficient evidence;
- absent;
- excused;
- not applicable;
- not observed; and
- deferred.

These should remain distinct from a low score.

## 17. Privacy Model

| Artifact | Default privacy |
|---|---|
| Peer Observation Sheet | Teacher-restricted |
| Discussion Map | Class-limited or teacher-restricted |
| Teacher Observation Tracker | Teacher-restricted |
| Group Process Review | Group-and-teacher or teacher-restricted |
| Teacher Scoring Rubric | Teacher and scored subject |
| Quillan Reflection Reference | Governed by Quillan |

Peer observer identity should not automatically be disclosed to the subject.

A public classroom display of discussion patterns should use a separate teacher-selected output, not the raw peer or teacher artifacts.

## 18. Exception Cases

The contracts must support:

### 18.1 Absence

An absent student may have:

- no participant artifact;
- no peer observation;
- no score;
- an excused status; or
- a later alternate activity.

### 18.2 Role change

A student may move from observer to participant within the same session.

Role assignments therefore need effective sequence or time context.

### 18.3 Group change

A student may move between seminar groups.

Group membership must be session-specific and should support changes without rewriting earlier records.

### 18.4 Missing observer evidence

A peer observation may be missing without implying that the participant failed to demonstrate the criterion.

### 18.5 Conflicting evidence

Teacher and peer evidence may disagree.

Concord preserves both and records the teacher's moderation decision.

### 18.6 One page, several subjects

The teacher tracker may concern the entire roster.

The contract must support multi-subject evidence without pretending the artifact belongs to one student.

### 18.7 One subject, several authors

A group review may have several contributors or a recorder acting for the group.

The contract must distinguish individual authorship from group-representative authorship.

### 18.8 Rescan or correction

A replacement scan may supersede a poor scan while retaining provenance and history.

## 19. Contract Requirements Discovered

This representative packet requires the future contracts to support:

1. activities with one or more sessions;
2. session-specific groups;
3. session-specific participant roles;
4. reusable template definitions;
5. generated packet instances;
6. generated artifact instances;
7. page-level QR identification;
8. artifact authors distinct from artifact subjects;
9. individual, group, session, activity, and multi-subject scopes;
10. multiple authors or group-representative authorship;
11. multiple subjects on one source artifact;
12. template and packet versioning;
13. privacy classifications;
14. retained source-scan provenance through PDS Core;
15. routed Concord evidence;
16. review states;
17. peer-evidence moderation;
18. criterion definitions and selected criterion sets;
19. teacher-defined scoring scales;
20. individual and group score targets;
21. many-to-many relationships between scores and evidence artifacts;
22. external ScoreForm and Quillan references;
23. missing, absent, excused, not observed, and insufficient-evidence states;
24. corrections, rescans, and superseding records;
25. durable standards references through PDS Core; and
26. a PDS Core QR extension for Concord and non-student artifact subjects.

## 20. Decisions Supported by This Model

The Socratic seminar case supports these design decisions:

1. Concord packets should be composable rather than universal.
2. Peer observations should be single-subject artifacts in the baseline design.
3. Peer evidence should not automatically become a score.
4. Teacher observation artifacts may be multi-subject.
5. Group artifacts must not require a student subject.
6. Group membership and roles belong to sessions.
7. Discussion maps are evidence artifacts, not transcripts.
8. Extended written seminar reflections belong to Quillan.
9. OMR-based seminar instruments belong to ScoreForm.
10. Scores may cite several Concord and external evidence sources.
11. Missing evidence must not become a low score by default.
12. The current PDS Core QR contract requires deliberate extension before Concord implementation.

## 21. Open Questions

1. Should the teacher scoring rubric be a scanned paper artifact, a digital review form, or support both equally?
2. Should one Peer Observation Sheet always concern one subject, or should an optional compact multi-student version exist?
3. How should multi-subject teacher tracker evidence link to later individual scores without handwriting-region extraction?
4. What should PDS Core call the QR field for a Concord artifact instance?
5. Should Core's `assignment_id` serve as Concord's activity-routing ID?
6. Which group and session identifiers belong in the QR payload versus the linked local record?
7. How should group-representative authorship be encoded?
8. Should students ever see the full peer artifact, a teacher-selected excerpt, or only synthesized feedback?
9. Which privacy values should be shared across PDS modules?
10. Which seminar criteria should ship as optional Concord starter templates?
11. Should discussion maps support named students, initials, numbered seats, or teacher-selected anonymity?
12. How should simultaneous small seminars be represented when one teacher tracker spans several groups?

## 22. Next Cross-Case Test

This packet model should next be compared with:

1. a science laboratory group packet; and
2. a collaborative programming or engineering project packet.

The comparison should identify which requirements are:

- universal across Concord;
- common but optional;
- specific to discussion-centered activities; or
- better owned by PDS Core, ScoreForm, Quillan, or a future module.
