# Concord #151 — Slice 2: shared scan-routing handoff

**Status:** Native Windows candidate; qualification is a separate gate.
**Baseline:** `151-authoritative-collect-returned-evidence` at `9a04a9b26ee92bf0812f81ea0d60c3ee1d4e544b` (Slice 1 qualified and pushed).
**Core:** published 0.6.6 is the installed target; provenance and future Core #244 qualification remain separate.

## Design decision

Keep one **shared PDS scan intake**, owned by existing `concord/menu_scan.py` and Core's PDS2 routing and retained-source services. Ordinary Collect now displays `R. Route or review scans (shared PDS workspace)` and calls `launch_scan_routing_menu(state)` with the exact existing teacher session. It does not create a second intake wizard or forcibly filter routing to the selected Activity.

The handoff opens an existing nested menu: `1. Route scans` and `2. Routing review`. The user must choose an operation there, then follow its existing source and write confirmation steps. Entering and leaving the menu is a no-write action. `B` returns to Collect; `M` and `Q` propagate to the module owner. The parent `S. Collection status` action refreshes canonical routed returns from a verified snapshot on demand.

### Why routing is not scoped to the opened Activity

Core PDS2 QR routes may designate another Concord Activity, Class, or a different module such as ScoreForm. Binding scanned physical pages to the **currently selected** Activity would risk false attribution or overwrite. The selected Activity is navigation context, **not** a routing destination assertion. Failures go to the existing workspace-wide Routing Review for explicit teacher selection. The Collect help explicitly discloses this boundary.

## What this slice changes

- `concord/menu_artifact.py`: shared Scan Routing shortcut and teacher-readable scope warning.
- `tests/test_issue151_slice0_collection_witnesses.py`: remove the strict xfail only from the now-implemented Scan Routing discovery witness; preserve both return-gating xfails.
- `tests/test_issue151_slice2_scan_routing_handoff.py`: isolated synthetic handoff/navigation/ownership tests.
- This audit file. No new persistent schema, routing writer, retained-scan store, Notes store, or Core patch.

## Explicit boundaries

- Core retains originals and source SHA-256; the existing scan intake uses Core registration/dispatch and PDS2 payload parsing.
- Concord's existing routing review handles unresolved/partially resolved pages. No route is inferred from menu context, authors, packet generation, or an Activity label.
- No automatic assembly, attribution confirmation, Review, Score, Grade, Notes, or publication.
- Neither shell-open success nor a preprepared packet is a physical scan-return acceptance.
- Shared B/M/Q/H semantics and no-color terminal behavior remain with the existing menu implementations. No custom global state or shadow workspace is introduced.

## Qualification

1. Confirm exact feature/base commits and a clean working tree before applying the patch.
2. Verify source ZIP and patch integrity; check the patch before writing any file.
3. Run Ruff and formatting on touched Python files, Mypy on the existing collection projection, documentation checks, and the new handoff tests.
4. Run both Slice 0 and Slice 1 tests and focused existing Scan Routing / Collect / navigation regressions. The two remaining return-gating tests must stay **strict xfail**; Scan Routing discovery must now pass.
5. Check exact staged scope and no whitespace errors before an optional guarded commit/push.

Not qualified in this slice: actual physical scan/QR, printed/distributed paper, live OneDrive shared workspace, Windows viewer alias, or published candidate wheel. Those remain integrated-acceptance gates.

**Next:** Slice 3 — exact assembly and verified viewer continuity (including historical version selection and returned, not merely prepared, deep-path PDFs).
