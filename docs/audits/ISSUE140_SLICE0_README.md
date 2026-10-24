# Issue #140 — Slice 0 capture contract

This slice **records only** the exact Concord v0.3.4 source/package/host baseline and #134/#136 regression inventory. It does not attempt the comprehensive operation matrix (Slice 1), failing-before live-reproduction harnesses (Slice 2), candidate classification (Slice 3), or guard rollout (Slice 4).

## Provenance

The v0.3.4 annotated tag peels to `68ddd804d2733fa900ee396ac7a2ba6bd98aa819`. As verified via the GitHub connector on October 20, 2026, the `140-freeze-baseline-and-teacher-context-audit` branch and `main` matched that commit. Local Git branch, `main`, tag, tracked cleanliness and origin must be verified afresh by the runner; the online remote-ref gate is separate from the offline Python baseline capture.

Expected Core: `pds-core` v0.6.6. The published Core wheel SHA-256, checked by the repository's own `scripts/verify_core_wheel.py`, is `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`. An installed distribution is not enough to authenticate a published wheel. The released Concord 0.3.4 wheel SHA-256 is `35fbebf4338420c83047f0cb4a09d06b22bb493abf4d67e6082e59ae4fc35b23`.

## Input and outputs

Run the supplied PowerShell runner on the correct checked-out branch from an active developer virtual environment. Supply paths to the original published Core and Concord release wheels if you have them; otherwise the receipt marks the absence explicitly. Do not copy or upload classroom data. The script does not access teacher workspaces, OneDrive, a roster or a network service.

Generated create-only files:

- `docs/audits/issue140/baseline.json`: versioned JSON with exact local Git identity, environment distribution metadata, trusted wheel digest status, source surface lists, and hash fingerprints of #134/#136 acceptance files.
- `docs/audits/issue140/baseline.md`: human-readable receipt with explicit limits and handoff to Slice 1.

The recorder validates expected branch, tracked-file cleanliness, source version/Core requirement, annotated-tag peeling and commit identity before writing. Rerunning against the same destination **fails safely** rather than silently rewriting a frozen baseline. To perform an independent rebuild, use a new output location and compare all stable fields; timestamps, environment/installation and untracked-file counts may differ.

The runner checks the remote branch and `main` against the fixed source commit before installation, verifies the payload hashes, installs additive files only, and executes focused Pytest/Ruff checks when available. The prior #134/#136 test outcomes must be reported from the runner output, not guessed from historical repository evidence. The baseline receipt itself does **not** certify human/physical or downstream acceptance.

## Limitations and handoff

- Existing #136 AST coverage enumerates bounded GroupPlan/Group/Session/Role/Responsibility routes. Other menus, especially Artifact/review/Score/labels, require Slice 1 inventory and Slice 3 contract classification.
- The known live Activity edit and dotted Standard Criterion preset failures belong to Slice 2 reproduction and subsequent #141/#143 fixes; source-only inventory is not a menu-reproduced failure.
- `prepare_artifact_pages` may resolve Core Standards internally and cannot be labeled defective just because a caller omits the context; preserve that candidate exception for dynamic verification.
- A prepared PDF viewed in Windows does not prove that genuinely returned work can be opened from a Windows long path. Real printer/QR/scanner/retention and authorized Meridian publication remain distinct later gates.
