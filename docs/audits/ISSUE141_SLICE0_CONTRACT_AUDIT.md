# Concord #141 — Slice 0: frozen Activity-edit contract and failing-before witness

**Source anchor:** Concord `main` `40837d54376f70cffb9ca539d52f7e40453ec1e6` (the #140 / PR #161 squash-merged audit baseline). **Scope:** audit-only; no production code, live teacher workspace, Core roster or Standards authority changes.

## Source boundary (reviewed on the pinned commit)

1. `concord/menu_activity.py::_update_activity_field`: loads compact Activity detail/current snapshot and initializes `library: StandardsLibrary | None = None`. Only `field == "scoring_orientation"` invokes `_standards_selection(orientation)`. All five branches—title, description, status, `activity_type`, and scoring-orientation/Focus—call `update_activity(..., standards_library=library)` after teacher confirmation. Thus ordinary mixed/standards-backed title/description/status/type edits can forward `None`.
2. `concord/workflows/activity.py::update_activity`: constructs the candidate from the durable current record and commits through `commit_record_batch` under the expected snapshot revision. It does **not** automatically load a missing canonical Standards Library. The standards argument remains a caller responsibility.
3. `concord/storage.py::_validate_loaded_graph_standards` and `_validate_candidate`: require canonical library if the Activity is mixed/standards-based **or** any Criterion or Score history is standards-backed. An evidence-only/local-only label is not independently conclusive of neutrality. The later fix must not weaken this graph/candidate validation.
4. `concord/menu_standards_context.py::standards_for_activity`: resolves the active library for standards-backed **orientation** only and has an error string ending `No GroupPlan was created.`; a direct unmodified reuse in Activity edits would miss the graph-history condition and show the wrong action name. #142 owns shared-message reconciliation.
5. `_standards_selection`: owns explicit scoring-orientation/profile/Focus selection and loads canonical Core Standards for modes that require it. Existing activity type and status prompt usability is separately owned by #146.

## Bounded failing-before replay

`tests/test_issue140_slice2_failing_before.py` has **five** synthetic test cases: one C1 mixed-status failure at the actual menu-to-service boundary; two neutral-control modes; one cancellation no-write test; one separate C2 Criterion preset failure assigned to #143. A green run of these tests on the pinned baseline documents **the old defect**, not the post-fix behavior. The generator's first invocation runs this exact file, rejects nonzero exit or an unexpected case count, and creates `docs/audits/issue141/slice0_baseline.json` using pinned Git-object hashes. It does not open a real Core/Concord classroom workspace.

The created JSON is an immutable *historical* receipt. `--check` verifies the original Git-object source and receipt bytes without re-running the obsolete failing-before C1 expectation after #141 repairs. A future slice converts C1 into a passing-after regression **without** modifying this historical receipt or any #140 frozen evidence.

## Slice 1 implementation constraints

- Use exact active Core Standards authority from the **same** current workspace and Activity; reject inactive/missing/mismatched profile or Focus before a write. Avoid cached or globally inferred libraries.
- Review *both* the existing graph and the proposed edit. Where the old Activity has standards-backed Criteria/Score history, orientation alone is insufficient. Preserve legal standards-neutral operations without requiring a library merely to satisfy a static checker.
- Retain expected-snapshot/CAS, cancel/no-op, actor provenance, and accurate, actionable error outcomes. Do not allow a write on invalid or stale state.
- Keep #141 confined to Activity lifecycle/edit propagation. Other Artifact/review/Score propagation is #142; preset identity #143; enum prompt UX #146; shared terminal/`:notes` adoption #153/#162.

## Core teacher-experience compatibility note

Core #236 specifies `pds_core.teacher_experience/1`; Core #237 was merged in [Core PR #246](https://github.com/Paper-Data-Suite/pds-core/pull/246), `main` `a0d5e1a50580bbe025f0cad23c7e8524203a52ec`. The source merge includes header rendering and exact choice-prompt `:notes` recognition, **not** Notes storage/menu or a qualified new Concord dependency. At Slice 0 preparation, Core's package still identified version `0.6.6` while Concord required `pds-core>=0.6.6,<0.7`. Do not import unreleased Core interfaces into this P0 correctness repair or duplicate them locally.

## Out-of-scope and honest gaps

No published Concord 0.3.4 wheel replay, actual physical return evidence, student authorship/judgment, new Core release, independent reviewer signoff, all-five-route success, or post-fix validation is claimed by Slice 0. Preserve the original #140 audit and hand the eventual fixed-after operation ID/test mapping to #162.
