# Concord #140 — Slice 3C: additional teacher-menu Attribution guard witnesses

**Baseline:** Concord issue #140 branch at `d9e0eb4c3b04dbc47ad67f12e9a09033b249ab58` (Slice 3B). Historical released comparison remains Concord v0.3.4 / Core v0.6.6. **Scope: tests and audit documentation only.**

## Evidence objective

Extend 3B's genuine handler → genuine workflow boundary checks to the seven remaining high-priority attribution families:

1. `menu_artifact._update_author` → `update_artifact_author`.
2. `menu_artifact._correct_author` → `replace_artifact_author`.
3. `menu_artifact._update_subject` → `update_artifact_subject`.
4. `menu_artifact._correct_subject` → `replace_artifact_subject`.
5. `menu_artifact._add_multiple_authors` → `add_artifact_authors`.
6. `menu_artifact._add_multiple_subjects` → `add_artifact_subjects`.
7. `menu_artifact._commit_attribution_confirmation` → `batch_confirm_artifact_attribution`.

The only substituted dependencies are menu input, selection/confirmation and the workspace-root injection for a real workflow call. The underlying services are **not mocked**. With the existing two-class, six-cluster disposable Core fixture and a real mixed Activity, each test expects a missing canonical Standards Library error **before** resolution of an intentionally nonexistent Artifact or relationship. The exact request is then replayed with the fixture's real Standards Library and must progress beyond that error, failing instead at the missing identity. Thus these are **context-first failing-before witnesses**, not proof of a valid full mutation.

For each branch, original graph and snapshot sequence must remain unchanged. Controls cover neutral `evidence_only` mode and explicit cancellation before dispatch; cancellation must not create a relationship or confirm a proposal. Synthetic student choices for multi-add are drawn from the actual test Core roster rather than arbitrary identifiers.

## Boundaries not claimed

- No real or synthetic Artifact has been printed, returned, assembled or reviewed in this slice. The test intentionally does **not** assert successful updating, confirming, correcting, or bulk-adding actual relationships. Explicit teacher authority and per-subject evidence must remain in later acceptance tests.
- No routine first Score or Score-another-Criterion is executed; these require genuinely eligible returned Artifact evidence, explicit Review/Moderation and a real Criterion/Scale context. These remain assigned to #142 and the #151/#155/#159 acceptance follow-ups.
- `NEUTRAL_VERIFIED` is not inferred for mixed-mode writes from evidence-only controls. Source-only matrix dispositions and baseline files remain unchanged pending consolidated Slice 4 review.
- The installed Concord v0.3.4 wheel is not replayed here. No publication, OneDrive, real learner data or cross-app writes are accessed.

## Reproduction

```powershell
python -m pytest -q tests/test_issue140_slice3c_attribution_guards.py
python scripts/issue140_slice1_census.py --repo . --check
python scripts/issue140_slice3a_triage.py --repo . --check
```
