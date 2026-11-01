# Concord #143 — Slice 6 Repair 1: transition the frozen #140 C2 witness to fixed-after

## Reason for the targeted test repair

The first Windows final-gate run on the exact Slice 1–5 Git tree `cddf772e0def2257cc0bcb4804165ab7ff140105` ran the **complete** pytest suite: **2,788 passed, one failed, 17 skipped**. The only failure was `tests/test_issue140_slice2_failing_before.py::test_c2_native_standards_identity_survives_but_menu_preset_save_rejects_it`. The failure was caused by an obsolete #140 assertion: the fixture intentionally called `pytest.fail` if the menu reached `confirm_write` after `prepare_criterion_set_preset_from_activity`. Issue #143 fixed this model contract; reaching confirmation now is correct.

The original #140 investigation and its frozen audit/census artifacts remain unchanged. This test retains its exact historical pytest node ID (as C1 did for #141) but changes **only** the C2 scenario's assertions to require the successful **reviewed** teacher menu flow, once-only preset revision creation, exact `SL.PE.11-12.1` and Standards profile identity, ordered individual/Group Criterion distinctions, intentional no-recommendation Scale choice, zero copied Scores, and unchanged source Activity graph and snapshot history. It invokes the genuine public preview and commit services, with monkeypatching limited to the menu's workspace binding/interaction, not to their implementation. No production code is changed by this repair.

## Guard and qualification sequence

1. Verify that the historical test's original Git blob is exactly `bc021349faa588c0f14a3628b8640a0a4d1e93dd` at the pinned #142 main ancestor, with the old C2 function occupying the final test block.
2. Rebuild a detached Git candidate from the exact qualified Slice 1–5 tree; append the existing Slice 6 operation-ID audit and this repair record; replace only C2's final function and its obsolete module docstring line.
3. Run **focused** pytest on the changed historical test file first. If it fails, stop without running the expensive full suite or touching the original checkout.
4. On focused success, run the existing complete `scripts/validate_repository.py` gate **once** on the repaired candidate, then the dedicated isolated installed Core 0.6.6 + candidate Concord mixed-Standards preset smoke. The full suite is repeated only because the previous gate did not produce a green final acceptance; not per ordinary slice.
5. Only after every gate passes, mirror the two additive audit documents and the single patched historical test into the original checkout. Preserve its empty Git index. No commit, push, PR, merge or release claim.

Passing this amended candidate and its isolated wheel is not a Suite-composition release certificate, #162 independent review, or CI approval. Source-only acceptance is never conflated with published release wheel authentication.
