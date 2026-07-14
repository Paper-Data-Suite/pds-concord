# PDS Core Integration Requirements

**Status:** Proposed integration specification
**Project:** Paper Data Suite
**Module:** `pds-concord`
**Issue:** `Paper-Data-Suite/pds-concord#10`
**Date:** July 13, 2026

## 1. Purpose

This document specifies the changes required in `pds-core` to make `pds-concord` a first-class Paper Data Suite module while establishing a QR, routing, identity, workspace, scan-provenance, and package contract suitable for all Paper Data Suite modules that generate and receive paper pages.

This specification addresses the current Core assumptions that:

* every routed page belongs to one student;
* every routed page belongs to one assignment identified by an unqualified `assignment_id`;
* every QR payload must contain `student_id`;
* every successful route terminates in a student submission directory;
* and every module can safely share one assignment directory and one `assignment.json`.

Those assumptions describe the initial ScoreForm and Quillan workflows but cannot represent Concord accurately.

Concord must support pages associated with:

* one student;
* several students;
* one Group;
* several Groups;
* one Session;
* one Activity;
* one Artifact Instance;
* one Artifact Page;
* one Activity Event;
* a teacher-authored multi-subject tracker;
* an unresolved Author or Subject;
* or another Concord-owned contextual record.

The new Core contract must support these cases without:

* creating synthetic students;
* placing Group, Session, Activity, Artifact, or other identifiers into `student_id`;
* treating a route target as an Artifact Author or Artifact Subject;
* encoding an Artifact’s complete Author or Subject graph in its QR code;
* duplicating Concord’s domain model in Core;
* or requiring direct dependencies among sibling modules.

This is an integration-requirements document. It defines the required architecture and contract semantics. It does not prescribe every internal class name, storage implementation, command-line interface, or graphical workflow.

---

## 2. Governing Design Sources

This specification must remain consistent with the accepted Concord Architecture Decision Records and the Concord conceptual domain model.

The most directly relevant decisions are:

* `docs/decisions/0001-concord-module-boundaries.md`;
* `docs/decisions/0002-paper-first-human-reviewed-evidence.md`;
* `docs/decisions/0005-separate-artifact-authors-and-subjects.md`;
* `docs/decisions/0007-preserve-source-evidence-and-history.md`;
* `docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`;
* `docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`;
* `docs/decisions/0010-exceptional-evidence-states-are-not-low-scores.md`;
* `docs/decisions/0012-link-scoreform-and-quillan-without-duplication.md`;
* and `docs/decisions/0013-keep-activity-specific-structures-optional.md`.

The relevant existing Core contracts and implementations include:

* `pds-core/docs/qr_payload_and_routing_contract.md`;
* `pds-core/docs/active_scan_contract.md`;
* `pds_core.qr_payload`;
* `pds_core.pds1`;
* `pds_core.routes`;
* `pds_core.scan_routes`;
* `pds_core.scan_failure_metadata`;
* and `pds_core.scan_resolution_metadata`.

When this specification conflicts with the current pre-production Core QR or route implementation, this specification describes the required replacement. When it conflicts with an accepted Concord ADR, the ADR governs unless a later ADR explicitly supersedes it.

---

## 3. Decision Summary

The integration should adopt the following architecture:

1. Replace the current student-oriented `PDS1` contract with a new `PDS2` page-locator contract.
2. Give every scannable returned page a durable, module-owned route identity before the page is generated.
3. Encode only a compact route locator in the QR code.
4. Resolve student, Group, Author, Subject, document, template, attempt, and other semantic context from a persisted route registration and module-owned records.
5. Define a neutral module work reference consisting of:

   * owning module;
   * Core class;
   * and module-owned work identifier.
6. Store module work beneath module-qualified class paths.
7. Persist route registrations at deterministic Core-defined locations so routing does not require recursive directory discovery.
8. Use a Core module-profile registry for module recognition and dispatch without hard-coding sibling-module imports into Core.
9. Replace student-specific normalized route and failure models with generic route-locator and typed-target models.
10. Preserve the existing Core source-scan retention, immutability, provenance, and append-only resolution principles.
11. Migrate ScoreForm and Quillan deliberately to the new contract rather than preserving the student-oriented route as the universal model.
12. Use explicit, compatible package versions across Core, ScoreForm, Quillan, and Concord.

The core principle is:

> A QR code identifies an expected physical page route. It does not identify the page’s Author, Subject, scorer, score target, or student submission.

---

## 4. Current Contract Defects

### 4.1 Student identity is universally required

The current normalized `QrPayload` requires:

* `schema`;
* `module`;
* `class_id`;
* `assignment_id`;
* `student_id`;
* `page`;
* and optional metadata.

The current `PDS1` parser similarly requires:

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

The current route layout uses:

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

The current shared `assignment.json` also creates an ownership collision because each module has a different assignment or activity schema.

### 4.3 The route destination is student-specific

The current universal route terminates in:

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

The current payload can carry student, page number, document type, template, form, attempt, and similar values.

Encoding semantic context in the QR creates several risks:

* the printed metadata may disagree with the authoritative module record;
* later attribution corrections cannot change the paper QR;
* duplicated values require conflict-resolution rules;
* the payload grows as workflows become more complex;
* and future modules may add incompatible optional fields.

The QR should contain a stable locator. The authoritative semantic record should remain outside the QR.

### 4.5 Failure metadata assumes assignment and student resolution

The current shared failure schema contains top-level:

* `class_id`;
* `assignment_id`;
* and `student_id`.

The shared categories include:

* `assignment_unknown`;
* and `student_unknown`.

These fields and categories cannot serve as the universal route model for non-student pages.

### 4.6 Package relationships are implicit

ScoreForm and Quillan import Core code but do not declare a released, versioned `pds-core` runtime dependency.

Quillan additionally relies on a sibling-repository `mypy_path`.

A coordinated breaking contract requires explicit dependency declarations and compatible supported Python versions.

---

## 5. Ownership Boundaries

### 5.1 Core ownership

`pds-core` must own:

* workspace-root resolution;
* canonical class identity;
* roster and student identity;
* identifier validation;
* module-qualified work references;
* the shared QR grammar;
* QR parsing and serialization;
* generic route-locator models;
* generic typed module-record references;
* route-registration schema and deterministic route-registration paths;
* module-profile registration and dispatch interfaces;
* safe module work-root construction;
* active source-scan retention;
* source-scan identity and provenance value objects;
* shared routing-failure metadata;
* shared routing-resolution metadata;
* and shared contract-version information.

### 5.2 Module ownership

Each module must own:

* the meaning of its work records;
* its assignment, Activity, or equivalent configuration;
* generation of module-specific page records;
* the semantic target represented by a route registration;
* Author and Subject relationships;
* student relationships where applicable;
* module-specific route validation;
* module-specific evidence filing;
* review, scoring, feedback, and result behavior;
* and module-specific failure details.

### 5.3 Core must not own Concord semantics

Core must not define or interpret:

* Activity;
* Session;
* Group;
* Group Membership;
* Role Assignment;
* Responsibility Assignment;
* Packet Instance;
* Artifact Instance;
* Artifact Page semantics beyond generic route identity;
* Artifact Author;
* Artifact Subject;
* Artifact Review;
* Moderation Record;
* Concord Criterion;
* Concord Score;
* or Score Evidence Link.

Core may carry a typed reference to one of these records without understanding its domain meaning.

### 5.4 No mandatory sibling dependencies

The intended dependency direction is:

```text
pds-scoreform -> pds-core
pds-quillan   -> pds-core
pds-concord   -> pds-core
```

The following must not be required:

```text
pds-concord -> pds-scoreform
pds-concord -> pds-quillan
pds-scoreform -> pds-concord
pds-quillan -> pds-concord
```

Cross-module relationships must use:

* module-qualified references;
* public serialized contracts;
* Core-owned shared value objects;
* module-owned exports;
* or optional adapters.

---

## 6. Shared Identity Model

### 6.1 Module identifier

Every module participating in Core routing must have one stable `module_id`.

Initial values include:

```text
scoreform
quillan
concord
```

A `module_id` is:

* a durable machine identifier;
* not a package import path;
* not a display label;
* and not inferred from a directory name.

Module identifiers should be lowercase and must satisfy the Core safe-identifier contract.

### 6.2 Module work reference

Core must introduce a neutral module work reference.

Conceptually:

```text
ModuleWorkRef
├── module_id
├── class_id
└── work_id
```

The effective identity of one module work unit is:

```text
module_id + class_id + work_id
```

A bare `work_id` is not globally meaningful.

`work_id` is a routing and storage term. It does not assert that every work unit is:

* a graded assignment;
* an assessment;
* student work;
* or one entry in a future gradebook.

Module mappings are:

| Module        | Meaning of `work_id`                                |
| ------------- | --------------------------------------------------- |
| ScoreForm     | `assignment_id`                                     |
| Quillan       | `assignment_id`                                     |
| Concord       | `activity_id`                                       |
| Future module | Its durable top-level routable work-unit identifier |

For Concord, using `activity_id` as `work_id` for route context does not collapse a Concord Activity into a future suite-level graded assignment. A future assignment registry may link one graded assignment to zero, one, or several module work references.

### 6.3 Route identifier

Every scannable returned page must receive one durable `route_id` before the page is rendered.

A `route_id` must be:

* collision-resistant;
* non-empty;
* path-safe and QR-safe;
* immutable after printing;
* non-semantic;
* unique within its `ModuleWorkRef`;
* and never reused for a different target.

Core should provide a shared route-ID generator.

The generated identifier should not contain:

* student identity;
* Group identity;
* names;
* grading categories;
* marking periods;
* page numbers;
* or mutable status.

A short prefix such as `rt_` may be used for diagnostics, but the identifier’s meaning must not depend on that prefix.

### 6.4 Module record reference

Core must define a generic typed reference for module-owned records.

Conceptually:

```text
ModuleRecordRef
├── module_id
├── record_kind
├── record_id
└── contract_version
```

Examples include:

```text
module_id: concord
record_kind: artifact_page
record_id: artifact_page_...
```

```text
module_id: scoreform
record_kind: answer_sheet_page
record_id: answer_sheet_page_...
```

```text
module_id: quillan
record_kind: response_page
record_id: response_page_...
```

Core validates the reference shape but does not interpret `record_kind`.

### 6.5 Distinct identities

The following identities must remain separate:

```text
route locator
module work reference
module record target
Artifact Author
Artifact Subject
student submission
evidence reference
score target
```

They may sometimes refer to related records, but none may be inferred universally from another.

---

## 7. PDS2 QR Contract

### 7.1 New schema identifier

The revised QR contract must use a new schema identifier:

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

Every `PDS2` payload contains exactly these four fields:

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

The parser must enforce:

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

The canonical serializer must emit:

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

Core must enforce an absolute serialized payload limit.

The initial maximum should be no more than:

```text
256 ASCII bytes
```

Generators should warn or fail earlier when identifiers produce a payload above a recommended operational target of:

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

## 9. Deterministic Workspace Layout

### 9.1 Required module-qualified root

Core must replace the unqualified shared assignment root with a module-qualified work root.

The preferred layout is:

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

The effective work-root identity is therefore visible in the path:

```text
classes/<class_id>/modules/<module_id>/work/<work_id>/
```

### 9.2 Route registration location

Core must define a deterministic helper for locating a route registration from a `RouteLocator`.

A conceptual layout is:

```text
classes/
  <class_id>/
    modules/
      <module_id>/
        work/
          <work_id>/
            routes/
              <route_id>.json
```

Callers must use Core route helpers rather than constructing this path manually.

Core may later introduce transparent sharding if a large route directory creates filesystem concerns. The public path API must insulate modules from that implementation detail.

### 9.3 Module-owned contents

Below the module work root, each module owns its internal layout.

Examples follow.

#### ScoreForm

```text
classes/<class_id>/modules/scoreform/work/<assignment_id>/
  assignment.json
  routes/
  pages/
  templates/
  scans/
  results/
  debug/
```

#### Quillan

```text
classes/<class_id>/modules/quillan/work/<assignment_id>/
  assignment.json
  routes/
  pages/
  templates/
  submissions/
  reviews/
  feedback/
```

#### Concord

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
```

These examples do not establish the final module-specific layouts. They demonstrate that Core owns the safe module work root while each module owns its schema beneath it.

### 9.4 Core path APIs

Core should provide helpers conceptually equivalent to:

```python
classes_dir(root)
class_dir(root, class_id)
class_roster_path(root, class_id)
class_metadata_path(root, class_id)

class_modules_dir(root, class_id)
class_module_dir(root, class_id, module_id)
module_work_collection_dir(root, class_id, module_id)
module_work_dir(root, class_id, module_id, work_id)

module_routes_dir(root, class_id, module_id, work_id)
route_registration_path(root, locator)
```

Core should also provide a safe module-owned descendant helper that:

* requires a validated module work root;
* rejects absolute paths;
* rejects `..`;
* prevents escape from the work root;
* and does not imply semantic ownership of the resulting path.

### 9.5 Existing assignment helpers

The current universal helpers such as:

```python
assignment_dir(...)
assignment_config_path(...)
assignment_submissions_dir(...)
student_submission_dir(...)
```

must no longer define the universal Core route model.

Migration options include:

* removing them during the coordinated breaking release;
* retaining them temporarily as deprecated wrappers for one documented module profile;
* or moving student-submission helpers into Quillan and ScoreForm.

No retained compatibility helper may cause Concord or future modules to adopt student-submission semantics.

---

## 10. Normalized Core Models

Core should replace the current student-required `QrPayload` with explicit models separating locator, registration, target, and resolution.

Representative conceptual models follow.

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
    created_at: str
    status: str
    human_fallback: str
    module_details: Mapping[str, JsonValue]
```

```python
@dataclass(frozen=True, slots=True)
class RouteResolution:
    locator: RouteLocator
    registration: RouteRegistration
    class_root: Path
    module_root: Path
    work_root: Path
```

A shared `RouteResolution` must not universally contain:

* `student_id`;
* `submission_dir`;
* Artifact Subjects;
* or a scoring target.

A module may derive those values after it receives the resolution.

---

## 11. Module Profiles and Dispatch

### 11.1 Requirement

Core must recognize installed PDS modules without importing their private implementations or maintaining a permanently closed module allow-list.

Core should define a public module-profile interface.

A profile should provide at least:

* stable `module_id`;
* supported Core contract range;
* supported route-registration contract range;
* route-registration validation hook where required;
* module work-root conventions;
* and module route-handling or dispatch integration.

### 11.2 Registration mechanisms

The implementation may support one or more of:

* explicit application registration;
* Python package entry points;
* a workspace module registry;
* or another documented discovery mechanism.

The selected mechanism must ensure that:

* Core does not depend on Concord, ScoreForm, or Quillan;
* modules can be installed independently;
* unsupported modules fail explicitly;
* mixed-module scans can be dispatched;
* and module identity is not accepted merely because an arbitrary string appears in a QR.

### 11.3 Core validation versus module validation

Core validates:

* PDS2 grammar;
* shared identifiers;
* payload length;
* deterministic route-registration path;
* exact locator match;
* route-registration schema;
* target-reference structure;
* and module-profile availability.

The module validates:

* target existence;
* target type;
* target lifecycle;
* expected page state;
* assignment or Activity semantics;
* student or Group relationships;
* document completeness;
* and module-specific evidence-writing rules.

### 11.4 Exact-match requirement

A route registration loaded from disk must match every locator field in the QR:

* schema;
* module;
* class;
* work;
* and route ID.

A registration found at the expected path but containing mismatched identity is a route-integrity failure, not a successful route.

---

## 12. Routing Workflow

The standard successful workflow should be:

1. The module creates its assignment, Activity, or equivalent work record.
2. The module creates one durable page record for each expected returned page.
3. The module creates and persists a Core route registration for each page.
4. The module renders the canonical `PDS2` QR from the route locator.
5. The page is printed and used.
6. A source file is selected for intake.
7. Core retains an immutable source copy before module-specific processing.
8. The scan processor extracts one source page and decodes its QR.
9. Core parses and validates the `PDS2` locator.
10. Core resolves the module profile.
11. Core calculates the deterministic route-registration path.
12. Core loads and validates the route registration.
13. Core confirms exact locator consistency.
14. The owning module receives:

    * the resolved route;
    * a Core source-scan reference;
    * source page number;
    * and processing context.
15. The module resolves the target page record and writes or links its routed evidence.
16. The module records provenance from its evidence back to the Core-retained source.
17. Review, moderation, scoring, or feedback occurs under module rules.

At no point does Core infer an Author or Subject from the route locator.

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

The shared failure schema must replace top-level assignment/student identity with route-oriented structures.

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

For Concord routing:

```text
work_id = activity_id
```

This identifies the Concord Activity as the top-level module work context.

An optional future suite assignment reference remains separate.

### 17.2 Route target

Every evidence-bearing returned Artifact Page must have:

* durable `artifact_page_id`;
* durable route registration;
* and PDS2 locator.

The route registration should normally target:

```text
module_id: concord
record_kind: artifact_page
record_id: <artifact_page_id>
```

The `route_id` may equal the `artifact_page_id` if the implementation deliberately adopts that identity rule, but Core must not require all modules to use their domain page ID as the route ID.

### 17.3 Semantic resolution

After resolving the Artifact Page, Concord obtains its broader context through Concord records:

```text
Artifact Page
    -> Artifact Instance
    -> Packet Instance where applicable
    -> Activity
    -> Session or Group context where applicable
    -> Authors
    -> Subjects
```

The QR does not contain this graph.

### 17.4 Required supported cases

The contract must support:

#### Peer observation

```text
route target: Artifact Page
Author: student observer
Subject: observed student
Context: Group and Session
```

#### Discussion map

```text
route target: Artifact Page
Author: mapper, several mappers, teacher, or unresolved
Subjects: Group and Session
student Subject: not required
```

#### Teacher tracker

```text
route target: one Artifact Page
Author: teacher
Subjects: several students, one or several Groups, or both
```

The tracker remains one Artifact. Its source page must not be duplicated into fabricated student routes.

#### Group Artifact

```text
route target: Artifact Page
Authors: collective Group, recorder, named contributors, or unresolved
Subjects: Group and Session
```

#### Activity-, Session-, or Event-scoped Artifact

```text
route target: Artifact Page
student Subject: not required
```

#### Unresolved attribution

A generated or scanned page may route successfully even when:

* its Author is unresolved;
* its Subjects are unresolved;
* attribution requires Review;
* or the physical recorder differs from the intended Author.

### 17.5 Scan Reference

A successful Concord route must create or support creation of a Concord Scan Reference linking:

* `artifact_page_id`;
* Core source-scan identity;
* source page number;
* routed derivative where applicable;
* routing state;
* readability state;
* filing state;
* and supersession history.

---

## 18. Versioning and Package Requirements

### 18.1 Core release

The PDS2 and module-qualified route redesign is a breaking Core contract.

Because `pds-core` is currently pre-1.0, the coordinated release should use at least:

```text
pds-core 0.2.0
```

### 18.2 Explicit dependencies

Each consuming module must declare a compatible Core dependency.

For the initial coordinated release:

```toml
dependencies = [
    "pds-core>=0.2,<0.3"
]
```

The exact installation source may be a local package, private index, or released distribution, but dependency compatibility must be machine-verifiable.

### 18.3 Python version alignment

All four repositories should align on:

```text
Python >= 3.11
```

ScoreForm must update its declared minimum from Python 3.10 if it depends on a Core release requiring Python 3.11.

### 18.4 No sibling-checkout type path

Quillan must remove:

```toml
mypy_path = "../pds-core"
```

Type checking and runtime imports must resolve through the declared package dependency.

### 18.5 Contract compatibility

Module profiles must declare the supported ranges of:

* Core package version;
* QR schema;
* route-registration schema;
* and any public module-record contract used by optional adapters.

Incompatibility must fail explicitly rather than being ignored.

---

## 19. Future Suite Assignment Registry Compatibility

A future grading and reporting module will require efficient discovery of assignments and other reportable work without recursively traversing every module’s directory tree.

This integration must therefore support, but not implement fully, a future suite assignment registry.

### 19.1 Registry identity

The future registry should reference module work through:

```text
module_id + class_id + work_id
```

That identity is already established by `ModuleWorkRef`.

### 19.2 Registry versus module authority

The registry may contain shared discovery metadata such as:

* title;
* owning module;
* class;
* academic periods;
* assessment classification;
* status;
* canonical module record;
* dates;
* and reporting eligibility.

The owning module must remain authoritative for its complete assignment, Activity, or work definition.

### 19.3 Academic periods

The future registry must be capable of relating work to configurable institutional periods such as:

* school years;
* semesters;
* trimesters;
* quarters;
* marking periods;
* terms;
* blocks;
* modules;
* summer sessions;
* midterm examination periods;
* final examination periods;
* and locally defined divisions.

Academic-period identity must not be encoded in PDS2 QR payloads.

### 19.4 Assessment classification

Assessment classification must remain separate from academic-period placement.

Examples include:

* practice;
* homework;
* quiz;
* test;
* unit exam;
* benchmark;
* diagnostic;
* midterm exam;
* final exam;
* project;
* laboratory;
* presentation;
* seminar;
* and writing assignment.

These classifications do not belong in the QR.

### 19.5 Non-goal for this issue

This issue does not define:

* the final assignment-registry schema;
* academic-period schemas;
* category or assignment weights;
* grade aggregation;
* dropped-score rules;
* exemptions;
* report-card calculation;
* or transcript reporting.

It requires only that the new Core identity and path architecture not obstruct that future work.

---

## 20. Security, Privacy, and Robustness Requirements

The implementation must:

* validate all path-bearing identifiers before path construction;
* reject path separators and traversal components;
* never accept a destination path from the QR;
* never create a target record solely because a QR names it;
* require a persisted route registration;
* confirm exact locator consistency;
* prevent route IDs from being silently repointed;
* retain the source before module processing;
* avoid student names and unnecessary personal information in QR payloads;
* treat QR data as untrusted input;
* impose payload-length limits;
* reject duplicate and unknown fields;
* preserve failures and resolutions;
* and prevent module-owned writes from escaping the module work root.

A QR checksum or cryptographic signature is not required initially.

QR error correction already addresses ordinary scan corruption, while route-registration validation addresses semantic integrity. A future signed-payload schema may be introduced if a concrete threat model requires it.

---

## 21. Testing Requirements

### 21.1 Core parser tests

Core tests must cover:

* canonical PDS2 serialization;
* field-order independence;
* missing fields;
* duplicate fields;
* unknown fields;
* empty keys;
* empty values;
* unsafe identifiers;
* oversized payloads;
* unsupported schemas;
* and exact round trips.

### 21.2 Route-registration tests

Tests must cover:

* registration creation before rendering;
* deterministic lookup;
* exact locator matching;
* missing registration;
* malformed registration;
* target mismatch;
* inactive route;
* superseded route;
* route-ID non-reuse;
* and safe path containment.

### 21.3 Module-profile tests

Tests must cover:

* ScoreForm profile discovery;
* Quillan profile discovery;
* Concord profile discovery;
* unsupported module;
* incompatible profile;
* and mixed-module dispatch.

### 21.4 ScoreForm acceptance cases

Tests must demonstrate:

* one-page student answer sheet;
* multi-page answer sheet;
* unique route per physical page;
* student resolved from the page record;
* duplicate scan;
* page conflict;
* same `work_id` existing in another module without collision;
* source provenance;
* and result generation after PDS2 routing.

### 21.5 Quillan acceptance cases

Tests must demonstrate:

* first response page;
* continuation page;
* student submission resolution;
* page-order assembly;
* duplicate page;
* missing page;
* same `work_id` existing in another module;
* source provenance;
* and review workflow after PDS2 routing.

### 21.6 Concord acceptance cases

Tests must demonstrate:

* peer observation with different Author and Subject;
* Group-scoped discussion map with no student Subject;
* teacher-authored multi-subject tracker;
* Group Artifact with collective or multiple Authors;
* Session-scoped Artifact;
* Activity-scoped Artifact;
* Activity Event Artifact;
* Artifact with unresolved Subjects;
* Artifact continuation pages;
* one mixed source scan containing pages from several modules;
* corrected routing without source modification;
* and one source page producing one Concord Scan Reference to an Artifact Page.

### 21.7 Cross-module collision tests

The following must coexist safely:

```text
scoreform / english10_p3 / project_check
quillan   / english10_p3 / project_check
concord   / english10_p3 / project_check
```

Each must have:

* a distinct module work root;
* distinct configuration;
* distinct route registrations;
* and no shared unqualified `assignment.json`.

### 21.8 End-to-end release gate

Before the next school year, the coordinated versions must pass:

* all Core tests;
* all ScoreForm tests;
* all Quillan tests;
* all Concord integration tests;
* one mixed-module scan test;
* package installation in a clean Python 3.11 environment;
* and command-line smoke tests without sibling repository path assumptions.

---

## 22. Explicit Non-Goals

This integration does not:

* implement the full Concord domain model;
* implement Concord Review, Moderation, or Scoring;
* make Core understand Artifact Authors or Subjects;
* define a universal gradebook;
* define the final assignment registry;
* define academic-period calculation;
* define assessment weighting;
* add OCR or handwriting interpretation;
* automate collaborative-performance judgment;
* make Group evidence produce individual scores automatically;
* define external cloud-document storage;
* replace module-owned assignment or Activity schemas;
* or require all PDS modules to use identical internal storage beneath their work roots.

---

## 23. Required Implementation Issues

Acceptance of this document should produce separate implementation issues.

### 23.1 `pds-core`

1. Record an ADR for PDS2 page-locator routing.
2. Add `ModuleWorkRef`, `RouteLocator`, `ModuleRecordRef`, `RouteRegistration`, and `RouteResolution`.
3. Implement strict PDS2 parsing and serialization.
4. Add route-ID generation.
5. Add module-qualified class/work path helpers.
6. Add deterministic route-registration storage and validation.
7. Add module-profile registration and dispatch.
8. Replace routing-failure metadata with schema version 2.
9. Update scan-resolution metadata for corrected generic routes.
10. Update the active-scan contract.
11. Remove or deprecate universal student-assignment route helpers.
12. Publish `pds-core 0.2.0`.

### 23.2 `pds-scoreform`

1. Declare the compatible Core dependency.
2. Align Python support.
3. Move assignment storage beneath the ScoreForm module work root.
4. Add durable answer-sheet page records.
5. Create route registrations before PDF rendering.
6. Generate PDS2 QR codes.
7. Resolve student identity from page records.
8. Migrate scanner and scoring routes.
9. Add provenance and duplicate-page tests.
10. Remove active generation of OMR1 and PDS1.

### 23.3 `pds-quillan`

1. Declare the compatible Core dependency.
2. Remove sibling `mypy_path`.
3. Move assignment storage beneath the Quillan module work root.
4. Add durable response-page records.
5. Create route registrations before document rendering.
6. Generate PDS2 QR codes.
7. Resolve student submissions from page records.
8. Migrate scan assembly and review routes.
9. Add continuation-page and provenance tests.
10. Remove active generation of PDS1.

### 23.4 `pds-concord`

1. Declare the compatible Core dependency.
2. Register the Concord module profile.
3. Use `activity_id` as the Concord routing `work_id`.
4. Create Artifact Page records before rendering.
5. Create route registrations for returned Artifact Pages.
6. Generate PDS2 QR codes.
7. Resolve routes to Artifact Pages.
8. Create Concord Scan References from Core source-page references.
9. Implement routing-review integration.
10. Test all representative student, Group, Session, Activity, Event, and multi-subject cases.

### 23.5 Future Core design issue

Open a separate issue for the suite assignment registry, including:

* module work discovery;
* academic-period hierarchy;
* assessment classification;
* lifecycle and status;
* rebuildable indexes;
* stale-entry detection;
* and grading/reporting consumption.

---

## 24. Acceptance Criteria

This integration specification is satisfied when:

1. Core no longer requires `student_id` in its universal QR or normalized route model.
2. Core no longer treats student submission directories as the universal route destination.
3. PDS2 is the active generated QR format for ScoreForm, Quillan, and Concord.
4. Every expected returned page has durable route identity and a persisted registration.
5. The PDS2 QR contains only module, class, work, and route identity.
6. Authors, Subjects, students, Groups, templates, and page semantics are resolved from module records.
7. route registrations are found deterministically without recursive directory traversal.
8. route IDs are immutable and never silently repointed.
9. module work roots are qualified by module.
10. ScoreForm, Quillan, and Concord can use the same `work_id` in the same class without collision.
11. Core can dispatch mixed-module scans without importing sibling private code.
12. generic failure metadata supports student and non-student routes.
13. retained source scans remain canonical and immutable.
14. all routed evidence remains traceable to its source scan and source page.
15. ScoreForm and Quillan declare compatible Core package dependencies.
16. all modules run under a compatible Python version.
17. Concord routes valid pages with no student Subject.
18. one teacher tracker can route as one Artifact while retaining several Subjects.
19. unresolved Author or Subject status does not prevent correct page routing.
20. the resulting identity model can be indexed later by a suite assignment registry without changing the QR contract.

---

## 25. Final Architectural Rule

The shared Paper Data Suite QR and routing model is:

```text
PDS2 QR
    -> Core RouteLocator
    -> persisted Core RouteRegistration
    -> typed module-owned page target
    -> module-owned semantic records
    -> module-owned evidence, Review, Scoring, or reporting workflow
```

It is not:

```text
QR
    -> student
    -> universal student submission directory
```

This distinction is required for Concord and provides the cleaner long-term contract for ScoreForm, Quillan, and future paper-processing modules.
