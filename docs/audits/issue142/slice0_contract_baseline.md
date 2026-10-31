# Concord #142 — Slice 0 additive contract baseline

**Status:** implementation-preparation evidence, **not** a repair, release, teacher-work acceptance, or #162 reviewer certification.

**Pinned starting source:** `pds-concord` `main` / `142-repair-artifact-standards-context` at `28bda95445fbaff631be362dd1ddf7206645172d` (merge of #141). This successor does **not** modify #140 archives, checksums, frozen CSVs, or tests.

## Distinctions verified in source

- `concord/storage.py` enforces canonical Standards when the Activity orientation or standard-backed Criterion/Score graph requires them. The structurally validated Activity read in `concord/workflows/activity_read.py` is not itself Core Standards authorization.
- `concord/menu_artifact.py`'s direct Author/Subject, batch attribution, Review, Quick Review, and Moderation handlers invoke guarded services without visible `standards_library` and `workspace_root` keywords; syntactic absence **does not** prove failure until the invoked path is exercised.
- `concord/menu_artifact_scoring.py` uses `record_prepared_routine_score` twice, once for initial Score and again for the second Criterion. The execution adapter already forwards optional canonical context to `add_score`; both menu calls visibly omit it.
- `concord/workflows/artifact_page.py::prepare_artifact_pages` already resolves its own workspace library if one is not provided. It is a **separate neutral/control seam**, not a mechanical fix target.
- `concord/menu_standards_context.py::standards_for_activity` decides from orientation alone and currently says *No GroupPlan was created* on missing library. `#141`'s Activity editing code separately checks graph history. A #142 resolver must not weaken either rule or inadvertently change GroupPlan behavior.
- Core `pds_core.standards.write_workspace_standards_library`, `load_workspace_standards_library` and profile/Focus verification remain Core-owned; no new Core development APIs are a required dependency. Core/Suite/Meridian are not edited here.

## Frozen #140 source families and forward qualification

The read-only `scripts/issue142_slice0_contract_probe.py --check` enumerates the 15 #142 writer families (13 original context-first, one routine Review, one routine Score) across **16 menu call sites**, attaches the exact #140 Slice 3E service/call-line dispositions, and marks every row **unreviewed**. Frozen #140 operation IDs must be joined in the #162 successor ledger before claims of complete lineage; this Slice 0 does not infer them from AST counts or fabricate human signoff.

| Operation family | Source | Required onward proof |
|---|---|---|
| Individual Author/Subject add, update and immutable replacement | `menu_artifact.py` | Exact selected Core class/Activity/Artifact/roster/actor; current predecessor, no phantom Correction |
| Several Authors/Subjects and selected batch confirmation | `menu_artifact.py` | All-or-nothing CAS, duplicate protection, exact selection, unrelated proposals unchanged |
| Detailed initial/replacement Review | `menu_artifact.py` | Genuine synthetic returned/assembled evidence, privacy and explicit teacher judgments |
| Moderation initial/replacement | `menu_artifact.py` | Exact evidence/Subject context, predecessor and immutable Correction |
| Routine first Review | `menu_artifact.py` → `artifact_routine_review_commit.py` | Eligible returned Artifact and separately chosen teacher outcome |
| Routine Score and Score another Criterion | `menu_artifact_scoring.py` → `artifact_routine_scoring_execution.py` | Fresh snapshot, explicit typed value, exact target, native evidence link; group Score not individual grades |

## Focused Slice 0 tests

`tests/test_issue142_slice0_menu_probe.py` uses only disposable synthetic Core classes and a **genuine persisted** Concord Artifact (created through `prepare_artifact_pages`, without fabricating returned scans). The multi-Author menu makes a **proposed** association, not confirmed academic participation. Mixed and standards-based initial dispatches should hit the missing-library guard before repair. The exact captured request should then succeed through the **real** service when explicitly supplied the fixture's canonical Core library; that discriminates the context defect from a missing Artifact. Standards-neutral orientations should succeed without Core library. Cancellation must have no write.

This is intentionally **not** a returned-evidence Review or routine Score acceptance. Those remain dedicated Slices 4–5. No installed-wheel acceptance is implied.

## Execution and next gate

1. Run the read-only inventory probe and six baseline parameterized menu tests; record environment and outcome. An unexpected result is a blocker, **not** permission to rewrite the expected observation silently.
2. Slice 1 implements operation-scoped root pinning and structurally verified graph-history/selected-revision authority, conditional Core library acquisition, identity checks, and caller-appropriate error messages. Replace the historical failing-before expectation with an explicit successful menu-path regression and no-write negative tests.
3. Hold commits/pushes/PR creation until the exact guarded candidate and local tests are reviewed. No actual school workspace, physical scan, cross-store publication, or changes to sibling PDS repositories.
