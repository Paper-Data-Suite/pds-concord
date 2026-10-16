# Concord #134 Slice 4B — Core v0.6.6 active release baseline

**State:** Unpublished Concord v0.3.3 candidate. Qualification is required before merge or release.

- Concord's active dependency contract is `pds-core>=0.6.6,<0.7`.
- The exact published Core v0.6.6 wheel is `pds_core-0.6.6-py3-none-any.whl` with SHA-256 `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301` (verified from the GitHub release asset).
- Current CI, wheel/authentication checks, packaging metadata, release compatibility guards and isolated installed-wheel smokes use Core 0.6.6 and the as-yet-unpublished Concord 0.3.3 candidate.
- The original Issue #129 Core 0.6.5 / Concord 0.3.2 installed acceptance source, as well as the v0.3.2 release notes/checklists, remain *historical*. The full repository gate instead runs a separate Issue #134 installed reader/publication acceptance under Core 0.6.6 and Concord 0.3.3; no old published artifact is rewritten.
- `pds-core v0.6.6` provides the Windows short viewer-junction handoff. Concord continues to verify exact Artifact/Packet/feedback bytes **before** requesting OS open. Neither a successful API return nor an intercepted shell call proves a real PDF viewer rendered the file.
- Run focused gate per slice. The final qualification must run a single necessary clean full CI, isolated installed smokes, and a **real Windows** long-path PDF/folder (and HTML when available) human-confirmed acceptance before release.

No Core installation in the developer's existing virtual environment is implied by this patch. The final published wheel and sdist must be built and qualified from the exact release commit.
