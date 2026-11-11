# Concord #148 — Slice 3D2B: Author and bulk-attribution actor review

## Exact scope

Branch `148-persistent-reviewable-teacher-attribution`, beginning at
`c4b6a8974e688e534110fc8dadf26ac17041d821`.

Only `concord/menu_artifact.py` changes in production. Five existing
mutations replace `confirm_write(...)` with the action-scoped
`confirm_actor_write(...)` and pass that reviewed `WorkflowActor` into
exactly one existing canonical request:

1. `_add_author` → `AddArtifactAuthorRequest`
2. `_correct_author` → `ReplaceArtifactAuthorRequest`
3. `_commit_attribution_confirmation` → `BatchConfirmArtifactAttributionRequest`
4. `_add_multiple_authors` → `AddArtifactAuthorsRequest`
5. `_add_multiple_subjects` → `AddArtifactSubjectsRequest`

All existing Artifact snapshot, workspace, evidence, roster, privacy, and
write-context verification remains in its original service path. A cancelled
review produces no canonical service call or success receipt. A temporary
reviewed recorder is discarded after the attempted action, not saved or
queued for the next operation. Legacy explicit session callers retain their
single substantive confirmation.

## Critical Author-versus-recorder invariant

An **Artifact Author** identifies the person/group/student who completed the
work. The **Recorded by** actor identifies the adult who creates or corrects
the Author association. These are different roles. In particular, choosing
**Current teacher** in `_choose_author_semantics` creates an explicit Author
reference to the then-current saved teacher *before* the review. Selecting
another adult in the Advanced recorded-by review must **not** silently turn
the Artifact Author into that recorder. The Author reference is deliberately
preserved, and an explicit, constant Author-name/ID receipt is added for
teacher/authorized-adult Author modes. The action review separately shows its
own current **Recorded by** actor and allows a one-action override.

A changed provider profile during the review is already fail-closed in
`MenuSessionContext.actor_for_action`; no automatic author substitution or
attempted repair is made. The new receipt does not confer or verify authority
or student evidence access. Canonical authorization and durability remain
service-owned.

## Qualification gates

- Authenticated source ZIP, pinned Git HEAD and ten exact blobs, clean tree.
- Ruff lint/format and mypy shadow-file qualification in temporary storage
  *before* changing the working tree.
- Regression AST checks for exact one-review/one-request linkage across five
  mutations; synthetic Author/recorder separation, cancellation, and bulk
  selection tests with no academic workspace.
- Installed Core wheel contract and focused prior Artifact/attribution tests.
- `git diff --check`, exact staged scope and remote branch pin before guarded
  commit/push. A failed gate leaves an uncommitted, reviewable working tree.

## Exclusions

Publication flows, routed Scan menu writes, unrelated role/responsibility
menus, and final cross-menu acceptance remain separately scoped; no global
identity authority, Core/Meridian/Suite file modification, or direct CLI actor
inference is introduced.
