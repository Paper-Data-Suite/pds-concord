# Concord v0.3.1

Concord v0.3.1 is the maintenance and teacher-workflow release built on the
released v0.3 foundation. It preserves existing workspace/native/public
contracts while incorporating the v0.3.1 teacher-workflow work accumulated in
the changelog.

## Core compatibility

The runtime floor is now:

```text
pds-core>=0.6.5,<0.7
```

Core 0.6.5 is required because Issue #129 adopts producer-declared reader
metadata through `PublicationReaderSupport`.

Historical Concord release tags retain their original Core qualification
evidence. No workspace migration is required for v0.3.1.

## Stable Academic Result reader contract

Concord continues to publish:

```text
concord_academic_result_manifest_v1
```

and now formally advertises:

```text
distribution:
    pds-concord

reader:
    concord_academic_result_reader_v1
```

The reader contract—not the exact Concord package version—is the downstream
semantic compatibility boundary for Meridian and Vitrine. Exact package and
wheel versions remain provenance and release-qualification evidence.

A future Concord package release may retain reader v1 when its public reader
imports, call shapes, returned models, validation/error behavior, and
interpretation semantics remain compatible.

## Core Standards identity correction

Issue #129 corrects Concord fields that previously applied routing/path
identifier grammar to authoritative Core Standards identities.

Durable values such as:

```text
profile_id:
    njsls-ela:profile.2023:11-12

standard_id:
    njsls-ela:2023:rl-ts-11-12-4
```

now survive native Activity/Criterion/Score state, canonical persistence,
analysis/reporting, Academic Result generation, Core publication, and the public
reader unchanged.

Teacher-facing depiction remains separate and may use:

```text
RL.TS.11-12.4 — Analyze Text Structure
```

when the authoritative Core Standards Library is available. Display metadata
never replaces the durable ID in machine/public state.

## Installed qualification

Issue #129 Slice 7 independently built the noneditable
`pds_concord-0.3.1-py3-none-any.whl` candidate and exercised the corrected
Standards -> publication -> public-reader path under the exact released Core
0.6.5 wheel.

The active final release validator additionally repins Concord's executable
installed-smoke matrix to Core 0.6.5 and reruns package, static, documentation,
release-artifact, and installed-distribution qualification.

Historical v0.3.0 audit/checklist files are intentionally not rewritten.
