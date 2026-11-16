# Concord #148 — Slice 3D3A: manifest generation and publication actor review

## Scope

Only `concord/menu_publication.py` is modified in production. The revision
uses `confirm_prepared_actor_write` for immutable manifest generation and for
first/superseding/withdrawn-head Publication, including the teacher-facing
Share Results path. Each selected actor yields a fresh
`GenerateAcademicResultManifestRequest` and `AcademicResultManifestPreview`.
The exact confirmed pair is passed to the canonical write service, including
the preview's generated-at clock.

## Security and ownership

The initial revision reason is selected once and preserved through temporary
actor selection. A temporary actor changes the actor-attribution portion of the
public manifest projection, not the Activity's academic state, registration,
publication lineage, or permissions. Profile-fingerprint revalidation and
no-write cancellation remain owned by `confirm_prepared_actor_write`.
Self-declared attribution is not login or publication authorization.

Core registration create/update, withdrawal, and catalog rebuild currently
have no `WorkflowActor` argument. This slice does not fabricate provenance or
replace Core service contracts. Publication conflict and partial-success
handling, expected current/withdrawn publication-head parameters, and
standards/privacy preparation remain unchanged.

## Qualification

Require the exact branch/commit and pinned Git blobs, a clean working tree,
and authenticated source archive. Before applying production changes, check
Ruff lint/format and mypy against a temporary shadow file. After applying,
run installed-Core verification, focused publication and #148 actor tests,
pytest collection, and Git diff checks. Automatically commit/push only after
successful qualification. Avoid full repository tests on this bounded slice.

## Follow-up

Finish actor-attributed Artifact scoring, inspect other module call sites, then
complete issue #148 cross-menu, cross-restart, cancellation, and Windows
acceptance before merge.
