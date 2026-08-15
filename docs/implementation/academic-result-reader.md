# Academic result consumer reader

Issue #32 adds Concord's stable consumer-neutral interpretation surface for
`concord_academic_result_manifest_v1` and a separate authorization-gated reader
for Concord-owned Artifact evidence.

The split is deliberate:

```text
verified immutable manifest bytes
-> concord.academic_result_reader
-> validated Concord public models and exact lookups
-> downstream policy
```

and, only after a separate Artifact authorization decision:

```text
validated Concord manifest
-> represented Concord Artifact evidence
-> deployment-owned authorization gate
-> exact historical Concord snapshot
-> retained-source integrity verification
-> bounded producer-approved PDF representation
```

The reader does not discover publications, choose a publication revision,
calculate Grades or proficiency, choose the "best" Score, or create portfolio
policy. Core, Meridian, Vitrine, and the deployment retain those responsibilities.

## Public modules

The stable import surfaces are:

```python
import concord.academic_result_reader
import concord.academic_result_artifacts
```

No top-level `concord` re-export and no new entry point are introduced.

`concord.academic_result_reader` is pure. It performs no workspace, filesystem,
Core registry, catalog, publication, or authorization I/O.

`concord.academic_result_artifacts` is the explicit Artifact I/O boundary. It
may inspect Concord native state and Core-retained scan bytes only after an
external authorization gate returns `allowed`.

The internal `concord.artifact_rendering` module contains the shared retained-
source verification and deterministic PDF rendering primitives used by both the
consumer reader and the teacher returned-Artifact assembly workflow. It is not a
consumer-policy surface.

## Canonical manifest reader

The main reader is:

```python
read_academic_result_manifest(value: bytes) -> AcademicResultManifest
```

It accepts exact immutable `bytes`, delegates decoding and whole-manifest
validation to Concord's authoritative manifest contract, serializes the restored
model through the same canonical serializer, and requires exact byte equality.

Semantically equivalent but noncanonical JSON is rejected. This includes
alternate whitespace, key order, newline handling, trailing whitespace, and
alternate timestamp text.

Core remains responsible for verifying the Publication Record's manifest path
and SHA-256 binding before those bytes reach this API.

Public model validation is exposed separately:

```python
validate_academic_result_manifest(manifest) -> AcademicResultManifest
```

It delegates to the authoritative whole-manifest validator and returns the same
immutable model on success.

## Exact lookup surface

The reader exposes exact producer-native lookups for:

```text
Criterion Set
Criterion
Scoring Scale
Scale level
Score
Score Evidence Link
Moderation
Score Evidence Links for one Score
Scores for one exact target
```

The helpers never choose an official, latest, best, or grading-selected Score.
Tuple-valued relationship helpers preserve manifest order.

Scale-value lookup is type-sensitive. These JSON scalars remain distinct:

```text
1
1.0
"1"
true
```

A consumer must not replace Concord's Scale lookup with ordinary Python scalar
equality.

`ScoreProjection.current_state` describes producer supersession state only. It
is not Meridian attempt-selection or grading policy.

Group targets remain Group targets. A Group Score is never expanded into
individual student Scores. Non-score dispositions retain `value = None` and are
never converted to numeric zero.

## Reader errors

The manifest reader defines:

```text
ConcordAcademicResultReaderError
ConcordAcademicResultReaderValidationError
ConcordAcademicResultReaderDecodeError
ConcordAcademicResultReaderNotFoundError
```

Validation failures cover invalid public input and noncanonical bytes. Decode
failures cover malformed or semantically invalid manifest bytes. Exact valid
identifiers that are absent raise the public not-found error.

Routine reader errors do not expose raw manifest content or private producer
notes.

## Artifact authorization contract

Artifact access is separate from manifest/result authorization.

The deployment provides an implementation of:

```python
AcademicResultArtifactAuthorizationGate
```

Concord supplies a request containing only manifest-derived public identity:

```text
work
record-set identity and revision
source snapshot revision
Score identity
Score Evidence Link identity
represented Evidence Reference
purpose
```

The gate returns one of:

```text
allowed
denied
unresolved
```

Only `allowed` permits native workspace I/O. `denied`, `unresolved`, and gate
exceptions fail closed. Concord does not define a role matrix or decide who is
entitled to an Artifact.

External ScoreForm, Quillan, or other producer evidence cannot enter the
Concord Artifact resolver. The represented evidence must be Concord-owned and
must be exactly one of:

```text
artifact_instance
artifact_page
```

There is no public path, filename, Scan Reference, or arbitrary native-record
selector.

## Historical source binding

Artifact resolution binds to:

```text
manifest.projection.source_snapshot_revision
```

It never substitutes the current Concord snapshot.

The historical storage reader validates the immutable snapshot predecessor
chain, selected record digests, and native graph structure without consulting
`current.json`. The native Score Evidence Link is then reprojected and must
agree exactly with the represented public manifest link before Artifact bytes
are considered.

This preserves old published manifests even after current Concord state has
advanced.

## Bounded Artifact representations

The current producer-approved representation is:

```text
returned_artifact_pdf
```

For `artifact_page`, the reader returns exactly the represented physical page.
A multi-page retained scan therefore yields one bounded PDF page, not the whole
source scan.

For `artifact_instance`, the reader returns the Artifact's canonical ordered
`return_expected` pages only.

If a required Artifact Page has no returned occurrence, the representation is
unavailable. If it has more than one returned Scan Reference, the read is
ambiguous and fails closed. The public API deliberately offers no Scan
Reference selector and never chooses by timestamp, filename, ID, filesystem
order, or recency.

## Retained-source integrity

The neutral rendering layer verifies:

```text
workspace containment
link/symlink/reparse safety
ordinary-file status
canonical retained-source SHA-256
supported image/PDF media
physical page bounds
safe decoding
```

Retained source bytes are read once, verified, and those exact immutable bytes
are rendered. This prevents a file replacement between digest verification and
decoding from changing the returned representation.

Returned bytes are deterministic PDF bytes. The public result reports the
representation SHA-256 and byte size. That digest is distinct from the Core
Publication manifest digest and from the retained source digest.

The consumer read creates no durable assembly, derivative manifest, native
record, Core record, catalog row, or current-snapshot change.

## Public Artifact metadata

The result contains bounded producer-approved metadata for the exact historical
Artifact, including:

```text
Artifact identity/category/session/group
ordered Artifact Page identity and logical page number
producer privacy classification
current-as-of-snapshot Artifact Author associations
current-as-of-snapshot Artifact Subject associations
```

Author and Subject remain independent relationships. The reader does not infer:

```text
Author == Subject
Subject == Score target
Group member == Author
Group member == Subject
recorder_for_group == individual owner
```

Superseded Author/Subject associations remain historical native state and are
not exposed as current attribution. Unrelated Artifact attribution records are
excluded.

The public projection does not expose native provenance notes, privacy reasons,
Role Assignment internals, route fallback text, Scan Reference IDs, source scan
IDs, retained-source paths, retained-source digests, source filenames, QR
payloads, Score rationale, Moderation rationale, or raw retained scan bytes.

## Artifact errors

The Artifact reader defines public failures for validation, authorization,
not-found historical state, unavailable evidence, ambiguous evidence, and
integrity failures.

Public messages are intentionally privacy-safe and do not include canonical
workspace paths, retained filenames, Scan Reference IDs, or deployment policy
text. Internal filesystem/rendering/authorization exceptions are not retained
as inspectable exception chains at the public API boundary.

## Consumer boundaries

Concord remains the producer-native interpretation authority. It does not import
Meridian, Vitrine, ScoreForm, Quillan, or Portia to implement these readers.

Meridian may use the manifest reader to build its own producer adapter and owns
Grade eligibility, reassessment selection, proficiency/mastery policy, Grade
calculation, Academic Period policy, weighting, and reporting.

Vitrine may use the reader and separately authorized Artifact representation as
source material and owns portfolio candidate, selection, placement, snapshot,
copying, and disclosure policy.

Core remains authoritative for publication discovery, canonical Publication
Records and Withdrawals, producer compatibility, manifest path/digest
verification, and the academic catalog.

## Installed acceptance boundary

Issue #32's isolated-wheel smoke verifies that:

```text
concord.academic_result_reader imports from the built wheel
concord.academic_result_artifacts imports from the built wheel
canonical manifest bytes round-trip through the reader
type-sensitive Scale lookup is preserved
exact Score/target lookup is preserved
reader imports and pure reads do not create a workspace
no sibling PDS package is required
```

The full clean-wheel chain from Activity creation through publication, Core
verification, Concord consumer read, Artifact authorization/read,
supersession/withdrawal, and audit remains assigned to Issue #33.
