# Concord Foundation Review

**Status:** Complete  
**Verdict:** APPROVED WITH NONBLOCKING FOLLOW-UP  
**Issue:** #13 — Conduct a Skeptical Foundation Review  
**Branch:** `13-conduct-skeptical-foundation-review`

**Historical context:** This document preserves the review evidence and wording
as evaluated during issue #13. The review is complete, ADR 0015 is Accepted, and
the released implementation baseline is now `pds-core` v0.6.0. Statements inside
individual findings about then-proposed decisions or then-unreleased contracts
remain historical evidence rather than current project status.

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
| OWN-002 | Module ownership and authority | Minor clarification | Resolved | Verify that the Core catalog remains derived and publication never implies grading or reporting inclusion. | Check during publication and Meridian reviews |
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
| MPA-001 | Manifest and publication architecture | Minor clarification | Resolved | Concord publication source identity is not fully constrained across `work`, `source_record`, `source_activity`, and `activity_context`. | Require exact Activity and class identity agreement |
| MPA-002 | Manifest and publication architecture | Minor clarification | Resolved | Idempotency descriptions omit replay-defining publication metadata enforced by Core. | Align replay identity with Core’s complete immutable request comparison |
| MPA-003 | Manifest and publication architecture | Minor clarification | Resolved | Capability declarations are not fully connected to required manifest projections. | Define conditional capability and Standards Result Projection rules |
| MPA-004 | Manifest and publication architecture | No issue identified | Reviewed | Producer authority, immutable binding, Core ownership, catalog nonauthority, and downstream separation are coherent. | None |
| RSW-001 | Revision, supersession, and withdrawal | Minor clarification | Resolved | Native same-type supersession chains lack complete shared invariants, and Score continuity is underconstrained. | Require explicit, acyclic, unbranched chains and Score-specific continuity rules |
| RSW-002 | Revision, supersession, and withdrawal | Minor clarification | Resolved | Correction Record replacement semantics are inconsistent when no replacement exists, and Correction Records cannot explicitly supersede earlier Correction Records. | Make replacement conditional and define correction-without-replacement behavior |
| RSW-003 | Revision, supersession, and withdrawal | Minor clarification | Resolved | Withdrawal does not state that a withdrawn series head leaves no currently selectable publication and does not reactivate its predecessor. | Document no-fallback selection and successor behavior |
| RSW-004 | Revision, supersession, and withdrawal | No issue identified | Reviewed | Native correction, manifest revision, publication supersession, withdrawal, and downstream histories remain coherently separated. | None |
| CPL-001 | Cross-producer evidence lineage | Minor clarification | Resolved | Exact source revision is assigned inconsistently between the general External Reference and the particular evidence use. | Place exact source-version identity on the Evidence Reference and Score Evidence Link |
| CPL-002 | Cross-producer evidence lineage | Minor clarification | Resolved | Direct source-owned and indirect Concord External Reference forms are both permitted but not distinguished. | Define one unambiguous representation form per Score Evidence Link |
| CPL-003 | Cross-producer evidence lineage | Minor clarification | Resolved | Exact source-publication conditionality, duplicate-field equality, source-record membership, and later lifecycle effects are underdefined. | Require exact source-version sufficiency and publication-integrity rules |
| CPL-004 | Cross-producer evidence lineage | Follow-up implementation concern | Tracked | Released ScoreForm and Quillan runtimes do not yet expose the complete source-publication contracts represented by the conceptual examples. | Stabilize public record, manifest, publication, and adapter contracts before runtime integration |
| CPL-005 | Cross-producer evidence lineage | No issue identified | Reviewed | Ownership, explicit judgment, Moderation, privacy, history, and Meridian overlap authority are coherent. | None |
| MCB-001 | Meridian consumption boundary | Minor clarification | Resolved | Meridian import provenance is advisory and omits parts of the exact publication observation required for reproducibility. | Make complete import provenance mandatory |
| MCB-002 | Meridian consumption boundary | Minor clarification | Resolved | Withdrawal is treated as a general import-validity failure rather than a current-selection restriction. | Separate historical import from ordinary current eligibility |
| MCB-003 | Meridian consumption boundary | Minor clarification | Resolved | Non-student Score targets lack an explicit rule governing student-level Meridian eligibility. | Preserve non-student targets and forbid synthesized student targets |
| MCB-004 | Meridian consumption boundary | Minor clarification | Resolved | Scale mapping is not explicitly bound to the exact producer Scale identity, revision, and level semantics. | Define exact source-scale mapping identity |
| MCB-005 | Meridian consumption boundary | No issue identified | Reviewed | Producer authority, Meridian policy ownership, Academic Periods, overrides, and reporting remain coherently separated. | None |
| PDM-001 | Privacy and data minimization | Minor clarification | Resolved | Direct privacy classifications and the `inherited` and `external_policy` resolution modes lack conditional-reference and effective-policy rules. | Require effective privacy resolution before access or publication |
| PDM-002 | Privacy and data minimization | Minor clarification | Resolved | Manifest-level privacy is not explicitly constrained by every included Score, evidence-lineage, and Moderation projection. | Define conservative manifest privacy aggregation |
| PDM-003 | Privacy and data minimization | Minor clarification | Resolved | Published narrative, display metadata, registration text, and External Locators lack explicit field-level minimization rules. | Prohibit PII, sensitive narrative, secrets, signed access material, and unsafe paths |
| PDM-004 | Privacy and data minimization | Follow-up implementation concern | Tracked | Coordinated retention and legal-deletion behavior across Core, Concord, Meridian, reports, catalogs, and backups remains undefined. | Establish suite-level retention, revocation, redaction, withdrawal, and deletion policy before production |
| PDM-005 | Privacy and data minimization | No issue identified | Reviewed | Record-specific privacy, minimized projections, historical restriction, redaction, and publication-versus-authorization boundaries are coherent. | None |
| REC-001 | Representative-example consistency | Major revision | Resolved | All six exact manifest byte blocks include top-level example-only `record_owner` and `record_kind` fields excluded by the shared notation and absent from the governing manifest contract. | Remove the two fields, recalculate six digests, update six Core Publication Records, and rerun validation |
| REC-002 | Representative-example consistency | Minor clarification | Resolved | The README and cross-example validation retain obsolete provisional-reference and source-publication wording for matters resolved by issue #13. | Replace provisional language with the finalized Score-Target, Core Publication, and source-version contracts |
| REC-003 | Representative-example consistency | Minor clarification | Resolved | The seminar, laboratory, and project Meridian sections retain abbreviated import-provenance lists superseded by MCB-001. | Add the complete mandatory publication observation to each example |
| REC-004 | Representative-example consistency | Minor clarification | Resolved | The README, seminar, and laboratory descriptions say the project exercises withdrawal even though it only provides bounded withdrawal semantics. | Correct the coverage descriptions |
| REC-005 | Representative-example consistency | No issue identified | Reviewed | The representative cases continue to cover the required semantic boundaries without case-specific foundational records. | None |
| ADR-001 | ADR 0015 disposition | No issue identified | Reviewed | ADR 0015 establishes a coherent producer-manifest, Core-publication, and Meridian-consumption boundary and should govern subsequent serialized-contract and implementation work. | Accept ADR 0015 |
| ADR-002 | ADR 0015 disposition | Minor clarification | Resolved | The ADR remains Proposed and retains stale future-tense governance and follow-up language after completion of the skeptical review. | Mark the ADR Accepted and distinguish implementation follow-up from settled architecture |
| ADR-003 | ADR 0015 disposition | Minor clarification | Resolved | The ADR contains one malformed code fence and one malformed Meridian validation bullet. | Repair the Markdown and list punctuation |
| PDS-001 | PDS2 routing and retained-source ownership | No issue identified | Reviewed | Artifact Pages, route identity, QR minimality, Core-retained scans, Concord Scan References, and routing independence remain coherently separated and compatible with the released Core routing baseline. | None |
| DOM-001 | Domain cardinality and identity | No issue identified | Reviewed | Activity, Session, Group, Membership, Author, Subject, Score, evidence-link, Criterion, Scale, and publication-series cardinalities are explicit and contain no unresolved hidden one-to-one assumption. | None |
| OPT-001 | Optionality and domain creep | No issue identified | Reviewed | Optional Activity structures remain conditional; evidence-only and local-criteria-only Activities remain valid without unrelated standards, scoring, publication, or project-management structures. | None |
| CMP-001 | Released-versus-proposed compatibility | No issue identified | Reviewed | Documentation distinguishes the released Core routing baseline from unreleased registry publication architecture and prohibits unsupported runtime compatibility claims. | None |

## 4. Required Review-Area Coverage

| Issue #13 area | Required review area | Primary report coverage |
|---:|---|---|
| 1 | Module ownership | Section 5 |
| 2 | Activity identity and Core registration | Section 6 |
| 3 | PDS2 routing and retained-source ownership | Section 16.2 |
| 4 | Domain cardinality and identity | Section 16.3, supported by Sections 6–10 and 14 |
| 5 | Evidence, Review, Moderation, and Scoring | Section 7 |
| 6 | Standards and local scoring | Section 8 |
| 7 | Concord Academic Result Manifest | Section 9 |
| 8 | Core Publication Records | Section 9 |
| 9 | Revision, correction, supersession, and withdrawal | Section 10 |
| 10 | Cross-producer evidence lineage | Section 11 |
| 11 | Meridian consumption boundary | Section 12 |
| 12 | Privacy and data minimization | Section 13 |
| 13 | Optionality and domain creep | Section 16.4, supported by Section 14 |
| 14 | Example validity | Section 14 |
| 15 | Released-versus-proposed compatibility | Sections 15.5, 16.5, and 17.7 |

ADR 0015 disposition is recorded in Section 15.

The required adversarial-scenario matrix is recorded in Section 16.6.

The final foundation verdict is recorded in Section 17.

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
| Status          | Resolved                                                                                                                                                                                                                                                                                           |
| Finding         | The architecture treats the Core publication catalog as derived and treats publication as separate from grading eligibility. These rules are present in the current design but are important enough to verify consistently in every governing document that discusses publication consumption. |
| Required action | During the publication-document review, confirm that no document treats the Core catalog as authoritative or implies that publication automatically creates Grade eligibility, Academic Period membership, or reporting inclusion.                                                             |

### 5.8 Ownership Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 1
Follow-up implementation concerns: 0
```

The proposed ownership model is suitable for continued foundation review.

Finding `OWN-002` was resolved during the manifest and publication review. Core and Concord consistently treat the registry catalog as derived and nonauthoritative, and publication does not create Grade eligibility, Academic Period membership, or reporting inclusion.

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
| Status                       | Resolved                                                                                                                                                              |
| Finding                      | ADR 0015 and the Core integration requirements describe `work.class_id = Activity.class_id`, but the Activity contract defines `class_reference`, not `class_id`. |
| Required action              | Replace the mapping with `work.class_id = Activity.class_reference.record_id`, while requiring `class_reference` to identify a Core class.                        |
| Architecture change required | No                                                                                                                                                                |

The Activity field table defines `class_reference`, while the registration prose uses `Activity.class_id`.

#### REG-002 — Concord Activity source binding should be mandatory

| Field                        | Value                                                                                                                                                                                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Activity identity and Core registration                                                                                                                                                                                                                                      |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                          |
| Status                       | Resolved                                                                                                                                                                                                                                                                         |
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
| Status                       | Resolved                                                                                                                                                                                                                                          |
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
Resolved minor clarifications: 3
No-issue findings: 1
```

The Activity identity and Academic Work Registration architecture is suitable for continued foundation review.

The three resolved findings required wording and producer-invariant corrections, not a redesign of Activity identity, Core registration, or the representative examples.

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
| Status                       | Resolved                                                                                                                                                                                                                                                                                                                                 |
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
| Status                       | Resolved                                                                                                                                                                                                                                                                     |
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
| Status                       | Resolved                                                                                                                                                                                                                                                                                                       |
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
Resolved minor clarifications: 3
No-issue findings: 1
```

The evidence, Review, Moderation, and Scoring foundation is suitable for continued review.

The three resolved findings tighten existing contracts. They do not require new foundational entities, a new ADR, changes to Core, changes to Meridian, or revisions to the representative records.

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
| Status                           | Resolved                                                                                                                                                                                                                                                                                                                                                |
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
| Status                           | Resolved                                                                                                                                                                                                                                                                                                                                                             |
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
| Status                           | Resolved                                                                                                                                                                                                                                                        |
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
Resolved minor clarifications: 3
No-issue findings: 1
```

The Criteria, Scoring Scales, and Score semantics foundation is suitable for continued review.

The three resolved findings strengthen validation and reproducibility. They do not require:

* a new foundational record type;
* a new ADR;
* changes to Core;
* changes to Meridian;
* or revisions to the representative example records.

## 9. Manifest and Publication Architecture Review

### 9.1 Review Question

Does the Concord manifest and Core publication architecture preserve producer authority, exact immutable identity, reproducible interpretation, truthful discovery metadata, safe publication workflow, and separation from grading and reporting?

### 9.2 Authority Model

The architecture correctly separates three authoritative layers:

```text
Concord canonical records
    -> Concord-owned immutable manifest revision
    -> Core-owned immutable Publication Record
    -> Meridian-owned policy interpretation
```

Concord remains authoritative for:

* Activity context;
* Criterion and Scoring Scale meaning;
* Score Records;
* evidence-use lineage;
* Moderation;
* native supersession;
* manifest schema;
* manifest contents;
* and manifest revision assignment.

Core remains authoritative for:

* Publication Record identity;
* publication schema;
* publication kind and shared capabilities;
* safe manifest-path validation;
* SHA-256 binding;
* publication-series validation;
* publication idempotency;
* supersession;
* withdrawal;
* canonical registry persistence;
* and the derived discovery catalog.

Meridian remains authoritative for:

* publication eligibility;
* Grade-item membership;
* Score and evidence selection;
* scale mapping;
* standards proficiency;
* Academic Period membership;
* Grades;
* overrides;
* and reports.

The manifest does not transfer ownership of Concord records to Core. The Publication Record does not make the manifest a Core-owned academic result. Meridian interpretation does not mutate either source.

### 9.3 Manifest Identity and Scope

One Concord Academic Result Manifest revision is identified by:

```text
work
record_set_id
record_set_revision
manifest_contract_version
exact manifest bytes
```

The initial manifest series is scoped to exactly one Concord Activity work context:

```text
module_id + class_id + activity_id
```

It must not become an implicit:

* cross-Activity aggregate;
* class-wide aggregate;
* course aggregate;
* Academic Period aggregate;
* or school-year aggregate.

The stable `record_set_id` identifies one logical publication series within the Activity. It remains distinct from:

* `activity_id`;
* `score_record_id`;
* `publication_id`;
* manifest path;
* Grade-item identity;
* and Academic Period identity.

The manifest remains reproducible from Concord’s canonical records and preserves every projection required to interpret its included Scores.

### 9.4 Required Identity Agreement

For initial Concord academic-result publication, the following identities must agree:

```text
Publication Record work
Manifest work
Publication Record source_record
Manifest source_activity
Manifest activity_context
```

The required relationship is:

```text
work.module_id = concord
source_record.module_id = concord
source_record.record_kind = activity
source_record.record_id = work.work_id
manifest.source_activity = source_record
manifest.activity_context.activity_id = work.work_id
manifest.activity_context.class_id = work.class_id
```

Core’s generic Publication Record contract cannot enforce all of these Concord-specific joins. Concord must validate them before submitting the publication request.

### 9.5 Manifest Interpretation

A manifest must contain or expose enough immutable producer meaning to interpret every included Score independently of mutable Concord configuration.

That includes:

* the Activity interpretation snapshot;
* every referenced Criterion;
* every referenced Scoring Scale revision;
* Score disposition and conditional value;
* target identity;
* standard-backed versus local classification;
* native supersession state;
* deliberate evidence-use lineage;
* and required Moderation state.

A bare Criterion ID or Scoring Scale ID is insufficient when the consumer cannot otherwise resolve the exact immutable semantics.

Local Scores may appear in the broader manifest but remain excluded from the direct standards-result subset.

Non-score dispositions remain explicit and contain no substituted value.

### 9.6 Publication Binding

The Core Publication Record identifies:

* the complete `ModuleWorkRef`;
* Concord source Activity;
* publication kind;
* shared capabilities;
* record-set identity and revision;
* manifest contract version;
* exact workspace-relative path;
* SHA-256 digest;
* publication time;
* exact registration revision current at publication time;
* and optional predecessor publication.

The digest binds the Publication Record to the exact manifest bytes.

The Publication Record is not:

* a copy of the manifest;
* a mutable pointer to current Concord state;
* an interpretation of Score meaning;
* authorization to inspect all manifest contents;
* Grade eligibility;
* or a report.

An unpublished manifest file remains unpublished even when it is otherwise valid.

### 9.7 Capability Semantics

Core capabilities are discovery metadata. Concord must declare them truthfully for the exact manifest revision.

For the initial Concord contract:

#### `criterion_scores`

This capability is required when the manifest contains one or more Criterion-level Score projections or non-score dispositions.

#### `standards_ratings`

This capability is required when the manifest contains one or more standard-backed Score projections or standard-backed non-score dispositions.

When it is declared:

* the Standards Result Projection is required;
* it must be nonempty;
* and it must correspond exactly to the manifest’s standard-backed Score subset.

When no standard-backed result exists:

* `standards_ratings` must be omitted;
* and the Standards Result Projection may be absent or explicitly empty.

#### `moderated_scores`

This capability is required when interpretation of at least one included consequential Score depends on projected Moderation state.

It must be omitted when the manifest contains no such Moderation-dependent Score.

Capabilities do not:

* define the complete manifest schema;
* guarantee completeness for every target;
* authorize access;
* create Grade eligibility;
* or normalize producer meaning.

### 9.8 Publication Workflow

The required workflow remains:

```text
validate native records
    -> determine exact projection
    -> assign manifest revision
    -> generate complete bytes
    -> validate manifest contract
    -> write new revision-addressed file
    -> durably close file
    -> calculate SHA-256 digest
    -> submit complete publication request
    -> Core validates registration, envelope, path, and digest
    -> Core creates immutable Publication Record
    -> catalog update or later rebuild
```

A valid native Score remains valid if publication fails.

If canonical Publication Record creation succeeds but the derived catalog update fails:

* publication remains successful;
* the manifest must not be rewritten;
* the Publication Record remains authoritative;
* and catalog rebuild may restore discovery.

### 9.9 Exact Replay and Contradictory Revision Reuse

Idempotent replay requires equality across the complete immutable publication request:

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

For a superseding publication, it must equal the expected current predecessor.

Core-owned `publication_id` and `published_at` are generated publication results rather than replay-request identity fields.

Any contradictory reuse of the same logical record-set revision is an integrity failure. Changed content or changed publication semantics require a new manifest revision rather than mutation or ordinary replay.

### 9.10 Catalog and Downstream Nonauthority

The Core catalog is derived, rebuildable, and nonauthoritative.

It cannot:

* create a registration;
* create a Publication Record;
* determine publication-series head independently;
* supersede a publication;
* withdraw a publication;
* authorize access;
* or determine Meridian eligibility.

Publication consistently remains distinct from:

* Grade-item membership;
* standards-evidence eligibility;
* Academic Period membership;
* proficiency;
* Grade calculation;
* overrides;
* and reports.

Finding `OWN-002` is therefore resolved by this review.

### 9.11 Representative-Example Assessment

The representative examples collectively demonstrate:

* six complete immutable manifest byte sequences;
* exact SHA-256 agreement;
* work-scoped revision-addressed paths;
* stable record-set identity;
* one-revision and multi-revision series;
* exact Criterion and Scale projections;
* standard-backed and local Score publication;
* standards-only subsets;
* non-score dispositions without values;
* cross-producer evidence lineage;
* Moderation projection;
* truthful capability combinations;
* publication supersession;
* registration-revision preservation;
* derived-catalog nonauthority;
* and publication without automatic Grade or Academic Period membership.

No representative record requires an architectural redesign.

The examples already conform to the stronger identity, replay, and capability rules identified below.

### 9.12 Findings

#### MPA-001 — Concord publication source identity is not fully constrained

| Field                            | Value                                                                                                                                                                                                                                                                                                                        |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Manifest and Publication Record identity                                                                                                                                                                                                                                                                                     |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                                                                          |
| Status                           | Resolved                                                                                                                                                                                                                                                                                                                         |
| Finding                          | The documents require a Concord Activity source record but do not consistently require exact agreement among `work`, Publication Record `source_record`, manifest `source_activity`, and manifest `activity_context`. Core’s generic contract validates only module ownership and cannot enforce all Concord-specific joins. |
| Required action                  | Add explicit Concord producer invariants requiring every identity representation to identify the same Activity and class.                                                                                                                                                                                                    |
| Architecture change required     | No                                                                                                                                                                                                                                                                                                                           |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                                                                           |
| Example changes required         | No                                                                                                                                                                                                                                                                                                                           |

##### Exact corrections

In `docs/decisions/0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md`, line 998, replace:

> For Concord, `source_record` should identify the Activity:

With:

```markdown
For initial Concord use, `source_record` is required and must identify the same Activity represented by the Publication Record’s `work`, the manifest’s `source_activity`, and the manifest’s `activity_context`.
```

After the existing `source_record` YAML block, add:

````markdown
The following identities must agree:

```text
source_record.module_id = concord = work.module_id
source_record.record_kind = activity
source_record.record_id = work.work_id
manifest.source_activity = source_record
manifest.activity_context.activity_id = work.work_id
manifest.activity_context.class_id = work.class_id
````

Concord must validate these producer-specific relationships before requesting Core publication.

````

In `docs/design/conceptual-data-contracts.md`, replace manifest invariants lines 2577–2579:

> The manifest belongs to exactly one Concord Activity work context.  
> `work.module_id` is `concord`.  
> `work.work_id` equals `source_activity.record_id` and the Activity’s `activity_id`.

With:

```markdown
* The manifest belongs to exactly one Concord Activity work context.
* `work.module_id` and `source_activity.module_id` are `concord`.
* `source_activity.record_kind` is `activity`.
* `work.work_id` equals `source_activity.record_id` and `activity_context.activity_id`.
* `work.class_id` equals `activity_context.class_id`.
````

In the same document, after the source-record block at lines 3058–3065, add:

```markdown
The Publication Record’s `source_record` must equal the manifest’s `source_activity`.

Its `record_id` must equal `work.work_id`, and the manifest Activity context must identify the same `work.class_id` and `work.work_id`.
```

In `docs/design/pds-core-integration-requirements.md`, after workflow step 1 at line 1489, add:

```markdown
For initial Concord publication, the submitted source Activity reference must equal the manifest’s `source_activity`; its `record_id` must equal `work.work_id`; and the manifest Activity context must identify the same `work.class_id` and `work.work_id`.
```

#### MPA-002 — Idempotency descriptions omit replay-defining metadata

| Field                            | Value                                                                                                                                                                                                                                                                      |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Publication idempotency                                                                                                                                                                                                                                                    |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                        |
| Status                           | Resolved                                                                                                                                                                                                                                                                       |
| Finding                          | Concord documentation lists only work, record-set identity, path, contract version, and digest as replay identity. Core actually compares the complete immutable request, including source record, publication kind, capabilities, registration revision, and predecessor. |
| Required action                  | Align all idempotency descriptions with Core’s exact replay comparison.                                                                                                                                                                                                    |
| Architecture change required     | No                                                                                                                                                                                                                                                                         |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                         |
| Example changes required         | No                                                                                                                                                                                                                                                                         |

##### Exact corrections

In `docs/decisions/0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md`, replace the duplicate and malformed idempotency material immediately before `## Manifest Revision` with:

````markdown
## Idempotency

Repeating the same publication request must return or reconcile to the existing Core Publication Record when all of the following are unchanged:

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
````

In `docs/design/examples/cross-example-validation.md`, replace the obsolete six-field summary under `### 20.1 Idempotent replay` with:

````markdown
### 20.1 Idempotent replay

Each publication example requires an identical replay request to preserve:

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

For a superseding publication, it identifies the exact expected predecessor.

An exact replay returns or recognizes the existing logical Publication Record rather than creating a duplicate.

Any difference in these request fields for the same logical record-set revision is an integrity conflict.
````

The corresponding replay rules in `conceptual-data-contracts.md`, the representative-examples `README.md`, and `pds-core-integration-requirements.md` were aligned during the same finding resolution.

#### MPA-003 — Capability and projection conditionality is incomplete

| Field                            | Value                                                                                                                                                                                                                                                                                                      |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Publication capabilities and manifest projections                                                                                                                                                                                                                                                          |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                                                        |
| Status                           | Resolved                                                                                                                                                                                                                                                                                                       |
| Finding                          | The documents require truthful capabilities but do not fully state the bidirectional conditions connecting capability declarations to actual Score, standards, and Moderation projections. The Standards Result Projection is currently labeled merely optional even when `standards_ratings` is declared. |
| Required action                  | Define exact conditional rules for `criterion_scores`, `standards_ratings`, `moderated_scores`, and the Standards Result Projection.                                                                                                                                                                       |
| Architecture change required     | No                                                                                                                                                                                                                                                                                                         |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                                                         |
| Example changes required         | No                                                                                                                                                                                                                                                                                                         |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, line 2510, replace:

> `standards_result_projection` | Optional | Direct standards-only subset

With:

```markdown
| `standards_result_projection` | Conditional | Required and nonempty when standard-backed Score projections are present; otherwise absent or explicitly empty |
```

In the same document, after the capability descriptions at lines 3042–3046, add:

```markdown
For the initial Concord manifest contract:

* `criterion_scores` is required when any Criterion-level Score projection or non-score disposition is present;
* `standards_ratings` is required when any standard-backed Score projection or standard-backed non-score disposition is present;
* when `standards_ratings` is declared, the Standards Result Projection is required, nonempty, and exactly represents the standard-backed subset;
* `moderated_scores` is required when interpretation of an included consequential Score depends on projected Moderation state;
* and each capability must be omitted when its represented feature is absent.
```

In ADR 0015, after line 945:

> Capability declaration must be truthful for the exact manifest revision.

Add the same five conditional rules.

In `docs/design/examples/README.md`, replace the examples at lines 3097–3102 with:

```markdown
For the initial Concord manifest contract:

* include `criterion_scores` when any Criterion-level Score projection or non-score disposition is present;
* include `standards_ratings` when any standard-backed Score projection or disposition is present;
* when `standards_ratings` is included, require a nonempty Standards Result Projection that exactly represents the standard-backed subset;
* include `moderated_scores` when interpretation of at least one included consequential Score depends on projected Moderation state;
* omit each capability when its represented feature is absent.
```

#### MPA-004 — Manifest and publication architecture is otherwise coherent

| Field           | Value                                                                                                                                                                                                                                                               |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Manifest and publication architecture                                                                                                                                                                                                                               |
| Severity        | No issue identified                                                                                                                                                                                                                                                 |
| Status          | Reviewed                                                                                                                                                                                                                                                            |
| Finding         | Producer authority, immutable manifest identity, exact digest binding, work-scoped storage, Core publication ownership, derived-catalog nonauthority, and separation from Meridian grading and reporting are coherent and supported by the representative examples. |
| Required action | None beyond MPA-001 through MPA-003.                                                                                                                                                                                                                                |

### 9.13 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 3
Resolved prior ownership clarifications: 1
No-issue findings: 1
```

The manifest and publication architecture is suitable for continued review.

The resolved findings tighten Concord producer validation and documentation. They do not require:

* a new foundational record type;
* a Core modification;
* a Meridian modification;
* or revision of the representative example records.

## 10. Revision, Supersession, and Withdrawal Review

### 10.1 Review Question

Do Concord’s correction, native supersession, manifest revision, Core publication supersession, and withdrawal contracts preserve an explicit, unambiguous, append-only history without silently reviving older state or collapsing distinct versioning axes?

### 10.2 Separate Historical Axes

The foundation correctly preserves the following as separate histories:

```text
source-scan and routing history
Concord association and metadata correction
Artifact Review supersession
Moderation supersession
Score Evidence Link supersession
native Score supersession
manifest record-set revision
Core Academic Work Registration revision
Core Publication Record supersession
Core Publication Withdrawal
Meridian import and derived-result revision
Meridian override
report snapshot revision
```

A change on one axis does not automatically create or modify a record on another axis.

In particular:

* a new native Score does not publish itself;
* a new manifest does not revise a Score;
* a new Publication Record does not supersede a native Score;
* a withdrawal does not correct native data;
* and a Meridian override does not revise Concord or Core records.

### 10.3 Native Correction Model

The hybrid native correction model is appropriate:

```text
same-type successor
    -> explicit record-specific supersession relationship

Correction Record
    -> why the correction occurred
    -> who authorized it
    -> when it occurred
    -> which record was affected
    -> which replacement exists, when applicable
```

The original record remains available.

A Correction Record does not itself rewrite the target, retarget existing references, or designate a replacement as current.

When a replacement exists, the same-type replacement’s explicit supersession relationship remains the authoritative current-record traversal mechanism.

A Correction Record without a replacement may document:

* invalidation;
* cancellation;
* a pending correction;
* or another correction event that does not yet create a new governing record.

### 10.4 Native Supersession Chains

Every native same-type supersession chain must be:

* explicit;
* append-preserving;
* acyclic;
* unbranched;
* and independently reproducible.

Each successor must identify its direct predecessor.

A predecessor must not acquire two competing successors.

Current state must be derived from explicit supersession relationships rather than:

* identifier ordering;
* creation time alone;
* modification time;
* the numerically highest value;
* or an isolated `current` label.

Record-specific contracts may impose stronger continuity rules.

### 10.5 Score Supersession

A superseding Score remains a new teacher-approved judgment.

It must not overwrite:

* the prior disposition or value;
* prior scorer;
* prior scoring time;
* prior evidence links;
* prior Moderation context;
* prior rationale;
* or prior publication history.

A superseding Score must:

* identify an existing predecessor;
* differ from its predecessor;
* belong to the same Activity;
* have a `scored_at` value no earlier than the predecessor;
* participate in an acyclic, unbranched chain;
* and preserve enough continuity to show which native judgment is being replaced.

The target and Criterion ordinarily remain the same.

When correction of the target, Criterion, Score classification, or governing standard is the reason for supersession, an accompanying Correction Record must identify that semantic correction explicitly.

Several later observations about the same standard are not automatically Score supersession. They may remain independent contextual observations unless Concord records a deliberate replacement relationship.

### 10.6 Manifest Revision

A new manifest revision is required when the published projection changes materially.

Examples include:

* a new publishable Score;
* native Score supersession;
* a target or governing-standard correction;
* a scored-to-non-score or non-score-to-scored change;
* a consequential evidence-link change;
* a Moderation decision that changes permitted use;
* an evidence-lineage correction;
* a Criterion or Scale projection correction;
* a privacy-projection correction;
* or a manifest-contract migration.

A native change that does not affect the published projection does not require republication.

Manifest revisions:

* are immutable;
* retain one stable `record_set_id`;
* use distinct positive revisions;
* need not be contiguous;
* and do not establish the current published head by themselves.

### 10.7 Core Publication Supersession

Core publication supersession is a single explicit chain for one publication-series identity:

```text
ModuleWorkRef
publication_kind
record_set_id
```

A successor Publication Record:

* identifies the exact current predecessor;
* uses a greater `record_set_revision`;
* retains the same work, publication kind, and record-set identity;
* points to a new immutable manifest;
* and does not mutate the predecessor.

The series must have:

* exactly one root;
* no branching successors;
* no cycles;
* and exactly one unsuperseded head.

The head is derived from explicit predecessor relationships rather than revision number or timestamp alone.

### 10.8 Publication Withdrawal

Publication Withdrawal is a separate immutable Core record attached to one exact Publication Record.

Withdrawal does not:

* delete the Publication Record;
* delete or alter manifest bytes;
* alter native Concord records;
* erase prior Meridian imports;
* rewrite prior calculations or reports;
* create a corrected result;
* or restore another publication automatically.

When the withdrawn publication is the series head:

```text
withdrawn head
    -> remains the structural series head
    -> is not currently selectable
    -> does not reactivate its predecessor
```

The series therefore has no currently selectable publication until a new successor Publication Record is created.

A corrected successor must explicitly supersede the withdrawn head.

When a historical non-head publication is withdrawn, the current series head is unchanged.

Withdrawal cannot be reversed by mutating or deleting the Withdrawal or Publication Record.

### 10.9 Representative-Example Assessment

The seminar and project examples demonstrate:

* native Score supersession;
* preservation of predecessor Scores;
* new manifest revision following native change;
* distinct Core publication supersession;
* stable record-set identity;
* immutable predecessor manifests;
* explicit predecessor Publication Record identity;
* and continued historical reproducibility.

The representative cases do not instantiate a complete Publication Withdrawal record.

That omission does not require an additional Concord-owned fixture before serialized Concord contracts proceed because:

* Publication Withdrawal is Core-owned;
* Core already defines and enforces its immutable shape and relationship;
* Concord introduces no producer-specific withdrawal record;
* and the remaining issue is documentation of selection behavior rather than an untested Concord entity.

The examples should nevertheless state explicitly that withdrawing a series head does not reactivate its predecessor.

### 10.10 Findings

#### RSW-001 — Native supersession chains lack complete shared invariants

| Field                            | Value                                                                                                                                                                                                                                                                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Native correction and supersession                                                                                                                                                                                                                                                                                     |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                                                                    |
| Status                           | Resolved                                                                                                                                                                                                                                                                                                                   |
| Finding                          | Numerous Concord records carry record-specific supersession fields, but the shared contracts do not fully require existing predecessors, non-self-reference, acyclic and unbranched chains, chronological consistency, or explicit-head derivation. Score supersession also lacks sufficient logical-continuity rules. |
| Required action                  | Add shared native supersession-chain invariants and Score-specific continuity requirements.                                                                                                                                                                                                                            |
| Architecture change required     | No                                                                                                                                                                                                                                                                                                                     |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                                                                     |
| Example changes required         | No; represented chains already follow the intended rules                                                                                                                                                                                                                                                               |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, immediately after line **486**:

> Corrections and replacements create explicit history.

Add:

```markdown
When a Concord record uses an explicit same-type supersession relationship:

* the predecessor must exist;
* the successor and predecessor must be distinct records of the same record kind;
* the successor must identify its direct predecessor;
* the successor’s applicable effective or decision time must not precede the predecessor’s;
* one predecessor must not have more than one successor;
* each supersession chain must be acyclic and have exactly one unsuperseded head;
* and current state must be derived from the explicit chain rather than identifier ordering, timestamps alone, or an isolated status label.

Record-specific contracts may impose stronger continuity requirements.
```

In the same document, immediately after line **2419**:

> Revised consequential Scores preserve earlier Score Records.

Add:

```markdown
When `supersedes_score_record_id` is present:

* it must identify an existing different Score Record;
* the predecessor and successor must belong to the same Activity;
* the successor’s `scored_at` must not precede the predecessor’s;
* the Score-supersession chain must be acyclic and unbranched;
* and the current Score must be derived from the explicit chain.

The target and Criterion ordinarily remain the same.

When target, Criterion, `score_kind`, or governing `standard_id` changes because an earlier Score was semantically incorrect, a Correction Record must identify the predecessor, replacement, and reason for that correction.

A later observation is not a superseding Score merely because it has a later timestamp or a higher value.
```

In `docs/design/initial-concord-domain-model.md`, immediately before line **1928**:

> `### 10.6 Score Evidence Link`

Add:

```markdown
#### Score supersession

A Score may supersede an earlier Score only through an explicit predecessor relationship.

The predecessor must exist, must belong to the same Activity, and must not be the successor itself. The successor’s scoring time must not precede the predecessor’s.

Score-supersession chains must be acyclic and unbranched. Current state is derived from the explicit relationship rather than timestamps or values.

The target and Criterion normally remain the same. A correction that changes the target, Criterion, Score classification, or governing standard requires an accompanying Correction Record explaining that semantic change.

A later contextual observation remains independent unless the teacher deliberately records native supersession.
```

In `docs/design/examples/README.md`, immediately after line **1450**:

> The replacement must identify the record it supersedes. A replacement becoming current does not make the original record invalid history.

Add:

```markdown
Every illustrated same-type supersession chain must be direct, acyclic, and unbranched.

The successor must identify an existing predecessor, and current state must be derived from the explicit chain rather than timestamps, values, filenames, or identifier ordering.

For Score supersession, the predecessor and successor must belong to the same Activity. A change to the target, Criterion, Score classification, or governing standard requires an explicit Correction Record.
```

#### RSW-002 — Correction Record replacement semantics are internally inconsistent

| Field                            | Value                                                                                                                                                                                                                                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area                             | Correction Record                                                                                                                                                                                                                                                                                |
| Severity                         | Minor clarification                                                                                                                                                                                                                                                                              |
| Status                           | Resolved                                                                                                                                                                                                                                                                                             |
| Finding                          | `replacement_reference` is optional, while the invariants state unconditionally that “the replacement must identify the record it supersedes.” The contracts also do not define what a Correction Record without a replacement accomplishes or how a Correction Record itself may be superseded. |
| Required action                  | Make replacement conditional, state the effect of a correction without replacement, and permit append-preserving correction of an erroneous Correction Record.                                                                                                                                   |
| Architecture change required     | No                                                                                                                                                                                                                                                                                               |
| Core or Meridian change required | No                                                                                                                                                                                                                                                                                               |
| Example changes required         | No                                                                                                                                                                                                                                                                                               |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, replace lines **1977–1982**:

> Concord uses a hybrid correction model:
>
> 1. same-type replacement records use an explicit `supersedes_<record>_id` relationship; and
> 2. a generic Correction Record explains the correction, actor, reason, and old-to-new relationship.
>
> This preserves efficient current-record traversal while maintaining one consistent audit contract.

With:

```markdown
Concord uses a hybrid correction model:

1. when one durable record replaces another, the same-type successor uses an explicit record-specific supersession relationship; and
2. a Correction Record documents the affected record, correction type, actor, time, reason, supporting source, and replacement when one exists.

A Correction Record may omit `replacement_reference` when it documents invalidation, cancellation, a pending correction, or another event that creates no replacement record.

A Correction Record without a replacement does not designate a new current record or retarget existing references.

This preserves efficient current-record traversal while maintaining one consistent audit contract.
```

In the Correction Record field table, add after line **1988**:

```markdown
| `supersedes_correction_id` | Optional | Earlier Correction Record replaced |
```

Replace line **1994**:

> `replacement_reference` | Optional | New governing record

With:

```markdown
| `replacement_reference` | Conditional | Required when the correction creates a replacement; otherwise omitted |
```

Replace lines **2017–2021** with:

```markdown
* The target record remains available.
* A Correction Record never rewrites a retained source scan.
* When `replacement_reference` is present, it must identify the same successor whose record-specific supersession field identifies `target_reference`.
* When `replacement_reference` is absent, the Correction Record documents the correction event but does not establish a new governing record.
* A Correction Record does not by itself retarget historical references.
* An erroneous Correction Record may be replaced through `supersedes_correction_id`.
* Current-record designation is derived from the applicable same-type supersession relationship rather than deletion of history.
* Corrections must not create ambiguous competing current records.
```

In `docs/design/initial-concord-domain-model.md`, replace lines **1511–1527** with:

```markdown
Concord uses a hybrid correction model:

1. a same-type replacement record explicitly identifies the record it supersedes; and
2. a general **Correction Record** documents the affected record, correction type, actor, time, reason, supporting source, and replacement when one exists.

A Correction Record should identify:

* durable `correction_id`;
* target record type and identifier;
* correction type;
* reason;
* correcting Actor;
* timestamp;
* replacement or superseding record when the correction creates one;
* optional supporting source;
* privacy policy;
* optional superseded Correction Record;
* and optional note.

A Correction Record without a replacement may document invalidation, cancellation, or a pending correction, but it does not create a new governing record or retarget existing references.
```

In `docs/design/examples/README.md`, immediately after line **1452**:

> A Correction Record never rewrites a Core-retained source scan.

Add:

```markdown
When a correction creates a replacement, `replacement_reference` is required and must agree with the replacement record’s explicit supersession field.

A Correction Record without a replacement documents the event only. It does not establish a new current record, retarget existing references, or make another record current implicitly.
```

#### RSW-003 — Withdrawal does not state its no-fallback selection semantics

| Field                            | Value                                                                                                                                                                                                                                     |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Core Publication Withdrawal                                                                                                                                                                                                               |
| Severity                         | Minor clarification                                                                                                                                                                                                                       |
| Status                           | Resolved                                                                                                                                                                                                                                      |
| Finding                          | Concord correctly describes withdrawal as immutable and non-destructive but does not state that withdrawing the current series head leaves the series with no currently selectable publication. Core does not reactivate the predecessor. |
| Required action                  | State the no-fallback rule and require a corrected successor to supersede the withdrawn head.                                                                                                                                             |
| Architecture change required     | No                                                                                                                                                                                                                                        |
| Core or Meridian change required | No; this documents existing Core behavior                                                                                                                                                                                                 |
| Example changes required         | No serialized record changes                                                                                                                                                                                                              |

##### Exact corrections

In ADR 0015, immediately after line **1235**:

> Core withdrawal is used when a published manifest revision should no longer be selected as current or ordinarily usable.

Add:

```markdown
Withdrawal does not alter publication-series structure.

When the withdrawn Publication Record is the unsuperseded series head, an earlier predecessor does not become current or ordinarily selectable again. The series has no currently selectable publication until a new successor is published.

A corrected successor must explicitly supersede the withdrawn head.

Withdrawing a historical non-head publication does not change the existing series head.
```

In `docs/design/conceptual-data-contracts.md`, immediately after line **3255**:

> Core withdrawal marks a publication as no longer ordinarily selectable as current data.

Add:

```markdown
Withdrawal does not change which Publication Record is the structural series head.

If the withdrawn record is the series head, no predecessor is reactivated. The series has no currently selectable publication until a new Publication Record explicitly supersedes the withdrawn head.

Withdrawal of a historical non-head publication does not change the current head.
```

In `docs/design/examples/README.md`, immediately after line **1497**:

> It records that one exact Publication Record should no longer be ordinarily selected as current data.

Add:

```markdown
If that Publication Record is the series head, withdrawal does not reactivate an earlier predecessor. The series remains without a currently selectable publication until a new successor explicitly supersedes the withdrawn head.

Withdrawal of a historical non-head publication leaves the existing series head unchanged.
```

In the same document, immediately after line **3235**:

> Core represents withdrawal as a separate immutable record.

Add:

```markdown
A withdrawn series head remains the structural head but is not currently selectable. Its predecessor does not become current again.

A corrected replacement must be a new Publication Record that explicitly supersedes the withdrawn head.
```

In `docs/design/pds-core-integration-requirements.md`, immediately after line **1527**, add:

```markdown
Withdrawal does not reactivate a predecessor publication.

When the withdrawn publication is the current series head, the series has no currently selectable publication until the corrected manifest is published through a new Publication Record that explicitly supersedes the withdrawn head.
```

In `docs/design/examples/cross-example-validation.md`, replace line **589**:

> This satisfies the representative README’s permitted bounded treatment, but issue #13 may require a concrete withdrawal fixture before serialized Core contracts are approved.

With:

```markdown
Issue #13 concludes that an additional Concord-specific withdrawal fixture is not required before serialized Concord contracts proceed because Publication Withdrawal is Core-owned and already governed by an implemented Core contract.

The Concord contracts and examples must nevertheless preserve the reviewed rule that withdrawing a series head does not reactivate its predecessor.
```

#### RSW-004 — Revision, supersession, and withdrawal architecture is otherwise coherent

| Field           | Value                                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area            | Revision, supersession, and withdrawal                                                                                                                                         |
| Severity        | No issue identified                                                                                                                                                            |
| Status          | Reviewed                                                                                                                                                                       |
| Finding         | Native correction, Score history, manifest revision, Core publication supersession, withdrawal, and Meridian-derived history remain correctly separated and append-preserving. |
| Required action | None beyond RSW-001 through RSW-003.                                                                                                                                           |

### 10.11 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 3
No-issue findings: 1
```

The revision, supersession, and withdrawal architecture is suitable for continued review.

The three resolved findings add explicit chain, correction, and selection invariants. They do not require:

* a new foundational record type;
* a new ADR;
* a Core implementation change;
* a Meridian implementation change;
* or changes to the represented manifest bytes.

## 11. Cross-Producer Evidence Lineage Review

### 11.1 Review Question

Does Concord preserve exact, historically sufficient, privacy-aware lineage when ScoreForm, Quillan, or another external producer supplies evidence for a Concord Score, without duplicating source records or assigning overlap policy to the wrong module?

### 11.2 Ownership Model

The cross-producer relationship is:

```text
source-producer record
    -> Concord External Reference when needed
    -> Evidence Reference
    -> Score Evidence Link
    -> teacher-approved Concord Score
    -> Concord manifest evidence-lineage projection
    -> Meridian overlap and selection policy
```

The originating producer remains authoritative for:

* its assignment or work;
* native result or response;
* native Review;
* native scale and interpretation;
* native revision history;
* and its own publication manifest.

Concord remains authoritative for:

* why the source is related to a Concord Activity;
* the relationship purpose;
* the particular source revision used as evidence;
* Subject and Activity context;
* relevance to a Concord Score;
* applicable Concord Moderation;
* and the teacher-approved Concord judgment.

Core remains authoritative for:

* Publication Record identity;
* exact manifest binding;
* supersession;
* withdrawal;
* and source-publication discovery state.

Meridian remains authoritative for:

* whether either publication is eligible;
* whether the two results overlap;
* whether one is derivative of the other;
* whether both may be used;
* whether one is corroborating;
* and whether one must be excluded to prevent double counting.

### 11.3 No Ownership Transfer

Use of an external record as evidence does not:

* copy the source record into Concord;
* transfer source ownership;
* convert the external result into a Concord Score;
* convert its native scale into a Concord Scoring Scale;
* authorize access to the full source;
* or establish Grade eligibility.

A Concord Score remains a separate teacher judgment even when external evidence strongly supports it.

A shared `standard_id`, similar label, identical numeric value, or common target does not make records from different producers equivalent.

### 11.4 External Reference Boundary

A Concord External Reference identifies a durable logical relationship between a Concord Activity and an externally owned record.

It preserves:

* the actual owning module or external system;
* public external record kind;
* durable external record ID;
* public contract version where available;
* relationship purpose;
* Concord context;
* availability;
* provenance;
* and correction or supersession history.

The External Reference is not, by itself, the exact historical evidence-use decision.

The exact source revision used for one consequential Score belongs to that Score’s Evidence Reference and Score Evidence Link.

This allows one logical external relationship to participate in several deliberate evidence uses without treating every use as the same historical decision.

### 11.5 Canonical Cross-Producer Evidence Forms

Two representation forms are permitted.

#### Indirect form through a Concord External Reference

The normal form when Concord maintains a contextual relationship record is:

```yaml
evidence_kind: external_record
owning_system: concord
record_id: <external_reference_id>
```

The referenced External Reference supplies the actual:

```text
external owning system
external record kind
external record ID
external contract version
relationship purpose
Concord context
availability state
```

#### Direct source-owned form

A direct Evidence Reference may identify an external source record without an intervening Concord External Reference when no durable Concord relationship record is required:

```yaml
evidence_kind: scoreform_result
owning_system: scoreform
record_id: <scoreform_result_id>
```

or:

```yaml
evidence_kind: quillan_response
owning_system: quillan
record_id: <quillan_response_id>
```

One Score Evidence Link must use one representation form.

It must not identify the same external record simultaneously through both:

* a Concord External Reference; and
* a separate direct source-owned Evidence Reference.

### 11.6 Exact Source-Revision Sufficiency

A consequential cross-producer evidence relationship must preserve the exact external state used by the teacher.

At least one of the following is required:

1. an exact Core Publication Reference whose bound manifest exposes the source record and revision used;
2. an immutable external record identity;
3. an explicit external revision identity;
4. a versioned export identity with integrity information;
5. or a bounded evidence snapshot.

A reference to a mutable “current result,” mutable file path, or display label alone is insufficient.

When the evidence was resolved through a Core Publication Record, or when an exact compatible source publication is verified to contain the source revision used, `source_publication_reference` is required.

A later publication must not be attached merely because it now contains a record with the same logical ID. Concord must verify that it exposes the exact source state used for the judgment.

When no source publication existed, Concord preserves another immutable source-version mechanism rather than fabricating a Publication Reference.

### 11.7 Source-Publication Integrity

When `source_publication_reference` is present:

* it identifies one exact immutable Core Publication Record;
* the referenced publication’s producer module must match the external source owner;
* its manifest must expose the exact `source_record_reference`;
* the source-record contract version must be compatible with the evidence relationship;
* and the source state must be sufficient to reproduce what the teacher used.

Within a Manifest Evidence-Lineage Projection:

* `source_record_reference` identifies the originating producer-owned record;
* `evidence_reference` identifies the Concord-native or direct evidence relationship;
* and `source_publication_reference` identifies the exact producer publication through which that source revision was resolved.

When the same source-publication field appears inside `evidence_reference` and at projection level, the two values must be either:

* both absent; or
* exactly equal.

Conflicting publication references are invalid.

### 11.8 Source Supersession and Withdrawal

A later source-producer revision or Publication Record does not silently retarget a historical Concord evidence relationship.

The teacher may deliberately:

* retain the existing Concord Score;
* create a new Score Evidence Link;
* supersede the External Reference;
* create a superseding Concord Score;
* or record that the source is no longer appropriate for active use.

The earlier relationship remains historical provenance.

A later source-publication withdrawal:

* does not delete the Concord Score;
* does not rewrite an existing Concord manifest;
* does not erase prior Meridian calculations;
* and does not automatically prove that the underlying teacher judgment was invalid.

It does require explicit policy or human review before the withdrawn publication is selected as current source evidence for a new calculation or later Concord publication.

The withdrawal state remains resolvable through Core even when the exact Publication Reference continues to serve as historical provenance.

### 11.9 External Availability and Compatibility

External availability states remain integration states rather than performance judgments.

Examples include:

```text
available
unavailable
unresolved
permission_restricted
incompatible
superseded
deleted_externally
not_yet_created
temporarily_inaccessible
```

None automatically creates:

* zero;
* the lowest scale value;
* failed participation;
* incomplete responsibility;
* absence;
* or another Score disposition.

When an external schema or contract is unsupported, Concord must not guess at field meaning.

A safe label or unresolved reference may remain available while detailed interpretation is disabled.

### 11.10 Moderation

Source-module processing does not eliminate Concord’s responsibility to moderate consequential use.

For example:

* ScoreForm may correctly process machine-readable peer ratings while Concord still evaluates bias and fairness;
* Quillan may contain a valid teacher-reviewed response while Concord separately moderates claims about another participant;
* and a technically verified repository record may still be insufficient to prove individual contribution.

The originating producer owns native processing.

Concord owns whether that processed source may support the particular Concord Score.

### 11.11 Privacy

A cross-producer reference does not broaden authorization.

Access to a Concord Score does not imply access to:

* complete Quillan writing;
* ScoreForm answers;
* answer keys;
* private feedback;
* source-module teacher notes;
* repository credentials;
* or other restricted evidence.

The manifest exposes only the minimum structured lineage needed to:

* identify the source;
* preserve exact revision provenance;
* establish relevance;
* establish applicable Moderation;
* and permit Meridian to recognize overlap.

Credentials, access tokens, unrestricted source content, and unnecessary sensitive narrative remain excluded.

### 11.12 Meridian Overlap Boundary

Meridian must not presume that two producer results are independent merely because they have different Publication Record IDs or producer modules.

For example:

```text
ScoreForm result
    -> evidence for Concord Score
```

is different from:

```text
ScoreForm result
    + unrelated Concord observation
```

The Concord manifest supplies the lineage required to distinguish them.

Meridian then applies an explicit policy that may:

* select both with their relationship documented;
* select only the Concord judgment;
* select only the originating producer result;
* treat one as corroboration;
* exclude one to prevent double counting;
* or use neither.

Concord does not make that policy decision by suppressing or rewriting lineage.

### 11.13 Representative-Example Assessment

The seminar example preserves:

* a Quillan-owned response;
* a Concord External Reference;
* a deliberate Score Evidence Link;
* the exact Quillan source record;
* and the exact Core Publication Reference through which the Quillan source revision became discoverable.

The laboratory example preserves the corresponding relationship for a ScoreForm result.

Both examples show:

* external ownership;
* explicit teacher use;
* no automatic Score conversion;
* exact source-publication provenance;
* repeated publication identity at the native and manifest projection layers;
* and sufficient lineage for Meridian to detect cross-producer overlap.

The project example demonstrates the complementary boundary for external systems that do not publish Paper Data Suite academic-result manifests. Repository, commit, pull-request, CI, CAD, and cloud-document records remain externally owned and are preserved through durable references rather than invented Core publications.

No representative manifest bytes require modification.

### 11.14 Findings

#### CPL-001 — Exact source revision is assigned inconsistently between External Reference and evidence use

| Field                        | Value                                                                                                                                                                                                                                                        |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area                         | External Reference and historical evidence identity                                                                                                                                                                                                          |
| Severity                     | Minor clarification                                                                                                                                                                                                                                          |
| Status                       | Resolved                                                                                                                                                                                                                                                         |
| Finding                      | ADR 0012 and the initial domain model allow source version or publication information to appear on the general External Reference, while the finalized Evidence Reference and examples attach exact source-publication state to the particular evidence use. |
| Required action              | Define the External Reference as the durable logical relationship and place the exact source revision on the Evidence Reference and Score Evidence Link.                                                                                                     |
| Architecture change required | No                                                                                                                                                                                                                                                           |
| Example changes required     | No                                                                                                                                                                                                                                                           |

##### Exact corrections

In `docs/decisions/0012-link-scoreform-and-quillan-without-duplication.md`, immediately after the External Reference field list ending with:

> and correction or supersession history.

add:

```markdown
An External Reference identifies the durable logical relationship to an external record.

It does not, by itself, select the exact source revision used for a particular Score.

The exact immutable source state used for consequential evidence belongs to the Evidence Reference and Score Evidence Link for that particular evidence use. That state may be preserved through a Core Publication Reference, immutable record identity, explicit source revision, versioned export, or bounded snapshot.
```

In `docs/design/initial-concord-domain-model.md`, under `## 11. External References`, remove this bullet from the External Reference field list:

> `* optional exact Core source-publication reference when known;`

Immediately after the field list, add:

```markdown
An External Reference identifies a durable logical relationship to an external record.

The exact source revision used for a particular Score belongs to the Evidence Reference and Score Evidence Link. It is preserved through an exact Core source-publication reference or another immutable source-version mechanism.
```

In `docs/design/conceptual-data-contracts.md`, add to the `## 14.2 External Reference` invariants:

```markdown
* An External Reference identifies a logical external relationship; the exact source revision used for a particular Score belongs to that Score’s Evidence Reference and Score Evidence Link.
```

#### CPL-002 — Direct and indirect cross-producer Evidence Reference forms are ambiguous

| Field                        | Value                                                                                                                                                                                                                                                                                                                                                                               |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Evidence Reference identity                                                                                                                                                                                                                                                                                                                                                         |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                                                                                                                                 |
| Status                       | Resolved                                                                                                                                                                                                                                                                                                                                                                                |
| Finding                      | The Evidence Reference vocabulary permits `scoreform_result`, `quillan_response`, and `external_record`, while the representative cases use a Concord-owned External Reference as the Evidence Reference target and a separate source-owned record projection. The contracts do not define when each form applies or prevent both forms from identifying one source simultaneously. |
| Required action              | Define the indirect External Reference form, retain a bounded direct form, and require one unambiguous representation per Score Evidence Link.                                                                                                                                                                                                                                      |
| Architecture change required | No                                                                                                                                                                                                                                                                                                                                                                                  |
| Example changes required     | No; the examples already use the intended indirect form                                                                                                                                                                                                                                                                                                                             |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, immediately after the initial Evidence Reference kinds, add:

````markdown
### Cross-producer representation

When Concord maintains a durable contextual relationship to an external record, the Evidence Reference uses the indirect form:

```yaml
evidence_kind: external_record
owning_system: concord
record_id: <external_reference_id>
````

The referenced Concord External Reference supplies the actual external owning system, record kind, record ID, contract version, relationship purpose, and availability state.

A direct source-owned Evidence Reference using `scoreform_result`, `quillan_response`, or another approved external kind is permitted only when no Concord External Reference is used for that evidence relationship.

One Score Evidence Link must not identify the same external source through both the indirect External Reference form and a direct source-owned Evidence Reference.

````

Add to the Evidence Reference invariants:

```markdown
* When `evidence_kind = external_record` and `owning_system = concord`, `record_id` must resolve to an existing Concord External Reference.
* A direct source-owned Evidence Reference must identify the actual external owner, public record kind, and durable record ID.
* One Score Evidence Link uses exactly one direct or indirect source representation.
````

In `docs/design/initial-concord-domain-model.md`, immediately after the Evidence Reference description ending with:

> and optional Moderation requirement.

add:

```markdown
For cross-producer evidence, Concord may use either:

1. an indirect Evidence Reference to a Concord External Reference; or
2. a direct module-qualified reference to the external source record.

The indirect form is preferred when Concord must preserve Activity context, relationship purpose, availability, correction, or supersession independently of one Score Evidence Link.

One evidence use must not represent the same external record through both forms.
```

In ADR 0012, immediately after:

```text
ScoreForm or Quillan record
    -> typed External Reference in Concord
    -> optional Evidence Reference
    -> optional Score Evidence Link
    -> explicit Concord teacher judgment
```

add:

````markdown
For consequential evidence use, the normal Concord form is:

```text
external producer record
    -> Concord External Reference
    -> Evidence Reference identifying that External Reference
    -> Score Evidence Link
    -> explicit Concord Score
````

A direct source-owned Evidence Reference remains permitted when no durable Concord External Reference is required.

One Score Evidence Link must not represent the same source through both forms.

````

In `docs/design/conceptual-data-contracts.md`, add to the Manifest Evidence-Lineage Projection invariants:

```markdown
* When `evidence_reference` identifies a Concord External Reference, `source_record_reference` must exactly match that External Reference’s external owning system, record kind, record ID, and compatible contract version.
* When `evidence_reference` directly identifies a source-owned record, `source_record_reference` must identify the same source record.
````

#### CPL-003 — Exact source-publication conditionality and integrity are incomplete

| Field                        | Value                                                                                                                                                                                                                                                                                                                                                                                        |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Source publication and manifest lineage                                                                                                                                                                                                                                                                                                                                                      |
| Severity                     | Minor clarification                                                                                                                                                                                                                                                                                                                                                                          |
| Status                       | Resolved                                                                                                                                                                                                                                                                                                                                                                                         |
| Finding                      | Source-publication identity is generally described as optional “when known,” even when the evidence was resolved through an exact producer publication. The contracts also duplicate the Publication Reference inside the Evidence Reference and manifest lineage row without an equality rule, and do not state how later source supersession or withdrawal affects historical Concord use. |
| Required action              | Make source-publication identity conditionally required, require another immutable source-version mechanism when absent, define duplicate-field equality and record-membership checks, and preserve later source lifecycle without silent retargeting.                                                                                                                                       |
| Architecture change required | No                                                                                                                                                                                                                                                                                                                                                                                           |
| Example changes required     | No                                                                                                                                                                                                                                                                                                                                                                                           |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, replace the Evidence Reference field-table row:

> `| source_publication_reference | Optional | Exact Core Publication Record through which an external source revision was resolved, when known |`

with:

```markdown
| `source_publication_reference` | Conditional | Required when the external source revision was resolved through, or verified against, an exact Core Publication Record; otherwise omitted only when another immutable source-version mechanism is preserved |
```

Replace these Evidence Reference invariants:

> `* source_publication_reference, when present, identifies the exact Core publication through which the source revision became discoverable; it does not transfer ownership to Core.`
> `* Absence of source_publication_reference does not make the external record invalid when another durable public reference is available.`

with:

```markdown
* `source_publication_reference`, when present, identifies the exact Core publication whose bound manifest exposes the source revision used; it does not transfer ownership to Core.
* When the evidence was resolved through a Core Publication Record, or an exact compatible publication is verified to contain the source revision used, `source_publication_reference` is required.
* When no source publication is available, the Evidence Reference must preserve another immutable source-version mechanism.
* A mutable current-result reference, mutable path, or display label alone is insufficient for consequential evidence use.
* A later publication must not be attached solely because it contains the same logical record ID; exact source-revision equivalence must be verified.
```

In the Manifest Evidence-Lineage Projection field table, replace:

> `| source_publication_reference | Optional | Exact Core source publication when known |`

with:

```markdown
| `source_publication_reference` | Conditional | Required when the source revision was resolved through or verified against an exact Core Publication Record |
```

Add to its invariants:

```markdown
* A projection-level `source_publication_reference` and any `source_publication_reference` inside `evidence_reference` must be both absent or exactly equal.
* When `source_publication_reference` is present, its bound producer manifest must expose the exact `source_record_reference`.
* The source publication’s producer module must match the originating source owner.
* Conflicting source-publication references are invalid.
* Later source-publication supersession or withdrawal does not silently retarget or rewrite the Concord Score, Evidence Reference, Score Evidence Link, or published Concord manifest.
```

In `docs/decisions/0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md`, replace the passage beginning:

> When Concord knows that the external source was imported or resolved through a Core Publication Record...

and ending:

> That publication reference is optional unless a later integration contract requires it.

with:

```markdown
When the external source revision was imported or resolved through a Core Publication Record, or when an exact compatible producer publication is verified to expose the source revision used, the lineage must include an exact Core Publication Reference.

The referenced producer manifest must expose the exact source record identified by the lineage.

When no source publication exists, lineage must preserve another immutable source-version mechanism, such as:

* immutable external record identity;
* explicit external revision identity;
* versioned export identity with integrity information;
* or a bounded evidence snapshot.

A mutable current-result reference, mutable path, or display label alone is insufficient for consequential evidence lineage.

A later source publication must not be attached merely because it contains the same logical record ID. Concord must verify exact source-revision equivalence.
```

In `docs/design/initial-concord-domain-model.md`, under `### 10.10 Cross-Producer Evidence Lineage`, replace:

> When known, lineage may include the exact Core Publication Record identity of the external source.

with:

```markdown
When the exact external source revision was resolved through, or verified against, a Core Publication Record, lineage must preserve that exact Publication Record identity.

When no source publication exists, lineage must preserve another immutable source-version mechanism. A mutable current-result reference alone is insufficient for consequential use.
```

Under `### Standards-related external evidence`, replace:

> When the external source publication is known, Concord should preserve its exact Core Publication Record identity so Meridian can detect related results.

with:

```markdown
When the external source revision was resolved through, or verified against, an exact Core Publication Record, Concord must preserve that Publication Record identity so Meridian can identify related producer results.

When no source publication exists, Concord must preserve another immutable source-version mechanism.
```

In ADR 0012, under `### Historical sufficiency`, replace:

> The integration contract should provide at least one of:
>
> * immutable external result identity;
> * external revision identity;
> * versioned export identity;
> * or a bounded evidence snapshot.

with:

```markdown
For consequential use, the integration contract must preserve at least one of:

* an exact Core Publication Reference whose manifest exposes the source revision used;
* immutable external result identity;
* explicit external revision identity;
* versioned export identity with integrity information;
* or a bounded evidence snapshot.

A mutable current-result reference, mutable path, or display label alone is insufficient.
```

Under `### External record revision`, after:

> The earlier relationship remains available for provenance.

add:

```markdown
A later source Publication Record does not silently retarget the earlier relationship.

A later source-publication withdrawal preserves historical provenance but requires explicit review or policy before that withdrawn publication is selected for new consequential use. It does not automatically delete or revise the existing Concord Score.
```

#### CPL-004 — Source producer publication contracts remain an implementation dependency

| Field                                    | Value                                                                                                                                                                                                                                                                      |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                                     | ScoreForm and Quillan implementation readiness                                                                                                                                                                                                                             |
| Severity                                 | Follow-up implementation concern                                                                                                                                                                                                                                           |
| Status                                   | Tracked                                                                                                                                                                                                                                                                    |
| Finding                                  | The representative examples correctly model exact ScoreForm and Quillan source Publication References, but the currently released source-module runtimes do not yet expose the complete Core academic-result publication contracts represented by those synthetic records. |
| Required action                          | Before Concord implementation, stabilize supported ScoreForm and Quillan public record kinds, immutable result identities, manifest contracts, Publication Records, and optional adapters.                                                                                 |
| Architecture change required             | No                                                                                                                                                                                                                                                                         |
| Blocks conceptual approval               | No                                                                                                                                                                                                                                                                         |
| Blocks corresponding runtime integration | Yes                                                                                                                                                                                                                                                                        |

#### CPL-005 — Cross-producer authority and overlap boundaries are coherent

| Field           | Value                                                                                                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Cross-producer evidence lineage                                                                                                                                                                               |
| Severity        | No issue identified                                                                                                                                                                                           |
| Status          | Reviewed                                                                                                                                                                                                      |
| Finding         | Source ownership, explicit teacher judgment, no automatic conversion, Moderation, privacy, historical preservation, and Meridian-owned overlap policy are coherently separated and supported by the examples. |
| Required action | None beyond CPL-001 through CPL-004.                                                                                                                                                                          |

### 11.15 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 3
Follow-up implementation concerns: 1
No-issue findings: 1
```

The cross-producer evidence-lineage foundation is suitable for continued review.

The three resolved minor findings make the existing lineage model unambiguous and historically reproducible. They do not require:

* a new foundational record type;
* a new ADR;
* changes to Core;
* changes to Meridian;
* or changes to the represented manifest bytes.

The implementation concern remains tracked until ScoreForm and Quillan expose compatible, stable producer-publication contracts.

## 12. Meridian Consumption Boundary Review

### 12.1 Review Question

Does the Concord-to-Meridian boundary provide enough exact, immutable, producer-owned meaning for Meridian to import, validate, select, map, aggregate, assign to Academic Periods, override, and report Concord results without mutating Concord records or inventing unsupported equivalences?

### 12.2 Consumption Path

The supported consumption path is:

```text
Concord canonical records
    -> immutable Concord Academic Result Manifest
    -> immutable Core Publication Record
    -> authorized Meridian import
    -> Meridian eligibility and selection policy
    -> Meridian mapping and calculation policy
    -> Meridian-derived result
    -> optional Meridian report snapshot
```

Meridian consumes Concord through:

* Core Academic Work Registrations;
* Core Publication Records;
* Core withdrawal state;
* the public Concord manifest contract;
* and supported producer-specific adapters.

Meridian must not:

* recursively crawl Concord directories;
* infer publication from files;
* import mutable convenience paths as authority;
* import Concord private Python implementation;
* parse arbitrary native Concord records;
* or bypass the Core publication boundary.

The Core catalog may assist discovery, but canonical Core records remain authoritative.

### 12.3 Import Is Distinct from Selection

A Meridian import records an exact observation of one Core Publication Record and its bound Concord manifest.

Import or historical retention does not itself mean that the publication:

* is current;
* is Grade eligible;
* is standards-evidence eligible;
* belongs to an Academic Period;
* should replace an earlier observation;
* or may appear in a current report.

A superseded or withdrawn publication may remain imported or retained when necessary for:

* historical provenance;
* reproduction of an earlier calculation;
* reproduction of an issued report;
* comparison;
* correction analysis;
* or another authorized historical workflow.

Current selection remains a separate Meridian policy decision.

### 12.4 Required Import Provenance

A Meridian import of a Concord publication must preserve at least:

* Core Publication Record ID;
* Core publication-schema version;
* exact `ModuleWorkRef`;
* exact source Activity `ModuleRecordRef`;
* publication kind;
* declared capabilities;
* manifest path;
* digest algorithm;
* exact manifest digest;
* manifest contract version;
* record-set identity;
* record-set revision;
* exact Academic Work Registration revision;
* predecessor Publication Record ID when present;
* withdrawal state observed at import;
* time at which withdrawal state was observed;
* import time;
* and the supported Meridian import-contract or adapter version.

The import must preserve enough information to determine exactly which producer publication and manifest bytes were observed.

A later registry, catalog, registration, publication, withdrawal, adapter, or policy change must not silently rewrite the earlier import record.

### 12.5 Import Validation

Before a Concord publication is eligible for interpretation, Meridian must validate:

* authorization;
* supported Core publication schema;
* compatible publication kind;
* supported manifest contract version;
* supported declared capabilities;
* safe and resolvable manifest reference;
* exact manifest digest;
* consistency between the Publication Record and manifest identity;
* Criterion and Score projection integrity;
* exact Scale resolution;
* standard-backed versus local classification;
* target-reference validity;
* non-score disposition rules;
* native supersession relationships;
* evidence-lineage integrity;
* and required Moderation state.

A structurally valid import may still be ineligible for every grading or reporting calculation.

Unsupported or internally inconsistent data must remain explicitly incompatible or ineligible. Meridian must not guess at producer meaning.

### 12.6 Withdrawal and Supersession

Publication importability, historical retention, and current selection are distinct.

A withdrawn publication:

* remains an immutable historical Publication Record;
* may remain referenced by earlier imports, calculations, overrides, and reports;
* may be loaded for authorized historical reproduction;
* but is not ordinarily eligible for a new current calculation or current report.

When a withdrawn Publication Record is the structural series head:

* its predecessor is not reactivated;
* Meridian must not fall back automatically;
* and the series has no currently selectable publication until a new successor explicitly supersedes the withdrawn head.

A superseded publication similarly remains available for provenance. Current policy may select the later series head without deleting or rewriting the earlier import.

### 12.7 Score-Target Eligibility

Every imported Concord Score retains its exact `target_reference`.

Initial Concord target kinds include:

```text
core_student
concord_group
concord_session
concord_activity
concord_artifact_instance
concord_work_item
another approved activity component
```

For the current foundation, only a `core_student` target is directly eligible to become student-level standards evidence, student proficiency evidence, or a student Grade-item input.

A non-student target may remain useful for:

* Group-level interpretation;
* Activity or work-level analysis;
* teacher dashboards;
* contextual reporting;
* workflow evaluation;
* or another explicitly non-student derived result.

Meridian must not:

* replace a Group target with its current members;
* copy a Group Score to each member;
* infer equal individual performance;
* turn a Session or Activity Score into student evidence;
* use Artifact authorship as a Score-target mapping;
* or synthesize a student target from Subject context.

Any future policy that allocates or translates a non-student result into student-level derived data requires a separate explicit contract and architectural decision. It must preserve the original non-student target and must not represent the derived allocation as a Concord-native individual Score.

### 12.8 Standard-Backed and Local Scores

A standard-backed Score may become candidate standards evidence only when:

* `score_kind = standard_backed`;
* the direct `standard_id` is present;
* the standard matches the projected Criterion;
* the standard is one of the Activity’s projected Focus Standards;
* the target is eligible for the intended Meridian result;
* required Moderation is complete;
* and the active Meridian policy selects it.

A local Score:

* retains `score_kind = local`;
* contains no governing `standard_id`;
* does not become direct standards evidence;
* and may participate in a conventional or hybrid calculation only through explicit policy.

Non-governing `alignment_standard_ids` on a local Criterion must not be promoted to direct standards evidence.

### 12.9 Exact Scale Mapping

Meridian must preserve the exact native Concord Scoring Scale revision before applying any mapping.

A source-scale mapping policy must bind to at least:

* producer module;
* manifest contract version;
* `scoring_scale_id`;
* `scale_lineage_id`;
* Scale revision;
* scale type;
* complete machine-value set;
* ordering;
* display meanings;
* and the intended destination scale or calculation role.

A mapping must not be selected solely because two Scales share:

* numeric values;
* labels;
* number of levels;
* ordering;
* or an apparent four-level structure.

A new or changed source Scale revision requires a separately valid mapping decision or explicit revalidation.

When no compatible mapping exists, the result remains:

```text
unmapped
unsupported
or ineligible for that calculation
```

Meridian must not guess a percentage, points value, letter Grade, proficiency level, or equivalent scale value.

Non-score dispositions are interpreted through disposition policy, not through Scale mapping.

### 12.10 Repeated Evidence and Native Supersession

Meridian must distinguish:

```text
native Concord Score supersession
```

from:

```text
several independent contextual observations
```

An explicit Concord supersession relationship establishes producer-native replacement history.

Absent that relationship, Meridian must not infer replacement solely from:

* a later timestamp;
* a later Session;
* a higher value;
* a higher manifest revision;
* a later Publication Record;
* or matching Criterion and target identity.

Meridian evidence-selection policy may use recency, highest evidence, reassessment, teacher selection, or another supported strategy, but the applied policy must remain explicit and versioned.

Earlier imported evidence remains available for provenance even when it is not selected.

### 12.11 Evidence Lineage and Moderation

Meridian must validate evidence lineage before treating two producer results as independent.

When a Concord Score used a ScoreForm or Quillan result as evidence, Meridian may:

* use both with their relationship documented;
* use only the Concord judgment;
* use only the originating producer result;
* treat one as corroboration;
* exclude one to prevent double counting;
* or use neither.

That decision belongs to an explicit Meridian policy.

For active consequential Score Evidence Links, Meridian must not rely solely on the Score-level `moderation_complete` Boolean.

It must validate that:

* every link requiring Moderation identifies the applicable projected Moderation Record;
* the Moderation decision permits the represented use;
* material qualification is preserved;
* rejected evidence is not active support;
* and the Score-level Boolean agrees with the active evidence and Moderation projections.

### 12.12 Academic Period Membership

Concord-native dates are preserved chronology, not authoritative Academic Period membership.

Meridian assigns eligible work and evidence to Academic Periods under explicit policy using Core-owned calendars.

A period-related calculation must preserve:

* school year;
* Academic Period ID;
* exact Core calendar revision;
* period-membership policy version;
* treatment of late evidence;
* treatment of reassessment;
* and any carry-forward or cumulative rule.

Meridian must not determine period membership solely from:

* Activity date;
* Session date;
* evidence date;
* `scored_at`;
* publication date;
* or import date.

Those dates may be policy inputs, but the membership decision remains a distinct derived record.

### 12.13 Overrides

A Concord Score revision changes the producer-native teacher judgment.

A Meridian override changes a Meridian-derived result or selection.

A Meridian override may apply to:

* evidence selection;
* standards proficiency;
* a Grade-item result;
* an Academic Period result;
* a conventional or hybrid Grade;
* or another explicitly supported Meridian-derived result.

It must preserve:

* the pre-override derived state;
* replacement state;
* scope;
* responsible Actor;
* time;
* rationale where required;
* authorization policy;
* and relationship to the affected calculation.

An override must not:

* mutate a Concord Score;
* alter its target;
* change its Criterion or standard;
* change its native Scale;
* rewrite its disposition;
* rewrite the manifest;
* mutate the Core Publication Record;
* or fabricate a new producer-native Score.

When the underlying teacher judgment changes, the correct sequence is:

```text
new Concord Score
    -> new Concord manifest revision
    -> new Core Publication Record
    -> later Meridian import or recalculation
```

### 12.14 Formal Reporting

A Concord manifest is not a formal report.

A Meridian report snapshot remains a separate derived product that preserves:

* exact source Publication Record IDs;
* relevant registration revisions;
* selected and materially excluded evidence;
* grading and evidence-selection policies;
* exact Academic Period context;
* active overrides;
* report-definition version;
* audience;
* generation provenance;
* rendering state;
* delivery state;
* and report supersession.

A frozen report snapshot must not silently change when:

* a Concord publication is superseded;
* a publication is withdrawn;
* a Score is revised;
* a grading policy changes;
* an Academic Period calendar changes;
* an override is added or removed;
* or the report definition changes.

A refresh creates a new identifiable generation result or snapshot.

### 12.15 Representative-Example Assessment

The seminar example demonstrates:

* individual standard-backed Score targets;
* native Score supersession;
* two Concord publications;
* cross-producer Quillan lineage;
* and no automatic Grade or period inclusion.

The laboratory example demonstrates:

* a Group standard-backed Score;
* a local Group Score;
* an individual standard-backed Score;
* an individual non-score disposition;
* distinct native Scales;
* ScoreForm overlap;
* and a manifest containing both standards and local results.

The project example demonstrates local-criteria publication, external technical evidence, publication supersession, and continued separation from Meridian policy.

Together the cases provide sufficient producer meaning for Meridian to:

* distinguish target kinds;
* distinguish standard-backed and local results;
* preserve non-score dispositions;
* resolve exact Scales;
* identify native supersession;
* detect cross-producer overlap;
* and apply separate Grade, period, override, and reporting policies.

No representative manifest bytes require modification.

### 12.16 Findings

#### MCB-001 — Meridian import provenance is advisory and incomplete

| Field                            | Value                                                                                                                                                                                                                                                 |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Meridian import provenance                                                                                                                                                                                                                            |
| Severity                         | Minor clarification                                                                                                                                                                                                                                   |
| Status                           | Resolved                                                                                                                                                                                                                                                  |
| Finding                          | The conceptual contract and ADR 0015 say a Meridian import “should” preserve a bounded subset of publication identity. Reproducibility requires a mandatory observation of the complete publication and manifest identity relevant to interpretation. |
| Required action                  | Make import provenance mandatory and preserve the exact publication envelope, withdrawal observation, and adapter compatibility state.                                                                                                                |
| Architecture change required     | No                                                                                                                                                                                                                                                    |
| Core or Meridian change required | No immediate implementation change; later Meridian serialization must follow the clarified contract                                                                                                                                                   |
| Example changes required         | No                                                                                                                                                                                                                                                    |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, under `## 13.18 Meridian Consumption Boundary`, replace:

> A Meridian import should preserve:
>
> * Core `publication_id`;
> * exact manifest digest;
> * manifest contract version;
> * record-set identity;
> * record-set revision;
> * Academic Work Registration revision;
> * source Activity reference;
> * publication withdrawal state;
> * and import time.

with:

```markdown
A Meridian import must preserve:

* Core Publication Record ID and publication-schema version;
* exact `ModuleWorkRef`;
* exact source Activity `ModuleRecordRef`;
* publication kind and declared capabilities;
* manifest path;
* manifest digest algorithm and exact digest;
* manifest contract version;
* record-set identity and revision;
* exact Academic Work Registration revision;
* predecessor Publication Record ID when present;
* withdrawal state observed at import;
* withdrawal-state observation time;
* import time;
* and the supported Meridian import-contract or adapter version.
```

In ADR 0015, under `## Meridian Consumption`, replace its corresponding “should preserve” list with the same mandatory list.

In `docs/design/initial-concord-domain-model.md`, under `### 10.15 Meridian Consumption Boundary`, replace the existing abbreviated import list with the same mandatory list.

#### MCB-002 — Withdrawal is treated as an import-validity condition rather than a selection condition

| Field                            | Value                                                                                                                                                                                                                                |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area                             | Withdrawal and Meridian selection                                                                                                                                                                                                    |
| Severity                         | Minor clarification                                                                                                                                                                                                                  |
| Status                           | Resolved                                                                                                                                                                                                                                 |
| Finding                          | ADR 0015 says Meridian must validate that a publication “has not been withdrawn.” That is correct for ordinary current selection, but too broad for historical import, prior-calculation reproduction, and frozen-report provenance. |
| Required action                  | Separate historical import and retention from current eligibility, while preserving the no-fallback rule for a withdrawn series head.                                                                                                |
| Architecture change required     | No                                                                                                                                                                                                                                   |
| Core or Meridian change required | No                                                                                                                                                                                                                                   |
| Example changes required         | No                                                                                                                                                                                                                                   |

##### Exact corrections

In ADR 0015, under `## Meridian Consumption`, replace:

> * the publication has not been withdrawn;

with:

```markdown
* the current withdrawal state has been resolved; and
* the publication is eligible for the intended import, selection, calculation, or historical operation.
```

Immediately after the validation list, add:

```markdown
Import, historical retention, and current selection are distinct.

A withdrawn publication may remain imported or resolvable for historical provenance, reproduction of an earlier calculation, or reproduction of an issued report.

It is not ordinarily eligible for a new current calculation or current report.

When a withdrawn publication is the structural series head, no predecessor is reactivated or selected as an implicit fallback.
```

Add the same distinction to:

* `docs/design/conceptual-data-contracts.md` under `## 13.18 Meridian Consumption Boundary`;
* and `docs/design/initial-concord-domain-model.md` under `### 10.15 Meridian Consumption Boundary`.

#### MCB-003 — Non-student target eligibility is underdefined

| Field                            | Value                                                                                                                                                                                                                                           |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Score targets and downstream eligibility                                                                                                                                                                                                        |
| Severity                         | Minor clarification                                                                                                                                                                                                                             |
| Status                           | Resolved                                                                                                                                                                                                                                            |
| Finding                          | Concord supports student, Group, Session, Activity, Artifact, Work Item, and other component targets. The contracts forbid copying Group Scores to members but do not state which targets may become student-level Meridian evidence or Grades. |
| Required action                  | Make `core_student` the only directly student-eligible target in the current boundary and forbid synthesized student targets from non-student Scores.                                                                                           |
| Architecture change required     | No                                                                                                                                                                                                                                              |
| Core or Meridian change required | No; a future non-student allocation model would require a separate decision                                                                                                                                                                     |
| Example changes required         | No                                                                                                                                                                                                                                              |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, add to the Score-Target Reference invariants:

```markdown
* For the current Meridian boundary, only a `core_student` target is directly eligible for student-level standards evidence, proficiency, or Grade-item calculation.
* Non-student targets must remain non-student downstream.
* Meridian must not synthesize a student target from Group Membership, Artifact Author, Artifact Subject, Session context, or another contextual relationship.
* Any future allocation of a non-student result to students requires a separate explicit contract and must preserve the original target.
```

Add to the Manifest Score Projection invariants:

```markdown
* Meridian must preserve `target_reference` exactly.
* A non-student Score may support Group-, Activity-, work-, or contextual reporting but must not become student-level evidence merely because students are related to its target.
```

In ADR 0015 and the initial domain model, add the same rules immediately after the existing prohibition against copying Group Scores to members.

#### MCB-004 — Scale mappings are not explicitly bound to the exact source Scale contract

| Field                            | Value                                                                                                                                                                                                           |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                             | Meridian scale mapping                                                                                                                                                                                          |
| Severity                         | Minor clarification                                                                                                                                                                                             |
| Status                           | Resolved                                                                                                                                                                                                            |
| Finding                          | The contracts correctly require explicit versioned mapping, but do not define the minimum exact source identity to which the mapping applies. A mapping could otherwise be selected by shared values or labels. |
| Required action                  | Bind every mapping to the exact producer, manifest contract, Scale identity, revision, type, and complete level semantics.                                                                                      |
| Architecture change required     | No                                                                                                                                                                                                              |
| Core or Meridian change required | No immediate change; later Meridian mapping contracts must implement the rule                                                                                                                                   |
| Example changes required         | No                                                                                                                                                                                                              |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, add to the Manifest Scoring Scale Projection invariants:

```markdown
* A Meridian source-scale mapping must bind to the producer module, manifest contract version, `scoring_scale_id`, `scale_lineage_id`, Scale revision, scale type, and complete projected level semantics.
* A mapping must not be selected solely by numeric values, labels, level count, or ordering.
* A changed Scale revision requires a separately valid mapping or explicit revalidation.
* When no compatible mapping exists, the result remains unmapped or ineligible for that calculation rather than being guessed.
```

In ADR 0015, add the same rules under `## Scoring Scale Projection`.

In `docs/design/initial-concord-domain-model.md`, add the same rules to `### 10.15 Meridian Consumption Boundary`.

#### MCB-005 — Meridian authority and producer separation are coherent

| Field           | Value                                                                                                                                                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area            | Meridian consumption boundary                                                                                                                                                                                                                          |
| Severity        | No issue identified                                                                                                                                                                                                                                    |
| Status          | Reviewed                                                                                                                                                                                                                                               |
| Finding         | Import, producer meaning, evidence selection, scale mapping, Academic Period membership, derived overrides, Grade calculation, and formal reporting are assigned to coherent authorities without requiring Meridian to mutate Concord or Core records. |
| Required action | None beyond MCB-001 through MCB-004.                                                                                                                                                                                                                   |

### 12.17 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 4
No-issue findings: 1
```

The Meridian consumption boundary is approved as part of the Concord conceptual foundation.

The four resolved findings strengthen reproducibility and prevent invalid downstream transformation. They do not require:

* a new Concord record type;
* a new Concord ADR;
* changes to Core;
* changes to the representative manifests;
* or changes to their SHA-256 digests.

Meridian runtime implementation remains dependent on a supported import contract or adapter, exact producer-scale mappings, explicit selection policy, Academic Period policy, override contracts, and report contracts.

## 13. Privacy and Data Minimization Review

### 13.1 Review Question

Does the Concord foundation preserve record-specific privacy, minimize published educational data, prevent authorization leakage through references and metadata, and reconcile historical preservation with restricted access without weakening provenance?

### 13.2 Privacy Boundary

The privacy architecture distinguishes:

```text
native Concord record privacy
    -> privacy-safe publication projection
    -> Core publication discovery
    -> Meridian source authorization
    -> audience-aware report composition
```

These layers answer different questions.

Concord owns:

* native record privacy;
* privacy inheritance and record-specific restriction;
* privacy-aware evidence, Score, and Moderation projections;
* publication-time minimization;
* and the decision whether a safe manifest can be produced.

Core owns:

* canonical identity and publication infrastructure;
* publication-path and digest validation;
* and shared authorization capabilities where defined.

Core publication does not authorize manifest access.

Meridian owns:

* source-access validation;
* derived-result access;
* audience-aware report composition;
* report minimization;
* report delivery authorization;
* and report-snapshot provenance.

An authorized reference to one record does not authorize unrestricted access to:

* its source evidence;
* every related Subject;
* full student writing;
* peer comments;
* teacher notes;
* Moderation rationale;
* external files;
* or sibling-module records.

### 13.3 Direct Classifications and Resolution Modes

The initial Privacy Policy vocabulary contains four direct classifications:

```text
teacher_restricted
teacher_and_subjects
group_and_teacher
classroom_shared
```

It also contains two policy-resolution modes:

```text
inherited
external_policy
```

`inherited` and `external_policy` are not independently usable final audience classifications.

An inherited policy must resolve through a valid parent record.

An external policy must resolve through an explicit policy reference.

Before a record is accessed, projected, published, or reported, the system must resolve an effective privacy policy.

The effective audience must account for:

* record-specific classification;
* applicable parent policy;
* explicit audience references;
* applicable external policy;
* record type;
* Subject context;
* Group context;
* current or superseded state;
* and authorized role.

Privacy classifications such as `teacher_and_subjects` and `group_and_teacher` are not necessarily totally ordered. When two policies authorize different audience sets, the system must evaluate their actual effective audiences rather than assume that one label is universally more restrictive.

### 13.4 Record-Specific Privacy

Privacy remains attached to the record or relationship whose disclosure is being evaluated.

The visibility of an Artifact must not be inferred from:

* its Authors;
* its Subjects;
* Group Membership;
* its Score target;
* its scorer;
* or another related record.

For example:

```text
peer observation source
    -> teacher_restricted

derived teacher-approved Score
    -> teacher_and_subjects

parent or guardian report field
    -> separately authorized Meridian projection
```

Those policies may legitimately differ because the records disclose different information.

A child record may narrow its audience.

A broader child audience requires an explicit authorized privacy decision. It must not arise merely from inheritance, association, or a less restrictive parent default.

### 13.5 Sensitive Native Information

Concord must not copy detailed records from external institutional domains merely to explain classroom context.

In particular, Concord should preserve only a minimal reference or safe reason code rather than copying:

* medical information;
* disability or accommodation details;
* counseling information;
* disciplinary records;
* family circumstances;
* formal incident reports;
* or other unrelated institutional narrative.

A contextual state such as:

```text
excused
absent
external_policy
permission_restricted
```

does not require Concord to reproduce the underlying sensitive institutional record.

The external authority remains authoritative.

### 13.6 Artifact, Author, Subject, and Evidence Privacy

Author, Subject, and source-evidence privacy remain independent.

A peer observer’s identity may be more restricted than:

* the fact that evidence was reviewed;
* the teacher’s resulting Score;
* or a privacy-safe report summary.

A multi-Subject Artifact remains one source Artifact. Its existence does not authorize every Subject to view:

* the full Artifact;
* information about every other Subject;
* all Author identities;
* or every later Score supported by that source.

Evidence locators help an authorized reviewer find relevant material. They do not broaden source authorization.

Access to a Score Evidence Link similarly does not imply access to the complete evidence source.

### 13.7 Historical Privacy

Historical preservation does not mean unrestricted visibility.

The following may require equal or greater protection after they become inactive, rejected, corrected, or superseded:

* disputed peer observations;
* corrected Author or Subject assignments;
* rejected Contribution Claims;
* superseded Moderation Records;
* withdrawn evidence relationships;
* teacher notes;
* superseded Scores;
* and earlier manifest revisions.

A record must not become more visible merely because it is:

* no longer current;
* rejected;
* superseded;
* withdrawn from use;
* or retained only for provenance.

Historical audit access remains permission-controlled.

### 13.8 Redaction and Derivatives

Redaction creates a derivative.

It does not silently alter the Core-retained source scan or other authoritative source record.

A redacted derivative must preserve provenance to:

* its restricted source;
* the reason for redaction;
* the responsible Actor or process;
* generation time;
* and the applicable access policy.

The restricted source remains under its existing controls unless a separate legal or institutional deletion process requires otherwise.

A redacted derivative must not be represented as the unmodified source.

### 13.9 Manifest Minimization

A Concord Academic Result Manifest contains sensitive educational data and must contain only the information needed to:

* identify the Activity and exact publication;
* interpret included Criteria and Scoring Scales;
* interpret included Scores and dispositions;
* preserve necessary native history;
* preserve consequential evidence lineage;
* establish required Moderation state;
* and support explicit downstream policy.

The manifest must not ordinarily contain:

* source scans;
* complete Artifact contents;
* full student writing;
* full peer comments;
* unrestricted teacher notes;
* detailed Moderation rationale;
* credentials;
* access tokens;
* private repository information;
* family information;
* medical, disability, counseling, or disciplinary details;
* or unrelated Activity records.

Student, Group, Actor, source, and target identity should use durable references rather than names when references are sufficient.

### 13.10 Effective Manifest Privacy

Publication-time validation must resolve the effective privacy policy of every included:

* Score projection;
* evidence-lineage projection;
* Moderation projection;
* narrative field;
* and display snapshot.

The effective manifest audience must be no broader than the audience permitted for every included projection.

The manifest-level `privacy_classification` is a conservative access summary. It does not:

* replace record-specific policies;
* authorize access by itself;
* authorize access to source evidence;
* or authorize every later report audience.

When one required projection is `teacher_restricted`, a manifest containing that projection cannot be made available under `teacher_and_subjects` merely because the associated Score uses that broader classification.

When projections cannot be combined under one safe effective audience, Concord must:

* omit an optional sensitive projection when the contract permits omission;
* use an adequate privacy-safe structured summary;
* defer publication;
* or use a later explicitly authorized publication contract.

Concord must not lower a child record’s protection to make a combined manifest easier to publish.

### 13.11 Published Text and Display Metadata

Every published free-text or display field must be concise, purpose-limited, and privacy-safe.

This requirement applies to fields such as:

* Activity title snapshots;
* revision reasons;
* Criterion labels and definitions;
* Scoring Scale names, labels, meanings, and descriptions;
* Score rationale;
* evidence relevance descriptions;
* Moderation qualifications;
* display labels;
* locator notes;
* and access hints.

Published text must not contain, when durable references or structured state are sufficient:

* student or family names;
* direct personal identifiers;
* sensitive medical, disability, counseling, or disciplinary information;
* credentials or secrets;
* bearer tokens;
* signed access URLs;
* machine-local user paths;
* unrestricted source excerpts;
* or information unrelated to interpreting the published result.

Optional native narrative should be omitted or replaced with a privacy-safe structured summary when its complete text is unnecessary downstream.

Required Criterion or Scale semantics must not be silently rewritten. If required semantic text contains prohibited personal information, publication must fail until Concord can supply a valid privacy-safe semantic revision or an approved immutable public-definition reference.

### 13.12 External Locators

A persisted External Locator must use a stable provider-neutral or provider-qualified identity rather than storing transient authorization material.

Concord must not persist:

* passwords;
* credentials;
* API keys;
* bearer tokens;
* session cookies;
* signed URL query parameters;
* secret repository URLs;
* or other embedded authentication material.

When a provider requires an expiring signed URL, Concord should preserve the stable underlying locator and generate the signed access URL only during an authorized access operation.

An External Locator identifies where an authorized user may resolve a source. It does not establish authorization to retrieve it.

### 13.13 Core Publication and Catalog Metadata

Core Publication Records and the derived catalog must remain privacy-minimized.

Concord-supplied identifiers and paths must not contain direct PII.

Concord-supplied Core registration or discovery display text must also be privacy-safe, including:

* Academic Work Registration titles;
* work labels;
* manifest paths;
* record-set identifiers;
* and other producer-supplied catalog metadata.

The derived Core catalog must not expose manifest contents or become an authorization bypass.

Discovery and retrieval authorization remain separate operations.

### 13.14 Meridian Reports

Meridian may present less information than the Concord manifest.

A report audience does not inherit every source authorization held by the report generator.

Report composition must separately evaluate:

* report purpose;
* intended audience;
* source authorization;
* field necessity;
* Subject scope;
* peer or Group-member privacy;
* intervention-information separation;
* override visibility;
* and delivery authorization.

A student-facing or parent-facing report may include a derived Score or proficiency result while excluding:

* peer identities;
* full evidence lineage;
* private teacher rationale;
* full Moderation qualification;
* unrelated Group-member information;
* and restricted source locations.

A frozen report snapshot preserves what was issued, but its continued access remains subject to applicable authorization and retention policy.

### 13.15 Retention and Deletion Boundary

The conceptual foundation correctly distinguishes ordinary correction from exceptional physical deletion.

Ordinary correction uses:

* supersession;
* withdrawal;
* invalidation;
* redaction derivatives;
* and append-preserving history.

Physical deletion may be required by:

* law;
* institutional retention policy;
* privacy obligations;
* accidental import cleanup;
* or another separately authorized process.

Before production deployment, Paper Data Suite requires a coordinated retention and deletion policy covering:

* Core-retained source scans;
* Concord native records;
* routed and redacted derivatives;
* immutable published manifests;
* Core Publication Records and withdrawals;
* derived catalogs;
* Meridian imports and calculations;
* frozen report snapshots;
* audit records;
* backups;
* and external-source references.

That implementation policy must define what is:

* physically deleted;
* access-revoked;
* withdrawn;
* tombstoned;
* retained under restriction;
* or preserved only as non-content audit metadata.

This requirement does not block conceptual foundation approval, but it blocks a claim of complete production privacy readiness.

### 13.16 Representative-Example Assessment

The representative examples already demonstrate:

* synthetic, non-name identifiers;
* no direct PII in record-set IDs or paths;
* record-specific native privacy;
* teacher-restricted peer and Moderation records;
* broader Score privacy where appropriate;
* privacy-safe module-qualified references;
* manifest-level conservative restriction;
* minimized evidence-lineage projections;
* no embedded source scans or full student writing;
* and separation between publication and authorization.

The seminar manifest demonstrates the intended aggregation rule:

```text
teacher_and_subjects Score projections
    + teacher_restricted Moderation projection
    -> teacher_restricted manifest
```

The examples use synthetic labels such as `Student 001`. Those are example-only display aids and are not permission to publish real student names in production manifests.

No representative manifest bytes or SHA-256 digests require modification.

### 13.17 Findings

#### PDM-001 — Privacy classifications and policy-resolution modes are underconstrained

| Field                        | Value                                                                                                                                                                                                                                                    |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Privacy Policy semantics                                                                                                                                                                                                                                 |
| Severity                     | Minor clarification                                                                                                                                                                                                                                      |
| Status                       | Resolved                                                                                                                                                                                                                                                     |
| Finding                      | `inherited` and `external_policy` are listed beside direct audience classifications, while `inherited_from` and `policy_reference` remain optional. The contract also does not define how explicit audiences interact with inherited or external policy. |
| Required action              | Distinguish direct classifications from resolution modes, make their supporting references conditional, and require effective-policy resolution before access or publication.                                                                            |
| Architecture change required | No                                                                                                                                                                                                                                                       |
| Example changes required     | No                                                                                                                                                                                                                                                       |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, under the exact heading:

> `## 7.11 Privacy Policy`

find this exact table fragment:

```markdown
| `audience_references` | Optional    | Explicit audience when the classification requires it |
| `policy_reference`    | Optional    | External policy controlling access                    |
| `reason`              | Optional    | Minimal explanation for restriction                   |
| `inherited_from`      | Optional    | Parent record supplying the default                   |
```

Replace only those four rows with:

```markdown
| `audience_references` | Conditional | Required when explicit audience identity is needed to resolve or narrow the effective policy |
| `policy_reference`    | Conditional | Required when `classification = external_policy` |
| `reason`              | Optional    | Minimal explanation for restriction |
| `inherited_from`      | Conditional | Required when `classification = inherited` |
```

In the same section, find this exact text:

```markdown
The values may later move into a shared Core contract.

### Invariants
```

Replace it with:

````markdown
The values may later move into a shared Core contract.

The following are direct audience classifications:

```text
teacher_restricted
teacher_and_subjects
group_and_teacher
classroom_shared
````

The following are policy-resolution modes:

```text
inherited
external_policy
```

A resolution mode must resolve to an effective direct classification or explicit authorized audience before access, projection, publication, or reporting.

### Invariants

````

Then add these bullets to the existing invariant list:

```markdown
* `classification = inherited` requires a valid `inherited_from` reference.
* `classification = external_policy` requires a valid `policy_reference`.
* `audience_references` may narrow an effective audience but must not silently broaden it.
* A broader child audience requires an explicit authorized privacy decision rather than automatic inheritance.
* Policies with different audience sets must be resolved from their effective audiences rather than an assumed total ordering of labels.
* Published projections must contain a resolved effective classification rather than unresolved `inherited` or `external_policy`.
````

In `docs/design/initial-concord-domain-model.md`, find this exact block:

```markdown
The initial minimum privacy vocabulary may include:

* `teacher_restricted`;
* `teacher_and_subjects`;
* `group_and_teacher`;
* `classroom_shared`;
* `inherited`;
* and `external_policy`.
```

Insert immediately after it:

```markdown
`teacher_restricted`, `teacher_and_subjects`, `group_and_teacher`, and `classroom_shared` are direct audience classifications.

`inherited` and `external_policy` are resolution modes. They require a valid parent or external policy reference and must resolve to an effective audience before access or publication.
```

#### PDM-002 — Manifest-level privacy is not tied explicitly to included projections

| Field                        | Value                                                                                                                                                                                                                |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Manifest privacy derivation                                                                                                                                                                                          |
| Severity                     | Minor clarification                                                                                                                                                                                                  |
| Status                       | Resolved                                                                                                                                                                                                                 |
| Finding                      | The manifest has one required `privacy_classification`, but the contract does not explicitly require its effective audience to be no broader than every included Score, evidence-lineage, and Moderation projection. |
| Required action              | Define conservative manifest privacy aggregation and publication-time compatibility validation.                                                                                                                      |
| Architecture change required | No                                                                                                                                                                                                                   |
| Example changes required     | No; the seminar already follows the intended rule                                                                                                                                                                    |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, under:

> `## 13.6 Concord Academic Result Manifest`

find this exact field-table row:

```markdown
| `privacy_classification` | Required | Manifest-level minimum access classification |
```

Replace it with:

```markdown
| `privacy_classification` | Required | Resolved effective manifest access classification; no broader than every included projection |
```

In the same section, find the exact final invariant:

```markdown
* Published manifest bytes are immutable.
```

Insert immediately after it:

```markdown
* Publication-time validation must resolve the effective privacy policy of every included Score, evidence-lineage, and Moderation projection.
* The effective manifest audience must be no broader than the audience permitted for every included projection.
* Manifest-level classification is a conservative access summary and does not replace record-specific authorization.
* Access to the manifest does not authorize access to referenced source evidence.
* When required projections cannot be combined under one safe audience, Concord must omit optional sensitive detail, use an adequate privacy-safe structured summary, or defer publication.
* A separate differently authorized record-set series requires an explicit later publication contract.
```

#### PDM-003 — Published narrative, display metadata, and locators lack field-level minimization rules

| Field                        | Value                                                                                                                                                                                                         |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                         | Published text and external locators                                                                                                                                                                          |
| Severity                     | Minor clarification                                                                                                                                                                                           |
| Status                       | Resolved                                                                                                                                                                                                          |
| Finding                      | General minimization language exists, but required or optional display and narrative fields could still expose names, sensitive context, unrestricted source text, signed URLs, or machine-local information. |
| Required action              | Add field-level publication-text rules and strengthen persisted External Locator restrictions.                                                                                                                |
| Architecture change required | No                                                                                                                                                                                                            |
| Example changes required     | No                                                                                                                                                                                                            |

##### Exact corrections

In `docs/design/conceptual-data-contracts.md`, under:

> `## 13.6 Concord Academic Result Manifest`

find this exact transition:

```markdown
A future reporting or evidence-publication contract may address that use separately.

### Invariants
```

Replace it with:

```markdown
A future reporting or evidence-publication contract may address that use separately.

### Published text and display minimization

Every published free-text or display field must be concise, purpose-limited, and privacy-safe.

This includes:

* Activity title snapshots;
* revision reasons;
* Criterion labels and definitions;
* Scoring Scale names, labels, meanings, and descriptions;
* Score rationale;
* evidence relevance descriptions;
* Moderation qualifications;
* display labels;
* locator notes;
* and access hints.

When durable references or structured state are sufficient, published text must not contain:

* names or direct personal identifiers;
* medical, disability, counseling, disciplinary, or family details;
* credentials, secrets, access tokens, or signed access URLs;
* machine-local user paths;
* unrestricted source excerpts;
* or unrelated narrative.

Optional native narrative should be omitted or replaced by a privacy-safe structured summary when its full text is unnecessary downstream.

Required Criterion or Scale semantics must not be silently rewritten. If required semantic text contains prohibited personal information, publication must fail until a privacy-safe semantic revision or approved immutable public-definition reference exists.

### Invariants
```

In the same file, under:

> `## 7.13 External Locator`

find this exact invariant list:

```markdown
* Credentials and access tokens must not be stored.
* The locator does not transfer ownership to Concord.
* File or account ownership does not establish Artifact authorship.
* Availability must be tracked independently.
```

Replace it with:

```markdown
* Credentials, access tokens, passwords, API keys, session secrets, and signed authorization parameters must not be persisted.
* A persisted `locator` or `access_hint` must not contain embedded authentication material.
* When access requires an expiring signed URL, Concord preserves a stable underlying locator and generates the signed URL only during an authorized access operation.
* Machine-local paths containing personal user-directory information must not be used when a stable workspace-relative or provider-owned locator is available.
* The locator does not transfer ownership to Concord.
* File or account ownership does not establish Artifact authorship.
* Availability must be tracked independently.
```

In ADR 0015, under the exact heading:

> `## Privacy and Data Minimization`

find this exact ending:

```markdown
Concord privacy rules, workspace authorization, Meridian source-access rules, and report-audience policy remain applicable.

## Publication Kind and Capabilities
```

Replace it with:

```markdown
Concord privacy rules, workspace authorization, Meridian source-access rules, and report-audience policy remain applicable.

### Effective manifest privacy

Publication-time validation must resolve the effective privacy policy of every included Score, evidence-lineage, Moderation, narrative, and display projection.

The effective manifest audience must be no broader than the audience permitted for every included projection.

Manifest-level classification is a conservative access summary rather than an authorization grant or substitute for record-specific policy.

When required projections cannot be combined under one safe audience, Concord must omit optional sensitive detail, use an adequate privacy-safe structured summary, or defer publication.

Access to a manifest does not authorize access to referenced source evidence.

### Published text and registration metadata

Published free-text and display metadata must be concise, purpose-limited, and privacy-safe.

Concord must not publish names or direct personal identifiers when durable references are sufficient.

It must not place sensitive medical, disability, counseling, disciplinary, family, credential, secret, signed-access, machine-local-user-path, or unrestricted source-content information in:

* Activity title snapshots;
* Academic Work Registration titles;
* manifest paths;
* record-set identifiers;
* revision reasons;
* Criterion or Scale display text;
* Score rationale;
* evidence relevance descriptions;
* Moderation qualifications;
* locator notes;
* access hints;
* or other producer-supplied discovery metadata.

Optional narrative should be omitted or reduced to a privacy-safe structured summary when full text is unnecessary.

Required semantic definitions must not be silently altered. Publication must fail when required Criterion or Scale meaning cannot be represented safely and exactly.

## Publication Kind and Capabilities
```

#### PDM-004 — Formal retention and legal-deletion behavior remains an implementation dependency

| Field                               | Value                                                                                                                                                                                                                                                                                                       |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                                | Retention, deletion, and immutable publication                                                                                                                                                                                                                                                              |
| Severity                            | Follow-up implementation concern                                                                                                                                                                                                                                                                            |
| Status                              | Tracked                                                                                                                                                                                                                                                                                                     |
| Finding                             | ADR 0007 correctly distinguishes ordinary append-preserving correction from exceptional deletion, but the suite does not yet define coordinated retention and legal-deletion behavior across source scans, Concord records, manifests, Core publications, Meridian imports, reports, catalogs, and backups. |
| Required action                     | Establish a permission-controlled, auditable suite-level retention, access-revocation, withdrawal, redaction, and legal-deletion policy before production deployment.                                                                                                                                       |
| Architecture change required        | Not necessarily; implementation work may reveal a need for additional shared contracts                                                                                                                                                                                                                      |
| Blocks conceptual approval          | No                                                                                                                                                                                                                                                                                                          |
| Blocks production privacy readiness | Yes                                                                                                                                                                                                                                                                                                         |

No governing-document correction is required during this foundation pass. Keep this finding `Tracked`.

#### PDM-005 — Privacy ownership and minimization boundaries are coherent

| Field           | Value                                                                                                                                                                                                                                                     |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Privacy and data minimization                                                                                                                                                                                                                             |
| Severity        | No issue identified                                                                                                                                                                                                                                       |
| Status          | Reviewed                                                                                                                                                                                                                                                  |
| Finding         | Record-specific privacy, opaque identifiers, separation of source evidence from projections, redacted derivatives, historical restriction, publication-versus-authorization separation, and audience-aware Meridian reporting form a coherent foundation. |
| Required action | None beyond PDM-001 through PDM-004.                                                                                                                                                                                                                      |

### 13.18 Review Conclusion

```text
Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 3
Follow-up implementation concerns: 1
No-issue findings: 1
```

The Privacy and Data Minimization foundation is approved with one nonblocking implementation concern.

The three resolved minor findings make the privacy semantics enforceable and publication-safe. They do not require:

* a new foundational record type;
* changes to Core publication identity;
* changes to the representative manifest bytes;
* or changes to their SHA-256 digests.

`PDM-004` remains tracked. A coordinated suite-level retention and lawful-deletion policy is required before production privacy readiness may be claimed.

## 14. Representative-Example Consistency Review

### 14.1 Review Question

Do the seminar, laboratory, project, shared README, and cross-example validation remain internally consistent with the governing contracts after the foundation-review corrections, including exact manifest bytes, source lineage, Meridian import provenance, privacy, target eligibility, supersession, and withdrawal?

### 14.2 Representative Set

The reviewed representative set consists of:

* `docs/design/examples/README.md`;
* `docs/design/examples/seminar-contract-example.md`;
* `docs/design/examples/laboratory-contract-example.md`;
* `docs/design/examples/project-contract-example.md`;
* and `docs/design/examples/cross-example-validation.md`.

The cases collectively represent:

```text
seminar
    -> standards-based Activity
    -> individual Scores
    -> peer Moderation
    -> Quillan lineage
    -> native Score and publication supersession

laboratory
    -> mixed Activity
    -> Group and individual targets
    -> local and standard-backed Scores
    -> ScoreForm lineage
    -> one publication

project
    -> mixed long-running Activity
    -> Group and individual targets
    -> external technical evidence
    -> native Score and publication supersession
    -> evidence-only addendum
    -> local-criteria-only published addendum
```

The represented domain states remain sufficient to test the Concord foundation without introducing case-specific foundational record types.

### 14.3 Exact Manifest Contract

The shared README states that exact published manifest blocks omit:

```text
record_owner
record_kind
```

when those fields are only illustrative envelope notation and are not part of the governing serialized manifest contract.

The conceptual Concord Academic Result Manifest field table does not define either field.

However, all six exact manifest JSON blocks currently contain:

```json
"record_kind": "concord_academic_result_manifest",
"record_owner": "concord",
```

The affected manifests are:

1. seminar revision 1;
2. seminar revision 2;
3. laboratory revision 1;
4. project primary revision 1;
5. project primary revision 2;
6. project retrospective revision 1.

These are not merely explanatory YAML blocks. They are the exact byte blocks whose SHA-256 digests are asserted by the corresponding Core Publication Records.

The fields therefore cannot be corrected only in prose.

The required sequence is:

```text
remove the two invalid top-level fields
    -> preserve every other byte and field
    -> validate JSON
    -> normalize to exactly one final LF
    -> recalculate SHA-256
    -> update the corresponding Core Publication Record digest
    -> rerun cross-example mechanical validation
```

Only the two top-level manifest fields are removed.

Nested contract-native fields named `record_kind`, including those inside:

* `source_activity`;
* Module Record References;
* source-record lineage;
* and other typed references

remain unchanged.

### 14.4 Shared Reference Conventions

Issue #13 has now formalized both previously provisional value objects:

* Score-Target Reference;
* and Core Publication Reference.

The representative README and cross-example validation still describe them as unresolved provisional conventions.

That language is obsolete.

The example notation itself is compatible with the finalized contracts:

```yaml
target_reference:
  target_kind: core_student
  target_id: stu_001
  owning_system: core
```

and:

```yaml
source_publication_reference:
  publication_id: pub_scoreform_resultset_001
```

The documentation must now identify those as contract-native value objects.

The finalized Core Publication Reference permits an optional `publication_schema_version` when compatibility requires it.

### 14.5 Source-Publication Conditionality

The README still describes a source Publication Record reference as:

> optional when no exact source publication is known

That formulation is no longer sufficiently precise.

The governing rule is:

* when a source revision was resolved through a Core Publication Record, or verified against an exact compatible Core publication, `source_publication_reference` is required;
* when no source publication exists, another immutable source-version mechanism is required;
* and a later publication must not be substituted merely because it contains the same logical source-record ID.

The seminar and laboratory exact manifests already preserve the required exact source Publication References.

No exact manifest change is required for cross-producer lineage.

### 14.6 Meridian Import Provenance

The three principal examples contain abbreviated Meridian import-provenance lists written before MCB-001 was resolved.

Every represented Meridian import must preserve:

* Core Publication Record ID and publication-schema version;
* exact `ModuleWorkRef`;
* exact source Activity `ModuleRecordRef`;
* publication kind and declared capabilities;
* manifest path;
* manifest digest algorithm and exact digest;
* manifest contract version;
* record-set identity and revision;
* exact Academic Work Registration revision;
* predecessor Publication Record ID when present;
* withdrawal state observed at import;
* withdrawal-state observation time;
* import time;
* and the supported Meridian import-contract or adapter version.

Case-specific interpretation state remains additional information rather than a substitute for that publication observation.

Examples include:

* standard-backed versus local Score classification;
* Group versus individual target identity;
* exact Scale semantics;
* native supersession;
* evidence lineage;
* and Moderation state.

### 14.7 Target Consistency

The examples preserve Group and individual Score targets correctly.

The laboratory and project cases do not fabricate individual Concord Scores from Group Scores.

The governing downstream rule is now explicit:

```text
core_student target
    -> may be directly eligible for student-level Meridian evidence

non-student target
    -> remains non-student downstream
```

The representative cases require no record or manifest changes for this rule.

Their Meridian prose should continue to state that Group Membership, authorship, Subject context, and Artifact association do not synthesize student targets.

### 14.8 Privacy Consistency

The exact manifest privacy examples remain consistent with the resolved privacy contract.

In particular, the seminar manifests demonstrate:

```text
teacher_and_subjects Score projections
    + teacher_restricted Moderation projection
    -> teacher_restricted manifest
```

The examples:

* use synthetic identifiers;
* contain no real student names;
* do not embed source scans;
* do not embed full student writing;
* preserve minimized evidence lineage;
* preserve structured Moderation state;
* and distinguish publication from authorization.

The shared README should now state explicitly that:

* all included projection policies must resolve before publication;
* the manifest audience must be no broader than every included projection;
* and unresolved `inherited` or `external_policy` modes are not valid published classifications.

No exact manifest bytes require alteration for privacy.

### 14.9 Withdrawal Coverage

The representative set does not contain a complete Publication Withdrawal record.

The project example provides a bounded treatment that establishes:

* withdrawal is Core-owned;
* withdrawal differs from publication supersession;
* withdrawal preserves the Publication Record and manifest;
* a withdrawn series head does not reactivate its predecessor;
* and a later correction requires a new manifest and Publication Record.

That bounded treatment is sufficient for this conceptual review.

The seminar, laboratory, and README prose must not say that the project case “exercises” withdrawal.

They should say that the project case bounds or documents withdrawal semantics without instantiating a complete withdrawal record.

### 14.10 Mechanical Validation

After removing the two invalid top-level manifest fields, mechanical validation must confirm for all six manifest blocks:

1. valid UTF-8 JSON;
2. LF line endings;
3. exactly one final LF;
4. no comments, placeholders, or ellipses;
5. absence of top-level `record_owner`;
6. absence of top-level `record_kind`;
7. preservation of required nested typed-reference fields;
8. exact SHA-256 equality;
9. exact agreement between each manifest and its Core Publication Record;
10. unchanged record-set identity and revision;
11. unchanged manifest path;
12. unchanged manifest contract version;
13. unchanged publication-series relationships;
14. unchanged capabilities;
15. and unchanged Academic Work Registration revision.

Changing the digest does not create a new conceptual manifest revision in these examples because the previously asserted fixtures were invalid representations of the intended contract rather than historical publications that actually occurred.

The corrected synthetic fixture replaces the invalid example before implementation.

### 14.11 Findings

#### REC-001 — Exact manifest fixtures include forbidden example-only envelope fields

| Field                                | Value                                                                                                                                                                                                                                                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area                                 | Exact representative manifest bytes                                                                                                                                                                                                                                                                    |
| Severity                             | Major revision                                                                                                                                                                                                                                                                                         |
| Status                               | Resolved                                                                                                                                                                                                                                                                                                   |
| Finding                              | All six exact published manifest blocks include top-level `record_owner` and `record_kind`, even though the shared README identifies them as illustrative fields that must be omitted from exact JSON unless the serialized contract defines them. The Concord manifest contract does not define them. |
| Required action                      | Remove only those two top-level fields, recalculate all six SHA-256 digests, update all six Core Publication Records, and rerun mechanical validation.                                                                                                                                                 |
| Architecture change required         | No                                                                                                                                                                                                                                                                                                     |
| Exact manifest changes required      | Yes                                                                                                                                                                                                                                                                                                    |
| Publication Record changes required  | Yes, digest only                                                                                                                                                                                                                                                                                       |
| Record-set revision changes required | No                                                                                                                                                                                                                                                                                                     |

##### Exact corrections

Apply the correction to every exact JSON block in:

```text
docs/design/examples/seminar-contract-example.md
docs/design/examples/laboratory-contract-example.md
docs/design/examples/project-contract-example.md
```

Remove exactly these two top-level lines wherever they occur in an exact manifest block:

```json
  "record_kind": "concord_academic_result_manifest",
  "record_owner": "concord",
```

Do not remove nested `record_kind` fields from typed references.

The following one-time script performs the byte correction and updates every matching digest in the three files:

````python
#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

FILES = {
    Path("docs/design/examples/seminar-contract-example.md"): 2,
    Path("docs/design/examples/laboratory-contract-example.md"): 1,
    Path("docs/design/examples/project-contract-example.md"): 3,
}

JSON_BLOCK = re.compile(
    r"```json\n(?P<body>\{.*?\}\n)```",
    flags=re.DOTALL,
)

RECORD_KIND_LINE = (
    '  "record_kind": "concord_academic_result_manifest",\n'
)
RECORD_OWNER_LINE = (
    '  "record_owner": "concord",\n'
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


for path, expected_manifest_count in FILES.items():
    original_text = path.read_text(encoding="utf-8")
    digest_replacements: dict[str, str] = {}
    changed_count = 0

    def correct_manifest(match: re.Match[str]) -> str:
        nonlocal changed_count

        body = match.group("body")
        parsed = json.loads(body)

        if (
            parsed.get("producer_module_id") != "concord"
            or "record_set_id" not in parsed
            or "record_set_revision" not in parsed
        ):
            return match.group(0)

        if parsed.get("record_kind") != "concord_academic_result_manifest":
            raise RuntimeError(
                f"{path}: expected top-level manifest record_kind"
            )

        if parsed.get("record_owner") != "concord":
            raise RuntimeError(
                f"{path}: expected top-level manifest record_owner"
            )

        old_digest = sha256_text(body)

        corrected = body.replace(RECORD_KIND_LINE, "", 1)
        corrected = corrected.replace(RECORD_OWNER_LINE, "", 1)

        corrected_parsed = json.loads(corrected)

        if "record_kind" in corrected_parsed:
            raise RuntimeError(
                f"{path}: top-level record_kind was not removed"
            )

        if "record_owner" in corrected_parsed:
            raise RuntimeError(
                f"{path}: top-level record_owner was not removed"
            )

        if not corrected.endswith("\n"):
            raise RuntimeError(
                f"{path}: corrected manifest must end with one LF"
            )

        new_digest = sha256_text(corrected)
        digest_replacements[old_digest] = new_digest
        changed_count += 1

        return f"```json\n{corrected}```"

    corrected_text = JSON_BLOCK.sub(correct_manifest, original_text)

    if changed_count != expected_manifest_count:
        raise RuntimeError(
            f"{path}: corrected {changed_count} manifests; "
            f"expected {expected_manifest_count}"
        )

    for old_digest, new_digest in digest_replacements.items():
        if old_digest not in corrected_text:
            raise RuntimeError(
                f"{path}: documented old digest {old_digest} not found"
            )

        corrected_text = corrected_text.replace(
            old_digest,
            new_digest,
        )

        print(f"{path}: {old_digest} -> {new_digest}")

    path.write_text(corrected_text, encoding="utf-8", newline="\n")

print("Corrected six exact manifests and their documented digests.")
````

Run from the repository root:

```bash
python tools_or_temporary_script_name.py
```

Then verify:

```bash
git diff --check
git diff -- docs/design/examples/
```

The diff should show:

* two removed JSON lines per manifest;
* one changed SHA-256 digest per manifest;
* no other exact-manifest field changes.

#### REC-002 — Shared example conventions retain resolved provisional language

| Field                           | Value                                                                                                                                                                                                                                                     |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                            | Shared notation and cross-example validation                                                                                                                                                                                                              |
| Severity                        | Minor clarification                                                                                                                                                                                                                                       |
| Status                          | Resolved                                                                                                                                                                                                                                                      |
| Finding                         | The README and cross-example validation still describe Score-Target Reference and Core Publication Reference as provisional, retain obsolete “when known” source-publication wording, and ask issue #13 to decide matters already resolved by the review. |
| Required action                 | Replace the provisional language with the finalized value-object contracts and source-publication rules.                                                                                                                                                  |
| Architecture change required    | No                                                                                                                                                                                                                                                        |
| Exact manifest changes required | No                                                                                                                                                                                                                                                        |

##### Exact corrections: README Score-Target Reference

In `docs/design/examples/README.md`, under the exact heading:

> `### 10.7 Score-Target Reference`

replace:

> The current conceptual contract defines supported target kinds and invariants but does not yet publish a field table. To keep the examples explicit and prevent accidental substitution of a Subject Reference, this directory uses the following provisional example notation:

with:

```markdown
The conceptual contract defines the Score-Target Reference field table and invariants. To prevent accidental substitution of a Subject Reference, every example uses the following contract-native notation:
```

Replace:

> This provisional shape is an example-document convention, not an amendment to the governing conceptual contract. Issue #13 should either accept it or add the missing Score-Target Reference field table before serialized contracts are defined.

with:

```markdown
This is the contract-native Score-Target Reference shape.

A Score target is not an Artifact Subject and must not be represented through Subject Reference fields.
```

Remove the now-duplicated following sentence when necessary:

> A Score target is not an Artifact Subject. Do not use `subject_kind` and `subject_id` for `target_reference`.

##### Exact corrections: README Core Publication Reference

Under the exact heading:

> `### 10.10 Core Publication Reference`

replace:

> The current conceptual contract requires an exact source publication reference but does not yet publish a separate field table for that reference. These examples therefore use the following provisional notation:

with:

```markdown
The conceptual contract defines a Core Publication Reference value object. These examples use the following contract-native notation:
```

Replace:

> This provisional shape is example-document notation. Issue #13 should either accept it or add a shared Core Publication Reference value-object contract before serialized Concord manifests are finalized.

with:

```markdown
The `publication_id` is required.

An optional `publication_schema_version` may be included when needed for compatibility.
```

Replace these two bullets:

```markdown
* optional when no exact source publication is known;
* required when a case claims exact published-source lineage;
```

with:

```markdown
* required when the source revision was resolved through, or verified against, an exact Core Publication Record;
* omitted only when another immutable source-version mechanism is preserved;
```

In the same file, replace:

```text
originating producer result
    -> optional exact Core source publication
    -> Concord evidence relationship and teacher-approved Score
```

with:

```text
originating producer result
    -> conditional exact Core source publication
    -> Concord evidence relationship and teacher-approved Score
```

Replace:

> source Publication Record lineage where the case claims that exact source publication is known;

with:

```markdown
source Publication Record lineage whenever the source revision was resolved through or verified against an exact Core publication;
```

Replace:

> cross-producer ScoreForm or Quillan lineage identifies the originating module record and exact source publication where known;

with:

```markdown
cross-producer ScoreForm or Quillan lineage identifies the originating module record and the exact source publication whenever required by the source-resolution contract;
```

##### Exact corrections: README completion language

Replace:

> every typed relationship uses its contract-native reference shape or a clearly identified provisional convention where the contract lacks a field table;

with:

```markdown
every typed relationship uses its contract-native reference shape;
```

Near the end of the README, replace:

```markdown
After all four documents are complete, issue #13 should perform the skeptical foundation review and determine:

* whether the Concord conceptual architecture is ready to govern serialized contracts and implementation work;
* whether the provisional Score-Target and Core Publication Reference notations require formal value-object contracts;
* whether ADR 0015 should be accepted, revised, or rejected;
* and which Core and Meridian APIs must be released before runtime publication work begins.
```

with:

```markdown
Issue #13 performs the skeptical foundation review and determines:

* whether the Concord conceptual architecture is ready to govern serialized contracts and implementation work;
* whether ADR 0015 should be accepted, revised, or rejected;
* and which Core, ScoreForm, Quillan, and Meridian contracts must be released before runtime publication work begins.

Issue #13 has already formalized the Score-Target Reference and Core Publication Reference value objects and has determined that bounded withdrawal coverage is sufficient for the conceptual examples.
```

##### Exact corrections: cross-example validation Section 4.6

In `docs/design/examples/cross-example-validation.md`, replace the complete subsection beginning with:

> `### 4.6 Readiness for issue #13`

and ending immediately before:

> `## 5. Representative Case Summary`

with:

````markdown
### 4.6 Issue #13 Reconciliation

```text
FOUNDATION REVIEW IN PROGRESS
````

Issue #13 has resolved the previously provisional:

* Score-Target Reference contract;
* Core Publication Reference contract;
* source-publication conditionality;
* and withdrawal no-fallback semantics.

The representative examples do not require a complete Publication Withdrawal fixture for conceptual approval.

The remaining issue #13 determinations are:

* whether ADR 0015 should be accepted, revised, or rejected;
* whether the corrected exact manifest fixtures pass final mechanical validation;
* and which Core, ScoreForm, Quillan, and Meridian APIs or public contracts must be released before implementation.

````

##### Exact corrections: cross-example validation Section 28

Replace subsections `### 28.1` through `### 28.3` with:

```markdown
### 28.1 Score-Target Reference — resolved

Issue #13 formalized the Score-Target Reference as a shared value object with:

```text
target_kind
target_id
owning_system
optional contract_version
````

The representative examples already use the compatible field shape.

### 28.2 Core Publication Reference — resolved

Issue #13 formalized the Core Publication Reference as:

```text
publication_id
optional publication_schema_version
```

The representative source-publication references already use the required `publication_id`.

### 28.3 Withdrawal fixture — resolved

No complete Publication Withdrawal record is represented.

Issue #13 determined that the bounded project treatment is sufficient because it explicitly preserves the distinction among:

* native correction;
* manifest revision;
* publication supersession;
* withdrawal;
* structural series head;
* and current selectable publication.

The examples must state the no-fallback rule but need not invent a Core-owned withdrawal record.

````

#### REC-003 — Principal Meridian sections retain obsolete abbreviated import provenance

| Field | Value |
|---|---|
| Area | Seminar, laboratory, and project Meridian sections |
| Severity | Minor clarification |
| Status | Resolved |
| Finding | Each principal example preserves only a subset of the publication observation now required by MCB-001. |
| Required action | Replace or supplement each abbreviated list with the complete mandatory import-provenance list. |
| Architecture change required | No |
| Exact manifest changes required | No |

##### Exact correction: seminar

In `docs/design/examples/seminar-contract-example.md`, under:

> `## 25. Meridian Consumption Boundary`

replace the list beginning with:

> `- publication_id;`

and ending with:

> `- and import time.`

with:

```markdown
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
````

Keep the following policy list beginning with:

> Meridian then applies explicit policy for:

unchanged.

##### Exact correction: laboratory

In `docs/design/examples/laboratory-contract-example.md`, locate the Meridian list containing this exact ending:

```markdown
- manifest contract version;
- `record_set_id`;
- `record_set_revision`;
- Academic Work Registration revision;
- source Activity reference;
- source-publication lineage;
- withdrawal state;
- and import time.
```

Replace the complete import-provenance list with:

```markdown
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
```

Immediately after that list, add:

```markdown
For interpretation of this laboratory result, Meridian must additionally preserve:

- standard-backed versus local Score classification;
- Group versus individual target identity;
- exact Scoring Scale identity and meaning;
- ScoreForm source-record and source-publication lineage;
- native Score dispositions;
- and applicable Moderation state.
```

Keep the following text beginning with:

> Meridian then owns explicit policy for:

unchanged.

##### Exact correction: project

In `docs/design/examples/project-contract-example.md`, replace the block beginning with:

> For the primary Activity, Meridian must preserve:

and ending with:

> * and the teacher's selected or excluded evidence under Meridian policy.

with:

```markdown
For every imported Concord publication, Meridian must preserve:

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

For interpretation of the primary Activity, Meridian must additionally preserve:

- standard-backed versus local Score classification;
- Group versus individual target identity;
- the exact Scoring Scale revision and level meaning;
- current versus superseded Score state;
- external project-evidence lineage;
- Moderation state;
- and the evidence selected or excluded under Meridian policy.
```

#### REC-004 — Withdrawal coverage is overstated in three example descriptions

| Field                           | Value                                                                                                                                                                                                     |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area                            | Withdrawal coverage claims                                                                                                                                                                                |
| Severity                        | Minor clarification                                                                                                                                                                                       |
| Status                          | Resolved                                                                                                                                                                                                      |
| Finding                         | The README, seminar, and laboratory prose say the project example exercises withdrawal, while the project and cross-example validation correctly state that no complete withdrawal record is represented. |
| Required action                 | Describe the project as bounding withdrawal semantics rather than exercising a withdrawal fixture.                                                                                                        |
| Architecture change required    | No                                                                                                                                                                                                        |
| Exact manifest changes required | No                                                                                                                                                                                                        |

##### Exact correction: README

In `docs/design/examples/README.md`, replace:

> Tests long-running collaborative work, changing Membership, child Groups, Activity Markers, Work Items, Dependencies, Events, Attachments, External References, Contribution Claims, externally owned technical evidence, native Score supersession, manifest revision, Core publication supersession, and withdrawal.

with:

```markdown
Tests long-running collaborative work, changing Membership, child Groups, Activity Markers, Work Items, Dependencies, Events, Attachments, External References, Contribution Claims, externally owned technical evidence, native Score supersession, manifest revision, Core publication supersession, and bounded withdrawal semantics.
```

##### Exact correction: seminar

In `docs/design/examples/seminar-contract-example.md`, replace:

> No publication withdrawal is represented in this seminar case. The architecture can represent withdrawal through a separate immutable Core record; the project example will exercise a withdrawal scenario.

with:

```markdown
No Publication Withdrawal record is represented in this seminar case.

The project example bounds the withdrawal contract and no-fallback rule without inventing a complete Core-owned withdrawal record.
```

##### Exact correction: laboratory

In `docs/design/examples/laboratory-contract-example.md`, replace:

> This case deliberately represents one valid publication revision. Native Score supersession, Core publication supersession, and publication withdrawal are exercised by the project example rather than fabricated here.

with:

```markdown
This case deliberately represents one valid publication revision.

Native Score supersession and Core publication supersession are exercised by the project example. Publication withdrawal is bounded there without a complete withdrawal record.
```

#### REC-005 — Representative semantic coverage remains coherent

| Field           | Value                                                                                                                                                                                                                                               |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Representative-example consistency                                                                                                                                                                                                                  |
| Severity        | No issue identified                                                                                                                                                                                                                                 |
| Status          | Reviewed                                                                                                                                                                                                                                            |
| Finding         | The three principal cases and two bounded addenda continue to exercise the required Activity, routing, evidence, Moderation, scoring, target, publication, lineage, and Meridian boundaries without introducing case-specific foundational records. |
| Required action | None beyond REC-001 through REC-004.                                                                                                                                                                                                                |

### 14.12 Document Metadata

Because all five representative-example documents will change during this correction, update their revision metadata.

In `docs/design/examples/README.md`:

```markdown
**Revision date:** July 31, 2026  
**Revision:** 4 — reconciled with issue #13 foundation-review findings
```

In `docs/design/examples/cross-example-validation.md`:

```markdown
**Revision date:** July 31, 2026  
**Revision:** 5 — reconciled with issue #13 foundation-review findings
```

In each principal example:

```text
seminar-contract-example.md
laboratory-contract-example.md
project-contract-example.md
```

use:

```markdown
**Revision date:** July 31, 2026  
**Revision:** 4 — reconciled with issue #13 representative-example consistency review
```

### 14.13 Review Conclusion

```text
Blocking defects: 0
Resolved major revisions: 1
Resolved minor clarifications: 3
No-issue findings: 1
```

The representative conceptual coverage and corrected fixture set are approved.

`REC-001` was resolved by:

* removing the two invalid top-level envelope fields from all six exact manifest blocks;
* preserving all contract-native nested reference fields;
* recalculating all six SHA-256 digests;
* updating every corresponding digest occurrence and Core Publication Record;
* correcting the affected byte-length declarations;
* and enforcing LF line endings for the representative Markdown files.

`REC-002` through `REC-004` were also resolved.

The corrected representative set requires:

* no new foundational record type;
* no manifest revision-number changes;
* no publication-series changes;
* no representative scenario changes;
* and no additional architectural decision.

The examples are suitable as conceptual test vectors for subsequent serialized-contract work.

ADR 0015 was accepted after the corrected fixtures passed the required mechanical and semantic review.

## 15. ADR 0015 Disposition Review

### 15.1 Review Question

Should ADR 0015, **Publish Versioned Concord Academic Result Manifests Through the Core Registry**, be accepted, revised, or rejected after completion of the skeptical foundation review?

### 15.2 Disposition

```text
ACCEPT
```

ADR 0015 should be accepted as the governing architectural decision for publishing selected Concord academic results.

Acceptance establishes this authoritative sequence:

```text
Concord native records
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> policy-controlled Meridian import
    -> Meridian-derived proficiency, Grade, Academic Period, or report result
```

The decision preserves the required ownership boundaries:

* Concord owns native educational records, manifest semantics, manifest generation, and manifest revision;
* Core owns Academic Work Registration, Publication Records, publication integrity, supersession, withdrawal, and discovery;
* Meridian owns import selection, evidence eligibility, scale mapping, Grade-item membership, Academic Period membership, calculations, overrides, and reports;
* ScoreForm and Quillan retain ownership of their native source records;
* and external systems retain ownership of repository, CI, CAD, cloud-document, and other external evidence.

### 15.3 Basis for Acceptance

The skeptical review found no blocking architectural defect in ADR 0015.

The decision now preserves:

* explicit Activity-to-registration identity;
* one authoritative owner for each record family;
* producer-owned manifest semantics;
* immutable revision-addressed manifest bytes;
* exact SHA-256 binding;
* Core-owned immutable Publication Records;
* truthful publication capabilities;
* explicit publication supersession;
* withdrawal without predecessor fallback;
* separation of native Score supersession from publication supersession;
* exact Criterion and Scoring Scale interpretation;
* explicit standard-backed and local Score distinction;
* explicit non-score dispositions;
* Group and individual target separation;
* complete cross-producer evidence lineage;
* conservative manifest privacy;
* publication as discoverability rather than authorization;
* complete Meridian import observation;
* Meridian-owned evidence selection and scale mapping;
* and separation of Concord Score revision from Meridian override.

The representative seminar, laboratory, project, evidence-only, and local-criteria-only cases demonstrate the architecture without requiring case-specific foundational entities.

### 15.4 Rejected Alternatives

ADR 0015 appropriately rejects:

* a direct Concord-to-Meridian package dependency;
* mutable `latest.json` as an authoritative handoff;
* a Core-owned universal Score schema;
* standards-only publication as the complete integration;
* separate Core publication of every native Concord record;
* mandatory automatic publication after every Score change;
* publication as automatic Grade inclusion;
* Concord-owned Academic Period membership;
* and assumed independence of related cross-producer publications.

Those alternatives either weaken reproducibility, collapse ownership boundaries, erase producer-native meaning, create unnecessary coupling, or risk duplicate evidence use.

### 15.5 Acceptance Does Not Mean Runtime Readiness

ADR acceptance and runtime readiness are distinct.

Acceptance authorizes:

* serialized-contract design;
* schema development;
* producer and consumer adapter planning;
* coordinated Core integration work;
* and implementation sequencing.

Acceptance does not establish that current released packages can perform the workflow.

Runtime publication remains dependent on:

* released or explicitly stabilized Core Academic Work Registration and Publication Record APIs;
* a finalized Concord manifest JSON Schema;
* stabilized ScoreForm and Quillan source-result and source-publication contracts;
* a supported Meridian import contract or adapter;
* versioned Meridian source-scale mappings;
* authorization enforcement;
* cross-repository integration fixtures;
* and coordinated retention and lawful-deletion policy.

The tracked findings remain:

```text
CPL-004
    -> ScoreForm and Quillan runtime publication contracts

PDM-004
    -> suite-level retention and legal-deletion behavior
```

Neither tracked concern invalidates the architectural decision.

Both constrain production-readiness claims.

### 15.6 ADR Corrections Completed for Acceptance

The following documentation corrections were completed:

1. the ADR status was changed from `Proposed` to `Accepted`, and the acceptance date was recorded;
2. the malformed code fence and Meridian validation bullet were repaired;
3. settled architecture was distinguished from remaining implementation follow-up;
4. and the documentation-reconciliation language was changed from future tense to completed reconciliation.

These corrections did not alter the substance of the decision.

### 15.7 Findings

#### ADR-001 — ADR 0015 is architecturally acceptable

| Field           | Value                                                                                                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | ADR 0015 disposition                                                                                                                                                             |
| Severity        | No issue identified                                                                                                                                                              |
| Status          | Reviewed                                                                                                                                                                         |
| Finding         | ADR 0015 establishes a coherent producer-manifest, Core-publication, and Meridian-consumption boundary and should govern subsequent serialized-contract and implementation work. |
| Required action | Accept ADR 0015.                                                                                                                                                                 |

#### ADR-002 — ADR status and post-review governance language remain stale

| Field           | Value                                                                                                                                                                                                            |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | ADR status and follow-up governance                                                                                                                                                                              |
| Severity        | Minor clarification                                                                                                                                                                                              |
| Status          | Resolved                                                                                                                                                                                                             |
| Finding         | The ADR remains marked `Proposed`, describes documentation reconciliation in future tense, and labels remaining implementation questions as general follow-up despite issue #13 having settled the architecture. |
| Required action | Mark the ADR accepted, record the acceptance date, classify remaining questions as implementation follow-up, and update the documentation-reconciliation wording.                                                |

#### ADR-003 — Two mechanical Markdown defects remain

| Field           | Value                                                                                                                                                           |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | ADR document integrity                                                                                                                                          |
| Severity        | Minor clarification                                                                                                                                             |
| Status          | Resolved                                                                                                                                                            |
| Finding         | The Core Publication Record identity block closes with four backticks, and the Meridian validation list contains a malformed final bullet beginning with “and.” |
| Required action | Repair the code fence and validation-list punctuation.                                                                                                          |

### 15.8 Review Conclusion

```text
Disposition: Accept

Blocking defects: 0
Major revisions: 0
Resolved minor clarifications: 2
No-issue findings: 1
```

ADR 0015 is accepted and is the governing Concord academic-result publication decision.

`ADR-002` and `ADR-003` are resolved.

Therefore:

* ADR 0015 governs subsequent serialized-contract and schema work;
* the conceptual foundation is ready for final-verdict approval;
* serialized-contract work may proceed;
* runtime publication remains gated by explicit compatibility and production-readiness dependencies;
* and no further architectural revision is required before the final verdict.

## 16. Issue #13 Rubric Completion Audit

### 16.1 Purpose

This section explicitly reconciles the completed foundation review with the full issue #13 rubric.

It records:

* the required PDS2 routing and retained-source review;
* the required domain-cardinality review;
* the required optionality and domain-creep review;
* the required released-versus-proposed compatibility review;
* and an individual result for every required adversarial scenario.

This section does not reopen findings already resolved in Sections 5–15.

### 16.2 PDS2 Routing and Retained-Source Ownership

The reviewed routing sequence is:

```text
Concord creates an Artifact Page
    -> Core creates or preserves the Route Registration
    -> the QR locator contains routing identity only
    -> Core retains the canonical returned source scan
    -> Concord creates semantic Scan References
    -> Review, Moderation, Author, Subject, and Score resolution occur separately
```

The following rules are approved:

* an Artifact Page exists before its ordinary Concord route is created;
* ordinary Concord routes target Artifact Pages rather than unresolved semantic entities;
* the QR payload contains only the PDS2 routing identity;
* Activity, Session, Group, Author, Subject, Criterion, Score, and privacy meaning remain outside the locator;
* Core retains the canonical source scan and routing provenance;
* Concord owns semantic filing through Scan References;
* rescans, duplicates, corrections, and misroutes preserve the earlier retained-source history;
* a routing event does not establish Artifact Author or Artifact Subject identity;
* successful routing does not create Review, Moderation, a Score, registration, publication, or Grade eligibility;
* and Concord must not replace Core’s routing or source-retention authority with a parallel implementation.

The released Core routing baseline is sufficient for this boundary.

Academic Work Registration and publication-registry behavior remain separately gated by explicit supported versions or coordinated development contracts.

### 16.3 Domain Cardinality and Identity

The reviewed cardinality rules are:

* one Activity belongs to exactly one Core class;
* an Activity uses explicit Sessions rather than implicit time slices;
* Membership is contextual to the applicable Activity, Session, or Group rather than copied from the class roster;
* parent and child Groups remain distinct identities;
* Role Assignments and Responsibility Assignments preserve their own histories;
* one Artifact may have several Authors;
* one Artifact may have several Subjects;
* Author identity does not imply Subject identity;
* one Score Record represents one Criterion-and-target judgment in one defined context;
* repeated observations remain separate Scores unless an explicit native supersession relationship exists;
* one Score may use several evidence sources;
* one evidence source may support several Scores;
* a standard-backed Criterion has exactly one governing standard;
* a local Criterion has no governing standard;
* one Score references one exact immutable Scoring Scale revision;
* Scoring Scale values resolve unambiguously within that revision;
* and one Core publication series is identified by its work, publication kind, and stable record-set identity.

No representative example depends on an undocumented one-to-one relationship.

Group evidence may support an individual judgment, but that relationship does not alter the identities or cardinalities of the Group evidence, student target, or resulting Score.

### 16.4 Optionality and Domain Creep

The foundation preserves required structures without turning every Activity into a project-management workflow.

The following structures remain conditional:

* child Groups;
* Role Assignments beyond those required by the Activity;
* Responsibility Assignments;
* Activity Markers;
* Work Items;
* Dependencies;
* Activity Events;
* Attachments;
* Contribution Claims;
* External References;
* Criteria;
* Scores;
* Core Academic Work Registration;
* and publication.

An Activity still requires explicit Session context under the accepted Session decision, but it does not require unrelated project structures.

The representative cases establish that:

* an evidence-only Activity is valid without Criteria, Scores, academic registration, or academic-result publication;
* a local-criteria-only Activity is valid without standards-profile or Focus Standard configuration;
* a standards-based Activity need not use project-management entities;
* child Groups are created only when bounded subgroup identity matters;
* optional evidence and project records are omitted when unused;
* manifest projections are conditional on represented content;
* unused capabilities are omitted;
* and manifests do not require empty placeholder records merely to satisfy a universal shape.

No foundational entity has been made mandatory solely because one representative case uses it.

### 16.5 Released-Versus-Proposed Compatibility

The review distinguishes conceptual architecture from supported runtime behavior.

The compatibility boundary is:

```text
released Core routing and retained-source contracts
    -> available runtime baseline

Core Academic Work Registration and publication-registry architecture
    -> accepted conceptual dependency
    -> runtime use only through a released, stabilized, or explicitly coordinated contract

ScoreForm and Quillan publication contracts
    -> tracked runtime dependency

Meridian import, mapping, grading, and reporting contracts
    -> approved conceptual boundary
    -> runtime implementation still required
```

Concord documentation may use accepted unreleased architecture for planning when that status is stated explicitly.

Concord runtime code must not:

* claim support for an unreleased Core registry API;
* infer compatibility from development-branch implementation alone;
* bind to unstable ScoreForm or Quillan result contracts without an approved coordination decision;
* claim a completed Meridian adapter that does not exist;
* or present conceptual fixtures as proof of released end-to-end behavior.

The existing compatibility gates are sufficient.

`CPL-004` and `PDM-004` remain the only tracked nonblocking concerns.

### 16.6 Required Adversarial Scenario Results

|  # | Required scenario                                                                | Result                                                          | Governing review evidence                                                                                       |
| -: | -------------------------------------------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
|  1 | An Activity exists but is never registered.                                      | Represents cleanly.                                             | Explicit registration is independent of Activity creation; Sections 6.2–6.4.                                    |
|  2 | An Activity is registered but never published.                                   | Represents cleanly.                                             | Registration and publication are independent explicit operations; Sections 6.4 and 9.8.                         |
|  3 | Evidence exists but no Score is created.                                         | Represents cleanly.                                             | Evidence is independent of scoring; Section 7.2 and the evidence-only representative case.                      |
|  4 | A local Score is published but excluded from standards reporting.                | Represents cleanly.                                             | Local Scores remain outside the standards-only projection; Sections 8.3, 9.7, and 12.8.                         |
|  5 | A non-score disposition is published without a value.                            | Represents cleanly.                                             | Non-score dispositions forbid `value`; Sections 7.7 and 9.5.                                                    |
|  6 | A Score is revised after an earlier publication.                                 | Represents cleanly.                                             | Native Score supersession and publication history remain separate; Sections 10.5–10.7.                          |
|  7 | A manifest revision includes the revised Score while preserving the earlier one. | Represents cleanly.                                             | Manifest revisions preserve necessary native history; Sections 9.5, 10.5, and 10.6.                             |
|  8 | A publication is superseded without mutating the earlier Publication Record.     | Represents cleanly.                                             | Publication supersession is immutable and append-preserving; Section 10.7.                                      |
|  9 | A publication must be withdrawn.                                                 | Represents cleanly with an accepted bounded-fixture limitation. | Withdrawal is Core-owned, immutable, and has no predecessor fallback; Sections 10.8, 14.9, and 17.9.            |
| 10 | The Core catalog is deleted and rebuilt.                                         | Represents cleanly.                                             | The catalog is derived and nonauthoritative; Sections 9.8 and 9.10.                                             |
| 11 | The same manifest revision is published twice identically.                       | Represents cleanly.                                             | Exact replay reconciles to the existing Publication Record; Section 9.9.                                        |
| 12 | The same record-set revision is reused with different bytes.                     | Represents cleanly as an integrity failure.                     | Contradictory revision reuse is rejected; Section 9.9.                                                          |
| 13 | The manifest digest does not match the file.                                     | Represents cleanly as a publication failure.                    | Core verifies the exact path and SHA-256 digest; Sections 9.6 and 9.8.                                          |
| 14 | The manifest contract version is unsupported.                                    | Represents cleanly as incompatible or ineligible.               | Meridian and Core compatibility validation reject unsupported contracts; Sections 12.5 and 15.5.                |
| 15 | A Publication Record references the wrong registration revision.                 | Represents cleanly as a publication failure.                    | Publication requires the exact current registration revision; Sections 6.6 and 9.6.                             |
| 16 | Capabilities overstate the manifest contents.                                    | Represents cleanly as a validation failure.                     | Capability declarations are bidirectionally tied to projections; Section 9.7.                                   |
| 17 | A source Quillan or ScoreForm publication is also imported directly by Meridian. | Represents cleanly with a tracked runtime dependency.           | Concord exposes derivation lineage and Meridian owns overlap policy; Sections 11.12 and 12.11; `CPL-004`.       |
| 18 | Group evidence supports an individual Score.                                     | Represents cleanly.                                             | A deliberate teacher judgment and individual relevance are required; Section 7.5.                               |
| 19 | Required Moderation remains unresolved.                                          | Represents cleanly as ineligible for consequential use.         | Unresolved Moderation blocks active consequential support; Sections 7.4 and 12.11.                              |
| 20 | A Meridian override changes a derived result without changing Concord.           | Represents cleanly.                                             | Overrides remain Meridian-owned and do not mutate producer records; Section 12.13.                              |
| 21 | A Grade policy changes without changing any producer record.                     | Represents cleanly.                                             | Meridian policy and recalculation history are independent of Concord records; Sections 12.10 and 12.13.         |
| 22 | An Academic Period assignment changes without changing producer dates.           | Represents cleanly.                                             | Period membership is a separate Meridian decision; Section 12.12.                                               |
| 23 | A restricted peer source supports a less-restricted Score.                       | Represents cleanly under record-specific privacy.               | Source and Score policies may differ, while manifest privacy remains conservative; Sections 13.4 and 13.10.     |
| 24 | A published manifest is valid but ineligible for Grade use.                      | Represents cleanly.                                             | Import, structural validity, eligibility, selection, and Grade membership are distinct; Sections 12.3 and 12.5. |

Scenario totals:

```text
Required scenarios evaluated: 24
Represented cleanly: 22
Represented with accepted bounded limitation: 1
Represented with tracked runtime dependency: 1
Requires unresolved clarification: 0
Contains blocking defect: 0
```

### 16.7 Findings

#### PDS-001 — PDS2 routing and retained-source ownership are coherent

| Field           | Value                                                                                                                                                                                                                |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | PDS2 routing and retained-source ownership                                                                                                                                                                           |
| Severity        | No issue identified                                                                                                                                                                                                  |
| Status          | Reviewed                                                                                                                                                                                                             |
| Finding         | Artifact Page creation, route identity, QR minimality, Core-retained source ownership, Concord semantic filing, and downstream Author, Subject, Review, Moderation, and Score independence form a coherent boundary. |
| Required action | None.                                                                                                                                                                                                                |

#### DOM-001 — Domain cardinalities and identities are coherent

| Field           | Value                                                                                                                                                                                                                     |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Area            | Domain cardinality and identity                                                                                                                                                                                           |
| Severity        | No issue identified                                                                                                                                                                                                       |
| Status          | Reviewed                                                                                                                                                                                                                  |
| Finding         | The foundation explicitly preserves Activity, Session, Group, Membership, Author, Subject, Score, evidence-link, Criterion, Scale, and publication-series cardinalities without unresolved hidden one-to-one assumptions. |
| Required action | None.                                                                                                                                                                                                                     |

#### OPT-001 — Optional structures remain optional

| Field           | Value                                                                                                                                                              |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area            | Optionality and domain creep                                                                                                                                       |
| Severity        | No issue identified                                                                                                                                                |
| Status          | Reviewed                                                                                                                                                           |
| Finding         | Optional project, evidence, scoring, registration, and publication structures remain conditional, and the representative cases demonstrate valid bounded omission. |
| Required action | None.                                                                                                                                                              |

#### CMP-001 — Released and proposed compatibility states are adequately separated

| Field           | Value                                                                                                                                                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Area            | Released-versus-proposed compatibility                                                                                                                                                                                         |
| Severity        | No issue identified                                                                                                                                                                                                            |
| Status          | Reviewed                                                                                                                                                                                                                       |
| Finding         | The documentation distinguishes released routing behavior, accepted conceptual registry architecture, tracked producer dependencies, and incomplete Meridian runtime behavior without making unsupported compatibility claims. |
| Required action | None.                                                                                                                                                                                                                          |

### 16.8 Rubric Completion Conclusion

```text
Additional blocking defects: 0
Additional major revisions: 0
Additional minor clarifications: 0
Additional follow-up implementation concerns: 0
Additional no-issue findings: 4

Required review areas explicitly covered: 15 of 15
Required adversarial scenarios explicitly evaluated: 24 of 24
```

The issue #13 review rubric is now explicitly satisfied.

The four additional no-issue findings document previously integrated but insufficiently indexed review work.

They do not alter the architectural verdict or introduce new implementation dependencies.

## 17. Final Foundation Verdict

### 17.1 Required Verdict

```text
APPROVED WITH NONBLOCKING FOLLOW-UP
```

The Concord v0.1.0 conceptual foundation is approved.

The foundation is internally coherent, appropriately bounded, historically reproducible, privacy-conscious, and sufficiently explicit to govern subsequent serialized-contract and schema work.

The approval carries two bounded implementation concerns:

```text
CPL-004
    -> ScoreForm and Quillan source-result and source-publication contracts

PDM-004
    -> coordinated suite-level retention and lawful-deletion policy
```

Neither concern invalidates the conceptual foundation.

Both constrain runtime and production-readiness claims.

### 17.2 Approval Scope

This verdict approves:

* the Concord conceptual domain;
* module ownership boundaries;
* Activity and Session identity;
* contextual Groups, Memberships, Roles, and Responsibilities;
* Artifact, Author, Subject, Review, and Moderation distinctions;
* Criterion, Scoring Scale, and Score semantics;
* standard-backed and local Score coexistence;
* non-score dispositions;
* Group and individual target separation;
* Core Academic Work Registration integration;
* immutable Concord Academic Result Manifests;
* immutable Core Publication Records;
* manifest revision and publication supersession;
* Core-owned withdrawal with no predecessor fallback;
* cross-producer evidence lineage;
* Meridian’s consumption and policy boundary;
* privacy and data-minimization requirements;
* the corrected representative contract examples;
* and accepted ADR 0015.

This approval does not assert that the complete runtime publication workflow is currently available in released packages.

### 17.3 Final Finding Disposition

The review recorded:

```text
Total findings: 49

Blocking defects: 0
Resolved major revisions: 1
Resolved minor clarifications: 31
Tracked implementation concerns: 2
No-issue findings: 15
Unresolved blocking, major, or minor findings: 0
```

The resolved major finding was:

```text
REC-001
    -> invalid example-only fields in six exact manifest fixtures
```

The correction changed only the synthetic exact manifest fixtures and their corresponding digest declarations.

No foundational architecture was rejected or replaced.

### 17.4 Conceptual-Foundation Readiness

```text
APPROVED
```

The conceptual domain is ready to govern subsequent work.

The review found:

* one authoritative owner for each foundational concept;
* no unresolved ownership conflict;
* no necessary case-specific foundational entity;
* no hidden automatic conversion among evidence, Review, Moderation, Score, Grade, and report;
* no unresolved ambiguity between standard-backed and local Scores;
* no automatic conversion of Group Scores into individual Scores;
* no conversion of non-score dispositions into low performance;
* no collapse of native correction, manifest revision, publication supersession, withdrawal, override, Grade, or report history;
* and no unresolved contradiction in the publication architecture.

### 17.5 Serialized-Contract Readiness

```text
READY TO PROCEED
```

Serialized-contract and schema work may begin.

That work must preserve:

* the accepted ownership boundaries;
* all resolved invariants in this review;
* ADR 0015;
* exact typed-reference contracts;
* immutable revision semantics;
* conservative privacy resolution;
* exact Criterion and Scoring Scale meaning;
* source-publication lineage;
* target identity;
* and publication-versus-grading separation.

Serialized-contract readiness does not mean that production JSON Schemas already exist.

The next phase must define and validate those schemas against the approved representative examples.

### 17.6 Runtime Implementation Readiness

```text
NOT READY FOR END-TO-END PUBLICATION
```

The complete Concord-to-Core-to-Meridian runtime workflow must not yet be represented as released or production-ready.

Runtime work remains dependent on:

* released or explicitly stabilized Core Academic Work Registration APIs;
* released or explicitly stabilized Core Publication Record, supersession, withdrawal, and catalog APIs;
* a finalized and versioned Concord Academic Result Manifest JSON Schema;
* finalized public Concord record contracts;
* stabilized ScoreForm and Quillan result and publication contracts;
* supported cross-producer adapters;
* a supported Meridian import contract or adapter;
* versioned Meridian source-scale mappings;
* authorization enforcement;
* cross-repository integration fixtures;
* and coordinated retention and lawful-deletion behavior.

Native implementation work that does not invent or assume unavailable cross-module APIs may be planned separately under later implementation issues.

### 17.7 Core Release Compatibility

```text
ROUTING BASELINE AVAILABLE
REGISTRY PUBLICATION RUNTIME NOT YET RELEASE-COMPATIBLE
```

Released Core behavior and future registry architecture remain explicitly distinguished.

The current released Core routing baseline may continue to govern:

* PDS2 locators;
* Route Registrations;
* retained source scans;
* and routing provenance.

Concord must not claim released compatibility with Academic Work Registration or publication-registry behavior solely because compatible architecture or development-branch code exists.

Runtime publication requires an explicitly supported Core version or coordinated development contract.

### 17.8 Meridian Readiness

```text
CONCEPTUAL BOUNDARY APPROVED
RUNTIME IMPLEMENTATION NOT READY
```

Meridian has sufficient producer meaning to consume Concord results without heuristic reinterpretation once compatible public contracts exist.

The approved boundary defines:

* complete import observation;
* publication and withdrawal validation;
* exact target preservation;
* student versus non-student eligibility;
* exact Scale mapping identity;
* standard-backed versus local treatment;
* repeated-observation and native-supersession distinctions;
* cross-producer overlap handling;
* Academic Period ownership;
* derived overrides;
* and reproducible report snapshots.

Meridian must still implement and version those contracts and policies.

### 17.9 Publication Withdrawal Decision

No additional Concord-specific Publication Withdrawal record is required.

Withdrawal remains Core-owned.

The approved rule is:

```text
withdrawn series head
    -> remains the structural head
    -> is not currently selectable
    -> does not reactivate its predecessor
    -> requires a new explicit successor for corrected current data
```

The bounded treatment in the representative examples is sufficient for the Concord conceptual foundation.

A later cross-repository integration fixture should test the released Core withdrawal contract when the compatible runtime exists.

### 17.10 Adversarial Review Outcome

Section 16.6 individually adjudicates all 24 adversarial scenarios required by issue #13.

The results are:

```text
Represented cleanly: 22
Represented with accepted bounded limitation: 1
Represented with tracked runtime dependency: 1
Requires unresolved clarification: 0
Contains blocking defect: 0
```
The credible failure modes were:

- corrected;
- explicitly prohibited by enforceable invariants;
- demonstrated safely in the representative examples;
- represented through an accepted bounded limitation;
- or assigned to bounded nonblocking implementation follow-up.

No required scenario and no blocking failure mode remains concealed beneath the final approval.

### 17.11 Work Authorized by This Verdict

The following work may proceed:

1. formal Concord serialized-record contracts;
2. the Concord Academic Result Manifest JSON Schema;
3. schema validators and compatibility policy;
4. deterministic manifest-generation design;
5. mechanical fixture validation;
6. producer compatibility declarations;
7. Core integration planning against explicit supported versions;
8. Meridian adapter and mapping design;
9. cross-repository contract fixtures;
10. and later runtime implementation issues with explicit dependency gates.

The following claims remain prohibited:

* that the complete publication runtime is currently released;
* that unreleased Core APIs are supported;
* that ScoreForm or Quillan publication adapters already exist when they do not;
* that Meridian runtime behavior is complete;
* that production authorization and retention policy are complete;
* or that conceptual approval alone constitutes production readiness.

### 17.12 Completion Determination

Issue #13 has completed its architectural purpose.

The review now establishes, with recorded evidence:

1. the Concord conceptual foundation is sound;
2. module ownership boundaries are stable;
3. the contracts preserve required educational meaning and history;
4. the publication architecture is sufficiently complete to govern serialized-contract work;
5. Meridian can consume the proposed outputs safely under explicit future contracts;
6. ADR 0015 governs later publication work;
7. bounded withdrawal representation is sufficient;
8. no blocking, major, or minor correction remains open;
9. runtime dependencies are explicitly identified;
10. and implementation may proceed only within the readiness boundaries stated above.

The final verdict is:

```text
APPROVED WITH NONBLOCKING FOLLOW-UP
```
