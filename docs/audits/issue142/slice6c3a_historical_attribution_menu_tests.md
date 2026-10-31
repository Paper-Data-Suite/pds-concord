# Concord #142 — Slice 6C3A: historical #106 attribution-menu unit tests

Test-only reconciliation of seven formerly failing #106 tests that construct
unpersisted `ActivitySummary` and relationship review spies. The #142 menu
write boundary now pins a real Core class, Activity revision, source snapshot
digest, and workspace, so those historical request-spy tests cannot use the
machine's ambient workspace as a legitimate authority fixture.

- Only the **seven named** unit tests patch the `begin_artifact_write_context`
  and `revalidate_artifact_write_context` boundaries; the other #106 tests
  remain unpatched and real #142 positive/negative synthetic integration tests
  continue to exercise the production authority and CAS gates.
- The historical `_review()` projection carries explicit class, Activity,
  revision and deterministic fake digest, so its exact selection is checked
  rather than incidentally failing to find the current Core class.
- Selected Activity revision is aligned with the historical Artifact revisions
  (17/23) for the three multi-add request spies, preserving snapshot freshness.
- Mock batch writers accept the explicit canonical service kwargs. The
  existing request and cancellation assertions remain intact.
- Production modules, frozen #140 inventory and historical archive bytes are
  unmodified. No school workspace is consulted.

**Status:** candidate; Windows focused/regression/static qualification pending.
