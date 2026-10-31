# Issue #142 — Slice 6B Repair 1: Canonical Standards in Artifact readers

## Observed failure

The genuine mixed-orientation Slice 6B integration fixture persisted its
synthetic Core Standards library. `list_artifacts()` nevertheless used
`load_graph()` without supplying that library, causing the canonical graph
validator to refuse the read before the Review/Score qualification could run.
The teacher-choice reader used the same unqualified graph-load path.

## Repair

The three Artifact summary/detail/scan readers and the teacher-choice reader
share one read-only `_load_artifact_graph` path. It loads the existing canonical
workspace Standards library when present and passes it to the *existing fully
validated* `load_graph`. Missing libraries remain `None`; standard-backed
Activities still fail closed. Malformed libraries are not suppressed.

## Scope and gates

Two production read-only modules; one additive synthetic test module; this
additive audit. No scoring or Review writer changes, Core Standards mutation,
student/school workspace access, staging, commits, or pushes. The original
Slice 6B real-score tests are unchanged and must pass before acceptance.
