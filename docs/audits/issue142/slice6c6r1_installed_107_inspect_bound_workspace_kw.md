# Concord #142 — Slice 6C6R1: #107 smoke adapter receives pinned workspace kwarg

## Evidence

The Windows #107 installed-wheel qualification using Concord 0.3.4 wheel SHA-256 `e90f789c0b51768408eedf582437212fb416405b88cc4d4da884b583347ce59c` and authenticated Core 0.6.6 wheel failed after passing all setup and selection gates:

`TypeError: inspect_bound() got an unexpected keyword argument 'workspace_root'`

The prior Slice 6C6 bound the genuine write-context resolver to the disposable synthetic root. The production Quick Review subsequently passes this pinned `workspace_root` into `inspect_artifact_routine_review`. The historical installed-smoke `inspect_bound` did not accept the new keyword, although its underlying real service already receives `workspace_root=root`.

## Bounded repair

Only the historical installed smoke's `inspect_bound` signature is changed to accept the optional `workspace_root` keyword. If provided it must equal the exact disposable fixture root. Its call to the real `inspect_artifact_routine_review(..., workspace_root=root)` is retained. No production code, canonical mutation, standards authority, snapshot checks, or original acceptance assertions are changed.

A complete installed-wheel rerun remains required to establish the behavior. Branch and exact commit remain pinned; original Git index remains unmodified. The detached validation worktree has an independent index.
