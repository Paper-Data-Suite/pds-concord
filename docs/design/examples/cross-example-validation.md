# Concord Cross-Example Validation

**Status:** Pass — publication-aware representative-contract validation complete  
**Project:** Paper Data Suite  
**Module:** `pds-concord`  
**Issue:** `#12 — 11. Create representative contract examples`  
**Branch:** `12-create-representative-contract-examples`  
**Original validation date:** July 22, 2026  
**Revision date:** July 31, 2026  
**Revision:** 5 — reconciled with issue #13 foundation-review findings

## 1. Purpose

This document validates the final representative Concord contract examples against the shared conventions and governing architecture.

The reviewed documents are:

- `docs/design/examples/README.md`;
- `docs/design/examples/seminar-contract-example.md`;
- `docs/design/examples/laboratory-contract-example.md`;
- and `docs/design/examples/project-contract-example.md`.

The validation asks whether one implementation-neutral Concord foundation can represent:

1. a standards-based Socratic seminar;
2. a mixed-scoring laboratory investigation;
3. a mixed-scoring collaborative programming or engineering project;
4. a bounded evidence-only follow-up Activity;
5. and a bounded local-criteria-only follow-up Activity

without:

- introducing unnecessary case-specific foundational entities;
- weakening accepted domain invariants;
- duplicating responsibilities owned by Core, ScoreForm, Quillan, Meridian, or external systems;
- forcing every Activity into academic registration or publication;
- treating standards selection or local alignment as a direct standards result;
- conflating routing, registration, native scoring, publication, grading, or reporting;
- obscuring source-producer lineage;
- or concealing missing concepts in undocumented extension data.

The revised validation also tests whether the cases preserve the complete suite-level progression:

```text
Concord Activity and native records
    -> optional Core Academic Work Registration
    -> immutable Concord Academic Result Manifest
    -> immutable Core Publication Record
    -> policy-controlled Meridian consumption
```

This document distinguishes:

- a conceptual-contract defect;
- an example defect;
- a direct-coverage gap;
- a bounded non-use finding;
- a release dependency;
- and deferred implementation work.

## 2. Validation Basis

The comparison applies the precedence and conventions established in the revised representative-examples README and the governing Concord sources, including:

- accepted Concord ADRs, especially ADR 0008 and ADR 0014;
- proposed ADR 0015, **Publish Versioned Concord Academic Result Manifests Through the Core Registry**;
- `docs/concord-conceptual-design-revised.md`;
- `docs/design/cross-case-requirements.md`;
- `docs/design/initial-concord-domain-model.md`;
- `docs/design/pds-core-integration-requirements.md`;
- `docs/design/conceptual-data-contracts.md`;
- released PDS Core 0.5/PDS2 routing contracts;
- later Core academic-work registration and publication-registry architecture used as a conceptual target;
- and Meridian’s documented grading and reporting boundaries.

The representative files remain conceptual design artifacts. They are not:

- production JSON Schemas;
- runtime fixtures;
- released Core registry records;
- released Meridian import records;
- persistence guarantees;
- or evidence that unreleased APIs are available in PDS Core 0.5.

The validation therefore separates two questions:

1. **Can the conceptual architecture represent the required states coherently?**
2. **Can current released runtime packages execute the workflow today?**

This document answers the first question **yes**. It does not answer the second question yes.

When sources disagree, the precedence remains:

1. accepted or superseding ADRs;
2. released Core contracts for currently released Core behavior;
3. accepted conceptual contracts;
4. the revised domain model and integration requirements;
5. proposed ADR 0015 and its coordinated examples as the publication design under review;
6. supporting design rationale.

Completion of issue #12 does not itself accept ADR 0015.

## 3. Status Legend

| Status                     | Meaning                                                                                                  |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| **Exercised**              | A complete representative record path directly demonstrates the requirement.                             |
| **Bounded**                | The example states the boundary precisely without claiming a complete record instance.                   |
| **Addendum**               | A linked, intentionally small example demonstrates the requirement without repeating the principal case. |
| **Deliberately omitted**   | The case does not require the capability and explains the omission.                                      |
| **Structurally supported** | The contracts support the state, but the represented records do not instantiate it.                      |
| **Coverage gap**           | Issue #12 requires direct or explicitly bounded coverage and the example set does not supply it.         |
| **Contract defect**        | A legitimate required state cannot be represented without semantic distortion.                           |
| **Release dependency**     | The conceptual contract is coherent, but compatible runtime APIs are not yet released.                   |

## 4. Executive Determination

### 4.1 Conceptual architecture

```text
PASS
```

The same Concord foundation represents the seminar, laboratory, project, evidence-only archive, and local-only retrospective without a case-specific foundational entity.

The examples preserve the required distinctions among:

- Activity context;
- Sessions;
- Groups and Memberships;
- Roles and Responsibilities;
- definitions, immutable versions, and generated instances;
- physical routing and semantic filing;
- Artifact Authors and Subjects;
- Score targets and scorers;
- evidence, Review, and Moderation;
- Criteria, Scoring Scales, and native Scores;
- Academic Work Registration;
- manifest revision;
- Core publication;
- Meridian policy;
- Grades;
- and reports.

No representative case requires a new Concord foundational record type or a new architectural decision beyond the already proposed ADR 0015 publication design.

### 4.2 Publication architecture

```text
PASS — conceptual model
```

The examples collectively demonstrate:

- explicit Academic Work Registration;
- Activity existence without automatic registration;
- `scoring_orientation` distinct from Core `academic_intent`;
- stable record-set identity;
- immutable revision-addressed manifests;
- exact Criterion and Scoring Scale semantics;
- standard-backed and local Score projection;
- cross-producer evidence lineage;
- Moderation projection;
- standards-only subset projection;
- SHA-256 binding;
- truthful Core Publication Record capabilities;
- publication supersession;
- idempotent replay and contradictory-revision rejection rules;
- derived-catalog nonauthority;
- and Meridian’s policy boundary.

No case treats publication as Grade inclusion or Academic Period membership.

### 4.3 Runtime readiness

```text
NOT YET
```

The examples do not claim that Core 0.5 exposes released Academic Work Registration, Publication Record, withdrawal, or catalog APIs. They also do not claim that Meridian has a released import or grading runtime.

Runtime implementation must wait for compatible released contracts.

### 4.4 Shared notation and terminology

```text
PASS
```

The revised examples consistently use the field-specific typed references and normalized shared value objects defined by the representative-examples README.

### 4.5 Detailed issue coverage

```text
PASS
```

The complete issue #12 validation scope is represented directly, through a bounded addendum, or through an explicit deliberate non-use finding.

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

## 5. Representative Case Summary

| Case                        | Activity form                                | Scoring orientation   | Academic registration                          | Manifest/publication                                              | Distinctive validation                                                                     |
| --------------------------- | -------------------------------------------- | --------------------- | ---------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Seminar                     | Two-session structured discussion            | `standards_based`     | Core revisions 1–2; formative; active → closed | `rs_seminar_results_01` revisions 1–2; two Core publications      | Peer Moderation, non-score supersession, exact Quillan source publication lineage          |
| Laboratory                  | Three-session science investigation          | `mixed`               | Core revisions 1–2; summative; active → closed | `rs_lab_results_01` revision 1; one Core publication              | Standard-backed and local Scores, ScoreForm source publication lineage, routing edge cases |
| Project                     | Five-session programming/engineering project | `mixed`               | Core revisions 1–2; summative; active → closed | `rs_proj_resource_finder_01` revisions 1–2; two Core publications | Native deferred-to-scored revision, publication supersession, technical evidence lineage   |
| Exhibition archive addendum | Evidence archive                             | `evidence_only`       | None by design                                 | None by design                                                    | Valid routed and reviewed evidence without academic-result publication                     |
| Retrospective addendum      | Group retrospective                          | `local_criteria_only` | Core revision 1; formative; closed             | `rs_proj_retrospective_01` revision 1; criterion-only publication | Local Score published without standards capability or Standards Result Projection row      |

## 6. Scoring-Orientation Coverage

| Orientation           | Representative location                     | Validation                                                                                                                 |
| --------------------- | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `standards_based`     | Seminar principal Activity                  | One profile, ordered Focus Standards, standard-backed Criteria, individual Score targets, two manifest revisions.          |
| `mixed`               | Laboratory and project principal Activities | Standard-backed and local Criteria coexist; local Scores remain excluded from the standards-only subset.                   |
| `evidence_only`       | Project exhibition archive addendum         | Routed and reviewed evidence exists with no registration, Criteria, Scales, Scores, manifest, or Core publication.         |
| `local_criteria_only` | Project retrospective addendum              | A formative local Score is registered and published with `criterion_scores` only and an empty Standards Result Projection. |
### Result

```text
PASS
```

The cases demonstrate that Concord scoring orientation controls native Concord configuration, not Core academic intent, Grade eligibility, or Academic Period membership.

## 7. README Cross-Example Matrix

| Requirement                                           | Seminar                               | Laboratory                             | Project                                                          | Collective result       |
| ----------------------------------------------------- | ------------------------------------- | -------------------------------------- | ---------------------------------------------------------------- | ----------------------- |
| Standards-based orientation                           | Exercised                             | Inside mixed Activity                  | Inside mixed Activity                                            | Pass                    |
| Mixed orientation                                     | Deliberately omitted                  | Exercised                              | Exercised                                                        | Pass                    |
| Evidence-only behavior                                | Deliberately omitted                  | Deliberately omitted                   | Addendum; no registration/publication                            | Pass                    |
| Local-only judgment                                   | No local Score                        | Local Score inside mixed manifest      | Local Scores plus local-only addendum                            | Pass                    |
| Individual Score target                               | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Group Score target                                    | Deliberately omitted                  | Exercised                              | Exercised                                                        | Pass                    |
| Multi-Subject evidence                                | Teacher tracker                       | Teacher tracker                        | Teacher tracker and project records                              | Pass                    |
| Teacher-authored evidence                             | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Peer or student-created evidence                      | Peer observations                     | Contribution record                    | Contribution Claims and project Artifacts                        | Pass                    |
| Moderation                                            | Accepted, qualified, insufficient     | Qualified contribution evidence        | Disputed and superseding claim decisions                         | Pass                    |
| External ScoreForm evidence                           | Deliberately omitted                  | Exact result and source publication    | Deliberately omitted                                             | Pass                    |
| External Quillan evidence                             | Exact response and source publication | Deliberately omitted                   | Deliberately omitted                                             | Pass                    |
| External project evidence                             | Deliberately omitted                  | Deliberately omitted                   | Repository, commit, PR, CI, CAD, cloud document                  | Pass                    |
| Membership change                                     | Stable by design                      | Stable by design                       | Historical reassignment                                          | Pass                    |
| Role rotation or reassignment                         | Session rotation                      | Contextual role change                 | Contextual role change                                           | Pass                    |
| Responsibility Assignment                             | Deliberately omitted                  | Exercised                              | Exercised                                                        | Pass                    |
| Packet and Template versioning                        | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| PDS2 route with no student Subject                    | Group maps                            | Group laboratory pages                 | Group project pages and addenda                                  | Pass                    |
| Duplicate, rescan, or correction                      | Rescan and attribution correction     | Rescan, duplicate, misroute correction | Rescan and several native corrections                            | Pass                    |
| Standard-backed Criterion                             | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Local Criterion                                       | Deliberately omitted                  | Exercised                              | Exercised                                                        | Pass                    |
| Non-governing alignment                               | Deliberately omitted                  | Exercised                              | Exercised                                                        | Pass                    |
| Non-score disposition                                 | `insufficient_evidence`               | `absent`                               | `deferred`                                                       | Pass                    |
| Native Score correction or supersession               | Exercised                             | Not needed                             | Exercised                                                        | Pass                    |
| Explicit Academic Work Registration                   | Revisions 1–2                         | Revisions 1–2                          | Primary revisions 1–2; retrospective revision 1                  | Pass                    |
| Activity present without automatic registration       | Not used                              | Not used                               | Evidence-only archive                                            | Pass                    |
| Scoring orientation distinct from academic intent     | Standards-based vs formative          | Mixed vs summative                     | Mixed vs summative; local-only vs formative                      | Pass                    |
| Concord Academic Result Manifest                      | Revisions 1–2                         | Revision 1                             | Primary revisions 1–2; retrospective revision 1                  | Pass                    |
| Stable record-set identity                            | Stable across two revisions           | Stable one-revision series             | Stable across primary revisions; separate retrospective series   | Pass                    |
| Manifest revision                                     | Exercised                             | One revision only                      | Exercised                                                        | Pass                    |
| Exact Criterion projection                            | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Exact Scoring Scale projection                        | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Standard-backed Score projection                      | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Local Score in broader manifest                       | Not applicable                        | Exercised                              | Exercised                                                        | Pass                    |
| Local Score excluded from Standards Result Projection | Not applicable                        | Exercised                              | Exercised, including empty local-only subset                     | Pass                    |
| Manifest Evidence-Lineage Projection                  | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Exact source Publication Record lineage               | Quillan publication                   | ScoreForm publication                  | No PDS result publication claimed for technical evidence         | Pass                    |
| Manifest Moderation Projection                        | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Standards Result Projection                           | Exercised                             | Exercised                              | Exercised; empty for local-only addendum                         | Pass                    |
| Revision-addressed manifest path                      | Exercised                             | Exercised                              | Exercised                                                        | Pass                    |
| Mechanical SHA-256 binding                            | Two digests verified                  | One digest verified                    | Three digests verified                                           | Pass                    |
| Core Publication Record                               | Two                                   | One                                    | Two primary plus one retrospective                               | Pass                    |
| Truthful capabilities                                 | Three applicable capabilities         | Three applicable capabilities          | Primary three; retrospective criterion-only                      | Pass                    |
| Idempotent publication replay                         | Explicit rule                         | Explicit rule                          | Explicit rule                                                    | Pass                    |
| Publication supersession                              | Exercised                             | Not needed                             | Exercised                                                        | Pass                    |
| Publication withdrawal                                | Not represented                       | Not represented                        | Bounded explicitly; no withdrawal record claimed                 | Pass as bounded non-use |
| Derived Core catalog treated as nonauthoritative      | Explicit                              | Explicit                               | Explicit                                                         | Pass                    |
| Meridian cross-producer overlap boundary              | Quillan lineage                       | ScoreForm lineage                      | Technical evidence retained as lineage, not duplicate PDS result | Pass                    |
| Meridian override distinct from Concord revision      | Explicit                              | Explicit                               | Explicit                                                         | Pass                    |
| No Academic Period ID in producer manifest            | Confirmed                             | Confirmed                              | Confirmed                                                        | Pass                    |
| Publication does not imply Grade inclusion            | Explicit                              | Explicit                               | Explicit                                                         | Pass                    |
The withdrawal row is intentionally not labeled **Exercised**. The project case establishes the boundary and preserves the distinction between publication supersession and a possible later Core withdrawal, but it does not contain an invented withdrawal identifier or a complete Core withdrawal record.

## 8. Shared Notation and Typed-Reference Validation

| Check                    | Seminar                                     | Laboratory              | Project                 | Result                |
| ------------------------ | ------------------------------------------- | ----------------------- | ----------------------- | --------------------- |
| Fenced YAML              | 36 blocks                                   | 49 blocks               | 50 blocks               | 135 total; all parsed |
| Exact manifest JSON      | 2 blocks                                    | 1 block                 | 3 blocks                | 6 total; all parsed   |
| Offset-aware timestamps  | 179                                         | 212                     | 402                     | 793 total; all parsed |
| Participant References   | Contract-native                             | Contract-native         | Contract-native         | Pass                  |
| Actor References         | `actor_kind` / `actor_id` / `owning_system` | Same                    | Same                    | Pass                  |
| Subject References       | Contract-native                             | Contract-native         | Contract-native         | Pass                  |
| Score-Target References  | Provisional shared notation                 | Same                    | Same                    | Pass                  |
| Evidence References      | Source-owner compatible                     | Source-owner compatible | Source-owner compatible | Pass                  |
| Evidence Locator fields  | Supported fields only                       | Supported fields only   | Supported fields only   | Pass                  |
| Non-score value omission | Confirmed                                   | Confirmed               | Confirmed               | Pass                  |
The examples no longer use one generic `owning_system` / `record_kind` / `record_id` object as a substitute for every semantic relationship.

Display labels are excluded from reference types that do not permit them. Actor display snapshots remain available where the Actor Reference contract permits them.

## 9. Activity and Collaboration Validation

| Requirement                                   | Seminar                | Laboratory            | Project                            | Result |
| --------------------------------------------- | ---------------------- | --------------------- | ---------------------------------- | ------ |
| Every Activity belongs to one Core class      | Yes                    | Yes                   | Yes, including addenda             | Pass   |
| Every Activity has at least one Session       | Two                    | Three                 | Five plus one per addendum         | Pass   |
| Groups are Activity-specific                  | Yes                    | Yes                   | Yes                                | Pass   |
| Membership is contextual                      | Two-session context    | Activity context      | Session- and stage-bounded         | Pass   |
| Membership change preserves history           | Deliberately absent    | Deliberately absent   | Explicit reassignment              | Pass   |
| Roles are contextual functions                | Rotating seminar roles | Laboratory roles      | Project roles                      | Pass   |
| Responsibilities remain separate from Roles   | Deliberately omitted   | Explicit              | Explicit                           | Pass   |
| Responsibility reassignment preserves history | Not applicable         | Probe reassignment    | Project reassignment               | Pass   |
| Assignment does not prove performance         | Explicit invariant     | Explicit invariant    | Explicit invariant                 | Pass   |
| Contribution evidence remains separate        | Peer evidence          | Contribution Artifact | Contribution Claims and Moderation | Pass   |
### Finding

The collaboration model scales from a short discussion to a multi-stage project without forcing Work Items, Dependencies, child Groups, or contribution claims into simpler Activities.

## 10. Template, Packet, Artifact, and Page Validation

| Requirement                                                     | Seminar              | Laboratory | Project              | Result |
| --------------------------------------------------------------- | -------------------- | ---------- | -------------------- | ------ |
| Template Definition and immutable Template Version are distinct | Yes                  | Yes        | Yes                  | Pass   |
| Packet Definition and immutable Packet Version are distinct     | Yes                  | Yes        | Yes                  | Pass   |
| Packet Version preserves ordered components                     | Yes                  | Yes        | Yes                  | Pass   |
| Packet Instance references exact Packet Version                 | Yes                  | Yes        | Yes                  | Pass   |
| Artifact Instance references exact Template Version             | Yes                  | Yes        | Yes                  | Pass   |
| Artifact Instance and scan identity remain separate             | Yes                  | Yes        | Yes                  | Pass   |
| Returned page exists before route registration                  | Yes                  | Yes        | Yes                  | Pass   |
| Route-required page has durable PDS2 identity                   | Yes                  | Yes        | Yes                  | Pass   |
| Non-returned instructional page omits route and fallback        | Deliberately omitted | Exercised  | Deliberately omitted | Pass   |
### Finding

Reusable lineages, immutable historical revisions, generated instances, and physical pages remain distinct across all cases.

## 11. PDS2 Routing and Scan-Intake Validation

| Requirement                                           | Seminar             | Laboratory                  | Project             | Result |
| ----------------------------------------------------- | ------------------- | --------------------------- | ------------------- | ------ |
| `module_id = concord`; `work_id = activity_id`        | All relevant routes | All relevant routes         | All relevant routes | Pass   |
| Route Registration targets an existing Artifact Page  | Yes                 | Yes                         | Yes                 | Pass   |
| QR contains route identity rather than semantic graph | Yes                 | Yes                         | Yes                 | Pass   |
| Core retains canonical source scan                    | Yes                 | Yes                         | Yes                 | Pass   |
| Concord creates Scan Reference after routing          | Yes                 | Yes                         | Yes                 | Pass   |
| Mixed-module batch                                    | Not used            | Concord and ScoreForm pages | Not used            | Pass   |
| Routing while attribution unresolved                  | Peer form           | Not needed                  | Not needed          | Pass   |
| Rescan preserves earlier source                       | Yes                 | Yes                         | Yes                 | Pass   |
| Actual duplicate separately retained and nonpreferred | Not used            | Exercised                   | Not used            | Pass   |
| Misroute correction preserves retained source         | Not used            | Exercised                   | Not used            | Pass   |
| Non-returned page has no Route Registration           | Not used            | Exercised                   | Not used            | Pass   |
### Finding

Routing remains independent of academic registration and publication. A routed Artifact Page does not create a Core Academic Work Registration or Core Publication Record.

## 12. Author, Subject, Target, and Scorer Validation

| Requirement                                         | Seminar                          | Laboratory                                 | Project                                  | Result |
| --------------------------------------------------- | -------------------------------- | ------------------------------------------ | ---------------------------------------- | ------ |
| Student Author differs from student Subject         | Peer observer / observed student | Student evidence concerning Group or peers | Individual and Group project evidence    | Pass   |
| Several Authors may be associated with one Artifact | Yes                              | Yes                                        | Yes                                      | Pass   |
| Recorder may represent a Group                      | Yes                              | Yes                                        | Yes                                      | Pass   |
| Collective Group authorship is explicit             | Yes                              | Yes                                        | Yes                                      | Pass   |
| Group Artifact may have no student Subject          | Yes                              | Yes                                        | Yes                                      | Pass   |
| Teacher Artifact may concern several Subjects       | Yes                              | Yes                                        | Yes                                      | Pass   |
| Unknown Author attribution can be corrected         | Exercised                        | Not required                               | Disputes remain distinct from authorship | Pass   |
| Artifact Subject differs from Score target          | Explicit                         | Explicit                                   | Explicit                                 | Pass   |
| Score target differs from scorer                    | Explicit                         | Explicit                                   | Explicit                                 | Pass   |
| External file/account ownership is not authorship   | Explicit rejection               | Explicit rejection                         | Explicit rejection                       | Pass   |

## 13. Review, Moderation, Correction, and Native Supersession Validation

| Requirement                                                      | Seminar            | Laboratory            | Project                          | Result |
| ---------------------------------------------------------------- | ------------------ | --------------------- | -------------------------------- | ------ |
| Normal Artifact Review                                           | Yes                | Yes                   | Yes                              | Pass   |
| Review requiring correction                                      | Author and Subject | Rescan and filing     | Claim, scan, and project history | Pass   |
| Moderation before consequential use                              | Peer evidence      | Contribution evidence | Contribution Claims              | Pass   |
| Accepted-with-qualification evidence                             | Yes                | Yes                   | Yes                              | Pass   |
| Insufficient, disputed, or rejected evidence                     | Yes                | Qualified limits      | Yes                              | Pass   |
| Rejected or insufficient evidence is not negative performance    | Yes                | Yes                   | Yes                              | Pass   |
| Native Score revision preserves earlier judgment                 | Yes                | Not needed            | Yes                              | Pass   |
| Native correction remains distinct from publication supersession | Yes                | Not applicable        | Yes                              | Pass   |

## 14. Criteria, Scales, and Native Scoring Validation

| Requirement                                                        | Seminar         | Laboratory      | Project          | Result |
| ------------------------------------------------------------------ | --------------- | --------------- | ---------------- | ------ |
| Standards-based or mixed Activity has one profile                  | Yes             | Yes             | Yes              | Pass   |
| Focus Standards are ordered and nonempty                           | Yes             | Yes             | Yes              | Pass   |
| Standard-backed Criterion has one governing standard               | Yes             | Yes             | Yes              | Pass   |
| Governing standard belongs to Focus Standards                      | Yes             | Yes             | Yes              | Pass   |
| Local Criterion has no governing standard                          | Not used        | Yes             | Yes              | Pass   |
| Local alignment remains non-governing                              | Not used        | Yes             | Yes              | Pass   |
| One Score evaluates one Criterion for one target                   | Yes             | Yes             | Yes              | Pass   |
| Individual standard-backed Score                                   | Yes             | Yes             | Yes              | Pass   |
| Group standard-backed Score                                        | Not used        | Yes             | Yes              | Pass   |
| Local Score                                                        | Not used        | Yes             | Yes              | Pass   |
| One source supports several Scores                                 | Teacher tracker | Teacher records | Project evidence | Pass   |
| One Score uses several sources                                     | Yes             | Yes             | Yes              | Pass   |
| Group evidence supports individual Score only by explicit judgment | Yes             | Yes             | Yes              | Pass   |
| Group Score does not create member Scores                          | Not applicable  | Explicit        | Explicit         | Pass   |

## 15. Non-Score and Exceptional-State Validation

| State or rule                                             | Representative location   | Result |
| --------------------------------------------------------- | ------------------------- | ------ |
| `insufficient_evidence`                                   | Seminar                   | Pass   |
| `absent`                                                  | Laboratory                | Pass   |
| `deferred`                                                | Project                   | Pass   |
| Non-score projection omits `value`                        | All three principal cases | Pass   |
| Non-score never becomes zero or lowest scale level        | All three principal cases | Pass   |
| Later Score may supersede non-score disposition           | Seminar and project       | Pass   |
| Equipment failure is context, not performance             | Laboratory                | Pass   |
| External-system outage is context, not performance        | Project                   | Pass   |
| Session interruption does not determine Score disposition | Laboratory and project    | Pass   |

## 16. Core Academic Work Registration Validation

| Case                  | Work ID                       | Registration revision | Academic intent | Lifecycle |
| --------------------- | ----------------------------- | --------------------- | --------------- | --------- |
| Seminar               | `act_seminar_01`              | 1                     | formative       | active    |
| Seminar               | `act_seminar_01`              | 2                     | formative       | closed    |
| Laboratory            | `act_lab_catalase_01`         | 1                     | summative       | active    |
| Laboratory            | `act_lab_catalase_01`         | 2                     | summative       | closed    |
| Project primary       | `act_proj_resource_finder_01` | 1                     | summative       | active    |
| Project primary       | `act_proj_resource_finder_01` | 2                     | summative       | closed    |
| Project retrospective | `act_proj_retrospective_01`   | 1                     | formative       | closed    |
The project exhibition archive deliberately has no Academic Work Registration.

The examples validate that:

- Activity existence does not create registration;
- PDS2 routing does not create registration;
- Focus Standard selection does not create registration;
- native Score existence does not create registration;
- `standards_based`, `mixed`, and `local_criteria_only` are not Core academic intents;
- `formative` and `summative` are not Concord scoring orientations;
- and every published `academic_result_set` references the exact Academic Work Registration revision that was current when that Publication Record was created.

All Activity, registration, manifest, and publication records agree on the exact module-qualified work reference.

## 17. Concord Academic Result Manifest Validation

| Case                  | Record-set ID                | Revision | Scores | Standards rows | Criteria | Scales | Evidence links | Moderation rows |
| --------------------- | ---------------------------- | -------- | ------ | -------------- | -------- | ------ | -------------- | --------------- |
| Seminar               | `rs_seminar_results_01`      | 1        | 4      | 4              | 3        | 1      | 6              | 1               |
| Seminar               | `rs_seminar_results_01`      | 2        | 5      | 5              | 3        | 1      | 9              | 2               |
| Laboratory            | `rs_lab_results_01`          | 1        | 4      | 3              | 3        | 2      | 11             | 1               |
| Project               | `rs_proj_resource_finder_01` | 1        | 6      | 4              | 3        | 2      | 16             | 4               |
| Project               | `rs_proj_resource_finder_01` | 2        | 7      | 5              | 3        | 2      | 22             | 4               |
| Project retrospective | `rs_proj_retrospective_01`   | 1        | 1      | 0              | 1        | 1      | 1              | 0               |
### Findings

- Seminar revisions 1 and 2 retain one stable record-set identity.
- Project primary revisions 1 and 2 retain one stable record-set identity.
- Laboratory and the local retrospective each demonstrate a valid one-revision series.
- Every included Score has a complete Criterion projection and exact Scoring Scale projection.
- Local laboratory and project Scores appear in the broader Score projection.
- Local Scores never appear in the direct Standards Result Projection.
- The local-only retrospective has an empty Standards Result Projection rather than a fabricated standards rating.
- Non-score dispositions remain present and valueless.
- Native superseded states remain reproducible in later manifest revisions rather than being removed from history.

## 18. Manifest Identity, Path, and Digest Validation

| Case                  | Record-set ID                | Revision | Verified SHA-256                                                   |
| --------------------- | ---------------------------- | -------- | ------------------------------------------------------------------ |
| Seminar               | `rs_seminar_results_01`      | 1        | `a6147ea67b6dd3582a7087bc930a490931082ba3a48ec49d53eabf02ef8dde28` |
| Seminar               | `rs_seminar_results_01`      | 2        | `8855b1162a9ea2c913a0c78a2c8e7c3db4d29f853c81eaab0b69aa0494624879` |
| Laboratory            | `rs_lab_results_01`          | 1        | `c5e11918d47585acf52bdd82604304470434723a4ba776e6e5f4dfd7d58e3a57` |
| Project primary       | `rs_proj_resource_finder_01` | 1        | `df5c502efd3649e776dae771905be2e4d4330099c270fdb02cb2c47e4c8ec412` |
| Project primary       | `rs_proj_resource_finder_01` | 2        | `dc64636d1f87ad8ec22a10df507d08403577e827997c75d7c20ab0aa6801f250` |
| Project retrospective | `rs_proj_retrospective_01`   | 1        | `9d54f078056388d4a42c50d185df9e9ffee5e2b0aa24b22c48c4435857b37198` |
All six manifest blocks were parsed as exact JSON and hashed from their represented UTF-8 bytes, including the declared final line-feed byte.

Every published path follows:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
  exports/manifests/<record_set_id>/<record_set_revision>.json
```

Validation confirmed:

- path containment under the exact Activity work root;
- positive revision numbers;
- stable record-set identity within a series;
- distinct bytes and digests for distinct revisions;
- lowercase 64-character SHA-256 syntax;
- and exact digest agreement between manifest bytes and the matching Core Publication Record.

No case uses mutable `latest.json` as the canonical publication object.

## 19. Core Publication Record Validation

| Case                  | Publication ID                         | Record-set ID                | Revision | Capabilities                    | Registration revision | Supersedes                             |
| --------------------- | -------------------------------------- | ---------------------------- | -------- | ------------------------------- | --------------------- | -------------------------------------- |
| Seminar               | `pub_concord_seminar_results_001`      | `rs_seminar_results_01`      | 1        | criterion, standards, moderated | 1                     | —                                      |
| Seminar               | `pub_concord_seminar_results_002`      | `rs_seminar_results_01`      | 2        | criterion, standards, moderated | 2                     | `pub_concord_seminar_results_001`      |
| Laboratory            | `pub_concord_lab_results_001`          | `rs_lab_results_01`          | 1        | criterion, standards, moderated | 2                     | —                                      |
| Project primary       | `pub_concord_proj_resource_finder_001` | `rs_proj_resource_finder_01` | 1        | criterion, standards, moderated | 2                     | —                                      |
| Project primary       | `pub_concord_proj_resource_finder_002` | `rs_proj_resource_finder_01` | 2        | criterion, standards, moderated | 2                     | `pub_concord_proj_resource_finder_001` |
| Project retrospective | `pub_concord_proj_retrospective_001`   | `rs_proj_retrospective_01`   | 1        | criterion only                  | 1                     | —                                      |
Every Publication Record agrees with its manifest on:

- exact `ModuleWorkRef`;
- record-set identity;
- record-set revision;
- manifest contract version;
- manifest path;
- digest algorithm;
- and digest.

Capabilities are truthful:

- principal seminar, laboratory, and project publications declare `criterion_scores`, `standards_ratings`, and `moderated_scores`;
- the local-only retrospective declares only `criterion_scores`;
- no evidence-only publication exists;
- and non-governing alignment does not justify `standards_ratings`.

## 20. Publication Replay, Supersession, Withdrawal, and Catalog Validation

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

### 20.2 Contradictory revision reuse

Each publication series rejects reuse of one logical `record_set_revision` with different:

- bytes;
- path;
- digest;
- or manifest contract version.

Such reuse is an integrity conflict, not an update.

### 20.3 Native Score supersession versus publication supersession

The seminar and project cases demonstrate both histories.

```text
native Score revision
    != manifest revision
    != Core publication supersession
```

A revised native Score requires a new manifest revision before a new publication can expose the new state. Neither native supersession nor publication supersession erases earlier records.

### 20.4 Publication withdrawal

```text
BOUNDED — NOT INSTANTIATED
```

No final case includes a complete Core publication-withdrawal record.

The project case explicitly establishes that:

- publication supersession is not withdrawal;
- a later withdrawal would be a separate Core-owned immutable record;
- the native manifest and Publication Record would remain preserved;
- and withdrawal would not rewrite the native Concord Score.

Issue #13 concludes that an additional Concord-specific withdrawal fixture is not required before serialized Concord contracts proceed because Publication Withdrawal is Core-owned and already governed by an implemented Core contract.

The Concord contracts and examples must nevertheless preserve the reviewed rule that withdrawing a series head does not reactivate its predecessor.

### 20.5 Derived Core catalog

All cases treat the Core registry catalog as:

- derived;
- rebuildable from immutable registry records;
- useful for discovery;
- and nonauthoritative.

Concord does not write authoritative catalog rows directly, and catalog loss does not invalidate the underlying registration, manifest, Publication Record, or withdrawal history.

## 21. Cross-Producer and External Evidence-Lineage Validation

| Case                  | Source evidence                         | Known source publication             | Validation                                                                                       |
| --------------------- | --------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Seminar               | Quillan response                        | `pub_quillan_seminar_reflection_001` | Exact module record and source publication retained in evidence lineage.                         |
| Laboratory            | ScoreForm result                        | `pub_scoreform_lab_check_001`        | Exact result and source publication retained; no automatic Concord conversion.                   |
| Project primary       | GitHub, CI, CAD, cloud-document records | No PDS result publication claimed    | Underlying external records remain evidence lineage, not duplicate academic-result publications. |
| Project retrospective | Concord Artifact                        | Not external                         | Native Concord evidence retained.                                                                |
### Finding

The manifests expose underlying source-record lineage rather than only Concord-local `score_evidence_link_id` values.

This permits Meridian to detect that:

```text
Quillan or ScoreForm publication
    -> source result used as Concord evidence
    -> Concord publication
```

and to avoid double counting the source publication and the derived Concord judgment as independent evidence.

External technical records in the project case do not become PDS academic-result publications merely because Concord uses them as evidence.

## 22. Meridian Consumption Boundary

| Concern                        | Owner                 | Cross-example finding                                                           |
| ------------------------------ | --------------------- | ------------------------------------------------------------------------------- |
| Publication discovery          | Core registry records | Concord does not decide which discovered publication Meridian imports.          |
| Publication eligibility        | Meridian              | Publication is not Grade authorization.                                         |
| Evidence selection and overlap | Meridian              | Source-publication lineage supports duplicate and derivation policy.            |
| Grade-item membership          | Meridian              | No producer record makes itself a Grade item.                                   |
| Academic Period membership     | Meridian              | No authoritative period ID appears in native Scores or manifests.               |
| Scale mapping                  | Meridian              | Exact producer scale meaning is preserved; mapping is downstream policy.        |
| Standards proficiency          | Meridian              | A Concord standards Score is contextual evidence, not longitudinal proficiency. |
| Weighting and aggregation      | Meridian              | Concord does not encode course policy.                                          |
| Derived override               | Meridian              | An override does not mutate Concord Score, manifest, or Core publication.       |
| Grade and report snapshots     | Meridian              | Snapshots preserve selected publication and policy versions.                    |
Every principal publication can be discovered by Meridian, but discovery alone does not establish:

- Grade eligibility;
- Grade-item membership;
- Academic Period membership;
- scale equivalence;
- evidence selection;
- proficiency;
- Grade;
- or report inclusion.

A Meridian override changes only the derived Meridian result. It does not create:

- a native Concord Score revision;
- a new Concord manifest revision;
- a Core Publication Record;
- or a Core publication withdrawal.

## 23. External Ownership Validation

| Authority                | Representative case | Finding                                                                                                                |
| ------------------------ | ------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Quillan                  | Seminar             | Source response and publication remain Quillan/Core-governed; Concord owns only its relationship and derived judgment. |
| ScoreForm                | Laboratory          | Source result and publication remain ScoreForm/Core-governed.                                                          |
| GitHub or source control | Project             | Repository, commit, and pull-request history remain externally authoritative.                                          |
| CI provider              | Project             | Test-run records remain external.                                                                                      |
| CAD system               | Project             | Design records remain external.                                                                                        |
| Cloud-document provider  | Project             | Document history remains external.                                                                                     |
No external relationship requires copying the complete external record into Concord ownership or inferring Artifact authorship from external account or file ownership.

## 24. Optional Contract Coverage

| Optional contract         | Seminar | Laboratory                          | Project                            | Result |
| ------------------------- | ------- | ----------------------------------- | ---------------------------------- | ------ |
| Responsibility Assignment | Omitted | Exercised                           | Exercised                          | Pass   |
| Child Group               | Omitted | Omitted                             | Exercised                          | Pass   |
| Activity Marker           | Omitted | Omitted                             | Exercised                          | Pass   |
| Work Item                 | Omitted | Omitted                             | Exercised                          | Pass   |
| Work-Item Dependency      | Omitted | Omitted                             | Exercised                          | Pass   |
| Activity Event            | Omitted | Equipment failure                   | Decision, outage, testing, release | Pass   |
| Contribution Claim        | Omitted | Moderated Artifact evidence instead | Explicit Claims                    | Pass   |
| Attachment                | Omitted | Omitted                             | Exercised                          | Pass   |
| External Reference        | Quillan | ScoreForm                           | Technical systems                  | Pass   |
Optional structures remain optional. The seminar and laboratory are not forced into a project-management ontology merely to match the project example.

## 25. Terminology and Semantic Consistency

The following meanings remain stable across all cases.

### Activity

One Concord-owned collaborative undertaking associated with one Core class.

Activity is not:

- a Core assignment identity;
- a Core Academic Work Registration;
- a manifest;
- or a Grade item.

### Scoring orientation

Concord-owned declaration of whether native judgments are:

- evidence-only;
- standards-based;
- mixed;
- or local-criteria-only.

It is not Core academic intent.

### Academic intent

Core-owned classification such as formative or summative for registered work.

It does not determine which native Scores Meridian grades.

### Evidence

A source used or considered during judgment.

Evidence is not Review, Moderation, Score, publication, Grade, or report.

### Score

One native teacher-approved Criterion judgment for one target and one exact Scoring Scale revision.

Score is not manifest, publication, mastery, or Grade.

### Concord Academic Result Manifest

One immutable producer-owned projection of a record-set revision.

It is not the Core registry record and is not a Meridian calculation.

### Core Publication Record

One immutable Core-owned discovery and integrity record for one exact manifest revision.

It is not the native Score, Grade authorization, or Academic Period assignment.

### Meridian result

A policy-derived result produced from explicitly selected publications and policy versions.

It does not replace or rewrite producer records.

### Result

```text
PASS
```

No material semantic drift was found after the publication revisions.

## 26. Cross-Case Invariants

1. Core owns class, roster, PDS2 routing, source retention, standards identity, Academic Work Registration, Publication Records, withdrawal records, and the rebuildable registry catalog.
2. Concord owns Activities, native collaboration records, Artifacts, Review, Moderation, Criteria, Scales, Scores, and exact manifest bytes.
3. Meridian owns publication eligibility, evidence selection, overlap policy, Grade-item membership, Academic Period membership, scale mapping, proficiency, Grades, overrides, and reports.
4. External systems retain ownership of their native records.
5. `activity_id` serves as Concord's `work_id` without becoming a Core assignment ID.
6. Routing, registration, publication, and grading remain separate domains.
7. An Activity may exist and route evidence without academic registration or publication.
8. Scoring orientation does not infer academic intent.
9. A QR identifies one physical route rather than semantic classroom meaning.
10. Author, Subject, Score target, scorer, standard, and publisher remain distinct.
11. Membership, Role, Responsibility, Work Item, Claim, and performance remain distinct.
12. Definitions remain separate from immutable versions and generated instances.
13. Review, Moderation, Scoring, publication, Grading, and Reporting remain separate.
14. Standards selection and alignment do not create a standards result.
15. A standard-backed Score has one governing standard.
16. A local Score may be published but remains local.
17. The Standards Result Projection excludes local Scores.
18. A Group Score does not create individual Scores.
19. Group or multi-Subject evidence does not create an individual Score automatically.
20. Missing or unavailable evidence is not a low Score.
21. Exceptional circumstances do not determine performance automatically.
22. Native records are superseded rather than silently rewritten.
23. Manifest revisions are immutable and revision-addressed.
24. Core publications bind exact manifest bytes through SHA-256.
25. Native Score supersession and publication supersession are separate histories.
26. Publication withdrawal is separate from supersession and native correction.
27. The derived catalog is nonauthoritative.
28. Known source-publication lineage remains available for overlap policy.
29. Publication does not imply Grade inclusion.
30. No producer manifest owns Academic Period, proficiency, Grade, override, or report state.
### Result

```text
PASS
```

## 27. Mechanical Audit Results

| Audit                          | Evidence                                                                                | Result  |
| ------------------------------ | --------------------------------------------------------------------------------------- | ------- |
| Markdown code fences           | Balanced in all three final case files                                                  | Pass    |
| YAML parsing                   | 135 fenced YAML blocks parsed                                                           | Pass    |
| Manifest JSON parsing          | 6 exact manifest JSON blocks parsed                                                     | Pass    |
| Timestamp syntax               | 793 offset-aware timestamps parsed                                                      | Pass    |
| Typed reference shapes         | Participant, Actor, Subject, Score-Target, and Evidence shapes checked                  | Pass    |
| Evidence Locator fields        | No unsupported fields found                                                             | Pass    |
| Score Evidence Link chronology | No link predates its parent Score                                                       | Pass    |
| Manifest series identity       | Stable record-set IDs and coherent revisions                                            | Pass    |
| Manifest semantic projection   | Local/standard classifications and non-score value omission checked                     | Pass    |
| Manifest prohibited state      | No authoritative Academic Period, Grade, proficiency, or Meridian override fields found | Pass    |
| Manifest digest                | All 6 SHA-256 values recomputed from exact represented bytes                            | Pass    |
| Publication match              | All 6 Publication Records match work, record set, revision, contract, path, and digest  | Pass    |
| Publication capabilities       | Compatible with represented projections                                                 | Pass    |
| Source publication lineage     | Quillan and ScoreForm references verified where claimed                                 | Pass    |
| Withdrawal record              | No record present; bounded treatment documented                                         | Bounded |
The automated cross-file audit complements, rather than replaces, each case’s own record-inventory and semantic validation.

Combined final case size:

```text
23,080 Markdown lines
135 YAML blocks
6 exact manifest JSON blocks
793 offset-aware timestamps
7 Academic Work Registration records
6 Core Publication Records
0 Core publication-withdrawal records
```

A prose PASS would not override a digest, parsing, chronology, reference, or projection failure. No such failure remained in the final files.

## 28. Cross-Case Tensions and Deferred Questions

The examples expose implementation and governance questions. None currently proves that the Concord conceptual foundation is defective.

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

### 28.4 Released Core registry APIs

Current PDS Core 0.5 documentation advertises routing-era support. The registration and publication examples target later architecture.

Implementation must not pin to invented or unreleased APIs.

### 28.5 Meridian import and policy contracts

Meridian is documented conceptually but has no represented runtime import, Grade-item, Academic Period, calculation, override, or report records in these examples.

That omission is deliberate because those are Meridian-owned contracts.

### 28.6 Manifest schema formalization

The exact examples establish semantics and digest mechanics but are not a production JSON Schema.

A later schema must preserve:

- deterministic serialization expectations;
- projection completeness;
- privacy boundaries;
- revision identity;
- and compatibility policy.

### 28.7 External adapter contracts

Exact public record kinds and contract versions for Quillan, ScoreForm, GitHub, CI, CAD, and cloud-document adapters remain implementation work.

### 28.8 Catalog repair interface

The derived-catalog principle is settled, but the final Core command or service interface for rebuild and repair remains outside this issue.

### Classification

```text
DEFERRED OR RELEASE-DEPENDENT — NOT A CONCORD CONTRACT DEFECT
```

## 29. Direct-Coverage Resolution

| Requirement                                     | Location                      | Classification            | Contract change required |
| ----------------------------------------------- | ----------------------------- | ------------------------- | ------------------------ |
| Non-returned instructional page without routing | Laboratory edge addendum      | Exercised                 | No                       |
| Explicit duplicate scan                         | Laboratory edge addendum      | Exercised                 | No                       |
| Misroute correction preserving source           | Laboratory edge addendum      | Exercised                 | No                       |
| Activity without automatic registration         | Project evidence-only archive | Exercised                 | No                       |
| Local-only academic-result publication          | Project retrospective         | Exercised                 | No                       |
| Native Score supersession                       | Seminar and project           | Exercised                 | No                       |
| Manifest revision                               | Seminar and project           | Exercised                 | No                       |
| Publication supersession                        | Seminar and project           | Exercised                 | No                       |
| Exact Quillan source publication lineage        | Seminar                       | Exercised                 | No                       |
| Exact ScoreForm source publication lineage      | Laboratory                    | Exercised                 | No                       |
| Publication withdrawal                          | Project boundary statement    | Bounded, not instantiated | Issue #13 decision       |
All previously identified routing and intake gaps are resolved.

The only non-instantiated publication lifecycle state is withdrawal, and the documents do not falsely claim otherwise.

## 30. Contract and ADR Changes Required

### Concord conceptual contracts

```text
None.
```

The examples do not reveal a legitimate classroom state that requires a new Concord foundational record or a change to current native scoring semantics.

### New ADR

```text
None.
```

No additional ADR is required by the examples.

### ADR 0015 status

```text
DECISION STILL REQUIRED
```

Issue #12 validates the proposed design through representative examples. It does not itself change ADR 0015 from Proposed to Accepted.

Issue #13 should explicitly accept, revise, or reject ADR 0015.

### Released Core and Meridian contracts

```text
RELEASE DEPENDENCY
```

Runtime publication work requires released compatible Core registry APIs and Meridian consumption contracts.

## 31. Representative-Examples README Changes Required

```text
None.
```

The revised README already defines:

- registration and publication notation;
- manifest projections;
- digest mechanics;
- exact source-publication lineage;
- publication lifecycle distinctions;
- derived-catalog nonauthority;
- Meridian boundaries;
- and the expanded 40-check mechanical audit.

The final cases conform to those conventions.

A future decision to require a concrete withdrawal fixture would require one additional example revision, not necessarily a README architecture change.

## 32. Completion-Standard Assessment

| Completion requirement                                             | Status          | Finding                                                          |
| ------------------------------------------------------------------ | --------------- | ---------------------------------------------------------------- |
| Coherent seminar, laboratory, and project record sets              | Pass            | All principal cases remain internally coherent.                  |
| Shared notation and typed references                               | Pass            | 135 YAML blocks parse under normalized conventions.              |
| Four scoring orientations                                          | Pass            | Principal cases plus bounded project addenda.                    |
| Routing separate from semantic context                             | Pass            | All PDS2 routes remain page-route locators.                      |
| Routing separate from registration and publication                 | Pass            | Evidence-only archive demonstrates non-inference.                |
| Standards alignment separate from direct result                    | Pass            | Local alignment never enters standards subset.                   |
| Group and individual judgments separate                            | Pass            | Targets remain explicit.                                         |
| Review, Moderation, Score, publication, Grade, report separate     | Pass            | Ownership boundaries preserved.                                  |
| Native correction and supersession preserve history                | Pass            | Seminar and project revisions.                                   |
| Explicit Academic Work Registration                                | Pass            | Seven Core registration records.                                 |
| Scoring orientation distinct from academic intent                  | Pass            | Formative/summative combinations demonstrate independence.       |
| Complete manifests mechanically validated                          | Pass            | Six exact JSON objects and digests.                              |
| Stable series and manifest revision                                | Pass            | Seminar and primary project.                                     |
| Complete Criterion and Scale semantics                             | Pass            | Every included Score is reproducible.                            |
| Local Score broader publication without standards reinterpretation | Pass            | Laboratory, project, retrospective.                              |
| Non-score dispositions remain valueless                            | Pass            | Insufficient, absent, deferred.                                  |
| Cross-producer source-publication lineage                          | Pass            | Quillan and ScoreForm.                                           |
| Moderation projection sufficient                                   | Pass            | Consequential uses preserve applicable decisions.                |
| Revision-addressed path and SHA-256 binding                        | Pass            | All six publications.                                            |
| Idempotent replay and contradictory-revision rules                 | Pass            | Explicit in each publication case.                               |
| Native and publication supersession separate                       | Pass            | Seminar and project.                                             |
| Withdrawal treatment                                               | Pass as bounded | No withdrawal record claimed; issue #13 may strengthen coverage. |
| Derived Core catalog nonauthoritative                              | Pass            | All cases state rebuildability.                                  |
| Meridian ownership boundary                                        | Pass            | No producer-owned grading or period state.                       |
| No producer Academic Period, Grade, proficiency, or override state | Pass            | Mechanical key audit.                                            |
| External ownership preserved                                       | Pass            | Sibling and technical systems remain authoritative.              |
| Optional structures remain optional                                | Pass            | Simpler cases remain simple.                                     |
| Release-status distinctions accurate                               | Pass            | Conceptual target is not presented as Core 0.5 runtime.          |
| No architecture-breaking workaround                                | Pass            | Rejected shortcuts documented.                                   |
The representative README completion standard is satisfied for conceptual validation.

This does not:

- accept ADR 0015;
- release a production manifest schema;
- release Core registry APIs;
- or approve Meridian implementation.

## 33. Issue #12 Acceptance Assessment

### Passed

- [x] Complete seminar, laboratory, and project conceptual-record sets exist.
- [x] The same foundation supports substantially different Activity families.
- [x] All four scoring orientations are represented.
- [x] Individual and Group evidence, targets, Scores, and histories remain distinct.
- [x] PDS2 routing supports student, Group, multi-Subject, teacher-authored, and unresolved-attribution contexts.
- [x] Routing remains separate from registration and publication.
- [x] Review, Moderation, correction, rescan, native Score revision, and publication supersession are represented.
- [x] Core Academic Work Registration is explicit and revisioned.
- [x] Activity presence without automatic registration is represented.
- [x] Concord scoring orientation remains distinct from Core academic intent.
- [x] Six immutable Concord Academic Result Manifest objects are represented and mechanically hashed.
- [x] Stable record-set identity and increasing manifest revision are demonstrated.
- [x] Criterion, Scoring Scale, Score, evidence-lineage, Moderation, and standards projections are represented.
- [x] Local Scores remain available in the broader manifest without becoming standards ratings.
- [x] Quillan and ScoreForm source-publication lineage is preserved.
- [x] Six Core Publication Records bind exact manifest bytes.
- [x] Publication capabilities are truthful.
- [x] Idempotent replay and contradictory-revision rejection are defined.
- [x] Native Score supersession and Core publication supersession remain distinct.
- [x] Publication withdrawal is bounded explicitly without an invented record.
- [x] The derived Core catalog remains nonauthoritative.
- [x] Meridian owns overlap, eligibility, Grade-item membership, Academic Period membership, scale policy, proficiency, Grades, overrides, and reports.
- [x] No producer manifest contains authoritative Academic Period, Grade, proficiency, or Meridian override state.
- [x] ScoreForm, Quillan, and external project evidence remain externally owned.
- [x] Non-score dispositions remain explicit and valueless.
- [x] Contextual failures do not become low performance.
- [x] Optional project structures remain optional.
- [x] A non-returned instructional page is instantiated without routing.
- [x] An explicit duplicate scan is retained and nonpreferred.
- [x] A misrouted source page is corrected without changing the retained source.
- [x] No new Concord conceptual-contract or ADR content is required.

### Remaining governance and release work

- [ ] Issue #13 decides whether ADR 0015 is accepted, revised, or rejected.
- [ ] Issue #13 decides whether a concrete withdrawal record is required.
- [ ] Core releases compatible registration, publication, withdrawal, and catalog APIs.
- [ ] Meridian releases compatible import and policy contracts.
- [ ] Production schemas and deterministic serialization rules are finalized.

## 34. Final Decision

```text
Conceptual architecture: PASS
Cross-case semantic consistency: PASS
Scoring-orientation coverage: PASS
Typed-reference consistency: PASS
PDS2 primary-path validation: PASS
Detailed intake-edge coverage: PASS
Academic Work Registration validation: PASS
Manifest projection validation: PASS
Manifest digest validation: PASS
Core Publication Record validation: PASS
Publication supersession validation: PASS
Publication withdrawal: BOUNDED, NOT INSTANTIATED
Cross-producer lineage validation: PASS
Meridian ownership-boundary validation: PASS
Conceptual-contract changes required: NONE
New ADR required: NO
ADR 0015 acceptance decision: PENDING ISSUE #13
Runtime registry readiness: NOT YET
Issue #12 ready for issue #13: YES
```

Issue #12 is complete as a conceptual representative-contract validation artifact.

The next step is the skeptical foundation review in issue #13.
