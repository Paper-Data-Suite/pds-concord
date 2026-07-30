# Concord Foundation Review

**Status:** In progress  
**Issue:** #13 — Conduct a Skeptical Foundation Review  
**Branch:** `13-conduct-skeptical-foundation-review`

## 1. Purpose

This document records a skeptical review of the proposed Concord conceptual foundation before serialized contracts or implementation begin.

The review evaluates the architecture established through issue #12, including its relationship with PDS Core, Meridian, ScoreForm, and Quillan.

## 2. Review Method

Each architectural area will be examined for:

- conflicting ownership;
- duplicated concepts;
- missing or unenforceable invariants;
- contradictions among governing documents;
- unsupported assumptions in the representative examples;
- and unnecessary complexity.

Findings will be classified as:

- blocking defect;
- major revision;
- minor clarification;
- follow-up implementation concern;
- or no issue identified.

## 3. Finding Register

| ID | Area | Severity | Status | Finding | Required action |
|---|---|---|---|---|---|
| OWN-001 | Module ownership and authority | No issue identified | Reviewed | Each foundational concept has one coherent authoritative owner. | None |
| OWN-002 | Module ownership and authority | Minor clarification | Open | Verify that the Core catalog remains derived and publication never implies grading or reporting inclusion. | Check during publication and Meridian reviews |
| REG-001 | Activity identity and Core registration | Minor clarification | Resolved | Registration prose refers to nonexistent `Activity.class_id` rather than `Activity.class_reference.record_id`. | Correct the mapping language |
| REG-002 | Activity identity and Core registration | Minor clarification | Resolved | Concord registration only recommends, rather than requires, an Activity source reference. | Make the matching Activity `ModuleRecordRef` a Concord invariant |
| REG-003 | Activity identity and Core registration | Minor clarification | Resolved | “Applicable registration revision” is less precise than Core’s current-revision publication requirement. | Require the exact current revision at publication time |
| REG-004 | Activity identity and Core registration | No issue identified | Reviewed | Activity identity, explicit registration, revision history, and separation from grading are coherent. | None |

## 4. Review Areas

1. Module ownership and authority
2. Activity identity and Core registration
3. Evidence, Review, Moderation, and Scoring
4. Criteria, Scales, and Score semantics
5. Manifest and publication architecture
6. Revision, supersession, and withdrawal
7. Cross-producer evidence lineage
8. Meridian consumption boundary
9. Privacy and data minimization
10. Representative-example consistency
11. ADR 0015 disposition
12. Final verdict

## 5. Module Ownership and Authority Review

### 5.1 Review Question

Does each foundational concept have one clear authoritative owner, without unnecessary duplication or conflicting responsibility across Concord, PDS Core, Meridian, ScoreForm, Quillan, or external systems?

### 5.2 Ownership Matrix

| Concept                                          | Authoritative owner    | Other modules’ permitted role                                                                                   |
| ------------------------------------------------ | ---------------------- | --------------------------------------------------------------------------------------------------------------- |
| Class and roster identity                        | PDS Core               | Concord and Meridian reference Core identities                                                                  |
| Standards profiles and standards                 | PDS Core               | Concord selects standards; Meridian interprets published standards evidence under its policies                  |
| PDS2 Route Registrations                         | PDS Core               | Concord creates Artifact Pages that routes may target                                                           |
| Retained source scans and source-page provenance | PDS Core               | Concord creates semantic Scan References to Core-owned sources                                                  |
| Activity                                         | Concord                | Core may register the Activity as academic work; Meridian may consume its publications                          |
| Session                                          | Concord                | Other modules may reference Session context when exposed through a contract                                     |
| Activity-specific Group and Membership           | Concord                | Meridian may preserve target and contextual identity                                                            |
| Role and Responsibility Assignment               | Concord                | Other modules may consume bounded contextual projections when necessary                                         |
| Template, Packet, Artifact, and Artifact Page    | Concord                | Core routes returned pages; downstream modules may reference published evidence lineage                         |
| Artifact Author and Artifact Subject             | Concord                | Downstream modules may consume privacy-appropriate projections                                                  |
| Artifact Review                                  | Concord                | Downstream modules may consume readiness or provenance information when published                               |
| Moderation                                       | Concord                | Meridian may use the published Moderation state when determining evidence eligibility                           |
| Criterion and Scoring Scale                      | Concord                | Meridian consumes their exact published definitions and revisions                                               |
| Score Record                                     | Concord                | Meridian may select, exclude, reinterpret under policy, or override a derived result without mutating the Score |
| Score Evidence Link                              | Concord                | Meridian may inspect the published lineage to detect overlap or double counting                                 |
| Academic Work Registration                       | PDS Core               | Concord requests or supplies registration information through the Core contract                                 |
| Concord Academic Result Manifest                 | Concord                | Core validates and registers its publication; Meridian consumes it                                              |
| Publication Record                               | PDS Core               | Concord supplies the immutable manifest; Meridian discovers and imports the publication                         |
| Derived publication catalog                      | PDS Core               | Consumers may query it, but it is not authoritative source data                                                 |
| Publication withdrawal                           | PDS Core               | Concord may request withdrawal under the Core contract; consumers respond to the Core withdrawal state          |
| Grade-item membership                            | Meridian               | Concord publication does not imply membership                                                                   |
| Evidence eligibility and selection               | Meridian               | Concord supplies evidence and lineage but does not determine grading eligibility                                |
| Academic Period membership                       | Meridian               | Producer dates and Activity dates do not determine period membership                                            |
| Grade and proficiency calculations               | Meridian               | Concord does not calculate course Grades or longitudinal proficiency                                            |
| Meridian override                                | Meridian               | Does not revise Concord Scores, manifests, or Core Publication Records                                          |
| Formal report snapshot                           | Meridian               | Preserves references to source publications, policies, periods, and overrides                                   |
| ScoreForm result                                 | ScoreForm              | Concord may reference it as evidence without copying or assuming ownership                                      |
| Quillan response or result                       | Quillan                | Concord may reference it as evidence without copying or assuming ownership                                      |
| Repository, CI, CAD, or cloud-document record    | External source system | Concord stores a typed reference and bounded lineage only                                                       |

### 5.3 Boundary Tests

#### Concord Activity versus Core Academic Work Registration

A Concord Activity is the authoritative collaborative-work record.

A Core Academic Work Registration is a separate Core-owned declaration of the Activity’s academic identity and intent.

The registration does not replace or duplicate the Activity. The Activity must not copy Core-owned registration fields merely to avoid resolving the registration.

The following distinction is coherent:

```text
Concord Activity.scoring_orientation
    = how Concord may produce evidence and judgments

Core Academic Work Registration.academic_intent
    = the academic purpose under which the work is registered
```

No automatic registration should be inferred from:

* Activity creation;
* selection of Focus Standards;
* existence of Criteria;
* existence of Scores;
* or publication capability.

#### Concord Manifest versus Core Publication Record

The Concord Academic Result Manifest is a producer-owned statement of Concord records and their meaning.

The Core Publication Record is an immutable registry record that identifies and cryptographically binds one manifest revision.

Core does not become the owner of:

* Concord Criteria;
* Concord Scoring Scales;
* Concord Scores;
* evidence relationships;
* or the manifest’s academic meaning.

Concord does not become the owner of:

* Publication Record identity;
* registry validation;
* publication withdrawal;
* or the derived Core catalog.

#### Concord Score versus Meridian Result

A Concord Score remains the authoritative producer judgment.

A Meridian result is derived under Meridian-owned selection, policy, period, and override rules.

A Meridian override must not:

* revise the Concord Score;
* create a replacement Concord Score;
* rewrite the manifest;
* or mutate the Core Publication Record.

A changed Concord judgment and a changed Meridian-derived result are separate histories.

#### Core Source Scan versus Concord Scan Reference

Core owns the retained source and routing provenance.

Concord owns the semantic association between that source and its Artifact Page, Artifact, Review, and evidence context.

A rescan, duplicate, or filing correction must not require Concord to rewrite or replace the Core-owned source record.

#### Producer Evidence versus Concord Evidence Use

ScoreForm, Quillan, and external systems remain authoritative for their native records.

Concord owns its decision to use a source as evidence for a Concord Score.

The Concord Score Evidence Link must expose enough underlying source lineage for Meridian to recognize that it may also have imported the source producer’s publication directly.

### 5.4 Duplication Review

No necessary concept is assigned as authoritative data to more than one module.

The following apparent overlaps are intentional separations rather than duplication:

| Apparent overlap                               | Required distinction                                               |
| ---------------------------------------------- | ------------------------------------------------------------------ |
| Activity and Academic Work Registration        | Native collaborative work versus Core academic registration        |
| Manifest and Publication Record                | Producer-owned content versus Core-owned registry statement        |
| Source scan and Scan Reference                 | Retained physical source versus Concord semantic filing            |
| Score and Meridian result                      | Producer judgment versus policy-derived downstream result          |
| Score revision and Meridian override           | Changed source judgment versus changed downstream treatment        |
| Activity date and Academic Period membership   | Producer chronology versus Meridian-owned reporting classification |
| External source record and Score Evidence Link | Source-owned evidence versus Concord’s use of that evidence        |

### 5.5 Missing-Owner Review

No foundational concept reviewed in this pass lacks an authoritative owner.

In particular:

* publication withdrawal is Core-owned;
* evidence-overlap policy is Meridian-owned;
* manifest construction is Concord-owned;
* source evidence remains producer-owned;
* and Academic Period assignment is Meridian-owned.

### 5.6 Authority Risks

Two authority boundaries should remain explicit throughout the documentation.

#### Core catalog authority

The derived Core publication catalog is an index that can be rebuilt from immutable source records.

It must not become the only authoritative representation of:

* Academic Work Registrations;
* Publication Records;
* manifests;
* publication supersession;
* or withdrawal history.

#### Publication does not confer grading authority

A valid Core Publication Record establishes that a producer published a valid record-set revision.

It does not establish:

* Grade eligibility;
* Grade-item membership;
* Academic Period membership;
* evidence selection;
* mastery;
* report visibility;
* or inclusion in any Meridian calculation.

### 5.7 Findings

#### OWN-001 — Module ownership is coherent

| Field           | Value                                                                                                                                                                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Module ownership and authority                                                                                                                                                                                                                                  |
| Severity        | No issue identified                                                                                                                                                                                                                                             |
| Status          | Reviewed                                                                                                                                                                                                                                                        |
| Finding         | The proposed architecture assigns one authoritative owner to each foundational concept. The apparent overlaps among Activities, registrations, manifests, publications, Scores, and Meridian results are meaningful boundaries rather than duplicate ownership. |
| Required action | None. Preserve these boundaries in later serialized contracts and implementation.                                                                                                                                                                               |

#### OWN-002 — Core catalog and publication semantics require explicit nonauthority language

| Field           | Value                                                                                                                                                                                                                                                                                          |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Module ownership and authority                                                                                                                                                                                                                                                                 |
| Severity        | Minor clarification                                                                                                                                                                                                                                                                            |
| Status          | Open                                                                                                                                                                                                                                                                                           |
| Finding         | The architecture treats the Core publication catalog as derived and treats publication as separate from grading eligibility. These rules are present in the current design but are important enough to verify consistently in every governing document that discusses publication consumption. |
| Required action | During the publication-document review, confirm that no document treats the Core catalog as authoritative or implies that publication automatically creates Grade eligibility, Academic Period membership, or reporting inclusion.                                                             |

### 5.8 Ownership Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Minor clarifications: 1
Follow-up implementation concerns: 0
```

The proposed ownership model is suitable for continued foundation review.

No architecture document should be changed yet. Finding `OWN-002` should remain open until the publication and Meridian review areas confirm that the nonauthority rules are stated consistently.

## 6. Activity Identity and Core Academic Work Registration Review

### 6.1 Review Question

Do Concord Activity identity and Core Academic Work Registration form a coherent relationship without duplicating ownership, inferring academic intent, or creating ambiguous revision and lifecycle behavior?

### 6.2 Established Contract

Core’s neutral work identity is:

```text
ModuleWorkRef
├── module_id
├── class_id
└── work_id
```

A `ModuleWorkRef` does not by itself mean that the work is academic, registered, graded, reportable, or associated with an Academic Period. Academic Work Registration is a separate, explicit Core action.

For Concord, the intended mapping is:

```text
module_id = concord
class_id  = Activity.class_reference.record_id
work_id   = Activity.activity_id
```

The Activity remains the authoritative Concord record. Its `activity_id` serves as the Core `work_id`, but the Activity is not itself a Core registration or assignment record.

The resulting relationship is:

```text
Concord Activity
    -> ModuleWorkRef
    -> optional Core Academic Work Registration
    -> optional Concord manifest publication
    -> optional Meridian use
```

Each step is independently explicit.

### 6.3 Registration Model Compatibility

The implemented Core registration model contains:

```text
schema_version
record_type
work
registration_revision
producer_contract_version
title
work_kind
academic_intent
lifecycle
created_at
updated_at
source_records
```

Core controls the academic-intent vocabulary:

```text
formative
summative
diagnostic
practice
feedback_only
reporting_only
```

and the registration lifecycle vocabulary:

```text
planned
active
closed
cancelled
```

Registration identity is the complete immutable `ModuleWorkRef`. Metadata changes create later registration revisions rather than replacing prior history.

Concord’s proposed registration values are compatible with those constraints:

```text
work_kind: collaborative_activity
source record kind: activity
source record module: concord
```

The representative examples use valid Core intent and lifecycle values and preserve registration revisions separately from native Score, manifest, publication, and Meridian histories.

### 6.4 Explicit Registration

The architecture correctly rejects inferred registration.

None of the following should create an Academic Work Registration:

* Activity creation;
* selection of Focus Standards;
* `standards_based` or `mixed` scoring orientation;
* Artifact or page generation;
* Route Registration;
* Review completion;
* Score creation;
* or manifest generation.

This agrees with Core, which does not infer academic intent from module identity, paths, standards, Scores, result files, or printable pages.

The examples collectively demonstrate both sides of the rule:

* registered standards-based, mixed, and local-criteria-only Activities;
* and an evidence-only Activity that exists without automatic registration or publication.

### 6.5 Scoring Orientation and Academic Intent

The separation among these concepts is coherent:

```text
Concord scoring_orientation
    = what kinds of native Concord judgments the Activity may produce

Core academic_intent
    = the broad academic purpose for which the work was registered

Meridian Grade-item membership
    = whether and how selected publications participate in grading
```

For example, a standards-based Activity may be registered as formative, while a mixed Activity may be registered as summative. Neither relationship is derivable from the other.

No duplicated `academic_intent` field should be added to the Concord Activity.

### 6.6 Registration Lifecycle

Concord Activity lifecycle and Core registration lifecycle are separate histories.

A completed or archived Activity does not automatically rewrite its Core registration. Any registration change must occur through an explicit Core registration update that produces a new revision.

Core’s publication service requires an academic-result publication to reference the exact current registration revision at publication time. It rejects publication when the current registration is cancelled. A closed registration remains eligible for publication under the current Core service.

This separation is coherent and does not require automatic lifecycle synchronization.

### 6.7 Producer Work-Root Requirement

Core requires the producer-owned work root to exist before initial registration. Core does not create the Concord Activity directory as a side effect of registration.

The correct workflow is therefore:

```text
create Activity
    -> create or establish its Concord work root
    -> explicitly request Core registration
```

The Concord integration document already describes this ordering correctly.

### 6.8 Findings

#### REG-001 — Registration mapping names a nonexistent Activity field

| Field                        | Value                                                                                                                                                             |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Activity identity and Core registration                                                                                                                           |
| Severity                     | Minor clarification                                                                                                                                               |
| Status                       | Open                                                                                                                                                              |
| Finding                      | ADR 0015 and the Core integration requirements describe `work.class_id = Activity.class_id`, but the Activity contract defines `class_reference`, not `class_id`. |
| Required action              | Replace the mapping with `work.class_id = Activity.class_reference.record_id`, while requiring `class_reference` to identify a Core class.                        |
| Architecture change required | No                                                                                                                                                                |

The Activity field table defines `class_reference`, while the registration prose uses `Activity.class_id`.

#### REG-002 — Concord Activity source binding should be mandatory

| Field                        | Value                                                                                                                                                                                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Activity identity and Core registration                                                                                                                                                                                                                                      |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                          |
| Status                       | Open                                                                                                                                                                                                                                                                         |
| Finding                      | The Concord documents state that the registration “should” include the Activity in `source_records`. Core’s generic model permits an empty `source_records` collection and cannot enforce Concord-specific Activity binding.                                                 |
| Required action              | Require every Concord Academic Work Registration to include exactly one Activity `ModuleRecordRef` whose `module_id` is `concord`, whose `record_kind` is `activity`, and whose `record_id` equals `work.work_id`. Other source records may also be included when justified. |
| Architecture change required | No; this is a Concord producer-contract invariant                                                                                                                                                                                                                            |

Core validates source-record structure and matching module ownership but does not require any source record or enforce that a record is the top-level Activity.

The representative examples already follow the stronger proposed rule.

#### REG-003 — Publication wording should specify the current registration revision

| Field                        | Value                                                                                                                                                                                                                                         |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Activity identity and Core registration                                                                                                                                                                                                       |
| Severity                     | Minor clarification                                                                                                                                                                                                                           |
| Status                       | Open                                                                                                                                                                                                                                          |
| Finding                      | Some Concord prose refers to the “applicable” registration revision. Core’s implemented publication service is more precise: an academic-result publication must reference the exact current registration revision at publication time.       |
| Required action              | Replace ambiguous “applicable registration revision” wording with “the exact current Academic Work Registration revision at publication time.” State separately that later registration revisions do not rewrite earlier Publication Records. |
| Architecture change required | No                                                                                                                                                                                                                                            |

Core enforces current-revision equality and rejects a cancelled current registration.

#### REG-004 — Activity and registration architecture is otherwise coherent

| Field           | Value                                                                                                                                                                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Activity identity and Core registration                                                                                                                                                                                                           |
| Severity        | No issue identified                                                                                                                                                                                                                               |
| Status          | Reviewed                                                                                                                                                                                                                                          |
| Finding         | `activity_id` works coherently as Concord’s `work_id`; registration remains explicit and revisioned; scoring orientation remains distinct from academic intent; and registration remains separate from publication and Meridian Grade membership. |
| Required action | None beyond REG-001 through REG-003.                                                                                                                                                                                                              |

### 6.9 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved Minor clarifications: 3
No-issue findings: 1
```

The Activity identity and Academic Work Registration architecture is suitable for continued foundation review.

The three open findings require wording and producer-invariant corrections, not a redesign of Activity identity, Core registration, or the representative examples.
