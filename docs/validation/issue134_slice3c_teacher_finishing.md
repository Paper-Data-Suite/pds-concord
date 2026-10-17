# Concord #134 — Slice 3C: scoring and scan-inbox finishing

Baseline: `25c63ae9036968dd08fb17cfbf124de413a24538`.

This is a **teacher-presentation-only** change. It does not migrate or rewrite Concord
records, change Score target/criterion/scale identity, infer evidence bindings,
select scan sources automatically, or alter Core scan custody or routing.

- Scoring confirmations display the exact selected Group, Session, Artifact or
  roster-authorized student **name when available**, rather than their opaque keys.
  The existing Group Score warning remains mandatory.
- Score history resolves target labels and historical Criterion/Scale names with
  a single display-context construction per screen, never a per-row Graph load.
  Display resolution failures give an explicit missing-label message; they never
  replace the exact canonical Score reference or manufacture its evidence basis.
- Ambiguous equal names receive numbered, explicitly nonchronological labels.
  History still distinguishes true current Score heads from historical records.
- Routine attribution confirmations and results do not print association IDs,
  correction IDs, or snapshot revisions. Advanced durable-ID authoring is preserved.
- Scan inbox rows display their **filesystem modified** time, never mislabeling it
  as physical scanning, routing, or receipt. Sort order and exact returned Paths
  are unchanged. Missing file metadata fails only the optional label.

Concord #134 continues with Core v0.6.6 installed viewer acceptance, then one
clean release qualification. The prior slices remain separate committed history.
