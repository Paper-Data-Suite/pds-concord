# Concord #136 — Slice 3: class-specific saved grouping records

**Branch:** `136-fix-standards-context-and-reusable-group-arrangements`

**Baseline:** `696bd58c533dab19dc91f6274a9bd9e7a890306c` (Slice 2).

**Target:** Concord v0.3.4. No version bump or menu/CLI integration in Slice 3.

## Storage and invariants

Saved arrangement location, under the **existing Core workspace**:

`shared/concord/class-group-arrangements/<school-year>/<class-id>/<arrangement-id>/`

- `library.json`: immutable class/year/owner/arrangement identity.
- `revisions/00000001.json`, `00000002.json`, ...: immutable canonical JSON snapshots, chained through preceding revision SHA-256.
- `current.json`: atomically replaced pointer to the exact current revision and digest.
- `.write.lock`: exclusive revision-writer lock; an unexpected leftover lock requires explicit recovery, never silent deletion.

`concord_class_group_arrangement_v1` is a strict JSON schema. Records carry only a teacher-selected name, owner and writer IDs, class/year, group keys/labels/descriptions, Core student IDs, an explicit roster capture, unresolved student IDs, status, timestamp, and revision lineage. They **never** contain Activity, Group, GroupMembership, Session, Role, Responsibility, Artifact, Score, routing, or publication identities.

The caller supplies a stable **teacher actor ID**, not a password. Access follows the same teacher-restricted local-workspace trust boundary as existing Concord preset storage; the API enforces owner identity but is not itself an authentication or multi-user permissions system. Keep the PDS workspace and backups restricted using operating-system permissions. No roster details should be exposed in public logs or ordinary saved-grouping lists.

Paths are identifier-constrained; symlink and Windows reparse-point traversal is rejected for grouping storage. Revision files are create-only with restrictive permissions where supported; pointer updates are atomic. Partial creation, orphan revisions, extra storage entries, missing revision numbers, hash mismatch, stale concurrency tokens, and unexpected lock files are fail-closed. No automatic cleanup of potentially durable records is performed.

## Class roster and teacher review

Initial save and revision append check the exact class/year against Core class metadata and require that the captured roster IDs equal the **current** Core roster. Within each revision, every captured student must appear exactly once among saved group members or in the explicitly unresolved list. Duplicate groups, overlapping assignments, and unknown/omitted roster members are rejected.

On subsequent browsing, `review_arrangement_roster` compares exact IDs against the current Core roster and reports newly enrolled IDs, departed IDs, unresolved IDs, and retained member count without modifying any record. The comparison never guesses placements or uses names as authority. A changed roster blocks direct save/append until the caller has explicitly reconciled captured student assignments. Cross-class and cross-school-year selection are rejected.

A revision can change name, group content, or status while preserving its immutable history; a retired current revision cannot be amended. Saving/revising these records has **no Activity write path**. No student/group Scores, grading evidence, or canonical Groups/Memberships are created.

## Follow-up slices

Slice 4 introduces reviewed capture from an editable existing GroupPlan (and exact operational Group/Membership snapshot after scope ambiguity checks), and creates **fresh Activity-owned draft GroupPlans** from selected revisions. It will integrate teacher menu and deterministic direct CLI with scoped actor authorization, one review confirmation, roster reconciliation, exact snapshot tokens, and conflict checks; any CSV path is optional. At that later materialization boundary, no canonical Group or Membership exists until separate preview → approve → apply.

Slice 5 performs cross-mode end-to-end scoring/publication and teacher acceptance. Release gating and v0.3.4 qualification follow.

## Focused verification

- Synthetic 29-student, six-table saved arrangement and restart-compatible list/read.
- Owner/class/year restrictions; cross-class comparison fails.
- Immutable revision rename/retirement and current pointer verification.
- Stale write/duplicate create blocks; no unexpected records created.
- Exact roster reconciliation (departed, newly enrolled, unresolved).
- Bad duplicates, overlapping placements, missing student coverage, drifted roster.
- Revision tamper and orphan detection; symlink/reparse fail-closed.

The repository's complete test suite will be run only on the final v0.3.4 release candidate.
