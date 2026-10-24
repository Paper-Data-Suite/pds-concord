# Concord #140 — Slice 1 automatic census and initial context matrix

**Scope:** Nonproduction, offline, source-only inventory. This slice does **not**
change production functions, confirm the runtime bugs from #138, or certify a
route's correctness. The next slices provide menu-dispatch evidence and manual
contract review.

## Generated, checked-in artifacts

- `issue140/teacher_operation_matrix.csv` — stable identities for every parsed
  source function plus detected workflow and menu-delegation boundaries, with
  explicit unverified context fields. Source triage in #138 is flagged as
  `CODE_PATH_VERIFIED` only at exact named sites with visibly missing forwarding;
  the classification does not imply runtime reproduction.
- `issue140/service_context_catalog.csv` — AST census of downstream workflow
  definitions exposing Standards parameters, guarded loads/writes, or internal
  workspace Standards lookup. This catalog is **not** a service contract proof.
- `issue140/surface_inventory.json` — every AST call in each enumerated menu and
  direct-CLI module (including non-service UI calls) and the reason those
  *non-service* calls are not included in the narrower service-boundary CSV.

The default disposition is `INVESTIGATE`, evidence status
`BLOCKED_OR_UNTESTED`. Fields such as roster, actor, provenance, privacy,
CAS and current Activity mode must be reviewed individually; no passing context
is invented. Known internal Standards resolution in `prepare_artifact_pages`
remains **unverified** until the positive test in Slice 3.

## Reproduce / consistency check

```powershell
python scripts/issue140_slice1_census.py --repo . --check
python -m pytest -q tests/test_issue140_slice1_census.py
```

Initial generation is performed by the guarded Slice 1 runner. It never
rewrites the original Slice 0 baseline files. If source changes add new
handlers or calls, `--check` fails until the audit inventory and reviewed
classifications are updated. Regenerate to a *separately reviewed* copy before
replacing existing matrix bytes; this script deliberately does not overwrite
preexisting audit files.

## Limitations / handoff

Static AST inventory cannot resolve dynamic dispatch, aliases, consumer
contracts or actual read/write safety conclusively. A handler row is not proof
that its route is reachable from the main menu. Calls classed `OTHER_CALL`
remain visible in the full inventory for a human to reclassify if they are
indirect service entry points. The matrix starts with `unreviewed` context
fields by design, to avoid false P0 assurance. Slice 2 records actual-menu
failing-before witnesses for #141 and #143, while Slice 3 qualifies #142's
candidate callsites and legitimate standards-neutral controls.

The human evidence and captured package identity in `baseline.json`/
`baseline.md` refer to the original released commit, *not* the subsequent
branch-tip WIP commits. Preserve that distinction.
