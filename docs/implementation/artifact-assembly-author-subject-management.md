# Artifact Assembly and Author/Subject Management

## Status

Implemented for Concord v0.2.0 issue #28.

## Boundary

Issue #27 established the physical-page chain:

```text
Activity
  -> Artifact Instance
  -> Artifact Page
  -> immutable PDS2 route
  -> Core-retained source
  -> Scan Reference
```

Issue #28 extends that chain with Artifact-level return state, reproducible returned
Artifact assembly, and explicit Artifact Author and Artifact Subject workflows.

These concepts remain independent. Routing does not establish authorship or Subject
identity. Group Membership and Role Assignment do not establish authorship. An
Artifact Subject is not a Score target.

## Returned Artifact state

The Concord route handler now evaluates the Artifact's declared `page_ids` after a
new returned physical occurrence is filed. Only pages with `return_expected=true`
participate in return completeness.

- some required pages returned -> `partially_returned`;
- every required page returned -> `returned`;
- non-return-expected pages do not block the transition.

The new Scan Reference, returned Artifact Page revision, and applicable Artifact
Instance return-state revision are committed in one guarded canonical batch. Exact
scan replay remains a semantic no-op. Concord does not silently reopen terminal
Artifact states.

`returned` means the physical evidence has been filed. It does not mean Artifact
Review, Moderation, scoring, publication, or grading is complete.

## Derived returned-Artifact assembly

`assemble_returned_artifact` constructs a convenience PDF only from canonical
`ScanReference` lineage and Core-retained source bytes. It never reads the original
scanner folder or an arbitrary external source path.

For every selected page, Concord verifies:

- the exact Artifact Page relationship;
- retained workspace-relative location;
- containment and link/junction safety;
- retained SHA-256;
- supported source type;
- and physical source-page bounds.

Image sources contribute physical page 1. PDF sources contribute only the exact
one-based physical page referenced by the Scan Reference.

Pages are assembled in `ArtifactInstance.page_ids` order, not scan order, route
order, filename order, or record-ID order. Missing required pages block completed
assembly. If several retained occurrences exist for one Artifact Page, automatic
selection stops and the caller must choose an exact `scan_reference_id`.

Completed derivatives live under:

```text
attachments/
  artifacts/
    <artifact_instance_id>/
      assemblies/
        <assembly_id>/
          artifact.pdf
          manifest.json
```

The `assembly_id` is derived from the exact ordered Artifact Page / Scan Reference
lineage and contains no names or student identity. A materially different source
selection creates another assembly identity. Exact replay verifies and reuses the
existing immutable derivative.

The strict JSON manifest preserves source snapshot identity, ordered page and Scan
Reference lineage, retained-source identifiers and digests, output digest, base
Artifact privacy classification, and creation provenance. It deliberately omits
Artifact Authors and Subjects. Correcting attribution therefore does not rewrite
physical evidence.

## Artifact Authors

`ArtifactAuthor` answers who produced, completed, recorded, or formally represented
an Artifact. Concord supports zero, one, or many Author associations.

Supported native modes include individual/co-author, observer, recorder,
recorder-for-Group, collective Group Author, teacher/authorized-adult Author, and
unknown.

A truly unknown Author is represented without a fake student, Group, or placeholder
person. `author_reference=None` is valid only for the exact native unknown-author
state.

Core student Authors are validated against the Core class roster. Collective Group
Authors remain Concord Group identities. Recorder-for-Group authorship preserves
both the individual recorder and represented Group. An optional Role Assignment is
context only and must identify the same participant.

State-only transitions revise the same durable association. Semantic correction
creates a new successor `ArtifactAuthor` and an atomic `CorrectionRecord` with
`author_correction`; the predecessor remains historical.

## Artifact Subjects

`ArtifactSubject` answers whom or what the Artifact concerns. It is independent
from authorship and supports zero-to-many associations without duplicating the
Artifact or retained source.

Supported Subject reference kinds are Core student, Concord Group, Session,
Activity, Artifact Instance, and explicit external record. Built-in roles enforce
their natural reference kind; namespace-qualified role extensions remain available
through the native model.

Student Subjects are validated against the Core roster. Concord-owned Group,
Session, Activity, and Artifact references must remain in the Activity context.
External records retain their declared owning system rather than importing a sibling
module.

State-only confirmation changes revise the same association. Semantic correction
creates a successor `ArtifactSubject` and atomic `CorrectionRecord` with
`subject_correction`.

## Interfaces

Direct commands remain noninteractive:

```text
concord artifact list
concord artifact show
concord artifact assemble

concord artifact author add|list|show|update|replace
concord artifact subject add|list|show|update|replace

concord artifact page prepare|list|show
concord artifact render
```

The teacher Artifact menu preserves the issue #27 page choices and adds Artifact
inspection, returned assembly, Authors, and Subjects. Long selections use the
shared ten-row paginator and H/B/M/Q navigation. Writes require explicit operation
words including `ASSEMBLE`, `ADD`, `UPDATE`, and `CORRECT`.

Stale canonical writes never force-overwrite or silently retry. Reload is read-only.

## Privacy and identity separation

Assembly manifests do not contain Author/Subject relationships, student names, or
Group membership lists. Association records retain their own optional privacy
policies independently from the base Artifact.

Adding, confirming, disputing, or replacing an Author/Subject does not change:

- Artifact Page identity;
- Core Route Registration;
- PDS2 payload;
- Scan Reference identity/history;
- retained source;
- or assembly source lineage.

No #28 workflow creates a Review, Moderation Record, Score, Score target, Grade, or
publication.

## Follow-on boundary

Issue #29 must build Artifact Review and Moderation on these exact records and
services. It must not introduce another source identity, another Author/Subject
model, or another Artifact assembly path.
## Pure graph integrity hardening

Issue #28 also extends `collect_record_graph_issues` so canonical validation does
not rely on the workflow path that created a record. Pure graph validation checks
Artifact return-state coherence, Author and Subject semantic/reference context,
duplicate current Author/Subject associations, and Author/Subject correction-type
agreement. Core roster membership and retained-source byte validation remain
workflow-boundary checks because they require external Core state or filesystem
bytes.
