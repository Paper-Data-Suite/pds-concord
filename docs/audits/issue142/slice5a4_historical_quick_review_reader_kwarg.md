# Concord #142 — Slice 5A4: historical Quick Review resolver mock

## Failure established in the Windows checkout

The Slice 5A3 test-only patch successfully passed preflight and applied. The two historical #140 unreturned-evidence cases then progressed into the newly repaired Quick Review inspection call, but the historical monkeypatch for `inspect_artifact_routine_review` accepted only three positional arguments. The production call now forwards the pinned `workspace_root` as a keyword. Both cases failed with a mock `TypeError`, before the intended ineligibility decision.

## Narrow correction

In the single historical test function `test_planned_unreturned_artifact_blocks_quick_review_and_routine_score`, replace the monkeypatched inspection lambda with one that requires and forwards the canonical `workspace_root` keyword to the real `inspect_artifact_routine_review` service. Do not intercept, drop, or override this pinned workspace path with a default. Leave all other test assertions unchanged, including unreturned evidence refusing Quick Review and routine Score, absence of write confirmations, and snapshot invariance.

## Installation and acceptance

The installer checks the exact #142 issue branch, baseline HEAD and origin, rejects staged or unexpected worktree changes, reconstructs the exact accepted Slice 5A3 historical test from baseline and source-only recipes, checks prior production Quick Review and its new test, and verifies archive manifest hashes. Only `tests/test_issue140_slice3d_review_score_boundaries.py` and this audit note are writable. No production file, frozen #140 audit, or teacher workspace is touched; no stage, commit, or push. Run the targeted two historical cases, full 136-case test group, repository-wide Ruff, `git diff --check`, and project-wide mypy. Acceptance awaits actual Windows results.
