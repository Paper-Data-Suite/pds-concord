# #153 Slice C1 — bounded iterative navigation repair

## Baseline evidence

A2b qualified on Windows at
`97b7d9038318d8b78298ac307aaa7edb80255014`: 12 passed, 7 strict expected
failures in 1.37 seconds; Ruff format/lint and repository integrity passed.
Six failures specifically witnessed recursive selector re-entry; the seventh
witnessed attention Help disappearing before acknowledgement.

## Scope

Replace self-recursive retry in three Concord-owned local controllers:
Activity Type, optional Role Group, Responsibility Assignee. Retain the
existing screen-clearing, Help acknowledgement, navigation parsing and exact
selection branches. Role Group refreshes the group list on each redraw,
including after invalid input or Help; Responsibility Assignee still reads
the relevant roster/Groups only when the teacher chooses that target kind.
No changes to authority, record models, durable writes or confirmation.

Six formerly strict-xfailed retry witnesses become ordinary passing tests.
Three additional stress witnesses repeat Help and invalid input 25 times;
one checks that the Role Group selector re-reads the group list and returns
without selecting a stale Group when none remain. The unrelated strict
attention Help xfail remains intentionally unresolved for C2.

Local qualification expected: 22 passed, one strict xfailed in the navigation
witness file, plus 18 existing foundation/density/date tests. Static checks
and actual local execution remain pending until the owner qualifies the
candidate. No Core functionality is added or emulated.

Next: C2 attention feedback acknowledgement and pagination scope.
