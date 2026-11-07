# Concord #147 — Slice 4 consolidated qualification plan

**Issue:** https://github.com/Paper-Data-Suite/pds-concord/issues/147

**Branch:** `147-planned-cluster-bulk-roster-placement`

**Entry baseline:** `0bbb9bf2e45e4e078add9c596c3c0d38794e8696` (Slice 3 qualified and pushed; 104 focused tests passed, zero XFAIL, Ruff and strict mypy passed).

**Released Core authority:** `pds-core` **0.6.6**, authenticated wheel `pds_core-0.6.6-py3-none-any.whl` with SHA-256 `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`. Core `main` was observed at `a0d5e1a50580bbe025f0cad23c7e8524203a52ec` and Suite `main` at `98649a5816485652a29b5c59e06f4704a7960626` during #147 planning. Source HEADs are **not** release-capability attestations.

## Consolidated acceptance evidence

| Requirement | Automated source witness and qualification lane |
| --- | --- |
| Zero-write bulk preparation; one guarded plan revision; digest and actor binding | `tests/test_issue147_slice1_bulk_engine.py`, `tests/test_issue147_slice3_batch_cli.py` |
| Core roster authority, stale snapshots, invalid IDs, wrong revisions, no implicit roster refresh | Slice 1 and 3 tests; original `test_group_plan_manual_issue51.py` and GroupPlan boundary tests |
| Cluster-first teacher choice, page-only/all-eligible selection, cancel/Back/Main/Quit and retained choice | `tests/test_issue147_slice2_cluster_bulk_menu.py` and retired original Slice 0 XFAIL witnesses |
| Synthetic 29-student `5/5/5/5/4/5` and 30-student `6/5/5/3/6/5` six-Cluster partitions | Real menu/service-backed Slice 2 acceptance tests |
| Direct-CLI parity and no regression to CSV, saved arrangements, approval/application | Slice 3 tests; `tests/test_group_plan_cli_issue51.py`; `tests/test_group_plan_application_cli_issue56.py`; `tests/test_issue136_slice5b_saved_grouping_cli.py`; `tests/test_issue136_slice5g_saved_grouping_csv.py` |
| Cross-surface invalidation, distinct GroupPlan approval, workspace-bound digest | `tests/test_issue147_slice4_consolidated.py` |
| Complete Concord repository, Core installed wheel, packaging, documentation, release artifacts, published grouping contract | Unmodified `scripts/validate_repository.py --core-wheel <authenticated Core 0.6.6 wheel> --allow-dirty` |
| Supported Python 3.11–3.14 on Linux and Windows | Existing `.github/workflows/ci.yml` on PR; **not** a local runner result |

## Qualifying this slice

The Slice 4 runner verifies the exact clean branch and source Git blobs, authenticates the **actual installed** Core distribution and released wheel, applies two **new-only** test/audit files, and runs focused tests. It then delegates exactly one complete local validation to the existing repository script, which covers: official Core and grouping fixtures, `pip check`, sdist/wheel builds, repository pytest, Ruff, strict mypy, documentation, release compatibility, Twine, package content, release artifacts, installed-wheel smokes, and isolated #136 Core 0.6.6 grouping acceptance. Commit and push happen only if those local checks and a strict file-scope/clean-index check pass.

**Contract boundary:** No change to Concord runtime, Core, Suite, Meridian, package version or published dependency constraints in Slice 4. This acceptance tests Concord's producer-owned GroupPlan draft mutation against the released Core class roster and Standards. Nothing here is a Core roster mutation, Suite launcher integration or cross-repository transaction.

**Remaining release gates after local qualification:** open a Concord PR, require the supported GitHub CI matrix to pass, inspect mergeability, obtain the final merge decision. A real classroom walkthrough and physical print/scan acceptance are separate under Concord #155; never claim the synthetic matrix constitutes human physical acceptance.
