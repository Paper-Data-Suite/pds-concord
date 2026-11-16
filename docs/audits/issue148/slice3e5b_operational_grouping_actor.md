# Concord #148 — 3E5B: operational grouping SAVE actor consistency

Baseline: `9455240ae7cd38d60704f40d46afaf6146a33c13`.

The teacher chooses one Session and names the grouping. The menu first prepares a read-only inspection of actual Group/Membership placements, displays that inspection, and obtains the existing explicit acknowledgment for unassigned students. No canonical write occurs at this stage.

The final `SAVE` uses `confirm_prepared_actor_write` with an actor-scoped callback. It creates a fresh `SaveOperationalGroupingRequest`, prepares that exact request and digest, and forwards the same pair to `save_operational_grouping`. Replaying the actor-review screen may reprepare, but never commits a stale actor/digest pair. A changed source Activity, Session, grouping name, membership projection, or unresolved student set compared to the inspected placement fails closed. Service-side source revalidation remains authoritative.

The original public menu entry, session selection, roster confidentiality, explicit unassigned acknowledgment, canonical provenance, and class-scoped ownership are retained. A temporary actor may become the grouping's owner; it never alters the saved default profile. An acknowledgment is not itself a canonical write and is separate from the final actor-reviewed SAVE.

The legacy test is updated for the intentional second read-only preparation. New synthetic tests verify actor/digest identity, cancellation, acknowledgment refusal, acknowledgment retention and stale-placement abort. Neither student records nor the personal attribution profile are opened by the tests.

Qualification: authenticated source and pinned blobs, clean working tree, temporary Ruff and mypy preflight, installed Core check, focused pytest, Git diff/staging checks, commit/push only after gates pass. Full repository, distribution-wheel and CI qualification remain separate final issue acceptance tasks.
