# Cross-Case Requirements Matrix

**Status:** Draft for domain-model design
**Project:** Paper Data Suite
**Module:** `pds-concord`
**Issue:** #7
**Date:** July 13, 2026

## 1. Purpose

This document compares the three representative Concord packet models:

* [Socratic Seminar Packet Model](../packet_models/socratic-seminar-packet-model.md);
* [Science Laboratory Group Packet Model](../packet_models/science-laboratory-group-packet-model.md); and
* [Collaborative Programming or Engineering Project Packet Model](../packet_models/collaborative-programming_engineering_project_packet_model.md).

The comparison identifies which concepts belong in Concord’s shared foundation and which should remain optional, activity-specific, unresolved, or owned by another Paper Data Suite module.

This document refines the [Concord Conceptual Design](../concord-conceptual-design-revised.md). It does not define final JSON contracts, schemas, classes, database tables, or filesystem paths.

## 2. Classification Method

The classification describes the level of support Concord needs, not whether every packet must use the feature.

| Classification                                   | Meaning                                                                                                                           |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| **Universal Concord requirement**                | The foundational model or workflow must support it across activity types.                                                         |
| **Common optional capability**                   | A reusable Concord capability needed by multiple activity types but not required in every activity.                               |
| **Activity-specific extension**                  | A concept that should normally remain in a template, artifact subtype, or activity-specific extension rather than the base model. |
| **Owned by another PDS module**                  | The capability belongs to Core, ScoreForm, Quillan, or a future PDS module. Concord may reference it but should not duplicate it. |
| **External institutional/system responsibility** | The capability belongs outside Paper Data Suite or in an existing institutional or technical system.                              |
| **Unresolved**                                   | The requirement is established, but its exact representation or ownership still requires a design decision.                       |

Case-column terms:

* **Central:** a defining part of the packet;
* **Present:** directly represented;
* **Possible:** supported or anticipated but not central;
* **Limited:** only a narrow form appears;
* **External:** deliberately delegated elsewhere.

## 3. Executive Conclusions

The three cases support a common Concord foundation centered on:

1. activities and sessions;
2. session-contextual groups, memberships, and roles;
3. reusable, versioned templates assembled into composable packets;
4. generated artifact instances with stable page identity;
5. authorship and subject relationships with flexible cardinality;
6. retained paper evidence and provenance;
7. human review and conditional moderation;
8. criteria, scoring scales, and score records;
9. many-to-many relationships between evidence and scores;
10. privacy, exception, correction, and supersession states; and
11. references to work owned by other PDS modules.

The comparison does **not** support making milestones, subteams, tasks, dependencies, trials, components, handoffs, or version labels mandatory for every Concord activity. These are recurring optional contexts that should be available without defining the base model around project-management or laboratory terminology.

## 4. Cross-Case Matrix

### 4.1 Activity and Collaboration Context

| Requirement                                  | Seminar  | Laboratory | Project  | Classification                | Likely owner or treatment                               |
| -------------------------------------------- | -------- | ---------- | -------- | ----------------------------- | ------------------------------------------------------- |
| Activity                                     | Central  | Central    | Central  | Universal Concord requirement | Concord first-class concept                             |
| One or more sessions per activity            | Present  | Present    | Central  | Universal Concord requirement | Concord first-class concept                             |
| Multi-session chronology                     | Possible | Present    | Central  | Universal Concord requirement | Concord must preserve ordered session context when used |
| Collaborative group                          | Central  | Central    | Central  | Universal Concord requirement | Concord activity-specific group                         |
| Session-contextual group membership          | Central  | Central    | Central  | Universal Concord requirement | Concord membership record; class roster remains in Core |
| Membership changes without rewriting history | Possible | Present    | Present  | Universal Concord requirement | Effective context and preserved history                 |
| Contextual participant roles                 | Central  | Present    | Present  | Universal Concord requirement | Concord role assignment                                 |
| Direct responsibility assignment             | Limited  | Central    | Central  | Common optional capability    | Concord responsibility assignment                       |
| Role or responsibility rotation/reassignment | Possible | Central    | Central  | Common optional capability    | Preserve original and revised assignments               |
| Stage or phase context                       | Limited  | Central    | Present  | Common optional capability    | Optional named context, not mandatory hierarchy         |
| Milestone or checkpoint                      | Rare     | Possible   | Central  | Common optional capability    | Optional Concord context record                         |
| Temporary subteam                            | Rare     | Possible   | Central  | Common optional capability    | Likely bounded child group; exact model unresolved      |
| Task or component reference                  | Limited  | Possible   | Central  | Common optional capability    | Optional activity context                               |
| Task dependency                              | Limited  | Possible   | Central  | Common optional capability    | Optional project/workflow extension                     |
| Handoff between participants or subteams     | Limited  | Possible   | Central  | Common optional capability    | Optional typed event or relationship                    |
| Trial, build, version, or iteration label    | Limited  | Central    | Central  | Common optional capability    | Human-entered context label; not source control         |
| Equipment or environmental context           | Rare     | Central    | Possible | Activity-specific extension   | Laboratory or material-work templates                   |
| Discussion structure or rotation             | Central  | Rare       | Rare     | Activity-specific extension   | Seminar packet/template configuration                   |

### 4.2 Packet, Template, and Artifact Model

| Requirement                                | Seminar  | Laboratory | Project  | Classification                               | Likely owner or treatment                                   |
| ------------------------------------------ | -------- | ---------- | -------- | -------------------------------------------- | ----------------------------------------------------------- |
| Composable packet definition               | Central  | Central    | Central  | Universal Concord requirement                | Concord first-class concept                                 |
| Generated packet instance                  | Central  | Central    | Central  | Universal Concord requirement                | Concord first-class concept                                 |
| Reusable template definition               | Central  | Central    | Central  | Universal Concord requirement                | Concord first-class concept                                 |
| Immutable template version reference       | Present  | Present    | Present  | Universal Concord requirement                | Concord first-class concept                                 |
| Generated artifact instance                | Central  | Central    | Central  | Universal Concord requirement                | Concord first-class concept                                 |
| Stable artifact identifier                 | Central  | Central    | Central  | Universal Concord requirement                | Concord ID validated through Core conventions               |
| Page-level identity                        | Central  | Central    | Central  | Universal Concord requirement                | Shared Core QR contract plus Concord artifact record        |
| Human-readable fallback identifier         | Present  | Present    | Present  | Universal Concord requirement                | Concord generation using shared identifier rules            |
| Page number and multi-page relationship    | Present  | Central    | Central  | Universal Concord requirement                | Artifact-page or page-manifest support                      |
| Continuation pages                         | Possible | Central    | Central  | Common optional capability                   | Preserve sequence and logical artifact relationship         |
| Structured Concord artifact                | Central  | Central    | Central  | Universal Concord requirement                | Concord-generated evidence artifact                         |
| Attached physical or digital work          | Possible | Central    | Central  | Common optional capability                   | Concord attachment/external-artifact relationship           |
| Artifact cover sheet or QR label           | Possible | Central    | Central  | Common optional capability                   | Concord routing aid                                         |
| Non-returned instructional scaffold        | Possible | Possible   | Possible | Common optional capability                   | Template declares whether evidence is expected back         |
| Activity-specific artifact subtype         | Central  | Central    | Central  | Universal Concord requirement                | Template taxonomy, not separate core schemas for every form |
| Subject-specific worksheet or project file | External | External   | External | External institutional/system responsibility | Referenced or attached; not reimplemented by Concord        |

### 4.3 Authorship, Subjects, and Contribution

| Requirement                                                          | Seminar  | Laboratory | Project | Classification                | Likely owner or treatment                                  |
| -------------------------------------------------------------------- | -------- | ---------- | ------- | ----------------------------- | ---------------------------------------------------------- |
| Artifact author distinct from artifact subject                       | Central  | Present    | Central | Universal Concord requirement | Separate relationships                                     |
| Zero, one, or several student subjects                               | Central  | Central    | Central | Universal Concord requirement | Flexible subject cardinality                               |
| Individual, group, session, activity, or multi-subject scope         | Central  | Central    | Central | Universal Concord requirement | Typed subject references                                   |
| One or several authors                                               | Present  | Central    | Central | Universal Concord requirement | Flexible author cardinality                                |
| Group-representative authorship                                      | Central  | Central    | Central | Universal Concord requirement | Authorship mode plus recorder identity when applicable     |
| Teacher-authored evidence                                            | Central  | Central    | Central | Universal Concord requirement | Authorized non-student author                              |
| Recorder or physical writer not treated as sole contributor          | Possible | Central    | Central | Universal Concord requirement | Explicit contributor/authorship semantics                  |
| Digital account or file ownership not treated as sole authorship     | Rare     | Rare       | Central | Universal Concord rule        | No automatic authorship inference                          |
| Assigned role/responsibility distinct from demonstrated contribution | Present  | Central    | Central | Universal Concord requirement | Evidence must remain separate from assignment              |
| Contribution type or category                                        | Limited  | Central    | Central | Common optional capability    | Configurable taxonomy; do not privilege visible production |
| Contribution claim                                                   | Limited  | Possible   | Central | Common optional capability    | Student/group evidence requiring review                    |
| Conflicting contribution claims                                      | Possible | Possible   | Central | Common optional capability    | Moderation workflow                                        |
| Consensus or authorship representation status                        | Central  | Central    | Central | Common optional capability    | Useful for group reviews and retrospectives                |
| Subteam, task, event, component, or external artifact as subject     | Rare     | Possible   | Central | Common optional capability    | Extend typed subject/context references                    |

### 4.4 Evidence, Review, Moderation, and Privacy

| Requirement                                                           | Seminar  | Laboratory | Project  | Classification                | Likely owner or treatment                            |
| --------------------------------------------------------------------- | -------- | ---------- | -------- | ----------------------------- | ---------------------------------------------------- |
| Scanned paper remains canonical evidence                              | Central  | Central    | Central  | Universal Concord requirement | Core retains source; Concord links routed evidence   |
| Source-scan provenance                                                | Central  | Central    | Central  | Owned by another PDS module   | Core retention and provenance contract               |
| Concord-specific identification and filing                            | Central  | Central    | Central  | Universal Concord requirement | Concord processing using Core contracts              |
| Mixed-batch and multi-page intake                                     | Present  | Present    | Present  | Universal Concord requirement | Core intake retention; Concord page processing       |
| Human review before consequential use                                 | Central  | Central    | Central  | Universal Concord requirement | Concord review record/workflow                       |
| Filing-metadata correction without altering source                    | Central  | Central    | Central  | Universal Concord requirement | Concord review plus Core provenance                  |
| Moderation of student-created evidence                                | Central  | Possible   | Present  | Universal Concord capability  | Invoked conditionally by evidence type               |
| Peer observation                                                      | Central  | Optional   | Possible | Common optional capability    | Concord artifact type with moderation                |
| Multi-subject teacher observation tracker                             | Central  | Central    | Central  | Universal Concord requirement | One source may support several subjects and scores   |
| Teacher support/intervention reference                                | Possible | Central    | Central  | Common optional capability    | Evidence context, not automatic performance judgment |
| Artifact-level privacy classification                                 | Central  | Central    | Central  | Universal Concord requirement | Concord use; shared vocabulary ownership unresolved  |
| More restrictive privacy for disputes and teacher notes               | Present  | Present    | Present  | Universal Concord requirement | Record-specific override                             |
| Missing, unreadable, duplicate, conflicting, or misrouted page states | Central  | Central    | Central  | Universal Concord requirement | Review and correction workflow                       |
| Rescan, correction, replacement, or supersession                      | Central  | Central    | Central  | Universal Concord requirement | Preserve history and source provenance               |
| Chronology of revised decisions or evidence                           | Possible | Central    | Central  | Universal Concord requirement | Supersession must not erase earlier records          |
| Handwriting, diagram, or digital-content interpretation               | Excluded | Excluded   | Excluded | External/out of scope         | Human interpretation only                            |

### 4.5 Criteria, Scores, and Exceptional States

| Requirement                                                                           | Seminar  | Laboratory | Project  | Classification                | Likely owner or treatment                                           |
| ------------------------------------------------------------------------------------- | -------- | ---------- | -------- | ----------------------------- | ------------------------------------------------------------------- |
| Criterion definitions and selected criterion sets                                     | Central  | Central    | Central  | Universal Concord requirement | Concord first-class concepts                                        |
| Teacher-defined scoring scale                                                         | Central  | Central    | Central  | Universal Concord requirement | Concord first-class concept                                         |
| Criterion-level score record                                                          | Central  | Central    | Central  | Universal Concord requirement | Concord first-class concept                                         |
| Individual score target                                                               | Central  | Central    | Central  | Universal Concord requirement | Concord score subject                                               |
| Group score target                                                                    | Central  | Central    | Central  | Universal Concord requirement | Concord score subject                                               |
| Subteam score target                                                                  | Rare     | Rare       | Present  | Common optional capability    | Optional score subject                                              |
| One score supported by several evidence sources                                       | Central  | Central    | Central  | Universal Concord requirement | Many-to-many evidence links                                         |
| One artifact supporting several scores                                                | Central  | Central    | Central  | Universal Concord requirement | Many-to-many evidence links                                         |
| External ScoreForm or Quillan evidence reference                                      | Present  | Present    | Present  | Universal Concord requirement | Shared cross-module reference contract                              |
| Teacher judgment without one controlling artifact                                     | Present  | Present    | Present  | Universal Concord requirement | Record rationale/provenance                                         |
| Review or moderation distinct from scoring                                            | Central  | Central    | Central  | Universal Concord requirement | Separate records and states                                         |
| Score distinct from course grade                                                      | Central  | Central    | Central  | Owned by another PDS module   | Future gradebook/reporting module owns grade calculation            |
| Group evidence not automatically propagated to individual scores                      | Central  | Central    | Central  | Universal Concord rule        | Requires explicit teacher judgment                                  |
| Missing evidence distinct from negative evidence                                      | Central  | Central    | Central  | Universal Concord requirement | Explicit non-score states                                           |
| Absent, excused, not observed, insufficient evidence, not applicable, deferred        | Central  | Central    | Central  | Universal Concord requirement | Shared status vocabulary                                            |
| Blocked, interrupted, equipment failure, dependency failure, or external tool failure | Possible | Central    | Central  | Common optional capability    | Contextual exception reasons, not low scores                        |
| Automated behavioral scoring or inferred engagement                                   | Excluded | Excluded   | Excluded | External/out of scope         | Prohibited Concord behavior                                         |
| Paper scoring form and digital score entry producing same conceptual record           | Possible | Possible   | Possible | Unresolved                    | Interaction design decision; contract should remain surface-neutral |

### 4.6 Module and System Ownership

| Capability                                                                                     | Seminar  | Laboratory | Project  | Classification                               | Owner                             |
| ---------------------------------------------------------------------------------------------- | -------- | ---------- | -------- | -------------------------------------------- | --------------------------------- |
| Workspace root and canonical shared paths                                                      | Required | Required   | Required | Owned by another PDS module                  | `pds-core`                        |
| Durable class, roster, and student identity                                                    | Required | Required   | Required | Owned by another PDS module                  | `pds-core`                        |
| Shared identifier validation and safe paths                                                    | Required | Required   | Required | Owned by another PDS module                  | `pds-core`                        |
| Shared `PDS1` QR construction, parsing, and routing contract                                   | Required | Required   | Required | Owned by another PDS module                  | `pds-core`                        |
| Source-scan retention and shared provenance                                                    | Required | Required   | Required | Owned by another PDS module                  | `pds-core`                        |
| Shared routing failure/resolution metadata                                                     | Required | Required   | Required | Owned by another PDS module                  | `pds-core`                        |
| Standards library, profiles, and durable standards IDs                                         | Optional | Optional   | Optional | Owned by another PDS module                  | `pds-core`                        |
| Activity-specific groups, sessions, roles, packets, artifacts, review, moderation, and scoring | Required | Required   | Required | Universal Concord requirement                | `pds-concord`                     |
| OMR and machine-readable checks                                                                | External | External   | External | Owned by another PDS module                  | `pds-scoreform`                   |
| Focused or extended written responses                                                          | External | External   | External | Owned by another PDS module                  | `pds-quillan`                     |
| Objectives, instructional sequence, materials, timing, and lesson plans                        | External | External   | External | Owned by another PDS module                  | Future lesson-planning module     |
| Course grades, weighting, reporting, and parent-facing output                                  | External | External   | External | Owned by another PDS module                  | Future gradebook/reporting module |
| Formal safety, medical, disciplinary, or incident record                                       | Rare     | Possible   | Possible | External institutional/system responsibility | School or district system         |
| Source control, repository history, CAD/project-file management, and digital edit history      | Rare     | Rare       | Central  | External institutional/system responsibility | Existing technical systems        |

## 5. Universal Concord Requirements

The following should be treated as foundation-level requirements for the initial domain model:

* activity and session identity;
* activity-specific groups and session-contextual membership;
* contextual role assignment;
* composable packet definitions and generated packet instances;
* reusable templates with immutable version references;
* stable artifact and page identity;
* flexible artifact author and subject relationships;
* individual, group, session, activity, and multi-subject scope;
* structured Concord artifacts and their scans;
* source provenance through Core;
* human review, metadata correction, and scoring readiness;
* conditional moderation of peer, disputed, or student-created evidence;
* artifact-level privacy;
* criteria, criterion sets, scoring scales, and score records;
* many-to-many evidence-to-score relationships;
* individual and group score targets;
* explicit non-score and exception states;
* corrections, rescans, revisions, and superseding records that preserve history; and
* cross-module references to ScoreForm, Quillan, Core standards, and future systems.

A universal capability does not imply that every packet must instantiate it. For example, moderation must exist in the foundational model even though many teacher-authored artifacts will not need a separate moderation step.

## 6. Common Optional Capabilities

These capabilities recur across multiple cases and should be supported without becoming mandatory parts of every activity:

* responsibility assignments separate from roles;
* activity stages or phases;
* milestones or checkpoints;
* temporary subteams;
* tasks and components;
* dependencies and handoffs;
* trial, build, version, or iteration labels;
* typed events for decisions, troubleshooting, testing, revision, and handoff;
* role and responsibility reassignment;
* contribution categories and contribution claims;
* group consensus or representation status;
* teacher assistance or intervention references;
* external artifact attachments and cover sheets;
* continuation pages and long-lived logs;
* subteam score targets; and
* contextual exception reasons such as equipment failure, interrupted work, or dependency blockage.

These features should be optional records or extensions around the universal activity-artifact-evidence model. Concord should not become a general project-management application merely because it can document tasks, milestones, or dependencies.

## 7. Activity-Specific Extensions

The following concepts should normally remain in templates, artifact subtypes, configurable vocabularies, or activity-specific metadata.

### Seminar-specific

* inner-circle and outer-circle rotations;
* discussion moves;
* speaker-response maps;
* observer-target pairings;
* seminar prompts and text references; and
* discussion-map legends.

### Laboratory-specific

* trial numbering;
* apparatus, material, or sample references;
* measurement-table layouts;
* invalid-trial reasons;
* routine safety prompts; and
* laboratory-specific procedure or data organizers.

### Programming or engineering project-specific

* build, prototype, or release labels;
* software test-case fields;
* regression or severity labels;
* component-integration terminology;
* repository or project-file locations; and
* domain-specific design-review fields.

The base model may provide generic context references, but it should not encode subject-specific vocabulary as mandatory fields.

## 8. Consolidated Ownership Boundaries

### 8.1 Concord owns

* packet, template, artifact, review, moderation, criterion, and score contracts;
* activity-specific sessions, groups, memberships, roles, and optional responsibilities;
* artifact authorship and subject relationships;
* Concord artifact layouts and packet manifests;
* Concord-specific QR extraction, page splitting, filing, and review interfaces;
* routed Concord evidence and result records;
* privacy use within Concord; and
* score entry and evidence linkage.

### 8.2 Core owns

* workspace resolution;
* canonical class, roster, assignment-route, and student identity conventions;
* identifier validation and safe path construction;
* the shared `PDS1` QR contract;
* source-scan retention and provenance;
* shared scan-routing failure and resolution metadata;
* standards libraries and durable standards/profile IDs;
* shared navigation and local file-opening behavior.

Core must eventually register `module=concord` and support artifact routing that does not require one student subject.

### 8.3 ScoreForm owns

* OMR;
* bubble ratings;
* machine-readable checklists;
* structured accountability checks; and
* ScoreForm result processing.

### 8.4 Quillan owns

* extended reflection;
* focused written analysis;
* substantial peer feedback;
* written defense or explanation; and
* Quillan review and scoring workflows.

### 8.5 Future or external systems own

* lesson and unit planning;
* grade calculation and reporting;
* formal safety or disciplinary incidents;
* source control and commit attribution;
* CAD, engineering-file, or project-file management; and
* authoritative cloud-document histories.

## 9. Unresolved Design Questions

The comparison establishes the need for the following decisions but does not settle their final contract representation:

1. **Activity identity:** Does Concord’s `activity_id` map directly to Core’s current `assignment_id`, or is a separate Concord identifier linked to the canonical assignment route?
2. **QR subject model:** How should the shared `PDS1` contract represent pages with group, session, activity, event, artifact, or multi-subject scope and no required `student_id`?
3. **QR payload size:** Which context belongs in the QR payload and which should be resolved through the artifact-instance record?
4. **Multi-subject evidence:** Is a teacher tracker one artifact with many subjects, one scan with derived evidence entries, or both?
5. **Temporal precision:** Do membership, role, and responsibility changes require session, sequence, stage, or timestamp precision?
6. **Roles, responsibilities, tasks, and contributions:** These are semantically distinct, but which require first-class records in the initial contract set?
7. **Subteams:** Should a subteam be a group with a parent group and bounded lifespan, or a separate project-specific concept?
8. **Events:** Should decisions, troubleshooting incidents, tests, revisions, and handoffs share one typed activity-event envelope or use separate record types?
9. **Attachments:** Should scans, photographs, external files, and teacher-entered locations use one attachment model or several evidence-reference types?
10. **Privacy vocabulary:** Which privacy values should be shared by Core, and which should remain Concord-specific?
11. **Scoring surface:** Should paper rubrics, digital entry, or both be first-class workflows if they produce the same score contract?
12. **Individual scoring sufficiency:** Must an individual score cite at least one individual-specific evidence source, or may reviewed group evidence and teacher judgment be sufficient?
13. **Long-lived packets:** Should milestone or multi-session work use one packet instance with continuing artifacts or several linked packet instances?
14. **Starter taxonomies:** Which roles, criteria, contribution types, event types, and artifact templates should ship as defaults without becoming contract requirements?

## 10. Recommendations for the Initial Domain Model

Issue #8 should begin with the following likely first-class concepts:

* `activity`;
* `session`;
* `group`;
* `group_membership`;
* `role_assignment`;
* `packet_definition`;
* `packet_instance`;
* `template_definition`;
* `template_version`;
* `artifact_instance`;
* `artifact_page` or equivalent page manifest;
* `artifact_author` relationship;
* `artifact_subject` relationship;
* `scan_reference` or routed evidence reference;
* `artifact_review`;
* `moderation_record`;
* `criterion_set` and `criterion`;
* `scoring_scale`;
* `score_record`;
* `score_evidence_link`; and
* `external_reference`.

The following should be evaluated as optional first-class records or extensible context structures rather than assumed universal entities:

* `responsibility_assignment`;
* `activity_phase`;
* `milestone`;
* `subteam`;
* `task` or `component`;
* `activity_event`;
* `dependency`;
* `handoff`;
* `contribution_claim`; and
* `attachment`.

The contract work should preserve these invariants:

1. source evidence is never silently altered or replaced;
2. author and subject are never implicitly assumed to be the same;
3. recorder, handwriting, account ownership, or file ownership never establishes sole authorship automatically;
4. assignment of a role or responsibility never proves fulfillment or contribution;
5. a blank field or missing artifact never becomes a low score automatically;
6. group evidence or group scores never propagate to individual scores without an explicit teacher judgment;
7. evidence, review, moderation, score, grade, and report remain separate concepts; and
8. activity-specific vocabulary does not become mandatory base-schema vocabulary.

## 11. Updated Provisional Findings

* authors and subjects are separate relationships with independent cardinality;
* artifacts may have zero, one, or several student subjects and may instead concern a group, session, activity, event, component, or external artifact;
* physical writer, recorder, account owner, and file owner are not reliable proxies for sole authorship or contribution;
* activities, sessions, groups, memberships, and contextual roles belong in Concord’s shared foundation;
* roles, responsibilities, tasks, and contributions are distinct concepts, although not all must be mandatory records;
* responsibilities may change by stage, trial, milestone, or work period, and changes must preserve history;
* assigned responsibility is not evidence of fulfillment;
* peer evidence and disputed contribution claims require human moderation;
* teacher observation artifacts may span several students, groups, sessions, or contextual units;
* decisions, trials, troubleshooting, testing, revision, and handoffs can be represented as typed evidence-bearing events;
* failure, interruption, or blocked work must remain separate from poor performance;
* nonverbal, technical, organizational, testing, integration, support, and material work are valid contribution types;
* external physical or digital work may be linked without Concord inspecting or managing its native system;
* scores and evidence have a many-to-many relationship;
* individual, subteam, and group scores may use overlapping evidence but remain distinct judgments;
* group evidence never automatically establishes an individual score;
* missing evidence and exceptional circumstances are explicit states, not negative scores;
* corrections, rescans, revised decisions, and superseding records preserve the earlier history;
* extended writing belongs to Quillan;
* OMR belongs to ScoreForm;
* lesson planning, grade calculation, reporting, formal incident management, and source-control attribution remain outside Concord; and
* Core’s QR contract must support Concord artifacts with non-student, group, session, event, artifact, and multi-subject scope.

## 12. Completion Assessment

The three packet models have now been compared systematically. Universal requirements, optional capabilities, activity-specific extensions, cross-module ownership, unresolved questions, and initial domain-model recommendations are documented.

This matrix provides the required basis for issue #8: **Define the initial Concord domain model**.
