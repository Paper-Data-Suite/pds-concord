# ADR 0015: Publish Versioned Concord Academic Result Manifests Through the Core Registry

**Status:** Proposed
**Date:** July 29, 2026
**Decision owners:** Paper Data Suite maintainers
**Applies to:** `pds-concord` and its integration with `pds-core` and `pds-meridian`

## Context

Paper Data Suite separates:

* shared canonical infrastructure;
* producer-native academic records;
* grading policy;
* standards-proficiency calculation;
* Grade calculation;
* and formal reporting

across distinct modules.

`pds-concord` owns collaborative classroom Activities and their native educational meaning, including:

* Sessions;
* Groups;
* Memberships;
* Roles;
* Responsibilities;
* Artifacts;
* Artifact Authors;
* Artifact Subjects;
* Review;
* Moderation;
* Criteria;
* Scoring Scales;
* Score Records;
* Score Evidence Links;
* non-score dispositions;
* and native correction and supersession history.

Concord does not own:

* Grade-item membership;
* standards-proficiency aggregation;
* attempt or evidence selection across Activities or modules;
* Academic Period membership;
* assignment Grades;
* marking-period Grades;
* cumulative course Grades;
* teacher overrides of derived Grade or proficiency results;
* or formal cross-module reporting.

Those responsibilities belong to `pds-meridian`.

`pds-core` now provides the shared infrastructure through which producer modules make selected result sets discoverable to Meridian and other authorized consumers.

Core owns:

* `ModuleWorkRef`;
* Academic Work Registration;
* immutable Publication Records;
* publication-series supersession;
* publication withdrawal;
* manifest-path and digest validation;
* shared publication kinds;
* shared publication capabilities;
* and the derived, nonauthoritative registry catalog.

Producer modules remain authoritative for:

* native records;
* native validation;
* native educational meaning;
* manifest schemas;
* manifest generation;
* and decisions about when a new manifest revision is required.

Core records that one exact producer-owned manifest revision was published. It does not reinterpret that manifest as a universal score, Grade, or report.

The Core publication architecture is:

```text
module-owned work
    -> optional Core Academic Work Registration
    -> module-owned authoritative records
    -> immutable module-owned manifest revision
    -> immutable Core Publication Record
    -> derived Core publication catalog
    -> Meridian or another authorized consumer
```

For Concord, the top-level work identity is:

```text
ModuleWorkRef
├── module_id: concord
├── class_id: <Core class_id>
└── work_id: <Concord activity_id>
```

The existing Concord architecture already establishes that:

* a Score Record is one teacher-approved judgment about one Criterion and one explicit target;
* a standard-backed Score has exactly one governing `standard_id`;
* a local Score is not a direct standards result;
* Group Scores do not create individual Scores;
* missing or exceptional evidence states do not automatically become low Scores;
* Review, Moderation, Scoring, Grading, and Reporting are separate;
* ScoreForm and Quillan records remain externally owned when used as Concord evidence;
* and grading and formal reporting remain outside Concord.

ADR 0014 anticipated a future Standards Result Handoff Projection containing standard-backed Score information.

That projection remains conceptually valid, but it is no longer sufficient as Concord’s complete downstream integration contract.

Meridian must support:

* pure standards-based grading;
* conventional grading;
* hybrid grading;
* repeated observations;
* reassessment;
* evidence-selection policies;
* local and standard-backed producer results;
* non-Grade states;
* Academic Period calculations;
* and formal report snapshots.

A standards-only handoff would prevent Meridian from deliberately considering valid local Concord Scores under an explicit conventional or hybrid policy.

Conversely, treating every published Concord Score as a Grade input would violate Meridian’s ownership of:

* Grade-item membership;
* evidence eligibility;
* standards-evidence selection;
* weighting;
* period membership;
* and Grade calculation.

Concord therefore requires a producer-owned, immutable, revision-addressable academic-result manifest that:

1. preserves Concord-native meaning;
2. exposes sufficient structured information for Meridian;
3. distinguishes standard-backed and local Scores;
4. preserves non-score dispositions;
5. preserves Score and evidence lineage;
6. preserves required Moderation state;
7. remains separate from Core’s Publication Record;
8. remains separate from Meridian’s derived calculations;
9. and can be published without a direct Concord-to-Meridian package dependency.

## Decision

Concord will publish selected academic results through **versioned Concord Academic Result Manifests** registered through the Core typed publication registry.

The normal relationship will be:

```text
Concord Activity
    -> optional Core Academic Work Registration
    -> Concord canonical Activity, Criterion, Scale, Score, and evidence records
    -> immutable Concord Academic Result Manifest revision
    -> immutable Core Publication Record
    -> Core registry catalog
    -> Meridian import
    -> Meridian evidence selection and grading policy
    -> Meridian proficiency, Grade, or report
```

The foundational rule is:

> Concord publishes faithful, versioned projections of its native academic results. Core records and validates publication of exact manifest bytes. Meridian determines whether and how those published results participate in proficiency, Grade, Academic Period, and reporting calculations.

This ADR does not transfer ownership of Concord Scores to Core or Meridian.

This ADR does not make publication equivalent to grading.

This ADR does not authorize Concord to calculate cumulative proficiency or Grades.

## Relationship to Existing Concord ADRs

This ADR does not supersede:

* ADR 0008, which separates Review, Moderation, Scoring, Grading, and Reporting;
* ADR 0010, which establishes that exceptional evidence states are not low Scores;
* ADR 0012, which links ScoreForm and Quillan records without duplication;
* or ADR 0014, which makes standards-based scoring Concord’s primary academic scoring model.

This ADR operationalizes their downstream integration boundary.

ADR 0014’s Standards Result Handoff Projection becomes a standards-specific projection within the broader Concord Academic Result Manifest.

It is no longer the entire cross-module result-publication contract.

## Ownership Boundaries

### Concord owns

Concord owns:

* Activity identity and semantics;
* Activity scoring orientation;
* Activity Focus Standards;
* Criterion definitions;
* Criterion classifications;
* Scoring Scale definitions and revisions;
* Score Records;
* Score targets;
* scorer provenance;
* Score Evidence Links;
* Concord Moderation Records;
* non-score dispositions;
* Score correction and supersession;
* external evidence relationships;
* manifest schema and validation;
* manifest record-set identity;
* manifest revision assignment;
* manifest generation;
* deciding when the published projection has materially changed;
* and the educational meaning of every manifest field.

### Core owns

Core owns:

* Academic Work Registration identity and revision;
* Publication Record identity;
* publication schema version;
* publication-kind vocabulary;
* shared capability vocabulary;
* manifest-path validation;
* manifest-digest validation;
* publication idempotency;
* publication-series supersession;
* publication withdrawal;
* canonical publication registry persistence;
* deterministic publication discovery;
* and the derived registry catalog.

Core does not interpret Concord Scores or calculate educational results from them.

### Meridian owns

Meridian owns:

* Grade-item membership;
* publication eligibility under a grading policy;
* standards-evidence eligibility;
* evidence selection;
* attempt and reassessment selection;
* cross-publication deduplication policy;
* cross-module evidence aggregation;
* standards-proficiency calculation;
* conventional Grade calculation;
* hybrid Grade calculation;
* weighting and category policy;
* minimum-evidence policy;
* Academic Period membership;
* teacher overrides of Meridian-derived results;
* Grade history;
* report definitions;
* report snapshots;
* audience-aware reporting;
* and formal report delivery coordination.

### Dependency direction

The required package dependency direction remains:

```text
pds-concord  -> pds-core
pds-meridian -> pds-core
```

Concord must not require a runtime dependency on Meridian.

Meridian must not require Concord’s private Python implementation to discover or interpret published Concord results.

Cross-module use must rely on:

* Core identities;
* Core Publication Records;
* the public Concord manifest contract;
* public serialized records;
* and optional adapters that preserve ownership.

## Academic Work Registration

A Concord Activity is not automatically registered as academic work.

None of the following alone creates an Academic Work Registration:

* creation of an Activity;
* selection of a standards profile;
* selection of Focus Standards;
* use of `standards_based` scoring orientation;
* use of `mixed` scoring orientation;
* creation of an Artifact;
* completion of Review;
* creation of a Score;
* or generation of printable pages.

Academic Work Registration is an explicit action.

For a registered Concord Activity:

```text
work.module_id = concord
work.class_id  = Activity.class_reference.record_id
work.work_id   = Activity.activity_id
```

The registration must include exactly one matching Activity source `ModuleRecordRef` whose `module_id` is `concord`, whose `record_kind` is `activity`, and whose `record_id` equals `work.work_id`. Additional source records may be included when justified.

Conceptually:

```yaml
work:
  module_id: concord
  class_id: cls_apcsp_p01
  work_id: act_proj_resource_finder_01

source_records:
  - module_id: concord
    record_kind: activity
    record_id: act_proj_resource_finder_01
    contract_version: <approved Concord Activity contract version>
```

The Academic Work Registration’s `producer_contract_version` identifies the applicable public Concord work contract.

The initial Concord `work_kind` should identify the work as a collaborative Activity without attempting to encode every instructional subtype.

A suitable semantic value is:

```text
collaborative_activity
```

The registration’s `academic_intent` uses the Core-controlled vocabulary:

```text
formative
summative
diagnostic
practice
feedback_only
reporting_only
```

The registration’s academic intent is distinct from Concord’s Activity scoring orientation.

### Activity scoring orientation

Concord’s Activity scoring orientation answers:

> What kinds of Concord Score Records may this Activity produce?

Initial orientations remain:

```text
evidence_only
standards_based
mixed
local_criteria_only
```

### Core academic intent

Core’s Academic Work Registration intent answers:

> For what broad academic purpose has this module work been registered?

### Meridian Grade membership

Meridian answers:

> Does this registered work or one of its publications contribute to a particular proficiency, Grade, Academic Period, or report calculation?

These decisions must not be collapsed.

## Registration by Activity Type

### `evidence_only`

An evidence-only Activity is not automatically registered.

The initial Concord Academic Result Manifest contract does not publish raw evidence-only Activities merely because they contain reviewed or moderated evidence.

A future reporting-specific or evidence-publication contract may support that use when a concrete requirement justifies it.

### `standards_based`

A standards-based Activity may be registered when its results are intended for:

* formative standards reporting;
* diagnostic standards reporting;
* summative standards reporting;
* progress reporting;
* or another explicit academic use.

Registration does not guarantee that Meridian will select any Score as standards evidence.

### `mixed`

A mixed Activity may be registered and may publish:

* standard-backed Scores;
* local Scores;
* non-score dispositions;
* and their distinct semantics

within one manifest.

Meridian must not reinterpret local Scores as direct standards results.

### `local_criteria_only`

A local-criteria-only Activity may be registered when its results are intended for legitimate academic grading or reporting.

Its published local Scores:

* are valid producer-native academic results;
* may be considered by a conventional or hybrid Meridian policy;
* and must not be presented as direct standards ratings.

## Concord Academic Result Manifest

A **Concord Academic Result Manifest** is an immutable, machine-readable, producer-owned projection of one exact revision of the publishable academic-result state for one registered Concord Activity.

The manifest is:

* owned by Concord;
* scoped to exactly one `ModuleWorkRef`;
* immutable after publication;
* revision-addressable;
* validated under a public Concord manifest contract;
* and bound to a Core Publication Record through a safe path and SHA-256 digest.

The manifest is not:

* a Core Publication Record;
* a route registration;
* an Artifact;
* a Grade;
* a calculated proficiency result;
* a report;
* a mutable `latest.json` file;
* or a replacement for Concord’s canonical records.

Concord’s canonical records remain authoritative for native semantics.

The manifest is the authoritative published projection for the exact record-set revision it represents.

## Initial Record-Set Scope

The initial integration will use one canonical academic-result record-set series for each registered Concord Activity.

A stable producer-owned `record_set_id` identifies that series.

The `record_set_id` must be:

* lowercase;
* safe under Core identifier rules;
* stable;
* unique within the Activity work context;
* free of student names and direct personal information;
* and independent of display labels or mutable Activity metadata.

A suitable generated form is conceptually:

```text
rs_<opaque-id>
```

The first published manifest uses:

```text
record_set_revision: 1
```

Every material change to the published projection requires a greater positive revision.

Revision numbers need not be contiguous.

Additional specialized Concord record-set series require a later contract or explicit compatibility decision.

## Manifest Envelope

The exact serialized schema belongs to implementation work, but every Concord Academic Result Manifest must make available at least:

```text
manifest_contract_version
record_set_id
record_set_revision
work
source_activity
generated_at
producer_module_id
Activity context
Criterion definitions
Scoring Scale revisions
Score Records
Score supersession relationships
Score Evidence Links or equivalent lineage projections
Moderation state
publication-projection provenance
```

A representative envelope is:

```yaml
manifest_contract_version: concord_academic_result_manifest_v1
record_set_id: rs_8f02a34c
record_set_revision: 2

producer_module_id: concord

work:
  module_id: concord
  class_id: cls_apcsp_p01
  work_id: act_proj_resource_finder_01

source_activity:
  module_id: concord
  record_kind: activity
  record_id: act_proj_resource_finder_01
  contract_version: <approved Activity contract version>

generated_at: 2026-09-29T16:20:00-04:00
```

The exact contract-version identifier is controlled by Concord and must satisfy Core identifier rules.

## Activity Context in the Manifest

The manifest must expose enough Activity context to interpret the published results without reproducing the complete Activity record.

Required Activity context includes:

```text
activity_id
class_id
title snapshot
scoring_orientation
```

When the Activity orientation is `standards_based` or `mixed`, the manifest also includes:

```text
standards_profile_id
ordered focus_standard_ids
```

The title is a historical display snapshot, not identity.

Focus Standard ordering remains meaningful.

A Focus Standard does not itself establish:

* assessment;
* demonstrated performance;
* standards evidence eligibility;
* proficiency;
* or Grade inclusion.

Those states require explicit Score and Meridian policy decisions.

## Criterion Projection

The manifest must expose every Criterion required to interpret an included Score.

For each included Criterion, the manifest must provide:

```text
criterion_id
criterion_set_id where applicable
criterion_kind
definition or durable public definition reference
supported target kinds
status or revision state
```

### Standard-backed Criterion

A standard-backed Criterion must expose:

```text
criterion_kind: standard_backed
standard_id: <exactly one governing Core standard_id>
```

The governing standard must match the Score Record’s direct `standard_id`.

### Local Criterion

A local Criterion must expose:

```text
criterion_kind: local
standard_id: absent
```

Optional alignment standards remain non-governing and may be exposed separately as:

```text
alignment_standard_ids
```

Meridian must not treat those alignment references as direct standards results.

## Scoring Scale Projection

A bare `scoring_scale_id` is not sufficient for independent downstream interpretation.

The manifest must include or publicly resolve the exact immutable Scoring Scale revision used by every included Score.

The scale projection must provide, as applicable:

```text
scoring_scale_id
scale_lineage_id
revision
scale_type
ordered levels
machine values
display labels
level descriptions or meanings
status
```

The manifest must preserve Concord’s native scale.

Concord and Core must not normalize the scale to:

* percentage;
* points;
* four universal proficiency levels;
* letter Grade;
* or another common numeric representation.

Meridian may map a Concord scale to a Meridian proficiency or Grade policy only through an explicit, versioned mapping.

A four-level scale is a supported use case, not a universal Concord or Meridian constant.

## Score Projection

The manifest must preserve each included Score Record’s native meaning.

Each Score projection must make available:

```text
score_record_id
activity_id
optional session_id
target_reference
criterion_id
score_kind
optional standard_id
scoring_scale_id
disposition
conditional value
basis
scorer
scored_at
moderation_complete
current_status
optional supersedes_score_record_id
```

### Standard-backed Score

A standard-backed Score must expose:

```text
score_kind: standard_backed
standard_id: <one governing Core standard_id>
```

The `standard_id` must:

* match the referenced standard-backed Criterion;
* appear in the Activity’s Focus Standards;
* and remain a contextual Concord judgment rather than a mastery determination.

### Local Score

A local Score must expose:

```text
score_kind: local
standard_id: absent
```

Local Scores may be published.

They must not enter the standards-specific result projection.

They may participate in conventional or hybrid Grade calculation only through explicit Meridian policy.

### Non-score dispositions

Initial Concord dispositions remain:

```text
scored
insufficient_evidence
absent
excused
not_observed
not_applicable
deferred
```

When:

```text
disposition: scored
```

the manifest must include a valid value from the exact referenced scale revision.

When:

```text
disposition != scored
```

the manifest must omit the value.

A non-score disposition must not be transformed into:

* zero;
* failure;
* the lowest scale value;
* missing-work penalty;
* or another academic consequence

inside the Concord manifest.

Meridian may apply a consequence only through an explicit policy that preserves the original disposition.

## Current and Superseded Score History

The manifest must preserve enough native Score history for Meridian to distinguish:

* current Score Records;
* superseded Score Records;
* corrected judgments;
* non-score records later replaced by scored judgments;
* and several valid contextual observations.

The initial manifest should be a self-contained snapshot of the publishable Activity result state at its generation time.

It should include the Score records and supersession relationships necessary to understand that state rather than exposing only an unexplained current value.

The manifest must not infer that:

* the latest `scored_at` value always wins;
* the highest value always wins;
* a later Session automatically replaces an earlier Session;
* or a later Score is a reassessment.

Those are Meridian policy questions unless Concord has recorded an explicit native supersession relationship.

## Score Evidence and Lineage Projection

The manifest must preserve deliberate evidence lineage for each published Score.

A Score projection may reference:

* Concord Artifacts;
* Artifact Pages;
* Attachments;
* Activity Events;
* Contribution Claims;
* teacher rationale;
* ScoreForm records;
* Quillan records;
* or another authorized source.

The manifest must not copy complete evidence merely to make it reportable.

For each published Score Evidence Link or equivalent lineage entry, the manifest should expose:

```text
score_evidence_link_id
score_record_id
evidence_kind
source record reference
optional evidence locator
optional subject context
relevance description
optional significance
optional moderation_record_id
status
```

The source record reference must preserve module ownership.

For Concord-owned evidence, a Concord record reference or module-qualified Concord reference may be used.

For sibling-module evidence, the lineage must preserve:

```text
module_id
record_kind
record_id
optional contract_version
```

When Concord knows that the external source was imported or resolved through a Core Publication Record, the lineage may additionally expose:

```text
source_publication_id
```

or another exact Core publication reference approved by the public contract.

That publication reference is optional unless a later integration contract requires it.

## Cross-Producer Double-Counting Risk

A Concord Score may be supported by a ScoreForm or Quillan result.

Meridian may also import the originating ScoreForm or Quillan publication directly.

The two records are not automatically independent evidence.

For example:

```text
ScoreForm result
    -> used as evidence for Concord Score
```

must remain distinguishable from:

```text
ScoreForm result
    + unrelated Concord observation
```

The Concord manifest must therefore expose sufficient source lineage for Meridian to determine that one published result was used in producing another published result.

Meridian owns the policy that decides whether to:

* use both;
* use only the Concord judgment;
* use only the originating producer result;
* treat one as corroboration;
* or apply another explicit relationship rule.

Concord must not silently suppress legitimate lineage merely to simplify Meridian calculations.

Meridian must not assume that two publications are independent merely because they were produced by different modules.

## Moderation Projection

When evidence required Moderation before consequential use, the manifest must expose enough information to establish that the Score was validly supported.

For each included Score, the manifest must make available:

```text
moderation_complete
```

When an active evidence link depends on a Moderation Record, the manifest must preserve:

```text
moderation_record_id
moderation outcome
permitted-use restriction where applicable
qualification where required for interpretation
```

The manifest need not expose unrestricted sensitive Moderation narrative.

It should expose only the minimum structured information required to understand:

* whether required Moderation occurred;
* whether the evidence was permitted for the Score’s use;
* and whether any qualification materially limits interpretation.

Rejected evidence must not remain represented as active support for a consequential Score.

Historical rejected or superseded links may remain available as history when clearly marked.

## Privacy and Data Minimization

A Concord Academic Result Manifest is expected to contain sensitive educational information.

It must include only the information required for:

* result interpretation;
* source identity;
* standards identity;
* scale interpretation;
* evidence lineage;
* Moderation state;
* supersession;
* and downstream policy application.

The manifest must not ordinarily embed:

* source scans;
* full student writing;
* full peer comments;
* unrestricted teacher notes;
* complete Artifact contents;
* detailed Moderation narratives;
* student names;
* family information;
* or unrelated Activity records.

Student and Group identity must use durable references rather than names.

Manifest paths, record-set IDs, publication IDs, and digests must not contain direct personal information.

Publication establishes discoverability, not authorization.

The existence of a Core Publication Record does not authorize every module, user, or report audience to inspect all manifest contents.

Concord privacy rules, workspace authorization, Meridian source-access rules, and report-audience policy remain applicable.

## Publication Kind and Capabilities

A Concord Academic Result Manifest is published through Core as:

```text
publication_kind: academic_result_set
```

An academic-result publication must reference the exact current Academic Work Registration revision at publication time. Later registration revisions do not alter the revision preserved by an existing Publication Record.

The Core Publication Record advertises only supported shared capabilities.

For the initial Concord manifest, applicable capabilities include:

```text
criterion_scores
standards_ratings
moderated_scores
```

Capability declaration must be truthful for the exact manifest revision.

For the initial Concord manifest contract:

* `criterion_scores` is required when any Criterion-level Score projection or non-score disposition is present;
* `standards_ratings` is required when any standard-backed Score projection or standard-backed non-score disposition is present;
* when `standards_ratings` is declared, the Standards Result Projection is required, nonempty, and exactly represents the standard-backed subset;
* `moderated_scores` is required when interpretation of an included consequential Score depends on projected Moderation state;
* and each capability must be omitted when its represented feature is absent.

### `criterion_scores`

The publication includes Concord Criterion-level Score Records.

This capability applies to standard-backed and local Scores.

### `standards_ratings`

The publication includes one or more direct standard-backed Score Records or non-score dispositions tied to governing standards.

This capability must not be declared solely because the Activity has Focus Standards or local alignment metadata.

### `moderated_scores`

The publication exposes Score results whose interpretation includes applicable Moderation state.

This capability does not imply that every Score required Moderation.

Capabilities:

* aid discovery and compatibility;
* do not define the complete manifest body;
* do not guarantee every target has a result;
* do not authorize access;
* and do not establish Grade eligibility.

## Core Publication Record

After Concord creates and durably closes an immutable manifest revision, it requests publication through Core.

The Core Publication Record must identify:

```text
schema_version
record_type
publication_id
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
published_at
academic_work_registration_revision
optional supersedes_publication_id
```

For initial Concord use, `source_record` is required and must identify the same Activity represented by the Publication Record’s `work`, the manifest’s `source_activity`, and the manifest’s `activity_context`.

```yaml
source_record:
  module_id: concord
  record_kind: activity
  record_id: act_proj_resource_finder_01
  contract_version: <approved Activity contract version>
```

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

The Core Publication Record is not a copy of the manifest.

It does not contain student result arrays or Score values.

## Manifest Storage

Published manifests must be stored beneath the exact Concord Activity work root.

A representative layout is:

```text
classes/
  <class_id>/
    modules/
      concord/
        work/
          <activity_id>/
            exports/
              manifests/
                <record_set_id>/
                  <record_set_revision>.json
```

The manifest path must be:

* workspace-relative;
* normalized;
* inside the workspace;
* inside the referenced Concord work root;
* outside Core-owned registry storage;
* and immutable after publication.

A mutable convenience path may exist for teacher workflows, such as:

```text
exports/latest.json
```

but it must not be the canonical target of a Core Publication Record.

## Publication Workflow

The publication workflow must occur in this order:

1. Concord validates the Activity and its publishable native records.
2. Concord determines the exact result-set projection.
3. Concord assigns the next valid `record_set_revision`.
4. Concord generates the complete manifest bytes.
5. Concord validates the manifest against the public manifest contract.
6. Concord writes the manifest to a new revision-addressed path.
7. Concord durably closes the manifest.
8. Concord requests or calculates the SHA-256 digest.
9. Concord submits the publication request to Core.
10. Core validates the Academic Work Registration relationship.
11. Core validates the publication envelope.
12. Core verifies the manifest path.
13. Core verifies the manifest digest.
14. Core exclusively creates the immutable Publication Record.
15. Core updates or later rebuilds the derived catalog.
16. Concord records or displays the publication result for teacher inspection.

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

## Manifest Revision

A new manifest revision is required when the published projection changes materially.

Examples include:

* creation of a new publishable Score Record;
* supersession of a published Score;
* correction of a Score target;
* correction of a governing standard;
* change from a non-score disposition to a scored judgment;
* change from a scored judgment to a valid non-score disposition;
* addition or removal of a consequential Score Evidence Link;
* a Moderation decision that changes whether evidence may support a Score;
* correction of published evidence lineage;
* correction of an included Criterion or Scale projection;
* or correction of a material manifest defect.

A new manifest revision is not necessarily required for every Concord-native change.

A change requires republication when it changes the exact projection that downstream consumers are expected to import.

The manifest should preserve generation provenance and an optional revision reason sufficient to distinguish:

* native result change;
* evidence-lineage correction;
* Moderation correction;
* projection correction;
* privacy correction;
* or manifest-contract migration.

## Publication Supersession

A later Core Publication Record may supersede an earlier Publication Record in the same Concord result-set series.

Supersession must preserve:

```text
same producing module
same ModuleWorkRef
same publication_kind
same record_set_id
greater record_set_revision
explicit predecessor publication_id
```

The earlier Publication Record and manifest remain immutable and available for:

* audit;
* reproducibility;
* historical Meridian calculations;
* and previously issued report snapshots.

The current publication head must be derived from explicit supersession relationships.

It must not be inferred from:

* filename;
* file modification time;
* highest revision alone;
* publication timestamp alone;
* or directory order.

## Native Score Supersession and Publication Supersession

Concord Score supersession and Core Publication supersession are separate relationships.

For example:

```text
Concord Score Record 2
    -> supersedes Concord Score Record 1
```

is Concord-native judgment history.

Separately:

```text
Core Publication Record B
    -> supersedes Core Publication Record A
```

is manifest-publication history.

A new Concord Score does not itself create a Core Publication Record.

A new Core Publication Record does not itself supersede any Concord Score.

The new Concord manifest explains native Score state.

The Core publication series explains which immutable manifest revisions were published.

Neither Core nor Meridian may infer one supersession relationship solely from the other.

## Publication Withdrawal

Core withdrawal is used when a published manifest revision should no longer be selected as current or ordinarily usable.

Withdrawal does not alter publication-series structure.

When the withdrawn Publication Record is the unsuperseded series head, an earlier predecessor does not become current or ordinarily selectable again. The series has no currently selectable publication until a new successor is published.

A corrected successor must explicitly supersede the withdrawn head.

Withdrawing a historical non-head publication does not change the existing series head.

A withdrawal may be appropriate when:

* the manifest was published from invalid native state;
* the manifest contains a material privacy defect;
* the manifest digest or path relationship is invalid;
* the publication selected the wrong Activity;
* the projection is materially misleading;
* or no immediate corrected replacement is ready.

Withdrawal:

* does not delete the Publication Record;
* does not delete the manifest;
* does not delete Concord-native records;
* does not alter earlier Meridian calculations;
* and does not erase historical use.

If corrected data becomes available, Concord creates:

1. a new immutable manifest revision;
2. a new Core Publication Record;
3. and the appropriate supersession relationship.

A withdrawn Publication Record must not be restored by mutation.

## Academic Periods

Concord must not assign authoritative Academic Period membership to:

* Activities;
* Score Records;
* evidence;
* manifest revisions;
* or Publication Records.

Concord preserves native dates such as:

* Activity dates;
* Session dates;
* evidence timestamps;
* Review timestamps;
* Moderation timestamps;
* and `scored_at`.

Those dates do not universally determine:

* marking-period membership;
* semester membership;
* reassessment period;
* Grade-item period;
* or reporting-period inclusion.

Meridian applies explicit period-membership policy using Core-owned Academic Period calendars and exact calendar revisions.

The initial Concord manifest therefore does not require an `academic_period_id`.

A later integration may expose optional nonauthoritative scheduling context, but it must not replace Meridian’s period-membership decision.

## Meridian Consumption

Meridian consumes Concord publications through Core.

A Meridian import should preserve:

* Core Publication Record ID;
* exact manifest digest;
* manifest contract version;
* record-set identity;
* record-set revision;
* source Academic Work Registration revision;
* source Activity reference;
* and import time.

Meridian must validate that:

* the publication kind is compatible;
* the manifest contract version is supported;
* declared capabilities are supported;
* the manifest digest matches;
* the publication has not been withdrawn;
* and access is authorized.

Meridian then applies explicit policy to determine:

* whether the publication is eligible;
* which Scores are eligible;
* which standard-backed Scores count as standards evidence;
* whether local Scores may participate in a conventional or hybrid Grade;
* which repeated observations are selected;
* how reassessment is handled;
* which Academic Period applies;
* and whether any result appears in a formal report.

Meridian must preserve Concord’s source meaning.

It must not:

* mutate Concord Scores;
* convert local Scores into standards ratings;
* copy Group Scores to members;
* convert non-score dispositions into zero without explicit policy;
* assume that the newest Score always wins;
* assume that the highest Score always wins;
* or assume publication means Grade inclusion.

## Meridian Overrides

A Meridian override and a Concord Score revision are different operations.

A Concord Score revision is appropriate when the underlying teacher-approved Criterion judgment changes.

A Meridian override is appropriate when the producer-native Concord Score remains valid but an authorized person changes a Meridian-derived:

* evidence-selection decision;
* calculated proficiency result;
* Grade-item result;
* Academic Period Grade;
* or another supported derived result.

A Meridian override must not rewrite the Concord manifest or Score Record.

A change to the underlying Concord judgment requires:

```text
new Concord Score
    -> new manifest revision
    -> new Core Publication Record
```

A change only to a Meridian-derived result remains Meridian-owned.

## Relationship to Formal Reports

Concord Academic Result Manifests are producer publications.

They are not formal reports.

Meridian may use one or more Concord publications to produce:

* standards-proficiency reports;
* assignment progress reports;
* marking-period reports;
* cumulative course reports;
* teacher dashboards;
* student-facing reports;
* parent or guardian reports;
* or administrative reports.

A Meridian report snapshot remains distinct from:

* the Concord manifest;
* the Core Publication Record;
* the Concord Score;
* and the Meridian calculation result.

A report snapshot must preserve its own:

* source Publication Record IDs;
* policy versions;
* Academic Period calendar revision;
* audience;
* generation provenance;
* and supersession state.

A later Concord publication must not silently rewrite a previously issued Meridian report snapshot.

## Failure and Recovery

Concord publication workflows must report distinct failure states.

Possible failures include:

* Activity is not registered;
* registration revision is stale;
* native Concord records are invalid;
* manifest validation fails;
* manifest path is unsafe;
* manifest already exists with conflicting bytes;
* manifest digest does not match;
* publication capability is unsupported;
* Core Publication Record creation conflicts;
* predecessor publication is not the current applicable head;
* publication was already withdrawn;
* catalog update failed after canonical publication;
* or the installed Core version does not support the required registry contract.

Repair may:

* regenerate an unpublished manifest;
* create a new manifest revision;
* retry an idempotent publication request;
* rebuild the Core catalog;
* or create an explicit withdrawal and replacement.

Repair must not:

* modify published manifest bytes;
* reuse a record-set revision for different content;
* alter a Core Publication Record;
* infer a new publication from an existing file;
* change a manifest digest to match mutated bytes;
* rewrite native Score history;
* or silently remove evidence lineage.

## Implementation Compatibility

The architectural decision may be adopted before Concord implements runtime publication.

Runtime implementation must wait until the required Core registry APIs are:

* released;
* explicitly stabilized for producer use;
* or deliberately consumed under an approved coordinated development contract.

Concord must not claim compatibility with an unreleased Core API merely because the code exists on Core’s development branch.

The implementation must declare:

* supported Core package versions;
* supported Core publication schema versions;
* supported Academic Work Registration schema versions;
* supported Concord manifest contract versions;
* and supported shared capabilities.

A future Concord producer-compatibility profile or entry point may advertise those values.

That profile must remain separate from the PDS2 route-dispatch profile unless Core explicitly defines a combined public contract.

## Consequences

### Positive consequences

#### Meridian can discover Concord results safely

Meridian can find published Concord result sets through Core without:

* recursively crawling Concord directories;
* importing Concord internals;
* guessing filenames;
* or treating mutable files as authoritative.

#### Concord retains native authority

Concord remains authoritative for:

* Score semantics;
* Criterion semantics;
* target identity;
* scale interpretation;
* Moderation;
* evidence lineage;
* non-score dispositions;
* and native supersession.

#### Core remains module-neutral

Core stores:

* registration metadata;
* publication metadata;
* paths;
* digests;
* capabilities;
* and lifecycle relationships

without calculating Grades or interpreting educational meaning.

#### Meridian remains policy-driven

Publication does not bypass Meridian’s policies for:

* Grade membership;
* evidence eligibility;
* reassessment;
* standards aggregation;
* Academic Periods;
* and reporting.

#### Standards and local results remain distinct

One manifest may expose both while preserving:

```text
standard-backed Score != local Score
```

This supports standards-based, conventional, and hybrid grading without false standards mappings.

#### Historical results remain reproducible

Immutable manifest revisions and Publication Records preserve the exact producer state used by earlier Meridian calculations and reports.

#### Cross-producer lineage remains visible

Meridian can identify when a Concord Score used ScoreForm or Quillan evidence and can apply an explicit policy rather than accidentally double-counting related results.

### Costs

#### Concord requires a public manifest contract

Concord must define, version, validate, and maintain a stable producer-facing result schema.

#### Publication adds another versioning axis

The system must distinguish:

* Concord native record revisions;
* Concord Score supersession;
* Concord manifest contract version;
* manifest record-set revision;
* Core Publication Record schema version;
* Academic Work Registration revision;
* and Meridian policy versions.

#### Immutable publication requires deliberate workflows

A published manifest cannot be edited in place.

Corrections require new manifest and Publication Record revisions.

#### Privacy projection requires discipline

Concord must expose enough information for Meridian without turning the manifest into a duplicate evidence repository.

#### Cross-module adapters remain necessary

Meridian may require producer-specific adapters or mappings for Concord Scoring Scales and other native semantics.

## Alternatives Considered

### Direct Concord-to-Meridian package dependency

Under this alternative, Meridian imports Concord’s private implementation or queries Concord through an implementation-specific API.

Rejected because it would:

* couple sibling packages;
* make independent installation difficult;
* bypass Core discovery;
* make historical imports less reproducible;
* and expose Meridian to Concord’s private storage layout.

### Mutable `latest.json` handoff

Under this alternative, Concord maintains one mutable current-results file.

Rejected because an earlier consumer reference could later resolve to different bytes.

It would not preserve:

* exact revision identity;
* digest integrity;
* supersession;
* withdrawal;
* or reproducible report provenance.

### Core-owned universal score schema

Under this alternative, Core normalizes Concord, ScoreForm, and Quillan results into one shared numeric result.

Rejected because it would erase distinctions among:

* Criterion Scores;
* standards ratings;
* local Scores;
* Group Scores;
* individual Scores;
* non-score dispositions;
* points;
* rubric levels;
* and narrative or moderated evidence.

Core must remain a shared registry, not the grading engine.

### Standards-only publication

Under this alternative, Concord publishes only its Standards Result Handoff Projection.

Rejected as the complete integration because Meridian must support conventional and hybrid policies that may deliberately consider local Concord Scores.

The standards-only projection remains useful as a subset.

### Publish every Concord native record independently through Core

Under this alternative, every Score, Criterion, Scale, Review, and Moderation Record becomes its own Core Publication Record.

Rejected because it would:

* create excessive registry volume;
* expose unnecessary sensitive metadata;
* fragment one coherent Activity result set;
* and turn Core into a duplicate native-record index.

Core publishes the manifest as one exact work-scoped result set.

### Automatic publication whenever a Score changes

Under this alternative, every native Score write immediately creates a new manifest and Core Publication Record.

Rejected as an architectural requirement because publication is a deliberate producer workflow.

Implementations may offer automatic or prompted publication when policy permits, but:

* publication failure must not invalidate the native Score;
* incomplete transactional state must not be published;
* and teachers must be able to distinguish saved native work from published cross-module results.

### Publication implies Grade inclusion

Rejected because Grade-item and evidence membership belong to Meridian.

A publication may be:

* formative;
* diagnostic;
* practice;
* feedback-only;
* reporting-only;
* summative;
* or excluded under a particular Meridian policy.

### Concord assigns Academic Period membership

Rejected because Core owns period definitions and Meridian owns membership policy.

Concord dates provide context but do not universally determine marking-period or reassessment placement.

### Meridian infers cross-producer independence

Under this alternative, Meridian treats a Concord Score and its ScoreForm or Quillan source as unrelated merely because they come from different publications.

Rejected because that can double-count the same underlying evidence.

Concord must expose lineage, and Meridian must apply an explicit relationship policy.

## Follow-Up Questions

This ADR establishes architecture and ownership. Later contracts or implementation issues must resolve the following.

### Manifest schema

* What exact JSON schema represents `concord_academic_result_manifest_v1`?
* Are Criteria and Scoring Scales embedded as snapshots or exposed through separately versioned public Concord records?
* Which fields are required for every Score projection?
* How are validation warnings represented?
* Does each manifest include all historical Scores or only the history necessary to interpret current state?

### Publication inclusion

* Which native Score lifecycle states are publishable?
* Are draft or provisional Score Records excluded?
* How are intentionally unpublished Scores represented to the teacher?
* Can one Activity maintain several specialized result-set series in a future version?

### Evidence lineage

* What exact value object represents a Concord-owned evidence source?
* How are Core Publication Record IDs attached to external ScoreForm or Quillan evidence when known?
* How does Meridian detect equivalent or overlapping external evidence?
* What privacy fields accompany lineage references?

### Scoring Scale interpretation

* What public scale contract must Meridian support?
* How are ordinal, categorical, numeric, or rubric scales distinguished?
* How are historical scale revisions resolved?
* How are producer scales mapped to Meridian proficiency scales?

### Registration workflow

* When is Academic Work Registration created?
* Which teacher interface selects `academic_intent`?
* Which Activity changes require a new registration revision?
* How is registration cancellation distinguished from Activity cancellation?

### Publication workflow

* Is publication manual, prompted, policy-driven, or optionally automatic?
* How are partial publication successes shown?
* How does Concord display current, superseded, and withdrawn publication state?
* What commands or interfaces support republishing and withdrawal?

### Compatibility

* What public producer profile advertises manifest contract versions and capabilities?
* How does Concord detect an unsupported Core registry version?
* How does Meridian report an unsupported Concord manifest?
* What cross-repository synthetic fixtures are required?

### Authorization and privacy

* Who may register academic work?
* Who may publish or withdraw Concord result sets?
* Who may inspect the manifest?
* Which sensitive Score rationale or Moderation fields are excluded?
* How are authorized deeper links back to Concord evidence provided?

### Evidence-only reporting

* Does a later contract permit evidence-only Activities to publish a reporting projection?
* Would such a projection remain `academic_result_set` or require a later Core publication kind?
* How would that projection avoid implying Score or Grade eligibility?

### Testing

* How are immutable manifest bytes verified?
* How are digest mismatch and conflicting revision reuse tested?
* How are publication supersession and withdrawal tested?
* How are local and standard-backed Scores tested independently?
* How is non-score omission of `value` tested?
* How is cross-producer evidence lineage tested?
* How is accidental double-counting prevented in Meridian integration fixtures?
* How are historical Meridian calculations reproduced from older Concord publications?

## Required Documentation Changes

Adoption of this ADR requires revisions to:

* `docs/design/conceptual-data-contracts.md`;
* `docs/design/initial-concord-domain-model.md`;
* `docs/design/cross-case-requirements.md`;
* `docs/design/pds-core-integration-requirements.md`;
* `docs/concord-conceptual-design-revised.md`;
* `docs/decisions/0008-separate-review-moderation-scoring-grading-and-reporting.md`;
* `docs/decisions/0014-make-standards-based-scoring-the-primary-concord-scoring-model.md`;
* and the representative examples under `docs/design/examples/`.

The changes must:

1. define the Concord Academic Result Manifest;
2. make the existing Standards Result Handoff Projection a standards-specific subset;
3. add Academic Work Registration requirements;
4. add Core Publication Record requirements;
5. define publication revision, supersession, and withdrawal;
6. preserve local Score publication without standards reinterpretation;
7. preserve external evidence lineage;
8. preserve the distinction between Score revision and Meridian override;
9. and validate all four Activity scoring orientations against the new publication boundary.

## Decision Summary

Concord will not become a grading or reporting module.

Concord will publish faithful, immutable, revision-addressable academic-result manifests through Core.

Core will make those exact manifest revisions discoverable without interpreting them.

Meridian will determine whether and how the published results contribute to:

* standards proficiency;
* Grade-item results;
* Academic Period Grades;
* cumulative Grades;
* and formal reports.

The resulting boundary is:

```text
Concord creates contextual teacher judgments.
Core registers and publishes exact producer projections.
Meridian applies grading and reporting policy.
```
