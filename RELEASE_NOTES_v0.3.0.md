# Concord v0.3.0

Release date: 2026-08-31

Concord v0.3.0 adds teacher-approved group planning, reusable classroom
materials, guided Activity setup, task-oriented teacher navigation, and
privacy-minimal suite operations while preserving Concord's paper-first,
human-reviewed evidence model.

## Highlights

- Teacher-controlled `GroupPlan` workflows now support manual, arrangement CSV,
  deterministic seeded-random, and Core `grouping_signal_set_v1`-backed
  strategies.
- GroupPlan preview and approval remain planning state. Only explicit application
  creates fresh canonical `Group` and `GroupMembership` records.
- Missing grouping signals use explicit teacher dispositions and never become a
  low band, low Score, learner-facing label, or canonical Group attribute.
- Workspace-level immutable Template and Packet libraries provide reusable
  definitions and versions without copying operational Activity state.
- A package-owned library of 30 declarative starter Templates supports common
  collaborative classroom workflows.
- Activity-specific Packet instantiation creates fresh PacketInstance, Artifact,
  ArtifactPage, and Core PDS2 route identities.
- Safe Activity copying uses a positive allowlist and creates a fresh draft
  Activity plus first Session without copying Groups, evidence, Scores, or
  operational history.
- Reusable Role, Responsibility, Criterion Set, and Scoring Scale presets
  materialize fresh Activity-native state; presets do not contain assignments or
  Scores.
- Guided Activity creation/setup and the task-oriented
  `Plan -> Prepare -> Collect -> Review -> Score -> Share` interface compose the
  existing authoritative workflows while keeping record-level tools available
  under Advanced.
- Read-only Activity attention and structural readiness are exposed through
  Core 0.6.3's neutral `paper_data_suite.module_operations` contract.
- The installed package continues to expose Concord's console, routing-module,
  publication-producer, and module-operations entry points without any sibling
  PDS runtime dependency.

## Architecture and privacy qualification

Issue #71's pre-release audit reports:

```text
11 ADRs: CONFORMS
4 ADRs: CONFORMS — DEFERRED SURFACE NOT REQUIRED BY v0.3.0
0 ADR blockers

architecture: CONFORMS — 0 blockers
privacy: CONFORMS — 0 blockers
usability: CONFORMS — 0 blockers
interoperability: CONFORMS — 0 blockers
```

The four bounded ADR deferrals are future optional surfaces: Work
Items/tasks/contributions, broader external-reference authoring, teacher-facing
ScoreForm/Quillan link management, and optional Activity markers/events/work
items/contributions.

Concord still does not calculate Grades, universal proficiency, reassessment
selection, or reporting policy.

## Physical starter-workflow qualification

The v0.3.0 physical path is inherited from the completed issue #70 acceptance
against source commit:

```text
33bd916978da21f4a317a1509adc77981a25aa26
```

That acceptance used six representative packets / ten physical pages across
seminar, signal-backed group-project, and peer-review starter families through
real print, physical marking, real scan, Core retained-source custody/dispatch,
Concord Artifact assembly, explicit Review, explicit Score, Academic Work
registration, publication, and public result readback.

Issue #71 intentionally does not repeat the physical run. The release-preparation
delta through the version promotion consists of release validators/tests,
documentation, and package version metadata; it does not change Template assets,
Packet rendering, PDS2 allocation, scan intake, Artifact assembly, Review, Score,
or publication behavior.

## Compatibility

- Python: `>=3.11`
- Core: `pds-core>=0.6.3,<0.7`
- Qualified Core release: `pds-core 0.6.3`
- No runtime dependency on Paper Data Suite shell, ScoreForm, Quillan, Meridian,
  Portia, or Vitrine.

## Distribution

The release process produces and authenticates exactly:

```text
pds_concord-0.3.0-py3-none-any.whl
pds_concord-0.3.0.tar.gz
SHA256SUMS.txt
```

The authoritative hashes are recorded only after the release-preparation PR is
merged and the exact clean `main` commit is qualified. Concord is distributed
through the GitHub Release for `v0.3.0`; this release does not publish to PyPI or
another package index.
