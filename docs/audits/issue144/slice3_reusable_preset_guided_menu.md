# Concord #144 — Slice 3: guided reusable Scoring Scale presets

## Frozen context

- Owner: `Paper-Data-Suite/pds-concord`, issue #144, branch `144-guided-type-safe-scale-creation-and-editing`.
- Git base: `e47c88654b239ccc4ee7d305e95ce822d67a9d0f` (post-#143 squash merge).
- Qualified cumulative Slice 2 tree: `e74030a997b897b5eb42279c456c30ca88a35905`.
- Preset menu source blob before Slice 3: `c422d00c895cc2612d11656b58eaacf791b41149`.
- Core official compatibility artifact: `pds_core-0.6.6-py3-none-any.whl`; no unpublished shared-Core feature assumption.
- Frozen #140 operation matrix unchanged; independent #162 audit remains unapproved.

## Scope

The previous reusable Scoring Scale menu used `Exact JSON value` for create and edit, rebuilding all levels even during an immutable revision. Slice 3 replaces the **reachable** preset create and edit paths with the shared Concord-only `guide_scale_levels` + `GuidedScaleDraft` facilities qualified in Slices 1–2. Preset create/revise continue to call only the existing `create_scoring_scale_preset` and `revise_scoring_scale_preset` services. The dormant `_json_scalar` helper is retained for backward-compatible internal references; neither active preset route uses it.

A teacher may choose four-level proficiency, a typed custom Scale, or a Yes–No Scale. The editor offers typed preview, selected-level changes and safe cancellation. The final preset confirmation shows exact integer/float/text/bool values, all labels/meanings/optional descriptions/order, preset ID and revision ID, existing metadata, and a clear warning: this creates **no** Score, Grade, native Activity Scale, evidence, or publication.

On revision, the current saved revision is loaded by ID, passed unmodified to `draft_from_existing`, and shown before draft editing. Optional intended-use and aggregation fields are **kept, changed, or cleared explicitly** rather than silently reset. A strictly type-aware comparison prevents a no-op edit from writing a new immutable revision; it distinguishes `1`, `1.0` and `true` despite Python numeric equality. A changed draft requires a new revision ID and literal `REVISE` approval, then passes `expected_revision=current.revision` to the existing optimistic concurrency service. A stale conflict does not claim success; the existing preset-menu error handling remains responsible for showing failure.

The generic `_edit` dispatcher no longer emits `Preset Updated` unconditionally for Scoring Scales. The Scale path has its own receipt **only after** the revision service succeeds. Other saved preset kinds are unchanged.

## Noncollision and negative boundaries

- No Core, Suite, or Meridian files, schema, grading policies, launcher, or trust logic are modified.
- No change to Advanced CLI `--definition` JSON input, exact `JsonScalar` values, storage codecs, preset IDs, native Scale models, or historic saved revisions.
- No Criterion Set wizard (#145), class copy (#150), Score-entry redesign (#152), global navigation overhaul (#153), or human audit closure (#162).
- No automatic materialization of the saved preset into an Activity; that requires a separate reviewed operation.
- No broad teacher-interface rewrite; only `concord/menu_presets.py`, plus the focused Slice 3 test/audit files.
- `B`/cancel, a declined `CREATE`/`REVISE`, a no-op, or a stale service refusal causes no new saved revision.
- Frozen #140 operation references: `concord/menu_presets.py::_create_scale::create_scoring_scale_preset::1` and `concord/menu_presets.py::_edit_scale::revise_scoring_scale_preset::1` are locators, not #162 certification.

## Required qualification

Check the source manifest; exact branch, HEAD, tree, origin and remote refs; frozen #140 bytes; official Core wheel; qualified Slices 1 and 2 archives and cumulative tree. Apply Slice 3 to a detached candidate only. Ruff, strict mypy, focused pytest (including existing native Scale, reusable preset, direct CLI and #143 regressions), and final candidate immutability checks must pass before any file is mirrored.

No commit, push, PR, merge, release, Suite composition, or classroom-data access is authorized by this slice.
