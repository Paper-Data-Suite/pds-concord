# ADR 0012: Link ScoreForm and Quillan Without Duplication

**Status:** Accepted
**Date:** July 13, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord`

## Context

Concord is one module in the Paper Data Suite.

Several collaborative Activities may require evidence that belongs naturally to another Paper Data Suite module.

Examples include:

* an individual multiple-choice concept check completed during a laboratory Activity;
* an OMR-based procedure check;
* a structured individual accountability form;
* a written explanation of a Group decision;
* an individual reflection on collaborative work;
* an extended project postmortem;
* a written defense of a design choice;
* or an analytical response completed after a seminar.

These workflows overlap with Concord’s Activities, Sessions, Groups, evidence, and Scores, but they do not belong entirely inside Concord.

`pds-scoreform` owns machine-readable selected-response and OMR workflows.

`pds-quillan` owns focused or extended written-response review workflows.

Concord owns collaborative Activity context, including:

* Sessions;
* Groups;
* Group Memberships;
* Roles;
* Responsibilities;
* Concord Artifacts;
* Artifact Review;
* evidence Moderation;
* Concord Criteria;
* Concord Scoring Scales;
* and Concord Score Records.

Without an explicit integration decision, Concord could begin duplicating sibling-module functionality.

Examples of duplication would include:

* creating Concord-specific bubble sheets;
* scoring OMR marks inside Concord;
* copying ScoreForm answer keys;
* recreating Quillan writing assignments;
* assembling written submissions in Concord;
* copying Quillan review data into Concord-owned records;
* recreating Quillan feedback workflows;
* or treating sibling-module results as though Concord had produced them.

The opposite problem is also possible.

If Concord cannot reference sibling-module records, teachers may have to:

* enter the same assignment information repeatedly;
* copy results manually;
* lose the relationship between individual checks and collaborative Activities;
* or preserve informal notes that cannot be traced back to the original record.

Concord therefore needs a cross-module relationship that preserves ownership while allowing related evidence to be used deliberately.

## Decision

Concord will link ScoreForm and Quillan records through durable, typed, module-qualified references.

Concord will not duplicate or assume ownership of their:

* assignments;
* generated instruments;
* source evidence;
* review records;
* scoring or rating records;
* feedback;
* exports;
* or module-specific processing workflows.

The conceptual relationship is:

```text
ScoreForm or Quillan record
    -> typed External Reference in Concord
    -> optional Evidence Reference
    -> optional Score Evidence Link
    -> explicit Concord teacher judgment
```

The originating module remains authoritative for its record.

Concord remains authoritative for:

* why the record is related to a Concord Activity;
* how it may be used as Concord evidence;
* any Concord-specific Moderation decision;
* and any Concord Score Record created from the teacher’s broader judgment.

## Dependency Direction

All three modules should consume shared infrastructure from `pds-core`.

The intended dependency direction is:

```text
pds-scoreform -> pds-core
pds-quillan   -> pds-core
pds-concord   -> pds-core
```

Concord must not depend directly on ScoreForm or Quillan merely to obtain:

* workspace resolution;
* class identity;
* assignment identity;
* roster identity;
* student identity;
* identifier validation;
* QR parsing;
* scan retention;
* safe path construction;
* standards references;
* or operating-system file opening.

Those capabilities belong to Core.

### No mandatory sibling-package dependency

Using Concord must not require importing the ScoreForm or Quillan Python packages.

Likewise, using ScoreForm or Quillan must not require installing Concord.

Cross-module relationships should operate through:

* durable identifiers;
* public data contracts;
* shared Core conventions;
* module-owned exports;
* or optional adapters.

Concord must not import private implementation modules from sibling repositories.

For example, Concord must not rely on:

```python
from scoreform.internal.results import ...
```

or:

```python
from quillan.internal.review import ...
```

to interpret sibling-module records.

Internal package layout is not a stable integration contract.

### Optional adapters

A future integration adapter may provide conveniences such as:

* validating that a referenced assignment exists;
* displaying a module-owned record label;
* opening the owning module’s evidence;
* reading a supported result export;
* or resolving a stable public record identifier.

Such an adapter must:

* use a documented public contract;
* preserve the owning module;
* handle absence or incompatibility explicitly;
* avoid mutating the external record;
* and remain optional to Concord’s foundational workflow.

An adapter does not transfer ownership to Concord.

## Shared Identity

Cross-module relationships should use Core-owned durable identity wherever the concepts are shared.

Possible shared identities include:

* `class_id`;
* `assignment_id`;
* `student_id`;
* `standard_id`;
* and `profile_id`.

Module-specific records require module-qualified identity.

For example:

```text
owning_module: scoreform
record_type: result
record_id: <durable ScoreForm result identifier>
```

and:

```text
owning_module: quillan
record_type: review
record_id: <durable Quillan review identifier>
```

### Module qualification is required

A bare identifier is insufficient when different modules may use the same value.

For example:

```text
assignment_id: project_reflection
```

does not establish whether the assignment belongs to:

* Concord;
* ScoreForm;
* Quillan;
* or another module.

The owning module and record type are part of the external identity.

The conceptual identity is:

```text
owning module
+ record type
+ durable record identifier
```

### Shared student identity

When an external record concerns one student, Concord should associate it with the same Core `student_id` where the owning module supports that identity.

Concord must not create a duplicate student record merely to link sibling-module evidence.

A name string is not a substitute for the durable student reference.

### Group and multi-subject limitations

Concord supports:

* Group;
* child-Group;
* Session;
* Activity;
* and multi-subject evidence.

ScoreForm or Quillan may not support every one of those subject forms in every current workflow.

Concord must not work around such limitations by:

* creating synthetic students;
* placing `group_id` into `student_id`;
* selecting an arbitrary Group member;
* or treating the recorder as the entire Group.

An external module should be used only for the subject and workflow forms that its contract supports.

The Concord relationship may still identify the broader:

* Activity;
* Session;
* Group;
* milestone;
* Work Item;
* or Criterion

to which the external record is relevant.

## External Reference Structure

A Concord External Reference to ScoreForm or Quillan should be capable of recording:

* durable `external_reference_id`;
* owning module;
* external record type;
* durable external record identifier;
* external schema or contract version where applicable;
* relationship purpose;
* parent Concord Activity;
* optional Session;
* optional Group;
* optional Work Item;
* optional Activity Marker;
* optional Artifact Instance;
* optional Criterion;
* optional Score Record;
* optional student or other Subject context;
* descriptive label;
* availability status;
* creation provenance;
* last-confirmed timestamp where applicable;
* and correction or supersession history.

The exact serialized contract belongs in later work.

### Relationship purpose

The reference should state why the external record is connected to Concord.

Possible purposes include:

* related assignment;
* packet instruction;
* individual accountability check;
* supporting evidence;
* complementary written response;
* prerequisite check;
* follow-up reflection;
* Score evidence;
* contextual result;
* or downstream export relationship.

A generic unlabeled link is insufficient when its use is ambiguous.

### Cardinality

The relationship may be many-to-many.

One Concord Activity may reference:

* several ScoreForm assignments;
* several Quillan assignments;
* and many individual external results or responses.

One external assignment may be related to:

* several Concord Sessions;
* several Groups;
* several Criteria;
* or several Concord Activities

when that use is deliberate.

Each relationship should remain explicit.

## ScoreForm Boundary

### ScoreForm owns

ScoreForm owns its selected-response and OMR workflows, including:

* answer-sheet layout;
* answer bubbles or structured mark fields;
* corner-registration marks;
* QR-bearing ScoreForm pages;
* answer keys;
* image and PDF mark detection;
* blank-answer detection;
* ambiguous- or double-mark detection;
* selected-response scoring;
* attempt handling;
* ScoreForm result records;
* result exports;
* ScoreForm-specific audit data;
* and ScoreForm-specific routed evidence.

ScoreForm remains authoritative for determining what its machine-readable marks represent under its assignment and answer-key contract.

### Concord may reference ScoreForm assignments

A Concord Activity may reference a ScoreForm assignment when the teacher wants an individual structured check related to the collaborative work.

Examples include:

* laboratory procedure check;
* terminology check;
* concept check;
* project-requirement check;
* interpretation-of-results check;
* structured self-rating;
* structured peer rating;
* or another machine-readable accountability instrument.

The reference may identify:

* ScoreForm assignment ID;
* related Concord Activity;
* optional Session or milestone;
* intended participants;
* relationship purpose;
* relevant Concord Criteria;
* and whether later ScoreForm results may be considered as evidence.

### Concord packet instructions

A Concord packet may include a brief instruction directing a participant to complete a ScoreForm instrument.

For example:

```text
Complete the ScoreForm procedure check identified for this Activity.
```

The instruction is a Concord Artifact or packet instruction.

The ScoreForm answer sheet remains a ScoreForm-owned instrument.

Concord must not recreate the answer sheet as a Concord Template Version.

### Physical packet assembly

A teacher may physically distribute:

* Concord pages;
* ScoreForm pages;
* and Quillan pages

as one classroom packet.

Physical assembly does not transfer ownership.

Each scannable page should retain:

* its owning module;
* its own artifact or submission identity;
* its module-appropriate QR payload;
* and its own processing contract.

The Concord packet manifest may record that an external component was expected without treating that component as a Concord Artifact Instance.

The exact external-component manifest structure remains a later contract decision.

### ScoreForm results as Concord evidence

A ScoreForm result may be used as an external evidence source.

For example:

```text
Concord Criterion:
Understands the agreed laboratory procedure

External evidence:
ScoreForm procedure-check result
```

The ScoreForm result remains a ScoreForm result.

Concord may create:

* an External Reference;
* a typed Evidence Reference;
* and a Score Evidence Link

to that result.

If a Concord Score is appropriate, the teacher must create an explicit Concord Score Record.

### No automatic Score conversion

A ScoreForm result must not automatically become a Concord Score.

For example, the following values are not inherently equivalent:

```text
ScoreForm result:
8 of 10 selected-response items correct

Concord Criterion:
Contributes to evidence-based Group decisions
```

The ScoreForm result may provide relevant context, but it does not determine the Concord Criterion judgment.

Even where a ScoreForm assignment appears closely aligned to a Concord Criterion, the teacher must decide:

* whether the result is relevant;
* which target it concerns;
* how it should be used;
* whether other evidence is required;
* and what Concord Score value is justified.

### No OMR processing in Concord

Concord must not:

* detect filled bubbles;
* interpret machine-readable marks;
* score selected responses;
* apply answer keys;
* determine ambiguous marks;
* manage ScoreForm attempts;
* or create ScoreForm result rows.

If an OMR page is supplied to Concord accidentally, Concord should not process it as a Concord Artifact.

It should remain:

* routed to ScoreForm through the shared contract;
* unresolved for the appropriate owning module;
* or explicitly identified as misrouted.

### Peer-rating qualification

A ScoreForm result may be generated from peer ratings or student self-ratings.

Machine readability does not establish evidentiary fairness.

When such a result is used for a consequential Concord Score, Concord may still require Moderation concerning:

* bias;
* relevance;
* conflicting accounts;
* inappropriate use;
* or the difference between peer perception and teacher judgment.

ScoreForm owns mark processing.

Concord owns the decision about how that processed result may be used in a Concord judgment.

## Quillan Boundary

### Quillan owns

Quillan owns its written-response workflow, including:

* writing assignment configuration;
* student prompts;
* printable written-response pages;
* continuation pages;
* written submission assembly;
* submission records;
* review units;
* Focus Standard observations;
* teacher-entered written-work ratings;
* written feedback;
* teacher notes within the Quillan workflow;
* student feedback exports;
* assignment-local written-performance summaries;
* and Quillan-specific routed evidence.

Quillan remains authoritative for its written submission and review records.

### Concord may reference Quillan assignments

A Concord Activity may reference a Quillan assignment when the teacher wants a focused or extended written response related to the collaborative work.

Examples include:

* individual reflection;
* explanation of learning;
* written defense of a Group decision;
* project postmortem;
* design rationale;
* analytical exit response;
* extended peer feedback;
* written self-assessment;
* or explanation of a failed approach.

The Concord reference may identify:

* Quillan assignment ID;
* related Activity;
* optional Session, milestone, or Work Item;
* intended relationship to the collaborative work;
* whether the response is expected from each student;
* and which Concord Criteria it may complement.

### Short writing remains possible in Concord

Concord may generate brief fields such as:

* label;
* caption;
* note;
* concise explanation;
* one-sentence rationale;
* short evidence box;
* or compact reflection prompt.

These fields are appropriate when they are part of a structured collaborative Artifact.

Concord should not use this allowance to recreate Quillan’s extended written-response workflow.

A response belongs more naturally to Quillan when it requires:

* substantial prose;
* several paragraphs;
* detailed written reasoning;
* standards-focused written review;
* extended feedback;
* or a dedicated writing submission.

### Quillan records as Concord evidence

A Quillan response, submission, Review, or teacher-entered rating may be relevant to Concord.

For example:

```text
Concord Criterion:
Explains the Group's design decisions using relevant evidence

External evidence:
Quillan written design rationale and teacher Review
```

Concord may link to:

* the Quillan assignment;
* the student submission;
* the relevant Review record;
* an overall Focus Standard rating;
* or another stable Quillan-owned result.

The exact record used should be explicit.

### Response and Review are distinct

A Quillan response and its teacher Review are different evidence sources.

The response records the student’s writing.

The Review records teacher judgment within Quillan’s written-work model.

Concord must not collapse them into one generic external result.

A Concord Score may reference:

* the response;
* the Review;
* both;
* or neither,

depending on the intended evidence use.

### No automatic rating conversion

A Quillan rating must not automatically become a Concord Score.

For example:

```text
Quillan Focus Standard rating:
3 on the Quillan assignment scale

Concord Criterion:
Supports Group coordination
```

The values are not equivalent merely because both use a value of `3`.

The modules may differ in:

* Criterion definitions;
* Standards;
* target;
* scale;
* evidence;
* purpose;
* and scoring context.

The teacher must make an explicit Concord judgment.

### No written-response review in Concord

Concord must not:

* assemble Quillan submissions;
* manage Quillan continuation pages;
* recreate Quillan review units;
* duplicate Focus Standard observations;
* generate Quillan feedback;
* mutate Quillan Review records;
* or reproduce Quillan assignment-local reports.

If the teacher needs to inspect the written response, Concord may:

* open the owning record through an authorized integration;
* display a safe external reference;
* or direct the teacher to Quillan.

Concord must not create an unsynchronized copy of the complete Quillan workflow.

### Written peer evidence

A Quillan response may include claims about another student or Group.

The presence of a teacher-reviewed written response does not automatically authorize every claim for consequential Concord use.

Concord may require additional Moderation when the response:

* attributes contribution;
* alleges nonparticipation;
* disputes authorship;
* assigns blame;
* or evaluates another participant.

Quillan owns the written-response Review.

Concord owns the moderation of its use as collaborative-performance evidence.

## Shared Routing

ScoreForm, Quillan, and Concord should use the shared Core QR and routing contract.

The QR payload or normalized route must identify the owning module.

Conceptually:

```text
module=scoreform
module=quillan
module=concord
```

Each module processes its own module-specific page.

### Concord must not intercept sibling pages

Concord must not:

* route a ScoreForm answer sheet into a Concord Artifact folder;
* reinterpret a Quillan response page as a Concord Artifact Page;
* replace the sibling module value in the QR payload;
* rewrite a sibling module’s identifiers;
* or process sibling pages under Concord rules.

If a scan batch contains pages from several modules, the shared intake and routing process should preserve the owning module of each page.

After ScoreForm or Quillan processes its pages, Concord may link the resulting record through a durable reference.

### No Concord-only cross-module QR grammar

Concord must not create a second QR syntax solely to encode relationships to ScoreForm or Quillan.

Cross-module context that does not fit safely in the shared payload should be stored in linked local records.

The QR code should identify and route the page.

It does not need to contain the complete relationship among:

* Concord Activity;
* external assignment;
* Criterion;
* evidence use;
* and Score.

## Record Ownership

### ScoreForm remains authoritative for

* ScoreForm assignments;
* answer keys;
* generated answer sheets;
* OMR source evidence;
* selected-response processing;
* attempt records;
* ScoreForm results;
* and ScoreForm exports.

### Quillan remains authoritative for

* Quillan assignments;
* student prompts;
* written submissions;
* submission-page management;
* Review records;
* Focus Standard observations;
* written-work ratings;
* feedback;
* and Quillan exports.

### Concord remains authoritative for

* Concord Activities;
* Sessions;
* Groups and Memberships;
* Roles and Responsibilities;
* Concord Artifacts;
* Concord Artifact Review;
* Concord Moderation decisions;
* Concord Criteria;
* Concord Scoring Scales;
* Concord Score Records;
* Concord Score Evidence Links;
* and the relationship between external records and Concord context.

### Core remains authoritative for

* shared workspace configuration;
* canonical class identity;
* canonical roster and student identity;
* shared identifiers;
* shared QR parsing and validation;
* source-scan retention;
* shared provenance;
* safe routes;
* and shared standards identity.

## No Full-Record Duplication

Concord should not copy the full external record when a durable reference is sufficient.

Examples of content that should ordinarily remain in the owning module include:

* ScoreForm assignment JSON;
* ScoreForm answer keys;
* complete ScoreForm result files;
* Quillan assignment JSON;
* Quillan submission manifests;
* complete student writing;
* Quillan Review JSON;
* complete Quillan feedback;
* and module-specific reports.

Concord may retain limited descriptive metadata such as:

* external title;
* record type;
* related student;
* relationship purpose;
* version;
* availability;
* or teacher-entered evidence-use note.

### Bounded snapshots

A bounded snapshot may be necessary when:

* the external record is mutable;
* a consequential Concord Score depends on an exact earlier state;
* the owning module does not provide immutable revision identity;
* or the external record may become unavailable.

A snapshot should contain only the information needed to preserve the historical evidence relationship.

It should identify:

* source module;
* source record;
* capture timestamp;
* source version or revision where known;
* capturing actor;
* and purpose.

A snapshot must not be represented as the authoritative external record.

### Historical sufficiency

For consequential Scoring, a reference to a mutable “current result” may be insufficient.

The integration contract should provide at least one of:

* immutable external result identity;
* external revision identity;
* versioned export identity;
* or a bounded evidence snapshot.

The goal is to determine what external evidence the teacher used at the time of the Concord Score.

## Evidence and Score Semantics

### External result remains external evidence

A ScoreForm result or Quillan Review may function as evidence.

It does not become Concord-owned merely because Concord uses it.

A Concord Score Evidence Link should preserve:

* owning module;
* external record type;
* external record identifier;
* optional version or snapshot;
* Subject context;
* relevance description;
* and applicable Moderation state.

### Different modules may express different judgments

A ScoreForm result may represent:

* item correctness;
* response selection;
* machine-readable rating;
* completion;
* or another selected-response result.

A Quillan Review may represent:

* written evidence presence;
* Focus Standard observation;
* written-performance rating;
* feedback decision;
* or minimum-requirement outcome.

A Concord Score represents:

* one teacher-approved judgment;
* about one Concord Criterion;
* for one Concord target;
* in one collaborative Activity context.

These are different semantic records.

### Similar labels do not imply equivalence

Two modules may use similar labels such as:

* evidence;
* review;
* score;
* rating;
* criterion;
* standard;
* or result.

The labels do not guarantee identical meaning.

Cross-module mapping must be explicit.

For example, the following should not be assumed automatically:

```text
ScoreForm percentage
    == Concord scale value
```

```text
Quillan Focus Standard rating
    == Concord Criterion Score
```

```text
Quillan minimum-requirement outcome
    == Concord responsibility Score
```

```text
ScoreForm completion
    == Concord participation
```

### Shared Standard does not create shared Score

A Quillan rating and Concord Score may both reference the same Core `standard_id`.

That shared Standard provides alignment context.

It does not make the records interchangeable.

The modules may evaluate different:

* evidence;
* assignments;
* Criteria;
* targets;
* and scales.

## Teacher Confirmation

External evidence must not be linked consequentially through an invisible automatic process.

Concord may suggest external records based on:

* matching class;
* student;
* Activity;
* assignment;
* Session;
* milestone;
* Standard;
* or teacher configuration.

The teacher must confirm:

* the correct external record;
* the intended relationship;
* the relevant Subject;
* the permitted evidence use;
* and any Concord Score Evidence Link.

### No automatic result ingestion into Scores

A synchronization or import process may discover new ScoreForm or Quillan records.

Discovery must not automatically:

* create Concord Scores;
* change Concord Scores;
* populate Group member Scores;
* convert missing records to zero;
* or mark Responsibilities fulfilled.

The records remain candidate evidence until the teacher makes an explicit decision.

## Availability and Failure States

An external reference may be:

* available;
* unavailable;
* unresolved;
* moved;
* permission restricted;
* incompatible;
* superseded;
* deleted externally;
* not yet created;
* or temporarily inaccessible.

These are integration and evidence-availability states.

They are not performance judgments.

Concord must not convert an unavailable ScoreForm or Quillan record into:

* zero;
* lowest Score;
* failed participation;
* incomplete responsibility;
* or missing student performance.

The teacher may decide that:

* other evidence is sufficient;
* the Score should be deferred;
* evidence is insufficient;
* or the external reference is unnecessary.

### Module not installed

Concord should remain usable when ScoreForm or Quillan is not installed.

A reference may still be:

* recorded manually;
* displayed as unresolved;
* retained for later use;
* or omitted.

Concord’s basic Activity, Artifact, Review, and Scoring workflows must not fail because a sibling module is unavailable.

### Schema incompatibility

If an external record uses an unsupported schema or contract version, Concord should mark the integration state explicitly.

It must not guess at field meanings.

A human-readable label or limited fallback metadata may remain available while the detailed integration is unavailable.

## Privacy

A Concord reference does not broaden access to the external record.

For example:

* access to a Concord Score does not authorize access to a complete Quillan response;
* access to a Concord Activity does not authorize access to ScoreForm answer data;
* and access to a Group record does not authorize access to another student’s external result.

The owning module retains its own privacy and access rules.

Concord separately controls access to:

* the External Reference;
* relationship-purpose metadata;
* Concord Moderation;
* Concord Score Evidence Link;
* and Concord Score.

### Minimize copied content

Concord should avoid copying:

* full student writing;
* selected-response details;
* answer keys;
* feedback text;
* or sensitive teacher notes

unless a deliberate, authorized snapshot is required.

### Restricted evidence descriptions

When a user may view a Concord Score but not its external source, Concord may display:

* a restricted-evidence indicator;
* authorized descriptive label;
* source module;
* or general evidence-use statement.

It must not expose restricted content merely to explain the Score.

## Corrections and Supersession

Cross-module references may require correction.

Examples include:

* wrong assignment;
* wrong student result;
* wrong Quillan submission;
* incorrect milestone;
* incorrect relationship purpose;
* stale external version;
* or incorrect Criterion mapping.

A consequential correction should preserve:

* original External Reference;
* original Score Evidence Link where applicable;
* correction reason;
* correcting actor;
* correction timestamp;
* and replacement or superseding record.

### External record revision

If ScoreForm or Quillan revises a result or Review, Concord must not silently rewrite the historical basis of an existing Score.

The teacher may:

* keep the Concord Score unchanged;
* add a new evidence link;
* revise the rationale;
* create a superseding Concord Score;
* or mark the earlier external evidence relationship as superseded.

The earlier relationship remains available for provenance.

### External deletion

Deleting or archiving an external record must not cascade automatically into deletion of:

* Concord External References;
* historical Score Evidence Links;
* Concord Scores;
* or Activity history.

The reference may become unavailable while its historical identity remains preserved.

## Example Integration Workflows

### ScoreForm concept check

```text
Concord Activity:
Science laboratory investigation

External assignment:
ScoreForm procedure and terminology check

Relationship:
Individual accountability evidence

Processing:
ScoreForm generates and scores the OMR sheets

Concord use:
Teacher links selected results while judging an individual Criterion
```

The ScoreForm result does not automatically determine the Concord Score.

### ScoreForm peer-rating instrument

```text
Concord Activity:
Socratic seminar

External assignment:
ScoreForm machine-readable peer ratings

Processing:
ScoreForm reads the marks and produces results

Concord use:
Teacher moderates the evidentiary use before any consequential Score
```

Machine processing does not remove the need to evaluate fairness and relevance.

### Quillan project explanation

```text
Concord Activity:
Collaborative engineering project

External assignment:
Quillan written design rationale

Processing:
Quillan assembles the submission and stores teacher Review

Concord use:
Teacher links the response or Review as evidence for a relevant
Concord Criterion
```

Concord does not copy the complete written-response Review workflow.

### Quillan individual reflection

```text
Concord Activity:
Group retrospective

External assignment:
Quillan individual reflection

Relationship:
Complementary individual evidence

Concord use:
Teacher may consider the reflection with teacher observations,
Group Artifacts, and handoff records
```

The reflection does not automatically verify every contribution claim contained within it.

### Mixed physical packet

```text
Distributed together:
- Concord Group process form
- ScoreForm individual check
- Quillan written response pages

Scanned later:
- each page retains its owning module identity
- Core preserves source provenance
- each module processes its own pages
- Concord later links relevant sibling-module records
```

Physical packet unity does not create data-model ownership unity.

## Consequences

### Positive consequences

* ScoreForm and Quillan remain focused on their established workflows.
* Concord can use individual accountability and written-response evidence.
* Shared Core identity reduces duplicate roster and student data.
* OMR processing is not reimplemented.
* Written-response Review and feedback are not reimplemented.
* External records retain authoritative ownership.
* Concord Criteria and Scores remain semantically explicit.
* Similar numeric values are not treated as automatically equivalent.
* Mixed-module classroom packets remain possible.
* Each module can evolve behind a public contract.
* Concord remains usable when sibling modules are absent.
* Historical Scores can preserve their exact external evidence basis.
* Privacy remains controlled by both the source and consuming records.

### Negative consequences

* Cross-module workflows require durable public contracts.
* Teachers may need to confirm external evidence links.
* Opening the full source may require switching to another module.
* External schemas may evolve independently.
* Stable result or Review identity may require new work in sibling modules.
* Mutable external records may require bounded snapshots.
* Mixed-module packet manifests require additional modeling.
* Integration errors require explicit availability and compatibility states.
* Similar concepts such as rating, Score, Criterion, and Review require careful labeling.
* Corrections may span more than one module.

### Implementation consequences

Implementations must:

* use module-qualified External References;
* preserve the owning module and record type;
* avoid mandatory sibling-package imports;
* use Core identity and routing contracts;
* distinguish assignments from results, submissions, and Reviews;
* permit external records to function as typed evidence;
* require explicit Score Evidence Links;
* prevent automatic external-result-to-Concord-Score conversion;
* preserve applicable Moderation decisions;
* keep sibling pages under their owning module during routing;
* avoid copying full external records by default;
* support unavailable and incompatible states;
* preserve historical versions or bounded snapshots for consequential use;
* enforce record-specific privacy;
* and preserve corrections and supersession.

Teacher-facing labels should identify the source clearly, such as:

* **ScoreForm assignment**;
* **ScoreForm result**;
* **Quillan assignment**;
* **Quillan response**;
* **Quillan Review**;
* **External evidence use**;
* and **Concord Score**.

A generic label such as **linked score** should be avoided when it obscures ownership or meaning.

## Alternatives Considered

### Alternative 1: Add OMR directly to Concord

Rejected.

ScoreForm already owns:

* OMR layout;
* mark detection;
* answer-key scoring;
* ambiguity handling;
* and selected-response result output.

A second implementation would create incompatible behavior and duplicate maintenance.

### Alternative 2: Add extended written-response review directly to Concord

Rejected.

Quillan owns:

* written assignments;
* written submissions;
* teacher Review;
* standards-focused ratings;
* feedback;
* and written-work summaries.

Concord should not become a second writing-review system.

### Alternative 3: Depend directly on ScoreForm and Quillan packages

Rejected as the foundational integration model.

Direct imports would couple Concord to:

* sibling internal APIs;
* release schedules;
* installation state;
* and implementation layout.

Shared infrastructure belongs in Core, and module data should cross public contracts.

### Alternative 4: Copy complete sibling records into Concord

Rejected.

Full copying would create:

* conflicting authorities;
* stale duplicates;
* additional privacy exposure;
* and unclear correction ownership.

### Alternative 5: Store only a filesystem path

Rejected.

A path alone does not identify:

* owning module;
* record type;
* relationship purpose;
* version;
* Subject;
* availability;
* or historical evidence state.

### Alternative 6: Treat external results as Concord Score Records

Rejected.

A ScoreForm result, Quillan rating, and Concord Score have different semantics.

The Concord teacher must make an explicit Concord judgment.

### Alternative 7: Convert sibling scales automatically

Rejected.

Identical numeric or categorical labels do not guarantee equivalent:

* Criteria;
* evidence;
* targets;
* definitions;
* or purposes.

### Alternative 8: Use the same unqualified assignment ID across modules

Rejected.

The same identifier string may exist in several module namespaces.

Owning module and record type are required.

### Alternative 9: Route every Paper Data Suite page through Concord

Rejected.

Each module owns its own page-processing workflow.

Core should provide shared routing infrastructure without making Concord the dispatcher or owner.

### Alternative 10: Reissue ScoreForm or Quillan pages with Concord QR codes

Rejected.

Reissuing would obscure the owning module and risk incompatible processing.

### Alternative 11: Create synthetic students for Group-level sibling records

Rejected.

Synthetic identities would corrupt Core student identity and blur Group and student semantics.

### Alternative 12: Automatically link every matching external result

Rejected.

Matching class, student, or assignment context does not prove relevance to a particular Concord Criterion or Score.

Teacher confirmation is required.

### Alternative 13: Require sibling modules to be installed

Rejected.

Concord’s foundational workflow must remain independently usable.

### Alternative 14: Let external revisions silently update Concord Scores

Rejected.

A revised external record may justify reconsideration, but it must not rewrite the historical basis of an existing Score.

### Alternative 15: Duplicate sibling reports inside Concord

Rejected.

ScoreForm and Quillan remain responsible for their module-specific outputs.

Cross-module Grade and reporting aggregation belongs to a future reporting or gradebook module.

## Required Follow-Up

Later contracts and implementation work must define:

* module-qualified External Reference identity;
* supported ScoreForm record types;
* supported Quillan record types;
* stable assignment, result, submission, and Review identifiers;
* external schema-version representation;
* public result and Review contracts;
* optional adapter interfaces;
* relationship-purpose vocabulary;
* subject and student mapping;
* external evidence availability states;
* mixed-module packet-component references;
* shared routing behavior for mixed scan batches;
* immutable revision or snapshot requirements for consequential evidence;
* Score Evidence Links to sibling-module records;
* Moderation behavior for peer- or student-generated external evidence;
* privacy and authorization boundaries;
* correction and supersession behavior;
* and compatibility behavior when sibling schemas change.

Representative contract examples should test at least:

* one Concord Activity linked to one ScoreForm assignment;
* one Concord Activity linked to one Quillan assignment;
* one ScoreForm result supporting a Concord individual Score;
* one Quillan response supporting a Concord Score;
* one Quillan Review and response used as separate evidence sources;
* one external result supporting several Concord Scores;
* one Concord Score supported by Concord, ScoreForm, and Quillan evidence together;
* one ScoreForm peer-rating result requiring Concord Moderation;
* one Quillan response containing a disputed contribution claim;
* one physical packet containing pages from all three modules;
* one unavailable sibling-module record;
* one incompatible external schema version;
* one sibling module not installed;
* one corrected external reference;
* one external result revised after a Concord Score was recorded;
* one historical Concord Score retaining an earlier external evidence version;
* and one Group-level Concord Activity that does not create a synthetic sibling-module student.

## References

* [`docs/concord-conceptual-design-revised.md`](../concord-conceptual-design-revised.md)
* [`docs/design/cross-case-requirements.md`](../design/cross-case-requirements.md)
* [`docs/design/initial-concord-domain-model.md`](../design/initial-concord-domain-model.md)
* [`docs/packet_models/socratic-seminar-packet-model.md`](../packet_models/socratic-seminar-packet-model.md)
* [`docs/packet_models/science-laboratory-group-packet-model.md`](../packet_models/science-laboratory-group-packet-model.md)
* [`docs/packet_models/collaborative-programming_engineering_project_packet_model.md`](../packet_models/collaborative-programming_engineering_project_packet_model.md)
* [`docs/decisions/0001-concord-module-boundaries.md`](0001-concord-module-boundaries.md)
* [`docs/decisions/0002-paper-first-human-reviewed-evidence.md`](0002-paper-first-human-reviewed-evidence.md)
* [`docs/decisions/0003-activities-require-explicit-sessions.md`](0003-activities-require-explicit-sessions.md)
* [`docs/decisions/0004-contextual-groups-memberships-and-roles.md`](0004-contextual-groups-memberships-and-roles.md)
* [`docs/decisions/0005-separate-artifact-authors-and-subjects.md`](0005-separate-artifact-authors-and-subjects.md)
* [`docs/decisions/0006-distinguish-roles-responsibilities-tasks-and-contributions.md`](0006-distinguish-roles-responsibilities-tasks-and-contributions.md)
* [`docs/decisions/0007-preserve-source-evidence-and-history.md`](0007-preserve-source-evidence-and-history.md)
* [`docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`](0008-separate-review-moderation-scoring-grading-and-reporting.md)
* [`docs/decisions/0009-many-to-many-evidence-to-score-relationships.md`](0009-many-to-many-evidence-to-score-relationships.md)
* [`docs/decisions/0010-exceptional-evidence-states-are-not-low-scores.md`](0010-exceptional-evidence-states-are-not-low-scores.md)
* [`docs/decisions/0011-link-external-artifacts-without-managing-source-systems.md`](0011-link-external-artifacts-without-managing-source-systems.md)
* [`pds-core QR Payload and Routing Contract`](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/qr_payload_and_routing_contract.md)
* [`pds-scoreform README`](https://github.com/Paper-Data-Suite/pds-scoreform/blob/main/README.md)
* [`pds-quillan README`](https://github.com/Paper-Data-Suite/pds-quillan/blob/main/README.md)

## Notes

This ADR establishes ownership and integration boundaries among Concord, ScoreForm, and Quillan.

It does not require every Concord Activity to use either sibling module. It also does not make ScoreForm- or Quillan-specific structures mandatory parts of the Concord domain.

The next ADR addresses how optional Activity structures should remain available without becoming required for every Activity.
