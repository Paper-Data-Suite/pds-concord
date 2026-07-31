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
| ESM-001 | Evidence, Review, Moderation, and Scoring | Minor clarification | Resolved | Score basis values do not fully constrain required evidence-link cardinality and rationale. | Define rules for `linked_evidence`, `professional_judgment`, and `mixed_basis` |
| ESM-002 | Evidence, Review, Moderation, and Scoring | Minor clarification | Resolved | Older Evidence Reference descriptions contain relevance and Moderation semantics that belong to Score Evidence Links. | Align ADR 0009 and the initial domain model with the finalized contracts |
| ESM-003 | Evidence, Review, Moderation, and Scoring | Minor clarification | Resolved | ADR 0008 describes Artifact Review too broadly as a generic routed-evidence Review. | Narrow the wording to one Artifact Instance and its routed evidence |
| ESM-004 | Evidence, Review, Moderation, and Scoring | No issue identified | Reviewed | Evidence, Review, Moderation, Score, lineage, correction, publication, and grading remain coherently separated. | None |
| CSS-001 | Criteria, Scales, and Score semantics | Minor clarification | Resolved | Standards-profile membership is stated as advisory rather than required validation. | Make Focus Standard and profile-bound Criterion membership mandatory at configuration and validation boundaries |
| CSS-002 | Criteria, Scales, and Score semantics | Minor clarification | Resolved | Criterion Set and Criterion immutability begins too late and is described inconsistently. | Make scoring semantics immutable when a Criterion Set revision is selected by an Activity |
| CSS-003 | Criteria, Scales, and Score semantics | Minor clarification | Resolved | Scoring Scale levels lack explicit machine-value uniqueness and deterministic-ordering invariants. | Require unique values, unambiguous ordering, and one-level resolution |
| CSS-004 | Criteria, Scales, and Score semantics | No issue identified | Reviewed | Standard/local classification, one-standard semantics, exact Scale interpretation, target distinctions, and the Meridian boundary are coherent. | None |

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

## 7. Evidence, Review, Moderation, and Scoring Review

### 7.1 Review Question

Does the Concord foundation preserve defensible boundaries among evidence, Artifact Review, Moderation, Score Records, Score Evidence Links, non-score dispositions, corrections, publication history, and downstream Meridian results?

### 7.2 Evidence Independence

The foundation correctly treats evidence as a role played by several record types rather than as one universal record.

Permitted evidence sources include:

* Artifact Instances and Pages;
* Attachments;
* Contribution Claims;
* Activity Events;
* teacher observations and rationales;
* ScoreForm results;
* Quillan responses;
* and authorized external records.

A typed Evidence Reference identifies a source without:

* copying it;
* transferring ownership;
* interpreting its meaning automatically;
* creating a Score;
* or authorizing consequential use.

Evidence may exist without:

* Review;
* Moderation;
* a Score;
* academic registration;
* publication;
* Grade inclusion;
* or reporting inclusion.

The representative evidence-only archive demonstrates reviewed and routed evidence without Criteria, Scores, registration, or publication.

### 7.3 Artifact Review Boundary

Artifact Review correctly concerns administrative and evidentiary readiness.

It may determine:

* readability;
* completeness;
* filing;
* Author and Subject attribution;
* privacy;
* relevance;
* correction needs;
* Moderation requirements;
* and readiness for possible scoring consideration.

Artifact Review does not determine:

* performance;
* Criterion satisfaction;
* evidence fairness;
* Score target;
* Score value;
* Grade eligibility;
* or reporting treatment.

A Review outcome such as `ready` means only that evidence may be considered. It does not create, recommend, or populate a Score.

Later Reviews preserve earlier Review history and may supplement, correct, or supersede prior judgments without modifying the retained source.

### 7.4 Moderation Boundary

Moderation correctly evaluates whether and how evidence may be used consequentially.

Moderation may assess:

* reliability;
* fairness;
* credibility;
* relevance;
* conflicting accounts;
* subject-specific applicability;
* qualification;
* and permissible scoring use.

Moderation does not select:

* a Criterion;
* a Score target;
* a governing standard;
* a Scoring Scale;
* a Score value;
* or a Grade consequence.

The following remain evidence-use decisions rather than performance levels:

```text
accepted
accepted_with_qualification
insufficient
disputed
rejected
not_used_for_scoring
```

Evidence requiring Moderation cannot actively support a consequential Score until an applicable Moderation Record permits the represented use.

Rejected evidence may remain preserved historically, but it must not remain an active supporting link for a consequential Score.

### 7.5 Score Boundary

A Score Record remains one teacher-approved judgment about:

* exactly one Criterion;
* exactly one explicit target;
* one exact Scoring Scale revision;
* and one defined Activity context.

A Score remains distinct from:

* its evidence;
* Artifact Author;
* Artifact Subject;
* scorer;
* Group Membership;
* Review;
* Moderation;
* manifest projection;
* Core publication;
* Meridian-derived result;
* proficiency;
* and Grade.

Review readiness and Moderation acceptance do not create a Score.

Group evidence may support an individual Score only when:

* the evidence is relevant to that individual;
* required Moderation permits the use;
* the teacher makes a deliberate individual judgment;
* and the rationale or Score Evidence Link explains the individual relevance.

A Group Score never creates member Scores automatically.

### 7.6 Evidence-to-Score Lineage

The many-to-many evidence relationship is appropriate.

```text
one Score
    -> zero or more deliberate Score Evidence Links

one evidence source
    -> zero or more distinct Scores
```

A Score Evidence Link preserves the specific claim that one source was deliberately considered in one criterion-level judgment.

The link may preserve:

* an evidence locator;
* Subject context;
* relevance description;
* significance;
* applicable Moderation Record;
* lifecycle;
* provenance;
* and supersession.

Link count must not determine Score value or be treated as proof of independent corroboration.

Overlapping provenance layers should not receive redundant links unless each layer has an independent evidentiary purpose.

### 7.7 Non-Score Dispositions

The foundation correctly distinguishes evidence state, contextual exception, and Score disposition.

The initial Score dispositions are:

```text
scored
insufficient_evidence
absent
excused
not_observed
not_applicable
deferred
```

When `disposition = scored`:

* a valid value from the exact Scoring Scale revision is required.

When `disposition != scored`:

* `value` is forbidden;
* zero must not be inferred;
* the lowest scale level must not be inferred;
* and the explicit disposition must be preserved downstream.

Absence of evidence remains distinct from affirmative evidence supporting a negative judgment.

Even affirmative negative evidence does not generate a Score automatically; the teacher must still apply the Criterion, context, Moderation state, and exact Scoring Scale deliberately.

### 7.8 Historical Separation

The following histories remain correctly separate:

```text
source and routing history
Artifact Review history
Moderation history
Score Evidence Link history
native Score supersession
manifest revision
Core publication supersession or withdrawal
Meridian import, calculation, and override history
```

A later Review or Moderation decision does not silently rewrite an earlier Score.

A changed teacher-approved judgment requires a new or superseding Score Record.

A Meridian policy change or override does not revise the Concord Score.

### 7.9 Representative-Example Assessment

The seminar, laboratory, and project examples collectively demonstrate:

* evidence remaining distinct from Review and Score;
* normal teacher-authored evidence without unnecessary Moderation;
* peer and Contribution Claim evidence requiring Moderation;
* accepted-with-qualification use;
* rejected or insufficient evidence without negative scoring;
* one source supporting several Scores;
* one Score using several sources;
* Group evidence supporting individual judgment only through explicit teacher action;
* Group Scores that do not propagate to members;
* `insufficient_evidence`, `absent`, and `deferred` dispositions without values;
* native Score supersession;
* ScoreForm and Quillan evidence lineage;
* and corrections that preserve prior records.

No representative example contradicts the intended evidence, Review, Moderation, or scoring architecture.

### 7.10 Findings

#### ESM-001 — Score basis does not fully constrain evidence-link cardinality

| Field                        | Value                                                                                                                                                                                                                                                                                                                                |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area                         | Scoring and evidence lineage                                                                                                                                                                                                                                                                                                         |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                                                                                  |
| Status                       | Open                                                                                                                                                                                                                                                                                                                                 |
| Finding                      | The contracts define `linked_evidence`, `professional_judgment`, and `mixed_basis`, but they do not fully state which basis values require Score Evidence Links. As written, a `linked_evidence` Score could contain zero links, or a `mixed_basis` Score could omit the rationale representing the professional-judgment component. |
| Required action              | Require at least one active Score Evidence Link for `linked_evidence` and `mixed_basis`; require rationale for `mixed_basis`; and require a zero-link Score to use `professional_judgment`.                                                                                                                                          |
| Architecture change required | No                                                                                                                                                                                                                                                                                                                                   |
| Example changes required     | No; the current examples already follow the intended rules                                                                                                                                                                                                                                                                           |

##### Exact corrections

In `docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`, replace lines 93–99:

> A Score Record may have:
>
> * no Score Evidence Links;
> * one Score Evidence Link;
> * or several Score Evidence Links.
>
> The number of links does not change the Score Record’s core identity.

with:

```markdown
A Score Record may have:

- no Score Evidence Links only when `basis = professional_judgment`;
- one or more Score Evidence Links when `basis = linked_evidence`;
- or one or more Score Evidence Links when `basis = mixed_basis`.

A `mixed_basis` Score must also preserve a rationale for the professional-judgment component.

The number of links does not change the Score Record’s core identity or determine its value.
```

In `docs/design/conceptual-data-contracts.md`, immediately after lines 2342–2346:

> When `basis = professional_judgment` and there are no Score Evidence Links:
>
> * `rationale` is required;
> * scorer provenance is required;
> * and the Activity context must be explicit.

add:

```markdown
When `basis = linked_evidence`:

- at least one active Score Evidence Link is required;
- and `rationale` is optional unless required by workflow policy.

When `basis = mixed_basis`:

- at least one active Score Evidence Link is required;
- and `rationale` is required to preserve the professional-judgment component.

A Score with zero Score Evidence Links must use `basis = professional_judgment`.
```

In `docs/design/initial-concord-domain-model.md`, replace lines 1878–1884:

> A teacher may enter a Score through professional judgment without one controlling Artifact.
>
> When no formal Score Evidence Link exists:
>
> * rationale is required;
> * scorer provenance is required;
> * and the Activity context must be explicit.

with:

```markdown
A teacher may enter a Score through professional judgment without one controlling Artifact.

When `basis = professional_judgment` and no formal Score Evidence Link exists:

- rationale is required;
- scorer provenance is required;
- and the Activity context must be explicit.

When `basis = linked_evidence`:

- at least one active Score Evidence Link is required.

When `basis = mixed_basis`:

- at least one active Score Evidence Link is required;
- and rationale is required to preserve the professional-judgment component.

A Score with zero Score Evidence Links must use `basis = professional_judgment`.
```

#### ESM-002 — Older Evidence Reference descriptions contain Score Evidence Link semantics

| Field                        | Value                                                                                                                                                                                                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area                         | Evidence references and Score Evidence Links                                                                                                                                                                                                                             |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                      |
| Status                       | Open                                                                                                                                                                                                                                                                     |
| Finding                      | ADR 0009 and the initial domain model place relevance description or applicable Moderation state on the Evidence Reference. The finalized contract correctly places deliberate relevance, significance, and the applicable Moderation Record on the Score Evidence Link. |
| Required action              | Align the older descriptions with the finalized Evidence Reference and Score Evidence Link contracts.                                                                                                                                                                    |
| Architecture change required | No                                                                                                                                                                                                                                                                       |
| Example changes required     | No                                                                                                                                                                                                                                                                       |

##### Exact corrections

In `docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`, replace lines 148–156:

> A typed Evidence Reference should identify:
>
> * evidence source type;
> * owning module where applicable;
> * durable source identifier;
> * optional page or evidence location;
> * optional Subject context;
> * optional relevance description;
> * and applicable Moderation state.

with:

```markdown
A typed Evidence Reference should identify:

- evidence source type;
- owning system;
- durable source identifier;
- optional public contract version;
- optional exact source-publication reference;
- optional source locator;
- optional Subject context;
- and optional Moderation requirement.

Relevance description, significance, and the applicable Moderation Record belong to the Score Evidence Link rather than the Evidence Reference.
```

In the same ADR, replace lines 164–174:

> It should be capable of recording:
>
> * durable `score_evidence_link_id`;
> * parent `score_record_id`;
> * typed Evidence Reference;
> * optional evidence locator;
> * relevance or use description;
> * optional significance note;
> * applicable Moderation status or decision reference;
> * creation provenance;
> * and correction or supersession history where required.

with:

```markdown
It should be capable of recording:

- durable `score_evidence_link_id`;
- parent `score_record_id`;
- typed Evidence Reference;
- optional evidence locator;
- optional Subject context;
- required relevance or use description;
- optional significance note;
- applicable Moderation Record reference where required;
- lifecycle status;
- creation provenance;
- and correction or supersession history where required.
```

In `docs/design/initial-concord-domain-model.md`, replace lines 1348–1357:

> An Evidence Reference should identify:
>
> * evidence source kind;
> * owning system;
> * durable source identifier;
> * optional public contract version;
> * optional page or source location;
> * optional Subject context;
> * optional relevance note;
> * and optional Moderation requirement.

with:

```markdown
An Evidence Reference should identify:

- evidence source kind;
- owning system;
- durable source identifier;
- optional public contract version;
- optional exact source-publication reference;
- optional page or source location;
- optional Subject context;
- and optional Moderation requirement.

Relevance description and the applicable Moderation Record belong to the Score Evidence Link for a particular evidence use.
```

#### ESM-003 — ADR 0008 describes Artifact Review as though it were a generic review record

| Field                        | Value                                                                                                                                                                                                                                                                                                      |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Review scope                                                                                                                                                                                                                                                                                               |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                                                        |
| Status                       | Open                                                                                                                                                                                                                                                                                                       |
| Finding                      | ADR 0008 says a Review may examine an Artifact Instance “or other routed evidence,” while the finalized contract defines Artifact Review specifically for one Artifact Instance and its routed evidence. Other source types retain source-owned review state or undergo Concord Moderation as appropriate. |
| Required action              | Narrow the ADR wording to the finalized Artifact Review target.                                                                                                                                                                                                                                            |
| Architecture change required | No                                                                                                                                                                                                                                                                                                         |
| Example changes required     | No                                                                                                                                                                                                                                                                                                         |

##### Exact correction

In `docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`, replace lines 129–131:

> A Review records a human examination of an Artifact Instance or other routed evidence.
>
> Review determines whether the evidence is administratively and evidentially ready for possible use.

with:

```markdown
An Artifact Review records a human examination of one Artifact Instance and its available routed evidence.

Other evidence sources retain their owning record’s review or validation state and may undergo Concord Moderation when consequential use requires it.

Artifact Review determines whether the Artifact and its routed evidence are administratively and evidentially ready for possible use.
```

#### ESM-004 — Evidence, Review, Moderation, and Scoring architecture is coherent

| Field           | Value                                                                                                                                                                                                                                                                                                                                                       |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Evidence, Review, Moderation, and Scoring                                                                                                                                                                                                                                                                                                                   |
| Severity        | No issue identified                                                                                                                                                                                                                                                                                                                                         |
| Status          | Reviewed                                                                                                                                                                                                                                                                                                                                                    |
| Finding         | The foundation consistently separates source evidence, administrative Review, consequential-use Moderation, criterion-level Scoring, evidence lineage, non-score dispositions, native correction, publication, and downstream grading. The representative cases support the architecture without introducing contradictory ownership or automatic judgment. |
| Required action | None beyond ESM-001 through ESM-003.                                                                                                                                                                                                                                                                                                                        |

### 7.11 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Minor clarifications: 3
No-issue findings: 1
```

The evidence, Review, Moderation, and Scoring foundation is suitable for continued review.

The three open findings tighten existing contracts. They do not require new foundational entities, a new ADR, changes to Core, changes to Meridian, or revisions to the representative records.

## 8. Criteria, Scoring Scales, and Score Semantics Review

### 8.1 Review Question

Do Concord’s Criterion, Criterion Set, Scoring Scale, and Score contracts preserve unambiguous standards meaning, exact historical interpretation, valid target semantics, and a clear boundary between contextual producer judgments and Meridian-owned proficiency or Grade calculations?

### 8.2 Standards Profile and Focus Standard Relationship

A `standards_based` or `mixed` Activity uses:

```text
one Core standards_profile_id
    -> one or more ordered focus_standard_ids
    -> one or more standard-backed Criteria
    -> teacher-approved standard-backed Scores
```

Core owns:

* standard identity;
* profile identity;
* profile membership;
* active, inactive, and deprecated status;
* and module-neutral validation.

Concord owns:

* the selection of Focus Standards;
* Activity-specific Criterion definitions;
* Criterion classification;
* Score targets;
* exact Scoring Scale selection;
* and the resulting teacher-approved contextual judgment.

The selected profile is not merely display context. At Activity configuration and validation boundaries, every selected Focus Standard must belong to that profile.

A later change to Core profile membership or standard lifecycle must not silently rewrite historical Concord records.

### 8.3 Criterion Classification

Every scoring Criterion is classified as:

```text
standard_backed
local
```

A standard-backed Criterion:

* has exactly one governing `standard_id`;
* defines how that standard is judged in the Activity context;
* must govern one of the Activity’s ordered Focus Standards;
* and may produce a direct contextual standards Score.

A local Criterion:

* has no governing `standard_id`;
* may carry non-governing alignment metadata;
* and must not produce a direct standards result.

The architecture correctly rejects using one holistic Score as several standards ratings.

When one behavior relates directly to several standards, Concord ordinarily creates separate standard-backed Criteria and separate Score Records. A genuinely holistic Criterion remains local unless a later explicit composite contract is established.

### 8.4 Criterion Set and Criterion Immutability

Criterion Set revisions preserve:

* ordered Criterion membership;
* Criterion classification;
* governing standards;
* target applicability;
* definitions;
* and scoring interpretation.

Once a Criterion Set revision is selected by an Activity, those scoring semantics must not change in place.

A teacher-facing interface may edit an unselected draft configuration, but an Activity must not continue to reference the same Criterion Set and Criterion identities after their academic meaning changes.

Changes to:

* Criterion membership;
* order;
* classification;
* governing or aligned standards;
* definition;
* target applicability;
* or scoring interpretation

require a new Criterion Set revision and new Criterion identities for the changed Criteria.

Historical Scores continue to reference the exact Criterion and Criterion Set revision used for the original judgment.

### 8.5 Scoring Scale Semantics

A Scoring Scale is one exact immutable revision of the values and meanings available to Score Records.

It preserves:

* scale identity;
* lineage;
* revision;
* scale type;
* permitted machine values;
* display labels;
* meanings;
* ordering where applicable;
* and optional nonbinding aggregation guidance.

Every machine value must resolve to exactly one level within the Scale revision.

Two Scales are not equivalent merely because they:

* contain the same number of levels;
* use the same numeric values;
* use similar labels;
* or appear in the same order.

For example:

```text
1 = Developing
2 = Approaching
3 = Meeting
4 = Exceeding
```

is not automatically equivalent to:

```text
1 = Beginning
2 = Developing
3 = Proficient
4 = Advanced
```

Scale mapping, normalization, weighting, and proficiency interpretation remain explicit, versioned Meridian policy.

### 8.6 Score Semantics

A Score Record remains one teacher-approved judgment about:

* exactly one Criterion;
* exactly one target;
* one exact Scoring Scale revision;
* and one defined Activity context.

For a standard-backed Score:

```text
Score
    -> standard-backed Criterion
    -> exactly one governing standard_id
    -> exactly one target
    -> exactly one Scoring Scale revision
```

The direct `standard_id` on the Score is a deliberate historical and interoperability field. It must match the immutable referenced Criterion.

For a local Score:

```text
score_kind: local
standard_id: absent
```

Optional Criterion alignment does not convert that Score into a direct standards result.

### 8.7 Target Compatibility

The Score target must be explicitly permitted by the selected Criterion.

An individual Score may use relevant Group or multi-subject evidence, but it remains an individual teacher judgment.

A Group Score:

* does not create individual Score Records;
* does not copy its value to Group members;
* does not establish equal contribution;
* and does not become individual standards evidence automatically.

A standard-backed Group Score is valid only when:

* the governing standard supports the represented Group-level judgment;
* the Criterion permits a `concord_group` target;
* and the teacher deliberately selects the Group.

The Group target remains visible downstream. Meridian must not silently reinterpret it as a student-target result.

### 8.8 Contextual Score Versus Proficiency

A standard-backed Concord Score is one contextual observation.

It is not automatically:

* mastery;
* final proficiency;
* course-level attainment;
* marking-period performance;
* Grade-item membership;
* an Academic Period result;
* or a course Grade.

Several judgments concerning the same standard may differ by:

* Activity;
* Session;
* target;
* producer module;
* evidence;
* Criterion definition;
* or Scoring Scale revision.

Meridian determines which observations are eligible and how they are selected, mapped, combined, excluded, or reported under an explicit policy.

### 8.9 Representative-Example Assessment

The seminar, laboratory, and project examples collectively demonstrate:

* standard-backed Criteria with exactly one governing standard;
* local Criteria with no governing standard;
* non-governing local alignment;
* exact Criterion and Scale projections;
* individual standards Scores;
* Group standards Scores;
* Group evidence supporting individual judgment only through explicit teacher action;
* standard-backed and local Scores coexisting without semantic merging;
* distinct standards and local Scales;
* non-score dispositions without values;
* and contextual Scores that are not presented as proficiency or Grades.

No representative example requires a new scoring entity or contradicts the intended Criterion, Scale, target, or Score architecture.

### 8.10 Findings

#### CSS-001 — Standards-profile membership is stated as advisory

| Field                            | Value                                                                                                                                                                                                                                                                                                                                               |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Standards profile and Focus Standard validation                                                                                                                                                                                                                                                                                                     |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                                                                                                 |
| Status                           | Open                                                                                                                                                                                                                                                                                                                                                |
| Finding                          | Several governing documents say that selected Focus Standards or profile-bound Criteria “should” belong to the selected standards profile. Core owns profile-membership validation, and the Activity contract describes the profile as the source of the Focus Standards. Membership must therefore be a validation requirement rather than advice. |
| Required action                  | Replace advisory profile-membership language with mandatory validation language while preserving historical records when later Core profile or lifecycle state changes.                                                                                                                                                                             |
| Architecture change required     | No                                                                                                                                                                                                                                                                                                                                                  |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                                                                                                  |
| Example changes required         | No                                                                                                                                                                                                                                                                                                                                                  |

##### Exact corrections

In `docs/decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md`, line 335, replace:

> `* every selected standard should belong to the selected profile;`

with:

```markdown
* every selected standard must belong to the selected profile when the Activity is configured or revalidated;
```

After the Focus Standard rules, add:

```markdown
Later profile-membership changes, inactivity, or deprecation must be reported explicitly without mutating historical Activity, Criterion, or Score records.
```

In `docs/design/conceptual-data-contracts.md`, line 1226, replace:

> `* Focus Standards should belong to the selected profile.`

with:

```markdown
* Every Focus Standard must belong to the selected profile when the Activity is configured or revalidated.
* Later profile-membership changes, inactivity, or deprecation do not rewrite historical Activity, Criterion, or Score records.
```

In the same document, line 2087, replace:

> `* When standards_profile_id is present, each standard-backed Criterion should govern a standard in that profile.`

with:

```markdown
* When `standards_profile_id` is present, each standard-backed Criterion must govern a standard in that profile.
```

In `docs/design/initial-concord-domain-model.md`, line 736, replace:

> `* each Focus Standard should belong to the selected profile;`

with:

```markdown
* each Focus Standard must belong to the selected profile when the Activity is configured or revalidated;
```

After the Criterion Set classification rules, add:

```markdown
When a Criterion Set declares Core standards-profile context, every standard-backed Criterion in that Set must govern a standard belonging to that profile.
```

#### CSS-002 — Criterion immutability begins too late and is described inconsistently

| Field                            | Value                                                                                                                                                                                                                                                                                                                                                            |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Criterion and Criterion Set revision semantics                                                                                                                                                                                                                                                                                                                   |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                                                                                                              |
| Status                           | Open                                                                                                                                                                                                                                                                                                                                                             |
| Finding                          | The contracts call Criterion Sets immutable revisions but state that a Set becomes immutable only when selected by an Activity that “produces Scores,” while an individual Criterion becomes immutable only when used by a Score. This leaves room for an Activity’s configured Criteria or generated scoring materials to change before the first Score exists. |
| Required action                  | Make Criterion Set membership, order, and member Criterion scoring semantics immutable once the Set revision is selected by an Activity.                                                                                                                                                                                                                         |
| Architecture change required     | No                                                                                                                                                                                                                                                                                                                                                               |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                                                                                                               |
| Example changes required         | No                                                                                                                                                                                                                                                                                                                                                               |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, line 2088, replace:

> `* A Criterion Set becomes immutable once selected by an Activity that produces Scores.`

with:

```markdown
* Once a Criterion Set revision is selected by an Activity, its Criterion membership, order, and member Criterion scoring semantics are immutable.
```

In the same document, line 2181, replace:

> `* A Criterion used by a Score is immutable.`

with:

```markdown
* A Criterion’s classification, governing or aligned standards, definition, target applicability, and scoring interpretation become immutable when its parent Criterion Set revision is selected by an Activity.
```

Retain the following rule that a semantic change creates a new Criterion identity and Criterion Set revision.

In `docs/design/initial-concord-domain-model.md`, line 1612, replace:

> `* A Criterion Set becomes immutable once selected by an Activity that produces Scores.`

with:

```markdown
* Once a Criterion Set revision is selected by an Activity, its Criterion membership, order, and member Criterion scoring semantics are immutable.
```

In `docs/decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md`, line 504, replace:

> `Criterion Sets and Criteria used by Scores remain immutable under the existing historical-preservation decisions.`

with:

```markdown
Once a Criterion Set revision is selected by an Activity, its membership, order, and member Criterion scoring semantics are immutable under the existing historical-preservation decisions.
```

In the same section, replace:

> `requires a new Criterion revision or identity under the later finalized contract.`

with:

```markdown
requires a new Criterion identity in a new Criterion Set revision.
```

#### CSS-003 — Scale levels lack explicit uniqueness and ordering invariants

| Field                            | Value                                                                                                                                                                                                                                                       |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Scoring Scale interpretation                                                                                                                                                                                                                                |
| Severity                         | Minor clarification                                                                                                                                                                                                                                         |
| Status                           | Open                                                                                                                                                                                                                                                        |
| Finding                          | The contracts require permitted Scale values and exact revision references but do not explicitly require machine values to be unique or ordering to be deterministic. A duplicated machine value could make one Score value resolve to more than one level. |
| Required action                  | Require at least one level, unique machine values within each Scale revision, and deterministic nonduplicated ordering where ordering applies.                                                                                                              |
| Architecture change required     | No                                                                                                                                                                                                                                                          |
| Core or Meridian change required | No                                                                                                                                                                                                                                                          |
| Example changes required         | No; all represented Scale values and order positions are already unique                                                                                                                                                                                     |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, lines 2213–2219, replace:

> Each level should define:
>
> * machine value;
> * display label;
> * meaning;
> * ordering where applicable;
> * and optional description.

with:

```markdown
Each level must define:

* a machine value unique within the Scoring Scale revision;
* a display label;
* a meaning;
* ordering when required by the `scale_type`;
* and an optional description.
```

Add to the Scale invariants:

```markdown
* A Scoring Scale revision contains at least one level.
* Each machine value is unique within the exact Scale revision.
* A scored value resolves to exactly one level.
* Ordering, when present, is deterministic and contains no duplicate positions.
```

In the Manifest Scoring Scale Projection section of the same document, lines 2647–2653, replace:

> Each projected level must preserve, as applicable:
>
> * machine value;
> * display label;
> * meaning;
> * ordering;
> * and description.

with:

```markdown
Each projected level must preserve, as applicable:

* the unique machine value from the native Scale revision;
* display label;
* meaning;
* exact ordering;
* and description.
```

Add to the projection invariants:

```markdown
* Projected machine values remain unique within the projected Scale revision.
* A projected scored value resolves to exactly one projected level.
```

In `docs/design/initial-concord-domain-model.md`, after lines 1730–1743 describing the Scoring Scale contents, add:

```markdown
Each Scoring Scale revision must contain at least one level. Machine values must be unique within the revision, and ordering must be deterministic and duplicate-free when the Scale type uses ordering. A scored value must resolve to exactly one level.
```

In `docs/decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md`, after lines 618–625 describing what the Scale preserves, add:

```markdown
Within one Scoring Scale revision:

* at least one level is required;
* every machine value must be unique;
* a scored value must resolve to exactly one level;
* and ordering must be deterministic and duplicate-free when applicable.
```

#### CSS-004 — Criterion, Scale, target, and Score semantics are otherwise coherent

| Field           | Value                                                                                                                                                                                                                                                                                                                  |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Criteria, Scoring Scales, and Score semantics                                                                                                                                                                                                                                                                          |
| Severity        | No issue identified                                                                                                                                                                                                                                                                                                    |
| Status          | Reviewed                                                                                                                                                                                                                                                                                                               |
| Finding         | The foundation consistently preserves standard-backed versus local classification, exactly one governing standard, exact Scale revision semantics, explicit target compatibility, Group-versus-individual distinctions, and the boundary between contextual Concord Scores and Meridian-derived proficiency or Grades. |
| Required action | None beyond CSS-001 through CSS-003.                                                                                                                                                                                                                                                                                   |

### 8.11 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Minor clarifications: 3
No-issue findings: 1
```

The Criteria, Scoring Scales, and Score semantics foundation is suitable for continued review.

The three open findings strengthen validation and reproducibility. They do not require:

* a new foundational record type;
* a new ADR;
* changes to Core;
* changes to Meridian;
* or revisions to the representative example records.
