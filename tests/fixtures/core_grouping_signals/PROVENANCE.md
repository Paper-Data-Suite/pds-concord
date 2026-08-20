# Core grouping-signal fixture provenance

These fixtures are the byte-exact synthetic `grouping_signal_set_v1` fixture
payload released with `pds-core` v0.6.1. They are vendored only for Concord
contract/compatibility tests; they are not runtime package data and they do not
define Concord grouping policy.

Release identity:

```text
Core tag: v0.6.1
Core release commit: f99c68a9fc8ed32546f28f78ea705f371fa088e4
Fixture asset: pds-core-0.6.1-grouping-signal-fixtures.zip
Fixture asset SHA-256: d8376292dd68ada48d35ab98233381de0008d41f868844e27e8507bf0d0f8f8d
Archive prefix: grouping_signals_v1/
```

The files below `v1/` are copied byte-for-byte from the released fixture asset.
`v1/SHA256SUMS.txt` is the upstream internal manifest and must not be edited to
make modified fixtures appear valid. `scripts/verify_core_grouping_fixtures.py`
authenticates both the vendored payload and, when supplied, the exact released
ZIP asset.

All class and student identities are synthetic. Dimension names, band counts,
and band values demonstrate contract behavior only; they are not defaults,
proficiency labels, ability labels, or recommendations for Concord planning.
