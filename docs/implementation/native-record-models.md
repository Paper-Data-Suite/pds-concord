# Native record models and validation

**Status:** Implemented for the v0.2.0 foundational in-memory contract

Concord provides immutable, side-effect-free Python models for the teacher-local
Activity slice. This layer defines semantic records and validates them; it does
not discover a workspace, choose storage paths, write files, register PDS2
routes, publish results, or calculate grades.

## Public API

Supported value objects and records are imported from `concord.models`. The
package covers:

- Activity, Session, Group, Membership, Role, and Responsibility records;
- Artifact Instance and Artifact Page identity plus independent Author and
  Subject associations;
- Artifact Review and evidence Moderation;
- Criterion Set, Criterion, immutable Scoring Scale revision and Scale Level;
- Score Record, Score Evidence Link, and Correction Record; and
- typed participant, actor, subject, score-target, evidence, provenance,
  effective-context, privacy, status-reason, publication, and Concord-record
  references.

Core-owned identities use `pds_core.routing_models.ModuleRecordRef` and
`ModuleWorkRef`. In particular, `Activity.work_reference` derives a Concord work
identity whose `work_id` is the Activity ID; it does not persist a second work
identity.

Exact record-body conversion is available from `concord.model_conversion`:

```python
from concord.model_conversion import record_from_dict, record_to_dict
```

Graph validation is available from `concord.model_validation`:

```python
from concord.model_validation import (
    ConcordRecordGraph,
    collect_core_standards_issues,
    collect_record_graph_issues,
    validate_core_standards,
    validate_record_graph,
)
```

## Structural and graph validation

Every model is a frozen, slotted standard-library dataclass. Construction
normalizes caller iterables into tuples and rejects invalid identifiers,
uncontrolled values, empty required text, duplicate ordered identifiers,
non-finite values, naive timestamps, and invalid conditional fields. A record
that fails these local rules raises `ConcordModelError`.

Rules needing related records are evaluated over an immutable
`ConcordRecordGraph`. Collection rejects duplicate `(record_kind, record_id)`
identities. Validation checks Activity and Effective Context boundaries, Group
ancestry and assignment agreement, Artifact/Page ownership and routes,
Author/Subject independence, Review and Moderation references, Criterion Set
membership, exact Scale values, Score basis and evidence cardinality, target
resolution, source evidence lineage, correction agreement, and acyclic,
unbranched supersession chains.

`collect_record_graph_issues` returns every `ValidationIssue` in deterministic
order. Each issue has a stable code, record identity, structured field path, and
optional related references. `validate_record_graph` raises
`ConcordRecordGraphError` with that same issue tuple.

## Exact conversion

`record_to_dict` produces an independent JSON-native record body. Ordered tuples
become arrays, nested value objects become exact mappings, and absent optional
values are omitted. `record_from_dict` dispatches through the controlled
`RECORD_KIND_REGISTRY`. It rejects unknown record kinds, unknown fields, missing
required fields, wrong primitive types (including booleans supplied as
integers), non-finite numbers, and malformed nested values. A valid record
round-trips without semantic loss.

This conversion deliberately does not define a filesystem envelope or canonical
path. Those belong to issue #25.

## Core standards boundary

`collect_core_standards_issues` and `validate_core_standards` accept a
caller-supplied immutable Core `StandardsLibrary`. They use Core's public
standards-selection API to validate profile existence and Focus Standard
membership, then report missing, outside-profile, inactive, or deprecated
references without loading or changing Core storage. Concord records are never
rewritten during validation.

## Controlled extensions and history

Where the contract permits extensions, a value must be a documented built-in or
a namespace-qualified key such as `local:discussion_mapper`. General record
identifiers continue to use Core's public identifier validator.

`ScanReference` is the immutable native successful-routing occurrence. It stores
only the Activity/Page/route identity, Core retained-source scan identity,
one-based physical page number, containment-safe workspace-relative source path,
lowercase SHA-256, and dispatch provenance. Graph validation requires the exact
page/activity/route relationship and rejects duplicate or contradictory physical
occurrences. It contains no student, Author, Subject, Group, Score, or Grade.

Historical replacement uses explicit `supersedes_*` fields. Graph validation
requires predecessor resolution and rejects self-reference, branches, cycles,
and backward Score times. Correction Records explain invalidation or connect a
target to a same-history successor; they never retarget or delete historical
references. Current state is derived from an explicit chain, not identifier or
timestamp ordering alone.

## Deliberately deferred

The current layer does not implement Templates or Packets beyond opaque identity
references, returned Artifact assembly, Author/Subject management workflows,
Review/Moderation, scoring, publication, consumer adapters, grading, reporting,
or authentication. Those responsibilities remain assigned to issues #28 through
#34.

