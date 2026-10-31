# Concord #142 Slice 4B — Detailed Review and Moderation successors

Scope: `concord/menu_artifact.py` (`_replace_review`, `_replace_moderation`), the executable historical `tests/test_issue140_slice3d_review_score_boundaries.py` test harness, one new synthetic regression suite, this audit handoff. No changes to models, Core, immutable #140 audit CSV/captures, scoring or installed school workspace.

## Context repair

Each successor menu opens a single operation-scoped `ArtifactWriteContext` from the selected Activity, loads the current predecessor using both the **pinned Core workspace root** and **canonical Core Standards library**, refuses a predecessor whose snapshot differs from the pinned snapshot, obtains the teacher's replacement fields, and on confirmation revalidates the root + snapshot and calls the existing service with the same exact workspace and Standards authority. The services retain native immutable predecessor/current-head checks, identity uniqueness, semantic validation, atomic correction record publication, and compare-and-swap.

- **Review successor:** updates Review judgment by recording a separate Review and a `review_correction` record. Never modifies evidence or creates a Score.
- **Moderation successor:** creates a successor and `moderation_revision` record, preserving evidence reference and explicit Subject scope exactly. No implicit authorship or scoring authority.
- **Historical #140 Slice 3D tests:** retains the absent predecessor and real services as negative controls; makes synthetic Core root/Standards context explicit and replaces the old expected missing-Standards error with the intended missing-target error. Frozen source audit remains immutable.

## Synthetic acceptance boundaries

The new tests use genuine synthetic Core/Concord temporary-workspace records, but the Artifact is `return_not_expected` and has no scans or returned student work. Reviews must be **not ready** and Moderation is **not to be used for scoring**. Positive successor tests cover four scoring orientations, linked correction and persistent predecessor, unmodified evidence and Subject scope, cancellation, stale selection, workspace drift, concurrent Activity revision, and historical predecessor refusal. Actual returned-evidence acceptance and routine scoring remain open for later slices.

## Gates required before acceptance

- Read-only preflight then apply with exact Git branch, HEAD, origin and worktree inventory; reconstruction of accepted Slice 4A menu/reader sources.
- New `tests/test_issue142_slice4b_successor_review_moderation.py` and existing Slice 4A tests.
- Historical `tests/test_issue140_slice3b_menu_guard.py`, `tests/test_issue140_slice3c_attribution_guards.py`, `tests/test_issue140_slice3d_review_score_boundaries.py`.
- Prior #142 Slice 0–3 and #141 workspace identity tests.
- Ruff and project-wide mypy.

No stage, commit, push, or use of real classroom workspace data.
