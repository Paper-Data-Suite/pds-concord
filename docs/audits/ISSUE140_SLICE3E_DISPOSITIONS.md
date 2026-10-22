# Concord #140 — Slice 3E: evidence-status ledger for the 18 #138 P0.2 suspects

**Exact parent checkout:** `4a0f75f41b33344556cbcdd2802d0a27f9c1249a` (qualified Slice 3D); Concord v0.3.4 / Core v0.6.6 remain the frozen comparison baseline. **Audit only; no production changes.**

## Accounting, not exaggerated qualification

The Slice 3A create-only candidate inventory originally marked all 18 callsite families `BLOCKED_OR_UNTESTED`. This new, separate create-only Slice 3E ledger maps **each of those exact 18 source families** to the evidence gathered in Slices 3A–3D, without rewriting prior evidence:

| Evidence status | Count | Meaning |
|---|---:|---|
| `SYNTHETIC_MENU_REPRODUCED` | **13** | The real menu handler invokes the real guarded service on a mixed synthetic Activity and fails **before** a deliberately nonexistent Artifact/association/Review/Moderation target is checked. Replaying the exact request with authoritative in-memory Standards crosses that guard and fails on the explicitly absent target; no write occurred. **Not a successful evidence lifecycle.** |
| `SYNTHETIC_DISPLAY_DEGRADED` | **2** | `list_scoring_scales` and `list_criterion_sets` fail to read the existing mixed Activity when Standards is omitted; the menu label helper suppresses both errors and drops human-readable Scale/Criterion labels. Native records are intact. |
| `BLOCKED_OR_UNTESTED` | **3** | `record_routine_artifact_review` and `record_prepared_routine_score` have **real pre-return refusal controls** but no legal eligible returned/assembled positive case; nested `show_criterion_set` is not reached after the prior Criterion Set list read fails. Neither a complete return nor the downstream Score write may be claimed. |

The 13 context-first family statuses are: Author add/update/replace, Subject add/update/replace, multi-Author, multi-Subject, batch confirmation, Detailed Review add/replace, Moderation add/replace. Each points to the exact test/function and parametrized case. The two label statuses point to the Slice 3A synthetic display regression. The three unqualified families preserve a follow-up owner and explicit scope.

This classification answers the **18 specifically named source families only**; it does not imply the full 3,685-row / 10,182-callsite audit has been behaviorally exercised. That broader matrix still needs the Slice 4 coverage guard and reviewer classification. Two `record_prepared_routine_score` *source callsites* are represented by one family row and remain individually subject to future first-score/continued-score acceptance.

## Separate neutral evidence

`prepare_artifact_pages` has an explicitly tested **internal Standards forwarding mechanism** (Slice 3A) and a real **planned/unreturned** synthetic Artifact creation (Slice 3D). No test certifies an end-to-end scan, PDS2 reconciliation of a routed returned page, or deployed canonical file-based Standards resolution. Legitimate no-Standards neutral modes and menu cancellation are tested in earlier slices. Do not turn this scoped status into an unconditional "all Artifact routes are neutral" waiver.

## Handoff and scope

- **#141:** Activity edit missing-Standards context, preserved independently in Slice 2.
- **#142:** 13 Artifact/Review/Moderation menu-context guard failures; routine Score/Quick Review positive-path qualification and repair; future conversion of expected-error witnesses to successful authorized assertions.
- **#143:** Valid dotted Core Standard ID rejected by reusable Criterion Set preset (Slice 2).
- **#142 / #152:** Two silent Score-label degradations and the still-unreached nested Criterion-detail read.
- **#151 / #155 / #159:** Truthful synthetic return/assembly, reviewed evidence/Score acceptance, physical/integrated follow-through. No real student or live classroom data was used or published.

Published Concord-wheel replay is still outstanding; this ledger records repository-context tests from the active branch, not independent installed-v0.3.4 behavior. Strict mypy in the continuation checks audit scripts only; a complete production suite is not implied.

## Qualification and extension

```powershell
python scripts/issue140_slice3a_triage.py --repo . --check
python scripts/issue140_slice3e_dispositions.py --repo . --check
python -m pytest -q tests/test_issue140_slice3e_dispositions.py
```

`--generate` is create-only and is used for first creation. The validator fails if a source family appears/disappears, schema/record count changes, an evidence function disappears, or the checked-in ledger drifts. It does not silently rewrite any committed record. Slice 4 will build on this scoped ledger to enforce broader teacher-operation matrix coverage, owned exceptions, and reviewer protocol.
