# #153 Slice A2b — local navigation and screen lifecycle witnesses

A2a qualified on Windows at
`3ec82e03fd919c5f80734c85def15ad6be64b5a9`: 105/105 direct input locations
matched the A1 census, no unmatched sites and no Notes enablement.
92 choice, 8 confirmation, 4 data-entry and 1 pause site.

## Representative controller and shortcut boundaries

| Controller | Existing local behavior to preserve | Future shared command posture |
| --- | --- | --- |
| Root menu | 1–8, H/Q; B/M disabled; existing Core unwind | candidate only after released Core and site review |
| Activity / Role / Responsibility selectors | numbered choice, H, B cancels, Core M/Q unwind; recursive retries observed | keep disabled inside form until context safety separately proved |
| Generic select_one/select_many | numeric page-local choices, N/P, A/D for multi-select, H/B/M/Q | keep disabled; temporary selection is local |
| GroupPlan bulk selector | V current page, A all eligible pages, C clear, D review, N/P | keep disabled; temporary selection and later reviewed batch |
| GroupPlan batch review | SAVE BATCH, A/D actor changes, N/P review pages, H/B/M/Q | confirmation, never shared Notes |
| Actor review | exact approval token, A alternate, D saved default, H/B/M/Q | confirmation, never shared Notes |
| Attention discovery | N/P, numeric item, read-only discovery, fresh Activity load before routing | disabled pending review |
| Attention details | N/P and B/H/M/Q, no owner action | disabled; current read-only screen remains local |
| Scan selection | numeric choices, C custom path, R refresh, N/P, H/B/M/Q | disabled; path entry separate and never eligible |
| Score post-commit | C another Criterion, N next work, A Advanced, H/B/M/Q | disabled; preserve pinned authority and post-write receipt |
| Workspace Settings | workspace selection uses Core authority; returning invalidates actor cache | disabled; never recreate shared classroom management |

All sites remain disabled for Notes. This representative review is not a
site-by-site proof of safe suspension for the 92 choice prompts. Final
collision, context restoration and actual parser integration remain F,
dependent on Core #244's qualified release. A2a line identities remain a
frozen baseline, not a live allowlist.

## Failing-before witnesses

`tests/test_issue153_slice_a2b_navigation_witnesses.py` adds strict,
exception-specific expected failures for confirmed source defects:

1. `menu_activity._choose_activity_type`, `menu_role._choose_optional_group`
   and `menu_responsibility._choose_assignee` call themselves after Help
   acknowledgement or invalid input. A spy intercepts only recursive
   re-entry while the original controller executes normally. Six bounded
   cases prove stack growth without requiring hundreds of prompts or
   changing the interpreter recursion limit.
2. `menu_attention.launch_activity_attention_details` prints the Help
   explanation, immediately continues its loop, then clears before the
   next input. A captured clear-marker witness detects this ordering.

These are expected failures, not repaired functionality. Strict XPASS or
an unexpected exception is a qualification failure. Twelve ordinary
selection and B/M/Q preservation cases must pass. The fixture uses no
real roster, workspace, or durable writes. Core's real published navigation
parser remains in use.

The unavailable/read-only attention branch also warrants review: its
helper prints H/invalid feedback without an acknowledgement before the
outer loop clears on the next redraw. Prelesson readiness instead retains
one screen and repeats its navigation prompt. C must distinguish these
contexts; do not blindly change the shared local helper in a way that
clears readiness facts or changes EOF behavior.

## Next implementation boundary

C1: replace the three confirmed recursive retry paths with local loops,
preserving per-redraw reads where present and the existing exact choices,
cancel/unwind semantics. Remove the corresponding strict xfail markers only
with the fix. C2: fix the attention Help/invalid feedback lifecycle, with
explicit acknowledgement and clear-marker regression tests; then clarify
generic multi-select scope. B preparation and E date work remain separately
bounded. D must preserve #152 confirmation and immutable history guards.

No production changes in A2b. No Core renderer, command parser, service,
storage, or substitute capability added. No claim of physical or installed
shared-feature acceptance.
