# Concord #146 — Slice 4 controlled-field audit and Group status disposition

**Issue:** https://github.com/Paper-Data-Suite/pds-concord/issues/146

**Branch:** `146-teacher-first-status-choices-and-enum-audit`

**Slice 4 baseline:** `8dd5a5be30b50b6c0f366d1cb95ddf0602012e65` (qualified Slice 3)

## Direct Group-status finding and resolution

`concord/menu_group.py::_edit_group` previously prompted for free-text `Status`. A seven-choice menu now presents only the **native** `Group` statuses from `concord/models/collaboration.py`: `planned`, `active`, `inactive`, `completed`, `cancelled`, `archived`, `superseded`.

The existing `concord/workflows/group.py::update_group` preserves durable Group ID, creation provenance, parent/context and `supersedes_group_id`. Its ordinary status-update service does **not** create a successor. The menu explicitly tells teachers this, and uses `select_one` with current value, Group/Class/Activity identification and snapshot. Same-value selection is a no-write receipt, Back and declined confirmation are no-write, and stale Group selection is rejected before a service request. The canonical service still enforces revision compare-and-swap and graph validation.

`superseded` is a valid controlled *status* but is **not** equivalent to the presence of a successor record. No Group successor is inferred or written and no new custom transition graph is created.

## Other controlled/enum-like teacher choices reviewed

| Control | Existing source | Disposition |
| --- | --- | --- |
| Activity status | `menu_activity.py::_choose_activity_status` | Bounded and qualified in Slice 1; no changes |
| Session status | `menu_session.py::_choose_session_status` | Bounded and qualified in Slice 2; no changes |
| Membership/Role/Responsibility endings | `menu_assignment_end.py::choose_assignment_end_status` | End-only `completed`, `withdrawn`, `cancelled` qualified Slice 3; no changes to reassign |
| Scoring orientation | `menu_activity.py::_choose_scoring_orientation` | Existing `select_one`; unchanged |
| Criteria and Score targeting | `menu_scoring.py` | Existing bounded `_criterion_targets`/`_choose_disposition`; unchanged |
| Artifact author attribution and representation | `menu_artifact.py::_author_status`, `_representation_status` | Existing bounded `select_one`; unchanged |
| Missing GroupPlan signal decision | `menu_group_plan_missing_signal.py` | Existing `select_one`; unchanged |
| GroupPlan stages | `menu_group_plan.py` | Preview/Approve/Apply/Cancel are separate guarded domain actions, **not** a generic status setter; unchanged |
| Teacher-entered Group description/label | `menu_group.py::_edit_group` | Intentionally free-text descriptive fields, not enums; preserved |
| Rationale, classroom content, scheduled times | Module-specific workflows | Not status enums; not forcibly converted |

This is a scoped source-level audit of known controlled prompts, not a blanket certification of all Concord menus. #149/#151/#152 and #162 own adjacent follow-ups and frozen semantic checks. Do not rewrite their bounded workflows.

## Ownership and compatibility

- Concord-only changes: `menu_group.py`, the #146 baseline test, new Slice 4 tests, this audit document.
- No Core, Suite, Meridian, direct CLI, PDS native model, schema, dependency or publication changes.
- Published Core compatibility remains `pds-core>=0.6.6,<0.7`; do not rely on unpublished Core teacher-UI source capabilities.
- Core roster identity remains authoritative. A Group status does not imply Membership changes, returned evidence, authorship, Scores, or Grades.
- GroupPlan approval/application stays separate, preserving Suite #49/#51 and Core #238 scopes.

## Verification boundary

The six original free-text controlled-status witnesses become six passing source checks (no remaining XFAIL). New tests exercise actual Group status writes, no-op, cancellation, bad selections, stale selection, unchanged successor link and descriptive text editing on synthetic workspaces. This is not proof of a physical classroom walkthrough or a full installed-wheel qualification; Slice 5 owns those final gates.
