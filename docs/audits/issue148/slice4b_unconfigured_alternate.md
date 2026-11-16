# Concord #148 — Slice 4B: unconfigured, explicitly reviewed alternate actor

## Review finding and exact scope

PR #171 review identified a gap in issue #148 Section 3A: while a saved
Concord-local actor default is absent, a teacher should still be able to
attribute **one action** to an explicitly reviewed temporary adult actor.
The previous menu reviewed the saved default before offering Advanced, so
this path could not be reached. This is not authentication or new permission.

## Fix and guardrails

- The normal configured-default path remains unchanged.
- Only a provider-backed interactive **action review** may deliberately
  permit a temporary actor while the profile is *genuinely absent*. No
  actor-attributed commit is available before A/Advanced is chosen.
- Actor-dependent prepared write/digest previews are constructed only after
  the exact temporary actor is selected and are rebound if it changes.
- Missing vs corrupt, inaccessible, unsupported and stale defaults remain
  distinct; invalid states cannot be turned into a silent alternate.
- If a default appears between the initial review and final confirmation,
  the attempt aborts rather than altering the reviewed attribution.
- A selected alternate remains local to one review and is never saved or
  copied into the session's default actor cache.
- Existing direct CLI requires explicit actor arguments and is unchanged.
- Academic workspace, student records, Core config, Meridian and Suite are
  untouched by this slice. Synthetic tests exercise only the local provider.

## Acceptance

Focused regression, Ruff, strict mypy, and the original complete repository
validation must all pass against the authenticated official Core 0.6.6 wheel
before committing or pushing. Hosted Linux/Windows PR CI must pass again on
the updated commit; PR review and squash/merge are subsequent gates.
