# Concord #151 — Slice 3B: verified historical assembly selection and viewer continuity

**Exact baseline:** `12d1caa46a9e4e260defcd2a4e9b2dcd4e35a07f`; expected `main` `8443e9093e8f0ca14fc4c0c0abc20e0ede7eb0d5`. This is a feature-branch-only source candidate, not a wheel or physical-scanner acceptance.

## Concrete teacher navigation gap

`open_verified_assembly_version` lists each verified historic assembly using only a minute-level printed creation timestamp, page count, and newer-evidence qualifier. Different exact assemblies can have identical display labels either because their recorded instants tie exactly or because distinct seconds collapse to the same displayed minute. The selector retains precise objects internally, but a teacher cannot determine which indistinguishable row they are selecting.

## Narrow correction

- Move the existing history-label calculation into `_saved_assembly_version_labels` and reuse the shared `distinguish_equal_labels` helper, adding `saved copy 1 of N (display order, not chronological)` only when labels are otherwise identical. Do not claim record-ID sort order means historical chronology.
- Bind the chosen row to the exact, original validated `VerifiedAssemblyVersion` object before passing its saved `AssemblyPageSelection` to the existing `open_returned_artifact_evidence`; reconstructed and non-listed objects fail closed with no viewer call.
- Echo the human-readable saved-choice label in the receipt so a teacher can distinguish equal displayed timestamps after selecting. Do not print assembly IDs, source paths or scan IDs.
- Preserve snapshot checks in both history inspection and verified opener. Unverified/corrupt manifest/source/PDF fails closed through the existing owner. Core's Windows safe opener is unmodified; a successful OS request is not proof of viewer display.

## Regression scenarios

Synthetic witnesses for exact timestamp ties, display-minute collisions, unique labels, exact selection, forged/reconstructed selections, missing history, cancellation, tampered history, stale state, and Core opener failure. Run the old `#105` and `#134` evidence/history/long-path tests alongside #151 Slice 0–3A to ensure no movement of the custody or write boundary. The two return-gated attribution strict xfails intentionally remain unresolved until Slice 4.

## Exclusions and qualification boundaries

No edits to Core, stored scans, PDS2, assembly byte generation, immutable manifests, source-hash verification, Notes/Tasks, Review/Score, saved version persistence, or actual local file opener. Qualification on synthetic fixtures does NOT establish physical classroom capture or native >260-character OneDrive PDF-viewer acceptance; both remain Slice 6 gates. No merge, publish, tag, or release.
