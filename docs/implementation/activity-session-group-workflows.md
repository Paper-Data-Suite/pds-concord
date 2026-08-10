# Activity, Session, and Group Workflow Implementation

## Status and scope

Issue #26 implements Concord’s first teacher-operable collaboration-context
vertical slice. It builds on the native record layer from issue #24 and the
guarded canonical persistence layer from issue #25.

Implemented workflow families are:

- Activity and required first Session;
- later Session creation and revision;
- Activity-specific Group creation and revision;
- contextual Group Membership add, end, and reassignment;
- contextual Role assignment, end, and reassignment;
- contextual Responsibility assignment, end, and reassignment;
- workspace inspection/configuration wrappers;
- a noninteractive direct CLI;
- and a teacher-facing menu.

Artifact, routing, Review, Moderation, scoring, publication, and grading remain
outside this issue.

## Architecture

Presentation is separated from application behavior:

```text
direct CLI parser/handler -> typed workflow service
teacher menu              -> same typed workflow service
workflow service          -> Core public APIs + Concord models/storage
```

Workflow services live under `concord.workflows`. Direct handlers live under
`concord.cli_app`. Teacher-facing workflows live in the `concord.menu_*`
modules. No presentation module writes canonical files directly.

## Workspace and Core ownership

Core owns workspace roots, saved workspace configuration, class metadata,
rosters, student display helpers, standards libraries, identifiers,
`ModuleRecordRef`, `ModuleWorkRef`, and shared B/M/Q navigation.

A mutating Concord service resolves the workspace through Core and calls
`ensure_workspace_root` when the selected root is absent. Read-only services use
non-mutating inspection and return an empty/not-found result without creating
state. Workspace initialization does not save a preference automatically.

Activity creation requires an existing Core class with valid metadata. Student
Memberships resolve against the Core class roster and persist only the typed
Core student reference. Concord does not copy the roster into native records.

## Actor and provenance

`WorkflowActor` supplies the durable actor identity and optional display/role
snapshots used to create native provenance. Direct mutations require an explicit
actor ID. The teacher menu asks for the actor ID on the first write and reuses it
in memory for the launched menu session.

This actor context is provenance only. It is not authentication, a credential,
or evidence of Artifact authorship.

## Activity creation

`create_activity_context` constructs one native `Activity` and one native
`Session` and submits both to `commit_record_batch` with
`expected_snapshot_revision=None`.

Defaults are:

```text
Activity status: draft
first Session status: planned
first Session sequence: 1
```

The initial current pointer is published only after the complete graph passes
native and applicable Core standards validation.

Supported scoring orientations are:

```text
evidence_only
standards_based
mixed
local_criteria_only
```

Standards-based and mixed Activities require a Core standards profile plus one
or more ordered Focus Standards. The immutable Core library is passed into the
guarded commit. Evidence-only and local-criteria-only Activities do not require
standards configuration.

## Revisions and concurrency

Every later mutation carries the exact current snapshot revision. Services do
not force-overwrite or silently retry a stale request. Exact semantic no-ops are
returned as no-op replays without an unnecessary snapshot.

Ordinary field corrections keep the same durable record identity and create a
new storage revision when content changes. Storage revision is not domain
supersession.

## Sessions

Sessions can be added, listed, shown, and revised. Sequence is positive and
unique within the Activity. Supported revision fields follow the native Session
contract, including scheduling/actual timing, status, label, and notes.

No destructive Session delete workflow exists.

## Groups

Groups can be created empty or together with initial Memberships, Roles, and
Responsibilities through one guarded service-layer commit. This composite setup
validates references against the complete candidate Group context before
publishing it. A Group may have a same-Activity parent and optional Effective
Context. Native graph validation rejects missing parents, cross-Activity
parents, and parent cycles.

Ordinary Group revision can change label, description, status, parent, and
Effective Context while preserving Group identity.

## Effective Context

Memberships, Roles, and Responsibilities always identify one or more Sessions.
The teacher menu presents the common choices in stages:

```text
1. One Session
2. Several selected Sessions
3. From a Session through the remaining Activity
```

The last form preserves the starting sequence and the
`applies_to_remaining_activity` intent. Later assignment changes create later
records/revisions; they do not rewrite the earlier contextual history.

## Memberships

Memberships use `ParticipantReference(participant_kind="core_student",
owning_system="core")` resolved from the Core roster.

The batch `add_memberships` service accepts one or more `GroupMemberSpec`
values, validates all students and contexts, rejects duplicate/overlapping
active Memberships, and commits the complete set atomically. The direct CLI
supports repeated student IDs; the teacher menu supports multi-selection.

Ending a Membership revises its status without deleting it. Reassignment is one
atomic batch that revises the predecessor to `reassigned`/`superseded` and
creates a successor with a new ID and `supersedes_membership_id`. The participant
identity is preserved while Group/context may change.

Membership does not establish authorship or prove contribution.

## Roles

Roles support the built-ins `facilitator`, `recorder`, `observer`, `speaker`,
`researcher`, `builder`, and `presenter`, plus valid namespace-qualified custom
keys.

When a Role references a Membership, participant/Group/context consistency is
validated. Ending preserves the record. Reassignment creates an explicit
successor through `supersedes_role_assignment_id`.

An assigned Role does not prove fulfillment, participation, authorship, or
performance.

## Responsibilities

A Responsibility assignee is either an explicit participant or a Concord Group
reference. Context and optional Group relationships are validated against the
Activity. Ending is non-destructive; reassignment creates an explicit successor
through `supersedes_responsibility_assignment_id`.

A Responsibility records what was assigned. It does not prove completion,
quality, contribution, or performance.

## Teacher interaction

Bare `concord` launches the menu. The menu uses Core’s B/M/Q semantics with a
Concord H=Help adapter. Screens clear between ordinary stages, selection lists
paginate after ten items, and only essential Activity context is retained.

Every teacher write uses a focused review screen and requires `CREATE`,
`UPDATE`, `ADD`, `END`, or `REASSIGN`. Confirmation screens honor H/B/M/Q before
writing. On an expected-snapshot conflict, the teacher gets an explicit
Reload/Back/Main/Quit decision; Reload performs a fresh read only and never
retries or force-overwrites the failed write. Partial-success screens state
whether the current pointer was published and preserve compact snapshot/digest
and durable-path-count identity without dumping filesystem paths. Result screens
otherwise show only the affected identity, snapshot, no-op state, and at most a
concise derived-state warning.

## Direct CLI

The direct command surface is documented in [`../cli-contract.md`](../cli-contract.md).
It is fully noninteractive and uses stable exit codes for success, ordinary
failure, usage errors, conflicts, and structured partial success.

## Persistence boundary

All collaboration writes call `commit_record_batch`. Workflow and presentation
modules do not construct revision paths, serialize canonical envelopes, replace
`current.json`, acquire storage locks directly, or patch SQLite.

Canonical reads do not depend on the derived SQLite catalog. A catalog failure
after canonical publication does not invalidate the committed snapshot.

## Validation and installed-wheel coverage

Tests cover service behavior, CLI behavior, menu navigation, screen density,
workspace bootstrap, exact expected-snapshot conflicts, no-op behavior,
Membership/Role/Responsibility supersession, parent cycles, roster identity, and
batch atomicity.

The installed-wheel smoke test now exercises:

- read-only help without workspace creation;
- quit-only bare/explicit menu launch;
- temporary Core class and roster creation;
- Activity plus first Session creation through the workflow service;
- Group and multi-student Membership creation;
- a later Session revision and historical revision loading;
- current graph reconstruction;
- and disposable catalog rebuild/query.

All smoke data is synthetic and stored under temporary directories outside the
source checkout and installed package.
