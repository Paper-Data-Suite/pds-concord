# Concord #148 — Slice 3E6B: guided Activity and Template Packet attribution

Starting branch: `148-persistent-reviewable-teacher-attribution`
Starting commit: `b016f4edf55a8fd82b9d9b7b5f77d03eeab66045`

## Scope and contracts

- `concord/menu_guided_activity.py::_create_fresh` now forwards the exact actor selected at the single existing `CREATE` review to `CreateActivityContextRequest`. The generated Activity/Session IDs and classroom-facing prompts remain unchanged.
- `_create_from_activity` now forwards the action-reviewed actor to `CopyActivityRequest`, retaining the existing, source-derived copy review digest and the independent target Activity. The copy preview is actor-independent; neither source records nor historical provenance is modified.
- `_start_packet_from_template` now prepares one complete `PreparedPacketFromTemplate` for each displayed actor. Its prepared Packet definition/version carry that actor's native provenance. The final `SAVE` accepts only the exact prepared object returned from the actor-bound confirmation. Stable IDs, template/version/audience choice, separate material-generation review, and navigation remain intact.
- No profile persistence, Core/Suite/Meridian ownership, direct CLI default, Workspace/Notes access, Score/Grade inference, or canonical record model is changed.

## Synthetic qualification

A focused test checks two guided Activity mutations, one prepared Template Packet save, cancel/no-write behavior, optional alternate/default actor switching, preservation of the saved session actor, exact request/digest or prepared-object forwarding, and all three callsite shapes.

## Deliberately outstanding #148 census dispositions

The source-pinned 3E6A gap ledger remains open. Subsequent bounded slices must inspect `menu_packet_generation.py` (generation/render writes), `menu_group_plan_bulk.py` (delegated bulk edit), publication/scan/CSV operations whose canonical services may not accept `WorkflowActor`, and purely read-only/acknowledgment helpers separately. No static candidate is assumed safe solely because the function has a review call. This slice is **not** full issue acceptance.

## Gate

Require exact pinned HEAD and blob identities; clean index/worktree; authenticated source manifest; temporary-projection Ruff and strict mypy; installed Core verification; focused tests; scoped diff and remote-head guards before commit/push. Full repository, installed-wheel relaunch and supported CI remain final #148 gates.
