# Concord #142 — Slice 2A read-selection correction

## Evidence

The first Windows Slice 2 gate completed application but failed 18/43 tests. All
observed failures came from missing Core Standards context while selecting a
planned Artifact or current Author/Subject: the test mock called a strict
read service without `standards_library`. The production menu selectors also
used the same strict read services without passing their pinned context.

## Narrow repair

- Add optional, explicit `standards_library` to `list_teacher_artifact_choices`,
  `list_artifact_authors` and `list_artifact_subjects`; pass it unchanged to
  their existing `load_graph` validation. Existing callers retain the same
  signatures/default behavior.
- In the six Slice 2 attribution menu handlers, pass their existing
  `write_preview` into the selected Artifact/Author/Subject helper, then forward
  `root`, `standards_library`, and the expected snapshot to the reads. No
  permission bypass, implicit global cache, or fallback to neutral validation.
- Fix synthetic fixture selectors to provide their canonical Core library,
  plus direct positive tests of the real production Artifact and association
  selectors in a disposable workspace.

## Limits and next gates

This tests read selection and service writes with fabricated planned work;
no returned work, scoring, or live classroom acceptance is asserted. Other
Artifact menu reader families remain for subsequent #142 slices. #140 frozen
inventory is unchanged. Run focused pytest, Ruff, and full mypy; do not stage,
commit, or push until these gates pass and the prior #140 failing-expectation
tests have been reconciled explicitly.
