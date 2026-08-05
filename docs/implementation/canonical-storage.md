# Canonical Storage and Guarded Persistence

Concord owns canonical native state only beneath the `state/` descendant of the
exact Core `ModuleWorkRef(module_id="concord", class_id=..., work_id=...)` work
root. Core continues to own workspace resolution, class metadata, work-root and
safe-descendant construction, routes, retained scans, academic registration,
and publication. Concord does not inspect or modify sibling namespaces such as
`routes/`, `exports/`, `rendered/`, or `attachments/`.

## Canonical layout and versions

```text
state/
  work.json
  records/<record_kind>/<record_id>/revisions/<record_revision>.json
  snapshots/<snapshot_revision>.json
  current.json
  derived/catalog.sqlite
  .locks/write.lock
  .locks/catalog.lock
```

Storage schema version, native-record contract version, and catalog schema
version are respectively `"1"`, `"1"`, and `1`. Canonical JSON is UTF-8,
sorted, two-space indented, finite-number-only JSON with LF endings and exactly
one final newline. Strict readers reject duplicate keys, unknown or missing
fields, invalid UTF-8, byte-order marks, nonstandard constants, wrong primitive
types, unsupported versions, symlinks, and any disagreement among path,
envelope, body, work, revision, or digest identity.

## Bootstrap and commits

The first commit requires an existing writable Core workspace and matching Core
class. Its complete graph contains exactly one Activity and at least one Session.
Concord creates no workspace or class implicitly. Standards-based or mixed
graphs, and graphs containing standards-backed Criteria or Scores, require an
explicit Core `StandardsLibrary` and must pass Core standards validation.

`commit_record_batch` acquires the versioned, work-qualified `write.lock`,
re-reads expected state, merges candidate identities without deletion, validates
the complete graph, and then writes in this order:

1. changed record revisions, created exclusively and verified byte-for-byte;
2. one immutable snapshot binding exact record digests and its predecessor;
3. one temporary current pointer, atomically installed with `os.replace`;
4. a strict reload of the complete selected graph.

Every later commit supplies the exact expected current snapshot revision. A
stale writer conflicts even if one candidate body matches current state. Exact
no-op replay creates neither record revisions nor a snapshot. Storage revision
numbers describe immutable versions of one durable identity; they never create
or replace domain `supersedes_*` relationships.

Before any initial, advancing, or replayed commit can proceed, Concord proves
that snapshot history is exactly contiguous from revision 1 through the current
snapshot and that every selected record has exactly contiguous revisions from 1
through its selected revision. Any orphan, gap, unexpected identity, or newer
unselected history blocks all future writes until separately reviewed
reconciliation. Writers never fill a gap beneath ambiguous newer history.

The current pointer is the only mutable canonical JSON file. Readers never infer
current state from the largest filename. An exclusive-write failure before file
synchronization removes the partial file when that can be proven safe; failed
cleanup is reported. Synchronized files whose directory durability cannot be
confirmed are preserved and reported as structured partial success. Before
pointer publication, durable new files remain noncurrent. After pointer
publication, final-verification failures explicitly report that canonical state
is already committed, including its snapshot revision and digest. Failure to
remove `write.lock` or `catalog.lock` is surfaced rather than suppressed,
including on exact no-op replay.

## Strict reads and reconstruction

Public read APIs load exact markers, record revisions, snapshots, the current
pointer, current records, and the complete current `ConcordRecordGraph`.
Enumeration is bounded to known directory levels and class work discovery reads
only each candidate `state/work.json`. Reads create no directories, locks,
catalogs, pointers, or repairs. Graph reconstruction never consults SQLite.
Loading snapshot N proves every declared predecessor identity and exact digest
back through snapshot 1; checking only N-1 or choosing filenames by order is
insufficient.

## Catalog nonauthority

`state/derived/catalog.sqlite` is disposable lookup and audit state. A rebuild
holds only `catalog.lock`, inventories strict canonical sources using sorted
POSIX relative path, byte size, and SHA-256 tuples, builds a complete temporary
database, repeats the inventory, atomically replaces the database only when the
source is unchanged, and verifies the installed result. Metadata records the
application and schema identifiers, build time, work identity, current snapshot
identity, source digest and counts. The catalog stores only minimized lookup
metadata—kind, identity, revision, canonical relative path, digest, and snapshot
selection—and never stores complete native record bodies, notes, rationale,
privacy data, or evidence lineage. Queries support current, historical, all, and
exact-snapshot projections.

A missing, stale, incompatible, or corrupt catalog fails clearly and never
changes canonical JSON. Recovery is full rebuild after a successful canonical
audit; catalog rows are never patched as repair.

## Diagnostics, interruption, and recovery

Storage diagnostics are deterministic and omit record bodies, names, review
notes, moderation rationale, credentials, and evidence content. Lock inspection
reports path, size, and byte fingerprint. Lock age alone never proves inactivity.
Storage validation accepts the Core standards context required by standards-
based data and reports `storage.standards_context.required` when it is absent.
Graph-integrity diagnostics preserve native validation codes, record identity,
field paths, and privacy-safe related references without collapsing them into a
generic text classification.

Recovery follows these rules:

- Diagnose before repairing and preserve immutable history.
- Never edit record revisions or snapshots in place.
- Never select the highest revision or snapshot automatically.
- Preserve and report orphan revisions and snapshots; do not select or delete
  them based on name, time, or apparent semantic validity.
- Never alter bytes to satisfy a digest or reconstruct a corrupt pointer by
  guessing.
- Never clear a lock solely because it appears old.
- Never patch catalog rows; validate canonical JSON and rebuild the whole
  catalog.

Backups must capture canonical `state/` JSON consistently. The derived catalog
may be omitted because it is rebuildable. Backup tooling, institutional
retention, legal deletion, cloud synchronization, and automatic repair remain
outside this layer.

## Follow-on boundary

Later Activity, Session, Group, Artifact, Review, Moderation, Scoring, routing,
and publication issues must use these APIs. This implementation does not create
teacher workflows, PDS2 routes, scans, rendered Artifacts, publication records
or manifests, Meridian adapters, Grades, standards aggregation, or reports.
