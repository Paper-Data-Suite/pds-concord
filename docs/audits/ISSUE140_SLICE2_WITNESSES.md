# Concord #140 — Slice 2 failing-before witnesses

The two tests execute real teacher-menu handlers with real Concord/Core workflow
services and only a disposable, fabricated Core workspace. In-memory stubs are
used to route menu service calls into the exact disposable root and capture
errors that the menu normally shows to the teacher. They do **not** replace the
underlying workflow implementation.

- **C1 / #141:** mixed Activity `draft → configured` through
  `menu_activity._update_activity_field`; confirms the exact missing-Standards
  error, `standards_library=None`, no changed graph/snapshot. Two neutral-mode
  controls and a cancellation case are included.
- **C2 / #143:** native mixed Criterion Set containing the valid Core Standards
  identity `SL.PE.11-12.1`, distinct individual and local Group targets, and
  ordinal four-level numeric Scale; invokes
  `menu_scoring._save_criterion_set_as_preset` and its real preparation service.
  Records the precise legacy identifier rejection with no Score or preset write.
- **Fixture:** 29 invented Period 2 student identifiers and 30 disjoint Period 4
  identifiers; six stable Cluster membership arrays in each class. No real
  returned evidence, publication or student Scores are invented.

The tests are **expected-bug witnesses**, not fixed-function tests. They pass
only while the baseline failure occurs with the exact error. When #141/#143
fix each bug, update the corresponding test to assert successful teacher-menu
behavior and verify an exact write, then retire the expected-error assertion.

No production code or frozen Slice 0/1 baseline artifacts are modified.
Published v0.3.4 wheel replay is not performed by these repository-context tests;
that remains an explicit outstanding qualification gate for #140.
