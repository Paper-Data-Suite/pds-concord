# Concord #142 · Slice 6C5 — #106 installed-wheel smoke workspace authority

## Observed failure and diagnostic

The disposable-worktree release-validator run passed the full pytest suite,
Ruff, mypy, documentation, wheel/package checks and prior installed smokes. The
#106 installed-wheel scenario failed at `assert "Authors: 0" in rendered`.
Read-only instrumentation exposed the actual `Attribution Review Error`:
`Activity is not available: activity-issue106-installed`. Source snapshot
remained 8 and both proposed Authors and Subjects were unchanged; the harness
had intentionally created the Activity in an explicit disposable `root` but did
not bind `_latest` / `begin_artifact_write_context` to that root after #142.

## Correction scope

Only `scripts/smoke_test_artifact_attribution_batch_wheel.py` changes. The
isolated synthetic #106 scenario delegates to real `_latest`-equivalent
`show_activity` and real `begin_artifact_write_context` using its existing
Core-owned disposable workspace. `revalidate_artifact_write_context` remains
fully real, checking the same pinned workspace and current snapshot digest.
Service adapters accept only the production-dispatched kwargs, assert the root
is exactly the fixture root and no Standards Library is provided for the
`evidence_only` Activity, and pass these kwargs to real canonical mutation
services. The later `Add Several Artifact Subjects` scenario uses the same
real preview binding. Existing `Authors: 0`, `Subjects: 0`, snapshot advance,
confirmed/unresolved statuses, multi-add results and installed `python -I`
provenance assertions are preserved verbatim.

## Qualification and integrity

The original repository and disposable worktree are independently verified
against exact pinned #142 HEAD `28bda95445fbaff631be362dd1ddf7206645172d`
and original smoke Git blob `0901aa0806b2e7b56480c60c13b5d30d565f1346`.
Only exact guarded text anchors may change. Both checkouts receive identical
patched source and this additive audit note. There are no changes to
`concord/` production, historical #140 evidence, installed distributions,
user workspace, staging on original checkout, commits or remote refs.

Before release acceptance, run the isolated #106 installed-wheel smoke using
the prequalified Concord 0.3.4 candidate/Core 0.6.6 wheels, legacy #106 pytest,
repository Ruff/mypy/whitespace, then the full installed-wheel validator.
