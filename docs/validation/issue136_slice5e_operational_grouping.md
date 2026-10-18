# Concord #136 — Slice 5E: save from operational Groups

**Exact predecessor:** `8f02f41f95bd816c807e4852073563f9fb014507` (Slice 5D).
**Branch:** `136-fix-standards-context-and-reusable-group-arrangements`.
**Release target:** v0.3.4 (no version bump in this slice).

## Intent and boundaries

`concord/workflows/class_group_arrangement_operational.py` adds a new **reviewed save source** to the existing immutable class-group-arrangement storage. The source is the current exact Group + Membership state in one Activity and **one explicitly chosen source Session**, not a saved GroupPlan.

Public service calls:

- `prepare_save_operational_grouping(SaveOperationalGroupingRequest(...))` is read-only. It verifies Core class/year and roster, source Activity snapshot, source Session identity, Group/Membership head revision consistency, teacher actor, and exact student placement.
- `save_operational_grouping(request, review_digest=...)` recomputes the review, rejects changed source or forged digest, requires explicit acknowledgement if any current Core student is unresolved, and delegates to existing `create_arrangement` (revision 1). There is no separate storage format or Activity write engine.

## Exact Session selection

- A source Session ID is mandatory, including for single-Session Activities.
- Membership `planned`/`active` is considered current; `completed`, `withdrawn`, `cancelled`, `reassigned`, and `superseded` historical memberships do **not** count.
- Existing `EffectiveContext` semantics are expanded against current Sessions: listed Session IDs, bounded sequence ranges, and applies-to-remaining-Activity. The selected Session must be covered.
- All planned/active Groups are included, ordered deterministically by display label + source Group ID. A group with a narrower context not covering the selected Session is rejected rather than guessed away. Hierarchical and superseded Groups are rejected to prevent silent flattening.
- An active Membership assigned to an inactive/missing Group, a non-Core/unknown student, or a student with two concurrent active Group memberships within the selected Session causes a prewrite conflict.
- Students without an applicable active Membership are **explicitly unresolved**; they are never presumed present from a seating label or from ended/historical assignments. Saving such a preview requires `acknowledge_unresolved=True` at the commit boundary.

## Preserved invariants

- **No source Group IDs or Membership IDs** enter saved arrangement revisions. New `saved-group-XX` keys are generated and are independent of operational identity.
- Only class/year/owner, teacher-facing name, group labels/descriptions, exact Core student IDs, and unresolved IDs are stored.
- Source Activity, Scores, Role/Responsibility, Artifact provenance, Sessions, existing memberships, grouping signals, publications, and evidence are unchanged.
- Storage remains teacher-restricted, immutable, revision-integrity checked and roster-validated. Existing Slice 4 `ReuseGroupingRequest` materializes a fresh editable GroupPlan; it does not automatically apply the plan.

## Focused acceptance

- Real synthetic Core class, six actual Groups/29 actual Memberships → review → save → reload after restart → reuse in another Activity → fresh **draft** plan; no canonical Groups or Scores auto-created in target.
- Read-only preview, digest mismatch, stale Activity snapshot, missing Session, duplicate active Memberships in Session, ended-membership exclusion, explicit unresolved acknowledgement, actor-kind validation, no-Groups diagnostics.
- Actual installed Core/Concord tests, Ruff, strict mypy, pip check and Git integrity once. Full expensive suite reserved for release candidate.

## Next slice

Expose the new operational source under **Save current grouping** in the teacher menu and direct CLI. This slice intentionally does not add a second menu that can bypass the exact Session/review boundary.
