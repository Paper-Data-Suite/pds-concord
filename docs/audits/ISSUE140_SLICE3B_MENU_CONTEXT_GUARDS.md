# Concord #140 — Slice 3B: guarded menu operations before Artifact eligibility

**Branch baseline:** `48df2af0c8564242c042360054ecf9bc32382cb0` (Slice 2) followed by `a8b6675bb31dc23fb5d77453644a47f0216d2ce8` (Slice 3A). Published reference is Concord `v0.3.4` / Core `v0.6.6`. Audit-only; **no production edits**.

This intentionally bounded Slice 3B tests a **context-first failure boundary** with the exact synthetic Period 2 Core class and Activity created by `tests/issue140_slice2_fixtures.py`. It does **not** substitute fabricated scanned pages for returned work or invent teacher judgments.

## Evidence — before-Artifact-context guard

In `tests/test_issue140_slice3b_menu_guard.py`, parametrized cases call the **actual menu handlers** and **actual service implementations** for four representative operations:

1. `menu_artifact._add_author` → `add_artifact_author` — **#142**.
2. `menu_artifact._add_subject` → `add_artifact_subject` — **#142**.
3. `menu_artifact._record_review_selected` → `add_artifact_review` (Detailed Review) — **#142**.
4. `menu_artifact._record_moderation` → `add_moderation_record` — **#142**.

Only the menu's input/selection/confirmation UI and workspace-root injection are substituted. The operations use a deliberately nonexistent Artifact/evidence reference to test an ordering property, **not** to simulate a returned or assembled page. On the mixed Activity, the expected failure is the **exact** guarded-graph error `standards_library is required for this Activity.` The test asserts that each handler reached its actual downstream service, that the complete graph and its snapshot sequence remain unchanged, and that **the same captured request with authoritative Standards context crosses the guard and fails on the absent target instead**. This confirms missing context as the first failing boundary rather than mistaking an invalid Artifact fixture for a context regression.

The test also verifies that an `evidence_only` Activity proceeds to the absent-Artifact identity check without a Standards requirement. An independent genuine routine-review **read** of the absent Artifact is exercised for both mixed and evidence-only Activities to distinguish a deliberately Standards-neutral read projection from an unguarded write. Neither positive neutral control certifies behavior with standards-backed Criteria or Score history.

## Classification discipline and remaining work

These are **`SYNTHETIC_MENU_REPRODUCED` context-first guard failures** for the four above handlers only; each is an actual menu-to-workflow invocation, *not* a successful end-to-end returned-work action. Passing assertions preserve reproducibility of the existing bug; the #142 implementation will need to replace error expectations with successful, authorized operations on genuine synthetic return-state fixtures.

- Author/Subject status changes, corrections, multi-add and batch confirmation need independent fixtures and menu-dispatch qualification. No proposed Author is assumed confirmed.
- Quick Review and **routine first/continued Score** need appropriate synthetically returned/assembled, explicitly reviewed evidence, real eligibility and score targets. The current probe does **not** establish those preconditions. Owner: #142 plus #151/#155/#159 physical/end-to-end acceptance.
- Previously qualified Slice 3A Score-label degradation stays separate from Canonical Score identity corruption. Owner: #142/#152.
- `prepare_artifact_pages` internal Standards resolution was proven at forwarding level in Slice 3A; full canonical stored-library retrieval and route creation still need a follow-on positive fixture.
- Matrix/coverage reconciliation and reviewer attestations belong in Slice 4. Do not modify the create-only Slice 0–3A evidence, overwrite its CSVs, or claim the v0.3.4 installed-wheel replay was performed.

## Qualification

```powershell
python -m pytest -q tests/test_issue140_slice3b_menu_guard.py
python scripts/issue140_slice3a_triage.py --repo . --check
python scripts/issue140_slice1_census.py --repo . --check
```

All tests write only to pytest `tmp_path`. No real teacher data, OneDrive location, print/scan process, Meridian operation or external publication is used.
