# Issue #129 — Slice 7 installed Core 0.6.5 acceptance

## Candidate identity

Issue #129 belongs to the Concord v0.3.1 milestone. Slice 7 therefore advances
the executable candidate package version from the already-released v0.3.0 to:

```text
pds-concord 0.3.1
```

This is required before installed qualification so the candidate artifact cannot
masquerade as a different v0.3.0 wheel.

Historical v0.3.0 release audits and validators remain unchanged in this slice.
They are reconciled for the new release only in Slice 8.

## Exact Core qualification artifact

The installed harness accepts only:

```text
pds_core-0.6.5-py3-none-any.whl
```

with SHA-256:

```text
9ace75f17b23b7f0ed6a709d531af5120db43d0325b4148d26f2d6ba1d4b3c18
```

Both filename/metadata and bytes are authenticated before building or installing
the Concord candidate.

## Noneditable candidate boundary

`scripts/run_issue129_installed_acceptance.py`:

1. requires an absent or empty work directory;
2. refuses to overwrite pre-existing repository build/egg-info roots;
3. builds exactly one wheel from the current source;
4. requires exact candidate name/version `pds_concord-0.3.1-py3-none-any.whl`;
5. records the exact candidate SHA-256;
6. creates an isolated virtual environment;
7. installs exact Core 0.6.5 and the built Concord wheel;
8. runs `pip check`;
9. runs a copied smoke program from outside the repository using `python -I`;
10. removes generated repository build roots after the run.

The smoke verifies both Concord and Core import from isolated `site-packages` and
that no repository path is present on `sys.path`.

## Installed producer contract

The installed producer profile must expose:

```text
distribution:
    pds-concord

manifest:
    concord_academic_result_manifest_v1

reader:
    concord_academic_result_reader_v1
```

through Core 0.6.5 `lookup_publication_reader_support(...)`.

## Installed Standards flow

The smoke creates a real Core Standards Library with:

```text
profile_id:
    njsls-ela:profile.2023:11-12

standard_id:
    njsls-ela:2023:rl-ts-11-12-4

code:
    RL.TS.11-12.4

short_name:
    Analyze Text Structure
```

and executes:

```text
Core class + roster
-> Core StandardsLibrary
-> Concord Activity
-> standard-backed Criterion Set / Criterion
-> standard-backed Score
-> persistence/reload
-> Core Academic Work Registration
-> Concord manifest generation
-> Core publication
-> concord_academic_result_reader_v1
```

The durable Profile/Standard IDs must remain exact throughout.

The teacher-facing `code` is deliberately absent from the published manifest
bytes, proving that depiction metadata was not substituted for durable identity.

## Consumer boundary

The installed smoke imports no Meridian or Vitrine code. Their compatibility
decision remains downstream and keyed to the stable reader contract rather than
the exact Concord package version.

The exact Concord v0.3.1 candidate wheel hash remains qualification provenance.
