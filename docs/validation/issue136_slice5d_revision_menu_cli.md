# Concord #136 — Slice 5D: Revision management in teacher menu and direct CLI

**Baseline:** `8fcc3c5b0e84d87f47270ecc9de87cbba95b0728` (Slice 5C).
**Branch:** `136-fix-standards-context-and-reusable-group-arrangements`.
**Target:** v0.3.4 (no version bump).

## Scope

- The existing **Manage saved groupings** menu permits read-only member review and immutable history browsing; active groupings additionally support **Rename**, **Replace from editable GroupPlan**, and **Retire** with a reviewed literal confirmation and preserved B/M/Q navigation.
- The `concord saved-grouping` CLI adds `history`, `change-preview`, and `change`. The direct path requires explicit teacher actor, class, current revision, SHA-256 and a two-step review digest for writes. `replace-from-plan` additionally requires an exact source Activity, editable GroupPlan, and expected Activity snapshot. No new grouping service or manual revision writes are introduced.
- History is loaded only after verifying the entire current canonical chain, teacher ownership, exact class/year scope and SHA integrity; summaries do not print student IDs. Detailed student placements remain within the authenticated teacher menu review.
- Metadata-only rename and retirement work despite roster drift. Membership replacement remains subject to Core-roster validation in the Slice 5C service.
- Retired groupings remain visible in history but cannot be renamed, revised or reused. No Activity, Score, membership, publication, or Core roster is modified.

## Example direct commands

Use synthetic IDs in documentation; real school/learner IDs are not logged.

```powershell
python -m concord saved-grouping history --class-id class-demo --actor-id teacher-demo --arrangement-id six-tables
python -m concord saved-grouping change-preview --class-id class-demo --actor-id teacher-demo --arrangement-id six-tables --action rename --new-name 'Six Table Groups' --expected-revision 1 --expected-sha256 <current-SHA256>
python -m concord saved-grouping change --class-id class-demo --actor-id teacher-demo --arrangement-id six-tables --action rename --new-name 'Six Table Groups' --expected-revision 1 --expected-sha256 <current-SHA256> --review-digest <preview-digest>
```

The preview and change commands revalidate the current immutable head. They do not silently retry stale reviews. The same `ChangeGroupingRequest` service is used by menus and CLI.

## Tests / gates

Focused tests verify parsing, exact-request forwarding, preview-before-confirm, refusal to write on cancel, history privacy, terminal retirement, recovery and existing menu dispatch. Run once, followed by Ruff, mypy, `pip check`, `git diff --cached --check`, and guarded commit/push. Full suite is reserved for the v0.3.4 qualification phase.
