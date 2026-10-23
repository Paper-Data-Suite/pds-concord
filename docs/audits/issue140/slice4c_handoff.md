# Concord #140 — Unsigned baseline and handoff (Slice 4C)

**This is an audit of known evidence, not a release qualification or
completed route-by-route semantic review.** No human signoffs recorded.

## Frozen release and observed environment

- Release: Concord 0.3.4 / tag
  `v0.3.4` at `68ddd804d2733fa900ee396ac7a2ba6bd98aa819`.
- Core published-wheel status: verified_published_bytes_and_metadata;
  SHA-256 `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`.
- Concord published wheel: **NOT PROVIDED**. A clean installed-wheel
  replay of v0.3.4 has **not** been authenticated by this audit.
- Captured Windows host: Python
  `3.11.9` / `AMD64`;
  editable installed Concord metadata
  `0.3.2`
  did **not** match the v0.3.4 source tag. Do not mistake this for
  verified release-wheel parity.
- Source-only audit branch parent: `5c8e29c889ad88538adb8c13b8fc5d440c32f5d8`.

## Coverage and review debt

- Teacher/CLI source surfaces: **67**.
- Inventoried operations: **3685**.
- AST calls (all kinds): **10182**.
- Additional calls outside the narrowed operation matrix:
  **7466** (not certified neutral).
- Operation rows still pending contextual contract review:
  **3685**.
- Every queue row: `REVIEW_REQUIRED`, reviewer `UNASSIGNED`.
  Owner proposals are routing suggestions, not approvals.

## 18 specifically named #138 P0.2 service families

| Evidence classification | Families |
|---|---:|
| Context-first guarded menu failures | 13 |
| Silently degraded Score labels | 2 |
| Positive behavior unqualified (including Score) | 3 |

Context-first witnesses use deliberately absent targets, proving the
Standards context guard fires first; they **do not** prove return,
attribution, Moderation or Score succeeds with legitimate evidence.
The two routine Score callsites are represented by one family.

| Operation family | Evidence | Follow-up | Exact witness |
|---|---|---|---|
| `add_artifact_author` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3b_menu_guard.py::test_mixed_teacher_menu_reaches_real_guard_before_missing_artifact (author)` |
| `update_artifact_author` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (update_author)` |
| `replace_artifact_author` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (correct_author)` |
| `add_artifact_subject` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3b_menu_guard.py::test_mixed_teacher_menu_reaches_real_guard_before_missing_artifact (subject)` |
| `update_artifact_subject` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (update_subject)` |
| `replace_artifact_subject` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (correct_subject)` |
| `add_artifact_authors` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (multi_author)` |
| `add_artifact_subjects` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (multi_subject)` |
| `batch_confirm_artifact_attribution` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3c_attribution_guards.py::test_mixed_menu_write_hits_standards_guard_before_missing_relationship (batch_confirm)` |
| `record_routine_artifact_review` | `BLOCKED_OR_UNTESTED` | #142/#151/#155/#159 | `tests/test_issue140_slice3d_review_score_boundaries.py::test_planned_unreturned_artifact_blocks_quick_review_and_routine_score (mixed/evidence_only)` |
| `add_artifact_review` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3b_menu_guard.py::test_mixed_teacher_menu_reaches_real_guard_before_missing_artifact (review)` |
| `replace_artifact_review` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3d_review_score_boundaries.py::test_mixed_successor_menu_guard_precedes_missing_predecessor (review)` |
| `add_moderation_record` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3b_menu_guard.py::test_mixed_teacher_menu_reaches_real_guard_before_missing_artifact (moderation)` |
| `replace_moderation_record` | `SYNTHETIC_MENU_REPRODUCED` | #142 | `tests/test_issue140_slice3d_review_score_boundaries.py::test_mixed_successor_menu_guard_precedes_missing_predecessor (moderation)` |
| `record_prepared_routine_score` | `BLOCKED_OR_UNTESTED` | #142/#151/#155/#159 | `tests/test_issue140_slice3d_review_score_boundaries.py::test_planned_unreturned_artifact_blocks_quick_review_and_routine_score (mixed/evidence_only)` |
| `list_scoring_scales` | `SYNTHETIC_DISPLAY_DEGRADED` | #142/#152 | `tests/test_issue140_slice3a_triage.py::test_mixed_activity_score_label_reader_silently_loses_native_definitions (mixed)` |
| `list_criterion_sets` | `SYNTHETIC_DISPLAY_DEGRADED` | #142/#152 | `tests/test_issue140_slice3a_triage.py::test_mixed_activity_score_label_reader_silently_loses_native_definitions (mixed)` |
| `show_criterion_set` | `BLOCKED_OR_UNTESTED` | #142/#152 | `No positive witness` |

## Other confirmed evidence and ownership

- **#141:** Actual Activity-edit menu failing-before witness:
  `tests/test_issue140_slice2_failing_before.py`.
- **#143:** The valid dotted Core Standard Criterion-preset save
  fails in that same Slice 2 witness; do not normalize the code.
- **#142/#152:** Scoped Artifact/context and Score-label failures
  require repairs; eligible returned Score paths remain unqualified.
- **Internal resolution:** `prepare_artifact_pages` has a tested
  forwarding mechanism and a separate planned/unreturned control,
  not complete physical PDS2 return acceptance.

## Outstanding gates (no assumed passes)

| Gate | Recorded state | Owner | Required next proof |
|---|---|---|---|
| Published Concord v0.3.4 wheel replay | `NOT_PERFORMED` | #154/#155 | Authenticate wheel bytes and replay menu witnesses |
| Full repository test suite on exact audit branch | `NOT_RECORDED` | #140/#155 | Run full pytest/Ruff/mypy and attach exact commit receipt |
| Positive returned/assembled Review and Score lifecycle | `NOT_QUALIFIED` | #142/#151/#155 | Use truthful synthetic returns and explicit human judgments |
| Physical Windows return scan and long-path opening | `NOT_PERFORMED` | #159 | Preserve original scans and qualify installed path behavior |
| Core publication reader and Meridian ingestion | `NOT_PERFORMED` | #155/#159 | Authorize source-versioned publication and downstream read |
| Independent route-level human semantic review | `UNASSIGNED` | #140/#156/#157 | Review the unsigned operation matrix and all other calls |
| Corbeau and Gemini independent attestations | `NOT_PERFORMED` | #156/#157/#158 | Obtain separate reviews after implementation |

## Reproduce, review and transfer

```powershell
python scripts/issue140_slice1_census.py --repo . --check
python scripts/issue140_slice3a_triage.py --repo . --check
python scripts/issue140_slice3e_dispositions.py --repo . --check
python scripts/issue140_slice4a_guard.py --repo . --check
python scripts/issue140_slice4b_review_queue.py --repo . --check
python scripts/issue140_slice4c_handoff.py --repo . --check
```

This report is deterministic from the immutable source receipts.
Its structured JSON records SHA-256 digests for all five inputs.
The editable branch's focused test result and full-suite status
must be attached separately as exact-commit qualification receipts.
Follow `ISSUE140_SLICE4B_REVIEW_QUEUE.md` for review protocol.
No operation may be declared `NEUTRAL_VERIFIED` solely from AST
absence of a keyword or a synthetic failing-before assertion.
Do not publish, overwrite prior audits, or add fake review dates.
