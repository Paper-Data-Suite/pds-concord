# Concord #148 — Slice 3C3A Guided Rubric Attribution

## Source and ownership

Starting branch `148-persistent-reviewable-teacher-attribution`, commit
`ac71b57a` (full commit pinned by the runner). Published Core 0.6.6 remains
required; no Core, Suite or Meridian change is introduced.

## Bounded implementation

- `_create_guided_criterion_set`: existing substantive CREATE/CREATE & USE review
  now returns exactly one operation-scoped actor. For CREATE & USE, the same
  reviewed actor is forwarded to both the initial immutable Criterion Set
  creation and the subsequent independently guarded Activity selection.
  Existing partial/indeterminate service receipts remain untouched.
- `_revise_criterion_set`: review chooses the actor recorded on the immutable
  successor. The existing current-head/CAS and historical Score protections
  remain unchanged.
- `_use_existing_criterion_set`: review chooses the actor recorded on the exact
  rubric-selection write, replacing the post-review lookup of the default.
- For guided creation and revision, the existing pre-review validation still
  runs against the saved actor. If the reviewed actor differs, the identical
  pure validation reruns with the effective actor's provenance immediately
  before canonical mutation. No second confirmation is introduced.

For sessions without an injected attribution provider, `legacy_confirm` retains
existing direct test/standalone semantics. Profile-backed menus use the normal
one-action Advanced override. This is self-declared provenance, **not** identity
verification, permission granting, publication authority or Notes ownership.

## Qualification requirements

- Source AST guards for exactly three reviewed operations; request actors must
  derive from the reviewed variable, never an unchecked post-review lookup.
- Two-stage guided create uses the same actor for both writes, with no automatic
  retry or rollback and unchanged canonical selection verification.
- Alternate actor receives provenance revalidation; cancellation writes nothing;
  the saved default actor is not modified.
- Exact branch/head and Git blobs; Ruff/format/mypy/installed Core; focused
  guided and native-rubric regressions; automatic commit/push after qualification.

## Deliberately deferred

Native Scale and Criterion preset **save/import/materialization review digests**
retain actor-bound requests created *before* confirmation. Those require
actor-aware re-preparation and exact digest forwarding and are assigned to
Slice 3C3B, not changed here. Other Artifact, Group, Packet, Publication and
Scan writes remain subject to the #148 final callsite audit and qualification.
