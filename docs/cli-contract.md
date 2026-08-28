# Concord CLI and Teacher-Menu Contract

## Status

Implemented through the v0.3.0 Activity attention and next-action workflow in issue #67.

## Two interfaces, one service layer

Concord exposes two presentation surfaces over the same typed workflow services:

- the direct CLI for scripts, tests, automation, and experienced users;
- the teacher-facing menu for normal interactive classroom use.

Neither interface invokes the other to perform domain work. Shared services do
not prompt, clear the screen, or print output.

## Top-level commands

```text
concord
concord menu
concord --help
concord --version
```

Bare `concord` and `concord menu` launch the teacher menu. Help and version are
direct, read-only operations and never launch the menu.

## Teacher attention navigation

Issue #67 adds read-only attention discovery without changing the direct CLI or
renumbering issue #66's opened-Activity task menu. When truthful attention exists,
an opened Activity may show:

```text
A. Open next action
```

Activity Management also offers:

```text
A. Attention needed
```

These `A` commands are controlled Concord menu choices on those specific screens;
they do not replace Core-owned H/B/M/Q navigation. A next action routes to the
existing Plan, Prepare, Collect, Review, Score, or Share menu and performs no
mutation merely by being selected. Attention screens follow the same
clear/redraw Information Density contract as the rest of the teacher menu.

The underlying native projection and Core v1 adapter are documented in
[`v0.3.0-activity-attention-next-actions.md`](v0.3.0-activity-attention-next-actions.md).

## Direct command inventory

```text
concord workspace show
concord workspace set <path>
concord workspace validate
concord workspace reset

concord activity create
concord activity copy-preview
concord activity copy
concord activity list
concord activity show
concord activity update
concord activity set-status

concord session add
concord session list
concord session show
concord session update
concord session set-status

concord group create
concord group list
concord group show
concord group update
concord group set-status

concord group member add
concord group member list
concord group member end
concord group member reassign

concord group-plan list
concord group-plan show
concord group-plan create-manual
concord group-plan create-random
concord group-plan create-similar-signal
concord group-plan create-mixed-signal
concord group-plan confirm-missing-manual
concord group-plan distribute-missing-random
concord group-plan leave-missing-unassigned
concord group-plan add-group
concord group-plan edit-group
concord group-plan remove-group
concord group-plan place-student
concord group-plan unassign-student
concord group-plan refresh-roster
concord group-plan import-arrangement
concord group-plan replace-arrangement
concord group-plan preview
concord group-plan approve
concord group-plan cancel
concord group-plan application-preview
concord group-plan apply

concord grouping-signal list
concord grouping-signal show
concord grouping-signal diagnose
concord grouping-signal import-csv

concord role assign
concord role list
concord role end
concord role reassign

concord responsibility assign
concord responsibility list
concord responsibility end
concord responsibility reassign

concord role-preset list|show|validate|create|revise|retire
concord role-preset apply-preview|apply|save-preview|save
concord responsibility-preset list|show|validate|create|revise|retire
concord responsibility-preset apply-preview|apply|save-preview|save
concord criterion-preset list|show|validate|create|revise|retire
concord criterion-preset apply-preview|apply|save-preview|save
concord scale-preset list|show|validate|create|revise|retire
concord scale-preset save-preview|save

concord template list
concord template show
concord template version-list
concord template version-show
concord template create
concord template revise
concord template activate
concord template update
concord template retire-version
concord template retire
concord template starter-list
concord template starter-show
concord template starter-install
concord template starter-install-all

concord packet list
concord packet show
concord packet version-list
concord packet version-show
concord packet create
concord packet revise
concord packet activate
concord packet update
concord packet retire-version
concord packet retire
concord packet instantiate-preview
concord packet instantiate
concord packet instantiate-resume
concord packet instance-list
concord packet instance-show
concord packet instance-render
concord packet generation-render

concord criterion-set create
concord criterion-set list
concord criterion-set show
concord criterion-set revise
concord criterion-set select

concord scale create
concord scale list
concord scale show
concord scale revise

concord score add
concord score list
concord score show
concord score replace

concord artifact list
concord artifact show
concord artifact assemble

concord artifact author add
concord artifact author list
concord artifact author show
concord artifact author update
concord artifact author replace

concord artifact subject add
concord artifact subject list
concord artifact subject show
concord artifact subject update
concord artifact subject replace

concord artifact review add
concord artifact review list
concord artifact review show
concord artifact review replace

concord moderation add
concord moderation list
concord moderation show
concord moderation replace

concord artifact page prepare
concord artifact page list
concord artifact page show
concord artifact render

concord scan route
concord scan review list
concord scan review show
concord scan review resolve

concord publication register
concord publication registration-show
concord publication registration-update
concord publication manifest-preview
concord publication manifest-generate
concord publication manifest-list
concord publication manifest-show
concord publication publish
concord publication supersede
concord publication withdraw
concord publication series-show
concord publication catalog-list
concord publication catalog-rebuild
```

Use `concord <family> <command> --help` for exact flags.

## Direct-command rules

Direct commands are fully noninteractive. They do not call `input()`, clear the
screen, or pause. A direct mutation is itself the user’s explicit write intent.

Mutations support explicit actor context:

```text
--actor-id
--actor-label
--actor-role
```

`--actor-id` is required. Actor identity is provenance, not authentication and
not Artifact authorship.

Reusable preset management is workspace-level. Preset application and
save-from-existing use zero-write previews plus exact review digests; applying
a preset creates fresh native state and never creates Scores. Preset revision
and retirement create immutable successor versions rather than editing history.

Activity copying is a special create-only workflow. `activity copy-preview`
performs strict zero-write preparation and prints a deterministic review
digest. `activity copy` requires that exact digest, re-reads the source,
revalidates Core class/standards/privacy, and creates a fresh draft Activity
plus one fresh planned Session. It never accepts `--expected-snapshot`,
overwrite, merge, force, source Session identity, or source operational state.

Every write after initial Activity creation requires:

```text
--expected-snapshot <positive integer>
```

There is no force-overwrite option. A stale expected snapshot is a conflict.

`group member add` accepts repeated `--student-id` values. Optional repeated
`--membership-id` values must have the same cardinality and order. All selected
Memberships are validated and committed in one guarded batch.

`group-plan` mutations also require the exact expected Activity snapshot.
Plan-local edits never allocate canonical `Group` or `GroupMembership` records.
Arrangement import uses the exact case-sensitive two-column `student_id,group`
contract documented in `v0.3.0-manual-group-planning.md`; no delimiter sniffing,
identity normalization, quick approval, or quick application occurs.

`grouping-signal` is a Core class-level exchange family rather than an Activity
mutation family. Every action requires `--class-id` and may use
`--workspace-root`. `list` and `show` remain metadata/count oriented;
`diagnose` requires an explicit `--dimension-id` and exposes only aggregate
band counts plus exact missing/wrong-class/unknown IDs needed for correction.
`import-csv` uses Core `grouping_signal_csv_v1` and does not require actor or
Activity expected-snapshot arguments. A `dimension_projection` additionally
requires explicit `--new-signal-set-id` and timezone-aware `--new-created-at`.

`template` is a workspace-level reusable family and never requires class or
Activity identity. `list`, `show`, `version-list`, and `version-show` are
read-only and do not initialize an absent workspace. Initial `create` requires
explicit Template/Version IDs, `--authoring-file`, `--rendering-spec`, and actor
provenance; `--activate` is explicit. `revise`, `activate`, `update`,
`retire-version`, and `retire` require `--expected-snapshot`, whose value is the
exact current **Template-library** snapshot, not an Activity snapshot. There is
no force/latest/skip-preview mode. Authoring uses
`concord_template_authoring_v1`; authoritative provenance, sequence,
predecessor, rendering digest, lifecycle, and storage snapshot state are derived
by Concord.

The packaged starter Template catalog is a read-only package resource until an
explicit install command runs. `starter-list` and `starter-show` never initialize
an absent workspace. `starter-install` requires `--starter-key` plus actor
provenance and creates the exact packaged initial Version as active/current
through the #58 Template storage authority. `starter-install-all` preflights all
30 stable identities, fails before writes on incompatible collisions, and then
installs only missing starters in deterministic order. Exact existing installs
are idempotent no-ops; teacher metadata revisions, successor Versions, and
retirement are never reset. A later failure after earlier successful independent
Template creates is exit code 4 partial success and is safe to reconcile by
rerunning install-all.

`packet` is also a workspace-level reusable family and never requires class or
Activity identity. `list`, `show`, `version-list`, and `version-show` are
read-only and do not initialize an absent workspace. Initial `create` requires
explicit Packet Definition/Version IDs, `--authoring-file`, and actor provenance;
`--activate` is explicit. `revise`, `activate`, `update`, `retire-version`, and
`retire` require `--expected-snapshot`, whose value is the exact current
**Packet-library** snapshot, not an Activity or Template snapshot. Authoring uses
`concord_packet_authoring_v1`; exact Template components pin both `template_id`
and `template_version_id`, while external components retain source-owned
`ModuleRecordRef` values without requiring sibling modules to be installed.
There is no force/latest/current-Template substitution mode.

The Activity-specific Packet runtime commands added by #62 are deliberately
separate from workspace-level Packet-library revision. `instantiate-preview`
requires class, Activity, Session, exact Packet Definition/Version, and actor
context, performs no writes, and prints the exact `review_digest`.
`instantiate` requires that digest and re-runs current canonical resolution before
allocating runtime identities. Optional strict `--options-file` input may carry
only explicit component choices and teacher rendering bindings. An optional
caller-supplied `--generation-id` is a retry/reconciliation identity, not a way
to clone an existing generation. `instantiate-resume` reconciles already-durable
native generation state with immutable Core routes. `instance-list` and
`instance-show` are read-only. `instance-render` and `generation-render` reuse
existing route identities for completed reprints. There is no force, skip-review,
manual route-ID, QR-payload, or latest-Template substitution mode.

## Exit codes

```text
0  success or exact no-op replay
1  validation, read, write, or integrity failure
2  command-line usage error
3  expected-revision or lock conflict
4  structured partial success
```

Ordinary results go to stdout and errors to stderr. Partial-success reporting
preserves whether a snapshot was published and its canonical identity.
Persisted page-level routing failures return 1 because teacher review is still
required; exit 4 is reserved for durable cross-store/output partial success.
That includes routing-review redispatch whose handler filed evidence before
Core resolution metadata failed to persist.

## Workspace behavior

Core owns workspace resolution and initialization. Concord preserves Core’s
resolution order:

1. explicit `--workspace-root`;
2. `PDS_WORKSPACE_ROOT`;
3. saved Core workspace configuration;
4. Core default workspace.

Mutating workflows may initialize an absent resolved workspace through Core.
Read-only commands and help never create it. Initialization does not implicitly
save a new workspace preference. An invalid selected root never causes silent
fallback to another location.

Activity creation requires an existing Core class and metadata. Membership
workflows use the Core-owned class roster.

## Activity and Session creation

`activity create` creates exactly one Activity and its required first Session in
a single `commit_record_batch` call with no expected prior snapshot. The current
pointer cannot expose an Activity-only graph.

Later Activity and Session revisions preserve durable identities and use exact
expected-snapshot protection. Session sequence remains positive and unique
within the Activity. No destructive Session delete command exists.

## Groups and contextual assignments

Groups belong to one Activity and may have an optional same-Activity parent and
Effective Context. Parent cycles are rejected. Group Membership, Role, and
Responsibility contexts contain one or more existing Sessions.

Membership add uses Core roster identities. Reassignment creates a new durable
Membership ID with `supersedes_membership_id`; it does not rewrite the historical
Membership into a different identity.

## Group planning versus operational Groups

`GroupPlan` is teacher-restricted proposal state and remains distinct from the
operational `Group`/`GroupMembership` command family.

The `group-plan` family supports manual draft creation, plan-local group metadata,
exact roster-student placement/movement/unassignment, explicit roster refresh,
strict arrangement CSV import/replacement, deterministic seeded random creation,
deterministic similar-signal/mixed-signal creation, and the existing
preview/approve/cancel lifecycle.

`group-plan create-random` requires an explicit seed and exactly one of
`--target-group-size` or `--target-group-count`. The same exact roster, target,
and seed use the documented `pds-concord:group-plan-random:v1` SHA-256 ranking
and balanced partitioning contract. Random creation assigns the complete current
roster, creates a `draft`, and creates no canonical Group or Membership.

`group-plan create-similar-signal` and `group-plan create-mixed-signal` require an
explicit Core signal set, explicit dimension, and exactly one size/count target.
They accept no seed. The target is resolved against the full exact Core roster;
selected-dimension missing students remain unresolved. Success reports the exact
Core canonical signal digest and aggregate group/coverage counts without emitting
student-band rows. Both commands create only a `draft` GroupPlan and explicitly
report `Canonical Groups created: no`.

For a signal-backed plan with current Core `missing_student_signal` findings,
`confirm-missing-manual`, `distribute-missing-random`, and
`leave-missing-unassigned` record the teacher's explicit disposition. These
commands use the signal ID/digest/dimension already frozen into the GroupPlan;
they do not accept signal reselection arguments. Random disposition requires
its own explicit `--seed`, separate from `GroupPlan.seed`. All three mutations
return a previewed plan to `draft` and report `Canonical Groups created: no`.

Targeted plan edits reject Core-roster drift instead of silently refreshing it.
`refresh-roster` is the explicit operation that preserves remaining placements,
drops departed students, adds newcomers unresolved, preserves empty planned
groups, and creates a draft revision when the roster changed.

Preview and approval remain separate writes. Signal-plan approval revalidates the
exact bound Core signal/dimension/digest and current missing set. `manual` and
`random` require zero unresolved students; `leave_unassigned` is the sole narrow
exception and requires the unresolved set to equal the exact current missing set.
Approval itself creates no canonical Group or Membership. Issue #56 then exposes
`group-plan application-preview` as a zero-write exact write-set preparation
command and `group-plan apply` as the only direct approved-plan application
mutation. Application requires the exact application ID, semantic application
digest, and expected Activity snapshot from the reviewed preview. It revalidates
the current Core roster and any frozen signal binding, resolves an explicit
fallback Effective Context when needed, and commits the applied GroupPlan plus
all canonical Groups and Memberships in one guarded batch. There is no force,
latest, skip-preview, or ignore-digest mode.

Within the teacher menu, `Groups and Participants` exposes separate `Plan groups`
and `Manage Groups and Memberships` paths over the same shared service layer.

Role and Responsibility reassignment use the corresponding explicit successor
fields. Assignment records are contextual facts, not proof of authorship,
contribution, fulfillment, quality, or performance.

## Teacher menu

The main menu is intentionally compact:

```text
Concord

1. Activity Management
2. Open an Activity
3. Workspace Settings
4. Scan Routing
5. Template Library
6. Packet Library
H. Help
Q. Quit
```

An opened Activity includes page preparation/inspection/rendering, Artifact
inspection and returned assembly, explicit Author/Subject management, Artifact
Review, evidence Moderation, Criterion/Scale/Score workflows, and an explicit
Publication surface immediately after Scoring. Teacher writes require
operation-specific words such as `CREATE`, `RENDER`, `ASSEMBLE`, `ADD`,
`UPDATE`, `COPY`, `CORRECT`, `REVIEW`, `MODERATE`, `SCORE`, `REVISE`, `REGISTER`,
`GENERATE`, `CONFIRM`, `DISTRIBUTE`, `LEAVE`, `APPLY`, `PUBLISH`,
`WITHDRAW`, `ACTIVATE`, `RETIRE`, and `REBUILD`.

The workspace-level Template Library requires no Activity selection and exposes
listing, creation, Version history, successor creation, activation, metadata
update, Version retirement, and whole-Template retirement. Template writes use
the same prepare/commit workflow services as the direct CLI and require
`CREATE`, `REVISE`, `ACTIVATE`, `UPDATE`, or `RETIRE` confirmation.

The workspace-level Packet Library likewise requires no Activity selection and
exposes listing, creation, Version history, successor creation, activation,
metadata update, Version retirement, and whole-Packet retirement. Packet
previews show bounded ordered component/reference intent and use the same
`CREATE`, `REVISE`, `ACTIVATE`, `UPDATE`, or `RETIRE` confirmations.

An opened Activity additionally exposes `Prepare / Generate Packet`. That
workflow chooses one active exact Packet Version and one explicit Session,
resolves conditional components and teacher rendering inputs, displays exact
target/Artifact/Page/route counts plus the review digest, and requires literal
`GENERATE` before committing native generation state. The same submenu lists and
inspects Packet Instances, resumes incomplete route preparation, and renders or
exactly reprints existing instances without asking the teacher for Artifact Page
IDs, route IDs, or QR payloads.

Global routing review remains
available when a failed scan has no trustworthy Activity locator.

Within controlled submenus:

```text
H. Help
B. Back
M. Main Menu
Q. Quit
```

Concord reuses Core’s B/M/Q parser and unwind semantics and adds only the H
adapter. Navigation input is case-insensitive. The issue #63 Activity-copy
write confirmation is deliberately stricter and requires uppercase `COPY`
exactly. Ctrl+C and EOF exit cleanly.

Teacher writes use staged disclosure:

```text
menu -> selection -> focused action -> confirmation -> concise result -> menu
```

Every teacher write requires one operation-specific confirmation word, including
`CREATE`, `RENDER`, `ROUTE`, and `RESOLVE` for this integration. Artifact Page
and Routing Review lists both provide next/previous navigation in ten-row pages,
including selection beyond the first page. Raw JSON, dataclass representations,
complete record graphs, and full provenance are not ordinary menu output.

Effective Context offers one Session, several selected Sessions, or a starting
Session through the remaining Activity. Group revision exposes ordinary label,
description, status, parent, and Effective Context changes without changing the
Group identity.


### Task-oriented opened Activities

Issue #66 changes the routine opened-Activity menu from a record-family list to:

```text
1. Plan
2. Prepare
3. Collect
4. Review
5. Score
6. Share
7. Advanced Activity tools
```

Plan composes Continue setup, Sessions, student Groups/GroupPlans,
Roles/Responsibilities, assessment configuration, and Activity editing. Prepare
uses the existing saved-material and reviewed Packet-generation paths. Collect
routes returned work, assembly, Authors, and Subjects. Review routes Artifact
Review and Moderation. Score exposes only actual Score record/view/revision;
Criterion Set and Scale configuration remain under Plan. Share wraps the existing
registration/manifest/publication services in teacher language.

Advanced Activity tools preserves the complete exact record-oriented menu,
including Artifact Pages, Scoring, Publication, Packet generation/recovery, and
diagnostic detail. The task layer adds no canonical task-status records.

The task screens extend the Information Density contract: clearing/redrawing is
the default, only current-action context remains visible, and routine screens
avoid IDs, paths, hashes, digests, raw JSON, grouping-signal internals, and
publication internals that are unnecessary for the current teacher decision.

This reorganization is interactive presentation only. The direct command
inventory above remains unchanged and noninteractive.

See `docs/v0.3.0-task-oriented-activity-menus.md` for the complete issue #66
contract.

## Concurrency and no-op behavior

Activity-context menus load the current Activity snapshot before collecting a
write. The Template Library analogously prepares against the exact current
reusable Template snapshot, and the Packet Library prepares against the exact
current reusable Packet snapshot. Final commits use those exact revisions. On conflict,
Concord does not retry against a newer revision or force-overwrite it.

An exact semantic no-op is success and does not advance the snapshot. Canonical
commit success remains valid if disposable catalog rebuilding later fails.

## Boundaries

This contract includes returned Artifact assembly, Author/Subject management,
Artifact Review, evidence Moderation, Criterion Set and Scoring Scale management,
explicit Score entry/revision, explicit Academic Result Publication, reusable
Packet storage/management, Activity-specific Packet generation, and safe
Activity copying. It does not add issue #64 reusable assignment/scoring presets,
Meridian grading policy, Grade or proficiency calculation, or destructive
collaboration-record deletion.

## Guided teacher setup versus direct CLI

Issue #65 adds interactive **Create Classroom Activity** and **Continue setup**
flows to the teacher menu. These are presentation/orchestration surfaces, not a
new direct-command format. Existing `concord activity create`, `concord activity
copy-preview|copy`, Group/GroupPlan, preset, scoring, Template/Packet, and Packet
runtime commands remain deterministic and noninteractive.

The teacher guide and direct CLI converge on the same typed workflow services.
The guide generates routine IDs internally, uses classroom-facing labels, and
derives resume status from canonical records. It does not persist wizard state.
The interactive guide follows the suite Information Density policy by
clearing/redrawing when the current action changes and retaining only information
needed for that action. Direct CLI output remains command-oriented and does not
clear the screen.

See `docs/v0.3.0-guided-create-classroom-activity.md` for the complete contract.
