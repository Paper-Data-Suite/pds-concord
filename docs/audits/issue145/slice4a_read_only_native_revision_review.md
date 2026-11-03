# Concord #145 Slice 4A — Native revision review (source-only)

Checkpoint: `145-teacher-first-criterion-sets-and-saved-assessment-setup` at `217162b7ee7dbf7555030782cc080fe54032966a`; tree `2133bcbe615fc5c29451a4d01b65f730dd9cddd5`.

## Scope

- New pure `concord.criterion_revision_guidance` adapter projects *one exact existing native* Criterion Set revision and its **ordered** native Criterion fields into an immutable in-memory `CriterionSetDraft` for later guided revision.
- It checks consistent Activity selection and exact native snapshot revision; no selection is inferred from browser sort order. It distinguishes current lineage heads from historical revisions and current Activity selection from preset saves.
- It preserves original Criterion IDs, lineage, revision, existing Criterion key/definition/kind/status, supported target kinds, governing/alignment Standard IDs and native default Scale identities in the read-only projection. No new IDs are issued and no writes occur in this slice.
- `_browse_criterion_sets` now displays a full read-only review with Core-provided Standard names when available, explicit historical lifecycle and exact native Scale references. If an old Standard definition is inactive or missing, browsing remains read-only and reports the limitation. It does **not** silently revalidate, upgrade, or remap historical content.
- Empty state suggests guided Create and Use. Stale/mismatched reads refuse with a reload message.
- Existing native creation, direct CLI, Advanced revise/select, Score and reusable-preset workflows are unchanged.

## Core/Suite noncollision

- Core #235, #241–#244: no new Standards, roster, Notes, shared navigation, or private workspace authority; labels come from canonical `pds_core.standards.StandardsLibrary` if present.
- Suite #49 and #51: no launch or composition metadata, no Suite-owned menu/global namespace, no release or dependency changes.
- Concord #143 and #144 remain the owners of native-to-preset bridge correctness and guided Scale choice respectively; this slice only *reads* their native references.
- This is *not* a released Core teacher-experience contract adoption. Core 0.6.6 remains the installed baseline; do not import future unreleased Core services.

## Deferred work

- **4B:** guided editing of the draft, guarded native `revise_criterion_set` immutable successor, no-op and selected/historical preservation, teacher-reviewed explicit use of an existing exact revision.
- **5:** saved assessment continuation including exact saved Scale preset mapping and reviewed save receipts.
- **6 / final:** adversarial two-class, installed-wheel, full repository/CI qualification and independently authorized PR/merge/release.

## Qualification constraints

Guard commit/tree, Core 0.6.6 installed wheel, frozen #140 operation census, exact file inventory, lint/type checks, synthetic zero-write browse tests, retained #145 Slice 1–3 focused regressions. Qualify in detached Git worktree; mirror only after all gates pass. Do not commit, push, run a production installation, or access classroom data in this slice.
