# Concord #146 — Slice 0 controlled-prompt baseline and implementation map

**Issue:** [#146](https://github.com/Paper-Data-Suite/pds-concord/issues/146)

**Baseline:** `146-teacher-first-status-choices-and-enum-audit` branched from reconciled `main` `b61d79f2157695c321e0248ba0735282dc5052c6` (merged #145).

**Evidence class:** *code-path verified* on 2026-11-06, not a claim of physical classroom or installed-wheel acceptance.

**Slice 0 effect:** tests and audit documentation only. **No production code, records, enum model, Core/Suite module, or classroom state changed.**

## Scope and existing defects

Routine menu `prompt_text` requests a hand-typed controlled status at **six** places. Five are the primary #146 requirements; Group status is an additional confirmed audit item. The actual canonical model and workflow **already constrain** values. These failures are UX/input-interface defects; this audit does not claim any of these operations can durably write an invalid status or that Core authority can be bypassed.

| Surface | Exact handler | Current prompt | Canonical values | Disposition |
| --- | --- | --- | --- | --- |
| Activity status | `menu_activity.py::_update_activity_field`, field `status` | `prompt_text("Edit Activity", "Status")` | `draft`, `configured`, `active`, `completed`, `cancelled`, `archived` | **Slice 1:** numbered choice and current → next confirmation; preserve #141 Standards guard |
| Session status | `menu_session.py::_edit_field`, field `status` | `prompt_text("Edit Session", "Status")` | `planned`, `active`, `completed`, `cancelled`, `interrupted`, `archived` | **Slice 2:** numbered choice, separate actual times/reasons |
| End Membership | `menu_group.py::_end_member` | `prompt_text("End Membership", "End status")` | **end-only:** `completed`, `withdrawn`, `cancelled` | **Slice 3:** shared end-choice helper; immutable Membership history |
| End Role | `menu_role.py::_end` | `prompt_text("End Role", "End status")` | Same end-only subset | **Slice 3:** do not conflate with reassign/supersede |
| End Responsibility | `menu_responsibility.py::_end` | `prompt_text("End Responsibility", "End status")` | Same end-only subset | **Slice 3:** preserve assignee/Group context and revision |
| Group status | `menu_group.py::_edit_group`, status branch | `prompt_text("Edit Group", "Status")` | `planned`, `active`, `inactive`, `completed`, `cancelled`, `archived`, `superseded` | **Slice 4:** inspect successor semantics before offering `superseded`; no invented transition graph |

**Sources of truth:** `concord/models/collaboration.py` supplies Activity/Session/Group allowed sets and broader assignment statuses. `concord/workflows/_collaboration.py` exposes `END_ASSIGNMENT_STATUSES = {completed, withdrawn, cancelled}`, separately from reassignment predecessor statuses (`reassigned`, `superseded`). `concord/workflows/activity.py`, `session.py`, `group.py`, `role.py`, and `responsibility.py` perform canonical writes under Activity snapshot compare-and-swap and model/graph validation. Avoid local enum copies drifting from those contracts; if a small presentation mapping is introduced, qualify it against canonical values.

**Transition caveat:** the native Activity and Session models validate membership in allowed sets; code inspected does **not** establish a separate state-to-state transition table for every Activity/Session state. Do not call an invented restricted transition map "canonical." Provide the legitimate currently offered statuses and preserve service validation. End assignment has a narrower real contract and only planned/active assignments are selected by the existing menus.

## Individually reviewed adjacent controls

| Control | Source finding | Decision |
| --- | --- | --- |
| Scoring orientation | `menu_activity.py::_choose_scoring_orientation` uses `select_one` for `evidence_only`, `standards_based`, `mixed`, `local_criteria_only` | **Already bounded; leave intact.** Changing orientation/Focus remains standards-authoritative under #141. |
| Criterion and Score targets | `menu_scoring.py::_criterion_targets` uses `select_many`; scoring-specific target selection is separately bounded | **Already bounded; leave intact.** No Group-to-student result inference (#145/#152). |
| Score disposition | `menu_scoring.py::_choose_disposition` delegates to `_choose_enum`; levels are chosen from typed Scale values | **Already bounded; leave intact.** Non-score dispositions are not low scores. |
| Author attribution and representation | `menu_artifact.py::_author_status` and `_representation_status` use `select_one` | **Already bounded; leave intact.** Human authorship is not inferred from packet or Group status. |
| Missing-signal GroupPlan disposition | `menu_group_plan_missing_signal.py::resolve_missing_signal_from_menu` uses numbered `select_one` decisions | **Already bounded; leave intact.** Never infer signal bands. |
| GroupPlan lifecycle | `menu_group_plan.py` offers separate Preview, Approve, Apply and Cancel actions, not a generic status setter | **Guarded domain workflow; leave intact.** Cross-class Core roster reconciliation remains authoritative (#147 owns bulk editing). |
| Review and moderation | `menu_artifact.py` contains bounded status/choice selectors, separate rationale text, review-state validation | **Existing bounded paths not a blanket rewrite.** Record any specific later gap with an exact callsite and route to #149/#151/#152 as appropriate. |
| Guided rubric and Scoring Scale | Completed #144/#145 guided menus already use bounded teachers' choices with immutable/native service writes | **Do not regress.** |

The surrounding complete teacher-operation semantic review remains **#162**. This focused inventory does not reclassify or modify #140's frozen census or certify every menu/CLI path.

## Proven protections to preserve during subsequent slices

1. **Activity status:** `menu_activity.py::_update_activity_field` was repaired by #141 to reload the pinned root and verified graph, require the authoritative Core Standards Library when orientation **or historical standard-backed Criteria/Scores** need it, then call canonical `update_activity` with `expected_snapshot_revision`. A new selector must not bypass this; `configured` is an **explicit** teacher choice, never computed from packet generation or readiness.
2. **Session:** the service retains native Session creation provenance and immutable record revisions. Changing status must not synthesize `actual_start`, `actual_end`, a reason, or an author. Current `standards_kwargs_for_activity` forwarding remains in place.
3. **End assignments:** ending one Membership/Role/Responsibility changes only the exact current assignment status and retains history. `completed`, `withdrawn`, `cancelled` differ from the Reassign service's `reassigned`/`superseded` semantics. Preview must name record/participant/role/responsibility and `current → chosen` state.
4. **Group status:** a generic `superseded` label is not evidence of a valid successor. Preserve existing Group identity and effective context; follow canonical service and graph checks, not guessed implications.
5. **Confirm/Back:** reuse `menu_prompts.py::select_one`, `confirm_write`, and existing H/B/M/Q. Failure, Back, no-op or stale snapshot must not create a write or a retry under a new revision.
6. **Cross-repo:** Concord currently requires published `pds-core>=0.6.6,<0.7`; newer Core teacher-experience source capabilities from #237 are not automatically part of that wheel. Do **not** import unreleased terminal UI/Notes APIs. Suite #49/#51 own launch/compatibility, not Concord lifecycle; Core #238's protected teacher-private storage is unrelated. No change to Core/Suite/Meridian, PDS2, release metadata or published manifests.

## Slice 0 automated witnesses

`tests/test_issue146_slice0_controlled_status_baseline.py` is deliberately **read-only AST/static contract evidence**; it never opens the PDS workspace or invokes mutators. Six parametric **expected failures** record where a free-text controlled-status prompt remains. They should start as `XFAIL`; after a menu is changed, its corresponding test becomes `XPASS` (non-strict) and targeted runtime acceptance in the implementing slice establishes behavior. Positive assertions guard known working numbered choices, exact canonical allowed values, assignment end-only set, #141 Activity context and the action-based GroupPlan lifecycle.

**Evidence boundary:** these tests cannot prove a real menu writes or correctly cancels; that requires Slice 1–5 controlled-I/O menu tests against isolated synthetic Core/Concord workspaces. Do not re-label source AST assertions as live teacher acceptance.

## Implementation handoff / gates

- **Slice 1:** Activity current/next numbered selection, explicit `configured`, preview/confirm, no-op/cancel/mixed/neutral/stale tests; use existing #141 guard and authoritative Core context.
- **Slice 2:** Session status and accurate timestamps/reasons; tested canonical readback, no-op/cancel/stale.
- **Slice 3:** shared **end-only** selection and contextual receipt for each of Membership, Role, Responsibility; 3×3 end-status cases plus reassign exclusion and immutable history.
- **Slice 4:** Group status gap; audit labels/semantics and preserve GroupPlan/scoring/review controls without rewriting them.
- **Slice 5:** consolidated menu-service synthetic E2E, direct CLI, Core 0.6.6 installed-wheel, full repo qualification and supported CI; human acceptance separately declared.

Each subsequent slice should amend the witness/disposition record with code-path and menu-level results, name exact changed files, pin its prerequisite tree, and avoid full repository qualification until the final integration gate.
