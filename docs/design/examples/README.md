# Concord Representative Contract Examples

**Status:** Draft for representative-contract validation  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Issue:** `#12 — 11. Create representative contract examples`  
**Branch:** `12-create-representative-contract-examples`  
**Revision date:** July 31, 2026  
**Revision:** 4 — reconciled with issue #13 foundation-review findings

## 1. Purpose

This directory contains representative conceptual-record examples for the initial Concord foundation.

The examples test whether the same implementation-neutral architecture can represent substantially different collaborative classroom activities without:

* introducing inappropriate case-specific foundational records;
* weakening accepted domain invariants;
* duplicating responsibilities owned by PDS Core, Meridian, ScoreForm, Quillan, or external systems;
* treating standards alignment as a standards result;
* forcing every Activity into the same scoring configuration;
* treating publication as Grade eligibility;
* hiding cross-producer evidence lineage;
* or concealing missing concepts inside undocumented extension data.

The representative activity families are:

1. a Socratic seminar or structured discussion;
2. a science laboratory investigation;
3. a collaborative programming or engineering project.

The examples also validate the proposed academic-result publication chain:

```text
Concord Activity and native records
    -> optional explicit Core Academic Work Registration
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> policy-controlled Meridian consumption
```

These layers remain distinct.

In particular:

* Activity creation does not create an Academic Work Registration;
* registration does not publish results;
* publication does not create Grade-item or Academic Period membership;
* Meridian policy does not rewrite Concord-native Scores;
* and a Meridian override does not become a Concord Score revision.

These examples are validation artifacts. They are not production fixtures, formal JSON Schemas, persistence formats, runtime API promises, or user-interface specifications.
## 2. Directory Contents

```text
docs/design/examples/
├── README.md
├── seminar-contract-example.md
├── laboratory-contract-example.md
├── project-contract-example.md
└── cross-example-validation.md
```

### `README.md`

Defines the shared notation, identifier conventions, record expectations, architectural rules, publication conventions, and validation method used by every representative example.

### `seminar-contract-example.md`

Tests individual standards judgments, peer evidence, teacher-authored multi-Subject evidence, Artifact Author and Subject separation, Moderation, non-score dispositions, optional Quillan evidence, an initial Concord Academic Result Manifest, and a Core Publication Record.

### `laboratory-contract-example.md`

Tests mixed standards-and-local scoring, Group evidence, Group and individual targets, Roles and Responsibilities, procedural exceptions, external ScoreForm evidence, cross-producer lineage, and publication of local and standard-backed Scores without conflating their meanings.

### `project-contract-example.md`

Tests long-running collaborative work, changing Membership, child Groups, Activity Markers, Work Items, Dependencies, Events, Attachments, External References, Contribution Claims, externally owned technical evidence, native Score supersession, manifest revision, Core publication supersession, and bounded withdrawal semantics.

### `cross-example-validation.md`

Compares the three cases against the same conceptual contracts and records any tensions, rejected workarounds, required clarifications, or foundation changes. It must also validate registration, immutable manifest publication, Core discovery, lineage, and Meridian ownership across the examples.
## 3. Governing Sources

The examples must conform to the current Concord architecture, including:

* `docs/decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md`;
* `docs/decisions/0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md`;
* `docs/concord-conceptual-design-revised.md`;
* `docs/design/cross-case-requirements.md`;
* `docs/design/initial-concord-domain-model.md`;
* `docs/design/pds-core-integration-requirements.md`;
* `docs/design/conceptual-data-contracts.md`;
* the other accepted Concord Architecture Decision Records;
* the released `pds-core` v0.6.0 PDS2 routing contracts;
* the released Core Academic Work Registration, Publication Record, Publication Withdrawal, and registry contracts;
* and the current Meridian architecture decisions governing grading, Academic Period membership, overrides, and report snapshots.

ADR 0015 is Accepted following the issue #13 skeptical foundation review. The
examples exercise its publication architecture but do not claim a Concord
runtime implementation.

The released `pds-core` v0.6.0 package is the routing and registry integration
baseline. The examples remain architecture fixtures, not evidence that Concord
implements those released APIs.

When two sources appear to conflict, the following precedence applies:

1. accepted or superseding ADRs;
2. released PDS Core contracts for released Core-owned infrastructure;
3. accepted ADR 0015 and released Core v0.6.0 registry contracts;
4. the current Concord conceptual data contracts;
5. the current Concord domain model;
6. the current conceptual design;
7. the reconciled cross-case requirements;
8. historical design rationale.

Historical PDS1 descriptions do not override current PDS2 requirements.

A representative case that cannot be modeled consistently under the governing sources must identify the problem explicitly. It must not silently invent a workaround, assume an unreleased API, or convert a proposed decision into an accepted one.
## 4. Scope

The examples may define representative instances of Concord-owned records and projections, including:

* Activity;
* Session;
* Group;
* Group Membership;
* Role Assignment;
* Responsibility Assignment;
* Template Definition;
* Template Version;
* Packet Definition;
* Packet Version;
* Packet Component;
* Packet Instance;
* Artifact Instance;
* Artifact Page;
* Artifact Author;
* Artifact Subject;
* Scan Reference;
* Artifact Review;
* Moderation Record;
* Correction Record;
* Criterion Set;
* Criterion;
* Scoring Scale;
* Score Record;
* Score Evidence Link;
* Attachment;
* External Reference;
* Activity Marker;
* Work Item;
* Work-Item Dependency;
* Activity Event;
* Contribution Claim;
* Concord Academic Result Manifest;
* Manifest Activity Context;
* Manifest Criterion Projection;
* Manifest Scoring Scale Projection;
* Manifest Score Projection;
* Manifest Evidence-Lineage Projection;
* Manifest Moderation Projection;
* and Standards Result Projection.

The examples may also show contract-complete Core-owned records or relationship summaries needed to validate publication:

* Academic Work Registration;
* Publication Record;
* Publication Withdrawal;
* Module Work Reference;
* Module Record Reference;
* and a source Publication Record reference used in cross-producer lineage.

A Meridian section may describe required import provenance and policy boundaries. It must not invent a complete Meridian serialized contract where the Meridian repository has not defined one.

Not every case must instantiate every record or projection.

The examples must document deliberately omitted records when their absence is meaningful to the validation. In particular, an evidence-only Activity should demonstrate that Activity existence does not automatically create registration or publication.
## 5. Out of Scope

The examples do not define:

* production Python classes;
* Pydantic or dataclass models;
* formal JSON Schema documents;
* database tables;
* final filesystem persistence;
* file-writing services;
* packet-rendering code;
* QR-generation code;
* route-registration implementation;
* route-dispatch handlers;
* scan-intake services;
* Core registry service implementation;
* Core catalog storage or repair implementation;
* CLI workflows;
* graphical workflows;
* final manifest serialization or canonicalization code;
* final publication authorization rules;
* grading algorithms;
* Meridian evidence-selection policies;
* Meridian scale-mapping policies;
* mastery calculations;
* cross-Activity aggregation;
* cross-module aggregation;
* Grade-item membership;
* Academic Period membership;
* report-card calculation;
* Meridian report snapshot schemas;
* parent communication;
* or final public API stability.

The examples may resemble YAML or JSON for readability, but their meaning remains conceptual.

They must not:

* claim that current Core registry APIs are part of `pds-core` 0.5;
* pin a speculative future Core package version;
* or imply that a conceptual example is an executable publication request.
## 6. Example Structure

Each principal example should use the following structure.

```text
1. Case purpose
2. Activity narrative
3. Governing assumptions
4. Record inventory
5. Shared external and Core references
6. Activity and collaboration records
7. Template and Packet records
8. Artifact and routing records
9. Author and Subject associations
10. Scan, Review, and Moderation records
11. Criteria and Scoring Scale records
12. Score Records and evidence links
13. External References and Attachments
14. Native correction and Score supersession
15. Core Academic Work Registration relationship
16. Concord Academic Result Manifest
17. Core Publication Record, supersession, or withdrawal
18. Meridian consumption boundary
19. Relationship summary
20. Lifecycle walkthrough
21. Invariant validation
22. Represented cleanly
23. Optional structures used
24. Contracts deliberately not used
25. Tensions or ambiguities
26. Workarounds rejected
27. Contract changes required
```

Sections may be combined when doing so does not reduce clarity.

A case that is deliberately unregistered or unpublished must still include Sections 15–18 and explain the omission. Absence is part of the validation; it must not be left implicit.
## 7. Record Notation

Representative records should use fenced `yaml` blocks unless another format makes a relationship clearer.

The examples use two illustrative envelope fields to keep ownership and record type visible:

```yaml
record_owner: concord
record_kind: activity
```

`record_owner` is example-document notation rather than a proposed serialized contract field. It identifies the authority responsible for the illustrated record without colliding with contract fields.

`record_kind` in the illustrative envelope identifies the illustrated conceptual record. A nested contract-native reference may also contain `record_kind`; the two uses remain distinguishable by nesting.

Do not use `owning_system` as the generic envelope field for a Concord-owned record. `owning_system` appears only where a governing value-object or record contract defines it, including Participant, Actor, Subject, Evidence, Score-Target, External Reference, and External Locator relationships.


Core-owned records use the same illustrative envelope convention:

```yaml
record_owner: core
record_kind: publication_record
```

The envelope does not transfer ownership to Concord.

A Concord Academic Result Manifest uses:

```yaml
record_owner: concord
record_kind: concord_academic_result_manifest
```

The manifest has no separate `manifest_id` in the conceptual contract. Its exact identity is the combination of:

```text
record_set_id
record_set_revision
manifest_contract_version
exact manifest bytes
```

An Academic Work Registration likewise has no invented registration ID in these examples. Its identity is governed by the Core work reference and `registration_revision`.

A Publication Withdrawal has no separate invented withdrawal ID under the current Core model. It identifies the immutable `publication_id` being withdrawn.

Example Activity record:

```yaml
record_owner: concord
record_kind: activity
activity_id: act_seminar_01
class_reference:
  module_id: core
  record_kind: class
  record_id: cls_ela10_p03
title: Evidence and Perspective Seminar
activity_type: local:socratic_seminar
scoring_orientation: standards_based
standards_profile_id: profile_njsls_ela_2023_09_10
focus_standard_ids:
- std_njsls_sl_pe_9_10_1
- std_njsls_rl_cr_9_10_1
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-14T14:30:00-04:00'
  source_kind: manual
  note: Created during teacher configuration.
```

The examples do not prescribe a future serialized envelope. They must nevertheless use the conceptual-contract field names and include all fields that the governing contract marks required or conditional for the represented state.

Each included record must make clear:

* record kind;
* durable identity;
* record owner;
* all required conceptual fields;
* all conditionally required fields triggered by the represented state;
* significant optional fields;
* contract-native typed relationships;
* lifecycle state;
* provenance;
* privacy where required or materially relevant;
* supersession where applicable;
* immutable revision identity where applicable;
* manifest or publication ownership where applicable;
* and digest or withdrawal state where applicable.

A case may represent repeated records as a YAML array or a compact table only when the notation supplies every required conceptual field for every record. An inventory row that merely names a record does not count as a complete representative record.

Optional fields should normally be omitted when they are absent. Use an explicit `null` only when the governing contract permits it and the distinction between “present with no value” and “absent” is semantically meaningful. A field forbidden for a represented state must be omitted rather than written as `null`.

A field omitted from a representative record should not be assumed forbidden unless the contract explicitly says so.

Display metadata must not be inserted into a typed reference unless that reference contract permits it. In particular:

* Concord Record References and Module Record References do not contain `display_label`;
* Participant References do not contain `display_label`;
* Subject References do not contain `display_label`;
* Evidence References do not contain `display_label`;
* Actor References may contain `display_label_snapshot`;
* External References and External Locators may contain their contract-defined display fields.

### 7.1 Exact manifest byte notation

Most conceptual records may use YAML.

A case that claims a valid Core Publication Record must additionally provide the exact published manifest bytes in one fenced `json` block under a heading such as:

```text
Exact Published Manifest Bytes
```

For issue #12 mechanical validation:

* the content between the opening and closing `json` fences is encoded as UTF-8;
* line endings are normalized to LF;
* exactly one final LF is included;
* comments, placeholders, and ellipses are forbidden;
* illustrative envelope fields such as `record_owner` and example-only `record_kind` are omitted unless the governing serialized contract explicitly defines them;
* the JSON must parse successfully;
* and the Publication Record’s SHA-256 digest must equal the digest of those exact bytes.

A formatted YAML projection may accompany the exact JSON for readability, but the digest binds the exact JSON byte block, not the explanatory YAML.

If the example does not provide exact manifest bytes, it may discuss publication conceptually but must not claim that the digest check passed.
## 8. Synthetic Identifier Conventions

All identifiers must be synthetic.

Identifiers must:

* contain no student names;
* contain no real school identifiers;
* contain no direct personal information;
* be safe for use in paths when applicable;
* remain stable when display labels change;
* identify one conceptual record only;
* and never be reused for a different record.

Recommended example prefixes include:

| Concept                      | Prefix      |
| ---------------------------- | ----------- |
| Core class                   | `cls_`      |
| Core student                 | `stu_`      |
| Core standards profile       | `profile_`  |
| Core standard                | `std_`      |
| Activity                     | `act_`      |
| Session                      | `ses_`      |
| Group                        | `grp_`      |
| Group Membership             | `mem_`      |
| Role Assignment              | `role_`     |
| Responsibility Assignment    | `resp_`     |
| Template Definition          | `tmpl_`     |
| Template Version             | `tmplv_`    |
| Packet Definition            | `pktdef_`   |
| Packet Version               | `pktv_`     |
| Packet Component             | `pktcmp_`   |
| Packet Instance              | `pkt_`      |
| Artifact Instance            | `art_`      |
| Artifact Page                | `page_`     |
| Artifact Author              | `author_`   |
| Artifact Subject             | `subject_`  |
| Route                        | `route_`    |
| Core source scan             | `scan_`     |
| Scan Reference               | `scanref_`  |
| Artifact Review              | `review_`   |
| Moderation Record            | `mod_`      |
| Correction Record            | `corr_`     |
| Criterion Set                | `critset_`  |
| Criterion                    | `crit_`     |
| Scoring Scale                | `scale_`    |
| Score Record                 | `score_`    |
| Score Evidence Link          | `scoreev_`  |
| Manifest record set          | `rs_`       |
| Core Publication Record       | `pub_`      |
| Attachment                   | `attach_`   |
| External Reference           | `extref_`   |
| Activity Marker              | `marker_`   |
| Work Item                    | `workitem_` |
| Work-Item Dependency         | `dep_`      |
| Activity Event               | `event_`    |
| Contribution Claim           | `claim_`    |

The prefixes improve readability only. They are not proposed production identifier formats.

Do not invent:

* `manifest_id`;
* `academic_work_registration_id`;
* `publication_withdrawal_id`;
* or a durable identifier for each Standards Result Projection row

unless a later governing contract explicitly adds one.

The current identities are:

```text
Academic Work Registration:
ModuleWorkRef + registration_revision

Concord Academic Result Manifest revision:
record_set_id + record_set_revision + manifest_contract_version

Core Publication Record:
publication_id

Core Publication Withdrawal:
publication_id + immutable withdrawal record

Standards Result Projection row:
the containing manifest revision + canonical score_record_id
```

Display labels may be human-readable:

```yaml
group_id: grp_lab_01
label: Group A
```

The label is not durable identity.
## 9. Shared Synthetic Context

The examples may share a synthetic suite context to simplify cross-case comparison.

Recommended Core-owned records:

```yaml
classes:
- class_id: cls_ela10_p03
  display_label: English 10 — Period 3
- class_id: cls_biology_p05
  display_label: Biology — Period 5
- class_id: cls_apcsp_p01
  display_label: AP Computer Science Principles — Period 1
```

Recommended synthetic Core students:

```yaml
students:
- student_id: stu_001
  display_label: Student 001
- student_id: stu_002
  display_label: Student 002
- student_id: stu_003
  display_label: Student 003
- student_id: stu_004
  display_label: Student 004
- student_id: stu_005
  display_label: Student 005
- student_id: stu_006
  display_label: Student 006
```

These blocks summarize referenced Core records. They are not Participant References.

Additional synthetic participants may be introduced when needed.

Teachers and authorized adults must use Actor References. They must not be represented as Core students.

Example Actor Reference:

```yaml
actor_kind: authorized_adult
actor_id: actor_teacher_001
owning_system: local_example_identity
display_label_snapshot: Teacher 001
```


### Shared publication context

Each publishable case should define one synthetic Core `ModuleWorkRef`:

```yaml
work:
  module_id: concord
  class_id: cls_ela10_p03
  work_id: act_seminar_01
```

For Concord:

```text
work_id = activity_id
```

An Academic Work Registration and Publication Record belong to one exact work reference. They are not shared globally across the three examples.

A case may refer to a synthetic Core Academic Period or calendar revision only in its Meridian-consumption discussion. The producer Activity, Score Records, and initial Concord manifest must not acquire authoritative `academic_period_id` fields merely to make the downstream example easier.
## 10. Typed Reference Conventions

The examples must use the distinct typed-reference contracts defined by the governing conceptual data contracts. A generic object containing only `owning_system`, `record_kind`, and `record_id` must not be substituted for every reference type.

The selected shape depends on the semantic role of the relationship.

### 10.1 Concord Record Reference

A Concord Record Reference identifies another Concord-owned record.

```yaml
record_kind: group
record_id: grp_lab_01
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `record_kind` | Required | Controlled Concord record kind |
| `record_id` | Required | Durable Concord identifier |
| `contract_version` | Optional | Referenced public contract version |

Do not add `owning_system: concord`; Concord ownership is inherent in this reference type.

Use this shape for fields such as:

* `target_reference` and `replacement_reference` on Correction Records when the target is Concord-owned;
* `source_reference` in Provenance when the source is Concord-owned;
* `inherited_from` when privacy is inherited from a Concord record;
* and other fields explicitly requiring a Concord Record Reference.

### 10.2 Module Work Reference

A Module Work Reference identifies one module-owned top-level work context.

```yaml
module_id: concord
class_id: cls_ela10_p03
work_id: act_seminar_01
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `module_id` | Required | Owning PDS module |
| `class_id` | Required | Core class identifier |
| `work_id` | Required | Producer-owned top-level work identifier |

For Concord:

```text
module_id = concord
work_id   = activity_id
```

Use this shape for:

* `work` on an Academic Work Registration;
* `work` on a Core Publication Record;
* and `work` on a Concord Academic Result Manifest.

A bare `activity_id` is not a complete suite-level work reference.

### 10.3 Module Record Reference

A Module Record Reference identifies a record owned by a PDS module.

```yaml
module_id: core
record_kind: class
record_id: cls_ela10_p03
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `module_id` | Required | Owning PDS module |
| `record_kind` | Required | Public module record kind |
| `record_id` | Required | Durable module-owned identifier |
| `contract_version` | Optional | Referenced public contract version |

Use this shape for Core class, Core source-scan, ScoreForm, Quillan, and other PDS-module record references when the field contract calls for a module-qualified record.

Examples:

```yaml
class_reference:
  module_id: core
  record_kind: class
  record_id: cls_biology_p05
```

```yaml
core_source_scan_reference:
  module_id: core
  record_kind: source_scan
  record_id: scan_core_lab_batch_01
```

```yaml
module_id: scoreform
record_kind: result
record_id: sf_result_001
contract_version: '1'
```

### 10.4 Participant Reference

A Participant Reference identifies a human participant in an Activity.

```yaml
participant_kind: core_student
participant_id: stu_001
owning_system: core
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `participant_kind` | Required | `core_student`, `authorized_actor`, or approved future kind |
| `participant_id` | Required | Durable participant identity |
| `owning_system` | Required | Identity authority |

Use Participant References for:

* `participant_reference` on Group Membership and Role Assignment;
* human assignees where a field permits a participant;
* and human audience entries where the policy uses participant identity.

A Group is not a human Participant Reference. Group relationships use a Concord Record Reference, Subject Reference, Score-Target Reference, or another field-specific type.

### 10.5 Actor Reference

An Actor Reference identifies a person or system responsible for an action.

```yaml
actor_kind: authorized_adult
actor_id: actor_teacher_001
owning_system: local_example_identity
display_label_snapshot: Teacher 001
role_snapshot: classroom_teacher
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `actor_kind` | Required | `core_student`, `authorized_adult`, `system`, or `external_actor` |
| `actor_id` | Required | Durable actor identity |
| `owning_system` | Required | Identity authority |
| `display_label_snapshot` | Optional | Historical display aid |
| `role_snapshot` | Optional | Actor role at the time of action |

Use Actor References for provenance, assignment, generation, Review, Moderation, correction, and scoring fields.

System Actor example:

```yaml
actor_kind: system
actor_id: generator_concord_001
owning_system: concord
display_label_snapshot: Concord packet generator
```

### 10.6 Subject Reference

A Subject Reference identifies whom or what a record concerns.

```yaml
subject_kind: core_student
subject_id: stu_002
owning_system: core
```

```yaml
subject_kind: concord_group
subject_id: grp_lab_a
owning_system: concord
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `subject_kind` | Required | Contract-supported Subject kind |
| `subject_id` | Required | Durable Subject identifier |
| `owning_system` | Required | Owner of the Subject record |
| `contract_version` | Optional | Referenced public contract version |

Initial kinds include:

```text
core_student
concord_group
concord_session
concord_activity
concord_activity_marker
concord_work_item
concord_activity_event
concord_attachment
external_record
```

Use Subject References for Artifact Subject associations, Moderation target subjects, External Reference subject context, and Score Evidence Link `subject_context`.

### 10.7 Score-Target Reference

A Score-Target Reference identifies the entity receiving one criterion-level judgment.

The conceptual contract defines the Score-Target Reference field table and invariants. To prevent accidental substitution of a Subject Reference, every example uses the following contract-native notation:

```yaml
target_kind: core_student
target_id: stu_001
owning_system: core
```

```yaml
target_kind: concord_group
target_id: grp_lab_a
owning_system: concord
```

Permitted initial kinds include:

```text
core_student
concord_group
concord_session
concord_activity
concord_artifact_instance
concord_work_item
```

This is the contract-native Score-Target Reference shape.

A Score target is not an Artifact Subject and must not be represented through Subject Reference fields.

### 10.8 Evidence Reference

An Evidence Reference identifies one evidence source.

```yaml
evidence_kind: artifact_instance
owning_system: concord
record_id: art_teacher_tracker_001
```

```yaml
evidence_kind: scoreform_result
owning_system: scoreform
record_id: sf_result_001
contract_version: '1'
```

Conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `evidence_kind` | Required | Evidence-source type |
| `owning_system` | Required | Owner of the source |
| `record_id` | Required | Durable source identifier |
| `contract_version` | Optional | Public source-contract version |
| `locator` | Optional | Location within the source |
| `subject_context` | Optional | Relevant Subject Reference |
| `moderation_requirement` | Optional | Whether Moderation is required |

Initial evidence kinds include:

```text
artifact_instance
artifact_page
attachment
contribution_claim
activity_event
teacher_rationale
scoreform_result
quillan_response
external_record
```

The `evidence_kind` must be compatible with `owning_system`.

### 10.9 External providers

A record owned by a non-PDS external provider is normally represented through a Concord-owned External Reference rather than through an undocumented generic typed reference.

Example external provider identity inside an External Reference:

```yaml
owning_system: github
external_record_kind: repository_commit
external_record_id: synthetic_commit_001
```

Do not use the above three fields as a generic replacement for Participant, Actor, Subject, Score-Target, Evidence, Concord Record, or Module Record References.

### 10.10 Core Publication Reference

The Manifest Evidence-Lineage Projection may identify an exact originating Core Publication Record when the source producer result is already published.

The conceptual contract defines a Core Publication Reference value object. These examples use the following contract-native notation:

```yaml
source_publication_reference:
  publication_id: pub_scoreform_resultset_001
```

The `publication_id` resolves to the immutable Core Publication Record. Do not copy the complete Publication Record into every lineage row.

The `publication_id` is required.

An optional `publication_schema_version` may be included when needed for compatibility.

A source Publication Record reference is:

* required when the source revision was resolved through, or verified against, an exact Core Publication Record;
* omitted only when another immutable source-version mechanism is preserved;
* distinct from the originating module-owned result record;
* and insufficient by itself without `source_record_reference`.

The manifest must preserve both where available:

```text
originating module record
    + exact Core source publication
    + Concord evidence-use relationship
```
## 11. Participant, Actor, Subject, and Target Distinctions

The examples must preserve the following distinctions and use the corresponding typed-reference shape from Section 10.

### Participant

A Participant Reference identifies a human participant in the Activity.

A rostered student is represented as:

```yaml
participant_kind: core_student
participant_id: stu_001
owning_system: core
```

### Actor

An Actor Reference identifies a person or authorized system responsible for an action such as:

* assigning a Role;
* creating a record;
* reviewing evidence;
* moderating evidence;
* correcting a record;
* or recording a Score.

```yaml
actor_kind: authorized_adult
actor_id: actor_teacher_001
owning_system: local_example_identity
display_label_snapshot: Teacher 001
```

### Artifact Author

An Artifact Author association identifies who produced, recorded, or formally represented an Artifact. Its nested `author_reference` uses the field-specific supported reference type; it is not inferred from Membership, Role, handwriting, possession, device ownership, account ownership, file ownership, or upload identity.

### Artifact Subject

An Artifact Subject association identifies whom or what the Artifact concerns. Its nested `subject_reference` is a Subject Reference.

### Score target

A Score target identifies whom or what received a teacher-approved judgment. Its nested `target_reference` is a Score-Target Reference.

### Scorer

A scorer identifies the authorized Actor who made the judgment. Its nested `scorer` field is an Actor Reference.

These relationships may refer to the same underlying identity in a particular case, but they must never be collapsed conceptually or serialized with the wrong reference type.

For example:

```text
Artifact Author: Student 001
Artifact Subject: Student 002
Score target: Student 002
Scorer: Teacher 001
```

The fact that the Subject and Score target happen to identify Student 002 does not make them the same relationship.

### Publication identities

The examples must also keep the following identities separate:

```text
Concord Activity identity
Core Academic Work Registration revision
Concord manifest record-set identity
Concord manifest revision
Core Publication Record identity
Core Publication Withdrawal state
Meridian import or derived-result identity
```

A shared Activity or Score does not make these records interchangeable.

For example:

```text
score_seminar_001_revision_2
```

may cause:

```text
rs_seminar_results revision 2
```

which may be announced by:

```text
pub_seminar_results_002
```

The Score ID, record-set ID, manifest revision, and publication ID remain different identities with different owners.
## 12. Provenance and Shared Value-Object Conventions

Every consequential record should retain sufficient provenance to identify:

* the Actor responsible for the action;
* the time of the action;
* the general source category;
* the source record or process when applicable;
* the producing application version when useful;
* and a concise explanatory note when useful.

The shared Provenance value object uses these conceptual fields:

| Field | Requirement | Meaning |
|---|---|---|
| `actor` | Required | Actor Reference responsible for the action |
| `timestamp` | Required | Time of the action |
| `source_kind` | Required | `manual`, `generated`, `imported`, `routed`, `system`, or another approved kind |
| `source_reference` | Optional | Concord Record Reference, Module Record Reference, or other field-approved source |
| `application_version` | Optional | Producing software version |
| `note` | Optional | Human explanation |

Recommended conceptual shape:

```yaml
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-15T10:12:00-04:00'
  source_kind: manual
  source_reference:
    record_kind: artifact_instance
    record_id: art_seminar_peer_001
  note: Attribution confirmed during teacher Review.
```

Use `source_kind` for the broad provenance category. Workflow-specific detail such as `teacher_configuration`, `packet_generation`, `teacher_review`, or `teacher_scoring` belongs in `note`, a typed `source_reference`, or a later approved controlled vocabulary; it must not replace the contract field with an alternate `creation_method` field.

Generated example:

```yaml
created_provenance:
  actor:
    actor_kind: system
    actor_id: generator_concord_001
    owning_system: concord
    display_label_snapshot: Concord packet generator
  timestamp: '2026-09-15T08:00:00-04:00'
  source_kind: generated
  application_version: synthetic-concord-0.1
  note: Generated from the selected immutable Packet Version.
```

Provenance identifies the source of the action. It does not establish Artifact authorship.

### 12.1 Effective Context

An Effective Context defines when a Membership, Role, Responsibility, Group, or other contextual relationship applies within one Activity.

The shared shape is:

```yaml
effective_context:
  activity_id: act_seminar_01
  session_ids:
  - ses_seminar_01
  sequence_start: 1
  sequence_end: 1
```

Conceptual fields are:

| Field | Requirement | Meaning |
|---|---|---|
| `activity_id` | Required | Parent Activity |
| `session_ids` | Conditional | Explicit Sessions in which the relationship applies |
| `activity_marker_ids` | Optional | Additional marker context |
| `sequence_start` | Optional | Start position within a Session or marker |
| `sequence_end` | Optional | End position within a Session or marker |
| `applies_to_remaining_activity` | Optional | Whether the relationship continues through later Sessions |

Session identity is the primary temporal unit. Timestamps remain provenance rather than the primary effective-period model.

Referenced Sessions and Activity Markers must belong to the same Activity identified by `activity_id`.

### 12.2 Status Reason

A Status Reason explains why a record has a particular lifecycle state or Score disposition. It does not replace the state itself.

```yaml
status_reason:
  reason_code: insufficient_specific_evidence
  note: No consequentially usable evidence yet demonstrates the Criterion.
  recorded_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  recorded_at: '2026-09-15T12:10:00-04:00'
```

Conceptual fields are:

| Field | Requirement | Meaning |
|---|---|---|
| `reason_code` | Required | Stable reason category |
| `note` | Optional | Human explanation |
| `related_record` | Optional | Related exception, Event, or external record using the appropriate reference type |
| `recorded_by` | Required | Actor Reference recording the reason |
| `recorded_at` | Required | Time recorded |

Do not replace this shape with shorthand fields such as `code` and `description` when illustrating a contracted Status Reason.

### 12.3 Evidence Locator

An Evidence Locator identifies where relevant material appears inside a broader evidence source.

Conceptual fields are:

| Field | Requirement | Meaning |
|---|---|---|
| `page_number` | Optional | Human-readable page number |
| `source_page_index` | Optional | Source position under the source contract |
| `section_label` | Optional | Section or heading |
| `row_label` | Optional | Row identifier |
| `column_label` | Optional | Column identifier |
| `participant_label` | Optional | Display aid inside the source |
| `session_id` | Optional | Relevant Session |
| `activity_marker_id` | Optional | Relevant Activity Marker |
| `work_item_id` | Optional | Relevant Work Item |
| `note` | Optional | Human-entered locator description |

Example:

```yaml
evidence_locator:
  page_number: 1
  row_label: Student 002
  session_id: ses_seminar_02
  note: Teacher observation of the target integrating two peers' ideas.
```

The Evidence Locator must not contain relationship fields that belong elsewhere. In particular, do not add:

```text
group_id
activity_event_id
artifact_instance_id
criterion_id
score_record_id
```

The evidence source is already identified by `evidence_reference`; Subject or Group relevance belongs in `subject_context`; Event identity belongs in an `activity_event` Evidence Reference.

### 12.4 External Locator

An External Locator identifies an authorized physical or digital location without transferring ownership to Concord.

```yaml
external_locator:
  scheme: institutional_record
  locator: quillan_response_seminar_002
  version_label: Revision 1
  display_label: Student 002 seminar synthesis reflection
  access_hint: Resolve through the authorized Quillan adapter.
```

Conceptual fields are:

| Field | Requirement | Meaning |
|---|---|---|
| `scheme` | Required | Locator scheme or provider-neutral type |
| `locator` | Required | Provider-specific opaque locator |
| `version_label` | Optional | Human-readable version or revision |
| `content_digest` | Optional | Integrity digest where available |
| `display_label` | Optional | Human-facing label |
| `access_hint` | Optional | Non-secret access guidance |

Possible schemes include `https`, `file`, `git`, `cloud_document`, `institutional_record`, and `physical_location`.

Credentials and access tokens must never appear in an External Locator. Availability is tracked independently.

### 12.5 Manifest and Core registry provenance

A Concord Academic Result Manifest uses the shared Concord Provenance value object in `generated_provenance`.

A Core Academic Work Registration, Publication Record, and Publication Withdrawal use their Core-defined timestamps and fields. Do not insert Concord `created_provenance` into those Core records unless the Core contract defines it.

A publication example must preserve at least:

```text
native Score scored_at
manifest generated_at
manifest digest calculation after final bytes exist
Core Publication Record published_at
optional withdrawal withdrawn_at
Meridian import time described downstream
```

These timestamps answer different questions and must not be collapsed into one generic `updated_at`.
## 13. Timestamp Conventions

All timestamps must:

* be synthetic;
* use valid ISO 8601 date-time syntax;
* use two-digit hour, minute, and second components;
* include an explicit UTC offset;
* preserve chronological consistency within a case;
* and not serve as the sole durable identity of a record.

Example:

```text
2026-09-15T10:12:00-04:00
```

Invalid examples include:

```text
2026-09-15T10:72:00-04:00
2026-09-15T10:12:93-04:00
2026-09-15T10:120:00-04:00
```

A later record must not precede the record on which it depends.

Minimum chronology for routed paper evidence and publication:

```text
Artifact Page created
    -> Route Registration created
    -> page rendered
    -> source scanned
    -> Scan Reference created
    -> Review completed
    -> Moderation completed where required
    -> Score recorded
    -> Score Evidence Link created
    -> Concord Academic Result Manifest generated
    -> immutable manifest bytes written
    -> SHA-256 digest calculated
    -> Core Publication Record created
    -> optional Meridian import
```

An Academic Work Registration must exist at the applicable revision before Core accepts an `academic_result_set` Publication Record. Registration may occur before or after native Score creation, but it must not be inferred from the Score timestamp.

A Publication Record’s `published_at` must not predate:

* the manifest’s `generated_at`;
* completion of the exact immutable manifest bytes;
* or the applicable Academic Work Registration revision.

A Publication Withdrawal’s `withdrawn_at` must not predate the Publication Record’s `published_at`.

A Score Evidence Link identifies an existing parent Score Record. Its `created_provenance.timestamp` therefore must be equal to or later than the parent Score’s `scored_at` timestamp.

Pre-score evidence selection or deliberation must not be back-modeled as a Score Evidence Link. A future workflow may define a separate evidence-selection or draft-judgment record if that state requires durable representation.

A superseding record must not predate the record it supersedes. A Correction Record must not predate either the identified error or the replacement record it cites.
## 14. Privacy Conventions

Privacy is record-specific and uses the conceptual Privacy Policy value object.

Initial classifications are:

```text
teacher_restricted
teacher_and_subjects
group_and_teacher
classroom_shared
inherited
external_policy
```

Conceptual fields are:

| Field | Requirement | Meaning |
|---|---|---|
| `classification` | Required | Initial shared classification |
| `audience_references` | Optional | Explicit audience when the classification requires it |
| `policy_reference` | Optional | External policy controlling access |
| `reason` | Optional | Minimal explanation for restriction |
| `inherited_from` | Optional | Parent Concord Record Reference supplying the default |

The foundation defines minimum privacy semantics without claiming final suite-wide ownership of the vocabulary.

Human audience entries use Participant References. Group or contextual audience entries use the field-appropriate Concord or Subject reference rather than a generic record reference.

Each case should demonstrate that:

* a child record may be more restrictive than its parent;
* a child record does not become less restrictive automatically;
* a Score may be visible to its target while supporting evidence remains restricted;
* access to a Score does not imply access to every evidence source;
* peer-observation evidence is restricted by default;
* Moderation rationales may be more restrictive than the resulting Score;
* Author or Subject visibility does not determine full Artifact visibility;
* and privacy is not inferred from record ownership or physical possession.

Example Score privacy:

```yaml
privacy_policy:
  classification: teacher_and_subjects
  audience_references:
  - participant_kind: core_student
    participant_id: stu_001
    owning_system: core
```

Example supporting peer-observation privacy:

```yaml
privacy_policy:
  classification: teacher_restricted
  reason: Student-authored observation awaiting or subject to Moderation.
```

Example inherited Activity default:

```yaml
privacy_policy:
  classification: inherited
  inherited_from:
    record_kind: activity
    record_id: act_seminar_01
```

Sensitive medical, disability, disciplinary, or counseling information must not be copied into Concord merely to explain a privacy restriction.

### Manifest and publication privacy

A Concord Academic Result Manifest has one manifest-level `privacy_classification` representing the minimum access classification for the manifest as a whole.

That field:

* does not authorize every reader;
* does not make more-restricted supporting evidence visible;
* does not override Core registry authorization;
* and does not determine the audience of a Meridian report.

Core publication establishes discoverability under authorized registry access. It does not make the manifest public.

A manifest must minimize sensitive Moderation narrative. Structured status, qualification, permitted use, and privacy classification should be projected when sufficient.

A Meridian import or report may be more restrictive than the producer manifest. It must not become less restrictive automatically merely because Core published the manifest.
## 15. Lifecycle and Status Conventions

Each example should use lifecycle states defined or permitted by the conceptual contracts.

A record’s state must describe its own lifecycle rather than stand in for several unrelated facts.

For example, an Artifact may separately have:

* generation state;
* expected-return state;
* scan state;
* filing state;
* Review state;
* Moderation state;
* scoring-readiness state;
* and supersession state.

The examples must avoid broad ambiguous statuses such as:

```text
complete
```

when the intended meaning is actually:

```text
scan readable
filing confirmed
review complete
moderation accepted
score not yet recorded
```

The publication architecture adds separate lifecycle dimensions:

* Academic Work Registration lifecycle: `planned`, `active`, `closed`, or `cancelled`;
* native Score current or superseded state;
* manifest `record_set_revision`;
* Core Publication Record supersession;
* Publication Withdrawal;
* Core catalog availability or repair state;
* Meridian import compatibility;
* Meridian evidence eligibility;
* Meridian Grade-item membership;
* Meridian Academic Period membership;
* Meridian override state;
* and Meridian report snapshot state.

The examples must not use one broad value such as:

```text
published
```

to mean simultaneously:

```text
manifest generated
Core Publication Record exists
catalog updated
Meridian imported
Score selected for grading
report issued
```

Those are independent facts owned by different layers.
## 16. Correction and Supersession Conventions

Historical records must not be silently rewritten after consequential use.

When a record is corrected:

1. the original record remains available;
2. the same-type replacement identifies what it supersedes;
3. a Correction Record explains the correction when required;
4. the current record can be identified without deleting history;
5. and references to historical decisions remain reproducible.

Same-type supersession example:

```yaml
record_owner: concord
record_kind: score_record
score_record_id: score_seminar_002_revision_2
supersedes_score_record_id: score_seminar_002_revision_1
```

Related Correction Record:

```yaml
record_owner: concord
record_kind: correction_record
correction_id: corr_score_seminar_002
target_reference:
  record_kind: score_record
  record_id: score_seminar_002_revision_1
correction_type: score_revision
reason: Additional reviewed evidence resolved the earlier insufficient-evidence disposition.
correcting_actor:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
corrected_at: '2026-09-16T11:21:00-04:00'
replacement_reference:
  record_kind: score_record
  record_id: score_seminar_002_revision_2
privacy_policy:
  classification: teacher_and_subjects
  audience_references:
  - participant_kind: core_student
    participant_id: stu_002
    owning_system: core
```

`target_reference` and `replacement_reference` above are Concord Record References, so they do not contain `owning_system: concord`.

The replacement must identify the record it supersedes. A replacement becoming current does not make the original record invalid history.

Every illustrated same-type supersession chain must be direct, acyclic, and unbranched.

The successor must identify an existing predecessor, and current state must be derived from the explicit chain rather than timestamps, values, filenames, or identifier ordering.

For Score supersession, the predecessor and successor must belong to the same Activity. A change to the target, Criterion, Score classification, or governing standard requires an explicit Correction Record.

A Correction Record never rewrites a Core-retained source scan.

When a correction creates a replacement, `replacement_reference` is required and must agree with the replacement record’s explicit supersession field.

A Correction Record without a replacement documents the event only. It does not establish a new current record, retarget existing references, or make another record current implicitly.

### Native Score, manifest, and publication histories

The examples must preserve three separate supersession relationships:

```text
Concord Score revision:
score_record_2
    -> supersedes score_record_1
```

```text
Concord manifest revision:
record_set_revision 2
    -> projects the revised publishable state of the record-set series
```

```text
Core publication supersession:
publication_2
    -> supersedes publication_1
```

A native Score supersession does not automatically create either a manifest revision or a Core Publication Record. Concord must generate and publish the changed projection explicitly.

A new manifest revision does not revise a native Score. It may project:

* newly created native records;
* corrected lineage;
* changed Moderation use;
* a manifest-contract migration;
* or another material publication change.

A later Core Publication Record must identify its predecessor explicitly. The current publication head must not be inferred solely from:

* the largest revision number;
* the latest timestamp;
* directory order;
* or filename order.

### Publication withdrawal

A Core Publication Withdrawal is not Score correction or publication supersession.

It records that one exact Publication Record should no longer be ordinarily selected as current data.

If that Publication Record is the series head, withdrawal does not reactivate an earlier predecessor. The series remains without a currently selectable publication until a new successor explicitly supersedes the withdrawn head.

Withdrawal of a historical non-head publication leaves the existing series head unchanged.

Withdrawal:

* preserves the Publication Record;
* preserves the manifest bytes;
* preserves native Concord records;
* preserves prior Meridian imports and calculations;
* and does not create a corrected replacement.

A corrected result requires:

```text
native correction where needed
    -> new manifest revision
    -> new Core Publication Record
```

A withdrawn publication must not be restored by mutating the withdrawal or Publication Record.
## 17. Definition, Version, and Instance Conventions

The examples must distinguish reusable lineages, immutable revisions, and generated classroom records.

### Templates

```text
Template Definition
    -> immutable Template Version
    -> generated Artifact Instance
```

### Packets

```text
Packet Definition
    -> immutable Packet Version
    -> generated Packet Instance
```

A Template Definition or Packet Definition is not the exact historical content used in a classroom Activity.

Generated records must identify the immutable versions from which they were created.

A changed printable design requires a new Template Version.

A changed Packet composition requires a new Packet Version.

### 17.1 Shared Template Version substructure

The examples use one normalized nested notation for the currently conceptual Template Version fields.

```yaml
page_manifest:
- page_number: 1
  page_kind: primary
  return_expected: true
  route_required: true
- page_number: 2
  page_kind: instructional
  return_expected: false
  route_required: false

expected_return_behavior:
  mode: all_declared_return_pages
  required_page_numbers:
  - 1

default_authorship_expectation:
  mode: local:collective_group_author

default_subject_expectation:
  mode: local:represented_group

qr_requirements:
  schema: PDS2
  required_page_numbers:
  - 1
  target_record_kind: artifact_page
```

For consistency across examples:

* use `page_number`, not `logical_page_number`;
* represent authorship and Subject expectations as objects with `mode`;
* use `required_page_numbers`, not `route_required_page_numbers`;
* use an explicit expected-return `mode`;
* include only pages whose `route_required` value is `true` in `qr_requirements.required_page_numbers`;
* and omit `route_id` and `human_fallback` from a non-returned, non-routed Artifact Page.

Initial example-document expected-return modes are:

```text
all_declared_return_pages
selected_declared_return_pages
no_return_expected
```

These nested shapes remain conceptual example notation. They do not claim to establish a production serialization beyond the governing top-level contract fields.
## 18. PDS2 Conventions

Every route-required Concord page uses the released PDS2 architecture.

### Module work identity

```text
module_id = concord
work_id   = activity_id
```

The effective work identity is:

```text
module_id + class_id + work_id
```

The conceptual work root is:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
```

The examples must not introduce a required Core `assignment_id` for Concord.

### QR grammar

```text
PDS2|m=<module_id>|c=<class_id>|w=<work_id>|r=<route_id>
```

Representative example:

```text
PDS2|m=concord|c=cls_ela10_p03|w=act_seminar_01|r=route_seminar_page_001
```

### Route Registration

A normal Concord Route Registration targets an existing Artifact Page:

```yaml
module_id: concord
record_kind: artifact_page
record_id: page_seminar_observation_001
```

The Artifact Page and Route Registration must exist before the page is rendered.

### QR limitations

The QR must not encode:

* student identity;
* Group identity;
* Artifact Author;
* Artifact Subject;
* Score target;
* scorer;
* Criterion;
* standard;
* Score value;
* privacy relationships;
* or full Artifact semantics.

Those meanings resolve through Concord-owned records.

### Source ownership

Core owns:

* retained source scans;
* source-scan identity;
* source-page provenance;
* route parsing;
* route resolution;
* generic failure metadata;
* and generic dispatch.

Concord owns:

* the Artifact Page;
* the Scan Reference;
* filing state;
* Author and Subject associations;
* Review;
* Moderation;
* evidence relationships;
* and Scores.

### Routing and publication are separate

PDS2 routing and Core academic-result publication use the same `ModuleWorkRef` but solve different problems.

```text
PDS2:
physical page
    -> Route Registration
    -> Artifact Page
```

```text
Academic publication:
registered Activity work
    -> Concord Academic Result Manifest
    -> Core Publication Record
    -> Meridian
```

A PDS2 QR, Route Registration, or Artifact Page must not contain:

* Academic Work Registration revision;
* academic intent;
* manifest record-set identity;
* manifest revision;
* Core publication ID;
* publication capabilities;
* manifest digest;
* withdrawal state;
* Grade-item membership;
* Academic Period membership;
* or Meridian policy state.

Likewise, a Core Publication Record does not route a physical page and must not replace an Artifact Page Route Registration.
## 19. Standards and Scoring Conventions

Concord is predominantly standards-based but not standards-exclusive.

Every Activity declares one scoring orientation:

```text
evidence_only
standards_based
mixed
local_criteria_only
```

### `evidence_only`

The Activity collects, files, Reviews, or Moderates evidence but creates no Concord Scores.

It does not require:

* a standards profile;
* Focus Standards;
* Criteria;
* or a Scoring Scale.

### `standards_based`

The Activity’s scored judgments are direct judgments about selected Focus Standards.

It requires:

* one Core `standards_profile_id`;
* one or more ordered `focus_standard_ids`;
* standard-backed Criteria;
* and applicable immutable Scoring Scale revisions.

### `mixed`

The Activity uses both:

* standard-backed Criteria;
* and local Criteria.

It requires one standards profile and one or more ordered Focus Standards.

### `local_criteria_only`

The Activity may create local Scores but no direct standards results.

It does not require standards configuration.

### Scoring orientation is not academic intent

Concord Activity `scoring_orientation` and Core Academic Work Registration `academic_intent` are separate controlled decisions.

Examples must not derive one automatically from the other.

For example, a `standards_based` Activity could be registered as:

* `formative`;
* `summative`;
* `diagnostic`;
* `practice`;
* `feedback_only`;
* or `reporting_only`

according to the teacher’s explicit academic purpose.

Likewise, the existence of a standard-backed Score does not establish that the Activity is summative or included in a Grade.
## 20. Focus Standard Conventions

A standards-based or mixed Activity identifies:

```yaml
standards_profile_id: profile_example
focus_standard_ids:
  - std_example_01
  - std_example_02
```

Focus Standard order is meaningful.

Selecting a Focus Standard does not prove that the standard was:

* taught;
* practiced;
* evidenced;
* assessed;
* demonstrated;
* mastered;
* graded;
* or reported.

A direct Concord standards result exists only through an explicit teacher-approved standard-backed Score.
## 21. Criterion Conventions

Every scored Criterion is classified as:

```text
standard_backed
local
```

### Standard-backed Criterion

A standard-backed Criterion:

* identifies exactly one governing `standard_id`;
* governs one standard selected in the Activity’s Focus Standards;
* defines Activity-specific performance meaning;
* and identifies supported Score-target kinds.

Example:

```yaml
criterion_id: crit_seminar_builds_on_ideas
criterion_kind: standard_backed
standard_id: std_njsls_sl_pe_9_10_1
supported_target_kinds:
  - core_student
```

### Local Criterion

A local Criterion:

* has no governing `standard_id`;
* evaluates an Activity-specific, procedural, organizational, or collaborative expectation;
* may include optional non-governing alignment;
* and must remain distinguishable from a direct standards judgment.

Example:

```yaml
criterion_id: crit_seminar_observer_rotation
criterion_kind: local
alignment_standard_ids:
  - std_njsls_sl_pe_9_10_1
```

The absence of `standard_id` is intentional. A local Criterion has no governing standard, so the field is omitted rather than represented as `null`.

The alignment records instructional relevance only.

A Score against that local Criterion is not a direct rating for the aligned standard.

### Multi-standard behaviors

One direct Score must not govern several standards.

When one behavior supplies evidence for two standards, the example should use:

```text
one evidence source
    -> Score Evidence Link A
    -> standard-backed Criterion A
    -> Score A

one evidence source
    -> Score Evidence Link B
    -> standard-backed Criterion B
    -> Score B
```

A holistic Criterion spanning several standards may instead remain local with non-governing alignment.
## 22. Scoring Scale Conventions

A Scoring Scale is one immutable revision.

The examples may use:

* ordinal proficiency levels;
* categorical judgments;
* numeric ordinal levels;
* binary values;
* or teacher-defined labels.

Example:

```yaml
scoring_scale_id: scale_proficiency_4_rev_1
lineage_id: scale_proficiency_4
levels:
  - value: developing
    label: Developing
  - value: approaching
    label: Approaching
  - value: meeting
    label: Meeting
  - value: exceeding
    label: Exceeding
```

The examples must not assume that:

```text
3 on Scale A = 3 on Scale B
```

Cross-scale comparison, weighting, normalization, mastery, and Grade calculation remain outside Concord.

Points-based rubrics must not be presented as the assumed primary Concord model.
## 23. Score Record Conventions

A Score Record is:

> One teacher-approved judgment about one Criterion for one explicit target in one Activity context using one exact Scoring Scale revision.

Each Score identifies:

* `activity_id`;
* optional `session_id`;
* exactly one target;
* exactly one Criterion;
* Score kind;
* governing `standard_id` when standard-backed;
* one exact Scoring Scale revision;
* one disposition;
* one value only when scored;
* basis;
* scorer;
* scoring timestamp;
* rationale when required;
* Moderation completion;
* privacy;
* and supersession when applicable.

### Standard-backed Score

```yaml
score_kind: standard_backed
standard_id: std_njsls_sl_pe_9_10_1
```

The standard must match the referenced standard-backed Criterion.

### Local Score

```yaml
score_kind: local
```

The governing `standard_id` field is forbidden for a local Score and is therefore omitted rather than written as `null`.

A local Score may appear in the broader Concord Academic Result Manifest but must not enter the direct Standards Result Projection.

### Score target terminology

Use:

```text
Score target
```

Do not use:

```text
Score subject
```

Artifact Subject and Score target are separate concepts.
## 24. Score Disposition Conventions

Initial dispositions include:

```text
scored
insufficient_evidence
absent
excused
not_observed
not_applicable
deferred
```

When:

```text
disposition = scored
```

a valid value from the selected Scoring Scale is required.

When:

```text
disposition != scored
```

the `value` field is forbidden and must be omitted. Do not represent it as `value: null`.

The examples must never convert a non-score disposition automatically into:

* zero;
* the lowest scale level;
* failure;
* or poor performance.

A later valid Score may supersede an earlier non-score disposition while preserving both records.
## 25. Evidence Conventions

Evidence is a role played by several possible record kinds.

Evidence may include:

* an Artifact Instance;
* an Artifact Page;
* a teacher observation;
* a peer observation;
* an Attachment;
* an Activity Event;
* a Contribution Claim;
* a ScoreForm result;
* a Quillan response;
* an external record;
* or documented professional judgment.

The examples use contract-native Evidence References rather than forcing all sources into one universal Evidence entity.

Example Concord Artifact evidence:

```yaml
evidence_reference:
  evidence_kind: artifact_instance
  owning_system: concord
  record_id: art_teacher_tracker_001
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
```

Example Activity Event evidence:

```yaml
evidence_reference:
  evidence_kind: activity_event
  owning_system: concord
  record_id: event_lab_probe_failure_01
```

Example ScoreForm evidence:

```yaml
evidence_reference:
  evidence_kind: scoreform_result
  owning_system: scoreform
  record_id: sf_result_001
  contract_version: '1'
```

An Evidence Reference does not create a Score.

Review does not create a Score.

Moderation does not create a Score.

A standards reference on evidence does not create a standards result.

Evidence ownership remains with the source owner. The reference does not copy or reinterpret the source.
## 26. Score Evidence Link Conventions

Scores and evidence have a many-to-many relationship.

One Score may use several evidence sources.

One evidence source may support several Scores.

Each deliberate use requires a separate Score Evidence Link.

Example:

```yaml
record_owner: concord
record_kind: score_evidence_link
score_evidence_link_id: scoreev_seminar_001
score_record_id: score_seminar_student_001_standard_01
evidence_reference:
  evidence_kind: artifact_instance
  owning_system: concord
  record_id: art_teacher_tracker_001
evidence_locator:
  page_number: 1
  row_label: Student 001
  session_id: ses_seminar_01
subject_context:
  subject_kind: core_student
  subject_id: stu_001
  owning_system: core
relevance_description: Teacher observation of the target building on a peer's comment.
significance: primary
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-15T12:01:00-04:00'
  source_kind: manual
  note: Evidence linked after the parent Score was recorded.
```

Link count does not determine Score value.

Evidence is referenced, not copied.

A Score Evidence Link must satisfy all of the following:

* the parent Score Record already exists;
* the link timestamp is equal to or later than the parent Score’s `scored_at`;
* the evidence source exists or is deliberately external;
* `evidence_kind` is compatible with `owning_system`;
* the Evidence Locator uses only the fields defined in Section 12.3;
* Subject relevance is expressed through `subject_context`, the locator, or the relevance description;
* required Moderation is complete before consequential use;
* and `moderation_record_id` is present when the applicable evidence requires Moderation.

An active consequential link must not cite evidence whose latest applicable Review says `moderation_required`, `awaiting_moderation`, or an equivalent unresolved state unless a completed Moderation Record explicitly permits that use.

Rejected evidence must not remain an active supporting link for a consequential current Score.
## 27. Group and Individual Judgment Conventions

A Group Score and individual Scores are separate judgments.

A Group Score must not automatically create Scores for Group members.

Group or multi-Subject evidence may support an individual Score only when:

* the evidence is relevant to that individual target;
* required Moderation permits the use;
* the teacher makes an explicit individual judgment;
* and the rationale or Score Evidence Link explains the individual relevance.

Group Membership alone does not prove contribution or performance.

Assigned Role or Responsibility alone does not prove contribution or performance.
## 28. Professional Judgment Conventions

A teacher may record a Score without one controlling Artifact.

When no formal evidence link controls the judgment:

* scorer provenance is required;
* an adequate rationale is required;
* the Activity context must be explicit;
* and the record must identify `professional_judgment` or equivalent as its basis.

Example:

```yaml
basis: professional_judgment
rationale: The teacher observed the target across three Sessions and recorded a contextual judgment based on repeated direct observation.
```

This does not permit unexplained or provenance-free scoring.
## 29. Review Conventions

Artifact Review determines administrative and evidentiary readiness.

Review may address:

* scan readability;
* page completeness;
* filing correctness;
* Author attribution;
* Subject attribution;
* privacy;
* relevance;
* Moderation requirement;
* and readiness for possible scoring.

Review does not:

* determine performance;
* establish a standard;
* select a Score target;
* choose a scale value;
* create a Score;
* or calculate a Grade.

### 29.1 Privacy judgment notation

The governing contract describes `privacy_judgment` as the Review’s privacy state but does not define a separate initial vocabulary.

For cross-example consistency, these representative files use the effective Privacy Policy classification judged appropriate:

```text
teacher_restricted
teacher_and_subjects
group_and_teacher
classroom_shared
inherited
external_policy
```

Example:

```yaml
privacy_judgment: teacher_restricted
privacy_policy:
  classification: teacher_restricted
```

Do not use an unqualified value such as `confirmed` in `privacy_judgment`. The Review must state which effective classification was judged appropriate.

The `privacy_policy` remains the actual access policy for the Review record. `privacy_judgment` records the reviewer’s conclusion about the reviewed Artifact’s effective classification.
## 30. Moderation Conventions

Moderation determines whether and how evidence may be used consequentially.

Moderation may produce outcomes such as:

```text
accepted
accepted_with_qualification
insufficient
disputed
rejected
not_used_for_scoring
```

An accepted Moderation decision means only that the evidence may be used under the recorded conditions.

It does not mean:

* the evidence proves high performance;
* the target receives a positive Score;
* or a Score value has been selected.

Rejected evidence is not automatically negative evidence about its Subject.

When an Artifact Review, Evidence Reference, Contribution Claim, or workflow rule says Moderation is required:

1. a Moderation Record must identify the exact evidence source;
2. the Moderation Record must be completed before the evidence is used consequentially;
3. the Moderation decision must permit the represented use;
4. each consequential Score Evidence Link must identify the applicable `moderation_record_id`;
5. the Score’s `moderation_complete` must agree with the linked evidence state;
6. and superseded or rejected Moderation decisions remain available but do not authorize a current active link.

A locator that excludes an unmoderated portion may support use only when the Review and relevance description explicitly establish that the linked portion is independent of the moderated claim.
## 31. External Record Conventions

ScoreForm, Quillan, source-control platforms, cloud-document platforms, CAD systems, and other external authorities retain ownership of their records.

An External Reference is a Concord-owned relationship record, but its required `owning_system` field identifies the external authority. To avoid ambiguity, the examples use `record_owner: concord` only as illustrative envelope notation.

Representative Quillan reference:

```yaml
record_owner: concord
record_kind: external_reference
external_reference_id: extref_seminar_quillan_001
owning_system: quillan
external_record_kind: response
external_record_id: quillan_response_seminar_002
contract_version: '1'
relationship_purpose: supporting_evidence
activity_id: act_seminar_01
session_id: ses_seminar_02
criterion_id: crit_seminar_integrates_discussion
subject_reference:
  subject_kind: core_student
  subject_id: stu_002
  owning_system: core
external_locator:
  scheme: institutional_record
  locator: quillan_response_seminar_002
  display_label: Student 002 seminar synthesis reflection
availability_status: available
last_confirmed_at: '2026-09-16T10:50:00-04:00'
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-16T10:52:00-04:00'
  source_kind: manual
  note: Created after confirming availability through the authorized Quillan adapter.
```

An External Reference may identify:

* owning system;
* external record kind;
* external record identifier;
* contract version where applicable;
* relationship purpose;
* Activity and optional contextual records;
* relevant Subject;
* provider-neutral External Locator;
* availability;
* and creation provenance.

Do not add a `score_record_id` before the referenced Score exists. A later Score Evidence Link can associate the external evidence with the Score without a forward reference.

The external record may support a Concord Score only through an explicit Evidence Reference and Score Evidence Link.

Example Score Evidence Link reference to the External Reference relationship:

```yaml
evidence_reference:
  evidence_kind: external_record
  owning_system: concord
  record_id: extref_seminar_quillan_001
```

An external result does not automatically become a Concord Score.

Concord must not copy a complete external record when a stable reference is sufficient.

### Published external-source lineage

When an external result supports a Concord Score and an exact source Publication Record is known, the later Manifest Evidence-Lineage Projection should preserve both:

```text
source_record_reference
source_publication_reference
```

Example:

```yaml
source_record_reference:
  module_id: scoreform
  record_kind: result
  record_id: sf_result_001
  contract_version: '1'
source_publication_reference:
  publication_id: pub_scoreform_resultset_001
```

The `source_record_reference` identifies the producer-owned result.

The `source_publication_reference` identifies the exact published source state.

The Concord External Reference and Score Evidence Link identify how Concord used that source.

None replaces the others.
## 32. Academic Result Manifest and Publication Conventions

The representative examples must validate the proposed ADR 0015 publication architecture without treating conceptual examples as released runtime APIs.

The governing chain is:

```text
Concord native records
    -> Concord Academic Result Manifest revision
    -> Core Publication Record
    -> Meridian import and policy
```

For `publication_kind: academic_result_set`, the exact Academic Work Registration revision current at publication time is required.

### 32.1 Authority boundaries

The layers answer different questions.

| Layer | Owner | Primary question |
|---|---|---|
| Concord Activity and Scores | Concord | What happened, what evidence was used, and what teacher-approved judgments exist? |
| Academic Work Registration | Core | May this module work participate in academic grading or reporting, and for what broad intent? |
| Concord Academic Result Manifest | Concord | What exact immutable public projection of the Activity’s publishable result state is being offered? |
| Publication Record | Core | Which exact manifest revision is discoverable through the suite registry? |
| Meridian | Meridian | Which publications and results are eligible under grading, Academic Period, proficiency, override, and reporting policy? |

The examples must not collapse these layers.

### 32.2 Core Academic Work Registration

An Academic Work Registration is a Core-owned, revisioned record.

Representative shape:

```yaml
record_owner: core
record_kind: academic_work_registration
schema_version: '1'
record_type: academic_work_registration
work:
  module_id: concord
  class_id: cls_ela10_p03
  work_id: act_seminar_01
registration_revision: 1
producer_contract_version: '1'
title: Evidence and Perspective Seminar
work_kind: collaborative_activity
academic_intent: formative
lifecycle: active
created_at: '2026-09-14T14:35:00-04:00'
updated_at: '2026-09-14T14:35:00-04:00'
source_records:
- module_id: concord
  record_kind: activity
  record_id: act_seminar_01
  contract_version: '1'
```

Core controls the initial `academic_intent` vocabulary:

```text
formative
summative
diagnostic
practice
feedback_only
reporting_only
```

Core controls the initial lifecycle vocabulary:

```text
planned
active
closed
cancelled
```

The initial Concord `work_kind` is:

```text
collaborative_activity
```

Do not invent an `academic_work_registration_id`.

The examples must show that:

* registration is explicit;
* Activity creation does not create registration;
* selecting Focus Standards does not create registration;
* creating Score Records does not create registration;
* registration does not publish results;
* registration does not create Grade-item membership;
* registration does not create Academic Period membership;
* and registration revision history remains separate from Activity history.

### 32.3 Scoring orientation, academic intent, and Meridian policy

The following are independent:

| Concept | Owner | Meaning |
|---|---|---|
| `scoring_orientation` | Concord | Kinds of Concord judgments the Activity may produce |
| `academic_intent` | Core registration | Broad academic purpose of the registered work |
| Grade-item membership | Meridian | Whether the work participates in a particular grading calculation |
| Academic Period membership | Meridian using Core calendar definitions | Which institutional period contains the work or result under policy |

No automatic mapping is permitted.

For example:

```text
scoring_orientation: standards_based
academic_intent: formative
Grade-item membership: excluded
```

is valid.

So is:

```text
scoring_orientation: mixed
academic_intent: summative
Grade-item membership: included under a named Meridian policy
```

The first two values must not determine the third automatically.

### 32.4 Concord Academic Result Manifest

A Concord Academic Result Manifest is an immutable, producer-owned projection of one exact revision of publishable academic-result state for one registered Activity.

Representative shape:

```yaml
record_owner: concord
record_kind: concord_academic_result_manifest
manifest_contract_version: concord_academic_result_manifest_v1
record_set_id: rs_seminar_results_01
record_set_revision: 1
producer_module_id: concord
work:
  module_id: concord
  class_id: cls_ela10_p03
  work_id: act_seminar_01
source_activity:
  module_id: concord
  record_kind: activity
  record_id: act_seminar_01
  contract_version: '1'
generated_at: '2026-09-16T12:30:00-04:00'
generated_provenance:
  actor:
    actor_kind: system
    actor_id: publisher_concord_001
    owning_system: concord
    display_label_snapshot: Concord academic-result publisher
  timestamp: '2026-09-16T12:30:00-04:00'
  source_kind: system
  application_version: synthetic-concord-0.1
  note: Generated from validated canonical Concord records.
activity_context:
  activity_id: act_seminar_01
  class_id: cls_ela10_p03
  title_snapshot: Evidence and Perspective Seminar
  activity_type: local:socratic_seminar
  scoring_orientation: standards_based
  standards_profile_id: profile_njsls_ela_2023_09_10
  focus_standard_ids:
  - std_njsls_sl_pe_9_10_1
  - std_njsls_rl_cr_9_10_1
  activity_status_snapshot: completed
  session_references:
  - record_kind: session
    record_id: ses_seminar_01
criterion_projections:
- criterion_id: crit_seminar_builds_on_ideas
  criterion_set_id: critset_seminar_standards_rev_1
  key: builds_on_ideas
  label: Builds on peers' ideas
  definition: Builds on peers' ideas and responds substantively during collaborative discussion.
  criterion_kind: standard_backed
  standard_id: std_njsls_sl_pe_9_10_1
  supported_target_kinds:
  - core_student
  status_snapshot: active
scoring_scale_projections:
- scoring_scale_id: scale_proficiency_4_rev_1
  lineage_id: scale_proficiency_4
  name: Four-Level Proficiency Scale
  revision: 1
  scale_type: ordinal
  levels:
  - value: developing
    label: Developing
    meaning: Evidence does not yet demonstrate the Criterion consistently.
    ordering: 1
    description: Initial evidence is limited or inconsistent.
  - value: approaching
    label: Approaching
    meaning: Evidence partially demonstrates the Criterion.
    ordering: 2
    description: Performance is emerging but not yet consistent.
  - value: meeting
    label: Meeting
    meaning: Evidence demonstrates the Criterion at the expected level.
    ordering: 3
    description: Performance is consistent in the represented context.
  - value: exceeding
    label: Exceeding
    meaning: Evidence demonstrates the Criterion with unusual depth or consistency.
    ordering: 4
    description: Performance extends beyond the expected contextual level.
  intended_use: standards_based
  aggregation_guidance: Treat as contextual evidence; do not infer longitudinal proficiency.
  status_snapshot: active
score_projections:
- score_record_id: score_seminar_student_002_builds_ideas
  activity_id: act_seminar_01
  session_id: ses_seminar_01
  target_reference:
    target_kind: core_student
    target_id: stu_002
    owning_system: core
  criterion_id: crit_seminar_builds_on_ideas
  score_kind: standard_backed
  standard_id: std_njsls_sl_pe_9_10_1
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-16T12:00:00-04:00'
  rationale: Moderated peer evidence corroborated the teacher's direct observation.
  moderation_complete: true
  current_status: current
  privacy_classification: teacher_and_subjects
score_evidence_link_projections:
- score_evidence_link_id: scoreev_seminar_peer_002
  score_record_id: score_seminar_student_002_builds_ideas
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_observation_002
    subject_context:
      subject_kind: core_student
      subject_id: stu_002
      owning_system: core
    moderation_requirement: required
  source_record_reference:
    record_kind: artifact_instance
    record_id: art_seminar_peer_observation_002
  evidence_locator:
    page_number: 1
    section_label: Builds on ideas
    session_id: ses_seminar_01
    note: Specific observation of the target responding to a peer.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  relevance_description: The observation corroborates the teacher's evidence for the target's response to a peer.
  significance: corroborating
  moderation_record_id: mod_seminar_peer_observation_002
  status: current
moderation_projections:
- moderation_record_id: mod_seminar_peer_observation_002
  target_evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_observation_002
    subject_context:
      subject_kind: core_student
      subject_id: stu_002
      owning_system: core
    moderation_requirement: required
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  status: accepted_with_qualification
  permitted_use: may_support_one_named_subject_only
  qualification: May corroborate the teacher's observation but may not independently determine the Score.
  moderated_at: '2026-09-16T11:45:00-04:00'
  privacy_classification: teacher_restricted
standards_result_projection:
- module_id: concord
  class_id: cls_ela10_p03
  activity_id: act_seminar_01
  session_id: ses_seminar_01
  score_record_id: score_seminar_student_002_builds_ideas
  target_reference:
    target_kind: core_student
    target_id: stu_002
    owning_system: core
  standard_id: std_njsls_sl_pe_9_10_1
  criterion_id: crit_seminar_builds_on_ideas
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: scored
  value: meeting
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-16T12:00:00-04:00'
  evidence_link_ids:
  - scoreev_seminar_peer_002
  moderation_complete: true
  current_status: current
privacy_classification: teacher_restricted
```

The YAML above illustrates the contract shape. It is not the exact byte block used for digest validation.

The manifest is not a replacement for the canonical native records. It is authoritative only as the exact Concord-produced projection identified by its record-set series, revision, contract version, and immutable bytes.

### 32.5 Record-set identity and scope

The initial architecture uses one academic-result record-set series per registered Concord Activity.

The `record_set_id` must be:

* stable;
* unique within the Activity work context;
* safe under Core identifier rules;
* independent of display labels;
* free of direct PII;
* and never reused for another logical publication series.

The `record_set_id` is not:

* `activity_id`;
* `score_record_id`;
* `publication_id`;
* a filename;
* a Grade-item ID;
* or an Academic Period ID.

A manifest is scoped to exactly one:

```text
module_id + class_id + activity_id
```

It must not become an implicit cross-Activity, class-wide, marking-period, course, or school-year aggregate.

### 32.6 Manifest inclusion rules

A manifest may include:

* current standard-backed Scores;
* current local Scores;
* explicit non-score dispositions;
* superseded Score Records required to understand native history;
* exact Criterion projections;
* exact Scoring Scale projections;
* deliberate evidence-use lineage;
* applicable Moderation state;
* and a direct standards-only subset.

The initial `academic_result_set` contract does not publish raw evidence-only Activities merely because reviewed evidence exists.

An evidence-only Activity should therefore demonstrate:

```text
Activity exists
registration absent unless separately justified
academic-result manifest absent
Core Publication Record absent
```

A later evidence-publication contract may define another publication kind or manifest.

### 32.7 Manifest Activity Context

The Activity context must include:

```text
activity_id
class_id
title_snapshot
activity_type
scoring_orientation
conditional standards_profile_id
conditional ordered focus_standard_ids
activity_status_snapshot
optional session_references
```

It must not include authoritative:

```text
academic_intent
Grade-item membership
academic_period_id
proficiency
course Grade
report state
```

Activity scoring orientation does not substitute for Core registration lifecycle or academic intent.

### 32.8 Manifest Criterion Projection

Each included Score must reference one included Criterion projection with:

```text
criterion_id
criterion_set_id
key
label
definition
criterion_kind
conditional standard_id
optional alignment_standard_ids
supported_target_kinds
status_snapshot
```

Rules:

* a standard-backed Criterion has exactly one governing `standard_id`;
* a local Criterion has no governing `standard_id`;
* local alignment remains non-governing;
* and Meridian must not split one local or holistic Criterion result across several standards.

### 32.9 Manifest Scoring Scale Projection

Each included Score must reference one included exact Scoring Scale revision with:

```text
scoring_scale_id
lineage_id
name
revision
scale_type
levels
optional intended_use
optional aggregation_guidance
status_snapshot
```

A bare scale ID is insufficient when downstream interpretation cannot resolve the exact semantics independently.

Every projected level should preserve, as applicable:

* machine value;
* display label;
* meaning;
* ordering;
* and description.

Concord does not normalize the scale to points, percentage, letter Grade, or universal proficiency.

### 32.10 Manifest Score Projection

Each Score projection preserves:

```text
score_record_id
activity_id
optional session_id
target_reference
criterion_id
score_kind
conditional standard_id
scoring_scale_id
disposition
conditional value
basis
scorer
scored_at
optional rationale
moderation_complete
current_status
optional supersedes_score_record_id
privacy_classification
```

A standard-backed Score:

```text
score_kind: standard_backed
standard_id: required
```

A local Score:

```text
score_kind: local
standard_id: forbidden
```

A local Score may appear in the broader manifest. It must not appear in the direct Standards Result Projection.

When `disposition != scored`, `value` is forbidden.

Native Score supersession remains explicit. A later timestamp alone does not establish supersession.

### 32.11 Manifest Evidence-Lineage Projection

A manifest must expose deliberate evidence use without copying complete source evidence.

Each lineage projection includes:

```text
score_evidence_link_id
score_record_id
evidence_reference
source_record_reference
optional source_publication_reference
optional evidence_locator
optional subject_context
relevance_description
optional significance
conditional moderation_record_id
status
```

For Concord-owned evidence:

```yaml
source_record_reference:
  record_kind: artifact_instance
  record_id: art_teacher_tracker_001
```

For an external producer result:

```yaml
evidence_reference:
  evidence_kind: external_record
  owning_system: concord
  record_id: extref_lab_scoreform_001
source_record_reference:
  module_id: scoreform
  record_kind: result
  record_id: sf_result_lab_001
  contract_version: '1'
source_publication_reference:
  publication_id: pub_scoreform_lab_results_001
```

The three relationships remain distinct:

```text
originating producer result
    -> conditional exact Core source publication
    -> Concord evidence relationship and teacher-approved Score
```

This lineage is required because Meridian may import both:

* the originating ScoreForm or Quillan publication;
* and the Concord publication whose Score used that result as evidence.

Concord supplies the relationship. Meridian owns overlap and deduplication policy.

The examples must not present related producer results as independent merely because they arrived through separate publications.

### 32.12 Manifest Moderation Projection

When an active consequential evidence link requires Moderation, the manifest includes sufficient structured state to validate the represented use:

```text
moderation_record_id
target_evidence_reference
optional target_subject_references
status
permitted_use
conditional qualification
moderated_at
privacy_classification
```

The projection should minimize sensitive narrative.

It must preserve a material qualification.

Rejected evidence must not remain an active supporting lineage row.

Moderation does not determine the Criterion, target, or Score value.

### 32.13 Standards Result Projection

The Standards Result Projection is the direct standards-only subset inside the broader manifest.

It replaces the earlier standalone “Standards Result Handoff Projection” as the representative publication form.

Each row includes:

```text
module_id
class_id
activity_id
optional session_id
score_record_id
target_reference
standard_id
criterion_id
scoring_scale_id
disposition
conditional value
scorer
scored_at
optional evidence_link_ids
moderation_complete
optional supersedes_score_record_id
current_status
```

Rules:

* only standard-backed Scores appear;
* local Scores are excluded;
* non-score dispositions remain explicit;
* Group and individual targets remain distinct;
* exact scale identity is preserved;
* native Score supersession is preserved;
* and no mastery, Grade, weight, average, growth, or Academic Period membership is calculated.

The row has no independent `handoff_id` under the current contract.

### 32.14 Manifest storage and digest

A published manifest is stored beneath the exact Concord Activity work root:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
  exports/manifests/<record_set_id>/<record_set_revision>.json
```

Example:

```text
classes/cls_ela10_p03/modules/concord/work/act_seminar_01/
  exports/manifests/rs_seminar_results_01/1.json
```

The path must be:

* workspace-relative;
* normalized;
* inside the workspace;
* inside the exact Activity work root;
* outside Core-owned registry storage;
* and revision-addressed.

A mutable convenience path such as:

```text
exports/latest.json
```

may exist but must not be the canonical target of a Publication Record.

The SHA-256 digest must be calculated from the exact final immutable bytes.

Principal examples that claim a valid publication must use a mechanically calculated lowercase 64-character SHA-256 digest. A prose placeholder does not satisfy the mechanical audit.

After publication:

* bytes must not change;
* the path must not be repointed;
* and a digest mismatch is an integrity failure rather than an update.

### 32.15 Core Publication Record

A Core Publication Record announces one exact manifest revision.

Representative shape:

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_seminar_results_001
work:
  module_id: concord
  class_id: cls_ela10_p03
  work_id: act_seminar_01
source_record:
  module_id: concord
  record_kind: activity
  record_id: act_seminar_01
  contract_version: '1'
publication_kind: academic_result_set
capabilities:
- criterion_scores
- standards_ratings
- moderated_scores
record_set_id: rs_seminar_results_01
record_set_revision: 1
manifest_contract_version: concord_academic_result_manifest_v1
manifest_path: classes/cls_ela10_p03/modules/concord/work/act_seminar_01/exports/manifests/rs_seminar_results_01/1.json
manifest_digest_algorithm: sha256
manifest_digest: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
published_at: '2026-09-16T12:32:00-04:00'
academic_work_registration_revision: 1
```

The digest above demonstrates shape only. A principal case must replace it with the actual digest of its exact represented manifest bytes.

The Publication Record:

* is not the manifest;
* does not copy result arrays into Core;
* does not transfer result ownership to Core;
* does not authorize access by itself;
* and does not create Grade eligibility.

### 32.16 Publication kind and capabilities

Concord uses:

```text
publication_kind: academic_result_set
```

Initial relevant capabilities are:

```text
criterion_scores
standards_ratings
moderated_scores
```

Capabilities must be truthful for the exact manifest.

For the initial Concord manifest contract:

* include `criterion_scores` when any Criterion-level Score projection or non-score disposition is present;
* include `standards_ratings` when any standard-backed Score projection or disposition is present;
* when `standards_ratings` is included, require a nonempty Standards Result Projection that exactly represents the standard-backed subset;
* include `moderated_scores` when interpretation of at least one included consequential Score depends on projected Moderation state;
* omit each capability when its represented feature is absent.

Capabilities are discovery metadata.

They do not establish:

* authorization;
* completeness for every target;
* numeric scoring;
* Grade eligibility;
* Academic Period membership;
* or universal educational meaning.

### 32.17 Required publication workflow

A valid publication example must preserve this order:

1. validate the Activity and native publishable records;
2. verify the exact Academic Work Registration revision currently selected by Core;
3. determine the exact result projection;
4. assign a new valid `record_set_revision`;
5. generate complete manifest bytes;
6. validate the manifest contract;
7. write a new revision-addressed immutable file;
8. durably close the file;
9. calculate the SHA-256 digest;
10. request Core publication;
11. validate registration, publication envelope, path scope, and digest;
12. let Core exclusively create the immutable Publication Record;
13. update or later rebuild the derived Core catalog;
14. report canonical publication success accurately.

Failure boundaries:

* a valid native Score remains valid if publication fails;
* a manifest file without a Publication Record is unpublished;
* a failed publication request creates no Publication Record;
* canonical publication success remains valid if the derived catalog update fails;
* catalog repair does not rewrite the manifest or Publication Record;
* and catalog failure must not be misreported as total publication failure after canonical publication succeeds.

### 32.18 Manifest revision

A new `record_set_revision` is required when the published projection changes materially.

Examples include:

* a new publishable Score;
* native Score supersession;
* target correction;
* governing-standard correction;
* scored-to-non-score or non-score-to-scored change;
* addition or removal of a consequential evidence link;
* changed Moderation permitted use;
* evidence-lineage correction;
* Criterion projection correction;
* Scoring Scale projection correction;
* privacy projection correction;
* or manifest-contract migration.

A native change that does not alter the published projection need not force a new manifest revision.

The manifest revision is not:

* a Score revision;
* a registration revision;
* a Core publication schema version;
* or a Meridian calculation revision.

### 32.19 Idempotency

Repeating the same publication request must reconcile to the existing successful Publication Record when all of the following are unchanged:

```text
work
source_record
publication_kind
capabilities
record_set_id
record_set_revision
manifest_contract_version
manifest_path
manifest_digest_algorithm
manifest_digest
academic_work_registration_revision
supersedes_publication_id
```

For an initial publication, `supersedes_publication_id` is absent.

For a superseding publication, `supersedes_publication_id` must identify the exact expected predecessor.

Core-owned `publication_id` and `published_at` are publication results rather than caller-supplied replay-identity fields.

Any difference in the listed fields for the same logical record-set revision is an integrity conflict.

Changed manifest content or changed publication semantics require a new `record_set_revision`.

The examples must not model a conflicting request as an ordinary update or successful idempotent replay.

### 32.20 Publication supersession

A later Publication Record may supersede an earlier Publication Record only within the same:

```text
producer module
ModuleWorkRef
publication_kind
record_set_id
```

It must:

* use a greater `record_set_revision`;
* identify `supersedes_publication_id`;
* and point to a new immutable manifest revision.

Representative successor fields:

```yaml
publication_id: pub_seminar_results_002
record_set_id: rs_seminar_results_01
record_set_revision: 2
supersedes_publication_id: pub_seminar_results_001
```

Core publication supersession does not imply that every included native Score was superseded.

Native Score supersession does not imply that a Core successor publication exists.

### 32.21 Core Publication Withdrawal

Core represents withdrawal as a separate immutable record.

A withdrawn series head remains the structural head but is not currently selectable. Its predecessor does not become current again.

A corrected replacement must be a new Publication Record that explicitly supersedes the withdrawn head.

Representative shape:

```yaml
record_owner: core
record_kind: publication_withdrawal
schema_version: '1'
record_type: publication_withdrawal
publication_id: pub_project_results_001
withdrawn_at: '2026-10-20T16:05:00-04:00'
reason: The manifest exposed incorrect evidence lineage and must not be selected as current data.
```

Withdrawal:

* does not delete the Publication Record;
* does not delete the manifest;
* does not delete or revise native Concord records;
* does not rewrite prior Meridian calculations;
* and does not create a corrected result.

A replacement requires a new manifest revision and new Publication Record.

### 32.22 Derived Core catalog

The Core registry catalog is a rebuildable discovery accelerator.

The examples must not treat it as authoritative.

A catalog row:

* does not create a registration;
* does not create a Publication Record;
* does not establish the current head independently;
* does not withdraw a publication;
* and does not authorize Meridian consumption.

A case may describe catalog failure or repair in prose. It should not invent catalog rows as foundational domain records.

### 32.23 Meridian consumption boundary

Meridian consumes Concord publications through Core.

A Meridian-consumption discussion should preserve at least:

```text
Core publication_id
exact manifest digest
manifest contract version
record_set_id
record_set_revision
Academic Work Registration revision
source Activity reference
withdrawal state
import time
```

Meridian then applies explicit policy for:

* publication eligibility;
* Grade-item membership;
* Score eligibility;
* direct standards-evidence eligibility;
* local Score use in conventional or hybrid grading;
* repeated-evidence selection;
* reassessment;
* cross-producer overlap;
* scale mapping;
* Academic Period membership;
* proficiency calculation;
* Grade calculation;
* overrides;
* and reporting.

The representative examples must not invent a complete Meridian record body unless a governing Meridian contract defines it.

### 32.24 Cross-producer overlap

When Concord used a ScoreForm or Quillan result and Meridian also imports the originating producer publication, Meridian must apply explicit policy.

Possible policy outcomes may include:

* use both while preserving the relationship;
* select the Concord teacher judgment;
* select the originating producer result;
* treat one as corroborating evidence;
* or exclude one to prevent double-counting.

The example must not prescribe one universal policy.

Concord supplies lineage.

Meridian owns selection and deduplication.

### 32.25 Meridian overrides

A Concord Score revision changes the producer-native teacher judgment.

A Meridian override changes a Meridian-derived selection, proficiency, Grade, or other supported derived result.

A Meridian override must not:

* rewrite a Concord Score;
* create a new Concord Score;
* mutate a manifest;
* mutate a Core Publication Record;
* or create publication supersession.

A changed underlying Concord judgment requires:

```text
new Concord Score
    -> new manifest revision
    -> new Core Publication Record
```

A Meridian-only policy or override change requires no Concord republication.

### 32.26 Academic Period and reporting boundary

Core owns Academic Period definitions and calendar revisions.

Meridian owns policy assigning work and evidence to those periods.

Concord preserves native dates but does not infer authoritative period membership from them.

The initial Concord manifest must not require or invent:

```text
academic_period_id
marking_period_id
term_id
```

A Meridian calculation or report associated with a period must preserve the exact Core calendar revision used.

A Concord manifest is not a formal report.

A later Concord publication must not silently rewrite an issued Meridian report snapshot.
## 33. Optional Structure Conventions

The following records are optional:

* Activity Marker;
* Work Item;
* Work-Item Dependency;
* Activity Event;
* Contribution Claim;
* Responsibility Assignment;
* child Group;
* Attachment;
* and specialized External References.

An example should instantiate one only when the Activity meaningfully requires it.

The absence of an optional record is not a deficiency.

Activity-specific vocabulary must not become a universal foundation requirement.

For example:

* a seminar may use rotations without requiring project milestones;
* a laboratory may use trials without requiring software builds;
* a project may use Work Items without requiring every Concord Activity to become a project-management system.

Academic Work Registration and academic-result publication are optional at the Activity level but not optional inside a case that claims a valid `academic_result_set` Publication Record.

A case may validly demonstrate:

```text
Activity exists
Scores exist
registration absent
manifest absent
publication absent
```

when the teacher has not registered or published the work.

A case must not demonstrate:

```text
Publication Record exists
Academic Work Registration absent
```

for `publication_kind: academic_result_set`.

A source Publication Record reference is optional when the external producer result has not been published or the exact publication is unknown. Its absence must be explicit when cross-producer lineage is being evaluated.
## 34. Omission Conventions

Each principal example should include a section titled:

```text
Contracts Deliberately Not Used
```

This section should identify foundation capabilities that the case does not need.

Example:

```text
The seminar case does not instantiate Work-Item Dependencies because the Activity does not include dependent task execution. Their absence is deliberate and does not indicate that the shared model cannot support them.
```

This prevents the representative examples from implying that every valid Activity must instantiate every available contract.

Publication-related omissions should use equally explicit language.

Example:

```text
The evidence-only Activity is not registered as academic work and has no Concord Academic Result Manifest or Core Publication Record. This is deliberate: reviewed evidence alone does not create an academic-result publication.
```

Example:

```text
The source Quillan response is referenced by module record identity, but no source Publication Record is known. The Manifest Evidence-Lineage Projection therefore omits source_publication_reference rather than inventing one.
```
## 35. Validation Method

Each case must be validated in six ways.

### 35.1 Record completeness

Confirm that every included record is represented either as a complete record body or through a formally defined compact representation containing every required and conditionally required conceptual field. A record inventory or identifier-only table is not sufficient.

Confirm that every included record clearly expresses:

* purpose;
* ownership;
* identity;
* significant required fields;
* significant optional fields;
* references;
* cardinality;
* lifecycle;
* mutability;
* provenance;
* privacy;
* supersession;
* and invariants.

Repeated records may use complete YAML arrays to avoid excessive headings, provided each array item remains contract-complete.

### 35.2 Relationship integrity

Confirm that:

* all referenced records exist or are deliberately external;
* every nested reference uses the correct contract-native reference type;
* target kinds match target identifiers;
* records refer to the correct Activity;
* immutable revisions are used consistently;
* supersession chains are coherent;
* Moderation requirements and Score Evidence Links agree;
* manifest projections resolve to canonical native records;
* Core records reference the exact `ModuleWorkRef`;
* and chronology is valid.

### 35.3 Architectural invariants

Confirm that the example preserves all applicable PDS2, evidence, authorship, Review, Moderation, scoring, standards, privacy, publication, Meridian-boundary, and history rules.

### 35.4 Publication integrity

For every claimed academic-result publication, confirm that:

* an applicable Academic Work Registration revision exists;
* the Activity `scoring_orientation` was not used as an inferred `academic_intent`;
* the manifest belongs to one exact Activity work context;
* the `record_set_id` is stable;
* `record_set_revision` is positive and coherent;
* all projected Scores, Criteria, Scales, evidence links, and Moderation records resolve;
* the manifest path is revision-addressed and inside the exact Activity work root;
* the digest is computed from the exact final bytes;
* the Publication Record matches the manifest identity, path, contract, and digest;
* capabilities are truthful;
* publication supersession is explicit;
* withdrawal preserves history;
* and no Grade, proficiency, Academic Period membership, or Meridian override state appears in the manifest.

### 35.5 Cross-case consistency

Confirm that the same conceptual term and nested notation have the same meaning in all three cases.

For example:

* `Artifact Subject` must not mean one thing in the seminar and another in the laboratory;
* `Score target` must not be replaced by `Score subject` in the project;
* `privacy_judgment` must use the shared classification convention;
* Template Version nested structures must use the normalized Section 17.1 notation;
* a local Criterion must not become a direct standards result in one case merely because that is convenient;
* one case must not treat publication as Grade inclusion while another does not;
* and source producer lineage must not disappear when the evidence comes from ScoreForm or Quillan.

### 35.6 Mechanical audit checks

Before a case or the cross-example validation may declare `PASS`, run or perform equivalent checks for:

1. successful parsing of every fenced YAML block and every exact published-manifest JSON block;
2. valid offset-aware ISO 8601 timestamps;
3. unique durable identifiers within the represented scope;
4. agreement between inventory counts and represented records;
5. resolution of every internal reference;
6. compatibility of reference kind and referenced record;
7. parent-before-child and dependency chronology;
8. Score Evidence Link creation at or after parent Score creation;
9. completed required Moderation before consequential evidence use;
10. Score value membership in the exact referenced scale;
11. omission of `value` for non-score dispositions;
12. standard-backed Score and Criterion standard agreement;
13. exclusion of local Scores from the direct Standards Result Projection;
14. inclusion of local Scores only in the broader manifest where represented;
15. correct PDS2 route targets and no route for declared non-returned instructional pages;
16. coherent duplicate, rescan, misroute, correction, and native supersession history;
17. absence of unsupported Evidence Locator fields;
18. exact `ModuleWorkRef` agreement among Activity, registration, manifest, and publication;
19. applicable Academic Work Registration revision for every `academic_result_set` Publication Record;
20. non-inference of registration from Activity, standards selection, or Score existence;
21. stable `record_set_id` and positive increasing `record_set_revision`;
22. uniqueness of each logical manifest revision;
23. complete Criterion and Scoring Scale projections for every included Score;
24. consistency between manifest Score projections and canonical native Scores;
25. complete source-record lineage for every projected evidence use;
26. source Publication Record lineage whenever the source revision was resolved through or verified against an exact Core publication;
27. truthful publication capabilities;
28. revision-addressed manifest path contained within the exact Activity work root;
29. lowercase 64-character SHA-256 digest syntax;
30. mechanical digest equality with the exact final manifest bytes;
31. Publication Record agreement with manifest path, contract version, record-set identity, revision, and digest;
32. idempotent replay of an identical publication request;
33. rejection of contradictory reuse of one logical manifest revision;
34. explicit same-series publication supersession with a greater record-set revision;
35. separation of native Score supersession from Core publication supersession;
36. preservation of manifest and Publication Record after withdrawal;
37. absence of `academic_period_id`, Grade eligibility, proficiency, or Meridian override state from the initial manifest;
38. preservation of Group versus individual targets;
39. preservation of non-score dispositions without numeric substitution;
40. and preservation of cross-producer lineage sufficient for Meridian overlap policy.

A prose assertion of compliance does not override a failed mechanical, relationship, digest, or publication check.
## 36. Required Validation Findings

Each principal example must end with the following sections.

### Represented Cleanly

Identify the parts of the case that the conceptual contracts express without ambiguity.

### Optional Structures Used

Identify optional records used by the case and explain why each is justified.

### Contracts Deliberately Not Used

Identify foundation contracts that the case did not require.

This section must address registration and publication explicitly, even when absent.

### Publication Validation

State:

* whether the Activity is registered;
* which Academic Work Registration revision applies;
* whether an academic-result manifest exists;
* the record-set identity and revision;
* whether Core publication exists;
* the publication ID and capabilities;
* whether publication supersession or withdrawal is represented;
* and whether the case claims exact source-publication lineage for external evidence.

Use:

```text
Not registered or published by design.
```

when appropriate.

### Meridian Boundary

State what Meridian could consume and which decisions remain policy-owned by Meridian.

The section must explicitly confirm that publication does not establish:

* Grade-item membership;
* Academic Period membership;
* proficiency;
* Grade;
* or report status.

### Tensions or Ambiguities

Identify any unclear terminology, lifecycle rule, cardinality, ownership boundary, validation question, or release-status dependency.

Use:

```text
None identified.
```

when appropriate.

### Workarounds Rejected

Identify tempting but architecturally invalid shortcuts that were deliberately avoided.

### Contract Changes Required

Use:

```text
None.
```

when the case fits the existing architecture.

Otherwise, identify:

* the governing file;
* the exact conflicting or missing semantic rule;
* the proposed correction;
* whether an ADR is required;
* and whether the issue concerns an accepted contract, proposed ADR 0015, or an unreleased Core/Meridian contract.
## 37. Prohibited Workarounds

The examples must not:

* use PDS1 as the active route model;
* require a student identity in every route;
* use a Group identifier as `student_id`;
* introduce a required Core `assignment_id` for Concord;
* store Concord work in an unqualified assignment directory;
* encode Authors, Subjects, standards, Criteria, or Scores in a QR;
* create a route before its Artifact Page exists;
* use a mutable Packet Definition as the exact historical packet composition;
* embed one Author or Subject field directly on an Artifact instead of association records;
* infer sole authorship from recorder status, handwriting, possession, file ownership, or account ownership;
* infer contribution from Membership, Role, or Responsibility Assignment;
* use generic `standard_references` as a substitute for one governing `standard_id`;
* assign several governing standards to one standard-backed Criterion;
* duplicate one Score across several standards;
* treat non-governing alignment as a standards result;
* treat a Group Score as member Scores;
* treat Group evidence as an individual Score without explicit teacher judgment;
* convert missing evidence into zero or the lowest scale value;
* treat Review as Scoring;
* treat Moderation acceptance as a Score;
* treat one Score as mastery or a course Grade;
* copy ScoreForm or Quillan records into Concord ownership;
* make external file or repository ownership equivalent to Artifact authorship;
* use an unrestricted extension object to conceal a missing shared concept;
* create an Academic Work Registration automatically from Activity existence;
* infer Core `academic_intent` from Concord `scoring_orientation`;
* duplicate Core registration fields onto the Concord Activity as authoritative state;
* create an `academic_result_set` Publication Record without an applicable Academic Work Registration revision;
* represent an evidence-only Activity as an academic-result publication merely because evidence exists;
* invent `manifest_id`, `academic_work_registration_id`, or `publication_withdrawal_id`;
* use one mutable `latest.json` file as the canonical published manifest;
* modify manifest bytes after publication;
* reuse one `record_set_revision` for different bytes, paths, digests, or contract versions;
* infer the current publication head solely from timestamp, filename, directory order, or highest revision;
* treat native Score supersession as automatic Core publication supersession;
* treat Core publication supersession as native Score correction;
* delete a manifest or Publication Record to simulate withdrawal;
* treat the derived Core catalog as authoritative;
* write Core registry records directly from Concord;
* declare untruthful publication capabilities;
* publish a bare Score ID without Criterion and exact Scoring Scale semantics;
* expose only a Concord `score_evidence_link_id` while omitting the underlying source-record lineage;
* hide known ScoreForm or Quillan source publication lineage;
* assume two producer publications are independent when one result was used to create the other;
* treat publication as authorization, Grade eligibility, or Academic Period membership;
* place authoritative `academic_period_id`, proficiency, Grade, or report state in the initial Concord manifest;
* encode Meridian evidence-selection, scale-mapping, or grading policy inside the Concord manifest;
* mutate a Concord Score or manifest to represent a Meridian override;
* treat a Meridian report snapshot as the Concord source record;
* claim unreleased Core registry APIs are part of `pds-core` 0.5;
* or mark a conceptual publication example as executable runtime behavior without a released compatible API.
## 38. Cross-Example Validation

The final `cross-example-validation.md` document should compare, at minimum:

| Requirement | Seminar | Laboratory | Project |
|---|---|---|---|
| Standards-based orientation | | | |
| Mixed orientation | | | |
| Evidence-only behavior | | | |
| Local-only judgment | | | |
| Individual Score target | | | |
| Group Score target | | | |
| Multi-Subject evidence | | | |
| Teacher-authored evidence | | | |
| Peer or student-created evidence | | | |
| Moderation | | | |
| External ScoreForm evidence | | | |
| External Quillan evidence | | | |
| External project evidence | | | |
| Membership change | | | |
| Role rotation or reassignment | | | |
| Responsibility Assignment | | | |
| Packet and Template versioning | | | |
| PDS2 route with no student Subject | | | |
| Duplicate, rescan, or correction | | | |
| Standard-backed Criterion | | | |
| Local Criterion | | | |
| Non-governing alignment | | | |
| Non-score disposition | | | |
| Native Score correction or supersession | | | |
| Explicit Academic Work Registration | | | |
| Activity present without automatic registration | | | |
| Scoring orientation distinct from academic intent | | | |
| Concord Academic Result Manifest | | | |
| Stable record-set identity | | | |
| Manifest revision | | | |
| Exact Criterion projection | | | |
| Exact Scoring Scale projection | | | |
| Standard-backed Score projection | | | |
| Local Score in broader manifest | | | |
| Local Score excluded from Standards Result Projection | | | |
| Manifest Evidence-Lineage Projection | | | |
| Exact source Publication Record lineage | | | |
| Manifest Moderation Projection | | | |
| Standards Result Projection | | | |
| Revision-addressed manifest path | | | |
| Mechanical SHA-256 binding | | | |
| Core Publication Record | | | |
| Truthful capabilities | | | |
| Idempotent publication replay | | | |
| Publication supersession | | | |
| Publication withdrawal | | | |
| Derived Core catalog treated as nonauthoritative | | | |
| Meridian cross-producer overlap boundary | | | |
| Meridian override distinct from Concord revision | | | |
| No Academic Period ID in producer manifest | | | |
| Publication does not imply Grade inclusion | | | |

The matrix should record both:

* where a capability is exercised;
* where its absence is deliberate;
* and whether the evidence is a complete record, a bounded conceptual illustration, or an explicit non-use finding.

The final validation must not mark publication architecture `PASS` solely because one case includes a plausible YAML block. The cross-case checks must validate identity, chronology, digest, lineage, and ownership behavior.
## 39. Change Threshold

The examples should not change the foundation merely to make one case shorter or easier to serialize.

A conceptual-contract or ADR change is justified only when the examples demonstrate that:

* a valid classroom state cannot be represented;
* governing documents assign conflicting meanings;
* a cardinality prevents a legitimate relationship;
* ownership cannot be preserved without duplication;
* correction or supersession cannot preserve history;
* the available representation materially misstates the evidence or judgment;
* immutable publication cannot be represented without ambiguity;
* cross-producer lineage cannot be preserved;
* or ownership among Concord, Core, and Meridian cannot be maintained.

The following are not sufficient reasons to change the foundation:

* cosmetic preference;
* shorter example syntax;
* anticipated interface inconvenience;
* fewer records;
* easier database mapping;
* a desire to copy one module’s workflow into another;
* a desire to avoid generating a new manifest revision;
* or a desire to make publication imply grading automatically.
## 40. Completion Standard

The representative examples are complete when:

1. the seminar, laboratory, and project cases each form a coherent conceptual record set;
2. all references and relationships are internally consistent;
3. all examples use the same shared notation and terminology;
4. every typed relationship uses its contract-native reference shape;
5. the four scoring orientations are represented collectively;
6. PDS2 routing remains separate from semantic context;
7. routing remains separate from academic registration and publication;
8. standards alignment remains separate from direct standards results;
9. Group and individual judgments remain distinct;
10. Review, Moderation, Scoring, publication, Grading, and Reporting remain separate;
11. correction and native supersession preserve history;
12. Academic Work Registration is explicit rather than inferred;
13. Activity scoring orientation remains distinct from Core academic intent;
14. at least one complete Concord Academic Result Manifest is represented and mechanically validated;
15. one stable record-set series and increasing manifest revision are demonstrated;
16. every included Score has sufficient Criterion and exact Scoring Scale projections;
17. local Scores may appear in the broader manifest but never in the direct Standards Result Projection;
18. non-score dispositions remain explicit and omit `value`;
19. cross-producer ScoreForm or Quillan lineage identifies the originating module record and the exact source publication whenever required by the source-resolution contract;
20. required Moderation state is sufficient to validate consequential evidence use;
21. published manifest paths are revision-addressed and contained within the exact Activity work root;
22. published manifest bytes are SHA-256 bound to immutable Core Publication Records;
23. identical publication replay is idempotent;
24. contradictory reuse of a logical manifest revision is rejected;
25. native Score supersession and Core publication supersession remain separate;
26. one publication withdrawal or explicitly bounded withdrawal example preserves history;
27. the derived Core catalog is treated as nonauthoritative;
28. Meridian owns publication eligibility, evidence selection, cross-producer overlap, scale mapping, Grade-item membership, Academic Period membership, proficiency, Grades, overrides, and reports;
29. no producer manifest stores authoritative Academic Period, Grade, proficiency, or Meridian override state;
30. external ownership remains intact;
31. optional structures remain optional;
32. the cross-example validation is complete;
33. all mechanical audit checks in Section 35.6 pass;
34. any real conceptual defect or remaining contract ambiguity is corrected or documented explicitly;
35. release-status distinctions between `pds-core` 0.5 routing and later registry architecture remain accurate;
36. no case depends on an undocumented or architecture-breaking workaround;
37. and no unresolved blocking finding is concealed by a `PASS` or `READY` declaration.

Completion of these examples validates the conceptual architecture. It does not by itself accept ADR 0015, release Core registry APIs, or approve a production manifest schema.
## 41. Next Step

After the shared conventions in this file are accepted, revise the representative cases in this order:

1. `seminar-contract-example.md`;
2. `laboratory-contract-example.md`;
3. `project-contract-example.md`;
4. `cross-example-validation.md`.

The seminar case should be completed and checked against this README before the laboratory and project cases are revised.

The seminar should establish the first complete publication pattern:

```text
standards-based Activity
    -> explicit Academic Work Registration
    -> native standard-backed Score
    -> moderated evidence lineage
    -> Concord Academic Result Manifest revision 1
    -> Core Publication Record
    -> bounded Meridian-consumption analysis
```

The laboratory should then validate:

```text
mixed standard-backed and local Scores
    -> ScoreForm lineage
    -> both Score kinds in the broader manifest
    -> only standard-backed Scores in the Standards Result Projection
```

The project should validate:

```text
native Score supersession
    -> manifest revision
    -> Core publication supersession
    -> withdrawal or explicitly bounded withdrawal behavior
    -> external technical evidence lineage
```

Issue #13 performs the skeptical foundation review and determines:

* whether the Concord conceptual architecture is ready to govern serialized contracts and implementation work;
* whether ADR 0015 should be accepted, revised, or rejected;
* and which Core, ScoreForm, Quillan, and Meridian contracts must be released before runtime publication work begins.

Issue #13 has already formalized the Score-Target Reference and Core Publication Reference value objects and has determined that bounded withdrawal coverage is sufficient for the conceptual examples.
