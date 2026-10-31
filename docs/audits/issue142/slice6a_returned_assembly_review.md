# Concord #142 — Slice 6A: Genuine synthetic returned Artifact qualification

## Purpose and evidence boundary

Prior Slice 5 boundary tests correctly prohibited an unreturned prepared Artifact from
being treated as Review-ready; service spies tested positive argument forwarding without
fabricating a successful Score. Slice 6A adds an **actual** synthetic Core route, retained
PNG scan, returned Artifact, verified PDF assembly, confirmed Author and Subject
associations, and teacher-confirmed Quick Review. All data is fabricated inside
`pytest.tmp_path`, with no access to the teacher's PDS workspace.

## Scenarios

1. Real returned/assembled Artifact plus independently confirmed Author and Subject
   receives exactly one native first Quick Review, either `ready` or
   `ready_with_qualification`. The assembled PDF and manifest must exist.
2. Returned evidence **without** a completed assembly remains ineligible and cannot
   reach the Review confirmation/write boundary, despite confirmed attribution.
3. Assembled evidence **without** a confirmed Author and Subject remains ineligible
   and cannot reach the Review confirmation/write boundary.
4. Evidence-only orientation remains **ineligible for Score** after a successful
   ready Review. The current graph contains no Score records.

The selected Artifact summary, real snap revision, active workspace pinning,
Review commit and Score eligibility reads all use the same disposable Core root.
The tests do not synthesize a ready state or monkeypatch the canonical Review
mutation service.

## Deliberate limit of Slice 6A

This slice qualifies the **returned → assembled → attribution → Quick Review**
path and the evidence-only no-Score invariant. It does **not** qualify a real
standards-backed/local-Criterion Score, Score-another-Criterion, correction
lineage, concurrency race, or cross-Activity continuation. Those are necessary
for follow-on integrated qualification before #142 is merge-ready.

## Integrity and acceptance

A source-only ZIP carries only the new synthetic test module and this audit
record, plus SHA-256 manifest. The separate runner-only ZIP carries the guarded
installer and pinned predecessor reconstruction tools. Default preflight is
read-only. Before adding files, validate the exact issue #142 branch and baseline
HEAD, origin, clean staging area, worktree inventory, accepted prior production
transforms, accepted Ruff/mypy corrections, and manifests. Apply writes only two
new files, never production code or school workspace files. Do not stage, commit
or push. Run focused tests, earlier #142/#140/#141 suite, repository-wide Ruff,
`git diff --check`, and `mypy`.
