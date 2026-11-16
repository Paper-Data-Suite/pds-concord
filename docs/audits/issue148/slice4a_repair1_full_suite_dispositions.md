# Concord #148 — Slice 4A Repair 1: full-suite regression reconciliation

**Pinned base:** `b5a14de2ccebc4bf91e4e208e3e2a7496e266b7d`
**Initial complete Windows attempt:** 3,522 passed, 19 skipped, 13 failed. This
was a **failed acceptance run**: no release/merge/CI claim is made.

## Root causes and reviewed dispositions

| Failure group | Count | Correction |
| --- | ---: | --- |
| #140 earlier actor-author fixtures | 3 | Supply the exact synthetic `ActorReference` for a `teacher_author` instead of an invalid `None` reference. The current teacher/Author mismatch guard stays enabled. |
| #146 controlled status baseline | 7 | Assert the new `confirm_actor_write` review, absence of direct legacy confirmation, exact `state` handoff and `legacy_confirm=confirm_write`; preserve numbered status choosers and Standards forwarding. |
| #140/#142 current-source boundary CSV | 1 | Regenerate **only** the explicitly current #142 successor call-line inventory from the current AST. Reject any drift outside call-line locations. Keep the frozen #140 baseline and its original Git-blob identity unmodified. |
| #113 Packet subject review | 1 | Expect third, actor-bound re-preparation before substantive write confirmation. Verify all subject bindings and actor consistency; no extra commit. |
| #101 post-generation open menu | 1 | Give the synthetic prepared result its actor-bearing `.request` as required by reviewed preparation; continue asserting render and post-generation handoff. |

All corrections are test/derived-audit maintenance only. No weakening of
provenance, currentness/authorization, Standards, immutable history, no-write
cancellation, or Core-owned storage constraints is permitted. Production files,
Core/Suite/Meridian dependencies, and version remain unchanged.

## Qualification gates

The repair runner refuses a changed branch, dirty/unrecognized residue, a
mismatched original Slice 4A payload, changed pinned source blobs, or a successor
inventory whose semantic columns drift. It first executes only the five affected
pytest files plus the live source-inventory witness, then runs **one**
`validate_repository.py` complete acceptance lane (including Ruff, mypy, docs,
wheel builds and smokes) against the authenticated official Core v0.6.6 wheel.

Native qualification, installed-wheel pass, CI, Suite foreground launch, and a
human trial must each be labeled separately; only a fully green native run may
update `slice4a_release_acceptance.md` and commit/push. The earlier 12-minute
failed pytest is not reused as a successful gate.
