# #153 Slice A1 — source/release baseline and teacher-interface census

Status: first bounded audit candidate. No runtime behavior or dependency
changes. A1 is not the complete Slice A semantic audit.

## Exact baseline

- Concord main and new branch at `75f607dba0179e77d1fa2c9602cd6d6449fc4e27`
  (#152 squash, PR #176). Branch `153-teacher-experience-navigation-recovery`.
- `pyproject.toml`: Python >=3.11; Core `>=0.6.6,<0.7`; Ruff E/F/I;
  strict Mypy over concord and scripts.
- Official latest Core release checked on GitHub: v0.6.6. Expected wheel
  `pds_core-0.6.6-py3-none-any.whl`, previously authenticated release
  digest `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`.
  Local artifact and installed distribution still require verification
  on the owner's workstation.
- Core v0.6.6 tag tree exposes `pds_core/menu_navigation.py` and
  `pds_core/cli_support/screen.py`, but no `pds_core/teacher_*.py`
  public v1 modules. Do not equate the old fixed Core-menu helper with
  the shared renderer.
- Core #236, #237, #239 and #240 are closed; #244 consolidated release
  is open. Source availability is not installed acceptance. #238 is
  superseded; workspace-native Notes is Core-owned.

## Ownership gate

Read the binding caution at the start of issue #153 and the accepted
Core contract at
[teacher_experience_contract_v1.md](https://github.com/Paper-Data-Suite/pds-core/blob/main/docs/teacher_experience_contract_v1.md).

No replacement renderer, shared parser, Notes implementation, roster
editor, workspace registry, compatibility emulation, private Core import,
or interim Core release is permitted. Preserve the pre-contract Concord
workflow. Future narrow consumer calls require actual authenticated
released public capabilities and installed acceptance. B/F shared-feature
acceptance is blocked pending the upstream release. No local substitute.

## Representative source-verified baseline

| Surface | Current implementation / disposition |
| --- | --- |
| Root menu | `menu.py::_main_menu_once` clears, prints legacy Concord identity without an explicit task title, offers eight numbered actions plus H/Q; B/M disabled. `launch_menu` unwinds Core M/Q and handles CancelMenuAction, Ctrl-C and EOF. Preserve these semantics. |
| Navigation | `menu_navigation.py::parse_menu_navigation` handles local H and delegates B/M/Q to published Core `parse_navigation_choice`. It is not a replacement Core parser. Preserve delegation and local flags. |
| Display | `menu_ui.py::print_menu_header` prints plain Concord, optional title, blank line. Shared renderer adoption blocked; don't clone it. `clear_screen` requires stdin and stdout TTY and catches AttributeError/OSError before OS-specific clear. No generalized deficiency asserted. |
| Data entry | `menu_prompts.py::prompt_text` strips input; `prompt_exact_text` preserves raw whitespace, both retain established H/B/M/Q. Do not alter these existing semantics to introduce shared Notes. |
| Approval | `confirm_write` renders reviewed values, requires the explicit token case-insensitively, accepts empty/B cancellation, supports H/M/Q. Not a Notes prompt. `menu_actor_action` supplies separate actor boundaries. |
| Choice/pagination | `select_one` and `select_many` are ten-row local selectors, N/P paging, H/B/M/Q, with A select-all and D done in multi-select. Existing A selects the whole input sequence, not just the page. Audit whether the displayed wording is explicit; no defect claimed yet. |
| Result/error | `show_result` clears, prints a titled result and waits for acknowledgement; `pause_for_user` is a pause, not a choice. `prompt_conflict_reload` offers explicit read-only reload; `handle_write_error` distinguishes storage conflict/partial success. Audit actual error scope and any raw detail leakage before proposing a fix. |
| Scoring | `menu_artifact_scoring.py` selected-work flow pins authority, selects explicit target/criterion/scale/value, previews, confirms and revalidates before mutation. Separate post-Score menu C/N/A plus navigation. Preserve #152's fresh continuation and immutable receipt semantics. |
| Attribution | `menu_context.py` caches the provider-backed teacher attribution with fingerprint checks; legacy actor-ID entry is data entry, not a Notes prompt. Returning from Workspace Settings invalidates process-local actor state. |
| Packet dates | `menu_packet_generation.py::_preview_lines` prints generation date; `_choose_generation` explicitly distinguishes planned date from actual created time. `menu_teacher_history.py::teacher_planned_date` validates date-only ISO input; `teacher_recorded_instant` requires offset-aware input and converts via local astimezone(). Do not change provenance. Trace the generation-date producer in A2/E before treating October 19/20 as a bug. |
| CLI boundary | `cli_app/handlers/menu.py::handle_menu` lazily launches teacher menu; `cli_app/main.py` also dispatches the interactive entry. Explicit direct CLI output and error/partial-success handling are a distinct boundary. |

Before traces are source-derived, not observed human timings:
root → Open an Activity → task → result → acknowledge → return;
reviewed Artifact → explicit target/criterion/scale/level/context →
reviewed authorization → guarded commit → receipt → fresh continuation.
No claims of redundant confirmations or measured interaction burden yet.

## Prompt scope and census

`scripts/audit_issue153_teacher_surfaces.py` enumerates the menu modules
and designated CLI entry boundaries without importing them. It records
source hashes, selected call names, source positions, first argument
expressions, keyword names and literal strings containing the Notes token.
Output is deterministic JSON for the same file bytes and interpreter.
Redirect it outside the repository. It performs no workspace access,
menu input, writes to the repository, or Core feature detection.

The census is **syntactic only**: matching names or literal strings does
not prove call resolution, prompt kind, shortcut behavior, reachability,
context safety, or absence of dynamic/aliased collisions. A2 must review
actual dispatch sites and follow helper delegation. Prompt examples above
are verified at the named source locations; all other rows remain
unclassified. The frozen #140 inventory and #162 semantic gate are
independent and untouched.

| Prompt example | Classification | Notes eligibility |
| --- | --- | --- |
| root and task numbered choices | menu choice | future opt-in only after collision and installed capability qualification |
| select_one/select_many | menu choice | review individually; no active command now |
| prompt_text/exact_text and actor ID | data entry | never |
| confirm_write | confirmation | never |
| pause_for_user | pause | never |
| direct CLI arguments | noninteractive | never |

## Bounded qualification and next work

Run the existing `tests/test_menu_foundation.py`,
`tests/test_menu_density.py`, and
`tests/test_issue134_slice3a_teacher_history.py` as baseline witnesses.
These cover Core navigation delegation, captured-stream clear suppression,
root help, paging, confirmation, read-only conflict reload, partial
success, nonchronological labels and date/instant distinctions. These
are preservation checks, not failing-before tests or complete acceptance.

Generate the callsite census twice and compare the output hashes; inspect
file coverage, literal mentions, Core imports and exact installed baseline
before A2. A2 will semantically classify the highest-value nested/local
dispatch boundaries, trace the date producer, identify actual mismatches
and add failing-before tests only for reproduced defects. No runtime
change is authorized in A1.

Remaining: A2 semantic prompt/screen/collision classification; installed
Core verification; B/F upstream gates; C/D/E targeted implementation;
complete local and CI qualification. No physical or release acceptance.
