# Concord #151 — Slice 0: collection authority, RED witnesses and checkpoint matrix

**Status:** source-audited candidate, subject to native Windows qualification; no production changes in this slice.
**Pin date:** 2026-11-20.
**Concord feature branch:** `151-authoritative-collect-returned-evidence`, initially identical to `main` at `8443e9093e8f0ca14fc4c0c0abc20e0ede7eb0d5` (squash merge of #150 / PR #173).
**Core main:** `a0d5e1a50580bbe025f0cad23c7e8524203a52ec`; **Suite main:** `f094da07b323a626212d7cbf7d15d95cec83817d`.
**Published package inputs inspected:** Concord `v0.3.4`, Core `v0.6.6`, Suite `v0.1.0`; **do not conflate source with wheels**. Concord declares `pds-core>=0.6.6,<0.7`, Python `>=3.11`, and existing `pypdfium2` / `zxing-cpp` scan support. Refresh pins before every implementation/release gate.

## 1. Authority and non-goals

- **Core**: selected workspace; school-year/class/roster/Standards authority; PDS2 route parsing, registration and dispatch; immutable retained-source custody; safe local-file viewer handoff (`pds_core.local_open`). Keep its existing workspace and file-sync configuration. Do not introduce a second roster, storage root, route registry or local viewer implementation.
- **Concord**: Activity/Session/Group/Artifact/ArtifactPage/ScanReference graph, returned assembly and version manifests, Author/Subject associations, Reviews/Moderation and Scores. Concord's UI owns the educator's Collect workflow; canonical writes still use current service owners and exact snapshots.
- **Suite**: teacher home and launcher; shared teacher-experience design; not a scan or academic-evidence writer. The Suite UI must not imply it executed/verified a Concord operation merely because the teacher launched it.
- **Core Notes roadmap changed on 2026-11-18**: #238 external OS-user-local store and #243 separate private portability were superseded. #239 now owns small workspace-native `.pds/notes/` records inside the *existing selected PDS workspace*; #240 owns Notes UI/CLI and #244 the one consolidated release. Old sections of Core contract/ADR and Suite v0.2 still describe the rejected OS-local model; consult newer issues as the active storage decision. **No Notes subsystem belongs in #151.** No `:notes` runtime claim on official Core 0.6.6. Broad Concord UI adoption is #153.
- **Physical reality**: generated/prepared ≠ printed/distributed ≠ retained ≠ routed ≠ assembled ≠ attributed ≠ reviewed ≠ scored. Neither a PDF viewer request nor a preparatory QR decode is proof of physical paper return. Synthetic tests are not physical qualification.

## 2. Exact current owner-path inventory (source verified)

| Teacher route / dependency | Existing implementation and observed semantics | Slice decision |
| --- | --- | --- |
| Activity → Collect | `menu_activity.launch_collect_menu` → `menu_artifact.launch_collect_work_menu`. Existing ordinary choices: View returned work; Assemble; Review attribution; Advanced attribution; Open; Verified versions. | **Gap:** Scan Routing is a separate `menu_scan.launch_scan_routing_menu`, not discoverable directly from Collect. Preserve its current owner and avoid inventing a new parser. |
| Scan intake | `routing.scan_intake.route_scan_sources`: source extension/symlink checks, Core `retain_source_scan`, QR extraction and PDS2 parse, registry dispatch, page-level failed-route metadata. | Introduce a **navigation handoff** after a zero-write stage review; do not reimplement retention, route decoding or reroute by filename/title. A retained but unrouted page is not a returned Artifact page. |
| Collection state | `workflows.artifact_collection.inspect_artifact_collection_state` and `_has_retained_return_reference`: distinguish missing/partial/ready/ambiguous/assembled/recovery; partial return requires canonical `ScanReference` on exact return-expected page and matching Activity/route. | Reuse logic for one coherent read-only teacher stage summary; ambiguous/corrupt references fail closed; no second status store. This is existing #149 behavior, **not** a new Slice 0 defect. |
| Teacher Artifact selection | `workflows.teacher_artifact_choices.list_teacher_artifact_choices` builds labels from one graph/revision; `menu_artifact._choose_artifact_choice` carries exact selection. | Preserve #134 labels and exact identity; do not regress to opaque IDs as primary choices. |
| Assembly | `workflows.artifact_assembly._select_lineage`, `assemble_returned_artifact`, `resolve_returned_artifact_assembly`, `returned_assembly_versions.list_verified_assembly_versions`. Retained-source hashes, exact occurrence IDs, manifest/PDF hashes and snapshot are independently validated. | Reuse; do not rewrite original source evidence or choose the newest scan by default. Report exact existing assembly reuse distinctly from new assembly. |
| Returned opening | `workflows.artifact_evidence_opening.open_returned_artifact_evidence` resolves and verifies before delegating to Core's `open_local_path`; receipt says **viewer requested**, not display confirmed. | Keep #134 Windows short alias/same-file/junction cleanup; real returned deep-path PDF must be physically viewed, distinct from successful prepared Packet opening. |
| Attribution review projection | `workflows.artifact_attribution_review.inspect_artifact_attribution_review` uses current author/subject association heads and semantic/duplicate validators to build confirmation candidates. It does **not independently call** the #149 returned-evidence gate. | **Candidate gap to prove:** pre-return paper relationships can be offered as candidates even without any `ScanReference`. Present explicit blocked reason in ordinary Collect while retaining safe pre-return proposals. |
| Attribution writer | `workflows.artifact_attribution.batch_confirm_artifact_attribution` checks revision, current proposed IDs, semantic/duplicate validity and commits statuses atomically. It does **not separately check physical routed-return eligibility** before commit. | **Writer gap to prove:** no premature confirmation for return-expected paper even through direct CLI/service callers. Do not enforce a blanket no-scan rule. Preserve explicit #106 non-return-expected observational associations. |
| Review and Score | `menu_artifact.launch_review_work_menu`; `artifact_review`; `menu_scoring`; #152 owns scoring label friction. | No automatic Review, Moderation, Score, Grade or publication from Collect/open/routing. Handoff to Review uses fresh context. |
| Attention and readiness | `activity_attention`, `activity_lesson_readiness` (#149). | Retain read-only truth about partial evidence, optional work and no false returned-work tasks. No new durable task record, Core Notes entry, or Suite attention rewrite. |

## 3. Checkpoint model: what is and is not established

| Stage and evidence | Read-only classification | Authorized next operation | Write ownership |
| --- | --- | --- | --- |
| Packet generated; no reported physical delivery | `prepared`, distribution **unknown/not tracked** | Teacher prints/distributes outside PDS; route returned paper later | Existing Concord Packet/Artifact owner; physical event not inferred |
| Scan source selected but not retained | `not received in PDS` | Explicit Core retention and dispatch via Concord Scan Routing | Core retained-source owner |
| Source retained, no valid route | `retained; routing requires review` | Existing PDS2 failure-review/resolution, never guessed target | Core PDS2 + Concord route adapter |
| 1 of 2 required pages correctly routed | `partially returned` | Await/review other pages; don't assemble or confirm returned authorship | Core route; Concord ScanReference |
| All pages returned, exact occurrence unambiguous | `ready to assemble` | One reviewed assembly action | Concord Artifact assembly |
| Duplicate or conflicting retained occurrence | `selection required` | Teacher chooses exact occurrence; chronology alone is not authority | Concord selection over Core retained sources |
| PDF and manifest verified for exact lineage | `assembled; viewer display unknown` | Request viewer, review association, continue to Review | Concord assembly; Core viewer handoff |
| Eligible proposed Author/Subject with supported returned evidence | `awaiting attribution decision` | Explicit reviewed confirmation after fresh snapshot and exact association validity | Concord attribution writer |
| Non-return-expected observation with valid proposed association | `not a returned-paper collection stage` | Existing explicit attribution confirmation remains valid (#106) | Concord attribution writer |
| Reviewed/Moderated/Scored | Only each separately recorded canonical judgment | Authorized separate action, never implicit | Concord Review/Moderation/Score; Meridian grading separate |

**No fabricated all-or-nothing transaction.** Retention, routing, assembly, attribution, and review can commit independently. A failure after one successful stage means the earlier evidence remains durable; re-read authoritative state before retrying. For an indeterminate commit, never blindly replay a potentially duplicating write.

## 4. Failing-before witness IDs and intended lifecycle

`tests/test_issue151_slice0_collection_witnesses.py` is a **nonmutating** isolated menu/service projection harness, not an installed-wheel/physical demonstration.

1. `test_return_expected_artifact_without_routed_evidence_is_not_confirmable` (**strict xfail before fix**): semantic-valid current proposed Author for an unreturned paper Artifact must not be selectable as a straightforward confirmation candidate.
2. `test_writer_rejects_pre_return_author_confirmation_before_any_commit` (**strict xfail before fix**): direct owner service must refuse such a request before invoking its canonical batch commit.
3. `test_collect_offers_scan_routing_from_the_current_activity` (**strict xfail before fix**): ordinary teacher Collect must expose a Scan Routing entry. Use the existing module's action; **do not** intercept arbitrary free-text/confirmation prompts.
4. `test_non_return_expected_observation_keeps_existing_confirmation_contract` (**positive regression**): an observational Artifact whose pages have `return_expected=False` may offer a semantic-valid candidate without a scan, consistent with #106.

**Scope limitation:** these tests use synthetic in-memory graph doubles with controlled semantic-validation substitutes to isolate the missing gate, and are **not** an end-to-end Core physical return or all-versions type/graph acceptance. Slice 1/4 must add real persisted synthetic `return_expected=True` / PDS2 route fixtures, both Author and Subject cases, and adversarial direct API/CLI witnesses. The existing #106 twenty-Artifact batch acceptance is a compatibility dependency and may require a narrowly scoped change only if the new rule regresses it.

**Qualification contract:** first run these tests with `--runxfail` and require only the three named RED witnesses to fail (not collection errors); next run normally and require `3 xfailed, 1 passed`. After a repair, remove each corresponding `xfail(strict=True)` only when its fully exercised contract passes. A surprise `XPASS(strict)` is a **release-blocking signal** to update the test, not an excuse to suppress it.

## 5. Core/Suite teacher-experience compatibility gate

- Preserve recognizable `Concord` identity and task/context labels, `B/M/Q/H`, `NO_COLOR`/non-ANSI readability and semantic terms **returned work**, **Cluster**, **Session**, **Author**, **Subject**, **review**, **save**. Do not advertise unqualified Core UI primitives as already shipped.
- `:notes` is reserved for exact menu-choice prompts *only after* the #153 collision audit and released Core service/menu capabilities. `terminal.notes_command.v1` is only a parser, not Notes persistence. Never intercept data-entry, path, search, free-text or confirmation fields; retain Quillan's `N`/`W` meanings.
- When a qualified in-process shared Core administration menu eventually returns, Concord must revalidate the selected workspace/class/roster/Activity/Student/Standards snapshot before any collection write. No guessed context based on display titles.
- Shared teacher-experience vocabulary (Suite §4–7) applies today as a **design target** even when Core official 0.6.6 lacks the newer source-only interface. #153 owns broad header/command adoption. #151 adds no Suite or Core dependency, schema or store.
- Corrected Notes storage: use Core's selected workspace, not a second private root, OS-user SID registry, cross-root transaction or separate sync/backup engine. Do not misinterpret stale Core v1 contract §4.5 or Suite v0.2 §8.4 as currently approved implementation authority. The active decision is Core #235/#239/#240/#244, pending formal design-doc reconciliation.

## 6. Test and evidence policy for subsequent slices

- Retain current `#134` viewer, `#149` collection/attention, `#150` target-only copy/restart, `#106` batch attribution, `#136` Core class/Standards and `#65` revision/receipt tests.
- Confirm exact snapshot/currentness and source hash; no anonymous or cross-class student leakage; preserve original scanned bytes; reject traversal/reparse/symlink escapes and stale OneDrive conflict copies without automatic overwrites.
- Zero-write preview/back, exception, missing workspace and stale selection must not create Activity, Packet, Note, ScanReference, assembled PDF, association, Review or Score.
- Use **focused** Windows native pytest/Ruff/docs gates per slice. Reserve complete `scripts/validate_repository.py --core-wheel <official Core wheel>` for integrated Slice 6 (plus exceptional risk-based needs). CI must pass on exact PR head before merge decision.
- Separate **source tested**, **candidate installed**, **official Core-wheel integrated**, **real native viewer displayed**, and **real physically printed/scanned/returned** evidence. Never upgrade an evidence label by inference.

## 7. Next bounded implementation decision

Slice 1 should add a single authoritative read-only collection projection for the teacher (Activity + Session/Cluster labels + returned page counts + assembly/attribution status), reuse #149 `ActivityReadContext` where safe, and preserve existing #134 teacher choices. Before choosing a new UI layout, first prove the three Slice 0 RED witnesses, update the issue audit if current native results differ, and then advance along the ticket's agreed ordered slices. **No new writer, Notes store, wizard cursor or Core/Suite source edit in Slice 0.**
