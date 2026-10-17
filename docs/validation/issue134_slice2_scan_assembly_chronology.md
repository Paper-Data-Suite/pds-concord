# Concord #134 - Slice 2: Returned evidence chronology and verified history

**Branch:** `134-reliable-long-path-opening-and-teacher-artifact-navigation`

**Required parent:** `6a258069718f55090219b73b769b34d962e440d7` (Slice 1)

## What a teacher can now do

- When an Artifact Page has several retained scan occurrences, the selector
  shows the **recorded routing** date/time (in the machine's configured local
  timezone), newest first if provable. It never calls this the physical scan
  date or infers chronology from a scan ID, path, or file modification time.
- Identical timestamps say **same recorded time; order uncertain**; missing
  timestamps say **chronology uncertain**. No newest-wins selection is automatic.
- Collect, Review, and Score expose **V. Open a verified saved assembly
  version** alongside the existing **O. Open returned work** operation.
  The `O` operation continues to prompt for exact scan occurrences. The `V`
  operation lists only existing, individually validated assembly combinations.
- The history list identifies when each assembly was created, its page count,
  and whether additional strictly newer routed evidence exists for a selected
  page. Ambiguous times are identified as such.
- The teacher selects the exact saved combination. Concord then passes every
  selected page/scan reference to the existing `open_returned_artifact_evidence`
  operation with the original expected snapshot revision. The resolver verifies
  the exact lineage, current authorization and manifest/PDF digest again before
  Core receives the local viewer request.

## Source-of-truth and security constraints

- Canonical `ScanReference.created_provenance.timestamp` records **routed**
  time. Replay of an identical already retained scan/route combination is not a
  newly received occurrence. This slice does not change that behavior.
- Assembly history is derived from a bounded, containment-safe assemblies
  directory. A directory entry is never trusted as an assembly on its own:
  require an allowable ID, non-link paths, a strict manifest, canonical page and
  scan identity, exact deterministic assembly ID, retained-source validation,
  matching PDF SHA-256 and unchanged current snapshot. Unexpected entries fail
  closed. Transient installer directories are not versions.
- No new latest-assembly pointer or mutable history record is introduced.
  Opening an assembly never marks a Review, changes a Score, publishes, assembles,
  repairs evidence, or records that an external PDF viewer displayed anything.
- `V` shows **when an assembly was recorded as created**; it does not claim to
  establish the actual physical scanning time, or prove which assembly underlay
  any prior Review or Score. Existing historic Review/Score exact-version links
  remain unspecified rather than guessed. Prospective binding of future Review/
  Score actions to exact immutable evidence identity requires a separate
  explicitly qualified data-contract change.
- Teacher-facing errors remain generic; technical IDs, hashes and paths are
  not dumped through the normal history operation.

## Verification scope

- New focused chronology, manifest-guard, snapshot-guard, and exact-selection
  tests. Existing Issue #105 evidence-opening tests are aligned with Slice 1's
  truthful `Viewer Requested` behavior and teacher choice wrapper.
- Focused legacy assembly/opening/Review-next tests, Ruff, strict MyPy and staged
  Git whitespace checks. Full suite and real Windows Core v0.6.6 viewer
  qualification are deferred to the designated release acceptance phase.

## Deliberately outside Slice 2

- Automatic promotion of newer evidence, rewriting earlier review judgments,
  migration of legacy Score evidence references, scores copied across versions,
  external file-opening success detection, and installed Core dependency-floor
  update are **not** authorized here.
