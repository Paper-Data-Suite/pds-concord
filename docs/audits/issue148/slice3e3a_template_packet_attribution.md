# Concord #148 — Slice 3E3A: actor-exact Template and Packet lifecycle review

Starting commit: `d28ef3798d4cd33ffdc4aa00113840b9164ea003`.

## Scope

Replaces the cached actor in **twelve** prepared, immutable, reusable-library lifecycle actions:

| Library | Actions |
|---|---|
| Template | Create; create successor version; activate version; update definition; retire version; retire definition |
| Packet | Create; create successor version; activate version; update definition; retire version; retire definition |

Each action now obtains a `PreparedTemplate*` / `PreparedPacket*` through a typed `_prepare_for_actor` callback provided to `confirm_prepared_actor_write`. The callback rebuilds both the exact canonical prepared payload and its accompanying preview using the actor selected for **this** action. When a teacher chooses Advanced attribution or restores the saved default, the candidate is re-prepared under that identity, and only the reviewed result is handed to `commit_*`. Canceling returns without a write. Existing immutable lineage, source validation, expected snapshot revisions, and service CAS protections remain authoritative.

The source-census regression for Template/Packet creation is updated from legacy-confirm to action-reviewed, while the original historic Slice 3E1 census report is retained unchanged.

## Deliberate exclusions

`_install_starter` and `_install_all_starters` in `menu_template.py` perform initial no-op/upgrade classification and need a separate actor-exact, no-write-preserving treatment. No changes to Core, Suite, Meridian, direct CLI, identity schemas, existing template/packet storage or academic records. An alternate adult is **the actor recording the library mutation**, not a replacement for an Artifact Author or Core workspace owner. It does not persist.

## Qualification

Guarded runner verifies the exact HEAD, branch, ten pinned Git blobs, clean working tree, and SHA-256 authenticated source members. The transformed Template/Packet files and census regression are linted/formatted in a disposable projection; strict mypy uses shadow files **before** applying the patch. After application: compileall, Ruff, mypy, authenticated installed Core wheel, pytest collection, focused legacy and new source/runtime regressions, Git diff scope and whitespace. Commit/push only if all gates pass and remote HEAD remains pinned.

Human classroom behavior and full installed-wheel end-to-end restart qualification remain for the final acceptance slice; this synthetic slice does not claim those tests.
