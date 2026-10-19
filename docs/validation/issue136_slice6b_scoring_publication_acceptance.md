# Issue #136 / Slice 6B — Score separation and publication acceptance

**Predecessor:** `36401440e916ef170af842782c24898dc8cdb16e` (Slice 6A)

## Scope

Synthetic classroom acceptance after an exact 29-student, six-group reuse and
approved GroupPlan application. Parametrize mixed and standards-based Activities.
All participant identities are fabricated. Only additive tests and documentation.

1. A new target GroupPlan starts draft, then becomes previewed, approved and
   applied; six canonical Groups and 29 Memberships exist before recording Scores.
2. Individually authored standard-backed Scores remain attached to their exact
   Core students. A local Group Score, when supported by the mixed orientation,
   remains attached to a Concord Group and never becomes 5-6 student Scores.
3. Creating an explicit Core Academic Work Registration and publishing the
   academic-result manifest does not leak the GroupPlan/saved grouping or the
   private scoring rationale. Neutral manifest readers preserve target identities.
4. Publication replay is idempotent. Both source Activity and saved arrangement
   revision remain unchanged. A later reuse cannot silently overwrite canonical
   Groups in the target Activity.

## Test scope / execution

Run the new test and the focused score/publication and standards regressions, not
the entire suite. The validated workflow requires the installed Core dependency.
Pass Ruff and environment gates before invoking pytest; auto-commit/push only
on a completely successful run, with no unrelated paths staged.

## Out of scope

The release candidate, full CI, installed Core v0.6.6 wheel, final version bump,
and user-workspace smoke tests belong to release qualification. No real data is
accessed by these tests.
