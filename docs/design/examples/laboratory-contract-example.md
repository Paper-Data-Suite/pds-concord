# Representative Contract Example: Mixed-Scoring Science Laboratory

**Status:** Revised draft for representative-contract validation  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Issue:** `#12 — 11. Create representative contract examples`  
**Example family:** Science laboratory investigation  
**Scoring orientation:** `mixed`  
**Publication model:** One immutable Concord Academic Result Manifest revision published through Core  
**Revision date:** July 31, 2026  
**Revision:** 4 — reconciled with issue #13 representative-example consistency review

## 1. Case Purpose

This example tests whether the Concord conceptual contracts can represent a collaborative science laboratory involving:

- Group planning and evidence records;
- Group and individual Score targets;
- standard-backed and local Criteria in one Activity;
- Roles and specific Responsibilities;
- an absence-driven Responsibility reassignment that preserves history;
- an interrupted Session and equipment-failure Event;
- an invalid trial that is not treated as poor performance;
- a Group standards Score;
- a local Group workflow Score;
- an individual standards Score supported partly by Group evidence;
- an external ScoreForm result used as supporting evidence;
- participant-authored contribution evidence requiring Moderation;
- a contextual `absent` non-score disposition;
- mixed-module source-scan intake;
- a clearer rescan that preserves the original source;
- a non-returned instructional page that deliberately has no route;
- an explicit duplicate scan retained separately from the preferred source;
- a misrouted source page corrected without modifying the Core-retained source;
- explicit Core Academic Work Registration;
- one immutable Concord Academic Result Manifest containing both standard-backed and local Score projections;
- a Standards Result Projection containing only the standard-backed subset;
- exact ScoreForm source-publication lineage;
- one SHA-256-bound Core Publication Record;
- and a bounded Meridian-consumption analysis.

The case uses shared Activity, Group, Artifact, Review, Moderation, Criterion, Score, Event, Responsibility, External Reference, PDS2, registration, manifest, and publication contracts. It does not introduce laboratory-specific foundational entities.

This case deliberately represents one valid publication revision.

Native Score supersession and Core publication supersession are exercised by the project example. Publication withdrawal is bounded there without a complete withdrawal record.

## 2. Activity Narrative

A Biology class conducts a three-session catalase reaction-rate investigation. Two stable laboratory Groups plan a controlled procedure, collect measurements, and interpret the resulting data.

During Session 2, Student 003 is absent. A temperature-probe calibration Responsibility originally assigned to Student 003 is reassigned to Student 002 without rewriting the earlier assignment. Group A then encounters unstable probe readings. The Group stops the affected trial, marks the measurements invalid, documents the failure, replaces the probe, and completes a valid repeat trial during Session 3.

The equipment failure and interrupted Session describe context. They do not determine a low Score. The teacher separately judges:

1. Group A’s planning and conduct against a selected science standard;
2. Group A’s safe and documented workflow against a local Criterion; and
3. Student 002’s data analysis against a second selected science standard.

Student 002’s individual judgment uses specifically located Group evidence, teacher observation, a moderated contribution record, and an externally owned ScoreForm result. None of those sources automatically creates the Score.

Student 003 receives an `absent` disposition for the Session 2 individual Criterion context. The record contains no Score value and does not characterize the student’s performance in the Activity as a whole.

After the native judgments and evidence links are complete, the teacher explicitly closes the Core Academic Work Registration. Concord generates one immutable academic-result manifest revision. The manifest includes all four Score Records, including the local Group workflow Score, while its nested Standards Result Projection includes only the three standard-backed records. Core publishes the exact manifest bytes. Meridian may then import the Concord publication and the originating ScoreForm publication, apply overlap and eligibility policy, and decide whether either result contributes to a Grade or Academic Period calculation.

## 3. Governing Assumptions

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

Every returned Concord page has Artifact Page identity and a Core Route Registration before rendering. The QR identifies only the expected physical route. Group, student, Author, Subject, Criterion, standard, Score target, and Score value resolve through Concord records.

One Core-retained mixed source scan also contains a ScoreForm page. Core routes that page to ScoreForm and the Concord pages to Concord. Concord creates no Scan Reference for the ScoreForm-owned page.

A bounded routing-and-intake addendum also demonstrates a non-returned instructional page, an explicit duplicate scan, and a corrected misroute. These records preserve the same ownership and history rules without changing the principal laboratory scoring narrative.

Routing, academic registration, result publication, and Meridian consumption are separate integration domains.

The publication flow is:

```text
Concord Activity and native records
    -> explicit Core Academic Work Registration
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> Meridian import and policy-controlled selection
```

Concord owns the Activity, native records, and exact manifest bytes. Core owns Academic Work Registration revisions, Publication Records, withdrawal records, and the rebuildable registry catalog. Meridian owns publication eligibility, Grade-item membership, Academic Period membership, evidence selection, scale mapping, proficiency and Grade calculation, overrides, and reports.

The Activity's `scoring_orientation: mixed` is Concord-owned. Core's `academic_intent: summative` is a separate registration field and is not inferred from the scoring orientation.

Publication does not imply Grade eligibility, Academic Period membership, or use in any Meridian calculation.

The registry architecture used in this conceptual example exists on the newer Core architecture described by the governing documents. It must not be misrepresented as part of the released `pds-core` 0.5 runtime baseline.

## 4. Record Inventory

### 4.1 Core-owned and external references

| Record family | Count represented |
|---|---:|
| Core Class | 1 |
| Core Students | 6 |
| Authorized teacher Actor | 1 |
| Core Standards Profile | 1 |
| Core Standards | 2 |
| Core Route Registrations | 9 |
| Core Source Scans | 5 |
| Core Academic Work Registration revisions | 2 |
| Core Publication Record for Concord | 1 |
| Core source-publication reference for ScoreForm | 1 |
| ScoreForm result | 1 |

### 4.2 Concord-owned records and projections

| Record family | Count represented |
|---|---:|
| Activity | 1 |
| Sessions | 3 |
| Groups | 2 |
| Group Memberships | 6 |
| Role Assignments | 8 |
| Responsibility Assignments | 5 |
| Activity Events | 1 |
| Template Definitions | 7 |
| Template Versions | 7 |
| Packet Definition | 1 |
| Packet Version | 1 |
| Packet Components | 6 |
| Packet Instance | 1 |
| Artifact Instances | 9 |
| Artifact Pages | 10 |
| Artifact Author associations | 16 |
| Artifact Subject associations | 32 |
| Scan References | 12 |
| Artifact Reviews | 10 |
| Moderation Records | 1 |
| Correction Records | 2 |
| Criterion Set revisions | 1 |
| Criteria | 3 |
| Scoring Scale revisions | 2 |
| Score Records | 4 |
| Score Evidence Links | 11 |
| External References | 1 |
| Concord Academic Result Manifest revisions | 1 |
| Standards Result Projection rows inside the manifest | 3 |

The ninth Scan Reference is a clearer rescan of the Group A evidence organizer. The tenth is an explicit duplicate of the Group A planning page. The eleventh and twelfth preserve the initial and corrected associations for one misrouted calibration page. The tenth Review validates that calibration Artifact after corrected filing.

The manifest contains all four Score Records. Its Standards Result Projection contains three rows because the local workflow Score is deliberately excluded from the direct standards subset.

No Meridian-owned record is invented. Meridian behavior is analyzed at the ownership boundary only.

## 5. Shared Core and External References

### 5.1 Core Class

```yaml
owning_system: core
record_kind: class
record_id: cls_biology_p05
display_label: Biology — Period 5
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

### 5.4 Standards Profile and Focus Standards

```yaml
standards_profile:
  owning_system: core
  record_kind: standards_profile
  record_id: profile_njsls_sci_2020_hs
  display_label: NJSLS Science 2020 — High School
standards:
- owning_system: core
  record_kind: standard
  record_id: std_njsls_sci_sep_3_plan_conduct
  display_code: SEP.3
  display_label: Plan and conduct investigations using appropriate methods and controls
- owning_system: core
  record_kind: standard
  record_id: std_njsls_sci_sep_4_analyze_interpret
  display_code: SEP.4
  display_label: Analyze and interpret data to support scientific explanations
```


The display metadata is illustrative. Durable identity comes from the Core-owned `record_id` values.

## 6. Activity and Collaboration Records

### 6.1 Activity

```yaml
record_owner: concord
record_kind: activity
activity_id: act_lab_catalase_01
class_reference:
  module_id: core
  record_kind: class
  record_id: cls_biology_p05
title: Catalase Reaction Rate Investigation
activity_type: local:science_laboratory
description: A three-session collaborative investigation in which Groups plan and conduct a catalase reaction-rate
  experiment, respond to an equipment failure, revise their method, and analyze the resulting data.
scoring_orientation: mixed
standards_profile_id: profile_njsls_sci_2020_hs
focus_standard_ids:
- std_njsls_sci_sep_3_plan_conduct
- std_njsls_sci_sep_4_analyze_interpret
criterion_set_ids:
- critset_lab_mixed_rev_1
status: completed
privacy_policy:
  classification: classroom_shared
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-05T14:20:00-04:00'
  source_kind: manual
  note: Activity configured by the teacher.
updated_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-09T14:30:00-04:00'
  source_kind: manual
  note: Activity marked completed after scoring.
```


The Activity declares `mixed` because it produces both direct standards judgments and a local workflow judgment. Focus Standard selection does not create performance results.

### 6.2 Sessions

```yaml
sessions:
- record_owner: concord
  record_kind: session
  session_id: ses_lab_01
  activity_id: act_lab_catalase_01
  sequence: 1
  label: Planning and Baseline Trial
  scheduled_start: '2026-10-06T11:05:00-04:00'
  scheduled_end: '2026-10-06T11:50:00-04:00'
  actual_start: '2026-10-06T11:06:00-04:00'
  actual_end: '2026-10-06T11:49:00-04:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:25:00-04:00'
    source_kind: manual
    note: Session configured.
- record_owner: concord
  record_kind: session
  session_id: ses_lab_02
  activity_id: act_lab_catalase_01
  sequence: 2
  label: Controlled Trials and Equipment Interruption
  scheduled_start: '2026-10-07T11:05:00-04:00'
  scheduled_end: '2026-10-07T11:50:00-04:00'
  actual_start: '2026-10-07T11:05:00-04:00'
  actual_end: '2026-10-07T11:43:00-04:00'
  status: interrupted
  status_reason:
    reason_code: equipment_failure
    note: Group A temperature probe produced unstable readings, so the affected trial was stopped and documented.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-10-07T11:32:00-04:00'
    related_record:
      record_kind: activity_event
      record_id: event_lab_probe_failure_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:26:00-04:00'
    source_kind: manual
    note: Session configured.
- record_owner: concord
  record_kind: session
  session_id: ses_lab_03
  activity_id: act_lab_catalase_01
  sequence: 3
  label: Revised Trial and Data Analysis
  scheduled_start: '2026-10-08T11:05:00-04:00'
  scheduled_end: '2026-10-08T11:50:00-04:00'
  actual_start: '2026-10-08T11:05:00-04:00'
  actual_end: '2026-10-08T11:50:00-04:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:27:00-04:00'
    source_kind: manual
    note: Session configured.
```


Session 2 is `interrupted`, not failed. Its status does not set any Score disposition automatically.

### 6.3 Groups

```yaml
groups:
- record_owner: concord
  record_kind: group
  group_id: grp_lab_a
  activity_id: act_lab_catalase_01
  label: Laboratory Group A
  description: Primary Group used to demonstrate equipment interruption, reassignment, and mixed scoring.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:35:00-04:00'
    source_kind: manual
    note: Activity-specific Group created.
- record_owner: concord
  record_kind: group
  group_id: grp_lab_b
  activity_id: act_lab_catalase_01
  label: Laboratory Group B
  description: Comparison Group completing the same investigation without the probe interruption.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:36:00-04:00'
    source_kind: manual
    note: Activity-specific Group created.
```

### 6.4 Group Memberships

```yaml
group_memberships:
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_lab_a_001
  group_id: grp_lab_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:40:00-04:00'
    source_kind: manual
    note: Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_lab_a_002
  group_id: grp_lab_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:40:00-04:00'
    source_kind: manual
    note: Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_lab_a_003
  group_id: grp_lab_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:40:00-04:00'
    source_kind: manual
    note: Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_lab_b_004
  group_id: grp_lab_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:40:00-04:00'
    source_kind: manual
    note: Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_lab_b_005
  group_id: grp_lab_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:40:00-04:00'
    source_kind: manual
    note: Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_lab_b_006
  group_id: grp_lab_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T14:40:00-04:00'
    source_kind: manual
    note: Group Membership created.
```


Membership establishes Activity context only. It does not prove authorship, contribution, Role fulfillment, or performance.

### 6.5 Role Assignments

```yaml
role_assignments:
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_a_materials
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  membership_id: mem_lab_a_001
  group_id: grp_lab_a
  role_key: local:materials_manager
  role_label_snapshot: Materials Manager
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_a_recorder
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  membership_id: mem_lab_a_002
  group_id: grp_lab_a
  role_key: local:data_recorder
  role_label_snapshot: Data Recorder
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_a_procedure_s1
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  membership_id: mem_lab_a_003
  group_id: grp_lab_a
  role_key: local:procedure_lead
  role_label_snapshot: Procedure Lead
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_a_procedure_s2
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  membership_id: mem_lab_a_002
  group_id: grp_lab_a
  role_key: local:procedure_lead
  role_label_snapshot: Procedure Lead
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_02
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_a_procedure_s3
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  membership_id: mem_lab_a_003
  group_id: grp_lab_a
  role_key: local:procedure_lead
  role_label_snapshot: Procedure Lead
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_03
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_b_materials
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  membership_id: mem_lab_b_004
  group_id: grp_lab_b
  role_key: local:materials_manager
  role_label_snapshot: Materials Manager
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_b_recorder
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  membership_id: mem_lab_b_005
  group_id: grp_lab_b
  role_key: local:data_recorder
  role_label_snapshot: Data Recorder
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_lab_b_procedure
  activity_id: act_lab_catalase_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  membership_id: mem_lab_b_006
  group_id: grp_lab_b
  role_key: local:procedure_lead
  role_label_snapshot: Procedure Lead
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
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
    timestamp: '2026-10-05T14:50:00-04:00'
    source_kind: manual
    note: Contextual laboratory Role assigned.
```


Student 003’s procedure-lead Role applies to Sessions 1 and 3 through separate records. Student 002 holds the temporary Session 2 procedure-lead Role. The earlier Role history is not rewritten.

### 6.6 Responsibility Assignments

```yaml
responsibility_assignments:
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_lab_a_probe_v1
  activity_id: act_lab_catalase_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  description: Calibrate and verify the temperature probe before controlled trials.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_02
  group_id: grp_lab_a
  expected_output: Verified calibration note on the procedure organizer.
  status: reassigned
  assigned_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  status_reason:
    reason_code: participant_absent
    note: Student 003 was absent during Session 2, so the responsibility was reassigned before trial setup.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-10-07T11:04:00-04:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-05T15:00:00-04:00'
    source_kind: manual
    note: Responsibility assigned during planning.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_lab_a_probe_v2
  activity_id: act_lab_catalase_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  description: Calibrate and verify the temperature probe before controlled trials.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_02
  group_id: grp_lab_a
  expected_output: Verified calibration note on the procedure organizer.
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
    timestamp: '2026-10-07T11:04:00-04:00'
    source_kind: manual
    note: Responsibility reassigned because the original assignee was absent.
  supersedes_responsibility_assignment_id: resp_lab_a_probe_v1
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_lab_a_data
  activity_id: act_lab_catalase_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  description: Record trial conditions, raw measurements, and invalid-trial annotations.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  group_id: grp_lab_a
  expected_output: Complete evidence organizer entries.
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
    timestamp: '2026-10-05T15:02:00-04:00'
    source_kind: manual
    note: Responsibility assigned during planning.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_lab_a_cleanup
  activity_id: act_lab_catalase_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  description: Manage materials, disposal, and final station cleanup.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_01
    - ses_lab_02
    - ses_lab_03
  group_id: grp_lab_a
  expected_output: Safe and complete station reset.
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
    timestamp: '2026-10-05T15:03:00-04:00'
    source_kind: manual
    note: Responsibility assigned during planning.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_lab_b_trial_control
  activity_id: act_lab_catalase_01
  assignee_reference:
    record_kind: group
    record_id: grp_lab_b
  description: Maintain the declared control condition across repeated trials.
  effective_context:
    activity_id: act_lab_catalase_01
    session_ids:
    - ses_lab_02
    - ses_lab_03
  group_id: grp_lab_b
  expected_output: Control-condition entries in the Group evidence organizer.
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
    timestamp: '2026-10-05T15:04:00-04:00'
    source_kind: manual
    note: Group-level responsibility assigned.
```


The replacement Responsibility identifies the earlier assignment it supersedes. The original assignment remains available and its `reassigned` status does not imply failure by Student 003.

### 6.7 Activity Event

```yaml
record_owner: concord
record_kind: activity_event
activity_event_id: event_lab_probe_failure_01
activity_id: act_lab_catalase_01
session_id: ses_lab_02
event_type: troubleshooting
occurred_at: '2026-10-07T11:28:00-04:00'
sequence: 1
group_id: grp_lab_a
contributor_references:
- actor_kind: core_student
  actor_id: stu_001
  owning_system: core
  display_label_snapshot: Student 001
- actor_kind: core_student
  actor_id: stu_002
  owning_system: core
  display_label_snapshot: Student 002
- actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
subject_references:
- subject_kind: concord_group
  subject_id: grp_lab_a
  owning_system: concord
description: The temperature probe produced unstable readings after setup. Group A stopped the trial, marked the
  measurements invalid, switched to a verified backup probe, and scheduled a repeat trial.
outcome: The affected trial was excluded from analysis; the Group documented the failure and revised its procedure.
status: completed
privacy_policy:
  classification: group_and_teacher
  audience_references:
  - record_kind: group
    record_id: grp_lab_a
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-07T11:34:00-04:00'
  source_kind: manual
  note: Teacher recorded the meaningful equipment-interruption event.
```


The Event explains the invalid trial and procedural revision. It is evidence-bearing context, not a Score and not automatic proof of either poor or strong performance.

## 7. Template and Packet Records

### 7.1 Template Definitions

```yaml
template_definitions:
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_lab_plan
  name: Laboratory Prediction and Planning Sheet
  artifact_category: local:lab_planning
  purpose: Record the Group prediction, variables, controls, and proposed method.
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
    timestamp: '2026-10-01T15:00:00-04:00'
    source_kind: manual
    note: Reusable laboratory template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_lab_organizer
  name: Laboratory Procedure and Evidence Organizer
  artifact_category: local:lab_evidence_organizer
  purpose: Record procedure decisions, raw measurements, valid and invalid trials, and analysis notes.
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
    timestamp: '2026-10-01T15:05:00-04:00'
    source_kind: manual
    note: Reusable laboratory template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_lab_troubleshoot
  name: Laboratory Troubleshooting Log
  artifact_category: local:troubleshooting_log
  purpose: Document an interruption, diagnosis, revision, and retest decision.
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
    timestamp: '2026-10-01T15:10:00-04:00'
    source_kind: manual
    note: Reusable laboratory template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_lab_contribution
  name: Laboratory Contribution Record
  artifact_category: local:contribution_record
  purpose: Record participant descriptions of individual and Group contributions for teacher Review.
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
    timestamp: '2026-10-01T15:15:00-04:00'
    source_kind: manual
    note: Reusable laboratory template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_lab_teacher_tracker
  name: Laboratory Teacher Observation Tracker
  artifact_category: local:teacher_observation
  purpose: Record teacher observations across Groups, students, Criteria, and Sessions.
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
    timestamp: '2026-10-01T15:20:00-04:00'
    source_kind: manual
    note: Reusable laboratory template lineage created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_lab_scoring_rubric
  name: Laboratory Mixed Scoring Rubric
  artifact_category: local:scoring_rubric
  purpose: Provide a paper surface for separate standards-based and local judgments.
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
    timestamp: '2026-10-01T15:25:00-04:00'
    source_kind: manual
    note: Reusable laboratory template lineage created.
```

### 7.2 Immutable Template Versions

```yaml
template_versions:
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_lab_plan_r1
  template_id: tmpl_lab_plan
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_lab_plan_r1
  artifact_category: local:lab_planning
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
  supported_criterion_ids:
  - crit_lab_plan_conduct
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
    timestamp: '2026-10-02T15:00:00-04:00'
    source_kind: manual
    note: Immutable printable laboratory revision created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_lab_organizer_r1
  template_id: tmpl_lab_organizer
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_lab_organizer_r1
  artifact_category: local:lab_evidence_organizer
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
  supported_criterion_ids:
  - crit_lab_plan_conduct
  - crit_lab_analyze_data
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
    timestamp: '2026-10-02T15:05:00-04:00'
    source_kind: manual
    note: Immutable printable laboratory revision created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_lab_troubleshoot_r1
  template_id: tmpl_lab_troubleshoot
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_lab_troubleshoot_r1
  artifact_category: local:troubleshooting_log
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
    mode: local:recorder_for_group
  default_subject_expectation:
    mode: local:documented_event
  supported_criterion_ids:
  - crit_lab_safe_workflow
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
    timestamp: '2026-10-02T15:10:00-04:00'
    source_kind: manual
    note: Immutable printable laboratory revision created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_lab_contribution_r1
  template_id: tmpl_lab_contribution
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_lab_contribution_r1
  artifact_category: local:contribution_record
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
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:co_author
  default_subject_expectation:
    mode: local:represented_group
  supported_criterion_ids:
  - crit_lab_analyze_data
  - crit_lab_safe_workflow
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
    timestamp: '2026-10-02T15:15:00-04:00'
    source_kind: manual
    note: Immutable printable laboratory revision created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_lab_teacher_tracker_r1
  template_id: tmpl_lab_teacher_tracker
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_lab_teacher_tracker_r1
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
  supported_criterion_ids:
  - crit_lab_plan_conduct
  - crit_lab_analyze_data
  - crit_lab_safe_workflow
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
    timestamp: '2026-10-02T15:20:00-04:00'
    source_kind: manual
    note: Immutable printable laboratory revision created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_lab_scoring_rubric_r1
  template_id: tmpl_lab_scoring_rubric
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_lab_scoring_rubric_r1
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
  supported_criterion_ids:
  - crit_lab_plan_conduct
  - crit_lab_analyze_data
  - crit_lab_safe_workflow
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
    timestamp: '2026-10-02T15:25:00-04:00'
    source_kind: manual
    note: Immutable printable laboratory revision created.
  status: active
```


Each Template Version supplies the exact rendering reference, Artifact category, page manifest, expected-return behavior, privacy default, authorship and Subject expectations, QR requirements, and supported Criteria.

### 7.3 Packet Definition

```yaml
record_owner: concord
record_kind: packet_definition
packet_definition_id: pktdef_lab_mixed
name: Mixed-Scoring Laboratory Packet
purpose: Assemble Group planning, evidence, troubleshooting, contribution, observation, and scoring surfaces for
  one laboratory Activity.
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-03T14:00:00-04:00'
  source_kind: manual
  note: Reusable laboratory packet lineage created.
```

### 7.4 Packet Version

```yaml
record_owner: concord
record_kind: packet_version
packet_version_id: pktv_lab_mixed_r1
packet_definition_id: pktdef_lab_mixed
version_label: Revision 1
revision_sequence: 1
component_ids:
- pktcmp_lab_01
- pktcmp_lab_02
- pktcmp_lab_03
- pktcmp_lab_04
- pktcmp_lab_05
- pktcmp_lab_06
generation_rules:
  packet_scope: one_activity
  assembly_order: component_sequence
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-03T14:10:00-04:00'
  source_kind: manual
  note: Immutable laboratory packet composition created.
status: active
```

### 7.5 Packet Components

```yaml
packet_components:
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_lab_01
  packet_version_id: pktv_lab_mixed_r1
  sequence: 1
  component_kind: concord_template
  template_version_id: tmplv_lab_plan_r1
  quantity_rule:
    mode: one_per_group
  audience_rule:
    target_kind: concord_group
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_lab_02
  packet_version_id: pktv_lab_mixed_r1
  sequence: 2
  component_kind: concord_template
  template_version_id: tmplv_lab_organizer_r1
  quantity_rule:
    mode: one_per_group
  audience_rule:
    target_kind: concord_group
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_lab_03
  packet_version_id: pktv_lab_mixed_r1
  sequence: 3
  component_kind: concord_template
  template_version_id: tmplv_lab_troubleshoot_r1
  quantity_rule:
    mode: conditional
    maximum_quantity: 2
  audience_rule:
    target_kind: concord_group
  requirement_level: conditional
  condition: Generate when a Group records an interruption or invalid trial.
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_lab_04
  packet_version_id: pktv_lab_mixed_r1
  sequence: 4
  component_kind: concord_template
  template_version_id: tmplv_lab_contribution_r1
  quantity_rule:
    mode: selected_groups
    count: 1
  audience_rule:
    group_id: grp_lab_a
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_lab_05
  packet_version_id: pktv_lab_mixed_r1
  sequence: 5
  component_kind: concord_template
  template_version_id: tmplv_lab_teacher_tracker_r1
  quantity_rule:
    mode: fixed
    quantity: 1
  audience_rule:
    target_kind: authorized_actor
  requirement_level: required
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_lab_06
  packet_version_id: pktv_lab_mixed_r1
  sequence: 6
  component_kind: concord_template
  template_version_id: tmplv_lab_scoring_rubric_r1
  quantity_rule:
    mode: fixed
    quantity: 1
  audience_rule:
    target_kind: authorized_actor
  requirement_level: required
```


The troubleshooting component is conditional. The Packet Version does not require every Group to produce a troubleshooting log when no meaningful interruption occurs.

### 7.6 Packet Instance

```yaml
record_owner: concord
record_kind: packet_instance
packet_instance_id: pkt_lab_01
packet_version_id: pktv_lab_mixed_r1
activity_id: act_lab_catalase_01
generation_status: completed
generated_at: '2026-10-06T08:00:00-04:00'
generated_by:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
artifact_instance_ids:
- art_lab_plan_a
- art_lab_plan_b
- art_lab_organizer_a
- art_lab_organizer_b
- art_lab_troubleshoot_a
- art_lab_contribution_a
- art_lab_teacher_tracker
- art_lab_scoring_rubric
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-06T08:00:00-04:00'
  source_kind: generated
  source_reference:
    record_kind: packet_version
    record_id: pktv_lab_mixed_r1
  note: Packet generated for the configured laboratory Activity.
```


The Packet Instance preserves the exact Packet Version and complete generated Artifact membership.

## 8. Artifact and Routing Records

### 8.1 Artifact Instances

```yaml
artifact_instances:
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_plan_a
  template_version_id: tmplv_lab_plan_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:lab_planning
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_lab_plan_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:01:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_plan_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_lab_01
  group_id: grp_lab_a
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_plan_b
  template_version_id: tmplv_lab_plan_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:lab_planning
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_lab_plan_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:02:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_plan_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_lab_01
  group_id: grp_lab_b
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_organizer_a
  template_version_id: tmplv_lab_organizer_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:lab_evidence_organizer
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_lab_organizer_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:03:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_organizer_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_lab_03
  group_id: grp_lab_a
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_organizer_b
  template_version_id: tmplv_lab_organizer_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:lab_evidence_organizer
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_lab_organizer_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:04:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_organizer_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_lab_03
  group_id: grp_lab_b
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_troubleshoot_a
  template_version_id: tmplv_lab_troubleshoot_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:troubleshooting_log
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_lab_troubleshoot_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:05:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_troubleshoot_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_lab_02
  group_id: grp_lab_a
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_contribution_a
  template_version_id: tmplv_lab_contribution_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:contribution_record
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_lab_contribution_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:06:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_contribution_r1
    note: Artifact generated from the immutable Template Version.
  session_id: ses_lab_03
  group_id: grp_lab_a
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_teacher_tracker
  template_version_id: tmplv_lab_teacher_tracker_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:teacher_observation
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_lab_tracker_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:07:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_teacher_tracker_r1
    note: Artifact generated from the immutable Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_lab_scoring_rubric
  template_version_id: tmplv_lab_scoring_rubric_r1
  activity_id: act_lab_catalase_01
  packet_instance_id: pkt_lab_01
  artifact_category: local:scoring_rubric
  generation_status: completed
  expected_return_status: returned_expected
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_lab_rubric_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:08:00-04:00'
    source_kind: generated
    source_reference:
      record_kind: template_version
      record_id: tmplv_lab_scoring_rubric_r1
    note: Artifact generated from the immutable Template Version.
```


Generation state, expected-return state, Artifact lifecycle, privacy, and page membership remain separate fields.

### 8.2 Artifact Pages

```yaml
artifact_pages:
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_plan_a_01
  artifact_instance_id: art_lab_plan_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_plan_a_01
  human_fallback: LAB-01-01
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:01:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_plan_a
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_plan_b_01
  artifact_instance_id: art_lab_plan_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_plan_b_01
  human_fallback: LAB-01-02
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:02:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_plan_b
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_organizer_a_01
  artifact_instance_id: art_lab_organizer_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_organizer_a_01
  human_fallback: LAB-01-03
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:03:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_organizer_a
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_organizer_b_01
  artifact_instance_id: art_lab_organizer_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_organizer_b_01
  human_fallback: LAB-01-04
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:04:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_organizer_b
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_troubleshoot_a_01
  artifact_instance_id: art_lab_troubleshoot_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_troubleshoot_a_01
  human_fallback: LAB-01-05
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:05:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_troubleshoot_a
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_contribution_a_01
  artifact_instance_id: art_lab_contribution_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_contribution_a_01
  human_fallback: LAB-01-06
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:06:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_contribution_a
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_tracker_01
  artifact_instance_id: art_lab_teacher_tracker
  page_number: 1
  expected_page_count: 1
  page_kind: observation
  return_expected: true
  route_required: true
  route_id: route_lab_tracker_01
  human_fallback: LAB-01-07
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:07:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_teacher_tracker
    note: Page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_rubric_01
  artifact_instance_id: art_lab_scoring_rubric
  page_number: 1
  expected_page_count: 1
  page_kind: rubric
  return_expected: true
  route_required: true
  route_id: route_lab_rubric_01
  human_fallback: LAB-01-08
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:08:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_scoring_rubric
    note: Page identity created before route registration and rendering.
```

### 8.3 Core Route Registrations

```yaml
route_registrations:
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_plan_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_plan_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_plan_a_01
  status: active
  registered_at: '2026-10-06T08:01:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_plan_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_plan_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_plan_b_01
  status: active
  registered_at: '2026-10-06T08:02:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_organizer_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_organizer_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_organizer_a_01
  status: active
  registered_at: '2026-10-06T08:03:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_organizer_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_organizer_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_organizer_b_01
  status: active
  registered_at: '2026-10-06T08:04:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_troubleshoot_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_troubleshoot_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_troubleshoot_a_01
  status: active
  registered_at: '2026-10-06T08:05:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_contribution_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_contribution_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_contribution_a_01
  status: active
  registered_at: '2026-10-06T08:06:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_tracker_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_tracker_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_tracker_01
  status: active
  registered_at: '2026-10-06T08:07:20-04:00'
- record_owner: core
  record_kind: route_registration
  route_id: route_lab_rubric_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
    route_id: route_lab_rubric_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_lab_rubric_01
  status: active
  registered_at: '2026-10-06T08:08:20-04:00'
```


Representative PDS2 locator:

```text
PDS2|m=concord|c=cls_biology_p05|w=act_lab_catalase_01|r=route_lab_organizer_a_01
```

No locator contains student identity, Group identity, Author, Subject, Criterion, standard, or Score context.

## 9. Artifact Author Associations

```yaml
artifact_authors:
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_plan_a_group
  artifact_instance_id: art_lab_plan_a
  author_reference:
    record_kind: group
    record_id: grp_lab_a
  authorship_mode: collective_group_author
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: packet_configuration
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T12:00:00-04:00'
    source_kind: manual
    note: Group authorship confirmed during Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_plan_a_recorder
  artifact_instance_id: art_lab_plan_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_lab_a
  role_assignment_id: role_lab_a_recorder
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: role_assignment_and_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T12:01:00-04:00'
    source_kind: manual
    note: Recorder attribution confirmed without treating the recorder as sole Author.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_plan_b_group
  artifact_instance_id: art_lab_plan_b
  author_reference:
    record_kind: group
    record_id: grp_lab_b
  authorship_mode: collective_group_author
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: packet_configuration
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T12:02:00-04:00'
    source_kind: manual
    note: Group authorship confirmed during Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_plan_b_recorder
  artifact_instance_id: art_lab_plan_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_lab_b
  role_assignment_id: role_lab_b_recorder
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: role_assignment_and_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T12:03:00-04:00'
    source_kind: manual
    note: Recorder attribution confirmed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_organizer_a_group
  artifact_instance_id: art_lab_organizer_a
  author_reference:
    record_kind: group
    record_id: grp_lab_a
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:05:00-04:00'
    source_kind: manual
    note: Group authorship confirmed after final return.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_organizer_a_recorder
  artifact_instance_id: art_lab_organizer_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_lab_a
  role_assignment_id: role_lab_a_recorder
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: role_assignment_and_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:06:00-04:00'
    source_kind: manual
    note: Recorder attribution confirmed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_organizer_b_group
  artifact_instance_id: art_lab_organizer_b
  author_reference:
    record_kind: group
    record_id: grp_lab_b
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:07:00-04:00'
    source_kind: manual
    note: Group authorship confirmed after final return.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_organizer_b_recorder
  artifact_instance_id: art_lab_organizer_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_lab_b
  role_assignment_id: role_lab_b_recorder
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: role_assignment_and_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:08:00-04:00'
    source_kind: manual
    note: Recorder attribution confirmed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_troubleshoot_a_group
  artifact_instance_id: art_lab_troubleshoot_a
  author_reference:
    record_kind: group
    record_id: grp_lab_a
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T12:05:00-04:00'
    source_kind: manual
    note: Group authorship confirmed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_troubleshoot_a_recorder
  artifact_instance_id: art_lab_troubleshoot_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  authorship_mode: recorder_for_group
  represented_group_id: grp_lab_a
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T12:06:00-04:00'
    source_kind: manual
    note: Student 001 recorded the troubleshooting sequence for the Group.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_contribution_a_001
  artifact_instance_id: art_lab_contribution_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  authorship_mode: co_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: signed_contribution_section
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:10:00-04:00'
    source_kind: manual
    note: Signed contribution section reviewed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_contribution_a_002
  artifact_instance_id: art_lab_contribution_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  authorship_mode: co_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: signed_contribution_section
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:11:00-04:00'
    source_kind: manual
    note: Signed contribution section reviewed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_contribution_a_003
  artifact_instance_id: art_lab_contribution_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  authorship_mode: co_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: signed_contribution_section
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:12:00-04:00'
    source_kind: manual
    note: Signed contribution section reviewed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_tracker_teacher
  artifact_instance_id: art_lab_teacher_tracker
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: not_applicable
  attribution_status: confirmed
  attribution_source: teacher_creation
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-08T12:15:00-04:00'
    source_kind: manual
    note: Teacher authorship confirmed.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_lab_rubric_teacher
  artifact_instance_id: art_lab_scoring_rubric
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: not_applicable
  attribution_status: confirmed
  attribution_source: teacher_creation
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T12:00:00-04:00'
    source_kind: manual
    note: Teacher authorship confirmed.
```


The Group Artifacts use separate collective Group and recorder associations. Recorder status never establishes sole authorship. The contribution record has three individual co-Authors, each retaining an individual-view representation status.

## 10. Artifact Subject Associations

```yaml
artifact_subjects:
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_plan_a_group
  artifact_instance_id: art_lab_plan_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_a
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
    timestamp: '2026-10-06T08:20:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_plan_a_session
  artifact_instance_id: art_lab_plan_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_01
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
    timestamp: '2026-10-06T08:20:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_plan_b_group
  artifact_instance_id: art_lab_plan_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_b
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
    timestamp: '2026-10-06T08:20:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_plan_b_session
  artifact_instance_id: art_lab_plan_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_01
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
    timestamp: '2026-10-06T08:20:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_org_a_group
  artifact_instance_id: art_lab_organizer_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_a
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
    timestamp: '2026-10-06T08:21:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_org_a_session2
  artifact_instance_id: art_lab_organizer_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_02
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
    timestamp: '2026-10-06T08:21:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_org_a_session3
  artifact_instance_id: art_lab_organizer_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_03
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
    timestamp: '2026-10-06T08:21:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_org_b_group
  artifact_instance_id: art_lab_organizer_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_b
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
    timestamp: '2026-10-06T08:21:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_org_b_session2
  artifact_instance_id: art_lab_organizer_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_02
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
    timestamp: '2026-10-06T08:21:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_org_b_session3
  artifact_instance_id: art_lab_organizer_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_03
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
    timestamp: '2026-10-06T08:21:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_trouble_group
  artifact_instance_id: art_lab_troubleshoot_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_a
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
    timestamp: '2026-10-07T12:08:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_trouble_event
  artifact_instance_id: art_lab_troubleshoot_a
  subject_reference:
    subject_kind: concord_activity_event
    subject_id: event_lab_probe_failure_01
    owning_system: concord
  subject_role: documented_event
  confirmation_status: confirmed
  assignment_source: teacher_review
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T12:08:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_trouble_session
  artifact_instance_id: art_lab_troubleshoot_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_02
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
    timestamp: '2026-10-07T12:08:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_contribution_group
  artifact_instance_id: art_lab_contribution_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_a
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
    timestamp: '2026-10-08T12:20:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_contribution_001
  artifact_instance_id: art_lab_contribution_a
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
    timestamp: '2026-10-08T12:20:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_contribution_002
  artifact_instance_id: art_lab_contribution_a
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
    timestamp: '2026-10-08T12:20:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_contribution_003
  artifact_instance_id: art_lab_contribution_a
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
    timestamp: '2026-10-08T12:20:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_contribution_session
  artifact_instance_id: art_lab_contribution_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_03
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
    timestamp: '2026-10-08T12:20:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_001
  artifact_instance_id: art_lab_teacher_tracker
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_002
  artifact_instance_id: art_lab_teacher_tracker
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_003
  artifact_instance_id: art_lab_teacher_tracker
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_004
  artifact_instance_id: art_lab_teacher_tracker
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_005
  artifact_instance_id: art_lab_teacher_tracker
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_006
  artifact_instance_id: art_lab_teacher_tracker
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_a
  artifact_instance_id: art_lab_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_a
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_b
  artifact_instance_id: art_lab_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_b
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_1
  artifact_instance_id: art_lab_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_01
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_2
  artifact_instance_id: art_lab_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_02
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_tracker_3
  artifact_instance_id: art_lab_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_03
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
    timestamp: '2026-10-08T12:25:00-04:00'
    source_kind: manual
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_rubric_activity
  artifact_instance_id: art_lab_scoring_rubric
  subject_reference:
    subject_kind: concord_activity
    subject_id: act_lab_catalase_01
    owning_system: concord
  subject_role: activity_context
  confirmation_status: confirmed
  assignment_source: packet_configuration
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-06T08:28:00-04:00'
    source_kind: generated
    note: Artifact Subject association recorded.
  privacy_policy:
    classification: teacher_restricted
```


The teacher tracker remains one Artifact with several student, Group, and Session Subjects. The Group planning and evidence Artifacts require no individual student Subject. Artifact Subject does not create a Score target.

## 11. Scan References and Mixed Scan Intake

### 11.1 Core-Retained Source Scans

```yaml
core_source_scans:
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_lab_batch_01
  source_filename: synthetic_lab_planning_batch.pdf
  retained_at: '2026-10-06T12:30:00-04:00'
  page_count: 3
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_lab_mixed_batch_02
  source_filename: synthetic_lab_mixed_batch.pdf
  retained_at: '2026-10-08T12:30:00-04:00'
  page_count: 5
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_lab_batch_03
  source_filename: synthetic_lab_scoring_and_rescan.pdf
  retained_at: '2026-10-09T12:30:00-04:00'
  page_count: 2
```


The mixed batch contains:

| Source page index | Route owner | Routed record |
|---:|---|---|
| 0 | Concord | Group A evidence organizer |
| 1 | Concord | Group B evidence organizer |
| 2 | Concord | Group A troubleshooting log |
| 3 | Concord | Group A contribution record |
| 4 | ScoreForm | Student 002 accountability sheet |

Core retains the complete source. Concord creates Scan References only for pages routed to Concord.

### 11.2 Concord Scan References

```yaml
scan_references:
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_plan_a
  artifact_page_id: page_lab_plan_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_batch_01
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_01
      owning_system: core
    timestamp: '2026-10-06T12:31:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_plan_b
  artifact_page_id: page_lab_plan_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_batch_01
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_02
      owning_system: core
    timestamp: '2026-10-06T12:32:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_tracker
  artifact_page_id: page_lab_tracker_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_batch_01
  source_page_index: 2
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_03
      owning_system: core
    timestamp: '2026-10-06T12:33:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_organizer_a_initial
  artifact_page_id: page_lab_organizer_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_mixed_batch_02
  source_page_index: 0
  routing_status: routed
  readability_status: partially_readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: false
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_04
      owning_system: core
    timestamp: '2026-10-08T12:34:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
  status_reason:
    reason_code: clearer_rescan_available
    note: A later retained source provides a clearer image of the same Artifact Page.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-10-09T12:42:00-04:00'
    related_record:
      record_kind: scan_reference
      record_id: scanref_lab_organizer_a_rescan
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_organizer_b
  artifact_page_id: page_lab_organizer_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_mixed_batch_02
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_05
      owning_system: core
    timestamp: '2026-10-08T12:35:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_troubleshoot_a
  artifact_page_id: page_lab_troubleshoot_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_mixed_batch_02
  source_page_index: 2
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_06
      owning_system: core
    timestamp: '2026-10-08T12:36:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_contribution_a
  artifact_page_id: page_lab_contribution_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_mixed_batch_02
  source_page_index: 3
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_07
      owning_system: core
    timestamp: '2026-10-08T12:37:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_rubric
  artifact_page_id: page_lab_rubric_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_batch_03
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_08
      owning_system: core
    timestamp: '2026-10-09T12:38:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_lab_organizer_a_rescan
  artifact_page_id: page_lab_organizer_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_batch_03
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_lab_09
      owning_system: core
    timestamp: '2026-10-09T12:39:00-04:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
  supersedes_scan_reference_id: scanref_lab_organizer_a_initial
```


The clearer rescan creates a new Core source and a new Concord Scan Reference. The initial source and association remain available.

## 12. Artifact Reviews, Moderation, and Correction

### 12.1 Artifact Reviews

```yaml
artifact_reviews:
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_plan_a
  artifact_instance_id: art_lab_plan_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-06T13:00:00-04:00'
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
  notes: Planning Artifact is complete and relevant.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_plan_b
  artifact_instance_id: art_lab_plan_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-06T13:01:00-04:00'
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
  notes: Planning Artifact is complete and relevant.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_organizer_a_v1
  artifact_instance_id: art_lab_organizer_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-08T13:02:00-04:00'
  readability_judgment: partially_readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: group_and_teacher
  relevance_judgment: relevant
  moderation_requirement: not_required
  scoring_readiness: awaiting_rescan
  review_outcome: ready_with_qualification
  notes: One data column is difficult to read; a clearer rescan is requested.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_organizer_a_v2
  artifact_instance_id: art_lab_organizer_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-09T12:45:00-04:00'
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
  notes: The clearer rescan resolves the earlier readability concern.
  privacy_policy:
    classification: teacher_restricted
  supersedes_artifact_review_id: review_lab_organizer_a_v1
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_organizer_b
  artifact_instance_id: art_lab_organizer_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-08T13:04:00-04:00'
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
  notes: Evidence organizer is complete.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_troubleshoot_a
  artifact_instance_id: art_lab_troubleshoot_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-07T13:05:00-04:00'
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
  notes: Troubleshooting record clearly documents the invalid trial and revision.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_contribution_a
  artifact_instance_id: art_lab_contribution_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-08T13:06:00-04:00'
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
  notes: Participant claims about contribution require Moderation before consequential individual use.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_tracker
  artifact_instance_id: art_lab_teacher_tracker
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-08T13:07:00-04:00'
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
  notes: Teacher observation tracker is complete.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_lab_rubric
  artifact_instance_id: art_lab_scoring_rubric
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-10-09T12:50:00-04:00'
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
  notes: Paper scoring surface is correctly filed and readable.
  privacy_policy:
    classification: teacher_restricted
```


Review establishes readability, filing, attribution, privacy, relevance, Moderation requirement, and scoring readiness. It does not determine performance or create a Score.

### 12.2 Contribution Record Moderation

```yaml
record_owner: concord
record_kind: moderation_record
moderation_record_id: mod_lab_contribution_a
target_evidence_reference:
  evidence_kind: artifact_instance
  owning_system: concord
  record_id: art_lab_contribution_a
target_subject_references:
- subject_kind: core_student
  subject_id: stu_001
  owning_system: core
- subject_kind: core_student
  subject_id: stu_002
  owning_system: core
- subject_kind: core_student
  subject_id: stu_003
  owning_system: core
moderator:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
moderated_at: '2026-10-08T14:00:00-04:00'
status: accepted_with_qualification
qualification: May corroborate individual contribution judgments only when matched to teacher observation or another
  specific evidence source.
permitted_use: may_corroborate_teacher_evidence
rationale: The record contains specific signed claims, but self- and peer-description cannot independently determine
  individual performance.
privacy_policy:
  classification: teacher_restricted
```


The contribution record may corroborate individual judgment only under the recorded qualification. Acceptance does not select a Criterion, Score target, or value.

### 12.3 Scan-Replacement Correction

```yaml
record_owner: concord
record_kind: correction_record
correction_id: corr_lab_organizer_a_scan
target_reference:
  record_kind: scan_reference
  record_id: scanref_lab_organizer_a_initial
correction_type: scan_replacement
reason: The initial routed image obscured one measurement column; a clearer rescan was retained and linked.
correcting_actor:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
corrected_at: '2026-10-09T12:42:00-04:00'
replacement_reference:
  record_kind: scan_reference
  record_id: scanref_lab_organizer_a_rescan
related_source_reference:
  module_id: core
  record_kind: source_scan
  record_id: scan_core_lab_batch_03
note: The original retained source and Scan Reference remain available.
privacy_policy:
  classification: teacher_restricted
```


The Correction Record explains the old-to-new relationship without changing the retained source.

## 13. Criteria and Scoring Scale Records

### 13.1 Mixed Criterion Set Revision

```yaml
record_owner: concord
record_kind: criterion_set
criterion_set_id: critset_lab_mixed_rev_1
lineage_id: critset_lab_mixed
name: Catalase Laboratory Mixed Criteria
purpose: Define separate Group standards, individual standards, and local procedural judgments for the laboratory
  Activity.
revision: 1
scope: activity_specific
criterion_set_kind: mixed
standards_profile_id: profile_njsls_sci_2020_hs
criterion_ids:
- crit_lab_plan_conduct
- crit_lab_analyze_data
- crit_lab_safe_workflow
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-04T14:00:00-04:00'
  source_kind: manual
  note: Immutable mixed Criterion Set revision created.
```

### 13.2 Criteria

```yaml
criteria:
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_lab_plan_conduct
  criterion_set_id: critset_lab_mixed_rev_1
  key: plan_conduct
  label: Plans and conducts a controlled investigation
  definition: Develops and follows a coherent method with identified variables, controls, repeatable measurements,
    and documented revisions.
  criterion_kind: standard_backed
  standard_id: std_njsls_sci_sep_3_plan_conduct
  supported_target_kinds:
  - concord_group
  default_scoring_scale_id: scale_lab_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-04T14:05:00-04:00'
    source_kind: manual
    note: Standard-backed Group Criterion created.
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_lab_analyze_data
  criterion_set_id: critset_lab_mixed_rev_1
  key: analyze_data
  label: Analyzes and interprets investigation data
  definition: Uses valid measurements, identifies patterns and limitations, and explains how the evidence supports
    or constrains a scientific conclusion.
  criterion_kind: standard_backed
  standard_id: std_njsls_sci_sep_4_analyze_interpret
  supported_target_kinds:
  - core_student
  default_scoring_scale_id: scale_lab_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-04T14:06:00-04:00'
    source_kind: manual
    note: Standard-backed individual Criterion created.
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_lab_safe_workflow
  criterion_set_id: critset_lab_mixed_rev_1
  key: safe_workflow
  label: Maintains a safe and documented laboratory workflow
  definition: Uses materials safely, identifies invalid conditions, records procedural changes, and restores the
    workspace responsibly.
  criterion_kind: local
  alignment_standard_ids:
  - std_njsls_sci_sep_3_plan_conduct
  supported_target_kinds:
  - concord_group
  default_scoring_scale_id: scale_lab_process_3_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-04T14:07:00-04:00'
    source_kind: manual
    note: Local procedural Criterion created with non-governing standards alignment.
```


The two standard-backed Criteria each identify exactly one governing Focus Standard. The local workflow Criterion omits `standard_id`. Its `alignment_standard_ids` entry is non-governing and does not make the local Score a direct standards result.

### 13.3 Scoring Scale Revisions

```yaml
scoring_scales:
- record_owner: concord
  record_kind: scoring_scale
  scoring_scale_id: scale_lab_proficiency_4_rev_1
  lineage_id: scale_lab_proficiency_4
  name: Laboratory Four-Level Proficiency Scale
  revision: 1
  scale_type: ordinal
  intended_use: standards_based
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
    meaning: Evidence demonstrates sustained, precise, and independently reasoned performance.
    order: 4
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-04T14:15:00-04:00'
    source_kind: manual
    note: Immutable standards scale revision created.
- record_owner: concord
  record_kind: scoring_scale
  scoring_scale_id: scale_lab_process_3_rev_1
  lineage_id: scale_lab_process_3
  name: Laboratory Workflow Scale
  revision: 1
  scale_type: ordinal
  intended_use: local
  levels:
  - value: needs_intervention
    label: Needs Intervention
    meaning: The workflow required repeated teacher intervention or remained insufficiently documented.
    order: 1
  - value: consistent
    label: Consistent
    meaning: The Group maintained a safe and adequately documented workflow.
    order: 2
  - value: exemplary
    label: Exemplary
    meaning: The Group anticipated, documented, and resolved workflow concerns with exceptional independence.
    order: 3
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-04T14:16:00-04:00'
    source_kind: manual
    note: Immutable local workflow scale revision created.
```


The standards and local scales are separate immutable revisions. Their values are not assumed equivalent or aggregable.

## 14. External ScoreForm Reference and Source-Publication Lineage

```yaml
record_owner: concord
record_kind: external_reference
external_reference_id: extref_lab_scoreform_002
owning_system: scoreform
external_record_kind: result
external_record_id: sf_result_lab_002
contract_version: '1'
relationship_purpose: individual_accountability_check
activity_id: act_lab_catalase_01
session_id: ses_lab_03
group_id: grp_lab_a
criterion_id: crit_lab_analyze_data
subject_reference:
  subject_kind: core_student
  subject_id: stu_002
  owning_system: core
external_locator:
  scheme: institutional_record
  locator: sf_result_lab_002
  display_label: Student 002 catalase data-analysis check
display_label: Student 002 catalase data-analysis check
availability_status: available
last_confirmed_at: '2026-10-08T12:45:00-04:00'
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-08T12:46:00-04:00'
  source_kind: manual
  note: Concord External Reference created after the ScoreForm result became available.
```


ScoreForm remains authoritative for the selected-response result. Concord stores a relationship record and does not copy or mutate the ScoreForm result. The result does not automatically become a Concord Score.

The exact originating ScoreForm publication is known in this synthetic case:

```yaml
source_publication_reference:
  publication_id: pub_scoreform_lab_check_001
```

That Core Publication Reference identifies the immutable ScoreForm result-set revision through which `sf_result_lab_002` became discoverable. It does not transfer ScoreForm ownership to Core or Concord.

The same source publication reference appears on:

- the ScoreForm Evidence Reference used by `scoreev_lab_002_scoreform`;
- the manifest evidence-lineage projection;
- and the source record's module-qualified lineage.

This explicit relationship allows Meridian to recognize that the Concord Score used an already-published ScoreForm result as evidence rather than treating the two producer publications as automatically independent.

## 15. Score Records

```yaml
score_records:
- record_owner: concord
  record_kind: score_record
  score_record_id: score_lab_group_a_plan
  activity_id: act_lab_catalase_01
  session_id: ses_lab_03
  target_reference:
    target_kind: concord_group
    target_id: grp_lab_a
    owning_system: concord
  criterion_id: crit_lab_plan_conduct
  score_kind: standard_backed
  standard_id: std_njsls_sci_sep_3_plan_conduct
  scoring_scale_id: scale_lab_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-10-09T13:00:00-04:00'
  rationale: The Group planned a controlled investigation, explicitly invalidated the faulty trial, revised the
    method, and completed a valid repeat trial.
  moderation_complete: true
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:00:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_scoring_rubric
    note: Teacher recorded a deliberate Group standards judgment.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_lab_group_a_workflow
  activity_id: act_lab_catalase_01
  session_id: ses_lab_03
  target_reference:
    target_kind: concord_group
    target_id: grp_lab_a
    owning_system: concord
  criterion_id: crit_lab_safe_workflow
  score_kind: local
  scoring_scale_id: scale_lab_process_3_rev_1
  disposition: scored
  value: exemplary
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-10-09T13:05:00-04:00'
  rationale: The Group stopped an invalid trial, documented the cause, used a verified replacement, and restored
    the station safely.
  moderation_complete: true
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_lab_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:05:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_scoring_rubric
    note: Teacher recorded a local Group workflow judgment.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_lab_002_analyze
  activity_id: act_lab_catalase_01
  session_id: ses_lab_03
  target_reference:
    target_kind: core_student
    target_id: stu_002
    owning_system: core
  criterion_id: crit_lab_analyze_data
  score_kind: standard_backed
  standard_id: std_njsls_sci_sep_4_analyze_interpret
  scoring_scale_id: scale_lab_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: mixed_basis
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-10-09T13:10:00-04:00'
  rationale: Student 002 accurately distinguished invalid from valid measurements, explained the pattern, and connected
    the Group data to the individual accountability result.
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
    timestamp: '2026-10-09T13:10:00-04:00'
    source_kind: manual
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_scoring_rubric
    note: Teacher recorded an explicit individual standards judgment.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_lab_003_analyze_absent
  activity_id: act_lab_catalase_01
  session_id: ses_lab_02
  target_reference:
    target_kind: core_student
    target_id: stu_003
    owning_system: core
  criterion_id: crit_lab_analyze_data
  score_kind: standard_backed
  standard_id: std_njsls_sci_sep_4_analyze_interpret
  scoring_scale_id: scale_lab_proficiency_4_rev_1
  disposition: absent
  basis: professional_judgment
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-10-07T12:15:00-04:00'
  rationale: Student 003 was absent during the interrupted controlled-trial Session; no Session 2 judgment is made.
  status_reason:
    reason_code: session_absence
    note: The disposition applies only to Session 2 and is not a performance rating.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-10-07T12:15:00-04:00'
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_003
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T12:15:00-04:00'
    source_kind: manual
    note: Teacher recorded a contextual non-score disposition.
```


The local Group Score contains no governing `standard_id`. The Student 003 `absent` record omits `value`; it is not zero or the lowest level. Session absence is not absence from the entire Activity.

## 16. Score Evidence Links

```yaml
score_evidence_links:
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_plan_plan
  score_record_id: score_lab_group_a_plan
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_plan_a
  evidence_locator:
    page_number: 1
    note: Variables, controls, and proposed procedure.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: The planning sheet records the Group method and controls.
  significance: contextual
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:20:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_plan_org
  score_record_id: score_lab_group_a_plan
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_organizer_a
  evidence_locator:
    page_number: 1
    note: Valid and invalid trial table plus revised method.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: The organizer shows implementation, invalid-trial annotation, and the revised repeat trial.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:21:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_plan_tracker
  score_record_id: score_lab_group_a_plan
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Group A planning-and-conduct observations.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: Teacher observations document the Group decision to stop and revise the trial.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:22:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_plan_event
  score_record_id: score_lab_group_a_plan
  evidence_reference:
    evidence_kind: activity_event
    owning_system: concord
    record_id: event_lab_probe_failure_01
  evidence_locator:
    note: Equipment interruption and procedural revision.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: The event explains why the invalid trial was excluded and why a revised trial was required.
  significance: qualifying
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:23:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_workflow_trouble
  score_record_id: score_lab_group_a_workflow
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_troubleshoot_a
  evidence_locator:
    page_number: 1
    note: Diagnosis, replacement, and retest steps.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: The troubleshooting log documents safe interruption and procedural recovery.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:24:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_workflow_tracker
  score_record_id: score_lab_group_a_workflow
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Group A safety and cleanup observations.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: Teacher observations confirm safe materials handling and station reset.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:25:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_group_workflow_event
  score_record_id: score_lab_group_a_workflow
  evidence_reference:
    evidence_kind: activity_event
    owning_system: concord
    record_id: event_lab_probe_failure_01
  evidence_locator: {}
  subject_context:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  relevance_description: The event records the context in which the Group demonstrated the local workflow Criterion.
  significance: contextual
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:26:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_002_org
  score_record_id: score_lab_002_analyze
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_organizer_a
  evidence_locator:
    page_number: 1
    note: Entries initialed by Student 002 in the data and analysis rows.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  relevance_description: The Group organizer contains specifically located data-analysis work attributable to Student
    002.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:27:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_002_contribution
  score_record_id: score_lab_002_analyze
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_contribution_a
  evidence_locator:
    page_number: 1
    note: Student 002 signed analysis and invalid-trial explanation.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  relevance_description: The moderated contribution record corroborates Student 002’s data-analysis role.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:28:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
  moderation_record_id: mod_lab_contribution_a
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_002_tracker
  score_record_id: score_lab_002_analyze
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_lab_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Student 002 analysis observations across Sessions 2 and 3.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  relevance_description: Teacher observations support the explicit individual judgment.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:29:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_lab_002_scoreform
  score_record_id: score_lab_002_analyze
  evidence_reference:
    evidence_kind: external_record
    owning_system: concord
    record_id: extref_lab_scoreform_002
    source_publication_reference:
      publication_id: pub_scoreform_lab_check_001
  evidence_locator:
    note: Individual selected-response data-analysis result.
  subject_context:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  relevance_description: The ScoreForm result independently corroborates Student 002’s interpretation of the data.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-09T13:30:00-04:00'
    source_kind: manual
    note: Teacher deliberately linked evidence to the Score Record.
```


The Group evidence organizer supports both a Group Score and an individual Score through separate deliberate links. The individual use identifies Student 002 through Subject context, a specific locator, and teacher rationale. Group evidence does not generate the individual Score automatically.

## 17. Routing and Intake Edge Cases

This bounded addendum exercises three routing and intake states that do not change the principal laboratory scoring narrative:

1. a non-returned instructional page that has no PDS2 route;
2. an explicit duplicate scan retained separately from the preferred source;
3. and a misrouted source page corrected without changing the Core-retained source.

The calibration Artifact is generated conditionally after the equipment failure and therefore exists outside the original Packet Instance. Artifact Instances are permitted to exist outside a Packet Instance.

### 18.1 Calibration Template Definition and Version

```yaml
record_owner: concord
record_kind: template_definition
template_id: tmpl_lab_calibration_card
name: Equipment Calibration Verification and Instructions
artifact_category: local:calibration_verification
purpose: Record the Group's probe-verification result and distribute a non-returned instructional reference page.
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
  timestamp: '2026-10-01T15:30:00-04:00'
  source_kind: manual
  note: Reusable calibration template lineage created.
```

```yaml
record_owner: concord
record_kind: template_version
template_version_id: tmplv_lab_calibration_card_r1
template_id: tmpl_lab_calibration_card
version_label: Revision 1
revision_sequence: 1
rendering_specification_reference:
  record_kind: rendering_specification
  record_id: render_lab_calibration_card_r1
artifact_category: local:calibration_verification
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
  mode: declared_return_pages_only
  required_page_numbers:
  - 1
  non_returned_page_numbers:
  - 2
default_privacy_policy:
  classification: group_and_teacher
default_authorship_expectation:
  mode: local:recorder_for_group
default_subject_expectation:
  mode: local:represented_group
supported_criterion_ids:
- crit_lab_plan_conduct
- crit_lab_safe_workflow
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
  timestamp: '2026-10-02T15:30:00-04:00'
  source_kind: manual
  note: Immutable two-page calibration revision created.
status: active
```

Page 2 is part of the immutable page manifest, but it is not expected back and does not receive a QR, human fallback, or Route Registration.

### 18.2 Calibration Artifact and Pages

```yaml
record_owner: concord
record_kind: artifact_instance
artifact_instance_id: art_lab_calibration_a
template_version_id: tmplv_lab_calibration_card_r1
activity_id: act_lab_catalase_01
session_id: ses_lab_02
group_id: grp_lab_a
artifact_category: local:calibration_verification
generation_status: completed
expected_return_status: partial_return_expected
artifact_status: completed
privacy_policy:
  classification: group_and_teacher
page_ids:
- page_lab_calibration_a_01
- page_lab_calibration_a_02
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-07T11:35:00-04:00'
  source_kind: generated
  source_reference:
    record_kind: template_version
    record_id: tmplv_lab_calibration_card_r1
  note: Conditional calibration Artifact generated after the probe interruption.
```

```yaml
artifact_pages:
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_calibration_a_01
  artifact_instance_id: art_lab_calibration_a
  page_number: 1
  expected_page_count: 2
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_lab_calibration_a_01
  human_fallback: LAB-01-09
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T11:35:10-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_calibration_a
    note: Return page identity created before route registration and rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_lab_calibration_a_02
  artifact_instance_id: art_lab_calibration_a
  page_number: 2
  expected_page_count: 2
  page_kind: instructional
  return_expected: false
  route_required: false
  page_status: distributed_not_returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T11:35:11-04:00'
    source_kind: generated
    source_reference:
      record_kind: artifact_instance
      record_id: art_lab_calibration_a
    note: Instructional page intentionally omits route identity and return handling.
```

The instructional page omits `route_id` and `human_fallback`. No Core Route Registration exists for `page_lab_calibration_a_02`.

### 18.3 Core Route Registration for the Return Page Only

```yaml
record_owner: core
record_kind: route_registration
route_id: route_lab_calibration_a_01
locator:
  schema: PDS2
  module_id: concord
  class_id: cls_biology_p05
  work_id: act_lab_catalase_01
  route_id: route_lab_calibration_a_01
target:
  module_id: concord
  record_kind: artifact_page
  record_id: page_lab_calibration_a_01
status: active
registered_at: '2026-10-07T11:35:20-04:00'
```

Only page 1 receives the locator:

```text
PDS2|m=concord|c=cls_biology_p05|w=act_lab_catalase_01|r=route_lab_calibration_a_01
```

### 18.4 Calibration Author and Subjects

```yaml
record_owner: concord
record_kind: artifact_author
artifact_author_id: author_lab_calibration_a_recorder
artifact_instance_id: art_lab_calibration_a
author_reference:
  participant_kind: core_student
  participant_id: stu_002
  owning_system: core
authorship_mode: local:recorder_for_group
represented_group_id: grp_lab_a
role_assignment_id: role_lab_a_recorder
representation_status: local:recorder_summary
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
  timestamp: '2026-10-07T13:02:00-04:00'
  source_kind: manual
  note: Teacher confirmed the recorder association after corrected filing.
```

```yaml
artifact_subjects:
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_calibration_a_group
  artifact_instance_id: art_lab_calibration_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_lab_a
    owning_system: concord
  subject_role: local:represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T13:03:00-04:00'
    source_kind: manual
    note: Group Subject confirmed after corrected filing.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_lab_calibration_a_session
  artifact_instance_id: art_lab_calibration_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_lab_02
    owning_system: concord
  subject_role: local:session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-07T13:03:10-04:00'
    source_kind: manual
    note: Session Subject confirmed after corrected filing.
```

The recorder association does not imply sole Group authorship or successful calibration performance.

### 18.5 Additional Core-Retained Sources

```yaml
core_source_scans:
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_lab_duplicate_01
  source_filename: synthetic_lab_plan_a_duplicate.pdf
  retained_at: '2026-10-06T12:45:00-04:00'
  page_count: 1
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_lab_misroute_01
  source_filename: synthetic_lab_calibration_misroute.pdf
  retained_at: '2026-10-07T12:45:00-04:00'
  page_count: 1
```

Core preserves both sources. Concord classifies their semantic relationship through separate Scan References.

### 18.6 Explicit Duplicate Scan

```yaml
record_owner: concord
record_kind: scan_reference
scan_reference_id: scanref_lab_plan_a_duplicate
artifact_page_id: page_lab_plan_a_01
core_source_scan_reference:
  module_id: core
  record_kind: source_scan
  record_id: scan_core_lab_duplicate_01
source_page_index: 0
routing_status: routed
readability_status: readable
filing_status: confirmed
review_status: reviewed
preferred_for_use: false
status_reason:
  reason_code: duplicate_scan
  note: This retained source reproduces the same physical planning page already represented by the preferred Scan
    Reference.
  recorded_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  recorded_at: '2026-10-06T12:50:00-04:00'
  related_record:
    record_kind: scan_reference
    record_id: scanref_lab_plan_a
created_provenance:
  actor:
    actor_kind: system
    actor_id: core_dispatch_lab_10
    owning_system: core
  timestamp: '2026-10-06T12:46:00-04:00'
  source_kind: routed
  note: Core route dispatch created a separate Concord Scan Reference for the retained duplicate source.
```

`scanref_lab_plan_a` remains preferred. The duplicate source and Scan Reference remain available for audit and are not overwritten or silently deleted.

### 18.7 Initial Misroute and Corrected Scan Reference

The calibration return page is initially associated with the troubleshooting page because manual fallback recovery selects the wrong Artifact Page. Core does not alter the retained source after the mistake is discovered.

```yaml
record_owner: concord
record_kind: scan_reference
scan_reference_id: scanref_lab_calibration_misrouted
artifact_page_id: page_lab_troubleshoot_a_01
core_source_scan_reference:
  module_id: core
  record_kind: source_scan
  record_id: scan_core_lab_misroute_01
source_page_index: 0
routing_status: misrouted
readability_status: readable
filing_status: incorrect
review_status: correction_required
preferred_for_use: false
status_reason:
  reason_code: manual_recovery_misroute
  note: Manual fallback recovery associated the calibration page with the troubleshooting Artifact Page.
  recorded_by:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  recorded_at: '2026-10-07T12:55:00-04:00'
  related_record:
    record_kind: artifact_page
    record_id: page_lab_calibration_a_01
created_provenance:
  actor:
    actor_kind: system
    actor_id: core_dispatch_lab_11
    owning_system: core
  timestamp: '2026-10-07T12:46:00-04:00'
  source_kind: routed
  note: Initial manual fallback dispatch created the incorrect association.
```

```yaml
record_owner: concord
record_kind: scan_reference
scan_reference_id: scanref_lab_calibration_corrected
artifact_page_id: page_lab_calibration_a_01
core_source_scan_reference:
  module_id: core
  record_kind: source_scan
  record_id: scan_core_lab_misroute_01
source_page_index: 0
routing_status: manually_resolved
readability_status: readable
filing_status: confirmed
review_status: reviewed
preferred_for_use: true
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-07T13:00:00-04:00'
  source_kind: manual
  source_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_lab_misroute_01
  note: Teacher created the corrected semantic filing association without changing the retained source.
supersedes_scan_reference_id: scanref_lab_calibration_misrouted
```

The same Core source and source-page index appear in both Scan References. The history records the erroneous and corrected semantic associations.

### 18.8 Filing Correction

```yaml
record_owner: concord
record_kind: correction_record
correction_id: corr_lab_calibration_misroute
target_reference:
  record_kind: scan_reference
  record_id: scanref_lab_calibration_misrouted
correction_type: filing_correction
reason: The retained calibration page was associated with the troubleshooting Artifact Page during manual fallback
  recovery.
correcting_actor:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
corrected_at: '2026-10-07T13:00:00-04:00'
replacement_reference:
  record_kind: scan_reference
  record_id: scanref_lab_calibration_corrected
related_source_reference:
  module_id: core
  record_kind: source_scan
  record_id: scan_core_lab_misroute_01
note: The original Core-retained source, incorrect Scan Reference, route history, and corrected association remain
  available.
privacy_policy:
  classification: teacher_restricted
```

The Correction Record does not rewrite the Core source or delete the initial Scan Reference.

### 18.9 Calibration Artifact Review

```yaml
record_owner: concord
record_kind: artifact_review
artifact_review_id: review_lab_calibration_a
artifact_instance_id: art_lab_calibration_a
reviewer:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
reviewed_at: '2026-10-07T13:05:00-04:00'
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
notes: The return page is readable and correctly filed. The instructional page was not expected back and correctly
  has no route or Scan Reference.
privacy_policy:
  classification: teacher_restricted
```

Review confirms the corrected filing and expected page behavior. It does not create a Score.

### 18.10 Edge-Case Validation

| Edge state | Result | Evidence |
|---|---|---|
| Non-returned instructional page omits route identity | Pass | `page_lab_calibration_a_02` has `return_expected: false`, `route_required: false`, and no route fields |
| Non-returned instructional page has no Core Route Registration | Pass | Only `route_lab_calibration_a_01` is registered |
| Duplicate source remains retained separately | Pass | `scan_core_lab_duplicate_01` and `scanref_lab_plan_a_duplicate` |
| Exactly one planning-page Scan Reference is preferred | Pass | `scanref_lab_plan_a` is preferred; the duplicate is not |
| Misrouted source remains unchanged | Pass | Both associations reference `scan_core_lab_misroute_01`, page index 0 |
| Incorrect Scan Reference remains historical | Pass | `scanref_lab_calibration_misrouted` is preserved |
| Corrected Scan Reference identifies the proper Artifact Page | Pass | `scanref_lab_calibration_corrected` targets `page_lab_calibration_a_01` |
| Filing correction is explicit | Pass | `corr_lab_calibration_misroute` |
| Review occurs after correction | Pass | Corrected association at 13:00; Review at 13:05 |

The duplicate, rescan, and filing-correction records change intake and evidence administration without changing the published Score, Criterion, Scoring Scale, Moderation, or source-record lineage represented in the academic-result manifest. They therefore do not require a second manifest revision in this case.

A future correction that changed consequential evidence use, target identity, Score meaning, or published lineage would require a new manifest revision and a new Core Publication Record rather than mutation of the publication represented below.

## 18. Core Academic Work Registration

The laboratory Activity is explicitly registered through Core. Activity existence, `scoring_orientation: mixed`, Focus Standard selection, local Score creation, or standard-backed Score creation would not register it automatically.

```yaml
academic_work_registrations:
- record_owner: core
  record_kind: academic_work_registration
  schema_version: '1'
  record_type: academic_work_registration
  work:
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
  registration_revision: 1
  producer_contract_version: '1'
  title: Catalase Reaction Rate Investigation
  work_kind: collaborative_activity
  academic_intent: summative
  lifecycle: active
  created_at: '2026-10-05T14:21:00-04:00'
  updated_at: '2026-10-05T14:21:00-04:00'
  source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_lab_catalase_01
    contract_version: '1'
- record_owner: core
  record_kind: academic_work_registration
  schema_version: '1'
  record_type: academic_work_registration
  work:
    module_id: concord
    class_id: cls_biology_p05
    work_id: act_lab_catalase_01
  registration_revision: 2
  producer_contract_version: '1'
  title: Catalase Reaction Rate Investigation
  work_kind: collaborative_activity
  academic_intent: summative
  lifecycle: closed
  created_at: '2026-10-05T14:21:00-04:00'
  updated_at: '2026-10-09T14:35:00-04:00'
  source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_lab_catalase_01
    contract_version: '1'
```

The two registration revisions preserve a Core-owned lifecycle change from `active` to `closed`. Both retain `academic_intent: summative`.

That intent is not inferred from Concord's `mixed` scoring orientation. It does not state which Score Records Meridian must select, whether the local workflow Score contributes to a Grade, or which Academic Period receives the work.

Registration revision is independent of:

- native Score revision;
- manifest revision;
- Publication Record schema version;
- Publication Record supersession;
- publication withdrawal;
- Meridian import revision;
- and Meridian calculation or report revision.

## 19. Concord Academic Result Manifest Revision 1

Manifest revision 1 captures the complete publishable laboratory result state after the Activity closes. It includes:

- two scored standard-backed judgments;
- one scored local workflow judgment;
- one explicit standard-backed `absent` disposition;
- all three exact Criterion projections;
- both exact Scoring Scale revisions;
- all eleven deliberate evidence-lineage rows;
- the applicable qualified Moderation projection;
- exact ScoreForm source-record and source-publication lineage;
- and a three-row Standards Result Projection that excludes the local Score.

The exact immutable bytes are the following UTF-8 JSON, including one trailing line-feed byte after the final closing brace:

```json
{
  "activity_context": {
    "activity_id": "act_lab_catalase_01",
    "activity_status_snapshot": "completed",
    "activity_type": "local:science_laboratory",
    "class_id": "cls_biology_p05",
    "focus_standard_ids": [
      "std_njsls_sci_sep_3_plan_conduct",
      "std_njsls_sci_sep_4_analyze_interpret"
    ],
    "scoring_orientation": "mixed",
    "session_references": [
      {
        "record_id": "ses_lab_01",
        "record_kind": "session"
      },
      {
        "record_id": "ses_lab_02",
        "record_kind": "session"
      },
      {
        "record_id": "ses_lab_03",
        "record_kind": "session"
      }
    ],
    "standards_profile_id": "profile_njsls_sci_2020_hs",
    "title_snapshot": "Catalase Reaction Rate Investigation"
  },
  "criterion_projections": [
    {
      "criterion_id": "crit_lab_analyze_data",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_lab_mixed_rev_1",
      "definition": "Uses valid measurements, identifies patterns and limitations, and explains how the evidence supports or constrains a scientific conclusion.",
      "key": "analyze_data",
      "label": "Analyzes and interprets investigation data",
      "standard_id": "std_njsls_sci_sep_4_analyze_interpret",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student"
      ]
    },
    {
      "criterion_id": "crit_lab_plan_conduct",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_lab_mixed_rev_1",
      "definition": "Develops and follows a coherent method with identified variables, controls, repeatable measurements, and documented revisions.",
      "key": "plan_conduct",
      "label": "Plans and conducts a controlled investigation",
      "standard_id": "std_njsls_sci_sep_3_plan_conduct",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "concord_group"
      ]
    },
    {
      "alignment_standard_ids": [
        "std_njsls_sci_sep_3_plan_conduct"
      ],
      "criterion_id": "crit_lab_safe_workflow",
      "criterion_kind": "local",
      "criterion_set_id": "critset_lab_mixed_rev_1",
      "definition": "Uses materials safely, identifies invalid conditions, records procedural changes, and restores the workspace responsibly.",
      "key": "safe_workflow",
      "label": "Maintains a safe and documented laboratory workflow",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "concord_group"
      ]
    }
  ],
  "generated_at": "2026-10-09T14:45:00-04:00",
  "generated_provenance": {
    "actor": {
      "actor_id": "publisher_concord_001",
      "actor_kind": "system",
      "display_label_snapshot": "Concord academic-result publisher",
      "owning_system": "concord"
    },
    "application_version": "synthetic-concord-0.1",
    "note": "Generated from validated canonical Concord records after the mixed-scoring Activity closed.",
    "source_kind": "system",
    "timestamp": "2026-10-09T14:45:00-04:00"
  },
  "manifest_contract_version": "concord_academic_result_manifest_v1",
  "moderation_projections": [
    {
      "moderated_at": "2026-10-08T14:00:00-04:00",
      "moderation_record_id": "mod_lab_contribution_a",
      "permitted_use": "may_corroborate_teacher_evidence",
      "privacy_classification": "teacher_restricted",
      "qualification": "May corroborate individual contribution judgments only when matched to teacher observation or another specific evidence source.",
      "status": "accepted_with_qualification",
      "target_evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_contribution_a"
      },
      "target_subject_references": [
        {
          "owning_system": "core",
          "subject_id": "stu_001",
          "subject_kind": "core_student"
        },
        {
          "owning_system": "core",
          "subject_id": "stu_002",
          "subject_kind": "core_student"
        },
        {
          "owning_system": "core",
          "subject_id": "stu_003",
          "subject_kind": "core_student"
        }
      ]
    }
  ],
  "privacy_classification": "teacher_restricted",
  "producer_module_id": "concord",
  "record_set_id": "rs_lab_results_01",
  "record_set_revision": 1,
  "score_evidence_link_projections": [
    {
      "evidence_locator": {
        "note": "Student 002 signed analysis and invalid-trial explanation.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_contribution_a"
      },
      "moderation_record_id": "mod_lab_contribution_a",
      "relevance_description": "The moderated contribution record corroborates Student 002’s data-analysis role.",
      "score_evidence_link_id": "scoreev_lab_002_contribution",
      "score_record_id": "score_lab_002_analyze",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_lab_contribution_a",
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
        "note": "Entries initialed by Student 002 in the data and analysis rows.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_organizer_a"
      },
      "relevance_description": "The Group organizer contains specifically located data-analysis work attributable to Student 002.",
      "score_evidence_link_id": "scoreev_lab_002_org",
      "score_record_id": "score_lab_002_analyze",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_lab_organizer_a",
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
        "note": "Individual selected-response data-analysis result."
      },
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_lab_scoreform_002",
        "source_publication_reference": {
          "publication_id": "pub_scoreform_lab_check_001"
        }
      },
      "relevance_description": "The ScoreForm result independently corroborates Student 002’s interpretation of the data.",
      "score_evidence_link_id": "scoreev_lab_002_scoreform",
      "score_record_id": "score_lab_002_analyze",
      "significance": "corroborating",
      "source_publication_reference": {
        "publication_id": "pub_scoreform_lab_check_001"
      },
      "source_record_reference": {
        "contract_version": "1",
        "module_id": "scoreform",
        "record_id": "sf_result_lab_002",
        "record_kind": "result"
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
        "note": "Student 002 analysis observations across Sessions 2 and 3.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_teacher_tracker"
      },
      "relevance_description": "Teacher observations support the explicit individual judgment.",
      "score_evidence_link_id": "scoreev_lab_002_tracker",
      "score_record_id": "score_lab_002_analyze",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_lab_teacher_tracker",
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
        "note": "Equipment interruption and procedural revision."
      },
      "evidence_reference": {
        "evidence_kind": "activity_event",
        "owning_system": "concord",
        "record_id": "event_lab_probe_failure_01"
      },
      "relevance_description": "The event explains why the invalid trial was excluded and why a revised trial was required.",
      "score_evidence_link_id": "scoreev_lab_group_plan_event",
      "score_record_id": "score_lab_group_a_plan",
      "significance": "qualifying",
      "source_record_reference": {
        "record_id": "event_lab_probe_failure_01",
        "record_kind": "activity_event"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Valid and invalid trial table plus revised method.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_organizer_a"
      },
      "relevance_description": "The organizer shows implementation, invalid-trial annotation, and the revised repeat trial.",
      "score_evidence_link_id": "scoreev_lab_group_plan_org",
      "score_record_id": "score_lab_group_a_plan",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_lab_organizer_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Variables, controls, and proposed procedure.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_plan_a"
      },
      "relevance_description": "The planning sheet records the Group method and controls.",
      "score_evidence_link_id": "scoreev_lab_group_plan_plan",
      "score_record_id": "score_lab_group_a_plan",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_lab_plan_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Group A planning-and-conduct observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_teacher_tracker"
      },
      "relevance_description": "Teacher observations document the Group decision to stop and revise the trial.",
      "score_evidence_link_id": "scoreev_lab_group_plan_tracker",
      "score_record_id": "score_lab_group_a_plan",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_lab_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "activity_event",
        "owning_system": "concord",
        "record_id": "event_lab_probe_failure_01"
      },
      "relevance_description": "The event records the context in which the Group demonstrated the local workflow Criterion.",
      "score_evidence_link_id": "scoreev_lab_group_workflow_event",
      "score_record_id": "score_lab_group_a_workflow",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "event_lab_probe_failure_01",
        "record_kind": "activity_event"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Group A safety and cleanup observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_teacher_tracker"
      },
      "relevance_description": "Teacher observations confirm safe materials handling and station reset.",
      "score_evidence_link_id": "scoreev_lab_group_workflow_tracker",
      "score_record_id": "score_lab_group_a_workflow",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_lab_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Diagnosis, replacement, and retest steps.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_lab_troubleshoot_a"
      },
      "relevance_description": "The troubleshooting log documents safe interruption and procedural recovery.",
      "score_evidence_link_id": "scoreev_lab_group_workflow_trouble",
      "score_record_id": "score_lab_group_a_workflow",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_lab_troubleshoot_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_lab_a",
        "subject_kind": "concord_group"
      }
    }
  ],
  "score_projections": [
    {
      "activity_id": "act_lab_catalase_01",
      "basis": "mixed_basis",
      "criterion_id": "crit_lab_analyze_data",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_lab_002_analyze",
      "scored_at": "2026-10-09T13:10:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "session_id": "ses_lab_03",
      "standard_id": "std_njsls_sci_sep_4_analyze_interpret",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_lab_catalase_01",
      "basis": "professional_judgment",
      "criterion_id": "crit_lab_analyze_data",
      "current_status": "current",
      "disposition": "absent",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_lab_003_analyze_absent",
      "scored_at": "2026-10-07T12:15:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "session_id": "ses_lab_02",
      "standard_id": "std_njsls_sci_sep_4_analyze_interpret",
      "status_reason": {
        "note": "The disposition applies only to Session 2 and is not a performance rating.",
        "reason_code": "session_absence"
      },
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_003",
        "target_kind": "core_student"
      }
    },
    {
      "activity_id": "act_lab_catalase_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_lab_plan_conduct",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "standard_backed",
      "score_record_id": "score_lab_group_a_plan",
      "scored_at": "2026-10-09T13:00:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "session_id": "ses_lab_03",
      "standard_id": "std_njsls_sci_sep_3_plan_conduct",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_lab_a",
        "target_kind": "concord_group"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_lab_catalase_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_lab_safe_workflow",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "local",
      "score_record_id": "score_lab_group_a_workflow",
      "scored_at": "2026-10-09T13:05:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_process_3_rev_1",
      "session_id": "ses_lab_03",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_lab_a",
        "target_kind": "concord_group"
      },
      "value": "exemplary"
    }
  ],
  "scoring_scale_projections": [
    {
      "aggregation_guidance": "Treat each Score as contextual evidence; Meridian applies any scale mapping, Grade-item, or aggregation policy.",
      "intended_use": "local",
      "levels": [
        {
          "label": "Needs Intervention",
          "meaning": "The workflow required repeated teacher intervention or remained insufficiently documented.",
          "ordering": 1,
          "value": "needs_intervention"
        },
        {
          "label": "Consistent",
          "meaning": "The Group maintained a safe and adequately documented workflow.",
          "ordering": 2,
          "value": "consistent"
        },
        {
          "label": "Exemplary",
          "meaning": "The Group anticipated, documented, and resolved workflow concerns with exceptional independence.",
          "ordering": 3,
          "value": "exemplary"
        }
      ],
      "lineage_id": "scale_lab_process_3",
      "name": "Laboratory Workflow Scale",
      "revision": 1,
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_lab_process_3_rev_1",
      "status_snapshot": "active"
    },
    {
      "aggregation_guidance": "Treat each Score as contextual evidence; Meridian applies any scale mapping, Grade-item, or aggregation policy.",
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
          "meaning": "Evidence demonstrates sustained, precise, and independently reasoned performance.",
          "ordering": 4,
          "value": "exceeding"
        }
      ],
      "lineage_id": "scale_lab_proficiency_4",
      "name": "Laboratory Four-Level Proficiency Scale",
      "revision": 1,
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "status_snapshot": "active"
    }
  ],
  "source_activity": {
    "contract_version": "1",
    "module_id": "concord",
    "record_id": "act_lab_catalase_01",
    "record_kind": "activity"
  },
  "standards_result_projection": [
    {
      "activity_id": "act_lab_catalase_01",
      "class_id": "cls_biology_p05",
      "criterion_id": "crit_lab_analyze_data",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_lab_002_contribution",
        "scoreev_lab_002_org",
        "scoreev_lab_002_scoreform",
        "scoreev_lab_002_tracker"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_lab_002_analyze",
      "scored_at": "2026-10-09T13:10:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "session_id": "ses_lab_03",
      "standard_id": "std_njsls_sci_sep_4_analyze_interpret",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_002",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_lab_catalase_01",
      "class_id": "cls_biology_p05",
      "criterion_id": "crit_lab_analyze_data",
      "current_status": "current",
      "disposition": "absent",
      "evidence_link_ids": [],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_lab_003_analyze_absent",
      "scored_at": "2026-10-07T12:15:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "session_id": "ses_lab_02",
      "standard_id": "std_njsls_sci_sep_4_analyze_interpret",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_003",
        "target_kind": "core_student"
      }
    },
    {
      "activity_id": "act_lab_catalase_01",
      "class_id": "cls_biology_p05",
      "criterion_id": "crit_lab_plan_conduct",
      "current_status": "current",
      "disposition": "scored",
      "evidence_link_ids": [
        "scoreev_lab_group_plan_event",
        "scoreev_lab_group_plan_org",
        "scoreev_lab_group_plan_plan",
        "scoreev_lab_group_plan_tracker"
      ],
      "moderation_complete": true,
      "module_id": "concord",
      "score_record_id": "score_lab_group_a_plan",
      "scored_at": "2026-10-09T13:00:00-04:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_lab_proficiency_4_rev_1",
      "session_id": "ses_lab_03",
      "standard_id": "std_njsls_sci_sep_3_plan_conduct",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_lab_a",
        "target_kind": "concord_group"
      },
      "value": "meeting"
    }
  ],
  "work": {
    "class_id": "cls_biology_p05",
    "module_id": "concord",
    "work_id": "act_lab_catalase_01"
  }
}
```

The canonical workspace-relative path is:

```text
classes/cls_biology_p05/modules/concord/work/act_lab_catalase_01/
  exports/manifests/rs_lab_results_01/1.json
```

The path is revision-addressed, contained within the exact Concord Activity work root, and outside Core-owned registry storage.

The SHA-256 digest of the exact JSON bytes shown above is:

```text
21240bacba9fea4faf3adc9c63b1f49b3b209f59e70ad85ec2c2422322d11b57
```

The broader `score_projections` collection includes both standard-backed and local Score Records. The nested `standards_result_projection` contains only standard-backed results and dispositions.

The local workflow Score remains semantically local even though its Criterion carries non-governing standards alignment. The manifest does not create a direct standards rating for that alignment.

The ScoreForm lineage row preserves three distinct relationships:

```text
ScoreForm-owned result
    -> exact Core source Publication Record
    -> Concord External Reference and teacher-approved Score
```

The manifest exposes the relationship without copying the ScoreForm result or determining how Meridian should handle overlap.

## 20. Core Publication Record

After Concord durably writes and validates the exact manifest bytes, calculates their digest, and submits a compatible publication request, Core creates the immutable Publication Record.

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_concord_lab_results_001
work:
  module_id: concord
  class_id: cls_biology_p05
  work_id: act_lab_catalase_01
source_record:
  module_id: concord
  record_kind: activity
  record_id: act_lab_catalase_01
  contract_version: '1'
publication_kind: academic_result_set
capabilities:
- criterion_scores
- standards_ratings
- moderated_scores
record_set_id: rs_lab_results_01
record_set_revision: 1
manifest_contract_version: concord_academic_result_manifest_v1
manifest_path: classes/cls_biology_p05/modules/concord/work/act_lab_catalase_01/exports/manifests/rs_lab_results_01/1.json
manifest_digest_algorithm: sha256
manifest_digest: 21240bacba9fea4faf3adc9c63b1f49b3b209f59e70ad85ec2c2422322d11b57
published_at: '2026-10-09T14:50:00-04:00'
academic_work_registration_revision: 2
```

Core announces the exact immutable manifest revision. It does not copy the Score, Criterion, Scoring Scale, evidence-lineage, or Moderation arrays into the Publication Record.

The capabilities are truthful for this manifest:

- `criterion_scores` because both standard-backed and local criterion-level Scores are exposed;
- `standards_ratings` because direct standards Scores and the `absent` disposition are exposed;
- `moderated_scores` because the individual Score includes consequential evidence governed by a qualified Moderation Record.

Capabilities are discovery metadata. They do not establish authorization, completeness for every student, Grade eligibility, Academic Period membership, or a universal grading interpretation.

Repeating the identical publication request with the same work, record-set identity, revision, path, contract version, and digest must reconcile to `pub_concord_lab_results_001`.

Reusing `record_set_revision: 1` with different bytes, path, digest, or contract version is an integrity conflict rather than an update.

The derived Core catalog may be updated or rebuilt after canonical publication. Catalog failure does not mutate the manifest or Publication Record and must not be reported as if the canonical publication failed after Core successfully created this record.

This laboratory case contains no successor Publication Record and no withdrawal. Those lifecycle behaviors are exercised by the project case.

## 21. Meridian Consumption Boundary

Meridian may discover and import both:

- `pub_concord_lab_results_001`; and
- the originating ScoreForm publication `pub_scoreform_lab_check_001`.

The Concord manifest explicitly records that the ScoreForm result supported `score_lab_002_analyze`. Meridian therefore has enough lineage to avoid assuming that the two producer results are independent evidence merely because they arrived through separate Core publications.

A Meridian import must preserve:

- Core Publication Record ID and publication-schema version;
- exact `ModuleWorkRef`;
- exact source Activity `ModuleRecordRef`;
- publication kind and declared capabilities;
- manifest path;
- manifest digest algorithm and exact digest;
- manifest contract version;
- record-set identity and revision;
- exact Academic Work Registration revision;
- predecessor Publication Record ID when present;
- withdrawal state observed at import;
- withdrawal-state observation time;
- import time;
- and the supported Meridian import-contract or adapter version.

For interpretation of this laboratory result, Meridian must additionally preserve:

- standard-backed versus local Score classification;
- Group versus individual target identity;
- exact Scoring Scale identity and meaning;
- ScoreForm source-record and source-publication lineage;
- native Score dispositions;
- and applicable Moderation state.

Meridian then owns explicit policy for:

- whether the Concord publication is eligible for grading;
- whether the ScoreForm result is independently eligible;
- whether related evidence should be selected, de-duplicated, or retained only as provenance;
- whether the Group standards Score can contribute to any Grade item;
- whether the local workflow Score contributes under conventional or hybrid grading;
- how the exact Scoring Scale revisions are interpreted;
- whether the `absent` disposition remains excluded, deferred, or otherwise handled;
- Grade-item membership;
- Academic Period membership;
- standards proficiency;
- Grade calculation;
- override behavior;
- calculation snapshots;
- and report snapshots.

Concord does not assign an Academic Period in the Activity, Score, manifest, or Publication Record. Native dates provide context but do not universally determine period membership.

This example does not invent Meridian records that lack a governing contract. The boundary analysis demonstrates what Meridian can consume and what it must decide.

A Meridian override would alter only a Meridian-derived result. It would not mutate:

- the Concord Score Record;
- the Concord manifest;
- the Core Publication Record;
- the ScoreForm source publication;
- or the underlying evidence lineage.

A changed Concord judgment would require a new native Score and a new manifest and publication sequence. A changed Meridian policy or override does not.

## 22. Relationship Summary

```text
Core Class
    -> mixed Concord Activity
        -> Sessions
            -> interrupted Session and equipment-failure Event
        -> Activity-specific Groups
            -> Memberships
            -> contextual Roles
            -> Responsibilities
                -> preserved reassignment history
        -> immutable Packet Version
            -> Packet Instance
                -> principal Artifact Instances
        -> immutable calibration Template Version
            -> standalone conditional calibration Artifact Instance
        -> generated Artifact Instances
            -> Artifact Pages
                -> returned pages with Core Route Registrations
                -> non-returned instructional page with no route
                -> Concord Scan References
                    -> preferred source
                    -> retained duplicate
                    -> preserved misroute and corrected filing
            -> Artifact Authors
            -> Artifact Subjects
            -> Reviews
            -> Moderation where required
        -> mixed Criterion Set
            -> Group standard-backed Criterion
            -> individual standard-backed Criterion
            -> local workflow Criterion
        -> native Score Records
            -> Group standards Score
            -> local Group Score
            -> individual standards Score
            -> contextual non-score disposition
            -> deliberate Score Evidence Links
                -> Concord Group evidence
                -> teacher observation
                -> moderated contribution evidence
                -> Activity Event
                -> ScoreForm result with source-publication lineage

Concord Activity
    -> explicit Core Academic Work Registration revisions
    -> immutable Concord Academic Result Manifest revision 1
        -> complete Score projections
        -> exact Criterion and Scoring Scale projections
        -> evidence-lineage and Moderation projections
        -> standards-only subset
    -> immutable Core Publication Record
    -> Meridian import
        -> policy-controlled eligibility, overlap, Academic Period, Grade, override, and reporting decisions
```

## 23. Lifecycle Walkthrough

### 23.1 Configuration and Registration

```text
Activity and Sessions configured
    -> Groups and Memberships created
    -> Roles and Responsibilities assigned
    -> standards profile and ordered Focus Standards selected
    -> mixed Criterion Set and two exact scales selected
    -> teacher explicitly requests Core Academic Work Registration
    -> Core creates registration revision 1 with lifecycle active
```

Activity creation, `mixed` orientation, standards selection, and registration remain separate actions.

### 23.2 Generation and Routing

```text
Packet Version selected
    -> Packet Instance generated
    -> principal Artifact Instances and Pages created
    -> conditional calibration Artifact generated outside the Packet Instance
    -> return-page Route Registrations created
    -> non-returned instructional page deliberately receives no route
    -> PDS2 codes rendered only for route-required pages
```

### 23.3 Classroom Use and Exception

```text
Session 1 planning occurs
    -> Session 2 begins
    -> Student 003 absence recorded contextually
    -> probe Responsibility reassigned
    -> unstable readings detected
    -> trial stopped and marked invalid
    -> troubleshooting Event and Artifact recorded
    -> Session 2 marked interrupted
    -> Session 3 repeat trial completed
```

### 23.4 Scan, Review, and Moderation

```text
mixed pages scanned
    -> Core retains complete source
    -> Core dispatches Concord and ScoreForm pages separately
    -> Concord creates Scan References for Concord pages
    -> duplicate planning-page source retained and classified separately
    -> calibration page initially misrouted during manual fallback recovery
    -> corrected Scan Reference and filing Correction Record preserve history
    -> teacher Reviews Artifacts
    -> clearer organizer rescan retained
    -> contribution record Moderated with qualification
```

### 23.5 Native Scoring

```text
teacher deliberately selects targets and Criteria
    -> Group standard-backed Score recorded
    -> local Group workflow Score recorded
    -> individual standard-backed Score recorded
    -> Session-specific absent disposition recorded
    -> eleven Score Evidence Links created after their parent Scores
```

### 23.6 Manifest and Publication

```text
Activity marked completed
    -> Core Academic Work Registration revision 2 closes the work
    -> Concord determines the complete publishable projection
    -> record_set_revision 1 assigned
    -> exact manifest JSON generated and validated
    -> revision-addressed immutable file written
    -> SHA-256 digest calculated from final bytes
    -> Core validates registration, path, contract, and digest
    -> Core creates pub_concord_lab_results_001
    -> derived catalog may update or later be repaired
```

A native Score remains valid if publication fails. A manifest file without a Publication Record remains unpublished.

### 23.7 Meridian Consumption

```text
Core publications discovered
    -> Meridian imports Concord and ScoreForm publication state
    -> source-publication lineage exposes overlap
    -> Meridian applies explicit evidence-selection and Grade-item policy
    -> Meridian assigns Academic Period membership under a Core calendar revision
    -> Meridian calculates or reports under versioned policy
```

Concord and Core do not perform those Meridian-owned operations.

## 24. Invariant Validation

| Invariant | Result | Evidence in this example |
|---|---|---|
| Activity declares exactly one scoring orientation | Pass | `mixed` |
| Concord scoring orientation is distinct from Core academic intent | Pass | `mixed` versus `summative` |
| Mixed Activity has one Core standards profile and ordered Focus Standards | Pass | Activity record |
| Academic Work Registration is explicit | Pass | Two Core-owned revisions |
| Activity existence does not imply registration | Pass | Registration is represented as a separate teacher-requested action |
| Every Activity has at least one Session | Pass | Three Sessions |
| Interrupted Session is not a performance judgment | Pass | Session 2 and equipment Event |
| Groups are Activity-specific | Pass | Group records reference one Activity |
| Membership does not prove contribution or performance | Pass | Separate Membership, evidence, and Score records |
| Role and Responsibility changes preserve history | Pass | Session-specific Roles and superseding probe Responsibility |
| Assigned Responsibility is not performance | Pass | No Score derives automatically from assignment |
| Template Definitions and immutable Versions remain separate | Pass | Seven lineages and seven exact Versions |
| Packet Definition, Version, and Instance remain separate | Pass | Complete packet chain |
| Artifact Pages exist before routes | Pass | Page and registration chronology |
| Non-returned instructional page omits route identity | Pass | `page_lab_calibration_a_02` has no route fields or registration |
| PDS2 encodes route identity only | Pass | No semantic scoring context in QR |
| Mixed source scan may route to several modules | Pass | Concord and ScoreForm pages coexist |
| Core source scan remains canonical | Pass | Concord stores references only |
| Rescan preserves earlier source and association | Pass | Two organizer Scan References and Correction Record |
| Duplicate scan remains separately retained and nonpreferred | Pass | Original and duplicate planning-page sources coexist |
| Misroute correction preserves source and filing history | Pass | Initial and corrected same-source associations remain |
| Artifact Author and Subject are separate | Pass | Contract-native association records |
| Recorder is not sole Group Author | Pass | Group and recorder associations coexist |
| Teacher tracker remains one multi-Subject Artifact | Pass | One tracker with several Subjects |
| Review does not create a Score | Pass | Reviews contain readiness judgments only |
| Required Moderation precedes consequential use | Pass | Qualified Moderation predates the individual Score and evidence link |
| Moderation does not select a Score value | Pass | It governs evidence use only |
| Equipment failure is not a low Score | Pass | Context is separate from teacher judgments |
| Standard-backed Criterion has exactly one standard | Pass | Two separate direct Criteria |
| Local Criterion has no governing standard | Pass | `crit_lab_safe_workflow` omits `standard_id` |
| Non-governing alignment is not a standards result | Pass | Local Score is absent from the standards-only subset |
| Group standards Score uses a Group-valid Criterion | Pass | Explicit `concord_group` target |
| Group Score does not create member Scores | Pass | No automatic member records |
| Group evidence may support an individual Score only through explicit judgment | Pass | Student 002 locators, context, rationale, and links |
| ScoreForm evidence remains externally owned | Pass | Concord External Reference plus module-qualified source lineage |
| ScoreForm result does not automatically become a Concord Score | Pass | Separate teacher-approved Score |
| Non-score disposition omits value | Pass | Student 003 `absent` projection |
| Every Score has its exact Criterion and Scoring Scale projection | Pass | Complete manifest projections |
| Both standard-backed and local Scores appear in the broader manifest | Pass | Four `score_projections` rows |
| Only standard-backed records appear in the Standards Result Projection | Pass | Three standards rows; local workflow Score excluded |
| Exact ScoreForm source publication is preserved | Pass | `pub_scoreform_lab_check_001` |
| Manifest path is revision-addressed and inside the Activity work root | Pass | `exports/manifests/rs_lab_results_01/1.json` |
| Manifest digest is calculated from exact immutable bytes | Pass | SHA-256 `c5e11918…3a57` |
| Core Publication Record does not copy results | Pass | It references work, path, contract, revision, and digest |
| Publication capabilities are truthful | Pass | Criterion, standards, and Moderation projections are present |
| Identical publication replay is idempotent | Pass | Reconciles to one Publication Record |
| Contradictory reuse of revision 1 is rejected | Pass | Different bytes, path, digest, or contract are an integrity conflict |
| Derived Core catalog is nonauthoritative | Pass | Catalog repair cannot create or rewrite canonical records |
| Publication does not imply Grade eligibility | Pass | Meridian policy remains separate |
| Native dates do not assign authoritative Academic Period membership | Pass | No period field appears in native or publication records |
| Cross-producer overlap is visible to Meridian | Pass | ScoreForm publication lineage is explicit |
| Meridian override does not mutate Concord or Core records | Pass | Ownership boundary is explicit |
| No mastery, Grade, or report is calculated by Concord | Pass | Meridian owns downstream policy |

## 25. Represented Cleanly

The current contracts represent the following laboratory requirements without ambiguity:

- a mixed Activity;
- explicit Core Academic Work Registration;
- several Sessions including an interrupted occurrence;
- Activity-specific Groups and Memberships;
- contextual Roles;
- a specific Responsibility and preserved reassignment;
- Group planning, evidence, troubleshooting, contribution, observation, and scoring Artifacts;
- conditional packet generation;
- mixed-module scan intake;
- rescanning and correction without source mutation;
- a non-returned instructional page with no route or Scan Reference;
- duplicate-scan classification with one preferred source;
- misroute correction that preserves the retained source and original association;
- participant-authored contribution evidence requiring Moderation;
- an equipment-failure Event;
- Group and individual standards targets;
- a local Group target;
- a local Criterion with non-governing standards alignment;
- individual scoring supported by Group evidence through explicit teacher judgment;
- externally owned ScoreForm evidence;
- exact ScoreForm source-publication lineage;
- a Session-specific `absent` disposition;
- one complete mixed-score Concord Academic Result Manifest;
- a standards-only subset that excludes the local Score;
- one exact digest-bound Core Publication Record;
- and a bounded Meridian-consumption handoff.

## 26. Optional Structures Used

### Responsibility Assignment

Responsibilities are used because the case distinguishes specific obligations from broad laboratory Roles. The probe-calibration reassignment preserves the original assignment and demonstrates that assignment does not prove completion or quality.

### Activity Event

The equipment failure is represented as an Event because chronology and explanation matter. Routine measurements do not become Events.

### External Reference

The ScoreForm result is linked without transferring ownership or creating a runtime dependency.

### Correction Record

Correction Records document both a scan replacement and a filing correction while preserving earlier sources and Scan References.

### Standalone conditional Artifact

The calibration Artifact exists outside the principal Packet Instance because it was generated only after the equipment failure. The foundation permits an Artifact Instance without a Packet Instance.

## 27. Contracts Deliberately Not Used

### Activity Marker

The three Sessions provide sufficient instructional structure. The laboratory does not require durable phases or milestones beyond those occurrences.

### Work Item and Work-Item Dependency

The Activity contains assigned Responsibilities but no independently tracked tasks whose dependency relationships require durable Work Item identity.

### Child Group

Different laboratory Roles do not create meaningful subteams.

### Attachment

All evidence represented here is either a generated Concord Artifact or an external ScoreForm record. No irregular poster, photograph, or externally generated worksheet requires an Attachment.

### Contribution Claim Record

The signed contribution Artifact contains participant statements, but the case does not require a separate durable Contribution Claim envelope for each statement. The Artifact is Reviewed and Moderated as evidence. The project case exercises explicit Contribution Claims.

### Quillan Reference

Written-response integration is exercised by the seminar case. This laboratory uses ScoreForm for individual accountability.

### Native Score supersession

No laboratory Score is revised in this case. Scan and filing corrections do not fabricate a Score supersession.

### Publication supersession and withdrawal

The laboratory publishes one valid manifest revision. The project case exercises successor publication and withdrawal behavior.

### Meridian records

The example preserves the Meridian consumption boundary but does not invent Grade-item, calculation, override, or report schemas that are not yet governed here.

## 28. Tensions or Ambiguities

### 28.1 Responsibility reassignment versus correction

The probe Responsibility changes because classroom circumstances changed; the original record was not erroneous. The example therefore uses same-type supersession and a `reassigned` status without a generic Correction Record.

### 28.2 Group evidence locator granularity

The individual Score uses a page-level locator plus a human-readable note identifying Student 002's entries. Later serialization may define richer structured row or region locators, but pixel coordinates and OCR are not required by the foundation.

### 28.3 ScoreForm public record shape

The exact released ScoreForm result and publication contracts remain future integration work. The conceptual Module Record Reference, External Reference, Core Publication Reference, and evidence-lineage projection are sufficient to preserve ownership and relationship semantics.

### 28.4 Duplicate, rescan, and misroute semantics

A duplicate scan, a clearer rescan, and a corrected misroute are different historical states. The example does not collapse them into one generic replacement workflow.

### 28.5 Registration and runtime availability

The Academic Work Registration and Publication Records model the reviewed Core architecture, not a claim that the released `pds-core` 0.5 package already exposes those runtime APIs.

No blocking conceptual ambiguity is identified.

## 29. Workarounds Rejected

- Treating the interrupted Session as a failed performance result.
- Scoring the invalid probe readings as poor science.
- Rewriting Student 003's original Responsibility after absence.
- Treating Student 002's temporary Responsibility as proof of successful contribution.
- Treating Group Membership as proof that every member performed equally.
- Copying the Group standards Score to all members.
- Converting the Group organizer directly into Student 002's Score.
- Using the ScoreForm result as an automatic Concord Score.
- Treating the ScoreForm and Concord publications as automatically independent evidence.
- Giving the local workflow Criterion a governing standard.
- Excluding the local Score from the broader manifest merely because it is not standards-backed.
- Including the local workflow Score in the Standards Result Projection.
- Converting Student 003's absence into zero or `developing`.
- Creating a Concord Scan Reference for the ScoreForm-owned page.
- Replacing the Core-retained source with the clearer routed image.
- Creating a dummy route or QR for a non-returned instructional page.
- Deleting or overwriting a duplicate scan instead of retaining and classifying it.
- Editing the Core-retained source after discovering a misroute.
- Rewriting the initial incorrect Scan Reference instead of preserving a corrected association.
- Encoding Group, student, Criterion, standard, or Score context in PDS2.
- Inferring Academic Work Registration from Activity existence or scoring orientation.
- Publishing mutable `latest.json` bytes as the canonical manifest target.
- Copying manifest result arrays into the Core Publication Record.
- Treating publication as automatic Grade or Academic Period membership.
- Treating the derived Core catalog as canonical authority.
- Rewriting Concord records to represent a Meridian-only override.

## 30. Contract Changes Required

```text
None.
```

The case exposes implementation questions about structured evidence locators, released ScoreForm publication adapters, and future Core and Meridian APIs, but it requires no conceptual-contract or ADR change.

## 31. Laboratory Case Acceptance Assessment

- [x] A mixed Activity is represented.
- [x] One Core standards profile and ordered Focus Standards are represented.
- [x] Explicit Core Academic Work Registration is represented.
- [x] Concord scoring orientation and Core academic intent remain distinct.
- [x] A Group standard-backed Criterion and Score are represented.
- [x] An individual standard-backed Criterion and Score are represented.
- [x] A local procedural Criterion and Score are represented.
- [x] The local Criterion has no governing standard.
- [x] The local Criterion demonstrates non-governing standards alignment.
- [x] Several Sessions are represented, including an interruption.
- [x] Groups, Memberships, Roles, and Responsibilities are represented.
- [x] Responsibility reassignment preserves the earlier record.
- [x] Assigned Responsibility does not prove completion or performance.
- [x] Prediction, planning, procedure, evidence, troubleshooting, contribution, observation, and scoring Artifacts are represented.
- [x] A contribution record is Moderated before consequential use.
- [x] An equipment failure and invalid trial are represented without becoming a low Score.
- [x] A mixed Core source scan routes pages to Concord and ScoreForm.
- [x] Core retains the canonical complete source.
- [x] A rescan creates a new source and Scan Reference.
- [x] A non-returned instructional page omits route identity, human fallback, and Route Registration.
- [x] An explicit duplicate scan remains separately retained and nonpreferred.
- [x] A misrouted source page is corrected without changing the Core-retained source.
- [x] Review, Moderation, Scoring, registration, publication, Grading, and Reporting remain separate.
- [x] Group evidence supports an individual Score only through explicit teacher judgment.
- [x] A ScoreForm result remains externally owned supporting evidence.
- [x] The exact ScoreForm source publication is preserved.
- [x] The ScoreForm result does not automatically become a Concord Score.
- [x] A contextual `absent` disposition is represented without a value.
- [x] One immutable Concord Academic Result Manifest revision is represented.
- [x] Both standard-backed and local Scores appear in the broader manifest.
- [x] The local Score is excluded from the Standards Result Projection.
- [x] Group and individual targets remain distinct in the standards subset.
- [x] Exact Criterion and Scoring Scale semantics are projected.
- [x] All eleven evidence uses are projected with source-record lineage.
- [x] Required Moderation state and qualification are projected.
- [x] The manifest is stored at a revision-addressed path inside the exact Activity work root.
- [x] The exact manifest bytes produce SHA-256 `21240bacba9fea4faf3adc9c63b1f49b3b209f59e70ad85ec2c2422322d11b57`.
- [x] One immutable Core Publication Record binds the path, contract, revision, and digest.
- [x] Publication capabilities are truthful.
- [x] Identical replay is idempotent and contradictory revision reuse is rejected.
- [x] The Core catalog remains a nonauthoritative derived index.
- [x] Publication does not imply Grade eligibility or Academic Period membership.
- [x] Meridian owns overlap, selection, scale mapping, Grades, overrides, and reports.
- [x] No architecture-breaking workaround is required.
