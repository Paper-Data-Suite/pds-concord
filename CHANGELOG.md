# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

- Explicit Core Academic Work Registration for Concord Activities plus immutable
  `concord_academic_result_manifest_v1` generation with semantic no-churn
  revisioning and publication-safe projection.
- A separate `paper_data_suite.publication_producers` Concord profile, explicit
  first publication/supersession/withdrawal, Core catalog reconciliation,
  deterministic publication-series status, and partial-success recovery.
- Direct `concord publication ...` commands and an Activity-scoped teacher
  Publication menu with read-only preview, deliberate confirmations, and no
  implicit publication from scoring mutations.
- Explicit Artifact Review workflows with coherent readiness/outcome state,
  one current supersession lineage per Artifact, and auditable Review
  correction history.
- Evidence Moderation workflows with exact immutable evidence lineage,
  canonical zero/one/many Subject scope, permitted-use restrictions, public
  Core Publication verification, and deterministic applicability readers.
- Direct and teacher-facing Review/Moderation interfaces plus installed-wheel
  persistence and nonmutation acceptance coverage.
- Returned Artifact state roll-up and reproducible PDF assembly from exact
  Core-retained Scan Reference lineage, with immutable derivative manifests.
- Explicit zero-to-many Artifact Author and Artifact Subject workflow services,
  including true unknown Author state, status revision, semantic correction,
  durable supersession, and correction history.
- Direct Artifact/assembly/Author/Subject CLI commands and teacher-facing
  Artifact, assembly, Author, and Subject menus.
- Core PDS2 Artifact Page integration with native preallocation, one immutable
  route per physical page, verified PDF rendering, and an installed Concord
  `paper_data_suite.modules` profile.
- Retain-first PDF/image scan intake, mixed installed-module dispatch, native
  Scan References, exact replay idempotency, and Core v2 append-only routing
  failure/resolution workflows.
- Direct Artifact/Page/scan commands and teacher-facing Artifact Pages and
  global Scan Routing menus over the shared typed services.

- Installable, typed `pds-concord` package baseline for v0.2.0 development.
- Side-effect-free help and version CLI.
- Authenticated released-Core integration, packaging, documentation, and CI
  validation tooling.
- Concord-owned canonical storage with immutable record revisions and work
  snapshots, atomic current-pointer publication, optimistic concurrency, strict
  graph reconstruction, and stable storage errors.
- Disposable per-Activity SQLite catalog, deterministic storage diagnostics,
  lock inspection, and conservative recovery documentation.
- Persistence durability hardening for complete orphan-free history checks,
  full snapshot-chain proof, structured post-publication and retained-lock
  outcomes, minimized catalog metadata, and native graph diagnostic codes.
- Typed Activity and Session workflow services with atomic Activity-plus-first-
  Session creation, standards validation, compact read models, guarded updates,
  and exact no-op behavior.
- Activity-specific Group workflows plus Core-roster-backed contextual
  Membership, Role, and Responsibility add/end/reassignment services.
- Atomic multi-student Membership addition for an existing Group and atomic
  Group-plus-initial-Membership creation.
- Fully noninteractive direct CLI command families for workspace, Activity,
  Session, Group/Membership, Role, and Responsibility workflows with stable exit
  codes and exact expected-snapshot protection.
- Teacher-facing menu with contextual H/B/M/Q navigation, explicit write
  confirmations, compact pagination, staged screen clearing, reusable in-memory
  actor context, standards selection, and one/several/remaining-Activity
  Effective Context choices.
- Installed-wheel workflow smoke coverage for read-only help, menu launch,
  synthetic Core class/roster integration, collaboration-context creation,
  immutable history, and derived-catalog rebuilding.

### Changed

- Group Membership supersession preserves participant identity while allowing
  explicit reassignment to a different Group/context, matching the accepted
  collaboration workflow contract.
- Bare `concord` and `python -m concord` now launch the teacher-facing menu;
  `--help` and `--version` remain direct and read-only.

