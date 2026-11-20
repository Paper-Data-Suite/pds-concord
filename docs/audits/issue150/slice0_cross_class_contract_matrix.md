# Concord #150 — Slice 0: pinned cross-class reuse and teacher-UI contract audit

**Evidence type:** source review + intentional synthetic failing-before test package; **not** an implementation, an installed-wheel acceptance result, actual student transfer, or physical printed/returned-paper qualification. The RED witnesses are deliberately retained as strict XFAILs until the intended teacher-facing behavior is delivered and requalified.

## Pinned starting point (2026-11-17; revalidate before applying or writing code)

| Source | Observed authority | Meaning |
| --- | --- | --- |
| `pds-concord` branch `150-use-lesson-with-another-class` | `59df22e07e7fa4e14677bf75cb0089fc0604f9fa` | Exact source starting point. Identical to `main`; #149 squash merge was completed. |
| `pds-core/main` | `a0d5e1a50580bbe025f0cad23c7e8524203a52ec` | **Source**, not a new official wheel. |
| `pds-paper-data-suite/main` | `f094da07b323a626212d7cbf7d15d95cec83817d` | Source of the merged teacher-home and UX design contract. |
| Concord published artifact | `v0.3.4` | Does **not** contain #149 or #150 source development. |
| Core published artifact | `pds-core 0.6.6` | Concord `pyproject.toml` requires `pds-core>=0.6.6,<0.7`; published 0.6.6 predates newly merged Core teacher header/parser source APIs. |
| Suite published artifact | `v0.1.0` (verify before release) | Suite source teacher home is not evidence of published newer UI components. |

Normative [Concord #150](https://github.com/Paper-Data-Suite/pds-concord/issues/150) is subordinate to the accepted [Suite design v0.2](https://github.com/Paper-Data-Suite/pds-paper-data-suite/blob/main/docs/design/teacher-experience-design-specification.md) §§3–7, 9–12, D-03/D-04/D-05/D-07/D-08 and [Core public teacher-experience contract v1](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/teacher_experience_contract_v1.md) with [ADR 0005](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/decisions/0005-adopt-versioned-teacher-experience-public-interfaces.md). Qualifying D1 source does not establish installed D2/D3 or classroom D4.

## Source callsites and ownership inventory

| Normal teacher step | Current code/service | Qualified baseline / new work required |
| --- | --- | --- |
| Choose **Start from another Activity** | `concord/menu_guided_activity.py::launch_guided_activity_menu`, `_create_from_activity` | Present but not yet named **Use this lesson with another class**. Slice 1 should preserve a single copy controller and introduce clear labeling/handoff, not a second copy engine. |
| Validate copy / show review | `concord/workflows/activity_copy.py::prepare_activity_copy`, `concord/menu_guided_activity.py::_create_from_activity` | Zero-write source/target copy preview and `review_digest` exist. Expand teacher preview to distinguish saved *definitions* selected later from previous *operations/evidence* that cannot be carried. |
| Create target Activity + first Session | `concord/workflows/activity_copy.py::copy_activity` | Exact reviewed create-only target; one fresh `draft` Activity and `planned` Session. No source Sessions, Groups, plan, student data, Scores, Artifacts or publications. Preserve this service contract. |
| After creation and general resume | `concord/menu_guided_activity.py::_offer_after_creation`, `launch_guided_setup_for_activity`; `concord/workflows/guided_activity_setup.py::inspect_guided_activity_setup` | Durable copy is acknowledged, general **Continue setup now** works. Missing target-stage-specific copy flow and return-from-partial stage receipts. Derive from canonical state; no separate durable wizard cursor. |
| Target Core roster / grouping | `concord/menu_group_plan.py`, `concord/workflows/class_group_arrangements.py::prepare_reuse_grouping`, `pds_core` roster authority | Saved grouping is **target class, school year, owner scoped**, with exact roster reconciliation and no source-class reuse. Source group's 29/30 memberships must never copy. Optional person-free six-Cluster shape only after explicit separate review. |
| Saved materials | `concord/menu_guided_activity.py::_launch_materials`, `concord/menu_packet_generation.py` | Reuse exact selected saved Packet/Template *definition*, generate independent target Packet Instances/Pages/PDS2 routes. No source PDFs, QR routes, scan references or return claims. |
| Saved assessment | `concord/menu_scoring.py`, `concord/workflows/reusable_presets.py::prepare_scoring_setup`, `materialize_scoring_setup` | Select exact active typed Scale/Criterion preset revision, validate target Standards/targets, materialize new target IDs and select appropriately. Never copy operational Score or grade. |
| Read-only teacher status | `concord/menu_activity.py` R/D, `concord/workflows/activity_lesson_readiness.py`, `activity_attention.py` | #149 source gate. Keep distinct generated vs actual returned lineage, optional work, operational applied plan and read-only zero-write behavior. |
| Core/Suite screen and navigation | `concord/menu_ui.py`, `concord/menu_navigation.py`, `concord/menu_context.py`; Core `teacher_experience/1`; Suite design v0.2 | Existing Concord prints plain text; shared green header is **not** present in official Core 0.6.6. #150 screens must be compatible with the accepted contract, but cannot import unpublished public Core symbols unconditionally. #153 owns producer-wide adoption. No competing Suite Teacher Home, roster admin or Notes menu. |

## Canonical state/checkpoint matrix for Slice 1 onward

| Stage | Before write/read-only decision | Durable success receipt and authoritative restart | No-write / conflict / partial meaning |
| --- | --- | --- | --- |
| 0 Source and target selection | Existing source + target Core class, current Standards and target vacancy | None yet | Cancel/no source/target/stale Standards: `NO_CHANGE`; no invented target. |
| 1 Reviewed Activity copy | #63 allowlist, privacy fallback, unique target and first planned Session, exact review digest | Fresh target class-qualified work and first Session; reread current snapshot; resume with target selection | Create-only collision, new target chosen only explicitly; never auto-overwrite or silently adopt by title. |
| 2 Target GroupPlan | Current target roster IDs, actual target GroupPlans/Groups, optional target-only arrangement | New reviewed target plan then approved/applied canonical Group/Membership with fresh IDs and current roster verification | `Decide later` is optional; stale/replaced roster prompts review; source membership never transferred. |
| 3 Target Packet/route generation | Selected current reusable Packet/Template version, current target groups, session, bindings | Fresh target Packet Instances, artifact pages/route registrations with status verified independently; #149 before-class readable | Generated is not distributed or returned. Partial routes/generation are **not** a rollback; inspect before retry. |
| 4 Saved assessment / assignments | Exact typed reusable preset revision, target scoring orientation/Standards, target assignees | Fresh target Scales/Criteria/selected set, optional target Role/Responsibility assignments, independent receipts | No Scores/Grades/publication; choosing later is not the same as a blocking failure; never duplicate during resume. |
| 5 Before-class review / finish | #149 single read-context, canonical current graphs, current GroupPlan/packet/return stages | **No writes** from inspection; prior verified commits remain durable | `B/M/Q`, EOF and process exit must not erase prior commits or fabricate physical distribution. |

**Crash windows:** between service success and receipt, across PDS2 registration, across target preset materialization and target selection, or between a completed GroupPlan and next menu render. Each window requires a reconciliation test that inspects exact canonical target state before any repeat mutation; there is no cross-store transaction and no legitimate default “retry everything.”

## User-visible screen grammar (must survive #150)

- **Header:** `Concord` application identity, current task title, and optional *validated* class/Activity context. Green application line only via qualified Core `terminal.header.v1` and supported ANSI; official Core 0.6.6 requires safe plain-text fallback. Never embed ad hoc ANSI/SGR or print private paths/student details into shared context.
- **Navigation:** Core B/M/Q semantics and Concord H; no stolen N, no global intercept. Reserve exact `:notes` for future qualified interactive menu-choice prompts only, never `COPY` or other confirmations, input values, file paths, pauses. Actual Notes records/menu cannot be inferred from the parser token. Concord owns its own navigation; Suite foreground child launch does not guarantee nested return.
- **Teacher choices:** **Orient → Choose → Prepare → Review → Confirm → Commit → Report → Continue**, one meaningful authorization per consequential decision. Existing `clear_screen()` and paginated selectors remain the default, with readable no-color output. Default labels are Clusters, saved Packet, saved rubric and target class rather than lineage hashes.
- **Technical details:** opaque IDs, revisions, hashes, source/target digest and error diagnostics are available deliberately, never required as routine teacher input. Validate class/work/roster context again after a supported Core shared menu return; never create Concord-owned roster administration.
- **Receipt:** explain *what was saved*, *what is not saved*, and *what action is safe next*. `Finish for Now` preserves only confirmed writes. A canceled, conflicting, partial or indeterminate return cannot truthfully claim full lesson preparation.

## Slice 0 tests: expected results and retirement plan

- `tests/test_issue150_slice0_copy_controls.py`: four passing source-contract guards for the #63 safe copy, existing guided path, class-scoped saved arrangement and Core navigation.
- `tests/test_issue150_slice0_reuse_witnesses.py`: one existing fixture control plus **three intentional strict XFAILs** to show the **missing** exact named cross-class menu choice, incomplete saved-definition versus returned-evidence preview, and generic post-copy screen lacking target-specific next-stage choices. `pytest --runxfail` must reproduce **exactly these three failing node IDs** on the pinned starting commit. The tests record *teacher-visible gaps*, not a claim that current services copy student data.
- **Slice 1** replaces/retargets the three witnesses to the eventual chosen UI implementation and retires their strict XFAIL markers, preserving all positive #63/#65 guards. Do not remove witnesses simply because the menu changed or skip red reproduction.
- Slice 2–5 add target Groups, saved Packet route, Scale/Criterion, interruption, privacy and Core/Suite UX tests. No live source profile, personal student data or real scan bytes are used.

## Qualification discipline

Slice 0 runs focused #63/#65 and its new controls, Ruff, docs check and authenticated installed Core version. Never run an unnecessary full repository test in an audit-only slice. The runner checks the exact feature branch, `main` source head, remote origin, clean tree, archive inventory and SHA-256 before creating **only** audit/test files; it stages no production modules. It commits/pushes only after focused green controls and *exact* RED witnesses. A failed guard leaves changes to inspect; no automatic `git reset --hard` or destructive cleanup.

After Slice 6, independently qualify source, official installed Core, optional distinct Core source candidate UI, packaged Concord, Windows/Linux hosted CI, and **physical** teacher/scan journeys. No version bump, release tag or cross-repository publish is implied by a source-only qualification.
