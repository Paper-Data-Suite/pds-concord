# Concord #148 — Slice 4A Repair 5: strict mypy module identity

## Cause and source-scoped fix

The full native pytest suite passed (3,535 passed; 19 skipped). Repair 4
reused that green suite, built pds-concord 0.3.4 and passed Ruff. Strict mypy
then stopped because `scripts/issue148_actor_callsite_census.py` was mapped
under both `issue148_actor_callsite_census` and
`scripts.issue148_actor_callsite_census`. The repository includes `scripts`
in `tool.mypy.files`; the sibling script imports the census via `scripts.*`
while the `scripts` folder has no `__init__.py` package marker.

The only new tracked source change in Repair 5 is
`[tool.mypy] explicit_package_bases = true`, retaining `strict = true` and
`files = ["concord", "scripts"]`. This follows mypy's documented treatment
of file-based namespace packages without creating a Python package or
skipping individual files. If strict typing discovers new errors, stop and
repair them; do not weaken the gate. This config change contains no
runtime execution logic and does not change the built Concord package.

## Evidence policy

The runner must validate the original complete pytest log, the Repair 4
mypy-failure log and the exact checkout residues from the failed execution.
It must compare the installed test fixture's Python AST modulo Ruff-only
adjacent import ordering, then run full `python -m mypy` before any new build.
It must run the remaining original validator gates unchanged, including
isolated installed-wheel setup/relaunch/authoring with synthetic records.
Missing or mismatched evidence is a hard stop. No commit/push until the
remaining validation and audit gates all pass. No Suite launch, classroom
trial, Linux/Windows PR CI, or human review is implied by this local gate.

## Native evidence

- Full-suite green log SHA-256: `a16feb99c7e939df0391d2d99a1171a34e83bfb689bdc86a8bfeaf197a56ab98`
- Repair 4 mypy failure log SHA-256: `7c3944faede7b07076d949eac758d06e62e6e451e2da3b230024ccdf0290e29d`
- Remaining validation SHA-256: `f86ef73e19cfa70d6cadc8354887cae708518b12700bde9974c163dcf27265a8`
- Official Core 0.6.6 wheel SHA-256: `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`
- Corrected pyproject SHA-256: `7caa91435b41cbf5cffe4f73fbd671296ae7a191376a1e8eb98a6b4dd48e8db6`
- Recorded: `2026-11-15T15:54:11.718565+00:00`
- Native platform: `Windows-10-10.0.26200-SP0`
- No production Concord module files were edited by Repair 5.
- Linux/Windows PR CI, Suite launch, and independent review remain separate gates.
