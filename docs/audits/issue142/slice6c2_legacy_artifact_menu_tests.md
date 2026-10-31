# Concord #142 — Slice 6C2: legacy Artifact menu unit-test adaptation

Test-only reconciliation of the **seven** expected #28/#29 failures after
introducing #142 Core activity/workspace authority checks. The old unit tests
inspect request construction, menu navigation, or teacher confirmation, but
use synthetic `ActivitySummary` objects without a persisted Core Class/Activity.

- Restrict authority-boundary stubs to the six named test functions (one is
  parametrized, yielding seven cases). All other tests retain actual behavior.
- No mock changes are applied to the production modules or #142 integration tests.
- Existing legacy fake service sinks accept additional explicit context keywords.
- Preserve original navigation, request semantics, and expectations; if further
  contract differences appear, they must be separately evaluated.
- Historical #140 inventory and #162 reviewer-attributed audit remain unchanged.

**Status:** candidate only; Windows regression qualification required.
