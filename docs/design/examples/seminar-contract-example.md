# Representative Contract Example: Standards-Based Socratic Seminar

**Status:** Revised draft for representative-contract validation  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Issue:** `#12 — 11. Create representative contract examples`  
**Example family:** Socratic seminar / structured discussion  
**Scoring orientation:** `standards_based`  
**Publication model:** Two immutable Concord Academic Result Manifest revisions published through Core  
**Revision date:** July 30, 2026  
**Revision:** 3 — aligned with ADR 0015, Core registry publication, and Meridian

## 1. Case Purpose

This example tests whether the Concord conceptual contracts can represent a standards-based Socratic seminar involving:

- rotating discussion and observation Roles;
- Group-authored discussion maps;
- student-authored peer observations;
- one teacher-authored multi-Subject observation tracker;
- Artifact Authors who differ from Artifact Subjects;
- unresolved and corrected attribution;
- human Review;
- Moderation of peer evidence;
- individual standards-based Scores;
- one evidence source supporting several Scores;
- one Score supported by several evidence sources;
- an explicit non-score disposition;
- a later superseding Score;
- an external Quillan response used as supporting evidence;
- paper-based teacher scoring;
- explicit Core Academic Work Registration revisions;
- two immutable Concord Academic Result Manifest revisions;
- exact SHA-256-bound Core Publication Records;
- native Score supersession followed by manifest and publication supersession;
- cross-producer Quillan publication lineage;
- and a bounded Meridian-consumption analysis.

The case deliberately uses the shared Concord foundation rather than introducing seminar-specific foundational entities. Terms such as inner circle, outer circle, discussion mapper, peer observer, and seminar round are represented through Groups, Roles, Sessions, sequence context, Templates, and Artifacts.

## 2. Activity Narrative

An English 10 class conducts a two-session Socratic seminar titled **Evidence, Perspective, and Responsibility**.

Students belong to two stable Activity-specific Groups. Each Session contains one represented seminar round. Students rotate individually among contextual Roles rather than treating the Groups as permanent inner-circle and outer-circle units. This keeps the record set focused on the foundation's Role and Effective Context contracts while still exercising rotation across Sessions.

During Session 1:

- Students 001–003 primarily discuss, cite evidence, and map the discussion;
- Students 004–006 primarily observe and synthesize.

During Session 2:

- Student 001 becomes a peer observer;
- Student 002 becomes a discussant;
- Student 003 becomes a peer observer;
- Students 004–006 cite evidence, map the discussion, and discuss.

The teacher uses one multi-Subject observation tracker across both Sessions. Selected peer observers complete peer-observation forms. Those forms require Review and Moderation before consequential use because they contain student-created claims about other students.

The Activity evaluates three Focus Standards through three separate standard-backed Criteria:

1. building on peers' ideas;
2. using relevant textual evidence;
3. integrating information from the discussion.

One student initially receives an `insufficient_evidence` disposition for one Criterion. Additional teacher observation and an external Quillan reflection later support a scored judgment. The later Score supersedes the non-score disposition without deleting it.

## 3. Governing Assumptions

```text
module_id = concord
work_id   = activity_id
```

The effective module work identity is:

```text
module_id + class_id + work_id
```

The conceptual work root is:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
```

Every returned scannable page receives an Artifact Page identity, a Core Route Registration, and a PDS2 locator before rendering.

The normal Route Registration target is:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

The QR identifies the expected physical page route only. Student identity, Group identity, Artifact Author, Artifact Subject, Score target, Criterion, standard, privacy, and Score value resolve through Concord-owned records.

Routing, academic registration, result publication, and Meridian consumption are separate integration domains.

The Activity is explicitly registered through Core before its academic-result manifest is published. Concord owns the native records and immutable manifest bytes. Core owns the Academic Work Registration revisions, Publication Records, publication withdrawal records, and the rebuildable registry catalog. Meridian owns publication selection, Grade-item membership, Academic Period membership, evidence selection, proficiency and Grade calculation, overrides, and reports.

The representative publication flow is:

```text
Concord Activity and native Score Records
    -> Core Academic Work Registration
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> Meridian import and policy-controlled selection
```

Publication does not imply Grade eligibility, Academic Period membership, or use in any Meridian calculation.

## 4. Record Inventory

### 4.1 Core-owned and external references

| Record family | Count represented |
|---|---:|
| Core Class | 1 |
| Core Students | 6 |
| Authorized teacher Actor | 1 |
| Core Standards Profile | 1 |
| Core Standards | 3 |
| Core Route Registrations | 7 |
| Core Source Scans | 4 |
| Core Academic Work Registration revisions | 2 |
| Core Publication Records for Concord | 2 |
| Core Publication Reference for the Quillan source result | 1 |
| Quillan response | 1 |

### 4.2 Concord-owned records

| Record family | Count represented |
|---|---:|
| Activity | 1 |
| Sessions | 2 |
| Groups | 2 |
| Group Memberships | 6 |
| Role Assignments | 12 |
| Template Definitions | 4 |
| Template Versions | 4 |
| Packet Definition | 1 |
| Packet Version | 1 |
| Packet Components | 4 |
| Packet Instance | 1 |
| Artifact Instances | 7 |
| Artifact Pages | 7 |
| Artifact Author associations | 10 |
| Artifact Subject associations | 18 |
| Scan References | 8 |
| Artifact Reviews | 9 |
| Moderation Records | 3 |
| Correction Records | 3 |
| Criterion Set revisions | 1 |
| Criteria | 3 |
| Scoring Scale revisions | 1 |
| Score Records | 5 |
| Score Evidence Links | 9 |
| External References | 1 |
| Concord Academic Result Manifest revisions | 2 |
| Manifest Score projections | 9 across two revisions |
| Manifest evidence-lineage projections | 15 across two revisions |
| Manifest Moderation projections | 3 across two revisions |
| Standards Result Projection rows | 9 across two revisions |

The extra Scan Reference represents a clearer rescan of one Artifact Page. The extra Author association preserves an explicit unknown-to-confirmed attribution history. Manifest revision 1 contains four Score projections and six evidence-lineage rows. Manifest revision 2 contains five Score projections and nine evidence-lineage rows, including the superseded non-score judgment and its scored replacement.

## 5. Shared Core and External References

The following blocks are typed references or reference summaries. They are not attempts to redefine Core or sibling-module contracts.

### 5.1 Core Class

```yaml
owning_system: core
record_kind: class
record_id: cls_ela10_p03
display_label: English 10 — Period 3
```

### 5.2 Core Students

```yaml
students:
- owning_system: core
  record_kind: student
  record_id: stu_001
  display_label: Student 001
- owning_system: core
  record_kind: student
  record_id: stu_002
  display_label: Student 002
- owning_system: core
  record_kind: student
  record_id: stu_003
  display_label: Student 003
- owning_system: core
  record_kind: student
  record_id: stu_004
  display_label: Student 004
- owning_system: core
  record_kind: student
  record_id: stu_005
  display_label: Student 005
- owning_system: core
  record_kind: student
  record_id: stu_006
  display_label: Student 006
```

### 5.3 Teacher Actor

```yaml
actor_kind: authorized_adult
actor_id: actor_teacher_001
owning_system: local_example_identity
display_label_snapshot: Teacher 001
```

### 5.4 Standards Profile

```yaml
owning_system: core
record_kind: standards_profile
record_id: profile_njsls_ela_2023_09_10
display_label: NJSLS ELA 2023 — Grades 9–10
```

### 5.5 Focus Standards

```yaml
standards:
- owning_system: core
  record_kind: standard
  record_id: std_njsls_ela_sl_pe_9_10_1
  display_code: SL.PE.9–10.1
  display_label: Participate effectively in collaborative discussions
- owning_system: core
  record_kind: standard
  record_id: std_njsls_ela_rl_cr_9_10_1
  display_code: RL.CR.9–10.1
  display_label: Cite relevant textual evidence
- owning_system: core
  record_kind: standard
  record_id: std_njsls_ela_sl_ii_9_10_2
  display_code: SL.II.9–10.2
  display_label: Integrate information presented in collaborative contexts
```

Display codes and labels are presentation metadata. The durable identities are the `record_id` values.

## 6. Activity and Collaboration Records

### 6.1 Activity

```yaml
record_owner: concord
record_kind: activity
activity_id: act_seminar_01
class_reference:
  module_id: core
  record_kind: class
  record_id: cls_ela10_p03
title: Evidence, Perspective, and Responsibility
activity_type: local:socratic_seminar
description: A two-session structured seminar in which students discuss a shared text, build on peers' ideas, use
  textual evidence, and synthesize information from the discussion.
scoring_orientation: standards_based
standards_profile_id: profile_njsls_ela_2023_09_10
focus_standard_ids:
- std_njsls_ela_sl_pe_9_10_1
- std_njsls_ela_rl_cr_9_10_1
- std_njsls_ela_sl_ii_9_10_2
criterion_set_ids:
- critset_seminar_focus_rev_1
status: completed
privacy_policy:
  classification: classroom_shared
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-14T14:30:00-04:00'
  source_kind: manual
  note: Created during teacher configuration.
updated_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-16T12:00:00-04:00'
  source_kind: manual
  note: Activity marked completed after scoring.
external_reference_ids:
- extref_seminar_quillan_001
```

The Activity belongs to one Core class, declares one scoring orientation, selects one Core standards profile, and preserves an ordered nonempty Focus Standard collection. None of those configuration choices creates a Score.

### 6.2 Sessions

```yaml
sessions:
- record_owner: concord
  record_kind: session
  session_id: ses_seminar_01
  activity_id: act_seminar_01
  sequence: 1
  label: Seminar Session 1
  scheduled_start: '2026-09-15T09:05:00-04:00'
  scheduled_end: '2026-09-15T09:50:00-04:00'
  actual_start: '2026-09-15T09:07:00-04:00'
  actual_end: '2026-09-15T09:49:00-04:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:35:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: session
  session_id: ses_seminar_02
  activity_id: act_seminar_01
  sequence: 2
  label: Seminar Session 2
  scheduled_start: '2026-09-16T09:05:00-04:00'
  scheduled_end: '2026-09-16T09:50:00-04:00'
  actual_start: '2026-09-16T09:06:00-04:00'
  actual_end: '2026-09-16T09:50:00-04:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:36:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
```

Session sequence is unique within the Activity. Each Session is an occurrence; neither Session status nor attendance context determines a Score.

### 6.3 Groups

```yaml
groups:
- record_owner: concord
  record_kind: group
  group_id: grp_seminar_a
  activity_id: act_seminar_01
  label: Seminar Group A
  description: Stable seminar Group for both Sessions.
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:40:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: group
  group_id: grp_seminar_b
  activity_id: act_seminar_01
  label: Seminar Group B
  description: Stable seminar Group for both Sessions.
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:41:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
```

The Groups are Concord-owned and Activity-specific. They are not added to the Core roster.

### 6.4 Group Memberships

```yaml
group_memberships:
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_seminar_a_001
  group_id: grp_seminar_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:45:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_seminar_a_002
  group_id: grp_seminar_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:46:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_seminar_a_003
  group_id: grp_seminar_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:47:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_seminar_b_004
  group_id: grp_seminar_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:48:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_seminar_b_005
  group_id: grp_seminar_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:49:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_seminar_b_006
  group_id: grp_seminar_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    - ses_seminar_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T14:50:00-04:00'
    source_kind: manual
    note: Created during teacher configuration.
```

Membership establishes contextual participation only. It does not establish Artifact authorship, contribution, Role fulfillment, or performance.

### 6.5 Role Assignments

```yaml
role_assignments:
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s1_r1_001
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  membership_id: mem_seminar_a_001
  group_id: grp_seminar_a
  role_key: local:discussant
  role_label_snapshot: Discussant
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:01:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s1_r1_002
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  membership_id: mem_seminar_a_002
  group_id: grp_seminar_a
  role_key: local:evidence_citer
  role_label_snapshot: Evidence Citer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:02:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s1_r1_003
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  membership_id: mem_seminar_a_003
  group_id: grp_seminar_a
  role_key: local:discussion_mapper
  role_label_snapshot: Discussion Mapper
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:03:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s1_r1_004
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  membership_id: mem_seminar_b_004
  group_id: grp_seminar_b
  role_key: local:peer_observer
  role_label_snapshot: Peer Observer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:04:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s1_r1_005
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  membership_id: mem_seminar_b_005
  group_id: grp_seminar_b
  role_key: local:peer_observer
  role_label_snapshot: Peer Observer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:05:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s1_r1_006
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  membership_id: mem_seminar_b_006
  group_id: grp_seminar_b
  role_key: local:outer_circle_synthesizer
  role_label_snapshot: Outer Circle Synthesizer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_01
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:06:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s2_r1_001
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  membership_id: mem_seminar_a_001
  group_id: grp_seminar_a
  role_key: local:peer_observer
  role_label_snapshot: Peer Observer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_02
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:11:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s2_r1_002
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  membership_id: mem_seminar_a_002
  group_id: grp_seminar_a
  role_key: local:discussant
  role_label_snapshot: Discussant
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_02
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:12:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s2_r1_003
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  membership_id: mem_seminar_a_003
  group_id: grp_seminar_a
  role_key: local:peer_observer
  role_label_snapshot: Peer Observer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_02
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:13:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s2_r1_004
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  membership_id: mem_seminar_b_004
  group_id: grp_seminar_b
  role_key: local:evidence_citer
  role_label_snapshot: Evidence Citer
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_02
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:14:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s2_r1_005
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  membership_id: mem_seminar_b_005
  group_id: grp_seminar_b
  role_key: local:discussion_mapper
  role_label_snapshot: Discussion Mapper
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_02
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:15:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_sem_s2_r1_006
  activity_id: act_seminar_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  membership_id: mem_seminar_b_006
  group_id: grp_seminar_b
  role_key: local:discussant
  role_label_snapshot: Discussant
  effective_context:
    activity_id: act_seminar_01
    session_ids:
    - ses_seminar_02
    sequence_start: 1
    sequence_end: 1
  status: completed
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-14T15:16:00-04:00'
    source_kind: manual
    note: Role assigned during teacher configuration.
```

The assignments preserve Session-specific rotation. Role keys use a local namespace. A Role Assignment does not prove successful Role fulfillment, and recorder status does not establish sole authorship.

## 7. Template and Packet Records

### 7.1 Template Definitions

```yaml
template_definitions:
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_seminar_discussion_map
  name: Socratic Seminar Discussion Map
  artifact_category: local:group_graphic_organizer
  purpose: Record the Group's discussion sequence, claims, evidence, and connections.
  owner_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:00:00-04:00'
    source_kind: manual
    note: Reusable template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_seminar_peer_observation
  name: Socratic Seminar Peer Observation
  artifact_category: local:peer_observation
  purpose: Record specific observed discussion behaviors for later teacher Review.
  owner_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:05:00-04:00'
    source_kind: manual
    note: Reusable template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_seminar_teacher_tracker
  name: Socratic Seminar Focus Standards Tracker
  artifact_category: local:teacher_observation
  purpose: Record teacher observations across several students and Criteria.
  owner_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:10:00-04:00'
    source_kind: manual
    note: Reusable template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_seminar_scoring_rubric
  name: Socratic Seminar Focus Standards Scoring Rubric
  artifact_category: local:scoring_rubric
  purpose: Provide a paper surface for entering separate Criterion-level teacher judgments.
  owner_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:15:00-04:00'
    source_kind: manual
    note: Reusable template lineage created.
```

### 7.2 Immutable Template Versions

```yaml
template_versions:
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_seminar_discussion_map_r1
  template_id: tmpl_seminar_discussion_map
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_seminar_discussion_map_r1
  artifact_category: local:group_graphic_organizer
  page_manifest:
  - page_number: 1
    page_kind: primary
    return_expected: true
    route_required: true
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: group_and_teacher
  default_authorship_expectation:
    mode: local:collective_group_author
  default_subject_expectation:
    mode: local:represented_group
  qr_requirements:
    schema: PDS2
    required_page_numbers:
    - 1
    target_record_kind: artifact_page
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:30:00-04:00'
    source_kind: manual
    note: Immutable printable revision created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_seminar_peer_observation_r1
  template_id: tmpl_seminar_peer_observation
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_seminar_peer_observation_r1
  artifact_category: local:peer_observation
  page_manifest:
  - page_number: 1
    page_kind: observation
    return_expected: true
    route_required: true
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:observer
  default_subject_expectation:
    mode: local:observed_participant
  qr_requirements:
    schema: PDS2
    required_page_numbers:
    - 1
    target_record_kind: artifact_page
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:35:00-04:00'
    source_kind: manual
    note: Immutable printable revision created.
  status: active
  supported_criterion_ids:
  - crit_seminar_builds_on_ideas
  - crit_seminar_integrates_discussion
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_seminar_teacher_tracker_r1
  template_id: tmpl_seminar_teacher_tracker
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_seminar_teacher_tracker_r1
  artifact_category: local:teacher_observation
  page_manifest:
  - page_number: 1
    page_kind: observation
    return_expected: true
    route_required: true
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:teacher_author
  default_subject_expectation:
    mode: local:observed_participant
  qr_requirements:
    schema: PDS2
    required_page_numbers:
    - 1
    target_record_kind: artifact_page
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:40:00-04:00'
    source_kind: manual
    note: Immutable printable revision created.
  status: active
  supported_criterion_ids:
  - crit_seminar_builds_on_ideas
  - crit_seminar_textual_evidence
  - crit_seminar_integrates_discussion
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_seminar_scoring_rubric_r1
  template_id: tmpl_seminar_scoring_rubric
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_seminar_scoring_rubric_r1
  artifact_category: local:scoring_rubric
  page_manifest:
  - page_number: 1
    page_kind: rubric
    return_expected: true
    route_required: true
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:teacher_author
  default_subject_expectation:
    mode: local:activity_context
  qr_requirements:
    schema: PDS2
    required_page_numbers:
    - 1
    target_record_kind: artifact_page
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-10T15:45:00-04:00'
    source_kind: manual
    note: Immutable printable revision created.
  status: active
  supported_criterion_ids:
  - crit_seminar_builds_on_ideas
  - crit_seminar_textual_evidence
  - crit_seminar_integrates_discussion
```

Each Version supplies the rendering reference, Artifact category, page manifest, return behavior, privacy default, authorship and Subject expectations, QR requirements, and exact supported Criteria where applicable. Once used to generate an Artifact Instance, the Version is immutable.

### 7.3 Packet Definition

```yaml
record_owner: concord
record_kind: packet_definition
packet_definition_id: pktdef_seminar_standard
name: Standards-Based Socratic Seminar Packet
purpose: Assemble Group discussion maps, selected peer observations, a teacher tracker, and a standards-based scoring
  rubric for one seminar Activity.
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-11T14:00:00-04:00'
  source_kind: manual
  note: Reusable packet lineage created.
```

### 7.4 Packet Version

```yaml
record_owner: concord
record_kind: packet_version
packet_version_id: pktv_seminar_standard_r1
packet_definition_id: pktdef_seminar_standard
version_label: Revision 1
revision_sequence: 1
component_ids:
- pktcmp_seminar_01
- pktcmp_seminar_02
- pktcmp_seminar_03
- pktcmp_seminar_04
generation_rules:
  packet_scope: one_activity
  assembly_order: component_sequence
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-11T14:10:00-04:00'
  source_kind: manual
  note: Immutable packet composition created.
status: active
```

The ordered component collection is immutable after generation.

### 7.5 Packet Components

```yaml
packet_components:
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_seminar_01
  packet_version_id: pktv_seminar_standard_r1
  sequence: 1
  component_kind: concord_template
  template_version_id: tmplv_seminar_discussion_map_r1
  quantity_rule:
    mode: one_per_group
  audience_rule:
    target_kind: concord_group
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_seminar_02
  packet_version_id: pktv_seminar_standard_r1
  sequence: 2
  component_kind: concord_template
  template_version_id: tmplv_seminar_peer_observation_r1
  quantity_rule:
    mode: selected_participants
    count: 3
  audience_rule:
    role_key: local:peer_observer
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_seminar_03
  packet_version_id: pktv_seminar_standard_r1
  sequence: 3
  component_kind: concord_template
  template_version_id: tmplv_seminar_teacher_tracker_r1
  quantity_rule:
    mode: fixed
    quantity: 1
  audience_rule:
    target_kind: authorized_actor
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_seminar_04
  packet_version_id: pktv_seminar_standard_r1
  sequence: 4
  component_kind: concord_template
  template_version_id: tmplv_seminar_scoring_rubric_r1
  quantity_rule:
    mode: fixed
    quantity: 1
  audience_rule:
    target_kind: authorized_actor
  requirement_level: required
```

Each Component is explicitly a Concord Template component and identifies exactly one immutable Template Version.

### 7.6 Packet Instance

```yaml
record_owner: concord
record_kind: packet_instance
packet_instance_id: pkt_seminar_01
packet_version_id: pktv_seminar_standard_r1
activity_id: act_seminar_01
generation_status: completed
generated_at: '2026-09-15T08:00:00-04:00'
generated_by:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
artifact_instance_ids:
- art_seminar_map_a
- art_seminar_map_b
- art_seminar_peer_001
- art_seminar_peer_002
- art_seminar_peer_003
- art_seminar_teacher_tracker
- art_seminar_scoring_rubric
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-15T08:00:00-04:00'
  source_kind: generated
  source_reference:
    record_kind: packet_version
    record_id: pktv_seminar_standard_r1
  note: Packet generated for the configured Activity.
```

The Packet Instance records its exact Packet Version, generator, generation time, and complete Artifact membership.

## 8. Artifact and Routing Records

### 8.1 Artifact Instances

```yaml
artifact_instances:
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_map_a
  template_version_id: tmplv_seminar_discussion_map_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:group_graphic_organizer
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_seminar_map_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:01:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_discussion_map_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_seminar_01
  group_id: grp_seminar_a
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_map_b
  template_version_id: tmplv_seminar_discussion_map_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:group_graphic_organizer
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_seminar_map_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:02:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_discussion_map_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_seminar_02
  group_id: grp_seminar_b
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_peer_001
  template_version_id: tmplv_seminar_peer_observation_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:peer_observation
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_seminar_peer_001_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:03:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_peer_observation_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_seminar_01
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_peer_002
  template_version_id: tmplv_seminar_peer_observation_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:peer_observation
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_seminar_peer_002_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:04:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_peer_observation_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_seminar_01
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_peer_003
  template_version_id: tmplv_seminar_peer_observation_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:peer_observation
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_seminar_peer_003_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:05:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_peer_observation_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_seminar_02
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_teacher_tracker
  template_version_id: tmplv_seminar_teacher_tracker_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:teacher_observation
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_seminar_tracker_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:06:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_teacher_tracker_r1
    note: Artifact generated from the immutable Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_seminar_scoring_rubric
  template_version_id: tmplv_seminar_scoring_rubric_r1
  activity_id: act_seminar_01
  packet_instance_id: pkt_seminar_01
  artifact_category: local:scoring_rubric
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_seminar_rubric_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:07:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_seminar_scoring_rubric_r1
    note: Artifact generated from the immutable Template Version.
```

Generation, expected-return, and Artifact lifecycle are represented separately. Privacy is effective at the Artifact level, and each Artifact names its ordered Artifact Pages.

### 8.2 Artifact Pages

```yaml
artifact_pages:
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_map_a_01
  artifact_instance_id: art_seminar_map_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_seminar_map_a_01
  human_fallback: SEM-01-MAP-A
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:01:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_map_a
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_map_b_01
  artifact_instance_id: art_seminar_map_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_seminar_map_b_01
  human_fallback: SEM-02-MAP-B
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:02:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_map_b
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_peer_001_01
  artifact_instance_id: art_seminar_peer_001
  page_number: 1
  expected_page_count: 1
  page_kind: observation
  return_expected: true
  route_required: true
  route_id: route_seminar_peer_001_01
  human_fallback: SEM-01-PO-001
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:03:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_peer_001
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_peer_002_01
  artifact_instance_id: art_seminar_peer_002
  page_number: 1
  expected_page_count: 1
  page_kind: observation
  return_expected: true
  route_required: true
  route_id: route_seminar_peer_002_01
  human_fallback: SEM-01-PO-002
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:04:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_peer_002
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_peer_003_01
  artifact_instance_id: art_seminar_peer_003
  page_number: 1
  expected_page_count: 1
  page_kind: observation
  return_expected: true
  route_required: true
  route_id: route_seminar_peer_003_01
  human_fallback: SEM-02-PO-003
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:05:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_peer_003
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_tracker_01
  artifact_instance_id: art_seminar_teacher_tracker
  page_number: 1
  expected_page_count: 1
  page_kind: observation
  return_expected: true
  route_required: true
  route_id: route_seminar_tracker_01
  human_fallback: SEM-01-TRACKER
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:06:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_teacher_tracker
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_seminar_rubric_01
  artifact_instance_id: art_seminar_scoring_rubric
  page_number: 1
  expected_page_count: 1
  page_kind: rubric
  return_expected: true
  route_required: true
  route_id: route_seminar_rubric_01
  human_fallback: SEM-01-RUBRIC
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:07:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_scoring_rubric
    note: Page identity created before route registration and rendering.
```

All seven pages exist before route registration and rendering. Each route-required page has one immutable `route_id` and one human-readable recovery identifier.

### 8.3 Core Route Registrations

```yaml
route_registrations:
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_map_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_map_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_map_a_01
  status: active
  registered_at: '2026-09-15T08:01:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_map_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_map_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_map_b_01
  status: active
  registered_at: '2026-09-15T08:02:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_peer_001_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_peer_001_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_peer_001_01
  status: active
  registered_at: '2026-09-15T08:03:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_peer_002_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_peer_002_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_peer_002_01
  status: active
  registered_at: '2026-09-15T08:04:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_peer_003_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_peer_003_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_peer_003_01
  status: active
  registered_at: '2026-09-15T08:05:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_tracker_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_tracker_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_tracker_01
  status: active
  registered_at: '2026-09-15T08:06:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_seminar_rubric_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
    route_id: route_seminar_rubric_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_seminar_rubric_01
  status: active
  registered_at: '2026-09-15T08:07:20-04:00'
```

Every Registration uses `work_id = activity_id` and targets an existing Concord Artifact Page.

### 8.4 Representative PDS2 Locator

```text
PDS2|m=concord|c=cls_ela10_p03|w=act_seminar_01|r=route_seminar_peer_001_01
```

The locator contains no student, Group, Author, Subject, Criterion, standard, scorer, privacy, or Score semantics.

## 9. Artifact Author Associations

```yaml
artifact_authors:
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_map_a_group
  artifact_instance_id: art_seminar_map_a
  author_reference:
    record_kind: group
    record_id: grp_seminar_a
  authorship_mode: collective_group_author
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: packet_configuration
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T10:15:00-04:00'
    source_kind: manual
    note: Confirmed during teacher Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_map_a_recorder
  artifact_instance_id: art_seminar_map_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_seminar_a
  role_assignment_id: role_sem_s1_r1_003
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: role_assignment_and_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T10:16:00-04:00'
    source_kind: manual
    note: Recorder relationship confirmed during teacher Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_map_b_group
  artifact_instance_id: art_seminar_map_b
  author_reference:
    record_kind: group
    record_id: grp_seminar_b
  authorship_mode: collective_group_author
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: packet_configuration
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:15:00-04:00'
    source_kind: manual
    note: Confirmed during teacher Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_map_b_recorder
  artifact_instance_id: art_seminar_map_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_seminar_b
  role_assignment_id: role_sem_s2_r1_005
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: role_assignment_and_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:16:00-04:00'
    source_kind: manual
    note: Recorder relationship confirmed during teacher Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_peer_001
  artifact_instance_id: art_seminar_peer_001
  author_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  authorship_mode: observer
  role_assignment_id: role_sem_s1_r1_004
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: preprinted_observer_assignment
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T10:20:00-04:00'
    source_kind: manual
    note: Confirmed during teacher Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_peer_002_unknown
  artifact_instance_id: art_seminar_peer_002
  author_reference:
    actor_kind: external_actor
    actor_id: unresolved_author_peer_002
    owning_system: local_example_identity
  authorship_mode: unknown
  representation_status: not_applicable
  attribution_status: unknown
  attribution_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T10:30:00-04:00'
    source_kind: manual
    note: The returned form omitted the observer name; handwriting was not used to infer identity.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_peer_002
  artifact_instance_id: art_seminar_peer_002
  author_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  authorship_mode: observer
  role_assignment_id: role_sem_s1_r1_005
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: packet_manifest_and_role_assignment
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T11:05:00-04:00'
    source_kind: manual
    note: Identity resolved through the packet manifest and Role Assignment.
  supersedes_artifact_author_id: author_seminar_peer_002_unknown
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_peer_003
  artifact_instance_id: art_seminar_peer_003
  author_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  authorship_mode: observer
  role_assignment_id: role_sem_s2_r1_003
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: preprinted_observer_assignment
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:18:00-04:00'
    source_kind: manual
    note: Confirmed during teacher Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_tracker_teacher
  artifact_instance_id: art_seminar_teacher_tracker
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: packet_configuration
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T10:19:00-04:00'
    source_kind: manual
    note: Teacher authorship confirmed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_seminar_rubric_teacher
  artifact_instance_id: art_seminar_scoring_rubric
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: packet_configuration
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:20:00-04:00'
    source_kind: manual
    note: Teacher authorship confirmed.
```

The record set demonstrates collective Group authorship, a recorder acting for a Group, individual peer observation, teacher authorship, and an explicit unknown-to-confirmed Author correction. Student 005—not Student 006—is the Group B discussion-map recorder because `role_sem_s2_r1_005` is the relevant discussion-mapper assignment.

The unknown Author association is not inferred from handwriting. The confirmed replacement uses the packet manifest and Role Assignment and explicitly supersedes the unknown association. Successful routing did not depend on resolving the Author.

## 10. Artifact Subject Associations

```yaml
artifact_subjects:
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_map_a_group
  artifact_instance_id: art_seminar_map_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_seminar_a
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: packet_configuration
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:01:30-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_map_a_session
  artifact_instance_id: art_seminar_map_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_seminar_01
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: packet_configuration
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:01:31-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_map_b_group
  artifact_instance_id: art_seminar_map_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_seminar_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: packet_configuration
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:02:30-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_map_b_session
  artifact_instance_id: art_seminar_map_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_seminar_02
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: packet_configuration
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:02:31-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_peer_001_student
  artifact_instance_id: art_seminar_peer_001
  subject_reference:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: preprinted_observation_target
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T10:21:00-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_peer_002_student_v1
  artifact_instance_id: art_seminar_peer_002
  subject_reference:
    subject_kind: core_student
    subject_id: stu_003
    owning_system: core
  subject_role: observed_participant
  confirmation_status: proposed
  assignment_source: packet_configuration
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T08:04:00-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_peer_002_student_v2
  artifact_instance_id: art_seminar_peer_002
  subject_reference:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T11:06:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
  supersedes_artifact_subject_id: subject_seminar_peer_002_student_v1
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_seminar_peer_003_student
  artifact_instance_id: art_seminar_peer_003
  subject_reference:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: preprinted_observation_target
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:19:00-04:00'
    source_kind: generated
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_stu_001
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:21:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_stu_002
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:22:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_stu_003
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_003
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:23:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_stu_004
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:24:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_stu_005
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:25:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_stu_006
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_006
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:26:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_group_a
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_seminar_a
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:27:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_group_b
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_seminar_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:28:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_session_1
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_seminar_01
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:29:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_tracker_session_2
  artifact_instance_id: art_seminar_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_seminar_02
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T10:30:00-04:00'
    source_kind: manual
    note: Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
```

The record set contains eighteen Subject associations: four for the two Group maps, one for Peer Observation 1, two historical versions for Peer Observation 2, one for Peer Observation 3, and ten for the teacher tracker. The Group maps have no individual student Subject. The teacher tracker remains one Artifact with several student, Group, and Session Subjects.

## 11. Scan References

### 11.1 Core-Retained Source Scan Summaries

```yaml
source_scans:
- record_owner: core
  record_kind: source_scan
  record_id: scan_core_seminar_batch_01
  source_filename: synthetic_seminar_batch_01.pdf
  retained_at: '2026-09-15T10:00:00-04:00'
  page_count: 3
- record_owner: core
  record_kind: source_scan
  record_id: scan_core_seminar_rescan_01
  source_filename: synthetic_peer_observation_rescan.pdf
  retained_at: '2026-09-15T10:45:00-04:00'
  page_count: 1
- record_owner: core
  record_kind: source_scan
  record_id: scan_core_seminar_batch_02
  source_filename: synthetic_seminar_batch_02.pdf
  retained_at: '2026-09-16T10:00:00-04:00'
  page_count: 3
- record_owner: core
  record_kind: source_scan
  record_id: scan_core_seminar_scoring
  source_filename: synthetic_seminar_scoring.pdf
  retained_at: '2026-09-16T11:30:00-04:00'
  page_count: 1
```

The Session 1 batch contains the Group A map and two peer observations. The rescan contains a clearer copy of Peer Observation 1. The Session 2 batch contains the Group B map, Peer Observation 3, and teacher tracker. The final scoring scan contains the completed paper scoring rubric.

### 11.2 Concord Scan References

```yaml
scan_references:
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_map_a
  artifact_page_id: page_seminar_map_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_batch_01
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-15T10:01:00-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_batch_01
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_peer_001_initial
  artifact_page_id: page_seminar_peer_001_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_batch_01
  source_page_index: 1
  routing_status: routed
  readability_status: partially_readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: false
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-15T10:02:00-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_batch_01
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
  status_reason:
    reason_code: clearer_rescan_available
    note: A later retained source provides a more readable image of the same page.
    related_record:
      owning_system: concord
      record_kind: scan_reference
      record_id: scanref_seminar_peer_001_rescan
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-09-15T10:47:00-04:00'
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_peer_002
  artifact_page_id: page_seminar_peer_002_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_batch_01
  source_page_index: 2
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-15T10:02:20-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_batch_01
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_peer_001_rescan
  artifact_page_id: page_seminar_peer_001_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_rescan_01
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-15T10:46:00-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_rescan_01
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
  supersedes_scan_reference_id: scanref_seminar_peer_001_initial
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_map_b
  artifact_page_id: page_seminar_map_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_batch_02
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-16T10:01:00-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_batch_02
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_peer_003
  artifact_page_id: page_seminar_peer_003_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_batch_02
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-16T10:01:20-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_batch_02
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_tracker
  artifact_page_id: page_seminar_tracker_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_batch_02
  source_page_index: 2
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-16T10:01:40-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_batch_02
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_seminar_rubric
  artifact_page_id: page_seminar_rubric_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_seminar_scoring
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: external_actor
      actor_id: core_dispatch_seminar
      owning_system: core
    timestamp: '2026-09-16T11:31:00-04:00'
    source_kind: routed
    source_reference:
      module_id: core
      record_kind: source_scan
      record_id: scan_core_seminar_scoring
    note: Core route dispatch linked the retained source page to the Concord Artifact Page.
```

The Core-retained source remains canonical. The rescan creates a new source scan and a new Scan Reference; it does not overwrite the earlier source or association.

## 12. Artifact Reviews

```yaml
artifact_reviews:
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_map_a
  artifact_instance_id: art_seminar_map_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-15T10:40:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: group_and_teacher
  relevance_judgment: relevant
  moderation_requirement: not_required
  scoring_readiness: ready
  review_outcome: ready
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_map_b
  artifact_instance_id: art_seminar_map_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-16T10:15:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: group_and_teacher
  relevance_judgment: relevant
  moderation_requirement: not_required
  scoring_readiness: ready
  review_outcome: ready
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_tracker
  artifact_instance_id: art_seminar_teacher_tracker
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-16T10:18:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: relevant
  moderation_requirement: not_required
  scoring_readiness: ready
  review_outcome: ready
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_peer_001_initial_scan
  artifact_instance_id: art_seminar_peer_001
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-15T10:10:00-04:00'
  readability_judgment: partially_readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: relevant
  moderation_requirement: required
  scoring_readiness: awaiting_rescan
  review_outcome: ready_with_qualification
  privacy_policy:
    classification: teacher_restricted
  notes: The initial scan is partially readable; a clearer rescan is requested.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_peer_001
  artifact_instance_id: art_seminar_peer_001
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-15T10:50:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: relevant
  moderation_requirement: required
  scoring_readiness: awaiting_moderation
  review_outcome: moderation_required
  privacy_policy:
    classification: teacher_restricted
  notes: The observation contains a specific description of Student 001 building on a peer's claim. Peer evidence
    requires Moderation before consequential use.
  supersedes_artifact_review_id: review_seminar_peer_001_initial_scan
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_peer_002_v1
  artifact_instance_id: art_seminar_peer_002
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-15T10:30:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: unresolved
  subject_judgment: incorrect
  privacy_judgment: teacher_restricted
  relevance_judgment: unresolved
  moderation_requirement: required
  scoring_readiness: not_ready
  review_outcome: awaiting_correction
  privacy_policy:
    classification: teacher_restricted
  notes: The name field is blank, and the observed student differs from the proposed target. Handwriting is not
    used to infer the Author.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_peer_002_v2
  artifact_instance_id: art_seminar_peer_002
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-15T11:10:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: limited
  moderation_requirement: required
  scoring_readiness: awaiting_moderation
  review_outcome: moderation_required
  privacy_policy:
    classification: teacher_restricted
  notes: The packet manifest confirms Student 005 as the observer. Teacher Review confirms Student 002 as the actual
    observed participant.
  supersedes_artifact_review_id: review_seminar_peer_002_v1
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_peer_003
  artifact_instance_id: art_seminar_peer_003
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-16T10:20:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: relevant
  moderation_requirement: required
  scoring_readiness: awaiting_moderation
  review_outcome: moderation_required
  privacy_policy:
    classification: teacher_restricted
  notes: Peer evidence requires Moderation before consequential use.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_seminar_rubric
  artifact_instance_id: art_seminar_scoring_rubric
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-09-16T11:35:00-04:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: relevant
  moderation_requirement: not_required
  scoring_readiness: ready
  review_outcome: ready
  privacy_policy:
    classification: teacher_restricted
  notes: The paper judgment surface is readable and correctly filed; the canonical judgments remain the Score Records.
```

Review establishes administrative and evidentiary readiness only. The Peer Observation 2 history preserves the unresolved Author and incorrect proposed Subject before the corrected Review. The paper scoring rubric Review confirms readability and filing after the final scoring scan; it does not replace the canonical Score Records.

## 13. Moderation Records

```yaml
moderation_records:
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_seminar_peer_001
  target_evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_001
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-09-15T11:20:00-04:00'
  status: accepted_with_qualification
  qualification: May corroborate teacher observation of Student 001 building on peers' ideas; it may not independently
    determine the final Score.
  permitted_use: may_corroborate_teacher_evidence
  rationale: The form describes a specific exchange and is consistent with the teacher tracker, but it represents
    one peer's perspective.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_seminar_peer_002
  target_evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_002
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-09-15T11:25:00-04:00'
  status: insufficient
  permitted_use: formative_only
  rationale: The observation confirms participation but does not identify a specific idea, source, or discussion
    connection. It may guide feedback but may not support a consequential standards Score.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_seminar_peer_003
  target_evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_003
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-09-16T10:25:00-04:00'
  status: accepted
  permitted_use: may_support_one_named_subject
  rationale: The observation identifies the peer ideas Student 002 synthesized and matches the sequence recorded
    on the teacher tracker.
  privacy_policy:
    classification: teacher_restricted
```

Moderation determines whether and how peer evidence may be used. It does not select a Criterion, target, or Score value. The insufficient peer observation remains available for formative use and is not negative evidence against Student 002.

## 14. Criteria and Scoring Scale Records

### 14.1 Criterion Set Revision

```yaml
record_owner: concord
record_kind: criterion_set
criterion_set_id: critset_seminar_focus_rev_1
lineage_id: critset_seminar_focus
name: Socratic Seminar Focus Standards
purpose: Define separate standards-based performance statements for collaborative discussion, textual evidence,
  and synthesis.
revision: 1
scope: activity_specific
criterion_set_kind: standard_backed
standards_profile_id: profile_njsls_ela_2023_09_10
criterion_ids:
- crit_seminar_builds_on_ideas
- crit_seminar_textual_evidence
- crit_seminar_integrates_discussion
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-12T14:00:00-04:00'
  source_kind: manual
  note: Immutable Activity-specific Criterion Set revision created.
```

### 14.2 Criteria

```yaml
criteria:
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_seminar_builds_on_ideas
  criterion_set_id: critset_seminar_focus_rev_1
  key: builds_on_ideas
  label: Builds on peers' ideas
  definition: Responds directly to a peer's contribution by extending, qualifying, challenging, or connecting the
    idea in a substantive manner.
  criterion_kind: standard_backed
  standard_id: std_njsls_ela_sl_pe_9_10_1
  supported_target_kinds:
  - core_student
  default_scoring_scale_id: scale_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-12T14:05:00-04:00'
    source_kind: manual
    note: Immutable Criterion created.
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_seminar_textual_evidence
  criterion_set_id: critset_seminar_focus_rev_1
  key: textual_evidence
  label: Uses relevant textual evidence
  definition: Selects and explains relevant textual evidence to support, refine, or challenge a claim during the
    seminar.
  criterion_kind: standard_backed
  standard_id: std_njsls_ela_rl_cr_9_10_1
  supported_target_kinds:
  - core_student
  default_scoring_scale_id: scale_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-12T14:06:00-04:00'
    source_kind: manual
    note: Immutable Criterion created.
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_seminar_integrates_discussion
  criterion_set_id: critset_seminar_focus_rev_1
  key: integrates_discussion
  label: Integrates information from the discussion
  definition: Synthesizes relevant ideas, evidence, or perspectives introduced by several participants into a coherent
    contribution or conclusion.
  criterion_kind: standard_backed
  standard_id: std_njsls_ela_sl_ii_9_10_2
  supported_target_kinds:
  - core_student
  default_scoring_scale_id: scale_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-12T14:07:00-04:00'
    source_kind: manual
    note: Immutable Criterion created.
```

Each standard-backed Criterion governs exactly one Focus Standard and supports only individual Core-student targets in this example. No `alignment_standard_ids` field is present because these Criteria are standard-backed, not local.

### 14.3 Scoring Scale Revision

```yaml
record_owner: concord
record_kind: scoring_scale
scoring_scale_id: scale_proficiency_4_rev_1
lineage_id: scale_proficiency_4
name: Four-Level Proficiency Scale
revision: 1
scale_type: ordinal
levels:
- value: developing
  label: Developing
  meaning: Evidence is limited, inconsistent, or substantially incomplete.
  order: 1
- value: approaching
  label: Approaching
  meaning: Evidence demonstrates partial or inconsistent performance.
  order: 2
- value: meeting
  label: Meeting
  meaning: Evidence demonstrates the expected level of performance.
  order: 3
- value: exceeding
  label: Exceeding
  meaning: Evidence demonstrates sustained and sophisticated performance.
  order: 4
intended_use: standards_based
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-09-12T14:15:00-04:00'
  source_kind: manual
  note: Immutable scale revision created.
```

The ordered levels do not make this scale semantically equivalent to another four-level scale. No points-total rubric is assumed.

## 15. External Quillan Reference and Source-Publication Lineage

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
group_id: grp_seminar_a
criterion_id: crit_seminar_integrates_discussion
subject_reference:
  subject_kind: core_student
  subject_id: stu_002
  owning_system: core
external_locator:
  scheme: institutional_record
  locator: quillan_response_seminar_002
  display_label: Student 002 seminar synthesis reflection
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
  note: Concord relationship created without copying the Quillan-owned response.
```

The Concord-owned relationship points to a Quillan-owned response. The External Reference is created before the superseding Score and therefore does not contain a forward `score_record_id` reference. The later Score Evidence Link supplies the deliberate Score relationship.

The exact originating producer publication is known in this synthetic case:

```yaml
source_publication_reference:
  publication_id: pub_quillan_seminar_reflection_001
```

That Core Publication Reference identifies the Quillan result-set revision through which the response became discoverable. It does not transfer Quillan ownership to Core or Concord. The same reference appears on the Quillan Evidence Reference and in the manifest evidence-lineage projection so Meridian can detect cross-producer overlap.

## 16. Score Records

```yaml
score_records:
- record_owner: concord
  record_kind: score_record
  score_record_id: score_seminar_001_builds
  activity_id: act_seminar_01
  session_id: ses_seminar_01
  target_reference:
    target_kind: core_student
    target_id: stu_001
    owning_system: core
  criterion_id: crit_seminar_builds_on_ideas
  score_kind: standard_backed
  standard_id: std_njsls_ela_sl_pe_9_10_1
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-15T12:00:00-04:00'
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_001
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:00:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_scoring_rubric
    note: Canonical Score entered from the reviewed paper scoring surface.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_seminar_001_evidence
  activity_id: act_seminar_01
  session_id: ses_seminar_01
  target_reference:
    target_kind: core_student
    target_id: stu_001
    owning_system: core
  criterion_id: crit_seminar_textual_evidence
  score_kind: standard_backed
  standard_id: std_njsls_ela_rl_cr_9_10_1
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: scored
  value: approaching
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-15T12:03:00-04:00'
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_001
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:03:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_scoring_rubric
    note: Canonical Score entered from the reviewed paper scoring surface.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_seminar_001_integrates
  activity_id: act_seminar_01
  session_id: ses_seminar_01
  target_reference:
    target_kind: core_student
    target_id: stu_001
    owning_system: core
  criterion_id: crit_seminar_integrates_discussion
  score_kind: standard_backed
  standard_id: std_njsls_ela_sl_ii_9_10_2
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: mixed_basis
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-15T12:06:00-04:00'
  rationale: Student 001 connected two peers' interpretations and explained how the textual evidence supported a
    broader conclusion.
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_001
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:06:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_scoring_rubric
    note: Canonical Score entered from the reviewed paper scoring surface.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_seminar_002_integrates_v1
  activity_id: act_seminar_01
  session_id: ses_seminar_01
  target_reference:
    target_kind: core_student
    target_id: stu_002
    owning_system: core
  criterion_id: crit_seminar_integrates_discussion
  score_kind: standard_backed
  standard_id: std_njsls_ela_sl_ii_9_10_2
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: insufficient_evidence
  basis: professional_judgment
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-15T12:10:00-04:00'
  rationale: Available evidence confirms participation but does not yet demonstrate a sufficiently specific synthesis
    of ideas from several participants.
  status_reason:
    reason_code: insufficient_specific_evidence
    note: No consequentially usable evidence yet demonstrates the Criterion.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-09-15T12:10:00-04:00'
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_002
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:10:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_scoring_rubric
    note: Teacher recorded an explicit non-score disposition.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_seminar_002_integrates_v2
  activity_id: act_seminar_01
  session_id: ses_seminar_02
  target_reference:
    target_kind: core_student
    target_id: stu_002
    owning_system: core
  criterion_id: crit_seminar_integrates_discussion
  score_kind: standard_backed
  standard_id: std_njsls_ela_sl_ii_9_10_2
  scoring_scale_id: scale_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-09-16T11:40:00-04:00'
  rationale: Session 2 observation and the written synthesis reflection demonstrate that Student 002 connected several
    participants' ideas into a coherent conclusion.
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_002
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T11:40:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_seminar_scoring_rubric
    note: A new canonical judgment was recorded after additional evidence became available.
  supersedes_score_record_id: score_seminar_002_integrates_v1
```

The non-score record omits `value` entirely, as required. It is not converted into zero, `developing`, failure, or another low-performance value. Student 002's later Score explicitly supersedes the earlier `insufficient_evidence` disposition while preserving the original record.

## 17. Score Evidence Links

```yaml
score_evidence_links:
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_001_builds_tracker
  score_record_id: score_seminar_001_builds
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_teacher_tracker
  evidence_locator:
    note: Page 1; Student 001 row; Builds on peers' ideas column.
  relevance_description: Teacher recorded a specific exchange in which Student 001 extended a peer's interpretation
    with a qualifying claim.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:00:30-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_001_builds_peer
  score_record_id: score_seminar_001_builds
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_001
  evidence_locator:
    note: Page 1; observed contribution 2.
  relevance_description: Student 004 recorded the peer idea to which Student 001 responded and described the substantive
    extension.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:01:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  moderation_record_id: mod_seminar_peer_001
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_001_evidence_tracker
  score_record_id: score_seminar_001_evidence
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_teacher_tracker
  evidence_locator:
    note: Page 1; Student 001 row; Uses textual evidence column.
  relevance_description: Teacher noted that Student 001 cited a relevant passage but only partially explained its
    connection to the claim.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:03:30-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_001_evidence_map
  score_record_id: score_seminar_001_evidence
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_map_a
  evidence_locator:
    note: Page 1; claim-and-evidence sequence 3.
  relevance_description: The Group map attributes the cited passage and related claim to Student 001; the teacher
    makes the individual judgment.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:04:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_001_integrates_tracker
  score_record_id: score_seminar_001_integrates
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_teacher_tracker
  evidence_locator:
    note: Page 1; Student 001 row; Integrates discussion information column.
  relevance_description: Teacher recorded the two peer contributions synthesized by Student 001.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:06:30-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_001_integrates_map
  score_record_id: score_seminar_001_integrates
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_map_a
  evidence_locator:
    note: Page 1; synthesis conclusion.
  relevance_description: The Group map preserves the sequence of ideas that Student 001 connected; the teacher makes
    the individual judgment.
  significance: contextual
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-15T12:07:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_002_integrates_peer
  score_record_id: score_seminar_002_integrates_v2
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_peer_003
  evidence_locator:
    note: Page 1; synthesis contribution.
  relevance_description: The observer identifies the separate participant ideas Student 002 combined and records
    the resulting conclusion.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T11:40:30-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  moderation_record_id: mod_seminar_peer_003
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_002_integrates_tracker
  score_record_id: score_seminar_002_integrates_v2
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_seminar_teacher_tracker
  evidence_locator:
    note: Page 1; Student 002 row; Session 2; Integrates discussion information column.
  relevance_description: Teacher recorded Student 002 connecting two peers' claims during Session 2.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T11:41:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_sem_002_integrates_quillan
  score_record_id: score_seminar_002_integrates_v2
  evidence_reference:
    evidence_kind: external_record
    owning_system: concord
    record_id: extref_seminar_quillan_001
    source_publication_reference:
      publication_id: pub_quillan_seminar_reflection_001
  evidence_locator:
    note: Synthesis paragraph in the referenced Quillan response.
  relevance_description: The written reflection identifies and connects the same participant ideas observed during
    Session 2.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-09-16T11:42:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence to the Score.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
```

The nine links demonstrate both directions of the many-to-many relationship: one source supports several separate Scores, and one Score uses several sources. Group and multi-Subject evidence identify the individual relevance through `subject_context`, the locator note, and the teacher's relevance description. The Quillan response remains external and is referenced rather than copied. Its Evidence Reference also preserves the exact Core source-publication identity for downstream overlap analysis.

## 18. Correction Records

```yaml
correction_records:
- record_owner: concord
  record_kind: correction_record
  correction_id: corr_seminar_peer_002_author
  target_reference:
    record_kind: artifact_author
    record_id: author_seminar_peer_002_unknown
  correction_type: author_correction
  reason: The returned form omitted the observer name. The packet manifest and Role Assignment identified Student
    005 without relying on handwriting.
  correcting_actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  corrected_at: '2026-09-15T11:05:00-04:00'
  replacement_reference:
    record_kind: artifact_author
    record_id: author_seminar_peer_002
  related_source_reference:
    record_kind: artifact_instance
    record_id: art_seminar_peer_002
  note: The retained source scan was not modified.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: correction_record
  correction_id: corr_seminar_peer_002_subject
  target_reference:
    record_kind: artifact_subject
    record_id: subject_seminar_peer_002_student_v1
  correction_type: subject_correction
  reason: Teacher Review determined that the observer documented Student 002 rather than the proposed target, Student
    003.
  correcting_actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  corrected_at: '2026-09-15T11:06:00-04:00'
  replacement_reference:
    record_kind: artifact_subject
    record_id: subject_seminar_peer_002_student_v2
  related_source_reference:
    record_kind: artifact_instance
    record_id: art_seminar_peer_002
  note: The retained source scan was not modified. The proposed Subject remains available for provenance.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: correction_record
  correction_id: corr_seminar_002_integrates_score
  target_reference:
    record_kind: score_record
    record_id: score_seminar_002_integrates_v1
  correction_type: score_revision
  reason: Additional Session 2 evidence and a reviewed Quillan reflection supported a scored judgment after the
    initial insufficient-evidence disposition.
  correcting_actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  corrected_at: '2026-09-16T11:44:00-04:00'
  replacement_reference:
    record_kind: score_record
    record_id: score_seminar_002_integrates_v2
  related_source_reference:
    record_kind: external_reference
    record_id: extref_seminar_quillan_001
  note: The original non-score disposition remains historically valid for the evidence available after Session 1.
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_002
      owning_system: core
```

The correction history covers Author attribution, Subject attribution, and Score revision. Each replacement also carries the appropriate same-type supersession field. No Correction Record alters a retained source scan.

## 19. Core Academic Work Registration

The seminar Activity is explicitly registered through Core. Activity existence, `scoring_orientation: standards_based`, Focus Standard selection, or Score creation would not register it automatically.

```yaml
academic_work_registrations:
- record_owner: core
  record_kind: academic_work_registration
  schema_version: '1'
  record_type: academic_work_registration
  work:
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
  registration_revision: 1
  producer_contract_version: '1'
  title: Evidence, Perspective, and Responsibility
  work_kind: collaborative_activity
  academic_intent: formative
  lifecycle: active
  created_at: '2026-09-14T14:31:00-04:00'
  updated_at: '2026-09-14T14:31:00-04:00'
  source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_seminar_01
    contract_version: '1'
- record_owner: core
  record_kind: academic_work_registration
  schema_version: '1'
  record_type: academic_work_registration
  work:
    module_id: concord
    class_id: cls_ela10_p03
    work_id: act_seminar_01
  registration_revision: 2
  producer_contract_version: '1'
  title: Evidence, Perspective, and Responsibility
  work_kind: collaborative_activity
  academic_intent: formative
  lifecycle: closed
  created_at: '2026-09-14T14:31:00-04:00'
  updated_at: '2026-09-16T11:52:00-04:00'
  source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_seminar_01
    contract_version: '1'
```

The two registration revisions preserve a Core-owned lifecycle change from `active` to `closed`. Both retain `academic_intent: formative`. That intent is not inferred from Concord's scoring orientation, and it does not force Meridian to include or exclude the work from a Grade.

Registration revision is independent of:

- native Score revision;
- manifest revision;
- Publication Record schema version;
- Publication Record supersession;
- Meridian import revision;
- and Meridian calculation or report revision.

## 20. Concord Academic Result Manifest Revision 1

Manifest revision 1 captures the publishable state after Session 1. It includes:

- three scored standard-backed judgments for Student 001;
- one explicit `insufficient_evidence` judgment for Student 002;
- the exact three Criterion projections;
- the exact Scoring Scale revision;
- six deliberate evidence-lineage rows;
- one applicable Moderation projection;
- and a standards-only subset containing the same four Score judgments.

The exact immutable bytes are the following UTF-8 JSON, including one trailing line-feed byte after the final closing brace:

```json
{
  "activity_context": {
    "activity_id": "act_seminar_01",
    "activity_status_snapshot": "active",
    "activity_type": "local:socratic_seminar",
    "class_id": "cls_ela10_p03",
    "focus_standard_ids": [
      "std_njsls_ela_sl_pe_9_10_1",
      "std_njsls_ela_rl_cr_9_10_1",
      "std_njsls_ela_sl_ii_9_10_2"
    ],
    "scoring_orientation": "standards_based",
    "session_references": [
      {
        "record_id": "ses_seminar_01",
        "record_kind": "session"
      },
      {
        "record_id": "ses_seminar_02",
        "record_kind": "session"
      }
    ],
    "standards_profile_id": "profile_njsls_ela_2023_09_10",
    "title_snapshot": "Evidence, Perspective, and Responsibility"
  },
  "criterion_projections": [
    {
      "criterion_id": "crit_seminar_builds_on_ideas",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_seminar_focus_rev_1",
      "definition": "Responds directly to a peer's contribution by extending, qualifying, challenging, or connecting the idea in a substantive manner.",
      "key": "builds_on_ideas",
      "label": "Builds on peers' ideas",
      "standard_id": "std_njsls_ela_sl_pe_9_10_1",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    },
    {
      "criterion_id": "crit_seminar_textual_evidence",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_seminar_focus_rev_1",
      "definition": "Selects and explains relevant textual evidence to support, refine, or challenge a claim during the seminar.",
      "key": "textual_evidence",
      "label": "Uses relevant textual evidence",
      "standard_id": "std_njsls_ela_rl_cr_9_10_1",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    },
    {
      "criterion_id": "crit_seminar_integrates_discussion",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_seminar_focus_rev_1",
      "definition": "Synthesizes relevant ideas, evidence, or perspectives introduced by several participants into a coherent contribution or conclusion.",
      "key": "integrates_discussion",
      "label": "Integrates information from the discussion",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    }
  ],
  "generated_at": "2026-09-15T12:15:00-04:00",
  "generated_provenance": {
    "actor": {
      "actor_id": "publisher_concord_001",
      "actor_kind": "system",
      "display_label_snapshot": "Concord academic-result publisher",
      "owning_system": "concord"
    },
    "application_version": "synthetic-concord-0.1",
    "note": "Generated from validated canonical Concord records.",
    "source_kind": "system",
    "timestamp": "2026-09-15T12:15:00-04:00"
  },
  "manifest_contract_version": "concord_academic_result_manifest_v1",
  "moderation_projections": [
    {
      "moderated_at": "2026-09-15T11:20:00-04:00",
      "moderation_record_id": "mod_seminar_peer_001",
      "permitted_use": "may_corroborate_teacher_evidence",
      "privacy_classification": "teacher_restricted",
      "qualification": "May corroborate teacher observation of Student 001 building on peers' ideas; it may not independently determine the final Score.",
      "status": "accepted_with_qualification",
      "target_evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_peer_001"
      },
      "target_subject_references": [
        {
          "owning_system": "core",
          "subject_id": "stu_001",
          "subject_kind": "core_student"
        }
      ]
    }
  ],
  "privacy_classification": "teacher_restricted",
  "producer_module_id": "concord",
  "record_kind": "concord_academic_result_manifest",
  "record_owner": "concord",
  "record_set_id": "rs_seminar_results_01",
  "record_set_revision": 1,
  "score_evidence_link_projections": [
    {
      "evidence_locator": {
        "note": "Page 1; Student 001 row; Builds on peers' ideas column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher recorded a specific exchange in which Student 001 extended a peer's interpretation with a qualifying claim.",
      "score_evidence_link_id": "scoreev_sem_001_builds_tracker",
      "score_record_id": "score_seminar_001_builds",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; observed contribution 2."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_peer_001"
      },
      "moderation_record_id": "mod_seminar_peer_001",
      "relevance_description": "Student 004 recorded the peer idea to which Student 001 responded and described the substantive extension.",
      "score_evidence_link_id": "scoreev_sem_001_builds_peer",
      "score_record_id": "score_seminar_001_builds",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_seminar_peer_001",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; Student 001 row; Uses textual evidence column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher noted that Student 001 cited a relevant passage but only partially explained its connection to the claim.",
      "score_evidence_link_id": "scoreev_sem_001_evidence_tracker",
      "score_record_id": "score_seminar_001_evidence",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; claim-and-evidence sequence 3."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_map_a"
      },
      "relevance_description": "The Group map attributes the cited passage and related claim to Student 001; the teacher makes the individual judgment.",
      "score_evidence_link_id": "scoreev_sem_001_evidence_map",
      "score_record_id": "score_seminar_001_evidence",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_seminar_map_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; Student 001 row; Integrates discussion information column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher recorded the two peer contributions synthesized by Student 001.",
      "score_evidence_link_id": "scoreev_sem_001_integrates_tracker",
      "score_record_id": "score_seminar_001_integrates",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; synthesis conclusion."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_map_a"
      },
      "relevance_description": "The Group map preserves the sequence of ideas that Student 001 connected; the teacher makes the individual judgment.",
      "score_evidence_link_id": "scoreev_sem_001_integrates_map",
      "score_record_id": "score_seminar_001_integrates",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_seminar_map_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    }
  ],
  "score_projections": [
    {
      "activity_id": "act_seminar_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_seminar_builds_on_ideas",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_001_builds",
      "scored_at": "2026-09-15T12:00:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_pe_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_seminar_textual_evidence",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_001_evidence",
      "scored_at": "2026-09-15T12:03:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_rl_cr_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "approaching"
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "mixed_basis",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "Student 001 connected two peers' interpretations and explained how the textual evidence supported a broader conclusion.",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_001_integrates",
      "scored_at": "2026-09-15T12:06:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "professional_judgment",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "insufficient_evidence",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "Available evidence confirms participation but does not yet demonstrate a sufficiently specific synthesis of ideas from several participants.",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_002_integrates_v1",
      "scored_at": "2026-09-15T12:10:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      }
    }
  ],
  "scoring_scale_projections": [
    {
      "aggregation_guidance": "Treat each Score as contextual evidence; do not infer longitudinal proficiency or Grade eligibility.",
      "intended_use": "standards_based",
      "levels": [
        {
          "label": "Developing",
          "meaning": "Evidence is limited, inconsistent, or substantially incomplete.",
          "ordering": 1,
          "value": "developing"
        },
        {
          "label": "Approaching",
          "meaning": "Evidence demonstrates partial or inconsistent performance.",
          "ordering": 2,
          "value": "approaching"
        },
        {
          "label": "Meeting",
          "meaning": "Evidence demonstrates the expected level of performance.",
          "ordering": 3,
          "value": "meeting"
        },
        {
          "label": "Exceeding",
          "meaning": "Evidence demonstrates sustained and sophisticated performance.",
          "ordering": 4,
          "value": "exceeding"
        }
      ],
      "lineage_id": "scale_proficiency_4",
      "name": "Four-Level Proficiency Scale",
      "revision": 1,
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "status_snapshot": "active"
    }
  ],
  "source_activity": {
    "contract_version": "1",
    "module_id": "concord",
    "record_id": "act_seminar_01",
    "record_kind": "activity"
  },
  "standards_result_projection": [
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_builds_on_ideas",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_001_builds_tracker",
        "scoreev_sem_001_builds_peer"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_001_builds",
      "scored_at": "2026-09-15T12:00:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_pe_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_textual_evidence",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_001_evidence_tracker",
        "scoreev_sem_001_evidence_map"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_001_evidence",
      "scored_at": "2026-09-15T12:03:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_rl_cr_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "approaching"
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_001_integrates_tracker",
        "scoreev_sem_001_integrates_map"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_001_integrates",
      "scored_at": "2026-09-15T12:06:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "insufficient_evidence",
      "evidence_link_ids": [],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_002_integrates_v1",
      "scored_at": "2026-09-15T12:10:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      }
    }
  ],
  "work": {
    "class_id": "cls_ela10_p03",
    "module_id": "concord",
    "work_id": "act_seminar_01"
  }
}
```

| Property | Exact value |
|---|---|
| Record-set ID | `rs_seminar_results_01` |
| Record-set revision | `1` |
| Manifest path | `classes/cls_ela10_p03/modules/concord/work/act_seminar_01/exports/manifests/rs_seminar_results_01/1.json` |
| Byte length | `19098` |
| Digest algorithm | `sha256` |
| SHA-256 digest | `a6147ea67b6dd3582a7087bc930a490931082ba3a48ec49d53eabf02ef8dde28` |

The manifest is a producer-owned projection, not a replacement for the Activity, Criteria, Scoring Scale, Scores, evidence, Reviews, or Moderation Records.

## 21. Core Publication Record Revision 1

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_concord_seminar_results_001
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
manifest_digest: a6147ea67b6dd3582a7087bc930a490931082ba3a48ec49d53eabf02ef8dde28
published_at: '2026-09-15T12:20:00-04:00'
academic_work_registration_revision: 1
```

Core announces the exact immutable manifest bytes. It does not copy the result arrays into the Publication Record, interpret the Score values, or make the work eligible for a Grade.

The declared capabilities are truthful:

- `criterion_scores` because criterion-level Score projections are present;
- `standards_ratings` because direct standard-backed judgments and a non-score disposition are present;
- `moderated_scores` because applicable Moderation state is included for consequential peer evidence.

A repeated request using the same work, record-set identity, revision, path, contract version, and digest is idempotent. Reusing revision `1` with different bytes, path, digest, or contract version would be an integrity conflict.

## 22. Native Score Revision and New Publication State

Additional Session 2 evidence becomes available for Student 002:

```text
reviewed teacher observation
    + moderated peer observation
    + Quillan response with exact source-publication lineage
    -> new teacher-approved Score
```

The new native Score:

```text
score_seminar_002_integrates_v2
    supersedes
score_seminar_002_integrates_v1
```

The native correction does not alter manifest revision 1 or Core Publication Record `pub_concord_seminar_results_001`. Instead, Concord generates a new manifest revision.

The Quillan evidence lineage preserves three distinct identities:

```text
Quillan response record
    -> Core source publication pub_quillan_seminar_reflection_001
    -> Concord External Reference and Score Evidence Link
```

Meridian may import both the Quillan publication and the Concord publication. Concord exposes the relationship; Meridian owns overlap and deduplication policy.

## 23. Concord Academic Result Manifest Revision 2

Manifest revision 2 contains the complete required native Score history:

- the three unchanged Student 001 Scores;
- the superseded Student 002 `insufficient_evidence` Score;
- the current Student 002 scored replacement;
- all nine active evidence-lineage rows;
- Moderation state for the two peer observations used consequentially;
- and five standards-result rows.

The exact immutable bytes are the following UTF-8 JSON, including one trailing line-feed byte after the final closing brace:

```json
{
  "activity_context": {
    "activity_id": "act_seminar_01",
    "activity_status_snapshot": "completed",
    "activity_type": "local:socratic_seminar",
    "class_id": "cls_ela10_p03",
    "focus_standard_ids": [
      "std_njsls_ela_sl_pe_9_10_1",
      "std_njsls_ela_rl_cr_9_10_1",
      "std_njsls_ela_sl_ii_9_10_2"
    ],
    "scoring_orientation": "standards_based",
    "session_references": [
      {
        "record_id": "ses_seminar_01",
        "record_kind": "session"
      },
      {
        "record_id": "ses_seminar_02",
        "record_kind": "session"
      }
    ],
    "standards_profile_id": "profile_njsls_ela_2023_09_10",
    "title_snapshot": "Evidence, Perspective, and Responsibility"
  },
  "criterion_projections": [
    {
      "criterion_id": "crit_seminar_builds_on_ideas",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_seminar_focus_rev_1",
      "definition": "Responds directly to a peer's contribution by extending, qualifying, challenging, or connecting the idea in a substantive manner.",
      "key": "builds_on_ideas",
      "label": "Builds on peers' ideas",
      "standard_id": "std_njsls_ela_sl_pe_9_10_1",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    },
    {
      "criterion_id": "crit_seminar_textual_evidence",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_seminar_focus_rev_1",
      "definition": "Selects and explains relevant textual evidence to support, refine, or challenge a claim during the seminar.",
      "key": "textual_evidence",
      "label": "Uses relevant textual evidence",
      "standard_id": "std_njsls_ela_rl_cr_9_10_1",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    },
    {
      "criterion_id": "crit_seminar_integrates_discussion",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_seminar_focus_rev_1",
      "definition": "Synthesizes relevant ideas, evidence, or perspectives introduced by several participants into a coherent contribution or conclusion.",
      "key": "integrates_discussion",
      "label": "Integrates information from the discussion",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    }
  ],
  "generated_at": "2026-09-16T12:00:00-04:00",
  "generated_provenance": {
    "actor": {
      "actor_id": "publisher_concord_001",
      "actor_kind": "system",
      "display_label_snapshot": "Concord academic-result publisher",
      "owning_system": "concord"
    },
    "application_version": "synthetic-concord-0.1",
    "note": "Generated from validated canonical Concord records.",
    "source_kind": "system",
    "timestamp": "2026-09-16T12:00:00-04:00"
  },
  "manifest_contract_version": "concord_academic_result_manifest_v1",
  "moderation_projections": [
    {
      "moderated_at": "2026-09-15T11:20:00-04:00",
      "moderation_record_id": "mod_seminar_peer_001",
      "permitted_use": "may_corroborate_teacher_evidence",
      "privacy_classification": "teacher_restricted",
      "qualification": "May corroborate teacher observation of Student 001 building on peers' ideas; it may not independently determine the final Score.",
      "status": "accepted_with_qualification",
      "target_evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_peer_001"
      },
      "target_subject_references": [
        {
          "owning_system": "core",
          "subject_id": "stu_001",
          "subject_kind": "core_student"
        }
      ]
    },
    {
      "moderated_at": "2026-09-16T10:25:00-04:00",
      "moderation_record_id": "mod_seminar_peer_003",
      "permitted_use": "may_support_one_named_subject",
      "privacy_classification": "teacher_restricted",
      "status": "accepted",
      "target_evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_peer_003"
      },
      "target_subject_references": [
        {
          "owning_system": "core",
          "subject_id": "stu_002",
          "subject_kind": "core_student"
        }
      ]
    }
  ],
  "privacy_classification": "teacher_restricted",
  "producer_module_id": "concord",
  "record_kind": "concord_academic_result_manifest",
  "record_owner": "concord",
  "record_set_id": "rs_seminar_results_01",
  "record_set_revision": 2,
  "score_evidence_link_projections": [
    {
      "evidence_locator": {
        "note": "Page 1; Student 001 row; Builds on peers' ideas column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher recorded a specific exchange in which Student 001 extended a peer's interpretation with a qualifying claim.",
      "score_evidence_link_id": "scoreev_sem_001_builds_tracker",
      "score_record_id": "score_seminar_001_builds",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; observed contribution 2."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_peer_001"
      },
      "moderation_record_id": "mod_seminar_peer_001",
      "relevance_description": "Student 004 recorded the peer idea to which Student 001 responded and described the substantive extension.",
      "score_evidence_link_id": "scoreev_sem_001_builds_peer",
      "score_record_id": "score_seminar_001_builds",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_seminar_peer_001",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; Student 001 row; Uses textual evidence column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher noted that Student 001 cited a relevant passage but only partially explained its connection to the claim.",
      "score_evidence_link_id": "scoreev_sem_001_evidence_tracker",
      "score_record_id": "score_seminar_001_evidence",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; claim-and-evidence sequence 3."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_map_a"
      },
      "relevance_description": "The Group map attributes the cited passage and related claim to Student 001; the teacher makes the individual judgment.",
      "score_evidence_link_id": "scoreev_sem_001_evidence_map",
      "score_record_id": "score_seminar_001_evidence",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_seminar_map_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; Student 001 row; Integrates discussion information column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher recorded the two peer contributions synthesized by Student 001.",
      "score_evidence_link_id": "scoreev_sem_001_integrates_tracker",
      "score_record_id": "score_seminar_001_integrates",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; synthesis conclusion."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_map_a"
      },
      "relevance_description": "The Group map preserves the sequence of ideas that Student 001 connected; the teacher makes the individual judgment.",
      "score_evidence_link_id": "scoreev_sem_001_integrates_map",
      "score_record_id": "score_seminar_001_integrates",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_seminar_map_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; synthesis contribution."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_peer_003"
      },
      "moderation_record_id": "mod_seminar_peer_003",
      "relevance_description": "The observer identifies the separate participant ideas Student 002 combined and records the resulting conclusion.",
      "score_evidence_link_id": "scoreev_sem_002_integrates_peer",
      "score_record_id": "score_seminar_002_integrates_v2",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_seminar_peer_003",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_002",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Page 1; Student 002 row; Session 2; Integrates discussion information column."
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_seminar_teacher_tracker"
      },
      "relevance_description": "Teacher recorded Student 002 connecting two peers' claims during Session 2.",
      "score_evidence_link_id": "scoreev_sem_002_integrates_tracker",
      "score_record_id": "score_seminar_002_integrates_v2",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_seminar_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_002",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Synthesis paragraph in the referenced Quillan response."
      },
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_seminar_quillan_001",
        "source_publication_reference": {
          "publication_id": "pub_quillan_seminar_reflection_001"
        }
      },
      "relevance_description": "The written reflection identifies and connects the same participant ideas observed during Session 2.",
      "score_evidence_link_id": "scoreev_sem_002_integrates_quillan",
      "score_record_id": "score_seminar_002_integrates_v2",
      "significance": "corroborating",
      "source_publication_reference": {
        "publication_id": "pub_quillan_seminar_reflection_001"
      },
      "source_record_reference": {
        "contract_version": "1",
        "module_id": "quillan",
        "record_id": "quillan_response_seminar_002",
        "record_kind": "response"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_002",
        "subject_kind": "core_student"
      }
    }
  ],
  "score_projections": [
    {
      "activity_id": "act_seminar_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_seminar_builds_on_ideas",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_001_builds",
      "scored_at": "2026-09-15T12:00:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_pe_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_seminar_textual_evidence",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_001_evidence",
      "scored_at": "2026-09-15T12:03:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_rl_cr_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "approaching"
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "mixed_basis",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "Student 001 connected two peers' interpretations and explained how the textual evidence supported a broader conclusion.",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_001_integrates",
      "scored_at": "2026-09-15T12:06:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "professional_judgment",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "superseded",
      "disposition": "insufficient_evidence",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "Available evidence confirms participation but does not yet demonstrate a sufficiently specific synthesis of ideas from several participants.",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_002_integrates_v1",
      "scored_at": "2026-09-15T12:10:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      }
    },
    {
      "activity_id": "act_seminar_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "Session 2 observation and the written synthesis reflection demonstrate that Student 002 connected several participants' ideas into a coherent conclusion.",
      "score_kind": "standard_backed",
      "score_record_id": "score_seminar_002_integrates_v2",
      "scored_at": "2026-09-16T11:40:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_02",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "supersedes_score_record_id": "score_seminar_002_integrates_v1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      },
      "value": "meeting"
    }
  ],
  "scoring_scale_projections": [
    {
      "aggregation_guidance": "Treat each Score as contextual evidence; do not infer longitudinal proficiency or Grade eligibility.",
      "intended_use": "standards_based",
      "levels": [
        {
          "label": "Developing",
          "meaning": "Evidence is limited, inconsistent, or substantially incomplete.",
          "ordering": 1,
          "value": "developing"
        },
        {
          "label": "Approaching",
          "meaning": "Evidence demonstrates partial or inconsistent performance.",
          "ordering": 2,
          "value": "approaching"
        },
        {
          "label": "Meeting",
          "meaning": "Evidence demonstrates the expected level of performance.",
          "ordering": 3,
          "value": "meeting"
        },
        {
          "label": "Exceeding",
          "meaning": "Evidence demonstrates sustained and sophisticated performance.",
          "ordering": 4,
          "value": "exceeding"
        }
      ],
      "lineage_id": "scale_proficiency_4",
      "name": "Four-Level Proficiency Scale",
      "revision": 1,
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "status_snapshot": "active"
    }
  ],
  "source_activity": {
    "contract_version": "1",
    "module_id": "concord",
    "record_id": "act_seminar_01",
    "record_kind": "activity"
  },
  "standards_result_projection": [
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_builds_on_ideas",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_001_builds_tracker",
        "scoreev_sem_001_builds_peer"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_001_builds",
      "scored_at": "2026-09-15T12:00:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_pe_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_textual_evidence",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_001_evidence_tracker",
        "scoreev_sem_001_evidence_map"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_001_evidence",
      "scored_at": "2026-09-15T12:03:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_rl_cr_9_10_1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "approaching"
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_001_integrates_tracker",
        "scoreev_sem_001_integrates_map"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_001_integrates",
      "scored_at": "2026-09-15T12:06:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "superseded",
      "disposition": "insufficient_evidence",
      "evidence_link_ids": [],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_002_integrates_v1",
      "scored_at": "2026-09-15T12:10:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_01",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      }
    },
    {
      "activity_id": "act_seminar_01",
      "class_id": "cls_ela10_p03",
      "criterion_id": "crit_seminar_integrates_discussion",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_sem_002_integrates_peer",
        "scoreev_sem_002_integrates_tracker",
        "scoreev_sem_002_integrates_quillan"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_seminar_002_integrates_v2",
      "scored_at": "2026-09-16T11:40:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proficiency_4_rev_1",
      "session_id": "ses_seminar_02",
      "standard_id": "std_njsls_ela_sl_ii_9_10_2",
      "supersedes_score_record_id": "score_seminar_002_integrates_v1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      },
      "value": "meeting"
    }
  ],
  "work": {
    "class_id": "cls_ela10_p03",
    "module_id": "concord",
    "work_id": "act_seminar_01"
  }
}
```

| Property | Exact value |
|---|---|
| Record-set ID | `rs_seminar_results_01` |
| Record-set revision | `2` |
| Manifest path | `classes/cls_ela10_p03/modules/concord/work/act_seminar_01/exports/manifests/rs_seminar_results_01/2.json` |
| Byte length | `25092` |
| Digest algorithm | `sha256` |
| SHA-256 digest | `8855b1162a9ea2c913a0c78a2c8e7c3db4d29f853c81eaab0b69aa0494624879` |

Manifest revision 2 does not mutate or replace revision 1. It is a new immutable projection with a greater logical revision.

## 24. Core Publication Record Revision 2

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_concord_seminar_results_002
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
record_set_revision: 2
manifest_contract_version: concord_academic_result_manifest_v1
manifest_path: classes/cls_ela10_p03/modules/concord/work/act_seminar_01/exports/manifests/rs_seminar_results_01/2.json
manifest_digest_algorithm: sha256
manifest_digest: 8855b1162a9ea2c913a0c78a2c8e7c3db4d29f853c81eaab0b69aa0494624879
published_at: '2026-09-16T12:05:00-04:00'
academic_work_registration_revision: 2
supersedes_publication_id: pub_concord_seminar_results_001
```

Publication revision 2 supersedes publication revision 1 within the same producer, work, publication kind, and record-set series.

The two supersession relationships remain different:

```text
native Score supersession:
score_seminar_002_integrates_v2
    -> score_seminar_002_integrates_v1

Core publication supersession:
pub_concord_seminar_results_002
    -> pub_concord_seminar_results_001
```

Neither relationship implies the other automatically. Publication supersession does not mean every Score in revision 1 was superseded.

No publication withdrawal is represented in this seminar case. The architecture can represent withdrawal through a separate immutable Core record; the project example will exercise a withdrawal scenario.

## 25. Meridian Consumption Boundary

Meridian can discover and import the two Concord publications through Core while preserving:

- `publication_id`;
- exact manifest digest;
- manifest contract version;
- record-set ID and revision;
- Academic Work Registration revision;
- source Activity reference;
- supersession and withdrawal state;
- and import time.

Meridian then applies explicit policy for:

- publication eligibility;
- Grade-item membership;
- Score eligibility;
- direct standards-evidence eligibility;
- repeated-evidence selection;
- reassessment;
- cross-producer overlap;
- Scoring Scale interpretation;
- Academic Period membership;
- proficiency calculation;
- Grade calculation;
- overrides;
- and reports.

This example does not invent Meridian records that lack a governing contract.

The following do **not** appear in either Concord manifest:

```text
academic_period_id
grade_item_id
proficiency
course_grade
report_status
```

A Meridian override would alter only a Meridian-derived result. It would not mutate a Concord Score, manifest, or Core Publication Record. A changed Concord judgment requires the native Score and republication sequence shown above.

## 26. Relationship Summary

```text
Core Class
    -> Concord Activity
        -> Sessions
        -> Groups
            -> Memberships
            -> contextual Role Assignments
        -> Packet Instance
            -> exact Packet Version
            -> Artifact Instances
                -> Artifact Pages
                    -> Core Route Registrations
                    -> Concord Scan References
                -> Artifact Authors
                -> Artifact Subjects
                -> Artifact Reviews
        -> Criterion Set revision
            -> three standard-backed Criteria
                -> one governing standard each
        -> native Score Records
            -> one explicit Score target each
            -> one Criterion each
            -> one Scoring Scale revision each
            -> Score Evidence Links
                -> teacher tracker
                -> discussion map
                -> moderated peer observation
                -> Quillan response and source publication lineage

Core Academic Work Registration
    -> registered Concord Activity

Concord native records
    -> immutable Academic Result Manifest revision 1
        -> Core Publication Record revision 1
    -> native Score supersession
    -> immutable Academic Result Manifest revision 2
        -> Core Publication Record revision 2

Core publications
    -> Meridian import
        -> policy-controlled selection, Academic Period membership,
           proficiency, Grade, override, and reporting
```

## 27. Lifecycle Walkthrough

### 27.1 Configuration and registration

```text
Activity created
    -> Sessions, Groups, Memberships, and Roles created
    -> standards profile and ordered Focus Standards selected
    -> Criterion Set and Scoring Scale selected
    -> teacher explicitly requests Core Academic Work Registration
    -> registration revision 1 created
```

No Score, manifest, publication, Grade item, or Academic Period membership exists merely because the Activity is configured.

### 27.2 Generation and routing

```text
Packet Version selected
    -> Packet Instance generated
    -> Artifact Instances generated
    -> Artifact Pages created
    -> Route Registrations created
    -> PDS2 QR codes rendered
```

Routing and publication use the same `ModuleWorkRef` but otherwise have separate records, services, paths, and lifecycles.

### 27.3 Classroom use, scan, Review, and Moderation

```text
Sessions occur
    -> paper Artifacts completed
    -> Core retains source scans
    -> PDS2 routes resolve
    -> Concord Scan References created
    -> teacher Reviews filing and attribution
    -> peer evidence Moderated where required
```

Peer Observation 2 routes before its Author and correct Subject are resolved.

### 27.4 Initial scoring and publication

```text
teacher records three scored judgments and one non-score disposition
    -> deliberate Score Evidence Links created after each parent Score
    -> manifest revision 1 generated and validated
    -> exact bytes written to revision-addressed path
    -> SHA-256 digest calculated
    -> Core Publication Record revision 1 created
```

Student 002 receives `insufficient_evidence`, not zero or `developing`.

### 27.5 Additional evidence, native supersession, and republication

```text
Session 2 evidence reviewed and Moderated
    -> Quillan source publication and response referenced
    -> teacher records new Score
    -> new Score supersedes earlier non-score disposition
    -> registration revision 2 closes the work
    -> manifest revision 2 generated
    -> Core Publication Record revision 2 supersedes publication revision 1
```

### 27.6 Meridian consumption

```text
Core publication discovery
    -> exact manifest verification
    -> Meridian import
    -> explicit eligibility and overlap policy
    -> optional proficiency, Grade, override, or report records
```

Concord and Core do not perform those Meridian-owned operations.

## 28. Invariant Validation

| Invariant | Result | Evidence in this example |
|---|---|---|
| `activity_id` is Concord's Core `work_id` | Pass | Activity, registrations, manifests, and route/publication records use `act_seminar_01` |
| Routing, registration, publication, and grading are separate | Pass | Distinct records, paths, workflows, and ownership are represented |
| Route target is an existing Artifact Page | Pass | Seven Artifact Pages precede seven registrations |
| QR contains route identity only | Pass | No Author, Subject, Criterion, standard, or Score appears in PDS2 |
| Artifact Author and Subject are separate | Pass | Student 004 authors an observation about Student 001 |
| Score target is separate from Artifact Subject | Pass | Score-Target References are explicit |
| Group Artifact may have no student Subject | Pass | Both discussion maps concern a Group and Session |
| Teacher tracker may remain one multi-Subject Artifact | Pass | One tracker has ten Subject associations |
| Routing does not require resolved attribution | Pass | Peer Observation 2 routes before Author resolution |
| Handwriting does not establish authorship | Pass | Packet and Role records resolve the Author |
| Review and Moderation do not create Scores | Pass | Separate teacher-approved Score Records follow them |
| Score Evidence Links do not predate parent Scores | Pass | All nine link timestamps are equal to or later than `scored_at` |
| Required Moderation precedes consequential use | Pass | Peer evidence links cite completed permitting decisions |
| One standard-backed Criterion has one standard | Pass | Three Criteria each identify one governing `standard_id` |
| Non-score disposition contains no value | Pass | Student 002 v1 omits `value` in native and manifest records |
| Revised Score preserves prior judgment | Pass | v2 explicitly supersedes v1 |
| External Quillan evidence remains externally owned | Pass | Source record and source publication remain Quillan/Core references |
| Manifest contains exact Criterion and scale semantics | Pass | Both revisions include all required projections |
| Exact manifest bytes are immutable and digest-bound | Pass | Both SHA-256 values are mechanically calculated from represented bytes |
| Manifest path is revision-addressed and work-scoped | Pass | Each path is beneath the exact Concord Activity work root |
| Core Publication Record does not copy results | Pass | It references path, contract, revision, and digest only |
| Publication capabilities are truthful | Pass | Criterion, standards, and Moderation projections are present |
| Publication does not imply Grade eligibility | Pass | Registration intent is formative and Meridian policy remains separate |
| Native Score and publication supersession remain distinct | Pass | Separate explicit chains are represented |
| Cross-producer overlap is exposed | Pass | Quillan source publication lineage appears in the evidence projection |
| Academic Period membership remains outside Concord | Pass | No period identifier appears in either manifest |
| Core catalog is nonauthoritative | Pass | No catalog row is treated as a source record |
| Course Grade and mastery remain outside Concord | Pass | Meridian owns calculation and reporting policy |
| Local Score publication | Not exercised | This standards-based Activity contains no local Criteria |
| Group Score publication | Not exercised | This case intentionally uses individual targets |
| Publication withdrawal | Not exercised | Reserved for another principal case |

## 29. Represented Cleanly

The conceptual contracts represent the following seminar requirements without ambiguity:

- standards-based Activity configuration;
- multiple Sessions and contextual Role rotation;
- Group-authored and peer-authored paper evidence;
- a teacher-authored multi-Subject tracker;
- route resolution before attribution Review;
- corrected Author and Subject attribution;
- rescan history;
- separate Review, Moderation, and Scoring;
- three direct standards Criteria;
- many-to-many evidence use;
- an explicit non-score disposition;
- native Score supersession;
- Quillan source-record and source-publication lineage;
- explicit Core Academic Work Registration;
- two immutable Concord Academic Result Manifest revisions;
- exact digest-bound Core Publication Records;
- publication supersession;
- and a bounded Meridian-consumption handoff.

## 30. Optional Structures Used

### Role Assignment

Role Assignment is used because students rotate contextual functions across Sessions. The Roles do not become permanent participant traits.

### External Reference

The Quillan response is linked without copying or taking ownership of the response.

### Core Publication Reference

The exact Quillan source publication is preserved so downstream overlap policy does not treat related producer results as independent by accident.

### Correction Record

Correction Records explain Author attribution, Subject attribution, and Score revision while same-type replacement records provide direct supersession traversal.

## 31. Contracts Deliberately Not Used

The case deliberately omits:

- Responsibility Assignment;
- Activity Marker;
- Work Item and Work-Item Dependency;
- Activity Event;
- Contribution Claim;
- Attachment;
- local Criterion and local Score;
- Group Score;
- evidence-only Activity publication;
- Core Publication Withdrawal;
- Core catalog rows;
- Meridian Grade, proficiency, override, and report records.

Their absence is deliberate and does not imply that the shared architecture cannot support them.

## 32. Tensions or Ambiguities

### 32.1 Sequence context below the Session level

The example uses `sequence_start` and `sequence_end` for one represented round within each Session. The later serialized Effective Context contract must define integer range validation and Session namespacing.

### 32.2 Paper scoring surface versus canonical Score

The scanned scoring rubric preserves the paper workflow and serves as Score creation provenance. The canonical judgments remain the Score Records.

### 32.3 Quillan public contract

The synthetic Quillan response and source-publication reference demonstrate lineage. Exact released Quillan record kinds, manifest contract versions, and adapter behavior remain implementation compatibility work.

### 32.4 Core runtime availability

The example targets the accepted publication architecture. Concord implementation must not pin unreleased Core registry APIs until a compatible Core release is available.

None of these questions changes the represented conceptual foundation.

## 33. Workarounds Rejected

The example deliberately rejects:

- a student-bearing QR;
- a universal student submission directory;
- using an observer or Subject as the Score target automatically;
- duplicating the teacher tracker into student-specific Artifacts;
- treating the physical recorder as sole Group author;
- inferring a blank observer name from handwriting;
- encoding Focus Standards or publication state in PDS2;
- automatic Academic Work Registration from Activity existence;
- deriving Core `academic_intent` from Concord `scoring_orientation`;
- one holistic Score tied to three standards;
- treating Review or Moderation as scoring;
- converting insufficient evidence to `developing`;
- destructive Score editing;
- mutating manifest revision 1 after the Score correction;
- reusing manifest revision 1 with new bytes;
- treating the Core catalog as authoritative;
- copying the Quillan response into Concord;
- hiding the Quillan source publication from lineage;
- treating the Quillan and Concord publications as independent evidence automatically;
- publication as automatic Grade inclusion;
- inferring Academic Period membership from native dates;
- and rewriting Concord records for a Meridian-only override.

## 34. Contract Changes Required

None.

The example fits the revised conceptual contracts and ADR 0015 without weakening an invariant, duplicating ownership, fabricating identity, or introducing a seminar-specific foundational entity.

## 35. Seminar Case Acceptance Assessment

- [x] A standards-based Activity is represented.
- [x] Core registration is explicit rather than inferred.
- [x] Activity scoring orientation and Core academic intent remain separate.
- [x] Two Core Academic Work Registration revisions are represented.
- [x] One Core standards profile and ordered Focus Standards are represented.
- [x] Separate standard-backed Criteria are used for separate standards.
- [x] Each Criterion has exactly one governing `standard_id`.
- [x] A complete immutable Scoring Scale revision is represented.
- [x] Individual standard-backed Scores are represented.
- [x] One source supports several Scores and one Score uses several sources.
- [x] Peer evidence is Reviewed and Moderated before consequential use.
- [x] Artifact Author, Artifact Subject, Score target, and scorer remain separate.
- [x] Unknown Author attribution and correction preserve history.
- [x] A rescan preserves the original source and Scan Reference.
- [x] A non-score disposition omits `value` and is not converted to low performance.
- [x] A later native Score supersedes the non-score disposition.
- [x] All Score Evidence Links are created at or after the parent Score.
- [x] A Quillan response remains externally owned.
- [x] The exact Quillan source publication is preserved in lineage.
- [x] Manifest revision 1 includes the initial non-score state.
- [x] Manifest revision 2 includes the superseded and current Score states.
- [x] Both manifests include exact Criterion, scale, Score, evidence, Moderation, and standards projections.
- [x] Both manifest byte sequences and SHA-256 digests are mechanically valid.
- [x] Two immutable Core Publication Records are represented.
- [x] Publication revision 2 explicitly supersedes revision 1.
- [x] Native Score supersession and publication supersession remain distinct.
- [x] Publication does not imply Grade eligibility or Academic Period membership.
- [x] Meridian overlap, selection, override, calculation, and reporting remain downstream policy.
- [x] PDS2 routes target existing Artifact Pages and carry no scoring semantics.
- [x] Repeated record families contain required conceptual fields.
- [x] Optional absent fields are omitted rather than represented with `null`.
- [x] No architecture-breaking workaround is required.
