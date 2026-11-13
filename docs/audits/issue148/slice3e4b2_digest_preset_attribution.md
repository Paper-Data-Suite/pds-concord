# Concord #148 — Slice 3E4B2: Digest-bound Role/Responsibility attribution

Start: `c5fac80d5046b2255390fa1b4449accf5c6b081c` on the issue branch.

## Scope

The following four teacher-facing canonical write paths now reprepare the
request and the service review digest under each actor selected in the
one-action confirmation UI:

1. Apply a saved Role preset to an Activity assignment.
2. Apply a saved Responsibility preset to an Activity assignment.
3. Save a Role Assignment's reusable definition as a preset.
4. Save a Responsibility Assignment's reusable definition as a preset.

`confirm_prepared_actor_write` receives one callback that constructs the
canonical request, computes the digest with the existing prepare service, and
returns the human review lines. The callback returns an inseparable
`(request, digest)` pair. After the actor review, canonical apply/save services
receive exactly that pair, preserving snapshot revision and Standards context.

The alternate actor lasts only for the current action, and cancellation never
calls the canonical write. No persisted teacher setting or request ABI changes.

## Testing and boundaries

Synthetic regression tests cover source-structure consistency and actual
menu calls with default/alternate/default preview transitions and cancellation.
The 3E4B1 direct-assignment regression now expects both branches of `_assign`
to be reviewed; direct-assignment behavior is otherwise untouched.

This is not a claim of full #148 acceptance. Saved grouping, other menu writes,
remaining 3E1 census dispositions, full test-suite and installed-wheel gates
remain to be completed separately.
