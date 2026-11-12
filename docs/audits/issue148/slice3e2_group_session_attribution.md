# Concord #148 — Slice 3E2: Group, Membership, and Session review adoption

**Purpose:** Close seven actor-bearing, legacy-confirmation workflow boundaries identified by the source-pinned 3E1 census. The original 3E1 census remains a historical record of commit `6b2f17f`; this slice updates the *living regression expectations*, not that historical record.

## Production scope

- `concord/menu_group.py`: `_create_group`, `_edit_group`, `_add_member`, `_end_member`, `_reassign_member`.
- `concord/menu_session.py`: `_add`, `_edit_field`.
- All seven display the canonical action's substantive confirmation with optional Advanced one-action actor choice through `confirm_actor_write`. A canceled review produces no write.
- Request constructors forward the returned reviewed `WorkflowActor` (including display-label snapshot) without introducing credential/permission claims, altering Core ownership, or changing academic-record schemas.
- Editing Group/Session formerly stored `state.require_actor()` inside `values` before confirmation. The actor is now inserted into that dictionary **after** review, before the canonical request construction. No selected field, snapshot, status transition, membership, or Standards context is changed.
- Group Membership reassign/end continue to use the existing strict domain-side snapshot/status contracts; all existing status and end-of-assignment review lines remain intact.

## Tests and acceptance

- Seven AST tests require exact matching actor review + existing request, proper cancel branch, and no unreviewed cached-actor reads.
- Synthetic runtime tests verify exact actor forwarding, preservation of the saved default and no write after cancellation for Group creation, Session creation and Session field edit.
- Existing `test_issue148_slice3e1_actor_census.py` is updated to expect Group and Session creation to be `action-reviewed`; Template and Packet creation remain `legacy-confirm-with-actor` and intentionally unresolved.
- Runner authenticates pinned Git objects, projects both module rewrites plus census test update, qualifies Ruff and strict mypy before modification, checks installed Core and focused pytest after application, and pushes only on success.

## Boundary and follow-on

This slice does not claim the full issue is accepted. The 3E1 census had **40** legacy-confirmation-with-actor candidates. Promoting seven of them would leave **33** in that classification, pending source-controlled rerun and semantic disposition. Other unresolved actor-resolution functions and different-contract Core confirmations are triaged separately.

Next: review and convert confirmed Template/Packet/Role/Responsibility and saved-grouping callsites in bounded slices; then complete issue-wide full-suite, installed wheel, platform CI, navigation, and cross-repository qualification. No Core, Suite, or Meridian code or settings are changed.
