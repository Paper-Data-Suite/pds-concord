# Concord #142 — Slice 3: multi-Author, multi-Subject and batch confirmation

## Scope and canonical authority

The three teacher-menu mutation paths now call `begin_artifact_write_context` before any Artifact/roster selection or confirmation. Each operation binds the same Core workspace as its canonical Standards Library, and `revalidate_artifact_write_context` checks the selected revision and active workspace again **after** the teacher's confirmation. The final atomic service receives only `artifact_write_kwargs(write_context)`. Native services retain roster validation, semantic relationship validation, duplicate prevention and snapshot CAS.

The multi-add paths select students from `write_preview.root`, not a second ambient workspace. Artifact selection passes the pinned preview and its conditional Standards authority. The batch-confirm path checks the exact previously reviewed class, Activity, snapshot revision and SHA-256; no proposal is silently re-selected after a stale review. A cancellation and an empty confirmation selection do not write anything.

## Synthetic proof and limits

`tests/test_issue142_slice3_batch_attribution.py` creates disposable Core classes and a genuine prepared Concord Artifact with a **return-not-expected** page. It never fabricates returned paper, student performance, or a Score. Positive cases validate homogeneous two-student Author/Subject commits, four Activity orientations, and a partial status-only confirmation. Negative cases validate cancellation, duplicates, invalid roster membership, stale reviews, changed active workspace, and no-write boundaries.

The #140 Slice 3C **executable test** is updated to supply the snapshot identity of its synthetic attribution review and assert the repaired missing-relationship result for all seven attribution operations. The frozen #140 audit and other historical test modules are not touched; this is retrospective test maintenance, not rewriting #140's recorded evidence.

## Work remaining

This is a guarded source-only package; repo-specific pytest, Ruff, mypy and full-regression checks must run on the teacher's Windows checkout. This does **not** close the Review, Moderation, routine Score, installed-wheel, or all historical operation-identity audit work remaining in #142. Do not commit/push until reviewed.
