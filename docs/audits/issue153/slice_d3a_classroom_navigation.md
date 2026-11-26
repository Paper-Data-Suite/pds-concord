# #153 Slice D3a — classroom planning navigation

D2 qualified at `4f33468303372d0f39964cf3c3e2a67721689290`:
30 action tests (1.31 s), 28 preservation tests (1.54 s); format, lint,
strict Mypy and integrity all passed.

Review found 19 equivalent catch boundaries in five local modules:
Group/Membership (6, including both edit boundaries), Session (2),
Role (4), Responsibility (4), and GroupPlan creation/import (3).
Each caught Core's Main/Quit exceptions through a broad Exception
handler after CancelMenuAction. Re-raise the existing public Core
exceptions before operational error handling. Preserve Back cancellation,
ordinary errors, actor confirmation and write services. Existing protected
outer GroupPlan catches are unchanged.

57 synthetic controller witnesses (18 first selection boundaries and
one nested Group edit boundary, each B/M/Q). Fixtures invoke the real
published navigation parser through a selection helper. They prohibit
error receipts and, at the tested pre-confirmation boundary, confirmation;
the nested edit witness also prohibits the update. No real workspace or
durable write is exercised. Local qualification pending.

Remaining audit: Advanced scoring and assessment, publication, presets,
saved grouping, guided material and other controller catches. Do not
blindly rewrite read-only exception boundaries or post-commit recovery
handlers; inspect their actual prompt reachability and durability.
No Core-owned implementation, parser, dependency or schema change.
