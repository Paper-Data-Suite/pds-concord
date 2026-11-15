# Concord #148 — Slice 4A: consolidated repository and installed acceptance

**Starting branch:** `148-persistent-reviewable-teacher-attribution`
**Pinned base:** `b5a14de2ccebc4bf91e4e208e3e2a7496e266b7d`
**Scope:** acceptance instrumentation only; no production Concord, Core, Suite, Meridian, or academic schema changes.

## One full-repository lane

Extend the existing `scripts/validate_repository.py` complete validation lane,
without invoking a second full pytest suite. This existing CI-aligned entry point
checks the official Core 0.6.6 wheel and vendored grouping fixtures, pip check,
package build, pytest, Ruff, strict mypy, documentation, release compatibility,
Twine, package content, release artifacts, and existing installed wheel smokes.

A new `scripts/smoke_test_issue148_teacher_attribution_wheel.py` receives the
*same candidate wheel* and authenticated Core wheel that validation already
builds/uses. It creates a disposable virtual environment and redirects both
Core configuration and academic workspace to synthetic temporary roots.

Three **distinct Python processes** execute the copied synthetic stage script
under `-I`, with `PYTHONPATH` removed:

1. `setup`: actual installed Concord Teacher Settings `_setup` logic reviews
   the exact saved name/actor/scope and saves the profile; no academic writes.
   UI text-entry and confirmation prompts are controlled by the test fixture,
   rather than pretending that a human operated a real console.
2. `author`: a newly started installed-wheel session silently resolves the
   profile, creates Core synthetic class/roster and Concord Activity plus Group,
   and reads the exact persisted actor ID and display-label snapshots.
3. `relaunch`: another fresh process silently reuses the profile, authors a
   second Activity and verifies historical records and the preference revision
   are unchanged. Core's config.json remains absent; no sibling packages are
   installed. This is a **source-independent installed consumer smoke**, not a
   claim that Suite itself launched Concord.

The suite also asserts the smoke is wired into complete repository validation.
No release version or manifest changes are part of #148.

## Acceptance distinctions and remaining gates

- **3E6F source actor census:** qualified at `b5a14de` (43 menus, 124 candidates,
  104 reviewed, 9 indirect, 11 other contracts; 107 focused passed, 2 skipped).
- **4A repository qualification:** PASS (combined evidence): earlier
  full pytest green; verified import-order-only repair; remaining validator
  phases and isolated-wheel acceptance passed natively in Repair 5.
- **Installed-wheel setup/relaunch/author:** PASS on native host,
  in three isolated site-packages-only Python processes after Repair 5.
- **Linux and Windows CI:** PENDING validation on resulting pull request.
- **Suite foreground launch and human classroom trial:** NOT demonstrated by
  the synthetic installed smoke. Treat as separate evidence; do not claim
  any live classroom records, login authority or private Notes ownership.

**Stop conditions:** any failure in the full repo or installed gates must halt
before commit. Subsequent repairs should rerun affected checks, not duplicate
successful full-suite validation without need. Verify clean tree and remote
branch HEAD before pushing. Confirm CI and review separately before squash/merge.

## Source-pinned native acceptance after Repair 5

- Full repository pytest: 3,535 passed, 19 skipped on the Repair 1
  candidate before the fixture import-order-only repair.
- Ruff import-only update: AST differs only in import-statement order; no production code edit.
- Pre-fix fixture SHA-256: `ff47e0063c5c28444305ce9bbb554d4daeccfde7f9e7cc3ae25a69347460a985`
- Post-fix fixture SHA-256: `7caa91435b41cbf5cffe4f73fbd671296ae7a191376a1e8eb98a6b4dd48e8db6`
- Previous full-suite log SHA-256: `a16feb99c7e939df0391d2d99a1171a34e83bfb689bdc86a8bfeaf197a56ab98`
- Resumed acceptance log SHA-256: `f86ef73e19cfa70d6cadc8354887cae708518b12700bde9974c163dcf27265a8`
- Official Core wheel SHA-256: `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`
- Timestamp UTC: `2026-11-15T15:54:11.663237+00:00`
- Platform: `Windows-10-10.0.26200-SP0`
- Runner Python: `3.11.9`
- Combined gate: full-suite evidence + independent full validator
  remainder (Ruff, strict mypy, docs, release, Twine, packaging,
  installed-wheel smokes and #148 setup/relaunch/author).
- Not yet proved: supported Linux/Windows PR CI, real Suite foreground
  launch, human classroom trial or independent PR review.

### Strict mypy module-name resolution

The source tree had no `scripts/__init__.py`, while one audit script
imports another as `scripts.issue148_actor_callsite_census`.
The original strict mypy command assigned two module names.
`[tool.mypy] explicit_package_bases = true` now stabilizes module
naming relative to the repository root, without silencing checks.
- Previous mypy-failure native evidence: `a16feb99c7e939df0391d2d99a1171a34e83bfb689bdc86a8bfeaf197a56ab98`
- Previous `pyproject.toml` SHA-256: `ff47e0063c5c28444305ce9bbb554d4daeccfde7f9e7cc3ae25a69347460a985`
- Corrected `pyproject.toml` SHA-256: `7caa91435b41cbf5cffe4f73fbd671296ae7a191376a1e8eb98a6b4dd48e8db6`
