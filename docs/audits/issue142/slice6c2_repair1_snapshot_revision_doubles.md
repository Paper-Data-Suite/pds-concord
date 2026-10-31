# Concord #142 — Slice 6C2 Repair 1: snapshot-aware historical doubles

The first Slice 6C2 Windows qualification ran 16 of 18 #28/#29 tests
successfully. Two #29 tests stopped at the existing explicit snapshot
freshness guards because their historical `SimpleNamespace` test doubles
lacked `snapshot_revision`.

This test-only repair supplies `snapshot_revision=9` on the selected Artifact
and Moderation predecessor respectively, corresponding to each test's
`_activity()` fixture. It does **not** stub snapshot comparisons, change
canonical operation context resolution, or alter production behavior.

- `test_record_review_uses_explicit_context_and_review_confirmation`
- `test_moderation_revision_preserves_exact_predecessor_scope`

The runner reconstructs the accepted Slice 6C2 test file exactly from pinned
Git HEAD and the SHA-256-authenticated Slice 6C2 recipe before applying this
repair. All old source/frozen #140 evidence files are preserved.

**Status:** Candidate; Windows focused, integrated and static gates pending.
