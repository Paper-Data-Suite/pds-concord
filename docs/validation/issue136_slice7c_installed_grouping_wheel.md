# Concord #136 Slice 7C — installed-wheel teacher grouping acceptance

## Scope

The existing #136 Core 0.6.6/Concord 0.3.4 isolated-wheel harness already
checks publication-producer/reader contracts, exact Core Standards identities,
package provenance and academic-result publication. Slice 7C appends an
**independent installed** synthetic grouping test in the *same* isolated Python
virtual environment, so there is no second wheel build or dependency installation.

## Acceptance gates

- Official `pds_core-0.6.6-py3-none-any.whl` SHA-256 equals
  `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`;
  metadata identifies Core 0.6.6. This is authenticated before building Concord.
- Source checkout is not on the isolated `python -I` import path. Concord and
  Core import from site-packages; no installed sibling PDS project is required.
- Actual **manual GroupPlan teacher-menu callback** resumes an existing mixed
  standards-backed Activity and persists a reloadable draft without error.
- Actual **save** and **use saved grouping** menu callbacks call production
  storage/workflow services. Six labeled groups/29 synthetic students survive
  save/reload and materialize as an independent target Activity draft.
- Existing GroupPlan preview, approve and application services create exactly
  six Groups and 29 Memberships in the target Activity. No Scores or evidence
  links are created. Source Activity and saved arrangement remain unchanged.
- Historic v0.3.3 installed-acceptance harness is not modified.

This is digital installed-wheel acceptance **only**. It is not an actual teacher
workstation review, physical printing, scan capture or real Windows long-path
PDF/folder/HTML viewer acceptance. Final CI/release remains pending.
