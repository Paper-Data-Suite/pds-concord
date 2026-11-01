# Concord #143 — Slice 6 Repair 3: installed smoke record ordering

**Scope:** qualify runner-only test correction; no Concord source change from Repair 2, no grading/publication authority, no alteration to frozen #140 audit or #162 review ledger.

## Observed baseline and failure

The Repair 1 candidate produced a successful full repository pytest run of **2,789 passed, 17 skipped**, but the historical C2 test repair introduced one E501 overlong module docstring. Repair 2 reconstructed the prior exact candidate (`6944779ece994afa59ce76267cde894fe7d28def`), modified only that docstring (executable AST unchanged), and produced the new candidate tree `43724cb8ca2c15eae2de8b0c2c493fda56592c7f`. Focused C2, Ruff, mypy, documentation, build, package/release verification and existing isolated installed-wheel smokes passed. The additional runner-only #143 installed smoke failed at `assert list(by_key) == ["discussion_participation", "collaborative_textual_analysis"]`.

**Failure category:** smoke-test assumption about order, not an observed error in Standards identity, Criterion semantics or candidate wheel construction. Concord's native `CriterionSet.criterion_ids` represents teacher-authored Criterion order; `ConcordRecordGraph.criteria` is read from canonical record references and does not guarantee that order. A dictionary constructed from `graph.criteria` inherits the record enumeration order, which is not the Criterion Set's sequence. This distinction is important: passing solely on membership would insufficiently test preservation of rubric order.

## Exact runner-local repair

Replace the order-dependent `list(by_key)` assertion only. Require exactly two native Criteria and both exact keys irrespective of graph enumeration order. Independently require native `CriterionSet.criterion_ids == ("native-individual-143", "native-group-143")` so teacher-specified Criterion order is still asserted. Retain the remaining exact assertions on `SL.PE.11-12.1`, `W.NW.11-12.3.D`, individual `core_student` vs local `concord_group`, four-level ordinal Scale, zero Scores, and persistent saved preset. Do not change the candidate Concord wheel or any repository production/test file as part of this repair.

## Qualification method and evidence requirements

- Authenticate the exact original Checkout/branch and Slice 1–5 inventory, and confirm remote main/issue refs still match the #142 baseline.
- Authenticate the original runner ZIP and the one allowed substitution in the installed smoke script by byte-exact SHA-256.
- Require the previous Repair 2 candidate indexed Git tree `43724cb8ca2c15eae2de8b0c2c493fda56592c7f`, green prior full pytest and resumed validation logs, and the specific previous smoke assertion failure.
- Authenticate the already-built candidate `pds_concord-0.3.4-py3-none-any.whl` (SHA-256 `0c7be0206c4b36221856eac1adf6b6e0135ebe6d603be7cf65c231c1937d048f`) and official Core 0.6.6 wheel (SHA-256 `d6d21e426092b0329bcfd69b6fbee44c345edc46794a914d847d5ea73a2b7301`). Re-execute only the repaired synthetic #143 installed smoke in the prior isolated venv with `-I` and a workspace outside any school repository or production data.
- On success, construct a fresh detached candidate reproducing Repair 2's exact Git tree; add *only* this additive audit, stage/check the exact tree and `git diff --check`, rerun short Ruff and documentation validation, then mirror the four #143 Slice 6 audit docs and the reviewed C2 test to the original checkout with an empty Git index.

The full pytest result is **reused only with exact candidate receipt and unchanged executable source**. The full validator was resumed rather than executed as a single uninterrupted green process. Record the smoke result and final candidate tree only from the Windows runner output; at document creation time Repair 3 is not qualified. PR CI on Linux/Windows, independent #162 operation-level semantic review, upstream merge, post-merge CI, and published-wheel release verification remain distinct gates.
