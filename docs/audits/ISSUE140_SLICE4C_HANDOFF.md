# Concord #140 — Slice 4C: reproducible, unsigned audit handoff

**Exact starting branch commit:** `5c8e29c889ad88538adb8c13b8fc5d440c32f5d8` (qualified Slice 4B). Frozen baseline source: Concord `v0.3.4` at `68ddd804d2733fa900ee396ac7a2ba6bd98aa819` with Core `v0.6.6`. **No production edits.**

## Deliverables

The source-only archive installs `scripts/issue140_slice4c_handoff.py`, `tests/test_issue140_slice4c_handoff.py`, and this note. Its offline `--generate` action creates exactly two **new** files under `docs/audits/issue140/`:

- `slice4c_handoff.json`: machine-readable, unsigned handoff with original receipt hashes, release / environment qualifications, all 18 scoped P0.2 findings, exact evidence test references, proposed issue owners, and remaining gates.
- `slice4c_handoff.md`: human-facing reproduction and review document, derived from the same source records.

`--check` regenerates both in memory and verifies byte equality. It never overwrites source audit files. A source or conclusion change requires separately reviewed successor evidence, not retroactive edits to frozen Slice 0–4B records.

## Interpretation: do not falsely close P0 defects

- C1 / **#141**: Activity-edit missing canonical Standards context is captured as a failing-before menu reproduction, not fixed.
- C2 / **#143**: Valid dotted Standard rejected by reusable Criterion Set preset, captured as failing-before and not fixed.
- P0.2 / **#142**: The 13 context-first Artifact/Review/Moderation failures demonstrate a **guard before an intentionally nonexistent downstream target**. They are not success scenarios for legitimately returned work.
- Score labels / **#142/#152**: Two demonstrated silent label degradations; `show_criterion_set` still needs an independent nested-path witness.
- Quick Review / routine Score: currently tested **pre-return refusal** only. Genuine returned/assembled positive cases, first and continued Score, and Core/Meridian acceptance require later proof.
- **67 source surfaces, 3,685 operation rows, 10,182 AST calls, and 7,466 other calls** are source-accounting numbers—not reviewer-certified contract outcomes. All 3,685 operations remain `context_fields_pending`; no reviewer is assigned or signed.

## Published wheel / installed distribution honesty

The frozen Slice 0 receipt verified Core `v0.6.6` published-wheel bytes but marks the Concord `v0.3.4` wheel **not provided**. The captured host is Windows AMD64, Python 3.11.9; the installed editable Concord metadata indicated **0.3.2**, although the examined source tag indicated 0.3.4. Do not describe branch tests as an isolated published-wheel replay. The full repository suite on the final audit commit is separately required; focused green tests cannot substitute for it.

## Reviewer transfer and unperformed gates

All row-level review signoffs are deliberately blank. Hand this report and the immutable matrix/queue to #141, #142, #143 and the later routing owners. For each route, independent reviewers must inspect actual downstream contracts, authority, Core class/Standards/roster context, actor, privacy, provenance, snapshot/CAS, stale/cancel/recovery, and legitimate neutral/self-resolving cases. Exact operation IDs and tests are required for promotion. Do not invent Core publications, returned scans, student Scores, human judgments, reviewer approvals or Meridian ingestion.

The generated report records explicit outstanding gates for authenticated Concord wheel replay (#154/#155), full exact-commit suite (#140/#155), positive synthetic return/Score lifecycle (#142/#151/#155), physical Windows/long-path return (#159), Core/Meridian end-to-end (#155/#159), and Corbeau/Gemini independent review (#156/#157/#158). These are **not** claimed complete by this slice.

## Commands

```powershell
python scripts/issue140_slice4c_handoff.py --repo . --generate
python scripts/issue140_slice4c_handoff.py --repo . --check
python scripts/issue140_slice4a_guard.py --repo . --check
python scripts/issue140_slice4b_review_queue.py --repo . --check
python -m pytest -q tests/test_issue140_slice4c_handoff.py
```

`--generate` is for first installation only. Re-running it once outputs exist deliberately refuses to overwrite. No network access, teacher workspace, physical device, Core/Concord runtime import or privileged location is used by the handoff script.
