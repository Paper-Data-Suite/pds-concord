# Concord #151 Slice 1 — Authoritative Collect overview

**Baseline:** #151 branch `1c05011` (Slice 0 accepted), published Core 0.6.6. This is a source candidate pending native Windows qualification, not a release assertion.

## Teacher behavior delivered

From one Activity's **Collect** menu, choose **S. Collection status (read-only)**. The existing numbered actions are unchanged. A paginated teacher choice displays Cluster/Session, routed return counts and status; selecting one displays the exact progress, outstanding attribution decisions, and a safe next action. The ordinary display does not expose raw Artifact IDs, ScanReference IDs, source file paths or hashes. Printing and classroom distribution are expressly **not tracked**; no scan is inferred from page-generation status.

The selection is read-only, uses one authoritative Concord Activity snapshot and a single Core class check, and rejects stale expected snapshot revisions. It uses the established `teacher_artifact_choices` grouping/session labels and `artifact_collection._assembly_state` for exact ready/ambiguous/assembled/recovery status. It indexes canonical `ScanReference` relationships once and counts distinct return-expected Artifact Pages, not mere repeated occurrences or `page_status="returned"`. Contradictory routes and missing canonical page identities fail closed.

A non-return-expected observational Artifact displays **No paper return required** and does not require a physical scan. No confirmation or Score is granted by this display. The Slice 0 strict xfails remain intentionally unresolved: the attribution review candidate gate, the batch writer gate, and direct Scan Routing handoff are owned by later slices.

## Stage interpretation

| Display state | Canonical basis | Teacher next step |
| --- | --- | --- |
| No paper return required | Zero return-expected Artifact Pages | Continue separate observational workflow |
| Awaiting returned pages | At least one required page, zero matching routed ScanReferences | Route returned scans when paper arrives |
| Partially returned | Some but not all required pages have matching route references | Route or resolve remaining pages |
| Ready to assemble | All required pages routed, existing authoritative assembly inspector reports `ready` | Deliberately Assemble returned work |
| Choose exact scanned occurrences | All required pages routed, authoritative assembly inspector reports `selection_required` | Choose exact occurrence, not automatically latest |
| Verified assembly available | Inspector verified current exact assembly manifest/PDF (`assembled`) | Open evidence, then make any explicit Review decision |
| Evidence needs inspection | Complete route references but inspector reports recovery/inconsistent readiness | Existing recovery tools; never auto-repair |

Routing reference counts do **not** prove the original source file remains byte-readable. The existing assembly and opening services retain the stronger file/hash/manifest verification responsibility. The projection does not create evidence, rebuild an assembly or mark a scan viewed.

## Boundary and contract rationale

- **Core** is the custody and routing owner. This slice does not change Core's PDS2 or retained-source API, create a workspace, write Notes, or introduce external scan storage.
- **Concord** owns Activity graph projection. Internal IDs remain available in service results for exact selection and technical diagnostics; teacher labels preserve missing Group/Session fallbacks and disambiguate repeated work without claiming chronological order.
- **Suite** remains launcher/home owner. The collection menu retains Concord's current `B/M/Q/H` semantics, class/Activity context, and independent consumer compatibility with installed Core 0.6.6. This slice does not activate source-only Core `:notes` or shared headers; general adoption is #153.
- **Corrected Notes roadmap:** Core #238/#243 OS-local storage and private portability were superseded. Workspace-native `.pds/notes/` records under Core #239, menu/CLI #240 and consolidated release #244 belong entirely outside #151.
- No academic write: no attribution confirmation, Review, Moderation, Score, Grade, roster mutation, publication, or implicit paper-distribution record.

## Negative and compatibility evidence

`tests/test_issue151_slice1_collection_overview.py` covers no-scan status despite generated pages, partial scans with multiple occurrences, each complete assembly stage, non-return observations, multiple indistinguishable Cluster/Session Artifacts, stale revision, corrupt route, missing page, empty Activity and the synthetic menu round trip. The source suite remains isolated from real school files. Keep #149/#134/#106 tests and the three documented Slice 0 strict xfails in focused qualification.

A service projection test cannot qualify an actual Windows viewer opening, source-file integrity, device paper handling, or `:notes` adoption. These remain separate later tickets/slices and physical acceptance gates. The final installed Core/Concord release tests and cross-platform CI belong to Slice 6.

## Qualification and handoff

- Run one controlled native Windows qualification via the guarded runner, checking exact branch/head/remote, source ZIP hash, no preexisting edits, `git apply --check`, syntax, Ruff, focused pytest and documentation validation.
- A successful candidate passes existing Slice 0 expected `3 xfailed` plus all Slice 1 tests. Unexpected XPASS or an unrelated old regression must stop commit/push.
- On passing gates, commit and push only the new module, test module, this audit, and the narrow `menu_artifact.py` patch. Do not touch version tags, CHANGELOG release entries, Core, Suite or real workspace data.
- Next: Slice 2 — existing Core PDS2 Scan Routing handoff from Collect. No fresh scan dispatch implementation.
