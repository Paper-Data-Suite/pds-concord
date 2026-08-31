# Concord v0.3.0 release checklist

The qualification Core artifact is:

```text
pds_core-0.6.3-py3-none-any.whl
SHA-256:
98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5
```

No phase publishes to PyPI or another package index.

## Phase A — release-preparation branch and PR

- [x] start from reconciled post-#70 / post-#98 `main` at
      `33bd916978da21f4a317a1509adc77981a25aa26`
- [x] authenticate the exact released Core 0.6.3 wheel
- [x] record the clean pre-edit authoritative baseline validator PASS
- [x] audit all 15 ADRs
- [x] audit architecture, grouping-signal privacy, reusable/instance boundaries,
      teacher usability, and installed/suite interoperability
- [x] inherit issue #70 physical acceptance without a redundant #71 physical run
- [x] harden release validators for module operations and the exact direct runtime
      dependency set
- [x] promote source and active qualification surfaces from `0.3.0.dev0` to
      `0.3.0`
- [x] roll the changelog and add `RELEASE_NOTES_v0.3.0.md`
- [x] focused issue #71 release-preparation tests pass
- [x] authoritative validator passes with `--allow-dirty`
- [x] physical qualification delta audit confirms no behavior-changing change to
      the #70-qualified print/PDS2/scan/Artifact/Review/Score/publication path
- [x] complete release-preparation diff receives independent review
- [x] hosted Ubuntu/Windows, Python 3.11–3.14 CI passes
- [x] release-preparation PR is squash-merged

Tagging, final artifact hashes, GitHub Release publication, and fresh-download
verification cannot be completed on the release-preparation branch.

## Phase B — post-merge exact-main qualification

- [x] reconcile local `main` and require `main == origin/main`
- [x] require a clean tree and record the exact merged commit
- [x] rerun the authoritative validator without `--allow-dirty`
- [x] build exactly `pds_concord-0.3.0-py3-none-any.whl` and
      `pds_concord-0.3.0.tar.gz` from that commit
- [x] pass Twine, ordinary wheel validation, release artifact validation, release
      compatibility, installed base smoke, installed shared-feature/starter
      smoke, and installed module-operations smoke
- [x] confirm the exact wheel resolves Concord/Core from isolated `site-packages`
      with `pip check` clean and no sibling PDS distribution required
- [x] complete the final physical-delta review against issue #70
- [x] compute `SHA256SUMS.txt` from these exact final artifacts
- [x] independently review the commit, filenames, byte lengths, and hashes

Expected final assets:

```text
pds_concord-0.3.0-py3-none-any.whl
pds_concord-0.3.0.tar.gz
SHA256SUMS.txt
```

## Phase C — tag and GitHub Release publication

- [x] create tag `v0.3.0` at the exact qualified commit
- [x] push the tag without rewriting an existing tag
- [x] create the GitHub Release from `v0.3.0` using
      `RELEASE_NOTES_v0.3.0.md`
- [x] upload the exact wheel, sdist, and `SHA256SUMS.txt`
- [x] verify uploaded asset byte lengths and SHA-256 values match Phase B
- [x] do not publish to a package index

## Phase D — post-release fresh-download verification

- [x] download Core 0.6.3 and Concord 0.3.0 assets into a fresh external directory
- [x] authenticate both wheels and the published Concord checksum file
- [x] install noneditably into a fresh virtual environment outside the checkout
- [x] run `pip check`
- [x] verify installed metadata, version, and `concord --version`
- [x] verify Core discovery of Concord routing-module, publication-producer, and
      module-operations providers
- [x] rerun bounded installed base and representative starter-workflow acceptance
- [x] rerun installed readiness/attention/module-operations acceptance
- [x] record issue #70 physical qualification as inherited PASS; do not perform a
      new physical print/mark/scan run for issue #71
- [x] record final artifact names, byte lengths, hashes, release URL/status, and
      fresh-download PASS in issue #71
- [x] final release verdict recorded; issue #71, umbrella #47, and the v0.3.0 milestone may now be closed

## Final v0.3.0 release record

```text
release commit:
fe37f9fca3dd7894a86f5a5c4e74bbe09c1e84ed

tag:
v0.3.0

GitHub Release:
https://github.com/Paper-Data-Suite/pds-concord/releases/tag/v0.3.0

pds_concord-0.3.0-py3-none-any.whl
bytes: 576627
SHA-256:
dd827f7059c91c79bd69b6190b3c673d6b3bbc02bc25fa666286bbf5883c5e12

pds_concord-0.3.0.tar.gz
bytes: 728573
SHA-256:
454ecb87bee50ec6a54b6e17c0d38ea14c3c7fb417a8926e2b32090dba0dc3db

SHA256SUMS.txt
bytes: 194
SHA-256:
869cb7d6247cc8ff9e7136cad7b0e775015b64c7ef33c868a51bdf73b9d4e6f9

pds_core-0.6.3-py3-none-any.whl
bytes: 305620
SHA-256:
98d7596ce0eed26e4d56a17bbbbd644db3014259b56a45783a173fe8237af5e5

fresh-download verification: PASS
installed provenance: PASS
installed module-operations smoke: PASS
issue #70 physical qualification: INHERITED PASS
new issue #71 physical print/mark/scan run: NOT REQUIRED
final release verdict: PASS
```
