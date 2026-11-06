# Concord #145 — Slice 0 baseline and Slice 1 pure draft

Status: **candidate, not qualified** until guarded Windows and GitHub checks pass.

## Source-pinned baseline and ownership

- Concord `main`, squash merged PR #166 / #144: `5aeb1ae3f98a4bac1439dcd46a802241ab3a9dc8`; root tree `19cb07889ad03db9dfee3144dea8a0ba1b7ab679`.
- Issue #145 branch at audit: `145-teacher-first-criterion-sets-and-saved-assessment-setup` at that same commit. Guard before each qualification; do not infer that a later branch still matches.
- Published compatible inputs: Concord v0.3.4 and **official Core v0.6.6**; later source-only Core functionality is not a released requirement. No release/version/tag change here.
- `menu_scoring.py::_create_criterion_set` calls `create_criterion_set` but does **not** call `select_activity_criterion_sets`; they are independent guarded commits. `menu_scoring.py::_select_criterion_sets` is a separate route.
- `menu_scoring.py::_build_criteria` asks for keys, labels, definitions, IDs, kind, Focus Standard IDs, target enums and native default Scales one Criterion at a time.
- `menu_scoring.py::_save_criterion_set_as_preset` separately prepares/reviews/commits native-to-reusable Criterion Set extraction, using an optional *exact saved Scale preset revision*, not a native Scale ID.
- `workflows/criterion_sets.py` owns create/revise/select and their exact snapshot/CAS and history/used-Score guards. No menu helper may bypass them.
- `workflows/reusable_presets.py` owns reviewed native-to-preset extraction and saved-to-native materialization. No alternative preset store is authorized.
- `pds_core.standards.StandardDefinition` supplies code, short_name, description, active/tags; Core `validate_profile_standard_selection` provides canonical profile membership. Raw IDs stay unchanged, including `SL.PE.11-12.1`.
- Native `CriterionSet(scope='reusable')` is **not** an independently saved preset. Semantic scope must never be advertised as a committed reusable library entry.

## Current menu to authority map

| Teacher route | Service authority | Writes | Scope disposition |
| --- | --- | --- | --- |
| Create native Criterion Set | `create_criterion_set` | Native Set + ordered Criteria, one guarded Activity snapshot | #145 replaces ordinary draft prompts, later adds safe selection continuation |
| Select exact Criterion Set revisions | `select_activity_criterion_sets` | Updated Activity selected Set IDs | #145 composite continuation; preserve historical Score-used Sets |
| Revise native Set | `revise_criterion_set` | New immutable Set revision + new Criteria | #145 later guided editor; no mutation of old history |
| Read native details | `list_criterion_sets`, `show_criterion_set` | Zero | #145 teacher labels and current/selected receipt |
| Save native Set for reuse | `prepare_criterion_set_preset_from_activity`, `save_criterion_set_preset_from_activity` | Read-only review, then separate preset write | #145 later explicit approval/partial recovery |
| Use saved setup | `prepare_scoring_setup`, `materialize_scoring_setup` | Read-only review, then guarded new native records | #143 authority, reused by #145 |
| Create/edit native Scale | `menu_scale_guidance` and scoring services | Independent native Scale write | #144 completed; #145 must not reimplement |
| Core Standards/profile and roster | `pds_core.standards`, Core class services | Canonical Core authority | Read/validate only in #145 |
| Grade/proficiency mapping | Meridian | Out of scope | No Grade or derived Score |

## Slice 1 implementation boundary

Three **additive** files only: this audit, `concord/criterion_guidance.py`, and `tests/test_issue145_slice1_criterion_guidance.py`. No existing menu, graph, serializer, Core or Suite file changes.

The module is a pure, frozen in-memory Criterion draft and presentation adapter. It shows all five canonical target kinds with human labels, resolves only actual Core Focus Standard metadata, rejects inactive/deprecated and invalid profile/Focus selections, preserves governing vs optional aligned Standard identity, maps drafts into preexisting `CriterionSpec` shape, and validates using the actual native `Criterion` and `CriterionSet` constructors. It includes edit/add/move/remove **in-memory only** and an honest zero-write preview.

**Not proven by Slice 1:** actual `create+select` completion, canonical graph Scale linkage or Activity freshness, native/preset writes, menu dispatch, historical Score resolution, installed-wheel parity, physical classroom acceptance, or full release qualification. Those require later slices with actual services and synthetic isolated workspaces.

## Required candidate qualification

Guard branch/HEAD/tree, clean index/checkout and exact remote refs. Authenticate the source ZIP manifest and published Core wheel; reconstruct a detached candidate; check only three additive files; run Core wheel verification, Ruff, strict mypy and the focused Slice 1 pure tests. Mirror three files into checkout only after success; do not stage, commit, push, PR, merge, release or read classroom data.
