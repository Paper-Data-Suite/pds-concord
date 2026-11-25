# #153 Slice C2 — feedback lifecycle and pagination scope

C1 behavioral qualification at `1437572fd6fe790f1113c8efe2cd67301059e6ed`:
40 passed, one expected attention Help failure in 1.97 seconds; strict Mypy,
Ruff lint and outcome reconciliation passed. The only unexpected gate was
Ruff formatting of one Responsibility Assignee Help print statement. C2
includes the exact prescribed formatting repair, without changing that text.

## Local changes

- Attention detail Help and invalid-choice guidance are rendered on the
  next cleared screen before input, preserving the same page and current
  snapshot facts. No extra acknowledgement keystroke is needed. Feedback
  is consumed on redraw and does not follow the teacher to another page.
- When the attention summary is unavailable, the existing read-only
  return prompt stays on its screen, as prelesson readiness already does.
  Help and invalid-choice feedback remain readable. No new mutation,
  navigation parser, shared command or service is introduced.
- Generic multi-selection explicitly says that A selects all items across
  every page; the existing A/D/N/P behavior and the distinct bulk Cluster
  selector remain unchanged.

The final A2b xfail becomes a passing regression, strengthened to check
that the Help text is actually present at the next input boundary. Four
additional cases cover paged feedback, unavailable/readiness feedback
and all-page selection. The existing #149 teacher-view regressions
remain applicable. These are synthetic controller tests, not physical or
installed shared-feature acceptance. Local and CI qualification pending.

A1/A2a frozen manifests retain their original source-line identities;
they are not a current runtime allowlist. Core #244 still gates shared
header and Notes adoption. No Core functionality is recreated.
