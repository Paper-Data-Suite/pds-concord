# Issue #129 — Concord Academic Result Reader v1 qualification

## Contract identity

```text
distribution:
    pds-concord

manifest:
    concord_academic_result_manifest_v1

reader:
    concord_academic_result_reader_v1
```

This qualification names the consumer-neutral public behavior already
implemented by Issue #32. It does not add a consumer adapter and does not change
the manifest schema.

## Stable public boundary

Reader v1 covers:

- the exact `concord.academic_result_reader.__all__` surface;
- the existing public callable parameter shapes;
- immutable canonical manifest-byte validation;
- exact public manifest/projection models and consumer-visible fields;
- exact lookups and manifest-order relation lists;
- type-sensitive Scale interpretation;
- bounded validation/decode/not-found exception semantics;
- deterministic repeated reads;
- no workspace/filesystem, Core registry/catalog, or consumer-policy access.

## Standards identity qualification

The reader fixture now uses a durable Profile identity and durable Standard
identity that contain punctuation and are intentionally not display codes:

```text
profile_id  = njsls-ela:profile.2023:11-12
standard_id = njsls-ela:2023:rl-ts-11-12-4
```

The identity survives canonical bytes, public readback, Criterion Set,
Criterion, Score, Focus Standard, and Standards Result projection unchanged.

Teacher-facing Core `code`, `short_name`, and Profile title are presentation
metadata. They are not substituted into the public reader's durable IDs.

## Versioning rule

A later Concord package release may continue declaring reader v1 when this
public behavior remains compatible. Exact installed package version remains
provenance and release-qualification evidence, not the semantic reader
compatibility key.

An incompatible change to the covered reader API/model/semantics requires a new
reader contract.
