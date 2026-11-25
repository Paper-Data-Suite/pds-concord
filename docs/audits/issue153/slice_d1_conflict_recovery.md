# #153 Slice D1 — truthful storage-conflict recovery

## Qualification carried forward

C2 local behavior at `cdccb468065edf624da9306e1da2071bb7678f02`: 52 passed
in 2.73 s, zero other outcomes; strict Mypy, Ruff lint and reconciliation
passed. Ruff requested two formatting-only corrections in menu_prompts.py
(an excess blank line and the Group display comprehension). D1 includes
both exact corrections. Final formatting acceptance is pending.

## Demonstrated source boundary

ConcordStorageConflictError is raised by storage.py for immutable-file
collisions, existing write locks, initial commits against existing work,
expected/current revision mismatch and absent expected snapshots. The
old prompt called all such cases "Activity Changed". The exception type
does not establish a OneDrive conflict, another running writer, or a
specific stale revision. Do not parse exception strings as authority.

The revised prompt identifies a canonical write conflict and explicitly
makes the cause unverified. Reload remains a read-only inspection, not
a retry, proof of lock clearance, or a confirmation of cloud propagation.
Back performs no reload. A failed reload uses a bounded teacher-safe
diagnosis rather than displaying exception text containing local paths
or student identifiers; navigation exceptions still unwind. Partial
outcomes preserve their existing published-pointer distinction, durable
path count and snapshot identity, and explicitly prohibit automatic
resubmission. No storage or workflow implementation changed.

## Tests and limits

Eleven targeted controller cases cover four real storage conflict message
shapes, Back, failed reload, three navigation unwind exceptions and two
partial-success pointer states. These are injected controller witnesses,
not real concurrent-write or sync experiments. Existing domain conflict,
partial receipt, confirmation, navigation, actor and #152 Score evidence
regressions remain applicable. No blanket redaction of unrelated workflow
exceptions, new retry mechanism, reduced write authorization, or Core
replacement. Technical snapshot-detail disclosure remains E. Review
specific remaining error boundaries and any redundant confirmation
only when evidence justifies a separate D2 repair.

Local static/behavioral qualification pending. B/F remain blocked on
the qualified consolidated Core release (#244).
