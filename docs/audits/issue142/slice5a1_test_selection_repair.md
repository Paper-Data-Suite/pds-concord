# Concord #142 — Slice 5A1: synthetic Artifact selection fixture

## Observed failure

After guarded Slice 5A applied, all nine newly added tests failed in `_selected()` before exercising Quick Review: the fixture invoked the real `_choose_artifact` without passing its operation context. The selection reader therefore used the default workspace rather than `tmp_path` and raised `ConcordWorkflowNotFoundError`. No Quick Review or Score was committed by these failing tests.

## Resolution

Use `begin_artifact_write_context(current, operation="Synthetic Quick Review selection")` to pin the synthetic Core workspace and its conditional canonical Standards library before calling `_choose_artifact(..., write_context=write_preview)`. This matches the existing production selection contract. Test and documentation only; no production service or menu code modified.

## Boundaries and follow-up

- The fixture uses disposable fabricated Core classes and an unreturned Artifact.
- The synthetic eligible-context spy in the test does **not** claim real returned/assembled evidence acceptance.
- Verify all 9 Slice 5A tests, the accepted 127-test regression suite, Ruff, whitespace, and mypy on Windows.
- Do not stage, commit, or push until separately authorized.
