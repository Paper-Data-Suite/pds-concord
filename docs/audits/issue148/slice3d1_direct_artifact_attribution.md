# Concord #148 — Slice 3D1 direct Artifact actor review

**Starting branch:** `148-persistent-reviewable-teacher-attribution` at `94692deb6d0add86aaef751d382d209b0694e613`.

## Change

Six teacher-menu actions retain their existing substantive confirmation and now
use the action-scoped `confirm_actor_write(...)` result for the canonical request.
This exposes the saved name/ID and optional one-action alternate through the
existing provider-backed UI, without a sticky override or additional automatic
approval. A cancelled confirmation produces no canonical mutation.

| Menu operation | Canonical request |
| --- | --- |
| Prepare Artifact Pages | `PrepareArtifactPagesRequest` |
| Render Artifact Pages | `RenderArtifactPagesRequest` |
| Assemble Returned Artifact | `AssembleArtifactRequest` |
| Add Artifact Subject | `AddArtifactSubjectRequest` |
| Update Artifact Subject | `UpdateArtifactSubjectRequest` |
| Correct Artifact Subject | `ReplaceArtifactSubjectRequest` |

Artifact Subject mutation retains `begin_artifact_write_context` and
`revalidate_artifact_write_context`, including its already-existing CAS and
trustworthy write receipts. Page preparation, rendering and assembly retain
canonical service behavior, including partial-outcome semantics.

## Non-goals / remaining work

- Artifact Author selection and its `attribution_source` snapshot involve
  an earlier actor reference and require separate actor-bound revalidation.
- Artifact Review, Moderation, multi-subject/author batches, Packet and
  Publication flows remain for subsequent census/qualification slices.
- This does not confer authentication, Notes ownership, academic access, or
  publication permission. Direct CLI actor flags remain explicit.

## Safety / verification

Exact branch, HEAD and pinned Git blobs; a manifest-authenticated source archive;
zero unrelated edits; Ruff lint and formatter + mypy projection before apply;
focused synthetic boundary/regression tests; conditional commit and push.
