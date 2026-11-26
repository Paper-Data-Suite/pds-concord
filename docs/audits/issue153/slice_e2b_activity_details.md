# #153 E2b — Activity summary and status picker disclosure

E2a qualified at `4078b4395dfa623d15f855a4be845c6e6b96165e`:
29 passed in 1.73 s; exact-tree reconciliation and final Ruff passed.

Move snapshot revisions from the ordinary Activity Summary and native
status picker into explicit T Technical Details. The Activity title
is the primary summary label. ClassSummary exposes only canonical
class ID/school year, and Activity titles need not be unique within
a class: retain the class and Activity IDs as exact identity cues.
No expensive class-wide discovery or fabricated label. Keep status,
type, scoring orientation, counts, description and Focus Standard count.
An unavailable summary suppresses raw workflow exception text.

The existing local select_one gains an opt-in technical_details argument;
only the status picker opts in. The details view displays the already
read metadata and returns to the exact same selection page, with B/Enter
and the published Core M/Q behavior. No new shared command/parser,
Core header or Notes capability. No service, schema, write review,
status values, no-op behavior or currentness protections changed.
The existing #146 picker tests are updated only for deliberate disclosure;
canonical native status write/guard tests are unchanged.

13 new synthetic menu cases cover summary and status disclosure,
navigation, same-read return, missing read redaction and unopted selector
behavior. Existing #146 native workspace tests and local menu regressions
remain separate preservation gates. Local qualification pending.
E2c review/receipt metadata remains; B/F await the released Core contract.
