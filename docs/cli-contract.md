# Concord CLI and Teacher-Menu Contract

## Status

Implemented through the v0.3.0 deterministic random GroupPlan workflow in issue #52.

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

## Direct command inventory

```text
concord workspace show
concord workspace set <path>
concord workspace validate
concord workspace reset

concord activity create
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

concord role assign
concord role list
concord role end
concord role reassign

concord responsibility assign
concord responsibility list
concord responsibility end
concord responsibility reassign

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
and the existing preview/approve/cancel lifecycle.

`group-plan create-random` requires an explicit seed and exactly one of
`--target-group-size` or `--target-group-count`. The same exact roster, target,
and seed use the documented `pds-concord:group-plan-random:v1` SHA-256 ranking
and balanced partitioning contract. Random creation assigns the complete current
roster, creates a `draft`, and creates no canonical Group or Membership.

Targeted plan edits reject Core-roster drift instead of silently refreshing it.
`refresh-roster` is the explicit operation that preserves remaining placements,
drops departed students, adds newcomers unresolved, preserves empty planned
groups, and creates a draft revision when the roster changed.

Preview and approval remain separate writes. Approval creates no canonical Group
or Membership, and there is no `group-plan apply` command in issue #51. The
`approved -> applied` transaction remains reserved for issue #56.

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
H. Help
Q. Quit
```

An opened Activity includes page preparation/inspection/rendering, Artifact
inspection and returned assembly, explicit Author/Subject management, Artifact
Review, evidence Moderation, Criterion/Scale/Score workflows, and an explicit
Publication surface immediately after Scoring. Teacher writes require
operation-specific words such as `CREATE`, `RENDER`, `ASSEMBLE`, `ADD`,
`UPDATE`, `CORRECT`, `REVIEW`, `MODERATE`, `SCORE`, `REVISE`, `REGISTER`,
`GENERATE`, `PUBLISH`, `WITHDRAW`, and `REBUILD`.
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
adapter. Input is case-insensitive. Ctrl+C and EOF exit cleanly.

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

## Concurrency and no-op behavior

Menus load the current Activity snapshot before collecting a write. The final
commit uses that exact revision. On conflict, Concord does not retry against a
newer revision or force-overwrite it; the teacher is told to reload.

An exact semantic no-op is success and does not advance the snapshot. Canonical
commit success remains valid if disposable catalog rebuilding later fails.

## Boundaries

This contract includes returned Artifact assembly, Author/Subject management,
Artifact Review, evidence Moderation, Criterion Set and Scoring Scale management,
explicit Score entry/revision, and explicit Academic Result Publication. It does
not add the issue #32 consumer-neutral reader, Meridian grading policy, Grade or
proficiency calculation, or destructive collaboration-record deletion.
