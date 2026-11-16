# Concord #148 — Slice 3B1: GroupPlan review adoption

**Starting branch HEAD:** `1fb4ea5b98c3edf03e2bbf54f35553a23610d171`
**Scope:** Concord-owned menu integration only; released `pds-core==0.6.6`.

## Included action boundaries

This slice adopts 14 previously unreviewed `require_actor()` handoffs, all with
existing substantive confirmations. In `menu_group_plan.py`: random GroupPlan
creation, CSV arrangement import, planned-group add/edit/remove, individual
placement/unassignment, roster refresh, CSV replacement, preview, approval,
and cancellation. In `menu_group_plan_signal.py`: reviewed signal-derived
GroupPlan creation. In `menu_group_plan_application.py`: atomic application of
an approved GroupPlan to canonical Groups/Memberships.

Each adopted path obtains its `WorkflowActor` from
`confirm_actor_write(..., state=state, legacy_confirm=confirm_write)` at the
*original substantive review*, returns on cancellation, and hands the exact
reviewed value to the existing request model. For provider-backed sessions the
teacher sees the persisted default (with a deliberate one-action Advanced
alternative); for legacy explicit sessions the old `confirm_write` callback
and `require_actor` behavior are preserved. No extra confirmation is added.

## Preserved safeguards

- No change to academic proposals, immutable history, roster validation,
  signal digest checks, CAS snapshot requirements, application digest, or Core.
- No implicit teacher login, cross-module identity binding, or actor
  authorization inference. The local profile remains only a Concord setting.
- A temporary actor never writes the saved profile and cannot leak to another
  action. Cancellation dispatches no workflow mutation.
- Direct CLI continues to require its explicit actor arguments.

## Not covered here

The cluster-bulk proposal path chooses its actor during preparation, before
its separate final review. Missing-signal disposition has three distinct
branching reviews and one shared service request. Both require separate
review ordering and no-write tests. Artifact evidence/review, Score,
Criterion Set, Preset, Group, Packet, and Publication routes also remain
outstanding and must not be represented as covered by this slice.

## Gates

Pinned branch/HEAD/blob preflight; exact source archive manifest; AST-guaranteed
14-function changes; no unplanned files; Ruff, strict mypy, installed Core
verification and focused GroupPlan/attribution regressions. New tests enumerate
every adopted request actor, assert cancel gates and explicitly check
approval/cancellation service actor forwarding with synthetic data.
