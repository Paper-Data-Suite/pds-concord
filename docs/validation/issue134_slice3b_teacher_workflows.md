# Concord #134 Slice 3B: everyday identity and history surfaces

Source baseline: `80ba15a5c3e1992a10bc4132e8424fa7179a1b44`.

## Teacher-facing improvements

- Shared prompt selection now uses current Group, Session and roster names without technical IDs. Duplicate names are numbered for display only; exact typed selections are unchanged.
- Group and Membership lists use classroom-facing names and report statuses instead of UUIDs, membership IDs, and snapshot revisions. Missing participant labels are explicitly unavailable rather than substituted with IDs.
- Session lists and save results use meaningful numbers, names, and status. Advanced creation still asks for a durable Session ID.
- Preset lists and pickers use name, revision and status; duplicate labels do not silently select the wrong preset.
- Artifact Page lists show logical page number and state; equal page numbers are disambiguated without claiming chronology.
- Review and Moderation histories show canonical dates, outcomes, states and permitted use without leaking evidence identifiers. Do not infer an exact historical reviewed scan if no immutable binding is recorded.
- Score lists use recorded time, target type, value and the canonical current/historical designation. The exact scored scan version is explicitly unrecorded where the Score model cannot prove it.

All canonical record identifiers, links, version selection, and mutation requests remain unchanged. No producer, Core requirement, storage schema or mutable evidence state changes.

## Deferred work

Slice 3C completes additional attribution associations, advanced criteria/scales, scan inbox routing chronology and downstream teacher result paths. The #134 audit remains the authoritative checklist; these changes do **not** claim the complete 30-file teacher-interface audit is closed.

## Qualification

Run `run_slice3b.ps1` once from a clean expected source. Focused menu/prompt/score/review regressions, Ruff, MyPy, and strict Git scope validation must all pass before the scripted commit/push.
