# Concord #148 — Slice 3C2: bounded native Scoring and Criterion actor review

Starting branch commit: `85afee71f6f6f0c0e40998cee1613464a636e3d1`.
Only `concord/menu_scoring.py` is altered in production; Core and CLI contracts are unchanged.

## Adopted confirmation/write pairs

- Create native Scoring Scale (`CreateScoringScaleRequest`).
- Revise native Scoring Scale (`ReviseScoringScaleRequest`).
- Use a saved Scoring Scale in this Activity (`CreateScoringScaleRequest`).
- Create native Criterion Set (`CreateCriterionSetRequest`).
- Revise advanced native Criterion Set (`ReviseCriterionSetRequest`).
- Select native Criterion Sets in advanced menu (`SelectActivityCriterionSetsRequest`).
- Record a Score (`AddScoreRequest`).
- Revise an existing Score immutably (`ReplaceScoreRequest`).

Each route retains its existing substantive confirmation verb and passes the reviewed actor directly to the guarded workflow request. The alternate is operation-local, not saved, queued, or treated as authentication; cancellation prevents dispatch. The legacy explicit-session `confirm_write` callback remains effective, and standalone CLI `--actor-id` is unchanged.

## Deferred boundaries (must not be presented as completed)

- Guided rubric Create & Use and guided native revisions: these validate provenance and sometimes write twice, so actor selection must be coordinated with provenance and multiple guarded writes.
- Using existing rubrics and saved scoring setup: may have no-op path, native selection verification, and review-digest contracts.
- Save native Scales/Criteria as reusable presets: actor is part of the preparation/review contract; selecting an actor after prepare would require a new digest and visible re-review.
- Other Score/Artifact write paths, publication and role responsibilities remain for later qualification.

Tests include AST checks for all eight source routes plus synthetic write/cancellation tests for Score recording and advanced Criterion selection. No private/student data is read in these tests. Qualification uses pinned source, installed Core, Ruff, mypy and focused pytest; do not close #148 based on this slice.
