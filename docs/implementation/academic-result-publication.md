# Concord Academic Result Publication

## Status

Implemented for issue #31 against the released `pds-core` v0.6.x producer
contracts. This document describes Concord's producer-owned academic-result
publication boundary. It does not define the consumer-neutral reader reserved
for issue #32 or the full installed Activity-to-publication acceptance reserved
for issue #33.

## Ownership boundary

Concord owns the educational meaning of the Activity, Criteria, Scales, Scores,
Score Evidence Links, Moderation, native supersession history, and the Concord
Academic Result Manifest. Core owns Academic Work Registration, Publication
Records, Publication Withdrawals, publication identity/timestamps, manifest
path and digest binding, canonical registry persistence, compatibility
metadata, and the derived academic catalog.

Meridian remains the owner of Grade-item membership, Academic Period
membership, evidence/attempt selection, scale mapping, proficiency/mastery
policy, weighting, Grade calculation, overrides, cross-publication
deduplication, and reporting. Concord publication does not calculate or imply
those results.

## Stable public identities

The v1 publication boundary uses these exact Concord contract identities:

```text
module_id                    = concord
display_name                 = Concord
academic work contract       = concord_academic_work_v1
Activity source kind         = activity
Activity source contract     = concord_activity_v1
manifest record type         = concord_academic_result_manifest
manifest contract            = concord_academic_result_manifest_v1
record-set ID                = academic_results
Core publication kind        = academic_result_set
```

For one Activity the shared work identity is:

```text
ModuleWorkRef(
    module_id = concord,
    class_id  = <Activity class_id>,
    work_id   = <Activity activity_id>,
)
```

The required source declaration is exactly:

```text
ModuleRecordRef(
    module_id        = concord,
    record_kind      = activity,
    record_id        = <Activity activity_id>,
    contract_version = concord_activity_v1,
)
```

The Activity source reference declares identity and contract version; it does
not create a second mutable Activity document.

## Explicit Academic Work Registration

Registration is explicit teacher academic intent. Activity creation, Focus
Standard selection, Score entry, Review, or Moderation never registers an
Activity automatically.

Concord maps registration to Core with:

```text
producer_contract_version = concord_academic_work_v1
work_kind                  = collaborative_activity
source_records             = exactly the versioned Activity reference
```

The teacher selects Core's exact academic-intent vocabulary independently of
Concord scoring orientation:

```text
formative
summative
diagnostic
practice
feedback_only
reporting_only
```

The teacher also selects Core's registration lifecycle independently of
Activity lifecycle:

```text
planned
active
closed
cancelled
```

Registration updates require the exact expected current registration revision.
Earlier revisions remain immutable. A later Activity title change does not
silently rewrite Core registration metadata.

## Publishability and read-only preview

Manifest generation requires an existing Core class, exact current Activity,
valid native graph, explicit current registration, non-`evidence_only` scoring
orientation, at least one Score Record, exact Criterion/Scale interpretation,
valid standards relationships, valid evidence lineage, satisfied Moderation,
and publication-safe public text.

`preview_academic_result_manifest(...)` performs the same semantic projection
and validation needed for generation but does not create producer manifest
bytes. The direct CLI and teacher menu use this path for readiness review.
Simply opening the Publication menu or inspecting readiness does not register,
generate, publish, supersede, withdraw, or rebuild the catalog.

## Manifest v1 schema

The top-level `concord_academic_result_manifest_v1` contract is closed and
contains:

```text
record_type
contract_version
producer_module_id
generated_at
record_set
work
source_activity
projection
activity_context
criterion_sets
criteria
scoring_scales
scores
score_evidence_links
moderation_records
standards_result_projection
privacy
```

Unknown top-level fields are rejected. The manifest is self-contained for the
Concord Score semantics it publishes without requiring private Concord storage.

### Activity context

The projection preserves Activity/work identity, title snapshot, scoring
orientation, standards profile, ordered Focus Standards, and exact selected
Criterion Set revisions. Unrelated Activity notes, packet/UI configuration, and
private operational metadata are excluded.

### Criterion Sets and Criteria

Every Score's exact Criterion is projected with the exact immutable Criterion
Set revision required to interpret it. Standard-backed Criteria preserve one
governing Core `standard_id`; local Criteria preserve the absence of a governing
standard. Alignment metadata on a local Criterion never creates direct
standards semantics.

### Scoring Scales

Every included Score's exact immutable Scale revision and levels are projected.
Scale machine values remain type-sensitive. In particular:

```text
1 != 1.0 != "1" != true
```

Concord does not normalize native Scale values to percentages, letter grades,
points, or universal proficiency.

### Scores and native history

V1 includes all valid Score Records in the Activity snapshot, including
historical Score revisions needed to reproduce current state. Each Score keeps
its exact target, Criterion, Scale, disposition, value when scored, basis,
scorer identity, scored time, Moderation-complete state, native predecessor,
and an explicit `current` or `superseded` state derived only from the native
supersession chain.

A `concord_group` Score remains a Group Score. Publication never expands Group
membership into student Scores or infers a target from Author, Subject,
evidence, Review, or Moderation context.

Non-score dispositions remain valueless:

```text
insufficient_evidence
absent
excused
not_observed
not_applicable
deferred
```

They are never serialized as zero, the lowest Scale level, failure, or an
inferred missing-data value.

### Evidence and external lineage

Score Evidence Links preserve exact Concord Artifact/Page identity and external
producer ownership. External evidence keeps its owner, evidence kind, exact
record ID/contract, immutable source version, and exact Core Publication
Reference when one is present. A referenced Core Publication is re-verified for
existence, lineage, and manifest path/digest integrity before it is retained in
the Concord projection.

Concord does not import ScoreForm or Quillan to interpret private producer
state, does not copy source evidence bytes, and does not replace an exact source
revision with a later logical equivalent.

### Moderation

When an included evidence use depends on Moderation, the exact minimal
Moderation semantics required to interpret that use are projected: identity,
evidence and Subject scope, status, permitted use, necessary safe qualification,
native predecessor, and current/superseded state. Moderation rationale is not
published.

### Standards result projection

The Standards Result Projection is a relational subset of the Score projection.
Every standard-backed Score appears exactly once with its governing
`standard_id`; local Scores never appear there. The Score object remains the
authoritative target/value/disposition/Scale representation.

## Capability derivation

Capabilities are derived from the exact manifest contents:

```text
criterion_scores   any valid Concord Score Record exists
standards_ratings  at least one standard-backed Score exists
moderated_scores   interpretation of an included consequential Score depends
                   on projected Moderation
```

Concord does not advertise `points`, `question_evidence`, or
`multiple_attempts` in manifest v1.

## Privacy and data minimization

The manifest uses a strict allowlist and a resolved effective privacy policy.
Publication means discoverability, not authorization.

V1 excludes source scan bytes, rendered pages, complete student work, Artifact
contents, peer comments, unrestricted Review/teacher notes, student names,
family information, sensitive medical/disability/counseling/disciplinary
narrative, credentials/secrets, local machine paths, and unrelated Concord
records. It also explicitly excludes:

```text
ScoreRecord.rationale
StatusReason.note
ModerationRecord.rationale
EvidenceLocator.note
```

Required public semantic display text passes Concord's publication-safe text
validation. If a required semantic projection cannot be represented safely and
exactly, generation fails rather than weakening privacy or changing meaning.

## Semantic projection digest and revision policy

Each manifest records the exact source Concord snapshot revision plus a
producer-owned SHA-256 semantic projection digest. The semantic digest excludes
envelope values that naturally change between otherwise identical projections,
including manifest revision, generation time, source snapshot revision,
generator, revision reason, and the digest itself.

An unrelated native change may advance the Concord snapshot while leaving the
semantic digest unchanged; in that case Concord reuses the existing producer
manifest head. A material public change creates the next immutable producer
manifest revision. Material changes include Score/evidence/Moderation
revisions, target or Scale corrections, public Criterion/Scale semantic changes,
privacy changes, and manifest-contract migration.

Producer revision numbers are immutable positive identities. Concord never
renumbers history merely to remove a gap.

## Canonical JSON and producer storage

Manifest bytes are deterministic UTF-8 JSON with no BOM, deterministic mapping
and array order, finite JSON numbers only, and one final LF. Platform line
endings do not affect the bytes.

Immutable producer manifests live under the exact Activity work root:

```text
classes/<class_id>/modules/concord/work/<activity_id>/
  exports/manifests/academic_results/
    1.json
    2.json
    ...
```

Core stores the workspace-relative forward-slash path and SHA-256 of the exact
manifest bytes. Published bytes are never modified. An existing revision with
identical bytes may reconcile as existing; the same revision with different
bytes is an integrity error. No mutable `latest.json` is required.

## Publication producer profile

The installed wheel declares the independent entry point:

```toml
[project.entry-points."paper_data_suite.publication_producers"]
concord = "concord.pds_publication:get_publication_producer_profile"
```

The metadata-only provider advertises Core Publication Record schema `1`,
`concord_academic_work_v1`, publication kind `academic_result_set`, manifest
contract `concord_academic_result_manifest_v1`, capabilities
`criterion_scores`, `standards_ratings`, and `moderated_scores`, and the required
versioned Activity source. Missing or unversioned sources are not permitted.

This profile is separate from the PDS2 routing `ModuleProfile` exposed through
`paper_data_suite.modules`. Importing/discovering the publication profile does
not resolve or mutate a workspace and does not require a sibling PDS package.

## First publication and replay

First publication generates or reuses the exact current producer manifest,
loads the explicit current registration, derives exact capabilities, builds a
Core `PublicationManifestRequest`, and calls Core
`publish_manifest_revision(...)`.

Core owns the Publication Record ID and timestamp. Concord then reloads the
canonical record, verifies work/source/record-set/registration/capability/path
and digest agreement, re-verifies exact manifest bytes through Core, evaluates
compatibility against its own producer profile, rebuilds the derived academic
catalog, and verifies the exact catalog row.

An identical replay reconciles to the existing Core Publication Record. A
different interpretation of the same logical producer revision is a conflict or
integrity failure, never a second publication meaning for that revision.

## Supersession

A material public change creates or reuses the next producer manifest revision.
Publication supersession requires the explicit expected current Core
publication ID and calls Core `supersede_manifest_revision(...)`. The successor
preserves work, publication kind, and `academic_results` series identity,
advances the record-set revision, and explicitly names
`supersedes_publication_id`.

Currentness is never inferred from timestamps, IDs, filenames, manifest revision
ordering, or catalog row ordering. Previous Core Publication Records and
producer manifest bytes remain immutable.

## Withdrawal and corrected republication

Withdrawal uses Core `PublicationWithdrawalRequest` and
`withdraw_publication(...)`. It does not delete or rewrite native Concord
records, producer manifests, Publication Records, or publication-series
structure. Withdrawing the structural series head leaves no current selectable
publication and never reactivates a predecessor.

A corrected publication after withdrawal requires a material new producer
manifest revision and a new Core Publication Record that explicitly supersedes
the withdrawn structural head. Withdrawal reason is deliberate Core operational
metadata, not copied from Score or Moderation narrative.

## Catalog discovery and reconciliation

Core's academic catalog is disposable derived state. Canonical registration,
Publication Record, and Withdrawal JSON remain authoritative.

Concord uses Core `rebuild_academic_catalog(...)` and
`query_publication_catalog(...)` with `PublicationCatalogQuery`; it never writes
SQLite directly or discovers publications by crawling work directories. Query
filters include exact class/work identity, publication kind, `academic_results`
record set, required capabilities, and Core publication state:

```text
current
series_heads
historical
withdrawn
all
```

Producer-series status distinguishes producer manifest head, structural Core
publication head, head Withdrawal, current selectable publication, current
registration revision, catalog availability, and catalog rows. Catalog rows are
reconciled against canonical Core state and contradictory derived state is
rejected.

## Partial success and recovery

Producer bytes and Core registry state are separate durable systems. If a Core
publication/withdrawal is durable but post-write verification or catalog
reconciliation fails, Concord returns structured partial success describing the
canonical durable state and the required reconciliation action.

Safe recovery replays the exact operation or rebuilds/reconciles the catalog.
It never mutates published bytes, reuses one revision for different content,
changes a digest to bless modified bytes, deletes Core history, fabricates a
current pointer, drops lineage, or creates a duplicate Publication Record merely
because catalog verification failed.

## Direct CLI

The noninteractive publication family is:

```text
concord publication register
concord publication registration-show
concord publication registration-update
concord publication manifest-preview
concord publication manifest-generate
concord publication manifest-list
concord publication manifest-show
concord publication publish
concord publication supersede
concord publication withdraw
concord publication series-show
concord publication catalog-list
concord publication catalog-rebuild
```

Exit codes retain the Concord contract: `0` success, `1` ordinary
validation/read/write/integrity failure, `2` usage, `3` stale expected
revision/head or lock conflict, and `4` structured partial success. List and
status output stays compact; exact manifest inspection exposes only the already
publication-safe manifest projection.

## Teacher Publication menu

Each opened Activity exposes **Publication** immediately after **Scoring**. The
surface provides registration status/create/update, read-only readiness preview,
immutable generation, publication history/status, first publish, explicit
supersession, exact withdrawal, catalog discovery/status, and catalog rebuild.

Opening the menu performs no publication mutation. Before generation or publish,
Concord shows the exact work/registration/source snapshot, record-set revision,
Score/current/history/standard/local/non-score/moderation counts, capabilities,
manifest path/digest when available, predecessor publication when applicable,
and a privacy warning. The menu explicitly states:

```text
Publication does not calculate a Grade or proficiency.
Group Scores remain Group Scores.
```

Writes require deliberate confirmation words `REGISTER`, `GENERATE`, `PUBLISH`,
`WITHDRAW`, or `REBUILD`. H/B/M/Q navigation and stale-state Reload behavior
remain unchanged; Reload re-reads state and never force-writes or silently
retries.

## Producer-management readers and issue boundaries

Issue #31 includes deterministic producer-management readers for exact manifest
revisions/head/digest, Core publication series, Withdrawal state, current
selectable publication, registration state, and catalog agreement. These are
not the final consumer-neutral manifest/artifact reader promised by Issue #32.

Issue #33 owns the full clean-wheel Activity-to-publication end-to-end
acceptance. Issue #31 limits installed acceptance to proving that the built wheel
ships and exposes exactly one valid Concord publication producer profile without
workspace mutation or sibling-module dependencies.

No Meridian adapter, portfolio projection, consumer target policy, Grade,
proficiency, mastery, Academic Period membership, weighting, or report logic is
implemented by this publication boundary.
