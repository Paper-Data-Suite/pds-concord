# Concord #140 Slice 0 — Baseline Receipt

> Nonproduction, metadata-only audit. No classroom workspace was read.

- Captured (UTC): `2026-10-20T23:33:07+00:00`
- Repository: `Paper-Data-Suite/pds-concord`
- Branch: `140-freeze-baseline-and-teacher-context-audit`
- HEAD and local main: `68ddd804d2733fa900ee396ac7a2ba6bd98aa819`
- Annotated tag: `v0.3.4` object `16dec4e2b26dea4dc7cedacb0f79102e602bbcef`
- Tag peels to: `68ddd804d2733fa900ee396ac7a2ba6bd98aa819`
- Tracked source clean when captured: `True`
- Concord source: `0.3.4`; Core requirement: `>=0.6.6,<0.7`
- Python: `3.11.9`; platform: `Windows` / `AMD64`

## Published wheel verification

- core_v0_6_6_wheel: **verified_published_bytes_and_metadata**
  - SHA-256: `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`
- concord_v0_3_4_wheel: **not_provided**

Installed distribution metadata is separately captured in the JSON; it is
**not** equivalent to published-byte authentication or a clean-wheel test.

## Source inventory (classification deferred to Slice 1)

- `direct_cli_modules`: 31 files
- `other_menu_tests`: 7 files
- `prior_issue134_tests`: 8 files
- `prior_issue136_tests`: 17 files
- `teacher_menu_modules`: 36 files
- `workflow_modules`: 77 files

Exact relative file lists and #134/#136 SHA-256 fingerprints are in the JSON.
The existing bounded #136 AST dispatch tests are **not** a full menu audit.

## Provenance / scope limitations

- Remote Git refs must be compared by the runner; this script verifies local commit and tag objects.
- No live Activity, Core roster, teacher workspace or OneDrive location was opened.
- No installed-wheel smoke tests are claimed by this receipt.
- Windows physical returned-work opening, real print/QR/scan intake and
  actual Meridian ingestion remain **unperformed**; opening a prepared PDF
  is not a returned-evidence acceptance witness.
- Reproduce #138 P0 Activity Edit and Criterion preset bugs in Slice 2,
  rather than mislabeling source inspection as a menu reproduction.
- The detailed audited menu/context matrix is due in Slice 1; suspects
  remain unverified until operation-specific evidence is recorded.

## Reproduction command

```powershell
python scripts/issue140_slice0_baseline.py --repo . --output-dir docs/audits/issue140
```

Pass `--core-wheel` and `--concord-wheel` for published-byte validation.
Capture again only to a new output location: baseline files are create-only.
