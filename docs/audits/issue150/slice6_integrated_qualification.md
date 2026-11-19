# Concord #150 — Slice 6 integrated qualification and PR handoff

**Status:** Source candidate; native Windows, candidate wheel, and PR CI pending.
**Exact branch baseline:** `150-use-lesson-with-another-class` at `280d93a3c6035f15b4f4f8ccd9e693b2ccb49564`.
**Base main:** `59df22e07e7fa4e14677bf75cb0089fc0604f9fa`.
**Published Concord version retained:** `0.3.4`; this is a **development candidate wheel**, not a public v0.3.4 re-release.
**Official Core release wheel:** `pds_core-0.6.6-py3-none-any.whl`, SHA-256 `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`.

## Final source and installed acceptance contract

The consolidated `scripts/validate_repository.py` is the existing CI-owned gate, not a second copy/build process. It performs official Core wheel authentication and installed-Core metadata checks, frozen Core grouping fixtures, dependency checks, build and packaging/entry-point audits, full source pytest, full Ruff/mypy, documentation/release checks, Twine, isolated existing wheel smokes, plus the new #150 synthetic installed wheel smoke. The runner invokes that validator **once** after verifying the exact source scope and preflight.

The new `scripts/smoke_test_issue150_reuse_wheel.py` installs the exact authenticated official Core wheel and a **candidate built Concord wheel** into an isolated virtual environment, then exercises:

- 30-student source versus disjoint 29-student target synthetic Core rosters;
- zero-write `prepare_activity_copy`, digest-authorized create-only target `copy_activity`, source snapshot unchanged;
- exactly one fresh planned target Session; no copied source Group, GroupPlan, Membership, Packet/Artifact, Criterion Set, or Score records;
- target-only read-only Core-roster Cluster preflight, material generation checkpoint, and typed assessment checkpoint;
- one explicit target six-empty-Cluster draft via the existing guarded GroupPlan writer;
- canonical resume sees its own draft GroupPlan as needing attention, not as applied operational Groups;
- source snapshot unchanged after copy and target-only planning.

The smoke does not issue a real printing command, scan paper, distribute handouts, collect returns, assign Scores, create Grades, or publish; those are **NOT YET PHYSICALLY QUALIFIED**. It does not infer that Core 0.6.6 has the newer header, `:notes`, or roster administration APIs. Broad producer UI migration remains #153.

## Evidence and release decision

| Gate | Status before native/PR completion | Expected evidence |
| --- | --- | --- |
| #150 Slices 1–5 focused source tests | Native accepted | Windows logs; Slice 5 `315 passed`, commit `280d93a` |
| Full source pytest and Ruff/mypy/docs | **PENDING** | `validate_repository.py` result and timing summary |
| Official Core 0.6.6 wheel provenance | **PENDING Slice 6** | Exact released wheel hash and installed verification |
| Concord candidate wheel/sdist and package boundary | **PENDING** | Build, release artifact contract, Twine, package checks |
| #150 isolated installed-wheel full reuse smoke | **PENDING** | Disjoint 30/29 synthetic class and Cluster evidence |
| Linux/Windows GitHub PR CI matrix | **PENDING** | Exact reviewed feature HEAD/PR workflow runs |
| End-to-end physical printer/scanner/returned-paper | **NOT YET PHYSICALLY QUALIFIED** | Separate real-paper classroom gate |
| Release/version/tag/publication/merge | **NOT AUTHORIZED** | Separate approval and milestone tickets |

After the native runner passes, open/update a PR titled `feat(concord): guide safe, resumable cross-class lesson reuse (#150)` with base `main`, head `150-use-lesson-with-another-class`, and `Closes #150` in the body. Wait for required Linux/Windows PR CI and independent review before any merge. The PR does not establish that v0.4.0 was released.

A failed qualification stops without deleting, resetting, or silently committing the worktree. Maintain separate terms: **source green**, **installed-candidate green**, **GitHub CI green**, and **physical accepted**.
