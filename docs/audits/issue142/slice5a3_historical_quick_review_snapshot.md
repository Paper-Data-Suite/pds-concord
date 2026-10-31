# Concord #142 — Slice 5A3: historical Quick Review snapshot fixture

## Source of failure

After the Slice 5A2 workspace patch was installed, all nine current Quick Review tests had previously passed; the two targeted historical #140 cases still raised `AttributeError` at the new selected-Artifact revision guard. The historical unreturned-work probe constructs `SimpleNamespace(artifact_instance_id=PLANNED_ARTIFACT)` without the selected Artifact's `snapshot_revision`.

## Narrow repair

In `test_planned_unreturned_artifact_blocks_quick_review_and_routine_score` only, supply `snapshot_revision=latest.snapshot_revision` on the fabricated selected-Artifact summary. This is the current synthetic Activity snapshot after page preparation. Retain the existing actual eligibility refusal, no confirmation, no Review/Score write, and unchanged-workspace assertions. The Slice 5A2 synthetic Standards-library persistence and workspace pin remain in force.

## Safety and acceptance

Patch exactly one historical executable test module and add this #142 note. Do not change production code, the frozen #140 audit, other tests or classroom workspace data. The runner checks exact branch/HEAD/origin, no staged changes, exact predecessor worktree, canonical replay of the historical test from HEAD through Slices 4B, 4C and 5A2, and the Quick Review production/test predecessor before applying. Rerun the targeted two cases, all nine new tests, the 127-case historical regression suite, Ruff, git diff --check and project-wide mypy. Acceptance is pending the user checkout results. No staging, commit or push.
