# Concord validation and CI performance

**Status:** Implemented for issue #93
**Applies to:** Concord `0.3.0.dev0` development validation
**Released Core baseline:** `pds-core` `0.6.3` / `pds-core>=0.6.3,<0.7`

Issue #93 reduces Concord validation and CI cost without reducing substantive
runtime, storage-integrity, packaging, installed-wheel, or cross-platform
coverage.

The governing rule is:

```text
faster validation != weaker validation
```

This work follows the sequence:

```text
measure
    ->
de-duplicate harness work
    ->
profile remaining runtime
    ->
optimize demonstrated hot paths
    ->
factor CI
    ->
remeasure
```

## Authoritative complete qualification

The authoritative local complete repository gate remains:

```powershell
python scripts\validate_repository.py `
  --core-wheel "<path-to-pds_core-0.6.3-py3-none-any.whl>"
```

For development on a dirty issue branch:

```powershell
python scripts\validate_repository.py `
  --core-wheel "<path-to-pds_core-0.6.3-py3-none-any.whl>" `
  --allow-dirty
```

The complete gate still establishes all of the following:

- authenticated released Core compatibility;
- Core grouping-fixture compatibility;
- `pip check`;
- full pytest;
- Ruff;
- strict Mypy;
- documentation validation;
- release-compatibility validation;
- clean source-tree wheel and sdist construction;
- Twine validation;
- package-content policy;
- release-artifact policy;
- base installed candidate-wheel acceptance;
- Activity-copying installed acceptance;
- reusable-presets installed acceptance;
- guided-Activity installed acceptance;
- task-oriented-menu installed acceptance;
- module-operations / readiness / attention installed acceptance;
- `git diff --check`; and
- repository-residue rejection unless `--allow-dirty` is explicitly used.

Timing diagnostics are observational only. No validation phase has a wall-clock
pass/fail threshold.

## Measurement baseline

The authoritative pre-optimization baseline was captured on Windows with Python
3.11.9 using released Core `0.6.3`.

```text
Core wheel verification:                    0.184 s
Core grouping fixtures:                     0.187 s
pip check:                                  1.162 s
pytest:                                   286.730 s
Ruff:                                       0.238 s
Mypy:                                       6.614 s
documentation validation:                   0.200 s
release compatibility:                      1.596 s
source tree copy:                            0.378 s
package build:                              23.430 s
Twine:                                      0.607 s
package content:                             0.166 s
release artifacts:                           0.193 s
installed-wheel smoke: base:                57.247 s
installed-wheel smoke: Activity copying:    21.453 s
installed-wheel smoke: reusable presets:    21.671 s
installed-wheel smoke: guided Activity:     21.588 s
installed-wheel smoke: task-oriented menu:  19.576 s
installed-wheel smoke: module operations:   20.524 s
git diff check:                              0.104 s
TOTAL:                                     487.916 s
```

The preliminary approximately-909-second pytest observation that motivated
issue #93 is not used as the comparison baseline because it came from a
different run context.

## Measured integration result

After the main optimization tranche, a comparable complete validator
integration run on the same Windows / Python 3.11.9 development environment reported:

```text
Core wheel verification:                             0.224 s
Core grouping fixtures:                              0.076 s
pip check:                                           0.329 s
source tree copy:                                     0.271 s
package build:                                       20.447 s
pytest:                                             220.944 s
Ruff:                                                0.182 s
Mypy:                                                2.884 s
documentation validation:                            0.205 s
release compatibility:                               1.334 s
Twine:                                               0.375 s
package content:                                      0.123 s
release artifacts:                                    0.166 s
installed-wheel smoke: base:                         44.637 s
installed-wheel smoke: shared feature scenarios:     21.962 s
installed-wheel smoke: module operations:            19.037 s
git diff check:                                       0.047 s
TOTAL:                                              336.195 s
```

That run completed with validator exit code `0`.

### Before / after summary

| Measure | Before | After | Change |
| --- | ---: | ---: | ---: |
| Full pytest inside complete validation | 286.730 s | 220.944 s | -22.9% |
| Four feature installed smokes | 84.288 s | 21.962 s | -73.9% |
| All installed-wheel qualification | 162.059 s | 85.636 s | -47.2% |
| Complete repository validation | 487.916 s | 336.195 s | -31.1% |

The complete validator therefore saved `151.721 s` in the measured comparison
while retaining the complete qualification boundary.

A separate post-storage full pytest profile completed `1,315` tests with `11`
expected platform skips in `216.31 s`. The later complete-validator run,
after additional issue #93 tests were added and the candidate Core wheel was
supplied, completed `1,318` tests with `10` expected skips in `220.54 s`
(`220.944 s` validator phase time).

## What changed

### 1. Stable phase timing

`scripts/validate_repository.py` now records each major phase with
`time.perf_counter()` and prints a stable summary even when a later phase
fails.

Pytest runs with `--durations=25` so the slowest tests remain visible during
complete qualification.

### 2. Installed-wheel environment de-duplication

The following installed feature scenarios still exist as independently
runnable smoke scripts:

```text
scripts/smoke_test_activity_copying_wheel.py
scripts/smoke_test_reusable_presets_wheel.py
scripts/smoke_test_guided_activity_wheel.py
scripts/smoke_test_task_oriented_activity_menu_wheel.py
```

Complete validation now executes those scenarios through:

```text
scripts/smoke_test_feature_wheels.py
```

That harness creates one fresh installed candidate-wheel environment, installs
released Core and Concord once, runs `pip check` once, and then executes each
feature scenario independently. Each scenario still creates its own fresh
workspace and retains its own assertions and failure identity.

The base installed producer acceptance and module-operations acceptance remain
separate because they establish distinct qualification boundaries.

### 3. Current graph read reuse

Within one `load_current_record_graph()` operation, Concord now reuses the exact
current pointer, verified snapshot chain, snapshot digest, and materialized graph
instead of reconstructing the same immutable state more than once.

There is no persistent canonical-state cache.

### 4. Commit-state reuse

`commit_record_batch()` now reuses already verified immutable current state
during its pre-publication work rather than invoking equivalent public reads
again.

The final post-pointer `load_current_record_graph()` verification remains in
place.

### 5. Linear snapshot-history validation

`list_work_snapshots()` now validates a snapshot history in one chronological
pass.

The old pattern validated each revision independently, repeatedly walking
overlapping predecessor chains. The new traversal still verifies:

- contiguous revisions;
- canonical snapshot identity;
- predecessor revision;
- predecessor SHA-256;
- every selected record digest and graph; and
- the same corruption / orphan failure modes.

Direct exact historical snapshot loads retain their full predecessor-chain
validation.

### 6. Single-pass record-history inspection

Canonical write-history validation now obtains verified record revision history
once per record identity and reuses those immutable results inside the same
operation.

Public `list_record_identities()` still validates the revisions behind each
identity; validation has not been converted into an unverified directory
listing.

### 7. Candidate release wheel reuse inside pytest

Complete validation now constructs the candidate release artifacts before
pytest and supplies the exact candidate wheel through:

```text
PDS_CONCORD_TEST_WHEEL
```

The package-metadata pytest fixture validates that supplied wheel rather than
building an equivalent second wheel.

Ordinary standalone `python -m pytest` remains self-contained: when
`PDS_CONCORD_TEST_WHEEL` is absent, the fixture still performs its own isolated
wheel build.

### 8. Opt-in reusable static-analysis caches

Cold, disposable static-analysis caches remain the default.

Developers may explicitly request reusable Ruff and Mypy caches:

```powershell
python scripts\validate_repository.py `
  --core-wheel "<path-to-Core-wheel>" `
  --allow-dirty `
  --reuse-static-caches
```

The optional cache root is controlled by:

```text
PDS_CONCORD_VALIDATION_CACHE_ROOT
```

If not configured, a persistent directory under the operating system temporary
area is used.

The cache:

- affects speed only;
- is not canonical authority;
- may be deleted at any time;
- is rejected if it resolves inside the repository; and
- does not alter validation coverage or pass/fail semantics.

CI does not use `--reuse-static-caches`; complete CI qualification remains cold
with respect to this development option.

## Final cold qualification

After all issue #93 implementation, CI factoring, cache-option, benchmark, and
documentation changes were present, the default cold authoritative validator
was run again without `--reuse-static-caches`.

The final Windows / Python 3.11.9 qualification reported:

```text
Core wheel verification:                             0.116 s
Core grouping fixtures:                              0.133 s
pip check:                                           0.421 s
source tree copy:                                     0.255 s
package build:                                       19.696 s
pytest:                                             197.694 s
Ruff:                                                0.225 s
Mypy:                                                5.112 s
documentation validation:                            0.250 s
release compatibility:                               1.724 s
Twine:                                               0.573 s
package content:                                      0.160 s
release artifacts:                                    0.244 s
installed-wheel smoke: base:                         51.630 s
installed-wheel smoke: shared feature scenarios:     22.219 s
installed-wheel smoke: module operations:            19.199 s
git diff check:                                       0.043 s
TOTAL:                                              322.901 s
```

That run completed with validator exit code `0`, with `1,330` tests passed and
`10` expected platform skips.

### Final before / after summary

| Measure | Before | Final cold run | Change |
| --- | ---: | ---: | ---: |
| Full pytest inside complete validation | 286.730 s | 197.694 s | -31.1% |
| Four feature installed smokes | 84.288 s | 22.219 s | -73.6% |
| All installed-wheel qualification | 162.059 s | 93.048 s | -42.6% |
| Complete repository validation | 487.916 s | 322.901 s | -33.8% |

The final cold complete validator therefore saved `165.015 s` versus the
authoritative pre-optimization baseline while retaining the complete
qualification boundary.

The earlier `336.195 s` run remains useful integration evidence showing the
same optimization direction before the final documentation and benchmark
coverage were added.

## Canonical-storage benchmark

Because issue #93 changed immutable-history traversal, the repository includes
the diagnostic benchmark at
`scripts/benchmark_storage_performance_issue93.py`:

```powershell
python scripts\benchmark_storage_performance_issue93.py `
  --snapshots 12 `
  --repetitions 5
```

The benchmark reconstructs the pre-#93 read patterns against the same synthetic
canonical history and compares them with the optimized paths. It uses median
`time.perf_counter()` measurements and defines no performance threshold.

Measured Windows / Python 3.11.9 results:

```text
Issue #93 storage benchmark: 12 snapshots, 5 median repetitions
list_work_snapshots:
    legacy=0.078408 s
    optimized=0.035175 s
    55.1% faster

load_current_record_graph:
    legacy=0.022176 s
    optimized=0.012696 s
    42.7% faster

record-history enumeration:
    legacy=0.034541 s
    optimized=0.017584 s
    49.1% faster
```

These results are diagnostic evidence, not contractual timing guarantees.

## Storage integrity preserved

The optimization does not weaken Concord's fail-closed storage contract.
Regression coverage specifically preserves:

```text
immutable record revisions
snapshot predecessor revision verification
snapshot predecessor SHA-256 verification
current pointer digest verification
record digest verification
canonical identity/path agreement
append-only semantics
expected snapshot revision conflicts
record graph validation
Core standards validation
work/class identity validation
symlink/path-security protections
pre-pointer failure semantics
post-pointer verification
partial-success boundaries
orphan/corruption detection
```

Optimized history traversal continues to reject corruption in predecessor
state, not only corruption at the current head.

## CI factoring

Supported runtime coverage remains:

```text
Ubuntu  x Python 3.11, 3.12, 3.13, 3.14
Windows x Python 3.11, 3.12, 3.13, 3.14
```

All eight cells remain compatibility cells and prove:

- authenticated Core release inputs;
- Core install;
- installed dependency boundary / `pip check`;
- Concord import;
- full pytest; and
- repository hygiene / `git diff --check`.

Complete qualification additionally runs on:

```text
Ubuntu / Python 3.11
Windows / Python 3.14
```

Those reference cells delegate to the authoritative
`scripts/validate_repository.py` gate and therefore add:

- Ruff;
- strict Mypy;
- documentation;
- release compatibility;
- clean wheel + sdist construction;
- Twine;
- package-content validation;
- release-artifact validation; and
- every required installed-wheel acceptance scenario.

This preserves both supported operating systems and spans the supported Python
range while avoiding eight repetitions of platform-independent release
qualification.

The structural change reduces complete-qualification execution from eight CI
cells to two, a 75% reduction in the number of cells performing that expensive
tier. This is not presented as a 75% aggregate CI-time reduction: exact GitHub
runner-time improvement must be taken from actual CI runs after the branch is
pushed.

## Remaining measured hotspots

After the optimization tranche, the two slowest application-level pytest calls
in the complete run were the starter-template install-all scenarios at
approximately five seconds each:

```text
test_starter_install_all_installs_only_missing
test_install_all_installs_thirty_and_replays_idempotently
```

They exercise real repeated canonical Template creation and idempotent replay.
They were not optimized further in issue #93 because the measured remaining
cost did not justify another storage-contract change after the larger duplicate
history and qualification costs had been removed.

Other individual slow tests were approximately one to three seconds and spread
across Packet, publication, scoring, Artifact, and GroupPlan workflows rather
than revealing another single dominant algorithmic hotspot.

`pytest-xdist` was not introduced.

## Teacher-runtime opened-Activity performance (issue #104)

Issue #104 is distinct from the validation/CI optimization above.

```text
#93
storage / validation / CI optimization

#104
teacher-runtime opened-Activity projection optimization
```

Issue #104 preserves the same governing rule at the teacher-runtime boundary:

```text
faster Activity projection != weaker canonical validation
```

The ordinary opened-Activity path now creates one ephemeral
`ActivityReadContext` from one exact verified current Activity head. The
summary and local Plan, Prepare, Collect, Review, and Score attention
projections reuse that immutable operation-scoped state. Inactive Share
attention reuses the same verified Activity identity and snapshot while
retaining its Core class validation. Once Share is registered, manifest preview
and publication-series reconciliation remain independent authorities.

There is no persistent canonical-state cache, no second canonical store, no
background index, and no asynchronous menu rendering.

### Before-change baseline

The pre-#104 baseline was captured on:

```text
OS: Windows-10-10.0.26200-SP0
Python: 3.11.9
pds-core: 0.6.3
pds-concord: 0.3.0
Concord commit: 01dc76b4b0859b1cc78fa48840b0de9ed59a8b45
Fixture: 12 snapshots / 0 Artifacts
Median repetitions: 5
```

```text
show_activity
  median_seconds: 0.050104
  snapshot_chain_loads: 4
  graph_materializations: 3
  graph_validations: 3

inspect_activity_attention
  median_seconds: 0.141985
  snapshot_chain_loads: 11
  graph_materializations: 9
  graph_validations: 9

opened_activity_local_projection
  median_seconds: 0.188104
  snapshot_chain_loads: 15
  graph_materializations: 12
  graph_validations: 12
```

The structural baseline for one opened Activity projection was therefore:

```text
15 / 12 / 12
snapshot-chain loads / graph materializations / graph validations
```

### Final clean-tree measurement

The repository-owned diagnostic benchmark is:

```text
scripts/benchmark_open_activity_performance_issue104.py
```

The final clean-tree measurement was captured on:

```text
OS: Windows-10-10.0.26200-SP0
Python: 3.11.9
pds-core: 0.6.3
pds-concord: 0.3.0.dev0
Concord commit: 88f03f52c3fb694ee570b9c926b942899046cb7d
Branch: 104-optimize-open-activity-performance
Working tree dirty: False
Median repetitions: 5
```

For the equivalent 12-snapshot / 0-Artifact case:

```text
show_activity
  median_seconds: 0.015694
  snapshot_chain_loads: 1
  graph_materializations: 1
  graph_validations: 1

inspect_activity_attention
  median_seconds: 0.015496
  snapshot_chain_loads: 1
  graph_materializations: 1
  graph_validations: 1

opened_activity_local_projection
  median_seconds: 0.016246
  snapshot_chain_loads: 1
  graph_materializations: 1
  graph_validations: 1
```

The opened projection moved from `0.188104 s` to `0.016246 s` in this measured
comparison, while its canonical-read structure moved from `15 / 12 / 12` to
`1 / 1 / 1`.

The wall-clock numbers are development-machine observations, not contractual
performance thresholds. The principal acceptance result is removal of duplicate
canonical reads while preserving complete validation.

### Artifact-count scaling

The same benchmark proves that complete Activity graph reconstruction does not
scale with Artifact count:

| Fixture | `show_activity` | Activity attention | Opened projection |
| --- | ---: | ---: | ---: |
| 12 snapshots / 0 Artifacts | 0.015694 s | 0.015496 s | 0.016246 s |
| 12 snapshots / 1 Artifact | 0.018653 s | 0.019453 s | 0.019301 s |
| 21 snapshots / 20 Artifacts | 0.088734 s | 0.088467 s | 0.090158 s |

Every measured operation in all three cases reported:

```text
1 / 1 / 1
snapshot-chain loads / graph materializations / graph validations
```

The 20-Artifact case therefore demonstrates the intended O(1) full-graph
materialization count with respect to Artifact count. Its larger wall-clock
cost reflects the larger verified graph and deeper 21-snapshot history rather
than an N+1 graph-reload pattern.

### Integrity and semantic qualification

Issue #104 regression coverage preserves:

```text
snapshot predecessor verification
current pointer digest verification
record digest verification
record graph validation
standards/mixed Activity compatibility
current-vs-superseded Author and Subject semantics
current Review head semantics
Moderation applicability
Score attention orientation semantics
GroupPlan lifecycle and leave_unassigned semantics
Packet generation-status semantics
Share authority boundaries
menu redraw freshness
read-only inspection
canonical corruption fail-closed behavior
```

Focused real-workspace tests prove 1-Artifact and 20-Artifact attention both
remain at one snapshot-chain load, one graph materialization, and one graph
validation.

The task-oriented-menu installed acceptance uses the candidate wheel in the
shared feature-wheel environment. It creates a nontrivial synthetic Activity
with real attention, opens the Activity through the installed optimized path,
renders attention, reaches Plan/Prepare/Collect/Review/Score/Share and Advanced
menus, and fingerprints the workspace to prove inspection remains read-only.

The existing installed module-operations acceptance remains separate and
continues to prove stable attention codes/counts/actions, privacy-minimal
payloads, read-only behavior, and Core `paper_data_suite.module_operations`
contract compatibility.

## Development guidance

For focused iteration, run the narrow affected tests plus Ruff/Mypy rather than
repeated complete qualification.

Use the complete validator at meaningful integration boundaries and before
merge.

Use `--reuse-static-caches` only as a local development acceleration. A clean
default complete run remains the reference qualification result.

When future validation cost increases materially, repeat the same method:

```text
measure first
    ->
identify duplicate proof or demonstrated hot path
    ->
optimize without changing authority
    ->
retain regression coverage
    ->
remeasure
```
