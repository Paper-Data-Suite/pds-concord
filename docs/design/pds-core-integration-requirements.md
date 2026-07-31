# PDS Core Integration Requirements

**Status:** Accepted integration architecture record; PDS2 is released, while Core registry and Academic Period integration remain pre-release mainline architecture
**Project:** Paper Data Suite
**Module:** `pds-concord`
**Issue:** `Paper-Data-Suite/pds-concord#10`
**Original date:** July 13, 2026
**PDS2 reconciliation:** July 24, 2026
**Registry and Meridian reconciliation:** July 29, 2026
**Revision:** 3 — incorporates ADR 0015, Core Academic Work Registration and Publication Records, Core Academic Periods, and Meridian ownership
**Released Core baseline:** `pds-core` 0.5.0, Python 3.11+, PDS2
**Post-0.5 architecture reviewed:** current `pds-core` mainline Academic Period, Academic Work Registration, Publication Record, withdrawal, and derived-catalog contracts

## 1. Purpose

This document records the integration requirements that led to the released `pds-core` 0.5/PDS2 architecture and defines the continuing integration boundary among:

* Core-owned routing and source-retention infrastructure;
* Core-owned Academic Period, Academic Work Registration, and publication-registry infrastructure;
* Concord-owned collaborative evidence, Review, Moderation, Criteria, Scores, and result manifests;
* and Meridian-owned grading and reporting policy.

The document was originally written prospectively, before PDS2 and module-qualified work identity were implemented. It is retained because it explains:

* why the earlier student-oriented PDS1 model could not represent Concord;
* why page routing must remain separate from Artifact Authors, Artifact Subjects, students, Groups, Criteria, standards, and Score targets;
* why module work identity must be qualified by module, class, and work;
* how Core-retained source scans and Concord-owned evidence remain connected;
* why physical-page routing and reportable-data publication are separate Core domains;
* how a Concord Activity may be explicitly registered as academic work without becoming a Grade item;
* how Concord publishes immutable academic-result manifests without transferring result authority to Core;
* how Meridian discovers exact published revisions without importing Concord internals;
* and which Concord implementation obligations remain after Core supplies the shared infrastructure.

The released Core 0.5 contracts govern the implemented PDS2 foundation. Core mainline now also contains accepted and substantially implemented architecture for:

* school-year-qualified hierarchical Academic Period calendars;
* revisioned Academic Work Registrations;
* immutable Publication Records;
* publication supersession and withdrawal;
* exact manifest-path and SHA-256 binding;
* idempotent producer-facing registration and publication services;
* and a disposable, nonauthoritative registry catalog.

Those post-0.5 capabilities are not assumed to be part of the released `pds-core` 0.5 public API. Concord may reconcile its architecture and examples against them now, but runtime dependency ranges and implementation claims must wait for an applicable Core release or another explicitly stabilized integration baseline.

For current Concord domain, scoring, and publication semantics, the governing Concord documents are:

* `docs/concord-conceptual-design-revised.md`;
* `docs/design/cross-case-requirements.md`;
* `docs/design/initial-concord-domain-model.md`;
* `docs/design/conceptual-data-contracts.md`;
* ADR 0014, which establishes standards-based scoring as Concord’s primary academic scoring model;
* and ADR 0015, which establishes versioned Concord Academic Result Manifests published through Core.

This remains an integration-architecture document. It does not define every Concord record, final serialized manifest schema, persistence service, command-line workflow, graphical workflow, Meridian policy, or formal report contract.

---
## 2. Governing Design Sources

This specification must remain consistent with accepted Concord decisions, current Concord conceptual documents, current Core contracts, and Meridian’s accepted grading and reporting architecture.

The most directly relevant Concord decisions are:

* `docs/decisions/0001-concord-module-boundaries.md`;
* `docs/decisions/0002-paper-first-human-reviewed-evidence.md`;
* `docs/decisions/0005-separate-artifact-authors-and-subjects.md`;
* `docs/decisions/0007-preserve-source-evidence-and-history.md`;
* `docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`;
* `docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`;
* `docs/decisions/0010-exceptional-evidence-states-are-not-low-scores.md`;
* `docs/decisions/0012-link-scoreform-and-quillan-without-duplication.md`;
* `docs/decisions/0013-keep-activity-specific-structures-optional.md`;
* `docs/decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md`;
* and `docs/decisions/0015-publish-versioned-concord-academic-result-manifests-through-the-core-registry.md`.

The current Concord conceptual authorities are:

* `docs/concord-conceptual-design-revised.md`;
* `docs/design/cross-case-requirements.md`;
* `docs/design/initial-concord-domain-model.md`;
* and `docs/design/conceptual-data-contracts.md`.

The relevant released Core authorities include:

* `pds-core` 0.5.0;
* the PDS2 payload contract;
* routing identity models;
* deterministic module-qualified workspace contracts;
* Route Registration persistence;
* module-profile registration and dispatch;
* active source-scan retention and provenance;
* generic routing failure and resolution schema version 2;
* Core standards contracts;
* and Core standards module-integration guidance.

The relevant post-0.5 Core authorities reviewed for this reconciliation include:

* Core ADR 0002, adopting a typed work and reportable-data publication registry;
* Core ADR 0003, adopting a school-year-scoped hierarchical Academic Period model;
* the `AcademicWorkRegistration` model and canonical revision storage;
* the immutable `PublicationRecord` and `PublicationWithdrawal` models;
* producer-facing registration and publication services;
* canonical publication-series validation;
* and the derived registry catalog.

The relevant Meridian authorities include:

* Meridian’s repository purpose and architectural boundary;
* its accepted grading architecture;
* and its accepted reporting architecture.

Those sources establish that Meridian owns policy-driven:

* evidence selection;
* standards-proficiency calculation;
* Grade-item membership;
* reassessment handling;
* conventional, standards-based, and hybrid grading;
* Academic Period aggregation;
* teacher overrides of derived results;
* report composition;
* report snapshots and provenance;
* report subscriptions;
* and coordination with authorized report-delivery systems.

The released Core contracts govern shared QR, route, path, scan, profile, and standards-reference behavior.

The current Core registry contracts govern shared registration and publication envelopes, manifest binding, publication lifecycle, and discovery. They do not define Concord-native result meaning.

Concord ADRs and conceptual contracts govern Concord-owned Activity, Artifact, Author, Subject, Review, Moderation, Criterion, Score, evidence-lineage, and manifest semantics.

Meridian contracts govern Grade eligibility, evidence selection, proficiency, Grade calculation, Academic Period membership, derived overrides, and formal reporting.

When historical language in this document conflicts with released Core 0.5 routing contracts, the released contract governs routing.

When this document conflicts with a later accepted Core registry contract, the later Core contract governs the shared registry envelope.

When this document conflicts with an accepted Concord ADR, the Concord ADR governs Concord semantics unless a later ADR explicitly supersedes it.

---
## 3. Decision Summary

The integration adopts four deliberately separate domains.

### 3.1 Physical-page routing

1. Use the released `PDS2` page-locator contract in place of historical PDS1 and OMR1 routing.
2. Give every scannable returned page a durable, module-owned route identity before rendering.
3. Encode only module, class, work, and route identity in the QR.
4. Resolve participant, Group, Author, Subject, template, Artifact, Criterion, Score target, and other semantic context from persisted Core and module-owned records.
5. Persist Route Registrations at deterministic Core-defined paths.
6. Preserve Core source-scan retention, immutability, provenance, and append-only resolution behavior.
7. Keep route dispatch separate from publication compatibility and grading/reporting compatibility.

The routing principle is:

> A QR code identifies an expected physical page route. It does not identify the page’s Author, Subject, scorer, Score target, standard, Grade item, Academic Period, or report.

### 3.2 Neutral module work identity

8. Use `ModuleWorkRef` as the shared identity for one module-owned top-level work context:

   ```text
   module_id + class_id + work_id
   ```

9. For Concord:

   ```text
   module_id = concord
   work_id = activity_id
   ```

10. Store Concord work beneath the module-qualified root:

    ```text
    classes/<class_id>/modules/concord/work/<activity_id>/
    ```

11. Do not infer that a `ModuleWorkRef` is academic, graded, reportable, or assigned to an Academic Period merely because it exists.

### 3.3 Academic registration and result publication

12. Register a Concord Activity as academic work only through an explicit Core Academic Work Registration.
13. Do not infer registration from Activity orientation, Focus Standards, page generation, or the existence of a Score.
14. Keep Concord `scoring_orientation`, Core `academic_intent`, and Meridian Grade-item membership as separate decisions.
15. Publish selected Concord results through an immutable, revision-addressable Concord Academic Result Manifest.
16. Store each publishable manifest beneath the exact Concord Activity work root.
17. Bind exact manifest bytes to an immutable Core Publication Record using a safe workspace-relative path and SHA-256 digest.
18. Publish Concord result manifests as Core `publication_kind: academic_result_set`.
19. Advertise only truthful Core-controlled capabilities such as `criterion_scores`, `standards_ratings`, and `moderated_scores`.
20. Preserve native Score supersession separately from manifest revision and Core Publication Record supersession.
21. Use Core withdrawal rather than mutation when a published revision should no longer be newly selected.
22. Treat the Core catalog as derived and disposable, never as the authority for registration, publication, or manifest content.

### 3.4 Meridian consumption

23. Allow Meridian to discover exact Concord publications through Core without recursively crawling Concord directories or importing Concord private code.
24. Preserve standard-backed and local Score classifications in the manifest.
25. Publish local Scores where academically relevant without representing them as direct standards ratings.
26. Preserve explicit non-score dispositions without converting them into zero.
27. Preserve exact Scoring Scale revisions and meanings rather than normalizing them in Core or Concord publication.
28. Preserve cross-producer evidence lineage so Meridian can recognize related ScoreForm, Quillan, and Concord results.
29. Assign Grade-item membership, standards-evidence eligibility, evidence selection, reassessment, weighting, scale mapping, Academic Period membership, proficiency, Grades, overrides, and formal reporting to Meridian.
30. Do not mutate Concord records when Meridian recalculates or overrides a derived result.

The complete integration principle is:

> Routing locates pages. Registration declares academic intent. Publication announces exact producer-owned result projections. Meridian applies grading and reporting policy.

---
## 4. Historical Pre-PDS2 Contract Defects

This section describes the defects in the earlier PDS1-era contracts that motivated PDS2. The defects are retained as architectural rationale; they are not descriptions of the released Core 0.5 design.


### 4.1 Student identity is universally required

The earlier normalized `QrPayload` required:

* `schema`;
* `module`;
* `class_id`;
* `assignment_id`;
* `student_id`;
* `page`;
* and optional metadata.

The earlier `PDS1` parser similarly required:

```text
module
class
aid
sid
page
```

This prevents valid Concord pages from being represented when:

* there is no student Subject;
* there are several Subjects;
* the Subject is a Group, Session, Activity, Event, or Artifact;
* the Author differs from the Subject;
* the Subjects are unresolved until Review;
* or the page is a teacher-authored tracker concerning several students or Groups.

Making `student_id` nullable would not solve the deeper problem. It would preserve a model in which student identity remains privileged as the presumed route target.

### 4.2 Assignment identity is not module-qualified

The earlier route layout used:

```text
classes/<class_id>/assignments/<assignment_id>/
```

Different modules can legitimately use the same identifier, such as:

```text
project_check
```

A bare `assignment_id` does not distinguish:

* ScoreForm assignment `project_check`;
* Quillan assignment `project_check`;
* Concord Activity `project_check`;
* or a similarly named record in a future module.

The earlier shared `assignment.json` also created an ownership collision because each module has a different assignment or activity schema.

### 4.3 The route destination is student-specific

The earlier universal route terminated in:

```text
submissions/<student_id>/
```

That path is appropriate as a Quillan-owned convenience and may remain useful to ScoreForm. It is not a valid universal destination.

A Concord Artifact Page may belong operationally beneath an Artifact Instance while concerning:

* no student;
* one student;
* several students;
* one or more Groups;
* a Session;
* an Activity;
* an Event;
* or another contextual record.

### 4.4 QR metadata duplicates mutable semantic data

The earlier payload could carry student, page number, document type, template, form, attempt, and similar values.

Encoding semantic context in the QR creates several risks:

* the printed metadata may disagree with the authoritative module record;
* later attribution corrections cannot change the paper QR;
* duplicated values require conflict-resolution rules;
* the payload grows as workflows become more complex;
* and future modules may add incompatible optional fields.

The QR should contain a stable locator. The authoritative semantic record should remain outside the QR.

### 4.5 Failure metadata assumes assignment and student resolution

The earlier shared failure schema contained top-level:

* `class_id`;
* `assignment_id`;
* and `student_id`.

The earlier shared categories included:

* `assignment_unknown`;
* and `student_unknown`.

These fields and categories cannot serve as the universal route model for non-student pages.

### 4.6 Package relationships are implicit

At the time of the original specification, ScoreForm and Quillan imported Core code without declaring a released, versioned `pds-core` runtime dependency.

At that time, Quillan also relied on a sibling-repository `mypy_path`.

A coordinated breaking contract requires explicit dependency declarations and compatible supported Python versions.

---
## 5. Ownership Boundaries

### 5.1 Core ownership

`pds-core` owns shared canonical infrastructure, including:

#### Routing and workspace

* workspace-root resolution;
* canonical class identity;
* roster and student identity;
* identifier validation;
* module-qualified work references;
* safe module work-root construction;
* the shared PDS2 QR grammar;
* QR parsing and serialization;
* generic route-locator models;
* typed module-record references;
* Route Registration schema and deterministic paths;
* route-registration lifecycle validation;
* module-profile registration and page dispatch;
* active source-scan retention;
* source-scan identity and provenance;
* shared routing-failure metadata;
* and shared routing-resolution metadata.

#### Standards and Academic Periods

* shared standards definitions and profiles;
* durable `standard_id` and `profile_id` identity;
* standards-library storage and module-neutral validation;
* school-year-qualified Academic Period references;
* revisioned Academic Period calendars;
* period hierarchy and date validation;
* and exact calendar-revision resolution.

#### Academic registration and publication

* the Academic Work Registration envelope and canonical revision storage;
* Academic Work Registration lifecycle and transition rules;
* Publication Record identity and schema;
* publication-kind vocabulary;
* shared publication-capability vocabulary;
* safe manifest-path validation;
* exact SHA-256 manifest binding;
* publication idempotency and conflict rules;
* publication-series supersession;
* immutable publication withdrawals;
* canonical registration and publication retrieval;
* and the disposable, nonauthoritative registry catalog.

Core may carry typed references to Concord records and manifests without interpreting their domain meaning.

### 5.2 Concord ownership

Concord owns:

* the meaning of a Concord Activity;
* Activity scoring orientation and Focus Standard selection;
* generation of Concord Artifact Page records;
* the semantic target represented by each Concord Route Registration;
* Artifact Authors and Subjects;
* Group, Membership, Role, and Responsibility context;
* Concord-specific evidence filing;
* Review and Moderation;
* Criteria and Scoring Scales;
* Score Records and Score Evidence Links;
* non-score dispositions;
* native Score correction and supersession;
* external evidence relationships;
* the Concord Academic Result Manifest contract;
* manifest generation and validation;
* producer-owned `record_set_id` and `record_set_revision` assignment;
* deciding when a native change warrants a new manifest revision;
* and the educational meaning of every published manifest value.

### 5.3 Meridian ownership

Meridian owns:

* source subscriptions and publication selection;
* exact imported-publication tracking;
* Grade-item membership;
* standards-evidence eligibility;
* evidence and attempt selection;
* reassessment policy;
* cross-producer overlap and deduplication policy;
* standards-proficiency calculation;
* conventional, standards-based, and hybrid grading policies;
* scale mapping and conversion;
* weighting and categories;
* minimum-evidence rules;
* Academic Period membership;
* Grade calculation and Grade history;
* teacher overrides of Meridian-derived results;
* reproducible calculation snapshots;
* formal report definitions and snapshots;
* audience-specific reports;
* report subscriptions;
* and delivery coordination.

Meridian must not mutate Concord-native records or silently replace an imported publication revision.

### 5.4 Core must not own Concord or Meridian semantics

Core does not define or interpret:

* Activity;
* Session;
* Group;
* Group Membership;
* Role Assignment;
* Responsibility Assignment;
* Packet Instance;
* Artifact Instance;
* Artifact Author;
* Artifact Subject;
* Artifact Review;
* Moderation Record;
* Concord Criterion;
* Concord Score;
* Score Evidence Link;
* evidence eligibility;
* Grade-item membership;
* standards proficiency;
* Grade calculation;
* or report composition.

Core validates shared envelopes and identities. It does not perform educational interpretation.

### 5.5 No mandatory sibling dependencies

The dependency direction is:

```text
pds-scoreform -> pds-core
pds-quillan   -> pds-core
pds-concord   -> pds-core
pds-meridian  -> pds-core
```

The following must not be required:

```text
pds-concord -> pds-scoreform
pds-concord -> pds-quillan
pds-concord -> pds-meridian
pds-meridian -> private Concord implementation
pds-core -> pds-concord
pds-core -> pds-meridian
```

Cross-module relationships must use:

* Core identities;
* Core Publication Records;
* public producer manifests;
* module-qualified references;
* documented serialized contracts;
* or optional adapters that preserve ownership.

---
## 6. Shared Identity Model

### 6.1 Module identifier

Every participating PDS module has one stable lowercase `module_id` satisfying Core identifier rules.

Relevant values include:

```text
scoreform
quillan
concord
meridian
```

A `module_id` is a durable machine identifier, not a package import path or display label.

### 6.2 Module work reference

Core provides the neutral top-level work identity:

```text
ModuleWorkRef
├── module_id
├── class_id
└── work_id
```

The effective identity is:

```text
module_id + class_id + work_id
```

Module mappings include:

| Module | Meaning of `work_id` |
| --- | --- |
| ScoreForm | `assignment_id` |
| Quillan | `assignment_id` |
| Concord | `activity_id` |
| Portia | Event or Support Process identity selected by its contract |
| Future producer | Durable top-level module work identity |

A `ModuleWorkRef` does not assert that the work is:

* academic;
* graded;
* reportable;
* registered;
* published;
* or associated with an Academic Period.

### 6.3 Route identifier

Every scannable returned page receives one durable `route_id` before rendering.

A route ID is:

* collision-resistant;
* non-empty;
* path-safe and QR-safe;
* immutable after printing;
* non-semantic;
* unique within its `ModuleWorkRef`;
* and never reused for another target.

It must not encode student, Group, Score, standard, Grade, Academic Period, or report semantics.

### 6.4 Module record reference

Core provides `ModuleRecordRef`:

```text
ModuleRecordRef
├── module_id
├── record_kind
├── record_id
└── optional contract_version
```

Core validates the shape but does not interpret the producer-controlled `record_kind`.

For Concord publication, an Activity reference is conceptually:

```yaml
module_id: concord
record_kind: activity
record_id: <activity_id>
contract_version: <public Concord Activity contract version>
```

### 6.5 Academic Period reference

Core provides a school-year-qualified Academic Period reference:

```text
AcademicPeriodRef
├── school_year
└── period_id
```

A bare label such as `MP1` is not a durable shared period identity.

Concord does not assign authoritative Academic Period membership to Scores or publications. Meridian references Core periods when applying period policy.

### 6.6 Academic Work Registration identity

The identity of a Core Academic Work Registration is the complete `ModuleWorkRef`.

For Concord:

```text
module_id: concord
class_id: <Activity class_id>
work_id: <Activity activity_id>
```

Registration revisions preserve one stable work identity while allowing controlled metadata changes.

The registration revision is not:

* an Activity revision;
* a Score revision;
* a manifest revision;
* or a Grade-item revision.

### 6.7 Concord manifest record-set identity

A Concord Academic Result Manifest belongs to one stable producer-owned result-set series identified by:

```text
ModuleWorkRef + record_set_id
```

Each immutable revision also has:

```text
record_set_revision
manifest_contract_version
manifest_path
manifest_digest
```

`record_set_id` must be lowercase, stable, safe, unique within the work context, and free of direct personal information.

### 6.8 Core Publication Record identity

A Core Publication Record has a Core-owned `publication_id` and binds one exact manifest revision.

The following remain distinct:

```text
publication_id
record_set_id
record_set_revision
manifest_contract_version
manifest_digest
source Score identities
```

A Core Publication Record is not the manifest and does not replace native Score identity.

### 6.9 Distinct identities

The following identities must remain separate:

```text
PDS2 route locator
Route Registration
ModuleWorkRef
Academic Work Registration revision
module-owned record reference
Concord Activity
Concord Score Record
Concord manifest record-set series
Concord manifest revision
Core Publication Record
Meridian imported-source record
Meridian Grade item
Meridian proficiency or Grade result
Meridian report snapshot
```

No identity may be inferred universally from another.

---
## 7. PDS2 QR Contract

### 7.1 New schema identifier

The released QR contract uses the schema identifier:

```text
PDS2
```

The existing `PDS1` contract materially means:

```text
module + class + assignment + student + page number
```

The new contract means:

```text
module + class + module work unit + durable page route
```

Reusing `PDS1` would make old and new payloads appear to share semantics when they do not.

### 7.2 Canonical payload

The canonical `PDS2` form is:

```text
PDS2|m=<module_id>|c=<class_id>|w=<work_id>|r=<route_id>
```

Examples:

```text
PDS2|m=scoreform|c=english9_p2|w=rj_act1_quiz|r=rt_01j2m8f4k9v7
```

```text
PDS2|m=quillan|c=english12_p4|w=personal_narrative|r=rt_01j2m8g6p3q1
```

```text
PDS2|m=concord|c=english10_p3|w=socratic_seminar_1|r=rt_01j2m8h8x5z2
```

### 7.3 Required fields

Every valid `PDS2` payload contains exactly these four fields:

| QR key | Internal name | Meaning                                  |
| ------ | ------------- | ---------------------------------------- |
| `m`    | `module_id`   | Owning PDS module                        |
| `c`    | `class_id`    | Core class identifier                    |
| `w`    | `work_id`     | Module-owned top-level route context     |
| `r`    | `route_id`    | Durable expected-page route registration |

All four fields are required.

### 7.4 Why the QR is page-locator based

Every physical page that is expected to return through scanning must have a durable route registration.

The QR therefore identifies an expected page route rather than:

* a student;
* an Artifact Subject;
* a document plus mutable page number;
* or an arbitrary destination path.

This provides one consistent model for all modules:

```text
physical page
    -> PDS2 RouteLocator
    -> persisted RouteRegistration
    -> module-owned page record
    -> module-owned semantic context
```

For Concord, the route registration normally targets one `Artifact Page`.

For ScoreForm, it targets one generated answer-sheet page record.

For Quillan, it targets one generated response-page record.

### 7.5 Fields deliberately excluded from PDS2

The following must not appear in the common QR envelope:

* `student_id`;
* student name;
* Author identity;
* Subject identity;
* Group identity;
* Session identity other than what the owning module resolves from its work and page records;
* template identifier;
* form identifier;
* attempt number;
* page number;
* total page count;
* document type;
* scoring criterion;
* expected score target;
* assignment title;
* marking period;
* assessment category;
* destination path;
* or arbitrary module metadata.

These values belong in the route registration or owning module’s records.

### 7.6 Page number is not part of the locator

A logical page number is not required in `PDS2` because `route_id` identifies one expected physical page.

The owning page record may contain:

* logical page number;
* total expected pages;
* page kind;
* continuation relationship;
* packet position;
* form version;
* or print-copy context.

Removing page number from the QR prevents conflicting states such as:

```text
route record says page 2
QR says page 3
```

The human-readable page number should still be printed normally on the document.

### 7.7 Student identity is resolved, not encoded

ScoreForm and Quillan may continue to require one student for their own workflows.

They must resolve that student through their page record:

```text
route_id
    -> answer_sheet_page or response_page
    -> student_id
```

The absence of `student_id` from the QR does not prevent student workflows. It prevents student identity from being treated as the universal route model.

### 7.8 Strict grammar

The parser enforces:

* the first segment is exactly `PDS2`;
* subsequent segments use `key=value`;
* exactly four keys are present;
* keys are unique;
* values are non-empty;
* no unknown keys are accepted;
* no empty segments are accepted;
* values satisfy their field-specific identifier rules;
* and the complete payload satisfies the configured maximum length.

Field order must not affect parsing.

The canonical serializer emits:

```text
PDS2|m=...|c=...|w=...|r=...
```

in that order.

### 7.9 No arbitrary extension fields

`PDS2` must not preserve arbitrary unknown keys as metadata.

Arbitrary extension fields would:

* make payload meaning dependent on module-specific parsing;
* increase QR density;
* create silent compatibility differences;
* and encourage semantic data to migrate back into the QR.

A future universally required routing field should be introduced through an explicitly versioned contract decision. Module-specific data belongs in module records.

### 7.10 Payload size

Core enforces an absolute serialized payload limit under the released contract.

The architectural maximum is:

```text
256 ASCII bytes
```

Generators should warn or fail earlier when identifiers produce a payload above the recommended operational target of:

```text
160 ASCII bytes
```

All `PDS2` field values must use the safe ASCII identifier character set, making byte length deterministic.

The compact QR keys exist to reduce print density without sacrificing an inspectable grammar.

### 7.11 Human-readable fallback

Every generated scannable page must print a human-readable fallback near the QR code.

The fallback must include enough information to recover the route manually, such as:

```text
PDS2 · concord · english10_p3 · socratic_seminar_1 · rt_01j2m8h8x5z2
```

A shorter display may be used if it remains lossless through a deterministic lookup.

The fallback must not expose a student name or other unnecessary personal information.

### 7.12 QR is not authorization

A valid QR code is a locator, not proof that:

* the page is authentic;
* the page was completed by an expected Author;
* its Subjects are correct;
* the page may be scored;
* or the route target should be created automatically.

Modules must verify the persisted route registration and apply their normal Review and validation rules.

---
## 8. Route Registration Contract

### 8.1 Purpose

A `RouteRegistration` is the persisted Core-readable record that connects one `PDS2` locator to one module-owned target.

It must exist before the corresponding QR is rendered.

The QR alone is not the complete route record.

### 8.2 Conceptual structure

A route registration should contain at least:

```json
{
  "schema_version": "1",
  "locator": {
    "schema": "PDS2",
    "module_id": "concord",
    "class_id": "english10_p3",
    "work_id": "socratic_seminar_1",
    "route_id": "rt_01j2m8h8x5z2"
  },
  "target": {
    "module_id": "concord",
    "record_kind": "artifact_page",
    "record_id": "artifact_page_01j2m8h7b6a4",
    "contract_version": "1"
  },
  "created_at": "2026-07-13T19:00:00-04:00",
  "status": "active",
  "human_fallback": "rt_01j2m8h8x5z2",
  "module_details": {}
}
```

### 8.3 Shared fields

Core owns validation of:

* registration schema version;
* locator structure;
* target-reference structure;
* creation timestamp;
* route status;
* human fallback;
* and JSON-serializable `module_details`.

### 8.4 Module details

`module_details` may contain module-owned routing diagnostics or lightweight lookup information.

It must not become a copied replacement for the authoritative module record.

Examples might include:

* expected document role;
* logical page number;
* expected page count;
* or a display label.

The target record remains authoritative.

### 8.5 Immutability and lifecycle

After a page is printed:

* its `route_id` must not be reused;
* its locator must not be changed;
* and its route registration must never be repointed silently to a different target.

A route may later become:

* inactive;
* retired;
* superseded;
* cancelled;
* or invalidated.

Such changes must preserve history.

A scanned old page should still resolve to its historical registration so the system can explain why the page is inactive or superseded.

### 8.6 Route registration is not an assignment registry

Route registrations identify expected physical page routes.

They do not replace a future suite assignment registry.

A future assignment registry will index module work references and academic organization. Route registrations operate at the generated-page level beneath those work references.

---
## 9. Deterministic Workspace and Registry Layout

### 9.1 Required module-qualified work root

Core uses a module-qualified work root:

```text
<PDS workspace>/
  classes/
    <class_id>/
      class.json
      roster.csv
      modules/
        <module_id>/
          work/
            <work_id>/
```

The effective path identity is:

```text
classes/<class_id>/modules/<module_id>/work/<work_id>/
```

For Concord:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
```

### 9.2 Route Registration location

Core defines deterministic Route Registration lookup from a `RouteLocator`.

Conceptually:

```text
classes/<class_id>/modules/<module_id>/work/<work_id>/routes/<route_id>.json
```

Callers use Core route helpers and do not construct the path manually.

### 9.3 Concord-owned contents

A representative Concord work root may contain:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
  activity.json
  sessions/
  groups/
  packets/
  artifacts/
  routes/
  reviews/
  moderation/
  scores/
  attachments/
  exports/
    manifests/
      <record_set_id>/
        <record_set_revision>.json
```

This is a conceptual layout, not a final module persistence contract.

Core owns safe construction of the work root. Concord owns the meaning and internal layout of its descendants except where a Core contract explicitly governs a shared descendant such as `routes/`.

### 9.4 Manifest path requirements

A published Concord manifest path must be:

* workspace-relative;
* normalized with forward slashes;
* free of absolute, drive, empty, dot, or traversal components;
* beneath the exact referenced Concord work root;
* outside Core-owned registry storage;
* revision-addressed;
* and ending in `.json`.

A representative path is:

```text
classes/<class_id>/modules/concord/work/<activity_id>/exports/manifests/<record_set_id>/<record_set_revision>.json
```

A mutable convenience path such as:

```text
exports/latest.json
```

may exist but must not be the canonical target of a Core Publication Record.

### 9.5 Core-owned registry storage

Core stores canonical registry records outside producer work roots.

Conceptually, the registry includes separate namespaces for:

```text
Academic Work Registrations
Publication Records
Publication Withdrawals
Derived catalog
```

Exact directory names, sharding, and filenames belong to Core.

Producer code must use Core registry services and path APIs rather than writing registry files directly.

### 9.6 Derived catalog

Core may maintain:

```text
registry/catalog.sqlite
```

as a disposable discovery accelerator.

The catalog:

* is explicitly rebuilt from bounded canonical Core JSON records;
* is not authoritative;
* does not crawl producer work directories during rebuild;
* does not open producer manifests merely to enumerate publications;
* may be missing, stale, locked, malformed, corrupt, or deleted without invalidating canonical records;
* and cannot create, revise, supersede, withdraw, or select a publication.

### 9.7 Core path APIs

Core supplies public helpers for:

* class and module work roots;
* Route Registration paths;
* Academic Work Registration storage and retrieval;
* Publication Record and withdrawal storage and retrieval;
* and safe producer manifest-path validation.

Modules must not bypass those helpers through unvalidated string concatenation.

---
## 10. Shared Core Models Relevant to Concord

Core separates routing identity, academic registration, publication identity, and Academic Period identity through explicit public models.

Representative conceptual models follow. Exact implementation classes and field types remain governed by Core.

### 10.1 Routing models

```python
@dataclass(frozen=True, slots=True)
class ModuleWorkRef:
    module_id: str
    class_id: str
    work_id: str
```

```python
@dataclass(frozen=True, slots=True)
class RouteLocator:
    schema: Literal["PDS2"]
    work: ModuleWorkRef
    route_id: str
```

```python
@dataclass(frozen=True, slots=True)
class ModuleRecordRef:
    module_id: str
    record_kind: str
    record_id: str
    contract_version: str | None = None
```

```python
@dataclass(frozen=True, slots=True)
class RouteRegistration:
    schema_version: str
    locator: RouteLocator
    target: ModuleRecordRef
    created_at: datetime
    status: str
    human_fallback: str
    module_details: Mapping[str, JsonValue]
```

A shared route resolution does not universally contain student, submission, Author, Subject, standard, Score, Grade, or Academic Period fields.

### 10.2 Academic Period models

Conceptually:

```python
@dataclass(frozen=True, slots=True)
class AcademicPeriodRef:
    school_year: str
    period_id: str
```

```python
@dataclass(frozen=True, slots=True)
class AcademicPeriod:
    period_id: str
    period_type: str
    label: str
    start_date: date
    end_date: date
    parent_period_id: str | None
    sequence: int
    lifecycle: str
```

Core owns period identity and calendar revisions. Meridian owns Grade-item and result membership in those periods.

### 10.3 Academic Work Registration

Core’s implemented registration model conceptually contains:

```python
@dataclass(frozen=True, slots=True)
class AcademicWorkRegistration:
    schema_version: str
    record_type: Literal["academic_work_registration"]
    work: ModuleWorkRef
    registration_revision: int
    producer_contract_version: str
    title: str
    work_kind: str
    academic_intent: str
    lifecycle: str
    created_at: datetime
    updated_at: datetime
    source_records: tuple[ModuleRecordRef, ...]
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

Core controls registration lifecycle values:

```text
planned
active
closed
cancelled
```

Registration does not publish results, create a Grade item, or assign an Academic Period.

### 10.4 Publication Record

Core’s implemented Publication Record conceptually contains:

```python
@dataclass(frozen=True, slots=True)
class PublicationRecord:
    schema_version: str
    record_type: Literal["publication_record"]
    publication_id: str
    work: ModuleWorkRef
    source_record: ModuleRecordRef | None
    publication_kind: str
    capabilities: tuple[str, ...]
    record_set_id: str
    record_set_revision: int
    manifest_contract_version: str
    manifest_path: str
    manifest_digest_algorithm: Literal["sha256"]
    manifest_digest: str
    published_at: datetime
    academic_work_registration_revision: int | None
    supersedes_publication_id: str | None
```

Initial Core publication kinds are:

```text
academic_result_set
intervention_record_set
```

A Concord Academic Result Manifest uses:

```text
academic_result_set
```

and requires the exact current Academic Work Registration revision at publication time.

### 10.5 Publication Withdrawal

Core represents withdrawal as a separate immutable record:

```python
@dataclass(frozen=True, slots=True)
class PublicationWithdrawal:
    schema_version: str
    record_type: Literal["publication_withdrawal"]
    publication_id: str
    withdrawn_at: datetime
    reason: str
```

Withdrawal does not delete or mutate the Publication Record, manifest, or native Concord records.

### 10.6 Authority rules

Core validates exact shared shapes and relationships.

Concord validates:

* Activity state;
* manifest body;
* Score and Criterion semantics;
* evidence lineage;
* Moderation requirements;
* and whether native changes require a new manifest revision.

Meridian validates:

* supported manifest contracts and capabilities;
* source eligibility;
* policy applicability;
* Grade-item and Academic Period membership;
* and derived calculations.

---
## 11. Module Profiles, Dispatch, and Publication Compatibility

### 11.1 Routing profile requirement

Core recognizes installed modules for PDS2 page dispatch through a routing-oriented module profile.

A routing profile provides at least:

* stable `module_id`;
* supported Core routing contract range;
* supported Route Registration contract range;
* optional registration validation hooks;
* and page dispatch integration.

Core does not derive import paths from arbitrary QR module values.

### 11.2 Routing registration mechanisms

Core may support:

* explicit application registration;
* Python entry points;
* or another documented discovery mechanism.

Unsupported or incompatible modules fail explicitly.

### 11.3 Publication compatibility is separate

Routing compatibility does not imply publication compatibility.

The questions are different:

```text
Routing profile:
Can this installed module receive a resolved physical page?
```

```text
Publication producer compatibility:
Can this module publish this publication kind, manifest contract, and capability set?
```

```text
Meridian consumer compatibility:
Can Meridian import and interpret this exact producer manifest contract under an authorized policy?
```

Core’s current routing `ModuleProfile` must not be silently expanded to mean all three.

A later public producer-compatibility profile may advertise:

* supported publication kinds;
* supported manifest contract versions;
* supported shared capabilities;
* and producer-specific compatibility information.

It may use a dedicated entry point or another Core-defined interface.

### 11.4 Core validation versus module validation

Core validates:

* PDS2 grammar;
* shared identifiers;
* deterministic paths;
* exact locator matching;
* Route Registration shape;
* Academic Work Registration shape and transitions;
* Publication Record envelope;
* safe manifest path;
* SHA-256 digest;
* publication idempotency;
* supersession series;
* withdrawal relationship;
* and catalog reconstruction from canonical records.

Concord validates:

* native target existence and lifecycle;
* Activity and Artifact semantics;
* standards and Criterion relationships;
* Score values and dispositions;
* Moderation completeness;
* manifest body and lineage;
* and manifest revision necessity.

Meridian validates:

* consumer support for the manifest contract;
* policy compatibility;
* source authorization;
* and derived-result rules.

### 11.5 Offline canonical validation

Core must be able to validate canonical registration and Publication Record envelopes without importing Concord or Meridian.

A producer-specific adapter may provide richer compatibility checks, labels, or opening behavior, but it does not transfer manifest authority to Core.

---
## 12. Integration Workflows

### 12.1 Successful PDS2 routing workflow

1. Concord creates an Activity.
2. Concord creates one durable Artifact Page for each expected returned physical page.
3. Concord creates and persists a Core Route Registration targeting each page.
4. Concord renders the canonical PDS2 QR from the Route Locator.
5. The page is printed and used.
6. Core retains an immutable source copy before module-specific processing.
7. Core decodes and validates the PDS2 locator.
8. Core resolves the routing module profile.
9. Core loads and validates the deterministic Route Registration.
10. Core confirms exact locator consistency.
11. Concord receives the resolved route and Core source-page provenance.
12. Concord validates the Artifact Page and creates a Scan Reference or other routed evidence relationship.
13. Review, Moderation, and Scoring occur under Concord rules.

Core does not infer Author, Subject, Score target, standard, or Grade membership from the route.

### 12.2 Academic Work Registration workflow

1. A Concord Activity and its module work root already exist.
2. An authorized workflow explicitly selects academic registration.
3. Concord supplies the complete `ModuleWorkRef` and Activity `ModuleRecordRef`.
4. Concord supplies teacher-readable metadata, `work_kind`, `academic_intent`, and lifecycle.
5. Core validates the exact registration request.
6. Core creates revision 1 or an explicit later revision under expected-revision protection.
7. Core preserves prior registration revisions and selects the new current revision.
8. Registration remains distinct from publication and Meridian Grade-item membership.

### 12.3 Concord manifest generation workflow

1. Concord validates canonical Activity, Criterion, Scale, Score, evidence-link, and Moderation records.
2. Concord selects the exact publishable result-set projection.
3. Concord assigns a stable `record_set_id` and a new positive `record_set_revision`.
4. Concord generates the complete manifest bytes under a supported Concord manifest contract.
5. Concord validates the manifest body.
6. Concord writes the manifest exclusively to a new revision-addressed path beneath the Activity work root.
7. Concord durably closes the manifest.
8. Published bytes are never rewritten.

### 12.4 Core publication workflow

1. Concord submits the exact manifest path, manifest contract version, publication kind, capabilities, record-set identity, revision, source Activity reference, and the exact current Academic Work Registration revision at publication time. For initial Concord publication, the submitted source Activity reference must equal the manifest’s `source_activity`; its `record_id` must equal `work.work_id`; and the manifest Activity context must identify the same `work.class_id` and `work.work_id`.
2. Core validates the shared publication envelope.
3. Core verifies that the path is safe, workspace-relative, work-scoped, and present.
4. Core calculates or verifies the SHA-256 digest.
5. Core reconciles exact replay idempotently. Exact replay requires agreement on `work`, source record, publication kind, capabilities, record-set identity and revision, manifest contract version, path, digest algorithm, digest, Academic Work Registration revision, and predecessor publication identity.
6. Core rejects contradictory reuse of the same logical revision.
7. Core exclusively creates the immutable Publication Record.
8. Core updates the derived catalog or reports canonical success with catalog partial failure.
9. Concord displays or records the resulting publication state.

The presence of an unpublished manifest file does not imply successful publication.

### 12.5 Meridian import workflow

1. Meridian queries canonical or derived Core discovery surfaces.
2. Meridian selects a compatible, authorized, nonwithdrawn Publication Record.
3. Meridian preserves the exact Core `publication_id`, digest, manifest contract version, record-set identity, revision, and registration revision.
4. Meridian loads the exact manifest bytes and verifies digest compatibility.
5. Meridian interprets the manifest through the public Concord contract or compatible adapter.
6. Meridian applies explicit source-selection, standards-evidence, Grade-item, reassessment, Academic Period, and grading policy.
7. Meridian creates reproducible derived results and report snapshots without modifying Concord or Core records.

### 12.6 Correction and replacement workflow

A native Concord judgment change requires:

```text
new or superseding Concord Score
    -> new manifest revision
    -> new Core Publication Record
```

A publication defect requiring immediate removal may require:

```text
Core Publication Withdrawal
    -> later corrected manifest revision
    -> new Core Publication Record
```

A Meridian-only policy or override change requires no Concord Score or manifest mutation.

---
## 13. Source-Scan Retention and Provenance

### 13.1 Preserve the existing source-retention model

The current Core source-retention principles must remain:

* copy the readable source before module-specific processing;
* leave the teacher’s external file untouched;
* retain every intake event separately;
* use collision-resistant names;
* preserve the full source hash;
* do not silently overwrite;
* keep retained sources separate from routed derivatives;
* and preserve provenance from every routed page back to the retained source.

The canonical source location remains conceptually:

```text
scans/source/YYYY-MM-DD/
```

Routing review remains conceptually:

```text
scans/review/
```

### 13.2 Generalize routed-evidence language

Core documentation must no longer define routed evidence only as evidence associated with:

* a class;
* an assignment;
* or a student.

The generalized relationship is:

```text
Core retained source scan
    -> source page
    -> PDS2 route locator
    -> route registration
    -> module-owned target
    -> module-owned routed evidence or reference
```

### 13.3 Shared source-page reference

Core should provide a reusable source-page provenance value object containing at least:

* `source_scan_id`;
* `source_sha256`;
* retained workspace-relative path;
* original source filename;
* source page number;
* and intake timestamp where required.

Each module stores or cites this shared value in its own evidence record.

### 13.4 Mixed-module scans

One retained source file may contain pages for:

* ScoreForm;
* Quillan;
* Concord;
* and future modules.

The source scan retains one identity.

Each routed source page receives its own route result, module record, failure, or resolution while preserving the common source-scan reference.

### 13.5 Corrections

Correcting:

* route assignment;
* Author;
* Subject;
* student relationship;
* page relationship;
* or module filing

must not modify the retained source bytes.

Corrections belong in:

* resolution metadata;
* superseding route/evidence relationships;
* module Review records;
* or other append-only historical records.

---
## 14. Routing Failure Metadata Version 2

### 14.1 Generalized identity

The shared failure schema version 2 uses route-oriented structures rather than top-level assignment/student identity.

A representative shape is:

```json
{
  "schema_version": "2",
  "failure_id": "failure_...",
  "scope": "page",
  "stage": "routing",
  "created_at": "2026-07-13T19:15:00-04:00",
  "failure_category": "route_unknown",
  "failure_message": "No route registration exists for the decoded locator.",
  "source_scan_id": "scan_...",
  "source_filename": "scanner_export.pdf",
  "source_sha256": "...",
  "retained_source_path": "scans/source/2026-07-13/...",
  "review_copy_path": null,
  "source_page_number": 2,
  "detected_payload": "PDS2|...",
  "route_locator": {
    "schema": "PDS2",
    "module_id": "concord",
    "class_id": "english10_p3",
    "work_id": "socratic_seminar_1",
    "route_id": "rt_01j2m8h8x5z2"
  },
  "target": null,
  "module_details": {}
}
```

### 14.2 Shared failure categories

The shared category set should include:

```text
source_missing
source_unreadable
source_type_unsupported
source_retention_failed

payload_missing
payload_unreadable
payload_invalid
payload_schema_unsupported
payload_too_large

identifier_invalid
module_unsupported
module_profile_incompatible

class_unknown
work_unknown
route_unknown
route_inactive
route_ambiguous
route_mismatch
route_registration_invalid
target_unknown
target_incompatible

page_conflict
processing_error
evidence_write_failed
```

### 14.3 Module-specific failures

The following remain module-specific:

* `student_unknown`;
* Artifact-specific validation failures;
* missing Artifact Subjects;
* Quillan submission completeness;
* ScoreForm mark-detection failures;
* scoring failures;
* Review readiness;
* moderation state;
* and result-export failures.

A missing or unresolved Concord Subject is not automatically a routing failure. A page may route correctly to an Artifact Page while its Authors or Subjects await Review.

### 14.4 Failure identity rules

A fully validated `RouteLocator` may be stored at the shared top level.

Unvalidated guessed values must not be promoted to authoritative identity.

When the complete locator cannot be validated:

* preserve the raw detected payload;
* record parser diagnostics;
* and place non-authoritative partial observations under structured diagnostic details.

### 14.5 Resolution metadata

Resolution records must remain separate from immutable failure records.

A routing resolution may record:

* corrected locator;
* selected route registration;
* selected module target;
* manual evidence filing;
* rescan requirement;
* duplicate dismissal;
* inability to route;
* or a deferred decision.

Re-routing must preserve:

* the original decoded payload;
* the original failure;
* the resolution decision;
* the retained source reference;
* and the final module evidence relationship.

---
## 15. ScoreForm Migration Requirements

ScoreForm must migrate from student-bearing QR payloads to route registrations.

### 15.1 Generation

Before rendering an answer-sheet page, ScoreForm must create:

1. a durable answer-sheet page record;
2. a route registration targeting that page record;
3. and the corresponding `PDS2` locator.

For a multi-page answer sheet, every physical page receives its own route ID.

### 15.2 Student relationship

The answer-sheet page record must resolve to:

* ScoreForm assignment;
* student;
* logical assessment page;
* question range;
* form/layout;
* and other ScoreForm-owned metadata.

None of this data is required in the QR.

### 15.3 Scanning

ScoreForm scanning must:

* parse PDS2 through Core;
* load the route registration;
* resolve the answer-sheet page;
* derive the expected student and assessment page;
* score the routed page;
* and preserve source provenance.

### 15.4 Storage

ScoreForm assignment data must move beneath:

```text
classes/<class_id>/modules/scoreform/work/<assignment_id>/
```

Its `assignment.json` remains ScoreForm-owned.

### 15.5 Duplicate and page handling

Because each physical page has durable identity, ScoreForm can distinguish:

* duplicate scans of the same expected page;
* separate pages for the same student;
* separate print copies;
* rescans;
* and page conflicts.

### 15.6 Legacy formats

ScoreForm must stop generating `OMR1` and `PDS1` after migration.

Legacy parsing may remain only if deliberately retained as a clearly separated legacy adapter. It must not define the normalized Core model or be enabled merely because the earlier implementation existed.

---
## 16. Quillan Migration Requirements

Quillan must migrate from student-bearing response QRs to route registrations.

### 16.1 Generation

Before rendering a response page, Quillan must create:

1. a durable response-page record;
2. a route registration targeting that page;
3. and its `PDS2` locator.

Every continuation page receives a distinct route ID.

### 16.2 Submission relationship

The response-page record resolves to:

* Quillan assignment;
* student submission;
* logical page order;
* response or document role;
* prompt or template version;
* and attempt or revision context where applicable.

### 16.3 Scanning and assembly

Quillan must:

* resolve each PDS2 page;
* derive the student submission through the page record;
* preserve source-page provenance;
* detect duplicates and conflicts;
* and assemble submissions according to Quillan-owned rules.

### 16.4 Storage

Quillan data must move beneath:

```text
classes/<class_id>/modules/quillan/work/<assignment_id>/
```

Student submission directories may remain inside that Quillan-owned root.

They must not remain the universal Core destination.

---
## 17. Concord Integration Requirements

### 17.1 Work identity

For Concord:

```text
module_id = concord
work_id = activity_id
```

The Activity is the top-level module work context for routing, academic registration, and work-scoped publication.

This does not make every Activity academic, graded, registered, or published.

### 17.2 Route target

Every evidence-bearing returned Artifact Page has:

* durable `artifact_page_id`;
* one immutable `route_id` when routing is required;
* a persisted Core Route Registration;
* and a PDS2 locator.

The normal target is:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

### 17.3 Semantic resolution

Concord resolves broader context through native records:

```text
Artifact Page
    -> Artifact Instance
    -> optional Packet Instance
    -> Activity
    -> optional Session, Group, Marker, Work Item, or Event context
    -> Authors
    -> Subjects
```

The QR does not contain this graph.

### 17.4 Required routing cases

The routing contract must support:

* peer observation with different Author and Subject;
* Group discussion map with no student Subject;
* teacher-authored multi-subject tracker;
* Group Artifact with collective or multiple Authors;
* Activity-, Session-, Work Item-, Marker-, or Event-scoped Artifact;
* unresolved attribution;
* continuation pages;
* non-returned instructional pages with no route;
* duplicate scans;
* misroute correction;
* rescans;
* and mixed-module source batches.

### 17.5 Scan Reference

A successful Concord route creates or supports a Concord Scan Reference linking:

* Artifact Page;
* Core source-scan identity;
* source-page index;
* routed derivative where applicable;
* routing, readability, filing, and review state;
* preferred-source state;
* provenance;
* and supersession history.

### 17.6 Standards integration boundary

Core owns shared standards identity and profiles.

Concord owns:

* Activity `standards_profile_id`;
* ordered `focus_standard_ids`;
* Activity scoring orientation;
* standard-backed and local Criterion classification;
* exactly one governing `standard_id` for a standard-backed Criterion;
* teacher-approved standard-backed and local Scores;
* and the standards-specific subset of the Concord manifest.

Standards identity does not belong in PDS2 or generic Route Registrations.

### 17.7 Explicit Academic Work Registration

A Concord Activity may be registered only through an explicit Core Academic Work Registration.

The registration uses:

```text
work.module_id = concord
work.class_id = Activity.class_reference.record_id
work.work_id = Activity.activity_id
```

and must include exactly one matching Activity source `ModuleRecordRef` whose `module_id` is `concord`, whose `record_kind` is `activity`, and whose `record_id` equals `work.work_id`.

Additional source records may be included when justified.

The initial Concord work kind is conceptually:

```text
collaborative_activity
```

The registration’s Core `academic_intent` remains distinct from Concord `scoring_orientation`.

None of the following creates registration automatically:

* Activity creation;
* standards configuration;
* Score creation;
* page generation;
* route creation;
* or manifest generation.

### 17.8 Concord Academic Result Manifest

Concord owns an immutable, revision-addressable Academic Result Manifest for selected results from one registered Activity.

The manifest must expose enough information to interpret included results, including:

* manifest contract version;
* record-set identity and revision;
* `ModuleWorkRef`;
* source Activity reference;
* generation time and provenance;
* Activity scoring context;
* exact Criterion projections;
* exact Scoring Scale projections;
* standard-backed and local Score projections;
* non-score dispositions;
* native Score supersession;
* Score Evidence Link or equivalent lineage projections;
* minimum required Moderation state;
* and a direct standards-result subset.

The manifest must not calculate mastery, Grades, weighting, Academic Period membership, or formal reports.

### 17.9 Standard-backed and local result publication

A single Concord manifest may include:

* standard-backed Scores;
* local Scores;
* standard-backed non-score dispositions;
* local non-score dispositions;
* and their separate Criteria and scale semantics.

Only standard-backed Scores appear in the direct standards-result subset.

A local Score may later participate in conventional or hybrid grading only through explicit Meridian policy.

### 17.10 Evidence lineage and cross-producer overlap

When a Concord Score uses ScoreForm, Quillan, or another external producer result, the manifest must preserve module-qualified source lineage.

When an exact source Core Publication Record is known, the lineage may also preserve that publication identity.

This allows Meridian to recognize that:

```text
external producer result
    -> Concord evidence use
    -> Concord teacher-approved Score
```

and apply an explicit overlap or deduplication policy.

Concord does not decide that Meridian must always use or exclude either record.

### 17.11 Manifest publication through Core

Concord publishes through Core as:

```text
publication_kind: academic_result_set
```

with truthful capabilities such as:

```text
criterion_scores
standards_ratings
moderated_scores
```

The Publication Record identifies the Activity as its optional source record and records the exact current Academic Work Registration revision at publication time.

Later Academic Work Registration revisions do not alter the registration revision preserved by an existing Publication Record.

### 17.12 Native versus publication history

These are separate:

```text
Score Record supersession
manifest record-set revision
Core Publication Record supersession
Core Publication Withdrawal
Meridian import and calculation history
```

No layer may infer one history solely from another.

### 17.13 Meridian boundary

Meridian owns:

* selection of Concord publications;
* selection of eligible Scores;
* direct standards-evidence eligibility;
* local Score use in conventional or hybrid policies;
* cross-producer overlap handling;
* scale mapping;
* repeated-observation and reassessment policy;
* Academic Period membership;
* proficiency and Grade calculation;
* overrides of derived results;
* and formal reports.

Concord must not duplicate those policies inside the manifest.

### 17.14 Academic Period boundary

Concord preserves native Activity, Session, evidence, Review, Moderation, and scoring dates.

It does not assign authoritative Academic Period membership from those dates.

The initial manifest does not require an `academic_period_id`.

Meridian uses exact Core Academic Period calendar revisions when assigning Grade items or results to periods.

---
## 18. Versioning and Package Requirements

### 18.1 Released routing baseline

The released baseline remains:

```text
pds-core 0.5.0
Python >= 3.11
QR schema: PDS2
Route Registration contract: 1
routing failure/resolution contract: 2
```

### 18.2 Post-0.5 registry architecture

Core mainline now contains newer registration, publication, catalog, and Academic Period architecture.

Until Core publishes an applicable release or explicitly stabilizes those producer-facing APIs, Concord must not:

* claim that `pds-core` 0.5 implements them;
* import unreleased APIs under a production compatibility claim;
* or widen its dependency range without coordinated verification.

### 18.3 Current Concord dependency range

For the released PDS2-only foundation, Concord may declare:

```toml
dependencies = [
    "pds-core>=0.5,<0.6"
]
```

Runtime publication implementation will require a later compatible Core range determined by the release that includes the registry contracts.

### 18.4 Contract axes

Compatibility declarations must distinguish:

* Core package version;
* PDS2 schema;
* Route Registration schema;
* routing failure and resolution schemas;
* Academic Period schema and calendar-revision contract;
* Academic Work Registration schema;
* Core Publication Record and withdrawal schemas;
* Concord Activity public contract version;
* Concord Academic Result Manifest contract version;
* and supported shared publication capabilities.

Changing one axis does not automatically change every other axis.

### 18.5 Sibling-module independence

The supported dependency direction remains:

```text
pds-scoreform -> pds-core
pds-quillan   -> pds-core
pds-concord   -> pds-core
pds-meridian  -> pds-core
```

Cross-module interpretation relies on public serialized contracts or optional adapters, not sibling private imports.

### 18.6 Python alignment

Every consuming module must declare and test a Python range compatible with its selected Core release and must resolve imports through installed dependencies rather than sibling checkout paths.

### 18.7 Explicit incompatibility

Unsupported package versions, schema versions, manifest contracts, publication kinds, capabilities, or producer adapters must fail explicitly.

A routing-compatible Concord installation may still be publication-incompatible with a particular Core or Meridian version.

---
## 19. Core Registry, Academic Period, and Meridian Compatibility

The earlier version of this document anticipated a future suite assignment registry. Core has now adopted a more precise architecture based on neutral work registration and typed manifest publication.

### 19.1 Academic Work Registration replaces inferred assignment discovery

A Core Academic Work Registration declares that an existing `ModuleWorkRef` may participate in academic grading or reporting.

It does not duplicate the complete Concord Activity and does not determine:

* Grade inclusion;
* weight;
* category;
* point value;
* standards proficiency;
* Academic Period membership;
* lateness;
* reassessment;
* mastery;
* or report audience.

### 19.2 Publication Record replaces recursive producer crawling

Meridian discovers deliberately published results through Core Publication Records.

It must not normally:

* recursively scan Concord work roots;
* infer reportable files from names;
* depend on mutable `latest.json` files;
* or import Concord private storage code.

The absence of a Core Publication Record means that Core does not consider a manifest published, even if a familiar file exists.

### 19.3 Producer manifest remains authoritative

The Concord manifest remains authoritative for the exact result projection and producer-specific meaning.

Core remains authoritative for:

* registration existence and revision;
* publication existence and identity;
* manifest path and digest binding;
* publication supersession;
* withdrawal;
* and shared discovery metadata.

The derived catalog is not authoritative for either layer.

### 19.4 Academic Period architecture

Core owns school-year-scoped hierarchical Academic Period calendars.

The complete period reference is:

```text
school_year + period_id
```

Core period types may include:

```text
marking_period
semester
quarter
trimester
progress_window
custom
```

Core does not assign Grade items or results to periods.

### 19.5 Meridian period membership

Meridian owns the policy that associates:

* registered work;
* selected publications;
* Grade items;
* evidence;
* proficiency calculations;
* Grade calculations;
* and report snapshots

with exact Core Academic Period references and calendar revisions.

Native Concord dates remain contextual evidence and chronology. They do not universally determine period membership.

### 19.6 Assessment and academic intent

Core registration `academic_intent` remains broad producer-facing metadata.

Meridian may define richer Grade-item classifications and policies without changing PDS2, the Activity record, or the Core registration envelope.

### 19.7 No cross-work producer publication in the initial contract

The initial Core publication contract scopes one Publication Record to exactly one `ModuleWorkRef`.

A Concord publication therefore represents one Activity work context.

Cross-Activity, class-wide, course-wide, or school-year aggregate publications require a later architectural decision. Meridian may aggregate several work-scoped publications under its own contracts.

### 19.8 Registry privacy boundary

Core registry records and catalog rows must remain metadata-minimized.

They must not embed:

* student result arrays;
* Score values;
* student writing;
* peer comments;
* private Review notes;
* detailed Moderation rationale;
* or full manifest bodies.

Discoverability is not authorization.

---
## 20. Security, Privacy, Integrity, and Robustness Requirements

### 20.1 Routing requirements

The implementation must:

* validate all path-bearing identifiers;
* reject separators and traversal components;
* never accept a destination path from a QR;
* never create a target solely because a QR names it;
* require a persisted Route Registration;
* confirm exact locator consistency;
* prevent route IDs from being repointed;
* retain source bytes before module processing;
* avoid direct PII in QR payloads;
* treat QR data as untrusted input;
* impose payload-length limits;
* reject duplicate and unknown fields;
* preserve failures and resolutions;
* and prevent module writes from escaping the work root.

### 20.2 Registration requirements

Academic Work Registration services must:

* require an existing producer work root for initial registration;
* preserve stable `ModuleWorkRef` identity;
* use positive service-owned revisions;
* use offset-aware timestamps;
* preserve initial `created_at` across revisions;
* prevent stale expected-revision writes;
* preserve all historical revisions;
* and reject contradictory or orphaned revision state.

### 20.3 Manifest requirements

Concord must:

* validate native records before projection;
* generate complete deterministic JSON under a versioned public contract;
* store manifests beneath the exact Activity work root;
* use exclusive revision-addressed creation;
* never rewrite published bytes;
* avoid direct PII in record-set IDs and paths;
* minimize sensitive evidence and Moderation content;
* preserve typed source lineage;
* and keep credentials and access tokens out of locators and manifests.

### 20.4 Publication requirements

Core publication must:

* validate publication kind and capabilities;
* require registration for `academic_result_set`;
* verify safe work-scoped manifest paths;
* calculate or verify exact SHA-256 digest;
* create immutable Publication Records exclusively;
* reconcile exact replay without duplication;
* reject contradictory logical-revision reuse;
* preserve one unbranched publication series;
* prevent multiple competing current heads;
* preserve immutable withdrawals;
* and treat catalog failure as derived-state failure rather than canonical publication failure.

### 20.5 Consumer requirements

Meridian must:

* verify supported publication and manifest contracts;
* preserve exact source publication identity and digest;
* refuse silent source-revision replacement;
* respect publication withdrawal for new selection;
* preserve older calculations against their original sources;
* maintain authorization boundaries;
* preserve producer-native non-score states;
* and avoid assuming that cross-producer results are independent when lineage shows a relationship.

### 20.6 Privacy requirements

Publication establishes discoverability, not authorization.

Access to a Concord Score does not imply access to:

* source scans;
* full Artifacts;
* peer observations;
* restricted Review notes;
* or detailed Moderation rationale.

Core registry metadata, Concord manifest contents, Meridian calculations, and report snapshots each require their own minimized and purpose-appropriate access rules.

---
## 21. Testing Requirements

### 21.1 PDS2 and Route Registration tests

Core and Concord tests must retain coverage for:

* canonical serialization and round trips;
* field-order independence;
* missing, duplicate, unknown, empty, unsafe, and oversized payloads;
* deterministic Route Registration lookup;
* exact locator matching;
* missing and malformed registrations;
* target mismatch;
* inactive and superseded routes;
* route-ID non-reuse;
* safe path containment;
* mixed-module dispatch;
* and source provenance.

### 21.2 Concord routing acceptance cases

Tests must demonstrate:

* peer observation with different Author and Subject;
* Group map with no student Subject;
* teacher multi-subject tracker;
* collective Group Artifact;
* Activity-, Session-, Event-, Marker-, and Work Item-scoped pages;
* unresolved attribution;
* continuation pages;
* non-returned instructional pages without routes;
* duplicate scan;
* rescan;
* misroute and correction;
* mixed-module source scan;
* and one source page producing one valid Concord Scan Reference.

### 21.3 Academic Work Registration tests

Tests must cover:

* explicit initial registration for an existing Concord Activity work root;
* no automatic registration on Activity or Score creation;
* all supported Core academic intents;
* planned, active, closed, and cancelled lifecycle;
* idempotent exact initial request where the Core service permits it;
* metadata revision under expected-current-revision protection;
* stale revision conflict;
* identity mutation rejection;
* duplicate source-reference rejection;
* source-record module mismatch;
* and preservation of registration history.

### 21.4 Manifest contract tests

Concord tests must cover:

* standard-backed-only manifest;
* mixed standard-backed and local manifest;
* local-criteria-only manifest;
* explicit non-score dispositions without `value`;
* exact Criterion and Scoring Scale projections;
* Group and individual target preservation;
* native Score supersession;
* active versus historical Score state;
* professional judgment without one controlling Artifact;
* evidence lineage to Concord sources;
* evidence lineage to ScoreForm and Quillan;
* optional exact source Publication Record identity;
* required Moderation projection;
* qualified Moderation;
* rejected evidence excluded from active support;
* privacy minimization;
* deterministic serialization;
* and invalid manifest rejection.

### 21.5 Manifest storage tests

Tests must cover:

* safe work-scoped path;
* exclusive revision creation;
* immutable published bytes;
* absent or mutable convenience path not used for publication;
* path traversal rejection;
* path outside work root rejection;
* non-JSON path rejection;
* and record-set ID free of direct PII.

### 21.6 Publication Record tests

Core and integration tests must cover:

* first `academic_result_set` publication;
* required registration revision;
* truthful capability validation;
* exact SHA-256 binding;
* exact replay idempotency;
* contradictory revision reuse conflict;
* later manifest publication superseding the current head;
* wrong predecessor rejection;
* branch and cycle rejection;
* publication withdrawal;
* withdrawal before publication rejection;
* replay never restoring a withdrawal;
* catalog rebuild from canonical records;
* missing or corrupt catalog not invalidating canonical records;
* and catalog update failure reported as partial success.

### 21.7 Meridian compatibility fixtures

Cross-repository fixtures should demonstrate:

* Meridian discovering a Concord publication by kind and capability;
* preserving publication ID and digest;
* importing a supported manifest revision;
* rejecting an unsupported manifest contract;
* keeping standard-backed and local Scores distinct;
* preserving non-score dispositions;
* mapping exact scales only under explicit policy;
* selecting repeated standards observations under explicit policy;
* assigning results to exact Core Academic Period references;
* recognizing a Concord Score derived from a ScoreForm or Quillan source;
* applying an explicit overlap policy;
* recalculating without mutating Concord;
* preserving a prior calculation against an older publication;
* and creating a report snapshot with exact source provenance.

### 21.8 End-to-end release gate

Before claiming integrated release readiness, coordinated versions must pass:

* all applicable Core routing tests;
* all Core registry and Academic Period tests;
* Concord routing and native-domain tests;
* Concord manifest contract tests;
* Core publication integration tests;
* Meridian producer-consumption fixtures;
* one mixed-module scan test;
* one cross-producer evidence-lineage test;
* clean installation in the declared Python environment;
* and command-line smoke tests without sibling checkout assumptions.

---
## 22. Explicit Non-Goals

This integration does not:

* make Core understand Concord Authors, Subjects, Review, Moderation, Criteria, Scores, or evidence meaning;
* make Concord a Gradebook or formal reporting module;
* make Meridian authoritative for Concord-native Scores;
* make a Route Registration an Academic Work Registration;
* make an Academic Work Registration a Grade item;
* make a Publication Record a Grade or report;
* make publication imply Grade inclusion;
* infer Academic Period membership from native dates;
* define one universal producer result schema;
* normalize all Scoring Scales in Core;
* make local Scores direct standards ratings;
* make Group Scores individual Scores;
* convert non-score dispositions into zero;
* publish raw source scans or full evidence through the Core registry;
* implement institution-wide authorization;
* define a universal grading formula;
* define one universal four-level proficiency scale;
* prescribe Meridian evidence-selection or reassessment policy;
* define cross-Activity producer manifests in the initial contract;
* add standards, Grades, Academic Periods, or report metadata to PDS2;
* require Concord to import Meridian;
* or require Meridian to import Concord private code.

---
## 23. Implementation Status and Remaining Work

### 23.1 Released Core PDS2 foundation

Core 0.5 provides:

1. PDS2 parsing and serialization.
2. `ModuleWorkRef`, `RouteLocator`, `ModuleRecordRef`, `RouteRegistration`, and route resolution.
3. route-ID generation and validation.
4. module-qualified work-path helpers.
5. deterministic Route Registration storage and validation.
6. module-profile registration and generic page dispatch.
7. routing failure and resolution schema version 2.
8. source-scan retention and provenance.
9. shared standards libraries, profiles, identifiers, and validation.
10. package and contract boundaries suitable for independently installed modules.

### 23.2 Core post-0.5 mainline architecture

Core mainline contains substantial implementation for:

1. revisioned Academic Period calendars and exact references;
2. revisioned Academic Work Registrations;
3. producer-facing registration services;
4. immutable Publication Records;
5. publication supersession and withdrawal;
6. producer-facing publication services and digest calculation;
7. canonical registry retrieval;
8. and a disposable SQLite discovery catalog.

These capabilities require release/version confirmation before Concord claims runtime support.

### 23.3 Completed Concord architecture work

Concord has now established:

* ADR 0015;
* the Concord Academic Result Manifest conceptual contract;
* Core Academic Work Registration and Publication Record relationships;
* standard-backed and local result publication semantics;
* cross-producer evidence lineage;
* manifest and publication revision distinctions;
* withdrawal semantics;
* and Meridian ownership boundaries.

### 23.4 Remaining Concord documentation work

Concord must still reconcile:

* cross-case requirements;
* the high-level conceptual design;
* cross-references in ADRs 0008 and 0014;
* representative-example notation;
* seminar, laboratory, and project examples;
* and cross-example validation.

### 23.5 Remaining Concord implementation work

Later implementation issues must:

1. declare the released Core range supporting the required registry APIs;
2. register the Concord routing profile;
3. create Artifact Pages before rendering;
4. create PDS2 Route Registrations;
5. create Scan References after successful dispatch;
6. implement explicit Academic Work Registration workflows;
7. define and version the serialized Concord Academic Result Manifest;
8. implement deterministic manifest generation and validation;
9. implement immutable revision-addressed manifest storage;
10. publish through Core’s producer-facing services;
11. display publication, supersession, withdrawal, and partial-success states;
12. expose producer publication compatibility metadata;
13. test Meridian-compatible fixtures;
14. and preserve all native/publication/consumer histories independently.

### 23.6 Meridian implementation dependency

Meridian remains in early architecture and documentation development.

Concord must not freeze unsupported assumptions about:

* final Meridian policy schemas;
* final producer adapter APIs;
* exact Grade-item contracts;
* or report snapshot serialization.

The Concord manifest should expose faithful native meaning and the information already required by accepted Core and Meridian architecture while leaving policy decisions to Meridian.

---
## 24. Architectural Acceptance Criteria

The reconciled integration architecture is satisfied when all applicable conditions hold.

### Routing and source evidence

1. PDS2 remains the active generated QR format.
2. Every expected returned page has durable route identity and a persisted Route Registration.
3. The PDS2 QR contains only module, class, work, and route identity.
4. Authors, Subjects, Groups, templates, Criteria, standards, and Score targets resolve from module records.
5. Route Registrations are found deterministically.
6. Route IDs are immutable and never silently repointed.
7. Module work roots are qualified by module.
8. Concord can route pages with no student Subject.
9. Multi-subject and unresolved-attribution pages route correctly.
10. Retained source scans remain canonical and every routed page remains traceable to source identity and source page.

### Registration and publication

11. A Concord Activity is not automatically registered as academic work.
12. Explicit Academic Work Registration uses `concord + class_id + activity_id`.
13. Registration preserves revision history and does not create a Grade item or Academic Period membership.
14. Concord defines a versioned public Academic Result Manifest.
15. Published manifests are immutable, revision-addressed, and beneath the exact Activity work root.
16. Standard-backed and local Scores remain separately classified.
17. Non-score dispositions remain explicit and omit `value`.
18. Exact Criterion and Scoring Scale revisions remain reproducible.
19. Cross-producer evidence lineage remains visible.
20. Required Moderation state is sufficient to validate consequential evidence use.
21. Core publishes the manifest as `academic_result_set` with truthful capabilities.
22. Core binds exact bytes by SHA-256 and safe path.
23. Exact replay is idempotent; contradictory revision reuse fails.
24. Native Score supersession, manifest revision, Publication Record supersession, and withdrawal remain distinct.
25. The catalog remains derived and nonauthoritative.

### Meridian boundary

26. Meridian can discover and import exact Concord publications without crawling work directories or importing Concord private code.
27. Publication does not imply Grade-item membership or standards-evidence selection.
28. Meridian preserves standard-backed versus local semantics.
29. Meridian preserves Group versus individual targets.
30. Meridian does not convert non-score dispositions into zero without explicit policy.
31. Meridian recognizes cross-producer lineage and applies explicit overlap policy.
32. Meridian uses exact Core Academic Period references and calendar revisions.
33. Meridian calculations, overrides, and reports do not mutate Concord or Core records.
34. Historical Meridian calculations and report snapshots retain their exact source publication identities and policy provenance.

### Compatibility and release

35. Routing compatibility and publication compatibility are declared separately.
36. Every module declares compatible Core and Python versions.
37. Unsupported schema, manifest, capability, or adapter versions fail explicitly.
38. Concord does not claim runtime registry support against unreleased Core APIs.
39. Cross-repository fixtures validate Concord publication and Meridian consumption.
40. No standard, Criterion, Score, Grade, Academic Period, or report semantics are placed in PDS2 or generic Route Registration metadata.

---
## 25. Final Architectural Rule

The shared physical-page routing model is:

```text
PDS2 QR
    -> Core RouteLocator
    -> persisted Core RouteRegistration
    -> typed module-owned page target
    -> module-owned semantic records
    -> module-owned evidence workflow
```

It is not:

```text
QR
    -> student
    -> universal student submission directory
```

The shared academic-registration and publication model is:

```text
Concord Activity as ModuleWorkRef
    -> explicit Core Academic Work Registration
    -> Concord canonical results
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> Core discovery
```

It is not:

```text
Activity or Score exists
    -> automatically graded or published
```

The grading and reporting model is:

```text
Core Publication Record
    -> exact Concord manifest import
    -> Meridian policy
    -> selected evidence
    -> proficiency or Grade
    -> formal report snapshot
```

It is not:

```text
Core or Concord publication
    -> inferred mastery, Grade, Academic Period, or report
```

The final boundary is:

> Routing locates the physical page. Concord owns the contextual evidence and teacher judgment. Core registers work and publishes exact producer projections. Meridian owns grading and reporting policy.
