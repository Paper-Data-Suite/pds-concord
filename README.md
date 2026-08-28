# pds-concord

Concord is the Paper Data Suite module for paper-first, human-reviewed evidence
created during collaborative classroom Activities. The released v0.2.0 artifact
remains historically qualified against `pds-core` v0.6.0. Current source is the
v0.3.0 development line (`0.3.0.dev0`) and requires `pds-core>=0.6.3,<0.7`
under the suite policy of developing against the latest released PDS
dependencies. The neutral `grouping_signal_set_v1` contract introduced in
Core 0.6.1 remains the grouping-signal boundary consumed by Concord. Official
release artifacts are distributed through GitHub Releases only after independent
review, hosted CI, merge, and exact-main requalification.

The package now includes the collaboration-context workflow required to create
and manage Activities, Sessions, Groups, contextual Group Memberships, Roles,
and Responsibilities. The v0.3 development line also includes teacher-restricted
`GroupPlan` authoring with manual plan-local groups, exact Core-roster placement,
explicit roster refresh, strict `student_id,group` arrangement CSV import, and
deterministic seeded random proposals using exact size/count targets. The v0.3
line now also provides Core grouping-signal discovery, exact signal/dimension
diagnostics, teacher-controlled `grouping_signal_csv_v1` import, and deterministic
`similar_signal` / `mixed_signal` GroupPlan drafts with exact signal provenance,
full-roster target semantics, explicit unresolved missing coverage, and no Meridian
runtime dependency. Issue #55 adds explicit manual/random/leave-unassigned missing-signal
decisions with exact Core revalidation. Issue #56 now adds read-only exact
application previews plus digest/snapshot-bound atomic application of approved
plans to native Group/GroupMembership state. Issue #57 now also defines public
immutable reusable Template Definition/Version contracts with typed page
manifests, rendering inputs, response regions, identity-free defaults and
compatibility, and exact rendering-source SHA-256 binding. Issue #58 now adds the canonical
workspace-level reusable Template library under `shared/concord/templates/`,
strict immutable history, exact rendering-byte storage, head/current Version
selection, successor/activation/retirement workflows, a direct `concord template`
CLI family, and a workspace-level teacher Template Library. Issue #59 now also
defines public immutable reusable Packet Definition/Version contracts with
deterministic ordered components, exact Template Version references, source-owned
external references, positive per-target copy counts, identity-free audience/role
intent, bounded conditions, and typed packet-level rendering rules. Issue #60 now
adds canonical workspace-level Packet persistence under `shared/concord/packets/`,
strict immutable revision/snapshot history, exact Template dependency validation,
head/current selection, successor/activation/retirement workflows, a direct
`concord packet` CLI family, and a workspace-level teacher Packet Library.
Issue #61 now ships a 30-form synthetic collaborative-learning starter Template
catalog using the bounded non-executable `concord_starter_layout_v1` format.
Teachers can browse the packaged catalog read-only, explicitly install one or all
missing starters through the canonical #58 Template authority, and then revise
installed starters through ordinary immutable Template successor workflows.
Stable starter identities, exact packaged rendering digests, idempotent install,
explicit collision handling, and package/wheel qualification prevent hidden
workspace mutation or package-owned overwrite of teacher state.
Issue #62 now implements the first complete Activity-specific Packet generation
and printable-paper path: exact Packet/Template resolution, zero-write target
preview, review-digest-bound generation, fresh PacketInstance/Artifact/Page/Core
PDS2 identities, deterministic starter-layout PDFs, explicit recovery/reprint,
direct runtime Packet commands, and the opened-Activity `Prepare / Generate
Packet` teacher workflow. The same typed service layer supports both fully
noninteractive direct commands and the low-information-density menu.
Issue #63 now adds safe Activity copying: exact source selection, a positive
configuration allowlist, target-specific privacy resolution, one fresh first
Session, zero-write review digests, and create-only commit semantics.
Issue #64 now adds workspace-level reusable Role, Responsibility, Criterion
Set, and Scoring Scale presets with immutable revisions, positive-allowlist
save-from-existing workflows, zero-write reviewed application, and fresh
Activity/assignment materialization that never copies Scores.
Canonical state remains protected by immutable history, exact expected-snapshot
concurrency, and guarded batch commits.

PDS2 Artifact Pages can be prepared, rendered, routed, and recorded as returned
physical occurrences. Returned pages now roll up to Artifact-level return state
and can be assembled reproducibly from exact Core-retained Scan Reference
lineage. Concord also provides explicit zero-to-many Artifact Author and Subject
management with preserved correction history.

Concord now provides explicit Artifact Review and evidence Moderation with
preserved history, exact Subject scope, immutable external-evidence lineage,
plus teacher-controlled Criterion Sets, Scoring Scales, Score Records, Score
Evidence Links, non-score dispositions, and Score revision history. Concord now
also publishes explicitly registered Activity results as immutable
`concord_academic_result_manifest_v1` revisions through Core Publication Records
and the derived academic catalog. Concord now also exposes a consumer-neutral
canonical manifest reader and a separately authorization-gated, bounded Artifact
reader. Concord does **not** calculate Grades or proficiency; Meridian owns
downstream grading/reporting policy. The complete clean-wheel
producer-to-consumer acceptance path established by issue #33 is part of the
authoritative release qualification.

## Requirements and installation

Current Concord development requires Python 3.11 or newer and
`pds-core>=0.6.3,<0.7`. Core is distributed as authenticated GitHub Release
artifacts rather than through PyPI. For v0.3 development, download the released
`pds_core-0.6.3-py3-none-any.whl` from the
[pds-core v0.6.3 release](https://github.com/Paper-Data-Suite/pds-core/releases/tag/v0.6.3).
When qualifying the immutable grouping-signal fixture asset, continue to use
`pds-core-0.6.1-grouping-signal-fixtures.zip` from the historical
[pds-core v0.6.1 release](https://github.com/Paper-Data-Suite/pds-core/releases/tag/v0.6.1).
Then verify/install the Core 0.6.3 wheel before installing Concord from source:

```powershell
python scripts/verify_core_wheel.py path\to\pds_core-0.6.3-py3-none-any.whl
python scripts/verify_core_grouping_fixtures.py path\to\pds-core-0.6.1-grouping-signal-fixtures.zip
python -m pip install path\to\pds_core-0.6.3-py3-none-any.whl
python -m pip install -e ".[dev]"
```

Historical v0.2.0 release installation remains documented by the `v0.2.0`
tag and its release checklist. That tagged source uses Core 0.6.0 and its own
version of `scripts/verify_core_wheel.py`; the current v0.3 development verifier
intentionally authenticates only the Core 0.6.3 wheel.

The Concord v0.2.0 wheel and checksum file remain available through that
historical GitHub Release and must be authenticated against its published
`SHA256SUMS.txt`. For current source development, use the Core 0.6.3 procedure
above.

## Teacher menu

Bare Concord launches the teacher-facing workflow:

```text
concord
concord menu
```

The main menu provides Activity Management, Activity opening, Workspace
Settings, global Scan Routing, the workspace-level Template Library, Packet Library, and Reusable Presets,
contextual Group planning versus operational Group/Membership
management,
Artifact Pages with assembly, Author/Subject,
Review, Moderation, Scoring, and explicit Publication workflows, Help, and Quit.
Controlled teacher screens use:

```text
H. Help
B. Back
M. Main Menu
Q. Quit
```

Every menu write shows a focused review screen and requires the operation word
`CREATE`, `COPY`, `RENDER`, `ASSEMBLE`, `ROUTE`, `RESOLVE`, `CONFIRM`,
`DISTRIBUTE`, `LEAVE`, `APPLY`, `UPDATE`, `ADD`, `CORRECT`, `REVIEW`,
`MODERATE`, `SCORE`, `REVISE`, `ACTIVATE`, `RETIRE`, `END`, `REASSIGN`,
`REGISTER`, `GENERATE`, `PUBLISH`, `WITHDRAW`, or `REBUILD`.
The menu clears between stages,
paginates long selections after ten items, and does not display raw record
bodies or complete graphs.

## Guided classroom Activity setup

Activity Management presents **Create Classroom Activity** and **Continue setup
for an Activity** before the exact advanced tools. The guide creates or safely
copies an Activity, then coordinates Sessions, classroom materials, student
groups, Roles/Responsibilities, assessment setup, final review, and optional
material preparation through the existing Concord workflow services.

Confirmed work is incremental and recoverable. Concord does not persist a
second wizard/checklist record; **Continue setup** derives what is Ready, Needs
attention, Not set up, or Not used from the Activity's canonical records.

The teacher interface follows the Paper Data Suite Information Density rule:
clear/redraw by default when the current action changes, and retain only the
context needed to complete that action. Routine guided screens avoid raw IDs,
JSON, snapshot/revision internals, digests, storage paths, and grouping-signal
internals.

See [guided Activity workflow documentation][guided-activity-doc] for the
complete #65 contract.

[guided-activity-doc]: docs/v0.3.0-guided-create-classroom-activity.md


## Task-oriented opened Activity navigation

After an Activity is opened, routine teacher navigation is organized around the
classroom task rather than Concord's record families:

```text
Plan
Prepare
Collect
Review
Score
Share
Advanced Activity tools
```

Plan contains setup, Sessions, student grouping, Roles/Responsibilities, and
assessment configuration. Prepare contains the classroom-material workflow.
Collect contains returned work, assembly, Author, and Subject actions. Review
contains Artifact Review and Moderation. Score contains actual Score
record/view/revision actions. Share presents existing registration/manifest/
publication services in teacher language.

The exact record-oriented Activity menu remains available through Advanced
Activity tools, and the deterministic direct CLI is unchanged. Task navigation
creates no canonical task state and follows the same Information Density
clear/redraw contract as guided setup.

See [task-oriented Activity menu documentation][task-activity-menu-doc] for the
complete #66 contract.

[task-activity-menu-doc]: docs/v0.3.0-task-oriented-activity-menus.md

## Activity attention and next actions

Issue #67 adds a read-only attention layer over the same six teacher tasks.
Opened Activities preserve the existing `1`-through-`7` task numbering and add
`A. Open next action` only when current canonical state establishes truthful
attention. Activity Management adds `A. Attention needed` for deterministic
cross-Activity discovery. These routes enter the existing task menus; attention
navigation creates no second workflow implementation or persisted task state.

Concord also exposes the same privacy-minimal facts through Core v1:

```text
paper_data_suite.module_operations
    concord = concord.pds_operations:get_module_operations_profile
```

The #67 profile provides attention only. `readiness_provider` remains `None` for
issue #68, which owns readiness plus suite doctor/launcher/mixed-intake work.

See [Activity attention and next-action documentation][activity-attention-doc]
for the complete semantic, privacy, count-unit, aggregation, and installed-wheel
contract.

[activity-attention-doc]: docs/v0.3.0-activity-attention-next-actions.md

## Direct CLI

Direct commands are deterministic and fully noninteractive. They never clear
the screen, pause, or call `input()`.

```text
concord workspace show|set|validate|reset
concord activity create|list|show|update|set-status
concord activity copy-preview|copy
concord session add|list|show|update|set-status
concord group create|list|show|update|set-status
concord group member add|list|end|reassign
concord group-plan list|show|create-manual|create-random|add-group|edit-group|remove-group
concord group-plan create-similar-signal|create-mixed-signal
concord group-plan confirm-missing-manual|distribute-missing-random|leave-missing-unassigned
concord group-plan place-student|unassign-student|refresh-roster
concord group-plan import-arrangement|replace-arrangement|preview|approve|cancel
concord group-plan application-preview
concord group-plan apply
concord grouping-signal list|show|diagnose|import-csv
concord role assign|list|end|reassign
concord responsibility assign|list|end|reassign
concord role-preset list|show|validate|create|revise|retire|apply-preview|apply|save-preview|save
concord responsibility-preset list|show|validate|create|revise|retire|apply-preview|apply|save-preview|save
concord criterion-preset list|show|validate|create|revise|retire|apply-preview|apply|save-preview|save
concord scale-preset list|show|validate|create|revise|retire|save-preview|save
concord template list|show|version-list|version-show
concord template create|revise|activate|update|retire-version|retire
concord template starter-list|starter-show
concord template starter-install|starter-install-all
concord packet list|show|version-list|version-show
concord packet create|revise|activate|update|retire-version|retire
concord packet instantiate-preview|instantiate|instantiate-resume
concord packet instance-list|instance-show|instance-render|generation-render
concord criterion-set create|list|show|revise|select
concord scale create|list|show|revise
concord score add|list|show|replace
concord artifact list|show|assemble
concord artifact author add|list|show|update|replace
concord artifact subject add|list|show|update|replace
concord artifact review add|list|show|replace
concord moderation add|list|show|replace
concord artifact page prepare|list|show
concord artifact render
concord scan route
concord scan review list|show|resolve
concord publication register|registration-show|registration-update
concord publication manifest-preview|manifest-generate|manifest-list|manifest-show
concord publication publish|supersede|withdraw|series-show
concord publication catalog-list|catalog-rebuild
```

Mutating direct commands require explicit actor context. Mutations of existing
Activity state require the exact current snapshot revision. Activity copy is a
separate create-only exception: `copy-preview` performs zero-write review and
`copy` requires its exact digest before creating a fresh target Activity/Session. Template mutations after initial Template creation likewise
require `--expected-snapshot`, but that value is the exact reusable Template
library snapshot rather than an Activity snapshot. Packet mutations after
initial Packet creation use the same flag for the exact reusable Packet-library
snapshot. Reusable preset revisions/retirement use exact preset revisions;
preset application and save-from-existing use zero-write review digests.
Reusable Packet-library commands require neither class nor Activity
identity; Activity-specific `packet instantiate-*`, `instance-*`, and
`generation-render` commands require explicit class/Activity context instead.
`group member add` accepts
repeated `--student-id` values and
commits the selected Memberships atomically.

See the [CLI contract](docs/cli-contract.md) for command behavior, exit codes,
workspace rules, and concurrency semantics.

## Workspace and identity

Core owns workspace resolution, saved workspace configuration, class metadata,
rosters, student identity, standards libraries, and shared B/M/Q navigation.
Concord uses those public APIs rather than copying their storage or parsing
rules.

Mutating Concord workflows initialize an absent resolved workspace through Core.
Read-only operations and help do not. Core resolution priority remains:

1. explicit runtime root;
2. `PDS_WORKSPACE_ROOT`;
3. saved Core configuration;
4. Core default.

Activity creation requires an existing Core class with valid class metadata.
Membership creation uses the Core class roster; a Concord Group is never a
student identity.

## Collaboration workflow semantics

Activity creation commits exactly one Activity and its required first Session
in one guarded batch. Later Activity, Session, Group, Membership, Role, and
Responsibility changes use the exact current snapshot revision. Exact no-ops do
not create new snapshots.

Membership, Role, and Responsibility reassignment preserves the predecessor and
creates an explicit successor. Storage revision and domain supersession remain
separate concepts. Membership does not establish authorship or contribution;
Role does not prove fulfillment; Responsibility does not prove performance.

Standards-based and mixed Activities require a Core standards profile and one or
more ordered Focus Standards validated through the Core standards contract.
Evidence-only and local-criteria-only Activities do not require standards
configuration.

Detailed behavior is documented in the
[workflow implementation guide](docs/implementation/activity-session-group-workflows.md).
Criterion, Scale, and Score behavior is documented in the
[scoring implementation guide](docs/implementation/criterion-scale-score-recording.md).
Academic-result registration, manifest generation, publication lifecycle, and
catalog reconciliation are documented in the
[publication implementation guide](docs/implementation/academic-result-publication.md).
Consumer-neutral manifest interpretation and authorization-gated bounded Artifact
access are documented in the
[consumer reader guide](docs/implementation/academic-result-reader.md). The v0.3
Core 0.6.3 dependency and neutral grouping-signal boundary are documented in the
[grouping-signal integration guide](docs/v0.3.0-core-grouping-signal-integration.md).
The planning-only record/lifecycle foundation is documented in the
[GroupPlan contract](docs/v0.3.0-group-plan-contract.md), and issue #51's manual
authoring, arrangement CSV, direct CLI, menu, roster-refresh, and privacy
boundaries are documented in the
[manual Group planning guide](docs/v0.3.0-manual-group-planning.md).
Issue #52's exact seeded SHA-256 ranking, balanced partitioning, direct CLI/menu
creation, refresh behavior, and privacy boundaries are documented in the
[deterministic random planning guide](docs/v0.3.0-random-group-planning.md).
Issue #53's exact discovery, diagnostics, dimension selection, Core CSV import,
privacy, producer-neutrality, and signal-selection boundary are documented in the
[grouping-signal workflow guide](docs/v0.3.0-grouping-signal-workflows.md).
Issue #54's deterministic similar/mixed algorithms, full-roster targets, exact Core
signal binding, partial-coverage behavior, direct CLI/menu creation, lifecycle reuse,
and privacy/dependency boundaries are documented in the
[signal-backed Group planning guide](docs/v0.3.0-signal-group-planning.md).
Issue #55's explicit missing-signal decisions, deterministic missing-only random
distribution, approval exception, privacy boundary, and #56 handoff are documented
in the [missing-signal disposition guide](docs/v0.3.0-missing-signal-disposition.md).
Issue #56's deterministic application identity, exact preview digest, context
resolution, atomic Group/GroupMembership write set, privacy boundary, direct CLI,
and teacher `APPLY` flow are documented in the
[approved GroupPlan application guide](docs/v0.3.0-group-plan-application.md).
Issue #58's workspace-level authority, immutable Template history, rendering-byte
integrity, head/current selection, authoring transport, direct CLI, and teacher
menu are documented in the
[Template storage and revision workflow guide](docs/v0.3.0-template-storage-revision-workflows.md).
Issue #59's immutable Packet lineage/version/component contracts, exact Template
references, copy/audience/role/condition semantics, external ownership, rendering
rules, and #60/#62 handoffs are documented in the
[Packet Definition contract](docs/v0.3.0-packet-definition-contract.md).
Issue #60's workspace-level Packet authority, immutable history, exact Template
dependency eligibility, authoring transport, direct CLI, teacher menu, and #62
handoff are documented in the
[Packet storage and revision workflow guide](docs/v0.3.0-packet-storage-revision-workflows.md).
Issue #61's 30-form package-owned starter catalog, bounded
`concord_starter_layout_v1` rendering specifications, explicit/idempotent install,
privacy defaults, direct CLI, teacher menu, package qualification, and #62/#64
boundaries are documented in the
[starter collaborative-learning Template library guide](docs/v0.3.0-starter-template-library.md).
Issue #62's runtime PacketInstance contract, exact prepare/commit boundary,
target/copy/input/privacy resolution, Core PDS2 allocation, deterministic PDF
rendering, retry/reprint semantics, direct CLI/menu workflow, installed-wheel
smoke, and accepted visual-review gate are documented in the
[Activity-specific Packet instantiation and rendering guide](docs/v0.3.0-packet-instantiation-rendering.md).
The clean installed-wheel producer lifecycle and its Core verification,
authorization, audit, and immutability boundaries are documented in the
[installed acceptance guide](docs/implementation/installed-end-to-end-acceptance.md).
Canonical persistence and recovery rules remain documented in the
[canonical storage guide](docs/implementation/canonical-storage.md).

## Validation

Run focused checks with `python -m pytest`, `python -m ruff check .`, and
`python -m mypy`. Run the complete repository validation on Windows with:

```powershell
.\run_tests.ps1 -CoreWheel path\to\pds_core-0.6.3-py3-none-any.whl
```

The cross-platform equivalent is:

```text
python scripts/validate_repository.py --core-wheel <wheel>
```

The validator authenticates the exact Core v0.6.3 wheel, runs pytest, Ruff,
strict Mypy, documentation checks, package builds, Twine validation, package
inspection, isolated installed-wheel workflow/menu/public-reader smoke tests, and
the full installed Activity-to-publication producer acceptance before
`git diff --check`.

Core exposes routing through `paper_data_suite.modules` and publication through
`paper_data_suite.publication_producers`. These remain independent integration
surfaces. Concord declares exactly one routing profile and one separate
publication-producer profile. Publication profile discovery is metadata-only and
does not require a sibling PDS package or mutate the workspace.

The implementation sequence is tracked by
[umbrella issue #22](https://github.com/Paper-Data-Suite/pds-concord/issues/22).
See the [documentation index](docs/README.md), the
[accepted ADR index](docs/decisions/README.md), and the
[foundation review](docs/design/foundation-review.md) for governing design. The
[release audit](docs/v0.2.0-release-audit.md),
[compatibility freeze](docs/v0.2.0-release-compatibility.md), and
[four-phase release checklist](docs/release_checklist.md) record the v0.2.0
release boundary.
