# Concord #145 — Slice 2: Guided native Criterion Set creation

**Base:** reconciled Concord main `5aeb1ae3f98a4bac1439dcd46a802241ab3a9dc8`, `145-teacher-first-criterion-sets-and-saved-assessment-setup` branch. **Qualified Slice 0/1 candidate tree:** `94f5e6824d7fdf7196753e8a25799ab8a5eacb2b`. Published dependency baseline: Core 0.6.6 wheel. This slice makes no claim about a published Concord wheel or integration-qualified Suite composition.

## Reviewable change

- Add `concord/menu_criterion_guidance.py`: in-memory teacher-facing Criterion builder, Core Focus Standard labels from exact existing Core library, human-readable canonical target kinds, draft add/edit/remove/reorder, scope distinctions and optional native Scale selection. No persistence or student/Group data.
- Patch **only** `concord/menu_scoring.py`: ordinary Criterion Sets option 1 calls the draft guide and uses existing `create_criterion_set` service after complete preview/`CREATE` confirmation. Original interactive ID-oriented native handler remains accessible at option 6, Advanced. No direct CLI behavior changes.
- Add `tests/test_issue145_slice2_native_guided_menu.py` to verify in-memory editing, cancellation, core orientation gates, approval required, no Activity auto-selection and stale snapshot refusal.

**Honest limitation:** This slice creates a native Criterion Set **only**, and labels it so. It does *not* select the newly created Set in the Activity, invoke reusable-preset saving or create Grades or Scores. Slice 3 owns the guarded Create-and-use selection continuation. The draft's generated IDs are final only if the existing canonical service succeeds. A declined review writes nothing.

## Cross-repository noncollision ledger

| Owner | Contract protection |
| --- | --- |
| Core #235–#244 (open infrastructure / Notes / roster / menu contracts) | Use existing published Core 0.6.6 `pds_core.standards` APIs; do not add Core-owned services, shared navigation parser, Notes/Tasks, roster mutations, or future-only imports. `:notes` remains unaffected. |
| Suite #49 (evergreen launcher / release trust) | No change to Suite, trusted release metadata, dependency pins, launch capability classification, or module certification. |
| Suite #51 (teacher experience adoption) | Apply teacher vocabulary and explicit Review/Confirm/Report locally; no duplicate suite-wide renderer, launcher, or conformance assertion. |
| Concord #143/#144 | Preserve installed native/preset materialization and typed Scales; guided creation invokes established `create_criterion_set` only. |
| Concord #146/#150/#152/#153/#162 | Do not expand to all enum menus, whole-lesson copy, score entry, general navigation rewrites, or cross-cutting semantic audit. |
| Meridian #124/#127/#128 | No Grade Item, proficiency policy or implicit standards/grade conversion. |

## Qualification

Guard exact branch, remote main/head, clean index and original HEAD; exact three additive Slice 0/1 source bytes and observed cumulative staged tree. Guard original native menu Git blob. Stage a detached candidate only, then Ruff, strict mypy and focused menu/pure and historical regression tests. Recheck source and destination before mirroring the one menu change and three additive files. Do not stage, commit, push, PR, merge, release or touch classroom work. A failure leaves the original checkout unchanged.
