# Representative Contract Example: Collaborative Programming and Engineering Project

**Status:** Revised draft for representative-contract validation  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Issue:** `#12 — 11. Create representative contract examples`  
**Example family:** Collaborative programming / engineering project  
**Primary scoring orientation:** `mixed`  
**Publication model:** Two main-Activity manifest revisions plus one local-only addendum publication  
**Revision date:** July 30, 2026  
**Revision:** 3 — aligned with ADR 0015, Core registry publication, and Meridian

## 1. Case Purpose

This example tests whether the Concord conceptual contracts can represent a long-running collaborative programming and engineering project involving:

- five instructional Sessions and ordered project stages;
- parent Groups and bounded child Groups;
- contextual Membership reassignment that preserves earlier history;
- changing Roles and Responsibilities;
- Work Items and explicit Dependencies;
- blocked work caused by an external-system outage;
- architecture, interruption, testing, intervention, and release Events;
- Group-authored plans, logs, and design reviews;
- individual contribution reflections;
- teacher-authored multi-Subject evidence;
- Attachments and external repository, commit, pull-request, CI, CAD, and cloud-document references;
- conflicting Contribution Claims and human Moderation;
- individual and Group Score targets;
- standard-backed and local Criteria in one mixed Activity;
- Group evidence supporting individual judgment only through explicit teacher use;
- a deferred individual standards judgment followed by a superseding Score;
- explicit Core Academic Work Registration;
- two immutable Concord Academic Result Manifest revisions for the primary Activity;
- Core publication supersession distinct from native Score supersession;
- publication of both standard-backed and local Scores while preserving their different meanings;
- exact external evidence lineage without treating repository ownership as contribution;
- an evidence-only addendum that deliberately creates no registration or result publication;
- a local-criteria-only addendum with its own registration, manifest, and Core Publication Record;
- and a bounded Meridian-consumption analysis.

The case uses shared Concord foundation records. It does not introduce repository, pull-request, build, sprint, branch, CAD, or software-team entities as universal foundational contracts.

The project case deliberately carries the most extensive publication lifecycle in the representative set. It demonstrates a native Score revision, a new immutable manifest revision, a superseding Core Publication Record, and a separately published local-only result set.

## 2. Activity Narrative

An AP Computer Science Principles class completes a five-session project titled **Accessible Community Resource Finder**. Two parent Groups design, build, test, and present an application that helps users locate community resources. Each Group also prepares a small physical display concept.

Group A uses two child Groups during early development:

- an interface subteam;
- and a data-and-test subteam.

Student 003 begins in Group A as a test engineer. Before Session 4, the teacher reassigns Student 003 to Group B to balance an expanded accessibility-testing workload. The earlier Membership, Role, Responsibility, Work Item, Artifact, and contribution history remains attached to Group A. Later records use Group B context.

During Session 3, Group A’s source-control remote is temporarily unavailable. Local work remains intact, but the integration Work Item is blocked. The interruption is recorded as context and does not imply poor performance. A replacement Work Item preserves the blocked history and records completion after service returns.

During testing, Group B discovers a keyboard-focus regression. Students reproduce, correct, and retest the defect. Student 005 initially claims sole authorship of the Group B test suite, while Student 004 attributes the entire test suite to Student 005. External history and teacher observation show a more nuanced result: Student 005 designed the test matrix and implemented most automated tests; Student 004 supplied acceptance cases; and Student 003 completed accessibility regression checks after reassignment. The teacher Moderates the claims, preserves the disputed original, and records a corrected bounded claim.

The teacher records:

1. separate Group standards Scores for iterative development;
2. an individual standards Score for Student 001’s testing and debugging;
3. an initially deferred, later superseded individual standards judgment for Student 005;
4. a local Group handoff Score for Group A; and
5. a local individual handoff Score for Student 004.

Repository ownership, file ownership, account identity, Work Item completion, Role Assignment, and Responsibility Assignment do not independently establish Artifact authorship, contribution, or performance.


After the first complete set of teacher judgments is available, the teacher explicitly closes the Core Academic Work Registration. Concord generates manifest revision 1. That revision includes Student 005's `deferred` standards judgment as the current native state.

Additional reviewed and moderated evidence then supports a new Score Record for Student 005. Concord does not rewrite the first Score or the first manifest. It generates manifest revision 2, and Core records a second Publication Record that supersedes the first publication while preserving both.

The evidence-only exhibition archive remains unregistered and unpublished because evidence collection alone does not create an academic-result publication. The local-criteria-only retrospective is explicitly registered and published as a criterion-score result set whose capabilities do not claim standards ratings.

## 3. Governing Assumptions

The primary and addendum Activities use the settled PDS2 architecture:

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

Every returned scannable page has an Artifact Page and Core Route Registration before rendering. A normal route target is:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

External systems retain ownership of repository, commit, pull-request, CI, CAD, and cloud-document records. Concord stores typed External References and deliberate Score Evidence Links rather than copying those records.

Routing, Academic Work Registration, result publication, and Meridian consumption are separate integration domains.

The primary publication flow is:

```text
Concord Activity and native records
    -> explicit Core Academic Work Registration
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> Meridian import and policy-controlled selection
```

Concord owns the Activity, native records, and exact manifest bytes. Core owns Academic Work Registration revisions, Publication Records, withdrawal records, and the rebuildable registry catalog. Meridian owns publication eligibility, Grade-item membership, Academic Period membership, evidence selection, scale interpretation, proficiency and Grade calculation, overrides, and reports.

The Activity's `scoring_orientation: mixed` is Concord-owned. Core's `academic_intent: summative` is a separate registration field and is not inferred from the scoring orientation.

Activity existence, standards configuration, Score existence, or route registration does not create a Core Academic Work Registration automatically.

Publication does not imply Grade eligibility, Academic Period membership, or inclusion in any Meridian calculation.

A native Score revision, manifest revision, Core publication supersession, Core publication withdrawal, Meridian import revision, Meridian override, and report snapshot are separate histories.

The registry architecture used in this conceptual example exists on the newer Core architecture described by the governing documents. It must not be misrepresented as part of the released `pds-core` 0.5 runtime baseline.

## 4. Record Inventory

### 4.1 Primary case: Core-owned and external context

| Record family | Count represented |
| --- | ---: |
| Core Class | 1 |
| Core Students | 6 |
| Authorized teacher Actor | 1 |
| Core Standards Profile | 1 |
| Core Standards | 2 |
| Core Route Registrations | 10 |
| Core Source Scans | 4 |
| Core Academic Work Registration revisions | 2 |
| Core Publication Records for the primary Activity | 2 |

### 4.2 Primary case: Concord-owned records and projections

| Record family | Count represented |
| --- | ---: |
| Activity | 1 |
| Sessions | 5 |
| Groups | 4 |
| Group Memberships | 10 |
| Role Assignments | 10 |
| Responsibility Assignments | 8 |
| Activity Markers | 5 |
| Work Items | 12 |
| Work-Item Dependencies | 9 |
| Activity Events | 5 |
| Contribution Claims | 4 |
| Template Definitions | 6 |
| Template Versions | 6 |
| Packet Definition | 1 |
| Packet Version | 1 |
| Packet Components | 6 |
| Packet Instance | 1 |
| Artifact Instances | 10 |
| Artifact Pages | 10 |
| Artifact Author associations | 16 |
| Artifact Subject associations | 45 |
| Scan References | 11 |
| Artifact Reviews | 11 |
| Moderation Records | 4 |
| Correction Records | 3 |
| Attachments | 3 |
| External References | 7 |
| Criterion Set revisions | 1 |
| Criteria | 3 |
| Scoring Scale revisions | 2 |
| Score Records | 7 |
| Score Evidence Links | 22 |
| Concord Academic Result Manifest revisions | 2 |
| Standards Result Projection rows in revision 1 | 4 |
| Standards Result Projection rows in revision 2 | 5 |

### 4.3 Bounded orientation addenda

| Record family | Count represented |
| --- | ---: |
| Evidence-only Activities | 1 |
| Local-criteria-only Activities | 1 |
| Sessions | 2 |
| Groups | 2 |
| Memberships | 10 |
| Template Definitions | 2 |
| Template Versions | 2 |
| Artifact Instances | 2 |
| Artifact Pages | 2 |
| Route Registrations | 2 |
| Core Source Scans | 2 |
| Scan References | 2 |
| Artifact Reviews | 2 |
| Artifact Author associations | 3 |
| Artifact Subject associations | 3 |
| Local Criterion Set revisions | 1 |
| Local Criteria | 1 |
| Local Score Records | 1 |
| Score Evidence Links | 1 |
| Core Academic Work Registration revisions | 1 |
| Concord Academic Result Manifest revisions | 1 |
| Core Publication Records | 1 |
| Standards Result Projection rows | 0 |

The evidence-only addendum intentionally has no Academic Work Registration, manifest, or Publication Record. The local-criteria-only addendum has one explicit registration and one publication whose only capability is `criterion_scores`.

No Meridian-owned record is invented. Meridian behavior is analyzed at the ownership boundary only.

## 5. Shared Core References

### 5.1 Core Class
```yaml
owning_system: core
record_kind: class
record_id: cls_apcsp_p01
display_label: AP Computer Science Principles — Period 1
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
  record_id: profile_njsls_cs_2023_hs
  display_label: NJSLS Computer Science 2023 — High School
focus_standards:
- owning_system: core
  record_kind: standard
  record_id: std_njsls_cs_8_1_12_ap_4
  display_label: Design and iteratively develop computational artifacts for a practical or societal purpose
- owning_system: core
  record_kind: standard
  record_id: std_njsls_cs_8_1_12_ap_6
  display_label: Create and refine computational artifacts through procedures, testing, and debugging
```

Display labels are illustrative. Durable identity resides in each Core `record_id`.

## 6. Primary Activity and Collaboration Records

### 6.1 Activity
```yaml
record_owner: concord
record_kind: activity
activity_id: act_proj_resource_finder_01
class_reference:
  module_id: core
  record_kind: class
  record_id: cls_apcsp_p01
title: Accessible Community Resource Finder
activity_type: local:collaborative_software_engineering_project
description: A five-session collaborative project in which two Groups design, implement, test, and present
  an accessible resource-finder application with a small physical display prototype.
scoring_orientation: mixed
standards_profile_id: profile_njsls_cs_2023_hs
focus_standard_ids:
- std_njsls_cs_8_1_12_ap_4
- std_njsls_cs_8_1_12_ap_6
criterion_set_ids:
- critset_proj_mixed_rev_1
status: completed
privacy_policy:
  classification: classroom_shared
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-30T14:20:00-04:00'
  source_kind: manual
  note: Teacher configured the project Activity.
updated_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-11-09T15:20:00-05:00'
  source_kind: manual
  note: Activity marked completed after scoring and final Review.
external_reference_ids:
- extref_proj_repo_a_v1
- extref_proj_repo_a_v2
- extref_proj_commit_001
- extref_proj_pr_005
- extref_proj_ci_b
- extref_proj_cad_b
- extref_proj_design_doc
```

The Activity is `mixed`: direct standards judgments use the two selected Focus Standards, while collaboration-and-handoff judgments use a local Criterion.

### 6.2 Sessions
```yaml
sessions:
- record_owner: concord
  record_kind: session
  session_id: ses_proj_01
  activity_id: act_proj_resource_finder_01
  sequence: 1
  label: Requirements and Architecture
  scheduled_start: '2026-11-02T08:05:00-05:00'
  scheduled_end: '2026-11-02T08:50:00-05:00'
  actual_start: '2026-11-02T08:05:00-05:00'
  actual_end: '2026-11-02T08:50:00-05:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:26:00-04:00'
    source_kind: manual
    note: Session configured.
- record_owner: concord
  record_kind: session
  session_id: ses_proj_02
  activity_id: act_proj_resource_finder_01
  sequence: 2
  label: Prototype Build
  scheduled_start: '2026-11-03T08:05:00-05:00'
  scheduled_end: '2026-11-03T08:50:00-05:00'
  actual_start: '2026-11-03T08:05:00-05:00'
  actual_end: '2026-11-03T08:50:00-05:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:27:00-04:00'
    source_kind: manual
    note: Session configured.
- record_owner: concord
  record_kind: session
  session_id: ses_proj_03
  activity_id: act_proj_resource_finder_01
  sequence: 3
  label: Integration Checkpoint
  scheduled_start: '2026-11-04T08:05:00-05:00'
  scheduled_end: '2026-11-04T08:42:00-05:00'
  actual_start: '2026-11-04T08:05:00-05:00'
  actual_end: '2026-11-04T08:42:00-05:00'
  status: interrupted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:28:00-04:00'
    source_kind: manual
    note: Session configured.
  status_reason:
    reason_code: external_tool_unavailable
    note: The Group A source-control remote was temporarily unavailable, so integration stopped early
      and continued from local copies.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-11-04T08:34:00-05:00'
    related_record:
      record_kind: activity_event
      record_id: event_proj_repo_interruption_01
- record_owner: concord
  record_kind: session
  session_id: ses_proj_04
  activity_id: act_proj_resource_finder_01
  sequence: 4
  label: Testing and Accessibility
  scheduled_start: '2026-11-05T08:05:00-05:00'
  scheduled_end: '2026-11-05T08:50:00-05:00'
  actual_start: '2026-11-05T08:05:00-05:00'
  actual_end: '2026-11-05T08:50:00-05:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:29:00-04:00'
    source_kind: manual
    note: Session configured.
- record_owner: concord
  record_kind: session
  session_id: ses_proj_05
  activity_id: act_proj_resource_finder_01
  sequence: 5
  label: Release and Demonstration
  scheduled_start: '2026-11-06T08:05:00-05:00'
  scheduled_end: '2026-11-06T08:50:00-05:00'
  actual_start: '2026-11-06T08:05:00-05:00'
  actual_end: '2026-11-06T08:50:00-05:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:30:00-04:00'
    source_kind: manual
    note: Session configured.
```

Session 3 is `interrupted` because the source-control remote is unavailable. That status describes the occurrence and does not set a Score disposition.

### 6.3 Parent and Child Groups
```yaml
groups:
- record_owner: concord
  record_kind: group
  group_id: grp_proj_a
  activity_id: act_proj_resource_finder_01
  label: Project Group A
  description: Primary software Group demonstrating child teams, blocked integration, and Membership reassignment.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:35:00-04:00'
    source_kind: manual
    note: Activity-specific Group created.
- record_owner: concord
  record_kind: group
  group_id: grp_proj_b
  activity_id: act_proj_resource_finder_01
  label: Project Group B
  description: Comparison Group receiving a reassigned participant during the testing phase.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:36:00-04:00'
    source_kind: manual
    note: Activity-specific Group created.
- record_owner: concord
  record_kind: group
  group_id: grp_proj_a_ui
  activity_id: act_proj_resource_finder_01
  label: Group A — Interface Subteam
  description: Child Group responsible for interface and keyboard-navigation work during early development.
  parent_group_id: grp_proj_a
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:37:00-04:00'
    source_kind: manual
    note: Child Group created for bounded collaborative identity.
- record_owner: concord
  record_kind: group
  group_id: grp_proj_a_data
  activity_id: act_proj_resource_finder_01
  label: Group A — Data and Test Subteam
  description: Child Group responsible for data validation and early test-harness work.
  parent_group_id: grp_proj_a
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
  status: inactive
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:38:00-04:00'
    source_kind: manual
    note: Child Group created for bounded collaborative identity.
```

Child Groups are used only where bounded subteam identity matters. Different Responsibilities alone would not justify a child Group.

### 6.4 Group Memberships
```yaml
group_memberships:
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_a_001
  group_id: grp_proj_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:40:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_a_002
  group_id: grp_proj_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:41:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_a_003_v1
  group_id: grp_proj_a
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
  status: reassigned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:42:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
  status_reason:
    reason_code: scope_rebalancing
    note: Student 003 moved to Group B beginning in Session 4 after the testing scope expanded.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-11-05T08:00:00-05:00'
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_b_004
  group_id: grp_proj_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:43:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_b_005
  group_id: grp_proj_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:44:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_b_006
  group_id: grp_proj_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:45:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_b_003_v2
  group_id: grp_proj_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
    - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-05T08:00:00-05:00'
    source_kind: manual
    note: Contextual Group Membership created.
  supersedes_membership_id: mem_proj_a_003_v1
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_a_ui_001
  group_id: grp_proj_a_ui
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:46:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_a_ui_002
  group_id: grp_proj_a_ui
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:47:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_a_data_003
  group_id: grp_proj_a_data
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T14:48:00-04:00'
    source_kind: manual
    note: Contextual Group Membership created.
```

Student 003’s earlier Group A Membership remains available. The later Group B Membership supersedes the earlier relationship only for the later effective context.

### 6.5 Role Assignments
```yaml
role_assignments:
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_001_ui_v1
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  membership_id: mem_proj_a_001
  group_id: grp_proj_a
  role_key: local:interface_lead
  role_label_snapshot: Interface Lead
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
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
    timestamp: '2026-10-30T15:00:00-04:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_002_data_v1
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  membership_id: mem_proj_a_002
  group_id: grp_proj_a
  role_key: local:data_validation_lead
  role_label_snapshot: Data Validation Lead
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
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
    timestamp: '2026-10-30T15:01:00-04:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_003_test_v1
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  membership_id: mem_proj_a_003_v1
  group_id: grp_proj_a
  role_key: local:test_engineer
  role_label_snapshot: Test Engineer
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
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
    timestamp: '2026-10-30T15:02:00-04:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_004_product
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  membership_id: mem_proj_b_004
  group_id: grp_proj_b
  role_key: local:product_owner
  role_label_snapshot: Product Owner
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
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
    timestamp: '2026-10-30T15:03:00-04:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_005_test_v1
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  membership_id: mem_proj_b_005
  group_id: grp_proj_b
  role_key: local:test_lead
  role_label_snapshot: Test Lead
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
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
    timestamp: '2026-10-30T15:04:00-04:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_006_docs
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  membership_id: mem_proj_b_006
  group_id: grp_proj_b
  role_key: local:documentation_lead
  role_label_snapshot: Documentation Lead
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_01
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
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
    timestamp: '2026-10-30T15:05:00-04:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_001_access_v2
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  membership_id: mem_proj_a_001
  group_id: grp_proj_a
  role_key: local:accessibility_lead
  role_label_snapshot: Accessibility Lead
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
    - ses_proj_05
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
    timestamp: '2026-11-05T08:01:00-05:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_002_integrate_v2
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  membership_id: mem_proj_a_002
  group_id: grp_proj_a
  role_key: local:integration_coordinator
  role_label_snapshot: Integration Coordinator
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
    - ses_proj_05
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
    timestamp: '2026-11-05T08:02:00-05:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_003_test_v2
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  membership_id: mem_proj_b_003_v2
  group_id: grp_proj_b
  role_key: local:test_engineer
  role_label_snapshot: Test Engineer
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
    - ses_proj_05
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
    timestamp: '2026-11-05T08:03:00-05:00'
    source_kind: manual
    note: Contextual project Role assigned.
- record_owner: concord
  record_kind: role_assignment
  role_assignment_id: role_proj_005_integrate_v2
  activity_id: act_proj_resource_finder_01
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  membership_id: mem_proj_b_005
  group_id: grp_proj_b
  role_key: local:integration_coordinator
  role_label_snapshot: Integration Coordinator
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
    - ses_proj_05
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
    timestamp: '2026-11-05T08:04:00-05:00'
    source_kind: manual
    note: Contextual project Role assigned.
```

Role changes preserve earlier assignments. A Role identifies contextual function; it does not prove fulfillment, authorship, contribution, or performance.

### 6.6 Responsibility Assignments
```yaml
responsibility_assignments:
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_a_keyboard
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  description: Implement keyboard navigation and visible focus states.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_02
    - ses_proj_04
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_ui
  expected_output: Reviewed keyboard-navigation implementation.
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
    timestamp: '2026-10-30T15:15:00-04:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_a_data
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  description: Implement input validation and normalize resource records.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_02
    - ses_proj_03
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_data
  expected_output: Validated data-processing module.
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
    timestamp: '2026-10-30T15:16:00-04:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_a_tests_v1
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  description: Build the first automated test harness for Group A.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_02
    - ses_proj_03
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_tests
  expected_output: Initial test-harness branch.
  status: reassigned
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
    timestamp: '2026-10-30T15:17:00-04:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
  status_reason:
    reason_code: membership_reassignment
    note: Student 003 moved to Group B before the final testing Session; remaining Group A test responsibility
      transferred to Student 002.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-11-05T08:05:00-05:00'
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_a_tests_v2
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  description: Complete and run the Group A automated test harness.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_tests
  expected_output: Completed automated test report.
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
    timestamp: '2026-11-05T08:05:00-05:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
  supersedes_responsibility_assignment_id: resp_proj_a_tests_v1
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_b_tests
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  description: Develop and document the Group B integration test suite.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_02
    - ses_proj_03
    - ses_proj_04
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_tests
  expected_output: Reviewed pull request and test report.
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
    timestamp: '2026-10-30T15:18:00-04:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_b_access
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  description: Conduct the final accessibility audit after joining Group B.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_access
  expected_output: Accessibility audit checklist.
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
    timestamp: '2026-11-05T08:06:00-05:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_b_release_notes
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  description: Prepare traceable release notes and evidence links.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_04
    - ses_proj_05
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_release
  expected_output: Final release notes.
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
    timestamp: '2026-10-30T15:19:00-04:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
- record_owner: concord
  record_kind: responsibility_assignment
  responsibility_assignment_id: resp_proj_b_integration
  activity_id: act_proj_resource_finder_01
  assignee_reference:
    record_kind: group
    record_id: grp_proj_b
  description: Integrate code, CAD export, and release documentation into one demonstrable build.
  effective_context:
    activity_id: act_proj_resource_finder_01
    session_ids:
    - ses_proj_03
    - ses_proj_04
    - ses_proj_05
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_integration
  expected_output: Demonstrable integrated prototype.
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
    timestamp: '2026-10-30T15:20:00-04:00'
    source_kind: manual
    note: Specific project Responsibility assigned.
```

The reassigned testing Responsibility preserves the original obligation and its context. Responsibility status does not itself establish completion quality or a Score.

## 7. Optional Project-Structure Records

### 7.1 Activity Markers
```yaml
activity_markers:
- record_owner: concord
  record_kind: activity_marker
  activity_marker_id: marker_proj_planning
  activity_id: act_proj_resource_finder_01
  marker_type: phase
  label: Planning and Architecture
  sequence: 1
  session_ids:
  - ses_proj_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:30:00-04:00'
    source_kind: manual
    note: Optional project Marker created.
- record_owner: concord
  record_kind: activity_marker
  activity_marker_id: marker_proj_prototype
  activity_id: act_proj_resource_finder_01
  marker_type: iteration
  label: Prototype Iteration
  sequence: 2
  session_ids:
  - ses_proj_02
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:31:00-04:00'
    source_kind: manual
    note: Optional project Marker created.
- record_owner: concord
  record_kind: activity_marker
  activity_marker_id: marker_proj_integration
  activity_id: act_proj_resource_finder_01
  marker_type: checkpoint
  label: Integration Checkpoint
  sequence: 3
  session_ids:
  - ses_proj_03
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:32:00-04:00'
    source_kind: manual
    note: Optional project Marker created.
- record_owner: concord
  record_kind: activity_marker
  activity_marker_id: marker_proj_testing
  activity_id: act_proj_resource_finder_01
  marker_type: phase
  label: Testing and Accessibility
  sequence: 4
  session_ids:
  - ses_proj_04
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:33:00-04:00'
    source_kind: manual
    note: Optional project Marker created.
- record_owner: concord
  record_kind: activity_marker
  activity_marker_id: marker_proj_release
  activity_id: act_proj_resource_finder_01
  marker_type: milestone
  label: Release Demonstration
  sequence: 5
  session_ids:
  - ses_proj_05
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:34:00-04:00'
    source_kind: manual
    note: Optional project Marker created.
```

Markers express project stages without replacing Sessions. A stage may span one or several Sessions, and one Session may interact with more than one project concern.

### 7.2 Work Items
```yaml
work_items:
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_requirements
  activity_id: act_proj_resource_finder_01
  work_item_type: local:requirements
  label: Shared Requirements
  description: Define users, accessibility constraints, data fields, and acceptance criteria.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:40:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  activity_marker_id: marker_proj_planning
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_ui
  activity_id: act_proj_resource_finder_01
  work_item_type: local:interface_component
  label: Group A Interface
  description: Build search controls, result cards, keyboard navigation, and focus states.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:41:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    record_kind: group
    record_id: grp_proj_a
  activity_marker_id: marker_proj_prototype
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_data
  activity_id: act_proj_resource_finder_01
  work_item_type: local:data_component
  label: Group A Data and Search
  description: Normalize resource data and implement search and filter logic.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:42:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  activity_marker_id: marker_proj_prototype
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_integration_v1
  activity_id: act_proj_resource_finder_01
  work_item_type: local:integration_build
  label: Group A Integration — Attempt 1
  description: Integrate interface and data modules through the shared remote repository.
  status: blocked
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:43:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    record_kind: group
    record_id: grp_proj_a
  activity_marker_id: marker_proj_integration
  status_reason:
    reason_code: external_tool_unavailable
    note: The source-control remote was unavailable during the checkpoint. Local work remained intact.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-11-04T08:34:00-05:00'
    related_record:
      record_kind: activity_event
      record_id: event_proj_repo_interruption_01
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_integration_v2
  activity_id: act_proj_resource_finder_01
  work_item_type: local:integration_build
  label: Group A Integration — Restored
  description: Integrate the preserved local modules after remote access returned.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-04T14:05:00-05:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    record_kind: group
    record_id: grp_proj_a
  activity_marker_id: marker_proj_testing
  supersedes_work_item_id: workitem_proj_a_integration_v1
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_tests
  activity_id: act_proj_resource_finder_01
  work_item_type: local:test_suite
  label: Group A Test Suite
  description: Run automated and manual tests against the restored integration build.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:44:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  activity_marker_id: marker_proj_testing
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_access
  activity_id: act_proj_resource_finder_01
  work_item_type: local:accessibility_audit
  label: Group A Accessibility Audit
  description: Verify keyboard operation, visible focus, labels, and readable contrast.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:45:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  activity_marker_id: marker_proj_testing
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_a_release
  activity_id: act_proj_resource_finder_01
  work_item_type: local:release
  label: Group A Release Build
  description: Prepare a demonstrable release with traceable evidence.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:46:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_a
  assignee_reference:
    record_kind: group
    record_id: grp_proj_a
  activity_marker_id: marker_proj_release
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_b_integration
  activity_id: act_proj_resource_finder_01
  work_item_type: local:integration_build
  label: Group B Integrated Prototype
  description: Integrate the application, physical display prototype, and documentation.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:47:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_b
  assignee_reference:
    record_kind: group
    record_id: grp_proj_b
  activity_marker_id: marker_proj_integration
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_b_tests
  activity_id: act_proj_resource_finder_01
  work_item_type: local:test_suite
  label: Group B Test Suite
  description: Develop and execute integration and regression tests.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:48:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_b
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  activity_marker_id: marker_proj_testing
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_b_access
  activity_id: act_proj_resource_finder_01
  work_item_type: local:accessibility_audit
  label: Group B Accessibility Audit
  description: Review interface and physical-display accessibility.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:49:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_b
  assignee_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  activity_marker_id: marker_proj_testing
- record_owner: concord
  record_kind: work_item
  work_item_id: workitem_proj_b_release
  activity_id: act_proj_resource_finder_01
  work_item_type: local:release
  label: Group B Release Build
  description: Prepare release notes, CAD export, and final demonstration.
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T15:50:00-04:00'
    source_kind: manual
    note: Bounded project Work Item created.
  group_id: grp_proj_b
  assignee_reference:
    record_kind: group
    record_id: grp_proj_b
  activity_marker_id: marker_proj_release
```

`workitem_proj_a_integration_v1` remains historically blocked because of the external outage. `workitem_proj_a_integration_v2` records the later completed state. The blocked state is not converted into poor performance.

### 7.3 Work-Item Dependencies
```yaml
work_item_dependencies:
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_a_ui_to_int
  predecessor_work_item_id: workitem_proj_a_ui
  dependent_work_item_id: workitem_proj_a_integration_v1
  dependency_type: requires_component
  status: satisfied
  note: Interface component must be available before initial integration.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:00:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_a_data_to_int
  predecessor_work_item_id: workitem_proj_a_data
  dependent_work_item_id: workitem_proj_a_integration_v1
  dependency_type: requires_component
  status: satisfied
  note: Data and search component must be available before initial integration.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:01:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_a_int_to_test
  predecessor_work_item_id: workitem_proj_a_integration_v2
  dependent_work_item_id: workitem_proj_a_tests
  dependency_type: requires_build
  status: satisfied
  note: Tests require the restored integrated build.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:02:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_a_ui_to_access
  predecessor_work_item_id: workitem_proj_a_ui
  dependent_work_item_id: workitem_proj_a_access
  dependency_type: requires_component
  status: satisfied
  note: Accessibility audit requires a usable interface.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:03:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_a_test_to_release
  predecessor_work_item_id: workitem_proj_a_tests
  dependent_work_item_id: workitem_proj_a_release
  dependency_type: release_gate
  status: satisfied
  note: Release requires completed testing.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:04:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_a_access_to_release
  predecessor_work_item_id: workitem_proj_a_access
  dependent_work_item_id: workitem_proj_a_release
  dependency_type: release_gate
  status: satisfied
  note: Release requires completed accessibility Review.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:05:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_b_int_to_test
  predecessor_work_item_id: workitem_proj_b_integration
  dependent_work_item_id: workitem_proj_b_tests
  dependency_type: requires_build
  status: satisfied
  note: Tests require the integrated prototype.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:06:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_b_test_to_release
  predecessor_work_item_id: workitem_proj_b_tests
  dependent_work_item_id: workitem_proj_b_release
  dependency_type: release_gate
  status: satisfied
  note: Release requires completed testing.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:07:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
- record_owner: concord
  record_kind: work_item_dependency
  work_item_dependency_id: dep_proj_b_access_to_release
  predecessor_work_item_id: workitem_proj_b_access
  dependent_work_item_id: workitem_proj_b_release
  dependency_type: release_gate
  status: satisfied
  note: Release requires completed accessibility Review.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T16:08:00-04:00'
    source_kind: manual
    note: Project dependency recorded.
```

Dependencies explain sequencing and blocked work. They do not create evidence or Scores.

### 7.4 Activity Events
```yaml
activity_events:
- record_owner: concord
  record_kind: activity_event
  activity_event_id: event_proj_architecture_decision_01
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_01
  event_type: decision
  occurred_at: '2026-11-02T08:31:00-05:00'
  sequence: 1
  activity_marker_id: marker_proj_planning
  contributor_references:
  - actor_kind: core_student
    actor_id: stu_001
    owning_system: core
    display_label_snapshot: Student 001
  - actor_kind: core_student
    actor_id: stu_002
    owning_system: core
    display_label_snapshot: Student 002
  - actor_kind: core_student
    actor_id: stu_003
    owning_system: core
    display_label_snapshot: Student 003
  subject_references:
  - subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  description: Group A selected a modular interface/data architecture and documented the rationale.
  outcome: The project was decomposed into interface, data/search, integration, testing, and accessibility
    work.
  status: completed
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T08:35:00-05:00'
    source_kind: manual
    note: Teacher recorded a meaningful design decision.
- record_owner: concord
  record_kind: activity_event
  activity_event_id: event_proj_repo_interruption_01
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_03
  event_type: interruption
  occurred_at: '2026-11-04T08:29:00-05:00'
  sequence: 2
  group_id: grp_proj_a
  activity_marker_id: marker_proj_integration
  work_item_id: workitem_proj_a_integration_v1
  contributor_references:
  - actor_kind: core_student
    actor_id: stu_001
    owning_system: core
    display_label_snapshot: Student 001
  - actor_kind: core_student
    actor_id: stu_002
    owning_system: core
    display_label_snapshot: Student 002
  - actor_kind: core_student
    actor_id: stu_003
    owning_system: core
    display_label_snapshot: Student 003
  subject_references:
  - subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  description: The source-control remote was temporarily unavailable during the Group A integration checkpoint.
  outcome: The Group preserved local work, recorded the blockage, and deferred the remote merge.
  status: resolved
  extension_data:
    local:project_exception:
      external_system: github
      local_work_preserved: true
      performance_inference: none
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-04T08:34:00-05:00'
    source_kind: manual
    note: Teacher recorded a contextual interruption.
- record_owner: concord
  record_kind: activity_event
  activity_event_id: event_proj_membership_rebalance_01
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_04
  event_type: teacher_intervention
  occurred_at: '2026-11-05T08:00:00-05:00'
  sequence: 3
  activity_marker_id: marker_proj_testing
  contributor_references:
  - actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  subject_references:
  - subject_kind: core_student
    subject_id: stu_003
    owning_system: core
  - subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  - subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  description: The teacher reassigned Student 003 from Group A to Group B to balance the expanded accessibility-testing
    scope.
  outcome: Earlier Membership, Role, Responsibility, and contribution history remained attached to Group
    A; later context uses Group B.
  status: completed
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
    timestamp: '2026-11-05T08:00:00-05:00'
    source_kind: manual
    note: Teacher recorded the contextual Membership change.
- record_owner: concord
  record_kind: activity_event
  activity_event_id: event_proj_test_failure_01
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_04
  event_type: test
  occurred_at: '2026-11-05T08:22:00-05:00'
  sequence: 4
  group_id: grp_proj_b
  activity_marker_id: marker_proj_testing
  work_item_id: workitem_proj_b_tests
  contributor_references:
  - actor_kind: core_student
    actor_id: stu_003
    owning_system: core
    display_label_snapshot: Student 003
  - actor_kind: core_student
    actor_id: stu_005
    owning_system: core
    display_label_snapshot: Student 005
  subject_references:
  - subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  description: A regression test revealed that one filter reset keyboard focus incorrectly.
  outcome: The defect was reproduced, corrected, and retested before release.
  status: completed
  extension_data:
    local:test_result:
      result: failed_then_passed
      defect_category: focus_management
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-05T08:40:00-05:00'
    source_kind: manual
    note: Meaningful test and correction recorded.
- record_owner: concord
  record_kind: activity_event
  activity_event_id: event_proj_release_handoff_01
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  event_type: handoff
  occurred_at: '2026-11-06T08:38:00-05:00'
  sequence: 5
  activity_marker_id: marker_proj_release
  contributor_references:
  - actor_kind: system
    actor_id: grp_proj_a
    owning_system: concord
    display_label_snapshot: Project Group A
  - actor_kind: system
    actor_id: grp_proj_b
    owning_system: concord
    display_label_snapshot: Project Group B
  subject_references:
  - subject_kind: concord_activity
    subject_id: act_proj_resource_finder_01
    owning_system: concord
  description: Both Groups presented release evidence, known limitations, and source locations to the
    teacher.
  outcome: The release package was accepted for final scoring and evidence-only exhibition archiving.
  status: completed
  privacy_policy:
    classification: classroom_shared
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T08:45:00-05:00'
    source_kind: manual
    note: Final project handoff recorded.
```

The Events record meaningful chronology and context. Routine actions are not converted into Events, and no Event automatically becomes a contribution or Score.

### 7.5 Contribution Claims
```yaml
contribution_claims:
- record_owner: concord
  record_kind: contribution_claim
  contribution_claim_id: claim_proj_001_keyboard
  activity_id: act_proj_resource_finder_01
  claimant_reference:
    owning_system: core
    record_kind: student
    record_id: stu_001
    display_label: Student 001
  claimed_contributor_reference:
    owning_system: core
    record_kind: student
    record_id: stu_001
    display_label: Student 001
  contribution_type: local:implementation
  description: Student 001 implemented keyboard navigation and visible focus behavior for Group A.
  artifact_instance_id: art_proj_log_a
  work_item_id: workitem_proj_a_ui
  responsibility_assignment_id: resp_proj_a_keyboard
  corroboration_status: corroborated
  moderation_requirement: required
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
    timestamp: '2026-11-05T09:05:00-05:00'
    source_kind: manual
    note: Contribution Claim recorded from reviewed project evidence.
- record_owner: concord
  record_kind: contribution_claim
  contribution_claim_id: claim_proj_004_about_005
  activity_id: act_proj_resource_finder_01
  claimant_reference:
    owning_system: core
    record_kind: student
    record_id: stu_004
    display_label: Student 004
  claimed_contributor_reference:
    owning_system: core
    record_kind: student
    record_id: stu_005
    display_label: Student 005
  contribution_type: local:testing
  description: Student 004 stated that Student 005 created the entire Group B test suite.
  artifact_instance_id: art_proj_reflection_004
  work_item_id: workitem_proj_b_tests
  responsibility_assignment_id: resp_proj_b_tests
  corroboration_status: partially_corroborated
  moderation_requirement: required
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:05:00-05:00'
    source_kind: manual
    note: Peer Contribution Claim created from reviewed reflection.
- record_owner: concord
  record_kind: contribution_claim
  contribution_claim_id: claim_proj_005_tests_v1
  activity_id: act_proj_resource_finder_01
  claimant_reference:
    owning_system: core
    record_kind: student
    record_id: stu_005
    display_label: Student 005
  claimed_contributor_reference:
    owning_system: core
    record_kind: student
    record_id: stu_005
    display_label: Student 005
  contribution_type: local:testing
  description: Student 005 initially claimed sole authorship of the Group B integration test suite.
  artifact_instance_id: art_proj_reflection_005
  work_item_id: workitem_proj_b_tests
  responsibility_assignment_id: resp_proj_b_tests
  corroboration_status: disputed
  moderation_requirement: required
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:06:00-05:00'
    source_kind: manual
    note: Initial self-claim recorded before evidence reconciliation.
- record_owner: concord
  record_kind: contribution_claim
  contribution_claim_id: claim_proj_005_tests_v2
  activity_id: act_proj_resource_finder_01
  claimant_reference:
    owning_system: core
    record_kind: student
    record_id: stu_005
    display_label: Student 005
  claimed_contributor_reference:
    owning_system: core
    record_kind: student
    record_id: stu_005
    display_label: Student 005
  contribution_type: local:testing
  description: Student 005 clarified that they designed the test matrix and implemented most automated
    tests, while Student 004 supplied acceptance cases and Student 003 completed accessibility regression
    checks.
  artifact_instance_id: art_proj_reflection_005
  work_item_id: workitem_proj_b_tests
  activity_event_id: event_proj_test_failure_01
  responsibility_assignment_id: resp_proj_b_tests
  corroboration_status: corroborated
  moderation_requirement: required
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_005
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:10:00-05:00'
    source_kind: manual
    note: Corrected Contribution Claim created after teacher Review.
  supersedes_contribution_claim_id: claim_proj_005_tests_v1
```

Contribution Claims remain claims until reviewed and, where required, Moderated. The corrected Student 005 Claim supersedes the disputed original without deleting it.

## 8. Template and Packet Records

### 8.1 Template Definitions
```yaml
template_definitions:
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_planning_canvas
  name: Collaborative Project Planning Canvas
  artifact_category: local:project_plan
  purpose: Capture Group requirements, architecture choices, role plan, and initial Work Item decomposition.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-28T14:00:00-04:00'
    source_kind: manual
    note: Reusable planning Template Definition created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_iteration_log
  name: Project Iteration and Debugging Log
  artifact_category: local:iteration_log
  purpose: Record builds, tests, defects, debugging decisions, and revised plans across project Sessions.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-28T14:05:00-04:00'
    source_kind: manual
    note: Reusable iteration-log Template Definition created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_contribution_reflection
  name: Individual Project Contribution Reflection
  artifact_category: local:contribution_reflection
  purpose: Collect a participant's bounded claims about specific project contributions and collaboration.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-28T14:10:00-04:00'
    source_kind: manual
    note: Reusable contribution-reflection Template Definition created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_design_review
  name: Project Design Review and Handoff
  artifact_category: local:design_review
  purpose: Document Group architecture, testing evidence, known limitations, and release handoff.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-28T14:15:00-04:00'
    source_kind: manual
    note: Reusable design-review Template Definition created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_teacher_tracker
  name: Collaborative Project Teacher Observation Tracker
  artifact_category: teacher_observation
  purpose: Record teacher observations of Groups, individuals, work states, and Criteria across Sessions.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-28T14:20:00-04:00'
    source_kind: manual
    note: Reusable teacher-tracker Template Definition created.
- record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_scoring_rubric
  name: Collaborative Project Mixed-Scoring Rubric
  artifact_category: scoring_rubric
  purpose: Provide a paper surface for separate standards-based and local Criterion judgments.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-28T14:25:00-04:00'
    source_kind: manual
    note: Reusable mixed-scoring rubric Template Definition created.
```

### 8.2 Immutable Template Versions

```yaml
template_versions:
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_planning_canvas_r1
  template_id: tmpl_proj_planning_canvas
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_planning_canvas_r1
  artifact_category: local:project_plan
  page_manifest:
  - page_kind: primary
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: group_and_teacher
  default_authorship_expectation:
    mode: local:collective_group_with_named_recorder
  default_subject_expectation:
    mode: local:generated_for_one_activity_group
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
    timestamp: '2026-10-28T15:00:00-04:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_iteration_log_r1
  template_id: tmpl_proj_iteration_log
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_iteration_log_r1
  artifact_category: local:iteration_log
  page_manifest:
  - page_kind: primary
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: group_and_teacher
  default_authorship_expectation:
    mode: local:collective_group_with_named_recorder
  default_subject_expectation:
    mode: local:generated_for_one_activity_group
  supported_criterion_ids:
  - crit_proj_iterative_development
  - crit_proj_testing_debugging
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
    timestamp: '2026-10-28T15:05:00-04:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_contribution_reflection_r1
  template_id: tmpl_proj_contribution_reflection
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_contribution_reflection_r1
  artifact_category: local:contribution_reflection
  page_manifest:
  - page_kind: primary
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:individual_author
  default_subject_expectation:
    mode: local:individual_author_and_claimed_contributors
  supported_criterion_ids:
  - crit_proj_collaborative_handoff
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
    timestamp: '2026-10-28T15:10:00-04:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_design_review_r1
  template_id: tmpl_proj_design_review
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_design_review_r1
  artifact_category: local:design_review
  page_manifest:
  - page_kind: primary
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: group_and_teacher
  default_authorship_expectation:
    mode: local:collective_group_with_named_recorder
  default_subject_expectation:
    mode: local:generated_for_one_activity_group
  supported_criterion_ids:
  - crit_proj_iterative_development
  - crit_proj_testing_debugging
  - crit_proj_collaborative_handoff
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
    timestamp: '2026-10-28T15:15:00-04:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_teacher_tracker_r1
  template_id: tmpl_proj_teacher_tracker
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_teacher_tracker_r1
  artifact_category: teacher_observation
  page_manifest:
  - page_kind: observation
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:teacher_author
  default_subject_expectation:
    mode: local:multiple_participants_groups_work_items_and_events
  supported_criterion_ids:
  - crit_proj_iterative_development
  - crit_proj_testing_debugging
  - crit_proj_collaborative_handoff
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
    timestamp: '2026-10-28T15:20:00-04:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
- record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_scoring_rubric_r1
  template_id: tmpl_proj_scoring_rubric
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_scoring_rubric_r1
  artifact_category: scoring_rubric
  page_manifest:
  - page_kind: rubric
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: teacher_restricted
  default_authorship_expectation:
    mode: local:teacher_author
  default_subject_expectation:
    mode: local:score_targets_and_criteria
  supported_criterion_ids:
  - crit_proj_iterative_development
  - crit_proj_testing_debugging
  - crit_proj_collaborative_handoff
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
    timestamp: '2026-10-28T15:25:00-04:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
```

Each generated Artifact identifies the exact immutable Template Version used. Changes to wording, layout, page structure, QR behavior, authorship expectations, Subject expectations, or supported Criteria require a new version.

### 8.3 Packet Definition and Version
```yaml
packet_definition:
  record_owner: concord
  record_kind: packet_definition
  packet_definition_id: pktdef_proj_standard
  name: Collaborative Software Project Packet
  purpose: Assemble Group planning, iteration, design-review, individual reflection, teacher observation,
    and mixed-scoring surfaces.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-29T14:00:00-04:00'
    source_kind: manual
    note: Reusable project Packet Definition created.
packet_version:
  record_owner: concord
  record_kind: packet_version
  packet_version_id: pktv_proj_standard_r1
  packet_definition_id: pktdef_proj_standard
  version_label: Revision 1
  revision_sequence: 1
  component_ids:
  - pktcmp_proj_01
  - pktcmp_proj_02
  - pktcmp_proj_03
  - pktcmp_proj_04
  - pktcmp_proj_05
  - pktcmp_proj_06
  generation_rules:
  - Generate planning, iteration-log, and design-review copies per parent Group.
  - Generate contribution reflections for selected participants.
  - Generate one teacher tracker and one scoring rubric per Activity.
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-29T14:10:00-04:00'
    source_kind: manual
    note: Immutable project Packet Version created.
  status: active
```

### 8.4 Packet Components

```yaml
packet_components:
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_proj_01
  packet_version_id: pktv_proj_standard_r1
  sequence: 1
  component_kind: concord_template
  template_version_id: tmplv_proj_planning_canvas_r1
  quantity_rule:
    mode: one_per_parent_group
  audience_rule:
    target_kind: concord_group
    exclude_child_groups: true
  requirement_level: required
  label: Group planning canvas
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_proj_02
  packet_version_id: pktv_proj_standard_r1
  sequence: 2
  component_kind: concord_template
  template_version_id: tmplv_proj_iteration_log_r1
  quantity_rule:
    mode: one_per_parent_group
  audience_rule:
    target_kind: concord_group
    exclude_child_groups: true
  requirement_level: required
  label: Group iteration log
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_proj_03
  packet_version_id: pktv_proj_standard_r1
  sequence: 3
  component_kind: concord_template
  template_version_id: tmplv_proj_contribution_reflection_r1
  quantity_rule:
    mode: selected_participants
    participant_ids:
    - stu_004
    - stu_005
  audience_rule:
    target_kind: core_student
  requirement_level: conditional
  condition: Generated for participants selected for contribution-claim validation.
  label: Individual contribution reflection
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_proj_04
  packet_version_id: pktv_proj_standard_r1
  sequence: 4
  component_kind: concord_template
  template_version_id: tmplv_proj_design_review_r1
  quantity_rule:
    mode: one_per_parent_group
  audience_rule:
    target_kind: concord_group
    exclude_child_groups: true
  requirement_level: required
  label: Group design review and handoff
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_proj_05
  packet_version_id: pktv_proj_standard_r1
  sequence: 5
  component_kind: concord_template
  template_version_id: tmplv_proj_teacher_tracker_r1
  quantity_rule:
    mode: one_per_activity
  audience_rule:
    target_kind: authorized_actor
  requirement_level: required
  label: Teacher observation tracker
- record_owner: concord
  record_kind: packet_component
  packet_component_id: pktcmp_proj_06
  packet_version_id: pktv_proj_standard_r1
  sequence: 6
  component_kind: concord_template
  template_version_id: tmplv_proj_scoring_rubric_r1
  quantity_rule:
    mode: one_per_activity
  audience_rule:
    target_kind: authorized_actor
  requirement_level: required
  label: Mixed-scoring rubric
```

### 8.5 Packet Instance

```yaml
record_owner: concord
record_kind: packet_instance
packet_instance_id: pkt_proj_01
packet_version_id: pktv_proj_standard_r1
activity_id: act_proj_resource_finder_01
generation_status: completed
generated_at: '2026-11-02T07:20:00-05:00'
generated_by:
  actor_kind: authorized_adult
  actor_id: actor_teacher_001
  owning_system: local_example_identity
  display_label_snapshot: Teacher 001
artifact_instance_ids:
- art_proj_plan_a
- art_proj_plan_b
- art_proj_log_a
- art_proj_log_b
- art_proj_reflection_004
- art_proj_reflection_005
- art_proj_review_a
- art_proj_review_b
- art_proj_teacher_tracker
- art_proj_scoring_rubric
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-11-02T07:20:00-05:00'
  source_kind: generated
  note: Project Packet Instance generated.
```

The Packet Instance preserves the exact Packet Version and generated Artifact identities. External project records are not converted into Concord Artifact Instances merely because they are used alongside the packet.

## 9. Artifact and Routing Records

### 9.1 Artifact Instances
```yaml
artifact_instances:
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_plan_a
  template_version_id: tmplv_proj_planning_canvas_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  session_id: ses_proj_01
  group_id: grp_proj_a
  artifact_category: local:project_plan
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_plan_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:21:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_plan_b
  template_version_id: tmplv_proj_planning_canvas_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  session_id: ses_proj_01
  group_id: grp_proj_b
  artifact_category: local:project_plan
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_plan_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:22:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_log_a
  template_version_id: tmplv_proj_iteration_log_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  group_id: grp_proj_a
  artifact_category: local:iteration_log
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_log_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:23:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_log_b
  template_version_id: tmplv_proj_iteration_log_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  group_id: grp_proj_b
  artifact_category: local:iteration_log
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_log_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:24:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_reflection_004
  template_version_id: tmplv_proj_contribution_reflection_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  session_id: ses_proj_05
  group_id: grp_proj_b
  artifact_category: local:contribution_reflection
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_proj_reflection_004_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:25:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_reflection_005
  template_version_id: tmplv_proj_contribution_reflection_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  session_id: ses_proj_05
  group_id: grp_proj_b
  artifact_category: local:contribution_reflection
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_proj_reflection_005_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:26:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_review_a
  template_version_id: tmplv_proj_design_review_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  session_id: ses_proj_05
  group_id: grp_proj_a
  artifact_category: local:design_review
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_review_a_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:27:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_review_b
  template_version_id: tmplv_proj_design_review_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  session_id: ses_proj_05
  group_id: grp_proj_b
  artifact_category: local:design_review
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_review_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:28:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_teacher_tracker
  template_version_id: tmplv_proj_teacher_tracker_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  artifact_category: teacher_observation
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_proj_tracker_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:29:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
- record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_scoring_rubric
  template_version_id: tmplv_proj_scoring_rubric_r1
  activity_id: act_proj_resource_finder_01
  packet_instance_id: pkt_proj_01
  artifact_category: scoring_rubric
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: teacher_restricted
  page_ids:
  - page_proj_rubric_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:30:00-05:00'
    source_kind: generated
    note: Artifact generated from the exact Template Version.
```

### 9.2 Artifact Pages

```yaml
artifact_pages:
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_plan_a_01
  artifact_instance_id: art_proj_plan_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_plan_a_01
  human_fallback: PRA-PLAN
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:21:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_plan_b_01
  artifact_instance_id: art_proj_plan_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_plan_b_01
  human_fallback: PRB-PLAN
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:22:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_log_a_01
  artifact_instance_id: art_proj_log_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_log_a_01
  human_fallback: PRA-LOG
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:23:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_log_b_01
  artifact_instance_id: art_proj_log_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_log_b_01
  human_fallback: PRB-LOG
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:24:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_reflection_004_01
  artifact_instance_id: art_proj_reflection_004
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_reflection_004_01
  human_fallback: PR-REF-004
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:25:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_reflection_005_01
  artifact_instance_id: art_proj_reflection_005
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_reflection_005_01
  human_fallback: PR-REF-005
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:26:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_review_a_01
  artifact_instance_id: art_proj_review_a
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_review_a_01
  human_fallback: PRA-REV
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:27:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_review_b_01
  artifact_instance_id: art_proj_review_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_review_b_01
  human_fallback: PRB-REV
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:28:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_tracker_01
  artifact_instance_id: art_proj_teacher_tracker
  page_number: 1
  expected_page_count: 1
  page_kind: observation
  return_expected: true
  route_required: true
  route_id: route_proj_tracker_01
  human_fallback: PR-TRACK
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:29:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
- record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_rubric_01
  artifact_instance_id: art_proj_scoring_rubric
  page_number: 1
  expected_page_count: 1
  page_kind: rubric
  return_expected: true
  route_required: true
  route_id: route_proj_rubric_01
  human_fallback: PR-RUBRIC
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T07:30:00-05:00'
    source_kind: generated
    note: Expected physical page identity created before rendering.
```

### 9.3 Core Route Registrations

```yaml
route_registrations:
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_plan_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_plan_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_plan_a_01
  status: active
  registered_at: '2026-11-02T07:21:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_plan_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_plan_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_plan_b_01
  status: active
  registered_at: '2026-11-02T07:22:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_log_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_log_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_log_a_01
  status: active
  registered_at: '2026-11-02T07:23:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_log_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_log_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_log_b_01
  status: active
  registered_at: '2026-11-02T07:24:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_reflection_004_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_reflection_004_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_reflection_004_01
  status: active
  registered_at: '2026-11-02T07:25:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_reflection_005_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_reflection_005_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_reflection_005_01
  status: active
  registered_at: '2026-11-02T07:26:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_review_a_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_review_a_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_review_a_01
  status: active
  registered_at: '2026-11-02T07:27:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_review_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_review_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_review_b_01
  status: active
  registered_at: '2026-11-02T07:28:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_tracker_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_tracker_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_tracker_01
  status: active
  registered_at: '2026-11-02T07:29:00-05:00'
- owning_system: core
  record_kind: route_registration
  route_id: route_proj_rubric_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
    route_id: route_proj_rubric_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_rubric_01
  status: active
  registered_at: '2026-11-02T07:30:00-05:00'
```

Representative locator:

```text
PDS2|m=concord|c=cls_apcsp_p01|w=act_proj_resource_finder_01|r=route_proj_log_a_01
```

The locator does not encode a student, Group, Author, Subject, Criterion, standard, contribution, or Score. Those meanings resolve through Concord-owned records.

## 10. Artifact Author Associations
```yaml
artifact_authors:
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_plan_a_group
  artifact_instance_id: art_proj_plan_a
  author_reference:
    record_kind: group
    record_id: grp_proj_a
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T09:10:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_plan_a_recorder
  artifact_instance_id: art_proj_plan_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T09:11:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_a
  role_assignment_id: role_proj_001_ui_v1
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_plan_b_group
  artifact_instance_id: art_proj_plan_b
  author_reference:
    record_kind: group
    record_id: grp_proj_b
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T09:12:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_plan_b_recorder
  artifact_instance_id: art_proj_plan_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T09:13:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_b
  role_assignment_id: role_proj_004_product
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_log_a_group
  artifact_instance_id: art_proj_log_a
  author_reference:
    record_kind: group
    record_id: grp_proj_a
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:10:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_log_a_recorder
  artifact_instance_id: art_proj_log_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:11:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_a
  role_assignment_id: role_proj_002_integrate_v2
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_log_b_group
  artifact_instance_id: art_proj_log_b
  author_reference:
    record_kind: group
    record_id: grp_proj_b
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:12:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_log_b_recorder
  artifact_instance_id: art_proj_log_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:13:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_b
  role_assignment_id: role_proj_006_docs
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_reflection_004
  artifact_instance_id: art_proj_reflection_004
  author_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  authorship_mode: individual_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:20:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_reflection_005
  artifact_instance_id: art_proj_reflection_005
  author_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  authorship_mode: individual_author
  representation_status: individual_view
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:21:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_review_a_group
  artifact_instance_id: art_proj_review_a
  author_reference:
    record_kind: group
    record_id: grp_proj_a
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:22:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_review_a_recorder
  artifact_instance_id: art_proj_review_a
  author_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:23:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_a
  role_assignment_id: role_proj_002_integrate_v2
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_review_b_group
  artifact_instance_id: art_proj_review_b
  author_reference:
    record_kind: group
    record_id: grp_proj_b
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:24:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_review_b_recorder
  artifact_instance_id: art_proj_review_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:25:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_b
  role_assignment_id: role_proj_006_docs
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_tracker_teacher
  artifact_instance_id: art_proj_teacher_tracker
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: not_applicable
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:26:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_rubric_teacher
  artifact_instance_id: art_proj_scoring_rubric
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: not_applicable
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:27:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
```

The collective Group and named recorder are separate Author associations. The recorder is not treated as the sole contributor. The teacher tracker and scoring rubric are teacher-authored. Repository or cloud-account ownership is not used as an authorship rule.

## 11. Artifact Subject Associations
```yaml
artifact_subjects:
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_plan_a_group
  artifact_instance_id: art_proj_plan_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-02T09:30:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_plan_a_marker
  artifact_instance_id: art_proj_plan_a
  subject_reference:
    subject_kind: concord_activity_marker
    subject_id: marker_proj_planning
    owning_system: concord
  subject_role: activity_context
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
    timestamp: '2026-11-02T09:30:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_plan_b_group
  artifact_instance_id: art_proj_plan_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-02T09:31:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_plan_b_marker
  artifact_instance_id: art_proj_plan_b
  subject_reference:
    subject_kind: concord_activity_marker
    subject_id: marker_proj_planning
    owning_system: concord
  subject_role: activity_context
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
    timestamp: '2026-11-02T09:31:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_a_group
  artifact_instance_id: art_proj_log_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-06T09:20:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_a_ses_proj_02
  artifact_instance_id: art_proj_log_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_02
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-06T09:20:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_a_ses_proj_03
  artifact_instance_id: art_proj_log_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_03
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-06T09:20:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_a_ses_proj_04
  artifact_instance_id: art_proj_log_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_04
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-06T09:20:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_b_group
  artifact_instance_id: art_proj_log_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-06T09:21:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_b_ses_proj_02
  artifact_instance_id: art_proj_log_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_02
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-06T09:21:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_b_ses_proj_03
  artifact_instance_id: art_proj_log_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_03
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-06T09:21:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_log_b_ses_proj_04
  artifact_instance_id: art_proj_log_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_04
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-06T09:21:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_reflection_004_self
  artifact_instance_id: art_proj_reflection_004
  subject_reference:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  subject_role: general_subject
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:35:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_reflection_004_group
  artifact_instance_id: art_proj_reflection_004
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:35:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_reflection_005_self
  artifact_instance_id: art_proj_reflection_005
  subject_reference:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  subject_role: general_subject
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:36:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_reflection_005_group
  artifact_instance_id: art_proj_reflection_005
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:36:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_review_a_group
  artifact_instance_id: art_proj_review_a
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-09T09:37:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_review_a_session
  artifact_instance_id: art_proj_review_a
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_05
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-09T09:37:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_review_a_release
  artifact_instance_id: art_proj_review_a
  subject_reference:
    subject_kind: concord_work_item
    subject_id: workitem_proj_a_release
    owning_system: concord
  subject_role: evaluated_work_item
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
    timestamp: '2026-11-09T09:37:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_review_b_group
  artifact_instance_id: art_proj_review_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-09T09:38:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_review_b_session
  artifact_instance_id: art_proj_review_b
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_05
    owning_system: concord
  subject_role: session_context
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
    timestamp: '2026-11-09T09:38:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_review_b_release
  artifact_instance_id: art_proj_review_b
  subject_reference:
    subject_kind: concord_work_item
    subject_id: workitem_proj_b_release
    owning_system: concord
  subject_role: evaluated_work_item
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
    timestamp: '2026-11-09T09:38:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_stu_001
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_stu_002
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_002
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_stu_003
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_003
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_stu_004
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_stu_005
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_stu_006
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: core_student
    subject_id: stu_006
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_grp_proj_a
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_grp_proj_b
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_grp_proj_a_ui
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a_ui
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_grp_proj_a_data
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a_data
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_ses_proj_01
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_01
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_ses_proj_02
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_02
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_ses_proj_03
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_03
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_ses_proj_04
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_04
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_tracker_ses_proj_05
  artifact_instance_id: art_proj_teacher_tracker
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_05
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:40:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_stu_001_testing
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_stu_004_testing
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_stu_005_testing
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_grp_proj_a_iteration
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_grp_proj_a_handoff
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_grp_proj_b_iteration
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_grp_proj_b_handoff
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_rubric_stu_004_handoff
  artifact_instance_id: art_proj_scoring_rubric
  subject_reference:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  subject_role: observed_participant
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: teacher_restricted
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:42:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
```

The teacher tracker remains one multi-Subject Artifact. It is not duplicated into student-specific source records. Artifact Subjects do not automatically become Score targets.

## 12. Scan, Review, Moderation, and Correction

### 12.1 Core-Retained Source Scans
```yaml
core_source_scans:
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_proj_batch_01
  source_filename: synthetic_project_batch_01.pdf
  retained_at: '2026-11-02T09:00:00-05:00'
  page_count: 2
  page_manifest:
  - source_page_index: 0
    route_id: route_proj_plan_a_01
  - source_page_index: 1
    route_id: route_proj_plan_b_01
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_proj_batch_02
  source_filename: synthetic_project_batch_02.pdf
  retained_at: '2026-11-06T09:00:00-05:00'
  page_count: 4
  page_manifest:
  - source_page_index: 0
    route_id: route_proj_log_a_01
  - source_page_index: 1
    route_id: route_proj_log_b_01
  - source_page_index: 2
    route_id: route_proj_reflection_004_01
  - source_page_index: 3
    route_id: route_proj_reflection_005_01
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_proj_batch_03
  source_filename: synthetic_project_batch_03.pdf
  retained_at: '2026-11-09T09:00:00-05:00'
  page_count: 4
  page_manifest:
  - source_page_index: 0
    route_id: route_proj_review_a_01
  - source_page_index: 1
    route_id: route_proj_review_b_01
  - source_page_index: 2
    route_id: route_proj_tracker_01
  - source_page_index: 3
    route_id: route_proj_rubric_01
- owning_system: core
  record_kind: source_scan
  record_id: scan_core_proj_reflection_005_rescan
  source_filename: synthetic_project_reflection_005_rescan.pdf
  retained_at: '2026-11-09T09:05:00-05:00'
  page_count: 1
  page_manifest:
  - source_page_index: 0
    route_id: route_proj_reflection_005_01
```

### 12.2 Concord Scan References

```yaml
scan_references:
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_plan_a
  artifact_page_id: page_proj_plan_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_01
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-02T09:01:00-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_plan_b
  artifact_page_id: page_proj_plan_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_01
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-02T09:01:30-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_tracker
  artifact_page_id: page_proj_tracker_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_03
  source_page_index: 2
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-09T09:02:00-05:00'
    source_kind: routed
    note: Core route dispatch created the final teacher-tracker Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_log_a
  artifact_page_id: page_proj_log_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_02
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-06T09:01:00-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_log_b
  artifact_page_id: page_proj_log_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_02
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-06T09:01:30-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_reflection_004
  artifact_page_id: page_proj_reflection_004_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_02
  source_page_index: 2
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-06T09:02:00-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_reflection_005_initial
  artifact_page_id: page_proj_reflection_005_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_02
  source_page_index: 3
  routing_status: routed
  readability_status: partially_readable
  filing_status: confirmed
  review_status: reviewed_with_qualification
  preferred_for_use: false
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-06T09:02:30-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
  status_reason:
    reason_code: clearer_rescan_required
    note: The initial image is partially readable; a clearer rescan is preferred for consequential Review.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-11-06T09:10:00-05:00'
    related_record:
      record_kind: artifact_page
      record_id: page_proj_reflection_005_01
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_review_a
  artifact_page_id: page_proj_review_a_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_03
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-09T09:01:00-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_review_b
  artifact_page_id: page_proj_review_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_03
  source_page_index: 1
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-09T09:01:30-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_rubric
  artifact_page_id: page_proj_rubric_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_batch_03
  source_page_index: 3
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-09T09:02:00-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
- record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_reflection_005_rescan
  artifact_page_id: page_proj_reflection_005_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_reflection_005_rescan
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project
      owning_system: core
    timestamp: '2026-11-09T09:06:00-05:00'
    source_kind: routed
    note: Core route dispatch created the Concord Scan Reference.
  supersedes_scan_reference_id: scanref_proj_reflection_005_initial
```

The clearer Student 005 reflection rescan creates a new Core source scan and a new Scan Reference. The initial source and association remain available.

### 12.3 Artifact Reviews
```yaml
artifact_reviews:
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_plan_a
  artifact_instance_id: art_proj_plan_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-02T09:10:00-05:00'
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
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_plan_b
  artifact_instance_id: art_proj_plan_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-02T09:12:00-05:00'
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
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_tracker
  artifact_instance_id: art_proj_teacher_tracker
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-09T09:30:00-05:00'
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
  notes: Teacher observations span all Sessions, parent Groups, child Groups, selected Work Items, and
    named participants.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_log_a
  artifact_instance_id: art_proj_log_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-06T09:10:00-05:00'
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
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_log_b
  artifact_instance_id: art_proj_log_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-06T09:12:00-05:00'
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
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_reflection_004
  artifact_instance_id: art_proj_reflection_004
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-06T09:15:00-05:00'
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
  notes: The reflection contains a peer Contribution Claim about Student 005.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_reflection_005_v1
  artifact_instance_id: art_proj_reflection_005
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-06T09:16:00-05:00'
  readability_judgment: partially_readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: teacher_restricted
  relevance_judgment: relevant
  moderation_requirement: required
  scoring_readiness: awaiting_additional_evidence
  review_outcome: ready_with_qualification
  privacy_policy:
    classification: teacher_restricted
  notes: The reflection is readable enough to identify a sole-authorship claim, but a clearer rescan and
    external evidence are required.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_review_a
  artifact_instance_id: art_proj_review_a
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-09T09:15:00-05:00'
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
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_review_b
  artifact_instance_id: art_proj_review_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-09T09:17:00-05:00'
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
    classification: group_and_teacher
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_rubric
  artifact_instance_id: art_proj_scoring_rubric
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-09T09:35:00-05:00'
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
  notes: Paper scoring entries are legible and filed; canonical judgments remain the Score Records.
- record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_reflection_005_v2
  artifact_instance_id: art_proj_reflection_005
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-09T09:12:00-05:00'
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
  notes: The clearer rescan and external history support Review of the corrected bounded contribution
    claim.
  supersedes_artifact_review_id: review_proj_reflection_005_v1
```

Review determines filing, attribution, relevance, privacy, and readiness. It does not determine performance or create a Score.

### 12.4 Moderation Records
```yaml
moderation_records:
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_proj_claim_001
  target_evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_001_keyboard
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-11-06T10:00:00-05:00'
  status: accepted
  permitted_use: may_support_one_named_subject
  rationale: The Group log, repository commit, teacher observation, and Work Item history consistently
    support the bounded keyboard-accessibility claim.
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_001
      owning_system: core
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_proj_claim_004_about_005
  target_evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_004_about_005
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-11-06T10:05:00-05:00'
  status: accepted_with_qualification
  qualification: May corroborate Student 005's test-design contribution but may not support the statement
    that Student 005 created the entire test suite.
  permitted_use: may_corroborate_teacher_evidence
  rationale: External history shows substantial Student 005 work plus meaningful acceptance-case and regression-test
    contributions by other students.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_proj_claim_005_v1
  target_evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_005_tests_v1
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  - subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  - subject_kind: core_student
    subject_id: stu_003
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-11-06T10:10:00-05:00'
  status: disputed
  permitted_use: may_not_be_used_for_scoring
  rationale: The sole-authorship statement conflicts with the pull-request discussion, test history, teacher
    observation, and Student 004's acceptance-case contribution.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: moderation_record
  moderation_record_id: mod_proj_claim_005_v2
  target_evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_005_tests_v2
  target_subject_references:
  - subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  moderator:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  moderated_at: '2026-11-09T10:00:00-05:00'
  status: accepted
  permitted_use: may_support_one_named_subject
  rationale: The corrected claim matches the external pull request, test matrix, teacher tracker, and
    Group B design review.
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_005
      owning_system: core
  supersedes_moderation_record_id: mod_proj_claim_005_v1
```

Moderation distinguishes:

- a corroborated bounded claim;
- a peer claim accepted with qualification;
- a disputed sole-authorship claim;
- and a corrected accepted claim.

Acceptance does not select a Criterion or Score value. Dispute or rejection is not automatically negative evidence about a participant.

### 12.5 Correction Records
```yaml
correction_records:
- record_owner: concord
  record_kind: correction_record
  correction_id: corr_proj_reflection_005_scan
  target_reference:
    target_kind: concord_scan_reference
    target_id: scanref_proj_reflection_005_initial
    owning_system: concord
  correction_type: scan_replacement
  reason: A clearer rescan was required to review the contribution statement without altering the original
    retained source.
  correcting_actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  corrected_at: '2026-11-09T09:06:00-05:00'
  replacement_reference:
    record_kind: scan_reference
    record_id: scanref_proj_reflection_005_rescan
  related_source_reference:
    owning_system: core
    record_kind: source_scan
    record_id: scan_core_proj_reflection_005_rescan
  note: Both Scan References and both Core-retained source scans remain available.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: correction_record
  correction_id: corr_proj_claim_005
  target_reference:
    target_kind: concord_contribution_claim
    target_id: claim_proj_005_tests_v1
    owning_system: concord
  correction_type: metadata_correction
  reason: The initial sole-authorship statement overstated Student 005's contribution and conflicted with
    reviewed external and Group evidence.
  correcting_actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  corrected_at: '2026-11-09T09:10:00-05:00'
  replacement_reference:
    record_kind: contribution_claim
    record_id: claim_proj_005_tests_v2
  related_source_reference:
    owning_system: concord
    record_kind: external_reference
    record_id: extref_proj_pr_005
  note: The corrected Claim preserves substantial Student 005 testing work while naming other participants'
    contributions.
  privacy_policy:
    classification: teacher_restricted
- record_owner: concord
  record_kind: correction_record
  correction_id: corr_proj_score_005
  target_reference:
    target_kind: concord_score_record
    target_id: score_proj_005_testing_v1
    owning_system: concord
  correction_type: score_revision
  reason: Reviewed contribution and test evidence resolved the earlier deferred disposition and supported
    a scored individual judgment.
  correcting_actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  corrected_at: '2026-11-09T12:05:00-05:00'
  replacement_reference:
    record_kind: score_record
    record_id: score_proj_005_testing_v2
  related_source_reference:
    owning_system: concord
    record_kind: moderation_record
    record_id: mod_proj_claim_005_v2
  note: The earlier deferred record remains historically valid for the unresolved evidence state on November
    6.
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_005
      owning_system: core
```

The Correction Records explain scan replacement, contribution-claim correction, and Score revision. Same-type replacement relationships preserve efficient current-record traversal while the original records remain historically reproducible.

## 13. Attachments and External References

### 13.1 Attachments
```yaml
attachments:
- record_owner: concord
  record_kind: attachment
  attachment_id: attach_proj_architecture_a
  activity_id: act_proj_resource_finder_01
  attachment_type: project_diagram
  title: Group A Application Architecture Diagram
  session_id: ses_proj_01
  group_id: grp_proj_a
  work_item_id: workitem_proj_requirements
  artifact_instance_id: art_proj_plan_a
  contributor_references:
  - actor_kind: system
    actor_id: grp_proj_a
    owning_system: concord
    display_label_snapshot: Project Group A
  location:
    scheme: file
    locator: attachments/attach_proj_architecture_a.svg
    version_label: Revision 1
    content_digest: synthetic_digest_architecture_a
    display_label: Group A architecture diagram
  version_label: Revision 1
  availability_status: available
  review_status: reviewed
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-02T09:20:00-05:00'
    source_kind: imported
    note: Teacher attached a reviewed Group architecture diagram.
- record_owner: concord
  record_kind: attachment
  attachment_id: attach_proj_keyboard_demo_a
  activity_id: act_proj_resource_finder_01
  attachment_type: screenshot
  title: Group A Keyboard Navigation Demonstration
  session_id: ses_proj_04
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_access
  artifact_instance_id: art_proj_log_a
  contributor_references:
  - actor_kind: core_student
    actor_id: stu_001
    owning_system: core
    display_label_snapshot: Student 001
  location:
    scheme: file
    locator: attachments/attach_proj_keyboard_demo_a.png
    version_label: Build 4
    content_digest: synthetic_digest_keyboard_demo_a
    display_label: Keyboard focus-state screenshot
  version_label: Build 4
  availability_status: available
  review_status: reviewed
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:25:00-05:00'
    source_kind: imported
    note: Screenshot attached after accessibility test Review.
- record_owner: concord
  record_kind: attachment
  attachment_id: attach_proj_display_wiring_b
  activity_id: act_proj_resource_finder_01
  attachment_type: project_diagram
  title: Group B Physical Display Wiring Diagram
  session_id: ses_proj_05
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_release
  activity_event_id: event_proj_release_handoff_01
  artifact_instance_id: art_proj_review_b
  contributor_references:
  - actor_kind: core_student
    actor_id: stu_006
    owning_system: core
    display_label_snapshot: Student 006
  - actor_kind: core_student
    actor_id: stu_004
    owning_system: core
    display_label_snapshot: Student 004
  location:
    scheme: physical_location
    locator: project-bin-b/wiring-diagram
    version_label: Release candidate
    display_label: Printed wiring diagram in Group B project bin
    access_hint: Teacher-controlled classroom storage.
  version_label: Release candidate
  availability_status: available
  review_status: reviewed
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:30:00-05:00'
    source_kind: manual
    note: Physical wiring diagram registered as an Attachment.
```

Attachments represent project evidence that is not a normal Concord-generated Artifact Page. File possession and physical storage do not establish authorship.

### 13.2 External References
```yaml
external_references:
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_repo_a_v1
  owning_system: github
  external_record_kind: repository
  external_record_id: synthetic_repo_resource_finder_a
  contract_version: '1'
  relationship_purpose: supporting_evidence
  activity_id: act_proj_resource_finder_01
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_integration_v1
  external_locator:
    scheme: git
    locator: github:synthetic-org/resource-finder-a
    version_label: Integration checkpoint
    display_label: Group A source repository
  display_label: Group A source repository — initial relationship
  availability_status: temporarily_unavailable
  last_confirmed_at: '2026-11-04T08:30:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-04T08:35:00-05:00'
    source_kind: manual
    note: Repository relationship recorded during external outage.
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_repo_a_v2
  owning_system: github
  external_record_kind: repository
  external_record_id: synthetic_repo_resource_finder_a
  contract_version: '1'
  relationship_purpose: supporting_evidence
  activity_id: act_proj_resource_finder_01
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_integration_v2
  external_locator:
    scheme: git
    locator: github:synthetic-org/resource-finder-a
    version_label: Recovered integration history
    display_label: Group A source repository
  display_label: Group A source repository — restored relationship
  availability_status: available
  last_confirmed_at: '2026-11-05T08:15:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-05T08:20:00-05:00'
    source_kind: manual
    note: Replacement External Reference created after availability returned.
  supersedes_external_reference_id: extref_proj_repo_a_v1
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_commit_001
  owning_system: github
  external_record_kind: repository_commit
  external_record_id: synthetic_commit_keyboard_navigation_001
  contract_version: '1'
  relationship_purpose: score_evidence
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_04
  group_id: grp_proj_a
  work_item_id: workitem_proj_a_access
  criterion_id: crit_proj_testing_debugging
  subject_reference:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  external_locator:
    scheme: git
    locator: github:synthetic-org/resource-finder-a@synthetic_commit_keyboard_navigation_001
    version_label: Build 4
    content_digest: synthetic_git_digest_keyboard_001
    display_label: Keyboard-navigation commit
  display_label: Student 001 keyboard-navigation commit
  availability_status: available
  last_confirmed_at: '2026-11-06T09:00:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T09:05:00-05:00'
    source_kind: manual
    note: Stable external commit reference created for evidence use.
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_pr_005
  owning_system: github
  external_record_kind: pull_request
  external_record_id: synthetic_pr_tests_005
  contract_version: '1'
  relationship_purpose: score_evidence
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_04
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_tests
  criterion_id: crit_proj_testing_debugging
  subject_reference:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  external_locator:
    scheme: git
    locator: github:synthetic-org/resource-finder-b/pull/5
    version_label: Merged test-suite revision
    content_digest: synthetic_git_digest_pr_005
    display_label: Group B test pull request
  display_label: Student 005 test-suite pull request
  availability_status: available
  last_confirmed_at: '2026-11-09T09:15:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:20:00-05:00'
    source_kind: manual
    note: Pull-request history referenced after contribution Review.
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_ci_b
  owning_system: github
  external_record_kind: ci_run
  external_record_id: synthetic_ci_run_b_release
  contract_version: '1'
  relationship_purpose: supporting_evidence
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_release
  criterion_id: crit_proj_testing_debugging
  external_locator:
    scheme: https
    locator: https://example.invalid/synthetic-ci/group-b-release
    version_label: Release candidate
    display_label: Group B release CI run
  display_label: Group B automated test run
  availability_status: available
  last_confirmed_at: '2026-11-09T09:25:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:27:00-05:00'
    source_kind: manual
    note: External automated-test result referenced without copying it.
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_cad_b
  owning_system: cad_platform
  external_record_kind: cad_model
  external_record_id: synthetic_cad_display_enclosure_b
  contract_version: '1'
  relationship_purpose: related_assignment
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  group_id: grp_proj_b
  work_item_id: workitem_proj_b_release
  external_locator:
    scheme: cloud_document
    locator: cad-platform:synthetic_cad_display_enclosure_b
    version_label: Revision 3
    content_digest: synthetic_cad_digest_b_r3
    display_label: Group B display enclosure model
  display_label: Group B CAD enclosure
  availability_status: available
  last_confirmed_at: '2026-11-09T09:28:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:29:00-05:00'
    source_kind: manual
    note: External CAD relationship recorded; CAD authority remains external.
- record_owner: concord
  record_kind: external_reference
  external_reference_id: extref_proj_design_doc
  owning_system: cloud_document_platform
  external_record_kind: design_document
  external_record_id: synthetic_design_doc_shared
  contract_version: '1'
  relationship_purpose: supporting_evidence
  activity_id: act_proj_resource_finder_01
  work_item_id: workitem_proj_requirements
  external_locator:
    scheme: cloud_document
    locator: cloud-doc:synthetic_design_doc_shared
    version_label: Final project plan
    content_digest: synthetic_cloud_digest_design_doc
    display_label: Shared design requirements document
  display_label: Shared requirements and architecture document
  availability_status: available
  last_confirmed_at: '2026-11-09T09:30:00-05:00'
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T09:31:00-05:00'
    source_kind: manual
    note: Shared design document referenced without treating account ownership as authorship.
```

The initial unavailable Group A repository relationship is superseded by an available relationship after service recovery. The external repository itself is not copied or mutated by Concord.

External records may contextualize or support a Concord judgment only through explicit Score Evidence Links. Commit authorship metadata and account ownership are evidence inputs, not automatic Concord authorship or performance determinations.

## 14. Criteria and Scoring Scales

### 14.1 Mixed Criterion Set Revision
```yaml
record_owner: concord
record_kind: criterion_set
criterion_set_id: critset_proj_mixed_rev_1
lineage_id: critset_proj_mixed
name: Collaborative Software Project Mixed Criteria
purpose: Define separate direct standards judgments for iterative development and testing plus a local
  collaboration-and-handoff judgment.
revision: 1
scope: activity_specific
criterion_set_kind: mixed
standards_profile_id: profile_njsls_cs_2023_hs
criterion_ids:
- crit_proj_iterative_development
- crit_proj_testing_debugging
- crit_proj_collaborative_handoff
status: active
created_provenance:
  actor:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  timestamp: '2026-10-30T13:30:00-04:00'
  source_kind: manual
  note: Immutable mixed Criterion Set revision created.
```

### 14.2 Criteria

```yaml
criteria:
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_proj_iterative_development
  criterion_set_id: critset_proj_mixed_rev_1
  key: iterative_development
  label: Develops through purposeful iteration
  definition: Plans, implements, evaluates, and revises a computing solution through traceable iterations
    responsive to evidence and constraints.
  criterion_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_4
  supported_target_kinds:
  - core_student
  - concord_group
  default_scoring_scale_id: scale_proj_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T13:35:00-04:00'
    source_kind: manual
    note: Standard-backed iterative-development Criterion created.
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_proj_testing_debugging
  criterion_set_id: critset_proj_mixed_rev_1
  key: testing_debugging
  label: Tests and debugs systematically
  definition: Designs meaningful tests, interprets failures, isolates causes, and verifies revisions against
    stated requirements.
  criterion_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_6
  supported_target_kinds:
  - core_student
  - concord_group
  default_scoring_scale_id: scale_proj_proficiency_4_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T13:36:00-04:00'
    source_kind: manual
    note: Standard-backed testing-and-debugging Criterion created.
- record_owner: concord
  record_kind: criterion
  criterion_id: crit_proj_collaborative_handoff
  criterion_set_id: critset_proj_mixed_rev_1
  key: collaborative_handoff
  label: Maintains a usable collaborative handoff
  definition: Keeps responsibilities, decisions, limitations, and next steps sufficiently explicit that
    collaborators can continue or review the work.
  criterion_kind: local
  alignment_standard_ids:
  - std_njsls_cs_8_1_12_ap_4
  supported_target_kinds:
  - core_student
  - concord_group
  default_scoring_scale_id: scale_proj_process_3_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T13:37:00-04:00'
    source_kind: manual
    note: Local collaboration-and-handoff Criterion created with non-governing alignment.
```

Each standard-backed Criterion governs exactly one Focus Standard. The local collaborative-handoff Criterion has no governing `standard_id`; its alignment is non-governing and cannot become a direct standards result.

### 14.3 Scoring Scale Revisions
```yaml
scoring_scales:
- record_owner: concord
  record_kind: scoring_scale
  scoring_scale_id: scale_proj_proficiency_4_rev_1
  lineage_id: scale_proj_proficiency_4
  name: Project Standards Proficiency Scale
  revision: 1
  scale_type: ordinal
  levels:
  - value: developing
    label: Developing
    meaning: Evidence is substantially incomplete or inconsistent.
    order: 1
  - value: approaching
    label: Approaching
    meaning: Evidence demonstrates partial performance with important gaps.
    order: 2
  - value: meeting
    label: Meeting
    meaning: Evidence demonstrates the expected contextual performance.
    order: 3
  - value: exceeding
    label: Exceeding
    meaning: Evidence demonstrates sustained, adaptive, and well-explained performance.
    order: 4
  intended_use: standards_based
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T13:45:00-04:00'
    source_kind: manual
    note: Immutable standards Scoring Scale revision created.
- record_owner: concord
  record_kind: scoring_scale
  scoring_scale_id: scale_proj_process_3_rev_1
  lineage_id: scale_proj_process_3
  name: Collaborative Process and Handoff Scale
  revision: 1
  scale_type: ordinal
  levels:
  - value: limited
    label: Limited
    meaning: The handoff is incomplete or difficult for collaborators to use.
    order: 1
  - value: functional
    label: Functional
    meaning: The handoff communicates enough information for routine continuation.
    order: 2
  - value: effective
    label: Effective
    meaning: The handoff is clear, current, traceable, and supports efficient continuation or review.
    order: 3
  intended_use: local
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-10-30T13:46:00-04:00'
    source_kind: manual
    note: Immutable local-process Scoring Scale revision created.
```

The two Scoring Scales are not interchangeable merely because they are ordinal. Concord does not normalize, average, weight, or aggregate them.

## 15. Score Records
```yaml
score_records:
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_group_a_iterative
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  target_reference:
    target_kind: concord_group
    target_id: grp_proj_a
    owning_system: concord
  criterion_id: crit_proj_iterative_development
  score_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_4
  scoring_scale_id: scale_proj_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-09T10:20:00-05:00'
  moderation_complete: true
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:20:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_group_b_iterative
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  target_reference:
    target_kind: concord_group
    target_id: grp_proj_b
    owning_system: concord
  criterion_id: crit_proj_iterative_development
  score_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_4
  scoring_scale_id: scale_proj_proficiency_4_rev_1
  disposition: scored
  value: exceeding
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-09T10:22:00-05:00'
  moderation_complete: true
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:22:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_group_a_handoff
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  target_reference:
    target_kind: concord_group
    target_id: grp_proj_a
    owning_system: concord
  criterion_id: crit_proj_collaborative_handoff
  score_kind: local
  scoring_scale_id: scale_proj_process_3_rev_1
  disposition: scored
  value: effective
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-09T10:24:00-05:00'
  moderation_complete: true
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_a
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:24:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_001_testing
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_04
  target_reference:
    target_kind: core_student
    target_id: stu_001
    owning_system: core
  criterion_id: crit_proj_testing_debugging
  score_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_6
  scoring_scale_id: scale_proj_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-09T10:26:00-05:00'
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
    timestamp: '2026-11-09T10:26:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_005_testing_v1
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_04
  target_reference:
    target_kind: core_student
    target_id: stu_005
    owning_system: core
  criterion_id: crit_proj_testing_debugging
  score_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_6
  scoring_scale_id: scale_proj_proficiency_4_rev_1
  disposition: deferred
  basis: professional_judgment
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-06T10:20:00-05:00'
  rationale: A direct testing judgment is deferred while conflicting contribution claims and external
    test history remain under Review.
  status_reason:
    reason_code: contribution_evidence_disputed
    note: The available evidence does not yet support a fair individual testing judgment.
    recorded_by:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    recorded_at: '2026-11-06T10:20:00-05:00'
    related_record:
      record_kind: moderation_record
      record_id: mod_proj_claim_005_v1
  moderation_complete: false
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_005
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-06T10:20:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_005_testing_v2
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  target_reference:
    target_kind: core_student
    target_id: stu_005
    owning_system: core
  criterion_id: crit_proj_testing_debugging
  score_kind: standard_backed
  standard_id: std_njsls_cs_8_1_12_ap_6
  scoring_scale_id: scale_proj_proficiency_4_rev_1
  disposition: scored
  value: meeting
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-09T12:00:00-05:00'
  rationale: Reviewed repository history, the corrected bounded Contribution Claim, automated tests, and
    teacher observation support the individual judgment.
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_005
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:00:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
  supersedes_score_record_id: score_proj_005_testing_v1
- record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_004_handoff
  activity_id: act_proj_resource_finder_01
  session_id: ses_proj_05
  target_reference:
    target_kind: core_student
    target_id: stu_004
    owning_system: core
  criterion_id: crit_proj_collaborative_handoff
  score_kind: local
  scoring_scale_id: scale_proj_process_3_rev_1
  disposition: scored
  value: effective
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-09T10:32:00-05:00'
  moderation_complete: true
  privacy_policy:
    classification: teacher_and_subjects
    audience_references:
    - participant_kind: core_student
      participant_id: stu_004
      owning_system: core
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:32:00-05:00'
    source_kind: manual
    note: Teacher recorded the canonical Concord Score.
```

Key distinctions:

- Group standards Scores remain Group judgments and do not populate member Scores.
- Local Scores remain valid Concord judgments but are not direct standards results.
- Student 005’s initial `deferred` record contains no value.
- The later Student 005 Score supersedes the deferred record without rewriting it.
- Group Membership, Role, Responsibility, Work Item status, repository ownership, and commit identity do not generate Scores.

## 16. Score Evidence Links
```yaml
score_evidence_links:
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_a_iter_plan
  score_record_id: score_proj_group_a_iterative
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_plan_a
  evidence_locator:
    page_number: 1
    note: Requirements and architecture sections.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  relevance_description: The planning canvas establishes the initial requirements, architecture, and iteration
    plan.
  significance: contextual
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:20:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_a_iter_log
  score_record_id: score_proj_group_a_iterative
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_log_a
  evidence_locator:
    page_number: 1
    activity_marker_id: marker_proj_integration
    note: Build and revision sequence.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  relevance_description: The Group log records planned builds, failed integration, recovery, and revised
    accessibility work.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:20:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_a_iter_tracker
  score_record_id: score_proj_group_a_iterative
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Group A iteration observations.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  relevance_description: Teacher observations document Group A adapting its plan after the source-control
    interruption and reassignment.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:21:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_a_iter_repo
  score_record_id: score_proj_group_a_iterative
  evidence_reference:
    evidence_kind: external_record
    owning_system: concord
    record_id: extref_proj_repo_a_v2
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  relevance_description: The restored repository history corroborates distinct revisions without transferring
    repository ownership to Concord.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:21:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_b_iter_plan
  score_record_id: score_proj_group_b_iterative
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_plan_b
  evidence_locator:
    page_number: 1
    note: Requirements and architecture sections.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  relevance_description: The planning canvas defines Group B's requirements and initial architecture.
  significance: contextual
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:22:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_b_iter_log
  score_record_id: score_proj_group_b_iterative
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_log_b
  evidence_locator:
    page_number: 1
    note: Iterations 2 through 5.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  relevance_description: The iteration log records multiple test-informed revisions and a resolved accessibility
    regression.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:22:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_b_iter_review
  score_record_id: score_proj_group_b_iterative
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_review_b
  evidence_locator:
    page_number: 1
    note: Revision rationale and known limitations.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_b
    owning_system: concord
  relevance_description: The final design review explains how Group B revised architecture and testing
    after failures.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:23:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_a_handoff_review
  score_record_id: score_proj_group_a_handoff
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_review_a
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  relevance_description: The design review provides current architecture, known limitations, and next-step
    guidance.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:24:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_a_handoff_tracker
  score_record_id: score_proj_group_a_handoff
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Handoff and reassignment observations.
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_a
    owning_system: concord
  relevance_description: Teacher observation confirms that Group A used the handoff to coordinate reassigned
    testing and integration responsibilities.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:24:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_001_commit
  score_record_id: score_proj_001_testing
  evidence_reference:
    evidence_kind: external_record
    owning_system: concord
    record_id: extref_proj_commit_001
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  relevance_description: The external commit identifies a bounded keyboard-navigation implementation and
    associated tests.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:26:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_001_log
  score_record_id: score_proj_001_testing
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_log_a
  evidence_locator:
    page_number: 1
    work_item_id: workitem_proj_a_access
    note: Keyboard-accessibility test cycle.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  relevance_description: The Group log attributes the keyboard-navigation test cycle to Student 001 and
    records the defect verification.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:26:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_001_screenshot
  score_record_id: score_proj_001_testing
  evidence_reference:
    evidence_kind: attachment
    owning_system: concord
    record_id: attach_proj_keyboard_demo_a
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  relevance_description: The reviewed screenshot documents the tested focus behavior.
  significance: contextual
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:27:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_001_tracker
  score_record_id: score_proj_001_testing
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Student 001 testing observation.
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  relevance_description: Teacher observation records Student 001 reproducing, isolating, and verifying
    the keyboard-accessibility defect.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:27:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_001_claim
  score_record_id: score_proj_001_testing
  evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_001_keyboard
  subject_context:
    subject_kind: core_student
    subject_id: stu_001
    owning_system: core
  relevance_description: The moderated bounded self-claim corroborates the specific implementation and
    testing contribution.
  significance: corroborating
  moderation_record_id: mod_proj_claim_001
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:28:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_005_pr
  score_record_id: score_proj_005_testing_v2
  evidence_reference:
    evidence_kind: external_record
    owning_system: concord
    record_id: extref_proj_pr_005
  subject_context:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  relevance_description: The pull-request history identifies Student 005's test matrix, automated tests,
    revisions, and review discussion.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:00:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_005_ci
  score_record_id: score_proj_005_testing_v2
  evidence_reference:
    evidence_kind: external_record
    owning_system: concord
    record_id: extref_proj_ci_b
  subject_context:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  relevance_description: The external CI result confirms that the revised test suite executed successfully
    against the release candidate.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:00:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_005_log
  score_record_id: score_proj_005_testing_v2
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_log_b
  evidence_locator:
    page_number: 1
    work_item_id: workitem_proj_b_tests
    note: Test matrix and debugging entries.
  subject_context:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  relevance_description: The Group log records Student 005 designing the test matrix and debugging failed
    integration cases.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:01:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_005_tracker
  score_record_id: score_proj_005_testing_v2
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_teacher_tracker
  evidence_locator:
    page_number: 1
    note: Student 005 testing observations.
  subject_context:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  relevance_description: Teacher observation distinguishes Student 005's testing work from contributions
    by Students 003 and 004.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:01:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_005_claim_v2
  score_record_id: score_proj_005_testing_v2
  evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_005_tests_v2
  subject_context:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  relevance_description: The corrected moderated claim states a bounded contribution consistent with the
    external and teacher evidence.
  significance: corroborating
  moderation_record_id: mod_proj_claim_005_v2
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:02:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_005_peer_claim
  score_record_id: score_proj_005_testing_v2
  evidence_reference:
    evidence_kind: contribution_claim
    owning_system: concord
    record_id: claim_proj_004_about_005
  subject_context:
    subject_kind: core_student
    subject_id: stu_005
    owning_system: core
  relevance_description: The qualified peer claim corroborates substantial testing leadership but is not
    used to support sole authorship.
  significance: qualifying
  moderation_record_id: mod_proj_claim_004_about_005
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T12:02:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_004_handoff_reflection
  score_record_id: score_proj_004_handoff
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_reflection_004
  subject_context:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  relevance_description: The reflection identifies acceptance criteria, collaborator dependencies, and
    release limitations communicated by Student 004.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:32:00-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
- record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_004_handoff_review
  score_record_id: score_proj_004_handoff
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_review_b
  evidence_locator:
    page_number: 1
    note: Product acceptance and release-handoff sections.
  subject_context:
    subject_kind: core_student
    subject_id: stu_004
    owning_system: core
  relevance_description: The Group B handoff records Student 004's product-owner decisions and acceptance-case
    contributions.
  significance: corroborating
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-09T10:32:30-05:00'
    source_kind: manual
    note: Teacher deliberately linked this evidence source to the Score.
```

The links demonstrate both directions of the many-to-many evidence relationship:

- one Score may use several sources;
- one source, such as the teacher tracker or Group log, may support several separate Scores;
- Group and multi-Subject evidence supports an individual Score only through explicit Subject context, locator detail, and teacher judgment;
- moderated Contribution Claims include the applicable Moderation Record;
- and external evidence is referenced rather than copied.

The disputed Student 005 v1 Claim does not remain an active supporting link for the consequential replacement Score.

## 17. Core Academic Work Registration

The primary project Activity is registered explicitly. Registration does not follow automatically from Activity creation, standards selection, PDS2 routing, or Score existence.

```yaml
academic_work_registrations:
- record_owner: core
  record_kind: academic_work_registration
  schema_version: '1'
  record_type: academic_work_registration
  work:
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
  registration_revision: 1
  producer_contract_version: concord_activity_v1
  title: Accessible Community Resource Finder
  work_kind: collaborative_activity
  academic_intent: summative
  lifecycle: active
  created_at: '2026-10-30T14:21:00-04:00'
  updated_at: '2026-10-30T14:21:00-04:00'
  source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_proj_resource_finder_01
    contract_version: '1'
- record_owner: core
  record_kind: academic_work_registration
  schema_version: '1'
  record_type: academic_work_registration
  work:
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_resource_finder_01
  registration_revision: 2
  producer_contract_version: concord_activity_v1
  title: Accessible Community Resource Finder
  work_kind: collaborative_activity
  academic_intent: summative
  lifecycle: closed
  created_at: '2026-10-30T14:21:00-04:00'
  updated_at: '2026-11-09T12:08:00-05:00'
  source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_proj_resource_finder_01
    contract_version: '1'
```

Revision 1 records the active summative work. Revision 2 closes the registration after the native scoring state needed for publication is complete.

The Core fields do not duplicate Concord's Activity contract:

- `scoring_orientation: mixed` remains Concord-owned;
- `academic_intent: summative` remains Core-owned;
- `work_kind: collaborative_activity` classifies the registered work for suite integration;
- and the registration says nothing about Grade eligibility or Academic Period membership.

## 18. Concord Academic Result Manifest Revision 1

Manifest revision 1 captures the first complete publishable state. It includes:

- two Group standards Scores;
- one individual standards Score for Student 001;
- Student 005's current `deferred` standards judgment;
- two local handoff Scores;
- exact Criterion and Scoring Scale semantics;
- external repository and project-system lineage;
- all consequential Score Evidence Links then in effect;
- and applicable Moderation state.

The local Scores appear in the broader Score projection but not in the nested Standards Result Projection.

The exact published bytes are:

```json
{
  "activity_context": {
    "activity_id": "act_proj_resource_finder_01",
    "activity_status_snapshot": "completed",
    "activity_type": "local:collaborative_software_engineering_project",
    "class_id": "cls_apcsp_p01",
    "focus_standard_ids": [
      "std_njsls_cs_8_1_12_ap_4",
      "std_njsls_cs_8_1_12_ap_6"
    ],
    "scoring_orientation": "mixed",
    "session_references": [
      {
        "record_id": "ses_proj_01",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_02",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_03",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_04",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_05",
        "record_kind": "session"
      }
    ],
    "standards_profile_id": "profile_njsls_cs_2023_hs",
    "title_snapshot": "Accessible Community Resource Finder"
  },
  "criterion_projections": [
    {
      "criterion_id": "crit_proj_iterative_development",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_proj_mixed_rev_1",
      "definition": "Plans, implements, evaluates, and revises a computing solution through traceable iterations responsive to evidence and constraints.",
      "key": "iterative_development",
      "label": "Develops through purposeful iteration",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student",
        "concord_group"
      ]
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_proj_mixed_rev_1",
      "definition": "Designs meaningful tests, interprets failures, isolates causes, and verifies revisions against stated requirements.",
      "key": "testing_debugging",
      "label": "Tests and debugs systematically",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student",
        "concord_group"
      ]
    },
    {
      "alignment_standard_ids": [
        "std_njsls_cs_8_1_12_ap_4"
      ],
      "criterion_id": "crit_proj_collaborative_handoff",
      "criterion_kind": "local",
      "criterion_set_id": "critset_proj_mixed_rev_1",
      "definition": "Keeps responsibilities, decisions, limitations, and next steps sufficiently explicit that collaborators can continue or review the work.",
      "key": "collaborative_handoff",
      "label": "Maintains a usable collaborative handoff",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student",
        "concord_group"
      ]
    }
  ],
  "generated_at": "2026-11-09T10:45:00-05:00",
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
    "timestamp": "2026-11-09T10:45:00-05:00"
  },
  "manifest_contract_version": "concord_academic_result_manifest_v1",
  "moderation_projections": [
    {
      "moderated_at": "2026-11-06T10:00:00-05:00",
      "moderation_record_id": "mod_proj_claim_001",
      "permitted_use": "may_support_one_named_subject",
      "privacy_classification": "teacher_and_subjects",
      "rationale": "The Group log, repository commit, teacher observation, and Work Item history consistently support the bounded keyboard-accessibility claim.",
      "status": "accepted",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_001_keyboard",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 001",
          "owning_system": "core",
          "record_id": "stu_001",
          "record_kind": "student"
        }
      ]
    },
    {
      "moderated_at": "2026-11-06T10:05:00-05:00",
      "moderation_record_id": "mod_proj_claim_004_about_005",
      "permitted_use": "may_corroborate_teacher_evidence",
      "privacy_classification": "teacher_restricted",
      "rationale": "External history shows substantial Student 005 work plus meaningful acceptance-case and regression-test contributions by other students.",
      "status": "accepted_with_qualification",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_004_about_005",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 005",
          "owning_system": "core",
          "record_id": "stu_005",
          "record_kind": "student"
        }
      ]
    },
    {
      "moderated_at": "2026-11-06T10:10:00-05:00",
      "moderation_record_id": "mod_proj_claim_005_v1",
      "permitted_use": "may_not_be_used_for_scoring",
      "privacy_classification": "teacher_restricted",
      "rationale": "The sole-authorship statement conflicts with the pull-request discussion, test history, teacher observation, and Student 004's acceptance-case contribution.",
      "status": "disputed",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_005_tests_v1",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 005",
          "owning_system": "core",
          "record_id": "stu_005",
          "record_kind": "student"
        },
        {
          "display_label": "Student 004",
          "owning_system": "core",
          "record_id": "stu_004",
          "record_kind": "student"
        },
        {
          "display_label": "Student 003",
          "owning_system": "core",
          "record_id": "stu_003",
          "record_kind": "student"
        }
      ]
    },
    {
      "moderated_at": "2026-11-09T10:00:00-05:00",
      "moderation_record_id": "mod_proj_claim_005_v2",
      "permitted_use": "may_support_one_named_subject",
      "privacy_classification": "teacher_and_subjects",
      "rationale": "The corrected claim matches the external pull request, test matrix, teacher tracker, and Group B design review.",
      "status": "accepted",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_005_tests_v2",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 005",
          "owning_system": "core",
          "record_id": "stu_005",
          "record_kind": "student"
        }
      ]
    }
  ],
  "privacy_classification": "teacher_restricted",
  "producer_module_id": "concord",
  "record_kind": "concord_academic_result_manifest",
  "record_owner": "concord",
  "record_set_id": "rs_proj_resource_finder_01",
  "record_set_revision": 1,
  "score_evidence_link_projections": [
    {
      "evidence_locator": {
        "note": "Requirements and architecture sections.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_plan_a"
      },
      "relevance_description": "The planning canvas establishes the initial requirements, architecture, and iteration plan.",
      "score_evidence_link_id": "scoreev_proj_a_iter_plan",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_proj_plan_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "activity_marker_id": "marker_proj_integration",
        "note": "Build and revision sequence.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_a"
      },
      "relevance_description": "The Group log records planned builds, failed integration, recovery, and revised accessibility work.",
      "score_evidence_link_id": "scoreev_proj_a_iter_log",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_log_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Group A iteration observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observations document Group A adapting its plan after the source-control interruption and reassignment.",
      "score_evidence_link_id": "scoreev_proj_a_iter_tracker",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_proj_repo_a_v2"
      },
      "relevance_description": "The restored repository history corroborates distinct revisions without transferring repository ownership to Concord.",
      "score_evidence_link_id": "scoreev_proj_a_iter_repo",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "corroborating",
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      },
      "underlying_source_lineage": {
        "contract_version": "1",
        "external_locator": {
          "display_label": "Group A source repository",
          "locator": "github:synthetic-org/resource-finder-a",
          "scheme": "git",
          "version_label": "Recovered integration history"
        },
        "external_record_id": "synthetic_repo_resource_finder_a",
        "external_record_kind": "repository",
        "owning_system": "github"
      }
    },
    {
      "evidence_locator": {
        "note": "Requirements and architecture sections.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_plan_b"
      },
      "relevance_description": "The planning canvas defines Group B's requirements and initial architecture.",
      "score_evidence_link_id": "scoreev_proj_b_iter_plan",
      "score_record_id": "score_proj_group_b_iterative",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_proj_plan_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_b",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Iterations 2 through 5.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_b"
      },
      "relevance_description": "The iteration log records multiple test-informed revisions and a resolved accessibility regression.",
      "score_evidence_link_id": "scoreev_proj_b_iter_log",
      "score_record_id": "score_proj_group_b_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_log_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_b",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Revision rationale and known limitations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_review_b"
      },
      "relevance_description": "The final design review explains how Group B revised architecture and testing after failures.",
      "score_evidence_link_id": "scoreev_proj_b_iter_review",
      "score_record_id": "score_proj_group_b_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_review_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_b",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_review_a"
      },
      "relevance_description": "The design review provides current architecture, known limitations, and next-step guidance.",
      "score_evidence_link_id": "scoreev_proj_a_handoff_review",
      "score_record_id": "score_proj_group_a_handoff",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_review_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Handoff and reassignment observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observation confirms that Group A used the handoff to coordinate reassigned testing and integration responsibilities.",
      "score_evidence_link_id": "scoreev_proj_a_handoff_tracker",
      "score_record_id": "score_proj_group_a_handoff",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_proj_commit_001"
      },
      "relevance_description": "The external commit identifies a bounded keyboard-navigation implementation and associated tests.",
      "score_evidence_link_id": "scoreev_proj_001_commit",
      "score_record_id": "score_proj_001_testing",
      "significance": "primary",
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      },
      "underlying_source_lineage": {
        "contract_version": "1",
        "external_locator": {
          "content_digest": "synthetic_git_digest_keyboard_001",
          "display_label": "Keyboard-navigation commit",
          "locator": "github:synthetic-org/resource-finder-a@synthetic_commit_keyboard_navigation_001",
          "scheme": "git",
          "version_label": "Build 4"
        },
        "external_record_id": "synthetic_commit_keyboard_navigation_001",
        "external_record_kind": "repository_commit",
        "owning_system": "github"
      }
    },
    {
      "evidence_locator": {
        "note": "Keyboard-accessibility test cycle.",
        "page_number": 1,
        "work_item_id": "workitem_proj_a_access"
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_a"
      },
      "relevance_description": "The Group log attributes the keyboard-navigation test cycle to Student 001 and records the defect verification.",
      "score_evidence_link_id": "scoreev_proj_001_log",
      "score_record_id": "score_proj_001_testing",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_proj_log_a",
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
      "evidence_reference": {
        "evidence_kind": "attachment",
        "owning_system": "concord",
        "record_id": "attach_proj_keyboard_demo_a"
      },
      "relevance_description": "The reviewed screenshot documents the tested focus behavior.",
      "score_evidence_link_id": "scoreev_proj_001_screenshot",
      "score_record_id": "score_proj_001_testing",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "attach_proj_keyboard_demo_a",
        "record_kind": "attachment"
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
        "note": "Student 001 testing observation.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observation records Student 001 reproducing, isolating, and verifying the keyboard-accessibility defect.",
      "score_evidence_link_id": "scoreev_proj_001_tracker",
      "score_record_id": "score_proj_001_testing",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
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
      "evidence_reference": {
        "evidence_kind": "contribution_claim",
        "owning_system": "concord",
        "record_id": "claim_proj_001_keyboard"
      },
      "moderation_record_id": "mod_proj_claim_001",
      "relevance_description": "The moderated bounded self-claim corroborates the specific implementation and testing contribution.",
      "score_evidence_link_id": "scoreev_proj_001_claim",
      "score_record_id": "score_proj_001_testing",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "claim_proj_001_keyboard",
        "record_kind": "contribution_claim"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_reflection_004"
      },
      "relevance_description": "The reflection identifies acceptance criteria, collaborator dependencies, and release limitations communicated by Student 004.",
      "score_evidence_link_id": "scoreev_proj_004_handoff_reflection",
      "score_record_id": "score_proj_004_handoff",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_reflection_004",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_004",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Product acceptance and release-handoff sections.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_review_b"
      },
      "relevance_description": "The Group B handoff records Student 004's product-owner decisions and acceptance-case contributions.",
      "score_evidence_link_id": "scoreev_proj_004_handoff_review",
      "score_record_id": "score_proj_004_handoff",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_proj_review_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_004",
        "subject_kind": "core_student"
      }
    }
  ],
  "score_projections": [
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_group_a_iterative",
      "scored_at": "2026-11-09T10:20:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_05",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_a",
        "target_kind": "concord_group"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_group_b_iterative",
      "scored_at": "2026-11-09T10:22:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_05",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_b",
        "target_kind": "concord_group"
      },
      "value": "exceeding"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_collaborative_handoff",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "local",
      "score_record_id": "score_proj_group_a_handoff",
      "scored_at": "2026-11-09T10:24:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "session_id": "ses_proj_05",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_a",
        "target_kind": "concord_group"
      },
      "value": "effective"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_001_testing",
      "scored_at": "2026-11-09T10:26:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_04",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "professional_judgment",
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "deferred",
      "moderation_complete": false,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "A direct testing judgment is deferred while conflicting contribution claims and external test history remain under Review.",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_005_testing_v1",
      "scored_at": "2026-11-06T10:20:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_04",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_005",
        "target_kind": "core_student"
      }
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_collaborative_handoff",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "local",
      "score_record_id": "score_proj_004_handoff",
      "scored_at": "2026-11-09T10:32:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "session_id": "ses_proj_05",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_004",
        "target_kind": "core_student"
      },
      "value": "effective"
    }
  ],
  "scoring_scale_projections": [
    {
      "levels": [
        {
          "label": "Developing",
          "meaning": "Evidence is substantially incomplete or inconsistent.",
          "order": 1,
          "value": "developing"
        },
        {
          "label": "Approaching",
          "meaning": "Evidence demonstrates partial performance with important gaps.",
          "order": 2,
          "value": "approaching"
        },
        {
          "label": "Meeting",
          "meaning": "Evidence demonstrates the expected contextual performance.",
          "order": 3,
          "value": "meeting"
        },
        {
          "label": "Exceeding",
          "meaning": "Evidence demonstrates sustained, adaptive, and well-explained performance.",
          "order": 4,
          "value": "exceeding"
        }
      ],
      "lineage_id": "scale_proj_proficiency_4",
      "name": "Project Standards Proficiency Scale",
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "status_snapshot": "active"
    },
    {
      "levels": [
        {
          "label": "Limited",
          "meaning": "The handoff is incomplete or difficult for collaborators to use.",
          "order": 1,
          "value": "limited"
        },
        {
          "label": "Functional",
          "meaning": "The handoff communicates enough information for routine continuation.",
          "order": 2,
          "value": "functional"
        },
        {
          "label": "Effective",
          "meaning": "The handoff is clear, current, traceable, and supports efficient continuation or review.",
          "order": 3,
          "value": "effective"
        }
      ],
      "lineage_id": "scale_proj_process_3",
      "name": "Collaborative Process and Handoff Scale",
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "status_snapshot": "active"
    }
  ],
  "source_activity": {
    "contract_version": "1",
    "record_id": "act_proj_resource_finder_01",
    "record_kind": "activity"
  },
  "standards_result_projection": [
    {
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_group_a_iterative",
      "scored_at": "2026-11-09T10:20:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_a",
        "target_kind": "concord_group"
      },
      "value": "meeting"
    },
    {
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_group_b_iterative",
      "scored_at": "2026-11-09T10:22:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_b",
        "target_kind": "concord_group"
      },
      "value": "exceeding"
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_001_testing",
      "scored_at": "2026-11-09T10:26:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "deferred",
      "score_record_id": "score_proj_005_testing_v1",
      "scored_at": "2026-11-06T10:20:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_005",
        "target_kind": "core_student"
      }
    }
  ],
  "work": {
    "class_id": "cls_apcsp_p01",
    "module_id": "concord",
    "work_id": "act_proj_resource_finder_01"
  }
}
```

The exact SHA-256 digest of those UTF-8 bytes, including the final newline, is:

```text
df5c502efd3649e776dae771905be2e4d4330099c270fdb02cb2c47e4c8ec412
```

Manifest revision 1 is immutable after publication.

## 19. Core Publication Record Revision 1

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_concord_proj_resource_finder_001
work:
  module_id: concord
  class_id: cls_apcsp_p01
  work_id: act_proj_resource_finder_01
source_record:
  module_id: concord
  record_kind: activity
  record_id: act_proj_resource_finder_01
  contract_version: '1'
publication_kind: academic_result_set
capabilities:
- criterion_scores
- standards_ratings
- moderated_scores
record_set_id: rs_proj_resource_finder_01
record_set_revision: 1
manifest_contract_version: concord_academic_result_manifest_v1
manifest_path: classes/cls_apcsp_p01/modules/concord/work/act_proj_resource_finder_01/exports/manifests/rs_proj_resource_finder_01/1.json
manifest_digest_algorithm: sha256
manifest_digest: df5c502efd3649e776dae771905be2e4d4330099c270fdb02cb2c47e4c8ec412
published_at: '2026-11-09T11:00:00-05:00'
academic_work_registration_revision: 2
```

The capabilities are truthful:

- `criterion_scores` because the manifest contains criterion-level standard-backed and local Scores;
- `standards_ratings` because the manifest contains an explicit standards-only projection;
- and `moderated_scores` because consequential Score evidence includes moderated Contribution Claims.

The publication does not claim `points`, `question_evidence`, or `multiple_attempts`.

Core publication is idempotent for the same work, record-set ID, revision, path, and digest. A contradictory attempt to reuse revision 1 with different bytes or a different digest must fail.

The Core catalog is derived. Deleting or rebuilding the catalog does not delete the immutable manifest or Publication Record.

## 20. Native Score Revision and New Publication State

Student 005's first Score Record remains a valid historical `deferred` judgment. The later evidence does not edit it in place.

The replacement sequence is:

```text
additional reviewed and moderated evidence
    -> new native Score Record
    -> Correction Record linking the old and new judgments
    -> new immutable manifest revision
    -> new Core Publication Record
```

The replacement Score is recorded at `2026-11-09T12:00:00-05:00`. Its six Score Evidence Links are created at or after that time. The related Correction Record is recorded after the replacement exists.

Native Score supersession does not itself supersede a Core publication. Concord must generate and publish a new manifest revision.

## 21. Concord Academic Result Manifest Revision 2

Revision 2 preserves every result from revision 1 and adds Student 005's new scored judgment.

It marks:

- `score_proj_005_testing_v1` as superseded;
- `score_proj_005_testing_v2` as current;
- the first standards projection row as historical rather than deleted;
- and the six new evidence-lineage rows as deliberate support for the replacement Score.

The exact published bytes are:

```json
{
  "activity_context": {
    "activity_id": "act_proj_resource_finder_01",
    "activity_status_snapshot": "completed",
    "activity_type": "local:collaborative_software_engineering_project",
    "class_id": "cls_apcsp_p01",
    "focus_standard_ids": [
      "std_njsls_cs_8_1_12_ap_4",
      "std_njsls_cs_8_1_12_ap_6"
    ],
    "scoring_orientation": "mixed",
    "session_references": [
      {
        "record_id": "ses_proj_01",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_02",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_03",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_04",
        "record_kind": "session"
      },
      {
        "record_id": "ses_proj_05",
        "record_kind": "session"
      }
    ],
    "standards_profile_id": "profile_njsls_cs_2023_hs",
    "title_snapshot": "Accessible Community Resource Finder"
  },
  "criterion_projections": [
    {
      "criterion_id": "crit_proj_iterative_development",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_proj_mixed_rev_1",
      "definition": "Plans, implements, evaluates, and revises a computing solution through traceable iterations responsive to evidence and constraints.",
      "key": "iterative_development",
      "label": "Develops through purposeful iteration",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student",
        "concord_group"
      ]
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "criterion_kind": "standard_backed",
      "criterion_set_id": "critset_proj_mixed_rev_1",
      "definition": "Designs meaningful tests, interprets failures, isolates causes, and verifies revisions against stated requirements.",
      "key": "testing_debugging",
      "label": "Tests and debugs systematically",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student",
        "concord_group"
      ]
    },
    {
      "alignment_standard_ids": [
        "std_njsls_cs_8_1_12_ap_4"
      ],
      "criterion_id": "crit_proj_collaborative_handoff",
      "criterion_kind": "local",
      "criterion_set_id": "critset_proj_mixed_rev_1",
      "definition": "Keeps responsibilities, decisions, limitations, and next steps sufficiently explicit that collaborators can continue or review the work.",
      "key": "collaborative_handoff",
      "label": "Maintains a usable collaborative handoff",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "core_student",
        "concord_group"
      ]
    }
  ],
  "generated_at": "2026-11-09T12:10:00-05:00",
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
    "timestamp": "2026-11-09T12:10:00-05:00"
  },
  "manifest_contract_version": "concord_academic_result_manifest_v1",
  "moderation_projections": [
    {
      "moderated_at": "2026-11-06T10:00:00-05:00",
      "moderation_record_id": "mod_proj_claim_001",
      "permitted_use": "may_support_one_named_subject",
      "privacy_classification": "teacher_and_subjects",
      "rationale": "The Group log, repository commit, teacher observation, and Work Item history consistently support the bounded keyboard-accessibility claim.",
      "status": "accepted",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_001_keyboard",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 001",
          "owning_system": "core",
          "record_id": "stu_001",
          "record_kind": "student"
        }
      ]
    },
    {
      "moderated_at": "2026-11-06T10:05:00-05:00",
      "moderation_record_id": "mod_proj_claim_004_about_005",
      "permitted_use": "may_corroborate_teacher_evidence",
      "privacy_classification": "teacher_restricted",
      "rationale": "External history shows substantial Student 005 work plus meaningful acceptance-case and regression-test contributions by other students.",
      "status": "accepted_with_qualification",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_004_about_005",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 005",
          "owning_system": "core",
          "record_id": "stu_005",
          "record_kind": "student"
        }
      ]
    },
    {
      "moderated_at": "2026-11-06T10:10:00-05:00",
      "moderation_record_id": "mod_proj_claim_005_v1",
      "permitted_use": "may_not_be_used_for_scoring",
      "privacy_classification": "teacher_restricted",
      "rationale": "The sole-authorship statement conflicts with the pull-request discussion, test history, teacher observation, and Student 004's acceptance-case contribution.",
      "status": "disputed",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_005_tests_v1",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 005",
          "owning_system": "core",
          "record_id": "stu_005",
          "record_kind": "student"
        },
        {
          "display_label": "Student 004",
          "owning_system": "core",
          "record_id": "stu_004",
          "record_kind": "student"
        },
        {
          "display_label": "Student 003",
          "owning_system": "core",
          "record_id": "stu_003",
          "record_kind": "student"
        }
      ]
    },
    {
      "moderated_at": "2026-11-09T10:00:00-05:00",
      "moderation_record_id": "mod_proj_claim_005_v2",
      "permitted_use": "may_support_one_named_subject",
      "privacy_classification": "teacher_and_subjects",
      "rationale": "The corrected claim matches the external pull request, test matrix, teacher tracker, and Group B design review.",
      "status": "accepted",
      "target_evidence_reference": {
        "owning_system": "concord",
        "record_id": "claim_proj_005_tests_v2",
        "record_kind": "contribution_claim"
      },
      "target_subject_references": [
        {
          "display_label": "Student 005",
          "owning_system": "core",
          "record_id": "stu_005",
          "record_kind": "student"
        }
      ]
    }
  ],
  "privacy_classification": "teacher_restricted",
  "producer_module_id": "concord",
  "record_kind": "concord_academic_result_manifest",
  "record_owner": "concord",
  "record_set_id": "rs_proj_resource_finder_01",
  "record_set_revision": 2,
  "score_evidence_link_projections": [
    {
      "evidence_locator": {
        "note": "Requirements and architecture sections.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_plan_a"
      },
      "relevance_description": "The planning canvas establishes the initial requirements, architecture, and iteration plan.",
      "score_evidence_link_id": "scoreev_proj_a_iter_plan",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_proj_plan_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "activity_marker_id": "marker_proj_integration",
        "note": "Build and revision sequence.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_a"
      },
      "relevance_description": "The Group log records planned builds, failed integration, recovery, and revised accessibility work.",
      "score_evidence_link_id": "scoreev_proj_a_iter_log",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_log_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Group A iteration observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observations document Group A adapting its plan after the source-control interruption and reassignment.",
      "score_evidence_link_id": "scoreev_proj_a_iter_tracker",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_proj_repo_a_v2"
      },
      "relevance_description": "The restored repository history corroborates distinct revisions without transferring repository ownership to Concord.",
      "score_evidence_link_id": "scoreev_proj_a_iter_repo",
      "score_record_id": "score_proj_group_a_iterative",
      "significance": "corroborating",
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      },
      "underlying_source_lineage": {
        "contract_version": "1",
        "external_locator": {
          "display_label": "Group A source repository",
          "locator": "github:synthetic-org/resource-finder-a",
          "scheme": "git",
          "version_label": "Recovered integration history"
        },
        "external_record_id": "synthetic_repo_resource_finder_a",
        "external_record_kind": "repository",
        "owning_system": "github"
      }
    },
    {
      "evidence_locator": {
        "note": "Requirements and architecture sections.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_plan_b"
      },
      "relevance_description": "The planning canvas defines Group B's requirements and initial architecture.",
      "score_evidence_link_id": "scoreev_proj_b_iter_plan",
      "score_record_id": "score_proj_group_b_iterative",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "art_proj_plan_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_b",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Iterations 2 through 5.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_b"
      },
      "relevance_description": "The iteration log records multiple test-informed revisions and a resolved accessibility regression.",
      "score_evidence_link_id": "scoreev_proj_b_iter_log",
      "score_record_id": "score_proj_group_b_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_log_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_b",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Revision rationale and known limitations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_review_b"
      },
      "relevance_description": "The final design review explains how Group B revised architecture and testing after failures.",
      "score_evidence_link_id": "scoreev_proj_b_iter_review",
      "score_record_id": "score_proj_group_b_iterative",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_review_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_b",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_review_a"
      },
      "relevance_description": "The design review provides current architecture, known limitations, and next-step guidance.",
      "score_evidence_link_id": "scoreev_proj_a_handoff_review",
      "score_record_id": "score_proj_group_a_handoff",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_review_a",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_locator": {
        "note": "Handoff and reassignment observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observation confirms that Group A used the handoff to coordinate reassigned testing and integration responsibilities.",
      "score_evidence_link_id": "scoreev_proj_a_handoff_tracker",
      "score_record_id": "score_proj_group_a_handoff",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_a",
        "subject_kind": "concord_group"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_proj_commit_001"
      },
      "relevance_description": "The external commit identifies a bounded keyboard-navigation implementation and associated tests.",
      "score_evidence_link_id": "scoreev_proj_001_commit",
      "score_record_id": "score_proj_001_testing",
      "significance": "primary",
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      },
      "underlying_source_lineage": {
        "contract_version": "1",
        "external_locator": {
          "content_digest": "synthetic_git_digest_keyboard_001",
          "display_label": "Keyboard-navigation commit",
          "locator": "github:synthetic-org/resource-finder-a@synthetic_commit_keyboard_navigation_001",
          "scheme": "git",
          "version_label": "Build 4"
        },
        "external_record_id": "synthetic_commit_keyboard_navigation_001",
        "external_record_kind": "repository_commit",
        "owning_system": "github"
      }
    },
    {
      "evidence_locator": {
        "note": "Keyboard-accessibility test cycle.",
        "page_number": 1,
        "work_item_id": "workitem_proj_a_access"
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_a"
      },
      "relevance_description": "The Group log attributes the keyboard-navigation test cycle to Student 001 and records the defect verification.",
      "score_evidence_link_id": "scoreev_proj_001_log",
      "score_record_id": "score_proj_001_testing",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_proj_log_a",
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
      "evidence_reference": {
        "evidence_kind": "attachment",
        "owning_system": "concord",
        "record_id": "attach_proj_keyboard_demo_a"
      },
      "relevance_description": "The reviewed screenshot documents the tested focus behavior.",
      "score_evidence_link_id": "scoreev_proj_001_screenshot",
      "score_record_id": "score_proj_001_testing",
      "significance": "contextual",
      "source_record_reference": {
        "record_id": "attach_proj_keyboard_demo_a",
        "record_kind": "attachment"
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
        "note": "Student 001 testing observation.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observation records Student 001 reproducing, isolating, and verifying the keyboard-accessibility defect.",
      "score_evidence_link_id": "scoreev_proj_001_tracker",
      "score_record_id": "score_proj_001_testing",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
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
      "evidence_reference": {
        "evidence_kind": "contribution_claim",
        "owning_system": "concord",
        "record_id": "claim_proj_001_keyboard"
      },
      "moderation_record_id": "mod_proj_claim_001",
      "relevance_description": "The moderated bounded self-claim corroborates the specific implementation and testing contribution.",
      "score_evidence_link_id": "scoreev_proj_001_claim",
      "score_record_id": "score_proj_001_testing",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "claim_proj_001_keyboard",
        "record_kind": "contribution_claim"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_001",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_proj_pr_005"
      },
      "relevance_description": "The pull-request history identifies Student 005's test matrix, automated tests, revisions, and review discussion.",
      "score_evidence_link_id": "scoreev_proj_005_pr",
      "score_record_id": "score_proj_005_testing_v2",
      "significance": "primary",
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_005",
        "subject_kind": "core_student"
      },
      "underlying_source_lineage": {
        "contract_version": "1",
        "external_locator": {
          "content_digest": "synthetic_git_digest_pr_005",
          "display_label": "Group B test pull request",
          "locator": "github:synthetic-org/resource-finder-b/pull/5",
          "scheme": "git",
          "version_label": "Merged test-suite revision"
        },
        "external_record_id": "synthetic_pr_tests_005",
        "external_record_kind": "pull_request",
        "owning_system": "github"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "external_record",
        "owning_system": "concord",
        "record_id": "extref_proj_ci_b"
      },
      "relevance_description": "The external CI result confirms that the revised test suite executed successfully against the release candidate.",
      "score_evidence_link_id": "scoreev_proj_005_ci",
      "score_record_id": "score_proj_005_testing_v2",
      "significance": "corroborating",
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_005",
        "subject_kind": "core_student"
      },
      "underlying_source_lineage": {
        "contract_version": "1",
        "external_locator": {
          "display_label": "Group B release CI run",
          "locator": "https://example.invalid/synthetic-ci/group-b-release",
          "scheme": "https",
          "version_label": "Release candidate"
        },
        "external_record_id": "synthetic_ci_run_b_release",
        "external_record_kind": "ci_run",
        "owning_system": "github"
      }
    },
    {
      "evidence_locator": {
        "note": "Test matrix and debugging entries.",
        "page_number": 1,
        "work_item_id": "workitem_proj_b_tests"
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_log_b"
      },
      "relevance_description": "The Group log records Student 005 designing the test matrix and debugging failed integration cases.",
      "score_evidence_link_id": "scoreev_proj_005_log",
      "score_record_id": "score_proj_005_testing_v2",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_log_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_005",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Student 005 testing observations.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_teacher_tracker"
      },
      "relevance_description": "Teacher observation distinguishes Student 005's testing work from contributions by Students 003 and 004.",
      "score_evidence_link_id": "scoreev_proj_005_tracker",
      "score_record_id": "score_proj_005_testing_v2",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_teacher_tracker",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_005",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "contribution_claim",
        "owning_system": "concord",
        "record_id": "claim_proj_005_tests_v2"
      },
      "moderation_record_id": "mod_proj_claim_005_v2",
      "relevance_description": "The corrected moderated claim states a bounded contribution consistent with the external and teacher evidence.",
      "score_evidence_link_id": "scoreev_proj_005_claim_v2",
      "score_record_id": "score_proj_005_testing_v2",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "claim_proj_005_tests_v2",
        "record_kind": "contribution_claim"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_005",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "contribution_claim",
        "owning_system": "concord",
        "record_id": "claim_proj_004_about_005"
      },
      "moderation_record_id": "mod_proj_claim_004_about_005",
      "relevance_description": "The qualified peer claim corroborates substantial testing leadership but is not used to support sole authorship.",
      "score_evidence_link_id": "scoreev_proj_005_peer_claim",
      "score_record_id": "score_proj_005_testing_v2",
      "significance": "qualifying",
      "source_record_reference": {
        "record_id": "claim_proj_004_about_005",
        "record_kind": "contribution_claim"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_005",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_reflection_004"
      },
      "relevance_description": "The reflection identifies acceptance criteria, collaborator dependencies, and release limitations communicated by Student 004.",
      "score_evidence_link_id": "scoreev_proj_004_handoff_reflection",
      "score_record_id": "score_proj_004_handoff",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_reflection_004",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_004",
        "subject_kind": "core_student"
      }
    },
    {
      "evidence_locator": {
        "note": "Product acceptance and release-handoff sections.",
        "page_number": 1
      },
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_review_b"
      },
      "relevance_description": "The Group B handoff records Student 004's product-owner decisions and acceptance-case contributions.",
      "score_evidence_link_id": "scoreev_proj_004_handoff_review",
      "score_record_id": "score_proj_004_handoff",
      "significance": "corroborating",
      "source_record_reference": {
        "record_id": "art_proj_review_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "core",
        "subject_id": "stu_004",
        "subject_kind": "core_student"
      }
    }
  ],
  "score_projections": [
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_group_a_iterative",
      "scored_at": "2026-11-09T10:20:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_05",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_a",
        "target_kind": "concord_group"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_group_b_iterative",
      "scored_at": "2026-11-09T10:22:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_05",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_b",
        "target_kind": "concord_group"
      },
      "value": "exceeding"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_collaborative_handoff",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "local",
      "score_record_id": "score_proj_group_a_handoff",
      "scored_at": "2026-11-09T10:24:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "session_id": "ses_proj_05",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_a",
        "target_kind": "concord_group"
      },
      "value": "effective"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_001_testing",
      "scored_at": "2026-11-09T10:26:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_04",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "professional_judgment",
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "superseded",
      "disposition": "deferred",
      "moderation_complete": false,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "A direct testing judgment is deferred while conflicting contribution claims and external test history remain under Review.",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_005_testing_v1",
      "scored_at": "2026-11-06T10:20:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_04",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_005",
        "target_kind": "core_student"
      }
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_collaborative_handoff",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "score_kind": "local",
      "score_record_id": "score_proj_004_handoff",
      "scored_at": "2026-11-09T10:32:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "session_id": "ses_proj_05",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_004",
        "target_kind": "core_student"
      },
      "value": "effective"
    },
    {
      "activity_id": "act_proj_resource_finder_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "teacher_and_subjects",
      "rationale": "Reviewed repository history, the corrected bounded Contribution Claim, automated tests, and teacher observation support the individual judgment.",
      "score_kind": "standard_backed",
      "score_record_id": "score_proj_005_testing_v2",
      "scored_at": "2026-11-09T12:00:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "session_id": "ses_proj_05",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "supersedes_score_record_id": "score_proj_005_testing_v1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_005",
        "target_kind": "core_student"
      },
      "value": "meeting"
    }
  ],
  "scoring_scale_projections": [
    {
      "levels": [
        {
          "label": "Developing",
          "meaning": "Evidence is substantially incomplete or inconsistent.",
          "order": 1,
          "value": "developing"
        },
        {
          "label": "Approaching",
          "meaning": "Evidence demonstrates partial performance with important gaps.",
          "order": 2,
          "value": "approaching"
        },
        {
          "label": "Meeting",
          "meaning": "Evidence demonstrates the expected contextual performance.",
          "order": 3,
          "value": "meeting"
        },
        {
          "label": "Exceeding",
          "meaning": "Evidence demonstrates sustained, adaptive, and well-explained performance.",
          "order": 4,
          "value": "exceeding"
        }
      ],
      "lineage_id": "scale_proj_proficiency_4",
      "name": "Project Standards Proficiency Scale",
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "status_snapshot": "active"
    },
    {
      "levels": [
        {
          "label": "Limited",
          "meaning": "The handoff is incomplete or difficult for collaborators to use.",
          "order": 1,
          "value": "limited"
        },
        {
          "label": "Functional",
          "meaning": "The handoff communicates enough information for routine continuation.",
          "order": 2,
          "value": "functional"
        },
        {
          "label": "Effective",
          "meaning": "The handoff is clear, current, traceable, and supports efficient continuation or review.",
          "order": 3,
          "value": "effective"
        }
      ],
      "lineage_id": "scale_proj_process_3",
      "name": "Collaborative Process and Handoff Scale",
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "status_snapshot": "active"
    }
  ],
  "source_activity": {
    "contract_version": "1",
    "record_id": "act_proj_resource_finder_01",
    "record_kind": "activity"
  },
  "standards_result_projection": [
    {
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_group_a_iterative",
      "scored_at": "2026-11-09T10:20:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_a",
        "target_kind": "concord_group"
      },
      "value": "meeting"
    },
    {
      "criterion_id": "crit_proj_iterative_development",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_group_b_iterative",
      "scored_at": "2026-11-09T10:22:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_4",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_b",
        "target_kind": "concord_group"
      },
      "value": "exceeding"
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_001_testing",
      "scored_at": "2026-11-09T10:26:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_001",
        "target_kind": "core_student"
      },
      "value": "meeting"
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "superseded",
      "disposition": "deferred",
      "score_record_id": "score_proj_005_testing_v1",
      "scored_at": "2026-11-06T10:20:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_005",
        "target_kind": "core_student"
      }
    },
    {
      "criterion_id": "crit_proj_testing_debugging",
      "current_status": "current",
      "disposition": "scored",
      "score_record_id": "score_proj_005_testing_v2",
      "scored_at": "2026-11-09T12:00:00-05:00",
      "scoring_scale_id": "scale_proj_proficiency_4_rev_1",
      "standard_id": "std_njsls_cs_8_1_12_ap_6",
      "supersedes_score_record_id": "score_proj_005_testing_v1",
      "target_reference": {
        "owning_system": "core",
        "target_id": "stu_005",
        "target_kind": "core_student"
      },
      "value": "meeting"
    }
  ],
  "work": {
    "class_id": "cls_apcsp_p01",
    "module_id": "concord",
    "work_id": "act_proj_resource_finder_01"
  }
}
```

The exact SHA-256 digest of those UTF-8 bytes, including the final newline, is:

```text
dc64636d1f87ad8ec22a10df507d08403577e827997c75d7c20ab0aa6801f250
```

Manifest revision 2 is a new immutable object. It does not rewrite revision 1.

## 22. Core Publication Record Revision 2

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_concord_proj_resource_finder_002
work:
  module_id: concord
  class_id: cls_apcsp_p01
  work_id: act_proj_resource_finder_01
source_record:
  module_id: concord
  record_kind: activity
  record_id: act_proj_resource_finder_01
  contract_version: '1'
publication_kind: academic_result_set
capabilities:
- criterion_scores
- standards_ratings
- moderated_scores
record_set_id: rs_proj_resource_finder_01
record_set_revision: 2
manifest_contract_version: concord_academic_result_manifest_v1
manifest_path: classes/cls_apcsp_p01/modules/concord/work/act_proj_resource_finder_01/exports/manifests/rs_proj_resource_finder_01/2.json
manifest_digest_algorithm: sha256
manifest_digest: dc64636d1f87ad8ec22a10df507d08403577e827997c75d7c20ab0aa6801f250
published_at: '2026-11-09T12:20:00-05:00'
academic_work_registration_revision: 2
supersedes_publication_id: pub_concord_proj_resource_finder_001
```

The second Publication Record identifies the first publication through `supersedes_publication_id`.

Publication supersession means that revision 2 is the newer published view of the same record-set series. It does not erase:

- manifest revision 1;
- Publication Record revision 1;
- Student 005's deferred Score;
- the earlier Moderation history;
- or any downstream Meridian import based on the first publication.

A later withdrawal, if required, would be a separate Core-owned withdrawal record. Neither native correction nor publication supersession is a withdrawal.

## 23. Bounded Scoring-Orientation Addenda

### 23.1 Evidence-Only Project Exhibition Archive

This follow-up Activity routes, files, and Reviews a project-exhibition archive. It deliberately defines no standards profile, Focus Standards, Criteria, Scoring Scale selection, Score Records, or Standards Result Projection rows.

### Activity, Session, Group, and Membership
```yaml
activity:
  record_owner: concord
  record_kind: activity
  activity_id: act_proj_exhibition_archive_01
  class_reference:
    module_id: core
    record_kind: class
    record_id: cls_apcsp_p01
  title: Project Exhibition Evidence Archive
  activity_type: local:project_exhibition_archive
  description: A bounded follow-up Activity that routes, files, and Reviews exhibition evidence without
    creating Concord Scores.
  scoring_orientation: evidence_only
  status: completed
  privacy_policy:
    classification: classroom_shared
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:00:00-05:00'
    source_kind: manual
    note: Evidence-only follow-up Activity configured.
session:
  record_owner: concord
  record_kind: session
  session_id: ses_proj_exhibition_01
  activity_id: act_proj_exhibition_archive_01
  sequence: 1
  label: Project Exhibition Archive Session
  scheduled_start: '2026-11-12T08:05:00-05:00'
  scheduled_end: '2026-11-12T08:50:00-05:00'
  actual_start: '2026-11-12T08:05:00-05:00'
  actual_end: '2026-11-12T08:48:00-05:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:05:00-05:00'
    source_kind: manual
    note: Evidence-only Session configured.
group:
  record_owner: concord
  record_kind: group
  group_id: grp_proj_exhibition_combined
  activity_id: act_proj_exhibition_archive_01
  label: Combined Exhibition Team
  description: Activity-specific Group for exhibition evidence.
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:10:00-05:00'
    source_kind: manual
    note: Exhibition Group created.
group_memberships:
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_exhibition_001
  group_id: grp_proj_exhibition_combined
  participant_reference:
    participant_kind: core_student
    participant_id: stu_001
    owning_system: core
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:12:00-05:00'
    source_kind: manual
    note: Exhibition Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_exhibition_002
  group_id: grp_proj_exhibition_combined
  participant_reference:
    participant_kind: core_student
    participant_id: stu_002
    owning_system: core
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:12:00-05:00'
    source_kind: manual
    note: Exhibition Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_exhibition_003
  group_id: grp_proj_exhibition_combined
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:12:00-05:00'
    source_kind: manual
    note: Exhibition Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_exhibition_004
  group_id: grp_proj_exhibition_combined
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:12:00-05:00'
    source_kind: manual
    note: Exhibition Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_exhibition_005
  group_id: grp_proj_exhibition_combined
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:12:00-05:00'
    source_kind: manual
    note: Exhibition Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_exhibition_006
  group_id: grp_proj_exhibition_combined
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  effective_context:
    activity_id: act_proj_exhibition_archive_01
    session_ids:
    - ses_proj_exhibition_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:12:00-05:00'
    source_kind: manual
    note: Exhibition Membership created.
```

### Template, Artifact, Page, and Route

```yaml
template_definition:
  record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_exhibition_archive
  name: Project Exhibition Evidence Archive Sheet
  artifact_category: local:exhibition_archive
  purpose: Record exhibition stations, presented builds, and feedback artifacts for filing and Review.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:20:00-05:00'
    source_kind: manual
    note: Evidence-only Template Definition created.
template_version:
  record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_exhibition_archive_r1
  template_id: tmpl_proj_exhibition_archive
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_exhibition_archive_r1
  artifact_category: local:exhibition_archive
  page_manifest:
  - page_kind: primary
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: classroom_shared
  default_authorship_expectation:
    mode: local:teacher_author
  default_subject_expectation:
    mode: local:activity_group_and_session
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
    timestamp: '2026-11-10T14:25:00-05:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
artifact_instance:
  record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_exhibition_archive
  template_version_id: tmplv_proj_exhibition_archive_r1
  activity_id: act_proj_exhibition_archive_01
  session_id: ses_proj_exhibition_01
  artifact_category: local:exhibition_archive
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: classroom_shared
  page_ids:
  - page_proj_exhibition_archive_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-12T07:45:00-05:00'
    source_kind: generated
    note: Evidence-only archive Artifact generated.
artifact_page:
  record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_exhibition_archive_01
  artifact_instance_id: art_proj_exhibition_archive
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_exhibition_archive_01
  human_fallback: PR-EXHIBIT
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-12T07:45:10-05:00'
    source_kind: generated
    note: Evidence-only page identity created before rendering.
route_registration:
  owning_system: core
  record_kind: route_registration
  route_id: route_proj_exhibition_archive_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_exhibition_archive_01
    route_id: route_proj_exhibition_archive_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_exhibition_archive_01
  status: active
  registered_at: '2026-11-12T07:45:20-05:00'
```

### Author, Subjects, Scan, and Review

```yaml
artifact_author:
  record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_exhibition_teacher
  artifact_instance_id: art_proj_exhibition_archive
  author_reference:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  authorship_mode: teacher_author
  representation_status: not_applicable
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: classroom_shared
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-12T09:05:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
artifact_subjects:
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_exhibition_group
  artifact_instance_id: art_proj_exhibition_archive
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_exhibition_combined
    owning_system: concord
  subject_role: represented_group
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: classroom_shared
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-12T09:06:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
- record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_exhibition_session
  artifact_instance_id: art_proj_exhibition_archive
  subject_reference:
    subject_kind: concord_session
    subject_id: ses_proj_exhibition_01
    owning_system: concord
  subject_role: session_context
  confirmation_status: confirmed
  assignment_source: teacher_review
  privacy_policy:
    classification: classroom_shared
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-12T09:06:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
core_source_scan:
  owning_system: core
  record_kind: source_scan
  record_id: scan_core_proj_exhibition
  source_filename: synthetic_project_exhibition_archive.pdf
  retained_at: '2026-11-12T09:00:00-05:00'
  page_count: 1
  page_manifest:
  - source_page_index: 0
    route_id: route_proj_exhibition_archive_01
scan_reference:
  record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_exhibition_archive
  artifact_page_id: page_proj_exhibition_archive_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_exhibition
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project_exhibition
      owning_system: core
    timestamp: '2026-11-12T09:01:00-05:00'
    source_kind: routed
    note: Evidence-only page routed and filed.
artifact_review:
  record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_exhibition_archive
  artifact_instance_id: art_proj_exhibition_archive
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-12T09:10:00-05:00'
  readability_judgment: readable
  page_completeness_judgment: complete
  filing_judgment: confirmed
  author_judgment: confirmed
  subject_judgment: confirmed
  privacy_judgment: classroom_shared
  relevance_judgment: relevant
  moderation_requirement: not_required
  scoring_readiness: not_applicable
  review_outcome: ready
  privacy_policy:
    classification: classroom_shared
  notes: The evidence is readable, correctly filed, and suitable for archive use. The Activity intentionally
    creates no Scores.
```

Validation:

```text
scoring_orientation: evidence_only
standards_profile_id: absent
focus_standard_ids: absent
criterion_set_ids: absent
Score Records: none
Standards Result Projection rows: none
```

The reviewed archive remains evidence organization, not performance judgment.

### 23.2 Local-Criteria-Only Project Retrospective

This follow-up Activity records one local Group judgment about retrospective handoff quality. It deliberately has no standards profile or Focus Standards.

### Activity, Session, Group, and Membership
```yaml
activity:
  record_owner: concord
  record_kind: activity
  activity_id: act_proj_retrospective_01
  class_reference:
    module_id: core
    record_kind: class
    record_id: cls_apcsp_p01
  title: Project Retrospective and Handoff Check
  activity_type: local:project_retrospective
  description: A bounded follow-up Activity that judges only the usability of a collaborative retrospective
    and handoff.
  scoring_orientation: local_criteria_only
  criterion_set_ids:
  - critset_proj_retro_local_rev_1
  status: completed
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:30:00-05:00'
    source_kind: manual
    note: Local-criteria-only follow-up Activity configured.
session:
  record_owner: concord
  record_kind: session
  session_id: ses_proj_retro_01
  activity_id: act_proj_retrospective_01
  sequence: 1
  label: Project Retrospective Session
  scheduled_start: '2026-11-13T08:05:00-05:00'
  scheduled_end: '2026-11-13T08:50:00-05:00'
  actual_start: '2026-11-13T08:06:00-05:00'
  actual_end: '2026-11-13T08:47:00-05:00'
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:35:00-05:00'
    source_kind: manual
    note: Local-only Session configured.
group:
  record_owner: concord
  record_kind: group
  group_id: grp_proj_retro_b
  activity_id: act_proj_retrospective_01
  label: Retrospective Group B
  description: Activity-specific retrospective Group.
  effective_context:
    activity_id: act_proj_retrospective_01
    session_ids:
    - ses_proj_retro_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:40:00-05:00'
    source_kind: manual
    note: Retrospective Group created.
group_memberships:
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_retro_003
  group_id: grp_proj_retro_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_003
    owning_system: core
  effective_context:
    activity_id: act_proj_retrospective_01
    session_ids:
    - ses_proj_retro_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:42:00-05:00'
    source_kind: manual
    note: Retrospective Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_retro_004
  group_id: grp_proj_retro_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_004
    owning_system: core
  effective_context:
    activity_id: act_proj_retrospective_01
    session_ids:
    - ses_proj_retro_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:42:00-05:00'
    source_kind: manual
    note: Retrospective Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_retro_005
  group_id: grp_proj_retro_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_005
    owning_system: core
  effective_context:
    activity_id: act_proj_retrospective_01
    session_ids:
    - ses_proj_retro_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:42:00-05:00'
    source_kind: manual
    note: Retrospective Membership created.
- record_owner: concord
  record_kind: group_membership
  membership_id: mem_proj_retro_006
  group_id: grp_proj_retro_b
  participant_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  effective_context:
    activity_id: act_proj_retrospective_01
    session_ids:
    - ses_proj_retro_01
  status: completed
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:42:00-05:00'
    source_kind: manual
    note: Retrospective Membership created.
```

### Local Criterion Set and Criterion

```yaml
criterion_set:
  record_owner: concord
  record_kind: criterion_set
  criterion_set_id: critset_proj_retro_local_rev_1
  lineage_id: critset_proj_retro_local
  name: Project Retrospective Local Criteria
  purpose: Judge only the usability and traceability of a collaborative retrospective.
  revision: 1
  scope: activity_specific
  criterion_set_kind: local
  criterion_ids:
  - crit_proj_retro_handoff
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:45:00-05:00'
    source_kind: manual
    note: Local-only Criterion Set revision created.
criterion:
  record_owner: concord
  record_kind: criterion
  criterion_id: crit_proj_retro_handoff
  criterion_set_id: critset_proj_retro_local_rev_1
  key: retrospective_handoff
  label: Produces a usable retrospective handoff
  definition: Explains major decisions, unfinished work, limitations, and recommended next steps in a
    form collaborators can use.
  criterion_kind: local
  alignment_standard_ids:
  - std_njsls_cs_8_1_12_ap_4
  supported_target_kinds:
  - concord_group
  default_scoring_scale_id: scale_proj_process_3_rev_1
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:46:00-05:00'
    source_kind: manual
    note: Local retrospective Criterion created with non-governing alignment.
```

The Criterion’s `alignment_standard_ids` record instructional relevance only. They do not make the local Score a direct standards result.

### Template, Artifact, Page, and Route
```yaml
template_definition:
  record_owner: concord
  record_kind: template_definition
  template_id: tmpl_proj_retrospective
  name: Collaborative Project Retrospective
  artifact_category: local:retrospective
  purpose: Capture Group decisions, lessons, limitations, unfinished work, and next steps.
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-10T14:50:00-05:00'
    source_kind: manual
    note: Local-only retrospective Template Definition created.
template_version:
  record_owner: concord
  record_kind: template_version
  template_version_id: tmplv_proj_retrospective_r1
  template_id: tmpl_proj_retrospective
  version_label: Revision 1
  revision_sequence: 1
  rendering_specification_reference:
    record_kind: rendering_specification
    record_id: render_tmplv_proj_retrospective_r1
  artifact_category: local:retrospective
  page_manifest:
  - page_kind: primary
    return_expected: true
    route_required: true
    page_number: 1
  expected_return_behavior:
    mode: all_declared_return_pages
    required_page_numbers:
    - 1
  default_privacy_policy:
    classification: group_and_teacher
  default_authorship_expectation:
    mode: local:collective_group_with_named_recorder
  default_subject_expectation:
    mode: local:one_activity_group
  supported_criterion_ids:
  - crit_proj_retro_handoff
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
    timestamp: '2026-11-10T14:55:00-05:00'
    source_kind: manual
    note: Immutable Revision 1 Template Version created.
  status: active
artifact_instance:
  record_owner: concord
  record_kind: artifact_instance
  artifact_instance_id: art_proj_retro_b
  template_version_id: tmplv_proj_retrospective_r1
  activity_id: act_proj_retrospective_01
  session_id: ses_proj_retro_01
  group_id: grp_proj_retro_b
  artifact_category: local:retrospective
  generation_status: generated
  expected_return_status: returned
  artifact_status: completed
  privacy_policy:
    classification: group_and_teacher
  page_ids:
  - page_proj_retro_b_01
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-13T07:45:00-05:00'
    source_kind: generated
    note: Local-only retrospective Artifact generated.
artifact_page:
  record_owner: concord
  record_kind: artifact_page
  artifact_page_id: page_proj_retro_b_01
  artifact_instance_id: art_proj_retro_b
  page_number: 1
  expected_page_count: 1
  page_kind: primary
  return_expected: true
  route_required: true
  route_id: route_proj_retro_b_01
  human_fallback: PR-RETRO-B
  page_status: returned
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-13T07:45:10-05:00'
    source_kind: generated
    note: Local-only page identity created before rendering.
route_registration:
  owning_system: core
  record_kind: route_registration
  route_id: route_proj_retro_b_01
  locator:
    schema: PDS2
    module_id: concord
    class_id: cls_apcsp_p01
    work_id: act_proj_retrospective_01
    route_id: route_proj_retro_b_01
  target:
    module_id: concord
    record_kind: artifact_page
    record_id: page_proj_retro_b_01
  status: active
  registered_at: '2026-11-13T07:45:20-05:00'
```

### Author, Subject, Scan, and Review

```yaml
artifact_authors:
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_retro_b_group
  artifact_instance_id: art_proj_retro_b
  author_reference:
    record_kind: group
    record_id: grp_proj_retro_b
  authorship_mode: collective_group_author
  representation_status: multiple_named_positions
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-13T09:05:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
- record_owner: concord
  record_kind: artifact_author
  artifact_author_id: author_proj_retro_b_recorder
  artifact_instance_id: art_proj_retro_b
  author_reference:
    participant_kind: core_student
    participant_id: stu_006
    owning_system: core
  authorship_mode: recorder_for_group
  representation_status: recorder_summary
  attribution_status: confirmed
  attribution_source: teacher_review
  privacy_policy:
    classification: group_and_teacher
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-13T09:06:00-05:00'
    source_kind: manual
    note: Artifact authorship association recorded after Review.
  represented_group_id: grp_proj_retro_b
artifact_subject:
  record_owner: concord
  record_kind: artifact_subject
  artifact_subject_id: subject_proj_retro_b_group
  artifact_instance_id: art_proj_retro_b
  subject_reference:
    subject_kind: concord_group
    subject_id: grp_proj_retro_b
    owning_system: concord
  subject_role: represented_group
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
    timestamp: '2026-11-13T09:07:00-05:00'
    source_kind: manual
    note: Artifact Subject association recorded.
core_source_scan:
  owning_system: core
  record_kind: source_scan
  record_id: scan_core_proj_retro_b
  source_filename: synthetic_project_retro_b.pdf
  retained_at: '2026-11-13T09:00:00-05:00'
  page_count: 1
  page_manifest:
  - source_page_index: 0
    route_id: route_proj_retro_b_01
scan_reference:
  record_owner: concord
  record_kind: scan_reference
  scan_reference_id: scanref_proj_retro_b
  artifact_page_id: page_proj_retro_b_01
  core_source_scan_reference:
    module_id: core
    record_kind: source_scan
    record_id: scan_core_proj_retro_b
  source_page_index: 0
  routing_status: routed
  readability_status: readable
  filing_status: confirmed
  review_status: reviewed
  preferred_for_use: true
  created_provenance:
    actor:
      actor_kind: system
      actor_id: core_dispatch_project_retro
      owning_system: core
    timestamp: '2026-11-13T09:01:00-05:00'
    source_kind: routed
    note: Local-only retrospective page routed and filed.
artifact_review:
  record_owner: concord
  record_kind: artifact_review
  artifact_review_id: review_proj_retro_b
  artifact_instance_id: art_proj_retro_b
  reviewer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  reviewed_at: '2026-11-13T09:10:00-05:00'
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
    classification: group_and_teacher
  notes: The retrospective is readable, correctly filed, and ready for local-Criterion scoring.
```

### Local Score and Evidence Link

```yaml
score_record:
  record_owner: concord
  record_kind: score_record
  score_record_id: score_proj_retro_b_handoff
  activity_id: act_proj_retrospective_01
  session_id: ses_proj_retro_01
  target_reference:
    target_kind: concord_group
    target_id: grp_proj_retro_b
    owning_system: concord
  criterion_id: crit_proj_retro_handoff
  score_kind: local
  scoring_scale_id: scale_proj_process_3_rev_1
  disposition: scored
  value: effective
  basis: linked_evidence
  scorer:
    actor_kind: authorized_adult
    actor_id: actor_teacher_001
    owning_system: local_example_identity
    display_label_snapshot: Teacher 001
  scored_at: '2026-11-13T09:20:00-05:00'
  moderation_complete: true
  privacy_policy:
    classification: group_and_teacher
    audience_references:
    - record_kind: group
      record_id: grp_proj_retro_b
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-13T09:20:00-05:00'
    source_kind: manual
    note: Teacher recorded a local-only Group Score.
score_evidence_link:
  record_owner: concord
  record_kind: score_evidence_link
  score_evidence_link_id: scoreev_proj_retro_b_handoff
  score_record_id: score_proj_retro_b_handoff
  evidence_reference:
    evidence_kind: artifact_instance
    owning_system: concord
    record_id: art_proj_retro_b
  subject_context:
    subject_kind: concord_group
    subject_id: grp_proj_retro_b
    owning_system: concord
  relevance_description: The reviewed retrospective directly documents decisions, limitations, unfinished
    work, and recommended next steps.
  significance: primary
  status: active
  created_provenance:
    actor:
      actor_kind: authorized_adult
      actor_id: actor_teacher_001
      owning_system: local_example_identity
      display_label_snapshot: Teacher 001
    timestamp: '2026-11-13T09:20:00-05:00'
    source_kind: manual
    note: Teacher linked the retrospective to the local Score.
```

Validation:

```text
scoring_orientation: local_criteria_only
standards_profile_id: absent
focus_standard_ids: absent
score_kind: local
standard_id: absent
Standards Result Projection rows: none
```

The local Score may be used by an explicit downstream policy, but it is not a direct standards result.

## 24. Addendum Registration and Publication Outcomes

### 24.1 Evidence-only archive

The exhibition archive demonstrates that an `evidence_only` Activity does not automatically create academic registration or publication.

```text
Core Academic Work Registration: none
Concord Academic Result Manifest: none
Core Publication Record: none
```

The Activity remains valid Concord work. Its routed and reviewed evidence may be referenced later, but evidence presence alone is not an `academic_result_set`.

### 24.2 Local-criteria-only retrospective registration

```yaml
record_owner: core
record_kind: academic_work_registration
schema_version: '1'
record_type: academic_work_registration
work:
  module_id: concord
  class_id: cls_apcsp_p01
  work_id: act_proj_retrospective_01
registration_revision: 1
producer_contract_version: concord_activity_v1
title: Project Retrospective and Handoff Check
work_kind: collaborative_activity
academic_intent: formative
lifecycle: closed
created_at: '2026-11-10T14:31:00-05:00'
updated_at: '2026-11-13T09:23:00-05:00'
source_records:
- module_id: concord
  record_kind: activity
  record_id: act_proj_retrospective_01
  contract_version: '1'
```

The registration uses `academic_intent: formative`. That Core intent is independent of Concord's `scoring_orientation: local_criteria_only`.

### 24.3 Local-criteria-only manifest

The manifest contains the local Score and its evidence lineage. Its Standards Result Projection is an empty array.

```json
{
  "activity_context": {
    "activity_id": "act_proj_retrospective_01",
    "activity_status_snapshot": "completed",
    "activity_type": "local:project_retrospective",
    "class_id": "cls_apcsp_p01",
    "scoring_orientation": "local_criteria_only",
    "session_references": [
      {
        "record_id": "ses_proj_retro_01",
        "record_kind": "session"
      }
    ],
    "title_snapshot": "Project Retrospective and Handoff Check"
  },
  "criterion_projections": [
    {
      "alignment_standard_ids": [
        "std_njsls_cs_8_1_12_ap_4"
      ],
      "criterion_id": "crit_proj_retro_handoff",
      "criterion_kind": "local",
      "criterion_set_id": "critset_proj_retro_local_rev_1",
      "definition": "Explains major decisions, unfinished work, limitations, and recommended next steps in a form collaborators can use.",
      "key": "retrospective_handoff",
      "label": "Produces a usable retrospective handoff",
      "status_snapshot": "active",
      "supported_target_kinds": [
        "concord_group"
      ]
    }
  ],
  "generated_at": "2026-11-13T09:25:00-05:00",
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
    "timestamp": "2026-11-13T09:25:00-05:00"
  },
  "manifest_contract_version": "concord_academic_result_manifest_v1",
  "moderation_projections": [],
  "privacy_classification": "group_and_teacher",
  "producer_module_id": "concord",
  "record_kind": "concord_academic_result_manifest",
  "record_owner": "concord",
  "record_set_id": "rs_proj_retrospective_01",
  "record_set_revision": 1,
  "score_evidence_link_projections": [
    {
      "evidence_reference": {
        "evidence_kind": "artifact_instance",
        "owning_system": "concord",
        "record_id": "art_proj_retro_b"
      },
      "relevance_description": "The reviewed retrospective directly documents decisions, limitations, unfinished work, and recommended next steps.",
      "score_evidence_link_id": "scoreev_proj_retro_b_handoff",
      "score_record_id": "score_proj_retro_b_handoff",
      "significance": "primary",
      "source_record_reference": {
        "record_id": "art_proj_retro_b",
        "record_kind": "artifact_instance"
      },
      "status": "current",
      "subject_context": {
        "owning_system": "concord",
        "subject_id": "grp_proj_retro_b",
        "subject_kind": "concord_group"
      }
    }
  ],
  "score_projections": [
    {
      "activity_id": "act_proj_retrospective_01",
      "basis": "linked_evidence",
      "criterion_id": "crit_proj_retro_handoff",
      "current_status": "current",
      "disposition": "scored",
      "moderation_complete": true,
      "privacy_classification": "group_and_teacher",
      "score_kind": "local",
      "score_record_id": "score_proj_retro_b_handoff",
      "scored_at": "2026-11-13T09:20:00-05:00",
      "scorer": {
        "actor_id": "actor_teacher_001",
        "actor_kind": "authorized_adult",
        "display_label_snapshot": "Teacher 001",
        "owning_system": "local_example_identity"
      },
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "session_id": "ses_proj_retro_01",
      "target_reference": {
        "owning_system": "concord",
        "target_id": "grp_proj_retro_b",
        "target_kind": "concord_group"
      },
      "value": "effective"
    }
  ],
  "scoring_scale_projections": [
    {
      "levels": [
        {
          "label": "Limited",
          "meaning": "The handoff is incomplete or difficult for collaborators to use.",
          "order": 1,
          "value": "limited"
        },
        {
          "label": "Functional",
          "meaning": "The handoff communicates enough information for routine continuation.",
          "order": 2,
          "value": "functional"
        },
        {
          "label": "Effective",
          "meaning": "The handoff is clear, current, traceable, and supports efficient continuation or review.",
          "order": 3,
          "value": "effective"
        }
      ],
      "lineage_id": "scale_proj_process_3",
      "name": "Collaborative Process and Handoff Scale",
      "scale_type": "ordinal",
      "scoring_scale_id": "scale_proj_process_3_rev_1",
      "status_snapshot": "active"
    }
  ],
  "source_activity": {
    "contract_version": "1",
    "record_id": "act_proj_retrospective_01",
    "record_kind": "activity"
  },
  "standards_result_projection": [],
  "work": {
    "class_id": "cls_apcsp_p01",
    "module_id": "concord",
    "work_id": "act_proj_retrospective_01"
  }
}
```

SHA-256:

```text
9d54f078056388d4a42c50d185df9e9ffee5e2b0aa24b22c48c4435857b37198
```

### 24.4 Local-criteria-only Core Publication Record

```yaml
record_owner: core
record_kind: publication_record
schema_version: '1'
record_type: publication_record
publication_id: pub_concord_proj_retrospective_001
work:
  module_id: concord
  class_id: cls_apcsp_p01
  work_id: act_proj_retrospective_01
source_record:
  module_id: concord
  record_kind: activity
  record_id: act_proj_retrospective_01
  contract_version: '1'
publication_kind: academic_result_set
capabilities:
- criterion_scores
record_set_id: rs_proj_retrospective_01
record_set_revision: 1
manifest_contract_version: concord_academic_result_manifest_v1
manifest_path: classes/cls_apcsp_p01/modules/concord/work/act_proj_retrospective_01/exports/manifests/rs_proj_retrospective_01/1.json
manifest_digest_algorithm: sha256
manifest_digest: 9d54f078056388d4a42c50d185df9e9ffee5e2b0aa24b22c48c4435857b37198
published_at: '2026-11-13T09:35:00-05:00'
academic_work_registration_revision: 1
```

The publication declares only `criterion_scores`. It does not claim `standards_ratings`, even though the local Criterion carries non-governing standards-alignment metadata.

This publication remains discoverable by Meridian, but Meridian must apply explicit policy before a local result can affect a Grade.

## 25. Meridian Consumption Boundary

Meridian may discover and import:

- the two primary-Activity Core Publication Records;
- the local-only retrospective Publication Record;
- and any other producer publications independently available through Core.

Meridian must not infer that every discovered publication is eligible for grading.

For the primary Activity, Meridian must preserve:

- the exact Core Publication Record ID selected;
- the exact Concord manifest revision;
- the Core Academic Work Registration revision;
- standard-backed versus local Score classification;
- Group versus individual target identity;
- the exact Scoring Scale revision and level meaning;
- current versus superseded Score state;
- external project-evidence lineage;
- Moderation status;
- and the teacher's selected or excluded evidence under Meridian policy.

The external GitHub, CI, CAD, and cloud-document records are not separate PDS result publications in this example. Their lineage is retained as underlying evidence, not imported as duplicate academic results.

Meridian owns:

- Grade-item membership;
- Academic Period membership;
- publication eligibility;
- overlap and duplicate-evidence policy;
- scale interpretation or mapping;
- standards proficiency calculation;
- weighting and aggregation;
- teacher overrides of derived results;
- Grade calculations;
- report snapshots;
- and report delivery.

A Meridian override changes the derived Meridian result. It does not create a Concord Score revision, a new Concord manifest, or a Core publication.

No Academic Period ID appears in the foundational Concord Score Records or manifests.

## 26. Relationship Summary

```text
Core Class
    -> Primary mixed Activity
        -> Sessions
        -> parent Groups
            -> child Groups
            -> historical Memberships
            -> contextual Roles
            -> contextual Responsibilities
        -> Activity Markers
        -> Work Items
            -> Work-Item Dependencies
        -> Activity Events
        -> Contribution Claims
            -> Moderation Records
            -> corrected/superseding Claims
        -> Packet Instance
            -> exact Packet Version
            -> Artifact Instances
                -> Artifact Pages
                    -> Core Route Registrations
                    -> Scan References
                -> Artifact Authors
                -> Artifact Subjects
                -> Artifact Reviews
        -> Attachments
        -> External References
        -> mixed Criterion Set
            -> standard-backed Criteria
            -> local Criterion
        -> Score Records
            -> Score Evidence Links
            -> standard-backed handoff rows only

Core Class
    -> Evidence-only exhibition Activity
        -> reviewed evidence
        -> no Scores

Core Class
    -> Local-criteria-only retrospective Activity
        -> local Criterion
        -> local Score
        -> no standards handoff
```

## 27. Lifecycle Walkthrough

### 20.1 Configuration

```text
Activity configured
    -> Sessions created
    -> parent and child Groups created
    -> Memberships created
    -> Roles and Responsibilities assigned
    -> Markers and Work Items created
    -> Dependencies recorded
    -> mixed Criterion Set and scales selected
```

No Score exists at configuration time.

### 20.2 Generation and Routing

```text
Packet Version selected
    -> Packet Instance generated
    -> Artifact Instances generated
    -> Artifact Pages created
    -> Core Route Registrations created
    -> PDS2 locators rendered
```

Artifact Page identity exists before Route Registration and rendering.

### 20.3 Iteration and Exception Handling

```text
requirements and architecture recorded
    -> implementation Work Items progress
    -> source-control outage interrupts integration
    -> blocked Work Item preserved
    -> service restored
    -> replacement Work Item completed
```

The outage remains contextual evidence and never becomes a low Score.

### 20.4 Membership and Responsibility Change

```text
Student 003 participates in Group A
    -> teacher records reassignment Event
    -> earlier Group A Membership remains
    -> later Group B Membership supersedes earlier context
    -> later Role and Responsibility records use Group B
```

Earlier contributions remain attached to their original Activity context.

### 20.5 Testing and Claim Moderation

```text
accessibility regression discovered
    -> defect reproduced and corrected
    -> Contribution Claims reviewed
    -> sole-authorship claim disputed
    -> corrected bounded Claim recorded
    -> corrected Claim Moderated
```

Claim acceptance is permission for use, not a Score.

### 20.6 Scoring and Supersession

```text
teacher selects explicit target and Criterion
    -> teacher deliberately links applicable evidence
    -> Group and individual Scores recorded separately
    -> Student 005 initially receives deferred disposition
    -> additional evidence resolves dispute
    -> later Score supersedes deferred record
```

Local Scores remain outside standards-only manifest projection.

### 20.7 Follow-Up Activities

```text
release evidence
    -> evidence-only exhibition archive
    -> Review without scoring

retrospective evidence
    -> local-criteria-only judgment
    -> no standards handoff
```

## 28. Invariant Validation
| Invariant | Result | Evidence |
| --- | --- | --- |
| Every Activity belongs to one Core class | Pass | All three Activities reference `cls_apcsp_p01`. |
| Every Activity has at least one Session | Pass | Primary has five; each addendum has one. |
| All four scoring orientations are exercised collectively | Pass | Seminar is standards-based, laboratory and primary project are mixed, and this file adds evidence-only and local-only. |
| Groups are Activity-specific | Pass | Primary and addendum Groups have distinct identities and parent Activities. |
| Membership history is preserved | Pass | Student 003 has separate Group A and Group B Memberships with bounded contexts. |
| Role and Responsibility history is preserved | Pass | Later assignments do not rewrite earlier records. |
| Assignment does not prove performance | Pass | Roles and Responsibilities never create Scores. |
| Child Groups are optional and bounded | Pass | Only Group A uses child Groups during early development. |
| Blocked work is not poor performance | Pass | The repository outage blocks a Work Item without setting a low Score. |
| Work Item dependencies do not create Scores | Pass | Dependencies provide sequence and context only. |
| Activity Events are not automatically contribution or performance | Pass | Events require separate evidence use and teacher judgment. |
| Contribution Claims remain distinct from contribution proof | Pass | Claims receive Review and Moderation. |
| Disputed claim is not negative evidence | Pass | The sole-authorship dispute prompts deferral and correction, not a low Score. |
| External ownership remains external | Pass | GitHub, CAD, CI, and cloud-document records are referenced only. |
| File/account ownership does not establish authorship | Pass | Artifact Author associations are reviewed Concord records. |
| Template definitions and immutable versions remain distinct | Pass | Every Artifact references one exact Template Version. |
| Artifact Pages exist before routes | Pass | All route-required pages have prior identities. |
| PDS2 contains route identity only | Pass | No Author, Subject, standard, Criterion, claim, or Score is encoded. |
| Core-retained source scan remains canonical | Pass | Concord stores Scan References; rescans preserve both sources. |
| Author, Subject, Score target, and scorer remain distinct | Pass | Separate typed associations and references are used. |
| Teacher tracker remains one multi-Subject Artifact | Pass | One tracker has 15 Subject associations. |
| Review does not create a Score | Pass | Reviews establish readiness only. |
| Moderation does not create a Score | Pass | Accepted claims still require explicit teacher judgment. |
| Standard-backed Criterion has one governing standard | Pass | Each direct Criterion has exactly one Focus Standard. |
| Local Criterion has no governing standard | Pass | Both local Criteria contain only non-governing alignment. |
| One Score evaluates one Criterion for one target | Pass | Every Score has one target and one immutable Criterion. |
| Group Score does not become member Scores | Pass | Group A and B standards Scores remain Group-targeted. |
| Group evidence may support an individual Score explicitly | Pass | Evidence Links identify Student 001 or Student 005 relevance. |
| Non-score disposition has no value | Pass | Student 005 v1 is `deferred` with no `value` field. |
| Supersession preserves prior judgment | Pass | Student 005 v2 supersedes v1; both remain represented. |
| Local Scores are excluded from standards handoff | Pass | Primary local Scores and the retrospective Score have no handoff rows. |
| Evidence-only Activity produces no Scores | Pass | Exhibition archive ends with Review only. |
| Standards handoff preserves target and scale identity | Pass | Five rows retain exact targets, Criteria, scales, dispositions, and current status. |
| Concord does not calculate mastery or Grades | Pass | No aggregation or grade fields appear. |

## 29. Represented Cleanly

The current conceptual contracts represent the following project requirements without a case-specific foundational entity:

- a five-Session collaborative project;
- parent and child Groups;
- contextual Membership reassignment;
- changing Roles and Responsibilities;
- ordered stages;
- bounded tasks and Dependencies;
- blocked work and external-system interruption;
- architecture, testing, intervention, and handoff Events;
- Group and individual Artifacts;
- teacher-authored multi-Subject evidence;
- Attachments;
- external repository, commit, pull-request, CI, CAD, and cloud-document relationships;
- moderated Contribution Claims;
- Group and individual standards Scores;
- local Group and individual Scores;
- a deferred individual judgment;
- Score supersession;
- standards-result handoff;
- evidence-only follow-up;
- and local-criteria-only follow-up.

The same foundation handles project semantics without making Concord a source-control, CAD, CI, or general project-management system.

## 30. Optional Structures Used

### Child Groups

Child Groups are used for bounded interface and data/test subteam identity during early development. They are not created merely because participants hold different Responsibilities.

### Responsibility Assignment

Responsibilities identify explicit obligations whose reassignment must remain historically visible. They do not prove completion or quality.

### Activity Markers

Markers identify planning, implementation, integration, testing, and release stages without replacing Sessions.

### Work Items and Dependencies

Work Items provide bounded task identity for implementation, testing, accessibility, integration, and release. Dependencies explain blocked or sequenced work.

### Activity Events

Events preserve meaningful decisions, interruption, reassignment, test failure, correction, and handoff chronology.

### Contribution Claims

Claims express participant statements about contribution. They remain distinct from reviewed contribution evidence and Scores.

### Attachments

Attachments represent screenshots, project diagrams, and physical materials that are not normal Concord-generated Artifact Pages.

### External References

External References preserve ownership boundaries while allowing repositories, commits, pull requests, CI runs, CAD models, and cloud documents to support Concord workflows.

## 31. Contracts Deliberately Not Used

### Universal repository or commit entities

Source-control concepts remain externally owned. Concord does not create universal Repository, Branch, Commit, Pull Request, or CI entities.

### Automatic contribution extraction

The project does not infer contribution from commit counts, lines changed, file ownership, Work Item completion, Role, Responsibility, or Group Membership.

### Automatic Group-to-individual scoring

Group Scores remain Group judgments. Member Scores require separate explicit teacher judgments.

### Grading and mastery records

The case stops at contextual Concord Scores and handoff projections. It does not calculate a course Grade, mastery state, growth trend, average, or weighting.

### Specialized software-build contract

Build and test semantics are represented through Work Items, Events, Attachments, External References, and controlled local vocabulary. No shared specialized build entity is required by the demonstrated invariants.

## 32. Tensions or Ambiguities

### 25.1 External evidence immutability

External References identify stable external records and may include content digests or version labels. A later implementation must define how adapters report changed or unavailable external content without implying that Concord controls the external source.

This is implementation work, not a conceptual blocker.

### 25.2 Contribution evidence granularity

The current Evidence Locator can identify a Work Item, page, marker, or human note. A future repository adapter may expose finer provider-specific locations. Those details should remain inside the External Locator or adapter contract rather than expanding the foundation prematurely.

No contract change is required.

### 25.3 Work Item replacement versus contextual continuation

The Group A integration replacement uses supersession because the later record becomes the current representation of the bounded integration task after an exceptional blocked state. Other workflows may choose a continuing Work Item with Event history instead.

The contracts permit either when the chosen history remains explicit. Later schema guidance should document validation expectations, but no conceptual change is required.

## 33. Workarounds Rejected

### Treating a GitHub account as the Artifact Author

Rejected. External account and file ownership do not establish Concord authorship.

### Using commit counts as contribution or performance

Rejected. Commit history may support judgment but does not create a Contribution Claim, Score, or authorship association automatically.

### Treating Work Item completion as performance

Rejected. Work Item status describes work state, not Criterion-level quality.

### Treating Responsibility as contribution proof

Rejected. Responsibility records what was assigned, not what was completed or demonstrated.

### Rewriting Student 003’s Group membership

Rejected. The later Group B Membership preserves the earlier Group A relationship.

### Deleting the blocked integration record

Rejected. The outage and blocked Work Item remain historically available.

### Assigning a low Score because the repository was unavailable

Rejected. External failure is contextual, not performance.

### Treating the failed regression test as poor performance

Rejected. The failed-then-corrected test may support strong testing-and-debugging evidence.

### Accepting sole authorship from repository metadata

Rejected. Teacher Review and Moderation reconcile several evidence sources and preserve a corrected bounded Claim.

### Converting the deferred disposition to the lowest scale level

Rejected. The non-score record contains no value.

### Exporting local collaboration Scores as standards results

Rejected. Non-governing alignment does not change Score classification.

### Copying repositories, CAD models, or cloud documents into Concord ownership

Rejected. Stable External References preserve external authority.

### Creating one holistic project Score and duplicating it across standards

Rejected. Separate standard-backed Criteria and Score Records preserve direct standards meaning.

## 34. Contract Changes Required

```text
None.
```

The project, evidence-only addendum, and local-criteria-only addendum can be represented without weakening accepted invariants, duplicating ownership, hiding missing concepts in unrestricted extension data, or introducing case-specific foundational records.

## 35. Project Case Acceptance Assessment

- [x] A primary `mixed` Activity is represented.
- [x] One Core standards profile and ordered Focus Standards are represented.
- [x] Separate standard-backed Criteria each govern exactly one Focus Standard.
- [x] A local Criterion has no governing standard.
- [x] Non-governing standards alignment is represented.
- [x] Group and individual standards Scores are represented.
- [x] Group and individual local Scores are represented.
- [x] Local Scores are excluded from standards-only manifest projection.
- [x] A bounded `evidence_only` Activity is represented.
- [x] The evidence-only Activity defines no Criteria, scales, Scores, or handoff rows.
- [x] A bounded `local_criteria_only` Activity is represented.
- [x] The local-only Activity has no standards profile or Focus Standards.
- [x] The local-only Score has no governing standard and no handoff row.
- [x] All four Activity scoring orientations are exercised collectively across the representative cases.
- [x] Multiple Sessions and project stages are represented.
- [x] Parent and child Groups are represented.
- [x] Changing Membership preserves earlier context.
- [x] Changing Roles and Responsibilities preserve earlier records.
- [x] Assigned work does not establish performance.
- [x] Work Items and Dependencies are represented.
- [x] A blocked Work Item is not treated as poor performance.
- [x] Architecture, interruption, reassignment, test, and handoff Events are represented.
- [x] Contribution Claims remain distinct from contribution proof.
- [x] Conflicting and corrected Contribution Claims are represented.
- [x] Moderation preserves disputed and superseding decisions.
- [x] External repository, commit, pull-request, CI, CAD, and cloud-document records remain externally owned.
- [x] External ownership does not establish Artifact authorship.
- [x] Group-authored, recorder-authored, individually authored, and teacher-authored Artifacts are represented.
- [x] One teacher tracker remains a multi-Subject Artifact.
- [x] PDS2 routes target existing Artifact Pages.
- [x] QR locators contain no semantic authorship, contribution, standards, Criterion, or Score data.
- [x] Core-retained source scans remain canonical.
- [x] A rescan preserves the original source and Scan Reference.
- [x] Review remains distinct from Moderation and Scoring.
- [x] Group evidence supports individual Scores only through explicit teacher judgment.
- [x] One Score uses several evidence sources.
- [x] One evidence source may support several separate Scores.
- [x] A deferred non-score disposition contains no value.
- [x] A later Score supersedes the deferred record while preserving history.
- [x] Standards Result Projection preserves individual and Group target identity.
- [x] Standards Result Projection preserves exact Criterion and scale identity.
- [x] Standards Result Projection performs no mastery, Grade, weighting, or aggregation calculation.
- [x] No architecture-breaking workaround is required.
