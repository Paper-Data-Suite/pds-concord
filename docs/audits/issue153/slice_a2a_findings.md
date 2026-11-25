# #153 Slice A2a — direct prompt classification and source findings

A1 local qualification: `fad9ad1fbc050713ec69ec8011a8707e6fa24377`.
Core wheel digest and installed 0.6.6 version checks passed. Ruff format/lint
and strict Mypy passed; 18 baseline regression tests passed in 1.66 s.
Two inventory exports matched; 46 files, 1,790 selected calls, 105 direct
input calls and zero literal Notes mentions. Owner-reported inventory SHA-256:
`F4F556EFDB05F6066A622FE060B14F506F380552D576058984FA12FEED78F26C`.

## Direct prompt review

The accompanying `slice_a2a_prompt_scope.json` classifies 105 source input
locations by prompt role, with all Notes flags disabled. The pinned menu
source was inspected remotely; the local JSON export was not attached.
Exact source path/line coverage must be reconciled against the local
census before accepting this artifact. This is not a claim that every
choice site is safe to suspend or that all local shortcut branches,
dynamic dispatch, nested state or helper calls have been reviewed.

- Choice: numbered task/menu/paging/selection actions, including read-only
  navigation, scan selection and post-Score actions. Future opt-in requires
  separate site-specific safety and collision qualification.
- Data entry: text/exact text, actor ID and workspace path. Existing
  local navigation semantics remain unchanged; never shared Notes.
- Confirmation: ordinary confirmation, copy, actor-reviewed approval,
  workspace confirmation, feedback/export and mixed GroupPlan batch review
  containing SAVE BATCH. Never shared Notes, even where A/D/N/P are accepted.
- Pause: acknowledgement only, never shared Notes.

The manifest is not a runtime parser or an enablement allowlist. Zero Notes
literal mentions is not proof against dynamic collisions. Core #244 remains
the B/F installed integration dependency. No replacement Core implementation.

## Source-verified observations for C/D/E

| Observation | Evidence | Next disposition |
| --- | --- | --- |
| Recursive help/invalid-choice retry | menu_activity.py::_choose_activity_type re-enters itself after help or invalid input; menu_role.py::_choose_optional_group and menu_responsibility.py::_choose_assignee have comparable recursive retry paths | C1: bounded reproducible regression for repeated help/invalid input; replace only confirmed recursive local retries with loops, preserving B/M/Q and selection semantics |
| Header task/context mixing | menu_activity.py::_choose_activity_status passes multiline title including Activity, class and Activity ID, current status and snapshot into select_one | B preparation/E: separate teacher-safe task title and verified context/details; no imitation of Core header renderer; Core v1 header rejects embedded newline/control characters |
| Generic multi-select scope | menu_prompts.py::select_many displays A. Select all and selects every item across all pages; menu_group_plan_bulk.py already explicitly distinguishes V current page and A all pages | C2: qualify generic wording and selection behavior; preserve already-correct bulk selector |
| Actor confirmation display | menu_actor_action.py prints Actor ID on ordinary reviewed confirmation; A/D modify only the immediate actor choice and exact confirmation still authorizes the write | D/E: review whether raw ID is essential to attribution disambiguation; preserve reviewed actor identity and guards, no blind deletion |
| Conflict and receipts | menu_prompts.py distinguishes storage conflict from partial success; reload is a read-only action, while generic error rendering uses str(error) and partial-success display includes a snapshot hash | D: audit actual error classes and sensitive-detail cases; preserve existing correct recovery, no speculative synchronization diagnosis |

These are source findings, not failing-before test results or human usability
measurements. Do not claim a defect fixed without the corresponding witness.

## Date producer trace (E)

- `workflows/packet_instantiation.py::_generation_date` defaults to
  `datetime.now(timezone.utc)`, requires an aware datetime and returns
  `value.date().isoformat()`. Its injected-clock behavior preserves the
  supplied offset's calendar date. It does not currently choose a local date
  for the default UTC clock.
- `prepare_packet_instantiation` includes this date in the reviewed preview
  and digest; template binding `current_date` uses the generation date.
- `workflows/packet_instantiation_commit.py::_revalidate_review` reconstructs
  a fixed clock at noon UTC on the reviewed date before checking the digest.
  Packet persistence retains the reviewed date, separate from created
  provenance. Do not rewrite historical dates or weaken digest revalidation.
- `menu_packet_generation.py::_preview_lines` displays Generation date;
  history distinguishes planned date from actual offset-aware created time.

At 2026-10-19 21:00 EDT the same instant is 2026-10-20 01:00 UTC. The default
UTC date extraction explains a plausible next-day label or template binding.
This is a deterministic source-level explanation, not proof of the exact
historical teacher event. E must reproduce the actual producer/display path
with controlled clocks and decide whether an explicit classroom date is
needed using the existing contract; do not change canonical provenance or
introduce new persisted date fields without evidence/approval.

## Next gate

Reconcile manifest path/line keys against all direct input calls in the A1
export and confirm counts by category. A2b still owns actual screen and
shortcut/context classification, particularly nested review/paging/return
sites. C1 is the first proposed independent runtime repair after bounded
failing-before reproduction. No production edits in A2a.
