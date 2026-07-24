# Cross-Case Requirements Matrix

**Status:** Revised for conceptual-contract consistency  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Original issue:** #7  
**Original date:** July 13, 2026  
**Revision date:** July 22, 2026  
**Revision:** 2 — reconciled with PDS Core 0.5/PDS2, ADR 0014, the revised Concord domain model, and the initial conceptual data contracts

## 1. Purpose

This document compares the three representative Concord packet models:

* [Socratic Seminar Packet Model](../packet_models/socratic-seminar-packet-model.md);
* [Science Laboratory Group Packet Model](../packet_models/science-laboratory-group-packet-model.md); and
* [Collaborative Programming or Engineering Project Packet Model](../packet_models/collaborative-programming_engineering_project_packet_model.md).

The comparison identifies which concepts belong in Concord’s shared foundation and which should remain optional, activity-specific, deferred, or owned by another Paper Data Suite module.

This matrix originally supplied the basis for the initial Concord domain model. It has since been reconciled with later governing decisions, including:

* the finalized PDS Core 0.5/PDS2 routing architecture;
* [ADR 0014: Make Standards-Based Scoring the Primary Concord Scoring Model](../decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md);
* the revised [Concord Conceptual Design](../concord-conceptual-design-revised.md);
* the revised [Initial Concord Domain Model](initial-concord-domain-model.md);
* the [PDS Core Integration Requirements](pds-core-integration-requirements.md); and
* the [Initial Concord Conceptual Data Contracts](conceptual-data-contracts.md).

The matrix therefore reflects both:

1. requirements demonstrated across the seminar, laboratory, and project packet cases; and
2. later suite-level architectural decisions that govern all Concord contract work.

This document does not define final JSON contracts, Python classes, database tables, filesystem persistence, route handlers, packet rendering, or user-interface workflows. Detailed record-level semantics belong to the conceptual data contracts.

## 2. Classification Method

The classification describes the level of support Concord needs, not whether every packet or Activity must instantiate the feature.

| Classification                                   | Meaning                                                                                                                           |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| **Universal Concord requirement**                | The foundational model or workflow must support it across activity types. Individual Activities may omit it when their declared orientation or workflow does not require it. |
| **Common optional capability**                   | A reusable Concord capability needed by multiple activity types but not required in every Activity.                               |
| **Activity-specific extension**                  | A concept that should normally remain in a template, artifact subtype, configurable vocabulary, or activity-specific extension rather than the base model. |
| **Owned by another PDS module**                  | The capability belongs to Core, ScoreForm, Quillan, or a future PDS module. Concord may reference it but must not duplicate it. |
| **External institutional/system responsibility** | The capability belongs outside Paper Data Suite or in an existing institutional or technical system.                              |
| **Deferred implementation detail**               | The conceptual requirement is settled, but its serialized form, interface, transport, or implementation mechanism belongs to later work. |
| **Unresolved**                                   | A genuine architectural question remains. This classification must not be used for decisions already settled by an accepted ADR or finalized Core contract. |

Case-column terms:

* **Central:** a defining part of the packet or its expected academic use;
* **Present:** directly represented;
* **Possible:** supported or anticipated but not central;
* **Limited:** only a narrow form appears;
* **Conditional:** required only under a declared Activity orientation or workflow;
* **External:** deliberately delegated elsewhere;
* **Excluded:** deliberately outside Concord.

## 3. Executive Conclusions

The three cases support a common Concord foundation centered on:

1. Activities and Sessions;
2. session-contextual Groups, Memberships, Roles, and optional Responsibilities;
3. reusable Template Definitions and immutable Template Versions;
4. reusable Packet Definitions and immutable Packet Versions;
5. generated Packet, Artifact, and Artifact Page instances with stable identity;
6. PDS2 route registrations that target existing Artifact Pages;
7. Artifact Author and Artifact Subject relationships with flexible cardinality;
8. retained paper evidence and end-to-end provenance;
9. human Review and conditional Moderation;
10. Activity scoring orientation;
11. standards profiles and ordered Focus Standards for standards-based and mixed Activities;
12. standard-backed and local Criteria;
13. immutable Scoring Scale revisions and criterion-level Score Records;
14. many-to-many relationships between evidence and Scores;
15. explicit standards-result semantics for future grading and reporting;
16. privacy, exception, correction, and supersession states; and
17. references to work owned by other PDS modules or external systems.

### 3.1 Standards-based but not standards-exclusive

Concord’s primary academic scoring model is standards-based.

The common foundation must support Activities with these scoring orientations:

```text
evidence_only
standards_based
mixed
local_criteria_only
```

A `standards_based` or `mixed` Activity selects:

* one Core-owned `standards_profile_id`;
* one or more ordered `focus_standard_ids`;
* and standard-backed Criteria whose governing standards belong to that selected scope.

A standard-backed Criterion identifies exactly one governing Core `standard_id`.

One teacher-approved Score against that Criterion is therefore one direct contextual judgment about one standard for one explicit target.

Concord must also preserve local collaboration Criteria for Activity-specific, procedural, organizational, or process expectations that are not direct standards ratings.

A local Criterion may carry non-governing standards-alignment metadata, but a Score against it must not be exported or interpreted as a direct standards result.

### 3.2 Standards selection is not performance

The matrix distinguishes:

```text
standards selection or alignment
    != evidence
    != teacher-approved standard-backed Score
    != longitudinal mastery
    != course Grade
```

Selecting a Focus Standard does not prove that it was taught, practiced, demonstrated, assessed, mastered, or graded.

A direct Concord standards result exists only when an authorized scorer records a standard-backed Score Record.

The future grading and reporting module—not Concord—will determine how results across Activities, modules, scales, and time are aggregated or reported.

### 3.3 Settled PDS2 identity model

For Concord:

```text
module_id = concord
work_id   = activity_id
```

The effective module work identity is:

```text
module_id + class_id + work_id
```

The canonical work root is module-qualified:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
```

The PDS2 QR grammar is:

```text
PDS2|m=<module_id>|c=<class_id>|w=<work_id>|r=<route_id>
```

A normal Concord route registration targets an existing Artifact Page:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

The QR identifies one expected physical page route. It does not identify an Author, Subject, student, Group, scorer, Score target, Criterion, standard, or Grade.

### 3.4 Optional structures remain optional

The comparison does **not** support making milestones, child Groups, Work Items, dependencies, trials, components, handoffs, Activity Events, Contribution Claims, or version labels mandatory for every Concord Activity.

These are recurring optional contexts that should be available without defining the base model around project-management, laboratory, or seminar terminology.

## 4. Cross-Case Matrix

### 4.1 Activity and Collaboration Context

| Requirement                                      | Seminar     | Laboratory  | Project     | Classification                | Likely owner or treatment                                      |
| ------------------------------------------------ | ----------- | ----------- | ----------- | ----------------------------- | -------------------------------------------------------------- |
| Activity                                         | Central     | Central     | Central     | Universal Concord requirement | Concord first-class concept; `activity_id` is PDS2 `work_id`   |
| Declared Activity scoring orientation            | Central     | Central     | Central     | Universal Concord requirement | Concord Activity configuration                                 |
| One or more Sessions per Activity                | Present     | Present     | Central     | Universal Concord requirement | Concord first-class concept                                    |
| Multi-Session chronology                         | Possible    | Present     | Central     | Universal Concord requirement | Preserve ordered Session context when used                     |
| Collaborative Group                              | Central     | Central     | Central     | Universal Concord requirement | Concord Activity-specific Group                                |
| Session-contextual Group Membership              | Central     | Central     | Central     | Universal Concord requirement | Concord Membership; class roster remains in Core               |
| Membership changes without rewriting history     | Possible    | Present     | Present     | Universal Concord requirement | Effective context and supersession                             |
| Contextual participant Roles                     | Central     | Present     | Present     | Universal Concord requirement | Concord Role Assignment                                        |
| Direct Responsibility Assignment                 | Limited     | Central     | Central     | Common optional capability    | Concord Responsibility Assignment                              |
| Role or Responsibility rotation/reassignment     | Possible    | Central     | Central     | Common optional capability    | Preserve original and revised assignments                      |
| Stage or phase context                           | Limited     | Central     | Present     | Common optional capability    | Optional Activity Marker, not mandatory hierarchy              |
| Milestone or checkpoint                          | Rare        | Possible    | Central     | Common optional capability    | Optional Activity Marker                                       |
| Temporary subteam                                | Rare        | Possible    | Central     | Common optional capability    | Child Group with parent Group and bounded Effective Context    |
| Task or component reference                      | Limited     | Possible    | Central     | Common optional capability    | Optional Work Item                                             |
| Task dependency                                  | Limited     | Possible    | Central     | Common optional capability    | Optional Work-Item Dependency                                  |
| Handoff between participants or child Groups     | Limited     | Possible    | Central     | Common optional capability    | Optional Activity Event or relationship                        |
| Trial, build, version, or iteration label        | Limited     | Central     | Central     | Common optional capability    | Activity Marker, Work Item, Event, or teacher-facing label     |
| Equipment or environmental context               | Rare        | Central     | Possible    | Activity-specific extension   | Laboratory or material-work template context                   |
| Discussion structure or rotation                 | Central     | Rare        | Rare        | Activity-specific extension   | Seminar packet or template configuration                       |
| Absence, late arrival, interruption, reassignment | Present    | Present     | Present     | Universal Concord requirement | Explicit context/status; never inferred as poor performance    |

### 4.2 Packet, Template, Artifact, and Routing Model

| Requirement                                      | Seminar     | Laboratory  | Project     | Classification                               | Likely owner or treatment                                      |
| ------------------------------------------------ | ----------- | ----------- | ----------- | -------------------------------------------- | -------------------------------------------------------------- |
| Reusable Packet Definition                       | Central     | Central     | Central     | Universal Concord requirement                | Concord stable lineage                                         |
| Immutable Packet Version                         | Present     | Present     | Present     | Universal Concord requirement                | Exact ordered composition used by Packet Instances             |
| Ordered Packet Components                        | Central     | Central     | Central     | Universal Concord requirement                | Concord Packet Component records                               |
| Generated Packet Instance                        | Central     | Central     | Central     | Universal Concord requirement                | Concord generated record                                       |
| Reusable Template Definition                     | Central     | Central     | Central     | Universal Concord requirement                | Concord stable lineage                                         |
| Immutable Template Version                       | Present     | Present     | Present     | Universal Concord requirement                | Exact printable revision                                       |
| Generated Artifact Instance                      | Central     | Central     | Central     | Universal Concord requirement                | One generated copy of one Template Version                     |
| Stable Artifact identifier                       | Central     | Central     | Central     | Universal Concord requirement                | Concord ID validated under Core rules                          |
| Stable Artifact Page identity before rendering   | Central     | Central     | Central     | Universal Concord requirement                | Concord Artifact Page                                          |
| PDS2 route identity before rendering              | Central     | Central     | Central     | Universal Concord requirement                | Core Route Registration targeting Artifact Page                |
| Human-readable fallback identifier               | Present     | Present     | Present     | Universal Concord requirement                | Concord generation using safe identifiers                      |
| Page number and multi-page relationship          | Present     | Central     | Central     | Universal Concord requirement                | Artifact Page and page manifest                                |
| Continuation pages                               | Possible    | Central     | Central     | Common optional capability                   | Preserve sequence and logical Artifact relationship            |
| Structured Concord Artifact                      | Central     | Central     | Central     | Universal Concord requirement                | Concord-generated evidence Artifact                            |
| Attached physical or digital work                | Possible    | Central     | Central     | Common optional capability                   | Attachment or External Reference                               |
| Artifact cover sheet or QR label                 | Possible    | Central     | Central     | Common optional capability                   | Concord routing aid                                            |
| Non-returned instructional scaffold              | Possible    | Possible    | Possible    | Common optional capability                   | Template declares whether return and routing are required      |
| Activity-specific Artifact subtype               | Central     | Central     | Central     | Universal Concord requirement                | Template taxonomy, not a schema per classroom form             |
| Subject-specific worksheet or project file       | External    | External    | External    | External institutional/system responsibility | Referenced or attached; not reimplemented by Concord           |
| Exact source scan retained before module filing  | Central     | Central     | Central     | Owned by another PDS module                  | Core source retention and provenance                           |
| QR carries full Author/Subject/scoring semantics  | Excluded    | Excluded    | Excluded    | Universal Concord prohibition                | Resolve semantics from Artifact Page and linked Concord records |

### 4.3 Authorship, Subjects, Targets, and Contribution

| Requirement                                                          | Seminar     | Laboratory  | Project     | Classification                | Likely owner or treatment                                      |
| -------------------------------------------------------------------- | ----------- | ----------- | ----------- | ----------------------------- | -------------------------------------------------------------- |
| Artifact Author distinct from Artifact Subject                       | Central     | Present     | Central     | Universal Concord requirement | Separate durable association records                            |
| Artifact Author distinct from Score target                           | Central     | Central     | Central     | Universal Concord requirement | Independent typed relationships                                 |
| Artifact Subject distinct from Score target                          | Central     | Central     | Central     | Universal Concord requirement | Subject context does not create a Score                          |
| Zero, one, or several student Subjects                               | Central     | Central     | Central     | Universal Concord requirement | Flexible Subject cardinality                                    |
| Individual, Group, Session, Activity, or multi-Subject scope         | Central     | Central     | Central     | Universal Concord requirement | Typed Subject References                                        |
| One or several Authors                                               | Present     | Central     | Central     | Universal Concord requirement | Flexible Author cardinality                                     |
| Group-representative authorship                                      | Central     | Central     | Central     | Universal Concord requirement | Authorship mode plus represented Group                           |
| Teacher-authored evidence                                            | Central     | Central     | Central     | Universal Concord requirement | Typed authorized Actor                                          |
| Recorder or physical writer not treated as sole contributor          | Possible    | Central     | Central     | Universal Concord requirement | Explicit authorship and contribution semantics                  |
| Digital account or file ownership not treated as sole authorship     | Rare        | Rare        | Central     | Universal Concord rule        | No automatic authorship inference                               |
| Assigned Role/Responsibility distinct from demonstrated contribution | Present     | Central     | Central     | Universal Concord requirement | Evidence remains separate from assignment                       |
| Contribution type or category                                       | Limited     | Central     | Central     | Common optional capability    | Configurable taxonomy; do not privilege visible production      |
| Contribution Claim                                                   | Limited     | Possible    | Central     | Common optional capability    | Student/Group evidence requiring Review or Moderation            |
| Conflicting Contribution Claims                                     | Possible    | Possible    | Central     | Common optional capability    | Moderation workflow                                             |
| Consensus or representation status                                  | Central     | Central     | Central     | Common optional capability    | Useful for Group-authored records and retrospectives            |
| Child Group, Work Item, Event, component, or external record as Subject | Rare     | Possible    | Central     | Common optional capability    | Extend typed Subject/context references                         |
| Group Score distinct from member Scores                             | Central     | Central     | Central     | Universal Concord requirement | No automatic propagation                                        |

### 4.4 Evidence, Review, Moderation, Privacy, and Correction

| Requirement                                                           | Seminar     | Laboratory  | Project     | Classification                | Likely owner or treatment                                      |
| --------------------------------------------------------------------- | ----------- | ----------- | ----------- | ----------------------------- | -------------------------------------------------------------- |
| Scanned paper remains canonical evidence                              | Central     | Central     | Central     | Universal Concord requirement | Core retains source; Concord links routed evidence             |
| Source-scan and source-page provenance                                | Central     | Central     | Central     | Owned by another PDS module   | Core retention and provenance contract                         |
| Concord Scan Reference to Artifact Page                               | Central     | Central     | Central     | Universal Concord requirement | Concord association after Core dispatch                        |
| Concord-specific identification and filing                            | Central     | Central     | Central     | Universal Concord requirement | Concord processing after PDS2 routing                           |
| Mixed-batch and multi-page intake                                     | Present     | Present     | Present     | Universal Concord requirement | Core retention; module-qualified dispatch                       |
| Human Review before consequential use                                 | Central     | Central     | Central     | Universal Concord requirement | Concord Artifact Review                                         |
| Filing-metadata correction without altering source                    | Central     | Central     | Central     | Universal Concord requirement | Review, replacement associations, and Correction Record         |
| Moderation of student-created evidence                                | Central     | Possible    | Present     | Universal Concord capability  | Invoked conditionally by evidence type                          |
| Peer observation                                                      | Central     | Optional    | Possible    | Common optional capability    | Concord Artifact type with Moderation                           |
| Multi-Subject teacher observation tracker                             | Central     | Central     | Central     | Universal Concord requirement | One source may support several Subjects and Scores              |
| Teacher support/intervention reference                                | Possible    | Central     | Central     | Common optional capability    | Evidence context, not automatic performance judgment            |
| Record-level Privacy Policy                                           | Central     | Central     | Central     | Universal Concord requirement | Concord use; vocabulary may later move to Core                  |
| More restrictive privacy for disputes and teacher notes               | Present     | Present     | Present     | Universal Concord requirement | Child record may be more restrictive                            |
| Missing, unreadable, duplicate, conflicting, or misrouted page states | Central     | Central     | Central     | Universal Concord requirement | Explicit routing, filing, Review, and correction states          |
| Rescan, correction, replacement, or supersession                      | Central     | Central     | Central     | Universal Concord requirement | Preserve source and decision history                            |
| Chronology of revised decisions or evidence                           | Possible    | Central     | Central     | Universal Concord requirement | Supersession must not erase earlier records                     |
| Handwriting, diagram, or digital-content interpretation               | Excluded    | Excluded    | Excluded    | External/out of scope         | Human interpretation only                                      |
| Review creates a Score                                                | Excluded    | Excluded    | Excluded    | Universal Concord prohibition | Review establishes readiness, not performance                   |
| Moderation acceptance creates a Score                                 | Excluded    | Excluded    | Excluded    | Universal Concord prohibition | Authorized scorer still makes the judgment                     |

### 4.5 Standards, Criteria, Scores, and Exceptional States

| Requirement                                                                                  | Seminar     | Laboratory  | Project     | Classification                | Likely owner or treatment                                               |
| -------------------------------------------------------------------------------------------- | ----------- | ----------- | ----------- | ----------------------------- | ----------------------------------------------------------------------- |
| Activity scoring orientation                                                                 | Central     | Central     | Central     | Universal Concord requirement | Concord Activity configuration                                          |
| `evidence_only` orientation                                                                  | Possible    | Possible    | Possible    | Universal Concord capability  | No Criteria or Scores required                                          |
| `standards_based` orientation                                                                | Central     | Central     | Central     | Universal Concord capability  | Primary academic scoring model                                          |
| `mixed` orientation                                                                          | Possible    | Central     | Central     | Universal Concord capability  | Standard-backed and local Criteria                                      |
| `local_criteria_only` orientation                                                            | Possible    | Possible    | Possible    | Universal Concord capability  | Scores are not direct standards results                                 |
| Core standards profile identity                                                              | Conditional | Conditional | Conditional | Owned by another PDS module   | Required for `standards_based` and `mixed`; Core owns `profile_id`       |
| Ordered Activity Focus Standards                                                             | Conditional | Conditional | Conditional | Universal Concord requirement | Concord selects durable Core `standard_id` values                        |
| Standard-backed Criterion                                                                    | Central     | Central     | Central     | Universal Concord requirement | Exactly one governing `standard_id`                                     |
| Local Criterion                                                                              | Present     | Present     | Present     | Universal Concord requirement | Activity-specific or process judgment, not direct standards result       |
| Non-governing standards alignment for a local Criterion                                      | Possible    | Possible    | Possible    | Common optional capability    | Alignment metadata only                                                  |
| Multi-standard holistic Criterion treated as several direct ratings                          | Excluded    | Excluded    | Excluded    | Universal Concord prohibition | Use separate standard-backed Criteria or retain as local                 |
| Criterion definitions and immutable Criterion Set revisions                                 | Central     | Central     | Central     | Universal Concord requirement | Concord first-class concepts                                             |
| Teacher-selected immutable Scoring Scale revision                                           | Central     | Central     | Central     | Universal Concord requirement | Concord first-class concept                                              |
| Standard-backed Score Record                                                                 | Central     | Central     | Central     | Universal Concord requirement | Direct contextual judgment about one standard                            |
| Local Score Record                                                                           | Present     | Present     | Present     | Universal Concord requirement | Valid Concord Score, not a direct standard rating                         |
| Individual Score target                                                                      | Central     | Central     | Central     | Universal Concord requirement | Typed Score-Target Reference                                             |
| Group Score target                                                                           | Central     | Central     | Central     | Universal Concord requirement | Group judgment remains distinct from member judgments                     |
| Child-Group Score target                                                                     | Rare        | Rare        | Present     | Common optional capability    | Group target with bounded context                                        |
| Session, Activity, Artifact, Work Item, or component target                                  | Possible    | Possible    | Possible    | Universal Concord capability  | Only when permitted by selected Criterion                                |
| One Score supported by several evidence sources                                              | Central     | Central     | Central     | Universal Concord requirement | Many-to-many Score Evidence Links                                        |
| One Artifact or source supporting several Scores                                             | Central     | Central     | Central     | Universal Concord requirement | Deliberate link per use                                                   |
| One source supporting several standards Scores                                               | Central     | Central     | Central     | Universal Concord requirement | Separate standard-backed Criteria and Score Records                       |
| External ScoreForm or Quillan evidence reference                                             | Present     | Present     | Present     | Universal Concord requirement | Module-qualified public reference                                        |
| External result automatically becomes a Concord Score                                        | Excluded    | Excluded    | Excluded    | Universal Concord prohibition | Explicit Concord teacher judgment required                               |
| Teacher professional judgment without one controlling Artifact                               | Present     | Present     | Present     | Universal Concord requirement | Rationale and scorer provenance                                          |
| Group or multi-Subject evidence supporting an individual standards Score                     | Present     | Present     | Present     | Universal Concord requirement | Explicit teacher judgment and relevance explanation                      |
| Group evidence automatically propagated to individual Scores                                 | Excluded    | Excluded    | Excluded    | Universal Concord prohibition | Never automatic                                                          |
| Review or Moderation distinct from Scoring                                                   | Central     | Central     | Central     | Universal Concord requirement | Separate records and states                                               |
| Score distinct from mastery, Grade, and longitudinal report                                  | Central     | Central     | Central     | Owned by another PDS module   | Future grading/reporting module owns aggregation and policy               |
| Standards alignment distinct from direct standards judgment                                 | Central     | Central     | Central     | Universal Concord requirement | Prevent inference from metadata alone                                     |
| Standards-result handoff preserves standard, target, scale, context, and supersession        | Central     | Central     | Central     | Universal Concord requirement | Conceptual handoff projection; serialization deferred                     |
| Missing evidence distinct from negative evidence                                             | Central     | Central     | Central     | Universal Concord requirement | Explicit non-score states                                                 |
| `absent`, `excused`, `not_observed`, `insufficient_evidence`, `not_applicable`, `deferred`    | Central     | Central     | Central     | Universal Concord requirement | Score disposition vocabulary                                              |
| Blocked, interrupted, equipment failure, dependency failure, or external tool failure        | Possible    | Central     | Central     | Common optional capability    | Contextual reasons, not low Scores                                        |
| Automated behavioral scoring or inferred engagement                                          | Excluded    | Excluded    | Excluded    | Universal Concord prohibition | Human-reviewed, teacher-approved judgments only                           |
| Paper scoring form and digital entry producing the same conceptual Score Record              | Possible    | Possible    | Possible    | Universal Concord requirement | Surface-neutral conceptual contract                                      |

### 4.6 Module and System Ownership

| Capability                                                                                                      | Seminar     | Laboratory  | Project     | Classification                               | Owner or treatment                              |
| --------------------------------------------------------------------------------------------------------------- | ----------- | ----------- | ----------- | -------------------------------------------- | ----------------------------------------------- |
| Workspace root and canonical class identity                                                                     | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| Durable roster and student identity                                                                              | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| Shared identifier validation and safe path helpers                                                               | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| Module-qualified work identity and work-root helpers                                                             | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| PDS2 QR parsing, serialization, Route Registration, and generic dispatch                                         | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| Source-scan retention and shared provenance                                                                     | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| Shared routing failure and resolution metadata                                                                  | Required    | Required    | Required    | Owned by another PDS module                  | `pds-core`                                      |
| Standards library, profiles, durable `standard_id`, and durable `profile_id`                                    | Conditional | Conditional | Conditional | Owned by another PDS module                  | `pds-core`; required when Activity uses standards |
| Activity scoring orientation and Focus Standard selection                                                       | Central     | Central     | Central     | Universal Concord requirement                | `pds-concord`                                   |
| Standard-backed/local Criterion semantics and Score Records                                                     | Central     | Central     | Central     | Universal Concord requirement                | `pds-concord`                                   |
| Activity-specific Groups, Sessions, Roles, Packets, Artifacts, Review, Moderation, and evidence linkage         | Required    | Required    | Required    | Universal Concord requirement                | `pds-concord`                                   |
| OMR and machine-readable checks                                                                                  | External    | External    | External    | Owned by another PDS module                  | `pds-scoreform`                                 |
| Focused or extended written responses                                                                           | External    | External    | External    | Owned by another PDS module                  | `pds-quillan`                                   |
| Cross-Activity or cross-module standards aggregation, weighting, mastery policy, grades, and reporting          | External    | External    | External    | Owned by another PDS module                  | Future grading/reporting module                 |
| Objectives, instructional sequence, materials, timing, lesson plans, and unit plans                            | External    | External    | External    | Owned by another PDS module                  | Future lesson-planning module                   |
| Formal safety, medical, disciplinary, or incident record                                                        | Rare        | Possible    | Possible    | External institutional/system responsibility | School or district system                       |
| Source control, repository history, CAD/project-file management, and digital edit history                       | Rare        | Rare        | Central     | External institutional/system responsibility | Existing technical systems                      |

## 5. Universal Concord Requirements

The following are foundation-level requirements for the Concord domain and conceptual contracts:

### 5.1 Activity, collaboration, and identity

* Activity and Session identity;
* `activity_id` as Concord’s Core routing `work_id`;
* module-qualified work identity and paths;
* Activity-specific Groups and Session-contextual Membership;
* contextual Role Assignment;
* optional Responsibility Assignment;
* typed participant, Actor, Subject, and Score-Target References;
* and historical preservation of Membership, Role, and Responsibility changes.

### 5.2 Definitions, generated records, and routing

* reusable Template Definitions with immutable Template Versions;
* reusable Packet Definitions with immutable Packet Versions;
* ordered Packet Components;
* generated Packet Instances;
* generated Artifact Instances;
* one or more Artifact Pages per Artifact;
* durable page and route identity before rendering;
* PDS2 Route Registration targeting an existing Artifact Page;
* human-readable fallback identification;
* and semantic resolution through linked Concord records rather than QR metadata.

### 5.3 Evidence and judgment

* flexible Artifact Author and Artifact Subject relationships;
* individual, Group, Session, Activity, Work Item, Event, Artifact, and multi-Subject scope;
* retained source evidence and provenance through Core;
* Concord Scan References;
* human Review, metadata correction, and scoring readiness;
* conditional Moderation of peer, disputed, or student-created evidence;
* record-level privacy;
* many-to-many evidence-to-Score relationships;
* explicit professional-judgment rationale when no formal evidence link controls the Score;
* and non-destructive correction and supersession.

### 5.4 Standards and scoring

* Activity scoring orientation;
* support for `evidence_only`, `standards_based`, `mixed`, and `local_criteria_only`;
* Core standards profile references for `standards_based` and `mixed` Activities;
* ordered Focus Standard IDs;
* standard-backed Criteria with exactly one governing `standard_id`;
* local Criteria that remain distinguishable from direct standards judgments;
* optional non-governing alignment metadata for local Criteria;
* immutable Criterion Set, Criterion, and Scoring Scale revisions;
* standard-backed and local Score semantics;
* individual and Group Score targets;
* explicit standards-specific non-score dispositions;
* one standard-backed Score representing one Criterion, one governing standard, one target, and one exact scale revision;
* standards-result handoff semantics sufficient for future reporting;
* and the separation of Score from mastery, Grade, and reporting policy.

A universal capability does not imply that every Activity must instantiate it.

For example:

* an `evidence_only` Activity may use no Criteria or Scores;
* a `local_criteria_only` Activity may produce Scores without standards results;
* and Moderation must exist in the foundation even though many teacher-authored sources will not require it.

## 6. Common Optional Capabilities

These capabilities recur across multiple cases and should be supported without becoming mandatory parts of every Activity:

* Responsibility Assignments separate from Roles;
* Activity Markers for stages, phases, milestones, checkpoints, rotations, or iterations;
* child Groups for temporary subteams;
* Work Items and bounded components;
* Work-Item Dependencies;
* typed Activity Events for decisions, troubleshooting, testing, revision, handoff, interruption, and teacher intervention;
* Role and Responsibility reassignment;
* contribution categories and Contribution Claims;
* Group consensus or representation status;
* teacher assistance or intervention references;
* Attachments and Artifact cover sheets;
* continuation pages and long-lived logs;
* long-running Packet series;
* child-Group Score targets;
* contextual exception reasons such as equipment failure, interrupted work, or dependency blockage;
* local Criteria alongside standard-backed Criteria;
* non-governing standards alignment for local Criteria;
* ScoreForm result references as supporting evidence;
* Quillan result references as supporting evidence;
* and standards-result export or handoff adapters.

These features should be optional records, relationships, or controlled extensions around the universal Activity–Artifact–Evidence–Judgment model.

Concord should not become:

* a general project-management application merely because it can document Work Items or dependencies;
* a general lesson-planning application merely because Activities select standards;
* or a gradebook merely because it records standard-backed Scores.

## 7. Activity-Specific Extensions

The following concepts should normally remain in Templates, Artifact subtypes, configurable vocabularies, or Activity-specific metadata.

### Seminar-specific

* inner-circle and outer-circle rotations;
* discussion moves;
* speaker-response maps;
* observer-target pairings;
* seminar prompts and text references;
* discussion-map legends;
* textual-evidence locators;
* and seminar-specific descriptions of selected speaking, listening, reading, or evidence-use standards.

### Laboratory-specific

* trial numbering;
* apparatus, material, sample, or environmental references;
* measurement-table layouts;
* invalid-trial reasons;
* routine safety prompts;
* procedure and data organizers;
* and laboratory-specific descriptions of selected science-practice or engineering standards.

### Programming or engineering project-specific

* build, prototype, or release labels;
* software test-case fields;
* regression or severity labels;
* component-integration terminology;
* repository or project-file locations;
* domain-specific design-review fields;
* and project-specific descriptions of selected computing, engineering, or design-practice standards.

The base model may provide generic context and standards references, but it must not encode subject-specific vocabulary as mandatory fields.

## 8. Consolidated Ownership Boundaries

### 8.1 Concord owns

* Activity and Session contracts;
* Activity scoring orientation;
* selection of Focus Standards for Concord Activities;
* Activity-specific Groups, Memberships, Roles, and optional Responsibilities;
* Packet, Template, Artifact, Review, Moderation, Criterion, Scoring Scale, and Score contracts;
* standard-backed and local Criterion semantics;
* teacher-approved standard-backed and local Score Records;
* Score Evidence Links;
* Artifact Author and Artifact Subject relationships;
* Concord Artifact layouts and Packet manifests;
* creation of Artifact Pages before rendering;
* Concord-specific page validation, filing, Review, and correction behavior after Core dispatch;
* Concord Scan References to Core-retained source pages;
* routed Concord evidence and result records;
* privacy use within Concord;
* standards-result handoff projections or exports; and
* Score entry and evidence linkage.

### 8.2 Core owns

* workspace resolution;
* canonical class, roster, and student identity;
* shared identifier validation;
* module-qualified work references and safe work-root construction;
* PDS2 QR construction, parsing, and validation;
* Route Locator and Route Registration contracts;
* module-profile recognition and generic dispatch;
* source-scan retention and source-page provenance;
* shared routing failure and resolution metadata;
* standards libraries;
* standards profiles;
* durable `standard_id` and `profile_id` values;
* standards selection and reference validation support;
* shared contract-version information;
* and shared navigation or local file-opening behavior where provided.

Core does not own:

* Concord Activity scoring orientation;
* Focus Standard ordering within a Concord Activity;
* Concord Criteria;
* Concord scoring semantics;
* Score targets;
* or standards-result interpretation.

### 8.3 ScoreForm owns

* OMR instruments;
* bubble ratings;
* machine-readable checklists;
* selected-response processing;
* ScoreForm attempts;
* question-level standards alignment;
* and ScoreForm result records.

A ScoreForm result may support a Concord Score through an explicit External Reference, Evidence Reference, and Score Evidence Link.

It does not automatically become a Concord standard-backed Score.

### 8.4 Quillan owns

* focused and extended written responses;
* Quillan assignment Focus Standards;
* review-unit observations;
* Quillan overall standard ratings;
* written feedback;
* and Quillan result records.

A Quillan standards result may support a Concord Score through an explicit external evidence relationship.

It does not automatically determine a Concord Score.

### 8.5 Future or external systems own

* lesson and unit planning;
* cross-Activity and cross-module standards aggregation;
* scale conversion and normalization;
* weighting;
* longitudinal mastery policy;
* marking-period and course-grade calculation;
* reporting and parent communication;
* formal safety or disciplinary incidents;
* source control and commit attribution;
* CAD, engineering-file, or project-file management;
* and authoritative cloud-document histories.

## 9. Settled Decisions and Remaining Deferred Questions

The original matrix identified several questions that have since been settled.

### 9.1 Settled decisions

1. **Activity identity:** Concord’s `activity_id` is the Core routing `work_id`. It is not a required Core `assignment_id`.

2. **QR model:** Concord uses PDS2:

   ```text
   PDS2|m=<module_id>|c=<class_id>|w=<work_id>|r=<route_id>
   ```

   The QR carries no required student, Group, Author, Subject, standard, Criterion, or Score semantics.

3. **Route target:** A normal Concord Route Registration targets an existing Artifact Page.

4. **Semantic resolution:** Author, Subject, participant, Group, template, standard, Criterion, and Score context resolve from module-owned records.

5. **Multi-Subject evidence:** A teacher tracker may remain one Artifact with several Artifact Subject associations. One source may support several Scores through separate Score Evidence Links.

6. **Temporal precision:** Session identity is the primary effective unit for Membership, Role, and Responsibility relationships. Activity Markers or sequence positions may refine it where needed.

7. **Roles, Responsibilities, Work Items, and Contributions:** These remain semantically distinct. Role is universal; Responsibility is optional first-class; Work Item and Contribution Claim are optional.

8. **Child Groups:** Temporary subteams use Groups with optional parent Group and bounded Effective Context.

9. **Activity Events:** A typed general Activity Event envelope is used initially. Specialized event contracts require demonstrated repeated invariants.

10. **Attachments:** Attachment is distinct from Artifact Page and Scan Reference. External records use External References and provider-neutral locators.

11. **Scoring surface:** Paper and digital entry may produce the same conceptual Score Record.

12. **Individual scoring sufficiency:** Individual Scores may use relevant Group or multi-Subject evidence when the teacher makes an explicit individual judgment and records relevance. Individual-specific evidence is not universally required.

13. **Long-running Packets:** One continuing Packet Instance or several linked Packet Instances are both permitted under explicit generation semantics.

14. **Packet versioning:** Packet Definition and immutable Packet Version are separate concepts.

15. **Criterion and scale revisioning:** Criterion Sets, Criteria, and Scoring Scales use immutable revision identities sufficient to reproduce historical Scores.

16. **Correction:** Concord uses same-type supersession relationships plus a generic Correction Record.

17. **Standards model:** Standards-based scoring is the primary academic model, but evidence-only, mixed, and local-criteria-only Activities remain valid.

18. **Governing standard:** A standard-backed Criterion has exactly one governing `standard_id`.

19. **Local Criteria:** Local collaboration Criteria remain valid and may carry non-governing alignment metadata.

20. **Grade boundary:** Concord records contextual Scores, not mastery, course Grades, or longitudinal reports.

### 9.2 Remaining deferred questions

The following do not block the conceptual foundation:

1. What exact serialized schemas and contract versions will implement each record?

2. What storage layout will Concord use beneath the Core module-qualified work root?

3. What user-interface controls will distinguish standard-backed Criteria, local Criteria, Focus Standards, and scoring orientations?

4. What exact export file, event, manifest, or API shape will carry the standards-result handoff to the future grading and reporting module?

5. Which privacy vocabulary values will ultimately remain Concord-specific and which may move into Core?

6. Which role, Criterion, contribution, Event, status, artifact, and template vocabularies should ship as starter data?

7. Which optional Activity-specific structures will prove necessary in the representative issue #12 examples?

8. What future compatibility policy will govern comparisons among different Scoring Scale revisions?

9. What optional adapters will resolve ScoreForm and Quillan public records without mandatory sibling-package dependencies?

10. What minimal review and scoring interfaces will be implemented first?

## 10. Requirements Carried into the Domain Model and Conceptual Contracts

The Concord foundation includes these first-class or explicitly contracted concepts:

* `activity`;
* `session`;
* `group`;
* `group_membership`;
* `role_assignment`;
* `responsibility_assignment`;
* `template_definition`;
* `template_version`;
* `packet_definition`;
* `packet_version`;
* `packet_component`;
* `packet_instance`;
* `artifact_instance`;
* `artifact_page`;
* `artifact_author`;
* `artifact_subject`;
* `scan_reference`;
* `artifact_review`;
* `moderation_record`;
* `correction_record`;
* `criterion_set`;
* `criterion`;
* `scoring_scale`;
* `score_record`;
* `score_evidence_link`;
* `attachment`;
* and `external_reference`.

The following are defined as optional first-class records or controlled extensions:

* `activity_marker`;
* `work_item`;
* `work_item_dependency`;
* `activity_event`;
* and `contribution_claim`.

The shared conceptual primitives include:

* Concord Record Reference;
* Module Record Reference;
* Participant Reference;
* Actor Reference;
* Subject Reference;
* Score-Target Reference;
* Evidence Reference;
* Evidence Locator;
* Provenance;
* Effective Context;
* Privacy Policy;
* Status Reason;
* External Locator;
* scoring orientation;
* Criterion classification;
* standard-backed Score semantics;
* and standards-result handoff projection.

Representative records in issue #12 should test at least:

1. a `standards_based` seminar Activity;
2. a `mixed` laboratory Activity;
3. a `mixed` or `standards_based` programming/engineering Activity;
4. an `evidence_only` Activity or Activity component;
5. standard-backed Criteria with one governing standard each;
6. local collaboration Criteria that are not direct standards ratings;
7. an individual standards Score;
8. a Group standards Score;
9. Group evidence supporting an individual Score through explicit teacher judgment;
10. one source supporting several standard-backed Scores;
11. a non-score disposition for a Focus Standard;
12. a ScoreForm result used as supporting evidence;
13. a Quillan standards result used as supporting evidence;
14. PDS2 routing to an Artifact Page with no student Subject;
15. and correction or supersession that preserves the prior record.

## 11. Confirmed Cross-Case Findings

* Authors and Subjects are separate relationships with independent cardinality.
* Authors, Subjects, Score targets, scorers, and standards are distinct concepts.
* Artifacts may have zero, one, or several student Subjects and may instead concern a Group, Session, Activity, Event, Work Item, component, Attachment, or external record.
* Physical writer, recorder, account owner, file owner, and scanner are not reliable proxies for sole authorship or contribution.
* Activities, Sessions, Groups, Memberships, and contextual Roles belong in Concord’s shared foundation.
* Roles, Responsibilities, Work Items, and contributions are distinct, although not all are mandatory for every Activity.
* Responsibilities may change by Session, marker, stage, trial, milestone, or work period, and changes preserve history.
* Assigned Responsibility is not evidence of fulfillment.
* Peer evidence and disputed Contribution Claims may require human Moderation.
* Teacher observation Artifacts may span several students, Groups, Sessions, or contextual units.
* One source may support several Subjects and several Scores without being duplicated.
* Decisions, trials, troubleshooting, testing, revision, and handoffs can be represented as typed evidence-bearing Events.
* Failure, interruption, blocked work, missing files, and equipment problems remain separate from poor performance.
* Nonverbal, technical, organizational, testing, integration, support, and material work are valid contribution forms.
* External physical or digital work may be linked without Concord inspecting or managing its native system.
* Scores and evidence have a many-to-many relationship.
* Individual, child-Group, and Group Scores may use overlapping evidence but remain distinct judgments.
* Group evidence never automatically establishes an individual Score.
* Missing evidence and exceptional circumstances are explicit dispositions or context states, not negative Scores.
* Corrections, rescans, revised decisions, and superseding records preserve earlier history.
* Standards-based scoring is Concord’s primary academic scoring model.
* Standards-based scoring does not require every Activity to produce a Score.
* `standards_based` and `mixed` Activities use a Core standards profile and ordered Focus Standards.
* A standard-backed Criterion identifies exactly one governing standard.
* A standard-backed Score is one contextual teacher-approved judgment about that standard for one target.
* Local collaboration Criteria remain supported.
* Standards alignment alone is not a direct standards result.
* A standard-backed Concord Score is not, by itself, longitudinal mastery or a course Grade.
* Extended written-response review belongs to Quillan.
* OMR and selected-response processing belong to ScoreForm.
* Lesson planning, grade calculation, reporting, formal incident management, and source-control attribution remain outside Concord.
* PDS2 routes identify physical page routes and resolve to Artifact Pages; they do not identify students or semantic scoring context directly.

## 12. Completion Assessment

The three packet models have been compared systematically and the matrix has been reconciled with the later Concord and Core architecture.

The revised matrix now distinguishes:

* universal foundation requirements from per-Activity optional use;
* reusable definitions from generated records;
* Activity identity from generic assignment assumptions;
* PDS2 route identity from Artifact semantics;
* Authors from Subjects and Score targets;
* evidence from Review, Moderation, and Scoring;
* standard-backed Criteria from local Criteria;
* standards alignment from direct standards judgments;
* individual Scores from Group Scores;
* contextual standards Scores from mastery and course Grades;
* and universal concepts from seminar-, laboratory-, and project-specific extensions.

This document now supports:

* the revised initial Concord domain model;
* the initial conceptual data contracts;
* ADR 0014;
* issue #11 documentation consistency;
* issue #12 representative contract examples;
* and issue #13 skeptical foundation review.

It does not replace the detailed record contracts. When this matrix conflicts with an accepted ADR, the finalized PDS Core contract, or the current conceptual data contracts, the later governing source controls.
