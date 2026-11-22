# Concord #151 — Slice 5B: attribution recovery and readable work identity

**Pinned feature baseline:** `3ee8dcec72fe44c29fc7652490fbc5908fd5a22d`.

## Exact teacher context without opaque identifiers

The routine attribution projection adds an optional `teacher_work_label`, using
existing `build_teacher_artifact_choices` on the **same canonical graph and
snapshot** loaded for attribution. Its `group_label` and `session_label` are
used, not its page-status-derived returned counts. Duplicate display labels
are disambiguated as *work X of Y (display order, not chronological)*. The
exact `artifact_instance_id`, Author ID, and Subject ID remain unchanged in
the projection and are still used for validated writer selections, but they
are not printed in normal review headings or proposal choices.

Group representation is indicated without exposing its internal Group ID.
When a legacy partial test projection has no display label, the menu fails
safe to generic, numbered work labels instead of printing raw identity.
No durable labeling records or extra graph loads are introduced.

## Recovery and menu resumption

Within **Review Attribution**, `R` invokes existing shared Scan Routing while
`T` invokes the read-only, snapshot-scoped Collection Status. The existing `S`
continues selecting attribution proposals. Both recovery actions return to the
review loop, where the current projection is read again. They never
implicitly confirm relationships or record Review, Score, or publication.
`B/M/Q/H` retain their established semantics. The confirmation writer remains
independently gated by Slice 4A; this slice does not relax its requirements.

## Qualification and acceptance boundaries

Run scoped Python syntax, Ruff, Mypy, documentation, new synthetic tests,
and #106/#142/#149/#151 navigation/attribution regressions on the official
Core 0.6.6 environment. No real student data, original scan mutation,
Core/Suite write, new database, or hidden physical return assumption.

This slice is NOT native Windows deep-path returned-PDF or physical scanning
acceptance; those are independently tracked in Slice 6.
