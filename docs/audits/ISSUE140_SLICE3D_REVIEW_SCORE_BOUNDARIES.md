# Concord #140 — Slice 3D: successor Review/Moderation and pre-return routine guards

**Exact start:** Concord `pds-concord` #140 branch after Slice 3C commit `d8ad8e21668596c15493493fc531b53898e4507e`. Frozen release reference remains Concord v0.3.4 / Core v0.6.6. **Audit only:** no production fixes.

## Evidence and classification

1. **Review replacement:** `menu_artifact._replace_review` invokes the real `replace_artifact_review` service. With a mixed synthetic Activity, a nonexistent predecessor intentionally makes the menu hit the **exact missing canonical Standards context guard first**. Replaying the captured unchanged request with the authoritative synthetic Core Standards library crosses that guard and fails specifically with `Artifact Review is not available: ...`. Snapshot and graph are unchanged. **`SYNTHETIC_MENU_REPRODUCED`** (context-first), owner **#142**.
2. **Moderation replacement:** `menu_artifact._replace_moderation` → `replace_moderation_record` follows the same independently checked boundary, ending on the explicit `Moderation Record is not available: ...` only when the canonical library is supplied. **`SYNTHETIC_MENU_REPRODUCED`** (context-first), owner **#142**.
3. **Cancellation and neutral Activity controls:** Both replacement handlers refuse to enter mutation when confirmation is declined. In `evidence_only` mode, absent predecessor identity is rejected without a Standards error. These are **scoped neutral controls**, not permission to omit Standards on Activities or graphs that require it.
4. **Real planned/unreturned Artifact refusal:** A genuine `prepare_artifact_pages` service call creates a **synthetic planned** Artifact and primary page in the disposable Core/Concord workspace, with route generation disabled and no scan, author attribution, Review, or Score. Genuine routine Review/Score read projections reject it as ineligible. Invoking the actual Quick Review and routine first-Score menu handlers refuses to offer teacher write/Score confirmation; neither service records a Review or Score. Runs separately for mixed and `evidence_only` orientations. These are **pre-return refusal controls**, not evidence of returned/assembled workflow acceptance. Owners **#142**, **#151/#155/#159** for positive return/score/physical qualification.

## Strict boundaries

- The fake predecessor selection exists **only in the local menu-choice stub**. No predecessor Record is created, and no successor or correction is written. This demonstrates the exact context-first failure, not authorized business success.
- The genuine planned Artifact is neither synthetically returned nor claimed to represent student performance. No evidence is opened, PDS2 route resolved, group score propagated, individual score inferred, publication submitted, or Meridian grade generated.
- No actual Core Standards Library file is installed by the fixture; the test supplies the deterministic canonical in-memory `StandardsLibrary` explicitly where permitted. Actual deployed Core-library load and installed-wheel replay remain separate gates.
- The records and audit assets from Slices 0, 1, 2, 3A, 3B, and 3C remain untouched. A pass of these tests preserves **failing-before witnesses**; #142 must later convert successful paths to authorized, precise regression assertions.
- Remaining `#138` suspects include the complete returned/assembled Quick Review transition; routine Score entry and continuation on eligible returned evidence; and direct Advanced Score service selection. Those require truthful synthetic return/review preconditions and dedicated follow-on tests, or explicit `BLOCKED_OR_UNTESTED` status and owner. Source-only omitted-kwarg detection cannot certify behavior by itself.

## Reproduction

```powershell
python -m pytest -q tests/test_issue140_slice3d_review_score_boundaries.py
python scripts/issue140_slice3a_triage.py --repo . --check
python scripts/issue140_slice1_census.py --repo . --check
```

All write activity is confined to pytest-managed `tmp_path`. No live OneDrive data, real students, physical scans, external publication, or changes to production Concord/Core are performed.
