# Concord #142 — Slice 6C3C: historical #108 scoring menu contract reconciliation

**Scope:** `tests/test_menu_artifact_scoring_issue108.py` and this additive audit note. **No production changes.**

Historical #108 menu-decision tests used a fake Activity without a Core class,
missing routine projection/preview snapshot evidence and post-commit pinned
workspace authority. With #142 authority guards, the former mocks stop before
exercise of the originally asserted preview, confirmation, cancellation, next
Artifact and another-Criterion behaviors. The accepted real-workspace synthetic
integration tests separately exercise canonical Core Standards loading,
workspace binding, revision checks, stale refusal and Score continuation.

This bounded reconciliation adds a named-case-only autouse fixture supplying a
synthetic authority (Class `class-1`, Activity `activity-1`, in-memory `Path('.')`
root, digest `abc123`), with strict snapshot/digest checks in the fake refresh.
The fixture is activated for only the eleven previously failing #108 tests.
The historical fake routine projection and Score preview carry matching snapshot
20/digest `abc123`. Score mutation doubles carry an explicit post-commit
`write_context`. The another-Criterion test passes a pinned origin; the next
Artifact and reload cases reflect their committed revisions, and mocks accept
new explicit `workspace_root` and canonical write keyword arguments.

Unit tests continue to assert teacher choice and confirmation, exact selected
Artifact, absence/no-write, no parallel Score, specific criterion/scale/value,
next work selection and iteration. These tests do not claim to re-prove canonical
Core validation, security guards, or real persistence; see #142 Slice 5B2, 6A,
6B and #162 for those independent evidence boundaries.

**Status:** Candidate; Windows pytest and repository-wide Ruff/mypy/whitespace
qualification required. Frozen #140 audit evidence untouched; no staging,
commit, push or school workspace access.
