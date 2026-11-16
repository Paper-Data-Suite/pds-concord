# Concord #148 — Slice 4A Repair 2: import-only resume

**Pinned starting HEAD:** `b5a14de2ccebc4bf91e4e208e3e2a7496e266b7d`

## Prior native evidence and allowed repair

Repair 1 completed a complete Windows pytest suite with **3,535 passed,
19 skipped, zero failed**. The validator then stopped at three Ruff I001
import-order blocks in the synthetic installed-wheel fixture
`tests/fixtures/issue148/installed_attribution_stage.py`.

Repair 2 permits **only Ruff import sorting/formatting of that fixture**,
asserting its full Python AST is unchanged. It pins and verifies the preceding
Repair 1 source archive, existing complete source and audit residue, the
original Git HEAD/blobs, official Core v0.6.6 wheel and the original native
full-suite log outside the repository. The log must demonstrate a completed
green pytest phase followed by the exact fixture I001 failure.

## Qualification resume boundary

After the safe import-only normalization, the runner invokes the existing
`scripts/validate_repository.py` complete lane. Only its single pytest phase
is replaced by the separately preserved and SHA-256-bound successful Repair 1
full-suite evidence. Every other existing validation phase actually runs:
Core and grouping fixtures, pip check, candidate build, Ruff, strict mypy,
docs, release compatibility, Twine, artifact and package checks, installed
wheel smoke tests, and the #148 Settings/setup→process restart→two authoring
workflows with exact immutable actor snapshots.

No Suite/Meridian/Core modification or new release version is authorized.
The reused pytest result applies to an AST-equivalent import-only fixture
change and must be labeled as **prior** testing, not as fresh execution.
Missing/unclear evidence or any remaining failure stops before commit/push.

Linux/Windows PR CI, real Suite foreground launch, PR review and human
classroom trial remain separate pending gates.

## Native evidence

- Prior green suite SHA-256: `a16feb99c7e939df0391d2d99a1171a34e83bfb689bdc86a8bfeaf197a56ab98`
- Repair 5 resumed acceptance SHA-256: `f86ef73e19cfa70d6cadc8354887cae708518b12700bde9974c163dcf27265a8`
- Current pinned base: `b5a14de2ccebc4bf91e4e208e3e2a7496e266b7d`
- Fixture AST unchanged except for contiguous import ordering after Ruff.
- CI and real Suite foreground launch remain separate pending gates.

### Strict mypy module-name resolution

The source tree had no `scripts/__init__.py`, while one audit script
imports another as `scripts.issue148_actor_callsite_census`.
The original strict mypy command assigned two module names.
`[tool.mypy] explicit_package_bases = true` now stabilizes module
naming relative to the repository root, without silencing checks.
- Previous mypy-failure native evidence: `a16feb99c7e939df0391d2d99a1171a34e83bfb689bdc86a8bfeaf197a56ab98`
- Previous `pyproject.toml` SHA-256: `ff47e0063c5c28444305ce9bbb554d4daeccfde7f9e7cc3ae25a69347460a985`
- Corrected `pyproject.toml` SHA-256: `7caa91435b41cbf5cffe4f73fbd671296ae7a191376a1e8eb98a6b4dd48e8db6`
