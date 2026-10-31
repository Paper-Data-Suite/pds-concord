# Concord #142 — Slice 5A2: historical Quick Review synthetic workspace

## Windows regression evidence

After accepted Slice 5A1, all 9 new Quick Review tests passed. The 127-test earlier regression suite reported 125 passed and 2 failed. Both failures were the same parametrized historical test (`mixed` and `evidence_only`) in `test_issue140_slice3d_review_score_boundaries.py`. The new Quick Review operation's structural guard used the default workspace because the older test only patched downstream read functions; for mixed orientation it also had not persisted the disposable Core Standards library. No scores were written by either failure.

## Exact repair

Within that single historical test only, (1) persist the fabricated canonical Core Standards library for mixed orientation, and (2) pin `authority.resolve_read_workspace_root` to the disposable fixture root before invoking `_quick_review_selected`. Keep the existing eligibility, pre-return refusal, no-confirmation, no-mutation, no-Score and unchanged-graph assertions intact. No production path is changed.

## Verification

Run all 9 Slice 5A tests, the 127 prior tests, repository-wide Ruff, git diff --check and project mypy. These are required acceptance gates rather than claimed outcomes. The #140 frozen audit and real teacher/classroom workspaces remain outside the patch. No stage, commit or push.
