# Issue #148 — Slice 3E4B1: direct Role and Responsibility assignment

**Bounded change:** `concord/menu_role.py::_assign` and `concord/menu_responsibility.py::_assign`, **manual/direct assignment branch only**.

## Scope and review contract

- The manual Role and Responsibility assignment branches replace a legacy `confirm_write` with `confirm_actor_write` and immediately forward the exact reviewed `WorkflowActor` into `AssignRoleRequest` or `AssignResponsibilityRequest`.
- A cancellation returns before the canonical assignment service is called. A temporary alternate actor is scoped to that single assignment; the process default is never changed.
- The selected student/assignee, Group, Session context, request identity, snapshot CAS, and Standards forwarding remain untouched. No Grades, scores, ownership, or authentication authority are inferred.
- **Not yet converted:** the saved-preset assignment branch still uses `state.require_actor()` and a digest-backed `prepare_*_preset_application` plus legacy confirmation. It must be handled in **3E4B2** together with Role/Responsibility preset-save paths. This audit makes no claim that both branches are fully reviewed.
- Actor-review discovery in 3E1 is a function-level static classification, so one reviewed branch can make the function appear fully reviewed. A future exit gate must examine branches, not merely the `action-reviewed` function count.

## Qualification

Preconditions: branch `148-persistent-reviewable-teacher-attribution`, HEAD `4bff0e1e278af4d94a35c47bb751e19201dc2325`, ten pinned Git blobs, clean working tree, authenticated source archive. Before applying, Ruff + strict mypy check temporary source projections. Focused tests prove actor forwarded to the exact canonical request, cancellation no-write, default unchanged, and explicit residual legacy saved-preset branch. Installed Core verification and focused regressions execute on Windows before any commit/push.

This is synthetic attribution testing only; it is not a human classroom trial, OS-user authentication, or a Core/Suite/Meridian identity contract.
