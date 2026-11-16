# Concord #148 — Slice 3E4A: Reviewed Role/Responsibility End and Reassignment

## Scope and authority

The four previously cached-actor menu operations in `concord/menu_role.py` and `concord/menu_responsibility.py` now bind the actor returned by `confirm_actor_write` in the same substantive confirmation screen:

| Operation | Canonical request/service |
| --- | --- |
| End Role | `EndRoleRequest` / `end_role` |
| Reassign Role | `ReassignRoleRequest` / `reassign_role` |
| End Responsibility | `EndResponsibilityRequest` / `end_responsibility` |
| Reassign Responsibility | `ReassignResponsibilityRequest` / `reassign_responsibility` |

The selected actor is an attribution label and ID, not authentication or Core workspace ownership. No academic record model or Core/Medidian/Suite code is changed. The existing service, explicit assignment context, expected Activity snapshot revision, standards-library arguments, original predecessor identity, status selection and error-handling paths are retained. Cancellation returns without a canonical write. Each action is independently reviewed; temporary selection is neither persisted nor inherited.

## Excluded from this bounded slice

`_assign` in Role and Responsibility contains two distinct branches: direct assignment versus digest-backed saved-preset application. `_save_role_as_preset` and `_save_responsibility_as_preset` also prepare and validate their own actor-bound review digests. They remain for Slice 3E4B so their exact request/digest pairing cannot be broken by a mechanical edit. Saved grouping and grouping revision semantics remain for subsequent 3E4 work.

## Qualification

The source-only archive uses an exact starting Git HEAD, pinned source blobs, a clean-tree requirement, and authenticated member checksums. The runner transforms and qualifies the candidate in temporary storage with Ruff import ordering, formatting, full lint and mypy before applying. After applying it validates compileall, Ruff, mypy, installed official Core and focused pytest using only synthetic test data. Auto-commit and push occur only after success and a remote-head CAS check.

New regression tests assert four canonical callsite contracts and eight approved/cancelled execution paths. In particular the actual service receives the exact reviewed actor even when it differs from the session's default; aborted operations do not call services; the session default is not mutated.

## Acceptance disposition

This is a subset of the outstanding legacy actor-callsite inventory. It does not imply full #148 acceptance, release qualification, installed Concord wheel acceptance or permission to merge. The historical Slice 3E1 census remains unchanged and current counts should be regenerated at final acceptance.
