# Concord #142 Slice 5B1A — Historical first-Score reader mock

## Trigger and scope

Slice 5B1 passed 13 new first-Score boundary tests. The accepted historical #140
Slice 3D unreturned-Artifact test had 134 passing and two failing variants:
`mixed` and `evidence_only`. Both fail at `inspect_artifact_routine_scoring`
because its monkeypatched lambda accepted only `(class_id, activity_id, artifact_id)`;
the repaired first-Score handler explicitly passes `workspace_root`.

## Exact correction

Only the synthetic test's `score_menu.inspect_artifact_routine_scoring`
monkeypatch is changed. It accepts keyword-only `workspace_root` and forwards
that exact value to the genuine eligibility reader. It does not force a root,
disable the eligibility projection, relax context verification, create Scores,
or change production. The historical test still asserts `None`, no Score
selection, no confirmation, no writes, and identical snapshots.

## Verification requirements

1. Runner dry-run and apply on the exact accepted uncommitted Slice 5B1 state.
2. Two historical target variants pass.
3. The new Slice 5B1 tests pass (13 anticipated).
4. Previously accepted suite passes (136 anticipated).
5. Repository-wide Ruff, `git diff --check`, and project-wide mypy pass.

Only after these gates pass is Slice 5B1 accepted. Slice 5B2 continues with
post-Score snapshot transitions and Score-another-Criterion.

No commits, pushes, actual student data, or canonical Score service modifications.
