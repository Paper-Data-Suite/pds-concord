# Issue #129 — Core 0.6.5 reader-contract foundation

## Status

Slice 4 adopts the producer-side reader metadata API released in Core 0.6.5.

The Unreleased Concord source now requires:

```text
pds-core>=0.6.5,<0.7
```

and declares:

```text
distribution:
    pds-concord

manifest:
    concord_academic_result_manifest_v1

reader:
    concord_academic_result_reader_v1
```

through Core `PublicationReaderSupport`.

## Compatibility authority

These identities remain deliberately separate:

```text
Concord distribution version
    exact implementation/provenance

concord_academic_result_manifest_v1
    durable serialized Academic Result evidence

concord_academic_result_reader_v1
    stable public consumer read behavior
```

A future Concord distribution release may continue declaring reader v1 when the
covered public reader API/model/semantics remain compatible. Meridian and
Vitrine therefore do not need a release merely because the Concord package
version changed.

An incompatible public reader/model change requires a new reader-contract
identity even if the manifest contract remains v1.

## Core authority boundary

Core validates and carries the producer declaration. Core lookup:

```text
lookup_publication_reader_support(...)
```

is metadata lookup only.

It does not:

- import or execute `concord.academic_result_reader`;
- decide that Meridian or Vitrine supports the reader;
- authorize manifest access;
- change Publication Record compatibility;
- replace exact installed distribution version as provenance.

Consumer adapter support remains consumer-owned.

## Historical release boundary

The released Concord v0.3.0 audit remains immutable and is not rewritten by this
slice. Concord v0.3.0 did not publish Core 0.6.5 reader-support metadata.

Repository release/version guards that intentionally freeze the historical
v0.3.0 artifact are reconciled only when the Unreleased branch is promoted to
the next Concord release. Slice 4 does not redefine the historical artifact.
