# Concord #148 — Slice 3E1 source census method and disposition rules

**Scope:** Every top-level function in every `concord/menu*.py` module at the pinned
branch HEAD; read-only AST inspection. The generated sibling
`slice3e1_actor_census.md` is the current, complete mechanical inventory.

## What the census establishes

- It records local calls to `require_actor`, `actor_for_action`,
  `confirm_actor_write`, `confirm_prepared_actor_write`, and `confirm_write`,
  plus the number of `actor=` request keywords per function.
- It preserves file/line/function identity for reproducible manual triage.
- It distinguishes a function with an action-scoped actor review from one with
  the older confirmation and a separately resolved cached actor.
- It flags actor resolution in helpers without local confirmation, instead of
  automatically concluding every such helper performs an unsafe durable write.
- It separately flags legacy confirmations without a local actor: some Core
  academic-registration/withdrawal/catalog APIs have no `WorkflowActor` field.

## Triage rule and issue gate

1. Trace each remaining actor-resolution call to the **canonical mutating
   service** and any associated preparatory review, identity snapshot, digest,
   or approval boundary.
2. If an actor-attributed write can be committed after an unrelated confirm,
   add `confirm_actor_write` or actor-specific preparation safely; forward the
   returned *one-action* actor through exactly one intended write.
3. Keep canonical writes, CAS, ownership, privacy, evidence access, foreign
   author references, and indeterminate durability receipts unchanged.
4. Distinguish read-only and delegated helpers from direct attributed writes.
5. Qualify new menu coverage in bounded slices before final full-suite,
   installed-wheel and PR CI acceptance; **do not close #148 on this census**.

**Non-goals:** This inventory is not dynamic trace coverage, authorization,
authentication, private Core Notes ownership, a release, or proof of a
foreground Suite launch. It does not inspect actual user config or academic
workspaces and does not adopt a Meridian or Suite private profile.
