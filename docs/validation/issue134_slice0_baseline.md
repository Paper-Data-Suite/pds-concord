# Concord #134 — Slice 0: frozen baseline and teacher-surface audit

**Status:** Pre-implementation baseline. No Concord runtime behavior changes in this slice.

**Suggested working branch:** `134-reliable-long-path-opening-and-teacher-artifact-navigation`

**Source baseline (reviewed `main`, as of October 14–15, 2026):** `65823415f03ab1d5209ad62d48859c02a33fb8a0`

**Concord source package:** `0.3.2`; declared Core requirement: `pds-core>=0.6.5,<0.7`

**Qualified target Core release:** [v0.6.6](https://github.com/Paper-Data-Suite/pds-core/releases/tag/v0.6.6), source `35af5d0642e84a625cd143285c4ef6de98dbcca4`; official wheel `pds_core-0.6.6-py3-none-any.whl` SHA-256 `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`. The target wheel has been published and checked independently in Core's release workflow. **This Concord slice has not yet installed or physically qualified it.**

## 1. Purpose, boundaries, and source evidence

The [amended coordinating issue #134](https://github.com/Paper-Data-Suite/pds-concord/issues/134) now covers **all ordinary teacher-facing identity and chronology presentations**, not only the original `Collect → Open returned work` picker. The assessment below is grounded in current repository source, not a claim that every exposed identifier is a defect. The accompanying `issue134_teacher_surface_inventory.json` records **every matching source line in all `concord/menu_*.py` modules and `concord/menu.py`**, with relative path, line, enclosing function, code-only source excerpt, and provisional classification. It deliberately does not read the teacher's OneDrive workspace, rosters, student work, or private records.

The JSON classifications are **triage**, not permission to hide every occurrence or a claim of completed manual review of every case. Each future behavior-changing slice must update the audited candidate list and review its affected cases. Preserve advanced diagnostics and machine-facing identifiers where technically required, but avoid IDs, route numbers, hashes, manifest locations, and internal revisions as ordinary primary navigation.

## 2. Confirmed ordinary teacher-path defects and contrasts

| Journey | Code inspected | Current presentation / issue | Slice responsibility |
| --- | --- | --- | --- |
| Collect / Open / Assemble | `concord/menu_artifact.py`: `_choose_artifact`, `_assembly_selections`, `_assemble`, `open_returned_work` | Main picker displays `artifact_instance_id` and return counts. Duplicate page occurrences display source scan and ScanReference IDs, not dates. Assembly confirmation/result displays Artifact and assembly IDs. Returned-work success claims PDF **opened**, though only OS dispatch is known. | 1, 2, 4 |
| Page and attribution | `concord/menu_artifact.py`: `_list_pages`, `_prepare`, `_render`, author/subject and Review/Moderation menus | Routine page list and detail show page/route IDs; preparatory advanced authoring requests raw IDs. Author/subject/review history can surface machine identities. | 3; explicitly classify whether authoring fields are advanced-only |
| Review next, record, revisions | `concord/menu_artifact.py`: `_review_next`, `_show_review_detail`, `_review_label` | Review-next exceptions identify Artifact by ID; Review history is ID-first. Current Review is a supersession relation, not simply newest occurrence or newest PDF. | 1–3 |
| Score | `concord/menu_scoring.py`: `_choose_target`, `_score_label`, `_browse_scores`, `_score_confirmation_lines`, `_revise_score` | Artifact Score targets and Score history are ID-driven; Score confirmation shows technical target/criterion/scale IDs. Canonical current head and exact evidence basis require independent verification. | 1–3 |
| Packet generation, ready materials | `concord/menu_packet_generation.py`: `_teacher_instance_labels`, `_choose_generation`, `_list_instances`, `_inspect_instance` | Some rendered-output choices **already** resolve authoritative student/group labels; preserve this. Generation picker omits existing `generation_date`/`created_at`, so multiple generations of the same Packet/Session can be visually indistinguishable. Other advanced screens display generation, instance, output and digest. | 3–4 |
| Scan routing | `concord/menu_scan.py`: `_choose_route_sources`, `_show_scan_batch_result`, `_routing_technical_detail_lines` | Inbox is filename-sorted, **not** chronological. Routing failure Technical Details is a deliberate, existing separation worth reusing. Do not interpret source filename or filesystem mtime as physical capture timestamp. | 2–3 |
| Activity, Group and Session | `concord/menu_activity.py`, `menu_group.py`, `menu_session.py` | Activity title is usually shown; Group labels and Session labels are available, but some normal results/summaries use raw IDs and revisions. A class ID is not necessarily a teacher-readable class name. | 1–3 |
| Templates, Packets, presets | `concord/menu_template.py`, `menu_packet.py`, `menu_presets.py` | Version names and revision numbers coexist with head/version IDs; template preview surfaces rendering SHA-256. **Head, active/current, and most recently authored can differ.** | 3 |
| Publication and Share | `concord/menu_publication.py` | Current teacher confirmation/preview displays manifest path and SHA, record set and publication identifiers. Publication/current selectability must not be inferred from creation order alone. | 3 |
| Other openers and error banners | `concord/workflows/artifact_evidence_opening.py`, Packet output, Activity reports, student feedback | `open_local_path` verifies launch request but cannot assert the viewer actually displayed the file. Every opening action requires exact evidence integrity and truthful messaging. | 4 |

**Existing good patterns to retain:** `menu_packet_generation._teacher_instance_labels` resolves Core-student and Group labels and avoids raw ID fallback; `menu_scan._routing_technical_detail_lines` keeps technical troubleshooting separate from normal routing choices; `workflows/packet_generation.list_packet_generations` exposes both date fields and loads a shared graph context; `menu_artifact._open_selected_returned_work` keeps explicit already-selected Artifact identity for the immediate action. These do not eliminate the broader problems.

## 3. Exact evidence chronology and immutable custody

| Object | Actual persisted source | May truthfully display | Must **not** claim |
| --- | --- | --- | --- |
| One routed occurrence | `models/artifacts.py` `ScanReference.created_provenance.timestamp`; generated during `workflows/artifact_page.handle_concord_route` | **Routed into Concord at** recorded timestamp. | Physical scanner capture time, or that lexical ScanReference ID order represents chronology. |
| Repeat dispatch of same retained source/page/route | `handle_concord_route` returns `replayed=True` for existing matching occurrence | Existing occurrence reused; no additional recorded occurrence. | Newly scanned/newly returned solely because routing was retried. |
| Two different physical returns for same logical page | Multiple immutable `ScanReference` records | Two selectable alternatives, each with its own routing time; tie or missing chronology explicitly reported. | Newest must replace earlier, or one occurrence is automatically correct. |
| Assembled PDF | `workflows/artifact_assembly.py` immutable `manifest.json` creation provenance; identity is hash of exact chosen `AssemblyPageLineage`, verified against current records | **Assembly created at** manifest timestamp; exact selected source occurrences; reused exact assembly where `reused=True`. | The most recently created assembly is automatically the current reviewed/scored version. |
| One current Review | `models/review.py` `ArtifactReview.reviewed_at`, `supersedes_artifact_review_id` | Reviewed at; current or historical as explicitly represented by Review lineage. | Review alone proves the exact selected assembly. `ArtifactReview` has Artifact identity but **no direct `assembly_id` or per-page scan-choice field**. |
| Score and Score evidence | `models/scoring.py` `ScoreRecord.scored_at`, `supersedes_score_record_id`, `ScoreEvidenceLink.evidence_reference` / optional locator | Scored/revised at; exact current historical Score lineage, linked evidence when demonstrably precise. | All historical Score links identify the assembled PDF; available fields need per-record inspection and prospective binding design. |
| Packet generation | `workflows/packet_generation.py` `PacketGenerationSummary.generation_date` and `created_at` | **Packet intended for** date vs **generation created at** timestamp; statuses and counts. | Source creation time is session date, or chronological newest is canonically active. |
| Template/Packet/version and publication | Current/head/supersession or Core publication state | Current and historical as defined by canonical lifecycle. | Last ID, last filename, largest revision string or newest clock defines authority. |

**Critical current behavior:** `workflows/artifact.list_artifact_scan_occurrences` sorts occurrences by `scan_reference_id`; `workflows/artifact_assembly._select_lineage` also sorts candidates by ScanReference ID. That order is deterministic but **not chronological**. `assemble_returned_artifact` reuses a verified assembly of the same exact lineage and creates a separate immutable PDF when the teacher selects different physical page evidence. `resolve_returned_artifact_assembly` fails closed if the requested exact lineage has no matching verified existing assembly. No “latest assembly wins” pointer has been established. Slice 2 must introduce a safe read-only history projection and exact selection; avoid replacing any canonical immutable record merely to improve presentation.

**Potential material design gap for Slice 2:** Review is attached to Artifact identity rather than a persisted assembly selection. A Score can link evidence references but that does not guarantee exact historical ScanReference/assembly provenance. The user interface must say **“Exact reviewed/scored scan version not recorded”** where authoritative evidence is insufficient. Slice 2 should propose minimal *prospective* immutable binding and qualify consumer compatibility if it is needed. Do not retroactively manufacture historical lineage or couple scoring correctness to a vague newest timestamp.

## 4. Source-only automated inventory contract

Run:

```powershell
python scripts/audit_issue134_teacher_surfaces.py --root . --check
```

The JSON file is a **baseline artifact**, not runtime config. It is intentionally sensitive to changes in menu source lines, so it must be deliberately regenerated and reviewed as later slices alter those files, then included in the relevant PR rather than weakened or silently skipped. Findings are only **code excerpts**, never roster/evidence contents or local absolute paths. Category labels (`teacher_display_candidate`, `teacher_input_candidate`, `advanced_technical_candidate`, `internal_reference_review`) are provisional and require human disposition during implementation. The accompanying table above records high-priority reviewed findings and their future owners.

## 5. Performance, test, and release qualification policy

- **Known structure:** `workflows/artifact.list_artifacts` loads a current graph once. `show_artifact` reloads the graph per explicit detail request. Naively calling `show_artifact` for each picker row would introduce expensive N+1 graph work; Slice 1 must build/index its label projection from one consistent graph. Existing `PacketGenerationSummary` uses a shared read context for many generations; preserve that pattern.
- **Performance acceptance target:** at 6 Artifacts and at a larger synthetic class-scale workload (e.g., 100+ Artifacts, duplicate names and scan alternatives), instrument actual graph loads, elapsed teacher-picker time, and snapshot identity. Assert graph loads scale by screen/action, not list length; do not introduce one load per item. **No numeric runtime baseline is claimed in this static slice**: creating one from live classroom/OneDrive data would be inappropriate, and the current code's complete synthetic timing fixture was not available from the remote source review. Establish quantitative timings on frozen synthetic fixture in Slice 1, then compare subsequent slices against that.
- **Focused gate for Slice 0:** audit JSON compare; `tests/test_issue134_slice0_audit.py`; Ruff for two added Python files; MyPy for added script; `git diff --check`. **Do not run the 1,000+ test full suite dirty and immediately repeat it clean.** Existing exact-wheel installed tests and physical Windows probes belong to Slice 4/5 qualification, not this read-only baseline.
- **Read-only contract:** no changes to `concord/`, dependencies, workflow outputs, canonical scan stores, historical release fixtures, student records, or published tags in Slice 0. After a source-only PR is clean and CI passes, later slices can implement presentation, chronology, physical viewer integration, and version qualification in that order.

## 6. Handoff to Slice 1

Required first design outcome: one immutable, snapshot-scoped teacher-label projection with Activity/class, Group, Session, authorized participant, status and fallback information. It must be reused across Collect, Review, Score and shortcut entry points, with exact ID selection retained internally, and must not build by repeatedly calling `show_artifact`. Slice 2 separately owns occurrence/assembly chronology and Review/Score exact-version binding decisions. The full source inventory must be reclassified at the point each affected UI site is touched; unsafe routine displays cannot be waved through merely because an unrelated primary picker is now readable.
