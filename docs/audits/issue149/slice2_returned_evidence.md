# Concord #149 — Slice 2: source-backed returned-evidence attention

## Evidence and boundary

Baseline: source-pinned Concord branch `149-stage-aware-attention-readiness`, HEAD `cd98613438b0ea06234fa6c43130d9236567a4c6`, following the qualified Slice 1 GroupPlan repair. Native Slice 1: 118 passed, one platform skip, one strict XFAIL; the deliberate `--runxfail` replay showed six generated unreturned blank Artifacts still caused six false Author and six false Subject attention items. No physical teacher/student work is used in this slice.

The defect is in two read projections: `workflows/activity_attention.py::_collection_state_from_context` (optimized exact graph) and `workflows/artifact_collection.py::inspect_artifact_collection_state` (public standalone inspection). Both previously treated proposed/disputed current associations alone as proof that **returned** evidence needed confirmation. Neither changed Core retention or the academic write workflows.

## Exact eligibility contract

- Assembly states `ready`, `selection_required`, `assembled` and `needs_recovery` are grounded in `artifact_assembly._select_lineage` and assembly verification. They permit returned-evidence Author/Subject attention where explicit current heads are actually pending. `needs_recovery` is *not* a claim that the output is healthy; recovery/inspection remains independently actionable.
- Partial return with `assembly_state=not_ready` qualifies **only when** a verified current Concord graph includes a routed `ScanReference` whose `artifact_page_id` names this Artifact's declared, `return_expected` page, whose `activity_id` matches the Artifact, and whose `route_id` equals that page's route. These are provenance references created from Core's retained-source routing. This read does not independently open or hash-check the physical retained file; physical custody/integrity qualification remains #151/#155.
- `not_applicable`, unlinked scan references, absent scans, generated or distributed blank pages, the Artifact's own `returned`/`completed` status label alone, packet generation, planned participants and GroupPlan Memberships never establish receipt. Missing evidence keeps proposals as *plans*, without publishing a misleading `Returned evidence ...` count.
- Inconsistent scan routes/activity fail closed with `ArtifactAssemblyIntegrityError`; do not silently translate them to zero. Prior current-head supersession, review/moderation, scoring, share, activity scope, and Core module-attention owner actions remain unchanged.
- `ArtifactCollectionState` and the 20 stable attention codes retain their existing public shapes. No schema, Core/Suite/Meridian, workspace, QR, PDFium or write service changes. The two inspector paths share exactly one helper and one source-of-truth rule.

## Verification

- Retire the last strict XFAIL in `tests/test_issue149_slice0_attention_witnesses.py`; original six-blank-Artifact case becomes a regular passing test.
- New `tests/test_issue149_slice2_collection_stage.py`: generated/distributed/status-only without return; verified assembly stages; partial return reference; missing/wrong route or Activity; unrelated reference and no-return-expected; superseded pending heads; no private paths or scan identifiers in summary; optimized/public inspector parity.
- Keep legacy #67/#104 collection/review/score/attention tests, Core module-attention and structural-readiness contract tests. Run targeted pytest, Ruff check/format, strict mypy on changed production modules and documentation validation. Full repository and installed-wheel acceptance deferred to Slice 4 to avoid redundant expensive tests.
- No official released-wheel, actual returned file opening, physical paper, or human usability pass is claimed by this synthetic qualification.
