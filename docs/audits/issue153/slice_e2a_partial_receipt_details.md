# #153 E2a — partial-success receipt disclosure

E1 qualified at `8a2da5344fb216d6a5421484933290ebb5a1644e`: 53 passed
in 31.07 s, including 15 new date cases; strict Mypy and static checks
passed; exact-tree Ruff reconciliation passed unchanged.

The former partial-success receipt always displayed snapshot revision,
hash and recovery-path count. The new ordinary receipt retains the
actual published-pointer outcome, inspection-before-retry guidance and
explicit prohibition of automatic resubmission. T is a Concord-local
read-only receipt choice, not a shared Core command. The separate
Technical Details screen shows reported revision, canonical-looking
SHA-256 or explicit unavailable, and recovery-path count, never paths
or arbitrary exception text. Back/Enter returns from details to the
receipt; Back/Enter acknowledges the receipt; public Core M/Q unwind.
Invalid choices redraw the outcome with feedback. No write or reload
is invoked by disclosure. The existing generic result/pause and
confirmation semantics remain unchanged. No Notes recognition added.

11 new controller cases cover ordinary published/unpublished outcomes,
opt-in metadata and return, M/Q on both screens, invalid input and
missing/malformed metadata. The existing menu density witness now
explicitly selects Technical Details; D1 outcome and recovery tests
remain unchanged. The fixtures are synthetic storage exceptions, not
a new durability experiment. Local qualification pending.

E2 is not closed: next inspect Activity summary/status and ordinary
Packet review/receipt metadata with exact identity/actor and #152
Score authority preserved. Technical details must not conceal
ambiguity or currentness warnings. B/F remain Core-release dependent.
