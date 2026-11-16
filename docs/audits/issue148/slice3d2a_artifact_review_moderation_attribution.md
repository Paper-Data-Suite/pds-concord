# Concord #148 — Slice 3D2A: Artifact author status, review, and moderation

Status: candidate; Windows qualification and commit pending.

## Scope

The menu's existing one-action `confirm_actor_write` is used for exactly six consequential operations:

1. `_update_author` — current Artifact Author status, `UpdateArtifactAuthorRequest`.
2. `_quick_review_selected` — routine ready/qualified Review, `record_routine_artifact_review`.
3. `_record_review_selected` — detailed Artifact Review, `AddArtifactReviewRequest`.
4. `_replace_review` — immutable Review successor, `ReplaceArtifactReviewRequest`.
5. `_record_moderation` — evidence Moderation, `AddModerationRecordRequest`.
6. `_replace_moderation` — immutable Moderation successor, `ReplaceModerationRecordRequest`.

Each substantive confirmation returns either the exact actor for this operation or cancellation. The actor is forwarded unchanged to the existing canonical request/service. The two `bool` Review helpers retain `False` on cancellation (rather than introducing a `None` return).

## Preserved invariants

- Continue to use `begin_artifact_write_context` and `revalidate_artifact_write_context` and `artifact_write_kwargs`. There is no attempt to add an independent authoritative workspace, bypass snapshot validation or mutate records after a declined review.
- Retain existing Artifact/Review/Moderation policies, evidence/Subject scopes and correction relationships. The saved teacher profile is never changed by temporary one-operation attribution.
- Existing `legacy_confirm` remains the confirmation path for explicit non-provider menu contexts. No changes to noninteractive CLI commands, Core, Suite, Meridian or any durable storage schema.
- Excludes Author creation and correction (`_choose_author_semantics` may capture `actor_reference(state.require_actor())` for the *authorship* identity itself, which is distinct from the *recorder* provenance); these require an explicit no-mismatch implementation in Slice 3D2B. Also excludes bulk Author and Subject records and publication.

## Test evidence

`tests/test_issue148_slice3d2a_artifact_review_actor.py` statically checks six one-review/one-write actor bindings with strict cancellation shapes. Synthetic dynamic tests cover Author status, Quick Review, and Moderation (reviewed alternate vs cancel), no service call after cancel, and no sticky change to the default actor. The runner tests adjacent #142, Artifact menu, and #148 regressions.

The runner checks an authenticated source manifest, ten pinned Git blobs and an empty change scope, projects the patch in temporary storage, and executes Ruff lint/format and mypy shadow-file validation **before** editing the checkout. Subsequent gates include source compilation, installed Core verification, focused pytest, staged diff hygiene, exact upstream HEAD and conditional commit/push.
