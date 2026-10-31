# Concord #142 — Slice 1: operation-scoped context (source candidate)

**Status:** Candidate source-only boundary; no existing Artifact handlers or CLI call sites are
rewired in this slice. Not an end-to-end Author/Subject/Review/Moderation/Score
acceptance, published-wheel qualification, or physical-return witness.

## Boundary

`concord/menu_artifact_write_context.py` provides:

1. `begin_artifact_write_context(selected, operation=..., workspace_root=...)`
   resolves one read-only Core workspace (menu default: active workspace),
   verifies the exact Core class and Concord Activity identities, loads the
   structurally verified snapshot/history, and rejects a stale selection.
2. `_needs_standards` uses the actual Activity orientation, persisted
   standard-backed Criterion/Score history, **and** an explicit proposed
   standard-backed operation flag. Neither a neutral orientation nor a
   previous preview is proof of a standards-neutral write.
3. The canonical Core library is read **from the pinned root only when needed**.
   The existing Concord `validate_core_standards` authority is invoked against
   the actual snapshot graph to check current profile and Focus membership,
   active/deprecated Focus, and relevant Criteria. The service and storage
   still validate the actual candidate/commit.
4. `revalidate_artifact_write_context` checks the exact expected revision,
   active-root continuity for menu calls, selected class/work identity,
   snapshot revision **and digest**, and loads/validates current Core Standards
   again before a mutator. It never silently retries, substitutes a different
   work item, edits Core records, or initializes a workspace.
5. `artifact_write_kwargs` forwards the pinned `workspace_root` and conditional
   `standards_library` explicitly to existing mutators. It is not permission
   to create a Score, infer individual authorship, or skip return evidence.
6. The pre-existing GroupPlan helper's missing-library error removes only the
   misleading statement that no **GroupPlan** was created. Its call signatures
   and validation rules are otherwise unchanged.

## Obligations retained by next slices

- Slice 2–3: Wire the concrete Author/Subject and batch teacher handlers **after**
  confirming snapshot selection and any Core roster/Group/Role semantics; verify
  immutable history, conflict and cancellation. Do not replace menu reads
  indiscriminately with structural-only authorization.
- Slice 4–5: Integrate Review/Moderation and both routine Score menu call sites;
  prove positive synthetic **returned/assembled** evidence and teacher-entered
  judgments. The service owns all CAS, privacy, evidence and immutable-link rules.
- Slice 6: Add exact #140 operation IDs to #162 successor ledger and qualify
  full source, Core v0.6.6 installed-wheel parity, frozen audit replay, and CI.
  All historical #140 artifacts remain unchanged.

## Evidence level

Slice 0: 15 families / 16 call sites inventoried; six Windows focused tests
passed in the teacher's `2026-10-26` log. Slice 1 tests are new and are **not**
claimed passed until run on the targeted branch and Python/Core wheel.
No real student data, publication, on-device scans, remote writes or cross-store
atomicity are involved. `#152` retains native Score-label UX ownership;
`prepare_artifact_pages` retains its independent canonical self-resolution.
