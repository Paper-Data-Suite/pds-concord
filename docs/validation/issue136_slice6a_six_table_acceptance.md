# Issue #136 — Slice 6A: six-table classroom acceptance

This slice adds synthetic Core-integrated regression coverage, not new production behavior.

## Real workflow boundary

For both `mixed` and `standards_based` Activity orientations, the test creates a synthetic Core class (29 students), two independent Activities, and an exact synthetic Standards Library. It authors six labeled Groups in an editable source GroupPlan; saves a teacher-owned class grouping; previews and materializes that arrangement as a distinct target Activity GroupPlan; and exercises draft → previewed → approved → applied using Concord's production workflow services.

The test requires six canonical Groups and 29 distinct Core-backed Memberships only **after** explicit approval and application. Read-only previews must never write. A forged reuse or application digest must not write; a second application must be rejected. The source Activity, saved revision and target academic evidence remain unchanged by grouping reuse.

Core Standards Library context is passed through each standards-backed write and application boundary, without disabling strict graph validation or creating a second grouping engine.

## Out-of-scope follow-up

This slice intentionally does not record Scores, generate packets or publish academic results. The subsequent acceptance slice will exercise individual versus Group Scores, publications, neutral manifest readers, and the producer/consumer contract. Installed-wheel and actual Windows teacher acceptance remain separate release gates.

Use the standard focused gating policy: one test run, lint, typing and package checks, then commit and push on the exact clean branch. No real student names, IDs, or roster snapshots enter logs or documentation.
