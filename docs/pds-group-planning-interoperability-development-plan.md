# Paper Data Suite Group Planning Interoperability Development Plan

## Scope

This plan coordinates development across three Paper Data Suite repositories:

- `pds-core`
- `pds-concord`
- `pds-meridian`

The goal is to allow Concord to form groups using optional academic grouping signals produced by Meridian **without creating a direct Concord → Meridian dependency**, while preserving fully manual group creation and organization inside Concord.

The architectural principle is:

```text
                    pds-core
                       │
          grouping_signal_set_v1
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
       pds-meridian          pds-concord
       optional producer     consumer / planner
            │                     │
            │                     ▼
            │              Group Plan Preview
            │                     │
            │                     ▼
            └──────────────> teacher approval
                                  │
                                  ▼
                         Group + Membership
```

The dependency direction must remain:

```text
Meridian -> Core
Concord  -> Core

Meridian -X-> Concord
Concord  -X-> Meridian
Core     -X-> Meridian policy
Core     -X-> Concord grouping algorithms
```

This gives teachers four legitimate grouping paths:

```text
1. Direct manual Group creation in Concord
2. Manual Group planning in Concord
3. Import a teacher-created grouping-signal file
4. Import a Meridian-generated grouping-signal file
```

Meridian must remain entirely optional.

---

# Release Strategy

## Core

Recommended release:

```text
pds-core 0.6.1
```

Recommended milestone:

> **v0.6.1 — Shared Grouping Signal Interchange**

This should be a backward-compatible additive release within the existing Core 0.6 contract family.

Using Core 0.6.1 instead of Core 0.7.0 avoids unnecessary coordinated releases of other modules that currently accept:

```text
pds-core>=0.6,<0.7
```

The intended compatibility target becomes:

```text
Core       0.6.1
ScoreForm  0.10.0
Quillan    0.9.0
Concord    0.3.0
Meridian   0.2.0
```

Recommended future dependency declarations:

```text
pds-concord 0.3.0:
    pds-core>=0.6.1,<0.7

pds-meridian 0.2.0:
    pds-core>=0.6.1,<0.7
```

---

# 1. pds-core — Neutral Grouping-Signal Interchange

## Proposed Milestone

> **v0.6.1 — Shared Grouping Signal Interchange**

## Proposed Umbrella Issue

> **Define a neutral, privacy-minimized interchange for student grouping signals**

Core should own only the shared interchange contract and its neutral infrastructure.

Core should own:

- contract models;
- validation;
- canonical serialization;
- human-editable import;
- immutable exchange storage;
- class and student identity validation;
- generic diagnostics.

Core must not own:

- what "ability" means;
- how an academic band is calculated;
- whether heterogeneous or homogeneous grouping is pedagogically preferable;
- how Concord Groups are formed;
- proficiency policy;
- grading policy;
- Concord Group planning algorithms.

---

## Contract Name

Recommended contract:

```text
grouping_signal_set_v1
```

Avoid names such as:

```text
ability_profile
student_ability
proficiency_group
```

A grouping signal is contextual and temporary. It must not become a permanent label attached to the student.

---

## Conceptual V1 Model

```json
{
  "record_type": "grouping_signal_set",
  "contract_version": "grouping_signal_set_v1",
  "signal_set_id": "argument-writing-2026-10-15",
  "class_id": "english10-p3",
  "created_at": "2026-10-15T14:30:00-04:00",
  "source": {
    "source_kind": "module_export",
    "producer_module_id": "meridian",
    "producer_export_id": "grouping-export-17"
  },
  "dimensions": [
    {
      "dimension_id": "argument_writing",
      "label": "Argument Writing",
      "band_count": 4
    }
  ],
  "students": [
    {
      "student_id": "student-001",
      "bands": {
        "argument_writing": 2
      }
    },
    {
      "student_id": "student-002",
      "bands": {
        "argument_writing": 4
      }
    }
  ]
}
```

For v1, signals should preferably be **ordinal bands**:

```text
1..N
```

rather than raw grades or percentages.

This is sufficient for:

```text
similar-signal grouping
mixed-signal grouping
distribution across groups
```

while avoiding unnecessary transmission of:

- percentages;
- raw evidence;
- Grade calculations;
- proficiency internals;
- producer-native evidence records.

A band must remain context-specific.

For example:

```text
band 1
```

must not universally mean:

```text
failing
low ability
below grade level
```

It means only the first ordinal band in the selected signal dimension.

---

## Human-Editable CSV

Core should support a convenience CSV form:

```csv
student_id,band
student-001,2
student-002,4
student-003,1
student-004,3
```

The importer can receive the remaining metadata explicitly:

```text
class_id
signal_set_id
dimension_id
dimension_label
band_count
```

This lets teachers create valid inputs using:

- Excel;
- Google Sheets;
- LibreOffice;
- Notepad;
- VS Code.

Teachers should not be required to hand-author canonical JSON.

---

## Shared Exchange Namespace

Recommended conceptual storage:

```text
exchange/
└── grouping-signals/
    └── <class_id>/
        └── <signal_set_id>.json
```

Do not create producer-specific integration paths such as:

```text
meridian/exports/for-concord/
```

The shared pattern should be:

```text
Core exchange namespace
      ↑
Meridian writes
Concord reads
Teacher may also import/write data
```

Signal sets should be immutable snapshots.

Avoid mutable aliases such as:

```text
latest.json
current.json
```

If the signal calculation changes, create another signal set.

Example:

```text
argument-writing-oct15
argument-writing-nov01
```

---

## Proposed Core Issues

### 1. Define Grouping Signal Set v1 and architectural boundaries

Define:

- exact contract;
- privacy model;
- purpose;
- producer-neutral semantics;
- distinction from grades/proficiency;
- distinction from Concord Groups;
- immutability rules.

Add an ADR if appropriate.

### 2. Implement typed grouping-signal models and canonical serialization

Implement:

- exact models;
- validation;
- canonical JSON;
- duplicate rejection;
- safe identifiers;
- ordinal-band validation;
- deterministic serialization;
- round-trip tests.

### 3. Implement human-editable CSV import/export

Support:

```text
student_id,band
```

with:

- strict validation;
- deterministic conversion;
- bounded diagnostics;
- unknown/duplicate student detection.

### 4. Implement neutral grouping-signal exchange storage

Implement:

- safe Core-owned paths;
- immutable writes;
- exact load;
- bounded list/query;
- no sibling-specific storage conventions.

### 5. Implement class/roster validation and diagnostics

Detect and report:

- unknown student;
- duplicate student;
- wrong class;
- invalid band;
- missing roster student;
- malformed dimension metadata.

Missing roster students should be reportable, not necessarily fatal, because Concord may allow the teacher to decide how to handle them during planning.

### 6. Build installed contract acceptance and release Core 0.6.1

Qualification should prove:

```text
CSV
-> Core model
-> canonical JSON
-> immutable storage
-> exact reload
```

while preserving all existing Core 0.6 contracts.

Also verify existing ScoreForm and Quillan dependency compatibility.

---

# 2. pds-meridian — Optional Grouping-Signal Producer

Meridian should not create Concord Groups.

Meridian should optionally produce neutral academic planning signals:

```text
academic evidence / proficiency
            ↓
teacher-selected planning dimension
            ↓
privacy-minimized ordinal grouping signals
```

Concord should never need to understand Meridian internals.

---

## Proposed Meridian Milestone Rename

Current:

> **v0.2.0 — Standards Proficiency and Grade-Item Policy Engine**

Recommended:

> **v0.2.0 — Standards Proficiency, Grade-Item Policy, and Planning Exports**

"Planning Exports" deliberately describes a generic downstream capability rather than a Concord-specific integration.

---

## Meridian Ownership

Meridian owns the transformation from its academic interpretation into a grouping signal.

For example:

```text
student     argument-writing proficiency
Alice       Developing
Ben         Advanced
Carla       Beginning
David       Proficient
```

could become:

```text
Alice   -> band 2
Ben     -> band 4
Carla   -> band 1
David   -> band 3
```

The shared output contains only:

```text
student ID
dimension
ordinal band
```

Concord does not need:

```text
EvidenceInventory
attempt-selection policy
proficiency calculation internals
GradeItem
Grade
Quillan rating semantics
ScoreForm attempt history
Meridian policy implementation details
```

---

## Teacher-Controlled Export

Grouping-signal generation should always be explicit.

Conceptual workflow:

```text
Meridian
  |
  +-- Export grouping signals
          |
          +-- Class: English 10 / P3
          |
          +-- Basis:
          |      Argument Writing
          |
          +-- Evidence window:
          |      Current marking period
          |
          +-- Bands:
          |      4
          |
          +-- Preview
          |
          +-- Export
```

The teacher should be able to inspect the proposed band distribution before export.

---

## Do Not Export Raw "Ability Scores"

Avoid using the grouping interface to emit data such as:

```csv
student_id,grade
001,67.4
002,94.2
```

The v1 planning contract should instead prefer:

```csv
student_id,band
001,2
002,4
```

This minimizes exposure and prevents Concord from becoming dependent on Meridian's grading semantics.

---

## Meridian-Side Provenance

Meridian may retain richer provenance internally, such as:

```text
export ID
source proficiency snapshot
policy ID/version
standards/dimensions
evidence window
banding method
teacher overrides
```

But the Core interchange representation should contain only the information required for neutral group planning.

---

## Proposed Meridian v0.2.0 Issues

### 1. Adopt Core 0.6.1 grouping-signal contract

- depend on Core 0.6.1;
- consume only Core's neutral models;
- introduce no Concord dependency.

### 2. Define teacher-controlled planning-signal derivation policy

Define:

- eligible academic dimensions;
- ordinal-band conversion;
- insufficient/missing evidence behavior;
- deterministic banding;
- teacher override semantics;
- provenance requirements.

### 3. Implement Grouping Signal Set generation

Initially support:

- one selected dimension;
- one class;
- configurable number of ordinal bands.

Multiple dimensions may be added if they remain cleanly within the same contract.

### 4. Implement preview and diagnostics

Show:

```text
matched students
students without sufficient information
band distribution
selected basis
evidence window
policy version
```

Do not form groups.

### 5. Export to Core neutral exchange

Write:

```text
grouping_signal_set_v1
```

through Core-owned storage APIs.

Optionally also produce a human-readable CSV export.

### 6. Build installed export acceptance

Prove:

```text
real Meridian academic state
-> grouping signal export
-> Core validates
-> Core stores
-> Core reloads exact signal set
```

No Concord installation should be required.

### 7. Integrate planning exports into v0.2.0 release qualification

The planning export becomes part of the same Meridian 0.2.0 release as proficiency and Grade-item policy work, avoiding a separate patch/minor release solely for Concord interoperability.

---

# 3. pds-concord — Group Planning and Group Formation

## Proposed Milestone Rename

Current:

> **v0.3.0 — Template and Packet Workflows**

Recommended:

> **v0.3.0 — Group Planning, Templates, and Packet Workflows**

This preserves the original milestone identity while making Group Planning a first-class feature.

---

## Proposed Revised Milestone Description

> Expand Concord from the v0.2.0 executable collaborative Activity slice into reusable **Group Planning, Template, and Packet workflows**. Allow teachers to form and revise Groups directly, preview deterministic random/similar-signal/mixed-signal arrangements, optionally consume Core `grouping_signal_set_v1` inputs produced manually or by systems such as Meridian, and commit approved plans through Concord's existing Group and Membership contracts. In parallel, implement reusable printable Template Definitions and Packets, generate Activity- and Group-specific scannable instances through the existing PDS2 Artifact Page infrastructure, and provide a starter library of collaborative-learning forms.
>
> Meridian remains optional. Imported planning signals are teacher-restricted operational inputs, not Concord Scores or published academic evidence. Manual Group creation remains fully supported.

---

# Group Plan Must Remain Distinct from Group

Introduce a planning layer:

```text
Grouping Signal Set
        ↓
Group Builder
        ↓
Group Plan
        ↓
Teacher Preview / Edit
        ↓
Teacher Approves
        ↓
Group + GroupMembership records
```

A proposal must never silently become canonical Group state.

---

## Conceptual GroupPlan Model

Possible fields:

```text
group_plan_id
activity_id
strategy
target_group_size
target_group_count
seed
source_signal_set_id
source_signal_set_digest
planned_groups
status
created_provenance
```

Not every field must be required.

Important invariants:

```text
GroupPlan != Group
GroupPlan != GroupMembership
GroupPlan != Academic Result
GroupingSignal != Score
```

When a plan is applied:

```text
Group
GroupMembership
```

remain the canonical collaboration records.

The plan may remain operational provenance but must not be published through Concord's Academic Result Manifest.

---

# Concord Grouping Modes

## Mode 1 — Existing Direct Group Creation

Preserve current native workflows:

```text
Create Group
Create Group with members
Add Membership
Add Memberships
Reassign Membership
End Membership
Update Group
```

Teachers must never be forced to use Group Plans or grouping signals.

---

## Mode 2 — Manual Group Planner

Allow a teacher to build a plan interactively:

```text
Create Group Plan
Target size: 4

Group A
  Alice
  Ben
  Carla
  David

Group B
  ...
```

Then explicitly:

```text
Apply Plan
```

---

## Mode 3 — Random Groups

Example:

```text
Strategy: Random
Target group size: 4
Seed: generated/displayed
```

Randomization should be deterministic once the seed is chosen so previews are reproducible and testable.

---

## Mode 4 — Similar-Signal Groups

Students with similar bands are clustered.

Example:

```text
Group A: 1 1 1 1
Group B: 2 2 2 2
Group C: 3 3 3 3
Group D: 4 4 4 4
```

Internal terminology should be:

```text
similar_signal
```

rather than labels such as:

```text
low group
high group
```

---

## Mode 5 — Mixed-Signal Groups

Distribute signal bands across groups.

Example:

```text
Group A: 1 2 3 4
Group B: 1 2 3 4
Group C: 1 2 3 4
```

Internal terminology:

```text
mixed_signal
```

This keeps the algorithm generic.

---

# Missing-Signal Behavior

Suppose:

```text
24 roster students
21 signal values
3 missing
```

Concord must never silently omit the three unmatched students.

Preview should report:

```text
24 roster students
21 have grouping signals
3 do not

Missing:
  Alice
  Ben
  Carla
```

Teacher choices can include:

```text
Assign missing students randomly
Place missing students manually
Leave unassigned in this plan
```

The safest default is:

```text
require teacher decision
```

before applying the plan.

Reject before planning:

```text
unknown student ID
wrong class
duplicate student
invalid band
malformed signal set
```

---

# Grouping Algorithm Boundaries for v0.3.0

Keep the first release deliberately bounded.

Implement:

```text
random
similar_signal
mixed_signal
```

Support:

```text
target group size
OR
target group count
```

Where mathematically possible, target:

```text
maximum group-size difference <= 1
```

Use deterministic tie-breaking and seed-based ordering.

Do not turn v0.3.0 into a general optimization engine.

Defer more sophisticated constraints such as:

```text
keep specific students apart
keep specific students together
avoid previous collaborators
balance language background
balance demographic properties
ensure one selected role per group
social-network optimization
```

unless a later issue explicitly adds them.

---

# Direct Arrangement Import

Concord should also support a very simple direct-plan format:

```csv
student_id,group
student-001,Group A
student-002,Group B
student-003,Group A
student-004,Group B
```

This means:

```text
"Here is my proposed arrangement."
```

It is distinct from a Grouping Signal Set, which means:

```text
"Here is information Concord may use to derive an arrangement."
```

Direct arrangement import should produce a **Group Plan**, not immediately mutate canonical Groups.

Workflow:

```text
CSV
-> validate against roster
-> Group Plan
-> preview/edit
-> teacher approval
-> Group + GroupMembership
```

---

# Integration with Templates and Packets

Adding Group Planning strengthens the original v0.3.0 milestone.

The teacher workflow becomes:

```text
Plan collaboration
        ↓
Create Groups
        ↓
Create Group-specific materials
        ↓
Print / distribute
        ↓
Conduct Activity
        ↓
Scan / route
        ↓
Review / score
```

Approved Groups can drive Packet generation:

```text
Group A
  - discussion map
  - role sheet
  - group reflection

Group B
  - discussion map
  - role sheet
  - group reflection
```

Each generated item continues to use the existing:

```text
PDS2 Artifact Page
Artifact Instance
Activity context
Session context
Group context
```

No second print/scan system should be introduced.

---

# Proposed Concord v0.3.0 Issue Structure

## Umbrella

> **v0.3.0 — Build Group Planning, Template, and Packet workflows**

### 1. Adopt Core 0.6.1 and Grouping Signal Set v1

- exact Core contract;
- no Meridian dependency;
- installed contract qualification.

### 2. Define Group Plan records and lifecycle

Define:

```text
draft
previewed
approved
applied
cancelled
```

or equivalent.

Group Plans remain operational, not academic-result records.

### 3. Implement manual and imported Group Plans

Support:

- roster-driven manual planning;
- direct `student_id,group` arrangement import;
- preview/edit before apply.

### 4. Implement deterministic random Group generation

Support:

- seed;
- target size/count;
- balanced group sizes;
- reproducible previews.

### 5. Implement grouping-signal import and diagnostics

Support:

- Core exchange discovery;
- exact signal-set selection;
- class/roster validation;
- missing-signal diagnostics;
- no producer-specific assumptions.

### 6. Implement similar-signal and mixed-signal planning

Use exact ordinal bands.

Support:

```text
similar_signal
mixed_signal
```

with deterministic behavior.

### 7. Apply approved Group Plans through native Group/Membership workflows

Do not create alternate Group storage.

Applying a plan must use Concord's canonical:

```text
Group
GroupMembership
```

workflow boundaries.

Preserve history and reassignment semantics.

### 8. Define Template Definition v1

Create immutable/versioned reusable printable Template Definitions.

### 9. Implement Template authoring and versioning workflows

Support teacher-local management of reusable templates.

### 10. Define Packet Definition and composition

Allow multiple Template Definitions to form reusable collaborative Packets.

### 11. Generate Activity-, Session-, and Group-specific Packet instances

Use existing PDS2 Artifact Page routing.

No parallel print/scan path.

### 12. Build starter collaborative Template library

Initial forms may include:

```text
Venn diagram
K-W-L chart
Socratic Seminar sheet
peer-observation form
group-role sheet
lab organizer
discussion map
reflection/checklist
```

### 13. Integrate Group Planning with Packet generation

Support generation such as:

```text
one Packet instance per approved Group
```

while preserving exact Activity/Session/Group context.

### 14. Build installed v0.3.0 end-to-end acceptance

Exercise at least:

```text
manual Group planning
direct arrangement import
hand-authored grouping signals
random planning
similar-signal planning
mixed-signal planning
teacher approval
native Group creation
Packet generation
PDS2 routing
```

Meridian should not be required for Concord's authoritative repository acceptance.

### 15. Conduct v0.3.0 implementation audit and release

Verify:

- Group planning semantics;
- no Meridian dependency;
- signal privacy;
- template/packet workflow;
- installed qualification;
- no duplicate Group or routing subsystem.

---

# Cross-Repository Sequencing

Recommended sequence:

```text
PHASE A
Core v0.6.1
Grouping Signal Set contract
CSV import
exchange namespace
release
        │
        ├──────────────────────────┐
        ▼                          ▼
PHASE B                     PHASE C
Concord v0.3.0             Meridian v0.2.0
signal importer             proficiency engine
Group Planner               planning exporter
manual/random               grouping signals
similar/mixed               Core exchange writer
        │                          │
        └──────────────┬───────────┘
                       ▼
                 INTEROP ACCEPTANCE
```

Concord should not wait for Meridian.

Once Core 0.6.1 exists, Concord can develop against:

```text
synthetic hand-authored Grouping Signal Sets
```

Meridian can develop its exporter independently.

This avoids cross-repository blocking.

---

# Cross-Repository Interoperability Acceptance

The final cross-suite proof should be:

```text
Meridian
  produces grouping_signal_set_v1
            ↓
Core
  validates and stores immutable signal set
            ↓
Concord
  discovers exact signal set
            ↓
  verifies class + roster
            ↓
  creates Group Plan
            ↓
  produces mixed/similar preview
            ↓
teacher approval
            ↓
  native Group + GroupMembership records
```

This should be a conformance/integration test, not a runtime package dependency.

---

# Repository-Local Acceptance Boundaries

## Core

Authoritative test:

```text
CSV
-> Core model
-> canonical serialization
-> immutable storage
-> exact reload
```

No Meridian or Concord installation required.

## Meridian

Authoritative test:

```text
Meridian academic state
-> grouping signal derivation
-> Core grouping_signal_set_v1
-> Core validation/storage/reload
```

No Concord installation required.

## Concord

Authoritative test:

```text
synthetic Core GroupingSignalSet
-> Group Plan
-> teacher approval
-> native Group + GroupMembership
```

No Meridian installation required.

## Optional Cross-Suite Qualification

A final suite-level acceptance may install all three exact released artifacts and prove the complete chain.

This remains release/conformance validation, not runtime coupling.

---

# Privacy and Data-Minimization Rules

The following distinctions should be explicit:

```text
Grouping Signal Set
!= Academic Result Manifest

Grouping Signal Set
!= Meridian Grade report

Grouping Signal Set
!= permanent student profile

Grouping band
!= universal student ability

Group Plan
!= published academic evidence

Group Membership
!= grouping-signal history

Grouping signal
!= Concord Score
```

Required rules:

- grouping signals are teacher-restricted operational inputs;
- Concord must not publish them in Academic Result Manifests;
- Packet or Artifact metadata must not expose signal values;
- canonical Group Membership must not copy forward a student's source band;
- Group Scores must never derive automatically from grouping bands;
- Meridian should export ordinal grouping signals rather than raw evidence;
- every Group Plan requires explicit teacher approval before canonical Group creation;
- manual Group creation remains fully supported whether or not Meridian is installed.

---

# Final Recommended Milestone Names

## pds-core

> **v0.6.1 — Shared Grouping Signal Interchange**

## pds-meridian

Current:

> v0.2.0 — Standards Proficiency and Grade-Item Policy Engine

Recommended:

> **v0.2.0 — Standards Proficiency, Grade-Item Policy, and Planning Exports**

## pds-concord

Current:

> v0.3.0 — Template and Packet Workflows

Recommended:

> **v0.3.0 — Group Planning, Templates, and Packet Workflows**

---

# Product-Level Outcome

The coordinated feature should ultimately support this teacher workflow:

```text
Choose how to form Groups
│
├── Create directly in Concord
│
├── Build manually in Concord
│
├── Import a direct arrangement
│
├── Randomize
│
└── Use grouping signals
      │
      ├── teacher-created
      └── Meridian-generated
             ↓
          Preview
             ↓
        Teacher edits
             ↓
        Teacher approves
             ↓
      Concord native Groups
             ↓
      Group-specific Packets
             ↓
       PDS2 Artifact Pages
             ↓
       collaborative Activity
             ↓
       scan / route / review
             ↓
          native Scores
```

This preserves clean module ownership while making the three repositories interoperable:

```text
Core defines the neutral language.
Meridian optionally produces academic planning signals.
Concord owns Group planning and Group creation.
```

No module needs to know another module's internal implementation.
