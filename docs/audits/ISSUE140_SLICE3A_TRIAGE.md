# Concord #140 — Slice 3A: bounded P0.2 context triage

**Release baseline:** Concord v0.3.4 / Core v0.6.6; original immutable Slice 0 manifest retained. **Scope:** audit-only; no production edits, classroom work, publication or external system operations.

This is the **first qualification increment within Slice 3**, not its complete closure. The full #138 P0.2 family is too varied to treat an omitted keyword as an independently verified runtime defect. The status fields in the new source-boundary census intentionally default to `BLOCKED_OR_UNTESTED` and `INVESTIGATE`, with the appropriate issue owner, until dynamic, exact-menu witnesses are available.

## New evidence and tested boundaries

1. **Native scoring labels — synthetic failure witness.** On the disposable **mixed** Period 2 Activity with a canonical Core Standards Library and native two-Criterion/four-level Scale created by Slice 2, `list_scoring_scales` and `list_criterion_sets` succeed with the authoritative Library and reject an otherwise equivalent guarded read without it. The genuine `build_score_teacher_labels(..., include_score_definitions=True)` projection currently catches those exceptions and returns empty Criterion/Scale labels, despite native definitions being present. This is a *display degradation*, not lost or altered canonical Score/Criteria/Scale data. Owner: **#142 / #152**. It does not demonstrate an individual teacher's actual Score-menu encounter.
2. **Page preparation — internally resolved context control.** A bounded synthetic `prepare_artifact_pages` execution probes the genuine code path before any write, verifying that the service either forwards an explicit Standards Library or attempts to resolve one for its supplied Core workspace, then forwards that result to the guarded graph reader. Both branches are tested and leave the synthetic snapshot unchanged. This is a **verified forwarding mechanism**, *not yet a complete `NEUTRAL_VERIFIED` designation*: full canonical Library-file loading, route reconciliation and positive page-preparation acceptance still require an end-to-end test. Owner: **#140 Slice 3B / #151**.
3. **Artifact, routine Review, Score and batch attribution candidate census.** `scripts/issue140_slice3a_triage.py` enumerates **18 explicitly named callsite families** from `menu_artifact.py`, `menu_artifact_scoring.py` and `menu_score_teacher_labels.py`. The checked-in generated `slice3a_candidate_boundaries.csv` records current call lines and whether an explicit Standards argument, unresolved `**kwargs`, or neither is syntactically visible. A missing explicit keyword is *never* classified as a reproduced runtime error by this audit. Owners: **#142 / #152**.

## Carry-forward requirements — Slice 3B and later

- Exercise real menu/service dispatch on disposable prepared/unreturned and actually **synthetically returned** Artifact states, distinguishing missing-context errors from eligibility rejection, invalid fixtures and deliberate refusal to infer authorship or scoring. Where full return evidence cannot be honestly established, retain `BLOCKED_OR_UNTESTED`, assigned to #151/#155/#159.
- Audit Author and Subject add/update/correct, multi-add and batch confirm; routine vs Advanced Review; moderation; first and continuation Score. Record no-write snapshots for each failure. Never auto-confirm attributions or create Score judgments merely to make a test pass.
- Check context behavior through wrappers, `inspect_*` calls, the actual downstream workflow contracts, and exceptions. An underlying workflow might itself resolve authoritative Standards; this source-only census cannot prove otherwise.
- Review `menu_standards_context.py` against the graph's Criteria/Score-based Standards requirement, including the misleading GroupPlan-specific error outside a GroupPlan path.
- Promote an audit row to `SYNTHETIC_MENU_REPRODUCED`/`NEUTRAL_VERIFIED` only with exact evidence reference; update coverage/handoff in Slice 4.

## Offline reproduction

```powershell
python scripts/issue140_slice1_census.py --repo . --check
python scripts/issue140_slice3a_triage.py --repo . --check
python -m pytest -q tests/test_issue140_slice3a_triage.py
```

Use `--generate` only for the first new, create-only inventory. If a source boundary changes, `--check` fails and the source-specific findings must be reviewed before a future new revision is published. Do not alter the frozen Slice 0 receipt.
