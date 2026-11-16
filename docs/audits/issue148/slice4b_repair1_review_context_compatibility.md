# Concord #148 — Slice 4B Repair 1: structural actor-review compatibility

## Native failed-before evidence

Slice 4B full Windows validation stopped at 32 failures, 3,510 passed and 19 skipped. Every failed test was an actor-review scenario in four pre-existing #148 groups (3C3B digest, 3D3A publication, 3E3A Template/Packet, 3E3B starter install). The displayed common traceback showed `AttributeError: '_ActorContext' object has no attribute 'actor'` from `confirm_actor_write`, with analogous provider-shaped synthetic review states used elsewhere. The runner stopped before commit or push.

## Exact repair

Keep the genuinely absent saved-profile exception **only** for a real `MenuSessionContext` with its guarded provider and fingerprint. The review helper continues to accept existing provider-shaped actor-review contexts by calling their established `actor_for_action(action_label=..., alternate=...)` signature, without assuming they expose `actor`, `actor_fingerprint`, or an `allow_unconfigured_default` keyword. An explicit temporary actor is never persisted and must be selected for the current action; corruption, stale defaults, profile creation during review, cancellation and actor/review digest binding remain guarded.

Changes: one production helper, one synthetic compatibility regression test, and this audit. No change to `concord/menu_context.py`, profile storage, canonical workflow services, direct CLI, Core, Suite or Meridian.

## Native qualification gate

Pin Git HEAD `ae51af6ff061be58ebcd78df04749c24419a3e30`, previous 4B source SHA-256, exact source residue after the stopped 4B run, and remote branch. Run the four formerly failing suites and the 4B unconfigured-default tests **before** one full repository validation. Run Ruff check/format, strict mypy, and all existing full validator phases including new installed-wheel smoke, only then guarded commit/push. Do not reuse the prior failed full-suite outcome as a pass. Hosted PR CI must rerun on a new commit; prior green checks do not qualify altered production source.
