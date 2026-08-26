# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

- Activity-specific reusable Packet instantiation now resolves exact Packet and
  Template Versions against one explicit Activity Session, previews concrete
  targets/copies/pages/routes without mutation, freezes teacher rendering
  bindings behind a review digest, and commits fresh PacketInstance, Artifact,
  ArtifactPage, and immutable Core PDS2 route identities only after approval.
- Deterministic Packet PDF rendering now supports the full 30-starter
  `concord_starter_layout_v1` library, exact reprint without route reallocation,
  typed route/render partial-success recovery, direct CLI and opened-Activity
  teacher workflows, and read-only Packet Instance inspection.
- Issue #62 qualification now includes an installed-wheel Packet generation
  smoke, adversarial planning/signal privacy checks, documentation invariants,
  and the accepted synthetic 30-starter / 35-PDS2-page visual-review gate.

- A deterministic package-owned library of 30 synthetic collaborative-learning
  starter Templates spanning discussion, reading, synthesis, teamwork, projects,
  peer feedback, science/STEM, problem solving, and reflection.
- Strict non-executable `concord_starter_layout_v1` JSON rendering specifications
  with stable starter/Template/Version identities, exact packaged SHA-256
  binding, shared copier-safe paper conventions, semantic response regions, and
  identity-free privacy/authorship/Subject defaults.
- Read-only starter browsing plus explicit/idempotent install-one/install-all
  workflows through canonical #58 Template storage, with collision detection,
  teacher-state preservation, bounded multi-Template partial-success reporting,
  direct `concord template starter-*` commands, and a teacher Template Library
  `INSTALL` flow.
- Wheel/package qualification now proves the complete 30-asset starter catalog is
  shipped and loadable from an isolated installed Concord distribution.

- Canonical workspace-level reusable Packet storage under
  `shared/concord/packets/` using `concord_packet_library_storage_v1`, with
  strict typed/canonical JSON, immutable Definition/Version record revisions,
  digest-linked snapshots, guarded current pointers, explicit head/current
  Version state, and fail-closed path/history validation.
- Explicit Packet successor, activation, metadata-update, Version-retirement,
  and whole-Packet-retirement workflows with exact Template dependency
  eligibility/revalidation, exact expected-Packet-snapshot concurrency,
  per-Packet locking, no-op suppression, and bounded partial-success reporting.
- Strict `concord_packet_authoring_v1` prepare/commit input with exact source
  fingerprint revalidation, plus the noninteractive `concord packet ...`
  command family and workspace-level teacher Packet Library over the same public
  workflow services. External `ModuleRecordRef` components remain
  structural/source-owned and require no sibling runtime dependency.

- Public immutable reusable `PacketDefinition` / `PacketVersion` contracts with
  deterministic ordered `PacketComponent` composition, exact Template
  Definition/Version identity pairs, source-owned Core `ModuleRecordRef`
  external components, positive `copies_per_target`, identity-free audience and
  role intent, bounded non-executable conditions, and typed deterministic
  packet-level rendering rules.
- Shared `ROLE_KEYS` now backs both operational `RoleAssignment` validation and
  reusable Packet role intent so the built-in role vocabulary cannot drift,
  while namespaced role-key extensions remain supported.

- Canonical workspace-level reusable Template storage under
  `shared/concord/templates/` using `concord_template_library_storage_v1`, with
  strict typed/canonical JSON, immutable Definition/Version record revisions,
  digest-linked snapshots, guarded current pointers, exact rendering-
  specification bytes, and fail-closed path/history validation.
- Explicit Template successor, activation, metadata-update, Version-retirement,
  and whole-Template-retirement workflows with independent head/current Version
  state, exact expected-Template-snapshot concurrency, per-Template locking,
  no-op suppression, and bounded partial-success reporting.
- Strict `concord_template_authoring_v1` prepare/commit input with exact
  authoring/rendering source fingerprint revalidation, plus the noninteractive
  `concord template ...` command family and workspace-level teacher Template
  Library over the same public workflow services.

- Public immutable reusable `TemplateDefinition` / `TemplateVersion` contracts
  with typed page manifests, rendering-input declarations, response regions,
  identity-free privacy/authorship/Subject expectations and compatibility,
  exact rendering-specification SHA-256 binding, and explicit separation from
  Activity-native storage until #58.
- Shared Activity/Artifact category, scoring-orientation, page-kind, return, and
  authorship vocabularies now back both operational Artifact models and reusable
  Template validation, preventing contract drift.

- Exact approved-GroupPlan application preparation and atomic application,
  including deterministic application-bound Group/Membership IDs, semantic
  preview digests, exact snapshot/roster/signal revalidation, explicit fallback
  Membership context, empty-group preservation, leave-unassigned handling, and
  one guarded batch containing the applied GroupPlan plus every canonical Group
  and Membership.
- Direct `concord group-plan application-preview|apply` commands and a
  teacher-menu exact write-set preview with literal `APPLY` confirmation.
- Applied GroupPlans now retain the exact `applied_application_id` and
  `applied_application_digest`, while canonical Group/Membership records exclude
  signal bands, signal provenance, missing-signal disposition, planning seeds,
  targets, and planning strategy.
- Explicit missing-signal `manual`, seeded `random`, and `leave_unassigned`
  GroupPlan dispositions with exact Core `missing_student_signal` authority,
  canonical-digest revalidation, structured provenance, preview invalidation,
  and the narrow approved-unresolved exception for deliberate leave-unassigned.
- Direct `confirm-missing-manual`, `distribute-missing-random`, and
  `leave-missing-unassigned` GroupPlan commands plus a teacher-menu decision
  workflow with missing-only seeded placement preview and no canonical Group or
  Membership creation.
- Deterministic `similar_signal` and `mixed_signal` GroupPlan generation from one
  explicitly selected Core signal/dimension, with shared full-roster size/count
  targets, exact canonical-digest binding, balanced represented-student placement,
  visible unresolved missing coverage, and fail-closed roster races.
- Direct `concord group-plan create-similar-signal|create-mixed-signal` commands and
  bounded teacher-menu signal-plan creation with explicit signal/dimension selection,
  neutral band-distribution diagnostics, in-memory membership preview, reviewed
  roster/digest preconditions, and `CREATE` confirmation without canonical
  Group/Membership creation or Meridian runtime dependency.
- Core-backed grouping-signal discovery, exact immutable signal inspection,
  explicit dimension diagnostics/selection, and teacher-controlled
  `grouping_signal_csv_v1` import with complete/projection identity semantics,
  immutable replay/conflict handling, and no Meridian runtime dependency.
- Direct `concord grouping-signal list|show|diagnose|import-csv` commands plus a
  bounded teacher-menu `Grouping signals` workflow with explicit signal and
  dimension selection, missing-only partial-coverage review, `IMPORT`
  confirmation, and reviewed canonical-digest binding before write.
- Deterministic seeded random GroupPlan generation over the exact Core roster,
  with the versioned `pds-concord:group-plan-random:v1` SHA-256 ranking contract,
  exact size/count targets, balanced nonempty groups, and exact-roster race
  protection.
- Direct `concord group-plan create-random` and bounded teacher-menu random-plan
  creation over the same typed workflow, preserving manual-edit/preview/approval
  behavior while creating no canonical Group/Membership or signal dependency.
- Native planning-only `GroupPlan` and `PlannedGroup` contracts registered in
  Concord's descriptor-driven record graph, with exact mapping conversion,
  Activity/class/context validation, existing immutable record-history
  qualification, and no canonical Group/Membership side effects.
- Typed GroupPlan create, full-proposal replacement, privacy-minimized list/show,
  explicit preview, guarded approval, and cancellation services with exact Core
  roster drift checks, native expected-snapshot concurrency, and no generic
  `applied` transition before #56.
- Teacher-controlled manual GroupPlan authoring with stable plan-local groups,
  exact Core-roster student placement/movement/unassignment, explicit roster
  refresh, preview-to-draft edit behavior, and exact no-op history suppression.
- Strict deterministic UTF-8/BOM-aware `student_id,group` arrangement CSV
  parsing plus atomic new-plan import and existing-plan replacement with bounded
  row diagnostics, no identity normalization, and no persisted source-file data.
- A complete noninteractive `concord group-plan ...` command family and bounded
  teacher-menu `Plan groups` path sharing the same typed services while keeping
  operational Group/Membership management separate and first-class.
- Authenticated Core v0.6.1 `grouping_signal_set_v1` compatibility fixtures, public-contract tests, immutable exchange/digest coverage, exact roster diagnostics, and producer/Meridian isolation checks for Concord's future GroupPlan workflows.
- A Core grouping-fixture verifier that authenticates the vendored golden payload and, when supplied, the exact released fixture ZIP asset.

### Changed

- Signal-backed approval now revalidates the frozen Core signal/dimension/digest
  and current missing set; ordinary plan edits preserve the explicit disposition,
  while changed roster refresh invalidates it for a fresh teacher decision.
- Random and signal-backed generated planning now share one pure full-roster target
  resolution/balanced-size implementation while preserving the frozen #52 random
  ranking and seed behavior.
- The teacher-facing `Groups and Participants` screen distinguishes planning
  (`GroupPlan`/`PlannedGroup`) from operational Group/Membership management;
  GroupPlan approval still creates no canonical Groups, while issue #56 now
  implements the sole explicit canonical application boundary.
- Began the v0.3 development line as `0.3.0.dev0` and raised the Core runtime minimum to `pds-core>=0.6.1,<0.7`; active CI/package/installed acceptance qualifies against the exact released Core v0.6.1 wheel while historical v0.2.0 release evidence remains bound to Core v0.6.0.


### Fixed

## 0.2.0 - 2026-08-16

### Added

- Clean-wheel installed producer acceptance against the authenticated Core
  0.6.0 wheel, covering the complete synthetic collaborative Activity,
  retained Artifact, Score/non-score, registration, two-revision publication,
  Core verification, authorized historical Artifact, withdrawal, registry
  audit, and immutable-history lifecycle.

- A pure `concord.academic_result_reader` facade for exact canonical Academic
  Result Manifest v1 bytes, whole-model validation, exact producer-native
  lookups, and type-sensitive Scoring Scale values.
- A separate `concord.academic_result_artifacts` authorization-gated reader for
  exact historical Concord Artifact evidence with authorization-before-I/O,
  bounded page/Artifact PDF representation, retained-source integrity, and
  privacy-minimized Author/Subject projection.
- A shared neutral Artifact rendering layer used by both consumer reads and the
  existing teacher assembly workflow, including verified-byte rendering and
  fail-closed missing/ambiguous retained evidence.
- Isolated-wheel reader smoke coverage and explicit wheel-content checks for the
  public reader modules without adding sibling PDS runtime dependencies.

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


### Fixed

- Canonicalize derived Concord capability ordering when verifying Core
  Publication Records, including historical reload for supersession, so mixed
  `criterion_scores`, `standards_ratings`, and `moderated_scores` manifests
  agree with Core's canonical capability tuple.

