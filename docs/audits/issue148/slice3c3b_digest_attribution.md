# Concord #148 — Slice 3C3B: actor-exact preset digest reviews

## Boundary

Three preset-related operations in `menu_scoring.py` prepare canonical read-only
review material from an actor-bearing request and then commit that request with
the preparation's `review_digest`:

1. `_save_scale_id_as_preset`: native Scale → reusable Scale preset.
2. `_save_criterion_set_as_preset`: native rubric → reusable Criterion Set preset.
3. `_use_saved_scoring_setup`: saved rubric/Scale presets → Activity setup.

A temporary alternate actor cannot safely be chosen **after** a preview is
prepared for the saved default: its actor and digest must be prepared and
reviewed together. A second preparatory pass must not silently inherit a stale
digest, alter preset IDs or rewrite immutable source records.

## Change

`confirm_actor_write` gains a narrowly optional `review_lines` callback;
ordinary callers and direct, noninteractive CLI commands are unchanged.
`confirm_prepared_actor_write` binds the exact actor, prepared request and
substantive preview to one review cycle, rebuilding the canonical preview when
an alternate is selected or the default restored. It returns a prepared value
only on a valid confirmation. A change in the actor between rendering and
confirmation aborts, not writes. No persistent alternate is introduced.

Each of the three menu callers now clones its immutable request via
`dataclasses.replace(request, actor=actor)`, prepares that exact request,
displays its preview, and commits the **same** returned request and digest.
Existing source revision checks, CAS, error/unknown outcome receipts,
no-auto-retry semantics, and all Core/Concord provenance contracts remain.

## Safety qualifications

* Synthetic tests cover default/alternate/restore/review cancellation and a
  deliberately changing actor. They include static request/digest contract
  checks at all three callsites.
* Pinned Git HEAD/blobs, authenticated source archive and clean worktree guard
  installation; Ruff and shadow-file mypy run on projected files before writes.
* No academic record, default attribution preference, Core, Meridian, Suite,
  publication or private Notes schema changes.
* No automated commit or push unless focused qualification completes.

## Residual scope

Artifact, publication, packet and other menu action reviews remain for later
#148 slices. This does not close the issue or claim authentication.
