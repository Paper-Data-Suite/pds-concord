# Concord #149 — Slice 0: source-pinned stage/attention inventory and RED witnesses

## Status and provenance (2026-11-16)

- Source: Concord `main` and feature branch `149-stage-aware-attention-readiness`, both `f29d92f56b01fb66b9afe98e246886336c1cb14c` at branch preflight; #148 PR #171 already squash-merged. This document is a source inspection, **not** physical classroom, scanned return, or released-wheel acceptance.
- Core `main` `a0d5e1a50580bbe025f0cad23c7e8524203a52ec`; Suite `main` `f094da07b323a626212d7cbf7d15d95cec83817d`. Concord dependency `pds-core>=0.6.6,<0.7`; Core `main` is not itself an approved installed capability.
- Latest observed published Concord release `v0.3.4` (2026-10-19); #149 work is not an official release.
- Source files reviewed: `concord/workflows/activity_attention.py`, `artifact_collection.py`, `group_plan.py`, `activity_read.py`, `concord/menu_attention.py`, `menu_group_plan.py`, `concord/attention_provider.py`, `readiness_provider.py`; baseline `tests/test_activity_attention_issue67.py`, `test_activity_attention_projection_issue104.py`, `test_activity_attention_read_context_issue104.py`, `test_activity_attention_menu_issue67.py`, `test_attention_provider_issue67.py`, `test_readiness_provider_issue68.py`.
- **Evidence distinctions**: symptom from #138/#139 **reported**; emission paths below **code-path verified**; new strict-xfail unit witnesses become **SYNTHETIC REPRODUCED** only after runner's `--runxfail` exit and failure IDs are observed; current **physical return acceptance unperformed**.

## Stage/source/false-inference matrix

| Stage | Canonical fact and read surface | Actionable now | Not justified by this fact | Planned #149 handling |
| --- | --- | --- | --- | --- |
| Plan — proposal | `context.graph.group_plans`: draft, previewed, approved, cancelled | Unresolved meaningful plan; approve/apply an *actually needed* proposal | Draft means a class with already-applied operational grouping is unprepared | Separate active/needed planning from unused alternative; retain explicit cleanup route and history |
| Plan — operational | Applied plan plus authoritative current Group/Membership/roster state; `group_plan.py` | Investigate contradictory, stale or unknown live placement | Applied historical plan alone proves today's membership/roster is still correct | Positively report current placement when verified; otherwise needs inspection |
| Prepare — packet | `packet_instances.generation_status`: planned, rendering, routes_pending, failed, generated, cancelled | Complete rendering or recover routes/errors | `generated` means printed, distributed, returned | Show generated/ready-to-print only; separate physical unknowns |
| Collect — return | Core PDS2 retained returned-page source/route and assembly lineage; `artifact_collection._assembly_state` | Assemble genuine returned pages or resolve ambiguous selection/integrity | Blank generated artifact/QR target/author proposal proves physical return | Gate returned-work phrasing to authoritative return stage; no fake received evidence |
| Attribute | Current Artifact Author/Subject heads from `_current_authors`/`_current_subjects` | Genuine proposed/disputed identities *when eligible returned evidence exists* | A proposed association on blank packets is actual verified authorship | Gate confirmation attention; retain dispute and supersession history |
| Review | Current `_review_heads`, assembly state, moderation lineage | First review or follow-up after genuinely assembled evidence | Blank packet or fabricated review equates to student work | Preserve existing review/moderation prerequisites and statuses |
| Score | Current review heads and `scoring_orientation`; criterion authority separate | Evidence explicitly ready for teacher Score judgment | Absence of a Score means overdue student performance, or Group score derives individual grade | Preserve optional/deferred and teacher authority; no auto score |
| Share | Verified academic-result registration/publication state; `_share_attention_from_context` | Genuine explicit manifest/publish/supersede/withdrawal inspection | Attention code grants publication or grade-policy authority | Keep explicit Core/Meridian boundary and existing action routing |
| Core/Suite boundary | `ModuleReadinessReport` structural class/workspace; `ModuleAttentionReport` privacy-minimal aggregates | Bounded read-only module owner action | Structural ready means lesson ready; Core Notes/Tasks are Concord attention | Preserve v1 structural readiness and distinguish Module Attention from My Tasks |

## Current actionable native attention codes (exact baseline)

- Plan (4): `concord_plan_prepare`, `concord_plan_unresolved_placements`, `concord_plan_approve`, `concord_plan_apply`.
- Prepare (3): `concord_prepare_materials`, `concord_prepare_routes_pending`, `concord_prepare_recovery`.
- Collect (3): `concord_collect_assembly`, `concord_collect_author_confirmation`, `concord_collect_subject_confirmation`.
- Review (4): `concord_review_first`, `concord_review_attention`, `concord_review_moderation`, `concord_review_post_moderation`.
- Score (1): `concord_score_ready`.
- Share (5): `concord_share_inspect`, `concord_share_withdrawn`, `concord_share_manifest`, `concord_share_publish`, `concord_share_supersede`.

There are **20** codes and 6 stage families. Native `_ATTENTION_DEFINITIONS`, Core-adapter `_ATTENTION_CODE_ORDER` and menu routing must remain congruent. This is neither chronological certainty nor urgency ranking. Counts are affected Artifacts or plans, not students or grades.

## Specific baseline mechanism and test contract

1. `_plan_attention_counts_from_context` counts `draft` before considering the presence of a verified applied operational plan; expected: applied six-Cluster operational state with *unrelated unused draft* does not emit blocking Plan attention. **Two strict-xfail witnesses**, for 29- and 30-student synthetic rosters, in `tests/test_issue149_slice0_attention_witnesses.py`. The supplied simplified synthetic group/roster objects demonstrate the projection error; they do **not** prove real Core roster reconciliation. Slice 1 must add authoritative integrated proof.
2. `_collection_state_from_context` projects proposed/disputed Author and Subject heads regardless of retained returns; `_attention_counts_from_context` then emits `Returned evidence needs ...` codes. **One strict-xfail witness** creates six generated unreturned blank Artifact records, six proposed authors and six proposed subjects, and a mocked `not_ready` assembly outcome. This tests an observed source-path behavior, not a forged Core-retained scan. Slice 2 must add PDS2-backed positive and negative source authority.
3. **Passing controls** retain action for a genuinely needed draft; do not flag only applied/cancelled plans; retain current assembled/disputed/reviewable evidence; generated packets alone are not preparation failures. The observed baseline #67/#104 test suite has expected historical semantics; some tests may require explicit, source-proved reinterpretation during implementation. Never delete assertions just to pass.
4. `tests/test_issue149_slice0_attention_witnesses.py` uses `@pytest.mark.xfail(strict=True)` as a temporary compatibility measure. Runner MUST execute those cases under `--runxfail`, see exactly the expected failures and no other errors, and also run normally to see **3 xfailed**. When implementation fixes a witness, strict XPASS is a failure until the marker is deliberately removed and corresponding tests become green. **A green suite with three XFAILs is not evidence that the defects are fixed.**

## Slices and ownership

- Slice 0: **test/audit only**; no production changes, no publication or release claim. Keep on branch `149-stage-aware-attention-readiness`.
- Slice 1: source-backed applied/operational GroupPlan readiness plus optional residual-draft cleanup through existing actor-reviewed CAS cancellation.
- Slice 2: return/assembly/attribution stage authority and optional/deferred Review/Score/Share, with Core retained-return positive witnesses.
- Slice 3: opened-Activity pre-lesson and all-category read-only views, exact menu routing, Core attention parity and no mutation on refresh.
- Slice 4: consolidated full suite and official Core wheel installed acceptance, PR hosted Linux/Windows CI, human review and merge decision. No release inferred from merge.

**Owner handoffs:** physical returned-file/scan path #151, cross-class copy #150, teacher Score labels #152, broad navigation #153, semantic operation inventory #162, mixed PDFium #170, independent/physical downstream acceptance #155–#160. No Core/Suite changes required for Slice 0.
