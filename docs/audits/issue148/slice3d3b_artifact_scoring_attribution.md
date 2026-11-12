# Concord #148 — Slice 3D3B: routine Artifact Score actor review

**Baseline:** `458bf76e08e4d26346c91cb82ffdbb7e473f93e7`, branch `148-persistent-reviewable-teacher-attribution`.

**Scope:** `concord/menu_artifact_scoring.py`, exactly two teacher-facing workflows:

1. `_record_selected_artifact_score`: record the initial prepared routine Score for one explicitly selected Artifact, target and Criterion.
2. `_record_another_criterion`: record a separate prepared Score for another explicit Criterion while retaining only revalidated Artifact, target, and Session context.

Both now call `confirm_actor_write(..., state=state, legacy_confirm=confirm_write)` once, use its `WorkflowActor` directly for `record_prepared_routine_score`, and return `None` without a write when review is canceled. Provider-backed confirmation displays the saved actor and allows a strictly one-action alternate; explicit legacy callers retain their previous one-confirmation contract. Neither path modifies the prepared Score preview or silently reuses a past temporary override.

## Preserved safeguards

- Score eligibility, current Score conflict detection, explicit target/Criterion/Scale selections, and source snapshot equivalence are unchanged.
- Workspace and Activity identity are revalidated after approval, just before the canonical service mutation.
- Each action retains one native `record_prepared_routine_score` service call and truthful Score receipt.
- Multi-criterion continuation remains a separate confirmation and actor selection; it does not automatically inherit the preceding Score's temporary override.
- Historical Scores, Group/student membership, Moderation, Academic Publication, and Core authentication contracts are unchanged.
- This is caller-declared attribution, not authorization or ownership of Core private Notes.

## Qualification

Synthetic tests assert exact actor forwarding, unchanged prepared Score identity, no-write cancellation, separate confirmation on another Criterion, and absence of sticky override. Focused existing Artifact routine scoring, continuation and #148 attribution regressions plus Ruff, mypy, and installed Core-wheel verification guard the change. Full issue-wide acceptance is separate.
